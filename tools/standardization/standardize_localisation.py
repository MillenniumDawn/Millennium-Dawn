#!/usr/bin/env python3

"""
Millennium Dawn Localisation Standardizer
Reorganises a loc file by content category: National Focus, Ideas, Dynamic Modifiers,
Opinion Modifiers, Decisions, Events, Characters, MIO, Traits, Variables & GUI,
Tooltips, Other, and Unreferenced (keys found nowhere in the mod's code).
"""

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared_utils import create_backup, log_message

# Output order
SECTION_ORDER = [
    "National Focus",
    "Ideas",
    "Dynamic Modifiers",
    "Opinion Modifiers",
    "Decisions",
    "Events",
    "Characters",
    "MIO",
    "Traits",
    "Variables & GUI",
    "Tooltips",
    "Other",
    "Unreferenced",
]

# Directories scanned to decide whether a key is referenced anywhere in the mod.
# A key that lands in "Other" but appears in none of these is a cleanup candidate
# (dead loc, or a dynamically-built key) and is routed to "Unreferenced".
REFERENCE_DIRS = ["common", "events", "interface"]
_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

# Content directories (relative to mod root) and extraction patterns per category.
# Each entry: (list_of_dirs, list_of_regex_patterns, recursive_glob)
CATEGORY_CONFIG: Dict[str, Tuple[List[str], List[str], bool]] = {
    "National Focus": (
        ["common/national_focus"],
        [r"\bid\s*=\s*(\w+)"],
        False,
    ),
    "Ideas": (
        ["common/ideas"],
        [r"^\t{2}(\w+)\s*=\s*\{"],
        False,
    ),
    "Dynamic Modifiers": (
        ["common/dynamic_modifiers"],
        [r"^(\w+)\s*=\s*\{"],
        False,
    ),
    "Opinion Modifiers": (
        ["common/opinion_modifiers"],
        [r"^\t(\w+)\s*=\s*\{"],
        False,
    ),
    "Decisions": (
        ["common/decisions"],
        [r"^(\w+)\s*=\s*\{", r"^\t(\w+)\s*=\s*\{"],
        True,  # includes categories/ subdir
    ),
    "Events": (
        ["events"],
        [r"^add_namespace\s*=\s*(\w+)"],
        False,
    ),
    "Characters": (
        ["common/characters"],
        [r"^\t(\w+)\s*=\s*\{"],
        False,
    ),
    "MIO": (
        ["common/military_industrial_organization/organizations"],
        [r"^(\w+)\s*=\s*\{", r"\bname\s*=\s*(\w+)"],
        False,
    ),
    "Traits": (
        ["common/unit_leader", "common/country_leader"],
        [r"^\t(\w+)\s*=\s*\{"],
        False,
    ),
    "Variables & GUI": (
        [
            "common/scripted_effects",
            "common/scripted_guis",
            "common/decisions",
            "interface",
        ],
        [
            r"set_variable\s*=\s*\{\s*(\w+)",
            r"add_to_variable\s*=\s*\{\s*(\w+)",
            r"set_global_variable\s*=\s*\{\s*(\w+)",
            r"set_country_flag\s*=\s*(\w+)",
        ],
        True,
    ),
}

# Key suffixes that may be appended to a base ID to form a loc key
_SUFFIXES = ("_desc", "_tt", "_name", "_short", "_loc", "_choice_tt")

SEPARATOR = " # =============================="


def _extract_tag(stem: str) -> Optional[str]:
    """Return the TAG from 'MD_focus_TAG_l_english', or None."""
    m = re.match(r"MD_focus_([A-Z]+)_l_english", stem)
    return m.group(1) if m else None


@dataclass
class LocEntry:
    leading_comments: List[str]
    key: str
    value: str  # everything after the colon (e.g. ` "Text"`)


def _scan_dir(directory: Path, recursive: bool) -> List[Path]:
    if not directory.exists():
        return []
    if recursive:
        return list(directory.rglob("*.txt")) + list(directory.rglob("*.gui"))
    return list(directory.glob("*.txt")) + list(directory.glob("*.gui"))


def _build_index(mod_root: Path, verbose: bool) -> Dict[str, Set[str]]:
    index: Dict[str, Set[str]] = {cat: set() for cat in SECTION_ORDER}

    for category, (dirs, patterns, recursive) in CATEGORY_CONFIG.items():
        compiled = [re.compile(p, re.MULTILINE) for p in patterns]
        for rel_dir in dirs:
            directory = mod_root / rel_dir
            for txt_file in _scan_dir(directory, recursive):
                try:
                    content = txt_file.read_text(encoding="utf-8-sig", errors="replace")
                except OSError:
                    continue
                for regex in compiled:
                    for match in regex.finditer(content):
                        token = match.group(1)
                        if token:
                            index[category].add(token)

        log_message(
            "DEBUG",
            f"{category}: {len(index[category])} IDs indexed",
            verbose,
        )

    return index


def _build_reference_tokens(mod_root: Path, verbose: bool) -> Set[str]:
    """Collect every identifier token appearing in REFERENCE_DIRS (excludes loc)."""
    tokens: Set[str] = set()
    for rel_dir in REFERENCE_DIRS:
        directory = mod_root / rel_dir
        for src_file in _scan_dir(directory, recursive=True):
            try:
                content = src_file.read_text(encoding="utf-8-sig", errors="replace")
            except OSError:
                continue
            tokens.update(_TOKEN_RE.findall(content))
    log_message("DEBUG", f"Reference tokens: {len(tokens)}", verbose)
    return tokens


def _referenced(key: str, references: Set[str]) -> bool:
    """True if the key, or its base after stripping a known loc suffix, appears
    in the mod's code. The engine auto-appends suffixes such as `_desc` to a
    referenced base (e.g. a `pdx_tooltip = X` or dynamic modifier named X pulls in
    `X_desc` as the tooltip body), so a referenced base keeps the companion live."""
    if key in references:
        return True
    for suffix in _SUFFIXES:
        if key.endswith(suffix):
            return key[: -len(suffix)] in references
    return False


def _find_category(
    key: str, index: Dict[str, Set[str]], references: Optional[Set[str]] = None
) -> str:
    # Event keys: `namespace.<id>` or `namespace.<id>.x`, numeric or text-named id.
    if "." in key:
        namespace = key.split(".", 1)[0]
        if namespace in index["Events"]:
            return "Events"

    # Try exact key first
    for category in SECTION_ORDER[:-1]:
        if key in index[category]:
            return category

    # Try stripping a known suffix
    for suffix in _SUFFIXES:
        if key.endswith(suffix):
            base = key[: -len(suffix)]
            for category in SECTION_ORDER[:-1]:
                if base in index[category]:
                    return category
            break

    # Tooltip strings with no ID backing (fallback only — a `_tt` key whose base
    # is a real focus/decision was already grouped with it above).
    if key.endswith("_tt"):
        return "Tooltips"

    # No category matched. If the key is referenced nowhere in the mod's code,
    # it is a cleanup candidate (dead loc or a dynamically-built key).
    if references is not None and not _referenced(key, references):
        return "Unreferenced"

    return "Other"


def _parse_loc_file(content: str) -> Tuple[str, List[LocEntry]]:
    """Return (header_line, list_of_entries). header_line is the `l_english:` line."""
    lines = content.splitlines()

    header = ""
    entries: List[LocEntry] = []
    pending_comments: List[str] = []

    for line in lines:
        stripped = line.strip()

        if not header:
            # First non-empty line must be the language header
            if stripped:
                header = line.rstrip()
            continue

        if not stripped:
            # Blank line — discard (we add our own spacing)
            continue

        if stripped.startswith("#"):
            pending_comments.append(line.rstrip())
            continue

        # Try to parse as a loc key: ` key: "value"` or ` key: value`
        m = re.match(r"^\s+(\S+?)\s*:(.*)", line)
        if m:
            key = m.group(1)
            value = m.group(2)
            entries.append(LocEntry(list(pending_comments), key, value))
            pending_comments = []
        else:
            # Unrecognised line — keep it as a standalone comment
            pending_comments.append(line.rstrip())

    # Any trailing comments with no following key → attach as Other comment entries
    if pending_comments:
        entries.append(LocEntry(list(pending_comments), "", ""))

    return header, entries


def _format_section_header(category: str) -> List[str]:
    return [
        "",
        SEPARATOR,
        f" # {category}",
        SEPARATOR,
    ]


def _format_output(
    header: str,
    entries: List[LocEntry],
    index: Dict[str, Set[str]],
    file_stem: str = "",
    references: Optional[Set[str]] = None,
) -> str:
    buckets: Dict[str, List[LocEntry]] = {cat: [] for cat in SECTION_ORDER}

    for entry in entries:
        if not entry.key:
            continue
        category = _find_category(entry.key, index, references)
        buckets[category].append(entry)

    output_lines: List[str] = [header]

    tag = _extract_tag(file_stem)

    for category in SECTION_ORDER:
        bucket = buckets[category]
        if not bucket:
            continue

        bucket.sort(key=lambda e: e.key.lower())

        if category == "National Focus" and tag:
            anchor_key = f"{tag}_focus_tree"
            existing = next((e for e in bucket if e.key == anchor_key), None)
            if existing:
                bucket.remove(existing)
            else:
                existing = LocEntry([], anchor_key, ' ""')
            bucket.insert(0, existing)

        output_lines.extend(_format_section_header(category))

        for entry in bucket:
            output_lines.append(f" {entry.key}:{entry.value}")

    output_lines.append("")  # trailing newline
    return "\n".join(output_lines)


def _detect_mod_root(start: Path) -> Optional[Path]:
    """Walk up from start until we find a directory containing both common/ and events/."""
    candidate = start if start.is_dir() else start.parent
    for _ in range(10):
        if (candidate / "common").is_dir() and (candidate / "events").is_dir():
            return candidate
        parent = candidate.parent
        if parent == candidate:
            break
        candidate = parent
    return None


class LocalisationStandardizer:
    def __init__(self, mod_root: Path, verbose: bool = False):
        self.mod_root = mod_root
        self.verbose = verbose
        log_message("INFO", f"Building content index from {mod_root}", verbose)
        self.index = _build_index(mod_root, verbose)
        self.references = _build_reference_tokens(mod_root, verbose)

    def standardize_file(self, input_file: Path, output_file: Path) -> bool:
        log_message("INFO", f"Standardising {input_file}", self.verbose)

        try:
            raw = input_file.read_text(encoding="utf-8-sig")
        except OSError as exc:
            log_message("ERROR", f"Cannot read {input_file}: {exc}")
            return False

        header, entries = _parse_loc_file(raw)

        if not header:
            log_message("ERROR", "No language header found (expected `l_english:`)")
            return False

        log_message("INFO", f"Parsed {len(entries)} entries", self.verbose)

        output = _format_output(
            header, entries, self.index, output_file.stem, self.references
        )

        try:
            output_file.write_text(output, encoding="utf-8-sig")
        except OSError as exc:
            log_message("ERROR", f"Cannot write {output_file}: {exc}")
            return False

        # Summary
        cats = {}
        for entry in entries:
            if entry.key:
                cat = _find_category(entry.key, self.index, self.references)
                cats[cat] = cats.get(cat, 0) + 1
        for cat in SECTION_ORDER:
            if cat in cats:
                log_message("INFO", f"  {cat}: {cats[cat]} keys", self.verbose)

        log_message("SUCCESS", f"Written to {output_file}")
        return True


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Standardise a Millennium Dawn localisation file by content category"
    )
    parser.add_argument("input_file", help="Input .yml localisation file")
    parser.add_argument("-o", "--output", help="Output file (default: overwrite input)")
    parser.add_argument(
        "-b", "--backup", action="store_true", help="Create backup first"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "--mod-root", help="Path to mod root (auto-detected if omitted)"
    )
    args = parser.parse_args()

    input_path = Path(args.input_file)
    if not input_path.exists():
        log_message("ERROR", f"File not found: {input_path}")
        sys.exit(1)

    output_path = Path(args.output) if args.output else input_path

    if args.mod_root:
        mod_root = Path(args.mod_root)
    else:
        mod_root = _detect_mod_root(input_path)
        if not mod_root:
            log_message("ERROR", "Could not detect mod root. Use --mod-root.")
            sys.exit(1)
    log_message("INFO", f"Mod root: {mod_root}", args.verbose)

    if args.backup:
        backup = create_backup(str(input_path))
        if not backup:
            sys.exit(1)

    standardizer = LocalisationStandardizer(mod_root, verbose=args.verbose)
    if not standardizer.standardize_file(input_path, output_path):
        sys.exit(1)


if __name__ == "__main__":
    main()
