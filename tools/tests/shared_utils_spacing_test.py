"""Unit tests for shared_utils.normalize_spacing.

Guards the MD style rule (AGENTS.md) that ``{``, ``}`` and ``=`` carry single
spaces, while string interiors, comments and indentation stay byte-exact.
"""

from shared_utils import normalize_spacing


def test_pads_inline_block():
    assert (
        normalize_spacing("\t\t\t\tNOT = {country_exists = ENG}")
        == "\t\t\t\tNOT = { country_exists = ENG }"
    )


def test_pads_nested_and_splits_double_close():
    assert (
        normalize_spacing("\t\tNOT = {FRA={has_idea = EU_member}}")
        == "\t\tNOT = { FRA = { has_idea = EU_member } }"
    )


def test_pads_equals():
    assert (
        normalize_spacing("\tNOT = {western_liberals_are_in_power=yes}")
        == "\tNOT = { western_liberals_are_in_power = yes }"
    )


def test_quoted_string_untouched():
    line = '\tlog = "[GetDateText]: a=b {c}  d"'
    assert normalize_spacing(line) == line


def test_inline_comment_kept_with_single_space():
    assert (
        normalize_spacing("\tfoo = {bar = yes}\t# why {this} matters")
        == "\tfoo = { bar = yes } # why {this} matters"
    )


def test_whole_line_comment_untouched():
    assert normalize_spacing("\t# a note = {x}") == "\t# a note = {x}"


def test_blank_line_untouched():
    assert normalize_spacing("") == ""
    assert normalize_spacing("\t\t") == ""


def test_indentation_preserved():
    assert normalize_spacing("\t\t\tid = focus") == "\t\t\tid = focus"


def test_already_correct_line_unchanged():
    line = "\tavailable = { has_country_flag = some_flag }"
    assert normalize_spacing(line) == line


def test_idempotent():
    once = normalize_spacing("\tNOT={FRA={has_idea=EU_member}}")
    assert normalize_spacing(once) == once


def test_empty_block_keeps_its_spacing():
    assert normalize_spacing("\ton_add = {}") == "\ton_add = {}"
    assert normalize_spacing("\tsearch_filters = { }") == "\tsearch_filters = { }"


def test_comparison_operators_not_split():
    assert (
        normalize_spacing("\tcheck_variable = {x != 3}")
        == "\tcheck_variable = { x != 3 }"
    )
    assert (
        normalize_spacing("\tcheck_variable = {x>=3}")
        == "\tcheck_variable = { x >= 3 }"
    )
    assert normalize_spacing("\thas_war_support > 0.5") == "\thas_war_support > 0.5"


def test_collapses_extra_whitespace_outside_strings():
    assert normalize_spacing("\tcost   =    10") == "\tcost = 10"


def test_trailing_whitespace_stripped():
    assert normalize_spacing("\tcost = 10   ") == "\tcost = 10"
