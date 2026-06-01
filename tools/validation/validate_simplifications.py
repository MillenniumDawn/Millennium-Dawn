#!/usr/bin/env python3
"""Suggest replacing inline random-build limits with the shared triggers.

When a random_owned_controlled_state (or every/random_controlled_state,
random_owned_state) block's limit is a token-exact match of a build-location
trigger in common/scripted_triggers/00_scripted_triggers.txt, flag it (WARNING)
with the one-line replacement. The match is exact on purpose: a different
size threshold, a missing or extra include_locked, or any added condition will
not match, so it never suggests a behaviour-changing rewrite.
"""
import os
import re

from validator_common import (
    BaseValidator,
    Severity,
    run_validator_main,
)

# Every shares_slots=yes building draws from the same pooled state slots, so one
# free_shared_building_slots check covers them all.
_SHARED_TRIGGER = "free_shared_building_slots"
_SHARED_BUILDINGS = frozenset(
    {
        "industrial_complex",
        "arms_factory",
        "offices",
        "synthetic_refinery",
        "microchip_plant",
        "energy_infrastructure",
        "industrial_infrastructure",
        "composite_plant",
        "agriculture_district",
    }
)

# building -> (trigger, include_locked, coastal). The flags must match what the
# trigger encodes, or the inline limit isn't equivalent and is left alone.
_BUILDING_TRIGGER = {
    "dockyard": ("dockyard_random_build_loc", True, True),
    "infrastructure": ("infrastructure_random_build_loc", False, False),
    "nuclear_reactor": ("nuclear_reactor_random_build_loc", False, False),
    "renewable_energy_infra": ("renewable_energy_infra_random_build_loc", False, False),
    "air_base": ("air_base_random_build_loc", False, False),
    "radar_station": ("radar_station_random_build_loc", False, False),
    "anti_air_building": ("anti_air_random_build_loc", False, False),
    "internet_station": ("network_infrastructure_random_build_loc", False, False),
    "fuel_silo": ("fuel_reserve_random_build_loc", False, False),
    "fossil_powerplant": ("fossil_powerplant_random_build_loc", False, False),
}
for _b in _SHARED_BUILDINGS:
    _BUILDING_TRIGGER[_b] = (_SHARED_TRIGGER, True, False)

_SCOPE_KEYWORDS = (
    "random_owned_controlled_state",
    "every_controlled_state",
    "random_controlled_state",
    "random_owned_state",
)

_SCAN_PATTERNS = [
    "common/national_focus/*.txt",
    "common/national_focus/**/*.txt",
    "common/decisions/*.txt",
    "common/decisions/**/*.txt",
    "common/scripted_effects/*.txt",
    "events/*.txt",
]


def _tokens(s: str) -> list:
    return s.replace("{", " { ").replace("}", " } ").replace(">", " > ").split()


def _canon_limit(building: str, include_locked: bool, coastal: bool) -> list:
    """Token list for the inline limit that a trigger exactly replaces."""
    il = "include_locked = yes" if include_locked else ""
    slot = f"free_building_slots = {{ building = {building} size > 0 {il} }}"
    coastal_top = "is_coastal = yes" if coastal else ""
    coastal_fallback = "is_coastal = yes" if coastal else ""
    return _tokens(
        f"limit = {{ {coastal_top} {slot} OR = {{ is_in_home_area = yes "
        f"NOT = {{ owner = {{ any_owned_state = {{ {slot} {coastal_fallback} "
        f"is_in_home_area = yes }} }} }} }} }}"
    )


def _match_brace_block(lines: list, start: int) -> int:
    depth = 0
    for j in range(start, len(lines)):
        depth += lines[j].count("{") - lines[j].count("}")
        if depth == 0 and j > start:
            return j
    return len(lines) - 1


def _find_limit(lines: list, start: int, end: int):
    for k in range(start, end + 1):
        if lines[k].strip().startswith("limit = {"):
            return k, _match_brace_block(lines, k)
    return None


_SCOPE_RE = re.compile(r"^\s*(%s) = \{" % "|".join(_SCOPE_KEYWORDS))
_BUILDING_RE = re.compile(r"building = (\w+)")


def _scan_text(text: str):
    """Return a list of (line, building, trigger) for each replaceable limit."""
    lines = text.split("\n")
    suggestions = []
    for i, line in enumerate(lines):
        m = _SCOPE_RE.match(line)
        if not m:
            continue
        end = _match_brace_block(lines, i)
        block = "\n".join(lines[i : end + 1])
        if "any_owned_state" not in block or "is_in_home_area" not in block:
            continue
        lim = _find_limit(lines, i, end)
        if not lim:
            continue
        lk, le = lim
        bm = _BUILDING_RE.search(block)
        if not bm:
            continue
        building = bm.group(1)
        spec = _BUILDING_TRIGGER.get(building)
        if not spec:
            continue
        trigger, il, coastal = spec
        if _tokens("\n".join(lines[lk : le + 1])) == _canon_limit(
            building, il, coastal
        ):
            suggestions.append((lk + 1, building, trigger))
    return suggestions


class Validator(BaseValidator):
    TITLE = "SIMPLIFICATION SUGGESTIONS"
    STAGED_EXTENSIONS = [".txt"]

    def run_validations(self):
        files = self._collect_files(_SCAN_PATTERNS)
        self.log(f"Scanning {len(files)} files for simplification opportunities")

        dedup_results = []
        for path in files:
            try:
                with open(path, encoding="utf-8") as f:
                    text = f.read()
            except (OSError, UnicodeDecodeError):
                continue
            if "any_owned_state" not in text:
                continue
            rel = os.path.relpath(path, self.mod_path)
            for line, building, trigger in _scan_text(text):
                dedup_results.append(
                    (
                        f"inline build-location limit for '{building}' can be replaced "
                        f"with `limit = {{ {trigger} = yes }}`",
                        rel,
                        line,
                    )
                )

        self._report(
            dedup_results,
            "No duplicated build-location limits found",
            "Inline build-location limits that can use a shared trigger:",
            severity=Severity.WARNING,
            category="simplification",
        )


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Suggest simplifications using shared triggers in Millennium Dawn mod",
    )
