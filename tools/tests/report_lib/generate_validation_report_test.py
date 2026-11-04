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

BASE_SHA = "0123456789abcdef"  # pragma: allowlist secret


def _write_baseline(base, toolshash, issues, run_id=""):
    base.mkdir(parents=True, exist_ok=True)
    meta = {
        "toolshash": toolshash,
        "commit_sha": BASE_SHA,
        "run_id": run_id,
        "sidecars": ["events.json"],
    }
    (base / META_FILENAME).write_text(json.dumps(meta), encoding="utf-8")
    (base / "events.json").write_text(json.dumps(issues), encoding="utf-8")


def _old_and_new_tree(tmp_path, toolshash="h", run_id=""):
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
        toolshash,
        [_issue_dict("error", file="old.txt", message="old finding")],
        run_id,
    )


def _argv(tmp_path, baseline_dir=None, baseline_toolshash=None, baseline_commit=None):
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
    if baseline_commit is not None:
        argv += ["--baseline-commit", baseline_commit]
    return argv


def _report_with_changed_files(tmp_path, changed_files):
    changed = tmp_path / "changed-files.txt"
    changed.write_text("".join(f"{name}\n" for name in changed_files), encoding="utf-8")

    code = generate_validation_report.main(
        _argv(tmp_path, baseline_dir=tmp_path / "baseline", baseline_toolshash="h")
        + ["--changed-files", str(changed)]
    )

    assert code == 0
    return (tmp_path / "report.md").read_text(encoding="utf-8")


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


@pytest.mark.parametrize(
    ("run_id", "source"),
    [
        pytest.param("", "", id="main's run"),
        pytest.param("7", " (scanned in this run)", id="this run's base scan"),
    ],
)
def test_main_annotates_new_vs_existing_from_baseline(
    tmp_path, monkeypatch, capsys, run_id, source
):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    monkeypatch.setenv("GITHUB_RUN_ID", "7")
    _old_and_new_tree(tmp_path, run_id=run_id)

    code = generate_validation_report.main(
        _argv(
            tmp_path,
            baseline_dir=tmp_path / "baseline",
            baseline_toolshash="h",
            baseline_commit=BASE_SHA,
        )
    )

    assert code == 0
    report = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "1 new error against the main baseline" in report
    assert f"**Baseline comparison:** main `0123456`{source}\n" in report
    err = capsys.readouterr().err
    assert "vs main baseline: 1 new error(s), 0 new warning(s)" in err


def test_main_reports_what_changed_validators_do_to_main(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    _old_and_new_tree(tmp_path)
    _write_baseline(tmp_path / "main-tools", "main-hash", [])

    code = generate_validation_report.main(
        _argv(
            tmp_path,
            baseline_dir=tmp_path / "baseline",
            baseline_toolshash="h",
            baseline_commit=BASE_SHA,
        )
        + ["--tooling-changed", "--main-tools-baseline", str(tmp_path / "main-tools")]
    )

    assert code == 0
    report = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "that code adds/drops: `c` +1/-0." in report


def test_main_moves_main_findings_to_renamed_files(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    make_results_tree(
        tmp_path,
        {
            "events": {
                "log": "VALIDATION COMPLETE",
                "issues": [_issue_dict("error", file="moved.txt", message="finding")],
            }
        },
    )
    _write_baseline(
        tmp_path / "baseline",
        "h",
        [_issue_dict("error", file="old.txt", message="finding")],
    )
    renames = tmp_path / "renames.txt"
    renames.write_text("old.txt\nmoved.txt\n", encoding="utf-8")

    code = generate_validation_report.main(
        _argv(tmp_path, baseline_dir=tmp_path / "baseline", baseline_toolshash="h")
        + ["--renames", str(renames)]
    )

    assert code == 0
    report = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "No new errors against the main baseline" in report


@pytest.mark.parametrize(
    ("hunks", "verdict"),
    [
        pytest.param("", "No new errors", id="no edit"),
        pytest.param("@@ -1,0 +2,2 @@\n", "1 new error", id="main's copy moved down"),
    ],
)
def test_main_places_main_findings_through_the_hunks(
    tmp_path, monkeypatch, hunks, verdict
):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    finding = _issue_dict("error", file="events/a.txt", line=10, message="finding")
    make_results_tree(
        tmp_path, {"events": {"log": "VALIDATION COMPLETE", "issues": [finding]}}
    )
    _write_baseline(tmp_path / "baseline", "h", [finding])
    hunks_file = tmp_path / "hunks.txt"
    hunks_file.write_text(
        "diff --git a/events/a.txt b/events/a.txt\n+++ b/events/a.txt\n" + hunks,
        encoding="utf-8",
    )

    code = generate_validation_report.main(
        _argv(tmp_path, baseline_dir=tmp_path / "baseline", baseline_toolshash="h")
        + ["--hunks", str(hunks_file)]
    )

    assert code == 0
    report = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert f"{verdict} against the main baseline" in report


@pytest.mark.parametrize(
    ("toolshash", "commit"),
    [
        pytest.param("new-generation", BASE_SHA, id="other validator code"),
        pytest.param(
            "h",
            "fedcba9876543210",  # pragma: allowlist secret
            id="other main commit",
        ),
    ],
)
def test_main_ignores_stale_baseline(tmp_path, monkeypatch, toolshash, commit):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    _findings_tree(tmp_path)
    _write_baseline(
        tmp_path / "baseline",
        "h",
        [_issue_dict("error", file="old.txt", message="old finding")],
    )

    code = generate_validation_report.main(
        _argv(
            tmp_path,
            baseline_dir=tmp_path / "baseline",
            baseline_toolshash=toolshash,
            baseline_commit=commit,
        )
    )

    assert code == 0
    report = (tmp_path / "report.md").read_text(encoding="utf-8")
    # A baseline from different validator code or another main commit must be
    # ignored, not compared: no NEW/EXISTING annotation anywhere.
    assert "main baseline" not in report
    assert "**Baseline comparison:** unavailable" in report
    assert f"no complete baseline of main `{commit[:7]}`" in report


def test_main_renders_without_baseline_when_dir_missing(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    _findings_tree(tmp_path)

    code = generate_validation_report.main(
        _argv(tmp_path, baseline_dir=tmp_path / "no-such-baseline")
    )

    assert code == 0
    report = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "1 error must be fixed before merge." in report
    assert "main baseline" not in report
    assert "**Baseline comparison:** unavailable" in report


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


def _write_tools_sidecar(tmp_path, os_name="Linux", **overrides):
    directory = tmp_path / "validation-results" / f"tools-tests-{os_name}-results"
    directory.mkdir(parents=True, exist_ok=True)
    sidecar = {
        "suite": "tools",
        "job": f"Tools tests ({os_name})",
        "name": f"tools-{os_name.lower()}",
        "title": f"Tools tests ({os_name})",
        "status": "passed",
        "errors": 0,
        "warnings": 0,
        "issues": [],
    }
    sidecar.update(overrides)
    (directory / "suite-run.json").write_text(json.dumps(sidecar), encoding="utf-8")


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


@pytest.mark.parametrize(
    ("specs", "skipped", "posts"),
    [
        pytest.param({}, False, True, id="missing results"),
        pytest.param({}, True, False, id="no tests selected"),
        pytest.param(
            {"events": {"log": "validator started"}},
            True,
            True,
            id="incomplete result is not hidden",
        ),
        pytest.param(
            {"events": {"issues": [_issue_dict("warning", message="warning")]}},
            True,
            True,
            id="findings are not hidden",
        ),
    ],
)
def test_main_handles_empty_validation(tmp_path, monkeypatch, specs, skipped, posts):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    monkeypatch.setenv("GITHUB_RUN_ID", "7")
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "2")
    make_results_tree(tmp_path, specs)
    posted, cleared = _comment_spies(monkeypatch)
    extra = ["--comment-output", str(tmp_path / "comment.json")]
    if skipped:
        extra.append("--no-tests-selected")

    code = generate_validation_report.main(_post_argv(tmp_path, *extra))

    assert code == 0
    assert len(posted) == int(posts)
    assert len(cleared) == int(not posts)
    if not specs and posts:
        assert "_No validator results found._" in posted[0][3]
    payload = json.loads((tmp_path / "comment.json").read_text(encoding="utf-8"))
    assert payload == {
        "pr_number": "42",
        "commit_sha": "abc1234deadbeef",  # pragma: allowlist secret
        "run_id": "7",
        "run_attempt": "2",
        "should_post": posts,
        "body": (tmp_path / "report.md").read_text(encoding="utf-8"),
    }


def test_main_writes_comment_payload_without_api_credentials(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    _findings_tree(tmp_path)
    posted, cleared = _comment_spies(monkeypatch)

    code = generate_validation_report.main(
        _argv(tmp_path) + ["--comment-output", str(tmp_path / "comment.json")]
    )

    assert code == 0
    assert (tmp_path / "comment.json").is_file()
    assert not posted and not cleared


def test_main_hands_tools_suite_runs_to_the_checks_api(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    _findings_tree(tmp_path)
    _write_tools_sidecar(tmp_path)
    seen = []
    monkeypatch.setattr(
        generate_validation_report,
        "post_checks",
        lambda _owner, _repo, _sha, runs, _token: seen.extend(runs) or [],
    )

    code = generate_validation_report.main(
        _argv(tmp_path) + ["--checks-api", "--github-token", "token"]
    )

    assert code == 0
    by_name = {run.name: run for run in seen}
    assert by_name["tools-linux"].suite == "tools"
    assert by_name["tools-linux"].job == "Tools tests (Linux)"
    assert by_name["events"].suite == "mod"
    assert by_name["events"].job == ""


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


@pytest.mark.parametrize("output", ["--output", "--comment-output"])
def test_main_fails_when_the_report_cannot_be_written(
    tmp_path, monkeypatch, capsys, output
):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    _findings_tree(tmp_path)
    blocked = tmp_path / "blocked"
    blocked.mkdir()
    argv = _argv(tmp_path)
    argv += [output, str(blocked)]

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


def test_main_step_summary_collapses_a_clean_tools_suite(tmp_path, monkeypatch):
    summary = tmp_path / "step-summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    _passing_tree(tmp_path)
    _write_tools_sidecar(tmp_path)

    code = generate_validation_report.main(_argv(tmp_path))

    assert code == 0
    step_body = summary.read_text(encoding="utf-8")
    assert "## Tools tests\n\n✅ All tools based tests have succeeded!" in step_body
    assert "| Tool suite |" not in step_body


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
    assert "# Test Suite Report" in capsys.readouterr().out


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


def test_main_tags_changed_files(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    _findings_tree(tmp_path)
    changed = tmp_path / "changed-files.txt"
    changed.write_text("new.txt\n", encoding="utf-8")

    code = generate_validation_report.main(
        _argv(tmp_path) + ["--changed-files", str(changed)]
    )

    assert code == 0
    report = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "**IN YOUR PR**" in report
    assert "## Findings in your PR" in report
    assert "**Changed files:** available" in report
    assert "tagged 1 finding(s) IN YOUR PR" in capsys.readouterr().err


def test_main_changed_files_missing_sets_unavailable(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    _findings_tree(tmp_path)

    code = generate_validation_report.main(
        _argv(tmp_path) + ["--changed-files", str(tmp_path / "missing.txt")]
    )

    assert code == 0
    report = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "Changed-file list was not available" in report
    assert "**IN YOUR PR**" not in report
    assert "changed-file list unavailable" in capsys.readouterr().err


def test_main_changed_files_and_baseline_tag_both(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    _old_and_new_tree(tmp_path)

    report = _report_with_changed_files(tmp_path, ["new.txt"])

    assert "**NEW** **IN YOUR PR**" in report
    assert "## New Findings Introduced by this branch." in report


def test_main_surfaces_existing_findings_in_touched_files(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    _old_and_new_tree(tmp_path)

    report = _report_with_changed_files(tmp_path, ["old.txt", "new.txt"])

    assert "## New Findings Introduced by this branch." in report
    in_pr = report[report.index("## Findings in your PR") :]
    assert "old finding" in in_pr
    assert "new finding" not in in_pr
