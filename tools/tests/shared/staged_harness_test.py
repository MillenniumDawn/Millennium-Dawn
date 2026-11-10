"""Unit tests for the staged-integration harness runner. Nothing is staged."""

import json
import subprocess

import pytest
from shared import staged_harness

ERROR = {
    "severity": "error",
    "category": "missing-triggered-only",
    "message": "demo.1 - Event Horizon.txt",
    "file": "",
    "line": 0,
}
WARNING = {**ERROR, "severity": "warning"}


def _fake_validator(monkeypatch, returncode, issues):
    """Stand in for the validator process; issues=None writes no result file."""

    def fake_run(cmd, **_kwargs):
        if issues is not None:
            json_path = cmd[cmd.index("--output") + 1].removesuffix(".log") + ".json"
            with open(json_path, "w", encoding="utf-8", newline="") as handle:
                json.dump(issues, handle)
        return subprocess.CompletedProcess(cmd, returncode, stdout="", stderr="")

    monkeypatch.setattr(staged_harness.subprocess, "run", fake_run)


@pytest.mark.parametrize("expect_issues", [True, False, None])
@pytest.mark.parametrize(
    "returncode, issues",
    [
        (2, None),  # usage error
        (1, None),  # traceback before the result file was written
        (0, None),  # exited clean without a result file
        (1, []),  # exit 1 with no recorded error
        (0, [ERROR]),  # recorded error without the strict exit
    ],
)
def test_incomplete_run_fails(monkeypatch, returncode, issues, expect_issues):
    _fake_validator(monkeypatch, returncode, issues)
    problems, _, _ = staged_harness.check_validator(
        "validate_events.py", expect_issues=expect_issues
    )
    assert problems


@pytest.mark.parametrize(
    "returncode, issues, expect_issues, passes",
    [
        (0, [], False, True),
        (0, [WARNING], False, True),
        (0, [], None, True),
        (1, [ERROR], True, True),
        (1, [ERROR], None, True),
        (0, [], True, False),
        (1, [ERROR], False, False),
    ],
)
def test_completed_run_meets_expectation(
    monkeypatch, returncode, issues, expect_issues, passes
):
    _fake_validator(monkeypatch, returncode, issues)
    problems, _, _ = staged_harness.check_validator(
        "validate_events.py", expect_issues=expect_issues
    )
    assert (not problems) == passes


@pytest.mark.parametrize(
    "issues, passes",
    [
        ([ERROR], True),
        # Category on one finding, path on another.
        (
            [
                {**ERROR, "message": "demo.1 - other.txt"},
                {**ERROR, "category": "other", "file": "events/Event Horizon.txt"},
            ],
            False,
        ),
    ],
)
def test_category_and_path_share_one_finding(monkeypatch, issues, passes):
    _fake_validator(monkeypatch, 1, issues)
    problems, _, _ = staged_harness.check_validator(
        "validate_events.py",
        expected_path="Event Horizon.txt",
        expected_category="missing-triggered-only",
    )
    assert (not problems) == passes


def test_timeout_fails(monkeypatch):
    def hang(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd, kwargs["timeout"])

    monkeypatch.setattr(staged_harness.subprocess, "run", hang)
    problems, _, _ = staged_harness.check_validator(
        "validate_events.py", expect_issues=None
    )
    assert problems == ["TIMED OUT after 300s"]


def test_slow_run_fails_its_budget_without_a_timeout(monkeypatch):
    _fake_validator(monkeypatch, 0, [])
    monkeypatch.setattr(staged_harness, "MAX_TIME", -1.0)
    problems, _, _ = staged_harness.check_validator(
        "validate_events.py", expect_issues=False
    )
    assert len(problems) == 1 and problems[0].startswith("TOO SLOW")


def test_harness_tallies_failures(monkeypatch):
    harness = staged_harness.StagedHarness()
    _fake_validator(monkeypatch, 0, [])
    harness.run_validator("validate_events.py", "clean", expect_issues=False)
    assert harness.summary() == 0
    _fake_validator(monkeypatch, 2, None)
    harness.run_validator("validate_events.py", "crash", expect_issues=None)
    assert (harness.passed, harness.failed) == (1, 1)
    assert harness.summary() == 1


def test_restore_all_attempts_every_path_then_raises():
    seen = []

    def restore(path):
        seen.append(path)
        if path == "a":
            raise subprocess.CalledProcessError(128, "git reset")

    with pytest.raises(RuntimeError, match="a: Command 'git reset'"):
        staged_harness.restore_all(["a", "b"], restore)
    assert seen == ["a", "b"]
