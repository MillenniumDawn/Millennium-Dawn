#!/usr/bin/env python3

"""
Drop redundant `enable` triggers from dynamic modifier definitions.

`enable` is re-evaluated at runtime, so a trigger that can never be false is a
recurring cost. Two shapes qualify:

  - `always = yes`, which is what an absent `enable` block already means
  - a top-level `original_tag = X` / `tag = X`, when the modifier is only ever
    attached by `add_dynamic_modifier` from X's own content

Only top-level triggers are touched. One inside `OR` / `NOT` is an alternative
or an exclusion, and `country_exists`, `has_idea` and `has_completed_focus`
stay put: those go false while the modifier is still attached, which is the
case `enable` exists for.

An emptied `enable` block is removed; a trimmed one keeps its other triggers.
Every strip is reported, because "only X ever attaches it" is a claim about the
rest of the repo that this script does not verify.
"""

import argparse
import os
import re
import sys
from typing import List, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from common_utils import (  # noqa: E402
    apply_brace_stack,
    code_of_line,
    find_block_span,
)
from shared_utils import atomic_write_text, create_backup, log_message  # noqa: E402

_TAG_GATE_RE = re.compile(r"^\s*(?:original_tag|tag)\s*=\s*[A-Z]{3}\s*$")
_ALWAYS_YES_RE = re.compile(r"^\s*always\s*=\s*yes\s*$")
_ENABLE_OPEN_RE = re.compile(r"^\s*enable\s*=\s*\{")
_PACKED_GATE_RE = re.compile(
    r"\s*(?:(?:original_tag|tag)\s*=\s*[A-Z]{3}|always\s*=\s*yes)(?=\s|$)"
)


def _strip_enable_body(body: List[str]) -> Tuple[List[str], int]:
    """Drop top-level tag gates and `always = yes` from an enable block body."""
    kept: List[str] = []
    stripped = 0
    depth = 0
    for line in body:
        code = code_of_line(line)
        if depth == 0 and (_TAG_GATE_RE.match(code) or _ALWAYS_YES_RE.match(code)):
            stripped += 1
        else:
            kept.append(line)
        depth += code.count("{") - code.count("}")
    return kept, stripped


def _rewrite_enable_block(
    lines: List[str], start: int, opener_match, span: Tuple[int, int]
) -> Tuple[List[str], bool, bool]:
    """Rewrite one `enable` block into the lines that replace it.

    Returns those lines (empty when the block leaves nothing behind), whether
    it was removed outright, and whether it was trimmed. Both flags are False
    when nothing was redundant and the block is returned untouched.
    """
    end, close_col = span
    opener = lines[start]
    packed = end == start
    head = opener[: opener_match.start()]
    tail = lines[end][close_col + 1 :]

    if packed:
        rest, stripped = _strip_packed_body(opener[opener_match.end() : close_col])
        empty = not rest.strip()
        body: List[str] = []
    else:
        # Anything after the `{` on the opener is body, not scaffolding.
        lead = opener[opener_match.end() :]
        body, stripped = _strip_enable_body(
            ([lead] if lead.strip() else []) + lines[start + 1 : end]
        )
        rest = ""
        empty = not [line for line in body if code_of_line(line).strip()]

    if not stripped:
        return lines[start : end + 1], False, False
    if empty:
        merged = head + tail
        return ([merged] if merged.strip() else []), True, False
    if packed:
        return [f"{head}enable = {{{rest.rstrip()} }}{tail}"], False, True
    return [head + "enable = {"] + body + [lines[end]], False, True


def strip_enable_gates(lines: List[str]) -> Tuple[List[str], int, int, int]:
    """Rewrite one dynamic modifier file.

    Returns the lines, the number of `enable` blocks removed outright, the
    number trimmed but kept, and the number skipped because their braces never
    balanced.
    """
    out: List[str] = []
    stack: List[str] = []
    removed = 0
    trimmed = 0
    skipped = 0
    i = 0

    while i < len(lines):
        code = code_of_line(lines[i])

        # Depth 1 is the modifier definition; `enable` is its direct child.
        opener_match = _ENABLE_OPEN_RE.match(code) if len(stack) == 1 else None
        span = find_block_span(lines, i, code.index("{")) if opener_match else None

        if opener_match and span is None:
            skipped += 1
        elif span:
            replacement, block_removed, block_trimmed = _rewrite_enable_block(
                lines, i, opener_match, span
            )
            removed += block_removed
            trimmed += block_trimmed
            i = span[0] + 1
            out.extend(replacement)
            # The enclosing modifier's own `}` can ride along on the closer
            # line, so the stack has to see what was emitted, not what was read.
            for line in replacement:
                apply_brace_stack(code_of_line(line), stack)
            # Collapse the blank pair a vanished block leaves behind.
            if (
                not replacement
                and out
                and not out[-1].strip()
                and i < len(lines)
                and not lines[i].strip()
            ):
                i += 1
            continue

        out.append(lines[i])
        apply_brace_stack(code, stack)
        i += 1

    return out, removed, trimmed, skipped


def _strip_packed_body(inner: str) -> Tuple[str, int]:
    """Splice depth-0 tag gates out of a one-line enable body.

    Cutting the matched substrings rather than re-joining parsed statements is
    what keeps a nested `OR = { ... }` intact: its braces are copied through
    untouched instead of being dropped by a statement split.
    """
    depth = 0
    depths = []
    for char in inner:
        depths.append(depth)
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1

    pieces = []
    stripped = 0
    cursor = 0
    for match in _PACKED_GATE_RE.finditer(inner):
        if depths[match.start()] != 0:
            continue
        pieces.append(inner[cursor : match.start()])
        cursor = match.end()
        stripped += 1
    pieces.append(inner[cursor:])
    return "".join(pieces), stripped


def process_file(path: str, dry_run: bool, backup: bool) -> Tuple[int, int, int]:
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        lines = handle.read().split("\n")

    stripped, removed, trimmed, skipped = strip_enable_gates(lines)
    if (removed or trimmed) and not dry_run:
        if backup:
            create_backup(path)
        atomic_write_text(path, "\n".join(stripped))
    return removed, trimmed, skipped


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", help="files (default: dynamic_modifiers/)")
    parser.add_argument("--root", default=None, help="mod root (default: auto)")
    parser.add_argument("--dry-run", action="store_true", help="report, do not write")
    parser.add_argument(
        "-b", "--backup", action="store_true", help="back each file up before writing"
    )
    args = parser.parse_args()

    root = args.root or os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )

    files = args.files
    if not files:
        mod_dir = os.path.join(root, "common", "dynamic_modifiers")
        files = [
            os.path.join(mod_dir, name)
            for name in sorted(os.listdir(mod_dir))
            if name.endswith(".txt")
        ]

    total_removed = 0
    total_trimmed = 0
    total_skipped = 0
    for path in files:
        removed, trimmed, skipped = process_file(path, args.dry_run, args.backup)
        rel = os.path.relpath(path, root)
        if skipped:
            total_skipped += skipped
            log_message("WARNING", f"{rel}: {skipped} enable blocks never close")
        if removed or trimmed:
            total_removed += removed
            total_trimmed += trimmed
            log_message("INFO", f"{rel}: {removed} removed, {trimmed} trimmed")

    verb = "would remove" if args.dry_run else "removed"
    log_message(
        "SUCCESS", f"{verb} {total_removed} enable blocks, trimmed {total_trimmed}"
    )
    return 1 if total_skipped else 0


if __name__ == "__main__":
    sys.exit(main())
