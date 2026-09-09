"""Tests for `report_lib.truncation`."""

from report_lib import MAX_COMMENT_BYTES, truncate_if_needed


def _body_with_tables(issues_section_size: int) -> str:
    head = "<!-- md-validation-report:v1 -->\n# Test Suite Report\n\n"
    tables = (
        "## Mod tests\n\n"
        "| Validator | Errors | Warnings |\n"
        "|-----------|-------:|---------:|\n"
        "| Events | 1 | 0 |\n"
        "| **Total** | **1** | **0** |\n\n"
    )
    issues = "## New Findings Introduced by this branch.\n\n"
    issues += ("x" * issues_section_size) + "\n"
    return head + tables + issues


def test_short_body_not_truncated():
    body = _body_with_tables(500)
    out, truncated = truncate_if_needed(body)
    assert out == body
    assert truncated is False


def test_long_body_keeps_tables_and_drops_findings():
    big = _body_with_tables(MAX_COMMENT_BYTES + 10_000)
    out, truncated = truncate_if_needed(
        big, artifact_url="https://example.test/artifact"
    )
    assert truncated is True
    assert len(out.encode("utf-8")) < MAX_COMMENT_BYTES + 5_000
    assert "| **Total** |" in out
    assert "## New Findings Introduced by this branch." not in out
    assert "This report was too large" in out
    assert "https://example.test/artifact" in out


def test_truncation_uses_workflow_url_when_no_artifact():
    big = _body_with_tables(MAX_COMMENT_BYTES + 10_000)
    out, truncated = truncate_if_needed(
        big, workflow_run_url="https://example.test/run/1"
    )
    assert truncated is True
    assert "https://example.test/run/1" in out


def test_truncation_falls_back_to_a_byte_slice_without_a_summary():
    body = "# Test Suite Report\n\n" + ("x" * (MAX_COMMENT_BYTES + 10_000))
    out, truncated = truncate_if_needed(body)
    assert truncated is True
    assert len(out.encode("utf-8")) < MAX_COMMENT_BYTES
    assert out.startswith("# Test Suite Report")
    assert "This report was too large" in out
    assert "available in the step summary." in out


def test_truncation_keeps_the_table_when_it_is_the_last_section():
    body = (
        "## Mod tests\n\n"
        "| Validator | Errors | Warnings |\n"
        "| **Total** | **1** | **0** |\n" + ("y" * (MAX_COMMENT_BYTES + 10_000)) + "\n"
    )
    out, truncated = truncate_if_needed(body, artifact_url="https://example.test/a")
    assert truncated is True
    assert out.endswith("available in [workflow artifact](https://example.test/a).\n")
    assert "| **Total** | **1** | **0** |" in out
    assert "yyyy" not in out


def test_truncation_keeps_a_table_section_with_no_totals_row():
    body = "## Tools tests\n\n" + ("z" * (MAX_COMMENT_BYTES + 10_000)) + "\n"
    out, truncated = truncate_if_needed(body)
    assert truncated is True
    assert out.startswith("## Tools tests")
    assert "This report was too large" in out


def test_truncation_keeps_tools_and_mod_tables():
    body = (
        "## Tools tests\n\n"
        "| Tool suite | Errors | Warnings |\n"
        "| Linux | 1 | 0 |\n\n"
        "## Mod tests\n\n"
        "| Validator | Errors | Warnings |\n"
        "| **Total** | **1** | **0** |\n\n"
        "## New Findings Introduced by this branch.\n\n"
        + ("x" * (MAX_COMMENT_BYTES + 10_000))
        + "\n"
    )
    out, truncated = truncate_if_needed(body, artifact_url="https://example.test/a")
    assert truncated is True
    assert "## Tools tests" in out
    assert "## Mod tests" in out
    assert "| **Total** |" in out
    assert "## New Findings Introduced by this branch." not in out


def test_long_body_keeps_the_category_table():
    head = "<!-- md-validation-report:v1 -->\n# Test Suite Report\n\n"
    tables = (
        "## Mod tests\n\n"
        "| Validator | Errors | Warnings |\n"
        "|-----------|-------:|---------:|\n"
        "| **Total** | **1** | **0** |\n\n"
        "## Findings by category\n\n"
        "| Category | Errors | Warnings |\n"
        "|----------|-------:|---------:|\n"
        "| Event Picture Format Mismatch | 0 | 211 |\n\n"
        "_…and 5 more categories._\n\n"
    )
    issues = "## New Findings Introduced by this branch.\n\n"
    issues += ("x" * (MAX_COMMENT_BYTES + 10_000)) + "\n"
    out, truncated = truncate_if_needed(head + tables + issues)
    assert truncated is True
    assert "| Event Picture Format Mismatch | 0 | 211 |" in out
    assert "_…and 5 more categories._" in out
    assert "## New Findings Introduced by this branch." not in out
