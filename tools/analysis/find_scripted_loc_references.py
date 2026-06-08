#!/usr/bin/env python3
"""
find_scripted_loc_references.py — Find unreferenced scripted localisation names.

Usage:
    python3 tools/find_scripted_loc_references.py common/scripted_localisation/LBA_scripted_localisation.txt
    python3 tools/find_scripted_loc_references.py common/scripted_localisation/ENG_scripted_localisation.txt --show-all
    python3 tools/find_scripted_loc_references.py common/scripted_localisation/BRM_scripted_localisation.txt --no-report
"""

import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _reference_finder import build_parser, run_reference_search  # noqa: E402

SEARCH_DIRS = [
    "interface",
    "localisation",
    "events",
    "common/decisions",
    "common/national_focus",
    "common/scripted_effects",
    "common/on_actions",
    "common/focuses",
    "common/scripted_guis",
    "gfx/interface",
]


def extract_scripted_loc_names(filepath: Path) -> list[str]:
    """Extract scripted localisation names (name = X) from a scripted_localisation file."""
    names: list[str] = []
    pattern = re.compile(r"^\s*name\s*=\s*([A-Za-z][A-Za-z0-9_]*)\s*$")
    for line in filepath.read_text(encoding="utf-8", errors="replace").splitlines():
        m = pattern.match(line)
        if m and m.group(1) not in names:
            names.append(m.group(1))
    return names


def make_scripted_loc_searcher(search_dirs: list[Path], source_file: Path):
    """Build a closure that searches for one scripted loc name across the given dirs.

    Skips the definition line in the source file. In localisation directories,
    only counts `[name]`-bracketed references.
    """

    def search(name: str) -> list[tuple[str, int, str]]:
        refs: list[tuple[str, int, str]] = []
        definition_pattern = re.compile(rf"^\s*name\s*=\s*{re.escape(name)}\s*$")
        for search_dir in search_dirs:
            if not search_dir.is_dir():
                continue
            is_loc_dir = "localisation" in search_dir.name
            globs = ["*.yml"] if is_loc_dir else ["*.txt", "*.gui", "*.gfx", "*.yml"]

            for glob_pattern in globs:
                for filepath in search_dir.rglob(glob_pattern):
                    try:
                        lines = filepath.read_text(
                            encoding="utf-8", errors="replace"
                        ).splitlines()
                    except OSError:
                        continue
                    for i, line in enumerate(lines, 1):
                        if name not in line:
                            continue
                        if filepath == source_file and definition_pattern.match(line):
                            continue
                        if is_loc_dir and f"[{name}]" not in line:
                            continue
                        rel = filepath.relative_to(REPO_ROOT)
                        refs.append((str(rel), i, line.strip()))
        return refs

    return search


def main() -> None:
    parser = build_parser(
        description="Find unreferenced scripted localisation names.",
        source_arg="scripted_loc_file",
        source_help="Path to the scripted localisation file to analyze",
    )
    args = parser.parse_args()

    source_file = Path(args.scripted_loc_file).resolve()
    search_dirs = [REPO_ROOT / d for d in SEARCH_DIRS]

    run_reference_search(
        source_file=source_file,
        search_dirs=search_dirs,
        repo_root=REPO_ROOT,
        analyzer_title="SCRIPTED LOCALISATION REFERENCE ANALYZER",
        subject_singular="scripted localisation name",
        subject_plural="scripted localisation names",
        extract_names=extract_scripted_loc_names,
        search_for_references=make_scripted_loc_searcher(search_dirs, source_file),
        show_all=args.show_all,
        no_report=args.no_report,
        report_prefix_all="all_scripted_loc_references",
        report_prefix_unref="unreferenced_scripted_loc",
        report_title_all="All Scripted Localisation References",
        report_title_unref="Unreferenced Scripted Localisation",
    )


if __name__ == "__main__":
    main()
