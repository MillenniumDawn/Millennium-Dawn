#!/usr/bin/env python3

"""Shared utilities for Millennium Dawn tools (standardization and validation)."""

import argparse
import bisect
import logging
import os
import re
import sys
import time
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

COLORS = {
    "SUCCESS": "\033[92m",  # Green
    "INFO": "\033[94m",  # Blue
    "DEBUG": "\033[90m",  # Gray
    "WARNING": "\033[93m",  # Yellow
    "ERROR": "\033[91m",  # Red
}
RESET_COLOR = "\033[0m"


def log_message(
    level: str, message: str, verbose: bool = False, use_colors: bool = True
):
    """Log a message with timestamp and optional color coding"""
    if level == "DEBUG" and not verbose:
        return

    timestamp = datetime.now().strftime("%H:%M:%S")

    color = COLORS.get(level, "") if use_colors else ""
    reset_color = RESET_COLOR if use_colors else ""

    formatted_message = f"{color}[{timestamp}] {level}: {message}{reset_color}"
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
        "--workers",
        type=int,
        default=None,
        help=f"Number of worker processes (default: auto-detect)",
    )
    return parser


def extract_block(lines: List[str], start_index: int) -> Tuple[List[str], int]:
    """Extract a multi-line block by counting braces"""
    if start_index >= len(lines):
        return [], start_index

    block_lines = []
    brace_count = 0
    i = start_index

    while i < len(lines):
        line = lines[i]
        block_lines.append(line)

        brace_count += line.count("{") - line.count("}")

        if brace_count == 0 and "{" in lines[start_index]:
            i += 1
            break
        elif brace_count < 0:
            # Malformed: more closing than opening braces.
            break

        i += 1

    return block_lines, i  # position AFTER the block, not i-1


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
    n = len(text)
    body_start = open_pos + 1
    depth = 1
    i = body_start
    in_str = False
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
                    return text[body_start:i], i + 1
        i += 1
    return "", -1


def compact_block(block_lines: List[str]) -> List[str]:
    """Completely compact a block by removing all internal blank lines"""
    if not block_lines:
        return block_lines

    compacted = []
    for line in block_lines:
        if line.strip():
            compacted.append(line.rstrip())

    return compacted


def create_backup(filename: str) -> str:
    """Create a backup of the input file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"{filename}.backup.{timestamp}"

    try:
        with open(filename, "r", encoding="utf-8") as src:
            with open(backup_filename, "w", encoding="utf-8") as dst:
                dst.write(src.read())
        log_message("INFO", f"Backup created: {backup_filename}")
        return backup_filename
    except Exception as e:
        log_message("ERROR", f"Failed to create backup: {str(e)}")
        return ""


def should_skip_file(
    filename: str, extra_skip_patterns: Optional[List[str]] = None
) -> bool:
    """Check if a file should be skipped during processing"""
    IGNORED_DIRS = ["gfx", "tools", "resources", "docs", "map"]

    normalized_path = filename.replace("\\", "/")
    for ignored_dir in IGNORED_DIRS:
        if f"/{ignored_dir}/" in normalized_path or normalized_path.startswith(
            f"{ignored_dir}/"
        ):
            return True
    if extra_skip_patterns:
        for pattern in extra_skip_patterns:
            if pattern in filename:
                return True
    return False


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

    for fname in sorted(os.listdir(tags_dir)):
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
        depth = 1
        i = start
        while i < len(text) and depth > 0:
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
            i += 1
        cat_block = text[start : i - 1] if depth == 0 else text[start:]

        pos = 0
        while True:
            cat_m = re.search(r"(\w+)\s*=\s*\{", cat_block[pos:])
            if not cat_m:
                break
            cat_name = cat_m.group(1)
            cat_start = pos + cat_m.end()
            cat_depth = 1
            cat_i = cat_start
            while cat_i < len(cat_block) and cat_depth > 0:
                if cat_block[cat_i] == "{":
                    cat_depth += 1
                elif cat_block[cat_i] == "}":
                    cat_depth -= 1
                cat_i += 1
            cat_body = (
                cat_block[cat_start : cat_i - 1]
                if cat_depth == 0
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


def get_non_selectable_idea_categories(mod_root: Optional[str] = None) -> frozenset:
    """Parse common/idea_tags/*.txt and return non-selectable idea category names.

    A category is non-selectable if it has `hidden = yes` or has neither
    `slot =` nor `character_slot =` entries (like `country` with
    `type = national_spirit`). These are categories where ideas are only
    added/removed via script (add_ideas/remove_ideas), never picked in the UI,
    so `allowed = { always = no }` is always redundant.

    Args:
        mod_root: Path to the mod root (auto-detected if None).
    Returns:
        frozenset of non-selectable category names (e.g. {'country', 'hidden_ideas'}).
    """
    categories = {
        c["name"]
        for c in get_all_idea_categories(mod_root)
        if c["hidden"] or (not c["has_slot"] and not c["has_char_slot"])
    }
    return (
        frozenset(categories) if categories else frozenset({"country", "hidden_ideas"})
    )


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
        stripped = line.lstrip()
        if stripped.startswith("#"):
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
        try:
            with open(filename, "r", encoding="utf-8-sig") as text_file:
                content = text_file.read()
                if strip_comments_flag:
                    content = strip_comments(content)
                if lowercase:
                    content = content.lower()
        except Exception as ex:
            log_message("WARNING", f"Skipping file {filename}: {ex}")
            return ""
        cls._cache[cache_key] = content
        if len(cls._cache) > cls._MAX_CACHE_SIZE:
            cls._cache.popitem(last=False)
        return content


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

    def __exit__(self, *exc):
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
    total = sum(t for _, t in timings)
    max_label = max(len(label) for label, _ in timings)
    print(f"\n\033[90m{'─' * (max_label + 18)}", file=sys.stderr)
    print(f"  Timing summary:", file=sys.stderr)
    for label, elapsed in timings:
        bar_len = int(elapsed / total * 20) if total > 0 else 0
        bar = "█" * bar_len + "░" * (20 - bar_len)
        print(
            f"  {label:<{max_label}}  {elapsed:6.3f}s  {bar}",
            file=sys.stderr,
        )
    print(f"  {'total':<{max_label}}  {total:6.3f}s", file=sys.stderr)
    print(f"{'─' * (max_label + 18)}\033[0m", file=sys.stderr)


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
        help=f"Check mode (default: all)",
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
        default=max(1, min(os.cpu_count() or 2, 4)),
        help="Number of parallel workers (default: min(CPU count, 4))",
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


def run_with_pool(func, items: list, workers: int, chunksize: int = None):
    """Run func over items using Pool when beneficial, sequential otherwise."""
    if len(items) < 10 or workers == 1:
        return [func(item) for item in items]
    from multiprocessing import Pool

    with Pool(processes=workers) as pool:
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
    mod_path: str, extensions: Optional[List[str]] = None
) -> Optional[List[str]]:
    """Get list of git changed files for validation.

    First checks for staged (cached) files — used in pre-commit hook context.
    Falls back to the branch diff vs main when nothing is staged, so that
    running --staged on a feature branch validates only the changed files.
    """
    if extensions is None:
        extensions = [".txt"]

    def _filter(names: list) -> list:
        return [
            os.path.join(mod_path, f)
            for f in names
            if f and any(f.endswith(ext) for ext in extensions)
        ]

    env_files = _read_staged_from_env()
    if env_files is not None:
        return _filter(env_files) or None

    try:
        import subprocess

        def _git_diff(*args):
            result = subprocess.run(
                ["git", "diff"] + list(args) + ["--name-only", "--diff-filter=ACM"],
                cwd=mod_path,
                capture_output=True,
                text=True,
                check=True,
                timeout=15,
            )
            return result.stdout.strip().split("\n")

        # Pre-commit hook context: files added to the index
        files = _filter(_git_diff("--cached"))
        if files:
            return files

        # Feature branch context: files changed vs main
        files = _filter(_git_diff("main...HEAD"))
        if files:
            return files

        return None
    except subprocess.CalledProcessError:
        return None
    except ImportError:
        log_message("WARNING", "Git not available, skipping staged file detection")
        return None


def run_tool_main(tool_class, description: str = "Run tool", extra_args_fn=None):
    """Main entry point for running tools with standard argument parsing"""
    parser = create_standard_parser(description)
    if extra_args_fn:
        extra_args_fn(parser)
    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        log_message("ERROR", f"File '{args.input_file}' does not exist")
        sys.exit(1)

    output_file = args.output if args.output else args.input_file
    tool = tool_class(verbose=args.verbose, use_colors=not args.no_color)

    if args.backup:
        backup_file = create_backup(args.input_file)
        if not backup_file:
            sys.exit(1)

    log_message("INFO", f"Starting processing of {args.input_file}", args.verbose)

    if tool.process_file(args.input_file, output_file):
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

    kwargs = dict(
        output_file=args.output,
        use_colors=not args.no_color,
        staged_only=args.staged,
        workers=args.workers,
    )
    if extra_args_fn:
        for key in vars(args):
            if key not in ("path", "strict", "output", "no_color", "staged", "workers"):
                kwargs[key] = getattr(args, key)

    validator = validator_class(str(mod_path), **kwargs)
    errors_found = validator.run_all_validations()

    if args.strict and errors_found > 0:
        sys.exit(1)
    else:
        sys.exit(0)
