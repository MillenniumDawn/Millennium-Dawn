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


def _blank_keep_newlines(match: re.Match[str]) -> str:
    return re.sub(r"[^\n]", " ", match.group(0))


# Only mask *balanced* inline-code spans (opening run matched by a closing run of
# the same length). A greedy `+...`+ would also blank a real `<script>` sitting
# between two stray unpaired backticks, hiding it from the blocked-HTML scan.
_INLINE_CODE_RE = re.compile(r"(`+)[^`\n]*\1(?!`)")


def mask_code(text: str) -> str:
    """Blank out fenced and inline code so `<tag>` examples aren't scanned as
    raw HTML. Newlines are preserved so reported line numbers stay accurate."""
    text = re.sub(r"```[\s\S]*?```", _blank_keep_newlines, text)
    text = re.sub(r"~~~[\s\S]*?~~~", _blank_keep_newlines, text)
    return _INLINE_CODE_RE.sub(lambda m: " " * len(m.group(0)), text)


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


def scan_blocked_html(text: str, name: str) -> list[str]:
    """Return blocked-HTML issue strings for *text*, with code spans masked."""
    body = mask_code(text)
    issues: list[str] = []
    for pattern, label in BLOCKED_PATTERNS:
        for match in pattern.finditer(body):
            line = body.count("\n", 0, match.start()) + 1
            issues.append(f"{name}:{line}: blocked {label}")
    return issues


def check_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    issues = scan_blocked_html(text, str(path.relative_to(CONTENT_ROOT.parent)))
    issues.extend(check_duplicate_hero_title(path, text))
    return issues


SELF_TEST_CASES: tuple[tuple[str, bool], ...] = (
    ("Inline `<script>` in code is safe.", False),  # balanced span, masked
    ("Angle brackets `<iframe>` in code.", False),
    ("Sample `<button onclick=x>` in code.", False),  # inline handler, masked
    ("Stray ``<script> between backticks.", True),  # unbalanced -> not masked
    ("A ` span ` and a real <script> tag.", True),  # tag sits outside the span
    ("Plain prose with no raw HTML.", False),
    ("Raw <script>alert(1)</script> tag.", True),
    ("```\n<script>\n```", False),  # fenced code is masked
)


def self_test() -> int:
    failures = []
    for text, should_flag in SELF_TEST_CASES:
        got = bool(scan_blocked_html(text, "self-test"))
        if got != should_flag:
            failures.append(
                f"  expected {'flag' if should_flag else 'clean'}, got "
                f"{'flag' if got else 'clean'}: {text!r}"
            )
    if failures:
        print("Content-HTML self-test FAILED:")
        print("\n".join(failures))
        return 1
    print(f"Content-HTML self-test passed ({len(SELF_TEST_CASES)} cases).")
    return 0


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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--self-test", action="store_true", help="Validate the checker and exit."
    )
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    passed, report = run()
    print(report, file=sys.stdout if passed else sys.stderr)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
