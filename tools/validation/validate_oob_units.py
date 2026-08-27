#!/usr/bin/env python3
# Validate that unit names in OOB files, AI templates, and namelists reference
# canonical sub-unit definitions from common/units/*.txt, suggesting the closest
# case-insensitive match for likely typos.
#
# Namelist blocks accept both sub_unit names AND equipment-type names (air
# namelists use keys like small_plane_airframe), so the canonical set for
# namelist validation extends the sub_unit set with equipment names extracted
# from `need = { ... }` blocks inside sub_unit definitions.
import glob
import os
import re
import sys
from difflib import get_close_matches
from typing import Any, Dict, List, Optional, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import disk_cache
from equipment_module_slots import (
    Finding,
    _iter_blocks,
    _iter_named_blocks,
    _scalar,
    blank_comments,
    build_equipment_index,
    check_created_variants,
    parse_variant_names,
)
from shared_utils import get_staged_files, read_text_under
from validator_common import (
    BaseValidator,
    Issue,
    Severity,
    run_validator_main,
    strip_comments,
)

_VARIANT_SLOT_CATEGORIES = {
    "unknown_hull": "SHIP VARIANT: unknown hull type",
    "unknown_slot": "SHIP VARIANT: slot not on hull",
    "unknown_module": "SHIP VARIANT: unknown module reference",
    "category_mismatch": "SHIP VARIANT: module category not allowed in slot",
}

_EQUIPMENT_VARIANT_SLOT_CATEGORIES = {
    "unknown_hull": "EQUIPMENT VARIANT: unknown hull type",
    "unknown_slot": "EQUIPMENT VARIANT: slot not on hull",
    "unknown_module": "EQUIPMENT VARIANT: unknown module reference",
    "category_mismatch": "EQUIPMENT VARIANT: module category not allowed in slot",
}

# Every directory where a create_equipment_variant effect actually appears.
_VARIANT_SOURCE_PATTERNS = [
    "history/countries/*.txt",
    "common/national_focus/*.txt",
    "events/*.txt",
    "common/decisions/*.txt",
    "common/special_projects/*.txt",
    "common/scripted_effects/*.txt",
]

_VARIANT_REF_CATEGORIES = {
    "unknown_variant": "OOB SHIP: version_name has no matching equipment variant",
    "attributed_archetype": "PRODUCTION: archetype attributed to a producer",
}

# The archetype rule only covers startup-loaded history. Focus and event rewards
# use the archetype+producer form in ~300 places as an established idiom, and
# there the fallback picks a sensible concrete equipment.
_HISTORY_PRODUCTION_PATTERNS = [
    "history/units/*.txt",
    "history/countries/*.txt",
]

_OOB_EQUIPMENT_RE = re.compile(
    r"equipment\s*=\s*\{\s*([A-Za-z_]\w*)\s*=\s*\{([^{}]*)\}"
)
_VERSION_NAME_RE = re.compile(r'\bversion_name\s*=\s*"([^"]*)"')
_OOB_CREATOR_RE = re.compile(r'\bcreator\s*=\s*"?([A-Za-z_]\w*)"?')
_OOB_OWNER_RE = re.compile(r'\bowner\s*=\s*"?([A-Za-z_]\w*)"?')
_PRODUCER_RE = re.compile(r'\b(?:creator|producer)\s*=\s*"?([A-Za-z_]\w*)"?')
_LOAD_OOB_RE = re.compile(r'\bload_oob\s*=\s*(?:"([^"]+)"|([A-Za-z_]\w*))')

# create_unit and runtime load_oob appear in these sources.
_CREATE_UNIT_SOURCE_PATTERNS = _VARIANT_SOURCE_PATTERNS + [
    "common/on_actions/*.txt",
    "common/operations/*.txt",
    "common/resistance_compliance_modifiers/*.txt",
    "common/scripted_guis/*.txt",
]


def _read_text(filepath: str, under: str) -> str:
    try:
        return read_text_under(filepath, under)
    except (OSError, ValueError):
        return ""


def find_load_oob_references(content: str) -> List[Tuple[str, int]]:
    """Return literal load_oob targets and their line numbers."""
    refs = []
    content = strip_comments(content)
    for match in _LOAD_OOB_RE.finditer(content):
        target = match.group(1) or match.group(2)
        if "$" in target or "[" in target:
            continue
        refs.append((target, content.count("\n", 0, match.start()) + 1))
    return refs


def _parse_canonical_units_file(content: str) -> Set[str]:
    """Extract canonical sub-unit names from one common/units/*.txt file's content.

    Unit names are top-level identifiers inside sub_units = { ... } blocks.
    """
    canonical = set()
    content = strip_comments(content)
    lines = content.split("\n")
    i = 0
    in_sub_units = False
    brace_depth = 0
    unit_brace_depth = 0
    in_unit_def = False

    while i < len(lines):
        line = lines[i].strip()

        if not in_sub_units:
            if re.match(r"^sub_units\s*=\s*\{", line):
                in_sub_units = True
                brace_depth = 1
                i += 1
                continue
            i += 1
            continue

        # Count braces on this line
        for ch in line:
            if ch == "{":
                brace_depth += 1
            elif ch == "}":
                brace_depth -= 1

        if brace_depth <= 0:
            in_sub_units = False
            i += 1
            continue

        # At depth 1 inside sub_units, look for unit_name = {
        if not in_unit_def:
            match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\{", line)
            if match and brace_depth >= 2:
                canonical.add(match.group(1))
                in_unit_def = True
                unit_brace_depth = brace_depth
        else:
            if brace_depth < unit_brace_depth:
                in_unit_def = False

        i += 1

    return canonical


def parse_canonical_units(mod_path: str) -> Set[str]:
    """Build a set of canonical sub-unit names from common/units/*.txt.

    Unit names are top-level identifiers inside sub_units = { ... } blocks.
    """
    canonical = set()
    for sub_units, _ in _parse_canonical_unit_sources(mod_path):
        canonical.update(sub_units)
    return canonical


def parse_canonical_namelist_keys(mod_path: str, sub_units: Set[str]) -> Set[str]:
    """Return the set of valid namelist block keys.

    A namelist block key is valid if it is either:
      - a sub_unit name, OR
      - an equipment-type name referenced in `need = { ... }` or
        `need_equipment = { ... }` inside a sub_unit definition.

    Air namelists use equipment-type keys (small_plane_airframe etc.) rather
    than sub_unit names (light_fighter etc.), so the canonical set must
    include both.
    """
    valid = set(sub_units)
    for _, equipment_names in _parse_canonical_unit_sources(mod_path):
        valid.update(equipment_names)
    return valid


def _parse_equipment_names_file(content: str) -> Set[str]:
    """Extract equipment-type names from `need`/`need_equipment` blocks in one file."""
    equipment = set()
    content = strip_comments(content)

    # Find each `need = { ... }` or `need_equipment = { ... }` block and
    # extract `key = N` entries inside it. These are equipment-type names.
    for match in re.finditer(r"\b(?:need|need_equipment)\s*=\s*\{([^{}]*)\}", content):
        for entry in re.finditer(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\d+", match.group(1)):
            equipment.add(entry.group(1))

    return equipment


def _parse_canonical_unit_source(
    content: str,
) -> Tuple[Set[str], Set[str]]:
    return _parse_canonical_units_file(content), _parse_equipment_names_file(content)


def _parse_canonical_unit_sources(
    mod_path: str,
) -> List[Tuple[Set[str], Set[str]]]:
    """Parse each unit source once for both canonical unit indexes."""
    units_dir = os.path.join(mod_path, "common", "units")
    parsed = []
    for filepath in glob.iglob(os.path.join(units_dir, "*.txt")):
        content = _read_text(filepath, mod_path)

        def compute(
            source_content: str = content,
        ) -> Tuple[Set[str], Set[str]]:
            return _parse_canonical_unit_source(source_content)

        parsed.append(
            disk_cache.per_file_cached_by_content(
                mod_path,
                "oob_units.composite",
                filepath,
                content,
                compute,
            )
        )
    return parsed


def _extract_namelist_block_keys(content: str) -> Set[str]:
    """Extract block keys at depth 2 in a 00_TAG_names.txt file.

    The schema is `TAG = { key1 = { ... } key2 = { ... } ... }` where each
    inner key names a sub_unit or equipment type. Assignment-style entries
    like `air_wing_names_template = AIR_WING_NAME_FOO` are skipped (no `{`).
    """
    refs = set()
    lines = content.split("\n")
    brace_depth = 0

    for raw in lines:
        line = raw.strip()
        depth_at_line_start = brace_depth

        for ch in raw:
            if ch == "{":
                brace_depth += 1
            elif ch == "}":
                brace_depth -= 1

        # Block keys live at depth 1 (inside the TAG = { ... } wrapper).
        # The wrapper itself is at depth 0 → 1 on its opening brace.
        if depth_at_line_start != 1:
            continue

        match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\{", line)
        if match:
            refs.add(match.group(1))

    return refs


_AIR_WING_TEMPLATE_RE = re.compile(r"air_wing_names_template\s*=\s*(\S+)")


def _extract_air_wing_template_refs(content: str) -> List[Tuple[str, int]]:
    """Return (loc_key, 1-based line number) for every `air_wing_names_template
    = KEY` assignment. A missing KEY renders as the literal token in-game."""
    refs = []
    for ln, line in enumerate(content.split("\n"), 1):
        match = _AIR_WING_TEMPLATE_RE.search(line)
        if match:
            refs.append((match.group(1).strip('"'), ln))
    return refs


def _extract_ship_types_tokens(content: str) -> Set[str]:
    """Extract tokens from `ship_types = { ... }` arrays in *_ship_names.txt."""
    refs = set()
    for match in re.finditer(r"ship_types\s*=\s*\{([^{}]*)\}", content):
        for tok in re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", match.group(1)):
            refs.add(tok)
    return refs


def _extract_division_types_tokens(content: str) -> Set[str]:
    """Extract quoted-string tokens from `division_types = { "Foo" "Bar" }` arrays.

    Used by *_names_divisions.txt files. Tokens are quoted (unlike ship_types,
    which uses bare identifiers).
    """
    refs = set()
    for match in re.finditer(r"division_types\s*=\s*\{([^{}]*)\}", content):
        for tok in re.findall(r'"([^"]+)"', match.group(1)):
            refs.add(tok)
    return refs


def _extract_division_group_keys(content: str) -> Set[str]:
    """Extract top-level group keys defined in a *_names_divisions.txt file.

    The schema is `GROUP_NAME = { name = ... for_countries = ... ... }` at the
    top level (depth 0 → 1 on the opening brace). Handles both same-line
    (`KEY = {`) and split-line (`KEY =\\n{`) brace styles.
    """
    refs = set()

    # Find every `KEY = {` (allowing whitespace/newlines between `=` and `{`)
    # then verify the match starts at depth 0.
    for match in re.finditer(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\{", content):
        prefix = content[: match.start()]
        depth = prefix.count("{") - prefix.count("}")
        if depth == 0:
            refs.add(match.group(1))

    return refs


def parse_division_group_keys(mod_path: str) -> Set[str]:
    """Return the set of all division_names_group keys defined across the mod."""
    keys = set()
    pattern = os.path.join(mod_path, "common", "units", "names_divisions", "*.txt")
    for filepath in glob.iglob(pattern):
        content = _read_text(filepath, mod_path)
        if not content:
            continue
        keys |= disk_cache.per_file_cached_by_content(
            mod_path,
            "oob_units.div_group_keys",
            filepath,
            content,
            lambda: _extract_division_group_keys(strip_comments(content)),
        )
    return keys


def _extract_division_names_group_refs(content: str) -> List[Tuple[str, int]]:
    """Find `division_names_group = X` references with their 1-based line numbers."""
    refs = []
    for ln, line in enumerate(content.split("\n"), 1):
        match = re.search(r"division_names_group\s*=\s*([A-Za-z_][A-Za-z0-9_]*)", line)
        if match:
            refs.append((match.group(1), ln))
    return refs


def _extract_unit_refs_from_blocks(content: str) -> Set[str]:
    """Extract unit names from regiments = { ... } and support = { ... } blocks.

    Handles two patterns:
      - unit_name = { x = 0 y = 0 }   (OOB / scripted effect style)
      - unit_name = N                   (AI template shorthand)
    """
    refs = set()
    lines = content.split("\n")
    i = 0
    in_block = False
    brace_depth = 0

    while i < len(lines):
        line = lines[i].strip()

        if not in_block:
            if re.match(r"^(regiments|support)\s*=\s*\{", line):
                in_block = True
                brace_depth = 1
                i += 1
                continue
            i += 1
            continue

        # Depth at the START of this line — unit references live at depth 1
        # (direct children of the regiments/support block). Deeper lines
        # (e.g. position `x = 0` / `y = 0` inside `unit_name = { ... }`) must
        # be skipped.
        depth_at_line_start = brace_depth

        for ch in line:
            if ch == "{":
                brace_depth += 1
            elif ch == "}":
                brace_depth -= 1

        if brace_depth <= 0:
            in_block = False
            i += 1
            continue

        if depth_at_line_start != 1:
            i += 1
            continue

        # At depth 1 inside the block, match unit references
        # Pattern 1: unit_name = { ... }
        match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\{", line)
        if match:
            refs.add(match.group(1))
            i += 1
            continue

        # Pattern 2: unit_name = N (number)
        match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\d+", line)
        if match:
            refs.add(match.group(1))

        i += 1

    return refs


def _suggest_match(ref: str, canonical_lower: Dict[str, str]) -> str:
    """Return a ' (did you mean ...?)' suffix for a ref, or empty string."""
    ref_lower = ref.lower()
    if ref_lower in canonical_lower:
        return f" (did you mean '{canonical_lower[ref_lower]}'?)"
    close = get_close_matches(ref_lower, canonical_lower.keys(), n=1, cutoff=0.7)
    if close:
        return f" (did you mean '{canonical_lower[close[0]]}'?)"
    return ""


def _check_refs(
    refs: Set[str],
    canonical: Set[str],
    canonical_lower: Dict[str, str],
    filename: str,
    label: str,
) -> List[str]:
    """Return error strings for refs that aren't in the canonical set."""
    results = []
    for ref in sorted(refs):
        if ref in canonical:
            continue
        msg = f"{filename}: unknown {label} '{ref}'" + _suggest_match(
            ref, canonical_lower
        )
        results.append(msg)
    return results


def variant_tag_from_path(rel: str) -> Optional[str]:
    """Tag owning the variants declared in *rel*, or None when the executing
    scope cannot be resolved statically."""
    norm = rel.replace("\\", "/")
    if not norm.startswith("history/countries/"):
        return None
    return os.path.basename(norm).split(" ")[0].split(".")[0].upper()


def build_variant_name_index(
    sources: List[Tuple[str, str]],
) -> Tuple[Dict[str, Set[Tuple[str, str]]], Set[Tuple[str, str]]]:
    """``(per-tag, wildcard)`` ``(type, name)`` sets from ``(relpath, content)``.

    A variant in `history/countries/` belongs to that file's tag. Everywhere else
    (focus rewards, events, decisions, scripted effects) the effect runs in a
    scope no static pass can pin down (Egypt's carrier purchase creates its
    design in FRA scope inside `events/Egypt.txt`), so those go to the wildcard
    set and satisfy a reference from any tag.
    """
    by_tag: Dict[str, Set[Tuple[str, str]]] = {}
    wildcard: Set[Tuple[str, str]] = set()
    for rel, content in sources:
        if "create_equipment_variant" not in content:
            continue
        tag = variant_tag_from_path(rel)
        for etype, name, _ in parse_variant_names(content):
            if tag:
                by_tag.setdefault(tag, set()).add((etype, name))
            else:
                wildcard.add((etype, name))
    return by_tag, wildcard


def parse_archetypes(equipment_texts: List[str]) -> Set[str]:
    """Equipment names declared `is_archetype = yes`."""
    archetypes: Set[str] = set()
    for raw in equipment_texts:
        text = blank_comments(raw)
        for elo, ehi in _iter_named_blocks(text, 0, len(text), "equipments"):
            for name, blo, bhi, _ in _iter_blocks(text, elo, ehi):
                if _scalar(text, blo, bhi, "is_archetype") == "yes":
                    archetypes.add(name)
    return archetypes


def check_oob_variant_refs(
    content: str,
    by_tag: Dict[str, Set[Tuple[str, str]]],
    wildcard: Set[Tuple[str, str]],
) -> List[Finding]:
    """OOB ships whose `version_name` their producer never created.

    The design is looked up in the `creator`'s pool, falling back to `owner`.
    A miss silently downgrades the ship to version 0 of the hull (stock modules,
    no icon, no name group) and logs `equipmentpool.cpp`.
    """
    text = blank_comments(content)
    findings: List[Finding] = []
    for m in _OOB_EQUIPMENT_RE.finditer(text):
        hull, body = m.group(1), m.group(2)
        version = _VERSION_NAME_RE.search(body)
        if not version:
            continue
        who = _OOB_CREATOR_RE.search(body) or _OOB_OWNER_RE.search(body)
        if not who or len(who.group(1)) != 3:
            continue
        tag = who.group(1).upper()
        ref = (hull, version.group(1))
        if ref in wildcard or ref in by_tag.get(tag, ()):
            continue
        findings.append(
            Finding(
                text.count("\n", 0, m.start()) + 1,
                "unknown_variant",
                f"{tag} has no '{hull}' variant named \"{version.group(1)}\": "
                f"the ship falls back to version 0 of the hull",
            )
        )
    return findings


def check_attributed_archetypes(content: str, archetypes: Set[str]) -> List[Finding]:
    """Production lines naming an archetype together with a producer.

    No country ever designs an archetype, so attributing one sends the engine
    looking for a national variant that cannot exist. It falls back to the latest
    concrete equipment and logs `equipmentvariant.cpp` on every game start.
    """
    text = blank_comments(content)
    findings: List[Finding] = []
    for effect in ("add_equipment_production", "add_equipment_to_stockpile"):
        for blo, bhi in _iter_named_blocks(text, 0, len(text), effect):
            producer = _PRODUCER_RE.search(text, blo, bhi)
            if not producer:
                continue
            equipment = _scalar(text, blo, bhi, "type")
            if equipment is None:
                for elo, ehi in _iter_named_blocks(text, blo, bhi, "equipment"):
                    equipment = _scalar(text, elo, ehi, "type")
                    break
            if equipment not in archetypes:
                continue
            findings.append(
                Finding(
                    text.count("\n", 0, blo) + 1,
                    "attributed_archetype",
                    f"'{equipment}' is an archetype but is attributed to "
                    f"{producer.group(1)}, name the concrete equipment instead",
                )
            )
    return findings


def validate_oob_file(
    args: Tuple[str, Set[str], Dict[str, str], str],
) -> List[str]:
    """Validate a single OOB or AI template file. Returns list of error strings."""
    filepath, canonical, canonical_lower, mod_path = args
    filename = os.path.basename(filepath)

    raw = _read_text(filepath, mod_path)
    if not raw:
        return []

    refs = disk_cache.per_file_cached_by_content(
        mod_path,
        "oob_units.oob_refs",
        filepath,
        raw,
        lambda: _extract_unit_refs_from_blocks(strip_comments(raw)),
    )
    return _check_refs(refs, canonical, canonical_lower, filename, "unit")


def _parse_namelist_file(content: str, parent: str) -> Tuple[Set[str], str]:
    """Parse one namelist file's content into (refs, label) given its parent dir."""
    content = strip_comments(content)

    if parent == "names":
        refs = _extract_namelist_block_keys(content)
        label = "namelist block key"
    elif parent == "names_ships":
        refs = _extract_ship_types_tokens(content)
        label = "ship_types token"
    elif parent == "names_divisions":
        refs = _extract_division_types_tokens(content)
        label = "division_types token"
    else:
        refs = set()
        label = ""

    return refs, label


def validate_namelist_file(
    args: Tuple[str, Set[str], Dict[str, str], str],
) -> List[str]:
    """Validate a single namelist file. Returns list of error strings.

    Handles two schemas:
      - 00_TAG_names.txt: block keys at depth 2 inside `TAG = { ... }`
      - *_ship_names.txt: tokens inside `ship_types = { ... }` arrays
    """
    filepath, canonical, canonical_lower, mod_path = args
    filename = os.path.basename(filepath)

    raw = _read_text(filepath, mod_path)
    if not raw:
        return []

    parent = os.path.basename(os.path.dirname(filepath))
    refs, label = disk_cache.per_file_cached_by_content(
        mod_path,
        "oob_units.namelist",
        filepath,
        raw,
        lambda: _parse_namelist_file(raw, parent),
    )
    if not label:
        return []

    return _check_refs(refs, canonical, canonical_lower, filename, label)


def validate_oob_division_groups_file(
    args: Tuple[str, Set[str], Dict[str, str], str],
) -> List[str]:
    """Check that every `division_names_group = X` ref points to a real group."""
    filepath, group_keys, group_keys_lower, mod_path = args
    filename = os.path.basename(filepath)

    raw = _read_text(filepath, mod_path)
    if not raw:
        return []

    refs = disk_cache.per_file_cached_by_content(
        mod_path,
        "oob_units.div_group_refs",
        filepath,
        raw,
        lambda: _extract_division_names_group_refs(strip_comments(raw)),
    )
    results = []
    for ref, line_no in refs:
        if ref in group_keys:
            continue
        msg = (
            f"{filename}:{line_no}: unknown division_names_group '{ref}'"
            + _suggest_match(ref, group_keys_lower)
        )
        results.append(msg)
    return results


# ---------------------------------------------------------------------------
# create_unit effect validation
# ---------------------------------------------------------------------------
#
# A create_unit only spawns units inside a state scope (capital_scope, a
# state-scope effect, a numeric state-ID block, or a state-scoped decision).
# Its division string must live on one physical line, parse as army data, and
# name a division_template. A template defined in the same country/effect path
# must appear before the create_unit that uses it.

# Documented create_unit block keys; anything else is a typo.
_CREATE_UNIT_KEYS = frozenset(
    {
        "division",
        "owner",
        "prioritize_location",
        "allow_spawning_on_enemy_provs",
        "count",
        "id",
        "country_score",
        "divisional_commander_xp",
    }
)

# Effect/block openers that yield a state scope (where create_unit may run).
_STATE_SCOPE_LABELS = frozenset(
    {
        "capital_scope",
        "random_owned_controlled_state",
        "random_owned_state",
        "random_controlled_state",
        "random_state",
        "random_owned_or_controlled_state",
        "random_enemy_state",
        "random_occupied_state",
        "every_owned_state",
        "every_controlled_state",
        "every_owned_controlled_state",
        "every_state",
        "every_neighbor_state",
        "random_neighbor_state",
        "state_event",
    }
)

_DIVISION_VALUE_RE = re.compile(r'\bdivision\s*=\s*"((?:[^"\\]|\\.)*)"', re.S)
_TEMPLATE_NAME_RE = re.compile(r'\bname\s*=\s*"([^"]*)"')
_KEY_RE = re.compile(r"\b([A-Za-z0-9_]+)\s*=")
_OWNER_RE = re.compile(r"\bowner\s*=")
_ZERO_FACTOR_RE = re.compile(
    r"\b(?:start_equipment_factor|start_manpower_factor)\s*=\s*0(?![.\d])"
)
_STATE_YES_RE = re.compile(r"\bstate\s*=\s*yes\b")
_EXECUTE_EFFECT_RE = re.compile(r"\bexecute_effect\b")
_HAS_TEMPLATE_RE = re.compile(r'\bhas_template\s*=\s*"([^\"]*)"')
_LITERAL_TAG_SCOPE_RE = re.compile(r"^[A-Z0-9_]{3}$")
_SCOPE_KEYWORDS = frozenset({"AND", "NOT", "NOR", "OR"})
_SCOPE_LABELS = frozenset(
    {
        "ROOT",
        "THIS",
        "PREV",
        "FROM",
        "OWNER",
        "CONTROLLER",
        "CAPITAL",
        "OVERLORD",
        "FROMFROM",
        "PREVPREV",
    }
)
_SCOPE_PREFIXES = ("event_target:", "global.event_target:", "var:")
_COUNTRY_ITERATOR_RE = re.compile(
    r"^(?:every|random|all)_(?:\w+_)?(?:country|puppet)(?:_|$)"
)
_NON_GUARANTEEING_GUARD_LABELS = frozenset({"NOT", "NAND", "NOR", "OR"})

# Execution-boundary labels: when walking up a create_unit's enclosing scopes,
# stop at these (a fresh effect sequence starts) so the ordering check doesn't
# compare a template and a create_unit from separate effects or event options.
_EFFECT_BOUNDARY_LABELS = frozenset(
    {
        "completion_reward",
        "execute_effect",
        "complete_effect",
        "remove_effect",
        "timeout_effect",
        "cancel_effect",
        "option",
    }
)


_CREATE_UNIT_CATEGORIES = {
    "scope": "CREATE UNIT: not in a state scope",
    "multiline-division": "CREATE UNIT: division string spans lines",
    "missing-division": "CREATE UNIT: missing division string",
    "missing-owner": "CREATE UNIT: missing owner",
    "missing-template": "CREATE UNIT: division string lacks division_template",
    "unknown-key": "CREATE UNIT: unknown key",
    "unknown-division-key": "CREATE UNIT: unknown key in division string",
    "unquoted-value": "CREATE UNIT: division string value must be quoted",
    "malformed-division": "CREATE UNIT: division string does not parse",
    "out-of-bounds-division": "CREATE UNIT: division string has German/Danish letters",
    "zero-factor": "CREATE UNIT: equipment/manpower factor is zero",
    "template-order": "CREATE UNIT: template defined after create_unit",
}
_CREATE_UNIT_WARNING_KINDS = frozenset({"out-of-bounds-division"})
# persistent.cpp rejects these even inside quotes (Sweden militärdistriktet).
# Romance/Slavic/Kurdish accents (é, á, š, ş, …) render in game and are allowed.
_OUT_OF_BOUNDS_LETTERS = frozenset("äöüßæøåÄÖÜÆØÅ")

# Inner army-data keys. create_unit re-parses `division = "..."` through
# persistent.cpp (not the file parser), so this set is the wiki/OOB subset
# that path actually accepts.
_DIVISION_STRING_KEYS = frozenset(
    {
        "name",
        "division_template",
        "start_experience_factor",
        "start_equipment_factor",
        "start_manpower_factor",
        "force_equipment_variants",
    }
)
_DIVISION_QUOTED_KEYS = frozenset({"name", "division_template"})
_DIVISION_NUMBER_KEYS = frozenset(
    {
        "start_experience_factor",
        "start_equipment_factor",
        "start_manpower_factor",
    }
)
_FEV_ENTRY_KEYS = frozenset({"owner", "amount", "version_name", "creator"})
_NUMBER_RE = re.compile(r"^[+-]?(?:\d+\.\d*|\.\d+|\d+)$")


class _CreateUnitChecks:
    """Collector for one create_unit block; keeps the worker readable."""

    __slots__ = ("issues", "file")

    def __init__(self, file: str):
        self.issues: List[Issue] = []
        self.file = file

    def error(self, kind: str, message: str, line: int):
        self._add(kind, message, line, Severity.ERROR)

    def warn(self, kind: str, message: str, line: int):
        self._add(kind, message, line, Severity.WARNING)

    def _add(self, kind: str, message: str, line: int, severity: str):
        self.issues.append(
            Issue(
                severity=severity,
                category=_CREATE_UNIT_CATEGORIES[kind],
                message=message,
                file=self.file,
                line=line,
            )
        )


def _line_of(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def _label_before_brace(text: str, brace_idx: int) -> Optional[str]:
    j = brace_idx - 1
    while j >= 0 and text[j] in " \t\r\n":
        j -= 1
    if j < 0 or text[j] != "=":
        return None
    j -= 1
    while j >= 0 and text[j] in " \t\r\n":
        j -= 1
    end = j + 1
    while j >= 0 and (text[j].isalnum() or text[j] in "_:.@"):
        j -= 1
    return text[j + 1 : end] or None


def _matching_braces(text: str) -> Dict[int, int]:
    stack = []
    pairs = {}
    in_str = False
    for i, c in enumerate(text):
        if c == '"' and (i == 0 or text[i - 1] != "\\"):
            in_str = not in_str
        elif not in_str:
            if c == "{":
                stack.append(i)
            elif c == "}" and stack:
                pairs[stack.pop()] = i
    return pairs


def _build_block_nodes(text: str) -> List[Dict]:
    """Flattened `key = { }` block tree: label/start/end/line/parent/children."""
    pairs = _matching_braces(text)
    nodes: List[Dict[str, Any]] = []
    stack: List[int] = []
    for op in sorted(pairs):
        while stack and nodes[stack[-1]]["end"] < op:
            stack.pop()
        node: Dict[str, Any] = {
            "label": _label_before_brace(text, op),
            "start": op,
            "end": pairs[op],
            "line": _line_of(text, op),
            "parent": stack[-1] if stack else -1,
            "children": [],
        }
        idx = len(nodes)
        if stack:
            nodes[stack[-1]]["children"].append(idx)
        nodes.append(node)
        stack.append(idx)
    return nodes


def _ancestors(nodes: List[Dict], idx: int) -> List[int]:
    chain = []
    while nodes[idx]["parent"] != -1:
        idx = nodes[idx]["parent"]
        chain.append(idx)
    return chain


def _container_for(nodes: List[Dict], idx: int) -> int:
    """Index of the nearest effect container (a boundary or top-level block)."""
    a = nodes[idx]["parent"]
    while a != -1:
        label = nodes[a]["label"] or ""
        if label in _EFFECT_BOUNDARY_LABELS or nodes[a]["parent"] == -1:
            return a
        a = nodes[a]["parent"]
    return -1


def _scope_label(label: str) -> Optional[str]:
    # State IDs 100-999 match the 3-char tag shape but never switch country.
    if label.isdigit():
        return None
    if label in _SCOPE_LABELS or label.startswith(_SCOPE_PREFIXES):
        return label
    if _LITERAL_TAG_SCOPE_RE.fullmatch(label) and label not in _SCOPE_KEYWORDS:
        return label
    return None


def _country_scope_path(
    nodes: List[Dict], idx: int, include_self: bool = False
) -> Tuple[str, ...]:
    path = ["ROOT"]
    chain = list(reversed(_ancestors(nodes, idx)))
    if include_self:
        chain.append(idx)
    for i in chain:
        label = nodes[i]["label"] or ""
        if _COUNTRY_ITERATOR_RE.match(label):
            path.append(f"@{i}")
            continue
        scope = _scope_label(label)
        if scope == "ROOT":
            path = ["ROOT"]
        elif scope is not None:
            path.append(scope)
    return tuple(path)


def _deepest_node_at(nodes: List[Dict], pos: int) -> int:
    candidates = [
        i for i, node in enumerate(nodes) if node["start"] < pos < node["end"]
    ]
    if not candidates:
        return -1
    return min(candidates, key=lambda i: nodes[i]["end"] - nodes[i]["start"])


def _closest_if(nodes: List[Dict], idx: int) -> int:
    for a in [idx] + _ancestors(nodes, idx):
        if nodes[a]["label"] == "if":
            return a
    return -1


def _is_positive_if_limit_condition(nodes: List[Dict], idx: int, if_idx: int) -> bool:
    saw_limit = False
    while idx != -1:
        label = nodes[idx]["label"]
        if label in _NON_GUARANTEEING_GUARD_LABELS:
            return False
        if label == "limit":
            saw_limit = True
        if idx == if_idx:
            return saw_limit
        idx = nodes[idx]["parent"]
    return False


def _runs_in_if_true_branch(nodes: List[Dict], idx: int, if_idx: int) -> bool:
    child = idx
    while nodes[child]["parent"] != if_idx:
        child = nodes[child]["parent"]
        if child == -1:
            return False
    return nodes[child]["label"] not in {"else", "else_if"}


def _in_has_template_guard(nodes: List[Dict], text: str, idx: int, name: str) -> bool:
    """True if a same-scope has_template condition dominates *idx*."""
    scope_path = _country_scope_path(nodes, idx)
    container = _container_for(nodes, idx)
    for a in _ancestors(nodes, idx):
        if nodes[a]["label"] == "if" and _runs_in_if_true_branch(nodes, idx, a):
            start = nodes[a]["start"]
            body = text[start : nodes[a]["end"]]
            for match in _HAS_TEMPLATE_RE.finditer(body):
                if match.group(1) != name:
                    continue
                match_idx = _deepest_node_at(nodes, start + match.start())
                if (
                    match_idx != -1
                    and _closest_if(nodes, match_idx) == a
                    and _is_positive_if_limit_condition(nodes, match_idx, a)
                    and _country_scope_path(nodes, match_idx, include_self=True)
                    == scope_path
                ):
                    return True
        if a == container:
            break
    return False


def _top_level_keys(text: str, start: int, end: int) -> List[str]:
    keys = []
    depth = 0
    in_str = False
    i = start
    while i < end:
        c = text[i]
        if c == '"' and (i == 0 or text[i - 1] != "\\"):
            in_str = not in_str
            i += 1
            continue
        if in_str:
            i += 1
            continue
        if c == "{":
            depth += 1
            i += 1
            continue
        if c == "}":
            depth -= 1
            i += 1
            continue
        if depth == 0:
            m = _KEY_RE.match(text, i)
            if m:
                keys.append(m.group(1))
                i = m.end()
                continue
        i += 1
    return keys


def _template_defs_named(
    nodes: List[Dict], text: str, container: int, name: str, scope_path: Tuple[str, ...]
) -> List[int]:
    """Indices of same-scope division_template blocks named *name*."""
    out = []
    stack = list(nodes[container]["children"])
    while stack:
        i = stack.pop()
        if (
            nodes[i]["label"] == "division_template"
            and _country_scope_path(nodes, i) == scope_path
        ):
            body = text[nodes[i]["start"] : nodes[i]["end"]]
            m = _TEMPLATE_NAME_RE.search(body)
            if m and m.group(1) == name:
                out.append(i)
        stack.extend(nodes[i]["children"])
    return out


def _in_state_scope(nodes: List[Dict], text: str, idx: int) -> bool:
    for a in _ancestors(nodes, idx):
        node = nodes[a]
        label = node["label"] or ""
        if label in _STATE_SCOPE_LABELS:
            return True
        if label.isdigit():
            return True
        body = text[node["start"] : node["end"]]
        if _EXECUTE_EFFECT_RE.search(body) and _STATE_YES_RE.search(body):
            return True
    return False


def _division_tokens(text: str) -> List[Tuple[str, str]]:
    tokens: List[Tuple[str, str]] = []
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c in " \t\r\n":
            i += 1
            continue
        if c in "{}=":
            tokens.append(("punct", c))
            i += 1
            continue
        if c == '"':
            j = i + 1
            while j < n and text[j] != '"':
                j += 1
            if j >= n:
                tokens.append(("error", "unclosed quote"))
                return tokens
            tokens.append(("string", text[i + 1 : j]))
            i = j + 1
            continue
        j = i + 1
        while j < n and text[j] not in ' \t\r\n{}="':
            j += 1
        raw = text[i:j]
        kind = "number" if _NUMBER_RE.fullmatch(raw) else "ident"
        tokens.append((kind, raw))
        i = j
    return tokens


def _out_of_bounds_chunks(text: str) -> List[str]:
    chunks: List[str] = []
    seen = set()
    for kind, value in _division_tokens(text):
        if kind == "error" or value in seen:
            continue
        if _OUT_OF_BOUNDS_LETTERS.isdisjoint(value):
            continue
        seen.add(value)
        chunks.append(value)
    return chunks


def _parse_fev_entry(
    tokens: List[Tuple[str, str]], start: int, equipment: str
) -> Tuple[int, List[Tuple[str, str]]]:
    issues: List[Tuple[str, str]] = []
    i = start
    if i >= len(tokens) or tokens[i] != ("punct", "{"):
        issues.append(
            (
                "malformed-division",
                f"division string force_equipment_variants '{equipment}' is not a block",
            )
        )
        return i, issues
    i += 1
    unknown: List[str] = []
    while i < len(tokens) and tokens[i] != ("punct", "}"):
        kind, value = tokens[i]
        if kind != "ident":
            issues.append(
                (
                    "malformed-division",
                    f"division string force_equipment_variants '{equipment}' does not parse",
                )
            )
            return i, issues
        key = value
        i += 1
        if i >= len(tokens) or tokens[i] != ("punct", "="):
            issues.append(
                (
                    "malformed-division",
                    f"division string force_equipment_variants '{equipment}' does not parse",
                )
            )
            return i, issues
        i += 1
        if i >= len(tokens):
            issues.append(
                (
                    "malformed-division",
                    f"division string force_equipment_variants '{equipment}' does not parse",
                )
            )
            return i, issues
        vkind, vval = tokens[i]
        i += 1
        if key not in _FEV_ENTRY_KEYS:
            unknown.append(key)
            continue
        if key == "version_name" and vkind != "string":
            issues.append(
                (
                    "unquoted-value",
                    "division string version_name must be a quoted string",
                )
            )
        elif key == "amount" and vkind != "number":
            issues.append(
                (
                    "malformed-division",
                    f"division string force_equipment_variants '{equipment}' amount must be a number",
                )
            )
        elif key in {"owner", "creator"} and vkind not in {"ident", "string"}:
            issues.append(
                (
                    "malformed-division",
                    f"division string force_equipment_variants '{equipment}' {key} must be a tag",
                )
            )
        elif vkind == "punct":
            issues.append(
                (
                    "malformed-division",
                    f"division string force_equipment_variants '{equipment}' does not parse",
                )
            )
            return i, issues
    if i >= len(tokens):
        issues.append(
            (
                "malformed-division",
                f"division string force_equipment_variants '{equipment}' is not a block",
            )
        )
        return i, issues
    i += 1
    if unknown:
        issues.append(
            (
                "unknown-division-key",
                "division string force_equipment_variants '"
                f"{equipment}' unknown key(s): {', '.join(sorted(set(unknown)))}",
            )
        )
    return i, issues


def _parse_division_string(
    text: str,
) -> Tuple[List[Tuple[str, str]], Optional[str]]:
    """Schema-check a create_unit division string. Returns (issues, template)."""
    issues: List[Tuple[str, str]] = []
    chunks = _out_of_bounds_chunks(text)
    if chunks:
        issues.append(
            (
                "out-of-bounds-division",
                "division string out-of-bounds letter in: " + "; ".join(chunks),
            )
        )

    tokens = _division_tokens(text)
    i = 0
    unknown: List[str] = []
    template: Optional[str] = None
    saw_template = False
    while i < len(tokens):
        kind, value = tokens[i]
        if kind == "error":
            issues.append(("malformed-division", f"division string {value}"))
            return issues, template
        if kind != "ident":
            issues.append(
                (
                    "malformed-division",
                    f"division string leftover token: {value}",
                )
            )
            return issues, template
        key = value
        i += 1
        if i >= len(tokens) or tokens[i] != ("punct", "="):
            issues.append(
                (
                    "malformed-division",
                    f"division string leftover token: {key}",
                )
            )
            return issues, template
        i += 1
        if i >= len(tokens):
            issues.append(
                (
                    "malformed-division",
                    f"division string {key} is missing a value",
                )
            )
            return issues, template
        vkind, vval = tokens[i]
        i += 1
        if key not in _DIVISION_STRING_KEYS:
            unknown.append(key)
            if vkind == "punct" and vval == "{":
                depth = 1
                while i < len(tokens) and depth:
                    if tokens[i] == ("punct", "{"):
                        depth += 1
                    elif tokens[i] == ("punct", "}"):
                        depth -= 1
                    i += 1
            continue
        if key in _DIVISION_QUOTED_KEYS:
            if key == "division_template":
                saw_template = True
            if vkind != "string":
                issues.append(
                    (
                        "unquoted-value",
                        f"division string {key} must be a quoted string",
                    )
                )
            elif key == "division_template":
                template = vval or None
        elif key in _DIVISION_NUMBER_KEYS:
            if vkind != "number":
                issues.append(
                    (
                        "malformed-division",
                        f"division string {key} must be a number",
                    )
                )
        elif key == "force_equipment_variants":
            if vkind != "punct" or vval != "{":
                issues.append(
                    (
                        "malformed-division",
                        "division string force_equipment_variants is not a block",
                    )
                )
                continue
            while i < len(tokens) and tokens[i] != ("punct", "}"):
                ekind, eval_ = tokens[i]
                if ekind != "ident":
                    issues.append(
                        (
                            "malformed-division",
                            "division string force_equipment_variants does not parse",
                        )
                    )
                    return issues, template
                i += 1
                if i >= len(tokens) or tokens[i] != ("punct", "="):
                    issues.append(
                        (
                            "malformed-division",
                            "division string force_equipment_variants does not parse",
                        )
                    )
                    return issues, template
                i += 1
                i, extra = _parse_fev_entry(tokens, i, eval_)
                issues.extend(extra)
            if i >= len(tokens):
                issues.append(
                    (
                        "malformed-division",
                        "division string force_equipment_variants is not a block",
                    )
                )
                return issues, template
            i += 1

    if unknown:
        issues.append(
            (
                "unknown-division-key",
                f"division string unknown key(s): {', '.join(sorted(set(unknown)))}",
            )
        )
    if not saw_template:
        issues.append(
            (
                "missing-template",
                'division string lacks division_template="..."',
            )
        )
    elif not template:
        issues.append(
            (
                "missing-template",
                'division string lacks division_template="..."',
            )
        )
    return issues, template


def _check_created_units(args: Tuple[str, str, str]) -> List[Issue]:
    """Validate every create_unit block in one file. Returns error Issues."""
    filepath, rel, mod_path = args
    raw = _read_text(filepath, mod_path)
    if not raw:
        return []
    content = strip_comments(raw)
    nodes = disk_cache.per_file_cached_by_content(
        mod_path,
        "oob_units.blocks",
        filepath,
        content,
        lambda: _build_block_nodes(content),
    )

    cu_nodes = [i for i, n in enumerate(nodes) if n["label"] == "create_unit"]
    if not cu_nodes:
        return []

    out = _CreateUnitChecks(rel)
    for cu_idx in cu_nodes:
        cu = nodes[cu_idx]
        body = content[cu["start"] + 1 : cu["end"]]
        line = cu["line"]

        if not _in_state_scope(nodes, content, cu_idx):
            out.error(
                "scope",
                f"{cu['line']}: create_unit outside a state scope (effect does "
                f"nothing at country scope)",
                line,
            )

        if not _OWNER_RE.search(body):
            out.error(
                "missing-owner", f"{cu['line']}: create_unit missing `owner`", line
            )

        keys = _top_level_keys(content, cu["start"] + 1, cu["end"])
        unknown = sorted(set(keys) - _CREATE_UNIT_KEYS)
        if unknown:
            out.error(
                "unknown-key",
                f"{cu['line']}: create_unit unknown key(s): {', '.join(unknown)}",
                line,
            )

        dm = _DIVISION_VALUE_RE.search(body)
        if not dm:
            out.error(
                "missing-division",
                f"{cu['line']}: create_unit missing `division` string",
                line,
            )
            continue
        dval = dm.group(1)
        if "\n" in dval:
            out.error(
                "multiline-division",
                f"{cu['line']}: division string must stay on one physical line",
                line,
            )
        # The string carries escaped quotes (\"...\"); normalize so the inner
        # name/template/factor tokens parse like the engine's parsed string.
        dval_clean = dval.replace('\\"', '"')
        if _ZERO_FACTOR_RE.search(dval_clean):
            out.error(
                "zero-factor",
                f"{cu['line']}: start_equipment_factor/start_manpower_factor of 0 is treated as 1",
                line,
            )

        parsed_issues, tname = _parse_division_string(dval_clean)
        for kind, message in parsed_issues:
            prefixed = f"{cu['line']}: {message}"
            if kind in _CREATE_UNIT_WARNING_KINDS:
                out.warn(kind, prefixed, line)
            else:
                out.error(kind, prefixed, line)
        if not tname:
            continue

        if _in_has_template_guard(nodes, content, cu_idx, tname):
            continue

        scope_path = _country_scope_path(nodes, cu_idx)
        container = _container_for(nodes, cu_idx)
        for a in _ancestors(nodes, cu_idx):
            defs = _template_defs_named(nodes, content, a, tname, scope_path)
            if not defs:
                if a == container:
                    break
                continue
            # A name can be defined multiple times in one country/effect path.
            # Only the earliest definition can make this create_unit valid.
            t = nodes[min(defs, key=lambda d: nodes[d]["start"])]
            if t["start"] > cu["start"]:
                out.error(
                    "template-order",
                    f"{cu['line']}: division_template '{tname}' is defined after the create_unit that uses it",
                    line,
                )
            break

    return out.issues


class Validator(BaseValidator):
    TITLE = "OOB UNIT NAME VALIDATION"
    STAGED_EXTENSIONS = [".txt"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.canonical = set()
        self.canonical_lower = {}
        self.namelist_canonical = set()
        self.namelist_canonical_lower = {}
        self._variant_sources_by_scope: Dict[bool, List[Tuple[str, str]]] = {}

    def _build_canonical_units(self):
        """Build the canonical unit name set from unit definition files."""
        self._log_section("Building canonical unit name set...")

        unit_sources = _parse_canonical_unit_sources(self.mod_path)
        self.canonical = {name for sub_units, _ in unit_sources for name in sub_units}
        self.canonical_lower = {name.lower(): name for name in self.canonical}

        # Namelist keys also accept equipment-type names (air namelists use
        # `small_plane_airframe` rather than the sub_unit name `light_fighter`).
        self.namelist_canonical = set(self.canonical)
        self.namelist_canonical.update(
            name for _, equipment_names in unit_sources for name in equipment_names
        )
        self.namelist_canonical_lower = {
            name.lower(): name for name in self.namelist_canonical
        }

        self.log(f"  Found {len(self.canonical)} canonical sub-unit definitions")
        self.log(
            f"  Found {len(self.namelist_canonical)} valid namelist block keys"
            f" (sub_units + equipment types)"
        )

    def _get_files_to_check(self) -> List[str]:
        """Get list of OOB and AI template files to validate."""
        patterns = [
            "history/units/*.txt",
            "common/ai_templates/*.txt",
            "common/scripted_effects/00_AI_scripted_effects.txt",
        ]
        return self._collect_files(patterns)

    def validate_unit_references(self):
        """Validate that all unit references match canonical definitions."""
        self._log_section("Checking unit references in OOB and AI template files...")

        files = self._get_files_to_check()
        self.log(f"  Found {len(files)} files to check")

        args_list = [
            (f, self.canonical, self.canonical_lower, self.mod_path) for f in files
        ]

        all_results = self._pool_map(validate_oob_file, args_list, chunksize=20)

        results = []
        for file_results in all_results:
            results.extend(file_results)

        self._report(
            results,
            "✓ All unit references match canonical definitions",
            "Files with unknown unit references:",
        )

    def validate_namelist_references(self):
        """Validate that namelist block keys and ship_types tokens are canonical."""
        self._log_section("Checking namelist block keys and ship_types tokens...")

        files = self._collect_files(
            [
                "common/units/names/*.txt",
                "common/units/names_ships/*.txt",
                "common/units/names_divisions/*.txt",
            ]
        )
        self.log(f"  Found {len(files)} namelist files to check")

        args_list = [
            (f, self.namelist_canonical, self.namelist_canonical_lower, self.mod_path)
            for f in files
        ]
        all_results = self._pool_map(validate_namelist_file, args_list, chunksize=20)

        results = []
        for file_results in all_results:
            results.extend(file_results)

        # Namelist mismatches are reported as warnings (not errors) — many
        # legacy 00_*_names.txt files still carry vanilla-style block keys
        # (cavalry, motorized, LHA, LPD, etc.) that need a per-block cleanup
        # decision (rename, merge, or delete). Surface them without breaking
        # CI on existing dead code.
        self._report(
            results,
            "✓ All namelist references match canonical definitions",
            "Files with unknown namelist references:",
            severity=Severity.WARNING,
        )

    def validate_division_names_group_references(self):
        """Validate every `division_names_group = X` in OOB files points to a real group."""
        self._log_section("Checking division_names_group references in OOB files...")

        group_keys = parse_division_group_keys(self.mod_path)
        group_keys_lower = {k.lower(): k for k in group_keys}
        self.log(f"  Found {len(group_keys)} division_names_group definitions")

        files = self._collect_files(["history/units/*.txt"])
        self.log(f"  Found {len(files)} OOB files to check")

        args_list = [(f, group_keys, group_keys_lower, self.mod_path) for f in files]
        all_results = self._pool_map(
            validate_oob_division_groups_file, args_list, chunksize=20
        )

        results = []
        for file_results in all_results:
            results.extend(file_results)

        self._report(
            results,
            "✓ All division_names_group references resolve",
            "OOB files with unknown division_names_group references:",
        )

    def validate_air_wing_names_template_loc(self):
        """Check that every `air_wing_names_template = KEY` resolves to a loc key.

        A missing KEY renders as the literal token in-game rather than the
        localized fallback air-wing name.
        """
        self._log_section("Checking air_wing_names_template loc references...")

        loc_keys = self._load_localisation_keys()
        files = self._collect_files(["common/units/names/*.txt", "history/units/*.txt"])
        self.log(f"  Found {len(files)} files to check")

        results = []
        for filepath in files:
            raw = _read_text(filepath, self.mod_path)
            if not raw:
                continue
            content = strip_comments(raw)
            refs = disk_cache.per_file_cached_by_content(
                self.mod_path,
                "oob_units.air_wing_template_refs",
                filepath,
                content,
                lambda content=content: _extract_air_wing_template_refs(content),
            )
            filename = os.path.basename(filepath)
            for key, line_no in refs:
                if key not in loc_keys:
                    results.append(
                        f"{filename}:{line_no}: air_wing_names_template references "
                        f"undefined loc key '{key}'"
                    )

        self._report(
            results,
            "✓ All air_wing_names_template references resolve to a loc key",
            "Files with unknown air_wing_names_template loc references:",
            severity=Severity.WARNING,
            category="air-wing-template-loc",
        )

    def _get_variant_sources(self, *, ignore_staged: bool) -> List[Tuple[str, str]]:
        """Read variant sources once per effective staged/full scope."""
        full_scope = not (self.staged_only and not ignore_staged)
        if full_scope in self._variant_sources_by_scope:
            return self._variant_sources_by_scope[full_scope]

        files = self._collect_files(_VARIANT_SOURCE_PATTERNS, ignore_staged=full_scope)
        sources = [
            (
                os.path.relpath(filepath, self.mod_path),
                _read_text(filepath, self.mod_path),
            )
            for filepath in files
        ]
        self._variant_sources_by_scope[full_scope] = sources
        return sources

    def validate_created_variant_modules(self):
        """Check every `create_equipment_variant` design against its hull's slots.

        A module in a slot the hull does not have, or whose category that slot
        rejects, is dropped at load with no error. The design still appears, so
        the loss only shows as missing stats — a Type 32 Guardian naming the
        tank slot `engine_type_slot` shipped with no engine at all. Ship hulls,
        tank chassis and plane airframes all follow the same rules, so every
        design is checked, whatever it builds.
        """
        self._log_section(
            "Checking created equipment variants against hull slot rules..."
        )

        units_dir = os.path.join(self.mod_path, "common", "units", "equipment")
        if not os.path.isdir(units_dir):
            self.log("  common/units/equipment/ not found, skipping")
            return

        sources = self._get_variant_sources(ignore_staged=False)
        if not sources:
            self.log("  No files with equipment variants to check")
            return
        self.log(f"  Found {len(sources)} files to check")

        index = self.cached(
            "equipment_hull_index", lambda: build_equipment_index(units_dir)
        )

        results = []
        for rel, content in sources:
            if "create_equipment_variant" not in content:
                continue

            for f in check_created_variants(content, index):
                labels = (
                    _VARIANT_SLOT_CATEGORIES
                    if f.hull in index.ship_hulls
                    else _EQUIPMENT_VARIANT_SLOT_CATEGORIES
                )
                results.append(
                    Issue(
                        severity=Severity.ERROR,
                        category=labels[f.kind],
                        message=f.message,
                        file=rel,
                        line=f.line,
                    )
                )

        self._report(
            results,
            "✓ All created variants match their hull slot rules",
            "Created variant modules invalid for their hull slot:",
        )

    def validate_oob_variant_references(self):
        """Check that every ship design an OOB or production line names exists.

        Both misses are silent in game and only surface as a log line plus a ship
        that quietly carries the wrong modules. Thailand's Naresuan frigates
        asked China for a `frigate_hull_3` design China only had as
        `frigate_hull_2`, and its convoy line named the archetype.
        """
        self._log_section("Checking OOB and production equipment references...")

        def _build_variants():
            return build_variant_name_index(
                self._get_variant_sources(ignore_staged=True)
            )

        by_tag, wildcard = self.cached("variant_name_index", _build_variants)
        if not by_tag and not wildcard:
            self.log("  No equipment variants found, skipping")
            return

        def _build_archetypes():
            units_dir = os.path.join(self.mod_path, "common", "units", "equipment")
            return parse_archetypes(
                [
                    _read_text(fp, self.mod_path)
                    for fp in sorted(glob.iglob(os.path.join(units_dir, "*.txt")))
                ]
            )

        archetypes = self.cached("equipment_archetypes", _build_archetypes)

        results = []
        for filepath in self._collect_files(["history/units/*.txt"]):
            content = _read_text(filepath, self.mod_path)
            if "version_name" not in content:
                continue
            rel = os.path.relpath(filepath, self.mod_path)
            for f in check_oob_variant_refs(content, by_tag, wildcard):
                results.append(
                    Issue(
                        severity=Severity.ERROR,
                        category=_VARIANT_REF_CATEGORIES[f.kind],
                        message=f.message,
                        file=rel,
                        line=f.line,
                    )
                )

        for filepath in self._collect_files(_HISTORY_PRODUCTION_PATTERNS):
            content = _read_text(filepath, self.mod_path)
            if "add_equipment_" not in content:
                continue
            rel = os.path.relpath(filepath, self.mod_path)
            for f in check_attributed_archetypes(content, archetypes):
                results.append(
                    Issue(
                        severity=Severity.ERROR,
                        category=_VARIANT_REF_CATEGORIES[f.kind],
                        message=f.message,
                        file=rel,
                        line=f.line,
                    )
                )

        self._report(
            results,
            "✓ All OOB and production equipment references resolve",
            "Equipment references with no matching variant:",
        )

    def validate_load_oob_references(self):
        """Check that runtime OOB loads name an existing history file."""
        self._log_section("Checking runtime OOB references...")

        target_paths = self._collect_files(["history/units/*.txt"], ignore_staged=True)
        targets = {
            os.path.splitext(os.path.basename(filepath))[0] for filepath in target_paths
        }
        changed_targets = self.staged_only and any(
            os.path.relpath(filepath, self.mod_path)
            .replace(os.sep, "/")
            .startswith("history/units/")
            for filepath in get_staged_files(
                self.mod_path, extensions=self.STAGED_EXTENSIONS, include_missing=True
            )
            or []
        )
        source_paths = self._collect_files(
            _CREATE_UNIT_SOURCE_PATTERNS, ignore_staged=changed_targets
        )

        results = []
        for filepath in source_paths:
            content = _read_text(filepath, self.mod_path)
            rel = os.path.relpath(filepath, self.mod_path)
            for target, line in find_load_oob_references(content):
                if target not in targets:
                    results.append(
                        Issue(
                            severity=Severity.ERROR,
                            category="unknown-load-oob",
                            message=(
                                f'load_oob references "{target}", but no '
                                f"history/units/{target}.txt file exists"
                            ),
                            file=rel,
                            line=line,
                        )
                    )

        self._report(
            results,
            "✓ All runtime OOB references resolve",
            "Runtime OOB references with no matching history file:",
        )

    def validate_created_units(self):
        """Check every create_unit effect source for proper form."""
        self._log_section("Checking create_unit effects across the mod...")

        files = self._collect_files(_CREATE_UNIT_SOURCE_PATTERNS)
        if not files:
            self.log("  No files to check")
            return
        self.log(f"  Found {len(files)} files to check")

        args_list = [
            (f, os.path.relpath(f, self.mod_path), self.mod_path) for f in files
        ]
        all_results = self._pool_map(_check_created_units, args_list, chunksize=20)

        results = []
        for file_results in all_results:
            results.extend(file_results)

        self._report(
            results,
            "✓ All create_unit effects are well-formed",
            "create_unit effects with structural problems:",
        )

    def run_validations(self):
        self._build_canonical_units()
        self.validate_unit_references()
        self.validate_namelist_references()
        self.validate_division_names_group_references()
        self.validate_air_wing_names_template_loc()
        self.validate_created_variant_modules()
        self.validate_oob_variant_references()
        self.validate_load_oob_references()
        self.validate_created_units()


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate unit names in OOB files and AI templates against canonical definitions",
    )
