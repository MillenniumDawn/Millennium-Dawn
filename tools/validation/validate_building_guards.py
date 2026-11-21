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

The advisory random-state slot check covers direct construction effects in
selected random-state iterators and randomly limited every-state iterators. It
looks for a free slot proven in the selector's own limit (`free_building_slots`
or a scripted trigger built on it), or made earlier in the same block by
`add_extra_state_shared_building_slots` or a `remove_building` of a building
the limit proves present. Shared-slot buildings share one proof. Province
buildings are skipped: `free_building_slots` only checks them for a fixed
province.

The same file walk also checks where buildings go and who owns them:

  - `add_building_construction` of a provincial building (a `province_max` cap
    in `common/buildings/`) with no `province` key. The engine rejects it.
  - `province = { province = 1234 }` inside `add_building_construction`. The
    block form takes a selector, not an id, so nothing is built.
  - A coastal provincial building (`only_costal = yes`, the engine's spelling)
    placed in a province that `map/definition.csv` does not mark as coastal
    land, through a state history province block or a construction's
    `province = 1234` / `province = { id = 1234 }`. Runtime picks are not checked.
  - A tag starting with a `nuclear_reactor` must grant a non-default
    `nuclear_status` idea, and a tag starting with a building a special project
    grants must complete that project, in its `history/countries/` file.
"""

import hashlib
import os
import re
import sys
from collections import defaultdict
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

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
_TRIGGER_CALL_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*=\s*yes\b")
_EXTRA_SHARED_SLOTS_RE = re.compile(
    r"\badd_extra_state_shared_building_slots\s*=\s*(?!-)(?!0(?![\w.]))[^\s{}]+"
)
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
DEFINITION_FILE = "map/definition.csv"
_BUILDINGS_GLOB = "common/buildings/*.txt"
_SCRIPTED_TRIGGERS_GLOB = "common/scripted_triggers/*.txt"
_SCAN_GLOBS = ["common/**/*.txt", "events/**/*.txt", "history/**/*.txt"]
# Inputs of the cross-file ownership checks, scanned in full in staged mode too.
_OWNERSHIP_GLOBS = [
    "history/states/*.txt",
    "history/countries/*.txt",
    "common/ideas/*.txt",
    "common/special_projects/projects/*.txt",
]
_TOKEN_RE = re.compile(r"[^\s{}=]+|[{}=]")
_IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_PROVINCE_ID_RE = re.compile(r"\d+\Z")
_PROJECT_PREFIX = "sp:"

# Set in each worker by _init_worker from common/buildings/, map/definition.csv,
# and common/scripted_triggers/.
_PROVINCIAL: FrozenSet[str] = frozenset()
_COASTAL_BUILDINGS: FrozenSet[str] = frozenset()
_COASTAL_PROVINCES: FrozenSet[int] = frozenset()
_KNOWN_PROVINCES: FrozenSet[int] = frozenset()
_SHARED_SLOTS: FrozenSet[str] = frozenset()
_SLOT_TRIGGERS: Dict[str, FrozenSet[str]] = {}
_FINGERPRINT = ""


def _init_worker(
    provincial: FrozenSet[str],
    coastal_buildings: FrozenSet[str],
    coastal_provinces: FrozenSet[int],
    known_provinces: FrozenSet[int],
    shared_slots: FrozenSet[str],
    triggers: Dict[str, FrozenSet[str]],
) -> None:
    global _PROVINCIAL, _COASTAL_BUILDINGS, _COASTAL_PROVINCES, _KNOWN_PROVINCES
    global _SHARED_SLOTS, _SLOT_TRIGGERS, _FINGERPRINT
    _PROVINCIAL = provincial
    _COASTAL_BUILDINGS = coastal_buildings
    _COASTAL_PROVINCES = coastal_provinces
    _KNOWN_PROVINCES = known_provinces
    _SHARED_SLOTS = shared_slots
    _SLOT_TRIGGERS = triggers
    reference = (
        provincial,
        coastal_buildings,
        coastal_provinces,
        known_provinces,
        shared_slots,
        [f"{name}={','.join(sorted(b))}" for name, b in triggers.items()],
    )
    _FINGERPRINT = hashlib.sha256(
        repr([sorted(part) for part in reference]).encode("utf-8")
    ).hexdigest()


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
                if building in _PROVINCIAL:
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
                named -= _PROVINCIAL
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


def _slot_guards(text: str, triggers: Dict[str, FrozenSet[str]]) -> Set[str]:
    """Buildings this state's triggers prove have a free slot, without following
    alternate scopes or branches."""
    blocks = _child_blocks(text, 0, len(text))
    guards: Set[str] = set()
    for call in _TRIGGER_CALL_RE.finditer(_direct_text(text, 0, len(text), blocks)):
        guards |= triggers.get(call.group(1), frozenset())
    for name, _, body_start, body_end in blocks:
        body = text[body_start:body_end]
        if name == "free_building_slots":
            fields = _direct_text(body, 0, len(body), _child_blocks(body, 0, len(body)))
            building = _SLOT_BUILDING_RE.search(fields)
            if building and any(
                _proves_present(match.group(1), int(match.group(2)))
                for match in _SLOT_COUNT_RE.finditer(fields)
            ):
                guards.add(building.group(1))
        elif name.lower() == "and":
            guards |= _slot_guards(body, triggers)
    return guards


def slot_triggers(text: str) -> Dict[str, FrozenSet[str]]:
    """Scripted triggers in one file that prove a free slot -> those buildings."""
    clean = _sanitize(text)
    found = {}
    for name, _, body_start, body_end in _child_blocks(clean, 0, len(clean)):
        guards = _slot_guards(clean[body_start:body_end], {})
        if guards:
            found[name] = frozenset(guards)
    return found


def _has_level_bound(text: str, building: str) -> bool:
    """Find a same-state upper bound without inferring that a slot is free."""
    if building in _comparisons_outside_blocks(text, lambda op, _: op in ("<", "<=")):
        return True
    return any(
        name.lower() == "and" and _has_level_bound(text[start:end], building)
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


def building_classes(text: str) -> Tuple[Set[str], Set[str], Set[str]]:
    """(provincial, coastal provincial, shared-slot) building names from a
    buildings file.

    A `level_cap = { province_max = N }` makes a building provincial,
    `only_costal = yes` makes it coastal, and `level_cap = { shares_slots = yes }`
    puts it in the shared state slots.
    """
    coastal: Set[str] = set()
    provincial: Set[str] = set()
    shared: Set[str] = set()
    for path, key, value, _line in _assignments(text):
        if len(path) < 2 or path[0] != "buildings":
            continue
        if len(path) == 2 and key == "only_costal" and value == "yes":
            coastal.add(path[1])
        elif key == "province_max" and path[2:] == ("level_cap",):
            provincial.add(path[1])
        elif (key, value) == ("shares_slots", "yes") and path[2:] == ("level_cap",):
            shared.add(path[1])
    return provincial, coastal & provincial, shared


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


def _coastal_finding(building: str, province: int, line: int):
    if building not in _COASTAL_BUILDINGS or province in _COASTAL_PROVINCES:
        return []
    if province in _KNOWN_PROVINCES:
        reason = f"which {DEFINITION_FILE} does not mark as coastal land"
    else:
        reason = f"which is not in {DEFINITION_FILE}"
    message = (
        f"coastal building '{building}' is placed in province {province}, {reason}"
    )
    return [("coastal-building-not-coastal", line, message)]


def _construction_findings(construction: list):
    building, line, has_province, provinces = construction
    if building is None:
        return []
    findings = []
    if building in _PROVINCIAL and not has_province:
        findings.append(
            (
                "building-missing-province",
                line,
                f"add_building_construction type = {building} has no "
                f"province -- it is a provincial building, so the engine rejects "
                f"the effect and nothing is built; add province = <id> or "
                f"province = {{ all_provinces = yes ... }}",
            )
        )
    for province, province_line in provinces:
        findings.extend(_coastal_finding(building, province, province_line))
    return findings


def placement_findings(text: str, is_state: bool):
    """Province-target findings for one file, plus a state file's owner and its
    state-level buildings at level 1 or more."""
    findings: List[Tuple[str, int, str]] = []
    owner: Optional[str] = None
    state_buildings: Set[str] = set()
    construction: list = []  # [type, line, has province, provinces] while open
    depth = -1

    for path, key, value, line in _assignments(text):
        if construction and (
            len(path) <= depth or path[depth] != "add_building_construction"
        ):
            findings.extend(_construction_findings(construction))
            construction, depth = [], -1

        if key == "add_building_construction" and value == "{":
            construction, depth = [None, line, False, []], len(path)
            continue

        if construction:
            inner = path[depth + 1 :]
            is_id = bool(_PROVINCE_ID_RE.match(value))
            if not inner and key == "type" and _IDENTIFIER_RE.match(value):
                construction[0] = value
            if key == "province":
                construction[2] = True
            if is_id and (
                (not inner and key == "province")
                or (inner == ("province",) and key == "id")
            ):
                construction[3].append((int(value), line))
            if is_id and inner == ("province",) and key == "province":
                findings.append(
                    (
                        "province-id-in-selector-block",
                        line,
                        "province = { province = <id> } is not a valid selector -- "
                        "the engine rejects the add_building token and nothing is "
                        "built; write province = <id>",
                    )
                )
            continue

        if not is_state:
            continue
        if owner is None and key == "owner":
            owner = value
        if path and path[-1] == "buildings" and _IDENTIFIER_RE.match(key):
            if value.isdigit() and int(value) >= 1:
                state_buildings.add(key)
        elif (
            len(path) >= 2
            and path[-2] == "buildings"
            and _PROVINCE_ID_RE.match(path[-1])
            and _IDENTIFIER_RE.match(key)
            and value != "{"
        ):
            findings.extend(_coastal_finding(key, int(path[-1]), line))

    if construction:
        findings.extend(_construction_findings(construction))
    return findings, owner, frozenset(state_buildings)


def nuclear_status_ideas(text: str) -> Set[str]:
    """Non-default members of a `nuclear_status` idea group."""
    members: Set[str] = set()
    defaults: Set[str] = set()
    for path, key, value, _line in _assignments(text):
        if path and path[-1] == "nuclear_status" and value == "{":
            members.add(key)
        elif path[-2:-1] == ("nuclear_status",) and (key, value) == ("default", "yes"):
            defaults.add(path[-1])
    return members - defaults


def project_building_grants(text: str) -> Set[Tuple[str, str]]:
    """(building, project) for each `set_building_level` in a project file."""
    return {
        (value, path[0])
        for path, key, value, _line in _assignments(text)
        if key == "type" and path and path[-1] == "set_building_level"
    }


def country_facts(text: str) -> Tuple[FrozenSet[str], FrozenSet[str]]:
    """(every token, completed special projects) of a country history file."""
    tokens = frozenset(_TOKEN_RE.findall(blank_quoted_strings(strip_comments(text))))
    completed = frozenset(
        value[len(_PROJECT_PREFIX) :]
        for _path, key, value, _line in _assignments(text)
        if key == "complete_special_project" and value.startswith(_PROJECT_PREFIX)
    )
    return tokens, completed


def _country_tag(relative: str) -> str:
    name = os.path.basename(relative)
    return name.split(" - ")[0] if " - " in name else os.path.splitext(name)[0]


def ownership_findings(facts: Dict[str, dict]) -> List[Tuple[str, str, int, str]]:
    """Join state owners with their country files, nuclear_status ideas, and
    special-project building grants."""
    owners: Dict[str, Set[str]] = defaultdict(set)
    countries: Dict[str, Tuple[str, FrozenSet[str], FrozenSet[str]]] = {}
    ideas: Set[str] = set()
    granted: Dict[str, Set[str]] = defaultdict(set)
    for relative, fact in facts.items():
        if fact.get("owner"):
            for building in fact["buildings"]:
                owners[building].add(fact["owner"])
        if "tokens" in fact:
            countries[_country_tag(relative)] = (
                relative,
                fact["tokens"],
                fact["completed"],
            )
        ideas |= fact.get("nuclear_ideas", set())
        for building, project in fact.get("granted", ()):
            granted[building].add(project)

    rows = []
    if ideas:
        for tag in sorted(owners.get("nuclear_reactor", ())):
            country = countries.get(tag)
            if country is None:
                message = (
                    f"{tag}: owns a state with a nuclear_reactor at game start "
                    f"but has no history/countries/ file"
                )
                rows.append(("reactor-owner-without-nuclear-status", "", 0, message))
            elif not ideas & country[1]:
                message = (
                    f"{tag}: owns a state with a nuclear_reactor at game start "
                    f"but grants no nuclear_status idea ({', '.join(sorted(ideas))})"
                )
                rows.append(
                    ("reactor-owner-without-nuclear-status", country[0], 0, message)
                )
    for building in sorted(granted):
        projects = granted[building]
        for tag in sorted(owners.get(building, ())):
            country = countries.get(tag)
            if country is None:
                message = (
                    f"{tag}: owns a state starting with {building} but has "
                    f"no history/countries/ file"
                )
                rows.append(("granted-building-without-project", "", 0, message))
            elif not projects & country[2]:
                listed = ", ".join(f"sp:{p}" for p in sorted(projects))
                message = (
                    f"{tag}: owns a state starting with {building} but never "
                    f"completes the granting special project ({listed})"
                )
                rows.append(
                    ("granted-building-without-project", country[0], 0, message)
                )
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

    def check_random_slot_guards(self, start: int, end: int):
        text = self.text[start:end]
        if "add_building_construction" not in text or not any(
            name in text for name in _CHECKED_RANDOM_SELECTORS
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
                self._check_selected_constructions(body_start, body_end, blocks)
            self.check_random_slot_guards(body_start, body_end)

    def _check_selected_constructions(self, start: int, end: int, blocks):
        limits = [self.text[s:e] for child, _, s, e in blocks if child == "limit"]
        guards: Set[str] = set()
        present: Set[str] = set()
        for limit in limits:
            guards |= _slot_guards(limit, _SLOT_TRIGGERS)
            present |= _extract_building_guards(limit)
        # Effects run in order, so an extra shared slot or a removed building
        # frees room only for the constructions after it.
        cursor = start
        for child, name_start, c_start, c_end in blocks:
            if _EXTRA_SHARED_SLOTS_RE.search(self.text, cursor, name_start):
                guards |= _SHARED_SLOTS
            cursor = c_end + 1
            match = _TYPE_RE.search(self.text[c_start:c_end])
            if not match:
                continue
            building = match.group(1)
            if child == "remove_building":
                if building in present:
                    guards.add(building)
                continue
            if child != "add_building_construction" or building in _PROVINCIAL:
                continue
            if building in guards or (
                building in _SHARED_SLOTS and guards & _SHARED_SLOTS
            ):
                continue
            message = (
                f"randomly selected state builds {building} without a recognized "
                "slot guard in its limit"
            )
            if any(_has_level_bound(limit, building) for limit in limits):
                message += (
                    "; a level bound is present but slot availability is not verified"
                )
            if building in _SHARED_SLOTS and _EXTRA_SHARED_SLOTS_RE.search(
                self.text, c_end, end
            ):
                message += "; the extra shared slots are only added after it"
            line = line_for_offset(self.offsets, c_start)
            self.findings.append(("random-building-slot-guard", line, message))

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


def scan_file(args: Tuple[str, str]) -> Tuple[List[Tuple[str, str, int, str]], dict]:
    """Return (category, relative path, line, message) rows for one content
    file, and the facts the ownership checks join across files."""
    filepath, mod_path = args
    raw = read_file(filepath)
    relative = os.path.relpath(filepath, mod_path).replace(os.sep, "/")
    has_existing_checks = any(
        token in raw
        for token in (
            "damage_building",
            "remove_building",
            *_STATE_ONLY_BUILDING_TRIGGERS,
        )
    )
    has_random_construction = "add_building_construction" in raw and any(
        name in raw for name in _CHECKED_RANDOM_SELECTORS
    )
    is_state = relative.startswith("history/states/")
    is_country = relative.startswith("history/countries/")
    is_ideas = relative.startswith("common/ideas/") and "nuclear_status" in raw
    is_projects = (
        relative.startswith("common/special_projects/projects/")
        and "set_building_level" in raw
    )
    has_placements = is_state or "add_building_construction" in raw
    if not (
        has_existing_checks
        or has_random_construction
        or has_placements
        or is_country
        or is_ideas
        or is_projects
    ):
        return [], {}

    def compute():
        scanner = Scanner(_sanitize(raw))
        if has_existing_checks:
            scanner.walk(0, len(scanner.text), Context())
            scanner.check_province_building_triggers()
        if has_random_construction:
            scanner.check_random_slot_guards(0, len(scanner.text))
        findings = scanner.findings
        facts: dict = {}
        if has_placements:
            placed, owner, buildings = placement_findings(raw, is_state)
            findings = findings + placed
            if is_state:
                facts = {"owner": owner, "buildings": buildings}
        if is_country:
            tokens, completed = country_facts(raw)
            facts = {"tokens": tokens, "completed": completed}
        if is_ideas:
            facts = {"nuclear_ideas": nuclear_status_ideas(raw)}
        if is_projects:
            facts = {"granted": project_building_grants(raw)}
        return findings, facts

    findings, facts = disk_cache.per_file_cached_by_content(
        mod_path,
        "building_guards_scan_v9",
        filepath,
        raw + "\x00" + _FINGERPRINT,
        compute,
    )
    rows = [(category, relative, line, message) for category, line, message in findings]
    return rows, facts


class Validator(BaseValidator):
    TITLE = "BUILDING VALIDATION"
    STAGED_EXTENSIONS = [".txt", ".csv"]

    def _relative(self, path: str) -> str:
        return os.path.relpath(path, self.mod_path).replace(os.sep, "/")

    def _reference(self) -> tuple:
        provincial: Set[str] = set()
        coastal: Set[str] = set()
        shared: Set[str] = set()
        for path in self._collect_files([_BUILDINGS_GLOB], ignore_staged=True):
            file_provincial, file_coastal, file_shared = building_classes(
                read_file(path)
            )
            provincial |= file_provincial
            coastal |= file_coastal
            shared |= file_shared
        triggers: Dict[str, FrozenSet[str]] = {}
        for path in self._collect_files([_SCRIPTED_TRIGGERS_GLOB], ignore_staged=True):
            triggers.update(slot_triggers(read_file(path)))
        known: Set[int] = set()
        coastal_provinces: Set[int] = set()
        if coastal:
            try:
                definition = read_file(os.path.join(self.mod_path, DEFINITION_FILE))
            except ValueError:
                self.add_warning(
                    "coastal-building-definition-missing",
                    f"cannot check coastal building placement because "
                    f"{DEFINITION_FILE} is missing",
                    DEFINITION_FILE,
                )
                coastal = set()
            else:
                known, coastal_provinces = coastal_land_provinces(definition)
        return (
            frozenset(provincial),
            frozenset(coastal),
            frozenset(coastal_provinces),
            frozenset(known),
            frozenset(shared),
            triggers,
        )

    def _scan(self):
        """Walk every file once; return sorted rows and per-file ownership facts."""
        # A changed building, province or slot trigger definition can break any site.
        reference_changed = self.staged_only and (
            self.staged_touches(("common/buildings", "common/scripted_triggers"))
            or any(
                path.replace("\\", "/").endswith(DEFINITION_FILE)
                for path in self.staged_files or []
            )
        )
        files = self._collect_files(_SCAN_GLOBS, ignore_staged=reference_changed)
        scoped: Optional[Set[str]] = None
        if self.staged_only and not reference_changed:
            scoped = {self._relative(path) for path in files}
            files = sorted(
                set(files)
                | set(self._collect_files(_OWNERSHIP_GLOBS, ignore_staged=True))
            )
        scans = self._pool_map_init(
            scan_file,
            [(path, self.mod_path) for path in files],
            _init_worker,
            self._reference(),
        )
        rows = sorted(
            row
            for file_rows, _facts in scans
            for row in file_rows
            if scoped is None or row[1] in scoped
        )
        facts = {
            self._relative(path): file_facts
            for path, (_rows, file_facts) in zip(files, scans)
            if file_facts
        }
        return rows, facts

    def validate_buildings(self):
        self._log_section("damage_building / remove_building existence guards")
        rows, facts = self._scan()

        def section(title, categories, record, summary, clean):
            self._log_section(title)
            report_findings(
                self,
                [row for row in rows if row[0] in categories],
                record,
                summary,
                clean,
            )

        report_findings(
            self,
            [row for row in rows if row[0].startswith("unguarded-")],
            self.add_error,
            "unguarded building effect(s)",
            "All damage_building/remove_building effects are guarded",
        )
        section(
            "province buildings named in state-only triggers",
            ("province-building-state-trigger",),
            self.add_error,
            "province building(s) named in a state-only trigger",
            "No province buildings named in state-only building triggers",
        )
        section(
            "randomly selected building construction",
            ("random-building-slot-guard",),
            self.add_warning,
            "random building construction(s) without a recognized slot guard",
            "Checked random-state building constructions have recognized slot guards",
        )
        section(
            "add_building_construction province targets",
            ("building-missing-province", "province-id-in-selector-block"),
            self.add_error,
            "building construction(s) with no valid province target",
            "Every provincial building construction names a valid province target",
        )
        section(
            "coastal buildings in fixed provinces",
            ("coastal-building-not-coastal",),
            self.add_error,
            "coastal building(s) placed in a province that is not coastal land",
            "Every fixed-province coastal building sits in coastal land",
        )

        self._log_section("starting building owners")
        report_findings(
            self,
            ownership_findings(facts),
            self.add_error,
            "starting building owner(s) missing a required idea or project",
            "Every starting reactor and project-granted building owner is covered",
        )

    def run_validations(self):
        self.validate_buildings()


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate building effects, placements, and starting building owners",
    )
