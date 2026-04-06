#!/usr/bin/env python3
"""
find_idea_references.py — Find unreferenced ideas from a given ideas file.

Usage:
    python3 tools/find_idea_references.py common/ideas/Greek.txt
    python3 tools/find_idea_references.py common/ideas/American.txt --show-all
"""

import argparse
import re
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

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
    pattern = re.compile(r"^\s{2,}([A-Za-z][A-Za-z0-9_]+)\s*=\s*\{")
    tag_pattern = re.compile(r"^[A-Z]{2,4}$")

    for line in filepath.read_text(encoding="utf-8", errors="replace").splitlines():
        m = pattern.match(line)
        if not m:
            continue
        name = m.group(1)
        if name in SKIP_KEYWORDS or tag_pattern.match(name):
            continue
        if name not in names:
            names.append(name)
    return names


def search_references(idea: str, search_dirs: list[Path]) -> list[tuple[str, int, str]]:
    """Search for references to an idea across the codebase. Returns (file, line_num, content)."""
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


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find unreferenced ideas from an ideas file."
    )
    parser.add_argument("ideas_file", help="Path to the ideas file to analyze")
    parser.add_argument(
        "--show-all",
        action="store_true",
        help="Show all ideas including referenced ones",
    )
    parser.add_argument(
        "--no-report", action="store_true", help="Skip the report file prompt"
    )
    args = parser.parse_args()

    ideas_file = Path(args.ideas_file)
    if not ideas_file.exists():
        sys.exit(f"Error: File '{ideas_file}' not found!")

    start = time.time()

    print("=" * 43)
    print("IDEA REFERENCE ANALYZER")
    print("=" * 43)
    print(f"Analyzing file: {ideas_file}")
    line_count = len(
        ideas_file.read_text(encoding="utf-8", errors="replace").splitlines()
    )
    print(f"File size: {line_count} lines")
    mode = (
        "Finding ALL references" if args.show_all else "Finding UNREFERENCED ideas only"
    )
    print(f"Mode: {mode}")
    print("=" * 43)

    names = extract_idea_names(ideas_file)
    if not names:
        sys.exit(f"No idea names found in {ideas_file}")

    print(f"Analyzing {len(names)} ideas...\n")

    search_dirs = [REPO_ROOT / d for d in SEARCH_DIRS]
    referenced: list[tuple[str, list[tuple[str, int, str]]]] = []
    unreferenced: list[str] = []

    for idea in names:
        print(f"\r  Searching: {idea:<50}", end="", flush=True)
        refs = search_references(idea, search_dirs)
        if refs:
            referenced.append((idea, refs))
            if args.show_all:
                print(f"\n  Referenced: {idea} ({len(refs)} refs)")
                for filepath, line_num, content in refs:
                    print(f"    {filepath}:{line_num} -> {content}")
        else:
            unreferenced.append(idea)
            print(f"\r  UNREFERENCED: {idea:<50}")

    elapsed = time.time() - start
    minutes, seconds = divmod(int(elapsed), 60)

    print("\n")
    print("=" * 43)
    print("Summary:")
    print(f"  Total ideas analyzed: {len(names)}")
    print(f"  Referenced ideas: {len(referenced)}")
    print(f"  UNREFERENCED ideas: {len(unreferenced)}")
    print(f"  Total references found: {sum(len(r) for _, r in referenced)}")
    time_str = f"{minutes}m {seconds}s" if minutes else f"{seconds}s"
    print(f"  Execution time: {time_str}")
    print("=" * 43)

    if unreferenced:
        print("\nUNREFERENCED IDEAS (consider removing):")
        for idea in unreferenced:
            print(f"  - {idea}")
    else:
        print("\nAll ideas are referenced somewhere in the codebase!")

    if not args.no_report:
        try:
            answer = input("\nGenerate detailed report file? (y/n): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = "n"
        if answer == "y":
            stem = ideas_file.stem
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            prefix = "all_idea_references" if args.show_all else "unreferenced_ideas"
            report_path = Path(f"{prefix}_{stem}_{timestamp}.txt")
            lines_out: list[str] = [
                f"{'All Idea References' if args.show_all else 'Unreferenced Ideas'} Report",
                f"Source file: {ideas_file}",
                f"Ideas analyzed: {len(names)}, Referenced: {len(referenced)}, Unreferenced: {len(unreferenced)}",
                "",
            ]
            if unreferenced:
                lines_out.append("UNREFERENCED IDEAS:")
                lines_out.extend(f"  - {idea}" for idea in unreferenced)
                lines_out.append("")
            if args.show_all:
                lines_out.append("REFERENCED IDEAS:")
                for idea, refs in referenced:
                    lines_out.append(f"\n  {idea} ({len(refs)} refs):")
                    for filepath, line_num, content in refs:
                        lines_out.append(f"    {filepath}:{line_num} -> {content}")
            report_path.write_text("\n".join(lines_out), encoding="utf-8")
            print(f"Report saved to: {report_path}")


if __name__ == "__main__":
    main()
