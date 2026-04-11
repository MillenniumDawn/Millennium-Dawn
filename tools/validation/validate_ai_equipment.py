#!/usr/bin/env python3
##########################
# AI Equipment Coverage Validation Script
# Ensures nations blocked from generic equipment files have all
# required equipment roles covered in custom or shared files.
#
# Validates both naval (generic_naval.txt) and land (generic_tank.txt,
# generic_afv.txt) equipment categories.
#
# Checks:
#   1. Parses generic_*.txt for roles and their blocked_for lists
#   2. Parses all other equipment files for roles and available_for lists
#   3. Reports any nation blocked from a generic role without custom coverage
#   4. Reports any role template with duplicate names across overlapping files
##########################
import glob
import os
import re
import sys
from typing import Dict, List, Set, Tuple

from validator_common import BaseValidator, Colors, run_validator_main, strip_comments

# Regex patterns
ROLE_RE = re.compile(r"roles\s*=\s*\{([^}]*)\}")
BLOCKED_FOR_RE = re.compile(r"blocked_for\s*=\s*\{([^}]*)\}", re.DOTALL)
AVAILABLE_FOR_RE = re.compile(r"available_for\s*=\s*\{([^}]*)\}", re.DOTALL)
CATEGORY_RE = re.compile(r"category\s*=\s*(naval|land|air)")
TEMPLATE_NAME_RE = re.compile(r"^(\w+)\s*=\s*\{", re.MULTILINE)


def parse_tags(text: str) -> Set[str]:
    """Extract 3-letter country tags from a block."""
    return set(re.findall(r"\b([A-Z]{3})\b", text))


def parse_equipment_file(
    filepath: str,
) -> List[Dict]:
    """Parse an AI equipment file and return role template info.

    Returns list of dicts with keys:
        name: template name
        category: 'naval' or 'land'
        roles: set of role names
        blocked_for: set of blocked tags (generic files)
        available_for: set of available tags (custom/shared files)
        filename: basename
    """
    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            content = f.read()
    except Exception:
        return []

    filename = os.path.basename(filepath)
    templates = []

    # Split into top-level blocks
    lines = content.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip comments
        if line.startswith("#") or not line:
            i += 1
            continue

        # Look for top-level template definition
        match = re.match(r"^(\w+)\s*=\s*\{", line)
        if match:
            template_name = match.group(1)
            brace_depth = line.count("{") - line.count("}")
            block_lines = [line]
            i += 1

            while i < len(lines) and brace_depth > 0:
                block_lines.append(lines[i])
                brace_depth += lines[i].count("{") - lines[i].count("}")
                i += 1

            block_text = "\n".join(block_lines)

            # Only process naval or land templates
            cat_match = CATEGORY_RE.search(block_text)
            if not cat_match:
                continue
            category = cat_match.group(1)

            # Extract roles
            role_match = ROLE_RE.search(block_text)
            if not role_match:
                continue
            roles = set(role_match.group(1).split())

            # Extract blocked_for
            blocked = set()
            blocked_match = BLOCKED_FOR_RE.search(block_text)
            if blocked_match:
                blocked = parse_tags(blocked_match.group(1))

            # Extract available_for
            available = set()
            available_match = AVAILABLE_FOR_RE.search(block_text)
            if available_match:
                available = parse_tags(available_match.group(1))

            templates.append(
                {
                    "name": template_name,
                    "category": category,
                    "roles": roles,
                    "blocked_for": blocked,
                    "available_for": available,
                    "filename": filename,
                }
            )
        else:
            i += 1

    return templates


class Validator(BaseValidator):
    TITLE = "AI EQUIPMENT COVERAGE"
    STAGED_EXTENSIONS = [".txt"]

    def run_validations(self):
        self._validate_coverage()

    def _validate_coverage(self):
        equip_dir = os.path.join(self.mod_path, "common", "ai_equipment")
        if not os.path.isdir(equip_dir):
            self.log("  common/ai_equipment/ not found, skipping")
            return

        # Skip if no relevant files staged
        if self.staged_only and self.staged_files:
            relevant = [f for f in self.staged_files if "ai_equipment" in f]
            if not relevant:
                self.log("  No staged ai_equipment files, skipping")
                return

        # Parse all equipment files
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Parsing AI equipment files...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        generic_templates = []
        custom_templates = []

        for filepath in sorted(glob.iglob(os.path.join(equip_dir, "*.txt"))):
            filename = os.path.basename(filepath)
            templates = parse_equipment_file(filepath)

            if filename.startswith("generic"):
                generic_templates.extend(templates)
            else:
                custom_templates.extend(templates)

        # Group by category for reporting
        categories = set()
        for t in generic_templates + custom_templates:
            categories.add(t["category"])

        self.log(
            f"  Found {len(generic_templates)} generic role templates, "
            f"{len(custom_templates)} custom/shared role templates "
            f"across categories: {', '.join(sorted(categories))}"
        )

        # Validate each category separately
        for category in sorted(categories):
            cat_generic = [t for t in generic_templates if t["category"] == category]
            cat_custom = [t for t in custom_templates if t["category"] == category]
            cat_labels = {
                "naval": "naval",
                "land": "land (tank/AFV)",
                "air": "air (plane)",
            }
            cat_label = cat_labels.get(category, category)

            # Build coverage map: for each role, which nations are blocked
            role_blocked: Dict[str, Set[str]] = {}
            for t in cat_generic:
                for role in t["roles"]:
                    role_blocked.setdefault(role, set()).update(t["blocked_for"])

            # Build coverage: role -> set of nations with custom coverage
            role_covered: Dict[str, Set[str]] = {}
            for t in cat_custom:
                for role in t["roles"]:
                    if t["available_for"]:
                        role_covered.setdefault(role, set()).update(t["available_for"])
                    else:
                        # No available_for means it's a nation-specific file
                        # Infer the tag from filename
                        tag = t["filename"].split("_")[0].upper()
                        if len(tag) == 3:
                            role_covered.setdefault(role, set()).add(tag)

            # Check: every blocked nation must have custom coverage
            self.log(f"\n{'='*80}")
            self.log(
                f"{Colors.CYAN if self.use_colors else ''}Checking {cat_label} coverage for blocked nations...{Colors.ENDC if self.use_colors else ''}"
            )
            self.log(f"{'='*80}")

            coverage_results = []
            for role, blocked_tags in sorted(role_blocked.items()):
                covered = role_covered.get(role, set())
                uncovered = blocked_tags - covered
                for tag in sorted(uncovered):
                    coverage_results.append(
                        f"{tag}: blocked from generic '{role}' but has no custom coverage"
                    )

            self._report(
                coverage_results,
                f"✓ All blocked nations have custom {cat_label} equipment coverage",
                f"Nations blocked from generic {cat_label} roles without custom coverage:",
            )

        # Check: duplicate template names across files
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking for duplicate template names...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        all_templates = generic_templates + custom_templates
        name_locations: Dict[str, List[str]] = {}
        for t in all_templates:
            name_locations.setdefault(t["name"], []).append(t["filename"])

        duplicate_results = []
        for name, files in sorted(name_locations.items()):
            if len(files) > 1:
                duplicate_results.append(
                    f"Template '{name}' defined in multiple files: {', '.join(files)}"
                )

        self._report(
            duplicate_results,
            "✓ No duplicate template names found",
            "Duplicate template names (last-loaded file wins silently):",
        )


if __name__ == "__main__":
    run_validator_main(Validator, "Validate AI equipment coverage")
