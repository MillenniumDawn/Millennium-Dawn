#!/usr/bin/env python3

"""
In-memory standardization for Millennium Dawn script files.

Answers two questions without touching disk: which standardizer owns a path,
and what that standardizer would write for a given text. The pre-commit router
(tools/standardize_staged.py) and validate_standardization.py both drive the
standardizers through here, so routing lives in exactly one place.
"""

import os
import re
import sys
from collections import defaultdict
from typing import Callable, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common_utils import BaseStandardizer, render_standardized
from shared_utils import (
    blank_quoted_strings,
    find_matching_brace,
    iter_statement_ops,
    reindent_by_brace_depth,
    strip_comments,
)
from standardize_decisions import DecisionStandardizer
from standardize_events import EventStandardizer
from standardize_focus_tree import format_focus_tree_lines
from standardize_history import HistoryStandardizer
from standardize_ideas import IdeaStandardizer
from standardize_mio import MIOStandardizer
from standardize_technologies import TechnologyStandardizer

# Path prefix -> standardizer kind. `common/decisions/` covers `categories/`
# too; DecisionStandardizer handles both shapes.
ROUTES: Tuple[Tuple[str, str], ...] = (
    ("common/national_focus/", "focus"),
    ("events/", "event"),
    ("common/decisions/", "decision"),
    ("common/ideas/", "idea"),
    ("common/military_industrial_organization/", "mio"),
    ("common/technologies/", "technology"),
    ("history/", "history"),
    # No block layout rules for these yet: tabs and spacing only.
    ("common/ai_equipment/", "indent"),
    ("common/characters/", "indent"),
    ("common/scripted_effects/", "indent"),
    ("common/scripted_triggers/", "indent"),
)

_STANDARDIZERS: dict[str, Callable[..., BaseStandardizer]] = {
    "event": EventStandardizer,
    "decision": DecisionStandardizer,
    "idea": IdeaStandardizer,
    "mio": MIOStandardizer,
    "technology": TechnologyStandardizer,
    "history": HistoryStandardizer,
}


_SCRIPT_TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|#[^\n]*|[<>!=]=|[{}=<>!]|[^\s{}=<>!"#]+')
_FOCUS_BLOCK = re.compile(r"\b(focus|shared_focus|joint_focus)\s*=\s*\{")
_FOCUS_DEFAULTS = {
    "cancel_if_invalid": "yes",
    "continue_if_invalid": "no",
    "available_if_capitulated": "no",
}
_FOCUS_EFFECTS = {"completion_reward", "select_effect", "bypass_effect"}
_EMPTY_FOCUS_BLOCKS = {"available", "bypass", "cancel", "mutually_exclusive"}
_MERGED_FOCUS_BLOCKS = {
    "allow_branch",
    "search_filters",
    "joint_trigger",
    "available",
    "bypass",
    "cancel",
    "completion_reward",
    "completion_reward_joint_originator",
    "completion_reward_joint_member",
    "select_effect",
    "bypass_effect",
}


def _script_tokens(text: str) -> list[str]:
    return [token for token in _SCRIPT_TOKEN.findall(text) if not token.startswith("#")]


def _focus_properties(body: str) -> dict[str, list[tuple[str, ...]]]:
    properties: dict[str, list[tuple[str, ...]]] = defaultdict(list)
    # Rejoin tokens so comments and quoted braces cannot confuse statement discovery.
    code = " ".join(_script_tokens(body))
    for key, operator, scalar, block in iter_statement_ops(code):
        if block is None:
            if _FOCUS_DEFAULTS.get(key) == scalar:
                continue
            properties[key].append((operator, "scalar", scalar or ""))
            continue
        tokens = _script_tokens(block)
        if key in _FOCUS_EFFECTS:
            index = 0
            while index + 2 < len(tokens):
                if tokens[index : index + 2] == ["log", "="] and tokens[
                    index + 2
                ].startswith('"'):
                    del tokens[index : index + 3]
                else:
                    index += 1
        if not tokens and key in _EMPTY_FOCUS_BLOCKS | _FOCUS_EFFECTS:
            continue
        if key == "ai_will_do":
            if not any(name == "base" for name, _, _, _ in iter_statement_ops(block)):
                depth = 0
                for index, token in enumerate(tokens):
                    if token == "factor" and depth == 0:
                        tokens[index] = "base"
                    depth += (token == "{") - (token == "}")
            if tokens == ["base", "=", "1"]:
                continue
        if key == "offset":
            fields = _focus_properties(block)
            properties[key].append((operator, "block", repr(sorted(fields.items()))))
        elif key in _MERGED_FOCUS_BLOCKS and properties[key]:
            properties[key][-1] += tuple(tokens)
        else:
            properties[key].append((operator, "block", *tokens))
    return dict(properties)


def _focus_blocks(text: str) -> list[tuple[str, str, int, str]]:
    code = strip_comments(text)
    masked = blank_quoted_strings(code)
    blocks = []
    position = 0
    while match := _FOCUS_BLOCK.search(masked, position):
        closing = find_matching_brace(code, match.end() - 1)
        if closing == -1:
            raise ValueError("unbalanced focus block")
        body = code[match.end() : closing]
        focus_id = next(
            (
                scalar or ""
                for key, _, scalar, _ in iter_statement_ops(body)
                if key == "id"
            ),
            "",
        )
        blocks.append(
            (focus_id, match.group(1), code.count("\n", 0, match.start()) + 1, body)
        )
        position = closing + 1
    return blocks


def focus_content_changes(before: str, after: str) -> list[tuple[int, str]]:
    """Find changed focus content, allowing the formatter's documented normalizations.

    Focus order and repeated property order must survive. Root property order,
    whitespace, comments, logs, explicit defaults, empty no-ops, duplicate block
    merging, and root AI factor-to-base conversion may change. This is not a
    gameplay validator and does not inspect properties outside focus blocks.
    """
    old_blocks = _focus_blocks(before)
    new_blocks = _focus_blocks(after)
    if [(row[0], row[1]) for row in old_blocks] != [
        (row[0], row[1]) for row in new_blocks
    ]:
        return [(0, "focus IDs, kinds, or order changed")]
    changes = []
    for old, new in zip(old_blocks, new_blocks):
        old_props = _focus_properties(old[3])
        new_props = _focus_properties(new[3])
        for key in sorted(old_props.keys() | new_props.keys()):
            if old_props.get(key) != new_props.get(key):
                changes.append((old[2], f"{old[0]}: {key} content changed"))
    return changes


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


def standardize_lines(
    kind: str, lines: List[str], mod_root: Optional[str] = None
) -> Optional[List[str]]:
    """Standardize already-read lines, or None when this file has no blocks."""
    if kind == "focus":
        output_lines, _ = format_focus_tree_lines(lines)
        return output_lines
    if kind == "indent":
        return reindent_by_brace_depth(lines)
    if kind == "history":
        return HistoryStandardizer(verbose=False, mod_root=mod_root).standardize_lines(
            lines
        )
    return _STANDARDIZERS[kind](verbose=False).standardize_lines(lines)


def standardize_text(
    kind: str, text: str, mod_root: Optional[str] = None
) -> Optional[str]:
    """Return the file text the standardizer would write, or None for a no-op.

    None means the file holds no block of this kind, which is the same case
    the file-writing path reports as "skipping file write".
    """
    # keepends matches what the file path's readlines() hands the standardizers.
    output_lines = standardize_lines(kind, text.splitlines(keepends=True), mod_root)
    if output_lines is None:
        return None
    return render_standardized(output_lines)
