"""Tests for the decision standardizer.

Regression guard for the corruption bug where the decision ID was read from an
inner property instead of the header line (renaming decisions to `remove_effect`,
`days_re_enable`, etc.) and block-valued properties were shredded line-by-line.
The standardizer must preserve every decision ID, keep all properties in source
order, and never drop or split content.
"""

from shared_utils import collapse_or_compact
from standardize_decisions import DecisionStandardizer, format_decision


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
