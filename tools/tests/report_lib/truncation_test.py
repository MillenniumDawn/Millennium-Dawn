"""Tests for `report_lib.truncation`."""

from report_lib import MAX_COMMENT_BYTES, truncate_if_needed

_TABLES = (
    "## Findings by category\n\n"
    "| Category | Errors | Warnings |\n"
    "|----------|-------:|---------:|\n"
    "| Event Picture Format Mismatch | 0 | 211 |\n\n"
    "_…and 5 more categories._\n\n"
    "## Mod tests\n\n"
    "| Validator | Errors | Warnings |\n"
    "|-----------|-------:|---------:|\n"
    "| Events | 1 | 0 |\n"
    "| **Total** | **1** | **0** |\n\n"
    "## Tools tests\n\n"
    "| Tool suite | Errors | Warnings |\n"
    "| Linux | 1 | 0 |\n"
)


def _body(findings_size: int, findings_body: str = "") -> str:
    head = "<!-- md-validation-report:v1 -->\n# Test Suite Report\n\n"
    findings = "## New Findings Introduced by this branch.\n\n"
    findings += findings_body or (("x" * findings_size) + "\n")
    return head + findings + "\n" + _TABLES


def test_short_body_not_truncated():
    body = _body(500)
    out, truncated = truncate_if_needed(body)
    assert out == body
    assert truncated is False


def test_long_body_keeps_tables_and_trims_findings():
    big = _body(MAX_COMMENT_BYTES + 10_000)
    out, truncated = truncate_if_needed(
        big, artifact_url="https://example.test/artifact"
    )
    assert truncated is True
    assert len(out.encode("utf-8")) <= MAX_COMMENT_BYTES
    assert out.startswith("<!-- md-validation-report:v1 -->")
    assert "## New Findings Introduced by this branch." in out
    assert "| Event Picture Format Mismatch | 0 | 211 |" in out
    assert "_…and 5 more categories._" in out
    assert "| **Total** | **1** | **0** |" in out
    assert "| Linux | 1 | 0 |" in out
    assert "This report was too large" in out
    assert "https://example.test/artifact" in out


def test_truncation_uses_workflow_url_when_no_artifact():
    big = _body(MAX_COMMENT_BYTES + 10_000)
    out, truncated = truncate_if_needed(
        big, workflow_run_url="https://example.test/run/1"
    )
    assert truncated is True
    assert "https://example.test/run/1" in out


def test_truncation_closes_an_orphaned_details_block():
    findings = (
        "<details open>\n"
        "<summary>❌ New errors (9000)</summary>\n\n"
        + ("- `events/MD_x.txt:1` — key FOO not found\n" * 4_000)
        + "\n</details>\n"
    )
    out, truncated = truncate_if_needed(_body(0, findings))
    assert truncated is True
    assert out.count("<details") == out.count("</details>")
    # The tail survives past the closed block.
    assert "## Tools tests" in out


def test_truncation_falls_back_to_a_byte_slice_without_tables():
    body = "# Test Suite Report\n\n" + ("x" * (MAX_COMMENT_BYTES + 10_000))
    out, truncated = truncate_if_needed(body)
    assert truncated is True
    assert len(out.encode("utf-8")) < MAX_COMMENT_BYTES
    assert out.startswith("# Test Suite Report")
    assert "This report was too large" in out
    assert "available in the step summary." in out


def test_truncation_falls_back_when_the_tables_alone_exceed_the_cap():
    body = (
        "# Test Suite Report\n\n"
        "## New Findings Introduced by this branch.\n\n"
        "- `events/MD_x.txt:1` — key FOO not found\n\n"
        "## Mod tests\n\n" + ("y" * (MAX_COMMENT_BYTES + 10_000)) + "\n"
    )
    out, truncated = truncate_if_needed(body, artifact_url="https://example.test/a")
    assert truncated is True
    assert len(out.encode("utf-8")) < MAX_COMMENT_BYTES
    assert out.startswith("# Test Suite Report")
    assert "This report was too large" in out
