#!/usr/bin/env python3

"""
Millennium Dawn MIO Standardizer
Standardizes HOI4 military industrial organization files according to
Millennium Dawn coding standards.
"""

from typing import Any, Dict, List

from common_utils import BaseStandardizer, run_standardizer


class MIOStandardizer(BaseStandardizer):
    """Standardizer for HOI4 military industrial organizations"""

    def get_block_pattern(self) -> str:
        """Return regex pattern to identify MIO organization blocks"""
        return r"^[A-Za-z0-9_:.@\-]+\s*=\s*{"

    def extract_properties(self, block_lines: List[str]) -> Dict[str, Any]:
        """Extract properties from a MIO block"""
        props = {
            "organization_id": "",
            "name": "",
            "allowed": [],
            "icon": [],
            "task_capacity": "",
            "equipment_type": [],
            "research_categories": [],
            "tree_header_text": [],
            "initial_trait": [],
            "traits": [],
            "other": [],
        }

        first_line = block_lines[0].strip()
        props["organization_id"] = first_line.split("=", 1)[0].strip()

        i = 1

        while i < len(block_lines) - 1:
            line = block_lines[i].strip()

            if not line:
                i += 1
                continue

            if line.startswith("name ="):
                props["name"] = line
            elif line.startswith("allowed ="):
                block, next_i = self.extract_block(block_lines, i)
                props["allowed"].append(block)
                i = next_i
                continue
            elif line.startswith("icon ="):
                if "{" in line:
                    block, next_i = self.extract_block(block_lines, i)
                    props["icon"].append(block)
                    i = next_i
                    continue
                props["icon"] = [line]
            elif line.startswith("task_capacity ="):
                props["task_capacity"] = line
            elif line.startswith("equipment_type ="):
                block, next_i = self.extract_block(block_lines, i)
                props["equipment_type"].append(block)
                i = next_i
                continue
            elif line.startswith("research_categories ="):
                block, next_i = self.extract_block(block_lines, i)
                props["research_categories"].append(block)
                i = next_i
                continue
            elif line.startswith("tree_header_text ="):
                block, next_i = self.extract_block(block_lines, i)
                props["tree_header_text"].append(block)
                i = next_i
                continue
            elif line.startswith("initial_trait ="):
                block, next_i = self.extract_block(block_lines, i)
                props["initial_trait"].append(block)
                i = next_i
                continue
            elif line.startswith("trait ="):
                block, next_i = self.extract_block(block_lines, i)
                props["traits"].append(block)
                i = next_i
                continue
            else:
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
                i += 1
                break
            elif brace_count < 0:
                break

            i += 1

        return block_lines, i

    def format_block(self, props: Dict[str, Any]) -> List[str]:
        """Format MIO according to Millennium Dawn standard"""
        lines = [f"{props['organization_id']} = {{"]

        if props["name"]:
            lines.append(f"\t{props['name']}")

        if props["allowed"]:
            self._add_blank_line_if_needed(lines)
            self._add_blocks(lines, props["allowed"])

        if props["icon"]:
            self._add_blank_line_if_needed(lines)
            self._add_blocks(lines, props["icon"])

        if props["task_capacity"]:
            self._add_blank_line_if_needed(lines)
            lines.append(f"\t{props['task_capacity']}")

        if props["equipment_type"]:
            self._add_blank_line_if_needed(lines)
            self._add_blocks(lines, props["equipment_type"])

        if props["research_categories"]:
            self._add_blank_line_if_needed(lines)
            self._add_blocks(lines, props["research_categories"])

        if props["tree_header_text"]:
            self._add_blank_line_if_needed(lines)
            self._add_blocks(lines, props["tree_header_text"])

        if props["initial_trait"]:
            self._add_blank_line_if_needed(lines)
            self._add_blocks(lines, props["initial_trait"])

        if props["traits"]:
            self._add_blank_line_if_needed(lines)
            self._add_blocks(lines, props["traits"])

        if props["other"]:
            self._add_blank_line_if_needed(lines)
            self._add_comments(lines, props["other"])

        lines.append("}")
        return self._clean_blank_lines(lines)

    def compact_block(self, block_lines: List[str]) -> List[str]:
        """Completely compact a block by removing all internal blank lines"""
        compacted = []
        for line in block_lines:
            if line.strip():
                compacted.append(line.rstrip())
        return compacted

    def _add_blocks(self, lines: List[str], blocks: List[List[str]]) -> None:
        for index, block in enumerate(blocks):
            for line in self.compact_block(block[:]):
                lines.append(line)
            if index < len(blocks) - 1:
                lines.append("")

    def _add_comments(self, lines: List[str], comments: List[str]) -> None:
        for comment in comments:
            if comment.strip():
                lines.append(comment.rstrip())

    def _add_blank_line_if_needed(self, lines: List[str]) -> None:
        if len(lines) > 1 and lines[-1].strip():
            lines.append("")

    def _clean_blank_lines(self, lines: List[str]) -> List[str]:
        cleaned_lines = []
        blank_count = 0

        for line in lines:
            if line.strip():
                blank_count = 0
                cleaned_lines.append(line)
            else:
                blank_count += 1
                if blank_count <= 1:
                    cleaned_lines.append("")

        return cleaned_lines


def main():
    run_standardizer(
        MIOStandardizer,
        "Standardize HOI4 military industrial organization files according to Millennium Dawn coding standards",
    )


if __name__ == "__main__":
    main()
