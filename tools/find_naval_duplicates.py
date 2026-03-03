#!/usr/bin/env python3
"""
find_naval_duplicates.py

Compares attack_submarine and missile_submarine design group module loadouts
across all country *_naval.txt files in common/ai_equipment/.

Groups countries by exact-match module patterns and outputs:
  - Which countries are 100% identical to the reference pattern
  - Which countries differ at specific hull tiers
  - Which countries have unique patterns (keep country-specific)

Usage:
    python tools/find_naval_duplicates.py [--ref ALG]
"""

import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

AI_DIR = Path(__file__).parent.parent / "common" / "ai_equipment"


def parse_modules_block(text: str, start: int) -> dict[str, str]:
    """Parse a modules = { ... } block starting at position `start`.
    Returns {slot_name: module_name} mapping."""
    depth = 0
    i = start
    inside = False
    modules = {}
    while i < len(text):
        ch = text[i]
        if ch == "{":
            depth += 1
            if not inside:
                inside = True
        elif ch == "}":
            depth -= 1
            if depth == 0:
                break
        elif inside and depth == 1:
            # Look for slot = value assignments
            m = re.match(r"\s*(\w+)\s*=\s*(\w+)", text[i:])
            if m:
                modules[m.group(1)] = m.group(2)
                i += len(m.group(0))
                continue
        i += 1
    return modules


def parse_design_group(text: str, group_start: int) -> list[dict]:
    """Parse variants within a design group block.
    Returns list of {type, match_value, modules} dicts per variant."""
    variants = []
    depth = 0
    i = group_start
    inside = False

    while i < len(text):
        ch = text[i]
        if ch == "{":
            depth += 1
            if not inside:
                inside = True
        elif ch == "}":
            depth -= 1
            if depth == 0:
                break
        i += 1

    # Now parse variant blocks inside this group
    block = text[group_start : i + 1]

    # Find target_variant = { ... } blocks
    for tv_match in re.finditer(r"target_variant\s*=\s*\{", block):
        tv_start = tv_match.end() - 1  # position of '{'
        # Extract type
        type_m = re.search(r"type\s*=\s*(\w+)", block[tv_start : tv_start + 200])
        hull_type = type_m.group(1) if type_m else "unknown"

        # Extract match_value
        mv_m = re.search(r"match_value\s*=\s*(\d+)", block[tv_start : tv_start + 200])
        match_value = int(mv_m.group(1)) if mv_m else 0

        # Find modules = { block
        mod_m = re.search(r"modules\s*=\s*\{", block[tv_start:])
        if mod_m:
            abs_pos = tv_start + mod_m.end() - 1
            modules = parse_modules_block(block, abs_pos)
        else:
            modules = {}

        variants.append(
            {"type": hull_type, "match_value": match_value, "modules": modules}
        )

    return variants


def parse_naval_file(filepath: Path) -> dict[str, list[dict]]:
    """Parse a *_naval.txt file and extract attack/missile submarine design groups.

    Returns {group_type: [variants]} where group_type is
    'attack_submarine' or 'missile_submarine'.
    """
    text = filepath.read_text(encoding="utf-8", errors="replace")
    result = {}

    for role, pattern in [
        ("attack_submarine", r"\w+_attack_submarines\s*=\s*\{"),
        ("missile_submarine", r"\w+_missile_submarines\s*=\s*\{"),
    ]:
        m = re.search(pattern, text)
        if m:
            group_start = m.end() - 1  # position of '{'
            variants = parse_design_group(text, group_start)
            if variants:
                result[role] = variants

    return result


def variants_signature(variants: list[dict]) -> tuple:
    """Return a hashable signature for a list of variants (modules only, no match_value)."""
    sig = []
    for v in sorted(variants, key=lambda x: x["type"]):
        mod_tuple = tuple(sorted(v["modules"].items()))
        sig.append((v["type"], mod_tuple))
    return tuple(sig)


def variants_full_signature(variants: list[dict]) -> tuple:
    """Return a hashable signature including match_values."""
    sig = []
    for v in sorted(variants, key=lambda x: x["type"]):
        mod_tuple = tuple(sorted(v["modules"].items()))
        sig.append((v["type"], v["match_value"], mod_tuple))
    return tuple(sig)


def compare_variants(ref_variants: list[dict], other_variants: list[dict]) -> dict:
    """Compare two variant lists. Returns dict of differences per hull type."""
    ref_map = {v["type"]: v for v in ref_variants}
    other_map = {v["type"]: v for v in other_variants}

    diffs = {}
    all_types = set(ref_map.keys()) | set(other_map.keys())

    for hull_type in sorted(all_types):
        if hull_type not in ref_map:
            diffs[hull_type] = {"only_in_other": other_map[hull_type]}
        elif hull_type not in other_map:
            diffs[hull_type] = {"only_in_ref": ref_map[hull_type]}
        else:
            ref_mods = ref_map[hull_type]["modules"]
            other_mods = other_map[hull_type]["modules"]
            if ref_mods != other_mods:
                changed = {}
                all_slots = set(ref_mods.keys()) | set(other_mods.keys())
                for slot in sorted(all_slots):
                    ref_val = ref_mods.get(slot, "<missing>")
                    other_val = other_mods.get(slot, "<missing>")
                    if ref_val != other_val:
                        changed[slot] = (ref_val, other_val)
                diffs[hull_type] = {"module_diffs": changed}

    return diffs


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Compare naval AI submarine design groups"
    )
    parser.add_argument(
        "--ref", default="ALG", help="Reference country tag (default: ALG)"
    )
    parser.add_argument(
        "--role",
        choices=["attack_submarine", "missile_submarine", "both"],
        default="both",
        help="Which role to compare",
    )
    parser.add_argument(
        "--json", action="store_true", help="Output JSON for machine parsing"
    )
    args = parser.parse_args()

    roles_to_check = (
        ["attack_submarine", "missile_submarine"]
        if args.role == "both"
        else [args.role]
    )

    # Find and parse all naval files
    all_files = sorted(AI_DIR.glob("*_naval.txt"))
    country_data: dict[str, dict] = {}

    for f in all_files:
        tag = f.stem.replace("_naval", "")
        data = parse_naval_file(f)
        if data:
            country_data[tag] = data

    ref_tag = args.ref.upper()
    if ref_tag not in country_data:
        print(f"ERROR: Reference tag '{ref_tag}' not found or has no submarine groups.")
        sys.exit(1)

    for role in roles_to_check:
        print(f"\n{'=' * 70}")
        print(f"ROLE: {role.upper().replace('_', ' ')}")
        print(f"Reference: {ref_tag}")
        print("=" * 70)

        if role not in country_data.get(ref_tag, {}):
            print(f"  {ref_tag} has no {role} group. Skipping.")
            continue

        ref_variants = country_data[ref_tag][role]
        ref_sig = variants_signature(ref_variants)
        ref_full_sig = variants_full_signature(ref_variants)

        identical_module: list[str] = []
        identical_full: list[str] = []
        differs: dict[str, dict] = {}
        missing: list[str] = []

        for tag, data in sorted(country_data.items()):
            if tag == ref_tag:
                continue
            if role not in data:
                missing.append(tag)
                continue
            other_variants = data[role]
            other_sig = variants_signature(other_variants)
            other_full = variants_full_signature(other_variants)

            if other_sig == ref_sig:
                identical_module.append(tag)
                if other_full == ref_full_sig:
                    identical_full.append(tag)
            else:
                diffs = compare_variants(ref_variants, other_variants)
                differs[tag] = diffs

        print(
            f"\n[IDENTICAL modules + match_values] ({len(identical_full)} countries):"
        )
        print(f"  {' '.join(sorted(identical_full)) if identical_full else '(none)'}")

        identical_mod_only = [t for t in identical_module if t not in identical_full]
        if identical_mod_only:
            print(
                f"\n[IDENTICAL modules only, DIFFERENT match_values] ({len(identical_mod_only)} countries):"
            )
            print(f"  {' '.join(sorted(identical_mod_only))}")

        print(f"\n[DIFFERENT module loadouts] ({len(differs)} countries):")
        if args.json:
            print(json.dumps(differs, indent=2))
        else:
            for tag, diffs in sorted(differs.items()):
                print(f"\n  {tag}:")
                for hull, diff in sorted(diffs.items()):
                    if "module_diffs" in diff:
                        for slot, (ref_val, other_val) in sorted(
                            diff["module_diffs"].items()
                        ):
                            print(f"    {hull} / {slot}: {ref_val} → {other_val}")
                    elif "only_in_ref" in diff:
                        print(f"    {hull}: only in {ref_tag}")
                    elif "only_in_other" in diff:
                        print(f"    {hull}: only in {tag}")

        print(f"\n[NO {role.replace('_', ' ')} group] ({len(missing)} countries):")
        print(f"  {' '.join(sorted(missing)) if missing else '(none)'}")

        # Group all countries by their module signature
        print(f"\n[SIGNATURE GROUPS (modules only)]:")
        sig_groups: dict[tuple, list[str]] = defaultdict(list)
        for tag, data in sorted(country_data.items()):
            if role in data:
                sig = variants_signature(data[role])
                sig_groups[sig].append(tag)

        for i, (sig, tags) in enumerate(
            sorted(sig_groups.items(), key=lambda x: -len(x[1])), 1
        ):
            print(f"\n  Group {i} ({len(tags)} countries): {' '.join(sorted(tags))}")
            # Print the signature summary
            for hull_type, mod_tuple in sig:
                mods_str = ", ".join(f"{k}={v}" for k, v in mod_tuple)
                print(f"    {hull_type}: {mods_str}")


if __name__ == "__main__":
    main()
