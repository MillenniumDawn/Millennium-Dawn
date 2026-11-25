#!/usr/bin/env python3
"""Set up and save headless HOI4 test runs of the mod.

    python tools/analysis/headless_run.py bench on
    python tools/analysis/headless_run.py war add CHI:RAJ PER:IRQ
    python tools/analysis/headless_run.py war remove
    python tools/analysis/headless_run.py probe add BRA --every year --kind stats infrastructure
    python tools/analysis/headless_run.py probe remove
    python tools/analysis/headless_run.py save ~/Documents/md-benchmarks/2026-11-17-run1

`bench on` turns on the benchmark log lines (Monthly Benchmark, Construction, Resource
Balance, Weekly Economic Update, Spending Laws, war declarations and capitulations)
without -debug, which halves run speed. `war add` declares test wars at game start.
`probe add` logs one country's state from its on_monthly_TAG on_action: `--kind`
picks probes from tools/analysis/hoi4_probes (default stats), and `--every year`
logs once every 12 months instead of monthly. All three write untracked, gitignored
zz_md_run_* on_actions files, so no tracked file changes between runs; `off` and
`remove` delete them. `save` copies game.log, error.log, and the newest save from
the HOI4 user folder into a run folder for benchmark_report.py and inspect_save.py.
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import shutil
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BENCH_FILE = "common/on_actions/zz_md_run_benchmark_logging.txt"
WAR_FILE = "common/on_actions/zz_md_run_test_war.txt"
PROBE_FILE = "common/on_actions/zz_md_run_probe.txt"
PROBE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hoi4_probes")
PROBE_KINDS = {
    "stats": "country_stats.txt",
    "infrastructure": "state_infrastructure.txt",
}
_PAIR_RE = re.compile(r"^([A-Z][A-Z0-9]{2}):([A-Z][A-Z0-9]{2})$")
_TAG_RE = re.compile(r"^[A-Z][A-Z0-9]{2}$")


def default_user_dir() -> str:
    if sys.platform.startswith("linux"):
        base = os.path.expanduser("~/.local/share")
    else:
        base = os.path.expanduser("~/Documents")
    return os.path.join(base, "Paradox Interactive", "Hearts of Iron IV")


def _write(path: str, effects: list[str], on_action: str = "on_startup") -> None:
    body = "".join(f"\t\t\t{line}\n" for line in effects)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(
            f"on_actions = {{\n\t{on_action} = {{\n\t\teffect = {{\n{body}\t\t}}\n\t}}\n}}\n"
        )
    print(f"wrote {path}")


def _remove(path: str) -> None:
    if os.path.exists(path):
        os.remove(path)
        print(f"removed {path}")
    else:
        print(f"nothing to remove at {path}")


def bench(root: str, state: str) -> int:
    path = os.path.join(root, BENCH_FILE)
    if state == "on":
        _write(path, ["set_global_flag = GLOBAL_md_benchmark_logging"])
    else:
        _remove(path)
    return 0


def war(root: str, action: str, pairs: list[str]) -> int:
    path = os.path.join(root, WAR_FILE)
    if action == "remove":
        _remove(path)
        return 0
    effects = []
    for pair in pairs:
        found = _PAIR_RE.match(pair)
        if not found:
            print(f"expected ATTACKER:DEFENDER tags, got {pair!r}", file=sys.stderr)
            return 1
        attacker, defender = found.groups()
        effects.append(
            f"{attacker} = {{ declare_war_on = {{ target = {defender} type = annex_everything }} }}"
        )
    if not effects:
        print("give at least one ATTACKER:DEFENDER pair", file=sys.stderr)
        return 1
    _write(path, effects)
    return 0


def probe(root: str, action: str, tag: str | None, every: str, kinds: list[str]) -> int:
    path = os.path.join(root, PROBE_FILE)
    if action == "remove":
        _remove(path)
        return 0
    if not tag or not _TAG_RE.match(tag):
        print(f"expected a country TAG, got {tag!r}", file=sys.stderr)
        return 1
    effects = []
    for kind in kinds:
        with open(os.path.join(PROBE_DIR, PROBE_KINDS[kind]), encoding="utf-8") as src:
            effects.extend(line.rstrip() for line in src if line.strip())
    if every == "year":
        effects = [
            "add_to_variable = { probe_months = 1 }",
            "if = {",
            "\tlimit = { check_variable = { probe_months > 11 } }",
            "\tset_variable = { probe_months = 0 }",
            *(f"\t{line}" for line in effects),
            "}",
        ]
    _write(path, effects, f"on_monthly_{tag}")
    return 0


def save(user_dir: str, destination: str) -> int:
    saves = glob.glob(os.path.join(user_dir, "save games", "*.hoi4"))
    sources = [
        os.path.join(user_dir, "logs", name) for name in ("game.log", "error.log")
    ]
    if saves:
        sources.append(max(saves, key=os.path.getmtime))
    missing = [path for path in sources if not os.path.isfile(path)]
    if missing or not saves:
        print(
            "missing: " + ", ".join(missing or ["a save in save games/"]),
            file=sys.stderr,
        )
        return 1
    os.makedirs(destination, exist_ok=True)
    for source in sources:
        target = os.path.join(destination, os.path.basename(source))
        shutil.copyfile(source, target)
        print(f"{target}: {os.path.getsize(target):,} bytes")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Set up and save headless HOI4 test runs."
    )
    parser.add_argument("--path", default=REPO, help="mod root (default: repo root)")
    commands = parser.add_subparsers(dest="command", required=True)
    bench_parser = commands.add_parser(
        "bench", help="benchmark log lines without -debug"
    )
    bench_parser.add_argument("state", choices=("on", "off"))
    war_parser = commands.add_parser("war", help="test wars declared at game start")
    war_parser.add_argument("action", choices=("add", "remove"))
    war_parser.add_argument("pairs", nargs="*", help="ATTACKER:DEFENDER tag pairs")
    probe_parser = commands.add_parser("probe", help="log one country's state in a run")
    probe_parser.add_argument("action", choices=("add", "remove"))
    probe_parser.add_argument("tag", nargs="?", help="country TAG to log")
    probe_parser.add_argument("--every", choices=("month", "year"), default="month")
    probe_parser.add_argument(
        "--kind", nargs="+", choices=tuple(PROBE_KINDS), default=["stats"]
    )
    save_parser = commands.add_parser("save", help="copy a run's logs and newest save")
    save_parser.add_argument("destination", help="run folder to create")
    save_parser.add_argument(
        "--user-dir", default=default_user_dir(), help="HOI4 user folder"
    )
    args = parser.parse_args()
    if args.command == "bench":
        return bench(args.path, args.state)
    if args.command == "war":
        return war(args.path, args.action, args.pairs)
    if args.command == "probe":
        return probe(args.path, args.action, args.tag, args.every, args.kind)
    return save(args.user_dir, args.destination)


if __name__ == "__main__":
    sys.exit(main())
