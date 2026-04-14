#!/usr/bin/env python3
##########################
# Shared Validation Infrastructure
# Common classes, functions, and base validator used by all validation scripts
##########################
import glob
import json
import logging
import os
import re
import sys
from dataclasses import dataclass, field
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


class Severity:
    ERROR = "error"
    WARNING = "warning"


@dataclass
class Issue:
    severity: str
    category: str
    message: str
    file: str = ""
    line: int = 0

    def to_dict(self) -> dict:
        return {
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "file": self.file,
            "line": self.line,
        }

    def to_key(self) -> tuple:
        return (self.file, self.line, self.severity, self.category)


HOI4_BUILTIN_BLOCKS = frozenset(
    {
        "if",
        "else",
        "else_if",
        "limit",
        "AND",
        "OR",
        "NOT",
        "hidden_effect",
        "random_list",
        "tooltip",
        "custom_effect_tooltip",
        "custom_trigger_tooltip",
        "modifier",
        "random",
        "every_country",
        "random_country",
        "every_state",
        "random_state",
        "every_owned_state",
        "random_owned_state",
        "every_neighbor_country",
        "random_neighbor_country",
        "every_enemy_country",
        "random_enemy_country",
        "every_other_country",
        "random_other_country",
        "capital_scope",
        "owner",
        "controller",
        "ROOT",
        "PREV",
        "FROM",
        "country_event",
        "news_event",
        "state_event",
        "every_army_leader",
        "random_army_leader",
        "every_unit_leader",
        "random_unit_leader",
        "every_navy_leader",
        "random_navy_leader",
        "every_possible_country",
        "random_possible_country",
        "all_of",
        "any_of",
        "for_each_scope_loop",
        "while_loop_effect",
        "for_loop_effect",
        "effect_tooltip",
        "add_to_array",
        "remove_from_array",
        "overlord",
        "faction_leader",
        "any_country",
        "any_state",
        "any_owned_state",
        "any_neighbor_country",
        "any_enemy_country",
        "any_other_country",
        "any_allied_country",
        "any_country_with_original_tag",
        "any_army_leader",
        "any_navy_leader",
        "any_unit_leader",
        "any_possible_country",
        "every_allied_country",
        "random_allied_country",
        "every_occupied_country",
        "random_occupied_country",
        "any_occupied_country",
        "every_country_with_original_tag",
        "random_country_with_original_tag",
        "meta_effect",
        "meta_trigger",
    }
)


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
        if not mod_path.endswith(os.sep):
            mod_path += os.sep
        self.mod_path = mod_path
        self.errors_found = 0
        self.warnings_found = 0
        self.output_file = output_file
        self.use_colors = use_colors
        self.staged_only = staged_only
        self.workers = workers if workers else max(1, cpu_count() // 2)
        self.staged_files = None
        self.output_lines = []
        self._pool: Optional[Pool] = None
        self._regex_cache: Dict[str, re.Pattern] = {}
        self._issues: List[Issue] = []

        if staged_only:
            self.staged_files = (
                get_staged_files(mod_path, extensions=self.STAGED_EXTENSIONS) or []
            )
            if not self.staged_files:
                logging.warning("No staged files found")

    def get_regex(self, pattern: str, flags: int = 0) -> re.Pattern:
        """Get a compiled regex pattern from cache or compile and cache it."""
        key = f"{pattern}:{flags}"
        if key not in self._regex_cache:
            self._regex_cache[key] = re.compile(pattern, flags)
        return self._regex_cache[key]

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

        json_file = (
            os.path.splitext(self.output_file)[0] + ".json"
            if self.output_file
            else None
        )
        if json_file and self._issues:
            try:
                with open(json_file, "w", encoding="utf-8") as f:
                    f.write(self.get_issues_json())
                logging.info(f"JSON results saved to: {json_file}")
            except Exception as e:
                logging.error(f"Failed to save JSON to {json_file}: {e}")

    def add_issue(
        self, severity: str, category: str, message: str, file: str = "", line: int = 0
    ):
        """Add an issue to the internal list for later deduplication and reporting."""
        issue = Issue(
            severity=severity, category=category, message=message, file=file, line=line
        )
        self._issues.append(issue)
        if severity == Severity.ERROR:
            self.errors_found += 1
        elif severity == Severity.WARNING:
            self.warnings_found += 1

    def add_error(self, category: str, message: str, file: str = "", line: int = 0):
        """Convenience method to add an ERROR level issue."""
        self.add_issue(Severity.ERROR, category, message, file, line)

    def add_warning(self, category: str, message: str, file: str = "", line: int = 0):
        """Convenience method to add a WARNING level issue."""
        self.add_issue(Severity.WARNING, category, message, file, line)

    def _report(
        self,
        results: list,
        ok_msg: str,
        fail_msg: str,
        severity: str = Severity.ERROR,
        category: str = "",
    ):
        """Report results with specified severity level.

        This is the single source of truth for counting and recording issues.
        Do NOT call add_error/add_warning separately for results passed here.
        """
        color = Colors.RED if severity == Severity.ERROR else Colors.YELLOW

        if len(results) > 0:
            self.log(
                f"{color if self.use_colors else ''}{fail_msg}{Colors.ENDC if self.use_colors else ''}",
                "error" if severity == Severity.ERROR else "warning",
            )
            for r in results:
                self.log(
                    f"  {color if self.use_colors else ''}{r}{Colors.ENDC if self.use_colors else ''}",
                    "error" if severity == Severity.ERROR else "warning",
                )
                if category:
                    issue = Issue(severity=severity, category=category, message=r)
                    self._issues.append(issue)
            self.log(
                f"{color if self.use_colors else ''}{len(results)} issue(s) found{Colors.ENDC if self.use_colors else ''}",
                "error" if severity == Severity.ERROR else "warning",
            )
            if severity == Severity.ERROR:
                self.errors_found += len(results)
            else:
                self.warnings_found += len(results)
        else:
            self.log(
                f"{Colors.GREEN if self.use_colors else ''}{ok_msg}{Colors.ENDC if self.use_colors else ''}"
            )

    def get_issues_json(self) -> str:
        """Get issues as JSON string."""
        return json.dumps([issue.to_dict() for issue in self._issues], indent=2)

    def get_summary(self) -> dict:
        """Get validation summary as dict."""
        return {
            "title": self.TITLE,
            "errors": self.errors_found,
            "warnings": self.warnings_found,
            "issues": [issue.to_dict() for issue in self._issues],
        }

    def get_full_path(
        self, basename: str, item: str, file_patterns: Optional[List[str]] = None
    ) -> Optional[str]:
        if file_patterns is None:
            file_patterns = ["**/*.txt"]
        for pattern in file_patterns:
            for filename in glob.iglob(
                os.path.join(self.mod_path, pattern), recursive=True
            ):
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

        if self.staged_only:
            if not self.staged_files:
                return []
            dir_hints = [
                next((s for s in p.replace("\\", "/").split("/") if "*" not in s), "")
                for p in patterns
            ]
            files = [
                f
                for f in self.staged_files
                if any(f.endswith(ext) for ext in extensions)
                and any(
                    hint == "" or hint in f.replace("\\", "/") for hint in dir_hints
                )
            ]
        else:
            seen: Set[str] = set()
            files = []
            for pattern in patterns:
                for f in glob.iglob(
                    os.path.join(self.mod_path, pattern), recursive=True
                ):
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
        if self.errors_found == 0 and self.warnings_found == 0:
            self.log(
                f"{Colors.GREEN if self.use_colors else ''}✓ VALIDATION COMPLETE - NO ISSUES FOUND{Colors.ENDC if self.use_colors else ''}"
            )
        else:
            error_msg = f"✗ VALIDATION COMPLETE"
            if self.errors_found > 0:
                error_msg += f" - {self.errors_found} ERROR(S)"
            if self.warnings_found > 0:
                error_msg += f" - {self.warnings_found} WARNING(S)"
            self.log(
                f"{Colors.RED if self.use_colors else ''}{error_msg}{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
        self.log(f"{'#'*80}\n")

        self.save_output()
        return self.errors_found
