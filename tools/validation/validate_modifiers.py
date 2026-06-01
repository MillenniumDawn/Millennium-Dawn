#!/usr/bin/env python3
##########################
# Modifier Name Validation Script
# Validates modifier names used inside modifier = { } blocks in Millennium Dawn
# Checks for:
#   1. Unknown modifier names (not seen 3+ times across the codebase)
#   2. Possible typos (single-occurrence names that don't match known-good patterns)
#
# Approach: build a known-good set from codebase frequency (3+ uses = valid).
# Custom MD modifiers in common/modifiers/ and common/dynamic_modifiers/ are
# always valid. Single-use names that start with md_ or MD_ are also valid.
# Targeted modifiers (XXX_opinion, XXX_autonomy_gain) are skipped.
##########################
import os
import re
import sys
from collections import Counter
from typing import Dict, FrozenSet, List, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from validator_common import (
    BaseValidator,
    FileOpener,
    Severity,
    run_validator_main,
    should_skip_file,
)

# ---------------------------------------------------------------------------
# Keys that can appear inside modifier = { } blocks but are NOT modifier names
# ---------------------------------------------------------------------------

# These are HOI4 structural / ai-weight / targeted-modifier keys that appear
# inside blocks named "modifier" but carry no game-modifier meaning.
_NON_MODIFIER_KEYS: FrozenSet[str] = frozenset(
    {
        # AI weight modifier fields
        "factor",
        "base",
        "add",
        # Structural keys
        "tag",
        "scope",
        "days",
        "value",
        "icon",
        "enable",
        "remove_trigger",
        "var",
        "compare",
        # HOI4 logic blocks (can nest inside modifier)
        "if",
        "else",
        "else_if",
        "AND",
        "OR",
        "NOT",
        "limit",
    }
)

# Keys whose block-level usage means the enclosing modifier = {} is an
# ai_will_do-style weight modifier, not a game modifier block.
# We detect these by looking for them as the FIRST assignment key in the block.
_AI_WEIGHT_INDICATOR_KEYS: FrozenSet[str] = frozenset({"factor", "base", "add"})

# Keys that introduce sub-blocks we should skip when looking for modifier names
_SKIP_BLOCK_KEYS: FrozenSet[str] = frozenset(
    {
        "targeted_modifier",
        "equipment_bonus",
        "research_bonus",
        "ai_will_do",
        "ai_research_weights",
    }
)

# Regex patterns for skipping obviously parametric / targeted modifier entries
# e.g. TAG_opinion, TAG_autonomy_gain, TAG_acceptance where TAG is a 3-letter tag.
_TARGETED_MODIFIER_RE = re.compile(r"^[A-Z]{2,3}_[a-z]")

# A modifier name is lowercase with underscores (and optionally digits).
# Some MD custom modifiers use mixed case (e.g. MD_something) — allow those.
_MODIFIER_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$|^[A-Z][A-Za-z0-9_]*$")

# Minimum frequency threshold for a modifier name to be "known good"
_FREQUENCY_THRESHOLD = 3

# Parametric modifier families. HOI4 generates one concrete modifier per game
# entity for each of these — e.g. the building infrastructure yields
# state_repair_speed_infrastructure_factor, the trait superior_tactician yields
# trait_superior_tactician_xp_gain_factor. They are valid but appear too rarely,
# or only in decision files, to clear the frequency threshold.
#
# Sourced from resources/documentation/modifiers_documentation.md. Families with
# an over-broad generic suffix (<ModifierStat>_factor, <Technology>_cost_factor,
# <IdeaGroup>_cost_factor, <Operation>_cost/_outcome/_risk,
# <SpecialProject>_speed_factor) are deliberately omitted — a regex for them
# would whitelist genuine typos.
_PARAMETRIC_MODIFIER_PATTERNS: Tuple[re.Pattern, ...] = tuple(
    re.compile(p)
    for p in (
        # <Building>-keyed
        r"^(?:state_)?repair_speed_[a-z][a-z0-9_]*_factor$",
        r"^(?:state_)?production_speed_[a-z][a-z0-9_]*_factor$",
        r"^production_cost_[a-z][a-z0-9_]*_factor$",
        r"^(?:state_)?[a-z][a-z0-9_]*_max_level_terrain_limit$",
        # <Trait>-keyed (covers the bare and trait_-prefixed forms)
        r"^[a-z][a-z0-9_]*_xp_gain_factor$",
        # <Unit>-keyed
        r"^experience_gain_[a-z][a-z0-9_]*_(?:combat|mission|training)_factor$",
        # <Equipment> / <EquipmentModule> / <Unit>-keyed design cost
        r"^[a-z][a-z0-9_]*_design_cost_factor$",
        r"^production_cost_max_[a-z][a-z0-9_]*$",
        # <Doctrine>-keyed (covers _mastery_gain and _track_mastery_gain)
        r"^[a-z][a-z0-9_]*_mastery_gain_factor$",
        r"^[a-z][a-z0-9_]*_doctrine_cost_factor$",
        # <Ideology>-keyed
        r"^[a-z][a-z0-9_]*_drift(?:_from_guarantees)?$",
        r"^[a-z][a-z0-9_]*_acceptance$",
        # <CombatTactic>-keyed
        r"^[a-z][a-z0-9_]*_preferred_weight_factor$",
        # <IdeaCategory>-keyed
        r"^[a-z][a-z0-9_]*_category_type_cost_factor$",
        # <Resource>-keyed
        r"^country_resource_(?:cost_)?[a-z][a-z0-9_]*$",
        r"^state_resource_(?:cost_)?[a-z][a-z0-9_]*$",
        r"^state_resources_[a-z][a-z0-9_]*_factor$",
        r"^local_resources_[a-z][a-z0-9_]*_factor$",
        r"^temporary_state_resource_[a-z][a-z0-9_]*$",
    )
)


def _extract_modifier_blocks(text: str) -> List[Tuple[int, str]]:
    """Extract the body text and start line of each top-level modifier = { } block.

    Returns a list of (line_number, block_body) tuples.
    Skips modifier blocks that are clearly AI weight blocks (first non-empty
    key is factor/base/add followed by a trigger condition, not a number-only
    value that a pure game modifier would have).

    Only returns blocks that are NOT inside ai_will_do, ai_research_weights,
    targeted_modifier, equipment_bonus, or research_bonus parents.
    """
    results: List[Tuple[int, str]] = []
    i = 0
    n = len(text)

    # Track contextual depth — when we're inside a skip-block, don't harvest
    # modifier blocks from within it.
    skip_depth_stack: List[int] = []  # stack of depths at which skip-blocks started
    current_depth = 0

    lines = text.split("\n")
    # Build a cumulative-offset table so we can map char offset → line number
    cum_offsets: List[int] = []
    off = 0
    for line in lines:
        cum_offsets.append(off)
        off += len(line) + 1  # +1 for \n

    def char_to_lineno(pos: int) -> int:
        lo, hi = 0, len(cum_offsets) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if cum_offsets[mid] <= pos:
                lo = mid
            else:
                hi = mid - 1
        return lo + 1  # 1-based

    i = 0
    current_depth = 0
    in_string = False

    while i < n:
        ch = text[i]

        if ch == '"':
            in_string = not in_string
            i += 1
            continue

        if in_string:
            i += 1
            continue

        if ch == "{":
            current_depth += 1
            i += 1
            continue

        if ch == "}":
            if skip_depth_stack and current_depth == skip_depth_stack[-1]:
                skip_depth_stack.pop()
            current_depth -= 1
            i += 1
            continue

        if ch.isalpha() or ch == "_":
            j = i
            while j < n and (text[j].isalnum() or text[j] == "_"):
                j += 1
            word = text[i:j]
            k = j
            while k < n and text[k] in " \t":
                k += 1
            if k < n and text[k] == "=":
                k += 1
                while k < n and text[k] in " \t":
                    k += 1
                if k < n and text[k] == "{":
                    if word in _SKIP_BLOCK_KEYS:
                        # Mark depth at which this skip-block opens
                        # The { hasn't been counted yet, so after we pass it
                        # depth becomes current_depth + 1
                        skip_depth_stack.append(current_depth + 1)
                    elif word == "modifier" and not skip_depth_stack:
                        block_lineno = char_to_lineno(i)
                        body_start = k + 1
                        depth = 1
                        p = body_start
                        in_str2 = False
                        while p < n and depth > 0:
                            c = text[p]
                            if c == '"':
                                in_str2 = not in_str2
                            elif not in_str2:
                                if c == "{":
                                    depth += 1
                                elif c == "}":
                                    depth -= 1
                            p += 1
                        body = text[body_start : p - 1]
                        results.append((block_lineno, body))
                        i = p
                        continue
            i = j
            continue

        i += 1

    return results


def _is_ai_weight_block(body: str) -> bool:
    """Return True if this modifier block body looks like an AI weight modifier.

    AI weight modifier blocks (inside ai_will_do, random_list, etc.) contain
    ``factor``, ``base``, or ``add`` as a key. Game modifier blocks contain
    only modifier_name = <number> lines. If either of those indicator keys
    appears anywhere in the block, it is an AI weight block.

    Also flags blocks whose first key has a non-numeric value (trigger conditions
    like ``has_idea``, ``OR = {``, comparison operators) — these are always weight
    blocks even if factor/base/add hasn't been seen yet.
    """
    # An indicator key anywhere in the body marks an AI weight block, even when
    # it follows the modifier lines (e.g. `has_decision = X` then `factor = 1.25`).
    for indicator in _AI_WEIGHT_INDICATOR_KEYS:
        if re.search(r"\b" + indicator + r"\s*=", body):
            return True

    for line in body.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)", stripped)
        if m:
            val = m.group(2).strip()
            # Non-numeric values (trigger conditions, booleans, block openers)
            if val.startswith("{") or any(op in val for op in ("<", ">", "yes", "no")):
                return True
        break
    return False


def _extract_modifier_names_from_body(body: str) -> List[str]:
    """Extract modifier key names from a modifier block body.

    Skips:
    - Lines that open sub-blocks (key = { ... })
    - Non-modifier structural keys (factor, base, tag, icon, etc.)
    - Targeted modifier entries (XXX_opinion where XXX is a country tag)
    - Anything that doesn't look like a valid modifier name
    """
    names: List[str] = []
    # Only look at top-level keys in the body (depth 0)
    depth = 0
    in_string = False
    lines = body.split("\n")
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        opens = stripped.count("{") - stripped.count("}")
        # A line opening a sub-block names that block, not a modifier — skip it.
        if "{" in stripped:
            depth += opens
            continue
        if "}" in stripped:
            depth += opens  # opens is negative here
            continue

        if depth != 0:
            continue

        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=", stripped)
        if not m:
            continue
        key = m.group(1)

        if key in _NON_MODIFIER_KEYS:
            continue
        if _TARGETED_MODIFIER_RE.match(key):
            continue
        if not _MODIFIER_NAME_RE.match(key):
            continue

        names.append(key)
    return names


# ---------------------------------------------------------------------------
# Pool workers (module-level for pickling)
# ---------------------------------------------------------------------------


def _harvest_modifiers_from_file(filepath: str) -> List[str]:
    """Pool worker: extract all modifier names from a single file.

    Used for building the known-good frequency table.
    """
    if should_skip_file(filepath):
        return []
    text = FileOpener.open_text_file(
        filepath, lowercase=False, strip_comments_flag=True
    )
    if not text or "modifier" not in text:
        return []

    names: List[str] = []
    for _lineno, body in _extract_modifier_blocks(text):
        if _is_ai_weight_block(body):
            continue
        names.extend(_extract_modifier_names_from_body(body))
    return names


def _harvest_flat_modifiers_from_traits_file(filepath: str) -> List[str]:
    """Pool worker: extract top-level modifier keys from traits files.

    Traits files (common/country_leader/*.txt, common/characters/*.txt) often
    place modifier keys directly at the trait body level (not in modifier = {}).
    We harvest these to supplement the known-good set.
    """
    if should_skip_file(filepath):
        return []
    text = FileOpener.open_text_file(
        filepath, lowercase=False, strip_comments_flag=True
    )
    if not text:
        return []

    # Collect keys that appear at depth 2 (inside leader_traits = { trait = { KEY = VAL } })
    # We do a simple heuristic: any `[a-z_]+ = <number>` at exactly 2 braces deep.
    names: List[str] = []
    depth = 0
    in_string = False
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        opens = stripped.count("{")
        closes = stripped.count("}")
        new_depth = depth + opens - closes
        # At depth 2 we're inside a trait body
        if depth == 2 and opens == 0 and closes == 0:
            m = re.match(r"^([a-z][a-z0-9_]*)\s*=\s*(-?[0-9])", stripped)
            if m:
                key = m.group(1)
                if key not in _NON_MODIFIER_KEYS and _MODIFIER_NAME_RE.match(key):
                    names.append(key)
        depth = new_depth
    return names


def _is_parametric_modifier(name: str) -> bool:
    """True if ``name`` matches a parametric HOI4 modifier family.

    See _PARAMETRIC_MODIFIER_PATTERNS — these are engine-generated per-entity
    modifiers that are valid but too rare to clear the frequency threshold.
    """
    return any(pattern.match(name) for pattern in _PARAMETRIC_MODIFIER_PATTERNS)


def _check_file_for_unknown_modifiers(
    args: Tuple[str, FrozenSet[str], str],
) -> List[Tuple[str, str, int]]:
    """Pool worker: find unknown modifier names in a single file.

    Returns a list of (modifier_name, rel_path, line_number) tuples.
    """
    filepath, known_good, mod_path = args
    if should_skip_file(filepath):
        return []
    text = FileOpener.open_text_file(
        filepath, lowercase=False, strip_comments_flag=True
    )
    if not text or "modifier" not in text:
        return []

    results: List[Tuple[str, str, int]] = []
    rel = os.path.relpath(filepath, mod_path)

    for lineno, body in _extract_modifier_blocks(text):
        if _is_ai_weight_block(body):
            continue
        for name in _extract_modifier_names_from_body(body):
            if name not in known_good:
                results.append((name, rel, lineno))

    return results


# ---------------------------------------------------------------------------
# Validator class
# ---------------------------------------------------------------------------


class Validator(BaseValidator):
    TITLE = "MODIFIER NAME VALIDATION"
    STAGED_EXTENSIONS = [".txt"]

    # Source directories for harvesting the known-good modifier set.
    # Always scanned in full regardless of staged mode.
    _HARVEST_PATTERNS: List[str] = [
        "common/ideas/**/*.txt",
        "common/national_focus/**/*.txt",
        "common/country_leader/**/*.txt",
        "common/characters/**/*.txt",
        "common/dynamic_modifiers/**/*.txt",
        "common/modifiers/**/*.txt",
        "common/opinion_modifiers/**/*.txt",
    ]

    # Explicit modifier definition directories — every top-level key is a valid
    # modifier name regardless of usage frequency.
    _DEFINITION_PATTERNS: List[str] = [
        "common/modifiers/**/*.txt",
        "common/dynamic_modifiers/**/*.txt",
        "common/modifier_definitions/**/*.txt",
    ]

    # Source patterns for validation targets
    _VALIDATE_PATTERNS: List[str] = [
        "common/ideas/**/*.txt",
        "common/national_focus/**/*.txt",
        "common/dynamic_modifiers/**/*.txt",
        "common/decisions/**/*.txt",
    ]

    def __init__(self, mod_path: str, **kwargs):
        super().__init__(mod_path, **kwargs)

    def _build_known_good_set(self) -> FrozenSet[str]:
        """Scan the codebase to build a frequency table of modifier names.

        Names that appear 3+ times across all source files are considered
        "known good". Names from custom MD modifier definition files are
        always added regardless of frequency.

        Returns a frozenset of known-good modifier names.
        """
        self.log("  Building known-good modifier set from codebase...")

        # Always scan the full codebase for the reference set
        saved = self.staged_only
        self.staged_only = False
        harvest_files = self._collect_files(self._HARVEST_PATTERNS)
        self.staged_only = saved

        self.log(f"  Harvesting from {len(harvest_files)} files...")

        # Traits files use flat modifier keys, not modifier = {} blocks
        traits_files = [
            f for f in harvest_files if "country_leader" in f or "characters" in f
        ]
        other_files = [f for f in harvest_files if f not in set(traits_files)]

        all_names: List[str] = []

        # Harvest modifier = {} blocks from main files
        block_results = self._pool_map(
            _harvest_modifiers_from_file, other_files, chunksize=50
        )
        for batch in block_results:
            all_names.extend(batch)

        # Harvest flat keys from traits files
        trait_results = self._pool_map(
            _harvest_flat_modifiers_from_traits_file, traits_files, chunksize=50
        )
        for batch in trait_results:
            all_names.extend(batch)

        freq = Counter(all_names)
        known_good: Set[str] = {
            name for name, count in freq.items() if count >= _FREQUENCY_THRESHOLD
        }

        # Also collect names explicitly defined in modifier definition files
        # (common/modifiers/, common/dynamic_modifiers/, common/modifier_definitions/).
        # These are always valid regardless of frequency.
        definition_files = self._collect_files(
            self._DEFINITION_PATTERNS,
            ignore_staged=True,
        )
        def_name_re = re.compile(r"^\s*([a-z][a-z0-9_]*)\s*=\s*", re.MULTILINE)
        for filepath in definition_files:
            try:
                with open(filepath, encoding="utf-8-sig") as fh:
                    content = fh.read()
            except Exception:
                continue
            # In modifier definition files, top-level keys ARE modifier names
            # (they appear inside a named block like weather_rain = { KEY = val })
            for m in def_name_re.finditer(content):
                key = m.group(1)
                if key not in _NON_MODIFIER_KEYS and _MODIFIER_NAME_RE.match(key):
                    known_good.add(key)

        self.log(
            f"  Known-good modifier set: {len(known_good)} names "
            f"(from {len(freq)} total harvested, threshold={_FREQUENCY_THRESHOLD})"
        )
        return frozenset(known_good)

    def validate_modifier_names(self, known_good: FrozenSet[str]):
        """Check modifier blocks in idea/focus/decision/dynamic_modifier files."""
        self._log_section("Checking modifier names in ideas, focuses, and decisions...")

        target_files = self._collect_files(self._VALIDATE_PATTERNS)
        self.log(f"  Checking {len(target_files)} files...")

        args_list = [(f, known_good, self.mod_path) for f in target_files]
        raw_results = self._pool_map(
            _check_file_for_unknown_modifiers, args_list, chunksize=30
        )

        # Collect and deduplicate
        seen: Set[Tuple[str, str, int]] = set()
        unknown_errors: List[Tuple[str, str, int]] = []

        for batch in raw_results:
            for name, rel, lineno in batch:
                key = (name, rel, lineno)
                if key in seen:
                    continue
                seen.add(key)
                # Modifiers prefixed with MD_ or md_ are always valid (custom MD)
                if name.startswith("MD_") or name.startswith("md_"):
                    continue
                # Engine-generated parametric modifier families (per building,
                # trait, unit, doctrine, resource, etc.)
                if _is_parametric_modifier(name):
                    continue
                unknown_errors.append((name, rel, lineno))

        # Format for _report: (message, file, line)
        formatted = [
            (f"Unknown modifier '{name}'", rel, lineno)
            for name, rel, lineno in sorted(unknown_errors, key=lambda x: (x[1], x[2]))
        ]

        self._report(
            formatted,
            "No unknown modifier names found",
            "Unknown modifier names (compile silently, do nothing in-game):",
            severity=Severity.WARNING,
            category="unknown-modifier",
        )

    def run_validations(self):
        known_good = self._build_known_good_set()
        self.validate_modifier_names(known_good)


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate modifier names in Millennium Dawn mod",
    )
