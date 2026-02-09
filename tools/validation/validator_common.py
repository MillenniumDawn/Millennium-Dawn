#!/usr/bin/env python3
##########################
# Shared Validation Infrastructure
# Common classes, functions, and base validator used by all validation scripts
##########################
import argparse
import glob
import logging
import os
import re
import subprocess
import sys
from multiprocessing import cpu_count
from pathlib import Path
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

IGNORED_DIRS = ["gfx", "tools", "resources", "docs", "map"]


class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def should_skip_file(
    filename: str, extra_skip_patterns: Optional[List[str]] = None
) -> bool:
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


def get_staged_files(
    mod_path: str, extensions: Optional[List[str]] = None
) -> Optional[List[str]]:
    if extensions is None:
        extensions = [".txt"]
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            cwd=mod_path,
            capture_output=True,
            text=True,
            check=True,
        )
        files = result.stdout.strip().split("\n")
        staged_files = [
            os.path.join(mod_path, f)
            for f in files
            if f and any(f.endswith(ext) for ext in extensions)
        ]
        return staged_files if staged_files else None
    except subprocess.CalledProcessError:
        return None


def find_line_number(filename: str, pattern: str, lowercase: bool = True) -> int:
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


class FileOpener:
    @classmethod
    def open_text_file(cls, filename: str, lowercase: bool = True) -> str:
        try:
            with open(filename, "r", encoding="utf-8-sig") as text_file:
                if lowercase:
                    return text_file.read().lower()
                else:
                    return text_file.read()
        except Exception as ex:
            logging.warning(f"Skipping the file {filename}, {ex}")
            return ""


class DataCleaner:
    @classmethod
    def clear_false_positives(cls, input_iter, false_positives: tuple = ()):
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


class BaseValidator:
    TITLE = "VALIDATION"
    STAGED_EXTENSIONS = [".txt"]

    def __init__(
        self,
        mod_path: str,
        output_file: Optional[str] = None,
        use_colors: bool = True,
        staged_only: bool = False,
        workers: int = None,
        **kwargs,
    ):
        if not mod_path.endswith("/"):
            mod_path += "/"
        self.mod_path = mod_path
        self.errors_found = 0
        self.output_file = output_file
        self.use_colors = use_colors
        self.staged_only = staged_only
        self.workers = workers if workers else max(1, cpu_count() // 2)
        self.staged_files = None
        self.output_lines = []

        if staged_only:
            self.staged_files = get_staged_files(
                mod_path, extensions=self.STAGED_EXTENSIONS
            )
            if not self.staged_files:
                logging.warning("No staged files found")

    def log(self, message: str, level: str = "info"):
        display_msg = (
            message if self.use_colors else re.sub(r"\033\[[0-9;]+m", "", message)
        )
        if level == "info":
            logging.info(display_msg)
        elif level == "warning":
            logging.warning(display_msg)
        elif level == "error":
            logging.error(display_msg)
        file_msg = re.sub(r"\033\[[0-9;]+m", "", message)
        self.output_lines.append(file_msg)

    def save_output(self):
        if self.output_file and self.output_lines:
            try:
                with open(self.output_file, "w", encoding="utf-8") as f:
                    f.write("\n".join(self.output_lines))
                logging.info(f"Results saved to: {self.output_file}")
            except Exception as e:
                logging.error(f"Failed to save output to {self.output_file}: {e}")

    def _report(self, results: list, ok_msg: str, fail_msg: str):
        if len(results) > 0:
            self.log(
                f"{Colors.RED if self.use_colors else ''}{fail_msg}{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
            for r in results:
                self.log(
                    f"  {Colors.YELLOW if self.use_colors else ''}{r}{Colors.ENDC if self.use_colors else ''}",
                    "error",
                )
            self.log(
                f"{Colors.RED if self.use_colors else ''}{len(results)} issues found{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
            self.errors_found += len(results)
        else:
            self.log(
                f"{Colors.GREEN if self.use_colors else ''}{ok_msg}{Colors.ENDC if self.use_colors else ''}"
            )

    def get_full_path(
        self, basename: str, item: str, file_patterns: Optional[List[str]] = None
    ) -> Optional[str]:
        if file_patterns is None:
            file_patterns = ["**/*.txt"]
        for pattern in file_patterns:
            for filename in glob.iglob(self.mod_path + pattern, recursive=True):
                if os.path.basename(filename) == basename:
                    if should_skip_file(filename):
                        continue
                    try:
                        with open(filename, "r", encoding="utf-8-sig") as f:
                            content = f.read()
                            if item in content:
                                return filename
                    except Exception:
                        pass
        return None

    def run_validations(self):
        raise NotImplementedError("Subclasses must implement run_validations()")

    def run_all_validations(self):
        self.log(f"\n{'#'*80}")
        self.log(
            f"{Colors.BOLD if self.use_colors else ''}MILLENNIUM DAWN {self.TITLE}{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'#'*80}")
        self.log(f"Mod path: {self.mod_path}")
        self.log(f"Worker processes: {self.workers}")
        if self.staged_only:
            self.log(
                f"{Colors.CYAN if self.use_colors else ''}Mode: Git staged files only{Colors.ENDC if self.use_colors else ''}"
            )
        if self.output_file:
            self.log(f"Output file: {self.output_file}")

        self.run_validations()

        self.log(f"\n{'#'*80}")
        if self.errors_found == 0:
            self.log(
                f"{Colors.GREEN if self.use_colors else ''}✓ VALIDATION COMPLETE - NO ISSUES FOUND{Colors.ENDC if self.use_colors else ''}"
            )
        else:
            self.log(
                f"{Colors.RED if self.use_colors else ''}✗ VALIDATION COMPLETE - {self.errors_found} TOTAL ISSUES FOUND{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
        self.log(f"{'#'*80}\n")

        self.save_output()
        return self.errors_found


def create_argument_parser(description: str) -> argparse.ArgumentParser:
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
        help=f"Number of worker processes (default: {max(1, cpu_count() // 2)})",
    )
    return parser


def run_validator_main(
    validator_class, description: str = "Run validation", extra_args_fn=None
):
    parser = create_argument_parser(description)
    if extra_args_fn:
        extra_args_fn(parser)
    args = parser.parse_args()

    mod_path = Path(args.path).resolve()
    if not mod_path.exists():
        logging.error(f"Error: Path does not exist: {mod_path}")
        sys.exit(1)
    if not mod_path.is_dir():
        logging.error(f"Error: Path is not a directory: {mod_path}")
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
