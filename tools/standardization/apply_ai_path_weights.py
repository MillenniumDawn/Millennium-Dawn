#!/usr/bin/env python3
"""
apply_ai_path_weights.py — write the AI path modifiers into a focus tree.

Takes a mapping of focus id -> ownership group and rewrites only the path
modifiers inside each focus's ai_will_do block, leaving base, ordering and every
unrelated modifier (bankruptcy, can_staff, ai_is_threatened) untouched.

Mapping format (one directive per line, `#` comments allowed in the map only):

    group historical owner=DEN_ai_historical_path not=DEN_ai_not_historical_path
    group socialist owner_flag=DEN_SOCIALIST_FOCUS_PATH not=DEN_ai_not_socialist_path
    boost 25

    DEN_join_the_euro       historical
    DEN_red_bloc            socialist 150
    DEN_army_reform         -

Usage:
    python3 tools/standardization/apply_ai_path_weights.py --tag DEN --map plan.txt
    python3 tools/standardization/apply_ai_path_weights.py --tag DEN --map - --dry-run
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

_TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, _TOOLS)
sys.path.insert(0, os.path.join(_TOOLS, "analysis"))

from ai_path_report import resolve_focus_file  # noqa: E402
from common_utils import code_of_line, find_block_span  # noqa: E402
from shared_utils import atomic_write_text  # noqa: E402

GUARD_TOKENS = ("can_staff_an_", "bankruptcy_incoming_collapse", "ai_is_threatened")
SHARED_MARKERS = ("_shared.txt", "shared_focus")

_TRIGGER_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_FOCUS_OPEN = re.compile(r"^([ \t]*)(focus|shared_focus|joint_focus)\s*=\s*\{")
_ID_LINE = re.compile(r"^[ \t]*id\s*=\s*(\S+)")
_AI_WILL_DO = re.compile(r"^([ \t]*)ai_will_do\s*=\s*\{")
_MODIFIER_OPEN = re.compile(r"^[ \t]*modifier\s*=\s*\{")
_BASE_LINE = re.compile(r"^[ \t]*(base|factor)\s*=\s*")


class MappingError(Exception):
    pass


@dataclass
class Group:
    name: str
    owner: str
    kill: str


@dataclass
class Mapping:
    groups: Dict[str, Group]
    assignments: Dict[str, Tuple[Optional[str], float]]
    default_boost: float


def parse_mapping(text: str) -> Mapping:
    groups: Dict[str, Group] = {}
    assignments: Dict[str, Tuple[Optional[str], float]] = {}
    default_boost = 25.0
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        if parts[0] == "group":
            groups[parts[1]] = _parse_group(parts, number)
        elif parts[0] == "boost":
            default_boost = _number(parts[1], number)
        elif parts[1] == "-":
            assignments[parts[0]] = (None, 0.0)
        else:
            boost = _number(parts[2], number) if len(parts) > 2 else default_boost
            assignments[parts[0]] = (parts[1], boost)
    for focus_id, (group, _boost) in assignments.items():
        if group is not None and group not in groups:
            raise MappingError(focus_id + " names undeclared group " + group)
    return Mapping(groups=groups, assignments=assignments, default_boost=default_boost)


def _parse_group(parts: Sequence[str], number: int) -> Group:
    fields = dict(part.split("=", 1) for part in parts[2:] if "=" in part)
    owner = fields.get("owner")
    owner_flag = fields.get("owner_flag")
    kill = fields.get("not")
    if not kill or not (owner or owner_flag):
        raise MappingError(
            "line {}: group needs owner/owner_flag and not".format(number)
        )
    for value in (owner, owner_flag, kill):
        if value and not _TRIGGER_NAME.match(value):
            raise MappingError(
                "line {}: '{}' is not a trigger name".format(number, value)
            )
    owner_line = (
        "has_global_flag = " + owner_flag if owner_flag else str(owner) + " = yes"
    )
    return Group(name=parts[1], owner=owner_line, kill=kill + " = yes")


def _number(raw: str, number: int) -> float:
    try:
        return float(raw)
    except ValueError:
        raise MappingError("line {}: '{}' is not a number".format(number, raw))


def is_path_modifier(block: str, tag: str) -> bool:
    """True when a modifier exists only to route this country's AI paths.

    A guard modifier is never path-owned even when it mentions a flag —
    validate_focus_tree scans for those tokens literally and stops recognising
    a guard that has been folded into something else.
    """
    if any(token in block for token in GUARD_TOKENS):
        return False
    if re.search(r"\b" + tag + r"_\w+_FOCUS_PATH\b", block):
        return True
    if re.search(r"\b" + tag + r"_ai_[a-z0-9_]*path\b", block):
        return True
    if "is_historical_focus_on" in block and re.search(r"\bfactor\s*=\s*0\b", block):
        return True
    return False


def find_focus_spans(lines: Sequence[str]) -> Dict[str, Tuple[int, int]]:
    """Map focus id -> (opening line, closing line) for every focus block."""
    spans: Dict[str, Tuple[int, int]] = {}
    duplicates: List[str] = []
    index = 0
    while index < len(lines):
        match = _FOCUS_OPEN.match(code_of_line(lines[index]))
        if not match:
            index += 1
            continue
        open_col = code_of_line(lines[index]).index("{")
        end = find_block_span(list(lines), index, open_col)
        if end is None:
            raise MappingError("unbalanced braces at line {}".format(index + 1))
        focus_id = None
        for cursor in range(index + 1, end[0]):
            id_match = _ID_LINE.match(code_of_line(lines[cursor]))
            if id_match:
                focus_id = id_match.group(1)
                break
        if focus_id:
            if focus_id in spans:
                duplicates.append(focus_id)
            spans[focus_id] = (index, end[0])
        index = end[0] + 1
    if duplicates:
        raise MappingError("duplicate focus ids: " + ", ".join(sorted(set(duplicates))))
    return spans


def rebuild_block(
    lines: Sequence[str],
    start: int,
    end: int,
    group: Optional[Group],
    boost: float,
    tag: str,
) -> Tuple[List[str], List[str]]:
    """Return (new ai_will_do lines, removed modifier descriptions)."""
    indent = _AI_WILL_DO.match(code_of_line(lines[start])).group(1)
    inner = indent + "\t"
    kept: List[str] = []
    removed: List[str] = []
    base_line = inner + "base = 1"
    if start == end:
        code = code_of_line(lines[start])
        body_text = code[code.index("{") + 1 : code.rindex("}")].strip()
        if "{" in body_text:
            raise MappingError(
                "inline ai_will_do with a nested block at line {}".format(start + 1)
            )
        if body_text:
            if _BASE_LINE.match(body_text):
                base_line = inner + body_text.replace("factor = ", "base = ", 1)
            else:
                kept.append(inner + body_text)
    cursor = start + 1
    while cursor < end:
        code = code_of_line(lines[cursor])
        if _BASE_LINE.match(code):
            base_line = inner + code.strip().replace("factor = ", "base = ", 1)
            cursor += 1
            continue
        if _MODIFIER_OPEN.match(code):
            open_col = code.index("{")
            span = find_block_span(list(lines), cursor, open_col)
            if span is None:
                raise MappingError("unbalanced modifier at line {}".format(cursor + 1))
            block_lines = list(lines[cursor : span[0] + 1])
            block = "".join(code_of_line(line) for line in block_lines)
            if is_path_modifier(block, tag):
                removed.append(" ".join(block.split()))
            else:
                kept.extend(line.rstrip("\r\n") for line in block_lines)
            cursor = span[0] + 1
            continue
        if code.strip():
            kept.append(lines[cursor].rstrip("\r\n"))
        cursor += 1

    body = [indent + "ai_will_do = {", base_line] + kept
    if group is not None:
        body.append(
            inner + "modifier = {{ factor = {} {} }}".format(_fmt(boost), group.owner)
        )
        body.append(inner + "modifier = {{ factor = 0 {} }}".format(group.kill))
    body.append(indent + "}")
    return body, removed


def _fmt(value: float) -> str:
    return str(int(value)) if value == int(value) else str(value)


def apply(
    lines: Sequence[str], mapping: Mapping, tag: str
) -> Tuple[List[str], List[str]]:
    spans = find_focus_spans(lines)
    missing = sorted(set(mapping.assignments) - set(spans))
    if missing:
        raise MappingError("focus ids not in this file: " + ", ".join(missing))
    output = list(lines)
    notes: List[str] = []
    for focus_id in sorted(mapping.assignments, key=lambda key: -spans[key][0]):
        group_name, boost = mapping.assignments[focus_id]
        group = mapping.groups[group_name] if group_name else None
        start, end = spans[focus_id]
        block = _find_ai_will_do(output, start, end)
        if block is None:
            indent = re.match(r"^[ \t]*", output[start]).group(0) + "\t"
            body = new_block(indent, group, boost)
            output[end:end] = [line + "\n" for line in body]
            removed: List[str] = []
        else:
            body, removed = rebuild_block(output, block[0], block[1], group, boost, tag)
            output[block[0] : block[1] + 1] = [line + "\n" for line in body]
        for entry in removed:
            notes.append(focus_id + ": removed " + entry)
    return output, notes


def new_block(indent: str, group: Optional[Group], boost: float) -> List[str]:
    body = [indent + "ai_will_do = {", indent + "\tbase = 1"]
    if group is not None:
        body.append(
            indent
            + "\tmodifier = {{ factor = {} {} }}".format(_fmt(boost), group.owner)
        )
        body.append(indent + "\tmodifier = {{ factor = 0 {} }}".format(group.kill))
    body.append(indent + "}")
    return body


def _find_ai_will_do(
    lines: Sequence[str], start: int, end: int
) -> Optional[Tuple[int, int]]:
    for cursor in range(start + 1, end):
        code = code_of_line(lines[cursor])
        match = _AI_WILL_DO.match(code)
        if not match:
            continue
        span = find_block_span(list(lines), cursor, code.index("{"))
        if span is None:
            raise MappingError("unbalanced ai_will_do at line {}".format(cursor + 1))
        return cursor, span[0]
    return None


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Apply AI path ai_will_do modifiers from a mapping (issue #3162)."
    )
    parser.add_argument("--tag", required=True, help="Three-letter country tag")
    parser.add_argument("--map", required=True, help="Mapping file, or - for stdin")
    parser.add_argument("--file", help="Focus file (default: resolved from --tag)")
    parser.add_argument(
        "--path", default=".", help="Mod root (default: current directory)"
    )
    parser.add_argument("--dry-run", action="store_true", help="Report without writing")
    args = parser.parse_args(argv)

    tag = args.tag.upper()
    raw = sys.stdin.read() if args.map == "-" else _read(args.map)
    try:
        mapping = parse_mapping(raw)
    except MappingError as error:
        print("mapping error: {}".format(error), file=sys.stderr)
        return 1

    target = args.file or resolve_focus_file(args.path, tag)
    if any(marker in os.path.basename(target) for marker in SHARED_MARKERS):
        print("refusing to gate a shared focus file: " + target, file=sys.stderr)
        return 1

    with open(target, "r", encoding="utf-8-sig", errors="strict") as handle:
        lines = handle.readlines()

    try:
        output, notes = apply(lines, mapping, tag)
        verify, _ = apply(output, mapping, tag)
    except MappingError as error:
        print("error: {}".format(error), file=sys.stderr)
        return 1
    if verify != output:
        print("error: rewrite is not idempotent, refusing to write", file=sys.stderr)
        return 1

    owned = sum(1 for group, _ in mapping.assignments.values() if group)
    print(
        "{}: {} focuses re-owned, {} un-owned, {} path modifiers replaced".format(
            os.path.basename(target),
            owned,
            len(mapping.assignments) - owned,
            len(notes),
        )
    )
    for note in notes:
        print("  " + note)
    if args.dry_run:
        print("dry run: nothing written")
        return 0
    atomic_write_text(target, "".join(output))
    return 0


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8-sig", errors="replace") as handle:
        return handle.read()


if __name__ == "__main__":
    raise SystemExit(main())
