#!/usr/bin/env python3

"""
Millennium Dawn Decision Standardizer
Standardizes HOI4 decision and decision category files according to Millennium Dawn coding standards
"""

import argparse
import os
import re
from typing import Any, Dict, List

from common_utils import (
    PROP_NAME_RE,
    BaseStandardizer,
    block_has_log,
    collapse_blank_runs,
    inject_log_after_brace,
)
from shared_utils import compact_block, create_backup, extract_block, log_message

_SINGLE_LINE_PROPS = {"cost", "days_remove", "fire_only_once", "icon"}
_BLOCK_PROPS = {"allowed", "visible", "available", "complete_effect", "ai_will_do"}

_CATEGORY_SINGLE_LINE_PROPS = {
    "icon",
    "picture",
    "scripted_gui",
    "visible_when_empty",
    "visibility_type",
}
_CATEGORY_BLOCK_PROPS = {
    "allowed",
    "available",
    "visible",
    "target_root_trigger",
    "on_map_area",
}


def reindent_block(block_lines: List[str], base_indent: int) -> List[str]:
    """Re-indent a block starting at base_indent tabs, tracking brace depth.

    The first line is always the property declaration (e.g. ``visible = {``)
    and is placed at *base_indent*.  Subsequent lines are indented relative
    to the brace depth so that nested blocks keep their structure.
    Closing braces ``}`` are placed at the same indent as their opening line.
    """
    if not block_lines:
        return block_lines

    result: List[str] = []
    depth = 0
    for i, line in enumerate(block_lines):
        stripped = line.strip()
        if not stripped:
            continue
        # Normalise internal whitespace (tabs → single spaces)
        normalized = " ".join(stripped.split())

        opens = normalized.count("{")
        closes = normalized.count("}")

        if i == 0:
            result.append("\t" * base_indent + normalized)
        else:
            # Closing braces sit at the same indent as their opening keyword
            if closes > opens:
                indent = base_indent + depth - (closes - opens)
            else:
                indent = base_indent + depth
            result.append("\t" * indent + normalized)
        depth += opens - closes

    return result


class DecisionCategoryStandardizer(BaseStandardizer):
    """Standardizer for HOI4 decision categories"""

    def get_block_pattern(self) -> str:
        """Return regex pattern to identify decision category blocks"""
        return r"\s*\w+_category\s*=\s*{"

    def extract_properties(self, block_lines: List[str]) -> Dict[str, Any]:
        """Extract properties from decision category block lines"""
        props: Dict[str, Any] = {
            "id": "",
            "allowed": [],
            "icon": "",
            "picture": "",
            "priority": "",
            "scripted_gui": "",
            "visible_when_empty": "",
            "visibility_type": "",
            "visible": [],
            "target_root_trigger": [],
            "on_map_area": [],
            "other": [],
        }

        if block_lines:
            first_line = block_lines[0].strip()
            if first_line and not first_line.startswith("#"):
                id_match = PROP_NAME_RE.match(first_line)
                if id_match:
                    props["id"] = id_match.group(1)

        i = 1  # Skip opening brace
        while i < len(block_lines) - 1:  # Skip closing brace
            line = block_lines[i].strip()
            match = PROP_NAME_RE.match(line)
            prop_name = match.group(1) if match else None

            if prop_name in _CATEGORY_SINGLE_LINE_PROPS:
                props[prop_name] = line
            elif prop_name == "priority":
                # priority can be `priority = 200` (single-line) or `priority = { base = 100 }` (block)
                if "{" in line:
                    block, next_i = extract_block(block_lines, i)
                    props["priority"] = block
                    i = next_i
                    continue
                else:
                    props["priority"] = line
            elif prop_name in _CATEGORY_BLOCK_PROPS:
                block, next_i = extract_block(block_lines, i)
                props[prop_name].append(block)
                i = next_i
                continue
            else:
                props["other"].append(block_lines[i])

            i += 1

        return props

    def format_block(self, props: Dict[str, Any]) -> List[str]:
        """Format decision category according to Millennium Dawn standard"""
        lines = []

        if props["id"]:
            lines.append(f"{props['id']} = {{")
        else:
            lines.append("category = {")

        for allowed in props["allowed"]:
            lines.extend(reindent_block(allowed, 1))
            lines.append("")

        if props["icon"]:
            lines.append(f"\t{props['icon']}")

        if props["picture"]:
            lines.append(f"\t{props['picture']}")

        if props["priority"]:
            if isinstance(props["priority"], list):
                lines.extend(reindent_block(props["priority"], 1))
                lines.append("")
            else:
                lines.append(f"\t{props['priority']}")

        if props["scripted_gui"]:
            lines.append(f"\t{props['scripted_gui']}")

        if props["visible_when_empty"]:
            lines.append(f"\t{props['visible_when_empty']}")

        if props["visibility_type"]:
            lines.append(f"\t{props['visibility_type']}")

        for visible in props["visible"]:
            lines.extend(reindent_block(visible, 1))
            lines.append("")

        for target_root_trigger in props["target_root_trigger"]:
            lines.extend(reindent_block(target_root_trigger, 1))
            lines.append("")

        for on_map_area in props["on_map_area"]:
            lines.extend(reindent_block(on_map_area, 1))
            lines.append("")

        if props["other"]:
            for line in props["other"]:
                if line.strip():
                    lines.append(f"\t{line.strip()}")
            lines.append("")

        # Remove trailing blank lines before closing brace
        while lines and lines[-1] == "":
            lines.pop()
        lines.append("}")

        return collapse_blank_runs(lines)


class DecisionStandardizer(BaseStandardizer):
    """Standardizer for HOI4 decisions"""

    def get_block_pattern(self) -> str:
        """Return regex pattern to identify decision blocks"""
        return r"\s*\w+_decision\s*=\s*{"

    def extract_properties(self, block_lines: List[str]) -> Dict[str, Any]:
        """Extract properties from decision block lines"""
        props: Dict[str, Any] = {
            "id": "",
            "allowed": [],
            "icon": "",
            "cost": "",
            "days_remove": "",
            "visible": [],
            "available": [],
            "complete_effect": [],
            "ai_will_do": [],
            "fire_only_once": "",
            "other": [],
        }

        i = 1  # Skip opening brace
        while i < len(block_lines) - 1:  # Skip closing brace
            line = block_lines[i].strip()
            match = PROP_NAME_RE.match(line)
            prop_name = match.group(1) if match else None

            if prop_name in _SINGLE_LINE_PROPS:
                props[prop_name] = line
            elif prop_name in _BLOCK_PROPS:
                block, next_i = extract_block(block_lines, i)
                props[prop_name].append(block)
                i = next_i
                continue
            else:
                # The decision ID is the first word of the first non-comment line.
                if not props["id"] and line and not line.startswith("#"):
                    props["id"] = line.split()[0] if line.split() else ""
                props["other"].append(block_lines[i])

            i += 1

        return props

    def format_block(self, props: Dict[str, Any]) -> List[str]:
        """Format decision according to Millennium Dawn standard"""
        lines = []

        # Decision ID (first line)
        if props["id"]:
            lines.append(f"\t{props['id']} = {{")
        else:
            lines.append("\tdecision = {")

        lines.append("")

        # 1. Allowed block (first)
        for allowed in props["allowed"]:
            lines.extend(compact_block(allowed[:]))
            lines.append("")

        # 2. Icon
        if props["icon"]:
            lines.append(f'\t\t{props["icon"]}')
            lines.append("")

        # 3. Cost and days_remove
        if props["cost"]:
            lines.append(f'\t\t{props["cost"]}')
        if props["days_remove"]:
            lines.append(f'\t\t{props["days_remove"]}')
        lines.append("")

        # 4. Visible block
        for visible in props["visible"]:
            lines.extend(compact_block(visible[:]))
            lines.append("")

        # 5. Available block
        for available in props["available"]:
            lines.extend(compact_block(available[:]))
            lines.append("")

        # 6. Complete effect (add log if missing)
        for complete_effect in props["complete_effect"]:
            if not block_has_log(complete_effect) and props["id"]:
                log_line = (
                    f'\t\t\tlog = "[GetDateText]: [Root.GetName]: '
                    f'Decision {props["id"]}"'
                )
                complete_effect = inject_log_after_brace(complete_effect, log_line)

            lines.extend(compact_block(complete_effect[:]))
            lines.append("")

        # 7. fire_only_once (use sparingly)
        if props["fire_only_once"]:
            lines.append(f'\t\t{props["fire_only_once"]}')
            lines.append("")

        # 8. AI will do (always last)
        for ai_will_do in props["ai_will_do"]:
            lines.extend(compact_block(ai_will_do[:]))
            lines.append("")

        # 9. Other properties
        if props["other"]:
            for line in props["other"]:
                if line.strip():
                    lines.append(line)
            lines.append("")

        lines.append("\t}")

        return collapse_blank_runs(lines)


def detect_file_type(input_file: str) -> BaseStandardizer:
    """Detect whether the file contains decision categories or decisions."""
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        category_count = sum(
            1 for line in lines if re.match(r"\s*\w+_category\s*=\s*\{", line)
        )
        decision_count = sum(
            1 for line in lines if re.match(r"\s*\w+_decision\s*=\s*\{", line)
        )
        if category_count > 0 and category_count >= decision_count:
            return DecisionCategoryStandardizer(verbose=False)
        return DecisionStandardizer(verbose=False)
    except Exception as e:
        log_message("WARNING", f"Failed to detect file type for {input_file}: {e}")
        return DecisionStandardizer(verbose=False)


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: standardize_decisions.py <input_file> [-o output_file] [-b] [-v]")
        sys.exit(1)

    if "--help" in sys.argv or "-h" in sys.argv:
        print("Usage: standardize_decisions.py <input_file> [-o output_file] [-b] [-v]")
        print("")
        print("Standardizes HOI4 decision and decision category files.")
        print("Detects file type automatically based on content.")
        sys.exit(0)

    parser = argparse.ArgumentParser(description="Standardize decision files")
    parser.add_argument("input_file", help="Input file to standardize")
    parser.add_argument(
        "-o", "--output", help="Output file (default: overwrites input)"
    )
    parser.add_argument(
        "-b", "--backup", action="store_true", help="Create backup before modifying"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args(sys.argv[1:])

    if not os.path.exists(args.input_file):
        log_message("ERROR", f"File '{args.input_file}' does not exist")
        sys.exit(1)

    standardizer = detect_file_type(args.input_file)
    standardizer.verbose = args.verbose

    output_file = args.output if args.output else args.input_file

    if args.backup:
        backup_file = create_backup(args.input_file)
        if not backup_file:
            sys.exit(1)

    log_message("INFO", f"Starting standardization of {args.input_file}", args.verbose)

    if standardizer.standardize_file(args.input_file, output_file):
        log_message("SUCCESS", f"Standardization completed: {output_file}")
    else:
        log_message("ERROR", "Standardization failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
