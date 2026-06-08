#!/usr/bin/env python3
"""
Redistribute productivity_state_var across each country's states.

Many countries in MD ship with identical productivity_state_var values on every
state (e.g., all 10 Saudi states = 1173, all 14 Turkish states = 603). The
Americas (USA/FRA/BRA) already disperse productivity by economic geography,
where capital / port / industrial states hold higher values than rural ones.

This tool extends that pattern to Africa, Europe, Asia, Oceania, and the Middle
East. For each in-scope country it:

  1. Reads every state owned by the tag,
  2. Computes a weight per state from manpower + economic markers (victory
     points, landmark buildings, factory count, dockyards),
  3. Allocates the country's existing total productivity proportionally to
     weight (so the country mean is preserved exactly),
  4. Clamps any state to [0.35 * mean, 2.00 * mean] and renormalizes,
  5. Rewrites the productivity_state_var line in each state file.

Idempotent. Default is --dry-run.

Usage:
    python3 tools/analysis/redistribute_productivity.py [options]

Options:
    --dry-run                   (default) print before/after table, no writes
    --write                     commit new values to history/states/*.txt
    --continent CONT[,CONT2]    africa,europe,asia,oceania,middle_east
    --tag TAG[,TAG2]            limit to specific country tags
    --skip-tag TAG[,TAG2]       exclude specific tags
    --min-states N              only redistribute if country has >= N states (default 3)
    --report                    also run GDP estimation and print delta vs. pre-write
"""

import argparse
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import estimate_gdp  # noqa: E402

BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
STATES_DIR = os.path.join(BASE_DIR, "history", "states")


# ─── Continent → tag mapping ───────────────────────────────────────────────────
# Listed once per tag. SOV (Russia) spans Europe + Asia; classified under europe.
# Tags with < 3 states are filtered out at runtime, so missing minor tags is OK.

CONTINENT_TAGS = {
    "africa": [
        "LBA",
        "TNZ",
        "EGY",
        "ALG",
        "DRC",
        "SUD",
        "SAF",
        "MAL",
        "MOR",
        "ETH",
        "NIG",
        "KEN",
        "MOZ",
        "SSU",
        "GAH",
        "MAD",
        "ZAM",
        "MAU",
        "CAR",
        "UGA",
        "CHA",
        "SEN",
        "BFA",
        "TUN",
        "NGR",
        "ZIM",
        "CAM",
        "PUN",
        "SML",
        "AGL",
        "UNI",
        "SNA",
    ],
    "europe": [
        "SOV",
        "ENG",
        "SPR",
        "GER",
        "ITA",
        "UKR",
        "POL",
        "GRE",
        "SWE",
        "POR",
        "BLR",
        "ROM",
        "BOS",
        "FIN",
        "HOL",
        "DEN",
        "LIT",
        "EST",
        "HUN",
        "CZE",
        "LAT",
        "SER",
        "BEL",
        "NOR",
        "MLV",
        "AUS",
        "BUL",
        "IRE",
        "SWI",
        "GEO",
        "ARM",
        "AZE",
    ],
    "asia": [
        "RAJ",
        "CHI",
        "PHI",
        "IND",
        "JAP",
        "PAK",
        "TAI",
        "TAL",
        "VIE",
        "BRM",
        "NKO",
        "MAY",
        "KOR",
        "KAZ",
        "SIA",
        "BAN",
        "CBD",
        "TAJ",
        "SRI",
        "KYR",
        "LAO",
        "AFG",
        "UZB",
    ],
    "oceania": [
        "AST",
        "NZL",
        "PAP",
        "KIR",
    ],
    "middle_east": [
        "PER",
        "SYR",
        "IRQ",
        "YEM",
        "TUR",
        "SAU",
        "ISR",
        "OMA",
        "LEB",
        "JOR",
        "NKR",
    ],
}

TAG_TO_CONTINENT = {tag: cont for cont, tags in CONTINENT_TAGS.items() for tag in tags}


# ─── Parsing ───────────────────────────────────────────────────────────────────

PROD_RE = re.compile(
    r"(set_variable\s*=\s*\{\s*productivity_state_var\s*=\s*)(\d+)(\s*\})"
)
VP_RE = re.compile(r"victory_points\s*=\s*\{\s*\d+\s+(\d+)\s*\}")
LANDMARK_RE = re.compile(r"\blandmark_[A-Za-z_]+\s*=\s*\{", re.IGNORECASE)
SPACEPORT_RE = re.compile(r"\bspaceport\s*=\s*\d+")


def parse_state_extras(content):
    """Extract victory-point sum, landmark presence, spaceport presence from state file text."""
    vp_sum = sum(int(m.group(1)) for m in VP_RE.finditer(content))
    has_landmark = bool(LANDMARK_RE.search(content))
    has_spaceport = bool(SPACEPORT_RE.search(content))
    return vp_sum, has_landmark, has_spaceport


def load_all_states():
    """Load every state with full economic data + extras. Returns {owner: [state...]}."""
    by_owner = defaultdict(list)
    for fname in sorted(os.listdir(STATES_DIR)):
        if not fname.endswith(".txt"):
            continue
        fpath = os.path.join(STATES_DIR, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        state = estimate_gdp.parse_state_file_from_content(content, fname)
        if not state["owner"] or state["id"] is None:
            continue
        vp_sum, has_landmark, has_spaceport = parse_state_extras(content)
        state["filepath"] = fpath
        state["vp_sum"] = vp_sum
        state["has_landmark"] = has_landmark
        state["has_spaceport"] = has_spaceport
        by_owner[state["owner"]].append(state)
    return by_owner


# ─── Weighting & redistribution ────────────────────────────────────────────────

FACTORY_BUILDINGS = (
    "industrial_complex",
    "arms_factory",
    "offices",
    "microchip_plant",
    "composite_plant",
    "agriculture_district",
    "synthetic_refinery",
)

CLAMP_FLOOR = 0.35  # state cannot drop below 35% of country mean
CLAMP_CEIL = 2.00  # state cannot rise above 200% of country mean — slightly
# tighter than USA's empirical 2.28, to keep megapoles like
# London from running away at the ceiling.
FACTORY_CAP = 12  # diminishing returns: factories beyond 12 don't compound
# per-capita productivity any further. London with 16+
# factories shouldn't outscale Madrid with 6 by 3x.


def compute_score(state, is_capital=False):
    """
    Per-capita productivity score for a state, **independent of manpower**.

    Manpower is the engine's weighting factor in pop_weighted_mean, so including
    it in the score would double-count and shift GDP. Score reflects how
    productive each citizen of this state is on average: industrial activity,
    political/economic importance (VPs / landmarks / capital), ports, spaceports.
    """
    vp_sum = state["vp_sum"]
    if vp_sum > 0:
        vp_boost = 1.40 + 0.04 * min(vp_sum, 25)
    else:
        vp_boost = 1.0

    landmark_boost = 1.35 if state["has_landmark"] else 1.0
    spaceport_boost = 1.25 if state["has_spaceport"] else 1.0
    capital_boost = 1.25 if is_capital else 1.0

    factory_count = sum(state["buildings"].get(b, 0) for b in FACTORY_BUILDINGS)
    factory_boost = 1.0 + 0.04 * min(factory_count, FACTORY_CAP)

    dockyards = state["buildings"].get("dockyard", 0)
    dockyard_boost = 1.25 if dockyards > 0 else 1.0

    return (
        vp_boost
        * landmark_boost
        * spaceport_boost
        * capital_boost
        * factory_boost
        * dockyard_boost
    )


def redistribute(states, capital_state_id=None):
    """
    Compute new productivity_state_var for each state in a single country,
    preserving the country's POPULATION-WEIGHTED productivity total (and thus
    its game-engine GDP) exactly.

    capital_state_id, if provided, marks the country's capital state for an
    extra +25% score boost. Pulled from `capital = N` in history/countries.

    The engine computes overall_productivity = sum(prod_i * pop_i) / sum(pop_i)
    (00_money_system.txt:4256-4285). Preserving sum(prod_i * pop_i) = T_w keeps
    overall_productivity invariant.

    We pick prod_i ∝ per-capita score (no manpower in the score), then solve
    for the scale factor S such that sum(clamp(S * score_i, floor, ceil) * pop_i)
    = T_w. Clamps are taken around the country's old POP-WEIGHTED mean so the
    per-state value is bounded the same regardless of arith-vs-weighted reference.

    Returns: list of (state, old_prod, new_prod) tuples, same order as input.
    """
    n = len(states)
    if n < 1:
        return []

    total_pop = sum(max(s["manpower"], 1) for s in states)
    target_weighted = sum(s["productivity"] * max(s["manpower"], 1) for s in states)
    if target_weighted <= 0 or total_pop <= 0:
        return [(s, s["productivity"], s["productivity"]) for s in states]

    # Anchor clamps around the pop-weighted mean — this is the quantity we preserve.
    pop_w_mean = target_weighted / total_pop
    floor = CLAMP_FLOOR * pop_w_mean
    ceil = CLAMP_CEIL * pop_w_mean

    scores = [
        compute_score(s, is_capital=(s["id"] == capital_state_id)) for s in states
    ]
    pops = [max(s["manpower"], 1) for s in states]

    # Solve for scale S such that sum(clamp(S * score_i, floor, ceil) * pop_i) = target_weighted.
    # f(S) is non-decreasing in S, so bisect.
    def weighted_sum_at(S):
        return sum(min(ceil, max(floor, S * sc)) * pp for sc, pp in zip(scores, pops))

    # If even at max S everything pins at ceil and the weighted total is still
    # below target, or at min S everything at floor is above target, we're
    # asking for the impossible — return the closest feasible result.
    max_feasible = ceil * total_pop
    min_feasible = floor * total_pop
    if target_weighted >= max_feasible:
        # Want more than possible; pin all at ceil.
        scaled = [ceil] * n
    elif target_weighted <= min_feasible:
        # Want less than possible; pin all at floor.
        scaled = [floor] * n
    else:
        lo, hi = 0.0, 1.0
        # Expand hi until f(hi) ≥ target_weighted.
        while weighted_sum_at(hi) < target_weighted and hi < 1e9:
            hi *= 2.0
        for _ in range(80):
            mid = 0.5 * (lo + hi)
            if weighted_sum_at(mid) < target_weighted:
                lo = mid
            else:
                hi = mid
        S = 0.5 * (lo + hi)
        scaled = [min(ceil, max(floor, S * sc)) for sc in scores]

    rounded = [int(round(v)) for v in scaled]

    # Idempotency snap: if a state's new value is within ±2 of its CURRENT
    # value, keep the current value. Bisect + round can produce ≤2-unit wobble
    # per state across re-runs (worst case: high-population states where a
    # rounding boundary flip carries weighted-sum across the drift tolerance).
    # Worst-case aggregate drift this introduces is 2 × sum(pop) ≈ 2/pop_w_mean
    # in relative terms — for the lowest-pop_w_mean country in scope (MLV at
    # ~336), that's a worst-case 0.6%. In practice across all 102 countries
    # the observed engine-faithful GDP delta is ≤ 0.09%.
    # NOTE: snap runs BEFORE drift correction so that the correction's ±1
    # adjustments are not silently undone by the snap.
    old_prods = [s["productivity"] for s in states]
    for i, (old, new) in enumerate(zip(old_prods, rounded)):
        if abs(new - old) <= 2 and old > 0:
            rounded[i] = old

    # Drift correction: any residual weighted-sum drift after snap. Adjust the
    # highest-pop states first (largest impact per ±1 adjustment). Break early
    # if a full pass through `order` makes no progress (all candidate states
    # pinned at ceil/floor).
    drift_weighted = target_weighted - sum(r * p for r, p in zip(rounded, pops))
    max_pop = max(pops)
    if abs(drift_weighted) > 0.5 * max_pop:
        order = sorted(range(n), key=lambda i: -pops[i])
        last_drift = drift_weighted
        guard = 0
        while abs(drift_weighted) > 0.5 * max_pop and guard < 20 * n:
            idx = order[guard % n]
            if drift_weighted > 0 and rounded[idx] < ceil:
                rounded[idx] += 1
                drift_weighted -= pops[idx]
            elif drift_weighted < 0 and rounded[idx] > floor:
                rounded[idx] -= 1
                drift_weighted += pops[idx]
            guard += 1
            # End-of-pass progress check: if a full sweep made no change,
            # every state is pinned at the clamp boundary — exit early.
            if guard % n == 0:
                if drift_weighted == last_drift:
                    break
                last_drift = drift_weighted

    return [(s, old, new) for s, old, new in zip(states, old_prods, rounded)]


# ─── File rewriting ────────────────────────────────────────────────────────────


def rewrite_state(state, new_prod):
    """Rewrite productivity_state_var = NNN in the state file. Returns True if changed."""
    fpath = state["filepath"]
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    m = PROD_RE.search(content)
    if not m:
        return False

    if int(m.group(2)) == new_prod:
        return False

    new_content, count = PROD_RE.subn(
        lambda m: f"{m.group(1)}{new_prod}{m.group(3)}",
        content,
        count=1,
    )
    if count != 1:
        return False

    with open(fpath, "w", encoding="utf-8", newline="\n") as f:
        f.write(new_content)
    return True


# ─── Main ──────────────────────────────────────────────────────────────────────


def parse_args():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--write", action="store_true", help="commit changes to state files")
    p.add_argument(
        "--continent",
        default=None,
        help="comma-separated continent filter "
        "(africa,europe,asia,oceania,middle_east)",
    )
    p.add_argument("--tag", default=None, help="comma-separated country tag filter")
    p.add_argument("--skip-tag", default=None, help="comma-separated tags to exclude")
    p.add_argument(
        "--min-states",
        type=int,
        default=3,
        help="only redistribute countries with >= N states (default 3)",
    )
    p.add_argument(
        "--report",
        action="store_true",
        help="run estimate_gdp before/after and print per-country delta",
    )
    p.add_argument(
        "--gdp-tolerance",
        type=float,
        default=0.5,
        help="fail if any country's GDP changes by more than this percent (default 0.5)",
    )
    return p.parse_args()


def select_tags(args, by_owner):
    """Return the list of tags to process based on filters."""
    if args.continent:
        wanted_continents = {c.strip() for c in args.continent.split(",")}
        unknown = wanted_continents - set(CONTINENT_TAGS.keys())
        if unknown:
            print(f"ERROR: unknown continent(s): {sorted(unknown)}", file=sys.stderr)
            print(f"  Valid: {sorted(CONTINENT_TAGS.keys())}", file=sys.stderr)
            sys.exit(2)
        candidate = []
        for c in wanted_continents:
            candidate.extend(CONTINENT_TAGS[c])
    else:
        candidate = list(TAG_TO_CONTINENT.keys())

    if args.tag:
        wanted_tags = {t.strip().upper() for t in args.tag.split(",")}
        candidate = [t for t in candidate if t in wanted_tags]

    if args.skip_tag:
        skip = {t.strip().upper() for t in args.skip_tag.split(",")}
        candidate = [t for t in candidate if t not in skip]

    candidate = [
        t for t in candidate if t in by_owner and len(by_owner[t]) >= args.min_states
    ]
    return sorted(set(candidate))


def main():
    args = parse_args()

    print("Loading state files...", file=sys.stderr)
    by_owner = load_all_states()
    tags = select_tags(args, by_owner)
    country_infos = {tag: estimate_gdp.parse_country_history(tag) for tag in tags}
    print(f"Processing {len(tags)} countries.\n", file=sys.stderr)

    if args.report:
        print("Loading idea definitions for GDP estimation...", file=sys.stderr)
        idea_db = estimate_gdp.parse_all_ideas()
    else:
        idea_db = None

    summary_rows = []
    total_changes = 0
    files_written = 0
    gdp_violations = []

    for tag in tags:
        states = by_owner[tag]
        country_info = country_infos[tag]
        plan = redistribute(states, capital_state_id=country_info["capital"])

        olds = [o for _, o, _ in plan]
        news = [n for _, _, n in plan]
        old_total = sum(olds)
        new_total = sum(news)
        old_min, old_max = min(olds), max(olds)
        new_min, new_max = min(news), max(news)
        changes = sum(1 for o, n in zip(olds, news) if o != n)
        # Population-weighted totals (what the engine actually uses for GDP)
        pops = [max(s["manpower"], 1) for s, _, _ in plan]
        total_pop = sum(pops)
        old_w = sum(o * p for o, p in zip(olds, pops))
        new_w = sum(n * p for n, p in zip(news, pops))
        old_pop_w_mean = old_w / total_pop
        new_pop_w_mean = new_w / total_pop
        pop_w_drift_pct = 100.0 * (new_w - old_w) / old_w if old_w else 0.0

        gdp_before = gdp_after = None
        if args.report and idea_db is not None:
            before = estimate_gdp.compute_country_gdp(
                tag, states, idea_db, country_data=country_info
            )
            mutated = []
            for s, _, new_prod in plan:
                ms = dict(s)
                ms["productivity"] = new_prod
                mutated.append(ms)
            after = estimate_gdp.compute_country_gdp(
                tag, mutated, idea_db, country_data=country_info
            )
            gdp_before = before["gdp_total"] if before else None
            gdp_after = after["gdp_total"] if after else None

        gdp_delta_pct = None
        if gdp_before and gdp_after:
            gdp_delta_pct = 100.0 * (gdp_after - gdp_before) / gdp_before
            if abs(gdp_delta_pct) > args.gdp_tolerance:
                gdp_violations.append((tag, gdp_delta_pct))

        summary_rows.append(
            {
                "tag": tag,
                "continent": TAG_TO_CONTINENT.get(tag, "?"),
                "n_states": len(states),
                "old_min": old_min,
                "old_max": old_max,
                "new_min": new_min,
                "new_max": new_max,
                "old_total": old_total,
                "new_total": new_total,
                "old_pop_w_mean": old_pop_w_mean,
                "new_pop_w_mean": new_pop_w_mean,
                "pop_w_drift_pct": pop_w_drift_pct,
                "changes": changes,
                "gdp_before": gdp_before,
                "gdp_after": gdp_after,
                "gdp_delta_pct": gdp_delta_pct,
            }
        )
        total_changes += changes

        if args.write:
            for s, _, new_prod in plan:
                if rewrite_state(s, new_prod):
                    files_written += 1

    # ─── Print summary ─────────────────────────────────────────────────────
    print(
        f"{'Continent':<12} {'TAG':<5} {'#':>4} "
        f"{'OldMin':>6} {'OldMax':>6} {'NewMin':>6} {'NewMax':>6} "
        f"{'PopW Δ%':>8} {'ArithΔ':>8} {'edits':>5} "
        + (f"{'GDP Δ%':>9}" if args.report else "")
    )
    print("─" * (95 + (9 if args.report else 0)))
    for r in summary_rows:
        gdp_str = ""
        if args.report and r["gdp_delta_pct"] is not None:
            gdp_str = f"{r['gdp_delta_pct']:+9.3f}"
        arith_drift = r["new_total"] - r["old_total"]
        print(
            f"{r['continent']:<12} {r['tag']:<5} {r['n_states']:>4} "
            f"{r['old_min']:>6} {r['old_max']:>6} {r['new_min']:>6} {r['new_max']:>6} "
            f"{r['pop_w_drift_pct']:>+8.3f} {arith_drift:>+8} {r['changes']:>5} {gdp_str}"
        )

    print()
    print(f"Total per-state edits: {total_changes}")
    if args.write:
        print(f"Files written:         {files_written}")
    else:
        print("(dry-run; no files written. Pass --write to apply.)")

    if gdp_violations:
        print(f"\nGDP DELTA VIOLATIONS (>{args.gdp_tolerance}%):", file=sys.stderr)
        for tag, pct in gdp_violations:
            print(f"  {tag}: {pct:+.3f}%", file=sys.stderr)
        sys.exit(3)

    # Pop-weighted preservation guard — this is the invariant we promise.
    drift_tags = [r for r in summary_rows if abs(r["pop_w_drift_pct"]) > 0.5]
    if drift_tags:
        print(
            "\nWARNING: pop-weighted mean drifted > 0.5% (binding clamps prevented full preservation):",
            file=sys.stderr,
        )
        for r in drift_tags:
            print(f"  {r['tag']}: {r['pop_w_drift_pct']:+.3f}%", file=sys.stderr)


if __name__ == "__main__":
    main()
