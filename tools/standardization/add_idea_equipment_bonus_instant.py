"""Add instant = yes to equipment bonuses in idea files without reformatting them."""

import argparse
import glob
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "validation"))

from equipment_module_slots import _iter_blocks, blank_comments
from shared_utils import atomic_write_text, find_matching_brace
from validate_ideas import _EQUIPMENT_BONUS_START, _INSTANT_YES

_INSTANT_KEY = re.compile(r"\binstant\s*=")


def add_instant(text: str) -> tuple[str, int]:
    clean = blank_comments(text)
    inserts: list[tuple[int, str]] = []
    for match in _EQUIPMENT_BONUS_START.finditer(clean):
        close = find_matching_brace(clean, match.end() - 1)
        if close == -1:
            raise ValueError("unclosed equipment_bonus")
        for name, lo, hi, _header in _iter_blocks(clean, match.end(), close):
            if _INSTANT_YES.search(clean, lo, hi):
                continue
            if _INSTANT_KEY.search(clean, lo, hi):
                raise ValueError(f"unexpected instant value for {name}")
            last_newline = text.rfind("\n", lo, hi)
            if last_newline == -1 or text[last_newline + 1 : hi].strip():
                inserts.append((lo + len(text[lo:hi].rstrip()), " instant = yes"))
            else:
                indent = text[last_newline + 1 : hi]
                inserts.append((last_newline + 1, indent + "\tinstant = yes\n"))
    for offset, insertion in reversed(inserts):
        text = text[:offset] + insertion + text[offset:]
    return text, len(inserts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "files", nargs="*", help="Idea files (default: common/ideas/**)"
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    root = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
    files = args.files or sorted(
        glob.iglob(os.path.join(root, "common", "ideas", "**", "*.txt"), recursive=True)
    )
    changes = []
    ideas_dir = os.path.realpath(os.path.join(root, "common", "ideas"))
    for path in files:
        if os.path.commonpath((ideas_dir, os.path.realpath(path))) != ideas_dir:
            parser.error(f"not an idea file: {path}")
        try:
            with open(path, encoding="utf-8", newline="") as handle:
                text = handle.read()
            updated, count = add_instant(text)
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            parser.error(f"{path}: {exc}")
        if count:
            changes.append((path, updated, count))
    for path, updated, count in changes:
        print(f"{os.path.relpath(path, root)}: {count}")
        if not args.dry_run:
            atomic_write_text(path, updated)
    total = sum(count for _, _, count in changes)
    print(
        f"{'Would add' if args.dry_run else 'Added'} instant = yes to {total} entries"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
