#!/usr/bin/env python3
# Cross-reference faction templates, goals, rules, manifests, upgrades, and icons
# to catch broken references and duplicate IDs that cause crashes or silent
# failures, and warn about orphaned manifests.
import glob
import os
import re
from typing import Dict, List, Set

from validator_common import (
    BaseValidator,
    Colors,
    FileOpener,
    run_validator_main,
)

# Valid faction rule types per engine documentation
VALID_RULE_TYPES = {
    "joining_rules",
    "war_declaration_rules",
    "call_to_war_rules",
    "dismissal_rules",
    "peace_conference_rules",
    "change_leader_rules",
    "member_rules",
    "contribution_rule",
}

# Top-level block: word = { at the start of a line (possibly indented by tabs)
BLOCK_DEF_RE = re.compile(r"^(\w+)\s*=\s*\{", re.MULTILINE)

MANIFEST_RE = re.compile(r"\bmanifest\s*=\s*(\w+)")
ICON_RE = re.compile(r"\bicon\s*=\s*(\w+)")
TYPE_RE = re.compile(r"\btype\s*=\s*(\w+)")
IS_MANIFEST_RE = re.compile(r"\bis_manifest\s*=\s*yes\b")


def read_file(filepath: str) -> str:
    # FileOpener-cached so the seven check methods that iterate templates only
    # pay disk cost once.
    return FileOpener.open_text_file(
        filepath, lowercase=False, strip_comments_flag=True
    )


def extract_block_ids(content: str) -> List[str]:
    """Extract all top-level block IDs from content."""
    return BLOCK_DEF_RE.findall(content)


def extract_goals_block(content: str, template_id: str) -> List[str]:
    """Extract goal IDs from a template's goals = { } block."""
    # Find the template block, then its goals sub-block
    pattern = re.compile(rf"{re.escape(template_id)}\s*=\s*\{{(.*?)\n\}}", re.DOTALL)
    match = pattern.search(content)
    if not match:
        return []

    template_body = match.group(1)
    goals_pattern = re.compile(r"\bgoals\s*=\s*\{([^}]*)\}", re.DOTALL)
    goals_match = goals_pattern.search(template_body)
    if not goals_match:
        return []

    goals_body = goals_match.group(1)
    return [
        w.strip() for w in goals_body.split() if w.strip() and not w.startswith("#")
    ]


def extract_default_rules_block(content: str, template_id: str) -> List[str]:
    """Extract rule IDs from a template's default_rules = { } block."""
    pattern = re.compile(rf"{re.escape(template_id)}\s*=\s*\{{(.*?)\n\}}", re.DOTALL)
    match = pattern.search(content)
    if not match:
        return []

    template_body = match.group(1)
    rules_pattern = re.compile(r"\bdefault_rules\s*=\s*\{([^}]*)\}", re.DOTALL)
    rules_match = rules_pattern.search(template_body)
    if not rules_match:
        return []

    rules_body = rules_match.group(1)
    return [
        w.strip() for w in rules_body.split() if w.strip() and not w.startswith("#")
    ]


def extract_group_rule_ids(content: str) -> Dict[str, List[str]]:
    """Extract rule group names and their listed rule IDs."""
    groups = {}
    for match in re.finditer(r"(\w+)\s*=\s*\{(.*?)\n\}", content, re.DOTALL):
        group_id = match.group(1)
        body = match.group(2)
        rules_match = re.search(r"\brules\s*=\s*\{([^}]*)\}", body, re.DOTALL)
        if rules_match:
            rules = [
                w.strip()
                for w in rules_match.group(1).split()
                if w.strip() and not w.startswith("#")
            ]
            groups[group_id] = rules
    return groups


def extract_upgrade_group_ids(content: str) -> Dict[str, List[str]]:
    """Extract upgrade group names and their listed upgrade IDs."""
    groups = {}
    for match in re.finditer(r"(\w+)\s*=\s*\{(.*?)\n\}", content, re.DOTALL):
        group_id = match.group(1)
        body = match.group(2)
        upgrades_match = re.search(r"\bupgrades\s*=\s*\{([^}]*)\}", body, re.DOTALL)
        if upgrades_match:
            upgrades = [
                w.strip()
                for w in upgrades_match.group(1).split()
                if w.strip() and not w.startswith("#")
            ]
            groups[group_id] = upgrades
    return groups


class Validator(BaseValidator):
    TITLE = "FACTION SYSTEM VALIDATION"
    STAGED_EXTENSIONS = [".txt"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.template_ids: Dict[str, str] = {}  # id -> filepath
        self.goal_ids: Set[str] = set()
        self.manifest_ids: Set[str] = set()
        self.rule_ids: Set[str] = set()
        self.upgrade_ids: Set[str] = set()
        self.icon_ids: Set[str] = set()
        self.interface_icon_count: int = 0
        self.interface_read_failures: List[str] = []

    def _faction_path(self, *parts: str) -> str:
        return os.path.join(self.mod_path, "common", "factions", *parts)

    def _collect_definitions(self):
        """Collect all defined IDs across the faction system."""
        self._log_section("Collecting faction definitions...")

        # Collect template IDs
        template_dir = self._faction_path("templates")
        for filepath in glob.glob(os.path.join(template_dir, "*.txt")):
            content = read_file(filepath)
            for block_id in extract_block_ids(content):
                fname = os.path.basename(filepath)
                if block_id in self.template_ids:
                    pass  # collection intentionally does not dedup; _validate_duplicate_templates reports duplicates
                self.template_ids[block_id] = fname

        # Collect goal and manifest IDs from goals/
        goals_dir = self._faction_path("goals")
        for filepath in glob.glob(os.path.join(goals_dir, "*.txt")):
            content = read_file(filepath)
            for block_id in extract_block_ids(content):
                if IS_MANIFEST_RE.search(
                    content[content.index(block_id) : content.index(block_id) + 500]
                    if block_id in content
                    else ""
                ):
                    self.manifest_ids.add(block_id)
                self.goal_ids.add(block_id)

        # Collect rule IDs from rules/
        rules_dir = self._faction_path("rules")
        for filepath in glob.glob(os.path.join(rules_dir, "*.txt")):
            content = read_file(filepath)
            for block_id in extract_block_ids(content):
                self.rule_ids.add(block_id)

        # Collect upgrade IDs
        upgrades_dir = self._faction_path("upgrades")
        for filepath in glob.glob(os.path.join(upgrades_dir, "*.txt")):
            content = read_file(filepath)
            for block_id in extract_block_ids(content):
                self.upgrade_ids.add(block_id)

        # Collect member upgrade IDs
        member_dir = self._faction_path("member_upgrades")
        for filepath in glob.glob(os.path.join(member_dir, "*.txt")):
            content = read_file(filepath)
            for block_id in extract_block_ids(content):
                self.upgrade_ids.add(block_id)

        # Collect icon IDs from pool.txt
        pool_path = self._faction_path("icons", "pool.txt")
        if os.path.exists(pool_path):
            content = read_file(pool_path)
            self.icon_ids = set(re.findall(r"(GFX_\w+)", content))

        # Also collect GFX from interface files. Read with errors="replace" so a
        # single stray byte in factions.gfx (which alone defines every faction
        # icon) can't drop the whole file and masquerade as dozens of bogus
        # "icon not found" errors; a genuine IO failure is logged, never silent.
        interface_dir = os.path.join(self.mod_path, "interface")
        for filepath in glob.glob(
            os.path.join(interface_dir, "**", "*.gfx"), recursive=True
        ):
            try:
                with open(filepath, "r", encoding="utf-8-sig", errors="replace") as f:
                    content = f.read()
            except OSError as ex:
                self.interface_read_failures.append(filepath)
                self.log(f"  Warning: could not read {filepath}: {ex}", "warning")
                continue
            for match in re.finditer(r'name\s*=\s*"?(GFX_faction\w+)"?', content):
                self.icon_ids.add(match.group(1))
                self.interface_icon_count += 1

        self.log(f"  Templates: {len(self.template_ids)}")
        self.log(f"  Goals (incl manifests): {len(self.goal_ids)}")
        self.log(f"  Manifests: {len(self.manifest_ids)}")
        self.log(f"  Rules: {len(self.rule_ids)}")
        self.log(f"  Upgrades: {len(self.upgrade_ids)}")
        self.log(f"  Icons: {len(self.icon_ids)}")

    def _validate_template_manifests(self):
        """Check that every template's manifest references an existing manifest."""
        self._log_section("Checking template manifest references...")

        results = []
        template_dir = self._faction_path("templates")
        for filepath in glob.glob(os.path.join(template_dir, "*.txt")):
            content = read_file(filepath)
            fname = os.path.basename(filepath)
            for match in MANIFEST_RE.finditer(content):
                manifest_id = match.group(1)
                if manifest_id not in self.goal_ids:
                    results.append(
                        f"{fname}: manifest '{manifest_id}' not found in any goal file"
                    )

        self._report(
            results,
            "All template manifest references are valid",
            "Templates with invalid manifest references:",
        )

    def _validate_template_goals(self):
        """Check that every goal listed in a template exists."""
        self._log_section("Checking template goal references...")

        results = []
        template_dir = self._faction_path("templates")
        for filepath in glob.glob(os.path.join(template_dir, "*.txt")):
            content = read_file(filepath)
            fname = os.path.basename(filepath)
            for template_id in extract_block_ids(content):
                goals = extract_goals_block(content, template_id)
                for goal_id in goals:
                    if goal_id not in self.goal_ids:
                        results.append(
                            f"{fname} ({template_id}): goal '{goal_id}' not found"
                        )

        self._report(
            results,
            "All template goal references are valid",
            "Templates with invalid goal references:",
        )

    def _validate_template_rules(self):
        """Check that every rule listed in default_rules exists."""
        self._log_section("Checking template default_rules references...")

        results = []
        template_dir = self._faction_path("templates")
        for filepath in glob.glob(os.path.join(template_dir, "*.txt")):
            content = read_file(filepath)
            fname = os.path.basename(filepath)
            for template_id in extract_block_ids(content):
                rules = extract_default_rules_block(content, template_id)
                for rule_id in rules:
                    if rule_id not in self.rule_ids:
                        results.append(
                            f"{fname} ({template_id}): rule '{rule_id}' not found"
                        )

        self._report(
            results,
            "All template rule references are valid",
            "Templates with invalid rule references:",
        )

    def _validate_template_icons(self):
        """Check that every template icon exists in pool or interface."""
        self._log_section("Checking template icon references...")

        results = []
        referenced: Set[str] = set()
        template_dir = self._faction_path("templates")
        for filepath in glob.glob(os.path.join(template_dir, "*.txt")):
            content = read_file(filepath)
            fname = os.path.basename(filepath)
            for match in ICON_RE.finditer(content):
                icon_id = match.group(1)
                referenced.add(icon_id)
                if icon_id not in self.icon_ids:
                    results.append(
                        f"{fname}: icon '{icon_id}' not found in pool or interface"
                    )

        # Faction icons all live in interface/factions/factions.gfx. Collecting
        # fewer faction sprites than the templates even reference means that
        # source did not load (missing, unreadable, or an empty scan), so every
        # "not found" above is a false positive. Report that one root cause
        # instead, naming the read failure when we caught one.
        if referenced and (
            self.interface_read_failures or self.interface_icon_count < len(referenced)
        ):
            detail = (
                "; ".join(self.interface_read_failures)
                if self.interface_read_failures
                else "interface/factions/factions.gfx missing or unreadable"
            )
            self._report(
                [
                    f"faction icon source did not load ({detail}); "
                    "skipping per-template icon checks"
                ],
                "All template icon references are valid",
                "Faction icon source unavailable:",
            )
            return

        self._report(
            results,
            "All template icon references are valid",
            "Templates with invalid icon references:",
        )

    def _validate_rule_groups(self):
        """Check that every rule referenced in rule groups exists."""
        self._log_section("Checking rule group references...")

        results = []
        groups_path = self._faction_path("rules", "groups", "rule_groups.txt")
        if os.path.exists(groups_path):
            content = read_file(groups_path)
            groups = extract_group_rule_ids(content)
            for group_id, rule_list in groups.items():
                for rule_id in rule_list:
                    if rule_id not in self.rule_ids:
                        results.append(
                            f"rule_groups.txt ({group_id}): rule '{rule_id}' not found"
                        )

        self._report(
            results,
            "All rule group references are valid",
            "Rule groups with invalid references:",
        )

    def _validate_rule_types(self):
        """Check that every rule has a valid type."""
        self._log_section("Checking rule types...")

        results = []
        rules_dir = self._faction_path("rules")
        for filepath in glob.glob(os.path.join(rules_dir, "*.txt")):
            content = read_file(filepath)
            fname = os.path.basename(filepath)
            for match in TYPE_RE.finditer(content):
                rule_type = match.group(1)
                if rule_type not in VALID_RULE_TYPES:
                    results.append(f"{fname}: unknown rule type '{rule_type}'")

        self._report(
            results,
            "All rule types are valid",
            "Rules with invalid types:",
        )

    def _validate_duplicate_templates(self):
        """Check for duplicate template IDs across files."""
        self._log_section("Checking for duplicate template IDs...")

        results = []
        seen: Dict[str, str] = {}
        template_dir = self._faction_path("templates")
        for filepath in sorted(glob.glob(os.path.join(template_dir, "*.txt"))):
            content = read_file(filepath)
            fname = os.path.basename(filepath)
            for block_id in extract_block_ids(content):
                if block_id in seen and seen[block_id] != fname:
                    results.append(
                        f"Duplicate template '{block_id}' in {fname} (first in {seen[block_id]})"
                    )
                seen[block_id] = fname

        self._report(
            results,
            "No duplicate template IDs found",
            "Duplicate template IDs:",
        )

    def _validate_duplicate_goals(self):
        """Check for duplicate goal IDs across files."""
        self._log_section("Checking for duplicate goal IDs...")

        results = []
        seen: Dict[str, str] = {}
        goals_dir = self._faction_path("goals")
        for filepath in sorted(glob.glob(os.path.join(goals_dir, "*.txt"))):
            content = read_file(filepath)
            fname = os.path.basename(filepath)
            for block_id in extract_block_ids(content):
                if block_id in seen and seen[block_id] != fname:
                    results.append(
                        f"Duplicate goal '{block_id}' in {fname} (first in {seen[block_id]})"
                    )
                seen[block_id] = fname

        self._report(
            results,
            "No duplicate goal IDs found",
            "Duplicate goal IDs:",
        )

    def _validate_duplicate_rules(self):
        """Check for duplicate rule IDs across files."""
        self._log_section("Checking for duplicate rule IDs...")

        results = []
        seen: Dict[str, str] = {}
        rules_dir = self._faction_path("rules")
        for filepath in sorted(glob.glob(os.path.join(rules_dir, "*.txt"))):
            if "groups" in filepath:
                continue
            content = read_file(filepath)
            fname = os.path.basename(filepath)
            for block_id in extract_block_ids(content):
                if block_id in seen and seen[block_id] != fname:
                    results.append(
                        f"Duplicate rule '{block_id}' in {fname} (first in {seen[block_id]})"
                    )
                seen[block_id] = fname

        self._report(
            results,
            "No duplicate rule IDs found",
            "Duplicate rule IDs:",
        )

    def _validate_upgrade_groups(self):
        """Check that every upgrade in a group exists."""
        self._log_section("Checking upgrade group references...")

        results = []
        for subdir in ["upgrades/groups", "member_upgrades/member_groups"]:
            groups_dir = self._faction_path(subdir)
            for filepath in glob.glob(os.path.join(groups_dir, "*.txt")):
                content = read_file(filepath)
                fname = os.path.basename(filepath)
                groups = extract_upgrade_group_ids(content)
                for group_id, upgrade_list in groups.items():
                    for upgrade_id in upgrade_list:
                        if upgrade_id not in self.upgrade_ids:
                            results.append(
                                f"{fname} ({group_id}): upgrade '{upgrade_id}' not found"
                            )

        self._report(
            results,
            "All upgrade group references are valid",
            "Upgrade groups with invalid references:",
        )

    def _check_orphaned_manifests(self):
        """Warn about manifests not referenced by any template."""
        self._log_section("Checking for orphaned manifests...")

        referenced_manifests: Set[str] = set()
        template_dir = self._faction_path("templates")
        for filepath in glob.glob(os.path.join(template_dir, "*.txt")):
            content = read_file(filepath)
            for match in MANIFEST_RE.finditer(content):
                referenced_manifests.add(match.group(1))

        orphaned = self.manifest_ids - referenced_manifests
        if orphaned:
            self.log(
                f"{Colors.YELLOW if self.use_colors else ''}Warning: {len(orphaned)} manifest(s) not referenced by any template:{Colors.ENDC if self.use_colors else ''}",
                "warning",
            )
            for m in sorted(orphaned):
                self.log(f"  {m}", "warning")
        else:
            self.log(
                f"{Colors.GREEN if self.use_colors else ''}All manifests are referenced by at least one template{Colors.ENDC if self.use_colors else ''}"
            )

    def run_validations(self):
        self._collect_definitions()
        self._validate_template_manifests()
        self._validate_template_goals()
        self._validate_template_rules()
        self._validate_template_icons()
        self._validate_rule_groups()
        self._validate_rule_types()
        self._validate_duplicate_templates()
        self._validate_duplicate_goals()
        self._validate_duplicate_rules()
        self._validate_upgrade_groups()
        self._check_orphaned_manifests()


if __name__ == "__main__":
    run_validator_main(Validator, "Validate faction system references")
