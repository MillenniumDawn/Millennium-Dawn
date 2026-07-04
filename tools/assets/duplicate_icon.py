#!/usr/bin/env python3
"""
Duplicate Icon Checker

This script checks a focus file for all of its icon definitions to find any icon defined more than once in a given focus file.
You must run the script from the tools directory.

Usage:
    python duplicate_icon.py [files...]

Arguments:
    file: focus tree file name

Example:
    python3 duplicate_icon.py turkey.txt
"""

import sys

file = f"../common/national_focus/{sys.argv[1]}"

with open(file) as f:
    seen = set()
    count = 0
    for line in f:
        line_lower = line.lower()
        if line_lower in seen:
            if "icon" in line_lower:
                count = count + 1
                print(line)
        else:
            seen.add(line_lower)

print(f"{sys.argv[1]} has {count} duplicate icons. Review the above list.")
