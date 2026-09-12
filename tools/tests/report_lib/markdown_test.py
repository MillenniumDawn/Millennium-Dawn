"""Tests for `report_lib.markdown`."""

from report_lib import (
    ReportContext,
    Severity,
    ValidatorRun,
    render,
)
from report_lib.baseline import BaselineStats
from report_lib.comment import REPORT_MARKER
from report_lib.markdown import _severity_icon
from shared.suite import make_issue


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


def test_render_defaults_to_the_test_suite_title():
    body = render([], [], _ctx())
    assert body.splitlines()[1] == "# Test Suite Report"


def _tools_run(os_name, errors=0, status=None):
    return ValidatorRun(
        name=f"tools-{os_name.lower()}",
        title=f"Tools tests ({os_name})",
        status=status or ("failed" if errors else "passed"),
        errors=errors,
        suite="tools",
        job=f"Tools tests ({os_name})",
    )


def test_render_leads_with_findings_and_ends_with_the_test_tables():
    runs = [
        ValidatorRun(name="events", title="Events", status="failed", errors=2),
        _tools_run("Linux", errors=1),
        _tools_run("macOS"),
    ]
    new_issue = make_issue(baseline_status="new", in_diff=True)
    old_issue = make_issue(
        message="key BAR not found", line=9, baseline_status="existing", in_diff=True
    )
    stats = _stats(new_issues=[new_issue], new_errors=1, new_warnings=0)
    body = render(runs, [new_issue, old_issue], _ctx(), baseline_stats=stats)
    order = [
        body.index("## New Findings Introduced by this branch."),
        body.index("## Findings in your PR"),
        body.index("## Findings by category"),
        body.index("## Mod tests"),
        body.index("## Tools tests"),
    ]
    assert order == sorted(order)
    assert "| ❌ Tools tests (Linux) | 0 | 1 | 0 |" in body
    assert "| ❌ Events | 1 | 2 | 0 |" in body


def test_tools_section_folds_passing_suites_into_a_count():
    runs = [_tools_run("Linux", errors=1), _tools_run("macOS"), _tools_run("Windows")]
    body = render(runs, [], _ctx())
    assert "| ❌ Tools tests (Linux) | 1 | 0 |" in body
    assert "Tools tests (macOS)" not in body
    assert "✅ 2 other tool suites completed successfully." in body


def test_tools_section_collapses_to_one_line_when_all_pass():
    runs = [_tools_run("Linux"), _tools_run("macOS")]
    body = render(runs, [], _ctx())
    assert "## Tools tests\n\n✅ All tools based tests have succeeded!" in body
    assert "| Tool suite |" not in body


def test_tools_section_collapses_with_a_baseline_classification():
    runs = [_tools_run("Linux"), _tools_run("macOS")]
    body = render(runs, [], _ctx(), baseline_stats=BaselineStats())
    assert "✅ All tools based tests have succeeded!" in body
    assert "| Tool suite | New |" not in body


def test_tools_section_keeps_an_incomplete_suite_visible():
    runs = [_tools_run("Linux"), _tools_run("macOS", status="no_output")]
    body = render(runs, [], _ctx())
    assert "All tools based tests have succeeded!" not in body
    assert "| ✅ Tools tests (macOS) | 0 | 0 |" in body
    assert "✅ 1 other tool suite completed successfully." in body


def test_render_omits_the_tools_section_without_tools_runs():
    runs = [ValidatorRun(name="events", title="Events", status="failed", errors=2)]
    body = render(runs, [], _ctx())
    assert "## Tools tests" not in body
    assert "## Mod tests" in body


def test_mod_tests_ignores_tools_runs_in_counts():
    runs = [_tools_run("Linux"), _tools_run("macOS")]
    body = render(runs, [], _ctx())
    assert "## Mod tests\n\n_No validator results found._" in body
    assert "✅ All tools based tests have succeeded!" in body


def test_mod_tests_passing_count_counts_only_mod_runs():
    runs = [
        ValidatorRun(name="events", title="Events", status="failed", errors=2),
        ValidatorRun(name="ideas", title="Ideas", status="passed"),
        _tools_run("Linux"),
    ]
    body = render(runs, [], _ctx())
    assert "✅ 1 other validator completed successfully." in body


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


def test_render_verdict_warns_when_a_run_is_incomplete():
    # A validator that never finished is a pipeline problem, not something the
    # PR introduced — it must not read as a merge blocker.
    runs = [ValidatorRun(name="events", title="Events", status="unknown")]
    body = render(runs, [], _ctx())
    assert "> [!WARNING]" in body
    assert "> [!CAUTION]" not in body
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
    issue = make_issue()
    body = render([], [issue], _ctx(repo="MillenniumDawn/Millennium-Dawn"))
    assert (
        "https://github.com/MillenniumDawn/Millennium-Dawn/blob/"
        "abc1234deadbeef/events/MD_x.txt#L212" in body
    )


def test_render_no_link_without_repo():
    issue = make_issue()
    body = render([], [issue], _ctx())
    assert "https://github.com/" not in body
    assert "`events/MD_x.txt:212`" in body


def test_render_groups_issues_by_category():
    issues = [
        make_issue(category="alpha", message="A", file="z.txt", line=5),
        make_issue(category="beta", message="B", file="a.txt", line=1),
        make_issue(
            severity=Severity.WARNING,
            category="alpha",
            message="C",
            file="a.txt",
            line=2,
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
    issue = make_issue(
        file="a.txt",
        line=1,
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
    issue = make_issue(
        category="missing_texture",
        message="texture not referenced",
        file="gfx/interface/My Cool File.dds",
        line=0,
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
    issue = make_issue()
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
    issue = make_issue(
        category="config",
        message="validator crashed before reporting a file",
        file="",
        line=0,
    )
    body = render([], [issue], _ctx(repo="MillenniumDawn/Millennium-Dawn"))
    assert "- ❌ validator crashed before reporting a file" in body
    assert "https://github.com/" not in body


def _two_category_issues():
    return [
        make_issue(
            category=f"cat_{n}",
            message=f"finding {n}",
            file=f"{n}.txt",
            line=1,
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


def _new_error(**overrides):
    issue = make_issue(baseline_status="new", **overrides)
    return issue, _stats(new_issues=[issue], new_errors=1, new_warnings=0)


def test_verdict_counts_new_against_baseline():
    runs = [ValidatorRun(name="events", title="Events", status="failed", errors=2)]
    body = render(
        [runs[0]], [], _ctx(), baseline_stats=_stats(new_errors=2, new_warnings=0)
    )
    assert "2 new errors against the main baseline must be fixed before merge." in body
    assert "2 errors total" in body


def _failed_events_body(*, new_errors, new_warnings):
    run = ValidatorRun(
        name="events", title="Events", status="failed", errors=2, warnings=6
    )
    return render(
        [run],
        [],
        _ctx(),
        baseline_stats=_stats(new_errors=new_errors, new_warnings=new_warnings),
    )


def test_verdict_says_none_new_when_all_existing():
    body = _failed_events_body(new_errors=0, new_warnings=0)
    # A standing backlog is not this branch's problem — no red banner.
    assert "> [!NOTE]" in body
    assert "> [!CAUTION]" not in body
    assert "✅ No new errors against the main baseline." in body
    assert "(2 pre-existing errors remain, 6 warnings, advisory.)" in body
    assert "must be fixed before merge" not in body


def test_verdict_warns_when_only_warnings_are_new():
    body = _failed_events_body(new_errors=0, new_warnings=1)
    assert "> [!WARNING]" in body
    assert "> [!CAUTION]" not in body
    assert "1 new warning against the main baseline." in body
    assert "2 pre-existing errors remain" in body
    assert "None block merge." in body


def test_verdict_splits_new_errors_and_warnings():
    runs = [
        ValidatorRun(
            name="events", title="Events", status="failed", errors=5, warnings=3
        )
    ]
    body = render(
        [runs[0]], [], _ctx(), baseline_stats=_stats(new_errors=2, new_warnings=1)
    )
    assert "2 new errors against the main baseline must be fixed before merge." in body
    assert "1 new warning" in body


def test_step_summary_lists_new_findings():
    runs = [
        ValidatorRun(
            name="events", title="Events", status="failed", errors=1, warnings=1
        )
    ]
    error = make_issue(baseline_status="new")
    warning = make_issue(
        severity=Severity.WARNING,
        message="key BAR unused",
        line=80,
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
    warning = make_issue(
        severity=Severity.WARNING,
        message="key BAR unused",
        line=80,
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
    assert "3 new warnings against the main baseline." in body
    assert "5 warnings to review. None block merge." in body


def test_warning_verdict_says_none_new():
    body = _warning_verdict_body(0)
    assert "No new warnings against the main baseline." in body
    assert "5 warnings to review. None block merge." in body


def test_baseline_section_caps_new_findings():
    runs = [ValidatorRun(name="events", title="Events", status="failed", errors=2)]
    issues = [
        make_issue(message=f"key {n} not found", line=n, baseline_status="new")
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
        make_issue(message=f"error {n}", line=n, baseline_status="new") for n in (1, 2)
    ] + [
        make_issue(
            severity=Severity.WARNING,
            message=f"warning {n}",
            line=n,
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


def test_concise_comment_lists_new_findings():
    runs = [
        ValidatorRun(
            name="events", title="Events", status="failed", errors=1, warnings=1
        )
    ]
    issue, stats = _new_error()
    body = render(
        [runs[0]],
        [issue],
        _ctx(),
        include_validator_sections=False,
        baseline_stats=stats,
    )
    assert "## New Findings Introduced by this branch." in body
    assert "**NEW**" in body
    assert "key FOO not found" in body
    assert "## Validators" not in body
    assert "1 new error against the main baseline must be fixed before merge." in body
    assert "step summary" in body


def test_summary_table_adds_new_column_with_baseline():
    runs = [
        ValidatorRun(
            name="events", title="Events", status="failed", errors=3, warnings=1
        ),
        ValidatorRun(name="ideas", title="Ideas", status="failed", errors=1),
    ]
    new_issue, stats = _new_error()
    body = render(runs, [new_issue], _ctx(), baseline_stats=stats)
    assert "| Validator | New | Errors | Warnings |" in body
    assert "| ❌ Events | 1 | 3 | 1 |" in body
    assert "| ❌ Ideas | 0 | 1 | 0 |" in body
    assert "| **Total** | **1** | **4** | **1** |" in body


def test_summary_table_sorts_new_error_validators_first():
    runs = [
        ValidatorRun(name="ideas", title="Ideas", status="failed", errors=9),
        ValidatorRun(name="events", title="Events", status="failed", errors=1),
    ]
    new_issue, stats = _new_error()
    body = render(runs, [new_issue], _ctx(), baseline_stats=stats)
    assert body.index("| ❌ Events | 1 |") < body.index("| ❌ Ideas | 0 |")


def test_unavailable_baseline_is_explicit():
    ctx = _ctx()
    ctx.baseline_status = "unavailable"
    runs = [ValidatorRun(name="events", title="Events", status="failed", errors=1)]
    body = render(runs, [], ctx)
    assert "Baseline comparison unavailable" in body
    assert "**Baseline comparison:** unavailable" in body
    assert "against the main baseline" not in body


def test_comment_lists_in_pr_findings_without_baseline():
    runs = [ValidatorRun(name="events", title="Events", status="failed", errors=1)]
    issue = make_issue(in_diff=True)
    body = render(runs, [issue], _ctx(), include_validator_sections=False)
    assert "## Findings in your PR" in body
    assert "**IN YOUR PR**" in body
    assert "**NEW**" not in body


def test_comment_tags_new_and_in_pr_together():
    runs = [ValidatorRun(name="events", title="Events", status="failed", errors=1)]
    issue, stats = _new_error(in_diff=True)
    body = render(
        runs,
        [issue],
        _ctx(),
        include_validator_sections=False,
        baseline_stats=stats,
    )
    assert "**NEW** **IN YOUR PR**" in body


def test_in_pr_section_lists_existing_findings_alongside_baseline():
    runs = [ValidatorRun(name="events", title="Events", status="failed", errors=2)]
    new_issue, stats = _new_error(in_diff=True, message="new key not found", line=1)
    existing = make_issue(
        in_diff=True, message="existing key not found", line=2, category="backlog"
    )
    body = render(
        runs,
        [new_issue, existing],
        _ctx(),
        include_validator_sections=False,
        baseline_stats=stats,
    )
    assert "## New Findings Introduced by this branch." in body
    assert "## Findings in your PR" in body
    in_pr = body[body.index("## Findings in your PR") :]
    assert "existing key not found" in in_pr
    assert "new key not found" not in in_pr


def test_comment_caps_new_findings():
    runs = [ValidatorRun(name="events", title="Events", status="failed", errors=5)]
    issues = [
        make_issue(message=f"key {n} not found", line=n, baseline_status="new")
        for n in range(1, 6)
    ]
    stats = _stats(new_issues=issues, new_errors=5, new_warnings=0)
    body = render(
        runs,
        issues,
        _ctx(),
        include_validator_sections=False,
        max_visible=3,
        baseline_stats=stats,
    )
    assert "key 3 not found" in body
    assert "key 4 not found" not in body
    assert "_…and 2 more new errors._" in body


def test_category_section_counts_errors_and_warnings_per_category():
    runs = [ValidatorRun(name="events", title="Events", status="failed", errors=1)]
    issues = [
        make_issue(category="missing-event-picture"),
        make_issue(category="event-picture-format-mismatch", severity=Severity.WARNING),
        make_issue(category="event-picture-format-mismatch", severity=Severity.WARNING),
    ]
    body = render(runs, issues, _ctx())
    assert "## Findings by category" in body
    assert "| ❌ Missing Event Picture | 1 | 0 |" in body
    assert "| ⚠️ Event Picture Format Mismatch | 0 | 2 |" in body


def test_category_section_reaches_the_pr_comment():
    """A baselined backlog reaches no other comment section — see #3829."""
    runs = [ValidatorRun(name="events", title="Events", status="failed", warnings=2)]
    issues = [
        make_issue(
            category="event-picture-format-mismatch",
            severity=Severity.WARNING,
            baseline_status="existing",
            line=n,
        )
        for n in (1, 2)
    ]
    body = render(
        runs,
        issues,
        _ctx(),
        include_validator_sections=False,
        baseline_stats=_stats(new_errors=0, new_warnings=0),
    )
    assert "| ⚠️ Event Picture Format Mismatch | 0 | 0 | 2 |" in body


def test_category_section_new_column_only_with_a_baseline():
    runs = [ValidatorRun(name="events", title="Events", status="failed", errors=1)]
    issues = [make_issue(category="missing-event-picture")]
    assert "| Category | New |" not in render(runs, issues, _ctx())
    assert "| Category | New |" in render(
        runs, issues, _ctx(), baseline_stats=_stats(new_errors=0, new_warnings=0)
    )


def test_category_section_caps_its_rows():
    runs = [ValidatorRun(name="events", title="Events", status="failed", errors=30)]
    issues = [make_issue(category=f"category-{n:02d}", line=n) for n in range(30)]
    body = render(runs, issues, _ctx())
    assert "| ❌ Category 00 | 1 | 0 |" in body
    assert "| ❌ Category 29 | 1 | 0 |" not in body
    assert "_…and 5 more categories._" in body


def test_category_section_omitted_without_findings():
    runs = [ValidatorRun(name="events", title="Events", status="passed", had_json=True)]
    assert "## Findings by category" not in render(runs, [], _ctx())
