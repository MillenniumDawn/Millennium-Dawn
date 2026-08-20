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

  - A bare building-count comparison in the enclosing `if = { limit = { ... } }`
    (the dominant idiom: `if = { limit = { fuel_silo > 0 } ... }`), including
    one nested inside an `any_core_state`/`any_owned_state`/`any_state`-style
    pre-selection trigger.
  - `non_damaged_building_level = { building = X ... }` or
    `any_province_building_level = { building = X ... }` (also accepts
    `has_building` / `num_of_buildings`, both unused today) anywhere in the
    limit, however deeply nested.
  - A sibling `modifier = { factor = 0  X < N }` zeroing a `random_list`
    bucket's weight when the building is absent.

This is WARNING-only: the mod carries a ~700-item backlog of unguarded sites
predating this check. Flip the crashing categories to ERROR once triaged.
"""

import os
import re
import sys
from typing import FrozenSet, List, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import disk_cache  # noqa: E402 — same-dir import after sys.path tweak above
from shared_utils import blank_quoted_strings, compute_line_offsets, line_for_offset
from validator_common import (  # noqa: E402
    BaseValidator,
    run_validator_main,
    strip_comments,
)

# Numeric names so `random_list` weight buckets (`50 = { ... }`) and state ids
# (`652 = { ... }`) parse as blocks.
_BLOCK_RE = re.compile(r"([A-Za-z_0-9@][A-Za-z0-9_.@]*(?::[A-Za-z0-9_]+)?)\s*=\s*\{")
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
# A has_dlc-style gate here would cover the whole enclosing object, but no
# building-guard idiom in the mod uses trigger/available/visible/allowed --
# building counts are always read in state/country scope, inside a `limit`.
_OBJECT_GATES = frozenset({"trigger", "available", "visible", "allowed"})
# Never contain effects; walking them would re-read a branch condition as a
# guarded effect, or double-count a gate already handled elsewhere.
_SKIP_BLOCKS = frozenset(
    {"limit", "ai_will_do", "search_filters", "prerequisite", "mutually_exclusive"}
)
_BRANCHES = frozenset({"if", "else_if", "else"})


def _match_brace(text: str, open_pos: int) -> int:
    """Return the index of the `}` closing the `{` at ``open_pos``, or -1."""
    depth = 0
    for i in range(open_pos, len(text)):
        char = text[i]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return i
    return -1


def _sanitize(text: str) -> str:
    """Strip comments and blank quoted strings, preserving line numbering.

    A `{` inside a `log = "..."` string, or a meta_effect template value like
    `DAM = "[?building_damage_by_missile]"`, would otherwise desync brace
    matching or false-match the bare-comparison guard regex.
    """
    return blank_quoted_strings(strip_comments(text))


def _child_blocks(text: str, start: int, end: int) -> List[Tuple[str, int, int, int]]:
    """Direct child blocks of a body as (name, name_start, body_start, body_end)."""
    blocks = []
    i = start
    while i < end:
        match = _BLOCK_RE.search(text, i, end)
        if not match:
            break
        close = _match_brace(text, match.end() - 1)
        if close < 0 or close > end:
            break
        blocks.append((match.group(1), match.start(), match.end(), close))
        i = close + 1
    return blocks


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


class Context:
    """Building types proven present at a point in the script."""

    __slots__ = ("present",)

    def __init__(self, present: FrozenSet[str] = frozenset()):
        self.present = present

    def apply(self, buildings: Set[str]) -> "Context":
        if not buildings:
            return self
        return Context(self.present | buildings)


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

    def walk(self, start: int, end: int, ctx: Context):
        blocks = _child_blocks(self.text, start, end)

        gate_buildings: Set[str] = set()
        for name, _, body_start, body_end in blocks:
            if name in _OBJECT_GATES:
                gate_buildings |= _extract_building_guards(
                    self.text[body_start:body_end]
                )
            elif name == "modifier":
                body = self.text[body_start:body_end]
                if _FACTOR_ZERO_RE.search(body):
                    gate_buildings |= _extract_building_guards(body)
        ctx = ctx.apply(gate_buildings)

        for name, _, body_start, body_end in blocks:
            if name in _SKIP_BLOCKS or name in _OBJECT_GATES or name == "modifier":
                continue
            category = _BUILDING_EFFECTS.get(name)
            if category is not None:
                self._check_effect(name, category, body_start, body_end, ctx)
                continue
            if name in _BRANCHES:
                branch_ctx = ctx
                if name != "else":
                    for sub, _, s_start, s_end in _child_blocks(
                        self.text, body_start, body_end
                    ):
                        if sub == "limit":
                            branch_ctx = ctx.apply(
                                _extract_building_guards(self.text[s_start:s_end])
                            )
                            break
                self.walk(body_start, body_end, branch_ctx)
                continue
            self.walk(body_start, body_end, ctx)


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
        mod_path, "building_guards_scan", filepath, raw, compute
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

        issues = sorted(row for rows in results for row in rows)
        for category, relative, line, message in issues:
            self.add_warning(category, message, relative, line)

        if issues:
            self.log(f"✗ {len(issues)} unguarded building effect(s):", "error")
            for _, relative, line, message in issues:
                self.log(f"  {relative}:{line} - {message}")
        else:
            self.log("✓ All damage_building/remove_building effects are guarded")

    def run_validations(self):
        self.validate_building_guards()


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate that damage_building/remove_building effects are guarded by a "
        "building-existence check",
    )
