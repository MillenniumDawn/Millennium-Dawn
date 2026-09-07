#!/usr/bin/env python3

"""
In-memory standardization for Millennium Dawn script files.

Answers two questions without touching disk: which standardizer owns a path,
and what that standardizer would write for a given text. The pre-commit router
(tools/standardize_staged.py) and validate_standardization.py both drive the
standardizers through here, so routing lives in exactly one place.
"""

import os
import sys
from typing import List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common_utils import render_standardized
from standardize_decisions import DecisionStandardizer
from standardize_events import EventStandardizer
from standardize_focus_tree import format_focus_tree_lines
from standardize_ideas import IdeaStandardizer
from standardize_mio import MIOStandardizer

# Path prefix -> standardizer kind. `common/decisions/` covers `categories/`
# too; DecisionStandardizer handles both shapes.
ROUTES: Tuple[Tuple[str, str], ...] = (
    ("common/national_focus/", "focus"),
    ("events/", "event"),
    ("common/decisions/", "decision"),
    ("common/ideas/", "idea"),
    ("common/military_industrial_organization/", "mio"),
)

_STANDARDIZERS = {
    "event": EventStandardizer,
    "decision": DecisionStandardizer,
    "idea": IdeaStandardizer,
    "mio": MIOStandardizer,
}


def kind_for_path(path: str) -> Optional[str]:
    """Return the standardizer kind owning `path`, or None when none does.

    Accepts a repo-relative or absolute path; matching is on the prefix at a
    path-segment boundary so a nested worktree checkout routes the same way.
    """
    normalized = str(path).replace("\\", "/")
    if not normalized.endswith(".txt"):
        return None
    for prefix, kind in ROUTES:
        if normalized.startswith(prefix) or ("/" + prefix) in normalized:
            return kind
    return None


def standardize_lines(kind: str, lines: List[str]) -> Optional[List[str]]:
    """Standardize already-read lines, or None when this file has no blocks."""
    if kind == "focus":
        output_lines, _ = format_focus_tree_lines(lines)
        return output_lines
    return _STANDARDIZERS[kind](verbose=False).standardize_lines(lines)


def standardize_text(kind: str, text: str) -> Optional[str]:
    """Return the file text the standardizer would write, or None for a no-op.

    None means the file holds no block of this kind, which is the same case
    the file-writing path reports as "skipping file write".
    """
    # keepends matches what the file path's readlines() hands the standardizers.
    output_lines = standardize_lines(kind, text.splitlines(keepends=True))
    if output_lines is None:
        return None
    return render_standardized(output_lines)
