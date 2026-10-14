"""Flag AI weight blocks where an `add` follows a `factor = 0` modifier.

`ai_chance` and `ai_will_do` apply their `modifier` blocks in order on a running
total, so a positive `add` after a `factor = 0` brings the zeroed weight back
(issue #5738). Triggers are not compared: two modifiers that can never both hold
are still reported.
"""

import os
import re
import sys
from typing import List, Optional, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import guard_scan  # noqa: E402 — same-dir import after sys.path tweak above
from shared_utils import (
    compute_line_offsets,
    find_unquoted_brace_close,
    line_for_offset,
)
from validator_common import (
    FACTOR_ZERO_RE,
    BaseValidator,
    Severity,
    _child_blocks,
    run_validator_main,
)

_AI_WEIGHT_RE = re.compile(r"\b(ai_chance|ai_will_do)\s*=\s*\{")
_ADD_RE = re.compile(r"\badd\s*=\s*(\d+(?:\.\d+)?)")
_CATEGORY = "ai-weight-zero-then-add"


def _own_text(text: str, start: int, end: int) -> str:
    """The body between ``start`` and ``end`` with nested blocks cut out."""
    parts = []
    cursor = start
    for _, name_start, _, body_end in _child_blocks(text, start, end):
        parts.append(text[cursor:name_start])
        cursor = body_end + 1
    parts.append(text[cursor:end])
    return " ".join(parts)


def _add_after_zero(text: str, start: int, end: int) -> Optional[int]:
    """Offset of the first positive-add modifier that follows a zeroing one."""
    zeroed = False
    for name, name_start, body_start, body_end in _child_blocks(text, start, end):
        if name != "modifier":
            continue
        own = _own_text(text, body_start, body_end)
        if zeroed and any(float(value) > 0 for value in _ADD_RE.findall(own)):
            return name_start
        if FACTOR_ZERO_RE.search(own):
            zeroed = True
    return None


def scan_text(raw: str) -> List[Tuple[int, str]]:
    """Return (line, message) for every AI weight block that adds after a zero."""
    text = guard_scan.sanitize(raw)
    offsets = compute_line_offsets(text)
    findings: List[Tuple[int, str]] = []
    for match in _AI_WEIGHT_RE.finditer(text):
        close = find_unquoted_brace_close(text, match.end() - 1)
        if close == -1:
            continue
        add_at = _add_after_zero(text, match.end(), close)
        if add_at is not None:
            findings.append(
                (
                    line_for_offset(offsets, add_at),
                    f"{match.group(1)} adds after a factor = 0 modifier, which "
                    "brings the zeroed weight back; move the factor = 0 "
                    "modifiers last",
                )
            )
    return findings


def scan_file(args: Tuple[str, str]) -> List[Tuple[str, int, str]]:
    """Return (relative path, line, message) for one content file."""
    return guard_scan.scan_file(args, "factor", "ai_weight_order_scan_v1", scan_text)


class Validator(BaseValidator):
    TITLE = "AI WEIGHT ORDER VALIDATION"
    STAGED_EXTENSIONS = [".txt"]

    def validate_ai_weight_order(self):
        self._log_section("factor = 0 modifiers followed by an add")
        rows = guard_scan.collect_findings(self, scan_file, _CATEGORY)
        self._report(
            [(message, relative, line) for _, relative, line, message in rows],
            "✓ No AI weight block adds after a factor = 0 modifier",
            "AI weight blocks adding after a factor = 0 modifier:",
            Severity.WARNING,
            category=_CATEGORY,
        )

    def run_validations(self):
        self.validate_ai_weight_order()


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate that factor = 0 modifiers come after the adds in AI weight blocks",
    )
