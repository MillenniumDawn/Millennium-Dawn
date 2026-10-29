#!/usr/bin/env python3
"""Reshape the energy technology buffs in ``common/technologies/industry.txt`` into
calibrated logistic S-curves, so the most cost-effective power source over time is:

    fossil  <2015<  renewable  <2060<  nuclear (fusion) forever

Fission nuclear ties fossil and renewable at 2014 but never leads once techs land at state
factor 1.0. It stays within 1.5x of renewables through 2055 and beats them in weak states.

WHY / DESIGN
------------
"Cost-effectiveness" is power per build cost:

    metric = base_GW * state_factor(renewable only) * (1 + cumulative power techs)
                                                     / (base_cost / (1 + cumulative construction-speed techs))

with the building stats from ``common/buildings/00_buildings.txt`` (renewable 0.5 GW /
50000 cost, nuclear 4 GW / 50000, fossil 2 GW / 9500) evaluated at state factor 1.0.
See ``tools/analysis/renewable_power_per_cost.py`` for the chart and the full model,
and ``.claude/docs/energy-power-balance.md`` for the design write-up.

Each tech grants at least ``MIN_GAIN`` on power, construction speed, and upkeep relief.
On top of that, each source's cumulative tech buff follows a logistic S-curve in calendar
year. Every curve is 0 one tech step before its chain's first tech, so the first tech is a
normal step, not a lump:

  * Fossil   - ONE S-curve past its midpoint: a mature tech whose gains shrink from ~+7% to
               the minimum, keeping the old game-start bonus; small total gain.
  * Renewable- ONE wide S-curve: good states (x1.5) beat fossil by 2010, average states by
               2015, and the 2060-2080 techs still grant real gains.
  * Nuclear  - TWO stacked S-curves: a wide fission curve that keeps growing through the
               Gen IV techs, then a fusion boost (~2050-2065) that takes the lead at 2060.

Per-source amplitudes are SOLVED (scipy.brentq) one year before each target: nuclear and
renewable cross fossil by 2015, and fusion crosses renewable by 2060. Speed amplitude =
``SPEED_RATIO`` * power amplitude per source. Upkeep relief past the minimum follows the
power curve, so the fully-teched chain reaches ``INFRA_CAP``.

CONSIDERATIONS (things this model deliberately does / omits)
-----------------------------------------------------------
  * Build cost is ``base_cost`` (civ-factory construction effort), NOT the in-game "$"
    (that is foreign investment / income, a separate system).
  * The renewable monthly random(0..1) is NOT in the metric - in game a renewable plant
    averages ~half its rated output, which shifts the renewable crossovers a little later.
  * Fuel upkeep is excluded (renewable 0, nuclear 40/wk, fossil 480/day) - it only makes
    renewables look better, so the crossovers here are conservative for renewables.
  * A longer renewable tail costs a higher late game: the 2060 average metric across
    sources is ~8.6e-4, still flatter than the old exponential design (~1.87e-3 renewable peak).

POTENTIAL FUTURE WORK
---------------------
  * Re-tune by editing the SHAPE/RATIO/PF/MIN_GAIN constants below and re-running
    --apply; the chart in tools/analysis confirms the crossovers.
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
F_T, F_K = 1954, 0.075  # fossil: past midpoint, each tech gives less than the last
R_T, R_K = 2015, 0.08  # renewable: wide rise, viable by 2010 (x1.5) and 2015 (x1.0)
FIS_T, FIS_K = 2028, 0.04  # nuclear fission: wide, keeps renewables within 1.5x to 2055
FUS_T, FUS_K = 2053, 0.24  # nuclear fusion (steep, plateaus ~2065)
SPEED_RATIO = {"fos": 0.5, "ren": 0.4, "nuc": 0.3}  # speed amplitude / power amplitude
PF = 0.65  # fossil power amplitude (fixed; only ~0.08 of it is reached by 2080)

MIN_GAIN = 0.03  # every tech adds at least this to power, speed, and upkeep relief

# --- infrastructure-maintenance relief (issue #1508) ------------------------
# Each chain also lowers its OWN plant type's weekly upkeep via a per-source
# infra-cost modifier (nuclear/fossil/renewable_infra_cost_multiplier_modifier),
# consumed in update_infra_rate (common/scripted_effects/00_money_system.txt).
# Each tech gives MIN_GAIN, and the rest follows that source's power S-curve, so
# the fully-teched chain reaches INFRA_CAP. Values are NEGATIVE.
INFRA_CAP = -0.40  # total per-source upkeep reduction at the end of each chain

# --- tech chains: year-ordered tech ids + the (power, speed, infra) modifier names ---
CHAINS = {
    "ren": {
        "power": "renewable_energy_gain_multiplier",
        "speed": "production_speed_renewable_energy_infra_factor",
        "infra": "renewable_infra_cost_multiplier_modifier",
        "years": [
            1990,
            1995,
            2000,
            2005,
            2010,
            2015,
            2020,
            2030,
            2040,
            2050,
            2060,
            2070,
            2080,
        ],
        "techs": [
            "early_renewables",
            "renewables",
            "improved_renewables",
            "advanced_renewables",
            "modern_renewables",
            "improved_modern_renewables",
            "advanced_modern_renewables",
            "early_renewables_9",
            "renewables_9",
            "renewables_10",
            "renewables_11",
            "renewables_12",
            "renewables_13",
        ],
    },
    "nuc": {
        "power": "nuclear_energy_generation_modifier",
        "speed": "production_speed_nuclear_reactor_factor",
        "infra": "nuclear_infra_cost_multiplier_modifier",
        "years": [
            1990,
            2000,
            2005,
            2015,
            2020,
            2030,
            2040,
            2045,
            2055,
            2060,
            2070,
            2080,
        ],
        "techs": [
            "reactor1",
            "reactor2",
            "reactor3",
            "reactor4",
            "reactor5",
            "reactor6",
            "reactor7",
            "reactor8",
            "reactor9",
            "reactor10",
            "reactor11",
            "reactor12",
        ],
    },
    "fos": {
        "power": "fossil_pp_energy_generation_modifier",
        "speed": "production_speed_fossil_powerplant_factor",  # NEW: fossil techs gain this
        "infra": "fossil_infra_cost_multiplier_modifier",
        "years": [1990, 2000, 2010, 2020, 2030, 2040, 2050, 2060, 2070, 2080],
        "techs": [
            "fuel_efficiency",
            "fuel_efficiency2",
            "fuel_efficiency3",
            "fuel_efficiency4",
            "fuel_efficiency5",
            "fuel_efficiency6",
            "fuel_efficiency_7",
            "fuel_efficiency_8",
            "fuel_efficiency_9",
            "fuel_efficiency_10",
        ],
    },
}


def lg(t, tmid, k):
    return 1 / (1 + math.exp(-k * (t - tmid)))


# each curve is 0 one tech step before its chain's first tech (no pre-1990 lump)
START = {k: c["years"][0] - (c["years"][1] - c["years"][0]) for k, c in CHAINS.items()}


def rise(t, tmid, k, key):
    return lg(t, tmid, k) - lg(START[key], tmid, k)


def Lf(t):
    return rise(t, F_T, F_K, "fos")


def Lr(t):
    return rise(t, R_T, R_K, "ren")


def Lfis(t):
    return rise(t, FIS_T, FIS_K, "nuc")


def Lfus(t):
    return rise(t, FUS_T, FUS_K, "nuc")


def researched(key, t):
    return sum(1 for y in CHAINS[key]["years"] if y <= t)


# S-curve part of the power buff as a function of year, given solved amplitudes
def curve(key, t, pf, pr, pfis, pfus):
    if key == "fos":
        return pf * Lf(t)
    if key == "ren":
        return pr * Lr(t)
    return pfis * Lfis(t) + pfus * Lfus(t)


def cum_power(key, t, *a):
    return curve(key, t, *a) + MIN_GAIN * researched(key, t)


def cum_speed(key, t, *a):
    return SPEED_RATIO[key] * curve(key, t, *a) + MIN_GAIN * researched(key, t)


def cum_infra(key, t, *a):
    rest = -INFRA_CAP - MIN_GAIN * len(CHAINS[key]["techs"])
    share = curve(key, t, *a) / curve(key, 2080, *a)
    return -(MIN_GAIN * researched(key, t) + rest * share)


def metric(key, t, *a):
    return BASE[key] * (1 + cum_power(key, t, *a)) * (1 + cum_speed(key, t, *a))


def solve_amplitudes():
    pf = PF
    pfis = brentq(
        lambda p: metric("nuc", 2014, pf, 0, p, 0) - metric("fos", 2014, pf, 0, 0, 0),
        0.01,
        80,
    )  # nuclear outperforms fossil by 2015
    pr = brentq(
        lambda p: (
            metric("ren", 2014, pf, p, pfis, 0) - metric("fos", 2014, pf, 0, 0, 0)
        ),
        0.01,
        200,
    )  # renewable beats fossil by 2015
    pfus = brentq(
        lambda p: (
            metric("nuc", 2059, pf, pr, pfis, p) - metric("ren", 2059, pf, pr, 0, 0)
        ),
        0.01,
        200,
    )  # nuclear (fusion) retakes by 2060, stays above renewable at 2080
    return pf, pr, pfis, pfus


def increments(amps):
    """tech_id -> (key, power_inc, speed_inc, infra_inc), rounded to 3 dp."""
    out = {}
    for key, c in CHAINS.items():
        pp = sp = ip = 0.0
        for yr, tech in zip(c["years"], c["techs"]):
            cp, cs, ci = (
                cum_power(key, yr, *amps),
                cum_speed(key, yr, *amps),
                cum_infra(key, yr, *amps),
            )
            out[tech] = (
                key,
                round(cp - pp, 3),
                round(cs - sp, 3),
                round(ci - ip, 3),
            )
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
        pmod, smod, imod = (
            CHAINS[key]["power"],
            CHAINS[key]["speed"],
            CHAINS[key]["infra"],
        )
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
            anchor = next(
                (
                    k
                    for k, bl in enumerate(block)
                    if re.match(rf"^\t+{re.escape(smod)}\s*=", bl)
                ),
                pidx,
            )
            if anchor is not None:
                ind = re.match(r"^(\t+)", block[anchor]).group(1)
                block.insert(anchor + 1, f"{ind}{imod} = {ival}")
        report.append(
            (
                tech,
                key,
                pval,
                sval,
                ival,
                "speed+" if sidx is None else "speed=",
                "infra+" if iidx is None else "infra=",
            )
        )
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
    ap.add_argument(
        "--apply", action="store_true", help="write industry.txt (default: dry run)"
    )
    args = ap.parse_args()

    amps = solve_amplitudes()
    pf, pr, pfis, pfus = amps
    print(
        f"amplitudes: fossil P={pf:.3f} | renewable P={pr:.3f} | nuclear fission P={pfis:.3f} fusion P={pfus:.3f}"
    )

    prev = None
    print("\nbest source by year (verify crossovers 2015/2060):")
    for y in range(1990, 2086):
        ms = {
            "fossil": metric("fos", y, *amps),
            "nuclear": metric("nuc", y, *amps),
            "renewable": metric("ren", y, *amps),
        }
        best = max(ms, key=ms.get)
        if best != prev:
            print(f"  {y}: {best}")
            prev = best
    avg = [
        sum(metric(k, y, *amps) for k in ("fos", "nuc", "ren")) / 3
        for y in (1990, 2030, 2060, 2080)
    ]
    print("avg metric 1990/2030/2060/2080: " + " ".join(f"{a:.2e}" for a in avg))

    edits = increments(amps)
    print(f"\nper-tech increments, power/speed/infra ({len(edits)} techs):")
    for key in ("ren", "nuc", "fos"):
        print(
            f"  {key}: "
            + ", ".join(
                f"{t}={p}/{s}/{iv}" for t, (kk, p, s, iv) in edits.items() if kk == key
            )
        )
        full = sum(iv for kk, p, s, iv in edits.values() if kk == key)
        print(f"       total infra relief @2080: {full:+.3f}")

    report, missing = apply_to_industry(amps, edits, args.apply)
    if missing:
        print(
            f"\nERROR: techs not found in industry.txt (aborted write): {sorted(missing)}"
        )
        return 1
    print(
        f"\n{'APPLIED' if args.apply else 'DRY RUN'}: {len(report)} techs edited "
        f"({sum(1 for r in report if r[5] == 'speed+')} gained a new speed line, "
        f"{sum(1 for r in report if r[6] == 'infra+')} gained a new infra line)"
    )
    if not args.apply:
        print("re-run with --apply to write")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
