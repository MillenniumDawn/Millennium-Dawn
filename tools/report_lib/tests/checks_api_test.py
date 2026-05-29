"""Tests for annotation-building logic in `report_lib.checks_api`.

HTTP posting is NOT exercised here — those tests belong in integration
against a real GitHub sandbox. We only verify that the payload the library
builds from a ValidatorRun matches our expectations (conclusion, annotation
level, truncation).
"""

from report_lib.checks_api import (
    MAX_ANNOTATIONS_PER_CHECK,
    _build_check_payload,
    _conclusion_for,
    _pick_annotations,
)
from report_lib.models import Issue, Severity, ValidatorRun


def _run_with_issues(issues, errors=None, warnings=None, status=None):
    errors = (
        errors
        if errors is not None
        else sum(1 for i in issues if i.severity == Severity.ERROR)
    )
    warnings = (
        warnings
        if warnings is not None
        else sum(1 for i in issues if i.severity == Severity.WARNING)
    )
    auto_status = status or (
        "failed" if errors else ("warnings" if warnings else "passed")
    )
    return ValidatorRun(
        name="events",
        title="Events",
        issues=issues,
        errors=errors,
        warnings=warnings,
        status=auto_status,
        log_text="log body",
    )


def test_conclusion_success_on_empty():
    run = _run_with_issues([])
    assert _conclusion_for(run) == "success"


def test_conclusion_neutral_on_warnings_only():
    run = _run_with_issues(
        [
            Issue(
                severity=Severity.WARNING,
                category="c",
                message="m",
                file="a.txt",
                line=1,
                validator="events",
            )
        ]
    )
    assert _conclusion_for(run) == "neutral"


def test_conclusion_failure_on_any_error():
    run = _run_with_issues(
        [
            Issue(
                severity=Severity.ERROR,
                category="c",
                message="m",
                file="a.txt",
                line=1,
                validator="events",
            )
        ]
    )
    assert _conclusion_for(run) == "failure"


def test_pick_annotations_skips_issues_without_file():
    issues = [
        Issue(
            severity=Severity.ERROR,
            category="c",
            message="has location",
            file="a.txt",
            line=1,
            validator="events",
        ),
        Issue(
            severity=Severity.ERROR,
            category="c",
            message="no file",
            file="",
            line=5,
            validator="events",
        ),
        Issue(
            severity=Severity.ERROR,
            category="c",
            message="no line",
            file="b.txt",
            line=0,
            validator="events",
        ),
    ]
    run = _run_with_issues(issues)
    anns = _pick_annotations(run)
    assert len(anns) == 1
    assert anns[0]["path"] == "a.txt"
    assert anns[0]["annotation_level"] == "failure"


def test_pick_annotations_errors_before_warnings():
    issues = [
        Issue(
            severity=Severity.WARNING,
            category="c",
            message="W",
            file="a.txt",
            line=1,
            validator="events",
        ),
        Issue(
            severity=Severity.ERROR,
            category="c",
            message="E",
            file="b.txt",
            line=5,
            validator="events",
        ),
    ]
    run = _run_with_issues(issues)
    anns = _pick_annotations(run)
    assert anns[0]["annotation_level"] == "failure"
    assert anns[1]["annotation_level"] == "warning"


def test_pick_annotations_truncates_with_overflow_notice():
    issues = [
        Issue(
            severity=Severity.ERROR,
            category="c",
            message=f"msg {i}",
            file=f"file_{i:03d}.txt",
            line=1,
            validator="events",
        )
        for i in range(MAX_ANNOTATIONS_PER_CHECK + 10)
    ]
    run = _run_with_issues(issues)
    anns = _pick_annotations(run)
    assert len(anns) == MAX_ANNOTATIONS_PER_CHECK
    # Last annotation is the synthetic overflow notice
    assert "additional issue(s) truncated" in anns[-1]["title"]
    assert anns[-1]["annotation_level"] == "notice"


def test_build_check_payload_includes_head_sha_and_name():
    run = _run_with_issues(
        [
            Issue(
                severity=Severity.ERROR,
                category="c",
                message="x",
                file="a.txt",
                line=1,
                validator="events",
            )
        ]
    )
    annotations = _pick_annotations(run)
    payload = _build_check_payload(run, head_sha="abc1234", annotations=annotations)
    assert payload["head_sha"] == "abc1234"
    assert payload["name"] == "Events"
    assert payload["status"] == "completed"
    assert payload["conclusion"] == "failure"
    assert len(payload["output"]["annotations"]) == 1


def test_pick_annotations_returns_all_when_under_cap():
    """When issue count fits in the per-check cap, no truncation notice fires."""
    issues = [
        Issue(
            severity=Severity.ERROR,
            category="c",
            message=f"msg {i}",
            file=f"file_{i}.txt",
            line=1,
            validator="events",
        )
        for i in range(MAX_ANNOTATIONS_PER_CHECK)
    ]
    run = _run_with_issues(issues)
    anns = _pick_annotations(run)
    assert len(anns) == MAX_ANNOTATIONS_PER_CHECK
    # No overflow notice when we land exactly at the cap.
    assert "truncated" not in anns[-1]["title"]
    assert anns[-1]["annotation_level"] == "failure"
