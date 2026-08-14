"""CLI contract tests for `generate_validation_report` — the production
entry point the workflow invokes. Covers the baseline flag wiring that the
unit tests of `build_report` cannot see (argparse → load_baseline →
build_report)."""

import json

import generate_validation_report

from report_lib.baseline import META_FILENAME

from .conftest import make_results_tree


def _issue_dict(severity, file="a.txt", line=1, message="m", category="c"):
    return {
        "severity": severity,
        "category": category,
        "message": message,
        "file": file,
        "line": line,
    }


def _write_baseline(base, toolshash, issues):
    base.mkdir(parents=True, exist_ok=True)
    (base / META_FILENAME).write_text(
        json.dumps({"toolshash": toolshash}), encoding="utf-8"
    )
    (base / "events.json").write_text(json.dumps(issues), encoding="utf-8")


def _argv(tmp_path, baseline_dir=None, baseline_toolshash=None):
    argv = [
        "--results-dir",
        str(tmp_path / "validation-results"),
        "--output",
        str(tmp_path / "report.md"),
        "--commit-sha",
        "abc1234deadbeef",  # pragma: allowlist secret
        "--validation-scope",
        "partial",
        "--github-repository",
        "MillenniumDawn/Millennium-Dawn",
    ]
    if baseline_dir is not None:
        argv += ["--baseline-dir", str(baseline_dir)]
    if baseline_toolshash is not None:
        argv += ["--baseline-toolshash", baseline_toolshash]
    return argv


def test_main_annotates_new_vs_existing_from_baseline(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    make_results_tree(
        tmp_path,
        {
            "events": {
                "log": "VALIDATION COMPLETE",
                "issues": [
                    _issue_dict("error", file="old.txt", message="old finding"),
                    _issue_dict("error", file="new.txt", message="new finding"),
                ],
            }
        },
    )
    _write_baseline(
        tmp_path / "baseline",
        "h",
        [_issue_dict("error", file="old.txt", message="old finding")],
    )

    code = generate_validation_report.main(
        _argv(tmp_path, baseline_dir=tmp_path / "baseline", baseline_toolshash="h")
    )

    assert code == 0
    report = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "1 new against the main baseline." in report
    err = capsys.readouterr().err
    assert "vs main baseline: 1 new error(s), 0 new warning(s)" in err


def test_main_ignores_stale_baseline(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    make_results_tree(
        tmp_path,
        {
            "events": {
                "log": "VALIDATION COMPLETE",
                "issues": [_issue_dict("error", file="new.txt", message="finding")],
            }
        },
    )
    _write_baseline(
        tmp_path / "baseline",
        "old-generation",
        [_issue_dict("error", file="old.txt", message="old finding")],
    )

    code = generate_validation_report.main(
        _argv(
            tmp_path,
            baseline_dir=tmp_path / "baseline",
            baseline_toolshash="new-generation",
        )
    )

    assert code == 0
    report = (tmp_path / "report.md").read_text(encoding="utf-8")
    # A baseline from a different validator generation must be ignored, not
    # compared: no NEW/EXISTING annotation anywhere.
    assert "main baseline" not in report


def test_main_renders_without_baseline_when_dir_missing(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    make_results_tree(
        tmp_path,
        {
            "events": {
                "log": "VALIDATION COMPLETE",
                "issues": [_issue_dict("error", file="new.txt", message="finding")],
            }
        },
    )

    code = generate_validation_report.main(
        _argv(tmp_path, baseline_dir=tmp_path / "no-such-baseline")
    )

    assert code == 0
    report = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "1 error must be fixed before merge." in report
    assert "main baseline" not in report
