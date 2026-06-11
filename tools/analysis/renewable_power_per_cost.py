#!/usr/bin/env python3
"""Plot power per build-cost over time for renewable / nuclear / fossil power.

"Build cost" = the construction effort civilian factories must spend, i.e. the
building's ``base_cost`` reduced by the cumulative construction-speed techs
(``base_cost / (1 + production_speed_<building>_factor)``). It is NOT the in-game
"$" figure (that is foreign-investment / income, a different system).

    power  = base_GW * state_factor(renewable only) * (1 + sum of power-output techs)
    effort = base_cost / (1 + sum of construction-speed techs)
    metric = power / effort

Each x value is a year in which every technology with start_year <= that year is
researched on-time. The renewable, nuclear and fossil tech values (power-output and
construction-speed multipliers, plus start_years) are parsed live from
common/technologies/industry.txt so the chart stays in sync with the mod. Building
base_GW and base_cost are from common/buildings/00_buildings.txt.

    python tools/analysis/renewable_power_per_cost.py [--out chart.png]

Needs matplotlib.
"""
from __future__ import annotations

import argparse
import os
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INDUSTRY = os.path.join(REPO, "common", "technologies", "industry.txt")

# --- building stats (common/buildings/00_buildings.txt) ---------------------
BASE_GW = {"ren": 0.5, "nuc": 4.0, "fos": 2.0}        # *_energy_gain, GW per level
BASE_COST = {"ren": 50000, "nuc": 50000, "fos": 9500}  # base_cost, construction effort per level

# modifier names: (power-output tech, construction-speed tech) per power type
MODS = {
    "ren": ("renewable_energy_gain_multiplier", "production_speed_renewable_energy_infra_factor"),
    "nuc": ("nuclear_energy_generation_modifier", "production_speed_nuclear_reactor_factor"),
    "fos": ("fossil_pp_energy_generation_modifier", "production_speed_fossil_powerplant_factor"),
}
FACTORS = [0.5, 1.0, 1.5]


def parse_techs(path):
    """Return {tech_name: {modifier: value, ..., 'start_year': int}} for every tech."""
    text = open(path, encoding="utf-8-sig").read()
    lines = [ln.split("#", 1)[0] for ln in text.split("\n")]   # strip comments
    head = re.compile(r"^\t([A-Za-z_]\w*)\s*=\s*\{\s*$")
    num = re.compile(r"^\s*([A-Za-z_]\w*)\s*=\s*(-?[0-9]+(?:\.[0-9]+)?)\s*$")
    techs, i, n = {}, 0, len(lines)
    while i < n:
        m = head.match(lines[i])
        if not m:
            i += 1
            continue
        name, depth, fields, i = m.group(1), 1, {}, i + 1
        while i < n and depth > 0:
            depth += lines[i].count("{") - lines[i].count("}")
            fm = num.match(lines[i])
            if fm:
                fields[fm.group(1)] = float(fm.group(2))
            i += 1
        techs[name] = fields
    return techs


def build_chains(techs):
    """For each power type build a sorted list of (year, power_inc, speed_inc, name)."""
    chains = {}
    for key, (pmod, smod) in MODS.items():
        rows = []
        for name, f in techs.items():
            p, s = f.get(pmod, 0.0), f.get(smod, 0.0)
            if (p or s) and "start_year" in f:
                rows.append((int(f["start_year"]), p, s, name))
        chains[key] = sorted(rows)
    return chains


def cum(chain, year, idx):
    return sum(row[idx] for row in chain if row[0] <= year)


def metric(key, chain, year, factor=1.0):
    power = BASE_GW[key] * factor * (1 + cum(chain, year, 1))
    effort = BASE_COST[key] / (1 + cum(chain, year, 2))
    return power / effort


def main():
    ap = argparse.ArgumentParser(description="Plot renewable/nuclear/fossil power per build cost over time.")
    ap.add_argument("--out", default="renewable_power_per_cost.png")
    args = ap.parse_args()

    techs = parse_techs(INDUSTRY)
    chains = build_chains(techs)
    for key in ("ren", "nuc", "fos"):
        print(f"{key}: {len(chains[key])} techs  "
              f"(power +{cum(chains[key], 2100, 1):.2f}, build-speed +{cum(chains[key], 2100, 2):.2f} cumulative by end)")

    years = list(range(1990, 2086))

    # crossovers: first year renewable(factor) beats nuclear and fossil on metric
    def first_above(factor, ref):
        for y in years:
            if metric("ren", chains["ren"], y, factor) > metric(ref, chains[ref], y):
                return y
        return None

    print(f"\n{'state':>6} | {'beats NUCLEAR':>13} | {'beats FOSSIL':>12}")
    print("-" * 40)
    for f in FACTORS:
        yn, yf = first_above(f, "nuc"), first_above(f, "fos")
        print(f"{f:>6.1f} | {str(yn) if yn else 'never':>13} | {str(yf) if yf else 'never':>12}")

    # --- plot (straight lines between each tech-tier coordinate) ------------
    fig, ax = plt.subplots(figsize=(17, 9))
    ren_colors = {0.5: "#9ecae1", 1.0: "#4292c6", 1.5: "#2171b5", 2.0: "#08306b"}
    tier = {k: [row[0] for row in chains[k]] for k in ("ren", "nuc", "fos")}

    for f in FACTORS:
        ax.plot(tier["ren"], [metric("ren", chains["ren"], y, f) for y in tier["ren"]],
                marker="o", ms=5, color=ren_colors[f], lw=2.0, label=f"Renewable  x{f:.1f} state factor")
    ax.plot(tier["nuc"], [metric("nuc", chains["nuc"], y) for y in tier["nuc"]],
            marker="s", ms=5, color="#e6550d", lw=2.4, ls="--", label="Nuclear (4 GW, cost 50000)")
    ax.plot(tier["fos"], [metric("fos", chains["fos"], y) for y in tier["fos"]],
            marker="^", ms=5, color="#636363", lw=2.4, ls="--", label="Fossil (2 GW, cost 9500)")

    # annotate each tech tier with its incremental "+power% / +construction%"
    def annotate(chain, key, factor, color, dy):
        for yr, p, s, name in chain:
            val = metric(key, chain, yr, factor)
            ax.annotate(f"+{p*100:g}% / +{s*100:g}%", xy=(yr, val),
                        xytext=(0, dy), textcoords="offset points",
                        fontsize=10, color=color, ha="center",
                        va="bottom" if dy > 0 else "top", rotation=90)

    annotate(chains["ren"], "ren", 2.0, "#08306b", 9)   # on the top (x2.0) renewable line
    annotate(chains["nuc"], "nuc", 1.0, "#a63603", -9)
    annotate(chains["fos"], "fos", 1.0, "#252525", 9)

    ax.set_xlabel("Year (all technologies that are not ahead-of-time at that year)")
    ax.set_ylabel("Power per build cost   (GW per unit construction effort)")
    ax.set_title("MD energy: power per build cost over time (both power and construction-speed techs)\n"
                 "renewable (4 state factors) vs nuclear vs fossil  -  labels: +power% / +construction-speed% per tech")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left", framealpha=0.95)
    ax.set_xlim(1988, 2086)
    ax.set_ylim(0, None)
    ax.text(0.99, 0.02,
            "power = base GW x state factor x (1 + sum power-output techs)\n"
            "effort = base_cost / (1 + sum construction-speed techs)   [civ-factory build effort, not $]\n"
            "Renewable lines are deterministic; in-game monthly output averages ~half (random 0..1). Excludes fuel.",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=8, color="#555",
            bbox=dict(boxstyle="round", fc="#f7f7f7", ec="#ccc"))
    fig.tight_layout()
    fig.savefig(args.out, dpi=110)
    print(f"\nsaved: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
