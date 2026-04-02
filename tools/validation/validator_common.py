#!/usr/bin/env python3
##########################
# Shared Validation Infrastructure
# Common classes, functions, and base validator used by all validation scripts
##########################
import glob
import logging
import os
import re
import sys
from multiprocessing import Pool, cpu_count
from typing import Callable, Dict, List, Optional, Set

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared_utils import (
    DataCleaner,
    FileOpener,
    create_validation_parser,
    find_line_number,
    get_staged_files,
    log_message,
    run_validator_main,
    should_skip_file,
    strip_comments,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


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
        self._pool: Optional[Pool] = None

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

    def _pool_map(self, func: Callable, args_list: List, chunksize: int = 50) -> List:
        """Run func over args_list using the validator's shared worker pool."""
        if self._pool is None:
            raise RuntimeError("_pool_map called outside run_all_validations")
        return self._pool.map(func, args_list, chunksize=chunksize)

    def _collect_files(
        self,
        patterns: List[str],
        extra_skip: Optional[Callable[[str], bool]] = None,
    ) -> List[str]:
        """Collect mod files matching glob patterns, with staged-file support.

        In staged mode, filters self.staged_files by extension and a coarse
        directory hint derived from each pattern's first non-wildcard segment.
        In full mode, expands each pattern via glob.iglob relative to mod_path.
        Always applies should_skip_file; extra_skip adds validator-local filtering.
        """
        extensions = list(
            {os.path.splitext(p)[1] for p in patterns if os.path.splitext(p)[1]}
        ) or [".txt"]

        if self.staged_files:
            dir_hints = [
                next((s for s in p.split("/") if "*" not in s), "") for p in patterns
            ]
            files = [
                f
                for f in self.staged_files
                if any(f.endswith(ext) for ext in extensions)
                and any(hint == "" or hint in f for hint in dir_hints)
            ]
        else:
            seen: Set[str] = set()
            files = []
            for pattern in patterns:
                for f in glob.iglob(self.mod_path + pattern, recursive=True):
                    if f not in seen:
                        seen.add(f)
                        files.append(f)

        result = [f for f in files if not should_skip_file(f)]
        if extra_skip is not None:
            result = [f for f in result if not extra_skip(f)]
        return result

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

        self._pool = Pool(processes=self.workers)
        try:
            self.run_validations()
        finally:
            self._pool.terminate()
            self._pool.join()
            self._pool = None

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
