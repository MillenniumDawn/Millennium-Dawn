#!/usr/bin/env python3
import fnmatch
import os
import re
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from path_utils import clean_filepath
from shared_utils import Timer, get_git_diff_files, print_timing_summary, run_with_pool

__version__ = 1.1

_RE_TAG_LINE = re.compile(r"^[A-Z]{3}", re.M | re.I)
_RE_FOCUS_FORMAT = re.compile(r"^[A-Z]{3}_[a-zA-Z0-9_-]+$", re.M | re.U)
_RE_NEWS_EVENT = re.compile(r"news_event\s*=\s*\{")
_RE_OPTION = re.compile(r"\boption\s*=\s*\{")


def get_tags(rootDir):
    tags = []
    with open(rootDir, "r", encoding="utf-8", errors="ignore") as file:
        content = file.readlines()
        for line in content:
            if (
                not line.startswith("#") and line.strip()
            ):  # If the line doesn't start with a comment or blank
                hasTag = _RE_TAG_LINE.match(line)  # If it's a tag
                if hasTag:
                    tags.append(hasTag.group())
    return tags


# Shared focus tree prefixes that don't follow the standard TAG_ format
SHARED_FOCUS_PREFIXES = [
    "USoE",  # United States of Europe shared tree
    "POTEF",  # EU POTEF shared tree
    "AFRICAN_UNION",  # African Union shared tree
]


def hasFocusFormat(focus_id):
    """Check if focus ID follows the correct format TAG_focus_name"""
    # Allow shared tree prefixes
    for prefix in SHARED_FOCUS_PREFIXES:
        if focus_id.startswith(prefix):
            return True
    return _RE_FOCUS_FORMAT.match(focus_id) is not None


def checkFocuses(filepath):
    warning_count_file = 0
    lineNum = 0
    with open(filepath, "r", encoding="utf-8", errors="ignore") as file:
        content = file.readlines()
        braces = 0
        current_focus_id = ""
        has_search_filters = False
        in_focus_block = False
        in_completion_reward = False
        in_focus_tree = False
        found_focus_id = False

        for line in content:
            lineNum += 1
            if (
                not line.startswith("#") and line.strip()
            ):  # If the line doesn't start with a comment or blank
                depth_before = braces
                if "{" in line:
                    braces += line.count("{")
                if "}" in line:
                    braces -= line.count("}")

                # Track focus_tree blocks (exclude tree-level IDs)
                if "focus_tree" in line and "{" in line:
                    in_focus_tree = True
                elif in_focus_tree and braces == 0:
                    in_focus_tree = False

                # Track completion_reward blocks
                if "completion_reward" in line and "{" in line:
                    in_completion_reward = True
                elif in_completion_reward and braces == 0:
                    in_completion_reward = False

                # Check for search_filters within focus block
                if in_focus_block:
                    if "search_filters" in line:
                        has_search_filters = True

                # Track focus blocks — only match a NEW top-level `focus = {`
                # (depth 0 before the opening brace).  Lines like
                # `prerequisite = { focus = X }` or `has_completed_focus = X`
                # contain the word "focus" but are NOT new focus block openers.
                is_new_focus_block = depth_before == 0 and re.match(
                    r"^\s*focus\s*=\s*\{", line
                )
                if is_new_focus_block:
                    in_focus_block = True
                    found_focus_id = False
                    has_search_filters = False
                elif in_focus_block and braces == 0:
                    # We're exiting the focus block
                    if found_focus_id and not has_search_filters:
                        print(
                            "WARNING: Focus "
                            + current_focus_id
                            + " doesn't have search_filters defined in {0} Line number: {1}".format(
                                clean_filepath(filepath), lineNum
                            )
                        )
                        warning_count_file += 1
                    in_focus_block = False
                    current_focus_id = ""
                    found_focus_id = False

                # Check for focus ID (only first one in focus block, exclude completion_reward and focus_tree)
                if (
                    in_focus_block
                    and not in_completion_reward
                    and not in_focus_tree
                    and not found_focus_id
                    and ("id =" in line or "id=" in line)
                ):
                    hasFocus = re.match(
                        r"[ \t]+id\s?=\s?([A-za-z0-9-?_?]+)", line, re.M | re.I
                    )
                    if hasFocus:
                        current_focus_id = hasFocus.group(1)
                        found_focus_id = True

                        # Check focus format
                        if not hasFocusFormat(current_focus_id):
                            print(
                                "WARNING: "
                                + current_focus_id
                                + " is formatted incorrectly, must be TAG_focus_name in {0} Line number: {1}".format(
                                    clean_filepath(filepath), lineNum
                                )
                            )
                            warning_count_file += 1

    return warning_count_file


def check_ideas(filepath):
    error_count_file = 0
    lineNum = 0
    pdxIdeaCode = [
        "allowed",
        "modifier",
        "country",
        "allowed_civil_war",
        "OR",
        "AND",
        "ideas",
        "NOT",
        "CANCEL",
        "on_add",
        "available",
        "ai_will_do",
        "rule",
        "do_effect",
    ]

    pdxIdeaCode = [element.lower() for element in pdxIdeaCode]
    with open(filepath, "r", encoding="utf-8", errors="ignore") as file:
        content = file.readlines()
        braces = 0
        for line in content:
            lineNum += 1
            if (
                not line.startswith("#") and line.strip()
            ):  # If the line doesn't start with a comment or blank
                if "{" in line:
                    braces += 1
                if braces == 3:
                    hasIdea = re.search(
                        r"([A-Za-z0-9_-]+)\s?=\s?{", line, re.M | re.I
                    )  # If it's a tag
                    if hasIdea:
                        countryIdea = re.search(
                            r"([A-Z]{3}_[a-z0-9_-]+)\s?=\s?{", line, re.M
                        )  # If it's a tag
                        # if countryIdea:
                        # print(countryIdea.group(1))
                        # input()
                        genericIdea = re.search(
                            r"([a-z0-9_-]+)\s?=\s?{", line, re.M
                        )  # If it's a tag
                        if not countryIdea and not genericIdea:
                            print(
                                "ERROR: "
                                + hasIdea.group(1)
                                + " is formatted incorrectly, must be TAG_idea_name or generic_idea_name {0} Line number: {1}".format(
                                    clean_filepath(filepath), lineNum
                                )
                            )
                            error_count_file += 1
                            # print(hasFocus.group(1))
                            # print("wrong: " + hasIdea.group(1))
                if "}" in line:
                    braces -= 1

    return error_count_file


def check_event_for_logs(filepath):
    warning_count_file = 0
    lineNum = 0
    hasLog = 0
    optionFound = 0
    optionName = ""
    hasOtherDefinitions = 0
    inNewsEvent = False
    eventBraces = 0

    with open(filepath, "r", encoding="utf-8", errors="ignore") as file:
        content = file.readlines()
        braces = 0
        for line in content:
            lineNum += 1
            if (
                not line.startswith("#") and line.strip()
            ):  # If the line doesn't start with a comment or blank
                # Track news_event blocks to skip them
                stripped = line.strip()
                if _RE_NEWS_EVENT.match(stripped):
                    inNewsEvent = True
                    eventBraces = 1
                elif inNewsEvent:
                    eventBraces += line.count("{")
                    eventBraces -= line.count("}")
                    if eventBraces <= 0:
                        inNewsEvent = False
                        eventBraces = 0
                    continue
                if inNewsEvent:
                    continue
                if _RE_OPTION.search(line):
                    optionFound = 1
                    optionLine = lineNum
                    optionName = ""
                    hasLog = 0
                    hasOtherDefinitions = 0
                if optionFound == 1:
                    if "name" in line and "=" in line:
                        hasName = re.search(
                            r"name\s?=\s([a-zA-Z0-9-_.]+)", line, re.M | re.I
                        )  # If it's a tag
                        if hasName:
                            optionName = hasName.group(1)
                    elif (
                        "=" in line
                        and braces > 0
                        and "name" not in line
                        and "log" not in line
                    ):
                        # Check for other definitions besides name and log
                        hasOtherDefinitions = 1
                    if "{" in line:
                        braces += line.count("{")

                    if braces > 0 and hasLog == 0 and "log" in line:
                        hasLog = 1
                        optionFound = 0
                        braces = 0
                    if "}" in line:
                        braces -= line.count("}")
                    if (
                        braces == 0
                        and hasLog == 0
                        and hasOtherDefinitions == 1
                        and optionName
                    ):
                        print(
                            "WARNING: Event option "
                            + optionName
                            + " has effects but no log in {0} Line number: {1}".format(
                                clean_filepath(filepath), optionLine
                            )
                        )
                        optionFound = 0
                        braces = 0
                        hasLog = 0
                        hasOtherDefinitions = 0
                        warning_count_file += 1
                    elif braces == 0:
                        # Reset for next option
                        optionFound = 0
                        braces = 0
                        hasLog = 0
                        hasOtherDefinitions = 0

    return warning_count_file


def check_Flags(filepath):
    error_count_file = 0
    lineNum = 0

    with open(filepath, "r", encoding="utf-8", errors="ignore") as file:
        content = file.readlines()
        advFlag = 0
        isGlobalFlag = 0
        countryFlags = []
        globalFlags = []
        for line in content:
            lineNum += 1
            if (
                not line.startswith("#") and line.strip()
            ):  # If the line doesn't start with a comment or blank
                if (
                    "set_country_flag" in line
                    or "has_country_flag" in line
                    or "set_global_flag" in line
                    or "has_global_flag" in line
                ):
                    # print("here: " + filepath + str(lineNum))
                    if advFlag == 0:
                        hasSimpleFlag = re.search(
                            r"[a-z_]+_flag\s?=\s?([A-Za-z0-9-_]+)", line, re.M
                        )  # If it's a tag
                        hasAdvFlag = re.search(
                            r"[a-z_]+_flag\s?=\s?{", line, re.M | re.I
                        )  # If it's a tag
                        if hasAdvFlag:
                            advFlag = 1
                            if "global_flag" in line:
                                isGlobalFlag = 1
                            # print("Test: " + str(lineNum))
                        elif hasSimpleFlag:
                            simpleFlagFormat = re.search(
                                r"([a-z_]+_flag\s?=\s?)([A-Z0-9]{1}([a-z0-9]+)?_[A-Z0-9]{1}([a-z0-9]+)?)(_[A-Z0-9]{1}([a-z0-9]+)?)?(_[A-Z0-9]{1}([a-z0-9]+)?)?(_[A-Z0-9]{1}([a-z0-9]+)?)?(_[A-Z0-9]{1}([a-z0-9]+)?)?(_[A-Z0-9]{1}([a-z0-9]+)?)?$",
                                line,
                                re.M | re.I,
                            )
                            if not simpleFlagFormat:
                                print(
                                    "ERROR: "
                                    + hasSimpleFlag.group(1)
                                    + " is formatted incorrectly, must be The_Flags_Name in {0} Line number: {1}".format(
                                        clean_filepath(filepath), lineNum
                                    )
                                )
                                error_count_file += 1
                            else:
                                if "global_flag" in line:
                                    globalFlags.append(hasSimpleFlag.group(1))
                                else:
                                    countryFlags.append(hasSimpleFlag.group(1))

                if advFlag == 1 and ("flag=" in line or "flag =" in line):
                    hasAdvFlag2 = re.search(
                        r"flag\s?=\s([a-zA-Z0-9\-\_]+)", line, re.M
                    )  # If it's a tag
                    # print("Test2: " + str(lineNum))
                    if hasAdvFlag2:
                        advFlag = 0
                        # print("Test3: " + str(lineNum))
                        advFlagFormat = re.search(
                            r"flag\s?=\s?(([A-Z0-9]{1}([a-z0-9]+)?_[A-Z0-9]{1}([a-z0-9]+)?)(_[A-Z0-9]{1}([a-z0-9]+)?)?(_[A-Z0-9]{1}([a-z0-9]+)?)?(_[A-Z0-9]{1}([a-z0-9]+)?)?(_[A-Z0-9]{1}([a-z0-9]+)?)?(_[A-Z0-9]{1}([a-z0-9]+)?)?$)",
                            line,
                            re.M,
                        )
                        if not advFlagFormat:
                            print(
                                "ERROR: "
                                + hasAdvFlag2.group(1)
                                + " is formatted incorrectly, must be The_Flags_Name {0} Line number: {1}".format(
                                    clean_filepath(filepath), lineNum
                                )
                            )
                            error_count_file += 1
                        else:
                            if isGlobalFlag == 1:
                                globalFlags.append(hasAdvFlag2.group(1))
                                isGlobalFlag = 0
                            else:
                                countryFlags.append(hasAdvFlag2.group(1))
    return error_count_file, globalFlags, countryFlags


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate Coding Standards for HOI4 mod files"
    )
    parser.add_argument(
        "--mode",
        choices=["all", "staged"],
        default="all",
        help="Check mode: all files or staged files only (default: all)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=max(1, min(os.cpu_count() or 2, 4)),
        help="Number of parallel workers (default: min(CPU count, 4))",
    )
    args = parser.parse_args()

    timings = []
    start_time = time.time()
    print(f"Validating Coding Standards (Mode: {args.mode})")

    scriptDir = os.path.realpath(__file__)
    rootDir = os.path.dirname(os.path.dirname(os.path.dirname(scriptDir)))

    with Timer("file collection") as t:
        staged_files = None
        if args.mode == "staged":
            staged_files = set(
                os.path.abspath(f) for f in get_git_diff_files(staged_only=True)
            )
            if not staged_files:
                print("No staged .txt files found")
                return 0

        focus_files = []
        for root, dirnames, filenames in os.walk(
            os.path.join(rootDir, "common", "national_focus")
        ):
            for filename in fnmatch.filter(filenames, "*.txt"):
                if filename != "generic.txt":
                    filepath = os.path.join(root, filename)
                    if (
                        staged_files is None
                        or os.path.abspath(filepath) in staged_files
                    ):
                        focus_files.append(filepath)

        event_files = []
        for root, dirnames, filenames in os.walk(os.path.join(rootDir, "events")):
            for filename in fnmatch.filter(filenames, "*.txt"):
                filepath = os.path.join(root, filename)
                if staged_files is None or os.path.abspath(filepath) in staged_files:
                    event_files.append(filepath)
    timings.append(("file collection", t.elapsed))

    with Timer("focus checks") as t:
        focus_results = run_with_pool(checkFocuses, focus_files, args.workers)
    timings.append(("focus checks", t.elapsed))

    with Timer("event log checks") as t:
        event_results = run_with_pool(check_event_for_logs, event_files, args.workers)
    timings.append(("event log checks", t.elapsed))

    warning_count = sum(focus_results) + sum(event_results)
    total_files = len(focus_files) + len(event_files)

    print(
        f"------\nChecked {total_files} files\n"
        f"Warnings detected: {warning_count}\nTotal issues: {warning_count}"
    )

    if warning_count == 0:
        print("File validation PASSED")
    else:
        print("File validation PASSED WITH WARNINGS")

    elapsed = time.time() - start_time
    print(f"Completed in {elapsed:.1f}s")
    print_timing_summary(timings)

    return 0


if __name__ == "__main__":
    sys.exit(main())
