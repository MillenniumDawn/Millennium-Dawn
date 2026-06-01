#!/usr/bin/env python3

"""
Millennium Dawn Decision Standardizer
Standardizes HOI4 decision files according to Millennium Dawn coding standards
"""

from typing import Any, Dict, List

from common_utils import (
    PROP_NAME_RE,
    BaseStandardizer,
    block_has_log,
    collapse_blank_runs,
    inject_log_after_brace,
    run_standardizer,
)
from shared_utils import compact_block, extract_block

_SINGLE_LINE_PROPS = {"cost", "days_remove", "fire_only_once", "icon"}
_BLOCK_PROPS = {"allowed", "visible", "available", "complete_effect", "ai_will_do"}


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


def main():
    run_standardizer(
        DecisionStandardizer,
        "Standardize HOI4 decision files according to Millennium Dawn coding standards",
    )


if __name__ == "__main__":
    main()
