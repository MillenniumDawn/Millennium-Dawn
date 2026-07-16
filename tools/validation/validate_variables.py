#!/usr/bin/env python3
# Variable and event target validation: checks flags (country/state/global) and
# event targets for cleared-but-not-set, used-but-not-set, and unused items.
# Based on Kaiserreich Autotests by Pelmen (https://github.com/Pelmen323).
import glob
import os
import re
import sys
from multiprocessing import Pool
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import disk_cache

# strip_comments is quote-aware: a '#' inside a quoted log string must survive,
# or the orphaned quote desyncs extract_block_from_text's in-string tracking
# and container spans are silently lost.
from shared_utils import extract_block_from_text, strip_comments
from validator_common import (
    BaseValidator,
    DataCleaner,
    FileOpener,
    Severity,
    find_line_number,
    run_validator_main,
    should_skip_file,
)

# Compiled at module load (once per worker process) instead of once per file scanned.
_FLAG_BLOCK_RE = re.compile(
    r"\bset_(country|global|state|character|mio|project|unit_leader)_flag\s*=\s*\{[^}]*\}",
)
_FLAG_DAYS_RE = re.compile(r"\bdays\s*=\s*[^\s}]+")
_FLAG_VALUE_RE = re.compile(r"\bvalue\s*=\s*[^\s}]+")
_FLAG_LONG_FORM_RE = re.compile(
    r"\bset_(country|global|state|character|mio|project|unit_leader)_flag\s*=\s*\{\s*flag\s*=\s*([^\s{}]+)\s*\}",
)

# Math expression operators with a numeric literal that has >5 decimal places.
# HOI4 silently truncates at 5, so the value computed at runtime is wrong.
_MATH_PRECISION_RE = re.compile(
    r"\b(add|subtract|multiply|divide|value)\s*=\s*[-+]?\d*\.\d{6,}"
)


def _scan_flags_in_file(
    text: str, flag_type: str
) -> Tuple[List[str], List[str], List[str]]:
    set_list: List[str] = []
    used_list: List[str] = []
    cleared_list: List[str] = []

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
    text = FileOpener.open_text_file(
        filename, lowercase=lowercase, strip_comments_flag=True
    )
    if not text:
        return {}, {}, {}
    basename = os.path.basename(filename)
    namespace = f"variables.flags.{flag_type}.lc={int(lowercase)}"
    set_list, used_list, cleared_list = disk_cache.per_file_cached_by_content(
        mod_path,
        namespace,
        filename,
        text,
        lambda: _scan_flags_in_file(text, flag_type),
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

        text = _Path(filename).read_text(encoding="utf-8-sig", errors="replace")
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


def process_file_for_math_precision(args: Tuple[str, str]) -> List[str]:
    """Pool worker: scan one file for math expression literals with >5 decimal places.

    Returns a list of 'rel:line - description' strings.
    """
    filename, mod_path = args
    if should_skip_file(filename):
        return []
    try:
        from pathlib import Path as _Path

        text = _Path(filename).read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return []

    cleaned = re.sub(r"#[^\n]*", "", text)
    rel = os.path.relpath(filename, mod_path)

    issues: List[str] = []
    for m in _MATH_PRECISION_RE.finditer(cleaned):
        line = cleaned[: m.start()].count("\n") + 1
        issues.append(
            f"{rel}:{line} - math expression literal with >5 decimal places"
            f" (engine truncates silently): {m.group(0).strip()}"
        )
    return issues


# Money-system input variables and the scripted effect that consumes each.
# A set_temp_variable of one of these with no consumer call afterwards in the
# same effect block is a dead setter — the money never moves (Sweden_foci.57).
_MONEY_EFFECT_PAIRS = {
    "treasury_change": "modify_treasury_effect",
    "debt_change": "modify_debt_effect",
    "int_investment_change": "modify_international_investment_effect",
}
_MONEY_SETTER_RE = re.compile(
    r"set_temp_variable\s*=\s*\{\s*(" + "|".join(_MONEY_EFFECT_PAIRS) + r")\s*="
)
# Blocks that delimit one effect execution. hidden_effect is NOT a boundary —
# it runs in the same execution as its parent, only hidden from the tooltip.
# effect_tooltip is deliberately its own container: a setter previewed there
# must also be consumed there or the tooltip renders nothing, and a consumer
# that only appears inside a tooltip never runs.
_EFFECT_CONTAINER_RE = re.compile(
    r"\b(?:completion_reward|select_effect|bypass_effect|option|immediate|"
    r"complete_effect|remove_effect|timeout_effect|cancel_effect|"
    r"effect_tooltip|effect)\s*=\s*\{"
)
_SCRIPTED_EFFECT_DEF_RE = re.compile(r"^([A-Za-z0-9_]+)\s*=\s*\{", re.MULTILINE)
# Value-producing writers only — add_to/multiply etc. read the existing value.
_WRITE_BEFORE_RE = re.compile(
    r"(?:set_temp_variable|set_variable)\s*=\s*\{\s*$"
    r"|set_temp_variable_to_random\s*=\s*\{\s*var\s*=\s*$"
)
_MONEY_WRITE_RES = {
    var: re.compile(
        r"\b(?:set_temp_variable|set_variable)\s*=\s*\{\s*" + var + r"\s*="
        r"|\bset_temp_variable_to_random\s*=\s*\{\s*var\s*=\s*" + var + r"\b"
    )
    for var in _MONEY_EFFECT_PAIRS
}


def build_money_consumer_map(effect_files: List[str]) -> Dict[str, frozenset]:
    """Map each money input variable to the scripted effects that consume it.

    An effect consumes a variable when the variable's first appearance in its
    body is a read (add_to_variable r-value, multiply, check, ...) rather than
    a set_temp_variable/set_variable write — a wrapper that writes first
    overwrites the caller's value and cannot consume it. Closed transitively
    so wrappers of wrappers (GRE_pay_or_defer -> modify_debt_effect) count.
    """
    bodies: Dict[str, str] = {}
    for fp in effect_files:
        try:
            with open(fp, "r", encoding="utf-8-sig", errors="replace") as fh:
                text = strip_comments(fh.read())
        except Exception:
            continue
        for m in _SCRIPTED_EFFECT_DEF_RE.finditer(text):
            body, _ = extract_block_from_text(text, m.start())
            if body:
                bodies[m.group(1)] = body

    def first_positions(body: str, var: str):
        first_read = first_write = None
        for om in re.finditer(r"\b" + var + r"\b", body):
            if _WRITE_BEFORE_RE.search(body, 0, om.start()):
                if first_write is None:
                    first_write = om.start()
            elif first_read is None:
                first_read = om.start()
            if first_read is not None and first_write is not None:
                break
        return first_read, first_write

    consumers = {var: {base} for var, base in _MONEY_EFFECT_PAIRS.items()}
    for var in _MONEY_EFFECT_PAIRS:
        for name, body in bodies.items():
            first_read, first_write = first_positions(body, var)
            if first_read is not None and (
                first_write is None or first_read < first_write
            ):
                consumers[var].add(name)

    changed = True
    while changed:
        changed = False
        for var, known in consumers.items():
            call_re = re.compile(
                r"\b(?:"
                + "|".join(re.escape(n) for n in sorted(known))
                + r")\s*=\s*yes\b"
            )
            for name, body in bodies.items():
                if name in known:
                    continue
                call = call_re.search(body)
                if not call:
                    continue
                _, first_write = first_positions(body, var)
                if first_write is None or call.start() < first_write:
                    known.add(name)
                    changed = True
    return {var: frozenset(names) for var, names in consumers.items()}


def _has_sequential_rewrite(
    cleaned: str, start: int, end: int, var: str, write_re: re.Pattern
) -> bool:
    """Whether the setter's variable is re-set in [start, end) as a clobber.

    Depth heuristic: only a re-write at the setter's own brace depth counts —
    branch-gated writes (if/else arms) sit in nested blocks and never clobber.
    A same-depth re-write that reads the variable in its value expression
    (``value = X multiply = -1``, events/raids.txt) folds the old value
    forward and is not a clobber either.
    """
    rewrites = [w.start() for w in write_re.finditer(cleaned, start, end)]
    if not rewrites:
        return False
    var_re = re.compile(r"\b" + var + r"\b")
    ri = 0
    depth = 1  # start sits inside the setter's own braces
    in_str = False
    for i in range(start, end):
        if ri < len(rewrites) and rewrites[ri] == i:
            if depth == 0 and not in_str:
                # First same-depth re-write decides: the sole var occurrence
                # in its block is the l-value; a second one is a self-read.
                body, _ = extract_block_from_text(cleaned, i)
                return len(var_re.findall(body)) <= 1
            ri += 1
            if ri == len(rewrites):
                return False
        c = cleaned[i]
        if c == '"' and cleaned[i - 1] != "\\":
            in_str = not in_str
        elif not in_str:
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth < 0:
                    return False
    return False


def process_file_for_orphan_money(
    args: Tuple[str, str, Dict[str, frozenset]],
) -> List[Tuple[str, str, int]]:
    """Pool worker: flag money-variable setters that are dead in their block —
    never consumed, or overwritten at the same depth before the consumer runs.

    Returns (message, rel_path, line) tuples. Setters outside any known effect
    container (loose scripted-effect bodies that produce the value for their
    caller) are skipped.
    """
    filename, mod_path, consumer_map = args
    if should_skip_file(filename):
        return []
    try:
        from pathlib import Path as _Path

        text = _Path(filename).read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return []

    # Quote-aware strip — the naive regex strip broke brace tracking in every
    # file with a '#' inside a log string.
    cleaned = strip_comments(text)
    setters = list(_MONEY_SETTER_RE.finditer(cleaned))
    if not setters:
        return []

    spans = []
    for m in _EFFECT_CONTAINER_RE.finditer(cleaned):
        brace = m.end() - 1  # the container regex ends at the opening brace
        body, end = extract_block_from_text(cleaned, brace)
        if body:
            is_tooltip = cleaned.startswith("effect_tooltip", m.start())
            spans.append((brace + 1, end, is_tooltip))
    tooltip_spans = [(s, e) for s, e, is_tt in spans if is_tt]

    consumer_res = {
        var: re.compile(
            r"\b(?:" + "|".join(re.escape(n) for n in sorted(names)) + r")\s*=\s*yes\b"
        )
        for var, names in consumer_map.items()
    }
    rel = os.path.relpath(filename, mod_path)
    issues: List[Tuple[str, str, int]] = []
    for m in setters:
        var = m.group(1)
        holder = None
        for start, end, is_tt in spans:
            if start <= m.start() < end and (holder is None or start > holder[0]):
                holder = (start, end, is_tt)
        if holder is None:
            continue
        if holder[2]:
            # Setter previewed in a tooltip: any consumer within it renders.
            hits = list(consumer_res[var].finditer(cleaned, m.end(), holder[1]))
        else:
            # Runtime setter: consumers that only exist inside a nested
            # effect_tooltip are previews and never execute.
            hits = [
                cm
                for cm in consumer_res[var].finditer(cleaned, m.end(), holder[1])
                if not any(ts <= cm.start() < te for ts, te in tooltip_spans)
            ]
        if hits and not _has_sequential_rewrite(
            cleaned, m.end(), hits[0].start(), var, _MONEY_WRITE_RES[var]
        ):
            continue
        line = cleaned[: m.start()].count("\n") + 1
        if hits:
            issues.append(
                (
                    f"set_temp_variable {var} is overwritten before"
                    f" {_MONEY_EFFECT_PAIRS[var]} (or wrapper) runs — a later"
                    f" write to {var} clobbers this value, so this setter is dead",
                    rel,
                    line,
                )
            )
        else:
            issues.append(
                (
                    f"set_temp_variable {var} is never consumed — no"
                    f" {_MONEY_EFFECT_PAIRS[var]} (or wrapper) follows in the"
                    f" same effect block, so the money never moves",
                    rel,
                    line,
                )
            )
    return issues


def _scan_targets_in_text(
    text_file: str, filename: str
) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
    """Extract set/used/cleared event targets from one file's text.

    `filename` only drives stable per-file branches (tag_aliases path check,
    basename labelling), so the result is deterministic for a (path, content)
    pair and safe to content-cache.
    """
    basename = os.path.basename(filename)
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


def process_file_for_all_targets(
    args: Tuple[str, bool, str],
) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
    """Single-pass worker: extract set, used, and cleared event targets.

    Returns (set_paths, used_paths, cleared_paths) dicts mapping target → basename.
    Replaces three separate pool scans with one.
    """
    filename, lowercase, mod_path = args

    if should_skip_file(filename):
        return ({}, {}, {})

    text_file = FileOpener.open_text_file(
        filename, lowercase=lowercase, strip_comments_flag=True
    )
    if not text_file:
        return ({}, {}, {})

    return disk_cache.per_file_cached_by_content(
        mod_path,
        f"variables.targets.lc={int(lowercase)}",
        filename,
        text_file,
        lambda: _scan_targets_in_text(text_file, filename),
    )


def _scan_targets_in_loc(args: Tuple[str, Tuple[str, ...]]) -> set:
    """Return which of `potential_targets` appear as [target.GetName]-style loc
    references in one yml file. Pooled; the union across files is order-
    independent, matching the old single-process accumulator exactly."""
    filename, potential_targets = args
    if should_skip_file(filename):
        return set()
    text_file = FileOpener.open_text_file(
        filename, lowercase=True, strip_comments_flag=True
    )
    found: set = set()
    if ".get" in text_file:
        for target in potential_targets:
            tl = target.lower()
            if (
                f"[{tl}.getname" in text_file
                or f"[{tl}.getadjective" in text_file
                or f"[event_target:{tl}.getname" in text_file
                or f"[event_target:{tl}.getadjective" in text_file
            ):
                found.add(target)
    return found


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

        args_list = [(f, lowercase, mod_path) for f in files_to_scan]
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

    def validate_math_precision(self):
        """Flag math expression operator literals with >5 decimal places (ERROR)."""
        self._log_section("Checking for math expression precision issues...")

        txt_files = self._collect_files(
            ["common/**/*.txt", "events/**/*.txt", "history/**/*.txt"]
        )
        args_list = [(f, self.mod_path) for f in txt_files]
        all_results = self._pool_map(
            process_file_for_math_precision, args_list, chunksize=30
        )
        issues = [issue for file_issues in all_results for issue in file_issues]
        self._report(
            issues,
            "✓ No math expression precision issues found",
            "Math expression literals with >5 decimal places (engine silently truncates):",
            severity=Severity.ERROR,
            category="math-precision",
        )

    def validate_orphan_money_setters(self):
        """Flag money-variable setters whose value is never consumed (WARNING).

        set_temp_variable of treasury_change/debt_change/int_investment_change
        must be followed, within the same effect block, by the matching
        modify_*_effect call or a wrapper that consumes it — otherwise the
        setter is dead and the transfer silently never happens. A setter
        re-written at the same brace depth before the consumer runs is
        equally dead (clobbered).
        """
        self._log_section("Checking for orphan money-variable setters...")

        txt_files = self._collect_files(
            [
                "common/national_focus/*.txt",
                "common/decisions/**/*.txt",
                "common/on_actions/**/*.txt",
                "events/**/*.txt",
            ]
        )
        if not txt_files:
            self.log("✓ No orphan money-variable setters found")
            return

        effect_files = self._collect_files(
            ["common/scripted_effects/**/*.txt"], ignore_staged=True
        )
        consumer_map = build_money_consumer_map(effect_files)
        args_list = [(f, self.mod_path, consumer_map) for f in txt_files]
        all_results = self._pool_map(
            process_file_for_orphan_money, args_list, chunksize=30
        )
        issues = [issue for file_issues in all_results for issue in file_issues]
        self._report(
            issues,
            "✓ No orphan money-variable setters found",
            "Dead money-variable setters (never consumed, or overwritten before the consumer runs — the money never moves):",
            severity=Severity.WARNING,
            category="orphan-money-setter",
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

        if self.staged_files:
            yml_files_to_scan = [f for f in self.staged_files if f.endswith(".yml")]
        else:
            yml_files_to_scan = list(
                glob.iglob(os.path.join(self.mod_path, "**", "*.yml"), recursive=True)
            )

        targets_tuple = tuple(potential_results)
        targets_used_in_loc: set = set()
        for found in self._pool_map(
            _scan_targets_in_loc,
            [(f, targets_tuple) for f in yml_files_to_scan],
            chunksize=30,
        ):
            targets_used_in_loc |= found

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
        self.validate_math_precision()
        self.validate_orphan_money_setters()

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
                pool=self._get_pool(),
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
            pool=self._get_pool(),
        )
        self.validate_cleared_event_targets(et_cleared, et_set)
        self.validate_missing_event_targets(et_used, et_set)
        self.validate_unused_event_targets(et_set, et_used)
        self.validate_flag_syntax()


if __name__ == "__main__":
    run_validator_main(
        Validator, "Validate variables and event targets in Millennium Dawn mod"
    )
