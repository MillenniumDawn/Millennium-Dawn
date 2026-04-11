#!/usr/bin/env python3
##########################
# Naval Template Validation Script
# Validates AI navy taskforce and fleet template definitions.
#
# Checks:
#   1. Ship types in taskforce templates match canonical sub_unit definitions
#   2. Taskforce names referenced in fleet templates match defined taskforces
#   3. Mission types in taskforce templates are valid HOI4 naval missions
#   4. Optimal composition sizes respect NAI define limits
#   5. Suggests closest match for likely typos
##########################
import difflib
import glob
import os
import re
import sys
from typing import Dict, List, Set, Tuple

from validator_common import BaseValidator, Colors, run_validator_main, strip_comments

# Valid HOI4 naval mission types
VALID_MISSIONS = {
    "naval_patrol",
    "naval_strike",
    "convoy_escort",
    "convoy_raiding",
    "naval_invasion_support",
    "mines_planting",
    "mines_sweeping",
    "naval_superiority",
    "hold",
    "naval_carrier_operations",
}

# Ship type classifications for composition limit checks
# Source: common/units/MD_naval_units.txt type = X fields
CARRIER_TYPES = {"carrier", "helicopter_operator"}
CAPITAL_TYPES = {
    "battleship",
    "battle_cruiser",
    "cruiser",
    "stealth_destroyer",
    "destroyer",
    "heavy_frigate",
}
SCREEN_TYPES = {
    "screen_destroyer",
    "stealth_frigate",
    "frigate",
    "corvette",
    "stealth_corvette",
    "patrol_boat",
}
SUB_TYPES = {"missile_submarine", "attack_submarine"}

# NAI define limits — from common/defines/MD_defines.lua
# These cap how many ships the AI puts per type category in a single taskforce.
CARRIER_MAX = 2  # CARRIER_TASKFORCE_MAX_CARRIER_COUNT
CAPITAL_MAX = 6  # CAPITAL_TASKFORCE_MAX_CAPITAL_COUNT
SCREEN_MAX = 8  # SCREEN_TASKFORCE_MAX_SHIP_COUNT
SUB_MAX = 8  # SUB_TASKFORCE_MAX_SHIP_COUNT

# Ship type references inside composition blocks: name = { amount = N }
SHIP_TYPE_RE = re.compile(r"^\s+(\w+)\s*=\s*\{")

# Mission references: mission = { ... } or mission { ... }
MISSION_BLOCK_RE = re.compile(r"mission\s*=?\s*\{([^}]*)\}")

# Taskforce name references in fleet templates
TASKFORCE_REF_RE = re.compile(r"^\s+(\w+)\s*=\s*(\d+)")

# Taskforce definition: top-level name = {
TASKFORCE_DEF_RE = re.compile(r"^(\w+)\s*=\s*\{")


def parse_naval_units(mod_path: str) -> Set[str]:
    """Parse canonical ship sub_unit names from common/units/*naval*.txt.

    Naval unit files use sub_units = { unit_name = { ... } ... } structure.
    The unit names at depth 2 (directly inside sub_units) are the ship types.
    We identify naval unit files by filename containing 'naval' — MD uses
    MD_naval_units.txt and there is no group = navy attribute on individual units.
    """
    units_dir = os.path.join(mod_path, "common", "units")
    ship_types = set()

    for filepath in glob.iglob(os.path.join(units_dir, "*.txt")):
        # Only parse naval unit files
        basename = os.path.basename(filepath).lower()
        if "naval" not in basename and "ship" not in basename:
            continue

        try:
            with open(filepath, "r", encoding="utf-8-sig") as f:
                content = f.read()
        except Exception:
            continue

        content = strip_comments(content)

        # Find sub_units block and extract unit names at depth 2
        brace_depth = 0
        for line in content.split("\n"):
            stripped = line.strip()
            if not stripped:
                continue

            # Count opening braces BEFORE checking for definitions,
            # so we get accurate depth tracking
            opens = stripped.count("{")
            closes = stripped.count("}")

            # At depth 1 (inside sub_units), a "name = {" is a unit definition
            if brace_depth == 1:
                match = re.match(r"^(\w+)\s*=\s*\{", stripped)
                if match:
                    ship_types.add(match.group(1))

            brace_depth += opens - closes

    return ship_types


# Composition entry: ship_type with amount
AMOUNT_RE = re.compile(r"amount\s*=\s*(\d+)")


def parse_taskforce_files(
    mod_path: str,
) -> Tuple[
    Set[str],
    List[Tuple[str, str, int]],
    List[Tuple[str, str, int]],
    List[Tuple[str, str, int, Dict[str, int]]],
]:
    """Parse taskforce template files.

    Returns:
        - Set of defined taskforce template names
        - List of (ship_type, filename, line_num) for ship type references
        - List of (mission_type, filename, line_num) for mission references
        - List of (tf_name, filename, line_num, {ship_type: amount}) for optimal compositions
    """
    taskforce_dir = os.path.join(mod_path, "common", "ai_navy", "taskforce")
    if not os.path.isdir(taskforce_dir):
        return set(), [], [], []

    defined_taskforces: Set[str] = set()
    ship_refs: List[Tuple[str, str, int]] = []
    mission_refs: List[Tuple[str, str, int]] = []
    optimal_compositions: List[Tuple[str, str, int, Dict[str, int]]] = []

    for filepath in glob.iglob(os.path.join(taskforce_dir, "*.txt")):
        filename = os.path.basename(filepath)
        try:
            with open(filepath, "r", encoding="utf-8-sig") as f:
                lines = f.readlines()
        except Exception:
            continue

        in_composition = False
        in_optimal = False
        brace_depth = 0
        current_tf_name = ""
        current_tf_line = 0
        current_optimal: Dict[str, int] = {}
        current_ship_type = ""

        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()

            # Strip comments
            comment_pos = stripped.find("#")
            if comment_pos >= 0:
                stripped = stripped[:comment_pos].strip()
            if not stripped:
                continue

            # Track brace depth
            opens = stripped.count("{")
            closes = stripped.count("}")

            # Top-level taskforce definition
            if brace_depth == 0:
                match = TASKFORCE_DEF_RE.match(stripped)
                if match:
                    current_tf_name = match.group(1)
                    current_tf_line = line_num
                    defined_taskforces.add(current_tf_name)

            # Detect composition blocks
            if "optimal_composition" in stripped:
                in_optimal = True
                in_composition = True
                current_optimal = {}
            elif "min_composition" in stripped:
                in_composition = True

            # Inside composition: ship type references
            if in_composition and brace_depth >= 2:
                match = SHIP_TYPE_RE.match(line)
                if match:
                    name = match.group(1)
                    if name not in ("amount", "min_composition", "optimal_composition"):
                        ship_refs.append((name, filename, line_num))
                        current_ship_type = name

                # Capture amount for optimal composition tracking
                if in_optimal and current_ship_type:
                    amount_match = AMOUNT_RE.search(stripped)
                    if amount_match:
                        current_optimal[current_ship_type] = int(amount_match.group(1))
                        current_ship_type = ""

            # Mission references
            mission_match = MISSION_BLOCK_RE.search(stripped)
            if mission_match:
                missions = mission_match.group(1).split()
                for m in missions:
                    m = m.strip()
                    if m:
                        mission_refs.append((m, filename, line_num))

            brace_depth += opens - closes

            # Reset composition tracking when we exit the block
            if in_composition and brace_depth < 2:
                if in_optimal and current_optimal:
                    optimal_compositions.append(
                        (
                            current_tf_name,
                            filename,
                            current_tf_line,
                            dict(current_optimal),
                        )
                    )
                in_composition = False
                in_optimal = False
                current_optimal = {}
                current_ship_type = ""

    return defined_taskforces, ship_refs, mission_refs, optimal_compositions


def parse_fleet_files(
    mod_path: str,
) -> List[Tuple[str, str, int]]:
    """Parse fleet template files for taskforce references.

    Returns list of (taskforce_name, filename, line_num).
    """
    fleet_dir = os.path.join(mod_path, "common", "ai_navy", "fleet")
    if not os.path.isdir(fleet_dir):
        return []

    refs: List[Tuple[str, str, int]] = []

    for filepath in glob.iglob(os.path.join(fleet_dir, "*.txt")):
        filename = os.path.basename(filepath)
        try:
            with open(filepath, "r", encoding="utf-8-sig") as f:
                lines = f.readlines()
        except Exception:
            continue

        in_taskforces_block = False
        brace_depth = 0

        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()

            comment_pos = stripped.find("#")
            if comment_pos >= 0:
                stripped = stripped[:comment_pos].strip()
            if not stripped:
                continue

            opens = stripped.count("{")
            closes = stripped.count("}")

            # Detect required_taskforces / optional_taskforces blocks
            if "taskforces" in stripped:
                in_taskforces_block = True

            # Inside taskforces block: references to taskforce template names
            if in_taskforces_block and brace_depth >= 2:
                match = TASKFORCE_REF_RE.match(line)
                if match:
                    name = match.group(1)
                    if name not in ("required_taskforces", "optional_taskforces"):
                        refs.append((name, filename, line_num))

            brace_depth += opens - closes

            if in_taskforces_block and brace_depth < 2:
                in_taskforces_block = False

    return refs


class Validator(BaseValidator):
    TITLE = "NAVAL TEMPLATE VALIDATION"
    STAGED_EXTENSIONS = [".txt"]

    def run_validations(self):
        # Skip if no relevant files staged
        if self.staged_only and self.staged_files:
            relevant = [f for f in self.staged_files if "ai_navy" in f or "units" in f]
            if not relevant:
                self.log("  No staged ai_navy or units files, skipping")
                return

        # Parse taskforce files once, reuse in all checks
        (
            self._defined_taskforces,
            self._ship_refs,
            self._mission_refs,
            self._optimal_compositions,
        ) = parse_taskforce_files(self.mod_path)
        self._validate_ship_types()
        self._validate_fleet_references()
        self._validate_composition_limits()

    def _validate_ship_types(self):
        """Validate ship types and missions in taskforce templates."""
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Collecting canonical ship types from common/units/...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        ship_types = parse_naval_units(self.mod_path)
        self.log(
            f"  Found {len(ship_types)} naval sub_unit types: {', '.join(sorted(ship_types))}"
        )

        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking taskforce template ship types...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        defined_taskforces = self._defined_taskforces
        ship_refs = self._ship_refs
        mission_refs = self._mission_refs
        self.log(
            f"  Found {len(defined_taskforces)} taskforce templates, "
            f"{len(ship_refs)} ship type references, "
            f"{len(mission_refs)} mission references"
        )

        # Check ship types
        ship_results = []
        for ship_type, filename, line_num in ship_refs:
            if ship_type not in ship_types:
                suggestion = ""
                matches = difflib.get_close_matches(
                    ship_type, list(ship_types), n=1, cutoff=0.6
                )
                if matches:
                    suggestion = f" (did you mean '{matches[0]}'?)"
                ship_results.append(
                    f"{filename}:{line_num}: unknown ship type '{ship_type}'{suggestion}"
                )

        self._report(
            ship_results,
            "✓ All ship types in taskforce templates are valid",
            "Invalid ship types in taskforce templates:",
        )

        # Check missions
        mission_results = []
        for mission, filename, line_num in mission_refs:
            if mission not in VALID_MISSIONS:
                suggestion = ""
                matches = difflib.get_close_matches(
                    mission, list(VALID_MISSIONS), n=1, cutoff=0.6
                )
                if matches:
                    suggestion = f" (did you mean '{matches[0]}'?)"
                mission_results.append(
                    f"{filename}:{line_num}: unknown mission type '{mission}'{suggestion}"
                )

        self._report(
            mission_results,
            "✓ All mission types in taskforce templates are valid",
            "Invalid mission types in taskforce templates:",
        )

    def _validate_fleet_references(self):
        """Validate that fleet templates reference defined taskforce templates."""
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking fleet template taskforce references...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        defined_taskforces = self._defined_taskforces

        # Get all fleet references
        fleet_refs = parse_fleet_files(self.mod_path)
        self.log(f"  Found {len(fleet_refs)} taskforce references in fleet templates")

        results = []
        for tf_name, filename, line_num in fleet_refs:
            if tf_name not in defined_taskforces:
                suggestion = ""
                matches = difflib.get_close_matches(
                    tf_name, list(defined_taskforces), n=1, cutoff=0.6
                )
                if matches:
                    suggestion = f" (did you mean '{matches[0]}'?)"
                results.append(
                    f"{filename}:{line_num}: unknown taskforce '{tf_name}'{suggestion}"
                )

        self._report(
            results,
            "✓ All fleet taskforce references are valid",
            "Invalid taskforce references in fleet templates:",
        )

    def _validate_composition_limits(self):
        """Validate optimal compositions respect NAI define limits."""
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking taskforce composition limits "
            f"(carrier≤{CARRIER_MAX}, capital≤{CAPITAL_MAX}, "
            f"screen≤{SCREEN_MAX}, sub≤{SUB_MAX})..."
            f"{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        results = []
        for tf_name, filename, line_num, composition in self._optimal_compositions:
            carrier_count = sum(composition.get(t, 0) for t in CARRIER_TYPES)
            capital_count = sum(composition.get(t, 0) for t in CAPITAL_TYPES)
            screen_count = sum(composition.get(t, 0) for t in SCREEN_TYPES)
            sub_count = sum(composition.get(t, 0) for t in SUB_TYPES)

            violations = []
            if carrier_count > CARRIER_MAX:
                violations.append(f"carrier={carrier_count}>{CARRIER_MAX}")
            if capital_count > CAPITAL_MAX:
                violations.append(f"capital={capital_count}>{CAPITAL_MAX}")
            if screen_count > SCREEN_MAX:
                violations.append(f"screen={screen_count}>{SCREEN_MAX}")
            if sub_count > SUB_MAX:
                violations.append(f"sub={sub_count}>{SUB_MAX}")

            if violations:
                results.append(
                    f"{filename}:{line_num}: {tf_name} exceeds NAI limits: "
                    f"{', '.join(violations)}"
                )

        self._report(
            results,
            "✓ All taskforce compositions within NAI define limits",
            "Taskforce compositions exceeding NAI define limits:",
        )


if __name__ == "__main__":
    run_validator_main(Validator, "Validate AI navy templates")
