#!/usr/bin/env python3
"""Collapse redundant effect_tooltip wrappers around pure custom_effect_tooltip.

`effect_tooltip = { ... }` DISPLAYS real effects without executing them. When a
block's only content is one or more `custom_effect_tooltip = KEY` lines (a plain
display string, no real effect), the wrapper does nothing and is removed:

    effect_tooltip = { custom_effect_tooltip = X }   ->   custom_effect_tooltip = X

    effect_tooltip = {                                    custom_effect_tooltip = X
        custom_effect_tooltip = X               ->
    }

Blocks that wrap a real effect (annex_country, country_event, transfer_state,
add_*/set_*, variable ops, ...) are left untouched, and so are empty
effect_tooltip = { } blocks and any block carrying an inline comment.

Run from the repo root:
    tools/cleanup_effect_tooltip.py <path> [<path> ...]   # explicit files/dirs
    tools/cleanup_effect_tooltip.py --all                 # whole repo (resources/ excluded)
    tools/cleanup_effect_tooltip.py --check <path>        # report only, do not write
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Reuse the block-parsing helpers cleanup_or already shares with
# check_common_mistakes.py rather than re-implementing brace matching.
from cleanup_or import (  # noqa: E402
    _collect_block,
    _extract_inner_text,
    _tokenize_inner,
)
from shared_utils import strip_inline_comment  # noqa: E402

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# resources/ is reference-only; .git is not content; .claude/worktrees holds full
# sibling checkouts that belong to other branches and must never be rewritten.
_EXCLUDED_DIRS = frozenset({"resources", ".git", ".claude"})


def _is_excluded_path(path, repo_root=None):
    """True if path is under an excluded dir, matched relative to the repo root.

    Matching is against the path relative to the repo root, not the absolute
    path: a checkout nested under an ancestor dir literally named `resources`
    would otherwise match every file and no-op the whole repo.
    """
    root = _REPO_ROOT if repo_root is None else os.path.abspath(repo_root)
    rel = os.path.relpath(os.path.abspath(path), root)
    return any(part in _EXCLUDED_DIRS for part in rel.split(os.sep))


_RE_EFFECT_TOOLTIP_OPEN = re.compile(r"^\s*effect_tooltip\s*=\s*\{")
# Inline form has no nested braces (custom_effect_tooltip = KEY never opens one).
_RE_INLINE_EFFECT_TOOLTIP = re.compile(r"\beffect_tooltip\s*=\s*\{([^{}]*)\}")


def _custom_tooltip_keys(inner):
    """Keys of a block that is ONLY custom_effect_tooltip statements, else None.

    Returns the list of loc KEYs (>= 1) when the block holds nothing but
    `custom_effect_tooltip = KEY` statements; returns None for a real effect, an
    empty block, a block-valued tooltip, or a block with a comment (whose text
    the token-based rebuild would silently drop).
    """
    if "#" in inner:
        return None
    tokens = _tokenize_inner(inner)
    if not tokens:
        return None
    keys = []
    i = 0
    n = len(tokens)
    while i < n:
        if (
            tokens[i] == "custom_effect_tooltip"
            and i + 2 < n
            and tokens[i + 1] == "="
            and tokens[i + 2] not in ("{", "}", "=")
        ):
            keys.append(tokens[i + 2])
            i += 3
        else:
            return None
    return keys or None


def _fix_inline_line(line):
    """Collapse inline effect_tooltip = { custom_effect_tooltip = X } on one line.

    Returns (new_line, num_collapsed). Comments are split off first so a `#`
    inside a trailing comment can't be mistaken for block content.
    """
    code = strip_inline_comment(line)
    comment = line[len(code) :]
    count = [0]

    def _replace(m):
        keys = _custom_tooltip_keys(m.group(1))
        if keys is None:
            return m.group(0)
        count[0] += 1
        return " ".join(f"custom_effect_tooltip = {k}" for k in keys)

    new_code = _RE_INLINE_EFFECT_TOOLTIP.sub(_replace, code)
    return new_code + comment, count[0]


def simplify_effect_tooltip_block(lines):
    """Return (new_lines, num_collapsed) with redundant wrappers removed.

    Pass 1 handles line-start effect_tooltip blocks (single- or multi-line);
    pass 2 catches any inline effect_tooltip = { ... } embedded mid-line.
    """
    out = []
    collapsed = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        if not _RE_EFFECT_TOOLTIP_OPEN.match(line):
            out.append(line)
            i += 1
            continue
        indent = line[: len(line) - len(line.lstrip())]
        block_lines, j = _collect_block(lines, i)
        keys = _custom_tooltip_keys(_extract_inner_text(block_lines))
        if keys is not None:
            out.extend(f"{indent}custom_effect_tooltip = {k}\n" for k in keys)
            collapsed += 1
        else:
            out.extend(block_lines)
        i = j

    new = []
    for ln in out:
        fixed, c = _fix_inline_line(ln)
        new.append(fixed)
        collapsed += c
    return new, collapsed


def find_redundant_effect_tooltip_wrappers(lines):
    """Return list of (line_num, message) for redundant wrappers (1-based).

    Detection twin of the fixer, for a validator to import without rewriting.
    """
    issues = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if _RE_EFFECT_TOOLTIP_OPEN.match(line):
            block_lines, j = _collect_block(lines, i)
            if _custom_tooltip_keys(_extract_inner_text(block_lines)) is not None:
                issues.append(
                    (
                        i + 1,
                        "redundant effect_tooltip = { } wrapper around a plain"
                        " custom_effect_tooltip -- run tools/cleanup_effect_tooltip.py",
                    )
                )
            i = j
        else:
            code = strip_inline_comment(line)
            for m in _RE_INLINE_EFFECT_TOOLTIP.finditer(code):
                if _custom_tooltip_keys(m.group(1)) is not None:
                    issues.append(
                        (
                            i + 1,
                            "redundant effect_tooltip = { } wrapper around a plain"
                            " custom_effect_tooltip -- run tools/cleanup_effect_tooltip.py",
                        )
                    )
                    break
            i += 1
    return issues


def process_file(filepath, check_only=False):
    # Read strict: silently dropping undecodable bytes would write mangled text
    # back and corrupt the file.
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except UnicodeDecodeError as e:
        print(f"ERROR: {filepath}: undecodable UTF-8, skipping ({e})", file=sys.stderr)
        return 0
    new_lines, collapsed = simplify_effect_tooltip_block(lines)
    if collapsed and not check_only and new_lines != lines:
        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
    return collapsed


def main(paths, check_only=False):
    """Process paths: directories are walked recursively, files processed directly."""
    total = 0
    changed = []
    for path in paths:
        if _is_excluded_path(path):
            print(
                f"SKIP: {path} is under an excluded directory (resources/, .git); not modified",
                file=sys.stderr,
            )
            continue
        if os.path.isdir(path):
            for dirpath, dirnames, filenames in os.walk(path):
                dirnames[:] = [d for d in dirnames if d not in _EXCLUDED_DIRS]
                for fn in filenames:
                    if fn.lower().endswith(".txt"):
                        full = os.path.join(dirpath, fn)
                        c = process_file(full, check_only)
                        if c:
                            changed.append((os.path.relpath(full, path), c))
                            total += c
        elif os.path.isfile(path):
            c = process_file(path, check_only)
            if c:
                changed.append((path, c))
                total += c
    verb = "Would collapse" if check_only else "Collapsed"
    if changed:
        print(
            f"{verb} {total} redundant effect_tooltip wrapper(s) in {len(changed)} file(s):"
        )
        for p, c in sorted(changed):
            print(f" - {c:4d}  {p}")
    else:
        print("No redundant effect_tooltip wrappers found.")
    return total


if __name__ == "__main__":
    argv = sys.argv[1:]
    check_only = "--check" in argv
    argv = [a for a in argv if a != "--check"]
    if argv == ["--all"]:
        # Repo-wide run must be explicit; resources/ is pruned by main().
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        main([root], check_only)
    elif argv:
        main(argv, check_only)
    else:
        print(
            "usage: cleanup_effect_tooltip.py [--check] <path> [<path> ...] | [--check] --all\n"
            "  Pass explicit files/dirs, or --all to scan the whole repo "
            "(resources/ is always excluded). --check reports without writing.",
            file=sys.stderr,
        )
        sys.exit(1)
