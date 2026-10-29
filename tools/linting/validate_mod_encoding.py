#!/usr/bin/env python3
"""Validate that .mod files are properly encoded as UTF-8."""

import sys
from pathlib import Path


def validate_mod_file(file_path: Path) -> bool:
    """Return True if file_path is valid UTF-8, False otherwise."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            file.read()
        print(f"{file_path}: Valid UTF-8 encoding")
        return True

    except UnicodeDecodeError as e:
        print(f"{file_path}: Invalid UTF-8 encoding - {e}", file=sys.stderr)
        return False

    except FileNotFoundError:
        print(f"{file_path}: File not found", file=sys.stderr)
        return False

    except Exception as e:
        print(f"{file_path}: Unexpected error - {e}", file=sys.stderr)
        return False


def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print("No files provided", file=sys.stderr)
        return 1

    files = [Path(f) for f in sys.argv[1:]]
    valid_count = 0
    error_count = 0

    for file_path in files:
        if validate_mod_file(file_path):
            valid_count += 1
        else:
            error_count += 1

    # Summary for multiple files
    if len(files) > 1:
        print(f"\nSummary: {valid_count} valid, {error_count} errors")

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
