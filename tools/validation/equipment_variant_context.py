"""Conservative country and starting-technology context for equipment rewards."""

import re
from dataclasses import dataclass, field

from equipment_module_slots import blank_comments
from linting.check_common_mistakes import (
    _first_child,
    _parse_script_nodes,
    _scope_frame_kind,
)

_TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|[{}]|[<>!]=?|=|[^\s{}=<>!]+')
_DATE = re.compile(r"\d{4}\.\d{1,2}\.\d{1,2}(?:\.\d{1,2})?")
_WRAPPERS = {
    "AND",
    "hidden_trigger",
    "custom_trigger_tooltip",
    "custom_override_tooltip",
}


def script_nodes(text):
    tokens = [
        (match.group(), line)
        for line, code in enumerate(blank_comments(text).splitlines(), 1)
        for match in _TOKEN.finditer(code)
    ]
    return _parse_script_nodes(tokens, 0)[0]


def value(node, key):
    child = _first_child(node, key)
    return child.value.strip('"') if child and child.value else None


def event_pool_targets(text):
    """Bare event lists are omitted by the shared assignment-only AST parser."""
    return {
        event
        for block in re.finditer(
            r"\b(?:random_events|events)\s*=\s*\{([^{}]*)\}", blank_comments(text)
        )
        for event in re.findall(r"\b[A-Za-z_]\w*\.\d+\b", block[1])
    }


def countries(nodes):
    """Return a bounded set of country identities, or None for an unknown set."""
    result = None
    for node in nodes:
        found = None
        if node.key in {"tag", "original_tag"} and node.value and node.op == "=":
            tag = node.value.strip('"')
            if re.fullmatch(r"[A-Z]{3}", tag):
                found = {tag}
        elif node.key in _WRAPPERS:
            found = countries(node.children)
        elif node.key == "OR" and node.children:
            arms = [countries([child]) for child in node.children]
            if all(arm is not None for arm in arms):
                found = set().union(*arms)
        if found is not None:
            result = found if result is None else result & found
    return result


def scope_country(key, current, root):
    if key == "ROOT":
        return root
    if re.fullmatch(r"[A-Z]{3}", key):
        return frozenset({key})
    if (
        _scope_frame_kind(key) == "foreign"
        or key.startswith(("random_", "every_", "FROM", "PREV"))
        or key in {"owner", "controller", "overlord"}
        or key.isdigit()
    ):
        return frozenset({None})
    return current


def focus_countries(node):
    country = _first_child(node, "country")
    if not country or value(country, "factor") != "0":
        return None
    result = set()
    for modifier in country.children:
        if modifier.key != "modifier":
            continue
        add = value(modifier, "add")
        if add is None or not re.fullmatch(r"-?\d+(?:\.\d+)?", add):
            return None
        if float(add) <= 0:
            continue
        tags = countries(modifier.children)
        if tags is None:
            return None
        result.update(tags)
    return result or None


def dlc_truth(nodes, dlcs):
    """Evaluate only DLC/constant predicates; every other predicate is unknown."""
    results = []
    for node in nodes:
        if node.op != "=":
            result = None
        elif node.key == "has_dlc" and node.value:
            result = dlcs.get(node.value.strip('"'))
        elif node.key == "always":
            result = {"yes": True, "no": False}.get(node.value)
        elif node.key in _WRAPPERS or node.key == "NOT":
            result = dlc_truth(node.children, dlcs)
            if node.key == "NOT" and result is not None:
                result = not result
        elif node.key == "OR":
            arms = [dlc_truth([child], dlcs) for child in node.children]
            result = True if True in arms else None if None in arms else False
        else:
            result = None
        results.append(result)
    return False if False in results else None if None in results else True


def branches(nodes, dlcs):
    """Yield ordinary nodes or every possible arm of an if/else chain."""
    index = 0
    while index < len(nodes):
        node = nodes[index]
        index += 1
        if node.key != "if":
            yield node
            continue
        outcomes = []
        reachable = True
        while True:
            limit = _first_child(node, "limit")
            truth = dlc_truth(limit.children, dlcs) if limit else None
            if reachable and truth is not False:
                outcomes.append(
                    [child for child in node.children if child.key != "limit"]
                )
            reachable = reachable and truth is not True
            if index == len(nodes) or nodes[index].key not in {"else_if", "else"}:
                if reachable:
                    outcomes.append([])
                break
            node = nodes[index]
            index += 1
            if node.key == "else":
                if reachable:
                    outcomes.append(node.children)
                break
        yield outcomes


def starting_techs(nodes, dlcs, start, known=None):
    known = set(known or ())
    dated = [node for node in nodes if _DATE.fullmatch(node.key)]
    ordered = [node for node in nodes if not _DATE.fullmatch(node.key)]
    ordered += sorted(
        dated, key=lambda node: tuple(int(part) for part in node.key.split("."))
    )
    for node in branches(ordered, dlcs):
        if isinstance(node, list):
            outcomes = [starting_techs(arm, dlcs, start, known) for arm in node]
            known = set.intersection(*outcomes)
        elif node.key == "set_technology":
            for tech in node.children:
                if tech.value == "1":
                    known.add(tech.key)
                elif tech.value == "0":
                    known.discard(tech.key)
        elif node.key == "hidden_effect":
            known = starting_techs(node.children, dlcs, start, known)
        elif _DATE.fullmatch(node.key) and start:
            date = tuple(int(part) for part in node.key.split("."))[:3]
            if date <= start:
                known = starting_techs(node.children, dlcs, start, known)
    return known


@dataclass
class VariantContext:
    documents: dict = field(default_factory=dict)
    histories: dict = field(default_factory=dict)
    categories: dict = field(default_factory=dict)
    event_countries: dict = field(default_factory=dict)
    unknown_events: set = field(default_factory=set)
    tech_dlcs: dict = field(default_factory=dict)
    start: tuple = ()
    _history_cache: dict = field(default_factory=dict)

    def history(self, country, dlcs):
        key = (country, tuple(sorted(dlcs.items())))
        if key not in self._history_cache:
            self._history_cache[key] = starting_techs(
                self.histories.get(country, []), dlcs, self.start
            )
        return self._history_cache[key]

    def index(self):
        """Resolve event recipients through all known callers, preserving unknown paths."""
        definitions = {}
        folders = {}
        dates = []
        for path, nodes in self.documents.items():
            if path.startswith("history/countries/"):
                match = re.match(r"([A-Z]{3})(?:\s|\.)", path.rsplit("/", 1)[-1])
                if match:
                    self.histories[match[1]] = nodes
            for node in nodes:
                if path.startswith("events/") and node.key in {
                    "country_event",
                    "news_event",
                }:
                    event = value(node, "id")
                    if event:
                        definitions[event] = node
                elif path.startswith("common/decisions/categories/"):
                    allowed = _first_child(node, "allowed")
                    self.categories[node.key] = (
                        countries(allowed.children) if allowed else None
                    )
                elif node.key == "technology_folders":
                    for folder in node.children:
                        available = _first_child(folder, "available")
                        folders[folder.key] = available.children if available else []
                elif node.key == "bookmarks":
                    for bookmark in node.children:
                        date = value(bookmark, "date")
                        if date and _DATE.fullmatch(date):
                            dates.append(
                                tuple(int(part) for part in date.split("."))[:3]
                            )
        self.start = min(dates) if dates else ()
        for nodes in self.documents.values():
            for node in nodes:
                if node.key == "technologies":
                    for tech in node.children:
                        folder = _first_child(tech, "folder")
                        gates = folders.get(value(folder, "name"), []) if folder else []
                        # Only simple folder DLC requirements establish equipment context.
                        dlcs = {}
                        for gate in gates:
                            if gate.key == "has_dlc" and gate.value and gate.op == "=":
                                dlcs[gate.value.strip('"')] = True
                            elif gate.key == "NOT" and len(gate.children) == 1:
                                child = gate.children[0]
                                if (
                                    child.key == "has_dlc"
                                    and child.value
                                    and child.op == "="
                                ):
                                    dlcs[child.value.strip('"')] = False
                        self.tech_dlcs[tech.key] = dlcs
        callers = {event: [] for event in definitions}
        for event in self.unknown_events & callers.keys():
            callers[event].append(frozenset({None}))
        definition_ids = {id(node) for node in definitions.values()}

        def visit(nodes, current=frozenset({None}), root=frozenset({None})):
            for node in nodes:
                if node.key in {
                    "trigger",
                    "available",
                    "allowed",
                    "visible",
                    "limit",
                    "country",
                    "ai_will_do",
                    "ai_chance",
                    "effect_tooltip",
                    "custom_effect_tooltip",
                }:
                    continue
                if node.key == "random_list":
                    for outcome in node.children:
                        visit(outcome.children, current, root)
                    continue
                selected = scope_country(node.key, current, root)
                if id(node) in definition_ids:
                    trigger = _first_child(node, "trigger")
                    tags = countries(trigger.children) if trigger else None
                    selected = (
                        frozenset(tags) if tags is not None else value(node, "id")
                    )
                    visit(node.children, selected, selected)
                    continue
                if node.key == "focus_tree":
                    selected = frozenset(focus_countries(node) or {None})
                elif node.key in self.categories:
                    selected = frozenset(self.categories[node.key] or {None})
                allowed = _first_child(node, "allowed")
                tags = countries(allowed.children) if allowed else None
                if tags is not None:
                    selected = frozenset(tags)
                if node.key in {"country_event", "news_event"}:
                    target = node.value.strip('"') if node.value else value(node, "id")
                    if target in callers:
                        callers[target].append(selected)
                    continue
                if node.value and node.value.strip('"') in callers and node.key != "id":
                    callers[node.value.strip('"')].append(frozenset({None}))
                if node.key in callers and node.value is None:
                    callers[node.key].append(frozenset({None}))
                visit(
                    node.children,
                    selected,
                    selected if node.key == "focus_tree" else root,
                )

        for nodes in self.documents.values():
            visit(nodes)
        resolved = {event: set() for event in callers}
        for event, node in definitions.items():
            trigger = _first_child(node, "trigger")
            tags = countries(trigger.children) if trigger else None
            if tags is not None:
                callers[event] = [frozenset(tags)]
            elif value(node, "is_triggered_only") != "yes" or not callers[event]:
                callers[event].append(frozenset({None}))
        for fill_unknown in (False, True):
            if fill_unknown:
                for tags in resolved.values():
                    if not tags:
                        tags.add(None)
            changed = True
            while changed:
                changed = False
                for event, sources in callers.items():
                    for source in sources:
                        tags = (
                            resolved.get(source, {None})
                            if isinstance(source, str)
                            else source
                        )
                        if not tags <= resolved[event]:
                            resolved[event].update(tags)
                            changed = True
        self.event_countries = resolved
