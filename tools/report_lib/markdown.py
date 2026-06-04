"""Render the validation report as Markdown.

Layout:
  1. Hidden stable marker (for comment-update matching).
  2. H1 + metadata strip (commit, PR, workflow run link, date).
  3. Summary table — one row per validator.
  4. Issues section — grouped by validator then category, each category under a
     readable heading.  Large categories are collapsed into <details> blocks.
  5. Collapsed raw per-validator logs at the bottom.
"""

from collections import defaultdict
from typing import Dict, List, Optional, Tuple

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
) -> str:
    """Render the full report body."""
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

    summary = _render_summary_table(runs)
    if summary:
        parts.append(summary)
        parts.append("")

    errored_or_warned = [
        i for i in issues if i.severity in (Severity.ERROR, Severity.WARNING)
    ]
    if errored_or_warned:
        parts.append("---")
        parts.append("")
        parts.append(_LEGEND)
        parts.append("")
        parts.append(_render_issues(errored_or_warned, ctx, max_visible))
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


def _render_summary_table(runs: List[ValidatorRun]) -> str:
    if not runs:
        return "_No validator results found._"

    with_findings: List[ValidatorRun] = []
    passed_count = 0
    for r in runs:
        if r.errors or r.warnings:
            with_findings.append(r)
        else:
            passed_count += 1

    # All clean — the verdict banner already states this; no table to show.
    if not with_findings:
        return ""

    # Only validators with findings get a row; the rest fold into one line.
    total_errors, total_warnings = _totals(with_findings)
    header = "| Validator | Errors | Warnings |\n|-----------|-------:|---------:|"
    rows = [
        f"| {_severity_icon(r.errors, r.warnings)} {r.title} | {r.errors:,} | {r.warnings:,} |"
        for r in with_findings
    ]
    rows.append(f"| **Total** | **{total_errors:,}** | **{total_warnings:,}** |")

    out = "## Summary\n\n" + header + "\n" + "\n".join(rows)
    if passed_count:
        out += (
            f"\n\n✅ {_plural(passed_count, 'other validator')} passed with no issues."
        )
    return out


# ── Issues section ─────────────────────────────────────────────────────────────


def _render_issues(issues: List[Issue], ctx: ReportContext, max_visible: int) -> str:
    # Build: {validator → {category → [issues]}}
    by_validator: Dict[str, Dict[str, List[Issue]]] = defaultdict(
        lambda: defaultdict(list)
    )
    validator_order: List[str] = []
    seen_validators: set = set()

    for issue in issues:
        v = issue.validator or "unknown"
        c = issue.category or "uncategorised"
        if v not in seen_validators:
            seen_validators.add(v)
            validator_order.append(v)
        by_validator[v][c].append(issue)

    total = len(issues)
    rendered_count = 0
    overflow = 0
    sections: List[str] = [f"## Issues — {total:,} total", ""]

    for v in validator_order:
        cat_map = by_validator[v]
        v_errors = sum(
            1 for cats in cat_map.values() for i in cats if i.severity == Severity.ERROR
        )
        v_warnings = sum(
            1
            for cats in cat_map.values()
            for i in cats
            if i.severity == Severity.WARNING
        )
        icon = _severity_icon(v_errors, v_warnings)
        label = _count_label(v_errors, v_warnings)

        sections.append(f"### {icon} {_humanize(v)} — {label}")
        sections.append("")

        for cat, cat_issues in cat_map.items():
            remaining = max_visible - rendered_count
            if remaining <= 0:
                overflow += len(cat_issues)
                continue

            cat_errors = sum(1 for i in cat_issues if i.severity == Severity.ERROR)
            cat_warnings = sum(1 for i in cat_issues if i.severity == Severity.WARNING)
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

            bullets = [_render_bullet(i, ctx) for i in to_render]
            if cat_overflow:
                bullets.append(f"_…and {cat_overflow:,} more in this category._")

            heading = f"#### {_humanize(cat)} ({cat_label})"

            # Small categories render inline; large ones collapse.
            if len(cat_issues) > 10:
                block = (
                    [
                        "<details>",
                        f"<summary>{heading}</summary>",
                        "",
                    ]
                    + bullets
                    + ["", "</details>"]
                )
                sections.extend(block)
            else:
                sections.append(heading)
                sections.append("")
                sections.extend(bullets)

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
        url = f"https://github.com/{ctx.repo}/blob/{ctx.commit_sha}/{issue.file}"
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
