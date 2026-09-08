"""Validate achievement definitions in Millennium Dawn.

The `possible` block is evaluated once at game start and stored in the save,
so it is effectively an `allowed` gate on which country may earn the
achievement. A country's `original_tag` never changes after campaign start
(country-tag aliases map a released nation back to its start-of-game tag), so
re-checking the same `original_tag = TAG` in `happened` is redundant, the tag
can only match the tags `possible` already admitted. This validator flags that
duplicate so `happened` only states the in-game condition actually being earned.
"""

import os
import re
import sys
from typing import List, Optional, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared_utils import FileOpener
from validator_common import (
    BaseValidator,
    Issue,
    Severity,
    _child_blocks,
    run_validator_main,
)

_VALIDATE_PATTERNS = ["common/achievements/**/*.txt"]

_ORIGINAL_TAG_RE = re.compile(r"\boriginal_tag\s*=\s*([A-Za-z0-9_]+)\b")


def _find_block(
    text: str, body_start: int, body_end: int, name: str
) -> Optional[Tuple[int, int]]:
    """Char span of the `name = { ... }` block directly inside body_start:end."""
    for child, _, c_start, c_end in _child_blocks(text, body_start, body_end):
        if child == name:
            return (c_start, c_end)
    return None


def _scan_file(
    args,
) -> List[Tuple[str, int, str]]:
    """Worker: every `original_tag` inside `possible` and `happened` of one file.

    Returns (rel, line, tag) pairs for occurrences in `happened` whose tag also
    appears in that achievement's `possible` block.
    """
    filepath, mod_path = args
    try:
        text = FileOpener.open_text_file(
            filepath, strip_comments_flag=True, lowercase=False
        )
    except (OSError, UnicodeDecodeError):
        return []
    if "original_tag" not in text:
        return []
    rel = os.path.relpath(filepath, mod_path).replace(os.sep, "/")

    findings: List[Tuple[str, int, str]] = []
    # Top-level blocks are achievement definitions (plus the scalar
    # `unique_id = ...` header line, which has no `{`).
    for _, name_start, body_start, body_end in _child_blocks(text, 0, len(text)):
        possible = _find_block(text, body_start, body_end, "possible")
        happened = _find_block(text, body_start, body_end, "happened")
        if possible is None or happened is None:
            continue
        p_start, p_end = possible
        h_start, h_end = happened
        possible_tags = {
            m.group(1) for m in _ORIGINAL_TAG_RE.finditer(text, p_start, p_end)
        }
        if not possible_tags:
            continue
        for m in _ORIGINAL_TAG_RE.finditer(text, h_start, h_end):
            if m.group(1) in possible_tags:
                line = text.count("\n", 0, m.start()) + 1
                findings.append((rel, line, m.group(1)))
    return findings


class Validator(BaseValidator):
    TITLE = "ACHIEVEMENT VALIDATION"

    def validate_achievements(self):
        self._log_section("Checking achievement original_tag gates...")

        files = self._collect_files(_VALIDATE_PATTERNS)
        self.log(f"  Checking {len(files)} file...")
        batches = self._pool_map(_scan_file, [(f, self.mod_path) for f in files])

        results: List[Issue] = []
        for batch in batches:
            for rel, line, tag in batch:
                results.append(
                    Issue(
                        severity=Severity.ERROR,
                        category="achievement-original-tag-redundant",
                        message=(
                            f"original_tag = {tag} is redundant in `happened`: the"
                            " same tag already gates `possible`, which is evaluated"
                            " once and stored in the save. Remove it so `happened`"
                            " states only the in-game condition earned."
                        ),
                        file=rel,
                        line=line,
                    )
                )

        self._report(
            results,
            "All achievement happened blocks avoid re-checking the possible gate",
            "Achievements that re-check their possible original_tag gate in happened:",
            severity=Severity.ERROR,
            category="achievement-original-tag-redundant",
        )

    def run_validations(self):
        self.validate_achievements()


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate achievement definitions in Millennium Dawn mod",
    )
