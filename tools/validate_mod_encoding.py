#!/usr/bin/env python3
"""
HOI4 Mod File UTF-8 Encoding Validator

This script validates that .mod files are properly encoded as UTF-8.

Usage:
    python validate_mod_encoding.py [files...]

Arguments:
    files: List of .mod files to check
"""

import sys
from pathlib import Path


def validate_mod_file(file_path: Path) -> bool:
    """
    Validate a single .mod file for UTF-8 encoding.

    Args:
        file_path: Path to the .mod file to validate

    Returns:
        True if file is valid UTF-8, False otherwise
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            file.read()
        print(f"✅ {file_path}: Valid UTF-8 encoding")
        return True

    except UnicodeDecodeError as e:
        print(f"❌ {file_path}: Invalid UTF-8 encoding - {e}", file=sys.stderr)
        return False

    except FileNotFoundError:
        print(f"❌ {file_path}: File not found", file=sys.stderr)
        return False

    except Exception as e:
        print(f"❌ {file_path}: Unexpected error - {e}", file=sys.stderr)
        return False


def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print("❌ No files provided", file=sys.stderr)
        return 1

    files = [Path(f) for f in sys.argv[1:]]
    all_valid = True

    for file_path in files:
        if not validate_mod_file(file_path):
            all_valid = False

    # Summary for multiple files
    if len(files) > 1:
        valid_count = sum(1 for f in files if f.suffix == ".mod")
        error_count = len(files) - valid_count if not all_valid else 0
        print(f"\nSummary: {valid_count - error_count} valid, {error_count} errors")

    return 0 if all_valid else 1


if __name__ == "__main__":
    sys.exit(main())
