"""Tests for the decision standardizer.

Regression coverage for the ID-corruption bug: the decision ID lives on the
block's declaration line, and an unrecognized top-level property (e.g.
days_re_enable) must never be mistaken for it. Also covers the root
factor -> base conversion wired into decision ai_will_do emission.
"""

from standardize_decisions import DecisionStandardizer


def _standardize(block):
    s = DecisionStandardizer()
    props = s.extract_properties(block)
    return props, s.format_block(props)


def test_id_survives_unrecognized_top_level_line():
    props, out = _standardize(
        [
            "\tCOM_disband_the_presidential_guard_decision = {\n",
            "\t\ticon = generic_civil_support\n",
            "\t\tcost = 25\n",
            "\t\tdays_re_enable = 180\n",
            "\t\tcomplete_effect = {\n",
            "\t\t\tadd_political_power = 10\n",
            "\t\t}\n",
            "\t}\n",
        ]
    )
    assert props["id"] == "COM_disband_the_presidential_guard_decision"
    assert out[0] == "\tCOM_disband_the_presidential_guard_decision = {"
    assert any(l.strip() == "days_re_enable = 180" for l in out)


def test_id_survives_when_all_properties_recognized():
    props, out = _standardize(
        [
            "\tTST_simple_decision = {\n",
            "\t\ticon = generic_civil_support\n",
            "\t\tcost = 10\n",
            "\t\tvisible = {\n",
            "\t\t\toriginal_tag = TST\n",
            "\t\t}\n",
            "\t}\n",
        ]
    )
    assert props["id"] == "TST_simple_decision"
    assert out[0] == "\tTST_simple_decision = {"


def test_other_lines_emitted_without_trailing_newline():
    _, out = _standardize(
        [
            "\tTST_timed_decision = {\n",
            "\t\tdays_re_enable = 90\n",
            "\t}\n",
        ]
    )
    assert not any(l.endswith("\n") for l in out)


def test_root_factor_converted_to_base_in_decision_ai_will_do():
    _, out = _standardize(
        [
            "\tTST_weighted_decision = {\n",
            "\t\tcost = 10\n",
            "\t\tai_will_do = {\n",
            "\t\t\tfactor = 5\n",
            "\t\t}\n",
            "\t}\n",
        ]
    )
    assert any(l.strip() == "ai_will_do = { base = 5 }" for l in out)
    assert not any("factor" in l for l in out)


def test_modifier_factor_untouched_in_decision_ai_will_do():
    _, out = _standardize(
        [
            "\tTST_guarded_decision = {\n",
            "\t\tcost = 10\n",
            "\t\tai_will_do = {\n",
            "\t\t\tbase = 5\n",
            "\t\t\tmodifier = {\n",
            "\t\t\t\tfactor = 0\n",
            "\t\t\t\thas_war = yes\n",
            "\t\t\t}\n",
            "\t\t}\n",
            "\t}\n",
        ]
    )
    joined = "\n".join(out)
    assert "base = 5" in joined
    assert "factor = 0" in joined
