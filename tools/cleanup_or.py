#!/usr/bin/env python3

"""Simplify OR blocks with a single condition.

For every .txt file under the worktree, this script finds blocks of the form:

    OR = {\n        <condition>\n    }

where <condition> is a single non‑blank line (ignoring comments and whitespace).
If such a block is found it is replaced with the inner line, removing the OR wrapper.
The script preserves the original indentation level.
"""

import os
import re
import sys


def simplify_or_block(lines):
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if re.match(r"^\s*OR\s*=\s*{", line):
            indent = line[: line.find("OR")]
            block = []
            brace_depth = 0
            while i < len(lines):
                l = lines[i]
                brace_depth += l.count("{") - l.count("}")
                block.append(l)
                i += 1
                if brace_depth == 0:
                    break
            inner = [
                ln.strip()
                for ln in block[1:-1]
                if ln.strip() and not ln.strip().startswith("#")
            ]
            if len(inner) == 1:
                out.append(f"{indent}{inner[0]}\n")
                continue
            else:
                out.extend(block)
                continue
        else:
            out.append(line)
            i += 1
    return out


def process_file(filepath):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    new_lines = simplify_or_block(lines)
    if new_lines != lines:
        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        return True
    return False


def main(root_dir):
    changed = []
    for dirpath, _, filenames in os.walk(root_dir):
        for fn in filenames:
            if fn.lower().endswith(".txt"):
                full = os.path.join(dirpath, fn)
                if process_file(full):
                    changed.append(os.path.relpath(full, root_dir))
    if changed:
        print("Simplified OR blocks in:")
        for p in changed:
            print(" -", p)
    else:
        print("No single‑condition OR blocks found.")


if __name__ == "__main__":
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    main(root)
