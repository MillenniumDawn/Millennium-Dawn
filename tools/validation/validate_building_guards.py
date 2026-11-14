#!/usr/bin/env python3
"""Validate that `damage_building` / `remove_building` effects are guarded by a
check that the named building actually exists.

Calling either effect against a building the state/country doesn't have spams
`error.log` and, at the scale MD runs raids and random-list decisions,
degrades performance across the campaign (issue #2806).

The rule: the `type = <building>` an effect names must also be proven present
by a trigger sitting between the effect and the top of its enclosing script
tree. "Proven present" is read strictly:

  - Only a comparison that cannot hold at level zero counts: `X > 0` (or any
    higher bound), `X >= 1`, `X == 1`. `X < 1`, `X <= 0`, `X == 0` and `X != 0`
    prove nothing about presence.
  - A comparison inside `NOT` / `OR` / `NAND` / `NOR` / `count_triggers` proves
    nothing -- a disjunct may be the branch that did not hold.
  - A comparison inside an `any_*` / `all_*` scope block proves nothing about
    the scope the effect runs in. `any_core_state = { arms_factory > 1 }` says
    some state has one, never that the selected state does.

The mod's accepted guard idioms, all derived from live usage:

  - A bare building-count comparison in an enclosing `limit`. That is the
    `if = { limit = { fuel_silo > 0 } ... }` form every `common/raids/` site
    uses, and the same `limit` on a scoped iterator (`random_owned_state =
    { limit = { dockyard > 0 } ... }`, `every_owned_state`,
    `random_core_state`, `random_controlled_state`, ...).
  - `non_damaged_building_level = { building = X ... }` or
    `any_province_building_level = { building = X ... }` (also accepts
    `has_building` / `num_of_buildings`, both unused today) anywhere in the
    limit, however deeply nested.
  - A sibling `modifier = { factor = 0  X < 1 }` zeroing a `random_list`
    bucket's weight when the building is absent. The polarity is inverted
    there: the bucket runs only when the condition fails, so it is the
    *absence* comparison that proves presence.

A state selector (`random_owned_state`, `every_core_state`, ...) picks a state
of its own, so proof gathered outside it does not carry in: each one must
carry its own `limit` naming the building. Fixed scopes (`652 = { ... }`,
`var:target_state = { ... }`) do inherit, since they name one specific state.

`non_damaged_building_level` and `num_of_buildings` only resolve *state*
buildings. Naming a province building in one is a load-time error -- the game
logs `Not a valid state building: building` and the trigger never validates --
so those two are additionally reported, and do not count as a guard. Use the
bare `naval_base > 0` comparison or `any_province_building_level` instead.

`trigger` / `available` / `visible` / `allowed` are not guards: a
country-level `any_owned_state = { arms_factory > 0 }` does not prove the
state the effect runs on has that building. `effect_tooltip` subtrees are
skipped because they only preview effects and never execute.

The advisory random-infrastructure check only covers direct construction effects
in selected random-state iterators and randomly limited every-state iterators.
It looks for a recognized slot check in the selector's own limit, not arbitrary
guards.

The advisory coastal check flags a coastal provincial building (`only_costal =
yes`, the engine's spelling, with a `province_max` cap) placed in a province that
`map/definition.csv` does not mark as coastal land. It reads province blocks in a
state history `buildings = { 1234 = { ... } }` and `add_building_construction`
with `province = 1234` or `province = { id = 1234 }`. Provinces picked at runtime
are not checked.
"""

import os
import re
import sys
from typing import FrozenSet, List, Optional, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import disk_cache  # noqa: E402 — same-dir import after sys.path tweak above
from guard_scan import SKIP_BLOCKS as _SKIP_BLOCKS  # noqa: E402
from guard_scan import Context, read_file, report_findings  # noqa: E402
from guard_scan import sanitize as _sanitize  # noqa: E402
from shared_utils import blank_quoted_strings, compute_line_offsets, line_for_offset
from validator_common import (
    FACTOR_ZERO_RE,
    BaseValidator,
    _child_blocks,
    run_validator_main,
    strip_comments,
)

_TYPE_RE = re.compile(r"\btype\s*=\s*([A-Za-z_][A-Za-z0-9_]*)")
_COMPARISON_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*(>=|<=|==|!=|>|<)\s*(-?\d+)")
_BUILDING_FIELD_RE = re.compile(r"\b(?:building|type)\s*=\s*([A-Za-z_][A-Za-z0-9_]*)")
# A comparison inside any of these cannot stand on its own: the branch that
# held may be another one, or the whole thing may be negated.
_UNPROVEN_IN = frozenset({"not", "or", "nand", "nor", "count_triggers"})
# Scope blocks that quantify over states other than the one in hand.
_QUANTIFIER_SCOPE_RE = re.compile(r"^(?:any|all)_")
# Scopes that pick their own state, so an outer guard says nothing about them.
_STATE_SELECTOR_RE = re.compile(r"^(?:random|every)_\w*state\w*$")
_RANDOM_SELECT_RE = re.compile(r"\brandom_select_amount\s*=")
_RANDOM_STATE_SELECTORS = frozenset(
    {
        "random_owned_state",
        "random_controlled_state",
        "random_owned_controlled_state",
        "random_core_state",
    }
)
_RANDOM_SUBSET_SELECTORS = frozenset({"every_owned_state", "every_controlled_state"})
_CHECKED_RANDOM_SELECTORS = _RANDOM_STATE_SELECTORS | _RANDOM_SUBSET_SELECTORS
_INFRASTRUCTURE_GUARD_RE = re.compile(r"\binfrastructure_random_build_loc\s*=\s*yes\b")
_SLOT_BUILDING_RE = re.compile(r"\bbuilding\s*=\s*([A-Za-z_][A-Za-z0-9_]*)")
_SLOT_COUNT_RE = re.compile(r"\bsize\s*(>=|==|>|<=|!=|<)\s*(-?\d+)(?![\w.])")

_BUILDING_EFFECTS = {
    "damage_building": "unguarded-damage-building",
    "remove_building": "unguarded-remove-building",
}
# Field-based building presence triggers -- name the building via `building =`
# or `type =` rather than a bare comparison. has_building/num_of_buildings
# have no live usage in the mod; kept for future-proofing.
_NAMED_BUILDING_TRIGGERS = frozenset(
    {
        "non_damaged_building_level",
        "any_province_building_level",
        "has_building",
        "num_of_buildings",
    }
)
# Triggers that read the state building list and cannot resolve a province
# building. Naming one is a load-time parser error, not just a weak guard.
_STATE_ONLY_BUILDING_TRIGGERS = frozenset(
    {"non_damaged_building_level", "num_of_buildings"}
)
# Every building carrying a `province_max` level cap in
# common/buildings/00_buildings.txt. building_guards_test keeps this in sync.
_PROVINCE_BUILDINGS = frozenset(
    {
        "air_facility",
        "bunker",
        "canal_locks",
        "coastal_bunker",
        "dam",
        "dam_mountain",
        "land_facility",
        "naval_base",
        "naval_facility",
        "naval_headquarters",
        "naval_supply_hub",
        "nuclear_facility",
        "rail_way",
        "supply_node",
    }
)


DEFINITION_FILE = "map/definition.csv"
_BUILDINGS_GLOB = "common/buildings/*.txt"
_SCAN_GLOBS = ["common/**/*.txt", "events/**/*.txt", "history/**/*.txt"]
_TOKEN_RE = re.compile(r"[^\s{}=]+|[{}=]")
_IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_PROVINCE_ID_RE = re.compile(r"\d+\Z")

# (coastal provincial buildings, coastal land province ids, every province id)
CoastalReference = Tuple[FrozenSet[str], FrozenSet[int], FrozenSet[int]]
# Set in each worker by _init_worker; None skips the coastal check.
_COASTAL: Optional[CoastalReference] = None


def _init_worker(coastal: Optional[CoastalReference]) -> None:
    global _COASTAL
    _COASTAL = coastal


def _proves_present(operator: str, value: int) -> bool:
    """Whether `<building> <operator> <value>` can only hold at level 1 or more."""
    if operator == ">":
        return value >= 0
    if operator in (">=", "=="):
        return value >= 1
    return False


def _proves_absent(operator: str, value: int) -> bool:
    """Whether `<building> <operator> <value>` can only hold at level 0."""
    if operator == "<":
        return value <= 1
    if operator == "<=":
        return value <= 0
    if operator == "==":
        return value == 0
    return False


def _find_province_building_triggers(text: str) -> List[Tuple[int, str, str]]:
    """`(offset, trigger, building)` for state-only triggers naming a province
    building, anywhere in ``text``."""
    found: List[Tuple[int, str, str]] = []
    for name, _, body_start, body_end in _child_blocks(text, 0, len(text)):
        if name in _STATE_ONLY_BUILDING_TRIGGERS:
            for building in _BUILDING_FIELD_RE.findall(text[body_start:body_end]):
                if building in _PROVINCE_BUILDINGS:
                    found.append((body_start, name, building))
        else:
            found.extend(
                (offset + body_start, trigger, building)
                for offset, trigger, building in _find_province_building_triggers(
                    text[body_start:body_end]
                )
            )
    return found


def _comparisons_outside_blocks(text: str, proves) -> Set[str]:
    """Names compared at this level only, with nested block bodies excluded so
    a `NOT` or `OR` subtree cannot leak its comparisons upwards."""
    names: Set[str] = set()
    cursor = 0
    for _, name_start, _, body_end in _child_blocks(text, 0, len(text)):
        names |= {
            match.group(1)
            for match in _COMPARISON_RE.finditer(text, cursor, name_start)
            if proves(match.group(2), int(match.group(3)))
        }
        cursor = body_end + 1
    names |= {
        match.group(1)
        for match in _COMPARISON_RE.finditer(text, cursor)
        if proves(match.group(2), int(match.group(3)))
    }
    return names


def _extract_building_guards(text: str) -> Set[str]:
    """Building type names proven present by triggers anywhere in ``text``.

    Combines the presence-comparison idiom (`fuel_silo > 0`) with the
    field-based triggers, whose value only appears as `building = X` /
    `type = X` inside a named child block. Negated, disjunctive and
    other-state subtrees are skipped: none of them proves the building is
    there when the effect runs.
    """
    buildings = _comparisons_outside_blocks(text, _proves_present)
    for name, _, body_start, body_end in _child_blocks(text, 0, len(text)):
        body = text[body_start:body_end]
        if name in _NAMED_BUILDING_TRIGGERS:
            named = set(_BUILDING_FIELD_RE.findall(body))
            if name in _STATE_ONLY_BUILDING_TRIGGERS:
                named -= _PROVINCE_BUILDINGS
            buildings.update(named)
        elif name.lower() in _UNPROVEN_IN or _QUANTIFIER_SCOPE_RE.match(name.lower()):
            continue
        else:
            buildings.update(_extract_building_guards(body))
    return buildings


def _extract_absent_buildings(text: str) -> Set[str]:
    """Building type names proven *absent* by triggers anywhere in ``text``.

    Only used on a `factor = 0` modifier body, where the polarity flips: the
    random_list bucket runs when the condition fails, so proving absence here
    proves presence at the effect. `NOT = { X > 0 }` is the exact dual of the
    bare `X < 1` and counts the same way.
    """
    buildings = _comparisons_outside_blocks(text, _proves_absent)
    for name, _, body_start, body_end in _child_blocks(text, 0, len(text)):
        body = text[body_start:body_end]
        if name.lower() == "not":
            buildings.update(_extract_building_guards(body))
        elif name.lower() in _UNPROVEN_IN:
            continue
        else:
            buildings.update(_extract_absent_buildings(body))
    return buildings


def _direct_text(text: str, start: int, end: int, blocks) -> str:
    parts = []
    cursor = start
    for _, name_start, _, body_end in blocks:
        parts.append(text[cursor:name_start])
        cursor = body_end + 1
    parts.append(text[cursor:end])
    return " ".join(parts)


def _has_infrastructure_slot_guard(text: str) -> bool:
    """Recognize guards in this state, without following alternate scopes."""
    blocks = _child_blocks(text, 0, len(text))
    cursor = 0
    for name, name_start, body_start, body_end in blocks:
        if _INFRASTRUCTURE_GUARD_RE.search(text, cursor, name_start):
            return True
        body = text[body_start:body_end]
        if name == "free_building_slots":
            fields = _direct_text(body, 0, len(body), _child_blocks(body, 0, len(body)))
            building = _SLOT_BUILDING_RE.search(fields)
            if building and building.group(1) == "infrastructure":
                if any(
                    _proves_present(match.group(1), int(match.group(2)))
                    for match in _SLOT_COUNT_RE.finditer(fields)
                ):
                    return True
        elif name.lower() == "and" and _has_infrastructure_slot_guard(body):
            return True
        cursor = body_end + 1
    return bool(_INFRASTRUCTURE_GUARD_RE.search(text, cursor))


def _has_infrastructure_level_bound(text: str) -> bool:
    """Find a same-state upper bound without inferring that a slot is free."""
    if "infrastructure" in _comparisons_outside_blocks(
        text, lambda op, _: op in ("<", "<=")
    ):
        return True
    return any(
        name.lower() == "and" and _has_infrastructure_level_bound(text[start:end])
        for name, _, start, end in _child_blocks(text, 0, len(text))
    )


def _assignments(text: str):
    """Yield (enclosing block keys, key, value, line) for each `key = value`,
    where value is "{" when the assignment opens a block."""
    clean = blank_quoted_strings(strip_comments(text))
    tokens = list(_TOKEN_RE.finditer(clean))
    path: List[str] = []
    line, last, index = 1, 0, 0
    while index < len(tokens):
        value = tokens[index].group()
        if value == "}":
            if path:
                path.pop()
            index += 1
            continue
        if (
            value not in ("{", "=")
            and index + 2 < len(tokens)
            and tokens[index + 1].group() == "="
        ):
            line += clean.count("\n", last, tokens[index].start())
            last = tokens[index].start()
            rhs = tokens[index + 2].group()
            yield tuple(path), value, rhs, line
            if rhs == "{":
                path.append(value)
            index += 3
            continue
        if value == "{":
            path.append("")
        index += 1


def coastal_provincial_buildings(text: str) -> Set[str]:
    """Names of buildings with `only_costal = yes` and a `province_max` cap."""
    coastal: Set[str] = set()
    provincial: Set[str] = set()
    for path, key, value, _line in _assignments(text):
        if len(path) < 2 or path[0] != "buildings":
            continue
        if len(path) == 2 and key == "only_costal" and value == "yes":
            coastal.add(path[1])
        elif key == "province_max" and path[2:] == ("level_cap",):
            provincial.add(path[1])
    return coastal & provincial


def coastal_land_provinces(text: str) -> Tuple[Set[int], Set[int]]:
    """Return (every province id, coastal land province ids) from definition.csv."""
    known: Set[int] = set()
    coastal: Set[int] = set()
    for row in text.splitlines():
        fields = row.split(";")
        if len(fields) < 6 or not fields[0].strip().isdigit():
            continue
        province = int(fields[0])
        known.add(province)
        if fields[4].strip() == "land" and fields[5].strip() == "true":
            coastal.add(province)
    return known, coastal


def province_placements(text: str) -> List[Tuple[str, int, int]]:
    """(building, province, line) for every building placed in a fixed province."""
    placements: List[Tuple[str, int, int]] = []
    building: Optional[str] = None
    provinces: List[Tuple[int, int]] = []
    depth = -1

    def flush():
        if building:
            placements.extend(
                (building, province, line) for province, line in provinces
            )

    for path, key, value, line in _assignments(text):
        if depth >= 0 and (
            len(path) <= depth or path[depth] != "add_building_construction"
        ):
            flush()
            building, provinces, depth = None, [], -1

        if key == "add_building_construction" and value == "{":
            building, provinces, depth = None, [], len(path)
            continue

        if depth >= 0:
            inner = path[depth + 1 :]
            if not inner and key == "type" and _IDENTIFIER_RE.match(value):
                building = value
            elif _PROVINCE_ID_RE.match(value) and (
                (not inner and key == "province")
                or (inner == ("province",) and key == "id")
            ):
                provinces.append((int(value), line))
            continue

        if (
            len(path) >= 2
            and path[-2] == "buildings"
            and _PROVINCE_ID_RE.match(path[-1])
            and _IDENTIFIER_RE.match(key)
            and value != "{"
        ):
            placements.append((key, int(path[-1]), line))

    flush()
    return placements


def _coastal_rows(
    relative: str, placements: List[Tuple[str, int, int]], coastal: CoastalReference
) -> List[Tuple[str, str, int, str]]:
    buildings, coastal_provinces, known = coastal
    rows = []
    for building, province, line in placements:
        if building not in buildings or province in coastal_provinces:
            continue
        if province in known:
            reason = f"which {DEFINITION_FILE} does not mark as coastal land"
        else:
            reason = f"which is not in {DEFINITION_FILE}"
        message = (
            f"coastal building '{building}' is placed in province {province}, {reason}"
        )
        rows.append(("coastal-building-not-coastal", relative, line, message))
    return rows


class Scanner:
    """Walks one file's script tree, tracking buildings proven present."""

    def __init__(self, text: str):
        self.text = text
        self.offsets = compute_line_offsets(text)
        self.findings: List[Tuple[str, int, str]] = []

    def check_province_building_triggers(self):
        for offset, trigger, building in _find_province_building_triggers(self.text):
            line = line_for_offset(self.offsets, offset)
            message = (
                f"{trigger} = {{ building = {building} ... }} cannot resolve "
                f"{building}, which is a province building; use "
                f"`{building} > 0` or any_province_building_level"
            )
            self.findings.append(("province-building-state-trigger", line, message))

    def check_random_infrastructure_slots(self, start: int, end: int):
        text = self.text[start:end]
        if (
            "add_building_construction" not in text
            or "infrastructure" not in text
            or not any(name in text for name in _CHECKED_RANDOM_SELECTORS)
        ):
            return
        for name, _, body_start, body_end in _child_blocks(self.text, start, end):
            if name in _SKIP_BLOCKS or name == "modifier":
                continue
            blocks = _child_blocks(self.text, body_start, body_end)
            selected = name in _RANDOM_STATE_SELECTORS
            if name in _RANDOM_SUBSET_SELECTORS:
                # Only a direct random_select_amount field applies to this iterator.
                direct = _direct_text(self.text, body_start, body_end, blocks)
                selected = bool(_RANDOM_SELECT_RE.search(direct))
            if selected:
                guarded = any(
                    child == "limit"
                    and _has_infrastructure_slot_guard(self.text[c_start:c_end])
                    for child, _, c_start, c_end in blocks
                )
                if not guarded:
                    level_bound = any(
                        child == "limit"
                        and _has_infrastructure_level_bound(self.text[c_start:c_end])
                        for child, _, c_start, c_end in blocks
                    )
                    for child, _, c_start, c_end in blocks:
                        if child != "add_building_construction":
                            continue
                        building = _TYPE_RE.search(self.text[c_start:c_end])
                        if building and building.group(1) == "infrastructure":
                            line = line_for_offset(self.offsets, c_start)
                            self.findings.append(
                                (
                                    "random-infrastructure-slot-guard",
                                    line,
                                    "randomly selected state builds infrastructure "
                                    "without a recognized slot guard in its limit"
                                    + (
                                        "; a level bound is present but slot availability "
                                        "is not verified"
                                        if level_bound
                                        else ""
                                    ),
                                )
                            )
            self.check_random_infrastructure_slots(body_start, body_end)

    def _check_effect(
        self, effect: str, category: str, body_start: int, body_end: int, ctx: Context
    ):
        match = _TYPE_RE.search(self.text[body_start:body_end])
        if not match:
            return
        building = match.group(1)
        if building in ctx.present:
            return
        line = line_for_offset(self.offsets, body_start)
        message = (
            f"{effect} = {{ type = {building} ... }} is not guarded by a check "
            f"that {building} exists"
        )
        self.findings.append((category, line, message))

    def _buildings_from_limit(self, body_start: int, body_end: int) -> Set[str]:
        for sub, _, s_start, s_end in _child_blocks(self.text, body_start, body_end):
            if sub == "limit":
                return _extract_building_guards(self.text[s_start:s_end])
        return set()

    def walk(self, start: int, end: int, ctx: Context):
        blocks = _child_blocks(self.text, start, end)

        gate_buildings: Set[str] = set()
        for name, _, body_start, body_end in blocks:
            if name == "modifier":
                body = self.text[body_start:body_end]
                if FACTOR_ZERO_RE.search(body):
                    gate_buildings |= _extract_absent_buildings(body)
        ctx = ctx.apply(gate_buildings)

        for name, _, body_start, body_end in blocks:
            if name in _SKIP_BLOCKS or name == "modifier":
                continue
            category = _BUILDING_EFFECTS.get(name)
            if category is not None:
                self._check_effect(name, category, body_start, body_end, ctx)
                continue
            inherited = Context() if _STATE_SELECTOR_RE.match(name) else ctx
            self.walk(
                body_start,
                body_end,
                inherited.apply(self._buildings_from_limit(body_start, body_end)),
            )


def scan_file(args: Tuple[str, str]) -> List[Tuple[str, str, int, str]]:
    """Return (category, relative path, line, message) for one content file."""
    filepath, mod_path = args
    raw = read_file(filepath)
    has_existing_checks = any(
        token in raw
        for token in (
            "damage_building",
            "remove_building",
            *_STATE_ONLY_BUILDING_TRIGGERS,
        )
    )
    has_random_infrastructure = (
        "add_building_construction" in raw
        and "infrastructure" in raw
        and any(name in raw for name in _CHECKED_RANDOM_SELECTORS)
    )
    # Placements are cached whatever the coastal reference holds, so the
    # cached entry depends on the file content alone.
    has_placements = "add_building_construction" in raw or "buildings" in raw
    if not (has_existing_checks or has_random_infrastructure or has_placements):
        return []

    def compute():
        scanner = Scanner(_sanitize(raw))
        if has_existing_checks:
            scanner.walk(0, len(scanner.text), Context())
            scanner.check_province_building_triggers()
        if has_random_infrastructure:
            scanner.check_random_infrastructure_slots(0, len(scanner.text))
        placements = province_placements(raw) if has_placements else []
        return scanner.findings, placements

    findings, placements = disk_cache.per_file_cached_by_content(
        mod_path, "building_guards_scan_v8", filepath, raw, compute
    )
    relative = os.path.relpath(filepath, mod_path).replace(os.sep, "/")
    rows = [(category, relative, line, message) for category, line, message in findings]
    if _COASTAL is not None:
        rows.extend(_coastal_rows(relative, placements, _COASTAL))
    return rows


class Validator(BaseValidator):
    TITLE = "BUILDING GUARD VALIDATION"
    STAGED_EXTENSIONS = [".txt", ".csv"]

    def _coastal_reference(self) -> Optional[CoastalReference]:
        buildings: Set[str] = set()
        for path in self._collect_files([_BUILDINGS_GLOB], ignore_staged=True):
            buildings |= coastal_provincial_buildings(read_file(path))
        if not buildings:
            return None
        try:
            definition = read_file(os.path.join(self.mod_path, DEFINITION_FILE))
        except ValueError:
            self.add_warning(
                "coastal-building-definition-missing",
                f"cannot check coastal building placement because "
                f"{DEFINITION_FILE} is missing",
                DEFINITION_FILE,
            )
            return None
        known, coastal_provinces = coastal_land_provinces(definition)
        return frozenset(buildings), frozenset(coastal_provinces), frozenset(known)

    def validate_building_guards(self):
        self._log_section("damage_building / remove_building existence guards")
        coastal = self._coastal_reference()
        # A changed building or province definition can break any placement.
        reference_changed = self.staged_only and (
            self.staged_touches(("common/buildings",))
            or any(
                path.replace("\\", "/").endswith(DEFINITION_FILE)
                for path in self.staged_files or []
            )
        )
        files = self._collect_files(_SCAN_GLOBS, ignore_staged=reference_changed)
        results = self._pool_map_init(
            scan_file, [(f, self.mod_path) for f in files], _init_worker, (coastal,)
        )
        rows = sorted(row for rows in results for row in rows)

        report_findings(
            self,
            [row for row in rows if row[0].startswith("unguarded-")],
            self.add_error,
            "unguarded building effect(s)",
            "All damage_building/remove_building effects are guarded",
        )

        self._log_section("province buildings named in state-only triggers")
        report_findings(
            self,
            [row for row in rows if row[0] == "province-building-state-trigger"],
            self.add_error,
            "province building(s) named in a state-only trigger",
            "No province buildings named in state-only building triggers",
        )

        self._log_section("randomly selected infrastructure construction")
        report_findings(
            self,
            [row for row in rows if row[0] == "random-infrastructure-slot-guard"],
            self.add_warning,
            "random infrastructure construction(s) without a recognized slot guard",
            "Checked random-state infrastructure constructions have recognized slot guards",
        )

        self._log_section("coastal buildings in fixed provinces")
        report_findings(
            self,
            [row for row in rows if row[0] == "coastal-building-not-coastal"],
            self.add_warning,
            "coastal building(s) placed in a province that is not coastal land",
            "Every fixed-province coastal building sits in coastal land",
        )

    def run_validations(self):
        self.validate_building_guards()


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate that damage_building/remove_building effects are guarded by a "
        "building-existence check",
    )
