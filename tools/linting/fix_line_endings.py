#!/usr/bin/env python3
"""Fix mixed line endings by converting CRLF to LF."""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared_utils import atomic_write_bytes


def fix_line_endings(file_path: Path) -> bool:
    """Return True if the file was modified (CRLF -> LF), False if unchanged."""
    try:
        if not file_path.is_file():
            print(f"SKIP {file_path}: Not a file, skipping")
            return False

        # Binary mode preserves bytes other than the line endings we rewrite
        with open(file_path, "rb") as f:
            original_content = f.read()

        if b"\r\n" not in original_content:
            print(f"OK {file_path}: Already has Unix line endings")
            return False

        fixed_content = original_content.replace(b"\r\n", b"\n")

        atomic_write_bytes(str(file_path), fixed_content)

        print(f"FIXED {file_path}: Fixed mixed line endings (CRLF to LF)")
        return True

    except Exception as e:
        print(f"ERROR {file_path}: Error fixing line endings - {e}", file=sys.stderr)
        return False


def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print("ERROR No files provided", file=sys.stderr)
        return 1

    files = [Path(f) for f in sys.argv[1:]]
    fixed_count = 0
    error_count = 0

    for file_path in files:
        try:
            if fix_line_endings(file_path):
                fixed_count += 1
        except Exception:
            error_count += 1

    # Summary for multiple files
    if len(files) > 1:
        total = len(files)
        unchanged = total - fixed_count - error_count
        print(
            f"\nSummary: {fixed_count} fixed, {unchanged} unchanged, {error_count} errors"
        )

    return 1 if error_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
