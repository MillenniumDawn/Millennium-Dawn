#!/usr/bin/env python3
"""Check that the top version of Changelog.txt keeps its entries ordered.

Within each category, untagged entries come first, then [TAG] entries in
alphabetical order of their first tag. No blank line sits between two entries,
and blank lines are never repeated. Exact duplicate entries and entries that
merge_changelog.py --fix would tidy are reported as warnings.
"""

import re
import sys
from pathlib import Path

VERSION_RE = re.compile(r"^v\d+\.\d+")
CATEGORY_RE = re.compile(r"^\s*[^\s-][^:]*:\s*$")
ENTRY_RE = re.compile(r"^\s*- ")
TAG_RE = re.compile(r"^\s*- \[([^\]/]+)")
BULLET_RE = re.compile(r"^\s*-\s*")
TAG_PREFIX_RE = re.compile(r"(?:\[[\w/]+\]\s*/?\s*)+")
WORD_RE = re.compile(r"\w+")


def top_version(lines):
    """Return the lines before the second version heading."""
    seen_version = False
    for index, line in enumerate(lines):
        if VERSION_RE.match(line.lstrip("\ufeff")):
            if seen_version:
                return lines[:index]
            seen_version = True
    return lines[:]


def check_lines(lines):
    """Return error messages for misplaced entries and blank lines in the top version."""
    errors = []
    previous = None
    blank_start = None
    for lineno, line in enumerate(top_version(lines), start=1):
        if not line.strip():
            if blank_start is None:
                blank_start = lineno
            else:
                errors.append(f"line {lineno}: remove the repeated blank line")
            continue
        blank_run, blank_start = blank_start, None
        if CATEGORY_RE.match(line):
            previous = None
            continue
        if not ENTRY_RE.match(line):
            continue
        match = TAG_RE.match(line)
        tag = match.group(1) if match else None
        if previous is not None:
            prev_lineno, prev_tag = previous
            if blank_run == prev_lineno + 1:
                errors.append(
                    f"line {blank_run}: remove the blank line between entries"
                )
            if prev_tag is not None and tag is None:
                errors.append(
                    f"line {lineno}: untagged entry must come before "
                    f"[{prev_tag}] (line {prev_lineno})"
                )
            elif (
                prev_tag is not None
                and tag is not None
                and tag.lower() < prev_tag.lower()
            ):
                errors.append(
                    f"line {lineno}: [{tag}] must come before "
                    f"[{prev_tag}] (line {prev_lineno})"
                )
        previous = (lineno, tag)
    return errors


def order_lines(lines):
    """Stable-sort entry lines in each top-version category and tidy its blank lines.

    Blank lines between two entries are dropped and repeated blank lines become one.
    Other lines stay intact.
    """
    top = top_version(lines)
    ordered = []
    for line in top:
        if not line.strip() and ordered and not ordered[-1].strip():
            continue
        if (
            ENTRY_RE.match(line)
            and len(ordered) > 1
            and not ordered[-1].strip()
            and ENTRY_RE.match(ordered[-2])
        ):
            ordered.pop()
        ordered.append(line)
    groups = [[]]
    for index, line in enumerate(ordered):
        if CATEGORY_RE.match(line):
            groups.append([])
        elif ENTRY_RE.match(line):
            groups[-1].append(index)
    for indexes in groups:
        entries = sorted(
            (ordered[index] for index in indexes),
            key=lambda line: (
                match.group(1).lower() if (match := TAG_RE.match(line)) else ""
            ),
        )
        for index, entry in zip(indexes, entries):
            ending = ordered[index][len(ordered[index].rstrip("\r\n")) :]
            ordered[index] = entry.rstrip("\r\n") + ending
    return ordered + lines[len(top) :]


def clean_entry(line):
    """Normalize one entry: ' - ' bullet, single spaces, [A]/[B] tags, closing period."""
    text = " ".join(BULLET_RE.sub("", line).split())
    prefix = TAG_PREFIX_RE.match(text)
    if prefix:
        tags = "/".join(f"[{tag}]" for tag in WORD_RE.findall(prefix.group()))
        text = f"{tags} {text[prefix.end() :]}".rstrip()
    if re.search(r"[\w%]$", text):
        text += "."
    return f" - {text}"


def clean_lines(lines):
    """Tidy the top version and drop entries that repeat one in the same category.

    Returns the cleaned lines and the removed entries. Older versions stay intact.
    """
    top = top_version(lines)
    cleaned = []
    removed = []
    seen = set()
    category = None
    for line in top:
        ending = line[len(line.rstrip("\r\n")) :]
        if CATEGORY_RE.match(line):
            category = line.strip()
            cleaned.append(category + ending)
        elif ENTRY_RE.match(line):
            entry = clean_entry(line)
            if (category, entry) in seen:
                removed.append(entry)
                continue
            seen.add((category, entry))
            cleaned.append(entry + ending)
        else:
            cleaned.append(line.rstrip() + ending)
    return cleaned + lines[len(top) :], removed


def top_entries(lines):
    """(line number, category name, cleaned entry) for each top-version entry."""
    category = "(no category)"
    for lineno, line in enumerate(top_version(lines), start=1):
        if CATEGORY_RE.match(line):
            category = line.strip()[:-1].rstrip()
        elif ENTRY_RE.match(line):
            yield lineno, category, clean_entry(line)


def duplicate_warnings(lines):
    """Warnings for top-version entries that repeat an earlier entry word for word."""
    first = {}
    warnings = []
    for lineno, category, entry in top_entries(lines):
        if entry not in first:
            first[entry] = (lineno, category)
            continue
        line, where = first[entry]
        note = (
            "--fix removes it"
            if where == category
            else f"keep one of {where} and {category}"
        )
        warnings.append(f"line {lineno}: warning: duplicate of line {line}; {note}")
    return warnings


def main():
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "Changelog.txt")
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except OSError as e:
        print(f"{path}: Unreadable - {e}", file=sys.stderr)
        return 1

    errors = check_lines(lines)
    warnings = duplicate_warnings(lines)
    if not errors and order_lines(clean_lines(lines)[0]) != lines:
        warnings.append(
            "warning: run python3 tools/merge_changelog.py --fix to tidy entries"
        )
    for message in errors + warnings:
        print(f"{path}: {message}", file=sys.stderr)
    if errors:
        print(
            "\nKeep untagged entries first in each category, then [TAG] "
            "entries in alphabetical order, with one blank line between "
            "categories.\n"
            "Quick fix: python3 tools/merge_changelog.py --fix",
            file=sys.stderr,
        )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
