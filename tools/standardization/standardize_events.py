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
    join_groups,
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

_BLOCK_PROPS = frozenset({"mean_time_to_happen", "trigger", "immediate", "option"})


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
            # A comment describes what comes next, so each block carries the
            # comments written above it. Same order and length as the block list.
            "mean_time_to_happen_comments": [],
            "trigger_comments": [],
            "immediate_comments": [],
            "option_comments": [],
            "comments_trailing": [],
            # format_block rebuilds the header from scratch, so a comment
            # trailing the opening brace has to be carried across explicitly.
            "header_comment": "",
        }

        first_line = block_lines[0].strip()
        for event_type in _EVENT_TYPES:
            if event_type in first_line:
                props["event_type"] = event_type
                break

        after_brace = first_line.partition("{")[2].strip()
        if after_brace.startswith("#"):
            props["header_comment"] = after_brace

        pending: List[str] = []

        i = 1  # Skip opening brace
        while i < len(block_lines) - 1:  # Skip closing brace
            line = block_lines[i].strip()
            match = PROP_NAME_RE.match(line)
            prop_name = match.group(1) if match else None

            if prop_name in _HEADER_SINGLE_PROPS:
                props[prop_name] = line
            elif prop_name in ("title", "desc"):
                if "{" in line:
                    block, next_i = extract_block(block_lines, i)
                    props[prop_name].append(block)
                    i = next_i
                    continue
                else:
                    props[prop_name].append(line)
            elif prop_name in _BLOCK_PROPS:
                block, next_i = extract_block(block_lines, i)
                props[prop_name].append(block)
                props[f"{prop_name}_comments"].append(pending)
                pending = []
                i = next_i
                continue
            else:
                pending.append(block_lines[i])

            i += 1

        props["comments_trailing"] = pending
        return props

    def format_block(self, props: Dict[str, Any]) -> List[str]:
        """Format event according to Millennium Dawn standard"""
        header = f"{props['event_type']} = {{"
        if props["header_comment"]:
            header += f" {props['header_comment']}"

        # 1-7. Header properties: id, title, desc, picture, is_triggered_only,
        # major, hidden, fire_only_once — one group, no blank lines between.
        head: List[str] = []
        if props["id"]:
            head.append(f"\t{props['id']}")

        for key in ("title", "desc"):
            for entry in props[key]:
                if isinstance(entry, list):
                    head.extend(collapse_or_compact(entry[:]))
                else:
                    head.append(f"\t{entry}")

        if props["picture"]:
            head.append(f"\t{props['picture']}")

        if props["is_triggered_only"]:
            head.append(f"\t{props['is_triggered_only']}")
        elif not props["mean_time_to_happen"]:
            head.append("\tis_triggered_only = yes")

        for key in ("major", "hidden", "fire_only_once"):
            if props[key]:
                head.append(f"\t{props[key]}")

        groups: List[List[str]] = [head]

        # 8-10. Mean time to happen, trigger, immediate effects.
        for key in ("mean_time_to_happen", "trigger", "immediate"):
            for comments, block in zip(props[f"{key}_comments"], props[key]):
                group: List[str] = []
                emit_comments(group, comments)
                group.extend(collapse_or_compact(block[:]))
                groups.append(group)

        # 11. Options
        for comments, option in zip(props["option_comments"], props["option"]):
            group = []
            emit_comments(group, comments)
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

            group.extend(collapse_or_compact(option[:]))
            groups.append(group)

        trailing: List[str] = []
        emit_comments(trailing, props["comments_trailing"])
        groups.append(trailing)

        return collapse_blank_runs([header] + join_groups(groups) + ["}"])


def main():
    run_standardizer(
        EventStandardizer,
        "Standardize HOI4 event files according to Millennium Dawn coding standards",
    )


if __name__ == "__main__":
    main()
