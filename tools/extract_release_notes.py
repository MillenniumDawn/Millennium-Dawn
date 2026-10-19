#!/usr/bin/env python3
"""Extract one version section from Changelog.txt for a GitHub release."""

import argparse
import re
import sys
from pathlib import Path

VERSION_HEADER_RE = re.compile(r"^v\d+\.\d+\.\d+[a-z]?$")


def extract_section(changelog: str, tag: str) -> str | None:
    """Return the exact tagged section, or None when it is absent or empty."""
    lines = changelog.splitlines()
    start = next(
        (index for index, line in enumerate(lines) if line == tag),
        None,
    )
    if start is None or not VERSION_HEADER_RE.fullmatch(lines[start]):
        return None

    end = next(
        (
            index
            for index in range(start + 1, len(lines))
            if VERSION_HEADER_RE.fullmatch(lines[index])
        ),
        len(lines),
    )
    if not any(line.strip() for line in lines[start + 1 : end]):
        return None
    section = "\n".join(lines[start:end]).strip()
    return section or None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag", help="release tag, including its v prefix")
    parser.add_argument("--changelog", type=Path, default=Path("Changelog.txt"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        changelog = args.changelog.read_text(encoding="utf-8-sig")
        section = extract_section(changelog, args.tag)
        if section is None:
            return 1
        with args.output.open("w", encoding="utf-8", newline="") as output:
            output.write(section + "\n")
    except OSError as error:
        print(f"Unable to read or write release notes: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
