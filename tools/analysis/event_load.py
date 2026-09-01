#!/usr/bin/env python3
"""Report how many events the yearly pulse schedules for one country, and when.

A country that receives several events within a few days reads as spam even when
the yearly total is modest, so the useful figure is not events per year but the
busiest window inside each year. This walks the two dispatch points that schedule
dated events:

    MD_event_on_startup_events   fires once at game start, so it owns year 2000
    trigger_year_<year>_events   one block per year after that

and follows any scripted effect they call, which is how the corporate history
milestones and similar wrappers hide their country_event behind a name.

    python tools/analysis/event_load.py --tag USA
    python tools/analysis/event_load.py --tag POL --window 45 --threshold 3

Only *scheduled* deliveries are counted. Events fired from an option, a decision
or an on_action are deliberately out of scope: their timing depends on play, so
they cannot be attributed to a calendar day from source alone.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# The startup pulse has no year in its name; it runs at the 2000.1.1 bookmark.
STARTUP_YEAR = "2000"

_EVENT_RE = re.compile(r"country_event = \{ id = ([\w.]+)(?: days = (\d+))?")
_CALL_RE = re.compile(r"^\s*(\w+) = yes\s*$", re.M)
_DEF_RE = re.compile(r"^(\w+) = \{\n(.*?)^\}\n", re.S | re.M)


def read(path: str) -> str:
    with open(path, encoding="utf-8-sig", newline="") as handle:
        return handle.read()


def load_effects(root: str) -> dict[str, str]:
    """Every scripted effect body in the mod, keyed by name."""
    bodies: dict[str, str] = {}
    for path in sorted(
        glob.glob(os.path.join(root, "common", "scripted_effects", "*.txt"))
    ):
        for match in _DEF_RE.finditer(read(path)):
            bodies.setdefault(match.group(1), match.group(2))
    return bodies


def scope_of(tag: str, block: str) -> str:
    """The TAG = { ... } sub-blocks of a yearly block, both multi and single line."""
    parts = re.findall(r"^\t%s = \{\n(.*?)^\t\}\n" % tag, block, re.S | re.M)
    parts += re.findall(r"^\t%s = \{ (.*?) \}\s*$" % tag, block, re.M)
    return "\n".join(parts)


def deliveries(
    body: str, bodies: dict[str, str], depth: int = 0, seen: set[str] | None = None
) -> list[tuple[str, int]]:
    """(event id, day offset) for everything this body schedules, following calls."""
    if seen is None:
        seen = set()
    found = [(m.group(1), int(m.group(2) or 0)) for m in _EVENT_RE.finditer(body)]
    if depth < 4:
        for match in _CALL_RE.finditer(body):
            name = match.group(1)
            if name in bodies and name not in seen:
                seen.add(name)
                found += deliveries(bodies[name], bodies, depth + 1, seen)
    return found


def collect(tag: str, root: str) -> dict[str, list[tuple[str, int]]]:
    """Scheduled deliveries to `tag`, by dispatch year."""
    bodies = load_effects(root)
    yearly = read(
        os.path.join(root, "common", "scripted_effects", "00_yearly_effects.txt")
    )
    rows: dict[str, list[tuple[str, int]]] = defaultdict(list)

    blocks = [
        (m.group(1), m.group(2))
        for m in re.finditer(
            r"^trigger_year_(\d{4})_events = \{\n(.*?)^\}\n", yearly, re.S | re.M
        )
    ]
    startup = re.search(
        r"^MD_event_on_startup_events = \{\n(.*?)^\}\n", yearly, re.S | re.M
    )
    if startup:
        blocks.append((STARTUP_YEAR, startup.group(1)))

    for year, block in blocks:
        rows[year] += deliveries(scope_of(tag, block), bodies)
        # A call at the block's top level may scope into the tag itself, which is
        # how a shared multi-country milestone dispatches.
        for name in re.findall(r"^\t(\w+) = yes$", block, re.M):
            if name in bodies:
                for match in re.finditer(
                    r"%s = \{ country_event = \{ id = ([\w.]+) days = (\d+)" % tag,
                    bodies[name],
                ):
                    rows[year].append((match.group(1), int(match.group(2))))
    return rows


def busiest(days: list[int], window: int) -> int:
    """Most deliveries landing inside any `window`-day span."""
    return max(
        (sum(1 for d in days if start <= d < start + window) for start in days),
        default=0,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report the scheduled event load for one country, by year."
    )
    parser.add_argument("--tag", default="USA", help="country tag (default: USA)")
    parser.add_argument("--path", default=REPO, help="mod root (default: repo root)")
    parser.add_argument(
        "--window", type=int, default=30, help="clustering window in days (default: 30)"
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=4,
        help="flag years with this many inside the window (default: 4)",
    )
    parser.add_argument(
        "--json", action="store_true", help="emit JSON instead of a table"
    )
    args = parser.parse_args()

    tag = args.tag.upper()
    rows = {y: v for y, v in collect(tag, args.path).items() if v}
    if not rows:
        print("no scheduled deliveries found for %s" % tag)
        return 0

    summary = {}
    for year in sorted(rows):
        days = sorted(d for _, d in rows[year])
        summary[year] = {
            "count": len(days),
            "peak": busiest(days, args.window),
            "days": days,
            "events": [e for e, _ in sorted(rows[year], key=lambda x: x[1])],
        }

    if args.json:
        print(
            json.dumps({"tag": tag, "window": args.window, "years": summary}, indent=2)
        )
        return 0

    total = sum(s["count"] for s in summary.values())
    print(
        "%s scheduled event load  (%d deliveries across %d years, mean %.1f/yr)"
        % (tag, total, len(summary), total / len(summary))
    )
    print()
    print("year   n  peak/%dd  day-of-year offsets" % args.window)
    for year, s in summary.items():
        flag = "  <-- clustered" if s["peak"] >= args.threshold else ""
        print(
            "%s %3d  %5d     %s%s"
            % (year, s["count"], s["peak"], ", ".join(str(d) for d in s["days"]), flag)
        )

    hot = [(y, s) for y, s in summary.items() if s["peak"] >= args.threshold]
    if hot:
        print()
        print(
            "years with %d or more inside a %d-day window:"
            % (args.threshold, args.window)
        )
        for year, s in hot:
            print("   %s: %d of %d" % (year, s["peak"], s["count"]))

    namespaces: dict[str, int] = defaultdict(int)
    for s in summary.values():
        for event in s["events"]:
            namespaces[event.split(".")[0]] += 1
    print()
    print("by namespace:")
    for name, count in sorted(namespaces.items(), key=lambda x: (-x[1], x[0])):
        print("   %-38s %d" % (name, count))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
