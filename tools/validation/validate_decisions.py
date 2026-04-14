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
#   8. Decisions without allowed check in unchecked categories
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
    run_validator_main,
    should_skip_file,
)

EXTRA_SKIP_PATTERNS = ["FR_loc"]

# Decisions activated dynamically (e.g. via variable-constructed IDs) that
# cannot be detected by static analysis and should be excluded from the
# unused-decision check.
DYNAMICALLY_ACTIVATED_DECISIONS = [f"AC_project_{i}_target_decision" for i in range(15)]


def _should_skip(filename: str) -> bool:
    return should_skip_file(filename, extra_skip_patterns=EXTRA_SKIP_PATTERNS)


# --- Decision parsing helpers ---


def extract_value_single_line(obj: str, s: str) -> str:
    pattern = r"\t+" + s + r" = (\S*)"
    matches = re.findall(pattern, obj)
    return matches[0] if f"\t{s} =" in obj and matches else False


def extract_value_multi_line(obj: str, s: str) -> str:
    pattern = r"(\t+)" + s + r" = (\{([^\n]*|.*?^\1)\})"
    if f"\t{s} =" not in obj:
        return False
    matches = re.findall(pattern, obj, flags=re.DOTALL | re.MULTILINE)
    return matches[0][1] if matches else False


class DecisionFactory:
    def __init__(self, dec: str) -> None:
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
        self.state_target = "state_target = yes" in dec
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
        self.fixed_random_seed_no = "fixed_random_seed = no" in dec


def parse_all_decisions(
    mod_path: str, lowercase: bool = False
) -> Tuple[List[str], Dict[str, str]]:
    filepath = str(Path(mod_path) / "common" / "decisions")
    pattern = re.compile(r"^\t[^\t#]+ = \{.*?^\t\}", flags=re.MULTILINE | re.DOTALL)
    decisions = []
    paths = {}

    for filename in glob.iglob(filepath + "/**/*.txt", recursive=True):
        if "categories" in filename:
            continue
        text_file = FileOpener.open_text_file(
            filename, lowercase=lowercase, strip_comments_flag=True
        )
        matches = pattern.findall(text_file)
        for match in matches:
            decisions.append(match)
            paths[match] = os.path.basename(filename)

    return decisions, paths


def parse_all_decision_names(
    mod_path: str, lowercase: bool = False
) -> Tuple[List[str], Dict[str, str]]:
    decisions, dec_paths = parse_all_decisions(mod_path, lowercase)
    pattern = re.compile(r"^\t(.+) =", flags=re.MULTILINE)
    names = []
    name_paths = {}
    for d in decisions:
        name = pattern.findall(d)[0]
        names.append(name)
        name_paths[name] = dec_paths[d]
    return names, name_paths


def parse_decision_categories(
    mod_path: str, lowercase: bool = False, visible_when_empty: bool = True
) -> Dict[str, str]:
    filepath = str(Path(mod_path) / "common" / "decisions" / "categories")
    categories = {}
    cat_pattern = re.compile(r"^\w* = \{.*?^\}", flags=re.DOTALL | re.MULTILINE)
    name_pattern = re.compile(r"^(.*) = \{")

    for filename in glob.iglob(filepath + "/**/*.txt", recursive=True):
        text_file = FileOpener.open_text_file(
            filename, lowercase=lowercase, strip_comments_flag=True
        )
        matches = re.findall(cat_pattern, text_file)
        for match in matches:
            if not visible_when_empty and "visible_when_empty = yes" in match:
                continue
            name = re.findall(name_pattern, match)
            if name:
                categories[name[0]] = match

    return categories


def parse_categories_with_decisions(
    mod_path: str, lowercase: bool = False, visible_when_empty: bool = True
) -> Dict[str, List[str]]:
    filepath = str(Path(mod_path) / "common" / "decisions")
    category_names = list(
        parse_decision_categories(mod_path, lowercase, visible_when_empty).keys()
    )
    result = {cat: [] for cat in category_names}
    dec_pattern = re.compile(r"^[ \t]+(\S+) = \{", flags=re.MULTILINE)

    for filename in glob.iglob(filepath + "/**/*.txt", recursive=True):
        if "categories" in filename:
            continue
        text_file = FileOpener.open_text_file(
            filename, lowercase=lowercase, strip_comments_flag=True
        )
        for category in category_names:
            if f"{category} = {{" in text_file:
                pattern = r"^" + re.escape(category) + r" = \{.*?^\}"
                matches = re.findall(pattern, text_file, flags=re.DOTALL | re.MULTILINE)
                for match in matches:
                    dec_names = dec_pattern.findall(match)
                    result[category].extend(dec_names)

    return result


class Validator(BaseValidator):
    TITLE = "DECISION VALIDATION"
    STAGED_EXTENSIONS = [".txt"]

    def __init__(self, *args, fix: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.fix = fix

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

    def validate_duplicated_decisions(self):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking for duplicated decisions...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        names, paths = parse_all_decision_names(self.mod_path)
        self.log(f"  Found {len(names)} total decisions")
        results = [f"{n} - {paths[n]}" for n in names if names.count(n) > 1]
        results = sorted(set(results))
        self._report(
            results, "✓ No duplicated decisions", "Duplicated decisions found:"
        )

    def validate_unused_decisions(self):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking for unused decisions (always=no but never activated)...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        decisions, paths = parse_all_decisions(self.mod_path)
        pattern_decision = re.compile(r"activate_targeted_decision = [^\n\t]*")
        pattern_mission = re.compile(r"activate_mission = \S*")
        manual_decisions = {}
        manual_missions = {}

        for dec_code in decisions:
            d = DecisionFactory(dec=dec_code)
            if d.allowed:
                if "always = no" in d.allowed and not d.mission_subtype:
                    manual_decisions[d.token] = 0
                elif "always = no" in d.allowed and d.mission_subtype:
                    manual_missions[d.token] = 0

        for filename in glob.iglob(self.mod_path + "**/*.txt", recursive=True):
            if _should_skip(filename):
                continue
            text_file = FileOpener.open_text_file(
                filename, lowercase=False, strip_comments_flag=True
            )
            if "activate_targeted_decision =" in text_file:
                remaining = {k: v for k, v in manual_decisions.items() if v == 0}
                all_matches = pattern_decision.findall(text_file)
                for dec in remaining:
                    for match in all_matches:
                        if f"decision = {dec}" in match:
                            manual_decisions[dec] += 1
            if "activate_mission =" in text_file:
                remaining = {k: v for k, v in manual_missions.items() if v == 0}
                all_matches = pattern_mission.findall(text_file)
                for mission in remaining:
                    if f"activate_mission = {mission}" in all_matches:
                        manual_missions[mission] += 1

        results = [
            k
            for k in manual_decisions
            if manual_decisions[k] == 0 and k not in DYNAMICALLY_ACTIVATED_DECISIONS
        ]
        results += [
            k
            for k in manual_missions
            if manual_missions[k] == 0 and k not in DYNAMICALLY_ACTIVATED_DECISIONS
        ]
        self._report(
            results,
            "✓ No unused decisions",
            "Unused decisions (always=no but never manually activated):",
        )

    def validate_unused_categories(self):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking for unused decision categories...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

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
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking decision AI factors...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        decisions, paths = parse_all_decisions(self.mod_path)
        categories = parse_decision_categories(self.mod_path)
        cats_with_decs = parse_categories_with_decisions(self.mod_path)
        results = []
        fixes_needed = []

        for dec_code in decisions:
            d = DecisionFactory(dec=dec_code)
            if d.available and any(
                ["is_ai = no" in d.available, "always = no" in d.available]
            ):
                continue
            if d.visible and any(
                ["is_ai = no" in d.visible, "always = no" in d.visible]
            ):
                continue

            dec_category = None
            for cat in cats_with_decs:
                if d.token in cats_with_decs[cat]:
                    dec_category = cat
                    break
            if dec_category and dec_category in categories:
                cat_code = categories[dec_category]
                if "is_ai = no" in cat_code or "always = no" in cat_code:
                    continue

            if d.mission_subtype:
                if d.selectable_mission and not d.ai_factor:
                    results.append(
                        f"{d.token} - {paths[dec_code]} - Selectable mission missing AI factor"
                    )
                elif not d.selectable_mission and d.ai_factor:
                    results.append(
                        f"{d.token} - {paths[dec_code]} - Non-selectable mission has AI factor"
                    )
            elif not d.ai_factor and "debug" not in d.token:
                results.append(
                    f"{d.token} - {paths[dec_code]} - Decision missing AI factor"
                )
                if self.fix:
                    fixes_needed.append((d.token, paths[dec_code]))

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
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking decisions with custom_cost_trigger have a tooltip...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        decisions, paths = parse_all_decisions(self.mod_path)
        results = []

        for dec_code in decisions:
            d = DecisionFactory(dec=dec_code)
            if d.custom_cost_trigger and not d.has_tooltip and not d.custom_cost_text:
                results.append(
                    f"{d.token:<55}{paths[dec_code]} - has custom_cost_trigger but no tooltip or custom_cost_text"
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
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking targeted decisions without targets (performance)...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        decisions, paths = parse_all_decisions(self.mod_path)
        results = []

        for dec_code in decisions:
            d = DecisionFactory(dec=dec_code)
            if d.target_root_trigger or d.target_trigger:
                if not d.targets and not d.target_array:
                    if d.allowed and "always = no" in d.allowed:
                        continue
                    if d.state_target or d.map_only:
                        continue
                    results.append(f"{d.token:<55}{paths[dec_code]}")

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
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking decisions with FROM checks in visible/available but no target_trigger (performance)...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        decisions, paths = parse_all_decisions(self.mod_path)
        results = []

        from_pattern = re.compile(r"\bFROM\s*=\s*\{")
        for dec_code in decisions:
            d = DecisionFactory(dec=dec_code)
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
                results.append(f"{d.token:<55}{paths[dec_code]}")

        self._report(
            results,
            "✓ No decisions with FROM checks needing target_trigger",
            "Decisions with FROM checks in visible/available but no target_trigger (move FROM into target_trigger for perf):",
        )

    def validate_without_allowed_check(self):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking decisions without allowed trigger in unchecked categories...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        cats_with_decs = parse_categories_with_decisions(self.mod_path)
        decisions, _ = parse_all_decisions(self.mod_path)
        categories = parse_decision_categories(self.mod_path)

        unchecked_cats = []
        for cat, cat_code in categories.items():
            if "allowed = {" not in cat_code:
                unchecked_cats.append(cat)

        decisions_to_check = []
        for cat in unchecked_cats:
            if cat in cats_with_decs:
                decisions_to_check.extend(cats_with_decs[cat])

        results = []
        for dec_code in decisions:
            d = DecisionFactory(dec=dec_code)
            if d.token in decisions_to_check:
                if not d.allowed:
                    results.append(d.token)

        self._report(
            results,
            "✓ No decisions missing allowed check",
            "Decisions in categories without allowed check that also lack their own allowed trigger:",
        )

    def validate_random_list_seed(self):
        """Flag decisions that use ``random_list = { ... }`` without ``fixed_random_seed = no``.

        HOI4 caches RNG outcomes by default within a single tick/save state, so
        a ``random_list`` inside a decision will deterministically pick the same
        branch every time it's evaluated unless ``fixed_random_seed = no`` is
        set on the decision. This defeats the point of the random_list and
        leads to confusingly stuck behavior. The fix is to add
        ``fixed_random_seed = no`` to the decision body.
        """
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking decisions with random_list missing fixed_random_seed = no...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        decisions, paths = parse_all_decisions(self.mod_path)
        results = []

        for dec_code in decisions:
            d = DecisionFactory(dec=dec_code)
            if d.has_random_list and not d.fixed_random_seed_no:
                results.append(f"{d.token:<55}{paths[dec_code]}")

        self._report(
            results,
            "✓ No random_list decisions missing fixed_random_seed = no",
            "Decisions with random_list but no 'fixed_random_seed = no' (RNG will deterministically repeat):",
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
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking decisions for redundant tag checks...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        decisions, paths = parse_all_decisions(self.mod_path)
        results = []

        # Pattern matching a `tag = TAG` or `original_tag = TAG` token anywhere
        # inside a block. We use brace-depth tracking to ensure the match is at
        # the *top level* of the surrounding block (depth 0 within the block),
        # not nested inside OR/NOT/AND/if subblocks.
        TAG_TOKEN_PATTERN = re.compile(
            r"\b(original_tag|tag)\s*=\s*([A-Z][A-Z0-9_]{1,7})\b"
        )

        def _flat_tag_pins(block: str):
            """Return set of tags pinned by flat (non-OR'd) tag/original_tag tokens.

            Tokens nested inside OR/NOT/AND/if subblocks are skipped — those
            are conditional, not a hard pin. Handles both multi-line and
            single-line ``{ original_tag = SER }`` formats.
            """
            if not block:
                return set()
            # Strip the outer braces of the block if present
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
                    # Skip to end of line
                    while i < n and inner[i] != "\n":
                        i += 1
                    continue
                if depth == 0:
                    m = TAG_TOKEN_PATTERN.match(inner, i)
                    if m:
                        tags.add(m.group(2))
                        i = m.end()
                        continue
                i += 1
            return tags

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

        for dec_code in decisions:
            d = DecisionFactory(dec=dec_code)
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
                    f"{d.token:<55}{paths[dec_code]} ({pinned}: {', '.join(issues)})"
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
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking decisions with allowed redundant with parent category...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        decisions, paths = parse_all_decisions(self.mod_path)
        categories = parse_decision_categories(self.mod_path)
        cats_with_decs = parse_categories_with_decisions(self.mod_path)

        TAG_TOKEN = re.compile(r"\b(original_tag|tag)\s*=\s*([A-Z][A-Z0-9_]{1,7})\b")

        def flat_pins(block):
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
                    m = TAG_TOKEN.match(inner, i)
                    if m:
                        tags.add(m.group(2))
                        i = m.end()
                        continue
                i += 1
            return tags

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
            cat_pins[cat_name] = flat_pins(cat_code[a_start:i])

        results = []
        for dec_code in decisions:
            d = DecisionFactory(dec=dec_code)
            if not d.allowed:
                continue
            dec_pinned = flat_pins(d.allowed)
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
                results.append(f"{d.token:<55}{paths[dec_code]} ({pinned})")

        self._report(
            results,
            "✓ No decisions with allowed redundant with parent category",
            "Decisions with `allowed` redundant with parent category (remove the decision's allowed):",
        )

    def validate_pp_charge_in_effect(self):
        """Flag decisions that charge political power via ``add_political_power = -N``
        in ``complete_effect``/``remove_effect`` instead of using the proper
        ``cost = N`` field.

        The ``cost`` field integrates with the engine's UI (greys out the
        decision when PP < cost, displays the cost in the tooltip, blocks
        the AI from queueing it without sufficient PP) and is the canonical
        way to charge PP for a decision. Hand-rolling the charge inside an
        effect block bypasses all of that and produces inconsistent UX.

        Only flags ``add_political_power = -N`` at the **top level** of the
        effect block — i.e. directly charging the decision-taker. Nested
        charges inside conditional blocks (``if``, ``random_list``) or scope
        changes (``OTHER_TAG = { ... }``) are gameplay outcomes, not costs,
        and are left alone.

        Skipped if:
        - decision already has a ``cost`` field
        - decision has a ``custom_cost_trigger`` (its own custom cost flow)
        - decision is a mission subtype (``days_mission_timeout``) — PP changes
          there are mission outcomes, not entry costs
        """
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking decisions for hand-rolled PP cost in effects...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        decisions, paths = parse_all_decisions(self.mod_path)
        results = []

        def _has_top_level_neg_pp(block: str) -> bool:
            """True if a literal `add_political_power = -N` exists at depth 0
            of the block (i.e. unconditional charge to the decision-taker)."""
            if not block:
                return False
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
                    m = re.match(r"add_political_power\s*=\s*(-\d+)", inner[i:])
                    if m:
                        return True
                i += 1
            return False

        for dec_code in decisions:
            d = DecisionFactory(dec=dec_code)
            if d.cost or d.custom_cost_trigger:
                continue
            if d.mission_subtype:
                continue
            for block_name, block in (
                ("complete_effect", d.complete_effect),
                ("remove_effect", d.remove_effect),
            ):
                if not block:
                    continue
                if _has_top_level_neg_pp(block):
                    results.append(
                        f"{d.token:<55}{paths[dec_code]} ({block_name}: charges PP without cost field)"
                    )
                    break

        self._report(
            results,
            "✓ No decisions hand-rolling PP cost in effects",
            "Decisions charging political power in effects (use 'cost = N' instead):",
        )

    def validate_bare_trigger_names(self):
        """Check for common bare trigger names that need a has_ prefix.

        HOI4 requires ``has_political_power``, ``has_stability``, etc. when
        used as comparison triggers.  The bare names (``political_power < 50``)
        are silently accepted by the parser but produce runtime errors.  Only
        flag occurrences that look like comparison triggers (followed by ``<``
        or ``>``), and exclude ``check_variable`` blocks where the bare name
        is a valid variable reference.
        """
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking for bare trigger names missing has_ prefix...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

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
        self.validate_without_allowed_check()
        self.validate_random_list_seed()
        self.validate_redundant_tag_checks()
        self.validate_allowed_redundant_with_category()
        self.validate_pp_charge_in_effect()
        self.validate_bare_trigger_names()


def _add_extra_args(parser):
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Auto-insert 'ai_will_do = { base = 0 }' into decisions missing an AI factor",
    )


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate decisions in Millennium Dawn mod",
        extra_args_fn=_add_extra_args,
    )
