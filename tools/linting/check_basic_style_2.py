#!/usr/bin/env python3
# Author(s): AngriestBird, Hiddengearz

import os
import re
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from path_utils import clean_filepath
from shared_utils import (
    Timer,
    collect_files_by_mode,
    create_linting_parser,
    get_root_dir,
    print_timing_summary,
    run_with_pool,
)

__version__ = 1.2

_RE_COMMENT_BRACE = re.compile(r"#.*[{}]+", re.M | re.I)
_RE_NO_SP_OPEN = re.compile(r"([^\s]+)\{|\{([^\s]+)", re.M | re.I)
_RE_NO_SP_CLOSE = re.compile(r"([^\s]+)\}|\}([^\s]+)", re.M | re.I)
_RE_COMMENT_QUOTE = re.compile(r'#.*["]+', re.M | re.I)


def check_basic_style(filepath):
    error_count = 0
    warning_count = 0
    with open(filepath, "r", encoding="utf-8", errors="ignore") as file:
        content = file.readlines()
        lineNum = 0
        openBraces = [0, 0]

        for line in content:
            lineNum += 1
            if not line.startswith("#"):  # If the line doesn't start with a comment
                if "{" in line:  # if there is an open brace in this line
                    hasComment = _RE_COMMENT_BRACE.search(
                        line
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
                            hasNoSpace = _RE_NO_SP_OPEN.search(
                                line
                            )  # If no space before or after brace
                            if (
                                hasNoSpace
                            ):  # If regex finds open braces not styled correctly
                                print(
                                    "WARNING: Missing a space before or after open brace at {0} Line number: {1}".format(
                                        clean_filepath(filepath), lineNum
                                    )
                                )
                                warning_count += 1
                if "}" in line:  # if there is an close brace in this line
                    hasComment = _RE_COMMENT_BRACE.search(
                        line
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
                            hasNoSpace = _RE_NO_SP_CLOSE.search(
                                line
                            )  # If no space before or after brace
                            if (
                                hasNoSpace
                            ):  # If regex finds open braces not styled correctly
                                print(
                                    "WARNING: Missing a space before or after close brace at {0} Line number: {1}".format(
                                        clean_filepath(filepath), lineNum
                                    )
                                )
                                warning_count += 1
                if '"' in line:  # if the line has a qoute
                    if (
                        line.count('"') % 2
                    ) != 0:  # if there are an odd number of qoutes on this line
                        hasComment = _RE_COMMENT_QUOTE.search(
                            line
                        )  # If comment at the start or before "
                        if not hasComment:  # if there is no comment before the qoute
                            print(
                                "WARNING: Missing a quotation sign at {0} Line number: {1}".format(
                                    clean_filepath(filepath), lineNum
                                )
                            )
                            warning_count += 1

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
                        warning_count += 1
                    if (
                        equalSign != 0
                    ):  # if there are equal signs that aren't used correctly
                        print(
                            "WARNING: Missing a space before or after an equal sign at {0} Line number: {1}".format(
                                clean_filepath(filepath), lineNum
                            )
                        )
                        warning_count += 1
                if "    " in line:  # if 4 spaces in the line
                    print(
                        "WARNING: spaces indent (4) detected instead of tab at {0} Line number: {1}".format(
                            clean_filepath(filepath), lineNum
                        )
                    )
                    warning_count += 1
                if openBraces[0] <= -1:
                    print(
                        "ERROR: A possible missing curly brace {{ in file {0} {{line {1}}}".format(
                            clean_filepath(filepath), lineNum
                        )
                    )
                    openBraces[0] = 0
                    error_count += 1

    return (error_count, warning_count)


def main():
    parser = create_linting_parser(
        "Validate Basic Style for HOI4 mod files - Secondary Check"
    )
    args = parser.parse_args()

    timings = []
    start_time = time.time()
    print(f"Validating Basic Style - Secondary Check (Mode: {args.mode})")

    with Timer("file collection") as t:
        existing_files = collect_files_by_mode(
            args, get_root_dir(), include_interface=True
        )
    timings.append(("file collection", t.elapsed))

    if not existing_files:
        print("No files to check")
        return 0

    print(f"Checking {len(existing_files)} files...")

    with Timer("checking") as t:
        results = run_with_pool(check_basic_style, existing_files, args.workers)
    timings.append(("checking", t.elapsed))

    bad_count = sum(r[0] for r in results)
    warning_count = sum(r[1] for r in results)

    print(
        f"------\nChecked {len(existing_files)} files\n"
        f"Total Errors detected: {bad_count}\n"
        f"Total Warnings detected: {warning_count}"
    )

    if bad_count == 0 and warning_count <= 4:
        print("File validation PASSED")
    else:
        print("File validation FAILED")

    elapsed = time.time() - start_time
    print(f"Completed in {elapsed:.1f}s")
    print_timing_summary(timings)

    return bad_count


if __name__ == "__main__":
    sys.exit(main())
