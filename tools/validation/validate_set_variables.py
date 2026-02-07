#!/usr/bin/env python3
##########################
# Variable Usage Validation Script (Multiprocessing Optimized)
# Validates that variables set with set_variable are actually referenced/used
# Based on the flag validation logic from validate_variables.py
# Optimized with multiprocessing for significantly faster execution
# By Claude Code
##########################
import argparse
import glob
import logging
import os
import re
import subprocess
import sys
from functools import partial
from multiprocessing import Pool, cpu_count
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


def process_file_for_set_variables(
    filename: str, lowercase: bool = True
) -> Tuple[List[str], Dict[str, str]]:
    """Process a single file to extract set_variable statements

    Args:
        filename (str): path to file to process
        lowercase (bool): whether to lowercase the content

    Returns:
        Tuple of (variables list, paths dict)
    """
    if should_skip_file(filename):
        return ([], {})

    variables = []
    paths = {}
    basename = os.path.basename(filename)

    text_file = FileOpener.open_text_file(filename, lowercase=lowercase)

    if "set_variable =" in text_file:
        # Pattern 1: set_variable = var_name
        pattern_matches = re.findall(r"set_variable = ([^ \t\n\}]+)", text_file)
        if len(pattern_matches) > 0:
            for match in pattern_matches:
                variables.append(match)
                paths[match] = basename

        # Pattern 2: set_variable = { var = value }
        pattern_matches = re.findall(
            r"set_variable = \{[^}]*?([a-z0-9_@\.\^\[\]]+)\s*=",
            text_file,
            flags=re.MULTILINE | re.DOTALL,
        )
        if len(pattern_matches) > 0:
            for match in pattern_matches:
                # Filter out common keywords that aren't variable names
                if match not in ["value", "days", "months", "years", "hours"]:
                    variables.append(match)
                    paths[match] = basename

    return (variables, paths)


def count_variable_references_wrapper(
    args: Tuple[str, str, bool, Optional[List[str]]]
) -> int:
    """Wrapper function for counting variable references across all files (sequential)

    Args:
        args: Tuple of (mod_path, variable_name, lowercase, staged_files)

    Returns:
        int: total reference count for the variable
    """
    mod_path, variable_name, lowercase, staged_files = args

    # Determine which files to scan
    if staged_files:
        files_to_scan = [
            f for f in staged_files if f.endswith(".txt") or f.endswith(".yml")
        ]
    else:
        txt_files = list(glob.iglob(mod_path + "**/*.txt", recursive=True))
        yml_files = list(glob.iglob(mod_path + "**/*.yml", recursive=True))
        files_to_scan = txt_files + yml_files

    # Sequential processing (parent process handles parallelization)
    total_refs = 0
    for filename in files_to_scan:
        if should_skip_file(filename):
            continue

        search_var = variable_name.lower() if lowercase else variable_name
        text_file = FileOpener.open_text_file(filename, lowercase=lowercase)

        # Count occurrences, but subtract set_variable occurrences
        total_count = text_file.count(search_var)
        set_count = text_file.count(f"set_variable = {search_var}")
        set_count += text_file.count(f"set_variable = {{ {search_var}")
        set_count += text_file.count(f"set_variable = {{{search_var}")

        total_refs += total_count - set_count

    return total_refs


class SetVariables:
    """Class for handling set_variable validation"""

    @classmethod
    def get_all_set_variables(
        cls,
        mod_path: str,
        lowercase: bool = True,
        return_paths: bool = False,
        staged_files: Optional[List[str]] = None,
        workers: int = None,
    ) -> Tuple[List[str], Dict[str, str]]:
        """Parse all files and return list with all variables set via set_variable

        Args:
            mod_path (str): path to mod folder
            lowercase (bool, optional): defines if returned list contains lowercase str or not. Defaults to True.
            return_paths (bool, optional): defines if paths dict is returned. Defaults to False.
            staged_files (list, optional): list of staged files to validate (if None, validates all files)
            workers (int, optional): number of worker processes (defaults to CPU count)

        Returns:
            tuple or list: (variables, paths) if return_paths else variables
        """
        variables = []
        paths = {}

        # Determine which files to scan
        if staged_files:
            files_to_scan = [f for f in staged_files if f.endswith(".txt")]
        else:
            files_to_scan = list(glob.iglob(mod_path + "**/*.txt", recursive=True))

        # Use multiprocessing to process files in parallel
        if workers is None:
            workers = max(1, cpu_count() // 2)

        process_func = partial(process_file_for_set_variables, lowercase=lowercase)

        with Pool(processes=workers) as pool:
            results = pool.map(process_func, files_to_scan, chunksize=50)

        # Merge results
        for vars_list, paths_dict in results:
            variables.extend(vars_list)
            paths.update(paths_dict)

        if return_paths:
            return (variables, paths)
        else:
            return variables

    @classmethod
    def get_all_variable_references(
        cls,
        mod_path: str,
        variable_name: str,
        lowercase: bool = True,
        staged_files: Optional[List[str]] = None,
        workers: int = None,
    ) -> int:
        """Count how many times a variable is referenced in the codebase

        Args:
            mod_path (str): path to mod folder
            variable_name (str): name of the variable to search for
            lowercase (bool, optional): defines if search is case-insensitive. Defaults to True.
            staged_files (list, optional): list of staged files to validate (if None, validates all files)
            workers (int, optional): number of worker processes (defaults to CPU count)

        Returns:
            int: number of references found (excluding the set_variable statements)
        """
        # Determine which files to scan
        if staged_files:
            files_to_scan = [
                f for f in staged_files if f.endswith(".txt") or f.endswith(".yml")
            ]
        else:
            txt_files = list(glob.iglob(mod_path + "**/*.txt", recursive=True))
            yml_files = list(glob.iglob(mod_path + "**/*.yml", recursive=True))
            files_to_scan = txt_files + yml_files

        # This method is no longer used in the optimized version
        # Variables are checked via count_variable_references_wrapper which handles file scanning internally
        # Keep this for API compatibility but redirect to the wrapper
        return count_variable_references_wrapper(
            (mod_path, variable_name, lowercase, staged_files)
        )


class Validator:
    """Main validation class that runs all checks"""

    def __init__(
        self,
        mod_path: str,
        output_file: Optional[str] = None,
        use_colors: bool = True,
        staged_only: bool = False,
        min_references: int = 0,
        workers: int = None,
    ):
        """Initialize validator with mod path

        Args:
            mod_path (str): path to mod folder (must end with /)
            output_file (str, optional): path to output file for results
            use_colors (bool): whether to use ANSI colors in output
            staged_only (bool): only validate git staged files
            min_references (int): minimum number of references to not flag as issue (default: 0)
            workers (int, optional): number of worker processes (defaults to half CPU count)
        """
        if not mod_path.endswith("/"):
            mod_path += "/"
        self.mod_path = mod_path
        self.errors_found = 0
        self.output_file = output_file
        self.use_colors = use_colors
        self.staged_only = staged_only
        self.min_references = min_references
        self.workers = workers if workers else max(1, cpu_count() // 2)
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

    def validate_set_variables(self, false_positives: List[str]):
        """Validate that set variables are actually referenced

        Args:
            false_positives (list): list of patterns to skip
        """
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking set_variable usage (variables set but not referenced)...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        results = []

        self.log(
            f"Collecting all set_variable statements (using {self.workers} workers)..."
        )
        set_variables, paths = SetVariables.get_all_set_variables(
            mod_path=self.mod_path,
            lowercase=False,
            return_paths=True,
            staged_files=self.staged_files,
            workers=self.workers,
        )

        # Remove duplicates while preserving first occurrence path
        unique_vars = {}
        for var in set_variables:
            if var not in unique_vars:
                unique_vars[var] = paths[var]

        # Clean false positives
        cleaned_vars = DataCleaner.clear_false_positives_partial_match(
            list(unique_vars.keys()), tuple(false_positives)
        )

        self.log(f"Found {len(cleaned_vars)} unique variables set via set_variable")
        self.log(
            f"Checking reference counts with {self.workers} workers... (this may take a while)"
        )

        # Check references for all variables using multiprocessing
        # Strategy: Parallelize across variables (each worker processes one variable sequentially through all files)
        var_ref_counts = {}

        # Prepare arguments for each variable check
        args_list = [
            (self.mod_path, var, True, self.staged_files) for var in cleaned_vars
        ]

        # Process variables in batches to show progress
        batch_size = (
            self.workers * 5
        )  # Process 5 batches worth at a time for progress updates
        for i in range(0, len(args_list), batch_size):
            batch_args = args_list[i : i + batch_size]
            batch_vars = cleaned_vars[i : i + batch_size]

            # Use multiprocessing to check multiple variables in parallel
            with Pool(processes=self.workers) as pool:
                ref_counts = pool.map(
                    count_variable_references_wrapper, batch_args, chunksize=1
                )

            for var, ref_count in zip(batch_vars, ref_counts):
                var_ref_counts[var] = ref_count

            self.log(
                f"Progress: {min(i+batch_size, len(cleaned_vars))}/{len(cleaned_vars)} variables checked..."
            )

        # Collect results for variables below threshold
        for var, ref_count in var_ref_counts.items():
            if ref_count <= self.min_references:
                basename = unique_vars[var]
                # Try to find the file where it was set
                full_path = self.get_full_path(basename, var)
                if full_path:
                    rel_path = os.path.relpath(full_path, self.mod_path)
                    line_num = find_line_number(full_path, var, lowercase=False)
                    results.append(
                        {
                            "variable": var,
                            "file": rel_path,
                            "line": line_num,
                            "references": ref_count,
                        }
                    )
                else:
                    # Couldn't find full path, just report the basename
                    results.append(
                        {
                            "variable": var,
                            "file": basename,
                            "line": 0,
                            "references": ref_count,
                        }
                    )

        if len(results) > 0:
            self.log(
                f"{Colors.RED if self.use_colors else ''}Set variables with {self.min_references} or fewer references were found.{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
            # Sort by reference count (lowest first) then by variable name
            results.sort(key=lambda x: (x["references"], x["variable"]))

            for result in results:
                ref_text = f"({result['references']} reference{'s' if result['references'] != 1 else ''})"
                if result["line"] > 0:
                    self.log(
                        f"  {Colors.YELLOW if self.use_colors else ''}{result['file']}:{result['line']}{Colors.ENDC if self.use_colors else ''} - {result['variable']} {ref_text}",
                        "error",
                    )
                else:
                    self.log(
                        f"  {Colors.YELLOW if self.use_colors else ''}{result['file']}{Colors.ENDC if self.use_colors else ''} - {result['variable']} {ref_text}",
                        "error",
                    )
            self.log(
                f"{Colors.RED if self.use_colors else ''}{len(results)} issues found{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
            self.errors_found += len(results)
        else:
            self.log(
                f"{Colors.GREEN if self.use_colors else ''}✓ No issues found - all set variables are referenced{Colors.ENDC if self.use_colors else ''}"
            )

    def run_validation(self):
        """Run set_variable validation"""
        self.log(f"\n{'#'*80}")
        self.log(
            f"{Colors.BOLD if self.use_colors else ''}MILLENNIUM DAWN SET_VARIABLE USAGE VALIDATION{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'#'*80}")
        self.log(f"Mod path: {self.mod_path}")
        self.log(f"Minimum references required: {self.min_references}")
        self.log(f"Worker processes: {self.workers}")
        if self.staged_only:
            self.log(
                f"{Colors.CYAN if self.use_colors else ''}Mode: Git staged files only{Colors.ENDC if self.use_colors else ''}"
            )
        if self.output_file:
            self.log(f"Output file: {self.output_file}")

        # Define false positives - patterns to skip
        FALSE_POSITIVES = [
            # Keywords that aren't variable names
            "value",
            "days",
            "months",
            "years",
            "hours",
            # Template variables
            "@",
            "[",
            "{",
            # Common system variables that are dynamically referenced
            "var:",
            "temp_",
            # Array access patterns
            "^",
        ]

        self.validate_set_variables(FALSE_POSITIVES)

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
        description="Validate that variables set with set_variable are actually referenced in Millennium Dawn mod",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate current directory
  python validate_set_variables.py

  # Validate specific mod directory
  python validate_set_variables.py --path /path/to/mod

  # Exit with error code on issues (useful for CI/CD)
  python validate_set_variables.py --strict

  # Only flag variables with 0 references (default is 0)
  python validate_set_variables.py --min-refs 0

  # Flag variables with 1 or fewer references
  python validate_set_variables.py --min-refs 1

  # Save output to file
  python validate_set_variables.py --output report.txt

  # Validate only git staged files (for pre-commit hook)
  python validate_set_variables.py --staged --strict

  # Use specific number of worker processes
  python validate_set_variables.py --workers 8

  # Disable colors
  python validate_set_variables.py --no-color
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
    parser.add_argument(
        "--min-refs",
        type=int,
        default=0,
        help="Minimum number of references required (default: 0)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help=f"Number of worker processes (default: {max(1, cpu_count() // 2)} = half CPU count)",
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
        min_references=args.min_refs,
        workers=args.workers,
    )
    errors_found = validator.run_validation()

    # Exit with appropriate code
    if args.strict and errors_found > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
