"""Parser-level tests for validate_modifiers' block scanners.

Everything the unknown-modifier check reports comes out of these three
functions, so a scanner that loses its place (a brace inside a quoted value, a
skip-block it forgets to leave) either hides a typo or invents one.
"""

from validate_modifiers import (
    _extract_modifier_blocks,
    _extract_modifier_entries_from_body,
    _extract_modifier_names_from_body,
    _extract_top_level_definition_blocks,
    _harvest_doctrine_folder_cost_factors,
    _harvest_idea_slot_cost_factors,
    _harvest_md_operation_names,
    _harvest_md_sub_unit_names,
    _is_ai_weight_block,
    _load_documented_modifiers,
    _redundant_enable_gates,
)

# --- modifier = { } harvesting ----------------------------------------------


def test_brace_inside_a_quoted_value_does_not_hide_the_block():
    text = (
        "test_idea = {\n"
        '\tname = "a { b } c"\n'
        "\tmodifier = {\n"
        "\t\tstability_factor = 0.1\n"
        "\t}\n"
        "}\n"
    )
    blocks = _extract_modifier_blocks(text)
    assert len(blocks) == 1
    assert _extract_modifier_names_from_body(blocks[0][1]) == ["stability_factor"]


def test_quoted_brace_inside_the_modifier_body_keeps_the_block_intact():
    text = (
        "\tmodifier = {\n"
        '\t\tcustom_modifier_tooltip = "x } y"\n'
        "\t\tif = { limit = { always = yes } }\n"
        "\t\tstability_factor = 0.1\n"
        "\t}\n"
        "\tsecond_modifier_holder = { modifier = { war_support_factor = 0.2 } }\n"
    )
    blocks = _extract_modifier_blocks(text)
    assert len(blocks) == 2
    # The quoted `}` must not close the block early, and the nested if/limit
    # braces must not close it late.
    assert "stability_factor = 0.1" in blocks[0][1]
    assert _extract_modifier_names_from_body(blocks[1][1]) == ["war_support_factor"]


def test_modifier_inside_a_skip_block_is_not_harvested():
    text = (
        "test_focus = {\n"
        "\tequipment_bonus = {\n"
        "\t\tmodifier = {\n"
        "\t\t\tbuild_cost_ic = -0.1\n"
        "\t\t}\n"
        "\t}\n"
        "\tmodifier = {\n"
        "\t\tstability_factor = 0.1\n"
        "\t}\n"
        "}\n"
    )
    blocks = _extract_modifier_blocks(text)
    assert [_extract_modifier_names_from_body(b) for _l, b in blocks] == [
        ["stability_factor"]
    ]


def test_block_line_number_points_at_the_modifier_keyword():
    text = "a = {\n\tb = {\n\t\tmodifier = {\n\t\t\tstability_factor = 0.1\n\t\t}\n\t}\n}\n"
    assert _extract_modifier_blocks(text)[0][0] == 3


# --- AI weight detection ----------------------------------------------------


def test_empty_body_is_not_an_ai_weight_block():
    assert _is_ai_weight_block("") is False


def test_first_key_with_a_boolean_value_marks_an_ai_weight_block():
    assert _is_ai_weight_block("\n\t\tis_major = yes\n\t\thas_war = no\n") is True


def test_first_key_opening_a_block_marks_an_ai_weight_block():
    assert _is_ai_weight_block("\n\t\tOR = {\n\t\t\ttag = USA\n\t\t}\n") is True


def test_body_whose_first_line_is_not_an_assignment_is_a_game_modifier():
    assert _is_ai_weight_block("\n\t\t}\n\t\tstability_factor = 0.1\n") is False


def test_numeric_modifier_body_is_a_game_modifier():
    assert _is_ai_weight_block("\n\t\tstability_factor = 0.1\n") is False


# --- entry extraction inside a body -----------------------------------------


def test_entries_skip_nested_blocks_and_malformed_names():
    body = (
        "\n"
        "\tstability_factor = 0.1\n"
        "\tcustom_modifier_tooltip = {\n"
        "\t\tnested_key = 1\n"
        "\t}\n"
        "\t_leading_underscore = 1\n"
        "\tno_equals_here\n"
        "\twar_support_factor = 0.2\n"
    )
    assert [name for name, _offset in _extract_modifier_entries_from_body(body)] == [
        "stability_factor",
        "war_support_factor",
    ]


def test_entry_offsets_are_zero_based_line_numbers_within_the_body():
    body = "\n\ticon = GFX_x\n\tstability_factor = 0.1\n"
    assert _extract_modifier_entries_from_body(body) == [("stability_factor", 2)]


# --- top-level definition blocks --------------------------------------------


def test_definition_scan_walks_past_quotes_and_non_block_assignments():
    text = (
        'version = "1.0 = { fake }"\n'
        "loose token here\n"
        "REAL_modifier = {\n\tstability_factor = 0.1\n}\n"
    )
    names = [
        name for name, _nl, _bl, _body in _extract_top_level_definition_blocks(text)
    ]
    assert "REAL_modifier" in names


def test_definition_scan_stops_at_an_unbalanced_block():
    text = "FIRST_modifier = {\n\tstability_factor = 0.1\n}\nSECOND_modifier = {\n"
    names = [
        name for name, _nl, _bl, _body in _extract_top_level_definition_blocks(text)
    ]
    assert names == ["FIRST_modifier"]


# --- engine-generated name harvesting ---------------------------------------


def test_idea_slot_cost_factors_cover_both_slot_spellings(tmp_path):
    path = tmp_path / "00_idea_tags.txt"
    path.write_text(
        "idea_tags = {\n"
        "\tslot = political_advisor\n"
        "\tcharacter_slot = head_of_government\n"
        "}\n",
        encoding="utf-8",
    )
    harvested = _harvest_idea_slot_cost_factors(
        [str(tmp_path / "absent.txt"), str(path)]
    )
    assert harvested == {
        "political_advisor_cost_factor",
        "head_of_government_cost_factor",
    }


def test_doctrine_folder_harvest_tolerates_a_vanished_file(tmp_path):
    assert (
        _harvest_doctrine_folder_cost_factors([str(tmp_path / "absent.txt")]) == set()
    )


def test_sub_unit_harvest_ignores_files_without_a_sub_units_block(tmp_path):
    unrelated = tmp_path / "filters.txt"
    unrelated.write_text("tank_filters = {\n\tvalues = { a b }\n}\n", encoding="utf-8")
    units = tmp_path / "units.txt"
    units.write_text(
        "sub_units = {\n\ttest_bat = {\n\t\tbuy_cost_ic = 1\n\t}\n}\n"
        "other_block = {\n\tnot_a_unit = {\n\t\tx = 1\n\t}\n}\n",
        encoding="utf-8",
    )
    assert _harvest_md_sub_unit_names([str(unrelated), str(units)]) == {"test_bat"}


def test_operation_harvest_ignores_empty_files(tmp_path):
    empty = tmp_path / "empty.txt"
    empty.write_text("", encoding="utf-8")
    ops = tmp_path / "ops.txt"
    ops.write_text("increase_graft = {\n\ticon = GFX_x\n}\n", encoding="utf-8")
    assert _harvest_md_operation_names([str(empty), str(ops)]) == {"increase_graft"}


# --- documentation parsing --------------------------------------------------


def test_multi_placeholder_family_is_not_turned_into_a_template(tmp_path):
    doc = tmp_path / "modifiers_documentation.md"
    doc.write_text(
        "## casualty_trickleback\n\n"
        '##  <span id="two"></span><Building>_<Terrain>_limit\n\n'
        "**Modified types**: arms_factory\n",
        encoding="utf-8",
    )
    names, templates_by_word = _load_documented_modifiers(str(doc))
    assert names == {"casualty_trickleback"}
    assert templates_by_word == {}


def test_missing_documentation_yields_nothing(tmp_path):
    assert _load_documented_modifiers(str(tmp_path / "absent.md")) == (set(), {})


# --- enable gates -----------------------------------------------------------


def test_empty_enable_block_is_not_a_finding():
    assert _redundant_enable_gates("\n\tenable = {}\n\tstability_factor = x\n") == []
