#!/usr/bin/env python3
"""Validate focus tree structural integrity in Millennium Dawn."""

import os
import re
import sys
from collections import defaultdict
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import disk_cache
from shared_utils import extract_block_from_text as _extract_block
from sprite_index import build_sprite_index
from validator_common import (
    BaseValidator,
    Severity,
    case_mismatch,
    casefold_index,
    run_validator_main,
    strip_comments,
)

# Opening of a focus_tree or top-level focus definition block
# (shared_focus and joint_focus are both standalone definitions that can be
# referenced as prerequisites — they live outside any focus_tree wrapper)
_FOCUS_TREE_START = re.compile(r"\bfocus_tree\s*=\s*\{")
_SHARED_FOCUS_DEF_START = re.compile(r"\b(?:shared_focus|joint_focus)\s*=\s*\{")

# focus ID extraction
_FOCUS_ID_RE = re.compile(r"\bfocus\s*=\s*\{")
_ID_LINE_RE = re.compile(r"\bid\s*=\s*(\S+)")

# focus icon: `icon = X` or `icon = "GFX X"`. The value resolves verbatim to a
# spriteType of that exact name (MD uses bare names like `money` as well as
# GFX_-prefixed ones), so it is checked against the full sprite-name index.
# Quoted values are captured whole, including embedded/trailing spaces, because
# the engine matches the sprite name verbatim (a quoted value with a space is a
# real, distinct sprite name, not two tokens).
_FOCUS_BLOCK_START = re.compile(r"\b(?:focus|shared_focus|joint_focus)\s*=\s*\{")
_ICON_LINE_RE = re.compile(r'\bicon\s*=\s*(?:"([^"]*)"|([^\s{}]+))')

# prerequisite blocks: prerequisite = { focus = A  focus = B }
_PREREQ_BLOCK_RE = re.compile(r"\bprerequisite\s*=\s*\{([^}]*)\}", re.DOTALL)
_PREREQ_FOCUS_RE = re.compile(r"\bfocus\s*=\s*(\S+)")

# shared_focus reference inside a focus_tree block (not a definition)
_SHARED_REF_RE = re.compile(r"\bshared_focus\s*=\s*(\w+)")

# add_tech_bonus inside completion_reward (incl. joint-focus reward variants)
_REWARD_BLOCK_RE = re.compile(
    r"\bcompletion_reward(?:_joint_originator|_joint_member)?\s*=\s*\{"
)
_TECH_BONUS_START = re.compile(r"\badd_tech_bonus\s*=\s*\{")
_NAME_LINE_RE = re.compile(r"\bname\s*=\s*(\S+)")

# PP malus in completion_reward (focus time is the cost — AGENTS.md).
# Occurrences inside an effect_tooltip = { } subtree preview a PP change
# applied elsewhere (e.g. a select_effect) rather than executing it, so
# they are not flagged.
_EFFECT_TOOLTIP_START = re.compile(r"\beffect_tooltip\s*=\s*\{")
_PP_MALUS_RE = re.compile(r"\badd_political_power\s*=\s*(-\d+(?:\.\d+)?)\b")

# ai_will_do staffing/bankruptcy guards (issue #2233 + the AGENTS.md
# convention). Building type -> the scripted trigger
# (common/scripted_triggers/00_economic_triggers.txt) that an ai_will_do
# factor = 0 modifier must check before the AI takes a focus building it.
_STAFFABLE_TRIGGERS = {
    "arms_factory": "can_staff_an_arms_industry",
    "industrial_complex": "can_staff_an_industrial_complex",
    "dockyard": "can_staff_an_dockyard",
    "offices": "can_staff_an_offices",
    "microchip_plant": "can_staff_an_microchip_plant",
    "composite_plant": "can_staff_an_composite_plant",
    "agriculture_district": "can_staff_an_agriculture_district",
}

# A focus whose completion_reward spends at least this much (billions, summed
# from negative treasury_change literals applied via modify_treasury_effect)
# needs the bankruptcy guard. Focus `cost` is completion time, not money, so
# the actual money spend in the reward is what gates the guard.
_MONEY_SPEND_THRESHOLD = 5.0
# Search filters that mark a focus as military/economic/research. A focus that
# spends money or builds should carry one of these; a money/building focus
# tagged with none of them is miscategorized (e.g. an economic focus tagged
# only political).
_MIL_ECON_RESEARCH_FILTERS = frozenset(
    {
        "FOCUS_FILTER_INDUSTRY",
        "FOCUS_FILTER_ECONOMY",
        "FOCUS_FILTER_EXPENDITURE",
        "FOCUS_FILTER_RESEARCH",
        "FOCUS_FILTER_MILITARY_LAWS",
        "FOCUS_FILTER_ARMY",
        "FOCUS_FILTER_NAVY",
        "FOCUS_FILTER_AIRCRAFT",
        "FOCUS_FILTER_EQUIPMENT",
    }
)

_AI_WILL_DO_START = re.compile(r"\bai_will_do\s*=\s*\{")
_MODIFIER_START = re.compile(r"\bmodifier\s*=\s*\{")
_FACTOR_ZERO_RE = re.compile(r"\bfactor\s*=\s*0(?:\.0+)?(?![\d.])")
_CAN_STAFF_NO_RE = re.compile(r"\b(can_staff_an_\w+)\s*=\s*no\b")
_CAN_STAFF_NOT_YES_RE = re.compile(
    r"\bNOT\s*=\s*\{\s*(can_staff_an_\w+)\s*=\s*yes\s*\}"
)
_BANKRUPTCY_GUARD_RE = re.compile(
    r"\bhas_active_mission\s*=\s*bankruptcy_incoming_collapse\b"
)
_ADD_BUILDING_START = re.compile(r"\badd_building_construction\s*=\s*\{")
_TYPE_LINE_RE = re.compile(r"\btype\s*=\s*(\w+)")
# Money spend (MD budget system): treasury_change is set (a literal, a `{ }`
# computed value, or a bare-identifier reference to another variable — the
# latter two we can't sum statically) then applied by modify_treasury_effect;
# modify_debt_effect raises debt. Negative treasury spends, positive is income.
# Only set_temp_variable/set_variable actually assign treasury_change (as the
# key, or as `var = treasury_change`); any other verb touching it
# (multiply_temp_variable, add_to_temp_variable, clamp_temp_variable, ...)
# mutates the running value in a way that can't be summed statically, so it
# forces the segment unknown rather than being read as a fresh set.
_TREASURY_CHANGE_RE = re.compile(
    r"\btreasury_change\s*=\s*(-?\d+(?:\.\d+)?|\{|[A-Za-z_]\w*)"
    r"|\bvar\s*=\s*treasury_change\b"
)
_TREASURY_SET_VERBS = frozenset({"set_temp_variable", "set_variable"})
_TREASURY_MUTATE_VERBS = frozenset(
    {
        "multiply_temp_variable",
        "add_to_temp_variable",
        "subtract_from_temp_variable",
        "divide_temp_variable",
        "clamp_temp_variable",
        "add_to_variable",
        "subtract_from_variable",
        "multiply_variable",
        "clamp_variable",
        "divide_variable",
    }
)
_NUMERIC_LITERAL_RE = re.compile(r"^-?\d+(?:\.\d+)?$")
# modify_treasury_effect and its variants (e.g. modify_treasury_effect_corruption,
# which scales the applied amount by a corruption-level idea before adding it to
# the treasury). Group 1 is the suffix, empty for the plain form; a non-empty
# suffix applies an amount that can't be computed statically, so it forces the
# segment unknown. The `_tt` loc key is never called with `= yes`.
_MODIFY_TREASURY_RE = re.compile(r"\bmodify_treasury_effect(\w*)\s*=\s*yes\b")
_MODIFY_DEBT_RE = re.compile(r"\bmodify_debt_effect\s*=\s*yes\b")
_SEARCH_FILTERS_RE = re.compile(r"\bsearch_filters\s*=\s*\{([^{}]*)\}")
_REWARD_KEY_RE = re.compile(r"\b([A-Za-z0-9_]+)\s*=")
_TOP_LEVEL_BLOCK_RE = re.compile(r"^([A-Za-z0-9_]+)\s*=\s*\{", re.M)

# Cross-country event tooltip check (AGENTS.md "Cross-country event tooltips"):
# a completion_reward that fires a country_event into another nation's scope
# should carry custom_effect_tooltip = TT_IF_THEY_ACCEPT so the player sees the
# acceptance outcome. Foreignness is decided by the fire's nearest enclosing
# scope-change (see _country_event_target_is_foreign).
_COUNTRY_EVENT_RE = re.compile(r"\bcountry_event\b")
_TT_IF_THEY_ACCEPT_RE = re.compile(r"\bTT_IF_THEY_ACCEPT\b")
# Target of a fire, in both `country_event = foo.1` and
# `country_event = { id = foo.1 days = 3 }` form.
_FIRE_TARGET_RE = re.compile(r"country_event\s*=\s*(?:\{[^{}]*?\bid\s*=\s*)?([\w.]+)")
# Event definitions, for deciding whether a fire can be accepted at all. Only
# depth-0 blocks are definitions — `country_event = { id = x days = 1 }` nested
# inside an option is a fire, and would otherwise index x as optionless.
_EVENT_BLOCK_RE = re.compile(r"^(country_event|news_event)\s*=\s*\{", re.M)
_EVENT_ID_RE = re.compile(r"\bid\s*=\s*([\w.]+)")
_EVENT_OPTION_RE = re.compile(r"\boption\s*=\s*\{")
_EVENT_HIDDEN_RE = re.compile(r"\bhidden\s*=\s*yes\b")
_OPTION_TRIGGER_RE = re.compile(r"\btrigger\s*=\s*\{")
_NEGATION_RE = re.compile(r"\bNOT\s*=\s*\{")
# `tag = XXX` / `original_tag = XXX`, in a focus_tree's `country = { }` block
# (the owner) and in an event option's `trigger = { }` (the recipient).
_FT_COUNTRY_BLOCK_RE = re.compile(r"\bcountry\s*=\s*\{")
_TAG_ASSIGN_RE = re.compile(r"\b(?:original_)?tag\s*=\s*([A-Z]{3})\b")
_LITERAL_TAG_RE = re.compile(r"^[A-Z]{3}$")
# Iterators that step over other countries (every_country, random_other_country,
# every_neighbor_country, every_puppet, ...).
_COUNTRY_ITERATOR_RE = re.compile(r"^(?:every|random|all)_\w*(?:country|puppet)")
# Scope labels that resolve to the current/self scope, never a foreign nation.
_SELF_SCOPES = frozenset(
    {"ROOT", "THIS", "PREV", "FROM", "OWNER", "CONTROLLER", "CAPITAL"}
)
# Wrapper blocks that don't change scope — walk through them when locating a
# fire's nearest enclosing scope-change.
_CONTROL_FLOW_SCOPES = frozenset(
    {
        "if",
        "else",
        "else_if",
        "random",
        "hidden_effect",
        "while_loop_effect",
        "for_loop_effect",
    }
)
# 3-letter all-caps tokens that are logic keywords, not country tags.
_NON_TAG_KEYWORDS = frozenset({"AND", "NOT", "NOR"})


def _top_level_search_filters(body: str) -> Set[str]:
    """Extract top-level search filter tokens from a focus block."""
    depth = 0
    i = 0
    while i < len(body):
        ch = body[i]
        if ch == "{":
            depth += 1
            i += 1
            continue
        if ch == "}":
            depth = max(0, depth - 1)
            i += 1
            continue
        if depth == 0:
            m = _SEARCH_FILTERS_RE.match(body, i)
            if m:
                return set(m.group(1).split())
        i += 1
    return set()


def _line_of(text: str, pos: int) -> int:
    """Return the 1-based line number of *pos* in *text*."""
    return text[:pos].count("\n") + 1


def _label_before_brace(body: str, brace_idx: int) -> Optional[str]:
    """Return the `key` of a `key = {` opener whose `{` is at *brace_idx*.

    Returns None for an anonymous block (no `=` before the brace), e.g. a
    color/array literal.
    """
    j = brace_idx - 1
    while j >= 0 and body[j] in " \t\r\n":
        j -= 1
    if j < 0 or body[j] != "=":
        return None
    j -= 1
    while j >= 0 and body[j] in " \t\r\n":
        j -= 1
    end = j + 1
    while j >= 0 and (body[j].isalnum() or body[j] in "_:.@"):
        j -= 1
    return body[j + 1 : end] or None


def _enclosing_block_label(body: str, pos: int) -> Tuple[Optional[str], int]:
    """Return (label, open_brace_index) of the innermost block enclosing *pos*.

    (None, -1) when *pos* is at the top level of *body*.
    """
    depth = 0
    i = pos - 1
    while i >= 0:
        c = body[i]
        if c == "}":
            depth += 1
        elif c == "{":
            if depth == 0:
                return _label_before_brace(body, i), i
            depth -= 1
        i -= 1
    return None, -1


def _is_conjunctive_guard(body: str, pos: int, *, negated: bool = False) -> bool:
    """Whether the condition at *pos* makes a factor-zero modifier apply.

    A guard under OR is not a firm veto: an OR can be satisfied by
    conditions other than the guarded one, so the factor-zero fires when
    *any* OR branch holds, not specifically when the guard is true. A
    direct `X = no` guard also cannot sit under NOT; the separate
    `NOT = { X = yes }` form is recognized through *negated* instead.
    """
    labels: List[str] = []
    while True:
        label, opener = _enclosing_block_label(body, pos)
        if label is None:
            break
        labels.append(label)
        pos = opener
    return "OR" not in labels and (negated or "NOT" not in labels)


def _effect_tooltip_spans(text: str, start: int, end: int) -> List[Tuple[int, int]]:
    """Spans of every `effect_tooltip = { }` subtree between *start* and *end*.

    An effect_tooltip renders its body without executing it, so anything inside
    is a preview of an outcome that happens elsewhere. Checks that reason about
    what a focus actually *does* must skip these spans.
    """
    spans: List[Tuple[int, int]] = []
    pos = start
    while True:
        tm = _EFFECT_TOOLTIP_START.search(text, pos, end)
        if not tm:
            return spans
        tbody, tend = _extract_block(text, tm.start())
        if not tbody or tend > end:
            pos = tm.end()
            continue
        spans.append((tm.start(), tend))
        pos = tend


def _body_money_cost(
    body: str, money_effects: FrozenSet[str]
) -> Tuple[float, bool, bool]:
    """Money an effect body spends. Returns (spend, has_cost, unknown).

    spend    - summed magnitude (billions) of negative treasury_change literals
               actually applied via modify_treasury_effect.
    has_cost - the body reduces the treasury or raises debt at all.
    unknown  - a real cost exists whose amount can't be summed statically (a
               computed or variable-referenced treasury_change, a
               treasury_change touched by anything other than a plain set, a
               debt change, a corruption-style modify_treasury_effect variant,
               or a called effect in *money_effects*).
    Amounts inside effect_tooltip previews (outcomes applied elsewhere) are
    ignored.
    """
    spans = _effect_tooltip_spans(body, 0, len(body))

    def previewed(i: int) -> bool:
        return any(s <= i < e for s, e in spans)

    events: List[Tuple[int, str, Optional[str]]] = []
    for m in _TREASURY_CHANGE_RE.finditer(body):
        if previewed(m.start()):
            continue
        verb, _ = _enclosing_block_label(body, m.start())
        if verb in _TREASURY_MUTATE_VERBS:
            events.append((m.start(), "mutate", None))
        elif verb in _TREASURY_SET_VERBS:
            val = m.group(1)
            known = val is not None and _NUMERIC_LITERAL_RE.match(val)
            events.append((m.start(), "set", val if known else None))
    for m in _MODIFY_TREASURY_RE.finditer(body):
        if not previewed(m.start()):
            events.append((m.start(), "apply", "variant" if m.group(1) else None))
    events.sort()

    # treasury_change is a temp var: each apply spends the value set most
    # recently before it. Across mutually exclusive if/else branches that both
    # set it (only one runs), take the largest magnitude so a big conditional
    # spend isn't hidden by a small sibling branch. An apply with no set since
    # the last one reuses the carried value (the var persists between applies).
    # A mutate event (multiply_temp_variable and friends touching
    # treasury_change) means the segment's magnitude can no longer be summed
    # statically, so it marks the segment unknown without resetting it as a
    # fresh set. A variant apply (modify_treasury_effect_corruption, ...)
    # scales the applied value unpredictably, so it forces that application
    # unknown regardless of the segment.
    spend = 0.0
    has_cost = False
    unknown = False
    cur_neg = 0.0
    cur_unknown = False
    cur_init = False
    seg_max = 0.0
    seg_unknown = False
    seg_has_set = False
    for _, kind, val in events:
        if kind == "set":
            seg_has_set = True
            if val is None:
                seg_unknown = True
            elif float(val) < 0:
                seg_max = max(seg_max, -float(val))
        elif kind == "mutate":
            seg_has_set = True
            seg_unknown = True
        else:  # apply
            if seg_has_set:
                cur_neg, cur_unknown, cur_init = seg_max, seg_unknown, True
            elif not cur_init:
                cur_unknown, cur_init = True, True  # treasury_change set elsewhere
            if val == "variant":
                cur_unknown = True
            if cur_unknown:
                has_cost = True
                unknown = True
            elif cur_neg > 0:
                spend += cur_neg
                has_cost = True
            # a non-negative applied treasury_change is income, not a cost
            seg_max, seg_unknown, seg_has_set = 0.0, False, False

    for m in _MODIFY_DEBT_RE.finditer(body):
        if not previewed(m.start()):
            has_cost = True
            unknown = True
            break

    if money_effects:
        for m in _REWARD_KEY_RE.finditer(body):
            if m.group(1) in money_effects and not previewed(m.start()):
                has_cost = True
                unknown = True
                break

    return spend, has_cost, unknown


def _is_tag_routed(option_bodies: List[str]) -> bool:
    """True when option-level triggers pin every option to a distinct tag.

    `poland.47` gives `.a` a `trigger = { original_tag = UKR }` and `.b` a
    `trigger = { original_tag = SOV }`. Ukraine only ever sees `.a`, Russia only
    `.b` — the event declares two options but hands each recipient exactly one.
    That is a notification, not an offer, so there is no accept branch to
    preview. A negated trigger is unanalysable here, so bail and stay noisy.
    """
    if len(option_bodies) < 2:
        return False
    claimed: Set[str] = set()
    for body in option_bodies:
        tm = _OPTION_TRIGGER_RE.search(body)
        if not tm:
            return False
        tbody, tend = _extract_block(body, tm.start())
        if tend == -1 or _NEGATION_RE.search(tbody):
            return False
        tags = set(_TAG_ASSIGN_RE.findall(tbody))
        if not tags or tags & claimed:
            return False
        claimed |= tags
    return True


def _country_event_target_is_foreign(
    body: str, ce_pos: int, owner_tags: FrozenSet[str]
) -> bool:
    """True if the country_event at *ce_pos* fires into another nation's scope
    and the player can see it happen.

    Walks outward from the fire through control-flow wrappers (if/random/
    hidden_effect/...) until it reaches a scope-changing block. A literal
    non-owner tag, a country iterator, or an event_target:/var: scope is
    foreign; a self scope (ROOT/THIS/…), the owner's own tag, or the reward
    root (bare fire to the focus owner) is not. Unknown scopes are treated as
    non-foreign to keep this warning quiet.

    The walk carries on past that verdict to the reward root, because a
    hidden_effect anywhere above the fire swallows every tooltip under it —
    there is nothing a TT_IF_THEY_ACCEPT could render.
    """
    foreign: Optional[bool] = None
    pos = ce_pos
    while True:
        label, opener = _enclosing_block_label(body, pos)
        if label is None:
            return bool(foreign)
        if label == "hidden_effect":
            return False
        if foreign is None and label not in _CONTROL_FLOW_SCOPES:
            if label in _SELF_SCOPES:
                foreign = False
            elif label.startswith("event_target:") or label.startswith("var:"):
                foreign = True
            elif _COUNTRY_ITERATOR_RE.match(label):
                foreign = True
            elif _LITERAL_TAG_RE.match(label) and label not in _NON_TAG_KEYWORDS:
                foreign = label not in owner_tags
            else:
                foreign = False
        pos = opener


def _parse_focus_ids_from_block(block: str) -> List[Tuple[str, int, List[List[str]]]]:
    """Parse all focus = { ... } blocks from a tree/shared block body.

    Returns a list of (focus_id, relative_line_offset, prerequisite_groups).
    prerequisite_groups is a list of lists — each inner list is the OR-group
    of focus IDs from one prerequisite = { ... } block.
    """
    results: List[Tuple[str, int, List[List[str]]]] = []
    search_start = 0
    while True:
        m = _FOCUS_ID_RE.search(block, search_start)
        if not m:
            break
        body, end = _extract_block(block, m.start())
        if not body:
            search_start = m.end()
            continue

        id_match = _ID_LINE_RE.search(body)
        if not id_match:
            search_start = end
            continue

        focus_id = id_match.group(1)
        line_offset = block[: m.start()].count("\n")

        prereq_groups: List[List[str]] = []
        for pb in _PREREQ_BLOCK_RE.finditer(body):
            group = _PREREQ_FOCUS_RE.findall(pb.group(1))
            if group:
                prereq_groups.append(group)

        results.append((focus_id, line_offset, prereq_groups))
        search_start = end
    return results


def parse_focus_file(args: Tuple[str, str]) -> Dict:
    """Read one focus tree file and return its parsed structure, content-cached."""
    filepath, mod_path = args
    try:
        with open(filepath, "r", encoding="utf-8-sig", errors="replace") as fh:
            raw = fh.read()
    except Exception:
        return {"filepath": filepath, "trees": [], "shared_defs": {}}
    text = strip_comments(raw)
    return disk_cache.per_file_cached_by_content(
        mod_path,
        "focus_tree.parse",
        filepath,
        text,
        lambda: _parse_focus_text(text, filepath),
    )


def _extract_focus_icons(args: Tuple[str, str]) -> List[Tuple[str, str, str, int]]:
    """Pool worker: return (focus_id, icon, filepath, line) for each focus.

    Takes the first `icon =` inside each focus/shared_focus/joint_focus block.
    Focuses that omit `icon` (or use a dynamic `[...]` value) are skipped.
    """
    filepath, mod_path = args
    try:
        with open(filepath, "r", encoding="utf-8-sig", errors="replace") as fh:
            raw = fh.read()
    except Exception:
        return []
    text = strip_comments(raw)

    def _compute() -> List[Tuple[str, str, str, int]]:
        out: List[Tuple[str, str, str, int]] = []
        pos = 0
        while True:
            m = _FOCUS_BLOCK_START.search(text, pos)
            if not m:
                break
            body, end = _extract_block(text, m.start())
            if not body:
                pos = m.end()
                continue
            idm = _ID_LINE_RE.search(body)
            icm = _ICON_LINE_RE.search(body)
            if idm and icm:
                icon = icm.group(1) if icm.group(1) is not None else icm.group(2)
                if "[" not in icon and "]" not in icon:
                    out.append(
                        (idm.group(1), icon, filepath, _line_of(text, m.start()))
                    )
            pos = end
        return out

    return disk_cache.per_file_cached_by_content(
        mod_path, "focus_tree.icons", filepath, text, _compute
    )


def _extract_tech_bonuses(
    args: Tuple[str, str],
) -> List[Tuple[str, Optional[str], str, int]]:
    """Pool worker: return (focus_id, bonus_name, filepath, line) for every
    add_tech_bonus inside a completion_reward* block. bonus_name is None when
    the block has no `name =` parameter.
    """
    filepath, mod_path = args
    try:
        with open(filepath, "r", encoding="utf-8-sig", errors="replace") as fh:
            raw = fh.read()
    except Exception:
        return []
    text = strip_comments(raw)

    def _compute() -> List[Tuple[str, Optional[str], str, int]]:
        out: List[Tuple[str, Optional[str], str, int]] = []
        pos = 0
        while True:
            fm = _FOCUS_BLOCK_START.search(text, pos)
            if not fm:
                break
            fbody, fend = _extract_block(text, fm.start())
            if not fbody:
                pos = fm.end()
                continue
            idm = _ID_LINE_RE.search(fbody)
            focus_id = idm.group(1) if idm else "?"
            # Search within the focus block's absolute span so reported line
            # numbers stay accurate.
            rpos = fm.start()
            while True:
                rm = _REWARD_BLOCK_RE.search(text, rpos, fend)
                if not rm:
                    break
                rbody, rend = _extract_block(text, rm.start())
                if not rbody or rend > fend:
                    rpos = rm.end()
                    continue
                bpos = rm.start()
                while True:
                    bm = _TECH_BONUS_START.search(text, bpos, rend)
                    if not bm:
                        break
                    bbody, bend = _extract_block(text, bm.start())
                    if not bbody:
                        bpos = bm.end()
                        continue
                    nm = _NAME_LINE_RE.search(bbody)
                    name = nm.group(1).strip('"') if nm else None
                    out.append((focus_id, name, filepath, _line_of(text, bm.start())))
                    bpos = bend
                rpos = rend
            pos = fend
        return out

    return disk_cache.per_file_cached_by_content(
        mod_path, "focus_tree.tech_bonus", filepath, text, _compute
    )


def _extract_ai_guard_data(
    args: Tuple[str, str, Dict[str, FrozenSet[str]], FrozenSet[str]],
) -> List[Dict]:
    """Pool worker: per-focus facts for the ai_will_do guard checks.

    Returns one dict per focus: id, line, search filters, the staffable
    building types its rewards construct (directly or via a scripted effect
    from *staffable_map*, and never from inside an effect_tooltip, which only
    previews), the money its rewards spend (spend / has_cost / unknown, with
    *money_effects* naming the scripted effects that spend money), and the
    guard triggers present in factor = 0 ai_will_do modifiers (both the
    `X = no` and `NOT = { X = yes }` forms; guards hidden behind wrapper
    scripted triggers are not recognized). The staffable and money-effect maps
    are folded into the cache tag so entries invalidate when scripted-effect
    definitions change.
    """
    filepath, mod_path, staffable_map, money_effects = args
    try:
        with open(filepath, "r", encoding="utf-8-sig", errors="replace") as fh:
            raw = fh.read()
    except Exception:
        return []
    text = strip_comments(raw)
    fingerprint = (
        ";".join(
            f"{name}:{','.join(sorted(types))}"
            for name, types in sorted(staffable_map.items())
        )
        + "|"
        + ",".join(sorted(money_effects))
    )

    def _compute() -> List[Dict]:
        out: List[Dict] = []
        pos = 0
        while True:
            fm = _FOCUS_BLOCK_START.search(text, pos)
            if not fm:
                break
            fbody, fend = _extract_block(text, fm.start())
            if not fbody:
                pos = fm.end()
                continue
            idm = _ID_LINE_RE.search(fbody)
            if not idm:
                pos = fend
                continue

            sf = _top_level_search_filters(fbody)

            buildings: Set[str] = set()
            spend = 0.0
            has_cost = False
            unknown_cost = False
            rpos = fm.start()
            while True:
                rm = _REWARD_BLOCK_RE.search(text, rpos, fend)
                if not rm:
                    break
                rbody, rend = _extract_block(text, rm.start())
                if not rbody or rend > fend:
                    rpos = rm.end()
                    continue
                # An effect_tooltip previewing someone else's construction is
                # not this focus building anything.
                spans = _effect_tooltip_spans(rbody, 0, len(rbody))

                def previewed(i: int, spans=spans) -> bool:
                    return any(s <= i < e for s, e in spans)

                for km in _REWARD_KEY_RE.finditer(rbody):
                    if km.group(1) in staffable_map and not previewed(km.start()):
                        buildings.update(staffable_map[km.group(1)])
                bpos = 0
                while True:
                    bm = _ADD_BUILDING_START.search(rbody, bpos)
                    if not bm:
                        break
                    bbody, bend = _extract_block(rbody, bm.start())
                    if not bbody:
                        bpos = bm.end()
                        continue
                    if not previewed(bm.start()):
                        buildings.update(
                            t
                            for t in _TYPE_LINE_RE.findall(bbody)
                            if t in _STAFFABLE_TRIGGERS
                        )
                    bpos = bend
                s, hc, u = _body_money_cost(rbody, money_effects)
                spend += s
                has_cost = has_cost or hc
                unknown_cost = unknown_cost or u
                rpos = rend

            guards: Set[str] = set()
            am = _AI_WILL_DO_START.search(fbody)
            if am:
                abody, _ = _extract_block(fbody, am.start())
                if abody:
                    mpos = 0
                    while True:
                        mm = _MODIFIER_START.search(abody, mpos)
                        if not mm:
                            break
                        mbody, mend = _extract_block(abody, mm.start())
                        if not mbody:
                            mpos = mm.end()
                            continue
                        factor_zero = any(
                            _enclosing_block_label(mbody, fm.start())[0] is None
                            for fm in _FACTOR_ZERO_RE.finditer(mbody)
                        )
                        if factor_zero:
                            for gm in _CAN_STAFF_NO_RE.finditer(mbody):
                                if _is_conjunctive_guard(mbody, gm.start(1)):
                                    guards.add(gm.group(1))
                            for gm in _CAN_STAFF_NOT_YES_RE.finditer(mbody):
                                if _is_conjunctive_guard(
                                    mbody, gm.start(1), negated=True
                                ):
                                    guards.add(gm.group(1))
                            for gm in _BANKRUPTCY_GUARD_RE.finditer(mbody):
                                if _is_conjunctive_guard(mbody, gm.start()):
                                    guards.add("bankruptcy_incoming_collapse")
                        mpos = mend

            out.append(
                {
                    "id": idm.group(1),
                    "file": filepath,
                    "line": _line_of(text, fm.start()),
                    "filters": sf,
                    "buildings": buildings,
                    "guards": guards,
                    "spend": spend,
                    "has_cost": has_cost,
                    "unknown": unknown_cost,
                }
            )
            pos = fend
        return out

    return disk_cache.per_file_cached_by_content(
        mod_path,
        "focus_tree.ai_guards.v5",
        filepath,
        text + "\x00" + fingerprint,
        _compute,
    )


def _extract_focus_search_filters(
    args: Tuple[str, str],
) -> List[Tuple[str, str, int]]:
    """Pool worker: focus blocks that omit a top-level search_filters block.

    The focus standard is checked on the focus block itself and not inside
    nested reward blocks.
    """
    filepath, mod_path = args
    try:
        with open(filepath, "r", encoding="utf-8-sig", errors="replace") as fh:
            raw = fh.read()
    except Exception:
        return []
    text = strip_comments(raw)

    def _compute() -> List[Tuple[str, str, int]]:
        out: List[Tuple[str, str, int]] = []
        pos = 0
        while True:
            fm = _FOCUS_BLOCK_START.search(text, pos)
            if not fm:
                break
            fbody, fend = _extract_block(text, fm.start())
            if not fbody:
                pos = fm.end()
                continue
            idm = _ID_LINE_RE.search(fbody)
            if not idm:
                pos = fend
                continue
            if not _top_level_search_filters(fbody):
                out.append((idm.group(1), filepath, _line_of(text, fm.start())))
            pos = fend
        return out

    return disk_cache.per_file_cached_by_content(
        mod_path, "focus_tree.search_filters.v1", filepath, text, _compute
    )


def _extract_cross_country_fires(args: Tuple[str, str, FrozenSet[str]]) -> List[Dict]:
    """Pool worker: focuses whose completion_reward fires an event to another
    nation without a TT_IF_THEY_ACCEPT tooltip.

    *notifications* holds the ids of events the target cannot answer — hidden,
    or a single option — so there is nothing for the player to accept and the
    tooltip would be a lie. Fires at an unknown id stay flagged: a missing
    definition can't be proven harmless.

    Returns one dict (id, file, line) per non-compliant focus.
    """
    filepath, mod_path, notifications = args
    try:
        with open(filepath, "r", encoding="utf-8-sig", errors="replace") as fh:
            raw = fh.read()
    except Exception:
        return []
    text = strip_comments(raw)
    fingerprint = ";".join(sorted(notifications))

    def _compute() -> List[Dict]:
        owner_tags: Set[str] = set()
        for cm in _FT_COUNTRY_BLOCK_RE.finditer(text):
            cbody, _ = _extract_block(text, cm.start())
            if cbody:
                owner_tags.update(_TAG_ASSIGN_RE.findall(cbody))
        owner_frozen = frozenset(owner_tags)

        out: List[Dict] = []
        pos = 0
        while True:
            fm = _FOCUS_BLOCK_START.search(text, pos)
            if not fm:
                break
            fbody, fend = _extract_block(text, fm.start())
            if not fbody:
                pos = fm.end()
                continue
            idm = _ID_LINE_RE.search(fbody)
            if not idm:
                pos = fend
                continue

            flagged = False
            rpos = fm.start()
            while not flagged:
                rm = _REWARD_BLOCK_RE.search(text, rpos, fend)
                if not rm:
                    break
                rbody, rend = _extract_block(text, rm.start())
                if not rbody or rend > fend:
                    rpos = rm.end()
                    continue
                if not _TT_IF_THEY_ACCEPT_RE.search(rbody):
                    for ce in _COUNTRY_EVENT_RE.finditer(rbody):
                        tm = _FIRE_TARGET_RE.match(rbody, ce.start())
                        if tm and tm.group(1) in notifications:
                            continue
                        if _country_event_target_is_foreign(
                            rbody, ce.start(), owner_frozen
                        ):
                            flagged = True
                            break
                rpos = rend

            if flagged:
                out.append(
                    {
                        "id": idm.group(1),
                        "file": filepath,
                        "line": _line_of(text, fm.start()),
                    }
                )
            pos = fend
        return out

    return disk_cache.per_file_cached_by_content(
        mod_path,
        "focus_tree.cross_country_tt.v3",
        filepath,
        text + "\x00" + fingerprint,
        _compute,
    )


def _extract_pp_malus(args: Tuple[str, str]) -> List[Tuple[str, str, int]]:
    """Pool worker: return (focus_id, filepath, line) for each negative,
    literal add_political_power inside a focus's completion_reward.

    Occurrences inside an effect_tooltip = { } subtree are skipped — those
    preview a PP change applied elsewhere (e.g. a select_effect) rather
    than executing the malus.
    """
    filepath, mod_path = args
    try:
        with open(filepath, "r", encoding="utf-8-sig", errors="replace") as fh:
            raw = fh.read()
    except Exception:
        return []
    text = strip_comments(raw)

    def _compute() -> List[Tuple[str, str, int]]:
        out: List[Tuple[str, str, int]] = []
        pos = 0
        while True:
            fm = _FOCUS_BLOCK_START.search(text, pos)
            if not fm:
                break
            fbody, fend = _extract_block(text, fm.start())
            if not fbody:
                pos = fm.end()
                continue
            idm = _ID_LINE_RE.search(fbody)
            focus_id = idm.group(1) if idm else "?"

            rpos = fm.start()
            while True:
                rm = _REWARD_BLOCK_RE.search(text, rpos, fend)
                if not rm:
                    break
                rbody, rend = _extract_block(text, rm.start())
                if not rbody or rend > fend:
                    rpos = rm.end()
                    continue

                tooltip_spans = _effect_tooltip_spans(text, rm.start(), rend)
                for pm in _PP_MALUS_RE.finditer(text, rm.start(), rend):
                    if any(s <= pm.start() < e for s, e in tooltip_spans):
                        continue
                    out.append((focus_id, filepath, _line_of(text, pm.start())))

                rpos = rend
            pos = fend
        return out

    return disk_cache.per_file_cached_by_content(
        mod_path, "focus_tree.pp_malus", filepath, text, _compute
    )


def _parse_focus_text(text: str, filepath: str) -> Dict:
    """Parse comment-stripped focus tree text into a structured result dict.

    Keys:
      "filepath"      — absolute path
      "trees"         — list of tree dicts (see below)
      "shared_defs"   — dict of shared_focus_id -> (line, filepath)

    Each tree dict:
      "focuses"       — list of (focus_id, abs_line, prereq_groups)
      "shared_refs"   — set of shared_focus IDs referenced inside the tree
    """
    result = {
        "filepath": filepath,
        "trees": [],
        "shared_defs": {},
    }

    # --- collect shared_focus definitions (top-level) ---
    pos = 0
    while True:
        m = _SHARED_FOCUS_DEF_START.search(text, pos)
        if not m:
            break
        body, end = _extract_block(text, m.start())
        if not body:
            pos = m.end()
            continue
        id_match = _ID_LINE_RE.search(body)
        if id_match:
            sfid = id_match.group(1)
            abs_line = _line_of(text, m.start())
            prereq_groups: List[List[str]] = []
            for pb in _PREREQ_BLOCK_RE.finditer(body):
                group = _PREREQ_FOCUS_RE.findall(pb.group(1))
                if group:
                    prereq_groups.append(group)
            # Store shared focus definition for the global duplicate check and
            # prerequisite resolution.  We also expose (line, filepath) so the
            # caller can report accurate locations.
            result["shared_defs"][sfid] = {
                "line": abs_line,
                "filepath": filepath,
                "prereq_groups": prereq_groups,
            }
        pos = end

    # --- collect focus_tree blocks ---
    pos = 0
    while True:
        m = _FOCUS_TREE_START.search(text, pos)
        if not m:
            break
        body, end = _extract_block(text, m.start())
        if not body:
            pos = m.end()
            continue

        tree_focuses: List[Tuple[str, int, List[List[str]]]] = []
        for focus_id, line_offset, prereq_groups in _parse_focus_ids_from_block(body):
            abs_line = _line_of(text, m.start()) + line_offset
            tree_focuses.append((focus_id, abs_line, prereq_groups))

        # shared_focus references inside the tree (not definitions)
        shared_refs: Set[str] = set()
        for sr in _SHARED_REF_RE.finditer(body):
            # Only consider bare `shared_focus = NAME` (not `shared_focus = {`)
            next_non_ws = body[sr.end() :].lstrip()
            if next_non_ws.startswith("{"):
                continue
            shared_refs.add(sr.group(1))

        result["trees"].append(
            {
                "focuses": tree_focuses,
                "shared_refs": shared_refs,
            }
        )
        pos = end

    return result


class Validator(BaseValidator):
    TITLE = "FOCUS TREE STRUCTURAL VALIDATION"
    STAGED_EXTENSIONS = [".txt", ".yml"]

    def __init__(self, mod_path: str, **kwargs):
        self.missing_icons = kwargs.pop("missing_icons", False)
        super().__init__(mod_path, **kwargs)
        self._parsed_cache: Optional[List[Dict]] = None
        self._staged_paths: Optional[Set[str]] = None

    # -----------------------------------------------------------------------
    # Data collection
    # -----------------------------------------------------------------------

    def _get_staged_paths(self) -> Set[str]:
        """Return the set of staged focus file paths (relative to mod_path).

        In non-staged mode returns an empty set (meaning: report all files).
        """
        if self._staged_paths is not None:
            return self._staged_paths
        if self.staged_only:
            staged = self._collect_files(["common/national_focus/*.txt"])
            self._staged_paths = {os.path.relpath(f, self.mod_path) for f in staged}
        else:
            self._staged_paths = set()
        return self._staged_paths

    def _is_reportable(self, filepath: str) -> bool:
        """Return True if issues in this file should be reported.

        In staged mode, only report for staged files. In full mode, report all.
        """
        staged = self._get_staged_paths()
        if not staged and self.staged_only:
            return False
        if not self.staged_only:
            return True
        rel = os.path.relpath(filepath, self.mod_path)
        return rel in staged

    def _get_parsed_files(self) -> List[Dict]:
        if self._parsed_cache is not None:
            return self._parsed_cache
        files = self._collect_files(["common/national_focus/*.txt"], ignore_staged=True)
        self._parsed_cache = self._pool_map(
            parse_focus_file, [(f, self.mod_path) for f in files], chunksize=10
        )
        return self._parsed_cache

    def _build_focus_registry(
        self, parsed_files: List[Dict]
    ) -> Tuple[
        Dict[str, List[Tuple[str, int]]], Dict[str, Tuple[str, int, List[List[str]]]]
    ]:
        """Build two lookup structures from parsed data.

        Returns:
          all_focuses   — focus_id -> list of (filepath, line)  (for dup detection)
          focus_info    — focus_id -> (filepath, line, prereq_groups)  (first seen)
        """
        all_focuses: Dict[str, List[Tuple[str, int]]] = defaultdict(list)
        focus_info: Dict[str, Tuple[str, int, List[List[str]]]] = {}

        for parsed in parsed_files:
            fp = parsed["filepath"]
            # shared focus definitions
            for sfid, sdata in parsed["shared_defs"].items():
                all_focuses[sfid].append((fp, sdata["line"]))
                if sfid not in focus_info:
                    focus_info[sfid] = (fp, sdata["line"], sdata["prereq_groups"])
            # focuses inside trees
            for tree in parsed["trees"]:
                for focus_id, line, prereq_groups in tree["focuses"]:
                    all_focuses[focus_id].append((fp, line))
                    if focus_id not in focus_info:
                        focus_info[focus_id] = (fp, line, prereq_groups)

        return all_focuses, focus_info

    # -----------------------------------------------------------------------
    # Check 1: Duplicate focus IDs
    # -----------------------------------------------------------------------

    def validate_duplicate_focus_ids(self):
        self._log_section("Checking for duplicate focus IDs...")

        parsed = self._get_parsed_files()
        all_focuses, _ = self._build_focus_registry(parsed)

        results = []
        for focus_id, locations in sorted(all_focuses.items()):
            if len(locations) < 2:
                continue
            if not any(self._is_reportable(fp) for fp, _ in locations):
                continue
            loc_strs = ", ".join(
                f"{os.path.relpath(fp, self.mod_path)}:{ln}" for fp, ln in locations
            )
            results.append(
                (
                    f"Duplicate focus ID '{focus_id}' defined {len(locations)} times: {loc_strs}",
                    os.path.relpath(locations[0][0], self.mod_path),
                    locations[0][1],
                )
            )

        self._report(
            results,
            "No duplicate focus IDs found",
            "Duplicate focus IDs (second definition overwrites the first):",
            Severity.ERROR,
            category="duplicate-focus-id",
        )

    # -----------------------------------------------------------------------
    # Check 2: Orphan focuses
    # -----------------------------------------------------------------------

    def validate_orphan_focuses(self):
        self._log_section(
            "Checking for orphan focuses (missing prerequisite targets in tree)..."
        )

        parsed = self._get_parsed_files()
        # Build global set of all defined focus IDs for missing-prereq resolution
        _, focus_info = self._build_focus_registry(parsed)
        all_defined: FrozenSet[str] = frozenset(focus_info.keys())

        results = []
        for pf in parsed:
            fp = pf["filepath"]
            if not self._is_reportable(fp):
                continue
            rel = os.path.relpath(fp, self.mod_path)
            for tree in pf["trees"]:
                # The IDs in this tree (NOT counting shared refs)
                tree_ids: Set[str] = {f[0] for f in tree["focuses"]}
                # Include shared focuses referenced into this tree
                effective_ids = tree_ids | tree["shared_refs"]

                for focus_id, line, prereq_groups in tree["focuses"]:
                    if not prereq_groups:
                        continue  # root focus — no prerequisites
                    # A focus is orphaned if ANY prerequisite block is entirely
                    # unsatisfied (none of its focus alternatives exist in the tree).
                    for group in prereq_groups:
                        group_satisfied = any(fid in effective_ids for fid in group)
                        if not group_satisfied:
                            # Also check if ALL alternatives are simply missing
                            # from the entire mod (that's a missing-prereq bug,
                            # not an orphan bug — only report orphan here when at
                            # least one alternative actually exists somewhere).
                            all_missing_globally = all(
                                fid not in all_defined for fid in group
                            )
                            if all_missing_globally:
                                # Will be caught by missing-prerequisite check; skip.
                                continue
                            results.append(
                                (
                                    f"Orphan focus '{focus_id}': prerequisite group {group} not present in tree",
                                    rel,
                                    line,
                                )
                            )
                            break  # one report per focus is enough

        self._report(
            results,
            "No orphan focuses found",
            "Orphan focuses (prerequisite group not found in same tree):",
            Severity.WARNING,
            category="orphan-focus",
        )

    # -----------------------------------------------------------------------
    # Check 3: Missing prerequisite targets
    # -----------------------------------------------------------------------

    def validate_missing_prerequisite_targets(self):
        self._log_section(
            "Checking for prerequisite targets that don't exist anywhere in the mod..."
        )

        parsed = self._get_parsed_files()
        _, focus_info = self._build_focus_registry(parsed)
        all_defined: FrozenSet[str] = frozenset(focus_info.keys())
        defined_ci = casefold_index(all_defined)

        results = []
        seen_missing: Set[str] = set()
        for pf in parsed:
            fp = pf["filepath"]
            if not self._is_reportable(fp):
                continue
            rel = os.path.relpath(fp, self.mod_path)
            # Check shared focus defs
            for sfid, sdata in pf["shared_defs"].items():
                for group in sdata["prereq_groups"]:
                    for prereq_id in group:
                        if (
                            prereq_id not in all_defined
                            and prereq_id not in seen_missing
                        ):
                            seen_missing.add(prereq_id)
                            canonical = case_mismatch(prereq_id, defined_ci)
                            if canonical:
                                results.append(
                                    (
                                        f"Missing prerequisite target '{prereq_id}' (referenced by '{sfid}')"
                                        f": case-mismatch reference '{prereq_id}' — defined as '{canonical}'"
                                        " (works on Windows, fails on Linux)",
                                        rel,
                                        sdata["line"],
                                    )
                                )
                            else:
                                results.append(
                                    (
                                        f"Missing prerequisite target '{prereq_id}' (referenced by '{sfid}')",
                                        rel,
                                        sdata["line"],
                                    )
                                )
            # Check focuses inside trees
            for tree in pf["trees"]:
                for focus_id, line, prereq_groups in tree["focuses"]:
                    for group in prereq_groups:
                        for prereq_id in group:
                            if (
                                prereq_id not in all_defined
                                and prereq_id not in seen_missing
                            ):
                                seen_missing.add(prereq_id)
                                canonical = case_mismatch(prereq_id, defined_ci)
                                if canonical:
                                    results.append(
                                        (
                                            f"Missing prerequisite target '{prereq_id}' (referenced by '{focus_id}')"
                                            f": case-mismatch reference '{prereq_id}' — defined as '{canonical}'"
                                            " (works on Windows, fails on Linux)",
                                            rel,
                                            line,
                                        )
                                    )
                                else:
                                    results.append(
                                        (
                                            f"Missing prerequisite target '{prereq_id}' (referenced by '{focus_id}')",
                                            rel,
                                            line,
                                        )
                                    )

        self._report(
            results,
            "No missing prerequisite targets found",
            "Missing prerequisite targets (focus ID not defined anywhere — likely a typo):",
            Severity.ERROR,
            category="missing-prerequisite",
        )

    # -----------------------------------------------------------------------
    # Check 4: Missing localisation keys
    # -----------------------------------------------------------------------

    def validate_missing_loc_keys(self):
        self._log_section(
            "Checking for missing localisation keys (focus ID and _desc)..."
        )

        parsed = self._get_parsed_files()
        _, focus_info = self._build_focus_registry(parsed)

        # Load all English loc keys (always full repo scan)
        loc_keys = self._load_localisation_keys()
        self.log(
            f"  Found {len(focus_info)} focuses, {len(loc_keys)} localisation keys"
        )

        results = []
        for focus_id, (fp, line, _) in sorted(focus_info.items()):
            if not self._is_reportable(fp):
                continue
            rel = os.path.relpath(fp, self.mod_path)
            missing_keys = []
            if focus_id not in loc_keys:
                missing_keys.append(focus_id)
            desc_key = f"{focus_id}_desc"
            if desc_key not in loc_keys:
                missing_keys.append(desc_key)
            for key in missing_keys:
                results.append(
                    (
                        f"Missing loc key '{key}' for focus '{focus_id}'",
                        rel,
                        line,
                    )
                )

        self._report(
            results,
            "No missing localisation keys found",
            "Focuses with missing localisation keys (may use inline name= override — verify before fixing):",
            Severity.WARNING,
            category="missing-loc-key",
        )

    # -----------------------------------------------------------------------
    # Check 5: add_tech_bonus name parameters
    # -----------------------------------------------------------------------

    def validate_tech_bonus_names(self):
        """Flag add_tech_bonus blocks in completion rewards without a
        localised `name =`.

        Without a name the research-bonus row shows no source; the convention
        is `name = <focus_id>`, which reuses the focus title loc key.
        """
        self._log_section("Checking add_tech_bonus name parameters in focus rewards...")

        files = self._collect_files(["common/national_focus/*.txt"], ignore_staged=True)
        bonus_lists = self._pool_map(
            _extract_tech_bonuses, [(f, self.mod_path) for f in files]
        )
        loc_keys = self._load_localisation_keys()

        results = []
        for sub in bonus_lists:
            for focus_id, name, fp, line in sub:
                if not self._is_reportable(fp):
                    continue
                rel = os.path.relpath(fp, self.mod_path)
                if name is None:
                    results.append(
                        (
                            f"add_tech_bonus in '{focus_id}' has no name = parameter"
                            f" — players see no source for the bonus (use name = {focus_id})",
                            rel,
                            line,
                        )
                    )
                elif "[" not in name and name not in loc_keys:
                    results.append(
                        (
                            f"add_tech_bonus name '{name}' in '{focus_id}' has no"
                            " localisation key (typo? convention is the focus id)",
                            rel,
                            line,
                        )
                    )

        self._report(
            results,
            "All add_tech_bonus blocks in focus rewards carry a localised name",
            "add_tech_bonus blocks missing a name or using an unlocalised name:",
            Severity.WARNING,
            category="tech-bonus-name",
        )

    # -----------------------------------------------------------------------
    # Check 5b: Missing search_filters in focus blocks
    # -----------------------------------------------------------------------

    def validate_missing_search_filters(self):
        self._log_section("Checking for focus blocks missing search_filters...")

        files = self._collect_files(["common/national_focus/*.txt"], ignore_staged=True)
        missing_lists = self._pool_map(
            _extract_focus_search_filters,
            [(f, self.mod_path) for f in files],
            chunksize=10,
        )

        results = []
        for sub in missing_lists:
            for focus_id, fp, line in sub:
                if not self._is_reportable(fp):
                    continue
                rel = os.path.relpath(fp, self.mod_path)
                results.append(
                    (f"Focus '{focus_id}' missing search_filters", rel, line)
                )

        self._report(
            results,
            "No focus blocks are missing search_filters",
            "Focuses missing search_filters:",
            Severity.WARNING,
            category="missing-search-filters",
        )

    # -----------------------------------------------------------------------
    # Check 5c: ai_will_do staffing / bankruptcy guards
    # -----------------------------------------------------------------------

    def _staffable_effect_map(self) -> Dict[str, FrozenSet[str]]:
        """Map scripted-effect name -> staffable building types it constructs.

        Scans every top-level effect in common/scripted_effects/ for
        add_building_construction of a staffable type, so new builder-effect
        variants are picked up without a hardcoded list.
        """
        fx_files = self._collect_files(
            ["common/scripted_effects/*.txt"], ignore_staged=True
        )
        mapping: Dict[str, FrozenSet[str]] = {}
        for fp in fx_files:
            try:
                with open(fp, "r", encoding="utf-8-sig", errors="replace") as fh:
                    text = strip_comments(fh.read())
            except Exception:
                continue

            def _compute(text=text) -> Dict[str, FrozenSet[str]]:
                found: Dict[str, FrozenSet[str]] = {}
                for m in _TOP_LEVEL_BLOCK_RE.finditer(text):
                    body, _ = _extract_block(text, m.start())
                    if not body:
                        continue
                    types: Set[str] = set()
                    bpos = 0
                    while True:
                        bm = _ADD_BUILDING_START.search(body, bpos)
                        if not bm:
                            break
                        bbody, bend = _extract_block(body, bm.start())
                        if not bbody:
                            bpos = bm.end()
                            continue
                        types.update(
                            t
                            for t in _TYPE_LINE_RE.findall(bbody)
                            if t in _STAFFABLE_TRIGGERS
                        )
                        bpos = bend
                    if types:
                        found[m.group(1)] = frozenset(types)
                return found

            mapping.update(
                disk_cache.per_file_cached_by_content(
                    self.mod_path, "focus_tree.staffable_fx", fp, text, _compute
                )
            )

        # Resolve scripted-effect chains to a fixed point so a builder wrapper
        # remains visible through any number of intermediate effects.
        direct = dict(mapping)
        effect_bodies: Dict[str, str] = {}
        for fp in fx_files:
            try:
                with open(fp, "r", encoding="utf-8-sig", errors="replace") as fh:
                    text = strip_comments(fh.read())
            except Exception:
                continue
            for m in _TOP_LEVEL_BLOCK_RE.finditer(text):
                body, _ = _extract_block(text, m.start())
                if body:
                    effect_bodies[m.group(1)] = body

        known_effects = set(effect_bodies)
        calls = {
            name: set(_REWARD_KEY_RE.findall(body)) & known_effects
            for name, body in effect_bodies.items()
        }
        mapping = dict(direct)
        changed = True
        while changed:
            changed = False
            for name, dependencies in calls.items():
                types: Set[str] = set(direct.get(name, frozenset()))
                for dependency in dependencies:
                    types.update(mapping.get(dependency, frozenset()))
                resolved = frozenset(types)
                if resolved and resolved != mapping.get(name):
                    mapping[name] = resolved
                    changed = True
        return mapping

    def _money_cost_effect_names(self) -> FrozenSet[str]:
        """Scripted-effect names that (transitively) reduce the treasury or
        raise debt, so a focus reward calling one counts as spending money.

        Mirrors _staffable_effect_map: each effect's own body is scanned with
        _body_money_cost, then call chains are resolved to a fixed point so a
        money-spending wrapper of any depth stays visible. A computed
        (non-literal) treasury_change is treated as a cost even though its sign
        is unknown, so a handful of computed-income effects may be included.
        """
        fx_files = self._collect_files(
            ["common/scripted_effects/*.txt"], ignore_staged=True
        )
        direct: Set[str] = set()
        effect_bodies: Dict[str, str] = {}
        for fp in fx_files:
            try:
                with open(fp, "r", encoding="utf-8-sig", errors="replace") as fh:
                    text = strip_comments(fh.read())
            except Exception:
                continue

            def _compute(text=text) -> List[str]:
                found: List[str] = []
                for m in _TOP_LEVEL_BLOCK_RE.finditer(text):
                    body, _ = _extract_block(text, m.start())
                    if body and _body_money_cost(body, frozenset())[1]:
                        found.append(m.group(1))
                return found

            direct.update(
                disk_cache.per_file_cached_by_content(
                    self.mod_path, "focus_tree.money_fx", fp, text, _compute
                )
            )
            for m in _TOP_LEVEL_BLOCK_RE.finditer(text):
                body, _ = _extract_block(text, m.start())
                if body:
                    effect_bodies[m.group(1)] = body

        known_effects = set(effect_bodies)
        calls = {
            name: set(_REWARD_KEY_RE.findall(body)) & known_effects
            for name, body in effect_bodies.items()
        }
        money = set(direct)
        changed = True
        while changed:
            changed = False
            for name, dependencies in calls.items():
                if name not in money and dependencies & money:
                    money.add(name)
                    changed = True
        return frozenset(money)

    def validate_ai_will_do_guards(self):
        """Flag focuses missing (or carrying an unneeded) ai_will_do guard.

        can_staff (issue #2233): a focus whose reward builds a staffable
        building — directly or via a scripted effect — needs the matching
        can_staff_an_* = no modifier so the AI skips it with no free workers.
        Bankruptcy: a focus whose reward spends money needs a
        has_active_mission = bankruptcy_incoming_collapse modifier. Spend is
        the money the reward actually costs (summed negative treasury_change,
        or a money-spending scripted effect), not the focus completion time —
        so a focus spending at least the threshold without the guard is
        flagged, a focus carrying the guard with no money cost is flagged as
        unneeded, and a money/building focus tagged neither economic nor
        military is flagged as miscategorized. Effect chains are resolved to a
        fixed point so a wrapper of any depth stays visible; guards written via
        wrapper scripted triggers are not recognized. All are per-file
        aggregates so the backlog stays readable.
        """
        self._log_section("Checking ai_will_do staffing/bankruptcy guards...")

        staffable = self._staffable_effect_map()
        if not staffable:
            self.log(
                "  No builder effects found under common/scripted_effects/ — "
                "can_staff detection limited to direct add_building_construction",
                "warning",
            )
        money_effects = self._money_cost_effect_names()
        files = self._collect_files(["common/national_focus/*.txt"], ignore_staged=True)
        data_lists = self._pool_map(
            _extract_ai_guard_data,
            [(f, self.mod_path, staffable, money_effects) for f in files],
            chunksize=10,
        )

        staff_results = []
        underguarded_by_file: Dict[str, List[Tuple[str, int, float]]] = defaultdict(
            list
        )
        unknown_spend_by_file: Dict[str, List[Tuple[str, int]]] = defaultdict(list)
        unneeded_by_file: Dict[str, List[Tuple[str, int]]] = defaultdict(list)
        miscategorized_by_file: Dict[str, List[Tuple[str, int]]] = defaultdict(list)
        for sub in data_lists:
            for d in sub:
                if not self._is_reportable(d["file"]):
                    continue
                rel = os.path.relpath(d["file"], self.mod_path)

                unguarded = sorted(
                    b
                    for b in d["buildings"]
                    if _STAFFABLE_TRIGGERS[b] not in d["guards"]
                )
                if unguarded:
                    triggers = ", ".join(
                        f"{_STAFFABLE_TRIGGERS[b]} = no" for b in unguarded
                    )
                    staff_results.append(
                        (
                            f"Focus '{d['id']}' builds {', '.join(unguarded)} but"
                            f" its ai_will_do has no factor = 0 modifier with"
                            f" {triggers}",
                            rel,
                            d["line"],
                        )
                    )

                has_guard = "bankruptcy_incoming_collapse" in d["guards"]
                if not has_guard:
                    if d["spend"] >= _MONEY_SPEND_THRESHOLD:
                        underguarded_by_file[rel].append(
                            (d["id"], d["line"], d["spend"])
                        )
                    elif d["unknown"]:
                        unknown_spend_by_file[rel].append((d["id"], d["line"]))
                elif not d["has_cost"]:
                    unneeded_by_file[rel].append((d["id"], d["line"]))

                if (
                    d["filters"]
                    and (d["buildings"] or d["spend"] >= _MONEY_SPEND_THRESHOLD)
                    and not (d["filters"] & _MIL_ECON_RESEARCH_FILTERS)
                ):
                    miscategorized_by_file[rel].append((d["id"], d["line"]))

        def _aggregate(by_file: Dict[str, List[Tuple]], noun: str) -> List[Tuple]:
            rows = []
            for rel, hits in sorted(by_file.items()):
                examples = ", ".join(f"{h[0]} (line {h[1]})" for h in hits[:3])
                more = f" and {len(hits) - 3} more" if len(hits) > 3 else ""
                rows.append((f"{len(hits)} {noun}: {examples}{more}", rel, hits[0][1]))
            return rows

        self._report(
            staff_results,
            "All building focuses carry the matching can_staff ai_will_do guard",
            "Focuses building staffable buildings without a can_staff guard:",
            Severity.WARNING,
            category="missing-can-staff-guard",
        )
        self._report(
            _aggregate(
                underguarded_by_file,
                f"focus(es) spending >= {_MONEY_SPEND_THRESHOLD:g}bn without the"
                " bankruptcy guard",
            ),
            "All money-spending focuses carry the bankruptcy ai_will_do guard",
            "Files with high-spend focuses missing the bankruptcy guard:",
            Severity.WARNING,
            category="missing-bankruptcy-guard",
        )
        self._report(
            _aggregate(
                unknown_spend_by_file,
                "focus(es) spending money via a scripted effect (amount unknown)"
                " without the bankruptcy guard",
            ),
            "No focuses spend via scripted effects without a bankruptcy guard",
            "Files with scripted-spend focuses missing the bankruptcy guard (verify):",
            Severity.WARNING,
            category="missing-bankruptcy-guard-scripted",
        )
        self._report(
            _aggregate(
                unneeded_by_file,
                "focus(es) with a bankruptcy guard but no money cost (guard unneeded)",
            ),
            "No focuses carry an unneeded bankruptcy guard",
            "Files with an unneeded bankruptcy guard (no treasury cost):",
            Severity.WARNING,
            category="unneeded-bankruptcy-guard",
        )
        self._report(
            _aggregate(
                miscategorized_by_file,
                "money/building focus(es) tagged neither economic nor military"
                " (search_filter mismatch)",
            ),
            "All money/building focuses carry an economic/military search filter",
            "Files with money/building focuses lacking an economic/military filter:",
            Severity.WARNING,
            category="focus-filter-mismatch",
        )

    def _notification_event_ids(self) -> FrozenSet[str]:
        """Event ids the target cannot answer: hidden, fewer than 2 options, or
        options tag-routed one per recipient (see _is_tag_routed).

        Firing one of these into a foreign scope is a notification, not an
        offer, so it never needs a TT_IF_THEY_ACCEPT tooltip.
        """
        ids: Set[str] = set()
        for fp in self._collect_files(["events/*.txt"], ignore_staged=True):
            try:
                with open(fp, "r", encoding="utf-8-sig", errors="replace") as fh:
                    text = strip_comments(fh.read())
            except Exception:
                continue

            def _compute(text=text) -> List[str]:
                found: List[str] = []
                for m in _EVENT_BLOCK_RE.finditer(text):
                    body, end = _extract_block(text, m.start())
                    if end == -1:
                        continue
                    idm = _EVENT_ID_RE.search(body)
                    if not idm:
                        continue
                    options: List[str] = []
                    opos = 0
                    while True:
                        om = _EVENT_OPTION_RE.search(body, opos)
                        if not om:
                            break
                        obody, oend = _extract_block(body, om.start())
                        if oend == -1:
                            break
                        options.append(obody)
                        opos = oend
                    if (
                        len(options) < 2
                        or _EVENT_HIDDEN_RE.search(body)
                        or _is_tag_routed(options)
                    ):
                        found.append(idm.group(1))
                return found

            ids.update(
                disk_cache.per_file_cached_by_content(
                    self.mod_path,
                    "focus_tree.notification_events.v3",
                    fp,
                    text,
                    _compute,
                )
            )
        return frozenset(ids)

    def validate_cross_country_event_tooltips(self):
        """Flag focuses that fire an event to another nation without a
        TT_IF_THEY_ACCEPT tooltip.

        AGENTS.md "Cross-country event tooltips": when a completion_reward fires
        a country_event into a foreign scope, the player should see the outcome
        via custom_effect_tooltip = TT_IF_THEY_ACCEPT. Reported per file as a
        WARNING — the presence of the tooltip anywhere in the reward clears it,
        so a reward already carrying one is not flagged. Fires at an event the
        target cannot answer are notifications and are skipped.
        """
        self._log_section("Checking cross-country event fires for TT_IF_THEY_ACCEPT...")

        notifications = self._notification_event_ids()
        files = self._collect_files(["common/national_focus/*.txt"])
        data_lists = self._pool_map(
            _extract_cross_country_fires,
            [(f, self.mod_path, notifications) for f in files],
            chunksize=10,
        )

        by_file: Dict[str, List[Tuple[str, int]]] = defaultdict(list)
        for sub in data_lists:
            for d in sub:
                if not self._is_reportable(d["file"]):
                    continue
                rel = os.path.relpath(d["file"], self.mod_path)
                by_file[rel].append((d["id"], d["line"]))

        results = []
        for rel, hits in sorted(by_file.items()):
            hits.sort(key=lambda h: h[1])
            examples = ", ".join(f"{fid} (line {line})" for fid, line in hits[:3])
            more = f" and {len(hits) - 3} more" if len(hits) > 3 else ""
            results.append(
                (
                    f"{len(hits)} focus(es) fire an event to another nation without"
                    f" a TT_IF_THEY_ACCEPT tooltip: {examples}{more}",
                    rel,
                    hits[0][1],
                )
            )

        self._report(
            results,
            "All cross-country event fires carry a TT_IF_THEY_ACCEPT tooltip",
            "Files with focuses firing an event to another nation without TT_IF_THEY_ACCEPT:",
            Severity.WARNING,
            category="missing-cross-country-tooltip",
        )

    def validate_pp_malus_in_rewards(self):
        """Flag a literal PP loss (add_political_power = -N) inside a focus's
        completion_reward.

        Focus time is the cost (AGENTS.md) — a PP malus on completion is a
        balance choice needing per-site judgment, so this reports at WARNING
        only. Scope is the literal-negative-number pattern: variable forms
        and timed lose-PP ideas are not detected. effect_tooltip previews of
        a PP change applied elsewhere (e.g. via select_effect) are skipped.
        """
        self._log_section("Checking for PP malus in focus completion_reward...")

        files = self._collect_files(["common/national_focus/*.txt"], ignore_staged=True)
        data_lists = self._pool_map(
            _extract_pp_malus, [(f, self.mod_path) for f in files], chunksize=10
        )

        results = []
        for sub in data_lists:
            for focus_id, fp, line in sub:
                if not self._is_reportable(fp):
                    continue
                rel = os.path.relpath(fp, self.mod_path)
                results.append(
                    (
                        f"Focus '{focus_id}' completion_reward applies a PP"
                        " malus (negative add_political_power) — focus time"
                        " is the cost; verify this is intended",
                        rel,
                        line,
                    )
                )

        self._report(
            results,
            "No PP malus found in focus completion_reward blocks",
            "Focuses applying a PP malus in completion_reward (balance-sensitive — verify intent):",
            Severity.WARNING,
            category="pp-malus-completion-reward",
        )

    # -----------------------------------------------------------------------
    # Check 6: Dependency cycles
    # -----------------------------------------------------------------------

    def validate_dependency_cycles(self):
        self._log_section("Checking for dependency cycles in prerequisite chains...")

        parsed = self._get_parsed_files()

        # Build ONE global dependency graph across every file. A prerequisite
        # edge can route through a shared_focus / joint_focus target (defined at
        # file top level, outside any focus_tree) and can cross files, so a
        # per-tree graph silently drops those edges and misses cycles that pass
        # through them.
        adjacency: Dict[str, Set[str]] = defaultdict(set)
        node_info: Dict[str, Tuple[str, int, str]] = {}

        def _register(focus_id: str, line: int, filepath: str) -> None:
            adjacency.setdefault(focus_id, set())
            if focus_id not in node_info:
                node_info[focus_id] = (
                    os.path.relpath(filepath, self.mod_path),
                    line,
                    filepath,
                )

        for pf in parsed:
            fp = pf["filepath"]
            for sfid, sdata in pf["shared_defs"].items():
                _register(sfid, sdata["line"], fp)
            for tree in pf["trees"]:
                for focus_id, line, _groups in tree["focuses"]:
                    _register(focus_id, line, fp)

        def _add_edges(focus_id: str, prereq_groups: List[List[str]]) -> None:
            # Flatten OR-groups — for cycle detection any edge matters. Only keep
            # edges to known nodes (a prereq into another mod object isn't ours).
            for group in prereq_groups:
                for prereq_id in group:
                    if prereq_id in node_info:
                        adjacency[focus_id].add(prereq_id)

        for pf in parsed:
            for sfid, sdata in pf["shared_defs"].items():
                _add_edges(sfid, sdata["prereq_groups"])
            for tree in pf["trees"]:
                for focus_id, _line, prereq_groups in tree["focuses"]:
                    _add_edges(focus_id, prereq_groups)

        # Iterative white/gray/black DFS with an explicit work stack: prerequisite
        # chains can run 1000+ deep, so a recursive DFS would blow the Python
        # recursion limit. Every node is finalized to BLACK when it pops, so no
        # GRAY state survives a cycle — that lets independent cycles sharing a
        # node each be reported instead of only the first one found.
        WHITE, GRAY, BLACK = 0, 1, 2
        color: Dict[str, int] = {fid: WHITE for fid in node_info}

        results = []
        reported_cycles: Set[FrozenSet] = set()

        def _record_cycle(cycle: List[str]) -> None:
            cycle_key = frozenset(cycle)
            if cycle_key in reported_cycles:
                return
            if not any(self._is_reportable(node_info[n][2]) for n in cycle):
                return
            reported_cycles.add(cycle_key)
            rel, line, _fp = node_info[cycle[0]]
            results.append(
                (
                    f"Dependency cycle detected: {' -> '.join(cycle)}",
                    rel,
                    line,
                )
            )

        for root in node_info:
            if color[root] != WHITE:
                continue
            path: List[str] = [root]
            on_path: Set[str] = {root}
            color[root] = GRAY
            work = [(root, iter(adjacency[root]))]
            while work:
                node, neighbors = work[-1]
                advanced = False
                for neighbor in neighbors:
                    if color[neighbor] == GRAY:
                        # A GRAY node is always still on the current path (popped
                        # nodes are BLACK), so this is a live back-edge -> cycle.
                        if neighbor in on_path:
                            start = path.index(neighbor)
                            _record_cycle(path[start:] + [neighbor])
                        continue
                    if color[neighbor] == WHITE:
                        color[neighbor] = GRAY
                        path.append(neighbor)
                        on_path.add(neighbor)
                        work.append((neighbor, iter(adjacency[neighbor])))
                        advanced = True
                        break
                if not advanced:
                    color[node] = BLACK
                    on_path.discard(node)
                    work.pop()
                    path.pop()

        self._report(
            results,
            "No dependency cycles found",
            "Dependency cycles in prerequisite chains:",
            Severity.ERROR,
            category="dependency-cycle",
        )

    # -----------------------------------------------------------------------
    # Entry point
    # -----------------------------------------------------------------------

    def validate_focus_icons(self):
        """Flag focuses whose `icon = X` sprite is not defined.

        A focus icon resolves verbatim to a spriteType named exactly `X` (MD
        uses bare names like `money` as well as `GFX_`-prefixed ones). When no
        such sprite exists in any interface/*.gfx (mod or vanilla) the focus
        shows a placeholder icon.
        """
        self._log_section("Checking for focuses with missing icons...")

        # Built sequentially (no pool_map): a sub-second scan that can't be left
        # empty by a 'spawn' pool worker that fails to start. An empty index
        # would otherwise flag every focus icon as missing.
        sprites = build_sprite_index(self.mod_path, gfx_only=False)
        if len(sprites) < 1000:
            self.log(
                f"  Only {len(sprites)} GFX sprites loaded — sprite definitions "
                "did not load; skipping the icon check",
                "warning",
            )
            return
        files = self._collect_files(["common/national_focus/*.txt"], ignore_staged=True)
        icon_lists = self._pool_map(
            _extract_focus_icons, [(f, self.mod_path) for f in files]
        )

        results = []
        for sub in icon_lists:
            for focus_id, icon, fp, line in sub:
                if icon in sprites:
                    continue
                if not self._is_reportable(fp):
                    continue
                rel = os.path.relpath(fp, self.mod_path)
                results.append(
                    (f"Missing icon sprite '{icon}' for focus '{focus_id}'", rel, line)
                )

        self._report(
            results,
            "No missing focus icons found",
            "Focuses with missing icons (icon sprite not defined in interface/*.gfx):",
            Severity.WARNING,
            category="missing-focus-icon",
        )

    def run_validations(self):
        self.validate_duplicate_focus_ids()
        self.validate_missing_prerequisite_targets()
        self.validate_orphan_focuses()
        self.validate_dependency_cycles()
        self.validate_missing_loc_keys()
        self.validate_tech_bonus_names()
        self.validate_missing_search_filters()
        self.validate_ai_will_do_guards()
        self.validate_cross_country_event_tooltips()
        self.validate_pp_malus_in_rewards()

        if self.missing_icons:
            self.validate_focus_icons()
        else:
            self._log_section(
                "Skipping missing icon check (pass --missing-icons to enable)"
            )


def _add_extra_args(parser):
    parser.add_argument(
        "--missing-icons",
        action="store_true",
        dest="missing_icons",
        help="Flag focuses whose icon sprite is undefined in interface/*.gfx",
    )


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate focus tree structure in Millennium Dawn mod",
        extra_args_fn=_add_extra_args,
    )
