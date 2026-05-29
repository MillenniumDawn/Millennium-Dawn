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
from typing import Any, Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared_utils import (
    compact_block,
    create_backup,
    create_standard_parser,
    extract_block,
    log_message,
)


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
        log_message("INFO", f"Starting standardization of {input_file}", self.verbose)

        if not os.path.exists(input_file):
            log_message("ERROR", f"Input file not found: {input_file}")
            return False

        try:
            with open(input_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            log_message(
                "INFO", f"Read {len(lines)} lines from {input_file}", self.verbose
            )
        except Exception as e:
            log_message("ERROR", f"Failed to read {input_file}: {e}")
            return False

        output_lines = []
        i = 0
        self.processed_count = 0

        while i < len(lines):
            line = lines[i].rstrip()

            if re.match(self.get_block_pattern(), line):
                log_message("DEBUG", f"Found block at line {i+1}", self.verbose)

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

        try:
            with open(output_file, "w", encoding="utf-8") as f:
                for line in output_lines:
                    f.write(line + "\n")

            end_time = time.time()
            elapsed_time = end_time - self.start_time

            if elapsed_time < 60:
                time_str = f"{elapsed_time:.2f} seconds"
            else:
                minutes = int(elapsed_time // 60)
                seconds = elapsed_time % 60
                time_str = f"{minutes}m {seconds:.2f}s"

            log_message("SUCCESS", f"Standardization completed in {time_str}")
            log_message("SUCCESS", f"Processed {self.processed_count} blocks")
            log_message("SUCCESS", f"Output written to: {output_file}")

        except Exception as e:
            log_message("ERROR", f"Failed to write {output_file}: {e}")
            return False

        return True


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
    """Run a standardizer with standard command line interface"""
    parser = create_standardizer_parser(description)
    args = parser.parse_args(argv)

    if not os.path.exists(args.input_file):
        log_message("ERROR", f"File '{args.input_file}' does not exist")
        sys.exit(1)

    output_file = args.output if args.output else args.input_file
    standardizer = standardizer_class(verbose=args.verbose)

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
