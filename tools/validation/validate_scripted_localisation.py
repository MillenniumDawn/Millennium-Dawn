#!/usr/bin/env python3
##########################
# Scripted Localisation Validation Script
# Validates scripted localisation definitions and usage
# Checks for: used but not defined, defined but not used
# Based on Millennium Dawn validation framework
##########################
import argparse
import glob
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

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
    """Get list of staged .txt, .yml, and .gui files from git

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
        # Filter for .txt, .yml, and .gui files
        staged_files = [
            os.path.join(mod_path, f)
            for f in files
            if f and (f.endswith(".txt") or f.endswith(".yml") or f.endswith(".gui"))
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


class ScriptedLocalisation:
    """Class for handling scripted localisation validation"""

    @classmethod
    def get_all_defined_localisations(
        cls,
        mod_path: str,
        lowercase: bool = True,
        return_paths: bool = False,
        staged_files: Optional[List[str]] = None,
    ) -> Tuple[List[str], Dict[str, str]]:
        """Parse all files and return list with all defined scripted localisations

        Args:
            mod_path (str): path to mod folder
            lowercase (bool, optional): defines if returned list contains lowercase str or not. Defaults to True.
            return_paths (bool, optional): defines if paths dict is returned. Defaults to False.
            staged_files (list, optional): list of staged files to validate (if None, validates all files)

        Returns:
            tuple or list: (localisations, paths) if return_paths else localisations
        """
        localisations = []
        paths = {}

        # Scripted localisation files are in common/scripted_localisation/
        if staged_files:
            files_to_scan = [
                f
                for f in staged_files
                if "scripted_localisation" in f and f.endswith(".txt")
            ]
        else:
            pattern = os.path.join(mod_path, "common", "scripted_localisation", "*.txt")
            files_to_scan = glob.glob(pattern)

        for filename in files_to_scan:
            if should_skip_file(filename):
                continue

            # Skip French localisation file
            if "00_scripted_localisation_FR_loc" in filename:
                continue

            text_file = FileOpener.open_text_file(filename, lowercase=lowercase)

            # Pattern: defined_text = { name = <name> ... }
            if "defined_text" in text_file and "name =" in text_file:
                # Match: name = <identifier> (including uppercase letters)
                pattern_matches = re.findall(
                    r"name\s*=\s*([a-zA-Z_0-9]+)", text_file if lowercase else text_file
                )
                if len(pattern_matches) > 0:
                    for match in pattern_matches:
                        localisations.append(match)
                        paths[match] = os.path.basename(filename)

        if return_paths:
            return (localisations, paths)
        else:
            return localisations

    @classmethod
    def get_all_used_localisations(
        cls,
        mod_path: str,
        defined_names: Set[str],
        lowercase: bool = True,
        return_paths: bool = False,
        staged_files: Optional[List[str]] = None,
    ) -> Tuple[List[str], Dict[str, str]]:
        """Parse all files and return list with all used scripted localisations

        Args:
            mod_path (str): path to mod folder
            defined_names (Set[str]): set of defined scripted localisation names to search for
            lowercase (bool, optional): defines if returned list contains lowercase str or not. Defaults to True.
            return_paths (bool, optional): defines if paths dict is returned. Defaults to False.
            staged_files (list, optional): list of staged files to validate (if None, validates all files)

        Returns:
            tuple or list: (localisations, paths) if return_paths else localisations
        """
        localisations = []
        paths = {}

        # Convert defined names to lowercase for searching if needed
        search_names = (
            {name.lower() for name in defined_names} if lowercase else defined_names
        )

        # Determine which files to scan:
        # - .gui files (interface definitions)
        # - .yml files (localisation files)
        # - .txt files ONLY in common/scripted_guis/ (scripted GUI definitions)
        if staged_files:
            files_to_scan = [
                f
                for f in staged_files
                if f.endswith(".gui")
                or f.endswith(".yml")
                or (f.endswith(".txt") and "scripted_guis" in f)
            ]
        else:
            gui_files = glob.iglob(mod_path + "**/*.gui", recursive=True)
            yml_files = glob.iglob(mod_path + "**/*.yml", recursive=True)
            scripted_gui_files = glob.iglob(
                mod_path + "common/scripted_guis/*.txt", recursive=True
            )
            files_to_scan = list(gui_files) + list(yml_files) + list(scripted_gui_files)

        for filename in files_to_scan:
            if should_skip_file(filename):
                continue

            # Skip the scripted localisation definition files themselves
            if "scripted_localisation" in filename:
                continue

            text_file = FileOpener.open_text_file(filename, lowercase=lowercase)

            # Check which defined scripted localisation names appear in this file
            # Use simple string containment for performance (much faster than regex)
            for name in search_names:
                if name not in localisations:  # Only check if not already found
                    if name in text_file:
                        localisations.append(name)
                        paths[name] = os.path.basename(filename)

        if return_paths:
            return (localisations, paths)
        else:
            return localisations


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
            item (str): item to search for in the file

        Returns:
            Full file path or None
        """
        # Search in both .txt and .gui files
        for pattern in ["**/*.txt", "**/*.gui"]:
            for filename in glob.iglob(self.mod_path + pattern, recursive=True):
                if os.path.basename(filename) == basename:
                    if should_skip_file(filename):
                        continue
                    # Quick check if this might be the right file
                    try:
                        with open(filename, "r", encoding="utf-8-sig") as f:
                            content = f.read()
                            if item.lower() in content.lower():
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

    def validate_missing_scripted_localisations(self, false_positives: List[str]):
        """Validate scripted localisations that are used but not defined

        Args:
            false_positives (list): list of patterns to skip
        """
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking missing scripted localisations (used but not defined)...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        results = []
        # First get all defined localisations
        defined_locs = ScriptedLocalisation.get_all_defined_localisations(
            mod_path=self.mod_path, lowercase=False, staged_files=self.staged_files
        )

        # Then search for uses of those specific names
        defined_names_set = set(defined_locs)
        used_locs, paths = ScriptedLocalisation.get_all_used_localisations(
            mod_path=self.mod_path,
            defined_names=defined_names_set,
            lowercase=False,
            return_paths=True,
            staged_files=self.staged_files,
        )

        # Convert to lowercase for comparison
        defined_locs_lower = [loc.lower() for loc in defined_locs]
        used_locs_lower = [loc.lower() for loc in used_locs]

        # Clean false positives
        used_locs_lower = DataCleaner.clear_false_positives_partial_match(
            used_locs_lower, tuple(false_positives)
        )

        # Track which we've already reported to avoid duplicates
        reported = set()

        for i, loc in enumerate(used_locs_lower):
            if loc not in defined_locs_lower and loc not in reported:
                # Get the original case version
                original_loc = used_locs[i]
                basename = paths.get(original_loc, paths.get(loc, "unknown"))

                # Try to find the file
                full_path = self.get_full_path(basename, loc)
                if full_path:
                    rel_path = os.path.relpath(full_path, self.mod_path)
                    line_num = find_line_number(full_path, loc, lowercase=True)
                    results.append(
                        {"localisation": loc, "file": rel_path, "line": line_num}
                    )
                    reported.add(loc)

        if len(results) > 0:
            self.log(
                f"{Colors.RED if self.use_colors else ''}Missing scripted localisations were encountered - they are referenced but not defined in common/scripted_localisation/.{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
            self.log(
                f"{Colors.YELLOW if self.use_colors else ''}Note: Some of these may be regular localisation keys rather than scripted localisation. Verify manually.{Colors.ENDC if self.use_colors else ''}",
                "warning",
            )
            for result in results:
                if result["line"] > 0:
                    self.log(
                        f"  {Colors.YELLOW if self.use_colors else ''}{result['file']}:{result['line']}{Colors.ENDC if self.use_colors else ''} - {result['localisation']}",
                        "error",
                    )
                else:
                    self.log(
                        f"  {Colors.YELLOW if self.use_colors else ''}{result['file']}{Colors.ENDC if self.use_colors else ''} - {result['localisation']}",
                        "error",
                    )
            self.log(
                f"{Colors.RED if self.use_colors else ''}{len(results)} issues found{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
            self.errors_found += len(results)
        else:
            self.log(
                f"{Colors.GREEN if self.use_colors else ''}✓ No issues found with missing scripted localisations{Colors.ENDC if self.use_colors else ''}"
            )

    def validate_unused_scripted_localisations(self, false_positives: List[str]):
        """Validate scripted localisations that are defined but not used

        Args:
            false_positives (list): list of patterns to skip
        """
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking unused scripted localisations (defined but not used)...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        results = []
        # First get all defined localisations
        defined_locs, paths = ScriptedLocalisation.get_all_defined_localisations(
            mod_path=self.mod_path,
            lowercase=False,
            return_paths=True,
            staged_files=self.staged_files,
        )

        # Then search for uses of those specific names
        defined_names_set = set(defined_locs)
        used_locs = ScriptedLocalisation.get_all_used_localisations(
            mod_path=self.mod_path,
            defined_names=defined_names_set,
            lowercase=False,
            staged_files=self.staged_files,
        )

        # Convert to lowercase for comparison
        defined_locs_lower = [loc.lower() for loc in defined_locs]
        used_locs_lower = [loc.lower() for loc in used_locs]

        # Clean false positives
        defined_locs_lower = DataCleaner.clear_false_positives_partial_match(
            defined_locs_lower, tuple(false_positives)
        )

        # Track which we've already reported to avoid duplicates
        reported = set()

        for i, loc in enumerate(defined_locs_lower):
            if loc not in used_locs_lower and loc not in reported:
                # Get the original case version
                original_loc = defined_locs[i]
                basename = paths.get(original_loc, paths.get(loc, "unknown"))

                # Find the definition file
                full_path = None
                pattern = os.path.join(
                    self.mod_path, "common", "scripted_localisation", basename
                )
                if os.path.exists(pattern):
                    full_path = pattern
                else:
                    # Try to find it
                    for filename in glob.iglob(
                        os.path.join(
                            self.mod_path, "common", "scripted_localisation", "*.txt"
                        )
                    ):
                        if os.path.basename(filename) == basename:
                            full_path = filename
                            break

                if full_path:
                    rel_path = os.path.relpath(full_path, self.mod_path)
                    line_num = find_line_number(
                        full_path, f"name = {loc}", lowercase=True
                    )
                    results.append(
                        {"localisation": loc, "file": rel_path, "line": line_num}
                    )
                    reported.add(loc)

        if len(results) > 0:
            self.log(
                f"{Colors.RED if self.use_colors else ''}Unused scripted localisations were encountered - they are defined but not referenced anywhere.{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
            for result in results:
                if result["line"] > 0:
                    self.log(
                        f"  {Colors.YELLOW if self.use_colors else ''}{result['file']}:{result['line']}{Colors.ENDC if self.use_colors else ''} - {result['localisation']}",
                        "error",
                    )
                else:
                    self.log(
                        f"  {Colors.YELLOW if self.use_colors else ''}{result['file']}{Colors.ENDC if self.use_colors else ''} - {result['localisation']}",
                        "error",
                    )
            self.log(
                f"{Colors.RED if self.use_colors else ''}{len(results)} issues found{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
            self.errors_found += len(results)
        else:
            self.log(
                f"{Colors.GREEN if self.use_colors else ''}✓ No issues found with unused scripted localisations{Colors.ENDC if self.use_colors else ''}"
            )

    def run_all_validations(self):
        """Run all validation checks"""
        self.log(f"\n{'#'*80}")
        self.log(
            f"{Colors.BOLD if self.use_colors else ''}MILLENNIUM DAWN SCRIPTED LOCALISATION VALIDATION{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'#'*80}")
        self.log(f"Mod path: {self.mod_path}")
        if self.staged_only:
            self.log(
                f"{Colors.CYAN if self.use_colors else ''}Mode: Git staged files only{Colors.ENDC if self.use_colors else ''}"
            )
        if self.output_file:
            self.log(f"Output file: {self.output_file}")

        # Define false positives
        # These are common patterns that should be skipped
        FALSE_POSITIVES = [
            # Common vanilla game references
            "root.getname",
            "this.getname",
            "from.getname",
            "prev.getname",
            "root.getadjective",
            "this.getadjective",
            "from.getadjective",
            "getdatetext",
            "getyear",
            "getmonth",
            "getday",
            # Common patterns that aren't scripted loc
            "tt",
            "_tt",
            "_desc",
            "_title",
            "button",
            "gfx_",
            "tooltip",
            # Color codes and formatting
            "§",
            "£",
            "$",
            # Variables and scope references
            "var:",
            "@",
            "[",
        ]

        # Run validations
        self.validate_missing_scripted_localisations(FALSE_POSITIVES)
        self.validate_unused_scripted_localisations(FALSE_POSITIVES)

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
        description="Validate scripted localisation in Millennium Dawn mod",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate current directory
  python validate_scripted_localisation.py

  # Validate specific mod directory
  python validate_scripted_localisation.py --path /path/to/mod

  # Exit with error code on issues (useful for CI/CD)
  python validate_scripted_localisation.py --strict

  # Save output to file
  python validate_scripted_localisation.py --output report.txt

  # Validate only git staged files (for pre-commit hook)
  python validate_scripted_localisation.py --staged --strict

  # Disable colors
  python validate_scripted_localisation.py --no-color
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
