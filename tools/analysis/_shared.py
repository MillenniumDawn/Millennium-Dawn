"""Shared search-loop helpers for find_idea_references.py and find_scripted_loc_references.py."""

import re
import sys
from pathlib import Path
from typing import Iterator

REPO_ROOT = Path(__file__).resolve().parents[2]


def configure_import_paths() -> None:
    """Make shared tools importable when a finder runs as a script."""
    tools_dir = str(REPO_ROOT / "tools")
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)


def read_text_lines(filepath: Path) -> list[str] | None:
    """Return UTF-8 text lines, ignoring files that cannot be read."""
    try:
        return filepath.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None


def compile_token_regex(names: list[str]) -> re.Pattern[str]:
    """Compile a regex matching any of `names` as a whole word/token."""
    return re.compile(r"(?<![\w])(?:" + "|".join(map(re.escape, names)) + r")(?![\w])")


def iter_existing_dirs(search_dirs: list[Path]) -> Iterator[Path]:
    """Yield each directory in `search_dirs` that exists on disk."""
    for search_dir in search_dirs:
        if search_dir.is_dir():
            yield search_dir


def iter_readable_files(
    search_dirs: list[Path], patterns: tuple[str, ...]
) -> Iterator[tuple[Path, list[str]]]:
    """Yield readable files matching *patterns* below existing search dirs."""
    for search_dir in iter_existing_dirs(search_dirs):
        for pattern in patterns:
            for filepath in search_dir.rglob(pattern):
                lines = read_text_lines(filepath)
                if lines is not None:
                    yield filepath, lines
