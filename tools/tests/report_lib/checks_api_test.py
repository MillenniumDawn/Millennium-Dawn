"""Tests for annotation-building and posting logic in `report_lib.checks_api`.

The GitHub transport is scripted through a fake `urlopen`, so the request
sequence (POST then PATCH per overflow batch), the payloads, and the failure
messages are all asserted without touching the network.
"""

import json
import urllib.error

import pytest
from report_lib import checks_api as CA
from report_lib.checks_api import (
    ANNOTATIONS_PER_REQUEST,
    MAX_ANNOTATIONS_PER_CHECK,
    MAX_MESSAGE_CHARS,
    _build_check_payload,
    _conclusion_for,
    _output_text,
    _pick_annotations,
    post_checks,
)
from report_lib.models import Issue, Severity, ValidatorRun
from shared.suite import http_error as _http_error


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


@pytest.mark.parametrize("status", ["failed", "unknown"])
def test_conclusion_failure_on_indeterminate_zero_count_run(status):
    run = _run_with_issues([], status=status)
    assert _conclusion_for(run) == "failure"


def test_conclusion_skips_no_output():
    run = _run_with_issues([], status="no_output")
    assert _conclusion_for(run) == "skipped"


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


def test_non_strict_error_is_neutral():
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
    run.strict = False
    assert _conclusion_for(run) == "neutral"


def test_non_strict_incomplete_run_is_failure():
    run = _run_with_issues([], errors=0, warnings=0, status="failed")
    run.strict = False
    run.execution_complete = False
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


def test_pick_annotations_returns_nothing_without_locations():
    issues = [
        Issue(
            severity=Severity.ERROR,
            category="c",
            message="no location",
            validator="events",
        )
    ]
    assert _pick_annotations(_run_with_issues(issues)) == []


def test_conclusion_failure_on_unrecognised_status():
    run = _run_with_issues([], errors=0, warnings=0, status="warnings")
    assert _conclusion_for(run) == "failure"


def test_summary_line_reports_no_issues_when_clean():
    payload = _build_check_payload(_run_with_issues([]), head_sha="abc", annotations=[])
    assert payload["output"]["summary"] == "No issues found."


def test_summary_line_omits_errors_when_only_warnings():
    run = _run_with_issues([], errors=0, warnings=2)
    payload = _build_check_payload(run, head_sha="abc", annotations=[])
    assert payload["output"]["summary"] == "2 warning(s)."


def _run_with_log(log_text):
    run = _run_with_issues([])
    run.log_text = log_text
    return run


def test_output_text_is_empty_without_a_log():
    assert _output_text(_run_with_log("")) == ""


def test_output_text_truncates_an_oversized_log():
    text = _output_text(_run_with_log("x" * (MAX_MESSAGE_CHARS + 5_000)))
    assert len(text) <= MAX_MESSAGE_CHARS
    assert text.endswith("... (truncated)\n```")


class _Resp:
    def __init__(self, body=b"{}"):
        self._body = body

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def _transport(monkeypatch, outcomes):
    """Script `urlopen` responses; returns the list of recorded requests."""
    calls = []

    def urlopen(request, timeout=None):
        calls.append(
            (
                request.get_method(),
                request.full_url,
                json.loads(request.data.decode("utf-8")),
                timeout,
            )
        )
        outcome = outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(CA.urllib.request, "urlopen", urlopen)
    return calls


def _error_issues(count):
    return [
        Issue(
            severity=Severity.ERROR,
            category="c",
            message=f"msg {i}",
            file=f"file_{i:03d}.txt",
            line=1,
            validator="events",
        )
        for i in range(count)
    ]


def test_post_checks_creates_one_check_run_per_validator(monkeypatch):
    runs = [_run_with_issues(_error_issues(1)), _run_with_issues([])]
    runs[1].name, runs[1].title = "ideas", "Ideas"
    calls = _transport(monkeypatch, [_Resp(b'{"id": 11}'), _Resp(b'{"id": 12}')])

    results = post_checks("MillenniumDawn", "Millennium-Dawn", "sha1", runs, "token")

    assert results == [("Events", True, "check #11"), ("Ideas", True, "check #12")]
    assert [c[0] for c in calls] == ["POST", "POST"]
    assert (
        calls[0][1]
        == "https://api.github.com/repos/MillenniumDawn/Millennium-Dawn/check-runs"
    )
    assert calls[0][2]["head_sha"] == "sha1"
    assert calls[0][2]["name"] == "Events"
    assert calls[1][2]["conclusion"] == "success"
    assert all(call[3] == 30 for call in calls)


def test_post_checks_patches_annotations_beyond_the_first_batch(monkeypatch):
    run = _run_with_issues(_error_issues(MAX_ANNOTATIONS_PER_CHECK))
    calls = _transport(monkeypatch, [_Resp(b'{"id": 7}'), _Resp(b"{}")])

    results = post_checks("owner", "repo", "sha1", [run], "token")

    assert results == [("Events", True, "check #7")]
    assert [c[0] for c in calls] == ["POST", "PATCH"]
    assert (
        calls[1][1] == "https://api.github.com/repos/owner/repo/check-runs/7"
    ), "PATCH must target the freshly created check run"
    assert len(calls[0][2]["output"]["annotations"]) == ANNOTATIONS_PER_REQUEST
    assert (
        len(calls[1][2]["output"]["annotations"])
        == MAX_ANNOTATIONS_PER_CHECK - ANNOTATIONS_PER_REQUEST
    )
    assert "head_sha" not in calls[1][2]


def test_post_checks_reports_a_failed_overflow_patch(monkeypatch):
    run = _run_with_issues(_error_issues(MAX_ANNOTATIONS_PER_CHECK))
    _transport(monkeypatch, [_Resp(b'{"id": 7}'), _http_error(422, b"unprocessable")])

    title, success, message = post_checks("owner", "repo", "sha1", [run], "token")[0]

    assert (title, success) == ("Events", False)
    assert "PATCH at offset 50 failed: HTTP 422: unprocessable" in message


def test_post_checks_reports_a_patch_error_with_an_unreadable_body(monkeypatch):
    run = _run_with_issues(_error_issues(MAX_ANNOTATIONS_PER_CHECK))
    _transport(monkeypatch, [_Resp(b'{"id": 7}'), _http_error(502, None)])

    _title, success, message = post_checks("owner", "repo", "sha1", [run], "token")[0]

    assert not success
    assert "HTTP 502: <no body>" in message


def test_post_checks_reports_a_patch_transport_error(monkeypatch):
    run = _run_with_issues(_error_issues(MAX_ANNOTATIONS_PER_CHECK))
    _transport(monkeypatch, [_Resp(b'{"id": 7}'), urllib.error.URLError("no route")])

    _title, success, message = post_checks("owner", "repo", "sha1", [run], "token")[0]

    assert not success
    assert "no route" in message


def test_post_checks_skips_patches_when_the_post_fails(monkeypatch):
    run = _run_with_issues(_error_issues(MAX_ANNOTATIONS_PER_CHECK))
    calls = _transport(monkeypatch, [_http_error(403, b"forbidden")])

    results = post_checks("owner", "repo", "sha1", [run], "token")

    assert results == [("Events", False, "HTTP 403: forbidden")]
    assert len(calls) == 1, "a failed POST must not be followed by PATCH batches"


def test_post_checks_reports_an_unreadable_error_body(monkeypatch):
    _transport(monkeypatch, [_http_error(500, None)])

    results = post_checks("owner", "repo", "sha1", [_run_with_issues([])], "token")

    assert results == [("Events", False, "HTTP 500: <no body>")]


def test_post_checks_reports_a_transport_error(monkeypatch):
    _transport(monkeypatch, [urllib.error.URLError("connection reset")])

    _title, success, message = post_checks(
        "owner", "repo", "sha1", [_run_with_issues([])], "token"
    )[0]

    assert not success
    assert "connection reset" in message


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
