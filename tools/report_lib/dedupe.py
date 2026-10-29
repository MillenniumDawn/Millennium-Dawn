"""Deduplicate issues that multiple validators surface about the same line.

Key design choice: dedupe is *cross-validator* only. An individual validator
is already responsible for not emitting the same issue twice. When two
validators happen to report the same (category, file, line, message) — e.g.
`events` and `localisation` both flag a missing loc key — we collapse them
into one rendered entry with a `detected_by: [events, localisation]` list.
"""

from collections import OrderedDict
from typing import List

from .models import Issue


def dedupe(issues: List[Issue]) -> List[Issue]:
    """Collapse duplicate issues, preserving first-seen order.

    Two issues are considered the same when `(category, file, line, message)`
    match. The first issue keeps its severity and validator; subsequent
    duplicates get appended to `detected_by`.
    """
    merged: "OrderedDict[tuple, Issue]" = OrderedDict()

    for issue in issues:
        key = issue.dedup_key
        if key in merged:
            existing = merged[key]
            other = issue.validator or issue.category
            if (
                other
                and other != existing.validator
                and other not in existing.detected_by
            ):
                existing.detected_by.append(other)
            # Escalate severity: error wins over warning
            if issue.severity == "error" and existing.severity == "warning":
                existing.severity = "error"
        else:
            merged[key] = issue
            if issue.validator:
                issue.detected_by = []  # primary validator is in .validator

    return list(merged.values())
