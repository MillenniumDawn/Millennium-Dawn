#!/usr/bin/env python3
"""
ai_path_report.py — facts for one country's AI path game rule (issue #3162).

Replaces reading an 8k-42k line focus tree by hand: resolves the country's rule,
flag wiring, scripted path triggers and focus weights, then reports what breaks.

Usage:
    python3 tools/analysis/ai_path_report.py --tag DEN
    python3 tools/analysis/ai_path_report.py --tag DEN --section matrix --limit 20
    python3 tools/analysis/ai_path_report.py --tag DEN --format json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Dict, Iterator, List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from shared_utils import (  # noqa: E402
    PARTY_SLOT_NAMES,
    blank_quoted_strings,
    find_matching_brace,
    iter_focus_blocks,
    iter_statements,
    line_of,
    read_script,
    strip_comments,
)

SECTIONS = (
    "rule",
    "wiring",
    "owners",
    "matrix",
    "graph",
    "plans",
    "rewards",
    "mechanics",
    "government",
)

DANGER_EFFECTS = (
    "delete_unit",
    "change_tag",
    "change_tag_from",
    "start_civil_war",
    "annex_country",
    "puppet",
    "set_politics",
    "drop_cosmetic_tag",
)

GUARD_TOKENS = (
    "can_staff_an_",
    "bankruptcy_incoming_collapse",
    "ai_is_threatened",
)

BOOKMARK_DATES = ((2016, 1, 2), (2017, 1, 1))
START_YEAR = 2000
TIMELINE_MIN_DATES = 3
DAYS_PER_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

_ID_LINE = re.compile(r"^[ \t]*id\s*=\s*(\S+)", re.M)
_LOC_KEY = re.compile(r'^\s*([A-Za-z_][A-Za-z0-9_]*):\s*\d*\s*"(.*)"\s*$')
_YEAR = re.compile(r"\b(19|20)\d{2}\b")
_HIGHLIGHT = re.compile(r"§.*?§!")
_LOC_SCOPE = re.compile(r"\[[^\]]*\]")
_TOP_BLOCK = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\{", re.M)
_STATE_BLOCK = re.compile(r"^[ \t]*\d+\s*=\s*\{", re.M)
_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_REMOVE_IDEA = re.compile(r"remove_ideas?\s*=\s*(\{[^{}]*\}|[A-Za-z_][A-Za-z0-9_]*)")
_REMOVE_DYNAMIC = re.compile(
    r"remove_dynamic_modifier\s*=\s*\{[^{}]*?modifier\s*=\s*([A-Za-z_][A-Za-z0-9_]*)"
)
_ADD_TO_VARIABLE = re.compile(
    r"add_to_variable\s*=\s*\{\s*(?:var\s*=\s*)?([A-Za-z_][A-Za-z0-9_.:^]*)"
)
_MODIFIER_NAME = re.compile(r"modifier\s*=\s*([A-Za-z_][A-Za-z0-9_]*)")
_AI_BLOCKED = re.compile(r"is_ai\s*=\s*no\b")
_PARTY_GATE = re.compile(r"[a-z_]+_in_power(?:_or_coalition)?")
_IDEA_KEYWORDS = ("idea", "ideas")

# Three-valued logic: None means "depends on something this tool cannot model".
TRUE, FALSE, UNKNOWN = True, False, None


# --------------------------------------------------------------------------
# Script parsing
# --------------------------------------------------------------------------


def iter_txt_files(folder: str) -> Iterator[str]:
    """Yield every .txt path directly in *folder*, in a stable order."""
    if not os.path.isdir(folder):
        return
    for name in sorted(os.listdir(folder)):
        if name.endswith(".txt"):
            yield os.path.join(folder, name)


def read_raw(path: str) -> str:
    with open(path, "r", encoding="utf-8-sig", errors="replace") as handle:
        return handle.read()


# --------------------------------------------------------------------------
# Trigger expressions
# --------------------------------------------------------------------------

Expr = Tuple  # ("and"|"or"|"not"|"flag"|"hist"|"call"|"unknown", ...)


def parse_expr(body: str, tag: str) -> Expr:
    """Parse a trigger body into an AND-of-children expression tree."""
    children: List[Expr] = []
    for key, scalar, block in iter_statements(body):
        children.append(_parse_statement(key, scalar, block, tag))
    return ("and", children)


def _parse_statement(
    key: str, scalar: Optional[str], block: Optional[str], tag: str
) -> Expr:
    if block is not None:
        if key == "OR":
            return ("or", parse_expr(block, tag)[1])
        if key in ("AND", "hidden_trigger", "custom_trigger_tooltip"):
            return parse_expr(block, tag)
        if key == "NOT":
            return ("not", parse_expr(block, tag))
        return ("unknown",)
    if scalar is None:
        return ("unknown",)
    if key == "has_global_flag":
        if is_path_flag(scalar, tag):
            return ("flag", scalar)
        return ("unknown",)
    if key == "is_historical_focus_on":
        return ("hist", scalar == "yes")
    if is_path_trigger(key, tag):
        node: Expr = ("call", key)
        return node if scalar == "yes" else ("not", node)
    return ("unknown",)


def is_path_flag(name: str, tag: str) -> bool:
    return name.startswith(tag + "_") and name.endswith("_FOCUS_PATH")


def is_path_trigger(name: str, tag: str) -> bool:
    return bool(re.fullmatch(tag + r"_ai_[a-z0-9_]+", name))


def evaluate(
    expr: Expr,
    flag: Optional[str],
    historical: bool,
    triggers: Dict[str, Expr],
    seen: Optional[frozenset] = None,
) -> Optional[bool]:
    """Three-valued evaluation of *expr* under one rule state.

    UNKNOWN never collapses to False: a modifier that cannot be decided is
    reported as unevaluable rather than counted as a killswitch, which is what
    stops the orphan walk inventing phantoms.
    """
    kind = expr[0]
    if kind == "flag":
        return flag == expr[1]
    if kind == "hist":
        return historical == expr[1]
    if kind == "unknown":
        return UNKNOWN
    if kind == "call":
        name = expr[1]
        seen = seen or frozenset()
        if name in seen or name not in triggers:
            return UNKNOWN
        return evaluate(triggers[name], flag, historical, triggers, seen | {name})
    if kind == "not":
        inner = evaluate(expr[1], flag, historical, triggers, seen)
        return UNKNOWN if inner is UNKNOWN else not inner
    values = [evaluate(child, flag, historical, triggers, seen) for child in expr[1]]
    if kind == "or":
        if any(value is TRUE for value in values):
            return TRUE
        return UNKNOWN if any(value is UNKNOWN for value in values) else FALSE
    if any(value is FALSE for value in values):
        return FALSE
    return UNKNOWN if any(value is UNKNOWN for value in values) else TRUE


def _expand_trigger(
    name: str, triggers: Dict[str, Expr], seen: Optional[frozenset] = None
) -> set:
    """Every path token a scripted trigger reaches, transitively."""
    seen = seen or frozenset()
    if name not in triggers or name in seen:
        return set()
    tokens = set()
    for token in expr_tokens(triggers[name]):
        tokens.add(token)
        tokens |= _expand_trigger(token, triggers, seen | {name})
    return tokens


def expr_tokens(expr: Expr) -> Iterator[str]:
    kind = expr[0]
    if kind in ("flag", "call"):
        yield expr[1]
    elif kind == "not":
        yield from expr_tokens(expr[1])
    elif kind in ("and", "or"):
        for child in expr[1]:
            yield from expr_tokens(child)


def load_path_triggers(root: str, tag: str) -> Dict[str, Expr]:
    """Index every `TAG_ai_*` scripted trigger definition in the mod."""
    triggers: Dict[str, Expr] = {}
    opener = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\{", re.M)
    for path in iter_txt_files(os.path.join(root, "common", "scripted_triggers")):
        text = read_script(path)
        for match in opener.finditer(text):
            if not is_path_trigger(match.group(1), tag):
                continue
            close = find_matching_brace(text, match.end() - 1)
            if close == -1:
                continue
            triggers[match.group(1)] = parse_expr(text[match.end() : close], tag)
    return triggers


# --------------------------------------------------------------------------
# Focus model
# --------------------------------------------------------------------------


@dataclass
class Modifier:
    op: str
    value: float
    expr: Expr
    tokens: Tuple[str, ...]
    guard: bool
    line: int

    @property
    def path_related(self) -> bool:
        return bool(self.tokens) and not self.guard


@dataclass
class Focus:
    id: str
    line: int
    kind: str
    prereq_groups: List[List[str]] = field(default_factory=list)
    mutex: List[str] = field(default_factory=list)
    gates: List[str] = field(default_factory=list)
    party_gates: List[str] = field(default_factory=list)
    always_off: bool = False
    base: float = 1.0
    has_ai_will_do: bool = False
    modifiers: List[Modifier] = field(default_factory=list)
    dangers: List[str] = field(default_factory=list)
    cures: List[str] = field(default_factory=list)

    @property
    def owner_tokens(self) -> Tuple[str, ...]:
        for modifier in self.modifiers:
            if modifier.path_related and modifier.value > 1:
                return modifier.tokens
        return ()


def parse_focus_file(text: str, tag: str) -> List[Focus]:
    return [
        _build_focus(focus_id, kind, line, body, tag)
        for focus_id, kind, line, body in iter_focus_blocks(text)
    ]


def _build_focus(focus_id: str, kind: str, line: int, body: str, tag: str) -> Focus:
    focus = Focus(id=focus_id, line=line, kind=kind)
    for key, scalar, block in iter_statements(body):
        if key == "prerequisite" and block is not None:
            group = [
                value
                for name, value, _ in iter_statements(block)
                if name == "focus" and value is not None
            ]
            if group:
                focus.prereq_groups.append(group)
        elif key == "mutually_exclusive" and block is not None:
            focus.mutex.extend(
                value
                for name, value, _ in iter_statements(block)
                if name == "focus" and value is not None
            )
        elif key in ("available", "allow_branch") and block is not None:
            _read_gates(block, focus)
        elif key == "ai_will_do" and block is not None:
            focus.has_ai_will_do = True
            _read_ai_will_do(block, focus, tag)
        elif key.startswith("completion_reward") and block is not None:
            focus.dangers.extend(_scan_dangers(block))
            focus.cures.extend(_scan_cures(block))
        elif key == "select_effect" and block is not None:
            focus.dangers.extend(_scan_dangers(block))
    return focus


def _read_gates(block: str, focus: Focus) -> None:
    """Collect only unconditional gates.

    A `has_completed_focus` nested in an OR is an alternative and in a NOT an
    exclusion; treating either as a hard requirement invents stranded focuses.
    """
    for key, scalar, _nested in iter_statements(block):
        if key == "has_completed_focus" and scalar:
            focus.gates.append(scalar)
        elif key == "always" and scalar == "no":
            focus.always_off = True
    focus.party_gates.extend(_collect_party_gates(block))


def _collect_party_gates(block: str) -> List[str]:
    """Ruling-party requirements this focus places on *itself*.

    Descends through `OR`/`AND` but not into a `TAG = { }` or state scope, whose
    party gate is somebody else's government, nor into a `NOT`, which excludes a
    party rather than requiring one.
    """
    found: List[str] = []
    for key, scalar, nested in iter_statements(block):
        if nested is not None:
            if key in ("OR", "AND", "hidden_trigger", "custom_trigger_tooltip"):
                found.extend(_collect_party_gates(nested))
        elif scalar == "yes" and _PARTY_GATE.fullmatch(key):
            found.append(key)
    return found


def _read_ai_will_do(block: str, focus: Focus, tag: str) -> None:
    for key, scalar, nested in iter_statements(block):
        if key in ("base", "factor") and nested is None and scalar:
            focus.base = _number(scalar, focus.base)
        elif key == "modifier" and nested is not None:
            focus.modifiers.append(_read_modifier(nested, tag))


def _read_modifier(block: str, tag: str) -> Modifier:
    op, value = "factor", 1.0
    trigger_parts: List[Expr] = []
    for key, scalar, nested in iter_statements(block):
        if key in ("factor", "add") and nested is None and scalar:
            op, value = key, _number(scalar, 1.0)
        else:
            trigger_parts.append(_parse_statement(key, scalar, nested, tag))
    expr: Expr = ("and", trigger_parts)
    guard = any(token in block for token in GUARD_TOKENS)
    return Modifier(
        op=op,
        value=value,
        expr=expr,
        tokens=tuple(sorted(set(expr_tokens(expr)))),
        guard=guard,
        line=0,
    )


def _scan_dangers(block: str) -> List[str]:
    found = []
    for effect in DANGER_EFFECTS:
        if re.search(r"\b" + effect + r"\s*=", block):
            found.append(effect)
    return found


def _scan_cures(block: str) -> List[str]:
    """Names this effect block relieves: ideas, dynamic modifiers, variables."""
    found: List[str] = []
    for match in _REMOVE_IDEA.finditer(block):
        raw = match.group(1)
        if raw.startswith("{"):
            found.extend(_idea_tokens(raw))
        else:
            found.append(raw)
    found.extend(match.group(1) for match in _REMOVE_DYNAMIC.finditer(block))
    found.extend(match.group(1) for match in _ADD_TO_VARIABLE.finditer(block))
    return found


def _idea_tokens(block: str) -> List[str]:
    return [name for name in _IDENTIFIER.findall(block) if name not in _IDEA_KEYWORDS]


def _number(raw: str, fallback: float) -> float:
    try:
        return float(raw)
    except ValueError:
        return fallback


# --------------------------------------------------------------------------
# Rule, wiring, localisation
# --------------------------------------------------------------------------


@dataclass
class RuleOption:
    name: str
    text_key: str
    desc_key: str
    is_default: bool


@dataclass
class Rule:
    name: str
    header_key: str
    options: List[RuleOption] = field(default_factory=list)


def parse_rule(root: str, tag: str) -> Optional[Rule]:
    path = os.path.join(root, "common", "game_rules", "00_game_rules.txt")
    if not os.path.isfile(path):
        return None
    text = read_script(path, keep_quotes=True)
    opener = re.compile(r"^" + tag + r"_ai_behavior\s*=\s*\{", re.M)
    match = opener.search(text)
    if not match:
        return None
    close = find_matching_brace(text, text.index("{", match.start()))
    if close == -1:
        return None
    body = text[text.index("{", match.start()) + 1 : close]
    rule = Rule(name=tag + "_ai_behavior", header_key="")
    for key, scalar, block in iter_statements(body):
        if key == "name" and scalar:
            rule.header_key = scalar
        elif key in ("default", "option") and block is not None:
            fields = {
                inner: value
                for inner, value, _ in iter_statements(block)
                if value is not None
            }
            rule.options.append(
                RuleOption(
                    name=fields.get("name", "?"),
                    text_key=fields.get("text", ""),
                    desc_key=fields.get("desc", ""),
                    is_default=key == "default",
                )
            )
    return rule


def parse_wiring(root: str, tag: str) -> Tuple[Dict[str, List[str]], Dict[str, float]]:
    """Return (option -> flags it sets, random_list bucket -> weight)."""
    path = os.path.join(root, "common", "on_actions", "999_game_rules_on_actions.txt")
    per_option: Dict[str, List[str]] = {}
    buckets: Dict[str, float] = {}
    if not os.path.isfile(path):
        return per_option, buckets
    text = read_script(path)
    rule_ref = re.compile(
        r"has_game_rule\s*=\s*\{\s*rule\s*=\s*"
        + tag
        + r"_ai_behavior\s+option\s*=\s*(\w+)"
    )
    for match in rule_ref.finditer(text):
        option = match.group(1)
        limit_open = text.rfind("limit", 0, match.start())
        block_start = text.find(
            "{", text.rfind("if", 0, limit_open) if limit_open > 0 else 0
        )
        close = find_matching_brace(text, block_start) if block_start != -1 else -1
        scope = (
            text[match.end() : close]
            if close != -1
            else text[match.end() : match.end() + 2000]
        )
        flags = re.findall(
            r"set_global_flag\s*=\s*(" + tag + r"_\w+_FOCUS_PATH)", scope
        )
        per_option.setdefault(option, []).extend(flags)
        if option == "RANDOM_PATH":
            for weight, flag in re.findall(
                r"([0-9.]+)\s*=\s*\{\s*set_global_flag\s*=\s*("
                + tag
                + r"_\w+_FOCUS_PATH)",
                scope,
            ):
                buckets[flag] = _number(weight, 0.0)
    return per_option, buckets


def load_localisation(root: str) -> Dict[str, str]:
    entries: Dict[str, str] = {}
    for folder in ("english", os.path.join("english", "replace")):
        path = os.path.join(root, "localisation", folder)
        if not os.path.isdir(path):
            continue
        for name in sorted(os.listdir(path)):
            if not name.endswith("_l_english.yml"):
                continue
            full = os.path.join(path, name)
            if not os.path.isfile(full):
                continue
            with open(full, "r", encoding="utf-8-sig", errors="replace") as handle:
                for line in handle:
                    match = _LOC_KEY.match(line)
                    if match:
                        entries[match.group(1)] = match.group(2)
    return entries


def count_sentences(text: str) -> int:
    """Sentence count for a rule description.

    Party highlights and `[Scope.GetName]` substitutions can carry a period of
    their own, so both are removed before counting terminators.
    """
    stripped = _LOC_SCOPE.sub("", _HIGHLIGHT.sub("X", text))
    return len(re.findall(r"[.!?](?=\s|$)", stripped))


# --------------------------------------------------------------------------
# Strategy plans
# --------------------------------------------------------------------------


def parse_plans(root: str, tag: str) -> List[Tuple[str, Dict[str, float], bool]]:
    """Return (plan name, focus_factors, reads_game_rule) per strategy plan."""
    path = os.path.join(
        root, "common", "ai_strategy_plans", tag + "_strategy_plans.txt"
    )
    if not os.path.isfile(path):
        return []
    text = read_script(path)
    plans = []
    opener = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\{", re.M)
    for match in opener.finditer(text):
        close = find_matching_brace(text, match.end() - 1)
        if close == -1:
            continue
        body = text[match.end() : close]
        factors: Dict[str, float] = {}
        for key, scalar, block in iter_statements(body):
            if key == "focus_factors" and block is not None:
                for focus_id, value, _ in iter_statements(block):
                    if value is not None:
                        factors[focus_id] = _number(value, 1.0)
        plans.append((match.group(1), factors, "has_game_rule" in body))
    return plans


# --------------------------------------------------------------------------
# Analysis
# --------------------------------------------------------------------------


@dataclass
class State:
    option: str
    flag: Optional[str]
    historical: bool

    @property
    def label(self) -> str:
        return "{:<22} {}".format(self.option, "on " if self.historical else "off")


def build_states(rule: Optional[Rule], flags: Sequence[str]) -> List[State]:
    options: List[Tuple[str, Optional[str]]] = []
    if rule:
        for option in rule.options:
            if option.name == "RANDOM_PATH":
                continue
            match = next(
                (flag for flag in flags if flag.endswith(option.name + "_FOCUS_PATH")),
                None,
            )
            options.append((option.name, match))
    else:
        options.extend((flag, flag) for flag in flags)
        options.append(("NO_PATH", None))
    return [
        State(option=name, flag=flag, historical=historical)
        for name, flag in options
        for historical in (True, False)
    ]


def focus_weight(
    focus: Focus, state: State, triggers: Dict[str, Expr]
) -> Tuple[float, int]:
    """Effective ai_will_do weight in one state, plus unevaluable modifier count."""
    weight = focus.base
    unknown = 0
    for modifier in focus.modifiers:
        if modifier.guard:
            continue
        verdict = evaluate(modifier.expr, state.flag, state.historical, triggers)
        if verdict is UNKNOWN:
            unknown += 1
            continue
        if verdict is FALSE:
            continue
        if modifier.op == "factor":
            weight *= modifier.value
        else:
            weight += modifier.value
    return weight, unknown


def unreachable_focuses(alive: Dict[str, bool], focuses: Dict[str, Focus]) -> set:
    """Focuses whose prerequisite chain is fully dead, to a fixed point."""
    reachable = {
        focus_id
        for focus_id, is_alive in alive.items()
        if is_alive and not focuses[focus_id].prereq_groups
    }
    changed = True
    while changed:
        changed = False
        for focus_id, focus in focuses.items():
            if focus_id in reachable or not alive.get(focus_id):
                continue
            if all(
                any(member in reachable for member in group)
                for group in focus.prereq_groups
            ):
                reachable.add(focus_id)
                changed = True
    return {
        focus_id
        for focus_id, is_alive in alive.items()
        if is_alive and focus_id not in reachable
    }


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------


def resolve_focus_file(root: str, tag: str) -> str:
    folder = os.path.join(root, "common", "national_focus")
    country_ref = re.compile(r"(original_tag|tag)\s*=\s*" + tag + r"\b")
    matches = []
    for path in iter_txt_files(folder):
        text = read_script(path)
        head = text[: text.find("focus", 200) if "focus" in text else 4000]
        if country_ref.search(head[:4000]):
            matches.append(path)
    if len(matches) == 1:
        return matches[0]
    id_ref = re.compile(r"^[ \t]*id\s*=\s*" + tag + r"_", re.M)
    counted = []
    for path in iter_txt_files(folder):
        count = len(id_ref.findall(read_raw(path)))
        if count:
            counted.append((count, path))
    if not counted:
        raise SystemExit("no focus file found for tag " + tag)
    counted.sort(reverse=True)
    return counted[0][1]


def build_report(root: str, tag: str, limit: int) -> Dict:
    focus_path = resolve_focus_file(root, tag)
    text = read_script(focus_path)
    focuses = parse_focus_file(text, tag)
    by_id = {focus.id: focus for focus in focuses}
    triggers = load_path_triggers(root, tag)
    rule = parse_rule(root, tag)
    wiring, buckets = parse_wiring(root, tag)
    loc = load_localisation(root)
    plans = parse_plans(root, tag)

    flags = sorted({flag for values in wiring.values() for flag in values})
    if not flags:
        flags = sorted(
            {
                token
                for focus in focuses
                for modifier in focus.modifiers
                for token in modifier.tokens
                if is_path_flag(token, tag)
            }
        )

    states = build_states(rule, flags)
    weights = {
        focus.id: [focus_weight(focus, state, triggers)[0] for state in states]
        for focus in focuses
    }
    return {
        "tag": tag,
        "focus_file": os.path.relpath(focus_path, root).replace("\\", "/"),
        "focus_count": len(focuses),
        "path_flags": flags,
        "triggers": sorted(triggers),
        "rule": _rule_findings(rule, loc, wiring, buckets, flags, tag),
        "owners": _owner_findings(focuses, tag, flags, triggers),
        "matrix": _matrix(focuses, by_id, states, triggers, limit),
        "graph": _graph_findings(focuses, by_id, weights, states, triggers, limit),
        "plans": _plan_findings(plans, by_id, limit),
        "rewards": _reward_findings(focuses, limit),
        "mechanics": _mechanics_findings(
            root, tag, focuses, by_id, states, triggers, limit
        ),
        "government": _government_findings(root, tag),
    }


def _rule_findings(
    rule: Optional[Rule],
    loc: Dict[str, str],
    wiring: Dict[str, List[str]],
    buckets: Dict[str, float],
    flags: Sequence[str],
    tag: str,
) -> Dict:
    issues: List[str] = []
    options: List[str] = []
    if not rule:
        return {
            "issues": ["no " + tag + "_ai_behavior rule in 00_game_rules.txt"],
            "options": [],
        }
    options = [option.name for option in rule.options]
    defaults = [option.name for option in rule.options if option.is_default]
    if defaults != ["NO_PATH"]:
        issues.append(
            "default block is {}, expected NO_PATH".format(defaults or "missing")
        )
    if "DEFAULT" in options:
        issues.append("DEFAULT option still present")
    for required in ("HISTORICAL", "RANDOM_PATH", "NO_PATH"):
        if required not in options:
            issues.append("missing " + required + " option")
    if rule.header_key and rule.header_key not in loc:
        issues.append("header key " + rule.header_key + " has no localisation")
    elif rule.header_key:
        header = loc[rule.header_key]
        if not header.startswith("@" + tag + " "):
            issues.append(
                "header key should read '@{} <short name>', found '{}'".format(
                    tag, header
                )
            )
    for option in rule.options:
        if (
            option.name == "RANDOM_PATH"
            and option.text_key != "RULE_OPTION_MD_RANDOM_PATH"
        ):
            issues.append("RANDOM_PATH must reuse RULE_OPTION_MD_RANDOM_PATH")
        if option.name == "NO_PATH" and option.text_key != "RULE_OPTION_MD_NO_PATH":
            issues.append("NO_PATH must reuse RULE_OPTION_MD_NO_PATH")
        if option.text_key and option.text_key not in loc:
            issues.append("missing loc key " + option.text_key)
        if option.name == "HISTORICAL" and loc.get(option.text_key) not in (
            None,
            "Historical",
        ):
            issues.append(
                "historical option text is '{}', must be 'Historical'".format(
                    loc[option.text_key]
                )
            )
        if "RANDOM" in option.name and option.name != "RANDOM_PATH":
            issues.append("option name " + option.name + " contains 'random'")
        if option.name.startswith(tag + "_"):
            issues.append("option name " + option.name + " is tag-prefixed")
        desc = loc.get(option.desc_key)
        if option.desc_key and desc is None:
            issues.append("missing loc key " + option.desc_key)
        elif desc and not option.desc_key.startswith("RULE_OPTION_MD_"):
            sentences = count_sentences(desc)
            if sentences != 2:
                issues.append(
                    "{} has {} sentences, must be 2".format(option.desc_key, sentences)
                )
            if _YEAR.search(desc):
                issues.append(option.desc_key + " contains a hard date")

    wired = {option: values for option, values in wiring.items() if values}
    for option in options:
        if option in ("RANDOM_PATH", "NO_PATH"):
            continue
        if option not in wired:
            issues.append(
                "option " + option + " sets no global flag in 999_game_rules_on_actions"
            )
    if wiring.get("NO_PATH"):
        issues.append("NO_PATH sets a flag; it must set none")
    if "RANDOM_PATH" in options:
        if not buckets:
            issues.append("RANDOM_PATH has no random_list buckets")
        else:
            missing = [flag for flag in flags if flag not in buckets]
            if missing:
                issues.append("RANDOM_PATH omits " + ", ".join(missing))
            empty = [flag for flag, weight in buckets.items() if weight <= 0]
            if empty:
                issues.append("RANDOM_PATH has empty buckets: " + ", ".join(empty))
    return {"issues": issues, "options": options, "buckets": buckets}


def _owner_findings(
    focuses: Sequence[Focus],
    tag: str,
    flags: Sequence[str],
    triggers: Dict[str, Expr],
) -> Dict:
    owned = [focus for focus in focuses if any(m.path_related for m in focus.modifiers)]
    additive = [
        focus.id
        for focus in focuses
        for modifier in focus.modifiers
        if modifier.path_related and modifier.op == "add"
    ]
    referenced = set()
    for focus in focuses:
        for modifier in focus.modifiers:
            for token in modifier.tokens:
                referenced.add(token)
                referenced.update(_expand_trigger(token, triggers))
    groups: Dict[str, int] = {}
    parties: Dict[str, set] = {}
    for focus in owned:
        key = " + ".join(focus.owner_tokens) or "(kill only)"
        groups[key] = groups.get(key, 0) + 1
        parties.setdefault(key, set()).update(focus.party_gates)
    unused = [flag for flag in flags if flag not in referenced]
    return {
        "owned": len(owned),
        "unowned": len(focuses) - len(owned),
        "groups": groups,
        "group_parties": {key: sorted(value) for key, value in parties.items()},
        "additive": sorted(set(additive)),
        "unused_flags": unused,
        "multi_root": _multi_root_owners(owned),
    }


def _multi_root_owners(owned: Sequence[Focus]) -> Dict[str, List[str]]:
    """Owner tokens boosting more than one branch root.

    One rule option is supposed to buy one government. A token owning several
    roots means the option covers rival spines the AI still picks between at
    random, whatever weight the tree carries. Legitimate when a single spine
    converges from two roots, so this is a read, not a verdict.
    """
    roots: Dict[str, List[str]] = {}
    for focus in owned:
        if focus.prereq_groups:
            continue
        for token in focus.owner_tokens:
            roots.setdefault(token, []).append(focus.id)
    return {token: ids for token, ids in sorted(roots.items()) if len(ids) > 1}


def _matrix(
    focuses: Sequence[Focus],
    by_id: Dict[str, Focus],
    states: Sequence[State],
    triggers: Dict[str, Expr],
    limit: int,
) -> List[Dict]:
    rows = []
    for state in states:
        alive: Dict[str, bool] = {}
        unknowns = 0
        for focus in focuses:
            weight, unknown = focus_weight(focus, state, triggers)
            alive[focus.id] = weight > 0
            unknowns += unknown
        orphans = sorted(unreachable_focuses(alive, by_id))
        stranded = sorted(
            focus.id
            for focus in focuses
            if alive.get(focus.id)
            and focus.id not in orphans
            and any(gate in by_id and not alive.get(gate, True) for gate in focus.gates)
        )
        rows.append(
            {
                "option": state.option,
                "historical": state.historical,
                "live": sum(1 for value in alive.values() if value),
                "zeroed": sum(1 for value in alive.values() if not value),
                "orphans": orphans[:limit] if limit else orphans,
                "orphan_count": len(orphans),
                "stranded": stranded[:limit] if limit else stranded,
                "stranded_count": len(stranded),
                "unevaluable": unknowns,
            }
        )
    return rows


def _owner_live(focus: Focus, state: State, triggers: Dict[str, Expr]) -> bool:
    """True when a boosting path modifier of *focus* fires in *state*."""
    return any(
        evaluate(modifier.expr, state.flag, state.historical, triggers) is TRUE
        for modifier in focus.modifiers
        if modifier.path_related and modifier.value > 1
    )


def _graph_findings(
    focuses: Sequence[Focus],
    by_id: Dict[str, Focus],
    weights: Dict[str, List[float]],
    states: Sequence[State],
    triggers: Dict[str, Expr],
    limit: int,
) -> Dict:
    routing_ties: List[str] = []
    neutral_ties = 0
    for focus in focuses:
        if focus.always_off:
            continue
        for other_id in focus.mutex:
            other = by_id.get(other_id)
            if not other or other.always_off or other.id < focus.id:
                continue
            if weights.get(focus.id) != weights.get(other_id):
                continue
            if focus.owner_tokens or other.owner_tokens:
                routing_ties.append(focus.id + " / " + other.id)
            else:
                neutral_ties += 1

    # Two sides of one either/or boosted by *different* paths in the same state:
    # each path thinks it owns the choice, and the larger number decides. A pair
    # inside one path's own spine is a flavour choice and stays out of this.
    both_owned: List[str] = []
    for state in states:
        for focus in focuses:
            if focus.always_off or not _owner_live(focus, state, triggers):
                continue
            for other_id in focus.mutex:
                other = by_id.get(other_id)
                if not other or other.always_off or other.id < focus.id:
                    continue
                if set(focus.owner_tokens) == set(other.owner_tokens):
                    continue
                if _owner_live(other, state, triggers):
                    both_owned.append(
                        "{} / {} boosted by rival paths under {} / historical {}".format(
                            focus.id,
                            other.id,
                            state.option,
                            "on" if state.historical else "off",
                        )
                    )

    # An explicit alternate rule must decide the tree on its own. A focus that
    # only survives because global history is on is reading past that rule.
    overrides: List[str] = []
    index = {(state.option, state.historical): pos for pos, state in enumerate(states)}
    for state in states:
        if not state.historical or state.flag is None or state.option == "HISTORICAL":
            continue
        off = index.get((state.option, False))
        if off is None:
            continue
        on = index[(state.option, True)]
        for focus in focuses:
            if focus.always_off:
                continue
            row = weights.get(focus.id)
            if not row or row[off] != 0 or row[on] <= 0:
                continue
            overrides.append(
                "{} under {}: 0 with historical off, {:g} with it on".format(
                    focus.id, state.option, row[on]
                )
            )

    missing = [focus.id for focus in focuses if not focus.has_ai_will_do]
    return {
        "roots": sum(1 for focus in focuses if not focus.prereq_groups),
        "mutex_ties": routing_ties[:limit] if limit else routing_ties,
        "mutex_tie_count": len(routing_ties),
        "neutral_ties": neutral_ties,
        "mutex_both_owned": both_owned[:limit] if limit else both_owned,
        "mutex_both_owned_count": len(both_owned),
        "historical_overrides": overrides[:limit] if limit else overrides,
        "historical_override_count": len(overrides),
        "no_ai_will_do": len(missing),
    }


def _plan_findings(
    plans: Sequence[Tuple[str, Dict[str, float], bool]],
    by_id: Dict[str, Focus],
    limit: int,
) -> Dict:
    empty = [name for name, factors, _ in plans if not factors]
    rule_readers = [name for name, _, reads_rule in plans if reads_rule]
    conflicts = [
        name + ": " + focus_id + " (no such focus)"
        for name, factors, _ in plans
        for focus_id in factors
        if focus_id not in by_id
    ]
    with_factors = [factors for _, factors, _ in plans if factors]
    orphaned = sorted(
        {
            focus_id
            for factors in with_factors
            for focus_id in factors
            if focus_id in by_id
            and all(other.get(focus_id, 1.0) == 0 for other in with_factors)
        }
    )
    return {
        "plans": len(plans),
        "no_focus_factors": empty,
        "reads_game_rule": rule_readers,
        "zeroed_by_every_plan": orphaned[:limit] if limit else orphaned,
        "zeroed_by_every_plan_count": len(orphaned),
        "conflicts": conflicts[:limit] if limit else conflicts,
        "conflict_count": len(conflicts),
    }


def _reward_findings(focuses: Sequence[Focus], limit: int) -> List[str]:
    rows = [
        focus.id + ": " + ", ".join(sorted(set(focus.dangers)))
        for focus in focuses
        if focus.dangers
    ]
    return rows[:limit] if limit else rows


# --------------------------------------------------------------------------
# Country mechanics
# --------------------------------------------------------------------------


@dataclass
class Burden:
    name: str
    kind: str


@dataclass
class Decision:
    id: str
    category: str
    base: float
    ai_blocked: bool
    cures: Tuple[str, ...] = ()
    visible: str = ""


def country_scope(text: str) -> str:
    """Blank every numeric state block, leaving country-scope statements.

    Length and newlines are preserved, so offsets stay valid. Dated blocks keep
    their contents — they are country scope too.
    """
    out = text
    for match in _STATE_BLOCK.finditer(text):
        close = find_matching_brace(text, match.end() - 1)
        if close == -1:
            continue
        out = (
            out[: match.start()] + " " * (close + 1 - match.start()) + out[close + 1 :]
        )
    return out


def parse_burdens(root: str, tag: str) -> List[Burden]:
    """Ideas, dynamic modifiers and negative variables the country starts with."""
    burdens: List[Burden] = []
    seen = set()

    def record(name: str, kind: str) -> None:
        if name and name not in seen:
            seen.add(name)
            burdens.append(Burden(name=name, kind=kind))

    for path in iter_txt_files(os.path.join(root, "history", "countries")):
        if not os.path.basename(path).startswith(tag + " "):
            continue
        for key, scalar, block in iter_statements(country_scope(read_script(path))):
            if key in ("add_ideas", "add_timed_idea"):
                names = _idea_tokens(block) if block is not None else [scalar]
                for name in names:
                    if name and _is_country_idea(name, tag):
                        record(name, "idea")
            elif key == "add_dynamic_modifier" and block is not None:
                match = _MODIFIER_NAME.search(block)
                if match:
                    record(match.group(1), "dynamic modifier")
            elif key == "set_variable" and block is not None:
                name, value = _variable_seed(block)
                if value is not None and value < 0:
                    record(name, "negative variable")
        break
    return burdens


def _is_country_idea(name: str, tag: str) -> bool:
    return name.startswith(tag + "_") or name.endswith("_" + tag)


def _variable_seed(block: str) -> Tuple[str, Optional[float]]:
    name, raw = "", None
    for key, scalar, nested in iter_statements(block):
        if nested is not None or scalar is None:
            continue
        if key == "var":
            name = scalar
        elif key == "value":
            raw = scalar
        elif not name:
            name, raw = key, scalar
    if raw is None:
        return name, None
    try:
        return name, float(raw)
    except ValueError:
        return name, None


def parse_decision_categories(root: str, tag: str) -> Dict[str, Dict[str, str]]:
    """Category id -> {gui, gates} for every decision category owned by *tag*.

    `gates` is the category's own visibility text: a category gated on an idea
    or modifier is that burden's mechanic, whatever its individual decisions do.
    """
    categories: Dict[str, Dict[str, str]] = {}
    owner = re.compile(r"(original_tag|tag)\s*=\s*" + tag + r"\b")
    folder = os.path.join(root, "common", "decisions", "categories")
    for path in iter_txt_files(folder):
        raw = read_raw(path)
        if tag not in raw:
            continue
        text = blank_quoted_strings(strip_comments(raw))
        for match in _TOP_BLOCK.finditer(text):
            close = find_matching_brace(text, match.end() - 1)
            if close == -1:
                continue
            body = text[match.end() : close]
            allowed, gui, visible, gates = "", "", "", []
            for key, scalar, block in iter_statements(body):
                if key == "allowed" and block is not None:
                    allowed = block
                elif key == "scripted_gui" and scalar:
                    gui = scalar
                elif key in ("visible", "available") and block is not None:
                    gates.append(block)
                    if key == "visible":
                        visible = block
            if owner.search(allowed):
                categories[match.group(1)] = {
                    "gui": gui,
                    "gates": " ".join(gates),
                    "visible": visible,
                }
    return categories


def parse_decisions(root: str, tag: str, categories: Sequence[str]) -> List[Decision]:
    decisions: List[Decision] = []
    wanted = set(categories)
    if not wanted:
        return decisions
    for path in iter_txt_files(os.path.join(root, "common", "decisions")):
        raw = read_raw(path)
        if not any(name in raw for name in wanted):
            continue
        text = blank_quoted_strings(strip_comments(raw))
        for match in _TOP_BLOCK.finditer(text):
            if match.group(1) not in wanted:
                continue
            close = find_matching_brace(text, match.end() - 1)
            if close == -1:
                continue
            for key, _, block in iter_statements(text[match.end() : close]):
                if block is not None:
                    decisions.append(_build_decision(key, match.group(1), block))
    return decisions


def _build_decision(decision_id: str, category: str, block: str) -> Decision:
    base = 1.0
    blocked = False
    visible = ""
    for key, _, nested in iter_statements(block):
        if nested is None:
            continue
        if key == "ai_will_do":
            base = _ai_will_do_base(nested)
        elif key in ("available", "visible", "allowed"):
            blocked = blocked or _AI_BLOCKED.search(nested) is not None
            if key == "visible":
                visible = nested
    return Decision(
        id=decision_id,
        category=category,
        base=base,
        ai_blocked=blocked,
        cures=tuple(_scan_cures(block)),
        visible=visible,
    )


def _ai_will_do_base(block: str) -> float:
    base = 1.0
    for key, scalar, nested in iter_statements(block):
        if key in ("base", "factor") and nested is None and scalar:
            base = _number(scalar, base)
    return base


def parse_guis(root: str, tag: str) -> List[Tuple[str, str, str]]:
    """(gui id, context_type, body) for every scripted GUI owned by *tag*."""
    results: List[Tuple[str, str, str]] = []
    folder = os.path.join(root, "common", "scripted_guis")
    for path in iter_txt_files(folder):
        named = tag in os.path.basename(path)
        raw = read_raw(path)
        if not named and tag + "_" not in raw:
            continue
        text = blank_quoted_strings(strip_comments(raw))
        for key, _, block in iter_statements(text):
            if key != "scripted_gui" or block is None:
                continue
            for gui_id, _, body in iter_statements(block):
                if body is None or not (named or gui_id.startswith(tag + "_")):
                    continue
                context = next(
                    (
                        scalar
                        for inner, scalar, _ in iter_statements(body)
                        if inner == "context_type" and scalar
                    ),
                    "",
                )
                results.append((gui_id, context, body))
    return results


def live_focuses(
    focuses: Sequence[Focus],
    by_id: Dict[str, Focus],
    state: State,
    triggers: Dict[str, Expr],
) -> set:
    """Focus ids the AI can both weigh above zero and actually reach."""
    alive = {focus.id: focus_weight(focus, state, triggers)[0] > 0 for focus in focuses}
    orphans = unreachable_focuses(alive, by_id)
    return {
        focus_id
        for focus_id, is_alive in alive.items()
        if is_alive and focus_id not in orphans
    }


def _has_priority_boost(focus: Focus) -> bool:
    if focus.base > 1:
        return True
    return any(
        not modifier.path_related
        and (
            (modifier.op == "factor" and modifier.value > 1)
            or (modifier.op == "add" and modifier.value > 0)
        )
        for modifier in focus.modifiers
    )


def _path_gate_issues(
    tag: str,
    categories: Dict[str, Dict[str, str]],
    decisions: Sequence[Decision],
    states: Sequence[State],
    triggers: Dict[str, Expr],
) -> List[str]:
    """Path gates outside the focus tree, where no killswitch modifier follows.

    Inside `ai_will_do` the mandated `factor = 0` pair settles the historical /
    explicit-rule overlap. A `visible` block has no second chance, so it has to
    read the historical *trigger*, guarded against the alt flags.
    """
    historical_flag = tag + "_HISTORICAL_FOCUS_PATH"
    issues: List[str] = []
    gates = [(name, entry["visible"]) for name, entry in sorted(categories.items())]
    gates.extend((decision.id, decision.visible) for decision in decisions)
    for name, block in gates:
        if not block:
            continue
        tokens = set(_IDENTIFIER.findall(block))
        if not any(
            is_path_flag(token, tag) or is_path_trigger(token, tag) for token in tokens
        ):
            continue
        if historical_flag in tokens:
            issues.append(
                "{}: gates on {}; NO_PATH with historical AI sets no flag, "
                "read {}_ai_historical_path instead".format(name, historical_flag, tag)
            )
            continue
        expr = parse_expr(block, tag)
        for state in states:
            if not state.historical or state.flag in (None, historical_flag):
                continue
            if evaluate(expr, state.flag, True, triggers) is not TRUE:
                continue
            if evaluate(expr, state.flag, False, triggers) is FALSE:
                issues.append(
                    "{}: visible under {} only because historical AI is on; "
                    "guard the historical arm against the alt flags".format(
                        name, state.option
                    )
                )
                break
    return issues


def _mechanics_findings(
    root: str,
    tag: str,
    focuses: Sequence[Focus],
    by_id: Dict[str, Focus],
    states: Sequence[State],
    triggers: Dict[str, Expr],
    limit: int,
) -> Dict:
    burdens = parse_burdens(root, tag)
    categories = parse_decision_categories(root, tag)
    decisions = parse_decisions(root, tag, sorted(categories))
    guis = parse_guis(root, tag)
    backed = {entry["gui"] for entry in categories.values() if entry["gui"]}
    names = {burden.name for burden in burdens}

    focus_cures: Dict[str, List[str]] = {}
    for focus in focuses:
        for cure in focus.cures:
            if cure in names:
                focus_cures.setdefault(cure, []).append(focus.id)
    decision_cures: Dict[str, List[Decision]] = {}
    for decision in decisions:
        for cure in decision.cures:
            if cure in names:
                decision_cures.setdefault(cure, []).append(decision)
    category_cover: Dict[str, List[str]] = {}
    for category, entry in categories.items():
        for name in names:
            if name in entry["gates"]:
                category_cover.setdefault(name, []).append(category)

    issues: List[str] = _path_gate_issues(tag, categories, decisions, states, triggers)
    rows: List[Dict] = []
    unrelieved: List[str] = []
    reachable = {
        state.option
        + str(state.historical): live_focuses(focuses, by_id, state, triggers)
        for state in states
    }
    for burden in burdens:
        cures = focus_cures.get(burden.name, [])
        cure_decisions = decision_cures.get(burden.name, [])
        cover = sorted(category_cover.get(burden.name, []))
        rows.append(
            {
                "name": burden.name,
                "kind": burden.kind,
                "focus_cures": cures,
                "decision_cures": [decision.id for decision in cure_decisions],
                "categories": cover,
            }
        )
        if not cures and not cure_decisions:
            if not cover:
                unrelieved.append(burden.name)
            continue
        if cure_decisions:
            continue
        for state in states:
            live = reachable[state.option + str(state.historical)]
            if not any(focus_id in live for focus_id in cures):
                issues.append(
                    "{}: every cure is dead under {} / historical {}".format(
                        burden.name,
                        state.option,
                        "on" if state.historical else "off",
                    )
                )

    for focus in focuses:
        cured = sorted({cure for cure in focus.cures if cure in names})
        if cured and not _has_priority_boost(focus):
            issues.append("{} cures {} at flat base".format(focus.id, ", ".join(cured)))
    for cure, cure_decisions in sorted(decision_cures.items()):
        for decision in cure_decisions:
            if decision.base <= 0 or decision.ai_blocked:
                issues.append(
                    "{} cures {} but the AI can never take it".format(decision.id, cure)
                )

    gui_rows = []
    for gui_id, context, body in guis:
        touched = sorted(name for name in names if name in body)
        backing = (
            "decision-backed"
            if gui_id in backed or context == "decision_category"
            else "player-only"
        )
        gui_rows.append(
            {
                "id": gui_id,
                "context": context or "-",
                "backing": backing,
                "touches": touched,
            }
        )
        if backing == "player-only" and touched:
            uncovered = [
                name
                for name in touched
                if name not in category_cover
                and not any(name in decision.cures for decision in decisions)
            ]
            if uncovered:
                issues.append(
                    "{} is player-only and no decision relieves {}".format(
                        gui_id, ", ".join(uncovered)
                    )
                )

    return {
        "burdens": rows[:limit] if limit else rows,
        "burden_count": len(rows),
        "decisions": len(decisions),
        "categories": sorted(categories),
        "guis": gui_rows[:limit] if limit else gui_rows,
        "gui_count": len(gui_rows),
        "unrelieved": unrelieved[:limit] if limit else unrelieved,
        "unrelieved_count": len(unrelieved),
        "issues": issues[:limit] if limit else issues,
        "issue_count": len(issues),
    }


# --------------------------------------------------------------------------
# Historical government walker
# --------------------------------------------------------------------------


@dataclass
class Leader:
    name: str
    index: int
    until: Optional[Tuple[int, int, int]] = None


@dataclass
class Branch:
    kind: str
    after: Optional[Tuple[int, int, int]] = None
    party: Optional[int] = None
    pointer: Optional[Tuple[str, int]] = None
    changes_party: bool = False
    advances: bool = False


@dataclass
class Walker:
    event_id: str = ""
    path: str = ""
    line: int = 0
    chain: List[Branch] = field(default_factory=list)
    pins_leader: bool = False


_DATE = re.compile(r"(\d{4})\.(\d{1,2})\.(\d{1,2})")
_ROSTER_DATE = re.compile(r"date\s*<\s*(\d{4}\.\d{1,2}\.\d{1,2})")
_WALKER_DATE = re.compile(r"date\s*>\s*(\d{4}\.\d{1,2}\.\d{1,2})")


def _parse_date(raw: str) -> Optional[Tuple[int, int, int]]:
    match = _DATE.search(raw)
    if not match:
        return None
    year, month, day = match.groups()
    return int(year), int(month), int(day)


def format_date(date: Optional[Tuple[int, int, int]]) -> str:
    return "{}.{}.{}".format(*date) if date else "-"


def day_offset_to_date(year: int, days: int) -> Tuple[int, int, int]:
    """Resolve a `days = N` offset inside `trigger_year_<year>_events`.

    The dispatcher runs at the January tick, and MD's own day counts ignore leap
    years, so a fixed month table reproduces the numbers already in the file.
    """
    month = 1
    remaining = days
    for length in DAYS_PER_MONTH:
        if remaining < length:
            break
        remaining -= length
        month += 1
    if month > 12:
        return year + 1, 1, 1
    return year, month, remaining + 1


def _block_of(body: str, key: str) -> Optional[str]:
    for name, _, block in iter_statements(body):
        if name == key and block is not None:
            return block
    return None


def parse_leader_roster(text: str, tag: str) -> Dict[str, List[Leader]]:
    """Map sub-ideology to its ordered succession list in `set_leader_<TAG>`."""
    match = re.search(r"^\s*set_leader_" + tag + r"\s*=\s*\{", text, re.M)
    if not match:
        return {}
    start = text.index("{", match.start())
    close = find_matching_brace(text, start)
    if close == -1:
        return {}
    branches: Dict[str, List[Leader]] = {}
    for key, _, block in iter_statements(text[start + 1 : close]):
        if key not in ("if", "else_if") or block is None:
            continue
        limit = _block_of(block, "limit") or ""
        name = None
        if re.search(r"western_autocrats_are_in_power\s*=\s*yes", limit):
            name = "Western_Autocracy"
        else:
            slot = re.search(r"ruling_party\s*=\s*(\d+)", limit)
            if slot:
                name = PARTY_SLOT_NAMES.get(int(slot.group(1)))
        if name:
            branches[name] = _parse_roster_branch(block, name)
    return branches


def _parse_roster_branch(block: str, subideology: str) -> List[Leader]:
    declared = re.compile(re.escape(subideology) + r"_leader\s*=\s*(\d+)")
    leaders: List[Leader] = []

    def walk(scope: str) -> None:
        for key, _, entry in iter_statements(scope):
            if key not in ("if", "else_if") or entry is None:
                continue
            create = _block_of(entry, "create_country_leader")
            if create is None:
                walk(entry)
                continue
            name = re.search(r'name\s*=\s*"([^"]*)"', create)
            index = declared.search(_block_of(entry, "limit") or "")
            until = _ROSTER_DATE.search(entry)
            leaders.append(
                Leader(
                    name=name.group(1) if name else "?",
                    index=int(index.group(1)) if index else len(leaders),
                    until=_parse_date(until.group(1)) if until else None,
                )
            )

    walk(block)
    return leaders


def parse_year_schedule(text: str, tag: str) -> List[Tuple[int, str, int]]:
    """Return (year, event id, day offset) for every event scheduled at *tag*."""
    entries: List[Tuple[int, str, int]] = []
    scope = re.compile(r"\b" + tag + r"\s*=\s*\{")
    fire = re.compile(
        r"country_event\s*=\s*\{[^{}]*?\bid\s*=\s*([A-Za-z0-9_.]+)"
        r"[^{}]*?\bdays\s*=\s*(\d+)"
    )
    blocks = [
        (int(match.group(1)), match)
        for match in re.finditer(r"^trigger_year_(\d{4})_events\s*=\s*\{", text, re.M)
    ]
    blocks += [
        (START_YEAR, match)
        for match in re.finditer(r"^MD_event_on_startup_events\s*=\s*\{", text, re.M)
    ]
    for year, match in blocks:
        start = text.index("{", match.start())
        close = find_matching_brace(text, start)
        if close == -1:
            continue
        body = text[start + 1 : close]
        for scoped in scope.finditer(body):
            inner = body.index("{", scoped.start())
            inner_close = find_matching_brace(body, inner)
            if inner_close == -1:
                continue
            for event in fire.finditer(body[inner + 1 : inner_close]):
                entries.append((year, event.group(1), int(event.group(2))))
    return entries


def parse_walker(immediate: str) -> Walker:
    """Read the date chain out of a historical government walker's `immediate`."""
    walker = Walker(
        pins_leader=bool(re.search(r"change_leader_temp\s*=\s*1", immediate))
    )
    chain_open = True
    for key, _, block in iter_statements(immediate):
        if key not in ("if", "else_if", "else") or block is None:
            continue
        bound = _WALKER_DATE.search(_block_of(block, "limit") or "")
        after = _parse_date(bound.group(1)) if bound else None
        changes_party = "change_ruling_party_effect" in block
        advances = "set_leader" in block
        if not chain_open or (after is None and not (key == "else" and walker.chain)):
            chain_open = False
            continue
        party = re.search(r"rul_party_temp\s*=\s*(\d+)", block)
        pointer = re.search(r"(\w+)_leader\s*=\s*(\d+)", block)
        walker.chain.append(
            Branch(
                kind=key,
                after=after,
                party=int(party.group(1)) if party else None,
                pointer=(
                    (pointer.group(1), int(pointer.group(2))) if pointer else None
                ),
                changes_party=changes_party,
                advances=advances,
            )
        )
        if key == "else":
            chain_open = False
    return walker


def resolve_branch(chain: Sequence[Branch], date: Tuple[int, int, int]):
    for branch in chain:
        if branch.after is None or date > branch.after:
            return branch
    return None


_EVENT_INDEX: Dict[str, Dict[str, str]] = {}


def event_index(root: str) -> Dict[str, str]:
    """Map every event id under events/ to the file that defines it."""
    cached = _EVENT_INDEX.get(root)
    if cached is not None:
        return cached
    index: Dict[str, str] = {}
    for path in iter_txt_files(os.path.join(root, "events")):
        for found in _ID_LINE.finditer(read_raw(path)):
            index.setdefault(found.group(1), path)
    _EVENT_INDEX[root] = index
    return index


def find_event(root: str, event_id: str) -> Tuple[str, int, str]:
    """Locate a `country_event` by id and return (path, line, body)."""
    path = event_index(root).get(event_id)
    if not path:
        return "", 0, ""
    text = read_script(path)
    for match in re.finditer(r"country_event\s*=\s*\{", text):
        start = match.end() - 1
        close = find_matching_brace(text, start)
        if close == -1:
            continue
        body = text[start + 1 : close]
        found = _ID_LINE.search(body)
        if found and found.group(1) == event_id:
            return (
                os.path.relpath(path, root).replace("\\", "/"),
                line_of(text, match.start()),
                body,
            )
    return "", 0, ""


def _history_facts(root: str, tag: str) -> Dict:
    facts = {
        "last_election": "",
        "frequency": 0,
        "term_limit": 0,
        "killswitch": False,
    }
    for path in iter_txt_files(os.path.join(root, "history", "countries")):
        if not os.path.basename(path).startswith(tag + " "):
            continue
        text = read_script(path, keep_quotes=True)
        election = re.search(r'last_election\s*=\s*"?([\d.]+)"?', text)
        frequency = re.search(r"election_frequency\s*=\s*(\d+)", text)
        limit = re.search(r"term_limit\s*=\s*(\d+)", text)
        facts["last_election"] = election.group(1) if election else ""
        facts["frequency"] = int(frequency.group(1)) if frequency else 0
        facts["term_limit"] = int(limit.group(1)) if limit else 0
        facts["killswitch"] = "generic_election_killswitch" in text
        break
    return facts


def _government_findings(root: str, tag: str) -> Dict:
    issues: List[str] = []
    roster_path = os.path.join(
        root, "common", "scripted_effects", tag + "_political_leaders.txt"
    )
    roster: Dict[str, List[Leader]] = {}
    if os.path.isfile(roster_path):
        roster = parse_leader_roster(read_script(roster_path, keep_quotes=True), tag)
    dated = {
        sub: sum(
            1
            for leader in leaders
            if leader.until and leader.until not in BOOKMARK_DATES
        )
        for sub, leaders in roster.items()
    }
    total_dated = sum(dated.values())

    parties = dict(PARTY_SLOT_NAMES)

    yearly = os.path.join(root, "common", "scripted_effects", "00_yearly_effects.txt")
    schedule = (
        parse_year_schedule(read_script(yearly), tag) if os.path.isfile(yearly) else []
    )

    walker = Walker()
    timetable: List[str] = []
    candidates: List[str] = []
    for event_id in sorted({entry[1] for entry in schedule}):
        path, line, body = find_event(root, event_id)
        if not body:
            issues.append(event_id + " is scheduled but no country_event defines it")
            continue
        immediate = _block_of(body, "immediate") or ""
        if not re.search(r"\bset_leader\b|change_ruling_party_effect", immediate):
            continue
        candidates.append(event_id)
        if not walker.event_id:
            walker = parse_walker(immediate)
            walker.event_id, walker.path, walker.line = event_id, path, line
    if len(candidates) > 1:
        issues.append(
            "{} scheduled events change the government ({}); this reads {}".format(
                len(candidates), ", ".join(candidates), walker.event_id
            )
        )

    history = _history_facts(root, tag)
    walker_dates = [
        (day_offset_to_date(year, days), event_id)
        for year, event_id, days in schedule
        if event_id == walker.event_id
    ]
    walker_dates.sort()

    if walker.event_id:
        if not walker_dates:
            issues.append(
                walker.event_id + " is never scheduled from 00_yearly_effects"
            )
        if walker.pins_leader:
            issues.append(
                "change_leader_temp = 1 sets do_not_retire and pins the roster pointer"
            )
        if history["killswitch"]:
            issues.append(
                "country carries generic_election_killswitch: extend its own "
                "election chain instead of stacking a walker"
            )
        if total_dated < TIMELINE_MIN_DATES:
            issues.append(
                "walker over an undated roster: {} real end-of-tenure dates".format(
                    total_dated
                )
            )
        if (
            walker.chain
            and walker.chain[-1].kind == "else"
            and walker.chain[-1].changes_party
        ):
            issues.append(
                "the chain's final else changes the ruling party with no upper "
                "date bound, so a late re-fire installs the wrong party"
            )
        reached = set()
        for date, _ in walker_dates:
            branch = resolve_branch(walker.chain, date)
            if branch is None:
                timetable.append(format_date(date) + "  no branch matches")
                continue
            reached.add(id(branch))
            party = (
                "{} ({})".format(branch.party, parties.get(branch.party, "?"))
                if branch.party is not None
                else "-"
            )
            person = "unasserted, the pointer blind-advances"
            if branch.pointer:
                sub, index = branch.pointer
                entry = next(
                    (leader for leader in roster.get(sub, []) if leader.index == index),
                    None,
                )
                person = (
                    "{}^{} {}".format(sub, index, entry.name)
                    if entry
                    else "{}^{} OUT OF RANGE".format(sub, index)
                )
            timetable.append(
                "{:<11} after {:<11} party {:<24} {}".format(
                    format_date(date), format_date(branch.after), party, person
                )
            )
        for position, branch in enumerate(walker.chain):
            label = "branch {} (after {})".format(position, format_date(branch.after))
            if branch.pointer is None:
                issues.append(
                    label + " asserts no roster index, so the pointer blind-advances"
                )
                continue
            sub, index = branch.pointer
            if not any(leader.index == index for leader in roster.get(sub, [])):
                issues.append(
                    "{} asserts {}^{}, which the roster does not define".format(
                        label, sub, index
                    )
                )
            elif (
                branch.party is not None
                and parties.get(branch.party)
                and parties[branch.party] != sub
            ):
                issues.append(
                    "{} installs party {} ({}) but seeds the {} pointer".format(
                        label, branch.party, parties[branch.party], sub
                    )
                )
            if id(branch) not in reached:
                issues.append(label + " is never reached by a scheduled date")
    elif total_dated >= TIMELINE_MIN_DATES:
        issues.append(
            "dated roster but no historical government walker"
            + (
                "; the country owns its election chain behind "
                "generic_election_killswitch, so extend that instead"
                if history["killswitch"]
                else ""
            )
        )

    verdict = "no roster file"
    if roster:
        verdict = (
            "dated timeline: a walker can name the historical person"
            if total_dated >= TIMELINE_MIN_DATES
            else "undated successor roster: write no walker"
        )
    return {
        "verdict": verdict,
        "roster": {
            sub: "{} entries, {} dated".format(len(leaders), dated[sub])
            for sub, leaders in sorted(roster.items())
        },
        "history": history,
        "walker": (
            "{} ({}:{})".format(walker.event_id, walker.path, walker.line)
            if walker.event_id
            else ""
        ),
        "timetable": timetable,
        "issues": issues,
    }


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------


def render(report: Dict, sections: Sequence[str]) -> str:
    out: List[str] = []
    out.append("AI path report: {} ({})".format(report["tag"], report["focus_file"]))
    out.append(
        "{} focuses, {} path flags, {} scripted path triggers".format(
            report["focus_count"], len(report["path_flags"]), len(report["triggers"])
        )
    )
    out.append("")

    if "rule" in sections:
        rule = report["rule"]
        out.append("RULE / WIRING  options: " + ", ".join(rule["options"]))
        out.extend("  ! " + issue for issue in rule["issues"])
        if not rule["issues"]:
            out.append("  clean")
        out.append("")

    if "owners" in sections:
        owners = report["owners"]
        out.append(
            "OWNERSHIP  {} owned / {} path-neutral".format(
                owners["owned"], owners["unowned"]
            )
        )
        for group, count in sorted(owners["groups"].items(), key=lambda item: -item[1]):
            out.append("  {:<5} {}".format(count, group))
            parties = owners["group_parties"].get(group, [])
            if parties:
                out.append(
                    "        parties ({}): {}".format(len(parties), ", ".join(parties))
                )
        if owners["additive"]:
            out.append("  ! additive path modifiers: " + ", ".join(owners["additive"]))
        if owners["unused_flags"]:
            out.append(
                "  ! flags never read in the tree: " + ", ".join(owners["unused_flags"])
            )
        for token, ids in owners["multi_root"].items():
            out.append(
                "  ! {} owns {} branch roots: {}".format(
                    token, len(ids), ", ".join(ids)
                )
            )
        out.append("")

    if "matrix" in sections:
        out.append(
            "STATE MATRIX  option / historical AI / live / zeroed / orphans / stranded"
        )
        for row in report["matrix"]:
            out.append(
                "  {:<22} {:<4} {:>5} {:>7} {:>8} {:>9}".format(
                    row["option"],
                    "on" if row["historical"] else "off",
                    row["live"],
                    row["zeroed"],
                    row["orphan_count"],
                    row["stranded_count"],
                )
            )
            if row["orphans"]:
                out.append("      orphans: " + ", ".join(row["orphans"]))
            if row["stranded"]:
                out.append("      stranded gates: " + ", ".join(row["stranded"]))
            if row["unevaluable"]:
                out.append("      unevaluable modifiers: {}".format(row["unevaluable"]))
        out.append("")

    if "graph" in sections:
        graph = report["graph"]
        out.append(
            "GRAPH  {} roots, {} focuses with no ai_will_do, "
            "{} path-relevant mutex ties, {} path-neutral ties".format(
                graph["roots"],
                graph["no_ai_will_do"],
                graph["mutex_tie_count"],
                graph["neutral_ties"],
            )
        )
        out.extend("  ! tie " + tie for tie in graph["mutex_ties"])
        if graph["mutex_both_owned_count"]:
            out.append(
                "  ! mutex pairs boosted on both sides: {}".format(
                    graph["mutex_both_owned_count"]
                )
            )
            out.extend("      " + row for row in graph["mutex_both_owned"])
        if graph["historical_override_count"]:
            out.append(
                "  ! alive only via global history under an explicit rule: {}".format(
                    graph["historical_override_count"]
                )
            )
            out.extend("      " + row for row in graph["historical_overrides"])
        out.append("")

    if "plans" in sections:
        plans = report["plans"]
        out.append("STRATEGY PLANS  {}".format(plans["plans"]))
        if plans["no_focus_factors"]:
            out.append("  no focus_factors: " + ", ".join(plans["no_focus_factors"]))
        if plans["reads_game_rule"]:
            out.append(
                "  ! reads has_game_rule: " + ", ".join(plans["reads_game_rule"])
            )
        if plans["zeroed_by_every_plan"]:
            out.append(
                "  ! zeroed by every plan ({}): {}".format(
                    plans["zeroed_by_every_plan_count"],
                    ", ".join(plans["zeroed_by_every_plan"]),
                )
            )
        out.extend("  ! " + conflict for conflict in plans["conflicts"])
        out.append("")

    if "rewards" in sections:
        out.append("DANGER REWARDS  {}".format(len(report["rewards"])))
        out.extend("  " + row for row in report["rewards"])
        out.append("")

    if "mechanics" in sections:
        mechanics = report["mechanics"]
        out.append(
            "MECHANICS  {} burdens, {} decisions in {} categories, {} GUIs".format(
                mechanics["burden_count"],
                mechanics["decisions"],
                len(mechanics["categories"]),
                mechanics["gui_count"],
            )
        )
        for row in mechanics["burdens"]:
            out.append(
                "  {:<19} {:<38} focus {:>2} / decision {:>2} {}".format(
                    row["kind"],
                    row["name"],
                    len(row["focus_cures"]),
                    len(row["decision_cures"]),
                    ", ".join(row["categories"]),
                ).rstrip()
            )
        for row in mechanics["guis"]:
            out.append(
                "  gui  {:<34} {:<20} {}".format(
                    row["id"], row["context"], row["backing"]
                )
            )
        if mechanics["unrelieved"]:
            out.append(
                "  nothing relieves ({}, judge the sign yourself): {}".format(
                    mechanics["unrelieved_count"], ", ".join(mechanics["unrelieved"])
                )
            )
        out.extend("  ! " + issue for issue in mechanics["issues"])
        if not mechanics["issues"]:
            out.append("  clean")
        out.append("")

    if "government" in sections:
        gov = report["government"]
        history = gov["history"]
        out.append("GOVERNMENT  " + gov["verdict"])
        out.append(
            "  elections  last {} every {} months, term_limit {}{}".format(
                history["last_election"] or "-",
                history["frequency"] or "-",
                history["term_limit"],
                ", generic_election_killswitch" if history["killswitch"] else "",
            )
        )
        for sub, summary in gov["roster"].items():
            out.append("  {:<28} {}".format(sub, summary))
        out.append("  walker  " + (gov["walker"] or "none"))
        out.extend("    " + row for row in gov["timetable"])
        out.extend("  ! " + issue for issue in gov["issues"])
        out.append("")

    return "\n".join(out).rstrip() + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Report the AI path facts for one country (issue #3162)."
    )
    parser.add_argument(
        "--tag", required=True, help="Three-letter country tag, e.g. DEN"
    )
    parser.add_argument(
        "--path", default=".", help="Mod root (default: current directory)"
    )
    parser.add_argument(
        "--section",
        action="append",
        choices=SECTIONS + ("all",),
        help="Limit output to one section; repeatable",
    )
    parser.add_argument(
        "--limit", type=int, default=15, help="Items per list (0 = all)"
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    tag = args.tag.upper()
    sections = args.section or ["all"]
    if "all" in sections:
        sections = list(SECTIONS)
    if "rule" in sections or "wiring" in sections:
        sections = list(sections) + ["rule"]

    report = build_report(args.path, tag, max(args.limit, 0))
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        sys.stdout.write(render(report, sections))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
