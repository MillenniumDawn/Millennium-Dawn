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

Three more collapses are flagged on top of the same-scope merge:

  * two-bucket `random_list` with one empty bucket -> `random = { chance = N }`
  * runs of identical adjacent `create_unit` blocks -> one block + `count = N`
  * empty `visible` / `available` / `allowed` blocks -> delete (engine default)

Output is WARNING-only.
"""
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


def _find_two_bucket_random(text: str):
    """Return (line, chance) for each two-bucket random_list with one empty
    bucket, where chance is the probability the non-empty bucket fires."""
    results = []
    for m in _RANDOM_LIST_RE.finditer(text):
        body, end = extract_block_from_text(text, m.end() - 1)
        if end == -1:
            continue
        buckets = []  # (weight, is_empty) for each direct-child bucket
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
            buckets.append((float(bm.group(1)), _effectively_empty(bbody)))
            pos = bend
        if malformed or len(buckets) != 2:
            continue
        empties = [w for w, e in buckets if e]
        non_empty = [w for w, e in buckets if not e]
        if len(empties) != 1 or len(non_empty) != 1:
            continue
        total = empties[0] + non_empty[0]
        if total <= 0:
            continue
        chance = round(100 * non_empty[0] / total)
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
    return findings


class Validator(BaseValidator):
    TITLE = "SIMPLIFICATION SUGGESTIONS"
    STAGED_EXTENSIONS = [".txt"]

    def run_validations(self):
        # parse_files_cached reads case-preserving + comment-stripped and
        # content-caches each file's findings, so a warm run only re-scans
        # changed files.
        parsed = self.parse_files_cached(
            _SCAN_PATTERNS, "simplifications.scan", _scan_file
        )
        self.log(f"Scanned {len(parsed)} files for simplification opportunities")

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


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Suggest merging consecutive same-scope blocks in Millennium Dawn mod",
    )
