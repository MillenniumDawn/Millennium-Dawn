#!/usr/bin/env python3
"""
review_branch.py — Show a summary of all changes on the current branch vs main.

Usage:
    python3 tools/review_branch.py [base_branch]
"""

import subprocess
import sys


def run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip()


def main() -> None:
    base = sys.argv[1] if len(sys.argv) > 1 else "main"
    current = run(["git", "branch", "--show-current"])

    print("=" * 40)
    print(f"Branch:  {current}")
    print(f"Base:    {base}")
    print("=" * 40)
    print()

    print("--- Commits ---")
    print(run(["git", "log", f"{base}..HEAD", "--oneline"]))
    print()

    print("--- Changed files ---")
    print(run(["git", "diff", f"{base}...HEAD", "--stat"]))
    print()

    print("--- Changes by directory ---")
    names = run(["git", "diff", f"{base}...HEAD", "--name-only"])
    if names:
        dir_counts: dict[str, int] = {}
        for line in names.splitlines():
            parts = line.rsplit("/", 1)
            d = parts[0] if len(parts) > 1 else "."
            dir_counts[d] = dir_counts.get(d, 0) + 1
        for d, count in sorted(dir_counts.items(), key=lambda x: -x[1]):
            print(f"  {count:3d}  {d}")
    print()

    print("--- Full diff ---")
    print(run(["git", "diff", f"{base}...HEAD"]))


if __name__ == "__main__":
    main()
