#!/usr/bin/env python3
"""
tick_audit.py — Report how much recurring work Millennium Dawn does every
in-game day / week / month.

HOI4 only auto-fires six recurring on_action hooks per country:

    on_daily   on_weekly   on_monthly            (GLOBAL — run for every country,
    on_daily_<TAG>   on_weekly_<TAG>   on_monthly_<TAG>   staggered across the period)

Everything that "runs daily/weekly/monthly" ultimately hangs off one of those
hooks. This tool traces that graph and reports the cost, with one hard rule:

    ACCURACY CONTRACT — a scripted_effect, event, or decision is only reported
    as running on a cadence if it is genuinely REACHABLE from a real recurring
    hook of that cadence (directly, through a scripted_effect the hook calls,
    or as a self-rescheduling event loop). An event that merely EXISTS in
    events/ is never counted. `country_event = { id = X days = N }` is treated
    as a one-shot DELAY, not recurrence — it only becomes recurring if X
    reschedules itself (a loop), which is detected separately.

What it measures
    A (on_actions):  each recurring hook, the scripted_effects it invokes
                     (expanded transitively, as a work proxy), and the events it
                     fires DIRECTLY in its own body (country_event/news_event vs.
                     weighted random_events pools). Events fired only deep inside
                     shared scripted_effects are counted as work but NOT
                     attributed as fires — their firing is gated by in-effect
                     conditions (e.g. original_tag) that can't be evaluated
                     statically, so per-country attribution would over-report.
    B (timers):      timed decisions (real timer fields days_mission_timeout /
                     days_remove / days_re_enable, literal vs variable) bucketed
                     by period, and self-rescheduling event loops (immediate =
                     automatic tick, option = player-driven).

Usage
    python3 tools/run.py tick_audit                 # summary, all cadences
    python3 tools/run.py tick_audit --cadence weekly
    python3 tools/run.py tick_audit --top 25        # heaviest-country table size
    python3 tools/run.py tick_audit --json out.json # machine-readable dump

    # Drill down into EXACTLY what is flagged (each item with file:line):
    python3 tools/run.py tick_audit --list all
    python3 tools/run.py tick_audit --list events --cadence monthly
    python3 tools/run.py tick_audit --list hooks --tag USA
    python3 tools/run.py tick_audit --list decisions --limit 0   # no cap

Nothing is written to the mod; this is read-only analysis.
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict

# tools/ (parent of analysis/) on path for shared_utils, mirroring sibling tools.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared_utils import (  # noqa: E402
    Colors,
    extract_block_from_text,
    strip_comments,
)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- HOI4 cadence facts -----------------------------------------------------

# The recurring hooks the engine fires on its own. Everything else is reached
# through these.
CADENCES = ("daily", "weekly", "monthly")
CADENCE_DAYS = {"daily": 1, "weekly": 7, "monthly": 30}

# on_<cadence> or on_<cadence>_<TAG>. TAG is an uppercase 2-4 char country tag.
HOOK_RE = re.compile(r"\bon_(daily|weekly|monthly)(?:_([A-Z0-9]{2,4}))?\b\s*=\s*\{")

# Effect verbs that fire an event. HOI4 accepts both `verb = id` and
# `verb = { id = id ... }` forms.
EVENT_FIRE_VERBS = (
    "country_event",
    "news_event",
    "state_event",
    "unit_leader_event",
    "operative_leader_event",
)

# An identifier as Paradox script allows it: dotted event ids (econvent.1),
# @-scoped variables, digits.
IDENT = r"[A-Za-z_][A-Za-z0-9_.@]*"

# Recursion guard for scripted_effect / event expansion.
MAX_DEPTH = 40

# A "statement" = any `key = ...` assignment. Counting these across a hook and
# everything it calls is a work proxy that captures inline effects AND the
# `limit`/trigger CHECKS the engine evaluates every tick — not just named
# scripted_effect calls (which miss hooks that only fire events / do inline
# work, e.g. on_daily_GER).
STMT_RE = re.compile(IDENT + r"\s*=")


def count_statements(body):
    """Rough count of `key = ...` operations (effects + checks) in `body`."""
    return len(STMT_RE.findall(body))


def bucket_for_days(days):
    """Map a raw day count onto a cadence bucket, keeping the exact value."""
    if days is None:
        return "other"
    if days <= 1:
        return "daily"
    if days <= 10:
        return "weekly"
    if 20 <= days <= 40:
        return "monthly"
    return "other"


# --- lightweight Paradox scanning helpers -----------------------------------


def _iter_txt(subdir):
    """Yield (path, text) for every .txt under REPO_ROOT/<subdir>."""
    base = os.path.join(REPO_ROOT, subdir)
    if not os.path.isdir(base):
        return
    for root, _dirs, files in os.walk(base):
        for name in files:
            if name.endswith(".txt"):
                path = os.path.join(root, name)
                try:
                    with open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
                        yield path, fh.read()
                except OSError:
                    continue


def _rel(path):
    return os.path.relpath(path, REPO_ROOT).replace("\\", "/")


def _top_level_blocks(text, _pre_stripped=False):
    """Yield (name, body, start) for each `name = { ... }` at brace-depth 0.

    `start` is the offset of `name` within the (comment-stripped) text, for line
    numbers. Comments are stripped first so `#` braces never corrupt matching;
    pass ``_pre_stripped=True`` when the caller already stripped them.
    """
    clean = text if _pre_stripped else strip_comments(text)
    pos = 0
    name_re = re.compile(r"(" + IDENT + r")\s*=\s*\{")
    while True:
        m = name_re.search(clean, pos)
        if not m:
            return
        body, end = extract_block_from_text(clean, m.end() - 1)
        if end == -1:
            return
        yield m.group(1), body, m.start()
        pos = end


def _depth0_assignments(body):
    """Return {key: value} for scalar `key = value` pairs at brace depth 0.

    Block-valued keys (`key = { ... }`) and anything nested inside braces are
    ignored. This is how a decision/effect's OWN direct fields are read without
    being fooled by a `days = N` buried inside a child effect.
    """
    assign_re = re.compile(r"(" + IDENT + r")\s*=\s*(-?[A-Za-z0-9_.@]+)")
    result = {}
    depth = 0
    i = 0
    n = len(body)
    while i < n:
        c = body[i]
        if c == "{":
            depth += 1
            i += 1
        elif c == "}":
            depth -= 1
            i += 1
        elif depth == 0:
            m = assign_re.match(body, i)
            if m:
                result.setdefault(m.group(1), m.group(2))
                i = m.end()
            else:
                i += 1
        else:
            i += 1
    return result


def _line_of(text, index):
    return text.count("\n", 0, index) + 1


# --- index construction -----------------------------------------------------


def index_scripted_effects():
    """name -> body text for every scripted_effect definition."""
    effects = {}
    for _path, text in _iter_txt("common/scripted_effects"):
        for name, body, _start in _top_level_blocks(text):
            # First definition wins on duplicates; MD does not intentionally
            # redefine, and load order would make the first the live one anyway.
            effects.setdefault(name, body)
    return effects


def index_events():
    """id -> {type, file, line, body} for every event DEFINITION.

    Only depth-0 `verb = { id = ... }` blocks count as definitions. Fire sites
    like `country_event = { id = X days = 3 }` sit nested inside options/effects
    and are skipped, so a fire stub can never masquerade as the real event body.
    """
    events = {}
    verbs = set(EVENT_FIRE_VERBS)
    for path, text in _iter_txt("events"):
        clean = strip_comments(text)
        for name, body, start in _top_level_blocks(clean, _pre_stripped=True):
            if name not in verbs:
                continue
            idm = re.search(r"\bid\s*=\s*(" + IDENT + r")", body)
            if not idm:
                continue
            events.setdefault(
                idm.group(1),
                {
                    "type": name,
                    "file": _rel(path),
                    "line": _line_of(clean, start),
                    "body": body,
                },
            )
    return events


# --- fire extraction --------------------------------------------------------


def extract_scripted_calls(body, effect_names):
    """Return the set of scripted_effect names invoked directly in `body`.

    Matches `name = yes` and `name = { ... }` (argument form) where `name` is a
    known scripted_effect. Restricting to known names avoids counting ordinary
    effects/triggers as calls.
    """
    calls = set()
    for m in re.finditer(r"(" + IDENT + r")\s*=\s*(?:yes\b|\{)", body):
        name = m.group(1)
        if name in effect_names:
            calls.add(name)
    return calls


def extract_direct_event_fires(body):
    """Events fired unconditionally by `verb = id` / `verb = { id = id ... }`.

    Returns list of (event_id, days_or_None). `days` marks a scheduled delay.
    """
    fires = []
    for verb in EVENT_FIRE_VERBS:
        # verb = { id = X ... days = N ... }
        for m in re.finditer(verb + r"\s*=\s*\{", body):
            block, end = extract_block_from_text(body, m.end() - 1)
            if end == -1:
                continue
            idm = re.search(r"\bid\s*=\s*(" + IDENT + r")", block)
            if not idm:
                continue
            dm = re.search(r"\bdays\s*=\s*(\d+)", block)
            fires.append((idm.group(1), int(dm.group(1)) if dm else None))
        # verb = X   (bare id, no block)
        for m in re.finditer(verb + r"\s*=\s*(" + IDENT + r")", body):
            fires.append((m.group(1), None))
    return fires


def extract_random_events(body):
    """Event ids in every `random_events = { weight = id ... }` pool in `body`.

    These are weighted candidates: at most ~one fires per tick. Returns a flat
    list of candidate event ids (duplicates across pools preserved).
    """
    candidates = []
    for m in re.finditer(r"random_events\s*=\s*\{", body):
        block, end = extract_block_from_text(body, m.end() - 1)
        if end == -1:
            continue
        for em in re.finditer(r"\d+\s*=\s*(" + IDENT + r")", block):
            candidates.append(em.group(1))
    return candidates


def extract_plain_events_block(body):
    """Event ids in an `events = { id id ... }` list (fired every tick)."""
    ids = []
    for m in re.finditer(r"\bevents\s*=\s*\{", body):
        block, end = extract_block_from_text(body, m.end() - 1)
        if end == -1:
            continue
        for em in re.finditer(r"\b(" + IDENT + r"\.[A-Za-z0-9_]+)\b", block):
            ids.append(em.group(1))
    return ids


# --- transitive expansion ---------------------------------------------------


def expand_effect(name, effects, cache, _stack):
    """Transitive closure of scripted_effect calls from `name`.

    Returns (reached_effects, call_edges) where reached_effects is the set of
    scripted_effects invoked (excluding `name` itself) and call_edges is the
    total number of call sites walked — a proxy for per-tick work volume.
    Recursion is bounded and cycle-safe.
    """
    if name in cache:
        return cache[name]
    if name in _stack or len(_stack) > MAX_DEPTH:
        return set(), 0
    body = effects.get(name)
    if body is None:
        return set(), 0
    _stack.add(name)
    reached = set()
    edges = 0
    for callee in extract_scripted_calls(body, effects):
        edges += 1
        reached.add(callee)
        sub_reached, sub_edges = expand_effect(callee, effects, cache, _stack)
        reached |= sub_reached
        edges += sub_edges
    _stack.discard(name)
    result = (reached, edges)
    # Only memoize acyclic results (stack empty of this name already handled).
    cache[name] = result
    return result


def _named_subblock(body, key):
    """Return the body of the first `key = { ... }` inside `body`, or ''."""
    m = re.search(r"\b" + re.escape(key) + r"\s*=\s*\{", body)
    if not m:
        return ""
    sub, end = extract_block_from_text(body, m.end() - 1)
    return sub if end != -1 else ""


# --- A: on_actions cadence inventory ----------------------------------------


def collect_hooks(effects, events, effect_cache):
    """Parse every recurring on_action hook into a structured record."""
    hooks = []
    for path, text in _iter_txt("common/on_actions"):
        clean = strip_comments(text)
        for m in HOOK_RE.finditer(clean):
            cadence, tag = m.group(1), m.group(2)
            body, end = extract_block_from_text(clean, m.end() - 1)
            if end == -1:
                continue
            direct_calls = extract_scripted_calls(body, effects)
            reached = set()
            edges = 0
            for name in direct_calls:
                reached.add(name)
                sub, sub_edges = expand_effect(name, effects, effect_cache, set())
                reached |= sub
                edges += 1 + sub_edges
            # Work proxy: inline statements in the hook (effects + checks + event
            # fires) plus statements in every scripted_effect it reaches. Each
            # reached effect counted once. This is what makes on_daily_GER (fires
            # events, calls no named effect) register as real work.
            work = count_statements(body) + sum(
                count_statements(effects.get(name, "")) for name in reached
            )
            # Event fires are taken ONLY from the hook's own text. Events fired
            # deep inside called scripted_effects are deliberately NOT attributed
            # here: those fires are gated by in-effect conditions (e.g.
            # `if = { limit = { original_tag = HOL } ... }`) that cannot be
            # evaluated statically, so attributing them to every caller would
            # over-report. They still count as work via `call_edges`.
            direct_events = {
                eid for eid, _d in extract_direct_event_fires(body) if eid in events
            }
            direct_events |= {
                eid for eid in extract_plain_events_block(body) if eid in events
            }
            random_pool = {eid for eid in extract_random_events(body) if eid in events}
            hooks.append(
                {
                    "cadence": cadence,
                    "scope": tag if tag else "GLOBAL",
                    "file": _rel(path),
                    "line": _line_of(clean, m.start()),
                    "direct_effect_calls": sorted(direct_calls),
                    "reached_effects": sorted(reached),
                    "call_edges": edges,
                    "work_units": work,
                    "events_direct": sorted(direct_events),
                    "events_random": sorted(random_pool),
                }
            )
    return hooks


# --- B: timed decisions -----------------------------------------------------


# HOI4 decision timer fields (direct children of a decision). A bare `days = N`
# is NOT a decision timer in HOI4 — these are the real ones.
DECISION_TIMER_FIELDS = ("days_mission_timeout", "days_remove", "days_re_enable")


def collect_timed_decisions():
    """Decisions with a real timer field, bucketed by period.

    Files nest: category = { decision = { ... } }. A timer only counts when it
    is a DIRECT child of the decision (read via _depth0_assignments), so a
    `days = N` sitting inside `set_country_flag = { ... }` or a fired event is
    never mistaken for the decision's own timer. Timer values that are variables
    or script expressions (e.g. `ROOT.battery_park_time`) cannot be resolved to
    a number statically and are bucketed as 'variable'.
    """
    timed = []
    for path, text in _iter_txt("common/decisions"):
        clean = strip_comments(text)
        for _cat, cat_body, cat_start in _top_level_blocks(clean, _pre_stripped=True):
            cat_body_start = clean.find("{", cat_start) + 1
            for dname, dbody, doff in _top_level_blocks(cat_body, _pre_stripped=True):
                fields = _depth0_assignments(dbody)
                timers = {f: fields[f] for f in DECISION_TIMER_FIELDS if f in fields}
                if not timers:
                    continue
                # Choose the shortest literal timer as the effective period;
                # if none are literal, mark the decision variable-timed.
                literals = {
                    f: int(v) for f, v in timers.items() if v.lstrip("-").isdigit()
                }
                if literals:
                    field, days = min(literals.items(), key=lambda kv: kv[1])
                    bucket = bucket_for_days(days)
                else:
                    field = next(iter(timers))
                    days = None
                    bucket = "variable"
                line = _line_of(clean, cat_body_start + doff)
                recurring = fields.get("fire_only_once", "yes") == "no"
                timed.append(
                    {
                        "name": dname,
                        "timer_field": field,
                        "timer_value": timers[field],
                        "days": days,
                        "bucket": bucket,
                        "recurring": recurring,
                        "file": _rel(path),
                        "line": line,
                    }
                )
    return timed


# --- B: self-rescheduling event loops ---------------------------------------


def collect_event_loops(events):
    """Events that reschedule THEMSELVES — genuine recurring event cycles.

    The classic MD pattern: an event whose `immediate = {}` re-fires its own id
    (usually `days = N`), so once started it ticks forever. That is real
    recurrence, unlike a one-shot delayed fire.

    A self-fire found only in an `option = {}` is player-driven, not an
    automatic tick, so it is recorded with trigger='option' and NOT bucketed
    onto a cadence — keeping the cadence counts honest. Multi-event cycles
    (A->B->A) are not traced in v1 and are noted as a limitation.
    """
    loops = []
    for eid, info in events.items():
        body = info["body"]
        immediate = _named_subblock(body, "immediate")
        trigger = None
        days = None
        # Prefer an automatic self-fire from immediate.
        for fired_id, d in extract_direct_event_fires(immediate):
            if fired_id == eid:
                trigger, days = "immediate", d
                break
        if trigger is None:
            # Otherwise look anywhere else (options / nested), mark as player.
            for fired_id, d in extract_direct_event_fires(body):
                if fired_id == eid:
                    trigger, days = "option", d
                    break
        if trigger is None:
            continue
        loops.append(
            {
                "id": eid,
                "days": days,
                # Player-driven loops are not on a fixed cadence.
                "bucket": bucket_for_days(days) if trigger == "immediate" else "player",
                "trigger": trigger,
                "type": info["type"],
                "file": info["file"],
                "line": info["line"],
            }
        )
    return loops


# --- call tree + flamegraph (profiler-style view) ---------------------------


def index_effect_locations():
    """name -> 'relpath:line' for every scripted_effect definition."""
    loc = {}
    for path, text in _iter_txt("common/scripted_effects"):
        clean = strip_comments(text)
        for name, _body, start in _top_level_blocks(clean, _pre_stripped=True):
            loc.setdefault(name, _rel(path) + ":" + str(_line_of(clean, start)))
    return loc


def _event_leaf(eid, events, random=False):
    info = events[eid]
    return {
        "name": eid,
        "kind": "random_event" if random else "event",
        "file": info["file"] + ":" + str(info["line"]),
        "ops": 1,
        "total": 1,
        "children": [],
    }


def _effect_subtree(name, effects, events, loc, path, depth, budget, counter):
    """Build the call subtree rooted at scripted_effect `name`.

    Sized by `ops` (statements). Cycle-safe (an effect already on the path is
    marked recursive and not re-expanded) and bounded by depth + a node budget
    so a pathological chain can't blow up the HTML.
    """
    body = effects.get(name, "")
    node = {
        "name": name,
        "kind": "effect",
        "file": loc.get(name),
        "ops": count_statements(body),
        "children": [],
    }
    counter[0] += 1
    if name in path:
        node["recursive"] = True
    elif depth < budget["depth"] and counter[0] < budget["nodes"]:
        newpath = path | {name}
        for callee in sorted(extract_scripted_calls(body, effects)):
            node["children"].append(
                _effect_subtree(
                    callee, effects, events, loc, newpath, depth + 1, budget, counter
                )
            )
        seen = set()
        for eid, _d in extract_direct_event_fires(body):
            if eid in events and eid not in seen:
                seen.add(eid)
                node["children"].append(_event_leaf(eid, events))
        for eid in extract_random_events(body):
            if eid in events and eid not in seen:
                seen.add(eid)
                node["children"].append(_event_leaf(eid, events, random=True))
    elif node["children"] == [] and count_statements(body):
        node["truncated"] = True
    node["total"] = node["ops"] + sum(c["total"] for c in node["children"])
    node["children"].sort(key=lambda c: -c["total"])
    return node


def build_call_tree(effects, events, loc, max_depth=22, max_nodes=9000):
    """Root -> cadence -> hook -> scripted_effect/event call tree.

    This is the static reconstruction of what each recurring tick runs, shaped
    like a profiler flamegraph and sized by `ops` instead of measured ms.
    """
    budget = {"depth": max_depth, "nodes": max_nodes}
    cad = {
        c: {"name": c.upper(), "kind": "cadence", "ops": 0, "children": []}
        for c in CADENCES
    }
    for path, text in _iter_txt("common/on_actions"):
        clean = strip_comments(text)
        for m in HOOK_RE.finditer(clean):
            cadence, tag = m.group(1), m.group(2)
            body, end = extract_block_from_text(clean, m.end() - 1)
            if end == -1:
                continue
            counter = [0]
            children = []
            for callee in sorted(extract_scripted_calls(body, effects)):
                children.append(
                    _effect_subtree(
                        callee, effects, events, loc, frozenset(), 1, budget, counter
                    )
                )
            seen = set()
            for eid, _d in extract_direct_event_fires(body):
                if eid in events and eid not in seen:
                    seen.add(eid)
                    children.append(_event_leaf(eid, events))
            for eid in extract_random_events(body):
                if eid in events and eid not in seen:
                    seen.add(eid)
                    children.append(_event_leaf(eid, events, random=True))
            self_ops = count_statements(body)
            children.sort(key=lambda c: -c["total"])
            node = {
                "name": "on_" + cadence + (("_" + tag) if tag else ""),
                "scope": tag or "GLOBAL",
                "kind": "hook",
                "file": _rel(path) + ":" + str(_line_of(clean, m.start())),
                "ops": self_ops,
                "children": children,
                "total": self_ops + sum(c["total"] for c in children),
            }
            cad[cadence]["children"].append(node)
    root = {"name": "Millennium Dawn - recurring ticks", "kind": "root", "children": []}
    for c in CADENCES:
        n = cad[c]
        n["children"].sort(key=lambda x: -x["total"])
        n["total"] = sum(ch["total"] for ch in n["children"])
        root["children"].append(n)
    root["total"] = sum(c["total"] for c in root["children"])
    root["ops"] = 0
    return root


def write_flamegraph(root, out_path, repo_root):
    """Emit a self-contained interactive HTML flamegraph of the call tree."""
    abs_root = os.path.abspath(repo_root).replace("\\", "/")
    html = (
        _FLAMEGRAPH_HTML.replace("/*DATA*/null", json.dumps(root))
        .replace("__REPO__", abs_root)
        .replace("__TOTAL__", str(root["total"]))
    )
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(html)


# aggregation ----------------------------------------------------------------


def build_report(tag_filter=None):
    effects = index_scripted_effects()
    events = index_events()
    effect_cache = {}

    hooks = collect_hooks(effects, events, effect_cache)
    timed_decisions = collect_timed_decisions()
    event_loops = collect_event_loops(events)

    # Event-centric detail: for each flagged event, where it is DEFINED and
    # which hook(s) fire it. Powers the `--list events` drill-down.
    event_fires = {}
    for h in hooks:
        for kind, key in (("direct", "events_direct"), ("random", "events_random")):
            for eid in h[key]:
                loc = events.get(eid, {})
                rec = event_fires.setdefault(
                    eid,
                    {
                        "def": f"{loc.get('file', '?')}:{loc.get('line', '?')}",
                        "type": loc.get("type", "?"),
                        "fired_by": [],
                    },
                )
                rec["fired_by"].append(
                    {
                        "cadence": h["cadence"],
                        "scope": h["scope"],
                        "hook": f"{h['file']}:{h['line']}",
                        "kind": kind,
                    }
                )

    report = {
        "totals": {
            "scripted_effects_indexed": len(effects),
            "events_indexed": len(events),
        },
        "cadences": {},
        "timed_decisions": timed_decisions,
        "event_loops": event_loops,
        "event_fires": event_fires,
        "hooks": hooks,
    }

    for cadence in CADENCES:
        ch = [h for h in hooks if h["cadence"] == cadence]
        globals_ = [h for h in ch if h["scope"] == "GLOBAL"]
        per_tag = [h for h in ch if h["scope"] != "GLOBAL"]
        tags = sorted({h["scope"] for h in per_tag})
        # Distinct events fired DIRECTLY by hooks on this cadence (no spray
        # through shared scripted_effects — see collect_hooks).
        ev_direct = set()
        ev_random = set()
        for h in ch:
            ev_direct.update(h["events_direct"])
            ev_random.update(h["events_random"])
        # Deterministic per-tick work for a GLOBAL tick (every country pays it).
        global_work = sum(h["work_units"] for h in globals_)
        report["cadences"][cadence] = {
            "global_hooks": len(globals_),
            "per_country_hooks": len(per_tag),
            "countries_with_own_hook": tags,
            "global_work_units": global_work,
            "events_direct": sorted(ev_direct),
            "events_random_pool": sorted(ev_random),
            "timed_decisions": [d for d in timed_decisions if d["bucket"] == cadence],
            "event_loops": [e for e in event_loops if e["bucket"] == cadence],
        }

    # Per-country workload: GLOBAL hooks (paid by all) + that country's own tags.
    per_country = defaultdict(
        lambda: {c: {"work": 0, "own_hooks": 0} for c in CADENCES}
    )
    global_work_by_cadence = {
        c: sum(
            h["work_units"]
            for h in hooks
            if h["cadence"] == c and h["scope"] == "GLOBAL"
        )
        for c in CADENCES
    }
    for h in hooks:
        if h["scope"] == "GLOBAL":
            continue
        pc = per_country[h["scope"]]
        pc[h["cadence"]]["work"] += h["work_units"]
        pc[h["cadence"]]["own_hooks"] += 1

    country_rows = []
    for tag, data in per_country.items():
        total = sum(data[c]["work"] + global_work_by_cadence[c] for c in CADENCES)
        country_rows.append(
            {
                "tag": tag,
                "total_work_units": total,
                "own_hooks": sum(data[c]["own_hooks"] for c in CADENCES),
                "by_cadence": {
                    c: data[c]["work"] + global_work_by_cadence[c] for c in CADENCES
                },
            }
        )
    country_rows.sort(key=lambda r: r["total_work_units"], reverse=True)
    report["global_work_by_cadence"] = global_work_by_cadence
    report["per_country"] = country_rows

    if tag_filter:
        report["focus_tag"] = tag_filter
        report["focus_hooks"] = [
            h for h in hooks if h["scope"] in (tag_filter, "GLOBAL")
        ]
    return report


# --- rendering --------------------------------------------------------------


def _c(color, text, use_colors):
    return f"{color}{text}{Colors.ENDC}" if use_colors else str(text)


def render_text(report, top, cadence_filter, use_colors):
    out = []
    B, C, G, Y, DIM = (
        Colors.BOLD,
        Colors.CYAN,
        Colors.GREEN,
        Colors.YELLOW,
        Colors.GRAY if hasattr(Colors, "GRAY") else "",
    )
    t = report["totals"]
    out.append(_c(B, "MILLENNIUM DAWN - RECURRING TICK AUDIT", use_colors))
    out.append(
        f"Indexed {t['scripted_effects_indexed']} scripted_effects, "
        f"{t['events_indexed']} events.  "
        + _c(DIM, "(only work reachable from real hooks is counted)", use_colors)
    )
    out.append("")

    shown = [cadence_filter] if cadence_filter else CADENCES
    for cadence in shown:
        cd = report["cadences"][cadence]
        header = f"== {cadence.upper()} " + "=" * (60 - len(cadence))
        out.append(_c(B + C, header, use_colors))
        out.append(
            f"  Hooks: {_c(G, cd['global_hooks'], use_colors)} global"
            f"  +  {_c(G, cd['per_country_hooks'], use_colors)} per-country"
            f" across {len(cd['countries_with_own_hook'])} countries"
        )
        out.append(
            f"  Per-tick script ops in GLOBAL hooks (effects + checks, paid by "
            f"every country): {_c(Y, cd['global_work_units'], use_colors)}"
        )
        out.append(
            f"  Events fired directly by these hooks: "
            f"{_c(Y, len(cd['events_direct']), use_colors)} via country_event/"
            f"news_event, {_c(Y, len(cd['events_random_pool']), use_colors)} in "
            f"random_events pools "
            f"{_c(DIM, '(~1 fires per tick, weighted)', use_colors)}"
        )
        if cd["timed_decisions"]:
            out.append(
                f"  Timed decisions (days~{CADENCE_DAYS[cadence]}): "
                f"{_c(Y, len(cd['timed_decisions']), use_colors)}"
            )
        if cd["event_loops"]:
            out.append(
                f"  Self-rescheduling event loops: "
                f"{_c(Y, len(cd['event_loops']), use_colors)}"
            )
        out.append("")

    if not cadence_filter:
        out.append(
            _c(
                B + C,
                "== HEAVIEST COUNTRIES (by per-tick script ops) " + "=" * 14,
                use_colors,
            )
        )
        out.append(
            _c(
                DIM,
                "  ops = effects + limit/trigger checks; total = own hooks + all "
                "GLOBAL hooks it also runs",
                use_colors,
            )
        )
        out.append(
            f"  {'TAG':<6}{'total':>8}{'daily':>8}{'weekly':>8}{'monthly':>9}{'own':>6}"
        )
        for row in report["per_country"][:top]:
            bc = row["by_cadence"]
            out.append(
                f"  {row['tag']:<6}{row['total_work_units']:>8}"
                f"{bc['daily']:>8}{bc['weekly']:>8}{bc['monthly']:>9}"
                f"{row['own_hooks']:>6}"
            )
        out.append("")

    # Timers summary (B) across all cadences.
    td = report["timed_decisions"]
    el = report["event_loops"]
    out.append(_c(B + C, "== TIMERS (B) " + "=" * 47, use_colors))
    by_bucket = defaultdict(int)
    for d in td:
        by_bucket[d["bucket"]] += 1
    recurring_n = sum(1 for d in td if d["recurring"])
    out.append(
        "  Timed decisions: "
        + ", ".join(
            f"{by_bucket[b]} {b}"
            for b in ("daily", "weekly", "monthly", "variable", "other")
        )
        + f"  (total {len(td)}; {recurring_n} recurring / fire_only_once=no)"
    )
    loop_bucket = defaultdict(int)
    for e in el:
        loop_bucket[e["bucket"]] += 1
    auto_n = sum(1 for e in el if e["trigger"] == "immediate")
    out.append(
        "  Self-rescheduling event loops (immediate=auto): "
        + ", ".join(
            f"{loop_bucket[b]} {b}"
            for b in ("daily", "weekly", "monthly", "other", "player")
        )
        + f"  (total {len(el)}; {auto_n} auto)"
    )
    out.append("")
    out.append(
        _c(
            DIM,
            "Notes: GLOBAL hooks fire once per country per period, "
            "staggered by the engine across the period (they are not all "
            "spent on the same day). 'ops' counts `key = ...` statements "
            "(effects + limit/trigger checks) in each hook plus every "
            "scripted_effect it reaches - a work proxy, not CPU time. "
            "`country_event ... days=N` is a one-shot delay unless the event "
            "reschedules itself (counted under loops).",
            use_colors,
        )
    )
    return "\n".join(out)


LIST_CHOICES = ("hooks", "events", "decisions", "loops")


def render_list(report, what, cadence_filter, tag_filter, limit, use_colors):
    """Itemize exactly WHAT the audit flags, with file:line for each item.

    Honors --cadence and --tag. `limit` caps each section (0 = unlimited) and a
    truncation line is printed so nothing is silently hidden.
    """
    B, C, Y, DIM = Colors.BOLD, Colors.CYAN, Colors.YELLOW, Colors.GRAY
    want = set(LIST_CHOICES) if "all" in what else set(what)
    cadences = [cadence_filter] if cadence_filter else list(CADENCES)
    out = []

    def section(title):
        out.append(
            _c(B + C, f"== {title} " + "=" * max(0, 58 - len(title)), use_colors)
        )

    def emit(rows):
        shown = rows if limit == 0 else rows[:limit]
        out.extend(shown)
        if limit and len(rows) > limit:
            out.append(
                _c(DIM, f"  ... {len(rows) - limit} more (raise --limit)", use_colors)
            )
        if not rows:
            out.append(_c(DIM, "  (none)", use_colors))
        out.append("")

    def tag_ok(scope):
        return tag_filter is None or scope in (tag_filter, "GLOBAL")

    if "hooks" in want:
        section("HOOKS (recurring on_action blocks)")
        rows = []
        for h in sorted(
            report["hooks"], key=lambda x: (-x["work_units"], x["cadence"], x["scope"])
        ):
            if h["cadence"] not in cadences or not tag_ok(h["scope"]):
                continue
            nfire = len(h["events_direct"]) + len(h["events_random"])
            rows.append(
                f"  [{h['cadence']:<7}] {h['scope']:<7} "
                f"{_c(Y, str(h['work_units']) + ' ops', use_colors)}, "
                f"{h['call_edges']} calls, "
                f"{nfire} event-fires  {_c(DIM, h['file'] + ':' + str(h['line']), use_colors)}"
            )
        emit(rows)

    if "events" in want:
        section("EVENTS fired directly by recurring hooks")
        rows = []
        for eid, rec in sorted(report["event_fires"].items()):
            fb = [
                f
                for f in rec["fired_by"]
                if f["cadence"] in cadences and tag_ok(f["scope"])
            ]
            if not fb:
                continue
            cad = sorted({f["cadence"] for f in fb})
            scopes = sorted({f["scope"] for f in fb})
            kinds = sorted({f["kind"] for f in fb})
            rows.append(
                f"  {_c(Y, eid, use_colors)} "
                f"[{','.join(cad)}] by {','.join(scopes)} ({','.join(kinds)})  "
                f"{_c(DIM, 'def ' + rec['def'], use_colors)}"
            )
        emit(rows)

    if "decisions" in want:
        section("TIMED DECISIONS (real timer fields)")
        rows = []
        for d in sorted(
            report["timed_decisions"], key=lambda x: (x["bucket"], x["name"])
        ):
            if cadence_filter and d["bucket"] != cadence_filter:
                continue
            rec = " recurring" if d["recurring"] else ""
            rows.append(
                f"  {_c(Y, d['name'], use_colors)}  "
                f"{d['timer_field']}={d['timer_value']} [{d['bucket']}]{rec}  "
                f"{_c(DIM, d['file'] + ':' + str(d['line']), use_colors)}"
            )
        emit(rows)

    if "loops" in want:
        section("SELF-RESCHEDULING EVENT LOOPS")
        rows = []
        for e in sorted(report["event_loops"], key=lambda x: (x["trigger"], x["id"])):
            if cadence_filter and e["bucket"] != cadence_filter:
                continue
            rows.append(
                f"  {_c(Y, e['id'], use_colors)}  {e['trigger']} "
                f"days={e['days']} [{e['bucket']}]  "
                f"{_c(DIM, e['file'] + ':' + str(e['line']), use_colors)}"
            )
        emit(rows)

    return "\n".join(out).rstrip()


# Self-contained flamegraph. Placeholders: /*DATA*/null (tree JSON), __REPO__
# (abs mod root for vscode:// links), __TOTAL__ (root total ops).
_FLAMEGRAPH_HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MD Tick Profiler</title>
<style>
  :root{
    --bg:#0f1620; --panel:#172231; --line:#243244; --ink:#e7edf5; --mut:#8595a9;
    --cadence:#c7d2e0; --hook:#e0a340; --effect:#3fb6a8; --event:#e5644e;
    --random:#b57edc; --track:#101a26;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);
    font:13px/1.5 ui-monospace,"Cascadia Code","Consolas",monospace}
  header{padding:20px 22px 14px;border-bottom:1px solid var(--line)}
  h1{margin:0 0 6px;font-size:17px;letter-spacing:.2px}
  .sub{color:var(--mut);max-width:82ch;font-size:12px}
  .warn{color:#f0c674}
  .legend{display:flex;flex-wrap:wrap;gap:14px;margin-top:10px;font-size:11px;color:var(--mut)}
  .legend span{display:inline-flex;align-items:center;gap:6px}
  .sw{width:10px;height:10px;border-radius:2px;display:inline-block}
  .tools{display:flex;gap:8px;align-items:center;margin-top:12px}
  .tools input{background:var(--track);border:1px solid var(--line);color:var(--ink);
    padding:6px 9px;border-radius:6px;font:inherit;width:260px}
  .tools button{background:var(--panel);border:1px solid var(--line);color:var(--ink);
    padding:6px 10px;border-radius:6px;font:inherit;cursor:pointer}
  .tools button:hover{border-color:var(--hook)}
  #tree{padding:10px 14px 60px}
  .node>.row{position:relative;display:flex;align-items:center;gap:8px;
    padding:2px 8px;border-radius:5px;cursor:default;white-space:nowrap;
    overflow:hidden}
  .node>.row.hask{cursor:pointer}
  .node>.row .fill{position:absolute;left:0;top:0;bottom:0;width:var(--w);
    opacity:.16;border-right:1px solid currentColor}
  .kind-cadence>.row{color:var(--cadence)} .kind-hook>.row{color:var(--hook)}
  .kind-effect>.row{color:var(--effect)} .kind-event>.row{color:var(--event)}
  .kind-random_event>.row{color:var(--random)}
  .node>.row:hover{background:#1b2838}
  .caret{width:12px;color:var(--mut);flex:0 0 auto}
  .nm{color:var(--ink);font-weight:600}
  .kind-event .nm,.kind-random_event .nm{color:inherit;font-weight:600}
  .meta{color:var(--mut);font-size:11px}
  .ops{color:var(--ink);font-variant-numeric:tabular-nums}
  .pct{color:var(--mut);font-variant-numeric:tabular-nums;min-width:52px;text-align:right}
  a.loc{color:var(--mut);text-decoration:none;font-size:11px}
  a.loc:hover{color:var(--hook);text-decoration:underline}
  .kids{margin-left:15px;border-left:1px solid var(--line);padding-left:3px}
  .tag{color:var(--mut)}
  .rec{color:#f0c674;font-size:11px}
  mark{background:#3a4a1e;color:#e7edf5;border-radius:2px}
  #tip{position:fixed;z-index:50;max-width:340px;background:#0b1119;
    border:1px solid var(--line);color:var(--ink);padding:9px 11px;
    border-radius:8px;font-size:12px;line-height:1.5;pointer-events:none;
    display:none;box-shadow:0 8px 26px rgba(0,0,0,.55)}
  #tip b{color:#fff} #tip .m{color:var(--mut)}
  .snote{padding:12px 16px 0;color:var(--mut);font-size:11.5px}
  #summary{display:flex;gap:12px;flex-wrap:wrap;padding:8px 14px 4px}
  .card{flex:1 1 240px;background:var(--panel);border:1px solid var(--line);
    border-left:3px solid var(--hook);border-radius:10px;padding:12px 15px}
  .card h3{margin:0 0 7px;font-size:11px;letter-spacing:1.5px;color:var(--mut)}
  .card .big{font-size:23px;font-weight:700;color:var(--ink);
    font-variant-numeric:tabular-nums}
  .card .big small{font-size:12px;color:var(--mut);font-weight:400}
  .card .brk{font-size:11px;color:var(--mut);margin-top:5px;
    font-variant-numeric:tabular-nums}
  .card .stmt{font-size:11px;color:var(--effect);margin-top:3px;
    font-variant-numeric:tabular-nums}
</style></head><body>
<header>
  <h1>Millennium&nbsp;Dawn — recurring tick profiler</h1>
  <div class="sub"><span class="warn">Static estimate.</span> The in-game
  profiler crashes on a mod this large, so this reconstructs what each recurring
  tick runs by reading the scripts. Every node is sized by <b>ops</b> — the
  count of <code>key = …</code> statements it runs (effects <i>and</i>
  limit/trigger checks), including everything it calls. It's a proxy for cost,
  not measured milliseconds. Click a row to open what it calls; click a file to
  jump to it in VS&nbsp;Code.</div>
  <div class="legend">
    <span><i class="sw" style="background:var(--hook)"></i>on_action hook</span>
    <span><i class="sw" style="background:var(--effect)"></i>scripted_effect</span>
    <span><i class="sw" style="background:var(--event)"></i>event fired</span>
    <span><i class="sw" style="background:var(--random)"></i>random_events pool</span>
  </div>
  <div class="tools">
    <input id="q" placeholder="filter by name (e.g. money, PER, econvent)…">
    <button id="clear">clear</button>
    <span class="meta" id="stat"></span>
  </div>
</header>
<div class="snote">Two ways to count one tick: <b>operations</b> — each hook,
scripted_effect and event counted once (the intuitive "how many things run") —
or <b>ops</b>, each individual script statement (what the bars below use).</div>
<div id="summary"></div>
<div id="tree"></div>
<script>
const ROOT=/*DATA*/null, REPO="__REPO__", TOTAL=__TOTAL__;
const fmt=n=>n.toLocaleString();
function vscode(file){
  if(!file) return null;
  const i=file.lastIndexOf(':'), rel=file.slice(0,i), line=file.slice(i+1);
  return 'vscode://file/'+REPO+'/'+rel+':'+line;
}
const tip=document.createElement('div'); tip.id='tip'; document.body.appendChild(tip);
const PER={daily:'day',weekly:'week',monthly:'month'};
function tipText(node,ctx,share){
  const cad=ctx.cadence||(node.kind==='cadence'?node.name.toLowerCase():null);
  const per=PER[cad]||'tick';
  const ops='<b>'+fmt(node.total)+' instructions</b>';
  const self=fmt(node.ops);
  let s='';
  if(node.kind==='cadence'){
    s='<b>'+node.name+' tick</b><br>Everything the game runs each in-game '+per+
      '. About '+ops+' total across every '+cad+' hook — '+share.toFixed(1)+
      '% of all recurring work.';
  }else if(node.kind==='hook'){
    const who=node.scope==='GLOBAL'
      ? 'for <b>every country</b> (the engine spreads it out across the '+per+')'
      : 'only for <b>'+node.scope+'</b>';
    s='<b>'+node.name+'</b> — an on_action that runs each in-game '+per+', '+who+
      '.<br>About '+ops+' per '+per+' ('+self+
      ' in the hook itself, the rest in what it calls).<br>'+share.toFixed(1)+
      '% of all recurring work.';
  }else if(node.kind==='effect'){
    s='<b>'+node.name+'</b> — a scripted_effect.<br>About '+ops+
      ' each time it runs ('+self+' its own lines, the rest nested in what it '+
      'calls).';
    if(node.recursive) s+='<br><span class="m">Calls itself — not expanded further.</span>';
  }else{
    s='<b>'+node.name+'</b> — an event this fires'+
      (node.kind==='random_event'
        ? ' (one of a weighted random pool; roughly one fires per '+per+')'
        : '')+'.';
  }
  s+='<br><span class="m">ops = script statements — the effects it does <i>and</i>'+
     ' the checks it runs. A proxy for cost, not milliseconds.</span>';
  return s;
}
function makeNode(node,parentTotal,depth,ctx){
  ctx=ctx||{};
  const wrap=document.createElement('div');
  wrap.className='node kind-'+node.kind;
  const row=document.createElement('div'); row.className='row';
  const kids=node.children||[];
  if(kids.length) row.classList.add('hask');
  const pct=parentTotal?(node.total/parentTotal*100):100;
  const share=TOTAL?(node.total/TOTAL*100):0;
  row.addEventListener('mouseenter',()=>{tip.innerHTML=tipText(node,ctx,share);tip.style.display='block';});
  row.addEventListener('mousemove',e=>{
    tip.style.left=Math.min(e.clientX+14,window.innerWidth-354)+'px';
    tip.style.top=Math.min(e.clientY+16,window.innerHeight-tip.offsetHeight-8)+'px';});
  row.addEventListener('mouseleave',()=>{tip.style.display='none';});
  const fill=document.createElement('div'); fill.className='fill';
  fill.style.setProperty('--w',pct.toFixed(3)+'%'); row.appendChild(fill);
  const caret=document.createElement('span'); caret.className='caret';
  caret.textContent=kids.length?'▸':'';
  row.appendChild(caret);
  const nm=document.createElement('span'); nm.className='nm'; nm.textContent=node.name;
  row.appendChild(nm);
  if(node.scope){const t=document.createElement('span');t.className='tag';t.textContent='· '+node.scope;row.appendChild(t);}
  const ops=document.createElement('span'); ops.className='ops';
  ops.textContent=fmt(node.total)+' ops'; row.appendChild(ops);
  if(node.total!==node.ops){const s=document.createElement('span');s.className='meta';s.textContent='(self '+fmt(node.ops)+')';row.appendChild(s);}
  const pc=document.createElement('span'); pc.className='pct';
  pc.textContent=share>=0.1?share.toFixed(1)+'%':''; row.appendChild(pc);
  if(node.recursive){const r=document.createElement('span');r.className='rec';r.textContent='↺ recurses';row.appendChild(r);}
  if(node.truncated){const r=document.createElement('span');r.className='rec';r.textContent='… truncated';row.appendChild(r);}
  if(node.file){const a=document.createElement('a');a.className='loc';a.textContent=node.file;
    const u=vscode(node.file); if(u)a.href=u; row.appendChild(a);
    a.addEventListener('click',e=>e.stopPropagation());}
  wrap.appendChild(row);
  let kidBox=null, built=false, open=false;
  if(kids.length){
    row.addEventListener('click',()=>{
      open=!open;
      if(!built){kidBox=document.createElement('div');kidBox.className='kids';
        const cctx=Object.assign({},ctx);
        if(node.kind==='cadence')cctx.cadence=node.name.toLowerCase();
        if(node.kind==='hook')cctx.scope=node.scope;
        kids.forEach(c=>kidBox.appendChild(makeNode(c,node.total,depth+1,cctx)));
        wrap.appendChild(kidBox);built=true;}
      kidBox.style.display=open?'':'none';
      caret.textContent=open?'▾':'▸';
    });
  }
  wrap._expand=()=>{if(kids.length&&!open)row.click();};
  return wrap;
}
const tree=document.getElementById('tree');
(ROOT.children||[]).forEach(c=>{
  const n=makeNode(c,ROOT.total,0,{}); tree.appendChild(n);
  n._expand(); // open cadences by default
});
document.getElementById('stat').textContent=
  fmt(TOTAL)+' total ops across daily+weekly+monthly';
// per-tick headcount: each hook / effect / event counted once (not by statement)
function subCount(n){return 1+(n.children||[]).reduce((s,c)=>s+subCount(c),0);}
function tally(cad){
  let hooks=0,eff=0,ev=0,g=0;
  (function w(n){for(const c of (n.children||[])){
    if(c.kind==='hook')hooks++;
    else if(c.kind==='effect')eff++;
    else if(c.kind==='event'||c.kind==='random_event')ev++;
    w(c);}})(cad);
  for(const h of cad.children) if(h.scope==='GLOBAL') g+=subCount(h);
  return {hooks,eff,ev,total:hooks+eff+ev,g,stmts:cad.total};
}
document.getElementById('summary').innerHTML=(ROOT.children||[]).map(cad=>{
  const t=tally(cad), per=PER[cad.name.toLowerCase()]||'tick';
  return '<div class="card"><h3>'+cad.name+' TICK</h3>'+
    '<div class="big">~'+fmt(t.g)+' <small>operations / country / '+per+'</small></div>'+
    '<div class="brk">'+fmt(t.total)+' wired across the world · '+t.hooks+
    ' hooks · '+fmt(t.eff)+' effect-calls · '+fmt(t.ev)+' events</div>'+
    '<div class="stmt">= '+fmt(t.stmts)+' script statements (ops)</div></div>';
}).join('');
// filter: show only rows whose name matches, expanding ancestors
const q=document.getElementById('q');
function applyFilter(term){
  term=term.trim().toLowerCase();
  function rec(wrap){
    const nm=wrap.querySelector(':scope > .row .nm');
    const self=nm&&nm.textContent.toLowerCase().includes(term);
    if(nm) nm.innerHTML = (self&&term)
      ? nm.textContent.replace(new RegExp('('+term.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+')','ig'),'<mark>$1</mark>')
      : nm.textContent;
    // ensure children built so we can search them
    if(term){wrap._expand&&wrap._expand();}
    let childHit=false;
    wrap.querySelectorAll(':scope > .kids > .node').forEach(k=>{childHit=rec(k)||childHit;});
    const show=!term||self||childHit;
    wrap.style.display=show?'':'none';
    const kb=wrap.querySelector(':scope > .kids');
    if(kb&&term) kb.style.display=childHit?'':'none';
    return show;
  }
  tree.querySelectorAll(':scope > .node').forEach(rec);
}
let t=null;
q.addEventListener('input',()=>{clearTimeout(t);t=setTimeout(()=>applyFilter(q.value),180);});
document.getElementById('clear').addEventListener('click',()=>{q.value='';location.reload();});
</script></body></html>"""


# --- CLI --------------------------------------------------------------------


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Audit Millennium Dawn's daily/weekly/monthly recurring workload."
    )
    parser.add_argument(
        "--cadence", choices=CADENCES, help="Restrict the report to one cadence."
    )
    parser.add_argument(
        "--top",
        type=int,
        default=20,
        help="How many countries to list in the heaviest-country table.",
    )
    parser.add_argument(
        "--tag", help="Focus a single country tag (filters --list hooks/events)."
    )
    parser.add_argument(
        "--list",
        nargs="+",
        choices=LIST_CHOICES + ("all",),
        metavar="{hooks,events,decisions,loops,all}",
        help="Itemize exactly what is flagged, with file:line, instead of the "
        "summary. Combine with --cadence / --tag / --limit.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Max items per --list section (0 = unlimited). Default 50.",
    )
    parser.add_argument("--json", metavar="PATH", help="Write the full report as JSON.")
    parser.add_argument(
        "--flamegraph",
        metavar="PATH",
        help="Write a self-contained interactive HTML call-tree (profiler-style "
        "view of what each tick runs). Open it in a browser.",
    )
    parser.add_argument(
        "--tree", metavar="PATH", help="Write the raw call tree as JSON."
    )
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI colors.")
    args = parser.parse_args(argv)

    # The call-tree outputs re-parse the mod once and are independent of the
    # text report, so handle them first and return if that's all that's asked.
    if args.flamegraph or args.tree:
        effects = index_scripted_effects()
        events = index_events()
        loc = index_effect_locations()
        root = build_call_tree(effects, events, loc)
        if args.tree:
            with open(args.tree, "w", encoding="utf-8") as fh:
                json.dump(root, fh, indent=1)
            print(f"Wrote {args.tree}")
        if args.flamegraph:
            write_flamegraph(root, args.flamegraph, REPO_ROOT)
            print(f"Wrote {args.flamegraph}  ({root['total']:,} total ops)")
        if not (args.json or args.list):
            return 0

    report = build_report(tag_filter=args.tag)

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
        print(f"Wrote {args.json}")

    use_colors = not args.no_color and sys.stdout.isatty()
    if args.list:
        print(
            render_list(
                report, args.list, args.cadence, args.tag, args.limit, use_colors
            )
        )
    else:
        print(render_text(report, args.top, args.cadence, use_colors))
    return 0


if __name__ == "__main__":
    sys.exit(main())
