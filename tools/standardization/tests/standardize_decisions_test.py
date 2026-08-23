"""Tests for the decision standardizer.

Regression guard for the corruption bug where the decision ID was read from an
inner property instead of the header line (renaming decisions to `remove_effect`,
`days_re_enable`, etc.) and block-valued properties were shredded line-by-line.
The standardizer must preserve every decision ID, keep all properties in source
order, and never drop or split content.
"""

import pytest
from shared_utils import collapse_or_compact
from standardize_decisions import (
    DecisionStandardizer,
    ensure_missing_ai_will_do,
    format_decision,
    inject_missing_decision_logs,
    strip_sole_decision_allowed,
)


def _decision(lines):
    """Wrap body lines into a decision block (header + closing brace), newline-terminated."""
    return [l + "\n" for l in lines]


def _ids(out_lines):
    """Category (col-0) and decision (1-tab) header identifiers, in order.

    Deeper property-block headers (`complete_effect = {` at 2+ tabs) are excluded.
    """
    ids = []
    for l in out_lines:
        indent = len(l) - len(l.lstrip("\t"))
        stripped = l.strip()
        if indent <= 1 and stripped.endswith("= {") and not stripped.startswith("#"):
            ids.append(stripped.split()[0])
    return ids


def test_id_read_from_header_not_inner_property():
    # First inner property is a block whose name would have been stolen as the ID.
    block = _decision(
        [
            "\tCHI_three_gorges_dam_decision = {",
            "\t\tremove_effect = {",
            "\t\t\tset_country_flag = foo",
            "\t\t}",
            "\t}",
        ]
    )
    out = format_decision(block)
    assert out[0].strip() == "CHI_three_gorges_dam_decision = {"
    assert "remove_effect = {" not in out[0]


def test_non_decision_suffixed_name_preserved():
    block = _decision(
        [
            "\tCHI_sco_upgrade_to_member = {",
            "\t\ticon = generic_decision",
            "\t}",
        ]
    )
    out = format_decision(block)
    assert out[0].strip() == "CHI_sco_upgrade_to_member = {"


def test_unknown_block_property_kept_intact_and_in_order():
    block = _decision(
        [
            "\tCHI_x_decision = {",
            "\t\tmodifier = {",
            "\t\t\tcivilian_factory_use = 30",
            "\t\t\tstability_factor = 0.05",
            "\t\t}",
            "\t\tai_will_do = { base = 1 }",
            "\t}",
        ]
    )
    out = format_decision(block)
    text = "\n".join(out)
    # modifier is a multi-leaf block: kept multi-line, not collapsed, not shredded.
    assert "civilian_factory_use = 30" in text
    assert "stability_factor = 0.05" in text
    # Order preserved: modifier before ai_will_do.
    assert text.index("modifier = {") < text.index("ai_will_do")
    # Re-parsing is idempotent.
    reparsed = format_decision([l + "\n" for l in out])
    assert reparsed[0].strip() == "CHI_x_decision = {"


def test_log_injected_into_complete_effect_when_missing():
    block = _decision(
        [
            "\tCHI_build_decision = {",
            "\t\tcomplete_effect = {",
            "\t\t\tadd_political_power = 10",
            "\t\t}",
            "\t}",
        ]
    )
    out = format_decision(block)
    text = "\n".join(out)
    assert 'log = "[GetDateText]: [Root.GetName]: Decision CHI_build_decision"' in text


def test_existing_complete_effect_log_not_duplicated():
    block = _decision(
        [
            "\tCHI_build_decision = {",
            "\t\tcomplete_effect = {",
            '\t\t\tlog = "[GetDateText]: [Root.GetName]: Decision CHI_build_decision"',
            "\t\t\tadd_political_power = 10",
            "\t\t}",
            "\t}",
        ]
    )
    out = format_decision(block)
    text = "\n".join(out)
    assert text.count("log =") == 1


def test_single_leaf_block_collapsed():
    block = _decision(
        [
            "\tCHI_x_decision = {",
            "\t\tvisible = {",
            "\t\t\thas_completed_focus = CHI_three_gorges_completion",
            "\t\t}",
            "\t}",
        ]
    )
    out = format_decision(block)
    visible_lines = [l for l in out if "visible" in l]
    assert visible_lines == [
        "\t\tvisible = { has_completed_focus = CHI_three_gorges_completion }"
    ]


def test_body_comment_hugs_the_property_it_describes():
    block = _decision(
        [
            "\tCHI_x_decision = {",
            "\t\tcost = 50",
            "\t\t# blocked once the ceasefire holds",
            "\t\tavailable = { has_war = yes }",
            "\t}",
        ]
    )
    out = format_decision(block)
    comment = out.index("\t\t# blocked once the ceasefire holds")
    assert out[comment + 1] == "\t\tavailable = { has_war = yes }"


def test_category_shell_preserved_and_decisions_reformatted():
    category = _decision(
        [
            "CHI_test_category = {",
            "\t# a leading comment",
            "\tCHI_first_decision = {",
            "\t\tremove_effect = {",
            "\t\t\tset_country_flag = foo",
            "\t\t}",
            "\t}",
            "\tCHI_second_decision = {",
            "\t\ticon = generic_decision",
            "\t}",
            "}",
        ]
    )
    std = DecisionStandardizer()
    props = std.extract_properties(category)
    out = std.format_block(props)
    assert out[0] == "CHI_test_category = {"
    ids = _ids(out)
    assert ids == ["CHI_test_category", "CHI_first_decision", "CHI_second_decision"]
    assert any("# a leading comment" in l for l in out)


def test_full_file_pass_preserves_all_ids():
    """End-to-end: a category with mixed decision names round-trips every ID."""
    src = _decision(
        [
            "CHI_cat = {",
            "\tCHI_alpha_decision = {",
            "\t\ttarget_array = global.majors",
            "\t\ttarget_trigger = { country_exists = FROM }",
            "\t\tcomplete_effect = {",
            "\t\t\tadd_political_power = 5",
            "\t\t}",
            "\t}",
            "\tsco_bilateral_trade_agreement = {",
            "\t\tfixed_random_seed = no",
            "\t\tai_will_do = { base = 1 }",
            "\t}",
            "}",
        ]
    )
    std = DecisionStandardizer()
    out = std.format_block(std.extract_properties(src))
    ids = _ids(out)
    assert ids == [
        "CHI_cat",
        "CHI_alpha_decision",
        "sco_bilateral_trade_agreement",
    ]
    text = "\n".join(out)
    # target_array / target_trigger / fixed_random_seed preserved (not dropped).
    assert "target_array = global.majors" in text
    assert "target_trigger = { country_exists = FROM }" in text
    assert "fixed_random_seed = no" in text


def test_multi_condition_block_stays_multi_line():
    # Comparison-operator children were invisible to the old `=`-only leaf test,
    # so this three-child block was wrongly collapsed onto one line.
    block = [
        "available = {\n",
        "\tNOT = { has_war = yes }\n",
        "\thas_political_power > 50\n",
        "\thas_stability > 0.25\n",
        "}\n",
    ]
    assert len(collapse_or_compact(block)) > 1

    # End-to-end: the emitted `available` spans multiple lines.
    decision = _decision(
        [
            "\tCHI_x_decision = {",
            "\t\tavailable = {",
            "\t\t\tNOT = { has_war = yes }",
            "\t\t\thas_political_power > 50",
            "\t\t\thas_stability > 0.25",
            "\t\t}",
            "\t}",
        ]
    )
    out = format_decision(decision)
    available_lines = [l for l in out if "has_political_power > 50" in l]
    assert available_lines == ["\t\t\thas_political_power > 50"]


def test_single_comparison_leaf_collapses():
    block = [
        "available = {\n",
        "\thas_political_power > 50\n",
        "}\n",
    ]
    assert collapse_or_compact(block) == ["available = { has_political_power > 50 }"]


def test_single_eq_leaf_still_collapses():
    block = [
        "visible = {\n",
        "\thas_completed_focus = CHI_x\n",
        "}\n",
    ]
    assert collapse_or_compact(block) == ["visible = { has_completed_focus = CHI_x }"]


def test_two_eq_children_stay_multi_line():
    block = [
        "modifier = {\n",
        "\tstability_factor = 0.05\n",
        "\twar_support_factor = 0.05\n",
        "}\n",
    ]
    assert len(collapse_or_compact(block)) > 1


def test_root_factor_converted_to_base_in_ai_will_do():
    block = _decision(
        [
            "\tTST_weighted_decision = {",
            "\t\tcost = 10",
            "\t\tai_will_do = {",
            "\t\t\tfactor = 5",
            "\t\t}",
            "\t}",
        ]
    )
    text = "\n".join(format_decision(block))
    assert "ai_will_do = { base = 5 }" in text
    assert "factor" not in text


def test_quoted_multiple_spaces_preserved_single_line():
    # Line-273 path: a single-line property whose quoted value has intentional
    # runs of spaces must stay byte-exact (old `" ".join(split())` collapsed them).
    block = _decision(
        [
            "\tCHI_x_decision = {",
            '\t\tcustom_tooltip = "Spaced    Out    Text"',
            "\t}",
        ]
    )
    text = "\n".join(format_decision(block))
    assert 'custom_tooltip = "Spaced    Out    Text"' in text


def test_quoted_multiple_spaces_preserved_in_reindented_block():
    # Line-79 path: multi-leaf block stays multi-line and is reindented; a quoted
    # value inside it must keep its internal spacing.
    block = _decision(
        [
            "\tCHI_x_decision = {",
            "\t\tmodifier = {",
            '\t\t\tcustom_modifier_tooltip = "A    B    C"',
            "\t\t\tstability_factor = 0.05",
            "\t\t}",
            "\t}",
        ]
    )
    text = "\n".join(format_decision(block))
    assert '"A    B    C"' in text


def test_log_string_spaces_preserved():
    block = _decision(
        [
            "\tCHI_x_decision = {",
            "\t\tcomplete_effect = {",
            '\t\t\tlog = "[GetDateText]: A   B"',
            "\t\t\tadd_political_power = 10",
            "\t\t}",
            "\t}",
        ]
    )
    text = "\n".join(format_decision(block))
    assert 'log = "[GetDateText]: A   B"' in text


def test_format_decision_idempotent():
    block = _decision(
        [
            "\tCHI_x_decision = {",
            '\t\tcustom_tooltip = "Spaced    Out"',
            "\t\tmodifier = {",
            "\t\t\tcivilian_factory_use = 30",
            "\t\t\tstability_factor = 0.05",
            "\t\t}",
            "\t\tcomplete_effect = {",
            "\t\t\tadd_political_power = 10",
            "\t\t}",
            "\t}",
        ]
    )
    once = format_decision(block)
    twice = format_decision([l + "\n" for l in once])
    assert once == twice


def test_modifier_factor_untouched_in_ai_will_do():
    block = _decision(
        [
            "\tTST_guarded_decision = {",
            "\t\tcost = 10",
            "\t\tai_will_do = {",
            "\t\t\tbase = 5",
            "\t\t\tmodifier = {",
            "\t\t\t\tfactor = 0",
            "\t\t\t\thas_war = yes",
            "\t\t\t}",
            "\t\t}",
            "\t}",
        ]
    )
    text = "\n".join(format_decision(block))
    assert "base = 5" in text
    assert "factor = 0" in text


def test_hyphenated_decision_id_preserved_and_idempotent():
    # Regression: `Communist-State_invite` was misread by the \w+-only header
    # regex and silently rewritten to the literal ID `decision`.
    block = _decision(
        [
            "\tCommunist-State_invite = {",
            "\t\tcomplete_effect = {",
            "\t\t\tadd_political_power = 10",
            "\t\t}",
            "\t}",
        ]
    )
    out = format_decision(block)
    assert out[0].strip() == "Communist-State_invite = {"
    text = "\n".join(out)
    assert 'Decision Communist-State_invite"' in text

    reparsed = format_decision([l + "\n" for l in out])
    assert reparsed == out


def test_hyphenated_decision_ids_survive_full_category_pass():
    category = _decision(
        [
            "Coalition_decisions = {",
            "\tCommunist-State_invite = {",
            "\t\ticon = generic_decision",
            "\t}",
            "\tCommunist-State_remove = {",
            "\t\ticon = generic_decision",
            "\t}",
            "}",
        ]
    )
    std = DecisionStandardizer()
    out = std.format_block(std.extract_properties(category))
    assert _ids(out) == [
        "Coalition_decisions",
        "Communist-State_invite",
        "Communist-State_remove",
    ]


def test_unreadable_decision_header_raises_instead_of_guessing():
    block = _decision(
        [
            "\t$broken@header = {",
            "\t\ticon = generic_decision",
            "\t}",
        ]
    )
    with pytest.raises(ValueError):
        format_decision(block)


def test_one_line_properties_are_not_blank_separated():
    # (defect) every property, one-liners included, was followed by a blank, so a
    # decision was double-spaced end to end and opened with a gap after `{`.
    out = format_decision(
        _decision(
            [
                "\tURA_world_opr = {",
                "\t\tallowed = { original_tag = URA }",
                "\t\ticon = GFX_decision_sovfed_button",
                "\t\tcost = 50",
                "\t\tdays_remove = 400",
                "\t\tai_will_do = { base = 10 }",
                "\t}",
            ]
        )
    )
    assert out == [
        "\tURA_world_opr = {",
        "\t\tallowed = { original_tag = URA }",
        "\t\ticon = GFX_decision_sovfed_button",
        "\t\tcost = 50",
        "\t\tdays_remove = 400",
        "\t\tai_will_do = { base = 10 }",
        "\t}",
    ]


def test_multiline_block_is_separated_from_one_line_run():
    out = format_decision(
        _decision(
            [
                "\tURA_world_opr = {",
                "\t\tcost = 50",
                "\t\tvisible = {",
                "\t\t\tcountry_exists = OPR",
                "\t\t\thas_country_flag = foo",
                "\t\t}",
                "\t}",
            ]
        )
    )
    assert out[-1] == "\t}"
    assert out[-2].strip() != ""
    blank_idx = out.index("")
    assert out[blank_idx - 1].strip() == "cost = 50"
    assert out[blank_idx + 1].strip() == "visible = {"


def test_unreadable_category_header_raises_instead_of_guessing():
    category = _decision(
        [
            "$broken@category = {",
            "\tCHI_x_decision = {",
            "\t\ticon = generic_decision",
            "\t}",
            "}",
        ]
    )
    with pytest.raises(ValueError):
        DecisionStandardizer().extract_properties(category)


def test_log_injected_into_remove_effect_when_missing():
    block = _decision(
        [
            "\tCHI_build_decision = {",
            "\t\tremove_effect = {",
            "\t\t\tadd_political_power = 10",
            "\t\t}",
            "\t}",
        ]
    )
    out = format_decision(block)
    text = "\n".join(out)
    assert 'log = "[GetDateText]: [Root.GetName]: Decision CHI_build_decision"' in text
    assert text.index("log =") < text.index("add_political_power")


def test_single_line_remove_effect_expanded_and_logged():
    block = _decision(
        [
            "\tCHI_visit = {",
            "\t\tremove_effect = { country_event = foo.1 }",
            "\t}",
        ]
    )
    out = format_decision(block)
    text = "\n".join(out)
    assert 'log = "[GetDateText]: [Root.GetName]: Decision CHI_visit"' in text
    assert "country_event = foo.1" in text


def test_logs_only_leaves_unrelated_formatting_alone():
    src = [
        "CHI_cat = {\n",
        "\tCHI_visit = {\n",
        "\t\tallowed = { tag = CHI }\n",
        "\t\tremove_effect = { country_event = foo.1 }\n",
        "\t}\n",
        "}\n",
    ]
    out = inject_missing_decision_logs(src)
    text = "".join(out)
    assert "allowed = { tag = CHI }" in text
    assert 'log = "[GetDateText]: [Root.GetName]: Decision CHI_visit"' in text
    assert "country_event = foo.1" in text
    assert text.count("log =") == 1


def test_strip_sole_decision_allowed_keeps_category_allowed():
    src = [
        "CHI_cat = {\n",
        "\tallowed = { tag = CHI }\n",
        "\tCHI_visit = {\n",
        "\t\tallowed = { tag = CHI }\n",
        "\t\ticon = generic_decision\n",
        "\t}\n",
        "}\n",
    ]
    out = "".join(strip_sole_decision_allowed(src))
    assert "\tallowed = { tag = CHI }" in out
    assert "\t\tallowed = { tag = CHI }" not in out
    assert "icon = generic_decision" in out


def test_ensure_ai_will_do_skips_decisions_that_already_have_it():
    src = [
        "CHI_cat = {\n",
        "\tCHI_ready = {\n",
        "\t\tai_will_do = { base = 5 }\n",
        "\t}\n",
        "\tCHI_bare = {\n",
        "\t\ticon = generic_decision\n",
        "\t}\n",
        "}\n",
    ]
    out = "".join(ensure_missing_ai_will_do(src))
    assert out.count("ai_will_do = { base = 5 }") == 1
    assert "ai_will_do = { base = 10 }" in out


def test_ensure_ai_will_do_skips_missions():
    src = [
        "CHI_cat = {\n",
        "\tCHI_timer = {\n",
        "\t\tdays_mission_timeout = 30\n",
        "\t\ttimeout_effect = { add_stability = -0.01 }\n",
        "\t}\n",
        "}\n",
    ]
    out = "".join(ensure_missing_ai_will_do(src))
    assert "ai_will_do" not in out
