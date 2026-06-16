#!/usr/bin/env python3
"""Fail when Markdown content has a malformed inline link.

Catches the failure mode that shipped 95 broken links once already: an inline
link `](...` whose closing paren was lost, so the destination runs to the end
of the line with no `)`. Such links emit no anchor at all, so a built-HTML
link checker never sees them. This scans the source instead.

Also flags empty link targets `]()`.

Usage:
    python3 check_link_syntax.py                 # scan all docs content
    python3 check_link_syntax.py FILE [FILE ...] # scan specific files (pre-commit)
    python3 check_link_syntax.py --self-test     # validate the checker itself
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    from common import CONTENT_ROOT, iter_markdown
except ImportError:  # when imported as a package module
    from .common import CONTENT_ROOT, iter_markdown

EMPTY_TARGET_RE = re.compile(r"\]\(\s*\)")
# A fence opens with 3+ of ` or ~; the close must use the same char and be at
# least as long (CommonMark), so a shorter run inside the block doesn't close it.
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
INLINE_CODE_RE = re.compile(r"`+[^`\n]*`+")


def mask_inline_code(line: str) -> str:
    """Blank out inline code spans, keeping length so columns stay accurate."""
    return INLINE_CODE_RE.sub(lambda m: " " * len(m.group(0)), line)


def find_unclosed_link(line: str) -> int | None:
    """Return the 1-based column of a `](` whose `)` is missing, else None.

    Tracks paren depth so a destination with balanced inner parens
    (`[x](/a_(b)/c)`) is not falsely flagged, while a target that runs to the
    end of the line with an unbalanced `(` is.
    """
    idx = 0
    while True:
        open_at = line.find("](", idx)
        if open_at == -1:
            return None
        depth = 1
        j = open_at + 2
        while j < len(line):
            if line[j] == "(":
                depth += 1
            elif line[j] == ")":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        if depth > 0:
            return open_at + 1
        idx = j + 1


def scan_text(text: str, name: str) -> list[str]:
    errors: list[str] = []
    fence: str | None = None  # the open fence marker, e.g. "```" or "~~~~"
    for i, raw_line in enumerate(text.splitlines(), start=1):
        m_fence = FENCE_RE.match(raw_line)
        if m_fence:
            marker = m_fence.group(1)
            if fence is None:
                fence = marker
                continue
            # Close only on the same char, at least as long as the opener.
            if marker[0] == fence[0] and len(marker) >= len(fence):
                fence = None
            continue
        if fence is not None:
            continue
        line = mask_inline_code(raw_line)
        if EMPTY_TARGET_RE.search(line):
            errors.append(f"{name}:{i}: empty link target `]()` -- {raw_line.strip()}")
        col = find_unclosed_link(line)
        if col is not None:
            errors.append(
                f"{name}:{i}:{col}: link missing closing `)` -- {raw_line.strip()}"
            )
    return errors


SELF_TEST_CASES: tuple[tuple[str, bool], ...] = (
    ("See the [Guide](/dev-resources/guide/).", False),
    ("Inline `code` and [Guide](/x/) and more.", False),
    ('A titled [link](/x/ "Title here").', False),
    ("Broken [Guide](/dev-resources/guide/", True),
    ("Broken [Guide](/dev-resources/guide// before text.", True),
    ("Broken [Guide](/dev-resources/guide/.", True),
    ("Empty [link]() here.", True),
    ("Valid [x](/a_(b)/c/) link.", False),  # balanced inner parens, not broken
    ("Broken [x](/a_(b)/c/ no close.", True),  # nested parens but still unclosed
    ("Inline code `[x](y` is not a link.", False),  # inline code is masked
    ("```\n[Guide](/broken/\n```", False),  # fenced code is skipped
    # A shorter run inside a longer fence does not close it.
    ("````\n[Guide](/broken/\n```\n[More](/broken2/\n````", False),
)


def self_test() -> int:
    failures = []
    for text, should_fail in SELF_TEST_CASES:
        got = bool(scan_text(text, "self-test"))
        if got != should_fail:
            failures.append(
                f"  expected {'fail' if should_fail else 'pass'}, got "
                f"{'fail' if got else 'pass'}: {text!r}"
            )
    if failures:
        print("Link-syntax self-test FAILED:")
        print("\n".join(failures))
        return 1
    print(f"Link-syntax self-test passed ({len(SELF_TEST_CASES)} cases).")
    return 0


def scan_paths(paths: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in paths:
        try:
            name = str(path.relative_to(CONTENT_ROOT))
        except ValueError:
            name = str(path)
        errors.extend(
            scan_text(path.read_text(encoding="utf-8", errors="replace"), name)
        )
    return errors


def run() -> tuple[bool, str]:
    """Scan all docs content for malformed links; return (passed, report)."""
    errors = scan_paths(list(iter_markdown()))
    if errors:
        return False, "Malformed Markdown links found:\n" + "\n".join(errors)
    return True, "No malformed Markdown links found."


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", help="Specific files to scan.")
    parser.add_argument(
        "--self-test", action="store_true", help="Validate the checker and exit."
    )
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    if args.files:
        errors = scan_paths(
            [Path(f) for f in args.files if f.endswith((".md", ".mdx"))]
        )
        if errors:
            print("Malformed Markdown links found:", file=sys.stderr)
            print("\n".join(errors), file=sys.stderr)
            return 1
        return 0

    passed, report = run()
    if not passed:
        print(report, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
