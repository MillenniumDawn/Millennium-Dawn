#!/usr/bin/env python3
"""Validate that shipped .txt script files carry no UTF-8 BOM."""

import sys
from pathlib import Path


def validate_txt_file(file_path: Path) -> bool:
    """Return True when file_path does not start with a UTF-8 BOM."""
    try:
        with open(file_path, "rb") as handle:
            head = handle.read(3)
    except FileNotFoundError:
        print(f"{file_path}: File not found", file=sys.stderr)
        return False
    except OSError as e:
        print(f"{file_path}: Unreadable - {e}", file=sys.stderr)
        return False
    if head == b"\xef\xbb\xbf":
        print(
            f"{file_path}: Unexpected UTF-8 BOM (game-script .txt must be plain UTF-8)",
            file=sys.stderr,
        )
        return False
    return True


def main():
    if len(sys.argv) < 2:
        print("No files provided", file=sys.stderr)
        return 1

    files = [Path(f) for f in sys.argv[1:]]
    error_count = 0
    for file_path in files:
        if not validate_txt_file(file_path):
            error_count += 1

    if len(files) > 1:
        print(f"\nSummary: {len(files) - error_count} valid, {error_count} errors")

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
