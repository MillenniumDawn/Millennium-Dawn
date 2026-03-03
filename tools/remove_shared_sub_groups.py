#!/usr/bin/env python3
"""
remove_shared_sub_groups.py

Removes attack_submarine and/or missile_submarine design groups from country
naval AI files that have been consolidated into shared files.

Usage:
    python3 tools/remove_shared_sub_groups.py [--dry-run]
"""

import re
import sys
from pathlib import Path

AI_DIR = Path(__file__).parent.parent / "common" / "ai_equipment"

# Countries whose attack_submarine group should be removed (now in shared file)
ATTACK_SUB_REMOVE = {
    "ALG",
    "AST",
    "CAN",
    "CHL",
    "EGY",
    "ENG",
    "FRA",
    "GER",
    "GRE",
    "IND",
    "ITA",
    "KOR",
    "LAT",
    "LIT",
    "POR",
    "RAJ",
    "SIN",  # Group 1
    "GAH",
    "KEN",
    "LUX",
    "MOR",
    "PRU",
    "SAF",
    "SIA",  # Group 3
}

# Countries whose missile_submarine group should be removed (now in shared file)
MISSILE_SUB_REMOVE = {
    "ALG",
    "AST",
    "CAN",
    "CHL",
    "EGY",
    "ENG",
    "FRA",
    "GAH",
    "GER",
    "GRE",
    "IND",
    "ITA",
    "KEN",
    "KOR",
    "LAT",
    "LIT",
    "LUX",
    "MOR",
    "POR",
    "PRU",
    "RAJ",
    "SAF",
    "SIA",
    "SIN",
    "SPA",
    "TUR",
    "UKR",  # Group 1
}


def remove_design_group(text: str, group_name_pattern: str) -> tuple[str, bool]:
    """Remove a top-level design group block matching group_name_pattern.

    Returns (new_text, was_removed).
    The pattern matches the opening line of the group.
    """
    # Match "### Attack Submarines ###\nTAG_attack_submarines = {\n..." or similar
    # Also handles optional preceding comment line
    pattern = re.compile(
        r"(### [^\n]+ ###\n)?"  # optional comment header
        r"[ \t]*" + re.escape(group_name_pattern) + r"[ \t]*=[ \t]*\{",
        re.MULTILINE,
    )

    m = pattern.search(text)
    if not m:
        return text, False

    # Find the matching closing brace
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
        # Unmatched brace
        return text, False

    # Also consume any trailing blank lines
    while end < len(text) and text[end] in ("\n", "\r", " ", "\t"):
        if text[end] == "\n":
            end += 1
            break
        end += 1

    # Remove the block
    new_text = text[:start] + text[end:]
    # Clean up extra blank lines
    new_text = re.sub(r"\n{3,}", "\n\n", new_text)
    return new_text.lstrip("\n"), True


def process_country_file(filepath: Path, tag: str, dry_run: bool = False) -> list[str]:
    """Process a country file, removing consolidated groups. Returns list of actions taken."""
    text = filepath.read_text(encoding="utf-8", errors="replace")
    original = text
    actions = []

    if tag in ATTACK_SUB_REMOVE:
        new_text, removed = remove_design_group(text, f"{tag}_attack_submarines")
        if removed:
            text = new_text
            actions.append(f"removed {tag}_attack_submarines")
        else:
            actions.append(f"WARNING: {tag}_attack_submarines not found")

    if tag in MISSILE_SUB_REMOVE:
        new_text, removed = remove_design_group(text, f"{tag}_missile_submarines")
        if removed:
            text = new_text
            actions.append(f"removed {tag}_missile_submarines")
        else:
            actions.append(f"WARNING: {tag}_missile_submarines not found")

    if text != original and not dry_run:
        filepath.write_text(text, encoding="utf-8")

    return actions


def main():
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("DRY RUN — no files will be modified\n")

    all_tags = ATTACK_SUB_REMOVE | MISSILE_SUB_REMOVE
    total_removed = 0

    for tag in sorted(all_tags):
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
