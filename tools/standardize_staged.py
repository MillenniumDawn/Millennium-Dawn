#!/usr/bin/env python3

"""
Pre-commit hook wrapper for Millennium Dawn standardizers.

Routes staged files to the correct standardizer based on path:
  - common/national_focus/*.txt  -> standardize_focus_tree()
  - events/*.txt                 -> EventStandardizer
  - common/decisions/*.txt       -> DecisionStandardizer
  - common/ideas/*.txt           -> IdeaStandardizer

Returns exit code 1 if any files were modified (pre-commit auto-fixer convention).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "standardization"))

from standardize_decisions import DecisionStandardizer
from standardize_events import EventStandardizer
from standardize_focus_tree import standardize_focus_tree
from standardize_ideas import IdeaStandardizer


def get_standardizer(filepath):
    """Return (type, standardizer_or_func) for a file, or None if no match."""
    if filepath.startswith("common/national_focus/") and filepath.endswith(".txt"):
        return "focus"
    if filepath.startswith("events/") and filepath.endswith(".txt"):
        return "event"
    if filepath.startswith("common/decisions/") and filepath.endswith(".txt"):
        return "decision"
    if filepath.startswith("common/ideas/") and filepath.endswith(".txt"):
        return "idea"
    return None


def standardize_file(filepath, file_type):
    """Run the appropriate standardizer on a file. Returns True if file was modified."""
    with open(filepath, "r", encoding="utf-8") as f:
        original = f.read()

    if file_type == "focus":
        standardize_focus_tree(filepath, filepath, verbose=False)
    else:
        cls = {
            "event": EventStandardizer,
            "decision": DecisionStandardizer,
            "idea": IdeaStandardizer,
        }[file_type]
        standardizer = cls(verbose=False)
        standardizer.standardize_file(filepath, filepath)

    with open(filepath, "r", encoding="utf-8") as f:
        updated = f.read()

    return updated != original


def main():
    filenames = sys.argv[1:]
    if not filenames:
        return 0

    modified = []
    skipped = 0
    errors = []

    for filepath in filenames:
        if not os.path.exists(filepath):
            continue

        file_type = get_standardizer(filepath)
        if file_type is None:
            skipped += 1
            continue

        try:
            if standardize_file(filepath, file_type):
                modified.append(filepath)
        except Exception as e:
            errors.append(f"  {filepath}: {e}")

    if modified:
        print(f"Standardized {len(modified)} file(s):")
        for f in modified:
            print(f"  {f}")

    if errors:
        print(f"\n{len(errors)} error(s):")
        for e in errors:
            print(e)

    # Exit 1 if any files were modified (pre-commit convention for auto-fixers)
    return 1 if modified else 0


if __name__ == "__main__":
    sys.exit(main())
