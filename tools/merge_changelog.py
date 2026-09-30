#!/usr/bin/env python3
"""Git merge driver for Changelog.txt.

Runs a normal three-way merge, then resolves the conflicts that come from both
sides adding or extending changelog entries. Exits 1 when a conflict needs a
human, so the caller skips the merge instead of duplicating entries.

Register it as: merge_changelog.py %O %A %B
"""

import difflib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

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


def merge_sequences(base, ours, theirs):
    """Apply both sides' edits to base; None when they touch or border each other.

    Insertions at the same spot are both kept, ours first.
    """
    edits = []
    for side, other in enumerate((ours, theirs)):
        edits.extend((i1, i2, side, items) for i1, i2, items in _edits(base, other))
    edits.sort(key=lambda edit: edit[:3])

    merged = []
    position = 0
    previous = None
    previous_insert = None
    for i1, i2, _side, items in edits:
        if previous == (i1, i2, items):
            continue
        if previous is not None and (
            i1 < position or (i1 == position and not previous_insert == i1 == i2)
        ):
            return None
        merged.extend(base[position:i1])
        merged.extend(items)
        position = i2
        previous = (i1, i2, items)
        previous_insert = i1 if i1 == i2 else None
    merged.extend(base[position:])
    return merged


def merge_line(base, ours, theirs):
    merged = merge_sequences(
        TOKEN_PATTERN.findall(base),
        TOKEN_PATTERN.findall(ours),
        TOKEN_PATTERN.findall(theirs),
    )
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
            if score < SIMILARITY:
                continue
            added.extend(range(start, j))
            pairs[i] = j
            start = j + 1
        added.extend(range(start, j2))
    return pairs, added


def resolve_hunk(base, ours, theirs):
    """Resolve one conflict hunk, keeping main's lines and adding the PR's."""
    our_pairs, _ = _align(base, ours)
    their_pairs, their_added = _align(base, theirs)
    merged = list(ours)
    for base_index, base_line in enumerate(base):
        our_index = our_pairs.get(base_index)
        their_index = their_pairs.get(base_index)
        if their_index is None:
            if our_index is not None:
                return None
            continue
        if our_index is None:
            if theirs[their_index] != base_line:
                return None
            continue
        line = merge_line(base_line, merged[our_index], theirs[their_index])
        if line is None:
            return None
        merged[our_index] = line

    present = {line.strip() for line in merged if line.strip()}
    for index in their_added:
        line = theirs[index]
        if line.strip() in present:
            continue
        merged.append(line)
        if line.strip():
            present.add(line.strip())
    return merged


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
            merged.extend(resolved)
            hunk = None
        else:
            hunk[section].append(line)
    return "".join(merged)


def main():
    if len(sys.argv) != 4:
        print("usage: merge_changelog.py BASE OURS THEIRS", file=sys.stderr)
        return 2
    base, ours, theirs = (Path(arg) for arg in sys.argv[1:])
    merged = merge_text(
        *(path.read_bytes().decode("utf-8") for path in (base, ours, theirs))
    )
    if merged is None:
        return 1
    ours.write_bytes(merged.encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
