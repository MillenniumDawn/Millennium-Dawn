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


def test_main_posts_comment_for_new_findings(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    _findings_tree(tmp_path)
    calls = []

    def fake_post(owner, repo, pr_number, body, token, update_only):
        calls.append(
            {
                "owner": owner,
                "repo": repo,
                "pr_number": pr_number,
                "body": body,
                "token": token,
                "update_only": update_only,
            }
        )
        return True, "posted"

    monkeypatch.setattr(generate_validation_report, "post_comment", fake_post)

    code = generate_validation_report.main(_post_argv(tmp_path))

    assert code == 0
    assert len(calls) == 1
    assert calls[0]["update_only"] is False
    assert calls[0]["pr_number"] == "42"


def test_main_updates_existing_comment_on_clean_partial_run(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    _passing_tree(tmp_path)
    calls = []

    def fake_post(owner, repo, pr_number, body, token, update_only):
        calls.append(update_only)
        return True, "posted"

    def fake_delete(*_args, **_kwargs):
        raise AssertionError("delete_comment must not be called on a clean partial run")

    monkeypatch.setattr(generate_validation_report, "post_comment", fake_post)
    monkeypatch.setattr(generate_validation_report, "delete_comment", fake_delete)

    code = generate_validation_report.main(_post_argv(tmp_path))

    assert code == 0
    # A clean partial run refreshes the existing comment but never opens a
    # new one (it cannot clear findings an unrun validator would report).
    assert calls == [True]


def test_main_deletes_comment_on_full_clean_run(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    _passing_tree(tmp_path)
    calls = []

    def fake_delete(owner, repo, pr_number, token):
        calls.append((owner, repo, pr_number, token))
        return True, "deleted"

    def fake_post(*args, **kwargs):
        raise AssertionError("post_comment must not be called on a full clean run")

    monkeypatch.setattr(generate_validation_report, "delete_comment", fake_delete)
    monkeypatch.setattr(generate_validation_report, "post_comment", fake_post)

    code = generate_validation_report.main(
        _post_argv(tmp_path, "--validation-scope", "full")
    )

    assert code == 0
    assert calls == [("MillenniumDawn", "Millennium-Dawn", "42", "token")]


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
    assert calls == [("abc1234deadbeef", "token")]


def test_main_post_comment_requires_repository(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    # GITHUB_REPOSITORY/GITHUB_TOKEN are always set in Actions; without this
    # the env fallback would bypass the guard and hit the real API.
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    def never_call(*_args, **_kwargs):
        raise AssertionError("API must not be called when the repository guard fails")

    monkeypatch.setattr(generate_validation_report, "post_comment", never_call)
    monkeypatch.setattr(generate_validation_report, "delete_comment", never_call)

    _findings_tree(tmp_path)
    argv = _post_argv(tmp_path)
    # Drop --github-repository (and its value): the flag must be rejected
    # before any API call is attempted.
    idx = argv.index("--github-repository")
    argv = argv[:idx] + argv[idx + 2 :]

    code = generate_validation_report.main(argv)

    assert code == 1


def test_main_post_comment_requires_pr_number(tmp_path, monkeypatch):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    def never_call(*_args, **_kwargs):
        raise AssertionError("API must not be called when the pr-number guard fails")

    monkeypatch.setattr(generate_validation_report, "post_comment", never_call)
    monkeypatch.setattr(generate_validation_report, "delete_comment", never_call)

    _findings_tree(tmp_path)
    argv = _post_argv(tmp_path)
    idx = argv.index("--pr-number")
    argv = argv[:idx] + argv[idx + 2 :]

    code = generate_validation_report.main(argv)

    assert code == 1
