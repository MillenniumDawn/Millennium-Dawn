#!/usr/bin/env python3

"""
Common utilities for Millennium Dawn standardizers
Shared functionality for focus trees, events, decisions, and ideas
"""

import argparse
import os
import re
import sys
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import format_elapsed
from shared_utils import (
    atomic_write_text,
    blank_quoted_strings,
    create_backup,
    extract_block,
    log_message,
    normalize_spacing,
    run_tool_main,
    strip_inline_comment,
)

# A named block opener, or a bare brace. Ordering matters: `foo = {` has to win
# over the lone `{` alternative so the name reaches the stack.
_BRACE_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\{|\{|\}")


def code_of_line(line: str) -> str:
    """Strip a line down to what the parser sees: no comment, no quoted text."""
    return blank_quoted_strings(strip_inline_comment(line))


def find_block_span(
    lines: List[str], start: int, open_col: int
) -> Optional[Tuple[int, int]]:
    """Locate the `}` closing the `{` at (start, open_col).

    Returns `(end_line, close_col)`, or None when the braces never balance.
    Column-accurate on purpose: a per-line depth counter that stops at "depth
    reached zero" cannot tell `}` from `} }`, so it swallows the enclosing
    block's closer along with the one it wanted. Callers slice around the
    returned position instead. None means "leave this alone" — an unbalanced
    source file must not be rewritten from the opener to EOF.
    """
    depth = 0
    for index in range(start, len(lines)):
        code = code_of_line(lines[index])
        begin = open_col if index == start else 0
        for col in range(begin, len(code)):
            if code[col] == "{":
                depth += 1
            elif code[col] == "}":
                depth -= 1
                if depth == 0:
                    return index, col
    return None


def apply_brace_stack(code: str, stack: List[str]) -> None:
    """Advance a stack of enclosing block names across one line of code.

    A named opener pushes its name, a bare `{` pushes an empty string, and `}`
    pops, so `len(stack)` is the nesting depth and `stack[n]` names the block at
    each level.
    """
    for match in _BRACE_RE.finditer(code):
        if match.group(0) == "}":
            if stack:
                stack.pop()
        else:
            stack.append(match.group(1) or "")


def compact_search_filters(block_lines: List[str]) -> str:
    """Compact search_filters block into a single line with spaces between entities"""
    if not block_lines:
        return "search_filters = { }"

    entities = []
    for line in block_lines:
        if "search_filters" in line and "{" in line:
            after_brace = line.split("{", 1)[1]
            after_brace = after_brace.split("}", 1)[0]
            tokens = after_brace.strip().split()
            entities.extend(tokens)
        elif "}" in line:
            before_brace = line.split("}", 1)[0]
            tokens = before_brace.strip().split()
            entities.extend(tokens)
        else:
            tokens = line.strip().split()
            entities.extend(tokens)

    entities = [e for e in entities if e]
    return f"search_filters = {{ {' '.join(entities)} }}"


def compact_icon(block_lines: List[str]) -> str:
    """Compact icon block into a single line, handling both simple strings and multi-line blocks"""
    if not block_lines:
        return "icon = GFX_goal_generic_support_the_left_wing"

    if len(block_lines) == 1:
        return block_lines[0].strip()

    compacted_lines = []
    for line in block_lines:
        if line.strip():
            compacted_lines.append(line.rstrip())

    return "\n".join(compacted_lines)


def collapse_blank_runs(lines: List[str], max_blank: int = 1) -> List[str]:
    """Collapse consecutive blank lines to at most `max_blank` in a row."""
    result = []
    blank_count = 0
    for line in lines:
        if line.strip() == "":
            blank_count += 1
            if blank_count <= max_blank:
                result.append(line)
        else:
            blank_count = 0
            result.append(line)
    return result


def join_groups(groups: List[List[str]]) -> List[str]:
    """Join line groups with exactly one blank line between them.

    A blank line separates two groups rather than terminating one, so an absent
    property contributes no gap and the last group is not followed by a blank.
    Emitting a trailing blank per section is what left a dead line before every
    closing brace and a stray gap wherever a property was missing."""
    out: List[str] = []
    for group in groups:
        body = list(group)
        while body and not body[0].strip():
            body.pop(0)
        while body and not body[-1].strip():
            body.pop()
        if not body:
            continue
        if out:
            out.append("")
        out.extend(body)
    return out


def block_has_log(block_lines: List[str]) -> bool:
    """Check whether any line in a block contains a log statement."""
    return any("log =" in line for line in block_lines)


def inject_log_after_brace(block_lines: List[str], log_line: str) -> List[str]:
    """Return a copy of block_lines with `log_line` inserted after the first line
    that contains an opening brace. No-op if no such line exists."""
    result = []
    injected = False
    for line in block_lines:
        result.append(line)
        if not injected and "{" in line:
            result.append(log_line)
            injected = True
    return result


# Shared regex: matches the property name at the start of a stripped line
# like `prop_name = value` or `prop_name = { ... }`.
PROP_NAME_RE = re.compile(r"^(\w+)\s*=")


def emit_comments(lines: List[str], comments: List[str]) -> None:
    """Append non-blank comment lines (rstripped) onto `lines` in-place."""
    for comment in comments:
        if comment.strip():
            lines.append(comment.rstrip())


def read_lines_for_standardization(
    input_file: str, *, verbose: bool = False
) -> List[str] | None:
    """Log the start of standardization and read input_file's lines.

    Returns None (after logging the failure) if the file is missing or
    unreadable, so callers can propagate that as a standardize_file False.
    """
    log_message("INFO", f"Starting standardization of {input_file}", verbose)

    if not os.path.exists(input_file):
        log_message("ERROR", f"Input file not found: {input_file}")
        return None

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        log_message("INFO", f"Read {len(lines)} lines from {input_file}", verbose)
    except Exception as e:
        log_message("ERROR", f"Failed to read {input_file}: {e}")
        return None

    return lines


def write_standardized_output(
    output_file: str,
    output_lines: List[str],
    *,
    start_time: float,
    processed_count: int,
    unit_label: str = "blocks",
) -> bool:
    """Join, write, and log the result of a standardizer's output lines.

    Returns True on success, False (after logging) if the write fails.
    """
    try:
        output = "".join(normalize_spacing(line) + "\n" for line in output_lines)
        atomic_write_text(output_file, output)

        time_str = format_elapsed(time.time() - start_time)

        log_message("SUCCESS", f"Standardization completed in {time_str}")
        log_message("SUCCESS", f"Processed {processed_count} {unit_label}")
        log_message("SUCCESS", f"Output written to: {output_file}")

    except Exception as e:
        log_message("ERROR", f"Failed to write {output_file}: {e}")
        return False

    return True


def resolve_output_file_and_backup(args: argparse.Namespace) -> str:
    """Validate args.input_file exists, optionally back it up, and return the
    resolved output path (args.output, or args.input_file if unset).

    Exits the process (sys.exit(1)) if the input file is missing or the
    backup fails, matching every standardizer CLI's existing behavior.
    """
    if not os.path.exists(args.input_file):
        log_message("ERROR", f"File '{args.input_file}' does not exist")
        sys.exit(1)

    output_file = args.output if args.output else args.input_file

    if args.backup:
        backup_file = create_backup(args.input_file)
        if not backup_file:
            sys.exit(1)

    return output_file


class BaseStandardizer(ABC):
    """Base class for all standardizers"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.processed_count = 0
        self.start_time = time.time()

    @abstractmethod
    def get_block_pattern(self) -> str:
        """Return regex pattern to identify blocks of this type"""
        pass

    @abstractmethod
    def extract_properties(self, block_lines: List[str]) -> Dict[str, Any]:
        """Extract properties from block lines"""
        pass

    @abstractmethod
    def format_block(self, props: Dict[str, Any]) -> List[str]:
        """Format block according to standard"""
        pass

    def standardize_file(self, input_file: str, output_file: str) -> bool:
        """Standardize file by processing blocks of the target type"""
        lines = read_lines_for_standardization(input_file, verbose=self.verbose)
        if lines is None:
            return False

        output_lines = []
        i = 0
        self.processed_count = 0

        while i < len(lines):
            line = lines[i].rstrip()

            if re.match(self.get_block_pattern(), line):
                log_message("DEBUG", f"Found block at line {i + 1}", self.verbose)

                block_lines, next_i = extract_block(lines, i)

                if block_lines:
                    props = self.extract_properties(block_lines)
                    formatted_lines = self.format_block(props)

                    output_lines.extend(formatted_lines)
                    self.processed_count += 1

                    log_message(
                        "DEBUG",
                        f"Processed block {self.processed_count}: {props.get('id', 'unknown')}",
                        self.verbose,
                    )

                i = next_i
            else:
                output_lines.append(line)
                i += 1

        if self.processed_count == 0:
            log_message("INFO", "No blocks matched — skipping file write")
            return True

        return write_standardized_output(
            output_file,
            output_lines,
            start_time=self.start_time,
            processed_count=self.processed_count,
        )


def create_gate_sweep_parser(
    description: str, files_help: str
) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("files", nargs="*", help=files_help)
    parser.add_argument("--root", default=None, help="mod root (default: auto)")
    parser.add_argument("--dry-run", action="store_true", help="report, do not write")
    parser.add_argument(
        "-b", "--backup", action="store_true", help="back each file up before writing"
    )
    return parser


def create_standardizer_parser(description: str) -> argparse.ArgumentParser:
    """Create a standard argument parser for all standardizers"""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("input_file", help="Input file to standardize")
    parser.add_argument(
        "-o", "--output", help="Output file (default: overwrites input)"
    )
    parser.add_argument(
        "-b", "--backup", action="store_true", help="Create backup before modifying"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    return parser


def run_standardizer(standardizer_class, description: str, argv=None):
    """Run a standardizer with standard command line interface."""
    parser = create_standardizer_parser(description)
    run_tool_main(
        standardizer_class,
        description=description,
        method_name="standardize_file",
        argv=argv,
        parser=parser,
    )
