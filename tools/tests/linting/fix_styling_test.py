"""Tests for fix_styling.fix_line after it delegated spacing to normalize_spacing.

Guards the parts fix_line still owns on its own: leading spaces become tabs,
``===`` runs inside comments become ``---``, and a trailing newline survives.
"""

from fix_styling import fix_line


def test_pads_inline_block():
    fixed, fixes = fix_line("\t\tNOT = {country_exists = ENG}\n")
    assert fixed == "\t\tNOT = { country_exists = ENG }\n"
    assert fixes == 1


def test_leading_spaces_become_tabs():
    fixed, _ = fix_line("    x = { y = 1 }")
    assert fixed == "\tx = { y = 1 }"


def test_equals_separator_in_comment():
    fixed, _ = fix_line("\t# ==== section ====\n")
    assert fixed == "\t# ---- section ----\n"


def test_inline_comment_preserved():
    fixed, _ = fix_line("\tfoo=bar  # note ==== here\n")
    assert fixed == "\tfoo = bar # note ---- here\n"


def test_quoted_string_not_rewritten():
    line = '\tlog = "a=b {c}"\n'
    assert fix_line(line) == (line, 0)


def test_comment_line_keeps_single_newline():
    line = "# plain {comment}\n"
    assert fix_line(line) == (line, 0)


def test_trailing_whitespace_stripped():
    fixed, _ = fix_line("\tcost = 10   \n")
    assert fixed == "\tcost = 10\n"


def test_clean_line_reports_no_fixes():
    line = "\tavailable = { has_country_flag = some_flag }\n"
    assert fix_line(line) == (line, 0)
