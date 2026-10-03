#!/usr/bin/env python3
"""Git merge driver for Changelog.txt.

Runs a normal three-way merge, then resolves the conflicts that come from both
sides adding or extending changelog entries. Exits 1 when a conflict needs a
human, so the caller skips the merge instead of duplicating entries.

Register it as: merge_changelog.py %O %A %B
Fix top-version ordering: merge_changelog.py --fix [Changelog.txt]
"""

import argparse
import difflib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from linting.check_changelog import CATEGORY_RE, order_lines, top_version

CONFLICT_RE = re.compile(r"^(?:<<<<<<< |\|{7} |=======\s*$|>>>>>>> )", re.M)
TOKEN_PATTERN = re.compile(r"\w+|\s+|[^\w\s]")
# Minimum difflib ratio for a changed line to count as an edit, not a new entry.
SIMILARITY = 0.6


def _edits(base, other):
    matcher = difflib.SequenceMatcher(None, base, other, autojunk=False)
    return [
        (i1, i2, other[j1:j2])
        for tag, i1, i2, j1, j2 in matcher.get_opcodes()
        if tag != "equal"
    ]


def _join_inserts(first, second):
    """Join two insertions at one spot, dropping one that the other already contains."""
    for outer, inner in ((first, second), (second, first)):
        if any(
            outer[start : start + len(inner)] == inner
            for start in range(len(outer) - len(inner) + 1)
        ):
            return outer
    return first + second


def merge_sequences(base, ours, theirs):
    """Apply both sides' edits to base; None when they touch or border each other.

    Insertions at the same spot are both kept, ours first, unless one contains the other.
    """
    edits = []
    for side, other in enumerate((ours, theirs)):
        edits.extend((i1, i2, side, items) for i1, i2, items in _edits(base, other))
    edits.sort(key=lambda edit: edit[:3])

    merged = []
    position = 0
    previous = None
    inserted_at = None
    inserted = []
    for i1, i2, _side, items in edits:
        if previous == (i1, i2, items):
            continue
        if inserted_at == i1 == i2:
            del merged[len(merged) - len(inserted) :]
            items = _join_inserts(inserted, items)
        elif previous is not None and i1 <= position:
            return None
        merged.extend(base[position:i1])
        merged.extend(items)
        position = i2
        previous = (i1, i2, items)
        inserted_at, inserted = (i1, items) if i1 == i2 else (None, [])
    merged.extend(base[position:])
    return merged


def merge_line(base, ours, theirs):
    """Merge two edits of one entry; when both sides changed it, both may only add words."""
    base, ours, theirs = (TOKEN_PATTERN.findall(line) for line in (base, ours, theirs))
    if (
        ours != base
        and theirs != base
        and any(
            i1 != i2 for side in (ours, theirs) for i1, i2, _items in _edits(base, side)
        )
    ):
        return None
    merged = merge_sequences(base, ours, theirs)
    return None if merged is None else "".join(merged)


def _similarity(first, second):
    return difflib.SequenceMatcher(
        None, first.strip(), second.strip(), autojunk=False
    ).ratio()


def _align(base, other):
    """Pair base lines with their kept or edited version on the other side.

    Returns base index -> other index, plus the other side's unpaired indexes.
    """
    pairs = {}
    added = []
    matcher = difflib.SequenceMatcher(None, base, other, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            pairs.update(zip(range(i1, i2), range(j1, j2)))
            continue
        start = j1
        for i in range(i1, i2):
            scores = [(_similarity(base[i], other[j]), j) for j in range(start, j2)]
            score, j = max(scores, key=lambda item: item[0], default=(0, None))
            if j is None or score < SIMILARITY:
                continue
            added.extend(range(start, j))
            pairs[i] = j
            start = j + 1
        added.extend(range(start, j2))
    return pairs, added


def _categories(lines):
    """Category heading each line sits under; None before the hunk's first heading."""
    category = None
    categories = []
    for line in lines:
        if CATEGORY_RE.match(line):
            category = line.strip()
        categories.append(category)
    return categories


def _category_end(lines, category):
    """Index after a top-version category's last line; None when the category is missing."""
    end = None
    for index, line in enumerate(top_version(lines)):
        if CATEGORY_RE.match(line):
            if end is not None:
                break
            if line.strip() == category:
                end = index + 1
        elif end is not None and line.strip():
            end = index + 1
    return end


def resolve_hunk(base, ours, theirs):
    """Resolve one conflict hunk, keeping main's lines and adding the PR's.

    A PR entry joins the category it sat under in the PR. Returns the hunk's lines
    and the (category, entry) pairs whose category main moved out of the hunk.
    """
    our_pairs, _ = _align(base, ours)
    their_pairs, their_added = _align(base, theirs)
    merged = list(ours)
    for base_index, base_line in enumerate(base):
        our_index = our_pairs.get(base_index)
        their_index = their_pairs.get(base_index)
        if their_index is None:
            if our_index is not None:
                if ours[our_index] != base_line:
                    return None
                merged[our_index] = None
            continue
        if our_index is None:
            if theirs[their_index] != base_line:
                return None
            continue
        line = merge_line(base_line, merged[our_index], theirs[their_index])
        if line is None:
            return None
        merged[our_index] = line

    our_categories = _categories(ours)
    their_categories = _categories(theirs)
    # Where each of main's categories ends inside the hunk, before its trailing blanks.
    ends = {None: 0}
    for index, line in enumerate(ours):
        if line.strip():
            ends[our_categories[index]] = index + 1

    new_categories = {
        theirs[index].strip()
        for index in their_added
        if CATEGORY_RE.match(theirs[index])
    }

    their_bases = {j: i for i, j in their_pairs.items()}
    present = {line.strip() for line in merged if line and line.strip()}
    before = {}
    moved = []
    for index in their_added:
        line = theirs[index]
        if line.strip() in present:
            continue
        if line.strip():
            present.add(line.strip())
        # Keep the PR's line ahead of the next entry it already shared with base.
        anchor = next(
            (
                our_pairs[their_bases[j]]
                for j in range(index + 1, len(theirs))
                if their_bases.get(j) in our_pairs
            ),
            len(merged),
        )
        category = their_categories[index]
        if line.strip() and not CATEGORY_RE.match(line):
            if category in ends:
                landing = our_categories[anchor - 1] if anchor else None
                if landing != category or anchor > ends[category]:
                    anchor = ends[category]
            elif category not in new_categories:
                moved.append((category, line))
                continue
        before.setdefault(anchor, []).append(line)

    result = []
    for index, line in enumerate(merged + [None]):
        added = before.get(index, [])
        # A blank line the PR added only matters next to its own new lines.
        if any(item.strip() for item in added):
            result.extend(added)
        if line is not None:
            result.append(line)
    return result, moved


def merge_text(base, ours, theirs):
    """Three-way merge of changelog text; None when a conflict stays unresolved."""
    with tempfile.TemporaryDirectory() as folder:
        paths = []
        for name, text in (("ours", ours), ("base", base), ("theirs", theirs)):
            path = Path(folder) / name
            path.write_bytes(text.encode("utf-8"))
            paths.append(str(path))
        result = subprocess.run(
            ["git", "merge-file", "-p", "--diff3"]
            + ["-L", "ours", "-L", "base", "-L", "theirs", *paths],
            capture_output=True,
            check=False,
        )
    if result.returncode < 0 or result.returncode > 127:
        return None
    output = result.stdout.decode("utf-8")
    if result.returncode == 0:
        return output

    merged = []
    moved = []
    hunk = None
    section = 0
    for line in output.splitlines(keepends=True):
        marker = line.rstrip("\r\n")
        if hunk is None:
            if marker == "<<<<<<< ours":
                hunk = ([], [], [])
                section = 0
            else:
                merged.append(line)
        elif marker == "||||||| base":
            section = 1
        elif marker == "=======":
            section = 2
        elif marker == ">>>>>>> theirs":
            resolved = resolve_hunk(hunk[1], hunk[0], hunk[2])
            if resolved is None:
                return None
            merged.extend(resolved[0])
            moved.extend(resolved[1])
            hunk = None
        else:
            hunk[section].append(line)
    for category, line in moved:
        end = _category_end(merged, category)
        if end is None:
            return None
        merged.insert(end, line)
    return "".join(merged)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fix", action="store_true", help="Fix top-version ordering")
    parser.add_argument("paths", nargs="*", metavar="PATH")
    args = parser.parse_args()
    if args.fix and len(args.paths) > 1:
        parser.error("--fix accepts at most one changelog path")
    if not args.fix and len(args.paths) != 3:
        parser.error("merge driver requires BASE OURS THEIRS")
    try:
        if args.fix:
            ours = Path(args.paths[0] if args.paths else "Changelog.txt")
            merged = ours.read_bytes().decode("utf-8")
        else:
            base, ours, theirs = (Path(arg) for arg in args.paths)
            merged = merge_text(
                *(path.read_bytes().decode("utf-8") for path in (base, ours, theirs))
            )
        if merged is None:
            return 1
        if CONFLICT_RE.search(merged):
            print("Resolve changelog conflict markers before sorting.", file=sys.stderr)
            return 1
        ordered = "".join(order_lines(merged.splitlines(keepends=True)))
        ours.write_bytes(ordered.encode("utf-8"))
    except (OSError, UnicodeError) as error:
        print(f"Cannot update changelog: {error}", file=sys.stderr)
        return 1
    if args.fix:
        print(f"Fixed changelog ordering: {ours}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
