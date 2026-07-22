#!/usr/bin/env python3

"""
Millennium Dawn Event Standardizer
Standardizes HOI4 event files according to Millennium Dawn coding standards
"""

import re
from typing import Any, Dict, List

from common_utils import (
    PROP_NAME_RE,
    BaseStandardizer,
    block_has_log,
    collapse_blank_runs,
    emit_comments,
    inject_log_after_brace,
    run_standardizer,
)
from shared_utils import (
    blank_quoted_strings,
    collapse_or_compact,
    extract_block,
    strip_inline_comment,
)

_EVENT_TYPES = ("country_event", "province_event", "unit_leader_event", "news_event")

_HEADER_SINGLE_PROPS = {
    "id",
    "picture",
    "is_triggered_only",
    "hidden",
    "major",
    "fire_only_once",
}

# Maps script property name -> (props key, section tag for comment placement)
_BLOCK_PROPS = {
    "mean_time_to_happen": ("mean_time_to_happen", "mtth"),
    "trigger": ("trigger", "trigger"),
    "immediate": ("immediate", "immediate"),
    "option": ("option", "options"),
}


_OPTION_STATEMENT_RE = re.compile(r"[A-Za-z_]\w*\s*=")


def _split_packed_body(body: str) -> List[str]:
    """Split a packed one-line option body into its top-level ``key = value``
    statements. Brace- and quote-aware so nested blocks and quoted values that
    contain spaces or ``=`` are not split mid-statement."""
    boundaries: List[int] = []
    depth = 0
    in_str = False
    for i, c in enumerate(body):
        if c == '"' and (i == 0 or body[i - 1] != "\\"):
            in_str = not in_str
        elif in_str:
            continue
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        elif (
            depth == 0
            and (i == 0 or body[i - 1].isspace())
            and _OPTION_STATEMENT_RE.match(body, i)
        ):
            boundaries.append(i)
    if not boundaries:
        stripped = body.strip()
        return [stripped] if stripped else []
    boundaries.append(len(body))
    out: List[str] = []
    for a, b in zip(boundaries, boundaries[1:]):
        seg = body[a:b].strip()
        if seg:
            out.append(seg)
    return out


def _option_body(option_block: List[str]) -> List[str]:
    """Statements between the option header's ``{`` and its matching ``}``.
    A packed single-line option (`option = { name = x  add_pp = 10 }`) keeps
    header, body, and closer on one physical line, so its body is split out of
    that line rather than read as the empty slice between two list elements."""
    if len(option_block) == 1:
        code = strip_inline_comment(option_block[0])
        open_idx = code.find("{")
        close_idx = code.rfind("}")
        if open_idx == -1 or close_idx <= open_idx:
            return []
        return _split_packed_body(code[open_idx + 1 : close_idx])
    body = list(option_block[1:-1])
    # A statement packed onto the closer line (`add_political_power = 10 }`) is
    # invisible to a plain [1:-1] slice — recover the code before the trailing `}`.
    last = strip_inline_comment(option_block[-1])
    close_idx = last.rfind("}")
    if close_idx != -1:
        tail = last[:close_idx].strip()
        if tail:
            body.append(tail)
    return body


def _explode_packed_option(option_block: List[str]) -> List[str]:
    """Expand a packed single-line option into header / body / closer lines so a
    log can be injected inside its braces. Multi-line options pass through."""
    if len(option_block) != 1:
        return option_block
    line = option_block[0].rstrip("\n")
    code = strip_inline_comment(line)
    comment = line[len(code) :].strip()
    indent = line[: len(line) - len(line.lstrip("\t"))]
    closer = f"{indent}}}" + (f" {comment}" if comment else "")
    return (
        [f"{indent}option = {{"]
        + [f"{indent}\t{stmt}" for stmt in _option_body(option_block)]
        + [closer]
    )


def _option_indent(option_block: List[str]) -> str:
    """Leading-tab indent of the option body, from its first non-blank line.
    Files with 2-tab option bodies get a 2-tab log line, 3-tab bodies get 3."""
    for line in _option_body(option_block):
        if line.strip():
            return line[: len(line) - len(line.lstrip("\t"))] or "\t\t\t"
    return "\t\t\t"


def _option_log_line(option_block: List[str]) -> str:
    """Build the log line for an event option. Uses the first `name = ...`
    line found in the block (matches legacy behaviour); indent follows the body."""
    option_name = "option"
    for line in option_block:
        stripped = line.strip()
        if stripped.startswith("name ="):
            option_name = stripped.split("=", 1)[1].strip()
            break
    indent = _option_indent(option_block)
    return f'{indent}log = "[GetDateText]: [This.GetName]: {option_name} executed"'


def _option_has_effects(option_block: List[str]) -> bool:
    """Check whether an option's body has any meaningful effect lines. Scans only
    the body so the `option = {` header line itself never trips detection. Each
    body line is split into its packed statements so an effect jammed onto a
    physical line after a skipped one (`name = x  add_pp = 10`) is still seen.

    Brace depth is tracked across body lines so the inner lines of a multi-line
    skipped block (`ai_chance = {` / `trigger = {`) are swallowed whole and not
    misread as top-level effects."""
    skip_prefixes = ("name =", "ai_chance =", "trigger =")
    depth = 0
    for line in _option_body(option_block):
        for stripped in _split_packed_body(line.strip()):
            if not stripped or stripped.startswith("#"):
                continue
            code = blank_quoted_strings(strip_inline_comment(stripped))
            delta = code.count("{") - code.count("}")
            if depth > 0:
                depth = max(0, depth + delta)
                continue
            if stripped in ("{", "}") or stripped.startswith(skip_prefixes):
                depth = max(0, depth + delta)
                continue
            return True
    return False


class EventStandardizer(BaseStandardizer):
    """Standardizer for HOI4 events"""

    def get_block_pattern(self) -> str:
        """Return regex pattern to identify event blocks"""
        return r"\s*(" + "|".join(_EVENT_TYPES) + r")\s*=\s*{"

    def extract_properties(self, block_lines: List[str]) -> Dict[str, Any]:
        """Extract properties from event block lines"""
        props: Dict[str, Any] = {
            "event_type": "",
            "id": "",
            # title/desc: list of entries. Each entry is either a single-line
            # string or a list[str] for `prop = { trigger = {...} text = ... }`
            # conditional blocks (which can repeat).
            "title": [],
            "desc": [],
            "picture": "",
            "is_triggered_only": "",
            "hidden": "",
            "major": "",
            "fire_only_once": "",
            "mean_time_to_happen": [],
            "trigger": [],
            "immediate": [],
            "option": [],
            "comments_after_header": [],
            "comments_after_mtth": [],
            "comments_after_trigger": [],
            "comments_after_immediate": [],
            "comments_after_options": [],
        }

        first_line = block_lines[0].strip()
        for event_type in _EVENT_TYPES:
            if event_type in first_line:
                props["event_type"] = event_type
                break

        # Track which section we're in for comment placement
        current_section = "header"

        i = 1  # Skip opening brace
        while i < len(block_lines) - 1:  # Skip closing brace
            line = block_lines[i].strip()
            match = PROP_NAME_RE.match(line)
            prop_name = match.group(1) if match else None

            if prop_name in _HEADER_SINGLE_PROPS:
                props[prop_name] = line
                current_section = "header"
            elif prop_name in ("title", "desc"):
                if "{" in line:
                    block, next_i = extract_block(block_lines, i)
                    props[prop_name].append(block)
                    i = next_i
                    current_section = "header"
                    continue
                else:
                    props[prop_name].append(line)
                    current_section = "header"
            elif prop_name in _BLOCK_PROPS:
                key, section = _BLOCK_PROPS[prop_name]
                block, next_i = extract_block(block_lines, i)
                props[key].append(block)
                i = next_i
                current_section = section
                continue
            else:
                # Comment or unrecognized line: bucket it under the current section.
                props[f"comments_after_{current_section}"].append(block_lines[i])

            i += 1

        return props

    def format_block(self, props: Dict[str, Any]) -> List[str]:
        """Format event according to Millennium Dawn standard"""
        lines = []
        lines.append(f"{props['event_type']} = {{")

        # 1. ID (first line after opening brace)
        if props["id"]:
            lines.append(f"\t{props['id']}")

        # 2. Title and description (may repeat as conditional blocks)
        for title_entry in props["title"]:
            if isinstance(title_entry, list):
                lines.extend(collapse_or_compact(title_entry[:]))
            else:
                lines.append(f"\t{title_entry}")
        for desc_entry in props["desc"]:
            if isinstance(desc_entry, list):
                lines.extend(collapse_or_compact(desc_entry[:]))
            else:
                lines.append(f"\t{desc_entry}")

        # 3. Picture
        if props["picture"]:
            lines.append(f"\t{props['picture']}")

        # 4. is_triggered_only (required for triggered events)
        if props["is_triggered_only"]:
            lines.append(f"\t{props['is_triggered_only']}")
        elif not props["mean_time_to_happen"]:
            lines.append("\tis_triggered_only = yes")

        # 5. major flag (use sparingly)
        if props["major"]:
            lines.append(f"\t{props['major']}")

        # 6. hidden parameter
        if props["hidden"]:
            lines.append(f"\t{props['hidden']}")

        # 7. fire_only_once (use sparingly)
        if props["fire_only_once"]:
            lines.append(f"\t{props['fire_only_once']}")

        lines.append("")

        emit_comments(lines, props["comments_after_header"])

        # 8. Mean time to happen
        for mtth in props["mean_time_to_happen"]:
            lines.extend(collapse_or_compact(mtth[:]))
            lines.append("")
        emit_comments(lines, props["comments_after_mtth"])

        # 9. Trigger
        for trigger in props["trigger"]:
            lines.extend(collapse_or_compact(trigger[:]))
            lines.append("")
        emit_comments(lines, props["comments_after_trigger"])

        # 10. Immediate effects
        for immediate in props["immediate"]:
            lines.extend(collapse_or_compact(immediate[:]))
            lines.append("")
        emit_comments(lines, props["comments_after_immediate"])

        # 11. Options
        for option in props["option"]:
            if (
                _option_has_effects(option)
                and not block_has_log(option)
                and props["id"]
            ):
                # Explode a packed single-line option first so the log lands
                # inside its braces, not as a sibling after the close.
                option = _explode_packed_option(option)
                log_line = _option_log_line(option)
                option = inject_log_after_brace(option, log_line)

            lines.extend(collapse_or_compact(option[:]))
            lines.append("")

        emit_comments(lines, props["comments_after_options"])
        if props["comments_after_options"]:
            lines.append("")

        lines.append("}")

        return collapse_blank_runs(lines)


def main():
    run_standardizer(
        EventStandardizer,
        "Standardize HOI4 event files according to Millennium Dawn coding standards",
    )


if __name__ == "__main__":
    main()
