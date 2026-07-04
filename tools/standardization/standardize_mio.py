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

    MANUFACTURER_CALLBACK_NAMES = (
        "on_design_team_assigned_to_tech",
        "on_design_team_assigned_to_variant",
        "on_industrial_manufacturer_assigned",
        "on_tech_research_cancelled",
        "on_tech_research_completed",
        "on_industrial_manufacturer_unassigned",
    )

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
            "include": "",
            "task_capacity": "",
            "available": [],
            "visible": [],
            "on_callbacks": [],
            "ai_will_do": [],
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
            elif line.startswith("available ="):
                block, next_i = self.extract_block(block_lines, i)
                props["available"].append(block)
                i = next_i
                continue
            elif line.startswith("visible ="):
                block, next_i = self.extract_block(block_lines, i)
                props["visible"].append(block)
                i = next_i
                continue
            elif line.startswith("icon ="):
                if "{" in line:
                    block, next_i = self.extract_block(block_lines, i)
                    props["icon"].append(block)
                    i = next_i
                    continue
                props["icon"].append([f"\t{line}"])
            elif line.startswith("include ="):
                props["include"] = line
            elif line.startswith("ai_will_do ="):
                block, next_i = self.extract_block(block_lines, i)
                props["ai_will_do"].append(block)
                i = next_i
                continue
            elif line.startswith("task_capacity ="):
                props["task_capacity"] = line
            elif any(
                line.startswith(f"{name} =")
                for name in self.MANUFACTURER_CALLBACK_NAMES
            ):
                callback_name = line.split("=", 1)[0].strip()
                block, next_i = self.extract_block(block_lines, i)
                props["on_callbacks"].append((callback_name, block))
                i = next_i
                continue
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

        if props["allowed"]:
            lines.extend(self._format_allowed_blocks(props["allowed"]))

        if props["name"]:
            lines.append(f"\t{props['name']}")

        if props["icon"]:
            self._add_blocks(lines, props["icon"])

        if props["include"]:
            lines.append(f"\t{props['include']}")

        if props["task_capacity"]:
            self._add_blank_line_if_needed(lines)
            lines.append(f"\t{props['task_capacity']}")
            lines.append("")

        if props["available"]:
            for index, block in enumerate(props["available"]):
                self._add_blank_line_if_needed(lines)
                lines.extend(self.format_nested_block(block, "\t"))
                if index < len(props["available"]) - 1:
                    lines.append("")
            lines.append("")

        if props["visible"]:
            for index, block in enumerate(props["visible"]):
                self._add_blank_line_if_needed(lines)
                lines.extend(self.format_nested_block(block, "\t"))
                if index < len(props["visible"]) - 1:
                    lines.append("")
            lines.append("")

        if props["on_callbacks"]:
            for _name, block in props["on_callbacks"]:
                self._add_blank_line_if_needed(lines)
                lines.extend(self.format_nested_block(block, "\t"))
                lines.append("")

        if props["other"]:
            self._add_blank_line_if_needed(lines)
            self._add_comments(lines, props["other"])
            lines.append("")

        if props["ai_will_do"]:
            self._add_blank_line_if_needed(lines)
            self._add_blocks(lines, props["ai_will_do"])
            lines.append("")

        if props["equipment_type"]:
            self._add_blank_line_if_needed(lines)
            self._add_token_list_blocks(
                lines, props["equipment_type"], "equipment_type", "\t"
            )
            lines.append("")

        if props["research_categories"]:
            self._add_blank_line_if_needed(lines)
            self._add_token_list_blocks(
                lines, props["research_categories"], "research_categories", "\t"
            )
            lines.append("")

        if props["tree_header_text"]:
            self._add_blank_line_if_needed(lines)
            self._add_blocks(lines, props["tree_header_text"])
            lines.append("")

        if props["initial_trait"]:
            self._add_blank_line_if_needed(lines)
            self._add_blocks(lines, props["initial_trait"], is_trait=True)
            lines.append("")

        if props["traits"]:
            self._add_blank_line_if_needed(lines)
            self._add_blocks(lines, props["traits"], is_trait=True)
            lines.append("")

        lines.append("}")
        return self._clean_blank_lines(lines)

    def compact_block(self, block_lines: List[str]) -> List[str]:
        """Completely compact a block by removing all internal blank lines"""
        compacted = []
        for line in block_lines:
            if line.strip():
                compacted.append(line.rstrip())
        return compacted

    def format_nested_block(
        self, block_lines: List[str], base_indent: str
    ) -> List[str]:
        """Re-emit a parsed block at base_indent, recomputing each inner line's
        indent from running brace depth. Drops blank lines and trailing whitespace."""
        result: List[str] = []
        depth = 0
        for line in block_lines:
            stripped = line.strip()
            if not stripped:
                continue
            leading_closes = 0
            for ch in stripped:
                if ch == "}":
                    leading_closes += 1
                elif not ch.isspace():
                    break
            emit_depth = max(0, depth - leading_closes)
            result.append(base_indent + ("\t" * emit_depth) + stripped)
            depth = max(0, depth + stripped.count("{") - stripped.count("}"))
        return result

    def normalize_on_complete(self, block_lines: List[str]) -> List[str]:
        """Normalize on_complete blocks to use expenditure_for_mio_upgrade = yes, preserving other content"""
        content = " ".join(line.strip() for line in block_lines if line.strip())
        if not content.startswith("on_complete"):
            return block_lines
        if (
            "free_trait_picks" not in content
            and "expenditure_for_mio_upgrade" not in content
        ):
            return block_lines

        indent = block_lines[0][: len(block_lines[0]) - len(block_lines[0].lstrip())]
        inner_indent = indent + "\t"

        # Collect non-expenditure inner content
        other_lines = []
        i = 1
        while i < len(block_lines) - 1:
            line = block_lines[i]
            stripped = line.strip()
            if not stripped:
                i += 1
                continue

            if stripped.startswith("expenditure_for_mio_upgrade"):
                i += 1
            elif "{" in stripped:
                sub, next_i = self.extract_block(block_lines, i)
                sub_content = " ".join(l.strip() for l in sub if l.strip())
                if (
                    "free_trait_picks" in sub_content
                    or "small_expenditure" in sub_content
                ):
                    i = next_i
                else:
                    other_lines.extend(sub)
                    i = next_i
            else:
                other_lines.append(line)
                i += 1

        if not other_lines:
            return [f"{indent}on_complete = {{ expenditure_for_mio_upgrade = yes }}"]

        result = [f"{indent}on_complete = {{"]
        for line in other_lines:
            if line.strip():
                result.append(line.rstrip())
        result.append(f"{inner_indent}expenditure_for_mio_upgrade = yes")
        result.append(f"{indent}}}")
        return result

    def _normalize_token_list(
        self, block_lines: List[str], key: str, indent: str
    ) -> List[str]:
        """Format `key = { tokens }` as single-line for 1 token, multi-line for 2+.
        Falls back to compact_block if the block contains comments (to preserve them).
        """
        for line in block_lines:
            if line.strip().startswith("#"):
                return self.compact_block(block_lines)

        content_tokens = []
        for line in block_lines:
            stripped = line.strip()
            if not stripped or stripped in ("{", "}"):
                continue
            if stripped.startswith(key):
                if "{" in stripped:
                    inner = stripped.split("{", 1)[1]
                    if "}" in inner:
                        inner = inner.rsplit("}", 1)[0]
                    if inner.strip():
                        content_tokens.extend(inner.split())
            elif stripped != "}":
                content_tokens.extend(stripped.rstrip("}").split())

        if not content_tokens:
            return self.compact_block(block_lines)
        if len(content_tokens) == 1:
            return [f"{indent}{key} = {{ {content_tokens[0]} }}"]

        inner_indent = indent + "\t"
        result = [f"{indent}{key} = {{"]
        for tok in content_tokens:
            result.append(f"{inner_indent}{tok}")
        result.append(f"{indent}}}")
        return result

    def _normalize_modifier_block(
        self, block_lines: List[str], key: str, indent: str
    ) -> List[str]:
        """Format `key = { stat = value ... }` as single-line for 1 modifier, multi-line for 2+.
        Falls back to compact_block if the block contains comments or nested blocks.
        """
        for line in block_lines:
            if line.strip().startswith("#"):
                return self.compact_block(block_lines)

        full = " ".join(l.strip() for l in block_lines if l.strip())
        if not full.startswith(key) or "{" not in full or "}" not in full:
            return self.compact_block(block_lines)

        inner = full.split("{", 1)[1].rsplit("}", 1)[0].strip()
        if "{" in inner or "}" in inner:
            return self.compact_block(block_lines)

        tokens = inner.split()
        if not tokens:
            return self.compact_block(block_lines)
        if len(tokens) % 3 != 0:
            return self.compact_block(block_lines)

        pairs = []
        for j in range(0, len(tokens), 3):
            if tokens[j + 1] != "=":
                return self.compact_block(block_lines)
            pairs.append(f"{tokens[j]} = {tokens[j + 2]}")

        if len(pairs) == 1:
            return [f"{indent}{key} = {{ {pairs[0]} }}"]

        inner_indent = indent + "\t"
        result = [f"{indent}{key} = {{"]
        for p in pairs:
            result.append(f"{inner_indent}{p}")
        result.append(f"{indent}}}")
        return result

    def _merge_and_normalize_modifier_blocks(
        self, blocks: List[List[str]], key: str, indent: str
    ) -> List[str]:
        """Merge multiple blocks with the same key into a single block, deduping
        modifiers (last value wins). Falls back to per-block normalization if any
        block contains comments or nested blocks.
        """
        if not blocks:
            return []
        if len(blocks) == 1:
            return self._normalize_modifier_block(blocks[0], key, indent)

        merged_pairs: Dict[str, str] = {}
        for block in blocks:
            for line in block:
                if line.strip().startswith("#"):
                    return self._fallback_concat_modifier_blocks(blocks, key, indent)

            full = " ".join(l.strip() for l in block if l.strip())
            if not full.startswith(key) or "{" not in full or "}" not in full:
                return self._fallback_concat_modifier_blocks(blocks, key, indent)

            inner = full.split("{", 1)[1].rsplit("}", 1)[0].strip()
            if "{" in inner or "}" in inner:
                return self._fallback_concat_modifier_blocks(blocks, key, indent)

            tokens = inner.split()
            if not tokens:
                continue
            if len(tokens) % 3 != 0:
                return self._fallback_concat_modifier_blocks(blocks, key, indent)

            for j in range(0, len(tokens), 3):
                if tokens[j + 1] != "=":
                    return self._fallback_concat_modifier_blocks(blocks, key, indent)
                merged_pairs[tokens[j]] = tokens[j + 2]

        if not merged_pairs:
            return self._normalize_modifier_block(blocks[0], key, indent)

        if len(merged_pairs) == 1:
            stat, value = next(iter(merged_pairs.items()))
            return [f"{indent}{key} = {{ {stat} = {value} }}"]

        inner_indent = indent + "\t"
        result = [f"{indent}{key} = {{"]
        for stat, value in merged_pairs.items():
            result.append(f"{inner_indent}{stat} = {value}")
        result.append(f"{indent}}}")
        return result

    def _fallback_concat_modifier_blocks(
        self, blocks: List[List[str]], key: str, indent: str
    ) -> List[str]:
        """Concat each block separately when merge isn't safe (comments/nested)."""
        result: List[str] = []
        for block in blocks:
            result.extend(self._normalize_modifier_block(block, key, indent))
        return result

    def normalize_mutually_exclusive(
        self, block_lines: List[str], inner_indent: str
    ) -> List[str]:
        """Format mutually_exclusive based on token count (single-line for 1, multi-line for 2+)"""
        return self._normalize_token_list(
            block_lines, "mutually_exclusive", inner_indent
        )

    def normalize_limit_to_equipment_type(
        self, block_lines: List[str], inner_indent: str
    ) -> List[str]:
        """Format limit_to_equipment_type based on token count (single-line for 1, multi-line for 2+)"""
        return self._normalize_token_list(
            block_lines, "limit_to_equipment_type", inner_indent
        )

    def format_trait_block(self, block_lines: List[str]) -> List[str]:
        """Format a trait block with blank lines between logical sections"""
        if not block_lines:
            return block_lines

        outer_indent = block_lines[0][
            : len(block_lines[0]) - len(block_lines[0].lstrip())
        ]
        inner_indent = outer_indent + "\t"

        sections: Dict[str, List[str]] = {
            "identity": [],
            "available": [],
            "visible": [],
            "parents": [],
            "position": [],
            "mutually_exclusive": [],
            "limit": [],
            "equipment_bonus": [],
            "production_bonus": [],
            "organization_modifier": [],
            "on_complete": [],
            "ai_will_do": [],
            "other": [],
        }
        modifier_blocks: Dict[str, List[List[str]]] = {
            "equipment_bonus": [],
            "production_bonus": [],
            "organization_modifier": [],
        }

        i = 1
        while i < len(block_lines) - 1:
            line = block_lines[i]
            stripped = line.strip()
            if not stripped:
                i += 1
                continue

            if stripped.startswith(
                ("token =", "name =", "icon =", "special_trait_background =")
            ):
                if "{" in stripped:
                    sub, i = self.extract_block(block_lines, i)
                    sections["identity"].extend(self.compact_block(sub))
                else:
                    sections["identity"].append(f"{inner_indent}{stripped}")
                    i += 1
            elif stripped.startswith("available ="):
                sub, i = self.extract_block(block_lines, i)
                sections["available"].extend(
                    self.format_nested_block(sub, inner_indent)
                )
            elif stripped.startswith("visible ="):
                sub, i = self.extract_block(block_lines, i)
                sections["visible"].extend(self.format_nested_block(sub, inner_indent))
            elif stripped.startswith(("all_parents =", "any_parent =", "parent =")):
                key_name = stripped.split("=", 1)[0].strip()
                if "{" in stripped:
                    sub, i = self.extract_block(block_lines, i)
                    sections["parents"].extend(
                        self._normalize_token_list(sub, key_name, inner_indent)
                    )
                else:
                    sections["parents"].append(f"{inner_indent}{stripped}")
                    i += 1
            elif stripped.startswith(("position =", "relative_position_id =")):
                if "{" in stripped:
                    sub, i = self.extract_block(block_lines, i)
                    sections["position"].extend(self.compact_block(sub))
                else:
                    sections["position"].append(f"{inner_indent}{stripped}")
                    i += 1
            elif stripped.startswith("mutually_exclusive ="):
                sub, i = self.extract_block(block_lines, i)
                sections["mutually_exclusive"].extend(
                    self.normalize_mutually_exclusive(sub, inner_indent)
                )
            elif stripped.startswith("limit_to_equipment_type ="):
                sub, i = self.extract_block(block_lines, i)
                sections["limit"].extend(
                    self.normalize_limit_to_equipment_type(sub, inner_indent)
                )
            elif stripped.startswith("equipment_bonus ="):
                sub, i = self.extract_block(block_lines, i)
                modifier_blocks["equipment_bonus"].append(sub)
            elif stripped.startswith("production_bonus ="):
                sub, i = self.extract_block(block_lines, i)
                modifier_blocks["production_bonus"].append(sub)
            elif stripped.startswith("organization_modifier ="):
                sub, i = self.extract_block(block_lines, i)
                modifier_blocks["organization_modifier"].append(sub)
            elif stripped.startswith("on_complete ="):
                sub, i = self.extract_block(block_lines, i)
                sections["on_complete"].extend(self.normalize_on_complete(sub))
            elif stripped.startswith("ai_will_do ="):
                sub, i = self.extract_block(block_lines, i)
                sections["ai_will_do"].extend(self.compact_block(sub))
            else:
                sections["other"].append(f"{inner_indent}{stripped}")
                i += 1

        for mod_key, blocks in modifier_blocks.items():
            if blocks:
                sections[mod_key].extend(
                    self._merge_and_normalize_modifier_blocks(
                        blocks, mod_key, inner_indent
                    )
                )

        result = [block_lines[0].rstrip()]
        section_order = [
            "identity",
            "available",
            "visible",
            "parents",
            "position",
            "mutually_exclusive",
            "limit",
            "equipment_bonus",
            "production_bonus",
            "organization_modifier",
            "on_complete",
            "ai_will_do",
            "other",
        ]
        first = True
        for key in section_order:
            if not sections[key]:
                continue
            if not first:
                result.append("")
            for line in sections[key]:
                result.append(line.rstrip())
            first = False

        result.append(block_lines[-1].rstrip())
        return result

    def compact_allowed_block(self, block_lines: List[str]) -> str:
        """Compact allowed block into a single standardized line"""
        if not block_lines:
            return "\tallowed = { }"

        content_parts = []
        for line in block_lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("allowed"):
                after_brace = stripped.split("{", 1)[1] if "{" in stripped else ""
                if "}" in after_brace:
                    after_brace = after_brace.split("}", 1)[0]
                if after_brace.strip():
                    content_parts.append(after_brace.strip())
            elif stripped == "}":
                continue
            else:
                before_brace = stripped.split("}", 1)[0].strip()
                if before_brace:
                    content_parts.append(before_brace)

        content = " ".join(content_parts).strip()
        content = " ".join(content.split())
        content = content.replace("{ ", "{").replace(" }", "}")
        content = content.replace("=", " = ")
        content = " ".join(content.split())
        return f"\tallowed = {{ {content} }}"

    def _add_blocks(
        self, lines: List[str], blocks: List[List[str]], is_trait: bool = False
    ) -> None:
        for index, block in enumerate(blocks):
            formatter = self.format_trait_block if is_trait else self.compact_block
            for line in formatter(block[:]):
                lines.append(line)
            if index < len(blocks) - 1:
                lines.append("")

    def _add_token_list_blocks(
        self,
        lines: List[str],
        blocks: List[List[str]],
        key: str,
        indent: str,
    ) -> None:
        for index, block in enumerate(blocks):
            for line in self._normalize_token_list(block, key, indent):
                lines.append(line)
            if index < len(blocks) - 1:
                lines.append("")

    def _format_allowed_blocks(self, blocks: List[List[str]]) -> List[str]:
        return [self.compact_allowed_block(block) for block in blocks]

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
