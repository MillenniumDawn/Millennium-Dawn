#!/usr/bin/env python3
"""Validate math expressions in variable effects (#2704).

A math expression is the value of a variable effect, wrapped in a block:
`set_variable = { X = { value = ... add = ... } }` (long form) or
`set_variable = { var = X value = { ... } }` (short form). The engine parses
a malformed expression to 0.0 with no in-game signal — only `script_math`
errors in error.log — and one bad expression desyncs the parser for the rest
of the file. Three documented failure classes, nothing broader:

* math statements written as siblings of the effect's `var =`/`value =`
  instead of inside the expression block (hoi4-data-structures.md, "Do not
  write the math expression as siblings of `var = X`");
* the unsafe comparators (`equals`, `not_equals`,
  `greater_than_or_equals`, `less_than_or_equals`) inside an expression —
  only `greater_than`/`less_than` parse there;
* `FROM.<var>` reads inside an expression, which parse but return 0
  (#2464). Effect-level `check_variable` comparators and plain
  `set_temp_variable = { x = FROM.y }` copies are valid and not reported.
"""

import os
import re
import sys
from typing import Iterator, List, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import disk_cache
from equipment_module_slots import blank_comments
from shared_utils import blank_quoted_strings, extract_block_from_text
from validator_common import BaseValidator, run_validator_main

# Every effect whose value can be a math expression (not modulo_variable /
# clamp_variable, which take plain min/max arguments).
VAR_EFFECT_RE = re.compile(
    r"(?<![A-Za-z0-9_])(set_variable|set_temp_variable|add_to_variable|"
    r"subtract_from_variable|multiply_variable|divide_variable|"
    r"add_to_temp_variable|subtract_from_temp_variable|multiply_temp_variable|"
    r"divide_temp_variable)\s*=\s*\{"
)

# Math statements that are only legal *inside* an expression block. Any of
# these at the effect block's own depth is the sibling-operator trap.
SIBLING_OPERATORS = frozenset(
    {
        "add",
        "subtract",
        "multiply",
        "divide",
        "min",
        "max",
        "clamp",
        "round",
        "greater_than",
        "less_than",
        "if",
        "else",
        "else_if",
        "every_collection",
    }
)

# Statements an expression subtree may recurse into. Anything else (an effect
# keyword, a trigger such as check_variable) ends the descent, so comparators
# legal at effect level are never judged as expression statements.
EXPR_STATEMENTS = SIBLING_OPERATORS | frozenset({"value", "limit", "named_collection"})

UNSAFE_COMPARATORS = frozenset(
    {"equals", "not_equals", "greater_than_or_equals", "less_than_or_equals"}
)

# A FROM-bound variable read: `FROM.debt_bailout`, `FROM.FROM.x`. A bare FROM
# (scope block, scope comparison) is not a variable read.
FROM_READ_RE = re.compile(r"(?<![A-Za-z0-9_.])FROM(?:\.[A-Za-z0-9_]+)+")

Finding = Tuple[int, str, str]

_STATEMENT_RE = re.compile(r"[^\s{}=]+\s*=\s*")
SCAN_PATTERNS = ["common/**/*.txt", "events/**/*.txt", "history/**/*.txt"]
_EXCLUDED_PARTS = ("Changelog.txt", "AUTHORS.txt", "/descriptions")


def _iter_statements(text: str) -> Iterator[Tuple[str, str, bool, int]]:
    """Yield top-level `key = value` statements from *text*."""
    i = 0
    n = len(text)
    while i < n:
        if text[i].isspace() or text[i] in "{}":
            i += 1
            continue
        match = _STATEMENT_RE.match(text, i)
        if not match:
            i += 1
            continue
        key = text[i : match.end()].split("=", 1)[0].rstrip()
        value_start = match.end()
        if value_start < n and text[value_start] == "{":
            body, end = extract_block_from_text(text, value_start)
            if end == -1:
                return
            yield key, body, True, i
            i = end
            continue
        value_end = value_start
        while (
            value_end < n
            and not text[value_end].isspace()
            and text[value_end] not in "{}"
        ):
            value_end += 1
        yield key, text[value_start:value_end], False, i
        i = value_end


def _check_expression(
    expr: str, base_line: int, findings: List[Finding], depth: int = 0
) -> None:
    """Report unsafe comparators and FROM reads in one expression subtree."""
    if depth > 20:
        return
    for key, value, is_block, offset in _iter_statements(expr):
        line = base_line + expr.count("\n", 0, offset)
        if key in UNSAFE_COMPARATORS:
            findings.append(
                (
                    line,
                    "math-unsafe-comparator",
                    f"`{key}` inside a math expression zeroes the whole "
                    f"expression — only greater_than/less_than are safe there; "
                    f"hoist the branch to an effect-level if with "
                    f"check_variable",
                )
            )
        if not is_block and FROM_READ_RE.search(value):
            findings.append(
                (
                    line,
                    "math-from-read",
                    "`FROM.<var>` inside a math expression parses but reads 0 "
                    "at runtime — copy FROM.<var> into a temp variable at "
                    "effect level first",
                )
            )
        if is_block and (key in EXPR_STATEMENTS or key in UNSAFE_COMPARATORS):
            _check_expression(value, line, findings, depth + 1)


def _scan_effect_block(block: str, base_line: int, findings: List[Finding]) -> None:
    statements = list(_iter_statements(block))
    siblings = sorted(
        {key for key, _v, _b, _o in statements if key in SIBLING_OPERATORS}
    )
    if siblings:
        findings.append(
            (
                base_line,
                "math-sibling-operator",
                f"math statements ({', '.join(siblings)}) sit beside var/value "
                f"instead of inside the expression — this parses as 0.0 "
                f"silently; wrap them in value = {{ ... }} (short form) or "
                f"<var> = {{ ... }} (long form)",
            )
        )
    nested_effects = {m.group(1) for m in VAR_EFFECT_RE.finditer(block)}
    for key, value, is_block, offset in statements:
        # `value = { ... }` is the short-form expression root; any other block
        # child of a var effect is the long-form expression, except the var
        # key itself and nested variable effects (scanned on their own).
        if not is_block or key == "var" or key in nested_effects:
            continue
        if key in SIBLING_OPERATORS:
            continue
        _check_expression(value, base_line + block.count("\n", 0, offset), findings)


def scan_text(raw: str) -> List[Finding]:
    """Scan script text; returns (line, category, message)."""
    text = blank_quoted_strings(blank_comments(raw))
    findings: List[Finding] = []
    for m in VAR_EFFECT_RE.finditer(text):
        block, end = extract_block_from_text(text, m.end() - 1)
        if end == -1:
            continue
        _scan_effect_block(block, text.count("\n", 0, m.start()) + 1, findings)
    return findings


def _scan_file(args: Tuple[str, str]) -> List[Finding]:
    """Pool worker: scan one file for math-expression traps, content-cached."""
    filepath, mod_path = args
    try:
        with open(filepath, "r", encoding="utf-8-sig") as handle:
            raw = handle.read()
    except OSError:
        return []
    if "variable" not in raw:
        return []
    return disk_cache.per_file_cached_by_content(
        mod_path, "math_expr.scan", filepath, raw, lambda: scan_text(raw)
    )


class Validator(BaseValidator):
    TITLE = "MATH EXPRESSION VALIDATION"
    STAGED_EXTENSIONS = [".txt"]

    def run_validations(self):
        files = self._collect_files(SCAN_PATTERNS)
        files = [
            path
            for path in files
            if not any(part in path.replace("\\", "/") for part in _EXCLUDED_PARTS)
        ]
        self._log_section("Scanning variable effects for math-expression traps")
        self.log(f"  Scanning {len(files)} files")
        total = 0
        for path, file_findings in zip(
            files,
            self._pool_map(_scan_file, [(f, self.mod_path) for f in files]),
        ):
            rel = os.path.relpath(path, self.mod_path)
            for line, category, message in file_findings:
                self.add_warning(category, message, rel, line)
            total += len(file_findings)
        if not total:
            self.log("No math-expression traps found")
        else:
            self.log(f"  {total} math-expression trap(s) found", "warning")


if __name__ == "__main__":
    run_validator_main(Validator, "Validate math-expression traps in variable effects")
