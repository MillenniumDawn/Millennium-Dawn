"""Render the validation report as Markdown.

Two renderings come out of the same builder:
  - PR comment (``include_validator_sections=False``): marker, "Test Suite
    Report" verdict banner (new counts lead when a baseline is present),
    metadata strip, an unavailable-baseline notice when needed, the Tools
    tests and Mod tests tables (findings only, with a New column when
    classified; a clean Tools sweep collapses to one line), capped
    new-findings and in-PR groups, plus a pointer to the step summary.
  - Step summary (default): the same top sections, then new findings in two
    collapsible error/warning groups, and per-validator <details> only for
    validators with findings. Clean validators collapse to a single count
    line. Optionally the raw per-validator logs.
"""

from collections import defaultdict
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple
from urllib.parse import quote

from .comment import REPORT_MARKER
from .models import Issue, ReportContext, Severity, ValidatorRun

if TYPE_CHECKING:
    from .baseline import BaselineStats

# PR comment cap — keeps comment inside GitHub's 65 536-byte limit.
MAX_ISSUES_COMMENT = 200
# New-findings listed in the PR comment (errors first, leftover for warnings).
MAX_NEW_FINDINGS_COMMENT = 40
# Step summary cap — kept well under GitHub's 1 024 KB step summary limit.
MAX_ISSUES_STEP_SUMMARY = 1000
# How many issues to show inside one collapsed category block.
MAX_PER_CATEGORY = 100

# Shown once above the issue list when there is anything to fix.
_LEGEND = "_Errors block merge. Warnings are advisory and won't fail CI._"
_NEW_FINDINGS_HEADING = "New Findings Introduced by this branch."
_IN_PR_HEADING = "Findings in your PR"
# Statuses that mean a run produced no usable result, so it cannot count as passed.
_INCOMPLETE_STATUSES = {"unknown", "no_output"}


def render(
    runs: List[ValidatorRun],
    issues: List[Issue],
    ctx: ReportContext,
    max_visible: int = MAX_ISSUES_COMMENT,
    include_raw_logs: bool = True,
    include_validator_sections: bool = True,
    baseline_stats: Optional["BaselineStats"] = None,
) -> str:
    """Render the report body.

    With ``include_validator_sections=False`` the per-validator <details>
    sections and raw logs are dropped (the concise PR comment). New findings
    and in-PR findings still appear, each capped by
    ``MAX_NEW_FINDINGS_COMMENT``. The default renders the full detail for the
    step summary.

    ``baseline_stats`` (from ``baseline.classify``) adds the new-vs-existing
    annotation: new counts lead the verdict, a New column appears on the
    tables, and new findings are listed in separate groups.
    ``Issue.baseline_status`` drives the per-bullet NEW tag; ``Issue.in_diff``
    drives IN YOUR PR. Omit ``baseline_stats`` (no baseline restored) and
    the report renders without NEW annotation.
    """
    parts: List[str] = []
    parts.append(ctx.report_marker or REPORT_MARKER)
    parts.append(f"# {ctx.report_title or 'Test Suite Report'}")
    parts.append("")

    verdict = _render_verdict(runs, ctx.validation_scope, baseline_stats)
    if verdict:
        parts.append(verdict)
        parts.append("")

    parts.append(_render_metadata_strip(ctx))
    parts.append("")

    notice = _render_availability_notice(ctx)
    if notice:
        parts.append(notice)
        parts.append("")

    new_errors = (
        _new_error_counts(baseline_stats) if baseline_stats is not None else None
    )

    tools_section = _render_tools_section(runs, new_errors)
    if tools_section:
        parts.append(tools_section)
        parts.append("")

    summary = _render_summary_table(runs, new_errors)
    if summary:
        parts.append(summary)
        parts.append("")

    findings_cap = (
        max_visible
        if include_validator_sections
        else min(max_visible, MAX_NEW_FINDINGS_COMMENT)
    )
    if baseline_stats is not None:
        baseline_section = _render_baseline_section(baseline_stats, ctx, findings_cap)
        if baseline_section:
            parts.append(baseline_section)
            parts.append("")

    in_pr_section = _render_in_pr_section(
        issues, ctx, findings_cap, exclude_new=baseline_stats is not None
    )
    if in_pr_section:
        parts.append(in_pr_section)
        parts.append("")

    errored_or_warned = [
        i for i in issues if i.severity in (Severity.ERROR, Severity.WARNING)
    ]
    if include_validator_sections:
        validator_sections = _render_validator_sections(
            runs, errored_or_warned, ctx, max_visible
        )
        if validator_sections:
            parts.append("---")
            parts.append("")
            if errored_or_warned:
                parts.append(_LEGEND)
                parts.append("")
            parts.append(validator_sections)
            parts.append("")
    elif errored_or_warned:
        parts.append("---")
        parts.append("")
        parts.append(_LEGEND)
        parts.append("")
        parts.append(_render_details_pointer(ctx))
        parts.append("")

    if include_raw_logs:
        raw_logs = _render_raw_logs(runs)
        if raw_logs:
            parts.append(raw_logs)
            parts.append("")

    parts.append("---")
    parts.append(_render_footer(ctx))
    return "\n".join(parts).rstrip() + "\n"


# ── Helpers ────────────────────────────────────────────────────────────────────


def _humanize(slug: str) -> str:
    """'missing-event-localisation' → 'Missing Event Localisation'"""
    return slug.replace("-", " ").replace("_", " ").title()


def _plural(n: int, word: str) -> str:
    """'5', 'error' → '5 errors'. Thousands-separated, pluralised on n != 1."""
    return f"{n:,} {word}{'s' if n != 1 else ''}"


def _totals(runs: List[ValidatorRun]) -> Tuple[int, int]:
    return sum(r.errors for r in runs), sum(r.warnings for r in runs)


def _count_label(errors: int, warnings: int) -> str:
    parts = []
    if errors:
        parts.append(_plural(errors, "error"))
    if warnings:
        parts.append(_plural(warnings, "warning"))
    return ", ".join(parts) or "0 issues"


def _new_error_counts(stats: "BaselineStats") -> Dict[str, int]:
    counts: Dict[str, int] = defaultdict(int)
    for issue in stats.new_issues:
        if issue.severity == Severity.ERROR and issue.validator:
            counts[issue.validator] += 1
    return counts


def _severity_icon(errors: int, warnings: int) -> str:
    if errors:
        return "❌"
    if warnings:
        return "⚠️"
    return "✅"


# ── Verdict banner ─────────────────────────────────────────────────────────────


def _error_verdict_with_baseline(
    total_errors: int, total_warnings: int, stats: "BaselineStats"
) -> str:
    if stats.new_errors:
        line = (
            f"{_plural(stats.new_errors, 'new error')} against the main baseline "
            f"must be fixed before merge."
        )
        extras = [f"{_plural(total_errors, 'error')} total"]
        if stats.new_warnings:
            extras.append(_plural(stats.new_warnings, "new warning"))
        elif total_warnings:
            extras.append(f"{_plural(total_warnings, 'warning')}, advisory")
        return f"{line} ({', '.join(extras)}.)"
    line = (
        f"No new errors against the main baseline. "
        f"{_plural(total_errors, 'error')} must be fixed before merge."
    )
    if stats.new_warnings:
        line += f" ({_plural(stats.new_warnings, 'new warning')}.)"
    elif total_warnings:
        line += f" ({_plural(total_warnings, 'warning')}, advisory.)"
    return line


def _warning_verdict_with_baseline(total_warnings: int, stats: "BaselineStats") -> str:
    if stats.new_warnings:
        return (
            f"{_plural(stats.new_warnings, 'new warning')} against the main baseline. "
            f"({_plural(total_warnings, 'warning')} to review. None block merge.)"
        )
    return (
        f"No new warnings against the main baseline. "
        f"{_plural(total_warnings, 'warning')} to review. None block merge."
    )


def _render_verdict(
    runs: List[ValidatorRun],
    validation_scope: str = "full",
    baseline_stats: Optional["BaselineStats"] = None,
) -> str:
    """A GitHub alert callout giving an at-a-glance pass/fail verdict."""
    if not runs:
        if validation_scope == "preview":
            return "> [!NOTE]\n> ✅ No validators selected. Nothing to run."
        return ""
    total_errors, total_warnings = _totals(runs)
    incomplete = sum(1 for run in runs if run.status in _INCOMPLETE_STATUSES)

    if total_errors:
        if baseline_stats is not None:
            line = _error_verdict_with_baseline(
                total_errors, total_warnings, baseline_stats
            )
        else:
            line = f"{_plural(total_errors, 'error')} must be fixed before merge."
            if total_warnings:
                line += f" ({_plural(total_warnings, 'warning')}, advisory.)"
        if incomplete:
            line += f" {_plural(incomplete, 'validator')} did not complete."
        return f"> [!CAUTION]\n> ❌ {line}"

    if total_warnings:
        if baseline_stats is not None:
            line = _warning_verdict_with_baseline(total_warnings, baseline_stats)
        else:
            line = f"{_plural(total_warnings, 'warning')} to review. None block merge."
        if incomplete:
            line += f" {_plural(incomplete, 'validator')} did not complete."
        return f"> [!WARNING]\n> ⚠️ {line}"

    if incomplete:
        line = f"{_plural(incomplete, 'validator')} did not produce a complete result."
        return f"> [!CAUTION]\n> ❌ {line} Review the workflow run."

    scope_tails = {
        "full": "Nothing to fix.",
        "partial": "Nothing to fix in the file groups this diff touches.",
        "preview": "Nothing to fix among the validators this PR's changes select.",
    }
    tail = scope_tails.get(
        validation_scope,
        "Nothing to fix in the file groups this diff touches.",
    )
    return f"> [!NOTE]\n> ✅ All {_plural(len(runs), 'validator')} passed. {tail}"


# ── Metadata strip ─────────────────────────────────────────────────────────────


def _render_metadata_strip(ctx: ReportContext) -> str:
    bits: List[str] = []
    if ctx.commit_sha:
        bits.append(f"**Commit:** `{ctx.commit_sha[:7]}`")
    if ctx.pr_number:
        bits.append(f"**PR:** #{ctx.pr_number}")
    if ctx.workflow_run_url:
        bits.append(f"**Run:** [step summary]({ctx.workflow_run_url})")
    if ctx.date_utc:
        bits.append(f"**Date:** {ctx.date_utc}")
    scope_labels = {
        "partial": "changed file groups only",
        "preview": "PR-code preview scan (no baseline comparison)",
    }
    scope_label = scope_labels.get(ctx.validation_scope)
    if scope_label:
        bits.append(f"**Scope:** {scope_label}")
    if ctx.baseline_status == "available":
        bits.append("**Baseline comparison:** available")
    elif ctx.baseline_status == "unavailable":
        bits.append("**Baseline comparison:** unavailable")
    if ctx.changed_files_status == "available":
        bits.append("**Changed files:** available")
    elif ctx.changed_files_status == "unavailable":
        bits.append("**Changed files:** unavailable")
    return " · ".join(bits)


def _render_availability_notice(ctx: ReportContext) -> str:
    bits: List[str] = []
    if ctx.baseline_status == "unavailable":
        bits.append(
            "Baseline comparison unavailable (cold cache or validator generation "
            "mismatch). Findings are not annotated NEW vs EXISTING."
        )
    if ctx.changed_files_status == "unavailable":
        bits.append(
            "Changed-file list was not available. Findings are not tagged IN YOUR PR."
        )
    if not bits:
        return ""
    lines = ["> [!NOTE]"]
    lines.extend(f"> {bit}" for bit in bits)
    return "\n".join(lines)


# ── Summary table ──────────────────────────────────────────────────────────────


def _run_sort_key(
    r: ValidatorRun, new_errors: Optional[Dict[str, int]] = None
) -> Tuple[int, int, str]:
    """New errors first when classified, then errors, warnings, clean."""
    n = (new_errors or {}).get(r.name, 0)
    if new_errors is not None:
        rank = 0 if n else (1 if r.errors else (2 if r.warnings else 3))
        return (rank, -n, r.title.lower())
    rank = 0 if r.errors else (1 if r.warnings else 2)
    return (rank, 0, r.title.lower())


def _table_row(
    title: str,
    errors: int,
    warnings: int,
    new_count: Optional[int] = None,
    bold: bool = False,
) -> str:
    icon = "" if bold else f"{_severity_icon(errors, warnings)} "
    label = f"**{title}**" if bold else f"{icon}{title}"
    err = f"**{errors:,}**" if bold else f"{errors:,}"
    warn = f"**{warnings:,}**" if bold else f"{warnings:,}"
    if new_count is None:
        return f"| {label} | {err} | {warn} |"
    new = f"**{new_count:,}**" if bold else f"{new_count:,}"
    return f"| {label} | {new} | {err} | {warn} |"


def _render_tools_section(
    runs: List[ValidatorRun], new_errors: Optional[Dict[str, int]] = None
) -> str:
    """Findings only; omitted when no tools suite ran, one line when all passed."""
    tools_runs = [r for r in runs if r.suite == "tools"]
    if not tools_runs:
        return ""

    total_errors, total_warnings = _totals(tools_runs)
    # A suite that produced no sidecar also reports 0/0 — never call that a success.
    incomplete = [r for r in tools_runs if r.status in _INCOMPLETE_STATUSES]
    if not total_errors and not total_warnings and not incomplete:
        return "## Tools tests\n\n✅ All tools based tests have succeeded!"

    sorted_runs = sorted(tools_runs, key=lambda r: _run_sort_key(r, new_errors))
    table_runs = [
        r
        for r in sorted_runs
        if r.errors or r.warnings or r.status in _INCOMPLETE_STATUSES
    ]
    passed = len(tools_runs) - len(table_runs)
    passed_note = ""
    if passed:
        passed_note = (
            f"\n\n✅ {_plural(passed, 'other tool suite')} completed successfully."
        )

    if new_errors is not None:
        header = "| Tool suite | New | Errors | Warnings |\n|-----------|----:|-------:|---------:|"
        rows = [
            _table_row(r.title, r.errors, r.warnings, new_errors.get(r.name, 0))
            for r in table_runs
        ]
    else:
        header = "| Tool suite | Errors | Warnings |\n|-----------|-------:|---------:|"
        rows = [_table_row(r.title, r.errors, r.warnings) for r in table_runs]
    return "## Tools tests\n\n" + header + "\n" + "\n".join(rows) + passed_note


def _render_summary_table(
    runs: List[ValidatorRun], new_errors: Optional[Dict[str, int]] = None
) -> str:
    mod_runs = [r for r in runs if r.suite != "tools"]
    if not mod_runs:
        return "## Mod tests\n\n_No validator results found._"

    runs = mod_runs
    total_errors, total_warnings = _totals(runs)
    if total_errors == 0 and total_warnings == 0:
        return ""

    sorted_runs = sorted(runs, key=lambda r: _run_sort_key(r, new_errors))
    table_runs = [r for r in sorted_runs if r.errors or r.warnings]
    passed = sum(1 for r in runs if not r.errors and not r.warnings)
    passed_note = ""
    if passed:
        passed_note = (
            f"\n\n✅ {_plural(passed, 'other validator')} completed successfully."
        )

    if new_errors is not None:
        header = "| Validator | New | Errors | Warnings |\n|-----------|----:|-------:|---------:|"
        rows = [
            _table_row(r.title, r.errors, r.warnings, new_errors.get(r.name, 0))
            for r in table_runs
        ]
        total_new = sum(new_errors.get(r.name, 0) for r in runs)
        rows.append(
            _table_row("Total", total_errors, total_warnings, total_new, bold=True)
        )
    else:
        header = "| Validator | Errors | Warnings |\n|-----------|-------:|---------:|"
        rows = [_table_row(r.title, r.errors, r.warnings) for r in table_runs]
        rows.append(_table_row("Total", total_errors, total_warnings, bold=True))
    return "## Mod tests\n\n" + header + "\n" + "\n".join(rows) + passed_note


# ── Issues section ─────────────────────────────────────────────────────────────


def _finding_sort_key(issue: Issue) -> Tuple[int, str, int, str]:
    """IN YOUR PR first (including NEW + in-PR), then file/line."""
    return (0 if issue.in_diff else 1, issue.file, issue.line, issue.message)


def _render_new_severity_group(
    heading: str,
    word: str,
    issues: List[Issue],
    ctx: ReportContext,
    limit: int,
    open_by_default: bool,
    overflow_word: Optional[str] = None,
) -> Tuple[List[str], int]:
    """One New-errors or New-warnings <details> block. Returns (lines, overflow)."""
    if not issues:
        return [], 0
    sorted_issues = sorted(issues, key=_finding_sort_key)
    shown = sorted_issues[: max(limit, 0)]
    overflow = len(sorted_issues) - len(shown)
    open_attr = " open" if open_by_default else ""
    lines = [
        f"<details{open_attr}>",
        f"<summary>{heading} ({len(issues)})</summary>",
        "",
    ]
    lines.extend(_render_bullet(i, ctx) for i in shown)
    if overflow:
        label = overflow_word or f"more new {word}"
        lines.append(f"_…and {_plural(overflow, label)}._")
    lines.append("")
    lines.append("</details>")
    lines.append("")
    return lines, overflow


def _render_in_pr_section(
    issues: List[Issue],
    ctx: ReportContext,
    max_visible: int,
    exclude_new: bool = False,
) -> str:
    """Findings whose file is in the PR diff, pre-existing ones included.

    Always rendered, so a standing backlog surfaces in the files a PR touches
    instead of staying invisible behind the new-vs-baseline comparison. With
    ``exclude_new`` the new findings are dropped here, since the New Findings
    section above already lists them.
    """
    in_pr = [
        i
        for i in issues
        if i.in_diff
        and i.severity in (Severity.ERROR, Severity.WARNING)
        and not (exclude_new and i.baseline_status == "new")
    ]
    if not in_pr:
        return ""
    lines: List[str] = [f"## {_IN_PR_HEADING}", ""]
    errors = [i for i in in_pr if i.severity == Severity.ERROR]
    warnings = [i for i in in_pr if i.severity != Severity.ERROR]
    remaining = max_visible
    error_lines, error_overflow = _render_new_severity_group(
        "❌ Errors in your PR",
        "error",
        errors,
        ctx,
        remaining,
        open_by_default=True,
        overflow_word="more error",
    )
    remaining = max(0, remaining - (len(errors) - error_overflow))
    warning_lines, _warning_overflow = _render_new_severity_group(
        "⚠️ Warnings in your PR",
        "warning",
        warnings,
        ctx,
        remaining,
        open_by_default=not errors,
        overflow_word="more warning",
    )
    lines.extend(error_lines)
    lines.extend(warning_lines)
    return "\n".join(lines)


def _render_baseline_section(
    stats: "BaselineStats", ctx: ReportContext, max_visible: int
) -> str:
    """New-findings section for the PR comment and the step summary."""
    lines: List[str] = [f"## {_NEW_FINDINGS_HEADING}", ""]

    if not stats.new_issues:
        lines.append("✅ No new findings against the main baseline.")
        if stats.unclassified:
            lines.append(
                f"_{stats.unclassified} finding(s) could not be compared "
                "(no file/line)._"
            )
        return "\n".join(lines)

    new_errors = [i for i in stats.new_issues if i.severity == Severity.ERROR]
    new_warnings = [i for i in stats.new_issues if i.severity != Severity.ERROR]
    remaining = max_visible
    error_lines, error_overflow = _render_new_severity_group(
        "❌ New errors", "error", new_errors, ctx, remaining, open_by_default=True
    )
    remaining = max(0, remaining - (len(new_errors) - error_overflow))
    warning_lines, _warning_overflow = _render_new_severity_group(
        "⚠️ New warnings",
        "warning",
        new_warnings,
        ctx,
        remaining,
        open_by_default=not new_errors,
    )
    lines.extend(error_lines)
    lines.extend(warning_lines)
    if stats.unclassified:
        lines.append(
            f"_{stats.unclassified} finding(s) could not be compared (no file/line)._"
        )
    return "\n".join(lines)


def _render_details_pointer(ctx: ReportContext) -> str:
    """Concise-comment line sending the reader to the step summary for detail."""
    target = (
        f"[step summary]({ctx.workflow_run_url})"
        if ctx.workflow_run_url
        else "the workflow step summary"
    )
    return f"See {target} for the full issue list with file and line references."


def _render_validator_sections(
    runs: List[ValidatorRun], issues: List[Issue], ctx: ReportContext, max_visible: int
) -> str:
    """One collapsible <details> per validator that has findings.

    Failing validators open by default and list their issues grouped by
    category. Clean validators are omitted and counted in a single line so the
    summary is not a wall of empty dropdowns.
    """
    by_validator: Dict[str, Dict[str, List[Issue]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for issue in issues:
        v = issue.validator or "unknown"
        c = issue.category or "uncategorised"
        by_validator[v][c].append(issue)

    # Every run, plus any validator that only shows up in the issues (defensive;
    # in CI each issue has a backing run). counts: name -> (title, errors, warns)
    counts: Dict[str, Tuple[str, int, int]] = {}
    order: List[str] = []
    for r in runs:
        counts[r.name] = (r.title, r.errors, r.warnings)
        order.append(r.name)
    for v, cat_map in by_validator.items():
        if v not in counts:
            flat = [i for lst in cat_map.values() for i in lst]
            e = sum(1 for i in flat if i.severity == Severity.ERROR)
            w = sum(1 for i in flat if i.severity == Severity.WARNING)
            counts[v] = (_humanize(v), e, w)
            order.append(v)

    if not order:
        return ""

    def sort_key(name: str) -> Tuple[int, str]:
        title, e, w = counts[name]
        rank = 0 if e else (1 if w else 2)
        return (rank, title.lower())

    finding_names = [
        name
        for name in sorted(order, key=sort_key)
        if counts[name][1] or counts[name][2]
    ]
    if not finding_names:
        return ""

    sections: List[str] = ["## Validators", ""]
    rendered_count = 0
    overflow = 0

    for name in finding_names:
        title, errors, warnings = counts[name]
        icon = _severity_icon(errors, warnings)
        label = _count_label(errors, warnings)

        body: List[str] = []
        cat_map = by_validator.get(name, {})
        if cat_map:
            for cat, cat_issues in cat_map.items():
                remaining = max_visible - rendered_count
                if remaining <= 0:
                    overflow += len(cat_issues)
                    continue

                cat_errors = sum(1 for i in cat_issues if i.severity == Severity.ERROR)
                cat_warnings = sum(
                    1 for i in cat_issues if i.severity == Severity.WARNING
                )
                cat_label = _count_label(cat_errors, cat_warnings)
                per_cat_limit = min(remaining, MAX_PER_CATEGORY)

                sorted_issues = sorted(
                    cat_issues,
                    key=lambda i: (
                        0 if i.severity == Severity.ERROR else 1,
                        i.file,
                        i.line,
                        i.message,
                    ),
                )
                to_render = sorted_issues[:per_cat_limit]
                cat_overflow = len(cat_issues) - len(to_render)
                overflow += cat_overflow
                rendered_count += len(to_render)

                body.append(f"#### {_humanize(cat)} ({cat_label})")
                body.append("")
                body.extend(_render_bullet(i, ctx) for i in to_render)
                if cat_overflow:
                    body.append(f"_…and {cat_overflow:,} more in this category._")
                body.append("")
        else:
            body.append("_Findings reported in the summary line; see the raw log._")
            body.append("")

        sections.append("<details open>")
        sections.append(f"<summary>{icon} {title} — {label}</summary>")
        sections.append("")
        sections.extend(body)
        sections.append("</details>")
        sections.append("")

    if overflow:
        link = ""
        if ctx.artifact_url:
            link = f" See [workflow artifact]({ctx.artifact_url}) for the full list."
        elif ctx.workflow_run_url:
            link = f" See the [step summary]({ctx.workflow_run_url}) for the full list."
        sections.append(f"> **{overflow:,} additional issues not shown.**{link}")

    return "\n".join(sections)


def _file_ref(issue: Issue, ctx: ReportContext) -> str:
    """`file:line` as inline code, linked to the blob at the head SHA when we
    have the repo + commit to build a URL."""
    label = f"{issue.file}:{issue.line}" if issue.line else issue.file
    code = f"`{label}`"
    if ctx.repo and ctx.commit_sha and issue.file:
        # quote() percent-encodes spaces and other URL-unsafe characters in the
        # path (keeping `/`), so paths like `gfx/My File.dds` produce a valid
        # link instead of one markdown breaks at the first space.
        path = quote(issue.file, safe="/")
        url = f"https://github.com/{ctx.repo}/blob/{ctx.commit_sha}/{path}"
        if issue.line:
            url += f"#L{issue.line}"
        return f"[{code}]({url})"
    return code


def _render_bullet(issue: Issue, ctx: ReportContext) -> str:
    marker = "❌" if issue.severity == Severity.ERROR else "⚠️"
    tags = []
    if issue.baseline_status == "new":
        tags.append("**NEW**")
    if issue.in_diff:
        tags.append("**IN YOUR PR**")
    tag_str = f" {' '.join(tags)}" if tags else ""
    also = f" _(also: {', '.join(issue.detected_by)})_" if issue.detected_by else ""

    if issue.file:
        return f"- {marker}{tag_str} {_file_ref(issue, ctx)} — {issue.message}{also}"
    return f"- {marker}{tag_str} {issue.message}{also}"


# ── Raw logs ───────────────────────────────────────────────────────────────────


def _render_raw_logs(runs: List[ValidatorRun]) -> str:
    has_any = any(r.log_text and r.log_text.strip() for r in runs)
    if not has_any:
        return ""

    parts = ["<details>", "<summary>Full raw logs</summary>", ""]
    for run in runs:
        if not run.log_text or not run.log_text.strip():
            continue
        parts.append(f"#### {run.title}")
        parts.append("")
        parts.append("```")
        parts.append(run.log_text.rstrip())
        parts.append("```")
        parts.append("")
    parts.append("</details>")
    return "\n".join(parts)


# ── Footer ─────────────────────────────────────────────────────────────────────


def _render_footer(ctx: ReportContext) -> str:
    bits = ["_Generated by `tools/generate_validation_report.py`_"]
    if ctx.workflow_run_url:
        bits.append(f"· [step summary]({ctx.workflow_run_url})")
    return " ".join(bits)
