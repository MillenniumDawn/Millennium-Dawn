#!/usr/bin/env python3
"""
Pre-place fossil power plants, composite factories, and the nuclear reactor
material stockpile into history files.

Replaces the runtime `setup_starting_fossil_powerplants`, `composite_building_add`,
and `setup_starting_reactor_stockpile` effects that ran in on_startup. By baking
these into the state and country history, the engine sees the correct building
counts and the nuclear stockpile before the first `calculate_energy_use` pass —
so nuclear comes online on the first tick instead of after a manual refresh.

Re-run this tool after any change that shifts the per-country energy balance:
    - energy formula constants in common/scripted_effects/!_energy_effects.txt
    - per-country composite seeds in tools/analysis/composite_factory_seeds.csv
    - state ownership, population, productivity, or building counts in history/states/
    - state-level nuclear_reactor placement (changes the baked stockpile)
    - ideas that touch `energy_use_*`, `energy_gain_*`, or `fossil_*` modifiers

The tool is idempotent: a second `--write` after the data has stabilised produces
no diffs. Use `--dry-run` to preview the impact before committing.

Usage:
    python3 tools/analysis/pre_place_power_plants.py --dry-run
    python3 tools/analysis/pre_place_power_plants.py --dry-run --top 20
    python3 tools/analysis/pre_place_power_plants.py --write
    python3 tools/analysis/pre_place_power_plants.py --write --only USA,CHI,GER
"""

import argparse
import math
import os
import re
import sys
from collections import defaultdict

# Reuse estimate_gdp's parsers for ideas, country history, and state files.
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if THIS_DIR not in sys.path:
    sys.path.insert(0, THIS_DIR)

from estimate_gdp import (
    COUNTRIES_DIR,
    HEALTH_GDP_MULT,
    RESOURCE_FACTOR_KEYS,
    STATES_DIR,
    build_modifier_stack,
)
from estimate_gdp import calculate_gdp as _calculate_gdp  # noqa: E402
from estimate_gdp import finalize_gdp as _finalize_gdp
from estimate_gdp import (
    parse_all_ideas,
    parse_country_history,
    parse_state_file_from_content,
)

REPO_ROOT = os.path.abspath(os.path.join(THIS_DIR, "..", ".."))

# ─── Energy formula constants (mirror !_energy_effects.txt) ────────────────────
ENERGY_USE_BALANCE_MULT = 1.25
POP_ENERGY_BALANCE = 28
FOSSIL_GW_PER_PLANT = (
    2  # base modifier@fossil_energy_gain from common/buildings/00_buildings.txt:344
)
NUCLEAR_GW_PER_REACTOR = (
    4  # nuclear_energy_gain in common/buildings/00_buildings.txt:169
)
NUCLEAR_FUEL_PER_REACTOR = (
    2500  # snapshot of the (removed) setup_starting_reactor_stockpile multiplier
)
RENEWABLE_BASE_GW = 0.5  # per renewable_energy_infra level
STATE_FOSSIL_CAP = 21  # match runtime limit { building_level@fossil_powerplant < 21 }

BUILDING_ENERGY_COEFF = {
    "industrial_complex": 0.5,
    "offices": 0.25,
    "agriculture_district": 0.10,
    "arms_factory": 0.5,
    "dockyard": 0.5,
    "microchip_plant": 0.75,
    "composite_plant": 0.8,
    "synthetic_refinery": 0.2,
}

# ─── Helpers ────────────────────────────────────────────────────────────────────


_RENEWABLE_VAR_PATTERNS = {
    var: re.compile(rf"set_variable\s*=\s*\{{\s*{var}\s*=\s*([-\d.]+)")
    for var in (
        "hydroelectric_energy_production_var",
        "geothermal_energy_production_var",
        "state_renewable_capacity_factor_modifier_var",
    )
}


def collect_state_renewable_vars(content, state):
    """Pull set_variable hydroelectric/geothermal/renewable_capacity values from state content."""
    for var, pat in _RENEWABLE_VAR_PATTERNS.items():
        m = pat.search(content)
        if m:
            try:
                state[var] = float(m.group(1))
            except ValueError:
                pass


COMPOSITE_SEED_CSV = os.path.join(THIS_DIR, "composite_factory_seeds.csv")


def load_composite_seed_values():
    """Return {tag: seed} from composite_factory_seeds.csv.

    These were formerly `startup_composite_fac_needed` set_variable seeds in
    history/countries/. The runtime effect that read them (composite_building_add_multi)
    was removed once its output got baked into state history, so the seeds now live
    here as pure tool input. Missing file or row → seed defaults to 0.
    """
    seeds = {}
    if not os.path.exists(COMPOSITE_SEED_CSV):
        return seeds
    with open(COMPOSITE_SEED_CSV, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line.lower().startswith("tag,"):
                continue
            parts = line.split(",")
            if len(parts) < 2:
                continue
            try:
                seeds[parts[0].strip()] = int(parts[1].strip())
            except ValueError:
                continue
    return seeds


def parse_composite_seeds():
    """Return {tag: count} for each country that had the composite special project
    completed at startup. Mirrors the old runtime: 1 plant from composite_building_add
    plus N from composite_building_add_multi (where N = the per-country seed in
    composite_factory_seeds.csv).
    """
    seed_values = load_composite_seed_values()
    seeds = {}
    project_pat = re.compile(
        r"complete_special_project\s*=\s*sp:sp_composite_production\b"
    )
    for fname in os.listdir(COUNTRIES_DIR):
        if not fname.endswith(".txt"):
            continue
        tag = fname.split(" ")[0]
        with open(
            os.path.join(COUNTRIES_DIR, fname), "r", encoding="utf-8", errors="replace"
        ) as f:
            content = f.read()
        if not project_pat.search(content):
            continue
        seeds[tag] = seed_values.get(tag, 0) + 1
    return seeds


def energy_consumption(states, modifier_stack, gdpc):
    """Approximate energy consumption (GW), mirroring calculate_energy_use.

    `gdpc` is the gdp_per_capita the engine will see in calculate_energy_use,
    i.e. the result of the first calculate_gdp pass (not the seeded value).
    Pass it directly so the bake's consumption math tracks what the engine
    actually computes on the first tick.
    """
    total_pop = sum(s["manpower"] for s in states)
    if total_pop == 0:
        return 0.0
    population_total = total_pop / 100_000  # hundred-thousands

    if gdpc is None or gdpc <= 0:
        # Fallback for paper tags without states / GDP — match engine clamp.
        gdpc = 2

    pop_use_mult = 1 + modifier_stack.get("pop_energy_use_multiplier", 0)
    energy_use_mult = 1 + modifier_stack.get("energy_use_multiplier", 0)

    # Population energy: pop_total(100k) * 0.001 * pop_mult * gdpc * 0.025 * 28
    pop_energy = (
        population_total * 0.001 * pop_use_mult * gdpc * 0.025 * POP_ENERGY_BALANCE
    )

    buildings = defaultdict(int)
    for s in states:
        for b, c in s["buildings"].items():
            buildings[b] += c

    # Engine groups industrial_complex under "civs"; arms_factory and dockyard each have a dedicated modifier;
    # the rest use a per-type modifier key.
    BUILDING_MODIFIER_KEY = {
        "arms_factory": "energy_use_modifier_mils",
        "dockyard": "energy_use_modifier_dockyards",
        "industrial_complex": "energy_use_modifier_civs",
    }
    bldg_energy = 0
    for bname, coeff in BUILDING_ENERGY_COEFF.items():
        count = buildings.get(bname, 0)
        mod_key = BUILDING_MODIFIER_KEY.get(bname, f"energy_use_modifier_{bname}")
        mult = 1 + modifier_stack.get(mod_key, 0)
        bldg_energy += count * mult * coeff

    other_energy = modifier_stack.get("energy_use", 0)

    total = (pop_energy + bldg_energy + other_energy) * energy_use_mult
    total *= ENERGY_USE_BALANCE_MULT
    return max(total, 0.001)


def energy_supply_non_fossil(states, modifier_stack, has_nuclear):
    """Approximate energy supply (GW) excluding fossil plants."""
    energy_gain_mult = 1 + modifier_stack.get("energy_gain_multiplier", 0)

    # Renewables: sum(infra * 0.5 * avg_random_factor), adjusted by per-state min cap
    renewables = 0
    for s in states:
        infra = s["buildings"].get("renewable_energy_infra", 0)
        if infra > 0:
            factor = s.get("state_renewable_capacity_factor_modifier_var", 1.0)
            avg_factor = factor / 2  # monthly output = rand(0..1) * factor, so expected value is factor/2
            renewables += infra * RENEWABLE_BASE_GW * avg_factor
    ren_mult = 1 + modifier_stack.get("renewable_energy_gain_multiplier", 0)
    renewables *= ren_mult * energy_gain_mult

    # Hydro & geothermal from per-state seeded variables
    hydro = sum(s.get("hydroelectric_energy_production_var", 0) for s in states)
    geo = sum(s.get("geothermal_energy_production_var", 0) for s in states)
    hydro *= (
        1 + modifier_stack.get("hydroelectric_power_generation_modifier", 0)
    ) * energy_gain_mult
    geo *= (
        1 + modifier_stack.get("geothermal_power_generation_modifier", 0)
    ) * energy_gain_mult

    # Nuclear
    nuclear = 0
    if has_nuclear:
        reactors = sum(s["buildings"].get("nuclear_reactor", 0) for s in states)
        nuclear_mult = 1 + modifier_stack.get("nuclear_energy_generation_modifier", 0)
        nuclear = reactors * NUCLEAR_GW_PER_REACTOR * nuclear_mult * energy_gain_mult

    other = modifier_stack.get("energy_gain", 0) * energy_gain_mult

    return renewables + hydro + geo + nuclear + other


def fossil_plants_needed(consumption, supply, safety_gw=2.0):
    """Compute how many fossil power plants to pre-place.

    Returns ceil((consumption + safety_gw - supply) / 2), clamped to min 1.

    `safety_gw` adds a 1-plant buffer of headroom. The bake model approximates
    the engine's first-tick energy math but loses a few GW per country to
    unmodelled effects: state controlled-vs-owned aggregation, manpower
    fulfillment scaling, drift in estimate_gdp's healthcare constants vs the
    engine's `health_gdp_level_mult`, the unrolled renewable random factor on
    first tick, etc. Without a buffer, marginal-balance countries (SOV, CHI,
    ETH) land just short in-game even though the bake's projection is
    "balanced." A 2 GW pad covers the noise; the engine's
    `free_fossil_powerplants_power` auto-throttle absorbs any incidental
    surplus on the high end.
    """
    gap = consumption + safety_gw - supply
    if gap <= 0:
        return 1
    return max(1, math.ceil(gap / 2))


# ─── State weight + distribution ───────────────────────────────────────────────


_CATEGORY_TIER_RE = re.compile(r"state_(\d+)")


def state_weight(s):
    """Higher weight = more likely to receive plants. Mirrors 'industrial state' bias."""
    cat = s.get("state_category", "state_00")
    m = _CATEGORY_TIER_RE.fullmatch(cat)
    tier = int(m.group(1)) if m else 0
    industry = (
        s["buildings"].get("industrial_complex", 0)
        + s["buildings"].get("arms_factory", 0)
        + s["buildings"].get("offices", 0)
    )
    manpower = s["manpower"] / 1_000_000  # millions
    return tier * 2 + industry * 3 + manpower + 1


def composite_weight(s):
    """Composite plants supply military-industrial inputs (aerospace, advanced materials),
    so prefer states that already host arms factories or dockyards."""
    arms = s["buildings"].get("arms_factory", 0)
    docks = s["buildings"].get("dockyard", 0)
    if arms == 0 and docks == 0:
        # Fall back to general industrial weight at a heavy discount so unrelated
        # states only receive composites when no military-industrial state has room.
        return state_weight(s) * 0.1
    return arms * 5 + docks * 3 + state_weight(s)


def distribute(count, states, building_name, cap=STATE_FOSSIL_CAP, weight_fn=None):
    """Distribute `count` plants across states by weight. Returns dict state_id -> N."""
    if count <= 0 or not states:
        return {}
    if weight_fn is None:
        weight_fn = state_weight
    placed = defaultdict(int)
    # Sort by weight desc, then state_id for deterministic order
    ranked = sorted(states, key=lambda s: (-weight_fn(s), s["id"]))
    # Weighted round-robin: pick the state whose current "deficit vs weight share" is largest.
    total_weight = sum(weight_fn(s) for s in ranked)
    if total_weight == 0:
        total_weight = len(ranked)
    target = {s["id"]: weight_fn(s) / total_weight * count for s in ranked}

    for _ in range(count):
        best, best_gap = None, -1
        for s in ranked:
            existing = s["buildings"].get(building_name, 0) + placed[s["id"]]
            if existing >= cap:
                continue
            gap = target[s["id"]] - placed[s["id"]]
            if gap > best_gap:
                best_gap = gap
                best = s
        if best is None:
            # All states capped; nothing else we can do
            break
        placed[best["id"]] += 1
    return dict(placed)


# ─── State parsing extension ────────────────────────────────────────────────────


_STATE_CATEGORY_RE = re.compile(r"^\s*state_category\s*=\s*(\w+)", re.MULTILINE)


def parse_state_with_category(filepath):
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    state = parse_state_file_from_content(content, os.path.basename(filepath))
    state["filepath"] = filepath
    m = _STATE_CATEGORY_RE.search(content)
    if m:
        state["state_category"] = m.group(1)
    collect_state_renewable_vars(content, state)
    return state


# ─── State file rewriting ──────────────────────────────────────────────────────


def inject_building(filepath, building_name, count):
    """Insert or update `building_name = count` inside history.buildings = {}."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    hist_m = re.search(r"\bhistory\s*=\s*\{", content)
    if not hist_m:
        return False, "no history block"

    bldg_m = re.search(r"\bbuildings\s*=\s*\{", content[hist_m.end() :])
    if bldg_m:
        bldg_open = hist_m.end() + bldg_m.end()
        depth = 1
        i = bldg_open
        while i < len(content) and depth > 0:
            if content[i] == "{":
                depth += 1
            elif content[i] == "}":
                depth -= 1
            i += 1
        bldg_close = i - 1  # position of the closing brace
        block = content[bldg_open:bldg_close]
        # Detect existing top-level entry for building_name (key = N, not nested in province block)
        # Walk block respecting depth; only match at depth 0.
        new_block = _replace_or_append_top_level(block, building_name, count)
        if new_block == block:
            return False, "no change"
        content = content[:bldg_open] + new_block + content[bldg_close:]
    else:
        # No buildings block — create one. MD/HOI4 convention is `owner = TAG`
        # first inside `history = { ... }`, then everything else. Insert the
        # new buildings block on the line after `owner = TAG`; fall back to
        # right after `history = {` only if owner isn't found (paper tags).
        indent = "\t\t"
        owner_m = re.search(r"\bowner\s*=\s*\w+[ \t]*\n", content[hist_m.end() :])
        if owner_m:
            insert_at = hist_m.end() + owner_m.end()
            content = (
                content[:insert_at]
                + f"{indent}buildings = {{\n{indent}\t{building_name} = {count}\n{indent}}}\n"
                + content[insert_at:]
            )
        else:
            insert_at = hist_m.end()
            content = (
                content[:insert_at]
                + f"\n{indent}buildings = {{\n{indent}\t{building_name} = {count}\n{indent}}}"
                + content[insert_at:]
            )

    with open(filepath, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    return True, "written"


_TOP_LEVEL_KEY_RE = re.compile(r"(\s*)(\w+)(\s*)=")
_SAMPLE_INDENT_RE = re.compile(r"^([ \t]+)\w+\s*=", re.MULTILINE)


def _replace_or_append_top_level(block, key, value):
    """Inside a `{ ... }` block (without surrounding braces), replace or append `key = value` at depth 0."""
    depth = 0
    i = 0
    keyword_start = -1
    found_end = -1
    while i < len(block):
        c = block[i]
        if c == "{":
            depth += 1
            i += 1
            continue
        if c == "}":
            depth -= 1
            i += 1
            continue
        if depth == 0:
            m = _TOP_LEVEL_KEY_RE.match(block, i)
            if m and m.group(2) == key:
                eq_end = m.end()
                j = eq_end
                while j < len(block) and block[j] in " \t":
                    j += 1
                if j < len(block) and block[j] == "{":
                    # Nested block (e.g. province-scoped) - not a simple key=N, skip.
                    i = m.end()
                    continue
                k = j
                while k < len(block) and block[k] not in " \t\r\n":
                    k += 1
                keyword_start = m.start(2)
                found_end = k
                break
            if m:
                i = m.end()
                continue
        i += 1

    if keyword_start >= 0:
        # Replace the entire `key = N` token, preserving indent before keyword.
        return block[:keyword_start] + f"{key} = {value}" + block[found_end:]

    # Append new entry. Pick indentation by scanning for the first top-level entry.
    indent = "\t\t\t"
    sample = _SAMPLE_INDENT_RE.search(block)
    if sample:
        indent = sample.group(1)
    trail = block.rstrip("\n\r\t ")
    return f"{trail}\n{indent}{key} = {value}" + block[len(trail) :]


# ─── Country history: reactor stockpile injection ──────────────────────────────


def find_country_file(tag):
    """Return the absolute path to the country history file for TAG, or None."""
    for fname in os.listdir(COUNTRIES_DIR):
        if fname.startswith(f"{tag} ") and fname.endswith(".txt"):
            return os.path.join(COUNTRIES_DIR, fname)
    return None


_ENRICHMENT_VALUE_RE = re.compile(
    r"set_variable\s*=\s*\{\s*enrichment_facilities\s*=\s*(\d+)"
)
_STOCKPILE_RE = re.compile(
    r"(?P<indent>[ \t]*)set_variable\s*=\s*\{\s*var_reactor_material_stockpile\s*=\s*[-\d.]+\s*\}"
)
_REACTOR_FLAG_RE = re.compile(
    r"set_country_flag\s*=\s*enabled_nuclear_reactor_fuel_production\b"
)
_ENRICHMENT_BLOCK_RE = re.compile(
    r"(?P<indent>[ \t]*)add_to_array\s*=\s*\{\s*global\.enrichment_countries\s*=\s*THIS\.id\s*\}[ \t]*\n"
)
_OVERALL_PRODUCTIVITY_RE = re.compile(
    r"(?P<indent>[ \t]*)set_variable\s*=\s*\{\s*overall_productivity\s*=\s*[-\d.]+\s*\}[ \t]*\n"
)


def read_enrichment_count(content):
    """Return the country's enrichment_facilities value from the country history content, or 0."""
    m = _ENRICHMENT_VALUE_RE.search(content)
    return int(m.group(1)) if m else 0


def inject_reactor_stockpile(filepath, stockpile, set_flag):
    """Inject (or update) var_reactor_material_stockpile and optionally the
    enabled_nuclear_reactor_fuel_production flag into a country history file.

    Placement:
      - After `add_to_array = { global.enrichment_countries = THIS.id }` if present.
      - Else after `set_variable = { overall_productivity = N }`.

    Returns (changed: bool, msg: str). Idempotent: re-running on a stabilised file
    produces no diff.
    """
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    original = content

    stockpile_target = (
        f"set_variable = {{ var_reactor_material_stockpile = {stockpile} }}"
    )

    # ── Step 1: stockpile var (replace or insert) ──
    existing = _STOCKPILE_RE.search(content)
    if existing:
        indent = existing.group("indent")
        content = (
            content[: existing.start()]
            + f"{indent}{stockpile_target}"
            + content[existing.end() :]
        )
    else:
        anchor = _ENRICHMENT_BLOCK_RE.search(
            content
        ) or _OVERALL_PRODUCTIVITY_RE.search(content)
        if not anchor:
            return (
                False,
                "no anchor (no enrichment_countries / overall_productivity line)",
            )
        indent = anchor.group("indent")
        content = (
            content[: anchor.end()]
            + f"{indent}{stockpile_target}\n"
            + content[anchor.end() :]
        )

    # ── Step 2: flag (insert after stockpile line if requested and not present) ──
    if set_flag and not _REACTOR_FLAG_RE.search(content):
        m = _STOCKPILE_RE.search(content)
        indent = m.group("indent")
        # Insert on the next line after the stockpile assignment.
        line_end = content.find("\n", m.end())
        if line_end == -1:
            line_end = len(content)
        content = (
            content[: line_end + 1]
            + f"{indent}set_country_flag = enabled_nuclear_reactor_fuel_production\n"
            + content[line_end + 1 :]
        )

    if content == original:
        return False, "no change"

    with open(filepath, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    return True, "written"


# ─── Main ──────────────────────────────────────────────────────────────────────


def gather_country_data():
    """Returns dict tag -> {states, ideas, seeded_gdpc, modifier_stack, has_nuclear}."""
    print("Loading idea definitions...", file=sys.stderr)
    idea_db = parse_all_ideas()

    print("Loading state files...", file=sys.stderr)
    country_states = defaultdict(list)
    for fname in os.listdir(STATES_DIR):
        if not fname.endswith(".txt"):
            continue
        fpath = os.path.join(STATES_DIR, fname)
        s = parse_state_with_category(fpath)
        if s["owner"]:
            country_states[s["owner"]].append(s)

    results = {}
    for tag, states in country_states.items():
        country_data = parse_country_history(tag)
        modifier_stack = build_modifier_stack(country_data["ideas"], idea_db)
        # Apply dynamic resource extraction modifiers (mirrors estimate_gdp's main loop).
        for var_name, var_val in country_data.get("dynamic_resource_vars", {}).items():
            for rkey in RESOURCE_FACTOR_KEYS.values():
                modifier_stack[rkey] = modifier_stack.get(rkey, 0) + var_val
        has_nuclear = any(
            i in ("nuclear_energy", "nuclear_power_off", "nuclear_power_def")
            for i in country_data["ideas"]
        )

        # Run the same GDP pipeline the engine runs on the first calculate_gdp
        # pass. This is what calculate_energy_use will see for `gdp_per_capita` —
        # NOT the seeded value, NOT gdpc_converging_var. Using the seeded value
        # underestimates consumption for countries whose history seeds a gdpc
        # well below the calculated one (VEN, ITA, RAJ).
        engine_gdpc = None
        gdp_result = _calculate_gdp(states, modifier_stack)
        if gdp_result:
            health_idea = next(
                (i for i in country_data["ideas"] if i in HEALTH_GDP_MULT),
                None,
            )
            _finalize_gdp(gdp_result, health_idea, country_data["seeded_gdpc"])
            engine_gdpc = gdp_result.get("gdp_per_capita")

        results[tag] = {
            "states": states,
            "ideas": country_data["ideas"],
            "seeded_gdpc": country_data["seeded_gdpc"],
            "engine_gdpc": engine_gdpc,
            "modifier_stack": modifier_stack,
            "has_nuclear": has_nuclear,
        }
    return results


def compute_placements(country_data, composite_seeds):
    """For each country: fossil count, composite count, per-state distribution.

    Composites contribute to energy consumption (0.8 GW each × balance multiplier),
    so we plan composites first and include them in the consumption calculation
    before computing fossil plant need.
    """
    plan = {}
    for tag, c in country_data.items():
        # ─── Composites first (they affect energy consumption) ────────────────
        composite_total = composite_seeds.get(tag, 0)
        composite_existing = sum(
            s["buildings"].get("composite_plant", 0) for s in c["states"]
        )
        composite_to_add = max(0, composite_total - composite_existing)
        composite_dist = distribute(
            composite_to_add,
            c["states"],
            "composite_plant",
            cap=999,
            weight_fn=composite_weight,
        )

        # Temporarily inject planned composites so energy_consumption sees them.
        # Use an ephemeral building map per state so we don't mutate the
        # state["buildings"] dict that apply_plan will later read.
        states_for_energy = []
        for s in c["states"]:
            added = composite_dist.get(s["id"], 0)
            if added:
                ephemeral = dict(s)
                ephemeral["buildings"] = dict(s["buildings"])
                ephemeral["buildings"]["composite_plant"] = (
                    s["buildings"].get("composite_plant", 0) + added
                )
                states_for_energy.append(ephemeral)
            else:
                states_for_energy.append(s)

        # ─── Fossil plants ────────────────────────────────────────────────────
        consumption = energy_consumption(
            states_for_energy, c["modifier_stack"], c["engine_gdpc"]
        )
        supply = energy_supply_non_fossil(
            states_for_energy, c["modifier_stack"], c["has_nuclear"]
        )
        fossil = fossil_plants_needed(consumption, supply)

        existing = sum(s["buildings"].get("fossil_powerplant", 0) for s in c["states"])
        fossil_to_add = max(0, fossil - existing)
        fossil_dist = distribute(fossil_to_add, c["states"], "fossil_powerplant")

        # ─── Nuclear stockpile (bake setup_starting_reactor_stockpile) ────────
        reactor_count = sum(
            s["buildings"].get("nuclear_reactor", 0) for s in c["states"]
        )
        stockpile = reactor_count * NUCLEAR_FUEL_PER_REACTOR
        country_file = find_country_file(tag)
        enrichment = 0
        if country_file:
            with open(country_file, "r", encoding="utf-8", errors="replace") as f:
                enrichment = read_enrichment_count(f.read())

        plan[tag] = {
            "consumption": consumption,
            "supply_non_fossil": supply,
            "fossil_needed": fossil,
            "fossil_existing": existing,
            "fossil_added": sum(fossil_dist.values()),
            "fossil_dist": fossil_dist,
            "composite_total": composite_total,
            "composite_added": sum(composite_dist.values()),
            "composite_dist": composite_dist,
            "reactor_count": reactor_count,
            "reactor_stockpile": stockpile,
            "enrichment": enrichment,
            "country_file": country_file,
        }
    return plan


def apply_plan(plan, country_data, write=False, only=None):
    """Apply the plan: rewrite state and country history files (write=True) or count (write=False)."""
    by_state_file = defaultdict(dict)  # filepath -> {building: count_delta}
    state_lookup = {}
    for tag, c in country_data.items():
        for s in c["states"]:
            state_lookup[s["id"]] = s

    country_edits = []  # list of (filepath, stockpile, set_flag)
    for tag, p in plan.items():
        if only and tag not in only:
            continue
        for sid, n in p["fossil_dist"].items():
            if n > 0:
                s = state_lookup[sid]
                existing = s["buildings"].get("fossil_powerplant", 0)
                by_state_file[s["filepath"]]["fossil_powerplant"] = existing + n
        for sid, n in p["composite_dist"].items():
            if n > 0:
                s = state_lookup[sid]
                existing = s["buildings"].get("composite_plant", 0)
                by_state_file[s["filepath"]]["composite_plant"] = existing + n
        if p["reactor_count"] > 0 and p["country_file"]:
            country_edits.append(
                (p["country_file"], p["reactor_stockpile"], p["enrichment"] > 0)
            )

    if not write:
        return len(by_state_file) + len(country_edits)

    written = 0
    for fpath, edits in by_state_file.items():
        for bname, total in edits.items():
            ok, msg = inject_building(fpath, bname, total)
            if ok:
                written += 1
    for fpath, stockpile, set_flag in country_edits:
        ok, msg = inject_reactor_stockpile(fpath, stockpile, set_flag)
        if ok:
            written += 1
    return written


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true", help="Apply changes to state files")
    ap.add_argument("--dry-run", action="store_true", help="Report only (default)")
    ap.add_argument(
        "--top", type=int, default=None, help="Show top N countries by fossil plants"
    )
    ap.add_argument("--only", default=None, help="Comma-separated tags to limit output")
    args = ap.parse_args()

    country_data = gather_country_data()
    composite_seeds = parse_composite_seeds()

    print(
        f"Loaded {len(country_data)} countries, {len(composite_seeds)} composite seeds",
        file=sys.stderr,
    )

    # Project countries that own 0 startup states are release-only paper tags
    # (e.g., Northern Ireland, Aegist). The runtime's random_owned_controlled_state
    # silently no-ops for them; the bake does the same. Flag them so the operator
    # knows the seed total won't fully land in state files.
    orphan_project_tags = sorted(t for t in composite_seeds if t not in country_data)
    if orphan_project_tags:
        print(
            f"  note: {len(orphan_project_tags)} composite-project countries own 0 startup states "
            f"and will be skipped: {', '.join(orphan_project_tags)}",
            file=sys.stderr,
        )

    plan = compute_placements(country_data, composite_seeds)

    only = set(args.only.split(",")) if args.only else None
    rows = []
    for tag, p in plan.items():
        if only and tag not in only:
            continue
        rows.append((tag, p))
    rows.sort(key=lambda r: -r[1]["fossil_added"])
    if args.top:
        rows = rows[: args.top]

    print(
        f"\n{'TAG':<5}  {'Use(GW)':>8} {'Sup(GW)':>8} {'Gap(GW)':>8} "
        f"{'Foss':>5} {'Have':>5} {'Add':>5} {'Comp+':>6} {'Rx':>4} {'Stkpl':>7}"
    )
    print("-" * 75)
    for tag, p in rows:
        gap = p["consumption"] - p["supply_non_fossil"]
        print(
            f"{tag:<5}  {p['consumption']:>8.1f} {p['supply_non_fossil']:>8.1f} "
            f"{gap:>8.1f} {p['fossil_needed']:>5} {p['fossil_existing']:>5} "
            f"{p['fossil_added']:>5} {p['composite_added']:>6} "
            f"{p['reactor_count']:>4} {p['reactor_stockpile']:>7}"
        )

    if args.write:
        n = apply_plan(plan, country_data, write=True, only=only)
        print(
            f"\nWrote {n} building/stockpile entries across state + country files.",
            file=sys.stderr,
        )
    else:
        n = apply_plan(plan, country_data, write=False, only=only)
        print(
            f"\nDry run: {n} state + country files would be modified. Use --write to apply.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
