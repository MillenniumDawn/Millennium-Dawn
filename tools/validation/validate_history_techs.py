#!/usr/bin/env python3
##########################
# History Technology Dependency Validation Script
# Validates that country history files include prerequisite technologies
# when granting technologies via set_technology blocks.
#
# Checks:
#   1. Builds a tech dependency graph from common/technologies/*.txt
#   2. For each history/countries/*.txt, extracts set_technology blocks
#   3. Verifies all transitive prerequisites are present
#   4. Handles DLC if/else branches correctly
##########################
import glob
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from validator_common import BaseValidator, Colors, run_validator_main, strip_comments


def parse_tech_dependencies(mod_path: str) -> Dict[str, Set[str]]:
    """Build a map of tech -> set of prerequisite techs.

    A tech B has prerequisite A if A contains `path = { leads_to_tech = B }`.
    Multiple techs can lead to the same tech; any one satisfies the prerequisite.
    """
    tech_dir = os.path.join(mod_path, "common", "technologies")
    prerequisites = defaultdict(set)  # tech -> set of techs that lead to it
    all_techs = set()

    for filepath in glob.iglob(os.path.join(tech_dir, "*.txt")):
        try:
            with open(filepath, "r", encoding="utf-8-sig") as f:
                content = f.read()
        except Exception:
            continue

        content = strip_comments(content)
        _parse_tech_file(content, prerequisites, all_techs)

    return prerequisites, all_techs


def _parse_tech_file(
    content: str,
    prerequisites: Dict[str, Set[str]],
    all_techs: Set[str],
):
    """Parse a single tech file to extract tech definitions and their paths."""
    # Find the technologies = { ... } wrapper
    # Then find each tech definition inside it
    lines = content.split("\n")
    i = 0
    brace_depth = 0
    in_technologies_block = False
    current_tech = None
    tech_brace_depth = 0

    while i < len(lines):
        line = lines[i].strip()

        if not in_technologies_block:
            if re.match(r"^technologies\s*=\s*\{", line):
                in_technologies_block = True
                brace_depth = 1
                i += 1
                continue
            i += 1
            continue

        # Count braces
        for ch in line:
            if ch == "{":
                brace_depth += 1
            elif ch == "}":
                brace_depth -= 1

        if brace_depth <= 0:
            break

        # At depth 1, we're looking for tech definitions
        # Skip variable assignments like @1965 = 0
        if current_tech is None:
            # Look for tech_name = { at the top level of technologies block
            match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\{", line)
            if match and brace_depth >= 2:
                current_tech = match.group(1)
                tech_brace_depth = brace_depth
                all_techs.add(current_tech)
        else:
            # Inside a tech definition, look for leads_to_tech
            leads_match = re.match(r"leads_to_tech\s*=\s*(\S+)", line)
            if leads_match:
                target = leads_match.group(1)
                prerequisites[target].add(current_tech)

            # Check if we've exited this tech's block
            if brace_depth < tech_brace_depth:
                current_tech = None

        i += 1


def parse_history_file(filepath: str) -> List[Tuple[Set[str], str]]:
    """Parse a history file and return tech sets with their context.

    Returns a list of (tech_set, context_label) where context_label
    describes the DLC branch (for error reporting).

    Each returned tech_set represents one possible effective set of
    technologies a country could have, depending on which DLCs are active.
    """
    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            content = f.read()
    except Exception:
        return []

    content = strip_comments(content)
    lines = content.split("\n")

    # We need to track:
    # - Base techs (unconditional set_technology blocks)
    # - DLC branch techs (set_technology inside if/else blocks)
    #
    # Strategy: parse the brace structure to identify set_technology blocks
    # and their enclosing if/else context.

    base_techs = set()
    branches = []  # list of (condition_label, if_techs, else_techs)

    _parse_history_blocks(lines, base_techs, branches)

    # Build effective tech sets for each DLC combination
    if not branches:
        return [(base_techs, "unconditional")]

    # Each branch is independent (NSB, BBA, LaR, AAT, etc.)
    # We need to check each combination, but typically branches are independent
    # So we check: base + each branch's if-path, and base + each branch's else-path
    tech_sets = []
    _build_tech_sets(base_techs, branches, 0, set(), "", tech_sets)

    return tech_sets


def _build_tech_sets(
    base_techs: Set[str],
    branches: List[Tuple[str, Set[str], Set[str]]],
    branch_idx: int,
    accumulated: Set[str],
    label: str,
    results: List[Tuple[Set[str], str]],
):
    """Recursively build all possible tech set combinations from DLC branches."""
    if branch_idx >= len(branches):
        final_set = base_techs | accumulated
        results.append((final_set, label if label else "unconditional"))
        return

    condition, if_techs, else_techs = branches[branch_idx]
    sep = " + " if label else ""

    # Path where DLC condition is true
    _build_tech_sets(
        base_techs,
        branches,
        branch_idx + 1,
        accumulated | if_techs,
        f"{label}{sep}{condition}",
        results,
    )

    # Path where DLC condition is false
    _build_tech_sets(
        base_techs,
        branches,
        branch_idx + 1,
        accumulated | else_techs,
        f"{label}{sep}NOT {condition}",
        results,
    )


def _parse_history_blocks(
    lines: List[str],
    base_techs: Set[str],
    branches: List[Tuple[str, Set[str], Set[str]]],
):
    """Parse history file lines to extract tech blocks and their DLC context."""
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Look for unconditional set_technology blocks
        if re.match(r"^set_technology\s*=\s*\{", line):
            techs, i = _extract_tech_block(lines, i)
            base_techs.update(techs)
            continue

        # Look for if blocks that might contain set_technology
        if_match = re.match(r"^if\s*=\s*\{", line)
        if if_match:
            condition, if_techs, else_techs, i = _parse_if_block(lines, i)
            if condition and (if_techs or else_techs):
                branches.append((condition, if_techs, else_techs))
            continue

        i += 1


def _extract_tech_block(lines: List[str], start: int) -> Tuple[Set[str], int]:
    """Extract tech names from a set_technology = { ... } block."""
    techs = set()
    brace_depth = 0
    i = start

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        for ch in stripped:
            if ch == "{":
                brace_depth += 1
            elif ch == "}":
                brace_depth -= 1

        # Look for tech assignments: tech_name = 1
        tech_match = re.match(r"\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*1\s*$", line)
        if tech_match and brace_depth >= 1:
            techs.add(tech_match.group(1))

        i += 1

        if brace_depth <= 0:
            break

    return techs, i


def _parse_if_block(
    lines: List[str], start: int
) -> Tuple[Optional[str], Set[str], Set[str], int]:
    """Parse an if = { ... else = { ... } } block.

    Returns (condition_label, if_techs, else_techs, next_line_index).
    """
    # First, extract the entire if block
    brace_depth = 0
    i = start
    block_lines = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        block_lines.append(line)

        for ch in stripped:
            if ch == "{":
                brace_depth += 1
            elif ch == "}":
                brace_depth -= 1

        i += 1

        if brace_depth <= 0:
            break

    # Now parse the block content
    block_text = "\n".join(block_lines)

    # Extract condition (DLC check)
    condition = None
    dlc_match = re.search(r'has_dlc\s*=\s*"([^"]+)"', block_text)
    if dlc_match:
        condition = dlc_match.group(1)

    # Check if condition is negated (NOT { has_dlc = "..." })
    not_dlc_match = re.search(r'NOT\s*=\s*\{[^}]*has_dlc\s*=\s*"([^"]+)"', block_text)
    if not_dlc_match and not dlc_match:
        condition = not_dlc_match.group(1)

    if not condition:
        # Not a DLC conditional - treat all techs as base techs
        # (could be other conditions like tag checks)
        all_techs = set()
        for line in block_lines:
            tech_match = re.match(r"\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*1\s*$", line)
            if tech_match:
                name = tech_match.group(1)
                # Filter out non-tech assignments
                if name not in ("limit", "factor", "base", "always"):
                    all_techs.add(name)
        return None, all_techs, set(), i

    # Split into if-body and else-body
    if_techs = set()
    else_techs = set()

    # Find the else = { boundary
    in_if_body = True
    inner_brace = 0
    found_limit_end = False

    for line in block_lines:
        stripped = line.strip()

        # Track when we pass the limit block
        if not found_limit_end:
            if "limit" in stripped:
                found_limit_end = False
            for ch in stripped:
                if ch == "{":
                    inner_brace += 1
                elif ch == "}":
                    inner_brace -= 1
            # After processing the limit block (depth returns to 1)
            if inner_brace <= 1 and "}" in stripped and not found_limit_end:
                found_limit_end = True
            continue

        # Check for else = {
        if re.match(r"else\s*=\s*\{", stripped):
            in_if_body = False
            continue

        # Check for set_technology blocks
        if re.match(r"set_technology\s*=\s*\{", stripped):
            # We'll collect techs from this sub-block
            continue

        tech_match = re.match(r"\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*1\s*$", line)
        if tech_match:
            name = tech_match.group(1)
            if name not in ("limit", "factor", "base", "always"):
                if in_if_body:
                    if_techs.add(name)
                else:
                    else_techs.add(name)

    # Handle negated conditions: if NOT { has_dlc = "..." }, swap branches
    # Extract the limit block content to check for negation
    limit_match = re.search(r"limit\s*=\s*\{(.*?)\}", block_text, re.DOTALL)
    if limit_match:
        limit_content = limit_match.group(1)
        if "NOT" in limit_content and "has_dlc" in limit_content:
            # The condition is negated - the if-body runs when DLC is NOT present
            if_techs, else_techs = else_techs, if_techs

    return condition, if_techs, else_techs, i


def validate_country_file(
    args: Tuple[str, Dict[str, Set[str]], Set[str]],
) -> List[str]:
    """Validate a single country history file. Returns list of error strings."""
    filepath, prerequisites, all_techs = args
    filename = os.path.basename(filepath)

    tech_sets = parse_history_file(filepath)
    total_sets = len(tech_sets)

    # Track which (tech, prereq_str) errors appear in which contexts
    error_contexts = defaultdict(list)  # (tech, prereq_str) -> [context, ...]

    for tech_set, context in tech_sets:
        for tech in sorted(tech_set):
            if tech not in all_techs:
                continue  # Unknown tech, skip (could be from a DLC we don't parse)

            if tech not in prerequisites:
                continue  # Root tech, no prerequisites needed

            prereqs = prerequisites[tech]
            # At least one prerequisite must be present
            if not any(p in tech_set for p in prereqs):
                missing_prereqs = sorted(prereqs)
                if len(missing_prereqs) == 1:
                    prereq_str = missing_prereqs[0]
                else:
                    prereq_str = "one of: " + ", ".join(missing_prereqs)
                error_contexts[(tech, prereq_str)].append(context)

    # Deduplicate: if error appears in ALL DLC combinations, report without context
    results = []
    for (tech, prereq_str), contexts in sorted(error_contexts.items()):
        if len(contexts) >= total_sets:
            # Error exists in all combinations - it's a base tech issue
            results.append(f"{filename}: {tech} requires {prereq_str}")
        else:
            # Error only in specific DLC combinations - report the simplest context
            # Deduplicate identical error messages
            results.append(f"{filename}: {tech} requires {prereq_str} [{contexts[0]}]")

    return results


class Validator(BaseValidator):
    TITLE = "HISTORY TECHNOLOGY DEPENDENCY VALIDATION"
    STAGED_EXTENSIONS = [".txt"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prerequisites = {}
        self.all_techs = set()

    def _build_tech_graph(self):
        """Build the technology dependency graph from tech definition files."""
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Building technology dependency graph...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        self.prerequisites, self.all_techs = parse_tech_dependencies(self.mod_path)

        # Count techs with prerequisites
        techs_with_prereqs = len(self.prerequisites)
        self.log(f"  Found {len(self.all_techs)} technology definitions")
        self.log(f"  Found {techs_with_prereqs} technologies with prerequisites")

    def _get_history_files(self) -> List[str]:
        """Get list of history country files to validate."""
        history_dir = os.path.join(self.mod_path, "history", "countries")
        if self.staged_files:
            return [
                f
                for f in self.staged_files
                if f.endswith(".txt") and "history/countries" in f.replace("\\", "/")
            ]
        return sorted(glob.iglob(os.path.join(history_dir, "*.txt")))

    def validate_tech_dependencies(self):
        """Validate that all history files have correct tech prerequisites."""
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking technology dependencies in history files...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        files = self._get_history_files()
        self.log(f"  Found {len(files)} history files to check")

        args_list = [(f, self.prerequisites, self.all_techs) for f in files]

        all_results = self._pool_map(validate_country_file, args_list, chunksize=20)

        results = []
        for file_results in all_results:
            results.extend(file_results)

        self._report(
            results,
            "✓ All history files have correct technology prerequisites",
            "History files with missing technology prerequisites:",
        )

    def run_validations(self):
        self._build_tech_graph()
        self.validate_tech_dependencies()


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate technology dependencies in country history files",
    )
