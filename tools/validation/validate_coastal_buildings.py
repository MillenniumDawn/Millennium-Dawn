#!/usr/bin/env python3
"""Flag coastal provincial buildings placed in provinces that are not coastal.

A coastal provincial building has `only_costal = yes` (the engine's spelling)
and a `province_max` level cap in `common/buildings/`. It can only exist in a
province that `map/definition.csv` marks as coastal land. The game drops a
placement anywhere else and logs an error.

Placements checked:

  - province blocks inside a state history `buildings = { 1234 = { ... } }`;
  - `add_building_construction = { type = X province = 1234 }`, including the
    `province = { id = 1234 }` form.
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared_utils import blank_quoted_strings  # noqa: E402
from validator_common import (  # noqa: E402
    BaseValidator,
    run_validator_main,
    strip_comments,
)

BUILDINGS_GLOB = "common/buildings/*.txt"
DEFINITION_FILE = "map/definition.csv"
PLACEMENT_GLOBS = ["common/**/*.txt", "events/**/*.txt", "history/**/*.txt"]

_TOKEN_RE = re.compile(r"[^\s{}=]+|[{}=]")
_IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_PROVINCE_ID_RE = re.compile(r"\d+\Z")

# (building, province, line)
Placement = Tuple[str, int, int]


def _tokens(text: str) -> List[Tuple[str, int]]:
    clean = blank_quoted_strings(strip_comments(text))
    tokens = []
    line = 1
    last = 0
    for match in _TOKEN_RE.finditer(clean):
        line += clean.count("\n", last, match.start())
        last = match.start()
        tokens.append((match.group(), line))
    return tokens


def _blocks(tokens: List[Tuple[str, int]]):
    """Yield (path, key, value, line) for each `key = value` and each
    `key = {` opening, where path is the tuple of enclosing block keys and
    value is "{" for an opening."""
    path: List[str] = []
    index = 0
    while index < len(tokens):
        value = tokens[index][0]
        if value == "}":
            if path:
                path.pop()
            index += 1
            continue
        if (
            value not in ("{", "=")
            and index + 2 < len(tokens)
            and tokens[index + 1][0] == "="
        ):
            rhs = tokens[index + 2][0]
            yield tuple(path), value, rhs, tokens[index][1]
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
    for path, key, value, _line in _blocks(_tokens(text)):
        if len(path) < 2 or path[0] != "buildings":
            continue
        building = path[1]
        if len(path) == 2 and key == "only_costal" and value == "yes":
            coastal.add(building)
        elif key == "province_max" and path[2:] == ("level_cap",):
            provincial.add(building)
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


def province_placements(text: str) -> List[Placement]:
    """Every building placed in a fixed province id, coastal or not."""
    placements: List[Placement] = []
    construction_type: Optional[str] = None
    construction_provinces: List[Tuple[int, int]] = []
    construction_depth = -1

    def flush():
        if construction_type:
            for province, line in construction_provinces:
                placements.append((construction_type, province, line))

    for path, key, value, line in _blocks(_tokens(text)):
        if construction_depth >= 0 and (
            len(path) <= construction_depth
            or path[construction_depth] != "add_building_construction"
        ):
            flush()
            construction_type, construction_provinces = None, []
            construction_depth = -1

        if key == "add_building_construction" and value == "{":
            flush()
            construction_type, construction_provinces = None, []
            construction_depth = len(path)
            continue

        if construction_depth >= 0:
            inner = path[construction_depth + 1 :]
            if not inner and key == "type" and _IDENTIFIER_RE.match(value):
                construction_type = value
            elif not inner and key == "province" and _PROVINCE_ID_RE.match(value):
                construction_provinces.append((int(value), line))
            elif inner == ("province",) and key == "id":
                if _PROVINCE_ID_RE.match(value):
                    construction_provinces.append((int(value), line))
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


class Validator(BaseValidator):
    TITLE = "COASTAL BUILDING PLACEMENT"
    STAGED_EXTENSIONS = [".txt", ".csv"]

    def _reference_changed(self) -> bool:
        mod_root = Path(self.mod_path).resolve()
        for staged_path in self.staged_files or []:
            try:
                relative = Path(staged_path).resolve().relative_to(mod_root).as_posix()
            except ValueError:
                continue
            if relative == DEFINITION_FILE or relative.startswith("common/buildings/"):
                return True
        return False

    def run_validations(self):
        definition_path = os.path.join(self.mod_path, DEFINITION_FILE)
        try:
            with open(definition_path, "r", encoding="utf-8-sig") as handle:
                known, coastal_provinces = coastal_land_provinces(handle.read())
        except OSError:
            self.add_warning(
                "coastal-building-definition-missing",
                f"cannot check coastal building placement because "
                f"{DEFINITION_FILE} is missing",
                DEFINITION_FILE,
            )
            return

        building_defs = self.parse_files_cached(
            [BUILDINGS_GLOB],
            "coastal_building_defs",
            lambda text, _path: coastal_provincial_buildings(text),
            ignore_staged=True,
        )
        coastal_buildings: Set[str] = set().union(*building_defs.values())

        full_scan = self.staged_only and self._reference_changed()
        placements: Dict[str, List[Placement]] = self.parse_files_cached(
            PLACEMENT_GLOBS,
            "coastal_building_placements",
            lambda text, _path: province_placements(text),
            ignore_staged=full_scan,
        )

        findings = 0
        for path, entries in placements.items():
            rel_path = Path(path).relative_to(self.mod_path).as_posix()
            for building, province, line in entries:
                if building not in coastal_buildings:
                    continue
                if province in coastal_provinces:
                    continue
                findings += 1
                if province in known:
                    reason = f"which {DEFINITION_FILE} does not mark as coastal land"
                else:
                    reason = f"which is not in {DEFINITION_FILE}"
                self.add_warning(
                    "coastal-building-not-coastal",
                    f"coastal building '{building}' is placed in province "
                    f"{province}, {reason}",
                    rel_path,
                    line,
                )
        self.log(
            f"  Scanned {len(placements)} files | "
            f"{len(coastal_buildings)} coastal provincial buildings | "
            f"{findings} warnings"
        )


if __name__ == "__main__":
    run_validator_main(Validator, "Validate coastal building placement")
