"""Tests for the decision fixed_random_seed check."""

import validate_decisions as V


class _FakeValidator(V.Validator):
    """Validator whose _report collects results instead of rendering."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.collected = []

    def _report(self, results, ok_msg, fail_msg, severity=None, category=""):
        self.collected.extend(results)


def _results_for(factories, monkeypatch):
    validator = _FakeValidator("/tmp")
    monkeypatch.setattr(V, "parse_all_decision_factories", lambda mod_path: factories)
    validator.validate_random_seed()
    return validator.collected


def _factory(body):
    return V.DecisionFactory(body, source_basename="X.txt")


def test_random_list_without_seed_flagged(monkeypatch):
    factory = _factory(
        "dec_one = {\n\tcomplete_effect = {\n"
        "\t\trandom_list = {\n\t\t\t50 = { add_stability = 0.01 }\n"
        "\t\t\t50 = { add_stability = -0.01 }\n\t\t}\n\t}\n}"
    )
    results = _results_for([factory], monkeypatch)
    assert len(results) == 1
    assert "dec_one" in results[0]


def test_random_chance_without_seed_flagged(monkeypatch):
    factory = _factory(
        "dec_two = {\n\tremove_effect = {\n"
        "\t\trandom = {\n\t\t\tchance = 50\n\t\t\tadd_stability = 0.01\n\t\t}\n\t}\n}"
    )
    results = _results_for([factory], monkeypatch)
    assert len(results) == 1
    assert "dec_two" in results[0]


def test_explicit_no_seed_not_flagged(monkeypatch):
    factory = _factory(
        "dec_three = {\n\tfixed_random_seed = no\n\tremove_effect = {\n"
        "\t\trandom = {\n\t\t\tchance = 50\n\t\t\tadd_stability = 0.01\n\t\t}\n\t}\n}"
    )
    assert _results_for([factory], monkeypatch) == []


def test_explicit_yes_seed_not_flagged(monkeypatch):
    # An explicit yes is a deliberate call for reproducible rolls.
    factory = _factory(
        "dec_four = {\n\tfixed_random_seed = yes\n\tcomplete_effect = {\n"
        "\t\trandom_list = {\n\t\t\t50 = { add_stability = 0.01 }\n"
        "\t\t\t50 = { add_stability = -0.01 }\n\t\t}\n\t}\n}"
    )
    assert _results_for([factory], monkeypatch) == []


def test_fire_only_once_not_flagged(monkeypatch):
    factory = _factory(
        "dec_five = {\n\tfire_only_once = yes\n\tcomplete_effect = {\n"
        "\t\trandom = {\n\t\t\tchance = 50\n\t\t\tadd_stability = 0.01\n\t\t}\n\t}\n}"
    )
    assert _results_for([factory], monkeypatch) == []


def test_fire_only_once_no_still_flagged(monkeypatch):
    factory = _factory(
        "dec_six = {\n\tfire_only_once = no\n\tcomplete_effect = {\n"
        "\t\trandom = {\n\t\t\tchance = 50\n\t\t\tadd_stability = 0.01\n\t\t}\n\t}\n}"
    )
    results = _results_for([factory], monkeypatch)
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
    assert _results_for([factory], monkeypatch) == []


def test_decision_without_randomness_not_flagged(monkeypatch):
    factory = _factory(
        "dec_eight = {\n\tcomplete_effect = {\n\t\tadd_political_power = 10\n\t}\n}"
    )
    assert _results_for([factory], monkeypatch) == []
