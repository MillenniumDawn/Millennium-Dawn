#!/usr/bin/env python3
"""Fail CI when Markdown content contains risky raw HTML."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

CONTENT_ROOT = Path(__file__).resolve().parents[1] / "src" / "content"
MARKDOWN_GLOB = ("**/*.md", "**/*.mdx")

BLOCKED_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"<\s*script\b", re.IGNORECASE), "<script>"),
    (re.compile(r"<\s*iframe\b", re.IGNORECASE), "<iframe>"),
    (re.compile(r"<\s*object\b", re.IGNORECASE), "<object>"),
    (re.compile(r"<\s*embed\b", re.IGNORECASE), "<embed>"),
    (re.compile(r"<\s*[^>]*\son[a-z]+\s*=", re.IGNORECASE), "inline event handler"),
)


def strip_fenced_code_blocks(text: str) -> str:
    return re.sub(r"```[\s\S]*?```", "", text)


def iter_markdown_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for pattern in MARKDOWN_GLOB:
        files.extend(root.glob(pattern))
    return sorted(set(files))


def check_file(path: Path) -> list[str]:
    text = strip_fenced_code_blocks(path.read_text(encoding="utf-8"))
    issues: list[str] = []

    for pattern, label in BLOCKED_PATTERNS:
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            issues.append(f"{path.relative_to(CONTENT_ROOT.parent)}:{line}: blocked {label}")

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    issues: list[str] = []
    for file_path in iter_markdown_files(CONTENT_ROOT):
        issues.extend(check_file(file_path))

    if issues:
        print("Blocked raw HTML found in content:", file=sys.stderr)
        for issue in issues:
            print(f"  {issue}", file=sys.stderr)
        return 1

    print("No blocked raw HTML patterns found in content.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
