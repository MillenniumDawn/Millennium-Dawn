#!/usr/bin/env python3

"""
Pre-commit hook wrapper for staged file validation.

Runs validators for file types that are staged. Each validator skips
cross-reference checks in staged mode so it only validates the staged
files themselves (CI handles the full cross-reference validation).

  - events/*.txt                      -> validate_events.py
  - common/decisions/*.txt            -> validate_decisions.py
  - localisation/*.yml                -> validate_localisation.py
  - history/countries/*.txt           -> validate_history_techs.py
  - common/, events/, history/        -> validate_variables.py
  - common/scripted_localisation/     -> validate_scripted_localisation.py
  - common/                           -> validate_cosmetic_tags.py
  - common/scripted_effects/,
    common/scripted_triggers/         -> validate_unused_scripted.py
  - history/units/, common/units/,
    common/ai_templates/,
    common/scripted_effects/          -> validate_oob_units.py
  - common/ideas/, common/national_focus/,
    common/decisions/, events/        -> validate_ideas.py

Opt-out via environment variable:
    MD_SKIP_VALIDATE=1 git commit -m "..."
"""

import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from shared_utils import timing_enabled

VALIDATORS = [
    {
        "name": "events",
        "prefixes": ["events/"],
        "suffix": ".txt",
        "cmd": [
            "python3",
            "tools/validation/validate_events.py",
            "--staged",
            "--strict",
            "--no-color",
        ],
    },
    {
        "name": "decisions",
        "prefixes": ["common/decisions/"],
        "suffix": ".txt",
        "cmd": [
            "python3",
            "tools/validation/validate_decisions.py",
            "--staged",
            "--strict",
            "--no-color",
        ],
    },
    {
        "name": "localisation",
        "prefixes": ["localisation/"],
        "suffix": ".yml",
        "cmd": [
            "python3",
            "tools/validation/validate_localisation.py",
            "--staged",
            "--strict",
            "--no-color",
        ],
    },
    {
        "name": "history techs",
        "prefixes": ["history/countries/"],
        "suffix": ".txt",
        "cmd": [
            "python3",
            "tools/validation/validate_history_techs.py",
            "--staged",
            "--strict",
            "--no-color",
        ],
    },
    {
        "name": "variables",
        "prefixes": ["common/", "events/", "history/"],
        "suffix": ".txt",
        "cmd": [
            "python3",
            "tools/validation/validate_variables.py",
            "--staged",
            "--strict",
            "--no-color",
            "--workers",
            "4",
        ],
    },
    {
        "name": "scripted localisation",
        "prefixes": ["common/scripted_localisation/"],
        "suffix": ".txt",
        "cmd": [
            "python3",
            "tools/validation/validate_scripted_localisation.py",
            "--staged",
            "--strict",
            "--no-color",
            "--workers",
            "4",
        ],
    },
    {
        "name": "cosmetic tags",
        "prefixes": ["common/"],
        "suffix": ".txt",
        "cmd": [
            "python3",
            "tools/validation/validate_cosmetic_tags.py",
            "--staged",
            "--strict",
            "--no-color",
            "--workers",
            "4",
        ],
    },
    {
        "name": "unused scripted",
        "prefixes": ["common/scripted_effects/", "common/scripted_triggers/"],
        "suffix": ".txt",
        "cmd": [
            "python3",
            "tools/validation/validate_unused_scripted.py",
            "--staged",
            "--strict",
            "--no-color",
        ],
    },
    {
        "name": "oob units",
        "prefixes": [
            "history/units/",
            "common/units/",
            "common/ai_templates/",
            "common/scripted_effects/",
        ],
        "suffix": ".txt",
        "cmd": [
            "python3",
            "tools/validation/validate_oob_units.py",
            "--staged",
            "--strict",
            "--no-color",
        ],
    },
    {
        "name": "ideas",
        "prefixes": [
            "common/ideas/",
            "common/national_focus/",
            "common/decisions/",
            "events/",
        ],
        "suffix": ".txt",
        "cmd": [
            "python3",
            "tools/validation/validate_ideas.py",
            "--staged",
            "--strict",
            "--no-color",
            "--workers",
            "4",
        ],
    },
]


def get_staged_files():
    """Return list of staged file paths."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMRT"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip().split("\n") if result.stdout.strip() else []


def main():
    if os.environ.get("MD_SKIP_VALIDATE", "") == "1":
        return 0

    show_timing = timing_enabled()
    total_start = time.perf_counter()

    staged = get_staged_files()
    os.environ["MD_STAGED_FILES"] = "\n".join(staged)
    failed = False
    timings = []

    for v in VALIDATORS:
        has_matching = any(
            any(f.startswith(p) for p in v["prefixes"]) and f.endswith(v["suffix"])
            for f in staged
        )
        if not has_matching:
            continue

        print(f"Running {v['name']} validator...")
        t0 = time.perf_counter()
        try:
            result = subprocess.run(v["cmd"], timeout=300)
        except subprocess.TimeoutExpired:
            print(f"ERROR: {v['name']} validator timed out after 5 minutes")
            failed = True
            timings.append((v["name"], 300.0))
            continue
        elapsed = time.perf_counter() - t0
        timings.append((v["name"], elapsed))
        if result.returncode != 0:
            failed = True

    if show_timing and timings:
        total = time.perf_counter() - total_start
        max_label = max(len(name) for name, _ in timings)
        print(f"\n\033[90m{'─' * (max_label + 18)}", file=sys.stderr)
        print("  Validator timing:", file=sys.stderr)
        for name, elapsed in timings:
            bar_len = int(elapsed / total * 20) if total > 0 else 0
            bar = "█" * bar_len + "░" * (20 - bar_len)
            print(
                f"  {name:<{max_label}}  {elapsed:6.3f}s  {bar}",
                file=sys.stderr,
            )
        print(f"  {'total':<{max_label}}  {total:6.3f}s", file=sys.stderr)
        print(f"{'─' * (max_label + 18)}\033[0m", file=sys.stderr)

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
