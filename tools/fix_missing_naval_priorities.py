#!/usr/bin/env python3
"""Add missing tech-gated priority blocks to naval AI equipment variants.

Finds variant blocks inside 'category = naval' design groups that have
a target_variant with a hull type but no priority block, and inserts one.

Usage: python3 tools/fix_missing_naval_priorities.py [--dry-run]
"""
import os
import re
import sys

AI_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "common",
    "ai_equipment",
)

MAX_TIER = {
    "attack_submarine_hull": 6,
    "missile_submarine_hull": 6,
    "corvette_hull": 6,
    "frigate_hull": 5,
    "destroyer_hull": 5,
    "cruiser_hull": 5,
    "battleship_hull": 4,
    "battle_cruiser_hull": 3,
    "carrier_hull": 3,
    "mine_sweeper_hull": 2,
}

TECH_OVERRIDE = {"battle_cruiser_hull": "battleship_hull"}

NOT_VARIANTS = {
    "category",
    "available_for",
    "roles",
    "priority",
    "blocked_for",
    "modules",
    "target_variant",
    "upgrades",
    "allowed_modules",
    "ai_equipment",
    "modifier",
    "type",
    "match_value",
}


def count_braces(line):
    code = line.split("#")[0] if "#" in line else line
    return code.count("{"), code.count("}")


def hull_info(hull_type):
    m = re.match(r"(.+?)_(\d+)$", hull_type)
    return (m.group(1), int(m.group(2))) if m else (hull_type, None)


def make_priority(hull_type, indent):
    base, tier = hull_info(hull_type)
    if tier is None:
        return None
    tech_base = TECH_OVERRIDE.get(base, base)
    tech = f"{tech_base}_{tier}"
    max_t = MAX_TIER.get(base, 6)
    lines = [
        f"{indent}priority = {{",
        f"{indent}\tbase = -1",
        f"{indent}\tmodifier = {{ add = 1000 has_tech = {tech} }}",
    ]
    if tier < max_t:
        lines.append(
            f"{indent}\tmodifier = {{ add = -999 has_tech = {tech_base}_{tier + 1} }}"
        )
    lines.append(f"{indent}}}")
    return "\n".join(lines)


def process_file(filepath, dry_run=False):
    with open(filepath, "r") as f:
        lines = f.read().split("\n")

    # Check if file has naval design groups
    has_naval = False
    for line in lines:
        if "category = naval" in line and not line.strip().startswith("#"):
            has_naval = True
            break
    if not has_naval:
        return 0

    result = []
    prio_added = 0
    depth = 0
    group_depth = None
    is_naval_group = False
    variant_info = None
    in_tv = False
    tv_depth = None

    for i, line in enumerate(lines):
        stripped = line.strip()

        if stripped.startswith("#"):
            result.append(line)
            continue

        ob, cb = count_braces(line)
        new_depth = depth + ob - cb

        # Detect top-level design group
        if depth == 0 and ob > 0:
            m = re.match(r"(\w+)\s*=\s*\{", stripped)
            if m:
                group_depth = new_depth
                is_naval_group = False  # will confirm when we see category = naval

        # Detect category = naval inside group
        if (
            group_depth is not None
            and depth == group_depth
            and "category = naval" in stripped
        ):
            is_naval_group = True

        # Detect variant start
        if (
            is_naval_group
            and group_depth is not None
            and depth == group_depth
            and variant_info is None
        ):
            m = re.match(r"(\w+)\s*=\s*\{", stripped)
            if m and m.group(1) not in NOT_VARIANTS:
                variant_info = {
                    "start_idx": len(result),
                    "has_priority": False,
                    "hull_type": None,
                    "depth": new_depth,
                }

        # Inside variant: track priority and hull type
        if variant_info is not None:
            vd = variant_info["depth"]
            if depth == vd and re.match(r"priority\s*=\s*\{", stripped):
                variant_info["has_priority"] = True
            if re.match(r"target_variant\s*=\s*\{", stripped):
                in_tv = True
                tv_depth = new_depth
            if in_tv:
                tm = re.match(r"type\s*=\s*(\w+)", stripped)
                if tm and variant_info["hull_type"] is None:
                    variant_info["hull_type"] = tm.group(1)

        result.append(line)

        # Check target_variant end
        if in_tv and tv_depth is not None and new_depth < tv_depth:
            in_tv = False
            tv_depth = None

        # Check variant end
        if variant_info is not None and new_depth <= (group_depth or 0):
            if not variant_info["has_priority"] and variant_info["hull_type"]:
                start = variant_info["start_idx"]
                var_line = result[start]
                var_indent = ""
                for ch in var_line:
                    if ch in " \t":
                        var_indent += ch
                    else:
                        break
                prio_indent = var_indent + "\t"
                pblock = make_priority(variant_info["hull_type"], prio_indent)
                if pblock:
                    result.insert(start + 1, pblock)
                    prio_added += 1

            variant_info = None
            in_tv = False
            tv_depth = None

        # Check group end
        if group_depth is not None and new_depth < group_depth:
            group_depth = None
            is_naval_group = False

        depth = new_depth

    if prio_added and not dry_run:
        with open(filepath, "w") as f:
            f.write("\n".join(result))

    return prio_added


def main():
    dry_run = "--dry-run" in sys.argv
    total = 0

    for fname in sorted(os.listdir(AI_DIR)):
        if not fname.endswith(".txt"):
            continue
        path = os.path.join(AI_DIR, fname)
        added = process_file(path, dry_run)
        if added:
            prefix = "[DRY RUN] " if dry_run else ""
            print(f"{prefix}{fname}: {added} priorities added")
            total += added

    print(f"\nTotal: {total} priorities added")
    if dry_run:
        print("(dry run — no files modified)")


if __name__ == "__main__":
    main()
