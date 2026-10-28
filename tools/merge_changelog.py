#!/usr/bin/env python3
"""Git merge driver and cleanup tool for Changelog.txt.

Runs a normal three-way merge, then resolves the conflicts that come from both
sides adding or extending changelog entries. Exits 1 when a conflict needs a
human, so the caller skips the merge instead of duplicating entries.

Register it as: merge_changelog.py %O %A %B
Clean and sort the top version: merge_changelog.py --fix [Changelog.txt]
Report duplicates and consolidation candidates: merge_changelog.py --preview
Fix, then write the docs page: merge_changelog.py --beta | --release NAME
"""

import argparse
import difflib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from linting.check_changelog import (
    BULLET_RE,
    CATEGORY_RE,
    ENTRY_RE,
    TAG_PREFIX_RE,
    VERSION_RE,
    WORD_RE,
    clean_lines,
    duplicate_warnings,
    order_lines,
    top_entries,
    top_version,
)

CONFLICT_RE = re.compile(r"^(?:<<<<<<< |\|{7} |=======\s*$|>>>>>>> )", re.M)
TOKEN_PATTERN = re.compile(r"\w+|\s+|[^\w\s]")
# Minimum difflib ratio for a changed line to count as an edit, not a new entry.
SIMILARITY = 0.6
ISSUE_RE = re.compile(r"#\d+")
DOCS_VERSION_RE = re.compile(r"^## v\d", re.M)
BETA_PAGE = Path("docs/src/content/misc/beta-changelogs.md")
RELEASE_DIR = Path("docs/src/content/changelogSections")
NEAR_DUPLICATE = 0.9
# Shortest entry text that counts as contained in a longer entry.
CONTAINED_LENGTH = 30
PHRASE_WORDS = 5
PHRASE_ENTRIES = 3


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


def _split(entry):
    """Tags and text of a cleaned entry."""
    text = entry[3:]
    prefix = TAG_PREFIX_RE.match(text)
    if not prefix:
        return [], text
    return WORD_RE.findall(prefix.group()), text[prefix.end() :]


def _keep(entries):
    """The tags and issue references a merged entry must keep."""
    tags = [f"[{tag}]" for entry in entries for tag in _split(entry)[0]]
    issues = [issue for entry in entries for issue in ISSUE_RE.findall(entry)]
    kept = list(dict.fromkeys(tags + issues))
    return f"; keep {', '.join(kept)}" if kept else ""


def consolidation_candidates(lines):
    """Near-duplicate entries and shared phrases a human could merge into one entry."""
    entries = list(top_entries(lines))
    candidates = []
    for index, (lineno, _, entry) in enumerate(entries):
        tags, text = _split(entry)
        matcher = difflib.SequenceMatcher(None, autojunk=False)
        matcher.set_seq2(text.lower())
        for other_lineno, _, other in entries[:index]:
            other_tags, other_text = _split(other)
            if entry == other:
                continue
            pair = f"lines {other_lineno} and {lineno}"
            if text.lower() == other_text.lower() and tags != other_tags:
                combined = "/".join(
                    f"[{tag}]" for tag in dict.fromkeys(other_tags + tags)
                )
                candidates.append(
                    f"{pair}: same entry for other tags; combine as {combined} {other_text}"
                )
                continue
            shorter, longer = sorted((text.lower(), other_text.lower()), key=len)
            matcher.set_seq1(other_text.lower())
            if (len(shorter) >= CONTAINED_LENGTH and shorter in longer) or (
                matcher.real_quick_ratio() >= NEAR_DUPLICATE
                and matcher.quick_ratio() >= NEAR_DUPLICATE
                and matcher.ratio() >= NEAR_DUPLICATE
            ):
                candidates.append(
                    f"{pair}: near-duplicate entries{_keep([other, entry])}"
                )

    phrases = {}
    for lineno, category, entry in entries:
        words = WORD_RE.findall(_split(entry)[1].lower())
        for start in range(len(words) - PHRASE_WORDS + 1):
            phrase = " ".join(words[start : start + PHRASE_WORDS])
            phrases.setdefault((category, phrase), {})[lineno] = entry
    groups = []
    for (category, phrase), found in sorted(
        phrases.items(), key=lambda item: -len(item[1])
    ):
        if len(found) < PHRASE_ENTRIES:
            break
        group = next(
            (group for group in groups if group[2].keys() & found.keys()), None
        )
        if group:
            group[2].update(found)
        else:
            groups.append((category, phrase, dict(found)))
    for category, phrase, found in sorted(groups, key=lambda group: min(group[2])):
        numbers = ", ".join(str(lineno) for lineno in sorted(found))
        candidates.append(
            f'lines {numbers}: {len(found)} {category} entries share "{phrase}"; '
            f"consider one summary entry{_keep([found[line] for line in sorted(found)])}"
        )
    return candidates


def render_markdown(lines, heading):
    """The top version as a docs Markdown section: '##' heading, '###' categories, '-' lists."""
    markdown = [f"## {heading}\n"]
    for line in top_version(lines):
        text = line.strip()
        if not text or VERSION_RE.match(text.lstrip("\ufeff")):
            continue
        if CATEGORY_RE.match(line):
            markdown.append(f"\n### {text[:-1].rstrip()}\n\n")
        elif ENTRY_RE.match(line):
            markdown.append(f"- {BULLET_RE.sub('', text)}\n")
        else:
            markdown.append(f"\n{text}\n")
    return "".join(markdown)


def replace_versions(page, markdown):
    """Swap a docs page's version sections for markdown, keeping its frontmatter and intro."""
    match = DOCS_VERSION_RE.search(page)
    head = page[: match.start()] if match else page
    return f"{head.rstrip()}\n\n{markdown}"


def release_page(root, version, name):
    """Path and current text of the release page, with frontmatter for a new one."""
    major, minor = version.lstrip("v").split(".")[:2]
    slug = f"v{major}-{minor}-{re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')}"
    path = root / RELEASE_DIR / f"{slug}.md"
    if path.exists():
        return path, path.read_bytes().decode("utf-8")
    orders = [
        int(match.group(1))
        for page in (root / RELEASE_DIR).glob("*.md")
        if (
            match := re.search(
                r"^order:\s*(\d+)", page.read_text(encoding="utf-8"), re.M
            )
        )
    ]
    title = json.dumps(f"{version} '{name}'", ensure_ascii=False)
    order = max(orders, default=0) + 1
    return (
        path,
        f"---\ntitle: {title}\npage_id: changelog-{slug}\norder: {order}\n---\n",
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument(
        "--fix", action="store_true", help="Clean and sort the top version"
    )
    modes.add_argument(
        "--preview",
        action="store_true",
        help="Report duplicates and consolidation candidates without writing",
    )
    modes.add_argument(
        "--beta", action="store_true", help="Fix, then update the beta changelog page"
    )
    modes.add_argument(
        "--release", metavar="NAME", help="Fix, then write the NAME release page"
    )
    parser.add_argument("paths", nargs="*", metavar="PATH")
    args = parser.parse_args()
    cleanup = args.fix or args.preview or args.beta or args.release is not None
    if cleanup and len(args.paths) > 1:
        parser.error("cleanup modes accept at most one changelog path")
    if not cleanup and len(args.paths) != 3:
        parser.error("merge driver requires BASE OURS THEIRS")
    if args.release is not None and not re.search(r"[A-Za-z0-9]", args.release):
        parser.error("--release needs a release name")
    removed = []
    try:
        if cleanup:
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
        lines = merged.splitlines(keepends=True)
        if args.preview:
            for message in duplicate_warnings(lines) + consolidation_candidates(lines):
                print(f"{ours}: {message}")
            return 0
        if cleanup:
            lines, removed = clean_lines(lines)
        lines = order_lines(lines)
        page = None
        if args.beta or args.release is not None:
            version = next(
                (
                    line.strip().lstrip("\ufeff")
                    for line in top_version(lines)
                    if VERSION_RE.match(line.lstrip("\ufeff"))
                ),
                None,
            )
            if version is None:
                print("Add a version heading before writing docs.", file=sys.stderr)
                return 1
            if args.beta:
                page = ours.parent / BETA_PAGE
                heading = version
                text = page.read_bytes().decode("utf-8")
            else:
                page, text = release_page(ours.parent, version, args.release)
                heading = f'{version} - "{args.release}"'
            text = replace_versions(text, render_markdown(lines, heading))
        ours.write_bytes("".join(lines).encode("utf-8"))
        if page:
            page.write_bytes(text.encode("utf-8"))
    except (OSError, UnicodeError) as error:
        print(f"Cannot update changelog: {error}", file=sys.stderr)
        return 1
    if cleanup:
        for entry in removed:
            print(
                f"{ours}: warning: removed duplicate entry: {entry[3:]}",
                file=sys.stderr,
            )
        for message in duplicate_warnings(lines):
            print(f"{ours}: {message}", file=sys.stderr)
        print(f"Fixed changelog: {ours}")
    if page:
        print(f"Updated changelog page: {page}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
