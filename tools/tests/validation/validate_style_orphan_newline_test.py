"""Tests for `validate_style.py` orphaned `newline = yes` detection.

`newline = yes` is only meaningful between two tooltip-visible effects. The
regression this guards against is an effect being deleted while its paired
separator is left behind, which ends the tooltip on a blank line.
"""

import validate_style as V


def _lines(*body):
    """Wrap effect-block body lines in a focus, tab-indented as MD files are."""
    inner = "\n".join("\t\t\t" + line for line in body)
    return (
        "\tfocus = {\n\t\tid = TAG_focus\n\t\tcompletion_reward = {\n"
        + inner
        + "\n\t\t}\n\t}\n"
    )


def _orphan_lines(text):
    return [
        line for _, line in V._check_orphan_newline(text, "common/national_focus/x.txt")
    ]


# ---------------------------------------------------------------------------
# Flagged: nothing visible survives after the separator
# ---------------------------------------------------------------------------


def test_newline_before_update_focus_tree_is_flagged():
    """The PR #2991 regression: treasury lines cut, separator left behind."""
    text = _lines(
        'log = "[GetDateText]: [Root.GetName]: Focus TAG_focus"',
        "add_ideas = TAG_idea",
        "newline = yes",
        "update_focus_tree_obsolete_branches = yes",
    )
    assert _orphan_lines(text) == [6]


def test_newline_before_hidden_effect_is_flagged():
    text = _lines(
        "add_stability = 0.05",
        "newline = yes",
        "hidden_effect = {",
        "\tevery_core_state = {",
        "\t\tstate_flat_productivity_change_effect = yes",
        "\t}",
        "}",
    )
    assert _orphan_lines(text) == [5]


def test_newline_at_end_of_reward_is_flagged():
    text = _lines("add_political_power = 100", "newline = yes")
    assert _orphan_lines(text) == [5]


def test_consecutive_newlines_both_flagged_when_nothing_follows():
    text = _lines("add_stability = 0.05", "newline = yes", "newline = yes")
    assert _orphan_lines(text) == [5, 6]


def test_newline_before_if_carrying_only_hidden_effects_is_flagged():
    """`if` renders its children inline, so the scan walks into the block."""
    text = _lines(
        "add_stability = 0.05",
        "newline = yes",
        "if = {",
        "\tlimit = { has_idea = TAG_idea }",
        "\tset_country_flag = TAG_flag",
        "}",
    )
    assert _orphan_lines(text) == [5]


def test_newline_before_only_temp_variable_math_is_flagged():
    """Bare temp-var math renders nothing without a following apply effect."""
    text = _lines(
        "add_stability = 0.05",
        "newline = yes",
        "set_temp_variable = { treasury_change = gdp_per_capita }",
        "multiply_temp_variable = { treasury_change = -0.10 }",
    )
    assert _orphan_lines(text) == [5]


# ---------------------------------------------------------------------------
# Not flagged: the separator still separates visible output
# ---------------------------------------------------------------------------


def test_newline_last_in_if_block_is_not_flagged():
    """The MD separator idiom — the regression risk a naive `newline`+`}`
    regex would break."""
    text = _lines(
        "if = {",
        "\tlimit = { has_idea = the_military }",
        "\tset_temp_variable = { temp_opinion = 2 }",
        "\tchange_the_military_opinion = yes",
        "\tnewline = yes",
        "}",
        "add_political_power = 100",
    )
    assert _orphan_lines(text) == []


def test_newline_before_if_carrying_a_visible_effect_is_not_flagged():
    text = _lines(
        "add_stability = 0.05",
        "newline = yes",
        "if = {",
        "\tlimit = { has_idea = TAG_idea }",
        "\tadd_political_power = 100",
        "}",
    )
    assert _orphan_lines(text) == []


def test_newline_before_power_balance_is_not_flagged():
    text = _lines(
        "add_stability = 0.05",
        "newline = yes",
        "add_power_balance_value = {",
        "\tid = TAG_balance_category",
        "\tvalue = 0.1",
        "}",
    )
    assert _orphan_lines(text) == []


def test_newline_before_treasury_apply_is_not_flagged():
    text = _lines(
        "add_stability = 0.05",
        "newline = yes",
        "set_temp_variable = { treasury_change = gdp_per_capita }",
        "multiply_temp_variable = { treasury_change = -0.10 }",
        "modify_treasury_effect = yes",
    )
    assert _orphan_lines(text) == []


def test_visible_effect_after_hidden_effect_is_not_flagged():
    text = _lines(
        "add_stability = 0.05",
        "newline = yes",
        "hidden_effect = { set_country_flag = TAG_flag }",
        "add_political_power = 100",
    )
    assert _orphan_lines(text) == []


def test_newline_outside_an_effect_block_is_ignored():
    """Only reward/effect blocks are scanned."""
    text = "\tfocus = {\n\t\tid = TAG_focus\n\t\tnewline = yes\n\t}\n"
    assert _orphan_lines(text) == []


def test_commented_out_effect_does_not_count_as_visible():
    text = _lines(
        "add_stability = 0.05",
        "newline = yes",
        "# add_political_power = 100",
        "update_focus_tree_obsolete_branches = yes",
    )
    assert _orphan_lines(text) == [5]


# ---------------------------------------------------------------------------
# Other effect-block types and validator-level wiring
# ---------------------------------------------------------------------------


def test_decision_complete_effect_is_scanned():
    text = (
        "\tTAG_decision = {\n"
        "\t\tcomplete_effect = {\n"
        '\t\t\tlog = "decision"\n'
        "\t\t\tadd_stability = 0.05\n"
        "\t\t\tnewline = yes\n"
        "\t\t}\n"
        "\t}\n"
    )
    assert _orphan_lines(text) == [5]


def test_scan_file_includes_orphan_findings():
    text = _lines("add_ideas = TAG_idea", "newline = yes")
    messages = [m for m, _ in V._scan_file(text, "common/national_focus/x.txt")]
    assert any("Orphaned newline" in m for m in messages)


def test_orphan_findings_are_error_severity(tmp_path):
    focus_dir = tmp_path / "common" / "national_focus"
    focus_dir.mkdir(parents=True)
    (focus_dir / "test.txt").write_text(
        "focus_tree = {\n" + _lines("add_ideas = TAG_idea", "newline = yes") + "}\n",
        encoding="utf-8",
    )

    v = V.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    v.run_validations()

    assert v.errors_found > 0
    assert any(i.category == "orphan-newline" for i in v._issues)
