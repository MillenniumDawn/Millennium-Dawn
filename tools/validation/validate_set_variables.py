#!/usr/bin/env python3
"""Validate that every set_variable target is referenced somewhere else.

Two passes: extract all `set_variable = X` targets, then scan the whole mod
for `\\bX\\b` references and report vars whose net refs (refs minus sets) is
zero. Both passes are multiprocessed and disk-cached via `disk_cache`.
"""
import glob
import hashlib
import os
import re
from functools import partial
from multiprocessing import Pool
from typing import Dict, List, Tuple

import disk_cache
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

# 25 chars on each side covers `set_variable = {` plus a short var name.
SET_CONTEXT_WINDOW = 25

_SET_SHORT_RE = re.compile(r"set_variable = ([^ \t\n\}]+)")
_SET_LONG_RE = re.compile(
    r"set_variable = \{[^}]*?([a-z0-9_@\.\^\[\]]+)\s*=",
    flags=re.MULTILINE | re.DOTALL,
)
_SET_LONG_RESERVED = frozenset(("value", "days", "months", "years", "hours"))


def _scan_set_variables(filename: str, lowercase: bool) -> Tuple[List[str], str]:
    text = FileOpener.open_text_file(
        filename, lowercase=lowercase, strip_comments_flag=True
    )
    variables: List[str] = []
    if "set_variable =" in text:
        variables.extend(_SET_SHORT_RE.findall(text))
        variables.extend(
            m for m in _SET_LONG_RE.findall(text) if m not in _SET_LONG_RESERVED
        )
    return variables, os.path.basename(filename)


def process_file_for_set_variables(
    filename: str, lowercase: bool, mod_path: str
) -> Tuple[List[str], Dict[str, str]]:
    if should_skip_file(filename):
        return [], {}
    namespace = f"set_variables.scan.lc={int(lowercase)}"
    variables, basename = disk_cache.per_file_cached(
        mod_path,
        namespace,
        filename,
        lambda: _scan_set_variables(filename, lowercase),
    )
    return variables, {v: basename for v in variables}


def _count_vars_in_file(
    filename: str, tracked_vars: frozenset, lowercase: bool
) -> Dict[str, int]:
    text = FileOpener.open_text_file(
        filename, lowercase=lowercase, strip_comments_flag=True
    )
    if not text or not tracked_vars:
        return {}
    pattern = re.compile(r"\b(" + "|".join(re.escape(v) for v in tracked_vars) + r")\b")
    ref_counts: Dict[str, int] = {}
    set_counts: Dict[str, int] = {}
    for m in pattern.finditer(text):
        var = m.group(1)
        start = max(0, m.start() - SET_CONTEXT_WINDOW)
        end = min(len(text), m.end() + SET_CONTEXT_WINDOW)
        if "set_variable" in text[start:end]:
            set_counts[var] = set_counts.get(var, 0) + 1
        else:
            ref_counts[var] = ref_counts.get(var, 0) + 1
    return {
        v: ref_counts[v] - set_counts.get(v, 0)
        for v in ref_counts
        if ref_counts[v] - set_counts.get(v, 0) > 0
    }


def count_all_variables_in_file(
    args: Tuple[str, frozenset, bool, str],
) -> Dict[str, int]:
    # Cache namespace includes a hash of tracked_vars: the alternation regex
    # output is only reusable when the input set is unchanged. Typical PRs
    # don't add/remove set_variable definitions, so the hash is stable.
    filename, tracked_vars, lowercase, mod_path = args
    if should_skip_file(filename) or not tracked_vars:
        return {}
    tracked_hash = hashlib.sha1(
        "|".join(sorted(tracked_vars)).encode("utf-8")
    ).hexdigest()[:16]
    namespace = f"set_variables.counts.lc={int(lowercase)}.{tracked_hash}"
    return disk_cache.per_file_cached(
        mod_path,
        namespace,
        filename,
        lambda: _count_vars_in_file(filename, tracked_vars, lowercase),
    )


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

        process_func = partial(
            process_file_for_set_variables, lowercase=lowercase, mod_path=mod_path
        )

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
        args_list = [(f, tracked_vars, True, self.mod_path) for f in files_to_scan]

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
