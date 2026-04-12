#!/usr/bin/env python3
##########################
# Defines Validation Script
# Cross-references MD_defines.lua against vanilla 00_defines.lua to catch
# dead/fabricated defines, wrong namespaces, and duplicates.
#
# Checks:
#   1. Every define in MD exists in vanilla with the correct namespace
#   2. No duplicate defines within MD (last-write-wins is a silent bug)
#   3. Suggests closest match for likely typos
#
# Requires vanilla HOI4 installed; auto-detects common Steam paths.
##########################
import difflib
import os
import re
import sys
from typing import Dict, List, Optional, Set, Tuple

from validator_common import BaseValidator, Colors, run_validator_main

# Pattern: NDefines.NAMESPACE.NAME = value
MD_DEFINE_RE = re.compile(r"NDefines\.(\w+)\.(\w+)\s*=", re.IGNORECASE)

# Pattern in vanilla: NAME = value (inside a namespace block)
VANILLA_DEFINE_RE = re.compile(r"^\s+(\w+)\s*=")

# Pattern for namespace blocks in vanilla: NAMESPACE = {
VANILLA_NAMESPACE_RE = re.compile(r"^(\w+)\s*=\s*\{")

# Common Steam install locations
STEAM_PATHS = [
    os.path.expanduser("~/.local/share/Steam/steamapps/common/Hearts of Iron IV"),
    os.path.expanduser("~/.steam/steam/steamapps/common/Hearts of Iron IV"),
    "C:/Program Files (x86)/Steam/steamapps/common/Hearts of Iron IV",
    "C:/Program Files/Steam/steamapps/common/Hearts of Iron IV",
    os.path.expanduser(
        "~/Library/Application Support/Steam/steamapps/common/Hearts of Iron IV"
    ),
]


def find_vanilla_defines() -> Optional[str]:
    """Auto-detect the vanilla 00_defines.lua path."""
    for base in STEAM_PATHS:
        path = os.path.join(base, "common", "defines", "00_defines.lua")
        if os.path.isfile(path):
            return path
    return None


def parse_vanilla_defines(filepath: str) -> Dict[str, Set[str]]:
    """Parse vanilla 00_defines.lua into {namespace: {define_names}}.

    Vanilla uses nested Lua tables:
        NDefines = {
            NNamespace = {
                DEFINE_NAME = value,
                ...
            },
        }

    Namespace blocks sit at brace depth 1 (inside the top-level NDefines table).
    """
    namespaces: Dict[str, Set[str]] = {}
    current_namespace = None
    brace_depth = 0

    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            for line in f:
                stripped = line.strip()

                # Skip pure comment lines
                if stripped.startswith("--"):
                    continue

                # Remove inline comments (naive — ignores strings, but
                # vanilla defines don't embed -- inside string values)
                comment_pos = stripped.find("--")
                if comment_pos >= 0:
                    stripped = stripped[:comment_pos].strip()

                if not stripped:
                    continue

                # Check for namespace opening at depth 1 (inside NDefines)
                ns_match = VANILLA_NAMESPACE_RE.match(stripped)
                if ns_match and brace_depth == 1:
                    ns_name = ns_match.group(1)
                    current_namespace = ns_name
                    namespaces.setdefault(current_namespace, set())

                # Track brace depth (simplified — ignores braces in strings)
                brace_depth += stripped.count("{") - stripped.count("}")

                # Inside a namespace (depth >= 2), collect define names
                if current_namespace and brace_depth >= 2:
                    def_match = VANILLA_DEFINE_RE.match(line)
                    if def_match:
                        name = def_match.group(1)
                        # Skip sub-table names and Lua keywords
                        if name not in (
                            "NDefines",
                            "local",
                            "return",
                            "end",
                            "if",
                            "then",
                            "else",
                            "elseif",
                            "for",
                            "do",
                            "while",
                        ):
                            namespaces[current_namespace].add(name)

                # Namespace closes when we return to depth 1
                if brace_depth <= 1 and current_namespace:
                    current_namespace = None

    except Exception as e:
        print(f"Error reading vanilla defines: {e}", file=sys.stderr)

    return namespaces


def parse_md_defines(
    filepath: str,
) -> List[Tuple[str, str, int, str]]:
    """Parse MD_defines.lua into list of (namespace, name, line_number, full_line).

    MD uses flat assignment: NDefines.NAMESPACE.NAME = value
    """
    results = []
    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            for line_num, line in enumerate(f, start=1):
                stripped = line.strip()

                # Skip empty lines and comments
                if not stripped or stripped.startswith("--"):
                    continue

                # Remove inline comments for matching but keep original for display
                clean = stripped
                comment_pos = clean.find("--")
                if comment_pos >= 0:
                    clean = clean[:comment_pos].strip()

                match = MD_DEFINE_RE.search(clean)
                if match:
                    namespace = match.group(1)
                    name = match.group(2)
                    results.append((namespace, name, line_num, stripped))
    except Exception as e:
        print(f"Error reading MD defines: {e}", file=sys.stderr)

    return results


class Validator(BaseValidator):
    TITLE = "DEFINES VALIDATION"
    STAGED_EXTENSIONS = [".lua"]

    def __init__(self, *args, vanilla_path: str = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.vanilla_path = vanilla_path

    def run_validations(self):
        self._validate_defines()

    def _validate_defines(self):
        # Find vanilla defines
        vanilla_path = self.vanilla_path or find_vanilla_defines()
        if not vanilla_path:
            self.log(
                f"{Colors.RED if self.use_colors else ''}Cannot find vanilla 00_defines.lua. "
                f"Set --vanilla-path or ensure HOI4 is installed via Steam.{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
            self.errors_found += 1
            return

        self.log(f"  Vanilla defines: {vanilla_path}")

        # Find MD defines file
        md_path = os.path.join(self.mod_path, "common", "defines", "MD_defines.lua")
        if not os.path.isfile(md_path):
            self.log(
                f"{Colors.RED if self.use_colors else ''}MD_defines.lua not found at {md_path}{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
            self.errors_found += 1
            return

        # In staged mode, only run if the defines file was actually changed
        if self.staged_only and self.staged_files:
            md_staged = any(f.endswith("MD_defines.lua") for f in self.staged_files)
            if not md_staged:
                self.log("  MD_defines.lua not staged, skipping")
                return

        # Parse both files
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Parsing vanilla defines...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        vanilla = parse_vanilla_defines(vanilla_path)
        total_vanilla = sum(len(v) for v in vanilla.values())
        self.log(f"  Found {total_vanilla} defines across {len(vanilla)} namespaces")

        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Parsing MD defines...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        md_defines = parse_md_defines(md_path)
        self.log(f"  Found {len(md_defines)} defines")

        # Build flat lookup: all define names across all namespaces
        all_vanilla_names: Dict[str, List[str]] = {}
        for ns, names in vanilla.items():
            for name in names:
                all_vanilla_names.setdefault(name, []).append(ns)

        # Check 1: Dead/fabricated defines
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking for dead/fabricated defines...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        dead_results = []
        namespace_results = []
        for namespace, name, line_num, full_line in md_defines:
            # Skip table assignments (e.g., NEW_NAVY_LEADER_LEVEL_CHANCES)
            # These have complex sub-values that aren't simple defines
            if name not in all_vanilla_names:
                # Try fuzzy match
                all_names = list(all_vanilla_names.keys())
                suggestion = ""
                matches = difflib.get_close_matches(name, all_names, n=1, cutoff=0.7)
                if matches:
                    correct_ns = all_vanilla_names[matches[0]]
                    suggestion = f" (did you mean '{matches[0]}' in {correct_ns[0]}?)"
                dead_results.append(
                    f"MD_defines.lua:{line_num}: "
                    f"{namespace}.{name} does not exist in vanilla{suggestion}"
                )
            else:
                # Check 2: Wrong namespace
                correct_namespaces = all_vanilla_names[name]
                if namespace not in correct_namespaces:
                    namespace_results.append(
                        f"MD_defines.lua:{line_num}: "
                        f"{namespace}.{name} — wrong namespace, "
                        f"vanilla has it in {', '.join(correct_namespaces)}"
                    )

        self._report(
            dead_results,
            "✓ All MD defines exist in vanilla",
            "Dead or fabricated defines (silently ignored by the game):",
        )

        self._report(
            namespace_results,
            "✓ All MD defines use correct namespaces",
            "Defines in wrong namespace (silently ignored by the game):",
        )

        # Check 3: Duplicates within MD
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking for duplicate defines...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        seen: Dict[str, Tuple[int, str]] = {}
        duplicate_results = []
        for namespace, name, line_num, full_line in md_defines:
            key = f"{namespace}.{name}"
            if key in seen:
                prev_line, prev_text = seen[key]
                duplicate_results.append(
                    f"MD_defines.lua:{line_num}: duplicate {key} "
                    f"(first defined at line {prev_line})"
                )
            seen[key] = (line_num, full_line)

        self._report(
            duplicate_results,
            "✓ No duplicate defines found",
            "Duplicate defines (last value wins silently):",
        )


if __name__ == "__main__":

    def extra_args(parser):
        parser.add_argument(
            "--vanilla-path",
            type=str,
            default=None,
            help="Path to vanilla 00_defines.lua (auto-detected from Steam if omitted)",
        )

    run_validator_main(
        Validator, "Validate MD defines against vanilla HOI4", extra_args_fn=extra_args
    )
