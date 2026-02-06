#!/usr/bin/env python3
##########################
# Comprehensive Variable and Event Target Validation Script
# Validates flags (country/state/global) and event targets
# Checks for: cleared but not set, used but not set, and unused items
# Based on Kaiserreich Autotests by Pelmen, https://github.com/Pelmen323
##########################
import argparse
import glob
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Directories to ignore during validation
IGNORED_DIRS = ["gfx", "tools", "resources", "docs", "map"]


# ANSI color codes for terminal output
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


def should_skip_file(filename: str) -> bool:
    """Check if file should be skipped based on ignored directories

    Args:
        filename (str): path to file

    Returns:
        bool: True if file should be skipped
    """
    normalized_path = filename.replace("\\", "/")
    for ignored_dir in IGNORED_DIRS:
        if f"/{ignored_dir}/" in normalized_path or normalized_path.startswith(
            f"{ignored_dir}/"
        ):
            return True
    return False


def get_staged_files(mod_path: str) -> Optional[List[str]]:
    """Get list of staged .txt and .yml files from git

    Args:
        mod_path (str): path to mod folder

    Returns:
        List of staged file paths, or None if not a git repo
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            cwd=mod_path,
            capture_output=True,
            text=True,
            check=True,
        )
        files = result.stdout.strip().split("\n")
        # Filter for .txt and .yml files only
        staged_files = [
            os.path.join(mod_path, f)
            for f in files
            if f and (f.endswith(".txt") or f.endswith(".yml"))
        ]
        return staged_files if staged_files else None
    except subprocess.CalledProcessError:
        return None


def find_line_number(filename: str, pattern: str, lowercase: bool = True) -> int:
    """Find the line number where a pattern first occurs in a file

    Args:
        filename (str): path to file
        pattern (str): pattern to search for
        lowercase (bool): whether to search case-insensitively

    Returns:
        int: line number (1-indexed) or 0 if not found
    """
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
    """Utility class for file operations"""

    @classmethod
    def open_text_file(cls, filename: str, lowercase: bool = True) -> str:
        """Opens and returns text file in utf-8-sig encoding

        Args:
            filename (str): text file to open
            lowercase (bool): defines if returned str is converted to lowercase or not. Default - True

        Returns:
            str: contents of the text file
        """
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
    """Utility class for cleaning data and removing false positives"""

    @classmethod
    def clear_false_positives_partial_match(
        cls, input_iter, false_positives: tuple = ()
    ):
        """Removes items from iterable based on partial match

        Args:
            input_iter: dict/list to remove items from
            false_positives (tuple, optional): iterable with patterns to remove

        Returns:
            dict or list: cleaned input_iter
        """
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


class Variables:
    """Class for handling flag validation"""

    @classmethod
    def get_all_used_flags(
        cls,
        mod_path: str,
        lowercase: bool = True,
        flag_type: str = "country",
        return_paths: bool = False,
        staged_files: Optional[List[str]] = None,
    ):
        """Parse all files and return list with all used flags

        Args:
            mod_path (str): path to mod folder
            lowercase (bool, optional): defines if returned list contains lowercase str or not. Defaults to True.
            flag_type (str, optional): type of flag (country/state/global). Defaults to "country".
            return_paths (bool, optional): defines if paths dict is returned. Defaults to False.
            staged_files (list, optional): list of staged files to validate (if None, validates all files)

        Returns:
            tuple or list: (flags, paths) if return_paths else flags
        """
        flags = []
        paths = {}
        if flag_type not in ["country", "state", "global"]:
            raise ValueError(
                "Unsupported flag value passed. Expected country, state, global"
            )

        # Determine which files to scan
        if staged_files:
            files_to_scan = [f for f in staged_files if f.endswith(".txt")]
        else:
            files_to_scan = glob.iglob(mod_path + "**/*.txt", recursive=True)

        for filename in files_to_scan:
            if should_skip_file(filename):
                continue
            text_file = FileOpener.open_text_file(filename, lowercase=lowercase)

            if (
                f"has_{flag_type}_flag =" in text_file
                or f"modify_{flag_type}_flag =" in text_file
            ):
                pattern_matches = re.findall(
                    r"has_" + flag_type + r"_flag = ([^ \t\n]+)", text_file
                )
                if len(pattern_matches) > 0:
                    for match in pattern_matches:
                        flags.append(match)
                        paths[match] = os.path.basename(filename)

                pattern_matches = re.findall(
                    r"[y|s]_" + flag_type + r"_flag = \{.*?flag = ([^ \t\n\}]+).*?\}",
                    text_file,
                    flags=re.MULTILINE | re.DOTALL,
                )
                if len(pattern_matches) > 0:
                    for match in pattern_matches:
                        flags.append(match)
                        paths[match] = os.path.basename(filename)

        if return_paths:
            return (flags, paths)
        else:
            return flags

    @classmethod
    def get_all_set_flags(
        cls,
        mod_path: str,
        lowercase: bool = True,
        flag_type: str = "country",
        return_paths: bool = False,
        staged_files: Optional[List[str]] = None,
    ):
        """Parse all files and return list with all set flags

        Args:
            mod_path (str): path to mod folder
            lowercase (bool, optional): defines if returned list contains lowercase str or not. Defaults to True.
            flag_type (str, optional): type of flag (country/state/global). Defaults to "country".
            return_paths (bool, optional): defines if paths dict is returned. Defaults to False.

        Returns:
            tuple or list: (flags, paths) if return_paths else flags
        """
        flags = []
        paths = {}
        if flag_type not in ["country", "state", "global"]:
            raise ValueError(
                "Unsupported flag value passed. Expected country, state, global"
            )

        # Determine which files to scan
        if staged_files:
            files_to_scan = [f for f in staged_files if f.endswith(".txt")]
        else:
            files_to_scan = glob.iglob(mod_path + "**/*.txt", recursive=True)

        for filename in files_to_scan:
            if should_skip_file(filename):
                continue
            text_file = FileOpener.open_text_file(filename, lowercase=lowercase)

            if f"set_{flag_type}_flag =" in text_file:
                pattern_matches = re.findall(
                    r"set_" + flag_type + r"_flag = ([^ \t\n]+)", text_file
                )
                if len(pattern_matches) > 0:
                    for match in pattern_matches:
                        flags.append(match)
                        paths[match] = os.path.basename(filename)

                pattern_matches = re.findall(
                    r"set_" + flag_type + r"_flag = \{.*?flag = ([^ \t\n\}]+).*?\}",
                    text_file,
                    flags=re.MULTILINE | re.DOTALL,
                )
                if len(pattern_matches) > 0:
                    for match in pattern_matches:
                        flags.append(match)
                        paths[match] = os.path.basename(filename)

        if return_paths:
            return (flags, paths)
        else:
            return flags

    @classmethod
    def get_all_cleared_flags(
        cls,
        mod_path: str,
        lowercase: bool = True,
        flag_type: str = "country",
        return_paths: bool = False,
        staged_files: Optional[List[str]] = None,
    ):
        """Parse all files and return list with all cleared flags

        Args:
            mod_path (str): path to mod folder
            lowercase (bool, optional): defines if returned list contains lowercase str or not. Defaults to True.
            flag_type (str, optional): type of flag (country/state/global). Defaults to "country".
            return_paths (bool, optional): defines if paths dict is returned. Defaults to False.

        Returns:
            tuple or list: (flags, paths) if return_paths else flags
        """
        flags = []
        paths = {}
        if flag_type not in ["country", "state", "global"]:
            raise ValueError(
                "Unsupported flag value passed. Expected country, state, global"
            )

        # Determine which files to scan
        if staged_files:
            files_to_scan = [f for f in staged_files if f.endswith(".txt")]
        else:
            files_to_scan = glob.iglob(mod_path + "**/*.txt", recursive=True)

        for filename in files_to_scan:
            if should_skip_file(filename):
                continue
            text_file = FileOpener.open_text_file(filename, lowercase=lowercase)

            if f"clr_{flag_type}_flag =" in text_file:
                pattern_matches = re.findall(
                    r"clr_" + flag_type + r"_flag = ([^ \t\n]+)", text_file
                )
                if len(pattern_matches) > 0:
                    for match in pattern_matches:
                        flags.append(match)
                        paths[match] = os.path.basename(filename)

        if return_paths:
            return (flags, paths)
        else:
            return flags


class EventTargets:
    """Class for handling event target validation"""

    @classmethod
    def get_all_used_targets(
        cls,
        mod_path: str,
        lowercase: bool = True,
        return_paths: bool = False,
        staged_files: Optional[List[str]] = None,
    ):
        """Parse all files and return list with all used event targets

        Args:
            mod_path (str): path to mod folder
            lowercase (bool, optional): defines if returned list contains lowercase str or not. Defaults to True.
            return_paths (bool, optional): defines if paths dict is returned. Defaults to False.

        Returns:
            tuple or list: (targets, paths) if return_paths else targets
        """
        targets = []
        paths = {}

        # Determine which files to scan
        if staged_files:
            files_to_scan = [f for f in staged_files if f.endswith(".txt")]
        else:
            files_to_scan = glob.iglob(mod_path + "**/*.txt", recursive=True)

        for filename in files_to_scan:
            if should_skip_file(filename):
                continue
            text_file = FileOpener.open_text_file(filename, lowercase=lowercase)
            if "tag_aliases" in filename:
                if "global_event_target =" in text_file:
                    pattern_matches = re.findall(
                        r'global_event_target = ([^ \n\t\#"]+)', text_file
                    )
                    if len(pattern_matches) > 0:
                        for match in pattern_matches:
                            targets.append(match)
                            paths[match] = os.path.basename(filename)
            else:
                if "event_target:" in text_file:
                    pattern_matches = re.findall(
                        r'event_target:([^ \n\t\#"]+)', text_file
                    )
                    if len(pattern_matches) > 0:
                        for match in pattern_matches:
                            targets.append(match)
                            paths[match] = os.path.basename(filename)

                if "has_event_target =" in text_file:
                    pattern_matches = re.findall(
                        r'has_event_target = ([^ \n\t"]+)', text_file
                    )
                    if len(pattern_matches) > 0:
                        for match in pattern_matches:
                            targets.append(match)
                            paths[match] = os.path.basename(filename)

        if return_paths:
            return (targets, paths)
        else:
            return targets

    @classmethod
    def get_all_set_targets(
        cls,
        mod_path: str,
        lowercase: bool = True,
        return_paths: bool = False,
        staged_files: Optional[List[str]] = None,
    ):
        """Parse all files and return list with all set event targets

        Args:
            mod_path (str): path to mod folder
            lowercase (bool, optional): defines if returned list contains lowercase str or not. Defaults to True.
            return_paths (bool, optional): defines if paths dict is returned. Defaults to False.

        Returns:
            tuple or list: (targets, paths) if return_paths else targets
        """
        targets = []
        paths = {}

        # Determine which files to scan
        if staged_files:
            files_to_scan = [f for f in staged_files if f.endswith(".txt")]
        else:
            files_to_scan = glob.iglob(mod_path + "**/*.txt", recursive=True)

        for filename in files_to_scan:
            if should_skip_file(filename):
                continue
            if "tag_aliases" in filename:
                continue
            text_file = FileOpener.open_text_file(filename, lowercase=lowercase)

            if "save_global_event_target_as =" in text_file:
                pattern_matches = re.findall(
                    r'save_global_event_target_as = ([^ \n\t\#"]+)', text_file
                )
                if len(pattern_matches) > 0:
                    for match in pattern_matches:
                        targets.append(match)
                        paths[match] = os.path.basename(filename)

            if "save_event_target_as =" in text_file:
                pattern_matches = re.findall(
                    r'save_event_target_as = ([^ \n\t\#"]+)', text_file
                )
                if len(pattern_matches) > 0:
                    for match in pattern_matches:
                        targets.append(match)
                        paths[match] = os.path.basename(filename)

        if return_paths:
            return (targets, paths)
        else:
            return targets

    @classmethod
    def get_all_cleared_targets(
        cls,
        mod_path: str,
        lowercase: bool = True,
        return_paths: bool = False,
        staged_files: Optional[List[str]] = None,
    ):
        """Parse all files and return list with all cleared event targets

        Args:
            mod_path (str): path to mod folder
            lowercase (bool, optional): defines if returned list contains lowercase str or not. Defaults to True.
            return_paths (bool, optional): defines if paths dict is returned. Defaults to False.

        Returns:
            tuple or list: (targets, paths) if return_paths else targets
        """
        targets = []
        paths = {}

        # Determine which files to scan
        if staged_files:
            files_to_scan = [f for f in staged_files if f.endswith(".txt")]
        else:
            files_to_scan = glob.iglob(mod_path + "**/*.txt", recursive=True)

        for filename in files_to_scan:
            if should_skip_file(filename):
                continue
            text_file = FileOpener.open_text_file(filename, lowercase=lowercase)

            if "clear_global_event_target =" in text_file:
                pattern_matches = re.findall(
                    r'clear_global_event_target = ([^ \n\t\#"]+)', text_file
                )
                if len(pattern_matches) > 0:
                    for match in pattern_matches:
                        targets.append(match)
                        paths[match] = os.path.basename(filename)

        if return_paths:
            return (targets, paths)
        else:
            return targets


class Validator:
    """Main validation class that runs all checks"""

    def __init__(
        self,
        mod_path: str,
        output_file: Optional[str] = None,
        use_colors: bool = True,
        staged_only: bool = False,
    ):
        """Initialize validator with mod path

        Args:
            mod_path (str): path to mod folder (must end with /)
            output_file (str, optional): path to output file for results
            use_colors (bool): whether to use ANSI colors in output
            staged_only (bool): only validate git staged files
        """
        if not mod_path.endswith("/"):
            mod_path += "/"
        self.mod_path = mod_path
        self.errors_found = 0
        self.output_file = output_file
        self.use_colors = use_colors
        self.staged_only = staged_only
        self.staged_files = None
        self.output_lines = []

        if staged_only:
            self.staged_files = get_staged_files(mod_path)
            if not self.staged_files:
                logging.warning("No staged .txt or .yml files found")

    def log(self, message: str, level: str = "info"):
        """Log message and optionally store for file output

        Args:
            message (str): message to log
            level (str): log level (info, warning, error)
        """
        # Strip ANSI codes if not using colors
        display_msg = (
            message if self.use_colors else re.sub(r"\033\[[0-9;]+m", "", message)
        )

        if level == "info":
            logging.info(display_msg)
        elif level == "warning":
            logging.warning(display_msg)
        elif level == "error":
            logging.error(display_msg)

        # Store for file output (without colors)
        file_msg = re.sub(r"\033\[[0-9;]+m", "", message)
        self.output_lines.append(file_msg)

    def get_full_path(self, basename: str, item: str) -> Optional[str]:
        """Find full path for a file given its basename and search item

        Args:
            basename (str): file basename
            item (str): item to search for in the file (case-sensitive)

        Returns:
            Full file path or None
        """
        for filename in glob.iglob(self.mod_path + "**/*.txt", recursive=True):
            if os.path.basename(filename) == basename:
                if should_skip_file(filename):
                    continue
                # Quick check if this might be the right file (case-sensitive)
                try:
                    with open(filename, "r", encoding="utf-8-sig") as f:
                        content = f.read()
                        if item in content:
                            return filename
                except:
                    pass
        return None

    def save_output(self):
        """Save output to file if output_file is specified"""
        if self.output_file and self.output_lines:
            try:
                with open(self.output_file, "w", encoding="utf-8") as f:
                    f.write("\n".join(self.output_lines))
                logging.info(f"Results saved to: {self.output_file}")
            except Exception as e:
                logging.error(f"Failed to save output to {self.output_file}: {e}")

    def validate_cleared_flags(self, flag_type: str, false_positives: list):
        """Validate flags that are cleared but never set

        Args:
            flag_type (str): type of flag (country/state/global)
            false_positives (list): list of patterns to skip
        """
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking cleared {flag_type} flags that are never set...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        results = []
        cleared_flags, paths = Variables.get_all_cleared_flags(
            mod_path=self.mod_path,
            lowercase=False,
            flag_type=flag_type,
            return_paths=True,
            staged_files=self.staged_files,
        )
        set_flags = Variables.get_all_set_flags(
            mod_path=self.mod_path,
            flag_type=flag_type,
            lowercase=False,
            staged_files=self.staged_files,
        )
        cleared_flags = DataCleaner.clear_false_positives_partial_match(
            cleared_flags, tuple(false_positives)
        )

        for flag in cleared_flags:
            if flag not in set_flags:
                basename = paths[flag]
                full_path = self.get_full_path(
                    basename, f"clr_{flag_type}_flag = {flag}"
                )
                if full_path:
                    rel_path = os.path.relpath(full_path, self.mod_path)
                    line_num = find_line_number(
                        full_path, f"clr_{flag_type}_flag = {flag}", lowercase=False
                    )
                    results.append({"flag": flag, "file": rel_path, "line": line_num})

        if len(results) > 0:
            self.log(
                f"{Colors.RED if self.use_colors else ''}Cleared {flag_type} flags that are never set were encountered. Flags with @ are skipped.{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
            for result in results:
                if result["line"] > 0:
                    self.log(
                        f"  {Colors.YELLOW if self.use_colors else ''}{result['file']}:{result['line']}{Colors.ENDC if self.use_colors else ''} - {result['flag']}",
                        "error",
                    )
                else:
                    self.log(
                        f"  {Colors.YELLOW if self.use_colors else ''}{result['file']}{Colors.ENDC if self.use_colors else ''} - {result['flag']}",
                        "error",
                    )
            self.log(
                f"{Colors.RED if self.use_colors else ''}{len(results)} issues found{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
            self.errors_found += len(results)
        else:
            self.log(
                f"{Colors.GREEN if self.use_colors else ''}✓ No issues found with cleared {flag_type} flags{Colors.ENDC if self.use_colors else ''}"
            )

    def validate_missing_flags(self, flag_type: str, false_positives: list):
        """Validate flags that are used but never set

        Args:
            flag_type (str): type of flag (country/state/global)
            false_positives (list): list of patterns to skip
        """
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking missing {flag_type} flags (used but not set)...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        results = []
        used_flags, paths = Variables.get_all_used_flags(
            mod_path=self.mod_path,
            lowercase=False,
            flag_type=flag_type,
            return_paths=True,
            staged_files=self.staged_files,
        )
        set_flags = Variables.get_all_set_flags(
            mod_path=self.mod_path,
            lowercase=False,
            flag_type=flag_type,
            staged_files=self.staged_files,
        )
        used_flags = DataCleaner.clear_false_positives_partial_match(
            used_flags, tuple(false_positives)
        )

        for flag in used_flags:
            if flag not in set_flags:
                basename = paths[flag]
                full_path = self.get_full_path(
                    basename, f"has_{flag_type}_flag = {flag}"
                )
                if full_path:
                    rel_path = os.path.relpath(full_path, self.mod_path)
                    line_num = find_line_number(
                        full_path, f"has_{flag_type}_flag = {flag}", lowercase=False
                    )
                    results.append({"flag": flag, "file": rel_path, "line": line_num})

        if len(results) > 0:
            self.log(
                f"{Colors.RED if self.use_colors else ''}Missing {flag_type} flags were encountered - they are not set via 'set_{flag_type}_flag'. Flags with @ are skipped.{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
            for result in results:
                if result["line"] > 0:
                    self.log(
                        f"  {Colors.YELLOW if self.use_colors else ''}{result['file']}:{result['line']}{Colors.ENDC if self.use_colors else ''} - {result['flag']}",
                        "error",
                    )
                else:
                    self.log(
                        f"  {Colors.YELLOW if self.use_colors else ''}{result['file']}{Colors.ENDC if self.use_colors else ''} - {result['flag']}",
                        "error",
                    )
            self.log(
                f"{Colors.RED if self.use_colors else ''}{len(results)} issues found{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
            self.errors_found += len(results)
        else:
            self.log(
                f"{Colors.GREEN if self.use_colors else ''}✓ No issues found with missing {flag_type} flags{Colors.ENDC if self.use_colors else ''}"
            )

    def validate_unused_flags(self, flag_type: str, false_positives: list):
        """Validate flags that are set but never used

        Args:
            flag_type (str): type of flag (country/state/global)
            false_positives (list): list of patterns to skip
        """
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking unused {flag_type} flags (set but not used)...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        results = []
        set_flags, paths = Variables.get_all_set_flags(
            mod_path=self.mod_path,
            lowercase=False,
            flag_type=flag_type,
            return_paths=True,
            staged_files=self.staged_files,
        )
        used_flags = Variables.get_all_used_flags(
            mod_path=self.mod_path,
            lowercase=False,
            flag_type=flag_type,
            staged_files=self.staged_files,
        )
        set_flags = DataCleaner.clear_false_positives_partial_match(
            set_flags, tuple(false_positives)
        )

        for flag in set_flags:
            if flag not in used_flags:
                basename = paths[flag]
                full_path = self.get_full_path(
                    basename, f"set_{flag_type}_flag = {flag}"
                )
                if full_path:
                    rel_path = os.path.relpath(full_path, self.mod_path)
                    line_num = find_line_number(
                        full_path, f"set_{flag_type}_flag = {flag}", lowercase=False
                    )
                    results.append({"flag": flag, "file": rel_path, "line": line_num})

        if len(results) > 0:
            self.log(
                f"{Colors.RED if self.use_colors else ''}Unused {flag_type} flags were encountered - they are not used via 'has_{flag_type}_flag' at least once. Flags with @ are skipped.{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
            for result in results:
                if result["line"] > 0:
                    self.log(
                        f"  {Colors.YELLOW if self.use_colors else ''}{result['file']}:{result['line']}{Colors.ENDC if self.use_colors else ''} - {result['flag']}",
                        "error",
                    )
                else:
                    self.log(
                        f"  {Colors.YELLOW if self.use_colors else ''}{result['file']}{Colors.ENDC if self.use_colors else ''} - {result['flag']}",
                        "error",
                    )
            self.log(
                f"{Colors.RED if self.use_colors else ''}{len(results)} issues found{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
            self.errors_found += len(results)
        else:
            self.log(
                f"{Colors.GREEN if self.use_colors else ''}✓ No issues found with unused {flag_type} flags{Colors.ENDC if self.use_colors else ''}"
            )

    def validate_cleared_event_targets(self):
        """Validate event targets that are cleared but not set"""
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking cleared event targets that are not set...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        results = []
        cleared_targets, paths = EventTargets.get_all_cleared_targets(
            mod_path=self.mod_path,
            lowercase=False,
            return_paths=True,
            staged_files=self.staged_files,
        )
        set_targets = EventTargets.get_all_set_targets(
            mod_path=self.mod_path, lowercase=False, staged_files=self.staged_files
        )

        for target in cleared_targets:
            if target not in set_targets:
                basename = paths[target]
                full_path = self.get_full_path(
                    basename, f"clear_global_event_target = {target}"
                )
                if full_path:
                    rel_path = os.path.relpath(full_path, self.mod_path)
                    line_num = find_line_number(
                        full_path,
                        f"clear_global_event_target = {target}",
                        lowercase=False,
                    )
                    results.append(
                        {"target": target, "file": rel_path, "line": line_num}
                    )

        if len(results) > 0:
            self.log(
                f"{Colors.RED if self.use_colors else ''}Cleared event targets that are not set were encountered.{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
            for result in results:
                if result["line"] > 0:
                    self.log(
                        f"  {Colors.YELLOW if self.use_colors else ''}{result['file']}:{result['line']}{Colors.ENDC if self.use_colors else ''} - {result['target']}",
                        "error",
                    )
                else:
                    self.log(
                        f"  {Colors.YELLOW if self.use_colors else ''}{result['file']}{Colors.ENDC if self.use_colors else ''} - {result['target']}",
                        "error",
                    )
            self.log(
                f"{Colors.RED if self.use_colors else ''}{len(results)} issues found{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
            self.errors_found += len(results)
        else:
            self.log(
                f"{Colors.GREEN if self.use_colors else ''}✓ No issues found with cleared event targets{Colors.ENDC if self.use_colors else ''}"
            )

    def validate_missing_event_targets(self):
        """Validate event targets that are used but not set"""
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking missing event targets (used but not set)...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        FALSE_POSITIVES = ["."]
        results = []
        used_targets, paths = EventTargets.get_all_used_targets(
            mod_path=self.mod_path,
            lowercase=False,
            return_paths=True,
            staged_files=self.staged_files,
        )
        set_targets = EventTargets.get_all_set_targets(
            mod_path=self.mod_path, lowercase=False, staged_files=self.staged_files
        )
        used_targets = DataCleaner.clear_false_positives_partial_match(
            used_targets, tuple(FALSE_POSITIVES)
        )

        for target in used_targets:
            if target not in set_targets:
                basename = paths[target]
                full_path = self.get_full_path(basename, f"event_target:{target}")
                if not full_path:
                    full_path = self.get_full_path(
                        basename, f"has_event_target = {target}"
                    )
                if full_path:
                    rel_path = os.path.relpath(full_path, self.mod_path)
                    line_num = find_line_number(
                        full_path, f"event_target:{target}", lowercase=False
                    )
                    if line_num == 0:
                        line_num = find_line_number(
                            full_path, f"has_event_target = {target}", lowercase=False
                        )
                    results.append(
                        {"target": target, "file": rel_path, "line": line_num}
                    )

        if len(results) > 0:
            self.log(
                f"{Colors.RED if self.use_colors else ''}Used event targets that are not set were encountered.{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
            for result in results:
                if result["line"] > 0:
                    self.log(
                        f"  {Colors.YELLOW if self.use_colors else ''}{result['file']}:{result['line']}{Colors.ENDC if self.use_colors else ''} - {result['target']}",
                        "error",
                    )
                else:
                    self.log(
                        f"  {Colors.YELLOW if self.use_colors else ''}{result['file']}{Colors.ENDC if self.use_colors else ''} - {result['target']}",
                        "error",
                    )
            self.log(
                f"{Colors.RED if self.use_colors else ''}{len(results)} issues found{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
            self.errors_found += len(results)
        else:
            self.log(
                f"{Colors.GREEN if self.use_colors else ''}✓ No issues found with missing event targets{Colors.ENDC if self.use_colors else ''}"
            )

    def validate_unused_event_targets(self):
        """Validate event targets that are set but never used"""
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking unused event targets (set but not used)...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        FALSE_POSITIVES = ["wca_usa_floyd_olson", "wca_usa_al_smith", "target_value"]
        results = []
        potential_results = []
        set_targets, paths = EventTargets.get_all_set_targets(
            mod_path=self.mod_path,
            lowercase=False,
            return_paths=True,
            staged_files=self.staged_files,
        )
        used_targets = EventTargets.get_all_used_targets(
            mod_path=self.mod_path, lowercase=False, staged_files=self.staged_files
        )
        set_targets = DataCleaner.clear_false_positives_partial_match(
            set_targets, tuple(FALSE_POSITIVES)
        )

        for target in set_targets:
            if target not in used_targets:
                potential_results.append(target)

        # Additionally checking yml files for loc functions
        targets_used_in_loc = []

        # Determine which yml files to scan
        if self.staged_files:
            yml_files_to_scan = [f for f in self.staged_files if f.endswith(".yml")]
        else:
            yml_files_to_scan = glob.iglob(self.mod_path + "**/*.yml", recursive=True)

        for filename in yml_files_to_scan:
            if should_skip_file(filename):
                continue
            text_file = FileOpener.open_text_file(filename)

            if ".get" in text_file:
                not_encountered_targets = [
                    i for i in potential_results if i not in targets_used_in_loc
                ]
                for target in not_encountered_targets:
                    if (
                        f"[{target}.getname" in text_file
                        or f"[{target}.getadjective" in text_file
                    ):
                        targets_used_in_loc.append(target)

        for target in potential_results:
            if target not in targets_used_in_loc:
                basename = paths[target]
                full_path = self.get_full_path(
                    basename, f"save_event_target_as = {target}"
                )
                if not full_path:
                    full_path = self.get_full_path(
                        basename, f"save_global_event_target_as = {target}"
                    )
                if full_path:
                    rel_path = os.path.relpath(full_path, self.mod_path)
                    line_num = find_line_number(
                        full_path, f"save_event_target_as = {target}", lowercase=False
                    )
                    if line_num == 0:
                        line_num = find_line_number(
                            full_path,
                            f"save_global_event_target_as = {target}",
                            lowercase=False,
                        )
                    results.append(
                        {"target": target, "file": rel_path, "line": line_num}
                    )

        if len(results) > 0:
            self.log(
                f"{Colors.RED if self.use_colors else ''}Unused event targets were encountered.{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
            for result in results:
                if result["line"] > 0:
                    self.log(
                        f"  {Colors.YELLOW if self.use_colors else ''}{result['file']}:{result['line']}{Colors.ENDC if self.use_colors else ''} - {result['target']}",
                        "error",
                    )
                else:
                    self.log(
                        f"  {Colors.YELLOW if self.use_colors else ''}{result['file']}{Colors.ENDC if self.use_colors else ''} - {result['target']}",
                        "error",
                    )
            self.log(
                f"{Colors.RED if self.use_colors else ''}{len(results)} issues found{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
            self.errors_found += len(results)
        else:
            self.log(
                f"{Colors.GREEN if self.use_colors else ''}✓ No issues found with unused event targets{Colors.ENDC if self.use_colors else ''}"
            )

    def run_all_validations(self):
        """Run all validation checks"""
        self.log(f"\n{'#'*80}")
        self.log(
            f"{Colors.BOLD if self.use_colors else ''}MILLENNIUM DAWN VARIABLE AND EVENT TARGET VALIDATION{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'#'*80}")
        self.log(f"Mod path: {self.mod_path}")
        if self.staged_only:
            self.log(
                f"{Colors.CYAN if self.use_colors else ''}Mode: Git staged files only{Colors.ENDC if self.use_colors else ''}"
            )
        if self.output_file:
            self.log(f"Output file: {self.output_file}")

        # Define false positives for each flag type
        FALSE_POSITIVES_GENERIC = ["@", "[", "{"]
        FALSE_POSITIVES_COUNTRY = [
            "@",
            "[",
            "{",
            "ire_got_guarantee",
            "ire_rejected_guarantee",
            "nfa_rebelled",
            "ire_alliance_refused",
            "nfa_previously_rebelled",
            "rom_deal",
            "rus_can_core",
            "sent_volunteers",
            "china_refused_alliance",
            "_QMV_voted",
            "recognised_opponent_",
            "rival_government_",
            "_QMV",
            "trade_agreement",
            "mutual_investment_treaty_",
            "libya_casablanca_accords_signed_by_",
            "_EP_agenda",
            "initiated_blockade_",
        ]
        FALSE_POSITIVES_GLOBAL = [
            "@",
            "[",
            "{",
            "kr_current_version",
            "_QMV_result",
            "_QMV_voted",
        ]
        FALSE_POSITIVES_COUNTRY_UNUSED = [
            "@",
            "[",
            "{",
            "saf_antagonise_",
            "default_puppet",
            "_QMV_voted",
            "_EP_approval",
            "recognised_opponent_",
        ]

        # Run flag validations
        for flag_type, fp_cleared, fp_missing, fp_unused in [
            (
                "country",
                FALSE_POSITIVES_COUNTRY,
                FALSE_POSITIVES_COUNTRY,
                FALSE_POSITIVES_COUNTRY_UNUSED,
            ),
            (
                "global",
                FALSE_POSITIVES_GENERIC,
                FALSE_POSITIVES_GENERIC,
                FALSE_POSITIVES_GLOBAL,
            ),
            (
                "state",
                FALSE_POSITIVES_GENERIC,
                FALSE_POSITIVES_GENERIC,
                FALSE_POSITIVES_GENERIC,
            ),
        ]:
            self.validate_cleared_flags(flag_type, fp_cleared)
            self.validate_missing_flags(flag_type, fp_missing)
            self.validate_unused_flags(flag_type, fp_unused)

        # Run event target validations
        self.validate_cleared_event_targets()
        self.validate_missing_event_targets()
        self.validate_unused_event_targets()

        # Final summary
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

        # Save output if requested
        self.save_output()

        return self.errors_found


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Validate variables and event targets in Millennium Dawn mod",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate current directory
  python validate_variables.py

  # Validate specific mod directory
  python validate_variables.py --path /path/to/mod

  # Exit with error code on issues (useful for CI/CD)
  python validate_variables.py --strict

  # Save output to file
  python validate_variables.py --output report.txt

  # Validate only git staged files (for pre-commit hook)
  python validate_variables.py --staged --strict

  # Disable colors
  python validate_variables.py --no-color
        """,
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
        "--staged",
        action="store_true",
        help="Only validate git staged files (for pre-commit hook)",
    )

    args = parser.parse_args()

    # Resolve and validate path
    mod_path = Path(args.path).resolve()
    if not mod_path.exists():
        logging.error(f"Error: Path does not exist: {mod_path}")
        sys.exit(1)

    if not mod_path.is_dir():
        logging.error(f"Error: Path is not a directory: {mod_path}")
        sys.exit(1)

    # Run validation
    validator = Validator(
        str(mod_path),
        output_file=args.output,
        use_colors=not args.no_color,
        staged_only=args.staged,
    )
    errors_found = validator.run_all_validations()

    # Exit with appropriate code
    if args.strict and errors_found > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
