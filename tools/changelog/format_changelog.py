#!/usr/bin/env python3
"""Convert ``Changelog.txt`` into Keep a Changelog markdown.

Usage:
  python3 tools/changelog/format_changelog.py [--check]

- By default the script rewrites/creates ``Changelog.md`` in the repository root.
- With ``--check`` it compares the generated markdown to the existing file and
  exits with status 0 if they match, otherwise it prints a diff and exits 1.

The source file is ``Changelog.txt``. Version headings are read from lines such
as ``v2.0.0`` or ``v2.0.0 - 2026-04-19``. Existing MD headings (Achievements,
AI, Balance, Bugfix, Content, etc.) are grouped into Keep a Changelog sections.
"""

from __future__ import annotations

import argparse
import difflib
import pathlib
import re
import sys

SECTION_ORDER = ["Added", "Changed", "Fixed", "Removed"]
VERSION_PATTERN = re.compile(
    r"^v(?P<version>\d+\.\d+\.\d+)(?:\s+-\s+(?P<date>\d{4}-\d{2}-\d{2}))?$"
)
BULLET_PATTERN = re.compile(r"^(?P<indent>\s*)-\s+(?P<text>.+)$")


def read_source(path: pathlib.Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def classify_heading(heading: str) -> str:
    """Map raw MD headings to Keep a Changelog sections."""
    normalized = heading.lower().strip()

    if normalized in {"achievements", "content"}:
        return "Added"
    if normalized in {"bugfix", "bugfixes"}:
        return "Fixed"

    return "Changed"


def parse_changelog(lines: list[str]) -> list[dict[str, object]]:
    """Parse the plain-text changelog into ordered version/section entries."""
    versions: list[dict[str, object]] = []
    current_version: dict[str, object] | None = None
    current_heading = ""
    current_item: dict[str, object] | None = None

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            continue

        version_match = VERSION_PATTERN.match(stripped)
        if version_match:
            current_version = {
                "version": version_match.group("version"),
                "date": version_match.group("date"),
                "sections": {},
            }
            versions.append(current_version)
            current_heading = ""
            current_item = None
            continue

        if not current_version:
            continue

        if not line.lstrip().startswith("-") and stripped.endswith(":"):
            current_heading = stripped[:-1]
            current_item = None
            continue

        bullet_match = BULLET_PATTERN.match(line)
        if bullet_match:
            section_name = classify_heading(current_heading)
            sections = current_version["sections"]
            section_entries = sections.setdefault(section_name, [])
            indent = len(bullet_match.group("indent")) // 4
            current_item = {
                "level": indent,
                "text": bullet_match.group("text").strip(),
            }
            section_entries.append(current_item)
            continue

        if current_item is not None:
            continuation_indent = len(line) - len(line.lstrip(" "))
            if (
                continuation_indent >= 6
                and ":" in stripped
                and (current_item["text"].endswith(":") or current_item["level"] > 0)
            ):
                section_name = classify_heading(current_heading)
                sections = current_version["sections"]
                section_entries = sections.setdefault(section_name, [])
                next_level = current_item["level"]
                if current_item["text"].endswith(":"):
                    next_level += 1
                current_item = {
                    "level": next_level,
                    "text": stripped,
                }
                section_entries.append(current_item)
                continue

            current_item["text"] = f"{current_item['text']} {stripped}"

    return versions


_LEADING_UNDERSCORE = re.compile(r"(?<!\w)_(?=\S)")


def _escape_md(text: str) -> str:
    """Escape markdown special chars the same way prettier does for list-item text.

    Prettier escapes a leading `_` when it is at a word boundary (not preceded
    by an alphanumeric) to prevent it from being misread as an emphasis marker.
    """
    return _LEADING_UNDERSCORE.sub(r"\\_", text)


def render_markdown(versions: list[dict[str, object]]) -> str:
    lines: list[str] = []

    for version_data in versions:
        version = version_data["version"]
        date = version_data["date"]
        sections = version_data["sections"]

        header = f"## [{version}]"
        if date:
            header = f"{header} - {date}"
        lines.append(f"{header}\n\n")

        for section_name in SECTION_ORDER:
            entries = sections.get(section_name)
            if not entries:
                continue

            # Blank line after header matches prettier's markdown formatting.
            lines.append(f"### {section_name}\n\n")
            for entry in entries:
                indent = "  " * entry["level"]
                lines.append(f"{indent}- {_escape_md(entry['text'])}\n")
            lines.append("\n")

    return "".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert the plain-text changelog to Keep a Changelog markdown."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only verify that Changelog.md is up-to-date.",
    )
    args = parser.parse_args()

    repo_root = pathlib.Path(__file__).resolve().parents[2]
    src_path = repo_root / "Changelog.txt"
    out_path = repo_root / "Changelog.md"

    if not src_path.is_file():
        sys.stderr.write(f"Source changelog not found: {src_path}\n")
        return 1

    parsed = parse_changelog(read_source(src_path))
    markdown = render_markdown(parsed)

    if args.check:
        if not out_path.is_file():
            sys.stderr.write(
                "Changelog.md does not exist - run without --check to generate it.\n"
            )
            return 1

        existing = out_path.read_text(encoding="utf-8")
        if existing == markdown:
            return 0

        diff = difflib.unified_diff(
            existing.splitlines(keepends=True),
            markdown.splitlines(keepends=True),
            fromfile="Changelog.md (current)",
            tofile="Changelog.md (generated)",
        )
        sys.stderr.writelines(diff)
        return 1

    out_path.write_text(markdown, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
