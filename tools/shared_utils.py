#!/usr/bin/env python3

"""Shared utilities for Millennium Dawn tools (standardization and validation)."""

import argparse
import bisect
import logging
import os
import re
import stat
import subprocess
import sys
import tempfile
import time
from collections import OrderedDict
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import (
    Any,
    Callable,
    Container,
    Dict,
    Iterator,
    List,
    Optional,
    Set,
    Tuple,
)


class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    GRAY = "\033[90m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


_LEVEL_COLORS = {
    "SUCCESS": Colors.GREEN,
    "INFO": Colors.BLUE,
    "DEBUG": Colors.GRAY,
    "WARNING": Colors.YELLOW,
    "ERROR": Colors.RED,
}


# Default skip patterns shared across validators. Individual validators can
# extend this list with their own patterns.
DEFAULT_EXTRA_SKIP_PATTERNS: List[str] = ["FR_loc"]

# ruling_party 0-23. Slot 0 is Western Autocracy.
PARTY_SLOT_NAMES: Dict[int, str] = {
    0: "Western_Autocracy",
    1: "conservatism",
    2: "liberalism",
    3: "socialism",
    4: "Communist-State",
    5: "anarchist_communism",
    6: "Conservative",
    7: "Autocracy",
    8: "Mod_Vilayat_e_Faqih",
    9: "Vilayat_e_Faqih",
    10: "Kingdom",
    11: "Caliphate",
    12: "Neutral_Muslim_Brotherhood",
    13: "Neutral_Autocracy",
    14: "Neutral_conservatism",
    15: "oligarchism",
    16: "Neutral_Libertarian",
    17: "Neutral_green",
    18: "neutral_Social",
    19: "Neutral_Communism",
    20: "Nat_Populism",
    21: "Nat_Fascism",
    22: "Nat_Autocracy",
    23: "Monarchist",
}

# Leave a quarter of the machine to whoever is using it. A full suite run
# fans out over every validator and each of those keeps its own pool, so
# without a shared ceiling the tooling oversubscribes the box and everything
# else on it stalls.
CPU_BUDGET_FRACTION = 0.75


def cpu_budget() -> int:
    """Cores this repo's tooling may occupy at once, never the whole machine.

    ``MD_MAX_WORKERS`` overrides the share outright. CI runners have the box to
    themselves, so there the budget is every core.
    """
    override = os.environ.get("MD_MAX_WORKERS", "").strip()
    if override.isdigit() and int(override) > 0:
        return int(override)
    cores = os.cpu_count() or 1
    if os.environ.get("CI", "").strip().lower() in ("1", "true"):
        return cores
    return max(1, int(cores * CPU_BUDGET_FRACTION))


def split_cpu_budget(tasks: int) -> Tuple[int, int]:
    """Split the budget into (concurrent tasks, workers each), product capped."""
    budget = cpu_budget()
    parallel = max(1, min(tasks, budget))
    return parallel, max(1, budget // parallel)


def log_message(
    level: str, message: str, verbose: bool = False, use_colors: bool = True
):
    """Log a message with timestamp and optional color coding."""
    if level == "DEBUG" and not verbose:
        return

    timestamp = datetime.now().strftime("%H:%M:%S")

    # Honor the NO_COLOR convention (https://no-color.org) so CI logs stay
    # escape-free even when a caller left use_colors at its default.
    colors_on = use_colors and not os.environ.get("NO_COLOR")
    color = _LEVEL_COLORS.get(level, "") if colors_on else ""
    reset = Colors.ENDC if colors_on else ""

    formatted_message = f"{color}[{timestamp}] {level}: {message}{reset}"
    print(formatted_message, file=sys.stderr)


def create_standard_parser(description: str) -> argparse.ArgumentParser:
    """Create a standard argument parser for Millennium Dawn tools"""
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input_file", help="Input file to process")
    parser.add_argument(
        "-o", "--output", help="Output file (default: overwrites input)"
    )
    parser.add_argument(
        "-b", "--backup", action="store_true", help="Create backup before modifying"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "--no-color", action="store_true", help="Disable ANSI color codes in output"
    )
    return parser


def create_validation_parser(description: str) -> argparse.ArgumentParser:
    """Create a standard argument parser for Millennium Dawn validation tools"""
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="Path to the mod folder (default: current directory)",
    )
    parser.add_argument(
        "--strict", action="store_true", help="Exit with error code if issues are found"
    )
    parser.add_argument(
        "--output", "-o", type=str, help="Save validation results to file"
    )
    parser.add_argument(
        "--no-color", action="store_true", help="Disable ANSI color codes in output"
    )
    parser.add_argument(
        "--staged", action="store_true", help="Only validate git staged files"
    )
    parser.add_argument(
        "--no-cache", action="store_true", help="Bypass disk cache for this run"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of worker processes (default: auto-detect)",
    )
    return parser


def strip_inline_comment(line: str) -> str:
    """Return *line* with any trailing ``#`` comment removed.

    A ``#`` inside a double-quoted string is not a comment. Use this anywhere a
    line's braces/tokens are counted so unbalanced braces inside comments don't
    corrupt the count. Returns the code portion (trailing newline/space preserved
    up to the cut), not stripped of surrounding whitespace.
    """
    if "#" not in line:
        return line
    in_str = False
    for i, c in enumerate(line):
        if c == '"' and (i == 0 or line[i - 1] != "\\"):
            in_str = not in_str
        elif c == "#" and not in_str:
            return line[:i]
    return line


def extract_block(lines: List[str], start_index: int) -> Tuple[List[str], int]:
    """Extract a multi-line block by counting braces.

    Inline comments are stripped and quoted-string interiors blanked before
    counting, so a ``#`` comment or a ``{`` / ``}`` inside a ``"..."`` string
    does not corrupt the depth.
    """
    if start_index >= len(lines):
        return [], start_index

    block_lines = []
    brace_count = 0
    opened = False
    i = start_index

    while i < len(lines):
        line = lines[i]
        block_lines.append(line)

        code = blank_quoted_strings(strip_inline_comment(line))
        if "{" in code:
            opened = True
        brace_count += code.count("{") - code.count("}")

        # `opened` lets the block terminate once braces balance even when the
        # opening `{` sits on a later line than the name; without it a next-line
        # brace never satisfies the old "{ on start line" check and the block
        # ran to EOF.
        if opened and brace_count == 0:
            i += 1
            break
        elif brace_count < 0:
            if opened:
                # Over-closing line (e.g. `} }` or a stray extra `}`) after the
                # block opened: keep the accumulated lines with this line as the
                # closer so the consumer never silently drops source lines.
                return block_lines, i + 1
            # Malformed: a stray `}` before any `{`. Advance past it (returning
            # no block) so a caller looping on the returned index still makes
            # forward progress instead of spinning on an unchanged start index.
            return [], i + 1

        i += 1

    return block_lines, i  # position AFTER the block, not i-1


def find_matching_brace(text: str, open_idx: int) -> int:
    """Return the index of the ``}`` matching the ``{`` at *open_idx*.

    Returns -1 if the braces never balance. Braces inside double-quoted
    strings are ignored; :func:`extract_block_from_text` delegates here for
    its own brace matching.
    """
    depth = 0
    in_str = False
    i = open_idx
    n = len(text)
    while i < n:
        c = text[i]
        if c == '"' and text[i - 1] != "\\":
            in_str = not in_str
        elif not in_str:
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return i
        i += 1
    return -1


def extract_block_from_text(text: str, start: int) -> Tuple[str, int]:
    """Char-accurate brace-block extractor for raw text.

    Returns ``(body, end_pos)`` where *body* is the text between the matching
    braces and *end_pos* is the index just past the closing ``}``. Braces
    inside double-quoted strings are ignored. Returns ``("", -1)`` when no
    opening brace is found or the block never balances.
    """
    open_pos = text.find("{", start)
    if open_pos == -1:
        return "", -1
    close_pos = find_matching_brace(text, open_pos)
    if close_pos == -1:
        return "", -1
    return text[open_pos + 1 : close_pos], close_pos + 1


def find_unquoted_block_end(text: str, start: int) -> Tuple[int, bool]:
    """Advance from *start* (just past an already-consumed opening ``{``),
    counting bare ``{``/``}`` until depth returns to zero or *text* runs out.

    Returns ``(end_index, balanced)`` — *end_index* is one past the matching
    ``}`` when *balanced*, else ``len(text)``. Unlike :func:`find_matching_brace`,
    quoted-string interiors are not respected; use only where the input can't
    hide a brace inside a ``"..."`` span.
    """
    depth = 1
    i = start
    n = len(text)
    while i < n and depth > 0:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        i += 1
    return i, depth == 0


def compact_block(block_lines: List[str]) -> List[str]:
    """Completely compact a block by removing all internal blank lines"""
    if not block_lines:
        return block_lines

    compacted = []
    for line in block_lines:
        if line.strip():
            compacted.append(line.rstrip())

    return compacted


def collapse_ws_outside_quotes(text: str) -> str:
    """Collapse runs of whitespace outside double-quoted spans to single spaces,
    leaving text inside `"..."` byte-exact. Like `" ".join(text.split())` for
    unquoted text, but a `log`/tooltip string keeps its internal spacing."""
    result: List[str] = []
    in_str = False
    prev_space = False
    for i, c in enumerate(text):
        if c == '"' and (i == 0 or text[i - 1] != "\\"):
            in_str = not in_str
            result.append(c)
            prev_space = False
        elif in_str:
            result.append(c)
        elif c.isspace():
            if not prev_space:
                result.append(" ")
            prev_space = True
        else:
            result.append(c)
            prev_space = False
    return "".join(result).strip()


def _normalize_oneline_braces(text: str) -> str:
    """Collapse whitespace and put single spaces around ``{``/``}``, leaving the
    contents of double-quoted strings untouched."""
    out: List[str] = []
    in_str = False
    for i, c in enumerate(text):
        if c == '"' and (i == 0 or text[i - 1] != "\\"):
            in_str = not in_str
            out.append(c)
        elif not in_str and c in "{}":
            out.append(" ")
            out.append(c)
            out.append(" ")
        else:
            out.append(c)
    return collapse_ws_outside_quotes("".join(out))


_COMPARISON_OPS = {"!=", "==", ">=", "<="}


def normalize_spacing(line: str) -> str:
    """Put single spaces around braces, assignments and comparisons in one line.

    Leading indentation, ``"..."`` string interiors and any trailing ``#``
    comment are left byte-exact; a whole-line comment is returned unchanged.
    Comparison operators are padded without splitting their two-character forms,
    and an empty block keeps its written spacing (``{}`` and ``{ }`` both survive).
    Idempotent.
    """
    code = strip_inline_comment(line)
    comment = line[len(code) :].strip()
    stripped = code.strip()
    if not stripped or stripped.startswith("#"):
        return line.rstrip()

    indent = code[: len(code) - len(code.lstrip())]

    out: List[str] = []
    in_str = False
    i = 0
    n = len(code)
    while i < n:
        c = code[i]
        if c == '"' and (i == 0 or code[i - 1] != "\\"):
            in_str = not in_str
            out.append(c)
        elif in_str:
            out.append(c)
        elif code[i : i + 2] in _COMPARISON_OPS or code[i : i + 2] == "{}":
            out.append(f" {code[i : i + 2]} ")
            i += 2
            continue
        elif c in "{}=<>":
            out.append(f" {c} ")
        else:
            out.append(c)
        i += 1

    body = collapse_ws_outside_quotes("".join(out))
    return f"{indent}{body} {comment}".rstrip() if comment else f"{indent}{body}"


def collapse_or_compact(
    block_lines: List[str], indent: Optional[str] = None
) -> List[str]:
    """Render a ``key = { ... }`` block on one line when it reduces to a single
    leaf assignment (even through nesting), else fall back to ``compact_block``.

    Single-leaf test (evaluated outside string literals and comments):
    ``leaves = (#"=<>") - (#"{")``; collapse iff ``leaves == 1`` and braces
    balance. Comparison operators ``<``/``>`` count as leaves alongside ``=`` so a
    block like ``{ a > 1 b > 2 }`` is not mistaken for a single leaf. Bails to
    ``compact_block`` if any line carries a ``#`` comment. When *indent* is None
    the single-line form keeps the block's existing leading whitespace (from
    ``block_lines[0]``); otherwise *indent* is used as the prefix.
    """
    if not block_lines:
        return compact_block(block_lines)

    for line in block_lines:
        if strip_inline_comment(line) != line:
            return compact_block(block_lines)

    if indent is None:
        first = block_lines[0]
        indent = first[: len(first) - len(first.lstrip())]

    text = " ".join(line.strip() for line in block_lines if line.strip())

    n_leaf = 0
    n_open = 0
    n_close = 0
    in_str = False
    for i, c in enumerate(text):
        if c == '"' and (i == 0 or text[i - 1] != "\\"):
            in_str = not in_str
        elif not in_str:
            if c in "=<>":
                n_leaf += 1
            elif c == "{":
                n_open += 1
            elif c == "}":
                n_close += 1

    if n_open != n_close or n_leaf - n_open != 1:
        return compact_block(block_lines)

    return [f"{indent}{_normalize_oneline_braces(text)}"]


_FACTOR_TOKEN_RE = re.compile(r"\bfactor\b")
_BASE_TOKEN_RE = re.compile(r"\bbase\b")


def convert_root_factor_to_base(block_lines: List[str]) -> List[str]:
    """Rename ``factor`` to ``base`` at the root of an ``ai_will_do`` block.

    MD convention (enforced by check_common_mistakes) is ``base`` at the root;
    ``factor`` belongs only inside ``modifier`` children, which are left
    untouched. No-op when the root already has a ``base`` — converting there
    would emit a duplicate key.
    """

    def _root_spans(pattern) -> List[Tuple[int, int, int]]:
        spans = []
        depth = 0
        for idx, line in enumerate(block_lines):
            code = strip_inline_comment(line)
            pos = 0
            for m in pattern.finditer(code):
                depth += code.count("{", pos, m.start()) - code.count(
                    "}", pos, m.start()
                )
                pos = m.start()
                if depth == 1:
                    spans.append((idx, m.start(), m.end()))
            depth += code.count("{", pos) - code.count("}", pos)
        return spans

    if not block_lines or _root_spans(_BASE_TOKEN_RE):
        return block_lines
    spans = _root_spans(_FACTOR_TOKEN_RE)
    if not spans:
        return block_lines
    out = list(block_lines)
    for idx, start, end in reversed(spans):
        out[idx] = out[idx][:start] + "base" + out[idx][end:]
    return out


def create_backup(filename: str) -> str:
    """Create a backup of the input file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"{filename}.backup.{timestamp}"

    try:
        with open(filename, "r", encoding="utf-8", newline="") as src:
            with open(backup_filename, "w", encoding="utf-8", newline="") as dst:
                dst.write(src.read())
        log_message("INFO", f"Backup created: {backup_filename}")
        return backup_filename
    except Exception as e:
        log_message("ERROR", f"Failed to create backup: {str(e)}")
        return ""


def should_skip_file(
    filename: str, extra_skip_patterns: Optional[List[str]] = None
) -> bool:
    """Check if a file should be skipped during processing."""
    ignored_dirs = {".git", ".claude", "gfx", "tools", "resources", "docs", "map"}
    content_roots = {"common", "events", "history", "interface", "localisation"}
    normalized_path = filename.replace("\\", "/").strip("/")
    parts = normalized_path.split("/")
    # Canal/strait closures set flags read here, so this file is game logic
    # that must count for variables validation. Stale worktree and reference
    # copies stay ignored.
    if parts[-2:] == ["map", "adjacency_rules.txt"] and not (
        ignored_dirs - {"map"}
    ).intersection(parts[:-2]):
        return False
    for index, part in enumerate(parts):
        if part not in ignored_dirs:
            continue
        if part in {".git", ".claude"} or not content_roots.intersection(parts[:index]):
            return True
    if extra_skip_patterns:
        for pattern in extra_skip_patterns:
            if pattern in normalized_path:
                return True
    return False


def normalize_path_separators(path: str) -> str:
    """Return a path with POSIX separators for public output."""
    return path.replace("\\", "/")


def is_excluded_path(path: str, excluded_dirs: Container[str], repo_root: str) -> bool:
    """True if path is under one of excluded_dirs, matched relative to repo_root.

    Matching is against the path relative to repo_root, not the absolute path:
    a checkout nested under an ancestor dir literally named after one of
    excluded_dirs would otherwise match every file and no-op the whole repo.
    """
    try:
        rel = os.path.relpath(os.path.abspath(path), os.path.abspath(repo_root))
    except ValueError:
        rel = normalize_path_separators(os.path.abspath(path)).strip("/")
        return any(part in excluded_dirs for part in rel.split("/"))
    return any(part in excluded_dirs for part in rel.split(os.sep))


def iter_txt_targets(
    path: str, excluded_dirs: Container[str]
) -> Iterator[Tuple[str, str]]:
    """Yield (display_path, full_path) for every .txt file a CLI target names.

    `path` may be a single file (yielded as-is) or a directory (walked
    recursively, pruning excluded_dirs). display_path is path-relative for a
    walked file, or path itself for a direct file argument. Callers must check
    whether path itself is excluded before calling this.
    """
    if os.path.isdir(path):
        for dirpath, dirnames, filenames in os.walk(path):
            dirnames[:] = [d for d in dirnames if d not in excluded_dirs]
            for fn in filenames:
                if fn.lower().endswith(".txt"):
                    full = os.path.join(dirpath, fn)
                    yield normalize_path_separators(os.path.relpath(full, path)), full
    elif os.path.isfile(path):
        yield path, path


def _reject_symlink_path(path: Path) -> None:
    if path.is_symlink():
        raise OSError(f"Refusing to access symlink: {path}")
    for parent in path.absolute().parents:
        if parent == parent.parent:
            break
        if parent.is_symlink():
            raise OSError(f"Refusing to access symlinked parent: {parent}")


def read_text_strict(
    filename: str,
    encoding: str = "utf-8-sig",
    *,
    reject_symlink: bool = True,
) -> str:
    """Read repository text without replacing malformed bytes."""
    path = Path(filename)
    if reject_symlink:
        _reject_symlink_path(path)
    with path.open("r", encoding=encoding, errors="strict", newline="") as handle:
        return handle.read()


def resolve_under(path: str, under: str) -> Path:
    """Resolve *path* and raise if it is not inside *under*."""
    root = Path(under).resolve()
    resolved = Path(path).resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"path {path} is not under {under}")
    _reject_symlink_path(resolved)
    return resolved


def read_text_under(
    path: str,
    under: str,
    encoding: str = "utf-8-sig",
    *,
    errors: str = "replace",
) -> str:
    """Read a text file after proving it lives under *under*."""
    resolved = resolve_under(path, under)
    return Path(os.fspath(resolved)).read_text(encoding=encoding, errors=errors)


def atomic_write_bytes(filename: str, data: bytes) -> None:
    """Replace a regular file atomically, preserving mode and old contents."""
    path = Path(filename)
    _reject_symlink_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing_mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else None
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as handle:
            temp_name = handle.name
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_name, existing_mode if existing_mode is not None else 0o644)
        os.replace(temp_name, path)
        opener = globals().get("FileOpener")
        if opener is not None:
            opener.invalidate(str(path))
        temp_name = None
    finally:
        if temp_name is not None:
            try:
                os.unlink(temp_name)
            except FileNotFoundError:
                pass


def atomic_write_text(
    filename: str,
    text: str,
    encoding: str = "utf-8",
    *,
    bom: Optional[bool] = None,
) -> None:
    """Atomically write text, preserving an existing UTF-8 BOM by default."""
    path = Path(filename)
    _reject_symlink_path(path)
    existing = b""
    if path.exists():
        try:
            existing = path.read_bytes()
        except OSError:
            existing = b""
    if bom is None:
        bom = existing.startswith(b"\xef\xbb\xbf")
    if b"\r\n" in existing and "\n" in text:
        text = text.replace("\r\n", "\n").replace("\n", "\r\n")
    text = text.removeprefix("\ufeff")
    if bom:
        text = "\ufeff" + text
    output_encoding = "utf-8" if encoding == "utf-8-sig" else encoding
    atomic_write_bytes(filename, text.encode(output_encoding, errors="strict"))


def write_text_under(
    path: str,
    under: str,
    text: str,
    encoding: str = "utf-8",
) -> None:
    """Write text after proving *path* lives under *under*."""
    resolved = resolve_under(path, under)
    atomic_write_text(str(resolved), text, encoding=encoding)


def clean_filepath(filepath: str) -> str:
    """Trim a filepath to start from the first known mod directory."""
    for prefix in ("common", "events", "history", "interface"):
        if prefix in filepath:
            return prefix + filepath.split(prefix, 1)[1]
    return filepath


# Common Hearts of Iron IV install locations, checked when a validator needs
# vanilla game files (defines, interface, gfx) that the mod doesn't ship.
HOI4_INSTALL_PATHS = [
    # Linux (Steam)
    os.path.expanduser(
        "~/.steam/debian-installation/steamapps/common/Hearts of Iron IV"
    ),
    os.path.expanduser("~/.local/share/Steam/steamapps/common/Hearts of Iron IV"),
    os.path.expanduser("~/.steam/steam/steamapps/common/Hearts of Iron IV"),
    # Windows (Steam)
    "C:/Program Files (x86)/Steam/steamapps/common/Hearts of Iron IV",
    "C:/Program Files/Steam/steamapps/common/Hearts of Iron IV",
    # macOS (Steam)
    os.path.expanduser(
        "~/Library/Application Support/Steam/steamapps/common/Hearts of Iron IV"
    ),
    # Windows (GOG)
    "C:/GOG Games/Hearts of Iron IV",
    "C:/Program Files (x86)/GOG Galaxy/Games/Hearts of Iron IV",
]


def find_hoi4_install(explicit_path: Optional[str] = None) -> Optional[str]:
    """Return the first existing HOI4 install root, checking explicit_path, $HOI4_PATH, then HOI4_INSTALL_PATHS."""
    candidates: List[str] = []
    if explicit_path:
        candidates.append(explicit_path)
    env_path = os.environ.get("HOI4_PATH")
    if env_path:
        candidates.append(env_path)
    candidates.extend(HOI4_INSTALL_PATHS)
    for base in candidates:
        if base and os.path.isdir(base):
            return base
    return None


def get_all_idea_categories(mod_root: Optional[str] = None) -> List[Dict]:
    """Parse common/idea_tags/*.txt and return every idea category in order.

    Returns a list of dicts (definition order preserved) with keys:
    `name`, `hidden` (bool), `has_slot` (bool), `has_char_slot` (bool),
    `type` (str or None — e.g. national_spirit, army_spirit).

    Definition order matters: the engine assigns each politics-view category
    icon a frame of GFX_idea_categories by the order it appears here.

    Args:
        mod_root: Path to the mod root (auto-detected if None).
    """
    if mod_root is None:
        mod_root = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))

    tags_dir = os.path.join(mod_root, "common", "idea_tags")
    if not os.path.isdir(tags_dir):
        return []

    out: List[Dict] = []
    try:
        filenames = sorted(os.listdir(tags_dir))
    except OSError:
        return out

    for fname in filenames:
        if not fname.endswith(".txt"):
            continue
        fpath = os.path.join(tags_dir, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                text = re.sub(r"#.*", "", f.read())
        except Exception:
            continue

        m = re.search(r"idea_categories\s*=\s*\{", text)
        if not m:
            continue
        start = m.end()
        i, balanced = find_unquoted_block_end(text, start)
        cat_block = text[start : i - 1] if balanced else text[start:]

        pos = 0
        while True:
            cat_m = re.search(r"(\w+)\s*=\s*\{", cat_block[pos:])
            if not cat_m:
                break
            cat_name = cat_m.group(1)
            cat_start = pos + cat_m.end()
            cat_i, cat_balanced = find_unquoted_block_end(cat_block, cat_start)
            cat_body = (
                cat_block[cat_start : cat_i - 1]
                if cat_balanced
                else cat_block[cat_start:]
            )
            type_m = re.search(r"\btype\s*=\s*(\w+)", cat_body)
            out.append(
                {
                    "name": cat_name,
                    "hidden": bool(re.search(r"\bhidden\s*=\s*yes\b", cat_body)),
                    "has_slot": bool(re.search(r"\bslot\s*=", cat_body)),
                    "has_char_slot": bool(re.search(r"\bcharacter_slot\s*=", cat_body)),
                    "type": type_m.group(1) if type_m else None,
                }
            )
            pos = cat_i

    return out


@lru_cache(maxsize=None)
def _non_selectable_idea_categories_cached(mod_root: str) -> frozenset:
    categories = {
        c["name"]
        for c in get_all_idea_categories(mod_root)
        if c["hidden"] or (not c["has_slot"] and not c["has_char_slot"])
    }
    return (
        frozenset(categories) if categories else frozenset({"country", "hidden_ideas"})
    )


def get_non_selectable_idea_categories(mod_root: Optional[str] = None) -> frozenset:
    """Return non-selectable idea categories for one normalized mod root."""
    if mod_root is None:
        mod_root = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
    normalized = os.path.normcase(os.path.abspath(os.path.normpath(mod_root)))
    return _non_selectable_idea_categories_cached(normalized)


@lru_cache(maxsize=None)
def _slotless_idea_categories_cached(mod_root: str) -> frozenset:
    return frozenset(
        c["name"]
        for c in get_all_idea_categories(mod_root)
        if not c["has_slot"] and not c["has_char_slot"]
    )


def get_slotless_idea_categories(mod_root: Optional[str] = None) -> frozenset:
    """Return idea categories with no slot of any kind.

    Narrower than get_non_selectable_idea_categories, which also counts a hidden
    category that still has a slot (dynamic_modifier_slots). An idea here can
    only arrive through add_idea, so its `allowed` gate is never consulted; one
    in a slotted category still filters the pool the slot draws from.

    Empty when common/idea_tags/ is missing or unparseable. This backs an
    ERROR-severity check, so it guesses at nothing: no categories means the
    check goes quiet rather than blocking a PR on a hardcoded assumption.
    """
    if mod_root is None:
        mod_root = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
    normalized = os.path.normcase(os.path.abspath(os.path.normpath(mod_root)))
    return _slotless_idea_categories_cached(normalized)


def find_line_number(filename: str, pattern: str, lowercase: bool = True) -> int:
    # Reads via FileOpener so iterating many lookups against the same file
    # only hits disk once.
    try:
        content = FileOpener.open_text_file(
            filename, lowercase=lowercase, strip_comments_flag=False
        )
        needle = pattern.lower() if lowercase else pattern
        idx = content.find(needle)
        if idx >= 0:
            return content.count("\n", 0, idx) + 1
    except Exception:
        pass
    return 0


def strip_comments(text: str) -> str:
    """Remove comment-only lines and inline comments from text."""
    lines = text.split("\n")
    result = []
    for line in lines:
        if "#" not in line:
            result.append(line)
            continue
        if line.lstrip().startswith("#"):
            result.append("")
            continue
        in_quote = False
        for i, ch in enumerate(line):
            if ch == '"':
                in_quote = not in_quote
            elif ch == "#" and not in_quote:
                line = line[:i]
                break
        result.append(line)
    return "\n".join(result)


def blank_quoted_strings(text: str, keep_start: Optional[Set[int]] = None) -> str:
    """Replace the interior of double-quoted strings with spaces.

    Quotes, string length, and newlines are preserved so byte offsets and line
    numbers stay valid; only interior characters are blanked. Neutralizes
    braces / ``#`` / ``=`` inside a quoted log string that would otherwise
    desync a brace-depth or token scan. Run AFTER comment stripping — a stray
    ``"`` in a ``#`` comment would otherwise flip the in-string state.

    ``keep_start``, if given, is a set of offsets of opening ``"`` characters
    whose string contents are left untouched — for a caller that must preserve
    specific quoted values (e.g. a ``has_dlc = "X"`` name) while still handling
    escaped quotes (``\\"``) correctly everywhere else.
    """
    if '"' not in text:
        return text
    out = list(text)
    in_str = False
    start = -1
    keep = keep_start or ()
    for i, c in enumerate(text):
        if c == '"' and (i == 0 or text[i - 1] != "\\"):
            if not in_str:
                start = i
            in_str = not in_str
        elif in_str and c != "\n" and start not in keep:
            out[i] = " "
    return "".join(out)


def flat_block_text(block: str) -> str:
    """Strip an outer brace pair, but only when the two actually match.

    A bare body ending in the `}` of its last child keeps both characters — a
    naive strip there would delete an unrelated brace and desync every depth
    count downstream.
    """
    inner = block.strip()
    if inner.startswith("{") and find_matching_brace(inner, 0) == len(inner) - 1:
        return inner[1:-1]
    return inner


def iter_flat_offsets(block: str) -> Iterator[Tuple[str, int]]:
    """Yield offsets at brace depth zero, skipping comments and nested blocks."""
    inner = flat_block_text(block)
    depth = 0
    index = 0
    while index < len(inner):
        char = inner[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
        elif char == "#":
            while index < len(inner) and inner[index] != "\n":
                index += 1
            continue
        elif depth == 0:
            yield inner, index
        index += 1


_STATEMENT = re.compile(r"([A-Za-z_][A-Za-z0-9_.:@]*)\s*(>=|<=|==|=|>|<)")
_FOCUS_START = re.compile(r"^[ \t]*(focus|shared_focus|joint_focus)\s*=\s*\{", re.M)
_FOCUS_ID = re.compile(r"^[ \t]*id\s*=\s*(\S+)", re.M)


def read_script(path: str, keep_quotes: bool = False) -> str:
    """Read a mod file and neutralise comments, and by default quoted strings.

    Both passes preserve length and newlines, so every offset and line number
    computed downstream still points at the original file. `keep_quotes` is for
    files whose quoted values are the data (loc key names in a game rule).
    """
    with open(path, "r", encoding="utf-8-sig", errors="replace") as handle:
        text = strip_comments(handle.read())
    return text if keep_quotes else blank_quoted_strings(text)


def iter_statement_ops(
    body: str,
) -> Iterator[Tuple[str, str, Optional[str], Optional[str]]]:
    """Yield (key, operator, scalar, block) for every statement at depth 0."""
    index = 0
    length = len(body)
    while index < length:
        if body[index] in "{}":
            index += 1
            continue
        match = _STATEMENT.match(body, index)
        if not match:
            index += 1
            continue
        key, operator = match.group(1), match.group(2)
        cursor = match.end()
        while cursor < length and body[cursor] in " \t\r\n":
            cursor += 1
        if cursor < length and body[cursor] == "{":
            close = find_matching_brace(body, cursor)
            if close == -1:
                return
            yield key, operator, None, body[cursor + 1 : close]
            index = close + 1
            continue
        if cursor < length and body[cursor] == '"':
            stop = body.find('"', cursor + 1)
            if stop == -1:
                return
            yield key, operator, body[cursor + 1 : stop], None
            index = stop + 1
            continue
        stop = cursor
        while stop < length and body[stop] not in " \t\r\n{}":
            stop += 1
        yield key, operator, body[cursor:stop], None
        index = stop


def iter_statements(body: str) -> Iterator[Tuple[str, Optional[str], Optional[str]]]:
    """Yield (key, scalar, block) for every `key = ...` at depth 0 of *body*."""
    for key, _operator, scalar, block in iter_statement_ops(body):
        yield key, scalar, block


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def iter_focus_blocks(text: str) -> Iterator[Tuple[str, str, int, str]]:
    """Yield (id, kind, line, body) for each focus of a focus tree file.

    A block without an `id` is skipped rather than reported under a made-up
    name; the game ignores it too.
    """
    position = 0
    while True:
        match = _FOCUS_START.search(text, position)
        if not match:
            return
        open_index = text.index("{", match.start())
        close = find_matching_brace(text, open_index)
        if close == -1:
            return
        body = text[open_index + 1 : close]
        position = close + 1
        id_match = _FOCUS_ID.search(body)
        if id_match:
            yield id_match.group(1), match.group(1), line_of(text, match.start()), body


_IS_AI_YES_RE = re.compile(r"is_ai\s*=\s*yes\b")
# The three trigger blocks that can hide a decision or category from a player.
_AI_GATE_FIELDS = ("visible", "available", "allowed")
_TOP_LEVEL_BLOCK_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\{", re.MULTILINE)


def first_flat_match(
    block: str, pattern: "re.Pattern[str]"
) -> Optional["re.Match[str]"]:
    """First match of *pattern* sitting unconditionally at depth 0 of a block.

    Nested inside NOT/OR/AND/if/limit or a scoped `TAG = { }` a token is
    conditional and means something different: `NOT = { has_country_flag = X }`
    is satisfied until X is set, the opposite of a gate that X opens.
    ``iter_flat_offsets`` yields every depth-0 character position, hence the
    preceding-whitespace guard against matching mid-token.
    """
    if not block:
        return None
    for inner, index in iter_flat_offsets(block):
        if index and not inner[index - 1].isspace():
            continue
        match = pattern.match(inner, index)
        if match:
            return match
    return None


def has_flat_is_ai(block: str) -> bool:
    """True when `is_ai = yes` sits unconditionally at depth 0 of a trigger block."""
    return first_flat_match(block, _IS_AI_YES_RE) is not None


def iter_direct_child_blocks(
    body: str, opener: "re.Pattern[str]"
) -> Iterator[Tuple["re.Match[str]", int, int]]:
    """Yield `(match, open_idx, close_idx)` for every *opener* block at depth 0.

    Depth-aware so a nested `visible` inside a `modifier` or an effect's `limit`
    is never mistaken for the object's own trigger block. Each hit advances past
    its own closing brace, which keeps the depth count balanced — landing back
    on that `}` would decrement a depth the matching `{` never incremented.
    """
    index = 0
    depth = 0
    while index < len(body):
        char = body[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
        elif depth == 0:
            match = opener.match(body, index)
            if match:
                close = find_matching_brace(body, match.end() - 1)
                if close == -1:
                    return
                yield match, match.end() - 1, close
                index = close + 1
                continue
        index += 1


def direct_child_block(body: str, name: str) -> str:
    """Return the `name = { ... }` block at depth 0 of *body*, braces included.

    Returns "" when there is no such block.
    """
    opener = re.compile(r"\b" + re.escape(name) + r"\s*=\s*\{")
    for _match, open_idx, close in iter_direct_child_blocks(body, opener):
        return body[open_idx : close + 1]
    return ""


def is_ai_only_block(body: str) -> bool:
    """True when a decision or category body is gated on an unconditional `is_ai = yes`.

    Accepts the body with or without its outer braces.
    """
    inner = flat_block_text(body)
    return any(has_flat_is_ai(direct_child_block(inner, f)) for f in _AI_GATE_FIELDS)


def ai_only_decision_categories(mod_path: str) -> Dict[str, str]:
    """Decision categories no human player ever sees, mapped to their filename.

    Every decision inside one inherits that: it needs no localisation and no
    tooltip wrapper, because there is nobody to read either. The basename comes
    back with the name so a finding can cite its source without a second walk
    over the same directory.
    """
    root = Path(mod_path) / "common" / "decisions" / "categories"
    names: Dict[str, str] = {}
    for path in sorted(root.rglob("*.txt")):
        try:
            text = path.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue
        if "is_ai" not in text:
            continue
        text = strip_comments(text)
        for match in _TOP_LEVEL_BLOCK_RE.finditer(text):
            body, _end = extract_block_from_text(text, match.end() - 1)
            if body and is_ai_only_block(body):
                names.setdefault(match.group(1), path.name)
    return names


class FileOpener:
    # LRU bound sized for common/ (~3600 files) plus localisation, so a broad
    # scan stays cached without evicting on every overflow.
    _cache: "OrderedDict[Tuple, str]" = OrderedDict()
    _MAX_CACHE_SIZE = 8192

    @classmethod
    def open_text_file(
        cls, filename: str, lowercase: bool = False, strip_comments_flag: bool = False
    ) -> str:
        # Linux-first default: HOI4 is case-sensitive on Linux, so validators
        # must match and report the exact case as written. Pass lowercase=True
        # only for deliberately case-insensitive lookups.
        cache_key = (filename, lowercase, strip_comments_flag)
        cached = cls._cache.get(cache_key)
        if cached is not None:
            cls._cache.move_to_end(cache_key)
            return cached
        content = read_text_strict(filename)
        if strip_comments_flag:
            content = strip_comments(content)
        if lowercase:
            content = content.lower()
        cls._cache[cache_key] = content
        if len(cls._cache) > cls._MAX_CACHE_SIZE:
            cls._cache.popitem(last=False)
        return content

    @classmethod
    def invalidate(cls, filename: str) -> None:
        """Drop every cached representation of one file."""
        target = os.path.abspath(os.fspath(filename))
        for key in [
            key for key in cls._cache if os.path.abspath(os.fspath(key[0])) == target
        ]:
            del cls._cache[key]

    @classmethod
    def clear_cache(cls) -> None:
        cls._cache.clear()


class DataCleaner:
    """Helper class for cleaning data structures"""

    @classmethod
    def clear_false_positives(cls, input_iter, false_positives: tuple = ()):
        """Remove false positives from a dictionary or list"""
        if isinstance(input_iter, dict):
            if len(false_positives) > 0:
                for key in false_positives:
                    try:
                        input_iter.pop(key)
                    except KeyError:
                        continue
            return input_iter
        elif isinstance(input_iter, list):
            if len(false_positives) > 0:
                return [i for i in input_iter if i not in false_positives]
            return input_iter

    @classmethod
    def clear_false_positives_partial_match(
        cls, input_iter, false_positives: tuple = ()
    ):
        """Remove items that partially match false positives"""
        if isinstance(input_iter, dict):
            if len(false_positives) > 0:
                skip_list = []
                for k in input_iter:
                    for f in false_positives:
                        if f in k:
                            skip_list.append(k)
                for i in skip_list:
                    if i in input_iter:
                        input_iter.pop(i)
            return input_iter
        elif isinstance(input_iter, list):
            if len(false_positives) > 0:
                skip_list = []
                for k in input_iter:
                    for f in false_positives:
                        if f in k:
                            skip_list.append(k)
                input_iter = [i for i in input_iter if i not in skip_list]
            return input_iter


def timing_enabled() -> bool:
    """Return True unless MD_TIMING=0 is explicitly set."""
    return os.environ.get("MD_TIMING", "1") != "0"


class Timer:
    """Lightweight timer that prints elapsed time to stderr. Suppress with MD_TIMING=0."""

    def __init__(self, label: str, enabled: Optional[bool] = None):
        self.label = label
        self.enabled = enabled if enabled is not None else timing_enabled()
        self._start: Optional[float] = None
        self.elapsed: float = 0.0

    def start(self):
        self._start = time.perf_counter()
        return self

    def stop(self) -> float:
        if self._start is not None:
            self.elapsed = time.perf_counter() - self._start
            self._start = None
        if self.enabled:
            print(
                f"  \033[90m[timer] {self.label}: {self.elapsed:.3f}s\033[0m",
                file=sys.stderr,
            )
        return self.elapsed

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()
        return False


def compute_line_offsets(text: str) -> List[int]:
    # Pair with line_for_offset() to turn per-match line lookups from O(N)
    # (text.count) into O(log N) (bisect). Worth the upfront pass when one
    # file is scanned many times.
    offsets: List[int] = []
    start = 0
    while True:
        p = text.find("\n", start)
        if p == -1:
            break
        offsets.append(p)
        start = p + 1
    return offsets


def line_for_offset(offsets: List[int], pos: int) -> int:
    # bisect_left (not bisect_right) so a pos landing on a newline reports
    # the line the newline ends, matching text.count("\n", 0, pos) + 1.
    return bisect.bisect_left(offsets, pos) + 1


def print_timing_summary(timings: List[Tuple[str, float]]):
    """Print a table of step timings. Suppressed when MD_TIMING=0."""
    if not timings or not timing_enabled():
        return
    # ANSI only on a live terminal — piped/CI output must stay escape-free.
    dim, reset = ("\033[90m", "\033[0m") if sys.stderr.isatty() else ("", "")
    total = sum(t for _, t in timings)
    max_label = max(len(label) for label, _ in timings)
    print(f"\n{dim}{'─' * (max_label + 18)}", file=sys.stderr)
    print("  Timing summary:", file=sys.stderr)
    for label, elapsed in timings:
        bar_len = round(elapsed / total * 20) if total > 0 else 0
        bar = "█" * bar_len + "░" * (20 - bar_len)
        print(
            f"  {label:<{max_label}}  {elapsed:6.3f}s  {bar}",
            file=sys.stderr,
        )
    print(f"  {'total':<{max_label}}  {total:6.3f}s", file=sys.stderr)
    print(f"{'─' * (max_label + 18)}{reset}", file=sys.stderr)


def create_linting_parser(
    description: str,
    include_diff: bool = True,
    extra_args_fn=None,
) -> argparse.ArgumentParser:
    """Standard argument parser for linting scripts. Custom args via extra_args_fn(parser)."""
    parser = argparse.ArgumentParser(description=description)
    modes = ["all", "staged"]
    if include_diff:
        modes.insert(1, "diff")
    parser.add_argument(
        "--mode",
        choices=modes,
        default="all",
        help="Check mode (default: all)",
    )
    if include_diff:
        parser.add_argument(
            "--base-branch",
            default="main",
            help="Base branch for diff comparison (default: main)",
        )
    parser.add_argument(
        "--files", nargs="+", help="Specific files to check (overrides mode)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=max(1, min(cpu_budget(), 4)),
        help="Number of parallel workers (default: min(CPU budget, 4))",
    )
    parser.add_argument(
        "filenames",
        nargs="*",
        help="Files to check (positional, for pre-commit)",
    )
    if extra_args_fn:
        extra_args_fn(parser)
    return parser


def collect_files_by_mode(
    args,
    root_dir: str,
    include_interface: bool = False,
) -> List[str]:
    """Collect files based on parsed --mode / --files / positional args."""
    if getattr(args, "filenames", None):
        files_list = args.filenames
    elif getattr(args, "files", None):
        files_list = args.files
    elif args.mode == "diff":
        base = getattr(args, "base_branch", "main")
        files_list = get_git_diff_files(
            base_branch=base, include_interface=include_interface
        )
    elif args.mode == "staged":
        files_list = get_git_diff_files(
            staged_only=True, include_interface=include_interface
        )
    else:
        files_list = get_all_txt_files(root_dir, include_interface=include_interface)

    existing = [f for f in files_list if os.path.exists(f)]
    missing = len(files_list) - len(existing)
    if missing:
        print(f"WARNING: {missing} file(s) not found, skipping")
    return existing


def get_root_dir() -> str:
    """Resolve the mod root directory (two levels up from tools/linting/)."""
    return os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.realpath(sys.argv[0])))
    )


def add_dry_run_argument(parser: argparse.ArgumentParser) -> None:
    """Add the standard `--dry-run` flag shared by the auto-fixer sweeps."""
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be fixed without writing changes",
    )


def run_linting_sweep(
    args,
    *,
    banner: str,
    file_filter: Callable[[str], bool],
    apply_fn: Callable[[str], Tuple[str, int]],
    dry_run_fn: Callable[[str], Tuple[str, int]],
    unit: str,
    no_files_message: str,
    applied_verb: str = "Fixed",
    dry_run_verb: str = "Would fix",
) -> int:
    """Run a whole-tree auto-fixer sweep and print its standard report.

    *apply_fn* / *dry_run_fn* each take a path and return (path, fix count).
    Returns the process exit code.
    """
    timings = []
    root_dir = get_root_dir()
    print(f"{banner} (Mode: {args.mode}, Dry run: {args.dry_run})")

    with Timer("file collection") as t:
        all_files = collect_files_by_mode(args, root_dir)
    timings.append(("file collection", t.elapsed))

    targets = [f for f in all_files if file_filter(f)]
    if not targets:
        print(no_files_message)
        return 0

    print(f"Processing {len(targets)} files...")

    process_fn = dry_run_fn if args.dry_run else apply_fn
    with Timer("processing") as t:
        results = run_with_pool(process_fn, targets, args.workers)
    timings.append(("processing", t.elapsed))

    action = dry_run_verb if args.dry_run else applied_verb
    files_fixed = [(f, c) for f, c in results if c > 0]
    total_fixes = sum(c for _, c in results)

    for filepath, count in sorted(files_fixed):
        print(f"  {clean_filepath(filepath)}: {action.lower()} {count} {unit}")

    print("\n------")
    print(f"Processed {len(targets)} files")
    print(f"{action} {total_fixes} {unit} in {len(files_fixed)} file(s)")

    elapsed_total = sum(t for _, t in timings)
    print(f"\nCompleted in {elapsed_total:.1f}s")
    print_timing_summary(timings)

    return 0


def run_with_pool(
    func,
    items: list,
    workers: int,
    chunksize: Optional[int] = None,
    initializer=None,
    initargs=(),
):
    """Run func over items using Pool when beneficial, sequential otherwise."""
    if len(items) < 10 or workers == 1:
        return [func(item) for item in items]
    from multiprocessing import Pool

    with Pool(processes=workers, initializer=initializer, initargs=initargs) as pool:
        if chunksize:
            return pool.map(func, items, chunksize=chunksize)
        return pool.map(func, items)


_DEFAULT_DIRECTORIES = ("common", "events", "history")
_DIRECTORIES_WITH_INTERFACE = ("common", "events", "history", "interface")

_staged_files_cache: Optional[List[str]] = None


def _read_staged_from_env() -> Optional[List[str]]:
    """Read cached staged-file list from MD_STAGED_FILES env var."""
    raw = os.environ.get("MD_STAGED_FILES")
    if raw is None:
        return None
    return [f for f in raw.split("\n") if f]


def get_git_diff_files(
    base_branch: str = "main",
    staged_only: bool = False,
    directories: tuple = _DEFAULT_DIRECTORIES,
    include_interface: bool = False,
) -> List[str]:
    """Get list of modified .txt files from git diff.

    Shared implementation used by all linting scripts. Checks the
    MD_STAGED_FILES env var first to avoid redundant git subprocess calls
    during pre-commit runs.
    """
    global _staged_files_cache

    if include_interface:
        directories = _DIRECTORIES_WITH_INTERFACE

    if staged_only and _staged_files_cache is not None:
        all_files = _staged_files_cache
    else:
        env_files = _read_staged_from_env() if staged_only else None
        if env_files is not None:
            all_files = env_files
        else:
            try:
                import subprocess as _sp

                if staged_only:
                    cmd = [
                        "git",
                        "diff",
                        "--cached",
                        "--name-only",
                        "--diff-filter=ACMRT",
                    ]
                else:
                    cmd = [
                        "git",
                        "diff",
                        "--name-only",
                        "--diff-filter=ACMRT",
                        f"{base_branch}...HEAD",
                    ]
                result = _sp.run(
                    cmd, capture_output=True, text=True, check=True, timeout=15
                )
                all_files = [f for f in result.stdout.strip().split("\n") if f]
            except Exception:
                return []

        if staged_only:
            _staged_files_cache = all_files

    return [
        f
        for f in all_files
        if f.endswith(".txt")
        and any(f.startswith(d + "/") for d in directories)
        and os.path.exists(f)
    ]


def get_all_txt_files(
    root_dir: str,
    directories: tuple = _DEFAULT_DIRECTORIES,
    include_interface: bool = False,
) -> List[str]:
    """Get all .txt files from relevant directories."""
    import fnmatch

    if include_interface:
        directories = _DIRECTORIES_WITH_INTERFACE

    files_list = []
    for directory in directories:
        dir_path = os.path.join(root_dir, directory)
        if os.path.exists(dir_path):
            for root, _, filenames in os.walk(dir_path):
                for filename in fnmatch.filter(filenames, "*.txt"):
                    files_list.append(os.path.join(root, filename))
    return files_list


def get_staged_files(
    mod_path: str,
    extensions: Optional[List[str]] = None,
    include_missing: bool = False,
) -> Optional[List[str]]:
    """Get list of git changed files for validation.

    First checks for staged (cached) files — used in pre-commit hook context.
    Falls back to the branch diff vs main when nothing is staged, so that
    running --staged on a feature branch validates only the changed files.
    Set include_missing to retain deleted paths for cross-reference checks.
    """
    if extensions is None:
        extensions = [".txt"]

    # Most validators open every changed path, so missing files are filtered
    # unless a cross-reference check needs to observe a deleted target.
    def _filter(names: list) -> list:
        paths = [
            os.path.normpath(os.path.join(mod_path, f))
            for f in names
            if f and any(f.endswith(ext) for ext in extensions)
        ]
        return paths if include_missing else [p for p in paths if os.path.isfile(p)]

    def _git_diff(*args):
        diff_filter = "ACMRD" if include_missing else "ACM"
        output_format = "--name-status" if include_missing else "--name-only"
        command = ["git", "diff"] + list(args) + [output_format]
        if include_missing:
            command.append("--find-renames")
        command.append(f"--diff-filter={diff_filter}")
        result = subprocess.run(
            command,
            cwd=mod_path,
            capture_output=True,
            text=True,
            check=True,
            timeout=15,
        )
        if not include_missing:
            return result.stdout.strip().split("\n")

        names = []
        for line in result.stdout.splitlines():
            status, *paths = line.split("\t")
            if status.startswith(("R", "C")):
                names.extend(paths)
            elif paths:
                names.append(paths[0])
        return names

    env_files = _read_staged_from_env()
    if env_files is not None:
        files = _filter(env_files)
        if not include_missing:
            return files or None
        try:
            files.extend(_filter(_git_diff("--cached")))
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass
        return list(dict.fromkeys(files)) or None

    try:
        # Pre-commit hook context: files added to the index
        files = _filter(_git_diff("--cached"))
        if files:
            return files

        # Feature branch context: files changed vs main
        files = _filter(_git_diff("main...HEAD"))
        if files:
            return files

        return None
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None


def run_tool_main(
    tool_class,
    description: str = "Run tool",
    extra_args_fn=None,
    method_name: str = "process_file",
    argv=None,
    parser=None,
):
    """Main entry point for single-file tools and standardizers.

    Args:
        tool_class: Class to instantiate (DataCleaner subclass or BaseStandardizer).
        description: CLI description string.
        extra_args_fn: Optional callback to add custom argparse arguments.
        method_name: Method to call on the instance (default: "process_file").
        argv: Argument list (default: sys.argv[1:]).
        parser: Custom ArgumentParser (default: create_standard_parser).
    """
    if parser is None:
        parser = create_standard_parser(description)
    if extra_args_fn:
        extra_args_fn(parser)
    args = parser.parse_args(argv)

    if not os.path.exists(args.input_file):
        log_message("ERROR", f"File '{args.input_file}' does not exist")
        sys.exit(1)

    output_file = args.output if args.output else args.input_file

    import inspect

    sig = inspect.signature(tool_class.__init__)
    valid_params = set(sig.parameters.keys()) - {"self"}
    ctor_kwargs = {}
    if "verbose" in valid_params:
        ctor_kwargs["verbose"] = args.verbose
    if "use_colors" in valid_params:
        ctor_kwargs["use_colors"] = not getattr(args, "no_color", False)
    tool = tool_class(**ctor_kwargs)

    if args.backup:
        backup_file = create_backup(args.input_file)
        if not backup_file:
            sys.exit(1)

    log_message("INFO", f"Starting processing of {args.input_file}", args.verbose)

    method = getattr(tool, method_name)
    if method(args.input_file, output_file):
        log_message("SUCCESS", f"Processing completed: {output_file}")
    else:
        log_message("ERROR", "Processing failed")
        sys.exit(1)


def run_validator_main(
    validator_class, description: str = "Run validation", extra_args_fn=None
):
    """Main entry point for running validators with standard argument parsing"""
    parser = create_validation_parser(description)
    if extra_args_fn:
        extra_args_fn(parser)
    args = parser.parse_args()

    mod_path = Path(args.path).resolve()
    if not mod_path.exists():
        log_message("ERROR", f"Path does not exist: {mod_path}")
        sys.exit(1)
    if not mod_path.is_dir():
        log_message("ERROR", f"Path is not a directory: {mod_path}")
        sys.exit(1)

    if getattr(args, "no_cache", False):
        os.environ["MD_NO_CACHE"] = "1"

    kwargs = dict(
        output_file=args.output,
        use_colors=not args.no_color,
        staged_only=args.staged,
        workers=args.workers,
        no_cache=getattr(args, "no_cache", False),
    )
    if extra_args_fn:
        for key in vars(args):
            if key not in (
                "path",
                "strict",
                "output",
                "no_color",
                "staged",
                "workers",
                "no_cache",
            ):
                kwargs[key] = getattr(args, key)

    validator = validator_class(str(mod_path), **kwargs)
    errors_found = validator.run_all_validations()

    if args.strict and errors_found > 0:
        sys.exit(1)
    else:
        sys.exit(0)
