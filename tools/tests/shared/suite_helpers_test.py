"""Behaviour tests for tools/shared/suite.py."""

import json

import pytest
from shared.suite import (
    assert_findings,
    collecting_validator,
    initialize_git_repository,
    make_results_tree,
    run_git,
    write_text,
)


class _Stub:
    def __init__(self, *args, **kwargs):
        pass

    def _report(self, results, ok_msg, fail_msg, severity=None, category=""):
        raise AssertionError("unwrapped _report should not run")


def test_collecting_validator_appends_results_and_severity():
    wrapped = collecting_validator(_Stub)("/tmp")
    wrapped._report(["a", "b"], "ok", "fail", severity="error", category="x")
    assert wrapped.collected == ["a", "b"]
    assert wrapped.last_severity == "error"


@pytest.mark.parametrize(
    ("results", "expected", "passes"),
    (
        (["a - b"], ["a - b"], True),
        (["a - b"], [("a", "b")], True),
        (["a - b"], ["a"], False),
        (["a - b"], [], False),
        ([], [("a",)], False),
        (["a - b"], [("a",), ("b",)], False),
    ),
    ids=(
        "whole finding",
        "fragments",
        "string is not a fragment",
        "extra finding",
        "missing finding",
        "one finding for two entries",
    ),
)
def test_assert_findings_matches_each_finding_once(results, expected, passes):
    if passes:
        assert_findings(results, expected)
    else:
        with pytest.raises(AssertionError):
            assert_findings(results, expected)


def test_make_results_tree_writes_log_and_sidecar(tmp_path):
    issues = [{"severity": "warning", "message": "m"}]
    root = make_results_tree(tmp_path, {"events": {"log": "ok\n", "issues": issues}})
    sub = root / "validation-events-results"
    assert (sub / "validation-events.log").read_text(encoding="utf-8") == "ok\n"
    assert (
        json.loads((sub / "validation-events.json").read_text(encoding="utf-8"))
        == issues
    )


def test_make_results_tree_log_only_skips_sidecar(tmp_path):
    root = make_results_tree(tmp_path, {"events": {"log": "ok\n"}})
    sub = root / "validation-events-results"
    assert (sub / "validation-events.log").is_file()
    assert not (sub / "validation-events.json").exists()


def test_initialize_git_repository_commits_added_paths(tmp_path):
    tracked = tmp_path / "history" / "units"
    tracked.mkdir(parents=True)
    write_text(tracked / "oob.txt", "units = { }\n")
    initialize_git_repository(tmp_path, "history/units")
    names = run_git(tmp_path, "ls-files").stdout.splitlines()
    assert "history/units/oob.txt" in names
