#!/usr/bin/env python3
# Ensure nations blocked from generic equipment files (naval generic_naval.txt,
# land generic_tank.txt / generic_afv.txt) have every required equipment role
# covered in a custom or shared file, and flag role templates whose names
# collide across overlapping files.
import glob
import logging
import os
import re
import sys
from typing import Any, Dict, List, Optional, Set

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from equipment_module_slots import build_equipment_index, check_target_variants
from shared_utils import strip_inline_comment
from validator_common import BaseValidator, Issue, Severity, run_validator_main

_NAVAL_SLOT_CATEGORIES = {
    "unknown_hull": "NAVAL VARIANT: unknown hull type",
    "unknown_slot": "NAVAL VARIANT: slot not on hull",
    "unknown_module": "NAVAL VARIANT: unknown module reference",
    "category_mismatch": "NAVAL VARIANT: module category not allowed in slot",
    "missing_required_module": "NAVAL VARIANT: required slot left empty",
}

_EQUIPMENT_SLOT_CATEGORIES = {
    "unknown_hull": "EQUIPMENT VARIANT: unknown hull type",
    "unknown_slot": "EQUIPMENT VARIANT: slot not on hull",
    "unknown_module": "EQUIPMENT VARIANT: unknown module reference",
    "category_mismatch": "EQUIPMENT VARIANT: module category not allowed in slot",
    "missing_required_module": "EQUIPMENT VARIANT: required slot left empty",
}

ROLE_RE = re.compile(r"roles\s*=\s*\{([^}]*)\}")
BLOCKED_FOR_RE = re.compile(r"blocked_for\s*=\s*\{([^}]*)\}", re.DOTALL)
AVAILABLE_FOR_RE = re.compile(r"available_for\s*=\s*\{([^}]*)\}", re.DOTALL)
CATEGORY_RE = re.compile(r"category\s*=\s*(naval|land|air)")
TEMPLATE_NAME_RE = re.compile(r"^(\w+)\s*=\s*\{", re.MULTILINE)
HISTORY_RE = re.compile(r"^\s*history\s*=\s*yes\s*$", re.MULTILINE)

# Keys that are design attributes rather than nested design blocks.
DESIGN_META_KEYS = {
    "priority",
    "roles",
    "available_for",
    "blocked_for",
    "allowed_modules",
    "allowed_types",
    "requirements",
    "enable",
    "allowed",
    "upgrades",
    "target_variant",
    "modules",
}


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
            code = strip_inline_comment(line)
            brace_depth = code.count("{") - code.count("}")
            block_lines = [line]
            i += 1

            while i < len(lines) and brace_depth > 0:
                block_lines.append(lines[i])
                code = strip_inline_comment(lines[i])
                brace_depth += code.count("{") - code.count("}")
                i += 1

            block_text = "\n".join(block_lines)

            # Only process naval or land templates
            cat_match = CATEGORY_RE.search(block_text)
            if not cat_match:
                continue
            category = cat_match.group(1)

            role_match = ROLE_RE.search(block_text)
            if not role_match:
                continue
            roles = set(role_match.group(1).split())

            blocked = set()
            blocked_match = BLOCKED_FOR_RE.search(block_text)
            if blocked_match:
                blocked = parse_tags(blocked_match.group(1))

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


def _read_text(filepath: str) -> str:
    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            return f.read()
    except OSError:
        logging.warning(
            "Could not read %s; its variant modules will not be checked", filepath
        )
        return ""


def parse_designs(content: str) -> List[Dict]:
    """Return one entry per design block, with the group it belongs to and
    whether it carries ``history = yes``.

    ``history`` decides which folder a design appears in inside the equipment
    designer, so a group that sets it on only some of its designs shows the
    player a partial preset list.
    """
    designs: List[Dict[str, Any]] = []
    lines = content.split("\n")
    group = None
    group_depth = 0
    depth = 0
    pending: Optional[Dict[str, Any]] = None

    for idx, raw in enumerate(lines):
        code = strip_inline_comment(raw)
        stripped = code.strip()
        match = re.match(r"^(\w+)\s*=\s*\{", stripped)
        if match and depth in (0, group_depth):
            name = match.group(1)
            if depth == 0:
                group = name
                group_depth = 1
            elif name not in DESIGN_META_KEYS:
                pending = {
                    "group": group,
                    "name": name,
                    "line": idx + 1,
                    "start": idx,
                    "depth": depth,
                }
                designs.append(pending)
        depth += code.count("{") - code.count("}")
        if pending is not None and depth <= pending["depth"]:
            body = "\n".join(lines[pending["start"] : idx + 1])
            pending["history"] = bool(HISTORY_RE.search(body))
            pending["is_design"] = "target_variant" in body
            pending = None
        if depth == 0:
            group = None

    return [d for d in designs if d.get("is_design")]


class Validator(BaseValidator):
    TITLE = "AI EQUIPMENT COVERAGE"
    STAGED_EXTENSIONS = [".txt"]

    # WARNING until the ~390-site pre-existing backlog on main is cleared, then
    # ERROR (measured 2026-08: 262 naval + 124 land/air). PR #2510 fixed the
    # screen-hull fire-control class but left other category mismatches (light
    # engines on destroyers, ESM on subs, mineclearing on corvettes, engine
    # modules in weapon slots) untouched; the tank and plane templates came into
    # scope later and carry their own share.
    # A template that leaves a `required = yes` slot empty is different: no
    # design can match it, so it is always a hard error regardless of backlog.
    SLOT_SEVERITY = Severity.WARNING

    def run_validations(self):
        self._validate_coverage()
        self._validate_variant_modules()
        self._validate_history_consistency()

    def _validate_variant_modules(self):
        equip_dir = os.path.join(self.mod_path, "common", "ai_equipment")
        units_dir = os.path.join(self.mod_path, "common", "units", "equipment")
        if not os.path.isdir(equip_dir) or not os.path.isdir(units_dir):
            return

        staged_equip = None
        if self.staged_only and self.staged_files:
            staged_equip = {
                os.path.basename(f) for f in self.staged_files if "ai_equipment" in f
            }
            if not staged_equip:
                return

        self._log_section("Checking AI variant modules against hull slot rules...")

        index = self.cached(
            "equipment_hull_index", lambda: build_equipment_index(units_dir)
        )

        results = []
        for fp in sorted(glob.iglob(os.path.join(equip_dir, "*.txt"))):
            basename = os.path.basename(fp)
            if staged_equip is not None and basename not in staged_equip:
                continue
            content = _read_text(fp)
            rel = os.path.relpath(fp, self.mod_path)
            for f in check_target_variants(content, index):
                labels = (
                    _NAVAL_SLOT_CATEGORIES
                    if f.hull in index.ship_hulls
                    else _EQUIPMENT_SLOT_CATEGORIES
                )
                results.append(
                    Issue(
                        severity=(
                            Severity.ERROR
                            if f.kind == "missing_required_module"
                            else self.SLOT_SEVERITY
                        ),
                        category=labels[f.kind],
                        message=f.message,
                        file=rel,
                        line=f.line,
                    )
                )

        self._report(
            results,
            "✓ All AI variant modules match their hull slot rules",
            "AI variant modules invalid for their hull slot:",
            severity=self.SLOT_SEVERITY,
        )

    def _validate_history_consistency(self):
        equip_dir = os.path.join(self.mod_path, "common", "ai_equipment")
        if not os.path.isdir(equip_dir):
            return

        staged_equip = None
        if self.staged_only and self.staged_files:
            staged_equip = {
                os.path.basename(f) for f in self.staged_files if "ai_equipment" in f
            }
            if not staged_equip:
                return

        self._log_section("Checking history = yes consistency within design groups...")

        results = []
        for fp in sorted(glob.iglob(os.path.join(equip_dir, "*.txt"))):
            basename = os.path.basename(fp)
            if staged_equip is not None and basename not in staged_equip:
                continue
            rel = os.path.relpath(fp, self.mod_path)
            groups: Dict[str, List[Dict]] = {}
            for design in parse_designs(_read_text(fp)):
                groups.setdefault(design["group"], []).append(design)
            for group, designs in groups.items():
                marked = [d for d in designs if d["history"]]
                if not marked or len(marked) == len(designs):
                    continue
                missing = [d for d in designs if not d["history"]]
                results.append(
                    Issue(
                        severity=Severity.WARNING,
                        category="AI EQUIPMENT: partial history = yes",
                        message=(
                            f"'{group}' sets history = yes on "
                            f"{len(marked)}/{len(designs)} designs; "
                            f"{', '.join(d['name'] for d in missing)} will not "
                            f"appear in the designer alongside the rest"
                        ),
                        file=rel,
                        line=missing[0]["line"],
                    )
                )

        self._report(
            results,
            "✓ history = yes is applied consistently within design groups",
            "Design groups with an inconsistent history = yes:",
            severity=Severity.WARNING,
        )

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
        self._log_section("Parsing AI equipment files...")

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
            self._log_section(f"Checking {cat_label} coverage for blocked nations...")

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
        self._log_section("Checking for duplicate template names...")

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
