"""CLI contract tests for `generate_validation_report` — the production
entry point the workflow invokes. Covers the baseline flag wiring that the
unit tests of `build_report` cannot see (argparse → load_baseline →
build_report)."""

import json
import runpy
import sys

import generate_validation_report
import pytest
from report_lib import truncation
from report_lib.baseline import META_FILENAME
from shared.paths import TOOLS_DIR
from shared.suite import issue_dict as _issue_dict
from shared.suite import make_results_tree


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


def _post_argv(tmp_path, *extra):
    argv = _argv(tmp_path)
    argv += [
        "--pr-number",
        "42",
        "--github-token",
        "token",
        "--post-comment",
    ]
    argv += list(extra)
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
    assert "1 new error against the main baseline." in report
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


def _findings_tree(tmp_path):
    return make_results_tree(
        tmp_path,
        {
            "events": {
                "log": "VALIDATION COMPLETE",
                "issues": [_issue_dict("error", file="new.txt", message="finding")],
            }
        },
    )


def _passing_tree(tmp_path):
    return make_results_tree(
        tmp_path,
        {"events": {"log": "✓ VALIDATION COMPLETE"}},
    )


def _warnings_tree(tmp_path):
    return make_results_tree(
        tmp_path,
        {
            "events": {
                "log": "VALIDATION COMPLETE",
                "issues": [_issue_dict("warning", message="warning")],
            }
        },
    )


def _comment_spies(monkeypatch):
    posted = []
    cleared = []
    monkeypatch.setattr(
        generate_validation_report,
        "post_comment",
        lambda *args: posted.append(args) or (True, "posted"),
    )
    monkeypatch.setattr(
        generate_validation_report,
        "clear_comment",
        lambda *args: cleared.append(args) or (True, "cleared"),
    )
    return posted, cleared


def test_main_posts_comment_for_new_findings(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    _findings_tree(tmp_path)
    posted, cleared = _comment_spies(monkeypatch)

    code = generate_validation_report.main(_post_argv(tmp_path))

    assert code == 0
    assert len(posted) == 1
    assert posted[0][2] == "42"
    assert not cleared


def test_main_posts_comment_for_warnings(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    _warnings_tree(tmp_path)
    posted, cleared = _comment_spies(monkeypatch)

    code = generate_validation_report.main(_post_argv(tmp_path))

    assert code == 0
    assert len(posted) == 1
    assert not cleared


def test_main_clears_comment_on_clean_partial_run(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    _passing_tree(tmp_path)
    posted, cleared = _comment_spies(monkeypatch)

    code = generate_validation_report.main(_post_argv(tmp_path))

    assert code == 0
    assert not posted
    assert len(cleared) == 1


def test_main_clears_comment_on_clean_full_run(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    _passing_tree(tmp_path)
    posted, cleared = _comment_spies(monkeypatch)

    code = generate_validation_report.main(
        _post_argv(tmp_path, "--validation-scope", "full")
    )

    assert code == 0
    assert not posted
    assert cleared == [("MillenniumDawn", "Millennium-Dawn", "42", "token")]


def test_main_posts_comment_for_unknown_run(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    make_results_tree(tmp_path, {"events": {"log": "validator started"}})
    posted, cleared = _comment_spies(monkeypatch)

    code = generate_validation_report.main(_post_argv(tmp_path))

    assert code == 0
    assert len(posted) == 1
    assert "did not produce a complete result" in posted[0][3]
    assert not cleared


def test_main_posts_comment_when_no_validator_ran(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    (tmp_path / "validation-results").mkdir()
    posted, cleared = _comment_spies(monkeypatch)

    code = generate_validation_report.main(_post_argv(tmp_path))

    assert code == 0
    assert len(posted) == 1
    assert "_No validator results found._" in posted[0][3]
    assert not cleared


def test_main_checks_api_failure_is_non_fatal(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    _findings_tree(tmp_path)
    calls = []

    def fake_checks(owner, repo, commit_sha, runs, token):
        calls.append((commit_sha, token))
        return [("Events", False, "boom")]

    monkeypatch.setattr(generate_validation_report, "post_checks", fake_checks)

    code = generate_validation_report.main(
        _argv(tmp_path)
        + [
            "--checks-api",
            "--github-token",
            "token",
        ]
    )

    assert code == 0
    assert calls == [("abc1234deadbeef", "token")]  # pragma: allowlist secret


def test_main_post_comment_requires_repository(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    # GITHUB_REPOSITORY/GITHUB_TOKEN are always set in Actions; without this
    # the env fallback would bypass the guard and hit the real API.
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    def never_call(*_args, **_kwargs):
        raise AssertionError("API must not be called when the repository guard fails")

    monkeypatch.setattr(generate_validation_report, "post_comment", never_call)

    _findings_tree(tmp_path)
    argv = _post_argv(tmp_path)
    # Drop --github-repository (and its value): the flag must be rejected
    # before any API call is attempted.
    idx = argv.index("--github-repository")
    argv = argv[:idx] + argv[idx + 2 :]

    code = generate_validation_report.main(argv)

    assert code == 1


def test_main_fails_when_the_report_cannot_be_written(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    _findings_tree(tmp_path)
    blocked = tmp_path / "blocked"
    blocked.mkdir()
    argv = _argv(tmp_path)
    argv[argv.index("--output") + 1] = str(blocked)

    code = generate_validation_report.main(argv)

    assert code == 1
    assert "Error writing report:" in capsys.readouterr().err


def test_main_reports_a_truncated_body(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    monkeypatch.setattr(truncation, "MAX_COMMENT_BYTES", 200)
    _findings_tree(tmp_path)

    code = generate_validation_report.main(_argv(tmp_path))

    assert code == 0
    err = capsys.readouterr().err
    assert "was truncated" in err
    report = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "This report was too large" in report


def test_main_writes_the_step_summary_when_ci_sets_the_path(
    tmp_path, monkeypatch, capsys
):
    summary = tmp_path / "step-summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    _findings_tree(tmp_path)

    code = generate_validation_report.main(_argv(tmp_path) + ["--print"])

    assert code == 0
    assert "Step summary written." in capsys.readouterr().err
    step_body = summary.read_text(encoding="utf-8")
    # The step summary carries the per-validator detail the comment drops.
    assert "## Validators" in step_body
    assert "## Validators" not in (tmp_path / "report.md").read_text(encoding="utf-8")


def test_main_survives_an_unwritable_step_summary(tmp_path, monkeypatch, capsys):
    unwritable = tmp_path / "summary-dir"
    unwritable.mkdir()
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(unwritable))
    _findings_tree(tmp_path)

    code = generate_validation_report.main(_argv(tmp_path))

    assert code == 0
    assert "Warning: could not write step summary:" in capsys.readouterr().err


def test_main_prints_the_body_when_asked(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    _findings_tree(tmp_path)

    code = generate_validation_report.main(_argv(tmp_path) + ["--print"])

    assert code == 0
    assert "# Validation Report" in capsys.readouterr().out


def test_main_api_call_requires_a_token(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr(
        generate_validation_report,
        "post_comment",
        lambda *a: (_ for _ in ()).throw(AssertionError("API must not be called")),
    )
    _findings_tree(tmp_path)
    argv = _post_argv(tmp_path)
    idx = argv.index("--github-token")

    code = generate_validation_report.main(argv[:idx] + argv[idx + 2 :])

    assert code == 1
    assert "--github-token" in capsys.readouterr().err


def test_main_rejects_a_repository_without_an_owner(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    monkeypatch.setattr(
        generate_validation_report,
        "post_comment",
        lambda *a: (_ for _ in ()).throw(AssertionError("API must not be called")),
    )
    _findings_tree(tmp_path)
    argv = _post_argv(tmp_path)
    argv[argv.index("--github-repository") + 1] = "no-slash-here"

    code = generate_validation_report.main(argv)

    assert code == 1
    assert "must be owner/repo" in capsys.readouterr().err


def test_main_continues_when_the_comment_cannot_be_posted(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    monkeypatch.setattr(
        generate_validation_report,
        "post_comment",
        lambda *a: (False, "HTTP 403 — read-only token"),
    )
    _findings_tree(tmp_path)

    code = generate_validation_report.main(_post_argv(tmp_path))

    assert code == 0
    err = capsys.readouterr().err
    assert "PR comment: HTTP 403 — read-only token" in err
    assert "PR comment could not be synchronized; continuing." in err


def test_main_checks_api_requires_a_commit_sha(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    monkeypatch.setattr(
        generate_validation_report,
        "post_checks",
        lambda *a: (_ for _ in ()).throw(AssertionError("API must not be called")),
    )
    _findings_tree(tmp_path)
    argv = _argv(tmp_path)
    idx = argv.index("--commit-sha")

    code = generate_validation_report.main(
        argv[:idx] + argv[idx + 2 :] + ["--checks-api", "--github-token", "token"]
    )

    assert code == 1
    assert "--commit-sha is required" in capsys.readouterr().err


def test_main_reports_each_check_run_result(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    monkeypatch.setattr(
        generate_validation_report,
        "post_checks",
        lambda *a: [("Events", False, "boom"), ("Ideas", True, "check #2")],
    )
    _findings_tree(tmp_path)

    code = generate_validation_report.main(
        _argv(tmp_path) + ["--checks-api", "--github-token", "token"]
    )

    assert code == 0
    err = capsys.readouterr().err
    assert "✗ Check Run 'Events': boom" in err
    assert "✓ Check Run 'Ideas': check #2" in err
    assert "Some Check Runs failed to post" in err


def test_main_stays_quiet_when_every_check_run_posts(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    monkeypatch.setattr(
        generate_validation_report,
        "post_checks",
        lambda *a: [("Events", True, "check #1")],
    )
    _findings_tree(tmp_path)

    code = generate_validation_report.main(
        _argv(tmp_path) + ["--checks-api", "--github-token", "token"]
    )

    assert code == 0
    assert "Some Check Runs failed to post" not in capsys.readouterr().err


def test_script_entry_point_rejects_a_missing_results_dir(monkeypatch):
    """Running the file directly must bootstrap tools/ onto sys.path itself."""
    script = str(TOOLS_DIR / "generate_validation_report.py")
    monkeypatch.setattr(sys, "path", [p for p in sys.path if p != str(TOOLS_DIR)])
    monkeypatch.setattr(sys, "argv", ["generate_validation_report.py"])

    with pytest.raises(SystemExit) as exit_info:
        runpy.run_path(script, run_name="__main__")

    assert exit_info.value.code == 2


def test_main_post_comment_requires_pr_number(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    def never_call(*_args, **_kwargs):
        raise AssertionError("API must not be called when the pr-number guard fails")

    monkeypatch.setattr(generate_validation_report, "post_comment", never_call)

    _findings_tree(tmp_path)
    argv = _post_argv(tmp_path)
    idx = argv.index("--pr-number")
    argv = argv[:idx] + argv[idx + 2 :]

    code = generate_validation_report.main(argv)

    assert code == 1
