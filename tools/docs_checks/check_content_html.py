#!/usr/bin/env python3
"""Fail CI when Markdown content contains risky raw HTML or duplicate page titles."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

try:
    from common import CONTENT_ROOT
except ImportError:  # when imported as a package module
    from .common import CONTENT_ROOT

MARKDOWN_GLOB = ("**/*.md", "**/*.mdx")

HERO_TITLE_COLLECTIONS = frozenset(
    {
        "tutorials",
        "resources",
        "changelogSections",
        "devDiaries",
        "countries",
        "misc",
    }
)

BLOCKED_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"<\s*script\b", re.IGNORECASE), "<script>"),
    (re.compile(r"<\s*iframe\b", re.IGNORECASE), "<iframe>"),
    (re.compile(r"<\s*object\b", re.IGNORECASE), "<object>"),
    (re.compile(r"<\s*embed\b", re.IGNORECASE), "<embed>"),
    (re.compile(r"<\s*[^>]*\son[a-z]+\s*=", re.IGNORECASE), "inline event handler"),
)

FRONTMATTER_RE = re.compile(r"^---\r?\n([\s\S]*?)\r?\n---[ \t]*\r?\n?", re.MULTILINE)
TITLE_RE = re.compile(r"^title:\s*[\"']?(.+?)[\"']?\s*$", re.MULTILINE)
LEADING_H1_RE = re.compile(r"^#\s+(.+?)\s*$")


def strip_fenced_code_blocks(text: str) -> str:
    text = re.sub(r"```[\s\S]*?```", "", text)
    return re.sub(r"~~~[\s\S]*?~~~", "", text)


def iter_markdown_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for pattern in MARKDOWN_GLOB:
        files.extend(root.glob(pattern))
    return sorted(set(files))


def collection_name(path: Path) -> str | None:
    try:
        relative = path.relative_to(CONTENT_ROOT)
    except ValueError:
        return None
    parts = relative.parts
    return parts[0] if parts else None


def parse_frontmatter_title(text: str) -> str | None:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return None
    title_match = TITLE_RE.search(match.group(1))
    if not title_match:
        return None
    return title_match.group(1).strip().strip('"').strip("'")


def body_after_frontmatter(text: str) -> str:
    match = FRONTMATTER_RE.match(text)
    return text[match.end() :] if match else text


def first_markdown_h1(body: str) -> str | None:
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        match = LEADING_H1_RE.match(stripped)
        return match.group(1).strip() if match else None
    return None


def check_duplicate_hero_title(path: Path, text: str) -> list[str]:
    collection = collection_name(path)
    if collection not in HERO_TITLE_COLLECTIONS:
        return []

    title = parse_frontmatter_title(text)
    if not title:
        return []

    body = strip_fenced_code_blocks(body_after_frontmatter(text))
    first_h1 = first_markdown_h1(body)
    if first_h1 and first_h1.casefold() == title.casefold():
        rel = path.relative_to(CONTENT_ROOT.parent)
        return [
            f"{rel}: body starts with '# {first_h1}' but layout already renders H1 from frontmatter title"
        ]

    return []


def check_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    body = strip_fenced_code_blocks(text)
    issues: list[str] = []

    for pattern, label in BLOCKED_PATTERNS:
        for match in pattern.finditer(body):
            line = body.count("\n", 0, match.start()) + 1
            issues.append(
                f"{path.relative_to(CONTENT_ROOT.parent)}:{line}: blocked {label}"
            )

    issues.extend(check_duplicate_hero_title(path, text))
    return issues


def run() -> tuple[bool, str]:
    """Scan docs content for blocked HTML / duplicate titles; return (passed, report)."""
    issues: list[str] = []
    for file_path in iter_markdown_files(CONTENT_ROOT):
        issues.extend(check_file(file_path))

    if issues:
        return False, "Content HTML / heading checks failed:\n" + "\n".join(
            f"  {issue}" for issue in issues
        )

    return (
        True,
        "No blocked raw HTML patterns or duplicate hero titles found in content.",
    )


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    passed, report = run()
    print(report, file=sys.stdout if passed else sys.stderr)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
