#!/usr/bin/env python3
"""Consolidated style and standards checks for HOI4 mod .txt files.

Replaces the former check_basic_style.py, coding_standards.py, and
check_braces.py with a single BaseValidator pass.

ERROR-level checks (fail the run):
  - Brace matching: unbalanced { } with comment/string awareness (stack-based)
  - 4-space indent instead of a tab
  - Orphaned `newline = yes` with no visible effect left after it

WARNING-level checks (reported, do not fail):
  - Missing space around open/close braces
  - Missing or doubled space around '='
  - Odd number of quotation marks on a line
  - Running brace depth going negative
  - Focus ID format (must be TAG_focus_name)
  - Event option has effects but no log =
"""

import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared_utils import strip_inline_comment
from validator_common import BaseValidator, Severity, run_validator_main

_SCAN_PATTERNS = [
    "common/**/*.txt",
    "events/**/*.txt",
    "history/**/*.txt",
]

_RE_COMMENT_QUOTE = re.compile(r'#.*["]+', re.M | re.I)
_RE_NO_SP_OPEN = re.compile(r"([^\s]+)\{|\{([^\s]+)", re.M | re.I)
_RE_NO_SP_CLOSE = re.compile(r"([^\s]+)\}|\}([^\s]+)", re.M | re.I)
_RE_TAG_LINE = re.compile(r"^[A-Z]{3}", re.M | re.I)
_RE_FOCUS_FORMAT = re.compile(r"^[A-Z]{3}_[a-zA-Z0-9_-]+$", re.M | re.U)
_RE_NEWS_EVENT = re.compile(r"news_event\s*=\s*\{")
_RE_OPTION = re.compile(r"\boption\s*=\s*\{")
_RE_OPTION_TRIGGER = re.compile(r"trigger\s*=\s*\{")

_RE_EFFECT_BLOCK = re.compile(
    r"^\s*(?:completion_reward|complete_effect|remove_effect|timeout_effect"
    r"|cancel_effect)\s*=\s*\{"
)
_RE_NEWLINE_YES = re.compile(r"^newline\s*=\s*yes$")
# Effects rendering no tooltip output, so a separator before them separates
# nothing. update_focus_tree_obsolete_branches is wholly wrapped in a
# hidden_effect (common/scripted_effects/00_focus_utilities.txt).
_RE_INVISIBLE_EFFECT = re.compile(
    r"^(?:log|newline|update_focus_tree_obsolete_branches"
    r"|set_temp_variable|add_to_temp_variable|subtract_from_temp_variable"
    r"|multiply_temp_variable|divide_temp_variable|clamp_temp_variable"
    r"|set_country_flag|clr_country_flag|set_global_flag|clr_global_flag)\b"
)
_RE_INVISIBLE_BLOCK = re.compile(r"^(?:hidden_effect|limit)\s*=\s*\{")
_RE_TRANSPARENT_BLOCK = re.compile(r"^(?:if|else|else_if)\s*=\s*\{")

# EH is the Event Horizon generic tree's mod-wide domain prefix, not a tag.
_SHARED_FOCUS_PREFIXES = ("USoE", "POTEF", "AFRICAN_UNION", "GENERIC", "EH")


def _check_brace_matching(text: str, path: str):
    """Stack-based brace matching with comment/string awareness. Returns
    [(message, line)]."""
    errors = []
    brace_stack = []
    line_num = 1
    col_num = 1
    in_comment = False
    in_string = False

    for char in text:
        if char == "\n":
            in_string = False
            line_num += 1
            col_num = 1
            in_comment = False
            continue
        col_num += 1
        if char == '"':
            if not in_comment:
                in_string = not in_string
            continue
        if in_string or in_comment:
            continue
        if char == "#":
            in_comment = True
            continue
        if char == "{":
            brace_stack.append((line_num, col_num))
        elif char == "}":
            if not brace_stack:
                errors.append(
                    ("Closing brace '}' without matching opening brace", line_num)
                )
            else:
                brace_stack.pop()

    for line, col in brace_stack:
        errors.append(("Opening brace '{' without matching closing brace", line))
    return errors


def _check_indent_and_brackets(text: str, path: str):
    """4-space indent and bracket balance checks. Returns [(message, line)]."""
    errors = []
    count_open_paren = 0
    count_close_paren = 0
    count_open_square = 0
    count_close_square = 0
    indent_count = 0
    at_line_start = True
    ignore_till_eol = False
    in_string = False
    line_num = 1

    for c in text:
        if c == "\n":
            line_num += 1
            ignore_till_eol = False
            in_string = False
            indent_count = 0
            at_line_start = True
            continue
        if c != " ":
            indent_count = 0
        # Leading whitespace ends at the first non-space, non-tab character;
        # spaces past that point are inline alignment (e.g. `= 1    }`), not
        # indentation, and must not be flagged as a 4-space indent.
        if c != " " and c != "\t":
            at_line_start = False
        if ignore_till_eol:
            continue
        if c == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if c == "#":
            ignore_till_eol = True
        elif c == "(":
            count_open_paren += 1
        elif c == ")":
            count_close_paren += 1
        elif c == "[":
            count_open_square += 1
        elif c == "]":
            count_close_square += 1
        elif c == " ":
            indent_count += 1
            if indent_count == 4 and at_line_start:
                errors.append(("4-space indent detected (use tab)", line_num))

    if count_open_square != count_close_square:
        errors.append(
            (
                f"Unbalanced square brackets: [ = {count_open_square}, ] = {count_close_square}",
                0,
            )
        )
    if count_open_paren != count_close_paren:
        errors.append(
            (
                f"Unbalanced round brackets: ( = {count_open_paren}, ) = {count_close_paren}",
                0,
            )
        )
    return errors


def _check_spacing_and_quotes(text: str, path: str):
    """Brace/equal-sign spacing, quote-parity, and running-brace-depth checks.
    Returns [(message, line)]."""
    warnings = []
    brace_depth = 0

    for line_num, line in enumerate(text.splitlines(), 1):
        if line.startswith("#"):
            continue

        # Empty `{}` blocks (e.g. `topbar_empty = {}`) are idiomatic and have no
        # interior to space; strip them before the brace-spacing check so they
        # don't false-positive. Brace depth still counts the originals.
        spacing_line = re.sub(r"\{\s*\}", "", line)

        if "{" in line:
            if not re.search(r"#.*[{}]+", line):
                brace_depth += line.count("{")
                unstyled = (
                    spacing_line.count("{")
                    - spacing_line.count(" {\n")
                    - spacing_line.count(" { ")
                )
                if unstyled > 0 and _RE_NO_SP_OPEN.search(spacing_line):
                    warnings.append(
                        ("Missing space before or after open brace", line_num)
                    )

        if "}" in line:
            if not re.search(r"#.*[{}]+", line):
                brace_depth -= line.count("}")
                unstyled = (
                    spacing_line.count("}")
                    - spacing_line.count(" }\n")
                    - spacing_line.count(" } ")
                )
                if unstyled > 0 and _RE_NO_SP_CLOSE.search(spacing_line):
                    warnings.append(
                        ("Missing space before or after close brace", line_num)
                    )

        if '"' in line:
            if (line.count('"') % 2) != 0:
                if not _RE_COMMENT_QUOTE.search(line):
                    warnings.append(("Odd number of quotation marks", line_num))

        if "=" in line:
            unstyled = line.count("=") - line.count(" = ") - line.count(" =\n")
            if line.count("  =") > 0 or line.count("=  ") > 0:
                warnings.append(("Two spaces before or after '='", line_num))
                unstyled -= line.count("  =") + line.count("=  ")
            if unstyled != 0:
                warnings.append(("Missing space before or after '='", line_num))

        if brace_depth <= -1:
            warnings.append(("Running brace depth went negative", line_num))
            brace_depth = 0

    return warnings


def _check_focus_standards(text: str, path: str):
    """Focus ID format checks. Returns [(message, line)]."""
    warnings = []
    lines = text.splitlines()
    depth = 0
    in_focus_block = False
    found_focus_id = False
    focus_open_depth = 0

    for line_num, line in enumerate(lines, 1):
        if line.startswith("#") or not line.strip():
            continue
        if "{" in line:
            depth += line.count("{")
        if "}" in line:
            depth -= line.count("}")

        # A focus = { block sits inside focus_tree = { ... } (depth 1); a
        # shared_focus/joint_focus = { block sits at the file top level
        # (depth 0). Match any and remember the depth so the block closes at
        # the right level.
        if not in_focus_block and re.match(
            r"^\s*(?:shared_|joint_)?focus\s*=\s*\{", line
        ):
            in_focus_block = True
            found_focus_id = False
            focus_open_depth = depth - 1
        elif in_focus_block and depth <= focus_open_depth:
            in_focus_block = False
            found_focus_id = False

        if in_focus_block and not found_focus_id and ("id =" in line or "id=" in line):
            m = re.match(r"[ \t]+id\s*=\s*([A-Za-z0-9_?]+)", line)
            if m:
                found_focus_id = True
                if not _has_focus_format(m.group(1)):
                    warnings.append(
                        (
                            f"Focus ID {m.group(1)} must be TAG_focus_name",
                            line_num,
                        )
                    )
    return warnings


def _has_focus_format(focus_id: str) -> bool:
    return focus_id.startswith(_SHARED_FOCUS_PREFIXES) or bool(
        _RE_FOCUS_FORMAT.match(focus_id)
    )


def _check_event_log_standards(text: str, path: str):
    """Event option has effects but no log =. Returns [(message, line)]."""
    warnings = []
    lines = text.splitlines()
    braces = 0
    option_found = False
    option_name = ""
    option_line = 0
    has_log = False
    has_other_defs = False
    in_news_event = False
    event_braces = 0
    # ai_chance / ai_will_do are AI weighting, not effects; -1 means "outside one".
    ai_block_depth = -1

    for line_num, line in enumerate(lines, 1):
        if line.startswith("#") or not line.strip():
            continue
        stripped = line.strip()

        if _RE_NEWS_EVENT.match(stripped):
            in_news_event = True
            event_braces = 1
        elif in_news_event:
            event_braces += line.count("{")
            event_braces -= line.count("}")
            if event_braces <= 0:
                in_news_event = False
                event_braces = 0
            continue
        if in_news_event:
            continue

        if _RE_OPTION.search(line):
            option_found = True
            option_line = line_num
            option_name = ""
            has_log = False
            has_other_defs = False
            ai_block_depth = -1

        if option_found:
            # Detect ai_chance / ai_will_do / trigger before the effects check so
            # the block's own opening line (an `=` line) isn't counted as an
            # effect. An option-level trigger is a visibility condition.
            if (
                ai_block_depth < 0
                and "{" in line
                and (
                    "ai_chance" in line
                    or "ai_will_do" in line
                    or _RE_OPTION_TRIGGER.match(stripped)
                )
            ):
                ai_block_depth = braces
            if "name" in line and "=" in line:
                m = re.search(r"name\s?=\s([a-zA-Z0-9_.]+)", line)
                if m:
                    option_name = m.group(1)
            elif (
                "=" in line
                and braces > 0
                and ai_block_depth < 0
                and "name" not in line
                and "log" not in line
            ):
                has_other_defs = True
            if "{" in line:
                braces += line.count("{")
            if braces > 0 and not has_log and "log" in line:
                has_log = True
                option_found = False
                braces = 0
                ai_block_depth = -1
            if "}" in line:
                braces -= line.count("}")
            if ai_block_depth >= 0 and braces <= ai_block_depth:
                ai_block_depth = -1
            if braces == 0 and not has_log and has_other_defs and option_name:
                warnings.append(
                    (f"Event option {option_name} has effects but no log", option_line)
                )
                option_found = False
                braces = 0
            elif braces == 0:
                option_found = False
                braces = 0

    return warnings


def _check_orphan_newline(text: str, path: str):
    """`newline = yes` with no tooltip-visible effect left after it.

    `newline = yes` inserts a blank line into a reward tooltip, so it is only
    meaningful as a separator between two visible effects. When everything
    following it inside the same effect block renders nothing, the tooltip ends
    on a dangling blank line. The usual cause is an effect being deleted while
    its paired separator is left behind.

    Deliberately not the naive "`newline = yes` then `}`" match: a separator as
    the last statement of an `if` is the standard MD idiom and is correct
    whenever visible content follows the `if`, so the scan continues past the
    enclosing braces to the end of the effect block.
    """
    warnings = []
    lines = [strip_inline_comment(line) for line in text.splitlines()]

    # Net brace delta per line, so a block's extent is a depth comparison.
    deltas = [line.count("{") - line.count("}") for line in lines]
    depths = []
    depth = 0
    for delta in deltas:
        depths.append(depth)
        depth += delta

    def _visible_effect_follows(start: int, end: int) -> bool:
        """Whether any line in (start, end) renders tooltip output."""
        idx = start + 1
        while idx < end:
            stripped = lines[idx].strip()
            if not stripped or stripped in ("{", "}"):
                idx += 1
                continue
            # hidden_effect renders nothing; limit is a condition, not output.
            if _RE_INVISIBLE_BLOCK.match(stripped):
                block_depth = depths[idx]
                idx += 1
                while idx < end and depths[idx] > block_depth:
                    idx += 1
                continue
            # if/else render their children inline, so keep scanning inside.
            if _RE_TRANSPARENT_BLOCK.match(stripped):
                idx += 1
                continue
            if _RE_INVISIBLE_EFFECT.match(stripped):
                idx += 1
                continue
            return True
        return False

    for line_num, line in enumerate(lines, 1):
        if not _RE_EFFECT_BLOCK.match(line):
            continue
        start = line_num - 1
        block_depth = depths[start]
        end = start + 1
        while end < len(lines) and depths[end] > block_depth:
            end += 1

        for idx in range(start + 1, end):
            if not _RE_NEWLINE_YES.match(lines[idx].strip()):
                continue
            if not _visible_effect_follows(idx, end):
                warnings.append(
                    (
                        "Orphaned newline = yes: no visible effect follows it in"
                        " this block, leaving a blank line at the end of the"
                        " tooltip",
                        idx + 1,
                    )
                )

    return warnings


def _scan_file(text: str, path: str):
    """Run all style checks on one file. Returns [(message, line)]."""
    findings = []
    rel = path

    # ERROR-level: brace matching
    findings.extend(_check_brace_matching(text, rel))
    # ERROR-level: indent and bracket balance
    findings.extend(_check_indent_and_brackets(text, rel))
    # WARNING-level: spacing and quotes
    findings.extend(_check_spacing_and_quotes(text, rel))
    # ERROR-level: orphaned tooltip separators
    findings.extend(_check_orphan_newline(text, rel))

    # Focus standards: only national_focus files
    if "/national_focus/" in path.replace("\\", "/"):
        findings.extend(_check_focus_standards(text, rel))

    # Event log standards: only event files
    if "/events/" in path.replace("\\", "/"):
        findings.extend(_check_event_log_standards(text, rel))

    return findings


class Validator(BaseValidator):
    TITLE = "STYLE & STANDARDS CHECKS"
    STAGED_EXTENSIONS = [".txt"]

    def run_validations(self):
        parsed = self.parse_files_cached(_SCAN_PATTERNS, "style.scan", _scan_file)
        self.log(f"Scanned {len(parsed)} files for style issues")

        error_results = []
        warning_results = []

        for path, findings in parsed.items():
            rel = os.path.relpath(path, self.mod_path)
            for message, line in findings:
                # Brace matching and indent errors are ERROR; everything else WARNING
                is_error = any(
                    kw in message
                    for kw in (
                        "without matching",
                        "Unbalanced",
                        "4-space indent",
                        "Orphaned newline",
                    )
                )
                entry = (message, rel, line)
                if is_error:
                    error_results.append(entry)
                else:
                    warning_results.append(entry)

        self._log_section("Brace Matching (ERROR)")
        brace_errors = [
            r
            for r in error_results
            if "brace" in r[0].lower() or "without matching" in r[0].lower()
        ]
        self._report(
            brace_errors,
            "All braces properly matched",
            "Brace matching errors:",
            severity=Severity.ERROR,
            category="brace-matching",
        )

        self._log_section("Indent & Brackets (ERROR)")
        orphan_errors = [r for r in error_results if "Orphaned newline" in r[0]]
        indent_errors = [
            r for r in error_results if r not in brace_errors and r not in orphan_errors
        ]
        self._report(
            indent_errors,
            "Indent and bracket balance OK",
            "Indent/bracket errors:",
            severity=Severity.ERROR,
            category="indent-brackets",
        )

        self._log_section("Orphaned Tooltip Separators (ERROR)")
        self._report(
            orphan_errors,
            "No orphaned newline = yes found",
            "Orphaned newline = yes (blank line at end of tooltip):",
            severity=Severity.ERROR,
            category="orphan-newline",
        )

        self._log_section("Spacing & Quotes (WARNING)")
        spacing_warnings = [
            r
            for r in warning_results
            if "brace" in r[0].lower()
            or "space" in r[0].lower()
            or "quotation" in r[0].lower()
            or "depth" in r[0].lower()
            or "=" in r[0]
        ]
        self._report(
            spacing_warnings,
            "Spacing and quotes OK",
            "Spacing/quote warnings:",
            severity=Severity.WARNING,
            category="spacing",
        )

        self._log_section("Focus Standards (WARNING)")
        focus_warnings = [r for r in warning_results if "focus" in r[0].lower()]
        self._report(
            focus_warnings,
            "Focus standards OK",
            "Focus standard warnings:",
            severity=Severity.WARNING,
            category="focus-standards",
        )

        self._log_section("Event Log Standards (WARNING)")
        event_warnings = [r for r in warning_results if "event option" in r[0].lower()]
        self._report(
            event_warnings,
            "Event log standards OK",
            "Event log warnings:",
            severity=Severity.WARNING,
            category="event-log",
        )


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Check style, brace matching, and coding standards in Millennium Dawn mod",
    )
