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

# Look-behind window for deciding whether a matched variable is the left-hand
# target of a `set_variable` assignment. `set_variable = {` is 17 chars; 40
# gives margin while staying tight enough never to reach a prior statement.
SET_LOOKBACK_WINDOW = 40

_SET_SHORT_RE = re.compile(r"set_variable = ([^ \t\n\}]+)")
# Char class includes A-Z so tag-prefixed targets (e.g. GER_event_counter_1_wot,
# ITA_ageing_population_var) are captured whole instead of having their uppercase
# prefix silently dropped — which previously made every such name fail to match
# its own reads and get reported as unused.
_SET_LONG_RE = re.compile(
    r"set_variable = \{[^}]*?([A-Za-z0-9_@\.\^\[\]]+)\s*=",
    flags=re.MULTILINE | re.DOTALL,
)
_SET_LONG_RESERVED = frozenset(("value", "days", "months", "years", "hours"))

# A matched variable is a set-target when `set_variable = {?` sits immediately
# before it (only whitespace, an optional brace, and an optional scope chain
# between). Anchored at the end of the look-behind slice so a `set_variable` on
# a *following* line can never be mistaken for the current match's context, and
# so a value on the RHS of an assignment (`set_variable = { x = y }` → `y`) is
# correctly counted as a read. The `(?:scope\.)*` tail lets the scope-stripped
# target (see _strip_scope_prefix) still be recognised inside a scoped write
# like `set_variable = { THIS.eurosceptic = ... }`.
_SET_TARGET_PREFIX_RE = re.compile(r"set_variable\s*=\s*\{?\s*(?:[a-z_][a-z0-9_]*\.)*$")


def _strip_scope_prefix(name: str) -> str:
    """Reduce a scope-qualified set_variable target to its bare variable name.

    `set_variable = { PREV.foo = ... }` stores `foo` on the PREV scope, but the
    same variable is read elsewhere as `THIS.foo`, `var:foo`, or bare `foo`.
    Matching the scope-prefixed capture against those reads fails and the var is
    wrongly reported unused, so track the bare name. `global.` vars are a real
    namespace (always read as `global.X`) and are left intact.
    """
    if "." not in name or name.startswith("global."):
        return name
    return name.rsplit(".", 1)[1]


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
        variables = [_strip_scope_prefix(v) for v in variables]
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
    # tracked_vars keep their original case from the case-sensitive scan, but
    # `text` is lowercased here, so match case-insensitively and map each hit
    # back to its canonical name. Without IGNORECASE a tag-prefixed GER_/ITA_
    # name would never match the lowercased reads.
    lc_to_orig = {v.lower(): v for v in tracked_vars}
    pattern = re.compile(
        r"\b(" + "|".join(re.escape(v) for v in tracked_vars) + r")\b",
        flags=re.IGNORECASE,
    )
    ref_counts: Dict[str, int] = {}
    for m in pattern.finditer(text):
        before = text[max(0, m.start() - SET_LOOKBACK_WINDOW) : m.start()]
        if _SET_TARGET_PREFIX_RE.search(before):
            # Left-hand target of a set_variable assignment: a definition, not a use.
            continue
        var = lc_to_orig.get(m.group(1).lower())
        if var is None:
            continue
        ref_counts[var] = ref_counts.get(var, 0) + 1
    return {v: c for v, c in ref_counts.items() if c > 0}


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
