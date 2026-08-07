"""Tests for the decision effect-block log checks."""

import validate_decisions as V


class _FakeValidator(V.Validator):
    """Validator whose _report collects results instead of rendering."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.collected = []

    def _report(self, results, ok_msg, fail_msg, severity=None, category=""):
        self.collected.extend(results)


def _results_for(factories, monkeypatch, check="validate_missing_log"):
    validator = _FakeValidator("/tmp")
    monkeypatch.setattr(V, "parse_all_decision_factories", lambda mod_path: factories)
    getattr(validator, check)()
    return validator.collected


def _factory(body):
    return V.DecisionFactory(body, source_basename="X.txt")


def test_logged_decision_not_flagged(monkeypatch):
    factory = _factory(
        "dec_one = {\n\tcomplete_effect = {\n"
        '\t\tlog = "[GetDateText]: [Root.GetName]: Decision dec_one"\n'
        "\t}\n}"
    )
    assert _results_for([factory], monkeypatch) == []


def test_effect_without_log_flagged(monkeypatch):
    factory = _factory(
        "dec_two = {\n\tcomplete_effect = {\n\t\tadd_political_power = 10\n\t}\n}"
    )
    results = _results_for([factory], monkeypatch)
    assert len(results) == 1
    assert "dec_two" in results[0]
    assert "no log" in results[0]


def test_empty_complete_effect_skipped(monkeypatch):
    factory = _factory("dec_three = {\n}")
    assert _results_for([factory], monkeypatch) == []


def test_log_requires_quote(monkeypatch):
    # A bare `log = something` without quotes is not a log line.
    factory = _factory(
        "dec_four = {\n\tcomplete_effect = {\n\t\tlog = some_unquoted_thing\n\t}\n}"
    )
    results = _results_for([factory], monkeypatch)
    assert len(results) == 1


def test_log_matches_inside_multiline_effect(monkeypatch):
    factory = _factory(
        "dec_five = {\n\tcomplete_effect = {\n"
        "\t\tadd_political_power = 10\n"
        '\t\tlog = "[GetDateText]: [Root.GetName]: Decision dec_five"\n'
        "\t}\n}"
    )
    assert _results_for([factory], monkeypatch) == []


def test_remove_timeout_cancel_effects_need_logs(monkeypatch):
    factory = _factory(
        "dec_six = {\n"
        "\tremove_effect = {\n\t\tadd_political_power = 10\n\t}\n"
        "\ttimeout_effect = {\n\t\tadd_stability = 0.05\n\t}\n"
        "\tcancel_effect = {\n\t\tadd_war_support = 0.05\n\t}\n"
        "}"
    )
    results = _results_for([factory], monkeypatch)
    assert len(results) == 3
    flagged = {r.split(": ")[1].split(" has")[0] for r in results}
    assert flagged == {"remove_effect", "timeout_effect", "cancel_effect"}


def test_each_effect_block_logs_for_itself(monkeypatch):
    # A log in complete_effect does not cover a bare remove_effect.
    factory = _factory(
        "dec_seven = {\n"
        "\tcomplete_effect = {\n"
        '\t\tlog = "[GetDateText]: [Root.GetName]: Decision dec_seven"\n'
        "\t\tadd_political_power = 10\n\t}\n"
        "\tremove_effect = {\n\t\tadd_political_power = -10\n\t}\n"
        "}"
    )
    results = _results_for([factory], monkeypatch)
    assert len(results) == 1
    assert "remove_effect" in results[0]


def test_single_line_effect_block_with_log_not_flagged(monkeypatch):
    factory = _factory(
        "dec_eight = {\n\tremove_effect = "
        '{ log = "[GetDateText]: [Root.GetName]: Decision dec_eight" }\n}'
    )
    assert _results_for([factory], monkeypatch) == []


def test_log_first_not_flagged(monkeypatch):
    factory = _factory(
        "dec_nine = {\n\tremove_effect = {\n"
        '\t\tlog = "[GetDateText]: [Root.GetName]: Decision dec_nine"\n'
        "\t\tadd_political_power = 10\n\t}\n}"
    )
    assert _results_for([factory], monkeypatch, "validate_log_not_first") == []


def test_log_after_an_effect_flagged(monkeypatch):
    factory = _factory(
        "dec_ten = {\n\ttimeout_effect = {\n"
        "\t\tadd_political_power = 10\n"
        '\t\tlog = "[GetDateText]: [Root.GetName]: Decision dec_ten"\n'
        "\t}\n}"
    )
    results = _results_for([factory], monkeypatch, "validate_log_not_first")
    assert len(results) == 1
    assert "timeout_effect" in results[0]
    assert "add_political_power" in results[0]


def test_nested_log_left_alone(monkeypatch):
    # A log inside a branch records which branch ran, so it is not "late".
    factory = _factory(
        "dec_eleven = {\n\tcomplete_effect = {\n"
        "\t\tcustom_effect_tooltip = some_tt\n"
        "\t\thidden_effect = {\n"
        '\t\t\tlog = "[GetDateText]: [Root.GetName]: Decision dec_eleven"\n'
        "\t\t}\n\t}\n}"
    )
    assert _results_for([factory], monkeypatch, "validate_log_not_first") == []


def test_comment_before_log_not_flagged(monkeypatch):
    factory = _factory(
        "dec_twelve = {\n\tcomplete_effect = {\n"
        "\t\t#the treasury hit is deliberate\n"
        '\t\tlog = "[GetDateText]: [Root.GetName]: Decision dec_twelve"\n'
        "\t\tadd_political_power = 10\n\t}\n}"
    )
    assert _results_for([factory], monkeypatch, "validate_log_not_first") == []


def test_quoted_brace_does_not_desync_statement_scan(monkeypatch):
    factory = _factory(
        "dec_thirteen = {\n\tcomplete_effect = {\n"
        '\t\tcustom_effect_tooltip = "a { brace } in a string"\n'
        '\t\tlog = "[GetDateText]: [Root.GetName]: Decision dec_thirteen"\n'
        "\t}\n}"
    )
    results = _results_for([factory], monkeypatch, "validate_log_not_first")
    assert len(results) == 1
    assert "custom_effect_tooltip" in results[0]
