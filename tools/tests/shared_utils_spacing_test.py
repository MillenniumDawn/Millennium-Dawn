"""Unit tests for the spacing and block compaction helpers in shared_utils.

Guards the MD style rule (tools/standardization/README.md) that ``{``, ``}``
and ``=`` carry single spaces, while string interiors, comments and indentation
stay byte-exact.
"""

import pytest
from shared_utils import (
    collapse_nested_blocks,
    collapse_or_compact,
    collapse_ws_outside_quotes,
    compact_block,
    convert_root_factor_to_base,
    normalize_spacing,
)


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


def test_pads_bare_single_character_comparisons():
    assert normalize_spacing("\thas_war_support>0.5") == "\thas_war_support > 0.5"
    assert normalize_spacing("\tvalue<3") == "\tvalue < 3"


def test_collapses_extra_whitespace_outside_strings():
    assert normalize_spacing("\tcost   =    10") == "\tcost = 10"


def test_trailing_whitespace_stripped():
    assert normalize_spacing("\tcost = 10   ") == "\tcost = 10"


def test_comment_line_is_unchanged():
    assert normalize_spacing("\t# unchanged = {x}") == "\t# unchanged = {x}"


def test_compact_block_drops_blank_lines_and_trailing_space():
    assert compact_block(["a\n", "\n", " b  \n"]) == ["a", " b"]


def test_collapse_ws_outside_quotes():
    assert collapse_ws_outside_quotes('  a   "b  c"  d  ') == 'a "b  c" d'


@pytest.mark.parametrize(
    "lines, base_line",
    [
        (["ai_will_do = {\n", " factor = 2\n", "}\n"], " base = 2\n"),
        (["ai_will_do = {\n", " base = 2\n", "}\n"], " base = 2\n"),
    ],
    ids=["root factor", "already base"],
)
def test_convert_root_factor_to_base(lines, base_line):
    assert convert_root_factor_to_base(lines)[1] == base_line


@pytest.mark.parametrize(
    "lines, expected",
    [
        (["a = {\n", " b = 1\n", "}\n"], ["a = { b = 1 }"]),
        (["a = { # keep\n", " b = 1\n", "}\n"], ["a = { # keep", "\tb = 1", "}"]),
    ],
    ids=["one leaf", "commented opener"],
)
def test_collapse_or_compact(lines, expected):
    assert collapse_or_compact(lines) == expected


def test_collapse_or_compact_reindents_a_multi_line_block():
    # Issue #4650: nested lines written at the wrong depth kept their tabs.
    block = [
        "\t\t34 = {\n",
        "\t\t\tadd_building_construction = {\n",
        "\t\t\ttype = infrastructure\n",
        "\t\t\tlevel = 1\n",
        "\t\t\t}\n",
        "\t\t}\n",
    ]
    expected = [
        "\t\t34 = {",
        "\t\t\tadd_building_construction = {",
        "\t\t\t\ttype = infrastructure",
        "\t\t\t\tlevel = 1",
        "\t\t\t}",
        "\t\t}",
    ]
    assert collapse_or_compact(block) == expected
    assert collapse_or_compact([line.lstrip() for line in block], "\t\t") == expected


_REWARD = [
    "\t\tcompletion_reward = {",
    '\t\t\tlog = "x"',
    "\t\t\tset_temp_variable = {",
    "\t\t\t\tparty_popularity_increase = 0.1",
    "\t\t\t}",
    "\t\t\thas_country_leader = {",
    '\t\t\t\tname = "Serzh Sargsyan"',
    "\t\t\t\truling_only = yes",
    "\t\t\t}",
    "\t\t}",
]
_REWARD_COLLAPSED = [
    "\t\tcompletion_reward = {",
    '\t\t\tlog = "x"',
    "\t\t\tset_temp_variable = { party_popularity_increase = 0.1 }",
    "\t\t\thas_country_leader = {",
    '\t\t\t\tname = "Serzh Sargsyan"',
    "\t\t\t\truling_only = yes",
    "\t\t\t}",
    "\t\t}",
]


def test_collapse_nested_blocks_collapses_one_leaf_children_once():
    assert collapse_nested_blocks(_REWARD) == _REWARD_COLLAPSED
    assert collapse_nested_blocks(_REWARD_COLLAPSED) == _REWARD_COLLAPSED
    assert collapse_or_compact(_REWARD) == _REWARD_COLLAPSED


# case: (block lines, collapsed lines)
_NESTED_CASES = {
    # Innermost first, at any depth.
    "innermost first": (
        [
            "a = {",
            "\tb = {",
            "\t\tc = {",
            "\t\t\tx = 1",
            "\t\t}",
            "\t\ty = 2",
            "\t}",
            "}",
        ],
        ["a = {", "\tb = {", "\t\tc = { x = 1 }", "\t\ty = 2", "\t}", "}"],
    ),
    "a child with a comment stays multi-line": (
        ["a = {", "\tb = {", "\t\tx = 1 # note", "\t}", "\tc = 3", "}"],
        ["a = {", "\tb = {", "\t\tx = 1 # note", "\t}", "\tc = 3", "}"],
    ),
    "unbalanced input is left alone": (
        ["a = {", "\tb = {", "\t\tx = 1", "}"],
        ["a = {", "\tb = {", "\t\tx = 1", "}"],
    ),
    "one line": (["a = { b = 1 }"], ["a = { b = 1 }"]),
}


@pytest.mark.parametrize(
    ("lines", "expected"), _NESTED_CASES.values(), ids=_NESTED_CASES
)
def test_collapse_nested_blocks(lines, expected):
    assert collapse_nested_blocks(lines) == expected


# A multi-token list is not a single leaf; a one-token list still collapses.
@pytest.mark.parametrize(
    "lines, expected",
    [
        (
            [
                "\t\t\treduce_focus_completion_cost = {",
                "\t\t\t\tcost = 20",
                "\t\t\t\tfocus = {",
                "\t\t\t\t\tCHI_project_921",
                "\t\t\t\t\tCHI_shenzhou_program",
                "\t\t\t\t}",
                "\t\t\t}",
            ],
            None,
        ),
        (
            [
                "\tx = {",
                "\t\tfocus = {",
                "\t\t\tJAP_blue_water_navy",
                "\t\t}",
                "\t\tcost = 35",
                "\t}",
            ],
            ["\tx = { focus = { JAP_blue_water_navy } cost = 35 }"],
        ),
    ],
    ids=["two tokens", "one token"],
)
def test_token_lists_collapse_only_with_one_token(lines, expected):
    assert collapse_or_compact(lines) == (lines if expected is None else expected)
