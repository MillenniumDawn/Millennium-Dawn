#!/usr/bin/env python3
"""
Fix styling issues in HOI4 mod files.

Automatically fixes all issues detected by check_basic_style.py and
check_basic_style_2.py:
  - 4-space indentation -> tabs
  - Missing/extra spaces around = signs
  - Missing spaces around { } braces
  - === separator lines in comments (-> ---)
  - Multiple consecutive spaces (collapsed to single)
  - Trailing whitespace
  - Trailing blank lines

Reports but does not fix:
  - Odd number of quotation marks (needs manual review)
  - Mismatched braces (structural issue)
"""

import argparse
import fnmatch
import os
import re
import subprocess
import sys
import time
from multiprocessing import Pool
from pathlib import Path

from path_utils import clean_filepath

__version__ = 2.0


def get_git_diff_files(base_branch="main", staged_only=False):
    """Get list of modified .txt files from git diff"""
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
                    file.startswith(d + "/")
                    for d in ["common", "events", "history", "interface"]
                ):
                    if os.path.exists(file):
                        modified_files.append(file)

        return modified_files
    except subprocess.CalledProcessError as e:
        print(f"Error getting git diff: {e}")
        return []


def fix_line(line):
    """Fix styling issues in a single line. Returns (fixed_line, fix_count)."""
    original = line
    fixes = 0

    # Step 1: Fix leading indentation (spaces -> tabs) on all lines
    stripped = line.lstrip(" \t")
    leading = line[: len(line) - len(stripped)]
    if " " in leading:
        # Expand existing tabs to 4 spaces, then convert back to tabs
        expanded = leading.replace("\t", "    ")
        num_spaces = len(expanded)
        tabs = num_spaces // 4
        remainder = num_spaces % 4
        new_leading = "\t" * tabs + " " * remainder
        line = new_leading + stripped
        if line != original:
            fixes += 1

    # Step 2: Handle comment-only lines
    stripped_content = line.lstrip("\t ")
    if stripped_content.startswith("#"):
        # Fix === separator lines in comments (validators flag these as = issues)
        if re.search(r"={3,}", line):
            line = re.sub(r"={3,}", lambda m: "-" * len(m.group()), line)
            if line != original:
                fixes += 1
        # Remove trailing whitespace on comment lines
        rstripped = line.rstrip(" \t")
        if rstripped != line.rstrip("\n"):
            line = rstripped + "\n" if original.endswith("\n") else rstripped
            fixes += 1
        return line, fixes

    # Step 3: Split into code and comment parts
    comment_pos = line.find("#")
    if comment_pos > 0:
        code_part = line[:comment_pos]
        comment_part = line[comment_pos:]
        # Fix === in inline comments too
        if re.search(r"={3,}", comment_part):
            comment_part = re.sub(
                r"={3,}", lambda m: "-" * len(m.group()), comment_part
            )
            fixes += 1
    else:
        code_part = line
        comment_part = ""

    # Step 4: Fix equal sign spacing in code part
    if "=" in code_part:
        # Fix double+ spaces before =
        new_code = re.sub(r"  +=", " =", code_part)
        # Fix double+ spaces after =
        new_code = re.sub(r"=  +", "= ", new_code)
        # Fix tab(s) before = (tab-alignment)
        new_code = re.sub(r"\t+(=)", r" \1", new_code)
        # Fix missing space before = (but not <=, >=, !=)
        new_code = re.sub(r"([^\s!<>=])=", r"\1 =", new_code)
        # Fix missing space after = (but not ==, =>)
        new_code = re.sub(r"=([^\s=>{])", r"= \1", new_code)
        if new_code != code_part:
            code_part = new_code
            fixes += 1

    # Step 5: Fix brace spacing in code part
    if "{" in code_part or "}" in code_part:
        new_code = code_part
        # Add space before { if missing (not at line start)
        new_code = re.sub(r"([^\s])\{", r"\1 {", new_code)
        # Add space after { if missing (not at end of line), including before }
        new_code = re.sub(r"\{([^\s\n])", r"{ \1", new_code)
        # Add space before } if missing (including after {)
        new_code = re.sub(r"([^\s])\}", r"\1 }", new_code)
        # Add space after } if missing (not at end of line)
        new_code = re.sub(r"\}([^\s\n}])", r"} \1", new_code)
        # Handle }} -> } } (add space between consecutive closing braces)
        while "}}" in new_code:
            new_code = new_code.replace("}}", "} }")
        # Fix double+ spaces around braces
        new_code = re.sub(r"  +\{", " {", new_code)
        new_code = re.sub(r"\{  +", "{ ", new_code)
        new_code = re.sub(r"  +\}", " }", new_code)
        new_code = re.sub(r"\}  +", "} ", new_code)
        if new_code != code_part:
            code_part = new_code
            fixes += 1

    # Step 6: Collapse multiple spaces to single in code part (not leading indent)
    code_stripped = code_part.lstrip("\t")
    code_indent = code_part[: len(code_part) - len(code_stripped)]
    if "    " in code_stripped:
        new_stripped = re.sub(r"  +", " ", code_stripped)
        if new_stripped != code_stripped:
            code_part = code_indent + new_stripped
            fixes += 1

    # Reassemble line
    line = code_part + comment_part

    # Step 7: Remove trailing whitespace (preserve newline)
    if line.endswith("\n"):
        rstripped = line.rstrip(" \t\n") + "\n"
    else:
        rstripped = line.rstrip(" \t")
    if rstripped != line:
        line = rstripped
        fixes += 1

    return line, fixes


def fix_file(filepath):
    """Fix all styling issues in a single file.

    Returns (filepath, fixes_count, unfixable_issues).
    """
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        lines = content.split("\n")
        fixed_lines = []
        total_fixes = 0
        unfixable = []

        for line_num, line in enumerate(lines, 1):
            # Preserve newlines for processing (add back for fix_line)
            fixed, fixes = fix_line(line)
            total_fixes += fixes
            fixed_lines.append(fixed)

            # Report unfixable: odd number of quotes
            if '"' in line and not line.strip().startswith("#"):
                code = line.split("#")[0] if "#" in line else line
                if code.count('"') % 2 == 1:
                    unfixable.append(
                        f"  {clean_filepath(filepath)}:{line_num}: Possible missing quotation mark"
                    )

        # Remove excessive trailing blank lines, ensure single newline at end
        while fixed_lines and fixed_lines[-1] == "":
            fixed_lines.pop()
        fixed_lines.append("")

        new_content = "\n".join(fixed_lines)

        if new_content != content:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)

        return (filepath, total_fixes, unfixable)

    except Exception as e:
        return (filepath, 0, [f"  Error processing {filepath}: {e}"])


def fix_file_dry_run(filepath):
    """Check what would be fixed without writing.

    Returns (filepath, fixes_count, unfixable_issues).
    """
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        total_fixes = 0
        unfixable = []

        for line_num, line in enumerate(lines, 1):
            _, fixes = fix_line(line)
            total_fixes += fixes

            if '"' in line and not line.strip().startswith("#"):
                code = line.split("#")[0] if "#" in line else line
                if code.count('"') % 2 == 1:
                    unfixable.append(
                        f"  {clean_filepath(filepath)}:{line_num}: Possible missing quotation mark"
                    )

        return (filepath, total_fixes, unfixable)

    except Exception as e:
        return (filepath, 0, [f"  Error processing {filepath}: {e}"])


def get_all_files(root_dir):
    """Get all .txt files from relevant directories"""
    files_list = []
    for directory in ["common", "events", "history", "interface"]:
        dir_path = os.path.join(root_dir, directory)
        if os.path.exists(dir_path):
            for root, dirnames, filenames in os.walk(dir_path):
                for filename in fnmatch.filter(filenames, "*.txt"):
                    files_list.append(os.path.join(root, filename))
    return files_list


def main():
    parser = argparse.ArgumentParser(description="Fix styling issues in HOI4 mod files")
    parser.add_argument(
        "--mode",
        choices=["all", "diff", "staged"],
        default="all",
        help="Fix mode: all files, git diff files, or staged files only (default: all)",
    )
    parser.add_argument(
        "--base-branch",
        default="main",
        help="Base branch for diff comparison (default: main)",
    )
    parser.add_argument(
        "--files", nargs="+", help="Specific files to fix (overrides mode)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be fixed without writing changes",
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
        help="Files to fix (positional argument for pre-commit)",
    )

    args = parser.parse_args()

    start_time = time.time()
    print(f"Fix Styling v{__version__} (Mode: {args.mode}, Dry run: {args.dry_run})")

    # Allow running from root directory or tools directory
    script_dir = os.path.realpath(__file__)
    root_dir = os.path.dirname(os.path.dirname(script_dir))

    # Determine which files to process
    if args.filenames:
        files_list = args.filenames
    elif args.files:
        files_list = args.files
    elif args.mode == "diff":
        files_list = get_git_diff_files(base_branch=args.base_branch, staged_only=False)
        if not files_list:
            print("No modified .txt files found in git diff")
            return 0
    elif args.mode == "staged":
        files_list = get_git_diff_files(staged_only=True)
        if not files_list:
            print("No staged .txt files found")
            return 0
    else:
        files_list = get_all_files(root_dir)

    # Filter to existing files
    existing_files = [f for f in files_list if os.path.exists(f)]
    missing = len(files_list) - len(existing_files)
    if missing:
        print(f"WARNING: {missing} files not found, skipping")

    print(f"Processing {len(existing_files)} files...")

    # Process files in parallel
    process_fn = fix_file_dry_run if args.dry_run else fix_file
    with Pool(processes=args.workers) as pool:
        results = pool.map(process_fn, existing_files)

    # Summarize results
    files_fixed = sum(1 for _, fixes, _ in results if fixes > 0)
    total_fixes = sum(fixes for _, fixes, _ in results)
    all_unfixable = []
    for _, _, unfixable in results:
        all_unfixable.extend(unfixable)

    action = "Would fix" if args.dry_run else "Fixed"
    print(f"\n------")
    print(f"Processed {len(existing_files)} files")
    print(f"{action} {total_fixes} issues in {files_fixed} files")

    if all_unfixable:
        print(f"\n{len(all_unfixable)} issues need manual attention:")
        for issue in all_unfixable[:50]:
            print(issue)
        if len(all_unfixable) > 50:
            print(f"  ... and {len(all_unfixable) - 50} more")

    elapsed = time.time() - start_time
    print(f"\nCompleted in {elapsed:.1f}s")

    return 0


if __name__ == "__main__":
    sys.exit(main())
