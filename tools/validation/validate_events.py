#!/usr/bin/env python3
"""Validate event definitions in Millennium Dawn.

Based on Kaiserreich Autotests by Pelmen (https://github.com/Pelmen323),
adapted for Millennium Dawn with multiprocessing.
"""

import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import disk_cache
from shared_utils import blank_quoted_strings, extract_block_from_text, strip_comments
from sprite_index import build_sprite_index
from validator_common import (
    DEFAULT_EXTRA_SKIP_PATTERNS,
    BaseValidator,
    FileOpener,
    Severity,
    run_validator_main,
    should_skip_file,
)

EXTRA_SKIP_PATTERNS = DEFAULT_EXTRA_SKIP_PATTERNS

# The five HOI4 event-firing keywords. It is `operative_leader_event`, not
# `operative_event`, and there is no `character_event`; because `operative` has
# no word boundary before `_leader_event`, an `operative`/`_event` split never
# matches the real keyword. Kept in sync with the definition keywords in
# _EVENT_BLOCK_PATTERN / _EVENT_TYPE_PATTERN.
_EVENT_CALL_KEYWORDS = (
    "country_event",
    "news_event",
    "state_event",
    "unit_leader_event",
    "operative_leader_event",
)
_EVENT_CALL_ALT = "|".join(_EVENT_CALL_KEYWORDS)

_LONG_FORM_PATTERN = re.compile(
    r"\b(" + _EVENT_CALL_ALT + r")\s*=\s*\{\s*id\s*=\s*([^\s{}]+)\s*\}",
)

# Event picture: `picture = GFX_xxx` (always GFX_-prefixed, resolves to that
# sprite). Sprite names may contain `.` (frame suffixes like GFX_CTC.5) and `-`
# (e.g. GFX_Polizistin-Kiesewetter), so both are part of the captured name.
_EVENT_PICTURE_REF = re.compile(r'\bpicture\s*=\s*"?(GFX_[A-Za-z0-9_.\-]+)"?')


def _should_skip(filename: str) -> bool:
    return should_skip_file(filename, extra_skip_patterns=EXTRA_SKIP_PATTERNS)


def _extract_event_pictures(filename: str) -> List[Tuple[str, str, int]]:
    """Pool worker: return (sprite, filename, line) for each event picture ref."""
    if _should_skip(filename):
        return []
    try:
        text = Path(filename).read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return []
    text = re.sub(r"#[^\n]*", "", text)
    out: List[Tuple[str, str, int]] = []
    for m in _EVENT_PICTURE_REF.finditer(text):
        line = text.count("\n", 0, m.start()) + 1
        out.append((m.group(1), filename, line))
    return out


_ID_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_.]+")


def count_event_ids_in_file(args: Tuple[str, frozenset]) -> Dict[str, int]:
    """Pool worker: count occurrences of each tracked event ID in one file.

    Tokenizes the file body ONCE and counts whole-token matches against the
    tracked-ID set, rather than scanning the file once per tracked ID. The `.`
    is part of an identifier token, so `ALG_civilwar.1` and its loc keys
    `ALG_civilwar.1.t` / `.d` / `.a` tokenize as distinct tokens and don't
    inflate each other's counts.
    """
    filename, tracked_ids = args
    if _should_skip(filename):
        return {}
    try:
        text = Path(filename).read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return {}
    cleaned = re.sub(r"#[^\n]*", "", text)
    counts = Counter(_ID_TOKEN_PATTERN.findall(cleaned))
    return {eid: counts[eid] for eid in tracked_ids if eid in counts}


# Event IDs built at runtime by string interpolation never appear as a literal
# `namespace.number` token, so the whole-token scan can't see them. Matches the
# namespace before a `.[…]` / `.N[…]` interpolation following an event-firing
# keyword, e.g. `country_event = UN.[ID]` or `country_event = MD_cyber.1[TYPE]`.
_DYNAMIC_EVENT_NS_PATTERN = re.compile(
    r"(?:country_event|news_event|state_event|unit_leader_event|operative_leader_event)"
    r"\s*=\s*(?:\{\s*id\s*=\s*)?([A-Za-z_]\w*)\.[A-Za-z0-9_.]*\["
)


def scan_dynamic_event_namespaces(args: Tuple[str, frozenset]) -> Set[str]:
    """Pool worker: namespaces fired via string-interpolated event IDs in a file.

    Any triggered-only event in a returned namespace is reachable through dynamic
    dispatch and must not be reported as unreferenced.
    """
    filename = args[0]
    if _should_skip(filename):
        return set()
    try:
        text = Path(filename).read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return set()
    cleaned = re.sub(r"#[^\n]*", "", text)
    return set(_DYNAMIC_EVENT_NS_PATTERN.findall(cleaned))


# --- fire_only_once fired inside a country/state iterator ---
#
# An event with `fire_only_once = yes` fired inside an iterating scope
# (every_country / every_other_country / every_state / for_each_scope_loop /
# any every_* or for_each_* iterator) only reaches the first recipient: the
# flag is set on the first iteration and subsequent firings no-op. The
# caller meant to drop fire_only_once, or fire the event outside the loop.
# A scope switch to a FIXED recipient between the iterator and the call
# (ROOT/FROM/PREV/THIS, a literal tag, event_target:/var:) fires the same
# recipient every iteration, so fire_only_once is a legitimate dedup idiom
# there and the outer iterator is not flagged. `random_country` /
# `random_state` pick a single scope by design and are not iterators.

# Iterating effect scopes: every_* and for_each_* (array walkers). `any_*` /
# `all_*` are triggers, not effect loops, so events are never fired inside
# them; they are not matched here. random_* picks a single scope (not an
# iterator) but does not shield an outer iterator either, so it needs no
# frame kind of its own — its brace is just an "other" frame.
_FOF_ITER_OPEN = r"\b(?:every_\w+|for_each_\w+)\s*=\s*\{"
_RE_FOF_ITER_OPEN = re.compile(_FOF_ITER_OPEN)
# Scope-switch openers that pin the recipient to a fixed country: an explicit
# scope keyword (incl. chains like PREV.PREV), a literal 3-letter tag (AND/NOT
# excluded — trigger operators, not scopes), or an event_target:/var: ref.
_FOF_PINNED = (
    r"(?:(?:ROOT|FROM|PREV|THIS)(?:\.(?:ROOT|FROM|PREV|THIS))*"
    r"|(?:event_target|var):[\w.@:^]+"
    r"|(?<![A-Za-z0-9_])(?!AND|NOT)[A-Z]{3}(?![A-Za-z0-9_]))\s*=\s*\{"
)
_RE_FOF_PINNED_OPEN = re.compile(_FOF_PINNED)

# Event-call opens. Long form (`<type>_event = { id = X ... }`) and short
# form (`<type>_event = X`). The long-form alternative is tried first so the
# brace is consumed with the opener (the bare `\{` below never re-matches
# it).
_FOF_EVENT_LONG = r"\b(?:" + _EVENT_CALL_ALT + r")\s*=\s*\{"
_FOF_EVENT_SHORT = r"\b(?:" + _EVENT_CALL_ALT + r")\s*=\s*[A-Za-z0-9_.]+"
_RE_FOF_EVENT_LONG = re.compile(_FOF_EVENT_LONG)
_RE_FOF_EVENT_SHORT = re.compile(_FOF_EVENT_SHORT)
_RE_FOF_ID = re.compile(r"\bid\s*=\s*([^\s}]+)")
_RE_FOF_TOKEN = re.compile(
    "|".join(
        (r"\{", r"\}", _FOF_ITER_OPEN, _FOF_PINNED, _FOF_EVENT_LONG, _FOF_EVENT_SHORT)
    )
)


def _fof_stack_flags(stack: List[str]) -> bool:
    """Walk scope frames innermost-first; True iff the nearest loop/pin frame is
    an iterator. A "pinned" scope switch fixes the recipient, so it shields an
    outer iterator (dedup idiom); "other" frames (incl. random_*) are
    transparent, so a random pick nested inside an iterator is still flagged."""
    for kind in reversed(stack):
        if kind == "iter":
            return True
        if kind == "pinned":
            return False
    return False


def scan_fire_only_once_in_loop(args: Tuple[str, frozenset, str]) -> List[str]:
    """Pool worker: flag fire_only_once events fired inside an iterator."""
    filename, fire_only_once_ids, mod_path = args
    if not fire_only_once_ids or _should_skip(filename):
        return []
    try:
        text = Path(filename).read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return []
    # Cheap early-out: a file that fires no events can't fire one inside a loop,
    # so skip the two full-text transforms + tokenize on the bulk of the repo
    # (history/, ai_strategy/, unit stat files, ... none of which fire events).
    if not any(k in text for k in _EVENT_CALL_KEYWORDS):
        return []
    # Quote-aware: strip comments, then blank quoted-string interiors so a
    # literal brace inside a `log = "...{..."` string can't desync the depth
    # stack and corrupt every finding after it.
    cleaned = blank_quoted_strings(strip_comments(text))
    findings: List[str] = []

    def _flag(eid: str, pos: int) -> None:
        line = cleaned.count("\n", 0, pos) + 1
        rel = os.path.relpath(filename, mod_path)
        findings.append(
            f"{rel}:{line} - fire_only_once event {eid} fired inside"
            f" an every_*/for_each_* iterator (only the first"
            f" recipient gets it; drop fire_only_once or fire it"
            f" outside the loop)"
        )

    # Stack of scope frames: "iter" (every_/for_each_), "pinned"
    # (fixed-recipient scope switch), or "other" (limit / if / random_* /
    # completion_reward / the event-call block / ...). An event call is flagged
    # when the nearest enclosing loop/pin frame is an iterator (_fof_stack_flags).
    stack: List[str] = []
    for m in _RE_FOF_TOKEN.finditer(cleaned):
        tok = m.group(0)
        if tok == "{":
            stack.append("other")
        elif tok == "}":
            if stack:
                stack.pop()
        elif _RE_FOF_ITER_OPEN.match(tok):
            stack.append("iter")
        elif _RE_FOF_PINNED_OPEN.match(tok):
            stack.append("pinned")
        elif _RE_FOF_EVENT_LONG.match(tok):
            # Long form: extract id from the block body (id may not be first).
            stack.append("other")
            body, _ = extract_block_from_text(cleaned, m.end() - 1)
            idm = _RE_FOF_ID.search(body)
            eid = idm.group(1) if idm else None
            if eid and eid in fire_only_once_ids and _fof_stack_flags(stack[:-1]):
                _flag(eid, m.start())
        elif _RE_FOF_EVENT_SHORT.match(tok):
            eid = tok.split("=", 1)[1].strip()
            if eid in fire_only_once_ids and _fof_stack_flags(stack):
                _flag(eid, m.start())
    return findings


def process_txt_for_long_form_events(args: Tuple[str, str]) -> List[str]:
    """Pool worker: find id-only long-form event calls in one .txt file."""
    filename, mod_path = args
    if _should_skip(filename):
        return []
    try:
        text = Path(filename).read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return []
    cleaned = re.sub(r"#[^\n]*", "", text)
    results = []
    seen = set()
    for m in _LONG_FORM_PATTERN.finditer(cleaned):
        line = cleaned[: m.start()].count("\n") + 1
        rel = os.path.relpath(filename, mod_path)
        key = (rel, line, m.group(1), m.group(2))
        if key in seen:
            continue
        seen.add(key)
        results.append(
            f"{rel}:{line} - {m.group(1)} = {{ id = {m.group(2)} }} → use shorthand `{m.group(1)} = {m.group(2)}`"
        )
    return results


# --- Event parsing ---


_EVENT_BLOCK_PATTERN = re.compile(
    r"^(?:country_event|news_event|state_event|unit_leader_event|operative_leader_event)"
    r"\s*=\s*\{(.*?)^\}",
    flags=re.DOTALL | re.MULTILINE,
)


def _parse_events(text: str, basename: str) -> Tuple[List[str], Dict[str, str]]:
    events = []
    paths = {}
    for match in _EVENT_BLOCK_PATTERN.findall(text):
        events.append(match)
        paths[match] = basename
    return events, paths


def process_file_for_events(
    args: Tuple[str, bool, str],
) -> Tuple[List[str], Dict[str, str]]:
    filename, lowercase, mod_path = args
    text_file = FileOpener.open_text_file(
        filename, lowercase=lowercase, strip_comments_flag=True
    )
    basename = os.path.basename(filename)
    return disk_cache.per_file_cached_by_content(
        mod_path,
        f"events.blocks.lc={int(lowercase)}",
        filename,
        text_file,
        lambda: _parse_events(text_file, basename),
    )


_EVENT_TYPE_PATTERN = re.compile(
    r"^(country_event|news_event|state_event|unit_leader_event|operative_leader_event)\s*=\s*\{",
    re.MULTILINE,
)
_ADD_NAMESPACE_PATTERN = re.compile(r"^\s*add_namespace\s*=\s*(\S+)", re.MULTILINE)
_EVENT_ID_PATTERN = re.compile(r"^\tid\s*=\s*(\S+)", re.MULTILINE)
_RANDOM_EVENTS_PATTERN = re.compile(r"\brandom_events\s*=\s*\{")
_RANDOM_EVENT_ID_PATTERN = re.compile(r"=\s*([A-Za-z_]\w*\.[\w.]+)")
_OPTION_BLOCK_PATTERN = re.compile(r"\boption\s*=\s*\{")
# Event-level (depth-1) title/desc fields — option-level name fields are
# nested deeper and are not matched.
_EVENT_TITLEDESC_PATTERN = re.compile(r"^\t(?:title|desc)\s*=\s*(.+)$", re.MULTILINE)

# `id = X` line inside an event block (literal single-space form, distinct
# from _EVENT_ID_PATTERN's \s* form used in metadata parsing). Reused across
# validate_unsupported_title_desc / validate_missing_triggered_only /
# validate_missing_localisation / validate_triggered_only_unreferenced.
_EVENT_ID_LITERAL_RE = re.compile(r"^\tid = (\S+)", flags=re.MULTILINE)

# title/desc block-vs-inline detection (validate_unsupported_title_desc).
_TITLE_DESC_BLOCK_RE = {
    lt: re.compile(r"^\t" + lt + r" = \{", flags=re.MULTILINE)
    for lt in ("title", "desc")
}
_TITLE_DESC_INLINE_RE = {
    lt: re.compile(r"^\t" + lt + r" = \w", flags=re.MULTILINE)
    for lt in ("title", "desc")
}

# Extracts values from title/desc/name fields that look like loc keys (contain
# a dot). Covers simple form (title = foo.1.t) and block form
# (triggered_desc { desc = foo.1.t }). validate_missing_localisation.
_LOC_REF_PATTERN = re.compile(r"\b(?:title|desc|name)\s*=\s*([\w][\w.]*)", re.MULTILINE)


def _extract_random_event_ids(text: str) -> set:
    """Find event IDs referenced inside ``random_events = { ... }`` blocks.

    Events fired through ``random_events`` in on_actions use ``mean_time_to_happen``
    as the engine-side weight even though they're declared ``is_triggered_only``,
    so they must be excluded from the MTTH+triggered_only warning.
    """
    ids: set = set()
    for m in _RANDOM_EVENTS_PATTERN.finditer(text):
        body, _ = extract_block_from_text(text, m.end() - 1)
        for id_match in _RANDOM_EVENT_ID_PATTERN.finditer(body):
            ids.add(id_match.group(1))
    return ids


def _parse_event_metadata(text: str, basename: str) -> Tuple[List[dict], Set[str]]:
    namespaces: Set[str] = set(_ADD_NAMESPACE_PATTERN.findall(text))
    meta: List[dict] = []
    for m in _EVENT_TYPE_PATTERN.finditer(text):
        event_type = m.group(1)
        body, _ = extract_block_from_text(text, m.end() - 1)
        # Quote-aware comment strip + quoted-string blanking before the `in body`
        # flag checks: a commented-out `#fire_only_once = yes` (or hidden /
        # is_triggered_only / mean_time_to_happen) must not count as an active
        # directive, and a `#` (or one of those keywords) inside a quoted
        # log/desc string must not truncate the line or false-match.
        body_nc = blank_quoted_strings(strip_comments(body))

        id_match = _EVENT_ID_PATTERN.search(body)
        if not id_match:
            continue

        meta.append(
            {
                "id": id_match.group(1),
                "type": event_type,
                "file": basename,
                "is_hidden": "hidden = yes" in body_nc,
                "is_triggered_only": "is_triggered_only = yes" in body_nc,
                "fire_only_once": "fire_only_once = yes" in body_nc,
                "has_mtth": "mean_time_to_happen" in body_nc,
                "option_count": len(_OPTION_BLOCK_PATTERN.findall(body)),
                "title_desc_refs": [
                    v.strip() for v in _EVENT_TITLEDESC_PATTERN.findall(body)
                ],
            }
        )
    return meta, namespaces


class Validator(BaseValidator):
    TITLE = "EVENT VALIDATION"
    STAGED_EXTENSIONS = [".txt"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._events_cache: Optional[Tuple[List[str], Dict[str, str]]] = None
        self._meta_cache: Optional[Tuple[List[dict], set]] = None
        self._random_events_cache: Optional[set] = None
        self._fire_only_once_ids_cache: Optional[set] = None

    def _get_all_events(self) -> Tuple[List[str], Dict[str, str]]:
        if self._events_cache is not None:
            return self._events_cache
        files = self._collect_files(["events/**/*.txt"])
        args_list = [(f, False, self.mod_path) for f in files]
        all_results = self._pool_map(process_file_for_events, args_list, chunksize=10)

        events = []
        paths = {}
        for ev_list, ev_paths in all_results:
            events.extend(ev_list)
            paths.update(ev_paths)

        self._events_cache = (events, paths)
        return self._events_cache

    def _get_event_metadata(self) -> Tuple[List[dict], set]:
        """Parse all event files and return (event_metadata_list, declared_namespaces).

        Each metadata dict has: id, type, file, is_hidden,
        is_triggered_only, fire_only_once, has_mtth, option_count,
        title_desc_refs.
        """
        if self._meta_cache is not None:
            return self._meta_cache

        files = self._collect_files(["events/**/*.txt"])
        meta: List[dict] = []
        namespaces: set = set()

        for filepath in files:
            text = FileOpener.open_text_file(
                filepath, lowercase=False, strip_comments_flag=True
            )
            if not text:
                continue
            basename = os.path.basename(filepath)
            file_meta, file_ns = disk_cache.per_file_cached_by_content(
                self.mod_path,
                "events.metadata",
                filepath,
                text,
                lambda: _parse_event_metadata(text, basename),
            )
            meta.extend(file_meta)
            namespaces |= file_ns

        self._meta_cache = (meta, namespaces)
        return self._meta_cache

    def _get_random_event_ids(self) -> set:
        """Return event IDs referenced inside ``random_events`` blocks in on_actions.

        These events use ``mean_time_to_happen`` as their relative weight even
        when ``is_triggered_only = yes`` is set, so MTTH is not redundant.
        """
        if self._random_events_cache is not None:
            return self._random_events_cache

        # Lookup pass: must scan full repo even in staged mode, or staged
        # events lose their random_events MTTH exemption.
        files = self._collect_files(["common/on_actions/**/*.txt"], ignore_staged=True)
        ids: set = set()
        for filepath in files:
            text = FileOpener.open_text_file(
                filepath, lowercase=False, strip_comments_flag=True
            )
            if not text:
                continue
            ids.update(_extract_random_event_ids(text))

        self._random_events_cache = ids
        return ids

    def _get_fire_only_once_ids(self) -> set:
        """Return IDs of events declared ``fire_only_once = yes``.

        Lookup pass: must scan the full repo even in staged mode. Otherwise a
        staged caller that fires an existing fire_only_once event whose
        definition lives in an unstaged file drops out of the ID set, and the
        real in-loop / multi-caller bug commits silently.
        """
        if self._fire_only_once_ids_cache is not None:
            return self._fire_only_once_ids_cache

        files = self._collect_files(["events/**/*.txt"], ignore_staged=True)
        ids: set = set()
        for filepath in files:
            text = FileOpener.open_text_file(
                filepath, lowercase=False, strip_comments_flag=True
            )
            if not text:
                continue
            basename = os.path.basename(filepath)
            file_meta, _ = disk_cache.per_file_cached_by_content(
                self.mod_path,
                "events.metadata",
                filepath,
                text,
                lambda: _parse_event_metadata(text, basename),
            )
            ids.update(ev["id"] for ev in file_meta if ev["fire_only_once"])

        self._fire_only_once_ids_cache = ids
        return ids

    def validate_unsupported_title_desc(self):
        self._log_section(
            "Checking for events with unsupported title/desc combinations..."
        )

        events, paths = self._get_all_events()
        self.log(f"  Found {len(events)} events")
        results = []

        for line_type in ["title", "desc"]:
            block_pat = _TITLE_DESC_BLOCK_RE[line_type]
            inline_pat = _TITLE_DESC_INLINE_RE[line_type]

            for event in events:
                if block_pat.search(event) and inline_pat.search(event):
                    eid_match = _EVENT_ID_LITERAL_RE.findall(event)
                    eid = eid_match[0] if eid_match else "unknown"
                    results.append(
                        f"{eid} - {paths.get(event, 'unknown')} - invalid {line_type} (has both block and inline forms)"
                    )

        self._report(
            results,
            "✓ No unsupported title/desc combinations",
            "Events with invalid title/desc combinations (both block and inline forms):",
            Severity.ERROR,
            category="invalid-title-desc",
        )

    def validate_missing_triggered_only(self):
        self._log_section("Checking for events missing is_triggered_only = yes...")

        events, paths = self._get_all_events()
        self.log(f"  Found {len(events)} events")
        results = []

        for event in events:
            if "is_triggered_only = yes" not in event:
                event_id = _EVENT_ID_LITERAL_RE.findall(event)
                eid = event_id[0] if event_id else "unknown"
                filename = paths.get(event, "unknown")
                results.append(f"{eid} - {filename}")

        self._report(
            results,
            "✓ All events have is_triggered_only = yes",
            "Events missing is_triggered_only = yes:",
            Severity.ERROR,
            category="missing-triggered-only",
        )

    def validate_event_call_long_form(self):
        """Flag ``country_event = { id = X }`` (or ``news_event``/``state_event``)
        where the only argument is ``id``. Should use the shorthand
        ``country_event = X``.

        Scans all .txt files in the mod, not just events/, since events are
        called from focuses, decisions, scripted effects, etc.
        """
        self._log_section("Checking for redundant long-form event calls (id-only)...")

        txt_files = self._collect_files(
            ["common/**/*.txt", "events/**/*.txt", "history/**/*.txt"]
        )
        args_list = [(f, self.mod_path) for f in txt_files]
        all_results = self._pool_map(
            process_txt_for_long_form_events, args_list, chunksize=30
        )
        results = [r for file_res in all_results for r in file_res]

        self._report(
            results,
            "✓ No redundant long-form event calls found",
            "Long-form event calls with only id (use shorthand instead):",
        )

    def validate_missing_localisation(self):
        self._log_section("Checking for events with missing localisation keys...")

        events, paths = self._get_all_events()
        loc_keys = self._load_localisation_keys()
        self.log(f"  Found {len(events)} events, {len(loc_keys)} localisation keys")

        results = []
        for event in events:
            # Hidden events display no window, so their title/desc/option-name
            # loc is dead — never flag them for missing keys.
            if "hidden = yes" in event:
                continue
            eid_matches = _EVENT_ID_LITERAL_RE.findall(event)
            eid = eid_matches[0] if eid_matches else "unknown"
            filename = paths.get(event, "unknown")

            loc_refs = [k for k in _LOC_REF_PATTERN.findall(event) if "." in k]
            missing = [k for k in loc_refs if k not in loc_keys]
            for key in missing:
                results.append(f"{eid} - {filename}: missing loc key '{key}'")

        self._report(
            results,
            "✓ All event localisation keys are defined",
            "Events with missing localisation keys:",
            Severity.WARNING,
            category="missing-event-localisation",
        )

    def validate_triggered_only_unreferenced(self):
        self._log_section(
            "Checking for triggered-only events never referenced anywhere..."
        )

        events, paths = self._get_all_events()

        triggered_only_ids: Dict[str, str] = {}
        for event in events:
            if "is_triggered_only = yes" in event:
                matches = _EVENT_ID_LITERAL_RE.findall(event)
                if matches:
                    eid = matches[0]
                    triggered_only_ids[eid] = paths.get(event, "unknown")

        self.log(
            f"  Found {len(triggered_only_ids)} triggered-only events — scanning for references..."
        )

        # Reference scan: must cover the full repo even in staged mode — a
        # staged event's references usually live in unstaged files.
        txt_files = self._collect_files(
            ["common/**/*.txt", "events/**/*.txt", "history/**/*.txt"],
            ignore_staged=True,
        )
        tracked = frozenset(triggered_only_ids.keys())
        args_list = [(f, tracked) for f in txt_files]
        all_counts = self._pool_map(count_event_ids_in_file, args_list, chunksize=30)

        total_counts: Dict[str, int] = {eid: 0 for eid in tracked}
        for file_counts in all_counts:
            for eid, count in file_counts.items():
                total_counts[eid] = total_counts.get(eid, 0) + count

        # Namespaces dispatched via runtime-interpolated IDs (e.g. UN.[ID],
        # MD_cyber.1[TYPE]) never appear as literal tokens — exempt them.
        dyn_ns_lists = self._pool_map(
            scan_dynamic_event_namespaces, args_list, chunksize=30
        )
        dynamic_namespaces: Set[str] = set()
        for s in dyn_ns_lists:
            dynamic_namespaces.update(s)

        # The definition itself contributes 1 occurrence (id = X inside the event block).
        # Anything > 1 means it's referenced somewhere else.
        results = []
        for eid in sorted(triggered_only_ids):
            if total_counts.get(eid, 0) > 1:
                continue
            last_dot = eid.rfind(".")
            ns = eid[:last_dot] if last_dot >= 0 else eid
            if ns in dynamic_namespaces:
                continue
            results.append(f"{eid} - {triggered_only_ids[eid]}")

        self._report(
            results,
            "✓ All triggered-only events are referenced somewhere",
            "Triggered-only events with no references found:",
            Severity.WARNING,
            category="unreferenced-triggered-only",
        )

    def validate_mtth_triggered_only(self):
        """Flag events with both mean_time_to_happen and is_triggered_only.

        MTTH only applies to auto-firing events. On triggered-only events
        it does nothing and the engine logs a warning.

        Exception: events fired through ``random_events`` blocks in on_actions
        use MTTH as their selection weight, so the combination is intentional
        there.
        """
        self._log_section(
            "Checking for mean_time_to_happen on triggered-only events..."
        )

        meta, _ = self._get_event_metadata()
        random_event_ids = self._get_random_event_ids()
        results = []

        for ev in meta:
            if not (ev["has_mtth"] and ev["is_triggered_only"]):
                continue
            if ev["id"] in random_event_ids:
                continue
            results.append(f"{ev['id']} - {ev['file']}")

        self._report(
            results,
            "✓ No triggered-only events with mean_time_to_happen",
            "Events with mean_time_to_happen AND is_triggered_only (MTTH does nothing — remove one):",
            Severity.WARNING,
            category="mtth-triggered-only",
        )

    def validate_hidden_event_options(self):
        """Flag hidden events that still carry option blocks.

        A hidden event shows no UI, so its option effects should run from
        immediate = { } instead. When two or more options exist only the
        first auto-fires — the rest are dead code.
        """
        self._log_section("Checking hidden events for option blocks...")

        meta, _ = self._get_event_metadata()
        results = []

        for ev in meta:
            if not ev["is_hidden"] or ev["option_count"] == 0:
                continue
            count = ev["option_count"]
            detail = f"{count} option block{'s' if count != 1 else ''}"
            if count >= 2:
                detail += " (only the first auto-fires — the rest are dead code)"
            results.append(f"{ev['id']} - {ev['file']}: {detail}")

        self._report(
            results,
            "✓ No hidden events with option blocks",
            "Hidden events with option blocks (move effects into immediate = { }):",
            Severity.WARNING,
            category="hidden-event-has-options",
        )

    def validate_hidden_event_localisation(self):
        """Flag hidden events that declare a title or desc field.

        A hidden event shows no window, so a ``title`` / ``desc`` field in its
        own body is dead — the field and its loc keys should be removed.

        Only fields declared in the event's own body are flagged. A loc key
        that merely shares the event's ID prefix is NOT flagged: prefixes are
        sometimes reused by a separate visible event (e.g. the visible
        ``investments_event.10`` displays ``investments_event.1.t``), so the
        hidden event ``investments_event.1`` owning no title field is correct.
        """
        self._log_section("Checking hidden events for pointless localisation...")

        meta, _ = self._get_event_metadata()
        loc_keys = self._load_localisation_keys()
        results = []

        for ev in meta:
            if not ev["is_hidden"] or not ev["title_desc_refs"]:
                continue
            # Only flag when the declared title/desc actually resolves to a real
            # loc key. A hidden event declaring `title = foo.t` with no `foo.t`
            # in any .yml has nothing to remove, so it is not a finding.
            real = [k for k in ev["title_desc_refs"] if k in loc_keys]
            if not real:
                continue
            detail = "; ".join(real)
            results.append(f"{ev['id']} - {ev['file']}: {detail}")

        self._report(
            results,
            "✓ No hidden events with pointless localisation",
            "Hidden events with localisation keys (hidden events display nothing — remove these keys):",
            Severity.WARNING,
            category="hidden-event-localisation",
        )

    def validate_duplicate_event_ids(self):
        """Flag events that share the same ID.

        When two events have the same ID, the second definition overwrites
        the first. This is almost always a copy-paste bug.
        """
        self._log_section("Checking for duplicate event IDs...")

        meta, _ = self._get_event_metadata()
        seen: Dict[str, str] = {}
        results = []

        for ev in meta:
            eid = ev["id"]
            if eid in seen:
                results.append(f"{eid} - defined in {seen[eid]} and {ev['file']}")
            else:
                seen[eid] = ev["file"]

        self._report(
            results,
            "✓ No duplicate event IDs",
            "Duplicate event IDs (second definition overwrites the first):",
            category="duplicate-event-id",
        )

    def validate_namespace_mismatch(self):
        """Flag events whose ID namespace is not declared via add_namespace.

        Every event ID has the format namespace.number. If the namespace
        isn't declared with add_namespace in any event file, the event ID
        is a malformed token and the event will silently not work in-game.
        """
        self._log_section("Checking event IDs against declared namespaces...")

        meta, namespaces = self._get_event_metadata()
        self.log(f"  Found {len(namespaces)} declared namespaces, {len(meta)} events")
        results = []

        for ev in meta:
            eid = ev["id"]
            last_dot = eid.rfind(".")
            if last_dot < 0:
                continue
            ns = eid[:last_dot]
            if ns not in namespaces:
                results.append(f"{eid} - {ev['file']} (namespace '{ns}' not declared)")

        self._report(
            results,
            "✓ All event namespaces are declared",
            "Events with undeclared namespace (add_namespace missing — event will silently fail):",
            category="namespace-mismatch",
        )

    def validate_event_pictures(self):
        """Flag events whose `picture = GFX_x` sprite is not MD-defined.

        An event's picture resolves directly to the named sprite. MD events must
        not rely on vanilla event pictures, so this checks against the mod's own
        interface/*.gfx only (no vanilla) — which also keeps it accurate in CI,
        where the vanilla install is absent. A missing sprite renders a blank
        picture box, so it is an error.
        """
        self._log_section("Checking for events with missing pictures...")

        files = self._collect_files(["events/**/*.txt"])
        if not files:
            self.log("  No event files in scope — skipping")
            return

        # Built sequentially (no pool_map): scanning ~150 .gfx files takes well
        # under a second, and a sequential read can't be left empty by a pool
        # worker that fails to start under the 'spawn' start method.
        sprites = build_sprite_index(
            self.mod_path,
            gfx_only=True,
            include_vanilla=False,
        )
        # Sanity guard: the mod defines tens of thousands of GFX sprites. If the
        # index comes back near-empty, sprite definitions failed to load (wrong
        # path, unreadable interface/*.gfx, a broken pool worker) — flagging
        # every picture as missing would be thousands of false errors. Skip
        # loudly instead so a load failure can't break CI or a commit.
        if len(sprites) < 1000:
            self.log(
                f"  Only {len(sprites)} GFX sprites loaded from "
                f"{os.path.join(self.mod_path, 'interface')}/*.gfx — sprite "
                "definitions did not load; skipping the picture check",
                "warning",
            )
            return
        refs = self._pool_map(_extract_event_pictures, files)

        results: List[str] = []
        seen: Set[Tuple[str, str, int]] = set()
        for sub in refs:
            for sprite, filename, line in sub:
                if sprite in sprites:
                    continue
                key = (sprite, filename, line)
                if key in seen:
                    continue
                seen.add(key)
                results.append(f"{os.path.basename(filename)}:{line} - {sprite}")

        self._report(
            sorted(results),
            "✓ All event pictures are MD-defined",
            "Events with missing pictures (picture sprite not defined in the mod's interface/*.gfx; MD must not use vanilla event pictures):",
            severity=Severity.ERROR,
            category="missing-event-picture",
        )

    def validate_fire_only_once_in_loop(self):
        """Flag fire_only_once events fired inside an every_*/for_each_* iterator.

        A fire_only_once event sets a one-shot flag on first firing, so inside
        an iterating scope (every_country / every_state / for_each_scope_loop
        / etc.) only the first recipient actually gets it -- the rest of the
        iterations silently no-op. ``random_country`` / ``random_state`` pick a
        single scope by design and are not iterators, so calls nested only in
        them are not flagged.
        """
        self._log_section(
            "Checking for fire_only_once events fired inside iterators..."
        )

        fire_only_once_ids = frozenset(self._get_fire_only_once_ids())
        if not fire_only_once_ids:
            self.log("  No fire_only_once events defined — skipping")
            self._report(
                [],
                "✓ No fire_only_once events fired inside iterators",
                "fire_only_once events fired inside iterators (only the first recipient gets it):",
                category="fire-only-once-in-loop",
            )
            return

        txt_files = self._collect_files(
            ["common/**/*.txt", "events/**/*.txt", "history/**/*.txt"]
        )
        args_list = [(f, fire_only_once_ids, self.mod_path) for f in txt_files]
        all_results = self._pool_map(
            scan_fire_only_once_in_loop, args_list, chunksize=30
        )
        results = [r for file_res in all_results for r in file_res]

        # WARNING until the 11-site pre-existing backlog is cleared, then ERROR.
        self._report(
            results,
            "✓ No fire_only_once events fired inside iterators",
            "fire_only_once events fired inside every_*/for_each_* iterators"
            " (only the first recipient gets it; drop fire_only_once or fire"
            " the event outside the loop):",
            Severity.WARNING,
            category="fire-only-once-in-loop",
        )

    def run_validations(self):
        self.validate_unsupported_title_desc()
        self.validate_missing_triggered_only()
        self.validate_event_call_long_form()
        self.validate_triggered_only_unreferenced()
        self.validate_missing_localisation()
        self.validate_mtth_triggered_only()
        self.validate_hidden_event_options()
        self.validate_hidden_event_localisation()
        self.validate_duplicate_event_ids()
        self.validate_namespace_mismatch()
        self.validate_event_pictures()
        self.validate_fire_only_once_in_loop()


if __name__ == "__main__":
    run_validator_main(Validator, "Validate events in Millennium Dawn mod")
