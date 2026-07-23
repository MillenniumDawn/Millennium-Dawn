"""Unit tests for shared_utils.extract_block brace-balancing."""

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))

from shared_utils import blank_quoted_strings, extract_block  # noqa: E402


def _split(text):
    return text.splitlines(keepends=True)


def test_same_line_brace():
    lines = _split("focus = { id = a }\nnext = yes\n")
    block, end = extract_block(lines, 0)
    assert block == [lines[0]]
    assert end == 1


def test_next_line_brace():
    # The `{` opens on a later line than the name — the regression case.
    lines = _split("focus =\n{\n\tid = a\n}\nnext = yes\n")
    block, end = extract_block(lines, 0)
    assert block == lines[0:4]
    assert end == 4


def test_nested_block():
    lines = _split("a = {\n\tb = {\n\t\tc = 1\n\t}\n}\ntrailing\n")
    block, end = extract_block(lines, 0)
    assert block == lines[0:5]
    assert end == 5


def test_unclosed_block_runs_to_eof():
    lines = _split("a = {\n\tb = 1\n\tc = 2\n")
    block, end = extract_block(lines, 0)
    assert block == lines
    assert end == len(lines)


def test_brace_inside_comment_ignored():
    lines = _split("a = { # stray } brace\n\tb = 1\n}\nafter\n")
    block, end = extract_block(lines, 0)
    assert block == lines[0:3]
    assert end == 3


def test_leading_stray_brace_advances_index():
    # A stray `}` before any `{` must return an advancing index (not the start
    # index) so a caller looping on it can't spin forever.
    lines = _split("}\nfocus = { id = a }\n")
    block, end = extract_block(lines, 0)
    assert block == []
    assert end > 0


def test_driver_loop_over_stray_brace_terminates():
    # Mirrors the standardizer driver loop: `i = next_i` unconditionally. A
    # non-advancing return (next_i == i) would hang here.
    lines = _split("}\na = {\n\tb = 1\n}\ntrailing\n")
    seen = []
    i = 0
    guard = 0
    while i < len(lines):
        guard += 1
        assert guard <= len(lines) + 5, "extract_block driver loop did not terminate"
        if "{" in lines[i] or "}" in lines[i]:
            block, next_i = extract_block(lines, i)
            assert next_i > i
            if block:
                seen.append(block)
            i = next_i
        else:
            seen.append([lines[i]])
            i += 1
    # The real block is still recovered after skipping the stray brace.
    assert lines[1:4] in seen


def test_over_closing_line_keeps_block():
    # `} }` overshoots the depth negative after the block opened. The whole
    # block (including the over-closing line) must be returned, never dropped —
    # a standardizer driver appends only truthy blocks, so a lost block deletes
    # those source lines from the rewritten file.
    lines = _split("focus = {\n\tid = a\n} }\nnext = yes\n")
    block, end = extract_block(lines, 0)
    assert block == lines[0:3]
    assert end == 3


def test_nested_over_closing_line_keeps_block():
    # A nested block whose final line over-closes (`} } }` at depth 2 drives
    # depth to -1). The accumulated lines must still come back with that line
    # as the closer instead of being discarded.
    lines = _split("a = {\n\tb = {\n\t} } }\nafter\n")
    block, end = extract_block(lines, 0)
    assert block == lines[0:3]
    assert end == 3


def test_over_closing_driver_loses_no_lines():
    # Reconstruct the file through the standardizer driver loop and assert every
    # input line is preserved (no silent data loss on an over-closing block).
    lines = _split("focus = {\n\tid = a\n} }\nnext = yes\n")
    out = []
    i = 0
    while i < len(lines):
        if "{" in lines[i] or "}" in lines[i]:
            block, next_i = extract_block(lines, i)
            assert next_i > i
            out.extend(block)
            i = next_i
        else:
            out.append(lines[i])
            i += 1
    assert out == lines


def test_quoted_string_brace_does_not_break_boundary():
    # A `{` / `}` inside a quoted string (blanked via blank_quoted_strings, as
    # the standardizers pass their input) must not shift the block boundary.
    raw = 'a = {\n\tlog = "brace } and { inside"\n\tb = 1\n}\nafter\n'
    lines = _split(blank_quoted_strings(raw))
    block, end = extract_block(lines, 0)
    assert len(block) == 4
    assert end == 4
