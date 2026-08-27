"""Output-contract tests for run_all_validators without content scans."""

import io
import json
from types import SimpleNamespace

import pytest
import run_all_validators as runner


class _Process:
    def __init__(self, returncode=0):
        self.returncode = returncode

    def wait(self):
        return self.returncode


def _args(format_, output=None, strict=False, persist_results=None):
    return SimpleNamespace(
        format=format_,
        output=output,
        strict=strict,
        no_color=True,
        persist_results=persist_results,
    )


def _run_stub(tmp_path, args):
    validators = [("stub", "validate_stub.py", "Stub")]
    return runner._run_suite(args, [], str(tmp_path), validators, str(tmp_path))


def _launcher_with(issues, returncode=0):
    def launch(_script, _flags, output_dir, name, _mod_path):
        # Mirror BaseValidator.save_output: a validator with no findings
        # writes no JSON sidecar at all.
        if issues:
            try:
                with open(f"{output_dir}/{name}.json", "w", encoding="utf-8") as stream:
                    json.dump(issues, stream)
            except OSError:
                raise
        return _Process(returncode), io.StringIO()

    return launch


def test_collect_all_issues_uses_report_dedupe_and_escalation(tmp_path):
    warning = {
        "severity": "warning",
        "category": "same",
        "message": "same finding",
        "file": "a.txt",
        "line": 1,
    }
    error = {**warning, "severity": "error"}
    (tmp_path / "one.json").write_text(json.dumps([warning]), encoding="utf-8")
    (tmp_path / "two.json").write_text(json.dumps([error]), encoding="utf-8")

    issues = runner.collect_all_issues(
        str(tmp_path),
        [("one", "one.py", "One"), ("two", "two.py", "Two")],
    )

    assert len(issues) == 1
    assert issues[0]["severity"] == "error"
    assert issues[0]["detected_by"] == ["two"]


def test_collect_all_issues_rejects_malformed_sidecar(tmp_path):
    (tmp_path / "stub.json").write_text("{broken", encoding="utf-8")
    with pytest.raises(ValueError, match="Malformed validator sidecar"):
        runner.collect_all_issues(str(tmp_path), [("stub", "stub.py", "Stub")])


def test_manual_texture_audit_is_not_auto_discovered():
    scripts = {script for _name, script, _label in runner.discover_validators()}
    assert "validate_unused_textures.py" not in scripts


def test_summary_totals_use_deduplicated_issues(tmp_path, monkeypatch):
    finding = {
        "severity": "error",
        "category": "same",
        "message": "same finding",
        "file": "a.txt",
        "line": 1,
    }
    monkeypatch.setattr(runner, "launch_validator", _launcher_with([finding]))

    report_path = tmp_path / "report.json"
    code = runner._run_suite(
        _args("json", str(report_path), strict=True),
        [],
        str(tmp_path),
        [("one", "one.py", "One"), ("two", "two.py", "Two")],
        str(tmp_path),
    )

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert code == 1
    assert payload["total_errors"] == 1
    assert payload["total_warnings"] == 0
    assert len(payload["issues"]) == 1


def test_clean_both_writes_text_and_json_reports(tmp_path, monkeypatch):
    report_path = tmp_path / "report.txt"
    monkeypatch.setattr(runner, "launch_validator", _launcher_with([]))

    code = _run_stub(tmp_path, _args("both", str(report_path)))

    assert code == 0
    assert "ALL VALIDATIONS PASSED" in report_path.read_text(encoding="utf-8")
    try:
        json_text = (tmp_path / "report.json").read_text(encoding="utf-8")
    except OSError:
        raise
    try:
        payload = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise AssertionError("combined JSON report is invalid") from exc
    assert payload["total_errors"] == 0
    assert payload["issues"] == []


def test_json_output_honors_exact_output_path(tmp_path, monkeypatch):
    report_path = tmp_path / "report.json"
    monkeypatch.setattr(runner, "launch_validator", _launcher_with([]))

    code = _run_stub(tmp_path, _args("json", str(report_path)))

    assert code == 0
    assert report_path.exists()
    assert not (tmp_path / "report.json.json").exists()
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AssertionError("JSON report is missing or invalid") from exc
    assert payload["total_errors"] == 0


def test_both_output_without_extension_uses_distinct_files(tmp_path, monkeypatch):
    report_path = tmp_path / "report"
    monkeypatch.setattr(runner, "launch_validator", _launcher_with([]))

    code = _run_stub(tmp_path, _args("both", str(report_path)))

    assert code == 0
    assert "COMBINED VALIDATION REPORT" in report_path.read_text(encoding="utf-8")
    try:
        payload = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AssertionError("combined JSON report is missing or invalid") from exc
    assert payload["total_errors"] == 0


def test_json_without_output_prints_json_for_findings(tmp_path, monkeypatch, capsys):
    issues = [
        {
            "severity": "error",
            "category": "test-finding",
            "message": "broken café",
            "file": "test.txt",
            "line": 3,
        }
    ]
    monkeypatch.setattr(runner, "launch_validator", _launcher_with(issues, 1))

    code = _run_stub(tmp_path, _args("json", strict=True))

    captured = capsys.readouterr()
    try:
        payload = json.loads(captured.out)
    except json.JSONDecodeError as exc:
        raise AssertionError("stdout is not valid JSON") from exc
    assert code == 1
    assert payload["total_errors"] == 1
    assert payload["issues"][0]["message"] == "broken café"
    assert "VALIDATION FAILED" in captured.err


def test_persist_results_copies_json_sidecars(tmp_path, monkeypatch):
    issues = [
        {
            "severity": "error",
            "category": "test-finding",
            "message": "finding",
            "file": "test.txt",
            "line": 1,
        }
    ]
    monkeypatch.setattr(runner, "launch_validator", _launcher_with(issues))
    persist_dir = tmp_path / "persisted"

    code = _run_stub(tmp_path, _args("both", persist_results=str(persist_dir)))

    assert code == 0
    try:
        payload = json.loads((persist_dir / "stub.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AssertionError("persisted sidecar is missing or invalid") from exc
    assert payload == issues
    assert (persist_dir / runner.PERSISTENCE_MARKER).read_text(encoding="utf-8") == (
        "complete\n"
    )


def test_persist_results_writes_completion_marker_when_clean(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "launch_validator", _launcher_with([]))
    persist_dir = tmp_path / "persisted"
    persist_dir.mkdir()
    (persist_dir / "stale.json").write_text("[]", encoding="utf-8")

    code = _run_stub(tmp_path, _args("both", persist_results=str(persist_dir)))

    assert code == 0
    assert list(persist_dir.glob("*.json")) == []
    assert (persist_dir / runner.PERSISTENCE_MARKER).read_text(encoding="utf-8") == (
        "complete\n"
    )


def test_persist_results_copy_failure_propagates(tmp_path, monkeypatch):
    # A copy failure must fail the run, never silently save a truncated
    # baseline under a valid-looking meta.
    issues = [
        {
            "severity": "error",
            "category": "test-finding",
            "message": "finding",
            "file": "test.txt",
            "line": 1,
        }
    ]
    monkeypatch.setattr(runner, "launch_validator", _launcher_with(issues))

    def broken_copy(_src, _dst):
        raise OSError("disk full")

    monkeypatch.setattr(runner.shutil, "copyfile", broken_copy)
    persist_dir = tmp_path / "persisted"

    with pytest.raises(OSError, match="disk full"):
        _run_stub(tmp_path, _args("both", persist_results=str(persist_dir)))


def test_crashed_validator_fails_run_without_strict(tmp_path, monkeypatch, capsys):
    # A validator that exits non-zero with no findings crashed. That is
    # infrastructure failure and must fail the run even when --strict is off.
    monkeypatch.setattr(runner, "launch_validator", _launcher_with([], returncode=2))

    code = _run_stub(tmp_path, _args("both", strict=False))

    captured = capsys.readouterr()
    assert code == 1
    assert "crashed" in (captured.out + captured.err)


def test_clean_run_passes_without_strict(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "launch_validator", _launcher_with([], returncode=0))

    code = _run_stub(tmp_path, _args("both", strict=False))

    assert code == 0


def test_findings_without_strict_do_not_fail(tmp_path, monkeypatch):
    # Ordinary findings (validator exits 0, reports errors) stay advisory in
    # non-strict mode — only crashes and --strict escalate to a non-zero exit.
    issues = [
        {
            "severity": "error",
            "category": "test-finding",
            "message": "finding",
            "file": "test.txt",
            "line": 1,
        }
    ]
    monkeypatch.setattr(
        runner, "launch_validator", _launcher_with(issues, returncode=0)
    )

    code = _run_stub(tmp_path, _args("both", strict=False))

    assert code == 0


def test_both_without_output_prints_json_and_human_report(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(runner, "launch_validator", _launcher_with([]))

    code = _run_stub(tmp_path, _args("both"))

    stdout = capsys.readouterr().out
    assert code == 0
    assert '"total_errors": 0' in stdout
    assert "COMBINED VALIDATION REPORT" in stdout
    assert "ALL VALIDATIONS PASSED" in stdout
