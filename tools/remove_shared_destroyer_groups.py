#!/usr/bin/env python3
"""
remove_shared_destroyer_groups.py

Removes TAG_destroyers design groups from country naval AI files that have
been consolidated into zz_shared_destroyers.txt.

Usage:
    python3 tools/remove_shared_destroyer_groups.py [--dry-run]
"""

import re
import sys
from pathlib import Path

AI_DIR = Path(__file__).parent.parent / "common" / "ai_equipment"

# Group A: Standard VLS SAM doctrine (23 countries)
# Group B: NATO high-end with asm_2 at hull_2 (8 countries)
# Group C: Baltic/Iberian reduced AAW at hull_2 (7 countries)
# Group D: West African chain-gun doctrine (3 countries)
DESTROYER_REMOVE = {
    # Group A
    "ALG",
    "AST",
    "CHI",
    "CHL",
    "EGY",
    "FIN",
    "GRE",
    "HOL",
    "IND",
    "ISR",
    "JAP",
    "KOR",
    "MOR",
    "NOR",
    "RAJ",
    "SAF",
    "SAU",
    "SIA",
    "SIN",
    "SWE",
    "TAI",
    "TUR",
    "UAE",
    # Group B
    "CAN",
    "ENG",
    "FRA",
    "GER",
    "ITA",
    "PER",
    "SPA",
    "USA",
    # Group C
    "EST",
    "LAT",
    "LIT",
    "LUX",
    "POR",
    "PRU",
    "UKR",
    # Group D
    "GAH",
    "KEN",
    "PHI",
}


def remove_design_group(text: str, group_name_pattern: str) -> tuple[str, bool]:
    """Remove a top-level design group block matching group_name_pattern.

    Returns (new_text, was_removed).
    """
    pattern = re.compile(
        r"(### [^\n]+ ###\n)?"  # optional comment header
        r"[ \t]*" + re.escape(group_name_pattern) + r"[ \t]*=[ \t]*\{",
        re.MULTILINE,
    )

    m = pattern.search(text)
    if not m:
        return text, False

    start = m.start()
    brace_start = m.end() - 1  # position of '{'
    depth = 0
    i = brace_start
    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
        i += 1
    else:
        return text, False

    # Consume trailing blank line
    while end < len(text) and text[end] in ("\n", "\r", " ", "\t"):
        if text[end] == "\n":
            end += 1
            break
        end += 1

    new_text = text[:start] + text[end:]
    new_text = re.sub(r"\n{3,}", "\n\n", new_text)
    return new_text.lstrip("\n"), True


def process_country_file(filepath: Path, tag: str, dry_run: bool = False) -> list[str]:
    """Process a country file, removing consolidated destroyer group."""
    text = filepath.read_text(encoding="utf-8", errors="replace")
    original = text
    actions = []

    new_text, removed = remove_design_group(text, f"{tag}_destroyers")
    if removed:
        text = new_text
        actions.append(f"removed {tag}_destroyers")
    else:
        actions.append(f"WARNING: {tag}_destroyers not found")

    if text != original and not dry_run:
        filepath.write_text(text, encoding="utf-8")

    return actions


def main():
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("DRY RUN — no files will be modified\n")

    total_removed = 0

    for tag in sorted(DESTROYER_REMOVE):
        filepath = AI_DIR / f"{tag}_naval.txt"
        if not filepath.exists():
            print(f"  SKIP {tag}: file not found at {filepath}")
            continue

        actions = process_country_file(filepath, tag, dry_run=dry_run)
        for action in actions:
            if "WARNING" in action:
                print(f"  {action}")
            else:
                print(f"  {tag}: {action}")
                total_removed += 1

    print(f"\nTotal design groups removed: {total_removed}")
    if dry_run:
        print("(dry run — no files modified)")


if __name__ == "__main__":
    main()
