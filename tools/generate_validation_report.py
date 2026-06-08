#!/usr/bin/env python3
"""
Generate the Millennium Dawn validation PR report.

Pipeline:
  1. Load per-validator JSON sidecars (falls back to parsing `.log` text).
  2. Dedupe issues that multiple validators surface about the same line.
  3. Render a Markdown body — summary table, issues by file, collapsed logs.
  4. Truncate if over GitHub's 65 536-byte comment limit.
  5. Optionally post the body as a PR comment and/or emit Checks API annotations.

All heavy lifting lives in `tools/report_lib/`; this file is just a CLI.
"""

import argparse
import os
import sys
from datetime import datetime, timezone

# Add tools/ to path so the report_lib package imports cleanly when this
# script is invoked directly (e.g. `python3 tools/generate_validation_report.py`).
_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

from report_lib import (  # noqa: E402
    MAX_ISSUES_STEP_SUMMARY,
    ReportContext,
    dedupe,
    load_all,
    post_checks,
    post_comment,
    render,
    truncate_if_needed,
)


def build_report(results_dir: str, ctx: ReportContext):
    """Return (body, step_summary_body, runs, deduped_issues, truncated)."""
    runs = load_all(results_dir)
    flat_issues = [i for run in runs for i in run.issues]
    deduped = dedupe(flat_issues)

    # PR comment — kept under 65 KB with truncation.
    body = render(runs, deduped, ctx)
    body, truncated = truncate_if_needed(
        body,
        artifact_url=ctx.artifact_url or "",
        workflow_run_url=ctx.workflow_run_url or "",
    )

    # Step summary — more issues, but skip raw logs (they're large and redundant
    # with the structured issue list; omitting them keeps the summary under 1 MB).
    step_body = render(
        runs, deduped, ctx, max_visible=MAX_ISSUES_STEP_SUMMARY, include_raw_logs=False
    )

    return body, step_body, runs, deduped, truncated


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate the Millennium Dawn validation PR report",
    )
    parser.add_argument("--results-dir", required=True)
    parser.add_argument("--output", default="report.md")
    parser.add_argument("--pr-number")
    parser.add_argument("--commit-sha")
    parser.add_argument("--workflow-run-url")
    parser.add_argument("--artifact-url")
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
        "--github-token",
        default=os.environ.get("GITHUB_TOKEN"),
    )
    parser.add_argument(
        "--github-repository",
        default=os.environ.get("GITHUB_REPOSITORY"),
        help="owner/repo (defaults to $GITHUB_REPOSITORY)",
    )

    args = parser.parse_args()

    ctx = ReportContext(
        pr_number=args.pr_number,
        commit_sha=args.commit_sha,
        workflow_run_url=args.workflow_run_url,
        artifact_url=args.artifact_url,
        date_utc=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        repo=args.github_repository,
    )

    body, step_body, runs, deduped, truncated = build_report(args.results_dir, ctx)

    try:
        with open(args.output, "w", encoding="utf-8") as f:
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
            with open(step_summary_path, "w", encoding="utf-8") as f:
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
            success, message = post_comment(
                repo_owner,
                repo_name,
                args.pr_number,
                body,
                args.github_token,
            )
            (print if success else _err)(f"PR comment: {message}")
            # A read-only GITHUB_TOKEN (fork PRs get one regardless of the
            # workflow's permissions block) can't post comments. Don't fail the
            # job over it — the report still uploads as an artifact. Mirrors the
            # Checks API handling below.
            if not success:
                _err(
                    "PR comment could not be posted; continuing. "
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
