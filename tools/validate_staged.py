#!/usr/bin/env python3

"""
Pre-commit hook wrapper for staged file validation.

Opt-in via environment variable:
    MD_VALIDATE=1 git commit -m "..."

Runs validators only for file types that are staged:
  - events/*.txt          -> validate_events.py
  - common/decisions/*.txt -> validate_decisions.py
  - localisation/*.yml    -> validate_localisation.py

Skips silently when MD_VALIDATE is not set.
"""

import os
import subprocess
import sys

VALIDATORS = [
    {
        "name": "events",
        "prefix": "events/",
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
        "prefix": "common/decisions/",
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
        "prefix": "localisation/",
        "suffix": ".yml",
        "cmd": [
            "python3",
            "tools/validation/validate_localisation.py",
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
    if os.environ.get("MD_VALIDATE", "") != "1":
        return 0

    staged = get_staged_files()
    failed = False

    for v in VALIDATORS:
        has_matching = any(
            f.startswith(v["prefix"]) and f.endswith(v["suffix"]) for f in staged
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
