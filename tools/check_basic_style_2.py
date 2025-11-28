#!/usr/bin/env python3
# Author(s): AngriestBird, Hiddengearz

import argparse
import fnmatch
import logging
import os
import re
import subprocess
import sys
import time

import requests
from path_utils import clean_filepath

startTime = time.time()

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
                    for dir in ["common", "events", "history", "interface"]
                ):
                    if os.path.exists(file):
                        modified_files.append(file)

        return modified_files
    except subprocess.CalledProcessError as e:
        print(f"Error getting git diff: {e}")
        return []


# Function: check_basic_style
# Purpose: Validates files to ensure the basic stylization of MD is ensured.
def check_basic_style(filepath, bad_count, warningErrors, message):
    fixedErrors = 0
    with open(filepath, "r", encoding="utf-8", errors="ignore") as file:
        content = file.readlines()
        lineNum = 0
        openBraces = [0, 0]

        for line in content:
            lineNum += 1
            if not line.startswith("#"):  # If the line doesn't start with a comment
                if "{" in line:  # if there is an open brace in this line
                    hasComment = re.search(
                        r"#.*[{}]+", line, re.M | re.I
                    )  # If comment at the start or before {
                    if (
                        not hasComment
                    ):  # if the line doesn't have a comment before the open brace
                        openBraces[0] += line.count("{")
                        # count total open braces and subtract open braces that are easy to find and used correctly
                        closingBraces = (
                            line.count("{") - line.count(" {\n") - line.count(" { ")
                        )

                        # if there are braces we couldn't find using efficient .count, use powerful inefficient regex
                        if closingBraces > 0:
                            hasNoSpace = re.search(
                                r"([^\s]+){|{([^\s]+)", line, re.M | re.I
                            )  # If no space before or after brace
                            if (
                                hasNoSpace
                            ):  # If regex finds open braces not styled correctly
                                print(
                                    "WARNING: Missing a space before or after open brace at {0} Line number: {1}".format(
                                        clean_filepath(filepath), lineNum
                                    )
                                )
                                warningErrors += 1
                if "}" in line:  # if there is an close brace in this line
                    hasComment = re.search(
                        r"#.*[{}]+", line, re.M | re.I
                    )  # If comment at the start or before {
                    if (
                        not hasComment
                    ):  # if the line doesn't have a comment before the open brace
                        openBraces[0] += -line.count("}")
                        # count total close braces and subtract open braces that are easy to find and used correctly
                        openingBraces = (
                            line.count("}") - line.count(" }\n") - line.count(" } ")
                        )

                        # if there are braces we couldn't find using efficient .count, use powerful inefficient regex
                        if openingBraces > 0:
                            hasNoSpace = re.search(
                                r"([^\s]+)}|}([^\s]+)", line, re.M | re.I
                            )  # If no space before or after brace
                            if (
                                hasNoSpace
                            ):  # If regex finds open braces not styled correctly
                                print(
                                    "WARNING: Missing a space before or after close brace at {0} Line number: {1}".format(
                                        clean_filepath(filepath), lineNum
                                    )
                                )
                                warningErrors += 1
                if '"' in line:  # if the line has a qoute
                    if (
                        line.count('"') % 2
                    ) != 0:  # if there are an odd number of qoutes on this line
                        hasComment = re.search(
                            r"#.*[\"]+", line, re.M | re.I
                        )  # If comment at the start or before "
                        if not hasComment:  # if there is no comment before the qoute
                            print(
                                "WARNING: Missing a quotation sign at {0} Line number: {1}".format(
                                    clean_filepath(filepath), lineNum
                                )
                            )
                            warningErrors += 1

                if "=" in line:  # if the line has an equal sign
                    equalSign = 0
                    # count total equal signs that are easy to find and used correctly
                    equalSign = line.count("=") - line.count(" = ") - line.count(" =\n")

                    if (line.count("  =") > 0) or (line.count("=  ") > 0):
                        print(
                            "WARNING: Two spaces before or after an equal sign at {0} Line number: {1}".format(
                                clean_filepath(filepath), lineNum
                            )
                        )
                        equalSign = equalSign - line.count("  =") - line.count("=  ")
                        warningErrors += 1
                    if (
                        equalSign != 0
                    ):  # if there are equal signs that aren't used correctly
                        print(
                            "WARNING: Missing a space before or after an equal sign at {0} Line number: {1}".format(
                                clean_filepath(filepath), lineNum
                            )
                        )
                        warningErrors += 1
                if "    " in line:  # if 4 spaces in the line
                    print(
                        "WARNING: spaces indent (4) detected instead of tab at {0} Line number: {1}".format(
                            clean_filepath(filepath), lineNum
                        )
                    )
                    warningErrors += 1
                if openBraces[0] <= -1:
                    print(
                        "ERROR: A possible missing curly brace {{ in file {} {{line {1}}}".format(
                            clean_filepath(filepath), lineNum
                        )
                    )
                    openBraces[0] = 0
                    fixedErrors += 1

    file.close()

    return bad_count + fixedErrors, warningErrors, message


def get_all_files(rootDir):
    """Get all .txt files from relevant directories"""
    files_list = []
    directories = ["common", "events", "history", "interface"]

    for directory in directories:
        dir_path = os.path.join(rootDir, directory)
        if os.path.exists(dir_path):
            for root, dirnames, filenames in os.walk(dir_path):
                for filename in fnmatch.filter(filenames, "*.txt"):
                    files_list.append(os.path.join(root, filename))

    return files_list


def main():
    parser = argparse.ArgumentParser(
        description="Validate Basic Style for HOI4 mod files - Secondary Check"
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
        "--no-gitlab",
        action="store_true",
        help="Disable GitLab integration even if environment variables are set",
    )
    parser.add_argument(
        "filenames",
        nargs="*",
        help="Files to check (positional argument for pre-commit)",
    )
    # Keep the private token as a positional argument for backward compatibility
    parser.add_argument(
        "private_token", nargs="?", help="GitLab private token for posting results"
    )

    args = parser.parse_args()

    logging.basicConfig(
        filename="pythontools.log", format="%(asctime)s %(message)s", filemode="w"
    )
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    logger.info(f"Validating Basic Style - Secondary Check (Mode: {args.mode})")
    message = f"Validating Basic Style - Secondary Check (Mode: {args.mode})\n"
    files_list = []
    bad_count = 0
    warningErrors = 0

    # Allow running from root directory as well as from inside the tools directory
    scriptDir = os.path.realpath(__file__)
    rootDir = os.path.dirname(os.path.dirname(scriptDir))

    # Determine which files to check
    if args.filenames:
        # If positional filenames are provided (from pre-commit)
        files_list = args.filenames
        logger.info(f"Checking specified files: {len(files_list)} files")
        print(f"Checking specified files: {len(files_list)} files")
    elif args.mode == "diff":
        # Check only modified files against base branch
        files_list = get_git_diff_files(base_branch=args.base_branch, staged_only=False)
        if not files_list:
            logger.info("No modified .txt files found in git diff")
            print("No modified .txt files found in git diff")
            return 0
        logger.info(
            f"Checking modified files against {args.base_branch}: {len(files_list)} files"
        )
        print(
            f"Checking modified files against {args.base_branch}: {len(files_list)} files"
        )
    elif args.mode == "staged":
        # Check only staged files
        files_list = get_git_diff_files(staged_only=True)
        if not files_list:
            logger.info("No staged .txt files found")
            print("No staged .txt files found")
            return 0
        logger.info(f"Checking staged files: {len(files_list)} files")
        print(f"Checking staged files: {len(files_list)} files")
    else:
        # Default: check all files
        logger.debug("Checking all folders...")
        files_list = get_all_files(rootDir)
        logger.debug("All folders checked...")
        logger.info(f"Checking all files: {len(files_list)} files")
        print(f"Checking all files: {len(files_list)} files")

    # Check each file
    for filename in files_list:
        if os.path.exists(filename):
            try:
                bad_count, warningErrors, message = check_basic_style(
                    filename, bad_count, warningErrors, message
                )
            except:
                print(
                    f"{clean_filepath(filename)} has a potentially broken curly brace or some other fixes..."
                )
                bad_count += 1
        else:
            logger.warning(f"File not found: {filename}")
            print(f"WARNING: File not found: {filename}")

    logger.info(
        "------\nChecked {0} files\nTotal Errors detected: {1}\nTotal Warnings detected: {2}".format(
            len(files_list), bad_count, warningErrors
        )
    )
    message = (
        message
        + "------\nChecked {0} files\nTotal Errors detected: {1}\nTotal Warnings Detected: {2}\n".format(
            len(files_list), bad_count, warningErrors
        )
    )

    if (bad_count == 0) and (warningErrors <= 4):
        logger.info("File validation PASSED")
        message = message + "File validation PASSED\n"
        postResults = False
        print("File validation PASSED")
    else:
        message = (
            message + "File validation FAILED\n Please fix all errors or warnings."
        )
        postResults = True
        print("File validation FAILED")

    logger.info("The script took {0} second!".format(time.time() - startTime))

    # GitLab integration (only if not disabled and environment variables exist)
    if not args.no_gitlab:
        try:
            projectId = os.environ["CI_PROJECT_ID"]
            # Try to get private token from args or fallback to command line argument
            privateToken = (
                args.private_token
                if args.private_token
                else sys.argv[1] if len(sys.argv) > 1 else None
            )

            if privateToken and postResults:
                headers = {"PRIVATE-TOKEN": privateToken}
                payload = {"body": message}

                if "CI_MERGE_REQUEST_IID" in os.environ:
                    mergeRequestId = os.environ["CI_MERGE_REQUEST_IID"]
                    r = requests.post(
                        "https://gitlab.com/api/v4/projects/"
                        + projectId
                        + "/merge_requests/"
                        + mergeRequestId
                        + "/discussions",
                        data=payload,
                        headers=headers,
                    )
                    print("Posted results to merge request")
                else:
                    commitID = os.environ["CI_COMMIT_SHA"]
                    r = requests.post(
                        "https://gitlab.com/api/v4/projects/"
                        + projectId
                        + "/commits/"
                        + commitID
                        + "/discussions",
                        data=payload,
                        headers=headers,
                    )
                    print("Posted results to commit")
            elif not postResults:
                print("File validation passed Coding Standards: SUCCESS")
        except KeyError:
            logger.info("Not in GitLab CI environment, skipping GitLab integration")
        except:
            print("Couldn't post results to gitlab")

    return bad_count


if __name__ == "__main__":
    sys.exit(main())
