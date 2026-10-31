"""Advisory, bounded starting-research checks for AI equipment candidates."""

import itertools
import math
import re
from dataclasses import dataclass, field

from equipment_module_slots import (
    _depth0_text,
    _iter_blocks,
    _module_forbidden,
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


def _scalar_nodes(text, lo, hi):
    parts = []
    cursor = lo
    for _, _, end, header in _iter_blocks(text, lo, hi):
        parts.append(text[cursor:header])
        cursor = end + 1
    parts.append(text[cursor:hi])
    return script_nodes(re.sub(r"=\s*([<>])", r"\1", " ".join(parts)))


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
class Analysis:
    findings: list = field(default_factory=list)
    records: list = field(default_factory=list)


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
    unresolved_modules: bool = False
    allowed_modules: set = field(default_factory=set)


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
                for node in _scalar_nodes(text, vlo, vhi)
            )
            unresolved_modules = unsupported
            for key, lo, hi, _ in _iter_blocks(text, vlo, vhi):
                if key == "modules":
                    slots.extend(
                        (node.key, [(node.op, node.value)], False)
                        for node in _scalar_nodes(text, lo, hi)
                    )
                    slots.extend(
                        (slot, *_selection(text[slo:shi]))
                        for slot, slo, shi, _ in _iter_blocks(text, lo, hi)
                    )
                elif text[lo:hi].strip():
                    unsupported = True
                    unresolved_modules |= key != "upgrades"
            requirements = any(
                key == "requirements" and text[lo:hi].strip()
                for key, lo, hi, _ in _iter_blocks(text, dlo, dhi)
            )
            duplicates = len(slots) != len({slot for slot, _, _ in slots})
            unsupported |= duplicates or requirements
            unresolved_modules |= duplicates or requirements
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
                    bool(unresolved_modules),
                    _tokens(text, glo, ghi, "allowed_modules")
                    | _tokens(text, dlo, dhi, "allowed_modules"),
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


def _weight(node, truth, bounds=(1.0, 1.0)):
    if node.op != "=":
        return None
    if node.value is not None:
        if not _NUMBER.fullmatch(node.value):
            return None
        number = float(node.value)
        return (number, number) if math.isfinite(number) else None
    arithmetic = [
        child.key for child in node.children if child.key in {"base", "add", "factor"}
    ]
    if len(arithmetic) != len(set(arithmetic)) or {"add", "factor"} <= set(arithmetic):
        return None
    modified_before = False
    for child in node.children:
        if child.key == "modifier":
            if child.value is not None or child.op != "=":
                return None
            gate = truth(
                [
                    part
                    for part in child.children
                    if part.key not in {"base", "add", "factor"}
                ]
            )
            if gate is False:
                continue
            modified_before = True
            modified = _weight(child, truth, bounds)
            if gate is True:
                bounds = modified
            elif bounds is None or modified is None:
                bounds = None
            else:
                bounds = (min(bounds[0], modified[0]), max(bounds[1], modified[1]))
        elif child.key in {"base", "add", "factor"}:
            if (
                child.op != "="
                or modified_before
                or child.key == "base"
                and arithmetic[0] != "base"
            ):
                return None
            if child.value is None or not _NUMBER.fullmatch(child.value):
                bounds = None
                continue
            number = float(child.value)
            if not math.isfinite(number):
                bounds = None
            elif child.key == "base" or child.key == "factor" and number == 0:
                bounds = (number, number)
            elif bounds is not None:
                values = [
                    bound + number if child.key == "add" else bound * number
                    for bound in bounds
                ]
                bounds = (min(values), max(values))
        elif node.key != "modifier":
            return None
        if bounds is not None and not all(map(math.isfinite, bounds)):
            bounds = None
    return bounds


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


def _assessment(design, kind, status, reason="", **details):
    return {
        "kind": kind,
        "status": status,
        "file": design.file.replace("\\", "/"),
        "line": design.line,
        "group": design.group,
        "design": design.name,
        "reason": reason,
        **details,
    }


def check_ammunition_compatibility(designs, index):
    analysis = Analysis()
    findings = analysis.findings
    for design in designs:
        slots = index.hull_slots.get(design.hull)
        if slots is None:
            if any(
                "ammo" in slot or "ammunition" in slot for slot, _, _ in design.slots
            ):
                analysis.records.append(
                    _assessment(
                        design, "ammunition", "unknown", "unresolved hull slots"
                    )
                )
            continue
        ammunition = {
            slot
            for slot, _, _ in design.slots
            if ("ammo" in slot or "ammunition" in slot)
            and slot in slots
            and slots[slot]
            and slots[slot].allowed is not None
        }
        if not ammunition:
            continue
        domains = {}
        unresolved = design.unresolved_modules
        hull_types = index.hull_types.get(design.hull, set())
        for slot, references, unsupported in design.slots:
            candidates, _, unknown = _candidates(
                references, index, lambda _: (True, set())
            )
            domains[slot] = [
                module
                for module in candidates
                if module == "empty" or not _module_forbidden(module, hull_types, index)
            ]
            unresolved |= unsupported or unknown
        unresolved |= bool(design.allowed_modules) and bool(set(slots) - domains.keys())
        if unresolved:
            analysis.records.append(
                _assessment(
                    design,
                    "ammunition",
                    "unknown",
                    "inherited or dynamic selections, requirements, or allowed-module filling",
                    ammunition_slots=sorted(ammunition),
                )
            )
            continue
        for ammo_slot in sorted(ammunition):
            record = _assessment(
                design,
                "ammunition",
                "checked",
                ammunition_slot=ammo_slot,
                incompatible_choices={},
                unresolved_providers={},
            )
            analysis.records.append(record)
            entry = slots[ammo_slot]
            ammo = domains[ammo_slot]
            if not entry.required and "empty" in ammo:
                continue
            categories = {
                index.module_category[module] for module in ammo if module != "empty"
            }
            grants = {
                source: set().union(
                    *(
                        index.slot_unlocks.get(module, {}).get(ammo_slot, set())
                        for module in choices
                    )
                )
                for source, choices in domains.items()
            }
            if not categories & (entry.allowed | set().union(*grants.values())):
                record["status"] = "slot-error"
                record["reason"] = "covered by existing slot errors"
                continue
            for source, choices in domains.items():
                if source == ammo_slot or len(choices) < 2 or not grants[source]:
                    continue
                other = entry.allowed | set().union(
                    *(provided for slot, provided in grants.items() if slot != source)
                )
                incompatible = [
                    module
                    for module in choices
                    if module != "empty"
                    and ammo_slot in index.slot_unlocks.get(module, {})
                    and not categories & (other | index.slot_unlocks[module][ammo_slot])
                ]
                unproven = [
                    module
                    for module in choices
                    if module != "empty"
                    and ammo_slot not in index.slot_unlocks.get(module, {})
                    and not categories & other
                ]
                if unproven:
                    record["unresolved_providers"][source] = unproven
                if incompatible:
                    record["incompatible_choices"][source] = incompatible
                    requested = sorted(
                        {
                            reference
                            for slot, refs, _ in design.slots
                            if slot == ammo_slot
                            for _, reference in refs
                        }
                    )
                    findings.append(
                        Issue(
                            Severity.WARNING,
                            "ai-equipment-incompatible-ammo",
                            f"{design.group}/{design.name}: {', '.join(incompatible)} in {source} cannot use any {ammo_slot} option ({', '.join(requested)}); another weapon alternative was masking the mismatch",
                            design.file,
                            design.line,
                        )
                    )
            if record["unresolved_providers"]:
                record["reason"] = (
                    "some weapon choices have no recorded ammunition allowance"
                )
            if record["incompatible_choices"]:
                record["status"] = (
                    "partial" if record["unresolved_providers"] else "incompatible"
                )
            elif record["unresolved_providers"]:
                record["status"] = "unknown"
    return analysis


def _design_state(design, index, unlocked_hull, unlocked_module, truth):
    priorities = [_weight(node, truth) for node in design.priorities]
    if any(bounds is not None and bounds[1] <= 0 for bounds in priorities):
        return "deferred", "nonpositive priority at the selected start"
    slots = index.hull_slots.get(design.hull)
    if not design.slots and (design.hull in index.non_modular_hulls or slots == {}):
        return "not-applicable", "non-modular hull availability is not modeled"
    if slots is None:
        return "unknown", "unknown or dynamic hull, or unresolved hull slots"
    hull, _ = unlocked_hull(design.hull)
    enabled = truth(design.gates)
    if hull is False or enabled is False:
        return "future", ""
    if hull is None or enabled is None:
        return "unknown", "unresolved hull unlock or enable condition"
    if any(bounds is None or bounds[0] <= 0 for bounds in priorities):
        return "unknown", "priority may be nonpositive or is not statically bounded"
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


def project_unlocks(texts, context):
    result = {"technologies": set(), "hulls": set(), "modules": set()}
    fields = {"enable_equipments": "hulls", "enable_equipment_modules": "modules"}
    for content in texts:
        text = blank_comments(content)
        result["technologies"].update(
            starting_techs(
                script_nodes(text),
                {},
                context.start,
                effects=context.effects,
                possible=True,
            )
        )
        pending = [(0, len(text))]
        while pending:
            for key, lo, hi, _ in _iter_blocks(text, *pending.pop()):
                if key in fields:
                    result[fields[key]].update(_depth0_text(text, lo, hi).split())
                else:
                    pending.append((lo, hi))
    return result


def check_buildability(
    designs, index, context, hull_techs, module_techs, tech_gates, unmodeled=None
):
    analysis = Analysis()
    if not context.start:
        for design in designs:
            analysis.records.append(
                _assessment(
                    design,
                    "starting-buildability",
                    "unknown",
                    "No bookmark start date; starting buildability was not checked",
                )
            )
        return analysis
    start = (*context.start[:3], 12)
    designs_by_id = {id(design): design for design in designs}
    unmodeled = unmodeled or {}
    hull_techs = dict(hull_techs)
    for hull, source in index.hull_sources.items():
        if source in hull_techs:
            hull_techs.setdefault(hull, hull_techs[source])
    design_axes = {}
    for design in designs:
        techs = set(hull_techs.get(design.hull, set()))
        for _, references, _ in design.slots:
            candidates, _, _ = _candidates(references, index, lambda _: (True, set()))
            for module in candidates:
                techs.update(module_techs.get(module, set()))
        design_axes[id(design)] = _dlcs(
            design.gates
            + design.priorities
            + [node for tech in techs for node in tech_gates.get(tech, [])]
        )
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
            _dlcs(history or [], context.effects)
            | set().union(*(design_axes[id(design)] for design in applicable))
        )
        if history is None or 2 ** len(axes) > _MAX_DLC_CONFIGS:
            reason = (
                "missing country history"
                if history is None
                else "DLC configuration limit exceeded"
            )
            for design in applicable:
                analysis.records.append(
                    _assessment(
                        design,
                        "starting-buildability",
                        "unknown",
                        reason,
                        country=country,
                        roles=sorted(design.roles),
                        start=list(start[:3]),
                        dlc_configurations=[],
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

            def unlocked(token, mapping, kind):
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
                state = _combine(states, True)
                if state is not True and (
                    techs & unmodeled.get("technologies", set())
                    or token in unmodeled.get(kind, set())
                    or kind == "hulls"
                    and index.hull_sources.get(token) in unmodeled.get(kind, set())
                ):
                    state = None
                return state, techs

            results = [
                (
                    design,
                    *_design_state(
                        design,
                        index,
                        lambda hull: unlocked(hull, hull_techs, "hulls"),
                        lambda module: unlocked(module, module_techs, "modules"),
                        truth,
                    ),
                )
                for design in applicable
            ]
            coverage = {}
            for other, status, _ in results:
                for role in other.roles:
                    usable, unresolved = coverage.setdefault(
                        (other.category, role), (set(), False)
                    )
                    if status == "usable":
                        usable.add(f"{other.group}/{other.name}")
                    coverage[(other.category, role)] = (
                        usable,
                        unresolved
                        or status in {"unknown", "deferred", "not-applicable"},
                    )
            for design, state, reason in results:
                for role in sorted(design.roles):
                    usable, unresolved = coverage[(design.category, role)]
                    key = (
                        id(design),
                        state,
                        role,
                        reason,
                        tuple(sorted(usable)),
                        unresolved,
                    )
                    grouped.setdefault(key, []).append(dlcs)
        for (
            identity,
            state,
            role,
            reason,
            usable,
            unresolved,
        ), configs in grouped.items():
            design = designs_by_id[identity]
            role_coverage = (
                f"usable fallback: {', '.join(usable)}"
                if usable
                else (
                    "role coverage unresolved"
                    if unresolved
                    else "no usable starting fallback"
                )
            )
            analysis.records.append(
                _assessment(
                    design,
                    "starting-buildability",
                    state,
                    reason,
                    country=country,
                    role=role,
                    coverage=role_coverage,
                    usable_candidates=list(usable),
                    start=list(start[:3]),
                    dlc_configurations=configs,
                )
            )
            if state != "missing":
                continue
            message = f"{country}: {design.group}/{design.name} ({role}): {reason}; {role_coverage}"
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
            analysis.findings.append(
                Issue(
                    Severity.WARNING,
                    "ai-buildability-missing-unlock",
                    f"{message} [start {'.'.join(map(str, start[:3]))}; {context_label}]",
                    design.file,
                    design.line,
                )
            )
    return analysis
