#!/usr/bin/env python3
"""Inspect countries in a text HOI4 save the way the game shows them.

    python tools/analysis/inspect_save.py <save.hoi4> SAU
    python tools/analysis/inspect_save.py <save.hoi4> SAU PER --var gdp_total
    python tools/analysis/inspect_save.py <save.hoi4> --world

Per country: stability, war support, political power, ruling party, MD economy
variables, ideas, the construction queue, military production lines by equipment
archetype, the stockpile, market contracts, and shared building slots over owned
states. --world prints production shares and market totals for every country.

Saves must be text (save_as_binary=no in settings.txt). The file is streamed once and
each country is read from its own block. The save holds no reliable resource balance,
fielded equipment, or helicopter stock under archetype names; read the benchmark
log's resource lines, or log num_equipment@ and num_equipment_in_armies@ from a probe.
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DEFAULT_VARIABLES = (
    "treasury",
    "treasury_rate",
    "debt",
    "interest_rate",
    "population_tax_rate",
    "corporate_tax_rate",
    "gdp_total",
    "gdp_per_capita",
    "inflation_rate_var",
    "total_unemployed_percentage_display",
)

_SECTION_RE = re.compile(r"^(\w+)=\{\s*$")
_ENTRY_RE = re.compile(r"^\t(\w+)=\{\s*$")
_EQUIPMENT_ID_RE = re.compile(r"^\t\tid=\{ id=(\d+) type=70 \}")
_STRING_RE = re.compile(r'"[^"]*"')
_FIELD_RE = re.compile(r"^\t+(\w+)=([^{\n]+)$", re.M)
_LEVEL_RE = re.compile(r"^\t\t\t(\w+)=\{\n\t\t\t\tlevel=(\d+)", re.M)
_SUFFIX_RE = re.compile(r"_\d+$")
_WANTED_SECTIONS = ("equipments", "states", "countries", "equipment_market")


def _depth_change(line: str) -> int:
    text = _STRING_RE.sub("", line)
    return text.count("{") - text.count("}")


def _block(text: str, key: str, indent: int) -> str:
    """The body of `key={` at `indent` tabs, up to its closing brace."""
    tabs = "\t" * indent
    start = text.find(f"\n{tabs}{key}={{\n")
    if start < 0:
        return ""
    end = text.find(f"\n{tabs}}}", start)
    return text[start : end if end >= 0 else len(text)]


def _value(text: str, key: str, indent: int) -> str | None:
    match = re.search(rf"^{chr(9) * indent}{key}=([^{{\n]+)$", text, re.M)
    return match.group(1).strip('"') if match else None


@dataclass
class State:
    owner: str = ""
    controller: str = ""
    category: str = ""
    extra_slots: int = 0
    buildings: dict[str, int] = field(default_factory=dict)


@dataclass
class Save:
    date: str = ""
    equipment: dict[str, str] = field(default_factory=dict)
    states: dict[str, State] = field(default_factory=dict)
    countries: dict[str, str] = field(default_factory=dict)
    market: str = ""


@dataclass
class Mod:
    archetype: dict[str, str]
    provincial: set[str]
    shared_slots: set[str]
    category_slots: dict[str, int]
    province_state: dict[str, str]

    def archetype_of(self, key: str) -> str:
        """Group a save equipment key by archetype, keeping sub-archetypes apart."""
        if key in self.archetype:
            return self.archetype[key]
        base = _SUFFIX_RE.sub("", key)
        return base if base in self.archetype else key


def _read(path: str) -> str:
    with open(path, encoding="utf-8-sig") as handle:
        return handle.read()


def _top_blocks(path_glob: str) -> list[tuple[str, str]]:
    blocks = []
    for path in sorted(glob.glob(path_glob, recursive=True)):
        text = _read(path)
        blocks += re.findall(r"^\t(\w+)\s*=\s*\{(.*?)^\t\}", text, re.S | re.M)
    return blocks


def load_mod(root: str) -> Mod:
    archetype = {}
    for name, body in _top_blocks(
        os.path.join(root, "common/units/equipment/**/*.txt")
    ):
        found = re.search(r"^\t\tarchetype\s*=\s*(\w+)", body, re.M)
        archetype[name] = found.group(1) if found else name
    provincial, shared = {"rail_way"}, set()
    for name, body in _top_blocks(os.path.join(root, "common/buildings/*.txt")):
        if re.search(r"^\t\tprovincial\s*=\s*yes", body, re.M):
            provincial.add(name)
        if re.search(r"shares_slots\s*=\s*yes", body):
            shared.add(name)
    slots = {}
    for name, body in _top_blocks(os.path.join(root, "common/state_category/*.txt")):
        found = re.search(r"local_building_slots\s*=\s*(\d+)", body)
        if found:
            slots[name] = int(found.group(1))
    province_state = {}
    for path in glob.glob(os.path.join(root, "history/states/*.txt")):
        text = _read(path)
        state_id = re.search(r"\bid\s*=\s*(\d+)", text)
        provinces = re.search(r"provinces\s*=\s*\{([^}]*)\}", text)
        if state_id and provinces:
            for province in provinces.group(1).split():
                province_state[province] = state_id.group(1)
    return Mod(archetype, provincial, shared, slots, province_state)


def _parse_state(body: str) -> State:
    owner = _value(body, "owner", 2) or ""
    return State(
        owner=owner,
        controller=_value(body, "controller", 2) or owner,
        category=_value(body, "state_category", 2) or "",
        extra_slots=int(_value(body, "extra_shared_slots", 2) or 0),
        buildings={
            b: int(n) for b, n in _LEVEL_RE.findall(_block(body, "buildings", 2))
        },
    )


def read_save(path: str, tags: set[str], every_country: bool) -> Save:
    """Stream the save and keep only the sections the reports read."""
    save = Save()
    depth, section, entry = 0, "", ""
    lines: list[str] = []
    # Saves are CRLF; universal newlines lets every pattern use \n.
    with open(path, encoding="utf-8") as handle:
        if not handle.readline().startswith("HOI4txt"):
            raise ValueError(f"{path} is not a text save; set save_as_binary=no")
        for line in handle:
            if depth == 0:
                found = _SECTION_RE.match(line)
                section = found.group(1) if found else ""
                if line.startswith("date="):
                    save.date = line.split("=", 1)[1].strip().strip('"')
            elif depth == 1 and section in _WANTED_SECTIONS:
                found = _ENTRY_RE.match(line)
                entry = found.group(1) if found else ""
            elif depth == 2 and section == "equipments" and entry:
                found = _EQUIPMENT_ID_RE.match(line)
                if found:
                    save.equipment[found.group(1)] = entry
            if section == "equipment_market":
                save.market += line
            elif depth >= 2 and section in ("states", "countries") and entry:
                if section == "states" or every_country or entry in tags:
                    lines.append(line)
            depth += _depth_change(line)
            if depth == 1 and entry and lines:
                body = "\n" + "".join(lines)
                if section == "states":
                    save.states[entry] = _parse_state(body)
                else:
                    save.countries[entry] = (
                        body if entry in tags else _block(body, "production", 2)
                    )
                lines, entry = [], ""
    return save


def production_lines(block: str, save: Save, mod: Mod) -> dict[str, list[int]]:
    """Archetype to [active factories, requested factories, lines]."""
    lines: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0])
    for body in re.findall(r"\n\t\t\tmilitary_lines=\{\n(.*?)\n\t\t\t\}", block, re.S):
        variant = re.search(r"equipment_variant_index=\{ id=(\d+)", body)
        if not variant:
            continue
        key = save.equipment.get(variant.group(1), "?" + variant.group(1))
        row = lines[mod.archetype_of(key)]
        row[0] += int(_value(body, "active_factories", 4) or 0)
        row[1] += int(_value(body, "requested_factories", 4) or 0)
        row[2] += 1
    return lines


def construction_queue(block: str, tag: str, save: Save, mod: Mod) -> list[str]:
    queue = _block(_block(block, "production", 2), "general_lines", 3)
    rows = []
    for body in re.findall(
        r"^\t\t\t\tbuilding=\{\n(.*?)^\t\t\t\t\}$", queue, re.S | re.M
    ):
        fields = dict(_FIELD_RE.findall(body))
        template = re.search(r"template=(\w+)", body)
        location = re.search(r"location=(\d+)", body)
        if not template or not location:
            continue
        building, place = template.group(1), location.group(1)
        # A state building's location is a state id; a provincial one's is a province.
        provincial = building in mod.provincial or place not in save.states
        state_id = mod.province_state.get(place, "") if provincial else place
        state = save.states.get(state_id)
        owner = (
            "owned"
            if state and state.owner == tag
            else f"not owned ({state.owner if state else '?'})"
        )
        amount = int(fields.get("amount", 1))
        cost = float(fields.get("cost", 0)) * amount
        produced = float(fields.get("produced", 0))
        speed = float(fields.get("speed", 0))
        left = (
            f"{(cost - produced) / speed / 365:.1f} years left"
            if speed > 0
            else "no progress"
        )
        rows.append(
            f"#{fields.get('priority', '?'):>2} {building:24} levels {amount:>3} factories "
            f"{fields.get('active_factories', '0'):>2} since {fields.get('created_date', '?').strip(chr(34))}, "
            f"{left}, {owner} state {state_id}"
        )
    return rows


def stockpile(block: str, save: Save, mod: Mod) -> Counter[str]:
    stock: Counter[str] = Counter()
    held = _block(_block(block, "production", 2), "equipments", 3)
    for variant, amount in re.findall(
        r"id=\{ id=(\d+) type=70 \}\n\t+amount=(-?\d+)", held
    ):
        stock[mod.archetype_of(save.equipment.get(variant, "?" + variant))] += int(
            amount
        )
    return stock


def contracts(save: Save, mod: Mod) -> list[tuple[str, str, str, int]]:
    """Every purchase contract line as (seller, buyer, archetype, amount)."""
    rows = []
    for body in re.findall(
        r"^\t\tpurchase_contract=\{\n(.*?)^\t\t\}$", save.market, re.S | re.M
    ):
        seller = re.search(r'seller="(\w+)"', body)
        buyer = re.search(r'buyer="(\w+)"', body)
        draft = _block(body, "contract_draft", 4)
        if not seller or not buyer:
            continue
        for variant, amount in re.findall(
            r"id=\{ id=(\d+) type=70 \}\n\t+amount=(\d+)", draft
        ):
            key = save.equipment.get(variant, "?" + variant)
            rows.append(
                (seller.group(1), buyer.group(1), mod.archetype_of(key), int(amount))
            )
    return rows


def print_country(
    tag: str, save: Save, mod: Mod, variables: list[str], top: int
) -> None:
    block = save.countries.get(tag)
    if block is None:
        print(f"## {tag}: not in this save\n")
        return
    politics = _block(block, "politics", 2)
    print(f"## {tag} ({save.date})")
    print(
        f"stability {_value(block, 'stability', 2)}, war support {_value(block, 'war_support', 2)}, "
        f"political power {_value(politics, 'political_power', 3)}, ruling party {_value(politics, 'ruling_party', 3)}"
    )
    values = _block(block, "variables", 2)
    print(
        "variables: "
        + ", ".join(f"{name} {_value(values, name, 3)}" for name in variables)
    )
    ideas = re.search(r"\n\t\t\tideas=\{\n\t+([^}]*)", politics)
    print("ideas: " + (" ".join(ideas.group(1).split()) if ideas else "none"))

    lines = production_lines(block, save, mod)
    total = sum(row[0] for row in lines.values())
    print(
        f"\nproduction: {total} factories on {sum(row[2] for row in lines.values())} lines"
    )
    for name, (active, requested, count) in sorted(
        lines.items(), key=lambda kv: -kv[1][0]
    ):
        print(f"  {name:42} {active:>4} requested {requested:>4} lines {count}")

    print("\nconstruction queue:")
    for row in construction_queue(block, tag, save, mod) or ["none"]:
        print("  " + row)

    print(
        "\nstockpile: "
        + ", ".join(f"{a} {n}" for a, n in stockpile(block, save, mod).most_common(top))
    )

    print("\nmarket contracts:")
    deals = [row for row in contracts(save, mod) if tag in row[:2]]
    for seller, buyer, name, amount in deals or [("", "", "none", 0)]:
        print(f"  {seller} -> {buyer}: {name} {amount}" if seller else "  none")

    owned = {sid: s for sid, s in save.states.items() if s.owner == tag}
    used = {
        sid: sum(n for b, n in s.buildings.items() if b in mod.shared_slots)
        for sid, s in owned.items()
    }
    caps = {
        sid: mod.category_slots.get(s.category, 0) + s.extra_slots
        for sid, s in owned.items()
    }
    free = {sid: caps[sid] - used[sid] for sid in owned if caps[sid] > used[sid]}
    occupied = sum(1 for s in owned.values() if s.controller != tag)
    print(
        f"\nstates: {len(owned)} owned ({occupied} occupied by others), shared slots used "
        f"{sum(used.values())} of {sum(caps.values())}, {len(free)} states with {sum(free.values())} free"
    )
    print()


def print_world(save: Save, mod: Mod, top: int) -> None:
    world: Counter[str] = Counter()
    for block in save.countries.values():
        for name, (active, _, _) in production_lines(block, save, mod).items():
            world[name] += active
    total = sum(world.values()) or 1
    print(
        f"## World ({save.date}): {sum(world.values())} factories on production lines"
    )
    for name, active in world.most_common(top):
        print(f"  {name:42} {active:>5} ({100 * active / total:4.1f}%)")
    deals = contracts(save, mod)
    units: Counter[str] = Counter()
    for _, _, name, amount in deals:
        units[name] += amount
    print(
        f"\nmarket: {len(deals)} contract lines, {len({row[1] for row in deals})} buyers"
    )
    for name, amount in units.most_common(top):
        print(f"  {name:42} {amount:>7}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect countries in a text HOI4 save."
    )
    parser.add_argument("save", help="path to a text .hoi4 save")
    parser.add_argument("tags", nargs="*", help="country tags to report")
    parser.add_argument(
        "--world",
        action="store_true",
        help="also report world production and market totals",
    )
    parser.add_argument(
        "--var", action="append", default=[], help="extra country variable to print"
    )
    parser.add_argument(
        "--top", type=int, default=15, help="rows in ranked lists (default: 15)"
    )
    parser.add_argument("--path", default=REPO, help="mod root (default: repo root)")
    args = parser.parse_args()
    if not args.tags and not args.world:
        parser.error("give at least one tag or --world")

    tags = {tag.upper() for tag in args.tags}
    mod = load_mod(args.path)
    try:
        save = read_save(args.save, tags, args.world)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1
    for tag in args.tags:
        print_country(
            tag.upper(), save, mod, list(DEFAULT_VARIABLES) + args.var, args.top
        )
    if args.world:
        print_world(save, mod, args.top)
    return 0


if __name__ == "__main__":
    sys.exit(main())
