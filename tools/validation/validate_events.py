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
# _EVENT_TYPE_PATTERN.
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


def _read_cleaned_text(filename: str, *, skip: bool = True) -> Optional[str]:
    """Read a mod file and strip ``#`` comments, or return ``None`` on failure."""
    if skip and _should_skip(filename):
        return None
    try:
        text = Path(filename).read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return None
    return re.sub(r"#[^\n]*", "", text)


def _extract_event_pictures(filename: str) -> List[Tuple[str, str, int]]:
    """Pool worker: return (sprite, filename, line) for each event picture ref."""
    text = _read_cleaned_text(filename)
    if text is None:
        return []
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
    cleaned = _read_cleaned_text(filename)
    if cleaned is None:
        return {}
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


# Every way a script fires an event: the short form `country_event = foo.1` and
# the block form `country_event = { id = foo.1 days = 3 }`. The block form is
# matched by finding the keyword and then the first `id =` inside its braces, so
# `days`/`hours`/`random_days` in any order are handled.
_EVENT_FIRE_SHORT_RE = re.compile(
    r"\b(" + _EVENT_CALL_ALT + r")\s*=\s*([A-Za-z_][\w.]*)"
)
_EVENT_FIRE_BLOCK_RE = re.compile(r"\b(" + _EVENT_CALL_ALT + r")\s*=\s*\{([^{}]*)\}")
_FIRE_ID_RE = re.compile(r"\bid\s*=\s*([A-Za-z_][\w.]*)")


# Keys that only ever appear in an event definition, never in a fire. Used to
# tell `country_event = { id = x title = ... }` (a definition) from
# `country_event = { id = x days = 3 }` (a fire).
_DEFINITION_ONLY_RE = re.compile(
    r"\b(?:title|desc|picture|is_triggered_only|fire_only_once|hidden|option|"
    r"immediate|major|trigger|mean_time_to_happen|timeout_days)\s*="
)
_EVENT_BLOCK_OPEN_RE = re.compile(r"\b(" + _EVENT_CALL_ALT + r")\s*=\s*\{")
_REVERSED_EVENT_CALL_RE = re.compile(
    r"\b(event_(?:country|news|state|unit_leader|operative_leader))\s*=\s*"
    r"(?:\{[^{}]*?\bid\s*=\s*([A-Za-z_][\w.]*)|([A-Za-z_][\w.]*))"
)
_MISSING_EVENT_CALL_EQUALS_RE = re.compile(
    r"\b(" + _EVENT_CALL_ALT + r")\s+\{[^{}]*?\bid\s*=\s*([A-Za-z_][\w.]*)"
)


def _matching_brace(text: str, open_pos: int) -> int:
    depth = 0
    for i in range(open_pos, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i
    return -1


def _iter_typed_event_bodies(cleaned: str):
    """Yield typed definitions using brace matching so indentation is irrelevant."""
    for m in _EVENT_BLOCK_OPEN_RE.finditer(cleaned):
        ob = cleaned.index("{", m.end() - 1)
        end = _matching_brace(cleaned, ob)
        if end == -1:
            continue
        body = cleaned[ob + 1 : end]
        idm = _FIRE_ID_RE.search(body)
        if idm and _DEFINITION_ONLY_RE.search(body):
            yield idm.group(1), m.group(1), body, m.start()


def _iter_event_bodies(cleaned: str):
    """Yield (event_id, body, match_start) for defined events."""
    for eid, _event_type, body, start in _iter_typed_event_bodies(cleaned):
        yield eid, body, start


def scan_event_definitions(args: Tuple[str, frozenset]) -> Set[str]:
    """Pool worker: event IDs *defined* in one file."""
    filename = args[0]
    cleaned = _read_cleaned_text(filename, skip=False)
    if cleaned is None:
        return set()
    return {eid for eid, _body, _start in _iter_event_bodies(cleaned)}


def scan_event_definition_types(
    args: Tuple[str, frozenset],
) -> List[Tuple[str, str]]:
    """Pool worker: event IDs and their declaration keywords."""
    filename = args[0]
    cleaned = _read_cleaned_text(filename, skip=False)
    if cleaned is None:
        return []
    return [
        (eid, event_type)
        for eid, event_type, _body, _start in _iter_typed_event_bodies(cleaned)
    ]


def _is_literal_id(eid: str, after: str) -> bool:
    """False when the ID is assembled at runtime rather than written out.

    `UN.[ID]` matches as `UN.` and `MD_cyber.1[TYPE]` as `MD_cyber.1`, so a
    trailing dot or a following `[` both mean the ID is interpolated.
    """
    return "." in eid and not eid.endswith(".") and not after.startswith("[")


def _iter_typed_fires(text: str):
    """Yield (event_id, call_keyword, match_start) for literal event fires."""
    for m in _EVENT_FIRE_SHORT_RE.finditer(text):
        if _is_literal_id(m.group(2), text[m.end() : m.end() + 1]):
            yield m.group(2), m.group(1), m.start()
    for m in _EVENT_FIRE_BLOCK_RE.finditer(text):
        idm = _FIRE_ID_RE.search(m.group(2))
        if idm and _is_literal_id(idm.group(1), m.group(2)[idm.end() : idm.end() + 1]):
            yield idm.group(1), m.group(1), m.start()


def _iter_fired_ids(text: str):
    """Yield (event_id, match_start) for every literal event fire in `text`."""
    for eid, _call_type, pos in _iter_typed_fires(text):
        yield eid, pos


def scan_event_fires(args: Tuple[str, frozenset]) -> List[Tuple[str, str, int]]:
    """Pool worker: every event ID fired from one file, as (id, file, line).

    Only literal IDs are returned. An ID assembled at runtime (`UN.[ID]`) has no
    literal form to resolve, so it is skipped rather than guessed at.
    """
    filename = args[0]
    cleaned = _read_cleaned_text(filename)
    if cleaned is None:
        return []

    return [
        (eid, filename, cleaned.count("\n", 0, pos) + 1)
        for eid, pos in _iter_fired_ids(cleaned)
    ]


def scan_typed_event_fires(
    args: Tuple[str, frozenset],
) -> List[Tuple[str, str, str, int]]:
    """Pool worker: literal event fires with their call keywords."""
    filename = args[0]
    cleaned = _read_cleaned_text(filename)
    if cleaned is None:
        return []
    return [
        (eid, call_type, filename, cleaned.count("\n", 0, pos) + 1)
        for eid, call_type, pos in _iter_typed_fires(cleaned)
    ]


def scan_invalid_event_calls(
    args: Tuple[str, frozenset],
) -> List[Tuple[str, str, str, str, int]]:
    """Pool worker: reversed keywords and event calls missing ``=``."""
    filename = args[0]
    if _should_skip(filename):
        return []
    try:
        text = Path(filename).read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return []
    cleaned = blank_quoted_strings(strip_comments(text))
    results: List[Tuple[str, str, str, str, int]] = []
    for m in _REVERSED_EVENT_CALL_RE.finditer(cleaned):
        results.append(
            (
                "reversed",
                m.group(1),
                m.group(2) or m.group(3),
                filename,
                cleaned.count("\n", 0, m.start()) + 1,
            )
        )
    for m in _MISSING_EVENT_CALL_EQUALS_RE.finditer(cleaned):
        results.append(
            (
                "missing-equals",
                m.group(1),
                m.group(2),
                filename,
                cleaned.count("\n", 0, m.start()) + 1,
            )
        )
    results.sort(key=lambda result: result[-1])
    return results


def scan_dynamic_event_namespaces(args: Tuple[str, frozenset]) -> Set[str]:
    """Pool worker: namespaces fired via string-interpolated event IDs in a file.

    Any triggered-only event in a returned namespace is reachable through dynamic
    dispatch and must not be reported as unreferenced.
    """
    filename = args[0]
    cleaned = _read_cleaned_text(filename)
    if cleaned is None:
        return set()
    return set(_DYNAMIC_EVENT_NS_PATTERN.findall(cleaned))


# --- date-gated events and the event fire graph ---
#
# A `date >` lower bound anchors an event to a point in history. A `date <`
# bound on its own is an expiry guard on a chain event and says nothing about
# scheduling, so only the lower bound is matched here.
_DATE_LOWER_BOUND_RE = re.compile(r"\bdate\s*>\s*\d{4}\.\d{1,2}\.\d{1,2}")
_TRIGGER_OPEN_RE = re.compile(r"\btrigger\s*=\s*\{")


def _event_trigger_body(body: str) -> Optional[str]:
    """Return the event's own ``trigger = { … }`` body, or None.

    Walks brace depth instead of anchoring on ``^\\ttrigger``: several event
    files indent their definitions one tab deeper than the norm, and the
    triggers nested in `option` / `immediate` / `mean_time_to_happen` blocks
    are not the event's own gate.
    """
    depth = 0
    pos = 0
    for m in _TRIGGER_OPEN_RE.finditer(body):
        seg = body[pos : m.start()]
        depth += seg.count("{") - seg.count("}")
        pos = m.start()
        if depth != 0:
            continue
        ob = body.index("{", m.end() - 1)
        end = _matching_brace(body, ob)
        return None if end == -1 else body[ob + 1 : end]
    return None


def scan_date_gated_events(args: Tuple[str, frozenset]) -> List[Tuple[str, str, int]]:
    """Pool worker: events whose own trigger carries a `date >` bound.

    Returns (id, file, line) so a finding can point at the definition.
    """
    filename = args[0]
    cleaned = _read_cleaned_text(filename)
    if cleaned is None:
        return []

    out: List[Tuple[str, str, int]] = []
    for eid, body, start in _iter_event_bodies(cleaned):
        trigger = _event_trigger_body(body)
        if trigger and _DATE_LOWER_BOUND_RE.search(trigger):
            out.append((eid, filename, cleaned.count("\n", 0, start) + 1))
    return out


def scan_event_fire_graph(args: Tuple[str, frozenset]) -> List[Tuple[str, str]]:
    """Pool worker: (parent_id, child_id) for every event fired from an event.

    Lets a chain event inherit whatever schedules its parent, so only the head
    of a chain needs a scheduling entry.
    """
    filename = args[0]
    cleaned = _read_cleaned_text(filename)
    if cleaned is None:
        return []

    out: List[Tuple[str, str]] = []
    for parent, body, _start in _iter_event_bodies(cleaned):
        for child, _pos in _iter_fired_ids(body):
            if child != parent:
                out.append((parent, child))
    return out


# Where MD schedules its historical events from.
_YEARLY_EFFECTS_REL = "common/scripted_effects/00_yearly_effects.txt"

# Fire sources where a date bound is an availability window rather than a
# missing schedule: the player decides when a focus completes or a decision is
# taken, so the event has no scheduled moment to belong to.
_PLAYER_DRIVEN_FIRE_DIRS = ("common/national_focus/", "common/decisions/")


def _is_scheduled_chain(
    eid: str, scheduled: Set[str], parents: Dict[str, Set[str]]
) -> bool:
    """True if `eid` or any ancestor that fires it is scheduled."""
    seen = {eid}
    stack = [eid]
    while stack:
        current = stack.pop()
        if current in scheduled:
            return True
        for parent in parents.get(current, ()):
            if parent not in seen:
                seen.add(parent)
                stack.append(parent)
    return False


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


# A `random = { chance = N ... }` block: the on_action poll that emulates MTTH.
# `\brandom\s*=\s*\{` cannot match `random_country` / `random_list` /
# `random_events` (those carry `_` after `random`, not `=`), so only the plain
# chance-rolled poll is matched.
_RANDOM_BLOCK_PATTERN = re.compile(r"\brandom\s*=\s*\{")
_CHANCE_PATTERN = re.compile(r"\bchance\s*=")


def scan_probability_rolled_fires(args: Tuple[str, frozenset]) -> Set[str]:
    """Pool worker: event IDs fired inside a `random = { chance = N ... }` poll.

    A chance-rolled on_action poll emulates MTTH: each tick it rolls a chance
    and fires the event when it wins. The event has no deterministic yearly
    slot, so the date-gated scheduling check must not flag it as dead content.
    """
    filename = args[0]
    if _should_skip(filename):
        return set()
    try:
        text = Path(filename).read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return set()
    cleaned = re.sub(r"#[^\n]*", "", text)
    ids: set = set()
    for m in _RANDOM_BLOCK_PATTERN.finditer(cleaned):
        body, _ = extract_block_from_text(cleaned, m.end() - 1)
        if _CHANCE_PATTERN.search(body):
            for eid, _pos in _iter_fired_ids(body):
                ids.add(eid)
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

        meta.append(
            {
                "id": id_match.group(1) if id_match else None,
                "body": body,
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
        self._meta_cache: Optional[Tuple[List[dict], set]] = None
        self._random_events_cache: Optional[set] = None
        self._probability_rolled_cache: Optional[set] = None
        self._fire_only_once_ids_cache: Optional[set] = None
        self._fire_scan_args_cache: Optional[List[Tuple[str, frozenset]]] = None
        self._fires_cache: Optional[List[Tuple[str, str, int]]] = None
        self._typed_fires_cache: Optional[List[Tuple[str, str, str, int]]] = None
        self._definition_types_cache: Optional[Dict[str, str]] = None

    def _get_event_metadata(self) -> Tuple[List[dict], set]:
        """Parse all event files and return (event_metadata_list, declared_namespaces).

        Each metadata dict has: id (or None for malformed blocks), type, file,
        is_hidden, is_triggered_only, fire_only_once, has_mtth, option_count,
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

    def _rel_posix(self, filename: str) -> str:
        """Mod-relative path with forward slashes, so matching works on Windows."""
        return Path(os.path.relpath(filename, self.mod_path)).as_posix()

    def _get_fire_scan_args(self) -> List[Tuple[str, frozenset]]:
        """Pool args for every file that can fire an event.

        Fires live all over the mod, not just in events/. Full repo even in
        staged mode: a staged caller's target usually sits elsewhere.
        """
        if self._fire_scan_args_cache is None:
            self._fire_scan_args_cache = [
                (f, frozenset())
                for f in self._collect_files(
                    ["common/**/*.txt", "events/**/*.txt", "history/**/*.txt"],
                    ignore_staged=True,
                )
            ]
        return self._fire_scan_args_cache

    def _get_scoped_fire_scan_args(self) -> List[Tuple[str, frozenset]]:
        """Pool args for callers in the current staged or full validation scope."""
        return [
            (f, frozenset())
            for f in self._collect_files(
                ["common/**/*.txt", "events/**/*.txt", "history/**/*.txt"]
            )
        ]

    def _get_event_fires(self) -> List[Tuple[str, str, int]]:
        """Every literal event fire in the mod as (event_id, file, line)."""
        if self._fires_cache is not None:
            return self._fires_cache
        fires: List[Tuple[str, str, int]] = []
        for result in self._pool_map(
            scan_event_fires, self._get_fire_scan_args(), chunksize=30
        ):
            fires.extend(result)
        self._fires_cache = fires
        return fires

    def _get_typed_event_fires(self) -> List[Tuple[str, str, str, int]]:
        """Every literal event fire with its call keyword."""
        if self._typed_fires_cache is not None:
            return self._typed_fires_cache
        fires: List[Tuple[str, str, str, int]] = []
        for result in self._pool_map(
            scan_typed_event_fires, self._get_fire_scan_args(), chunksize=30
        ):
            fires.extend(result)
        self._typed_fires_cache = fires
        return fires

    def _get_event_definition_types(self) -> Dict[str, str]:
        """Return event declaration keywords from the full events tree."""
        if self._definition_types_cache is not None:
            return self._definition_types_cache
        definitions: Dict[str, str] = {}
        event_files = self._collect_files(["events/**/*.txt"], ignore_staged=True)
        for result in self._pool_map(
            scan_event_definition_types,
            [(f, frozenset()) for f in event_files],
            chunksize=20,
        ):
            definitions.update(result)
        self._definition_types_cache = definitions
        return definitions

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

    def _get_probability_rolled_ids(self) -> set:
        """Return event IDs fired from chance-rolled on_action polls.

        A `random = { chance = N ... }` poll emulates MTTH: each tick it rolls
        a chance and fires the event when it wins, so the event has no
        deterministic yearly slot. The date-gated scheduling check must not
        flag such an event as dead content.
        """
        if self._probability_rolled_cache is not None:
            return self._probability_rolled_cache

        # Lookup pass: must scan full repo even in staged mode, mirroring
        # `_get_random_event_ids`.
        files = self._collect_files(["common/on_actions/**/*.txt"], ignore_staged=True)
        ids: set = set()
        for result in self._pool_map(
            scan_probability_rolled_fires,
            [(f, frozenset()) for f in files],
            chunksize=30,
        ):
            ids.update(result)

        self._probability_rolled_cache = ids
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

        meta, _ = self._get_event_metadata()
        self.log(f"  Found {len(meta)} events")
        results = []

        for ev in meta:
            eid = ev["id"] or "unknown"
            for line_type in ("title", "desc"):
                if _TITLE_DESC_BLOCK_RE[line_type].search(
                    ev["body"]
                ) and _TITLE_DESC_INLINE_RE[line_type].search(ev["body"]):
                    results.append(
                        f"{eid} - {ev['file']} - invalid {line_type} (has both block and inline forms)"
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

        meta, _ = self._get_event_metadata()
        self.log(f"  Found {len(meta)} events")
        results = [
            f"{ev['id'] or 'unknown'} - {ev['file']}"
            for ev in meta
            if not ev["is_triggered_only"]
        ]

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

        meta, _ = self._get_event_metadata()
        loc_keys = self._load_localisation_keys()
        self.log(f"  Found {len(meta)} events, {len(loc_keys)} localisation keys")

        results = []
        for ev in meta:
            # Hidden events display no window, so their title/desc/option-name
            # loc is dead — never flag them for missing keys.
            if ev["is_hidden"]:
                continue
            eid = ev["id"] or "unknown"
            for key in _LOC_REF_PATTERN.findall(ev["body"]):
                if "." in key and key not in loc_keys:
                    results.append(f"{eid} - {ev['file']}: missing loc key '{key}'")

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

        meta, _ = self._get_event_metadata()
        triggered_only_ids: Dict[str, str] = {
            ev["id"]: ev["file"]
            for ev in meta
            if ev["id"] is not None and ev["is_triggered_only"]
        }

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

    def validate_date_gated_scheduling(self):
        """Flag date-anchored events nothing schedules from the yearly effects.

        MD fires its historical events from
        `common/scripted_effects/00_yearly_effects.txt`
        (`MD_event_on_startup_events` for 2000, `trigger_year_YYYY_events`
        after) and uses the event's own `date >` check only as a guard. An
        event that carries the guard but never gets a scheduling entry is dead
        content: it is triggered-only, so nothing ever fires it.

        A `date <` bound alone is an expiry guard on a chain event and says
        nothing about scheduling, so only `date >` counts. Chain events inherit
        whatever schedules an ancestor, focus/decision fires are player-driven
        availability windows, `random_events` pools weight their events by
        MTTH, and chance-rolled on_action polls emulate MTTH. All are exempt.
        """
        self._log_section(
            "Checking date-gated events are scheduled from the yearly effects..."
        )

        # Staged-aware on purpose: on commit, only report on the event files
        # actually being committed.
        gated_args = [
            (f, frozenset()) for f in self._collect_files(["events/**/*.txt"])
        ]
        gated: List[Tuple[str, str, int]] = []
        for result in self._pool_map(scan_date_gated_events, gated_args, chunksize=10):
            gated.extend(result)
        self.log(f"  Found {len(gated)} events with a date > guard")

        results = []
        if gated:
            results = self._unscheduled_date_gated(gated)
            if results is None:
                # Scheduling file missing: logged and skipped, nothing to report.
                return

        self._report(
            results,
            "✓ Every date-gated event is scheduled from the yearly effects",
            f"Date-gated events missing a {_YEARLY_EFFECTS_REL} entry:",
            Severity.ERROR,
            category="date-gated-not-scheduled",
        )

    def _unscheduled_date_gated(
        self, gated: List[Tuple[str, str, int]]
    ) -> Optional[List[str]]:
        """Findings for `gated`, or None when the scheduling file is missing."""
        sources: Dict[str, Set[str]] = {}
        for eid, filename, _line in self._get_event_fires():
            sources.setdefault(eid, set()).add(self._rel_posix(filename))
        scheduled = {
            eid for eid, rels in sources.items() if _YEARLY_EFFECTS_REL in rels
        }
        if not scheduled:
            # Without the scheduling file every date-gated event would be
            # reported, so a rename must skip the check rather than flood it.
            self.log(f"  {_YEARLY_EFFECTS_REL} schedules nothing, skipping")
            return None

        # Lookup pass: a staged event's parent almost always lives elsewhere.
        graph_args: List[Tuple[str, frozenset]] = [
            (f, frozenset())
            for f in self._collect_files(["events/**/*.txt"], ignore_staged=True)
        ]
        parents: Dict[str, Set[str]] = {}
        for pairs in self._pool_map(scan_event_fire_graph, graph_args, chunksize=10):
            for parent, child in pairs:
                parents.setdefault(child, set()).add(parent)

        results = []
        random_events_ids = self._get_random_event_ids()
        probability_rolled_ids = self._get_probability_rolled_ids()
        for eid, filename, line in sorted(gated):
            if _is_scheduled_chain(eid, scheduled, parents):
                continue
            if eid in random_events_ids:
                # A `random_events` pool weights its events by MTTH; the pool
                # is the schedule.
                continue
            if eid in probability_rolled_ids:
                # A chance-rolled on_action poll emulates MTTH and has no
                # deterministic yearly slot.
                continue
            rels = sources.get(eid, set())
            if any(r.startswith(d) for r in rels for d in _PLAYER_DRIVEN_FIRE_DIRS):
                continue
            origin = ", ".join(sorted(rels)) if rels else "nothing"
            results.append(
                f"{eid} - {self._rel_posix(filename)}:{line} has a date > guard but "
                f"nothing schedules it from {_YEARLY_EFFECTS_REL} "
                f"(fired from: {origin})"
            )
        return results

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
            if ev["id"] is None:
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
            event_id = ev["id"] or "unknown"
            results.append(f"{event_id} - {ev['file']}: {detail}")

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
            event_id = ev["id"] or "unknown"
            results.append(f"{event_id} - {ev['file']}: {detail}")

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
            if eid is None:
                continue
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
            if eid is None:
                continue
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

    def validate_invalid_event_calls(self):
        """Flag malformed event effects that the engine cannot execute."""
        self._log_section("Checking event call syntax...")

        results = []
        for matches in self._pool_map(
            scan_invalid_event_calls,
            self._get_scoped_fire_scan_args(),
            chunksize=30,
        ):
            for kind, keyword, eid, filename, line in matches:
                if kind == "reversed":
                    message = f"{keyword} = {eid} - use an event effect keyword"
                else:
                    message = f"{keyword} {{ id = {eid} }} - missing '='"
                results.append(
                    (message, os.path.relpath(filename, self.mod_path), line)
                )

        self._report(
            results,
            "✓ Event call syntax is valid",
            "Malformed event calls (silently do nothing or break parsing):",
            Severity.ERROR,
            category="malformed-event-fire",
        )

    def validate_event_fire_types(self):
        """Flag fires whose effect keyword does not match the declaration."""
        self._log_section("Checking event call types match their declarations...")

        definitions = self._get_event_definition_types()
        results = []
        for eid, call_type, filename, line in self._get_typed_event_fires():
            expected = definitions.get(eid)
            if expected is None or expected == call_type:
                continue
            rel = os.path.relpath(filename, self.mod_path)
            results.append(
                (
                    f"{eid} - fired with {call_type}, defined as {expected}",
                    rel,
                    line,
                )
            )

        self._report(
            results,
            "✓ Event call types match their declarations",
            "Event calls using the wrong effect type:",
            Severity.ERROR,
            category="event-fire-type-mismatch",
        )

    def validate_undefined_event_fires(self):
        """Flag scripts that fire an event ID no event file defines.

        MD sets `replace_path = "events"`, so vanilla events are not loaded and
        every fired ID has to resolve inside the mod. A fire at an undefined ID
        compiles fine and silently does nothing, which is how a whole chain can
        rot after its events are renamed or commented out.

        IDs assembled at runtime (`country_event = UN.[ID]`) never appear as a
        literal token, so any namespace dispatched that way is exempt.
        """
        self._log_section("Checking event fires resolve to a defined event...")

        args_list = self._get_fire_scan_args()

        # The definition scan must also cover the full repo in staged mode: a
        # staged caller's target event almost always lives in an unstaged file.
        event_files = [
            (f, frozenset())
            for f in self._collect_files(["events/**/*.txt"], ignore_staged=True)
        ]
        defined: Set[str] = set()
        for s in self._pool_map(scan_event_definitions, event_files, chunksize=10):
            defined.update(s)
        self.log(f"  Found {len(defined)} defined event IDs")

        dynamic_namespaces: Set[str] = set()
        for s in self._pool_map(scan_dynamic_event_namespaces, args_list, chunksize=30):
            dynamic_namespaces.update(s)

        seen: Dict[str, Tuple[str, int]] = {}
        for eid, filename, line in self._get_event_fires():
            if eid in defined or eid in seen:
                continue
            if eid[: eid.rfind(".")] in dynamic_namespaces:
                continue
            seen[eid] = (filename, line)

        results = []
        for eid in sorted(seen):
            filename, line = seen[eid]
            rel = os.path.relpath(filename, self.mod_path)
            results.append(f"{eid} - fired from {rel}:{line}, no event defines it")

        self._report(
            results,
            "✓ Every fired event ID resolves to a defined event",
            "Fires at undefined event IDs (silently do nothing):",
            category="undefined-event-fire",
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

        # ERROR: the 11-site pre-existing backlog was cleared.
        self._report(
            results,
            "✓ No fire_only_once events fired inside iterators",
            "fire_only_once events fired inside every_*/for_each_* iterators"
            " (only the first recipient gets it; drop fire_only_once or fire"
            " the event outside the loop):",
            Severity.ERROR,
            category="fire-only-once-in-loop",
        )

    def run_validations(self):
        self.validate_unsupported_title_desc()
        self.validate_missing_triggered_only()
        self.validate_event_call_long_form()
        self.validate_triggered_only_unreferenced()
        self.validate_date_gated_scheduling()
        self.validate_missing_localisation()
        self.validate_mtth_triggered_only()
        self.validate_hidden_event_options()
        self.validate_hidden_event_localisation()
        self.validate_duplicate_event_ids()
        self.validate_namespace_mismatch()
        self.validate_invalid_event_calls()
        self.validate_event_fire_types()
        self.validate_undefined_event_fires()
        self.validate_event_pictures()
        self.validate_fire_only_once_in_loop()


if __name__ == "__main__":
    run_validator_main(Validator, "Validate events in Millennium Dawn mod")
