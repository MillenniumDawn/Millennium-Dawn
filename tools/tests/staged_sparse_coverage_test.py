#!/usr/bin/env python3
"""Coverage guard for the staged-integration checkout (sparse or full).

The staged validators serve reference lookups from full-tree globs even in
--staged mode (ignore_staged=True). If the CI sparse worktree ever drops one
of those trees, the globs return [] and checks silently narrow instead of
failing. These floors fail loudly instead.

Read-only and fast; runs in the default sweep and in the CI worktree run.
"""

import glob
import os
from unittest import SkipTest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PROFILE = os.path.join(REPO_ROOT, "tools", "validation", "staged_sparse_profile.txt")

# Glob pattern -> minimum file count. Floors sit near half of current counts:
# they catch an emptied scan, never normal content churn.
COVERAGE = {
    "events/**/*.txt": 100,
    "common/**/*.txt": 2000,
    "history/countries/*.txt": 200,
    "history/states/*.txt": 500,
    "history/units/*.txt": 500,
    "localisation/english/**/*.yml": 150,
    "interface/**/*.gfx": 100,
    "gfx/flags/**/*.tga": 5000,
    "common/technologies/*.txt": 10,
    "common/scripted_localisation/*.txt": 20,
    "common/on_actions/**/*.txt": 20,
    "common/national_focus/*.txt": 50,
}

# Single files validators open directly (colors, typo list, engine doc).
SENTINELS = [
    "interface/core.gfx",
    ".claude/docs/typo-watchlist.md",
    "resources/documentation/dynamic_variables_documentation.md",
    "pyproject.toml",
]

# Anchored sparse paths the CI worktree profile must keep. Root-anchored on
# purpose: a bare `interface` also matches the 1.8 GB gfx/interface art tree.
REQUIRED_PROFILE_ENTRIES = [
    "/tools/",
    "/common/",
    "/events/",
    "/history/",
    "/localisation/english/",
    "/interface/",
    "/gfx/flags/",
    "/resources/documentation/",
    "/.claude/docs/typo-watchlist.md",
    "/pyproject.toml",
]

_GAME_DIRS = ("common", "events", "history", "localisation")


def _game_content_checked_out() -> bool:
    return all(os.path.isdir(os.path.join(REPO_ROOT, d)) for d in _GAME_DIRS)


def test_staged_reference_coverage():
    """Reference trees and the sparse profile pinning them are intact."""
    if not _game_content_checked_out():
        raise SkipTest("game content not checked out (sparse checkout)")
    problems = []
    for pattern, floor in COVERAGE.items():
        count = sum(
            1 for _ in glob.iglob(os.path.join(REPO_ROOT, pattern), recursive=True)
        )
        if count < floor:
            problems.append(f"{pattern}: {count} files < floor {floor}")
    for rel in SENTINELS:
        if not os.path.exists(os.path.join(REPO_ROOT, rel)):
            problems.append(f"missing sentinel file: {rel}")
    try:
        with open(PROFILE, encoding="utf-8") as handle:
            entries = {line.strip() for line in handle if line.strip()}
    except OSError:
        problems.append(f"missing sparse profile: {PROFILE}")
    else:
        for required in REQUIRED_PROFILE_ENTRIES:
            if required not in entries:
                problems.append(f"sparse profile dropped {required}")
    assert not problems, "staged reference coverage gaps:\n" + "\n".join(problems)
