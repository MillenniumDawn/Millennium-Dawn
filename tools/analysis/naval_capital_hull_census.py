#!/usr/bin/env python3
"""
naval_capital_hull_census.py — capital_ship hull census per starting naval OOB.

For every history/units/*_naval_mtg.txt file, counts hulls by sub_unit
`definition` and reports how many are capital_ship-typed, per tag. The
capital set is read from common/units/MD_naval_units.txt, not hardcoded,
so a later archetype change is picked up automatically.

Usage:
    python3 tools/analysis/naval_capital_hull_census.py
    python3 tools/analysis/naval_capital_hull_census.py --zero-only
    python3 tools/analysis/naval_capital_hull_census.py --format json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Set

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from shared_utils import find_matching_brace, read_script, strip_comments  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NAVAL_UNITS_FILE = os.path.join(REPO_ROOT, "common", "units", "MD_naval_units.txt")
UNITS_DIR = os.path.join(REPO_ROOT, "history", "units")

_SUB_UNIT_HEADER = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\{")
_TYPE = re.compile(r"\btype\s*=\s*\{\s*([^}]*)\}")
_DEFINITION = re.compile(r"\bdefinition\s*=\s*([A-Za-z_][A-Za-z0-9_]*)")
_TAG_FROM_FILENAME = re.compile(r"^([A-Za-z0-9]+)_")


def capital_ship_definitions(path: str = NAVAL_UNITS_FILE) -> List[str]:
    """Sub_unit names in MD_naval_units.txt whose `type` includes capital_ship."""
    text = strip_comments(read_script(path))
    sub_units_start = text.index("sub_units")
    body_open = text.index("{", sub_units_start)
    body_end = find_matching_brace(text, body_open)
    body = text[body_open + 1 : body_end]

    capital = []
    pos = 0
    while True:
        match = _SUB_UNIT_HEADER.search(body, pos)
        if not match:
            break
        name = match.group(1)
        block_open = match.end() - 1
        block_end = find_matching_brace(body, block_open)
        block = body[block_open : block_end + 1]
        type_match = _TYPE.search(block)
        if type_match and "capital_ship" in type_match.group(1).split():
            capital.append(name)
        pos = block_end + 1
    return capital


@dataclass
class TagCensus:
    tag: str
    total: int = 0
    capital: int = 0
    by_definition: Dict[str, int] = field(default_factory=dict)


def census_file(path: str, capital_defs: Set[str]) -> TagCensus:
    filename = os.path.basename(path)
    tag_match = _TAG_FROM_FILENAME.match(filename)
    tag = tag_match.group(1) if tag_match else filename
    text = strip_comments(read_script(path))

    result = TagCensus(tag=tag)
    for match in _DEFINITION.finditer(text):
        definition = match.group(1)
        result.total += 1
        result.by_definition[definition] = result.by_definition.get(definition, 0) + 1
        if definition in capital_defs:
            result.capital += 1
    return result


def run_census(
    units_dir: str = UNITS_DIR, naval_units_file: str = NAVAL_UNITS_FILE
) -> List[TagCensus]:
    capital_defs = set(capital_ship_definitions(naval_units_file))
    results = []
    for filename in sorted(os.listdir(units_dir)):
        if not filename.endswith("_naval_mtg.txt"):
            continue
        results.append(census_file(os.path.join(units_dir, filename), capital_defs))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--zero-only",
        action="store_true",
        help="Only list navies with a naval OOB and zero capital hulls.",
    )
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    results = run_census()
    with_oob = [r for r in results if r.total > 0]
    zero_capital = [r for r in with_oob if r.capital == 0]

    if args.format == "json":
        payload = {
            "navies_with_oob": len(with_oob),
            "zero_capital_count": len(zero_capital),
            "zero_capital_tags": [r.tag for r in zero_capital],
            "tags": [
                {
                    "tag": r.tag,
                    "total": r.total,
                    "capital": r.capital,
                    "by_definition": r.by_definition,
                }
                for r in (zero_capital if args.zero_only else results)
            ],
        }
        print(json.dumps(payload, indent=2))
        return 0

    print(f"Navies with a naval OOB: {len(with_oob)}")
    print(f"Navies with zero capital hulls: {len(zero_capital)} of {len(with_oob)}")
    print()
    rows = zero_capital if args.zero_only else results
    for r in rows:
        print(f"{r.tag:4s} total={r.total:3d} capital={r.capital:3d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
