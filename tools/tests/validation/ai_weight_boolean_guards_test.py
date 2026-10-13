"""Opposite scripted boolean guards require a real trigger definition."""

import validate_ai_weight_order as V
from shared.suite import issue_rows, run_validator

_SCRIPT = (
    "ai_will_do = {\n"
    " modifier = { factor = 0 test_path = yes }\n"
    " modifier = { add = 5 test_path = no }\n"
    "}\n"
)


def test_only_defined_scripted_triggers_are_boolean():
    assert len(V.scan_text(_SCRIPT)) == 1
    assert V.scan_text(_SCRIPT, frozenset({"test_path"})) == []


def test_changed_trigger_definitions_invalidate_cached_weights(
    tmp_path, write_path, issues_by_line, monkeypatch
):
    monkeypatch.delenv("MD_NO_CACHE", raising=False)
    write_path(tmp_path, "common/decisions/Test.txt", _SCRIPT)
    trigger_path = "common/scripted_triggers/Test.txt"
    write_path(tmp_path, trigger_path, "other_path = { always = yes }")

    assert len(issue_rows(issues_by_line(V.Validator, tmp_path)[1])) == 1
    write_path(tmp_path, trigger_path, "test_path = { always = yes }")
    assert issue_rows(issues_by_line(V.Validator, tmp_path)[1]) == []
    assert issue_rows(issues_by_line(V.Validator, tmp_path)[1]) == []
    assert issue_rows(run_validator(V.Validator, tmp_path)) == []

    write_path(tmp_path, trigger_path, "other_path = { always = yes }")
    assert len(issue_rows(issues_by_line(V.Validator, tmp_path)[1])) == 1
