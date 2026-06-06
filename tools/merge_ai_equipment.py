#!/usr/bin/env python3
"""
One-time script to merge fragmented ai_equipment files by country tag
and fix formatting (spaces -> tabs, trailing whitespace, etc.)
"""
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

AI_EQUIP_DIR = Path(__file__).parent.parent / "common" / "ai_equipment"

# Files that should NOT be merged (generic, multi-tag, or non-naval)
SKIP_MERGE = {
    "generic_naval.txt",
    "generic_tank.txt",
    "generic_plane.txt",
    "generic_afv.txt",
    "documentation.info",
    "zz_battlecruiser_ai_Big5_nations.txt",
    "zz_md_battleships_big5_one.txt",
    "zz_ai_battlecruiser_USA_variants.txt",
    "zzz_generic_battlecruisers.txt",
    "zzz_generic_battleships.txt",
}

# Ship type labels for section headers
SHIP_TYPE_MAP = {
    "attack_subs": "Attack Submarines",
    "missile_subs": "Missile Submarines",
    "corvettes": "Corvettes",
    "destroyers": "Destroyers",
    "frigates": "Frigates",
    "cruisers": "Cruisers",
    "carriers": "Carriers",
    "battleships": "Battleships",
    "battlecruisers": "Battlecruisers",
    "naval_variants": "Naval Variants",
    "naval": "Naval",
    "variants": "Variants",
}

# Multi-tag coalition/regional files - merge into a group file
COALITION_FILES = {
    "zzz_ARAB_CARRIERS.txt",
    "zzz_BALTIC_UKR_Carriers.txt",
    "zzz_BENELUX_POR_Carriers.txt",
    "zzz_NORDIC_Carriers.txt",
    "zzz_SEA_Carriers.txt",
    "zzz_SEA_Cruisers.txt",
    "zzz_MLY_VIE_SeaCarriers.txt",
    "zzz_AFR_BlueWater_Carriers.txt",
    "zzz_CHL_COL_PER_Carriers.txt",
    "zzz_IRN_Carriers.txt",
    "zzz_ISR_Carriers.txt",
    "zzz_SPA_Carriers.txt",  # SPR is the tag but SPA used in filenames
    "zzz_TUR_Carriers.txt",
}


def fix_formatting(content: str) -> str:
    """Fix formatting issues in file content."""
    lines = content.split("\n")
    fixed = []
    for line in lines:
        # Replace 4-space indentation with tabs (repeatedly for nested)
        original = line
        while "    " in line and not line.lstrip().startswith("#"):
            # Only replace leading spaces
            stripped = line.lstrip(" ")
            leading_spaces = len(line) - len(stripped)
            tabs = leading_spaces // 4
            remaining_spaces = leading_spaces % 4
            line = "\t" * tabs + " " * remaining_spaces + stripped
            if line == original:
                break
            original = line
        # Remove trailing whitespace
        line = line.rstrip()
        fixed.append(line)

    # Remove excessive trailing blank lines, ensure single newline at end
    while fixed and fixed[-1] == "":
        fixed.pop()
    fixed.append("")  # single trailing newline

    return "\n".join(fixed)


def extract_tag_from_filename(filename: str) -> tuple:
    """Extract country tag and ship type from filename.

    Returns (tag, ship_type) or (None, None) if can't parse.
    """
    name = Path(filename).stem

    # Remove zz_ or zzz_ or ZZ_ or ZZZ_ prefix (case insensitive)
    clean = re.sub(r"^[Zz]{2,3}_", "", name)

    # Try TAG_type pattern (e.g. RAJ_Carriers, raj_attack_subs, RAJ_naval)
    match = re.match(r"^([A-Za-z]{3})[\s_](.+)$", clean)
    if match:
        tag = match.group(1).upper()
        ship_type = match.group(2).lower().replace(" ", "_")
        return tag, ship_type

    return None, None


def get_ship_type_label(ship_type: str) -> str:
    """Get a human-readable label for section headers."""
    for key, label in SHIP_TYPE_MAP.items():
        if key in ship_type:
            return label
    return ship_type.replace("_", " ").title()


def read_file(filepath: Path) -> str:
    """Read file content, return empty string for empty/missing files."""
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        return content.strip()
    except Exception:
        return ""


def group_files():
    """Group all files by country tag."""
    tag_groups = defaultdict(list)  # tag -> [(ship_type, filepath), ...]
    skip_files = []
    standalone_files = []

    for filepath in sorted(AI_EQUIP_DIR.iterdir()):
        if not filepath.is_file():
            continue
        if filepath.suffix not in (".txt",):
            skip_files.append(filepath)
            continue

        name = filepath.name

        # Skip generic/multi-tag files
        if name in SKIP_MERGE:
            standalone_files.append(filepath)
            continue

        # Skip coalition files - they stay standalone
        if name in COALITION_FILES:
            standalone_files.append(filepath)
            continue

        # Skip tank and plane files - they stay separate
        tag, ship_type = extract_tag_from_filename(name)
        if tag and ship_type:
            if "tank" in ship_type or "plane" in ship_type or "afv" in ship_type:
                standalone_files.append(filepath)
                continue
            tag_groups[tag].append((ship_type, filepath))
        else:
            # Can't parse - leave standalone
            standalone_files.append(filepath)

    return tag_groups, standalone_files, skip_files


def merge_tag_files(tag: str, files: list) -> str:
    """Merge all files for a single tag into one combined content string."""
    sections = []

    # Sort: put 'naval' (main file) first, then 'naval_variants', then alphabetically
    def sort_key(item):
        ship_type = item[0]
        if ship_type == "naval":
            return (0, ship_type)
        if "variant" in ship_type:
            return (1, ship_type)
        return (2, ship_type)

    files.sort(key=sort_key)

    for ship_type, filepath in files:
        content = read_file(filepath)
        if not content:
            continue  # Skip empty files

        label = get_ship_type_label(ship_type)
        sections.append(f"### {label} ###")
        sections.append(content)
        sections.append("")

    return "\n".join(sections)


def main():
    print(f"Scanning {AI_EQUIP_DIR}...")

    tag_groups, standalone_files, skip_files = group_files()

    # Stats
    total_source_files = sum(len(files) for files in tag_groups.values())
    print(
        f"Found {len(tag_groups)} country tags with {total_source_files} naval files to merge"
    )
    print(
        f"Found {len(standalone_files)} standalone files (tank/plane/generic/coalition)"
    )

    # Count lines before
    total_lines_before = 0
    all_source_paths = set()
    for files in tag_groups.values():
        for _, fp in files:
            all_source_paths.add(fp)
            content = read_file(fp)
            total_lines_before += content.count("\n") + 1 if content else 0

    merged_count = 0
    deleted_count = 0
    files_to_delete = []

    for tag in sorted(tag_groups.keys()):
        files = tag_groups[tag]

        if len(files) <= 1:
            # Only one file - just fix formatting, no merge needed
            ship_type, filepath = files[0]
            content = read_file(filepath)
            if content:
                fixed = fix_formatting(content)
                target = AI_EQUIP_DIR / f"{tag}_naval.txt"
                if filepath != target:
                    target.write_text(fixed, encoding="utf-8")
                    files_to_delete.append(filepath)
                    print(f"  Renamed: {filepath.name} -> {target.name}")
                else:
                    filepath.write_text(fixed, encoding="utf-8")
            continue

        # Multiple files - merge them
        merged = merge_tag_files(tag, files)
        fixed = fix_formatting(merged)

        target = AI_EQUIP_DIR / f"{tag}_naval.txt"
        target.write_text(fixed, encoding="utf-8")
        merged_count += 1

        # Mark source files for deletion (except the target itself)
        for _, filepath in files:
            if filepath != target:
                files_to_delete.append(filepath)

        print(f"  Merged {len(files)} files -> {target.name}")

    # Fix formatting in standalone files too
    for filepath in standalone_files:
        content = read_file(filepath)
        if content:
            fixed = fix_formatting(content)
            filepath.write_text(fixed, encoding="utf-8")

    # Delete merged source files
    for filepath in files_to_delete:
        if filepath.exists():
            filepath.unlink()
            deleted_count += 1

    # Count lines after
    total_lines_after = 0
    for filepath in AI_EQUIP_DIR.iterdir():
        if filepath.suffix == ".txt":
            content = read_file(filepath)
            total_lines_after += content.count("\n") + 1 if content else 0

    print(f"\n=== Summary ===")
    print(f"Tags merged: {merged_count}")
    print(f"Files deleted: {deleted_count}")
    print(f"Lines before: {total_lines_before} (in merged source files)")
    print(f"Lines after: {total_lines_after} (total in directory)")
    print(f"Remaining files: {len(list(AI_EQUIP_DIR.glob('*.txt')))}")


if __name__ == "__main__":
    main()
