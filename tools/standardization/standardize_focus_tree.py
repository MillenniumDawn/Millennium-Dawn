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


def log_message(level: str, message: str, verbose: bool = False):
    """Log a message with timestamp"""
    if level == "DEBUG" and not verbose:
        return

    timestamp = datetime.now().strftime("%H:%M:%S")

    colors = {
        "SUCCESS": "\033[92m",  # Green
        "INFO": "\033[94m",  # Blue
        "DEBUG": "\033[90m",  # Gray
        "WARNING": "\033[93m",  # Yellow
        "ERROR": "\033[91m",  # Red
    }
    reset_color = "\033[0m"

    color = colors.get(level, "")

    formatted_message = f"{color}[{timestamp}] {level}: {message}{reset_color}"
    print(formatted_message, file=sys.stderr)


def extract_focus_properties(focus_lines):
    """Extract properties from focus block lines"""
    props = {
        "id": "",
        "icon": "",
        "x": "",
        "y": "",
        "relative_position_id": "",
        "cost": "",
        "prerequisites": [],
        "mutually_exclusive": [],
        "will_lead_to_war_with": [],
        "available": [],
        "bypass": [],
        "cancel": [],
        "completion_reward": [],
        "ai_will_do": [],
        "search_filters": "",
        "allow_branch": [],
        "select_effect": [],
        "bypass_effect": [],
        "other": [],
    }

    i = 1  # Skip opening brace
    while i < len(focus_lines) - 1:  # Skip closing brace
        line = focus_lines[i].strip()

        if line.startswith("id ="):
            props["id"] = line
        elif line.startswith("icon ="):
            # Check if this is a multi-line block or single line
            if "{" in line:
                # Multi-line block
                block_lines, next_i = extract_block(focus_lines, i)
                if isinstance(props["icon"], list):
                    # Already have icon blocks, append to the list
                    if not isinstance(props["icon"][0], list):
                        # Convert single icon to list format
                        props["icon"] = [props["icon"]]
                    props["icon"].append(block_lines)
                else:
                    # First icon block
                    props["icon"] = [block_lines]
                i = next_i  # Set i to the position after the block
                continue  # Skip the i += 1 at the end of the loop
            else:
                # Single line
                if isinstance(props["icon"], list):
                    # Already have icon blocks, append to the list
                    props["icon"].append(line)
                else:
                    # First icon
                    props["icon"] = [line]
        elif line.startswith("x ="):
            props["x"] = line
        elif line.startswith("y ="):
            props["y"] = line
        elif line.startswith("relative_position_id ="):
            props["relative_position_id"] = line
        elif line.startswith("cost ="):
            props["cost"] = line
        elif line.startswith("search_filters ="):
            block_lines, next_i = extract_block(focus_lines, i)
            props["search_filters"] = block_lines
            i = next_i  # Set i to the position after the block
            continue  # Skip the i += 1 at the end of the loop
        elif line.startswith("will_lead_to_war_with ="):
            props["will_lead_to_war_with"] = line

        elif line.startswith("prerequisite ="):
            block_lines, next_i = extract_block(focus_lines, i)
            props["prerequisites"].append(block_lines)
            i = next_i  # Set i to the position after the block
            continue  # Skip the i += 1 at the end of the loop
        elif line.startswith("mutually_exclusive ="):
            block_lines, next_i = extract_block(focus_lines, i)
            props["mutually_exclusive"].append(block_lines)
            i = next_i  # Set i to the position after the block
            continue  # Skip the i += 1 at the end of the loop
        elif line.startswith("available ="):
            block_lines, next_i = extract_block(focus_lines, i)
            props["available"] = block_lines
            i = next_i  # Set i to the position after the block
            continue  # Skip the i += 1 at the end of the loop
        elif line.startswith("bypass ="):
            block_lines, next_i = extract_block(focus_lines, i)
            props["bypass"] = block_lines
            i = next_i  # Set i to the position after the block
            continue  # Skip the i += 1 at the end of the loop
        elif line.startswith("cancel ="):
            block_lines, next_i = extract_block(focus_lines, i)
            props["cancel"] = block_lines
            i = next_i  # Set i to the position after the block
            continue  # Skip the i += 1 at the end of the loop
        elif line.startswith("completion_reward ="):
            block_lines, next_i = extract_block(focus_lines, i)
            props["completion_reward"] = block_lines
            i = next_i  # Set i to the position after the block
            continue  # Skip the i += 1 at the end of the loop
        elif line.startswith("ai_will_do ="):
            block_lines, next_i = extract_block(focus_lines, i)
            props["ai_will_do"] = block_lines
            i = next_i  # Set i to the position after the block
            continue  # Skip the i += 1 at the end of the loop
        elif line.startswith("allow_branch ="):
            block_lines, next_i = extract_block(focus_lines, i)
            props["allow_branch"] = block_lines
            i = next_i  # Set i to the position after the block
            continue  # Skip the i += 1 at the end of the loop
        elif line.startswith("select_effect ="):
            block_lines, next_i = extract_block(focus_lines, i)
            props["select_effect"] = block_lines
            i = next_i  # Set i to the position after the block
            continue  # Skip the i += 1 at the end of the loop
        elif line.startswith("bypass_effect ="):
            block_lines, next_i = extract_block(focus_lines, i)
            props["bypass_effect"] = block_lines
            i = next_i  # Set i to the position after the block
            continue  # Skip the i += 1 at the end of the loop
        else:
            props["other"].append(focus_lines[i])

        i += 1

    return props


def extract_block(lines, start_index):
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

    return block_lines, i  # Return the position AFTER the block (not i-1)


def clean_block_lines(block_lines):
    """Remove trailing blank lines from a block and return cleaned lines"""
    if not block_lines:
        return block_lines

    while block_lines and block_lines[-1].strip() == "":
        block_lines.pop()

    return block_lines


def compact_block(block_lines):
    """Completely compact a block by removing all internal blank lines"""
    if not block_lines:
        return block_lines

    compacted = []
    for line in block_lines:
        stripped = line.strip()
        if stripped:
            compacted.append(line.rstrip())

    return compacted


def compact_search_filters(block_lines):
    """Compact search_filters block into a single line with spaces between entities, supporting both single-line and multi-line formats."""
    if not block_lines:
        return "search_filters = { }"

    entities = []
    for line in block_lines:
        # Find everything between { and } (or after {, or before })
        if "search_filters" in line and "{" in line:
            # Get everything after the first '{'
            after_brace = line.split("{", 1)[1]
            # Remove everything after '}' if present
            after_brace = after_brace.split("}", 1)[0]
            tokens = after_brace.strip().split()
            entities.extend(tokens)
        elif "}" in line:
            # Get everything before '}'
            before_brace = line.split("}", 1)[0]
            tokens = before_brace.strip().split()
            entities.extend(tokens)
        else:
            tokens = line.strip().split()
            entities.extend(tokens)

    # Remove empty tokens
    entities = [e for e in entities if e]
    return f"search_filters = {{ {' '.join(entities)} }}"


def compact_icon(block_lines):
    """Compact icon block into a single line, handling both simple strings and multi-line blocks"""
    if not block_lines:
        return "icon = GFX_goal_generic_support_the_left_wing"  # Default fallback

    # If it's already a single line (simple icon)
    if len(block_lines) == 1:
        return block_lines[0].strip()

    # For complex multi-line blocks, just remove blank lines and preserve original indentation
    compacted_lines = []
    for line in block_lines:
        if line.strip():  # Only keep non-empty lines
            compacted_lines.append(line.rstrip())

    return "\n".join(compacted_lines)


def format_focus_block(props):
    """Format focus according to Millennium Dawn standard"""
    lines = []
    lines.append("\tfocus = {")

    # 1. ID and icon (no blank line between them)
    if props["id"]:
        lines.append(f'\t\t{props["id"]}')
    if props["icon"]:
        # Handle multiple icon blocks
        if isinstance(props["icon"], list) and len(props["icon"]) > 0:
            # Check if it's a list of icon blocks or a single block
            if isinstance(props["icon"][0], list):
                # Multiple icon blocks
                for icon_block in props["icon"]:
                    icon_lines = compact_icon(icon_block)
                    if "\n" in icon_lines:
                        # Multi-line output - split and add each line with proper indentation
                        for icon_line in icon_lines.split("\n"):
                            if icon_line.strip():  # Only add non-empty lines
                                lines.append(icon_line)
                    else:
                        # Single line output
                        lines.append(f"\t\t{icon_lines}")
            else:
                # Single icon block
                icon_lines = compact_icon(props["icon"])
                if "\n" in icon_lines:
                    # Multi-line output - split and add each line with proper indentation
                    for icon_line in icon_lines.split("\n"):
                        if icon_line.strip():  # Only add non-empty lines
                            lines.append(icon_line)
                else:
                    # Single line output
                    lines.append(f"\t\t{icon_lines}")
        else:
            # Single line - use as-is
            lines.append(f'\t\t{props["icon"]}')

    # 2. Blank line before position group
    lines.append("")

    # 3. Position group (x, y, relative_position_id - no blank lines between them)
    if props["x"]:
        lines.append(f'\t\t{props["x"]}')
    if props["y"]:
        lines.append(f'\t\t{props["y"]}')
    if props["relative_position_id"]:
        lines.append(f'\t\t{props["relative_position_id"]}')

    # 4. Blank line before cost
    lines.append("")

    # 5. Cost
    if props["cost"]:
        lines.append(f'\t\t{props["cost"]}')

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

    # 10. Available block
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

    # 14. Completion reward (add log if missing)
    if props["completion_reward"]:
        has_log = any("log =" in line for line in props["completion_reward"])
        if not has_log and props["id"]:
            focus_id = props["id"].split("=")[1].strip()
            modified_reward = []
            for i, line in enumerate(props["completion_reward"]):
                modified_reward.append(line)
                if i == 0 and "{" in line:
                    modified_reward.append(
                        f'\t\t\tlog = "[GetDateText]: [Root.GetName]: Focus {focus_id}"'
                    )
            props["completion_reward"] = modified_reward

        compacted_reward = compact_block(props["completion_reward"][:])
        for line in compacted_reward:
            lines.append(line)
        lines.append("")

    # 15. Select effect (add log if missing)
    if props["select_effect"]:
        has_log = any("log =" in line for line in props["select_effect"])
        if not has_log and props["id"]:
            focus_id = props["id"].split("=")[1].strip()
            modified_effect = []
            for i, line in enumerate(props["select_effect"]):
                modified_effect.append(line)
                if i == 0 and "{" in line:
                    modified_effect.append(
                        f'\t\t\tlog = "[GetDateText]: [Root.GetName]: Focus {focus_id}"'
                    )
            props["select_effect"] = modified_effect

        compacted_effect = compact_block(props["select_effect"][:])
        for line in compacted_effect:
            lines.append(line)
        lines.append("")

    # 16. Bypass effect (add log if missing)
    if props["bypass_effect"]:
        has_log = any("log =" in line for line in props["bypass_effect"])
        if not has_log and props["id"]:
            focus_id = props["id"].split("=")[1].strip()
            modified_effect = []
            for i, line in enumerate(props["bypass_effect"]):
                modified_effect.append(line)
                if i == 0 and "{" in line:
                    modified_effect.append(
                        f'\t\t\tlog = "[GetDateText]: [Root.GetName]: Focus {focus_id}"'
                    )
            props["bypass_effect"] = modified_effect

        compacted_effect = compact_block(props["bypass_effect"][:])
        for line in compacted_effect:
            lines.append(line)
        lines.append("")

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

    # Extract properties
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

    # Format output
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

    # Extract properties
    window_id = ""
    position_lines = []
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
        else:
            other_lines.append(block_lines[i])

        i += 1

    # Format output
    if window_id:
        lines.append(f"\t\t{window_id}")

    if position_lines:
        compacted_position = compact_block(position_lines[:])
        for line in compacted_position:
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

    # Extract properties
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

    # Format output
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
    # Extract x and y values
    x_val = ""
    y_val = ""

    for line in block_lines:
        stripped = line.strip()
        if stripped.startswith("x ="):
            x_val = stripped.split("=")[1].strip()
        elif stripped.startswith("y ="):
            y_val = stripped.split("=")[1].strip()

    # Format as single line
    if x_val and y_val:
        return [f"\tcontinuous_focus_position = {{ x = {x_val} y = {y_val} }}"]
    else:
        # Fallback to original if parsing fails
        return block_lines


def format_initial_show_position_block(block_lines):
    """Format initial_show_position block according to standard"""
    lines = []
    lines.append("\tinitial_show_position = {")

    # Extract properties
    x_val = ""
    y_val = ""
    focus_val = ""
    offset_lines = []
    other_lines = []

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

    # Format output - prefer single line if simple
    if focus_val and not x_val and not y_val and not offset_lines and not other_lines:
        # Simple case: just focus reference
        return [f"\tinitial_show_position = {{ {focus_val} }}"]

    # Multi-line format
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
    focus_count = 0
    shortcut_count = 0
    inlay_count = 0
    offset_count = 0
    continuous_pos_count = 0
    initial_pos_count = 0

    while i < len(lines):
        line = lines[i].rstrip()

        if re.match(r"\s*focus\s*=\s*{", line):
            log_message("DEBUG", f"Found focus block at line {i+1}", verbose)

            focus_block, next_i = extract_block(lines, i)

            if focus_block:
                props = extract_focus_properties(focus_block)
                formatted_lines = format_focus_block(props)

                output_lines.extend(formatted_lines)
                focus_count += 1

                log_message(
                    "DEBUG",
                    f"Processed focus block {focus_count}: {props.get('id', 'unknown')}",
                    verbose,
                )

            i = next_i
        elif re.match(r"\s*shortcut\s*=\s*{", line):
            log_message("DEBUG", f"Found shortcut block at line {i+1}", verbose)

            shortcut_block, next_i = extract_block(lines, i)

            if shortcut_block:
                formatted_lines = format_shortcut_block(shortcut_block)
                output_lines.extend(formatted_lines)
                shortcut_count += 1

                log_message(
                    "DEBUG", f"Processed shortcut block {shortcut_count}", verbose
                )

            i = next_i
        elif re.match(r"\s*inlay_window\s*=\s*{", line):
            log_message("DEBUG", f"Found inlay_window block at line {i+1}", verbose)

            inlay_block, next_i = extract_block(lines, i)

            if inlay_block:
                formatted_lines = format_inlay_window_block(inlay_block)
                output_lines.extend(formatted_lines)
                inlay_count += 1

                log_message(
                    "DEBUG", f"Processed inlay_window block {inlay_count}", verbose
                )

            i = next_i
        elif re.match(r"\s*offset\s*=\s*{", line):
            log_message("DEBUG", f"Found offset block at line {i+1}", verbose)

            offset_block, next_i = extract_block(lines, i)

            if offset_block:
                formatted_lines = format_offset_block(offset_block)
                output_lines.extend(formatted_lines)
                offset_count += 1

                log_message("DEBUG", f"Processed offset block {offset_count}", verbose)

            i = next_i
        elif re.match(r"\s*continuous_focus_position\s*=\s*{", line):
            log_message(
                "DEBUG", f"Found continuous_focus_position block at line {i+1}", verbose
            )

            block, next_i = extract_block(lines, i)

            if block:
                formatted_lines = format_continuous_focus_position_block(block)
                output_lines.extend(formatted_lines)
                continuous_pos_count += 1

                log_message(
                    "DEBUG", f"Processed continuous_focus_position block", verbose
                )

            i = next_i
        elif re.match(r"\s*initial_show_position\s*=\s*{", line):
            log_message(
                "DEBUG", f"Found initial_show_position block at line {i+1}", verbose
            )

            block, next_i = extract_block(lines, i)

            if block:
                formatted_lines = format_initial_show_position_block(block)
                output_lines.extend(formatted_lines)
                initial_pos_count += 1

                log_message("DEBUG", f"Processed initial_show_position block", verbose)

            i = next_i
        else:
            output_lines.append(line)
            i += 1

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
        log_message("SUCCESS", f"Processed {focus_count} focus blocks")
        if continuous_pos_count > 0:
            log_message(
                "SUCCESS",
                f"Processed {continuous_pos_count} continuous_focus_position blocks",
            )
        if initial_pos_count > 0:
            log_message(
                "SUCCESS", f"Processed {initial_pos_count} initial_show_position blocks"
            )
        if shortcut_count > 0:
            log_message("SUCCESS", f"Processed {shortcut_count} shortcut blocks")
        if inlay_count > 0:
            log_message("SUCCESS", f"Processed {inlay_count} inlay_window blocks")
        if offset_count > 0:
            log_message("SUCCESS", f"Processed {offset_count} offset blocks")
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
