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
# `\w` (Unicode) keeps tag-prefixed targets whole (GER_event_counter_1_wot,
# ITA_ageing_population_var) AND non-ASCII names like additional_income_GER_Ökosteuer.
# An ASCII-only class split on the Ö and captured only the `kosteuer` tail, which
# never matched its own reads and so was wrongly reported as unused. `@.^[]` stay
# for indexed/array and scoped targets.
_SET_LONG_RE = re.compile(
    r"set_variable = \{[^}]*?([\w@\.\^\[\]]+)\s*=",
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


def _scan_set_variables(text: str) -> List[str]:
    variables: List[str] = []
    if "set_variable =" in text:
        variables.extend(_SET_SHORT_RE.findall(text))
        variables.extend(
            m for m in _SET_LONG_RE.findall(text) if m not in _SET_LONG_RESERVED
        )
        variables = [_strip_scope_prefix(v) for v in variables]
    return variables


def process_file_for_set_variables(
    filename: str, lowercase: bool, mod_path: str
) -> Tuple[List[str], Dict[str, str]]:
    if should_skip_file(filename):
        return [], {}
    text = FileOpener.open_text_file(
        filename, lowercase=lowercase, strip_comments_flag=True
    )
    namespace = f"set_variables.scan.v2.lc={int(lowercase)}"
    variables = disk_cache.per_file_cached_by_content(
        mod_path, namespace, filename, text, lambda: _scan_set_variables(text)
    )
    basename = os.path.basename(filename)
    return variables, {v: basename for v in variables}


# Maximal identifier run, including scope-chain dots (e.g. "this.foo",
# "global.bar.GetName"). A maximal word run is exactly a `\bWORD\b` span, so
# tokenising and looking each run up in a lowercased name set reproduces the
# old `\b(v1|v2|...)\b` IGNORECASE alternation without compiling a ~3,900-branch
# regex per file. `\w` (Unicode, like the engine's `\b`) is used rather than an
# ASCII class so boundaries fall exactly where the old alternation put them:
# a non-ASCII letter such as the Ö in `additional_income_GER_Ökosteuer` is a
# word char and must not split the name (an ASCII class would, spuriously
# matching the `kosteuer` tail that pass 1 also mis-captures).
_RUN_RE = re.compile(r"\w+(?:\.\w+)*")
_WORD_RE = re.compile(r"\w+")

# Dynamic variable references: `prefix_[interpolated]_suffix`, e.g.
# `global.EU_draft_party_[MEP_sup_n]_variable`. The `[...]` index is resolved at
# runtime, so a static tokenizer never sees the concrete sibling name and the
# literally-set `..._0_variable`, `..._7_variable`, … all look unused. We collect
# these refs, turn each into an anchored regex (every `[...]` → `\w+`), and
# suppress any tracked var a pattern matches. It is a widespread idiom (EU
# parliament, espionage, investments, recognition, voting), so handling it once
# clears a whole class of false positives rather than one variable family.
_DYNAMIC_REF_RE = re.compile(r"[\w.:]*\[[^\]\s]+\][\w.]*")
# Scope prefixes a read can carry that a set target is stored without (mirrors
# _strip_scope_prefix). `global.` is its own namespace and is left intact.
_SCOPE_PREFIXES = (
    "this.",
    "root.",
    "prev.",
    "from.",
    "owner.",
    "controller.",
    "capital.",
    "var:",
)


def _dynamic_ref_pattern(ref: str):
    """Anchored regex for a dynamic ref, or None when nothing literal anchors it.

    `ref` is already lowercased (pass 2 reads files lowercased). A leading scope
    prefix is stripped so a scoped read (`this.foo_[i]`) matches the bare name the
    var is tracked under. A ref with no literal text (a bare `[x]`, or loc noise
    like `[GetName]`) would match every tracked var, so it is dropped.
    """
    if not ref.startswith("global."):
        for prefix in _SCOPE_PREFIXES:
            if ref.startswith(prefix):
                ref = ref[len(prefix) :]
                break
    literals = re.split(r"\[[^\]]*\]", ref)
    if not any(literals):
        return None
    return "^" + r"\w+".join(re.escape(part) for part in literals) + "$"


# Pass-2 per-worker state, populated once by _pass2_init via the Pool
# initializer instead of being re-pickled in every task's args (the old args
# tuple shipped the full ~3,900-element tracked set to each of ~8,800 files).
_W_MOD_PATH: str = ""
_W_BARE: Dict[str, str] = {}
_W_DOTTED: Dict[str, str] = {}
_W_NAMESPACE: str = ""


def _pass2_init(mod_path, bare_map, dotted_map, namespace):
    global _W_MOD_PATH, _W_BARE, _W_DOTTED, _W_NAMESPACE
    _W_MOD_PATH = mod_path
    _W_BARE = bare_map
    _W_DOTTED = dotted_map
    _W_NAMESPACE = namespace


def _is_definition(text: str, start: int) -> bool:
    # A match is the left-hand target of a set_variable assignment (a
    # definition, not a use) when `set_variable = {? (scope.)*` sits directly
    # before it. Identical to the old per-match look-behind.
    before = text[max(0, start - SET_LOOKBACK_WINDOW) : start]
    return _SET_TARGET_PREFIX_RE.search(before) is not None


def _count_refs_in_text(text: str) -> Tuple[Dict[str, int], set]:
    bare = _W_BARE
    dotted = _W_DOTTED
    counts: Dict[str, int] = {}
    dynamic_patterns: set = set()
    if "[" in text:
        for dm in _DYNAMIC_REF_RE.finditer(text):
            pattern = _dynamic_ref_pattern(dm.group())
            if pattern is not None:
                dynamic_patterns.add(pattern)
    for m in _RUN_RE.finditer(text):
        run = m.group()
        base = m.start()
        if "." not in run:
            orig = bare.get(run)
            if orig is not None and not _is_definition(text, base):
                counts[orig] = counts.get(orig, 0) + 1
            continue
        # Dotted run: walk segments left-to-right, mirroring the old
        # alternation's non-overlapping match. A tracked global.X (the only
        # kind of dotted target — scope prefixes are stripped to bare names)
        # is matched as a segment-aligned prefix, so it still hits inside a
        # longer chain like global.X.GetFlag, and is consumed as a unit so its
        # tail segment is not also counted as a bare X. Any other segment
        # (THIS.foo, root.bar) is matched as a bare name, exactly as the old
        # `\bX\b` did for the inner token of a scope chain.
        segs = list(_WORD_RE.finditer(run))
        j = 0
        n = len(segs)
        while j < n:
            sm = segs[j]
            seg = sm.group()
            if seg == "global" and j + 1 < n:
                cand = "global." + segs[j + 1].group()
                orig = dotted.get(cand)
                if orig is not None:
                    if not _is_definition(text, base + sm.start()):
                        counts[orig] = counts.get(orig, 0) + 1
                    j += 2
                    continue
            orig = bare.get(seg)
            if orig is not None and not _is_definition(text, base + sm.start()):
                counts[orig] = counts.get(orig, 0) + 1
            j += 1
    return counts, dynamic_patterns


def count_all_variables_in_file(filename: str) -> Tuple[Dict[str, int], set]:
    # Per-worker globals (set by _pass2_init) hold the tracked maps and cache
    # namespace, so each task carries only the filename string.
    if should_skip_file(filename):
        return {}, set()
    text = FileOpener.open_text_file(filename, lowercase=True, strip_comments_flag=True)
    if not text:
        return {}, set()
    return disk_cache.per_file_cached_by_content(
        _W_MOD_PATH, _W_NAMESPACE, filename, text, lambda: _count_refs_in_text(text)
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

        if pool is not None:
            # Reuse the caller's pool (e.g. the shared self._pool); it owns the
            # lifecycle, so don't close it here.
            results = pool.map(process_func, files_to_scan, chunksize=50)
        elif workers == 1:
            results = [process_func(f) for f in files_to_scan]
        else:
            with Pool(processes=workers) as p:
                results = p.map(process_func, files_to_scan, chunksize=50)

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
            pool=self._pool,
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

        # Scan every file once with a single tokenizer pass — no per-file regex
        # build. .yml is restricted to English; other languages are Paratranz
        # mirrors that only echo the same [?var] references, adding no signal.
        if self.staged_files:
            files_to_scan = [
                f
                for f in self.staged_files
                if f.endswith(".txt")
                or (
                    f.endswith(".yml")
                    and "localisation/english/" in f.replace("\\", "/")
                )
            ]
        else:
            txt_files = list(
                glob.iglob(os.path.join(self.mod_path, "**", "*.txt"), recursive=True)
            )
            yml_files = list(
                glob.iglob(
                    os.path.join(
                        self.mod_path, "localisation", "english", "**", "*.yml"
                    ),
                    recursive=True,
                )
            )
            files_to_scan = txt_files + yml_files

        # Partition into bare names and global.-dotted names (lowercased -> orig
        # case). A scoped read like THIS.foo stores/reads bare `foo`; a global.X
        # is its own namespace and is matched whole — see _count_refs_in_text.
        bare_map: Dict[str, str] = {}
        dotted_map: Dict[str, str] = {}
        for var in cleaned_vars:
            if "." in var:
                dotted_map[var.lower()] = var
            else:
                bare_map[var.lower()] = var
        tracked_hash = hashlib.sha1(
            "|".join(sorted(cleaned_vars)).encode("utf-8")
        ).hexdigest()[:16]
        namespace = f"set_variables.counts.lc=2.{tracked_hash}"

        var_ref_counts = {var: 0 for var in cleaned_vars}
        dynamic_patterns: set = set()
        if files_to_scan and (bare_map or dotted_map):
            if self.workers == 1:
                _pass2_init(self.mod_path, bare_map, dotted_map, namespace)
                all_file_counts = [
                    count_all_variables_in_file(f) for f in files_to_scan
                ]
            else:
                with Pool(
                    processes=self.workers,
                    initializer=_pass2_init,
                    initargs=(self.mod_path, bare_map, dotted_map, namespace),
                ) as p:
                    all_file_counts = p.map(
                        count_all_variables_in_file, files_to_scan, chunksize=20
                    )
            for file_counts, file_patterns in all_file_counts:
                for var, count in file_counts.items():
                    var_ref_counts[var] = var_ref_counts.get(var, 0) + count
                dynamic_patterns.update(file_patterns)

        # A var read only through a runtime-built name (`foo_[idx]_bar`) has zero
        # literal refs; suppress it if any collected dynamic pattern matches.
        compiled_dynamic = [re.compile(p) for p in dynamic_patterns]

        for var, ref_count in var_ref_counts.items():
            if ref_count <= self.min_references:
                if any(rx.match(var.lower()) for rx in compiled_dynamic):
                    continue
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
