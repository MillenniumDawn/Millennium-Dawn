#!/usr/bin/env python3
"""
Check for common scripting mistakes in HOI4 mod files.

Detects mechanically-checkable rule violations from CLAUDE.md:
  - threat/has_war_support/has_stability comparisons >= 1 (all are 0.0-1.0 ranges)
  - allowed = { always = no } in country/hidden_ideas idea categories (default, hurts performance)
  - allowed = { tag = TAG } in country/hidden_ideas (breaks civil war split-offs; use original_tag)
  - allowed_civil_war = { always = no } in ideas (no effect, remove it)
  - cancel = { always = no } in ideas (checked hourly, never true)
  - ai_will_do root-level factor = N (should be base = N; factor only valid in modifier children)
  - Division instead of multiplication (/ 100 -> * 0.01)
"""

import argparse
import os
import re
import subprocess
import sys
from multiprocessing import Pool

# Compiled patterns — done once at import, not per file/line
_RE_THREAT = re.compile(r"(?<!\w)threat\s*([><]=?)\s*(\d+\.?\d*)")
_RE_WAR_SUPPORT = re.compile(r"(?<!\w)has_war_support\s*([><]=?)\s*(\d+\.?\d*)")
_RE_STABILITY = re.compile(r"(?<!\w)has_stability\s*([><]=?)\s*(\d+\.?\d*)")
_RE_ALLOWED_ALWAYS_NO = re.compile(r"allowed\s*=\s*\{\s*always\s*=\s*no\s*\}")
_RE_ALLOWED_OPEN = re.compile(r"allowed\s*=\s*\{")
_RE_ALLOWED_TAG = re.compile(r"allowed\s*=\s*\{\s*tag\s*=\s*\w+\s*\}")
_RE_ALLOWED_CIVIL_WAR = re.compile(r"allowed_civil_war\s*=\s*\{\s*always\s*=\s*no\s*\}")
_RE_CANCEL = re.compile(r"cancel\s*=\s*\{\s*always\s*=\s*no\s*\}")
_RE_AI_WILL_DO = re.compile(r"ai_will_do\s*=\s*\{[^{]*?\bfactor\b\s*=")
_RE_DIVISION = re.compile(r"/\s*(100|1000|10|50|200|500)\b")
_RE_IDEAS_BLOCK = re.compile(r"^ideas\s*=\s*\{")
_RE_CATEGORY = re.compile(r"^(\w+)\s*=\s*\{")

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

    is_ideas = "common/ideas" in filepath
    is_ai_file = any(
        d in filepath
        for d in (
            "common/national_focus",
            "common/decisions",
            "common/military_industrial_organization",
        )
    )

    # Only track idea categories for idea files (country/hidden_ideas vs others)
    FLAGGED_IDEA_CATEGORIES = {"country", "hidden_ideas"}
    current_category = None
    brace_depth = 0
    ideas_depth = None
    # Multi-line allowed block tracking (flags only if sole content is always = no)
    in_allowed_block = False
    allowed_block_start_line = 0
    allowed_block_depth = 0
    allowed_block_lines = []

    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()

        # Brace/category tracking is only needed for idea files
        if is_ideas:
            brace_depth += stripped.count("{") - stripped.count("}")

            if _RE_IDEAS_BLOCK.match(stripped):
                ideas_depth = brace_depth - 1
            if ideas_depth is not None and brace_depth == ideas_depth + 2:
                cat_match = _RE_CATEGORY.match(stripped)
                if cat_match:
                    current_category = cat_match.group(1)
            elif ideas_depth is not None and brace_depth <= ideas_depth + 1:
                current_category = None

        if stripped.startswith("#"):
            continue

        code_part = line.split("#")[0] if "#" in line else line

        # threat is 0.0-1.0; exclude add_threat/named_threat which use absolute values
        threat_match = _RE_THREAT.search(code_part)
        if (
            threat_match
            and "add_threat" not in code_part
            and "named_threat" not in code_part
        ):
            value = float(threat_match.group(2))
            if value >= 1.0:
                issues.append(
                    (
                        line_num,
                        f"threat {threat_match.group(1)} {value} looks like a percentage -- threat is 0.0-1.0 (use {round(value / 100.0, 4)}?)",
                    )
                )

        for trigger_name, pattern in (
            ("has_war_support", _RE_WAR_SUPPORT),
            ("has_stability", _RE_STABILITY),
        ):
            ws_match = pattern.search(code_part)
            if ws_match:
                value = float(ws_match.group(2))
                if value >= 1.0:
                    issues.append(
                        (
                            line_num,
                            f"{trigger_name} {ws_match.group(1)} {ws_match.group(2)} looks like a percentage -- {trigger_name} is 0.0-1.0 (use {round(value / 100.0, 4)}?)",
                        )
                    )

        if is_ideas and current_category in FLAGGED_IDEA_CATEGORIES:
            # Single-line forms
            if _RE_ALLOWED_ALWAYS_NO.search(code_part):
                issues.append(
                    (
                        line_num,
                        f"allowed = {{ always = no }} is the default for ideas in '{current_category}' -- remove it (hurts performance)",
                    )
                )
            elif _RE_ALLOWED_OPEN.search(code_part) and "}" not in code_part:
                # Opening of a multi-line allowed block — collect its contents
                in_allowed_block = True
                allowed_block_start_line = line_num
                allowed_block_depth = brace_depth
                allowed_block_lines = []
            if _RE_ALLOWED_TAG.search(code_part):
                issues.append(
                    (
                        line_num,
                        "allowed = { tag = TAG } breaks for civil war split-offs -- use original_tag = TAG instead",
                    )
                )

        # Multi-line allowed block: flag only if sole content is always = no
        if in_allowed_block:
            if brace_depth < allowed_block_depth:
                content_lines = [
                    l for l in allowed_block_lines if l not in ("", "{", "}")
                ]
                if content_lines == ["always = no"]:
                    issues.append(
                        (
                            allowed_block_start_line,
                            f"allowed = {{ always = no }} is the default for ideas in '{current_category}' -- remove it (hurts performance)",
                        )
                    )
                in_allowed_block = False
                allowed_block_lines = []
            elif stripped and not _RE_ALLOWED_OPEN.match(stripped):
                allowed_block_lines.append(stripped)

        if is_ideas:
            if _RE_ALLOWED_CIVIL_WAR.search(code_part):
                issues.append(
                    (
                        line_num,
                        "allowed_civil_war = { always = no } has no effect -- remove it",
                    )
                )
            if _RE_CANCEL.search(code_part):
                issues.append(
                    (
                        line_num,
                        "cancel = { always = no } is checked hourly and never true -- remove it",
                    )
                )

        # [^{]*? stops before any nested { so modifier = { factor = X } children are not flagged
        if is_ai_file and _RE_AI_WILL_DO.search(code_part):
            issues.append(
                (
                    line_num,
                    "ai_will_do root-level 'factor =' should be 'base =' -- factor is only valid inside modifier = { } children",
                )
            )

        div_match = _RE_DIVISION.search(code_part)
        if div_match:
            divisor = int(div_match.group(1))
            multiplier = 1.0 / divisor
            mult_str = (
                str(int(multiplier))
                if multiplier == int(multiplier)
                else f"{multiplier:g}"
            )
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

    script_dir = os.path.dirname(os.path.realpath(__file__))
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

    all_issues = [issue for file_issues in results for issue in file_issues]

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
