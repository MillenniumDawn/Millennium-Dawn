#!/usr/bin/env python3

"""
Shared utilities for Millennium Dawn tools
Common functionality shared between standardization and validation tools
"""

import argparse
import logging
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Color coding for different log levels
COLORS = {
    "SUCCESS": "\033[92m",  # Green
    "INFO": "\033[94m",  # Blue
    "DEBUG": "\033[90m",  # Gray
    "WARNING": "\033[93m",  # Yellow
    "ERROR": "\033[91m",  # Red
}
RESET_COLOR = "\033[0m"


def log_message(
    level: str, message: str, verbose: bool = False, use_colors: bool = True
):
    """Log a message with timestamp and optional color coding"""
    if level == "DEBUG" and not verbose:
        return

    timestamp = datetime.now().strftime("%H:%M:%S")

    color = COLORS.get(level, "") if use_colors else ""
    reset_color = RESET_COLOR if use_colors else ""

    formatted_message = f"{color}[{timestamp}] {level}: {message}{reset_color}"
    print(formatted_message, file=sys.stderr)


def create_standard_parser(description: str) -> argparse.ArgumentParser:
    """Create a standard argument parser for Millennium Dawn tools"""
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input_file", help="Input file to process")
    parser.add_argument(
        "-o", "--output", help="Output file (default: overwrites input)"
    )
    parser.add_argument(
        "-b", "--backup", action="store_true", help="Create backup before modifying"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "--no-color", action="store_true", help="Disable ANSI color codes in output"
    )
    return parser


def create_validation_parser(description: str) -> argparse.ArgumentParser:
    """Create a standard argument parser for Millennium Dawn validation tools"""
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="Path to the mod folder (default: current directory)",
    )
    parser.add_argument(
        "--strict", action="store_true", help="Exit with error code if issues are found"
    )
    parser.add_argument(
        "--output", "-o", type=str, help="Save validation results to file"
    )
    parser.add_argument(
        "--no-color", action="store_true", help="Disable ANSI color codes in output"
    )
    parser.add_argument(
        "--staged", action="store_true", help="Only validate git staged files"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help=f"Number of worker processes (default: auto-detect)",
    )
    return parser


def extract_block(lines: List[str], start_index: int) -> Tuple[List[str], int]:
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


def compact_block(block_lines: List[str]) -> List[str]:
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


def should_skip_file(
    filename: str, extra_skip_patterns: Optional[List[str]] = None
) -> bool:
    """Check if a file should be skipped during processing"""
    IGNORED_DIRS = ["gfx", "tools", "resources", "docs", "map"]

    normalized_path = filename.replace("\\", "/")
    for ignored_dir in IGNORED_DIRS:
        if f"/{ignored_dir}/" in normalized_path or normalized_path.startswith(
            f"{ignored_dir}/"
        ):
            return True
    if extra_skip_patterns:
        for pattern in extra_skip_patterns:
            if pattern in filename:
                return True
    return False


def find_line_number(filename: str, pattern: str, lowercase: bool = True) -> int:
    """Find the line number where a pattern occurs in a file"""
    try:
        with open(filename, "r", encoding="utf-8-sig") as f:
            for line_num, line in enumerate(f, 1):
                search_line = line.lower() if lowercase else line
                search_pattern = pattern.lower() if lowercase else pattern
                if search_pattern in search_line:
                    return line_num
    except Exception:
        pass
    return 0


def strip_comments(text: str) -> str:
    """Remove comment-only lines and inline comments from text"""
    lines = text.split("\n")
    result = []
    for line in lines:
        # Check if line is entirely a comment
        stripped = line.lstrip()
        if stripped.startswith("#"):
            result.append("")
            continue
        # Strip inline comments (# not inside quotes)
        in_quote = False
        for i, ch in enumerate(line):
            if ch == '"':
                in_quote = not in_quote
            elif ch == "#" and not in_quote:
                line = line[:i]
                break
        result.append(line)
    return "\n".join(result)


class FileOpener:
    """Helper class for opening and reading files with various options"""

    @classmethod
    def open_text_file(
        cls, filename: str, lowercase: bool = True, strip_comments_flag: bool = False
    ) -> str:
        """Open a text file with optional processing"""
        try:
            with open(filename, "r", encoding="utf-8-sig") as text_file:
                content = text_file.read()
                if strip_comments_flag:
                    content = strip_comments(content)
                if lowercase:
                    return content.lower()
                else:
                    return content
        except Exception as ex:
            log_message("WARNING", f"Skipping the file {filename}, {ex}")
            return ""


class DataCleaner:
    """Helper class for cleaning data structures"""

    @classmethod
    def clear_false_positives(cls, input_iter, false_positives: tuple = ()):
        """Remove false positives from a dictionary or list"""
        if isinstance(input_iter, dict):
            if len(false_positives) > 0:
                for key in false_positives:
                    try:
                        input_iter.pop(key)
                    except KeyError:
                        continue
            return input_iter
        elif isinstance(input_iter, list):
            if len(false_positives) > 0:
                return [i for i in input_iter if i not in false_positives]
            return input_iter

    @classmethod
    def clear_false_positives_partial_match(
        cls, input_iter, false_positives: tuple = ()
    ):
        """Remove items that partially match false positives"""
        if isinstance(input_iter, dict):
            if len(false_positives) > 0:
                skip_list = []
                for k in input_iter:
                    for f in false_positives:
                        if f in k:
                            skip_list.append(k)
                for i in skip_list:
                    if i in input_iter:
                        input_iter.pop(i)
            return input_iter
        elif isinstance(input_iter, list):
            if len(false_positives) > 0:
                skip_list = []
                for k in input_iter:
                    for f in false_positives:
                        if f in k:
                            skip_list.append(k)
                input_iter = [i for i in input_iter if i not in skip_list]
            return input_iter


def get_staged_files(
    mod_path: str, extensions: Optional[List[str]] = None
) -> Optional[List[str]]:
    """Get list of git changed files for validation.

    First checks for staged (cached) files — used in pre-commit hook context.
    Falls back to the branch diff vs main when nothing is staged, so that
    running --staged on a feature branch validates only the changed files.
    """
    if extensions is None:
        extensions = [".txt"]

    def _filter(names: list) -> list:
        return [
            os.path.join(mod_path, f)
            for f in names
            if f and any(f.endswith(ext) for ext in extensions)
        ]

    try:
        import subprocess

        def _git_diff(*args):
            result = subprocess.run(
                ["git", "diff"] + list(args) + ["--name-only", "--diff-filter=ACM"],
                cwd=mod_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip().split("\n")

        # Pre-commit hook context: files added to the index
        files = _filter(_git_diff("--cached"))
        if files:
            return files

        # Feature branch context: files changed vs main
        files = _filter(_git_diff("main...HEAD"))
        if files:
            return files

        return None
    except subprocess.CalledProcessError:
        return None
    except ImportError:
        log_message("WARNING", "Git not available, skipping staged file detection")
        return None


def run_tool_main(tool_class, description: str = "Run tool", extra_args_fn=None):
    """Main entry point for running tools with standard argument parsing"""
    parser = create_standard_parser(description)
    if extra_args_fn:
        extra_args_fn(parser)
    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        log_message("ERROR", f"File '{args.input_file}' does not exist")
        sys.exit(1)

    output_file = args.output if args.output else args.input_file
    tool = tool_class(verbose=args.verbose, use_colors=not args.no_color)

    if args.backup:
        backup_file = create_backup(args.input_file)
        if not backup_file:
            sys.exit(1)

    log_message("INFO", f"Starting processing of {args.input_file}", args.verbose)

    if tool.process_file(args.input_file, output_file):
        log_message("SUCCESS", f"Processing completed: {output_file}")
    else:
        log_message("ERROR", "Processing failed")
        sys.exit(1)


def run_validator_main(
    validator_class, description: str = "Run validation", extra_args_fn=None
):
    """Main entry point for running validators with standard argument parsing"""
    parser = create_validation_parser(description)
    if extra_args_fn:
        extra_args_fn(parser)
    args = parser.parse_args()

    mod_path = Path(args.path).resolve()
    if not mod_path.exists():
        log_message("ERROR", f"Path does not exist: {mod_path}")
        sys.exit(1)
    if not mod_path.is_dir():
        log_message("ERROR", f"Path is not a directory: {mod_path}")
        sys.exit(1)

    kwargs = dict(
        output_file=args.output,
        use_colors=not args.no_color,
        staged_only=args.staged,
        workers=args.workers,
    )
    # Pass any extra args as kwargs
    if extra_args_fn:
        for key in vars(args):
            if key not in ("path", "strict", "output", "no_color", "staged", "workers"):
                kwargs[key] = getattr(args, key)

    validator = validator_class(str(mod_path), **kwargs)
    errors_found = validator.run_all_validations()

    if args.strict and errors_found > 0:
        sys.exit(1)
    else:
        sys.exit(0)
