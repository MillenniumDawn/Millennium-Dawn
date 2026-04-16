"""Tests for `report_lib.loader`."""

from report_lib import load_all

from .conftest import make_results_tree


def test_load_passed_validator(tmp_path):
    root = make_results_tree(
        tmp_path,
        {
            "events": {
                "log": "################################################################################\n✓ VALIDATION COMPLETE - NO ISSUES FOUND\n################################################################################\n",
                "issues": [],
            }
        },
    )
    runs = load_all(str(root))
    assert len(runs) == 1
    run = runs[0]
    assert run.name == "events"
    assert run.status == "passed"
    assert run.errors == 0
    assert run.warnings == 0
    assert run.had_json is True


def test_load_failed_from_json_sidecar(tmp_path):
    issues = [
        {
            "severity": "error",
            "category": "unknown_unit",
            "message": "references template foo",
            "file": "history/units/FOO_1979.txt",
            "line": 12,
        },
        {
            "severity": "warning",
            "category": "unused",
            "message": "something",
            "file": "common/events/bar.txt",
            "line": 5,
        },
    ]
    root = make_results_tree(
        tmp_path,
        {
            "oob-units": {
                "log": "################################################################################\n✗ VALIDATION COMPLETE - 1 ERROR(S) - 1 WARNING(S)\n################################################################################\n",
                "issues": issues,
            }
        },
    )
    runs = load_all(str(root))
    assert len(runs) == 1
    run = runs[0]
    assert run.status == "failed"
    assert run.errors == 1
    assert run.warnings == 1
    assert run.issues[0].file == "history/units/FOO_1979.txt"
    assert run.issues[0].line == 12
    assert run.had_json is True


def test_load_warnings_only(tmp_path):
    root = make_results_tree(
        tmp_path,
        {
            "variables": {
                "log": "################################################################################\n✗ VALIDATION COMPLETE - 0 ERROR(S) - 2 WARNING(S)\n################################################################################\n",
                "issues": [
                    {
                        "severity": "warning",
                        "category": "unused",
                        "message": "x",
                        "file": "a.txt",
                        "line": 1,
                    },
                    {
                        "severity": "warning",
                        "category": "unused",
                        "message": "y",
                        "file": "b.txt",
                        "line": 2,
                    },
                ],
            }
        },
    )
    runs = load_all(str(root))
    assert runs[0].status == "warnings"
    assert runs[0].errors == 0
    assert runs[0].warnings == 2


def test_text_fallback_when_no_json(tmp_path):
    log = (
        "  common/events/foo.txt:42 - missing localisation EVT_FOO_DESC\n"
        "  common/events/foo.txt:98 - trigger is_bar never evaluated\n"
        "################################################################################\n"
        "✗ VALIDATION COMPLETE - 2 ERROR(S)\n"
        "################################################################################\n"
    )
    root = make_results_tree(tmp_path, {"events": {"log": log}})
    runs = load_all(str(root))
    assert len(runs) == 1
    run = runs[0]
    assert run.had_json is False
    # Parsed 2 issue lines from the log
    assert len(run.issues) == 2
    assert run.issues[0].file == "common/events/foo.txt"
    assert run.issues[0].line == 42


def test_text_fallback_warnings_only_marks_severity(tmp_path):
    """When the summary says ``0 ERROR(S) - N WARNING(S)`` every text-parsed
    issue should be tagged as WARNING and the overall status should be
    ``warnings`` — not ``failed``. Regresses a bug found during CLI smoke
    testing where text-fallback always defaulted to ERROR.
    """
    log = (
        "  common/events/foo.txt:42 - missing localisation EVT_FOO_DESC\n"
        "################################################################################\n"
        "✗ VALIDATION COMPLETE - 0 ERROR(S) - 2 WARNING(S)\n"
        "################################################################################\n"
    )
    root = make_results_tree(tmp_path, {"warnings": {"log": log}})
    runs = load_all(str(root))
    assert len(runs) == 1
    run = runs[0]
    assert run.had_json is False
    assert run.status == "warnings"
    # Summary-line counts override parsed issues for totals
    assert run.errors == 0
    assert run.warnings == 2
    # The one issue we were able to parse inherited the warning severity
    assert len(run.issues) == 1
    assert run.issues[0].severity == "warning"


def test_text_fallback_summary_counts_override_parsed(tmp_path):
    """Summary line ``2 ERROR(S)`` overrides parsed bullet count (only 1 here)."""
    log = (
        "  history/units/FOO.txt:12 - references template infantry_brigade_old\n"
        "✗ VALIDATION COMPLETE - 2 ERROR(S) - 1 WARNING(S)\n"
    )
    root = make_results_tree(tmp_path, {"oob": {"log": log}})
    runs = load_all(str(root))
    run = runs[0]
    assert run.errors == 2
    assert run.warnings == 1
    assert run.status == "failed"


def test_empty_results_dir(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    assert load_all(str(empty)) == []


def test_missing_results_dir_returns_empty():
    assert load_all("/nonexistent/path/that/does/not/exist") == []
