#!/usr/bin/env python3
"""
focus_overlap_report.py — report focuses that draw in the same cell.

A focus sits at its own `x`/`y` plus the `relative_position_id` chain above it,
plus every `offset` whose trigger passes right now. Branches that never share a
cell in one game state can pile up in another, so overlaps are only meaningful
per scenario: which focuses are completed, and what the date is.

Triggers are evaluated three-valued. An offset is applied only when its trigger
is provably true, and a focus is dropped only when its `allow_branch` is provably
false, so an unrecognised trigger widens the report rather than hiding a clash.

Usage:
    python3 tools/analysis/focus_overlap_report.py
    python3 tools/analysis/focus_overlap_report.py --completed POL_stay_on_track --date 2006.1.1
    python3 tools/analysis/focus_overlap_report.py --region 12,26,0,12 --map
    python3 tools/analysis/focus_overlap_report.py --adjacent --format json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Iterator, List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from shared_utils import (  # noqa: E402
    blank_quoted_strings,
    find_matching_brace,
    strip_comments,
)

DEFAULT_FILE = "common/national_focus/05_poland.txt"

_FOCUS_START = re.compile(r"\b(shared_focus|focus)\s*=\s*\{")
_ID_LINE = re.compile(r"^\s*id\s*=\s*(\S+)", re.M)
_STATEMENT = re.compile(r"([A-Za-z_][A-Za-z0-9_.:@]*)\s*(>=|<=|==|=|>|<)")

Date = Tuple[int, int, int]


def iter_statements(
    body: str,
) -> Iterator[Tuple[str, str, Optional[str], Optional[str]]]:
    """Yield (key, operator, scalar, block) for every statement at depth 0."""
    index = 0
    length = len(body)
    while index < length:
        if body[index] in "{}":
            index += 1
            continue
        match = _STATEMENT.match(body, index)
        if not match:
            index += 1
            continue
        key, operator = match.group(1), match.group(2)
        cursor = match.end()
        while cursor < length and body[cursor] in " \t\r\n":
            cursor += 1
        if cursor < length and body[cursor] == "{":
            close = find_matching_brace(body, cursor)
            if close == -1:
                return
            yield key, operator, None, body[cursor + 1 : close]
            index = close + 1
            continue
        stop = cursor
        while stop < length and body[stop] not in " \t\r\n{}":
            stop += 1
        yield key, operator, body[cursor:stop], None
        index = stop


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


@dataclass
class Offset:
    dx: int = 0
    dy: int = 0
    trigger: str = ""


@dataclass
class Focus:
    id: str
    line: int
    kind: str
    x: int = 0
    y: int = 0
    relative_to: Optional[str] = None
    allow_branch: Optional[str] = None
    offsets: List[Offset] = field(default_factory=list)
    prereq_groups: List[List[str]] = field(default_factory=list)


@dataclass
class Scenario:
    tag: str = "POL"
    completed: frozenset = frozenset()
    date: Optional[Date] = None


def parse_date(value: str) -> Date:
    parts = value.split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        raise ValueError(f"expected a YYYY.M.D date, got {value!r}")
    return int(parts[0]), int(parts[1]), int(parts[2])


def read_script(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        return blank_quoted_strings(strip_comments(handle.read()))


def parse_focus_file(text: str) -> Dict[str, Focus]:
    """Return every focus in *text*, keyed by id and in file order."""
    focuses: Dict[str, Focus] = {}
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
        if not id_match or id_match.group(1) in focuses:
            continue
        focuses[id_match.group(1)] = _build_focus(
            id_match.group(1), match.group(1), line_of(text, match.start()), body
        )


def _build_focus(focus_id: str, kind: str, line: int, body: str) -> Focus:
    focus = Focus(id=focus_id, line=line, kind=kind)
    for key, _operator, scalar, block in iter_statements(body):
        if key == "x" and scalar is not None:
            focus.x = int(scalar)
        elif key == "y" and scalar is not None:
            focus.y = int(scalar)
        elif key == "relative_position_id" and scalar is not None:
            focus.relative_to = scalar
        elif key == "allow_branch" and block is not None:
            focus.allow_branch = block
        elif key == "offset" and block is not None:
            focus.offsets.append(_build_offset(block))
        elif key == "prerequisite" and block is not None:
            group = [
                value
                for name, _op, value, _nested in iter_statements(block)
                if name == "focus" and value is not None
            ]
            if group:
                focus.prereq_groups.append(group)
    return focus


def _build_offset(block: str) -> Offset:
    offset = Offset()
    for key, _operator, scalar, nested in iter_statements(block):
        if key == "x" and scalar is not None:
            offset.dx = int(scalar)
        elif key == "y" and scalar is not None:
            offset.dy = int(scalar)
        elif key == "trigger" and nested is not None:
            offset.trigger = nested
    return offset


def evaluate(body: str, scenario: Scenario) -> Optional[bool]:
    """Three-valued AND over the statements of a trigger body."""
    unknown = False
    for key, operator, scalar, block in iter_statements(body):
        value = _evaluate_statement(key, operator, scalar, block, scenario)
        if value is False:
            return False
        if value is None:
            unknown = True
    return None if unknown else True


def _evaluate_statement(
    key: str,
    operator: str,
    scalar: Optional[str],
    block: Optional[str],
    scenario: Scenario,
) -> Optional[bool]:
    if block is not None:
        if key == "OR":
            return _evaluate_or(block, scenario)
        if key == "NOT":
            return _invert(evaluate(block, scenario))
        if key in ("AND", "hidden_trigger", "custom_trigger_tooltip"):
            return evaluate(block, scenario)
        return None
    if scalar is None:
        return None
    if key == "has_completed_focus":
        return scalar in scenario.completed
    if key == "date":
        return _evaluate_date(operator, scalar, scenario)
    if key in ("tag", "original_tag"):
        return scalar == scenario.tag
    if key == "always":
        return scalar == "yes"
    return None


def _evaluate_or(block: str, scenario: Scenario) -> Optional[bool]:
    unknown = False
    for key, operator, scalar, nested in iter_statements(block):
        value = _evaluate_statement(key, operator, scalar, nested, scenario)
        if value is True:
            return True
        if value is None:
            unknown = True
    return None if unknown else False


def _evaluate_date(operator: str, scalar: str, scenario: Scenario) -> Optional[bool]:
    if scenario.date is None:
        return None
    try:
        threshold = parse_date(scalar)
    except ValueError:
        return None
    if operator == ">":
        return scenario.date > threshold
    if operator == "<":
        return scenario.date < threshold
    return None


def _invert(value: Optional[bool]) -> Optional[bool]:
    return None if value is None else not value


def resolve_positions(
    focuses: Dict[str, Focus], scenario: Scenario
) -> Dict[str, Tuple[int, int]]:
    positions: Dict[str, Tuple[int, int]] = {}

    def resolve(focus_id: str, seen: frozenset) -> Tuple[int, int]:
        focus = focuses[focus_id]
        x, y = focus.x, focus.y
        for offset in focus.offsets:
            if evaluate(offset.trigger, scenario) is True:
                x += offset.dx
                y += offset.dy
        parent = focus.relative_to
        if parent in focuses and parent not in seen:
            parent_x, parent_y = resolve(parent, seen | {focus_id})
            return parent_x + x, parent_y + y
        return x, y

    for focus_id in focuses:
        positions[focus_id] = resolve(focus_id, frozenset())
    return positions


def resolve_visibility(
    focuses: Dict[str, Focus], scenario: Scenario
) -> Dict[str, bool]:
    """A focus is hidden when its own `allow_branch` fails, and so is everything
    that can only be reached through it."""
    visible: Dict[str, bool] = {}

    def resolve(focus_id: str, stack: frozenset) -> bool:
        if focus_id in visible:
            return visible[focus_id]
        if focus_id in stack or focus_id not in focuses:
            return True
        focus = focuses[focus_id]
        shown = True
        if focus.allow_branch is not None:
            shown = evaluate(focus.allow_branch, scenario) is not False
        if shown:
            for group in focus.prereq_groups:
                if not any(resolve(parent, stack | {focus_id}) for parent in group):
                    shown = False
                    break
        visible[focus_id] = shown
        return shown

    for focus_id in focuses:
        resolve(focus_id, frozenset())
    return visible


Region = Tuple[int, int, int, int]


def parse_region(value: str) -> Region:
    parts = value.split(",")
    if len(parts) != 4:
        raise ValueError(f"expected x0,x1,y0,y1, got {value!r}")
    x0, x1, y0, y1 = (int(part) for part in parts)
    return x0, x1, y0, y1


def in_region(position: Tuple[int, int], region: Optional[Region]) -> bool:
    if region is None:
        return True
    x0, x1, y0, y1 = region
    return x0 <= position[0] <= x1 and y0 <= position[1] <= y1


def find_collisions(
    focuses: Dict[str, Focus],
    positions: Dict[str, Tuple[int, int]],
    visible: Dict[str, bool],
    region: Optional[Region],
) -> List[Tuple[Tuple[int, int], List[str]]]:
    cells: Dict[Tuple[int, int], List[str]] = defaultdict(list)
    for focus_id in focuses:
        if visible[focus_id] and in_region(positions[focus_id], region):
            cells[positions[focus_id]].append(focus_id)
    return sorted((cell, ids) for cell, ids in cells.items() if len(ids) > 1)


def find_adjacent(
    focuses: Dict[str, Focus],
    positions: Dict[str, Tuple[int, int]],
    visible: Dict[str, bool],
    region: Optional[Region],
) -> List[Tuple[int, str, str]]:
    rows: Dict[int, List[Tuple[int, str]]] = defaultdict(list)
    for focus_id in focuses:
        if visible[focus_id] and in_region(positions[focus_id], region):
            x, y = positions[focus_id]
            rows[y].append((x, focus_id))
    pairs: List[Tuple[int, str, str]] = []
    for y, entries in sorted(rows.items()):
        entries.sort()
        for left, right in zip(entries, entries[1:]):
            if right[0] - left[0] == 1:
                pairs.append((y, left[1], right[1]))
    return pairs


def build_report(
    focuses: Dict[str, Focus],
    positions: Dict[str, Tuple[int, int]],
    visible: Dict[str, bool],
    scenario: Scenario,
    region: Optional[Region],
    adjacent: bool,
    show_map: bool,
) -> dict:
    def entry(focus_id: str) -> dict:
        return {
            "id": focus_id,
            "line": focuses[focus_id].line,
            "x": positions[focus_id][0],
            "y": positions[focus_id][1],
        }

    report = {
        "scenario": {
            "tag": scenario.tag,
            "completed": sorted(scenario.completed),
            "date": (
                ".".join(str(part) for part in scenario.date) if scenario.date else None
            ),
        },
        "focuses": len(focuses),
        "visible": sum(1 for shown in visible.values() if shown),
        "collisions": [
            {"x": cell[0], "y": cell[1], "focuses": [entry(i) for i in ids]}
            for cell, ids in find_collisions(focuses, positions, visible, region)
        ],
    }
    if adjacent:
        report["adjacent"] = [
            {"y": y, "left": entry(left), "right": entry(right)}
            for y, left, right in find_adjacent(focuses, positions, visible, region)
        ]
    if show_map:
        shown = [i for i in focuses if visible[i] and in_region(positions[i], region)]
        report["map"] = [
            entry(i)
            for i in sorted(shown, key=lambda i: (positions[i][1], positions[i][0]))
        ]
    return report


def format_text(report: dict) -> str:
    scenario = report["scenario"]
    lines = [
        "Scenario: tag={} completed={} date={}".format(
            scenario["tag"],
            ",".join(scenario["completed"]) or "-",
            scenario["date"] or "-",
        ),
        "Focuses: {} total, {} visible".format(report["focuses"], report["visible"]),
        "",
        "Overlapping cells ({}):".format(len(report["collisions"])),
    ]
    for collision in report["collisions"]:
        head = "  ({},{})".format(collision["x"], collision["y"])
        for focus in collision["focuses"]:
            lines.append("{:<12} {} (l{})".format(head, focus["id"], focus["line"]))
            head = ""
    if "adjacent" in report:
        lines.append("")
        lines.append("Adjacent columns ({}):".format(len(report["adjacent"])))
        for pair in report["adjacent"]:
            lines.append(
                "  y={:<4} x={} {} (l{})  <->  x={} {} (l{})".format(
                    pair["y"],
                    pair["left"]["x"],
                    pair["left"]["id"],
                    pair["left"]["line"],
                    pair["right"]["x"],
                    pair["right"]["id"],
                    pair["right"]["line"],
                )
            )
    if "map" in report:
        lines.append("")
        lines.append("Visible focuses ({}):".format(len(report["map"])))
        for focus in report["map"]:
            lines.append(
                "  ({:>3},{:>3}) {} (l{})".format(
                    focus["x"], focus["y"], focus["id"], focus["line"]
                )
            )
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Report focuses that share a cell in a given game state."
    )
    parser.add_argument("--file", default=DEFAULT_FILE, help="focus tree file to read")
    parser.add_argument("--tag", default="POL", help="country the tree is read as")
    parser.add_argument(
        "--completed",
        action="append",
        default=[],
        metavar="FOCUS_ID",
        help="focus treated as completed (repeatable)",
    )
    parser.add_argument("--date", help="in-game date, e.g. 2006.1.1")
    parser.add_argument("--region", help="limit output to x0,x1,y0,y1")
    parser.add_argument(
        "--adjacent",
        action="store_true",
        help="also list visible focuses one column apart",
    )
    parser.add_argument(
        "--map", action="store_true", help="list every visible focus and its cell"
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    try:
        scenario = Scenario(
            tag=args.tag,
            completed=frozenset(args.completed),
            date=parse_date(args.date) if args.date else None,
        )
        region = parse_region(args.region) if args.region else None
    except ValueError as error:
        parser.error(str(error))

    focuses = parse_focus_file(read_script(args.file))
    positions = resolve_positions(focuses, scenario)
    visible = resolve_visibility(focuses, scenario)
    report = build_report(
        focuses, positions, visible, scenario, region, args.adjacent, args.map
    )
    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(format_text(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
