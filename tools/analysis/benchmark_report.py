#!/usr/bin/env python3
"""Turn Hearts of Iron IV game.log and error.log files from headless runs into reports.

The mod's debug logging writes one line per fact, for example:

    [12:28:36][2000.02.01.01]: [12:28:36][2000.02.01.01]:  1:00, 1 February, 2000: SAU: Monthly Benchmark: Civilian: 13 Military: 2 GDP per Capita: 5.5

A line has a game date, a subject (a tag or a country name) and a message. Most
messages are a label followed by `Name: number` pairs. Those parse generically, so
a new probe line needs no new code. Spending Laws (law/expected/offset triplets),
wars, decisions, event options, ideas and investments are the exceptions.

    python tools/analysis/benchmark_report.py compare base=a/game.log fix=b/game.log
    python tools/analysis/benchmark_report.py series game.log SAU --fields GDP,Debt --every 12
    python tools/analysis/benchmark_report.py spread a/game.log b/game.log "Treasury Rate" --below 0
    python tools/analysis/benchmark_report.py wars game.log
    python tools/analysis/benchmark_report.py counts a=a/game.log b=b/game.log --who Italy --before 2002
    python tools/analysis/benchmark_report.py laws game.log --law Defence
    python tools/analysis/benchmark_report.py errors error.log
    python tools/analysis/benchmark_report.py volume game.log

A run is `LABEL=LOG`, or a bare path labelled by its folder name. Logs stream line by
line. Nothing is written to disk: reports go to stdout.
"""

from __future__ import annotations

import argparse
import re
import statistics
import sys
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from io import TextIOWrapper
from pathlib import Path
from typing import NamedTuple

Date = tuple[int, int, int]
Month = tuple[int, int]
Fields = dict[str, float]

# Use the last game date before the clock; debug logs add a source location.
_LINE = re.compile(
    r"\[(\d{4})\.(\d{2})\.(\d{2})\.\d+\](?:\[[^\]\r\n]+:\d+\])?:"
    r"\s+\d+:\d+, [^:]*?: ([^:]+): (.*)$"
)
_NUMBER = r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?"
# Field names start with a capital and hold spaces. A number followed by `/` is part
# of a triplet, not a field.
_PAIR = re.compile(rf"([A-Z][A-Za-z ]*?): ({_NUMBER})(?![\d./])")
_TRIPLET = re.compile(rf"([A-Z]\w*): ({_NUMBER})/({_NUMBER})/({_NUMBER})")
_RAW = re.compile(r"Raw \(([A-Z/]+)\): (\S+)")
_STAMPS = re.compile(r"^(?:\[[^\]]*\]:?\s*)+")
_ERROR_STAMP = re.compile(r"^\[[^\]]*\]\[[^\]]*\]: ")
_QUOTED = re.compile(r"'[^']*'")
_PATH = re.compile(r"\"?(?:[\w.-]+/)+[^/:\"()]*?\.\w{2,4}\"?")
_TAG = re.compile(r"\b[A-Z]{3}\b")
_DIGITS = re.compile(r"\d+(?:\.\d+)?")
_VOLUME_DIGITS = re.compile(r"-?\d[\d.,]*")

# Monthly families merge into one row per tag and month; later kinds get a prefix.
_MONTHLY_PREFIX = {
    "Monthly Benchmark": "",
    "Resource Balance (net)": "res_",
    "Resource Imports": "imp_",
    "Construction": "con_",
}
_WAR_PREFIX = "War Declared on "
_CAPITULATION_PREFIX = "Capitulated to "
_LAWS_PREFIX = "Spending Laws"

RESOURCES = [
    "Oil",
    "Steel",
    "Aluminium",
    "Rubber",
    "Tungsten",
    "Chromium",
    "Microchips",
    "Composites",
]
CONSTRUCTION = [
    "Arms",
    "Dockyards",
    "Agriculture",
    "Fossil Plants",
    "Reactors",
    "Renewables",
    "Enrichment",
    "Internet",
    "Rail Terminals",
]
DEFAULT_MAJORS = "CHI,GER,USA,JAP,RAJ,SOV,ENG,FRA"
DEFAULT_ALSO = "SER,SAF,EGY,LBA"
# Headless runs start as GRA (-start_tag=GRA, or hlab --tag GRA), so keep it out of totals.
DEFAULT_SKIP = "GRA"

# Lines that fill error.log on every healthy run.
ERROR_NOISE = ("AI tried to post", "Sub-unit 'Light_", "context_type")

_COUNT_KINDS = {
    "decision": re.compile(r"Decision (?:timeout )?(\S+)"),
    "option": re.compile(
        r"([A-Za-z_]\w*\.\d+\.[A-Za-z0-9]+)|Event ([A-Za-z_]\w*\.\d+) Option ([A-Za-z0-9]+)"
    ),
    "focus": re.compile(r"Focus (\S+)"),
    "idea": re.compile(r"(Idea \S+ (?:added|removed)|add idea \S+)"),
    "investment": re.compile(r"Investment Succeeded"),
}


class Record(NamedTuple):
    date: Date
    who: str
    message: str


class Declaration(NamedTuple):
    date: Date
    attacker: str
    defender: str
    attacker_debt: float
    attacker_interest: float
    attacker_crisis: bool
    defender_debt: float
    defender_interest: float
    defender_crisis: bool


class Capitulation(NamedTuple):
    date: Date
    loser: str
    winner: str
    debt: float
    interest: float
    rate: float


@dataclass
class Run:
    label: str
    months: dict[Month, dict[str, Fields]] = field(
        default_factory=lambda: defaultdict(dict)
    )
    laws: dict[str, list[tuple[Date, Fields]]] = field(
        default_factory=lambda: defaultdict(list)
    )
    declarations: list[Declaration] = field(default_factory=list)
    capitulations: list[Capitulation] = field(default_factory=list)


@dataclass
class Churn:
    changes: Counter[str] = field(default_factory=Counter)
    reversals: Counter[str] = field(default_factory=Counter)
    offset_reversals: Counter[str] = field(default_factory=Counter)
    gap: dict[str, float] = field(default_factory=dict)


# Reading


def read_lines(path: Path) -> Iterator[str]:
    """Yield decoded lines, warning once if bad bytes needed replacement."""
    bad = 0
    with open(path, "rb") as handle:
        for raw in handle:
            try:
                line = raw.decode("utf-8")
            except UnicodeDecodeError:
                bad += 1
                line = raw.decode("utf-8", errors="replace")
            yield line.rstrip("\r\n")
    if bad:
        print(
            f"warning: {path}: {bad} lines had invalid UTF-8 and were decoded "
            "with replacement characters",
            file=sys.stderr,
        )


def iter_records(path: Path) -> Iterator[Record]:
    for line in read_lines(path):
        match = _LINE.search(line)
        if match:
            year, month, day, who, message = match.groups()
            yield Record((int(year), int(month), int(day)), who, message)


def split_message(message: str) -> tuple[str, str]:
    """Label before the first `: ` and the rest. Decisions have no label."""
    label, _, rest = message.partition(": ")
    return label, rest


def pairs(text: str) -> list[tuple[str, float]]:
    """Every `Name: number` pair in order. Names repeat in some lines."""
    return [(name, float(value)) for name, value in _PAIR.findall(text)]


def law_fields(text: str) -> Fields:
    """Spending Laws: `Cat: l/e/o` becomes `Cat`, `Cat Expected`, `Cat Offset`."""
    fields: Fields = {}
    initials: dict[str, str] = {}
    for name, law, expected, offset in _TRIPLET.findall(text):
        fields[name] = float(law)
        fields[f"{name} Expected"] = float(expected)
        fields[f"{name} Offset"] = float(offset)
        initials[name[0]] = name
    fields.update(pairs(text))
    raw = _RAW.search(text)
    if raw:
        for initial, value in zip(raw.group(1).split("/"), raw.group(2).split("/")):
            if initial in initials:
                fields[f"Raw {initials[initial]}"] = float(value)
    return fields


def parse_fields(label: str, rest: str) -> Fields:
    if label.startswith(_LAWS_PREFIX):
        return law_fields(rest)
    return dict(pairs(rest))


def law_categories(fields: Fields) -> list[str]:
    return [name for name in fields if f"{name} Expected" in fields]


def load_run(label: str, path: Path, skip: frozenset[str]) -> Run:
    run = Run(label)
    for record in iter_records(path):
        kind, rest = split_message(record.message)
        prefix = _MONTHLY_PREFIX.get(kind)
        if prefix is not None:
            if record.who in skip:
                continue
            row = run.months[record.date[:2]].setdefault(record.who, {})
            row.update({prefix + name: value for name, value in pairs(rest)})
        elif kind.startswith(_LAWS_PREFIX):
            run.laws[record.who].append((record.date, law_fields(rest)))
        elif kind.startswith(_WAR_PREFIX):
            values = [value for _, value in pairs(rest)]
            if len(values) == 8:
                defender = kind.removeprefix(_WAR_PREFIX)
                run.declarations.append(
                    Declaration(
                        record.date,
                        record.who,
                        defender,
                        values[0],
                        values[1],
                        bool(values[3]),
                        values[4],
                        values[5],
                        bool(values[7]),
                    )
                )
        elif kind.startswith(_CAPITULATION_PREFIX):
            values = [value for _, value in pairs(rest)]
            if len(values) == 3:
                winner = kind.removeprefix(_CAPITULATION_PREFIX)
                run.capitulations.append(
                    Capitulation(record.date, record.who, winner, *values)
                )
    return run


# Formatting


def fmt(value: float, digits: int = 1) -> str:
    if abs(value) >= 1000:
        return f"{value:,.0f}"
    return f"{value:.{digits}f}"


def short(value: float) -> str:
    """Compact cell for generic series: four significant digits."""
    return f"{value:,.0f}" if abs(value) >= 1000 else f"{value:.4g}"


def num(row: Fields, key: str, digits: int = 0, scale: float = 1.0) -> str:
    value = row.get(key)
    return "-" if value is None else fmt(value * scale, digits)


def percent(row: Fields, key: str, digits: int = 0) -> str:
    value = num(row, key, digits, 100)
    return value if value == "-" else value + "%"


def change(start: Fields, end: Fields, key: str, digits: int = 0) -> str:
    return f"{num(start, key, digits)} -> {num(end, key, digits)}"


def pct(new: float | None, old: float | None) -> str:
    if new is None or not old:
        return "-"
    return f"{(new - old) / old * 100:+.0f}%"


def fmt_date(date: Date) -> str:
    return f"{date[0]}-{date[1]:02d}-{date[2]:02d}"


def fmt_month(month: Month) -> str:
    return f"{month[0]}-{month[1]:02d}"


def table(header: Sequence[str], rows: Iterable[Sequence[str]]) -> list[str]:
    lines = ["| " + " | ".join(header) + " |", "|" + " --- |" * len(header)]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return lines


def split_csv(text: str) -> list[str]:
    return [part.strip() for part in text.split(",") if part.strip()]


# compare


def full_months(months: dict[Month, dict[str, Fields]]) -> list[Month]:
    """Keep every month except a likely truncated final month."""
    ordered = sorted(months)
    if len(ordered) > 1 and len(months[ordered[-1]]) < 0.9 * len(months[ordered[-2]]):
        ordered.pop()
    return ordered


def world(rows: dict[str, Fields]) -> dict[str, float]:
    values = list(rows.values())
    total_gdp = sum(r.get("GDP", 0) for r in values) or 1

    def total(key: str) -> float:
        return sum(r.get(key, 0) for r in values)

    def count(test: Callable[[Fields], bool]) -> int:
        return sum(1 for r in values if test(r))

    def median(key: str) -> float:
        return statistics.median(r.get(key, 0) for r in values) if values else 0

    def gdp_weighted(key: str) -> float:
        return sum(r.get(key, 0) * r.get("GDP", 0) for r in values) / total_gdp

    return {
        "Countries": len(values),
        "Civilian factories": total("Civilian"),
        "Military factories": total("Military"),
        "Offices": total("Offices"),
        "Microchip plants": total("Microchip Plants"),
        "Composite plants": total("Composite Plants"),
        "World GDP": total_gdp,
        "Median GDP per capita": median("GDP per Capita"),
        "Total debt": total("Debt"),
        "Debt over 100% of GDP": count(
            lambda r: r.get("GDP", 0) > 0 and r.get("Debt", 0) > r["GDP"]
        ),
        "Weekly deficit (count)": count(lambda r: r.get("Treasury Rate", 0) < 0),
        "Deficit over 3% of GDP a year": count(
            lambda r: r.get("GDP", 0) > 0
            and r.get("Treasury Rate", 0) * 52 / r["GDP"] < -0.03
        ),
        "GDP-weighted inflation %": gdp_weighted("Inflation") * 100,
        "Inflation over 10%": count(lambda r: r.get("Inflation", 0) > 0.10),
        "Deflation": count(lambda r: r.get("Inflation", 0) < 0),
        "Interest over 8%": count(lambda r: r.get("Interest Rate", 0) > 8),
        "GDP-weighted population tax": gdp_weighted("Population Tax"),
        "GDP-weighted corporate tax": gdp_weighted("Corporate Tax"),
        "Median daily PP": median("Daily PP"),
        "Negative PP stockpile": count(lambda r: r.get("Political Power", 0) < 0),
        "Stability under 30%": count(lambda r: r.get("Stability", 1) < 0.30),
    }


def law_churn(samples: Sequence[tuple[Date, Fields]]) -> Churn:
    """Changes and direction reversals per law category over one country's samples."""
    churn = Churn()
    last_direction: dict[str, int] = {}
    last_offset: dict[str, float] = {}
    for (_, prev), (_, cur) in zip(samples, samples[1:]):
        for cat in law_categories(cur):
            old, new = prev.get(cat), cur[cat]
            if old is None or new == old:
                continue
            direction = 1 if new > old else -1
            offset = cur[f"{cat} Offset"]
            churn.changes[cat] += 1
            if last_direction.get(cat, direction) != direction:
                churn.reversals[cat] += 1
                if offset != last_offset.get(cat):
                    churn.offset_reversals[cat] += 1
            last_direction[cat] = direction
            last_offset[cat] = offset
    if samples:
        final = samples[-1][1]
        for cat in law_categories(final):
            churn.gap[cat] = final[cat] - final[f"{cat} Expected"]
    return churn


def world_section(runs: Sequence[Run], first: Month, last: Month) -> list[str]:
    starts = [world(run.months.get(first, {})) for run in runs]
    ends = [world(run.months.get(last, {})) for run in runs]
    header = ["Metric"]
    for run in runs:
        header += [f"{run.label} start", f"{run.label} end"]

    def cell(value: float) -> str:
        return fmt(value, 0 if float(value).is_integer() else 1)

    rows = []
    for key in starts[0]:
        cells = []
        for start, end in zip(starts, ends):
            cells += [cell(start[key]), cell(end[key])]
        rows.append([key, *cells])
    return ["## World totals", "", *table(header, rows), ""]


def shortage_section(runs: Sequence[Run], last: Month) -> list[str]:
    header = ["Resource"]
    for run in runs:
        header += [f"{run.label} countries short", f"{run.label} total shortfall"]
    rows = []
    for res in RESOURCES:
        cells = []
        for run in runs:
            values = [r.get(f"res_{res}") for r in run.months[last].values()]
            short_by = [v for v in values if v is not None and v < 0]
            cells += [str(len(short_by)), fmt(sum(short_by))]
        rows.append([res, *cells])
    return [
        "## Resource deficits at the comparison month",
        "",
        *table(header, rows),
        "",
    ]


def top_section(
    runs: Sequence[Run], first: Month, last: Month, also: Sequence[str]
) -> list[str]:
    base = runs[0].months[first]
    top = sorted(base, key=lambda tag: -base[tag].get("GDP", 0))[:20]
    top += [tag for tag in also if tag not in top]
    header = [
        "Tag",
        "Civilian",
        "Military",
        "Chip plants",
        "GDP",
        "GDP/c",
        "Debt",
        "Interest",
        "Taxes pop/corp",
        "Inflation",
        "Treasury rate",
        "PP",
        "Daily PP",
        "Influence slots",
        "States",
        "Short of",
    ]
    out: list[str] = []
    for run in runs:
        rows = []
        for tag in top:
            s, e = run.months[first].get(tag), run.months[last].get(tag)
            if not s or not e:
                rows.append([tag, "gone", *[""] * (len(header) - 2)])
                continue
            shortages = ", ".join(
                f"{res} {num(e, f'res_{res}')}"
                for res in RESOURCES
                if e.get(f"res_{res}", 0) < 0
            )
            rows.append(
                [
                    tag,
                    change(s, e, "Civilian"),
                    change(s, e, "Military"),
                    change(s, e, "Microchip Plants"),
                    f"{num(e, 'GDP')} ({pct(e.get('GDP'), s.get('GDP'))})",
                    num(e, "GDP per Capita", 2),
                    change(s, e, "Debt"),
                    num(e, "Interest Rate", 1),
                    f"{num(e, 'Population Tax')}/{num(e, 'Corporate Tax')}",
                    percent(e, "Inflation", 1),
                    num(e, "Treasury Rate", 1),
                    num(e, "Political Power"),
                    num(e, "Daily PP", 2),
                    num(e, "Influence Slots"),
                    change(s, e, "States"),
                    shortages or "-",
                ]
            )
        title = f"Top 20 economies plus {', '.join(also)} ({run.label}, start to {fmt_month(last)})"
        out += [f"## {title}", "", *table(header, rows), ""]
    return out


def civilian_section(runs: Sequence[Run], first: Month, last: Month) -> list[str]:
    out: list[str] = []
    for run in runs:
        start, end = run.months[first], run.months[last]
        deltas = sorted(
            (end[tag].get("Civilian", 0) - start[tag].get("Civilian", 0), tag)
            for tag in start
            if tag in end
        )
        gained = sum(1 for delta, _ in deltas if delta > 0)
        lost = sum(1 for delta, _ in deltas if delta < 0)
        shown = deltas if len(deltas) <= 20 else deltas[:10] + deltas[-10:]
        rows = [
            [
                tag,
                num(start[tag], "Civilian"),
                num(end[tag], "Civilian"),
                f"{delta:+.0f}",
                num(end[tag], "Civilian Buildings"),
            ]
            for delta, tag in shown
        ]
        out += [
            f"## Civilian factory change ({run.label})",
            "",
            f"{gained} countries gained, {lost} lost, "
            f"{len(deltas) - gained - lost} unchanged.",
            "",
            *table(["Tag", "Start", "End", "Change", "Buildings at end"], rows),
            "",
        ]
    return out


def majors_over_time_section(
    runs: Sequence[Run], last: Month, majors: Sequence[str]
) -> list[str]:
    columns = ["PP", "daily PP", "civ (buildings)", "chips", "GDP", "debt"]
    columns += ["inflation", "taxes"]
    header = ["Month"] + [f"{run.label} {name}" for run in runs for name in columns]
    reach = max(full_months(run.months)[-1] for run in runs)
    months = sorted(set().union(*(run.months for run in runs)))
    out: list[str] = []
    for tag in majors:
        rows = []
        for month in months:
            if month > reach or (month[1] not in (1, 7) and month != last):
                continue
            cells: list[str] = []
            for run in runs:
                r = run.months.get(month, {}).get(tag)
                if not r:
                    cells += ["-"] * len(columns)
                    continue
                cells += [
                    num(r, "Political Power"),
                    num(r, "Daily PP", 2),
                    f"{num(r, 'Civilian')} ({num(r, 'Civilian Buildings')})",
                    num(r, "Microchip Plants"),
                    num(r, "GDP"),
                    num(r, "Debt"),
                    percent(r, "Inflation", 1),
                    f"{num(r, 'Population Tax')}/{num(r, 'Corporate Tax')}",
                ]
            rows.append([fmt_month(month), *cells])
        out += [f"## {tag} over time", "", *table(header, rows), ""]
    return out


def construction_section(
    runs: Sequence[Run], first: Month, last: Month, majors: Sequence[str]
) -> list[str]:
    rows = []
    for tag in majors:
        for run in runs:
            s, e = run.months[first].get(tag), run.months[last].get(tag)
            if not s or not e:
                continue
            rows.append(
                [
                    tag,
                    run.label,
                    *(
                        change(s, e, key)
                        for key in (
                            "Civilian Buildings",
                            "Offices",
                            "Microchip Plants",
                            "Composite Plants",
                        )
                    ),
                    percent(e, "Unemployment"),
                    num(e, "Microchip Staffing", 2),
                ]
            )
    header = ["Tag", "Run", "Civ buildings", "Offices", "Chip plants"]
    header += ["Composite plants", "Unemployment", "Chip staffing"]
    out = [
        f"## Majors' construction, start to {fmt_month(last)}",
        "",
        *table(header, rows),
        "",
    ]
    first_key = f"con_{CONSTRUCTION[0]}"
    if not any(first_key in r for run in runs for r in run.months[last].values()):
        return out
    rows = []
    for tag in majors:
        for run in runs:
            s, e = run.months[first].get(tag), run.months[last].get(tag)
            if not s or not e or first_key not in e:
                continue
            cells = [change(s, e, f"con_{key}") for key in CONSTRUCTION]
            rows.append(
                [
                    tag,
                    run.label,
                    *cells,
                    num(e, "con_Energy Deficit"),
                    num(e, "con_Nuclear Fuel", 1),
                ]
            )
    header = ["Tag", "Run", *CONSTRUCTION, "Energy deficit", "Nuclear fuel"]
    return out + [
        f"## Majors' other buildings, start to {fmt_month(last)}",
        "",
        *table(header, rows),
        "",
    ]


def resource_section(
    runs: Sequence[Run], last: Month, majors: Sequence[str]
) -> list[str]:
    out: list[str] = []
    for run in runs:
        month = run.months[last]
        if not any(f"imp_{RESOURCES[0]}" in r for r in month.values()):
            continue
        rows = []
        for tag in majors:
            r = month.get(tag)
            if not r:
                continue
            cells = [
                f"{num(r, f'res_{res}')} ({num(r, f'imp_{res}')})" for res in RESOURCES
            ]
            made, used = num(r, "res_Microchips Produced"), num(
                r, "res_Microchips Consumed"
            )
            rows.append([tag, *cells, f"{made}/{used}"])
        out += [
            f"## Majors' resources at {fmt_month(last)} ({run.label}): net balance (imported)",
            "",
            *table(["Tag", *RESOURCES, "Chips made/used"], rows),
            "",
        ]
    return out


def wars_section(run: Run, heading: str, cutoff: Date | None = None) -> list[str]:
    declared = [w for w in run.declarations if cutoff is None or w.date <= cutoff]
    capitulated = [c for c in run.capitulations if cutoff is None or c.date <= cutoff]
    if not declared and not capitulated:
        return []
    crisis = sum(1 for w in declared if w.attacker_crisis or w.defender_crisis)
    attacker_heavy = sum(1 for w in declared if w.attacker_debt > 1)
    defender_heavy = sum(1 for w in declared if w.defender_debt > 1)
    declaration_rows = [
        [
            fmt_date(w.date),
            w.attacker,
            w.defender,
            f"{w.attacker_debt:.2f}, {w.attacker_interest:.1f}%, "
            f"{'yes' if w.attacker_crisis else 'no'}",
            f"{w.defender_debt:.2f}, {w.defender_interest:.1f}%, "
            f"{'yes' if w.defender_crisis else 'no'}",
        ]
        for w in declared
    ]
    capitulation_rows = [
        [
            fmt_date(c.date),
            c.loser,
            c.winner,
            f"{c.debt:.2f}",
            f"{c.interest:.1f}%",
            f"{c.rate:.1f}",
        ]
        for c in capitulated
    ]
    return [
        f"## {heading}",
        "",
        f"{len(declared)} declarations, {crisis} with a side in a debt crisis, "
        f"{attacker_heavy} by an attacker with debt over 100% of GDP, "
        f"{defender_heavy} on a defender with debt over 100% of GDP.",
        "",
        *table(
            [
                "Date",
                "Attacker",
                "Defender",
                "Attacker debt/GDP, interest, crisis",
                "Defender debt/GDP, interest, crisis",
            ],
            declaration_rows,
        ),
        "",
        *table(
            ["Date", "Capitulated", "To", "Debt/GDP", "Interest", "Treasury rate"],
            capitulation_rows,
        ),
        "",
    ]


def churn_section(run: Run, last: Month) -> list[str]:
    if not run.laws:
        return []
    cutoff = (last[0], last[1], 31)
    changes: Counter[str] = Counter()
    reversals: Counter[str] = Counter()
    offset_reversals: Counter[str] = Counter()
    above: Counter[str] = Counter()
    reversing = 0
    for samples in run.laws.values():
        churn = law_churn([s for s in samples if s[0] <= cutoff])
        changes.update(churn.changes)
        reversals.update(churn.reversals)
        offset_reversals.update(churn.offset_reversals)
        above.update(cat for cat, gap in churn.gap.items() if gap > 0)
        reversing += bool(churn.reversals)
    rows = [
        [
            cat,
            str(changes[cat]),
            str(reversals[cat]),
            str(offset_reversals[cat]),
            str(above[cat]),
        ]
        for cat in sorted(changes)
    ]
    header = ["Law", "Changes", "Reversals", "of which the offset moved"]
    header += ["Above expected at end"]
    return [
        f"## Spending law churn ({run.label})",
        "",
        f"Countries with a reversal: {reversing}",
        "",
        *table(header, rows),
        "",
    ]


def cmd_compare(args: argparse.Namespace) -> int:
    skip = frozenset(split_csv(args.skip))
    runs = [load_run(label, path, skip) for label, path in args.runs]
    for run in runs:
        if not run.months:
            print(f"error: {run.label}: no Monthly Benchmark lines", file=sys.stderr)
            return 1
    ends = {run.label: full_months(run.months)[-1] for run in runs}
    last = min(ends.values())
    first = max(min(run.months) for run in runs)
    if first > last:
        print("error: the runs share no fully reported month", file=sys.stderr)
        return 1
    majors, also = split_csv(args.majors), split_csv(args.also)
    out = [
        "# MD headless economy benchmark",
        "",
        f"Compared at {fmt_month(last)} (last month every run fully reported).",
        *(f"- {label}: reached {fmt_month(end)}" for label, end in ends.items()),
        "",
    ]
    out += world_section(runs, first, last)
    out += shortage_section(runs, last)
    out += top_section(runs, first, last, also)
    out += civilian_section(runs, first, last)
    out += majors_over_time_section(runs, last, majors)
    out += construction_section(runs, first, last, majors)
    out += resource_section(runs, last, majors)
    for run in runs:
        heading = f"Wars ({run.label}, to {fmt_month(last)})"
        out += wars_section(run, heading, (last[0], last[1], 31))
    for run in runs:
        out += churn_section(run, last)
    print("\n".join(out))
    return 0


# series and spread


def collect_series(
    path: Path, who: str, label: str, wanted: Sequence[str]
) -> dict[str, list[tuple[Date, Fields]]]:
    series: dict[str, list[tuple[Date, Fields]]] = defaultdict(list)
    for record in iter_records(path):
        if who != "*" and record.who != who:
            continue
        kind, rest = split_message(record.message)
        if not kind.startswith(label):
            continue
        values = parse_fields(kind, rest)
        if wanted:
            values = {name: values[name] for name in wanted if name in values}
        series[record.who].append((record.date, values))
    return series


def find_jumps(
    rows: Sequence[tuple[Date, Fields]], name: str, threshold: float
) -> list[tuple[Date, float, float]]:
    """Steps of at least `threshold` that also exceed three times the old value."""
    jumps = []
    for (_, prev), (date, cur) in zip(rows, rows[1:]):
        if name not in prev or name not in cur:
            continue
        step = abs(cur[name] - prev[name])
        if step >= threshold and step > 3 * max(abs(prev[name]), 0.05):
            jumps.append((date, prev[name], cur[name]))
    return jumps


def cmd_series(args: argparse.Namespace) -> int:
    wanted = split_csv(args.fields)
    series = collect_series(args.log, args.who, args.label, wanted)
    if not series:
        print(f'error: no "{args.label}" lines for {args.who}', file=sys.stderr)
        return 1
    names = wanted or list(
        dict.fromkeys(n for rows in series.values() for _, v in rows for n in v)
    )
    with_who = args.who == "*"
    if args.jumps is not None:
        rows = [
            [who, fmt_date(date), names[0], short(old), short(new)]
            for who, points in series.items()
            for date, old, new in find_jumps(points, names[0], args.jumps)
        ]
        header = ["Who", "Date", "Field", "From", "To"]
        print("\n".join(table(header, rows)))
        print(f"\n{len(rows)} jumps")
        return 0
    rows = []
    for who, points in series.items():
        if args.changes:
            kept: list[tuple[list[float | None], tuple[Date, Fields]]] = []
            for point in points:
                key = [point[1].get(n) for n in names]
                if not kept or key != kept[-1][0]:
                    kept.append((key, point))
            points = [point for _, point in kept]
        for i, (date, values) in enumerate(points):
            if i % args.every and i != len(points) - 1:
                continue
            cells = [short(values[n]) if n in values else "-" for n in names]
            rows.append([*([who] if with_who else []), fmt_date(date), *cells])
    header = [*(["Who"] if with_who else []), "Date", *names]
    print("\n".join(table(header, rows)))
    print(f"\n{len(rows)} rows")
    return 0


def cmd_spread(args: argparse.Namespace) -> int:
    runs: dict[str, dict[Month, list[float]]] = {}
    for label, path in args.runs:
        values: dict[Month, list[float]] = defaultdict(list)
        for record in iter_records(path):
            kind, rest = split_message(record.message)
            if not kind.startswith(args.label):
                continue
            fields = parse_fields(kind, rest)
            # A country with no states is gone.
            if args.field in fields and fields.get("States", 1) > 0:
                values[record.date[:2]].append(fields[args.field])
        runs[label] = values
    months = sorted(set.intersection(*(set(v) for v in runs.values())))
    if not months:
        print(f'error: no "{args.field}" month shared by every run', file=sys.stderr)
        return 1
    rows = []
    for i, month in enumerate(months):
        if i % args.every and i != len(months) - 1:
            continue
        cells = []
        for values in runs.values():
            sample = values[month]
            q = (
                statistics.quantiles(sample, n=4, method="inclusive")
                if len(sample) > 1
                else sample * 3
            )
            cell = f"{q[0]:.1f}/{q[1]:.1f}/{q[2]:.1f} (n={len(sample)}"
            if args.below is not None:
                cell += (
                    f", {sum(1 for v in sample if v < args.below)} below {args.below:g}"
                )
            cells.append(cell + ")")
        rows.append([fmt_month(month), *cells])
    header = ["Month", *(f"{label} p25/p50/p75" for label in runs)]
    print("\n".join(table(header, rows)))
    return 0


# wars


def war_spells(
    run: Run, min_months: int, min_civilian: float
) -> list[tuple[str, Month, Fields, Month, Fields, int]]:
    """Runs of monthly rows with At War above zero, per tag."""
    by_tag: dict[str, list[tuple[Month, Fields]]] = defaultdict(list)
    for month in sorted(run.months):
        for tag, row in run.months[month].items():
            by_tag[tag].append((month, row))
    spells = []
    for tag, rows in by_tag.items():
        start = None
        for i, (_, row) in enumerate([*rows, ((0, 0), {})]):
            at_war = row.get("At War", 0) > 0
            if at_war and start is None:
                start = i
            elif not at_war and start is not None:
                (m1, first), (m2, final) = rows[start], rows[i - 1]
                if i - start >= min_months and first.get("Civilian", 0) >= min_civilian:
                    spells.append((tag, m1, first, m2, final, i - start))
                start = None
    return sorted(spells, key=lambda spell: (spell[0], spell[1]))


def cmd_wars(args: argparse.Namespace) -> int:
    out: list[str] = []
    for label, path in args.runs:
        run = load_run(label, path, frozenset())
        rows = [
            [
                tag,
                fmt_month(m1),
                fmt_month(m2),
                str(length),
                change(first, final, "Military"),
                change(first, final, "Civilian"),
                change(first, final, "GDP"),
            ]
            for tag, m1, first, m2, final, length in war_spells(
                run, args.min_months, args.min_civilian
            )
        ]
        header = ["Tag", "From", "To", "Months", "Military", "Civilian", "GDP"]
        out += [f"## War spells ({label})", "", *table(header, rows), ""]
        out += wars_section(run, f"Wars ({label})")
    print("\n".join(out))
    return 0


# counts


def count_item(kind: str, record: Record) -> str | None:
    match = _COUNT_KINDS[kind].match(record.message)
    if not match:
        return None
    if kind == "investment":
        return record.who
    if kind == "option" and match[1] is None:
        return f"{match[2]}.{match[3]}"
    return match[1]


def cmd_counts(args: argparse.Namespace) -> int:
    pattern = re.compile(args.match) if args.match else None
    tallies: dict[str, Counter[tuple[str, int]]] = {}
    for label, path in args.runs:
        tally: Counter[tuple[str, int]] = Counter()
        for record in iter_records(path):
            if args.who and record.who != args.who:
                continue
            if args.before and record.date[:2] >= args.before:
                continue
            item = count_item(args.kind, record)
            if item is not None and (not pattern or pattern.search(item)):
                tally[(item, record.date[0])] += 1
        tallies[label] = tally
    if args.by_year:
        out = []
        for label, tally in tallies.items():
            out += [f"## {label}", "", *year_table(tally, args.top), ""]
        print("\n".join(out))
        return 0
    per_run = {label: item_totals(tally) for label, tally in tallies.items()}
    items = set().union(*per_run.values())
    rows = [
        [item, *(str(totals[item]) for totals in per_run.values())]
        for item in sorted(
            items, key=lambda i: (-max(t[i] for t in per_run.values()), i)
        )
        if not args.diff or len({totals[item] for totals in per_run.values()}) > 1
    ]
    note = f"{len(rows) - args.top} more rows" if len(rows) > args.top else ""
    rows = rows[: args.top]
    rows.append(["Total", *(str(sum(totals.values())) for totals in per_run.values())])
    print("\n".join(table([args.kind.capitalize(), *per_run], rows)))
    if note:
        print(f"\n{note} not shown (--top)")
    return 0


def item_totals(tally: Counter[tuple[str, int]]) -> Counter[str]:
    totals: Counter[str] = Counter()
    for (item, _), count in tally.items():
        totals[item] += count
    return totals


def year_table(tally: Counter[tuple[str, int]], top: int) -> list[str]:
    years = sorted({year for _, year in tally})
    totals = item_totals(tally)
    rows = [
        [item, *(str(tally[(item, y)]) for y in years), str(total)]
        for item, total in sorted(totals.items(), key=lambda kv: (-kv[1], kv[0]))[:top]
    ]
    by_year: Counter[int] = Counter()
    for (_, year), count in tally.items():
        by_year[year] += count
    rows.append(["All", *(str(by_year[y]) for y in years), str(sum(by_year.values()))])
    return table(["Item", *map(str, years), "Total"], rows)


# laws


def cmd_laws(args: argparse.Namespace) -> int:
    wanted = split_csv(args.law)
    samples: dict[str, list[tuple[Date, Fields]]] = defaultdict(list)
    for record in iter_records(args.log):
        if args.who and record.who != args.who:
            continue
        kind, rest = split_message(record.message)
        if kind.startswith(_LAWS_PREFIX):
            samples[record.who].append((record.date, law_fields(rest)))
    if not samples:
        print("error: no Spending Laws lines found", file=sys.stderr)
        return 1
    if args.who:
        return print_law_trace(samples[args.who], wanted)
    rows = []
    for name, points in samples.items():
        churn = law_churn(points)
        cats = wanted or list(churn.gap)
        rows.append(
            (
                sum(churn.reversals[c] for c in cats),
                sum(churn.changes[c] for c in cats),
                sum(churn.gap.get(c, 0) for c in cats),
                name,
            )
        )
    rows.sort(key=lambda r: (-r[0], r[3]))
    shown = [[str(r), str(c), f"{g:+.0f}", n] for r, c, g, n in rows[: args.top]]
    print("\n".join(table(["Reversals", "Changes", "End gap", "Country"], shown)))
    print(f"\nCountries with a reversal: {sum(1 for r in rows if r[0])}")
    return 0


def print_law_trace(
    points: Sequence[tuple[Date, Fields]], wanted: Sequence[str]
) -> int:
    cats = list(wanted) or law_categories(points[0][1])
    rows = []
    last_key: list[float | None] | None = None
    for date, fields in points:
        key = [fields.get(name) for cat in cats for name in (cat, f"{cat} Expected")]
        if key == last_key:
            continue
        last_key = key
        cells = [
            "/".join(
                short(fields.get(f"{cat}{suffix}", 0))
                for suffix in ("", " Expected", " Offset")
            )
            for cat in cats
        ]
        rows.append(
            [
                fmt_date(date),
                *cells,
                short(fields.get("Balance Ratio", 0)),
                short(fields.get("AI Balance", 0)),
            ]
        )
    header = ["Date", *(f"{cat} l/e/o" for cat in cats), "Balance Ratio", "AI Balance"]
    print("\n".join(table(header, rows)))
    return 0


# errors and volume


def error_shape(text: str) -> str:
    """Message with file paths, quoted names, country tags and numbers blanked."""
    text = _PATH.sub("<file>", text)
    text = _QUOTED.sub("'_'", text)
    return _DIGITS.sub("#", _TAG.sub("<tag>", text))[:160]


def cmd_errors(args: argparse.Namespace) -> int:
    shapes: Counter[str] = Counter()
    examples: dict[str, str] = {}
    dropped = 0
    for number, line in enumerate(read_lines(args.log), 1):
        text = _ERROR_STAMP.sub("", line.strip())
        if number <= args.start or not text:
            continue
        if any(noise in text for noise in ERROR_NOISE):
            dropped += 1
            continue
        shape = error_shape(text)
        shapes[shape] += 1
        examples.setdefault(shape, text[:300])
    print(
        f"{sum(shapes.values())} lines in {len(shapes)} shapes "
        f"({dropped} known noise lines dropped)"
    )
    for shape, count in shapes.most_common(args.top):
        print(f"{count:6}  {examples[shape]}")
    return 0


def cmd_volume(args: argparse.Namespace) -> int:
    counts: Counter[str] = Counter()
    sizes: Counter[str] = Counter()
    lines = 0
    for line in read_lines(args.log):
        lines += 1
        match = _LINE.search(line)
        body = match.group(5) if match else _STAMPS.sub("", line)
        kind = _VOLUME_DIGITS.sub("#", body)[:60].strip()
        counts[kind] += 1
        sizes[kind] += len(line.encode("utf-8")) + 1
    print(f"{lines:,} lines, {sum(sizes.values()) / 1e6:.1f} MB")
    for kind, size in sizes.most_common(args.top):
        print(f"{size / 1e6:7.2f} MB {counts[kind]:>9,}  {kind}")
    return 0


# CLI


def run_arg(text: str) -> tuple[str, Path]:
    """`LABEL=LOG`, or a bare path labelled by its folder."""
    label, sep, path = text.partition("=")
    if sep and label:
        return label, Path(path)
    return Path(text).resolve().parent.name, Path(text)


def positive_int(text: str) -> int:
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError("must be 1 or more")
    return value


def cutoff_arg(text: str) -> Month:
    """`YYYY` or `YYYY.MM`, as the first month to leave out."""
    try:
        year, _, month = text.partition(".")
        return int(year), int(month or 1)
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"expected YYYY or YYYY.MM: {text}") from error


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Turn HOI4 game.log and error.log files into reports."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def command(name: str, handler: Callable[[argparse.Namespace], int], summary: str):
        cmd = sub.add_parser(name, help=summary, description=summary)
        cmd.set_defaults(handler=handler)
        return cmd

    cmd = command("compare", cmd_compare, "Compare runs at the last month all reached.")
    cmd.add_argument("runs", nargs="+", type=run_arg, metavar="LABEL=LOG")
    cmd.add_argument(
        "--majors", default=DEFAULT_MAJORS, help="tags with their own tables"
    )
    cmd.add_argument(
        "--also", default=DEFAULT_ALSO, help="tags added to the top-20 table"
    )
    cmd.add_argument(
        "--skip", default=DEFAULT_SKIP, help="tags left out of every total"
    )

    cmd = command("series", cmd_series, "One subject's fields over time.")
    cmd.add_argument("log", type=Path)
    cmd.add_argument("who", help='tag or country name, or "*" for every subject')
    cmd.add_argument(
        "--label", default="Monthly Benchmark", help="message label prefix"
    )
    cmd.add_argument("--fields", default="", help="comma list; default is every field")
    cmd.add_argument("--every", type=positive_int, default=1, help="keep every Nth row")
    cmd.add_argument(
        "--changes", action="store_true", help="only rows where a field changed"
    )
    cmd.add_argument(
        "--jumps",
        type=float,
        metavar="STEP",
        help="list steps of STEP or more in the first field that triple the old value",
    )

    cmd = command(
        "spread", cmd_spread, "Quartiles of one field across countries, by month."
    )
    cmd.add_argument("runs", nargs="+", type=run_arg, metavar="LOG")
    cmd.add_argument("field")
    cmd.add_argument(
        "--label", default="Monthly Benchmark", help="message label prefix"
    )
    cmd.add_argument(
        "--every", type=positive_int, default=1, help="keep every Nth month"
    )
    cmd.add_argument(
        "--below", type=float, help="also count countries under this value"
    )

    cmd = command("wars", cmd_wars, "War spells, declarations and capitulations.")
    cmd.add_argument("runs", nargs="+", type=run_arg, metavar="LOG")
    cmd.add_argument("--min-months", type=positive_int, default=3)
    cmd.add_argument(
        "--min-civilian",
        type=float,
        default=3,
        help="civilian factories at the first war month",
    )

    cmd = command(
        "counts", cmd_counts, "Count logged items per run and show the differences."
    )
    cmd.add_argument("runs", nargs="+", type=run_arg, metavar="LABEL=LOG")
    cmd.add_argument("--kind", choices=sorted(_COUNT_KINDS), default="decision")
    cmd.add_argument("--who", help="only this country name")
    cmd.add_argument("--before", type=cutoff_arg, metavar="YYYY[.MM]")
    cmd.add_argument("--match", help="only items matching this regex")
    cmd.add_argument(
        "--diff", action="store_true", help="only rows that differ between runs"
    )
    cmd.add_argument(
        "--by-year", action="store_true", help="one table per run, columns are years"
    )
    cmd.add_argument("--top", type=positive_int, default=50)

    cmd = command(
        "laws", cmd_laws, "Spending law reversals, or one country's law trace."
    )
    cmd.add_argument("log", type=Path)
    cmd.add_argument("--who", help="country name: print its trace instead of a ranking")
    cmd.add_argument("--law", default="", help="comma list of laws; default is all")
    cmd.add_argument("--top", type=positive_int, default=15)

    cmd = command("errors", cmd_errors, "Group error.log by message shape.")
    cmd.add_argument("log", type=Path)
    cmd.add_argument("--top", type=positive_int, default=25)
    cmd.add_argument(
        "--start", type=int, default=0, help="skip lines up to this line number"
    )

    cmd = command("volume", cmd_volume, "Top message kinds in a game.log by bytes.")
    cmd.add_argument("log", type=Path)
    cmd.add_argument("--top", type=positive_int, default=25)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    labels: set[str] = set()
    for label, _ in getattr(args, "runs", ()):
        if label in labels:
            parser.error(f"duplicate run label {label!r}; use distinct LABEL=LOG pairs")
        labels.add(label)
    try:
        if isinstance(sys.stdout, TextIOWrapper):
            sys.stdout.reconfigure(errors="replace")
        return args.handler(args)
    except OSError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
