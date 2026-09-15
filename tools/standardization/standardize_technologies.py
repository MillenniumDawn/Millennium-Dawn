#!/usr/bin/env python3

"""
Millennium Dawn Technology Standardizer
Standardizes HOI4 technology files according to Millennium Dawn coding standards
"""

import re
from typing import Any, Dict, List, Optional

from common_utils import (
    PROP_NAME_RE,
    BaseStandardizer,
    collapse_blank_runs,
    join_groups,
    run_standardizer,
)
from shared_utils import (
    blank_quoted_strings,
    collapse_nested_blocks,
    collapse_or_compact,
    extract_block,
    normalize_spacing,
    strip_inline_comment,
)
from standardize_decisions import reindent_block
from standardize_ideas import _explode_braces

_GATE_KEYS = (
    "is_special_project_tech",
    "doctrine",
    "allow",
    "allow_branch",
    "dependencies",
    "XOR",
    "xor",
)
_MODIFIER_TAIL_KEYS = ("modifier", "custom_modifier_tooltip", "show_effect_as_desc")
_UNLOCK_KEYS = (
    "enable_equipments",
    "enable_equipment_modules",
    "enable_subunits",
    "enable_building",
    "enable_tactic",
    "sub_technologies",
    "show_equipment_icon",
)
_ON_COMPLETE_KEYS = ("on_research_complete_limit", "on_research_complete")
_RESEARCH_KEYS = ("research_cost", "start_year")
_XP_KEYS = (
    "xp_research_type",
    "xp_boost_cost",
    "xp_unlock_cost",
    "xp_research_bonus",
    "special_project_specialization",
)
_LAYOUT_KEYS = ("force_use_small_tech_layout", "path", "folder")
_CATEGORY_KEYS = ("categories",)
_AI_KEYS = ("ai_research_weights", "ai_will_do")
_PATH_ORDER = ("research_cost_coeff", "leads_to_tech")

# Every key not listed here is a modifier (a plain stat, a `category_*` block,
# or a sub-unit block) and keeps its source order inside the modifiers group.
_STRUCTURAL = frozenset(
    _GATE_KEYS
    + _MODIFIER_TAIL_KEYS
    + _UNLOCK_KEYS
    + _ON_COMPLETE_KEYS
    + _RESEARCH_KEYS
    + _XP_KEYS
    + _LAYOUT_KEYS
    + _CATEGORY_KEYS
    + _AI_KEYS
)

_MODIFIERS = "modifiers"
_TRAILING = "trailing"


def _split_packed_scalars(lines: List[str]) -> List[str]:
    """Split `a = 1 b = 2` (left glued by _explode_braces) into one line each."""
    out: List[str] = []
    for line in lines:
        if re.search(r'[{}"#]', line):
            out.append(line)
        else:
            out.extend(re.split(r"\s+(?=\w+\s*=)", line.strip()))
    return out


def _token_list(block_lines: List[str]) -> Optional[List[str]]:
    """Return the bare tokens of `key = { A B }`, or None for any other body."""
    text = " ".join(line.strip() for line in block_lines)
    if strip_inline_comment(text) != text:
        return None
    body = text.partition("{")[2]
    body, _, tail = body.rpartition("}")
    if tail.strip() or re.search(r'[=<>{}"]', body):
        return None
    return body.split()


def _one_line(block_lines: List[str], indent: str) -> Optional[List[str]]:
    """Pack `path`/`folder` onto one line; None when a comment must survive."""
    if any(strip_inline_comment(line) != line for line in block_lines):
        return None
    text = " ".join(line.strip() for line in block_lines)
    head, _, rest = text.partition("{")
    inner, _, tail = rest.rpartition("}")
    if head.split("=")[0].strip() == "path" and not re.search(r"[{}]", inner):
        rank = {name: i for i, name in enumerate(_PATH_ORDER)}
        pairs = re.findall(r"\w+\s*=\s*\S+", inner)
        pairs.sort(key=lambda pair: rank.get(pair.split("=")[0].strip(), len(rank)))
        inner = " ".join(pairs)
    return [normalize_spacing(f"{indent}{head}{{{inner}}}{tail}")]


def _render(entry, base_indent: int) -> List[str]:
    kind, data = entry
    indent = "\t" * base_indent
    if kind == "scalar":
        return [indent + data.strip()]
    if data[0].split("=")[0].strip() in ("path", "folder"):
        packed = _one_line(data, indent)
        if packed is not None:
            return packed
    tokens = _token_list(data)
    if tokens is not None:
        key = data[0].split("=")[0].strip()
        if len(tokens) < 2:
            return [f"{indent}{key} = {{ {' '.join(tokens)} }}".replace("{  }", "{ }")]
        return (
            [f"{indent}{key} = {{"]
            + [indent + "\t" + t for t in tokens]
            + [indent + "}"]
        )
    collapsed = collapse_or_compact(data[:], indent)
    multi = reindent_block(collapse_nested_blocks(data), base_indent)
    if len(collapsed) == 1 and len(multi) != 1:
        return collapsed
    return multi


class TechnologyStandardizer(BaseStandardizer):
    """Standardizer for HOI4 technologies"""

    def get_block_pattern(self) -> str:
        # Any indented block is a technology: the column-0 `technologies = {`
        # wrapper never matches and `@row = 1` constants carry no brace.
        return r"^[ \t]+\w+\s*=\s*\{"

    def extract_properties(self, block_lines: List[str]) -> Dict[str, Any]:
        props: Dict[str, Any] = {
            "id": "",
            "id_comment": "",
            _MODIFIERS: [],
            _TRAILING: [],
            "comments": {},
        }
        for key in _STRUCTURAL:
            props[key] = []

        first_code = strip_inline_comment(block_lines[0])
        props["id_comment"] = block_lines[0][len(first_code) :].strip()
        props["id"] = first_code.split("=")[0].strip()

        brace = first_code.find("{")
        if brace != -1 and first_code[brace + 1 :].strip():
            block_lines = _split_packed_scalars(_explode_braces(block_lines))

        pending: List[str] = []
        i = 1
        while i < len(block_lines) - 1:
            line = block_lines[i].strip()
            if not line:
                i += 1
                continue
            if line.startswith("#"):
                pending.append(line)
                i += 1
                continue
            match = PROP_NAME_RE.match(line)
            if not match:
                props[_TRAILING].extend(pending)
                props[_TRAILING].append(line)
                pending = []
                i += 1
                continue
            key = match.group(1)
            if "{" in blank_quoted_strings(strip_inline_comment(line)):
                block, next_i = extract_block(block_lines, i)
                entry = ("block", block)
            else:
                next_i = i + 1
                entry = ("scalar", line)
            slot = key if key in _STRUCTURAL else _MODIFIERS
            props[slot].append(entry)
            props["comments"][(slot, len(props[slot]) - 1)] = pending
            pending = []
            i = next_i

        props[_TRAILING].extend(pending)
        return props

    def format_block(self, props: Dict[str, Any], base_indent: int = 1) -> List[str]:
        prop_indent = base_indent + 1

        def emit(keys) -> List[str]:
            lines: List[str] = []
            for key in keys:
                for index, entry in enumerate(props[key]):
                    for comment in props["comments"].get((key, index), []):
                        lines.append("\t" * prop_indent + comment)
                    lines.extend(_render(entry, prop_indent))
            return lines

        groups = [
            emit(_GATE_KEYS),
            emit((_MODIFIERS,) + _MODIFIER_TAIL_KEYS),
            emit(_UNLOCK_KEYS),
            emit(_ON_COMPLETE_KEYS),
            emit(_RESEARCH_KEYS),
            emit(_XP_KEYS),
            emit(_LAYOUT_KEYS),
            emit(_CATEGORY_KEYS),
            emit(_AI_KEYS),
            ["\t" * prop_indent + line for line in props[_TRAILING]],
        ]

        suffix = f" = {{ {props['id_comment']}" if props["id_comment"] else " = {"
        return (
            ["\t" * base_indent + props["id"] + suffix]
            + join_groups(groups)
            + ["\t" * base_indent + "}"]
        )

    def standardize_lines(self, lines: List[str]) -> Optional[List[str]]:
        output_lines = super().standardize_lines(lines)
        if output_lines is None:
            return None
        # One blank line after every technology, none before the wrapper closer.
        spaced: List[str] = []
        previous = ""
        for line in output_lines:
            if line.strip():
                if previous == "\t}":
                    while spaced and not spaced[-1].strip():
                        spaced.pop()
                    if line != "}":
                        spaced.append("")
                previous = line
            spaced.append(line)
        return collapse_blank_runs(spaced)


def main():
    run_standardizer(
        TechnologyStandardizer,
        "Standardize HOI4 technology files according to Millennium Dawn coding standards",
    )


if __name__ == "__main__":
    main()
