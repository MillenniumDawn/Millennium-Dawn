#!/usr/bin/env python3

"""
Millennium Dawn Focus Tree Standardizer
Simple approach: Only reformat focus blocks, leave everything else untouched
"""

import re
import sys
import argparse
import os
import time
from datetime import datetime

def log_message(level: str, message: str, verbose: bool = False):
    """Log a message with timestamp"""
    if level == 'DEBUG' and not verbose:
        return

    timestamp = datetime.now().strftime("%H:%M:%S")

    # Color coding for different log levels
    colors = {
        'SUCCESS': '\033[92m',  # Green
        'INFO': '\033[94m',     # Blue
        'DEBUG': '\033[90m',    # Gray
        'WARNING': '\033[93m',  # Yellow
        'ERROR': '\033[91m'     # Red
    }
    reset_color = '\033[0m'

    color = colors.get(level, '')

    formatted_message = f"{color}[{timestamp}] {level}: {message}{reset_color}"
    print(formatted_message, file=sys.stderr)

def extract_focus_properties(focus_lines):
    """Extract properties from focus block lines"""
    props = {
        'id': '', 'icon': '', 'x': '', 'y': '', 'relative_position_id': '', 'cost': '',
        'prerequisites': [], 'mutually_exclusive': [], 'will_lead_to_war_with': [],
        'available': [], 'bypass': [], 'cancel': [], 'completion_reward': [], 'ai_will_do': [],
        'search_filters': '', 'other': []
    }

    i = 1  # Skip opening brace
    while i < len(focus_lines) - 1:  # Skip closing brace
        line = focus_lines[i].strip()

        # Single line properties
        if line.startswith('id ='):
            props['id'] = line
        elif line.startswith('icon ='):
            props['icon'] = line
        elif line.startswith('x ='):
            props['x'] = line
        elif line.startswith('y ='):
            props['y'] = line
        elif line.startswith('relative_position_id ='):
            props['relative_position_id'] = line
        elif line.startswith('cost ='):
            props['cost'] = line
        elif line.startswith('search_filters ='):
            props['search_filters'] = line
        elif line.startswith('will_lead_to_war_with ='):
            props['will_lead_to_war_with'] = line

        # Multi-line blocks
        elif line.startswith('prerequisite ='):
            block_lines, next_i = extract_block(focus_lines, i)
            props['prerequisites'].append(block_lines)
            i = next_i  # Set i to the position after the block
            continue  # Skip the i += 1 at the end of the loop
        elif line.startswith('mutually_exclusive ='):
            block_lines, next_i = extract_block(focus_lines, i)
            props['mutually_exclusive'].append(block_lines)
            i = next_i  # Set i to the position after the block
            continue  # Skip the i += 1 at the end of the loop
        elif line.startswith('available ='):
            block_lines, next_i = extract_block(focus_lines, i)
            props['available'] = block_lines
            i = next_i  # Set i to the position after the block
            continue  # Skip the i += 1 at the end of the loop
        elif line.startswith('bypass ='):
            block_lines, next_i = extract_block(focus_lines, i)
            props['bypass'] = block_lines
            i = next_i  # Set i to the position after the block
            continue  # Skip the i += 1 at the end of the loop
        elif line.startswith('cancel ='):
            block_lines, next_i = extract_block(focus_lines, i)
            props['cancel'] = block_lines
            i = next_i  # Set i to the position after the block
            continue  # Skip the i += 1 at the end of the loop
        elif line.startswith('completion_reward ='):
            block_lines, next_i = extract_block(focus_lines, i)
            props['completion_reward'] = block_lines
            i = next_i  # Set i to the position after the block
            continue  # Skip the i += 1 at the end of the loop
        elif line.startswith('ai_will_do ='):
            block_lines, next_i = extract_block(focus_lines, i)
            props['ai_will_do'] = block_lines
            i = next_i  # Set i to the position after the block
            continue  # Skip the i += 1 at the end of the loop
        else:
            # Other content
            props['other'].append(focus_lines[i])

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

        # Count braces
        brace_count += line.count('{') - line.count('}')

        if brace_count == 0 and '{' in lines[start_index]:
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

    # Remove trailing blank lines
    while block_lines and block_lines[-1].strip() == '':
        block_lines.pop()

    return block_lines

def compact_block(block_lines):
    """Completely compact a block by removing all internal blank lines"""
    if not block_lines:
        return block_lines

    compacted = []
    for line in block_lines:
        stripped = line.strip()
        if stripped:  # Only keep non-empty lines
            # Preserve the original indentation structure
            compacted.append(line.rstrip())

    return compacted

def format_focus_block(props):
    """Format focus according to Bulgarian standard"""
    lines = []
    lines.append('\tfocus = {')

    # 1. ID and icon (no blank line between them)
    if props['id']:
        lines.append(f'\t\t{props["id"]}')
    if props['icon']:
        lines.append(f'\t\t{props["icon"]}')

    # 2. Blank line before position group
    lines.append('')

    # 3. Position group (x, y, relative_position_id - no blank lines between them)
    if props['x']:
        lines.append(f'\t\t{props["x"]}')
    if props['y']:
        lines.append(f'\t\t{props["y"]}')
    if props['relative_position_id']:
        lines.append(f'\t\t{props["relative_position_id"]}')

    # 4. Blank line before cost
    lines.append('')

    # 5. Cost
    if props['cost']:
        lines.append(f'\t\t{props["cost"]}')

    # 6. Blank line before prerequisites/conditions
    lines.append('')

    # 7. Prerequisites and related conditions (grouped together without internal spacing)
    condition_group_added = False

    # Add all prerequisites
    for prereq in props['prerequisites']:
        compacted_prereq = compact_block(prereq[:])  # Remove all internal blank lines
        for line in compacted_prereq:
            lines.append(line)
        condition_group_added = True

    # Add all mutually_exclusive (no spacing between these and prerequisites)
    for mutex in props['mutually_exclusive']:
        compacted_mutex = compact_block(mutex[:])
        for line in compacted_mutex:
            lines.append(line)
        condition_group_added = True

    # Add will_lead_to_war_with as single-line property
    if props['will_lead_to_war_with']:
        lines.append(f'\t\t{props["will_lead_to_war_with"]}')
        condition_group_added = True

    # Only add blank line after the entire condition group (if any conditions were added)
    if condition_group_added:
        lines.append('')

    # 8. Search filters (right after condition group, before available)
    if props['search_filters']:
        lines.append(f'\t\t{props["search_filters"]}')
        lines.append('')

    # 9. Available block
    if props['available']:
        compacted_available = compact_block(props['available'][:])  # Completely remove internal blank lines
        for line in compacted_available:
            lines.append(line)
        lines.append('')  # Always add exactly one blank line after

    # 10. Bypass block (positioned after available)
    if props['bypass']:
        compacted_bypass = compact_block(props['bypass'][:])  # Completely remove internal blank lines
        for line in compacted_bypass:
            lines.append(line)
        lines.append('')  # Always add exactly one blank line after

    # 11. Cancel block (positioned after bypass)
    if props['cancel']:
        compacted_cancel = compact_block(props['cancel'][:])  # Completely remove internal blank lines
        for line in compacted_cancel:
            lines.append(line)
        lines.append('')  # Always add exactly one blank line after

    # 12. Other properties (preserve as-is, but ensure spacing)
    if props['other']:
        for line in props['other']:
            if line.strip():  # Only add non-empty lines
                lines.append(line)
        if props['other']:  # Add blank line after other properties if they exist
            lines.append('')

    # 13. Completion reward (add log if missing)
    if props['completion_reward']:
        # Check if log exists
        has_log = any('log =' in line for line in props['completion_reward'])
        if not has_log and props['id']:
            # Add log after opening brace
            focus_id = props['id'].split('=')[1].strip()
            modified_reward = []
            for i, line in enumerate(props['completion_reward']):
                modified_reward.append(line)
                if i == 0 and '{' in line:  # After opening brace
                    modified_reward.append(f'\t\t\tlog = "[GetDateText]: [Root.GetName]: Focus {focus_id}"')
            props['completion_reward'] = modified_reward

        compacted_reward = compact_block(props['completion_reward'][:])  # Completely remove internal blank lines
        for line in compacted_reward:
            lines.append(line)
        lines.append('')  # Always add exactly one blank line after

    # 14. AI will do (always last, always multi-line)
    if props['ai_will_do']:
        # Check if ai_will_do is on a single line and reformat it
        ai_lines = props['ai_will_do']
        if len(ai_lines) == 1 and 'ai_will_do = {' in ai_lines[0]:
            # Single line format, extract the factor value and reformat
            line = ai_lines[0]
            factor_match = re.search(r'factor\s*=\s*(\d+)', line)
            if factor_match:
                factor_value = factor_match.group(1)
                lines.append('\t\tai_will_do = {')
                lines.append(f'\t\t\tfactor = {factor_value}')
                lines.append('\t\t}')
            else:
                # Fallback to original if no factor found
                compacted_ai = compact_block(ai_lines[:])
                for line in compacted_ai:
                    lines.append(line)
        else:
            # Already multiline, just compact it
            compacted_ai = compact_block(ai_lines[:])
            for line in compacted_ai:
                lines.append(line)
    else:
        lines.append('\t\tai_will_do = {')
        lines.append('\t\t\tfactor = 1')
        lines.append('\t\t}')

    lines.append('\t}')

    # Clean up excessive blank lines
    cleaned_lines = []
    blank_count = 0

    for line in lines:
        if line.strip() == '':
            blank_count += 1
            if blank_count <= 1:  # Only allow 1 consecutive blank line
                cleaned_lines.append(line)
        else:
            blank_count = 0
            cleaned_lines.append(line)

    return cleaned_lines

def standardize_focus_tree(input_file: str, output_file: str, verbose: bool = False):
    """Standardize focus tree by only reformatting focus blocks"""
    start_time = time.time()

    log_message("INFO", f"Starting standardization of {input_file}", verbose)

    if not os.path.exists(input_file):
        log_message("ERROR", f"Input file not found: {input_file}")
        return False

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        log_message("INFO", f"Read {len(lines)} lines from {input_file}", verbose)
    except Exception as e:
        log_message("ERROR", f"Failed to read {input_file}: {e}")
        return False

    # Process the file
    output_lines = []
    i = 0
    focus_count = 0

    while i < len(lines):
        line = lines[i].rstrip()

        if re.match(r'\s*focus\s*=\s*{', line):
            log_message("DEBUG", f"Found focus block at line {i+1}", verbose)

            focus_block, next_i = extract_block(lines, i)

            if focus_block:
                props = extract_focus_properties(focus_block)
                formatted_lines = format_focus_block(props)

                output_lines.extend(formatted_lines)
                focus_count += 1

                log_message("DEBUG", f"Processed focus block {focus_count}: {props.get('id', 'unknown')}", verbose)

            i = next_i
        else:
            output_lines.append(line)
            i += 1

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for line in output_lines:
                f.write(line + '\n')

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
        log_message("SUCCESS", f"Output written to: {output_file}")

    except Exception as e:
        log_message("ERROR", f"Failed to write {output_file}: {e}")
        return False

    return True

def create_backup(filename: str) -> str:
    """Create a backup of the input file"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"{filename}.backup.{timestamp}"

    try:
        with open(filename, 'r', encoding='utf-8') as src:
            with open(backup_filename, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        log_message('INFO', f'Backup created: {backup_filename}')
        return backup_filename
    except Exception as e:
        log_message('ERROR', f'Failed to create backup: {str(e)}')
        return ""

def main():
    parser = argparse.ArgumentParser(
        description='Standardize HOI4 focus tree files - only reformats focus blocks'
    )
    parser.add_argument('input_file', help='Input focus tree file')
    parser.add_argument('-o', '--output', help='Output file (default: overwrites input)')
    parser.add_argument('-b', '--backup', action='store_true', help='Create backup before modifying')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        log_message('ERROR', f"File '{args.input_file}' does not exist")
        sys.exit(1)

    output_file = args.output if args.output else args.input_file

    if args.backup:
        backup_file = create_backup(args.input_file)
        if not backup_file:
            sys.exit(1)

    log_message('INFO', f'Starting focus block standardization of {args.input_file}', args.verbose)

    if standardize_focus_tree(args.input_file, output_file, args.verbose):
        log_message('SUCCESS', f'Standardization completed: {output_file}')
    else:
        log_message('ERROR', 'Standardization failed')
        sys.exit(1)

if __name__ == '__main__':
    main()