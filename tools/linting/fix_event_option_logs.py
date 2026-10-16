#!/usr/bin/env python3
"""Delete log lines from event options that run no effects (issue #3677 sweep).

Shares detection with validate_events.py's find_option_logs_without_effects
(the `event-option-log-without-effect` check) -- same core, so a clean run of
the validator implies a clean run here and vice versa. An option whose only
statements are `name`, `log`, `ai_chance` and `trigger` changes nothing, so its
log records a state change that never happened. Scope: events/.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "validation"))
from shared_utils import (
    add_dry_run_argument,
    atomic_write_text,
    create_linting_parser,
    read_text_strict,
    run_linting_sweep,
)
from validate_events import find_option_logs_without_effects

__version__ = 1.0


def _is_event_file(filepath):
    return "events/" in filepath.replace("\\", "/")


def _apply(filepath, dry_run):
    """Delete effect-free option log lines in a single file.

    Returns (filepath, fix_count).
    """
    if not _is_event_file(filepath):
        return (filepath, 0)

    try:
        text = read_text_strict(filepath)
    except Exception:
        return (filepath, 0)

    findings = find_option_logs_without_effects(text)
    if not findings:
        return (filepath, 0)

    lines = text.splitlines(keepends=True)
    for line_no in sorted({line for _name, line in findings}, reverse=True):
        del lines[line_no - 1]

    if not dry_run:
        atomic_write_text(filepath, "".join(lines))

    return (filepath, len(findings))


def fix_file(filepath):
    return _apply(filepath, dry_run=False)


def fix_file_dry_run(filepath):
    return _apply(filepath, dry_run=True)


def main():
    parser = create_linting_parser(
        "Delete log lines from event options that run no effects",
        extra_args_fn=add_dry_run_argument,
    )
    args = parser.parse_args()

    return run_linting_sweep(
        args,
        banner=f"Fix Event Option Logs v{__version__}",
        file_filter=_is_event_file,
        apply_fn=fix_file,
        dry_run_fn=fix_file_dry_run,
        unit="log line(s)",
        no_files_message="No event files to process",
        applied_verb="Removed",
        dry_run_verb="Would remove",
    )


if __name__ == "__main__":
    sys.exit(main())
