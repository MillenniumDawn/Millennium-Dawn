#!/usr/bin/env python3
"""Assign MIO trait icons by the house rule.

Rule (deterministic):
  1. Winning modifier = highest |value| across equipment_bonus + production_bonus
     + organization_modifier. Ties -> first in file order.
  2. Prefix = the equipment-type prefix when the trait has a limit_to_equipment_type
     with exactly ONE token mapped in PREFIX_MAP; otherwise no prefix (standard icon).
  3. Candidate chain (first that exists as a sprite wins):
        <prefix>_<alias>   (family-specific suffix spelling)
        <suffix>           (standard)
        <prefix>           (base family icon)
        unique             (last resort)

Only `icon = x` placeholders are touched. Source of truth for sprite existence:
  interface/military_industrial_organization/industrial_organization_policies_and_traits_icons.gfx
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GFX = ROOT / "interface/military_industrial_organization/industrial_organization_policies_and_traits_icons.gfx"

PREFIX_MAP = {
    "util_vehicle_type": "util",
    "medium_tank_amphibious_chassis": "apc",
    "mio_cat_frigates": "frigate",
    "mio_cat_only_small_ships": "small_ship",
    "helicopter_operator": "heli_operator",
    "carrier": "carrier",
    "attack_submarine": "submarine",
    "convoy": "convoy",
    "mio_cat_eq_only_transport": "transport_airplane",
    "guided_missile_equipment": "guided_missile",
    "cnc_equipment_type": "cnc",
    "infantry_weapons_type": "smallarms",
    # ballistic_missile_equipment -> intentionally no prefix (standard icons)
}

# modifier name -> standard icon suffix (None = no standard icon for it)
STD = {
    "soft_attack": "soft_attack", "hard_attack": "hard_attack", "ap_attack": "ap_attack",
    "air_attack": "air_attack", "air_ground_attack": "air_ground_attack",
    "air_agility": "air_agility", "air_range": "air_range", "air_defence": "air_defence",
    "air_superiority": "air_superiority",
    "armor_value": "armor_value", "defense": "defense", "breakthrough": "breakthrough",
    "reliability": "reliability", "hardness": "hardness", "weight": "weight",
    "maximum_speed": "maximum_speed", "naval_speed": "naval_speed",
    "fuel_consumption": "fuel_consumption", "build_cost_ic": "build_cost_ic",
    "max_strength": "max_strength", "max_organisation": None, "carrier_size": None,
    "surface_detection": "surface_detection", "surface_visibility": "surface_visibility",
    "sub_detection": "sub_detection", "sub_visibility": "sub_visibility", "sub_attack": "sub_attack",
    "naval_range": "naval_range", "naval_strike_targetting": "naval_strike_targetting",
    "naval_strike_attack": "naval_strike_attack", "naval_anti_air_attack": "naval_anti_air_attack",
    "anti_air_attack": "anti_air_attack", "lg_attack": "lg_attack", "hg_attack": "hg_attack",
    "strategic_attack": "strategic_attack", "torpedo_attack": "torpedo_attack",
    "naval_light_gun_hit_chance_factor": "lg_attack",
    "naval_heavy_gun_hit_chance_factor": "hg_attack",
    "detection": "detection", "entrenchment": "entrenchment",
    "supply_consumption": "supply_consumption", "mines": "mines",
    "night_penalty": "night_penalty", "conversion_speed": "conversion_speed",
    "tank_gun": "tank_gun",
    "production_capacity_factor": "production_capacity",
    "production_efficiency_gain_factor": "efficiency_gain",
    "production_efficiency_cap_factor": "efficiency_cap",
    "production_cost_factor": "build_cost_ic",
    "production_resource_need_factor": "resources",
    "production_resource_penalty_factor": "resources",
    "thrust": "maximum_speed",
    "military_industrial_organization_task_capacity": "task",
    "military_industrial_organization_research_bonus": "research",
    "military_industrial_organization_funds_gain": "funds",
    "military_industrial_organization_design_team_assign_cost": "design",
    "military_industrial_organization_design_team_change_cost": "design",
    "military_industrial_organization_industrial_manufacturer_assign_cost": "design",
    "military_industrial_organization_size_up_requirement": "task",
}

# modifier -> ordered family-suffix aliases tried as <prefix>_<alias>
ALIAS = {
    "armor_value": ["armor", "armor_value"],
    "maximum_speed": ["speed"], "naval_speed": ["speed"],
    "build_cost_ic": ["buildcost"], "production_cost_factor": ["buildcost"],
    "production_resource_need_factor": ["resources", "resource"],
    "production_resource_penalty_factor": ["resources", "resource"],
    "production_efficiency_gain_factor": ["efficiency_gain", "efficiency_growth"],
    "production_efficiency_cap_factor": ["efficiency_cap"],
    "defense": ["defense", "defence"],
    "naval_anti_air_attack": ["anti_air"], "anti_air_attack": ["anti_air"],
    "naval_range": ["range"], "air_range": ["range"], "air_agility": ["agility"],
    "torpedo_attack": ["torpedo"],
    "naval_light_gun_hit_chance_factor": ["lg_attack"],
    "naval_heavy_gun_hit_chance_factor": ["hg_attack"],
}

PRE = "GFX_generic_mio_trait_icon_"


def load_sprites():
    try:
        text = GFX.read_text(encoding="utf-8")
    except OSError as e:
        sys.exit(f"error: cannot read sprite file {GFX}: {e}")
    return set(re.findall(r"GFX_generic_mio_trait_icon_[a-z0-9_]+", text))


def inner_block(block, keyword):
    """Return inner text of `keyword = { ... }` via brace matching, or ''."""
    m = re.search(keyword + r"\s*=\s*\{", block)
    if not m:
        return ""
    i = m.end() - 1
    depth = 0
    for j in range(i, len(block)):
        if block[j] == "{":
            depth += 1
        elif block[j] == "}":
            depth -= 1
            if depth == 0:
                return block[i + 1:j]
    return ""


def winning_modifier(block):
    best = None
    for kw in ("equipment_bonus", "production_bonus", "organization_modifier"):
        inner = inner_block(block, kw)
        for key, val in re.findall(r"([a-z_]+)\s*=\s*(-?\d*\.?\d+)", inner):
            v = abs(float(val))
            if best is None or v > best[1]:
                best = (key, v)
    return best[0] if best else None


def choose_icon(prefix, mod, sprites):
    cands = []
    if prefix:
        for alias in ALIAS.get(mod, [STD.get(mod)] if STD.get(mod) else []):
            cands.append(f"{prefix}_{alias}")
    std = STD.get(mod)
    if std:
        cands.append(std)
    if prefix:
        cands.append(prefix)
    cands.append("unique")
    for c in cands:
        if PRE + c in sprites:
            return PRE + c
    return PRE + "unique"


def main():
    sprites = load_sprites()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if args:
        target = Path(args[0])
        path = target if target.is_absolute() else ROOT / target
    else:
        path = ROOT / "common/military_industrial_organization/organizations/MD_HOL_organizations.txt"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        sys.exit(f"error: cannot read {path}: {e}")
    lines = text.split("\n")

    out = []
    i = 0
    n = len(lines)
    report = []
    while i < n:
        line = lines[i]
        if re.match(r"^\s*trait\s*=\s*\{", line):
            # capture full trait block by brace matching
            depth = 0
            j = i
            buf = []
            started = False
            while j < n:
                buf.append(lines[j])
                code = lines[j].split("#", 1)[0]
                depth += code.count("{") - code.count("}")
                if "{" in code:
                    started = True
                if started and depth <= 0:
                    break
                j += 1
            block = "\n".join(buf)
            if re.search(r"^\s*icon\s*=\s*x\s*$", block, re.M):
                lt = inner_block(block, "limit_to_equipment_type")
                tokens = lt.split()
                prefix = PREFIX_MAP.get(tokens[0]) if len(tokens) == 1 else None
                mod = winning_modifier(block)
                icon = choose_icon(prefix, mod, sprites) if mod else PRE + "unique"
                tok = re.search(r"token\s*=\s*(\S+)", block)
                report.append((tok.group(1) if tok else "?", mod, prefix or "-", icon))
                block = re.sub(r"(^\s*icon\s*=\s*)x(\s*$)",
                               lambda m: m.group(1) + icon + m.group(2),
                               block, count=1, flags=re.M)
                buf = block.split("\n")
            out.extend(buf)
            i = j + 1
        else:
            out.append(line)
            i += 1

    new_text = "\n".join(out)
    if "--write" in sys.argv:
        tmp = path.with_suffix(path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8", newline="") as f:
            f.write(new_text)
        os.replace(tmp, path)
    for tok, mod, prefix, icon in report:
        print(f"{icon.replace(PRE,''):28} <- {str(mod):45} [{prefix}]  {tok}")
    print(f"\nTotal placeholders resolved: {len(report)}")
    # any unique fallbacks?
    uniq = [r for r in report if r[3].endswith("_unique")]
    if uniq:
        print(f"unique fallbacks: {len(uniq)} -> " + ", ".join(r[0] for r in uniq))


if __name__ == "__main__":
    main()
