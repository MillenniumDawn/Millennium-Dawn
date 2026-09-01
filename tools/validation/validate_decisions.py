#!/usr/bin/env python3
"""Validate decision definitions and usage in Millennium Dawn.

Based on Kaiserreich Autotests by Pelmen (https://github.com/Pelmen323),
adapted for Millennium Dawn with multiprocessing.
"""

import bisect
import glob
import os
import re
import sys
from pathlib import Path
from typing import AbstractSet, Any, Dict, List, Optional, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import disk_cache
from image_size import read_image_size
from shared_utils import (
    ai_only_decision_categories,
    atomic_write_text,
    blank_quoted_strings,
    direct_child_block,
    extract_block_from_text,
    first_flat_match,
    flat_block_text,
    has_flat_is_ai,
    iter_flat_offsets,
    read_text_strict,
    strip_comments,
    strip_inline_comment,
)
from sprite_index import build_sprite_index, build_sprite_texture_index
from validator_common import (
    DEFAULT_EXTRA_SKIP_PATTERNS,
    BaseValidator,
    Colors,
    FileOpener,
    Severity,
    run_validator_main,
    should_skip_file,
)

EXTRA_SKIP_PATTERNS = DEFAULT_EXTRA_SKIP_PATTERNS

_DECISION_REFERENCE_SOURCE_PATTERNS = (
    "common/**/*.txt",
    "events/**/*.txt",
    "history/**/*.txt",
)


def _should_skip(filename: str) -> bool:
    return should_skip_file(filename, extra_skip_patterns=EXTRA_SKIP_PATTERNS)


_TARGETED_BLOCK_RE = re.compile(
    r"\bactivate_targeted_decision\s*=\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}"
)
_DECISION_NAME_RE = re.compile(r"\bdecision\s*=\s*(\S+)")
_MISSION_NAME_RE = re.compile(r"\bactivate_mission\s*=\s*(\S+)")
_BRACKETED_LOC_RE = re.compile(r"^\[([A-Za-z0-9_]+)\]$")
_SCRIPTED_LOC_RE = re.compile(r"\bname\s*=\s*([A-Za-z0-9_]+)")

# The four blocks the engine runs as a decision's effects, all of which log.
EFFECT_BLOCKS = (
    "complete_effect",
    "remove_effect",
    "timeout_effect",
    "cancel_effect",
)
_LOG_STRING_RE = re.compile(r'\blog\s*=\s*"')
_STATEMENT_NAME_RE = re.compile(r"([A-Za-z_]\w*)\s*=")

# Icon/picture sprite references (_extract_decision_icons). `.` and `-` stay
# inside the character class: they are part of a sprite name, not a delimiter
# (GFX_CTC.5, GFX_MIG-29-GER), a regression sprite_reference_test.py pins.
_SPRITE_VALUE = r'"?([A-Za-z0-9_.\-]+)"?'
_DEC_ICON_SIMPLE_RE = re.compile(
    r"^[ \t]*icon\s*=\s*(?!\{)" + _SPRITE_VALUE + r"[ \t]*\r?$", re.MULTILINE
)
_DEC_ICON_BLOCK_RE = re.compile(r"^[ \t]*icon\s*=\s*\{", re.MULTILINE)
_DEC_ICON_KEY_RE = re.compile(r"\bkey\s*=\s*" + _SPRITE_VALUE)
_DEC_PICTURE_RE = re.compile(
    r"^[ \t]*picture\s*=\s*" + _SPRITE_VALUE + r"[ \t]*\r?$", re.MULTILINE
)
# The token naming a block, read backwards from its opening brace.
_DEC_OWNER_RE = re.compile(r"([A-Za-z0-9_.]+)\s*=\s*$")


def _owner_spans(text: str, want_depth: int) -> List[Tuple[int, int, str]]:
    """Return (start, end, token) for every named block opened at *want_depth*.

    A decision id sits one level inside its category block (depth 1); a category
    definition is at file level (depth 0). Selecting by depth rather than by
    "nearest `x = {` above" keeps a one-line `visible = { ... }` sitting between
    the id and its `icon` from being reported as the owner.
    """
    spans: List[Tuple[int, int, str]] = []
    stack: List[Tuple[int, str]] = []
    for m in re.finditer(r"[{}]", text):
        pos = m.start()
        if m.group() == "{":
            name = _DEC_OWNER_RE.search(text, max(0, pos - 128), pos)
            stack.append((pos, name.group(1) if name else ""))
        elif stack:
            start, token = stack.pop()
            if len(stack) == want_depth and token:
                spans.append((start, pos, token))
    return spans


_ICON_KIND_FIELD = {
    "decision": "icon",
    "category_icon": "icon",
    "category_picture": "picture",
}


def _sprite_candidates(kind: str, value: str) -> List[str]:
    """Return the sprite names the engine tries for one icon/picture value.

    A decision `icon = X` resolves to X verbatim when it is already a full
    sprite name, otherwise the engine prepends `GFX_decision_` (bare names are
    the dominant MD convention and are NOT a bug). A decision *category* uses
    the `GFX_decision_category_` prefix instead, and a category `picture` is
    always the full sprite name.
    """
    if kind == "category_picture" or value.startswith("GFX_"):
        return [value]
    if kind == "category_icon":
        return [value, f"GFX_decision_category_{value}"]
    return [value, f"GFX_decision_{value}", f"GFX_{value}"]


def _missing_sprite_message(
    kind: str, owner: str, value: str, sprites: frozenset
) -> Optional[str]:
    """Return a finding message when no candidate sprite is defined, else None.

    Dynamic `[...]` values resolve at runtime, so they are skipped.
    """
    if "[" in value or "]" in value:
        return None
    candidates = _sprite_candidates(kind, value)
    if sprites.intersection(candidates):
        return None
    tried = " / ".join(candidates)
    return (
        f"{owner}: {_ICON_KIND_FIELD[kind]} = {value} -> no sprite {tried} defined "
        "in interface/*.gfx (create the sprite or pick an existing icon)"
    )


_SLOT_LABEL = {
    "decision": "decision icon",
    "category_icon": "category icon",
    "category_picture": "category picture",
}

# The decision UI draws each sprite at its texture's native size — the category
# tab's `icon` (interface/countrydecisionview.gui:97) and the decision row's
# (:411) both declare a position and no size — so art from the wrong slot renders
# oversized or shrunken instead of being scaled to fit. MD's decision art comes in
# three size families, keyed here by longest edge. The gaps between the bands are
# deliberate: MD has a handful of in-between textures (a 38x38 category icon, a
# 38x40 decision icon) that read as either family, and reporting those would bury
# the real swaps, so a size that lands in a gap identifies no slot at all.
_SLOT_EDGE_RANGES = (
    ("decision", 0, 36),
    ("category_icon", 48, 79),
    ("category_picture", 80, None),
)
_SLOT_TYPICAL_SIZE = {
    "decision": "32x31",
    "category_icon": "52x40",
    "category_picture": "114x101",
}


def _slot_for_size(width: int, height: int) -> Optional[str]:
    """Return the icon slot a texture of this size is drawn for, if unambiguous."""
    longest = max(width, height)
    for slot, low, high in _SLOT_EDGE_RANGES:
        if low <= longest and (high is None or longest <= high):
            return slot
    return None


def _resolved_sprite(kind: str, value: str, textures: Dict[str, str]) -> Optional[str]:
    """Return the sprite name the engine renders for one icon/picture value."""
    for candidate in _sprite_candidates(kind, value):
        if candidate in textures:
            return candidate
    return None


def _icon_type_message(
    kind: str, owner: str, value: str, textures: Dict[str, str]
) -> Optional[str]:
    """Return a finding when the value's art belongs to a different slot.

    Values that resolve to nothing, or to a texture whose size cannot be read,
    are left to the missing-icon check rather than reported twice.
    """
    if "[" in value or "]" in value:
        return None
    sprite = _resolved_sprite(kind, value, textures)
    if sprite is None:
        return None
    size = read_image_size(textures[sprite])
    if size is None:
        return None
    actual = _slot_for_size(*size)
    if actual is None or actual == kind:
        return None
    return (
        f"{owner}: {_ICON_KIND_FIELD[kind]} = {value} -> {sprite} is "
        f"{size[0]}x{size[1]}, which is {_SLOT_LABEL[actual]} art; a "
        f"{_SLOT_LABEL[kind]} is {_SLOT_TYPICAL_SIZE[kind]}"
    )


def _is_category_file(filepath: str) -> bool:
    return "decisions/categories/" in filepath.replace("\\", "/")


def _extract_decision_icons(args: Tuple[str, str]) -> List[Tuple[str, str, str, int]]:
    """Pool worker: return (owner, kind, value, line) for each sprite reference.

    Covers a decision's `icon`, a category's `icon` and `picture`, and the
    dynamic `icon = { key = ... trigger = { ... } }` form, which contributes one
    entry per `key`.
    """
    filepath, mod_path = args
    try:
        text = strip_comments(read_text_strict(filepath))
    except FileNotFoundError:
        return []
    is_category = _is_category_file(filepath)
    icon_kind = "category_icon" if is_category else "decision"

    def _compute() -> List[Tuple[str, str, str, int]]:
        # Owner spans and newline offsets are collected once and bisected per
        # reference; rescanning from the top for every icon is quadratic on the
        # bigger decision files.
        owners = _owner_spans(text, 0 if is_category else 1)
        owner_starts = [s for s, _, _ in owners]
        newlines = [i for i, ch in enumerate(text) if ch == "\n"]

        refs: List[Tuple[int, str, str]] = []
        for m in _DEC_ICON_SIMPLE_RE.finditer(text):
            refs.append((m.start(), icon_kind, m.group(1)))
        for m in _DEC_ICON_BLOCK_RE.finditer(text):
            block, end = extract_block_from_text(text, m.start())
            if end == -1:
                continue
            for km in _DEC_ICON_KEY_RE.finditer(block):
                refs.append((m.start(), icon_kind, km.group(1)))
        if is_category:
            for m in _DEC_PICTURE_RE.finditer(text):
                refs.append((m.start(), "category_picture", m.group(1)))

        out: List[Tuple[str, str, str, int]] = []
        for offset, kind, value in sorted(refs):
            idx = bisect.bisect_right(owner_starts, offset) - 1
            owner = "<unknown>"
            if idx >= 0 and offset < owners[idx][1]:
                owner = owners[idx][2]
            line = bisect.bisect_right(newlines, offset) + 1
            out.append((owner, kind, value, line))
        return out

    return disk_cache.per_file_cached_by_content(
        mod_path, "decisions.icons", filepath, text, _compute
    )


def _block_level_statements(block: str) -> List[str]:
    """Statement names at an effect block's own level, in source order.

    *block* is the ``{ ... }`` text of the block. Nested blocks are skipped, so
    a ``log`` inside an ``if`` / ``hidden_effect`` does not read as a statement
    of the block itself.
    """
    names: List[str] = []
    depth = 0
    for line in block.split("\n"):
        code = blank_quoted_strings(strip_inline_comment(line))
        i = 0
        while i < len(code):
            char = code[i]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
            elif depth == 1:
                match = _STATEMENT_NAME_RE.match(code, i)
                if match:
                    names.append(match.group(1))
                    i = match.end()
                    continue
            i += 1
    return names


# --- Decision parsing helpers ---

_REMOVE_DECISION_RE = re.compile(r"\bremove_decision\s*=\s*(\w+)")
_REMOVE_TARGETED_BLOCK_RE = re.compile(
    r"\bremove_targeted_decision\s*=\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}"
)
_REMOVE_DECISION_NAME_RE = re.compile(r"\bdecision\s*=\s*(\S+)")

_CYBER_OPERATION_TYPES = (
    "gps_tracking",
    "economic_tracking",
    "propaganda_tracking",
    "infra_tracking",
    "crit_tracking",
    "sigint_surveillance_tracking",
    "radar_spoofing_tracking",
    "election_interference_tracking",
    "industrial_espionage_tracking",
    "comms_intercept_tracking",
    "financial_system_attack_tracking",
    "logistics_disruption_tracking",
    "sleeper_network_tracking",
    "deception_campaign_tracking",
    "zero_day_strike_tracking",
    "network_hardening_tracking",
    "counter_intrusion_tracking",
    "attribution_hunt_tracking",
)
_DYNAMIC_ACTIVATION_EXPANSIONS = {
    "cyber_op_slot_[SLOT]_[TYPE]": {
        f"cyber_op_slot_{slot}_{operation_type}"
        for slot in range(10)
        for operation_type in _CYBER_OPERATION_TYPES
    },
    "investments_project_[INDEX]_target_decision": {
        f"investments_project_{index}_target_decision" for index in range(15)
    },
}


def _unactivated(candidates: set, activated: set) -> list:
    """Sorted *candidates* with no literal or finite meta-effect activation."""
    remaining = candidates - activated
    for name in activated:
        remaining.difference_update(_DYNAMIC_ACTIVATION_EXPANSIONS.get(name, ()))
    return sorted(remaining)


_UNLOCK_CATEGORY_RE = re.compile(
    r"unlock_decision_category_tooltip\s*=\s*([A-Za-z0-9_]+)"
)
_UNLOCK_DECISION_RE = re.compile(r"unlock_decision_tooltip\s*=\s*([A-Za-z0-9_]+)")
# State that flips on during play, so the category it gates appears mid-game.
_MIDGAME_GATE_RE = re.compile(
    r"\b(?:has_country_flag|has_global_flag|has_completed_focus|has_idea)"
    r"\s*=\s*[A-Za-z0-9_]+|\bcheck_variable\b"
)
_FLAG_GATE_RE = re.compile(r"has_(?:country|global)_flag\s*=\s*([A-Za-z0-9_]+)")
# Both the bare form and the timed `set_country_flag = { flag = X days = N }`.
_SET_FLAG_RE = re.compile(
    r"set_(?:country|global)_flag\s*=\s*(?:([A-Za-z0-9_]+)"
    r"|\{[^{}]*?flag\s*=\s*([A-Za-z0-9_]+))"
)
_UNLOCK_IN_EFFECT_RE = re.compile(r"unlock_decision_tooltip\s*=\s*([A-Za-z0-9_]+)")


def _flat_flag_gates(block: str) -> Set[str]:
    """Flags a trigger block waits on positively, at depth 0.

    Depth 0 only: `NOT = { has_country_flag = X }` is satisfied *until* X is set,
    so treating it as a gate X opens inverts the meaning.
    """
    flags: Set[str] = set()
    if not block:
        return flags
    for inner, index in iter_flat_offsets(block):
        if index and not inner[index - 1].isspace():
            continue
        match = _FLAG_GATE_RE.match(inner, index)
        if match:
            flags.add(match.group(1))
    return flags


def _scan_activations_and_removals(filename: str) -> Tuple[set, set, set, set]:
    """Single-read worker: (activated, missions, removed, announced).

    Combines the activation, external-removal and unlock-tooltip scans so the
    full-repo .txt sweep reads each file once instead of three times.
    `announced` holds both the categories and the individual decisions that some
    focus or effect tells the player it has unlocked.
    """
    if _should_skip(filename):
        return set(), set(), set(), set()
    text_file = FileOpener.open_text_file(
        filename, lowercase=False, strip_comments_flag=True
    )
    decisions: set = set()
    missions: set = set()
    removals: set = set()
    announced: set = set()
    if "activate_targeted_decision" in text_file:
        for block in _TARGETED_BLOCK_RE.findall(text_file):
            decisions.update(_DECISION_NAME_RE.findall(block))
    if "activate_mission" in text_file:
        missions.update(_MISSION_NAME_RE.findall(text_file))
    if "remove_decision" in text_file or "remove_targeted_decision" in text_file:
        removals.update(_REMOVE_DECISION_RE.findall(text_file))
        for block in _REMOVE_TARGETED_BLOCK_RE.findall(text_file):
            removals.update(_REMOVE_DECISION_NAME_RE.findall(block))
    if "unlock_decision_category_tooltip" in text_file:
        announced.update(_UNLOCK_CATEGORY_RE.findall(text_file))
    if "unlock_decision_tooltip" in text_file:
        announced.update(_UNLOCK_DECISION_RE.findall(text_file))
    return decisions, missions, removals, announced


def _load_scripted_localisation_keys(mod_path: str) -> set:
    keys = set()
    pattern = os.path.join(mod_path, "common", "scripted_localisation", "*.txt")
    for filename in glob.iglob(pattern):
        if _should_skip(filename):
            continue
        text_file = FileOpener.open_text_file(
            filename, lowercase=False, strip_comments_flag=True
        )
        if "defined_text" in text_file and "name =" in text_file:
            keys.update(_SCRIPTED_LOC_RE.findall(text_file))
    return keys


_TAG_TOKEN_PATTERN = re.compile(r"\b(original_tag|tag)\s*=\s*([A-Z][A-Z0-9_]{1,7})\b")

# Decision-block / category-block parsing patterns (hoisted from cached
# closures in parse_all_decisions / parse_all_decision_names /
# parse_decision_categories / parse_categories_with_decisions).
# The name is confined to its own line (`[^\t#\n]`): allowing newlines let the
# non-greedy match jump from a stray `\t}` across blank lines into a column-0
# decision, producing a bogus block with no name line.
_DECISIONS_BLOCK_RE = re.compile(
    r"^\t[^\t#\n]+?\s*=\s*\{.*?^\t\}", flags=re.MULTILINE | re.DOTALL
)
_DECISION_TOKEN_LINE_RE = re.compile(r"^\t(\S+)\s*=", flags=re.MULTILINE)
_CATEGORY_BLOCK_RE = re.compile(r"^\w* = \{.*?^\}", flags=re.DOTALL | re.MULTILINE)
_CATEGORY_NAME_RE = re.compile(r"^(.*) = \{")
_CATEGORY_DECISION_TOKEN_RE = re.compile(r"^[ \t]+(\S+) = \{", flags=re.MULTILINE)

# FROM-usage detection (hoisted from validate_targets_no_trigger /
# validate_from_without_targets).
_FROM_BLOCK_RE = re.compile(r"\bFROM\s*=\s*\{")
_FROM_WORD_RE = re.compile(r"\bFROM\b")

# Formable commitment ratchet sync (validate_formable_commitment_sync).
_FORMABLE_DECISIONS_BASENAME = "formable_nation_decisions.txt"
_FORMABLE_TAG_RE = re.compile(
    r"^([A-Z0-9]+)_(?:integrate_|buy_core_state$|update_flag$)"
)
_STATE_ENTRY_RE = re.compile(r"\b\d+\s*=\s*\{")
_SIZE_SET_RE = re.compile(r"formable_committed_size\s*=\s*(\d+)")
_SIZE_CMP_RE = re.compile(r"var\s*=\s*formable_committed_size\s+value\s*=\s*(\d+)")
_COMMIT_PAIR_RE = re.compile(
    r"set_variable\s*=\s*\{\s*formable_committed_id\s*=\s*(\d+)\s*\}\s*"
    r"set_variable\s*=\s*\{\s*formable_committed_size\s*=\s*(\d+)\s*\}"
)
_OWN_GATE_ID_RE = re.compile(
    r"NOT\s*=\s*\{\s*check_variable\s*=\s*\{\s*formable_committed_id\s*=\s*(\d+)\s*\}\s*\}"
)
_ID_LITERAL_RE = re.compile(r"formable_committed_id\s*=\s*(\d+)")


def _is_targeted_decision(d: "DecisionFactory") -> bool:
    """True if targets/target_array/target_trigger/target_root_trigger is present."""
    return bool(
        d.targets or d.target_array or d.target_trigger or d.target_root_trigger
    )


def _extract_from_blocks(block: str) -> List[str]:
    """Return the brace-balanced body text of every ``FROM = { ... }`` in *block*.

    ``_FROM_BLOCK_RE`` only matches the opening ``FROM = {``; this walks
    forward to the matching close so callers get the full block body, not
    just the header.
    """
    if not block:
        return []
    bodies = []
    for m in _FROM_BLOCK_RE.finditer(block):
        depth = 1
        i = m.end()
        n = len(block)
        while i < n and depth > 0:
            if block[i] == "{":
                depth += 1
            elif block[i] == "}":
                depth -= 1
            i += 1
        if depth == 0:
            bodies.append(block[m.end() : i - 1])
    return bodies


# Bare trigger names needing a has_ prefix (hoisted from validate_bare_trigger_names).
_BARE_TRIGGERS = {
    "political_power": "has_political_power",
    "stability": "has_stability",
    "war_support": "has_war_support",
    "manpower": "has_manpower",
}
_BARE_TRIGGER_RE = re.compile(
    r"^\t+(" + "|".join(_BARE_TRIGGERS.keys()) + r")\s+[<>]",
    flags=re.MULTILINE,
)


def _flat_tag_pins_with_kind(block: str) -> set:
    """Return {(keyword, tag), ...} for flat (non-nested), depth-0 tag/original_tag tokens.

    Dim-aware sibling of ``_flat_tag_pins``: keeps the keyword ('tag' or
    'original_tag') alongside each pinned tag so callers can tell a
    ``tag = X`` lock (excludes civil-war split-offs) apart from
    ``original_tag = X`` (admits them). Tokens nested inside OR/NOT/AND/if/
    FROM/any_country/TAG={} subblocks are skipped because they are
    conditional or scoped, not flat hard pins.
    """
    if not block:
        return set()
    pins = set()
    for inner, index in iter_flat_offsets(block):
        match = _TAG_TOKEN_PATTERN.match(inner, index)
        if match:
            pins.add((match.group(1), match.group(2)))
    return pins


def _flat_tag_pins(block: str) -> set:
    """Return the set of tags pinned by flat (non-nested) tag/original_tag tokens.

    Tokens nested inside OR/NOT/AND/if subblocks are skipped because they are
    conditional, not hard pins. Handles both multi-line and single-line block
    formats.
    """
    return {tag for _, tag in _flat_tag_pins_with_kind(block)}


def _is_sole_flat_pin(block: str, tag: str) -> bool:
    """True if ``block``'s only content (after comment-stripping) is a single
    flat ``tag = X`` / ``original_tag = X`` pin equal to ``tag``.

    Mirrors the sole-pin shape validate_allowed_redundant_with_category
    already reports, so callers can skip re-flagging it.
    """
    if not block:
        return False
    inner = block.strip()
    if inner.startswith("{"):
        inner = inner[1:]
    if inner.endswith("}"):
        inner = inner[:-1]
    cleaned = re.sub(r"#[^\n]*", "", inner).strip()
    pat = re.compile(r"^\s*(?:original_tag|tag)\s*=\s*" + re.escape(tag) + r"\s*$")
    return bool(pat.match(cleaned))


def _category_allowed_pins(categories: Dict[str, str]) -> Dict[str, set]:
    """Return category name -> {(keyword, tag), ...} pinned by its flat,
    depth-0 ``allowed`` block.

    Categories with no ``allowed`` block are omitted; categories whose
    ``allowed`` has no flat tag pin at all (e.g. a scripted trigger) map to
    an empty set — both read as "no lock" to callers.
    """
    cat_pins: Dict[str, set] = {}
    for cat_name, cat_code in categories.items():
        am = re.search(r"\ballowed\s*=\s*\{", cat_code)
        if not am:
            continue
        a_start = cat_code.find("{", am.start())
        depth = 1
        i = a_start + 1
        while i < len(cat_code) and depth > 0:
            if cat_code[i] == "{":
                depth += 1
            elif cat_code[i] == "}":
                depth -= 1
            i += 1
        cat_pins[cat_name] = _flat_tag_pins_with_kind(cat_code[a_start:i])
    return cat_pins


def _scan_top_level(block: str):
    """Iterate top-level tokens inside a block.

    Yields (kind, payload) pairs where kind is 'tag' or 'scope' and payload
    is the tag string. Tokens nested inside subblocks (OR/AND/NOT/if/
    custom_trigger_tooltip/etc.) are skipped — those are conditional
    context, not unconditional pins.
    """
    if not block:
        return
    for inner, index in iter_flat_offsets(block):
        char = inner[index]
        if not (char.isalpha() or char == "_"):
            continue
        previous = inner[index - 1] if index > 0 else "\n"
        if previous.isalnum() or previous == "_":
            continue
        match = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*", inner[index:])
        if not match:
            continue
        ident = match.group(1)
        after = index + match.end()
        if ident in ("tag", "original_tag"):
            tag_match = re.match(r"([A-Z][A-Z0-9_]{1,7})\b", inner[after:])
            if tag_match:
                yield ("tag", tag_match.group(1))
        elif (
            re.match(r"^[A-Z][A-Z0-9_]{1,7}$", ident)
            and after < len(inner)
            and inner[after] == "{"
        ):
            yield ("scope", ident)


def _find_category_redundant_rows(
    factories: List["DecisionFactory"],
    cat_pins: Dict[str, set],
    cats_with_decs: Dict[str, List[str]],
) -> List[str]:
    """Pure detection: decision-level tag/original_tag re-checks already
    covered by the parent category's single-tag lock.

    Fills the gap between ``validate_redundant_tag_checks`` (decision's own
    ``allowed`` pin vs its own ``visible``/``available``) and
    ``validate_allowed_redundant_with_category`` (sole-content ``allowed``
    duplicating the category pin): neither compares the *category* lock
    against a decision's ``visible``/``available``, or against a partial
    (multi-condition) ``allowed`` block.

    Rules:
    - Only single-tag category locks count: the category's ``allowed`` must
      pin exactly one tag value at depth 0. A scripted-trigger ``allowed``
      (no flat tag/original_tag token) or one pinning several different tags
      yields no lock and is skipped.
    - A category locked via ``original_tag = X`` only flags decision-level
      ``original_tag = X`` re-checks. ``tag = X`` is a real narrowing (it
      excludes civil-war split-offs the ``original_tag`` lock admits), so
      it's left alone.
    - A category locked via ``tag = X`` (with or without an accompanying
      ``original_tag = X`` for the same tag) flags both ``tag = X`` and
      ``original_tag = X`` re-checks — the category is already at least as
      restrictive as either.
    - ``allowed`` is skipped when its only content is the pin itself; that
      exact shape is already reported by
      ``validate_allowed_redundant_with_category``.
    - Depth-0 only, via ``_flat_tag_pins_with_kind``: negations
      (``NOT = {...}``), ``FROM``/``any_country``/``TAG = {}`` scopes are
      auto-excluded. ``target_trigger``/``target_root_trigger`` are separate
      factory fields and are not scanned.
    """
    token_to_cat: Dict[str, str] = {}
    for cat, dec_tokens in cats_with_decs.items():
        for tok in dec_tokens:
            token_to_cat.setdefault(tok, cat)

    results: List[str] = []
    for d in factories:
        cat_name = token_to_cat.get(d.token)
        if cat_name is None:
            continue
        pins = cat_pins.get(cat_name)
        if not pins:
            continue
        tag_values = {tg for _, tg in pins}
        if len(tag_values) != 1:
            continue
        lock_tag = next(iter(tag_values))
        keywords_used = {kw for kw, tg in pins if tg == lock_tag}
        lock_kind = "tag" if "tag" in keywords_used else "original_tag"
        flagged_kinds = (
            {"tag", "original_tag"} if lock_kind == "tag" else {"original_tag"}
        )

        issues = []
        for field_name, block in (
            ("allowed", d.allowed),
            ("available", d.available),
            ("visible", d.visible),
        ):
            if not block:
                continue
            if field_name == "allowed" and _is_sole_flat_pin(block, lock_tag):
                continue
            hits = _flat_tag_pins_with_kind(block)
            for kw in ("original_tag", "tag"):
                if kw in flagged_kinds and (kw, lock_tag) in hits:
                    issues.append(f"{field_name} re-checks {kw}")

        if issues:
            results.append(
                f"{d.token:<55}{d.source_basename} "
                f"(category locked to {lock_kind} = {lock_tag}: {', '.join(issues)})"
            )

    return results


def _group_fixes_by_basename(fixes: list) -> Dict[str, List[str]]:
    grouped: Dict[str, List[str]] = {}
    for token, basename in fixes:
        grouped.setdefault(basename, []).append(token)
    return grouped


def _find_decision_file(mod_path: str, basename: str) -> str | None:
    pattern = str(Path(mod_path) / "common" / "decisions" / "**" / "*.txt")
    return next(
        (
            filepath
            for filepath in glob.iglob(pattern, recursive=True)
            if os.path.basename(filepath) == basename
        ),
        None,
    )


def _int_literal(value: str) -> int:
    """Convert a regex-captured decimal literal to an integer."""
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"invalid decimal literal: {value}") from None


def _is_effectively_ai_only(
    dec: "DecisionFactory", dec_id: str, ai_only_by_category: Set[str]
) -> bool:
    """Whether the decision or its category is gated to AI players."""
    return dec.ai_only or dec_id in ai_only_by_category


def _find_formable_commitment_rows(
    factories: List["DecisionFactory"], focus_texts: Dict[str, str]
) -> List[str]:
    """Drift check for the formable commitment ratchet.

    Every decision in the formables file carries an ``ai_will_do`` gate
    comparing ``formable_committed_size`` against that formable's full state
    count, and the commit sites (integrate_start / update_flag complete_effect,
    the IBR/ANZ remove_effects, Spain's focus tree) store the same id/size
    pair. The counts exist only as inlined literals, so editing an
    update_flag's state list silently corrupts the ratchet ordering — this
    recomputes each count from the update_flag ``available`` block and diffs
    it against every literal.

    ``factories`` must already be restricted to the formables file;
    ``focus_texts`` maps basename -> text for focus files mentioning
    ``formable_committed_``.
    """
    rows: List[str] = []
    by_tag: Dict[str, List["DecisionFactory"]] = {}
    for d in factories:
        m = _FORMABLE_TAG_RE.match(d.token)
        if not m:
            rows.append(
                f"{d.token:<55}{d.source_basename} - not a formable decision shape"
            )
            continue
        by_tag.setdefault(m.group(1), []).append(d)

    canonical: Dict[str, int] = {}
    for tag, decs in by_tag.items():
        uf = next((d for d in decs if d.token == f"{tag}_update_flag"), None)
        if uf is None or not uf.available:
            rows.append(f"{tag}: no update_flag available block - cannot derive size")
            continue
        canonical[tag] = len(_STATE_ENTRY_RE.findall(uf.available))

    commit_ids: Dict[str, int] = {}
    for tag, decs in by_tag.items():
        if tag not in canonical:
            continue
        size = canonical[tag]
        ids = set()
        for d in decs:
            literals = [
                _int_literal(v)
                for regex in (_SIZE_SET_RE, _SIZE_CMP_RE)
                for v in regex.findall(d.raw)
            ]
            if not literals:
                rows.append(
                    f"{d.token:<55}{d.source_basename} - missing commitment gate (no formable_committed_size literal)"
                )
            for v in literals:
                if v != size:
                    rows.append(
                        f"{d.token:<55}{d.source_basename} - size literal {v} != {tag} update_flag state count {size}"
                    )
            for i, _ in _COMMIT_PAIR_RE.findall(d.raw):
                ids.add(_int_literal(i))
        if len(ids) > 1:
            rows.append(f"{tag}: conflicting commit ids {sorted(ids)}")
        elif ids:
            commit_ids[tag] = next(iter(ids))
        else:
            rows.append(f"{tag}: no commit write (set_variable formable_committed_id)")

    id_owner: Dict[int, str] = {}
    for tag in sorted(commit_ids):
        commit_id = commit_ids[tag]
        if commit_id in id_owner:
            rows.append(
                f"{tag}: commit id {commit_id} collides with {id_owner[commit_id]}"
            )
        else:
            id_owner[commit_id] = tag

    for tag, decs in by_tag.items():
        fid = commit_ids.get(tag)
        for d in decs:
            for g in _OWN_GATE_ID_RE.findall(d.raw):
                if fid is not None and _int_literal(g) != fid:
                    rows.append(
                        f"{d.token:<55}{d.source_basename} - gate id {g} != {tag} commit id {fid}"
                    )
            for ref in _ID_LITERAL_RE.findall(d.raw):
                if id_owner and _int_literal(ref) not in id_owner:
                    rows.append(
                        f"{d.token:<55}{d.source_basename} - references unknown formable id {ref}"
                    )

    size_by_id = {commit_ids[t]: canonical[t] for t in commit_ids if t in canonical}
    for basename, text in focus_texts.items():
        for i, s in _COMMIT_PAIR_RE.findall(text):
            if _int_literal(i) not in size_by_id:
                rows.append(
                    f"{basename}: focus commit references unknown formable id {i}"
                )
            elif _int_literal(s) != size_by_id[_int_literal(i)]:
                rows.append(
                    f"{basename}: focus commit size {s} != update_flag state count {size_by_id[_int_literal(i)]} for id {i}"
                )
        for v in _SIZE_CMP_RE.findall(text):
            if size_by_id and _int_literal(v) not in set(size_by_id.values()):
                rows.append(
                    f"{basename}: focus guard size {v} matches no formable state count"
                )
    return rows


def extract_value_single_line(obj: str, s: str) -> str:
    pattern = r"\t+" + s + r" = (\S*)"
    matches = re.findall(pattern, obj)
    return matches[0] if f"\t{s} =" in obj and matches else ""


def _top_level_field_value(raw: str, field: str):
    """Return the value of ``field = X`` at the top level of a decision body.

    The decision body is at brace depth 1 (depth 0 = before/after the outer
    braces of the decision token). Occurrences nested inside sub-blocks like
    ``complete_effect = { create_ship = { name = ... } }`` are ignored.

    Returns ``None`` if the field is absent at depth 1 or if its value is a
    quoted literal string (which the engine renders verbatim, with no loc
    lookup to verify).
    """
    pat = re.compile(r"\b" + re.escape(field) + r"\s*=\s*(\S+)")
    depth = 0
    i = 0
    n = len(raw)
    while i < n:
        ch = raw[i]
        if ch == "{":
            depth += 1
            i += 1
            continue
        if ch == "}":
            depth -= 1
            i += 1
            continue
        if ch == "#":
            while i < n and raw[i] != "\n":
                i += 1
            continue
        if depth == 1:
            prev = raw[i - 1] if i > 0 else "\n"
            if not (prev.isalnum() or prev == "_"):
                m = pat.match(raw, i)
                if m:
                    value = m.group(1)
                    if value.startswith('"'):
                        return None
                    return value
        i += 1
    return None


def _top_level_neg_pp(block: str):
    """Return the magnitude (positive int) of an unconditional
    ``add_political_power = -N`` at depth 0 of ``block``, or ``None``
    if there is no such line. Conditional/nested subtractions are
    ignored (they are gameplay outcomes, not entry costs)."""
    if not block:
        return None
    for inner, index in iter_flat_offsets(block):
        match = re.match(r"add_political_power\s*=\s*-(\d+)", inner[index:])
        if match:
            return _int_literal(match.group(1))
    return None


def extract_value_multi_line(obj: str, s: str) -> str:
    pattern = r"(\t+)" + s + r" = (\{([^\n]*|.*?^\1)\})"
    if f"\t{s} =" not in obj:
        return ""
    matches = re.findall(pattern, obj, flags=re.DOTALL | re.MULTILINE)
    return matches[0][1] if matches else ""


class DecisionFactory:
    def __init__(self, dec: str, source_basename: str = "") -> None:
        self.source_basename = source_basename
        self.raw = dec
        self.token = re.findall(r"^\t*(\S+)\s*=\s*\{", dec, flags=re.MULTILINE)[0]
        self.allowed = extract_value_multi_line(dec, "allowed")
        self.available = extract_value_multi_line(dec, "available")
        self.visible = extract_value_multi_line(dec, "visible")
        self.cancel_effect = extract_value_multi_line(dec, "cancel_effect")
        self.complete_effect = extract_value_multi_line(dec, "complete_effect")
        self.remove_effect = extract_value_multi_line(dec, "remove_effect")
        self.timeout_effect = extract_value_multi_line(dec, "timeout_effect")
        self.cancel_trigger = extract_value_multi_line(dec, "cancel_trigger")
        self.cancel_if_not_visible = "cancel_if_not_visible = yes" in dec
        self.activation = extract_value_multi_line(dec, "activation")
        self.target_root_trigger = extract_value_multi_line(dec, "target_root_trigger")
        self.target_trigger = extract_value_multi_line(dec, "target_trigger")
        self.targets = extract_value_multi_line(dec, "targets")
        self.target_array = extract_value_single_line(dec, "target_array")
        _st_match = re.search(r"\bstate_target\s*=\s*(\w+)", dec)
        self.state_target_value = _st_match.group(1) if _st_match else None
        self.state_target = (
            self.state_target_value is not None and self.state_target_value != "no"
        )
        self.map_only = "on_map_mode = map_only" in dec
        self.mission_subtype = "\tdays_mission_timeout =" in dec
        self.selectable_mission = (
            "\tdays_mission_timeout =" in dec and "selectable_mission = yes" in dec
        )
        self.ai_factor = extract_value_multi_line(dec, "ai_will_do")
        self.custom_cost_trigger = extract_value_multi_line(dec, "custom_cost_trigger")
        self.custom_cost_text = extract_value_single_line(dec, "custom_cost_text")
        self.ai_hint_pp_cost = extract_value_single_line(dec, "ai_hint_pp_cost")
        self.cost = extract_value_single_line(dec, "cost")
        self.has_tooltip = "tooltip =" in dec
        self.has_random_list = bool(re.search(r"\brandom_list\s*=\s*\{", dec))
        self.has_random_effect = bool(re.search(r"\brandom\s*=\s*\{", dec))
        self.fire_only_once = "fire_only_once = yes" in dec
        self.fixed_random_seed_explicit = bool(
            re.search(r"\bfixed_random_seed\s*=\s*(yes|no)\b", dec)
        )
        self.war_with_on_complete = extract_value_single_line(
            dec, "war_with_on_complete"
        )
        self.war_with_on_remove = extract_value_single_line(dec, "war_with_on_remove")
        self.war_with_on_timeout = extract_value_single_line(dec, "war_with_on_timeout")
        self.has_timeout_effect = "timeout_effect" in dec
        self.has_activation_block = bool(re.search(r"\bactivation\s*=\s*\{", dec))
        self.has_is_good = "is_good" in dec
        self.has_selectable_mission_kw = "selectable_mission = yes" in dec
        self.has_days_remove = "days_remove" in dec
        self.has_remove_trigger = "remove_trigger" in dec
        self.targets_dynamic = "targets_dynamic" in dec
        self.target_non_existing = "target_non_existing" in dec
        # Top-level name/desc overrides redirect the engine's loc lookup.
        # When set, the engine uses these keys instead of the decision id /
        # `<id>_desc` pair. Extract them with brace-depth awareness so we
        # don't pick up nested `name = ...` inside create_ship / create_unit
        # effect sub-blocks.
        self.name_override = _top_level_field_value(dec, "name")
        self.desc_override = _top_level_field_value(dec, "desc")
        # An unconditional `is_ai = yes` hides the decision from every human
        # player, so it needs no localisation. Category-level AI gating is
        # resolved by the validator, which is the only side that knows the
        # decision's parent category.
        self.ai_only = (
            has_flat_is_ai(self.visible)
            or has_flat_is_ai(self.available)
            or has_flat_is_ai(self.allowed)
        )


# Decisions parsing cache - enabled by default, disabled via BaseValidator.no_cache
_DECISION_CACHE: Dict[str, Any] = {"enabled": True, "data": {}}


def _set_cache_enabled(enabled: bool):
    """Enable or disable the decision parsing cache."""
    global _DECISION_CACHE
    _DECISION_CACHE["enabled"] = enabled
    if not enabled:
        _DECISION_CACHE["data"].clear()


def _invalidate_decision_cache():
    """Drop all cached decision data so subsequent parse calls re-read disk.

    Call this after any ``--fix`` pass that rewrites decision files so later
    validators see the patched contents instead of stale factories.
    """
    _DECISION_CACHE["data"].clear()
    FileOpener.clear_cache()


def _get_cached(key: str, mod_path: str, lowercase: bool, factory_fn):
    """Get cached result or compute and cache it."""
    if not _DECISION_CACHE["enabled"]:
        return factory_fn()

    cache_key = f"{mod_path}:{lowercase}:{key}"
    if cache_key not in _DECISION_CACHE["data"]:
        _DECISION_CACHE["data"][cache_key] = factory_fn()
    return _DECISION_CACHE["data"][cache_key]


def parse_all_decisions(
    mod_path: str, lowercase: bool = False
) -> Tuple[List[str], Dict[str, str]]:
    """Parse all decisions with caching."""

    def _parse():
        filepath = str(Path(mod_path) / "common" / "decisions")
        decisions = []
        paths = {}

        for filename in glob.iglob(filepath + "/**/*.txt", recursive=True):
            if "categories" in filename:
                continue
            text_file = FileOpener.open_text_file(
                filename, lowercase=lowercase, strip_comments_flag=True
            )
            # Neutralize quoted strings before block-splitting: a literal `}`
            # inside a `name = "... } ..."` value would otherwise close the
            # block early and drop every field after it. blank_quoted_strings
            # preserves length/offsets, so match spans still slice the real
            # text (quoted fields intact) for downstream extraction.
            blanked = blank_quoted_strings(text_file)
            for m in _DECISIONS_BLOCK_RE.finditer(blanked):
                match = text_file[m.start() : m.end()]
                decisions.append(match)
                paths[match] = os.path.basename(filename)

        return decisions, paths

    return _get_cached("decisions", mod_path, lowercase, _parse)


def parse_all_decision_factories(
    mod_path: str, lowercase: bool = False
) -> List["DecisionFactory"]:
    """Build DecisionFactory instances for every decision and cache them.

    Each factory does ~14 multi-line regex extractions in __init__, so building
    them once and reusing across all validators eliminates the dominant cost of
    a full decisions validation run (was ~7s of ~10s on this mod).

    The source filename is stored on the factory as ``source_basename`` so
    reporting code can avoid re-keying a parallel paths dict.
    """

    def _build():
        decisions, dec_paths = parse_all_decisions(mod_path, lowercase)
        return [DecisionFactory(dec=d, source_basename=dec_paths[d]) for d in decisions]

    return _get_cached("decision_factories", mod_path, lowercase, _build)


def parse_all_decision_names(
    mod_path: str, lowercase: bool = False
) -> Tuple[List[str], Dict[str, str]]:
    """Parse all decision names with caching."""

    def _parse():
        decisions, dec_paths = parse_all_decisions(mod_path, lowercase)
        names = []
        name_paths = {}
        for d in decisions:
            name = _DECISION_TOKEN_LINE_RE.findall(d)[0]
            names.append(name)
            name_paths[name] = dec_paths[d]
        return names, name_paths

    return _get_cached("decision_names", mod_path, lowercase, _parse)


def parse_decision_categories(
    mod_path: str, lowercase: bool = False, visible_when_empty: bool = True
) -> Dict[str, str]:
    """Parse decision categories with caching."""

    def _parse():
        filepath = str(Path(mod_path) / "common" / "decisions" / "categories")
        categories = {}

        for filename in glob.iglob(filepath + "/**/*.txt", recursive=True):
            text_file = FileOpener.open_text_file(
                filename, lowercase=lowercase, strip_comments_flag=True
            )
            matches = _CATEGORY_BLOCK_RE.findall(text_file)
            for match in matches:
                if not visible_when_empty and "visible_when_empty = yes" in match:
                    continue
                name = _CATEGORY_NAME_RE.findall(match)
                if name:
                    categories[name[0]] = match

        return categories

    cache_key = f"categories:{visible_when_empty}"
    return _get_cached(cache_key, mod_path, lowercase, _parse)


def parse_categories_with_decisions(
    mod_path: str, lowercase: bool = False, visible_when_empty: bool = True
) -> Dict[str, List[str]]:
    """Parse categories with their decisions - reuses category cache."""

    def _parse():
        categories = parse_decision_categories(mod_path, lowercase, visible_when_empty)
        category_names = list(categories.keys())

        result = {cat: [] for cat in category_names}

        filepath = str(Path(mod_path) / "common" / "decisions")

        for filename in glob.iglob(filepath + "/**/*.txt", recursive=True):
            if "categories" in filename:
                continue
            text_file = FileOpener.open_text_file(
                filename, lowercase=lowercase, strip_comments_flag=True
            )
            for category in category_names:
                if f"{category} = {{" in text_file:
                    pattern = r"^" + re.escape(category) + r" = \{.*?^\}"
                    matches = re.findall(
                        pattern, text_file, flags=re.DOTALL | re.MULTILINE
                    )
                    for match in matches:
                        dec_names = _CATEGORY_DECISION_TOKEN_RE.findall(match)
                        result[category].extend(dec_names)

        return result

    cache_key = f"cats_with_decs:{visible_when_empty}"
    return _get_cached(cache_key, mod_path, lowercase, _parse)


def _remove_available_block_for_token(content: str, token: str):
    """Remove the ``available = { ... }`` sub-block of a decision named ``token``.

    Uses brace-balanced scanning so nested blocks (``NOT = { ... }``, etc.)
    inside ``available`` are handled correctly. Returns the rewritten content,
    or ``None`` if the token / available block could not be located.
    """
    token_pattern = re.compile(
        r"(^|\n)(\s*)" + re.escape(token) + r"\s*=\s*\{", re.MULTILINE
    )
    m = token_pattern.search(content)
    if not m:
        return None

    body_start = m.end()
    depth = 1
    i = body_start
    dec_end = -1
    while i < len(content):
        ch = content[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                dec_end = i
                break
        i += 1
    if dec_end < 0:
        return None

    decision_body = content[body_start:dec_end]
    avail_match = re.search(
        r"(^|\n)([ \t]*)available\s*=\s*\{", decision_body, re.MULTILINE
    )
    if not avail_match:
        return None

    avail_body_start = avail_match.end()
    depth = 1
    j = avail_body_start
    avail_end = -1
    while j < len(decision_body):
        ch = decision_body[j]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                avail_end = j
                break
        j += 1
    if avail_end < 0:
        return None

    # Range covers the leading newline (if any), keyword, and block.
    remove_start = avail_match.start()
    remove_end = avail_end + 1  # include closing brace
    new_decision_body = decision_body[:remove_start] + decision_body[remove_end:]
    # Collapse any doubled blank lines introduced by the removal.
    new_decision_body = re.sub(r"\n[ \t]*\n[ \t]*\n", "\n\n", new_decision_body)

    return content[:body_start] + new_decision_body + content[dec_end:]


class Validator(BaseValidator):
    TITLE = "DECISION VALIDATION"
    STAGED_EXTENSIONS = [".txt"]

    def __init__(
        self,
        *args,
        fix: bool = False,
        missing_icons: bool = False,
        unannounced_categories: bool = False,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.fix = fix
        self.missing_icons = missing_icons
        self.unannounced_categories = unannounced_categories
        self._activation_removal_cache: Optional[
            Tuple[Set[str], Set[str], Set[str], Set[str]]
        ] = None
        self._ai_only_by_category: Optional[Set[str]] = None
        self._ai_only_categories: Optional[Dict[str, str]] = None
        if self.no_cache:
            _set_cache_enabled(False)

    def _get_ai_only_categories(self) -> Dict[str, str]:
        """AI-only decision category names, mapped to their defining filename."""
        if self._ai_only_categories is None:
            self._ai_only_categories = ai_only_decision_categories(self.mod_path)
        return self._ai_only_categories

    def _get_ai_only_by_category(self) -> Set[str]:
        """Return decision ids that are AI-only because their category is."""
        if self._ai_only_by_category is not None:
            return self._ai_only_by_category

        ai_categories = self._get_ai_only_categories()
        members: Set[str] = set()
        if ai_categories:
            # parse_categories_with_decisions matches every indented `X = {`,
            # so its lists also carry nested block names (visible, available,
            # complete_effect). Intersect with the real decision names.
            known, _ = parse_all_decision_names(self.mod_path, lowercase=False)
            known_set = set(known)
            by_category = parse_categories_with_decisions(
                self.mod_path, lowercase=False
            )
            for category in ai_categories:
                members.update(
                    name for name in by_category.get(category, []) if name in known_set
                )

        self._ai_only_by_category = members
        return members

    def _get_activation_removal_scan(
        self,
    ) -> Tuple[Set[str], Set[str], Set[str], Set[str]]:
        """Scan shipped content for activations, external removals and unlocks."""
        if self._activation_removal_cache is not None:
            return self._activation_removal_cache
        all_files = [
            filename
            for pattern in _DECISION_REFERENCE_SOURCE_PATTERNS
            for filename in glob.iglob(
                os.path.join(self.mod_path, pattern), recursive=True
            )
        ]
        activated_decisions: Set[str] = set()
        activated_missions: Set[str] = set()
        externally_removed: Set[str] = set()
        announced: Set[str] = set()
        for decision_set, mission_set, removed_set, announced_set in self._pool_map(
            _scan_activations_and_removals, all_files, chunksize=30
        ):
            activated_decisions |= decision_set
            activated_missions |= mission_set
            externally_removed |= removed_set
            announced |= announced_set
        self._activation_removal_cache = (
            activated_decisions,
            activated_missions,
            externally_removed,
            announced,
        )
        return self._activation_removal_cache

    def _apply_decision_file_fixes(self, fixes, patch):
        fixed_total = 0
        for basename, tokens in _group_fixes_by_basename(fixes).items():
            target_file = _find_decision_file(self.mod_path, basename)
            if target_file is None:
                self.log(f"  Could not locate file: {basename}", "warning")
                continue
            content = read_text_strict(target_file)
            for token in tokens:
                patched = patch(content, token)
                if patched is None or patched == content:
                    self.log(f"  Could not patch {token} in {basename}", "warning")
                    continue
                content = patched
                fixed_total += 1
            atomic_write_text(target_file, content)
        return fixed_total

    def _apply_ai_factor_fixes(self, fixes: list):
        """Insert a default ai_will_do = { base = 0 } block into decisions missing one."""

        def patch(content, token):
            pattern = re.compile(
                r"(^\t" + re.escape(token) + r" = \{.*?)(^\t\})",
                flags=re.MULTILINE | re.DOTALL,
            )

            def insert(match):
                return (
                    match.group(1)
                    + "\t\tai_will_do = {\n\t\t\tbase = 0\n\t\t}\n"
                    + match.group(2)
                )

            patched, count = pattern.subn(insert, content)
            return patched if count else None

        fixed_total = self._apply_decision_file_fixes(fixes, patch)

        self.log(
            f"{Colors.GREEN if self.use_colors else ''}  Auto-fixed {fixed_total} decision(s) with missing ai_will_do{Colors.ENDC if self.use_colors else ''}"
        )
        if fixed_total:
            _invalidate_decision_cache()

    def validate_duplicated_decisions(self):
        self._log_section("Checking for duplicated decisions...")

        names, paths = parse_all_decision_names(self.mod_path)
        self.log(f"  Found {len(names)} total decisions")
        results = [f"{n} - {paths[n]}" for n in names if names.count(n) > 1]
        results = sorted(set(results))
        self._report(
            results, "✓ No duplicated decisions", "Duplicated decisions found:"
        )

    def validate_unused_decisions(self):
        self._log_section(
            "Checking for unused decisions (always=no but never activated)..."
        )

        manual = {
            d.token
            for d in parse_all_decision_factories(self.mod_path)
            if d.allowed and "always = no" in d.allowed
        }

        # The worker extracts `decision = X` only from inside an
        # `activate_targeted_decision = { ... }` block; the bare keyword
        # `decision` appears in unrelated places (on_political_decision hooks etc.)
        # and matching them would hide genuinely unused decisions.
        activated_decisions, activated_missions, _, _ = (
            self._get_activation_removal_scan()
        )

        # A mission with a target is activated by activate_targeted_decision, so
        # neither set alone covers every activation mechanism.
        results = _unactivated(manual, activated_decisions | activated_missions)
        self._report(
            results,
            "✓ No unused decisions",
            "Unused decisions (always=no but never manually activated):",
        )

    def validate_unused_categories(self):
        self._log_section("Checking for unused decision categories...")

        cats_with_decisions = parse_categories_with_decisions(
            self.mod_path, visible_when_empty=False
        )
        cats_to_validate = {
            cat: 0 for cat in cats_with_decisions if cats_with_decisions[cat] == []
        }

        if not cats_to_validate:
            self.log(
                f"{Colors.GREEN if self.use_colors else ''}✓ No empty decision categories{Colors.ENDC if self.use_colors else ''}"
            )
            return

        bop_path = str(Path(self.mod_path) / "common" / "bop")
        found_files = False
        for filename in glob.iglob(bop_path + "/**/*.txt", recursive=True):
            found_files = True
            text_file = FileOpener.open_text_file(
                filename, lowercase=False, strip_comments_flag=True
            )
            not_found = [c for c in cats_to_validate if cats_to_validate[c] == 0]
            for cat in not_found:
                if f"decision_category = {cat}" in text_file:
                    cats_to_validate[cat] += 1

        if not found_files:
            self.log(
                f"{Colors.YELLOW if self.use_colors else ''}No BOP files found, skipping BOP check{Colors.ENDC if self.use_colors else ''}",
                "warning",
            )

        results = [cat for cat in cats_to_validate if cats_to_validate[cat] == 0]
        self._report(
            results,
            "✓ No unused decision categories",
            "Unused decision categories (empty, not in BOP):",
        )

    def validate_ai_factors(self):
        self._log_section("Checking decision AI factors...")

        factories = parse_all_decision_factories(self.mod_path)
        categories = parse_decision_categories(self.mod_path)
        cats_with_decs = parse_categories_with_decisions(self.mod_path)

        # Reverse index: decision token -> parent category. The previous
        # version did an O(N) scan per decision over `cats_with_decs`, which
        # added ~1.5s on this mod.
        decision_to_category: Dict[str, str] = {}
        for cat, dec_tokens in cats_with_decs.items():
            for tok in dec_tokens:
                decision_to_category.setdefault(tok, cat)

        results = []
        fixes_needed = []

        for d in factories:
            if d.available and any(
                ["is_ai = no" in d.available, "always = no" in d.available]
            ):
                continue
            if d.visible and any(
                ["is_ai = no" in d.visible, "always = no" in d.visible]
            ):
                continue

            dec_category = decision_to_category.get(d.token)
            if dec_category and dec_category in categories:
                cat_code = categories[dec_category]
                if "is_ai = no" in cat_code or "always = no" in cat_code:
                    continue

            if d.mission_subtype:
                if d.selectable_mission and not d.ai_factor:
                    results.append(
                        f"{d.token} - {d.source_basename} - Selectable mission missing AI factor"
                    )
                elif not d.selectable_mission and d.ai_factor:
                    results.append(
                        f"{d.token} - {d.source_basename} - Non-selectable mission has AI factor"
                    )
            elif not d.ai_factor and "debug" not in d.token:
                results.append(
                    f"{d.token} - {d.source_basename} - Decision missing AI factor"
                )
                if self.fix:
                    fixes_needed.append((d.token, d.source_basename))

            # Note: we previously flagged "zeroed AI factors not evaluated
            # immediately" when factor=0 modifiers appeared after add=N
            # modifiers. That heuristic is wrong for HOI4: ai_will_do
            # evaluates in order on a running total, and clustering
            # factor=0 before the adds makes them a no-op (0*0=0 with base=0).
            # The whole point of placing factor=0 after adds is to override
            # the adds conditionally. Do not re-add that check.

        self._report(results, "✓ No AI factor issues", "Decision AI factor issues:")

        if self.fix and fixes_needed:
            self._apply_ai_factor_fixes(fixes_needed)

    def validate_custom_cost_trigger(self):
        self._log_section(
            "Checking decisions with custom_cost_trigger have a tooltip..."
        )

        factories = parse_all_decision_factories(self.mod_path)
        results = []

        for d in factories:
            if d.custom_cost_trigger and not d.has_tooltip and not d.custom_cost_text:
                results.append(
                    f"{d.token:<55}{d.source_basename} - has custom_cost_trigger but no tooltip or custom_cost_text"
                )

        self._report(
            results,
            "✓ No custom cost trigger issues",
            "Decisions with custom_cost_trigger but missing tooltip:",
        )

    def validate_targeted_without_target(self):
        """Flag targeted decisions missing an explicit target set.

        Exempts:
        - ``allowed = { always = no }`` (decision is script-activated, never auto-visible)
        - ``state_target = yes`` / ``on_map_mode = map_only`` (player-driven map click;
          the engine iterates states/countries only on map interaction, not daily)
        """
        self._log_section(
            "Checking targeted decisions without targets (performance)..."
        )

        factories = parse_all_decision_factories(self.mod_path)
        results = []

        for d in factories:
            if d.target_root_trigger or d.target_trigger:
                if not d.targets and not d.target_array:
                    if d.allowed and "always = no" in d.allowed:
                        continue
                    if d.state_target or d.map_only:
                        continue
                    results.append(f"{d.token:<55}{d.source_basename}")

        self._report(
            results,
            "✓ No targeted decisions without targets",
            "Decisions with target_root_trigger/target_trigger but no targets (checks every country daily):",
        )

    def validate_targets_no_trigger(self):
        """Flag decisions whose visible/available contains FROM checks but lack a target_trigger.

        Having ``targets = { TAG }`` or ``target_array = X`` without a target_trigger
        is perfectly valid — the game simply uses ``visible``/``available`` to filter
        per target. The performance concern arises only when those blocks contain
        FROM checks (evaluated every tick per target). Moving those FROM checks
        into ``target_trigger`` makes them daily instead.
        """
        self._log_section(
            "Checking decisions with FROM checks in visible/available but no target_trigger (performance)..."
        )

        factories = parse_all_decision_factories(self.mod_path)
        results = []

        for d in factories:
            if not (d.targets or d.target_array):
                continue
            if d.target_trigger:
                continue
            # Only flag if there's at least one FROM = { ... } block in visible or available
            has_from_filter = False
            if d.visible and _FROM_BLOCK_RE.search(d.visible):
                has_from_filter = True
            if d.available and _FROM_BLOCK_RE.search(d.available):
                has_from_filter = True
            if has_from_filter:
                results.append(f"{d.token:<55}{d.source_basename}")

        self._report(
            results,
            "✓ No decisions with FROM checks needing target_trigger",
            "Decisions with FROM checks in visible/available but no target_trigger (move FROM into target_trigger for perf):",
        )

    def validate_root_only_visible_on_targeted(self):
        """Flag targeted decisions whose visible block is entirely ROOT-only.

        A targeted decision (targets/target_array/target_trigger/
        target_root_trigger present) evaluates visible every tick, once per
        surviving target with FROM bound. If visible never references FROM
        and there's no target_root_trigger already carrying the ROOT-only
        checks, the whole block is redundant per-target work for something
        that only needs to run once per ROOT per day. Rename it to
        target_root_trigger.

        Exempts:
        - ``allowed = { always = no }`` (decision is script-activated, never
          auto-visible)
        - ``state_target = yes`` / ``on_map_mode = map_only`` (player-driven
          map click, not a daily per-target loop)
        """
        self._log_section(
            "Checking targeted decisions for a ROOT-only visible block (performance)..."
        )

        factories = parse_all_decision_factories(self.mod_path)
        results = []

        for d in factories:
            if not _is_targeted_decision(d):
                continue
            if d.target_root_trigger:
                continue
            if not d.visible:
                continue
            if d.allowed and "always = no" in d.allowed:
                continue
            if d.state_target or d.map_only:
                continue
            if _FROM_WORD_RE.search(d.visible):
                continue
            results.append(
                f"{d.token:<55}{d.source_basename} - visible is ROOT-only and "
                f"re-evaluated every tick per target; rename to target_root_trigger"
            )

        self._report(
            results,
            "✓ No targeted decisions with a ROOT-only visible block",
            "Targeted decisions with a ROOT-only visible and no target_root_trigger (rename visible to target_root_trigger, evaluated daily instead of every tick per target):",
        )

    def validate_from_checks_in_visible(self):
        """Flag targeted decisions with FROM checks in visible when a
        target_trigger already exists.

        visible is evaluated every tick with FROM bound to each surviving
        target; target_trigger runs the same predicate once per (ROOT, FROM)
        pair per day. Moving a FROM check from visible into an existing
        target_trigger is safe with no player-facing change: a failing
        visible hides the entry and renders no tooltip, exactly like a
        failing target_trigger.

        Deliberately out of scope: FROM checks in ``available`` are NOT
        flagged here and must stay put. ``available`` is what renders the
        red blocked-reason tooltip; moving those into target_trigger would
        silently drop targets from the list instead of explaining why
        they're blocked. ``validate_targets_no_trigger`` already covers the
        case where target_trigger is genuinely missing.

        Exempts:
        - ``allowed = { always = no }``
        - ``state_target = yes`` / ``on_map_mode = map_only``
        """
        self._log_section(
            "Checking targeted decisions for FROM checks in visible duplicating target_trigger (performance)..."
        )

        factories = parse_all_decision_factories(self.mod_path)
        results = []

        for d in factories:
            if not d.target_trigger:
                continue
            if d.allowed and "always = no" in d.allowed:
                continue
            if d.state_target or d.map_only:
                continue
            if not d.visible:
                continue

            visible_from_bodies = _extract_from_blocks(d.visible)
            if not visible_from_bodies:
                continue

            normalized_visible = {self._normalize_block(b) for b in visible_from_bodies}
            normalized_trigger = {
                self._normalize_block(b) for b in _extract_from_blocks(d.target_trigger)
            }

            if normalized_visible <= normalized_trigger:
                advice = (
                    "identical to the FROM check already in target_trigger; "
                    "delete it from visible instead of moving it"
                )
            else:
                advice = "move the FROM check into target_trigger (daily) instead of visible (every tick)"

            results.append(f"{d.token:<55}{d.source_basename} - {advice}")

        self._report(
            results,
            "✓ No targeted decisions with FROM checks in visible duplicating target_trigger",
            "Targeted decisions with FROM checks in visible while target_trigger exists:",
        )

    def validate_from_without_targets(self):
        """Flag decisions referencing FROM without a targeting mechanism.

        On a non-targeted country-scoped decision, ``FROM`` falls back to
        ROOT/THIS — so ``var:FROM.array^i`` and ``FROM.GetName`` usually
        resolve to the decision owner rather than firing into the void.
        That makes the code redundant at best and misleading at worst:
        a reader sees FROM and assumes another country is involved, when
        really the decision is just self-referencing.

        Exempts:
        - ``allowed = { always = no }`` — activated via ``activate_decision``
          / ``activate_targeted_decision`` with an explicit FROM set by the
          caller.
        - ``targets`` / ``target_array`` — standard targeted decision.
        - ``state_target = yes`` / ``on_map_mode = map_only`` — FROM is the
          state selected by the player.
        """
        self._log_section("Checking decisions for FROM usage without a target set...")

        factories = parse_all_decision_factories(self.mod_path)
        results = []

        for d in factories:
            if d.targets or d.target_array:
                continue
            if d.state_target or d.map_only:
                continue
            if d.allowed and "always = no" in d.allowed:
                continue

            offending = []
            if d.visible and _FROM_WORD_RE.search(d.visible):
                offending.append("visible")
            if d.available and _FROM_WORD_RE.search(d.available):
                offending.append("available")
            if d.complete_effect and _FROM_WORD_RE.search(d.complete_effect):
                offending.append("complete_effect")

            if offending:
                results.append(
                    f"{d.token:<55}{d.source_basename} - FROM used in {', '.join(offending)} but no targets/target_array/state_target"
                )

        self._report(
            results,
            "✓ No decisions with unscoped FROM usage",
            "Decisions using FROM without a target mechanism (FROM falls back to ROOT so the code is redundant/misleading — add targets/target_array if another country was intended, drop the FROM prefix otherwise, or set allowed = { always = no } if activated via script):",
        )

    def validate_without_allowed_check(self):
        self._log_section(
            "Checking decisions without allowed trigger in unchecked categories..."
        )

        cats_with_decs = parse_categories_with_decisions(self.mod_path)
        factories = parse_all_decision_factories(self.mod_path)
        categories = parse_decision_categories(self.mod_path)

        unchecked_cats = []
        for cat, cat_code in categories.items():
            if "allowed = {" not in cat_code:
                unchecked_cats.append(cat)

        decisions_to_check = set()
        for cat in unchecked_cats:
            if cat in cats_with_decs:
                decisions_to_check.update(cats_with_decs[cat])

        results = []
        for d in factories:
            if d.token in decisions_to_check:
                if not d.allowed:
                    results.append(d.token)

        self._report(
            results,
            "✓ No decisions missing allowed check",
            "Decisions in categories without allowed check that also lack their own allowed trigger:",
        )

    def validate_random_seed(self):
        """Flag repeatable decisions rolling randomness without an explicit ``fixed_random_seed``.

        HOI4 caches RNG outcomes by default within a single tick/save state, so
        a ``random_list`` or ``random = { chance = N ... }`` inside a decision
        will deterministically pick the same branch every time it's evaluated
        unless ``fixed_random_seed = no`` is set on the decision. This defeats
        the point of the roll and leads to confusingly stuck behavior.

        ``fire_only_once = yes`` decisions are exempt: they resolve their roll
        once, so a repeating seed can never surface.

        We only flag decisions where ``fixed_random_seed`` is omitted entirely;
        an explicit ``fixed_random_seed = yes`` is treated as a deliberate
        choice (e.g. reproducible AI rolls) and left alone.
        """
        self._log_section(
            "Checking repeatable decisions with random rolls missing fixed_random_seed = no..."
        )

        factories = parse_all_decision_factories(self.mod_path)
        results = []

        for d in factories:
            if d.fire_only_once or d.fixed_random_seed_explicit:
                continue
            if d.has_random_list or d.has_random_effect:
                results.append(f"{d.token:<55}{d.source_basename}")

        self._report(
            results,
            "✓ No repeatable random decisions missing an explicit fixed_random_seed setting",
            "Repeatable decisions with random_list or random but no explicit 'fixed_random_seed' (RNG will deterministically repeat — set 'fixed_random_seed = no' to randomise, or 'fixed_random_seed = yes' to acknowledge intentional determinism):",
        )

    def validate_redundant_tag_checks(self):
        """Flag redundant tag/original_tag checks within a single decision.

        Two patterns are flagged:

        1. ``allowed`` already pins the decision to a single tag (via
           ``tag = X`` or ``original_tag = X``) and ``visible`` or ``available``
           re-checks the same tag. Since ``allowed`` permanently disables the
           decision for any country with a different tag, the visible/available
           check is dead weight evaluated every tick.

        2. ``allowed`` has both ``tag = X`` and ``original_tag = X`` for the
           same tag — only one is needed (and ``original_tag`` is preferred so
           civil-war split-offs still match).

        Note: this only flags decisions whose ``allowed`` is a flat single-tag
        gate. Decisions whose ``allowed`` uses ``OR``/``NOT``/no tag at all
        are skipped — those legitimately need per-tag filtering downstream.
        """
        self._log_section("Checking decisions for redundant tag checks...")

        factories = parse_all_decision_factories(self.mod_path)
        results = []

        def _has_top_level_tag_check(block: str, tag: str) -> bool:
            for kind, payload in _scan_top_level(block):
                if kind == "tag" and payload == tag:
                    return True
            return False

        def _has_top_level_self_scope(block: str, tag: str) -> bool:
            for kind, payload in _scan_top_level(block):
                if kind == "scope" and payload == tag:
                    return True
            return False

        for d in factories:
            if not d.allowed:
                continue
            allowed_tags = _flat_tag_pins(d.allowed)
            if not allowed_tags:
                continue
            # Only consider single-tag pins (multi-tag allowed is not a redundancy issue here)
            if len(allowed_tags) != 1:
                continue
            pinned = next(iter(allowed_tags))

            issues = []

            # Pattern 2a: allowed has BOTH `tag = X` and `original_tag = X`
            tag_count = len(
                re.findall(
                    r"\btag\s*=\s*" + re.escape(pinned) + r"\b",
                    d.allowed,
                )
            )
            orig_count = len(
                re.findall(
                    r"\boriginal_tag\s*=\s*" + re.escape(pinned) + r"\b",
                    d.allowed,
                )
            )
            if tag_count and orig_count:
                issues.append("allowed has both 'tag' and 'original_tag'")
            # Pattern 2b: allowed uses `tag = X` instead of `original_tag = X`.
            # The `tag` form excludes civil-war split-offs (which have
            # `original_tag = X` but a different runtime tag), so it's almost
            # always a code smell.
            elif tag_count and not orig_count:
                issues.append(
                    "allowed uses 'tag' (prefer 'original_tag' for civil-war robustness)"
                )

            # Pattern 1: visible/available re-checks the same tag at top level
            if _has_top_level_tag_check(d.visible, pinned):
                issues.append("visible re-checks tag")
            if _has_top_level_tag_check(d.available, pinned):
                issues.append("available re-checks tag")

            # Pattern 3: visible/available scopes back into self at top level
            if _has_top_level_self_scope(d.visible, pinned):
                issues.append("visible self-scopes")
            if _has_top_level_self_scope(d.available, pinned):
                issues.append("available self-scopes")

            if issues:
                results.append(
                    f"{d.token:<55}{d.source_basename} ({pinned}: {', '.join(issues)})"
                )

        self._report(
            results,
            "✓ No redundant tag checks found",
            "Decisions with redundant tag checks (allowed already pins the tag):",
        )

    def validate_allowed_redundant_with_category(self):
        """Flag decisions whose ``allowed`` is fully redundant with the parent
        category's ``allowed`` (same single-tag pin, no extra conditions).

        E.g. a decision with ``allowed = { original_tag = TAG }`` inside a
        category that already declares ``allowed = { original_tag = TAG }``.
        The decision-level allowed is dead weight — remove it.
        """
        self._log_section(
            "Checking decisions with allowed redundant with parent category..."
        )

        factories = parse_all_decision_factories(self.mod_path)
        categories = parse_decision_categories(self.mod_path)
        cats_with_decs = parse_categories_with_decisions(self.mod_path)
        cat_pins = _category_allowed_pins(categories)

        results = []
        for d in factories:
            if not d.allowed:
                continue
            dec_pinned = _flat_tag_pins(d.allowed)
            if len(dec_pinned) != 1:
                continue
            pinned = next(iter(dec_pinned))
            # Verify allowed has ONLY this pin (no extra conditions)
            if not _is_sole_flat_pin(d.allowed, pinned):
                continue

            # Find parent category
            cat_name = None
            for c, dec_set in cats_with_decs.items():
                if d.token in dec_set:
                    cat_name = c
                    break
            if cat_name not in cat_pins:
                continue
            cat_tag_values = {tg for _, tg in cat_pins[cat_name]}
            if pinned in cat_tag_values:
                results.append(f"{d.token:<55}{d.source_basename} ({pinned})")

        self._report(
            results,
            "✓ No decisions with allowed redundant with parent category",
            "Decisions with `allowed` redundant with parent category (remove the decision's allowed):",
        )

    def validate_tag_redundant_with_category(self):
        """Flag decision-level tag/original_tag re-checks already covered by
        the parent category's single-tag lock.

        See ``_find_category_redundant_rows`` for the full rule set.
        """
        self._log_section(
            "Checking decisions for tag re-checks redundant with category lock..."
        )

        factories = parse_all_decision_factories(self.mod_path)
        categories = parse_decision_categories(self.mod_path)
        cats_with_decs = parse_categories_with_decisions(self.mod_path)
        cat_pins = _category_allowed_pins(categories)

        results = _find_category_redundant_rows(factories, cat_pins, cats_with_decs)

        self._report(
            results,
            "✓ No decisions with tag checks redundant with category lock",
            "Decisions with tag/original_tag re-checks redundant with the parent category's lock (remove the re-check):",
        )

    def validate_pp_charge_in_effect(self):
        """Flag decisions that charge political power via ``add_political_power = -N``
        in ``complete_effect``/``remove_effect`` instead of (or in addition to)
        the proper ``cost = N`` field.

        Two cases are reported:

        1. **Hidden cost** — no top-level ``cost`` field and the effect block
           has an unconditional ``add_political_power = -N``. The player pays
           PP without the engine displaying a cost or gating affordability.

        2. **Double-charge** — both a ``cost = N`` field AND an unconditional
           ``add_political_power = -M`` in the effect. The true cost is
           ``N + M`` but the UI shows only ``N``. Roll the hidden charge into
           the cost field and remove the duplicate.

        Only flags ``add_political_power = -N`` at the **top level** of the
        effect block — i.e. unconditional charges to the decision-taker.
        Nested charges inside ``if``/``random_list``/scope changes are
        gameplay outcomes, not costs, and are left alone.

        Skipped if:

        - decision has a ``custom_cost_trigger`` (its own custom cost flow)
        - decision is a non-selectable mission (``days_mission_timeout``
          without ``selectable_mission = yes``) — PP changes in those effects
          are timeout outcomes, not entry costs. Selectable missions still
          get checked because their ``complete_effect`` is the player path.
        """
        self._log_section("Checking decisions for hand-rolled PP cost in effects...")

        factories = parse_all_decision_factories(self.mod_path)
        hidden = []
        double = []

        for d in factories:
            if d.custom_cost_trigger:
                continue
            if d.mission_subtype and not d.selectable_mission:
                continue

            try:
                cost_val = int(d.cost) if d.cost else 0
            except (TypeError, ValueError):
                cost_val = 0

            for block_name, block in (
                ("complete_effect", d.complete_effect),
                ("remove_effect", d.remove_effect),
            ):
                # remove_effect is always a timeout outcome for mission-type decisions;
                # skip it regardless of selectable_mission to avoid false positives.
                if block_name == "remove_effect" and d.mission_subtype:
                    continue
                pp = _top_level_neg_pp(block)
                if pp is None:
                    continue
                if cost_val > 0:
                    double.append(
                        f"{d.token:<55}{d.source_basename} ({block_name}: cost={cost_val} + {pp} hidden = {cost_val + pp} true; roll into cost)"
                    )
                else:
                    hidden.append(
                        f"{d.token:<55}{d.source_basename} ({block_name}: charges {pp} PP without cost field)"
                    )
                break

        self._report(
            hidden,
            "✓ No decisions hand-rolling PP cost in effects",
            "Decisions charging political power in effects without a cost field (use 'cost = N' instead):",
        )
        self._report(
            double,
            "✓ No decisions double-charging PP",
            "Decisions double-charging PP (cost field plus add_political_power in effect — roll into cost):",
        )

    def _normalize_block(self, block: str) -> str:
        """Normalize a trigger block for comparison by stripping whitespace/comments."""
        if not block:
            return ""
        inner = block.strip()
        if inner.startswith("{"):
            inner = inner[1:]
        if inner.endswith("}"):
            inner = inner[:-1]
        normalized = re.sub(r"#.*$", "", inner, flags=re.MULTILINE)
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized.strip()

    def validate_visible_equals_available(self):
        """Flag decisions where ``visible`` and ``available`` are functionally identical.

        In HOI4, the engine checks ``visible`` first to determine if a decision appears
        in the UI, then checks ``available`` to determine if it's clickable. If both
        blocks are identical, one is redundant. We move available -> visible since
        it's more efficient (only one check instead of two identical checks).
        """
        self._log_section("Checking decisions with identical visible and available...")

        factories = parse_all_decision_factories(self.mod_path)
        results = []
        fixes_needed = []

        for d in factories:
            if not d.visible or not d.available:
                continue

            vis_normalized = self._normalize_block(d.visible)
            avail_normalized = self._normalize_block(d.available)

            if (
                vis_normalized
                and avail_normalized
                and vis_normalized == avail_normalized
            ):
                results.append(f"{d.token:<55}{d.source_basename}")
                if self.fix:
                    fixes_needed.append((d.token, d.source_basename))

        self._report(
            results,
            "✓ No decisions with identical visible and available",
            "Decisions with identical visible and available:",
        )

        if self.fix and fixes_needed:
            self._apply_visible_to_available_fixes(fixes_needed)

    def _apply_visible_to_available_fixes(self, fixes: list):
        """Replace identical available blocks with the visible content and remove available."""
        fixed_total = self._apply_decision_file_fixes(
            fixes, _remove_available_block_for_token
        )

        self.log(
            f"{Colors.GREEN if self.use_colors else ''}  Auto-fixed {fixed_total} decision(s) by moving available -> visible{Colors.ENDC if self.use_colors else ''}"
        )
        if fixed_total:
            _invalidate_decision_cache()

    def validate_bare_trigger_names(self):
        """Check for common bare trigger names that need a has_ prefix.

        HOI4 requires ``has_political_power``, ``has_stability``, etc. when
        used as comparison triggers.  The bare names (``political_power < 50``)
        are silently accepted by the parser but produce runtime errors.  Only
        flag occurrences that look like comparison triggers (followed by ``<``
        or ``>``), and exclude ``check_variable`` blocks where the bare name
        is a valid variable reference.
        """
        self._log_section("Checking for bare trigger names missing has_ prefix...")

        results = []
        dec_filepath = str(Path(self.mod_path) / "common" / "decisions")
        for filename in sorted(glob.iglob(dec_filepath + "/**/*.txt", recursive=True)):
            if _should_skip(filename):
                continue
            text_file = FileOpener.open_text_file(
                filename, lowercase=False, strip_comments_flag=True
            )
            # Remove check_variable blocks where bare names are valid
            cleaned = re.sub(r"check_variable\s*=\s*\{[^}]*\}", "", text_file)
            for match in _BARE_TRIGGER_RE.finditer(cleaned):
                bare = match.group(1)
                correct = _BARE_TRIGGERS[bare]
                line_num = cleaned[: match.start()].count("\n") + 1
                basename = os.path.basename(filename)
                results.append(
                    f"{basename}:{line_num} - '{bare}' should be '{correct}'"
                )

        self._report(
            results,
            "✓ No bare trigger names found",
            "Bare trigger names (need has_ prefix):",
            category="bare-trigger-name",
        )

    def validate_missing_localisation(self):
        self._log_section("Checking for decisions with missing localisation keys...")

        factories = parse_all_decision_factories(self.mod_path, lowercase=False)
        loc_keys = self._load_localisation_keys()
        scripted_loc_keys = _load_scripted_localisation_keys(self.mod_path)
        self.log(
            f"  Found {len(factories)} decisions, {len(loc_keys)} localisation keys"
        )

        ai_only_by_category = self._get_ai_only_by_category()

        results = []
        ai_results = []
        for dec in factories:
            dec_id = dec.token
            filename = dec.source_basename
            # Decisions can redirect the engine's loc lookup via top-level
            # `name = X` / `desc = X` fields. Validate the override key when
            # present; otherwise check the default `<id>` for the name. The
            # default `<id>_desc` is *not* checked when no override is set —
            # many decisions intentionally omit a description tooltip.
            name_key = dec.name_override if dec.name_override else dec_id

            if _is_effectively_ai_only(dec, dec_id, ai_only_by_category):
                # No human ever sees an AI-only decision, so its loc is dead
                # weight — the check runs in reverse and reports keys that
                # exist. `custom_cost_text` is exempt: it can point at a
                # scripted-loc key shared with player-facing decisions.
                for key in (name_key, f"{dec_id}_desc", dec.desc_override):
                    if key and key in loc_keys:
                        ai_results.append(
                            f"{dec_id} - {filename}: AI-only decision has "
                            f"localisation key '{key}'"
                        )
                continue

            missing = []
            if name_key not in loc_keys:
                missing.append(name_key)
            if dec.desc_override and dec.desc_override not in loc_keys:
                missing.append(dec.desc_override)
            if dec.custom_cost_text:
                scripted_loc = _BRACKETED_LOC_RE.match(dec.custom_cost_text)
                if scripted_loc:
                    if scripted_loc.group(1) not in scripted_loc_keys:
                        missing.append(dec.custom_cost_text)
                elif dec.custom_cost_text not in loc_keys:
                    missing.append(dec.custom_cost_text)
            for key in missing:
                results.append(f"{dec_id} - {filename}: missing loc key '{key}'")

        ai_results.extend(self._ai_only_category_loc(loc_keys))

        self._report(
            results,
            "✓ All decision localisation keys are defined",
            "Decisions with missing localisation keys:",
            Severity.WARNING,
            category="missing-decision-localisation",
        )
        self._report(
            ai_results,
            "✓ No AI-only decision or category carries dead localisation",
            "AI-only decisions and categories with localisation keys:",
            Severity.WARNING,
            category="ai-only-decision-localisation",
        )

    def _ai_only_category_loc(self, loc_keys: AbstractSet[str]) -> List[str]:
        """Findings for AI-only decision categories that still carry loc keys.

        The category header is drawn in the same tab as its decisions, so an
        AI-only category needs no `<id>` or `<id>_desc` either. Categories carry
        no `name =` / `desc =` override, so those two are the whole surface.
        A category named by `unlock_decision_category_tooltip` is exempt: that
        effect renders its name key inside a focus or decision tooltip, which is
        the one place a player sees it outside the category's own tab.
        """
        sources = self._get_ai_only_categories()
        flagged: Dict[str, List[str]] = {}
        for name in sources:
            keys = [key for key in (name, f"{name}_desc") if key in loc_keys]
            if keys:
                flagged[name] = keys
        if not flagged:
            return []

        _, _, _, announced = self._get_activation_removal_scan()
        return [
            f"{name} - {sources.get(name, 'decisions/categories')}: AI-only "
            f"decision category has localisation key '{key}'"
            for name in sorted(flagged)
            if name not in announced
            for key in flagged[name]
        ]

    def validate_unannounced_categories(self):
        """Flag categories that switch on mid-game without telling the player.

        A category with no `visible` block is always on the decisions tab, and
        one gated only on the tag or the date is on from the start, so neither
        has anything to announce. A category gated on state that flips during
        play — a flag, a completed focus, an idea, a variable — appears part-way
        through, and needs `unlock_decision_category_tooltip` (or
        `unlock_decision_tooltip` on one of its decisions) in whatever turns it
        on. Without it a whole tab of decisions shows up with no indication of
        where it came from. AI-only categories are exempt: nobody is watching.
        """
        self._log_section("Checking decision categories announce themselves...")
        self._report(
            self._unannounced_categories(),
            "✓ Every mid-game decision category announces itself",
            "Decision categories that appear without telling the player:",
            Severity.WARNING,
            category="unannounced-decision-category",
        )

    def _unannounced_categories(self) -> List[str]:
        """Findings for mid-game categories nothing announces to the player."""
        ai_only = self._get_ai_only_categories()
        _, _, _, announced = self._get_activation_removal_scan()
        by_category = parse_categories_with_decisions(self.mod_path, lowercase=False)

        results = []
        for name, body in sorted(parse_decision_categories(self.mod_path).items()):
            if name in ai_only or name in announced:
                continue
            # parse_decision_categories hands back `NAME = { ... }`, so unwrap
            # the header before looking for the category's own child blocks.
            inner = flat_block_text(direct_child_block(body, name))
            gate = first_flat_match(
                direct_child_block(inner, "visible"), _MIDGAME_GATE_RE
            )
            if not gate:
                continue
            if any(dec in announced for dec in by_category.get(name, [])):
                continue
            results.append(
                f"{name}: becomes visible on {gate.group(0).strip()} but nothing "
                f"calls unlock_decision_category_tooltip = {name}"
            )
        return results

    def validate_unannounced_decision_unlocks(self):
        """Flag effects that announce some decisions they unlock but not others.

        A decision whose effect sets a flag that another decision's `visible` or
        `available` waits on has unlocked that decision. `unlock_decision_tooltip`
        is how the player is told. MD does not announce every unlock, so only the
        inconsistent case is reported: a block that already announces at least one
        decision, and misses a sibling gated on the very flag it just set. That is
        an oversight rather than a style choice.
        """
        self._log_section("Checking decisions announce the decisions they unlock...")
        self._report(
            self._unannounced_decision_unlocks(),
            "✓ Every decision that announces an unlock announces all of them",
            "Decision effects that unlock a decision without telling the player:",
            Severity.WARNING,
            category="unannounced-decision-unlock",
        )

    def _unannounced_decision_unlocks(self) -> List[str]:
        """Findings for effects that announce some unlocks but miss others."""
        factories = list(parse_all_decision_factories(self.mod_path))
        ai_only_by_category = self._get_ai_only_by_category()

        # flag -> decisions a player can only reach once that flag is set
        gated: Dict[str, Set[str]] = {}
        for dec in factories:
            if _is_effectively_ai_only(dec, dec.token, ai_only_by_category):
                continue
            for block in (dec.visible, dec.available):
                for match in _flat_flag_gates(block):
                    gated.setdefault(match, set()).add(dec.token)

        results = []
        for setter in factories:
            for block_name in EFFECT_BLOCKS:
                block = getattr(setter, block_name)
                if not block or "unlock_decision_tooltip" not in block:
                    continue
                announced = set(_UNLOCK_IN_EFFECT_RE.findall(block))
                missed: Set[str] = set()
                for first, second in _SET_FLAG_RE.findall(block):
                    missed |= gated.get(first or second, set())
                missed -= announced
                missed.discard(setter.token)
                if missed:
                    results.append(
                        f"{setter.token} - {setter.source_basename}: {block_name} "
                        f"announces {len(announced)} unlock(s) but not "
                        f"{', '.join(sorted(missed))}"
                    )
        return results

    def validate_missing_log(self):
        """Flag decision effect blocks that carry no log line.

        AGENTS.md / decision-reference.md require the log in every block the
        engine runs as a decision's effects (complete_effect, remove_effect,
        timeout_effect, cancel_effect):
        `log = "[GetDateText]: [Root.GetName]: Decision <ID>"`. An effect block
        with nothing in it is dead script, so it is reported too.
        """
        self._log_section("Checking decision effect blocks for a missing log...")

        results = []
        for dec in parse_all_decision_factories(self.mod_path):
            for block_name in EFFECT_BLOCKS:
                block = getattr(dec, block_name)
                if not block or _LOG_STRING_RE.search(block):
                    continue
                results.append(
                    f"{dec.token} - {dec.source_basename}: {block_name} has no log line"
                )

        self._report(
            results,
            "✓ Every decision effect block logs",
            "Decision effect blocks with no log line:",
            Severity.ERROR,
            category="missing-decision-log",
        )

    def validate_log_not_first(self):
        """Flag effect blocks whose log is not the block's first statement.

        The log goes at the top so the game log reads in firing order. Only a
        log at the block's own level counts: one nested inside an `if` /
        `hidden_effect` records which branch ran and belongs where it sits.
        """
        self._log_section("Checking decision effect blocks for a log placed late...")

        results = []
        for dec in parse_all_decision_factories(self.mod_path):
            for block_name in EFFECT_BLOCKS:
                block = getattr(dec, block_name)
                if not block:
                    continue
                statements = _block_level_statements(block)
                if "log" not in statements or statements[0] == "log":
                    continue
                results.append(
                    f"{dec.token} - {dec.source_basename}: {block_name} logs "
                    f"after {statements[0]}, move the log to the top of the block"
                )

        self._report(
            results,
            "✓ Every decision effect block logs first",
            "Decision effect blocks whose log is not the first statement:",
            Severity.WARNING,
            category="decision-log-not-first",
        )

    def validate_visible_in_missions(self):
        """Flag missions that have a visible block.

        The HOI4 engine ignores visible on mission-type decisions entirely.
        For script-activated missions (activation = { always = no }) the fix
        is to delete the dead block — moving the condition into activation
        would make the mission double-activate.
        """
        self._log_section(
            "Checking missions with visible block (does nothing for missions)..."
        )

        factories = parse_all_decision_factories(self.mod_path)
        results = []

        for d in factories:
            if d.mission_subtype and d.visible:
                script_activated = (
                    d.activation
                    and "always = no" in d.activation
                    and not d.cancel_if_not_visible
                )
                if script_activated:
                    advice = "delete the dead visible block (mission is script-activated; do NOT move it to activation)"
                else:
                    advice = "delete the dead visible block, or move the condition to activation if it should gate appearance"
                results.append(f"{d.token:<55}{d.source_basename} - {advice}")

        self._report(
            results,
            "✓ No missions with useless visible block",
            "Missions with visible block (engine ignores it on missions):",
        )

    def validate_war_with_targeted(self):
        """Flag targeted decisions using war_with_on_* = FROM.

        The regular war_with_on_complete/remove/timeout arguments do not work
        when the target is FROM. Use the war_with_target_on_* = yes variants.
        """
        self._log_section("Checking targeted decisions for war_with_on_* = FROM...")

        factories = parse_all_decision_factories(self.mod_path)
        results = []

        for d in factories:
            issues = []
            if d.war_with_on_complete == "FROM":
                issues.append(
                    "war_with_on_complete = FROM → war_with_target_on_complete = yes"
                )
            if d.war_with_on_remove == "FROM":
                issues.append(
                    "war_with_on_remove = FROM → war_with_target_on_remove = yes"
                )
            if d.war_with_on_timeout == "FROM":
                issues.append(
                    "war_with_on_timeout = FROM → war_with_target_on_timeout = yes"
                )
            if issues:
                results.append(
                    f"{d.token:<55}{d.source_basename} - {'; '.join(issues)}"
                )

        self._report(
            results,
            "✓ No targeted decisions misusing war_with_on_* = FROM",
            "Targeted decisions using war_with_on_* = FROM (silently fails — use war_with_target_on_* = yes):",
        )

    def validate_missing_war_hint(self):
        """Flag decisions that declare war but carry no war_with_* hint.

        A decision whose complete_effect/remove_effect/timeout_effect calls
        create_wargoal or declare_war should set one of the war_with_on_* (fixed
        target) or war_with_target_on_* (FROM target) attributes so the AI
        prepares for the war. create_wargoal inside an effect_tooltip still
        represents an intended war, so its presence counts; the hint anywhere in
        the decision body clears it.
        """
        self._log_section(
            "Checking decisions declaring war for a missing war_with_* hint..."
        )

        factories = parse_all_decision_factories(self.mod_path)
        results = []
        hints = (
            "war_with_on_complete",
            "war_with_on_remove",
            "war_with_on_timeout",
            "war_with_target_on_complete",
            "war_with_target_on_remove",
            "war_with_target_on_timeout",
        )

        for d in factories:
            if not re.search(r"\b(?:create_wargoal|declare_war_on)\b", d.raw):
                continue
            if any(hint in d.raw for hint in hints):
                continue
            results.append(f"{d.token:<55}{d.source_basename}")

        self._report(
            results,
            "✓ No decisions declaring war without a war_with_* hint",
            "Decisions that declare war but have no war_with_on_* / war_with_target_on_* hint (AI won't prepare):",
        )

    def validate_cancel_if_not_visible(self):
        """Flag decisions with cancel_if_not_visible = yes but no visible block.

        cancel_if_not_visible adds the visible block's conditions to the
        cancel_trigger. Without a visible block, there are no conditions to
        add, making it dead code.
        """
        self._log_section(
            "Checking decisions with cancel_if_not_visible but no visible block..."
        )

        factories = parse_all_decision_factories(self.mod_path)
        results = []

        for d in factories:
            if d.cancel_if_not_visible and not d.visible:
                results.append(f"{d.token:<55}{d.source_basename}")

        self._report(
            results,
            "✓ No decisions with cancel_if_not_visible but missing visible",
            "Decisions with cancel_if_not_visible = yes but no visible block (dead code — remove cancel_if_not_visible or add visible):",
        )

    def validate_custom_cost_ai_hint(self):
        """Flag decisions that spend political power but carry no ai_hint_pp_cost.

        The AI only reserves PP for a decision when it can see the price. It
        reads the ``cost`` field, and nothing else — a custom cost replaces
        that field, and an ``add_political_power = -N`` buried in an effect is
        invisible to it. ``ai_hint_pp_cost`` is how either shape gets declared,
        and without it the AI evaluates a free decision it cannot actually
        afford, ranking it against genuinely free ones.

        Two shapes are reported:

        1. ``custom_cost_trigger`` gating on political power.
        2. An unconditional ``add_political_power = -N`` at the top level of
           ``complete_effect``/``remove_effect``.

        Nested charges inside ``if``/``random_list``/scope changes are gameplay
        outcomes rather than prices, so they are left alone. Skipped when the
        AI never takes the decision (``base = 0`` with no ``add``), and for a
        non-selectable mission's ``remove_effect``, where the PP change is a
        timeout outcome.
        """
        self._log_section("Checking decisions that spend PP for ai_hint_pp_cost...")

        factories = parse_all_decision_factories(self.mod_path)
        results = []

        for d in factories:
            if d.ai_hint_pp_cost:
                continue
            if d.ai_factor and "base = 0" in d.ai_factor and "add" not in d.ai_factor:
                continue

            if d.custom_cost_trigger and "political_power" in d.custom_cost_trigger:
                results.append(
                    f"{d.token:<55}{d.source_basename} - custom_cost_trigger checks political_power but no ai_hint_pp_cost"
                )
                continue

            for block_name, block in (
                ("complete_effect", d.complete_effect),
                ("remove_effect", d.remove_effect),
            ):
                if block_name == "remove_effect" and d.mission_subtype:
                    continue
                pp = _top_level_neg_pp(block)
                if pp is None:
                    continue
                results.append(
                    f"{d.token:<55}{d.source_basename} - {block_name} spends {pp} PP but no ai_hint_pp_cost"
                )
                break

        self._report(
            results,
            "✓ No PP-spending decisions missing ai_hint_pp_cost",
            "Decisions spending political power with no ai_hint_pp_cost (AI won't reserve PP):",
            severity=Severity.WARNING,
        )

    def validate_state_target_with_targets(self):
        """Flag state-targeted decisions with explicit targets but incompatible state_target value.

        When using targets = {} or target_array with state-targeted decisions,
        only state_target = yes or state_target = any will work. Other values
        (any_owned_state, any_controlled_state, continent keys) produce errors.
        """
        self._log_section(
            "Checking state-targeted decisions for incompatible state_target with explicit targets..."
        )

        factories = parse_all_decision_factories(self.mod_path)
        results = []
        valid_with_targets = {"yes", "any"}

        for d in factories:
            if not d.state_target_value:
                continue
            if (
                d.state_target_value in valid_with_targets
                or d.state_target_value == "no"
            ):
                continue
            if d.targets or d.target_array:
                results.append(
                    f"{d.token:<55}{d.source_basename} - state_target = {d.state_target_value} with explicit targets (only yes/any work; use state_target = yes)"
                )

        self._report(
            results,
            "✓ No incompatible state_target with explicit targets",
            "State-targeted decisions with incompatible state_target value (produces error):",
        )

    def validate_mission_only_attributes(self):
        """Flag regular decisions using mission-only attributes.

        Several attributes only function on mission-type decisions (those with
        days_mission_timeout). On regular decisions they are silently ignored:
        timeout_effect, activation, is_good, selectable_mission,
        war_with_on_timeout, war_with_target_on_timeout.
        """
        self._log_section(
            "Checking regular decisions for mission-only attributes (silently ignored)..."
        )

        factories = parse_all_decision_factories(self.mod_path)
        results = []

        for d in factories:
            if d.mission_subtype:
                continue
            issues = []
            if d.has_timeout_effect:
                issues.append("timeout_effect")
            if d.has_activation_block:
                issues.append("activation")
            if d.has_is_good:
                issues.append("is_good")
            if d.has_selectable_mission_kw:
                issues.append("selectable_mission")
            if d.war_with_on_timeout:
                issues.append("war_with_on_timeout")
            if "war_with_target_on_timeout" in d.raw:
                issues.append("war_with_target_on_timeout")
            if issues:
                results.append(
                    f"{d.token:<55}{d.source_basename} - mission-only: {', '.join(issues)}"
                )

        self._report(
            results,
            "✓ No regular decisions with mission-only attributes",
            "Regular decisions using mission-only attributes (silently ignored — add days_mission_timeout to make a mission, or remove these):",
        )

    def validate_orphaned_remove_effect(self):
        """Flag decisions with remove_effect but no timer or removal trigger.

        remove_effect fires when a decision's timer expires (days_remove) or
        when remove_trigger evaluates true. Without either, the effect block
        is dead code that will never execute (unless removed externally via
        the remove_decision effect).

        Exempts missions (which use timeout_effect) and decisions activated
        via script (allowed = { always = no }).
        """
        self._log_section(
            "Checking decisions with remove_effect but no removal mechanism..."
        )

        factories = parse_all_decision_factories(self.mod_path)

        _, _, externally_removed, _ = self._get_activation_removal_scan()

        results = []

        for d in factories:
            if not d.remove_effect:
                continue
            if d.mission_subtype:
                continue
            if d.allowed and "always = no" in d.allowed:
                continue
            if d.has_days_remove or d.has_remove_trigger:
                continue
            if d.token in externally_removed:
                continue
            results.append(f"{d.token:<55}{d.source_basename}")

        self._report(
            results,
            "✓ No decisions with orphaned remove_effect",
            "Decisions with remove_effect but no days_remove or remove_trigger (dead code — add a timer or removal trigger):",
            severity=Severity.WARNING,
        )

    def validate_orphaned_target_modifiers(self):
        """Flag decisions with targets_dynamic or target_non_existing but no targets.

        targets_dynamic = yes makes the game check dynamic country variants
        (civil war split-offs). target_non_existing = yes allows targeting
        countries that don't exist. Both only work with an explicit
        targets = { } list and are meaningless without one.
        """
        self._log_section(
            "Checking decisions with targets_dynamic/target_non_existing but no targets..."
        )

        factories = parse_all_decision_factories(self.mod_path)
        results = []

        for d in factories:
            issues = []
            if d.targets_dynamic and not d.targets:
                issues.append("targets_dynamic")
            if d.target_non_existing and not d.targets:
                issues.append("target_non_existing")
            if issues:
                results.append(
                    f"{d.token:<55}{d.source_basename} - {', '.join(issues)} without targets = {{ }}"
                )

        self._report(
            results,
            "✓ No decisions with orphaned target modifiers",
            "Decisions with targets_dynamic/target_non_existing but no targets (meaningless — add targets or remove):",
        )

    def validate_formable_commitment_sync(self):
        """Flag formable commitment-ratchet literals out of sync with state lists.

        See ``_find_formable_commitment_rows`` for the rule set. New formables
        must wire the ratchet (gate on every decision, commit in
        integrate_start/update_flag) or this check reports them.
        """
        self._log_section(
            "Checking formable commitment ratchet id/size literals for drift..."
        )

        factories = [
            d
            for d in parse_all_decision_factories(self.mod_path)
            if d.source_basename == _FORMABLE_DECISIONS_BASENAME
        ]

        focus_texts: Dict[str, str] = {}
        pattern = os.path.join(self.mod_path, "common", "national_focus", "*.txt")
        for filename in glob.iglob(pattern):
            if _should_skip(filename):
                continue
            text = FileOpener.open_text_file(
                filename, lowercase=False, strip_comments_flag=True
            )
            if "formable_committed_" in text:
                focus_texts[os.path.basename(filename)] = text

        results = _find_formable_commitment_rows(factories, focus_texts)
        self._report(
            results,
            "✓ Formable commitment ids/sizes in sync",
            "Formable commitment ratchet drift (gate/commit literals out of sync with update_flag state lists — update every size literal for the formable):",
        )

    def validate_missing_icons(self):
        """Flag decisions/categories whose icon or picture sprite is undefined.

        A decision `icon = X` renders X verbatim when X is already a full sprite
        name and `GFX_decision_X` otherwise; a category uses
        `GFX_decision_category_X`, and a category `picture` is always the full
        name. When none of those exist in any interface/*.gfx (mod or vanilla)
        the decision draws a missing-texture box.
        """
        self._log_section("Checking for decisions with missing icons...")

        # Built sequentially (no pool_map): a sub-second scan that can't be left
        # empty by a 'spawn' pool worker that fails to start. An empty index
        # would otherwise flag every icon as missing.
        sprites = build_sprite_index(self.mod_path, gfx_only=False)
        if len(sprites) < 1000:
            self.log(
                f"  Only {len(sprites)} GFX sprites loaded — sprite definitions "
                "did not load; skipping the icon check",
                "warning",
            )
            return

        files = self._collect_files(["common/decisions/**/*.txt"], ignore_staged=True)
        ref_lists = self._pool_map(
            _extract_decision_icons, [(f, self.mod_path) for f in files]
        )

        results = []
        checked = 0
        for filepath, refs in zip(files, ref_lists):
            for owner, kind, value, line in refs:
                checked += 1
                msg = _missing_sprite_message(kind, owner, value, sprites)
                if not msg:
                    continue
                results.append((msg, os.path.relpath(filepath, self.mod_path), line))

        self.log(f"  Checked {checked} decision icon/picture references")
        self._report(
            results,
            "✓ All decision icons and pictures are defined",
            "Decisions with missing icons (sprite not defined in interface/*.gfx):",
            Severity.WARNING,
            category="missing-decision-icon",
        )

    def validate_icon_types(self):
        """Flag icons whose art belongs to a different decision-UI slot.

        Sprite names do not tell the slot apart — MD categories use both
        `GFX_decision_category_*` and `GFX_decisions_category_*`, and category
        `picture` banners use the plain `GFX_decision_*` prefix — so the texture's
        pixel size is what identifies the art. Nothing here overlaps the
        missing-icon check: a value that resolves to no sprite is skipped.
        """
        self._log_section("Checking decision icons match their UI slot...")

        textures = build_sprite_texture_index(self.mod_path)
        if len(textures) < 1000:
            self.log(
                f"  Only {len(textures)} GFX textures loaded — sprite definitions "
                "did not load; skipping the icon type check",
                "warning",
            )
            return

        files = self._collect_files(["common/decisions/**/*.txt"], ignore_staged=True)
        ref_lists = self._pool_map(
            _extract_decision_icons, [(f, self.mod_path) for f in files]
        )

        results = []
        for filepath, refs in zip(files, ref_lists):
            for owner, kind, value, line in refs:
                msg = _icon_type_message(kind, owner, value, textures)
                if not msg:
                    continue
                results.append((msg, os.path.relpath(filepath, self.mod_path), line))

        self._report(
            results,
            "✓ All decision icons use art sized for their slot",
            "Decision icons using art from the wrong slot:",
            Severity.WARNING,
            category="decision-icon-slot-mismatch",
        )

    def run_validations(self):
        if self.staged_only:
            # Decision checks parse all 200+ decision files even for structural
            # validation (duplicates, AI factors). Skip entirely in staged mode;
            # CI handles the full decision validation.
            self.log(
                "Decision validation requires full file scan — skipping in staged mode",
                "warning",
            )
            return

        self.validate_duplicated_decisions()
        self.validate_unused_decisions()
        self.validate_unused_categories()
        self.validate_ai_factors()
        self.validate_custom_cost_trigger()
        self.validate_targeted_without_target()
        self.validate_targets_no_trigger()
        self.validate_root_only_visible_on_targeted()
        self.validate_from_checks_in_visible()
        self.validate_from_without_targets()
        self.validate_without_allowed_check()
        self.validate_random_seed()
        self.validate_redundant_tag_checks()
        self.validate_allowed_redundant_with_category()
        self.validate_tag_redundant_with_category()
        self.validate_pp_charge_in_effect()
        self.validate_visible_equals_available()
        self.validate_bare_trigger_names()
        self.validate_missing_localisation()
        self.validate_unannounced_decision_unlocks()
        self.validate_missing_log()
        self.validate_log_not_first()
        self.validate_visible_in_missions()
        self.validate_war_with_targeted()
        self.validate_missing_war_hint()
        self.validate_cancel_if_not_visible()
        self.validate_custom_cost_ai_hint()
        self.validate_state_target_with_targets()
        self.validate_mission_only_attributes()
        self.validate_orphaned_remove_effect()
        self.validate_orphaned_target_modifiers()
        self.validate_formable_commitment_sync()
        self.validate_icon_types()

        if self.missing_icons:
            self.validate_missing_icons()
        else:
            self._log_section(
                "Skipping missing icon check (pass --missing-icons to enable)"
            )

        if self.unannounced_categories:
            self.validate_unannounced_categories()
        else:
            self._log_section(
                "Skipping unannounced category check "
                "(pass --unannounced-categories to enable)"
            )


def _add_extra_args(parser):
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Auto-fix decisions: insert 'ai_will_do = { base = 0 }' for missing AI factors, and move identical available blocks into visible",
    )
    parser.add_argument(
        "--missing-icons",
        action="store_true",
        dest="missing_icons",
        help="Flag decisions and decision categories whose icon/picture sprite is undefined in interface/*.gfx",
    )
    parser.add_argument(
        "--unannounced-categories",
        action="store_true",
        dest="unannounced_categories",
        help="Flag decision categories that become visible mid-game without any unlock_decision_category_tooltip telling the player",
    )


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate decisions in Millennium Dawn mod",
        extra_args_fn=_add_extra_args,
    )
