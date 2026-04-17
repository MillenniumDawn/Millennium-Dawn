"""Render the validation report as Markdown.

Layout:
  1. Hidden stable marker (for comment-update matching).
  2. H1 + metadata strip (commit, PR, workflow run link, date).
  3. Summary table with one row per validator plus totals.
  4. "Issues by file" section (default visible) grouped by file, sorted by line.
  5. Collapsed raw per-validator logs at the bottom.
"""

from typing import Iterable, List, Tuple

from .comment import REPORT_MARKER
from .models import Issue, ReportContext, Severity, ValidatorRun

MAX_VISIBLE_ISSUES = 200


def render(runs: List[ValidatorRun], issues: List[Issue], ctx: ReportContext) -> str:
    """Render the full report body.

    `runs` is used for the summary table and raw logs; `issues` is the already-
    deduped list used for the "Issues by file" section.
    """
    parts: List[str] = []
    parts.append(REPORT_MARKER)
    parts.append("# Validation Report")
    parts.append("")
    parts.append(_render_metadata_strip(ctx))
    parts.append("")
    parts.append(_render_summary_table(runs))
    parts.append("")

    errored_or_warned = [
        i for i in issues if i.severity in (Severity.ERROR, Severity.WARNING)
    ]
    if errored_or_warned:
        parts.append(_render_issues_by_file(errored_or_warned, ctx))
        parts.append("")

    raw_logs = _render_raw_logs(runs)
    if raw_logs:
        parts.append(raw_logs)
        parts.append("")

    parts.append("---")
    parts.append(_render_footer(ctx))
    return "\n".join(parts).rstrip() + "\n"


def _render_metadata_strip(ctx: ReportContext) -> str:
    bits: List[str] = []
    if ctx.commit_sha:
        bits.append(f"**Commit:** `{ctx.commit_sha[:7]}`")
    if ctx.pr_number:
        bits.append(f"**PR:** #{ctx.pr_number}")
    if ctx.workflow_run_url:
        bits.append(f"**Run:** [workflow]({ctx.workflow_run_url})")
    if ctx.date_utc:
        bits.append(f"**Date:** {ctx.date_utc}")
    return " · ".join(bits)


def _render_summary_table(runs: List[ValidatorRun]) -> str:
    if not runs:
        return "_No validator results found._"

    header = (
        "| Validator | Errors | Warnings | Status |\n"
        "|-----------|-------:|---------:|:------:|"
    )
    lines = [header]
    total_errors = 0
    total_warnings = 0
    for run in runs:
        lines.append(
            f"| {run.title} | {run.errors} | {run.warnings} | {run.status_symbol()} |"
        )
        total_errors += run.errors
        total_warnings += run.warnings
    lines.append(f"| **Total** | **{total_errors}** | **{total_warnings}** |  |")
    return "## Summary\n\n" + "\n".join(lines)


def _render_issues_by_file(issues: List[Issue], ctx: ReportContext) -> str:
    by_file: dict = {}
    for issue in issues:
        key = issue.file or "_unknown file_"
        by_file.setdefault(key, []).append(issue)

    rendered_count = 0
    overflow = 0
    sections: List[str] = ["## Issues by file", ""]

    for file_path in sorted(by_file):
        file_issues = sorted(
            by_file[file_path],
            key=lambda i: (0 if i.severity == Severity.ERROR else 1, i.line, i.message),
        )
        remaining = MAX_VISIBLE_ISSUES - rendered_count
        if remaining <= 0:
            overflow += len(file_issues)
            continue

        sections.append(f"### `{file_path}`")
        to_render = file_issues[:remaining]
        overflow += len(file_issues) - len(to_render)
        for issue in to_render:
            sections.append(_render_issue_bullet(issue))
        sections.append("")
        rendered_count += len(to_render)

    if overflow:
        link = ""
        if ctx.artifact_url:
            link = f" — see [workflow artifact]({ctx.artifact_url})"
        elif ctx.workflow_run_url:
            link = f" — see [workflow run]({ctx.workflow_run_url})"
        sections.append(f"_…and **{overflow}** additional issue(s) not shown{link}._")

    return "\n".join(sections)


def _render_issue_bullet(issue: Issue) -> str:
    marker = "✗" if issue.severity == Severity.ERROR else "⚠"
    loc = f"line {issue.line}" if issue.line else "_no line_"
    detected_suffix = ""
    if issue.detected_by:
        also = ", ".join(issue.detected_by)
        detected_suffix = f" _(also detected by: {also})_"
    # Keep a light bold for validator name + backticked category so long
    # categories don't wrap the row awkwardly.
    validator = issue.validator or issue.category or "?"
    category = issue.category or "-"
    return (
        f"- {marker} **{validator}** · `{category}` · {loc} — "
        f"{issue.message}{detected_suffix}"
    )


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


def _render_footer(ctx: ReportContext) -> str:
    bits = ["_Generated by `tools/generate_validation_report.py`_"]
    if ctx.workflow_run_url:
        bits.append(f"· [workflow run]({ctx.workflow_run_url})")
    return " ".join(bits)
