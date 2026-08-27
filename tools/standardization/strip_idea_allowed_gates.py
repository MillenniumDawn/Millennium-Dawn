#!/usr/bin/env python3

"""
Remove `allowed` blocks from ideas in slotless categories.

An idea in a category with no slot (`country`, `hidden_ideas`) can only arrive
through `add_idea`, which does not consult `allowed`, so the block is a gate on
a pool the idea never enters. Categories are read from common/idea_tags/, so a
new slotless category is covered without editing this script.

Rewrites in place, touching nothing but the blocks it removes.
"""

import argparse
import os
import re
import sys
from typing import List, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from common_utils import apply_brace_stack, code_of_line, find_block_span  # noqa: E402
from shared_utils import (  # noqa: E402
    atomic_write_text,
    create_backup,
    get_slotless_idea_categories,
    log_message,
)

_ALLOWED_OPEN_RE = re.compile(r"\s*allowed\s*=\s*\{")


def strip_allowed_blocks(
    lines: List[str], slotless: frozenset
) -> Tuple[List[str], int, int]:
    """Drop every `allowed` block sitting directly inside a slotless-category idea.

    Returns the rewritten lines, the number of blocks removed, and the number
    skipped because their braces never balanced. Only the
    ideas > category > idea nesting is touched, so an `allowed` somewhere
    unexpected is left alone rather than guessed at.
    """
    out: List[str] = []
    stack: List[str] = []
    removed = 0
    skipped = 0
    i = 0

    while i < len(lines):
        code = code_of_line(lines[i])
        opener = (
            _ALLOWED_OPEN_RE.match(code)
            if len(stack) == 3 and stack[0] == "ideas" and stack[1] in slotless
            else None
        )

        span = find_block_span(lines, i, code.index("{")) if opener else None
        if opener and span is None:
            skipped += 1
        elif span:
            end, close_col = span
            # Slice around the block instead of dropping whole lines: the
            # closer can share a line with the idea's own `}`.
            merged = lines[i][: opener.start()] + lines[end][close_col + 1 :]
            removed += 1
            i = end + 1
            if merged.strip():
                out.append(merged)
                # The idea's own `}` can ride along on the closer line, so the
                # stack has to see what was emitted, not what was read.
                apply_brace_stack(code_of_line(merged), stack)
                continue
            # Collapse the blank pair a removed block can leave behind.
            if out and not out[-1].strip() and i < len(lines) and not lines[i].strip():
                i += 1
            continue

        out.append(lines[i])
        apply_brace_stack(code, stack)
        i += 1

    return out, removed, skipped


def process_file(
    path: str, slotless: frozenset, dry_run: bool, backup: bool
) -> Tuple[int, int]:
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        text = handle.read()
    lines = text.split("\n")

    stripped, removed, skipped = strip_allowed_blocks(lines, slotless)
    if removed and not dry_run:
        if backup:
            create_backup(path)
        atomic_write_text(path, "\n".join(stripped))
    return removed, skipped


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", help="idea files (default: common/ideas/)")
    parser.add_argument("--root", default=None, help="mod root (default: auto)")
    parser.add_argument("--dry-run", action="store_true", help="report, do not write")
    parser.add_argument(
        "-b", "--backup", action="store_true", help="back each file up before writing"
    )
    args = parser.parse_args()

    root = args.root or os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )
    slotless = get_slotless_idea_categories(root)

    files = args.files
    if not files:
        ideas_dir = os.path.join(root, "common", "ideas")
        files = [
            os.path.join(ideas_dir, name)
            for name in sorted(os.listdir(ideas_dir))
            if name.endswith(".txt")
        ]

    total = 0
    touched = 0
    unbalanced = 0
    for path in files:
        removed, skipped = process_file(path, slotless, args.dry_run, args.backup)
        rel = os.path.relpath(path, root)
        if skipped:
            unbalanced += skipped
            log_message("WARNING", f"{rel}: {skipped} allowed blocks never close")
        if removed:
            touched += 1
            total += removed
            log_message("INFO", f"{rel}: {removed} removed")

    verb = "would remove" if args.dry_run else "removed"
    log_message("SUCCESS", f"{verb} {total} allowed blocks across {touched} files")
    return 1 if unbalanced else 0


if __name__ == "__main__":
    sys.exit(main())
