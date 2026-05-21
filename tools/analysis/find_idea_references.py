#!/usr/bin/env python3
"""
find_idea_references.py — Find unreferenced ideas from a given ideas file.

Usage:
    python3 tools/find_idea_references.py common/ideas/Greek.txt
    python3 tools/find_idea_references.py common/ideas/American.txt --show-all
"""

import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _reference_finder import build_parser, run_reference_search  # noqa: E402

SEARCH_DIRS = [
    "common/events",
    "common/decisions",
    "common/national_focus",
    "history/countries",
    "common/scripted_effects",
    "events",
    "common/on_actions",
    "common/focuses",
    "common/country_leader",
    "common/ideas",
]

PATTERNS = [
    "add_ideas",
    "remove_ideas",
    "has_idea",
    "swap_ideas",
    "modify_ideas",
    "add_timed_idea",
    "remove_timed_idea",
    r"idea.*=",
    r"=\s*idea",
]

SKIP_KEYWORDS = {
    "ideas",
    "country",
    "hidden_ideas",
    "modifier",
    "allowed",
    "allowed_civil_war",
    "cancel",
    "on_add",
    "on_remove",
    "equipment_bonus",
    "if",
    "limit",
    "OR",
    "AND",
    "NOT",
    "picture",
    "name",
}


def extract_idea_names(filepath: Path) -> list[str]:
    """Extract idea names from an ideas file."""
    names: list[str] = []
    pattern = re.compile(r"^\s+([A-Za-z][A-Za-z0-9_]+)\s*=\s*\{\s*$")
    tag_pattern = re.compile(r"^[A-Z]{2,4}$")

    depth = 0
    for line in filepath.read_text(encoding="utf-8", errors="replace").splitlines():
        opens = line.count("{")
        closes = line.count("}")
        # Idea names are always at depth 2: ideas = { category = { idea_name = {
        if opens > closes and depth == 2:
            m = pattern.match(line)
            if m:
                name = m.group(1)
                if name not in SKIP_KEYWORDS and not tag_pattern.match(name):
                    if name not in names:
                        names.append(name)
        depth += opens - closes
    return names


def make_idea_searcher(search_dirs: list[Path]):
    """Build a closure that searches for one idea name across the given dirs."""

    def search(idea: str) -> list[tuple[str, int, str]]:
        refs: list[tuple[str, int, str]] = []
        for search_dir in search_dirs:
            if not search_dir.is_dir():
                continue
            for txt_file in search_dir.rglob("*.txt"):
                try:
                    lines = txt_file.read_text(
                        encoding="utf-8", errors="replace"
                    ).splitlines()
                except OSError:
                    continue
                for i, line in enumerate(lines, 1):
                    if idea not in line:
                        continue
                    if any(re.search(p, line) for p in PATTERNS):
                        rel = txt_file.relative_to(REPO_ROOT)
                        refs.append((str(rel), i, line.strip()))
        return refs

    return search


def main() -> None:
    parser = build_parser(
        description="Find unreferenced ideas from an ideas file.",
        source_arg="ideas_file",
        source_help="Path to the ideas file to analyze",
    )
    args = parser.parse_args()

    ideas_file = Path(args.ideas_file)
    search_dirs = [REPO_ROOT / d for d in SEARCH_DIRS]

    run_reference_search(
        source_file=ideas_file,
        search_dirs=search_dirs,
        repo_root=REPO_ROOT,
        analyzer_title="IDEA REFERENCE ANALYZER",
        subject_singular="idea",
        subject_plural="ideas",
        extract_names=extract_idea_names,
        search_for_references=make_idea_searcher(search_dirs),
        show_all=args.show_all,
        no_report=args.no_report,
        report_prefix_all="all_idea_references",
        report_prefix_unref="unreferenced_ideas",
        report_title_all="All Idea References",
        report_title_unref="Unreferenced Ideas",
    )


if __name__ == "__main__":
    main()
