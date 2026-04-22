#!/usr/bin/env python3

"""
Millennium Dawn Event Standardizer
Standardizes HOI4 event files according to Millennium Dawn coding standards
"""

from typing import Any, Dict, List

from common_utils import (
    PROP_NAME_RE,
    BaseStandardizer,
    block_has_log,
    collapse_blank_runs,
    emit_comments,
    inject_log_after_brace,
    run_standardizer,
)
from shared_utils import compact_block, extract_block

_EVENT_TYPES = ("country_event", "province_event", "unit_leader_event", "news_event")

_HEADER_SINGLE_PROPS = {
    "id",
    "picture",
    "is_triggered_only",
    "hidden",
    "major",
    "fire_only_once",
}

# Maps script property name -> (props key, section tag for comment placement)
_BLOCK_PROPS = {
    "mean_time_to_happen": ("mean_time_to_happen", "mtth"),
    "trigger": ("trigger", "trigger"),
    "immediate": ("immediate", "immediate"),
    "option": ("option", "options"),
}


def _option_log_line(option_block: List[str]) -> str:
    """Build the log line for an event option. Uses the first `name = ...`
    line found in the block (matches legacy behaviour)."""
    option_name = "option"
    for line in option_block:
        stripped = line.strip()
        if stripped.startswith("name ="):
            option_name = stripped.split("=", 1)[1].strip()
            break
    return f'\t\t\tlog = "[GetDateText]: [This.GetName]: {option_name} executed"'


def _option_has_effects(option_block: List[str]) -> bool:
    """Check whether an option has any meaningful effect lines."""
    skip_prefixes = ("name =", "ai_chance =", "trigger =")
    for line in option_block:
        stripped = line.strip()
        if not stripped or stripped in ("{", "}"):
            continue
        if stripped.startswith("#"):
            continue
        if stripped.startswith(skip_prefixes):
            continue
        return True
    return False


class EventStandardizer(BaseStandardizer):
    """Standardizer for HOI4 events"""

    def get_block_pattern(self) -> str:
        """Return regex pattern to identify event blocks"""
        return r"\s*(" + "|".join(_EVENT_TYPES) + r")\s*=\s*{"

    def extract_properties(self, block_lines: List[str]) -> Dict[str, Any]:
        """Extract properties from event block lines"""
        props: Dict[str, Any] = {
            "event_type": "",
            "id": "",
            # title/desc: list of entries. Each entry is either a single-line
            # string or a list[str] for `prop = { trigger = {...} text = ... }`
            # conditional blocks (which can repeat).
            "title": [],
            "desc": [],
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
        for event_type in _EVENT_TYPES:
            if event_type in first_line:
                props["event_type"] = event_type
                break

        # Track which section we're in for comment placement
        current_section = "header"

        i = 1  # Skip opening brace
        while i < len(block_lines) - 1:  # Skip closing brace
            line = block_lines[i].strip()
            match = PROP_NAME_RE.match(line)
            prop_name = match.group(1) if match else None

            if prop_name in _HEADER_SINGLE_PROPS:
                props[prop_name] = line
                current_section = "header"
            elif prop_name in ("title", "desc"):
                if "{" in line:
                    block, next_i = extract_block(block_lines, i)
                    props[prop_name].append(block)
                    i = next_i
                    current_section = "header"
                    continue
                else:
                    props[prop_name].append(line)
                    current_section = "header"
            elif prop_name in _BLOCK_PROPS:
                key, section = _BLOCK_PROPS[prop_name]
                block, next_i = extract_block(block_lines, i)
                props[key].append(block)
                i = next_i
                current_section = section
                continue
            else:
                # This is a comment or unrecognized line - add to current section
                props[f"comments_after_{current_section}"].append(block_lines[i])

            i += 1

        return props

    def format_block(self, props: Dict[str, Any]) -> List[str]:
        """Format event according to Millennium Dawn standard"""
        lines = []
        lines.append(f"{props['event_type']} = {{")

        # 1. ID (first line after opening brace)
        if props["id"]:
            lines.append(f'\t{props["id"]}')

        # 2. Title and description (may repeat as conditional blocks)
        for title_entry in props["title"]:
            if isinstance(title_entry, list):
                lines.extend(compact_block(title_entry[:]))
            else:
                lines.append(f"\t{title_entry}")
        for desc_entry in props["desc"]:
            if isinstance(desc_entry, list):
                lines.extend(compact_block(desc_entry[:]))
            else:
                lines.append(f"\t{desc_entry}")

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

        emit_comments(lines, props["comments_after_header"])

        # 8. Mean time to happen
        for mtth in props["mean_time_to_happen"]:
            lines.extend(compact_block(mtth[:]))
            lines.append("")
        emit_comments(lines, props["comments_after_mtth"])

        # 9. Trigger
        for trigger in props["trigger"]:
            lines.extend(compact_block(trigger[:]))
            lines.append("")
        emit_comments(lines, props["comments_after_trigger"])

        # 10. Immediate effects
        for immediate in props["immediate"]:
            lines.extend(compact_block(immediate[:]))
            lines.append("")
        emit_comments(lines, props["comments_after_immediate"])

        # 11. Options
        for option in props["option"]:
            if (
                _option_has_effects(option)
                and not block_has_log(option)
                and props["id"]
            ):
                log_line = _option_log_line(option)
                option = inject_log_after_brace(option, log_line)

            lines.extend(compact_block(option[:]))
            lines.append("")

        emit_comments(lines, props["comments_after_options"])
        if props["comments_after_options"]:
            lines.append("")

        lines.append("}")

        return collapse_blank_runs(lines)


def main():
    run_standardizer(
        EventStandardizer,
        "Standardize HOI4 event files according to Millennium Dawn coding standards",
    )


if __name__ == "__main__":
    main()
