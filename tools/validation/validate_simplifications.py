#!/usr/bin/env python3
"""Suggest simplifications where inline script duplicates a shared trigger.

Currently focuses on random-construction build-location limits. Many focuses,
decisions, and scripted effects open a `random_owned_controlled_state` (or
`every_controlled_state` / `random_controlled_state` / `random_owned_state`)
and inline the same ~20-line "is there a free building slot in a home-area
state" limit that now lives as a shared scripted trigger in
`common/scripted_triggers/00_scripted_triggers.txt`:

  - `free_shared_building_slots`        any pooled shared-slot building
  - `<building>_random_build_loc`       the non-pooled buildings

When a block's `limit` is a byte-for-byte (token) match of one of those
triggers, this validator flags it as a WARNING suggesting the one-line
replacement. It is intentionally conservative: a different slot threshold
(`size > 1`), a missing/extra `include_locked`, or any extra condition will
NOT match, so it never suggests a behaviour-changing rewrite.

It also flags the invalid effect `every_owned_controlled_state` (it does not
exist in the engine; the valid effect is `every_controlled_state`), which is
the exact mistake the shared helpers were rewritten to avoid.
"""
import os
import re

from validator_common import (
    BaseValidator,
    Severity,
    run_validator_main,
)

# Pooled shared-slot buildings: every shares_slots=yes building (00_buildings.txt)
# whose random-build limit carries no extra condition. They all draw from the
# same pooled state slots, so the single free_shared_building_slots trigger
# (which checks industrial_complex with include_locked=yes) covers them.
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

# building -> (trigger, include_locked, coastal). The flags must mirror exactly
# what the trigger in 00_scripted_triggers.txt encodes; a candidate limit that
# differs on either flag is not equivalent and is left alone.
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
    """Yield (line_1based, building, trigger) for each replaceable limit and
    ("__invalid_effect__", line_1based) for every_owned_controlled_state use."""
    lines = text.split("\n")
    suggestions = []
    invalid = []
    for i, line in enumerate(lines):
        if "every_owned_controlled_state" in line and not line.lstrip().startswith("#"):
            invalid.append(i + 1)
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
    return suggestions, invalid


class Validator(BaseValidator):
    TITLE = "SIMPLIFICATION SUGGESTIONS"
    STAGED_EXTENSIONS = [".txt"]

    def run_validations(self):
        files = self._collect_files(_SCAN_PATTERNS)
        self.log(f"Scanning {len(files)} files for simplification opportunities")

        dedup_results = []
        invalid_results = []
        for path in files:
            try:
                with open(path, encoding="utf-8") as f:
                    text = f.read()
            except (OSError, UnicodeDecodeError):
                continue
            if (
                "any_owned_state" not in text
                and "every_owned_controlled_state" not in text
            ):
                continue
            rel = os.path.relpath(path, self.mod_path)
            suggestions, invalid = _scan_text(text)
            for line, building, trigger in suggestions:
                dedup_results.append(
                    (
                        f"inline build-location limit for '{building}' can be replaced "
                        f"with `limit = {{ {trigger} = yes }}`",
                        rel,
                        line,
                    )
                )
            for line in invalid:
                invalid_results.append(
                    (
                        "every_owned_controlled_state is not a real effect; "
                        "use every_controlled_state",
                        rel,
                        line,
                    )
                )

        self._report(
            invalid_results,
            "No invalid every_owned_controlled_state usage found",
            "Invalid effect (does not exist in engine):",
            severity=Severity.WARNING,
            category="invalid-effect",
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
