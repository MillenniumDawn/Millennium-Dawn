#!/usr/bin/env python3
##########################
# OOB Unit Name Validation Script
# Validates that unit names used in OOB files, AI templates, and namelists
# reference canonical sub-unit definitions from common/units/*.txt.
#
# Checks:
#   1. Parses common/units/*.txt to build a set of canonical sub-unit names
#   2. Parses history/units/*.txt to extract unit names from regiments/support blocks
#   3. Parses common/ai_templates/*.txt and common/scripted_effects/00_AI_templates.txt
#   4. Parses common/units/names/00_*_names.txt block keys (legacy namelist schema)
#   5. Parses common/units/names_ships/*.txt ship_types arrays (modern namelist schema)
#   6. Reports any reference not in the canonical set
#   7. Suggests closest case-insensitive match for likely typos
#
# Note: namelist blocks accept both sub_unit names AND equipment-type names
# (used by air namelists like small_plane_airframe). The canonical set for
# namelist validation extends the sub_unit set with equipment names extracted
# from `need = { ... }` blocks inside sub_unit definitions.
##########################
import glob
import os
import re
from difflib import get_close_matches
from typing import Dict, List, Set, Tuple

from validator_common import (
    BaseValidator,
    Colors,
    Severity,
    run_validator_main,
    strip_comments,
)


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


def parse_canonical_namelist_keys(mod_path: str, sub_units: Set[str]) -> Set[str]:
    """Return the set of valid namelist block keys.

    A namelist block key is valid if it is either:
      - a sub_unit name, OR
      - an equipment-type name referenced in `need = { ... }` or
        `need_equipment = { ... }` inside a sub_unit definition.

    Air namelists use equipment-type keys (small_plane_airframe etc.) rather
    than sub_unit names (light_fighter etc.), so the canonical set must
    include both.
    """
    valid = set(sub_units)
    units_dir = os.path.join(mod_path, "common", "units")

    for filepath in glob.iglob(os.path.join(units_dir, "*.txt")):
        try:
            with open(filepath, "r", encoding="utf-8-sig") as f:
                content = f.read()
        except Exception:
            continue
        content = strip_comments(content)

        # Find each `need = { ... }` or `need_equipment = { ... }` block and
        # extract `key = N` entries inside it. These are equipment-type names.
        for match in re.finditer(
            r"\b(?:need|need_equipment)\s*=\s*\{([^{}]*)\}", content
        ):
            for entry in re.finditer(
                r"([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\d+", match.group(1)
            ):
                valid.add(entry.group(1))

    return valid


def _extract_namelist_block_keys(content: str) -> Set[str]:
    """Extract block keys at depth 2 in a 00_TAG_names.txt file.

    The schema is `TAG = { key1 = { ... } key2 = { ... } ... }` where each
    inner key names a sub_unit or equipment type. Assignment-style entries
    like `air_wing_names_template = AIR_WING_NAME_FOO` are skipped (no `{`).
    """
    refs = set()
    lines = content.split("\n")
    brace_depth = 0

    for raw in lines:
        line = raw.strip()
        depth_at_line_start = brace_depth

        for ch in raw:
            if ch == "{":
                brace_depth += 1
            elif ch == "}":
                brace_depth -= 1

        # Block keys live at depth 1 (inside the TAG = { ... } wrapper).
        # The wrapper itself is at depth 0 → 1 on its opening brace.
        if depth_at_line_start != 1:
            continue

        match = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\{", line)
        if match:
            refs.add(match.group(1))

    return refs


def _extract_ship_types_tokens(content: str) -> Set[str]:
    """Extract tokens from `ship_types = { ... }` arrays in *_ship_names.txt."""
    refs = set()
    for match in re.finditer(r"ship_types\s*=\s*\{([^{}]*)\}", content):
        for tok in re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", match.group(1)):
            refs.add(tok)
    return refs


def _extract_division_types_tokens(content: str) -> Set[str]:
    """Extract quoted-string tokens from `division_types = { "Foo" "Bar" }` arrays.

    Used by *_names_divisions.txt files. Tokens are quoted (unlike ship_types,
    which uses bare identifiers).
    """
    refs = set()
    for match in re.finditer(r"division_types\s*=\s*\{([^{}]*)\}", content):
        for tok in re.findall(r'"([^"]+)"', match.group(1)):
            refs.add(tok)
    return refs


def _extract_division_group_keys(content: str) -> Set[str]:
    """Extract top-level group keys defined in a *_names_divisions.txt file.

    The schema is `GROUP_NAME = { name = ... for_countries = ... ... }` at the
    top level (depth 0 → 1 on the opening brace). Handles both same-line
    (`KEY = {`) and split-line (`KEY =\\n{`) brace styles.
    """
    refs = set()

    # Find every `KEY = {` (allowing whitespace/newlines between `=` and `{`)
    # then verify the match starts at depth 0.
    for match in re.finditer(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\{", content):
        prefix = content[: match.start()]
        depth = prefix.count("{") - prefix.count("}")
        if depth == 0:
            refs.add(match.group(1))

    return refs


def parse_division_group_keys(mod_path: str) -> Set[str]:
    """Return the set of all division_names_group keys defined across the mod."""
    keys = set()
    pattern = os.path.join(mod_path, "common", "units", "names_divisions", "*.txt")
    for filepath in glob.iglob(pattern):
        try:
            with open(filepath, "r", encoding="utf-8-sig") as f:
                content = f.read()
        except OSError:
            continue
        keys |= _extract_division_group_keys(strip_comments(content))
    return keys


def _extract_division_names_group_refs(content: str) -> List[Tuple[str, int]]:
    """Find `division_names_group = X` references with their 1-based line numbers."""
    refs = []
    for ln, line in enumerate(content.split("\n"), 1):
        match = re.search(r"division_names_group\s*=\s*([A-Za-z_][A-Za-z0-9_]*)", line)
        if match:
            refs.append((match.group(1), ln))
    return refs


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

        # Depth at the START of this line — unit references live at depth 1
        # (direct children of the regiments/support block). Deeper lines
        # (e.g. position `x = 0` / `y = 0` inside `unit_name = { ... }`) must
        # be skipped.
        depth_at_line_start = brace_depth

        for ch in line:
            if ch == "{":
                brace_depth += 1
            elif ch == "}":
                brace_depth -= 1

        if brace_depth <= 0:
            in_block = False
            i += 1
            continue

        if depth_at_line_start != 1:
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


def _suggest_match(ref: str, canonical_lower: Dict[str, str]) -> str:
    """Return a ' (did you mean ...?)' suffix for a ref, or empty string."""
    ref_lower = ref.lower()
    if ref_lower in canonical_lower:
        return f" (did you mean '{canonical_lower[ref_lower]}'?)"
    close = get_close_matches(ref_lower, canonical_lower.keys(), n=1, cutoff=0.7)
    if close:
        return f" (did you mean '{canonical_lower[close[0]]}'?)"
    return ""


def _check_refs(
    refs: Set[str],
    canonical: Set[str],
    canonical_lower: Dict[str, str],
    filename: str,
    label: str,
) -> List[str]:
    """Return error strings for refs that aren't in the canonical set."""
    results = []
    for ref in sorted(refs):
        if ref in canonical:
            continue
        msg = f"{filename}: unknown {label} '{ref}'" + _suggest_match(
            ref, canonical_lower
        )
        results.append(msg)
    return results


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
    return _check_refs(refs, canonical, canonical_lower, filename, "unit")


def validate_namelist_file(
    args: Tuple[str, Set[str], Dict[str, str]],
) -> List[str]:
    """Validate a single namelist file. Returns list of error strings.

    Handles two schemas:
      - 00_TAG_names.txt: block keys at depth 2 inside `TAG = { ... }`
      - *_ship_names.txt: tokens inside `ship_types = { ... }` arrays
    """
    filepath, canonical, canonical_lower = args
    filename = os.path.basename(filepath)

    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            content = f.read()
    except Exception:
        return []

    content = strip_comments(content)
    parent = os.path.basename(os.path.dirname(filepath))

    if parent == "names":
        refs = _extract_namelist_block_keys(content)
        label = "namelist block key"
    elif parent == "names_ships":
        refs = _extract_ship_types_tokens(content)
        label = "ship_types token"
    elif parent == "names_divisions":
        refs = _extract_division_types_tokens(content)
        label = "division_types token"
    else:
        return []

    return _check_refs(refs, canonical, canonical_lower, filename, label)


def validate_oob_division_groups_file(
    args: Tuple[str, Set[str], Dict[str, str]],
) -> List[str]:
    """Check that every `division_names_group = X` ref points to a real group."""
    filepath, group_keys, group_keys_lower = args
    filename = os.path.basename(filepath)

    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            content = f.read()
    except OSError:
        return []

    content = strip_comments(content)
    results = []
    for ref, line_no in _extract_division_names_group_refs(content):
        if ref in group_keys:
            continue
        msg = (
            f"{filename}:{line_no}: unknown division_names_group '{ref}'"
            + _suggest_match(ref, group_keys_lower)
        )
        results.append(msg)
    return results


class Validator(BaseValidator):
    TITLE = "OOB UNIT NAME VALIDATION"
    STAGED_EXTENSIONS = [".txt"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.canonical = set()
        self.canonical_lower = {}
        self.namelist_canonical = set()
        self.namelist_canonical_lower = {}

    def _build_canonical_units(self):
        """Build the canonical unit name set from unit definition files."""
        self._log_section("Building canonical unit name set...")

        self.canonical = parse_canonical_units(self.mod_path)
        self.canonical_lower = {name.lower(): name for name in self.canonical}

        # Namelist keys also accept equipment-type names (air namelists use
        # `small_plane_airframe` rather than the sub_unit name `light_fighter`).
        self.namelist_canonical = parse_canonical_namelist_keys(
            self.mod_path, self.canonical
        )
        self.namelist_canonical_lower = {
            name.lower(): name for name in self.namelist_canonical
        }

        self.log(f"  Found {len(self.canonical)} canonical sub-unit definitions")
        self.log(
            f"  Found {len(self.namelist_canonical)} valid namelist block keys"
            f" (sub_units + equipment types)"
        )

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
        self._log_section("Checking unit references in OOB and AI template files...")

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

    def validate_namelist_references(self):
        """Validate that namelist block keys and ship_types tokens are canonical."""
        self._log_section("Checking namelist block keys and ship_types tokens...")

        files = self._collect_files(
            [
                "common/units/names/*.txt",
                "common/units/names_ships/*.txt",
                "common/units/names_divisions/*.txt",
            ]
        )
        self.log(f"  Found {len(files)} namelist files to check")

        args_list = [
            (f, self.namelist_canonical, self.namelist_canonical_lower) for f in files
        ]
        all_results = self._pool_map(validate_namelist_file, args_list, chunksize=20)

        results = []
        for file_results in all_results:
            results.extend(file_results)

        # Namelist mismatches are reported as warnings (not errors) — many
        # legacy 00_*_names.txt files still carry vanilla-style block keys
        # (cavalry, motorized, LHA, LPD, etc.) that need a per-block cleanup
        # decision (rename, merge, or delete). Surface them without breaking
        # CI on existing dead code.
        self._report(
            results,
            "✓ All namelist references match canonical definitions",
            "Files with unknown namelist references:",
            severity=Severity.WARNING,
        )

    def validate_division_names_group_references(self):
        """Validate every `division_names_group = X` in OOB files points to a real group."""
        self._log_section("Checking division_names_group references in OOB files...")

        group_keys = parse_division_group_keys(self.mod_path)
        group_keys_lower = {k.lower(): k for k in group_keys}
        self.log(f"  Found {len(group_keys)} division_names_group definitions")

        files = self._collect_files(["history/units/*.txt"])
        self.log(f"  Found {len(files)} OOB files to check")

        args_list = [(f, group_keys, group_keys_lower) for f in files]
        all_results = self._pool_map(
            validate_oob_division_groups_file, args_list, chunksize=20
        )

        results = []
        for file_results in all_results:
            results.extend(file_results)

        self._report(
            results,
            "✓ All division_names_group references resolve",
            "OOB files with unknown division_names_group references:",
        )

    def run_validations(self):
        self._build_canonical_units()
        self.validate_unit_references()
        self.validate_namelist_references()
        self.validate_division_names_group_references()


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate unit names in OOB files and AI templates against canonical definitions",
    )
