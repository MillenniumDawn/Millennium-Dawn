#!/usr/bin/env python3
"""
Fix missing -999 deprioritize modifiers for hull types whose max tier was
previously underestimated.

Affected hull types (old max → actual max):
  frigate_hull:        5 → 6
  battle_cruiser_hull: 3 → 4  (uses battleship_hull tech)
  carrier_hull:        3 → 5

For each priority block containing a positive modifier for one of these
hull techs at a non-final tier, this script adds the missing
  modifier = { add = -999 has_tech = <next_tier_tech> }
line if it doesn't already exist.
"""

import os
import re
import sys
from pathlib import Path

EQUIP_DIR = Path(__file__).resolve().parent.parent / "common" / "ai_equipment"

# Correct max tiers
MAX_TIER = {
    "attack_submarine_hull": 6,
    "missile_submarine_hull": 6,
    "corvette_hull": 6,
    "frigate_hull": 6,
    "destroyer_hull": 5,
    "cruiser_hull": 5,
    "battleship_hull": 4,
    "battle_cruiser_hull": 4,
    "carrier_hull": 5,
    "mine_sweeper_hull": 2,
}

# battle_cruiser_hull uses battleship_hull tech names
TECH_OVERRIDE = {"battle_cruiser_hull": "battleship_hull"}

# Only fix hull types whose max tier was previously wrong in the scripts.
# Other hull types already had correct -999 modifiers from the original run.
AFFECTED_TECHS = {
    "frigate_hull_5",  # was treated as max, actual max is 6
    "battle_cruiser_hull_3",  # was treated as max, actual max is 4 (uses battleship tech)
    "carrier_hull_3",  # was treated as max, actual max is 5
    "carrier_hull_4",  # also needs -999 for carrier_hull_5
}

HULL_RE = re.compile(r"([\w]+_hull)_(\d+)")


def next_tier_tech(hull_tech: str) -> str | None:
    """Given e.g. 'frigate_hull_5', return the next tier tech string or None."""
    m = HULL_RE.fullmatch(hull_tech)
    if not m:
        return None
    base, tier = m.group(1), int(m.group(2))
    max_t = MAX_TIER.get(base)
    if max_t is None or tier >= max_t:
        return None
    tech_base = TECH_OVERRIDE.get(base, base)
    return f"{tech_base}_{tier + 1}"


def find_variant_hull_types(lines: list[str]) -> set[str]:
    """Find all hull types used in target_variant type = blocks in the file."""
    types = set()
    for line in lines:
        m = re.search(r"type\s*=\s*([\w]+_hull_\d+)", line.strip())
        if m:
            types.add(m.group(1))
    return types


def fix_file(filepath: Path, dry_run: bool = False) -> list[str]:
    """Fix priority blocks in a single file. Returns list of changes made."""
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Pre-scan: find which hull types have target_variant entries in this file.
    # Only add -999 for a next tier if the file actually has variants for it.
    variant_types = find_variant_hull_types(lines)

    changes = []
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]
        # Detect start of a priority block
        stripped = line.strip()
        if stripped.startswith("priority") and "=" in stripped and "{" in stripped:
            # Collect the entire priority block
            brace_depth = stripped.count("{") - stripped.count("}")
            block_lines = [line]
            i += 1
            while i < len(lines) and brace_depth > 0:
                bl = lines[i]
                brace_depth += bl.count("{") - bl.count("}")
                block_lines.append(bl)
                i += 1

            # Analyze block: find positive modifiers with has_tech = hull_N
            positive_techs = set()
            negative_techs = set()
            last_modifier_idx = -1
            last_modifier_indent = "\t\t\t"

            for bi, bline in enumerate(block_lines):
                bs = bline.strip()
                if bs.startswith("modifier") and "has_tech" in bs:
                    tech_match = re.search(r"has_tech\s*=\s*(\w+)", bs)
                    add_match = re.search(r"add\s*=\s*(-?\d+)", bs)
                    if tech_match and add_match:
                        tech = tech_match.group(1)
                        add_val = int(add_match.group(1))
                        if add_val < 0:
                            negative_techs.add(tech)
                        else:
                            positive_techs.add(tech)
                            last_modifier_idx = bi
                            # Capture the indentation
                            indent_match = re.match(r"^(\s*)", bline)
                            if indent_match:
                                last_modifier_indent = indent_match.group(1)

            # Determine what -999 modifiers are missing (only for affected techs)
            missing = []
            for ptech in positive_techs:
                if ptech not in AFFECTED_TECHS:
                    continue
                nt = next_tier_tech(ptech)
                if not nt or nt in negative_techs:
                    continue
                # Only add -999 if the file has variants for the next tier hull.
                # For battle_cruiser, the next-tier TECH is battleship_hull_N
                # but the variant type is still battle_cruiser_hull_N.
                m = HULL_RE.fullmatch(ptech)
                if m:
                    next_variant_type = f"{m.group(1)}_{int(m.group(2)) + 1}"
                    if next_variant_type in variant_types:
                        missing.append((ptech, nt))

            if missing and last_modifier_idx >= 0:
                # Insert after the last modifier line
                insert_after = last_modifier_idx
                for ptech, nt in sorted(missing, key=lambda x: x[1]):
                    new_line = f"{last_modifier_indent}modifier = {{ add = -999 has_tech = {nt} }}\n"
                    insert_after += 1
                    block_lines.insert(insert_after, new_line)
                    changes.append(
                        f"  {filepath.name}: added -999 {nt} "
                        f"(deprioritizes {ptech})"
                    )

            result.extend(block_lines)
        else:
            result.append(line)
            i += 1

    if changes and not dry_run:
        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(result)

    return changes


def main():
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("=== DRY RUN (no files will be modified) ===\n")

    total_changes = 0
    files_changed = 0

    for fpath in sorted(EQUIP_DIR.glob("*.txt")):
        changes = fix_file(fpath, dry_run=dry_run)
        if changes:
            files_changed += 1
            total_changes += len(changes)
            for c in changes:
                print(c)

    print(
        f"\n{'Would add' if dry_run else 'Added'} {total_changes} "
        f"missing -999 modifiers across {files_changed} files."
    )


if __name__ == "__main__":
    main()
