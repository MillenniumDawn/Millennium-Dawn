#!/usr/bin/env python3

"""
Millennium Dawn Idea Standardizer
Standardizes HOI4 idea files according to Millennium Dawn coding standards
"""

import re
from typing import Any, Dict, List

from common_utils import BaseStandardizer, run_standardizer


class IdeaStandardizer(BaseStandardizer):
    """Standardizer for HOI4 ideas"""

    def get_block_pattern(self) -> str:
        """Return regex pattern to identify idea blocks"""
        return r"\s*\w+_idea\s*=\s*{"

    def extract_properties(self, block_lines: List[str]) -> Dict[str, Any]:
        """Extract properties from idea block lines"""
        props = {
            "id": "",
            "name": "",
            "allowed_civil_war": [],
            "picture": "",
            "modifier": [],
            "on_add": [],
            "on_remove": [],
            "other": [],
        }

        i = 1  # Skip opening brace
        while i < len(block_lines) - 1:  # Skip closing brace
            line = block_lines[i].strip()

            if line.startswith("name ="):
                props["name"] = line
            elif line.startswith("picture ="):
                props["picture"] = line

            elif line.startswith("allowed_civil_war ="):
                block_lines_block, next_i = self.extract_block(block_lines, i)
                props["allowed_civil_war"].append(block_lines_block)
                i = next_i
                continue
            elif line.startswith("modifier ="):
                block_lines_block, next_i = self.extract_block(block_lines, i)
                props["modifier"].append(block_lines_block)
                i = next_i
                continue
            elif line.startswith("on_add ="):
                block_lines_block, next_i = self.extract_block(block_lines, i)
                props["on_add"].append(block_lines_block)
                i = next_i
                continue
            elif line.startswith("on_remove ="):
                block_lines_block, next_i = self.extract_block(block_lines, i)
                props["on_remove"].append(block_lines_block)
                i = next_i
                continue
            else:
                # Other content (including the idea ID which is the first word)
                if not props["id"] and line and not line.startswith("#"):
                    # Extract idea ID from the first non-comment line
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
        """Format idea according to Millennium Dawn standard"""
        lines = []

        # Idea ID (first line)
        if props["id"]:
            lines.append(f"\t{props['id']} = {{")
        else:
            lines.append("\tidea = {")

        lines.append("")

        # 1. Name (first property)
        if props["name"]:
            lines.append(f'\t\t{props["name"]}')
            lines.append("")

        # 2. allowed_civil_war (include for civil war tags)
        for allowed_civil_war in props["allowed_civil_war"]:
            compacted_allowed = self.compact_block(allowed_civil_war[:])
            for line in compacted_allowed:
                lines.append(line)
            lines.append("")

        # 3. Picture
        if props["picture"]:
            lines.append(f'\t\t{props["picture"]}')
            lines.append("")

        # 4. Modifier block
        for modifier in props["modifier"]:
            compacted_modifier = self.compact_block(modifier[:])
            for line in compacted_modifier:
                lines.append(line)
            lines.append("")

        # 5. on_add (log only when making changes)
        for on_add in props["on_add"]:
            has_log = any("log =" in line for line in on_add)
            has_effects = any(
                line.strip()
                and line.strip() not in ("{", "}")
                and not line.strip().startswith("#")
                and not line.strip().startswith("log =")
                for line in on_add
            )

            if has_effects:
                if not has_log and props["id"]:
                    # Add log after opening brace if there are effects
                    idea_id = props["id"]
                    modified_on_add = []
                    for j, line in enumerate(on_add):
                        modified_on_add.append(line)
                        if j == 0 and "{" in line:  # After opening brace
                            modified_on_add.append(
                                f'\t\t\tlog = "[GetDateText]: [Root.GetName]: Idea {idea_id} added"'
                            )
                    on_add = modified_on_add

                compacted_on_add = self.compact_block(on_add[:])
                for line in compacted_on_add:
                    lines.append(line)
                lines.append("")

        # 6. on_remove (log only when making changes)
        for on_remove in props["on_remove"]:
            has_log = any("log =" in line for line in on_remove)
            has_effects = any(
                line.strip()
                and line.strip() not in ("{", "}")
                and not line.strip().startswith("#")
                and not line.strip().startswith("log =")
                for line in on_remove
            )

            if has_effects:
                if not has_log and props["id"]:
                    # Add log after opening brace if there are effects
                    idea_id = props["id"]
                    modified_on_remove = []
                    for j, line in enumerate(on_remove):
                        modified_on_remove.append(line)
                        if j == 0 and "{" in line:  # After opening brace
                            modified_on_remove.append(
                                f'\t\t\tlog = "[GetDateText]: [Root.GetName]: Idea {idea_id} removed"'
                            )
                    on_remove = modified_on_remove

                compacted_on_remove = self.compact_block(on_remove[:])
                for line in compacted_on_remove:
                    lines.append(line)
                lines.append("")

        # 7. Other properties (remove performance-hurting ones)
        if props["other"]:
            for line in props["other"]:
                line_stripped = line.strip()
                # Remove performance-hurting properties
                if (
                    line_stripped.startswith("allowed = { always = no }")
                    or line_stripped.startswith("cancel = { always = no }")
                    or (
                        line_stripped.startswith("on_add = {")
                        and 'log = ""' in line_stripped
                    )
                ):
                    continue  # Skip these performance-hurting properties

                if line.strip():  # Only add non-empty lines
                    lines.append(line)

            # Add blank line after other properties if they exist and we kept any
            if any(
                line.strip()
                and not (
                    line.strip().startswith("allowed = { always = no }")
                    or line.strip().startswith("cancel = { always = no }")
                    or (
                        line.strip().startswith("on_add = {")
                        and 'log = ""' in line.strip()
                    )
                )
                for line in props["other"]
            ):
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
        IdeaStandardizer,
        "Standardize HOI4 idea files according to Millennium Dawn coding standards",
    )


if __name__ == "__main__":
    main()
