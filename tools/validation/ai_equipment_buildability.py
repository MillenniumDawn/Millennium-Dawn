"""Advisory, bounded starting-research checks for AI equipment candidates."""

import itertools
import math
import re
from dataclasses import dataclass

from equipment_module_slots import (
    _depth0_text,
    _iter_blocks,
    _scalar,
    blank_comments,
    check_target_variants,
)
from equipment_variant_context import script_nodes, starting_techs
from validator_common import Issue, Severity

_DATE = re.compile(r"\d{4}\.\d{1,2}\.\d{1,2}(?:\.\d{1,2})?")
_NUMBER = re.compile(r"-?\d+(?:\.\d+)?")
_TOKEN = re.compile(r"[A-Za-z_]\w*\Z")
_MAX_SELECTIONS = 256
_MAX_DLC_CONFIGS = 64


def _date(text):
    if not _DATE.fullmatch(text):
        return None
    parts = tuple(map(int, text.split(".")))
    return parts if len(parts) == 4 else (*parts, 0)


def _children(nodes, key):
    return [child for node in nodes if node.key == key for child in node.children]


def _tokens(text, lo, hi, key):
    return {
        token
        for name, blo, bhi, _ in _iter_blocks(text, lo, hi)
        if name == key
        for token in _depth0_text(text, blo, bhi).split()
    }


def _selection(text):
    text = re.sub(r"=\s*([<>])", r"\1", text)
    nodes = script_nodes(text)
    references = [(node.op, node.value) for node in nodes if node.key == "module"]
    for name, lo, hi, _ in _iter_blocks(text, 0, len(text)):
        if name == "any_of":
            references.extend(("=", token) for token in text[lo:hi].split())
    unknown = any(node.key not in {"module", "any_of"} for node in nodes)
    return references, unknown


@dataclass
class Design:
    group: str
    name: str
    category: str
    roles: set
    users: set
    blocked: set
    file: str
    line: int
    hull: str | None
    slots: list
    gates: list
    priorities: list
    unsupported: bool


def parse_designs(content, path):
    text = blank_comments(content)
    designs = []
    for group, glo, ghi, _ in _iter_blocks(text, 0, len(text)):
        category = _scalar(text, glo, ghi, "category")
        roles = _tokens(text, glo, ghi, "roles")
        if category not in {"land", "naval", "air"} or not roles:
            continue
        group_nodes = script_nodes(text[glo:ghi])
        for name, dlo, dhi, header in _iter_blocks(text, glo, ghi):
            variants = [
                (lo, hi)
                for key, lo, hi, _ in _iter_blocks(text, dlo, dhi)
                if key == "target_variant"
            ]
            if not variants:
                continue
            vlo, vhi = variants[0]
            nodes = script_nodes(text[dlo:dhi])
            slots = []
            unsupported = len(variants) != 1 or any(
                node.key not in {"type", "match_value"}
                for node in script_nodes(_depth0_text(text, vlo, vhi))
            )
            for key, lo, hi, _ in _iter_blocks(text, vlo, vhi):
                if key == "modules":
                    scalar = re.sub(r"=\s*([<>])", r"\1", _depth0_text(text, lo, hi))
                    slots.extend(
                        (node.key, [(node.op, node.value)], False)
                        for node in script_nodes(scalar)
                    )
                    slots.extend(
                        (slot, *_selection(text[slo:shi]))
                        for slot, slo, shi, _ in _iter_blocks(text, lo, hi)
                    )
                elif text[lo:hi].strip():
                    unsupported = True
            unsupported |= len(slots) != len({slot for slot, _, _ in slots})
            unsupported |= any(
                key == "requirements" and text[lo:hi].strip()
                for key, lo, hi, _ in _iter_blocks(text, dlo, dhi)
            )
            designs.append(
                Design(
                    group,
                    name,
                    category,
                    roles,
                    _tokens(text, glo, ghi, "available_for"),
                    _tokens(text, glo, ghi, "blocked_for"),
                    path,
                    text.count("\n", 0, header) + 1,
                    _scalar(text, vlo, vhi, "type"),
                    slots,
                    _children(group_nodes, "enable") + _children(nodes, "enable"),
                    [node for node in group_nodes + nodes if node.key == "priority"],
                    bool(unsupported),
                )
            )
    return designs


def _combine(results, disjunction=False):
    decisive = True if disjunction else False
    if decisive in results:
        return decisive
    return None if None in results else not decisive


def _truth(nodes, known, possible, dlcs, country, start):
    results = []
    for node in nodes:
        result = None
        if node.key == "date" and node.value:
            date = _date(node.value.strip('"'))
            if date:
                result = {"=": start == date, ">": start > date, "<": start < date}.get(
                    node.op
                )
        elif node.op == "=":
            if node.key == "has_tech" and node.value:
                tech = node.value.strip('"')
                result = True if tech in known else None if tech in possible else False
            elif node.key == "has_dlc" and node.value:
                result = dlcs.get(node.value.strip('"'))
            elif node.key == "tag" and node.value:
                result = country == node.value.strip('"')
            elif node.key == "always":
                result = {"yes": True, "no": False}.get(node.value)
            elif node.key in {"AND", "OR", "NOT", "hidden_trigger"}:
                arms = [
                    _truth([child], known, possible, dlcs, country, start)
                    for child in node.children
                ]
                result = _combine(arms, node.key in {"OR", "NOT"})
                if node.key == "NOT" and result is not None:
                    result = not result
        results.append(result)
    return _combine(results)


def _weight(node, truth, weight=1.0):
    if node.value is not None:
        if not _NUMBER.fullmatch(node.value):
            return None
        number = float(node.value)
        return number if math.isfinite(number) else None
    for child in node.children:
        if child.key == "modifier":
            gate = truth(
                [
                    part
                    for part in child.children
                    if part.key not in {"base", "add", "factor"}
                ]
            )
            if gate is None:
                return None
            if gate:
                weight = _weight(child, truth, weight)
        elif child.key in {"base", "add", "factor"}:
            if child.value is None or not _NUMBER.fullmatch(child.value):
                return None
            number = float(child.value)
            weight = (
                number
                if child.key == "base"
                else weight + number if child.key == "add" else weight * number
            )
        elif node.key != "modifier":
            return None
        if weight is None or not math.isfinite(weight):
            return None
    return weight


def _candidates(references, index, unlocked):
    candidates, missing = set(), set()
    unknown = False
    for operator, reference in references:
        if operator != "=" or not reference or not _TOKEN.fullmatch(reference):
            unknown = True
            continue
        if reference == "empty":
            candidates.add("empty")
            continue
        modules = (
            {reference}
            if reference in index.module_category
            else {
                module
                for module, category in index.module_category.items()
                if category == reference
            }
        )
        if not modules:
            unknown = True
        for module in sorted(modules):
            state, techs = unlocked(module)
            if state is True:
                candidates.add(module)
            elif state is None:
                unknown = True
            else:
                missing.add(f"{module} requires {' or '.join(sorted(techs))}")
    return sorted(candidates), missing, unknown


def _design_state(design, index, unlocked_hull, unlocked_module, truth):
    if index.hull_slots.get(design.hull) is None:
        return "unknown", "unknown or dynamic hull, or unresolved hull slots"
    hull, _ = unlocked_hull(design.hull)
    enabled = truth(design.gates)
    if hull is False or enabled is False:
        return "future", ""
    if hull is None or enabled is None:
        return "unknown", "unresolved hull unlock or enable condition"
    priorities = [_weight(node, truth) for node in design.priorities]
    if any(weight is None or weight <= 0 for weight in priorities):
        return "unknown", "dynamic or nonpositive priority"
    choices, missing = [], set()
    unknown = design.unsupported
    for slot, references, unsupported in design.slots:
        candidates, needs, unresolved = _candidates(references, index, unlocked_module)
        unknown |= unsupported
        if not candidates and needs and not (unsupported or unresolved):
            missing.update(needs)
        choices.append([(slot, module) for module in candidates])
    if missing and not design.unsupported:
        return "missing", "; ".join(sorted(missing))
    count = math.prod(len(options) for options in choices)
    if unknown or not count or count > _MAX_SELECTIONS:
        return (
            "unknown",
            "unresolved module selection, requirements, upgrades, or selection limit",
        )
    for selection in itertools.product(*choices):
        modules = " ".join(f"{slot} = {module}" for slot, module in selection)
        variant = (
            f"target_variant = {{ type = {design.hull} modules = {{ {modules} }} }}"
        )
        if not check_target_variants(variant, index):
            return "usable", ""
    return (
        "unknown",
        "no slot-valid researched selection proved; see existing slot checks",
    )


def _dlcs(nodes, effects=None):
    result, seen = set(), set()
    pending = list(nodes)
    while pending:
        node = pending.pop()
        if node.key == "has_dlc" and node.value:
            result.add(node.value.strip('"'))
        pending.extend(node.children)
        if effects and node.key in effects and node.key not in seen:
            seen.add(node.key)
            pending.extend(effects[node.key][1])
    return result


def check_buildability(designs, index, context, hull_techs, module_techs, tech_gates):
    if not context.start:
        if not designs:
            return []
        return [
            Issue(
                Severity.WARNING,
                "ai-buildability-unresolved",
                "No bookmark start date; starting buildability was not checked",
                designs[0].file,
                designs[0].line,
            )
        ]
    start = (*context.start[:3], 12)
    findings = []
    dlc_names = _dlcs([node for nodes in tech_gates.values() for node in nodes])
    for country in sorted(
        set(context.histories) | {tag for design in designs for tag in design.users}
    ):
        applicable = [
            design
            for design in designs
            if (not design.users or country in design.users)
            and country not in design.blocked
        ]
        if not applicable:
            continue
        history = context.histories.get(country)
        axes = sorted(
            dlc_names
            | _dlcs(history or [], context.effects)
            | _dlcs(
                [
                    node
                    for design in applicable
                    for node in design.gates + design.priorities
                ]
            )
        )
        if history is None or 2 ** len(axes) > _MAX_DLC_CONFIGS:
            reason = (
                "missing country history"
                if history is None
                else "DLC configuration limit exceeded"
            )
            findings.append(
                Issue(
                    Severity.WARNING,
                    "ai-buildability-unresolved",
                    f"{country}: {reason}",
                    applicable[0].file,
                    applicable[0].line,
                )
            )
            continue
        grouped = {}
        for bits in itertools.product((False, True), repeat=len(axes)):
            dlcs = dict(zip(axes, bits))
            known = starting_techs(history, dlcs, start[:3], effects=context.effects)
            possible = starting_techs(
                history, dlcs, start[:3], effects=context.effects, possible=True
            )

            def truth(nodes):
                return _truth(nodes, known, possible, dlcs, country, start)

            def unlocked(token, mapping):
                techs = mapping.get(token)
                if not techs:
                    return None, set()
                states = []
                for tech in techs:
                    researched = (
                        True if tech in known else None if tech in possible else False
                    )
                    states.append(
                        _combine([researched, truth(tech_gates.get(tech, []))])
                    )
                return _combine(states, True), techs

            results = [
                (
                    design,
                    *_design_state(
                        design,
                        index,
                        lambda hull: unlocked(hull, hull_techs),
                        lambda module: unlocked(module, module_techs),
                        truth,
                    ),
                )
                for design in applicable
            ]
            for design, state, reason in results:
                if state not in {"missing", "unknown"}:
                    continue
                for role in sorted(design.roles):
                    peers = [
                        (other, status)
                        for other, status, _ in results
                        if other.category == design.category and role in other.roles
                    ]
                    usable = sorted(
                        {other.name for other, status in peers if status == "usable"}
                    )
                    unresolved = any(status == "unknown" for _, status in peers)
                    coverage = (
                        f"usable fallback: {', '.join(usable)}"
                        if usable
                        else (
                            "role coverage unresolved"
                            if unresolved
                            else "no usable starting fallback"
                        )
                    )
                    category = (
                        "ai-buildability-missing-unlock"
                        if state == "missing"
                        else "ai-buildability-unresolved"
                    )
                    message = f"{country}: {design.group}/{design.name} ({role}): {reason}; {coverage}"
                    key = (category, message, design.file, design.line)
                    grouped.setdefault(key, []).append(dlcs)
        for (category, message, path, line), configs in grouped.items():
            labels = [
                " + ".join(
                    name if enabled else f"NOT {name}"
                    for name, enabled in config.items()
                )
                or "no DLC conditions"
                for config in configs
            ]
            context_label = (
                f"all {len(configs)} evaluated DLC configurations"
                if axes and len(configs) == 2 ** len(axes)
                else "; ".join(labels)
            )
            findings.append(
                Issue(
                    Severity.WARNING,
                    category,
                    f"{message} [start {'.'.join(map(str, start[:3]))}; {context_label}]",
                    path,
                    line,
                )
            )
    return findings
