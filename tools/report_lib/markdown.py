"""Render the validation report as Markdown.

Two renderings come out of the same builder:
  - PR comment (``include_validator_sections=False``): marker, verdict banner,
    metadata strip, and a summary table of only the validators with findings
    (passing ones fold into a count line), plus a pointer to the step summary.
    Kept small so the comment doesn't drown the PR conversation in inline findings.
  - Step summary (default): the full validator roster in the summary table plus
    the per-validator <details> sections — failing ones open with issues grouped
    by category, passing ones collapsed to a one-liner — and optionally the raw
    per-validator logs.
"""

from collections import defaultdict
from typing import Dict, List, Tuple
from urllib.parse import quote

from .comment import REPORT_MARKER
from .models import Issue, ReportContext, Severity, ValidatorRun

# PR comment cap — keeps comment inside GitHub's 65 536-byte limit.
MAX_ISSUES_COMMENT = 200
# Step summary cap — kept well under GitHub's 1 024 KB step summary limit.
MAX_ISSUES_STEP_SUMMARY = 1000
# How many issues to show inside one collapsed category block.
MAX_PER_CATEGORY = 100

# Shown once above the issue list when there is anything to fix.
_LEGEND = "_Errors block merge. Warnings are advisory and won't fail CI._"


def render(
    runs: List[ValidatorRun],
    issues: List[Issue],
    ctx: ReportContext,
    max_visible: int = MAX_ISSUES_COMMENT,
    include_raw_logs: bool = True,
    include_validator_sections: bool = True,
) -> str:
    """Render the report body.

    With ``include_validator_sections=False`` the per-validator <details>
    sections and raw logs are dropped in favour of a one-line pointer to the
    step summary — that's the concise PR comment. The default renders the full
    detail for the step summary.
    """
    parts: List[str] = []
    parts.append(REPORT_MARKER)
    parts.append("# Validation Report")
    parts.append("")

    verdict = _render_verdict(runs)
    if verdict:
        parts.append(verdict)
        parts.append("")

    parts.append(_render_metadata_strip(ctx))
    parts.append("")

    # Concise comment hides passing validators (count note only); the step
    # summary lists the full roster alongside the per-validator sections.
    summary = _render_summary_table(runs, show_passing=include_validator_sections)
    if summary:
        parts.append(summary)
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
        # Concise PR comment: the summary table carries the counts; the full
        # per-validator issue list lives in the step summary.
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


def _severity_icon(errors: int, warnings: int) -> str:
    if errors:
        return "❌"
    if warnings:
        return "⚠️"
    return "✅"


# ── Verdict banner ─────────────────────────────────────────────────────────────


def _render_verdict(runs: List[ValidatorRun]) -> str:
    """A GitHub alert callout giving an at-a-glance pass/fail verdict."""
    if not runs:
        return ""
    total_errors, total_warnings = _totals(runs)

    if total_errors:
        line = f"{_plural(total_errors, 'error')} must be fixed before merge."
        if total_warnings:
            line += f" ({_plural(total_warnings, 'warning')}, advisory.)"
        return f"> [!CAUTION]\n> ❌ {line}"

    if total_warnings:
        line = f"{_plural(total_warnings, 'warning')} to review. None block merge."
        return f"> [!WARNING]\n> ⚠️ {line}"

    return (
        f"> [!NOTE]\n> ✅ All {_plural(len(runs), 'validator')} passed. Nothing to fix."
    )


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
    return " · ".join(bits)


# ── Summary table ──────────────────────────────────────────────────────────────


def _run_sort_key(r: ValidatorRun) -> Tuple[int, str]:
    """Errors first, then warnings, then clean — alphabetical within each tier."""
    rank = 0 if r.errors else (1 if r.warnings else 2)
    return (rank, r.title.lower())


def _render_summary_table(runs: List[ValidatorRun], show_passing: bool = True) -> str:
    if not runs:
        return "_No validator results found._"

    total_errors, total_warnings = _totals(runs)
    # All clean — the verdict banner already states this; a zero table is noise.
    if total_errors == 0 and total_warnings == 0:
        return ""

    sorted_runs = sorted(runs, key=_run_sort_key)
    passed_note = ""
    if show_passing:
        # Step summary: every validator gets a row (passing ones included) so the
        # table is the full at-a-glance roster; failures sort to the top.
        table_runs = sorted_runs
    else:
        # Concise comment: only validators with findings get a row; the rest are
        # folded into a single count line so the comment stays small.
        table_runs = [r for r in sorted_runs if r.errors or r.warnings]
        passed = sum(1 for r in runs if not r.errors and not r.warnings)
        if passed:
            passed_note = (
                f"\n\n✅ {_plural(passed, 'validator')} passed with no issues."
            )

    header = "| Validator | Errors | Warnings |\n|-----------|-------:|---------:|"
    rows = [
        f"| {_severity_icon(r.errors, r.warnings)} {r.title} | {r.errors:,} | {r.warnings:,} |"
        for r in table_runs
    ]
    rows.append(f"| **Total** | **{total_errors:,}** | **{total_warnings:,}** |")
    return "## Summary\n\n" + header + "\n" + "\n".join(rows) + passed_note


# ── Issues section ─────────────────────────────────────────────────────────────


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
    """One collapsible <details> per validator (pass or fail).

    Failing validators open by default and list their issues grouped by
    category; passing validators collapse to a single 'no issues' line, so the
    full roster is browsable for review and debugging.
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

    sections: List[str] = ["## Validators", ""]
    rendered_count = 0
    overflow = 0

    for name in sorted(order, key=sort_key):
        title, errors, warnings = counts[name]
        icon = _severity_icon(errors, warnings)
        label = _count_label(errors, warnings)
        has_findings = bool(errors or warnings)

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
        elif has_findings:
            body.append("_Findings reported in the summary line; see the raw log._")
            body.append("")
        else:
            body.append("✅ No issues found.")
            body.append("")

        open_attr = " open" if has_findings else ""
        sections.append(f"<details{open_attr}>")
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
    also = f" _(also: {', '.join(issue.detected_by)})_" if issue.detected_by else ""

    if issue.file:
        return f"- {marker} {_file_ref(issue, ctx)} — {issue.message}{also}"
    return f"- {marker} {issue.message}{also}"


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
