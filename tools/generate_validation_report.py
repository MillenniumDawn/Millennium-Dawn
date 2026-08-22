#!/usr/bin/env python3
"""
Generate the Millennium Dawn validation PR report.

Pipeline:
  1. Load per-validator JSON sidecars (falls back to parsing `.log` text).
  2. Dedupe issues that multiple validators surface about the same line.
  3. Classify NEW vs EXISTING against the main-side baseline when one was
     restored (otherwise render as before the baseline existed).
  4. Render two bodies: a concise PR comment (summary table + step-summary
     pointer) and a detailed step summary (full per-validator issue list).
  5. Truncate the comment if over GitHub's 65 536-byte limit.
  6. Optionally post the comment as a PR comment and/or emit Checks API annotations.

All heavy lifting lives in `tools/report_lib/`; this file is just a CLI.
"""

import argparse
import os
import sys
from datetime import datetime, timezone
from typing import List, Optional

# Add tools/ to path so the report_lib package imports cleanly when this
# script is invoked directly (e.g. `python3 tools/generate_validation_report.py`).
_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

from report_lib import (  # noqa: E402
    MAX_ISSUES_STEP_SUMMARY,
    ReportContext,
    classify,
    dedupe,
    delete_comment,
    load_all,
    load_baseline,
    post_checks,
    post_comment,
    render,
    truncate_if_needed,
)


def build_report(results_dir: str, ctx: ReportContext, baseline=None):
    """Return (body, step_summary_body, runs, deduped_issues, truncated, stats)."""
    runs = load_all(results_dir)
    flat_issues = [i for run in runs for i in run.issues]
    deduped = dedupe(flat_issues)

    # NEW vs EXISTING classification against the main-side baseline, when
    # one was restored. None keeps rendering exactly as before the baseline
    # existed (cold cache, validator generation change).
    baseline_stats = classify(deduped, baseline) if baseline is not None else None

    # PR comment — concise: verdict, summary-table counts, and a pointer to the
    # step summary. The full per-validator issue list is dropped here so the
    # comment stays small instead of dumping every finding into the PR thread.
    body = render(
        runs,
        deduped,
        ctx,
        include_raw_logs=False,
        include_validator_sections=False,
        baseline_stats=baseline_stats,
    )
    body, truncated = truncate_if_needed(
        body,
        artifact_url=ctx.artifact_url or "",
        workflow_run_url=ctx.workflow_run_url or "",
    )

    # Step summary — the full report: new findings split by severity, then each
    # failing validator's issues. Skip raw logs (large and redundant with the
    # structured list; omitting them keeps the summary under 1 MB).
    step_body = render(
        runs,
        deduped,
        ctx,
        max_visible=MAX_ISSUES_STEP_SUMMARY,
        include_raw_logs=False,
        baseline_stats=baseline_stats,
    )

    return body, step_body, runs, deduped, truncated, baseline_stats


def should_delete_comment(runs, deduped, validation_scope: str) -> bool:
    """Only a full run proves the PR clean, so only a full run may delete."""
    return (
        validation_scope == "full"
        and bool(runs)
        and not deduped
        and all(run.status == "passed" for run in runs)
    )


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate the Millennium Dawn validation PR report",
    )
    parser.add_argument("--results-dir", required=True)
    parser.add_argument("--output", default="report.md")
    parser.add_argument("--pr-number")
    parser.add_argument("--commit-sha")
    parser.add_argument("--workflow-run-url")
    parser.add_argument("--artifact-url")
    parser.add_argument(
        "--validation-scope",
        choices=("partial", "full"),
        default="partial",
    )
    parser.add_argument("--print", action="store_true")
    parser.add_argument(
        "--post-comment",
        action="store_true",
        help="POST/PATCH the PR comment via the GitHub REST API",
    )
    parser.add_argument(
        "--checks-api",
        action="store_true",
        help="Emit one Check Run per validator with inline annotations",
    )
    parser.add_argument(
        "--baseline-dir",
        default=None,
        help=(
            "Directory holding the main-side validation baseline (restored "
            "cache entry, .validation_baseline). Findings are tagged NEW vs "
            "EXISTING when it loads; a missing/stale baseline only drops the "
            "annotation."
        ),
    )
    parser.add_argument(
        "--baseline-toolshash",
        default=None,
        help=(
            "Validator source hash the baseline must have been built with; "
            "a mismatch ignores the baseline instead of comparing stale output."
        ),
    )
    parser.add_argument(
        "--github-token",
        default=os.environ.get("GITHUB_TOKEN"),
    )
    parser.add_argument(
        "--github-repository",
        default=os.environ.get("GITHUB_REPOSITORY"),
        help="owner/repo (defaults to $GITHUB_REPOSITORY)",
    )

    args = parser.parse_args(argv)

    ctx = ReportContext(
        pr_number=args.pr_number,
        commit_sha=args.commit_sha,
        workflow_run_url=args.workflow_run_url,
        artifact_url=args.artifact_url,
        date_utc=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        repo=args.github_repository,
        validation_scope=args.validation_scope,
    )

    # None on a cold cache or stale toolshash: classification (and the
    # NEW/EXISTING rendering) is skipped instead of comparing against output
    # from a different validator generation.
    baseline = (
        load_baseline(args.baseline_dir, args.baseline_toolshash)
        if args.baseline_dir
        else None
    )

    body, step_body, runs, deduped, truncated, baseline_stats = build_report(
        args.results_dir, ctx, baseline
    )

    try:
        with open(args.output, "w", encoding="utf-8", newline="") as f:
            f.write(body)
    except Exception as e:
        print(f"Error writing report: {e}", file=sys.stderr)
        return 1
    print(f"Report written to {args.output}", file=sys.stderr)
    if truncated:
        print(
            "Report body exceeded 60 KB and was truncated; artifact has the full data.",
            file=sys.stderr,
        )

    # Write richer report to GitHub Actions step summary when running in CI.
    step_summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary_path:
        try:
            with open(step_summary_path, "w", encoding="utf-8", newline="") as f:
                f.write(step_body)
            print("Step summary written.", file=sys.stderr)
        except Exception as e:
            print(f"Warning: could not write step summary: {e}", file=sys.stderr)

    if args.print:
        print(body)

    total_errors = sum(r.errors for r in runs)
    total_warnings = sum(r.warnings for r in runs)
    print(
        f"Loaded {len(runs)} validator run(s): {total_errors} error(s), {total_warnings} warning(s) "
        f"({len(deduped)} unique issue(s) after dedupe)",
        file=sys.stderr,
    )
    if baseline_stats is not None:
        print(
            f"vs main baseline: {baseline_stats.new_errors} new error(s), "
            f"{baseline_stats.new_warnings} new warning(s), "
            f"{baseline_stats.existing_errors + baseline_stats.existing_warnings} existing, "
            f"{baseline_stats.unclassified} unclassified",
            file=sys.stderr,
        )

    if args.post_comment or args.checks_api:
        if not args.github_repository:
            print(
                "--github-repository (or $GITHUB_REPOSITORY) is required for API calls",
                file=sys.stderr,
            )
            return 1
        if not args.github_token:
            print(
                "--github-token (or $GITHUB_TOKEN) is required for API calls",
                file=sys.stderr,
            )
            return 1
        try:
            repo_owner, repo_name = args.github_repository.split("/", 1)
        except ValueError:
            print(
                "--github-repository must be owner/repo",
                file=sys.stderr,
            )
            return 1

        if args.post_comment:
            if not args.pr_number:
                print(
                    "--pr-number is required when --post-comment is used",
                    file=sys.stderr,
                )
                return 1
            if should_delete_comment(runs, deduped, args.validation_scope):
                success, message = delete_comment(
                    repo_owner,
                    repo_name,
                    args.pr_number,
                    args.github_token,
                )
            else:
                # A clean partial run refreshes an existing comment so it stops
                # reporting an older commit, but never opens a new one: only the
                # changed groups' validators ran, so it cannot clear a finding
                # an unrun validator would still report.
                success, message = post_comment(
                    repo_owner,
                    repo_name,
                    args.pr_number,
                    body,
                    args.github_token,
                    update_only=not deduped,
                )
            (print if success else _err)(f"PR comment: {message}")
            # A read-only GITHUB_TOKEN (fork PRs get one regardless of the
            # workflow's permissions block) can't write comments. Don't fail the
            # job over it — the report still uploads as an artifact. Mirrors the
            # Checks API handling below.
            if not success:
                _err(
                    "PR comment could not be updated; continuing. "
                    "See the validation-report artifact for the full report."
                )

        if args.checks_api:
            if not args.commit_sha:
                print(
                    "--commit-sha is required when --checks-api is used",
                    file=sys.stderr,
                )
                return 1
            results = post_checks(
                repo_owner,
                repo_name,
                args.commit_sha,
                runs,
                args.github_token,
            )
            any_failed = False
            for title, success, msg in results:
                prefix = "✓" if success else "✗"
                print(f"{prefix} Check Run '{title}': {msg}", file=sys.stderr)
                if not success:
                    any_failed = True
            # Don't fail the workflow over Checks API hiccups — the PR
            # comment is the source of truth. Just log and continue.
            if any_failed:
                print(
                    "Some Check Runs failed to post; see above. Continuing anyway.",
                    file=sys.stderr,
                )

    return 0


def _err(msg: str) -> None:
    print(msg, file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
