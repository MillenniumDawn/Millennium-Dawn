#!/usr/bin/env python3
"""
Fix helicopter DLC guards in history/countries files.

Two patterns exist:

Pattern A (3-tab indentation - already inside NSB DLC block):
  - complete_special_project = sp:sp_helicopter_project is at 1-tab (top level) but should be
    inside the if = { has_dlc = "No Step Back" } block.
  - Fix: remove the top-level occurrence, add inside the DLC block if not already there.

Pattern B (2-tab indentation - in main set_technology without DLC guard):
  - transport_helicopter_1/2 and nsb_transport_helicopter_1/2 are all in the main set_technology.
  - complete_special_project = sp:sp_helicopter_project is at top level.
  - Fix: remove helicopter techs from main set_technology, replace the top-level
    complete_special_project with a proper if/else DLC block.
"""

import os
import re

HISTORY_DIR = "/mnt/Linux/Millennium-Dawn/history/countries"


def collapse_blank_lines(content):
    """Collapse 3+ consecutive blank lines down to 2 blank lines."""
    while "\n\n\n\n" in content:
        content = content.replace("\n\n\n\n", "\n\n\n")
    return content


def fix_file(filepath):
    with open(filepath, "r", encoding="utf-8-sig") as f:
        content = f.read()

    if "nsb_transport_helicopter_1" not in content:
        return None

    original_content = content

    # Detect pattern by indentation of nsb_transport_helicopter_1
    pattern = None
    for line in content.split("\n"):
        if re.search(r"^(\t+)nsb_transport_helicopter_1 = 1$", line):
            tabs = len(line) - len(line.lstrip("\t"))
            if tabs >= 3:
                pattern = "A"
            elif tabs == 2:
                pattern = "B"
            break

    if pattern is None:
        return f"  SKIP (unknown indentation): {os.path.basename(filepath)}"

    if pattern == "B":
        # Determine which helicopter techs are present at 2-tab level
        has_heli1 = bool(
            re.search(r"^\t\ttransport_helicopter_1 = 1$", content, re.MULTILINE)
        )
        has_heli2 = bool(
            re.search(r"^\t\ttransport_helicopter_2 = 1$", content, re.MULTILINE)
        )
        has_nsb1 = bool(
            re.search(r"^\t\tnsb_transport_helicopter_1 = 1$", content, re.MULTILINE)
        )
        has_nsb2 = bool(
            re.search(r"^\t\tnsb_transport_helicopter_2 = 1$", content, re.MULTILINE)
        )

        # Build the NSB if/else block
        nsb_techs = []
        if has_nsb1:
            nsb_techs.append("\t\t\tnsb_transport_helicopter_1 = 1")
        if has_nsb2:
            nsb_techs.append("\t\t\tnsb_transport_helicopter_2 = 1")

        else_techs = []
        if has_heli1:
            else_techs.append("\t\t\t\ttransport_helicopter_1 = 1")
        if has_heli2:
            else_techs.append("\t\t\t\ttransport_helicopter_2 = 1")

        nsb_block = '\tif = { limit = { has_dlc = "No Step Back" }\n'
        nsb_block += "\t\tcomplete_special_project = sp:sp_helicopter_project\n"
        nsb_block += "\t\tset_technology = {\n"
        for tech in nsb_techs:
            nsb_block += tech + "\n"
        nsb_block += "\t\t}\n"
        if else_techs:
            nsb_block += "\t\telse = {\n"
            nsb_block += "\t\t\tset_technology = {\n"
            for tech in else_techs:
                nsb_block += tech + "\n"
            nsb_block += "\t\t\t}\n"
            nsb_block += "\t\t}\n"
        nsb_block += "\t}"

        # Remove helicopter tech lines from main set_technology (exactly 2-tab level)
        lines = content.split("\n")
        new_lines = []
        for line in lines:
            if re.search(r"^\t\t(nsb_)?transport_helicopter[12] = 1$", line):
                continue  # Remove this line
            new_lines.append(line)
        content = "\n".join(new_lines)

        # Collapse blank lines that result from removal (max 2 blank lines = 3 newlines)
        content = collapse_blank_lines(content)

        # Replace the complete_special_project = sp:sp_helicopter_project with the new if/else
        # block. Check at 1-tab first, then fall back to 2-tab (common formatting error where
        # the line appears after `\t}` but is misindented with an extra tab).
        if re.search(
            r"^\tcomplete_special_project = sp:sp_helicopter_project$",
            content,
            re.MULTILINE,
        ):
            content = re.sub(
                r"^\tcomplete_special_project = sp:sp_helicopter_project$",
                nsb_block,
                content,
                count=1,
                flags=re.MULTILINE,
            )
        elif re.search(
            r"^\t\tcomplete_special_project = sp:sp_helicopter_project$",
            content,
            re.MULTILINE,
        ):
            # Misindented at 2 tabs — replace with the block at 1-tab level
            content = re.sub(
                r"^\t\tcomplete_special_project = sp:sp_helicopter_project$",
                nsb_block,
                content,
                count=1,
                flags=re.MULTILINE,
            )
        else:
            # No complete_special_project = sp:sp_helicopter_project exists at all.
            # Insert the new if/else block right before the first NSB DLC check block.
            # Handles both single-line and two-line `if = { limit = {...} }` formats.
            nsb_if_pattern = (
                r'\tif = \{ limit = \{ has_dlc = "No Step Back" \}'
                r'|\tif = \{\n\t\tlimit = \{ has_dlc = "No Step Back" \}'
            )
            match = re.search(nsb_if_pattern, content)
            if match:
                insert_pos = match.start()
                content = (
                    content[:insert_pos] + nsb_block + "\n\n" + content[insert_pos:]
                )
            else:
                return f"  WARNING (Pattern B, no insertion point found): {os.path.basename(filepath)}"

    elif pattern == "A":
        # Check current state
        top_level_exists = bool(
            re.search(
                r"^\tcomplete_special_project = sp:sp_helicopter_project$",
                content,
                re.MULTILINE,
            )
        )
        already_inside_dlc = bool(
            re.search(
                r"^\t\tcomplete_special_project = sp:sp_helicopter_project$",
                content,
                re.MULTILINE,
            )
        )

        if top_level_exists:
            # Remove the top-level occurrence (including its trailing newline)
            content = re.sub(
                r"^\tcomplete_special_project = sp:sp_helicopter_project\n",
                "",
                content,
                count=1,
                flags=re.MULTILINE,
            )

        if not already_inside_dlc:
            # Insert complete_special_project inside the NSB DLC block,
            # right before the set_technology block that contains nsb_transport_helicopter_1
            lines = content.split("\n")
            inserted = False
            for i, line in enumerate(lines):
                if re.search(r"^\t\t\tnsb_transport_helicopter_1 = 1$", line):
                    # Look backwards for the opening set_technology = { at 2 tabs
                    for j in range(i - 1, -1, -1):
                        if re.search(r"^\t\tset_technology = \{", lines[j]):
                            lines.insert(
                                j,
                                "\t\tcomplete_special_project = sp:sp_helicopter_project",
                            )
                            inserted = True
                            break
                    break
            if not inserted:
                return f"  WARNING (Pattern A, could not find insertion point): {os.path.basename(filepath)}"
            content = "\n".join(lines)

    if content != original_content:
        with open(filepath, "w", encoding="utf-8-sig") as f:
            f.write(content)
        return f"  Fixed (Pattern {pattern}): {os.path.basename(filepath)}"
    else:
        return f"  No change needed: {os.path.basename(filepath)}"


def main():
    print("Fixing helicopter DLC blocks in history/countries files...\n")
    results = []
    fixed = 0
    warnings = 0

    for filename in sorted(os.listdir(HISTORY_DIR)):
        if not filename.endswith(".txt"):
            continue
        filepath = os.path.join(HISTORY_DIR, filename)
        result = fix_file(filepath)
        if result:
            results.append(result)
            if "Fixed" in result:
                fixed += 1
            elif "WARNING" in result or "SKIP" in result:
                warnings += 1

    for r in results:
        print(r)

    print(f"\nSummary: {fixed} files fixed, {warnings} warnings/skips")


if __name__ == "__main__":
    main()
