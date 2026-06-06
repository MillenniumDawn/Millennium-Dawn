#!/usr/bin/env python3
# Author(s): AngriestBird, Hiddengearz
#
# Basic style checks for HOI4 mod .txt files. Merged from the former
# check_basic_style.py + check_basic_style_2.py — one file, one invocation.
#
# Errors (fail the run):
#   - 4-space indent instead of a tab
#   - unbalanced () / [] / {} counts in a file
#   - a closing bracket whose nearest opener is a different type
#   - running brace depth going negative (a stray closing brace)
# Warnings (reported, do not fail):
#   - missing space around an open/close brace
#   - missing / doubled space around an '=' sign
#   - an odd number of quotation marks on a line
#
# Curly-brace balance is also checked, more accurately, by check_braces.py in
# the structural-lint job; the counts here are a cheap first pass. The
# cross-type bracket heuristic is noisy for HOI4 (which barely uses () / []) and
# is a candidate for removal if it proves to add no signal.
import re
import sys

from path_utils import clean_filepath
from shared_utils import (
    Timer,
    collect_files_by_mode,
    create_linting_parser,
    get_root_dir,
    print_timing_summary,
    run_with_pool,
)

__version__ = 2.0

_RE_COMMENT_BRACE = re.compile(r"#.*[{}]+", re.M | re.I)
_RE_NO_SP_OPEN = re.compile(r"([^\s]+)\{|\{([^\s]+)", re.M | re.I)
_RE_NO_SP_CLOSE = re.compile(r"([^\s]+)\}|\}([^\s]+)", re.M | re.I)
_RE_COMMENT_QUOTE = re.compile(r'#.*["]+', re.M | re.I)


def _check_brackets_and_indent(filepath):
    """Bracket-balance, cross-type, and 4-space-indent checks. Returns an
    error count. Comment-aware (skips from '#' to end of line)."""
    bad_count_file = 0

    with open(filepath, "r", encoding="utf-8", errors="replace") as file:
        content = file.read()

        count_open_paren = 0
        count_close_paren = 0
        count_open_square = 0
        count_close_square = 0
        count_open_curly = 0
        count_close_curly = 0
        last_open_bracket = None
        indent_count = 0

        ignoreTillEndOfLine = False
        lineNumber = 1

        for c in content:
            if c == "\n":
                lineNumber += 1
                ignoreTillEndOfLine = False
                indent_count = 0
                continue
            if c != " ":
                indent_count = 0
            if ignoreTillEndOfLine:
                continue
            if c == "#":
                ignoreTillEndOfLine = True
            elif c == "(":
                count_open_paren += 1
                last_open_bracket = "("
            elif c == ")":
                if last_open_bracket in ("{", "["):
                    print(
                        "ERROR: Possible missing round bracket ')' detected at {0} Line number: {1}".format(
                            clean_filepath(filepath), lineNumber
                        )
                    )
                    bad_count_file += 1
                count_close_paren += 1
                last_open_bracket = ")"
            elif c == "[":
                count_open_square += 1
                last_open_bracket = "["
            elif c == "]":
                if last_open_bracket in ("{", "("):
                    print(
                        "ERROR: Possible missing square bracket ']' detected at {0} Line number: {1}".format(
                            clean_filepath(filepath), lineNumber
                        )
                    )
                    bad_count_file += 1
                count_close_square += 1
                last_open_bracket = "]"
            elif c == "{":
                count_open_curly += 1
                last_open_bracket = "{"
            elif c == "}":
                if last_open_bracket in ("(", "["):
                    print(
                        "ERROR: Possible missing curly brace '}}' detected at {0} Line number: {1}".format(
                            clean_filepath(filepath), lineNumber
                        )
                    )
                    bad_count_file += 1
                count_close_curly += 1
                last_open_bracket = "}"
            elif c == " ":
                indent_count += 1
                if indent_count == 4:
                    print(
                        "ERROR: spaces indent (4) detected instead of tab at {0} Line number: {1}".format(
                            clean_filepath(filepath), lineNumber
                        )
                    )
                    bad_count_file += 1

        if count_open_square != count_close_square:
            print(
                "ERROR: A possible missing square bracket [ or ] in file {0} [ = {1} ] = {2}".format(
                    clean_filepath(filepath),
                    count_open_square,
                    count_close_square,
                )
            )
            bad_count_file += 1
        if count_open_paren != count_close_paren:
            print(
                "ERROR: A possible missing round bracket ( or ) in file {0} ( = {1} ) = {2}".format(
                    clean_filepath(filepath),
                    count_open_paren,
                    count_close_paren,
                )
            )
            bad_count_file += 1
        if count_open_curly != count_close_curly:
            print(
                "ERROR: A possible missing curly brace {{ or }} in file {0} {{ = {1} }} = {2}".format(
                    clean_filepath(filepath),
                    count_open_curly,
                    count_close_curly,
                )
            )
            bad_count_file += 1

    return bad_count_file


def _check_spacing_and_braces(filepath):
    """Brace/equal-sign spacing, quote-parity, and running-brace-depth checks.
    Returns (error_count, warning_count)."""
    error_count = 0
    warning_count = 0
    with open(filepath, "r", encoding="utf-8", errors="replace") as file:
        content = file.readlines()
        lineNum = 0
        openBraces = [0, 0]

        for line in content:
            lineNum += 1
            if not line.startswith("#"):
                if "{" in line:
                    hasComment = _RE_COMMENT_BRACE.search(line)
                    if not hasComment:
                        openBraces[0] += line.count("{")
                        # Subtract braces already styled correctly so the slow regex below only runs for the rest
                        closingBraces = (
                            line.count("{") - line.count(" {\n") - line.count(" { ")
                        )

                        if closingBraces > 0:
                            hasNoSpace = _RE_NO_SP_OPEN.search(line)
                            if hasNoSpace:
                                print(
                                    "WARNING: Missing a space before or after open brace at {0} Line number: {1}".format(
                                        clean_filepath(filepath), lineNum
                                    )
                                )
                                warning_count += 1
                if "}" in line:
                    hasComment = _RE_COMMENT_BRACE.search(line)
                    if not hasComment:
                        openBraces[0] += -line.count("}")
                        # Subtract braces already styled correctly so the slow regex below only runs for the rest
                        openingBraces = (
                            line.count("}") - line.count(" }\n") - line.count(" } ")
                        )

                        if openingBraces > 0:
                            hasNoSpace = _RE_NO_SP_CLOSE.search(line)
                            if hasNoSpace:
                                print(
                                    "WARNING: Missing a space before or after close brace at {0} Line number: {1}".format(
                                        clean_filepath(filepath), lineNum
                                    )
                                )
                                warning_count += 1
                if '"' in line:
                    if (line.count('"') % 2) != 0:
                        hasComment = _RE_COMMENT_QUOTE.search(line)
                        if not hasComment:
                            print(
                                "WARNING: Missing a quotation sign at {0} Line number: {1}".format(
                                    clean_filepath(filepath), lineNum
                                )
                            )
                            warning_count += 1

                if "=" in line:
                    equalSign = 0
                    # Count only the equal signs not already correctly spaced
                    equalSign = line.count("=") - line.count(" = ") - line.count(" =\n")

                    if (line.count("  =") > 0) or (line.count("=  ") > 0):
                        print(
                            "WARNING: Two spaces before or after an equal sign at {0} Line number: {1}".format(
                                clean_filepath(filepath), lineNum
                            )
                        )
                        equalSign = equalSign - line.count("  =") - line.count("=  ")
                        warning_count += 1
                    if equalSign != 0:
                        print(
                            "WARNING: Missing a space before or after an equal sign at {0} Line number: {1}".format(
                                clean_filepath(filepath), lineNum
                            )
                        )
                        warning_count += 1
                if "    " in line:
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


def check_basic_style(filepath):
    """Run both style passes over a file. Returns (error_count, warning_count)."""
    errors = _check_brackets_and_indent(filepath)
    extra_errors, warnings = _check_spacing_and_braces(filepath)
    return (errors + extra_errors, warnings)


def main():
    parser = create_linting_parser("Validate Basic Style for HOI4 mod files")
    args = parser.parse_args()

    timings = []
    print(f"Validating Basic Style (Mode: {args.mode})")

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
    if bad_count == 0:
        print("File validation PASSED")
    else:
        print("File validation FAILED")
    print_timing_summary(timings)

    return bad_count


if __name__ == "__main__":
    sys.exit(main())
