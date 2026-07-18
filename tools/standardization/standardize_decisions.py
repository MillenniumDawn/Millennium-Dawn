#!/usr/bin/env python3

"""
Millennium Dawn Decision Standardizer
Standardizes HOI4 decision and decision category files according to Millennium Dawn coding standards
"""

import argparse
import os
from typing import Any, Dict, List

from common_utils import (
    PROP_NAME_RE,
    BaseStandardizer,
    block_has_log,
    collapse_blank_runs,
    inject_log_after_brace,
)
from shared_utils import (
    collapse_or_compact,
    convert_root_factor_to_base,
    create_backup,
    extract_block,
    log_message,
    strip_inline_comment,
)

_CATEGORY_SINGLE_LINE_PROPS = {
    "icon",
    "picture",
    "scripted_gui",
    "visible_when_empty",
    "visibility_type",
}
_CATEGORY_BLOCK_PROPS = {
    "allowed",
    "available",
    "visible",
    "target_root_trigger",
    "on_map_area",
}


def _count_braces(text: str) -> tuple:
    """Return ``(opens, closes)`` for *text*, ignoring braces inside double-quoted
    strings and after an unquoted ``#`` comment."""
    code = strip_inline_comment(text)
    opens = closes = 0
    in_str = False
    for i, c in enumerate(code):
        if c == '"' and (i == 0 or code[i - 1] != "\\"):
            in_str = not in_str
        elif not in_str:
            if c == "{":
                opens += 1
            elif c == "}":
                closes += 1
    return opens, closes


def reindent_block(block_lines: List[str], base_indent: int) -> List[str]:
    """Re-indent a block starting at base_indent tabs, tracking brace depth.

    The first line is always the property declaration (e.g. ``visible = {``)
    and is placed at *base_indent*.  Subsequent lines are indented relative
    to the brace depth so that nested blocks keep their structure.
    Closing braces ``}`` are placed at the same indent as their opening line.
    """
    if not block_lines:
        return block_lines

    result: List[str] = []
    depth = 0
    for i, line in enumerate(block_lines):
        stripped = line.strip()
        if not stripped:
            continue
        # Normalise internal whitespace (tabs → single spaces)
        normalized = " ".join(stripped.split())

        opens, closes = _count_braces(normalized)

        if i == 0:
            result.append("\t" * base_indent + normalized)
        else:
            # Closing braces sit at the same indent as their opening keyword
            if closes > opens:
                indent = base_indent + depth - (closes - opens)
            else:
                indent = base_indent + depth
            result.append("\t" * indent + normalized)
        depth += opens - closes

    return result


def _reindent_or_collapse(block_lines: List[str], base_indent: int) -> List[str]:
    """Single-line collapse a single-leaf block, else reindent at base_indent tabs."""
    collapsed = collapse_or_compact(block_lines, "\t" * base_indent)
    multi = reindent_block(block_lines, base_indent)
    if len(collapsed) == 1 and len(multi) != 1:
        return collapsed
    return multi


class DecisionCategoryStandardizer(BaseStandardizer):
    """Standardizer for HOI4 decision categories"""

    def get_block_pattern(self) -> str:
        """Return regex pattern to identify decision category blocks"""
        return r"\s*\w+_category\s*=\s*{"

    def extract_properties(self, block_lines: List[str]) -> Dict[str, Any]:
        """Extract properties from decision category block lines"""
        props: Dict[str, Any] = {
            "id": "",
            "allowed": [],
            "icon": "",
            "picture": "",
            "priority": "",
            "scripted_gui": "",
            "visible_when_empty": "",
            "visibility_type": "",
            "visible": [],
            "target_root_trigger": [],
            "on_map_area": [],
            "other": [],
        }

        if block_lines:
            first_line = block_lines[0].strip()
            if first_line and not first_line.startswith("#"):
                id_match = PROP_NAME_RE.match(first_line)
                if id_match:
                    props["id"] = id_match.group(1)

        i = 1  # Skip opening brace
        while i < len(block_lines) - 1:  # Skip closing brace
            line = block_lines[i].strip()
            match = PROP_NAME_RE.match(line)
            prop_name = match.group(1) if match else None

            if prop_name in _CATEGORY_SINGLE_LINE_PROPS:
                props[prop_name] = line
            elif prop_name == "priority":
                # priority can be `priority = 200` (single-line) or `priority = { base = 100 }` (block)
                if "{" in line:
                    block, next_i = extract_block(block_lines, i)
                    props["priority"] = block
                    i = next_i
                    continue
                else:
                    props["priority"] = line
            elif prop_name in _CATEGORY_BLOCK_PROPS:
                block, next_i = extract_block(block_lines, i)
                props[prop_name].append(block)
                i = next_i
                continue
            else:
                props["other"].append(block_lines[i])

            i += 1

        return props

    def format_block(self, props: Dict[str, Any]) -> List[str]:
        """Format decision category according to Millennium Dawn standard"""
        lines = []

        if props["id"]:
            lines.append(f"{props['id']} = {{")
        else:
            lines.append("category = {")

        for allowed in props["allowed"]:
            lines.extend(_reindent_or_collapse(allowed, 1))
            lines.append("")

        if props["icon"]:
            lines.append(f"\t{props['icon']}")

        if props["picture"]:
            lines.append(f"\t{props['picture']}")

        if props["priority"]:
            if isinstance(props["priority"], list):
                lines.extend(_reindent_or_collapse(props["priority"], 1))
                lines.append("")
            else:
                lines.append(f"\t{props['priority']}")

        if props["scripted_gui"]:
            lines.append(f"\t{props['scripted_gui']}")

        if props["visible_when_empty"]:
            lines.append(f"\t{props['visible_when_empty']}")

        if props["visibility_type"]:
            lines.append(f"\t{props['visibility_type']}")

        for visible in props["visible"]:
            lines.extend(_reindent_or_collapse(visible, 1))
            lines.append("")

        for target_root_trigger in props["target_root_trigger"]:
            lines.extend(_reindent_or_collapse(target_root_trigger, 1))
            lines.append("")

        for on_map_area in props["on_map_area"]:
            lines.extend(_reindent_or_collapse(on_map_area, 1))
            lines.append("")

        if props["other"]:
            for line in props["other"]:
                if line.strip():
                    lines.append(f"\t{line.strip()}")
            lines.append("")

        # Remove trailing blank lines before closing brace
        while lines and lines[-1] == "":
            lines.pop()
        lines.append("}")

        return collapse_blank_runs(lines)


def format_decision(block_lines: List[str]) -> List[str]:
    """Order-preserving reformat of a single decision block.

    The decision ID is read from the header line (``block_lines[0]``) — the
    only reliable source. Every body property is preserved in source order:
    block-valued properties are re-indented (or collapsed when a single leaf),
    single-line properties are whitespace-normalised, comments are kept verbatim.
    A ``log`` line is injected into ``complete_effect`` when missing.
    Header sits at one tab, body at two.
    """
    if not block_lines:
        return block_lines

    header_match = PROP_NAME_RE.match(block_lines[0].strip())
    did = header_match.group(1) if header_match else "decision"

    lines: List[str] = [f"\t{did} = {{", ""]
    i = 1  # skip opening header line
    while i < len(block_lines) - 1:  # skip closing brace
        stripped = block_lines[i].strip()
        if not stripped:
            i += 1
            continue
        if stripped.startswith("#"):
            lines.append(f"\t\t{stripped}")
            lines.append("")
            i += 1
            continue

        opens, closes = _count_braces(stripped)
        prop_match = PROP_NAME_RE.match(stripped)
        prop_name = prop_match.group(1) if prop_match else None

        if opens > closes:
            block, next_i = extract_block(block_lines, i)
            if prop_name == "complete_effect" and not block_has_log(block):
                log_line = (
                    f'\t\t\tlog = "[GetDateText]: [Root.GetName]: Decision {did}"'
                )
                block = inject_log_after_brace(block, log_line)
            elif prop_name == "ai_will_do":
                block = convert_root_factor_to_base(block)
            lines.extend(_reindent_or_collapse(block, 2))
            lines.append("")
            i = next_i
        else:
            lines.append(f"\t\t{' '.join(stripped.split())}")
            lines.append("")
            i += 1

    while lines and lines[-1] == "":
        lines.pop()
    lines.append("\t}")
    return lines


class DecisionStandardizer(BaseStandardizer):
    """Standardizer for HOI4 decision files.

    A decisions file is a set of column-0 category blocks, each containing
    one-tab decision blocks (plus the occasional category-level property or
    comment). This standardizer matches categories at the top level and, for
    each, reformats its decisions in place — preserving property order and
    never dropping or splitting content.
    """

    def get_block_pattern(self) -> str:
        """Category blocks are the only column-0 (unindented) blocks."""
        return r"^\w+\s*=\s*{"

    def extract_properties(self, block_lines: List[str]) -> Dict[str, Any]:
        """Split a category into an ordered list of children.

        Each child is tagged: ``cat_single`` / ``cat_block`` for category-level
        properties, ``decision`` for a nested decision block, ``raw`` for a
        comment or stray line kept verbatim.
        """
        props: Dict[str, Any] = {"id": "", "children": []}

        header_match = (
            PROP_NAME_RE.match(block_lines[0].strip()) if block_lines else None
        )
        if header_match:
            props["id"] = header_match.group(1)

        i = 1  # skip opening header line
        while i < len(block_lines) - 1:  # skip closing brace
            raw = block_lines[i]
            stripped = raw.strip()
            if not stripped:
                i += 1
                continue
            if stripped.startswith("#"):
                props["children"].append(("raw", raw.rstrip()))
                i += 1
                continue

            name_match = PROP_NAME_RE.match(stripped)
            name = name_match.group(1) if name_match else None
            opens, closes = _count_braces(stripped)
            opens_block = opens > closes

            if name in _CATEGORY_SINGLE_LINE_PROPS or (
                name == "priority" and "{" not in stripped
            ):
                props["children"].append(("cat_single", stripped))
                i += 1
            elif name in _CATEGORY_BLOCK_PROPS or (
                name == "priority" and "{" in stripped
            ):
                block, next_i = extract_block(block_lines, i)
                props["children"].append(("cat_block", block))
                i = next_i
            elif opens_block:
                block, next_i = extract_block(block_lines, i)
                props["children"].append(("decision", block))
                i = next_i
            else:
                props["children"].append(("raw", raw.rstrip()))
                i += 1

        return props

    def format_block(self, props: Dict[str, Any]) -> List[str]:
        """Emit the category with its children reformatted in source order."""
        cid = props["id"] or "category"
        lines: List[str] = [f"{cid} = {{", ""]

        for kind, data in props["children"]:
            if kind == "cat_single":
                lines.append(f"\t{data}")
                lines.append("")
            elif kind == "cat_block":
                lines.extend(_reindent_or_collapse(data, 1))
                lines.append("")
            elif kind == "decision":
                lines.extend(format_decision(data))
                lines.append("")
            else:  # raw — comment or stray line, hug the following block
                lines.append(data)

        while lines and lines[-1] == "":
            lines.pop()
        lines.append("}")

        return collapse_blank_runs(lines)


def detect_file_type(input_file: str) -> BaseStandardizer:
    """Return the unified decision standardizer (handles categories + decisions)."""
    return DecisionStandardizer(verbose=False)


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: standardize_decisions.py <input_file> [-o output_file] [-b] [-v]")
        sys.exit(1)

    if "--help" in sys.argv or "-h" in sys.argv:
        print("Usage: standardize_decisions.py <input_file> [-o output_file] [-b] [-v]")
        print("")
        print("Standardizes HOI4 decision and decision category files.")
        print("Detects file type automatically based on content.")
        sys.exit(0)

    parser = argparse.ArgumentParser(description="Standardize decision files")
    parser.add_argument("input_file", help="Input file to standardize")
    parser.add_argument(
        "-o", "--output", help="Output file (default: overwrites input)"
    )
    parser.add_argument(
        "-b", "--backup", action="store_true", help="Create backup before modifying"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args(sys.argv[1:])

    if not os.path.exists(args.input_file):
        log_message("ERROR", f"File '{args.input_file}' does not exist")
        sys.exit(1)

    standardizer = detect_file_type(args.input_file)
    standardizer.verbose = args.verbose

    output_file = args.output if args.output else args.input_file

    if args.backup:
        backup_file = create_backup(args.input_file)
        if not backup_file:
            sys.exit(1)

    log_message("INFO", f"Starting standardization of {args.input_file}", args.verbose)

    if standardizer.standardize_file(args.input_file, output_file):
        log_message("SUCCESS", f"Standardization completed: {output_file}")
    else:
        log_message("ERROR", "Standardization failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
