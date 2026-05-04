#!/usr/bin/env python3
import os
import sys

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


def check_basic_style(filepath):
    bad_count_file = 0

    with open(filepath, "r", encoding="utf-8", errors="ignore") as file:
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


def main():
    parser = create_linting_parser("Validate Basic Style for HOI4 mod files")
    args = parser.parse_args()

    timings = []
    print(f"Validating Basic Style (Mode: {args.mode})")

    with Timer("file collection") as t:
        existing_files = collect_files_by_mode(args, get_root_dir())
    timings.append(("file collection", t.elapsed))

    if not existing_files:
        print("No files to check")
        return 0

    print(f"Checking {len(existing_files)} files...")

    with Timer("checking") as t:
        results = run_with_pool(check_basic_style, existing_files, args.workers)
    timings.append(("checking", t.elapsed))
    bad_count = sum(results)

    print(f"------\nChecked {len(existing_files)} files\nErrors detected: {bad_count}")
    if bad_count == 0:
        print("File validation PASSED")
    else:
        print("File validation FAILED")
    print_timing_summary(timings)

    return bad_count


if __name__ == "__main__":
    sys.exit(main())
