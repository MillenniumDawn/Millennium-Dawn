#!/usr/bin/env python3
##########################
# Decision Validation Script (Multiprocessing Optimized)
# Validates decision definitions and usage
# Checks for:
#   1. Duplicated decisions
#   2. Unused decisions (always=no in allowed but never manually activated)
#   3. Unused decision categories (empty categories not used in BOP)
#   4. Decisions with AI factor issues
#   5. Custom cost trigger validation (tooltip presence)
#   6. Targeted decisions without targets (performance issue)
#   7. Decisions with targets but no target_trigger (performance issue)
#   8. Decisions using FROM without a target set (undefined scope)
#   9. Decisions without allowed check in unchecked categories
#  10. Random list without explicit fixed_random_seed
#  11. Redundant tag checks (allowed already pins tag)
#  12. Allowed redundant with parent category
#  13. Political power charge in effects (hidden or double cost)
#  14. Identical visible and available blocks
#  15. Bare trigger names missing has_ prefix
#  16. Missing localisation keys
#  17. Visible block in missions (does nothing; use activation instead)
#  18. war_with_on_* = FROM in targeted decisions (use war_with_target_on_*)
#  19. cancel_if_not_visible without a visible block (dead code)
#  20. Custom cost with PP but no ai_hint_pp_cost (AI unaware of cost)
#  21. Incompatible state_target value with explicit targets
#  22. Mission-only attributes on regular decisions (silently ignored)
#  23. remove_effect without days_remove or remove_trigger (dead code)
#  24. targets_dynamic / target_non_existing without targets (meaningless)
# Based on Kaiserreich Autotests by Pelmen, https://github.com/Pelmen323
# Adapted for Millennium Dawn with multiprocessing
##########################
import glob
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

from validator_common import (
    BaseValidator,
    Colors,
    FileOpener,
    Severity,
    run_validator_main,
    should_skip_file,
)

EXTRA_SKIP_PATTERNS = ["FR_loc"]

# Decisions activated dynamically (e.g. via variable-constructed IDs) that
# cannot be detected by static analysis and should be excluded from the
# unused-decision check.
DYNAMICALLY_ACTIVATED_DECISIONS = [
    f"AC_project_{i}_target_decision" for i in range(15)
] + [f"investments_project_{i}_target_decision" for i in range(15)]


def _should_skip(filename: str) -> bool:
    return should_skip_file(filename, extra_skip_patterns=EXTRA_SKIP_PATTERNS)


_TARGETED_BLOCK_RE = re.compile(
    r"\bactivate_targeted_decision\s*=\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}"
)
_DECISION_NAME_RE = re.compile(r"\bdecision\s*=\s*(\S+)")
_MISSION_NAME_RE = re.compile(r"\bactivate_mission\s*=\s*(\S+)")


def _scan_activations_in_file(filename: str) -> Tuple[set, set]:
    if _should_skip(filename):
        return set(), set()
    text_file = FileOpener.open_text_file(
        filename, lowercase=False, strip_comments_flag=True
    )
    decisions: set = set()
    missions: set = set()
    if "activate_targeted_decision" in text_file:
        for block in _TARGETED_BLOCK_RE.findall(text_file):
            decisions.update(_DECISION_NAME_RE.findall(block))
    if "activate_mission" in text_file:
        missions.update(_MISSION_NAME_RE.findall(text_file))
    return decisions, missions


# --- Decision parsing helpers ---

_TAG_TOKEN_PATTERN = re.compile(r"\b(original_tag|tag)\s*=\s*([A-Z][A-Z0-9_]{1,7})\b")


def _flat_tag_pins(block: str) -> set:
    """Return the set of tags pinned by flat (non-nested) tag/original_tag tokens.

    Tokens nested inside OR/NOT/AND/if subblocks are skipped because they are
    conditional, not hard pins. Handles both multi-line and single-line block
    formats.
    """
    if not block:
        return set()
    inner = block.strip()
    if inner.startswith("{"):
        inner = inner[1:]
    if inner.endswith("}"):
        inner = inner[:-1]
    tags = set()
    depth = 0
    i = 0
    n = len(inner)
    while i < n:
        ch = inner[i]
        if ch == "{":
            depth += 1
            i += 1
            continue
        if ch == "}":
            depth -= 1
            i += 1
            continue
        if ch == "#":
            while i < n and inner[i] != "\n":
                i += 1
            continue
        if depth == 0:
            m = _TAG_TOKEN_PATTERN.match(inner, i)
            if m:
                tags.add(m.group(2))
                i = m.end()
                continue
        i += 1
    return tags


def extract_value_single_line(obj: str, s: str) -> str:
    pattern = r"\t+" + s + r" = (\S*)"
    matches = re.findall(pattern, obj)
    return matches[0] if f"\t{s} =" in obj and matches else False


def _top_level_field_value(raw: str, field: str):
    """Return the value of ``field = X`` at the top level of a decision body.

    The decision body is at brace depth 1 (depth 0 = before/after the outer
    braces of the decision token). Occurrences nested inside sub-blocks like
    ``complete_effect = { create_ship = { name = ... } }`` are ignored.

    Returns ``None`` if the field is absent at depth 1 or if its value is a
    quoted literal string (which the engine renders verbatim, with no loc
    lookup to verify).
    """
    pat = re.compile(r"\b" + re.escape(field) + r"\s*=\s*(\S+)")
    depth = 0
    i = 0
    n = len(raw)
    while i < n:
        ch = raw[i]
        if ch == "{":
            depth += 1
            i += 1
            continue
        if ch == "}":
            depth -= 1
            i += 1
            continue
        if ch == "#":
            while i < n and raw[i] != "\n":
                i += 1
            continue
        if depth == 1:
            prev = raw[i - 1] if i > 0 else "\n"
            if not (prev.isalnum() or prev == "_"):
                m = pat.match(raw, i)
                if m:
                    value = m.group(1)
                    if value.startswith('"'):
                        return None
                    return value
        i += 1
    return None


def extract_value_multi_line(obj: str, s: str) -> str:
    pattern = r"(\t+)" + s + r" = (\{([^\n]*|.*?^\1)\})"
    if f"\t{s} =" not in obj:
        return False
    matches = re.findall(pattern, obj, flags=re.DOTALL | re.MULTILINE)
    return matches[0][1] if matches else False


class DecisionFactory:
    def __init__(self, dec: str, source_basename: str = "") -> None:
        self.source_basename = source_basename
        self.raw = dec
        self.token = re.findall(r"^\t*(.+) = \{", dec, flags=re.MULTILINE)[0]
        self.allowed = extract_value_multi_line(dec, "allowed")
        self.available = extract_value_multi_line(dec, "available")
        self.visible = extract_value_multi_line(dec, "visible")
        self.cancel_effect = extract_value_multi_line(dec, "cancel_effect")
        self.complete_effect = extract_value_multi_line(dec, "complete_effect")
        self.remove_effect = extract_value_multi_line(dec, "remove_effect")
        self.cancel_trigger = extract_value_multi_line(dec, "cancel_trigger")
        self.cancel_if_not_visible = "cancel_if_not_visible = yes" in dec
        self.target_root_trigger = extract_value_multi_line(dec, "target_root_trigger")
        self.target_trigger = extract_value_multi_line(dec, "target_trigger")
        self.targets = extract_value_multi_line(dec, "targets")
        self.target_array = extract_value_single_line(dec, "target_array")
        _st_match = re.search(r"\bstate_target\s*=\s*(\w+)", dec)
        self.state_target_value = _st_match.group(1) if _st_match else None
        self.state_target = (
            self.state_target_value is not None and self.state_target_value != "no"
        )
        self.map_only = "on_map_mode = map_only" in dec
        self.mission_subtype = "\tdays_mission_timeout =" in dec
        self.selectable_mission = (
            "\tdays_mission_timeout =" in dec and "selectable_mission = yes" in dec
        )
        self.ai_factor = extract_value_multi_line(dec, "ai_will_do")
        self.custom_cost_trigger = extract_value_multi_line(dec, "custom_cost_trigger")
        self.custom_cost_text = extract_value_single_line(dec, "custom_cost_text")
        self.ai_hint_pp_cost = extract_value_single_line(dec, "ai_hint_pp_cost")
        self.cost = extract_value_single_line(dec, "cost")
        self.has_tooltip = "tooltip =" in dec
        self.has_random_list = bool(re.search(r"\brandom_list\s*=\s*\{", dec))
        self.fixed_random_seed_explicit = bool(
            re.search(r"\bfixed_random_seed\s*=\s*(yes|no)\b", dec)
        )
        self.war_with_on_complete = extract_value_single_line(
            dec, "war_with_on_complete"
        )
        self.war_with_on_remove = extract_value_single_line(dec, "war_with_on_remove")
        self.war_with_on_timeout = extract_value_single_line(dec, "war_with_on_timeout")
        self.has_timeout_effect = "timeout_effect" in dec
        self.has_activation_block = bool(re.search(r"\bactivation\s*=\s*\{", dec))
        self.has_is_good = "is_good" in dec
        self.has_selectable_mission_kw = "selectable_mission = yes" in dec
        self.has_days_remove = "days_remove" in dec
        self.has_remove_trigger = "remove_trigger" in dec
        self.targets_dynamic = "targets_dynamic" in dec
        self.target_non_existing = "target_non_existing" in dec
        # Top-level name/desc overrides redirect the engine's loc lookup.
        # When set, the engine uses these keys instead of the decision id /
        # `<id>_desc` pair. Extract them with brace-depth awareness so we
        # don't pick up nested `name = ...` inside create_ship / create_unit
        # effect sub-blocks.
        self.name_override = _top_level_field_value(dec, "name")
        self.desc_override = _top_level_field_value(dec, "desc")


# Decisions parsing cache - enabled by default, disabled via --no-cache for CI
_DECISION_CACHE = {"enabled": True, "data": {}}


def _set_cache_enabled(enabled: bool):
    """Enable or disable the decision parsing cache."""
    global _DECISION_CACHE
    _DECISION_CACHE["enabled"] = enabled
    if not enabled:
        _DECISION_CACHE["data"].clear()


def _invalidate_decision_cache():
    """Drop all cached decision data so subsequent parse calls re-read disk.

    Call this after any ``--fix`` pass that rewrites decision files so later
    validators see the patched contents instead of stale factories.
    """
    _DECISION_CACHE["data"].clear()


def _get_cached(key: str, mod_path: str, lowercase: bool, factory_fn):
    """Get cached result or compute and cache it."""
    if not _DECISION_CACHE["enabled"]:
        return factory_fn()

    cache_key = f"{mod_path}:{lowercase}:{key}"
    if cache_key not in _DECISION_CACHE["data"]:
        _DECISION_CACHE["data"][cache_key] = factory_fn()
    return _DECISION_CACHE["data"][cache_key]


def parse_all_decisions(
    mod_path: str, lowercase: bool = False
) -> Tuple[List[str], Dict[str, str]]:
    """Parse all decisions with caching."""

    def _parse():
        filepath = str(Path(mod_path) / "common" / "decisions")
        # Pre-compile pattern once
        _decisions_pattern = re.compile(
            r"^\t[^\t#]+ = \{.*?^\t\}", flags=re.MULTILINE | re.DOTALL
        )
        decisions = []
        paths = {}

        for filename in glob.iglob(filepath + "/**/*.txt", recursive=True):
            if "categories" in filename:
                continue
            text_file = FileOpener.open_text_file(
                filename, lowercase=lowercase, strip_comments_flag=True
            )
            matches = _decisions_pattern.findall(text_file)
            for match in matches:
                decisions.append(match)
                paths[match] = os.path.basename(filename)

        return decisions, paths

    return _get_cached("decisions", mod_path, lowercase, _parse)


def parse_all_decision_factories(
    mod_path: str, lowercase: bool = False
) -> List["DecisionFactory"]:
    """Build DecisionFactory instances for every decision and cache them.

    Each factory does ~14 multi-line regex extractions in __init__, so building
    them once and reusing across all validators eliminates the dominant cost of
    a full decisions validation run (was ~7s of ~10s on this mod).

    The source filename is stored on the factory as ``source_basename`` so
    reporting code can avoid re-keying a parallel paths dict.
    """

    def _build():
        decisions, dec_paths = parse_all_decisions(mod_path, lowercase)
        return [DecisionFactory(dec=d, source_basename=dec_paths[d]) for d in decisions]

    return _get_cached("decision_factories", mod_path, lowercase, _build)


def parse_all_decision_names(
    mod_path: str, lowercase: bool = False
) -> Tuple[List[str], Dict[str, str]]:
    """Parse all decision names with caching."""

    def _parse():
        decisions, dec_paths = parse_all_decisions(mod_path, lowercase)
        _names_pattern = re.compile(r"^\t(.+) =", flags=re.MULTILINE)
        names = []
        name_paths = {}
        for d in decisions:
            name = _names_pattern.findall(d)[0]
            names.append(name)
            name_paths[name] = dec_paths[d]
        return names, name_paths

    return _get_cached("decision_names", mod_path, lowercase, _parse)


def parse_decision_categories(
    mod_path: str, lowercase: bool = False, visible_when_empty: bool = True
) -> Dict[str, str]:
    """Parse decision categories with caching."""

    def _parse():
        filepath = str(Path(mod_path) / "common" / "decisions" / "categories")
        categories = {}
        # Pre-compile patterns once
        _cat_pattern = re.compile(r"^\w* = \{.*?^\}", flags=re.DOTALL | re.MULTILINE)
        _name_pattern = re.compile(r"^(.*) = \{")

        for filename in glob.iglob(filepath + "/**/*.txt", recursive=True):
            text_file = FileOpener.open_text_file(
                filename, lowercase=lowercase, strip_comments_flag=True
            )
            matches = re.findall(_cat_pattern, text_file)
            for match in matches:
                if not visible_when_empty and "visible_when_empty = yes" in match:
                    continue
                name = re.findall(_name_pattern, match)
                if name:
                    categories[name[0]] = match

        return categories

    cache_key = f"categories:{visible_when_empty}"
    return _get_cached(cache_key, mod_path, lowercase, _parse)


def parse_categories_with_decisions(
    mod_path: str, lowercase: bool = False, visible_when_empty: bool = True
) -> Dict[str, List[str]]:
    """Parse categories with their decisions - reuses category cache."""

    def _parse():
        # Reuse the categories cache instead of re-parsing
        categories = parse_decision_categories(mod_path, lowercase, visible_when_empty)
        category_names = list(categories.keys())

        result = {cat: [] for cat in category_names}

        filepath = str(Path(mod_path) / "common" / "decisions")
        _dec_pattern = re.compile(r"^[ \t]+(\S+) = \{", flags=re.MULTILINE)

        for filename in glob.iglob(filepath + "/**/*.txt", recursive=True):
            if "categories" in filename:
                continue
            text_file = FileOpener.open_text_file(
                filename, lowercase=lowercase, strip_comments_flag=True
            )
            for category in category_names:
                if f"{category} = {{" in text_file:
                    pattern = r"^" + re.escape(category) + r" = \{.*?^\}"
                    matches = re.findall(
                        pattern, text_file, flags=re.DOTALL | re.MULTILINE
                    )
                    for match in matches:
                        dec_names = _dec_pattern.findall(match)
                        result[category].extend(dec_names)

        return result

    cache_key = f"cats_with_decs:{visible_when_empty}"
    return _get_cached(cache_key, mod_path, lowercase, _parse)


def _remove_available_block_for_token(content: str, token: str):
    """Remove the ``available = { ... }`` sub-block of a decision named ``token``.

    Uses brace-balanced scanning so nested blocks (``NOT = { ... }``, etc.)
    inside ``available`` are handled correctly. Returns the rewritten content,
    or ``None`` if the token / available block could not be located.
    """
    token_pattern = re.compile(
        r"(^|\n)(\s*)" + re.escape(token) + r"\s*=\s*\{", re.MULTILINE
    )
    m = token_pattern.search(content)
    if not m:
        return None

    body_start = m.end()
    depth = 1
    i = body_start
    dec_end = -1
    while i < len(content):
        ch = content[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                dec_end = i
                break
        i += 1
    if dec_end < 0:
        return None

    decision_body = content[body_start:dec_end]
    avail_match = re.search(
        r"(^|\n)([ \t]*)available\s*=\s*\{", decision_body, re.MULTILINE
    )
    if not avail_match:
        return None

    avail_body_start = avail_match.end()
    depth = 1
    j = avail_body_start
    avail_end = -1
    while j < len(decision_body):
        ch = decision_body[j]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                avail_end = j
                break
        j += 1
    if avail_end < 0:
        return None

    # Range covers the leading newline (if any), keyword, and block.
    remove_start = avail_match.start()
    remove_end = avail_end + 1  # include closing brace
    new_decision_body = decision_body[:remove_start] + decision_body[remove_end:]
    # Collapse any doubled blank lines introduced by the removal.
    new_decision_body = re.sub(r"\n[ \t]*\n[ \t]*\n", "\n\n", new_decision_body)

    return content[:body_start] + new_decision_body + content[dec_end:]


class Validator(BaseValidator):
    TITLE = "DECISION VALIDATION"
    STAGED_EXTENSIONS = [".txt"]

    def __init__(self, *args, fix: bool = False, no_cache: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.fix = fix
        if no_cache:
            _set_cache_enabled(False)

    def _apply_ai_factor_fixes(self, fixes: list):
        """Insert a default ai_will_do = { base = 0 } block into decisions missing one."""
        dec_filepath = str(Path(self.mod_path) / "common" / "decisions")

        by_file: Dict[str, List[str]] = {}
        for token, basename in fixes:
            by_file.setdefault(basename, []).append(token)

        fixed_total = 0
        for basename, tokens in by_file.items():
            target_file = None
            for filepath in glob.iglob(dec_filepath + "/**/*.txt", recursive=True):
                if os.path.basename(filepath) == basename:
                    target_file = filepath
                    break

            if not target_file:
                self.log(f"  Could not locate file: {basename}", "warning")
                continue

            with open(target_file, "r", encoding="utf-8-sig") as f:
                content = f.read()

            for token in tokens:
                pattern = re.compile(
                    r"(^\t" + re.escape(token) + r" = \{.*?)(^\t\})",
                    flags=re.MULTILINE | re.DOTALL,
                )

                def _inserter(m):
                    return (
                        m.group(1)
                        + "\t\tai_will_do = {\n\t\t\tbase = 0\n\t\t}\n"
                        + m.group(2)
                    )

                new_content, count = pattern.subn(_inserter, content)
                if count:
                    content = new_content
                    fixed_total += 1
                else:
                    self.log(f"  Could not patch {token} in {basename}", "warning")

            with open(target_file, "w", encoding="utf-8-sig") as f:
                f.write(content)

        self.log(
            f"{Colors.GREEN if self.use_colors else ''}  Auto-fixed {fixed_total} decision(s) with missing ai_will_do{Colors.ENDC if self.use_colors else ''}"
        )
        if fixed_total:
            _invalidate_decision_cache()

    def validate_duplicated_decisions(self):
        self._log_section("Checking for duplicated decisions...")

        names, paths = parse_all_decision_names(self.mod_path)
        self.log(f"  Found {len(names)} total decisions")
        results = [f"{n} - {paths[n]}" for n in names if names.count(n) > 1]
        results = sorted(set(results))
        self._report(
            results, "✓ No duplicated decisions", "Duplicated decisions found:"
        )

    def validate_unused_decisions(self):
        self._log_section(
            "Checking for unused decisions (always=no but never activated)..."
        )

        factories = parse_all_decision_factories(self.mod_path)
        manual_decisions: set = set()
        manual_missions: set = set()

        for d in factories:
            if d.allowed and "always = no" in d.allowed:
                if d.mission_subtype:
                    manual_missions.add(d.token)
                else:
                    manual_decisions.add(d.token)

        # The worker extracts `decision = X` only from inside an
        # `activate_targeted_decision = { ... }` block; the bare keyword
        # `decision` appears in unrelated places (on_political_decision hooks etc.)
        # and matching them would hide genuinely unused decisions.
        all_files = list(
            glob.iglob(os.path.join(self.mod_path, "**", "*.txt"), recursive=True)
        )
        activated_decisions: set = set()
        activated_missions: set = set()
        for dec_set, mis_set in self._pool_map(
            _scan_activations_in_file, all_files, chunksize=30
        ):
            activated_decisions.update(dec_set)
            activated_missions.update(mis_set)

        results = sorted(
            (manual_decisions - activated_decisions)
            - set(DYNAMICALLY_ACTIVATED_DECISIONS)
        )
        results += sorted(
            (manual_missions - activated_missions)
            - set(DYNAMICALLY_ACTIVATED_DECISIONS)
        )
        self._report(
            results,
            "✓ No unused decisions",
            "Unused decisions (always=no but never manually activated):",
        )

    def validate_unused_categories(self):
        self._log_section("Checking for unused decision categories...")

        cats_with_decisions = parse_categories_with_decisions(
            self.mod_path, visible_when_empty=False
        )
        cats_to_validate = {
            cat: 0 for cat in cats_with_decisions if cats_with_decisions[cat] == []
        }

        if not cats_to_validate:
            self.log(
                f"{Colors.GREEN if self.use_colors else ''}✓ No empty decision categories{Colors.ENDC if self.use_colors else ''}"
            )
            return

        bop_path = str(Path(self.mod_path) / "common" / "bop")
        found_files = False
        for filename in glob.iglob(bop_path + "/**/*.txt", recursive=True):
            found_files = True
            text_file = FileOpener.open_text_file(
                filename, lowercase=False, strip_comments_flag=True
            )
            not_found = [c for c in cats_to_validate if cats_to_validate[c] == 0]
            for cat in not_found:
                if f"decision_category = {cat}" in text_file:
                    cats_to_validate[cat] += 1

        if not found_files:
            self.log(
                f"{Colors.YELLOW if self.use_colors else ''}No BOP files found, skipping BOP check{Colors.ENDC if self.use_colors else ''}",
                "warning",
            )

        results = [cat for cat in cats_to_validate if cats_to_validate[cat] == 0]
        self._report(
            results,
            "✓ No unused decision categories",
            "Unused decision categories (empty, not in BOP):",
        )

    def validate_ai_factors(self):
        self._log_section("Checking decision AI factors...")

        factories = parse_all_decision_factories(self.mod_path)
        categories = parse_decision_categories(self.mod_path)
        cats_with_decs = parse_categories_with_decisions(self.mod_path)

        # Reverse index: decision token -> parent category. The previous
        # version did an O(N) scan per decision over `cats_with_decs`, which
        # added ~1.5s on this mod.
        decision_to_category: Dict[str, str] = {}
        for cat, dec_tokens in cats_with_decs.items():
            for tok in dec_tokens:
                decision_to_category.setdefault(tok, cat)

        results = []
        fixes_needed = []

        for d in factories:
            if d.available and any(
                ["is_ai = no" in d.available, "always = no" in d.available]
            ):
                continue
            if d.visible and any(
                ["is_ai = no" in d.visible, "always = no" in d.visible]
            ):
                continue

            dec_category = decision_to_category.get(d.token)
            if dec_category and dec_category in categories:
                cat_code = categories[dec_category]
                if "is_ai = no" in cat_code or "always = no" in cat_code:
                    continue

            if d.mission_subtype:
                if d.selectable_mission and not d.ai_factor:
                    results.append(
                        f"{d.token} - {d.source_basename} - Selectable mission missing AI factor"
                    )
                elif not d.selectable_mission and d.ai_factor:
                    results.append(
                        f"{d.token} - {d.source_basename} - Non-selectable mission has AI factor"
                    )
            elif not d.ai_factor and "debug" not in d.token:
                results.append(
                    f"{d.token} - {d.source_basename} - Decision missing AI factor"
                )
                if self.fix:
                    fixes_needed.append((d.token, d.source_basename))

            # Note: we previously flagged "zeroed AI factors not evaluated
            # immediately" when factor=0 modifiers appeared after add=N
            # modifiers. That heuristic is wrong for HOI4: ai_will_do
            # evaluates in order on a running total, and clustering
            # factor=0 before the adds makes them a no-op (0*0=0 with base=0).
            # The whole point of placing factor=0 after adds is to override
            # the adds conditionally. Do not re-add that check.

        self._report(results, "✓ No AI factor issues", "Decision AI factor issues:")

        if self.fix and fixes_needed:
            self._apply_ai_factor_fixes(fixes_needed)

    def validate_custom_cost_trigger(self):
        self._log_section(
            "Checking decisions with custom_cost_trigger have a tooltip..."
        )

        factories = parse_all_decision_factories(self.mod_path)
        results = []

        for d in factories:
            if d.custom_cost_trigger and not d.has_tooltip and not d.custom_cost_text:
                results.append(
                    f"{d.token:<55}{d.source_basename} - has custom_cost_trigger but no tooltip or custom_cost_text"
                )

        self._report(
            results,
            "✓ No custom cost trigger issues",
            "Decisions with custom_cost_trigger but missing tooltip:",
        )

    def validate_targeted_without_target(self):
        """Flag targeted decisions missing an explicit target set.

        Exempts:
        - ``allowed = { always = no }`` (decision is script-activated, never auto-visible)
        - ``state_target = yes`` / ``on_map_mode = map_only`` (player-driven map click;
          the engine iterates states/countries only on map interaction, not daily)
        """
        self._log_section(
            "Checking targeted decisions without targets (performance)..."
        )

        factories = parse_all_decision_factories(self.mod_path)
        results = []

        for d in factories:
            if d.target_root_trigger or d.target_trigger:
                if not d.targets and not d.target_array:
                    if d.allowed and "always = no" in d.allowed:
                        continue
                    if d.state_target or d.map_only:
                        continue
                    results.append(f"{d.token:<55}{d.source_basename}")

        self._report(
            results,
            "✓ No targeted decisions without targets",
            "Decisions with target_root_trigger/target_trigger but no targets (checks every country daily):",
        )

    def validate_targets_no_trigger(self):
        """Flag decisions whose visible/available contains FROM checks but lack a target_trigger.

        Having ``targets = { TAG }`` or ``target_array = X`` without a target_trigger
        is perfectly valid — the game simply uses ``visible``/``available`` to filter
        per target. The performance concern arises only when those blocks contain
        FROM checks (evaluated every tick per target). Moving those FROM checks
        into ``target_trigger`` makes them daily instead.
        """
        self._log_section(
            "Checking decisions with FROM checks in visible/available but no target_trigger (performance)..."
        )

        factories = parse_all_decision_factories(self.mod_path)
        results = []

        from_pattern = re.compile(r"\bFROM\s*=\s*\{")
        for d in factories:
            if not (d.targets or d.target_array):
                continue
            if d.target_trigger:
                continue
            # Only flag if there's at least one FROM = { ... } block in visible or available
            has_from_filter = False
            if d.visible and from_pattern.search(d.visible):
                has_from_filter = True
            if d.available and from_pattern.search(d.available):
                has_from_filter = True
            if has_from_filter:
                results.append(f"{d.token:<55}{d.source_basename}")

        self._report(
            results,
            "✓ No decisions with FROM checks needing target_trigger",
            "Decisions with FROM checks in visible/available but no target_trigger (move FROM into target_trigger for perf):",
        )

    def validate_from_without_targets(self):
        """Flag decisions referencing FROM without a targeting mechanism.

        On a non-targeted country-scoped decision, ``FROM`` falls back to
        ROOT/THIS — so ``var:FROM.array^i`` and ``FROM.GetName`` usually
        resolve to the decision owner rather than firing into the void.
        That makes the code redundant at best and misleading at worst:
        a reader sees FROM and assumes another country is involved, when
        really the decision is just self-referencing.

        Exempts:
        - ``allowed = { always = no }`` — activated via ``activate_decision``
          / ``activate_targeted_decision`` with an explicit FROM set by the
          caller.
        - ``targets`` / ``target_array`` — standard targeted decision.
        - ``state_target = yes`` / ``on_map_mode = map_only`` — FROM is the
          state selected by the player.
        """
        self._log_section("Checking decisions for FROM usage without a target set...")

        factories = parse_all_decision_factories(self.mod_path)
        results = []

        from_pattern = re.compile(r"\bFROM\b")
        for d in factories:
            if d.targets or d.target_array:
                continue
            if d.state_target or d.map_only:
                continue
            if d.allowed and "always = no" in d.allowed:
                continue

            offending = []
            if d.visible and from_pattern.search(d.visible):
                offending.append("visible")
            if d.available and from_pattern.search(d.available):
                offending.append("available")
            if d.complete_effect and from_pattern.search(d.complete_effect):
                offending.append("complete_effect")

            if offending:
                results.append(
                    f"{d.token:<55}{d.source_basename} - FROM used in {', '.join(offending)} but no targets/target_array/state_target"
                )

        self._report(
            results,
            "✓ No decisions with unscoped FROM usage",
            "Decisions using FROM without a target mechanism (FROM falls back to ROOT so the code is redundant/misleading — add targets/target_array if another country was intended, drop the FROM prefix otherwise, or set allowed = { always = no } if activated via script):",
        )

    def validate_without_allowed_check(self):
        self._log_section(
            "Checking decisions without allowed trigger in unchecked categories..."
        )

        cats_with_decs = parse_categories_with_decisions(self.mod_path)
        factories = parse_all_decision_factories(self.mod_path)
        categories = parse_decision_categories(self.mod_path)

        unchecked_cats = []
        for cat, cat_code in categories.items():
            if "allowed = {" not in cat_code:
                unchecked_cats.append(cat)

        decisions_to_check = set()
        for cat in unchecked_cats:
            if cat in cats_with_decs:
                decisions_to_check.update(cats_with_decs[cat])

        results = []
        for d in factories:
            if d.token in decisions_to_check:
                if not d.allowed:
                    results.append(d.token)

        self._report(
            results,
            "✓ No decisions missing allowed check",
            "Decisions in categories without allowed check that also lack their own allowed trigger:",
        )

    def validate_random_list_seed(self):
        """Flag decisions using ``random_list`` without an explicit ``fixed_random_seed`` setting.

        HOI4 caches RNG outcomes by default within a single tick/save state, so
        a ``random_list`` inside a decision will deterministically pick the same
        branch every time it's evaluated unless ``fixed_random_seed = no`` is
        set on the decision. This defeats the point of the random_list and
        leads to confusingly stuck behavior.

        We only flag decisions where ``fixed_random_seed`` is omitted entirely;
        an explicit ``fixed_random_seed = yes`` is treated as a deliberate
        choice (e.g. reproducible AI rolls) and left alone.
        """
        self._log_section(
            "Checking decisions with random_list missing fixed_random_seed = no..."
        )

        factories = parse_all_decision_factories(self.mod_path)
        results = []

        for d in factories:
            if d.has_random_list and not d.fixed_random_seed_explicit:
                results.append(f"{d.token:<55}{d.source_basename}")

        self._report(
            results,
            "✓ No random_list decisions missing an explicit fixed_random_seed setting",
            "Decisions with random_list but no explicit 'fixed_random_seed' (RNG will deterministically repeat — set 'fixed_random_seed = no' to randomise, or 'fixed_random_seed = yes' to acknowledge intentional determinism):",
        )

    def validate_redundant_tag_checks(self):
        """Flag redundant tag/original_tag checks within a single decision.

        Two patterns are flagged:

        1. ``allowed`` already pins the decision to a single tag (via
           ``tag = X`` or ``original_tag = X``) and ``visible`` or ``available``
           re-checks the same tag. Since ``allowed`` permanently disables the
           decision for any country with a different tag, the visible/available
           check is dead weight evaluated every tick.

        2. ``allowed`` has both ``tag = X`` and ``original_tag = X`` for the
           same tag — only one is needed (and ``original_tag`` is preferred so
           civil-war split-offs still match).

        Note: this only flags decisions whose ``allowed`` is a flat single-tag
        gate. Decisions whose ``allowed`` uses ``OR``/``NOT``/no tag at all
        are skipped — those legitimately need per-tag filtering downstream.
        """
        self._log_section("Checking decisions for redundant tag checks...")

        factories = parse_all_decision_factories(self.mod_path)
        results = []

        def _scan_top_level(block: str):
            """Iterate top-level tokens inside a block.

            Yields (kind, payload) pairs where kind is 'tag' or 'scope' and
            payload is the tag string. Tokens nested inside subblocks
            (OR/AND/NOT/if/custom_trigger_tooltip/etc.) are skipped — those are
            conditional context, not unconditional pins.
            """
            if not block:
                return
            inner = block.strip()
            if inner.startswith("{"):
                inner = inner[1:]
            if inner.endswith("}"):
                inner = inner[:-1]

            depth = 0
            i = 0
            n = len(inner)
            while i < n:
                ch = inner[i]
                if ch == "{":
                    depth += 1
                    i += 1
                    continue
                if ch == "}":
                    depth -= 1
                    i += 1
                    continue
                if ch == "#":
                    while i < n and inner[i] != "\n":
                        i += 1
                    continue
                if depth == 0:
                    # An identifier-start char only counts if it begins on a
                    # word boundary (preceded by start-of-block or whitespace),
                    # otherwise we'd misread `has_cosmetic_tag = MAU` as a
                    # `tag = MAU` token.
                    if ch.isalpha() or ch == "_":
                        prev = inner[i - 1] if i > 0 else "\n"
                        if prev.isalnum() or prev == "_":
                            i += 1
                            continue
                        m = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*", inner[i:])
                        if m:
                            ident = m.group(1)
                            after = i + m.end()
                            # `tag = X` / `original_tag = X` token
                            if ident in ("tag", "original_tag"):
                                tm = re.match(r"([A-Z][A-Z0-9_]{1,7})\b", inner[after:])
                                if tm:
                                    yield ("tag", tm.group(1))
                                    i = after + tm.end()
                                    continue
                            # `TAG = { ... }` self-scope (3-letter caps tag)
                            if (
                                re.match(r"^[A-Z][A-Z0-9_]{1,7}$", ident)
                                and after < n
                                and inner[after] == "{"
                            ):
                                yield ("scope", ident)
                                # Don't consume the brace, let the outer loop dive in
                                i = after
                                continue
                            # Skip past the entire identifier so we don't
                            # re-scan its tail and falsely match nested tokens.
                            i = after
                            continue
                i += 1

        def _has_top_level_tag_check(block: str, tag: str) -> bool:
            for kind, payload in _scan_top_level(block):
                if kind == "tag" and payload == tag:
                    return True
            return False

        def _has_top_level_self_scope(block: str, tag: str) -> bool:
            for kind, payload in _scan_top_level(block):
                if kind == "scope" and payload == tag:
                    return True
            return False

        for d in factories:
            if not d.allowed:
                continue
            allowed_tags = _flat_tag_pins(d.allowed)
            if not allowed_tags:
                continue
            # Only consider single-tag pins (multi-tag allowed is not a redundancy issue here)
            if len(allowed_tags) != 1:
                continue
            pinned = next(iter(allowed_tags))

            issues = []

            # Pattern 2a: allowed has BOTH `tag = X` and `original_tag = X`
            tag_count = len(
                re.findall(
                    r"\btag\s*=\s*" + re.escape(pinned) + r"\b",
                    d.allowed,
                )
            )
            orig_count = len(
                re.findall(
                    r"\boriginal_tag\s*=\s*" + re.escape(pinned) + r"\b",
                    d.allowed,
                )
            )
            if tag_count and orig_count:
                issues.append("allowed has both 'tag' and 'original_tag'")
            # Pattern 2b: allowed uses `tag = X` instead of `original_tag = X`.
            # The `tag` form excludes civil-war split-offs (which have
            # `original_tag = X` but a different runtime tag), so it's almost
            # always a code smell.
            elif tag_count and not orig_count:
                issues.append(
                    "allowed uses 'tag' (prefer 'original_tag' for civil-war robustness)"
                )

            # Pattern 1: visible/available re-checks the same tag at top level
            if _has_top_level_tag_check(d.visible, pinned):
                issues.append("visible re-checks tag")
            if _has_top_level_tag_check(d.available, pinned):
                issues.append("available re-checks tag")

            # Pattern 3: visible/available scopes back into self at top level
            if _has_top_level_self_scope(d.visible, pinned):
                issues.append("visible self-scopes")
            if _has_top_level_self_scope(d.available, pinned):
                issues.append("available self-scopes")

            if issues:
                results.append(
                    f"{d.token:<55}{d.source_basename} ({pinned}: {', '.join(issues)})"
                )

        self._report(
            results,
            "✓ No redundant tag checks found",
            "Decisions with redundant tag checks (allowed already pins the tag):",
        )

    def validate_allowed_redundant_with_category(self):
        """Flag decisions whose ``allowed`` is fully redundant with the parent
        category's ``allowed`` (same single-tag pin, no extra conditions).

        E.g. a decision with ``allowed = { original_tag = SER }`` inside a
        category that already declares ``allowed = { original_tag = SER }``.
        The decision-level allowed is dead weight — remove it.
        """
        self._log_section(
            "Checking decisions with allowed redundant with parent category..."
        )

        factories = parse_all_decision_factories(self.mod_path)
        categories = parse_decision_categories(self.mod_path)
        cats_with_decs = parse_categories_with_decisions(self.mod_path)

        # Build category -> pinned tags
        cat_pins = {}
        for cat_name, cat_code in categories.items():
            am = re.search(r"\ballowed\s*=\s*\{", cat_code)
            if not am:
                continue
            a_start = cat_code.find("{", am.start())
            depth = 1
            i = a_start + 1
            while i < len(cat_code) and depth > 0:
                if cat_code[i] == "{":
                    depth += 1
                elif cat_code[i] == "}":
                    depth -= 1
                i += 1
            cat_pins[cat_name] = _flat_tag_pins(cat_code[a_start:i])

        results = []
        for d in factories:
            if not d.allowed:
                continue
            dec_pinned = _flat_tag_pins(d.allowed)
            if len(dec_pinned) != 1:
                continue
            pinned = next(iter(dec_pinned))
            # Verify allowed has ONLY this pin (no extra conditions)
            inner = d.allowed.strip()
            if inner.startswith("{"):
                inner = inner[1:]
            if inner.endswith("}"):
                inner = inner[:-1]
            cleaned = re.sub(r"#[^\n]*", "", inner).strip()
            single_pin_pat = re.compile(
                r"^\s*(?:original_tag|tag)\s*=\s*" + re.escape(pinned) + r"\s*$"
            )
            if not single_pin_pat.match(cleaned):
                continue

            # Find parent category
            cat_name = None
            for c, dec_set in cats_with_decs.items():
                if d.token in dec_set:
                    cat_name = c
                    break
            if cat_name not in cat_pins:
                continue
            if pinned in cat_pins[cat_name]:
                results.append(f"{d.token:<55}{d.source_basename} ({pinned})")

        self._report(
            results,
            "✓ No decisions with allowed redundant with parent category",
            "Decisions with `allowed` redundant with parent category (remove the decision's allowed):",
        )

    def validate_pp_charge_in_effect(self):
        """Flag decisions that charge political power via ``add_political_power = -N``
        in ``complete_effect``/``remove_effect`` instead of (or in addition to)
        the proper ``cost = N`` field.

        Two cases are reported:

        1. **Hidden cost** — no top-level ``cost`` field and the effect block
           has an unconditional ``add_political_power = -N``. The player pays
           PP without the engine displaying a cost or gating affordability.

        2. **Double-charge** — both a ``cost = N`` field AND an unconditional
           ``add_political_power = -M`` in the effect. The true cost is
           ``N + M`` but the UI shows only ``N``. Roll the hidden charge into
           the cost field and remove the duplicate.

        Only flags ``add_political_power = -N`` at the **top level** of the
        effect block — i.e. unconditional charges to the decision-taker.
        Nested charges inside ``if``/``random_list``/scope changes are
        gameplay outcomes, not costs, and are left alone.

        Skipped if:

        - decision has a ``custom_cost_trigger`` (its own custom cost flow)
        - decision is a non-selectable mission (``days_mission_timeout``
          without ``selectable_mission = yes``) — PP changes in those effects
          are timeout outcomes, not entry costs. Selectable missions still
          get checked because their ``complete_effect`` is the player path.
        """
        self._log_section("Checking decisions for hand-rolled PP cost in effects...")

        factories = parse_all_decision_factories(self.mod_path)
        hidden = []
        double = []

        def _top_level_neg_pp(block: str):
            """Return the magnitude (positive int) of an unconditional
            ``add_political_power = -N`` at depth 0 of ``block``, or ``None``
            if there is no such line. Conditional/nested subtractions are
            ignored (they are gameplay outcomes, not entry costs)."""
            if not block:
                return None
            inner = block.strip()
            if inner.startswith("{"):
                inner = inner[1:]
            if inner.endswith("}"):
                inner = inner[:-1]
            depth = 0
            i = 0
            n = len(inner)
            while i < n:
                ch = inner[i]
                if ch == "{":
                    depth += 1
                    i += 1
                    continue
                if ch == "}":
                    depth -= 1
                    i += 1
                    continue
                if ch == "#":
                    while i < n and inner[i] != "\n":
                        i += 1
                    continue
                if depth == 0:
                    m = re.match(r"add_political_power\s*=\s*-(\d+)", inner[i:])
                    if m:
                        return int(m.group(1))
                i += 1
            return None

        for d in factories:
            if d.custom_cost_trigger:
                continue
            if d.mission_subtype and not d.selectable_mission:
                continue

            try:
                cost_val = int(d.cost) if d.cost else 0
            except (TypeError, ValueError):
                cost_val = 0

            for block_name, block in (
                ("complete_effect", d.complete_effect),
                ("remove_effect", d.remove_effect),
            ):
                # remove_effect is always a timeout outcome for mission-type decisions;
                # skip it regardless of selectable_mission to avoid false positives.
                if block_name == "remove_effect" and d.mission_subtype:
                    continue
                pp = _top_level_neg_pp(block)
                if pp is None:
                    continue
                if cost_val > 0:
                    double.append(
                        f"{d.token:<55}{d.source_basename} ({block_name}: cost={cost_val} + {pp} hidden = {cost_val + pp} true; roll into cost)"
                    )
                else:
                    hidden.append(
                        f"{d.token:<55}{d.source_basename} ({block_name}: charges {pp} PP without cost field)"
                    )
                break

        self._report(
            hidden,
            "✓ No decisions hand-rolling PP cost in effects",
            "Decisions charging political power in effects without a cost field (use 'cost = N' instead):",
        )
        self._report(
            double,
            "✓ No decisions double-charging PP",
            "Decisions double-charging PP (cost field plus add_political_power in effect — roll into cost):",
        )

    def _normalize_block(self, block: str) -> str:
        """Normalize a trigger block for comparison by stripping whitespace/comments."""
        if not block:
            return ""
        inner = block.strip()
        if inner.startswith("{"):
            inner = inner[1:]
        if inner.endswith("}"):
            inner = inner[:-1]
        normalized = re.sub(r"#.*$", "", inner, flags=re.MULTILINE)
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized.strip()

    def validate_visible_equals_available(self):
        """Flag decisions where ``visible`` and ``available`` are functionally identical.

        In HOI4, the engine checks ``visible`` first to determine if a decision appears
        in the UI, then checks ``available`` to determine if it's clickable. If both
        blocks are identical, one is redundant. We move available -> visible since
        it's more efficient (only one check instead of two identical checks).
        """
        self._log_section("Checking decisions with identical visible and available...")

        factories = parse_all_decision_factories(self.mod_path)
        results = []
        fixes_needed = []

        for d in factories:
            if not d.visible or not d.available:
                continue

            vis_normalized = self._normalize_block(d.visible)
            avail_normalized = self._normalize_block(d.available)

            if (
                vis_normalized
                and avail_normalized
                and vis_normalized == avail_normalized
            ):
                results.append(f"{d.token:<55}{d.source_basename}")
                if self.fix:
                    fixes_needed.append((d.token, d.source_basename))

        self._report(
            results,
            "✓ No decisions with identical visible and available",
            "Decisions with identical visible and available:",
        )

        if self.fix and fixes_needed:
            self._apply_visible_to_available_fixes(fixes_needed)

    def _apply_visible_to_available_fixes(self, fixes: list):
        """Replace identical available blocks with the visible content and remove available."""
        dec_filepath = str(Path(self.mod_path) / "common" / "decisions")

        by_file: Dict[str, List[str]] = {}
        for token, basename in fixes:
            by_file.setdefault(basename, []).append(token)

        fixed_total = 0
        for basename, tokens in by_file.items():
            target_file = None
            for filepath in glob.iglob(dec_filepath + "/**/*.txt", recursive=True):
                if os.path.basename(filepath) == basename:
                    target_file = filepath
                    break

            if not target_file:
                self.log(f"  Could not locate file: {basename}", "warning")
                continue

            with open(target_file, "r", encoding="utf-8-sig") as f:
                content = f.read()

            for token in tokens:
                # Find the decision block, then remove its available = { ... }
                # sub-block using brace-balanced matching so nested blocks
                # (NOT = { ... }, AND = { ... }, etc.) don't break the patch.
                new_content = _remove_available_block_for_token(content, token)
                if new_content is not None and new_content != content:
                    content = new_content
                    fixed_total += 1
                else:
                    self.log(f"  Could not patch {token} in {basename}", "warning")

            with open(target_file, "w", encoding="utf-8-sig") as f:
                f.write(content)

        self.log(
            f"{Colors.GREEN if self.use_colors else ''}  Auto-fixed {fixed_total} decision(s) by moving available -> visible{Colors.ENDC if self.use_colors else ''}"
        )
        if fixed_total:
            _invalidate_decision_cache()

    def validate_bare_trigger_names(self):
        """Check for common bare trigger names that need a has_ prefix.

        HOI4 requires ``has_political_power``, ``has_stability``, etc. when
        used as comparison triggers.  The bare names (``political_power < 50``)
        are silently accepted by the parser but produce runtime errors.  Only
        flag occurrences that look like comparison triggers (followed by ``<``
        or ``>``), and exclude ``check_variable`` blocks where the bare name
        is a valid variable reference.
        """
        self._log_section("Checking for bare trigger names missing has_ prefix...")

        BARE_TRIGGERS = {
            "political_power": "has_political_power",
            "stability": "has_stability",
            "war_support": "has_war_support",
            "manpower": "has_manpower",
        }

        pattern = re.compile(
            r"^\t+(" + "|".join(BARE_TRIGGERS.keys()) + r")\s+[<>]",
            flags=re.MULTILINE,
        )

        results = []
        dec_filepath = str(Path(self.mod_path) / "common" / "decisions")
        for filename in sorted(glob.iglob(dec_filepath + "/**/*.txt", recursive=True)):
            if _should_skip(filename):
                continue
            text_file = FileOpener.open_text_file(
                filename, lowercase=False, strip_comments_flag=True
            )
            # Remove check_variable blocks where bare names are valid
            cleaned = re.sub(r"check_variable\s*=\s*\{[^}]*\}", "", text_file)
            for match in pattern.finditer(cleaned):
                bare = match.group(1)
                correct = BARE_TRIGGERS[bare]
                line_num = cleaned[: match.start()].count("\n") + 1
                basename = os.path.basename(filename)
                results.append(
                    f"{basename}:{line_num} - '{bare}' should be '{correct}'"
                )

        self._report(
            results,
            "✓ No bare trigger names found",
            "Bare trigger names (need has_ prefix):",
            category="bare-trigger-name",
        )

    def validate_missing_localisation(self):
        self._log_section("Checking for decisions with missing localisation keys...")

        factories = parse_all_decision_factories(self.mod_path, lowercase=False)
        loc_keys = self._load_localisation_keys()
        self.log(
            f"  Found {len(factories)} decisions, {len(loc_keys)} localisation keys"
        )

        results = []
        for dec in factories:
            dec_id = dec.token
            filename = dec.source_basename
            missing = []
            # Decisions can redirect the engine's loc lookup via top-level
            # `name = X` / `desc = X` fields. Validate the override key when
            # present; otherwise check the default `<id>` for the name. The
            # default `<id>_desc` is *not* checked when no override is set —
            # many decisions intentionally omit a description tooltip.
            name_key = dec.name_override if dec.name_override else dec_id
            if name_key not in loc_keys:
                missing.append(name_key)
            if dec.desc_override and dec.desc_override not in loc_keys:
                missing.append(dec.desc_override)
            if dec.custom_cost_text and dec.custom_cost_text not in loc_keys:
                missing.append(dec.custom_cost_text)
            for key in missing:
                results.append(f"{dec_id} - {filename}: missing loc key '{key}'")

        self._report(
            results,
            "✓ All decision localisation keys are defined",
            "Decisions with missing localisation keys:",
            Severity.WARNING,
            category="missing-decision-localisation",
        )

    def validate_visible_in_missions(self):
        """Flag missions that have a visible block.

        The HOI4 engine ignores visible on mission-type decisions entirely.
        Use activation = { ... } to control when a mission appears.
        """
        self._log_section(
            "Checking missions with visible block (does nothing for missions)..."
        )

        factories = parse_all_decision_factories(self.mod_path)
        results = []

        for d in factories:
            if d.mission_subtype and d.visible:
                results.append(
                    f"{d.token:<55}{d.source_basename} - visible does nothing on missions; use activation"
                )

        self._report(
            results,
            "✓ No missions with useless visible block",
            "Missions with visible block (does nothing — use activation instead):",
        )

    def validate_war_with_targeted(self):
        """Flag targeted decisions using war_with_on_* = FROM.

        The regular war_with_on_complete/remove/timeout arguments do not work
        when the target is FROM. Use the war_with_target_on_* = yes variants.
        """
        self._log_section("Checking targeted decisions for war_with_on_* = FROM...")

        factories = parse_all_decision_factories(self.mod_path)
        results = []

        for d in factories:
            issues = []
            if d.war_with_on_complete == "FROM":
                issues.append(
                    "war_with_on_complete = FROM → war_with_target_on_complete = yes"
                )
            if d.war_with_on_remove == "FROM":
                issues.append(
                    "war_with_on_remove = FROM → war_with_target_on_remove = yes"
                )
            if d.war_with_on_timeout == "FROM":
                issues.append(
                    "war_with_on_timeout = FROM → war_with_target_on_timeout = yes"
                )
            if issues:
                results.append(
                    f"{d.token:<55}{d.source_basename} - {'; '.join(issues)}"
                )

        self._report(
            results,
            "✓ No targeted decisions misusing war_with_on_* = FROM",
            "Targeted decisions using war_with_on_* = FROM (silently fails — use war_with_target_on_* = yes):",
        )

    def validate_cancel_if_not_visible(self):
        """Flag decisions with cancel_if_not_visible = yes but no visible block.

        cancel_if_not_visible adds the visible block's conditions to the
        cancel_trigger. Without a visible block, there are no conditions to
        add, making it dead code.
        """
        self._log_section(
            "Checking decisions with cancel_if_not_visible but no visible block..."
        )

        factories = parse_all_decision_factories(self.mod_path)
        results = []

        for d in factories:
            if d.cancel_if_not_visible and not d.visible:
                results.append(f"{d.token:<55}{d.source_basename}")

        self._report(
            results,
            "✓ No decisions with cancel_if_not_visible but missing visible",
            "Decisions with cancel_if_not_visible = yes but no visible block (dead code — remove cancel_if_not_visible or add visible):",
        )

    def validate_custom_cost_ai_hint(self):
        """Flag decisions with custom_cost_trigger involving PP but no ai_hint_pp_cost.

        A custom cost replaces the regular cost field, so the AI has no idea
        it needs to save up political power. ai_hint_pp_cost tells the AI
        how much PP to reserve before attempting the decision.
        """
        self._log_section(
            "Checking decisions with custom PP cost but no ai_hint_pp_cost..."
        )

        factories = parse_all_decision_factories(self.mod_path)
        results = []

        for d in factories:
            if not d.custom_cost_trigger:
                continue
            if d.ai_hint_pp_cost:
                continue
            if d.ai_factor and "base = 0" in d.ai_factor and "add" not in d.ai_factor:
                continue
            if "political_power" in d.custom_cost_trigger:
                results.append(
                    f"{d.token:<55}{d.source_basename} - custom_cost_trigger checks political_power but no ai_hint_pp_cost"
                )

        self._report(
            results,
            "✓ No custom PP cost decisions missing ai_hint_pp_cost",
            "Decisions with custom PP cost but no ai_hint_pp_cost (AI won't save up PP):",
            severity=Severity.WARNING,
        )

    def validate_state_target_with_targets(self):
        """Flag state-targeted decisions with explicit targets but incompatible state_target value.

        When using targets = {} or target_array with state-targeted decisions,
        only state_target = yes or state_target = any will work. Other values
        (any_owned_state, any_controlled_state, continent keys) produce errors.
        """
        self._log_section(
            "Checking state-targeted decisions for incompatible state_target with explicit targets..."
        )

        factories = parse_all_decision_factories(self.mod_path)
        results = []
        valid_with_targets = {"yes", "any"}

        for d in factories:
            if not d.state_target_value:
                continue
            if (
                d.state_target_value in valid_with_targets
                or d.state_target_value == "no"
            ):
                continue
            if d.targets or d.target_array:
                results.append(
                    f"{d.token:<55}{d.source_basename} - state_target = {d.state_target_value} with explicit targets (only yes/any work; use state_target = yes)"
                )

        self._report(
            results,
            "✓ No incompatible state_target with explicit targets",
            "State-targeted decisions with incompatible state_target value (produces error):",
        )

    def validate_mission_only_attributes(self):
        """Flag regular decisions using mission-only attributes.

        Several attributes only function on mission-type decisions (those with
        days_mission_timeout). On regular decisions they are silently ignored:
        timeout_effect, activation, is_good, selectable_mission,
        war_with_on_timeout, war_with_target_on_timeout.
        """
        self._log_section(
            "Checking regular decisions for mission-only attributes (silently ignored)..."
        )

        factories = parse_all_decision_factories(self.mod_path)
        results = []

        for d in factories:
            if d.mission_subtype:
                continue
            issues = []
            if d.has_timeout_effect:
                issues.append("timeout_effect")
            if d.has_activation_block:
                issues.append("activation")
            if d.has_is_good:
                issues.append("is_good")
            if d.has_selectable_mission_kw:
                issues.append("selectable_mission")
            if d.war_with_on_timeout:
                issues.append("war_with_on_timeout")
            if "war_with_target_on_timeout" in d.raw:
                issues.append("war_with_target_on_timeout")
            if issues:
                results.append(
                    f"{d.token:<55}{d.source_basename} - mission-only: {', '.join(issues)}"
                )

        self._report(
            results,
            "✓ No regular decisions with mission-only attributes",
            "Regular decisions using mission-only attributes (silently ignored — add days_mission_timeout to make a mission, or remove these):",
        )

    def validate_orphaned_remove_effect(self):
        """Flag decisions with remove_effect but no timer or removal trigger.

        remove_effect fires when a decision's timer expires (days_remove) or
        when remove_trigger evaluates true. Without either, the effect block
        is dead code that will never execute (unless removed externally via
        the remove_decision effect).

        Exempts missions (which use timeout_effect) and decisions activated
        via script (allowed = { always = no }).
        """
        self._log_section(
            "Checking decisions with remove_effect but no removal mechanism..."
        )

        factories = parse_all_decision_factories(self.mod_path)

        remove_pat = re.compile(r"\bremove_decision\s*=\s*(\w+)")
        remove_targeted_block_pat = re.compile(
            r"\bremove_targeted_decision\s*=\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}"
        )
        decision_name_pat = re.compile(r"\bdecision\s*=\s*(\w+)")
        externally_removed: set = set()

        for filename in glob.iglob(
            os.path.join(self.mod_path, "**", "*.txt"), recursive=True
        ):
            if _should_skip(filename):
                continue
            text_file = FileOpener.open_text_file(
                filename, lowercase=False, strip_comments_flag=True
            )
            if "remove_decision" not in text_file:
                continue
            externally_removed.update(remove_pat.findall(text_file))
            for block in remove_targeted_block_pat.findall(text_file):
                externally_removed.update(decision_name_pat.findall(block))

        results = []

        for d in factories:
            if not d.remove_effect:
                continue
            if d.mission_subtype:
                continue
            if d.allowed and "always = no" in d.allowed:
                continue
            if d.has_days_remove or d.has_remove_trigger:
                continue
            if d.token in externally_removed:
                continue
            results.append(f"{d.token:<55}{d.source_basename}")

        self._report(
            results,
            "✓ No decisions with orphaned remove_effect",
            "Decisions with remove_effect but no days_remove or remove_trigger (dead code — add a timer or removal trigger):",
            severity=Severity.WARNING,
        )

    def validate_orphaned_target_modifiers(self):
        """Flag decisions with targets_dynamic or target_non_existing but no targets.

        targets_dynamic = yes makes the game check dynamic country variants
        (civil war split-offs). target_non_existing = yes allows targeting
        countries that don't exist. Both only work with an explicit
        targets = { } list and are meaningless without one.
        """
        self._log_section(
            "Checking decisions with targets_dynamic/target_non_existing but no targets..."
        )

        factories = parse_all_decision_factories(self.mod_path)
        results = []

        for d in factories:
            issues = []
            if d.targets_dynamic and not d.targets:
                issues.append("targets_dynamic")
            if d.target_non_existing and not d.targets:
                issues.append("target_non_existing")
            if issues:
                results.append(
                    f"{d.token:<55}{d.source_basename} - {', '.join(issues)} without targets = {{ }}"
                )

        self._report(
            results,
            "✓ No decisions with orphaned target modifiers",
            "Decisions with targets_dynamic/target_non_existing but no targets (meaningless — add targets or remove):",
        )

    def run_validations(self):
        if self.staged_only:
            # Decision checks parse all 200+ decision files even for structural
            # validation (duplicates, AI factors). Skip entirely in staged mode;
            # CI handles the full decision validation.
            self.log(
                "Decision validation requires full file scan — skipping in staged mode",
                "warning",
            )
            return

        self.validate_duplicated_decisions()
        self.validate_unused_decisions()
        self.validate_unused_categories()
        self.validate_ai_factors()
        self.validate_custom_cost_trigger()
        self.validate_targeted_without_target()
        self.validate_targets_no_trigger()
        self.validate_from_without_targets()
        self.validate_without_allowed_check()
        self.validate_random_list_seed()
        self.validate_redundant_tag_checks()
        self.validate_allowed_redundant_with_category()
        self.validate_pp_charge_in_effect()
        self.validate_visible_equals_available()
        self.validate_bare_trigger_names()
        self.validate_missing_localisation()
        self.validate_visible_in_missions()
        self.validate_war_with_targeted()
        self.validate_cancel_if_not_visible()
        self.validate_custom_cost_ai_hint()
        self.validate_state_target_with_targets()
        self.validate_mission_only_attributes()
        self.validate_orphaned_remove_effect()
        self.validate_orphaned_target_modifiers()


def _add_extra_args(parser):
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Auto-fix decisions: insert 'ai_will_do = { base = 0 }' for missing AI factors, and move identical available blocks into visible",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable decision parsing cache (useful for CI runs where cache overhead exceeds benefit)",
    )


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate decisions in Millennium Dawn mod",
        extra_args_fn=_add_extra_args,
    )
