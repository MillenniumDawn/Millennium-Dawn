"""Shared scaffolding for "find unreferenced X" analysis tools.

Used by find_idea_references.py and find_scripted_loc_references.py to provide
the common argparse/header/per-name-loop/summary/report harness. The two scripts
supply their domain-specific name extractor and reference search logic via the
``extract_names`` and ``search_for_references`` callbacks.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Callable, List, Tuple


def build_parser(
    description: str, source_arg: str, source_help: str
) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=description)
    p.add_argument(source_arg, help=source_help)
    p.add_argument(
        "--show-all",
        action="store_true",
        help="Show all entries including referenced ones",
    )
    p.add_argument(
        "--no-report", action="store_true", help="Skip the report file prompt"
    )
    return p


def run_reference_search(
    *,
    source_file: Path,
    search_dirs: List[Path],
    repo_root: Path,
    analyzer_title: str,
    subject_singular: str,
    subject_plural: str,
    extract_names: Callable[[Path], List[str]],
    search_for_references: Callable[[str], List[Tuple[str, int, str]]],
    show_all: bool,
    no_report: bool,
    report_prefix_all: str,
    report_prefix_unref: str,
    report_title_all: str,
    report_title_unref: str,
) -> None:
    """Run the shared "find unreferenced X" workflow.

    ``search_for_references(name)`` is a thin closure the caller builds — it
    captures any per-search context (source file, search dirs) so this harness
    does not need to know about them.
    """
    if not source_file.exists():
        sys.exit(f"Error: File '{source_file}' not found!")

    start = time.time()

    header_bar = "=" * 43
    print(header_bar)
    print(analyzer_title)
    print(header_bar)
    print(f"Analyzing file: {source_file}")
    line_count = len(
        source_file.read_text(encoding="utf-8", errors="replace").splitlines()
    )
    print(f"File size: {line_count} lines")
    mode = (
        "Finding ALL references"
        if show_all
        else f"Finding UNREFERENCED {subject_plural} only"
    )
    print(f"Mode: {mode}")
    print(header_bar)

    names = extract_names(source_file)
    if not names:
        sys.exit(f"No {subject_plural} found in {source_file}")

    print(f"Analyzing {len(names)} {subject_plural}...\n")

    referenced: List[Tuple[str, List[Tuple[str, int, str]]]] = []
    unreferenced: List[str] = []

    for name in names:
        print(f"\r  Searching: {name:<50}", end="", flush=True)
        refs = search_for_references(name)
        if refs:
            referenced.append((name, refs))
            if show_all:
                print(f"\n  Referenced: {name} ({len(refs)} refs)")
                for filepath, line_num, content in refs:
                    print(f"    {filepath}:{line_num} -> {content}")
        else:
            unreferenced.append(name)
            print(f"\r  UNREFERENCED: {name:<50}")

    elapsed = time.time() - start
    minutes, seconds = divmod(int(elapsed), 60)

    print("\n")
    print(header_bar)
    print("Summary:")
    print(f"  Total {subject_plural} analyzed: {len(names)}")
    print(f"  Referenced: {len(referenced)}")
    print(f"  UNREFERENCED: {len(unreferenced)}")
    print(f"  Total references found: {sum(len(r) for _, r in referenced)}")
    time_str = f"{minutes}m {seconds}s" if minutes else f"{seconds}s"
    print(f"  Execution time: {time_str}")
    print(header_bar)

    if unreferenced:
        print(f"\nUNREFERENCED {subject_plural.upper()} (consider removing):")
        for name in unreferenced:
            print(f"  - {name}")
    else:
        print(f"\nAll {subject_plural} are referenced somewhere in the codebase!")

    if no_report:
        return

    try:
        answer = input("\nGenerate detailed report file? (y/n): ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        answer = "n"
    if answer != "y":
        return

    stem = source_file.stem
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    prefix = report_prefix_all if show_all else report_prefix_unref
    report_path = Path(f"{prefix}_{stem}_{timestamp}.txt")
    title = report_title_all if show_all else report_title_unref
    lines_out: List[str] = [
        f"{title} Report",
        f"Source file: {source_file}",
        f"{subject_plural.capitalize()} analyzed: {len(names)}, "
        f"Referenced: {len(referenced)}, Unreferenced: {len(unreferenced)}",
        "",
    ]
    if unreferenced:
        lines_out.append(f"UNREFERENCED {subject_plural.upper()}:")
        lines_out.extend(f"  - {name}" for name in unreferenced)
        lines_out.append("")
    if show_all:
        lines_out.append(f"REFERENCED {subject_plural.upper()}:")
        for name, refs in referenced:
            lines_out.append(f"\n  {name} ({len(refs)} refs):")
            for filepath, line_num, content in refs:
                lines_out.append(f"    {filepath}:{line_num} -> {content}")
    report_path.write_text("\n".join(lines_out), encoding="utf-8")
    print(f"Report saved to: {report_path}")
