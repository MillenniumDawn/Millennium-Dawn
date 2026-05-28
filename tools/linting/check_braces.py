#!/usr/bin/env python3
"""
Check for missing or mismatched braces in HOI4 mod files.
This script validates that all opening braces { have matching closing braces }.
"""

import sys
from pathlib import Path


def check_braces(file_path):
    """
    Check if braces are properly matched in a file.

    Returns:
        tuple: (is_valid, errors) where is_valid is bool and errors is list of error messages
    """
    errors = []

    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            return False, [f"Error reading file: {e}"]
    except Exception as e:
        return False, [f"Error reading file: {e}"]

    brace_stack = []
    line_num = 1
    col_num = 1

    in_comment = False
    in_string = False

    for i, char in enumerate(content):
        if char == "\n":
            in_string = False
            line_num += 1
            col_num = 1
            in_comment = False
            continue

        col_num += 1

        if char == '"':
            if not in_comment:
                in_string = not in_string
            continue

        if in_string or in_comment:
            continue

        if char == "#":
            in_comment = True
            continue

        if char == "{":
            brace_stack.append((line_num, col_num))
        elif char == "}":
            if not brace_stack:
                errors.append(
                    f"Line {line_num}, Column {col_num}: Closing brace '}}' without matching opening brace"
                )
            else:
                brace_stack.pop()

    if brace_stack:
        for line, col in brace_stack:
            errors.append(
                f"Line {line}, Column {col}: Opening brace '{{' without matching closing brace"
            )

    return len(errors) == 0, errors


def main():
    """Main entry point for the brace checker."""
    if len(sys.argv) < 2:
        print("Usage: check_braces.py <file1> [file2] ...", file=sys.stderr)
        sys.exit(1)

    has_errors = False

    for file_path in sys.argv[1:]:
        path = Path(file_path)

        if not path.exists():
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            has_errors = True
            continue

        is_valid, errors = check_braces(file_path)

        if not is_valid:
            has_errors = True
            print(f"\n{file_path}:", file=sys.stderr)
            for error in errors:
                print(f"  {error}", file=sys.stderr)

    if has_errors:
        print(
            "\n❌ Brace validation failed! Please fix the issues above.",
            file=sys.stderr,
        )
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
