#!/usr/bin/env python3
"""Find locally created equipment variants consumed before their unlock is assured.

This is a local effect-flow check, not a whole-program proof. External scripted
effects, focus prerequisites and history unlocks can establish availability too,
so findings are warnings. All equipment types use the same engine contract.
"""

import os
import re
import sys
from dataclasses import dataclass, field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from equipment_module_slots import _depth0_text, _iter_blocks, blank_comments
from linting.check_common_mistakes import (
    _first_child,
    _parse_script_nodes,
    _scope_frame_kind,
)
from shared_utils import FileOpener
from validator_common import BaseValidator, Severity, run_validator_main

_TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|[{}]|[<>!]=?|=|[^\s{}=<>!]+')
_LITERAL = re.compile(r"[A-Za-z_][\w.-]*\Z")
_CONSUMERS = {
    "add_equipment_production": "version_name",
    "create_ship": "equipment_variant",
    "add_equipment_to_stockpile": "variant_name",
}
_METADATA = {
    "limit",
    "trigger",
    "available",
    "allowed",
    "visible",
    "ai_will_do",
    "ai_chance",
    "modifier",
    "effect_tooltip",
    "custom_effect_tooltip",
    "custom_trigger_tooltip",
}
_EFFECTS = {
    "completion_reward",
    "complete_effect",
    "remove_effect",
    "timeout_effect",
    "cancel_effect",
    "immediate",
    "option",
    "effect",
    "project_output",
}


def _nodes(text):
    tokens = [
        (match.group(), line)
        for line, code in enumerate(blank_comments(text).splitlines(), 1)
        for match in _TOKEN.finditer(code)
    ]
    return _parse_script_nodes(tokens, 0)[0]


def _value(node, key):
    child = _first_child(node, key)
    return child.value.strip('"') if child and child.value else None


def equipment_unlocks(text):
    """Map equipment tokens to their enabling technologies, not assumed names."""
    text = blank_comments(text)
    result = {}
    for container, lo, hi, _ in _iter_blocks(text, 0, len(text)):
        if container != "technologies":
            continue
        for tech, tlo, thi, _ in _iter_blocks(text, lo, hi):
            for key, elo, ehi, _ in _iter_blocks(text, tlo, thi):
                if key == "enable_equipments":
                    for equipment in _depth0_text(text, elo, ehi).split():
                        if _LITERAL.fullmatch(equipment):
                            result.setdefault(equipment, set()).add(tech)
    return result


def _guaranteed(nodes):
    """Technologies required by a conjunctive trigger; OR needs every arm."""
    known = set()
    for node in nodes:
        if node.key == "has_tech" and node.value:
            known.add(node.value.strip('"'))
        elif node.key in {"AND", "hidden_trigger"}:
            known.update(_guaranteed(node.children))
        elif node.key == "OR" and node.children:
            known.update(set.intersection(*(_guaranteed([n]) for n in node.children)))
    return known


def _when_false(nodes):
    if len(nodes) == 1 and nodes[0].key == "NOT":
        return _guaranteed(nodes[0].children) if len(nodes[0].children) == 1 else set()
    return set()


@dataclass
class _Flow:
    techs: set = field(default_factory=set)
    pending: dict = field(default_factory=dict)

    def copy(self):
        return _Flow(self.techs.copy(), self.pending.copy())


def _join(states):
    pending = {}
    for state in states:
        for key, (techs, line) in state.pending.items():
            if not techs & state.techs:
                pending[key] = (techs, line)
    return _Flow(set.intersection(*(state.techs for state in states)), pending)


def check_variant_availability(text, unlocks):
    """Return (message, use-line) warnings for deferred variants used locally."""
    findings = set()

    def walk(nodes, state, country="ROOT"):
        index = 0
        while index < len(nodes):
            node = nodes[index]
            index += 1
            if node.key in _METADATA:
                continue
            if node.key == "if":
                outcomes = []
                remaining = state.copy()
                branch = node
                while True:
                    limit = _first_child(branch, "limit")
                    conditions = limit.children if limit else []
                    selected = remaining.copy()
                    selected.techs.update(_guaranteed(conditions))
                    outcomes.append(walk(branch.children, selected, country))
                    remaining.techs.update(_when_false(conditions))
                    if index == len(nodes) or nodes[index].key not in {
                        "else_if",
                        "else",
                    }:
                        outcomes.append(remaining)
                        break
                    branch = nodes[index]
                    index += 1
                    if branch.key == "else":
                        outcomes.append(walk(branch.children, remaining, country))
                        break
                state = _join(outcomes)
            elif node.key == "set_technology":
                for tech in node.children:
                    if tech.value == "1":
                        state.techs.add(tech.key)
                    elif tech.value == "0":
                        state.techs.discard(tech.key)
            elif node.key == "create_equipment_variant":
                equipment, name = _value(node, "type"), _value(node, "name")
                if not equipment or not name or any(c in name for c in "[]$"):
                    continue
                key = (equipment, name)
                techs = unlocks.get(equipment)
                if _value(node, "allow_without_tech") == "yes" or (
                    techs and techs & state.techs
                ):
                    state.pending.pop(key, None)
                elif techs:
                    state.pending[key] = (techs, node.line)
            elif node.key in _CONSUMERS:
                source = (
                    _first_child(node, "equipment")
                    if node.key == "add_equipment_production"
                    else node
                )
                if source is None:
                    continue
                creator = _value(
                    source,
                    (
                        "producer"
                        if node.key == "add_equipment_to_stockpile"
                        else "creator"
                    ),
                )
                if creator and creator not in {country, "THIS"}:
                    continue
                key = (_value(source, "type"), _value(source, _CONSUMERS[node.key]))
                deferred = state.pending.get(key)
                if deferred and not deferred[0] & state.techs:
                    findings.add(
                        (
                            f'{node.key} uses "{key[1]}" ({key[0]}) created at line '
                            f"{deferred[1]} without assured technology "
                            f'({", ".join(sorted(deferred[0]))}). Grant or require the '
                            "technology, or use allow_without_tech = yes before consuming the variant.",
                            node.line,
                        )
                    )
            elif node.key in {"hidden_effect", "THIS", country}:
                state = walk(node.children, state, country)
            elif node.key in {"random", "while"}:
                conditional = state.copy()
                limit = _first_child(node, "limit")
                conditional.techs.update(
                    _guaranteed(limit.children) if limit else set()
                )
                state = _join([state, walk(node.children, conditional, country)])
            elif node.key == "random_list":
                outcomes = []
                guaranteed_selection = False
                for outcome in node.children:
                    if outcome.value is not None or outcome.key in _METADATA:
                        continue
                    weight = (
                        float(outcome.key)
                        if re.fullmatch(r"-?\d+(?:\.\d+)?", outcome.key)
                        else None
                    )
                    modified = _first_child(outcome, "modifier") is not None
                    if weight is not None and weight <= 0 and not modified:
                        continue
                    trigger = _first_child(outcome, "trigger")
                    selected = state.copy()
                    selected.techs.update(
                        _guaranteed(trigger.children) if trigger else set()
                    )
                    outcomes.append(walk(outcome.children, selected, country))
                    if (
                        weight is not None
                        and weight > 0
                        and not modified
                        and not trigger
                    ):
                        guaranteed_selection = True
                if not guaranteed_selection:
                    outcomes.append(state)
                state = _join(outcomes)
            elif node.key in {"country_event", "news_event"}:
                event_state = _Flow()
                trigger = _first_child(node, "trigger")
                if trigger:
                    event_state.techs.update(_guaranteed(trigger.children))
                immediate = _first_child(node, "immediate")
                if immediate:
                    event_state = walk(immediate.children, event_state)
                for child in node.children:
                    if child.key != "immediate":
                        walk([child], event_state.copy())
            elif node.children:
                inherited = state.copy() if node.key in _EFFECTS else _Flow()
                for gate in node.children:
                    if gate.key in {"available", "trigger", "limit"}:
                        inherited.techs.update(_guaranteed(gate.children))
                scope = country
                if node.key == "ROOT":
                    scope = "ROOT"
                elif re.fullmatch(r"[A-Z]{3}", node.key):
                    scope = node.key
                elif (
                    _scope_frame_kind(node.key) == "foreign"
                    or node.key.startswith(("random_", "every_", "FROM", "PREV"))
                    or node.key in {"owner", "controller", "overlord"}
                    or node.key.isdigit()
                ):
                    scope = None
                walk(node.children, inherited, scope)
        return state

    walk(_nodes(text), _Flow())
    return sorted(findings, key=lambda finding: (finding[1], finding[0]))


class Validator(BaseValidator):
    TITLE = "EQUIPMENT VARIANT AVAILABILITY"
    STAGED_EXTENSIONS = [".txt"]

    def run_validations(self):
        unlocks = {}
        tech_files = self._collect_files(
            ["common/technologies/**/*.txt"], ignore_staged=True
        )
        for path in tech_files:
            for equipment, techs in equipment_unlocks(
                FileOpener.open_text_file(path)
            ).items():
                unlocks.setdefault(equipment, set()).update(techs)
        tech_changed = self.staged_only and any(
            "common/technologies/" in path.replace("\\", "/")
            for path in self.staged_files
        )
        results = []
        for path in self._collect_files(
            ["common/**/*.txt", "events/**/*.txt", "history/**/*.txt"],
            ignore_staged=tech_changed,
        ):
            text = FileOpener.open_text_file(path)
            if "create_equipment_variant" not in text:
                continue
            for message, line in check_variant_availability(text, unlocks):
                results.append((message, os.path.relpath(path, self.mod_path), line))
        self._report(
            results,
            "No locally deferred equipment variants consumed",
            "Equipment variants consumed without an assured unlock:",
            severity=Severity.WARNING,
            category="equipment-variant-unavailable",
        )


if __name__ == "__main__":
    run_validator_main(Validator, "Check equipment variant availability before use")
