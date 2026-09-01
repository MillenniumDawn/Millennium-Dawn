"""Tests for `report_lib.markdown`."""

from report_lib import (
    Issue,
    ReportContext,
    Severity,
    ValidatorRun,
    render,
)
from report_lib.baseline import BaselineStats
from report_lib.comment import REPORT_MARKER
from report_lib.markdown import _severity_icon


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
    assert "| ❌ Events | 3 | 1 |" in body
    assert "| ✅ Variables | 0 | 0 |" not in body
    assert "✅ 1 other validator completed successfully." in body


def test_render_verdict_caution_when_errors():
    runs = [ValidatorRun(name="events", title="Events", status="failed", errors=2)]
    body = render(runs, [], _ctx())
    assert "> [!CAUTION]" in body
    assert "2 errors must be fixed before merge." in body


def test_render_verdict_caution_when_a_run_is_incomplete():
    runs = [ValidatorRun(name="events", title="Events", status="unknown")]
    body = render(runs, [], _ctx())
    assert "> [!CAUTION]" in body
    assert "1 validator did not produce a complete result" in body
    assert "All 1 validator passed" not in body


def test_render_verdict_note_when_all_pass():
    runs = [
        ValidatorRun(name="events", title="Events", status="passed"),
        ValidatorRun(name="variables", title="Variables", status="passed"),
    ]
    body = render(runs, [], _ctx())
    assert "> [!NOTE]" in body
    assert "All 2 validators passed" in body
    assert "Nothing to fix." in body
    # No table when everything is clean.
    assert "| Validator | Errors | Warnings |" not in body


def test_render_qualifies_a_clean_partial_run():
    # A per-PR run only gates the validators covering the changed groups, so a
    # clean result must not read as "the whole mod is clean".
    runs = [ValidatorRun(name="events", title="Events", status="passed")]
    ctx = _ctx()
    ctx.validation_scope = "partial"
    body = render(runs, [], ctx)
    assert "Nothing to fix in the file groups this diff touches." in body
    assert "**Scope:** changed file groups only" in body


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


def test_render_passing_validator_omits_empty_dropdown():
    run = ValidatorRun(name="events", title="Events", status="passed")
    body = render([run], [], _ctx())
    assert "## Issues" not in body  # old per-issue heading is gone
    assert "## Validators" not in body
    assert "<summary>✅ Events — 0 issues</summary>" not in body
    assert "✅ No issues found." not in body
    assert "All 1 validator passed" in body


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
    assert "✅ 2 other validators completed successfully." in body


def test_step_summary_hides_passing_validators():
    runs = [
        ValidatorRun(name="events", title="Events", status="failed", errors=2),
        ValidatorRun(name="variables", title="Variables", status="passed"),
    ]
    body = render(runs, [], _ctx())
    assert "| ✅ Variables | 0 | 0 |" not in body
    assert "<summary>✅ Variables" not in body
    assert "<summary>✅ Variables — 0 issues</summary>" not in body
    assert "✅ 1 other validator completed successfully." in body


def test_concise_comment_no_pointer_when_clean():
    runs = [ValidatorRun(name="events", title="Events", status="passed")]
    body = render(runs, [], _ctx(), include_validator_sections=False)
    assert "## Validators" not in body
    assert "full issue list" not in body
    assert "All 1 validator passed" in body


def test_severity_icon_ranks_errors_over_warnings():
    assert _severity_icon(2, 3) == "❌"
    assert _severity_icon(0, 3) == "⚠️"
    assert _severity_icon(0, 0) == "✅"


def test_error_verdict_flags_an_incomplete_validator():
    runs = [
        ValidatorRun(name="events", title="Events", status="failed", errors=2),
        ValidatorRun(name="ideas", title="Ideas", status="no_output"),
    ]
    body = render(runs, [], _ctx())
    assert "2 errors must be fixed before merge." in body
    assert "1 validator did not complete." in body


def test_warning_verdict_flags_an_incomplete_validator():
    runs = [
        ValidatorRun(name="events", title="Events", status="warnings", warnings=2),
        ValidatorRun(name="ideas", title="Ideas", status="unknown"),
    ]
    body = render(runs, [], _ctx())
    assert "> [!WARNING]" in body
    assert "2 warnings to review. None block merge." in body
    assert "1 validator did not complete." in body


def test_metadata_strip_omits_missing_fields():
    ctx = ReportContext(date_utc="2026-04-16 14:02:00 UTC")
    body = render([], [], ctx)
    assert "**Date:** 2026-04-16 14:02:00 UTC" in body
    assert "**Commit:**" not in body
    assert "**PR:**" not in body
    assert "**Run:**" not in body


def test_bullet_without_a_file_renders_the_message_alone():
    issue = Issue(
        severity=Severity.ERROR,
        category="config",
        message="validator crashed before reporting a file",
        validator="events",
    )
    body = render([], [issue], _ctx(repo="MillenniumDawn/Millennium-Dawn"))
    assert "- ❌ validator crashed before reporting a file" in body
    assert "https://github.com/" not in body


def _two_category_issues():
    return [
        Issue(
            severity=Severity.ERROR,
            category=f"cat_{n}",
            message=f"finding {n}",
            file=f"{n}.txt",
            line=1,
            validator="events",
        )
        for n in (1, 2)
    ]


def test_overflow_beyond_max_visible_points_at_the_artifact():
    issues = _two_category_issues()
    body = render([], issues, _ctx(), max_visible=1)
    assert "finding 1" in body
    assert "finding 2" not in body
    assert "> **1 additional issues not shown.**" in body
    assert "[workflow artifact](https://example.test/artifact)" in body


def test_overflow_falls_back_to_the_step_summary_link():
    ctx = _ctx()
    ctx.artifact_url = None
    body = render([], _two_category_issues(), ctx, max_visible=1)
    assert "> **1 additional issues not shown.**" in body
    assert "[step summary](https://example.test/run/1) for the full list." in body


def test_overflow_notice_has_no_link_without_urls():
    ctx = ReportContext(commit_sha="abc1234deadbeef")  # pragma: allowlist secret
    body = render([], _two_category_issues(), ctx, max_visible=1)
    assert "> **1 additional issues not shown.**\n" in body + "\n"
    assert "http" not in body


def test_raw_logs_skip_validators_with_no_output():
    runs = [
        ValidatorRun(
            name="events", title="Events", status="failed", errors=1, log_text="boom"
        ),
        ValidatorRun(name="ideas", title="Ideas", status="no_output", log_text="   "),
    ]
    body = render(runs, [], _ctx())
    assert "#### Events" in body
    assert "#### Ideas" not in body


def _stats(**overrides):
    fields = {
        "new_errors": 1,
        "new_warnings": 1,
        "existing_errors": 4,
        "existing_warnings": 2,
        "unclassified": 0,
    }
    fields.update(overrides)
    stats = BaselineStats()
    for key, value in fields.items():
        setattr(stats, key, value)
    return stats


def test_verdict_counts_new_against_baseline():
    runs = [ValidatorRun(name="events", title="Events", status="failed", errors=2)]
    body = render(
        [runs[0]], [], _ctx(), baseline_stats=_stats(new_errors=2, new_warnings=0)
    )
    assert (
        "2 errors must be fixed before merge. (2 new errors against the main baseline.)"
        in body
    )


def test_verdict_says_none_new_when_all_existing():
    runs = [ValidatorRun(name="events", title="Events", status="failed", errors=2)]
    body = render(
        [runs[0]], [], _ctx(), baseline_stats=_stats(new_errors=0, new_warnings=0)
    )
    assert "(none new against the main baseline.)" in body


def test_verdict_splits_new_errors_and_warnings():
    runs = [
        ValidatorRun(
            name="events", title="Events", status="failed", errors=5, warnings=3
        )
    ]
    body = render(
        [runs[0]], [], _ctx(), baseline_stats=_stats(new_errors=2, new_warnings=1)
    )
    assert "(2 new errors, 1 new warning against the main baseline.)" in body


def test_step_summary_lists_new_findings():
    runs = [
        ValidatorRun(
            name="events", title="Events", status="failed", errors=1, warnings=1
        )
    ]
    error = Issue(
        severity=Severity.ERROR,
        category="missing_key",
        message="key FOO not found",
        file="events/MD_x.txt",
        line=212,
        validator="events",
        baseline_status="new",
    )
    warning = Issue(
        severity=Severity.WARNING,
        category="missing_key",
        message="key BAR unused",
        file="events/MD_x.txt",
        line=80,
        validator="events",
        baseline_status="new",
    )
    stats = _stats(new_issues=[error, warning], unclassified=1)
    body = render([runs[0]], [error, warning], _ctx(), baseline_stats=stats)
    assert "## New Findings Introduced by this branch." in body
    assert "<summary>❌ New errors (1)</summary>" in body
    assert "<summary>⚠️ New warnings (1)</summary>" in body
    error_pos = body.index("<summary>❌ New errors (1)</summary>")
    warning_pos = body.index("<summary>⚠️ New warnings (1)</summary>")
    assert error_pos < warning_pos
    error_details = body[body.rfind("<details", 0, error_pos) : error_pos]
    warning_details = body[body.rfind("<details", 0, warning_pos) : warning_pos]
    assert error_details.startswith("<details open>")
    assert warning_details.startswith("<details>")
    assert "**NEW**" in body
    assert "1 finding(s) could not be compared (no file/line)." in body


def test_step_summary_opens_warnings_when_no_new_errors():
    runs = [
        ValidatorRun(
            name="events", title="Events", status="warnings", errors=0, warnings=1
        )
    ]
    warning = Issue(
        severity=Severity.WARNING,
        category="missing_key",
        message="key BAR unused",
        file="events/MD_x.txt",
        line=80,
        validator="events",
        baseline_status="new",
    )
    stats = _stats(new_issues=[warning], new_errors=0, new_warnings=1)
    body = render([runs[0]], [warning], _ctx(), baseline_stats=stats)
    warning_pos = body.index("<summary>⚠️ New warnings (1)</summary>")
    warning_details = body[body.rfind("<details", 0, warning_pos) : warning_pos]
    assert warning_details.startswith("<details open>")
    assert "<summary>❌ New errors" not in body


def test_step_summary_baseline_section_when_nothing_new():
    runs = [ValidatorRun(name="events", title="Events", status="failed", errors=2)]
    body = render([runs[0]], [], _ctx(), baseline_stats=_stats(new_errors=0))
    assert "✅ No new findings against the main baseline." in body


def _warning_verdict_body(new_warnings):
    runs = [
        ValidatorRun(
            name="events", title="Events", status="warnings", errors=0, warnings=5
        )
    ]
    return render(
        [runs[0]],
        [],
        _ctx(),
        baseline_stats=_stats(new_errors=0, new_warnings=new_warnings),
    )


def test_warning_verdict_counts_new_against_baseline():
    body = _warning_verdict_body(3)
    assert "5 warnings to review. None block merge." in body
    assert "(3 new warnings against the main baseline.)" in body


def test_warning_verdict_says_none_new():
    body = _warning_verdict_body(0)
    assert "(none new against the main baseline.)" in body


def test_baseline_section_caps_new_findings():
    runs = [ValidatorRun(name="events", title="Events", status="failed", errors=2)]
    issues = [
        Issue(
            severity=Severity.ERROR,
            category="missing_key",
            message=f"key {n} not found",
            file="events/MD_x.txt",
            line=n,
            validator="events",
            baseline_status="new",
        )
        for n in range(1, 6)
    ]
    stats = _stats(new_issues=issues)

    body = render([runs[0]], issues, _ctx(), max_visible=3, baseline_stats=stats)

    assert "_…and 2 more new errors._" in body
    assert "key 3 not found" in body
    assert "key 4 not found" not in body


def test_baseline_section_gives_remaining_budget_to_warnings():
    runs = [
        ValidatorRun(
            name="events", title="Events", status="failed", errors=2, warnings=2
        )
    ]
    issues = [
        Issue(
            severity=Severity.ERROR,
            category="missing_key",
            message=f"error {n}",
            file="events/MD_x.txt",
            line=n,
            validator="events",
            baseline_status="new",
        )
        for n in (1, 2)
    ] + [
        Issue(
            severity=Severity.WARNING,
            category="missing_key",
            message=f"warning {n}",
            file="events/MD_x.txt",
            line=n,
            validator="events",
            baseline_status="new",
        )
        for n in (3, 4)
    ]
    stats = _stats(new_issues=issues, new_errors=2, new_warnings=2)

    body = render([runs[0]], issues, _ctx(), max_visible=3, baseline_stats=stats)

    assert "<summary>❌ New errors (2)</summary>" in body
    assert "<summary>⚠️ New warnings (2)</summary>" in body
    assert "error 2" in body
    assert "warning 3" in body
    assert "warning 4" not in body
    assert "_…and 1 more new warning._" in body


def test_baseline_section_notes_unclassified_findings():
    runs = [ValidatorRun(name="events", title="Events", status="failed", errors=2)]
    body = render(
        [runs[0]],
        [],
        _ctx(),
        baseline_stats=_stats(new_errors=0, unclassified=2),
    )
    assert "✅ No new findings against the main baseline." in body
    assert "2 finding(s) could not be compared (no file/line)." in body


def test_concise_comment_omits_baseline_section():
    runs = [
        ValidatorRun(
            name="events", title="Events", status="failed", errors=1, warnings=1
        )
    ]
    issue = Issue(
        severity=Severity.ERROR,
        category="missing_key",
        message="key FOO not found",
        file="events/MD_x.txt",
        line=212,
        validator="events",
        baseline_status="new",
    )
    stats = _stats(new_issues=[issue])
    body = render(
        [runs[0]],
        [issue],
        _ctx(),
        include_validator_sections=False,
        baseline_stats=stats,
    )
    # The concise PR comment carries the counts in the verdict, not the
    # per-finding section that lives in the step summary.
    assert "## New Findings Introduced by this branch." not in body
    assert "(1 new error, 1 new warning against the main baseline.)" in body
