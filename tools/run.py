#!/usr/bin/env python3
"""
run.py — Run any Millennium Dawn tool by short name.

Usage:
    python3 tools/run.py <tool-name> [args...]
    python3 tools/run.py --list

Examples:
    python3 tools/run.py estimate_gdp --all
    python3 tools/run.py gfx_entry_generator_linux
    python3 tools/run.py publish_workshop release --full
    python3 tools/run.py find_idea_references common/ideas/Greek.txt
    python3 tools/run.py standardize focus common/national_focus/SER.txt
    python3 tools/run.py review_branch main
"""

import os
import subprocess
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent

# Directories to search for scripts (order matters for display grouping).
SEARCH_DIRS = [
    "analysis",
    "assets",
    "generators",
    "linting",
    "publishing",
    "standardization",
    "validation",
    "tests",
    ".",  # root-level scripts
]

# Internal/library scripts that should not appear in --list.
HIDDEN = {
    "path_utils",
    "shared_utils",
    "loc",
    "logging_tool",
    "run",
    "validate_staged",
    "standardize_staged",
    "common_utils",
    "validator_common",
}


def find_all_tools() -> dict[str, Path]:
    """Discover all runnable scripts, keyed by short name (no .py)."""
    tools: dict[str, Path] = {}
    for subdir in SEARCH_DIRS:
        search_path = TOOLS_DIR / subdir if subdir != "." else TOOLS_DIR
        if not search_path.is_dir():
            continue
        for py_file in sorted(search_path.glob("*.py")):
            name = py_file.stem
            if name.startswith("_") or name in HIDDEN:
                continue
            # Don't recurse — only direct children of each search dir.
            if py_file.parent != search_path:
                continue
            # First match wins (subdirectory scripts take priority over root).
            if name not in tools:
                tools[name] = py_file
    return tools


def print_list(tools: dict[str, Path]) -> None:
    """Print all available tools grouped by directory."""
    groups: dict[str, list[tuple[str, Path]]] = {}
    for name, path in tools.items():
        rel = path.parent.relative_to(TOOLS_DIR)
        group = str(rel) if str(rel) != "." else "root"
        groups.setdefault(group, []).append((name, path))

    print("Available tools:\n")
    for subdir in SEARCH_DIRS:
        group = subdir if subdir != "." else "root"
        if group not in groups:
            continue
        print(f"  {group}/")
        for name, _ in sorted(groups[group]):
            print(f"    {name}")
        print()


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("--help", "-h"):
        print(__doc__.strip())
        sys.exit(0)

    if sys.argv[1] == "--list":
        print_list(find_all_tools())
        sys.exit(0)

    tool_name = sys.argv[1].replace(".py", "").replace("-", "_")
    tool_args = sys.argv[2:]

    tools = find_all_tools()
    if tool_name not in tools:
        # Fuzzy match: check for partial matches.
        matches = [k for k in tools if tool_name in k]
        if len(matches) == 1:
            tool_name = matches[0]
        elif matches:
            print(f"Ambiguous tool name '{tool_name}'. Did you mean one of:")
            for m in sorted(matches):
                print(f"  {m}")
            sys.exit(1)
        else:
            print(f"Unknown tool: '{tool_name}'")
            print("Run 'python3 tools/run.py --list' to see available tools.")
            sys.exit(1)

    script_path = tools[tool_name]
    result = subprocess.run(
        [sys.executable, str(script_path)] + tool_args,
        cwd=os.getcwd(),
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
