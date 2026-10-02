#!/usr/bin/env python3
"""Flag consecutive scope blocks that can be merged into one.

Two sibling blocks that open the *same deterministic scope* back to back, with
nothing but whitespace between them, can always be collapsed:

    USA = { add_stability = 0.05 }
    USA = { add_war_support = 0.05 }
    # -> USA = { add_stability = 0.05 add_war_support = 0.05 }

The same holds for state-id scopes (`123 = { } 123 = { }`), magic scopes
(`PREV`, `FROM`, `ROOT.CAPITAL`, ...), relation scopes (`owner`, `controller`,
`capital_scope`, ...) and variable scopes (`var:foo`, `event_target:bar`).

Only deterministic scopes are flagged. Random scopes (`random_country`,
`random_owned_state`, ...) pick a different target per block, iterators
(`every_*`, `any_*`) iterate a set, and control-flow blocks (`if`, `limit`,
`AND`, ...) are not scopes — merging any of those would change behaviour, so
they are never suggested.

Four more collapses are flagged on top of the same-scope merge:

  * two-bucket `random_list` with one empty bucket -> `random = { chance = N }`
  * runs of identical adjacent `create_unit` blocks -> one block + `count = N`
  * empty `visible` / `available` / `allowed` blocks -> delete (engine default)
  * `random_state` limited by `controller = { tag = X }` / `is_controlled_by = X`
    -> `random_controlled_state` (drop the controller check; keep other limits)

A second pass flags redundant owner scopes in focus and decision files
(_scan_focus_file / _scan_decision_file): a tree locked to one country via
`focus_tree = { country = { ... tag = X } }`, or a decision locked via its
own (or its enclosing category's) `allowed`, already runs every trigger and
effect in that country's scope, so `X = { ... }` wrappers splice into the
parent and bare `tag = X` / `original_tag = X` re-checks drop out. Only
strict (`tag = X`) ownership lifts scopes; `original_tag = X` gates admit
breakaways, so they only lose their always-true `original_tag` re-checks.
`joint_focus` blocks are never scanned (rewards fan out to every member).

Output is WARNING-only.
"""

import fnmatch
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# strip_comments is re-exported here so validate_simplifications_test can import it.
from shared_utils import extract_block_from_text, strip_comments  # noqa: F401
from validator_common import BaseValidator, Severity, run_validator_main

_SCAN_PATTERNS = [
    "common/national_focus/*.txt",
    "common/national_focus/**/*.txt",
    "common/decisions/*.txt",
    "common/decisions/**/*.txt",
    "common/scripted_effects/*.txt",
    "common/scripted_effects/**/*.txt",
    "common/scripted_triggers/*.txt",
    "common/scripted_triggers/**/*.txt",
    "common/on_actions/*.txt",
    "events/*.txt",
    "events/**/*.txt",
]

# The bare multi-child NOT check scans every trigger-bearing script file, not
# just the effect-heavy dirs above (history/ carries no bare multi-child NOTs).
_NOT_SCAN_PATTERNS = [
    "common/**/*.txt",
    "events/**/*.txt",
]

# Matches `HEADER = {`. The header charset covers tags, state ids, magic scopes,
# and variable/target scopes (var:x, event_target:y, global.event_target:z^0).
_OPEN_RE = re.compile(r"([\w.:^@\[\]-]+)\s*=\s*\{")

# Magic scopes that resolve to a single deterministic target. Dotted chains of
# these (PREV.PREV, ROOT.CAPITAL) are deterministic too.
_MAGIC = frozenset({"ROOT", "PREV", "FROM", "THIS", "OWNER", "CONTROLLER", "CAPITAL"})

# Lower-case relation scopes that resolve to a single deterministic target.
_RELATION_SCOPES = frozenset(
    {"owner", "controller", "capital_scope", "overlord", "faction_leader"}
)

# 3-letter all-caps tokens that are logical operators, not country tags.
_NOT_TAGS = frozenset({"AND", "NOT"})

# Parent blocks whose direct children are NOT a plain AND/sequential list, so
# merging two same-header children would change meaning:
#   OR             - operands are OR-ed; merging ANDs them
#   count_triggers - counts how many children are true
#   random_list    - numeric children are weight buckets, not state scopes
_NO_MERGE_PARENTS = frozenset({"OR", "count_triggers", "random_list"})

_TAG_RE = re.compile(r"^[A-Z]{3}$")
_VAR_SCOPE_RE = re.compile(r"^(var|event_target|global\.event_target):")

# Scope-expansion simplifications: a `TAG = { <single trigger> }` block whose
# body is one trigger that has a flat country-scoped equivalent. Opening a TAG
# scope just to check one boolean is an unnecessary scope switch (see AGENTS.md
# "Minimize scope expansion"). Only single-condition bodies are flagged; a flat
# form with NOT/relative scopes (e.g. exists = no) is context-dependent and left
# alone.
_TAG_BLOCK_RE = re.compile(r"\b([A-Z]{3})\s*=\s*\{")
_SINGLE_TRIGGER_RE = re.compile(r"^([a-z_]+)\s*=\s*(\w+)$")
_FLAT_EQUIV = {
    ("exists", "yes"): "country_exists = {tag}",
    ("is_puppet", "yes"): "is_puppet_of = {tag}",
}


def _effectively_empty(body: str) -> bool:
    """True when *body* contains only whitespace and line comments."""
    for line in body.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return False
    return True


def _find_scope_expansion(text: str):
    """Return (line, tag, flat_form) for each `TAG = { single trigger }` block
    that collapses to a flat country trigger."""
    results = []
    for m in _TAG_BLOCK_RE.finditer(text):
        tag = m.group(1)
        if tag in _NOT_TAGS:
            continue
        body, end = extract_block_from_text(text, m.end() - 1)
        if end == -1:
            continue
        sm = _SINGLE_TRIGGER_RE.match(body.strip())
        if not sm:
            continue
        flat = _FLAT_EQUIV.get((sm.group(1), sm.group(2)))
        if flat:
            line = text.count("\n", 0, m.start()) + 1
            results.append((line, tag, flat.format(tag=tag)))
    return results


# random_list with exactly two weight buckets where one is empty is a Bernoulli
# trial in the wrong syntax; it collapses to a single `random = { chance = N }`.
# Three+ buckets, or two non-empty buckets, must stay (see AGENTS.md).
_RANDOM_LIST_RE = re.compile(r"\brandom_list\s*=\s*\{")
_WEIGHT_RE = re.compile(r"^[0-9]+(?:\.[0-9]+)?$")
_MODIFIER_RE = re.compile(r"\bmodifier\s*=\s*\{")


def _find_two_bucket_random(text: str):
    """Return (line, chance) for each two-bucket random_list with one empty
    bucket, where chance is the probability the non-empty bucket fires.

    Buckets containing ``modifier = { }`` blocks are skipped — ``random = {}
    chance = N`` has no modifier support, so the conversion is not valid."""
    results = []
    for m in _RANDOM_LIST_RE.finditer(text):
        body, end = extract_block_from_text(text, m.end() - 1)
        if end == -1:
            continue
        buckets = []  # (weight, is_empty, has_modifier) for each direct-child bucket
        pos = 0
        malformed = False
        while pos < len(body):
            bm = _OPEN_RE.search(body, pos)
            if not bm:
                break
            bbody, bend = extract_block_from_text(body, bm.end() - 1)
            if bend == -1:
                malformed = True
                break
            if not _WEIGHT_RE.match(bm.group(1)):
                malformed = True  # non-weight child: not a plain bucket list
                break
            buckets.append(
                (
                    float(bm.group(1)),
                    _effectively_empty(bbody),
                    bool(_MODIFIER_RE.search(bbody)),
                )
            )
            pos = bend
        if malformed or len(buckets) != 2:
            continue
        empties = [w for w, e, _ in buckets if e]
        non_empty = [(w, has_mod) for w, e, has_mod in buckets if not e]
        if len(empties) != 1 or len(non_empty) != 1:
            continue
        if non_empty[0][1]:
            continue  # bucket has modifiers; random doesn't support them
        total = empties[0] + non_empty[0][0]
        if total <= 0:
            continue
        chance = round(100 * non_empty[0][0] / total)
        line = text.count("\n", 0, m.start()) + 1
        results.append((line, chance))
    return results


# Runs of byte-identical adjacent `create_unit` blocks collapse to one block
# with `count = N`. Only direct siblings (whitespace-only between them) are
# flagged: blocks each wrapped in their own `123 = { }` / `random_owned_state`
# scope are separated by braces, so they never match here — the state-id case is
# already covered by the same-scope merge detector, and merging random scopes
# would change the spawn target. Blocks that already carry their own `count` are
# skipped so the suggested total is never wrong.
_CREATE_UNIT_RE = re.compile(r"\bcreate_unit\s*=\s*\{")
_HAS_COUNT_RE = re.compile(r"\bcount\s*=")


def _find_count_collapsible(text: str):
    """Return (line, run_len) for each run of 2+ identical adjacent create_unit
    blocks that collapse into one block with `count = run_len`. *line* is the
    first block in the run."""
    results = []
    pos = 0
    run_start_line = None
    run_norm = None
    run_len = 0
    prev_end = None

    def flush():
        if run_len >= 2:
            results.append((run_start_line, run_len))

    while True:
        m = _CREATE_UNIT_RE.search(text, pos)
        if not m:
            break
        body, end = extract_block_from_text(text, m.end() - 1)
        if end == -1:
            break
        has_count = bool(_HAS_COUNT_RE.search(body))
        norm = None if has_count else re.sub(r"\s+", "", body)
        line = text.count("\n", 0, m.start()) + 1
        adjacent = prev_end is not None and text[prev_end : m.start()].strip() == ""
        if adjacent and norm is not None and norm == run_norm:
            run_len += 1
        else:
            flush()
            run_start_line = line
            run_norm = norm
            run_len = 1
        prev_end = end
        pos = end
    flush()
    return results


# Empty `visible` / `available` / `allowed` blocks fall through to the engine
# default (visible, available, allowed), so an effectively-empty one is dead
# weight that can be deleted outright.
_EMPTY_BLOCK_RE = re.compile(r"\b(visible|available|allowed)\s*=\s*\{")


def _find_empty_trigger_blocks(text: str):
    """Return (line, keyword) for each effectively-empty visible/available/
    allowed block."""
    results = []
    for m in _EMPTY_BLOCK_RE.finditer(text):
        body, end = extract_block_from_text(text, m.end() - 1)
        if end == -1:
            continue
        if _effectively_empty(body):
            line = text.count("\n", 0, m.start()) + 1
            results.append((line, m.group(1)))
    return results


# Government-match enumeration: an `OR` of `AND` clauses that compares the
# current scope's government to one other country group-by-group across every
# ideology. Because a country has exactly one government, the whole block
# collapses to the engine-native country comparison:
#
#   OR = {
#       AND = { has_government = democratic  FROM = { has_government = democratic } }
#       ... one AND per ideology group ...
#   }
#   # -> has_government = FROM          (same government)
#
# The negated clause shape (`FROM = { NOT = { has_government = X } }` or
# `NOT = { FROM = { has_government = X } }`) collapses to `NOT = { has_government = FROM }`.
#
# Only flagged when the OR enumerates ALL FIVE ideology groups with one
# consistent target and one consistent sense, and contains nothing but those
# AND clauses. A non-exhaustive enumeration (missing neutrality/nationalist)
# does NOT collapse cleanly (the omitted groups change meaning), and a mixed OR
# (extra `has_war = yes`, an `original_tag` gate, etc.) is left alone, so neither
# is suggested here.
_GOV_IDEOS = frozenset(
    {"democratic", "communism", "fascism", "neutrality", "nationalist"}
)
_OR_BLOCK_RE = re.compile(r"\bOR\s*=\s*\{")
_HAS_GOV_RE = re.compile(r"\bhas_government\s*=\s*(\w+)")
_GOV_ONLY_RE = re.compile(r"has_government\s*=\s*(\w+)\s*$")
_NOT_GOV_RE = re.compile(r"NOT\s*=\s*\{(.*)\}\s*$", re.DOTALL)


def _gov_scope_sense(inner: str, ideology: str):
    """For a scope-block body that must contain only a government check, return
    True when it is `NOT = { has_government = <ideology> }`, False when it is a
    bare `has_government = <ideology>`, or None for anything else (an extra
    condition, a different ideology, an unrelated NOT)."""
    stripped = inner.strip()
    negated = _NOT_GOV_RE.match(stripped)
    if negated:
        match = _GOV_ONLY_RE.fullmatch(negated.group(1).strip())
        return True if match and match.group(1) == ideology else None
    match = _GOV_ONLY_RE.fullmatch(stripped)
    return False if match and match.group(1) == ideology else None


def _parse_gov_clause(body: str):
    """Classify one `AND = { ... }` clause. Returns (target, sense, ideology)
    with sense "SAME"/"DIFF", or None unless the clause is EXACTLY one bare
    `has_government = X` plus one scope block checking the same ideology, with
    nothing else. Any extra condition (a stray trigger, a second scope, an
    unrelated NOT) makes the clause non-collapsible, so it is rejected."""
    bare = [
        (m.start(), m.end(), m.group(1))
        for m in _HAS_GOV_RE.finditer(body)
        if body.count("{", 0, m.start()) == body.count("}", 0, m.start())
    ]
    if len(bare) != 1:
        return None
    blocks = []
    pos = 0
    while True:
        bm = _OPEN_RE.search(body, pos)
        if not bm:
            break
        inner, end = extract_block_from_text(body, bm.end() - 1)
        if end == -1:
            return None
        blocks.append((bm.start(), end, bm.group(1), inner))
        pos = end
    if len(blocks) != 1:  # exactly one scope block beside the bare check
        return None
    b_start, b_end, ideology = bare[0]
    s_start, s_end, name, inner = blocks[0]
    # Nothing may sit in the AND body but the bare check and the scope block.
    leftover = body
    for start, end in sorted([(b_start, b_end), (s_start, s_end)], reverse=True):
        leftover = leftover[:start] + leftover[end:]
    if leftover.strip() or ideology not in _GOV_IDEOS:
        return None
    if name == "NOT":  # outer NOT = { TARGET = { [NOT = {] has_government = X [}] } }
        inner_block = _OPEN_RE.search(inner)
        if not inner_block:
            return None
        t_inner, t_end = extract_block_from_text(inner, inner_block.end() - 1)
        if t_end == -1 or inner[: inner_block.start()].strip() or inner[t_end:].strip():
            return None
        sense = _gov_scope_sense(t_inner, ideology)
        if sense is None:
            return None
        # The outer NOT flips the inner sense: NOT(same) is "different".
        return (inner_block.group(1), "SAME" if sense else "DIFF", ideology)
    sense = _gov_scope_sense(inner, ideology)
    if sense is None:
        return None
    return (name, "DIFF" if sense else "SAME", ideology)


def _find_government_match(text: str):
    """Return (line, replacement) for each exhaustive government-match `OR`
    block that collapses to a single `has_government` comparison."""
    results = []
    for m in _OR_BLOCK_RE.finditer(text):
        body, end = extract_block_from_text(text, m.end() - 1)
        if end == -1:
            continue
        clauses = []
        spans = []
        pos = 0
        clean = True
        while True:
            cm = _OPEN_RE.search(body, pos)
            if not cm:
                break
            if cm.group(1) != "AND":
                clean = False  # a non-AND child means this is not a pure enumeration
                break
            cbody, cend = extract_block_from_text(body, cm.end() - 1)
            if cend == -1:
                clean = False
                break
            parsed = _parse_gov_clause(cbody)
            if parsed is None:
                clean = False
                break
            clauses.append(parsed)
            spans.append((cm.start(), cend))
            pos = cend
        if not clean or len(clauses) < 2:
            continue
        # Reject mixed ORs: any bare condition outside the AND blocks (e.g.
        # `has_war = yes`) leaves non-whitespace once the AND spans are removed.
        leftover = body
        for s, e in reversed(spans):
            leftover = leftover[:s] + leftover[e:]
        if leftover.strip():
            continue
        targets = {c[0] for c in clauses}
        senses = {c[1] for c in clauses}
        ideologies = {c[2] for c in clauses}
        if ideologies != _GOV_IDEOS or len(targets) != 1 or len(senses) != 1:
            continue
        target = next(iter(targets))
        replacement = (
            f"has_government = {target}"
            if next(iter(senses)) == "SAME"
            else f"NOT = {{ has_government = {target} }}"
        )
        results.append((text.count("\n", 0, m.start()) + 1, replacement))
    return results


# Bare multi-child NOT is ambiguous: the project doc reads it as NAND, cwtools
# as NOR (see AGENTS.md "NOT blocks and NOR"). A single child — one trigger or
# one explicit AND/OR wrapper — is unambiguous and never flagged.
_NOT_RE = re.compile(r"\bNOT\s*=\s*\{")
_CHILD_KEY_RE = re.compile(r"[\w.:^@\[\]-]+\s*(?:>=|<=|=|>|<)\s*")
_VALUE_RE = re.compile(r"\S+")


def _count_children(body: str) -> int:
    """Count direct depth-1 constructs in a block body: a `key = { ... }`
    block (however large) and a bare `key = value` scalar each count as one
    child. Stops counting on anything unparseable, so malformed input
    undercounts rather than false-flagging."""
    count = 0
    pos = 0
    n = len(body)
    while pos < n:
        while pos < n and body[pos].isspace():
            pos += 1
        if pos >= n:
            break
        m = _CHILD_KEY_RE.match(body, pos)
        if not m:
            break
        count += 1
        pos = m.end()
        if pos < n and body[pos] == "{":
            _, end = extract_block_from_text(body, pos)
            if end == -1:
                break
            pos = end
        elif pos < n and body[pos] == '"':
            close = body.find('"', pos + 1)
            if close == -1:
                break
            pos = close + 1
        else:
            vm = _VALUE_RE.match(body, pos)
            if not vm:
                break
            pos = vm.end()
    return count


def _find_bare_not(text: str):
    """Return (line, child_count) for each `NOT = { ... }` with 2+ direct
    children. A single child — a lone trigger or an explicit AND/OR wrapper —
    is unambiguous and not flagged. finditer walks the whole file, so a NOT
    nested inside another block (OR, if, a second NOT) is found independently
    of its container."""
    results = []
    for m in _NOT_RE.finditer(text):
        body, end = extract_block_from_text(text, m.end() - 1)
        if end == -1:
            continue
        count = _count_children(body)
        if count >= 2:
            results.append((text.count("\n", 0, m.start()) + 1, count))
    return results


def _is_magic_chain(header: str) -> bool:
    return all(part in _MAGIC for part in header.split("."))


def _is_mergeable_scope(header: str) -> bool:
    """True when two adjacent `header = { }` blocks always merge safely."""
    if header in _NOT_TAGS:
        return False
    if header in _RELATION_SCOPES:
        return True
    if header.isdigit():
        return True
    if _TAG_RE.match(header):
        return True
    if _VAR_SCOPE_RE.match(header):
        return True
    return _is_magic_chain(header)


def _find_mergeable(text: str, base_line: int = 0, parent: str = ""):
    """Return (line, header) for every block that repeats its immediately
    preceding sibling's deterministic scope. Recurses into every block body so
    nested scopes are covered; only direct siblings at one depth are compared.

    *parent* is the header of the enclosing block; merging is suppressed under
    OR-like / weighted parents where siblings are not a plain AND list.
    """
    results = []
    pos = 0
    n = len(text)
    prev_header = None
    prev_end = None  # index just past the previous sibling's closing brace
    safe_context = parent not in _NO_MERGE_PARENTS
    while pos < n:
        m = _OPEN_RE.search(text, pos)
        if not m:
            break
        header = m.group(1)
        open_brace = m.end() - 1
        body, end = extract_block_from_text(text, open_brace)
        if end == -1:
            break

        if (
            safe_context
            and header == prev_header
            and prev_end is not None
            and _is_mergeable_scope(header)
            and text[prev_end : m.start()].strip() == ""
        ):
            line = base_line + text.count("\n", 0, m.start()) + 1
            results.append((line, header))

        body_start = open_brace + 1
        child_base = base_line + text.count("\n", 0, body_start)
        results.extend(_find_mergeable(body, child_base, header))

        prev_header = header
        prev_end = end
        pos = end
    return results


# random_state walks every state in the world. A limit whose only country
# filter is `controller = { tag = X }` or `is_controlled_by = X` is the
# engine-native `random_controlled_state` iterator (scoped to that country),
# which skips the world scan. Nested under AND/OR/NOT is left alone: those
# are not a plain controller filter. Extra sibling limits stay on the rewrite.
_RANDOM_STATE_RE = re.compile(r"\brandom_state\s*=\s*\{")
_CHILD_HEAD_RE = re.compile(r"([\w.:^@\[\]-]+)\s*(?:>=|<=|=|>|<)\s*")
_TAG_ONLY_RE = re.compile(r"^tag\s*=\s*(\S+)$")


def _iter_direct_assignments(body: str):
    """Yield (name, value, is_block) for each direct child. Stops on
    unparseable input rather than guessing."""
    pos = 0
    n = len(body)
    while pos < n:
        while pos < n and body[pos].isspace():
            pos += 1
        if pos >= n:
            return
        m = _CHILD_HEAD_RE.match(body, pos)
        if not m:
            return
        name = m.group(1)
        pos = m.end()
        if pos < n and body[pos] == "{":
            inner, end = extract_block_from_text(body, pos)
            if end == -1:
                return
            yield name, inner, True
            pos = end
        elif pos < n and body[pos] == '"':
            close = body.find('"', pos + 1)
            if close == -1:
                return
            yield name, body[pos : close + 1], False
            pos = close + 1
        else:
            vm = _VALUE_RE.match(body, pos)
            if not vm:
                return
            yield name, vm.group(0), False
            pos = vm.end()


def _controller_limit_detail(limit_body: str):
    """Return the controller-check text if *limit_body* has a direct
    `controller = { tag = X }` or `is_controlled_by = X` child, else None."""
    for name, value, is_block in _iter_direct_assignments(limit_body):
        if is_block and name == "controller":
            tm = _TAG_ONLY_RE.fullmatch(value.strip())
            if tm:
                return f"controller = {{ tag = {tm.group(1)} }}"
        elif not is_block and name == "is_controlled_by":
            return f"is_controlled_by = {value}"
    return None


def _find_random_controlled_shortcut(text: str):
    """Return (line, detail) for each `random_state` whose own limit has a
    controller-tag / is_controlled_by check that collapses to
    `random_controlled_state`."""
    results = []
    for m in _RANDOM_STATE_RE.finditer(text):
        body, end = extract_block_from_text(text, m.end() - 1)
        if end == -1:
            continue
        limit_body = None
        for name, value, is_block in _iter_direct_assignments(body):
            if is_block and name == "limit":
                limit_body = value
                break
        if limit_body is None:
            continue
        detail = _controller_limit_detail(limit_body)
        if detail:
            results.append((text.count("\n", 0, m.start()) + 1, detail))
    return results


# Redundant owner scope: a focus tree or decision locked to one country
# already evaluates in that scope. Ownership is strict (`tag = X`, current
# scope provably IS X) or gate-only (`original_tag = X`, breakaways admitted).
_OWNER_ATOM_RE = re.compile(r"\b(tag|original_tag)\s*=\s*([A-Z]{3})\b")
_REL_SCOPE_REF_RE = re.compile(r"\b(PREV|FROM)\b")

# Block headers that preserve the current country scope. Anything else that
# opens a block (tags, state ids, magic scopes, iterators, `target_trigger`,
# effect-parameter blocks, ...) drops the walk to non-owner scope, which only
# suppresses findings. `target_trigger` is deliberately absent: it runs in
# the target's scope, while `target_root_trigger` runs in ROOT's.
_OWNER_TRANSPARENT = frozenset(
    {
        "AND",
        "OR",
        "NOT",
        "if",
        "else_if",
        "else",
        "limit",
        "trigger",
        "hidden_trigger",
        "hidden_effect",
        "effect_tooltip",
        "custom_effect_tooltip",
        "custom_trigger_tooltip",
        "available",
        "allowed",
        "allow_branch",
        "visible",
        "activation",
        "bypass",
        "bypass_effect",
        "complete_effect",
        "remove_effect",
        "timeout_effect",
        "cancel_effect",
        "remove_trigger",
        "cancel_trigger",
        "target_root_trigger",
        "completion_reward",
        "select_effect",
        "ai_will_do",
        "modifier",
        "country",
        "offset",
    }
)
_OR_LIKE_HEADERS = frozenset({"OR", "NOT"})
_GATE_SITE_HEADERS = frozenset({"allowed", "allow_branch"})
# Ownership collection recurses only through AND-like wrappers. OR dilutes
# identity (`OR = { tag = X ... }` still admits non-X) and NOT inverts it
# (`allowed = { NOT = { tag = X } }` locks to everyone BUT X), so atoms under
# either prove nothing about the current scope.
_OWNER_GATE_TRANSPARENT = frozenset(
    {
        "AND",
        "limit",
        "trigger",
        "hidden_trigger",
        "allowed",
        "allow_branch",
        "country",
        "modifier",
    }
)


def _collect_owner_atoms(text: str) -> tuple[set[str], set[str]]:
    """Return (strict_tags, orig_tags) for `tag = X` / `original_tag = X`
    triggers not nested under a scope-changing or sense-changing block.
    AND-like wrappers don't block collection; country, state, magic, or
    iterator scopes do (atoms there describe another scope), as do OR and NOT
    (which dilute or invert the identity the atom asserts)."""
    strict: set[str] = set()
    orig: set[str] = set()
    pos = 0
    while True:
        m = _OPEN_RE.search(text, pos)
        gap = text[pos : m.start() if m else len(text)]
        for gm in _OWNER_ATOM_RE.finditer(gap):
            (strict if gm.group(1) == "tag" else orig).add(gm.group(2))
        if not m:
            break
        body, end = extract_block_from_text(text, m.end() - 1)
        if end == -1:
            break
        if m.group(1) in _OWNER_GATE_TRANSPARENT:
            s, o = _collect_owner_atoms(body)
            strict |= s
            orig |= o
        pos = end
    return strict, orig


def _owner_from_atoms(strict: set[str], orig: set[str]) -> tuple[str, bool] | None:
    """Return (tag, is_strict) when the atoms lock to one country, else None.
    Strict needs a strict atom for the tag; original-only gates admit
    breakaways whose current tag differs, so they never prove scope."""
    tags = strict | orig
    if len(tags) != 1:
        return None
    tag = next(iter(tags))
    if strict == {tag} and orig <= {tag}:
        return (tag, True)
    if not strict and orig == {tag}:
        return (tag, False)
    return None


def _liftable_owner_block(body: str) -> bool:
    """True when an owner-scope block splices into its parent. Bodies
    referencing PREV/FROM are left alone (relative chains), as are the two
    single-trigger shapes the scope-expansion check already owns."""
    if _REL_SCOPE_REF_RE.search(body):
        return False
    sm = _SINGLE_TRIGGER_RE.match(body.strip())
    if sm and (sm.group(1), sm.group(2)) in _FLAT_EQUIV:
        return False
    return True


def _walk_owner_scope(
    body: str,
    owner: str,
    strict: bool,
    findings: list,
    start_line: int,
    scope_owner: bool = True,
    or_depth: int = 0,
    gate_site: bool = False,
) -> None:
    """Append (message, line) for redundant owner-scope blocks and
    always-true owner checks. *body* starts at file line *start_line*;
    scope, OR/NOT depth, and gate-site state thread through transparent
    wrappers, while any other block drops to non-owner scope."""
    pos = 0
    while True:
        m = _OPEN_RE.search(body, pos)
        gap = body[pos : m.start() if m else len(body)]
        if scope_owner and or_depth == 0 and not gate_site:
            for gm in _OWNER_ATOM_RE.finditer(gap):
                kind, tag = gm.group(1), gm.group(2)
                if tag != owner:
                    continue
                if kind == "original_tag" or strict:
                    line = start_line + gap.count("\n", 0, gm.start())
                    findings.append(
                        (
                            f"`{kind} = {tag}` always true in this owner scope; remove it",
                            line,
                        )
                    )
        if not m:
            break
        header = m.group(1)
        inner, end = extract_block_from_text(body, m.end() - 1)
        if end == -1:
            break
        line = start_line + body.count("\n", 0, m.start())
        child_line = start_line + body.count("\n", 0, m.end())
        if header in _OWNER_TRANSPARENT:
            _walk_owner_scope(
                inner,
                owner,
                strict,
                findings,
                child_line,
                scope_owner,
                or_depth + (header in _OR_LIKE_HEADERS),
                gate_site or header in _GATE_SITE_HEADERS,
            )
        elif header == owner and scope_owner and strict:
            if _liftable_owner_block(inner):
                findings.append(
                    (
                        f"`{owner} = {{ ... }}` already runs in the `{owner}` scope; "
                        "remove the wrapper",
                        line,
                    )
                )
            else:
                _walk_owner_scope(
                    inner, owner, strict, findings, child_line, True, or_depth, False
                )
        else:
            _walk_owner_scope(
                inner, owner, strict, findings, child_line, False, or_depth, False
            )
        pos = end


def _top_level_blocks(text: str, names, start_line: int = 1):
    """Yield (header, body, body_start_line) for each depth-0 block. *names*
    None matches every header. Callers always land on depth 0 by jumping
    block to block."""
    pos = 0
    while True:
        m = _OPEN_RE.search(text, pos)
        if not m:
            break
        body, end = extract_block_from_text(text, m.end() - 1)
        if end == -1:
            break
        if names is None or m.group(1) in names:
            yield m.group(1), body, start_line + text.count("\n", 0, m.end())
        pos = end


def _direct_gate_atoms(body: str) -> tuple[set[str], set[str]]:
    """Owner atoms from direct-child `allowed` / `allow_branch` blocks."""
    strict: set[str] = set()
    orig: set[str] = set()
    for _, abody, _ in _top_level_blocks(body, _GATE_SITE_HEADERS):
        s, o = _collect_owner_atoms(abody)
        strict |= s
        orig |= o
    return strict, orig


def _scan_focus_file(text: str) -> list:
    """Return [(message, line)] for redundant owner scopes in one focus file.
    Ownership comes from the single `focus_tree` country gate, narrowed by
    each focus's own `allow_branch`; `joint_focus` blocks are never scanned."""
    findings: list = []
    trees = list(_top_level_blocks(text, {"focus_tree"}))
    if len(trees) != 1:
        return findings
    _, tbody, tline = trees[0]
    countries = list(_top_level_blocks(tbody, {"country"}))
    if len(countries) > 1:
        return findings
    base = _collect_owner_atoms(countries[0][1]) if countries else (set(), set())
    blocks = list(_top_level_blocks(tbody, {"focus"}, tline))
    blocks += list(_top_level_blocks(text, {"focus"}))
    for _, fbody, fline in blocks:
        s, o = _direct_gate_atoms(fbody)
        owner = _owner_from_atoms(base[0] | s, base[1] | o)
        if owner is None:
            continue
        _walk_owner_scope(fbody, owner[0], owner[1], findings, fline)
    return findings


def _scan_decision_file(text: str) -> list:
    """Return [(message, line)] for redundant owner scopes in one decisions
    file. Ownership comes from each decision's own `allowed`, extended with
    the enclosing `*_category` block's `allowed` when nested."""
    findings: list = []
    for header, body, bline in _top_level_blocks(text, None):
        if header.endswith("_category"):
            cstrict, corig = _direct_gate_atoms(body)
            for dheader, dbody, dline in _top_level_blocks(body, None, bline):
                if dheader.endswith("_category"):
                    continue
                if dheader in _GATE_SITE_HEADERS:
                    continue  # gate definition, not a decision
                s, o = _direct_gate_atoms(dbody)
                owner = _owner_from_atoms(cstrict | s, corig | o)
                if owner is None:
                    continue
                _walk_owner_scope(dbody, owner[0], owner[1], findings, dline)
        else:
            owner = _owner_from_atoms(*_direct_gate_atoms(body))
            if owner is None:
                continue
            _walk_owner_scope(body, owner[0], owner[1], findings, bline)
    return findings


def _scan_file(text: str, path: str):
    """Return [(message, line)] for one comment-stripped file. Pure function of
    *text*, so parse_files_cached can content-cache it."""
    findings = []
    for line, header in _find_mergeable(text):
        findings.append(
            (f"consecutive `{header} = {{ }}` blocks can be merged into one", line)
        )
    for line, tag, flat in _find_scope_expansion(text):
        findings.append(
            (f"`{tag} = {{ ... }}` scope opened for one trigger; use `{flat}`", line)
        )
    for line, chance in _find_two_bucket_random(text):
        findings.append(
            (
                f"two-bucket random_list with an empty bucket; use "
                f"`random = {{ chance = {chance} ... }}`",
                line,
            )
        )
    for line, run_len in _find_count_collapsible(text):
        findings.append(
            (
                f"{run_len} identical adjacent `create_unit` blocks; collapse "
                f"into one with `count = {run_len}`",
                line,
            )
        )
    for line, keyword in _find_empty_trigger_blocks(text):
        findings.append(
            (f"empty `{keyword} = {{ }}` block is redundant; remove it", line)
        )
    for line, replacement in _find_government_match(text):
        findings.append(
            (
                f"ideology enumeration over all five governments; use `{replacement}`",
                line,
            )
        )
    for line, detail in _find_random_controlled_shortcut(text):
        findings.append(
            (
                f"`random_state` limited by `{detail}`; use `random_controlled_state`",
                line,
            )
        )
    return findings


def _scan_bare_not(text: str, path: str):
    """Return [(message, line)] for the bare multi-child NOT check. Separate
    from _scan_file: NOT lives in trigger contexts across all of common/ (the
    founding bug was in an ai_strategy allowed block), so this check scans
    wider than the effect-bearing files the other detectors target."""
    findings = []
    for line, count in _find_bare_not(text):
        findings.append(
            (
                f"NOT with {count} children is ambiguous (semantics disputed "
                "NAND vs NOR); write `NOT = { OR = { ... } }` or one NOT "
                "per trigger",
                line,
            )
        )
    return findings


_FOCUS_PATTERNS = [
    "common/national_focus/*.txt",
    "common/national_focus/**/*.txt",
]
_DECISION_PATTERNS = [
    "common/decisions/*.txt",
    "common/decisions/**/*.txt",
]

_ALL_SCAN_PATTERNS = list(
    dict.fromkeys(
        _SCAN_PATTERNS + _NOT_SCAN_PATTERNS + _FOCUS_PATTERNS + _DECISION_PATTERNS
    )
)


def _matches_relative_pattern(path: str, patterns) -> bool:
    path_parts = path.replace(os.sep, "/").split("/")

    def matches(pattern_parts, path_index=0, pattern_index=0):
        if pattern_index == len(pattern_parts):
            return path_index == len(path_parts)
        pattern_part = pattern_parts[pattern_index]
        if pattern_part == "**":
            return matches(pattern_parts, path_index, pattern_index + 1) or (
                path_index < len(path_parts)
                and matches(pattern_parts, path_index + 1, pattern_index)
            )
        return (
            path_index < len(path_parts)
            and fnmatch.fnmatchcase(path_parts[path_index], pattern_part)
            and matches(pattern_parts, path_index + 1, pattern_index + 1)
        )

    return any(matches(pattern.replace(os.sep, "/").split("/")) for pattern in patterns)


def _scan_composite(text: str, path: str):
    """Run the simplification passes after one content read/cache lookup."""
    findings = []
    if _matches_relative_pattern(path, _SCAN_PATTERNS):
        findings.extend(_scan_file(text, path))
    if _matches_relative_pattern(path, _NOT_SCAN_PATTERNS):
        findings.extend(_scan_bare_not(text, path))
    if _matches_relative_pattern(path, _FOCUS_PATTERNS):
        findings.extend(_scan_focus_file(text))
    if _matches_relative_pattern(path, _DECISION_PATTERNS):
        findings.extend(_scan_decision_file(text))
    return findings


def _scan_owner_scope_only(text: str, path: str):
    """Run just the redundant owner-scope pass (focus trees + decisions)."""
    findings = []
    if _matches_relative_pattern(path, _FOCUS_PATTERNS):
        findings.extend(_scan_focus_file(text))
    if _matches_relative_pattern(path, _DECISION_PATTERNS):
        findings.extend(_scan_decision_file(text))
    return findings


_OWNER_SCOPE_PATTERNS = list(dict.fromkeys(_FOCUS_PATTERNS + _DECISION_PATTERNS))


class Validator(BaseValidator):
    TITLE = "SIMPLIFICATION SUGGESTIONS"
    STAGED_EXTENSIONS = [".txt"]

    def __init__(self, *args, owner_scope_only: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.owner_scope_only = owner_scope_only

    def run_validations(self):
        self._log_section("Scanning for simplification opportunities...")
        # All passes share one comment-stripped read per file; the cache key
        # must differ per pass set, since the same content yields different
        # findings under --owner-scope-only.
        if self.owner_scope_only:
            self._log_section("Owner-scope pass only (--owner-scope-only).")
            patterns = _OWNER_SCOPE_PATTERNS
            cache_key = "simplifications.owner-scope"
            scan_fn = _scan_owner_scope_only
        else:
            patterns = _ALL_SCAN_PATTERNS
            cache_key = "simplifications.composite"
            scan_fn = _scan_composite
        parsed = self.parse_files_cached(
            patterns,
            cache_key,
            lambda text, path: scan_fn(text, os.path.relpath(path, self.mod_path)),
        )
        self.log(f"Scanned {len(parsed)} files for simplification opportunities")

        self._log_section("Collecting and reporting results...")
        results = []
        for path, findings in parsed.items():
            rel = os.path.relpath(path, self.mod_path)
            for message, line in findings:
                results.append((message, rel, line))

        self._report(
            results,
            "No scope simplification opportunities found",
            "Scope simplifications (merge same-scope blocks / collapse one-trigger scopes):",
            severity=Severity.WARNING,
            category="simplification",
        )


def _add_extra_args(parser):
    parser.add_argument(
        "--owner-scope-only",
        action="store_true",
        dest="owner_scope_only",
        help="Only run the redundant owner-scope pass (focus trees and "
        "decisions); skip the other simplification checks",
    )


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Suggest merging consecutive same-scope blocks in Millennium Dawn mod",
        extra_args_fn=_add_extra_args,
    )
