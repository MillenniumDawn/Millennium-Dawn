#!/usr/bin/env python3
import argparse
import fnmatch
import os
import subprocess
import sys
import time

from path_utils import clean_filepath

__version__ = 1.1


def get_git_diff_files(base_branch="main", staged_only=False):
    """Get list of modified .txt files from git diff"""
    try:
        if staged_only:
            # Check only staged files
            cmd = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMRT"]
        else:
            # Check all modified files against base branch
            cmd = [
                "git",
                "diff",
                "--name-only",
                "--diff-filter=ACMRT",
                f"{base_branch}...HEAD",
            ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Filter for .txt files only
        modified_files = []
        for file in result.stdout.strip().split("\n"):
            if file and file.endswith(".txt"):
                # Check if file is in relevant directories
                if any(
                    file.startswith(dir + "/")
                    for dir in ["common", "events", "history"]
                ):
                    if os.path.exists(file):
                        modified_files.append(file)

        return modified_files
    except subprocess.CalledProcessError as e:
        print(f"Error getting git diff: {e}")
        return []


def check_basic_style(filepath):
    bad_count_file = 0

    with open(filepath, "r", encoding="utf-8", errors="ignore") as file:
        content = file.read()

        # Store all brackets we find in this file, so we can validate everything on the end
        brackets_list = []
        indent_List = []

        # To check if we are in a comment block.
        checkIfInComment = False
        # Used in case we are in a line comment (//)
        ignoreTillEndOfLine = False
        # Used in case we are in a comment block (/* */). This is true if we detect a * inside a comment block.
        # If the next character is a /, it means we end our comment block.
        checkIfNextIsClosingBlock = False

        lastIsCurlyBrace = False

        # Extra information so we know what line we find errors at
        lineNumber = 1

        indexOfCharacter = 0

        for c in content:
            if lastIsCurlyBrace:
                lastIsCurlyBrace = False
            if c == "\n":  # Keeping track of our line numbers
                lineNumber += 1  # so we can print accurate line number information when we detect a possible error
            if c != " ":
                indent_List = []
            # if we are not in a comment block, we will check if we are at the start of one or count the () {} and []
            elif checkIfInComment == False:
                if (
                    ignoreTillEndOfLine
                ):  # we are in a line comment, just continue going through the characters until we find an end of line
                    if c == "\n":
                        ignoreTillEndOfLine = False
                else:  # validate brackets
                    if c == "#":
                        ignoreTillEndOfLine = True
                    elif c == "(":
                        brackets_list.append("(")
                    elif c == ")":
                        if len(brackets_list) > 0 and brackets_list[-1] in ["{", "["]:
                            print(
                                "ERROR: Possible missing round bracket ')' detected at {0} Line number: {1}".format(
                                    clean_filepath(filepath), lineNumber
                                )
                            )
                            bad_count_file += 1
                        brackets_list.append(")")
                    elif c == "[":
                        brackets_list.append("[")
                    elif c == "]":
                        if len(brackets_list) > 0 and brackets_list[-1] in ["{", "("]:
                            print(
                                "ERROR: Possible missing square bracket ']' detected at {0} Line number: {1}".format(
                                    clean_filepath(filepath), lineNumber
                                )
                            )
                            bad_count_file += 1
                        brackets_list.append("]")
                    elif c == "{":
                        brackets_list.append("{")
                    elif c == "}":
                        lastIsCurlyBrace = True
                        if len(brackets_list) > 0 and brackets_list[-1] in ["(", "["]:
                            print(
                                "ERROR: Possible missing curly brace '}}' detected at {0} Line number: {1}".format(
                                    clean_filepath(filepath), lineNumber
                                )
                            )
                            bad_count_file += 1
                        brackets_list.append("}")

                    elif c == " ":  # checking indent
                        indent_List.append("space")
                        if len(indent_List) == 4:
                            print(
                                "ERROR: spaces indent (4) detected instead of tab at {0} Line number: {1}".format(
                                    clean_filepath(filepath), lineNumber
                                )
                            )
                            bad_count_file += 1

            indexOfCharacter += 1

        if brackets_list.count("[") != brackets_list.count("]"):
            print(
                "ERROR: A possible missing square bracket [ or ] in file {0} [ = {1} ] = {2}".format(
                    clean_filepath(filepath),
                    brackets_list.count("["),
                    brackets_list.count("]"),
                )
            )
            bad_count_file += 1
        if brackets_list.count("(") != brackets_list.count(")"):
            print(
                "ERROR: A possible missing round bracket ( or ) in file {0} ( = {1} ) = {2}".format(
                    clean_filepath(filepath),
                    brackets_list.count("("),
                    brackets_list.count(")"),
                )
            )
            bad_count_file += 1
        if brackets_list.count("{") != brackets_list.count("}"):
            print(
                "ERROR: A possible missing curly brace {{ or }} in file {0} {{ = {1} }} = {2}".format(
                    clean_filepath(filepath),
                    brackets_list.count("{"),
                    brackets_list.count("}"),
                )
            )
            bad_count_file += 1

    return bad_count_file


def get_all_files(rootDir):
    """Get all .txt files from relevant directories"""
    files_list = []

    for directory in ["common", "events", "history"]:
        dir_path = os.path.join(rootDir, directory)
        if os.path.exists(dir_path):
            for root, dirnames, filenames in os.walk(dir_path):
                for filename in fnmatch.filter(filenames, "*.txt"):
                    files_list.append(os.path.join(root, filename))

    return files_list


def main():
    parser = argparse.ArgumentParser(
        description="Validate Basic Style for HOI4 mod files"
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
        "--files", nargs="+", help="Specific files to check (overrides mode)"
    )

    args = parser.parse_args()

    print(f"Validating Basic Style (Mode: {args.mode})")

    files_list = []
    bad_count = 0

    # Allow running from root directory as well as from inside the tools directory
    scriptDir = os.path.realpath(__file__)
    rootDir = os.path.dirname(os.path.dirname(scriptDir))

    # Determine which files to check
    if args.files:
        # If specific files are provided, use those
        files_list = args.files
        print(f"Checking specified files: {len(files_list)} files")
    elif args.mode == "diff":
        # Check only modified files against base branch
        files_list = get_git_diff_files(base_branch=args.base_branch, staged_only=False)
        if not files_list:
            print("No modified .txt files found in git diff")
            return 0
        print(
            f"Checking modified files against {args.base_branch}: {len(files_list)} files"
        )
    elif args.mode == "staged":
        # Check only staged files
        files_list = get_git_diff_files(staged_only=True)
        if not files_list:
            print("No staged .txt files found")
            return 0
        print(f"Checking staged files: {len(files_list)} files")
    else:
        # Default: check all files
        files_list = get_all_files(rootDir)
        print(f"Checking all files: {len(files_list)} files")

    # Check each file
    for filename in files_list:
        if os.path.exists(filename):
            bad_count = bad_count + check_basic_style(filename)
        else:
            print(f"WARNING: File not found: {filename}")

    # Print summary
    print(
        "------\nChecked {0} files\nErrors detected: {1}".format(
            len(files_list), bad_count
        )
    )
    if bad_count == 0:
        print("File validation PASSED")
    else:
        print("File validation FAILED")

    return bad_count


if __name__ == "__main__":
    sys.exit(main())
