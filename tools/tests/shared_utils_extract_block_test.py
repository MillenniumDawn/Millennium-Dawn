"""Unit tests for shared_utils.extract_block brace-balancing."""

import random

import pytest
from shared_utils import blank_quoted_strings, extract_block, find_matching_brace


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


def test_blank_quoted_strings_escaped_quote_does_not_end_the_string():
    raw = 'log = "a \\"b\\" c { d } e"\nafter = { yes }\n'
    out = blank_quoted_strings(raw)
    assert out.count("{") == 1
    assert out.count("}") == 1
    assert 'log = "' in out
    assert out.endswith("after = { yes }\n")


def test_blank_quoted_strings_keep_start_preserves_one_string():
    raw = 'has_dlc = "By Blood Alone" log = "hide me"\n'
    keep_at = raw.index('"By Blood Alone"')
    out = blank_quoted_strings(raw, {keep_at})
    assert 'has_dlc = "By Blood Alone"' in out
    assert "hide me" not in out
    assert 'log = "' in out


# --- the bulk scanners against the per-character loops they replaced --------


def _reference_blank_quoted_strings(text, keep_start=None):
    if '"' not in text:
        return text
    out = list(text)
    in_str = False
    start = -1
    keep = keep_start or ()
    for i, c in enumerate(text):
        if c == '"' and (i == 0 or text[i - 1] != "\\"):
            if not in_str:
                start = i
            in_str = not in_str
        elif in_str and c != "\n" and start not in keep:
            out[i] = " "
    return "".join(out)


def _reference_find_matching_brace(text, open_idx):
    # Every character from open_idx, negative offsets included.
    level, quoted, pos = 0, False, open_idx
    while pos < len(text):
        char = text[pos]
        toggles = char == '"' and text[pos - 1] != "\\"
        quoted ^= toggles
        if not quoted and not toggles and char in "{}":
            level += 1 if char == "{" else -1
            if char == "}" and level == 0:
                return pos
        pos += 1
    return -1


_SCANNER_CASES = {
    "brace in a string": 'a = { log = "x } y {" b = 1 }\n',
    "hash in a string": 'a = { log = "#1 } done" }\n',
    "comment with braces": "a = { b = 1 } # c = { d }\n}\n",
    "unbalanced": "a = { b = { c = 1 }\n",
    "three deep": "a = {\n\tb = {\n\t\tc = { d = 1 }\n\t}\n}\n",
    "first and last line": '{ "x" }\nmid\n{ "y" }',
    "empty": "",
    "no trailing newline": 'a = { log = "q" }',
    "crlf": 'a = {\r\n\tlog = "x\r\ny"\r\n}\r\n',
    "escaped quote": 'log = "a \\"b\\" { c"\nd = { }\n',
    "backslash run before a quote": 'log = "a\\\\" b = { "c\\\\\\"" }\n',
    "unterminated string": 'a = { log = "never closed }\n',
    "adjacent strings": 'a = { "one""two" "" }\n',
    "quote first": '"{" = { x }',
}


@pytest.mark.parametrize("text", _SCANNER_CASES.values(), ids=_SCANNER_CASES.keys())
def test_blank_quoted_strings_matches_the_reference_loop(text):
    quotes = [i for i, c in enumerate(text) if c == '"']
    for keep in [None, set(quotes)] + [{q} for q in quotes]:
        assert blank_quoted_strings(text, keep) == _reference_blank_quoted_strings(
            text, keep
        )


def _brace_outcome(find, text, open_idx):
    # A quote at text[-len] makes both versions index before the text.
    try:
        return find(text, open_idx)
    except IndexError:
        return "IndexError"


def _same_brace_outcome(text, open_idx):
    return _brace_outcome(find_matching_brace, text, open_idx) == _brace_outcome(
        _reference_find_matching_brace, text, open_idx
    )


@pytest.mark.parametrize("text", _SCANNER_CASES.values(), ids=_SCANNER_CASES.keys())
def test_find_matching_brace_matches_the_reference_loop(text):
    # Negative offsets walk the tail first, as indexing from the end does.
    for open_idx in range(-len(text) - 1, len(text) + 2):
        assert _same_brace_outcome(text, open_idx), open_idx


def test_text_scanners_match_their_reference_loops_on_random_input():
    rng = random.Random(20261002)
    alphabet = ['"', "\\", "{", "}", "#", "a", " ", "\n", "\r"]
    for _ in range(3000):
        text = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 20)))
        keep = {i for i, c in enumerate(text) if c == '"' and rng.random() < 0.5}
        assert blank_quoted_strings(text, keep) == _reference_blank_quoted_strings(
            text, keep
        ), repr(text)
        open_idx = rng.randint(-len(text) - 1, len(text) + 1)
        assert _same_brace_outcome(text, open_idx), (text, open_idx)
