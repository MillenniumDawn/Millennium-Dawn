"""Tests for `report_lib.truncation`."""

from report_lib import MAX_COMMENT_BYTES, truncate_if_needed


def _body_with_summary(issues_section_size: int) -> str:
    head = "<!-- md-validation-report:v1 -->\n# Validation Report\n\n"
    summary = (
        "## Summary\n\n"
        "| Validator | Errors | Warnings | Status |\n"
        "|-----------|-------:|---------:|:------:|\n"
        "| Events | 1 | 0 | ✗ Fail |\n"
        "| **Total** | **1** | **0** |  |\n\n"
    )
    issues = "## Issues by file\n\n" + ("x" * issues_section_size) + "\n"
    return head + summary + issues


def test_short_body_not_truncated():
    body = _body_with_summary(500)
    out, truncated = truncate_if_needed(body)
    assert out == body
    assert truncated is False


def test_long_body_keeps_summary_and_drops_issues():
    big = _body_with_summary(MAX_COMMENT_BYTES + 10_000)
    out, truncated = truncate_if_needed(
        big, artifact_url="https://example.test/artifact"
    )
    assert truncated is True
    assert len(out.encode("utf-8")) < MAX_COMMENT_BYTES + 5_000
    # Summary table must still be there
    assert "| **Total** |" in out
    # But the giant issues section is gone
    assert "## Issues by file" not in out
    # And a visible notice with the artifact link is present
    assert "This report was too large" in out
    assert "https://example.test/artifact" in out


def test_truncation_uses_workflow_url_when_no_artifact():
    big = _body_with_summary(MAX_COMMENT_BYTES + 10_000)
    out, truncated = truncate_if_needed(
        big, workflow_run_url="https://example.test/run/1"
    )
    assert truncated is True
    assert "https://example.test/run/1" in out
