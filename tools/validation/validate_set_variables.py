#!/usr/bin/env python3
##########################
# Variable Usage Validation Script (Multiprocessing Optimized)
# Validates that variables set with set_variable are actually referenced/used
# Based on the flag validation logic from validate_variables.py
# Optimized with multiprocessing for significantly faster execution
# By Claude Code
##########################
import glob
import os
import re
from functools import partial
from multiprocessing import Pool
from typing import Dict, List, Optional, Tuple

from validator_common import (
    BaseValidator,
    Colors,
    DataCleaner,
    FileOpener,
    find_line_number,
    run_validator_main,
    should_skip_file,
)


def process_file_for_set_variables(
    filename: str, lowercase: bool = True
) -> Tuple[List[str], Dict[str, str]]:
    if should_skip_file(filename):
        return ([], {})

    variables = []
    paths = {}
    basename = os.path.basename(filename)

    text_file = FileOpener.open_text_file(filename, lowercase=lowercase)

    if "set_variable =" in text_file:
        pattern_matches = re.findall(r"set_variable = ([^ \t\n\}]+)", text_file)
        if len(pattern_matches) > 0:
            for match in pattern_matches:
                variables.append(match)
                paths[match] = basename

        pattern_matches = re.findall(
            r"set_variable = \{[^}]*?([a-z0-9_@\.\^\[\]]+)\s*=",
            text_file,
            flags=re.MULTILINE | re.DOTALL,
        )
        if len(pattern_matches) > 0:
            for match in pattern_matches:
                if match not in ["value", "days", "months", "years", "hours"]:
                    variables.append(match)
                    paths[match] = basename

    return (variables, paths)


def count_variable_references_wrapper(
    args: Tuple[str, str, bool, Optional[List[str]]]
) -> int:
    mod_path, variable_name, lowercase, staged_files = args

    if staged_files:
        files_to_scan = [
            f for f in staged_files if f.endswith(".txt") or f.endswith(".yml")
        ]
    else:
        txt_files = list(glob.iglob(mod_path + "**/*.txt", recursive=True))
        yml_files = list(glob.iglob(mod_path + "**/*.yml", recursive=True))
        files_to_scan = txt_files + yml_files

    total_refs = 0
    for filename in files_to_scan:
        if should_skip_file(filename):
            continue

        search_var = variable_name.lower() if lowercase else variable_name
        text_file = FileOpener.open_text_file(filename, lowercase=lowercase)

        total_count = text_file.count(search_var)
        set_count = text_file.count(f"set_variable = {search_var}")
        set_count += text_file.count(f"set_variable = {{ {search_var}")
        set_count += text_file.count(f"set_variable = {{{search_var}")

        total_refs += total_count - set_count

    return total_refs


class SetVariables:
    @classmethod
    def get_all_set_variables(
        cls,
        mod_path,
        lowercase=True,
        return_paths=False,
        staged_files=None,
        workers=None,
    ):
        variables = []
        paths = {}

        if staged_files:
            files_to_scan = [f for f in staged_files if f.endswith(".txt")]
        else:
            files_to_scan = list(glob.iglob(mod_path + "**/*.txt", recursive=True))

        process_func = partial(process_file_for_set_variables, lowercase=lowercase)

        with Pool(processes=workers) as pool:
            results = pool.map(process_func, files_to_scan, chunksize=50)

        for vars_list, paths_dict in results:
            variables.extend(vars_list)
            paths.update(paths_dict)

        return (variables, paths) if return_paths else variables


class Validator(BaseValidator):
    TITLE = "SET_VARIABLE USAGE VALIDATION"
    STAGED_EXTENSIONS = [".txt", ".yml"]

    def __init__(self, mod_path, min_refs=0, **kwargs):
        super().__init__(mod_path, **kwargs)
        self.min_references = min_refs

    def run_all_validations(self):
        self.log(f"\n{'#'*80}")
        self.log(
            f"{Colors.BOLD if self.use_colors else ''}MILLENNIUM DAWN {self.TITLE}{Colors.ENDC if self.use_colors else ''}"
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

    def validate_set_variables(self, false_positives):
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

        unique_vars = {}
        for var in set_variables:
            if var not in unique_vars:
                unique_vars[var] = paths[var]

        cleaned_vars = DataCleaner.clear_false_positives_partial_match(
            list(unique_vars.keys()), tuple(false_positives)
        )

        self.log(f"Found {len(cleaned_vars)} unique variables set via set_variable")
        self.log(
            f"Checking reference counts with {self.workers} workers... (this may take a while)"
        )

        var_ref_counts = {}
        args_list = [
            (self.mod_path, var, True, self.staged_files) for var in cleaned_vars
        ]

        batch_size = self.workers * 5
        for i in range(0, len(args_list), batch_size):
            batch_args = args_list[i : i + batch_size]
            batch_vars = cleaned_vars[i : i + batch_size]

            with Pool(processes=self.workers) as pool:
                ref_counts = pool.map(
                    count_variable_references_wrapper, batch_args, chunksize=1
                )

            for var, ref_count in zip(batch_vars, ref_counts):
                var_ref_counts[var] = ref_count

            self.log(
                f"Progress: {min(i+batch_size, len(cleaned_vars))}/{len(cleaned_vars)} variables checked..."
            )

        for var, ref_count in var_ref_counts.items():
            if ref_count <= self.min_references:
                basename = unique_vars[var]
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

    def run_validations(self):
        FALSE_POSITIVES = [
            "value",
            "days",
            "months",
            "years",
            "hours",
            "@",
            "[",
            "{",
            "var:",
            "temp_",
            "^",
        ]
        self.validate_set_variables(FALSE_POSITIVES)


def add_extra_args(parser):
    parser.add_argument(
        "--min-refs",
        type=int,
        default=0,
        help="Minimum number of references required (default: 0)",
    )


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate set_variable usage in Millennium Dawn mod",
        extra_args_fn=add_extra_args,
    )
