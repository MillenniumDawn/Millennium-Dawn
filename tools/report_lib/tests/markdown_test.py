"""Tests for `report_lib.markdown`."""

from report_lib import Issue, ReportContext, Severity, ValidatorRun, render
from report_lib.comment import REPORT_MARKER


def _ctx(repo=None):
    return ReportContext(
        pr_number="42",
        commit_sha="abc1234deadbeef",  # pragma: allowlist secret
        workflow_run_url="https://example.test/run/1",
        artifact_url="https://example.test/artifact",
        date_utc="2026-04-16 14:02:00 UTC",
        repo=repo,
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
    # Every validator gets a row now — passing ones included, failures first.
    assert "| ❌ Events | 3 | 1 |" in body
    assert "| ✅ Variables | 0 | 0 |" in body


def test_render_verdict_caution_when_errors():
    runs = [ValidatorRun(name="events", title="Events", status="failed", errors=2)]
    body = render(runs, [], _ctx())
    assert "> [!CAUTION]" in body
    assert "2 errors must be fixed before merge." in body


def test_render_verdict_note_when_all_pass():
    runs = [
        ValidatorRun(name="events", title="Events", status="passed"),
        ValidatorRun(name="variables", title="Variables", status="passed"),
    ]
    body = render(runs, [], _ctx())
    assert "> [!NOTE]" in body
    assert "All 2 validators passed" in body
    # No table when everything is clean.
    assert "| Validator | Errors | Warnings |" not in body


def test_render_links_file_to_blob_when_repo_known():
    issue = Issue(
        severity=Severity.ERROR,
        category="missing_key",
        message="key FOO not found",
        file="events/MD_x.txt",
        line=212,
        validator="events",
    )
    body = render([], [issue], _ctx(repo="MillenniumDawn/Millennium-Dawn"))
    assert (
        "https://github.com/MillenniumDawn/Millennium-Dawn/blob/"
        "abc1234deadbeef/events/MD_x.txt#L212" in body
    )


def test_render_no_link_without_repo():
    issue = Issue(
        severity=Severity.ERROR,
        category="missing_key",
        message="key FOO not found",
        file="events/MD_x.txt",
        line=212,
        validator="events",
    )
    body = render([], [issue], _ctx())
    assert "https://github.com/" not in body
    assert "`events/MD_x.txt:212`" in body


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
    assert alpha_section.index("❌") < alpha_section.index("⚠️")


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


def test_render_passing_validator_collapses_to_no_issues():
    run = ValidatorRun(name="events", title="Events", status="passed")
    body = render([run], [], _ctx())
    assert "## Issues" not in body  # old per-issue heading is gone
    assert "## Validators" in body
    assert "<summary>✅ Events — 0 issues</summary>" in body
    assert "✅ No issues found." in body


def test_render_url_encodes_spaces_in_file_path():
    issue = Issue(
        severity=Severity.ERROR,
        category="missing_texture",
        message="texture not referenced",
        file="gfx/interface/My Cool File.dds",
        validator="unused-textures",
    )
    body = render([], [issue], _ctx(repo="MillenniumDawn/Millennium-Dawn"))
    # URL percent-encoded so markdown doesn't break the link at the space.
    assert "gfx/interface/My%20Cool%20File.dds" in body
    # Display label keeps the human-readable spaced path.
    assert "`gfx/interface/My Cool File.dds`" in body


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


def test_concise_comment_omits_validator_sections():
    runs = [
        ValidatorRun(
            name="events", title="Events", status="failed", errors=2, warnings=1
        ),
    ]
    issue = Issue(
        severity=Severity.ERROR,
        category="missing_key",
        message="key FOO not found",
        file="events/MD_x.txt",
        line=212,
        validator="events",
    )
    body = render([runs[0]], [issue], _ctx(), include_validator_sections=False)
    # Summary table counts stay so reviewers see the totals at a glance.
    assert "| **Total** | **2** | **1** |" in body
    # No per-validator detail dumped into the comment.
    assert "## Validators" not in body
    assert "key FOO not found" not in body
    # Reader is pointed at the step summary for the full list.
    assert "[step summary](https://example.test/run/1)" in body
    assert "full issue list" in body


def test_concise_comment_hides_passing_validators():
    runs = [
        ValidatorRun(name="events", title="Events", status="failed", errors=2),
        ValidatorRun(name="variables", title="Variables", status="passed"),
        ValidatorRun(name="ideas", title="Ideas", status="passed"),
    ]
    body = render(runs, [], _ctx(), include_validator_sections=False)
    # Failing validator keeps its row.
    assert "| ❌ Events | 2 | 0 |" in body
    # Passing validators are not listed individually...
    assert "Variables |" not in body
    assert "Ideas |" not in body
    # ...but are summarised as a count.
    assert "✅ 2 validators passed with no issues." in body


def test_step_summary_keeps_passing_validators_in_table():
    runs = [
        ValidatorRun(name="events", title="Events", status="failed", errors=2),
        ValidatorRun(name="variables", title="Variables", status="passed"),
    ]
    # Default render (step-summary mode) keeps the full roster.
    body = render(runs, [], _ctx())
    assert "| ✅ Variables | 0 | 0 |" in body
    assert "passed with no issues." not in body


def test_concise_comment_no_pointer_when_clean():
    runs = [ValidatorRun(name="events", title="Events", status="passed")]
    body = render(runs, [], _ctx(), include_validator_sections=False)
    assert "## Validators" not in body
    assert "full issue list" not in body
    assert "All 1 validator passed" in body
