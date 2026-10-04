#!/usr/bin/env python3
"""
Suggest starting overall_productivity and gdp_per_capita seeds for country history files.

Suggestions follow the states a country owns. overall_productivity is the
population-weighted mean of productivity_state_var. gdp_per_capita is the value
the game's GDP calculation settles on, using the @gdp_* factors in
common/scripted_effects/00_money_system.txt (via estimate_gdp.py).

Seeds may deviate for gameplay reasons, so the check only reports and always
exits 0. --write applies the suggestions for the TAGs you name.

Usage:
    python3 tools/run.py gdp_seeds TAG [TAG ...]
    python3 tools/run.py gdp_seeds "history/states/1-Central Plateau.txt"
    python3 tools/run.py gdp_seeds --all
    python3 tools/run.py gdp_seeds --write TAG [TAG ...]
"""

import argparse
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import estimate_gdp  # noqa: E402

SEED_KEYS = ("overall_productivity", "gdp_per_capita")
COUNTRY_FILE_RE = re.compile(r"history[\\/]countries[\\/]([A-Z0-9]{3}) [^\\/]*\.txt$")
STATE_FILE_RE = re.compile(r"history[\\/]states[\\/][^\\/]*\.txt$")
GDPC_PRECISION = 0.001


def seed_re(key):
    """Match both `{ key = N }` and `{ var = key value = N }` seed lines."""
    return re.compile(
        rf"(set_variable\s*=\s*\{{\s*(?:var\s*=\s*{key}\s+value|{key})\s*=\s*)"
        rf"([-\d.]+)(\s*\}})"
    )


SEED_RES = {key: seed_re(key) for key in SEED_KEYS}


def load_states_by_owner():
    by_owner = defaultdict(list)
    for fname in sorted(os.listdir(estimate_gdp.STATES_DIR)):
        if not fname.endswith(".txt"):
            continue
        state = estimate_gdp.parse_state_file(
            os.path.join(estimate_gdp.STATES_DIR, fname)
        )
        if state["owner"]:
            by_owner[state["owner"]].append(state)
    return by_owner


def country_file(tag):
    for fname in sorted(os.listdir(estimate_gdp.COUNTRIES_DIR)):
        if fname.startswith(f"{tag} ") and fname.endswith(".txt"):
            return os.path.join(estimate_gdp.COUNTRIES_DIR, fname)
    return None


def read_text(path):
    """Read without newline translation so a rewrite keeps the file's line endings."""
    with open(path, "r", encoding="utf-8", newline="") as f:
        return f.read()


def read_seeds(path):
    """Return {key: [values in file order]} for each seed key."""
    content = read_text(path)
    return {
        key: [float(m.group(2)) for m in SEED_RES[key].finditer(content)]
        for key in SEED_KEYS
    }


def suggest_seeds(tag, states, idea_db):
    """Return {key: suggested value} or None when the country has no population."""
    result = estimate_gdp.compute_country_gdp(tag, states, idea_db)
    if result is None:
        return None
    # Healthcare GDP uses the previous gdp_per_capita, so iterate to the value
    # the game converges on after its first few calculations.
    health_idea = result["health_idea"]
    gdpc = result["gdp_per_capita"]
    for _ in range(50):
        estimate_gdp.finalize_gdp(result, health_idea, gdpc)
        if abs(result["gdp_per_capita"] - gdpc) < GDPC_PRECISION:
            break
        gdpc = result["gdp_per_capita"]
    return {
        "overall_productivity": round(result["overall_productivity"]),
        "gdp_per_capita": round(result["gdp_per_capita"], 3),
    }


def format_seed(key, value):
    if key == "overall_productivity":
        return str(int(value))
    return f"{value:.3f}"


def write_seeds(path, suggestion):
    """Rewrite the seed lines in place. Returns a list of skip reasons."""
    original = content = read_text(path)
    skipped = []
    for key in SEED_KEYS:
        matches = list(SEED_RES[key].finditer(content))
        if len(matches) != 1:
            skipped.append(f"{key}: {len(matches)} seed lines, not written")
            continue
        new_value = format_seed(key, suggestion[key])
        content = SEED_RES[key].sub(
            lambda m: f"{m.group(1)}{new_value}{m.group(3)}", content, count=1
        )
    if content != original:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(content)
    return skipped


def tags_from_targets(targets):
    """Split CLI targets into TAGs, resolving state and country file paths."""
    tags = []
    for target in targets:
        normalized = target.replace("\\", "/")
        country = COUNTRY_FILE_RE.search(normalized)
        if country:
            tags.append(country.group(1))
        elif STATE_FILE_RE.search(normalized):
            if os.path.isfile(target):
                owner = estimate_gdp.parse_state_file(target)["owner"]
                if owner:
                    tags.append(owner)
        elif not target.endswith(".txt"):
            tags.append(target.upper())
    return list(dict.fromkeys(tags))


def delta_pct(seed, suggested):
    if seed is None or seed == 0:
        return None
    return 100.0 * (suggested - seed) / seed


def parse_args(argv):
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("targets", nargs="*", help="country TAGs or history file paths")
    p.add_argument("--all", action="store_true", help="every country that owns states")
    p.add_argument(
        "--write",
        action="store_true",
        help="apply the suggestions to the named TAGs (or --all)",
    )
    p.add_argument(
        "--tolerance",
        type=float,
        default=5.0,
        help="flag seeds that differ by more than this percent (default 5)",
    )
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.write and not args.all:
        if not args.targets or any(t.endswith(".txt") for t in args.targets):
            print("error: --write needs TAG arguments or --all", file=sys.stderr)
            return 2
    if not args.targets and not args.all:
        print(__doc__)
        return 2

    by_owner = load_states_by_owner()
    tags = sorted(by_owner) if args.all else tags_from_targets(args.targets)
    if not tags:
        return 0
    idea_db = estimate_gdp.parse_all_ideas()

    rows = []
    for tag in tags:
        path = country_file(tag)
        if tag not in by_owner or path is None:
            print(f"{tag}: no owned states or no history/countries file, skipped")
            continue
        suggestion = suggest_seeds(tag, by_owner[tag], idea_db)
        if suggestion is None:
            print(f"{tag}: no population, skipped")
            continue
        seeds = read_seeds(path)
        current = {key: (seeds[key][0] if seeds[key] else None) for key in SEED_KEYS}
        rows.append((tag, path, current, suggestion))

    print(
        f"{'TAG':<5} {'Productivity':>12} {'Suggested':>10} {'Delta%':>8}"
        f" {'GDP/C':>10} {'Suggested':>10} {'Delta%':>8}"
    )
    flagged = []
    for tag, _, current, suggestion in rows:
        cells = []
        off = False
        for key in SEED_KEYS:
            seed = current[key]
            delta = delta_pct(seed, suggestion[key])
            off = off or delta is None or abs(delta) > args.tolerance
            width = 12 if key == "overall_productivity" else 10
            seed_text = "-" if seed is None else format_seed(key, seed)
            delta_text = "-" if delta is None else f"{delta:+.1f}"
            cells.append(
                f"{seed_text:>{width}} {format_seed(key, suggestion[key]):>10}"
                f" {delta_text:>8}"
            )
        if off:
            flagged.append(tag)
        print(f"{tag:<5} {' '.join(cells)}{' *' if off else ''}")

    if args.write:
        for tag, path, _, suggestion in rows:
            skipped = write_seeds(path, suggestion)
            for reason in skipped:
                print(f"{tag}: {reason}")
            if len(skipped) < len(SEED_KEYS):
                print(f"{tag}: seeds written to {os.path.basename(path)}")
    elif flagged:
        print(
            f"\n* differs by more than {args.tolerance:g}% or has no seed. Keep a seed"
            " that is intentional, or apply with:\n"
            f"  python3 tools/run.py gdp_seeds --write {' '.join(flagged)}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
