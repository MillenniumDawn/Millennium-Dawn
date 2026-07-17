"""Output-contract tests for run_all_validators without content scans."""

import io
import json
from types import SimpleNamespace

import run_all_validators as runner


class _Process:
    def __init__(self, returncode=0):
        self.returncode = returncode

    def wait(self):
        return self.returncode


def _args(format_, output=None, strict=False):
    return SimpleNamespace(format=format_, output=output, strict=strict, no_color=True)


def _launcher_with(issues, returncode=0):
    def launch(_script, _flags, output_dir, name, _mod_path):
        try:
            with open(f"{output_dir}/{name}.json", "w", encoding="utf-8") as stream:
                json.dump(issues, stream)
        except OSError:
            raise
        return _Process(returncode), io.StringIO()

    return launch


def test_clean_both_writes_text_and_json_reports(tmp_path, monkeypatch):
    report_path = tmp_path / "report.txt"
    monkeypatch.setattr(runner, "launch_validator", _launcher_with([]))

    code = runner._run_suite(
        _args("both", str(report_path)),
        [],
        str(tmp_path),
        [("stub", "validate_stub.py", "Stub")],
        str(tmp_path),
    )

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

    code = runner._run_suite(
        _args("json", str(report_path)),
        [],
        str(tmp_path),
        [("stub", "validate_stub.py", "Stub")],
        str(tmp_path),
    )

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

    code = runner._run_suite(
        _args("both", str(report_path)),
        [],
        str(tmp_path),
        [("stub", "validate_stub.py", "Stub")],
        str(tmp_path),
    )

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

    code = runner._run_suite(
        _args("json", strict=True),
        [],
        str(tmp_path),
        [("stub", "validate_stub.py", "Stub")],
        str(tmp_path),
    )

    captured = capsys.readouterr()
    try:
        payload = json.loads(captured.out)
    except json.JSONDecodeError as exc:
        raise AssertionError("stdout is not valid JSON") from exc
    assert code == 1
    assert payload["total_errors"] == 1
    assert payload["issues"][0]["message"] == "broken café"
    assert "VALIDATION FAILED" in captured.err


def test_both_without_output_prints_json_and_human_report(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(runner, "launch_validator", _launcher_with([]))

    code = runner._run_suite(
        _args("both"),
        [],
        str(tmp_path),
        [("stub", "validate_stub.py", "Stub")],
        str(tmp_path),
    )

    stdout = capsys.readouterr().out
    assert code == 0
    assert '"total_errors": 0' in stdout
    assert "COMBINED VALIDATION REPORT" in stdout
    assert "ALL VALIDATIONS PASSED" in stdout
