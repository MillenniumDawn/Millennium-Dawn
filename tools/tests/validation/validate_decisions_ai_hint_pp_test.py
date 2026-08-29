"""Tests for the decision ai_hint_pp_cost check."""

from shared.suite import _factory, results_for


def test_custom_cost_trigger_pp_without_hint_flagged(monkeypatch):
    factory = _factory(
        "dec_one = {\n\tcustom_cost_trigger = {\n\t\thas_political_power > 74\n\t}\n"
        "\tcustom_cost_text = some_key\n}"
    )
    results = results_for([factory], monkeypatch, "validate_custom_cost_ai_hint")
    assert len(results) == 1
    assert "dec_one" in results[0]
    assert "custom_cost_trigger" in results[0]


def test_complete_effect_pp_without_hint_flagged(monkeypatch):
    factory = _factory(
        "dec_two = {\n\tcomplete_effect = {\n\t\tadd_political_power = -75\n\t}\n}"
    )
    results = results_for([factory], monkeypatch, "validate_custom_cost_ai_hint")
    assert len(results) == 1
    assert "dec_two" in results[0]
    assert "complete_effect spends 75 PP" in results[0]


def test_remove_effect_pp_without_hint_flagged(monkeypatch):
    factory = _factory(
        "dec_three = {\n\tdays_remove = 365\n\tremove_effect = {\n"
        "\t\tadd_political_power = -50\n\t}\n}"
    )
    results = results_for([factory], monkeypatch, "validate_custom_cost_ai_hint")
    assert len(results) == 1
    assert "remove_effect spends 50 PP" in results[0]


def test_hint_present_not_flagged(monkeypatch):
    factory = _factory(
        "dec_four = {\n\tai_hint_pp_cost = 75\n\tcomplete_effect = {\n"
        "\t\tadd_political_power = -75\n\t}\n}"
    )
    assert results_for([factory], monkeypatch, "validate_custom_cost_ai_hint") == []


def test_nested_pp_charge_not_flagged(monkeypatch):
    # A conditional charge is a gameplay outcome, not a price the AI budgets for.
    factory = _factory(
        "dec_five = {\n\tcomplete_effect = {\n\t\tif = {\n"
        "\t\t\tlimit = { has_war = yes }\n\t\t\tadd_political_power = -75\n\t\t}\n\t}\n}"
    )
    assert results_for([factory], monkeypatch, "validate_custom_cost_ai_hint") == []


def test_positive_pp_not_flagged(monkeypatch):
    factory = _factory(
        "dec_six = {\n\tcomplete_effect = {\n\t\tadd_political_power = 75\n\t}\n}"
    )
    assert results_for([factory], monkeypatch, "validate_custom_cost_ai_hint") == []


def test_ai_never_takes_decision_not_flagged(monkeypatch):
    factory = _factory(
        "dec_seven = {\n\tai_will_do = { base = 0 }\n\tcomplete_effect = {\n"
        "\t\tadd_political_power = -75\n\t}\n}"
    )
    assert results_for([factory], monkeypatch, "validate_custom_cost_ai_hint") == []


def test_mission_remove_effect_not_flagged(monkeypatch):
    # remove_effect on a non-selectable mission is a timeout outcome, not a cost.
    factory = _factory(
        "dec_eight = {\n\tdays_mission_timeout = 365\n\tremove_effect = {\n"
        "\t\tadd_political_power = -75\n\t}\n}"
    )
    assert results_for([factory], monkeypatch, "validate_custom_cost_ai_hint") == []


def test_reported_once_when_both_blocks_charge(monkeypatch):
    factory = _factory(
        "dec_nine = {\n\tcomplete_effect = {\n\t\tadd_political_power = -75\n\t}\n"
        "\tremove_effect = {\n\t\tadd_political_power = -50\n\t}\n}"
    )
    results = results_for([factory], monkeypatch, "validate_custom_cost_ai_hint")
    assert len(results) == 1
    assert "complete_effect spends 75 PP" in results[0]
