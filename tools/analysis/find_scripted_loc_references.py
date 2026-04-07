#!/usr/bin/env python3
"""
find_scripted_loc_references.py — Find unreferenced scripted localisation names.

Usage:
    python3 tools/find_scripted_loc_references.py common/scripted_localisation/LBA_scripted_localisation.txt
    python3 tools/find_scripted_loc_references.py common/scripted_localisation/ENG_scripted_localisation.txt --show-all
    python3 tools/find_scripted_loc_references.py common/scripted_localisation/BRM_scripted_localisation.txt --no-report
"""

import argparse
import re
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

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

FILE_EXTENSIONS = {"*.txt", "*.gui", "*.gfx", "*.yml"}


def extract_scripted_loc_names(filepath: Path) -> list[str]:
    """Extract scripted localisation names (name = X) from a scripted_localisation file."""
    names: list[str] = []
    pattern = re.compile(r"^\s*name\s*=\s*([A-Za-z][A-Za-z0-9_]*)\s*$")
    for line in filepath.read_text(encoding="utf-8", errors="replace").splitlines():
        m = pattern.match(line)
        if m and m.group(1) not in names:
            names.append(m.group(1))
    return names


def search_references(
    name: str, search_dirs: list[Path], source_file: Path
) -> list[tuple[str, int, str]]:
    """Search for references to a scripted loc name across the codebase."""
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
                    # Skip the definition itself
                    if filepath == source_file and definition_pattern.match(line):
                        continue
                    # In localisation dirs, only match [name] bracketed references
                    if is_loc_dir:
                        if f"[{name}]" not in line:
                            continue
                    rel = filepath.relative_to(REPO_ROOT)
                    refs.append((str(rel), i, line.strip()))
    return refs


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find unreferenced scripted localisation names."
    )
    parser.add_argument(
        "scripted_loc_file", help="Path to the scripted localisation file to analyze"
    )
    parser.add_argument(
        "--show-all",
        action="store_true",
        help="Show all names including referenced ones",
    )
    parser.add_argument(
        "--no-report", action="store_true", help="Skip the report file prompt"
    )
    args = parser.parse_args()

    source_file = Path(args.scripted_loc_file).resolve()
    if not source_file.exists():
        sys.exit(f"Error: File '{args.scripted_loc_file}' not found!")

    start = time.time()

    print("=" * 43)
    print("SCRIPTED LOCALISATION REFERENCE ANALYZER")
    print("=" * 43)
    print(f"Analyzing file: {args.scripted_loc_file}")
    line_count = len(
        source_file.read_text(encoding="utf-8", errors="replace").splitlines()
    )
    print(f"File size: {line_count} lines")
    mode = (
        "Finding ALL references" if args.show_all else "Finding UNREFERENCED names only"
    )
    print(f"Mode: {mode}")
    print("=" * 43)

    names = extract_scripted_loc_names(source_file)
    if not names:
        sys.exit(f"No scripted localisation names found in {args.scripted_loc_file}")

    print(f"Analyzing {len(names)} scripted localisation names...\n")

    search_dirs = [REPO_ROOT / d for d in SEARCH_DIRS]
    referenced: list[tuple[str, list[tuple[str, int, str]]]] = []
    unreferenced: list[str] = []

    for name in names:
        print(f"\r  Searching: {name:<50}", end="", flush=True)
        refs = search_references(name, search_dirs, source_file)
        if refs:
            referenced.append((name, refs))
            if args.show_all:
                print(f"\n  Referenced: {name} ({len(refs)} refs)")
                for filepath, line_num, content in refs:
                    print(f"    {filepath}:{line_num} -> {content}")
        else:
            unreferenced.append(name)
            print(f"\r  UNREFERENCED: {name:<50}")

    elapsed = time.time() - start
    minutes, seconds = divmod(int(elapsed), 60)

    print("\n")
    print("=" * 43)
    print("Summary:")
    print(f"  Total names analyzed: {len(names)}")
    print(f"  Referenced: {len(referenced)}")
    print(f"  UNREFERENCED: {len(unreferenced)}")
    print(f"  Total references found: {sum(len(r) for _, r in referenced)}")
    time_str = f"{minutes}m {seconds}s" if minutes else f"{seconds}s"
    print(f"  Execution time: {time_str}")
    print("=" * 43)

    if unreferenced:
        print("\nUNREFERENCED SCRIPTED LOCALISATION NAMES (consider removing):")
        for name in unreferenced:
            print(f"  - {name}")
    else:
        print(
            "\nAll scripted localisation names are referenced somewhere in the codebase!"
        )

    if not args.no_report:
        try:
            answer = input("\nGenerate detailed report file? (y/n): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = "n"
        if answer == "y":
            stem = Path(args.scripted_loc_file).stem
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            prefix = (
                "all_scripted_loc_references"
                if args.show_all
                else "unreferenced_scripted_loc"
            )
            report_path = Path(f"{prefix}_{stem}_{timestamp}.txt")
            lines_out: list[str] = [
                f"{'All Scripted Localisation References' if args.show_all else 'Unreferenced Scripted Localisation'} Report",
                f"Source file: {args.scripted_loc_file}",
                f"Names analyzed: {len(names)}, Referenced: {len(referenced)}, Unreferenced: {len(unreferenced)}",
                "",
            ]
            if unreferenced:
                lines_out.append("UNREFERENCED NAMES:")
                lines_out.extend(f"  - {name}" for name in unreferenced)
                lines_out.append("")
            if args.show_all:
                lines_out.append("REFERENCED NAMES:")
                for name, refs in referenced:
                    lines_out.append(f"\n  {name} ({len(refs)} refs):")
                    for filepath, line_num, content in refs:
                        lines_out.append(f"    {filepath}:{line_num} -> {content}")
            report_path.write_text("\n".join(lines_out), encoding="utf-8")
            print(f"Report saved to: {report_path}")


if __name__ == "__main__":
    main()
