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
    Severity,
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

    text_file = FileOpener.open_text_file(
        filename, lowercase=lowercase, strip_comments_flag=True
    )

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


def count_all_variables_in_file(args: Tuple[str, frozenset, bool]) -> Dict[str, int]:
    """Scan one file for references to all tracked variables in a single read.

    Returns {var: net_ref_count} with only variables that have net_ref_count > 0.
    This inverted approach (scan per-file, not per-variable) eliminates the O(N×M)
    pool churn of the old per-variable wrapper.
    """
    filename, tracked_vars, lowercase = args

    if should_skip_file(filename):
        return {}

    text_file = FileOpener.open_text_file(
        filename, lowercase=lowercase, strip_comments_flag=True
    )

    result = {}
    for var in tracked_vars:
        total = text_file.count(var)
        if total == 0:
            continue
        set_count = text_file.count(f"set_variable = {var}")
        set_count += text_file.count(f"set_variable = {{ {var}")
        set_count += text_file.count(f"set_variable = {{{var}")
        net = total - set_count
        if net > 0:
            result[var] = net
    return result


class SetVariables:
    @classmethod
    def get_all_set_variables(
        cls,
        mod_path,
        lowercase=True,
        return_paths=False,
        staged_files=None,
        workers=None,
        pool=None,
    ):
        variables = []
        paths = {}

        if staged_files:
            files_to_scan = [f for f in staged_files if f.endswith(".txt")]
        else:
            files_to_scan = list(
                glob.iglob(os.path.join(mod_path, "**", "*.txt"), recursive=True)
            )

        process_func = partial(process_file_for_set_variables, lowercase=lowercase)

        p = pool if pool else Pool(processes=workers)
        results = p.map(process_func, files_to_scan, chunksize=50)
        if not pool:
            p.close()

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

    def validate_set_variables(self, false_positives):
        self._log_section(
            "Checking set_variable usage (variables set but not referenced)..."
        )

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
        self.log(f"Checking reference counts with {self.workers} workers...")

        # Build the full file list once, then scan every file once for ALL variables —
        # O(files) instead of O(variables × files) with the old per-variable approach.
        if self.staged_files:
            files_to_scan = [
                f for f in self.staged_files if f.endswith(".txt") or f.endswith(".yml")
            ]
        else:
            txt_files = list(
                glob.iglob(os.path.join(self.mod_path, "**", "*.txt"), recursive=True)
            )
            yml_files = list(
                glob.iglob(os.path.join(self.mod_path, "**", "*.yml"), recursive=True)
            )
            files_to_scan = txt_files + yml_files

        tracked_vars = frozenset(cleaned_vars)
        args_list = [(f, tracked_vars, True) for f in files_to_scan]

        var_ref_counts = {var: 0 for var in cleaned_vars}
        if self._pool is not None:
            all_file_counts = self._pool.map(
                count_all_variables_in_file, args_list, chunksize=20
            )
        else:
            with Pool(processes=self.workers) as p:
                all_file_counts = p.map(
                    count_all_variables_in_file, args_list, chunksize=20
                )
        for file_counts in all_file_counts:
            for var, count in file_counts.items():
                var_ref_counts[var] = var_ref_counts.get(var, 0) + count

        for var, ref_count in var_ref_counts.items():
            if ref_count <= self.min_references:
                basename = unique_vars[var]
                ref_text = f"(refs: {ref_count})"
                full_path = self.get_full_path(basename, var)
                if full_path:
                    rel_path = os.path.relpath(full_path, self.mod_path)
                    line_num = find_line_number(full_path, var, lowercase=False)
                    results.append((f"{var} {ref_text}", rel_path, line_num))
                else:
                    results.append((f"{var} {ref_text}", basename, 0))

        results.sort(key=lambda x: x[0])

        self._report(
            results,
            "✓ No issues found - all set variables are referenced",
            f"Set variables with {self.min_references} or fewer references were found:",
            Severity.ERROR,
            category="set-variable",
        )

    def run_validations(self):
        if self.min_references:
            self.log(f"Minimum references required: {self.min_references}")

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
