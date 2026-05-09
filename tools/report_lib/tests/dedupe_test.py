"""Tests for `report_lib.dedupe`."""

from report_lib import Issue, Severity, dedupe


def _issue(**kw):
    defaults = dict(
        severity=Severity.ERROR,
        category="cat",
        message="m",
        file="a.txt",
        line=1,
        validator="v1",
    )
    defaults.update(kw)
    return Issue(**defaults)


def test_dedupe_keeps_unique_issues():
    issues = [
        _issue(file="a.txt", line=1),
        _issue(file="b.txt", line=2),
        _issue(file="a.txt", line=2),
    ]
    result = dedupe(issues)
    assert len(result) == 3


def test_dedupe_collapses_duplicates_across_validators():
    issues = [
        _issue(validator="events", file="a.txt", line=10, message="missing key X"),
        _issue(
            validator="localisation", file="a.txt", line=10, message="missing key X"
        ),
        _issue(validator="variables", file="a.txt", line=10, message="missing key X"),
    ]
    result = dedupe(issues)
    assert len(result) == 1
    merged = result[0]
    assert merged.validator == "events"  # first wins
    assert "localisation" in merged.detected_by
    assert "variables" in merged.detected_by


def test_dedupe_escalates_warning_to_error():
    issues = [
        _issue(validator="v1", severity=Severity.WARNING, file="a.txt", line=1),
        _issue(validator="v2", severity=Severity.ERROR, file="a.txt", line=1),
    ]
    result = dedupe(issues)
    assert len(result) == 1
    assert result[0].severity == Severity.ERROR


def test_dedupe_does_not_collapse_different_messages():
    issues = [
        _issue(file="a.txt", line=1, message="one"),
        _issue(file="a.txt", line=1, message="two"),
    ]
    result = dedupe(issues)
    assert len(result) == 2


def test_dedupe_preserves_order():
    issues = [
        _issue(file="c.txt", line=1),
        _issue(file="a.txt", line=1),
        _issue(file="b.txt", line=1),
    ]
    result = dedupe(issues)
    assert [i.file for i in result] == ["c.txt", "a.txt", "b.txt"]
