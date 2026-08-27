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

from common_utils import apply_brace_stack, code_of_line  # noqa: E402
from shared_utils import (  # noqa: E402
    atomic_write_text,
    get_slotless_idea_categories,
    log_message,
)


def strip_allowed_blocks(
    lines: List[str], slotless: frozenset
) -> Tuple[List[str], int]:
    """Drop every `allowed` block sitting directly inside a slotless-category idea.

    Returns the rewritten lines and the number of blocks removed. Only the
    ideas > category > idea nesting is touched, so an `allowed` somewhere
    unexpected is left alone rather than guessed at.
    """
    out: List[str] = []
    stack: List[str] = []
    removed = 0
    i = 0

    while i < len(lines):
        code = code_of_line(lines[i])
        opens_allowed = (
            len(stack) == 3
            and stack[0] == "ideas"
            and stack[1] in slotless
            and re.match(r"\s*allowed\s*=\s*\{", code)
        )

        if opens_allowed:
            depth = 0
            j = i
            while True:
                depth += code.count("{") - code.count("}")
                if depth <= 0 or j + 1 >= len(lines):
                    break
                j += 1
                code = code_of_line(lines[j])
            removed += 1
            i = j + 1
            # Collapse the blank pair a removed block can leave behind.
            if out and not out[-1].strip() and i < len(lines) and not lines[i].strip():
                i += 1
            continue

        out.append(lines[i])
        apply_brace_stack(code, stack)
        i += 1

    return out, removed


def process_file(path: str, slotless: frozenset, dry_run: bool) -> int:
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        text = handle.read()
    lines = text.split("\n")

    stripped, removed = strip_allowed_blocks(lines, slotless)
    if removed and not dry_run:
        atomic_write_text(path, "\n".join(stripped))
    return removed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", help="idea files (default: common/ideas/)")
    parser.add_argument("--root", default=None, help="mod root (default: auto)")
    parser.add_argument("--dry-run", action="store_true", help="report, do not write")
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
    for path in files:
        removed = process_file(path, slotless, args.dry_run)
        if removed:
            touched += 1
            total += removed
            log_message("INFO", f"{os.path.relpath(path, root)}: {removed} removed")

    verb = "would remove" if args.dry_run else "removed"
    log_message("SUCCESS", f"{verb} {total} allowed blocks across {touched} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
