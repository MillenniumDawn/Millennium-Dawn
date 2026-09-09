#!/usr/bin/env python3
"""Validate that `remove_dynamic_modifier` is guarded by a presence check.

Removing a dynamic modifier the scope is not carrying makes the engine log an
error and do nothing. MD calls the effect from focus rewards, on_actions and
repeatable decisions, so an unguarded call keeps writing to `error.log` for the
whole campaign (issue #3764).

The rule: the `modifier = <name>` a removal names must also be named by a
`has_dynamic_modifier` trigger inside an enclosing `limit`. Both live forms
count, because the modifier name is harvested from the whole `limit` subtree
regardless of nesting:

  - Same scope, the FRA/USA house style --
    `if = { limit = { has_dynamic_modifier = { modifier = X } }
    remove_dynamic_modifier = { modifier = X } }`.
  - Cross scope, where the `limit` re-enters the state the removal runs in --
    `limit = { 215 = { has_dynamic_modifier = { modifier = X } } }` guarding
    `215 = { remove_dynamic_modifier = { modifier = X } }`.

`has_dynamic_modifier`'s optional `scope =` is ignored: matching on the modifier
name alone can only under-report, which is the safe direction for a gate.

`trigger` / `available` / `visible` / `allowed` are not guards. `allowed` is
evaluated once at game start, and the other three sit on the enclosing decision
or event rather than on the scope the effect runs in. `effect_tooltip` subtrees
are skipped because they only preview effects and never execute. The skip list,
the sanitize step and the report shape are shared with
`validate_building_guards.py` through `guard_scan.py`.
"""

import os
import re
import sys
from typing import List, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import disk_cache  # noqa: E402 — same-dir import after sys.path tweak above
import guard_scan  # noqa: E402 — same-dir import after sys.path tweak above
from shared_utils import compute_line_offsets, line_for_offset
from validator_common import BaseValidator, _child_blocks, run_validator_main

_MODIFIER_RE = re.compile(r"\bmodifier\s*=\s*([A-Za-z_][A-Za-z0-9_]*)")

_REMOVE_EFFECT = "remove_dynamic_modifier"
_PRESENCE_TRIGGER = "has_dynamic_modifier"
_CATEGORY = "unguarded-remove-dynamic-modifier"


def _extract_modifier_guards(text: str) -> Set[str]:
    """Modifier names proven present by triggers anywhere in ``text``."""
    guarded: Set[str] = set()
    for name, _, body_start, body_end in _child_blocks(text, 0, len(text)):
        body = text[body_start:body_end]
        if name == _PRESENCE_TRIGGER:
            guarded.update(_MODIFIER_RE.findall(body))
        else:
            guarded.update(_extract_modifier_guards(body))
    return guarded


class Scanner:
    """Walks one file's script tree, tracking modifiers proven present."""

    def __init__(self, text: str):
        self.text = text
        self.offsets = compute_line_offsets(text)
        self.findings: List[Tuple[int, str]] = []

    def _check_removal(self, header_start: int, body_start: int, body_end: int, ctx):
        match = _MODIFIER_RE.search(self.text[body_start:body_end])
        if match is None or match.group(1) in ctx.present:
            return
        modifier = match.group(1)
        self.findings.append(
            (
                line_for_offset(self.offsets, header_start),
                f"{_REMOVE_EFFECT} = {{ modifier = {modifier} }} is not guarded by a "
                f"check that {modifier} is applied",
            )
        )

    def _guards_from_limit(self, start: int, end: int) -> Set[str]:
        for name, _, body_start, body_end in _child_blocks(self.text, start, end):
            if name == "limit":
                return _extract_modifier_guards(self.text[body_start:body_end])
        return set()

    def walk(self, start: int, end: int, ctx: guard_scan.Context):
        for name, header_start, body_start, body_end in _child_blocks(
            self.text, start, end
        ):
            if name in guard_scan.SKIP_BLOCKS:
                continue
            if name == _REMOVE_EFFECT:
                self._check_removal(header_start, body_start, body_end, ctx)
                continue
            self.walk(
                body_start,
                body_end,
                ctx.apply(self._guards_from_limit(body_start, body_end)),
            )


def scan_text(raw: str) -> List[Tuple[int, str]]:
    """Return (line, message) for every unguarded removal in ``raw``."""
    scanner = Scanner(guard_scan.sanitize(raw))
    scanner.walk(0, len(scanner.text), guard_scan.Context())
    return scanner.findings


def scan_file(args: Tuple[str, str]) -> List[Tuple[str, int, str]]:
    """Return (relative path, line, message) for one content file."""
    filepath, mod_path = args
    try:
        with open(filepath, encoding="utf-8-sig", errors="replace") as handle:
            raw = handle.read()
    except OSError:
        return []
    if _REMOVE_EFFECT not in raw:
        return []

    findings = disk_cache.per_file_cached_by_content(
        mod_path,
        "dynamic_modifier_guards_scan_v1",
        filepath,
        raw,
        lambda: scan_text(raw),
    )
    relative = os.path.relpath(filepath, mod_path).replace(os.sep, "/")
    return [(relative, line, message) for line, message in findings]


class Validator(BaseValidator):
    TITLE = "DYNAMIC MODIFIER GUARD VALIDATION"
    STAGED_EXTENSIONS = [".txt"]

    def validate_dynamic_modifier_guards(self):
        self._log_section("remove_dynamic_modifier presence guards")
        files = self._collect_files(["common/**/*.txt", "events/**/*.txt"])
        results = self._pool_map(scan_file, [(f, self.mod_path) for f in files])

        guard_scan.report_findings(
            self,
            sorted((_CATEGORY,) + row for rows in results for row in rows),
            self.add_error,
            "unguarded dynamic modifier removal(s)",
            "All remove_dynamic_modifier calls are guarded",
        )

    def run_validations(self):
        self.validate_dynamic_modifier_guards()


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate that remove_dynamic_modifier calls are guarded by a "
        "has_dynamic_modifier check",
    )
