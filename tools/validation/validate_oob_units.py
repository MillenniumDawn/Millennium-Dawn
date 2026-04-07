#!/usr/bin/env python3
##########################
# OOB Unit Name Validation Script
# Validates that unit names used in OOB files and AI templates reference
# canonical sub-unit definitions from common/units/*.txt.
#
# Checks:
#   1. Parses common/units/*.txt to build a set of canonical sub-unit names
#   2. Parses history/units/*.txt to extract unit names from regiments/support blocks
#   3. Parses common/ai_templates/*.txt and common/scripted_effects/00_AI_templates.txt
#   4. Reports any reference not in the canonical set
#   5. Suggests closest case-insensitive match for likely typos
##########################
import glob
import os
import re
from difflib import get_close_matches
from typing import Dict, List, Set, Tuple

from validator_common import BaseValidator, Colors, run_validator_main, strip_comments


def parse_canonical_units(mod_path: str) -> Set[str]:
    """Build a set of canonical sub-unit names from common/units/*.txt.

    Unit names are top-level identifiers inside sub_units = { ... } blocks.
    """
    units_dir = os.path.join(mod_path, "common", "units")
    canonical = set()

    for filepath in glob.iglob(os.path.join(units_dir, "*.txt")):
        try:
            with open(filepath, "r", encoding="utf-8-sig") as f:
                content = f.read()
        except Exception:
            continue

        content = strip_comments(content)
        lines = content.split("\n")
        i = 0
        in_sub_units = False
        brace_depth = 0
        unit_brace_depth = 0
        in_unit_def = False

        while i < len(lines):
            line = lines[i].strip()

            if not in_sub_units:
                if re.match(r"^sub_units\s*=\s*\{", line):
                    in_sub_units = True
                    brace_depth = 1
                    i += 1
                    continue
                i += 1
                continue

            # Count braces on this line
            for ch in line:
                if ch == "{":
                    brace_depth += 1
                elif ch == "}":
                    brace_depth -= 1

            if brace_depth <= 0:
                in_sub_units = False
                i += 1
                continue

            # At depth 1 inside sub_units, look for unit_name = {
            if not in_unit_def:
                match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\{", line)
                if match and brace_depth >= 2:
                    canonical.add(match.group(1))
                    in_unit_def = True
                    unit_brace_depth = brace_depth
            else:
                if brace_depth < unit_brace_depth:
                    in_unit_def = False

            i += 1

    return canonical


def _extract_unit_refs_from_blocks(content: str) -> Set[str]:
    """Extract unit names from regiments = { ... } and support = { ... } blocks.

    Handles two patterns:
      - unit_name = { x = 0 y = 0 }   (OOB / scripted effect style)
      - unit_name = N                   (AI template shorthand)
    """
    refs = set()
    lines = content.split("\n")
    i = 0
    in_block = False
    brace_depth = 0

    while i < len(lines):
        line = lines[i].strip()

        if not in_block:
            if re.match(r"^(regiments|support)\s*=\s*\{", line):
                in_block = True
                brace_depth = 1
                i += 1
                continue
            i += 1
            continue

        for ch in line:
            if ch == "{":
                brace_depth += 1
            elif ch == "}":
                brace_depth -= 1

        if brace_depth <= 0:
            in_block = False
            i += 1
            continue

        # At depth 1 inside the block, match unit references
        # Pattern 1: unit_name = { ... }
        match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\{", line)
        if match:
            refs.add(match.group(1))
            i += 1
            continue

        # Pattern 2: unit_name = N (number)
        match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\d+", line)
        if match:
            refs.add(match.group(1))

        i += 1

    return refs


def validate_oob_file(
    args: Tuple[str, Set[str], Dict[str, str]],
) -> List[str]:
    """Validate a single OOB or AI template file. Returns list of error strings."""
    filepath, canonical, canonical_lower = args
    filename = os.path.basename(filepath)

    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            content = f.read()
    except Exception:
        return []

    content = strip_comments(content)
    refs = _extract_unit_refs_from_blocks(content)

    results = []
    for ref in sorted(refs):
        if ref not in canonical:
            msg = f"{filename}: unknown unit '{ref}'"
            # Suggest closest match (case-insensitive)
            ref_lower = ref.lower()
            if ref_lower in canonical_lower:
                msg += f" (did you mean '{canonical_lower[ref_lower]}'?)"
            else:
                close = get_close_matches(
                    ref_lower, canonical_lower.keys(), n=1, cutoff=0.7
                )
                if close:
                    msg += f" (did you mean '{canonical_lower[close[0]]}'?)"
            results.append(msg)

    return results


class Validator(BaseValidator):
    TITLE = "OOB UNIT NAME VALIDATION"
    STAGED_EXTENSIONS = [".txt"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.canonical = set()
        self.canonical_lower = {}

    def _build_canonical_units(self):
        """Build the canonical unit name set from unit definition files."""
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Building canonical unit name set...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        self.canonical = parse_canonical_units(self.mod_path)
        # Build case-insensitive lookup: lowercase -> original name
        self.canonical_lower = {name.lower(): name for name in self.canonical}

        self.log(f"  Found {len(self.canonical)} canonical sub-unit definitions")

    def _get_files_to_check(self) -> List[str]:
        """Get list of OOB and AI template files to validate."""
        patterns = [
            "history/units/*.txt",
            "common/ai_templates/*.txt",
            "common/scripted_effects/00_AI_templates.txt",
        ]
        return self._collect_files(patterns)

    def validate_unit_references(self):
        """Validate that all unit references match canonical definitions."""
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking unit references in OOB and AI template files...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        files = self._get_files_to_check()
        self.log(f"  Found {len(files)} files to check")

        args_list = [(f, self.canonical, self.canonical_lower) for f in files]

        all_results = self._pool_map(validate_oob_file, args_list, chunksize=20)

        results = []
        for file_results in all_results:
            results.extend(file_results)

        self._report(
            results,
            "✓ All unit references match canonical definitions",
            "Files with unknown unit references:",
        )

    def run_validations(self):
        self._build_canonical_units()
        self.validate_unit_references()


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate unit names in OOB files and AI templates against canonical definitions",
    )
