#!/usr/bin/env python3
"""
Estimate a nation's starting GDP based on in-game Millennium Dawn economic formulas.

Reads state history files, country history files, and idea definitions to gather
population, buildings, resources, productivity, and all modifier stacks, then
applies the same GDP calculation the game uses on startup.

Usage:
    python3 tools/estimate_gdp.py TAG [TAG2 TAG3 ...]
    python3 tools/estimate_gdp.py USA
    python3 tools/estimate_gdp.py USA CHI GER BRA
    python3 tools/estimate_gdp.py --all          # estimate all countries
    python3 tools/estimate_gdp.py --top 20       # top 20 by GDP
"""

import os
import re
import sys
from collections import defaultdict

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
STATES_DIR = os.path.join(BASE_DIR, "history", "states")
COUNTRIES_DIR = os.path.join(BASE_DIR, "history", "countries")
IDEAS_DIR = os.path.join(BASE_DIR, "common", "ideas")

# Building GDP formula: base + bonus_rate * modifier@<building>_productivity
# From 00_money_system.txt lines 4956-5005
BUILDING_GDP_FORMULA = {
    #                       (base, bonus_rate, modifier_key)
    "industrial_complex": (17.5, 20, "civilian_factories_productivity"),
    "arms_factory": (1.5, 1, "military_factories_productivity"),
    "dockyard": (1.5, 1, "dockyard_productivity"),
    "offices": (50, 50, "offices_productivity"),
    "agriculture_district": (25, 25, "agricolture_productivity_modifier"),
    "microchip_plant": (32, 35, "microchip_plant_productivity_modifier"),
    "composite_plant": (28, 30, "composite_plant_productivity_modifier"),
    "synthetic_refinery": (10, 10, "synthetic_refinery_productivity_modifier"),
    "nuclear_reactor": (4, 0, None),
    "fossil_powerplant": (1.7, 0, None),
    "renewable_energy_infra": (2, 0, None),
    "internet_station": (3.5, 0, None),
}

ALL_BUILDING_TYPES = set(BUILDING_GDP_FORMULA.keys()) | {
    "infrastructure",
    "fuel_silo",
    "air_base",
}

RESOURCE_GDP_COEFF = 0.5
RESOURCE_TYPES = {"oil", "aluminium", "rubber", "tungsten", "steel", "chromium"}

# Per-resource modifier keys from environmental ideas
RESOURCE_FACTOR_KEYS = {
    "oil": "local_resources_oil_factor",
    "aluminium": "local_resources_aluminium_factor",
    "rubber": "local_resources_rubber_factor",
    "tungsten": "local_resources_tungsten_factor",
    "steel": "local_resources_steel_factor",
    "chromium": "local_resources_chromium_factor",
}

HEALTH_GDP_MULT = {
    "health_01": 0.30,
    "health_02": 0.60,
    "health_03": 1.00,
    "health_04": 1.40,
    "health_05": 1.80,
    "health_06": 2.20,
}

# All modifier keys we care about for GDP calculation
GDP_MODIFIER_KEYS = {
    "civilian_factories_productivity",
    "military_factories_productivity",
    "dockyard_productivity",
    "offices_productivity",
    "agricolture_productivity_modifier",
    "microchip_plant_productivity_modifier",
    "composite_plant_productivity_modifier",
    "synthetic_refinery_productivity_modifier",
    "local_resources_factor",
    "gdp_from_resource_sector_modifier",
    "total_workforce_modifier",
    "local_resources_oil_factor",
    "local_resources_aluminium_factor",
    "local_resources_rubber_factor",
    "local_resources_tungsten_factor",
    "local_resources_steel_factor",
    "local_resources_chromium_factor",
}


# ─── Idea Parsing ──────────────────────────────────────────────────────────────


def parse_all_ideas():
    """
    Parse all idea definition files and build a lookup: idea_name -> {modifier_key: value}.
    Only extracts GDP-relevant modifiers.
    """
    idea_modifiers = {}

    for fname in os.listdir(IDEAS_DIR):
        if not fname.endswith(".txt"):
            continue
        fpath = os.path.join(IDEAS_DIR, fname)
        try:
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception:
            continue

        _extract_ideas_from_content(content, idea_modifiers)

    return idea_modifiers


def _extract_ideas_from_content(content, idea_modifiers):
    """Extract idea definitions and their modifiers from file content."""
    # Remove comments
    content = re.sub(r"#[^\n]*", "", content)

    # Tokenize: we need to find idea blocks and their modifier sub-blocks
    # Strategy: find top-level idea names by looking for patterns like:
    #   idea_name = { ... modifier = { key = val ... } ... }

    # Find all potential idea definitions (word = {) at reasonable indent levels
    # Ideas are typically at depth 2 (inside a category block)
    tokens = _tokenize(content)
    _parse_idea_tokens(tokens, idea_modifiers)


def _tokenize(content):
    """Simple tokenizer for HOI4 script: returns list of (type, value) tokens."""
    tokens = []
    i = 0
    while i < len(content):
        c = content[i]
        if c in " \t\r\n":
            i += 1
            continue
        if c == "{":
            tokens.append(("OPEN", "{"))
            i += 1
        elif c == "}":
            tokens.append(("CLOSE", "}"))
            i += 1
        elif c == "=":
            tokens.append(("EQ", "="))
            i += 1
        elif c == '"':
            # Quoted string
            j = i + 1
            while j < len(content) and content[j] != '"':
                j += 1
            tokens.append(("STR", content[i + 1 : j]))
            i = j + 1
        else:
            # Word token
            j = i
            while j < len(content) and content[j] not in ' \t\r\n{}=\n"':
                j += 1
            tokens.append(("WORD", content[i:j]))
            i = j
    return tokens


def _parse_idea_tokens(tokens, idea_modifiers):
    """Parse tokenized content to extract idea modifier values."""
    i = 0
    depth = 0
    # Track context: we want ideas at depth >= 2
    context_stack = []

    while i < len(tokens):
        ttype, tval = tokens[i]

        if ttype == "OPEN":
            depth += 1
            i += 1
        elif ttype == "CLOSE":
            if context_stack and context_stack[-1][1] == depth:
                context_stack.pop()
            depth -= 1
            i += 1
        elif ttype in ("WORD", "STR") and i + 2 < len(tokens):
            next_type, next_val = tokens[i + 1]
            if next_type == "EQ":
                key = tval
                i += 2  # skip past '='
                if i < len(tokens):
                    val_type, val_val = tokens[i]
                    if val_type == "OPEN":
                        # This is a block: key = { ... }
                        if depth >= 1 and key == "modifier":
                            # Extract modifiers from this block
                            parent = context_stack[-1][0] if context_stack else None
                            if parent:
                                mods = _extract_modifier_block(tokens, i)
                                if mods:
                                    if parent not in idea_modifiers:
                                        idea_modifiers[parent] = {}
                                    for mk, mv in mods.items():
                                        idea_modifiers[parent][mk] = (
                                            idea_modifiers[parent].get(mk, 0) + mv
                                        )
                        # Push context
                        context_stack.append((key, depth + 1))
                        # Don't increment i here; the OPEN will be handled next loop
                    elif val_type in ("WORD", "STR"):
                        # key = value (simple assignment)
                        i += 1
                    else:
                        i += 1
                continue
            else:
                i += 1
        else:
            i += 1


def _extract_modifier_block(tokens, start_idx):
    """Extract GDP-relevant key=value pairs from a modifier = { ... } block."""
    mods = {}
    i = start_idx
    if tokens[i][0] != "OPEN":
        return mods
    i += 1
    depth = 1

    while i < len(tokens) and depth > 0:
        ttype, tval = tokens[i]
        if ttype == "OPEN":
            depth += 1
            i += 1
        elif ttype == "CLOSE":
            depth -= 1
            i += 1
        elif depth == 1 and ttype == "WORD" and tval in GDP_MODIFIER_KEYS:
            # Look for = value
            if i + 2 < len(tokens) and tokens[i + 1][0] == "EQ":
                val_tok = tokens[i + 2]
                if val_tok[0] in ("WORD", "STR"):
                    try:
                        mods[tval] = float(val_tok[1])
                    except ValueError:
                        pass
                    i += 3
                    continue
            i += 1
        else:
            i += 1

    return mods


# ─── Country History Parsing ───────────────────────────────────────────────────


def parse_country_history(tag):
    """Parse a country's history file to get starting ideas and seeded variables."""
    for fname in os.listdir(COUNTRIES_DIR):
        if fname.startswith(f"{tag} ") and fname.endswith(".txt"):
            fpath = os.path.join(COUNTRIES_DIR, fname)
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
            except Exception:
                continue

            ideas = []
            # Find add_ideas blocks
            for m in re.finditer(r"add_ideas\s*=\s*\{([^}]+)\}", content):
                block = m.group(1)
                for line in block.split("\n"):
                    line = re.sub(r"#.*", "", line).strip()
                    if line and "=" not in line:
                        ideas.append(line)

            # Find seeded gdp_per_capita
            seeded_gdpc = None
            m = re.search(
                r"set_variable\s*=\s*\{\s*gdp_per_capita\s*=\s*([\d.]+)\s*\}",
                content,
            )
            if m:
                seeded_gdpc = float(m.group(1))

            # Find seeded resource extraction dynamic modifier variables
            # (e.g., doti_resource_extraction for USA DOI)
            dynamic_resource_vars = {}
            for vm in re.finditer(
                r"set_variable\s*=\s*\{\s*(\w+resource_extraction\w*)\s*=\s*([-\d.]+)\s*\}",
                content,
            ):
                dynamic_resource_vars[vm.group(1)] = float(vm.group(2))

            return {
                "ideas": ideas,
                "seeded_gdpc": seeded_gdpc,
                "dynamic_resource_vars": dynamic_resource_vars,
            }
    return {"ideas": [], "seeded_gdpc": None, "dynamic_resource_vars": {}}


# ─── State Parsing ─────────────────────────────────────────────────────────────


def parse_state_file(filepath):
    """Parse a state history file and extract relevant economic data."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    state = {
        "id": None,
        "name": os.path.basename(filepath),
        "owner": None,
        "manpower": 0,
        "productivity": 0,
        "buildings": defaultdict(int),
        "resources": defaultdict(float),
    }

    m = re.search(r"^\s*id\s*=\s*(\d+)", content, re.MULTILINE)
    if m:
        state["id"] = int(m.group(1))

    m = re.search(r"^\s*manpower\s*=\s*(\d+)", content, re.MULTILINE)
    if m:
        state["manpower"] = int(m.group(1))

    m = re.search(r"^\s*owner\s*=\s*(\w+)", content, re.MULTILINE)
    if m:
        state["owner"] = m.group(1)

    m = re.search(r"productivity_state_var\s*=\s*(\d+)", content)
    if m:
        state["productivity"] = int(m.group(1))

    res_match = re.search(r"resources\s*=\s*\{([^}]+)\}", content)
    if res_match:
        for rm in re.finditer(r"(\w+)\s*=\s*([\d.]+)", res_match.group(1)):
            res_name = rm.group(1)
            if res_name in RESOURCE_TYPES:
                state["resources"][res_name] = float(rm.group(2))

    history_match = re.search(r"history\s*=\s*\{", content)
    if history_match:
        bldg_match = re.search(r"buildings\s*=\s*\{", content[history_match.start() :])
        if bldg_match:
            bldg_start = history_match.start() + bldg_match.end()
            depth = 1
            i = bldg_start
            while i < len(content) and depth > 0:
                if content[i] == "{":
                    depth += 1
                elif content[i] == "}":
                    depth -= 1
                i += 1
            bldg_text = content[bldg_start : i - 1]

            clean_lines = []
            bdepth = 0
            for line in bldg_text.split("\n"):
                stripped = line.strip()
                bdepth += stripped.count("{") - stripped.count("}")
                if bdepth == 0 and "=" in stripped and not stripped.startswith("#"):
                    clean_lines.append(stripped)

            for line in clean_lines:
                bm = re.match(r"(\w+)\s*=\s*(\d+)", line)
                if bm:
                    bname = bm.group(1)
                    bcount = int(bm.group(2))
                    if bname in ALL_BUILDING_TYPES:
                        state["buildings"][bname] = bcount

    return state


# ─── GDP Calculation ───────────────────────────────────────────────────────────


def build_modifier_stack(idea_names, idea_db):
    """Build a combined modifier stack from a country's starting ideas."""
    stack = defaultdict(float)
    for idea in idea_names:
        if idea in idea_db:
            for mod_key, mod_val in idea_db[idea].items():
                stack[mod_key] += mod_val
    return dict(stack)


def calculate_gdp(states, modifier_stack=None):
    """
    Calculate GDP for a country, applying modifier stack from starting ideas.

    Follows the game's calculation chain from 00_money_system.txt.
    """
    if modifier_stack is None:
        modifier_stack = {}

    total_pop = sum(s["manpower"] for s in states)
    population_total_m = total_pop / 1_000_000
    population_total = total_pop / 100_000  # hundred-thousands, for healthcare

    if population_total_m <= 0:
        return None

    # Overall productivity (population-weighted average)
    overall_productivity = (
        sum(s["productivity"] * s["manpower"] for s in states) / total_pop
        if total_pop > 0
        else 0
    )

    # Aggregate buildings and resources
    buildings = defaultdict(int)
    base_resources = defaultdict(float)
    for s in states:
        for bname, bcount in s["buildings"].items():
            buildings[bname] += bcount
        for rname, rcount in s["resources"].items():
            base_resources[rname] += rcount

    # Apply per-resource modifiers (from environmental ideas etc.)
    total_resources = 0
    for rname, base_amount in base_resources.items():
        factor_key = RESOURCE_FACTOR_KEYS.get(rname)
        resource_factor = 1 + modifier_stack.get(factor_key, 0) if factor_key else 1
        total_resources += base_amount * resource_factor

    gdpc_converging = max(overall_productivity * 0.05, 2)

    # Workforce (line 4387-4393)
    workforce_mult = 1 + modifier_stack.get("total_workforce_modifier", 0)
    workforce_mult = max(0, min(1.5, workforce_mult))
    workforce_total = population_total_m * 0.6 * workforce_mult

    # --- Resource sector GDP (lines 4437-4444) ---
    gdp_from_resources = total_resources * RESOURCE_GDP_COEFF
    gdp_from_resources *= 1 + modifier_stack.get("gdp_from_resource_sector_modifier", 0)
    gdp_from_resources *= 1 + modifier_stack.get("local_resources_factor", 0)

    # --- Agriculture GDP (lines 4446-4487) ---
    if gdpc_converging < 1.3:
        agri_pct = gdpc_converging * -0.02 + 0.9
    else:
        threshold = 1.076
        temp_gdpc = max(gdpc_converging, threshold)
        agri_pct = (threshold * 0.9 / temp_gdpc) * (-threshold / temp_gdpc + 2)
        agri_pct = max(0.0, min(0.9, agri_pct))

    # Resource workers (lines 4403-4435)
    gdpc_safe = max(gdpc_converging, 0.1)
    resource_workers = total_resources * 0.075 / gdpc_safe
    max_resource_workers = workforce_total * 0.75
    actual_resource_workers = min(resource_workers, max_resource_workers)
    remaining_workforce = workforce_total - actual_resource_workers

    agriculture_workers = remaining_workforce * agri_pct
    agri_prod_mult = 1 + modifier_stack.get("agricolture_productivity_modifier", 0)
    gdp_from_agriculture = agriculture_workers * 2.75 * agri_prod_mult * 1.337
    remaining_workforce -= agriculture_workers

    # --- Building GDP (lines 4956-5027) ---
    fulfillment = 1.0  # assume full staffing at game start
    gdp_from_buildings = 0
    building_breakdown = {}

    for bname, (base, bonus_rate, mod_key) in BUILDING_GDP_FORMULA.items():
        count = buildings.get(bname, 0)
        if count > 0:
            # base contribution
            contribution = count * base
            # productivity bonus contribution
            if mod_key and bonus_rate > 0:
                mod_val = modifier_stack.get(mod_key, 0)
                contribution += count * bonus_rate * mod_val
            contribution *= fulfillment
            gdp_from_buildings += contribution
            building_breakdown[bname] = contribution

    # --- Healthcare GDP (lines 5029-5043) ---
    # Find health idea level from modifier stack or ideas
    health_mult = 0
    for hkey, hmult in HEALTH_GDP_MULT.items():
        # We detect health level from ideas passed in; stored in result
        pass  # handled below via health_idea parameter

    # --- Total pre-healthcare GDP ---
    productivity_mult = overall_productivity * 0.001
    gdp_pre_healthcare = gdp_from_buildings + gdp_from_agriculture + gdp_from_resources

    return {
        "population": total_pop,
        "population_m": population_total_m,
        "population_total": population_total,
        "overall_productivity": overall_productivity,
        "productivity_mult": productivity_mult,
        "gdpc_converging": gdpc_converging,
        "workforce_m": workforce_total,
        "total_resources": total_resources,
        "gdp_from_resources": gdp_from_resources,
        "gdp_from_agriculture": gdp_from_agriculture,
        "gdp_from_buildings": gdp_from_buildings,
        "gdp_pre_healthcare": gdp_pre_healthcare,
        "buildings": dict(buildings),
        "building_breakdown": building_breakdown,
        "num_states": len(states),
        "agri_worker_pct": agri_pct,
        "modifier_stack": modifier_stack,
    }


def finalize_gdp(result, health_idea=None, seeded_gdpc=None):
    """Apply productivity multiplier and healthcare GDP.

    If seeded_gdpc is provided (from country history), use it for the first
    healthcare calculation, then iterate to convergence. This matches the
    game's behavior where gdp_per_capita is preset in history files.
    """
    productivity_mult = result["productivity_mult"]
    population_total = result["population_total"]
    population_total_m = result["population_m"]
    gdp_pre_healthcare = result["gdp_pre_healthcare"]

    health_mult = HEALTH_GDP_MULT.get(health_idea, 0) if health_idea else 0

    # Start with non-healthcare GDP
    gdp_total = gdp_pre_healthcare * productivity_mult
    gdp_from_healthcare_pre = 0

    if health_mult > 0:
        # The game uses the PREVIOUS tick's gdp_per_capita (or the seeded value
        # from the history file on the first tick) to compute healthcare GDP.
        # It does NOT iterate within a single tick.
        if seeded_gdpc is not None:
            gdp_per_capita = seeded_gdpc
        else:
            # No seeded value: use initial estimate from gdpc_converging
            gdp_per_capita = (
                gdp_total / population_total_m if population_total_m > 0 else 0
            )

        healthcare_raw = population_total * 0.01 * gdp_per_capita * health_mult
        gdp_total = (gdp_pre_healthcare + healthcare_raw) * productivity_mult
        gdp_from_healthcare_pre = healthcare_raw

    gdp_total = max(gdp_total, 0.1)
    gdp_per_capita = gdp_total / population_total_m if population_total_m > 0 else 0

    result["gdp_from_healthcare"] = gdp_from_healthcare_pre * productivity_mult
    result["gdp_from_resources_scaled"] = (
        result["gdp_from_resources"] * productivity_mult
    )
    result["gdp_from_agriculture_scaled"] = (
        result["gdp_from_agriculture"] * productivity_mult
    )
    result["gdp_from_buildings_scaled"] = (
        result["gdp_from_buildings"] * productivity_mult
    )
    result["gdp_total"] = gdp_total
    result["gdp_per_capita"] = gdp_per_capita
    result["health_idea"] = health_idea or "none"
    result["building_breakdown_scaled"] = {
        k: v * productivity_mult for k, v in result["building_breakdown"].items()
    }
    return result


# ─── Main ──────────────────────────────────────────────────────────────────────


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    show_all = "--all" in args
    top_n = None
    if "--top" in args:
        idx = args.index("--top")
        top_n = int(args[idx + 1])
        args = [a for a in args if a not in ("--top", args[idx + 1])]

    verbose = "-v" in args or "--verbose" in args
    args = [a for a in args if a not in ("-v", "--verbose")]

    # Parse all idea definitions
    print("Loading idea definitions...", file=sys.stderr)
    idea_db = parse_all_ideas()
    print(f"  Loaded {len(idea_db)} ideas with GDP modifiers", file=sys.stderr)

    # Parse all state files
    print("Loading state files...", file=sys.stderr)
    country_states = defaultdict(list)
    for fname in os.listdir(STATES_DIR):
        if not fname.endswith(".txt"):
            continue
        fpath = os.path.join(STATES_DIR, fname)
        state = parse_state_file(fpath)
        if state["owner"]:
            country_states[state["owner"]].append(state)
    print(
        f"  Loaded {sum(len(v) for v in country_states.values())} states for {len(country_states)} countries",
        file=sys.stderr,
    )

    if show_all or top_n:
        tags = sorted(country_states.keys())
    else:
        tags = [a.upper() for a in args if not a.startswith("--")]

    results = []
    for tag in tags:
        if tag not in country_states:
            if not (show_all or top_n):
                print(f"WARNING: No states found for {tag}")
            continue

        states = country_states[tag]
        country_data = parse_country_history(tag)
        starting_ideas = country_data["ideas"]
        seeded_gdpc = country_data["seeded_gdpc"]
        modifier_stack = build_modifier_stack(starting_ideas, idea_db)

        # Apply dynamic resource extraction modifiers if found
        for var_name, var_val in country_data["dynamic_resource_vars"].items():
            # These typically apply to all resource types
            for rkey in RESOURCE_FACTOR_KEYS.values():
                modifier_stack[rkey] = modifier_stack.get(rkey, 0) + var_val

        # Detect health idea
        health_idea = None
        for idea in starting_ideas:
            if idea in HEALTH_GDP_MULT:
                health_idea = idea
                break

        result = calculate_gdp(states, modifier_stack)
        if result:
            result["tag"] = tag
            result["starting_ideas"] = starting_ideas
            result["seeded_gdpc"] = seeded_gdpc
            finalize_gdp(result, health_idea, seeded_gdpc)
            results.append(result)

    if top_n:
        results.sort(key=lambda r: r["gdp_total"], reverse=True)
        results = results[:top_n]

    if show_all or top_n:
        print(
            f"\n{'Rank':>4}  {'TAG':<5} {'GDP Total':>12} {'GDP/C':>8} "
            f"{'Pop (M)':>10} {'Productivity':>12} {'Health':>10} {'States':>6}"
        )
        print("-" * 78)
        for i, r in enumerate(results, 1):
            pop_m = r["population"] / 1_000_000
            print(
                f"{i:>4}  {r['tag']:<5} {r['gdp_total']:>12.2f} {r['gdp_per_capita']:>8.2f} "
                f"{pop_m:>10.2f} {r['overall_productivity']:>12.1f} "
                f"{r['health_idea']:>10} {r['num_states']:>6}"
            )
    else:
        for r in results:
            tag = r["tag"]
            pop_m = r["population"] / 1_000_000
            print(f"\n{'='*65}")
            print(f"  {tag} - GDP Estimation (with modifier stack)")
            print(f"{'='*65}")
            print(f"  States:              {r['num_states']}")
            print(f"  Population:          {pop_m:.2f}M")
            print(f"  Overall Productivity:{r['overall_productivity']:.1f}")
            print(f"  Productivity Mult:   {r['productivity_mult']:.3f}")
            print(f"  GDP/C Converging:    {r['gdpc_converging']:.2f}")
            print(f"  Health Level:        {r['health_idea']}")
            print(f"  Agri Worker %:       {r['agri_worker_pct']:.1%}")
            print()
            print(f"  GDP Total:           {r['gdp_total']:.2f}")
            print(f"  GDP per Capita:      {r['gdp_per_capita']:.2f}")
            print()
            gdp = r["gdp_total"]
            b = r["gdp_from_buildings_scaled"]
            h = r["gdp_from_healthcare"]
            a = r["gdp_from_agriculture_scaled"]
            res = r["gdp_from_resources_scaled"]
            print(f"  GDP Breakdown:")
            print(f"    Buildings:         {b:.2f} ({b/gdp*100:.1f}%)")
            print(f"    Healthcare:        {h:.2f} ({h/gdp*100:.1f}%)")
            print(f"    Agriculture:       {a:.2f} ({a/gdp*100:.1f}%)")
            print(f"    Resources:         {res:.2f} ({res/gdp*100:.1f}%)")
            print()
            if r["buildings"]:
                print(f"  Buildings:")
                for bname, bcount in sorted(
                    r["buildings"].items(), key=lambda x: -x[1]
                ):
                    gdp_c = r["building_breakdown_scaled"].get(bname, 0)
                    if gdp_c > 0:
                        print(f"    {bname:<25} x{bcount:>4}  -> GDP: {gdp_c:.2f}")
                    else:
                        print(f"    {bname:<25} x{bcount:>4}")

            # Show active modifiers
            ms = r["modifier_stack"]
            active = {k: v for k, v in ms.items() if abs(v) > 0.001}
            if active and verbose:
                print()
                print(
                    f"  Active GDP Modifiers (from {len(r['starting_ideas'])} ideas):"
                )
                for mk in sorted(active):
                    print(f"    {mk:<45} {active[mk]:+.3f}")
            elif active:
                # Show count
                print(f"\n  Modifiers: {len(active)} active " f"(use -v for details)")
            print()


if __name__ == "__main__":
    main()
