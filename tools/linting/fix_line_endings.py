#!/usr/bin/env python3
"""
Line Ending Normalizer

This script fixes mixed line endings by converting CRLF to LF for consistency
across development platforms.

Usage:
    python fix_line_endings.py [files...]

Arguments:
    files: List of files to normalize line endings for
"""

import os
import sys
from pathlib import Path
from typing import List


def fix_line_endings(file_path: Path) -> bool:
    """
    Fix line endings in a single file by converting CRLF to LF.

    Args:
        file_path: Path to the file to fix

    Returns:
        True if file was modified, False if no changes needed
    """
    try:
        if not file_path.is_file():
            print(f"⚠️  {file_path}: Not a file, skipping")
            return False

        # Read file in binary mode to preserve exact content
        with open(file_path, "rb") as f:
            original_content = f.read()

        # Check if file has CRLF line endings
        if b"\r\n" not in original_content:
            print(f"✅ {file_path}: Already has Unix line endings")
            return False

        # Convert CRLF to LF
        fixed_content = original_content.replace(b"\r\n", b"\n")

        # Write back the fixed content
        with open(file_path, "wb") as f:
            f.write(fixed_content)

        print(f"🔧 {file_path}: Fixed mixed line endings (CRLF → LF)")
        return True

    except Exception as e:
        print(f"❌ {file_path}: Error fixing line endings - {e}", file=sys.stderr)
        return False


def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print("❌ No files provided", file=sys.stderr)
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
