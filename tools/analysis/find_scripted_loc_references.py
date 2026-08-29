#!/usr/bin/env python3
"""
find_scripted_loc_references.py — Find unreferenced scripted localisation names.

Usage:
    python3 tools/find_scripted_loc_references.py common/scripted_localisation/LBA_scripted_localisation.txt
    python3 tools/find_scripted_loc_references.py common/scripted_localisation/ENG_scripted_localisation.txt --show-all
    python3 tools/find_scripted_loc_references.py common/scripted_localisation/BRM_scripted_localisation.txt --no-report
"""

import re
from pathlib import Path

from _shared import (  # noqa: E402
    REPO_ROOT,
    compile_token_regex,
    configure_import_paths,
    iter_existing_dirs,
    iter_readable_files,
)

configure_import_paths()

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
    """Build a closure that scans each candidate file once for all names."""

    def record_file(refs, token_re, filepath, lines, is_loc_dir):
        rel = str(filepath.relative_to(REPO_ROOT))
        for line_number, line in enumerate(lines, 1):
            for name in dict.fromkeys(token_re.findall(line)):
                if filepath == source_file and re.fullmatch(
                    rf"\s*name\s*=\s*{re.escape(name)}\s*", line
                ):
                    continue
                if is_loc_dir and f"[{name}]" not in line:
                    continue
                refs[name].append((rel, line_number, line.strip()))

    def search(names: list[str]) -> dict[str, list[tuple[str, int, str]]]:
        if not names:
            return {}
        references: dict[str, list[tuple[str, int, str]]] = dict(
            (name, []) for name in names
        )
        matcher = compile_token_regex(names)
        for directory in iter_existing_dirs(search_dirs):
            is_loc_dir = "localisation" in directory.parts
            patterns = ["*.yml"] if is_loc_dir else ["*.txt", "*.gui", "*.gfx", "*.yml"]
            for path, lines in iter_readable_files([directory], tuple(patterns)):
                record_file(references, matcher, path, lines, is_loc_dir)
        return references

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
