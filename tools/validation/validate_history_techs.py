#!/usr/bin/env python3
##########################
# History Technology Dependency Validation Script
# Validates that country history files include prerequisite technologies
# when granting technologies via set_technology blocks, and that equipment
# variant designs only use modules the country has unlocked.
#
# Checks:
#   1. Builds a tech dependency graph from common/technologies/*.txt
#   2. For each history/countries/*.txt, extracts set_technology blocks
#   3. Verifies all transitive prerequisites are present
#   4. Handles DLC if/else branches correctly
#   5. Builds a module -> enabling-tech map from enable_equipment_modules blocks
#   6. Verifies every module used in a create_equipment_variant is enabled by
#      a technology the country has in any DLC branch (BBA and NSB content
#      is interwoven — an NSB variant may use modules from BBA techs)
##########################
import glob
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import disk_cache
from validator_common import BaseValidator, Colors, run_validator_main, strip_comments


def parse_tech_dependencies(mod_path: str) -> Tuple[Dict, Set, Dict]:
    """Build the tech prerequisite graph and the module -> enabling-tech map.

    A tech B has prerequisite A if A contains `path = { leads_to_tech = B }`.
    Multiple techs can lead to the same tech; any one satisfies the prerequisite.

    A module M is enabled by tech A if A contains M inside an
    `enable_equipment_modules = { ... }` block. Multiple techs can enable the
    same module; any one satisfies the requirement.
    """
    tech_dir = os.path.join(mod_path, "common", "technologies")
    prerequisites = defaultdict(set)  # tech -> set of techs that lead to it
    all_techs = set()
    module_techs = defaultdict(set)  # module -> set of techs that enable it

    for filepath in glob.iglob(os.path.join(tech_dir, "*.txt")):
        try:
            with open(filepath, "r", encoding="utf-8-sig") as f:
                content = f.read()
        except Exception:
            continue

        content = strip_comments(content)
        _parse_tech_file(content, prerequisites, all_techs, module_techs)

    return prerequisites, all_techs, module_techs


def _parse_tech_file(
    content: str,
    prerequisites: Dict[str, Set[str]],
    all_techs: Set[str],
    module_techs: Optional[Dict[str, Set[str]]] = None,
):
    """Parse a single tech file to extract tech definitions, their paths, and
    the modules each tech enables."""
    lines = content.split("\n")
    i = 0
    brace_depth = 0
    in_technologies_block = False
    current_tech = None
    tech_brace_depth = 0
    in_enable = False
    enable_brace_depth = 0

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

        for ch in line:
            if ch == "{":
                brace_depth += 1
            elif ch == "}":
                brace_depth -= 1

        if brace_depth <= 0:
            break

        # At depth 1: tech definitions. Variable assignments like @1965 = 0
        # are filtered out by requiring a `= {` block opener at depth >= 2.
        if current_tech is None:
            match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\{", line)
            if match and brace_depth >= 2:
                current_tech = match.group(1)
                tech_brace_depth = brace_depth
                all_techs.add(current_tech)
        else:
            leads_match = re.match(r"leads_to_tech\s*=\s*(\S+)", line)
            if leads_match:
                target = leads_match.group(1)
                prerequisites[target].add(current_tech)

            if module_techs is not None:
                if in_enable:
                    if brace_depth >= enable_brace_depth:
                        mod_match = re.match(
                            r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*$", line.strip()
                        )
                        if mod_match:
                            module_techs[mod_match.group(1)].add(current_tech)
                    if brace_depth < enable_brace_depth:
                        in_enable = False
                if not in_enable and re.match(
                    r"^enable_equipment_modules\s*=\s*\{", line
                ):
                    in_enable = True
                    enable_brace_depth = brace_depth

            if brace_depth < tech_brace_depth:
                current_tech = None
                in_enable = False

        i += 1


def _parse_history_text(content: str) -> List[Tuple[Set[str], str]]:
    """Parse comment-stripped history text into tech sets with their context."""
    lines = content.split("\n")

    base_techs: Set[str] = set()
    branches: List[Tuple[str, Set[str], Set[str]]] = []

    _parse_history_blocks(lines, base_techs, branches)

    if not branches:
        return [(base_techs, "unconditional")]

    tech_sets: List[Tuple[Set[str], str]] = []
    _build_tech_sets(base_techs, branches, 0, set(), "", tech_sets)

    return tech_sets


def parse_history_file(filepath: str, mod_path: str) -> List[Tuple[Set[str], str]]:
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
    return disk_cache.per_file_cached_by_content(
        mod_path,
        "history_techs.history_parse",
        filepath,
        content,
        lambda: _parse_history_text(content),
    )


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

    _build_tech_sets(
        base_techs,
        branches,
        branch_idx + 1,
        accumulated | if_techs,
        f"{label}{sep}{condition}",
        results,
    )

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

        if re.match(r"^set_technology\s*=\s*\{", line):
            techs, i = _extract_tech_block(lines, i)
            base_techs.update(techs)
            continue

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

    block_text = "\n".join(block_lines)

    condition = None
    dlc_match = re.search(r'has_dlc\s*=\s*"([^"]+)"', block_text)
    if dlc_match:
        condition = dlc_match.group(1)

    not_dlc_match = re.search(r'NOT\s*=\s*\{[^}]*has_dlc\s*=\s*"([^"]+)"', block_text)
    if not_dlc_match and not dlc_match:
        condition = not_dlc_match.group(1)

    if not condition:
        # Non-DLC conditional (e.g. a tag check): treat its techs as base techs.
        all_techs = set()
        for line in block_lines:
            tech_match = re.match(r"\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*1\s*$", line)
            if tech_match:
                name = tech_match.group(1)
                if name not in ("limit", "factor", "base", "always"):
                    all_techs.add(name)
        return None, all_techs, set(), i

    if_techs = set()
    else_techs = set()

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

        if re.match(r"else\s*=\s*\{", stripped):
            in_if_body = False
            continue

        if re.match(r"set_technology\s*=\s*\{", stripped):
            continue

        tech_match = re.match(r"\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*1\s*$", line)
        if tech_match:
            name = tech_match.group(1)
            if name not in ("limit", "factor", "base", "always"):
                if in_if_body:
                    if_techs.add(name)
                else:
                    else_techs.add(name)

    # NOT { has_dlc } gates run the if-body when the DLC is absent, so swap the
    # branches to keep if_techs aligned with "DLC present".
    limit_match = re.search(r"limit\s*=\s*\{(.*?)\}", block_text, re.DOTALL)
    if limit_match:
        limit_content = limit_match.group(1)
        if "NOT" in limit_content and "has_dlc" in limit_content:
            if_techs, else_techs = else_techs, if_techs

    return condition, if_techs, else_techs, i


def _match_brace_end(text: str, pos: int) -> int:
    """Given pos pointing just past an opening `{`, return the index just past
    its matching `}`. Returns len(text) if the braces never balance."""
    depth = 1
    j = pos
    while j < len(text) and depth > 0:
        ch = text[j]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        j += 1
    return j


def _find_dlc_if_blocks(content: str) -> List[Tuple[int, int, str]]:
    """Return (start, end, dlc_name) for every positive `has_dlc` if-block.

    `start`/`end` bracket the whole `if = { ... }` span. Only the if-block's
    own `limit` is inspected, so a nested DLC if does not mistag its parent,
    and negated (`NOT = { has_dlc }`) gates are skipped.
    """
    blocks = []
    for m in re.finditer(r"\bif\s*=\s*\{", content):
        end = _match_brace_end(content, m.end())
        inner = content[m.end() : end - 1]
        limit = re.search(r"\blimit\s*=\s*\{(.*?)\}", inner, re.DOTALL)
        if not limit:
            continue
        region = limit.group(1)
        if "NOT" in region:
            continue
        dlc = re.search(r'has_dlc\s*=\s*"([^"]+)"', region)
        if dlc:
            blocks.append((m.start(), end, dlc.group(1)))
    return blocks


def _parse_variants_text(content: str) -> List[Tuple[str, Set[str], frozenset]]:
    """Parse comment-stripped history text into create_equipment_variant triples."""
    dlc_blocks = _find_dlc_if_blocks(content)

    variants = []
    for m in re.finditer(r"\bcreate_equipment_variant\s*=\s*\{", content):
        start = m.start()
        end = _match_brace_end(content, m.end())
        block = content[m.end() : end - 1]

        name_match = re.search(r'name\s*=\s*"([^"]*)"', block)
        name = name_match.group(1) if name_match else "?"

        modules = set()
        mod_block = re.search(r"\bmodules\s*=\s*\{", block)
        if mod_block:
            mod_end = _match_brace_end(block, mod_block.end())
            mod_inner = block[mod_block.end() : mod_end - 1]
            for entry in re.finditer(
                r"[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*([a-zA-Z_][a-zA-Z0-9_]*)", mod_inner
            ):
                if entry.group(1) != "empty":
                    modules.add(entry.group(1))

        gating = frozenset(dlc for (s, e, dlc) in dlc_blocks if s <= start < e)
        variants.append((name, modules, gating))

    return variants


def parse_equipment_variants(
    filepath: str, mod_path: str
) -> List[Tuple[str, Set[str], frozenset]]:
    """Parse a history file and return every create_equipment_variant as a
    (variant_name, set_of_module_names, dlc_gating) triple.

    Only the modules listed inside the variant's `modules = { ... }` sub-block
    are collected; `upgrades` and other sub-blocks are ignored. The literal
    value `empty` (an unfilled slot) is skipped. Both single-line and
    multi-line `modules` blocks are handled.

    `dlc_gating` is the set of `has_dlc` conditions whose if-block encloses the
    variant — i.e. the DLCs that must be active for the variant to exist.
    """
    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            content = f.read()
    except Exception:
        return []

    content = strip_comments(content)
    return disk_cache.per_file_cached_by_content(
        mod_path,
        "history_techs.variant_parse",
        filepath,
        content,
        lambda: _parse_variants_text(content),
    )


def validate_country_equipment(
    args: Tuple[str, Dict[str, Set[str]], str],
) -> List[str]:
    """Validate that a country's equipment variants only use modules enabled by
    a technology the country has in any DLC branch. Returns error strings.

    DLC branches (NSB, BBA, etc.) contain interwoven content: an NSB-gated
    helicopter variant may use modules whose enabling tech is granted in the
    BBA block. Both DLCs are active simultaneously in normal play, and
    create_equipment_variant bypasses module tech checks anyway, so we
    accept any tech from any branch.
    """
    filepath, module_techs, mod_path = args
    filename = os.path.basename(filepath)

    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            content = f.read()
    except Exception:
        return []
    lines = strip_comments(content).split("\n")

    base_techs: Set[str] = set()
    branches: List[Tuple[str, Set[str], Set[str]]] = []
    _parse_history_blocks(lines, base_techs, branches)

    results = []
    seen = set()
    for name, modules, gating in parse_equipment_variants(filepath, mod_path):
        have = set(base_techs)
        for condition, if_techs, else_techs in branches:
            have |= if_techs | else_techs

        for module in sorted(modules):
            enabling = module_techs.get(module)
            if not enabling:
                continue  # module needs no tech (always available)
            if enabling & have:
                continue  # at least one enabling tech is guaranteed
            key = (name, module)
            if key in seen:
                continue
            seen.add(key)
            techs = sorted(enabling)
            if len(techs) == 1:
                tech_str = techs[0]
            else:
                tech_str = "one of: " + ", ".join(techs)
            results.append(
                f'{filename}: variant "{name}" uses {module} '
                f"without enabling tech {tech_str}"
            )

    return results


def validate_country_file(
    args: Tuple[str, Dict[str, Set[str]], Set[str], str],
) -> List[str]:
    """Validate a single country history file. Returns list of error strings."""
    filepath, prerequisites, all_techs, mod_path = args
    filename = os.path.basename(filepath)

    tech_sets = parse_history_file(filepath, mod_path)
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
            if not any(p in tech_set for p in prereqs):
                missing_prereqs = sorted(prereqs)
                if len(missing_prereqs) == 1:
                    prereq_str = missing_prereqs[0]
                else:
                    prereq_str = "one of: " + ", ".join(missing_prereqs)
                error_contexts[(tech, prereq_str)].append(context)

    # An error present in every DLC combination is a base-tech issue, so report
    # it without a context tag; otherwise tag it with the first context it hit.
    results = []
    for (tech, prereq_str), contexts in sorted(error_contexts.items()):
        if len(contexts) >= total_sets:
            results.append(f"{filename}: {tech} requires {prereq_str}")
        else:
            results.append(f"{filename}: {tech} requires {prereq_str} [{contexts[0]}]")

    return results


class Validator(BaseValidator):
    TITLE = "HISTORY TECHNOLOGY DEPENDENCY VALIDATION"
    STAGED_EXTENSIONS = [".txt"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prerequisites = {}
        self.all_techs = set()
        self.module_techs = {}

    def _build_tech_graph(self):
        """Build the technology dependency graph from tech definition files."""
        self._log_section("Building technology dependency graph...")

        self.prerequisites, self.all_techs, self.module_techs = parse_tech_dependencies(
            self.mod_path
        )

        techs_with_prereqs = len(self.prerequisites)
        self.log(f"  Found {len(self.all_techs)} technology definitions")
        self.log(f"  Found {techs_with_prereqs} technologies with prerequisites")
        self.log(f"  Found {len(self.module_techs)} modules mapped to enabling techs")

    def _get_history_files(self) -> List[str]:
        """Get list of history country files to validate."""
        history_dir = os.path.join(self.mod_path, "history", "countries")
        if self.staged_only:
            if not self.staged_files:
                return []
            return [
                f
                for f in self.staged_files
                if f.endswith(".txt") and "history/countries" in f.replace("\\", "/")
            ]
        return sorted(glob.iglob(os.path.join(history_dir, "*.txt")))

    def validate_tech_dependencies(self):
        """Validate that all history files have correct tech prerequisites."""
        self._log_section("Checking technology dependencies in history files...")

        files = self._get_history_files()
        self.log(f"  Found {len(files)} history files to check")

        args_list = [
            (f, self.prerequisites, self.all_techs, self.mod_path) for f in files
        ]

        all_results = self._pool_map(validate_country_file, args_list, chunksize=20)

        results = []
        for file_results in all_results:
            results.extend(file_results)

        self._report(
            results,
            "✓ All history files have correct technology prerequisites",
            "History files with missing technology prerequisites:",
        )

    def validate_equipment_modules(self):
        """Validate that equipment variants only use unlocked modules."""
        self._log_section("Checking equipment variant module technologies...")

        files = self._get_history_files()
        self.log(f"  Found {len(files)} history files to check")

        args_list = [(f, self.module_techs, self.mod_path) for f in files]

        all_results = self._pool_map(
            validate_country_equipment, args_list, chunksize=20
        )

        results = []
        for file_results in all_results:
            results.extend(file_results)

        self._report(
            results,
            "✓ All equipment variants use unlocked modules",
            "Equipment variants using modules without the enabling technology:",
        )

    def run_validations(self):
        self._build_tech_graph()
        self.validate_tech_dependencies()
        self.validate_equipment_modules()


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate technology dependencies in country history files",
    )
