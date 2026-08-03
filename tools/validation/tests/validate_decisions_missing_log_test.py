"""Tests for the decision log-in-complete_effect check."""

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
    validator.validate_missing_log()
    return validator.collected


def test_logged_decision_not_flagged(monkeypatch):
    factory = V.DecisionFactory(
        "dec_one = {\n\tcomplete_effect = {\n"
        '\t\tlog = "[GetDateText]: [Root.GetName]: Decision dec_one"\n'
        "\t}\n}",
        source_basename="X.txt",
    )
    assert _results_for([factory], monkeypatch) == []


def test_effect_without_log_flagged(monkeypatch):
    factory = V.DecisionFactory(
        "dec_two = {\n\tcomplete_effect = {\n\t\tadd_political_power = 10\n\t}\n}",
        source_basename="X.txt",
    )
    results = _results_for([factory], monkeypatch)
    assert len(results) == 1
    assert "dec_two" in results[0]
    assert "no log" in results[0]


def test_empty_complete_effect_skipped(monkeypatch):
    factory = V.DecisionFactory("dec_three = {\n}", source_basename="X.txt")
    assert _results_for([factory], monkeypatch) == []


def test_log_requires_quote(monkeypatch):
    # A bare `log = something` without quotes is not a log line.
    factory = V.DecisionFactory(
        "dec_four = {\n\tcomplete_effect = {\n\t\tlog = some_unquoted_thing\n\t}\n}",
        source_basename="X.txt",
    )
    results = _results_for([factory], monkeypatch)
    assert len(results) == 1


def test_log_matches_inside_multiline_effect(monkeypatch):
    factory = V.DecisionFactory(
        "dec_five = {\n\tcomplete_effect = {\n"
        "\t\tadd_political_power = 10\n"
        '\t\tlog = "[GetDateText]: [Root.GetName]: Decision dec_five"\n'
        "\t}\n}",
        source_basename="X.txt",
    )
    assert _results_for([factory], monkeypatch) == []
