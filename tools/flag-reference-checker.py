#!/usr/bin/env python3

import os
import re
import sys
from collections import defaultdict


def find_flags(content):
    """Extract all flags from set_country_flag syntax patterns."""
    flags = set()

    flags.update(re.findall(r"set_country_flag\s*=\s*([A-Za-z0-9_]+)", content))

    # Only match the bare `flag = X` form when the file uses set_country_flag,
    # to avoid catching unrelated `flag = ...` assignments.
    if "set_country_flag" in content:
        flags.update(re.findall(r"flag\s*=\s*([A-Za-z0-9_]+)", content))

    return flags


def should_skip(root, filename):
    """Check if file should be skipped."""
    if filename.startswith("."):
        return True

    root_lower = root.lower()

    # gfx holds binary assets, not flag-bearing script
    if "gfx" in root_lower.split(os.sep):
        return True

    if "localisation" in root_lower or "localization" in root_lower:
        if filename.endswith((".yml", ".yaml", ".csv")):
            return True

    return False


def scan_directory(search_dir):
    """Scan directory once, collecting all flags and their locations."""
    file_contents = {}  # filepath -> content
    all_flags = set()
    files_processed = 0

    print("Reading files...", end="", flush=True)

    for root, dirs, files in os.walk(search_dir):
        # Remove hidden, localisation, and gfx directories
        dirs[:] = [
            d
            for d in dirs
            if not d.startswith(".")
            and d.lower() not in ["localisation", "localization", "gfx"]
        ]

        for filename in files:
            if should_skip(root, filename):
                continue

            filepath = os.path.join(root, filename)

            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    file_contents[filepath] = content

                    flags = find_flags(content)
                    all_flags.update(flags)

                    files_processed += 1
                    if files_processed % 100 == 0:
                        print(".", end="", flush=True)

            except (IOError, OSError):
                continue

    print(f" Done! ({files_processed} files)\n")

    # Count references by scanning each file once, not each flag once (faster)
    print("Analyzing flag references...")
    flag_references = defaultdict(lambda: defaultdict(int))

    flags_processed = 0
    for filepath, content in file_contents.items():
        for flag in all_flags:
            if flag in content:
                flag_references[flag][filepath] = content.count(flag)

        flags_processed += 1
        if flags_processed % 50 == 0:
            print(
                f"\r  Processed {flags_processed}/{len(file_contents)} files...",
                end="",
                flush=True,
            )

    print(f"\r  Processed {flags_processed}/{len(file_contents)} files... Done!\n")

    return all_flags, flag_references


def main():
    if len(sys.argv) != 2:
        print("Usage: python flag-reference-checker.py <directory>")
        sys.exit(1)

    search_dir = sys.argv[1]

    if not os.path.isdir(search_dir):
        print(f"Error: Directory '{search_dir}' does not exist")
        sys.exit(1)

    print(f"Scanning for flags in: {search_dir}")
    print("=" * 60 + "\n")

    all_flags, flag_references = scan_directory(search_dir)

    print(f"Found {len(all_flags)} unique flags\n")

    # Sort flags alphabetically
    for flag in sorted(all_flags):
        print(f"Flag: {flag}")
        print("-" * 60)

        refs = flag_references.get(flag, {})

        if not refs:
            print("  ⚠ Not referenced anywhere")
        else:
            print(f"  Referenced in {len(refs)} file(s):")
            for filepath, count in sorted(refs.items()):
                print(f"    - {filepath} ({count} occurrence(s))")

        print()

    print("=" * 60)
    print("Scan complete!")


if __name__ == "__main__":
    main()
