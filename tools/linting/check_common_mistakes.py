#!/usr/bin/env python3
"""
Check for common scripting mistakes in HOI4 mod files.

Detects mechanically-checkable rule violations from CLAUDE.md:
  - threat > N where N >= 1 (threat is 0.0-1.0, not a percentage)
  - has_war_support / has_stability > N where N >= 1 (0.0-1.0 range)
  - allowed = { always = no } in ideas (default, hurts performance)
  - cancel = { always = no } in ideas (checked hourly, never true)
  - Division instead of multiplication (/ 100 -> * 0.01)
"""

import argparse
import os
import re
import subprocess
import sys
from multiprocessing import Pool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from path_utils import clean_filepath


def get_git_diff_files(base_branch="main", staged_only=False):
    """Get list of modified .txt files from git diff."""
    try:
        if staged_only:
            cmd = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMRT"]
        else:
            cmd = [
                "git",
                "diff",
                "--name-only",
                "--diff-filter=ACMRT",
                f"{base_branch}...HEAD",
            ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        modified_files = []
        for file in result.stdout.strip().split("\n"):
            if file and file.endswith(".txt"):
                if any(
                    file.startswith(d + "/") for d in ["common", "events", "history"]
                ):
                    if os.path.exists(file):
                        modified_files.append(file)
        return modified_files
    except subprocess.CalledProcessError:
        return []


def check_file(filepath):
    """Check a single file for common mistakes. Returns list of (filepath, line_num, message) tuples."""
    issues = []

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception:
        return issues

    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()

        # Skip comments
        if stripped.startswith("#"):
            continue

        # Remove inline comments for analysis
        code_part = line.split("#")[0] if "#" in line else line

        # Check 1: threat > N where N >= 1 (should be decimal 0.0-1.0)
        # Only match comparison operators (> < >= <=), not bare = which is
        # used in add_named_threat = { threat = N } and similar effects
        threat_match = re.search(r"(?<!\w)threat\s*([><]=?)\s*(\d+\.?\d*)", code_part)
        if (
            threat_match
            and "add_threat" not in code_part
            and "named_threat" not in code_part
        ):
            value = float(threat_match.group(2))
            if value >= 1.0:
                suggestion = round(value / 100.0, 4)
                issues.append(
                    (
                        line_num,
                        f"threat {threat_match.group(1)} {value} looks like a percentage -- threat is 0.0-1.0 (use {suggestion}?)",
                    )
                )

        # Check 5: has_war_support / has_stability with values >= 1 (should be 0.0-1.0)
        for trigger_name in ("has_war_support", "has_stability"):
            ws_match = re.search(
                rf"(?<!\w){trigger_name}\s*([><]=?)\s*(\d+\.?\d*)", code_part
            )
            if ws_match:
                value = float(ws_match.group(2))
                if value >= 1.0:
                    suggestion = round(value / 100.0, 4)
                    issues.append(
                        (
                            line_num,
                            f"{trigger_name} {ws_match.group(1)} {ws_match.group(2)} looks like a percentage -- {trigger_name} is 0.0-1.0 (use {suggestion}?)",
                        )
                    )

        # Check 2: allowed = { always = no } in ideas (default, hurts performance)
        # Only flag in idea files -- decisions use this intentionally to hide
        # programmatically-activated decisions
        if "common/ideas" in filepath:
            if re.search(r"allowed\s*=\s*\{\s*always\s*=\s*no\s*\}", code_part):
                issues.append(
                    (
                        line_num,
                        "allowed = { always = no } is the default for ideas -- remove it (hurts performance)",
                    )
                )

        # Check 3: cancel = { always = no } in ideas (checked hourly, never true)
        if "common/ideas" in filepath:
            if re.search(r"cancel\s*=\s*\{\s*always\s*=\s*no\s*\}", code_part):
                issues.append(
                    (
                        line_num,
                        "cancel = { always = no } is checked hourly and never true -- remove it",
                    )
                )

        # Check 4: Division where multiplication should be used
        div_match = re.search(r"/\s*(100|1000|10|50|200|500)\b", code_part)
        if div_match:
            divisor = int(div_match.group(1))
            multiplier = 1.0 / divisor
            if multiplier == int(multiplier):
                mult_str = str(int(multiplier))
            else:
                mult_str = f"{multiplier:g}"
            issues.append(
                (
                    line_num,
                    f"use multiplication instead of division (/ {divisor} -> * {mult_str})",
                )
            )

    return [(filepath, ln, msg) for ln, msg in issues]


def get_all_files(root_dir):
    """Get all .txt files from relevant directories."""
    files = []
    for directory in ["common", "events", "history"]:
        dir_path = os.path.join(root_dir, directory)
        if os.path.exists(dir_path):
            for root, _, filenames in os.walk(dir_path):
                for filename in filenames:
                    if filename.endswith(".txt"):
                        files.append(os.path.join(root, filename))
    return files


def main():
    parser = argparse.ArgumentParser(
        description="Check for common HOI4 scripting mistakes"
    )
    parser.add_argument(
        "--mode",
        choices=["all", "diff", "staged"],
        default="all",
        help="Check mode: all files, git diff files, or staged files only (default: all)",
    )
    parser.add_argument(
        "--base-branch",
        default="main",
        help="Base branch for diff comparison (default: main)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=os.cpu_count() or 4,
        help="Number of parallel workers (default: CPU count)",
    )
    parser.add_argument(
        "filenames",
        nargs="*",
        help="Files to check (positional argument for pre-commit)",
    )
    args = parser.parse_args()

    script_dir = os.path.realpath(__file__)
    root_dir = os.path.dirname(os.path.dirname(script_dir))

    if args.filenames:
        files_list = [f for f in args.filenames if os.path.exists(f)]
    elif args.mode == "staged":
        files_list = get_git_diff_files(staged_only=True)
    elif args.mode == "diff":
        files_list = get_git_diff_files(base_branch=args.base_branch)
    else:
        files_list = get_all_files(root_dir)

    if not files_list:
        print("No files to check")
        return 0

    print(f"Checking {len(files_list)} files for common mistakes...")

    with Pool(processes=args.workers) as pool:
        results = pool.map(check_file, files_list)

    all_issues = []
    for file_issues in results:
        all_issues.extend(file_issues)

    for filepath, line_num, message in sorted(all_issues):
        print(f"WARNING: {clean_filepath(filepath)}:{line_num}: {message}")

    print(f"------\nChecked {len(files_list)} files")
    if all_issues:
        print(f"Found {len(all_issues)} issue(s)")
        print("Check FAILED")
        return 1
    else:
        print("No issues found")
        print("Check PASSED")
        return 0


if __name__ == "__main__":
    sys.exit(main())
