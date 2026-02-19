#!/usr/bin/env python3

"""
Millennium Dawn Decision Standardizer
Standardizes HOI4 decision files according to Millennium Dawn coding standards
"""

import re
from typing import Any, Dict, List

from common_utils import BaseStandardizer, run_standardizer


class DecisionStandardizer(BaseStandardizer):
    """Standardizer for HOI4 decisions"""

    def get_block_pattern(self) -> str:
        """Return regex pattern to identify decision blocks"""
        return r"\s*\w+_decision\s*=\s*{"

    def extract_properties(self, block_lines: List[str]) -> Dict[str, Any]:
        """Extract properties from decision block lines"""
        props = {
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

            if line.startswith("cost ="):
                props["cost"] = line
            elif line.startswith("days_remove ="):
                props["days_remove"] = line
            elif line.startswith("fire_only_once ="):
                props["fire_only_once"] = line
            elif line.startswith("icon ="):
                props["icon"] = line

            elif line.startswith("allowed ="):
                block_lines_block, next_i = self.extract_block(block_lines, i)
                props["allowed"].append(block_lines_block)
                i = next_i
                continue
            elif line.startswith("visible ="):
                block_lines_block, next_i = self.extract_block(block_lines, i)
                props["visible"].append(block_lines_block)
                i = next_i
                continue
            elif line.startswith("available ="):
                block_lines_block, next_i = self.extract_block(block_lines, i)
                props["available"].append(block_lines_block)
                i = next_i
                continue
            elif line.startswith("complete_effect ="):
                block_lines_block, next_i = self.extract_block(block_lines, i)
                props["complete_effect"].append(block_lines_block)
                i = next_i
                continue
            elif line.startswith("ai_will_do ="):
                block_lines_block, next_i = self.extract_block(block_lines, i)
                props["ai_will_do"].append(block_lines_block)
                i = next_i
                continue
            else:
                # Other content (including the decision ID which is the first word)
                if not props["id"] and line and not line.startswith("#"):
                    # Extract decision ID from the first non-comment line
                    props["id"] = line.split()[0] if line.split() else ""
                props["other"].append(block_lines[i])

            i += 1

        return props

    def extract_block(
        self, lines: List[str], start_index: int
    ) -> tuple[List[str], int]:
        """Extract a multi-line block by counting braces"""
        if start_index >= len(lines):
            return [], start_index

        block_lines = []
        brace_count = 0
        i = start_index

        while i < len(lines):
            line = lines[i]
            block_lines.append(line)

            brace_count += line.count("{") - line.count("}")

            if brace_count == 0 and "{" in lines[start_index]:
                # We've closed all braces, block is complete
                i += 1
                break
            elif brace_count < 0:
                # More closing than opening braces - malformed
                break

            i += 1

        return block_lines, i

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
            compacted_allowed = self.compact_block(allowed[:])
            for line in compacted_allowed:
                lines.append(line)
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
            compacted_visible = self.compact_block(visible[:])
            for line in compacted_visible:
                lines.append(line)
            lines.append("")

        # 5. Available block
        for available in props["available"]:
            compacted_available = self.compact_block(available[:])
            for line in compacted_available:
                lines.append(line)
            lines.append("")

        # 6. Complete effect (add log if missing)
        for complete_effect in props["complete_effect"]:
            has_log = any("log =" in line for line in complete_effect)

            if not has_log and props["id"]:
                # Add log after opening brace
                decision_id = props["id"]
                modified_effect = []
                for j, line in enumerate(complete_effect):
                    modified_effect.append(line)
                    if j == 0 and "{" in line:  # After opening brace
                        modified_effect.append(
                            f'\t\t\tlog = "[GetDateText]: [Root.GetName]: Decision {decision_id}"'
                        )
                complete_effect = modified_effect

            compacted_effect = self.compact_block(complete_effect[:])
            for line in compacted_effect:
                lines.append(line)
            lines.append("")

        # 7. fire_only_once (use sparingly)
        if props["fire_only_once"]:
            lines.append(f'\t\t{props["fire_only_once"]}')
            lines.append("")

        # 8. AI will do (always last)
        for ai_will_do in props["ai_will_do"]:
            compacted_ai = self.compact_block(ai_will_do[:])
            for line in compacted_ai:
                lines.append(line)
            lines.append("")

        # 9. Other properties
        if props["other"]:
            for line in props["other"]:
                if line.strip():
                    lines.append(line)
            if props["other"]:
                lines.append("")

        lines.append("\t}")

        # Clean up excessive blank lines
        cleaned_lines = []
        blank_count = 0

        for line in lines:
            if line.strip() == "":
                blank_count += 1
                if blank_count <= 1:  # Only allow 1 consecutive blank line
                    cleaned_lines.append(line)
            else:
                blank_count = 0
                cleaned_lines.append(line)

        return cleaned_lines

    def compact_block(self, block_lines: List[str]) -> List[str]:
        """Completely compact a block by removing all internal blank lines"""
        if not block_lines:
            return block_lines

        compacted = []
        for line in block_lines:
            stripped = line.strip()
            if stripped:
                compacted.append(line.rstrip())

        return compacted


def main():
    run_standardizer(
        DecisionStandardizer,
        "Standardize HOI4 decision files according to Millennium Dawn coding standards",
    )


if __name__ == "__main__":
    main()
