#!/usr/bin/env python3
# Check that every equipment archetype a land battalion fields is charged
# maintenance by the money system. The equipment_operative_cost accumulator in
# `update_military_rate` is a hand-written list of per-archetype blocks with
# nothing tying it to the units that exist, so an archetype added later is
# simply free forever: MLRS (medium_tank_rocket_chassis) was never in it, and
# neither were the walker chassis, land drones, or the orbital fire control
# relay (issue #3578). Nothing in game surfaces the omission — the cost lands in
# one aggregated Army Operational Cost figure — so only a cross-reference finds
# it.
import os
import re
import sys
from typing import Dict, List, Optional, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from equipment_module_slots import (
    _depth0_text,
    _iter_blocks,
    blank_comments,
    parse_duplicate_archetypes,
)
from shared_utils import FileOpener, find_matching_brace
from validator_common import BaseValidator, Severity, run_validator_main

EQUIPMENT_GLOB = "common/units/equipment/**/*.txt"
UNIT_GLOB = "common/units/*.txt"
MONEY_FILE = "common/scripted_effects/00_money_system.txt"

_TRIGGER_PATTERNS = [EQUIPMENT_GLOB, UNIT_GLOB, MONEY_FILE]

_ACCUMULATOR = "equipment_operative_cost"

# Ships and planes are costed by a different model entirely
# (num_ships_with_type@ and weighted plane buckets), so only land battalions are
# in scope. A sub_unit that draws a map counter is a land battalion; air wings
# and missile batteries carry land_air_wing_size instead and no map icon.
_LAND_MARKER = "map_icon_category"

# Archetypes deliberately charged nothing, with the reason each one is exempt.
# Anything not listed here that a land battalion needs is a finding.
UPKEEP_EXEMPT: Dict[str, str] = {
    "zombie": "event-spawned infection, never produced or stockpiled",
    "zombie_runner": "event-spawned infection, never produced or stockpiled",
    "zombie_brute": "event-spawned infection, never produced or stockpiled",
    "HACS_equipment": "build_cost_ic 99999999 — never buildable by design",
    "CHIMERA_equipment": "event-granted special content, outside the economy",
}

_NEED_KEYS = ("need", "essential")
_TOKEN_RE = re.compile(r"[A-Za-z_]\w*")
_TRANSPORT_RE = re.compile(r"\btransport\s*=\s*(\w+)")
_ARCHETYPE_RE = re.compile(r"\barchetype\s*=\s*(\w+)")
_IS_ARCHETYPE_RE = re.compile(r"\bis_archetype\s*=\s*yes\b")
_ADD_TO_VARIABLE_RE = re.compile(r"\badd_to_variable\s*=\s*\{")
_VAR_RE = re.compile(r"\bvar\s*=\s*" + _ACCUMULATOR + r"\b")
_DEPLOYED_RE = re.compile(r"num_equipment_in_armies(?:_k)?@(\w+)")
_STOCKPILE_RE = re.compile(r"num_equipment@(\w+)")
_INIT_RE = re.compile(r"\bset_variable\s*=\s*\{\s*" + _ACCUMULATOR + r"\s*=")


def _read(path: str) -> Optional[str]:
    """File text with comments blanked, keeping every character offset intact."""
    try:
        return blank_comments(FileOpener.open_text_file(path))
    except (OSError, UnicodeDecodeError):
        return None


def _line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _parse_equipment(text: str) -> Tuple[Set[str], Dict[str, str]]:
    """(archetype names, variant -> parent archetype) declared in one file."""
    archetypes: Set[str] = set()
    parents: Dict[str, str] = {}

    containers = [
        (lo, hi)
        for name, lo, hi, _ in _iter_blocks(text, 0, len(text))
        if name == "equipments"
    ]
    if not containers:
        containers = [(0, len(text))]
    for lo, hi in containers:
        for name, blo, bhi, _ in _iter_blocks(text, lo, hi):
            body = _depth0_text(text, blo, bhi)
            if _IS_ARCHETYPE_RE.search(body):
                archetypes.add(name)
            m = _ARCHETYPE_RE.search(body)
            if m:
                parents[name] = m.group(1)

    # duplicate_archetypes entries are archetypes in their own right — the engine
    # clones a whole family under the new name — even though each declares an
    # `archetype =` source, which would otherwise read as a variant.
    dups, _ = parse_duplicate_archetypes(text)
    archetypes.update(dups)
    for dup in dups:
        parents.pop(dup, None)
    return archetypes, parents


def _land_equipment_refs(text: str) -> Dict[str, Tuple[str, int]]:
    """equipment token -> (battalion, line) for every land sub_unit in one file."""
    refs: Dict[str, Tuple[str, int]] = {}
    for name, lo, hi, _ in _iter_blocks(text, 0, len(text)):
        if name != "sub_units":
            continue
        for unit, ulo, uhi, header in _iter_blocks(text, lo, hi):
            body = _depth0_text(text, ulo, uhi)
            if _LAND_MARKER not in body:
                continue
            line = _line_of(text, header)
            tokens: Set[str] = set()
            for key, klo, khi, _ in _iter_blocks(text, ulo, uhi):
                if key in _NEED_KEYS:
                    tokens.update(_TOKEN_RE.findall(_depth0_text(text, klo, khi)))
            tokens.update(_TRANSPORT_RE.findall(body))
            for token in tokens:
                refs.setdefault(token, (unit, line))
    return refs


def _upkeep_terms(text: str) -> Tuple[Set[str], Set[str], int]:
    """(deployed archetypes, stockpiled archetypes, accumulator line).

    Blocks are found by their `var = equipment_operative_cost` assignment rather
    than by position, so reordering or moving the accumulator does not blind the
    check.
    """
    deployed: Set[str] = set()
    stockpiled: Set[str] = set()
    line = 0
    for m in _ADD_TO_VARIABLE_RE.finditer(text):
        open_idx = m.end() - 1
        close = find_matching_brace(text, open_idx)
        if close == -1:
            continue
        body = text[open_idx:close]
        if not _VAR_RE.search(body):
            continue
        if not line:
            line = _line_of(text, m.start())
        deployed.update(_DEPLOYED_RE.findall(body))
        stockpiled.update(_STOCKPILE_RE.findall(body))
    if not line:
        init = _INIT_RE.search(text)
        line = _line_of(text, init.start()) if init else 0
    return deployed, stockpiled, line


class Validator(BaseValidator):
    TITLE = "EQUIPMENT UPKEEP VALIDATION"

    def _resolve(
        self, token: str, archetypes: Set[str], parents: Dict[str, str]
    ) -> str:
        """The archetype *token* belongs to. Battalions name variants directly in
        places (HACS_0), and only the archetype is ever counted."""
        seen: Set[str] = set()
        while token not in archetypes and token in parents and token not in seen:
            seen.add(token)
            token = parents[token]
        return token

    def _load_archetypes(self) -> Tuple[Set[str], Dict[str, str]]:
        archetypes: Set[str] = set()
        parents: Dict[str, str] = {}
        for path in self._collect_files([EQUIPMENT_GLOB], ignore_staged=True):
            text = _read(path)
            if text is None:
                continue
            found, child_of = _parse_equipment(text)
            archetypes.update(found)
            parents.update(child_of)
        self.log(f"  Equipment archetypes: {len(archetypes)}")
        return archetypes, parents

    def _load_land_refs(self) -> Dict[str, Tuple[str, int, str]]:
        """equipment token -> (battalion, line, mod-relative file)."""
        refs: Dict[str, Tuple[str, int, str]] = {}
        for path in self._collect_files([UNIT_GLOB], ignore_staged=True):
            text = _read(path)
            if text is None:
                continue
            rel = os.path.relpath(path, self.mod_path).replace(os.sep, "/")
            for token, (unit, line) in _land_equipment_refs(text).items():
                refs.setdefault(token, (unit, line, rel))
        self.log(f"  Land battalion equipment references: {len(refs)}")
        return refs

    def validate_land_equipment_upkeep(self):
        self._log_section("Checking land equipment maintenance coverage...")

        money_path = os.path.join(self.mod_path, MONEY_FILE)
        money = _read(money_path)
        if money is None:
            self._report(
                [(f"Cannot read {MONEY_FILE}", MONEY_FILE, 0)],
                "",
                "Money system unreadable:",
                severity=Severity.ERROR,
                category="upkeep-accumulator-missing",
            )
            return

        deployed, stockpiled, acc_line = _upkeep_terms(money)
        if not deployed and not stockpiled:
            # A rename or a refactor moved the accumulator. Reporting every
            # archetype as uncosted would bury that under 20 identical findings.
            self._report(
                [
                    (
                        f"No '{_ACCUMULATOR}' entries found — the accumulator was "
                        "renamed or removed, so upkeep coverage cannot be checked",
                        MONEY_FILE,
                        acc_line,
                    )
                ],
                "",
                "Equipment upkeep accumulator missing:",
                severity=Severity.ERROR,
                category="upkeep-accumulator-missing",
            )
            return

        archetypes, parents = self.cached("equipment_archetypes", self._load_archetypes)
        refs = self.cached("land_equipment_refs", self._load_land_refs)

        needed: Dict[str, Tuple[str, str]] = {}
        for token, (unit, line, rel) in refs.items():
            needed.setdefault(self._resolve(token, archetypes, parents), (unit, rel))

        uncosted: List[Tuple[str, str, int]] = []
        partial: List[Tuple[str, str, int]] = []
        for archetype, (unit, rel) in sorted(needed.items()):
            if archetype in UPKEEP_EXEMPT:
                continue
            has_deployed = archetype in deployed
            has_stockpile = archetype in stockpiled
            if not has_deployed and not has_stockpile:
                uncosted.append(
                    (
                        f"Land equipment archetype '{archetype}' has no "
                        f"{_ACCUMULATOR} entry, so it is free to field and free to "
                        f"stockpile (fielded by '{unit}' in {rel})",
                        MONEY_FILE,
                        acc_line,
                    )
                )
            elif not has_stockpile:
                partial.append(
                    (
                        f"'{archetype}' is charged for deployed units but not for "
                        "stockpile (missing the "
                        f"num_equipment@{archetype} term)",
                        MONEY_FILE,
                        acc_line,
                    )
                )
            elif not has_deployed:
                partial.append(
                    (
                        f"'{archetype}' is charged for stockpile but not for "
                        "deployed units (missing the "
                        f"num_equipment_in_armies@{archetype} term)",
                        MONEY_FILE,
                        acc_line,
                    )
                )

        self._report(
            uncosted,
            "Every land equipment archetype is charged maintenance",
            "Land equipment archetypes with no maintenance cost:",
            severity=Severity.ERROR,
            category="uncosted-land-equipment",
        )
        self._report(
            partial,
            "Every costed archetype charges both deployed and stockpiled units",
            "Equipment costed on only one of deployed/stockpile:",
            severity=Severity.ERROR,
            category="partial-equipment-cost",
        )

        stale = [
            (
                f"'{archetype}' is on UPKEEP_EXEMPT ({UPKEEP_EXEMPT[archetype]}) but "
                f"now has a {_ACCUMULATOR} entry — drop the exemption",
                MONEY_FILE,
                acc_line,
            )
            for archetype in sorted(UPKEEP_EXEMPT)
            if archetype in deployed or archetype in stockpiled
        ]
        self._report(
            stale,
            "Upkeep exemption list is current",
            "Stale upkeep exemptions:",
            severity=Severity.WARNING,
            category="stale-upkeep-exemption",
        )

    def run_validations(self):
        if self.staged_only and not self._collect_files(_TRIGGER_PATTERNS):
            self.log("  No staged equipment, unit or money-system files")
            return
        self.validate_land_equipment_upkeep()


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate land equipment maintenance coverage in Millennium Dawn mod",
    )
