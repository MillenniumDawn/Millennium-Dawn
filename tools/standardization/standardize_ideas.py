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

    # Wrapper blocks that should be preserved, not processed
    WRAPPER_BLOCKS = {
        "ideas",
        "country",
        "hidden_ideas",
        "political_advisor",
        "theorist",
        "army_chief",
        "navy_chief",
        "air_chief",
        "high_command",
        "tank_manufacturer",
        "naval_manufacturer",
        "aircraft_manufacturer",
        "materiel_manufacturer",
        "industrial_concern",
    }

    def get_block_pattern(self) -> str:
        """Return regex pattern to identify idea blocks"""
        # Match any idea block (ID is extracted from the block name, not the pattern)
        return r"\s*[\w_]+\s*=\s*{"

    def extract_properties(self, block_lines: List[str]) -> Dict[str, Any]:
        """Extract properties from idea block lines"""
        props = {
            "id": "",
            "name": "",
            "allowed": [],
            "allowed_civil_war": [],
            "picture": "",
            "cancel": [],
            "modifier": [],
            "targeted_modifier": [],
            "research_bonus": [],
            "rule": [],
            "equipment_bonus": [],
            "on_add": [],
            "on_remove": [],
            "other": [],
        }

        # Extract ID from the opening line (e.g., "BRA_idea_higher_minimum_wage_1 = {")
        first_line = block_lines[0].strip()
        if "=" in first_line:
            props["id"] = first_line.split("=")[0].strip()

        i = 1  # Skip opening brace line
        while i < len(block_lines) - 1:  # Skip closing brace
            line = block_lines[i].strip()

            if line.startswith("name ="):
                props["name"] = line
            elif line.startswith("picture ="):
                props["picture"] = line
            elif line.startswith("allowed ="):
                block_lines_block, next_i = self.extract_block(block_lines, i)
                # Skip performance-hurting allowed = { always = no }
                if not self.is_performance_hurting_block(block_lines_block, "allowed"):
                    props["allowed"].append(block_lines_block)
                i = next_i
                continue
            elif line.startswith("allowed_civil_war ="):
                block_lines_block, next_i = self.extract_block(block_lines, i)
                props["allowed_civil_war"].append(block_lines_block)
                i = next_i
                continue
            elif line.startswith("cancel ="):
                block_lines_block, next_i = self.extract_block(block_lines, i)
                # Skip performance-hurting cancel = { always = no }
                if not self.is_performance_hurting_block(block_lines_block, "cancel"):
                    props["cancel"].append(block_lines_block)
                i = next_i
                continue
            elif line.startswith("modifier ="):
                block_lines_block, next_i = self.extract_block(block_lines, i)
                props["modifier"].append(block_lines_block)
                i = next_i
                continue
            elif line.startswith("targeted_modifier ="):
                block_lines_block, next_i = self.extract_block(block_lines, i)
                props["targeted_modifier"].append(block_lines_block)
                i = next_i
                continue
            elif line.startswith("research_bonus ="):
                block_lines_block, next_i = self.extract_block(block_lines, i)
                props["research_bonus"].append(block_lines_block)
                i = next_i
                continue
            elif line.startswith("rule ="):
                block_lines_block, next_i = self.extract_block(block_lines, i)
                props["rule"].append(block_lines_block)
                i = next_i
                continue
            elif line.startswith("equipment_bonus ="):
                block_lines_block, next_i = self.extract_block(block_lines, i)
                props["equipment_bonus"].append(block_lines_block)
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
                # Store other properties
                if line and not line.startswith("#"):
                    props["other"].append(block_lines[i])
                elif line.startswith("#"):
                    # Keep comments
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

    def is_empty_log_block(self, block_lines: List[str]) -> bool:
        """Check if a block is an empty log-only block (performance issue)"""
        if not block_lines:
            return True

        for line in block_lines:
            stripped = line.strip()
            # Skip opening/closing braces and whitespace
            if stripped in ("{", "}", "") or not stripped:
                continue
            # Skip comments
            if stripped.startswith("#"):
                continue
            # Check if it's just an empty log
            if 'log = ""' in stripped or "log = ''" in stripped:
                continue
            # If we find any other content, it's not an empty log block
            return False

        # If we only found empty logs, opening/closing braces, it's an empty log block
        return True

    def has_meaningful_effects(self, block_lines: List[str]) -> bool:
        """Check if a block has meaningful effects beyond just logging"""
        if not block_lines:
            return False

        for line in block_lines:
            stripped = line.strip()
            # Skip opening/closing braces, whitespace, comments, and log statements
            if (
                stripped in ("{", "}", "")
                or not stripped
                or stripped.startswith("#")
                or stripped.startswith("log =")
            ):
                continue
            # Found a meaningful effect
            return True

        return False

    def is_performance_hurting_block(
        self, block_lines: List[str], property_name: str
    ) -> bool:
        """Check if a block matches performance-hurting patterns to be removed"""
        if not block_lines:
            return False

        # Check for allowed = { always = no } (default, hurts performance)
        if property_name == "allowed":
            for line in block_lines:
                stripped = line.strip()
                if "always = no" in stripped or "always=no" in stripped:
                    return True

        # Check for cancel = { always = no } (checked hourly, never true)
        if property_name == "cancel":
            for line in block_lines:
                stripped = line.strip()
                if "always = no" in stripped or "always=no" in stripped:
                    return True

        return False

    def compact_block(
        self, block_lines: List[str], base_indent: str = "\t\t"
    ) -> List[str]:
        """Compact a block by removing blank lines and comments, properly nesting by brace depth"""
        if not block_lines:
            return block_lines

        compacted = []
        depth = 0

        for i, line in enumerate(block_lines):
            stripped = line.strip()
            # Skip blank lines
            if not stripped:
                continue
            # Skip commented-out code (but keep inline comments)
            if stripped.startswith("#") and i > 0:
                continue

            # Calculate indentation based on brace depth
            # First, determine the indent for this line (before processing braces)
            line_indent = base_indent + ("\t" * depth)

            # If this is a closing brace, decrease depth first
            if stripped == "}":
                depth = max(0, depth - 1)
                line_indent = base_indent + ("\t" * depth)

            # Add the line with proper indentation
            new_line = line_indent + stripped
            compacted.append(new_line)

            # Update depth based on braces in this line
            if i == 0 and "{" in stripped:
                # First line with opening brace - increase depth for next lines
                depth += 1
            elif i > 0 and stripped.endswith("{"):
                # A line that opens a new block
                depth += 1

        return compacted

    def format_block(self, props: Dict[str, Any], base_indent: str = "\t") -> List[str]:
        """Format idea according to Millennium Dawn standard"""
        lines = []

        # Idea ID (first line) - use base indent
        if props["id"]:
            lines.append(base_indent + props["id"] + " = {")
        else:
            lines.append(base_indent + "idea = {")

        # Property indent is one level deeper
        prop_indent = base_indent + "\t"

        # 1. Name (optional, first property if present)
        if props["name"]:
            lines.append(prop_indent + props["name"])

        # 2. Picture
        if props["picture"]:
            lines.append(prop_indent + props["picture"])

        # 3. allowed (only if not performance-hurting)
        for allowed in props["allowed"]:
            compacted_allowed = self.compact_block(allowed[:], prop_indent)
            for line in compacted_allowed:
                lines.append(line)

        # 4. allowed_civil_war (include for civil war tags)
        for allowed_civil_war in props["allowed_civil_war"]:
            compacted_civil_war = self.compact_block(allowed_civil_war[:], prop_indent)
            for line in compacted_civil_war:
                lines.append(line)

        # 5. cancel (only if not performance-hurting)
        for cancel in props["cancel"]:
            compacted_cancel = self.compact_block(cancel[:], prop_indent)
            for line in compacted_cancel:
                lines.append(line)

        # 6. Modifier block
        for modifier in props["modifier"]:
            compacted_modifier = self.compact_block(modifier[:], prop_indent)
            for line in compacted_modifier:
                lines.append(line)

        # 7. Targeted modifier block
        for targeted_modifier in props["targeted_modifier"]:
            compacted_targeted = self.compact_block(targeted_modifier[:], prop_indent)
            for line in compacted_targeted:
                lines.append(line)

        # 8. Research bonus block
        for research_bonus in props["research_bonus"]:
            compacted_research = self.compact_block(research_bonus[:], prop_indent)
            for line in compacted_research:
                lines.append(line)

        # 9. Rule block
        for rule in props["rule"]:
            compacted_rule = self.compact_block(rule[:], prop_indent)
            for line in compacted_rule:
                lines.append(line)

        # 10. Equipment bonus (for MIO ideas)
        for equipment_bonus in props["equipment_bonus"]:
            compacted_equipment = self.compact_block(equipment_bonus[:], prop_indent)
            for line in compacted_equipment:
                lines.append(line)

        # 11. on_add (log only when making changes)
        for on_add in props["on_add"]:
            # Check if this is an empty log-only block (performance issue)
            is_empty_log = self.is_empty_log_block(on_add)
            if is_empty_log:
                continue  # Skip empty log-only blocks

            has_log = any("log =" in line for line in on_add)
            has_effects = self.has_meaningful_effects(on_add)

            if has_effects:
                if not has_log and props["id"]:
                    # Add log after opening brace if there are effects
                    idea_id = props["id"]
                    modified_on_add = []
                    for j, line in enumerate(on_add):
                        modified_on_add.append(line)
                        if j == 0 and "{" in line:  # After opening brace
                            modified_on_add.append(
                                f'{prop_indent}\tlog = "[GetDateText]: [Root.GetName]: Idea {idea_id} added"'
                            )
                    on_add = modified_on_add

                compacted_on_add = self.compact_block(on_add[:], prop_indent)
                for line in compacted_on_add:
                    lines.append(line)

        # 12. on_remove (log only when making changes)
        for on_remove in props["on_remove"]:
            # Check if this is an empty log-only block (performance issue)
            is_empty_log = self.is_empty_log_block(on_remove)
            if is_empty_log:
                continue  # Skip empty log-only blocks

            has_log = any("log =" in line for line in on_remove)
            has_effects = self.has_meaningful_effects(on_remove)

            if has_effects:
                if not has_log and props["id"]:
                    # Add log after opening brace if there are effects
                    idea_id = props["id"]
                    modified_on_remove = []
                    for j, line in enumerate(on_remove):
                        modified_on_remove.append(line)
                        if j == 0 and "{" in line:  # After opening brace
                            modified_on_remove.append(
                                f'{prop_indent}\tlog = "[GetDateText]: [Root.GetName]: Idea {idea_id} removed"'
                            )
                    on_remove = modified_on_remove

                compacted_on_remove = self.compact_block(on_remove[:], prop_indent)
                for line in compacted_on_remove:
                    lines.append(line)

        # 13. Other properties (filter out commented code)
        if props["other"]:
            for line in props["other"]:
                line_stripped = line.strip()
                # Skip commented-out code
                if line_stripped.startswith("#"):
                    continue
                # Only add non-empty lines
                if line.strip():
                    # Re-indent the line to match our base indent
                    lines.append(prop_indent + line_stripped)

        # Don't add allowed = { always = no } (it's the default and hurts performance)
        # This is now filtered in the extraction phase

        # Don't add cancel = { always = no } (checked hourly, never true)
        # This is now filtered in the extraction phase

        lines.append(base_indent + "}")

        # Clean up excessive blank lines - ensure exactly 1 blank line between sections
        cleaned_lines = []
        prev_line_blank = False

        for i, line in enumerate(lines):
            is_blank = line.strip() == ""
            is_first_line = i == 0
            is_last_line = i == len(lines) - 1

            # Don't add blank lines at the start or end
            if is_first_line or is_last_line:
                if not is_blank:
                    cleaned_lines.append(line)
                    prev_line_blank = False
            # Only add one blank line between sections
            elif is_blank:
                if not prev_line_blank:
                    cleaned_lines.append("")
                prev_line_blank = True
            else:
                cleaned_lines.append(line)
                prev_line_blank = False

        return cleaned_lines

    def standardize_file(self, input_file: str, output_file: str) -> bool:
        """Standardize ideas file by handling nested structure properly"""
        import os
        import re
        import time

        from shared_utils import extract_block, log_message

        self.start_time = time.time()
        log_message("INFO", f"Starting standardization of {input_file}", self.verbose)

        if not os.path.exists(input_file):
            log_message("ERROR", f"Input file not found: {input_file}")
            return False

        try:
            with open(input_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            log_message(
                "INFO", f"Read {len(lines)} lines from {input_file}", self.verbose
            )
        except Exception as e:
            log_message("ERROR", f"Failed to read {input_file}: {e}")
            return False

        output_lines = self._process_lines(lines, depth=0)

        try:
            with open(output_file, "w", encoding="utf-8") as f:
                for line in output_lines:
                    f.write(line + "\n")

            end_time = time.time()
            elapsed_time = end_time - self.start_time

            if elapsed_time < 60:
                time_str = f"{elapsed_time:.2f} seconds"
            else:
                minutes = int(elapsed_time // 60)
                seconds = elapsed_time % 60
                time_str = f"{minutes}m {seconds:.2f}s"

            log_message("SUCCESS", f"Standardization completed in {time_str}")
            log_message("SUCCESS", f"Processed {self.processed_count} ideas")
            log_message("SUCCESS", f"Output written to: {output_file}")

        except Exception as e:
            log_message("ERROR", f"Failed to write {output_file}: {e}")
            return False

        return True

    def _process_lines(self, lines: List[str], depth: int) -> List[str]:
        """Recursively process lines, handling nested structures"""
        import re

        from shared_utils import extract_block, log_message

        output_lines = []
        i = 0

        while i < len(lines):
            line = lines[i].rstrip()
            stripped = line.strip()

            # Check if this line starts a block
            if re.match(r"\s*[\w_]+\s*=\s*{", line):
                # Extract the block name
                block_name = line.split("=")[0].strip()

                # Check if this is a wrapper block or an actual idea
                if block_name in self.WRAPPER_BLOCKS:
                    # This is a wrapper block - preserve it and process its contents
                    log_message(
                        "DEBUG",
                        f"Found wrapper block: {block_name} at line {i+1}",
                        self.verbose,
                    )

                    # Add the opening line
                    output_lines.append(line)

                    # Extract the block content (without the opening/closing braces)
                    block_lines, next_i = extract_block(lines, i)

                    # Process the inner content recursively
                    inner_lines = block_lines[
                        1:-1
                    ]  # Skip opening and closing brace lines
                    processed_inner = self._process_lines(inner_lines, depth + 1)

                    # Add processed inner content
                    output_lines.extend(processed_inner)

                    # Add the closing brace (from the original)
                    if block_lines:
                        output_lines.append(block_lines[-1].rstrip())

                    i = next_i
                else:
                    # This is an actual idea - process it
                    log_message(
                        "DEBUG", f"Found idea: {block_name} at line {i+1}", self.verbose
                    )

                    block_lines, next_i = extract_block(lines, i)

                    if block_lines:
                        props = self.extract_properties(block_lines)

                        # Calculate base indentation from depth
                        # depth=2 means we're inside ideas{} and country{}, so use 2 tabs
                        base_indent = "\t" * depth
                        formatted_lines = self.format_block(props, base_indent)

                        output_lines.extend(formatted_lines)
                        self.processed_count += 1

                        log_message(
                            "DEBUG",
                            f"Processed idea {self.processed_count}: {props.get('id', 'unknown')}",
                            self.verbose,
                        )

                    i = next_i
            else:
                # Not a block start - preserve the line as-is
                output_lines.append(line)
                i += 1

        return output_lines


def main():
    run_standardizer(
        IdeaStandardizer,
        "Standardize HOI4 idea files according to Millennium Dawn coding standards",
    )


if __name__ == "__main__":
    main()
