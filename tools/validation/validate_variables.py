#!/usr/bin/env python3
# Variable and event target validation: checks flags (country/state/global) and
# event targets for cleared-but-not-set, used-but-not-set, and unused items.
# Based on Kaiserreich Autotests by Pelmen (https://github.com/Pelmen323).
import bisect
import glob
import os
import re
import sys
from multiprocessing import Pool
from typing import Dict, List, Set, Tuple, cast

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import disk_cache

# strip_comments is quote-aware: a '#' inside a quoted log string must survive,
# or the orphaned quote desyncs extract_block_from_text's in-string tracking
# and container spans are silently lost.
from shared_utils import (
    blank_quoted_strings,
    compute_line_offsets,
    extract_block_from_text,
    line_for_offset,
    read_text_under,
    strip_comments,
)
from validator_common import (
    HOI4_BUILTIN_BLOCKS,
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
# Shorthand variable assignment: `set_variable = { my_var = 0.1234567 }` (also
# set_temp_variable / add_to_variable / multiply_variable / …). The value sits
# on the RHS of the variable name, not behind a `value =` key, so the operator
# pattern above misses it. Requires a `..._variable` opener so a plain
# `{ key = 0.123456 }` block (e.g. an ai_will_do factor) is not matched. The
# `[^{}]*?` lets the offending key sit anywhere in the block, not just first, so
# `clamp_variable = { var = x min = 0.123456789 }` is still caught.
_MATH_PRECISION_SHORTHAND_RE = re.compile(
    r"\b\w*_variable\s*=\s*\{[^{}]*?\b\w+\s*=\s*[-+]?\d*\.\d{6,}"
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
    namespace = f"variables.flags.{flag_type}.lc={'1' if lowercase else '0'}"
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

    # Quote-aware comment strip, then blank quoted-string interiors so a `#` or a
    # high-precision decimal inside a `desc = "..."` string is neither treated as
    # a comment nor mis-flagged as a truncated math literal.
    cleaned = blank_quoted_strings(strip_comments(text))
    rel = os.path.relpath(filename, mod_path)

    issues: List[str] = []
    # Both patterns fire on `..._variable = { ... value = X.XXXXXX }`, matching the
    # same literal (same end offset). Dedupe on it so one bad literal is one finding;
    # the operator pattern runs first, so its tighter match text is what's reported.
    seen_ends: set = set()
    for pattern in (_MATH_PRECISION_RE, _MATH_PRECISION_SHORTHAND_RE):
        for m in pattern.finditer(cleaned):
            if m.end() in seen_ends:
                continue
            seen_ends.add(m.end())
            line = cleaned[: m.start()].count("\n") + 1
            issues.append(
                f"{rel}:{line} - math expression literal with >5 decimal places"
                f" (engine truncates silently): {m.group(0).strip()}"
            )
    return issues


# A variable clamped to a literal range can never hold a value outside it, so a
# check_variable comparing against one is dead logic — always true or always false.
# The sub-1 case is the same bug seen from the other side: a 0-1 scale value written
# against a variable clamped to a wide integer range (taliban_strength > 0.19 on a
# 0..100 clamp fires immediately instead of at 19%). Same failure class as the
# `threat > 40` trap in general-rules.md.
_CLAMP_RE = re.compile(
    r"clamp_variable\s*=\s*\{(?P<body>[^{}]*?)\}",
    re.S,
)
_CLAMP_VAR_RE = re.compile(r"\bvar\s*=\s*([A-Za-z_][A-Za-z0-9_.]*)")
_CLAMP_MIN_RE = re.compile(r"\bmin\s*=\s*(-?\d+(?:\.\d+)?)")
_CLAMP_MAX_RE = re.compile(r"\bmax\s*=\s*(-?\d+(?:\.\d+)?)")
# `check_variable = { my_var > 5 }` and `check_variable = { var = my_var value = 5 ... }`
_CHECKVAR_SHORT_RE = re.compile(
    r"check_variable\s*=\s*\{\s*([A-Za-z_][A-Za-z0-9_.]*)\s*[<>=]\s*(-?\d+(?:\.\d+)?)\s*\}"
)
_CHECKVAR_LONG_RE = re.compile(
    r"check_variable\s*=\s*\{\s*var\s*=\s*([A-Za-z_][A-Za-z0-9_.]*)\s+value\s*=\s*(-?\d+(?:\.\d+)?)"
)
# A clamp on a scratch parameter constrains that one invocation, not the variable,
# so its range says nothing about what a check elsewhere may compare against.
_SET_TEMP_VAR_RE = re.compile(
    r"set_temp_variable\s*=\s*\{\s*(?:var\s*=\s*)?([A-Za-z_][A-Za-z0-9_.]*)"
)
_SET_PERSISTENT_VAR_RE = re.compile(
    r"set(?:_global)?_variable\s*=\s*\{\s*(?:var\s*=\s*)?([A-Za-z_][A-Za-z0-9_.]*)"
)


_UNTOOLTIPPED_TRIGGER_RE = re.compile(r"\bcheck_variable\s*=\s*\{")
_TOOLTIP_WRAPPER_TOKENS = frozenset(
    {"custom_trigger_tooltip", "hidden_trigger", "custom_override_tooltip"}
)
# check_variable takes its own inline `tooltip = KEY`, which renders the same
# requirement line a wrapper would. `\b` does not match custom_trigger_tooltip.
_INLINE_TOOLTIP_RE = re.compile(r"\btooltip\s*=")
_PLAYER_FACING_BLOCK = "available"
# Both `available` scans cover the same player-facing object types.
_PLAYER_FACING_GLOBS = [
    "common/decisions/**/*.txt",
    "common/national_focus/*.txt",
    "common/ideas/*.txt",
    "common/military_industrial_organization/**/*.txt",
    "common/operations/*.txt",
    "common/special_projects/**/*.txt",
    "common/scripted_diplomatic_actions/*.txt",
]
# Shorthand and long form, both flag types: `has_country_flag = X` /
# `has_global_flag = { flag = X value > 0 }`. Group 1 is the flag kind
# ("country"|"global"), group 2 the flag name.
_AVAILABLE_FLAG_RE = re.compile(
    r"\bhas_(country|global)_flag\s*=\s*(?:\{\s*flag\s*=\s*)?([A-Za-z_][A-Za-z0-9_.@]*)"
)


# Variable effects that render a tooltip line. The `*_temp_variable` forms are
# excluded structurally — no alternation below is a substring of them — because a
# temp variable backs no dynamic modifier and survives nothing the player sees.
_VAR_TOOLTIP_EFFECT_RE = re.compile(
    r"\b(?:set|add_to|subtract_from|multiply|divide|clamp)_variable\s*=\s*\{"
)
# Only the two write forms that move an existing modifier by a delta.
_VAR_WRITE_EFFECT_RE = re.compile(r"\b(add_to|subtract_from)_variable\s*=\s*\{")
_TOOLTIP_KEY_RE = re.compile(r"\btooltip\s*=\s*([A-Za-z_][A-Za-z0-9_.]*)")
# Target variable of a variable effect: shorthand `{ my_var = 5 }` or long form
# `{ var = my_var value = 5 }`.
_VAR_TARGET_RE = re.compile(r"\{\s*(?:var\s*=\s*)?([A-Za-z_][A-Za-z0-9_.:^]*)")

_RE_HIDDEN_EFFECT = re.compile(r"\bhidden_effect\s*=\s*\{")
# Block kinds the engine renders as a player-facing effect tooltip. cancel_effect
# is absent on purpose: it fires on cancellation, not on a player action.
_TOOLTIP_EFFECT_BLOCKS = (
    "complete_effect",
    "timeout_effect",
    "remove_effect",
    "completion_reward",
    "option",
    "on_complete",
)
_RE_TOOLTIP_EFFECT_BLOCK = re.compile(
    r"\b(?:" + "|".join(_TOOLTIP_EFFECT_BLOCKS) + r")\s*=\s*\{"
)

# Dynamic modifier definitions: `<modifier_key> = <backing_variable>` at depth 1
# of a `<modifier_name> = { ... }` block.
_DM_PAIR_RE = re.compile(r"^([A-Za-z_][\w.]*)\s*=\s*([^\s{}#]+)$")
_DM_NON_MODIFIER_KEYS = frozenset(
    {"icon", "enable", "remove_trigger", "custom_modifier_tooltip"}
)
# `x` is the placeholder icon; yes/no are booleans, not variables.
_DM_NON_VARIABLE_VALUES = frozenset({"yes", "no", "x"})


def _matching_brace(text: str, open_idx: int) -> int:
    """Index of the `}` closing the `{` at ``open_idx``, or ``len(text)`` if unbalanced."""
    depth = 0
    for i in range(open_idx, len(text)):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
    return len(text)


def _brace_spans(text: str, pattern) -> List[Tuple[int, int]]:
    """(open, close) offsets of every block whose opener matches ``pattern``."""
    return [
        (m.start(), _matching_brace(text, m.end() - 1)) for m in pattern.finditer(text)
    ]


def _span_index(spans: List[Tuple[int, int]]) -> Tuple[List[int], List[int]]:
    """Sorted starts plus a prefix-max of ends, for O(log n) containment tests.

    The prefix-max is what makes nesting work: a position inside an outer span
    but past every inner one still resolves to the outer span's end.
    """
    spans = sorted(spans)
    starts = [start for start, _ in spans]
    max_ends: List[int] = []
    running = -1
    for _, end in spans:
        running = max(running, end)
        max_ends.append(running)
    return starts, max_ends


def _inside(index: Tuple[List[int], List[int]], pos: int) -> bool:
    starts, max_ends = index
    i = bisect.bisect_right(starts, pos) - 1
    return i >= 0 and max_ends[i] > pos


def _normalise_variable(name: str) -> str:
    """Strip scope prefixes and array indices so a write matches its definition.

    `var:X`, `global.X`, `BRA.X` and `SPR.X^0` all name the same variable X.
    """
    if name.startswith("var:"):
        name = name[4:]
    name = name.split("^", 1)[0]
    if "." in name:
        name = name.rsplit(".", 1)[1]
    return name


def collect_clamp_ranges(
    args: Tuple[str, str],
) -> Tuple[List[Tuple[str, float, float]], List[str], List[str]]:
    """Pool worker: harvest ``clamp_variable`` min/max pairs and variable writes."""
    filename, _mod_path = args
    if should_skip_file(filename):
        return [], [], []
    try:
        from pathlib import Path as _Path

        text = _Path(filename).read_text(encoding="utf-8-sig", errors="replace")
        cleaned = blank_quoted_strings(strip_comments(text))
    except Exception:
        return [], [], []
    found: List[Tuple[str, float, float]] = []
    for m in _CLAMP_RE.finditer(cleaned):
        body = m.group("body")
        var = _CLAMP_VAR_RE.search(body)
        lo = _CLAMP_MIN_RE.search(body)
        hi = _CLAMP_MAX_RE.search(body)
        if var and lo and hi:
            name = var.group(1)
            if name.startswith("global."):
                name = name[7:]
            try:
                lower = float(lo.group(1))
                upper = float(hi.group(1))
            except ValueError:
                continue
            found.append((name, lower, upper))
    temp_written = _SET_TEMP_VAR_RE.findall(cleaned)
    persistent_written = _SET_PERSISTENT_VAR_RE.findall(cleaned)
    return found, temp_written, persistent_written


def process_file_for_clamp_conflicts(args) -> List[str]:
    """Pool worker: flag check_variable comparisons that contradict a clamp range."""
    filename, mod_path, ranges = args
    if should_skip_file(filename):
        return []
    try:
        from pathlib import Path as _Path

        text = _Path(filename).read_text(encoding="utf-8-sig", errors="replace")
        cleaned = blank_quoted_strings(strip_comments(text))
    except Exception:
        return []
    rel = os.path.relpath(filename, mod_path)

    issues: List[str] = []
    seen_ends: set = set()
    for pattern in (_CHECKVAR_SHORT_RE, _CHECKVAR_LONG_RE):
        for m in pattern.finditer(cleaned):
            if m.end() in seen_ends:
                continue
            name, raw = m.group(1), m.group(2)
            base = name[7:] if name.startswith("global.") else name
            bounds = ranges.get(base)
            if not bounds:
                continue
            lo, hi = bounds
            try:
                value = float(raw)
            except ValueError:
                continue
            line = cleaned[: m.start()].count("\n") + 1
            if value < lo or value > hi:
                seen_ends.add(m.end())
                issues.append(
                    f"{rel}:{line} - {base} is clamped to {lo}..{hi} but compared"
                    f" against {raw} — the check can never change outcome"
                )
            elif hi >= 10 and 0 < abs(value) < 1:
                seen_ends.add(m.end())
                issues.append(
                    f"{rel}:{line} - {base} is clamped to {lo}..{hi} but compared"
                    f" against {raw} — looks like a 0-1 scale value on a 0-{hi:g} variable"
                )
    return issues


def _scan_available_file(
    args: Tuple[str, str],
) -> Tuple[List[Tuple[str, str, int]], List[Tuple[str, str, int, str]]]:
    """Extract both available-block checks from one comment-stripped source."""
    filename, mod_path = args
    if should_skip_file(filename):
        return [], []
    try:
        from pathlib import Path as _Path

        text = _Path(filename).read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return [], []

    cleaned = blank_quoted_strings(strip_comments(text))
    rel = os.path.relpath(filename, mod_path)
    events: List[Tuple[int, int, object]] = []
    for m in _SCOPE_OPEN_RE.finditer(cleaned):
        events.append((m.end() - 1, 0, m.group(1)))
    for m in re.finditer(r"\}", cleaned):
        events.append((m.start(), 1, ""))
    for m in _UNTOOLTIPPED_TRIGGER_RE.finditer(cleaned):
        open_idx = m.end() - 1
        body = cleaned[open_idx : _matching_brace(cleaned, open_idx)]
        if not _INLINE_TOOLTIP_RE.search(body):
            events.append((m.start(), 2, ""))
    for m in _AVAILABLE_FLAG_RE.finditer(cleaned):
        events.append((m.start(), 3, (m.group(1), m.group(2))))
    events.sort(key=lambda e: (e[0], e[1]))

    stack: List[str] = []
    untooltipped: List[Tuple[str, str, int]] = []
    flags: List[Tuple[str, str, int, str]] = []
    for pos, kind, tok in events:
        if kind == 0:
            stack.append(cast(str, tok))
            continue
        if kind == 1:
            if stack:
                stack.pop()
            continue
        if kind == 2:
            for token in reversed(stack):
                if token in _TOOLTIP_WRAPPER_TOKENS:
                    break
                if token == _PLAYER_FACING_BLOCK:
                    line = cleaned[:pos].count("\n") + 1
                    untooltipped.append(
                        (
                            "check_variable in `available` renders no tooltip line"
                            " - the player sees a blank requirement; wrap it in"
                            " custom_trigger_tooltip = { tooltip = KEY ... }",
                            rel,
                            line,
                        )
                    )
                    break
        elif kind == 3:
            flag_kind, flag = cast(Tuple[str, str], tok)
            if "@" in flag:
                continue
            for token in reversed(stack):
                if token in _TOOLTIP_WRAPPER_TOKENS:
                    break
                if token == _PLAYER_FACING_BLOCK:
                    flags.append((flag, rel, cleaned[:pos].count("\n") + 1, flag_kind))
                    break
    return untooltipped, flags


def process_file_for_untooltipped_available_checks(
    args: Tuple[str, str],
) -> List[Tuple[str, str, int]]:
    return _scan_available_file(args)[0]


def process_file_for_available_flags(
    args: Tuple[str, str],
) -> List[Tuple[str, str, int, str]]:
    return _scan_available_file(args)[1]


# A scripted trigger's body checking a flag with no tooltip wrapper is the
# one-hop-removed case the unlocalised-available-flag check cannot see:
# `pak_raj_border_available = yes` renders no tooltip of its own, so a caller
# in `available` with no wrapper shows the player nothing at all where a
# requirement line belongs. Wrappers inside the definition already supply that
# line, so those triggers stay out of the index.
# Global-flag bodies only: a repo-wide measurement including has_country_flag
# produced 270 pre-existing hits (mostly cooldown/eligibility helpers with a
# stable name that already reads as a requirement), against ~2 for the
# unlocalised-flag sibling check. Narrowed here per the border-war plan
# rather than shipping with `--strict` gating a backlog this size.
_HAS_FLAG_BODY_RE = re.compile(r"\bhas_global_flag\b")
_BARE_TRIGGER_CALL_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*=\s*yes\b")


def _scripted_trigger_body_has_unwrapped_global_flag(body: str) -> bool:
    """True when a has_global_flag sits outside every tooltip wrapper.

    A wrapper around the check inside the definition already supplies the
    requirement line (custom_trigger_tooltip / custom_override_tooltip) or
    hides it (hidden_trigger), so the call site does not need another one.
    """
    if not _HAS_FLAG_BODY_RE.search(body):
        return False
    events: List[Tuple[int, int, str]] = []
    for m in _SCOPE_OPEN_RE.finditer(body):
        events.append((m.end() - 1, 0, m.group(1)))
    for m in re.finditer(r"\}", body):
        events.append((m.start(), 1, ""))
    for m in _HAS_FLAG_BODY_RE.finditer(body):
        events.append((m.start(), 2, ""))
    events.sort(key=lambda e: (e[0], e[1]))
    stack: List[str] = []
    for _pos, kind, tok in events:
        if kind == 0:
            stack.append(tok)
        elif kind == 1:
            if stack:
                stack.pop()
        elif not any(t in _TOOLTIP_WRAPPER_TOKENS for t in stack):
            return True
    return False


def process_file_for_untooltipped_available_scripted_trigger(
    args: Tuple[str, str, frozenset],
) -> List[Tuple[str, str, int]]:
    """Pool worker: flag bare `<name> = yes` in `available` that resolves to a
    scripted trigger whose own body checks an unwrapped global flag, with no
    tooltip wrapper around the call.

    Walks the enclosing block stack outward from each call so a wrapper at any
    depth above it counts, not just the direct parent - same machinery as
    ``process_file_for_untooltipped_available_checks``.
    """
    filename, mod_path, flagged_names = args
    if not flagged_names:
        return []
    if should_skip_file(filename):
        return []
    try:
        from pathlib import Path as _Path

        text = _Path(filename).read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return []

    cleaned = blank_quoted_strings(strip_comments(text))
    call_matches = [
        (m.start(), m.group(1))
        for m in _BARE_TRIGGER_CALL_RE.finditer(cleaned)
        if m.group(1) in flagged_names
    ]
    if not call_matches:
        return []

    events: List[Tuple[int, int, str]] = []
    for m in _SCOPE_OPEN_RE.finditer(cleaned):
        events.append((m.end() - 1, 0, m.group(1)))
    for m in re.finditer(r"\}", cleaned):
        events.append((m.start(), 1, ""))
    for pos, name in call_matches:
        events.append((pos, 2, name))
    events.sort(key=lambda e: (e[0], e[1]))

    rel = os.path.relpath(filename, mod_path)
    stack: List[str] = []
    issues: List[Tuple[str, str, int]] = []
    for pos, kind, tok in events:
        if kind == 0:
            stack.append(tok)
        elif kind == 1:
            if stack:
                stack.pop()
        else:
            for token in reversed(stack):
                if token in _TOOLTIP_WRAPPER_TOKENS:
                    break
                if token == _PLAYER_FACING_BLOCK:
                    line = cleaned[:pos].count("\n") + 1
                    issues.append(
                        (
                            f"{tok} = yes in `available` resolves to a scripted"
                            " trigger that checks a flag directly - the player"
                            " sees no requirement line at all; wrap it in"
                            " custom_trigger_tooltip = { tooltip = KEY ... }",
                            rel,
                            line,
                        )
                    )
                    break
    return issues


def collect_dynamic_modifier_vars(args: Tuple[str, str]) -> List[Tuple[str, str]]:
    """Pool worker: harvest (backing variable, modifier key) pairs from one file.

    Depth-1 filtering is load-bearing — it keeps `remove_trigger` / `enable`
    bodies (`original_tag`, `has_country_flag`, …) out of the map.
    """
    filename, _mod_path = args
    try:
        from pathlib import Path as _Path

        text = _Path(filename).read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return []
    cleaned = blank_quoted_strings(strip_comments(text))

    pairs: List[Tuple[str, str]] = []
    depth = 0
    for raw_line in cleaned.splitlines():
        line = raw_line.strip()
        if depth == 1:
            m = _DM_PAIR_RE.match(line)
            if m:
                key, value = m.group(1), m.group(2)
                if key not in _DM_NON_MODIFIER_KEYS and value.lower() not in (
                    _DM_NON_VARIABLE_VALUES
                ):
                    try:
                        float(value)
                    except ValueError:
                        name = _normalise_variable(value)
                        if name:
                            pairs.append((name, key))
        depth += line.count("{") - line.count("}")
    return pairs


def process_file_for_variable_tooltips(
    args: Tuple[str, str],
) -> List[Tuple[str, str, int]]:
    """Pool worker: collect `tooltip = KEY` used inside variable effects.

    Returns (key, relative path, line) triples; the parent owns the loc index
    and does the missing-key filtering.
    """
    filename, mod_path = args
    if should_skip_file(filename):
        return []
    try:
        from pathlib import Path as _Path

        text = _Path(filename).read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return []

    cleaned = blank_quoted_strings(strip_comments(text))
    if "tooltip" not in cleaned:
        return []

    hidden = _span_index(_brace_spans(cleaned, _RE_HIDDEN_EFFECT))
    offsets = compute_line_offsets(cleaned)
    rel = os.path.relpath(filename, mod_path)

    issues: List[Tuple[str, str, int]] = []
    for m in _VAR_TOOLTIP_EFFECT_RE.finditer(cleaned):
        open_idx = m.end() - 1
        body = cleaned[open_idx : _matching_brace(cleaned, open_idx)]
        key = _TOOLTIP_KEY_RE.search(body)
        if not key or _inside(hidden, m.start()):
            continue
        pos = open_idx + key.start(1)
        issues.append((key.group(1), rel, line_for_offset(offsets, pos)))
    return issues


def process_file_for_missing_variable_tooltips(
    args,
) -> List[Tuple[str, str, Tuple[str, ...], str, int]]:
    """Pool worker: flag dynamic-modifier writes carrying no `tooltip =`.

    Fires only inside the block kinds the engine renders as a player tooltip, so
    a scripted_effects helper or a history bootstrap write — neither of which has
    a tooltip surface — is never reported. A `hidden_effect` anywhere above the
    write swallows the tooltip, so it wins over the enclosing rendered block.
    """
    filename, mod_path, backing = args
    if should_skip_file(filename):
        return []
    try:
        from pathlib import Path as _Path

        text = _Path(filename).read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return []

    cleaned = blank_quoted_strings(strip_comments(text))
    if "_variable" not in cleaned:
        return []

    rendered = _span_index(_brace_spans(cleaned, _RE_TOOLTIP_EFFECT_BLOCK))
    if not rendered[0]:
        return []
    hidden = _span_index(_brace_spans(cleaned, _RE_HIDDEN_EFFECT))
    offsets = compute_line_offsets(cleaned)
    rel = os.path.relpath(filename, mod_path)

    issues: List[Tuple[str, str, Tuple[str, ...], str, int]] = []
    for m in _VAR_WRITE_EFFECT_RE.finditer(cleaned):
        open_idx = m.end() - 1
        body = cleaned[open_idx : _matching_brace(cleaned, open_idx)]
        target = _VAR_TARGET_RE.match(body)
        if not target:
            continue
        name = _normalise_variable(target.group(1))
        keys = backing.get(name)
        if not keys or _TOOLTIP_KEY_RE.search(body):
            continue
        if not _inside(rendered, m.start()) or _inside(hidden, m.start()):
            continue
        effect = f"{m.group(1)}_variable"
        issues.append((effect, name, keys, rel, line_for_offset(offsets, m.start())))
    return issues


# modify_treasury_effect / modify_debt_effect / modify_international_investment_effect
# each write a country-scope variable (treasury / debt / int_investment) via
# add_to_variable. Called while the current scope is a STATE they silently write an
# unrelated state variable and the nation's balance never changes. The scope tracker
# below flags calls whose nearest enclosing scope switch is a state block with no
# intervening country-scope opener.
_TREASURY_EFFECT_KEYWORDS = (
    "modify_treasury_effect",
    "modify_debt_effect",
    "modify_international_investment_effect",
)
_TREASURY_ANCHOR_RE = re.compile(
    r"\b(modify_(?:treasury|debt|international_investment)_effect)\s*=\s*yes\b"
)
_SCOPE_OPEN_RE = re.compile(r"([^\s{}=]+)\s*=\s*\{")
# Effect iterators / scopes that switch the current scope to a STATE.
_STATE_SCOPE_TOKENS = frozenset(
    {
        "capital_scope",
        "random_owned_state",
        "every_owned_state",
        "all_owned_state",
        "random_state",
        "every_state",
        "all_state",
        "random_controlled_state",
        "every_controlled_state",
        "all_controlled_state",
        "random_owned_controlled_state",
        "every_owned_controlled_state",
        "random_neighbor_state",
        "every_neighbor_state",
        "all_neighbor_state",
    }
)
# Scopes that switch to a country / other non-state scope. These mask an outer
# state scope, so a treasury call inside them is not flagged. ROOT/PREV/FROM/THIS
# are treated as non-state conservatively (unknown target → don't flag).
_NONSTATE_SCOPE_TOKENS = frozenset(
    {
        "owner",
        "OWNER",
        "controller",
        "CONTROLLER",
        "ROOT",
        "PREV",
        "FROM",
        "THIS",
        "overlord",
    }
)
_TAG_SCOPE_RE = re.compile(r"^[A-Z][A-Z0-9]{2}(?:_[A-Za-z0-9]+)*$")
_DECIMAL_RE = re.compile(r"\d+\.\d+")


def _classify_scope_token(token: str, parent: str) -> str:
    """Classify a `token = {` opener as STATE, NONSTATE, or INHERIT.

    INHERIT means the block does not change scope (if/limit/effect args, weights),
    so the current scope is whatever the nearest STATE/NONSTATE ancestor set.
    """
    if token.isdigit() or _DECIMAL_RE.fullmatch(token):
        # A bare number is a state id at effect level, but a bucket weight inside
        # random_list (inherits the enclosing scope, not a state switch).
        if parent == "random_list":
            return "INHERIT"
        return "STATE"
    if token in _STATE_SCOPE_TOKENS:
        return "STATE"
    low = token.lower()
    if low.startswith(("random_", "every_", "all_")) and "state" in low:
        return "STATE"
    if token in _NONSTATE_SCOPE_TOKENS:
        return "NONSTATE"
    if token.startswith(("ROOT", "PREV", "FROM", "THIS", "var:", "event_target:")):
        return "NONSTATE"
    if "country" in low:
        return "NONSTATE"
    if _TAG_SCOPE_RE.match(token):
        return "NONSTATE"
    return "INHERIT"


def process_file_for_treasury_scope(
    args: Tuple[str, str],
) -> List[Tuple[str, str, int]]:
    """Pool worker: flag modify_treasury_effect calls that run in state scope.

    Returns (message, rel_path, line) tuples. Only flags a call whose nearest
    enclosing scope switch is a state block — conservative, so an intervening
    owner/CONTROLLER/tag/ROOT opener suppresses the finding.
    """
    filename, mod_path = args
    if should_skip_file(filename):
        return []
    try:
        from pathlib import Path as _Path

        text = _Path(filename).read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return []

    cleaned = strip_comments(text)
    if not any(k in cleaned for k in _TREASURY_EFFECT_KEYWORDS):
        return []

    # Blank quoted-string interiors so a literal `}` inside a `log = "...}"`
    # string can't be counted as a real close brace and desync the scope stack.
    cleaned = blank_quoted_strings(cleaned)

    events = []
    for m in _SCOPE_OPEN_RE.finditer(cleaned):
        events.append((m.end() - 1, 0, m.group(1)))
    for m in re.finditer(r"\}", cleaned):
        events.append((m.start(), 1, None))
    for m in _TREASURY_ANCHOR_RE.finditer(cleaned):
        events.append((m.start(), 2, m.group(1)))
    events.sort(key=lambda e: (e[0], e[1]))

    rel = os.path.relpath(filename, mod_path)
    stack: List[Tuple[str, str]] = []
    issues: List[Tuple[str, str, int]] = []
    for pos, kind, tok in events:
        if kind == 0:
            parent = stack[-1][1] if stack else ""
            stack.append((_classify_scope_token(tok, parent), tok))
        elif kind == 1:
            if stack:
                stack.pop()
        else:
            scope = ""
            frame_tok = ""
            for cat, ftok in reversed(stack):
                if cat in ("STATE", "NONSTATE"):
                    scope = cat
                    frame_tok = ftok
                    break
            if scope == "STATE":
                line = cleaned[:pos].count("\n") + 1
                issues.append(
                    (
                        f"{tok} runs in state scope"
                        f" (inside `{frame_tok} = {{`) — the target is a country"
                        f" variable, so the nation's balance never changes",
                        rel,
                        line,
                    )
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


def build_money_consumer_map(
    effect_files: List[str], under: str
) -> Dict[str, frozenset]:
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
            text = strip_comments(read_text_under(fp, under))
        except (OSError, ValueError):
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
        holder_start = -1
        holder_end = -1
        holder_is_tooltip = False
        for start, end, is_tt in spans:
            if start <= m.start() < end and start > holder_start:
                holder_start = start
                holder_end = end
                holder_is_tooltip = is_tt
        if holder_start < 0:
            continue
        if holder_is_tooltip:
            # Setter previewed in a tooltip: any consumer within it renders.
            hits = list(consumer_res[var].finditer(cleaned, m.end(), holder_end))
        else:
            # Runtime setter: consumers that only exist inside a nested
            # effect_tooltip are previews and never execute.
            hits = [
                cm
                for cm in consumer_res[var].finditer(cleaned, m.end(), holder_end)
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
        f"variables.targets.lc={'1' if lowercase else '0'}",
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
            line_no = result.get("line", 0) or 0
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

        cleared_flags = (
            DataCleaner.clear_false_positives_partial_match(
                list(cleared_paths.keys()), tuple(false_positives)
            )
            or []
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

        used_flags = (
            DataCleaner.clear_false_positives_partial_match(
                list(used_paths.keys()), tuple(false_positives)
            )
            or []
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

        set_flags = (
            DataCleaner.clear_false_positives_partial_match(
                list(set_paths.keys()), tuple(false_positives)
            )
            or []
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
        consumer_map = build_money_consumer_map(effect_files, self.mod_path)
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

    def validate_treasury_state_scope(self):
        """Flag treasury/debt/investment effect calls in state scope (WARNING).

        Each effect writes a country-scope variable (treasury / debt /
        int_investment); called inside a state block (state id,
        random_owned_state, ...) it silently writes an unrelated state variable
        and the money never moves. Only flags when the nearest enclosing scope
        switch is a state — an intervening owner/CONTROLLER/tag/ROOT opener
        suppresses it.
        """
        self._log_section(
            "Checking for treasury/debt/investment effects in state scope..."
        )

        txt_files = self._collect_files(
            [
                "common/national_focus/*.txt",
                "common/decisions/**/*.txt",
                "common/on_actions/**/*.txt",
                "common/special_projects/**/*.txt",
                "common/intelligence_agency_upgrades/**/*.txt",
                "events/**/*.txt",
            ]
        )
        if not txt_files:
            self.log("✓ No treasury/debt/investment state-scope issues found")
            return

        args_list = [(f, self.mod_path) for f in txt_files]
        all_results = self._pool_map(
            process_file_for_treasury_scope, args_list, chunksize=30
        )
        issues = [issue for file_issues in all_results for issue in file_issues]
        self._report(
            issues,
            "✓ No treasury/debt/investment state-scope issues found",
            "treasury/debt/investment effect calls in state scope (each writes a country variable — the money never moves):",
            severity=Severity.WARNING,
            category="treasury-state-scope",
        )

    def validate_clamp_range_conflicts(self):
        """Flag check_variable comparisons that contradict the variable's own clamp.

        A variable clamped to a literal min/max can never hold a value outside
        that range, so comparing against one is dead logic. The paired sub-1
        heuristic catches the inverse slip: a 0-1 scale value written against a
        variable clamped to a wide integer range.
        """
        self._log_section("Checking clamp ranges against check_variable values...")

        txt_files = self._collect_files(["common/**/*.txt", "events/**/*.txt"])
        if not txt_files:
            self.log("✓ No clamp-range conflicts found")
            return

        # Clamps are harvested repo-wide even in staged mode: the clamp and the
        # check that contradicts it almost never sit in the same file.
        clamp_files = self._collect_files(
            ["common/**/*.txt", "events/**/*.txt"], ignore_staged=True
        )
        args_list = [(f, self.mod_path) for f in clamp_files]
        harvested = self._pool_map(collect_clamp_ranges, args_list, chunksize=30)
        ranges: Dict[str, Tuple[float, float]] = {}
        temp_names: Set[str] = set()
        persistent_names: Set[str] = set()
        for file_ranges, temp_written, persistent_written in harvested:
            for name, lo, hi in file_ranges:
                if name in ranges:
                    prev = ranges[name]
                    ranges[name] = (min(prev[0], lo), max(prev[1], hi))
                else:
                    ranges[name] = (lo, hi)
            temp_names.update(temp_written)
            persistent_names.update(persistent_written)
        for name in temp_names - persistent_names:
            ranges.pop(name, None)
        if not ranges:
            self.log("✓ No clamp-range conflicts found")
            return

        conflict_args = [(f, self.mod_path, ranges) for f in txt_files]
        all_results = self._pool_map(
            process_file_for_clamp_conflicts, conflict_args, chunksize=30
        )
        issues = [issue for file_issues in all_results for issue in file_issues]
        self._report(
            issues,
            "✓ No clamp-range conflicts found",
            "check_variable comparisons that contradict the variable's clamp range:",
            severity=Severity.WARNING,
            category="clamp-range-conflict",
        )

    def _get_available_scan(self):
        """Return both available-block scans from one per-file worker pass."""
        memo = getattr(self, "_available_scan_memo", None)
        if memo is not None:
            return memo
        files = self._collect_files(_PLAYER_FACING_GLOBS)
        if not files:
            self._available_scan_memo = []
            return self._available_scan_memo
        self._available_scan_memo = self._pool_map(
            _scan_available_file,
            [(f, self.mod_path) for f in files],
            chunksize=30,
        )
        return self._available_scan_memo

    def validate_untooltipped_available_checks(self):
        """Flag bare check_variable inside `available` blocks (WARNING).

        `visible` is excluded: a failing visible hides the object outright, so
        there is no tooltip surface for the check to render into.
        """
        self._log_section(
            "Checking for untooltipped check_variable in available blocks..."
        )

        available = self._get_available_scan()
        if not available:
            self.log("✓ No untooltipped check_variable in available blocks")
            return

        issues = [issue for untooltipped, _flags in available for issue in untooltipped]
        self._report(
            issues,
            "✓ No untooltipped check_variable in available blocks",
            "check_variable in `available` with no tooltip wrapper (the player sees a blank requirement line):",
            severity=Severity.WARNING,
            category="untooltipped-available-check",
        )

    def validate_unlocalised_available_flags(self):
        """Flag `has_country_flag` / `has_global_flag` in `available` whose flag
        has no loc key (WARNING).

        HOI4 renders the requirement line from a loc key named after the flag;
        with no key the player reads the raw token.
        """
        self._log_section("Checking for unlocalised flags in available blocks...")

        available = self._get_available_scan()
        if not available:
            self.log("✓ No unlocalised flags in available blocks")
            return

        loc_keys = self._load_localisation_keys()

        seen: Set[Tuple[str, str]] = set()
        issues = []
        for _unt, file_results in available:
            for flag, rel, line, flag_kind in file_results:
                if flag in loc_keys:
                    continue
                key = (flag, rel)
                if key in seen:
                    continue
                seen.add(key)
                issues.append(
                    (
                        f"has_{flag_kind}_flag = {flag} in `available` has no localisation"
                        " key - the player sees the raw flag name; add a loc key named"
                        " after the flag",
                        rel,
                        line,
                    )
                )

        self._report(
            issues,
            "✓ No unlocalised flags in available blocks",
            "flags checked in `available` with no localisation key (the player sees the raw token):",
            severity=Severity.WARNING,
            category="unlocalised-available-flag",
        )

    def _collect_scripted_trigger_flag_names(self) -> frozenset:
        """Names of common/scripted_triggers/** definitions whose body checks a
        global flag that is not already under a tooltip wrapper.

        A `custom_trigger_tooltip` / `custom_override_tooltip` / `hidden_trigger`
        around the flag inside the definition already renders or hides the
        requirement line, so a bare `<name> = yes` call is not a finding.
        Narrowed to `has_global_flag` only (not `has_country_flag`): a
        repo-wide measurement against both produced 270 pre-existing hits
        outside the border-war files, versus ~2 for the sibling
        unlocalised-available-flag check. Harvested repo-wide even in staged
        mode: the scripted trigger's own definition and the decision/focus
        that calls it bare in `available` are almost never in the same file.
        """
        memo = getattr(self, "_scripted_trigger_flag_names_memo", None)
        if memo is not None:
            return memo

        files = self._collect_files(
            ["common/scripted_triggers/**/*.txt"], ignore_staged=True
        )
        names: Set[str] = set()
        for fp in files:
            try:
                with open(fp, "r", encoding="utf-8-sig", errors="replace") as fh:
                    text = blank_quoted_strings(strip_comments(fh.read()))
            except Exception:
                continue
            for m in _SCRIPTED_EFFECT_DEF_RE.finditer(text):
                name = m.group(1)
                if name in HOI4_BUILTIN_BLOCKS:
                    continue
                body, _ = extract_block_from_text(text, m.start())
                if body and _scripted_trigger_body_has_unwrapped_global_flag(body):
                    names.add(name)

        self._scripted_trigger_flag_names_memo = frozenset(names)
        return self._scripted_trigger_flag_names_memo

    def validate_untooltipped_available_scripted_trigger(self):
        """Flag bare scripted-trigger calls in `available` whose body checks a
        flag with no tooltip wrapper (WARNING).

        One hop further out than ``validate_unlocalised_available_flags``: a
        bare flag check at least renders the raw token, but a bare call to a
        scripted trigger wrapping that same check (``pak_raj_border_available
        = yes``) renders no tooltip line at all - the player sees nothing
        where a requirement should be. A wrapper around the flag inside the
        scripted trigger itself already supplies the line, so that call is
        not a finding.
        """
        self._log_section(
            "Checking for untooltipped scripted-trigger calls in available blocks..."
        )

        flagged_names = self._collect_scripted_trigger_flag_names()
        if not flagged_names:
            self.log("✓ No untooltipped scripted-trigger calls in available blocks")
            return

        txt_files = self._collect_files(_PLAYER_FACING_GLOBS)
        if not txt_files:
            self.log("✓ No untooltipped scripted-trigger calls in available blocks")
            return

        args_list = [(f, self.mod_path, flagged_names) for f in txt_files]
        all_results = self._pool_map(
            process_file_for_untooltipped_available_scripted_trigger,
            args_list,
            chunksize=30,
        )
        issues = [issue for file_issues in all_results for issue in file_issues]
        self._report(
            issues,
            "✓ No untooltipped scripted-trigger calls in available blocks",
            "bare scripted-trigger call in `available` whose body checks a flag directly, with no tooltip wrapper (the player sees no requirement line at all):",
            severity=Severity.WARNING,
            category="untooltipped-available-scripted-trigger",
        )

    def _collect_dynamic_modifier_vars(self) -> Dict[str, Tuple[str, ...]]:
        """Map each dynamic-modifier backing variable to the modifier keys it drives.

        Harvested repo-wide even in staged mode: the modifier definition and the
        write that moves it are almost never in the same file. One variable can
        back several modifier keys, so the value is a tuple.
        """
        memo = getattr(self, "_dyn_mod_vars_memo", None)
        if memo is not None:
            return memo

        files = self._collect_files(
            ["common/dynamic_modifiers/**/*.txt"], ignore_staged=True
        )
        mapping: Dict[str, Set[str]] = {}
        harvested = self._pool_map(
            collect_dynamic_modifier_vars,
            [(f, self.mod_path) for f in files],
            chunksize=10,
        )
        for pairs in harvested:
            for name, key in pairs:
                mapping.setdefault(name, set()).add(key)

        self._dyn_mod_vars_memo = {
            name: tuple(sorted(keys)) for name, keys in mapping.items()
        }
        return self._dyn_mod_vars_memo

    def validate_variable_tooltip_keys(self):
        """Flag `tooltip = KEY` in a variable effect whose key has no loc entry.

        The engine renders the raw key when it does not resolve, so the player
        reads `political_power_factor_tt` instead of the modifier line.
        """
        self._log_section("Checking variable effect tooltip keys...")

        txt_files = self._collect_files(["common/**/*.txt", "events/**/*.txt"])
        if not txt_files:
            self.log("✓ No unlocalised variable effect tooltips found")
            return

        args_list = [(f, self.mod_path) for f in txt_files]
        all_results = self._pool_map(
            process_file_for_variable_tooltips, args_list, chunksize=30
        )
        loc_keys = self._load_localisation_keys()

        seen: Set[Tuple[str, str]] = set()
        issues: List[Tuple[str, str, int]] = []
        for file_results in all_results:
            for key, rel, line in file_results:
                if key in loc_keys or (key, rel) in seen:
                    continue
                seen.add((key, rel))
                issues.append(
                    (
                        f"tooltip = {key} has no English localisation entry - the"
                        " tooltip renders the raw key; add it to"
                        " MD_dm_modifiers_l_english.yml",
                        rel,
                        line,
                    )
                )

        self._report(
            issues,
            "✓ No unlocalised variable effect tooltips found",
            "variable effect tooltips whose key has no localisation entry (the player sees the raw key):",
            severity=Severity.WARNING,
            category="variable-tooltip-missing-loc",
        )

    def validate_missing_variable_tooltips(self):
        """Flag dynamic-modifier writes with no `tooltip =` (WARNING).

        Without one the modifier changes silently — the player gets no line for
        it anywhere. Scoped to rendered effect blocks; see the pool worker.
        """
        self._log_section("Checking dynamic modifier writes for tooltips...")

        txt_files = self._collect_files(["common/**/*.txt", "events/**/*.txt"])
        backing = self._collect_dynamic_modifier_vars() if txt_files else {}
        if not backing:
            self.log("✓ No untooltipped dynamic modifier writes found")
            return

        args_list = [(f, self.mod_path, backing) for f in txt_files]
        all_results = self._pool_map(
            process_file_for_missing_variable_tooltips, args_list, chunksize=30
        )
        loc_keys = self._load_localisation_keys()

        issues: List[Tuple[str, str, int]] = []
        for file_results in all_results:
            for effect, name, keys, rel, line in file_results:
                resolvable = [key for key in keys if f"{key}_tt" in loc_keys]
                prefix = (
                    f"{effect} = {{ {name} ... }} moves dynamic modifier"
                    f" `{keys[0]}` with no tooltip - the change is invisible to"
                    " the player;"
                )
                if resolvable:
                    fix = " or ".join(f"tooltip = {key}_tt" for key in resolvable)
                    issues.append((f"{prefix} add {fix}", rel, line))
                else:
                    issues.append(
                        (
                            f"{prefix} `{keys[0]}_tt` does not exist either, so add"
                            " it to MD_dm_modifiers_l_english.yml first",
                            rel,
                            line,
                        )
                    )

        self._report(
            issues,
            "✓ No untooltipped dynamic modifier writes found",
            "dynamic modifier writes in player-facing effect blocks with no `tooltip =` (the modifier changes silently):",
            severity=Severity.WARNING,
            category="dynamic-modifier-tooltip-missing",
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
        used_targets = (
            DataCleaner.clear_false_positives_partial_match(
                list(used_paths.keys()), tuple(FALSE_POSITIVES)
            )
            or []
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
        set_targets = (
            DataCleaner.clear_false_positives_partial_match(
                list(set_paths.keys()), tuple(FALSE_POSITIVES)
            )
            or []
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
        self.validate_treasury_state_scope()
        self.validate_clamp_range_conflicts()
        self.validate_untooltipped_available_checks()
        self.validate_unlocalised_available_flags()
        self.validate_untooltipped_available_scripted_trigger()
        self.validate_variable_tooltip_keys()
        self.validate_missing_variable_tooltips()

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
