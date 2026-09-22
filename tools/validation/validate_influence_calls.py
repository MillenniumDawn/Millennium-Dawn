"""Validate that `change_influence_percentage` loop calls retarget per iteration.

`change_influence_percentage` defaults its `tag_index` / `influence_target`
parameters only when they are 0 (unset, `00_influence_scripted_effects.txt`).
Temp variables persist across `every_*` / `for_each_loop` iterations within one
effect execution, so a loop call that never sets `influence_target` locks onto
the first iterated country: iteration one defaults it, and every later pass
reuses the stale value. Issue #4592: Spain's `SPR_hispanidad` focus stacked ~20
passes of +2 influence onto Mexico instead of granting +2 to each Spanish-speaking
country.

The fix at the call site is the house style China's SCO focus already uses
(`05_china.txt`): `set_temp_variable = { influence_target = THIS }` inside the
loop before the call. The check asks for exactly that: between a multi-iteration
scope's opening and the call, some `set_temp_variable = { influence_target ... }`
must run. A set before the loop does not count — it is the stale value every
later iteration reuses. A set inside a conditional block before the call is not
accepted, because the call can still run on a pass where the condition skipped
the set.

Single-execution scopes are deliberately out of scope: a call under
`random_country` / `random_list` / `TAG = { }` runs once per invocation, so the
0-default works and a call there leaning on an earlier call's values is a
separate (latent) contract question, not this bug class. `meta_effect` /
`meta_trigger` template bodies are skipped because their text is generated at
runtime, not executed as written.

WARNING-severity until the backlog lands; #4675 sweeps the remaining sites and
flips the check to ERROR in the same change.
"""

import os
import re
import sys
from typing import List, Tuple

sys.path.insert(0, os.path.dirname(__file__))
import guard_scan  # noqa: E402 — same-dir import after sys.path tweak above
from shared_utils import compute_line_offsets, line_for_offset
from validator_common import BaseValidator, _child_blocks, run_validator_main

_CATEGORY = "stale-influence-target"
_CALL_RE = re.compile(r"\bchange_influence_percentage\s*=\s*yes\b")
_SET_TARGET_RE = re.compile(
    r"(?:^\s*influence_target\s*=|\bvar\s*=\s*influence_target\b)"
)
# every_* selectors plus the array/counter loop effects. `for_countries` is an
# ai_strategy block key, not an effect, and random_* selectors execute once.
_LOOP_RE = re.compile(
    r"^(every_[a-z_]+|for_each_[a-z_]+|for_loop_[a-z_]+|while_loop_[a-z_]+)$"
)

# Never contains a runtime call of its own.
_SKIP_BLOCKS = guard_scan.SKIP_BLOCKS | {"meta_effect", "meta_trigger"}


def _is_multi_iteration(name: str) -> bool:
    return bool(_LOOP_RE.match(name))


class Scanner:
    """Walks one file's script tree tracking open multi-iteration scopes."""

    def __init__(self, text: str):
        self.text = text
        self.offsets = compute_line_offsets(text)
        self.findings: List[Tuple[int, str]] = []

    def _own_call_lines(self, start: int, end: int, children) -> List[int]:
        """Line of every call statement not inside a nested child block."""
        lines = []
        for match in _CALL_RE.finditer(self.text, start, end):
            if any(bs <= match.start() < be for _, _, bs, be in children):
                continue
            lines.append(line_for_offset(self.offsets, match.start()))
        return lines

    def walk(self, start: int, end: int, loops: List[Tuple[str, bool]]):
        """`loops` carries (name, target-set-seen) for enclosing loop scopes."""
        children = _child_blocks(self.text, start, end)
        cursor = start
        for name, name_start, body_start, body_end in children:
            for line in self._own_call_lines(cursor, name_start, children):
                self._report(line, loops)
            if name in _SKIP_BLOCKS:
                pass
            elif _is_multi_iteration(name):
                self.walk(body_start, body_end, loops + [(name, False)])
            else:
                if name == "set_temp_variable" and _SET_TARGET_RE.search(
                    self.text[body_start:body_end]
                ):
                    loops = [(loop, True) for loop, _ in loops]
                self.walk(body_start, body_end, loops)
            cursor = body_end + 1
        for line in self._own_call_lines(cursor, end, children):
            self._report(line, loops)

    def _report(self, line: int, loops: List[Tuple[str, bool]]):
        missing = next((name for name, covered in loops if not covered), None)
        if missing is None:
            return
        self.findings.append(
            (
                line,
                f"change_influence_percentage = yes runs inside {missing} without a "
                f"per-iteration influence_target; temp variables persist across "
                f"iterations, so every pass after the first re-targets the first "
                f"iterated country",
            )
        )


def scan_text(raw: str) -> List[Tuple[int, str]]:
    """Return (line, message) for every stale-target loop call in ``raw``."""
    scanner = Scanner(guard_scan.sanitize(raw))
    scanner.walk(0, len(scanner.text), [])
    return scanner.findings


def scan_file(args: Tuple[str, str]) -> List[Tuple[str, int, str]]:
    """Return (relative path, line, message) for one content file."""
    return guard_scan.scan_file(
        args, "change_influence_percentage", "influence_calls_scan_v2", scan_text
    )


class Validator(BaseValidator):
    TITLE = "INFLUENCE CALL VALIDATION"
    STAGED_EXTENSIONS = [".txt"]

    def validate_influence_calls(self):
        self._log_section("change_influence_percentage loop retargeting")
        guard_scan.report_findings(
            self,
            guard_scan.collect_findings(self, scan_file, _CATEGORY),
            self.add_warning,
            "loop influence call(s) without a per-iteration influence_target",
            "All change_influence_percentage loop calls retarget per iteration",
        )

    def run_validations(self):
        self.validate_influence_calls()


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate that change_influence_percentage calls inside every_*/for_* loops "
        "set influence_target per iteration",
    )
