#!/usr/bin/env python3

"""
Millennium Dawn Focus Tree Standardizer
Reformats focus blocks and focus tree properties (shortcuts, inlay windows, offsets, positions), leaving everything else untouched
"""

import argparse
import os
import re
import sys
import time
from datetime import datetime

from common_utils import compact_icon, compact_search_filters
from shared_utils import compact_block, extract_block, log_message


def is_empty_block(block_lines):
    """Check if a block contains only braces and whitespace (no meaningful content)"""
    if not block_lines:
        return True
    content = "".join(line.strip() for line in block_lines)
    # Remove the property name and braces, check if anything remains
    inner = re.sub(r"^[^{]*\{(.*)\}$", r"\1", content, flags=re.DOTALL)
    return inner.strip() == ""


# Property dispatch tables for extract_focus_properties.
# Single-line props: map script name -> props dict key.
_SINGLE_LINE_PROPS = {
    "id": "id",
    "text_icon": "text_icon",
    "overlay": "overlay",
    "x": "x",
    "y": "y",
    "relative_position_id": "relative_position_id",
    "cost": "cost",
    "will_lead_to_war_with": "will_lead_to_war_with",
}

# Block props: map script name -> (props key, style).
# Styles: "scalar" overwrites; "list" appends; "skip_empty_scalar"/"skip_empty_list"
# drop blocks that contain only whitespace.
_BLOCK_PROPS = {
    "offset": ("offset", "list"),
    "allow_branch": ("allow_branch", "scalar"),
    "search_filters": ("search_filters", "scalar"),
    "prerequisite": ("prerequisites", "list"),
    "mutually_exclusive": ("mutually_exclusive", "skip_empty_list"),
    "joint_trigger": ("joint_trigger", "scalar"),
    "available": ("available", "skip_empty_scalar"),
    "cancel": ("cancel", "skip_empty_scalar"),
    "select_effect": ("select_effect", "scalar"),
    "bypass": ("bypass", "skip_empty_scalar"),
    "bypass_effect": ("bypass_effect", "scalar"),
    "completion_reward": ("completion_reward", "scalar"),
    "completion_reward_joint_originator": (
        "completion_reward_joint_originator",
        "scalar",
    ),
    "completion_reward_joint_member": ("completion_reward_joint_member", "scalar"),
    "ai_will_do": ("ai_will_do", "scalar"),
}

_DEFAULT_REMOVALS = {
    "cancel_if_invalid = yes",
    "continue_if_invalid = no",
    "available_if_capitulated = no",
}

_PROP_NAME_RE = re.compile(r"^(\w+)\s*=")
_COMMENTED_EMPTY_BLOCK_RE = re.compile(
    r"^#\s*(available|bypass|cancel|visible|mutually_exclusive)\s*=\s*\{\s*\}$"
)

# Matches an existing log line so we can correct a wrong focus ID or missing prefix.
# Handles [Root.GetName] / [This.GetName] (any capitalisation) and an optional "Focus " prefix.
_LOG_FOCUS_RE = re.compile(
    r'(log\s*=\s*"\[GetDateText\]:\s*\[[Rr]oot\.[Gg]etName\]:\s*)(?:Focus\s+)?(\w+)(")'
)


def extract_focus_properties(focus_lines):
    """Extract properties from focus block lines"""
    props = {
        "id": "",
        "icon": "",
        "text_icon": "",
        "overlay": "",
        "x": "",
        "y": "",
        "relative_position_id": "",
        "offset": [],
        "allow_branch": [],
        "cost": "",
        "prerequisites": [],
        "mutually_exclusive": [],
        "will_lead_to_war_with": [],
        "joint_trigger": [],
        "available": [],
        "cancel": [],
        "select_effect": [],
        "bypass": [],
        "bypass_effect": [],
        "completion_reward": [],
        "completion_reward_joint_originator": [],
        "completion_reward_joint_member": [],
        "search_filters": "",
        "ai_will_do": [],
        "other": [],
    }

    i = 1  # Skip opening brace
    while i < len(focus_lines) - 1:  # Skip closing brace
        line = focus_lines[i].strip()

        if line in _DEFAULT_REMOVALS or _COMMENTED_EMPTY_BLOCK_RE.match(line):
            i += 1
            continue

        match = _PROP_NAME_RE.match(line)
        prop_name = match.group(1) if match else None

        if prop_name == "icon":
            # Icon may repeat, and each entry can be a single line or a block.
            # Store uniformly as list[list[str]] — single-line entries become a
            # one-element sublist so downstream code can treat every entry the same.
            if "{" in line:
                block_lines, next_i = extract_block(focus_lines, i)
                entry = block_lines
                i = next_i
            else:
                entry = [line]
                i += 1
            if not isinstance(props["icon"], list):
                props["icon"] = []
            props["icon"].append(entry)
            continue

        if prop_name in _SINGLE_LINE_PROPS:
            props[_SINGLE_LINE_PROPS[prop_name]] = line
            i += 1
            continue

        if prop_name in _BLOCK_PROPS:
            key, style = _BLOCK_PROPS[prop_name]
            block_lines, next_i = extract_block(focus_lines, i)
            skip_empty = style.startswith("skip_empty_")
            if not skip_empty or not is_empty_block(block_lines):
                if style.endswith("list"):
                    props[key].append(block_lines)
                else:
                    props[key] = block_lines
            i = next_i
            continue

        props["other"].append(focus_lines[i])
        i += 1

    return props


def clean_block_lines(block_lines):
    """Remove trailing blank lines from a block and return cleaned lines"""
    if not block_lines:
        return block_lines

    while block_lines and block_lines[-1].strip() == "":
        block_lines.pop()

    return block_lines


def _fix_log_id(line: str, focus_id: str) -> str:
    """Correct a log line: ensure 'Focus ' prefix and replace the focus ID."""
    return _LOG_FOCUS_RE.sub(rf"\g<1>Focus {focus_id}\g<3>", line)


def emit_effect_block_with_log(lines, effect_block, focus_id):
    """Append an effect block to `lines`, injecting a log line as the first
    statement if the block doesn't already contain one, or correcting a
    mismatched focus ID / missing 'Focus ' prefix in an existing log line."""
    if not effect_block:
        return
    if focus_id and not any("log =" in line for line in effect_block):
        log_line = f'\t\t\tlog = "[GetDateText]: [Root.GetName]: Focus {focus_id}"'
        # Single-line block (`prop = { ... }` on one line): expand to multi-line
        # so the log lands INSIDE the braces, not after them.
        first = effect_block[0]
        if (
            len(effect_block) == 1
            and "{" in first
            and "}" in first
            and first.count("{") == first.count("}")
        ):
            leading = re.match(r"^(\s*)", first).group(1)
            open_idx = first.index("{")
            close_idx = first.rindex("}")
            header = first[: open_idx + 1].rstrip()
            inner = first[open_idx + 1 : close_idx].strip()
            expanded = [header, log_line]
            if inner:
                expanded.append(f"{leading}\t{inner}")
            expanded.append(f"{leading}}}")
            effect_block = expanded
        else:
            new_block = []
            for i, line in enumerate(effect_block):
                new_block.append(line)
                if i == 0 and "{" in line:
                    new_block.append(log_line)
            effect_block = new_block
    elif focus_id:
        # Log line already exists — correct wrong ID or missing 'Focus ' prefix.
        effect_block = [
            _fix_log_id(line, focus_id) if "log =" in line else line
            for line in effect_block
        ]
    for line in compact_block(effect_block[:]):
        lines.append(line)
    lines.append("")


def format_focus_offset_block(block_lines):
    """Format offset block within a focus (with 2-tab base indentation)"""
    lines = []
    lines.append("\t\toffset = {")

    x_val = ""
    y_val = ""
    trigger_lines = []
    other_lines = []

    i = 1  # Skip opening brace
    while i < len(block_lines) - 1:  # Skip closing brace
        line = block_lines[i].strip()

        if line.startswith("x ="):
            x_val = line
        elif line.startswith("y ="):
            y_val = line
        elif line.startswith("trigger ="):
            trigger_block, next_i = extract_block(block_lines, i)
            trigger_lines = trigger_block
            i = next_i
            continue
        else:
            other_lines.append(block_lines[i])

        i += 1

    if x_val:
        lines.append(f"\t\t\t{x_val}")
    if y_val:
        lines.append(f"\t\t\t{y_val}")

    if trigger_lines:
        # Reformat trigger block with brace-aware indentation
        lines.append("\t\t\ttrigger = {")
        depth = 0  # Nesting depth relative to trigger block
        for trigger_line in trigger_lines[1:-1]:  # Skip opening/closing braces
            stripped = trigger_line.strip()
            if not stripped:
                continue
            # Adjust depth for closing braces before writing the line
            close_count = stripped.count("}")
            open_count = stripped.count("{")
            if stripped == "}":
                depth -= 1
            indent = "\t\t\t\t" + "\t" * max(0, depth)
            lines.append(f"{indent}{stripped}")
            # Adjust depth for opening braces after writing the line
            if stripped != "}":
                depth += open_count - close_count
        lines.append("\t\t\t}")

    for line in other_lines:
        if line.strip():
            lines.append(line)

    lines.append("\t\t}")
    return lines


def format_focus_block(props, block_type="focus"):
    """Format focus according to Millennium Dawn standard"""
    lines = []
    lines.append(f"\t{block_type} = {{")

    # 1. ID and icon (no blank line between them)
    if props["id"]:
        lines.append(f'\t\t{props["id"]}')
    if props["icon"]:
        # `icon` is always list[list[str]] — emit each entry in order.
        for icon_block in props["icon"]:
            icon_lines = compact_icon(icon_block)
            if "\n" in icon_lines:
                for icon_line in icon_lines.split("\n"):
                    if icon_line.strip():
                        lines.append(icon_line)
            else:
                lines.append(f"\t\t{icon_lines}")

    # 2. Blank line before position group
    lines.append("")

    # 3. Position group (x, y, relative_position_id - no blank lines between them)
    if props["x"]:
        lines.append(f'\t\t{props["x"]}')
    if props["y"]:
        lines.append(f'\t\t{props["y"]}')
    if props["relative_position_id"]:
        lines.append(f'\t\t{props["relative_position_id"]}')
    for offset_block in props["offset"]:
        formatted_offset = format_focus_offset_block(offset_block[:])
        for line in formatted_offset:
            lines.append(line)

    # 4. Blank line before cost
    lines.append("")

    # 5. Cost
    if props["cost"]:
        lines.append(f'\t\t{props["cost"]}')
    if props["text_icon"]:
        lines.append(f'\t\t{props["text_icon"]}')
    if props["overlay"]:
        lines.append(f'\t\t{props["overlay"]}')

    # 6. Blank line before prerequisites/conditions
    lines.append("")

    # 7. Allow branch (before prerequisites)
    if props["allow_branch"]:
        compacted_allow_branch = compact_block(props["allow_branch"][:])
        for line in compacted_allow_branch:
            lines.append(line)
        lines.append("")

    # 8. Prerequisites and related conditions (grouped together without internal spacing)
    condition_group_added = False

    for prereq in props["prerequisites"]:
        compacted_prereq = compact_block(prereq[:])
        for line in compacted_prereq:
            lines.append(line)
        condition_group_added = True

    # Add all mutually_exclusive (no spacing between these and prerequisites)
    for mutex in props["mutually_exclusive"]:
        compacted_mutex = compact_block(mutex[:])
        for line in compacted_mutex:
            lines.append(line)
        condition_group_added = True

    # Add will_lead_to_war_with as single-line property
    if props["will_lead_to_war_with"]:
        lines.append(f'\t\t{props["will_lead_to_war_with"]}')
        condition_group_added = True

    # Only add blank line after the entire condition group (if any conditions were added)
    if condition_group_added:
        lines.append("")

    # 9. Search filters (right after condition group, before available)
    if props["search_filters"]:
        search_filters_line = compact_search_filters(props["search_filters"])
        lines.append(f"\t\t{search_filters_line}")
        lines.append("")

    # 10. Joint trigger (after search filters, before available)
    if props["joint_trigger"]:
        compacted_joint_trigger = compact_block(props["joint_trigger"][:])
        for line in compacted_joint_trigger:
            lines.append(line)
        lines.append("")

    # 11. Available block
    if props["available"]:
        compacted_available = compact_block(props["available"][:])
        for line in compacted_available:
            lines.append(line)
        lines.append("")

    # 11. Bypass block (positioned after available)
    if props["bypass"]:
        compacted_bypass = compact_block(props["bypass"][:])
        for line in compacted_bypass:
            lines.append(line)
        lines.append("")

    # 12. Cancel block (positioned after bypass)
    if props["cancel"]:
        compacted_cancel = compact_block(props["cancel"][:])
        for line in compacted_cancel:
            lines.append(line)
        lines.append("")

    # 13. Other properties (preserve as-is, but ensure spacing)
    if props["other"]:
        for line in props["other"]:
            if line.strip():
                lines.append(line)
        if props["other"]:
            lines.append("")

    focus_id = props["id"].split("=")[1].strip() if props["id"] else ""

    # 14. Completion reward (add log if missing)
    emit_effect_block_with_log(lines, props["completion_reward"], focus_id)

    # 15. Completion reward joint originator
    if props["completion_reward_joint_originator"]:
        compacted = compact_block(props["completion_reward_joint_originator"][:])
        for line in compacted:
            lines.append(line)
        lines.append("")

    # 16. Completion reward joint member
    if props["completion_reward_joint_member"]:
        compacted = compact_block(props["completion_reward_joint_member"][:])
        for line in compacted:
            lines.append(line)
        lines.append("")

    # 17. Select effect (add log if missing)
    emit_effect_block_with_log(lines, props["select_effect"], focus_id)

    # 18. Bypass effect (add log if missing)
    emit_effect_block_with_log(lines, props["bypass_effect"], focus_id)

    # 17. AI will do (always last, always multi-line)
    if props["ai_will_do"]:
        ai_lines = props["ai_will_do"]
        if len(ai_lines) == 1 and "ai_will_do = {" in ai_lines[0]:
            line = ai_lines[0]
            factor_match = re.search(r"factor\s*=\s*(\d+)", line)
            if factor_match:
                factor_value = factor_match.group(1)
                lines.append("\t\tai_will_do = {")
                lines.append(f"\t\t\tfactor = {factor_value}")
                lines.append("\t\t}")
            else:
                # Fallback to original if no factor found
                compacted_ai = compact_block(ai_lines[:])
                for line in compacted_ai:
                    lines.append(line)
        else:
            compacted_ai = compact_block(ai_lines[:])
            for line in compacted_ai:
                lines.append(line)
    else:
        lines.append("\t\tai_will_do = {")
        lines.append("\t\t\tfactor = 1")
        lines.append("\t\t}")

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


def format_shortcut_block(block_lines):
    """Format shortcut block according to standard"""
    lines = []
    lines.append("\tshortcut = {")

    name = ""
    target = ""
    scroll_wheel_factor = ""
    trigger_lines = []
    other_lines = []

    i = 1  # Skip opening brace
    while i < len(block_lines) - 1:  # Skip closing brace
        line = block_lines[i].strip()

        if line.startswith("name ="):
            name = line
        elif line.startswith("target ="):
            target = line
        elif line.startswith("scroll_wheel_factor ="):
            scroll_wheel_factor = line
        elif line.startswith("trigger ="):
            trigger_block, next_i = extract_block(block_lines, i)
            trigger_lines = trigger_block
            i = next_i
            continue
        else:
            other_lines.append(block_lines[i])

        i += 1

    if name:
        lines.append(f"\t\t{name}")
    if target:
        lines.append(f"\t\t{target}")
    if scroll_wheel_factor:
        lines.append(f"\t\t{scroll_wheel_factor}")

    if trigger_lines:
        compacted_trigger = compact_block(trigger_lines[:])
        for line in compacted_trigger:
            lines.append(line)

    for line in other_lines:
        if line.strip():
            lines.append(line)

    lines.append("\t}")
    return lines


def format_inlay_window_block(block_lines):
    """Format inlay_window block according to standard"""
    lines = []
    lines.append("\tinlay_window = {")

    window_id = ""
    position_lines = []
    override_position_lines = []
    other_lines = []

    i = 1  # Skip opening brace
    while i < len(block_lines) - 1:  # Skip closing brace
        line = block_lines[i].strip()

        if line.startswith("id ="):
            window_id = line
        elif line.startswith("position ="):
            position_block, next_i = extract_block(block_lines, i)
            position_lines = position_block
            i = next_i
            continue
        elif line.startswith("override_position ="):
            override_block, next_i = extract_block(block_lines, i)
            override_position_lines = override_block
            i = next_i
            continue
        else:
            other_lines.append(block_lines[i])

        i += 1

    if window_id:
        lines.append(f"\t\t{window_id}")

    if position_lines:
        compacted_position = compact_block(position_lines[:])
        for line in compacted_position:
            lines.append(line)

    if override_position_lines:
        compacted_override = compact_block(override_position_lines[:])
        for line in compacted_override:
            lines.append(line)

    for line in other_lines:
        if line.strip():
            lines.append(line)

    lines.append("\t}")
    return lines


def format_offset_block(block_lines):
    """Format offset block according to standard"""
    lines = []
    lines.append("\toffset = {")

    x_val = ""
    y_val = ""
    trigger_lines = []
    other_lines = []

    i = 1  # Skip opening brace
    while i < len(block_lines) - 1:  # Skip closing brace
        line = block_lines[i].strip()

        if line.startswith("x ="):
            x_val = line
        elif line.startswith("y ="):
            y_val = line
        elif line.startswith("trigger ="):
            trigger_block, next_i = extract_block(block_lines, i)
            trigger_lines = trigger_block
            i = next_i
            continue
        else:
            other_lines.append(block_lines[i])

        i += 1

    if x_val:
        lines.append(f"\t\t{x_val}")
    if y_val:
        lines.append(f"\t\t{y_val}")

    if trigger_lines:
        compacted_trigger = compact_block(trigger_lines[:])
        for line in compacted_trigger:
            lines.append(line)

    for line in other_lines:
        if line.strip():
            lines.append(line)

    lines.append("\t}")
    return lines


def format_continuous_focus_position_block(block_lines):
    """Format continuous_focus_position block according to standard"""
    x_val = ""
    y_val = ""

    # Handle single-line blocks like `continuous_focus_position = { x = 5700 y = 2000 }`
    # by tokenising the contents between the braces.
    if len(block_lines) == 1 and "{" in block_lines[0] and "}" in block_lines[0]:
        inner = block_lines[0].split("{", 1)[1].rsplit("}", 1)[0].strip()
        for match in re.finditer(r"(x|y)\s*=\s*(\S+)", inner):
            key, value = match.group(1), match.group(2)
            if key == "x":
                x_val = value
            elif key == "y":
                y_val = value

    # Multi-line blocks: one property per line.
    for line in block_lines:
        stripped = line.strip()
        if stripped.startswith("x ="):
            x_val = stripped.split("=")[1].strip()
        elif stripped.startswith("y ="):
            y_val = stripped.split("=")[1].strip()

    if x_val and y_val:
        return [f"\tcontinuous_focus_position = {{ x = {x_val} y = {y_val} }}"]

    # Fallback: return rstripped lines so no stray newlines survive.
    return [line.rstrip("\r\n") for line in block_lines]


def format_initial_show_position_block(block_lines):
    """Format initial_show_position block according to standard"""
    lines = []
    lines.append("\tinitial_show_position = {")

    x_val = ""
    y_val = ""
    focus_val = ""
    offset_lines = []
    other_lines = []

    # Handle single-line blocks like `initial_show_position = { x = 2 y = 0 }`
    # by extracting the contents between the braces and tokenising them.
    if len(block_lines) == 1 and "{" in block_lines[0] and "}" in block_lines[0]:
        inner = block_lines[0].split("{", 1)[1].rsplit("}", 1)[0].strip()
        for match in re.finditer(r"(x|y|focus)\s*=\s*(\S+)", inner):
            key, value = match.group(1), match.group(2)
            if key == "x":
                x_val = f"x = {value}"
            elif key == "y":
                y_val = f"y = {value}"
            elif key == "focus":
                focus_val = f"focus = {value}"

    i = 1  # Skip opening brace
    while i < len(block_lines) - 1:  # Skip closing brace
        line = block_lines[i].strip()

        if line.startswith("x ="):
            x_val = line
        elif line.startswith("y ="):
            y_val = line
        elif line.startswith("focus ="):
            focus_val = line
        elif line.startswith("offset ="):
            offset_block, next_i = extract_block(block_lines, i)
            offset_lines = offset_block
            i = next_i
            continue
        else:
            other_lines.append(block_lines[i])

        i += 1

    # Prefer single-line output when the block has only simple coordinates.
    if focus_val and not x_val and not y_val and not offset_lines and not other_lines:
        return [f"\tinitial_show_position = {{ {focus_val} }}"]

    if x_val and y_val and not focus_val and not offset_lines and not other_lines:
        x_num = x_val.split("=", 1)[1].strip()
        y_num = y_val.split("=", 1)[1].strip()
        return [f"\tinitial_show_position = {{ x = {x_num} y = {y_num} }}"]

    if x_val:
        lines.append(f"\t\t{x_val}")
    if y_val:
        lines.append(f"\t\t{y_val}")
    if focus_val:
        lines.append(f"\t\t{focus_val}")

    if offset_lines:
        compacted_offset = compact_block(offset_lines[:])
        for line in compacted_offset:
            lines.append(line)

    for line in other_lines:
        if line.strip():
            lines.append(line)

    lines.append("\t}")
    return lines


# Dispatch tables for standardize_focus_tree's main loop.
_FOCUS_BLOCK_TYPES = {"focus", "shared_focus", "joint_focus"}

_SIMPLE_BLOCK_HANDLERS = {
    "shortcut": format_shortcut_block,
    "inlay_window": format_inlay_window_block,
    "offset": format_offset_block,
    "continuous_focus_position": format_continuous_focus_position_block,
    "initial_show_position": format_initial_show_position_block,
}

# Order preserved for the SUCCESS log output at end of standardization.
_BLOCK_COUNT_ORDER = (
    "focus",
    "shared_focus",
    "joint_focus",
    "continuous_focus_position",
    "initial_show_position",
    "shortcut",
    "inlay_window",
    "offset",
)

_BLOCK_DISPATCH_RE = re.compile(r"^\s*(" + "|".join(_BLOCK_COUNT_ORDER) + r")\s*=\s*\{")


def standardize_focus_tree(input_file: str, output_file: str, verbose: bool = False):
    """Standardize focus tree by reformatting focus blocks and all focus tree properties"""
    start_time = time.time()

    log_message("INFO", f"Starting standardization of {input_file}", verbose)

    if not os.path.exists(input_file):
        log_message("ERROR", f"Input file not found: {input_file}")
        return False

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        log_message("INFO", f"Read {len(lines)} lines from {input_file}", verbose)
    except Exception as e:
        log_message("ERROR", f"Failed to read {input_file}: {e}")
        return False

    output_lines = []
    i = 0
    counts = {block_type: 0 for block_type in _BLOCK_COUNT_ORDER}

    while i < len(lines):
        line = lines[i].rstrip()
        match = _BLOCK_DISPATCH_RE.match(line)

        if not match:
            output_lines.append(line)
            i += 1
            continue

        block_type = match.group(1)
        log_message("DEBUG", f"Found {block_type} block at line {i + 1}", verbose)

        block_lines, next_i = extract_block(lines, i)
        if block_lines:
            if block_type in _FOCUS_BLOCK_TYPES:
                props = extract_focus_properties(block_lines)
                formatted_lines = format_focus_block(props, block_type)
                counts[block_type] += 1
                log_message(
                    "DEBUG",
                    f"Processed {block_type} block {counts[block_type]}: "
                    f"{props.get('id', 'unknown')}",
                    verbose,
                )
            else:
                formatted_lines = _SIMPLE_BLOCK_HANDLERS[block_type](block_lines)
                counts[block_type] += 1
                log_message(
                    "DEBUG",
                    f"Processed {block_type} block {counts[block_type]}",
                    verbose,
                )
            output_lines.extend(formatted_lines)

        i = next_i

    # Post-processing: ensure blank lines between consecutive focus/shared_focus/joint_focus blocks
    focus_block_pattern = re.compile(r"^\t(focus|shared_focus|joint_focus)\s*=\s*{")
    final_lines = []
    for idx, line in enumerate(output_lines):
        if focus_block_pattern.match(line) and final_lines:
            # Find the previous non-empty line
            prev_idx = len(final_lines) - 1
            while prev_idx >= 0 and final_lines[prev_idx].strip() == "":
                prev_idx -= 1
            # If the previous content line is a closing brace and there's no blank line, add one
            if (
                prev_idx >= 0
                and final_lines[prev_idx].strip() == "}"
                and final_lines[-1].strip() != ""
            ):
                final_lines.append("")
        final_lines.append(line)
    output_lines = final_lines

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            for line in output_lines:
                f.write(line + "\n")

        end_time = time.time()
        elapsed_time = end_time - start_time

        if elapsed_time < 60:
            time_str = f"{elapsed_time:.2f} seconds"
        else:
            minutes = int(elapsed_time // 60)
            seconds = elapsed_time % 60
            time_str = f"{minutes}m {seconds:.2f}s"

        log_message("SUCCESS", f"Standardization completed in {time_str}")
        log_message("SUCCESS", f"Processed {counts['focus']} focus blocks")
        for block_type in _BLOCK_COUNT_ORDER:
            if block_type == "focus":
                continue  # already logged above, unconditionally
            if counts[block_type] > 0:
                log_message(
                    "SUCCESS", f"Processed {counts[block_type]} {block_type} blocks"
                )
        log_message("SUCCESS", f"Output written to: {output_file}")

    except Exception as e:
        log_message("ERROR", f"Failed to write {output_file}: {e}")
        return False

    return True


def create_backup(filename: str) -> str:
    """Create a backup of the input file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"{filename}.backup.{timestamp}"

    try:
        with open(filename, "r", encoding="utf-8") as src:
            with open(backup_filename, "w", encoding="utf-8") as dst:
                dst.write(src.read())
        log_message("INFO", f"Backup created: {backup_filename}")
        return backup_filename
    except Exception as e:
        log_message("ERROR", f"Failed to create backup: {str(e)}")
        return ""


def main():
    parser = argparse.ArgumentParser(
        description="Standardize HOI4 focus tree files - reformats focus blocks and all focus tree properties"
    )
    parser.add_argument("input_file", help="Input focus tree file")
    parser.add_argument(
        "-o", "--output", help="Output file (default: overwrites input)"
    )
    parser.add_argument(
        "-b", "--backup", action="store_true", help="Create backup before modifying"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        log_message("ERROR", f"File '{args.input_file}' does not exist")
        sys.exit(1)

    output_file = args.output if args.output else args.input_file

    if args.backup:
        backup_file = create_backup(args.input_file)
        if not backup_file:
            sys.exit(1)

    log_message(
        "INFO",
        f"Starting focus block standardization of {args.input_file}",
        args.verbose,
    )

    if standardize_focus_tree(args.input_file, output_file, args.verbose):
        log_message("SUCCESS", f"Standardization completed: {output_file}")
    else:
        log_message("ERROR", "Standardization failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
