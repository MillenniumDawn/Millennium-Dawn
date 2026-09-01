"""Tests for `report_lib.loader`."""

from report_lib import discover_validator_runs, load_all
from shared.suite import make_results_tree, write_log, write_sidecar, write_text


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


def test_load_single_flat_artifact(tmp_path):
    root = tmp_path / "validation-results"
    root.mkdir()
    write_log(root, "file-paths", "✓ VALIDATION COMPLETE - NO ISSUES FOUND\n")
    write_sidecar(root, "file-paths", [])

    runs = load_all(str(root))

    assert len(runs) == 1
    assert runs[0].name == "file-paths"
    assert runs[0].status == "passed"


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


def test_malformed_json_sidecar_fails_closed(tmp_path):
    root = make_results_tree(
        tmp_path,
        {"events": {"log": "✓ VALIDATION COMPLETE - NO ISSUES FOUND\n"}},
    )
    artifact = root / "validation-events-results"
    (artifact / "validation-events.json").write_text("{truncated", encoding="utf-8")

    run = load_all(str(root))[0]

    assert run.status == "failed"
    assert run.errors == 1
    assert run.issues[0].category == "malformed-validator-sidecar"


def test_non_list_json_sidecar_fails_closed(tmp_path):
    root = make_results_tree(tmp_path, {"events": {"log": "incomplete\n"}})
    artifact = root / "validation-events-results"
    (artifact / "validation-events.json").write_text("{}", encoding="utf-8")
    assert load_all(str(root))[0].status == "failed"


def test_empty_results_dir(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    assert load_all(str(empty)) == []


def test_missing_results_dir_returns_empty():
    assert load_all("/nonexistent/path/that/does/not/exist") == []


def test_discovery_ignores_non_artifact_entries(tmp_path):
    root = tmp_path / "validation-results"
    root.mkdir()
    # A plain file whose name looks like an artifact directory.
    write_text(root / "validation-decoy-results", "not a directory")
    # A flat artifact with an extension the loader does not read.
    write_text(root / "validation-notes.md", "ignored")
    write_sidecar(root, "events", [])

    assert [slug for slug, _ in discover_validator_runs(str(root))] == ["events"]


def test_legacy_total_issue_summary_line_counts_as_errors(tmp_path):
    log = (
        "  common/events/foo.txt:42 - missing localisation\n"
        "✗ VALIDATION COMPLETE - 3 TOTAL ISSUES FOUND\n"
    )
    root = make_results_tree(tmp_path, {"events": {"log": log}})

    run = load_all(str(root))[0]

    assert (run.errors, run.warnings, run.status) == (3, 0, "failed")


def test_sidecar_without_a_log_still_loads(tmp_path):
    root = tmp_path / "validation-results"
    write_sidecar(root, "events", [])

    run = load_all(str(root))[0]

    assert run.log_text is None
    assert run.status == "passed"


def test_unreadable_log_is_treated_as_absent(tmp_path):
    root = tmp_path / "validation-results"
    write_sidecar(root, "events", [])
    (root / "validation-events.log").write_bytes(b"\xff\xfe not utf-8 \xff")

    run = load_all(str(root))[0]

    assert run.log_text is None
    assert run.status == "passed"


def test_log_only_run_without_output_is_no_output(tmp_path):
    root = tmp_path / "validation-results"
    root.mkdir()
    # A directory artifact holding neither a .log nor a .json.
    (root / "validation-events-results").mkdir()
    write_text(root / "validation-events-results" / "notes.txt", "nothing useful")

    run = load_all(str(root))[0]

    assert run.status == "no_output"
    assert run.had_json is False


def test_failure_marker_without_parsable_issues_still_fails(tmp_path):
    root = make_results_tree(
        tmp_path, {"events": {"log": "✗ VALIDATION COMPLETE\nsomething went wrong\n"}}
    )

    run = load_all(str(root))[0]

    assert run.status == "failed"
    assert run.issues == []
