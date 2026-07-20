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
        ok = standardize_focus_tree(filepath, filepath, verbose=False)
    else:
        cls = {
            "event": EventStandardizer,
            "decision": DecisionStandardizer,
            "idea": IdeaStandardizer,
        }[file_type]
        standardizer = cls(verbose=False)
        ok = standardizer.standardize_file(filepath, filepath)

    # A False return is a non-raising failure (e.g. a write error left the file
    # unprocessed). Raise so main() logs it as an error and the commit stops
    # rather than proceeding with an unstandardized file.
    if ok is False:
        raise RuntimeError("standardizer reported failure")

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
            import traceback

            errors.append(f"  {filepath}: {e}\n{traceback.format_exc()}")

    if modified:
        print(f"Standardized {len(modified)} file(s):")
        for f in modified:
            print(f"  {f}")

    if errors:
        print(f"\n{len(errors)} error(s):")
        for e in errors:
            print(e)

    # Exit 1 if any files were modified (pre-commit convention for auto-fixers)
    # or if a standardizer crashed — a crash means the file was left
    # unprocessed/corrupt, so the commit must not proceed silently.
    return 1 if (modified or errors) else 0


if __name__ == "__main__":
    sys.exit(main())
