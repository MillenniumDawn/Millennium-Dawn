#!/usr/bin/env python3
"""Validate math expressions in variable effects (#2704).

A math expression is the value of a variable effect, wrapped in a block:
`set_variable = { X = { value = ... add = ... } }` (long form) or
`set_variable = { var = X value = { ... } }` (short form). The engine parses
a malformed expression to 0.0 with no in-game signal — only `script_math`
errors in error.log — and one bad expression desyncs the parser for the rest
of the file. Two documented failure classes, nothing broader:

* math statements written as siblings of the effect's `var =`/`value =`
  instead of inside the expression block (see hoi4-data-structures.md);
* `FROM.<var>` reads inside an expression, which parse but return 0
  (#2464). Plain `set_temp_variable = { x = FROM.y }` copies are valid and
  not reported.

`--clamp-bounds` (opt-in, #5321) also reports a `clamp`, `clamp_variable`, or
`clamp_temp_variable` whose literal `min` is above its literal `max`.

Weight blocks also warn when they write temp variables, directly or through
scripted triggers (#6452). Scorer `score` blocks are checked only in common/scorers.

Statement names follow resources/documentation/script_math_functions.md.
"""

import hashlib
import os
import re
import sys
from functools import partial
from typing import Dict, FrozenSet, Iterator, List, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import disk_cache
from guard_scan import read_file, sanitize
from shared_utils import extract_block_from_text
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
        "mod",
        "pow",
        "root",
        "log",
        "min",
        "max",
        "clamp",
        "lerp",
        "round",
        "sin",
        "cos",
        "tan",
        "atan",
        "atan2",
        "equals",
        "not_equals",
        "greater_than",
        "less_than",
        "greater_than_or_equals",
        "less_than_or_equals",
        "and",
        "or",
        "xor",
        "not",
        "if",
        "else",
        "else_if",
        "every_collection",
    }
)

# Statements an expression subtree may recurse into. Anything else (an effect
# keyword, a trigger such as check_variable) ends the descent, so a FROM read
# legal at effect level is never judged as an expression read.
EXPR_STATEMENTS = SIBLING_OPERATORS | frozenset({"value", "limit", "named_collection"})

# A FROM-bound variable read: `FROM.debt_bailout`, `FROM.FROM.x`. A bare FROM
# (scope block, scope comparison) is not a variable read.
FROM_READ_RE = re.compile(r"(?<![A-Za-z0-9_.])FROM(?:\.[A-Za-z0-9_]+)+")

# The expression statement and the two effects, all of which take min/max.
CLAMP_RE = re.compile(
    r"(?<![A-Za-z0-9_])(clamp|clamp_variable|clamp_temp_variable)\s*=\s*\{"
)
CLAMP_BOUNDS_CATEGORY = "clamp-min-above-max"
_NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")
AI_WEIGHT_TEMP_CATEGORY = "ai-weight-temp-variable"
_WEIGHT_BLOCK_RE = re.compile(r"\b(ai_will_do|ai_chance|score)\s*=\s*\{")
_TEMP_WRITE_RE = re.compile(
    r"\b(?:set_temp_variable|add_to_temp_variable|subtract_from_temp_variable|"
    r"multiply_temp_variable|divide_temp_variable|modulo_temp_variable|"
    r"clamp_temp_variable|round_temp_variable|randomize_temp_variable|"
    r"set_temp_variable_to_random|career_profile_set_temp_variable|"
    r"career_profile_set_temp_playthrough_variable)\s*="
)
_SCRIPTED_CALL_RE = re.compile(r"(?<![\w.:])([A-Za-z_]\w*)\s*=\s*(?:yes|no)\b")

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
    """Report FROM reads in one expression subtree."""
    if depth > 20:
        return
    for key, value, is_block, offset in _iter_statements(expr):
        line = base_line + expr.count("\n", 0, offset)
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
        if is_block and key in EXPR_STATEMENTS:
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


def _iter_blocks(text: str, pattern: re.Pattern[str]) -> Iterator[Tuple[int, str, str]]:
    """Yield (line, name, body) for each block *pattern* opens."""
    # Matches come in file order, so count only the newlines since the last one.
    line = 1
    line_pos = 0
    for m in pattern.finditer(text):
        line += text.count("\n", line_pos, m.start())
        line_pos = m.start()
        block, end = extract_block_from_text(text, m.end() - 1)
        if end != -1:
            yield line, m.group(1), block


def _scan_clamp_bounds(text: str, findings: List[Finding]) -> None:
    for line, name, block in _iter_blocks(text, CLAMP_RE):
        bounds = {
            key: value
            for key, value, is_block, _offset in _iter_statements(block)
            if key in ("min", "max") and not is_block and _NUMBER_RE.fullmatch(value)
        }
        if len(bounds) == 2 and float(bounds["min"]) > float(bounds["max"]):
            findings.append(
                (
                    line,
                    CLAMP_BOUNDS_CATEGORY,
                    f"`{name}` has min {bounds['min']} above max {bounds['max']}, "
                    f"so the bounds are swapped or mistyped",
                )
            )


def _temp_writing_triggers(files: List[str]) -> FrozenSet[str]:
    """Find scripted triggers that write temps, including through other triggers."""
    definitions: Dict[str, str] = {}
    for path in files:
        text = sanitize(read_file(path))
        for name, body, is_block, _offset in _iter_statements(text):
            if is_block:
                definitions[name] = body

    writers: Set[str] = set()
    callers: Dict[str, Set[str]] = {}
    for name, body in definitions.items():
        if _TEMP_WRITE_RE.search(body):
            writers.add(name)
        for call in _SCRIPTED_CALL_RE.finditer(body):
            callers.setdefault(call[1], set()).add(name)

    pending = list(writers)
    while pending:
        for caller in callers.get(pending.pop(), set()):
            if caller not in writers:
                writers.add(caller)
                pending.append(caller)
    return frozenset(writers)


def scan_text(
    raw: str, temp_triggers: FrozenSet[str] = frozenset(), *, scorer: bool = False
) -> List[Finding]:
    """Scan script text; returns (line, category, message)."""
    text = sanitize(raw)
    findings: List[Finding] = []
    for line, _name, block in _iter_blocks(text, VAR_EFFECT_RE):
        _scan_effect_block(block, line, findings)
    _scan_clamp_bounds(text, findings)
    for line, name, block in _iter_blocks(text, _WEIGHT_BLOCK_RE):
        if name == "score" and not scorer:
            continue
        if _TEMP_WRITE_RE.search(block) or any(
            call[1] in temp_triggers for call in _SCRIPTED_CALL_RE.finditer(block)
        ):
            findings.append(
                (
                    line,
                    AI_WEIGHT_TEMP_CATEGORY,
                    f"{name} writes temp variables directly or through a scripted "
                    "trigger; use check_expr for comparisons or threshold "
                    "modifiers for computed weights",
                )
            )
    return findings


def _scan_file(
    args: Tuple[str, str],
    temp_triggers: FrozenSet[str],
    namespace: str,
) -> List[Finding]:
    """Pool worker: scan one file for math-expression traps, content-cached."""
    filepath, mod_path = args
    raw = read_file(filepath)
    if "variable" not in raw and not _WEIGHT_BLOCK_RE.search(raw):
        return []
    scorer = (
        os.path.relpath(filepath, mod_path)
        .replace(os.sep, "/")
        .startswith("common/scorers/")
    )
    return disk_cache.per_file_cached_by_content(
        mod_path,
        namespace,
        filepath,
        raw,
        lambda: scan_text(raw, temp_triggers, scorer=scorer),
    )


class Validator(BaseValidator):
    TITLE = "MATH EXPRESSION VALIDATION"
    STAGED_EXTENSIONS = [".txt"]

    def __init__(self, mod_path: str, **kwargs):
        self.clamp_bounds = kwargs.pop("clamp_bounds", False)
        super().__init__(mod_path, **kwargs)

    def run_validations(self):
        files = self._collect_files(SCAN_PATTERNS)
        files = [
            path
            for path in files
            if not any(part in path.replace("\\", "/") for part in _EXCLUDED_PARTS)
        ]
        self._log_section("Scanning math expressions and AI weight temp writes")
        trigger_files = self._collect_files(
            ["common/scripted_triggers/**/*.txt"], ignore_staged=True
        )
        temp_triggers = _temp_writing_triggers(trigger_files)
        digest = hashlib.sha256("\n".join(sorted(temp_triggers)).encode()).hexdigest()
        scan = partial(
            _scan_file,
            temp_triggers=temp_triggers,
            namespace="math_expr.scan." + digest,
        )
        self.log(f"  Scanning {len(files)} files")
        total = 0
        for path, file_findings in zip(
            files,
            self._pool_map(scan, [(f, self.mod_path) for f in files]),
        ):
            rel = os.path.relpath(path, self.mod_path)
            for line, category, message in file_findings:
                if category == CLAMP_BOUNDS_CATEGORY and not self.clamp_bounds:
                    continue
                if category == AI_WEIGHT_TEMP_CATEGORY:
                    self.add_warning(category, message, rel, line)
                else:
                    self.add_error(category, message, rel, line)
                total += 1
        if not total:
            self.log("No math-expression traps or AI weight temp writes found")
        else:
            self.log(
                f"  {total} math-expression issue(s) found",
                "error" if self.errors_found else "warning",
            )


def _add_extra_args(parser):
    parser.add_argument(
        "--clamp-bounds",
        action="store_true",
        dest="clamp_bounds",
        help="Flag a clamp, clamp_variable, or clamp_temp_variable whose literal min is above its literal max",
    )


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate math-expression traps in variable effects",
        extra_args_fn=_add_extra_args,
    )
