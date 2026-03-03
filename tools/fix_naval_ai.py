#!/usr/bin/env python3
"""Fix naval AI equipment files:
1. Rename 'ai_equipment = {' headers to unique design group names
2. Add tech-gated priority blocks to variant blocks that lack them

Usage: python3 tools/fix_naval_ai.py [--dry-run]
"""
import os
import re
import sys

AI_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "common",
    "ai_equipment",
)

ROLE_MAP = {
    "naval_attack_submarines": "attack_submarines",
    "naval_attack_submarine": "attack_submarines",
    "naval_missile_submarines": "missile_submarines",
    "naval_missile_submarine": "missile_submarines",
    "naval_corvettes": "corvettes",
    "naval_corvette": "corvettes",
    "naval_frigate": "frigates",
    "naval_frigates": "frigates",
    "naval_destroyer": "destroyers",
    "naval_destroyers": "destroyers",
    "naval_cruiser": "cruisers",
    "naval_cruisers": "cruisers",
    "naval_battleship": "battleships",
    "naval_battlecruiser": "battlecruisers",
    "naval_carrier": "carriers",
    "naval_capital_bb": "battleships",
    "naval_lhd": "lhd",
    "naval_mine_sweeper": "minesweepers",
    "naval_mine_layer": "minelayers",
}

# Battle cruiser hulls use battleship tech
TECH_OVERRIDE = {"battle_cruiser_hull": "battleship_hull"}

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

# Keywords that are NOT variant block names
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
    """Count { and } excluding comments."""
    code = line.split("#")[0] if "#" in line else line
    return code.count("{"), code.count("}")


def hull_info(hull_type):
    """Parse 'frigate_hull_3' into ('frigate_hull', 3)."""
    m = re.match(r"(.+?)_(\d+)$", hull_type)
    return (m.group(1), int(m.group(2))) if m else (hull_type, None)


def make_priority(hull_type, indent):
    """Generate a priority block string for a variant."""
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


def clean_filename(fname):
    """Strip prefix and extension from filename for naming."""
    base = fname.replace(".txt", "")
    for prefix in ("zzz_", "zz_"):
        if base.startswith(prefix):
            base = base[len(prefix) :]
    return base


def derive_name(filepath, tag, role):
    """Generate a design group name."""
    suffix = ROLE_MAP.get(role, (role or "naval").replace("naval_", ""))
    if tag:
        return f"{tag}_{suffix}"
    # Multi-tag or unknown: use filename as base
    base = clean_filename(os.path.basename(filepath))
    # Avoid redundancy: if filename already contains the ship type, just use filename
    suffix_words = suffix.lower().rstrip("s")  # e.g. 'battleship', 'carrier'
    if suffix_words in base.lower():
        return base
    return f"{base}_{suffix}"


def process_file(filepath, global_names, dry_run=False):
    """Process a single file. Returns (renames, priorities_added)."""
    with open(filepath, "r") as f:
        lines = f.read().split("\n")

    has_ai_eq = any(
        re.match(r"\s*ai_equipment\s*=\s*\{", l)
        for l in lines
        if not l.strip().startswith("#")
    )
    if not has_ai_eq:
        return 0, 0

    result = []
    renames = 0
    prio_added = 0

    # Collect existing non-ai_equipment block names to avoid local conflicts
    local_names = set()
    for line in lines:
        m = re.match(r"^(\w+)\s*=\s*\{", line.strip())
        if m and m.group(1) != "ai_equipment":
            local_names.add(m.group(1))

    depth = 0
    group_depth = None
    variant_info = None  # dict tracking current variant
    in_tv = False
    tv_depth = None

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Skip pure comment lines for brace counting but still output them
        if stripped.startswith("#"):
            result.append(line)
            continue

        ob, cb = count_braces(line)
        new_depth = depth + ob - cb

        # === RENAME ai_equipment ===
        if depth == 0 and re.match(r"\s*ai_equipment\s*=\s*\{", stripped):
            tag, role = None, None
            sd = ob - cb  # typically 1
            for j in range(i + 1, min(i + 30, len(lines))):
                s = lines[j].strip()
                if s.startswith("#"):
                    continue
                job, jcb = count_braces(lines[j])
                sd += job - jcb
                if sd <= 0:
                    break
                af = re.search(r"available_for\s*=\s*\{(.+?)\}", s)
                if af:
                    tags = af.group(1).split()
                    tag = tags[0] if len(tags) == 1 else None
                rm = re.search(r"roles\s*=\s*\{(.+?)\}", s)
                if rm:
                    role = rm.group(1).strip()

            new_name = derive_name(filepath, tag, role)

            # Ensure global + local uniqueness
            orig = new_name
            c = 2
            while new_name in global_names or new_name in local_names:
                new_name = f"{orig}_{c}"
                c += 1
            global_names.add(new_name)
            local_names.add(new_name)

            indent = line[: len(line) - len(line.lstrip())]
            result.append(f"{indent}{new_name} = {{")
            group_depth = new_depth
            depth = new_depth
            renames += 1
            continue

        # === DETECT VARIANT START ===
        if group_depth is not None and depth == group_depth and variant_info is None:
            m = re.match(r"(\w+)\s*=\s*\{", stripped)
            if m:
                word = m.group(1)
                if word not in NOT_VARIANTS:
                    variant_info = {
                        "start_idx": len(result),
                        "has_priority": False,
                        "hull_type": None,
                        "depth": new_depth,
                    }

        # === INSIDE VARIANT ===
        if variant_info is not None:
            vd = variant_info["depth"]

            # Detect priority at variant's direct child level
            if depth == vd and re.match(r"priority\s*=\s*\{", stripped):
                variant_info["has_priority"] = True

            # Detect target_variant
            if re.match(r"target_variant\s*=\s*\{", stripped):
                in_tv = True
                tv_depth = new_depth

            # Extract hull type from target_variant
            if in_tv:
                tm = re.match(r"type\s*=\s*(\w+)", stripped)
                if tm and variant_info["hull_type"] is None:
                    variant_info["hull_type"] = tm.group(1)

        result.append(line)

        # === CHECK target_variant END ===
        if in_tv and tv_depth is not None and new_depth < tv_depth:
            in_tv = False
            tv_depth = None

        # === CHECK VARIANT END ===
        if variant_info is not None and new_depth <= group_depth:
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

        # === CHECK GROUP END ===
        if group_depth is not None and new_depth < group_depth:
            group_depth = None

        depth = new_depth

    if (renames or prio_added) and not dry_run:
        with open(filepath, "w") as f:
            f.write("\n".join(result))

    return renames, prio_added


def main():
    dry_run = "--dry-run" in sys.argv

    # Collect all existing non-ai_equipment design group names globally
    global_names = set()
    all_files = sorted(os.listdir(AI_DIR))
    for fname in all_files:
        if not fname.endswith(".txt"):
            continue
        path = os.path.join(AI_DIR, fname)
        with open(path, "r") as f:
            for line in f:
                s = line.strip()
                if s.startswith("#"):
                    continue
                m = re.match(r"^(\w+)\s*=\s*\{", s)
                if m and m.group(1) != "ai_equipment":
                    global_names.add(m.group(1))

    # Process country-specific TAG_naval.txt files first (they get clean names),
    # then shared/special files
    country_files = []
    other_files = []
    for fname in all_files:
        if not fname.endswith(".txt"):
            continue
        if re.match(r"^[A-Z]{3}_naval\.txt$", fname):
            country_files.append(fname)
        elif (
            "naval" in fname.lower()
            or "battleship" in fname.lower()
            or "battlecruiser" in fname.lower()
            or "carrier" in fname.lower()
            or "cruiser" in fname.lower()
            or "_BC" in fname
        ):
            other_files.append(fname)

    total_r, total_p = 0, 0

    for fname in country_files + other_files:
        path = os.path.join(AI_DIR, fname)
        r, p = process_file(path, global_names, dry_run)
        if r or p:
            prefix = "[DRY RUN] " if dry_run else ""
            print(f"{prefix}{fname}: {r} renames, {p} priorities added")
            total_r += r
            total_p += p

    print(f"\nTotal: {total_r} renames, {total_p} priorities added")
    if dry_run:
        print("(dry run — no files modified)")


if __name__ == "__main__":
    main()
