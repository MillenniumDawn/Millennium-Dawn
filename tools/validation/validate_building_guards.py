#!/usr/bin/env python3
"""Validate that `damage_building` / `remove_building` effects are guarded by a
check that the named building actually exists.

Calling either effect against a building the state/country doesn't have spams
`error.log` and, at the scale MD runs raids and random-list decisions,
degrades performance across the campaign (issue #2806).

The rule: the `type = <building>` an effect names must also be named by a
guard trigger that can only pass when that building is present, sitting
somewhere between the effect and the top of its enclosing script tree. The
mod's accepted guard idioms, all derived from live usage:

  - A bare building-count comparison in an enclosing `limit`. That is the
    `if = { limit = { fuel_silo > 0 } ... }` form every `common/raids/` site
    uses, and the same `limit` on a scoped iterator (`random_owned_state =
    { limit = { dockyard > 0 } ... }`, `every_owned_state`,
    `random_core_state`, `random_controlled_state`, ...). Nested
    `any_core_state`/`any_owned_state` pre-selection inside an `if` limit
    also counts.
  - `non_damaged_building_level = { building = X ... }` or
    `any_province_building_level = { building = X ... }` (also accepts
    `has_building` / `num_of_buildings`, both unused today) anywhere in the
    limit, however deeply nested.
  - A sibling `modifier = { factor = 0  X < N }` zeroing a `random_list`
    bucket's weight when the building is absent.

`trigger` / `available` / `visible` / `allowed` are not guards: a
country-level `any_owned_state = { arms_factory > 0 }` does not prove the
state the effect runs on has that building. `effect_tooltip` subtrees are
skipped because they only preview effects and never execute.

This is WARNING-only while the rule remains in rollout.
"""

import os
import re
import sys
from typing import List, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import disk_cache  # noqa: E402 — same-dir import after sys.path tweak above
from guard_scan import SKIP_BLOCKS as _SKIP_BLOCKS  # noqa: E402
from guard_scan import Context, report_findings  # noqa: E402
from guard_scan import sanitize as _sanitize  # noqa: E402
from shared_utils import compute_line_offsets, line_for_offset
from validator_common import BaseValidator, _child_blocks, run_validator_main

_TYPE_RE = re.compile(r"\btype\s*=\s*([A-Za-z_][A-Za-z0-9_]*)")
_BARE_GUARD_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*(?:>=|<=|==|!=|>|<)\s*-?\d")
_BUILDING_FIELD_RE = re.compile(r"\b(?:building|type)\s*=\s*([A-Za-z_][A-Za-z0-9_]*)")
_FACTOR_ZERO_RE = re.compile(r"\bfactor\s*=\s*0(?:\.0+)?\b")

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


def _extract_building_guards(text: str) -> Set[str]:
    """Building type names proven present by triggers anywhere in ``text``.

    Combines the bare-comparison idiom (`fuel_silo > 0`, matched regardless of
    nesting depth -- an `any_core_state = { arms_factory > 1 }` pre-selection
    reads the same as a flat one) with the field-based triggers, whose value
    only appears as `building = X` / `type = X` inside a named child block.
    """
    buildings = {m.group(1) for m in _BARE_GUARD_RE.finditer(text)}
    for name, _, body_start, body_end in _child_blocks(text, 0, len(text)):
        if name in _NAMED_BUILDING_TRIGGERS:
            body = text[body_start:body_end]
            buildings.update(_BUILDING_FIELD_RE.findall(body))
        else:
            buildings.update(_extract_building_guards(text[body_start:body_end]))
    return buildings


class Scanner:
    """Walks one file's script tree, tracking buildings proven present."""

    def __init__(self, text: str):
        self.text = text
        self.offsets = compute_line_offsets(text)
        self.findings: List[Tuple[str, int, str]] = []

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
                if _FACTOR_ZERO_RE.search(body):
                    gate_buildings |= _extract_building_guards(body)
        ctx = ctx.apply(gate_buildings)

        for name, _, body_start, body_end in blocks:
            if name in _SKIP_BLOCKS or name == "modifier":
                continue
            category = _BUILDING_EFFECTS.get(name)
            if category is not None:
                self._check_effect(name, category, body_start, body_end, ctx)
                continue
            self.walk(
                body_start,
                body_end,
                ctx.apply(self._buildings_from_limit(body_start, body_end)),
            )


def scan_file(args: Tuple[str, str]) -> List[Tuple[str, str, int, str]]:
    """Return (category, relative path, line, message) for one content file."""
    filepath, mod_path = args
    try:
        with open(filepath, encoding="utf-8-sig", errors="replace") as handle:
            raw = handle.read()
    except OSError:
        return []
    if "damage_building" not in raw and "remove_building" not in raw:
        return []

    def compute():
        scanner = Scanner(_sanitize(raw))
        scanner.walk(0, len(scanner.text), Context())
        return scanner.findings

    findings = disk_cache.per_file_cached_by_content(
        mod_path, "building_guards_scan_v3", filepath, raw, compute
    )
    relative = os.path.relpath(filepath, mod_path).replace(os.sep, "/")
    return [(category, relative, line, message) for category, line, message in findings]


class Validator(BaseValidator):
    TITLE = "BUILDING GUARD VALIDATION"
    STAGED_EXTENSIONS = [".txt"]

    def validate_building_guards(self):
        self._log_section("damage_building / remove_building existence guards")
        files = self._collect_files(["common/**/*.txt", "events/**/*.txt"])
        results = self._pool_map(scan_file, [(f, self.mod_path) for f in files])

        report_findings(
            self,
            sorted(row for rows in results for row in rows),
            self.add_warning,
            "unguarded building effect(s)",
            "All damage_building/remove_building effects are guarded",
        )

    def run_validations(self):
        self.validate_building_guards()


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate that damage_building/remove_building effects are guarded by a "
        "building-existence check",
    )
