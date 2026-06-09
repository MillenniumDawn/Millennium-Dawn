#!/usr/bin/env python3
"""Consolidated style and standards checks for HOI4 mod .txt files.

Replaces the former check_basic_style.py, coding_standards.py, and
check_braces.py with a single BaseValidator pass.

ERROR-level checks (fail the run):
  - Brace matching: unbalanced { } with comment/string awareness (stack-based)
  - 4-space indent instead of a tab

WARNING-level checks (reported, do not fail):
  - Missing space around open/close braces
  - Missing or doubled space around '='
  - Odd number of quotation marks on a line
  - Running brace depth going negative
  - Focus ID format (must be TAG_focus_name)
  - Missing search_filters in focus blocks
  - Event option has effects but no log =
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

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

_SHARED_FOCUS_PREFIXES = ("USoE", "POTEF", "AFRICAN_UNION")


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
    ignore_till_eol = False
    in_string = False
    line_num = 1

    for c in text:
        if c == "\n":
            line_num += 1
            ignore_till_eol = False
            in_string = False
            indent_count = 0
            continue
        if c != " ":
            indent_count = 0
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
            if indent_count == 4:
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

        if "{" in line:
            if not re.search(r"#.*[{}]+", line):
                brace_depth += line.count("{")
                unstyled = line.count("{") - line.count(" {\n") - line.count(" { ")
                if unstyled > 0 and _RE_NO_SP_OPEN.search(line):
                    warnings.append(
                        ("Missing space before or after open brace", line_num)
                    )

        if "}" in line:
            if not re.search(r"#.*[{}]+", line):
                brace_depth -= line.count("}")
                unstyled = line.count("}") - line.count(" }\n") - line.count(" } ")
                if unstyled > 0 and _RE_NO_SP_CLOSE.search(line):
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
    """Focus ID format and missing search_filters. Returns [(message, line)]."""
    warnings = []
    lines = text.splitlines()
    braces = 0
    current_focus_id = ""
    has_search_filters = False
    in_focus_block = False
    in_completion_reward = False
    found_focus_id = False
    focus_line = 0
    focus_open_depth = 0
    completion_reward_depth = 0

    for line_num, line in enumerate(lines, 1):
        if line.startswith("#") or not line.strip():
            continue
        depth_before = braces
        if "{" in line:
            braces += line.count("{")
        if "}" in line:
            braces -= line.count("}")

        if "completion_reward" in line and "{" in line:
            in_completion_reward = True
            completion_reward_depth = depth_before
        elif in_completion_reward and braces == completion_reward_depth:
            in_completion_reward = False

        if in_focus_block and "search_filters" in line:
            has_search_filters = True

        # A focus = { block sits inside focus_tree = { ... } (depth 1); a
        # shared_focus = { block sits at the file top level (depth 0). Match
        # either and remember the depth so the block closes at the right level.
        if not in_focus_block and re.match(r"^\s*(?:shared_)?focus\s*=\s*\{", line):
            in_focus_block = True
            found_focus_id = False
            has_search_filters = False
            focus_line = line_num
            focus_open_depth = depth_before
        elif in_focus_block and braces == focus_open_depth:
            if found_focus_id and not has_search_filters:
                warnings.append(
                    (f"Focus {current_focus_id} missing search_filters", focus_line)
                )
            in_focus_block = False
            current_focus_id = ""
            found_focus_id = False

        if (
            in_focus_block
            and not in_completion_reward
            and not found_focus_id
            and ("id =" in line or "id=" in line)
        ):
            m = re.match(r"[ \t]+id\s?=\s?([A-Za-z0-9_?]+)", line)
            if m:
                current_focus_id = m.group(1)
                found_focus_id = True
                if not _has_focus_format(current_focus_id):
                    warnings.append(
                        (
                            f"Focus ID {current_focus_id} must be TAG_focus_name",
                            line_num,
                        )
                    )
    return warnings


def _has_focus_format(focus_id: str) -> bool:
    for prefix in _SHARED_FOCUS_PREFIXES:
        if focus_id.startswith(prefix):
            return True
    return bool(_RE_FOCUS_FORMAT.match(focus_id))


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

        if option_found:
            if "name" in line and "=" in line:
                m = re.search(r"name\s?=\s([a-zA-Z0-9_.]+)", line)
                if m:
                    option_name = m.group(1)
            elif (
                "=" in line and braces > 0 and "name" not in line and "log" not in line
            ):
                has_other_defs = True
            if "{" in line:
                braces += line.count("{")
            if braces > 0 and not has_log and "log" in line:
                has_log = True
                option_found = False
                braces = 0
            if "}" in line:
                braces -= line.count("}")
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
        indent_errors = [r for r in error_results if r not in brace_errors]
        self._report(
            indent_errors,
            "Indent and bracket balance OK",
            "Indent/bracket errors:",
            severity=Severity.ERROR,
            category="indent-brackets",
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
        focus_warnings = [
            r
            for r in warning_results
            if "focus" in r[0].lower() or "search_filters" in r[0].lower()
        ]
        self._report(
            focus_warnings,
            "Focus standards OK",
            "Focus standard warnings:",
            severity=Severity.WARNING,
            category="focus-standards",
        )

        self._log_section("Event Log Standards (WARNING)")
        event_warnings = [
            r
            for r in warning_results
            if "event option" in r[0].lower() or "log" in r[0].lower()
        ]
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
