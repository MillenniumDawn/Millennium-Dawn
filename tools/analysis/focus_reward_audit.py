#!/usr/bin/env python3
"""Audit what one country's focuses hand out: per focus, per branch, and stacked.

    python tools/analysis/focus_reward_audit.py --tag BRA
    python tools/analysis/focus_reward_audit.py --tag BRA --forks --focuses --top 20
    python tools/analysis/focus_reward_audit.py --tag BRA --paths --stack-limit 0.3
    python tools/analysis/focus_reward_audit.py --tag BRA --json
    python tools/analysis/focus_reward_audit.py --tag BRA --file path/to/tree.txt

A tag's focuses are every `focus`, `shared_focus` and `joint_focus` block whose id
starts with `TAG_`, in `common/national_focus/*.txt` (or in the `--file` paths).
Per focus, from `completion_reward`:

    buildings    `add_building_construction` and `add_offsite_building`, plus the
                 standard building effects of `00_scripted_effects.txt` (name,
                 building types and counts, and price are read from that file).
    money        constant `treasury_change` values committed by
                 `modify_treasury_effect`, plus standard building prices. A formula
                 is listed as unquantified, not counted as 0.
    pp, stability, war support    `add_political_power` and friends.
    spirits      permanent, timed (`add_timed_idea` or `days`), removed, swapped.
    variables    `add_to_variable` on a variable that a `common/dynamic_modifiers`
                 modifier reads, so its amount lands on that modifier key.
    days         `cost` (10 when absent) times 7.

Prerequisites give the graph. A branch is a root focus (no prerequisite) and every
focus below it. `mutually_exclusive` partners form forks, and a branch total is a
min..max range over the valid paths, so alternatives are never summed. `--forks`
lists what every alternative of a fork leads to. Stacking sums the numeric
`modifier` values of the permanent spirits a branch can grant, plus dynamic modifier
variable adds, and flags a factor-style key (`_factor`, `_multiplier`, `_modifier`)
whose best path passes `--stack-limit`. A spirit that a focus on the path removes
does not count, and one that several focuses on it grant counts once.

Path choices. Two kinds of `available` gate also split a branch, and totals and
stacking count only paths that can happen:

    path flag    A flag that a focus sets unconditionally (`set_global_flag`,
                 `set_country_flag`) on an exclusive arm, meaning the focus or an
                 ancestor has a `mutually_exclusive` partner, and that another
                 focus gates with `has_global_flag` or `has_country_flag`. A focus
                 that needs it (alone, in `AND`, or in an `OR` of such tests) waits
                 for a setter. A focus under `NOT = { has_..._flag = F }` is off
                 the table once a setter of F is.
    leader       Each name in `has_country_leader = { name = X }` that a branch
                 needs. A path has one leader, so the branch is totaled per leader
                 and the best (or lowest) wins.

`--paths` lists them and `--json` has them under `paths`. A stacking row names the
choice behind its sum.

What this misses or approximates:

    - Reward totals are unconditional. An `if` chain, a `random` block or a
      `random_list` contributes its richest branch to a separate conditional total,
      an upper bound shown by `--focuses` and kept out of branch totals. Stacking
      does include it.
    - Scripted effects other than the standard building ones are expanded only when
      named `TAG_...`. Any other effect is invisible, as is every `bypass` and
      `ai_will_do` block. An `available` counts only for the path choices above.
    - A flag with no focus setter, or set only outside an exclusive arm, gates
      nothing: an event, decision or on_action may set it, so it proves no path. That
      covers the game-rule AI path flags (`TAG_*_FOCUS_PATH`, read in `ai_will_do`)
      and flags that an event option sets. `clr_*_flag` is ignored. A path flag that
      an event also sets would wrongly gate its focuses.
    - A gate counts only when every test in the `OR` is a flag or leader test, and a
      `NOT` only around a single test. A set of flags mixed with leaders in one `OR`
      is not read.
    - Leaders do not change over time in this model, so a branch that hands from one
      leader to the next is totaled as if the player had only one of them.
    - `NOT` ignores order: in game a focus can be taken before the setter it forbids,
      and a setter below the fork focus is optional. Here the focus is off the table
      whenever a setter on the path can be taken, so it never shares a path with one.
    - Forks resolve one at a time, so a fork whose arms differ by flag or leader
      gate is judged before the choice it depends on, and may miss the best path.
    - Blocks that switch to another country (`every_other_country`, another tag's
      block, ...) are skipped. `PREV`, `FROM` and variable scopes are not resolved.
    - An `every_*` loop, `for_each_loop`, `for_each_scope_loop` or `while_loop_effect`
      counts its effects once, and says so.
    - `mutually_exclusive` is read as symmetric. Partners joined only through a third
      focus are treated as one fork. A fork's alternatives include nested forks.
    - A prerequisite that names a focus outside the audited set is ignored. A focus
      under two roots counts in both branches.
    - Stacking reads `modifier` blocks only, not `research_bonus`, and ignores
      `validation_config.json` caps.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter, defaultdict
from collections.abc import Callable, Collection, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import NamedTuple

REPO_ROOT = Path(__file__).resolve().parents[2]

STANDARD_EFFECTS_FILE = "00_scripted_effects.txt"
DEFAULT_COST = 10.0
DAYS_PER_COST = 7
SPIRIT_MODIFIER_LIMIT = 5
FACTOR_SUFFIXES = ("_factor", "_multiplier", "_modifier")
FOCUS_BLOCKS = {"focus", "shared_focus", "joint_focus"}

# Blocks that only describe an effect for the tooltip, never run it.
SILENT = frozenset(
    {
        "limit",
        "log",
        "custom_effect_tooltip",
        "effect_tooltip",
        "tooltip",
        "custom_trigger_tooltip",
    }
)
SIMPLE_AMOUNTS = {
    "add_political_power": "pp",
    "add_stability": "stability",
    "add_war_support": "war_support",
}
# Loops whose repeat count is not read, so their body counts once.
LOOP_EFFECTS = frozenset({"for_each_loop", "for_each_scope_loop", "while_loop_effect"})
FLAG_SETS = {"set_global_flag": "global flag", "set_country_flag": "country flag"}
FLAG_TESTS = {"has_global_flag": "global flag", "has_country_flag": "country flag"}
# Blocks of an `available` whose conditions all still apply.
TRIGGER_WRAPPERS = frozenset({"AND", "custom_trigger_tooltip", "hidden_trigger"})
LEADER = "leader "
TEMP_OPS = frozenset(
    {
        "set_temp_variable",
        "add_to_temp_variable",
        "subtract_from_temp_variable",
        "multiply_temp_variable",
        "divide_temp_variable",
        "modulo_temp_variable",
        "round_temp_variable",
        "clamp_temp_variable",
    }
)
# Keys of a dynamic modifier whose value is not a variable.
DYNAMIC_META_KEYS = frozenset({"icon", "custom_modifier_tooltip"})

_TOKEN_RE = re.compile(r'"[^"\n]*"|#[^\n]*|<=|>=|!=|[{}=<>]|[^\s{}=<>"#]+')
_OPERATORS = frozenset({"=", "<", ">", "<=", ">=", "!="})
_TAG_RE = re.compile(r"[A-Z][A-Z0-9]{2}")
_WORD_RE = re.compile(r"[\w.@:-]+")


# --- parsing ---------------------------------------------------------------


class Node(NamedTuple):
    """One `key op value` entry, a bare token (op None), or a `key = { ... }` block."""

    key: str
    op: str | None
    value: str | list[Node] | None
    line: int


def tokenize(text: str) -> list[tuple[str, int]]:
    """Tokens with line numbers. A string is one token and a comment is dropped, so
    braces inside either never reach the block matching."""
    tokens = []
    line, pos = 1, 0
    for match in _TOKEN_RE.finditer(text):
        line += text.count("\n", pos, match.start())
        pos = match.start()
        if match.group()[0] != "#":
            tokens.append((match.group(), line))
    return tokens


def _parse_block(tokens: list[tuple[str, int]], i: int) -> tuple[list[Node], int]:
    nodes: list[Node] = []
    count = len(tokens)
    while i < count:
        token, line = tokens[i]
        if token == "}":
            return nodes, i + 1
        if token == "{":
            block, i = _parse_block(tokens, i + 1)
            nodes.append(Node("", None, block, line))
        elif i + 1 < count and tokens[i + 1][0] in _OPERATORS:
            operator = tokens[i + 1][0]
            if i + 2 < count and tokens[i + 2][0] == "{":
                block, i = _parse_block(tokens, i + 3)
                nodes.append(Node(token, operator, block, line))
            elif i + 2 < count and tokens[i + 2][0] != "}":
                nodes.append(Node(token, operator, tokens[i + 2][0], line))
                i += 3
            else:
                i += 2
        else:
            nodes.append(Node(token, None, None, line))
            i += 1
    return nodes, i


def parse(text: str) -> list[Node]:
    tokens = tokenize(text)
    nodes: list[Node] = []
    i = 0
    while i < len(tokens):  # a stray `}` ends a block early, so resume after it
        block, i = _parse_block(tokens, i)
        nodes += block
    return nodes


def child(nodes: Sequence[Node], key: str) -> str | list[Node] | None:
    """Value of the first entry named key."""
    return next((node.value for node in nodes if node.key == key), None)


def number(value: object) -> float | None:
    if not isinstance(value, str):
        return None
    try:
        result = float(value)
    except ValueError:
        return None
    return result if math.isfinite(result) else None


def show(value: str | list[Node] | None) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    entries = (
        node.key if node.op is None else f"{node.key} {node.op} {show(node.value)}"
        for node in value
    )
    return "{ " + " ".join(entries) + " }"


def idea_names(value: str | list[Node] | None) -> list[str]:
    if isinstance(value, str):
        return [value]
    return [node.key for node in value or () if node.op is None]


def group_chains(nodes: Sequence[Node]) -> Iterator[Node | list[list[Node]]]:
    """The nodes, with each `if` / `else_if` / `else` chain as a list of its blocks."""
    i = 0
    while i < len(nodes):
        node = nodes[i]
        if node.key in ("if", "else_if", "else") and isinstance(node.value, list):
            blocks = [node.value]
            i += 1
            while (
                i < len(nodes)
                and nodes[i].key in ("else_if", "else")
                and isinstance(nodes[i].value, list)
            ):
                blocks.append(nodes[i].value)
                i += 1
            yield blocks
        else:
            yield node
            i += 1


def walk_nodes(nodes: Sequence[Node]) -> Iterator[Node]:
    for node in nodes:
        yield node
        if isinstance(node.value, list):
            yield from walk_nodes(node.value)


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as error:
        raise UnicodeError(f"{path}: {error}") from error


# --- standard building effects ----------------------------------------------


class StandardEffect(NamedTuple):
    buildings: dict[str, float]
    price: float


def count_buildings(nodes: Sequence[Node], multiplier: float = 1.0) -> Counter[str]:
    """Levels one call of an effect body builds.

    An if/else chain counts its richest branch, and a loop that selects N states
    counts N times.
    """
    total: Counter[str] = Counter()
    for item in group_chains(nodes):
        if isinstance(item, list):
            total.update(
                max(
                    (count_buildings(block, multiplier) for block in item),
                    key=lambda counts: sum(counts.values()),
                )
            )
        elif item.key != "limit" and isinstance(item.value, list):
            if item.key == "add_building_construction":
                kind = child(item.value, "type")
                level = number(child(item.value, "level"))
                if isinstance(kind, str):
                    total[kind] += multiplier * (1.0 if level is None else level)
            else:
                selected = number(child(item.value, "random_select_amount"))
                total.update(count_buildings(item.value, multiplier * (selected or 1)))
    return total


def standard_price(nodes: Sequence[Node]) -> float:
    """The first constant `treasury_change` an effect body sets."""
    for node in walk_nodes(nodes):
        if node.key == "set_temp_variable" and isinstance(node.value, list):
            price = number(child(node.value, "treasury_change"))
            if price is not None:
                return price
    return 0.0


def standard_effects(nodes: Sequence[Node]) -> dict[str, StandardEffect]:
    table = {}
    for node in nodes:
        if isinstance(node.value, list):
            buildings = count_buildings(node.value)
            if buildings:
                table[node.key] = StandardEffect(
                    dict(buildings), standard_price(node.value)
                )
    return table


# --- context: effects, dynamic modifier variables, ideas ---------------------


@dataclass
class Context:
    tag: str
    standard: dict[str, StandardEffect]
    tag_effects: dict[str, list[Node]]
    variables: dict[str, list[str]]  # variable -> modifier keys that read it


def load_context(root: Path, tag: str) -> Context:
    standard: dict[str, StandardEffect] = {}
    tag_effects: dict[str, list[Node]] = {}
    for path in sorted((root / "common" / "scripted_effects").glob("*.txt")):
        text = read(path)
        is_standard = path.name == STANDARD_EFFECTS_FILE
        if not is_standard and f"{tag}_" not in text:
            continue
        nodes = parse(text)
        if is_standard:
            standard = standard_effects(nodes)
        for node in nodes:
            if isinstance(node.value, list) and node.key.startswith(f"{tag}_"):
                tag_effects[node.key] = node.value
    if not standard:
        print(
            f"warning: no standard building effects found in "
            f"common/scripted_effects/{STANDARD_EFFECTS_FILE} under {root}",
            file=sys.stderr,
        )
    return Context(tag, standard, tag_effects, dynamic_variables(root))


def dynamic_variables(root: Path) -> dict[str, list[str]]:
    variables: dict[str, list[str]] = defaultdict(list)
    for path in sorted((root / "common" / "dynamic_modifiers").glob("*.txt")):
        for modifier in parse(read(path)):
            entries = modifier.value if isinstance(modifier.value, list) else []
            for entry in entries:
                value = entry.value
                if (
                    isinstance(value, str)
                    and entry.key not in DYNAMIC_META_KEYS
                    and number(value) is None
                    and value not in ("yes", "no")
                    and not value.startswith('"')
                    and entry.key not in variables[value]
                ):
                    variables[value].append(entry.key)
    return dict(variables)


class Idea(NamedTuple):
    modifiers: dict[str, float]  # numeric `modifier` entries
    count: int  # every entry of the `modifier` block


def load_ideas(root: Path, names: set[str]) -> dict[str, Idea]:
    """The named ideas, parsing only the idea files that mention one of them."""
    found: dict[str, Idea] = {}
    for path in sorted((root / "common" / "ideas").glob("*.txt")):
        text = read(path)
        if not names & set(_WORD_RE.findall(text)):
            continue
        for idea in idea_definitions(parse(text)):
            if idea.key in names and isinstance(idea.value, list):
                block = child(idea.value, "modifier")
                entries = block if isinstance(block, list) else []
                found[idea.key] = Idea(
                    {
                        entry.key: amount
                        for entry in entries
                        if (amount := number(entry.value)) is not None
                    },
                    len(entries),
                )
    return found


def idea_definitions(nodes: Sequence[Node]) -> Iterator[Node]:
    """Each idea of `ideas = { category = { idea = { ... } } }`."""
    for top in nodes:
        if top.key == "ideas" and isinstance(top.value, list):
            for category in top.value:
                if isinstance(category.value, list):
                    yield from category.value


# --- rewards ------------------------------------------------------------------


@dataclass
class Reward:
    buildings: Counter[str] = field(default_factory=Counter)
    money: float = 0.0
    pp: float = 0.0
    stability: float = 0.0
    war_support: float = 0.0
    permanent: list[str] = field(default_factory=list)
    timed: list[tuple[str, float | None]] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    swaps: list[tuple[str, str]] = field(default_factory=list)
    variables: Counter[str] = field(default_factory=Counter)
    unquantified: list[str] = field(default_factory=list)
    flags: set[str] = field(default_factory=set)  # "global flag X", "country flag X"

    def weight(self) -> float:
        """Rough size, only to pick the richest branch of a chain or random_list."""
        spirits = len(self.permanent) + len(self.timed) + len(self.removed)
        return (
            sum(self.buildings.values())
            + abs(self.money) / 10
            + abs(self.pp) / 10
            + 3 * spirits
            + len(self.variables)
        )

    def merge(self, other: Reward) -> None:
        self.buildings.update(other.buildings)
        self.variables.update(other.variables)
        self.money += other.money
        self.pp += other.pp
        self.stability += other.stability
        self.war_support += other.war_support
        self.permanent += other.permanent
        self.timed += other.timed
        self.removed += other.removed
        self.swaps += other.swaps
        self.unquantified += other.unquantified
        self.flags |= other.flags


def other_country(key: str, tag: str) -> bool:
    """Whether a scope key leaves the audited country."""
    if _TAG_RE.fullmatch(key):
        return key != tag
    return key.startswith(("every_", "random_")) and (
        "countr" in key or "faction" in key
    )


class Walk:
    """Walks one `completion_reward` and sorts what it grants into two rewards:
    `always` for unconditional effects, `maybe` for those in an if chain or a
    random_list."""

    def __init__(
        self, ctx: Context, stack: tuple[str, ...] = (), skip_payment: bool = False
    ) -> None:
        self.ctx = ctx
        self.always = Reward()
        self.maybe = Reward()
        self.pending: float | str | None = None  # treasury_change awaiting payment
        self.skip_payment = skip_payment
        self.stack = stack  # tag effects being expanded, against cycles

    def run(self, nodes: Sequence[Node], cond: bool = False) -> None:
        for item in group_chains(nodes):
            if isinstance(item, list):
                self.richest(item)
            else:
                self.statement(item, cond)

    def richest(self, blocks: Sequence[Sequence[Node]]) -> None:
        best = None
        for block in blocks:
            sub = Walk(self.ctx, self.stack, self.skip_payment)
            sub.run(block, cond=True)
            if best is None or sub.maybe.weight() > best.weight():
                best = sub.maybe
        if best is not None:
            self.maybe.merge(best)

    def statement(self, node: Node, cond: bool) -> None:
        key, value = node.key, node.value
        target = self.maybe if cond else self.always
        if key in SILENT or not key:
            return
        if key in ("add_building_construction", "add_offsite_building"):
            if isinstance(value, list):
                prefix = "offsite_" if key == "add_offsite_building" else ""
                add_building(target, value, prefix)
        elif key in self.ctx.standard:
            effect = self.ctx.standard[key]
            target.buildings.update(effect.buildings)
            if not self.skip_payment:
                target.money += effect.price
        elif key in SIMPLE_AMOUNTS:
            amount = number(value)
            if amount is None:
                target.unquantified.append(f"{key} = {show(value)}")
            else:
                name = SIMPLE_AMOUNTS[key]
                setattr(target, name, getattr(target, name) + amount)
        elif key in ("add_ideas", "add_idea"):
            if isinstance(value, list) and child(value, "days") is not None:
                days = number(child(value, "days"))
                target.timed.append((str(child(value, "idea")), days))
            else:
                target.permanent += idea_names(value)
        elif key == "add_timed_idea" and isinstance(value, list):
            target.timed.append(
                (str(child(value, "idea")), number(child(value, "days")))
            )
        elif key == "swap_ideas" and isinstance(value, list):
            old, new = child(value, "remove_idea"), child(value, "add_idea")
            if isinstance(old, str):
                target.removed.append(old)
            if isinstance(new, str):
                target.permanent.append(new)
            if isinstance(old, str) and isinstance(new, str):
                target.swaps.append((old, new))
        elif key in ("remove_ideas", "remove_idea"):
            target.removed += idea_names(value)
        elif key in FLAG_SETS:
            if name := flag_name(value):
                target.flags.add(f"{FLAG_SETS[key]} {name}")
        elif key in ("add_to_variable", "subtract_from_variable"):
            if isinstance(value, list):
                self.add_variables(target, key, value)
        elif key in TEMP_OPS and isinstance(value, list):
            self.temp_variable(key, value, cond)
        elif key == "modify_treasury_effect":
            self.pay(target)
        elif key == "random_list" and isinstance(value, list):
            self.richest([n.value for n in value if isinstance(n.value, list)])
        elif key == "random" and isinstance(value, list):
            self.richest([value])
        elif isinstance(value, list):
            self.scope(key, value, cond, target)
        elif key in self.ctx.tag_effects and key not in self.stack:
            self.stack += (key,)
            self.run(self.ctx.tag_effects[key], cond)
            self.stack = self.stack[:-1]

    def scope(self, key: str, body: list[Node], cond: bool, target: Reward) -> None:
        if other_country(key, self.ctx.tag):
            return
        before = target.weight()
        self.run(body, cond)
        note = f"{key} loop counted once"
        if (
            (key.startswith("every_") or key in LOOP_EFFECTS)
            and target.weight() > before
            and note not in target.unquantified
        ):
            target.unquantified.append(note)

    def add_variables(self, target: Reward, key: str, entries: list[Node]) -> None:
        sign = -1.0 if key == "subtract_from_variable" else 1.0
        for entry in entries:
            if entry.key not in self.ctx.variables:
                continue
            amount = number(entry.value)
            if amount is None:
                target.unquantified.append(f"{entry.key} {show(entry.value)}")
            else:
                target.variables[entry.key] += sign * amount

    def temp_variable(self, op: str, entries: list[Node], cond: bool) -> None:
        for entry in entries:
            amount = number(entry.value)
            if entry.key == "skip_payment" and op == "set_temp_variable" and not cond:
                self.skip_payment = amount not in (None, 0.0)
            elif entry.key != "treasury_change":
                continue
            elif op == "set_temp_variable":
                self.pending = amount if amount is not None else show(entry.value)
            elif (
                op in ("add_to_temp_variable", "subtract_from_temp_variable")
                and amount is not None
                and not isinstance(self.pending, str)
            ):
                sign = 1.0 if op == "add_to_temp_variable" else -1.0
                self.pending = (self.pending or 0.0) + sign * amount
            else:
                self.pending = f"{op} {show(entry.value)}"

    def pay(self, target: Reward) -> None:
        pending, self.pending = self.pending, None
        if isinstance(pending, float):
            target.money += pending
        elif pending is not None:
            target.unquantified.append(f"money {pending}")


def add_building(target: Reward, block: list[Node], prefix: str = "") -> None:
    kind = child(block, "type")
    if not isinstance(kind, str):
        return
    level = child(block, "level")
    amount = 1.0 if level is None else number(level)
    if amount is None:
        target.unquantified.append(f"{kind} level {show(level)}")
        amount = 1.0
    target.buildings[prefix + kind] += amount


# --- focuses and the prerequisite graph -----------------------------------------


def flag_name(value: str | list[Node] | None) -> str | None:
    """The flag of `set_x_flag = NAME` or `has_x_flag = { flag = NAME ... }`."""
    name = child(value, "flag") if isinstance(value, list) else value
    return name if isinstance(name, str) else None


def gate_token(node: Node) -> str | None:
    """`global flag X`, `country flag X` or `leader NAME` for such a test, else None."""
    if node.key in FLAG_TESTS and (name := flag_name(node.value)):
        return f"{FLAG_TESTS[node.key]} {name}"
    if node.key == "has_country_leader" and isinstance(node.value, list):
        name = child(node.value, "name")
        return LEADER + name.strip('"') if isinstance(name, str) else None
    return None


def read_gates(nodes: Sequence[Node]) -> tuple[list[frozenset[str]], frozenset[str]]:
    """What an `available` demands: token sets of which one must hold, and tokens
    that must not. An `OR` with any other condition in it gates nothing, and only a
    `NOT` of one test counts."""
    needs: list[frozenset[str]] = []
    forbids: set[str] = set()
    for node in nodes:
        value = node.value
        if token := gate_token(node):
            needs.append(frozenset([token]))
        elif not isinstance(value, list):
            continue
        elif node.key in TRIGGER_WRAPPERS:
            inner_needs, inner_forbids = read_gates(value)
            needs += inner_needs
            forbids |= inner_forbids
        elif node.key == "OR":
            tokens = [gate_token(entry) for entry in value]
            if tokens and all(tokens):
                needs.append(frozenset(tokens))
        elif node.key == "NOT" and len(value) == 1 and (token := gate_token(value[0])):
            forbids.add(token)
    return needs, frozenset(forbids)


@dataclass
class Focus:
    id: str
    file: str
    line: int
    cost: float
    prerequisites: list[list[str]]
    exclusive: list[str]
    needs: list[frozenset[str]]  # `available`: one token of each set must hold
    forbids: frozenset[str]  # `available`: none of these may hold
    always: Reward
    maybe: Reward

    @property
    def days(self) -> float:
        return self.cost * DAYS_PER_COST


def focus_ids(blocks: Sequence[str | list[Node] | None]) -> list[list[str]]:
    return [
        [n.value for n in block if n.key == "focus" and isinstance(n.value, str)]
        for block in blocks
        if isinstance(block, list)
    ]


def tag_focus_blocks(nodes: Sequence[Node], tag: str) -> Iterator[Node]:
    for node in nodes:
        if not isinstance(node.value, list):
            continue
        if node.key == "focus_tree":
            yield from tag_focus_blocks(node.value, tag)
        elif node.key in FOCUS_BLOCKS:
            focus_id = child(node.value, "id")
            if isinstance(focus_id, str) and focus_id.startswith(f"{tag}_"):
                yield node


def build_focus(node: Node, file: str, ctx: Context) -> Focus:
    body = node.value if isinstance(node.value, list) else []
    cost = number(child(body, "cost"))
    walk = Walk(ctx)
    reward = child(body, "completion_reward")
    if isinstance(reward, list):
        walk.run(reward)
    prerequisites = focus_ids([n.value for n in body if n.key == "prerequisite"])
    exclusive = [
        focus
        for block in focus_ids([n.value for n in body if n.key == "mutually_exclusive"])
        for focus in block
    ]
    available = child(body, "available")
    needs, forbids = read_gates(available if isinstance(available, list) else ())
    return Focus(
        id=str(child(body, "id")),
        file=file,
        line=node.line,
        cost=DEFAULT_COST if cost is None else cost,
        prerequisites=prerequisites,
        exclusive=exclusive,
        needs=needs,
        forbids=forbids,
        always=walk.always,
        maybe=walk.maybe,
    )


def display_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def read_focuses(
    root: Path, tag: str, files: Sequence[Path], ctx: Context
) -> tuple[list[str], list[Focus]]:
    paths = list(files) or sorted((root / "common" / "national_focus").glob("*.txt"))
    used: list[str] = []
    focuses: dict[str, Focus] = {}
    for path in paths:
        text = read(path)
        if f"{tag}_" not in text:
            continue
        found = [
            build_focus(node, display_path(path, root), ctx)
            for node in tag_focus_blocks(parse(text), tag)
        ]
        if found:
            used.append(display_path(path, root))
        for focus in found:
            focuses.setdefault(focus.id, focus)
    return used, list(focuses.values())


class Branch(NamedTuple):
    root: str
    members: list[str]  # shallowest first
    inside: frozenset[str]  # the same, as a set
    forks: list[list[str]]  # deepest first
    leaders: list[tuple[str, frozenset[str]]]  # leader token, focuses it rules out


class Pick(NamedTuple):
    focuses: set[str]
    choice: list[str]  # the leader and path flags this path takes


def is_leader(token: str) -> bool:
    return token.startswith(LEADER)


class Graph:
    def __init__(self, focuses: Sequence[Focus]) -> None:
        known = {f.id for f in focuses}
        self.blocks = {
            f.id: [
                b
                for block in f.prerequisites
                if (b := [p for p in block if p in known])
            ]
            for f in focuses
        }
        self.depth: dict[str, int] = {}
        for focus in focuses:
            self._depth(focus.id, frozenset())
        order = sorted(known, key=lambda i: (self.depth[i], i))
        ancestors: dict[str, set[str]] = {}
        for fid in order:
            ancestors[fid] = set()
            for block in self.blocks[fid]:
                for parent in block:
                    ancestors[fid] |= ancestors.get(parent, set()) | {parent}
        components = self._exclusive_components(focuses, known)
        self.ancestors = ancestors
        self._read_gates(focuses, {m for comp in components for m in comp})
        self.branches = []
        self.roots_of: dict[str, list[str]] = defaultdict(list)
        for root in (i for i in order if not self.blocks[i]):
            members = [i for i in order if i == root or root in ancestors[i]]
            inside = frozenset(members)
            for member in members:
                self.roots_of[member].append(root)
            forks = [
                alternatives
                for comp in components
                if len(alternatives := [m for m in comp if m in inside]) > 1
            ]
            forks.sort(key=lambda c: (-min(self.depth[m] for m in c), c[0]))
            self.branches.append(
                Branch(root, members, inside, forks, self._leaders(members))
            )

    def _read_gates(self, focuses: Sequence[Focus], forked: set[str]) -> None:
        """Sort the `available` gates into leader choices and path flags.

        A path flag is set by a focus on an exclusive arm (the focus or an ancestor
        has a `mutually_exclusive` partner) and gates a focus. Only path flags are
        enforced: a flag nothing in the audited set sets, or that every path sets,
        may be set elsewhere, so it is no proof of a path.
        """
        self.setters: dict[str, list[str]] = defaultdict(list)
        self.gates: dict[str, list[str]] = defaultdict(list)
        for focus in focuses:
            for token in sorted(focus.always.flags):
                self.setters[token].append(focus.id)
            for token in sorted({t for b in focus.needs for t in b} | focus.forbids):
                self.gates[token].append(focus.id)
        self.path_flags = {
            token: setters
            for token, setters in sorted(self.setters.items())
            if token in self.gates
            and any(({s} | self.ancestors[s]) & forked for s in setters)
        }
        self.flag_needs = {
            f.id: [
                block
                for block in f.needs
                if all(t in self.path_flags for t in block)
                and not block & f.always.flags  # it would need its own flag
            ]
            for f in focuses
        }
        self.flag_forbids = {
            f.id: [t for t in f.forbids if t in self.path_flags] for f in focuses
        }
        self.leader_needs = {
            f.id: [b for b in f.needs if all(is_leader(t) for t in b)] for f in focuses
        }
        self.leader_forbids = {
            f.id: {t for t in f.forbids if is_leader(t)} for f in focuses
        }
        self.gated = any(self.flag_needs.values())
        self.forbidders = [f for f, tokens in self.flag_forbids.items() if tokens]

    def _leaders(self, members: Sequence[str]) -> list[tuple[str, frozenset[str]]]:
        """One choice per leader a focus of the branch needs, each with the focuses
        that leader rules out. A path has one leader, so a lone name is no choice."""
        names = sorted({t for m in members for b in self.leader_needs[m] for t in b})
        if len(names) < 2:
            return []
        return [
            (
                name,
                frozenset(
                    m
                    for m in members
                    if name in self.leader_forbids[m]
                    or any(name not in block for block in self.leader_needs[m])
                ),
            )
            for name in names
        ]

    def _depth(self, fid: str, trail: frozenset[str]) -> int:
        if fid in self.depth:
            return self.depth[fid]
        if fid in trail:
            return 0
        parents = [p for block in self.blocks[fid] for p in block]
        depth = 1 + max((self._depth(p, trail | {fid}) for p in parents), default=-1)
        self.depth[fid] = depth
        return depth

    @staticmethod
    def _exclusive_components(
        focuses: Sequence[Focus], known: set[str]
    ) -> list[list[str]]:
        parent = {i: i for i in known}

        def find(i: str) -> str:
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        for focus in focuses:
            for other in focus.exclusive:
                if other in known:
                    parent[find(focus.id)] = find(other)
        groups: dict[str, list[str]] = defaultdict(list)
        for fid in sorted(known):
            groups[find(fid)].append(fid)
        return [group for group in groups.values() if len(group) > 1]

    def reach(self, branch: Branch, excluded: Collection[str]) -> set[str]:
        """Focuses of the branch a player can take when `excluded` are off the table.

        A prerequisite outside the branch counts as taken, and so does a path flag
        set outside it. A focus that needs a path flag waits for one of its setters,
        and one that forbids it is off the table once a setter is.
        """
        off = set(excluded)
        while True:
            reached: set[str] = set()
            grew = True
            while grew:
                grew = False
                for fid in branch.members:
                    if fid not in reached and fid not in off:
                        if self._open(fid, branch, reached):
                            reached.add(fid)
                            grew = True
                grew = grew and self.gated  # a deeper focus may set the flag
            banned = {f for f in self.forbidders if self._forbidden(f, reached)}
            if not banned:
                return reached
            off |= banned

    def _open(self, fid: str, branch: Branch, reached: set[str]) -> bool:
        """Whether the prerequisites and path flag needs of `fid` are met."""
        return all(
            any(p in reached or p not in branch.inside for p in block)
            for block in self.blocks[fid]
        ) and all(
            any(
                s in reached or s not in branch.inside
                for token in block
                for s in self.setters[token]
            )
            for block in self.flag_needs[fid]
        )

    def _forbidden(self, fid: str, reached: set[str]) -> bool:
        """Whether `fid` is reachable beside a setter of a flag it forbids. A setter
        below `fid` comes after it, so it does not count."""
        return fid in reached and any(
            s in reached and s != fid and fid not in self.ancestors[s]
            for token in self.flag_forbids[fid]
            for s in self.setters[token]
        )

    def pick_path(
        self, branch: Branch, score: Mapping[str, float], largest: bool
    ) -> Pick:
        """The path with the highest (or lowest) total score, and what it chose.

        Each leader choice of the branch gets its best path, and the best of those
        wins.
        """
        picks = []
        for leader, ruled_out in branch.leaders or [("", frozenset())]:
            focuses = self._resolve_forks(branch, score, largest, set(ruled_out))
            flags = [t for t, s in self.path_flags.items() if focuses.intersection(s)]
            picks.append(Pick(focuses, ([leader] if leader else []) + flags))
        return (max if largest else min)(
            picks, key=lambda pick: sum(score.get(f, 0.0) for f in pick.focuses)
        )

    def _resolve_forks(
        self,
        branch: Branch,
        score: Mapping[str, float],
        largest: bool,
        excluded: set[str],
    ) -> set[str]:
        """Forks resolve deepest first, each to its best alternative given the forks
        already settled. That is exact when forks nest and scores add up."""
        for fork in branch.forks:
            reached = self.reach(branch, excluded)
            live = [m for m in fork if m in reached]
            if len(live) < 2:
                continue
            best = (max if largest else min)(
                live,
                key=lambda member: sum(
                    score.get(f, 0.0)
                    for f in self.reach(branch, excluded | (set(fork) - {member}))
                ),
            )
            excluded |= set(fork) - {best}
        return self.reach(branch, excluded)

    def path_rows(self) -> list[dict]:
        """Every path choice the audit applies: path flags, then leaders."""
        rows = [
            {
                "choice": token,
                "kind": "flag",
                "setters": setters,
                "gates": len(self.gates[token]),
                "branches": sorted({r for s in setters for r in self.roots_of[s]}),
            }
            for token, setters in self.path_flags.items()
        ]
        leaders: dict[str, list[str]] = defaultdict(list)
        for branch in self.branches:
            for token, _ in branch.leaders:
                leaders[token].append(branch.root)
        rows += [
            {
                "choice": token,
                "kind": "leader",
                "setters": [],
                "gates": len(self.gates[token]),
                "branches": roots,
            }
            for token, roots in sorted(leaders.items())
        ]
        return rows

    def alternatives(self, branch: Branch, fork: Sequence[str]) -> dict[str, set[str]]:
        """For each focus of a fork, what only taking it opens up."""
        without_fork = self.reach(branch, set(fork))
        every = self.reach(branch, set())
        return {
            member: self.reach(branch, set(fork) - {member}) - without_fork
            for member in fork
            if member in every
        }


# --- report -----------------------------------------------------------------------

METRICS: dict[str, Callable[[Focus], float]] = {
    "buildings": lambda f: sum(f.always.buildings.values()),
    "money": lambda f: f.always.money,
    "pp": lambda f: f.always.pp,
    "stability": lambda f: f.always.stability,
    "war_support": lambda f: f.always.war_support,
    "spirits": lambda f: len(f.always.permanent) - len(f.always.removed),
    "timed": lambda f: len(f.always.timed),
    "days": lambda f: f.days,
}


def is_factor(key: str) -> bool:
    return key.endswith(FACTOR_SUFFIXES)


def stacking_rows(
    graph: Graph,
    branch: Branch,
    by_id: Mapping[str, Focus],
    ideas: Mapping[str, Idea],
    ctx: Context,
    limit: float,
) -> list[dict]:
    # key -> focus -> [(source, amount, is an idea)]. Every granter of an idea is
    # listed: which one counts depends on the path.
    swapped = {
        idea
        for fid in branch.members
        for r in (by_id[fid].always, by_id[fid].maybe)
        for idea in r.removed
    }
    granters: dict[str, set[str]] = defaultdict(set)
    parts: dict[str, dict[str, list[tuple[str, float, bool]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for fid in branch.members:
        for reward in (by_id[fid].always, by_id[fid].maybe):
            for idea in reward.permanent:
                if idea in ideas:
                    granters[idea].add(fid)
                    for key, amount in ideas[idea].modifiers.items():
                        parts[key][fid].append((idea, amount, True))
            for variable, amount in reward.variables.items():
                for key in ctx.variables[variable]:
                    parts[key][fid].append((variable, amount, False))

    def tally(key: str, path: set[str]) -> tuple[float, list[tuple[str, float]]]:
        """What the path stacks: an idea applies once, and not if the path removes it."""
        skip = {
            idea
            for f in path
            for r in (by_id[f].always, by_id[f].maybe)
            for idea in r.removed
        }
        sources: list[tuple[str, float]] = []
        for fid in branch.members:
            if fid not in path:
                continue
            for source, amount, is_idea in parts[key].get(fid, ()):
                if is_idea:
                    if source in skip:
                        continue
                    skip.add(source)
                sources.append((source, amount))
        return sum(a for _, a in sources), sorted(sources, key=lambda s: -abs(s[1]))

    rows = []
    for key in sorted(parts):
        amounts = [a for entries in parts[key].values() for _, a, _ in entries]
        if not is_factor(key) or (
            sum(a for a in amounts if a > 0) <= limit
            and sum(a for a in amounts if a < 0) >= -limit
        ):
            continue
        # Judging forks: a spirit that something removes scores 0, so a swap ladder
        # counts by its last rung, and one that a prerequisite also grants scores
        # once. The tally above is exact for the path picked.
        score = {
            fid: sum(
                a
                for source, a, is_idea in entries
                if not is_idea
                or (
                    source not in swapped
                    and not graph.ancestors[fid] & granters[source]
                )
            )
            for fid, entries in parts[key].items()
        }
        results = []
        for largest in (True, False):
            pick = graph.pick_path(branch, score, largest)
            results.append((*tally(key, pick.focuses), pick.choice))
        total, sources, choice = max(results, key=lambda r: abs(r[0]))
        if abs(total) > limit:
            rows.append({"key": key, "sum": total, "from": sources, "path": choice})
    return rows


def branch_rows(
    graph: Graph,
    by_id: Mapping[str, Focus],
    ideas: Mapping[str, Idea],
    ctx: Context,
    limit: float,
) -> list[dict]:
    rows = []
    for branch in graph.branches:
        members = [by_id[m] for m in branch.members]
        metrics = {}
        for name, value in METRICS.items():
            score = {f.id: value(f) for f in members}
            bounds = [
                sum(score[i] for i in graph.pick_path(branch, score, largest).focuses)
                for largest in (False, True)
            ]
            metrics[name] = {"min": bounds[0], "max": bounds[1]}
        forks = []
        for fork in branch.forks:
            arms = graph.alternatives(branch, fork)
            if len(arms) > 1:
                forks.append(
                    [
                        {"focus": member, "focuses": len(arm), **arm_totals(arm, by_id)}
                        for member, arm in arms.items()
                    ]
                )
        rows.append(
            {
                "root": branch.root,
                "focuses": len(members),
                "metrics": metrics,
                "forks": forks,
                "stacking": stacking_rows(graph, branch, by_id, ideas, ctx, limit),
            }
        )
    return rows


def arm_totals(arm: set[str], by_id: Mapping[str, Focus]) -> dict[str, float]:
    return {
        name: sum(METRICS[name](by_id[f]) for f in arm)
        for name in ("buildings", "money", "pp", "spirits", "days")
    }


def outliers(
    focuses: Sequence[Focus], ideas: Mapping[str, Idea], top: int
) -> dict[str, list[dict]]:
    measures: dict[str, Callable[[Reward], float]] = {
        "buildings_per_day": lambda r: sum(r.buildings.values()),
        "money_per_day": lambda r: r.money,
        "pp_per_day": lambda r: r.pp,
    }
    result: dict[str, list[dict]] = {}
    for name, measure in measures.items():
        ranked = sorted(
            (f for f in focuses if measure(f.always) > 0 and f.days > 0),
            key=lambda f: (-measure(f.always) / f.days, f.id),
        )
        result[name] = []
        for f in ranked[:top]:
            row = {
                "focus": f.id,
                "value": measure(f.always),
                "days": f.days,
                "per_day": measure(f.always) / f.days,
            }
            if name == "buildings_per_day":
                row["types"] = dict(sorted(f.always.buildings.items()))
            result[name].append(row)
    spirits: dict[str, dict] = {}
    for focus in focuses:
        for reward in (focus.always, focus.maybe):
            for idea in reward.permanent + [name for name, _ in reward.timed]:
                info = ideas.get(idea)
                if info and info.count > SPIRIT_MODIFIER_LIMIT:
                    spirits.setdefault(
                        idea, {"idea": idea, "modifiers": info.count, "focus": focus.id}
                    )
    result["spirits"] = sorted(
        spirits.values(), key=lambda s: (-s["modifiers"], s["idea"])
    )
    return result


def reward_row(reward: Reward) -> dict:
    return {
        "buildings": dict(sorted(reward.buildings.items())),
        "money": reward.money,
        "pp": reward.pp,
        "stability": reward.stability,
        "war_support": reward.war_support,
        "permanent": reward.permanent,
        "timed": [{"idea": idea, "days": days} for idea, days in reward.timed],
        "removed": reward.removed,
        "swaps": [{"from": old, "to": new} for old, new in reward.swaps],
        "variables": dict(reward.variables),
        "unquantified": reward.unquantified,
        "flags": sorted(reward.flags),
    }


def rounded(value: object) -> object:
    """The report with float noise (0.15000000000000002) rounded off, for JSON."""
    if isinstance(value, float):
        return round(value, 4)
    if isinstance(value, dict):
        return {key: rounded(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [rounded(item) for item in value]
    return value


def build_report(
    tag: str,
    files: Sequence[str],
    focuses: Sequence[Focus],
    ctx: Context,
    ideas: Mapping[str, Idea],
    limit: float,
    top: int,
) -> dict:
    graph = Graph(focuses)
    by_id = {f.id: f for f in focuses}
    granted = {
        idea
        for f in focuses
        for r in (f.always, f.maybe)
        for idea in r.permanent + [name for name, _ in r.timed]
    }
    return {
        "tag": tag,
        "files": list(files),
        "stack_limit": limit,
        "standard_effects": len(ctx.standard),
        "tag_effects": len(ctx.tag_effects),
        "dynamic_variables": len(ctx.variables),
        "ideas_not_found": sorted(granted - set(ideas)),
        "focuses": [
            {
                "id": f.id,
                "file": f.file,
                "line": f.line,
                "cost": f.cost,
                "days": f.days,
                "branches": graph.roots_of.get(f.id, []),
                "prerequisites": f.prerequisites,
                "mutually_exclusive": f.exclusive,
                "requires": [sorted(block) for block in f.needs],
                "forbids": sorted(f.forbids),
                "reward": reward_row(f.always),
                "conditional": reward_row(f.maybe),
            }
            for f in focuses
        ],
        "paths": graph.path_rows(),
        "branches": branch_rows(graph, by_id, ideas, ctx, limit),
        "outliers": outliers(focuses, ideas, top),
    }


# --- text ---------------------------------------------------------------------------


def fmt(value: float) -> str:
    return f"{value:g}"


def span(bounds: Mapping[str, float]) -> str:
    low, high = fmt(bounds["min"]), fmt(bounds["max"])
    return low if low == high else f"{low}..{high}"


def table(rows: Sequence[Sequence[str]]) -> list[str]:
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
    return [
        "  ".join(
            c.ljust(w) if i == 0 else c.rjust(w)
            for i, (c, w) in enumerate(zip(row, widths))
        )
        for row in rows
    ]


def reward_text(reward: dict) -> str:
    swapped = {swap["from"]: swap["to"] for swap in reward["swaps"]}
    replaced = {swap["to"]: swap["from"] for swap in reward["swaps"]}
    parts = []
    if reward["buildings"]:
        built = ", ".join(f"{k} {fmt(v)}" for k, v in reward["buildings"].items())
        parts.append(f"buildings {built}")
    for label, name in (
        ("money", "money"),
        ("pp", "pp"),
        ("stability", "stability"),
        ("war support", "war_support"),
    ):
        if reward[name]:
            parts.append(f"{label} {reward[name]:+g}")
    if reward["permanent"]:
        ideas = [
            f"{i} (replaces {replaced[i]})" if i in replaced else i
            for i in reward["permanent"]
        ]
        parts.append("spirits " + ", ".join(ideas))
    if reward["timed"]:
        timed = [f"{t['idea']} {fmt(t['days'] or 0)}d" for t in reward["timed"]]
        parts.append("timed " + ", ".join(timed))
    if lost := [i for i in reward["removed"] if i not in swapped]:
        parts.append("removes " + ", ".join(lost))
    if reward["variables"]:
        parts.append(
            "variables "
            + ", ".join(f"{k} {v:+g}" for k, v in reward["variables"].items())
        )
    if reward["unquantified"]:
        parts.append("unquantified: " + "; ".join(reward["unquantified"]))
    return "; ".join(parts)


def format_text(
    report: dict,
    *,
    show_forks: bool = False,
    show_focuses: bool = False,
    show_paths: bool = False,
) -> str:
    lines = [
        f"{report['tag']} focus reward audit ({', '.join(report['files'])})",
        f"  {len(report['focuses'])} focuses, {report['standard_effects']} standard "
        f"building effects, {report['tag_effects']} tag effects, "
        f"{report['dynamic_variables']} dynamic modifier variables",
        "  Totals count unconditional rewards. A range spans the valid paths "
        "through exclusive forks.",
    ]
    left_out = sum(
        bool(f["reward"]["unquantified"] or f["conditional"]["unquantified"])
        for f in report["focuses"]
    )
    if left_out:
        lines.append(
            f"  unquantified rewards in {left_out} focuses (formulas, state loops); "
            "--focuses shows them"
        )
    if report["ideas_not_found"]:
        lines.append(
            f"  {len(report['ideas_not_found'])} granted ideas not found in "
            f"common/ideas: {', '.join(report['ideas_not_found'][:8])}"
        )
    header = ["branch", "focuses", *METRICS]
    rows = [header] + [
        [b["root"], str(b["focuses"]), *(span(b["metrics"][m]) for m in METRICS)]
        for b in report["branches"]
    ]
    lines += ["", "== branches ==", *table(rows)]
    if show_forks:
        lines += ["", "== forks (what each alternative leads to) =="]
        for branch in report["branches"]:
            for fork in branch["forks"]:
                arms = " | ".join(
                    f"{a['focus']} [{a['focuses']} focuses, "
                    f"buildings {fmt(a['buildings'])}, money {fmt(a['money'])}, "
                    f"pp {fmt(a['pp'])}, spirits {fmt(a['spirits'])}]"
                    for a in fork
                )
                lines.append(f"  {branch['root']}: {arms}")
    if show_paths:
        lines += ["", "== paths (choices that exclude each other) =="]
        for path in report["paths"]:
            setters = (
                f"set by {', '.join(path['setters'])}; " if path["setters"] else ""
            )
            lines.append(
                f"  {path['choice']}: {setters}gates {path['gates']} focuses; "
                f"branches {', '.join(path['branches'])}"
            )
        if not report["paths"]:
            lines.append("  none")
    lines += ["", f"== stacking over {fmt(report['stack_limit'])} =="]
    flagged = [(b["root"], row) for b in report["branches"] for row in b["stacking"]]
    for root, row in flagged:
        sources = ", ".join(f"{name} {amount:+g}" for name, amount in row["from"][:6])
        choice = f"  [{', '.join(row['path'])}]" if row["path"] else ""
        lines.append(f"  {root}: {row['key']} {row['sum']:+g}  <- {sources}{choice}")
    if not flagged:
        lines.append("  none")
    lines += ["", "== outliers =="]
    for name, rows_ in report["outliers"].items():
        lines.append(f"  {name.replace('_', ' ')}:")
        if name == "spirits":
            lines += [
                f"    {s['idea']}  {s['modifiers']} modifiers  ({s['focus']})"
                for s in rows_
            ]
        else:
            for r in rows_:
                types = ", ".join(
                    f"{k} {fmt(v)}" for k, v in r.get("types", {}).items()
                )
                lines.append(
                    f"    {r['focus']}  {fmt(r['value'])} over {fmt(r['days'])}d = "
                    f"{r['per_day']:.4f}/day" + (f"  ({types})" if types else "")
                )
        if not rows_:
            lines.append("    none")
    if show_focuses:
        lines += ["", "== focuses =="]
        for focus in report["focuses"]:
            text = reward_text(focus["reward"])
            maybe = reward_text(focus["conditional"])
            if text or maybe:
                suffix = f"  [conditional: {maybe}]" if maybe else ""
                lines.append(f"  {focus['id']}  {fmt(focus['days'])}d  {text}{suffix}")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Audit what a country's focus rewards hand out, per focus, "
        "per branch, and stacked"
    )
    parser.add_argument("--tag", required=True, help="country tag, such as BRA")
    parser.add_argument(
        "--file",
        action="append",
        default=[],
        type=Path,
        metavar="PATH",
        help="focus file to read, repeatable (default: every common/national_focus file)",
    )
    parser.add_argument(
        "--root", type=Path, default=REPO_ROOT, help="mod root (default: repo root)"
    )
    parser.add_argument(
        "--stack-limit",
        type=float,
        default=0.20,
        help="flag a factor-style modifier whose summed permanent bonus passes this",
    )
    parser.add_argument(
        "--top", type=int, default=10, help="rows per outlier list (default: 10)"
    )
    parser.add_argument(
        "--forks",
        action="store_true",
        help="also list what each fork alternative leads to",
    )
    parser.add_argument(
        "--focuses", action="store_true", help="also list every focus's rewards"
    )
    parser.add_argument(
        "--paths",
        action="store_true",
        help="also list the path flags and leaders that split a branch",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON, not text")
    args = parser.parse_args(argv)
    tag = args.tag.upper()

    try:
        ctx = load_context(args.root, tag)
        files, focuses = read_focuses(args.root, tag, args.file, ctx)
        if not focuses:
            sys.exit(f"error: no {tag}_ focuses found under {args.root}")
        granted = {
            idea
            for f in focuses
            for r in (f.always, f.maybe)
            for idea in r.permanent + [name for name, _ in r.timed]
        }
        ideas = load_ideas(args.root, granted)
    except FileNotFoundError as error:
        sys.exit(f"error: file not found: {error.filename}")
    except OSError as error:
        sys.exit(f"error: cannot read {error.filename}: {error.strerror}")
    except UnicodeError as error:
        sys.exit(f"error: input is not valid UTF-8: {error}")

    report = build_report(tag, files, focuses, ctx, ideas, args.stack_limit, args.top)
    if args.json:
        print(json.dumps(rounded(report), indent=2))
    else:
        print(
            format_text(
                report,
                show_forks=args.forks,
                show_focuses=args.focuses,
                show_paths=args.paths,
            )
        )


if __name__ == "__main__":
    main()
