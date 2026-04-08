#!/usr/bin/env python3
"""
Duplicate Icon Checker

This script checks a focus file for all of it's icon definitions to see if there is an icon that is defined multiple times in a given focus file.
The current state of the script you need to be in the tools directory.

Usage:
    python duplicate_icon.py [files...]

Arguments:
    file: focus tree file name

Example:
    python3 duplicate_icon.py turkey.txt
"""

import os
import shutil
import sys
from tokenize import Ignore

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
