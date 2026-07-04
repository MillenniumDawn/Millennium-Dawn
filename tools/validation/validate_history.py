#!/usr/bin/env python3
"""Validate technology prerequisites, equipment module unlocks, DLC gating,
and special-project requirements in history files."""

import glob
import os
import re
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

import disk_cache
from validator_common import BaseValidator, run_validator_main, strip_comments

# --- Module-level compiled patterns ---
# Hoisted from per-line/per-file loops in the tech-graph and history-file
# parsers below, so repeated parsing of large history/tech directories
# doesn't recompile the same regex on every line.

_TECHNOLOGIES_BLOCK_RE = re.compile(r"^technologies\s*=\s*\{")
_TECH_DEF_RE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\{")
_LEADS_TO_TECH_RE = re.compile(r"leads_to_tech\s*=\s*(\S+)")
_MODULE_NAME_RE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*$")
_ENABLE_MODULES_RE = re.compile(r"^enable_equipment_modules\s*=\s*\{")
_ALLOW_BRANCH_RE = re.compile(r"^allow_branch\s*=\s*\{")
# Reused with .match() on already-left-stripped lines, so the leading ^
# behaves identically whether or not it's spelled out in the source pattern.
_SET_TECHNOLOGY_BLOCK_RE = re.compile(r"^set_technology\s*=\s*\{")
_IF_BLOCK_LINE_RE = re.compile(r"^if\s*=\s*\{")
_SET_TECH_1_RE = re.compile(r"\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*1\s*$")
_ELSE_BLOCK_RE = re.compile(r"else\s*=\s*\{")
_HAS_DLC_RE = re.compile(r'has_dlc\s*=\s*"([^"]+)"')
_NOT_HAS_DLC_BLOCK_RE = re.compile(
    r'NOT\s*=\s*\{[^{}]*?has_dlc\s*=\s*"([^"]+)"[^{}]*?\}'
)
_STRIP_NOT_BLOCK_RE = re.compile(r"NOT\s*=\s*\{[^{}]*?\}")
_NOT_HAS_DLC_PREFIX_RE = re.compile(r'NOT\s*=\s*\{[^}]*has_dlc\s*=\s*"([^"]+)"')
_LIMIT_BLOCK_RE = re.compile(r"limit\s*=\s*\{(.*?)\}", re.DOTALL)
_LIMIT_BLOCK_WORDBOUND_RE = re.compile(r"\blimit\s*=\s*\{(.*?)\}", re.DOTALL)
_IF_BLOCK_START_RE = re.compile(r"\bif\s*=\s*\{")
_CREATE_VARIANT_RE = re.compile(r"\bcreate_equipment_variant\s*=\s*\{")
_VARIANT_NAME_RE = re.compile(r'name\s*=\s*"([^"]*)"')
_MODULES_BLOCK_RE = re.compile(r"\bmodules\s*=\s*\{")
_MODULE_ENTRY_RE = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*([a-zA-Z_][a-zA-Z0-9_]*)")
_STATE_OWNER_RE = re.compile(r"^\s*owner\s*=\s*(\S+)")
_OOB_REF_RE = re.compile(r'(oob|set_oob|set_air_oob|set_naval_oob)\s*=\s*"([^"]+)"')
_CAPITAL_RE = re.compile(r"^capital\s*=\s*\d+", re.MULTILINE)
# `complete_special_project = sp:sp_X` lines grant a country the special project
# at game start. Used to detect techs whose `allow` block requires an SP the
# country has not completed.
_COMPLETE_SP_RE = re.compile(r"^\s*complete_special_project\s*=\s*sp:([a-zA-Z0-9_]+)")
# `is_special_project_completed = sp:sp_X` inside a tech's `allow` block.
_SP_REQUIRED_RE = re.compile(r"is_special_project_completed\s*=\s*sp:([a-zA-Z0-9_]+)")


def parse_tech_dependencies(mod_path: str) -> Tuple[Dict, Set, Dict, Dict]:
    """Build the tech prerequisite graph, the module -> enabling-tech map, and
    the per-tech DLC gating map.

    A tech B has prerequisite A if A contains `path = { leads_to_tech = B }`.
    Multiple techs can lead to the same tech; any one satisfies the prerequisite.

    A module M is enabled by tech A if A contains M inside an
    `enable_equipment_modules = { ... }` block. Multiple techs can enable the
    same module; any one satisfies the requirement.

    A tech A is DLC-gated if it contains an `allow_branch = { ... }` block with
    a `has_dlc` condition. `has_dlc = "X"` requires DLC X; `NOT = { has_dlc =
    "X" }` forbids it. The gating is collected as (kind, dlc) pairs so history
    files that grant A in a contradicting DLC branch can be flagged.
    """
    tech_dir = os.path.join(mod_path, "common", "technologies")
    prerequisites = defaultdict(set)  # tech -> set of techs that lead to it
    all_techs = set()
    module_techs = defaultdict(set)  # module -> set of techs that enable it
    tech_dlc_reqs = defaultdict(list)  # tech -> [(kind, dlc), ...]

    for filepath in glob.iglob(os.path.join(tech_dir, "*.txt")):
        try:
            with open(filepath, "r", encoding="utf-8-sig") as f:
                content = f.read()
        except Exception:
            continue

        content = strip_comments(content)
        _parse_tech_file(content, prerequisites, all_techs, module_techs, tech_dlc_reqs)

    return prerequisites, all_techs, module_techs, tech_dlc_reqs


def propagate_dlc_reqs(
    prerequisites: Dict[str, Set[str]],
    tech_dlc_reqs: Dict[str, List[Tuple[str, str]]],
) -> Dict[str, List[Tuple[str, str]]]:
    """Propagate DLC gating along the prerequisite graph.

    A tech inherits a (kind, dlc) constraint when every one of its prerequisite
    techs carries it: if all paths to a tech run through techs forbidden under
    DLC X, the tech itself cannot legitimately exist under X (and likewise for
    `require`). This extends a base-tech gate (e.g. SP_arty_0 forbidden under No
    Step Back) to its whole upgrade chain (SP_arty_1..4, Arty_upgrade_*), so
    granting any tier of the legacy or NSB line in a contradicting branch is
    caught, not just the root.
    """
    constraints = defaultdict(set)  # (kind, dlc) -> seed techs
    for tech, pairs in tech_dlc_reqs.items():
        for kind, dlc in pairs:
            constraints[(kind, dlc)].add(tech)

    propagated = defaultdict(set)  # tech -> {(kind, dlc), ...}
    for (kind, dlc), seed in constraints.items():
        gated = set(seed)
        changed = True
        while changed:
            changed = False
            for tech, prereqs in prerequisites.items():
                if tech in gated or not prereqs:
                    continue
                if all(p in gated for p in prereqs):
                    gated.add(tech)
                    changed = True
        for tech in gated:
            propagated[tech].add((kind, dlc))

    return {tech: sorted(pairs) for tech, pairs in propagated.items()}


def _extract_dlc_conditions(text: str) -> List[Tuple[str, str]]:
    """Extract (kind, dlc) gating pairs from an `allow_branch` block body.

    `NOT = { has_dlc = "X" }` yields ("forbid", "X"); a bare `has_dlc = "X"`
    yields ("require", "X"). Non-DLC triggers (dates, flags) are ignored.
    """
    reqs: List[Tuple[str, str]] = []
    for m in _NOT_HAS_DLC_BLOCK_RE.finditer(text):
        reqs.append(("forbid", m.group(1)))
    no_not = _STRIP_NOT_BLOCK_RE.sub("", text)
    for m in _HAS_DLC_RE.finditer(no_not):
        reqs.append(("require", m.group(1)))
    return reqs


def parse_tech_sp_requirements(mod_path: str) -> Dict[str, Set[str]]:
    """Build the tech -> required-SP map from technology files.

    For each tech defined under `technologies = { ... }`, walk the tech block
    and collect every `is_special_project_completed = sp:sp_X` mention. A tech
    may require multiple SPs (joined by AND in the `allow` block); the returned
    set is the full list, and the history check requires all of them to be
    completed by the country.

    The outer `technologies = { ... }` wrapper is skipped so the literal
    `technologies` key is not itself treated as a tech definition. Nested
    sub-blocks (`allow = { ... }`, `ROOT = { ... }`) are excluded by tracking
    brace depth and only registering tech opens at depth 0 relative to the
    outer wrapper.
    """
    tech_dir = os.path.join(mod_path, "common", "technologies")
    sp_reqs: Dict[str, Set[str]] = defaultdict(set)

    for filepath in glob.iglob(os.path.join(tech_dir, "*.txt")):
        try:
            with open(filepath, "r", encoding="utf-8-sig") as f:
                content = f.read()
        except Exception:
            continue

        content = strip_comments(content)
        outer = re.search(r"^technologies\s*=\s*\{", content, re.MULTILINE)
        if not outer:
            continue
        # Brace-match the outer wrapper so we scan only its body.
        depth = 1
        j = outer.end()
        while j < len(content) and depth > 0:
            ch = content[j]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
            j += 1
        inner = content[outer.end() : j - 1]

        # Walk inner character by character, only treating `name = {` as a
        # tech open when we are at the outer depth (1). Anything nested
        # (allow, ROOT, paths, categories) is left alone.
        outer_depth = 1
        cur_depth = 1
        i = 0
        while i < len(inner):
            ch = inner[i]
            if ch == "{":
                cur_depth += 1
                i += 1
                continue
            if ch == "}":
                cur_depth -= 1
                i += 1
                continue
            if ch not in (" ", "\t", "\n"):
                # Look for `name = {` at the current line start.
                line_end = inner.find("\n", i)
                if line_end < 0:
                    line_end = len(inner)
                line = inner[i:line_end]
                m = re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*\{", line)
                if m and cur_depth == outer_depth:
                    tech = line.split("=", 1)[0].strip()
                    if tech != "technologies":
                        # Brace-match this tech block.
                        block_depth = 1
                        k = i + m.end()
                        block_start = i
                        while k < len(inner) and block_depth > 0:
                            c = inner[k]
                            if c == "{":
                                block_depth += 1
                            elif c == "}":
                                block_depth -= 1
                            k += 1
                        block = inner[block_start:k]
                        for spm in _SP_REQUIRED_RE.finditer(block):
                            sp_reqs[tech].add(spm.group(1))
                        # Resume scanning after this block; depth already
                        # closed back to outer_depth.
                        i = k
                        continue
                i = line_end + 1 if line_end < len(inner) else len(inner)
                continue
            i += 1

    return dict(sp_reqs)


def parse_sp_allowed_dlc(mod_path: str) -> Dict[str, str]:
    """Map each special project to the DLC its `allowed` block requires, if any.

    A project gated on `allowed = { has_dlc = "X" }` does not exist without DLC
    X, so a tech requiring it is not actually locked when X is absent (the whole
    subsystem is off). Projects with a generic `allowed` (always yes, a tag
    check, or none) are not in the returned map. Used to suppress false
    positives in the SP-completion check for configurations lacking the DLC.
    """
    projects_dir = os.path.join(mod_path, "common", "special_projects", "projects")
    allowed_dlc: Dict[str, str] = {}

    for filepath in glob.iglob(os.path.join(projects_dir, "*.txt")):
        try:
            with open(filepath, "r", encoding="utf-8-sig") as f:
                content = f.read()
        except Exception:
            continue

        content = strip_comments(content)
        for m in re.finditer(r"(?m)^([a-zA-Z0-9_]+)\s*=\s*\{", content):
            name = m.group(1)
            end = _match_brace_end(content, m.end())
            block = content[m.end() : end]
            allowed = re.search(r"allowed\s*=\s*\{", block)
            if not allowed:
                continue
            # Brace-match the allowed block so a has_dlc nested inside (e.g. in
            # an OR) is still seen; a flat `[^{}]*` capture would miss it.
            allowed_end = _match_brace_end(block, allowed.end())
            dlc = _HAS_DLC_RE.search(block[allowed.end() : allowed_end])
            if dlc:
                allowed_dlc[name] = dlc.group(1)

    return allowed_dlc


def _parse_tech_file(
    content: str,
    prerequisites: Dict[str, Set[str]],
    all_techs: Set[str],
    module_techs: Optional[Dict[str, Set[str]]] = None,
    tech_dlc_reqs: Optional[Dict[str, List[Tuple[str, str]]]] = None,
):
    """Parse a single tech file to extract tech definitions, their paths, the
    modules each tech enables, and the DLC each tech is gated on."""
    lines = content.split("\n")
    i = 0
    brace_depth = 0
    in_technologies_block = False
    current_tech = None
    tech_brace_depth = 0
    in_enable = False
    enable_brace_depth = 0
    in_allow = False
    allow_brace_depth = 0
    allow_buf: List[str] = []

    while i < len(lines):
        line = lines[i].strip()

        if not in_technologies_block:
            if _TECHNOLOGIES_BLOCK_RE.match(line):
                in_technologies_block = True
                brace_depth = 1
                i += 1
                continue
            i += 1
            continue

        for ch in line:
            if ch == "{":
                brace_depth += 1
            elif ch == "}":
                brace_depth -= 1

        if brace_depth <= 0:
            break

        # At depth 1: tech definitions. Variable assignments like @1965 = 0
        # are filtered out by requiring a `= {` block opener at depth >= 2.
        if current_tech is None:
            match = _TECH_DEF_RE.match(line)
            if match and brace_depth >= 2:
                current_tech = match.group(1)
                tech_brace_depth = brace_depth
                all_techs.add(current_tech)
        else:
            leads_match = _LEADS_TO_TECH_RE.match(line)
            if leads_match:
                target = leads_match.group(1)
                prerequisites[target].add(current_tech)

            if module_techs is not None:
                if in_enable:
                    if brace_depth >= enable_brace_depth:
                        mod_match = _MODULE_NAME_RE.match(line.strip())
                        if mod_match:
                            module_techs[mod_match.group(1)].add(current_tech)
                    if brace_depth < enable_brace_depth:
                        in_enable = False
                if not in_enable and _ENABLE_MODULES_RE.match(line):
                    in_enable = True
                    enable_brace_depth = brace_depth

            if tech_dlc_reqs is not None:
                if in_allow:
                    allow_buf.append(line)
                    if brace_depth < allow_brace_depth:
                        in_allow = False
                        for kind, dlc in _extract_dlc_conditions("\n".join(allow_buf)):
                            tech_dlc_reqs[current_tech].append((kind, dlc))
                        allow_buf = []
                if not in_allow and _ALLOW_BRANCH_RE.match(line):
                    in_allow = True
                    allow_brace_depth = brace_depth
                    allow_buf = [line]

            if brace_depth < tech_brace_depth:
                current_tech = None
                in_enable = False
                in_allow = False
                allow_buf = []

        i += 1


def _parse_history_text(
    content: str,
) -> List[Tuple[Set[str], Set[str], str]]:
    """Parse comment-stripped history text into one (tech_set, sp_set, label)
    tuple per DLC configuration.

    Each `set_technology` tech and each `complete_special_project` SP is tagged
    with the DLC guard of its enclosing `if`/`else` blocks (which DLCs must be
    present or absent), then the guards are expanded into a tuple per DLC
    configuration. A real brace stack tracks nesting, so a nested `else` inside
    a large `if` body no longer flips a tech or SP into the wrong branch.
    """
    techs, sps, dlcs = _walk_history_tokens(_tokenize_history(content))
    return _expand_dlc_configs(techs, sps, dlcs)


def parse_history_file(
    filepath: str, mod_path: str
) -> List[Tuple[Set[str], Set[str], str]]:
    """Parse a history file and return tech sets, SP completion sets, and their
    context.

    Returns a list of (tech_set, sp_set, context_label) where context_label
    describes the DLC branch (for error reporting).

    Each returned (tech_set, sp_set) pair represents one possible effective
    (techs, completed-SP) state a country could have, depending on which DLCs
    are active. The branch's tech and SP sets grow together: an SP completed
    inside an `if` block is present only when the matching DLC is active.
    """
    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            content = f.read()
    except Exception:
        return []

    content = strip_comments(content)
    return disk_cache.per_file_cached_by_content(
        mod_path,
        "history_techs.history_parse_v5",
        filepath,
        content,
        lambda: _parse_history_text(content),
    )


# --- History-file brace-aware DLC-guard parser ------------------------------
# Splits into `{`, `}`, `=`, quoted strings, and everything else. Comments are
# already stripped before this runs.
_HISTORY_TOKEN_RE = re.compile(r'"[^"]*"|[{}=]|[^\s{}=]+')
_SP_VALUE_RE = re.compile(r"^sp:([a-zA-Z0-9_]+)$")
_INT_VALUE_RE = re.compile(r"^\d+$")

# A DLC guard maps each constraining DLC to whether it must be present (True) or
# absent (False) for the tagged tech/SP to apply.
Guard = Dict[str, bool]


def _tokenize_history(content: str) -> List[str]:
    return _HISTORY_TOKEN_RE.findall(content)


def _walk_history_tokens(
    tokens: List[str],
) -> Tuple[List[Tuple[str, Guard]], List[Tuple[str, Guard]], Set[str]]:
    """Walk the token stream with a real brace stack.

    Returns (techs, sps, dlcs). `techs` and `sps` are lists of (name, guard);
    `dlcs` is the set of DLC names that appear in any guard.

    Each frame carries a list of DLC constraints. An `if` frame learns its
    constraints from its `limit`'s `has_dlc`. In HOI4 an `else` is nested
    *inside* the `if` block, so it takes the negation of its enclosing `if`'s
    constraints; because the enclosing `if` frame is still on the stack, deeper
    frames override shallower ones for the same DLC when the guard is resolved.
    """
    root = {"name": None, "conds": []}
    stack = [root]
    techs: List[Tuple[str, Guard]] = []
    sps: List[Tuple[str, Guard]] = []

    def current_guard() -> Guard:
        guard: Guard = {}
        for fr in stack:
            for dlc, present in fr["conds"]:
                guard[dlc] = present  # deeper frames (e.g. else) override
        return guard

    i, n = 0, len(tokens)
    while i < n:
        t = tokens[i]

        if t == "}":
            if len(stack) > 1:
                stack.pop()
            i += 1
            continue

        if t == "{":
            stack.append({"name": None, "conds": []})
            i += 1
            continue

        if i + 1 < n and tokens[i + 1] == "=":
            key = t
            after = tokens[i + 2] if i + 2 < n else None
            if after == "{":
                frame = {"name": key, "conds": []}
                if key in ("else", "else_if"):
                    frame["conds"] = [
                        (dlc, not present) for dlc, present in stack[-1]["conds"]
                    ]
                stack.append(frame)
                i += 3
                continue
            _handle_history_assignment(stack, key, after, techs, sps, current_guard)
            i += 3
            continue

        i += 1

    # Only DLCs that actually gate a tech or SP become configuration axes; a
    # DLC that appears solely in a non-tech `if` (e.g. an intelligence-agency
    # block) must not turn base-level techs into DLC-branch content.
    dlcs = {dlc for _, guard in techs for dlc in guard}
    dlcs |= {dlc for _, guard in sps for dlc in guard}
    return techs, sps, dlcs


def _handle_history_assignment(stack, key, value, techs, sps, current_guard):
    """Record a tech, SP completion, or DLC condition from a `key = value`."""
    if value is None:
        return

    if key == "has_dlc":
        dlc = value.strip('"')
        # An odd number of enclosing NOT blocks flips the sense of the gate.
        negated = sum(1 for fr in stack if fr["name"] == "NOT") % 2 == 1
        for fr in reversed(stack):
            if fr["name"] in ("if", "else_if"):
                fr["conds"].append((dlc, not negated))
                break
        return

    if key == "complete_special_project":
        m = _SP_VALUE_RE.match(value)
        if m:
            sps.append((m.group(1), current_guard()))
        return

    if stack[-1]["name"] == "set_technology" and _INT_VALUE_RE.match(value):
        techs.append((key, current_guard()))


def _guard_satisfied(guard: Guard, config: Dict[str, bool]) -> bool:
    return all(config.get(dlc) == present for dlc, present in guard.items())


def _expand_dlc_configs(
    techs: List[Tuple[str, Guard]],
    sps: List[Tuple[str, Guard]],
    dlcs: Set[str],
) -> List[Tuple[Set[str], Set[str], str]]:
    """Expand guard-tagged techs/SPs into one (tech_set, sp_set, label) per DLC
    configuration. With no DLC-gated content there is a single `unconditional`
    configuration holding every tech and SP."""
    dlc_list = sorted(dlcs)
    results: List[Tuple[Set[str], Set[str], str]] = []
    for bits in range(1 << len(dlc_list)):
        config = {dlc: bool(bits & (1 << k)) for k, dlc in enumerate(dlc_list)}
        tech_set = {name for name, g in techs if _guard_satisfied(g, config)}
        sp_set = {name for name, g in sps if _guard_satisfied(g, config)}
        label = (
            " + ".join(dlc if config[dlc] else f"NOT {dlc}" for dlc in dlc_list)
            or "unconditional"
        )
        results.append((tech_set, sp_set, label))
    return results


def _match_brace_end(text: str, pos: int) -> int:
    """Given pos pointing just past an opening `{`, return the index just past
    its matching `}`. Returns len(text) if the braces never balance."""
    depth = 1
    j = pos
    while j < len(text) and depth > 0:
        ch = text[j]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        j += 1
    return j


def _find_dlc_if_blocks(content: str) -> List[Tuple[int, int, str]]:
    """Return (start, end, dlc_name) for every positive `has_dlc` if-block.

    `start`/`end` bracket the whole `if = { ... }` span. Only the if-block's
    own `limit` is inspected, so a nested DLC if does not mistag its parent,
    and negated (`NOT = { has_dlc }`) gates are skipped.
    """
    blocks = []
    for m in _IF_BLOCK_START_RE.finditer(content):
        end = _match_brace_end(content, m.end())
        inner = content[m.end() : end - 1]
        limit = _LIMIT_BLOCK_WORDBOUND_RE.search(inner)
        if not limit:
            continue
        region = limit.group(1)
        if "NOT" in region:
            continue
        dlc = _HAS_DLC_RE.search(region)
        if dlc:
            blocks.append((m.start(), end, dlc.group(1)))
    return blocks


def _parse_variants_text(content: str) -> List[Tuple[str, Set[str], frozenset]]:
    """Parse comment-stripped history text into create_equipment_variant triples."""
    dlc_blocks = _find_dlc_if_blocks(content)

    variants = []
    for m in _CREATE_VARIANT_RE.finditer(content):
        start = m.start()
        end = _match_brace_end(content, m.end())
        block = content[m.end() : end - 1]

        name_match = _VARIANT_NAME_RE.search(block)
        name = name_match.group(1) if name_match else "?"

        modules = set()
        mod_block = _MODULES_BLOCK_RE.search(block)
        if mod_block:
            mod_end = _match_brace_end(block, mod_block.end())
            mod_inner = block[mod_block.end() : mod_end - 1]
            for entry in _MODULE_ENTRY_RE.finditer(mod_inner):
                if entry.group(1) != "empty":
                    modules.add(entry.group(1))

        gating = frozenset(dlc for (s, e, dlc) in dlc_blocks if s <= start < e)
        variants.append((name, modules, gating))

    return variants


def parse_equipment_variants(
    filepath: str, mod_path: str
) -> List[Tuple[str, Set[str], frozenset]]:
    """Parse a history file and return every create_equipment_variant as a
    (variant_name, set_of_module_names, dlc_gating) triple.

    Only the modules listed inside the variant's `modules = { ... }` sub-block
    are collected; `upgrades` and other sub-blocks are ignored. The literal
    value `empty` (an unfilled slot) is skipped. Both single-line and
    multi-line `modules` blocks are handled.

    `dlc_gating` is the set of `has_dlc` conditions whose if-block encloses the
    variant — i.e. the DLCs that must be active for the variant to exist.
    """
    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            content = f.read()
    except Exception:
        return []

    content = strip_comments(content)
    return disk_cache.per_file_cached_by_content(
        mod_path,
        "history_techs.variant_parse",
        filepath,
        content,
        lambda: _parse_variants_text(content),
    )


def validate_country_equipment(
    args: Tuple[str, Dict[str, Set[str]], str],
) -> List[str]:
    """Validate that a country's equipment variants only use modules enabled by
    a technology the country has in any DLC branch. Returns error strings.

    DLC branches (NSB, BBA, etc.) contain interwoven content: an NSB-gated
    helicopter variant may use modules whose enabling tech is granted in the
    BBA block. Both DLCs are active simultaneously in normal play, and
    create_equipment_variant bypasses module tech checks anyway, so we
    accept any tech from any branch.
    """
    filepath, module_techs, mod_path = args
    filename = os.path.basename(filepath)

    # Union of techs across all DLC branches — if any branch grants a module's
    # enabling tech, the country can use the module.
    have: Set[str] = set()
    for tech_set, _sps, _ctx in parse_history_file(filepath, mod_path):
        have |= tech_set

    results = []
    seen = set()
    for name, modules, _gating in parse_equipment_variants(filepath, mod_path):
        for module in sorted(modules):
            enabling = module_techs.get(module)
            if not enabling:
                continue  # module needs no tech (always available)
            if enabling & have:
                continue  # at least one enabling tech is guaranteed
            key = (name, module)
            if key in seen:
                continue
            seen.add(key)
            techs = sorted(enabling)
            if len(techs) == 1:
                tech_str = techs[0]
            else:
                tech_str = "one of: " + ", ".join(techs)
            results.append(
                f'{filename}: variant "{name}" uses {module} '
                f"without enabling tech {tech_str}"
            )

    return results


def _context_dlcs(label: str) -> Tuple[Set[str], Set[str]]:
    """Split a tech-set context label into (present_dlcs, absent_dlcs).

    Labels are conjunctions built by `_expand_dlc_configs`, e.g.
    `No Step Back + NOT By Blood Alone`. A bare term means the DLC is present in
    that branch; a `NOT ` prefix means it is absent.
    """
    present: Set[str] = set()
    absent: Set[str] = set()
    if label and label != "unconditional":
        for term in label.split(" + "):
            term = term.strip()
            if not term or term == "unconditional":
                continue
            if term.startswith("NOT "):
                absent.add(term[4:])
            else:
                present.add(term)
    return present, absent


def validate_country_dlc_techs(
    args: Tuple[str, Dict[str, List[Tuple[str, str]]], str],
) -> List[str]:
    """Validate that a country never gets a DLC-gated tech in a DLC branch that
    contradicts the tech's `allow_branch`. Returns error strings.

    A tech gated `NOT has_dlc = "X"` (the non-DLC fallback, e.g. SP_arty_0) must
    not be set in any reachable DLC configuration where X is active; a tech
    gated `has_dlc = "X"` (a DLC-only tech, e.g. nsb_artillery_0) must not be
    set where X is inactive. Granting it anyway force-enables equipment whose
    tech branch is disabled, duplicating the active-DLC designer's equipment.

    Only flagged when the history file itself branches on the conflicting DLC,
    so its presence/absence in a given context is known.
    """
    filepath, tech_dlc_reqs, mod_path = args
    filename = os.path.basename(filepath)

    tech_sets = parse_history_file(filepath, mod_path)

    error_contexts = defaultdict(list)  # (tech, kind, dlc) -> [context, ...]
    for tech_set, _sps, context in tech_sets:
        present, absent = _context_dlcs(context)
        for tech in sorted(tech_set):
            for kind, dlc in tech_dlc_reqs.get(tech, ()):
                if kind == "forbid" and dlc in present:
                    error_contexts[(tech, kind, dlc)].append(context)
                elif kind == "require" and dlc in absent:
                    error_contexts[(tech, kind, dlc)].append(context)

    results = []
    for (tech, kind, dlc), contexts in sorted(error_contexts.items()):
        if kind == "forbid":
            results.append(
                f'{filename}: {tech} is granted while "{dlc}" is active, but its '
                f"tech branch requires that DLC be absent [{contexts[0]}]"
            )
        else:
            results.append(
                f'{filename}: {tech} is granted while "{dlc}" is inactive, but its '
                f"tech branch requires that DLC [{contexts[0]}]"
            )

    return results


def validate_country_sp_requirements(
    args: Tuple[str, Dict[str, Set[str]], Dict[str, str], str],
) -> List[str]:
    """Validate that a country completes every special project required by the
    techs in its `set_technology` block, in every DLC configuration where it
    starts with the tech. Returns error strings.

    A tech with an `allow = { is_special_project_completed = sp:sp_X }` block
    can only be researched after the matching special project is finished. A
    country that starts with the tech but never completed the project has to
    research the project before it can advance that branch, and its
    project-gated equipment stays locked. This most often bites when a *generic*
    project (available regardless of DLC) is completed only inside a DLC `if`
    block: a player without that DLC still gets the tech but not the project.

    A project whose own `allowed` block is limited to a DLC does not exist
    without that DLC, so in a configuration lacking it the whole subsystem is
    off and the requirement is moot — those are skipped via `sp_allowed_dlc`.

    Only the SPs the country itself completes via
    `complete_special_project = sp:sp_X` in the same history file count. SPs
    granted at runtime by scripted effects, focus trees, or operations are out
    of scope for this check.
    """
    filepath, tech_sp_reqs, sp_allowed_dlc, mod_path = args
    filename = os.path.basename(filepath)

    # (tech, sorted missing SPs) -> list of (present_dlcs, absent_dlcs) for each
    # configuration where the gap appears, used to derive a concise condition.
    gaps: Dict[Tuple[str, Tuple[str, ...]], List[Tuple[Set[str], Set[str]]]] = (
        defaultdict(list)
    )
    for tech_set, sp_set, context in parse_history_file(filepath, mod_path):
        present, absent = _context_dlcs(context)
        for tech in sorted(tech_set):
            required = tech_sp_reqs.get(tech)
            if not required:
                continue
            missing = set()
            for sp in required:
                if sp in sp_set:
                    continue
                gate = sp_allowed_dlc.get(sp)
                # DLC-limited project that cannot exist in this configuration:
                # the subsystem is off, so the tech is not actually locked.
                if gate is not None and gate in absent:
                    continue
                missing.add(sp)
            if missing:
                gaps[(tech, tuple(sorted(missing)))].append((present, absent))

    results = []
    for (tech, missing_sps), configs in sorted(gaps.items()):
        # Condition shared by every configuration where the gap appears.
        common_present = set.intersection(*[p for p, _ in configs])
        common_absent = set.intersection(*[a for _, a in configs])
        terms = sorted(common_present) + [f"NOT {d}" for d in sorted(common_absent)]
        label = " + ".join(terms) if terms else "any DLC configuration"
        sps_str = ", ".join(f"sp:{sp}" for sp in missing_sps)
        if len(missing_sps) == 1:
            results.append(
                f"{filename}: {tech} requires special project {sps_str} "
                f"but it is not completed at game start [{label}]"
            )
        else:
            results.append(
                f"{filename}: {tech} requires special projects {sps_str} "
                f"but they are not completed at game start [{label}]"
            )

    return results


def _get_state_owners(mod_path: str) -> Set[str]:
    """Parse history/states/ files to find which tags own states at game start.

    Returns a set of tag strings (e.g. {'USA', 'FRA', ...}).
    """
    owners = set()
    states_dir = os.path.join(mod_path, "history", "states")
    for f in glob.iglob(os.path.join(states_dir, "*.txt")):
        try:
            with open(f, "r", encoding="utf-8-sig") as fh:
                for line in fh:
                    m = _STATE_OWNER_RE.match(line)
                    if m:
                        owners.add(m.group(1))
        except Exception:
            continue
    return owners


def _get_oob_refs(filepath: str) -> List[Tuple[str, int, str]]:
    """Extract (oob_name, line_number, ref_type) from a history file.

    Returns all non-commented OOB references: oob, set_oob, set_air_oob,
    set_naval_oob. ref_type is the HOI4 key used (e.g. 'oob', 'set_oob').
    """
    refs = []
    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            lines = f.readlines()
    except Exception:
        return refs

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        # Skip comments
        if stripped.startswith("#"):
            continue
        # Match oob = "...", set_oob = "...", set_air_oob = "...", set_naval_oob = "..."
        m = _OOB_REF_RE.match(stripped)
        if m:
            refs.append((m.group(2), i, m.group(1)))

    return refs


def validate_oob_references(
    args: Tuple[str, Set[str], Set[str]],
) -> List[str]:
    """Validate that a history file for a state-owning nation has a land OOB.

    Nations that own states at game start MUST have at least one land OOB
    reference (oob or set_oob) that loads on game start, otherwise they will
    have no division templates and be unplayable until save/reload.

    Returns error strings for any state-owning nation missing a land OOB or
    referencing an OOB file that does not exist.
    """
    filepath, existing_oobs, state_owners = args
    filename = os.path.basename(filepath)

    # Extract the tag from the filename (e.g. "USA - USA.txt" -> "USA")
    tag = filename.split(" - ")[0] if " - " in filename else filename[:-4]

    if tag not in state_owners:
        return []

    refs = _get_oob_refs(filepath)
    has_land_oob = any(ref_type in ("oob", "set_oob") for _, _, ref_type in refs)

    if not has_land_oob:
        return [
            f"{filename}: {tag} owns states at game start but has no land OOB (oob/set_oob) - nation will be unplayable until save/reload"
        ]

    return [
        f'{filename}:{line_num} - {ref_type} references "{oob_name}" '
        f"but no history/units/{oob_name}.txt file exists"
        for oob_name, line_num, ref_type in refs
        if ref_type in ("oob", "set_oob") and oob_name not in existing_oobs
    ]


def validate_capital_defined(filepath: str) -> List[str]:
    """Check that a history file has a capital defined.

    Returns an error string if no `capital = N` line is found.
    """
    filename = os.path.basename(filepath)
    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            content = f.read()
    except Exception:
        return [f"{filename}: could not read file"]

    if not _CAPITAL_RE.search(content):
        return [f"{filename}: no capital defined"]
    return []


def validate_country_file(
    args: Tuple[str, Dict[str, Set[str]], Set[str], str],
) -> List[str]:
    """Validate a single country history file. Returns list of error strings."""
    filepath, prerequisites, all_techs, mod_path = args
    filename = os.path.basename(filepath)

    tech_sets = parse_history_file(filepath, mod_path)
    total_sets = len(tech_sets)

    # Track which (tech, prereq_str) errors appear in which contexts
    error_contexts = defaultdict(list)  # (tech, prereq_str) -> [context, ...]

    for tech_set, _sps, context in tech_sets:
        for tech in sorted(tech_set):
            if tech not in all_techs:
                continue  # Unknown tech, skip (could be from a DLC we don't parse)

            if tech not in prerequisites:
                continue  # Root tech, no prerequisites needed

            prereqs = prerequisites[tech]
            if not any(p in tech_set for p in prereqs):
                missing_prereqs = sorted(prereqs)
                if len(missing_prereqs) == 1:
                    prereq_str = missing_prereqs[0]
                else:
                    prereq_str = "one of: " + ", ".join(missing_prereqs)
                error_contexts[(tech, prereq_str)].append(context)

    # An error present in every DLC combination is a base-tech issue, so report
    # it without a context tag; otherwise tag it with the first context it hit.
    results = []
    for (tech, prereq_str), contexts in sorted(error_contexts.items()):
        if len(contexts) >= total_sets:
            results.append(f"{filename}: {tech} requires {prereq_str}")
        else:
            results.append(f"{filename}: {tech} requires {prereq_str} [{contexts[0]}]")

    return results


class Validator(BaseValidator):
    TITLE = "HISTORY FILE VALIDATION"
    STAGED_EXTENSIONS = [".txt"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prerequisites = {}
        self.all_techs = set()
        self.module_techs = {}
        self.tech_dlc_reqs = {}
        self.tech_sp_reqs = {}
        self.sp_allowed_dlc = {}

    def _build_tech_graph(self):
        """Build the technology dependency graph from tech definition files."""
        self._log_section("Building technology dependency graph...")

        (
            self.prerequisites,
            self.all_techs,
            self.module_techs,
            direct_dlc_reqs,
        ) = parse_tech_dependencies(self.mod_path)

        # Extend each base-tech DLC gate to its whole upgrade chain.
        self.tech_dlc_reqs = propagate_dlc_reqs(self.prerequisites, direct_dlc_reqs)

        # Map each tech to the special projects its `allow` block requires, and
        # each special project to the DLC its own `allowed` block requires.
        self.tech_sp_reqs = parse_tech_sp_requirements(self.mod_path)
        self.sp_allowed_dlc = parse_sp_allowed_dlc(self.mod_path)

        techs_with_prereqs = len(self.prerequisites)
        self.log(f"  Found {len(self.all_techs)} technology definitions")
        self.log(f"  Found {techs_with_prereqs} technologies with prerequisites")
        self.log(f"  Found {len(self.module_techs)} modules mapped to enabling techs")
        self.log(
            f"  Found {len(direct_dlc_reqs)} DLC-gated technologies "
            f"({len(self.tech_dlc_reqs)} incl. upgrade chains)"
        )
        self.log(
            f"  Found {len(self.tech_sp_reqs)} technologies requiring special projects"
        )

    def _get_history_files(self) -> List[str]:
        """Get list of history country files to validate."""
        history_dir = os.path.join(self.mod_path, "history", "countries")
        if self.staged_only:
            if not self.staged_files:
                return []
            return [
                f
                for f in self.staged_files
                if f.endswith(".txt") and "history/countries" in f.replace("\\", "/")
            ]
        return sorted(glob.iglob(os.path.join(history_dir, "*.txt")))

    def _validate_history_files(
        self,
        title: str,
        success_msg: str,
        error_header: str,
        args_list: List[Tuple],
        func,
        chunksize: int = 20,
    ):
        """Pool a per-file validator across all history files and report results."""
        self._log_section(title)
        self.log(f"  Found {len(args_list)} history files to check")
        all_results = self._pool_map(func, args_list, chunksize=chunksize)
        results = [r for file_results in all_results for r in file_results]
        self._report(results, success_msg, error_header)

    def validate_tech_dependencies(self):
        """Validate that all history files have correct tech prerequisites."""
        files = self._get_history_files()
        args_list = [
            (f, self.prerequisites, self.all_techs, self.mod_path) for f in files
        ]
        self._validate_history_files(
            "Checking technology dependencies in history files...",
            "✓ All history files have correct technology prerequisites",
            "History files with missing technology prerequisites:",
            args_list,
            validate_country_file,
        )

    def validate_equipment_modules(self):
        """Validate that equipment variants only use unlocked modules."""
        files = self._get_history_files()
        args_list = [(f, self.module_techs, self.mod_path) for f in files]
        self._validate_history_files(
            "Checking equipment variant module technologies...",
            "✓ All equipment variants use unlocked modules",
            "Equipment variants using modules without the enabling technology:",
            args_list,
            validate_country_equipment,
        )

    def validate_dlc_branch_techs(self):
        """Validate that history files never grant a DLC-gated tech in a branch
        that contradicts the tech's allow_branch DLC condition."""
        files = self._get_history_files()
        args_list = [(f, self.tech_dlc_reqs, self.mod_path) for f in files]
        self._validate_history_files(
            "Checking DLC-gated technologies in history files...",
            "✓ All history files grant DLC-gated technologies in compatible branches",
            "History files granting DLC-gated technologies in a contradicting DLC branch:",
            args_list,
            validate_country_dlc_techs,
        )

    def validate_sp_completions(self):
        """Validate that every tech whose `allow` block requires a special
        project is paired with a `complete_special_project` line in the same
        history-file branch."""
        files = self._get_history_files()
        args_list = [
            (f, self.tech_sp_reqs, self.sp_allowed_dlc, self.mod_path) for f in files
        ]
        self._validate_history_files(
            "Checking special project completions for SP-gated technologies...",
            "✓ All history files complete the special projects required by their techs",
            "History files granting SP-gated technologies without completing the special project:",
            args_list,
            validate_country_sp_requirements,
        )

    def validate_oob_references(self):
        """Validate that every state-owning nation has a land OOB on game start."""
        self._log_section("Checking OOB references in history files...")

        files = self._get_history_files()
        self.log(f"  Found {len(files)} history files to check")

        # Build the set of existing OOB files (basenames without extension)
        units_dir = os.path.join(self.mod_path, "history", "units")
        existing_oobs = {
            os.path.splitext(os.path.basename(f))[0]
            for f in glob.iglob(os.path.join(units_dir, "*.txt"))
        }
        self.log(f"  Found {len(existing_oobs)} OOB files in history/units/")

        # Build the set of tags that own states at game start
        state_owners = _get_state_owners(self.mod_path)
        self.log(f"  Found {len(state_owners)} tags that own states at game start")

        args_list = [(f, existing_oobs, state_owners) for f in files]
        all_results = self._pool_map(validate_oob_references, args_list, chunksize=50)
        results = [r for file_results in all_results for r in file_results]
        self._report(
            results,
            "✓ All state-owning nations have a land OOB on game start",
            "State-owning nations missing a land OOB (unplayable until save/reload):",
        )

    def validate_capital_defined(self):
        """Check that every history file has a capital defined."""
        self._log_section("Checking capital definitions in history files...")

        files = self._get_history_files()
        self.log(f"  Found {len(files)} history files to check")

        results = []
        for f in files:
            results.extend(validate_capital_defined(f))

        self._report(
            results,
            "✓ All history files have a capital defined",
            "History files missing a capital definition:",
        )

    def run_validations(self):
        self._build_tech_graph()
        self.validate_tech_dependencies()
        self.validate_equipment_modules()
        self.validate_dlc_branch_techs()
        self.validate_sp_completions()
        self.validate_oob_references()
        self.validate_capital_defined()


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate history files: technology dependencies, OOB references, capital definitions",
    )
