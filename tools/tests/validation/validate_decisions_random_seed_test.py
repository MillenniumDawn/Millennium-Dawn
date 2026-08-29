"""Tests for the decision fixed_random_seed check."""

from shared.suite import _factory, results_for


def test_random_list_without_seed_flagged(monkeypatch):
    factory = _factory(
        "dec_one = {\n\tcomplete_effect = {\n"
        "\t\trandom_list = {\n\t\t\t50 = { add_stability = 0.01 }\n"
        "\t\t\t50 = { add_stability = -0.01 }\n\t\t}\n\t}\n}"
    )
    results = results_for([factory], monkeypatch, "validate_random_seed")
    assert len(results) == 1
    assert "dec_one" in results[0]


def test_random_chance_without_seed_flagged(monkeypatch):
    factory = _factory(
        "dec_two = {\n\tremove_effect = {\n"
        "\t\trandom = {\n\t\t\tchance = 50\n\t\t\tadd_stability = 0.01\n\t\t}\n\t}\n}"
    )
    results = results_for([factory], monkeypatch, "validate_random_seed")
    assert len(results) == 1
    assert "dec_two" in results[0]


def test_explicit_no_seed_not_flagged(monkeypatch):
    factory = _factory(
        "dec_three = {\n\tfixed_random_seed = no\n\tremove_effect = {\n"
        "\t\trandom = {\n\t\t\tchance = 50\n\t\t\tadd_stability = 0.01\n\t\t}\n\t}\n}"
    )
    assert results_for([factory], monkeypatch, "validate_random_seed") == []


def test_explicit_yes_seed_not_flagged(monkeypatch):
    # An explicit yes is a deliberate call for reproducible rolls.
    factory = _factory(
        "dec_four = {\n\tfixed_random_seed = yes\n\tcomplete_effect = {\n"
        "\t\trandom_list = {\n\t\t\t50 = { add_stability = 0.01 }\n"
        "\t\t\t50 = { add_stability = -0.01 }\n\t\t}\n\t}\n}"
    )
    assert results_for([factory], monkeypatch, "validate_random_seed") == []


def test_fire_only_once_not_flagged(monkeypatch):
    factory = _factory(
        "dec_five = {\n\tfire_only_once = yes\n\tcomplete_effect = {\n"
        "\t\trandom = {\n\t\t\tchance = 50\n\t\t\tadd_stability = 0.01\n\t\t}\n\t}\n}"
    )
    assert results_for([factory], monkeypatch, "validate_random_seed") == []


def test_fire_only_once_no_still_flagged(monkeypatch):
    factory = _factory(
        "dec_six = {\n\tfire_only_once = no\n\tcomplete_effect = {\n"
        "\t\trandom = {\n\t\t\tchance = 50\n\t\t\tadd_stability = 0.01\n\t\t}\n\t}\n}"
    )
    results = results_for([factory], monkeypatch, "validate_random_seed")
    assert len(results) == 1
    assert "dec_six" in results[0]


def test_random_scope_effects_not_flagged(monkeypatch):
    # random_owned_state / random_country are scope changes, not RNG rolls.
    factory = _factory(
        "dec_seven = {\n\tcomplete_effect = {\n"
        "\t\trandom_owned_state = { add_extra_state_shared_building_slots = 1 }\n"
        "\t\trandom_country = { add_opinion_modifier = { target = ROOT modifier = x } }\n"
        "\t}\n}"
    )
    assert results_for([factory], monkeypatch, "validate_random_seed") == []


def test_decision_without_randomness_not_flagged(monkeypatch):
    factory = _factory(
        "dec_eight = {\n\tcomplete_effect = {\n\t\tadd_political_power = 10\n\t}\n}"
    )
    assert results_for([factory], monkeypatch, "validate_random_seed") == []
