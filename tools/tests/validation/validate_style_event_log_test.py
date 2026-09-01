"""Tests for `validate_style.py` event option log detection."""

import validate_style as V


def _findings(text):
    return V._check_event_log_standards(text, "events/Test.txt")


def test_option_with_effects_but_no_log_flagged():
    text = "option = {\n\tname = test.1.a\n\tadd_political_power = 50\n}\n"
    assert _findings(text) == [("Event option test.1.a has effects but no log", 1)]


def test_option_with_log_not_flagged():
    text = (
        "option = {\n"
        "\tname = test.1.a\n"
        '\tlog = "[GetDateText]: [Root.GetName]: test.1.a"\n'
        "\tadd_political_power = 50\n"
        "}\n"
    )
    assert _findings(text) == []


def test_trigger_only_option_not_flagged():
    text = "option = {\n\tname = test.1.a\n\ttrigger = {\n\t\ttag = CHE\n\t}\n}\n"
    assert _findings(text) == []


def test_single_line_trigger_only_option_not_flagged():
    text = "option = {\n\tname = test.1.a\n\ttrigger = { tag = CHE }\n}\n"
    assert _findings(text) == []


def test_trigger_plus_effect_without_log_still_flagged():
    text = (
        "option = {\n"
        "\tname = test.1.a\n"
        "\ttrigger = {\n"
        "\t\ttag = CHE\n"
        "\t}\n"
        "\tadd_political_power = 50\n"
        "}\n"
    )
    assert _findings(text) == [("Event option test.1.a has effects but no log", 1)]


def test_ai_chance_only_option_not_flagged():
    text = "option = {\n\tname = test.1.a\n\tai_chance = {\n\t\tbase = 10\n\t}\n}\n"
    assert _findings(text) == []
