#!/usr/bin/env python3
"""Simplify redundant OR and AND wrapper blocks.

For every .txt file under the worktree:
  - OR = { single_cond } → bare condition (OR with one branch is meaningless)
  - AND = { ... } outside OR context → contents promoted to parent scope
    (AND is the default scope everywhere except inside OR)

Handles all formatting variants:
  - Standard multi-line:    OR = {\n    cond\n}
  - Inline:                 OR = { cond }
  - Tab-after-brace:        OR = {\\tcond\\n}
  - Nested block condition: OR = {\\n    NOT = {\\n        ...\\n    }\\n}

AND cleanup respects OR context: AND = { A B } inside OR = { } is kept
because it groups A and B as a single OR branch.

Run tools/cleanup_or.py from the repo root to process all files, or pass
explicit file paths as arguments to process only those files.
"""

import os
import re
import sys

# ---------------------------------------------------------------------------
# Core OR-block parsing helpers (also imported by check_common_mistakes.py)
# ---------------------------------------------------------------------------


def _tokenize_inner(text):
    """Tokenize HOI4 script text, stripping comments.

    Returns list of token strings: identifier-like words, '=', '{', '}'.
    """
    tokens = []
    for line in text.splitlines():
        code = line.split("#")[0]
        for tok in re.findall(r"[{}=]|[^\s{}=#]+", code):
            tokens.append(tok)
    return tokens


def _count_top_level_conditions(tokens):
    """Count top-level key=value conditions in a flat token list.

    Each condition is: word '=' (word | '{' ... '}').
    Nested blocks are consumed as a single condition.
    """
    depth = 0
    count = 0
    i = 0
    n = len(tokens)
    while i < n:
        tok = tokens[i]
        if tok == "{":
            depth += 1
            i += 1
        elif tok == "}":
            depth -= 1
            i += 1
        elif depth == 0 and tok != "=":
            # Word at top level: start of a new condition
            count += 1
            i += 1  # consume key
            if i < n and tokens[i] == "=":
                i += 1  # consume '='
                if i < n and tokens[i] == "{":
                    # Block value: skip to matching '}'
                    inner_depth = 0
                    while i < n:
                        if tokens[i] == "{":
                            inner_depth += 1
                        elif tokens[i] == "}":
                            inner_depth -= 1
                            if inner_depth == 0:
                                i += 1
                                break
                        i += 1
                elif i < n and tokens[i] != "}":
                    i += 1  # consume simple value
        else:
            i += 1
    return count


def _extract_inner_text(block_lines):
    """Return the text between the outermost { and } of a collected OR block."""
    if not block_lines:
        return ""
    if len(block_lines) == 1:
        line = block_lines[0]
        open_pos = line.index("{")
        close_pos = line.rindex("}")
        return line[open_pos + 1 : close_pos]
    first = block_lines[0]
    open_pos = first.index("{")
    after_open = first[open_pos + 1 :]
    last = block_lines[-1]
    close_pos = last.rfind("}")
    before_close = last[:close_pos]
    return "".join([after_open] + block_lines[1:-1] + [before_close])


def _extract_single_condition_lines(inner_text, or_indent):
    """Given inner_text of a single-condition OR block, return replacement lines.

    Strips the extra indentation level and re-applies or_indent, preserving
    the relative indentation of multi-line (nested block) conditions.
    """
    content_lines = [
        ln
        for ln in inner_text.splitlines(keepends=True)
        if ln.strip() and not ln.strip().startswith("#")
    ]
    if not content_lines:
        return []
    if len(content_lines) == 1:
        return [or_indent + content_lines[0].strip() + "\n"]
    # Multi-line: re-base indentation from cond_indent to or_indent
    first = content_lines[0]
    cond_indent = first[: len(first) - len(first.lstrip())]
    result = []
    for ln in content_lines:
        if ln.startswith(cond_indent):
            result.append(or_indent + ln[len(cond_indent) :])
        else:
            result.append(ln)
    if not result[-1].endswith("\n"):
        result[-1] += "\n"
    return result


def _collect_or_block(lines, start):
    """Collect all lines belonging to the OR = { } block starting at start.

    Returns (block_lines, next_index) where next_index is the first line
    after the block.
    """
    line = lines[start]
    block_lines = [line]
    depth = 1
    after_brace = re.sub(r"^.*OR\s*=\s*\{", "", line, count=1).split("#")[0]
    depth += after_brace.count("{") - after_brace.count("}")
    j = start + 1
    while depth > 0 and j < len(lines):
        l = lines[j]
        block_lines.append(l)
        code = l.split("#")[0]
        depth += code.count("{") - code.count("}")
        j += 1
    return block_lines, j


def _collect_block(lines, start):
    """Collect all lines of any brace-delimited block starting at lines[start].

    Unlike _collect_or_block this works for ANY block type (AND, NOT, etc.)
    because it counts braces from the full opening line rather than stripping
    an OR-specific prefix first.

    Returns (block_lines, next_index).
    """
    code = lines[start].split("#")[0]
    depth = code.count("{") - code.count("}")
    block_lines = [lines[start]]
    j = start + 1
    while depth > 0 and j < len(lines):
        l = lines[j]
        block_lines.append(l)
        code = l.split("#")[0]
        depth += code.count("{") - code.count("}")
        j += 1
    return block_lines, j


# ---------------------------------------------------------------------------
# Inline OR handling  (OR = { cond } all on one line, embedded in other blocks)
# ---------------------------------------------------------------------------

_RE_INLINE_OR = re.compile(r"\bOR\s*=\s*\{([^{}]+)\}")


def _fix_inline_or_line(line):
    """Replace all inline OR = { single_cond } occurrences within a single line.

    Only replaces when the content between the braces is exactly one condition.
    Handles lines with trailing comments by splitting on # first.
    """
    comment_pos = line.find("#")
    if comment_pos >= 0:
        code, comment = line[:comment_pos], line[comment_pos:]
    else:
        code, comment = line, ""

    def _replace(m):
        inner = m.group(1)
        tokens = _tokenize_inner(inner)
        if _count_top_level_conditions(tokens) == 1:
            return inner.strip()
        return m.group(0)

    new_code = _RE_INLINE_OR.sub(_replace, code)
    return new_code + comment


# ---------------------------------------------------------------------------
# AND block helpers
# ---------------------------------------------------------------------------

_RE_AND_OPEN = re.compile(r"^\s*AND\s*=\s*\{")
_RE_OR_BLOCK_OPEN = re.compile(r"^\s*OR\s*=\s*\{")


def _extract_all_inner_lines(inner_text, target_indent):
    """Extract all content lines from inside an AND block, rebased to target_indent.

    Blank lines and leading/trailing whitespace-only lines are stripped.
    Comments are preserved.
    """
    raw = inner_text.splitlines(keepends=True)

    # Find base indentation from the first non-blank line
    base_indent = None
    for ln in raw:
        if ln.strip():
            base_indent = ln[: len(ln) - len(ln.lstrip())]
            break

    if base_indent is None:
        return []

    result = []
    for ln in raw:
        if not ln.strip():
            continue
        if ln.startswith(base_indent):
            result.append(target_indent + ln[len(base_indent) :])
        else:
            result.append(ln)

    if result and not result[-1].endswith("\n"):
        result[-1] += "\n"
    return result


def _simplify_and_single_pass(lines):
    """Single pass: remove AND = { } wrappers that are not in OR context.

    AND is HOI4's default scope.  It is only meaningful inside OR = { }
    blocks, where it groups several conditions as one OR branch.  Elsewhere
    the wrapper adds noise without changing semantics.

    When an AND block is removed its content is promoted to the parent
    indentation level.  The brace-context stack is NOT updated for removed
    AND blocks because AND = { ... } always has net-zero brace effect.
    """
    out = []
    i = 0
    n = len(lines)
    # Stack of bools: True = this brace depth was opened by OR = {
    block_is_or = [False]

    while i < n:
        line = lines[i]
        code = line.split("#")[0]

        if _RE_AND_OPEN.match(line):
            in_or = block_is_or[-1]
            if not in_or:
                and_indent = line[: len(line) - len(line.lstrip())]
                block_lines, j = _collect_block(lines, i)
                inner = _extract_inner_text(block_lines)
                out.extend(_extract_all_inner_lines(inner, and_indent))
                i = j
                # Stack unchanged: net brace effect of the AND block is 0
                continue

        # Track which brace depths are OR blocks
        is_or = bool(_RE_OR_BLOCK_OPEN.match(line))
        opens = code.count("{")
        closes = code.count("}")
        out.append(line)
        for k in range(opens):
            block_is_or.append(True if (is_or and k == 0) else False)
        for _ in range(closes):
            if len(block_is_or) > 1:
                block_is_or.pop()

        i += 1

    return out


def simplify_and_block(lines):
    """Remove redundant AND = { } wrappers (not inside OR context).

    Runs multiple passes until stable so nested redundant ANDs are
    all removed (outer pass exposes inner AND blocks for the next pass).
    """
    current = lines
    while True:
        result = _simplify_and_single_pass(current)
        if result == current:
            break
        current = result
    return current


# ---------------------------------------------------------------------------
# Detection helper (used by check_common_mistakes.py)
# ---------------------------------------------------------------------------


def find_single_condition_or_blocks(lines):
    """Return list of (line_num, message) for redundant single-condition OR blocks.

    line_num is 1-based to match the convention in check_common_mistakes.py.
    Detects both line-start OR blocks and inline OR = { cond } on any line.
    """
    issues = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if re.match(r"^\s*OR\s*=\s*\{", line):
            block_lines, j = _collect_or_block(lines, i)
            inner = _extract_inner_text(block_lines)
            tokens = _tokenize_inner(inner)
            if _count_top_level_conditions(tokens) == 1:
                issues.append(
                    (
                        i + 1,
                        "redundant OR = { } wrapper around single condition"
                        " -- run tools/cleanup_or.py to fix",
                    )
                )
            i = j
        else:
            code = line.split("#")[0]
            for m in _RE_INLINE_OR.finditer(code):
                tokens = _tokenize_inner(m.group(1))
                if _count_top_level_conditions(tokens) == 1:
                    issues.append(
                        (
                            i + 1,
                            "redundant OR = { } wrapper around single condition"
                            " -- run tools/cleanup_or.py to fix",
                        )
                    )
                    break
            i += 1
    return issues


def find_redundant_and_blocks(lines):
    """Return list of (line_num, message) for redundant AND = { } blocks.

    Detects AND blocks that are not inside an OR context.  line_num is 1-based.
    Only the outermost redundant AND at each location is reported (inner ones
    are revealed after the outer is fixed by cleanup_or.py).
    """
    issues = []
    i = 0
    n = len(lines)
    block_is_or = [False]

    while i < n:
        line = lines[i]
        code = line.split("#")[0]

        if _RE_AND_OPEN.match(line):
            in_or = block_is_or[-1]
            if not in_or:
                issues.append(
                    (
                        i + 1,
                        "redundant AND = { } wrapper (AND is the default scope)"
                        " -- run tools/cleanup_or.py to fix",
                    )
                )
            # Skip past the block; net brace effect is 0 so stack is unchanged
            _, j = _collect_block(lines, i)
            i = j
            continue

        is_or = bool(_RE_OR_BLOCK_OPEN.match(line))
        opens = code.count("{")
        closes = code.count("}")
        for k in range(opens):
            block_is_or.append(True if (is_or and k == 0) else False)
        for _ in range(closes):
            if len(block_is_or) > 1:
                block_is_or.pop()

        i += 1

    return issues


# ---------------------------------------------------------------------------
# File transformation
# ---------------------------------------------------------------------------


def simplify_or_block(lines):
    """Return lines with all single-condition OR = { } wrappers removed.

    Two passes:
    1. Line-start OR blocks (multi-line or inline-after-OR-keyword).
    2. Inline OR = { cond } embedded within other constructs on the same line.
    """
    # Pass 1: line-start OR blocks
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not re.match(r"^\s*OR\s*=\s*\{", line):
            out.append(line)
            i += 1
            continue
        or_indent = line[: len(line) - len(line.lstrip())]
        block_lines, j = _collect_or_block(lines, i)
        inner = _extract_inner_text(block_lines)
        tokens = _tokenize_inner(inner)
        if _count_top_level_conditions(tokens) == 1:
            out.extend(_extract_single_condition_lines(inner, or_indent))
        else:
            out.extend(block_lines)
        i = j

    # Pass 2: inline OR = { cond } on any line
    return [_fix_inline_or_line(ln) for ln in out]


def process_file(filepath):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    # OR cleanup first so OR = { AND = { A B } } chains fully collapse
    new_lines = simplify_or_block(lines)
    new_lines = simplify_and_block(new_lines)
    if new_lines != lines:
        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        return True
    return False


def main(paths):
    """Process paths: directories are walked recursively, files are processed directly."""
    changed = []
    for path in paths:
        if os.path.isdir(path):
            for dirpath, _, filenames in os.walk(path):
                for fn in filenames:
                    if fn.lower().endswith(".txt"):
                        full = os.path.join(dirpath, fn)
                        if process_file(full):
                            changed.append(os.path.relpath(full, path))
        elif os.path.isfile(path):
            if process_file(path):
                changed.append(path)
    if changed:
        print("Simplified OR blocks in:")
        for p in changed:
            print(" -", p)
    else:
        print("No single-condition OR blocks found.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1:])
    else:
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        main([root])
