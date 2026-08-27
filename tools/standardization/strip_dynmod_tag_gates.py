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

from common_utils import apply_brace_stack, code_of_line  # noqa: E402
from shared_utils import atomic_write_text, log_message  # noqa: E402

_TAG_GATE_RE = re.compile(r"^\s*(?:original_tag|tag)\s*=\s*[A-Z]{3}\s*$")
_ALWAYS_YES_RE = re.compile(r"^\s*always\s*=\s*yes\s*$")
_ENABLE_OPEN_RE = re.compile(r"^\s*enable\s*=\s*\{")


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


def strip_enable_gates(lines: List[str]) -> Tuple[List[str], int, int]:
    """Rewrite one dynamic modifier file.

    Returns the lines, the number of `enable` blocks removed outright, and the
    number trimmed but kept.
    """
    out: List[str] = []
    stack: List[str] = []
    removed = 0
    trimmed = 0
    i = 0

    while i < len(lines):
        code = code_of_line(lines[i])

        # Depth 1 is the modifier definition; `enable` is its direct child.
        if len(stack) == 1 and _ENABLE_OPEN_RE.match(code):
            depth = 0
            end = i
            while True:
                line_code = code_of_line(lines[end])
                depth += line_code.count("{") - line_code.count("}")
                if depth <= 0 or end + 1 >= len(lines):
                    break
                end += 1

            opener = lines[i]
            packed = end == i
            if packed:
                inner = code_of_line(opener).split("{", 1)[1].rsplit("}", 1)[0]
                body = _split_packed(inner)
                closer = ""
            else:
                body = lines[i + 1 : end]
                closer = lines[end]

            kept, stripped = _strip_enable_body(body)
            if not stripped:
                out.append(lines[i])
                apply_brace_stack(code, stack)
                i += 1
                continue

            if not [line for line in kept if code_of_line(line).strip()]:
                removed += 1
                i = end + 1
                if (
                    out
                    and not out[-1].strip()
                    and i < len(lines)
                    and not lines[i].strip()
                ):
                    i += 1
                continue

            trimmed += 1
            if packed:
                indent = opener[: len(opener) - len(opener.lstrip())]
                out.append(f"{indent}enable = {{ {' '.join(kept)} }}")
            else:
                out.append(opener)
                out.extend(kept)
                out.append(closer)
            i = end + 1
            continue

        out.append(lines[i])
        apply_brace_stack(code, stack)
        i += 1

    return out, removed, trimmed


def _split_packed(inner: str) -> List[str]:
    """Split a one-line enable body into one statement per entry."""
    return [part.strip() for part in re.findall(r"[A-Za-z_]\w*\s*=\s*\S+", inner)]


def process_file(path: str, dry_run: bool) -> Tuple[int, int]:
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        lines = handle.read().split("\n")

    stripped, removed, trimmed = strip_enable_gates(lines)
    if (removed or trimmed) and not dry_run:
        atomic_write_text(path, "\n".join(stripped))
    return removed, trimmed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", help="files (default: dynamic_modifiers/)")
    parser.add_argument("--root", default=None, help="mod root (default: auto)")
    parser.add_argument("--dry-run", action="store_true", help="report, do not write")
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
    for path in files:
        removed, trimmed = process_file(path, args.dry_run)
        if removed or trimmed:
            total_removed += removed
            total_trimmed += trimmed
            log_message(
                "INFO",
                f"{os.path.relpath(path, root)}: {removed} removed, {trimmed} trimmed",
            )

    verb = "would remove" if args.dry_run else "removed"
    log_message(
        "SUCCESS", f"{verb} {total_removed} enable blocks, trimmed {total_trimmed}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
