#!/usr/bin/env python3
##########################
# Comprehensive Variable and Event Target Validation Script (Multiprocessing Optimized)
# Validates flags (country/state/global) and event targets
# Checks for: cleared but not set, used but not set, and unused items
# Based on Kaiserreich Autotests by Pelmen, https://github.com/Pelmen323
# Optimized with multiprocessing for significantly faster execution
##########################
import glob
import os
import re
from multiprocessing import Pool
from typing import Dict, List, Optional, Tuple

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

# Module-level regex for per-file flag-syntax check (process_file_for_flag_syntax).
# Compiled once per worker process import instead of once per file scanned.
_FLAG_BLOCK_RE = re.compile(
    r"\bset_(country|global|state|character|mio|project|unit_leader)_flag\s*=\s*\{[^}]*\}",
)
_FLAG_DAYS_RE = re.compile(r"\bdays\s*=\s*[^\s}]+")
_FLAG_VALUE_RE = re.compile(r"\bvalue\s*=\s*[^\s}]+")
_FLAG_LONG_FORM_RE = re.compile(
    r"\bset_(country|global|state|character|mio|project|unit_leader)_flag\s*=\s*\{\s*flag\s*=\s*([^\s{}]+)\s*\}",
)


def _scan_flags_in_file(
    filename: str, lowercase: bool, flag_type: str
) -> Tuple[List[str], List[str], List[str]]:
    text = FileOpener.open_text_file(
        filename, lowercase=lowercase, strip_comments_flag=True
    )
    set_list: List[str] = []
    used_list: List[str] = []
    cleared_list: List[str] = []
    if not text:
        return set_list, used_list, cleared_list

    if f"set_{flag_type}_flag =" in text:
        set_list.extend(re.findall(r"set_" + flag_type + r"_flag = ([^ \t\n]+)", text))
        set_list.extend(
            re.findall(
                r"set_" + flag_type + r"_flag = \{.*?flag = ([^ \t\n\}]+).*?\}",
                text,
                flags=re.MULTILINE | re.DOTALL,
            )
        )

    if f"has_{flag_type}_flag =" in text or f"modify_{flag_type}_flag =" in text:
        used_list.extend(re.findall(r"has_" + flag_type + r"_flag = ([^ \t\n]+)", text))
        used_list.extend(
            re.findall(
                r"(?:has|modify)_"
                + flag_type
                + r"_flag = \{.*?flag = ([^ \t\n\}]+).*?\}",
                text,
                flags=re.MULTILINE | re.DOTALL,
            )
        )

    if f"clr_{flag_type}_flag =" in text:
        cleared_list.extend(
            re.findall(r"clr_" + flag_type + r"_flag = ([^ \t\n]+)", text)
        )

    return set_list, used_list, cleared_list


def process_file_for_all_flags(
    args: Tuple[str, bool, str, str],
) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
    filename, lowercase, flag_type, mod_path = args
    if should_skip_file(filename):
        return {}, {}, {}
    basename = os.path.basename(filename)
    namespace = f"variables.flags.{flag_type}.lc={int(lowercase)}"
    set_list, used_list, cleared_list = disk_cache.per_file_cached(
        mod_path,
        namespace,
        filename,
        lambda: _scan_flags_in_file(filename, lowercase, flag_type),
    )
    return (
        {m: basename for m in set_list},
        {m: basename for m in used_list},
        {m: basename for m in cleared_list},
    )


def process_file_for_flag_syntax(args: Tuple[str, str]) -> Tuple[List[str], List[str]]:
    """Combined pool worker: check both days-no-value and long-form flag calls in one file.

    Returns (days_no_value_issues, long_form_issues).
    """
    filename, mod_path = args

    if should_skip_file(filename):
        return ([], [])

    try:
        from pathlib import Path as _Path

        text = _Path(filename).read_text(encoding="utf-8-sig", errors="ignore")
    except Exception:
        return ([], [])

    cleaned = re.sub(r"#[^\n]*", "", text)
    rel = os.path.relpath(filename, mod_path)

    days_issues: List[str] = []
    long_form_issues: List[str] = []

    for m in _FLAG_BLOCK_RE.finditer(cleaned):
        block = m.group(0)
        if _FLAG_DAYS_RE.search(block) and not _FLAG_VALUE_RE.search(block):
            line = cleaned[: m.start()].count("\n") + 1
            days_issues.append(
                f"{rel}:{line} - {block.strip()} (missing value field; flag will default to 0 and fail shortform has_*_flag check)"
            )

    for m in _FLAG_LONG_FORM_RE.finditer(cleaned):
        line = cleaned[: m.start()].count("\n") + 1
        long_form_issues.append(
            f"{rel}:{line} - set_{m.group(1)}_flag = {{ flag = {m.group(2)} }} → use shorthand `set_{m.group(1)}_flag = {m.group(2)}`"
        )

    return (days_issues, long_form_issues)


def process_file_for_all_targets(
    args: Tuple[str, bool],
) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
    """Single-pass worker: extract set, used, and cleared event targets.

    Returns (set_paths, used_paths, cleared_paths) dicts mapping target → basename.
    Replaces three separate pool scans with one.
    """
    filename, lowercase = args

    if should_skip_file(filename):
        return ({}, {}, {})

    basename = os.path.basename(filename)
    text_file = FileOpener.open_text_file(
        filename, lowercase=lowercase, strip_comments_flag=True
    )

    set_paths: Dict[str, str] = {}
    used_paths: Dict[str, str] = {}
    cleared_paths: Dict[str, str] = {}

    # used — event_target: references and has_event_target
    if "tag_aliases" in filename:
        if "global_event_target =" in text_file:
            for m in re.findall(r'global_event_target = ([^ \n\t\#"]+)', text_file):
                used_paths[m] = basename
    else:
        if "event_target:" in text_file:
            for m in re.findall(r'event_target:([^ \n\t\#"]+)', text_file):
                used_paths[m] = basename
        if "has_event_target =" in text_file:
            for m in re.findall(r'has_event_target = ([^ \n\t"]+)', text_file):
                used_paths[m] = basename

    # set — save_global_event_target_as / save_event_target_as (not in tag_aliases)
    if "tag_aliases" not in filename:
        if "save_global_event_target_as =" in text_file:
            for m in re.findall(
                r'save_global_event_target_as = ([^ \n\t\#"]+)', text_file
            ):
                set_paths[m] = basename
        if "save_event_target_as =" in text_file:
            for m in re.findall(r'save_event_target_as = ([^ \n\t\#"]+)', text_file):
                set_paths[m] = basename

    # cleared — clear_global_event_target
    if "clear_global_event_target =" in text_file:
        for m in re.findall(r'clear_global_event_target = ([^ \n\t\#"]+)', text_file):
            cleared_paths[m] = basename

    return (set_paths, used_paths, cleared_paths)


def _map_with_optional_pool(func, args_list, workers, pool, chunksize=50):
    """Reuse the caller's pool when given; otherwise spin up a transient one.

    Keeps the helper usable as a standalone library function while letting
    BaseValidator subclasses pass `self._pool` to avoid spawning a second
    worker pool inside run_validations().
    """
    if pool is not None:
        return pool.map(func, args_list, chunksize=chunksize)
    with Pool(processes=workers) as p:
        return p.map(func, args_list, chunksize=chunksize)


class Variables:
    @classmethod
    def get_all_flags(
        cls,
        mod_path,
        lowercase=False,
        flag_type="country",
        staged_files=None,
        workers=None,
        files_to_scan=None,
        pool=None,
    ) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
        if flag_type not in ("country", "state", "global"):
            raise ValueError(f"Unsupported flag_type: {flag_type!r}")
        if files_to_scan is None:
            files_to_scan = _collect_txt_files(mod_path, staged_files)

        args_list = [(f, lowercase, flag_type, mod_path) for f in files_to_scan]
        results = _map_with_optional_pool(
            process_file_for_all_flags, args_list, workers, pool
        )
        return _merge_three_dicts(results)


class EventTargets:
    @classmethod
    def get_all_targets(
        cls,
        mod_path,
        lowercase=False,
        staged_files=None,
        workers=None,
        files_to_scan=None,
        pool=None,
    ) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
        if files_to_scan is None:
            files_to_scan = _collect_txt_files(mod_path, staged_files)

        args_list = [(f, lowercase) for f in files_to_scan]
        results = _map_with_optional_pool(
            process_file_for_all_targets, args_list, workers, pool
        )
        return _merge_three_dicts(results)


def _collect_txt_files(mod_path: str, staged_files) -> List[str]:
    if staged_files is not None:
        return [f for f in staged_files if f.endswith(".txt")]
    return list(glob.iglob(os.path.join(mod_path, "**", "*.txt"), recursive=True))


def _merge_three_dicts(
    results,
) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
    a: Dict[str, str] = {}
    b: Dict[str, str] = {}
    c: Dict[str, str] = {}
    for da, db, dc in results:
        a.update(da)
        b.update(db)
        c.update(dc)
    return a, b, c


class Validator(BaseValidator):
    TITLE = "VARIABLE AND EVENT TARGET VALIDATION"
    STAGED_EXTENSIONS = [".txt", ".yml"]

    def _report_with_locations(
        self, results: list, ok_msg: str, fail_msg: str, category: str = "variables"
    ):
        """Report a list of ``{"file", "line", "flag"|"target"}`` dicts.

        Delegates to ``BaseValidator._report`` with structured tuples so
        ``file`` and ``line`` flow into the JSON sidecar and become eligible
        for Checks API annotations.
        """
        tuples = []
        for result in results:
            identifier = result.get("flag") or result.get("target") or ""
            file_path = result.get("file", "")
            line_no = int(result.get("line", 0) or 0)
            tuples.append((identifier, file_path, line_no))
        self._report(
            tuples,
            ok_msg=ok_msg,
            fail_msg=fail_msg,
            severity=Severity.ERROR,
            category=category,
        )

    # HOI4 scope keywords that can appear in @SCOPE substitutions inside flag names
    _SCOPE_KEYWORDS = (
        "ROOT",
        "FROM",
        "PREV",
        "THIS",
        "OWNER",
        "CONTROLLER",
        "CAPITAL",
    )

    @classmethod
    def _build_dynamic_flag_matchers(cls, flags):
        """Build regex patterns from flags containing @SCOPE substitutions.

        A flag like ``libya_casablanca_accords_@ROOT_left`` is set at runtime as
        ``libya_casablanca_accords_MOR_left``, ``_ALG_left``, etc. Convert the
        ``@SCOPE`` segments to a 3-letter tag wildcard so literal flag checks
        can be matched back to their dynamic setter. Only recognized HOI4 scope
        keywords are treated as substitution points — an ``@`` followed by
        anything else is left literal.
        """
        scope_pat = re.compile(
            r"@(?:" + "|".join(cls._SCOPE_KEYWORDS) + r")(?![A-Za-z0-9])"
        )
        patterns = []
        # Country tags are upper-case letters/digits (``ISR``, ``CHI``).
        # During civil wars, runtime tags can also appear as
        # ``TAG_CW_0`` etc., so allow underscores and digits. This is
        # narrower than ``\w+`` (which matched lowercase and could
        # incorrectly capture unrelated literal flags).
        tag_wildcard = r"[A-Z][A-Z0-9_]{1,11}"
        for flag in flags:
            if "@" not in flag:
                continue
            if not scope_pat.search(flag):
                continue
            parts = scope_pat.split(flag)
            pattern_str = tag_wildcard.join(re.escape(p) for p in parts)
            patterns.append(re.compile(f"^{pattern_str}$"))
        return patterns

    def validate_cleared_flags(
        self,
        flag_type: str,
        false_positives: list,
        cleared_paths: Dict[str, str],
        set_paths: Dict[str, str],
    ):
        self._log_section(f"Checking cleared {flag_type} flags that are never set...")

        cleared_flags = DataCleaner.clear_false_positives_partial_match(
            list(cleared_paths.keys()), tuple(false_positives)
        )
        dynamic_set_patterns = self._build_dynamic_flag_matchers(list(set_paths.keys()))

        results = []
        for flag in cleared_flags:
            if flag in set_paths:
                continue
            if any(p.match(flag) for p in dynamic_set_patterns):
                continue
            basename = cleared_paths[flag]
            full_path = self.get_full_path(basename, f"clr_{flag_type}_flag = {flag}")
            if full_path:
                rel_path = os.path.relpath(full_path, self.mod_path)
                line_num = find_line_number(
                    full_path, f"clr_{flag_type}_flag = {flag}", lowercase=False
                )
                results.append({"flag": flag, "file": rel_path, "line": line_num})

        self._report_with_locations(
            results,
            f"✓ No issues found with cleared {flag_type} flags",
            f"Cleared {flag_type} flags that are never set were encountered. Flags with @ are skipped.",
        )

    def validate_missing_flags(
        self,
        flag_type: str,
        false_positives: list,
        used_paths: Dict[str, str],
        set_paths: Dict[str, str],
    ):
        self._log_section(f"Checking missing {flag_type} flags (used but not set)...")

        used_flags = DataCleaner.clear_false_positives_partial_match(
            list(used_paths.keys()), tuple(false_positives)
        )
        dynamic_set_patterns = self._build_dynamic_flag_matchers(list(set_paths.keys()))

        results = []
        for flag in used_flags:
            if flag in set_paths:
                continue
            if any(p.match(flag) for p in dynamic_set_patterns):
                continue
            basename = used_paths[flag]
            full_path = self.get_full_path(basename, f"has_{flag_type}_flag = {flag}")
            if full_path:
                rel_path = os.path.relpath(full_path, self.mod_path)
                line_num = find_line_number(
                    full_path, f"has_{flag_type}_flag = {flag}", lowercase=False
                )
                results.append({"flag": flag, "file": rel_path, "line": line_num})

        self._report_with_locations(
            results,
            f"✓ No issues found with missing {flag_type} flags",
            f"Missing {flag_type} flags were encountered - they are not set via 'set_{flag_type}_flag'. Flags with @ are skipped.",
        )

    def validate_unused_flags(
        self,
        flag_type: str,
        false_positives: list,
        set_paths: Dict[str, str],
        used_paths: Dict[str, str],
    ):
        self._log_section(f"Checking unused {flag_type} flags (set but not used)...")

        set_flags = DataCleaner.clear_false_positives_partial_match(
            list(set_paths.keys()), tuple(false_positives)
        )
        dynamic_used_patterns = self._build_dynamic_flag_matchers(
            list(used_paths.keys())
        )

        results = []
        for flag in set_flags:
            if flag in used_paths:
                continue
            if any(p.match(flag) for p in dynamic_used_patterns):
                continue
            basename = set_paths[flag]
            full_path = self.get_full_path(basename, f"set_{flag_type}_flag = {flag}")
            if full_path:
                rel_path = os.path.relpath(full_path, self.mod_path)
                line_num = find_line_number(
                    full_path, f"set_{flag_type}_flag = {flag}", lowercase=False
                )
                results.append({"flag": flag, "file": rel_path, "line": line_num})

        self._report_with_locations(
            results,
            f"✓ No issues found with unused {flag_type} flags",
            f"Unused {flag_type} flags were encountered - they are not used via 'has_{flag_type}_flag' at least once. Flags with @ are skipped.",
        )

    def validate_flag_syntax(self):
        """Combined check for two flag syntax issues in a single pool_map pass:

        1. ``set_*_flag = { flag = X days = N }`` omitting ``value`` — the flag
           defaults to 0 and fails the shortform ``has_*_flag = X`` check.
        2. ``set_*_flag = { flag = X }`` with only the flag arg — should use
           the shorthand ``set_*_flag = X``.

        Previously two separate serial rglob loops; now one pool_map pass.
        """
        self._log_section("Checking for set_*_flag syntax issues...")

        txt_files = self._collect_files(
            ["common/**/*.txt", "events/**/*.txt", "history/**/*.txt"]
        )
        args_list = [(f, self.mod_path) for f in txt_files]
        all_results = self._pool_map(
            process_file_for_flag_syntax, args_list, chunksize=30
        )

        days_issues: List[str] = []
        long_form_issues: List[str] = []
        for d, l in all_results:
            days_issues.extend(d)
            long_form_issues.extend(l)

        self._report(
            days_issues,
            "✓ No set_*_flag calls missing value when days is set",
            "set_*_flag with days but no value (flag defaults to 0, fails shortform has_*_flag check):",
        )
        self._report(
            long_form_issues,
            "✓ No set_*_flag long-form-only calls found",
            "Redundant long-form set_*_flag calls (use shorthand instead):",
        )

    def validate_cleared_event_targets(
        self,
        cleared_paths: Dict[str, str],
        set_paths: Dict[str, str],
    ):
        self._log_section("Checking cleared event targets that are not set...")

        results = []
        for target in cleared_paths:
            if target not in set_paths:
                basename = cleared_paths[target]
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

        self._report_with_locations(
            results,
            "✓ No issues found with cleared event targets",
            "Cleared event targets that are not set were encountered.",
        )

    def validate_missing_event_targets(
        self,
        used_paths: Dict[str, str],
        set_paths: Dict[str, str],
    ):
        self._log_section("Checking missing event targets (used but not set)...")

        FALSE_POSITIVES = ["."]
        results = []
        used_targets = DataCleaner.clear_false_positives_partial_match(
            list(used_paths.keys()), tuple(FALSE_POSITIVES)
        )

        for target in used_targets:
            if target not in set_paths:
                basename = used_paths[target]
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

        self._report_with_locations(
            results,
            "✓ No issues found with missing event targets",
            "Used event targets that are not set were encountered.",
        )

    def validate_unused_event_targets(
        self,
        set_paths: Dict[str, str],
        used_paths: Dict[str, str],
    ):
        self._log_section("Checking unused event targets (set but not used)...")

        FALSE_POSITIVES = ["wca_usa_floyd_olson", "wca_usa_al_smith", "target_value"]
        results = []
        potential_results = []
        set_targets = DataCleaner.clear_false_positives_partial_match(
            list(set_paths.keys()), tuple(FALSE_POSITIVES)
        )

        for target in set_targets:
            if target not in used_paths:
                potential_results.append(target)

        targets_used_in_loc = []
        if self.staged_files:
            yml_files_to_scan = [f for f in self.staged_files if f.endswith(".yml")]
        else:
            yml_files_to_scan = glob.iglob(
                os.path.join(self.mod_path, "**", "*.yml"), recursive=True
            )

        for filename in yml_files_to_scan:
            if should_skip_file(filename):
                continue
            text_file = FileOpener.open_text_file(filename, strip_comments_flag=True)

            if ".get" in text_file:
                not_encountered_targets = [
                    i for i in potential_results if i not in targets_used_in_loc
                ]
                for target in not_encountered_targets:
                    target_lower = target.lower()
                    if (
                        f"[{target_lower}.getname" in text_file
                        or f"[{target_lower}.getadjective" in text_file
                        or f"[event_target:{target_lower}.getname" in text_file
                        or f"[event_target:{target_lower}.getadjective" in text_file
                    ):
                        targets_used_in_loc.append(target)

        for target in potential_results:
            if target not in targets_used_in_loc:
                basename = set_paths[target]
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

        self._report_with_locations(
            results,
            "✓ No issues found with unused event targets",
            "Unused event targets were encountered.",
        )

    def run_validations(self):
        if self.staged_only:
            # Variable validation cross-references flags across all files
            # (used in A, set in B). Scanning only staged files produces
            # false positives. Skip in staged mode; CI handles full validation.
            self.log(
                "Variable validation requires cross-file comparison — skipping in staged mode",
                "warning",
            )
            return

        # Collect the file list once and share across all flag-type and
        # event-target scans — avoids one glob.iglob per flag_type (×3) plus
        # one more for event targets, for a total of 4 redundant scans.
        self.log("Collecting all .txt files (one scan for all validators)...")
        all_txt_files = list(
            glob.iglob(os.path.join(self.mod_path, "**", "*.txt"), recursive=True)
        )
        self.log(f"  Found {len(all_txt_files)} .txt files")

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
            # One scan per flag_type instead of six separate pool scans.
            set_paths, used_paths, cleared_paths = Variables.get_all_flags(
                mod_path=self.mod_path,
                lowercase=False,
                flag_type=flag_type,
                staged_files=self.staged_files,
                workers=self.workers,
                files_to_scan=all_txt_files,
                pool=self._pool,
            )
            self.validate_cleared_flags(flag_type, fp_cleared, cleared_paths, set_paths)
            self.validate_missing_flags(flag_type, fp_missing, used_paths, set_paths)
            self.validate_unused_flags(flag_type, fp_unused, set_paths, used_paths)

        # One scan for all three event-target checks instead of six pool scans.
        et_set, et_used, et_cleared = EventTargets.get_all_targets(
            mod_path=self.mod_path,
            lowercase=False,
            staged_files=self.staged_files,
            workers=self.workers,
            files_to_scan=all_txt_files,
            pool=self._pool,
        )
        self.validate_cleared_event_targets(et_cleared, et_set)
        self.validate_missing_event_targets(et_used, et_set)
        self.validate_unused_event_targets(et_set, et_used)
        self.validate_flag_syntax()


if __name__ == "__main__":
    run_validator_main(
        Validator, "Validate variables and event targets in Millennium Dawn mod"
    )
