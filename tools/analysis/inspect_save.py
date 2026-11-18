#!/usr/bin/env python3
"""Inspect countries in a text HOI4 save the way the game shows them.

    python tools/analysis/inspect_save.py <save.hoi4> SAU
    python tools/analysis/inspect_save.py <save.hoi4> SAU PER --var gdp_total
    python tools/analysis/inspect_save.py <save.hoi4> --world

Per country: stability, war support, political power, ruling party, MD budget, debt,
tax, growth, and spending law variables, ideas, the resource balance, divisions with
their templates and fielded equipment against the templates' base need, military
production lines by equipment archetype, the construction queue, the stockpile, market
contracts, and shared building slots and buildings over owned states. --world prints
production shares, resource shortages, and market totals for every country.

Saves must be text (save_as_binary=no in settings.txt). The file is streamed once and
each country is read from its own block. Base need leaves out need modifiers, so the
engine's army target can be higher; log num_target_equipment_in_armies@ from a probe
for that. The resource net is available minus demand, so a shortage shows even where
the benchmark log's consumed-based net reads 0.
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

# Country variables MD's economy keeps, by topic.
ECONOMY = {
    "budget": (
        "display_income",
        "display_expense",
        "treasury",
        "treasury_rate",
        "budget_balance_ratio",
        "ai_budget_balance",
    ),
    "debt": ("debt", "debt_ratio", "interest_rate", "debt_service_share"),
    "taxes": (
        "population_tax_rate",
        "expected_population_tax_rate",
        "corporate_tax_rate",
        "expected_corporate_tax_rate",
        "population_tax",
        "corporate_tax",
    ),
    "growth": (
        "gdp_total",
        "gdp_per_capita",
        "last_quarter_gdp_growth_rate",
        "overall_productivity",
        "inflation_rate_var",
        "currency_strength",
        "total_unemployed_percentage_display",
        "population_total_m",
        "actual_consumer_goods_percent_display",
    ),
}
# Spending law variable and the expected level it is measured against.
SPENDING_LAWS = (
    ("bureau_law", "expected_adm_spending"),
    ("police_law", "expected_police_spending"),
    ("education_law", "expected_edu_spending"),
    ("health_law", "expected_health_spending"),
    ("social_law", "expected_welfare_spending"),
    ("military_law", "expected_military_law"),
)

_SECTION_RE = re.compile(r"^(\w+)=\{\s*$")
_ENTRY_RE = re.compile(r"^\t(\w+)=\{\s*$")
_EQUIPMENT_ID_RE = re.compile(r"^\t\tid=\{ id=(\d+) type=70 \}")
_STRING_RE = re.compile(r'"[^"]*"')
_FIELD_RE = re.compile(r"^\t+(\w+)=([^{\n]+)$", re.M)
_LEVEL_RE = re.compile(r"^\t\t\t(\w+)=\{\n\t\t\t\tlevel=(\d+)", re.M)
_SUFFIX_RE = re.compile(r"_\d+$")
_SLOT_RE = re.compile(r"^\t+(\w+)=\{ x=\d+ y=\d+ \}", re.M)
_VARIANT_AMOUNT_RE = re.compile(r"id=\{ id=(\d+) type=70 \}\n\t+amount=(-?[\d.]+)")
_WANTED_SECTIONS = (
    "equipments",
    "states",
    "countries",
    "equipment_market",
    "division_templates",
)


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
class Template:
    country: str
    name: str
    battalions: list[str]


@dataclass
class Save:
    date: str = ""
    equipment: dict[str, str] = field(default_factory=dict)
    states: dict[str, State] = field(default_factory=dict)
    countries: dict[str, str] = field(default_factory=dict)
    templates: dict[str, Template] = field(default_factory=dict)
    market: str = ""


@dataclass
class Mod:
    archetype: dict[str, str]
    provincial: set[str]
    shared_slots: set[str]
    category_slots: dict[str, int]
    province_state: dict[str, str]
    unit_need: dict[str, dict[str, int]]

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
        # A for_each frame such as heavy_tank_amphibious_chassis is its own group.
        frame = re.search(r"^\t\tfor_each\s*=", body, re.M)
        archetype[name] = found.group(1) if found and not frame else name
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
    unit_need = {}
    for name, body in _top_blocks(os.path.join(root, "common/units/*.txt")):
        need = re.search(r"\bneed\s*=\s*\{([^}]*)\}", body)
        if need:
            unit_need[name] = {
                a: int(n) for a, n in re.findall(r"(\w+)\s*=\s*(\d+)", need.group(1))
            }
    return Mod(archetype, provincial, shared, slots, province_state, unit_need)


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


def _add_template(save: Save, body: str, tags: set[str]) -> None:
    country = _value(body, "country", 2) or ""
    template_id = re.search(r"\n\t\tid=\{ id=(\d+) type=52 \}", body)
    if country in tags and template_id:
        name = _value(body, "name", 2) or _value(body, "localization_key", 2) or "?"
        battalions = _SLOT_RE.findall(
            _block(body, "regiments", 2) + _block(body, "support", 2)
        )
        save.templates[template_id.group(1)] = Template(country, name, battalions)


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
            elif depth >= 2 and entry:
                if section in ("states", "division_templates"):
                    lines.append(line)
                elif section == "countries" and (every_country or entry in tags):
                    lines.append(line)
            depth += _depth_change(line)
            if depth == 1 and entry and lines:
                body = "\n" + "".join(lines)
                if section == "states":
                    save.states[entry] = _parse_state(body)
                elif section == "division_templates":
                    _add_template(save, body, tags)
                elif entry in tags:
                    save.countries[entry] = body
                else:
                    # World reports read only these two blocks; keep each one closed.
                    save.countries[entry] = "".join(
                        _block(body, key, 2) + "\n\t\t}"
                        for key in ("production", "resources")
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


def units(block: str, save: Save, mod: Mod, top: int) -> list[str]:
    """Division totals, templates in use, and fielded against needed equipment."""
    divisions = re.findall(
        r"^\t\t\tdivision=\{\n(.*?)^\t\t\t\}$", _block(block, "units", 2), re.S | re.M
    )
    if not divisions:
        return ["units: none"]
    fielded: Counter[str] = Counter()
    needed: Counter[str] = Counter()
    templates: Counter[str] = Counter()
    strength = organisation = experience = manpower = 0.0
    for body in divisions:
        strength += float(_value(body, "strength", 4) or 0)
        organisation += float(_value(body, "organisation", 4) or 0)
        experience += float(_value(body, "experience", 4) or 0)
        men = re.search(
            r"army_manpower_value=\{\n\t+value=\{ tag=\"\w+\" value=(\d+)", body
        )
        manpower += int(men.group(1)) if men else 0
        for variant, amount in _VARIANT_AMOUNT_RE.findall(_block(body, "equipment", 4)):
            key = save.equipment.get(variant, "?" + variant)
            fielded[mod.archetype_of(key)] += float(amount)
        template_id = re.search(r"division_template_id=\{ id=(\d+)", body)
        template = save.templates.get(template_id.group(1) if template_id else "")
        templates[template.name if template else "?"] += 1
        for battalion in template.battalions if template else []:
            needed.update(mod.unit_need.get(battalion, {}))
    count = len(divisions)
    rows = [
        f"units: {count} divisions, strength {strength / count:.0f}% and organisation "
        f"{organisation / count:.1f} on average, experience {experience / count:.0f}, "
        f"manpower {manpower:,.0f}",
        "templates: "
        + ", ".join(f"{name} {n}" for name, n in templates.most_common(top)),
        "equipment fielded / template base need (before need modifiers):",
    ]
    for name in sorted(
        needed, key=lambda a: fielded[a] / needed[a] if needed[a] else 1
    ):
        share = 100 * fielded[name] / needed[name] if needed[name] else 0
        rows.append(
            f"  {name:42} {fielded[name]:>9,.0f} / {needed[name]:>9,} ({share:3.0f}%)"
        )
    return rows


def _amounts(text: str) -> dict[str, float]:
    return {name: float(n) for name, n in _FIELD_RE.findall(text)}


def resource_balance(block: str) -> dict[str, dict[str, float]]:
    """Resource to its produced, imported, export pool, exported, available, demand,
    net, deposit and building figures, from the country's own resources block.

    to_use holds three unnamed groups: what is available after the export pool, an
    empty group, and demand as negative numbers.
    """
    res = _block(block, "resources", 2)
    to_use = [
        _amounts(group)
        for group in re.findall(r"\{([^{}]*)\}", _block(res, "to_use", 3))
    ]
    figures = {
        "produced": _amounts(_block(res, "produced", 3)),
        "imported": _amounts(_block(res, "imported", 3)),
        "export pool": _amounts(_block(res, "to_export", 3)),
        "exported": _amounts(_block(res, "exported", 3)),
        "available": to_use[0] if to_use else {},
        "demand": {r: -n for r, n in (to_use[2] if len(to_use) > 2 else {}).items()},
        "deposits": {},
        "buildings": {},
    }
    for origin in re.findall(r"^\t\t\torigin=\{\n(.*?)^\t\t\t\}$", res, re.S | re.M):
        for source in ("resources", "buildings"):
            for name, amount in _amounts(_block(origin, source, 4)).items():
                target = figures["deposits" if source == "resources" else "buildings"]
                target[name] = target.get(name, 0) + amount
    balance: dict[str, dict[str, float]] = defaultdict(dict)
    for figure, values in figures.items():
        for name, amount in values.items():
            balance[name][figure] = amount
    for row in balance.values():
        row["net"] = row.get("available", 0) - row.get("demand", 0)
    return dict(balance)


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
    for topic, names in ECONOMY.items():
        print(f"{topic}: " + ", ".join(f"{n} {_value(values, n, 3)}" for n in names))
    print(
        "spending laws (law/expected): "
        + ", ".join(
            f"{law.removesuffix('_law')} {_value(values, law, 3)}/{_value(values, expected, 3)}"
            for law, expected in SPENDING_LAWS
        )
    )
    if variables:
        print(
            "variables: " + ", ".join(f"{n} {_value(values, n, 3)}" for n in variables)
        )
    ideas = re.search(r"\n\t\t\tideas=\{\n\t+([^}]*)", politics)
    print("ideas: " + (" ".join(ideas.group(1).split()) if ideas else "none"))

    print(
        "\nresources: produced + imported - export pool = available, minus demand = net"
    )
    for name, row in sorted(resource_balance(block).items()):
        g = row.get
        print(
            f"  {name:12} {g('produced', 0):>7g} + {g('imported', 0):>6g} - {g('export pool', 0):>6g} "
            f"= {g('available', 0):>7g} - {g('demand', 0):>6g} = {g('net', 0):>+8.2f}"
            f"  (deposits {g('deposits', 0):g}, buildings {g('buildings', 0):g}, sold {g('exported', 0):g})"
        )

    print()
    for row in units(block, save, mod, top):
        print(row)

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
    buildings: Counter[str] = Counter()
    for state in owned.values():
        buildings.update(state.buildings)
    print(
        "buildings in owned states: "
        + ", ".join(f"{b} {n}" for b, n in buildings.most_common() if n)
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
    short: Counter[str] = Counter()
    shortfall: Counter[str] = Counter()
    produced: Counter[str] = Counter()
    for block in save.countries.values():
        for name, row in resource_balance(block).items():
            produced[name] += row.get("produced", 0)
            if row["net"] < 0:
                short[name] += 1
                shortfall[name] -= row["net"]
    print("\nresources: world produced, countries short, total shortfall")
    for name in sorted(produced):
        print(
            f"  {name:12} {produced[name]:>9,.0f} {short[name]:>5} {shortfall[name]:>9,.1f}"
        )

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
        print_country(tag.upper(), save, mod, args.var, args.top)
    if args.world:
        print_world(save, mod, args.top)
    return 0


if __name__ == "__main__":
    sys.exit(main())
