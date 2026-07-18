#!/usr/bin/env python3
"""Rewrite mismatched log IDs in focus/decision log strings (Check C sweep).

Shares detection with check_common_mistakes.py's _find_focus_log_mismatches /
_find_decision_log_mismatches (Check C) -- same core, so a clean run of the
checker implies a clean run here and vice versa. Only the mismatched ID token
inside the quoted log string is rewritten; complete/timeout/remove/cancel
phrasing around it is left untouched. Scope: common/national_focus/ and
common/decisions/ (fix_common_mistakes.py's event-log check has no fixer --
its ~13 legacy sites were hand-verified and hand-fixed instead).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from check_common_mistakes import (
    _find_decision_log_mismatches,
    _find_focus_log_mismatches,
)
from shared_utils import (
    Timer,
    clean_filepath,
    collect_files_by_mode,
    create_linting_parser,
    get_root_dir,
    print_timing_summary,
    run_with_pool,
)

__version__ = 1.0


def _finder_for(filepath):
    normalized = filepath.replace("\\", "/")
    if "common/national_focus" in normalized:
        return _find_focus_log_mismatches
    if "common/decisions" in normalized:
        return _find_decision_log_mismatches
    return None


def _rewrite_line(line, spans):
    """Apply (start, end, replacement) *spans* to *line*, rightmost first so
    earlier spans stay valid after the length changes."""
    for start, end, replacement in sorted(spans, reverse=True):
        line = line[:start] + replacement + line[end:]
    return line


def _apply(filepath, dry_run):
    """Rewrite mismatched log-id tokens in a single file.

    Returns (filepath, fix_count).
    """
    finder = _finder_for(filepath)
    if finder is None:
        return (filepath, 0)

    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception:
        return (filepath, 0)

    mismatches = finder(lines)
    if not mismatches:
        return (filepath, 0)

    by_line = {}
    for line_idx, start, end, correct_id, _bad_token in mismatches:
        by_line.setdefault(line_idx, []).append((start, end, correct_id))

    for line_idx, spans in by_line.items():
        lines[line_idx] = _rewrite_line(lines[line_idx], spans)

    if not dry_run:
        with open(filepath, "w", encoding="utf-8", newline="") as f:
            f.writelines(lines)

    return (filepath, len(mismatches))


def fix_file(filepath):
    return _apply(filepath, dry_run=False)


def fix_file_dry_run(filepath):
    return _apply(filepath, dry_run=True)


def main():
    def _extra(parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would be fixed without writing changes",
        )

    parser = create_linting_parser(
        "Rewrite mismatched log IDs in focus/decision log strings (Check C sweep)",
        extra_args_fn=_extra,
    )
    args = parser.parse_args()

    timings = []
    root_dir = get_root_dir()
    print(f"Fix Log IDs v{__version__} (Mode: {args.mode}, Dry run: {args.dry_run})")

    with Timer("file collection") as t:
        all_files = collect_files_by_mode(args, root_dir)
    timings.append(("file collection", t.elapsed))

    existing_files = [f for f in all_files if _finder_for(f) is not None]

    if not existing_files:
        print("No focus/decision files to process")
        return 0

    print(f"Processing {len(existing_files)} files...")

    process_fn = fix_file_dry_run if args.dry_run else fix_file
    with Timer("processing") as t:
        results = run_with_pool(process_fn, existing_files, args.workers)
    timings.append(("processing", t.elapsed))

    action = "Would fix" if args.dry_run else "Fixed"
    files_fixed = [(f, c) for f, c in results if c > 0]
    total_fixes = sum(c for _, c in results)

    for f, c in sorted(files_fixed):
        print(f"  {clean_filepath(f)}: {action.lower()} {c} log id(s)")

    print("\n------")
    print(f"Processed {len(existing_files)} files")
    print(f"{action} {total_fixes} log id(s) in {len(files_fixed)} file(s)")

    elapsed_total = sum(t for _, t in timings)
    print(f"\nCompleted in {elapsed_total:.1f}s")
    print_timing_summary(timings)

    return 0


if __name__ == "__main__":
    sys.exit(main())
