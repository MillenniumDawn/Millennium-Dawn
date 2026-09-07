"""Tests for the brace helpers both gate sweeps are built on.

`strip_idea_allowed_gates.py` and `strip_dynmod_tag_gates.py` both slice around
a block by column and both track their nesting with the same stack, so a
regression here silently corrupts whichever file the next sweep touches.
"""

from common_utils import (
    apply_brace_stack,
    code_of_line,
    collapse_blank_gap,
    find_block_span,
)


def test_span_stops_at_the_first_closer_on_a_shared_line():
    # `} }` is the whole reason this returns a column: a depth counter that
    # stops at "reached zero" cannot tell the two apart.
    lines = ["\tallowed = { original_tag = FOO } }"]
    assert find_block_span(lines, 0, 11) == (0, 32)


def test_span_crosses_lines():
    lines = ["\tallowed = {", "\t\tOR = { a = b }", "\t}", "\tpicture = x"]
    assert find_block_span(lines, 0, 11) == (2, 1)


def test_span_ignores_a_brace_in_a_comment():
    lines = ["\tallowed = { # }", "\t\ta = b", "\t}"]
    assert find_block_span(lines, 0, 11) == (2, 1)


def test_unbalanced_span_is_none():
    assert find_block_span(["\tallowed = {", "\t\ta = b"], 0, 11) is None


def test_stack_names_each_level():
    stack = []
    apply_brace_stack(code_of_line("ideas = {"), stack)
    assert stack == ["ideas"]
    apply_brace_stack(code_of_line("\tcountry = {"), stack)
    assert stack == ["ideas", "country"]
    apply_brace_stack(code_of_line("\t\tFOO = { OR = { a = b } }"), stack)
    assert stack == ["ideas", "country"]
    apply_brace_stack(code_of_line("\t}"), stack)
    assert stack == ["ideas"]


def test_stack_pushes_an_empty_name_for_a_bare_brace():
    stack = []
    apply_brace_stack("{", stack)
    assert stack == [""]


def test_stack_pop_on_an_empty_stack_is_survivable():
    stack = []
    apply_brace_stack("}", stack)
    assert stack == []


def test_code_of_line_blanks_quotes_and_comments_without_moving_columns():
    line = '\tname = "a } b" # }'
    code = code_of_line(line)
    assert "}" not in code
    assert code.index('"') == line.index('"')


def test_gap_collapses_a_doubled_blank():
    out = ["a", ""]
    lines = ["", "b"]
    assert collapse_blank_gap(out, lines, 0) == 1
    assert out == ["a", ""]


def test_gap_collapses_a_blank_under_the_parent_opener():
    out = ["FOO = {"]
    lines = ["", "\tb = c"]
    assert collapse_blank_gap(out, lines, 0) == 1


def test_gap_drops_a_blank_left_above_the_parent_closer():
    out = ["FOO = {", "\tb = c", ""]
    lines = ["}"]
    assert collapse_blank_gap(out, lines, 0) == 0
    assert out == ["FOO = {", "\tb = c"]


def test_gap_keeps_a_real_separator():
    out = ["FOO = {", "\tb = c"]
    lines = ["", "\td = e"]
    assert collapse_blank_gap(out, lines, 0) == 0
    assert out == ["FOO = {", "\tb = c"]
