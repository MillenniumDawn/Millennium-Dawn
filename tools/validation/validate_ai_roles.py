#!/usr/bin/env python3
##########################
# AI Role Reference Validation Script
# Cross-references role_ratio and build_army references in AI strategy files
# against role definitions in AI template files.
#
# Checks:
#   1. Collects all valid role names from common/ai_templates/*.txt
#   2. Finds all role_ratio id = X and build_army id = X in common/ai_strategy/*.txt
#   3. Reports any referenced role not found in the template definitions
#   4. Suggests closest match for likely typos
##########################
import difflib
import glob
import os
import re
from typing import Dict, List, Set, Tuple

from validator_common import BaseValidator, Colors, run_validator_main, strip_comments

# Regex to match role definitions: role = <name>
ROLE_DEF_RE = re.compile(r"role\s*=\s*(\w+)")

# Regex to match role references: role_ratio id = <name> or build_army id = <name>
ROLE_REF_RE = re.compile(r"(?:role_ratio|build_army)\s+id\s*=\s*(\w+)")

# Vanilla HOI4 roles defined outside common/ai_templates/ (naval, air, missile, etc.)
# These are valid roles handled by the base game engine, not mod templates.
VANILLA_ROLES = {
    # Naval roles (defined in vanilla naval templates)
    "naval_corvettes",
    "naval_frigate",
    "naval_destroyer",
    "naval_stealth_destroyer",
    "naval_attack_submarine",
    "naval_missile_submarine",
    "naval_helicopter_operator",
    "naval_carrier",
    "naval_cruiser",
    "naval_mine_sweeper",
    # Missile roles (no templates but valid engine roles)
    "missile",
    "sam_missile",
    "ballistic_missile",
    "nuclear_missile",
    # Air roles handled by vanilla
    "cv_fighter",
    "cv_naval_bomber",
    "cv_interceptor",
}


def collect_roles_from_file(filepath: str) -> Set[str]:
    """Parse an AI template file and return the set of defined role names."""
    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            content = f.read()
    except Exception:
        return set()

    content = strip_comments(content)
    return set(ROLE_DEF_RE.findall(content))


def collect_references_from_file(
    filepath: str,
) -> List[Tuple[str, str, int]]:
    """Parse an AI strategy file and return role references.

    Returns list of (role_name, filename, line_number).
    """
    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            lines = f.readlines()
    except Exception:
        return []

    filename = os.path.basename(filepath)
    results = []
    for i, line in enumerate(lines, start=1):
        # Strip inline comments
        comment_pos = line.find("#")
        if comment_pos >= 0:
            line = line[:comment_pos]
        for match in ROLE_REF_RE.finditer(line):
            results.append((match.group(1), filename, i))
    return results


def validate_strategy_file(
    args: Tuple[str, Set[str]],
) -> List[str]:
    """Validate a single AI strategy file. Returns list of error strings."""
    filepath, valid_roles = args
    references = collect_references_from_file(filepath)
    results = []
    for role_name, filename, line_num in references:
        if role_name not in valid_roles:
            suggestion = ""
            matches = difflib.get_close_matches(role_name, valid_roles, n=1, cutoff=0.6)
            if matches:
                suggestion = f" (did you mean '{matches[0]}'?)"
            results.append(
                f"{filename}:{line_num}: unknown role '{role_name}'{suggestion}"
            )
    return results


class Validator(BaseValidator):
    TITLE = "AI ROLE REFERENCES"
    STAGED_EXTENSIONS = [".txt"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.valid_roles: Set[str] = set()

    def _collect_valid_roles(self):
        """Collect all role definitions from AI template files."""
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Collecting role definitions from AI templates...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        # Always scan ALL template files for role definitions, even in staged mode.
        # Role definitions are the "truth set" — we need the complete picture.
        template_pattern = os.path.join(
            self.mod_path, "common", "ai_templates", "*.txt"
        )
        template_files = glob.glob(template_pattern)
        for filepath in template_files:
            self.valid_roles.update(collect_roles_from_file(filepath))

        # Add vanilla roles that are defined outside mod templates
        self.valid_roles.update(VANILLA_ROLES)

        self.log(
            f"  Found {len(self.valid_roles)} role definitions (including vanilla)"
        )
        if self.valid_roles:
            self.log(f"  Roles: {', '.join(sorted(self.valid_roles))}")

    def _validate_strategy_references(self):
        """Validate that all role references in strategy files point to valid roles."""
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking role references in AI strategy files...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        strategy_files = self._collect_files(["common/ai_strategy/*.txt"])
        self.log(f"  Found {len(strategy_files)} strategy files to check")

        args_list = [(f, self.valid_roles) for f in strategy_files]

        all_results = self._pool_map(validate_strategy_file, args_list, chunksize=20)

        results = []
        for file_results in all_results:
            results.extend(file_results)

        self._report(
            results,
            "✓ All AI role references are valid",
            "AI strategy files with invalid role references:",
        )

    def run_validations(self):
        self._collect_valid_roles()
        self._validate_strategy_references()


if __name__ == "__main__":
    run_validator_main(Validator, "Validate AI role references")
