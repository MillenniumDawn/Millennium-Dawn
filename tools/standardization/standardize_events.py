#!/usr/bin/env python3

"""
Millennium Dawn Event Standardizer
Standardizes HOI4 event files according to Millennium Dawn coding standards
"""

import re
from typing import Any, Dict, List

from common_utils import BaseStandardizer, run_standardizer


class EventStandardizer(BaseStandardizer):
    """Standardizer for HOI4 events"""

    def get_block_pattern(self) -> str:
        """Return regex pattern to identify event blocks"""
        return r"\s*(country_event|province_event|unit_leader_event|news_event)\s*=\s*{"

    def extract_properties(self, block_lines: List[str]) -> Dict[str, Any]:
        """Extract properties from event block lines"""
        props = {
            "event_type": "",
            "id": "",
            "title": "",
            "desc": "",
            "picture": "",
            "is_triggered_only": "",
            "hidden": "",
            "major": "",
            "fire_only_once": "",
            "mean_time_to_happen": [],
            "trigger": [],
            "immediate": [],
            "option": [],
            "comments_after_header": [],
            "comments_after_mtth": [],
            "comments_after_trigger": [],
            "comments_after_immediate": [],
            "comments_after_options": [],
        }

        # Determine event type from first line
        first_line = block_lines[0].strip()
        if "country_event" in first_line:
            props["event_type"] = "country_event"
        elif "province_event" in first_line:
            props["event_type"] = "province_event"
        elif "unit_leader_event" in first_line:
            props["event_type"] = "unit_leader_event"
        elif "news_event" in first_line:
            props["event_type"] = "news_event"

        # Track which section we're in for comment placement
        current_section = "header"

        i = 1  # Skip opening brace
        while i < len(block_lines) - 1:  # Skip closing brace
            line = block_lines[i].strip()

            if line.startswith("id ="):
                props["id"] = line
                current_section = "header"
            elif line.startswith("title ="):
                props["title"] = line
                current_section = "header"
            elif line.startswith("desc ="):
                # Check if this is a multi-line block or single line
                if "{" in line:
                    # Multi-line block
                    block_lines_block, next_i = self.extract_block(block_lines, i)
                    props["desc"] = block_lines_block
                    i = next_i
                    current_section = "header"
                    continue
                else:
                    # Single line
                    props["desc"] = line
                    current_section = "header"
            elif line.startswith("picture ="):
                props["picture"] = line
                current_section = "header"
            elif line.startswith("is_triggered_only ="):
                props["is_triggered_only"] = line
                current_section = "header"
            elif line.startswith("hidden ="):
                props["hidden"] = line
                current_section = "header"
            elif line.startswith("major ="):
                props["major"] = line
                current_section = "header"
            elif line.startswith("fire_only_once ="):
                props["fire_only_once"] = line
                current_section = "header"

            elif line.startswith("mean_time_to_happen ="):
                block_lines_block, next_i = self.extract_block(block_lines, i)
                props["mean_time_to_happen"].append(block_lines_block)
                i = next_i
                current_section = "mtth"
                continue
            elif line.startswith("trigger ="):
                block_lines_block, next_i = self.extract_block(block_lines, i)
                props["trigger"].append(block_lines_block)
                i = next_i
                current_section = "trigger"
                continue
            elif line.startswith("immediate ="):
                block_lines_block, next_i = self.extract_block(block_lines, i)
                props["immediate"].append(block_lines_block)
                i = next_i
                current_section = "immediate"
                continue
            elif line.startswith("option ="):
                block_lines_block, next_i = self.extract_block(block_lines, i)
                props["option"].append(block_lines_block)
                i = next_i
                current_section = "options"
                continue
            else:
                # This is a comment or unrecognized line - add to current section
                if current_section == "header":
                    props["comments_after_header"].append(block_lines[i])
                elif current_section == "mtth":
                    props["comments_after_mtth"].append(block_lines[i])
                elif current_section == "trigger":
                    props["comments_after_trigger"].append(block_lines[i])
                elif current_section == "immediate":
                    props["comments_after_immediate"].append(block_lines[i])
                elif current_section == "options":
                    props["comments_after_options"].append(block_lines[i])

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
        """Format event according to Millennium Dawn standard"""
        lines = []
        lines.append(f"{props['event_type']} = {{")

        # 1. ID (first line after opening brace)
        if props["id"]:
            lines.append(f'\t{props["id"]}')

        # 2. Title and description
        if props["title"]:
            lines.append(f'\t{props["title"]}')
        if props["desc"]:
            if isinstance(props["desc"], list):
                compacted_desc = self.compact_block(props["desc"][:])
                for line in compacted_desc:
                    lines.append(line)
            else:
                lines.append(f'\t{props["desc"]}')

        # 3. Picture
        if props["picture"]:
            lines.append(f'\t{props["picture"]}')

        # 4. is_triggered_only (required for triggered events)
        if props["is_triggered_only"]:
            lines.append(f'\t{props["is_triggered_only"]}')
        elif not props["mean_time_to_happen"]:
            lines.append("\tis_triggered_only = yes")

        # 5. major flag (use sparingly)
        if props["major"]:
            lines.append(f'\t{props["major"]}')

        # 6. hidden parameter
        if props["hidden"]:
            lines.append(f'\t{props["hidden"]}')

        # 7. fire_only_once (use sparingly)
        if props["fire_only_once"]:
            lines.append(f'\t{props["fire_only_once"]}')

        lines.append("")

        # Comments after header section
        for comment in props["comments_after_header"]:
            if comment.strip():
                lines.append(comment.rstrip())

        # 8. Mean time to happen
        for mtth in props["mean_time_to_happen"]:
            compacted_mtth = self.compact_block(mtth[:])
            for line in compacted_mtth:
                lines.append(line)
            lines.append("")

        # Comments after MTTH section
        for comment in props["comments_after_mtth"]:
            if comment.strip():
                lines.append(comment.rstrip())

        # 9. Trigger
        for trigger in props["trigger"]:
            compacted_trigger = self.compact_block(trigger[:])
            for line in compacted_trigger:
                lines.append(line)
            lines.append("")

        # Comments after trigger section
        for comment in props["comments_after_trigger"]:
            if comment.strip():
                lines.append(comment.rstrip())

        # 10. Immediate effects
        for immediate in props["immediate"]:
            compacted_immediate = self.compact_block(immediate[:])
            for line in compacted_immediate:
                lines.append(line)
            lines.append("")

        # Comments after immediate section
        for comment in props["comments_after_immediate"]:
            if comment.strip():
                lines.append(comment.rstrip())

        # 11. Options
        for option in props["option"]:
            has_log = any(line.strip().startswith("log =") for line in option)

            # Only add log if there are actual effects in the option
            has_effects = any(
                line.strip()
                and line.strip() not in ("{", "}")
                and not line.strip().startswith("#")
                and not line.strip().startswith("name =")
                and not line.strip().startswith("ai_chance =")
                and not line.strip().startswith("trigger =")
                for line in option
            )

            if has_effects and not has_log and props["id"]:
                # Add log after opening brace of option
                event_id = props["id"].split("=")[1].strip()
                modified_option = []
                for j, line in enumerate(option):
                    modified_option.append(line)
                    if j == 0 and "{" in line:  # After opening brace
                        # Extract option name for log message
                        option_name = "option"
                        for opt_line in option:
                            if opt_line.strip().startswith("name ="):
                                option_name = opt_line.split("=")[1].strip()
                                break
                        modified_option.append(
                            f'\t\t\tlog = "[GetDateText]: [This.GetName]: {option_name} executed"'
                        )
                option = modified_option

            compacted_option = self.compact_block(option[:])
            for line in compacted_option:
                lines.append(line)
            lines.append("")

        # Comments after options section
        for comment in props["comments_after_options"]:
            if comment.strip():
                lines.append(comment.rstrip())
        if props["comments_after_options"]:
            lines.append("")

        lines.append("}")

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
        EventStandardizer,
        "Standardize HOI4 event files according to Millennium Dawn coding standards",
    )


if __name__ == "__main__":
    main()
