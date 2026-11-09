"""Flag AI weight blocks where an `add` follows a `factor = 0` modifier.

`ai_chance` and `ai_will_do` apply their `modifier` blocks in order on a running
total, so a positive `add` after a `factor = 0` brings the zeroed weight back
(issue #5738). Opposite literal boolean conditions in the same scope cannot
hold together. Other trigger relationships remain unknown.
"""

import hashlib
import os
import re
import sys
from functools import lru_cache, partial
from typing import FrozenSet, List, Optional, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import guard_scan  # noqa: E402 — same-dir import after sys.path tweak above
from shared_utils import (
    compute_line_offsets,
    find_unquoted_brace_close,
    iter_statements,
    line_for_offset,
)
from validate_unused_scripted import extract_definitions
from validator_common import (
    FACTOR_ZERO_RE,
    BaseValidator,
    Severity,
    _child_blocks,
    run_validator_main,
)

_AI_WEIGHT_RE = re.compile(r"\b(ai_chance|ai_will_do)\s*=\s*\{")
_ADD_RE = re.compile(r"\badd\s*=\s*(\d+(?:\.\d+)?)")
_CATEGORY = "ai-weight-zero-then-add"
_BOOLEAN_TRIGGERS = frozenset({"always", "has_war", "is_ai"})


def _own_text(text: str, start: int, end: int) -> str:
    """The body between ``start`` and ``end`` with nested blocks cut out."""
    parts = []
    cursor = start
    for _, name_start, _, body_end in _child_blocks(text, start, end):
        parts.append(text[cursor:name_start])
        cursor = body_end + 1
    parts.append(text[cursor:end])
    return " ".join(parts)


def _add_after_zero(
    text: str, start: int, end: int, boolean_keys: FrozenSet[str]
) -> Optional[int]:
    """Offset of the first positive-add modifier that follows a zeroing one."""
    zero_guards: List[Set[Tuple[tuple, str, str]]] = []
    for name, name_start, body_start, body_end in _child_blocks(text, start, end):
        if name != "modifier":
            continue
        own = _own_text(text, body_start, body_end)
        facts = _required_booleans(text[body_start:body_end], boolean_keys)
        if any(float(value) > 0 for value in _ADD_RE.findall(own)) and any(
            not any(
                (scope, key, "no" if value == "yes" else "yes") in facts
                for scope, key, value in guard
            )
            for guard in zero_guards
        ):
            return name_start
        if FACTOR_ZERO_RE.search(own):
            zero_guards.append(facts)
    return None


def _required_booleans(
    body: str, boolean_keys: FrozenSet[str], scope: tuple = ()
) -> Set[Tuple[tuple, str, str]]:
    """Literal boolean facts every satisfying trigger path must have."""
    facts = set()
    for key, value, block in iter_statements(body):
        if key in {"factor", "add"}:
            continue
        if block is None:
            if key in boolean_keys and value in {"yes", "no"}:
                facts.add((scope, key, value))
        elif key in {"AND", "hidden_trigger", "custom_trigger_tooltip"}:
            facts |= _required_booleans(block, boolean_keys, scope)
        elif key == "NOT":
            statements = list(iter_statements(block))
            if len(statements) == 1:
                name, literal, nested = statements[0]
                if name in boolean_keys and nested is None and literal in {"yes", "no"}:
                    facts.add((scope, name, "no" if literal == "yes" else "yes"))
        elif key == "OR":
            branches = [
                _required_booleans(
                    (
                        f"{name} = {{ {nested} }}"
                        if nested is not None
                        else f"{name} = {literal}"
                    ),
                    boolean_keys,
                    scope,
                )
                for name, literal, nested in iter_statements(block)
            ]
            if branches:
                facts |= set.intersection(*branches)
        elif key == "ROOT":
            facts |= _required_booleans(block, boolean_keys)
        elif key == "THIS":
            facts |= _required_booleans(block, boolean_keys, scope)
        elif key in {"FROM", "PREV", "SNDR"} or re.fullmatch(r"[A-Z0-9_]{3}", key):
            facts |= _required_booleans(block, boolean_keys, (*scope, key))
    return facts


def scan_text(
    raw: str, boolean_triggers: FrozenSet[str] = _BOOLEAN_TRIGGERS
) -> List[Tuple[int, str]]:
    """Return (line, message) for every AI weight block that adds after a zero."""
    text = guard_scan.sanitize(raw)
    offsets = compute_line_offsets(text)
    findings: List[Tuple[int, str]] = []
    for match in _AI_WEIGHT_RE.finditer(text):
        close = find_unquoted_brace_close(text, match.end() - 1)
        if close == -1:
            continue
        add_at = _add_after_zero(text, match.end(), close, boolean_triggers)
        if add_at is not None:
            findings.append(
                (
                    line_for_offset(offsets, add_at),
                    f"{match.group(1)} adds after a factor = 0 modifier, which "
                    "brings the zeroed weight back; move the factor = 0 "
                    "modifiers last",
                )
            )
    return findings


@lru_cache(maxsize=None)
def _cache_namespace(boolean_triggers: FrozenSet[str]) -> str:
    """Findings depend on which triggers are boolean, so the set keys the cache."""
    digest = hashlib.sha256("\n".join(sorted(boolean_triggers)).encode()).hexdigest()
    return "ai_weight_order_scan_v1." + digest


def scan_file(
    args: Tuple[str, str], boolean_triggers: FrozenSet[str] = _BOOLEAN_TRIGGERS
) -> List[Tuple[str, int, str]]:
    """Return (relative path, line, message) for one content file."""
    return guard_scan.scan_file(
        args,
        "factor",
        _cache_namespace(boolean_triggers),
        partial(scan_text, boolean_triggers=boolean_triggers),
    )


class Validator(BaseValidator):
    TITLE = "AI WEIGHT ORDER VALIDATION"
    STAGED_EXTENSIONS = [".txt"]

    def validate_ai_weight_order(self):
        self._log_section("factor = 0 modifiers followed by an add")
        trigger_files = self._collect_files(
            ["common/scripted_triggers/*.txt"], ignore_staged=True
        )
        definitions = self._pool_map(
            extract_definitions, [(path, self.mod_path) for path in trigger_files]
        )
        boolean_triggers = _BOOLEAN_TRIGGERS | frozenset(
            name for rows in definitions for name, _, _ in rows
        )
        rows = guard_scan.collect_findings(
            self, partial(scan_file, boolean_triggers=boolean_triggers), _CATEGORY
        )
        self._report(
            [(message, relative, line) for _, relative, line, message in rows],
            "✓ No AI weight block adds after a factor = 0 modifier",
            "AI weight blocks adding after a factor = 0 modifier:",
            Severity.WARNING,
            category=_CATEGORY,
        )

    def run_validations(self):
        self.validate_ai_weight_order()


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate that factor = 0 modifiers come after the adds in AI weight blocks",
    )
