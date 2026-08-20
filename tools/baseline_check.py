#!/usr/bin/env python3
"""Nightly baseline check: diff fresh main-side results against the baseline.

Run by validator-cache.yml's check-baseline job after
`run_all_validators.py --persist-results` has left the per-validator JSON
sidecars of a full main run on disk. Exit codes:

  0 — no new errors on main (baseline promoted to tonight's results), or no
      previous baseline to compare against (a fresh one is established).
  1 — new errors on main: the workflow goes red and the previous baseline is
      kept, so the alarm repeats every night until the regression is fixed.
      A validator-code change moves the toolshash, which re-establishes the
      baseline instead of comparing against stale output.

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
    issue_key,
    load_baseline,
    load_issues,
    write_baseline,
)

# How many new findings the step summary lists before folding into a count.
MAX_LISTED = 50


def _split_new_findings(
    current: Sequence[Issue], previous: Baseline
) -> Tuple[List[Issue], List[Issue]]:
    """Split current issues into (new errors, new warnings).

    Findings whose key also exists in the previous baseline are existing.
    Findings without a file/line can never match a key and count as new —
    the alarm direction for the nightly check.
    """
    new_errors: List[Issue] = []
    new_warnings: List[Issue] = []
    for issue in current:
        key = issue_key(issue)
        if key is not None and key in previous.keys:
            continue
        if issue.severity == Severity.ERROR:
            new_errors.append(issue)
        else:
            new_warnings.append(issue)
    return new_errors, new_warnings


def _current_keys(current: Sequence[Issue]) -> set:
    keys = set()
    for issue in current:
        key = issue_key(issue)
        if key is not None:
            keys.add(key)
    return keys


def _fixed_counts(current: Sequence[Issue], previous: Baseline) -> Tuple[int, int]:
    """(errors, warnings) present in the previous baseline but gone tonight."""
    fixed = previous.keys - _current_keys(current)
    fixed_errors = sum(1 for key in fixed if key[0] == Severity.ERROR)
    return fixed_errors, len(fixed) - fixed_errors


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
        required=True,
        help="Directory holding the previous baseline (restored cache entry)",
    )
    parser.add_argument(
        "--current",
        required=True,
        help="Directory holding tonight's per-validator JSON sidecars",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Directory to write the new baseline into on a clean diff",
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

    # An empty sidecar dir is a legitimate all-clean run: validators only
    # write a JSON sidecar when they have findings. A missing directory is
    # a wiring error (the persist step never ran), so that alone fails fast.
    current_dir = Path(args.current)
    if not current_dir.is_dir():
        print("--current directory does not exist", file=sys.stderr)
        return 1
    current = load_issues(args.current)

    previous = load_baseline(args.previous, args.toolshash or None)
    meta = _build_meta(args)

    if previous is None:
        write_baseline(args.current, args.output, meta)
        print(
            "No previous baseline for this validator generation; established "
            f"a new baseline from {len(current)} issue(s)."
        )
        _write_step_summary(
            _header_lines(args)
            + [
                f"**Established a new baseline** from {len(current)} issue(s).",
                "",
                "No previous baseline existed for the current validator code "
                "(first run or a validator change moved the toolshash).",
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
