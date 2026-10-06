#!/usr/bin/env python3
"""Validate that callers of documented scripted effects pass required temp variables.

Auto-discovers parameter contracts from "# Parameters:" comment blocks in
common/scripted_effects/*.txt and validates each call site sets required vars
before calling. Warns on scope-boundary violations (temp var set inside a
scope-changing block, but the effect call is outside). The reverse is checked
too: a declared parameter that is set and then never used is a dead setter.
"""

import functools
import glob
import os
import re
from typing import Dict, Iterable, List, Set, Tuple

import disk_cache
from shared_utils import (
    blank_quoted_strings,
    extract_block_from_text,
    get_staged_files,
)
from validate_unused_scripted import extract_definitions
from validator_common import (
    HOI4_BUILTIN_BLOCKS,
    BaseValidator,
    Severity,
    run_validator_main,
    strip_comments,
)

# Every tree the engine runs script from, not a per-directory caller list: that
# list drifted past operations, scripted_diplomatic_actions, ideas, MIOs,
# factions and bop, all of which already call contracted effects, and any new
# common/ subdirectory would be missed the same way. _validate_call_sites_in_file
# drops a file that names no contract before parsing it, so the extra breadth
# costs a read per file.
_CALLER_PATTERNS = [
    "common/**/*.txt",
    "events/**/*.txt",
    "history/**/*.txt",
]

# A staged change here can break a caller that did not change.
_DEPENDENCY_DIRS = (
    "common/scripted_effects",
    "common/scripted_triggers",
    "common/country_tags",
    "common/country_tag_aliases",
)

# Hardcoded contracts for well-documented effects. Auto-discovery fills in
# additional contracts from "# Parameters:" comment blocks.
# Mapping: effect_name -> { "required": [...], "optional": [...] }
HARDCODED_CONTRACTS: Dict[str, Dict[str, List[str]]] = {
    "change_influence_percentage": {
        "required": ["percent_change"],
        "optional": ["tag_index", "influence_target"],
    },
    "change_domestic_influence_percentage": {
        "required": ["percent_change"],
        "optional": ["influencer_index"],
    },
    "change_current_influencer_index_percentage": {
        "required": ["percent_change", "influencer_index"],
        "optional": [],
    },
    "steal_from_party": {
        "required": ["steal_party_index"],
        "optional": [],
    },
    "remove_coalition_members_effect": {
        "required": ["remove_col_one"],
        "optional": [],
    },
    "change_arab_spring_strength": {
        "required": ["temp_strength"],
        "optional": [],
    },
    "add_hydroelectric_energy_production_effect": {
        "required": ["electric_addition", "storage_addition"],
        "optional": [],
    },
    "get_pol_distance": {
        "required": ["pol_dist_target_index", "pol_dist_source_index"],
        "optional": [],
    },
    "configure_religious_setup": {
        "required": ["nation_to_copy_from"],
        "optional": [],
    },
    "set_elections_with_frequency": {
        "required": ["election_freq"],
        "optional": ["election_year_param", "election_month_param"],
    },
}

# Scope keywords: a temp var set inside one of these blocks is NOT available
# in the parent scope after the block closes.
# The every_/random_ iterators come from HOI4_BUILTIN_BLOCKS so a newly-added
# iterator only needs to be registered there. Remaining entries (relation/magic
# scopes, loops, var:X = {}) aren't engine "blocks", so they stay explicit.
_SCOPE_ITERATORS = {
    b for b in HOI4_BUILTIN_BLOCKS if b.startswith(("every_", "random_"))
} - {
    "random_list"  # probability buckets, not a scope change
}
SCOPE_CHANGING_KEYWORDS: Set[str] = {
    keyword.lower()
    for keyword in _SCOPE_ITERATORS
    | {
        "capital_scope",
        "owner",
        "controller",
        "overlord",
        "faction_leader",
        "ROOT",
        "PREV",
        "FROM",
        "var",  # var:X = { } scope
        "for_each_scope_loop",
        "while_loop_effect",
        "for_loop_effect",
        "for_each_loop",
    }
}

# Each of these runs as its own effect, so its temp variables are gone before
# the next one runs.
EFFECT_BLOCK_KEYWORDS: Set[str] = {
    "completion_reward",
    "completion_reward_joint_originator",
    "completion_reward_joint_member",
    "select_effect",
    "immediate",
    "option",
    "complete_effect",
    "remove_effect",
    "timeout_effect",
    "cancel_effect",
    "bypass_effect",
    "effect",
    "on_add",
    "on_remove",
    "on_activate",
    "on_deactivate",
    "on_complete",
    "outcome_extra_execute",
}

# Every statement that gives a temp variable a value. add_to/subtract_from count:
# they start from zero on an unset variable. `var = NAME` is the long form.
_TEMP_WRITERS = (
    r"(?:set_temp_variable(?:_to_random)?|add_to_temp_variable"
    r"|subtract_from_temp_variable)"
)
_TEMP_TARGET = r"(?:var\s*=\s*)?([a-zA-Z_][a-zA-Z0-9_]*)"
_SET_TEMP_RE = re.compile(
    r"\b" + _TEMP_WRITERS + r"\s*=\s*\{\s*" + _TEMP_TARGET + r"\s*=?\s*([^}]*?)\s*\}",
)
_CALL_RE = re.compile(r"\b([A-Za-z][A-Za-z0-9_]*)\s*=\s*yes\b")
_SINGLE_CALL_LINE_RE = re.compile(
    r"(?:[A-Za-z0-9_:.@^+-]+\s*=\s*\{\s*)*"
    r"[A-Za-z][A-Za-z0-9_]*\s*=\s*yes\s*(?:\}\s*)*"
)
# Numeric scopes (741 = {) must open a block, or their close pops the wrong one.
_KW_OPEN_RE = re.compile(r"\b([A-Za-z0-9_]+)\s*=\s*\{")

_READ_ERRORS = (OSError, UnicodeDecodeError)


def _unreadable(filepath: str, mod_path: str, exc: Exception) -> str:
    """Describe an input that could not be read, in the `file:line - text` form."""
    rel = os.path.relpath(filepath, mod_path)
    return f"{rel}:0 - cannot read file ({type(exc).__name__})"


def _normalize_influence_value(value: str) -> str:
    """Normalize a tag_index / influence_target value for identity comparison.

    The corpus mixes two equivalent syntaxes for the same source:
        USA       (country scope)         vs  USA.id      (country ID)
        var:foo   (variable scope)        vs  var:foo.id  (variable ID)
        THIS      (scope keyword)         vs  THIS.id     (scope keyword ID)
        event_target:foo                  vs  event_target:foo.id
    All six forms resolve to the same numeric tag at runtime.  Stripping
    the trailing ".id" so both forms collapse to a canonical form lets the
    identity check catch the full set of same-source pairs, not just the
    half where the author happened to use the same syntax on both sides.

    The ".id" match is case-insensitive: the corpus ships "FROM.ID" as
    well as "FROM.id", and both resolve to the same numeric ID.
    """
    if value.lower().endswith(".id"):
        return value[:-3]
    return value


def _same_influence_source(tag_entry: Dict, inf_entry: Dict) -> bool:
    """Return whether both entries are guaranteed to resolve to one country."""
    tag_value = _normalize_influence_value(tag_entry["value"])
    inf_value = _normalize_influence_value(inf_entry["value"])
    if tag_value != inf_value:
        return False
    if tag_value.upper() == "THIS":
        return tag_entry["scope_depth"] == inf_entry["scope_depth"]
    return True


# Scope keywords that resolve to a country at runtime and are NOT tags.  A value
# matching one of these (case-insensitively, so "Root" passes) is a valid
# tag_index / influence_target reference, never a typo.
_INFLUENCE_SCOPE_KEYWORDS: Set[str] = {
    "ROOT",
    "THIS",
    "PREV",
    "FROM",
    "OWNER",
    "CONTROLLER",
    "OVERLORD",
    "CAPITAL",
    "FROMFROM",
    "PREVPREV",
}
_TAG_LITERAL_RE = re.compile(r"[A-Z][A-Z0-9_]{2}")
_MISCASED_TAG_RE = re.compile(r"[A-Za-z]{3}")
_NUMERIC_RE = re.compile(r"-?\d+(\.\d+)?")


def _load_valid_country_tags(mod_path: str) -> Tuple["frozenset[str]", List[str]]:
    """Load valid country tags and tag aliases as one accept-set.

    Tags come from common/country_tags/*.txt (`TAG = "path"`); aliases from
    common/country_tag_aliases/*.txt (`ALIAS = { ... }`).  Aliases are real
    references at runtime — e.g. STC / NTR are aliases, not typos — so the
    tag-validity check accepts both.  Also returns the files that could not
    be read.
    """
    valid: Set[str] = set()
    unreadable: List[str] = []
    tag_re = re.compile(r'^\s*([A-Z0-9_]{3})\s*=\s*"')
    for fp in glob.glob(os.path.join(mod_path, "common", "country_tags", "*.txt")):
        try:
            with open(fp, "r", encoding="utf-8-sig") as fh:
                for line in fh:
                    m = tag_re.match(line)
                    if m:
                        valid.add(m.group(1))
        except _READ_ERRORS as exc:
            unreadable.append(_unreadable(fp, mod_path, exc))
    alias_re = re.compile(r"^\s*([A-Za-z0-9_]{3})\s*=\s*\{")
    for fp in glob.glob(
        os.path.join(mod_path, "common", "country_tag_aliases", "*.txt")
    ):
        try:
            with open(fp, "r", encoding="utf-8-sig") as fh:
                for line in fh:
                    m = alias_re.match(line)
                    if m:
                        valid.add(m.group(1))
        except _READ_ERRORS as exc:
            unreadable.append(_unreadable(fp, mod_path, exc))
    return frozenset(valid), unreadable


def _is_invalid_influence_tag(value: str, valid_tags: "frozenset[str]") -> bool:
    """Return True if `value` is a tag_index / influence_target that no tag matches.

    `value` is the RHS of `set_temp_variable = { tag_index/influence_target = ... }`.
    Accepts real tags, tag aliases, scope keywords, var: / event_target: /
    global. references, array subscripts, getters, numerics, and bare
    temp-variable names.  Flags only literals that look like a country tag but
    are not one — typos such as GBR for ENG, ISL for ICE, or the mis-cased
    CHl for CHI.
    """
    v = _normalize_influence_value(value.strip())
    if not v or _NUMERIC_RE.fullmatch(v):
        return False
    # var: / event_target: / global. refs, array subscripts (name^i), getters
    if any(c in v for c in ":^.@"):
        return False
    if v.upper() in _INFLUENCE_SCOPE_KEYWORDS:
        return False
    # An all-caps tag literal, or a 3-letter mixed-case token (a mis-cased tag
    # like CHl): must match a real tag exactly, since tags are case-sensitive.
    if _TAG_LITERAL_RE.fullmatch(v) or (
        _MISCASED_TAG_RE.fullmatch(v) and v != v.lower()
    ):
        return v not in valid_tags
    return False


def _parse_effect_contracts_from_file(
    filepath: str,
) -> Dict[str, Dict[str, List[str]]]:
    """Parse a scripted_effects file and extract parameter contracts from comment blocks.

    Looks for the pattern:
        # Parameters:
        # - param_name: description
        effect_name = {

    A read or decode error propagates so the caller can report the file.
    """
    with open(filepath, "r", encoding="utf-8-sig") as fh:
        content = fh.read()

    contracts: Dict[str, Dict[str, List[str]]] = {}
    lines = content.splitlines()
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()

        # Look for "# Parameters:" or "# Parameter:" comment block
        if re.match(r"^#\s*[Pp]arameters?\s*:", stripped):
            params_required: List[str] = []
            params_optional: List[str] = []
            j = i + 1

            while j < len(lines):
                pline = lines[j].strip()
                if not pline.startswith("#"):
                    break
                inner = pline.lstrip("#").strip()
                if not inner or re.match(r"^[-=*]+$", inner):
                    j += 1
                    continue

                # "# set_temp_variable = { param_name = ... }"
                stv_m = re.search(
                    r"set_temp_variable\s*=\s*\{\s*([A-Za-z][A-Za-z0-9_]*)\s*=", inner
                )
                if stv_m:
                    pname = stv_m.group(1)
                    if "optional" in inner.lower():
                        params_optional.append(pname)
                    else:
                        params_required.append(pname)
                    j += 1
                    continue

                # "# - param_name: ..." or "# - param_name - ..."
                plain_m = re.match(r"^[-\*]?\s*([A-Za-z][A-Za-z0-9_]*)\s*[-:]", inner)
                if plain_m:
                    pname = plain_m.group(1)
                    skip_words = {
                        "note",
                        "purpose",
                        "effect",
                        "function",
                        "output",
                        "how",
                        "example",
                        "null",
                        "none",
                        "n",
                        "a",
                        "the",
                        "this",
                        "see",
                        "usage",
                    }
                    if pname.lower() not in skip_words:
                        if "optional" in inner.lower():
                            params_optional.append(pname)
                        else:
                            params_required.append(pname)
                j += 1

            # Find the effect definition immediately after the comment block
            k = j
            while k < len(lines) and not lines[k].strip():
                k += 1
            if k < len(lines):
                def_m = re.match(r"^([A-Za-z][A-Za-z0-9_]*)\s*=\s*\{", lines[k].strip())
                if def_m and (params_required or params_optional):
                    eff_name = def_m.group(1)
                    if eff_name not in HARDCODED_CONTRACTS:
                        contracts[eff_name] = {
                            "required": params_required,
                            "optional": params_optional,
                        }
            i = j
            continue
        i += 1

    return contracts


def _normalize_multiline_set_temp(text: str) -> str:
    """Collapse multi-line temp-variable writes without changing line numbers."""
    normalized = []
    cursor = 0
    pattern = re.compile(r"\b" + _TEMP_WRITERS + r"\s*=\s*\{")
    target = re.compile(r"\s*" + _TEMP_TARGET)

    while match := pattern.search(text, cursor):
        block_start = match.end() - 1
        name_match = target.match(text, block_start + 1)
        if not name_match:
            normalized.append(text[cursor : match.end()])
            cursor = match.end()
            continue

        depth = 1
        block_end = block_start + 1
        while block_end < len(text) and depth:
            if text[block_end] == "{":
                depth += 1
            elif text[block_end] == "}":
                depth -= 1
            block_end += 1
        if depth or "\n" not in text[block_start:block_end]:
            normalized.append(text[cursor : match.end()])
            cursor = match.end()
            continue

        normalized.append(text[cursor : match.start()])
        normalized.append(f"set_temp_variable = {{ {name_match.group(1)} = 0 }}")
        normalized.append("\n" * text[match.start() : block_end].count("\n"))
        cursor = block_end

    normalized.append(text[cursor:])
    return "".join(normalized)


def _tokenize(text: str) -> List[Tuple[str, int, str, str]]:
    """Tokenize script text, comments stripped and quotes blanked, into tokens.

    Each token is (kind, line_number, value, rhs):
      "set_temp"   — set_temp_variable = { NAME = RHS }  (value=NAME, rhs=RHS)
      "call"       — NAME = yes                           (value=NAME, rhs="")
      "scope_open" — NAME = { (scope-changing or effect)  (value=NAME, rhs="")
      "plain_open" — NAME = { (any other block)           (value=NAME, rhs="")
      "close"      — }                                    (value="",    rhs="")
    The rhs on a set_temp is the literal RHS string (whitespace stripped).
    It powers the identical-params check for change_influence_percentage; any
    other call site only needs the name.
    """
    # Collapse multi-line set_temp_variable = { ... } blocks so the regex can
    # match them on a single line.
    text = _normalize_multiline_set_temp(text)

    tokens: List[Tuple[str, int, str, str]] = []
    lines = text.splitlines()

    for lineno, raw in enumerate(lines, start=1):
        line_tokens = []
        for m in _SET_TEMP_RE.finditer(raw):
            line_tokens.append(
                (m.start(), 0, ("set_temp", lineno, m.group(1), m.group(2).strip()))
            )
        for m in _KW_OPEN_RE.finditer(raw):
            kw = m.group(1)
            line_tokens.append(
                (
                    m.start(),
                    1,
                    (
                        (
                            "scope_open"
                            if kw.lower() in SCOPE_CHANGING_KEYWORDS
                            or kw in EFFECT_BLOCK_KEYWORDS
                            else "plain_open"
                        ),
                        lineno,
                        kw,
                        "",
                    ),
                )
            )
        for m in re.finditer(r"\}", raw):
            line_tokens.append((m.start(), 0, ("close", lineno, "", "")))
        for m in _CALL_RE.finditer(raw):
            line_tokens.append((m.start(), 0, ("call", lineno, m.group(1), "")))

        # Sort by source position, not by the category that discovered a token.
        # The remaining fields make overlapping matches deterministic.
        line_tokens.sort(
            key=lambda item: (item[0], item[1], item[2][0], item[2][2], item[2][3])
        )
        tokens.extend(token for _offset, _priority, token in line_tokens)

    return tokens


def _validate_call_sites_in_file(
    args: Tuple[
        str, Dict[str, Dict[str, List[str]]], str, "frozenset[str]", "frozenset[str]"
    ],
) -> List[Tuple[str, str, int]]:
    """Validate one file for missing required params and orphaned sets.

    A call may share its line with enclosing wrappers and closing braces,
    but not other statements. ``audit_names`` checks uncontracted effects too.

    Returns a list of (category, message, line_number) tuples.
    """
    filepath, contracts, mod_path, valid_tags, audit_names = args

    try:
        with open(filepath, "r", encoding="utf-8-sig") as fh:
            raw = fh.read()
    except _READ_ERRORS as exc:
        return [("unreadable-input", _unreadable(filepath, mod_path, exc), 0)]

    # A quoted log can hold a `#`, a brace, or text shaped like a call.
    text = blank_quoted_strings(strip_comments(raw))
    rel = os.path.relpath(filepath, mod_path)

    # Quick pre-check: does this file reference any contracted effect?
    contracted_names = set(contracts.keys())
    if not audit_names and not any(name in text for name in contracted_names):
        return []

    lines = text.splitlines()
    shared_lines: Set[int] = set()
    results: List[Tuple[str, str, int]] = []
    # Cache the tokenisation (the expensive, contract-independent step); the
    # contract validation below runs per call against the cached tokens.
    tokens = disk_cache.per_file_cached_by_content(
        mod_path, "scripted_params.tokens", filepath, text, lambda: _tokenize(text)
    )
    contracted_lines = {
        line
        for kind, line, name, _rhs in tokens
        if kind == "call" and name in contracts
    }

    # Scope stack.  Each frame:
    #   "scope_changing": bool — True if opened by a scope-changing keyword
    #   "temps": Dict[str, int]  — temp vars SET at this frame level -> line number
    #   "depth": int — count of non-scope-changing { } nesting inside this frame
    #
    # Temp variables set in a frame are visible to all descendants until the
    # frame is popped.  This means a set_temp at depth 0 is visible inside any
    # if/hidden_effect/etc. at deeper non-scope-changing levels, which is the
    # correct HOI4 behaviour.
    #
    # When a scope-changing keyword opens, we push a new frame.  Temp vars from
    # outer frames are NOT passed into the inner frame's "temps", but they are
    # still technically visible to the inner scope in the game engine.  However,
    # if a param is set ONLY in the inner frame and the CALL is outside, that is
    # a scope-boundary violation.

    stack: List[Dict] = [{"scope_changing": False, "temps": {}, "depth": 0}]

    for kind, lineno, value, rhs in tokens:
        if kind == "scope_open":
            # Push a new scope frame
            stack.append({"scope_changing": True, "temps": {}, "depth": 0})

        elif kind == "plain_open":
            # Non-scope-changing open: increment depth counter on current frame
            stack[-1]["depth"] += 1

        elif kind == "close":
            if stack[-1]["depth"] > 0:
                stack[-1]["depth"] -= 1
            elif len(stack) > 1:
                stack.pop()
            # else: extra close at root, ignore

        elif kind == "set_temp":
            # Record in the current frame. Track both the line and the RHS
            # value: the line is used for the existing missing-param check,
            # and the RHS powers the identical-params check for
            # change_influence_percentage.
            stack[-1]["temps"][value] = {
                "line": lineno,
                "value": rhs,
                "scope_depth": len(stack),
            }

            # Tag-validity check: an influencer/influencee written as a literal
            # that is neither a real tag nor an alias is a silent typo (resolves
            # to nothing at runtime, so the influence call no-ops or misfires).
            if value in ("tag_index", "influence_target") and _is_invalid_influence_tag(
                rhs, valid_tags
            ):
                results.append(
                    (
                        "invalid-influence-tag",
                        f"{rel}:{lineno} - '{value}' set to {rhs!r} which is not a "
                        f"valid country tag or tag alias",
                        lineno,
                    )
                )

        elif kind == "call":
            contracted = value in contracts
            if (
                (
                    contracted
                    or (value in audit_names and lineno not in contracted_lines)
                )
                and lineno not in shared_lines
                and not _SINGLE_CALL_LINE_RE.fullmatch(lines[lineno - 1].strip())
            ):
                shared_lines.add(lineno)
                results.append(
                    (
                        "call-shares-line" if contracted else "audit-call-shares-line",
                        f"{rel}:{lineno} - '{value}' shares its line with other "
                        f"statements; put the call on its own line",
                        lineno,
                    )
                )
            if not contracted:
                continue

            contract = contracts[value]
            required = contract.get("required", [])

            # Collect all temp vars visible in the current scope chain
            # (frames at all levels, since even outer scope vars are visible
            # unless a scope-changing frame was introduced after they were set)
            #
            # The visibility model: temp vars set before a scope-changing block
            # are visible inside it; temp vars set inside a scope-changing block
            # are NOT visible outside.  Since we track frames, any temp var in
            # any frame on the stack at this point was set in the current or an
            # ancestor scope, so it is visible.
            visible: Dict[str, Dict] = {}
            for frame in stack:
                visible.update(frame["temps"])

            for param in required:
                if param not in visible:
                    results.append(
                        (
                            "missing-required-param",
                            f"{rel}:{lineno} - '{value}' called without required "
                            f"temp variable '{param}'",
                            lineno,
                        )
                    )

            # Identical-params check: a change_influence_percentage call where
            # tag_index and influence_target resolve to the same country is the
            # self-influence (Code 5001) bug.  Flag only when BOTH are set to an
            # explicit non-zero value; the effect's own defaults (tag_index ->
            # ROOT, influence_target -> THIS) are reliable and left alone.
            #
            # "Same block" is approximated by line proximity (<= 20 lines): the
            # scope tracker can keep a temp var from an earlier block it does not
            # reset, such as a previous scripted effect, visible when it wouldn't
            # be in scope at runtime, so the window suppresses those false
            # positives while still catching
            # the leak-between-calls pattern (tag_index from call N-1 reused by
            # call N).  Values are normalized so "USA"/"USA.id" and the other
            # .id variants compare equal.
            if value == "change_influence_percentage":
                tag_entry = visible.get("tag_index")
                inf_entry = visible.get("influence_target")
                if tag_entry and inf_entry:
                    tag_val = tag_entry["value"]
                    inf_val = inf_entry["value"]
                    tag_line = tag_entry["line"]
                    inf_line = inf_entry["line"]
                    if (
                        tag_val
                        and inf_val
                        and tag_val != "0"
                        and inf_val != "0"
                        and _same_influence_source(tag_entry, inf_entry)
                        and abs(lineno - tag_line) <= 20
                        and abs(lineno - inf_line) <= 20
                    ):
                        results.append(
                            (
                                "identical-influence-params",
                                f"{rel}:{lineno} - 'change_influence_percentage' called with "
                                f"tag_index = {tag_val!r} and influence_target = {inf_val!r}; "
                                f"both resolve to the same country and this is a self-influence "
                                f"(Code 5001) error",
                                lineno,
                            )
                        )

            # Scope-boundary violations (temp set inside a popped scope-changing
            # frame, call outside) are already caught by the missing-param check:
            # once the inner frame is popped, the param is no longer in any
            # frame on the stack, so the param check above will fire.

    return results


# Blocks that delimit one effect execution. hidden_effect is NOT a boundary:
# it runs in the same execution as its parent, only hidden from the tooltip.
# effect_tooltip is deliberately its own container: a setter previewed there
# must also be used there or the tooltip renders nothing.
_EFFECT_CONTAINER_RE = re.compile(
    r"\b(?:"
    + "|".join(sorted(EFFECT_BLOCK_KEYWORDS))
    + r"|effect_tooltip|\w+_click)\s*=\s*\{"
)
_SCRIPTED_EFFECT_DEF_RE = re.compile(r"^([A-Za-z0-9_]+)\s*=\s*\{", re.MULTILINE)
# A variable statement up to the operand it changes. That operand is not a read.
_TARGET_BEFORE_RE = re.compile(
    r"\b(?:set|add_to|subtract_from|multiply|divide|modulo|round|clamp)"
    r"_(?:temp_)?variable(?:_to_random)?\s*=\s*\{\s*(?:var\s*=\s*)?$"
)
# Longest statement opener, with its whitespace, that can precede an operand.
_OPENER_WINDOW = 160


@functools.lru_cache(maxsize=None)
def _param_res(var: str) -> Tuple[re.Pattern, re.Pattern]:
    """(any occurrence, value-producing write) patterns for one parameter.

    add_to/multiply etc. read the existing value, so they are not writes. The
    write's last group is the parameter it sets.
    """
    name = re.escape(var)
    return (
        re.compile(r"\b" + name + r"\b"),
        re.compile(
            r"\b(?:set_temp_variable|set_variable)\s*=\s*\{\s*(?:var\s*=\s*)?"
            r"(" + name + r")\s*(?:=|value\s*=)"
            r"|\bset_temp_variable_to_random\s*=\s*\{\s*var\s*=\s*(" + name + r")\b"
        ),
    )


@functools.lru_cache(maxsize=None)
def _setter_re(params: Tuple[str, ...]) -> re.Pattern:
    """A statement that hands one of the parameters a value, short or long form."""
    return re.compile(
        r"\b(?:set|add_to|subtract_from)_temp_variable\s*=\s*\{\s*(?:var\s*=\s*)?("
        + "|".join(re.escape(p) for p in params)
        + r")\s*(?:=|value\s*=)"
    )


@functools.lru_cache(maxsize=None)
def _consumer_call_re(effects: frozenset) -> re.Pattern:
    return re.compile(
        r"\b(?:" + "|".join(re.escape(n) for n in sorted(effects)) + r")\s*=\s*yes\b"
    )


def _scripted_bodies(filepath: str) -> Dict[str, str]:
    """Each scripted effect or trigger in a file, mapped to its comment-free body.

    A read or decode error propagates so the caller can report the file.
    """
    with open(filepath, "r", encoding="utf-8-sig") as fh:
        text = strip_comments(fh.read())
    bodies: Dict[str, str] = {}
    for m in _SCRIPTED_EFFECT_DEF_RE.finditer(text):
        body, _ = extract_block_from_text(text, m.start())
        if body:
            bodies[m.group(1)] = body
    return bodies


def _reads_itself(text: str, write_start: int, var_re: re.Pattern) -> bool:
    """Whether the write opening at write_start reads the variable it sets.

    The sole occurrence in the write's block is the l-value. A second one
    (``value = X multiply = -1``, events/raids.txt) folds the old value forward.
    """
    body, _ = extract_block_from_text(text, write_start)
    return len(var_re.findall(body)) > 1


def build_param_consumer_map(
    bodies: Dict[str, str], declared: Dict[str, Iterable[str]]
) -> Dict[str, frozenset]:
    """Map each declared parameter to the scripted effects that consume it.

    An effect consumes a parameter when the parameter's first appearance in
    its body is a read (add_to_variable r-value, multiply, check, ...) rather
    than a set_temp_variable/set_variable write. A wrapper that writes first
    overwrites the caller's value and cannot consume it. A write nested in a
    branch may not run, so it does not count, the same as on the caller side.
    Closed transitively so wrappers of wrappers (GRE_pay_or_defer ->
    modify_debt_effect) count. An effect needs no contract of its own to count.
    """
    callers: Dict[str, List[Tuple[str, int]]] = {}
    for name, body in bodies.items():
        for m in _CALL_RE.finditer(body):
            callers.setdefault(m.group(1), []).append((name, m.start()))

    consumers: Dict[str, frozenset] = {}
    for var, effects in declared.items():
        var_re, write_re = _param_res(var)
        first_write: Dict[str, int] = {}
        known = set(effects)
        for name, body in bodies.items():
            if var not in body:
                continue
            # target position -> start of the statement that writes it
            writes = {w.start(w.lastindex): w.start() for w in write_re.finditer(body)}
            read = write = None
            for om in var_re.finditer(body):
                opener = writes.get(om.start())
                if opener is None or _reads_itself(body, opener, var_re):
                    if read is None:
                        read = om.start()
                elif write is None and body.count("{", 0, opener) == body.count(
                    "}", 0, opener
                ):
                    write = om.start()
                if read is not None and write is not None:
                    break
            if write is not None:
                first_write[name] = write
            if read is not None and (write is None or read < write):
                known.add(name)
        queue = list(known)
        while queue:
            for caller, pos in callers.get(queue.pop(), ()):
                write = first_write.get(caller)
                if caller not in known and (write is None or pos < write):
                    known.add(caller)
                    queue.append(caller)
        consumers[var] = frozenset(known)
    return consumers


def _has_sequential_rewrite(
    cleaned: str, start: int, end: int, var_re: re.Pattern, write_re: re.Pattern
) -> bool:
    """Whether the setter's variable is re-set in [start, end) as a clobber.

    Depth heuristic: only a re-write at the setter's own brace depth counts.
    Branch-gated writes (if/else arms) sit in nested blocks and never clobber.
    A same-depth re-write that reads the variable in its value expression
    folds the old value forward and is not a clobber either.
    """
    rewrites = [w.start() for w in write_re.finditer(cleaned, start, end)]
    if not rewrites:
        return False
    ri = 0
    depth = 1  # start sits inside the setter's own braces
    for i in range(start, end):
        if ri < len(rewrites) and rewrites[ri] == i:
            if depth == 0:
                # The first same-depth re-write decides.
                return not _reads_itself(cleaned, i, var_re)
            ri += 1
            if ri == len(rewrites):
                return False
        c = cleaned[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth < 0:
                return False
    return False


def _scan_orphan_setters_text(
    cleaned: str, consumers: Dict[str, frozenset]
) -> List[Tuple[str, bool, int]]:
    """Find declared-parameter setters that are dead in their block: never
    used, or overwritten at the same depth before the first use.

    A use is a call to an effect that consumes the parameter, or a direct read
    of it. A use inside a nested effect_tooltip counts, since a preview reads
    the value too. Setters outside any known effect container (loose
    scripted-effect bodies that produce the value for their caller) are skipped.
    Returns (parameter, overwritten, line) triples.
    """
    setters = list(_setter_re(tuple(sorted(consumers))).finditer(cleaned))
    if not setters:
        return []

    spans = []
    for m in _EFFECT_CONTAINER_RE.finditer(cleaned):
        brace = m.end() - 1
        body, end = extract_block_from_text(cleaned, brace)
        if body:
            spans.append((brace + 1, end))

    found: List[Tuple[str, bool, int]] = []
    for m in setters:
        var = m.group(1)
        holder_start = -1
        holder_end = -1
        for start, end in spans:
            if start <= m.start() < end and start > holder_start:
                holder_start = start
                holder_end = end
        if holder_start < 0:
            continue
        var_re, write_re = _param_res(var)
        _, setter_end = extract_block_from_text(cleaned, m.start())
        # Assigning zero resets a parameter after use. It passes nothing on.
        if cleaned[m.end() : setter_end - 1].strip() == "0":
            continue
        uses = [
            cm.start()
            for cm in _consumer_call_re(consumers[var]).finditer(
                cleaned, m.end(), holder_end
            )
        ]
        # The setter's own value expression may read the variable it sets.
        uses += [
            om.start()
            for om in var_re.finditer(cleaned, setter_end, holder_end)
            if not _TARGET_BEFORE_RE.search(
                cleaned, max(0, om.start() - _OPENER_WINDOW), om.start()
            )
        ]
        overwritten = bool(uses) and _has_sequential_rewrite(
            cleaned, m.end(), min(uses), var_re, write_re
        )
        if not uses or overwritten:
            found.append((var, overwritten, cleaned.count("\n", 0, m.start()) + 1))
    return found


def _scan_orphan_setters_in_file(
    args: Tuple[str, str, Dict[str, frozenset], Dict[str, str]],
) -> List[str]:
    """Report the dead declared-parameter setters in one file."""
    filepath, mod_path, consumers, owners = args
    try:
        with open(filepath, "r", encoding="utf-8-sig") as fh:
            raw = fh.read()
    except _READ_ERRORS:
        # The call-site pass reads the same file and reports it.
        return []
    if "_temp_variable" not in raw or not any(var in raw for var in consumers):
        return []

    rel = os.path.relpath(filepath, mod_path)
    results = []
    text = blank_quoted_strings(strip_comments(raw))
    for var, overwritten, line in _scan_orphan_setters_text(text, consumers):
        if overwritten:
            results.append(
                f"{rel}:{line} - '{var}' is set and then overwritten before"
                f" anything uses it, so this setter is dead"
            )
        else:
            results.append(
                f"{rel}:{line} - '{var}' is set but never used: no {owners[var]}"
                f" call, wrapper, or read follows in the same effect block"
            )
    return results


class Validator(BaseValidator):
    TITLE = "SCRIPTED EFFECT PARAMETER VALIDATION"
    STAGED_EXTENSIONS = [".txt"]

    def __init__(self, *args, audit_shared_lines: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.audit_shared_lines = audit_shared_lines
        self._audit_names: Set[str] = set()
        self._contracts: Dict[str, Dict[str, List[str]]] = {}
        # Every declared parameter, required or optional -> effects declaring it.
        self._declared: Dict[str, Set[str]] = {}
        self._consumers: Dict[str, frozenset] = {}
        self._valid_tags: "frozenset[str]" = frozenset()
        self._unreadable: List[str] = []
        if self.staged_only:
            # A deleted or renamed contract or tag file is a dependency change too.
            self.staged_files = (
                get_staged_files(
                    self.mod_path,
                    extensions=self.STAGED_EXTENSIONS,
                    include_missing=True,
                )
                or []
            )

    def _build_tag_set(self):
        """Load valid country tags + aliases for the tag-validity check."""
        self._valid_tags, unreadable = _load_valid_country_tags(self.mod_path)
        self._unreadable.extend(unreadable)
        self.log(f"  Valid country tags + aliases:     {len(self._valid_tags)}")

    def _declare(self, eff_name: str, contract: Dict[str, List[str]]):
        for param in contract["required"] + contract["optional"]:
            self._declared.setdefault(param, set()).add(eff_name)

    def _build_contracts(self):
        """Build the parameter contract registry from hardcoded + auto-discovered data."""
        self._log_section("Building scripted effect parameter contracts")

        self._contracts.update(HARDCODED_CONTRACTS)
        for eff_name, contract in HARDCODED_CONTRACTS.items():
            self._declare(eff_name, contract)

        # Auto-discover from scripted effect files (always full scan — definitions
        # are the truth set and must be complete even in staged mode)
        effect_files = glob.glob(
            os.path.join(self.mod_path, "common", "scripted_effects", "*.txt")
        )
        discovered = 0
        bodies: Dict[str, str] = {}
        for filepath in sorted(effect_files):
            try:
                parsed = _parse_effect_contracts_from_file(filepath)
                bodies.update(_scripted_bodies(filepath))
            except _READ_ERRORS as exc:
                self._unreadable.append(_unreadable(filepath, self.mod_path, exc))
                continue
            if self.audit_shared_lines:
                self._audit_names.update(
                    name
                    for name, _file, _line in extract_definitions(
                        (filepath, self.mod_path)
                    )
                )
            for eff_name, contract in parsed.items():
                self._declare(eff_name, contract)
                if eff_name not in self._contracts and contract["required"]:
                    self._contracts[eff_name] = contract
                    discovered += 1
        # A scripted trigger reads a parameter the same way an effect does.
        trigger_files = glob.glob(
            os.path.join(self.mod_path, "common", "scripted_triggers", "*.txt")
        )
        for filepath in sorted(trigger_files):
            try:
                bodies.update(_scripted_bodies(filepath))
            except _READ_ERRORS as exc:
                self._unreadable.append(_unreadable(filepath, self.mod_path, exc))
        self._consumers = build_param_consumer_map(bodies, self._declared)

        self.log(f"  Hardcoded contracts:              {len(HARDCODED_CONTRACTS)}")
        self.log(f"  Auto-discovered contracts:        {discovered}")
        self.log(f"  Total contracts:                  {len(self._contracts)}")
        for eff_name, c in sorted(self._contracts.items()):
            req = ", ".join(c.get("required", [])) or "(none)"
            opt = ", ".join(c.get("optional", [])) or "(none)"
            self.log(f"    {eff_name}: required=[{req}] optional=[{opt}]")

    def _validate_callers(self):
        """Validate all caller files against the contract registry."""
        self._log_section("Checking scripted effect parameter usage")

        if not self._declared:
            self.log("  No contracts found — nothing to validate")
            return

        rescan = self.staged_touches(_DEPENDENCY_DIRS)
        if rescan:
            self.log("  Contract or tag source staged: rescanning every caller")
        # Staged deletions are listed too and have nothing to scan.
        files = self._collect_files(
            _CALLER_PATTERNS,
            extra_skip=lambda path: not os.path.isfile(path),
            ignore_staged=rescan,
        )
        self.log(f"  Scanning {len(files)} files for effect calls")

        audit_names = frozenset(self._audit_names)
        args_list = [
            (f, self._contracts, self.mod_path, self._valid_tags, audit_names)
            for f in files
        ]
        all_results = self._pool_map(
            _validate_call_sites_in_file, args_list, chunksize=20
        )

        missing_param_results = []
        scope_violation_results = []
        identical_param_results = []
        invalid_tag_results = []
        shared_line_results = []
        audit_shared_line_results = []

        for file_results in all_results:
            for category, message, _line in file_results:
                if category == "missing-required-param":
                    missing_param_results.append(message)
                elif category == "scope-boundary-violation":
                    scope_violation_results.append(message)
                elif category == "identical-influence-params":
                    identical_param_results.append(message)
                elif category == "invalid-influence-tag":
                    invalid_tag_results.append(message)
                elif category == "call-shares-line":
                    shared_line_results.append(message)
                elif category == "audit-call-shares-line":
                    audit_shared_line_results.append(message)
                elif category == "unreadable-input":
                    self._unreadable.append(message)

        self._report(
            missing_param_results,
            "All contracted effect calls have required temp variables set",
            "Effect calls missing required temp variable setup:",
            severity=Severity.ERROR,
            category="missing-required-param",
        )

        self._report(
            scope_violation_results,
            "No scope-boundary violations found",
            "Scope-boundary violations (temp var set in inner scope, call in outer scope):",
            severity=Severity.ERROR,
            category="scope-boundary-violation",
        )

        self._report(
            identical_param_results,
            "No change_influence_percentage calls have identical tag_index and influence_target",
            "change_influence_percentage calls with tag_index == influence_target (self-influence):",
            severity=Severity.ERROR,
            category="identical-influence-params",
        )

        self._report(
            invalid_tag_results,
            "All tag_index / influence_target values are valid country tags or aliases",
            "tag_index / influence_target set to an unknown country tag (typo or removed tag):",
            severity=Severity.ERROR,
            category="invalid-influence-tag",
        )

        self._report(
            shared_line_results,
            "No contracted effect calls share a line with other statements",
            "Contracted effect calls sharing a line with other statements:",
            severity=Severity.ERROR,
            category="call-shares-line",
        )
        if self.audit_shared_lines:
            self._report(
                audit_shared_line_results,
                "No uncontracted effect calls share a line with other statements",
                "Uncontracted effect calls sharing a line with other statements:",
                severity=Severity.WARNING,
                category="audit-call-shares-line",
            )

        owners = {}
        for var, effects in self._declared.items():
            first = min(effects)
            more = len(effects) - 1
            owners[var] = f"{first} (or {more} more)" if more else first
        orphan_results = self._pool_map(
            _scan_orphan_setters_in_file,
            [(f, self.mod_path, self._consumers, owners) for f in files],
            chunksize=20,
        )
        self._report(
            [message for file_results in orphan_results for message in file_results],
            "Every declared parameter that is set is also used",
            "Declared parameters set and never used, or overwritten before use:",
            severity=Severity.ERROR,
            category="orphan-param-setter",
        )

    def run_validations(self):
        self._build_contracts()
        self._build_tag_set()
        self._validate_callers()
        # A scripted effect file is read as a contract source and as a caller.
        self._report(
            sorted(set(self._unreadable)),
            "All scripted effect inputs were readable",
            "Inputs that could not be read, so nothing in them was validated:",
            severity=Severity.ERROR,
            category="unreadable-input",
        )


def _add_extra_args(parser):
    parser.add_argument(
        "--audit-shared-lines",
        action="store_true",
        dest="audit_shared_lines",
        help="Also warn on uncontracted scripted effect calls that share a line "
        "with other statements; contracted calls remain errors",
    )


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate scripted effect parameters in Millennium Dawn mod",
        extra_args_fn=_add_extra_args,
    )
