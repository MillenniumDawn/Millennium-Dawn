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
    blank_quoted_strings,
    find_matching_brace,
    strip_comments,
)

SECTIONS = ("rule", "wiring", "owners", "matrix", "graph", "plans", "rewards")

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

_STATEMENT = re.compile(r"([A-Za-z_][A-Za-z0-9_.:]*)\s*=\s*")
_FOCUS_START = re.compile(r"^[ \t]*(focus|shared_focus|joint_focus)\s*=\s*\{", re.M)
_ID_LINE = re.compile(r"^[ \t]*id\s*=\s*(\S+)", re.M)
_LOC_KEY = re.compile(r'^\s*([A-Za-z_][A-Za-z0-9_]*):\s*\d*\s*"(.*)"\s*$')
_YEAR = re.compile(r"\b(19|20)\d{2}\b")
_HIGHLIGHT = re.compile(r"§.*?§!")
_LOC_SCOPE = re.compile(r"\[[^\]]*\]")

# Three-valued logic: None means "depends on something this tool cannot model".
TRUE, FALSE, UNKNOWN = True, False, None


# --------------------------------------------------------------------------
# Script parsing
# --------------------------------------------------------------------------


def read_script(path: str, keep_quotes: bool = False) -> str:
    """Read a mod file and neutralise comments, and by default quoted strings.

    Both passes preserve length and newlines, so every offset and line number
    computed downstream still points at the original file. `keep_quotes` is for
    files whose quoted values are the data (loc key names in a game rule).
    """
    with open(path, "r", encoding="utf-8-sig", errors="replace") as handle:
        text = strip_comments(handle.read())
    return text if keep_quotes else blank_quoted_strings(text)


def iter_statements(body: str) -> Iterator[Tuple[str, Optional[str], Optional[str]]]:
    """Yield (key, scalar, block) for every `key = ...` at depth 0 of *body*."""
    index = 0
    length = len(body)
    while index < length:
        char = body[index]
        if char in "{}":
            index += 1
            continue
        match = _STATEMENT.match(body, index)
        if not match:
            index += 1
            continue
        cursor = match.end()
        while cursor < length and body[cursor] in " \t\r\n":
            cursor += 1
        if cursor < length and body[cursor] == "{":
            close = find_matching_brace(body, cursor)
            if close == -1:
                return
            yield match.group(1), None, body[cursor + 1 : close]
            index = close + 1
            continue
        if cursor < length and body[cursor] == '"':
            stop = body.find('"', cursor + 1)
            if stop == -1:
                return
            yield match.group(1), body[cursor + 1 : stop], None
            index = stop + 1
            continue
        stop = cursor
        while stop < length and body[stop] not in " \t\r\n{}":
            stop += 1
        yield match.group(1), body[cursor:stop], None
        index = stop


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


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
    folder = os.path.join(root, "common", "scripted_triggers")
    if not os.path.isdir(folder):
        return triggers
    opener = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\{", re.M)
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".txt"):
            continue
        text = read_script(os.path.join(folder, name))
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
    always_off: bool = False
    base: float = 1.0
    has_ai_will_do: bool = False
    modifiers: List[Modifier] = field(default_factory=list)
    dangers: List[str] = field(default_factory=list)

    @property
    def owner_tokens(self) -> Tuple[str, ...]:
        for modifier in self.modifiers:
            if modifier.path_related and modifier.value > 1:
                return modifier.tokens
        return ()


def parse_focus_file(text: str, tag: str) -> List[Focus]:
    focuses: List[Focus] = []
    position = 0
    while True:
        match = _FOCUS_START.search(text, position)
        if not match:
            return focuses
        open_index = text.index("{", match.start())
        close = find_matching_brace(text, open_index)
        if close == -1:
            return focuses
        body = text[open_index + 1 : close]
        position = close + 1
        id_match = _ID_LINE.search(body)
        if not id_match:
            continue
        focuses.append(
            _build_focus(
                id_match.group(1), match.group(1), line_of(text, match.start()), body, tag
            )
        )


def _build_focus(
    focus_id: str, kind: str, line: int, body: str, tag: str
) -> Focus:
    focus = Focus(id=focus_id, line=line, kind=kind)
    for key, scalar, block in iter_statements(body):
        if key == "prerequisite" and block is not None:
            group = [value for name, value, _ in iter_statements(block) if name == "focus"]
            if group:
                focus.prereq_groups.append(group)
        elif key == "mutually_exclusive" and block is not None:
            focus.mutex.extend(
                value for name, value, _ in iter_statements(block) if name == "focus"
            )
        elif key in ("available", "allow_branch") and block is not None:
            _read_gates(block, focus)
        elif key == "ai_will_do" and block is not None:
            focus.has_ai_will_do = True
            _read_ai_will_do(block, focus, tag)
        elif key.startswith("completion_reward") and block is not None:
            focus.dangers.extend(_scan_dangers(block))
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
        r"has_game_rule\s*=\s*\{\s*rule\s*=\s*" + tag + r"_ai_behavior\s+option\s*=\s*(\w+)"
    )
    for match in rule_ref.finditer(text):
        option = match.group(1)
        limit_open = text.rfind("limit", 0, match.start())
        block_start = text.find("{", text.rfind("if", 0, limit_open) if limit_open > 0 else 0)
        close = find_matching_brace(text, block_start) if block_start != -1 else -1
        scope = text[match.end() : close] if close != -1 else text[match.end() : match.end() + 2000]
        flags = re.findall(r"set_global_flag\s*=\s*(" + tag + r"_\w+_FOCUS_PATH)", scope)
        per_option.setdefault(option, []).extend(flags)
        if option == "RANDOM_PATH":
            for weight, flag in re.findall(
                r"([0-9.]+)\s*=\s*\{\s*set_global_flag\s*=\s*(" + tag + r"_\w+_FOCUS_PATH)",
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
    path = os.path.join(root, "common", "ai_strategy_plans", tag + "_strategy_plans.txt")
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
        options = [(flag, flag) for flag in flags] + [("NO_PATH", None)]
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
        focus_id for focus_id, is_alive in alive.items() if is_alive and not focuses[focus_id].prereq_groups
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
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".txt"):
            continue
        path = os.path.join(folder, name)
        text = read_script(path)
        head = text[: text.find("focus", 200) if "focus" in text else 4000]
        if country_ref.search(head[:4000]):
            matches.append(path)
    if len(matches) == 1:
        return matches[0]
    counted = []
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".txt"):
            continue
        path = os.path.join(folder, name)
        with open(path, "r", encoding="utf-8-sig", errors="replace") as handle:
            count = len(re.findall(r"^[ \t]*id\s*=\s*" + tag + r"_", handle.read(), re.M))
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
        "graph": _graph_findings(focuses, by_id, weights, limit),
        "plans": _plan_findings(plans, by_id, limit),
        "rewards": _reward_findings(focuses, limit),
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
        return {"issues": ["no " + tag + "_ai_behavior rule in 00_game_rules.txt"], "options": []}
    options = [option.name for option in rule.options]
    defaults = [option.name for option in rule.options if option.is_default]
    if defaults != ["HISTORICAL"]:
        issues.append("default block is {}, expected HISTORICAL".format(defaults or "missing"))
    if "DEFAULT" in options:
        issues.append("DEFAULT option still present")
    for required in ("RANDOM_PATH", "NO_PATH"):
        if required not in options:
            issues.append("missing " + required + " option")
    if rule.header_key and rule.header_key not in loc:
        issues.append("header key " + rule.header_key + " has no localisation")
    elif rule.header_key:
        header = loc[rule.header_key]
        if not header.startswith("@" + tag + " "):
            issues.append("header key should read '@{} <short name>', found '{}'".format(tag, header))
    for option in rule.options:
        if option.name == "RANDOM_PATH" and option.text_key != "RULE_OPTION_MD_RANDOM_PATH":
            issues.append("RANDOM_PATH must reuse RULE_OPTION_MD_RANDOM_PATH")
        if option.name == "NO_PATH" and option.text_key != "RULE_OPTION_MD_NO_PATH":
            issues.append("NO_PATH must reuse RULE_OPTION_MD_NO_PATH")
        if option.text_key and option.text_key not in loc:
            issues.append("missing loc key " + option.text_key)
        if option.name == "HISTORICAL" and loc.get(option.text_key) not in (None, "Historical"):
            issues.append(
                "historical option text is '{}', must be 'Historical'".format(loc[option.text_key])
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
                issues.append("{} has {} sentences, must be 2".format(option.desc_key, sentences))
            if _YEAR.search(desc):
                issues.append(option.desc_key + " contains a hard date")

    wired = {option: values for option, values in wiring.items() if values}
    for option in options:
        if option in ("RANDOM_PATH", "NO_PATH"):
            continue
        if option not in wired:
            issues.append("option " + option + " sets no global flag in 999_game_rules_on_actions")
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
    for focus in owned:
        key = " + ".join(focus.owner_tokens) or "(kill only)"
        groups[key] = groups.get(key, 0) + 1
    unused = [flag for flag in flags if flag not in referenced]
    return {
        "owned": len(owned),
        "unowned": len(focuses) - len(owned),
        "groups": groups,
        "additive": sorted(set(additive)),
        "unused_flags": unused,
    }


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


def _graph_findings(
    focuses: Sequence[Focus],
    by_id: Dict[str, Focus],
    weights: Dict[str, List[float]],
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
    missing = [focus.id for focus in focuses if not focus.has_ai_will_do]
    return {
        "roots": sum(1 for focus in focuses if not focus.prereq_groups),
        "mutex_ties": routing_ties[:limit] if limit else routing_ties,
        "mutex_tie_count": len(routing_ties),
        "neutral_ties": neutral_ties,
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
            "OWNERSHIP  {} owned / {} path-neutral".format(owners["owned"], owners["unowned"])
        )
        for group, count in sorted(owners["groups"].items(), key=lambda item: -item[1]):
            out.append("  {:<5} {}".format(count, group))
        if owners["additive"]:
            out.append("  ! additive path modifiers: " + ", ".join(owners["additive"]))
        if owners["unused_flags"]:
            out.append("  ! flags never read in the tree: " + ", ".join(owners["unused_flags"]))
        out.append("")

    if "matrix" in sections:
        out.append("STATE MATRIX  option / historical AI / live / zeroed / orphans / stranded")
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
        out.append("")

    if "plans" in sections:
        plans = report["plans"]
        out.append("STRATEGY PLANS  {}".format(plans["plans"]))
        if plans["no_focus_factors"]:
            out.append("  no focus_factors: " + ", ".join(plans["no_focus_factors"]))
        if plans["reads_game_rule"]:
            out.append("  ! reads has_game_rule: " + ", ".join(plans["reads_game_rule"]))
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

    return "\n".join(out).rstrip() + "\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Report the AI path facts for one country (issue #3162)."
    )
    parser.add_argument("--tag", required=True, help="Three-letter country tag, e.g. DEN")
    parser.add_argument("--path", default=".", help="Mod root (default: current directory)")
    parser.add_argument(
        "--section",
        action="append",
        choices=SECTIONS + ("all",),
        help="Limit output to one section; repeatable",
    )
    parser.add_argument("--limit", type=int, default=15, help="Items per list (0 = all)")
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
