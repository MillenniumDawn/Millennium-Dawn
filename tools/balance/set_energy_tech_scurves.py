#!/usr/bin/env python3
"""Reshape the energy technology buffs in ``common/technologies/industry.txt`` into
calibrated logistic S-curves, so the most cost-effective power source over time is:

    fossil  <2015<  nuclear (fission)  <2020<  renewable  <2060<  nuclear (fusion) forever

WHY / DESIGN
------------
"Cost-effectiveness" is power per build cost:

    metric = base_GW * state_factor(renewable only) * (1 + cumulative power techs)
                                                     / (base_cost / (1 + cumulative construction-speed techs))

with the building stats from ``common/buildings/00_buildings.txt`` (renewable 0.5 GW /
50000 cost, nuclear 4 GW / 50000, fossil 2 GW / 9500) evaluated at state factor 1.0.
See ``tools/analysis/renewable_power_per_cost.py`` for the chart and the full model,
and ``.claude/docs/energy-power-balance.md`` for the design write-up.

Each source's cumulative tech buff (both the power-output modifier and the
construction-speed modifier) is a logistic S-curve in calendar year:

  * Fossil   - ONE S-curve starting LOW (~0.25 @1990) and steepened so the 1990s-2010s techs
               each give a worthwhile bonus, reaching the same efficiency as before by 2020;
               small total gain, less game-start advantage.
  * Renewable- ONE S-curve starting at the bottom, shifted early enough to cross fossil by
               2020 (steep rise across the 2010s-2020s techs, plateaus by ~2040).
  * Nuclear  - TWO stacked S-curves: fission (rises ~1990-2015) then fusion (rises
               ~2050-2065), so nuclear leads twice.

Per-source amplitudes are SOLVED (scipy.brentq) to put the three crossovers exactly on
2015 / 2020 / 2060; speed amplitude = ``SPEED_RATIO`` * power amplitude per source.

CONSIDERATIONS (things this model deliberately does / omits)
-----------------------------------------------------------
  * Build cost is ``base_cost`` (civ-factory construction effort), NOT the in-game "$"
    (that is foreign investment / income, a separate system).
  * The renewable monthly random(0..1) is NOT in the metric - in game a renewable plant
    averages ~half its rated output, which shifts the renewable crossovers a little later.
  * Fuel upkeep is excluded (renewable 0, nuclear 40/wk, fossil 480/day) - it only makes
    renewables look better, so the crossovers here are conservative for renewables.
  * "Average metric across sources per year" is kept broadly stable and is much flatter
    late-game than the old exponential design (renewable peak ~6.3e-4 vs old ~1.87e-3).

POTENTIAL FUTURE WORK
---------------------
  * The renewable rise is spread across the 2010s-2020s techs (no single mega-tech), but its
    S-curve plateaus by ~2040, so renewables_11-13 (2060-2080) grant only token gains (floored to
    0.001). Re-tuning R_T/R_K trades breakthrough sharpness against the length of that dead tail.
  * Nuclear's fission/fusion split is purely numeric here; the reactor* techs / loc could be
    re-themed (reactor1-8 fission, reactor9-12 fusion) to match.
  * Re-tune by editing the SHAPE/RATIO/PF constants below and re-running --apply; the chart
    in tools/analysis confirms the crossovers.
  * Hydro/geothermal are separate systems and are not modelled here.

USAGE
-----
    python tools/balance/set_energy_tech_scurves.py            # dry run: report + verify
    python tools/balance/set_energy_tech_scurves.py --apply    # write industry.txt

Needs scipy.
"""
from __future__ import annotations

import argparse
import math
import os
import re

from scipy.optimize import brentq

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INDUSTRY = os.path.join(REPO, "common", "technologies", "industry.txt")

# --- building stats (common/buildings/00_buildings.txt) ---------------------
GW = {"ren": 0.5, "nuc": 4.0, "fos": 2.0}
COST = {"ren": 50000, "nuc": 50000, "fos": 9500}
BASE = {k: GW[k] / COST[k] for k in GW}

# --- S-curve shapes (tmid, steepness) and amplitude couplings ---------------
F_T, F_K = 2004, 0.077       # fossil: lower start (L~0.25 @1990), steeper early climb, same level by 2020
R_T, R_K = 2016, 0.17        # renewable: bottom start, shifted earlier (beats fossil by 2020)
FIS_T, FIS_K = 2002, 0.16    # nuclear fission
FUS_T, FUS_K = 2053, 0.24    # nuclear fusion (steep, plateaus ~2065)
SPEED_RATIO = {"fos": 0.5, "ren": 0.4, "nuc": 0.3}   # speed amplitude / power amplitude
PF = 0.30                    # fossil power amplitude (fixed; mature, small total gain)

# --- infrastructure-maintenance relief (issue #1508) ------------------------
# Each chain also lowers its OWN plant type's weekly upkeep via a per-source
# infra-cost modifier (nuclear/fossil/renewable_infra_cost_multiplier_modifier),
# consumed in update_infra_rate (common/scripted_effects/00_money_system.txt).
# The relief follows that source's POWER S-curve (so it tracks tech progress) and
# is scaled so the fully-teched chain reaches INFRA_CAP. Values are NEGATIVE.
INFRA_CAP = -0.40            # total per-source upkeep reduction at the end of each chain

# --- tech chains: year-ordered tech ids + the (power, speed, infra) modifier names ---
CHAINS = {
    "ren": {
        "power": "renewable_energy_gain_multiplier",
        "speed": "production_speed_renewable_energy_infra_factor",
        "infra": "renewable_infra_cost_multiplier_modifier",
        "years": [1990, 1995, 2000, 2005, 2010, 2015, 2020, 2030, 2040, 2050, 2060, 2070, 2080],
        "techs": ["early_renewables", "renewables", "improved_renewables", "advanced_renewables",
                  "modern_renewables", "improved_modern_renewables", "advanced_modern_renewables",
                  "early_renewables_9", "renewables_9", "renewables_10", "renewables_11",
                  "renewables_12", "renewables_13"],
    },
    "nuc": {
        "power": "nuclear_energy_generation_modifier",
        "speed": "production_speed_nuclear_reactor_factor",
        "infra": "nuclear_infra_cost_multiplier_modifier",
        "years": [1990, 2000, 2005, 2015, 2020, 2030, 2040, 2045, 2055, 2060, 2070, 2080],
        "techs": ["reactor1", "reactor2", "reactor3", "reactor4", "reactor5", "reactor6",
                  "reactor7", "reactor8", "reactor9", "reactor10", "reactor11", "reactor12"],
    },
    "fos": {
        "power": "fossil_pp_energy_generation_modifier",
        "speed": "production_speed_fossil_powerplant_factor",   # NEW: fossil techs gain this
        "infra": "fossil_infra_cost_multiplier_modifier",
        "years": [1990, 2000, 2010, 2020, 2030, 2040, 2050, 2060, 2070, 2080],
        "techs": ["fuel_efficiency", "fuel_efficiency2", "fuel_efficiency3", "fuel_efficiency4",
                  "fuel_efficiency5", "fuel_efficiency6", "fuel_efficiency_7", "fuel_efficiency_8",
                  "fuel_efficiency_9", "fuel_efficiency_10"],
    },
}


def lg(t, tmid, k):
    return 1 / (1 + math.exp(-k * (t - tmid)))


Lf = lambda t: lg(t, F_T, F_K)
Lr = lambda t: lg(t, R_T, R_K)
Lfis = lambda t: lg(t, FIS_T, FIS_K)
Lfus = lambda t: lg(t, FUS_T, FUS_K)

# cumulative power buff as a function of year, given solved amplitudes
def cum_power(key, t, pf, pr, pfis, pfus):
    if key == "fos":
        return pf * Lf(t)
    if key == "ren":
        return pr * Lr(t)
    return pfis * Lfis(t) + pfus * Lfus(t)

def cum_speed(key, t, *a):
    return SPEED_RATIO[key] * cum_power(key, t, *a)

# cumulative infra-cost relief: that source's power S-curve normalised to its 2080
# asymptote and scaled to INFRA_CAP, so the fully-teched chain reaches INFRA_CAP.
def cum_infra(key, t, *a):
    full = cum_power(key, 2080, *a)
    if full <= 0:
        return 0.0
    return INFRA_CAP * cum_power(key, t, *a) / full

def metric(key, t, *a):
    return BASE[key] * (1 + cum_power(key, t, *a)) * (1 + cum_speed(key, t, *a))


def solve_amplitudes():
    pf = PF
    pfis = brentq(lambda p: metric("nuc", 2014, pf, 0, p, 0) - metric("fos", 2014, pf, 0, 0, 0), 0.01, 80)   # nuclear outperforms fossil by 2015
    pr = brentq(lambda p: metric("ren", 2019, pf, p, pfis, 0) - metric("fos", 2019, pf, 0, 0, 0), 0.01, 200)  # renewable beats fossil by 2020
    pfus = brentq(lambda p: metric("nuc", 2060, pf, pr, pfis, p) - metric("ren", 2060, pf, pr, 0, 0), 0.01, 200)  # nuclear (fusion) retakes by 2060, stays above renewable at 2080
    return pf, pr, pfis, pfus


def increments(amps):
    """tech_id -> (key, power_inc, speed_inc, infra_inc), rounded to 3 dp.

    power/speed increments are floored at +0.001 (no dead tech). infra increments
    are NEGATIVE upkeep relief and are floored toward 0 at -0.001 instead, so a
    plateaued tail tech still grants a token reduction rather than nothing."""
    out = {}
    for key, c in CHAINS.items():
        pp = sp = ip = 0.0
        for yr, tech in zip(c["years"], c["techs"]):
            cp, cs, ci = cum_power(key, yr, *amps), cum_speed(key, yr, *amps), cum_infra(key, yr, *amps)
            out[tech] = (key, max(round(cp - pp, 3), 0.001), max(round(cs - sp, 3), 0.001),
                         min(round(ci - ip, 3), -0.001))
            pp, sp, ip = cp, cs, ci
    return out


# --- industry.txt editing ---------------------------------------------------
HEAD = re.compile(r"^\t([A-Za-z_]\w*)\s*=\s*\{\s*$")


def apply_to_industry(amps, edits, apply):
    lines = open(INDUSTRY, encoding="utf-8").read().split("\n")
    report, i, n = [], 0, len(lines)
    seen = set()
    while i < n:
        m = HEAD.match(lines[i])
        if not (m and m.group(1) in edits):
            i += 1
            continue
        tech = m.group(1)
        seen.add(tech)
        key, pval, sval, ival = edits[tech]
        pmod, smod, imod = CHAINS[key]["power"], CHAINS[key]["speed"], CHAINS[key]["infra"]
        depth = lines[i].count("{") - lines[i].count("}")
        j = i + 1
        while j < n and depth > 0:
            depth += lines[j].count("{") - lines[j].count("}")
            j += 1
        block = lines[i:j]
        pidx = None
        for k, bl in enumerate(block):
            if re.match(rf"^\t+{re.escape(pmod)}\s*=", bl):
                ind = re.match(r"^(\t+)", bl).group(1)
                block[k] = f"{ind}{pmod} = {pval}"
                pidx = k
                break
        sidx = None
        for k, bl in enumerate(block):
            if re.match(rf"^\t+{re.escape(smod)}\s*=", bl):
                ind = re.match(r"^(\t+)", bl).group(1)
                block[k] = f"{ind}{smod} = {sval}"
                sidx = k
                break
        if sidx is None and pidx is not None:
            ind = re.match(r"^(\t+)", block[pidx]).group(1)
            block.insert(pidx + 1, f"{ind}{smod} = {sval}")
        iidx = None
        for k, bl in enumerate(block):
            if re.match(rf"^\t+{re.escape(imod)}\s*=", bl):
                ind = re.match(r"^(\t+)", bl).group(1)
                block[k] = f"{ind}{imod} = {ival}"
                iidx = k
                break
        if iidx is None:
            anchor = next((k for k, bl in enumerate(block)
                           if re.match(rf"^\t+{re.escape(smod)}\s*=", bl)), pidx)
            if anchor is not None:
                ind = re.match(r"^(\t+)", block[anchor]).group(1)
                block.insert(anchor + 1, f"{ind}{imod} = {ival}")
        report.append((tech, key, pval, sval, ival, "speed+" if sidx is None else "speed=",
                       "infra+" if iidx is None else "infra="))
        lines[i:j] = block
        n = len(lines)
        i += len(block)
    missing = set(edits) - seen
    if apply and not missing:
        out = "\n".join(lines)
        with open(INDUSTRY, "w", encoding="utf-8", newline="\n") as f:
            f.write(out)
    return report, missing


def main():
    ap = argparse.ArgumentParser(description="Reshape energy tech buffs into S-curves.")
    ap.add_argument("--apply", action="store_true", help="write industry.txt (default: dry run)")
    args = ap.parse_args()

    amps = solve_amplitudes()
    pf, pr, pfis, pfus = amps
    print(f"amplitudes: fossil P={pf:.3f} | renewable P={pr:.3f} | nuclear fission P={pfis:.3f} fusion P={pfus:.3f}")

    prev = None
    print("\nbest source by year (verify crossovers 2020/2030/2060):")
    for y in range(1990, 2086):
        ms = {"fossil": metric("fos", y, *amps), "nuclear": metric("nuc", y, *amps), "renewable": metric("ren", y, *amps)}
        best = max(ms, key=ms.get)
        if best != prev:
            print(f"  {y}: {best}")
            prev = best
    avg = [sum(metric(k, y, *amps) for k in ("fos", "nuc", "ren")) / 3 for y in (1990, 2030, 2060, 2080)]
    print(f"avg metric 1990/2030/2060/2080: " + " ".join(f"{a:.2e}" for a in avg))

    edits = increments(amps)
    print(f"\nper-tech increments, power/speed/infra ({len(edits)} techs):")
    for key in ("ren", "nuc", "fos"):
        print(f"  {key}: " + ", ".join(f"{t}={p}/{s}/{iv}" for t, (kk, p, s, iv) in edits.items() if kk == key))
        full = sum(iv for kk, p, s, iv in edits.values() if kk == key)
        print(f"       total infra relief @2080: {full:+.3f}")

    report, missing = apply_to_industry(amps, edits, args.apply)
    if missing:
        print(f"\nERROR: techs not found in industry.txt (aborted write): {sorted(missing)}")
        return 1
    print(f"\n{'APPLIED' if args.apply else 'DRY RUN'}: {len(report)} techs edited "
          f"({sum(1 for r in report if r[5] == 'speed+')} gained a new speed line, "
          f"{sum(1 for r in report if r[6] == 'infra+')} gained a new infra line)")
    if not args.apply:
        print("re-run with --apply to write")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
