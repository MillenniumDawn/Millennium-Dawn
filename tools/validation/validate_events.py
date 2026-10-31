#!/usr/bin/env python3
"""Validate event definitions in Millennium Dawn.

Based on Kaiserreich Autotests by Pelmen (https://github.com/Pelmen323),
adapted for Millennium Dawn with multiprocessing.
"""

import os
import re
import sys
from collections import Counter
from decimal import Decimal
from functools import partial
from pathlib import Path
from typing import Callable, Dict, Iterable, Iterator, List, Optional, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "linting"))

import disk_cache
from check_common_mistakes import _iter_event_log_mismatches
from image_size import read_image_size
from shared_utils import (
    IS_AI_NO_RE,
    blank_quoted_strings,
    extract_block_from_text,
    find_unquoted_brace_close,
    first_flat_match,
    get_staged_files,
    iter_statements,
    strip_comments,
    strip_inline_comment,
    validation_config,
)
from shared_utils import MODIFIER_OPEN_RE as _AI_CHANCE_MODIFIER_RE
from shared_utils import OPTION_OPEN_RE as _OPTION_OPEN_RE
from shared_utils import TRIGGER_OPEN_RE as _TRIGGER_OPEN_RE
from sprite_index import build_sprite_index, build_sprite_texture_index
from validator_common import BANKRUPTCY_GUARD_RE as _BANKRUPTCY_GUARD_RE
from validator_common import (
    DEFAULT_EXTRA_SKIP_PATTERNS,
    MONEY_COMMITMENT_RE,
    BaseValidator,
    FileOpener,
    Severity,
    lowering_treasury_checks,
    run_validator_main,
    should_skip_file,
    unneeded_treasury_checks,
    weight_stays_zero,
)

EXTRA_SKIP_PATTERNS = DEFAULT_EXTRA_SKIP_PATTERNS

# The five HOI4 event-firing keywords. It is `operative_leader_event`, not
# `operative_event`, and there is no `character_event`; because `operative` has
# no word boundary before `_leader_event`, an `operative`/`_event` split never
# matches the real keyword.
_EVENT_CALL_KEYWORDS = (
    "country_event",
    "news_event",
    "state_event",
    "unit_leader_event",
    "operative_leader_event",
)
_EVENT_CALL_ALT = "|".join(_EVENT_CALL_KEYWORDS)
_EVENT_CALL_NEEDLES = tuple(keyword.encode() for keyword in _EVENT_CALL_KEYWORDS)
# `event_country`, `event_news`, ...: what _REVERSED_EVENT_CALL_RE matches.
_REVERSED_CALL_NEEDLES = tuple(
    "event_" + keyword.removesuffix("_event") for keyword in _EVENT_CALL_KEYWORDS
)


def _has_event_call(text: str) -> bool:
    return any(keyword in text for keyword in _EVENT_CALL_KEYWORDS)


def _keyword_starts(text: str) -> List[int]:
    starts: List[int] = []
    for keyword in _EVENT_CALL_KEYWORDS:
        pos = text.find(keyword)
        while pos != -1:
            starts.append(pos)
            pos = text.find(keyword, pos + 1)
    starts.sort()
    return starts


def _keyword_matches(
    pattern: "re.Pattern[str]", text: str, starts: Optional[List[int]] = None
) -> Iterator["re.Match[str]"]:
    """Same matches as `pattern.finditer(text)` for a pattern whose every match
    starts with an event call keyword.

    Trying the pattern only where a keyword starts skips the regex engine's
    attempt at every other offset. `starts` lets callers share one keyword scan.
    """
    if starts is None:
        starts = _keyword_starts(text)
    end = 0
    for pos in starts:
        if pos >= end and (match := pattern.match(text, pos)):
            end = match.end()
            yield match


def _line_lookup(text: str) -> Callable[[int], int]:
    """1-based line of an offset in `text`, counted from the previous lookup.

    Scans look offsets up in file order, so each lookup costs only the distance
    moved instead of a count from the start of the file.
    """
    last_pos = 0
    last_line = 1

    def line(pos: int) -> int:
        nonlocal last_pos, last_line
        if pos >= last_pos:
            last_line += text.count("\n", last_pos, pos)
        else:
            last_line -= text.count("\n", pos, last_pos)
        last_pos = pos
        return last_line

    return line


_LONG_FORM_PATTERN = re.compile(
    r"\b(" + _EVENT_CALL_ALT + r")\s*=\s*\{\s*id\s*=\s*([^\s{}]+)\s*\}",
)

# Event picture: `picture = GFX_xxx` (always GFX_-prefixed, resolves to that
# sprite). Sprite names may contain `.` (frame suffixes like GFX_CTC.5) and `-`
# (e.g. GFX_Polizistin-Kiesewetter), so both are part of the captured name.
_EVENT_PICTURE_REF = re.compile(r'\bpicture\s*=\s*"?(GFX_[A-Za-z0-9_.\-]+)"?')
_PICTURE_TOKEN_RE = re.compile(r"[{}]|\bpicture\s*=\s*")

# Stand-in art used while drafting an event; shipped events need real art.
_PLACEHOLDER_PICTURES = frozenset(
    {"GFX_placeholder_events", "GFX_placeholder_news", "GFX_news_md4"}
)


def _own_picture_refs(body: str) -> List[Tuple[str, int]]:
    """Return (sprite, offset) for the picture fields an event itself declares.

    A body-wide scan is wrong here: `create_country_leader = { picture = "..." }`
    and advisor portraits nested in an `immediate` block are character art, not
    the event's picture. `_iter_typed_event_bodies` yields a body stripped of its
    outer braces, so the event's own fields sit at depth 0 — the convention
    `_own_id` uses. The conditional form `picture = { trigger = { ... }
    picture = GFX_x }` contributes its inner references instead.
    """
    refs: List[Tuple[str, int]] = []
    depth = 0
    in_conditional = False
    for token in _PICTURE_TOKEN_RE.finditer(body):
        char = token.group()
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                in_conditional = False
        elif depth == 0 and body.startswith("{", token.end()):
            in_conditional = True
        elif depth == 0 or (depth == 1 and in_conditional):
            ref = _EVENT_PICTURE_REF.match(body, token.start())
            if ref:
                refs.append((ref.group(1), token.start()))
    return refs


# Both event windows draw `event_picture` at the texture's native size — the
# country/report slot (interface/eventwindow.gui:87) and the news slot (:425)
# each declare a position and no size — so art authored for one window overflows
# or under-fills the other. The two families separate cleanly by aspect ratio and
# not by name: GFX_china_trade_war is news art, GFX_FRA_eiffel_tower_news is not.
# Country art tops out at 1.45 (217x163 dominant) and news art starts at 2.0
# (397x153 dominant, 500x250 at the low end), so the 1.5-2.0 band identifies no
# family and is deliberately left unreported.
_PICTURE_ASPECT_COUNTRY_MAX = 1.5
_PICTURE_ASPECT_NEWS_MIN = 2.0
# Decision and idea icons used as event pictures are a different defect entirely;
# classifying them by shape would report the wrong thing, so they are skipped.
_PICTURE_MIN_EDGE = 100
_PICTURE_FORMAT_LABEL = {
    "country_event": "country event",
    "news_event": "news event",
}
_PICTURE_TYPICAL_SIZE = {
    "country_event": "217x163",
    "news_event": "397x153",
}


def _picture_format_for_size(width: int, height: int) -> Optional[str]:
    """Return the event window a texture of this size is authored for, if clear."""
    if height <= 0 or max(width, height) < _PICTURE_MIN_EDGE:
        return None
    aspect = width / height
    if aspect <= _PICTURE_ASPECT_COUNTRY_MAX:
        return "country_event"
    if aspect >= _PICTURE_ASPECT_NEWS_MIN:
        return "news_event"
    return None


def _picture_format_message(
    event_type: str, event_id: str, sprite: str, textures: Dict[str, str]
) -> Optional[str]:
    """Return a finding when the picture's art is authored for the other window.

    A sprite that resolves to nothing, or to a texture whose size cannot be read,
    is left to the missing-picture check rather than reported twice.
    """
    texture = textures.get(sprite)
    if texture is None:
        return None
    size = read_image_size(texture)
    if size is None:
        return None
    authored = _picture_format_for_size(*size)
    if authored is None or authored == event_type:
        return None
    return (
        f"{event_id}: picture = {sprite} is {size[0]}x{size[1]}, which is "
        f"{_PICTURE_FORMAT_LABEL[authored]} art; a "
        f"{_PICTURE_FORMAT_LABEL[event_type]} picture is "
        f"{_PICTURE_TYPICAL_SIZE[event_type]}"
    )


def _should_skip(filename: str, *, mod_path: Optional[str] = None) -> bool:
    return should_skip_file(
        filename, extra_skip_patterns=EXTRA_SKIP_PATTERNS, mod_path=mod_path
    )


def _read_cleaned_text(
    filename: str, *, skip: bool = True, mod_path: Optional[str] = None
) -> Optional[str]:
    """Read a mod file and strip ``#`` comments, or return ``None`` on failure."""
    if skip and _should_skip(filename, mod_path=mod_path):
        return None
    try:
        text = Path(filename).read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return None
    return re.sub(r"#[^\n]*", "", text)


def _extract_event_pictures(
    filename: str, *, mod_path: Optional[str] = None
) -> List[Tuple[str, str, int]]:
    """Pool worker: return (sprite, filename, line) for each event picture ref."""
    text = _read_cleaned_text(filename, mod_path=mod_path)
    if text is None:
        return []
    line = _line_lookup(text)
    return [
        (m.group(1), filename, line(m.start()))
        for m in _EVENT_PICTURE_REF.finditer(text)
    ]


def _extract_option_logs_without_effects(
    filename: str, *, mod_path: Optional[str] = None
) -> List[Tuple[str, str, int]]:
    """Pool worker: (option name, filename, line) for logs in effect-free options."""
    if _should_skip(filename, mod_path=mod_path):
        return []
    try:
        text = Path(filename).read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return []
    return [
        (name, filename, line) for name, line in find_option_logs_without_effects(text)
    ]


def _extract_event_log_id_mismatches(
    filename: str, *, mod_path: Optional[str] = None
) -> List[Tuple[str, str, int]]:
    """Pool worker: (message, filename, line) for option logs citing the wrong id."""
    if _should_skip(filename, mod_path=mod_path):
        return []
    try:
        lines = (
            Path(filename)
            .read_text(encoding="utf-8-sig", errors="replace")
            .splitlines(keepends=True)
        )
    except OSError:
        return []
    results: List[Tuple[str, str, int]] = []
    for row, _s, _e, _repl, token, own_name, kind in _iter_event_log_mismatches(lines):
        if own_name in _OPTION_LOG_ID_EXEMPT:
            continue
        if kind == "letter":
            message = f"{own_name} log says Option {token}"
        else:
            message = f"{own_name} log cites {token}"
        results.append((message, filename, row + 1))
    return results


_ALL_GATED_NOTE = " (every option has a trigger; check the AI sees more than one)"

# Per-worker copies of load_cost_lookups, set once by the Pool initializer.
_W_COSTLY_EFFECTS: Dict[str, str] = {}
_W_STORED_SIGNS: Dict[str, int] = {}
_W_COMMITMENTS: Set[str] = set()


def _init_cost_lookups(
    effects: Dict[str, str], stored: Dict[str, int], commitments: Set[str]
) -> None:
    global _W_COSTLY_EFFECTS, _W_STORED_SIGNS, _W_COMMITMENTS
    _W_COSTLY_EFFECTS = effects
    _W_STORED_SIGNS = stored
    _W_COMMITMENTS = commitments


def _scan_stored_variable_signs(
    filename: str, *, mod_path: Optional[str] = None
) -> Dict[str, int]:
    """Pool worker: stored_variable_signs for one file."""
    text = _read_cleaned_text(filename, mod_path=mod_path)
    if text is None or "set_variable" not in text:
        return {}
    return stored_variable_signs([text])


def load_cost_lookups(
    validator: BaseValidator,
) -> Tuple[Dict[str, str], Dict[str, int], Set[str]]:
    """(costly_scripted_effects, stored_variable_signs, money_commitment_effects)
    read from the whole mod."""
    effect_texts = (
        _read_cleaned_text(path, mod_path=validator.mod_path)
        for path in validator._collect_files(
            ["common/scripted_effects/**/*.txt"], ignore_staged=True
        )
    )
    bodies = _scripted_effect_bodies(text for text in effect_texts if text)
    effects = _costly_effects(bodies)
    commitments = money_commitment_effects(bodies)
    stored: Dict[str, int] = {}
    script_files = validator._collect_files(
        ["common/**/*.txt", "events/**/*.txt", "history/**/*.txt"],
        ignore_staged=True,
    )
    for found in validator._pool_map(
        partial(_scan_stored_variable_signs, mod_path=validator.mod_path), script_files
    ):
        for name, signs in found.items():
            stored[name] = stored.get(name, 0) | signs
    return effects, stored, commitments


def _extract_option_cost_weights(
    filename: str, *, mod_path: Optional[str] = None
) -> Tuple[List[Tuple[str, str, int]], List[Tuple[str, str, int]]]:
    """Pool worker: (message, path, line) rows for both AI weight cost checks."""
    text = _read_cleaned_text(filename, mod_path=mod_path)
    if text is None:
        return [], []
    path = os.path.relpath(filename, mod_path)
    blind, unneeded = find_option_cost_weights(
        text, _W_COSTLY_EFFECTS, _W_STORED_SIGNS, _W_COMMITMENTS
    )
    return [
        (
            f"{name} - ai_chance ignores the {costs} cost"
            + (_ALL_GATED_NOTE if all_gated else ""),
            path,
            line,
        )
        for name, line, costs, all_gated in blind
    ], [(f"{name} - ai_chance {reason}", path, line) for name, line, reason in unneeded]


def _extract_corruption_pp_cost_options(
    filename: str, *, mod_path: Optional[str] = None
) -> List[Tuple[str, str, int]]:
    """Pool worker: options that charge PP while decreasing corruption unguarded."""
    if _should_skip(filename, mod_path=mod_path):
        return []
    text = FileOpener.open_text_file(filename)
    path = os.path.relpath(filename, mod_path)
    return [
        (
            f"{name} - PP charge above the {_MIN_CORRUPTION_REFUND} PP refund per "
            f"decrease_corruption; no recognized local guard against "
            f"{_MIN_CORRUPTION_ID}",
            path,
            line,
        )
        for name, line in find_corruption_pp_cost_options(text)
    ]


_ID_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_.]+")


def _scan_event_id_counts_text(cleaned: str, tracked_ids: frozenset) -> Dict[str, int]:
    """Whole-token counts: `foo.1` and its loc key `foo.1.t` are distinct tokens."""
    counts = Counter(_ID_TOKEN_PATTERN.findall(cleaned))
    return {eid: counts[eid] for eid in tracked_ids.intersection(counts)}


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


_ID_OR_BRACE_RE = re.compile(r"[{}]|\bid\s*=\s*([A-Za-z_][\w.]*)")


def _own_id(body: str):
    """The `id` at the definition's own depth.

    A malformed event with no id of its own can still contain a block fire
    (`country_event = { id = foo.1 days = 1 }`) in its effects. Searching the
    whole body would adopt that child's id, inventing a duplicate of the real
    foo.1 and mislabelling the malformed block instead of leaving it unknown.
    """
    depth = 0
    for m in _ID_OR_BRACE_RE.finditer(body):
        token = m.group(0)
        if token == "{":
            depth += 1
        elif token == "}":
            depth -= 1
        elif depth == 0:
            return m.group(1)
    return None


def _iter_typed_event_bodies(cleaned: str, *, require_id: bool = True):
    """Yield typed definitions using brace matching so indentation is irrelevant.

    With require_id=False a definition block missing its `id` is still yielded,
    with None for the id; the metadata checks report those blocks as "unknown"
    rather than passing over them.
    """
    for m in _keyword_matches(_EVENT_BLOCK_OPEN_RE, cleaned):
        ob = cleaned.index("{", m.end() - 1)
        end = find_unquoted_brace_close(cleaned, ob)
        if end == -1:
            continue
        body = cleaned[ob + 1 : end]
        if not _DEFINITION_ONLY_RE.search(body):
            continue
        event_id = _own_id(body)
        if event_id is None and require_id:
            continue
        yield event_id, m.group(1), body, m.start()


def _iter_event_bodies(cleaned: str):
    """Yield (event_id, body, match_start) for defined events."""
    for eid, _event_type, body, start in _iter_typed_event_bodies(cleaned):
        yield eid, body, start


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
        if eid
    ]


def _is_literal_id(eid: str, after: str) -> bool:
    """False when the ID is assembled at runtime rather than written out.

    `UN.[ID]` matches as `UN.` and `MD_cyber.1[TYPE]` as `MD_cyber.1`, so a
    trailing dot or a following `[` both mean the ID is interpolated.
    """
    return "." in eid and not eid.endswith(".") and not after.startswith("[")


def _iter_typed_fires(text: str):
    """Yield (event_id, call_keyword, match_start) for literal event fires."""
    starts = _keyword_starts(text)
    for m in _keyword_matches(_EVENT_FIRE_SHORT_RE, text, starts):
        if _is_literal_id(m.group(2), text[m.end() : m.end() + 1]):
            yield m.group(2), m.group(1), m.start()
    for m in _keyword_matches(_EVENT_FIRE_BLOCK_RE, text, starts):
        idm = _FIRE_ID_RE.search(m.group(2))
        if idm and _is_literal_id(idm.group(1), m.group(2)[idm.end() : idm.end() + 1]):
            yield idm.group(1), m.group(1), m.start()


def _iter_fired_ids(text: str):
    """Yield (event_id, match_start) for every literal event fire in `text`."""
    for eid, _call_type, pos in _iter_typed_fires(text):
        yield eid, pos


def _scan_typed_fires_text(
    cleaned: str, filename: str
) -> List[Tuple[str, str, str, int]]:
    line = _line_lookup(cleaned)
    return [
        (eid, call_type, filename, line(pos))
        for eid, call_type, pos in _iter_typed_fires(cleaned)
    ]


def _scan_invalid_calls_text(
    cleaned: str, filename: str
) -> List[Tuple[str, str, str, str, int]]:
    results: List[Tuple[str, str, str, str, int]] = []
    line = _line_lookup(cleaned)
    # Every reversed match starts with one of these keywords.
    if any(needle in cleaned for needle in _REVERSED_CALL_NEEDLES):
        for m in _REVERSED_EVENT_CALL_RE.finditer(cleaned):
            results.append(
                (
                    "reversed",
                    m.group(1),
                    m.group(2) or m.group(3),
                    filename,
                    line(m.start()),
                )
            )
    for m in _keyword_matches(_MISSING_EVENT_CALL_EQUALS_RE, cleaned):
        results.append(
            ("missing-equals", m.group(1), m.group(2), filename, line(m.start()))
        )
    results.sort(key=lambda result: result[-1])
    return results


def _scan_dynamic_namespaces_text(cleaned: str) -> Set[str]:
    return {m.group(1) for m in _keyword_matches(_DYNAMIC_EVENT_NS_PATTERN, cleaned)}


# --- date-gated events and the event fire graph ---
#
# A `date >` lower bound anchors an event to a point in history. A `date <`
# bound on its own is an expiry guard on a chain event and says nothing about
# scheduling, so only the lower bound is matched here.
_DATE_LOWER_BOUND_RE = re.compile(r"\bdate\s*>\s*\d{4}\.\d{1,2}\.\d{1,2}")
# Any bound is redundant on an event the yearly effects already schedule.
_DATE_BOUND_RE = re.compile(r"\bdate\s*[<>]=?\s*\d{4}\.\d{1,2}\.\d{1,2}")


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
        end = find_unquoted_brace_close(body, ob)
        return None if end == -1 else body[ob + 1 : end]
    return None


def _events_with_trigger_date(
    filename: str, pattern: "re.Pattern[str]", mod_path: Optional[str]
) -> List[Tuple[str, str, int]]:
    """(id, file, line) of every event whose own trigger matches `pattern`."""
    cleaned = _read_cleaned_text(filename, mod_path=mod_path)
    if cleaned is None:
        return []

    out: List[Tuple[str, str, int]] = []
    line = _line_lookup(cleaned)
    for eid, body, start in _iter_event_bodies(cleaned):
        if not eid:
            continue
        trigger = _event_trigger_body(body)
        if trigger and pattern.search(trigger):
            out.append((eid, filename, line(start)))
    return out


def scan_date_gated_events(
    args: Tuple[str, frozenset], *, mod_path: Optional[str] = None
) -> List[Tuple[str, str, int]]:
    """Pool worker: events whose own trigger carries a `date >` bound."""
    return _events_with_trigger_date(args[0], _DATE_LOWER_BOUND_RE, mod_path)


def scan_date_bounded_events(
    args: Tuple[str, frozenset], *, mod_path: Optional[str] = None
) -> List[Tuple[str, str, int]]:
    """Pool worker: events whose own trigger carries any `date` comparison."""
    return _events_with_trigger_date(args[0], _DATE_BOUND_RE, mod_path)


def scan_event_fire_graph(
    args: Tuple[str, frozenset], *, mod_path: Optional[str] = None
) -> List[Tuple[str, str]]:
    """Pool worker: (parent_id, child_id) for every event fired from an event.

    Lets a chain event inherit whatever schedules its parent, so only the head
    of a chain needs a scheduling entry.
    """
    filename = args[0]
    cleaned = _read_cleaned_text(filename, mod_path=mod_path)
    if cleaned is None:
        return []

    out: List[Tuple[str, str]] = []
    for parent, body, _start in _iter_event_bodies(cleaned):
        if not parent:
            continue
        for child, _pos in _iter_fired_ids(body):
            if child and child != parent:
                out.append((parent, child))
    return out


def _stat_cached_scan(mod_path: str, namespace: str, filename: str, scanner):
    return disk_cache.per_file_cached(
        mod_path,
        namespace,
        filename,
        lambda: scanner((filename, frozenset()), mod_path=mod_path),
    )


def _cached_scan_event_fire_graph(args: Tuple[str, str]) -> List[Tuple[str, str]]:
    filename, mod_path = args
    return _stat_cached_scan(
        mod_path, "events.fire_graph", filename, scan_event_fire_graph
    )


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
# Every token starts with one of these characters; testing that first skips most
# positions without trying each alternative.
_RE_FOF_TOKEN = re.compile(
    r"(?=[{}A-Zcefnosuv])(?:"
    + "|".join(
        (r"\{", r"\}", _FOF_ITER_OPEN, _FOF_PINNED, _FOF_EVENT_LONG, _FOF_EVENT_SHORT)
    )
    + ")"
)
_LOOP_OPENERS = ("every_", "for_each_")


_FOF_IN_LOOP_MSG = (
    "fire_only_once event {eid} fired inside"
    " an every_*/for_each_* iterator (only the first"
    " recipient gets it; drop fire_only_once or fire it"
    " outside the loop)"
)
_MAJOR_IN_LOOP_MSG = (
    "major event {eid} fired inside an every_*/for_each_*"
    " iterator (each iteration broadcasts to every country;"
    " fire it once outside the loop)"
)


def _loop_stack_flags(stack: List[str], pinned_shields: bool) -> bool:
    """True iff the nearest loop/pin frame is an iterator.

    pinned_shields: a ROOT/TAG switch fixes the recipient, which is a
    fire_only_once dedup idiom. Major events still broadcast once per
    iteration even when pinned, so they pass False.
    """
    for kind in reversed(stack):
        if kind == "iter":
            return True
        if kind == "pinned" and pinned_shields:
            return False
    return False


def _scan_in_loop_text(
    cleaned: str,
    filename: str,
    mod_path: str,
    fof_ids: frozenset,
    major_ids: frozenset,
) -> Tuple[List[str], List[str]]:
    """(fire_only_once, major) findings for tracked events fired inside an iterator.

    One token walk serves both checks. A fire inside any iterator repeats a major
    broadcast; a fire_only_once event is flagged only with no pinned scope between.
    """
    fof: List[str] = []
    major: List[str] = []
    line = _line_lookup(cleaned)

    def _finding(eid: str, pos: int, message: str) -> str:
        rel = os.path.relpath(filename, mod_path)
        return f"{rel}:{line(pos)} - {message.format(eid=eid)}"

    def _check(eid: str, pos: int, stack: List[str]) -> None:
        if eid in major_ids:
            major.append(_finding(eid, pos, _MAJOR_IN_LOOP_MSG))
        if eid in fof_ids and _loop_stack_flags(stack, pinned_shields=True):
            fof.append(_finding(eid, pos, _FOF_IN_LOOP_MSG))

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
            if "iter" in stack:
                body, _ = extract_block_from_text(cleaned, m.end() - 1)
                idm = _RE_FOF_ID.search(body)
                if idm:
                    _check(idm.group(1), m.start(), stack)
            stack.append("other")
        elif _RE_FOF_EVENT_SHORT.match(tok) and "iter" in stack:
            _check(tok.split("=", 1)[1].strip(), m.start(), stack)
    return fof, major


def _scan_long_form_text(cleaned: str, filename: str, mod_path: str) -> List[str]:
    rel = os.path.relpath(filename, mod_path)
    results = []
    seen = set()
    lookup = _line_lookup(cleaned)
    for m in _keyword_matches(_LONG_FORM_PATTERN, cleaned):
        line = lookup(m.start())
        key = (rel, line, m.group(1), m.group(2))
        if key in seen:
            continue
        seen.add(key)
        results.append(
            f"{rel}:{line} - {m.group(1)} = {{ id = {m.group(2)} }} → use shorthand `{m.group(1)} = {m.group(2)}`"
        )
    return results


_C_LONGFORM = 1
_C_INVALID = 2
_C_TYPED = 4
_C_COUNT = 8
_C_DYNAMIC = 16
_C_FOF = 32
_C_MAJOR = 64

_EMPTY_SHARED_CALL_SITE_RESULT: Tuple = ([], [], [], {}, set(), [], [])


def _scan_shared_call_site_file(args) -> Tuple:
    """Pool worker: run every applicable call-site scan on one file.

    Reads the file once and shares the naive-stripped and quote-aware artifacts
    across long-form, invalid-call, typed-fire, count, dynamic-namespace, and
    in-loop scans instead of one read plus strip pass per check. Each scan is
    gated by ``mask`` so the file set per check is unchanged. Typed fires and
    dynamic namespaces keep their disk-cache namespaces.
    Returns (longform, invalid, typed, counts, dynamic, fof, major).
    """
    filename, mod_path, mask, count_tracked, fof_ids, major_ids = args
    if mask == 0 or _should_skip(filename, mod_path=mod_path):
        return _EMPTY_SHARED_CALL_SITE_RESULT
    try:
        text = Path(filename).read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return _EMPTY_SHARED_CALL_SITE_RESULT

    # Drop scans that cannot match: every call-site match contains an event
    # keyword (a reversed call its reversed keyword), and an in-loop finding
    # needs an every_*/for_each_* opener. Comment stripping only removes text.
    if not _has_event_call(text):
        mask &= _C_COUNT | _C_INVALID
        if not any(needle in text for needle in _REVERSED_CALL_NEEDLES):
            mask &= _C_COUNT
    if not any(opener in text for opener in _LOOP_OPENERS):
        mask &= ~(_C_FOF | _C_MAJOR)
    if not count_tracked:
        mask &= ~_C_COUNT
    if not fof_ids:
        mask &= ~_C_FOF
    if not major_ids:
        mask &= ~_C_MAJOR

    need_naive = mask & (_C_LONGFORM | _C_TYPED | _C_COUNT | _C_DYNAMIC)
    need_blanked = mask & (_C_INVALID | _C_FOF | _C_MAJOR)
    if not (need_naive or need_blanked):
        return _EMPTY_SHARED_CALL_SITE_RESULT

    naive = re.sub(r"#[^\n]*", "", text) if need_naive else ""
    blanked = blank_quoted_strings(strip_comments(text)) if need_blanked else ""

    longform: List[str] = []
    invalid: List = []
    typed: List = []
    counts: Dict[str, int] = {}
    dynamic: Set[str] = set()
    fof: List[str] = []
    major: List[str] = []

    if mask & _C_LONGFORM:
        longform = _scan_long_form_text(naive, filename, mod_path)
    if mask & _C_INVALID:
        invalid = _scan_invalid_calls_text(blanked, filename)
    if mask & _C_TYPED:
        typed = disk_cache.per_file_cached_by_content(
            mod_path,
            "events.typed_fires",
            filename,
            naive,
            lambda: _scan_typed_fires_text(naive, filename),
        )
    if mask & _C_COUNT:
        counts = _scan_event_id_counts_text(naive, count_tracked)
    if mask & _C_DYNAMIC:
        dynamic = disk_cache.per_file_cached_by_content(
            mod_path,
            "events.dynamic_namespaces",
            filename,
            naive,
            lambda: _scan_dynamic_namespaces_text(naive),
        )
    if mask & (_C_FOF | _C_MAJOR):
        fof, major = _scan_in_loop_text(
            blanked,
            filename,
            mod_path,
            fof_ids if mask & _C_FOF else frozenset(),
            major_ids if mask & _C_MAJOR else frozenset(),
        )
    return (longform, invalid, typed, counts, dynamic, fof, major)


# --- Event parsing ---


_ADD_NAMESPACE_PATTERN = re.compile(r"^\s*add_namespace\s*=\s*(\S+)", re.MULTILINE)
_RANDOM_EVENTS_PATTERN = re.compile(r"\brandom_events\s*=\s*\{")
_RANDOM_EVENT_ID_PATTERN = re.compile(r"=\s*([A-Za-z_]\w*\.[\w.]+)")

# Statements an option can carry that change no game state. `trigger` gates the
# option's visibility and `ai_chance` weights the AI's pick; neither runs an effect.
# Triggered-only events the engine dispatches with no script reference to find.
_EXEMPT_UNREFERENCED_EVENT_IDS = frozenset(
    validation_config("validate_events", "exempt_unreferenced_event_ids")
)
_OPTION_LOG_ID_EXEMPT = frozenset(
    validation_config("validate_events", "option_log_id_exempt")
)

_OPTION_NON_EFFECT_KEYS = frozenset({"name", "log", "ai_chance", "trigger"})
# A scope key is an effect too: `652 = { ... }` opens a state scope and `"LGN" = { ... }`
# a quoted tag scope, so both alternatives must match or an option whose only effect is
# one of them reads as effect-free. Quoted keys survive blank_quoted_strings, which
# blanks the interior but keeps the quotes.
_OPTION_STATEMENT_RE = re.compile(r'([A-Za-z_]\w*|\d+|"[^"]*")\s*=')
_OPTION_TOKEN_RE = re.compile(r"[{}]|" + _OPTION_STATEMENT_RE.pattern)
_BRACE_RE = re.compile(r"[{}]")

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


def find_option_logs_without_effects(text: str) -> List[Tuple[str, int]]:
    """(option name, 1-based log line) for every `log` in an effect-free option.

    Shared with tools/linting/fix_event_option_logs.py so detection cannot drift.
    Line-based rather than offset-based: strip_comments preserves line counts but
    not offsets, and the fixer needs the exact line to delete.
    """
    lines = text.splitlines()
    code = [blank_quoted_strings(strip_inline_comment(line)) for line in lines]
    out: List[Tuple[str, int]] = []
    row = 0
    while row < len(code):
        match = _OPTION_OPEN_RE.search(code[row]) if "option" in code[row] else None
        if match is None:
            row += 1
            continue
        names: List[str] = []
        logs: List[int] = []
        name: Optional[str] = None
        depth = 0
        end_row = row
        closed = False
        while end_row < len(code) and not closed:
            line = code[end_row]
            i = match.end() - 1 if end_row == row else 0
            # Statements count only at the option's own depth; deeper, only braces matter.
            while token := (_OPTION_TOKEN_RE if depth == 1 else _BRACE_RE).search(
                line, i
            ):
                i = token.end()
                char = token.group()
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        closed = True
                        break
                else:
                    key = token.group(1)
                    names.append(key)
                    if key == "log":
                        logs.append(end_row + 1)
                    elif key == "name":
                        value = line[i:].split()
                        name = value[0] if value else None
            if not closed:
                end_row += 1
        if logs and not (set(names) - _OPTION_NON_EFFECT_KEYS):
            out.extend((name or "unnamed option", line_no) for line_no in logs)
        row = end_row + 1 if end_row > row else row + 1
    return out


# Blocks that keep the option's own country scope. A cost inside any other block
# (`FROM = { ... }`, a state scope, a trigger) is not paid by the country choosing.
_OWN_SCOPE_BLOCKS = frozenset(
    {
        "if",
        "else",
        "else_if",
        "hidden_effect",
        "random",
        "random_list",
        "meta_effect",
        "text",
        "ROOT",
        "THIS",
    }
)
_VARIABLE_OPS = ("set", "add_to", "subtract_from", "multiply", "divide")
# Kept whole: the math block nested in one (`x = { value = ... }`) is not a scope.
_VARIABLE_EFFECTS = frozenset(
    f"{op}_{temp}variable" for op in _VARIABLE_OPS for temp in ("", "temp_")
) | {"clamp_variable", "round_variable", "modulo_variable", "set_variable_to_random"}
_IDEA_MUTATION_BLOCKS = frozenset(
    {"add_ideas", "remove_ideas", "add_timed_idea", "remove_timed_idea", "swap_ideas"}
)
_BLOCK_TOKEN_RE = re.compile(r"(?:([\w.:@^]+)\s*=\s*)?\{|\}")
_OPTION_NAME_RE = re.compile(r'\bname\s*=\s*"?([\w.]+)')
_AI_WEIGHT_LITERAL_RE = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)")
_FINANCIAL_GUARD_RE = re.compile(
    _BANKRUPTCY_GUARD_RE.pattern + r"|\bai_has_high_deficit\s*=\s*(?:yes|no)\b"
    r"|\bcheck_variable\s*=\s*\{\s*(?:var\s*=\s*)?(?:ROOT\.|THIS\.)?"
    r"(?:treasury|debt|int_investments|treasury_rate|budget_balance_ratio|"
    r"corporate_tax_rate|population_tax_rate)\b"
)
_COST_GUARDS = {
    "treasury": _FINANCIAL_GUARD_RE,
    "debt": _FINANCIAL_GUARD_RE,
    "international investment": _FINANCIAL_GUARD_RE,
    "tax rate": _FINANCIAL_GUARD_RE,
    "political power": _BANKRUPTCY_GUARD_RE,
    "stability": re.compile(r"\bhas_stability\s*[<>=]"),
    "war support": re.compile(r"\bhas_war_support\s*[<>=]"),
}
_MONEY_COSTS = frozenset({"treasury", "debt", "international investment", "tax rate"})
# lowering_treasury_checks name -> label in findings.
_TREASURY_CHECK_LABELS = {"bankruptcy": "bankruptcy", "deficit": "high deficit"}
_TRIGGER_SCOPE_BLOCKS = frozenset(
    {"AND", "OR", "NOT", "hidden_trigger", "custom_trigger_tooltip"}
)

# Signs a value can have, as bits. Zero has neither, so a zero change costs nothing.
_NEG, _POS = 1, 2
_EQUIPMENT_COSTS = {"add_equipment_to_stockpile": _NEG, "send_equipment": _POS}

# Stored variable -> (signs of a change that cost the country, label). Debt is the
# odd one out: adding to it is what hurts. A tax rate change costs either way.
_COST_VARIABLES = {
    "treasury": (_NEG, "treasury"),
    "debt": (_POS, "debt"),
    "int_investments": (_NEG, "international investment"),
    "corporate_tax_rate": (_NEG | _POS, "tax rate"),
    "population_tax_rate": (_NEG | _POS, "tax rate"),
}
_STAT_COSTS = {
    "add_political_power": "political power",
    "add_stability": "stability",
    "add_war_support": "war support",
    "add_command_power": "command power",
    "add_manpower": "manpower",
}
_COST_ORDER = tuple(_COST_GUARDS)
_MIN_CORRUPTION_ID = "corruption_level_01"
_MIN_CORRUPTION_REFUND = 150
_CORRUPTION_LEVEL_RE = re.compile(r"corruption_level_(0[1-9]|10)")
_CORRUPTION_ID_RE = re.compile(r"(?<![\w])corruption_level_(?:0[1-9]|10)(?![\w])")
_NEGATIVE_NUMBER_RE = re.compile(r"-(?:\d+(?:\.\d*)?|\.\d+)")
# `{ x = operand }` or the long form `{ var = x value = operand }`.
_VARIABLE_ARGS = (
    r"\s*=\s*\{\s*(?:var\s*=\s*(?P<long>[^\s={}]+)\s+value\s*=\s*"
    r"|(?P<short>[^\s={}]+)\s*=\s*)(?P<operand>\{|[^\s{}]+)"
)
_STAT_COST = r"\b(?P<stat>" + "|".join(_STAT_COSTS) + r")\s*=\s*"
_COST_STEP_RE = re.compile(
    r"\b(?P<op>"
    + "|".join(_VARIABLE_OPS)
    + r")_(?P<temp>temp_)?variable"
    + _VARIABLE_ARGS
    + "|"
    + _STAT_COST
    + r"(?P<stat_operand>[^\s{}]+)"
    + r"|\b(?P<equipment>"
    + "|".join(_EQUIPMENT_COSTS)
    + r")\s*=\s*\{"
    + r"|\b(?P<call>[A-Za-z_]\w*)\s*=\s*yes\b"
    r"|\b(?P<branch>if|else_if|else|random_list|random|\d+)\s*=\s*\{"
)
_DIRECT_COST_RE = re.compile(
    r"\b(?:add_to|subtract_from)_variable\s*=\s*\{\s*(?:var\s*=\s*)?(?:"
    + "|".join(_COST_VARIABLES)
    + r")\b|"
    + _STAT_COST
    + r"(?:-|[A-Za-z_])|\b(?:"
    + "|".join(_EQUIPMENT_COSTS)
    + r")\s*=\s*\{"
)
_EFFECT_CALL_RE = re.compile(r"\b([A-Za-z_]\w*)\s*=\s*yes\b")
# A building effect, or a payment a caller can waive with skip_payment for a free build.
_BUILDING_PAYMENT_RE = re.compile(
    r"\b(?:add_building_construction|add_offsite_building|skip_payment)\b"
)
_SCRIPTED_EFFECT_DEF_RE = re.compile(r"^([A-Za-z_][\w.]*)\s*=\s*\{", re.MULTILINE)
_STORED_LITERAL_RE = re.compile(
    r"\bset_variable\s*=\s*\{\s*(?:var\s*=\s*([^\s={}]+)\s+value\s*=\s*"
    r"|([^\s={}]+)\s*=\s*)(-?[\d.]+)\s*\}"
)
_VARIABLE_REFERENCE_RE = re.compile(r"[A-Za-z_][\w.:@^]*")
_RANDOM_LIST_BUCKET_RE = re.compile(r"\b[\d.]+\s*=\s*\{")


def _flip(signs: int) -> int:
    return ((signs & _NEG) << 1) | ((signs & _POS) >> 1)


def _combine(op: str, signs: int, term: int) -> int:
    """Signs `signs` can have after one variable op (or math-block term) with `term`.

    Adding or subtracting only decides the sign of a value that was zero
    (`needed_money = 0`, then `subtract 4.5`). A value that already has a sign
    keeps it: script subtracts a part from a whole (`bailout - debt`) far more
    often than it crosses zero, and calling that negative would invent a charge.
    """
    if op in ("set", "value"):
        return term
    if op in ("multiply", "divide"):
        return (signs if term & _POS else 0) | (_flip(signs) if term & _NEG else 0)
    return signs or (_flip(term) if op.startswith("subtract") else term)


def _guaranteed_cost(signs: int, cost_signs: int) -> bool:
    """Whether every possible nonzero sign represents a charge."""
    return bool(signs) and not signs & ~cost_signs


def _stored_name(variable: str) -> str:
    """`FROM.LBA_cost^2` -> `LBA_cost`: the name a stored variable is set under."""
    return variable.rsplit(".", 1)[-1].split("^", 1)[0]


def _uses_conditional_variable(operand: str, conditional_variables: Set[str]) -> bool:
    return any(
        _stored_name(variable) in conditional_variables
        for variable in _VARIABLE_REFERENCE_RE.findall(operand)
    )


def _skip_switch(limit: str) -> Optional[str]:
    """The charge-skip switch a limit checks, when that is all it checks.

    MD_skip_treasury_cost is set only around history-file setup. skip_payment is
    a temp variable callers set to 1 for a free build.
    """
    guards = list(iter_statements(limit))
    if len(guards) != 1 or guards[0][0] != "NOT" or guards[0][2] is None:
        return None
    skip = list(iter_statements(guards[0][2]))
    if skip == [("has_country_flag", "MD_skip_treasury_cost", None)]:
        return "MD_skip_treasury_cost"
    if (
        len(skip) == 1
        and skip[0][0] == "check_variable"
        and list(iter_statements(skip[0][2] or "")) == [("skip_payment", "1", None)]
    ):
        return "skip_payment"
    return None


def _signs(operand: str, known: Dict[str, int], stored: Dict[str, int]) -> int:
    """Signs a variable-effect operand can have.

    `known` is what this run of effects has set. `stored` is stored_variable_signs.
    Anything else is a stored value like `gdp_total` and counts as positive.
    """
    if operand.startswith("{"):
        signs = 0
        for op, value, block in iter_statements(operand[1:-1]):
            if op in {"value", "add", "subtract", "multiply", "divide"}:
                term = "{" + block + "}" if block is not None else value
                if term is not None:
                    signs = _combine(op, signs, _signs(term, known, stored))
        return signs
    if operand[0] in "-.0123456789":
        if not operand.strip("-.0"):
            return 0
        return _NEG if operand[0] == "-" else _POS
    if operand in known:
        return known[operand]
    return stored.get(_stored_name(operand), _POS)


def _branch_costs(
    body: str,
    start: Dict[str, int],
    known: Dict[str, int],
    conditional_variables: Set[str],
    effects: Dict[str, str],
    stored: Dict[str, int],
    stack: Tuple[str, ...],
) -> Tuple[Set[str], Set[str]]:
    """Costs of a branch run from `start`; its variable changes merge into `known`."""
    branch = dict(start)
    branch_conditional = set(conditional_variables)
    costs, guaranteed = _effect_costs(
        body, effects, branch, stored, stack, branch_conditional
    )
    conditional_variables.update(branch_conditional)
    for variable, signs in branch.items():
        if signs != start.get(variable):
            conditional_variables.add(variable)
        known[variable] = signs | known.get(variable, 0)
    return costs, guaranteed


def _effect_costs(
    text: str,
    effects: Dict[str, str],
    known: Dict[str, int],
    stored: Dict[str, int],
    stack: Tuple[str, ...] = (),
    conditional_variables: Optional[Set[str]] = None,
) -> Tuple[Set[str], Set[str]]:
    """Possible and guaranteed costs to the country running these effects.

    Charges are rarely a plain negative literal: `treasury_change` is often set to
    a GDP variable and negated by `multiply_temp_variable`, or built in one math
    block (`{ value = gdp_total multiply = -0.03 }`), then applied by a scripted
    effect. So this tracks the signs every variable can have and follows calls
    into `effects` (see costly_scripted_effects), which share the caller's temp
    variables the way the game does. A branch (`if`, `random`, a `random_list`
    bucket) may or may not run, so its costs are possible but not guaranteed, and
    its variable changes are added to what was possible before it. A cost every
    arm of an `if`/`else` chain or every `random_list` bucket guarantees is
    guaranteed, and so is an `if` that only checks a charge-skip switch this run
    leaves off. An `else` starts from what held before its `if`. The cost itself
    is a write to a stored variable in _COST_VARIABLES, a negative stat effect, or
    equipment leaving the stockpile.
    """
    # Sign unions omit zero, so retain conditional writes separately.
    if conditional_variables is None:
        conditional_variables = set()
    costs: Set[str] = set()
    guaranteed: Set[str] = set()
    # Also right for the old `if = { ... else = { ... } }` form: this call is the `if`.
    before_if = dict(known)
    # What every arm of the open `if`/`else_if` chain guarantees so far.
    chain: Optional[Set[str]] = None
    pos = 0
    while True:
        m = _COST_STEP_RE.search(text, pos)
        if m is None:
            return costs, guaranteed
        pos = m.end()
        branch_key = m["branch"]
        if branch_key not in ("else_if", "else"):
            chain = None
        end = find_unquoted_brace_close(text, pos - 1) if branch_key else -1
        if end != -1:
            body = text[pos:end]
            pos = end
            limit = (
                next((b for k, _v, b in iter_statements(body) if k == "limit"), None)
                if branch_key == "if"
                else None
            )
            switch = _skip_switch(limit or "")
            # Off unless this run set it: the flag is never set by an event or decision.
            if switch and not known.get(switch):
                body_costs, body_guaranteed = _effect_costs(
                    body, effects, known, stored, stack, conditional_variables
                )
                costs |= body_costs
                guaranteed |= body_guaranteed
            elif branch_key == "random_list":
                start = dict(known)
                bucket_guaranteed: List[Set[str]] = []
                bucket = _RANDOM_LIST_BUCKET_RE.search(body)
                while bucket is not None:
                    bucket_end = find_unquoted_brace_close(body, bucket.end() - 1)
                    if bucket_end == -1:
                        break
                    bucket_costs, bucket_kinds = _branch_costs(
                        body[bucket.end() : bucket_end],
                        start,
                        known,
                        conditional_variables,
                        effects,
                        stored,
                        stack,
                    )
                    costs |= bucket_costs
                    bucket_guaranteed.append(bucket_kinds)
                    bucket = _RANDOM_LIST_BUCKET_RE.search(body, bucket_end)
                if bucket_guaranteed:
                    guaranteed |= set.intersection(*bucket_guaranteed)
            else:
                if branch_key == "if":
                    before_if = dict(known)
                branch_costs, branch_guaranteed = _branch_costs(
                    body,
                    before_if if branch_key.startswith("else") else known,
                    known,
                    conditional_variables,
                    effects,
                    stored,
                    stack,
                )
                costs |= branch_costs
                if branch_key == "if":
                    chain = branch_guaranteed
                elif chain is not None and branch_key.startswith("else"):
                    chain &= branch_guaranteed
                    if branch_key == "else":
                        guaranteed |= chain
                        chain = None
        elif m["stat"]:
            signs = _signs(m["stat_operand"], known, stored)
            if signs & _NEG:
                costs.add(_STAT_COSTS[m["stat"]])
                if _guaranteed_cost(signs, _NEG) and not _uses_conditional_variable(
                    m["stat_operand"], conditional_variables
                ):
                    guaranteed.add(_STAT_COSTS[m["stat"]])
        elif m["equipment"]:
            end = find_unquoted_brace_close(text, pos - 1)
            if end == -1:
                return costs, guaranteed
            for key, value, block in iter_statements(text[pos:end]):
                if key == "amount":
                    operand = "{" + block + "}" if block is not None else value
                    if operand:
                        signs = _signs(operand, known, stored)
                        cost_signs = _EQUIPMENT_COSTS[m["equipment"]]
                        if signs & cost_signs:
                            costs.add("equipment")
                            if _guaranteed_cost(
                                signs, cost_signs
                            ) and not _uses_conditional_variable(
                                operand, conditional_variables
                            ):
                                guaranteed.add("equipment")
            pos = end + 1
        elif m["call"]:
            call = m["call"]
            if call in effects and call not in stack:
                call_costs, call_guaranteed = _effect_costs(
                    effects[call],
                    effects,
                    known,
                    stored,
                    (*stack, call),
                    conditional_variables,
                )
                costs |= call_costs
                guaranteed |= call_guaranteed
        elif m["op"]:
            target = m["long"] or m["short"]
            operand = m["operand"]
            if operand == "{":
                end = find_unquoted_brace_close(text, pos - 1)
                if end == -1:
                    return costs, guaranteed
                operand = text[pos - 1 : end + 1]
                pos = end + 1
            term = _signs(operand, known, stored)
            if target not in _COST_VARIABLES or m["temp"]:
                current = 0 if m["op"] == "set" else _signs(target, known, stored)
                known[target] = _combine(m["op"], current, term)
                if _uses_conditional_variable(operand, conditional_variables):
                    conditional_variables.add(target)
                elif m["op"] == "set":
                    conditional_variables.discard(target)
            elif m["op"] in ("add_to", "subtract_from"):
                cost_signs, kind = _COST_VARIABLES[target]
                signs = _combine(m["op"], 0, term)
                if signs & cost_signs:
                    costs.add(kind)
                    if _guaranteed_cost(
                        signs, cost_signs
                    ) and not _uses_conditional_variable(
                        operand, conditional_variables
                    ):
                        guaranteed.add(kind)


def stored_variable_signs(texts: Iterable[str]) -> Dict[str, int]:
    """Stored variables some script sets to a negative literal -> the signs it is set to.

    An option that reads `treasury_change = TAG_project_cost` charges the country
    only if the stored value is negative, and that is decided wherever the mod
    sets it (`set_variable = { TAG_project_cost = -4 }`), not in the option.
    """
    seen: Dict[str, int] = {}
    for text in texts:
        for long_name, short_name, literal in _STORED_LITERAL_RE.findall(text):
            name = _stored_name(long_name or short_name)
            seen[name] = seen.get(name, 0) | _signs(literal, {}, {})
    return {name: signs for name, signs in seen.items() if signs & _NEG}


def _scripted_effect_bodies(texts: Iterable[str]) -> Dict[str, str]:
    """Whole body of every scripted effect defined in `texts`, quotes blanked."""
    bodies: Dict[str, str] = {}
    for text in texts:
        code = blank_quoted_strings(text)
        pos = 0
        while True:
            m = _SCRIPTED_EFFECT_DEF_RE.search(code, pos)
            end = find_unquoted_brace_close(code, m.end() - 1) if m else -1
            if m is None or end == -1:
                break
            bodies[m.group(1)] = code[m.end() : end]
            pos = end
    return bodies


def costly_scripted_effects(texts: Iterable[str]) -> Dict[str, str]:
    """Own-scope body of every scripted effect that can charge the country calling it.

    That is an effect that writes a money variable or lowers a stat itself, or
    calls one that does. `modify_treasury_effect` and the `*_expenditure` presets
    are found this way, not listed by hand.
    """
    return _costly_effects(_scripted_effect_bodies(texts))


def _costly_effects(bodies: Dict[str, str]) -> Dict[str, str]:
    own = {name: _split_option(body)[0] for name, body in bodies.items()}
    costly = _with_callers(
        {name for name, body in own.items() if _DIRECT_COST_RE.search(body)}, own
    )
    return {name: own[name] for name in costly}


def money_commitment_effects(bodies: Dict[str, str]) -> Set[str]:
    """Scripted effects that commit money, and their callers.

    `bodies` maps each scripted effect to its whole body. See MONEY_COMMITMENT_RE.
    """
    return _with_callers(
        {name for name, body in bodies.items() if MONEY_COMMITMENT_RE.search(body)},
        bodies,
    )


def commits_money(effect_text: str, commitments: Set[str]) -> bool:
    """Whether effects anywhere in `effect_text` commit money, directly or through
    a call to one of `commitments` (money_commitment_effects)."""
    return bool(MONEY_COMMITMENT_RE.search(effect_text)) or not commitments.isdisjoint(
        _EFFECT_CALL_RE.findall(effect_text)
    )


def building_payment_effects(bodies: Dict[str, str]) -> Set[str]:
    """Scripted effects that build or pay for a building, and every effect calling one.

    `bodies` maps each scripted effect to its whole body, nested scopes included.
    """
    return _with_callers(
        {name for name, body in bodies.items() if _BUILDING_PAYMENT_RE.search(body)},
        bodies,
    )


def _with_callers(names: Set[str], bodies: Dict[str, str]) -> Set[str]:
    """`names` plus every effect in `bodies` that calls one of them, at any depth."""
    calls = {name: set(_EFFECT_CALL_RE.findall(body)) for name, body in bodies.items()}
    while True:
        callers = {
            name
            for name, called in calls.items()
            if name not in names and not names.isdisjoint(called)
        }
        if not callers:
            return names
        names |= callers


def _disabled_cost_branch(key: str, body: str) -> bool:
    for name, value, block in iter_statements(body):
        if key == "random" and name == "chance" and value:
            return _signs(value, {}, {}) == 0
        if name == "limit" and block is not None:
            return ("always", "no", None) in iter_statements(block)
    return False


def _split_option(
    body: str,
    country: Optional[str] = None,
    *,
    triggers: bool = False,
    preserve_limits: bool = False,
    numeric_state_scopes: bool = False,
    preserve_idea_effects: bool = False,
    preserve_root_reentry: bool = False,
) -> Tuple[str, Dict[Optional[str], Tuple[int, str]]]:
    """(own-scope text, excluded option-level blocks as key -> (offset, body))."""
    scope_blocks = _OWN_SCOPE_BLOCKS
    if triggers:
        scope_blocks |= _TRIGGER_SCOPE_BLOCKS
    own: List[str] = []
    blocks: Dict[Optional[str], Tuple[int, str]] = {}
    depth = 0
    cursor = 0
    kept_whole = 0
    stack: List[Optional[str]] = []
    skip: Optional[Tuple[int, int, Optional[str], Optional[str]]] = None
    for m in _BLOCK_TOKEN_RE.finditer(body):
        if m.group(0) != "}":
            parent_key = stack[-1] if stack else None
            depth += 1
            key = m.group(1)
            stack.append(key)
            if skip is not None or kept_whole:
                continue
            if (
                (
                    key == "limit"
                    and _skip_switch(
                        body[m.end() : find_unquoted_brace_close(body, m.end() - 1)]
                    )
                )
                or key in _VARIABLE_EFFECTS
                or key in _EQUIPMENT_COSTS
                or (triggers and key == "check_variable")
                or (preserve_limits and key == "limit")
                or (preserve_idea_effects and key in _IDEA_MUTATION_BLOCKS)
            ):
                kept_whole = depth
            else:
                excluded = (
                    key not in scope_blocks
                    and (country is None or key != country)
                    and not (
                        (key or "").isdigit()
                        and (not numeric_state_scopes or parent_key == "random_list")
                    )
                )
                if not triggers and key in {"if", "else_if", "random"}:
                    end = find_unquoted_brace_close(body, m.end() - 1)
                    excluded = _disabled_cost_branch(key, body[m.end() : end])
                if excluded:
                    own.append(body[cursor : m.start()])
                    skip = (depth, m.end(), key, parent_key)
            continue
        if kept_whole == depth:
            kept_whole = 0
        if skip is not None and skip[0] == depth:
            if depth == 1:
                blocks[skip[2]] = (skip[1], body[skip[1] : m.start()])
            if (
                preserve_root_reentry
                and skip[2] not in {"limit", "trigger"}
                and not ((skip[2] or "").isdigit() and skip[3] == "random_list")
            ):
                own.append(
                    _root_reentry_effects(
                        body[skip[1] : m.start()],
                        country,
                        preserve_limits=preserve_limits,
                    )
                )
            cursor = m.end()
            skip = None
        depth -= 1
        if stack:
            stack.pop()
    if skip is None:
        own.append(body[cursor:])
    return " ".join(own), blocks


def _root_reentry_effects(
    body: str, country: Optional[str], *, preserve_limits: bool
) -> str:
    """Keep only ROOT effects reached while executing in a foreign scope."""
    effects: List[str] = []
    for key, _value, block in iter_statements(body):
        if (
            block is None
            or key in {"limit", "trigger"}
            or key in _VARIABLE_EFFECTS
            or key in _EQUIPMENT_COSTS
            or key in _IDEA_MUTATION_BLOCKS
        ):
            continue
        if key == "ROOT":
            own, _blocks = _split_option(
                block,
                country,
                preserve_limits=preserve_limits,
                numeric_state_scopes=True,
                preserve_idea_effects=True,
                preserve_root_reentry=True,
            )
            if own.strip():
                effects.append(f"ROOT = {{ {own} }}")
        else:
            effects.append(
                _root_reentry_effects(block, country, preserve_limits=preserve_limits)
            )
    return " ".join(effect for effect in effects if effect)


def ai_weight_cost_checks(
    ai_weights: str, country: Optional[str] = None
) -> Tuple[Set[str], Set[str]]:
    """(cost kinds the weight covers, treasury checks lowering it), in one walk.

    Each modifier is read in the choosing country's scope. A non-neutral one
    covers the cost kinds of _COST_GUARDS it checks; the treasury checks come
    from validator_common.lowering_treasury_checks.
    """
    covered: Set[str] = set()
    lowering: Set[str] = set()
    pos = 0
    while True:
        match = _AI_CHANCE_MODIFIER_RE.search(ai_weights, pos)
        if match is None:
            return covered, lowering
        end = find_unquoted_brace_close(ai_weights, match.end() - 1)
        if end == -1:
            return covered, lowering
        own, _blocks = _split_option(
            ai_weights[match.end() : end], country, triggers=True
        )
        pos = end + 1
        lowering |= lowering_treasury_checks(own)
        if any(
            float(value) != (1 if key == "factor" else 0)
            for key, value, block in iter_statements(own)
            if key in {"factor", "add"}
            and block is None
            and value is not None
            and _AI_WEIGHT_LITERAL_RE.fullmatch(value)
        ):
            covered.update(
                kind for kind, guard in _COST_GUARDS.items() if guard.search(own)
            )


def unneeded_treasury_reason(
    checks: Set[str], costs: Set[str], commits: bool, item: str
) -> Optional[str]:
    """Why lowering treasury *checks* are unneeded, or None.

    *costs* are the item's possible costs, *commits* whether it commits money
    (commits_money). The rule is validator_common.unneeded_treasury_checks.
    *item* names what the weight belongs to.
    """
    unneeded = unneeded_treasury_checks(
        checks, commits or bool(costs & _MONEY_COSTS), "political power" in costs
    )
    if not unneeded:
        return None
    labels = [
        label for name, label in _TREASURY_CHECK_LABELS.items() if name in unneeded
    ]
    kinds = "money or political power" if "bankruptcy" in unneeded else "money"
    return f"lowers the weight on {' and '.join(labels)}, but the {item} has no {kinds} cost"


def possible_costs(
    effect_text: str, effects: Dict[str, str], stored: Dict[str, int]
) -> Set[str]:
    """Costs effects anywhere in `effect_text` may charge, nested scopes included.

    Wider than effect_costs: a charge back to ROOT from a state scope counts,
    and so does one to another country.
    """
    return _effect_costs(blank_quoted_strings(effect_text), effects, {}, stored)[0]


def effect_costs(
    effect_text: str, effects: Dict[str, str], stored: Dict[str, int]
) -> Set[str]:
    """Costs an effect block body charges its own country.

    The body has comments already stripped. `effects` and `stored` come from
    load_cost_lookups.
    """
    own = _split_option(blank_quoted_strings(effect_text))[0]
    return _effect_costs(own, effects, {}, stored)[0]


def _receiver_tag(trigger: str) -> Optional[str]:
    """A literal tag required on every trigger path, not just mentioned in one."""
    tags = set()
    for key, value, block in iter_statements(trigger):
        if key == "tag" and value and re.fullmatch(r"[A-Z0-9]{3}", value):
            tags.add(value)
        elif key in {"AND", "hidden_trigger", "ROOT", "THIS"} and block is not None:
            tag = _receiver_tag(block)
            if tag:
                tags.add(tag)
    return next(iter(tags)) if len(tags) == 1 else None


def _option_tag_constraints(
    trigger: str,
) -> Tuple[Set[Tuple[str, str]], Set[Tuple[str, str]]]:
    """Required and excluded receiver identities, without crossing scopes or ORs."""
    required: Set[Tuple[str, str]] = set()
    excluded: Set[Tuple[str, str]] = set()
    for key, value, block in iter_statements(strip_comments(trigger)):
        if (
            key in {"tag", "original_tag"}
            and value
            and re.fullmatch(r"[A-Z0-9]{3}", value)
        ):
            required.add((key, value))
        elif key in {"AND", "hidden_trigger", "ROOT", "THIS"} and block is not None:
            inner_required, inner_excluded = _option_tag_constraints(block)
            required |= inner_required
            excluded |= inner_excluded
        elif key == "NOT" and block is not None:
            for field, tag, nested in iter_statements(block):
                if (
                    field in {"tag", "original_tag"}
                    and nested is None
                    and tag
                    and re.fullmatch(r"[A-Z0-9]{3}", tag)
                ):
                    excluded.add((field, tag))
    return required, excluded


def _options_have_disjoint_receivers(triggers: List[str]) -> bool:
    """Prove no receiver can see two options using the same identity field."""
    constraints = [_option_tag_constraints(trigger) for trigger in triggers]
    for index, (required, excluded) in enumerate(constraints):
        for other_required, other_excluded in constraints[:index]:
            if not (
                required & other_excluded
                or other_required & excluded
                or any(
                    field == other_field and tag != other_tag
                    for field, tag in required
                    for other_field, other_tag in other_required
                )
            ):
                return False
    return True


def _literal_cost_amounts(body: str) -> Optional[Dict[str, Decimal]]:
    """Direct literal prices; refunds, balance rewrites, and calls stay unknown."""
    amounts: Dict[str, Decimal] = {}
    for key, value, block in iter_statements(strip_comments(body)):
        if key in {"ROOT", "THIS", "hidden_effect"} and block is not None:
            nested = _literal_cost_amounts(block)
            if nested is None:
                return None
            for kind, amount in nested.items():
                amounts[kind] = amounts.get(kind, Decimal(0)) + amount
        elif (
            (value == "yes" and key not in _OPTION_NON_EFFECT_KEYS)
            or key
            in {"if", "else_if", "else", "random", "random_list", "meta_effect", "text"}
            or (block is not None and key.isdigit())
        ):
            return None
        elif key in _STAT_COSTS and _STAT_COSTS[key] in _COST_GUARDS:
            if value is None or not _AI_WEIGHT_LITERAL_RE.fullmatch(value):
                return None
            delta = -Decimal(value)
            if delta < 0:
                return None
            kind = _STAT_COSTS[key]
            amounts[kind] = amounts.get(kind, Decimal(0)) + delta
        elif key in _VARIABLE_EFFECTS and "_temp_" not in key and block is not None:
            fields = {name: scalar for name, scalar, _nested in iter_statements(block)}
            target = fields.get("var")
            if target is None:
                if len(fields) != 1:
                    return None
                target, value = next(iter(fields.items()))
            else:
                value = fields.get("value")
            cost = _COST_VARIABLES.get(target or "")
            if cost is None or cost[1] == "tax rate":
                continue
            if (
                key not in {"add_to_variable", "subtract_from_variable"}
                or value is None
                or not _AI_WEIGHT_LITERAL_RE.fullmatch(value)
            ):
                return None
            signs, kind = cost
            delta = Decimal(value)
            if key == "subtract_from_variable":
                delta = -delta
            if signs == _NEG:
                delta = -delta
            if delta < 0:
                return None
            amounts[kind] = amounts.get(kind, Decimal(0)) + delta
    return amounts


def find_option_cost_weights(
    text: str, effects: Dict[str, str], stored: Dict[str, int], commitments: Set[str]
) -> Tuple[List[Tuple[str, int, str, bool]], List[Tuple[str, int, str]]]:
    """AI weights that ignore an option's cost, and treasury checks it lacks a cost for.

    The first list holds (option name, 1-based line, costs, all gated): each cost
    not covered by a relevant, non-neutral AI modifier in the choosing country's
    scope. Opinion and path modifiers do not cover costs. A missing `ai_chance` is
    the flat default weight. `all gated` marks an event where every option has a
    `trigger`: those may be variants the AI never chooses between, so the finding
    needs a look before it is fixed. The second list holds (option name, line,
    reason) from unneeded_treasury_reason, against possible_costs and
    commits_money over the whole option. The line is the `ai_chance` when there
    is one, since that is where the fix goes. `effects`, `stored` and
    `commitments` come from load_cost_lookups.

    Skipped: an event whose own trigger requires `is_ai = no`, an event whose
    option tag gates prove each receiver sees at most one option, an option the AI
    never picks (`base = 0`, no `add`) while another option can win, and, for
    ignored costs, a cost every option always pays, or every option pays only
    sometimes, since a guard on each one scales them all alike. Unequal direct
    literal prices need guards above the cheapest AI-eligible price when no option
    has a trigger. Scripted, computed, and conditional prices remain unmeasured.
    Tax rate is never shared: options can move it apart.
    """
    code = blank_quoted_strings(text)
    line = _line_lookup(code)
    out: List[Tuple[str, int, str, bool]] = []
    unneeded: List[Tuple[str, int, str]] = []
    for _eid, body, start in _iter_event_bodies(code):
        base = code.index("{", start) + 1
        options = [
            (match.end(), find_unquoted_brace_close(body, match.end() - 1))
            for match in _OPTION_OPEN_RE.finditer(body)
        ]
        trigger = _event_trigger_body(body) or ""
        if len(options) < 2 or first_flat_match(trigger, IS_AI_NO_RE):
            continue
        country = _receiver_tag(trigger)
        splits = [
            _split_option(body[opt_start:opt_end], country)
            for opt_start, opt_end in options
        ]
        all_gated = all("trigger" in blocks for _own, blocks in splits)
        if all_gated and _options_have_disjoint_receivers(
            [blocks["trigger"][1] for _own, blocks in splits]
        ):
            continue
        option_effect_costs = [
            _effect_costs(own, effects, {}, stored) for own, _b in splits
        ]
        option_costs = [costs for costs, _guaranteed in option_effect_costs]
        guaranteed_costs = [guaranteed for _costs, guaranteed in option_effect_costs]
        # Shared when every option pays it always, or every option only sometimes.
        always_somewhere: Set[str] = set().union(*guaranteed_costs)
        shared = (
            set.intersection(*guaranteed_costs)
            | set.intersection(*option_costs) - always_somewhere
        ) - {"tax rate"}
        never_picked = [
            weight_stays_zero(blocks.get("ai_chance", (0, ""))[1])
            for _own, blocks in splits
        ]
        shared_by_option = [shared.copy() for _option in options]
        eligible = [index for index, never in enumerate(never_picked) if not never]
        if (
            shared
            and len(eligible) > 1
            and not any("trigger" in blocks for _own, blocks in splits)
        ):
            prices = [_literal_cost_amounts(splits[index][0]) for index in eligible]
            for kind in shared:
                amounts = [
                    price[kind]
                    for price in prices
                    if price is not None and price.get(kind, Decimal(0)) > 0
                ]
                if len(amounts) != len(eligible):
                    continue
                cheapest = min(amounts)
                for index, amount in zip(eligible, amounts):
                    if amount > cheapest:
                        shared_by_option[index].discard(kind)
        for (opt_start, opt_end), (_own, blocks), costs, never, shared_costs in zip(
            options, splits, option_costs, never_picked, shared_by_option
        ):
            if never and not all(never_picked):
                continue
            ai_offset, ai_chance = blocks.get("ai_chance", (0, ""))
            covered, lowering = ai_weight_cost_checks(ai_chance, country)
            option = body[opt_start:opt_end]
            reason = (
                unneeded_treasury_reason(
                    lowering,
                    possible_costs(option, effects, stored),
                    commits_money(option, commitments),
                    "option",
                )
                if lowering
                else None
            )
            ignored = (costs - shared_costs - covered) & _COST_GUARDS.keys()
            if not (ignored or reason):
                continue
            match = _OPTION_NAME_RE.search(text, base + opt_start, base + opt_end)
            name = match.group(1) if match else "unnamed option"
            ai_line = line(base + opt_start + ai_offset)
            if ignored:
                out.append(
                    (
                        name,
                        ai_line,
                        ", ".join(kind for kind in _COST_ORDER if kind in ignored),
                        all_gated,
                    )
                )
            if reason:
                unneeded.append((name, ai_line, reason))
    return out, unneeded


def _statement_corruption_level_bound(
    key: str,
    value: Optional[str],
    block: Optional[str],
    country: Optional[str] = None,
) -> Optional[int]:
    """Minimum corruption level implied by one trigger statement, if known.

    A level-1 exclusion supplies a floor of 2. Repeated decreases can still
    reach the level-1 PP refund branch.
    """
    if key == "NOT" and block is not None:
        statements = list(iter_statements(block))
        if len(statements) == 1:
            child_key, child_value, child_block = statements[0]
            if (
                child_key == "has_idea"
                and child_value == _MIN_CORRUPTION_ID
                and child_block is None
            ):
                return 2
            if child_key == "OR" and child_block is not None:
                excludes = any(
                    branch_key == "has_idea"
                    and branch_value == _MIN_CORRUPTION_ID
                    and branch_block is None
                    for branch_key, branch_value, branch_block in iter_statements(
                        child_block
                    )
                )
                return 2 if excludes else None
        return None
    if key == "has_idea" and value is not None and block is None:
        match = _CORRUPTION_LEVEL_RE.fullmatch(value)
        return int(match.group(1)) if match else None
    if block is None:
        return None
    statements = list(iter_statements(block))
    if key == "OR":
        bounds = [
            _statement_corruption_level_bound(
                child_key, child_value, child_block, country=country
            )
            for child_key, child_value, child_block in statements
        ]
        proven = [bound for bound in bounds if bound is not None]
        return min(proven) if proven and len(proven) == len(bounds) else None
    if (
        key in {"AND", "ROOT", "THIS", "hidden_trigger", "custom_trigger_tooltip"}
        or key == country
    ):
        bounds = [
            _statement_corruption_level_bound(
                child_key, child_value, child_block, country=country
            )
            for child_key, child_value, child_block in statements
        ]
        proven = [bound for bound in bounds if bound is not None]
        return max(proven) if proven else None
    return None


def _trigger_corruption_level_bound(
    trigger: str, country: Optional[str] = None
) -> Optional[int]:
    """Minimum corruption level implied by a trigger's conjunctive conditions."""
    bounds = [
        _statement_corruption_level_bound(key, value, block, country)
        for key, value, block in iter_statements(trigger)
    ]
    proven = [bound for bound in bounds if bound is not None]
    return max(proven) if proven else None


def _negative_pp_cost(value: Optional[str]) -> bool:
    return bool(
        value is not None
        and _NEGATIVE_NUMBER_RE.fullmatch(value)
        and any(character in "123456789" for character in value)
    )


def _effect_presence(body: str) -> Tuple[float, int]:
    """Total literal negative PP charge and count of decrease_corruption calls."""
    pp_charge = 0.0
    decreases_corruption = 0
    for key, value, block in iter_statements(body):
        if (
            key in {"limit", "trigger"}
            or key in _VARIABLE_EFFECTS
            or key in _EQUIPMENT_COSTS
        ):
            continue
        if key == "add_political_power" and _negative_pp_cost(value):
            pp_charge -= float(value or 0)
        elif key == "decrease_corruption" and value == "yes":
            decreases_corruption += 1
        if block is not None:
            nested_charge, nested_decrease = _effect_presence(block)
            pp_charge += nested_charge
            decreases_corruption += nested_decrease
    return pp_charge, decreases_corruption


def _guard_prevents_min_corruption_refund(
    bound: Optional[int], decrease_calls: int
) -> bool:
    return bound is not None and decrease_calls < bound


def _has_corruption_level_mutation(body: str) -> bool:
    """Whether own-scope effects can invalidate a previously checked level bound."""
    for key, value, block in iter_statements(body):
        if key == "decrease_corruption" and value == "yes":
            return True
        if key in _IDEA_MUTATION_BLOCKS and _CORRUPTION_ID_RE.search(
            value or block or ""
        ):
            return True
        if (
            block is not None
            and key not in {"limit", "trigger"}
            and key not in _VARIABLE_EFFECTS
            and key not in _EQUIPMENT_COSTS
            and _has_corruption_level_mutation(block)
        ):
            return True
    return False


def _idea_mutation_before_decrease(
    body: str, changed_idea: bool = False
) -> Tuple[bool, bool]:
    """Whether an idea change precedes a decrease, and whether one remains pending."""
    for key, value, block in iter_statements(body):
        if key == "decrease_corruption" and value == "yes":
            if changed_idea:
                return True, True
            continue
        if key in _IDEA_MUTATION_BLOCKS and _CORRUPTION_ID_RE.search(
            value or block or ""
        ):
            changed_idea = True
            continue
        if (
            block is not None
            and key not in {"limit", "trigger"}
            and key not in _VARIABLE_EFFECTS
            and key not in _EQUIPMENT_COSTS
        ):
            invalidated, nested_change = _idea_mutation_before_decrease(
                block, changed_idea
            )
            if invalidated:
                return True, True
            changed_idea = nested_change
    return False, changed_idea


def _all_corruption_operations_guarded(
    body: str, country: Optional[str] = None
) -> bool:
    """Require every relevant operation to sit in a guarded paid-decrease block."""
    for key, value, block in iter_statements(body):
        if (key == "add_political_power" and _negative_pp_cost(value)) or (
            key == "decrease_corruption" and value == "yes"
        ):
            return False
        if (
            block is None
            or key in {"limit", "trigger"}
            or key in _VARIABLE_EFFECTS
            or key in _EQUIPMENT_COSTS
        ):
            continue
        if key in {"if", "else_if"}:
            limit = next(
                (
                    nested
                    for nested_key, _nested_value, nested in iter_statements(block)
                    if nested_key == "limit" and nested is not None
                ),
                None,
            )
            bound = _trigger_corruption_level_bound(limit, country) if limit else None
            if bound is not None:
                pp_charge, decreases_corruption = _effect_presence(block)
                idea_bound_invalidated, _idea_change_remains = (
                    _idea_mutation_before_decrease(block)
                )
                if (
                    pp_charge
                    and decreases_corruption
                    and not idea_bound_invalidated
                    and _guard_prevents_min_corruption_refund(
                        bound, decreases_corruption
                    )
                ):
                    continue
        if not _all_corruption_operations_guarded(block, country):
            return False
    return True


def find_corruption_pp_cost_options(text: str) -> List[Tuple[str, int]]:
    """Return event options charging literal PP while decreasing corruption unguarded.

    Only a charge above the 150 PP each decrease refunds at level 1 can lose PP.
    A level-1 exclusion must gate the event, the option, or an effect block that
    contains both operations. Dynamic PP values and unrelated country scopes are
    left to manual review.
    """
    source = strip_comments(text)
    code = blank_quoted_strings(source)
    line = _line_lookup(code)
    out: List[Tuple[str, int]] = []
    for _event_id, body, start in _iter_event_bodies(code):
        event_trigger = _event_trigger_body(body) or ""
        country = _receiver_tag(event_trigger)
        event_bound = _trigger_corruption_level_bound(event_trigger, country)
        event_immediate = next(
            (
                block
                for key, _value, block in iter_statements(body)
                if key == "immediate" and block is not None
            ),
            "",
        )
        immediate_effects, _immediate_blocks = _split_option(
            event_immediate,
            country,
            numeric_state_scopes=True,
            preserve_idea_effects=True,
            preserve_root_reentry=True,
        )
        if _has_corruption_level_mutation(immediate_effects):
            event_bound = None
        base = code.index("{", start) + 1
        for match in _OPTION_OPEN_RE.finditer(body):
            end = find_unquoted_brace_close(body, match.end() - 1)
            if end == -1:
                continue
            option = body[match.end() : end]
            own_effects, blocks = _split_option(
                option,
                country,
                preserve_limits=True,
                numeric_state_scopes=True,
                preserve_idea_effects=True,
                preserve_root_reentry=True,
            )
            option_trigger = blocks.get("trigger", (0, ""))[1]
            option_bound = _trigger_corruption_level_bound(option_trigger, country)
            idea_bound_invalidated, _idea_change_remains = (
                _idea_mutation_before_decrease(own_effects)
            )
            if idea_bound_invalidated:
                bound = None
            else:
                bound = max(
                    (
                        value
                        for value in (event_bound, option_bound)
                        if value is not None
                    ),
                    default=None,
                )
            pp_charge, decreases_corruption = _effect_presence(own_effects)
            # At level 1 each decrease refunds this much, so a smaller charge loses nothing.
            if (
                not decreases_corruption
                or pp_charge <= _MIN_CORRUPTION_REFUND * decreases_corruption
            ):
                continue
            if _guard_prevents_min_corruption_refund(bound, decreases_corruption):
                continue
            if _all_corruption_operations_guarded(own_effects, country):
                continue
            option_name = _OPTION_NAME_RE.search(
                source, base + match.start(), base + end
            )
            out.append(
                (
                    option_name.group(1) if option_name else "unnamed option",
                    line(base + match.start()),
                )
            )
    return out


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


def scan_probability_rolled_fires(
    args: Tuple[str, frozenset], *, mod_path: Optional[str] = None
) -> Set[str]:
    """Pool worker: event IDs fired inside a `random = { chance = N ... }` poll.

    A chance-rolled on_action poll emulates MTTH: each tick it rolls a chance
    and fires the event when it wins. The event has no deterministic yearly
    slot, so the date-gated scheduling check must not flag it as dead content.
    """
    filename = args[0]
    if _should_skip(filename, mod_path=mod_path):
        return set()
    try:
        text = Path(filename).read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return set()
    cleaned = re.sub(r"#[^\n]*", "", text)
    ids: set = set()
    for m in _RANDOM_BLOCK_PATTERN.finditer(cleaned):
        body, _ = extract_block_from_text(cleaned, m.end() - 1)
        if _CHANCE_PATTERN.search(body):
            for eid, _pos in _iter_fired_ids(body):
                ids.add(eid)
    return ids


# `is_major = yes` is a country trigger ("this is a major power") and must
# not count as the event-level `major = yes` broadcast flag.
_RE_MAJOR_YES = re.compile(r"(?<![A-Za-z0-9_])major\s*=\s*yes")


def _parse_event_metadata(text: str, basename: str) -> Tuple[List[dict], Set[str]]:
    namespaces: Set[str] = set(_ADD_NAMESPACE_PATTERN.findall(text))
    meta: List[dict] = []
    line = _line_lookup(text)
    # Brace matching rather than column-anchored patterns: 64 definitions in
    # the mod are indented, and an anchored scan drops every one of them from
    # the checks that read this metadata.
    for event_id, event_type, body, start in _iter_typed_event_bodies(
        text, require_id=False
    ):
        # Quote-aware comment strip + quoted-string blanking before the `in body`
        # flag checks: a commented-out `#fire_only_once = yes` (or hidden /
        # is_triggered_only / mean_time_to_happen) must not count as an active
        # directive, and a `#` (or one of those keywords) inside a quoted
        # log/desc string must not truncate the line or false-match.
        body_c = strip_comments(body)
        body_nc = blank_quoted_strings(body_c)
        # Picture refs read the un-blanked text: Event Horizon quotes its values
        # (`picture = "GFX_EH_USN_HQ"`), which blank_quoted_strings would erase.
        # The body starts one character past its opening brace, so that brace's
        # line is the base every in-body offset counts from.
        picture_base_line = line(text.index("{", start))

        meta.append(
            {
                "id": event_id,
                "body": body,
                "type": event_type,
                "file": basename,
                "line": line(start),
                "is_hidden": "hidden = yes" in body_nc,
                "picture_refs": [
                    (sprite, picture_base_line + body_c.count("\n", 0, offset))
                    for sprite, offset in _own_picture_refs(body_c)
                ],
                "is_triggered_only": "is_triggered_only = yes" in body_nc,
                "fire_only_once": "fire_only_once = yes" in body_nc,
                "is_major": bool(_RE_MAJOR_YES.search(body_nc)),
                "has_mtth": "mean_time_to_happen" in body_nc,
                "option_count": len(_OPTION_OPEN_RE.findall(body)),
                "title_desc_refs": [
                    v.strip() for v in _EVENT_TITLEDESC_PATTERN.findall(body)
                ],
            }
        )
    return meta, namespaces


class Validator(BaseValidator):
    TITLE = "EVENT VALIDATION"
    STAGED_EXTENSIONS = [".txt"]

    def __init__(
        self,
        *args,
        check_ai_chance_costs: bool = False,
        check_corruption_pp_costs: bool = False,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.check_ai_chance_costs = check_ai_chance_costs
        self.check_corruption_pp_costs = check_corruption_pp_costs
        self._meta_cache: Optional[Tuple[List[dict], set]] = None
        self._parsed_event_files: Dict[str, Tuple[List[dict], Set[str]]] = {}
        self._random_events_cache: Optional[set] = None
        self._probability_rolled_cache: Optional[set] = None
        self._fire_only_once_ids_cache: Optional[set] = None
        self._major_event_ids_cache: Optional[set] = None
        self._fire_scan_args_cache: Optional[List[Tuple[str, frozenset]]] = None
        self._fires_cache: Optional[List[Tuple[str, str, int]]] = None
        self._fire_sources_cache: Optional[Dict[str, Set[str]]] = None
        self._definition_types_cache: Optional[Dict[str, str]] = None
        self._full_call_site_scan_cache: Optional[bool] = None

    def _get_event_metadata(self) -> Tuple[List[dict], set]:
        """Parse all event files and return (event_metadata_list, declared_namespaces).

        Each metadata dict has: id (or None for malformed blocks), type, file
        (basename), path (mod-relative), line, is_hidden, picture_refs, is_triggered_only, fire_only_once,
        is_major, has_mtth, option_count, title_desc_refs.
        """
        if self._meta_cache is None:
            self._meta_cache = self._merged_event_metadata(
                self._collect_files(["events/**/*.txt"])
            )
        return self._meta_cache

    def _merged_event_metadata(self, files: List[str]) -> Tuple[List[dict], set]:
        """Metadata of `files` in order; each event file is parsed once per run.

        The staged-scope checks and the full-repo fire_only_once / major lookups
        read the same files, so they share one parse.
        """
        meta: List[dict] = []
        namespaces: set = set()
        for filepath in files:
            parsed = self._parsed_event_files.get(filepath)
            if parsed is None:
                text = FileOpener.open_text_file(
                    filepath, lowercase=False, strip_comments_flag=True
                )
                basename = os.path.basename(filepath)
                parsed = (
                    disk_cache.per_file_cached_by_content(
                        self.mod_path,
                        "events.metadata",
                        filepath,
                        text,
                        lambda: _parse_event_metadata(text, basename),
                    )
                    if text
                    else ([], set())
                )
                rel = self._rel_posix(filepath)
                for ev in parsed[0]:
                    ev["path"] = rel
                self._parsed_event_files[filepath] = parsed
            meta.extend(parsed[0])
            namespaces |= parsed[1]
        return meta, namespaces

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

    def _files_contain_event_fires(self, files: List[str]) -> bool:
        for path in files:
            try:
                with open(path, "rb") as handle:
                    data = handle.read()
            except OSError:
                return True
            if any(needle in data for needle in _EVENT_CALL_NEEDLES):
                return True
        return False

    def _needs_full_call_site_scan(self) -> bool:
        if not self.staged_only:
            return True
        if self._full_call_site_scan_cache is not None:
            return self._full_call_site_scan_cache
        paths = list(self.staged_files or [])
        paths.extend(
            get_staged_files(
                self.mod_path,
                extensions=self.STAGED_EXTENSIONS,
                include_missing=True,
            )
            or []
        )
        self._full_call_site_scan_cache = any(
            self._rel_posix(
                path if os.path.isabs(path) else os.path.join(self.mod_path, path)
            ).startswith("events/")
            for path in paths
        )
        return self._full_call_site_scan_cache

    def _skip_call_site_check(
        self, success: str, fail: str, category: str, severity=Severity.ERROR
    ) -> bool:
        if not self.staged_only or self._needs_full_call_site_scan():
            return False
        files = [path for path, _ in self._get_scoped_fire_scan_args()]
        if self._files_contain_event_fires(files):
            return False
        self.log("  No event fires in scope — skipping")
        self._report([], success, fail, severity, category)
        return True

    def _get_shared_call_site_scan(self) -> dict:
        """Run every call-site check in one pool pass over the union file set.

        Reads each candidate file once and shares the naive-stripped and
        quote-aware artifacts across long-form, invalid-call, typed-fire,
        count, dynamic-namespace, and in-loop scans. Each file runs exactly the
        scans its own check file list selects (via ``mask``). Typed fires derive
        untyped fires parent-side,
        and the two disk-cache namespaces are kept. Events-only passes (pictures,
        option logs, date gates, fire graph, definitions) and on_actions lookups
        keep their own file sets and stay separate.
        """
        memo = getattr(self, "_shared_call_site_memo", None)
        if memo is not None:
            return memo
        self._log_section("Sharing per-file reads across event call-site checks...")

        scoped_files = [f for f, _ in self._get_scoped_fire_scan_args()]
        use_full = (not self.staged_only) or self._needs_full_call_site_scan()
        # A staged run with no event file staged scans only its own callers.
        full_files = [f for f, _ in self._get_fire_scan_args()] if use_full else []
        union = full_files if use_full else scoped_files

        # The in-loop scans only run on scoped files.
        fof_ids: frozenset = frozenset()
        major_ids: frozenset = frozenset()
        if scoped_files:
            fof_ids = frozenset(self._get_fire_only_once_ids())
            major_ids = frozenset(self._get_major_event_ids())
        count_tracked: frozenset = frozenset()
        if not self.staged_only:
            meta, _ = self._get_event_metadata()
            count_tracked = frozenset(
                ev["id"]
                for ev in meta
                if ev["id"] is not None
                and ev["is_triggered_only"]
                and ev["id"] not in _EXEMPT_UNREFERENCED_EVENT_IDS
            )

        scoped_set = set(scoped_files)
        typed_set = set(full_files) if use_full else scoped_set
        count_set = set(full_files) if not self.staged_only else set()
        args_list = []
        for f in union:
            mask = 0
            if f in scoped_set:
                mask |= _C_LONGFORM | _C_INVALID | _C_FOF | _C_MAJOR
            if f in typed_set:
                mask |= _C_TYPED | _C_DYNAMIC
            if f in count_set:
                mask |= _C_COUNT
            args_list.append(
                (f, self.mod_path, mask, count_tracked, fof_ids, major_ids)
            )

        longform_all: List[str] = []
        invalid_all: List = []
        typed_all: List = []
        fof_all: List[str] = []
        major_all: List[str] = []
        dynamic_all: Set[str] = set()
        total_counts: Dict[str, int] = {}
        for longform, invalid, typed, counts, dynamic, fof, major in self._pool_map(
            _scan_shared_call_site_file, args_list, chunksize=30
        ):
            longform_all.extend(longform)
            invalid_all.extend(invalid)
            typed_all.extend(typed)
            fof_all.extend(fof)
            major_all.extend(major)
            dynamic_all.update(dynamic)
            for eid, count in counts.items():
                total_counts[eid] = total_counts.get(eid, 0) + count
        fires_all = [
            (eid, filename, line) for eid, _call_type, filename, line in typed_all
        ]
        empty: dict = {
            "longform": longform_all,
            "invalid": invalid_all,
            "typed": typed_all,
            "fires": fires_all,
            "counts": total_counts,
            "dynamic": dynamic_all,
            "fof": fof_all,
            "major": major_all,
        }
        self._shared_call_site_memo = empty
        return empty

    def _get_event_fires(self) -> List[Tuple[str, str, int]]:
        """Every literal event fire in the mod as (event_id, file, line)."""
        if self._fires_cache is None:
            self._fires_cache = list(self._get_shared_call_site_scan()["fires"])
        return self._fires_cache

    def _get_fire_sources(self) -> Dict[str, Set[str]]:
        """Event id -> mod-relative posix paths of the files that fire it."""
        if self._fire_sources_cache is None:
            rels: Dict[str, str] = {}
            sources: Dict[str, Set[str]] = {}
            for eid, filename, _line in self._get_event_fires():
                if filename not in rels:
                    rels[filename] = self._rel_posix(filename)
                sources.setdefault(eid, set()).add(rels[filename])
            self._fire_sources_cache = sources
        return self._fire_sources_cache

    def _get_event_definition_types(self) -> Dict[str, str]:
        """Return event declaration keywords from the full events tree."""
        if self._definition_types_cache is not None:
            return self._definition_types_cache
        event_files = self._collect_files(["events/**/*.txt"], ignore_staged=True)

        def _build() -> Dict[str, str]:
            return dict(
                self._pool_flat_map(
                    scan_event_definition_types,
                    [(f, frozenset()) for f in event_files],
                    chunksize=20,
                )
            )

        definitions = disk_cache.aggregate_cached(
            self.mod_path,
            "events.definition_types",
            event_files,
            _build,
            namespace="events",
        )
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

        def _build() -> set:
            ids: set = set()
            for filepath in files:
                text = FileOpener.open_text_file(
                    filepath, lowercase=False, strip_comments_flag=True
                )
                if not text:
                    continue
                ids.update(_extract_random_event_ids(text))
            return ids

        ids = disk_cache.aggregate_cached(
            self.mod_path,
            "events.random_event_ids",
            files,
            _build,
            namespace="events",
        )
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
        ids = set(
            self._pool_flat_map(
                partial(scan_probability_rolled_fires, mod_path=self.mod_path),
                [(f, frozenset()) for f in files],
                chunksize=30,
            )
        )

        self._probability_rolled_cache = ids
        return ids

    def _collect_event_ids_where(self, predicate: Callable[[dict], bool]) -> set:
        meta, _ = self._merged_event_metadata(
            self._collect_files(["events/**/*.txt"], ignore_staged=True)
        )
        return {ev["id"] for ev in meta if predicate(ev)}

    def _get_fire_only_once_ids(self) -> set:
        """Return IDs of events declared ``fire_only_once = yes``.

        Lookup pass: must scan the full repo even in staged mode. Otherwise a
        staged caller that fires an existing fire_only_once event whose
        definition lives in an unstaged file drops out of the ID set, and the
        real in-loop / multi-caller bug commits silently.
        """
        if self._fire_only_once_ids_cache is not None:
            return self._fire_only_once_ids_cache
        self._fire_only_once_ids_cache = self._collect_event_ids_where(
            lambda ev: bool(ev["fire_only_once"])
        )
        return self._fire_only_once_ids_cache

    def _get_major_event_ids(self) -> set:
        """Return IDs of events declared ``major = yes``.

        Lookup pass: must scan the full repo even in staged mode. Otherwise a
        staged caller that fires an existing major event whose definition
        lives in an unstaged file drops out of the ID set, and the in-loop
        broadcast bug commits silently.
        """
        if self._major_event_ids_cache is not None:
            return self._major_event_ids_cache
        self._major_event_ids_cache = self._collect_event_ids_where(
            lambda ev: bool(ev["is_major"] and ev["id"])
        )
        return self._major_event_ids_cache

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

        results = list(self._get_shared_call_site_scan()["longform"])

        self._report(
            results,
            "✓ No redundant long-form event calls found",
            "Long-form event calls with only id (use shorthand instead):",
        )

    def validate_missing_localisation(self):
        self._log_section("Checking for events with missing localisation keys...")

        meta, _ = self._get_event_metadata()
        if not meta:
            self.log("  No events in scope — skipping")
            self._report(
                [],
                "✓ All event localisation keys are defined",
                "Events with missing localisation keys:",
                Severity.WARNING,
                category="missing-event-localisation",
            )
            return
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
                    results.append(
                        (f"{eid}: missing loc key '{key}'", ev["path"], ev["line"])
                    )

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
        triggered_only_ids: Dict[str, dict] = {
            ev["id"]: ev
            for ev in meta
            if ev["id"] is not None
            and ev["is_triggered_only"]
            and ev["id"] not in _EXEMPT_UNREFERENCED_EVENT_IDS
        }

        self.log(
            f"  Found {len(triggered_only_ids)} triggered-only events — scanning for references..."
        )
        # Staged mode cannot scan only staged files (fires live elsewhere) and
        # the full-tree walk is a warning-only CI audit, so commit skips it.
        if not triggered_only_ids or self.staged_only:
            if self.staged_only and triggered_only_ids:
                self.log(
                    "  Staged mode — skipping unreferenced scan; CI covers the full tree"
                )
            else:
                self.log(
                    "  No triggered-only events in scope — skipping reference scan"
                )
            self._report(
                [],
                "✓ All triggered-only events are referenced somewhere",
                "Triggered-only events with no references found:",
                Severity.WARNING,
                category="unreferenced-triggered-only",
            )
            return

        shared = self._get_shared_call_site_scan()
        total_counts: Dict[str, int] = dict(shared["counts"])

        dynamic_namespaces: Set[str] = set(shared["dynamic"])

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
            ev = triggered_only_ids[eid]
            results.append((f"{eid}: no references found", ev["path"], ev["line"]))

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
        gated: List[Tuple[str, str, int]] = self._pool_flat_map(
            partial(scan_date_gated_events, mod_path=self.mod_path),
            gated_args,
            chunksize=10,
        )
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
        sources = self._get_fire_sources()
        scheduled = {
            eid for eid, rels in sources.items() if _YEARLY_EFFECTS_REL in rels
        }
        if not scheduled:
            # Without the scheduling file every date-gated event would be
            # reported, so a rename must skip the check rather than flood it.
            self.log(f"  {_YEARLY_EFFECTS_REL} schedules nothing, skipping")
            return None

        # Lookup pass: a staged event's parent almost always lives elsewhere.
        graph_args: List[Tuple[str, str]] = [
            (f, self.mod_path)
            for f in self._collect_files(["events/**/*.txt"], ignore_staged=True)
        ]
        parents: Dict[str, Set[str]] = {}
        for pairs in self._pool_map(
            _cached_scan_event_fire_graph, graph_args, chunksize=10
        ):
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

    def validate_scheduled_date_bounds(self):
        """Flag scheduled events whose own trigger still carries a date bound.

        A `trigger_year_YYYY_events` slot already fixes the year and `days =`
        the day, so a `date` comparison on the event is redundant, and a
        `date <` bound can silently drop the event when `random_days` spills
        past it. Only events whose sole fire source is the yearly effects are
        reported: a second fire path (focus, decision, chain, `random_events`
        pool) may need the guard.
        """
        self._log_section(
            "Checking scheduled events for redundant date bounds in their trigger..."
        )

        bounded_args = [
            (f, frozenset()) for f in self._collect_files(["events/**/*.txt"])
        ]
        bounded: List[Tuple[str, str, int]] = self._pool_flat_map(
            partial(scan_date_bounded_events, mod_path=self.mod_path),
            bounded_args,
            chunksize=10,
        )
        self.log(f"  Found {len(bounded)} events with a date bound")
        if not bounded:
            self._report(
                [],
                "✓ No scheduled event carries a redundant date bound",
                f"Events scheduled from {_YEARLY_EFFECTS_REL} with a redundant date bound:",
                Severity.ERROR,
                category="scheduled-event-date-bound",
            )
            return

        sources = self._get_fire_sources()
        if not any(_YEARLY_EFFECTS_REL in rels for rels in sources.values()):
            self.log(f"  {_YEARLY_EFFECTS_REL} schedules nothing, skipping")
            return

        pool_ids = self._get_random_event_ids()
        results = [
            f"{eid} - {self._rel_posix(filename)}:{line} is scheduled from "
            f"{_YEARLY_EFFECTS_REL}, so the date bound in its trigger is redundant "
            "(remove it; drop the trigger block if nothing else is left)"
            for eid, filename, line in sorted(bounded)
            if sources.get(eid) == {_YEARLY_EFFECTS_REL} and eid not in pool_ids
        ]
        self._report(
            results,
            "✓ No scheduled event carries a redundant date bound",
            f"Events scheduled from {_YEARLY_EFFECTS_REL} with a redundant date bound:",
            Severity.ERROR,
            category="scheduled-event-date-bound",
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
        mtth_triggered = [
            ev for ev in meta if ev["has_mtth"] and ev["is_triggered_only"]
        ]
        if not mtth_triggered:
            self._report(
                [],
                "✓ No triggered-only events with mean_time_to_happen",
                "Events with mean_time_to_happen AND is_triggered_only (MTTH does nothing — remove one):",
                Severity.WARNING,
                category="mtth-triggered-only",
            )
            return
        random_event_ids = self._get_random_event_ids()
        results = []

        for ev in mtth_triggered:
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
        hidden_with_loc = [
            ev for ev in meta if ev["is_hidden"] and ev["title_desc_refs"]
        ]
        if not hidden_with_loc:
            self._report(
                [],
                "✓ No hidden events with pointless localisation",
                "Hidden events with localisation keys (hidden events display nothing — remove these keys):",
                Severity.WARNING,
                category="hidden-event-localisation",
            )
            return
        loc_keys = self._load_localisation_keys()
        results = []

        for ev in hidden_with_loc:
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

    def validate_hidden_event_pictures(self):
        """Flag hidden events that still declare a picture.

        A hidden event opens no window, so the picture is never drawn and the
        field is dead. Only the event's own picture counts — a portrait inside a
        nested character block is not the event's.
        """
        self._log_section("Checking hidden events for pointless pictures...")

        meta, _ = self._get_event_metadata()
        results = [
            f"{ev['id'] or 'unknown'} - {ev['file']}"
            for ev in meta
            if ev["is_hidden"] and ev["picture_refs"]
        ]

        self._report(
            results,
            "✓ No hidden events with pictures",
            "Hidden events declaring a picture (hidden events display nothing — remove the field):",
            Severity.ERROR,
            category="hidden-event-picture",
        )

    def validate_event_picture_formats(self):
        """Flag pictures whose art is authored for the other event window.

        News art is roughly 397x153 and country art 217x163, and each window
        draws its picture at the texture's native size, so a swap overflows the
        frame or leaves a gap. Hidden events are skipped — nothing renders.

        Reports as ERROR: the #3993 backlog is cleared, so this gates --strict.
        """
        self._log_section("Checking event pictures match their window...")

        meta, _ = self._get_event_metadata()
        candidates = [
            ev
            for ev in meta
            if ev["type"] in ("country_event", "news_event")
            and not ev["is_hidden"]
            and ev["picture_refs"]
        ]
        if not candidates:
            self.log("  No event pictures in scope — skipping")
            return

        # Built sequentially for the reason validate_event_pictures documents,
        # and without vanilla because MD must not use vanilla event pictures.
        textures = build_sprite_texture_index(self.mod_path, include_vanilla=False)
        if len(textures) < 1000:
            self.log(
                f"  Only {len(textures)} GFX textures loaded from "
                f"{os.path.join(self.mod_path, 'interface')}/*.gfx — sprite "
                "definitions did not load; skipping the picture format check",
                "warning",
            )
            return

        results = []
        for ev in candidates:
            for sprite, line in ev["picture_refs"]:
                message = _picture_format_message(
                    ev["type"], ev["id"] or "unknown", sprite, textures
                )
                if message:
                    results.append((message, ev["file"], line))

        self._report(
            results,
            "✓ All event pictures use art sized for their window",
            "Event pictures using art authored for the other event window:",
            Severity.ERROR,
            category="event-picture-format-mismatch",
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
        for matches in [self._get_shared_call_site_scan()["invalid"]]:
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

        if self._skip_call_site_check(
            "✓ Event call types match their declarations",
            "Event calls using the wrong effect type:",
            "event-fire-type-mismatch",
        ):
            return
        definitions = self._get_event_definition_types()
        results = []
        typed_fires: List[Tuple[str, str, str, int]] = list(
            self._get_shared_call_site_scan()["typed"]
        )
        for eid, call_type, filename, line in typed_fires:
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

        if self._skip_call_site_check(
            "✓ Every fired event ID resolves to a defined event",
            "Fires at undefined event IDs (silently do nothing):",
            "undefined-event-fire",
        ):
            return
        shared = self._get_shared_call_site_scan()

        # The definition scan must also cover the full repo in staged mode: a
        # staged caller's target event almost always lives in an unstaged file.
        defined = set(self._get_event_definition_types())
        self.log(f"  Found {len(defined)} defined event IDs")

        dynamic_namespaces: Set[str] = set(shared["dynamic"])

        seen: Dict[str, Tuple[str, int]] = {}
        fires: List[Tuple[str, str, int]] = list(shared["fires"])
        for eid, filename, line in fires:
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

    def validate_event_picture_omissions(self):
        """Flag visible news events that declare no picture of their own.

        Reads `picture_refs` (depth 0 of the event body) rather than a body-wide
        scan, so a `create_country_leader = { picture = ... }` portrait nested
        in an option or `immediate` block does not count as the event's picture.
        The finding names the fix, since the group header is not rendered.
        Country events may omit their picture, so only news events are checked.
        """
        self._log_section("Checking visible news events have pictures...")

        meta, _ = self._get_event_metadata()
        omitted = [
            (
                f"{ev['id'] or 'unknown'}: event has no picture, "
                "add `picture = GFX_<sprite>` below `desc =`",
                ev["file"],
                ev["line"],
            )
            for ev in meta
            if ev["type"] == "news_event"
            and not ev["is_hidden"]
            and not ev["picture_refs"]
        ]

        self._report(
            omitted,
            "✓ All visible news events have pictures",
            "News events with no picture (add `picture = GFX_<sprite>` below `desc =`):",
            Severity.ERROR,
            category="news-event-picture-omitted",
        )

    def validate_placeholder_event_pictures(self):
        """Flag events whose own picture is one of the drafting stand-in sprites."""
        self._log_section("Checking for events using placeholder pictures...")

        meta, _ = self._get_event_metadata()
        results = [
            (f"{ev['id'] or 'unknown'} - {sprite}", ev["file"], line)
            for ev in meta
            for sprite, line in ev["picture_refs"]
            if sprite in _PLACEHOLDER_PICTURES
        ]

        self._report(
            results,
            "✓ No events use a placeholder picture",
            "Events using placeholder art (replace with real event art):",
            Severity.ERROR,
            category="placeholder-event-picture",
        )

    def validate_event_pictures(self):
        """Flag events whose `picture = GFX_x` sprite is not MD-defined.

        An event's picture resolves directly to the named sprite. MD events must
        not rely on vanilla event pictures, so this checks against the mod's own
        interface/*.gfx only (no vanilla) — which also keeps it accurate in CI,
        where the vanilla install is absent. A missing sprite renders a blank
        picture box, so it is an error.
        """
        self.validate_event_picture_omissions()
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
        refs = self._pool_map(
            partial(_extract_event_pictures, mod_path=self.mod_path), files
        )

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

        if self._skip_call_site_check(
            "✓ No fire_only_once events fired inside iterators",
            "fire_only_once events fired inside iterators (only the first recipient gets it):",
            "fire-only-once-in-loop",
        ):
            return

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

        results = list(self._get_shared_call_site_scan()["fof"])

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

    def validate_major_event_in_loop(self):
        """Flag major events fired inside an every_*/for_each_* iterator.

        A ``major = yes`` event already broadcasts to every country on each
        fire. Inside an iterating scope that becomes one broadcast per
        iteration (N countries, N popups; worse in MP). A pinned ROOT/TAG
        scope does not exempt it: the same global broadcast still repeats.
        Non-major news_event fires inside every_country are the per-country
        notification pattern and are not flagged.
        """
        self._log_section("Checking for major events fired inside iterators...")

        if self._skip_call_site_check(
            "✓ No major events fired inside iterators",
            "major events fired inside iterators (each iteration broadcasts to every country):",
            "major-event-in-loop",
        ):
            return

        major_ids = frozenset(self._get_major_event_ids())
        if not major_ids:
            self.log("  No major events defined — skipping")
            self._report(
                [],
                "✓ No major events fired inside iterators",
                "major events fired inside iterators (each iteration broadcasts to every country):",
                category="major-event-in-loop",
            )
            return
        results = list(self._get_shared_call_site_scan()["major"])

        # ERROR: the 9-site pre-existing backlog was cleared.
        self._report(
            results,
            "✓ No major events fired inside iterators",
            "major events fired inside every_*/for_each_* iterators"
            " (each iteration broadcasts to every country; fire the event"
            " once outside the loop):",
            Severity.ERROR,
            category="major-event-in-loop",
        )

    def validate_option_log_without_effect(self):
        """Flag `log` lines in event options that run no effects.

        An option carrying only `name`, `log`, `trigger` and `ai_chance` changes
        nothing, so its log records a state change that never happened.
        """
        self._log_section("Checking event options for logs without effects...")
        files = self._collect_files(["events/**/*.txt"])
        if not files:
            self.log("  No event files in scope — skipping")
            return
        results: List[str] = []
        for sub in self._pool_map(
            partial(_extract_option_logs_without_effects, mod_path=self.mod_path), files
        ):
            for name, filename, line in sub:
                results.append(f"{os.path.basename(filename)}:{line} - {name}")
        self._report(
            sorted(results),
            "✓ No event option logs without effects",
            "Event options with a log but no effects (the option changes nothing"
            " — remove the log line):",
            Severity.ERROR,
            category="event-option-log-without-effect",
        )

    def validate_option_log_id(self):
        """Flag option logs that cite another option's id.

        Shares detection with check_common_mistakes._iter_event_log_mismatches
        and tools/linting/fix_log_ids.py.
        """
        self._log_section("Checking event option logs for copied ids...")
        files = self._collect_files(["events/**/*.txt"])
        if not files:
            self.log("  No event files in scope — skipping")
            return
        results: List[str] = []
        for sub in self._pool_map(
            partial(_extract_event_log_id_mismatches, mod_path=self.mod_path), files
        ):
            for message, filename, line in sub:
                results.append(f"{os.path.basename(filename)}:{line} - {message}")
        self._report(
            sorted(results),
            "✓ No event option logs citing another option's id",
            "Event options whose log cites another option's id"
            " (likely copy-paste — fix the log id):",
            Severity.ERROR,
            category="event-option-log-id",
        )

    def _option_cost_weight_rows(
        self,
    ) -> Optional[Tuple[List[Tuple[str, str, int]], List[Tuple[str, str, int]]]]:
        """Both AI weight cost checks' rows from one pass, or None with no files."""

        def scan():
            files = self._collect_files(["events/**/*.txt"])
            if not files:
                return None
            blind: List[Tuple[str, str, int]] = []
            unneeded: List[Tuple[str, str, int]] = []
            for file_blind, file_unneeded in self._pool_map_init(
                partial(_extract_option_cost_weights, mod_path=self.mod_path),
                files,
                _init_cost_lookups,
                load_cost_lookups(self),
            ):
                blind.extend(file_blind)
                unneeded.extend(file_unneeded)
            return (
                sorted(blind, key=lambda r: (r[1], r[2])),
                sorted(unneeded, key=lambda r: (r[1], r[2])),
            )

        return self.cached("option_cost_weights", scan)

    def validate_ai_chance_ignores_cost(self):
        """Warn on cost-insensitive AI weights when enabled by CLI or the CI batch."""
        if not self.check_ai_chance_costs:
            self._log_section(
                "Skipping AI weight cost check (pass --check-ai-chance-costs to enable)"
            )
            return
        self._log_section("Checking event options for AI weights that ignore costs...")
        rows = self._option_cost_weight_rows()
        if rows is None:
            self.log("  No event files in scope — skipping")
            return
        self._report(
            rows[0],
            "✓ No event AI weights ignoring option costs",
            "Event options whose ai_chance ignores a cost (add a relevant modifier"
            " in the choosing country's scope):",
            Severity.WARNING,
            category="event-ai-chance-ignores-cost",
        )

    def validate_unneeded_treasury_checks(self):
        """Warn on ai_chance treasury checks for a cost the option does not have.

        The inverse of validate_ai_chance_ignores_cost, from the same pass and
        behind the same flag. See unneeded_treasury_reason.
        """
        if not self.check_ai_chance_costs:
            self._log_section(
                "Skipping AI treasury check scan (pass --check-ai-chance-costs to enable)"
            )
            return
        self._log_section("Checking event options for treasury checks with no cost...")
        rows = self._option_cost_weight_rows()
        if rows is None:
            self.log("  No event files in scope — skipping")
            return
        self._report(
            rows[1],
            "✓ No event AI treasury checks without a cost",
            "Event options whose ai_chance lowers the weight on a treasury check the"
            " option has no cost for (drop the modifier, or add the missing cost):",
            Severity.WARNING,
            category="event-unneeded-treasury-guard",
        )

    def validate_corruption_pp_cost(self):
        """Warn when paid event options can waste PP at the minimum corruption level."""
        if not self.check_corruption_pp_costs:
            self._log_section(
                "Skipping event corruption PP cost check "
                "(pass --check-corruption-pp-costs to enable)"
            )
            return
        self._log_section(
            "Checking event options for paid corruption decreases without a level-1 guard..."
        )
        files = self._collect_files(["events/**/*.txt"])
        if not files:
            self.log("  No event files in scope — skipping")
            return
        results: List[Tuple[str, str, int]] = []
        for sub in self._pool_map(
            partial(_extract_corruption_pp_cost_options, mod_path=self.mod_path), files
        ):
            results.extend(sub)
        self._report(
            sorted(results, key=lambda result: (result[1], result[2])),
            "✓ No charged event corruption decreases omit a level-1 guard",
            "Event options needing review for a PP charge with decrease_corruption "
            "and no recognized local minimum-corruption guard:",
            Severity.WARNING,
            category="event-corruption-pp-cost",
        )

    def run_validations(self):
        self.validate_unsupported_title_desc()
        self.validate_missing_triggered_only()
        self.validate_event_call_long_form()
        self.validate_triggered_only_unreferenced()
        self.validate_date_gated_scheduling()
        self.validate_scheduled_date_bounds()
        self.validate_missing_localisation()
        self.validate_mtth_triggered_only()
        self.validate_hidden_event_options()
        self.validate_hidden_event_localisation()
        self.validate_hidden_event_pictures()
        self.validate_duplicate_event_ids()
        self.validate_namespace_mismatch()
        self.validate_invalid_event_calls()
        self.validate_event_fire_types()
        self.validate_undefined_event_fires()
        self.validate_event_pictures()
        self.validate_placeholder_event_pictures()
        self.validate_event_picture_formats()
        self.validate_fire_only_once_in_loop()
        self.validate_major_event_in_loop()
        self.validate_option_log_without_effect()
        self.validate_option_log_id()
        self.validate_corruption_pp_cost()
        self.validate_ai_chance_ignores_cost()
        self.validate_unneeded_treasury_checks()


def _add_extra_args(parser):
    parser.add_argument(
        "--check-ai-chance-costs",
        action="store_true",
        dest="check_ai_chance_costs",
        help="Report event options whose ai_chance ignores the option's cost",
    )
    parser.add_argument(
        "--check-corruption-pp-costs",
        action="store_true",
        dest="check_corruption_pp_costs",
        help=(
            "Warn on event options that charge political power to decrease "
            "corruption without a minimum-corruption guard"
        ),
    )


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate events in Millennium Dawn mod",
        extra_args_fn=_add_extra_args,
    )
