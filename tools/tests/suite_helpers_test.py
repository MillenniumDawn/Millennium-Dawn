"""Behaviour tests for tools/shared/suite.py."""

from shared.paths import TOOLS_DIR
from shared.suite import (
    collecting_validator,
    initialize_git_repository,
    issue_dict,
    make_results_tree,
    run_git,
    write_slug_json,
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


def test_issue_dict_defaults():
    assert issue_dict("warning") == {
        "severity": "warning",
        "category": "c",
        "message": "m",
        "file": "a.txt",
        "line": 1,
    }


def test_write_text_creates_parents_and_returns_path(tmp_path):
    path = write_text(tmp_path / "nested" / "file.txt", "hello\n")
    assert path.read_text(encoding="utf-8") == "hello\n"
    assert path == tmp_path / "nested" / "file.txt"


def test_write_slug_json_and_results_tree(tmp_path):
    write_slug_json(tmp_path, "events", [{"severity": "error"}])
    assert (tmp_path / "events.json").read_text(encoding="utf-8") == (
        '[{"severity": "error"}]'
    )

    root = make_results_tree(
        tmp_path,
        {
            "events": {
                "log": "ok\n",
                "issues": [{"severity": "warning"}],
            }
        },
    )
    sub = root / "validation-events-results"
    assert (sub / "validation-events.log").read_text(encoding="utf-8") == "ok\n"
    assert "warning" in (sub / "validation-events.json").read_text(encoding="utf-8")


def test_initialize_git_repository_commits_added_paths(tmp_path):
    tracked = tmp_path / "history" / "units"
    tracked.mkdir(parents=True)
    write_text(tracked / "oob.txt", "units = { }\n")
    initialize_git_repository(tmp_path, "history/units")
    names = run_git(tmp_path, "ls-files").stdout.splitlines()
    assert "history/units/oob.txt" in names


def test_suite_module_lives_in_shared_not_tests_root():
    assert (TOOLS_DIR / "shared" / "suite.py").is_file()
    assert not (TOOLS_DIR / "suite_helpers.py").exists()
