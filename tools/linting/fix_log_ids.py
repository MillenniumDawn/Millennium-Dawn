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
    add_dry_run_argument,
    atomic_write_text,
    create_linting_parser,
    read_text_strict,
    run_linting_sweep,
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
        lines = read_text_strict(filepath).splitlines(keepends=True)
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
        atomic_write_text(filepath, "".join(lines))

    return (filepath, len(mismatches))


def fix_file(filepath):
    return _apply(filepath, dry_run=False)


def fix_file_dry_run(filepath):
    return _apply(filepath, dry_run=True)


def main():
    parser = create_linting_parser(
        "Rewrite mismatched log IDs in focus/decision log strings (Check C sweep)",
        extra_args_fn=add_dry_run_argument,
    )
    args = parser.parse_args()

    return run_linting_sweep(
        args,
        banner=f"Fix Log IDs v{__version__}",
        file_filter=lambda filepath: _finder_for(filepath) is not None,
        apply_fn=fix_file,
        dry_run_fn=fix_file_dry_run,
        unit="log id(s)",
        no_files_message="No focus/decision files to process",
    )


if __name__ == "__main__":
    sys.exit(main())
