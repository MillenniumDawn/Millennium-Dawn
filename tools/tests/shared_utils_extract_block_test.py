"""Unit tests for shared_utils.extract_block brace-balancing."""

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO_ROOT, "tools"))

from shared_utils import extract_block  # noqa: E402


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
