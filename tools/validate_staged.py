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

Opt-out via environment variable:
    MD_SKIP_VALIDATE=1 git commit -m "..."
"""

import os
import subprocess
import sys

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

    staged = get_staged_files()
    failed = False

    for v in VALIDATORS:
        has_matching = any(
            any(f.startswith(p) for p in v["prefixes"]) and f.endswith(v["suffix"])
            for f in staged
        )
        if not has_matching:
            continue

        print(f"Running {v['name']} validator...")
        result = subprocess.run(v["cmd"])
        if result.returncode != 0:
            failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
