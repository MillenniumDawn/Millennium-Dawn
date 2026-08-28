"""Regression tests for validation report comment behavior."""

from generate_validation_report import main


def _passing_tree(tmp_path):
    result_dir = tmp_path / "validation-results" / "validation-events-results"
    result_dir.mkdir(parents=True)
    with open(
        result_dir / "validation-events.log", "w", encoding="utf-8", newline=""
    ) as result_file:
        result_file.write("✓ VALIDATION COMPLETE\n")
    return tmp_path / "validation-results"


def _argv(tmp_path, scope):
    return [
        "--results-dir",
        str(tmp_path / "validation-results"),
        "--output",
        str(tmp_path / "report.md"),
        "--pr-number",
        "42",
        "--commit-sha",
        "test-head-sha",
        "--github-token",
        "token",
        "--github-repository",
        "MillenniumDawn/Millennium-Dawn",
        "--validation-scope",
        scope,
        "--post-comment",
    ]


def test_clean_runs_post_reports_for_every_scope(tmp_path, monkeypatch):
    _passing_tree(tmp_path)
    scopes = []

    def fake_post(owner, repo, pr_number, body, token):
        scopes.append(pr_number)
        return True, "posted"

    monkeypatch.setattr("generate_validation_report.post_comment", fake_post)

    for scope in ("partial", "full"):
        assert main(_argv(tmp_path, scope)) == 0

    assert scopes == ["42", "42"]


def test_run_without_validator_results_still_posts(tmp_path, monkeypatch):
    (tmp_path / "validation-results").mkdir()
    comments = []

    def fake_post(owner, repo, pr_number, body, token):
        comments.append(body)
        return True, "posted"

    monkeypatch.setattr("generate_validation_report.post_comment", fake_post)

    assert main(_argv(tmp_path, "partial")) == 0
    assert len(comments) == 1
    assert "_No validator results found._" in comments[0]
