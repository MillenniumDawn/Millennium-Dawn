#!/usr/bin/env python3

"""
Millennium Dawn Idea Standardizer
Standardizes HOI4 idea files according to Millennium Dawn coding standards
"""

import os
import re
import time
from typing import Any, Dict, List

from _common import format_elapsed
from common_utils import PROP_NAME_RE, BaseStandardizer, run_standardizer
from shared_utils import (
    blank_quoted_strings,
    collapse_or_compact,
    extract_block,
    log_message,
    strip_inline_comment,
)

_SINGLE_LINE_PROPS = {"name", "picture"}

_BLOCK_PROPS = {
    "allowed",
    "allowed_civil_war",
    "cancel",
    "modifier",
    "targeted_modifier",
    "research_bonus",
    "rule",
    "equipment_bonus",
    "on_add",
    "on_remove",
}

# Blocks that get filtered out when they contain `always = no`
_ALWAYS_NO_FILTERED = {"allowed", "allowed_civil_war", "cancel"}

# Block pattern for wrapper blocks / idea blocks
_BLOCK_START_RE = re.compile(r"\s*[\w_]+\s*=\s*{")


_ALLOWED_TAG_RE = re.compile(r"\btag\s*=\s*(\w+)")


def _rewrite_allowed_tag(line: str) -> str:
    """Rewrite ``tag = TAG`` to ``original_tag = TAG`` in an allowed block,
    leaving any trailing ``#`` comment untouched (a commented `#tag = X` stays
    as written)."""
    code = strip_inline_comment(line)
    comment = line[len(code) :]
    return _ALLOWED_TAG_RE.sub(r"original_tag = \1", code) + comment


def _explode_braces(block_lines: List[str]) -> List[str]:
    """Split packed lines at each ``{``/``}`` boundary so every brace and the text
    between braces sits on its own line. Statements sharing a brace level are not
    split apart (`{ a = 1 b = 2 }` yields `{`, `a = 1 b = 2`, `}`).

    Quoted strings and trailing ``#`` comments are preserved. Used to normalize a
    single-line or opener-packed idea/lifecycle block before property extraction
    so no content is dropped (``foo = { picture = x }`` on one line) and so an
    injected log line lands inside the block, not after it.
    """
    out: List[str] = []
    for raw in block_lines:
        code = strip_inline_comment(raw)
        comment = raw[len(code) :].strip()
        segments: List[str] = []
        buf = ""
        in_str = False
        for i, c in enumerate(code):
            if c == '"' and (i == 0 or code[i - 1] != "\\"):
                in_str = not in_str
                buf += c
            elif c == "{" and not in_str:
                buf += "{"
                segments.append(buf.strip())
                buf = ""
            elif c == "}" and not in_str:
                if buf.strip():
                    segments.append(buf.strip())
                segments.append("}")
                buf = ""
            else:
                buf += c
        if buf.strip():
            segments.append(buf.strip())
        if comment:
            if segments:
                segments[-1] = (segments[-1] + " " + comment).strip()
            else:
                segments.append(comment)
        out.extend(segments if segments else [raw.strip()])
    return out


class IdeaStandardizer(BaseStandardizer):
    """Standardizer for HOI4 ideas"""

    # Wrapper blocks that should be preserved, not processed
    WRAPPER_BLOCKS = {
        "ideas",
        "country",
        "hidden_ideas",
        "political_advisor",
        "theorist",
        "army_chief",
        "navy_chief",
        "air_chief",
        "high_command",
        "tank_manufacturer",
        "naval_manufacturer",
        "aircraft_manufacturer",
        "materiel_manufacturer",
        "industrial_concern",
    }

    def get_block_pattern(self) -> str:
        """Return regex pattern to identify idea blocks"""
        # Match any idea block (ID is extracted from the block name, not the pattern)
        return r"\s*[\w_]+\s*=\s*{"

    def extract_properties(self, block_lines: List[str]) -> Dict[str, Any]:
        """Extract properties from idea block lines"""
        props: Dict[str, Any] = {
            "id": "",
            "id_comment": "",
            "name": "",
            "allowed": [],
            "allowed_civil_war": [],
            "picture": "",
            "cancel": [],
            "modifier": [],
            "targeted_modifier": [],
            "research_bonus": [],
            "rule": [],
            "equipment_bonus": [],
            "on_add": [],
            "on_remove": [],
            "other": [],
        }

        # Extract ID from the opening line (e.g., "BRA_idea_higher_minimum_wage_1 = {").
        # Keep any trailing comment on that line (`FOO = { # note`) so it survives.
        first_code = strip_inline_comment(block_lines[0])
        props["id_comment"] = block_lines[0][len(first_code) :].strip()
        if "=" in first_code:
            props["id"] = first_code.split("=")[0].strip()

        # A packed idea has its body on the opener line (`FOO = { picture = x }` on
        # one line). Explode braces so the property loop below sees one statement
        # per line instead of skipping the whole body.
        brace = first_code.find("{")
        if brace != -1 and first_code[brace + 1 :].strip():
            block_lines = _explode_braces(block_lines)

        i = 1  # Skip opening brace line
        while i < len(block_lines) - 1:  # Skip closing brace
            line = block_lines[i].strip()
            match = PROP_NAME_RE.match(line)
            prop_name = match.group(1) if match else None

            if prop_name in _SINGLE_LINE_PROPS:
                props[prop_name] = line
            elif prop_name in _BLOCK_PROPS:
                block, next_i = extract_block(block_lines, i)
                if prop_name in _ALWAYS_NO_FILTERED and self.is_always_no_block(
                    block, prop_name
                ):
                    i = next_i
                    continue
                if prop_name == "allowed":
                    # Replace tag = TAG with original_tag = TAG (civil war safety).
                    # Only touch the code portion so a commented `#tag = X` line
                    # is preserved verbatim.
                    block = [_rewrite_allowed_tag(bl) for bl in block]
                props[prop_name].append(block)
                i = next_i
                continue
            elif line.startswith("#"):
                props["other"].append(("comment", block_lines[i].rstrip()))
            elif line:
                # Blank quoted strings before counting so a `{` inside a quoted
                # value isn't misread as a block opener (which would send the
                # quote-aware extract_block negative and drop lines to the closer).
                code = blank_quoted_strings(strip_inline_comment(line))
                if code.count("{") > code.count("}"):
                    block, next_i = extract_block(block_lines, i)
                    if block:
                        props["other"].append(("block", block))
                        i = next_i
                        continue
                props["other"].append(("line", line))

            i += 1

        return props

    def is_empty_log_block(self, block_lines: List[str]) -> bool:
        """Check if a block is an empty log-only block (performance issue)"""
        if not block_lines:
            return True

        for line in block_lines:
            stripped = line.strip()
            if stripped in ("{", "}", "") or not stripped:
                continue
            if stripped.startswith("#"):
                continue
            if stripped.endswith("{"):  # block opener, e.g. `on_remove = {`
                continue
            if 'log = ""' in stripped or "log = ''" in stripped:
                continue
            return False

        return True

    def has_meaningful_effects(self, block_lines: List[str]) -> bool:
        """Check if a block has meaningful effects beyond just logging"""
        if not block_lines:
            return False

        for line in block_lines:
            stripped = line.strip()
            if (
                stripped in ("{", "}", "")
                or not stripped
                or stripped.startswith("#")
                or stripped.endswith("{")  # block opener, e.g. `on_remove = {`
                or stripped.startswith("log =")
            ):
                continue
            return True

        return False

    def is_always_no_block(self, block_lines: List[str], property_name: str) -> bool:
        """Check if a block contains only `always = no` — a redundant default.

        Removed as code cleanup, NOT a performance optimization.
        `allowed` is checked once at game start/load (default = always allowed)
        and is bypassed by add_ideas — so `allowed = { always = no }` is dead code.
        Tradeoff: `has_available_idea_with_trait` builds a list of every idea that
        passes `allowed`, then evaluates their `available` triggers at runtime.
        Keeping `allowed = { always = no }` keeps ideas out of that list (fewer
        runtime checks). Removing it lets more ideas into the pool (more runtime
        checks). MD does not use that trigger, so the tradeoff is moot here.
        """
        if property_name not in _ALWAYS_NO_FILTERED:
            return False
        return any(
            "always = no" in line.strip() or "always=no" in line.strip()
            for line in block_lines
        )

    def compact_block(
        self, block_lines: List[str], base_indent: str = "\t\t"
    ) -> List[str]:
        """Reindent a block by brace depth, dropping blank lines and keeping
        comments. Multi-brace lines (e.g. `if = { limit = {`) are counted so
        nesting stays intact instead of flattening."""
        if not block_lines:
            return block_lines

        compacted = []
        depth = 0

        for line in block_lines:
            stripped = line.strip()
            if not stripped:
                continue

            code = strip_inline_comment(stripped)
            opens = code.count("{")
            closes = code.count("}")

            if closes > opens:
                indent_depth = max(0, depth - (closes - opens))
            else:
                indent_depth = depth

            compacted.append(base_indent + ("\t" * indent_depth) + stripped)
            depth = max(0, depth + opens - closes)

        return compacted

    def _reindent_or_collapse(
        self, block_lines: List[str], prop_indent: str
    ) -> List[str]:
        """Single-line collapse a single-leaf block, else reindent at prop_indent."""
        collapsed = collapse_or_compact(block_lines[:], prop_indent)
        multi = self.compact_block(block_lines[:], prop_indent)
        if len(collapsed) == 1 and len(multi) != 1:
            return collapsed
        return multi

    def _emit_lifecycle_block(
        self,
        block: List[str],
        prop_indent: str,
        idea_id: str,
        action: str,
    ) -> List[str]:
        """Emit an on_add / on_remove block, injecting a log line if there are
        meaningful effects and no existing log. Returns [] if the block is an
        empty log-only block or has no meaningful effects."""
        # A single-line block (`on_add = { set_variable = { x = 1 } }`) has its
        # opener and closer on the same line, so an injected log would land
        # outside the block and re-inject on the next run (non-idempotent).
        # Explode it only when a log will actually be injected (meaningful
        # effects, no existing log) — leaving log-only single-line blocks handled
        # exactly as before so this fix doesn't silently strip them.
        if len(block) == 1:
            exploded = _explode_braces(block)
            # An empty single-line block (`on_add = { }`) reads as meaningful when
            # left packed, so the legacy path would inject a log outside its
            # braces. Detect emptiness on the exploded form and drop it.
            if self.is_empty_log_block(exploded):
                return []
            if self.has_meaningful_effects(exploded) and not any(
                "log =" in line for line in exploded
            ):
                block = exploded
        if self.is_empty_log_block(block):
            return []
        if not self.has_meaningful_effects(block):
            return []

        has_log = any("log =" in line for line in block)
        if not has_log and idea_id:
            log_line = (
                f'{prop_indent}\tlog = "[GetDateText]: [Root.GetName]: '
                f'Idea {idea_id} {action}"'
            )
            modified = []
            for j, line in enumerate(block):
                modified.append(line)
                if j == 0 and "{" in line:
                    modified.append(log_line)
            block = modified

        return self.compact_block(block[:], prop_indent)

    def format_block(self, props: Dict[str, Any], base_indent: str = "\t") -> List[str]:
        """Format idea according to Millennium Dawn standard"""
        lines = []

        # Idea ID (first line) - use base indent, keeping any opener comment.
        id_comment = props.get("id_comment", "")
        suffix = f" = {{ {id_comment}" if id_comment else " = {"
        if props["id"]:
            lines.append(base_indent + props["id"] + suffix)
        else:
            lines.append(base_indent + "idea" + suffix)

        # Property indent is one level deeper
        prop_indent = base_indent + "\t"

        # 1. Name (optional, first property if present)
        if props["name"]:
            lines.append(prop_indent + props["name"])

        # 2. Picture
        if props["picture"]:
            lines.append(prop_indent + props["picture"])

        # 3-10. Simple blocks emitted in order
        for key in (
            "allowed",
            "allowed_civil_war",
            "cancel",
            "modifier",
            "targeted_modifier",
            "research_bonus",
            "rule",
            "equipment_bonus",
        ):
            for block in props[key]:
                lines.extend(self._reindent_or_collapse(block, prop_indent))

        # 11. on_add (log only when making changes)
        for block in props["on_add"]:
            lines.extend(
                self._emit_lifecycle_block(block, prop_indent, props["id"], "added")
            )

        # 12. on_remove (log only when making changes)
        for block in props["on_remove"]:
            lines.extend(
                self._emit_lifecycle_block(block, prop_indent, props["id"], "removed")
            )

        # 13. Other properties in source order — comments, single-line props,
        # and unknown/nested blocks (reindented, structure preserved).
        for kind, data in props["other"]:
            if kind == "block":
                lines.extend(self._reindent_or_collapse(data, prop_indent))
            else:
                lines.append(prop_indent + data.strip())

        lines.append(base_indent + "}")

        # Clean up excessive blank lines - ensure exactly 1 blank line between
        # sections, no blanks at start or end.
        cleaned_lines = []
        prev_line_blank = False
        last_idx = len(lines) - 1

        for i, line in enumerate(lines):
            is_blank = line.strip() == ""

            if i == 0 or i == last_idx:
                if not is_blank:
                    cleaned_lines.append(line)
                    prev_line_blank = False
            elif is_blank:
                if not prev_line_blank:
                    cleaned_lines.append("")
                prev_line_blank = True
            else:
                cleaned_lines.append(line)
                prev_line_blank = False

        return cleaned_lines

    def standardize_file(self, input_file: str, output_file: str) -> bool:
        """Standardize ideas file by handling nested structure properly"""
        self.start_time = time.time()
        log_message("INFO", f"Starting standardization of {input_file}", self.verbose)

        if not os.path.exists(input_file):
            log_message("ERROR", f"Input file not found: {input_file}")
            return False

        try:
            with open(input_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            log_message(
                "INFO", f"Read {len(lines)} lines from {input_file}", self.verbose
            )
        except Exception as e:
            log_message("ERROR", f"Failed to read {input_file}: {e}")
            return False

        output_lines = self._process_lines(lines, depth=0)

        try:
            with open(output_file, "w", encoding="utf-8") as f:
                for line in output_lines:
                    f.write(line + "\n")

            time_str = format_elapsed(time.time() - self.start_time)

            log_message("SUCCESS", f"Standardization completed in {time_str}")
            log_message("SUCCESS", f"Processed {self.processed_count} ideas")
            log_message("SUCCESS", f"Output written to: {output_file}")

        except Exception as e:
            log_message("ERROR", f"Failed to write {output_file}: {e}")
            return False

        return True

    def _process_lines(
        self, lines: List[str], depth: int, mode: str = "root"
    ) -> List[str]:
        """Recursively process lines, handling nested structures.

        ``mode`` tracks the level so category blocks are recognized by position,
        not by a hardcoded name list: ``root`` -> the ``ideas`` block; ``category``
        -> every direct child of ``ideas`` (country, hidden_ideas, and law/spirit
        categories like ``internal_factions``) is a wrapper; ``idea`` -> children
        of a category are ideas, unless the child is itself a known wrapper key
        (``country = { political_advisor = { ADVISOR = {...} } }``), which is
        recursed into rather than flattened. Without this, non-wrapper law
        categories were mistaken for ideas and their child ideas re-nested wrongly,
        and genuine 3-level nestings had their middle wrapper flattened.
        """
        output_lines = []
        i = 0

        while i < len(lines):
            line = lines[i].rstrip()

            if _BLOCK_START_RE.match(line):
                block_name = line.split("=")[0].strip()

                if mode == "root":
                    is_wrapper = block_name in self.WRAPPER_BLOCKS
                    child_mode = "category"
                elif mode == "category":
                    is_wrapper = True  # every direct child of `ideas` is a category
                    child_mode = "idea"
                else:  # mode == "idea"
                    # A genuine wrapper key nested under a category is recursed
                    # into; a plain idea (not in the set) is formatted as a block.
                    is_wrapper = block_name in self.WRAPPER_BLOCKS
                    child_mode = "idea"

                if is_wrapper:
                    log_message(
                        "DEBUG",
                        f"Found wrapper block: {block_name} at line {i + 1}",
                        self.verbose,
                    )
                    block_lines, next_i = extract_block(lines, i)
                    if len(block_lines) == 1:
                        # A packed one-line wrapper (`internal_factions = { X = {...} }`)
                        # has its opener and closer on the same physical line; the raw
                        # opener/closer path would emit that line twice. Explode it so
                        # opener, inner, and closer are distinct.
                        indent = line[: len(line) - len(line.lstrip("\t"))]
                        exploded = _explode_braces(block_lines)
                        output_lines.append(indent + exploded[0])
                        output_lines.extend(
                            self._process_lines(exploded[1:-1], depth + 1, child_mode)
                        )
                        output_lines.append(indent + exploded[-1])
                    else:
                        output_lines.append(line)
                        inner_lines = block_lines[1:-1]  # Skip opening/closing braces
                        output_lines.extend(
                            self._process_lines(inner_lines, depth + 1, child_mode)
                        )
                        if block_lines:
                            output_lines.append(block_lines[-1].rstrip())

                    i = next_i
                else:
                    log_message(
                        "DEBUG",
                        f"Found idea: {block_name} at line {i + 1}",
                        self.verbose,
                    )
                    block_lines, next_i = extract_block(lines, i)

                    if block_lines:
                        props = self.extract_properties(block_lines)
                        base_indent = "\t" * depth
                        output_lines.extend(self.format_block(props, base_indent))
                        self.processed_count += 1

                        log_message(
                            "DEBUG",
                            f"Processed idea {self.processed_count}: {props.get('id', 'unknown')}",
                            self.verbose,
                        )

                    i = next_i
            else:
                output_lines.append(line)
                i += 1

        return output_lines


def main():
    run_standardizer(
        IdeaStandardizer,
        "Standardize HOI4 idea files according to Millennium Dawn coding standards",
    )


if __name__ == "__main__":
    main()
