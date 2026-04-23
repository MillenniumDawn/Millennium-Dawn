#!/usr/bin/env python3

"""
Millennium Dawn Idea Standardizer
Standardizes HOI4 idea files according to Millennium Dawn coding standards
"""

import os
import re
import time
from typing import Any, Dict, List

from common_utils import PROP_NAME_RE, BaseStandardizer, run_standardizer
from shared_utils import extract_block, log_message

_SINGLE_LINE_PROPS = {"name", "picture"}

_BLOCK_PROPS = {
    "allowed",
    "allowed_civil_war",
    "cancel",
    "modifier",
    "targeted_modifier",
    "research_bonus",
    "rule",
    "equipment_bonus",
    "on_add",
    "on_remove",
}

# Blocks that get filtered out when they contain `always = no`
_ALWAYS_NO_FILTERED = {"allowed", "allowed_civil_war", "cancel"}

# Block pattern for wrapper blocks / idea blocks
_BLOCK_START_RE = re.compile(r"\s*[\w_]+\s*=\s*{")


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
        props: Dict[str, Any] = {
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
            match = PROP_NAME_RE.match(line)
            prop_name = match.group(1) if match else None

            if prop_name in _SINGLE_LINE_PROPS:
                props[prop_name] = line
            elif prop_name in _BLOCK_PROPS:
                block, next_i = extract_block(block_lines, i)
                if (
                    prop_name in _ALWAYS_NO_FILTERED
                    and self.is_performance_hurting_block(block, prop_name)
                ):
                    i = next_i
                    continue
                if prop_name == "allowed":
                    # Replace tag = TAG with original_tag = TAG (civil war safety)
                    block = [
                        re.sub(r"\btag\s*=\s*(\w+)", r"original_tag = \1", bl)
                        for bl in block
                    ]
                props[prop_name].append(block)
                i = next_i
                continue
            else:
                # Store other properties (content + comments)
                if line:
                    props["other"].append(block_lines[i])

            i += 1

        return props

    def is_empty_log_block(self, block_lines: List[str]) -> bool:
        """Check if a block is an empty log-only block (performance issue)"""
        if not block_lines:
            return True

        for line in block_lines:
            stripped = line.strip()
            if stripped in ("{", "}", "") or not stripped:
                continue
            if stripped.startswith("#"):
                continue
            if 'log = ""' in stripped or "log = ''" in stripped:
                continue
            return False

        return True

    def has_meaningful_effects(self, block_lines: List[str]) -> bool:
        """Check if a block has meaningful effects beyond just logging"""
        if not block_lines:
            return False

        for line in block_lines:
            stripped = line.strip()
            if (
                stripped in ("{", "}", "")
                or not stripped
                or stripped.startswith("#")
                or stripped.startswith("log =")
            ):
                continue
            return True

        return False

    def is_performance_hurting_block(
        self, block_lines: List[str], property_name: str
    ) -> bool:
        """Check if a block matches performance-hurting patterns to be removed"""
        if property_name not in _ALWAYS_NO_FILTERED:
            return False
        return any(
            "always = no" in line.strip() or "always=no" in line.strip()
            for line in block_lines
        )

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
            line_indent = base_indent + ("\t" * depth)

            # If this is a closing brace, decrease depth first
            if stripped == "}":
                depth = max(0, depth - 1)
                line_indent = base_indent + ("\t" * depth)

            compacted.append(line_indent + stripped)

            # Update depth based on braces in this line
            if i == 0 and "{" in stripped:
                depth += 1
            elif i > 0 and stripped.endswith("{"):
                depth += 1

        return compacted

    def _emit_lifecycle_block(
        self,
        block: List[str],
        prop_indent: str,
        idea_id: str,
        action: str,
    ) -> List[str]:
        """Emit an on_add / on_remove block, injecting a log line if there are
        meaningful effects and no existing log. Returns [] if the block is an
        empty log-only block or has no meaningful effects."""
        if self.is_empty_log_block(block):
            return []
        if not self.has_meaningful_effects(block):
            return []

        has_log = any("log =" in line for line in block)
        if not has_log and idea_id:
            log_line = (
                f'{prop_indent}\tlog = "[GetDateText]: [Root.GetName]: '
                f'Idea {idea_id} {action}"'
            )
            modified = []
            for j, line in enumerate(block):
                modified.append(line)
                if j == 0 and "{" in line:
                    modified.append(log_line)
            block = modified

        return self.compact_block(block[:], prop_indent)

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

        # 3-10. Simple blocks emitted in order
        for key in (
            "allowed",
            "allowed_civil_war",
            "cancel",
            "modifier",
            "targeted_modifier",
            "research_bonus",
            "rule",
            "equipment_bonus",
        ):
            for block in props[key]:
                lines.extend(self.compact_block(block[:], prop_indent))

        # 11. on_add (log only when making changes)
        for block in props["on_add"]:
            lines.extend(
                self._emit_lifecycle_block(block, prop_indent, props["id"], "added")
            )

        # 12. on_remove (log only when making changes)
        for block in props["on_remove"]:
            lines.extend(
                self._emit_lifecycle_block(block, prop_indent, props["id"], "removed")
            )

        # 13. Other properties (filter out commented code)
        for line in props["other"]:
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if stripped:
                lines.append(prop_indent + stripped)

        lines.append(base_indent + "}")

        # Clean up excessive blank lines - ensure exactly 1 blank line between
        # sections, no blanks at start or end.
        cleaned_lines = []
        prev_line_blank = False
        last_idx = len(lines) - 1

        for i, line in enumerate(lines):
            is_blank = line.strip() == ""

            if i == 0 or i == last_idx:
                if not is_blank:
                    cleaned_lines.append(line)
                    prev_line_blank = False
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

            elapsed_time = time.time() - self.start_time
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
        output_lines = []
        i = 0

        while i < len(lines):
            line = lines[i].rstrip()

            if _BLOCK_START_RE.match(line):
                block_name = line.split("=")[0].strip()

                if block_name in self.WRAPPER_BLOCKS:
                    log_message(
                        "DEBUG",
                        f"Found wrapper block: {block_name} at line {i+1}",
                        self.verbose,
                    )
                    output_lines.append(line)

                    block_lines, next_i = extract_block(lines, i)
                    inner_lines = block_lines[1:-1]  # Skip opening and closing braces
                    output_lines.extend(self._process_lines(inner_lines, depth + 1))

                    if block_lines:
                        output_lines.append(block_lines[-1].rstrip())

                    i = next_i
                else:
                    log_message(
                        "DEBUG", f"Found idea: {block_name} at line {i+1}", self.verbose
                    )
                    block_lines, next_i = extract_block(lines, i)

                    if block_lines:
                        props = self.extract_properties(block_lines)
                        base_indent = "\t" * depth
                        output_lines.extend(self.format_block(props, base_indent))
                        self.processed_count += 1

                        log_message(
                            "DEBUG",
                            f"Processed idea {self.processed_count}: {props.get('id', 'unknown')}",
                            self.verbose,
                        )

                    i = next_i
            else:
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
