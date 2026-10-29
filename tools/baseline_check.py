#!/usr/bin/env python3
"""Main baseline check: record a main run and diff it against the accepted one.

Run by validator-cache.yml after `run_all_validators.py --persist-results`
has left the per-validator JSON sidecars of a full main run on disk. A
complete run is always written to --observation: PR reports compare against
that commit's results whether or not they pass the alarm. The alarm compares
the run with the last accepted baseline (--previous) and promotes it to
--output only on a clean diff. The PR suite's base scan passes neither and
only records the observation. Exit codes:

  0 — no new errors on main (accepted baseline promoted to tonight's
      results), or no complete accepted baseline to compare against (a fresh
      one is established).
  1 — new errors on main: the workflow goes red and the accepted baseline is
      kept, so the alarm repeats every night until the regression is fixed.
      A validator-code change moves the toolshash, which re-establishes the
      baseline instead of comparing against stale output. Also returned when
      tonight's results are empty or malformed, so they are written nowhere.

New warnings are reported but never fail the job: warnings are advisory
everywhere else in the pipeline, so the nightly alarm tracks errors only.
"""

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

# report_lib imports need tools/ on sys.path (same bootstrap as
# generate_validation_report.py).
_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

from report_lib import (  # noqa: E402
    Baseline,
    Issue,
    Severity,
    classify,
    count_keys,
    load_baseline,
    load_issues,
    sidecar_names,
    write_baseline,
)

# How many new findings the step summary lists before folding into a count.
MAX_LISTED = 50


def _split_new_findings(
    current: List[Issue], previous: Baseline
) -> Tuple[List[Issue], List[Issue]]:
    """Split current issues into (new errors, new warnings).

    Existing findings and errors lowered to warnings are skipped; a warning
    raised to an error counts as a new error. Findings without a category or
    message can never match a key and count as new, the alarm direction for
    the nightly check.
    """
    classify(current, previous.issues())
    new_errors: List[Issue] = []
    new_warnings: List[Issue] = []
    for issue in current:
        if issue.baseline_status in ("existing", "lowered"):
            continue
        if issue.severity == Severity.ERROR:
            new_errors.append(issue)
        else:
            new_warnings.append(issue)
    return new_errors, new_warnings


def _fixed_counts(current: Sequence[Issue], previous: Baseline) -> Tuple[int, int]:
    """(errors, warnings) present in the previous baseline but gone tonight."""
    fixed = count_keys(previous.issues()) - count_keys(current)
    fixed_errors = sum(n for key, n in fixed.items() if key[0] == Severity.ERROR)
    return fixed_errors, fixed.total() - fixed_errors


def _issue_line(issue: Issue) -> str:
    marker = "❌" if issue.severity == Severity.ERROR else "⚠️"
    if issue.file and issue.line:
        ref = f"`{issue.file}:{issue.line}`"
    elif issue.file:
        ref = f"`{issue.file}`"
    else:
        ref = "_(no location)_"
    return f"- {marker} {ref} — {issue.message}"


def _write_step_summary(lines: Sequence[str]) -> None:
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    try:
        with open(path, "a", encoding="utf-8", newline="") as stream:
            stream.write("\n".join(lines) + "\n")
    except OSError:
        # The step summary is a nicety; the exit code and stdout are the
        # real signal for the workflow.
        print("Warning: could not write step summary", file=sys.stderr)


def _build_meta(args) -> Dict[str, str]:
    return {
        "toolshash": args.toolshash,
        "commit_sha": args.commit_sha,
        "date_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "run_id": os.environ.get("GITHUB_RUN_ID", ""),
        "repo": args.github_repository,
    }


def _header_lines(args) -> List[str]:
    lines = ["## Validation baseline check", ""]
    if args.commit_sha:
        lines.append(f"**Commit:** `{args.commit_sha[:7]}`")
    if args.workflow_run_url:
        lines.append(f"**Run:** [{args.workflow_run_url}]({args.workflow_run_url})")
    lines.append("")
    return lines


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Diff a main-side validation run against the stored baseline"
    )
    parser.add_argument(
        "--previous",
        help=(
            "Directory holding the last accepted baseline (restored cache entry). "
            "Without --previous and --output, only the observation is recorded."
        ),
    )
    parser.add_argument(
        "--current",
        required=True,
        help="Directory holding tonight's per-validator JSON sidecars",
    )
    parser.add_argument(
        "--output",
        help="Directory to write the new accepted baseline into on a clean diff",
    )
    parser.add_argument(
        "--observation",
        required=True,
        help="Directory to write this commit's complete results into, for PR reports",
    )
    parser.add_argument(
        "--toolshash",
        default="",
        help="Validator source hash the previous baseline must match",
    )
    parser.add_argument("--commit-sha", default="")
    parser.add_argument("--workflow-run-url", default="")
    parser.add_argument(
        "--github-repository",
        default=os.environ.get("GITHUB_REPOSITORY", ""),
    )
    args = parser.parse_args(argv)
    if (args.previous is None) != (args.output is None):
        parser.error("--previous and --output go together")

    # Every validator writes a sidecar, even when clean, so a directory with
    # none is a run that produced nothing, not an all-clean main.
    current_dir = Path(args.current)
    if not current_dir.is_dir():
        print("--current directory does not exist", file=sys.stderr)
        return 1
    if not sidecar_names(args.current):
        print("--current holds no validator results", file=sys.stderr)
        return 1
    try:
        current = load_issues(args.current)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1

    meta = _build_meta(args)
    write_baseline(args.current, args.observation, meta)
    if args.previous is None:
        print(f"Recorded a baseline of {len(current)} issue(s).")
        return 0
    previous = load_baseline(args.previous, args.toolshash or None)

    if previous is None:
        write_baseline(args.current, args.output, meta)
        print(
            "No usable previous baseline for this validator generation; "
            f"established a new baseline from {len(current)} issue(s)."
        )
        _write_step_summary(
            _header_lines(args)
            + [
                f"**Established a new baseline** from {len(current)} issue(s).",
                "",
                "No complete previous baseline existed for the current validator "
                "code (first run, a validator change moved the toolshash, or the "
                "stored baseline was incomplete).",
            ]
        )
        return 0

    new_errors, new_warnings = _split_new_findings(current, previous)
    fixed_errors, fixed_warnings = _fixed_counts(current, previous)

    summary = _header_lines(args)
    summary.extend(
        [
            f"- **New errors:** {len(new_errors)}",
            f"- **New warnings:** {len(new_warnings)}",
            f"- **Fixed since last baseline:** {fixed_errors} error(s), "
            f"{fixed_warnings} warning(s)",
        ]
    )

    if new_errors:
        summary.append("")
        summary.append("❌ **New errors on main — baseline not updated.**")
        summary.append("")
        summary.append(f"<details><summary>New errors ({len(new_errors)})</summary>")
        summary.append("")
        shown = new_errors[:MAX_LISTED]
        summary.extend(_issue_line(issue) for issue in shown)
        if len(new_errors) > len(shown):
            summary.append(f"_…and {len(new_errors) - len(shown):,} more._")
        summary.extend(["", "</details>"])
        _write_step_summary(summary)
        print(
            f"✗ {len(new_errors)} new error(s) on main; baseline not updated.",
            file=sys.stderr,
        )
        return 1

    write_baseline(args.current, args.output, meta)
    if new_warnings:
        summary.append("")
        summary.append(
            f"<details><summary>New warnings ({len(new_warnings)})</summary>"
        )
        summary.append("")
        shown = new_warnings[:MAX_LISTED]
        summary.extend(_issue_line(issue) for issue in shown)
        if len(new_warnings) > len(shown):
            summary.append(f"_…and {len(new_warnings) - len(shown):,} more._")
        summary.extend(["", "</details>"])
    summary.append("")
    summary.append("✅ No new errors — baseline updated to tonight's results.")
    _write_step_summary(summary)
    print(
        f"✓ no new errors; baseline updated ({len(new_warnings)} new "
        f"warning(s), {fixed_errors} error(s), {fixed_warnings} warning(s) fixed)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
