"""Tests for `report_lib.markdown`."""

from report_lib import Issue, ReportContext, Severity, ValidatorRun, render
from report_lib.comment import REPORT_MARKER


def _ctx():
    return ReportContext(
        pr_number="42",
        commit_sha="abc1234deadbeef",  # pragma: allowlist secret
        workflow_run_url="https://example.test/run/1",
        artifact_url="https://example.test/artifact",
        date_utc="2026-04-16 14:02:00 UTC",
    )


def test_render_starts_with_marker(tmp_path):
    run = ValidatorRun(name="events", title="Events", status="passed", had_json=True)
    body = render([run], [], _ctx())
    assert body.startswith(REPORT_MARKER)


def test_render_includes_summary_table_totals():
    runs = [
        ValidatorRun(
            name="events", title="Events", status="failed", errors=3, warnings=1
        ),
        ValidatorRun(name="variables", title="Variables", status="passed"),
    ]
    body = render(runs, [], _ctx())
    assert "| **Total** | **3** | **1** |" in body
    assert "✗ Fail" in body
    assert "✓ Pass" in body


def test_render_groups_issues_by_category():
    issues = [
        Issue(
            severity=Severity.ERROR,
            category="alpha",
            message="A",
            file="z.txt",
            line=5,
            validator="events",
        ),
        Issue(
            severity=Severity.ERROR,
            category="beta",
            message="B",
            file="a.txt",
            line=1,
            validator="events",
        ),
        Issue(
            severity=Severity.WARNING,
            category="alpha",
            message="C",
            file="a.txt",
            line=2,
            validator="events",
        ),
    ]
    body = render([], issues, _ctx())
    # Both categories appear as H4 sections
    assert "#### Alpha" in body
    assert "#### Beta" in body
    # Within a category, errors sort before warnings
    alpha_pos = body.index("#### Alpha")
    alpha_section = body[alpha_pos : body.index("#### Beta")]
    assert alpha_section.index("✗") < alpha_section.index("⚠")


def test_render_shows_detected_by_when_multiple_validators():
    issue = Issue(
        severity=Severity.ERROR,
        category="missing_key",
        message="key FOO not found",
        file="a.txt",
        line=1,
        validator="events",
        detected_by=["localisation", "variables"],
    )
    body = render([], [issue], _ctx())
    assert "also: localisation, variables" in body


def test_render_omits_issues_section_when_none():
    run = ValidatorRun(name="events", title="Events", status="passed")
    body = render([run], [], _ctx())
    assert "## Issues" not in body


def test_render_collapses_raw_logs_into_details_block():
    run = ValidatorRun(
        name="events",
        title="Events",
        status="failed",
        errors=1,
        log_text="some validator output\nerror on line 42",
    )
    body = render([run], [], _ctx())
    assert "<details>" in body
    assert "<summary>Full raw logs</summary>" in body
    assert "some validator output" in body


def test_render_has_footer_with_step_summary_link():
    ctx = _ctx()
    body = render([], [], ctx)
    assert "[step summary](https://example.test/run/1)" in body
