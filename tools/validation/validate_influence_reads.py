"""Advisory country bindings for MD's foreign-influence trigger reads."""

import json
import os
import re
import sys
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, replace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from equipment_variant_context import event_pool_targets, script_nodes, value
from guard_scan import read_file
from shared_utils import atomic_write_text
from validator_common import BaseValidator, run_validator_main

CONTRACTS = {
    name: ("ROOT", "THIS")
    for name in (
        "is_influencer",
        "is_top3_influencer",
        "is_top3_twenty_influencer",
        "is_top3_thirty_influencer",
        "is_top_twenty_influencer",
        "is_top_fifty_influencer",
        "is_top_eighty_influencer",
        "is_top5_influencer",
        *(
            f"influence_higher_{n}"
            for n in (5, 10, 15, 20, 25, 30, 35, 40, 50, 60, 70, 75, 80, 90)
        ),
    )
}
CONTRACTS.update(
    {
        name: ("FROM", "THIS")
        for name in (
            "sender_is_influencer",
            "sender_is_top5_influencer",
            "sender_is_top_eighty_influencer",
            "FROM_is_top3_influencer",
            *(
                f"sender_influence_higher_{n}"
                for n in (5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 90)
            ),
        )
    }
)
CONTRACTS.update(
    {
        name: ("PREV", "THIS")
        for name in (
            "prev_is_top3_influencer",
            "coup_is_available",
            "target_other_influence_available",
            "manipulate_politics_action_available",
            "make_puppet_action_available",
            "economic_exploitation_available",
            "economic_aid_available",
        )
    }
)
CONTRACTS.update(
    {f"influence_less_{n}": ("THIS", "ROOT") for n in (5, 10, 20, 30, 40, 60, 70)}
)
CONTRACTS.update(
    {
        name: ("HOL", "THIS")
        for name in ("HOL_is_top3_influencer", "HOL_is_top5_influencer")
    }
)

_TAG = re.compile(r"[A-Z][A-Z0-9]{2}")
_NEUTRAL = frozenset(
    {
        "AND",
        "OR",
        "NOT",
        "if",
        "else_if",
        "else",
        "limit",
        "trigger",
        "available",
        "allowed",
        "visible",
        "bypass",
        "joint_trigger",
        "possible",
        "happened",
        "hidden_trigger",
        "custom_trigger_tooltip",
        "custom_override_tooltip",
        "hidden_effect",
        "effect",
        "completion_reward",
        "completion_reward_joint_originator",
        "completion_reward_joint_member",
        "immediate",
        "after",
        "option",
        "ai_chance",
        "ai_will_do",
        "modifier",
        "mean_time_to_happen",
        "complete_effect",
        "remove_effect",
        "cancel_effect",
        "timeout_effect",
        "select_effect",
        "ai_desire",
        "random",
        "for_each_loop",
        "for_loop_effect",
        "while_loop_effect",
        "any_of",
        "all_of",
        "desc",
        "title",
    }
)
_SKIP = frozenset(
    {"meta_effect", "meta_trigger", "effect_tooltip", "custom_effect_tooltip"}
)
_CONDITION_LISTS = frozenset(
    {
        "AND",
        "limit",
        "trigger",
        "available",
        "allowed",
        "visible",
        "bypass",
        "possible",
        "happened",
        "joint_trigger",
        "hidden_trigger",
        "custom_trigger_tooltip",
        "modifier",
    }
)
_PATTERNS = ["common/**/*.txt", "events/**/*.txt", "history/countries/*.txt"]
_CONTEXT_LIMIT = 64


@dataclass(frozen=True)
class Scope:
    root: str | None = None
    current: str | None = None
    previous: tuple = ()
    senders: tuple = ()

    def resolve(self, token):
        token = token.removesuffix(".id")
        if _TAG.fullmatch(token):
            return token
        if token == "ROOT":
            return self.root
        if token == "THIS":
            return self.current
        for prefix, chain in (("PREV", self.previous), ("FROM", self.senders)):
            parts = token.split(".") if "." in token else re.findall(prefix, token)
            if (
                parts
                and all(part == prefix for part in parts)
                and "".join(parts) == token.replace(".", "")
            ):
                return chain[len(parts) - 1] if len(parts) <= len(chain) else None
        return None

    def enter(self, country, depth):
        return replace(
            self, current=country, previous=(self.current, *self.previous)[:depth]
        )

    def constrain(self, nodes):
        tags = {
            node.value
            for node in nodes
            if node.key == "tag"
            and node.op == "="
            and node.value
            and _TAG.fullmatch(node.value)
        }
        if not tags:
            return self
        if len(tags) != 1:
            return None
        tag = next(iter(tags))
        if self.current and _TAG.fullmatch(self.current) and self.current != tag:
            return None
        old = self.current
        return Scope(
            tag if old is not None and self.root == old else self.root,
            tag,
            tuple(
                tag if old is not None and item == old else item
                for item in self.previous
            ),
            tuple(
                tag if old is not None and item == old else item
                for item in self.senders
            ),
        )


@dataclass(frozen=True, order=True)
class Read:
    file: str
    line: int
    trigger: str
    influencer: str
    target: str
    status: str
    caller: str

    def message(self):
        pair = f"{self.trigger}: influencer={self.influencer}; target={self.target}"
        if self.status == "self":
            detail = "foreign-influence self-comparison; review the caller's scope"
        elif self.status == "unresolved":
            detail = "binding unresolved; review candidate, not proof of an unset sender or a gameplay defect"
        else:
            detail = "resolved binding; diplomatic intent is not inferred"
        return f"{pair}; {detail}; caller={self.caller}"


def _nodes(nodes):
    for node in nodes:
        yield node
        if node.key not in _SKIP:
            yield from _nodes(node.children)


def _root(path, node):
    identity = value(node, "id") or node.key
    origins = {
        child.value
        for block in node.children
        if block.key in {"possible", "available", "allowed", "trigger"}
        for child in block.children
        if child.key == "original_tag" and child.op == "=" and child.value
    }
    hint = f"; original_tag={next(iter(origins))}" if len(origins) == 1 else ""
    return f"ROOT[{identity}{hint}]@{path}:{node.line}"


class Reader:
    def __init__(self, documents):
        self.documents = documents
        self.definitions = {}
        self.events = {}
        self.relevant = set(CONTRACTS)
        self.queue = deque()
        self.seen = defaultdict(set)
        self.reads = set()
        self.depth = 1
        self._index()

    def _index(self):
        for path, nodes in self.documents.items():
            for node in nodes:
                if (
                    path.startswith(
                        ("common/scripted_triggers/", "common/scripted_effects/")
                    )
                    and node.key not in CONTRACTS
                ):
                    self.definitions[node.key] = (path, node)
                elif path.startswith("events/") and node.key in {
                    "country_event",
                    "news_event",
                }:
                    event = value(node, "id")
                    if event:
                        self.events[event] = "event:" + event
                        self.definitions["event:" + event] = (path, node)
            for node in _nodes(nodes):
                for prefix in ("PREV", "FROM"):
                    if node.key.replace(".", "").replace(prefix, "") == "":
                        self.depth = max(
                            self.depth, len(node.key.replace(".", "")) // len(prefix)
                        )
        changed = True
        while changed:
            changed = False
            for name, (_, definition) in self.definitions.items():
                if name in self.relevant:
                    continue
                for node in _nodes(definition.children):
                    event = node.value if node.value else value(node, "id")
                    if (
                        node.key in self.relevant
                        or self.events.get(event) in self.relevant
                    ):
                        self.relevant.add(name)
                        changed = True
                        break

    def _enqueue(self, name, scope, caller):
        if name not in self.relevant:
            return
        contexts = self.seen[name]
        if scope in contexts:
            return
        if len(contexts) >= _CONTEXT_LIMIT:
            scope = Scope()
            caller = "context limit reached; caller unresolved"
            if scope in contexts:
                return
        contexts.add(scope)
        self.queue.append((name, scope, caller))

    def _event(self, event, scope, caller):
        name = self.events.get(event)
        if name not in self.relevant:
            return
        path, node = self.definitions[name]
        recipient = scope.current or _root(path, node)
        self._enqueue(
            name,
            Scope(recipient, recipient, (), (scope.root, *scope.senders)[: self.depth]),
            caller,
        )
        if value(node, "major") == "yes":
            audience = _root(path, node)
            self._enqueue(
                name,
                Scope(
                    audience, audience, (), (scope.root, *scope.senders)[: self.depth]
                ),
                caller + " (broadcast audience)",
            )

    def _walk(self, path, nodes, scope, caller, preview=False):
        for node in nodes:
            if node.key in _SKIP:
                continue
            if node.key in CONTRACTS and node.value in {"yes", "no"}:
                influencer, target = (
                    scope.resolve(token) for token in CONTRACTS[node.key]
                )
                status = (
                    "unresolved"
                    if influencer is None or target is None
                    else "self" if influencer == target else "resolved"
                )
                self.reads.add(
                    Read(
                        path,
                        node.line,
                        node.key,
                        influencer or "unknown",
                        target or "unknown",
                        status,
                        caller,
                    )
                )
                continue
            if node.key in self.definitions and node.value in {"yes", "no"}:
                self._enqueue(node.key, scope, f"{path}:{node.line}")
                continue
            if node.key in {"country_event", "news_event"}:
                if not preview:
                    self._event(
                        node.value or value(node, "id"), scope, f"{path}:{node.line}"
                    )
                continue
            if node.value in self.events and node.key not in {
                "id",
                "title",
                "desc",
                "name",
                "tooltip",
            }:
                self._event(
                    node.value, Scope(), f"{path}:{node.line} (unsupported dispatch)"
                )
            if not node.children:
                continue
            if node.key == "random_list":
                for outcome in node.children:
                    self._walk(path, outcome.children, scope, caller, preview)
                continue
            if node.key in _NEUTRAL:
                child_scope = (
                    scope.constrain(node.children)
                    if node.key in _CONDITION_LISTS
                    else scope
                )
            elif (
                node.key in {"ROOT", "THIS"}
                or node.key.startswith(("PREV", "FROM"))
                or _TAG.fullmatch(node.key)
            ):
                child_scope = scope.enter(scope.resolve(node.key), self.depth)
            elif (
                node.key.endswith("_country")
                or node.key == "any_country_with_original_tag"
                or node.key in {"owner", "controller", "overlord", "faction_leader"}
            ):
                country = f"country[{node.key}]@{path}:{node.line}"
                # Repeating a selector need not select the same country.
                if country in (
                    scope.root,
                    scope.current,
                    *scope.previous,
                    *scope.senders,
                ):
                    country = None
                child_scope = scope.enter(country, self.depth)
            else:
                # An unmodeled block may change scope; inheriting THIS would invent a binding.
                child_scope = replace(scope, current=None, previous=())
            if child_scope is not None:
                self._walk(
                    path,
                    node.children,
                    child_scope,
                    caller,
                    preview or node.key in _CONDITION_LISTS,
                )

    def _entry(self, path, node, country=True):
        root = _root(path, node) if country else None
        self._walk(path, node.children, Scope(root, root), f"{path}:{node.line}")

    def scan(self):
        for path, nodes in self.documents.items():
            if path.startswith(
                ("common/scripted_triggers/", "common/scripted_effects/", "events/")
            ):
                continue
            if path.startswith("common/national_focus/"):
                for node in nodes:
                    focuses = node.children if node.key == "focus_tree" else [node]
                    for focus in focuses:
                        if focus.key in {"focus", "shared_focus", "joint_focus"}:
                            self._entry(path, focus)
            elif path.startswith("common/achievements/"):
                for node in nodes:
                    self._entry(path, node)
            elif path.startswith("common/decisions/"):
                for category in nodes:
                    for decision in category.children:
                        if decision.children:
                            targeted = any(
                                child.key
                                in {
                                    "target_array",
                                    "targets",
                                    "target_trigger",
                                    "target_root_trigger",
                                }
                                for child in decision.children
                            )
                            self._entry(path, decision, not targeted)
            elif path.startswith("history/countries/"):
                match = re.match(
                    r"([A-Z][A-Z0-9]{2})(?:\s|\.)", path.rsplit("/", 1)[-1]
                )
                country = match[1] if match else None
                self._walk(path, nodes, Scope(country, country), path)
            else:
                self._walk(path, nodes, Scope(), path + " (caller unresolved)")
        for event, name in self.events.items():
            path, node = self.definitions[name]
            if value(node, "is_triggered_only") != "yes":
                self._event(
                    event,
                    Scope(),
                    f"{path}:{node.line} (automatic or unresolved caller)",
                )
        self._drain()
        for name in sorted(self.relevant & self.definitions.keys()):
            if not self.seen[name]:
                path, node = self.definitions[name]
                root = _root(path, node) if name.startswith("event:") else None
                self._enqueue(
                    name, Scope(root, root), f"{path}:{node.line} (caller unresolved)"
                )
        self._drain()
        return sorted(self.reads)

    def _drain(self):
        while self.queue:
            name, scope, caller = self.queue.popleft()
            path, node = self.definitions[name]
            if name.startswith("event:"):
                trigger = next(
                    (child for child in node.children if child.key == "trigger"), None
                )
                scope = scope.constrain(trigger.children) if trigger else scope
            if scope is not None:
                self._walk(path, node.children, scope, caller)


class Validator(BaseValidator):
    TITLE = "INFLUENCE TRIGGER READ VALIDATION"

    def validate_influence_reads(self):
        self._log_section("Foreign-influence trigger bindings (advisory)")
        files = self._collect_files(_PATTERNS, ignore_staged=True)
        documents = {}
        pools = set()
        for path in sorted(files):
            text = read_file(path)
            relative = os.path.relpath(path, self.mod_path).replace(os.sep, "/")
            documents[relative] = script_nodes(text)
            pools.update(event_pool_targets(text))
        reader = Reader(documents)
        for event in sorted(pools):
            reader._event(event, Scope(), "event pool (caller unresolved)")
        selected = None
        if self.staged_only:
            selected = {
                os.path.relpath(path, self.mod_path).replace(os.sep, "/")
                for path in self._collect_files(_PATTERNS)
            }
        self.bindings = [
            row for row in reader.scan() if selected is None or row.file in selected
        ]
        for row in self.bindings:
            if row.status != "resolved":
                category = (
                    "influence-read-self"
                    if row.status == "self"
                    else "influence-read-unresolved"
                )
                self.add_warning(category, row.message(), row.file, row.line)
            self.log(f"  {row.file}:{row.line} - {row.message()}")
        self.log(
            f"Reviewed {len(self.bindings)} influence-read binding(s); resolved pairs are not defect findings"
        )

    def run_validations(self):
        self.validate_influence_reads()

    def save_output(self):
        super().save_output()
        if self.output_file:
            path = os.path.splitext(self.output_file)[0] + ".bindings.jsonl"
            atomic_write_text(
                path,
                "".join(
                    json.dumps(asdict(row), sort_keys=True) + "\n"
                    for row in getattr(self, "bindings", [])
                ),
            )


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Review country bindings in foreign-influence trigger reads (advisory)",
    )
