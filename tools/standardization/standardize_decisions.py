#!/usr/bin/env python3

"""
Millennium Dawn Decision Standardizer
Standardizes HOI4 decision and decision category files according to Millennium Dawn coding standards
"""

import argparse
import os
import re
from typing import Any, Dict, List

from common_utils import (
    PROP_NAME_RE,
    BaseStandardizer,
    collapse_blank_runs,
    inject_log_after_brace,
    join_groups,
)
from shared_utils import (
    atomic_write_text,
    collapse_or_compact,
    collapse_ws_outside_quotes,
    convert_root_factor_to_base,
    create_backup,
    extract_block,
    log_message,
    strip_inline_comment,
)

# Decision/category IDs, unlike the property keywords PROP_NAME_RE matches, may
# contain hyphens (e.g. `Communist-State_invite`) — verified against every ID in
# common/decisions/. A header this can't read is surfaced as an error, not guessed.
_HEADER_ID_RE = re.compile(r"^([\w-]+)\s*=")
_ONE_LINE_EFFECT_RE = re.compile(r"^(\w+)\s*=\s*\{(.*)\}\s*$")
_EFFECT_LOG_BLOCKS = frozenset(
    {
        "complete_effect",
        "remove_effect",
        "timeout_effect",
        "cancel_effect",
    }
)


def _read_header_id(block_lines: List[str]) -> str:
    """Read the ID from a block's header line (block_lines[0]), or raise ValueError."""
    header = block_lines[0].strip() if block_lines else ""
    match = _HEADER_ID_RE.match(header)
    if not match:
        raise ValueError(f"cannot read an identifier from block header: {header!r}")
    return match.group(1)


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
        # Normalise internal whitespace (tabs → single spaces), quote-safe
        normalized = collapse_ws_outside_quotes(stripped)

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


def _split_one_line_effect(line: str) -> List[str] | None:
    """Expand ``prop = { body }`` into open / body / close lines."""
    newline = "\n" if line.endswith("\n") else ""
    raw = line[: -len(newline)] if newline else line
    indent = raw[: len(raw) - len(raw.lstrip("\t"))]
    match = _ONE_LINE_EFFECT_RE.match(raw.strip())
    if not match or match.group(1) not in _EFFECT_LOG_BLOCKS:
        return None
    body = match.group(2).strip()
    lines = [f"{indent}{match.group(1)} = {{{newline}"]
    if body:
        lines.append(f"{indent}\t{body}{newline}")
    lines.append(f"{indent}}}{newline}")
    return lines


def ensure_effect_log(block_lines: List[str], decision_id: str) -> List[str]:
    """Insert the decision log as the first statement of an effect block."""
    if not block_lines:
        return block_lines
    block = block_lines
    if len(block) == 1:
        split = _split_one_line_effect(block[0])
        if split is None:
            return block
        block = split
    open_line = block[0]
    raw = open_line[:-1] if open_line.endswith("\n") else open_line
    tabs = len(raw) - len(raw.lstrip("\t"))
    if any(
        len(line) - len(line.lstrip("\t")) == tabs + 1
        and line.lstrip("\t").startswith("log =")
        for line in block[1:]
    ):
        return block
    indent = "\t" * (tabs + 1)
    log_line = f'{indent}log = "[GetDateText]: [Root.GetName]: Decision {decision_id}"'
    if open_line.endswith("\n"):
        log_line += "\n"
    return inject_log_after_brace(block, log_line)


_SOLE_ALLOWED_RE = re.compile(r"^allowed = \{ (?:original_)?tag = [A-Z]{3} \}$")


def ensure_missing_ai_will_do(lines: List[str], base: int = 10) -> List[str]:
    """Add ``ai_will_do = { base = N }`` to decisions that have none."""
    out: List[str] = []
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        tabs = len(lines[i]) - len(lines[i].lstrip("\t"))
        if tabs == 0 and _HEADER_ID_RE.match(stripped) and "{" in lines[i]:
            category, next_i = extract_block(lines, i)
            if category:
                out.extend(_ensure_ai_in_category(category, base))
                i = next_i
                continue
        out.append(lines[i])
        i += 1
    return out


def _ensure_ai_in_category(category_lines: List[str], base: int) -> List[str]:
    out = [category_lines[0]]
    i = 1
    while i < len(category_lines) - 1:
        stripped = category_lines[i].strip()
        tabs = len(category_lines[i]) - len(category_lines[i].lstrip("\t"))
        header = _HEADER_ID_RE.match(stripped)
        opens, closes = _count_braces(stripped)
        if tabs == 1 and header and opens > closes:
            name = header.group(1)
            block, next_i = extract_block(category_lines, i)
            if name in _CATEGORY_BLOCK_PROPS or name == "priority":
                out.extend(block)
            else:
                out.extend(_ensure_ai_in_decision(block, base))
            i = next_i
            continue
        out.append(category_lines[i])
        i += 1
    out.append(category_lines[-1])
    return out


def _ensure_ai_in_decision(decision_lines: List[str], base: int) -> List[str]:
    if any("ai_will_do" in line for line in decision_lines):
        return decision_lines
    if any("days_mission_timeout" in line for line in decision_lines):
        return decision_lines
    out = list(decision_lines[:-1])
    if out and out[-1].strip():
        if not out[-1].endswith("\n"):
            out[-1] += "\n"
        out.append("\n")
    out.append(f"\t\tai_will_do = {{ base = {base} }}\n")
    out.append(decision_lines[-1])
    return out


def strip_sole_decision_allowed(lines: List[str]) -> List[str]:
    """Drop an allowed line only when it exactly repeats its category pin."""
    out: List[str] = []
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        tabs = len(lines[i]) - len(lines[i].lstrip("\t"))
        header = _HEADER_ID_RE.match(stripped)
        opens, closes = _count_braces(stripped)
        if tabs == 0 and header and opens > closes:
            category, next_i = extract_block(lines, i)
            out.extend(_strip_category_decision_allowed(category))
            i = next_i
            continue
        out.append(lines[i])
        i += 1
    return out


def _strip_category_decision_allowed(category_lines: List[str]) -> List[str]:
    category_allowed = {
        line.strip()
        for line in category_lines
        if len(line) - len(line.lstrip("\t")) == 1
        and _SOLE_ALLOWED_RE.match(line.strip())
    }
    if not category_allowed:
        return category_lines

    out = [category_lines[0]]
    i = 1
    while i < len(category_lines) - 1:
        stripped = category_lines[i].strip()
        tabs = len(category_lines[i]) - len(category_lines[i].lstrip("\t"))
        header = _HEADER_ID_RE.match(stripped)
        opens, closes = _count_braces(stripped)
        if tabs == 1 and header and opens > closes:
            name = header.group(1)
            block, next_i = extract_block(category_lines, i)
            if name in _CATEGORY_BLOCK_PROPS or name == "priority":
                out.extend(block)
            else:
                out.extend(
                    line
                    for line in block
                    if not (
                        len(line) - len(line.lstrip("\t")) == 2
                        and line.strip() in category_allowed
                    )
                )
            i = next_i
            continue
        out.append(category_lines[i])
        i += 1
    out.append(category_lines[-1])
    return out


def inject_missing_decision_logs(lines: List[str]) -> List[str]:
    """Inject missing effect logs without reformatting the rest of the file."""
    out: List[str] = []
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        tabs = len(lines[i]) - len(lines[i].lstrip("\t"))
        if tabs == 0 and _HEADER_ID_RE.match(stripped) and "{" in lines[i]:
            category, next_i = extract_block(lines, i)
            if category:
                out.extend(_inject_logs_in_category(category))
                i = next_i
                continue
        out.append(lines[i])
        i += 1
    return out


def _inject_logs_in_category(category_lines: List[str]) -> List[str]:
    out = [category_lines[0]]
    i = 1
    while i < len(category_lines) - 1:
        stripped = category_lines[i].strip()
        tabs = len(category_lines[i]) - len(category_lines[i].lstrip("\t"))
        header = _HEADER_ID_RE.match(stripped)
        opens, closes = _count_braces(stripped)
        if tabs == 1 and header and opens > closes:
            name = header.group(1)
            block, next_i = extract_block(category_lines, i)
            if name in _CATEGORY_BLOCK_PROPS or name == "priority":
                out.extend(block)
            else:
                out.extend(_inject_logs_in_decision(block))
            i = next_i
            continue
        out.append(category_lines[i])
        i += 1
    out.append(category_lines[-1])
    return out


def _inject_logs_in_decision(decision_lines: List[str]) -> List[str]:
    did = _read_header_id(decision_lines)
    out = [decision_lines[0]]
    i = 1
    while i < len(decision_lines) - 1:
        stripped = decision_lines[i].strip()
        prop = PROP_NAME_RE.match(stripped)
        opens, closes = _count_braces(stripped)
        if prop and prop.group(1) in _EFFECT_LOG_BLOCKS and opens > 0:
            block, next_i = extract_block(decision_lines, i)
            out.extend(ensure_effect_log(block, did))
            i = next_i
            continue
        out.append(decision_lines[i])
        i += 1
    out.append(decision_lines[-1])
    return out


def format_decision(block_lines: List[str]) -> List[str]:
    """Order-preserving reformat of a single decision block.

    The decision ID is read from the header line (``block_lines[0]``) — the
    only reliable source. Every body property is preserved in source order:
    block-valued properties are re-indented (or collapsed when a single leaf),
    single-line properties are whitespace-normalised, comments are kept verbatim.
    A ``log`` line is injected into complete/remove/timeout/cancel when missing.
    Header sits at one tab, body at two.
    """
    if not block_lines:
        return block_lines

    did = _read_header_id(block_lines)

    # Consecutive one-line properties share a group; each multi-line block gets
    # its own. `join_groups` then puts a single blank between groups, so a
    # decision reads as the guide's example rather than one blank per property.
    groups: List[List[str]] = []
    singles: List[str] = []
    pending: List[str] = []

    i = 1  # skip opening header line
    while i < len(block_lines) - 1:  # skip closing brace
        stripped = block_lines[i].strip()
        if not stripped:
            i += 1
            continue
        if stripped.startswith("#"):
            # The comment hugs the property it describes, so it waits for it.
            pending.append(f"\t\t{stripped}")
            i += 1
            continue

        opens, closes = _count_braces(stripped)
        prop_match = PROP_NAME_RE.match(stripped)
        prop_name = prop_match.group(1) if prop_match else None

        if opens > closes:
            block, next_i = extract_block(block_lines, i)
            if prop_name in _EFFECT_LOG_BLOCKS:
                block = ensure_effect_log(block, did)
            elif prop_name == "ai_will_do":
                block = convert_root_factor_to_base(block)
            rendered = _reindent_or_collapse(block, 2)
            if len(rendered) == 1:
                singles.extend(pending)
                singles.extend(rendered)
            else:
                if singles:
                    groups.append(singles)
                    singles = []
                groups.append(pending + rendered)
            pending = []
            i = next_i
        else:
            if prop_name in _EFFECT_LOG_BLOCKS and "log =" not in stripped:
                logged = ensure_effect_log([block_lines[i]], did)
                rendered = _reindent_or_collapse(logged, 2)
                if singles:
                    groups.append(singles)
                    singles = []
                groups.append(pending + rendered)
                pending = []
                i += 1
                continue
            singles.extend(pending)
            pending = []
            singles.append(f"\t\t{collapse_ws_outside_quotes(stripped)}")
            i += 1

    groups.append(singles)
    groups.append(pending)
    return [f"\t{did} = {{"] + join_groups(groups) + ["\t}"]


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
        props: Dict[str, Any] = {"id": _read_header_id(block_lines), "children": []}

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
        groups: List[List[str]] = []
        singles: List[str] = []
        pending: List[str] = []

        for kind, data in props["children"]:
            if kind == "cat_single":
                singles.extend(pending)
                pending = []
                singles.append(f"\t{data}")
                continue
            if kind == "raw":  # comment or stray line, hug the following block
                pending.append(data)
                continue
            if singles:
                groups.append(singles)
                singles = []
            if kind == "cat_block":
                groups.append(pending + _reindent_or_collapse(data, 1))
            else:  # decision
                groups.append(pending + format_decision(data))
            pending = []

        groups.append(singles)
        groups.append(pending)

        return collapse_blank_runs(
            [f"{props['id']} = {{"] + join_groups(groups) + ["}"]
        )


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
    parser.add_argument(
        "--logs-only",
        action="store_true",
        help="Inject missing effect logs without reformatting",
    )
    parser.add_argument(
        "--strip-sole-allowed",
        action="store_true",
        help="Remove decision-level allowed = { tag = TAG } lines",
    )
    parser.add_argument(
        "--ensure-ai-will-do",
        action="store_true",
        help="Add ai_will_do = { base = 10 } to decisions that have none",
    )
    args = parser.parse_args(sys.argv[1:])

    if not os.path.exists(args.input_file):
        log_message("ERROR", f"File '{args.input_file}' does not exist")
        sys.exit(1)

    output_file = args.output if args.output else args.input_file

    if args.backup:
        backup_file = create_backup(args.input_file)
        if not backup_file:
            sys.exit(1)

    if args.logs_only or args.strip_sole_allowed or args.ensure_ai_will_do:
        try:
            with open(args.input_file, encoding="utf-8", newline="") as handle:
                lines = handle.readlines()
        except OSError as exc:
            log_message("ERROR", f"Failed to read {args.input_file}: {exc}")
            sys.exit(1)
        new_lines = lines
        if args.logs_only:
            new_lines = inject_missing_decision_logs(new_lines)
        if args.strip_sole_allowed:
            new_lines = strip_sole_decision_allowed(new_lines)
        if args.ensure_ai_will_do:
            new_lines = ensure_missing_ai_will_do(new_lines)
        atomic_write_text(output_file, "".join(new_lines))
        log_message("SUCCESS", f"Updated decision file: {output_file}")
        return

    standardizer = detect_file_type(args.input_file)
    standardizer.verbose = args.verbose

    log_message("INFO", f"Starting standardization of {args.input_file}", args.verbose)

    if standardizer.standardize_file(args.input_file, output_file):
        log_message("SUCCESS", f"Standardization completed: {output_file}")
    else:
        log_message("ERROR", "Standardization failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
