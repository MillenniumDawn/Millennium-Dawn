#!/usr/bin/env python3
"""Validate modifier names inside modifier = {} blocks in Millennium Dawn.

Builds a known-good set from authoritative documentation and explicit modifier
definitions. Targeted modifiers (XXX_opinion, XXX_autonomy_gain) are skipped.
"""

import os
import re
import sys
from typing import Dict, FrozenSet, List, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import disk_cache
from shared_utils import compute_line_offsets, extract_block_from_text, line_for_offset
from validator_common import (
    BaseValidator,
    FileOpener,
    Severity,
    run_validator_main,
    should_skip_file,
)

# HOI4 structural / ai-weight / targeted-modifier keys that appear inside
# blocks named "modifier" but carry no game-modifier meaning.
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
        # Vanilla dynamic-modifier flag: "if yes this modifier will also be
        # read in combat" (documented in vanilla 0_dynamic_modifiers.txt).
        "attacker_modifier",
        "custom_modifier_tooltip",
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

_SKIP_BLOCK_KEYS: FrozenSet[str] = frozenset(
    {
        "targeted_modifier",
        "equipment_bonus",
        "research_bonus",
        "ai_will_do",
        "ai_research_weights",
    }
)

# Parametric/targeted modifier entries (e.g. TAG_opinion, TAG_autonomy_gain) — skip these.
_TARGETED_MODIFIER_RE = re.compile(r"^[A-Z]{2,3}_[a-z]")

# A modifier name is lowercase with underscores (and optionally digits).
# Some MD custom modifiers use mixed case (e.g. MD_something) — allow those.
_MODIFIER_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$|^[A-Z][A-Za-z0-9_]*$")

# Parametric modifier families. HOI4 generates one concrete modifier per game
# entity for each of these, e.g. the building infrastructure yields
# state_repair_speed_infrastructure_factor and the trait superior_tactician yields
# trait_superior_tactician_xp_gain_factor.
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

    # Map char offset → 1-based line number via the shared bisect helper.
    _line_offsets = compute_line_offsets(text)

    def char_to_lineno(pos: int) -> int:
        return line_for_offset(_line_offsets, pos)

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


def _extract_modifier_entries_from_body(body: str) -> List[Tuple[str, int]]:
    """Extract (modifier key name, 0-based line offset within body) pairs.

    Skips:
    - Lines that open sub-blocks (key = { ... })
    - Non-modifier structural keys (factor, base, tag, icon, etc.)
    - Targeted modifier entries (XXX_opinion where XXX is a country tag)
    - Anything that doesn't look like a valid modifier name
    """
    entries: List[Tuple[str, int]] = []
    # Only look at top-level keys in the body (depth 0)
    depth = 0
    lines = body.split("\n")
    for offset, line in enumerate(lines):
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

        entries.append((key, offset))
    return entries


def _extract_modifier_names_from_body(body: str) -> List[str]:
    """Extract modifier key names from a modifier block body. See
    _extract_modifier_entries_from_body for the skip rules."""
    return [name for name, _offset in _extract_modifier_entries_from_body(body)]


def _is_parametric_modifier(name: str) -> bool:
    """True if ``name`` matches a parametric HOI4 modifier family.

    See _PARAMETRIC_MODIFIER_PATTERNS. These are engine-generated per-entity
    modifiers documented by the vanilla modifier reference.
    """
    return any(pattern.match(name) for pattern in _PARAMETRIC_MODIFIER_PATTERNS)


# Vanilla modifier reference doc. Each `## name` section is a concrete modifier;
# each `## <span id="...">` section is a parametric family whose concrete
# members are listed on a `**Modified types**:` line. The span anchor encodes
# the placeholder position as `-word-`, so the template is recoverable.
_DOC_REL_PATH = os.path.join("resources", "documentation", "modifiers_documentation.md")
_DOC_CONCRETE_RE = re.compile(r"^## ([a-z][a-z0-9_]*)\s*$", re.MULTILINE)
_DOC_MODIFIED_TYPES_RE = re.compile(r"\*\*Modified types\*\*:\s*(.+)")
_DOC_SPAN_PLACEHOLDER_RE = re.compile(r"-([a-z0-9]+)-")

# modifier_army_sub_unit_<Unit>_attack/defence_factor is only documented as a
# concrete per-vanilla-unit listing (no <span> template — every vanilla sub-unit
# type gets its own header), but the engine generates the same pair for any
# sub_units entry, including MD's own. Expand these against harvested MD names
# the same way as the doc's genuine unit-keyed templates.
_EXTRA_UNIT_TEMPLATES: Tuple[str, ...] = (
    "modifier_army_sub_unit_{}_attack_factor",
    "modifier_army_sub_unit_{}_defence_factor",
)


def _load_documented_modifiers(
    doc_path: str,
) -> Tuple[Set[str], Dict[str, List[str]]]:
    """Build a known-good set + parametric templates from the vanilla modifier documentation.

    Adds every concrete `## name` header, then expands each parametric family
    (`## <span id="-building-_max_level_terrain_limit">…`) against its
    documented **Modified types** list. Expansion is exact — only entities the
    doc actually lists pass — so it never whitelists a typo the way a broad
    `<anything>_factor` regex would.

    Also returns every single-placeholder template grouped by its placeholder
    word (e.g. "unit" -> ["experience_gain_{}_training_factor", ...]) so callers
    can expand a family against a name list not documented in the vanilla doc
    (MD's own sub-units). Returns ({}, {}) if the doc is missing.
    """
    try:
        with open(doc_path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return set(), {}

    names: Set[str] = set(_DOC_CONCRETE_RE.findall(text))
    templates_by_word: Dict[str, List[str]] = {}

    for section in re.split(r"^## ", text, flags=re.MULTILINE):
        m = re.match(r'<span id="([^"]+)">', section)
        if not m:
            continue
        anchor = m.group(1)
        template = re.sub(r"-[a-z0-9]+-", "{}", anchor)
        if "{}" not in template:
            continue
        words = _DOC_SPAN_PLACEHOLDER_RE.findall(anchor)
        if len(words) == 1:
            templates_by_word.setdefault(words[0], []).append(template)
        types_line = _DOC_MODIFIED_TYPES_RE.search(section)
        if not types_line:
            continue
        for entity in types_line.group(1).split(","):
            entity = entity.strip()
            if not _MODIFIER_NAME_RE.match(entity):
                continue
            try:
                concrete = template.format(entity)
            except (IndexError, KeyError):
                continue
            if _MODIFIER_NAME_RE.match(concrete):
                names.add(concrete)

    return names, templates_by_word


_IDEA_SLOT_RE = re.compile(r"^\s*(?:character_)?slot\s*=\s*([A-Za-z][A-Za-z0-9_]*)")


def _harvest_idea_slot_cost_factors(idea_tags_files: List[str]) -> Set[str]:
    """Every idea slot auto-generates a `<slot>_cost_factor` modifier.

    Harvest the slot names from common/idea_tags and register the generated
    modifier directly. Case is preserved to match usage.
    """
    names: Set[str] = set()
    for filepath in idea_tags_files:
        try:
            with open(filepath, encoding="utf-8-sig") as fh:
                content = fh.read()
        except OSError:
            continue
        for line in content.splitlines():
            m = _IDEA_SLOT_RE.match(line)
            if m:
                names.add(f"{m.group(1)}_cost_factor")
    return names


def _extract_top_level_definition_blocks(text: str) -> List[Tuple[str, int, str]]:
    """Return (name, line, body) for blocks assigned at file scope."""
    blocks: List[Tuple[str, int, str]] = []
    cursor = 0
    in_string = False
    while cursor < len(text):
        char = text[cursor]
        if char == '"':
            in_string = not in_string
            cursor += 1
            continue
        if in_string or not (char.isalpha() or char == "_"):
            cursor += 1
            continue

        end_name = cursor + 1
        while end_name < len(text) and (
            text[end_name].isalnum() or text[end_name] == "_"
        ):
            end_name += 1
        equals = end_name
        while equals < len(text) and text[equals].isspace():
            equals += 1
        if equals >= len(text) or text[equals] != "=":
            cursor = end_name
            continue
        opener = equals + 1
        while opener < len(text) and text[opener].isspace():
            opener += 1
        if opener >= len(text) or text[opener] != "{":
            cursor = end_name
            continue

        body, end = extract_block_from_text(text, opener)
        if end == -1:
            break
        line = text.count("\n", 0, cursor) + 1
        blocks.append((text[cursor:end_name], line, body))
        cursor = end
    return blocks


def _extract_top_level_definition_names(text: str) -> Set[str]:
    """Return valid names assigned to blocks at the file's top level."""
    return {
        name
        for name, _line, _body in _extract_top_level_definition_blocks(text)
        if _MODIFIER_NAME_RE.match(name) and name not in _NON_MODIFIER_KEYS
    }


def _harvest_md_sub_unit_names(unit_files: List[str]) -> Set[str]:
    """Sub-unit type names defined under top-level ``sub_units = { ... }`` blocks.

    Unit files can carry other top-level blocks (equipment filters, etc.), so
    only the sub_units block's own top-level keys are harvested.
    """
    names: Set[str] = set()
    for filepath in unit_files:
        text = FileOpener.open_text_file(
            filepath, lowercase=False, strip_comments_flag=True
        )
        if not text or "sub_units" not in text:
            continue
        for name, _line, body in _extract_top_level_definition_blocks(text):
            if name != "sub_units":
                continue
            for sub_name, _l, _b in _extract_top_level_definition_blocks(body):
                names.add(sub_name)
    return names


def _harvest_md_operation_names(operation_files: List[str]) -> Set[str]:
    """Operation names — every top-level block in common/operations files."""
    names: Set[str] = set()
    for filepath in operation_files:
        text = FileOpener.open_text_file(
            filepath, lowercase=False, strip_comments_flag=True
        )
        if not text:
            continue
        for name, _line, _body in _extract_top_level_definition_blocks(text):
            names.add(name)
    return names


def _extract_dynamic_modifier_names(text: str) -> List[Tuple[str, int]]:
    """Return names and lines of top-level dynamic modifier definitions."""
    return [
        (name, line) for name, line, _body in _extract_top_level_definition_blocks(text)
    ]


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
    rel = os.path.relpath(filepath, mod_path)
    is_dynamic = rel.replace("\\", "/").startswith("common/dynamic_modifiers/")
    if not text or ("modifier" not in text and not is_dynamic):
        return []

    def _compute():
        # Parse all modifier names in the file (independent of known_good so the
        # cached value is a pure function of file content); the known_good filter
        # is applied below on the cached result.
        parsed: List[Tuple[str, str, int]] = []
        if is_dynamic:
            # Dynamic modifier blocks can run to dozens of keys — report each
            # key's own line instead of the enclosing block's header line.
            for _name, block_line, body in _extract_top_level_definition_blocks(text):
                for name, offset in _extract_modifier_entries_from_body(body):
                    parsed.append((name, rel, block_line + offset))
        else:
            for lineno, body in _extract_modifier_blocks(text):
                if _is_ai_weight_block(body):
                    continue
                for name in _extract_modifier_names_from_body(body):
                    parsed.append((name, rel, lineno))
        return parsed

    parsed = disk_cache.per_file_cached_by_content(
        mod_path, "modifiers.check.v2", filepath, text, _compute
    )

    return [
        (name, rel, lineno) for name, rel, lineno in parsed if name not in known_good
    ]


class Validator(BaseValidator):
    TITLE = "MODIFIER NAME VALIDATION"
    STAGED_EXTENSIONS = [".txt"]

    # Explicit modifier definitions. Static and dynamic modifier files consume
    # modifier keys inside their top-level blocks; they do not define those keys.
    _DEFINITION_PATTERNS: List[str] = ["common/modifier_definitions/**/*.txt"]

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
        """Build the known-good set from authoritative modifier sources."""
        self.log("  Building known-good modifier set...")

        known_good: Set[str] = set()

        # Collect names explicitly defined in modifier definition files.
        definition_files = self._collect_files(
            self._DEFINITION_PATTERNS,
            ignore_staged=True,
        )
        for filepath in definition_files:
            content = FileOpener.open_text_file(
                filepath, lowercase=False, strip_comments_flag=True
            )
            if not content:
                continue
            known_good.update(_extract_top_level_definition_names(content))

        # Authoritative vanilla reference — concrete modifiers plus parametric
        # families expanded against their documented Modified types.
        doc_path = os.path.join(self.mod_path, _DOC_REL_PATH)
        documented, templates_by_word = _load_documented_modifiers(doc_path)
        if not documented:
            self.log(
                f"  WARNING: {_DOC_REL_PATH} missing or empty — known-good set is "
                "missing ~4000 vanilla modifiers, expect false positives. Ensure "
                "resources/documentation is checked out (CI sparse-checkout)."
            )
        known_good |= documented

        # Engine-generated <slot>_cost_factor modifiers from every idea slot.
        idea_tag_files = self._collect_files(
            ["common/idea_tags/**/*.txt"], ignore_staged=True
        )
        slot_factors = _harvest_idea_slot_cost_factors(idea_tag_files)
        known_good |= slot_factors

        # Engine-generated per-sub-unit modifiers (unit-keyed doc templates plus
        # modifier_army_sub_unit_*, doc-concrete for vanilla only) for MD's own
        # sub_units entries — the vanilla doc has no MD unit names to expand against.
        unit_files = self._collect_files(["common/units/**/*.txt"], ignore_staged=True)
        md_sub_units = _harvest_md_sub_unit_names(unit_files)
        unit_templates = list(templates_by_word.get("unit", [])) + list(
            _EXTRA_UNIT_TEMPLATES
        )
        sub_unit_modifiers = {
            template.format(name)
            for template in unit_templates
            for name in md_sub_units
        }
        known_good |= sub_unit_modifiers

        # Same for operation-keyed families (<Operation>_cost/_outcome/_risk):
        # the doc's Modified types only list vanilla operations, so expand the
        # templates against MD's own common/operations definitions too.
        operation_files = self._collect_files(
            ["common/operations/**/*.txt"], ignore_staged=True
        )
        md_operations = _harvest_md_operation_names(operation_files)
        operation_modifiers = {
            template.format(name)
            for template in templates_by_word.get("operation", [])
            for name in md_operations
        }
        known_good |= operation_modifiers

        self.log(
            f"  Known-good modifier set: {len(known_good)} names "
            f"({len(documented)} documented, {len(slot_factors)} slot cost factors, "
            f"{len(sub_unit_modifiers)} MD sub-unit modifiers, "
            f"{len(operation_modifiers)} MD operation modifiers)"
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

        # Report each unknown name once. Repeated use is not proof of validity and
        # should not produce hundreds of identical findings either.
        unknown_errors: Dict[str, Tuple[str, int]] = {}

        for batch in raw_results:
            for name, rel, lineno in batch:
                # Modifiers prefixed with MD_ or md_ are always valid (custom MD)
                if name.startswith("MD_") or name.startswith("md_"):
                    continue
                # Engine-generated parametric modifier families (per building,
                # trait, unit, doctrine, resource, etc.)
                if _is_parametric_modifier(name):
                    continue
                unknown_errors.setdefault(name, (rel, lineno))

        # Format for _report: (message, file, line)
        formatted = [
            (f"Unknown modifier '{name}'", rel, lineno)
            for name, (rel, lineno) in sorted(
                unknown_errors.items(), key=lambda item: (item[1][0], item[1][1])
            )
        ]

        self._report(
            formatted,
            "No unknown modifier names found",
            "Unknown modifier names (compile silently, do nothing in-game):",
            severity=Severity.WARNING,
            category="unknown-modifier",
        )

    def validate_dynamic_modifier_name_loc(self):
        """Check that dynamic modifiers with a _TT/_desc loc entry also have a
        bare-name loc key — the in-game modifier header renders the bare key,
        so a missing one shows the literal token to players."""
        self._log_section("Checking dynamic modifier name loc references...")

        loc_keys = self._load_localisation_keys()
        files = self._collect_files(
            ["common/dynamic_modifiers/**/*.txt"], ignore_staged=True
        )
        self.log(f"  Found {len(files)} dynamic modifier files to check")

        results = []
        for filepath in files:
            if should_skip_file(filepath):
                continue
            text = FileOpener.open_text_file(
                filepath, lowercase=False, strip_comments_flag=True
            )
            if not text:
                continue
            rel = os.path.relpath(filepath, self.mod_path)
            names = disk_cache.per_file_cached_by_content(
                self.mod_path,
                "modifiers.dynamic_names",
                filepath,
                text,
                lambda text=text: _extract_dynamic_modifier_names(text),
            )
            for name, lineno in names:
                has_tt_or_desc = f"{name}_TT" in loc_keys or f"{name}_desc" in loc_keys
                if has_tt_or_desc and name not in loc_keys:
                    results.append(
                        (
                            f"Dynamic modifier '{name}' has a _TT/_desc loc entry but "
                            f"no bare '{name}' key (in-game header shows the literal token)",
                            rel,
                            lineno,
                        )
                    )

        self._report(
            results,
            "✓ All dynamic modifiers with _TT/_desc loc have a bare-name key",
            "Dynamic modifiers missing a bare-name loc key:",
            severity=Severity.WARNING,
            category="dynamic-modifier-name-loc",
        )

    def run_validations(self):
        known_good = self._build_known_good_set()
        self.validate_modifier_names(known_good)
        self.validate_dynamic_modifier_name_loc()


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate modifier names in Millennium Dawn mod",
    )
