"""Shared scaffolding for the "this effect must be guarded" validators.

`validate_building_guards.py` and `validate_dynamic_modifier_guards.py` ask the
same question of different effects: does a trigger naming the *same* thing the
effect names sit between the effect and the top of its enclosing script tree?
The sanitize step, the skip list, the fact set carried down the walk, and the
report shape are identical for both.
"""

import os
import sys
from typing import Callable, FrozenSet, List, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared_utils import blank_quoted_strings  # noqa: E402
from validator_common import strip_comments  # noqa: E402

# Never contain effects. `trigger`/`available`/`visible`/`allowed` are skipped
# rather than treated as proofs: they gate the enclosing decision or event, not
# the scope the effect runs in, and `allowed` is evaluated once at game start.
# `effect_tooltip` only previews effects and never executes.
SKIP_BLOCKS = frozenset(
    {
        "limit",
        "ai_will_do",
        "effect_tooltip",
        "search_filters",
        "prerequisite",
        "mutually_exclusive",
        "trigger",
        "available",
        "visible",
        "allowed",
    }
)


def sanitize(text: str) -> str:
    """Strip comments and blank quoted strings, preserving line numbering.

    A `{` inside a `log = "..."` string, or a meta_effect template value like
    `DAM = "[?building_damage_by_missile]"`, would otherwise desync brace
    matching or false-match a guard regex.
    """
    return blank_quoted_strings(strip_comments(text))


class Context:
    """The things proven present at a point in the script."""

    __slots__ = ("present",)

    def __init__(self, present: FrozenSet[str] = frozenset()):
        self.present = present

    def apply(self, proven: Set[str]) -> "Context":
        if not proven:
            return self
        return Context(self.present | proven)


def report_findings(
    validator,
    issues: List[Tuple[str, str, int, str]],
    record: Callable[[str, str, str, int], None],
    summary: str,
    clean: str,
) -> None:
    """Record sorted `(category, path, line, message)` rows and log them."""
    for category, relative, line, message in issues:
        record(category, message, relative, line)

    if issues:
        validator.log(f"✗ {len(issues)} {summary}:", "error")
        for _, relative, line, message in issues:
            validator.log(f"  {relative}:{line} - {message}")
    else:
        validator.log(f"✓ {clean}")
