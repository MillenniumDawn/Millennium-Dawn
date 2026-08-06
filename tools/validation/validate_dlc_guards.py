#!/usr/bin/env python3
"""Validate that DLC-gated technologies and special projects are guarded.

A technology whose folder is disabled without a DLC still parses, but the game
crashes when a tooltip resolves a reference into the disabled folder: hovering
China's `CHI_project_jxx` focus with no DLC enabled was a reproducible CTD
(issue #2790). The same applies to `sp:<project>` references whose project is
`allowed = { has_dlc = "..." }`.

The rule: any `add_tech_bonus` naming a DLC-gated technology, and any `sp:`
reference to a DLC-gated project, must sit inside an
`if = { limit = { has_dlc = "X" } }` branch, or under an equivalent
trigger/available/visible/allowed gate on the enclosing object.

Gating is derived, not hardcoded:
  - `common/technology_tags/*.txt` -- a folder's `available` block.
  - `common/technologies/*.txt` -- a tech's own `allow_branch`, plus the gate of
    its folders (only when every folder it sits in carries the same gate).
  - A research category counts as gated only when every tech carrying it shares
    one gate.
  - `common/special_projects/projects/*.txt` -- a project's `allowed` block.

A named technology or project is an ERROR: it crashes the game. A fully gated
category is a WARNING: it resolves to nothing and only wastes the bonus.
"""

import glob
import os
import re
import sys
from collections import defaultdict
from typing import Dict, FrozenSet, List, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import disk_cache  # noqa: E402 — same-dir import after sys.path tweak above
from shared_utils import compute_line_offsets, line_for_offset  # noqa: E402
from validate_history import _extract_dlc_conditions  # noqa: E402
from validator_common import (  # noqa: E402
    BaseValidator,
    run_validator_main,
    strip_comments,
)

Gates = FrozenSet[Tuple[str, str]]
Conditions = List[Tuple[str, str]]

# Numeric names so `random_list` weight buckets (`50 = { ... }`) parse as blocks.
_BLOCK_RE = re.compile(r"([A-Za-z_0-9@][A-Za-z0-9_.@]*(?::[A-Za-z0-9_]+)?)\s*=\s*\{")
_HAS_DLC_RE = re.compile(r'has_dlc\s*=\s*"([^"\n]+)"')
_QUOTED_RE = re.compile(r'"[^"\n]*"')
_TECH_ENTRY_RE = re.compile(r"\btechnology\s*=\s*([A-Za-z_][A-Za-z0-9_]*)")
_CATEGORY_ENTRY_RE = re.compile(r"\bcategory\s*=\s*([A-Za-z_][A-Za-z0-9_]*)")
_FOLDER_NAME_RE = re.compile(r"\bname\s*=\s*([A-Za-z_][A-Za-z0-9_]*)")
_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_PURE_REQUIRE_RE = re.compile(r'^has_dlc = "[^"\n]+"$')
_PURE_FORBID_RE = re.compile(r'^NOT = \{ has_dlc = "[^"\n]+" \}$')

# A has_dlc here gates the whole enclosing object, not just one branch body.
_OBJECT_GATES = frozenset({"trigger", "available", "visible", "allowed"})
# Never contain effects; walking `limit` would re-read a branch condition as a gate.
_SKIP_BLOCKS = frozenset(
    {"limit", "ai_will_do", "search_filters", "prerequisite", "mutually_exclusive"}
)
_BRANCHES = frozenset({"if", "else_if", "else"})
# Naming a disabled technology or project crashes the game; a fully gated
# category resolves to nothing and only wastes the bonus.
_CRASHING = frozenset({"dlc_tech_bonus", "dlc_special_project"})


def _match_brace(text: str, open_pos: int) -> int:
    """Return the index of the `}` closing the `{` at ``open_pos``, or -1."""
    depth = 0
    for i in range(open_pos, len(text)):
        char = text[i]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return i
    return -1


def _sanitize(text: str) -> str:
    """Strip comments and blank quoted strings, preserving line numbering.

    A `{` inside a `log = "..."` string would desync brace matching. DLC names
    are kept so `has_dlc = "X"` still yields X.
    """
    text = strip_comments(text)
    keep = {m.start(1) - 1 for m in _HAS_DLC_RE.finditer(text)}

    def _blank(match: "re.Match") -> str:
        if match.start() in keep:
            return match.group(0)
        return '"' + " " * (len(match.group(0)) - 2) + '"'

    return _QUOTED_RE.sub(_blank, text)


def _child_blocks(text: str, start: int, end: int) -> List[Tuple[str, int, int, int]]:
    """Direct child blocks of a body as (name, name_start, body_start, body_end)."""
    blocks = []
    i = start
    while i < end:
        match = _BLOCK_RE.search(text, i, end)
        if not match:
            break
        close = _match_brace(text, match.end() - 1)
        if close < 0 or close > end:
            break
        blocks.append((match.group(1), match.start(), match.end(), close))
        i = close + 1
    return blocks


def _branch_conditions(
    text: str, body_start: int, body_end: int
) -> Tuple[Conditions, bool]:
    """DLC conditions of an if/else_if branch, and whether the limit is pure.

    "Pure" means the limit is exactly one `has_dlc` (or one negated `has_dlc`)
    and nothing else, so the branch can be soundly inverted for a following
    `else`. A limit that also tests a tech or a flag says nothing definite about
    the DLC in the else branch.
    """
    for name, _, child_start, child_end in _child_blocks(text, body_start, body_end):
        if name != "limit":
            continue
        body = " ".join(text[child_start:child_end].split())
        pure = bool(_PURE_REQUIRE_RE.match(body) or _PURE_FORBID_RE.match(body))
        return _extract_dlc_conditions(body), pure
    return [], False


class Context:
    """DLCs known present / absent at a point in the script."""

    __slots__ = ("present", "absent")

    def __init__(
        self,
        present: FrozenSet[str] = frozenset(),
        absent: FrozenSet[str] = frozenset(),
    ):
        self.present = present
        self.absent = absent

    def apply(self, conditions: Conditions) -> "Context":
        if not conditions:
            return self
        present = set(self.present)
        absent = set(self.absent)
        for kind, dlc in conditions:
            if kind == "require":
                present.add(dlc)
                absent.discard(dlc)
            else:
                absent.add(dlc)
                present.discard(dlc)
        return Context(frozenset(present), frozenset(absent))

    def invert(self, conditions: Conditions) -> "Context":
        flipped = [
            ("forbid" if k == "require" else "require", d) for k, d in conditions
        ]
        return self.apply(flipped)


def parse_folder_gates(mod_path: str) -> Dict[str, Gates]:
    """Map technology folder name -> DLC gate from its `available` block."""
    gates: Dict[str, Gates] = {}
    pattern = os.path.join(mod_path, "common", "technology_tags", "*.txt")
    for filepath in sorted(glob.iglob(pattern)):
        try:
            with open(filepath, encoding="utf-8-sig", errors="replace") as handle:
                text = _sanitize(handle.read())
        except OSError:
            continue
        for name, _, body_start, body_end in _child_blocks(text, 0, len(text)):
            if name != "technology_folders":
                continue
            for folder, _, f_start, f_end in _child_blocks(text, body_start, body_end):
                conditions: Conditions = []
                for sub, _, s_start, s_end in _child_blocks(text, f_start, f_end):
                    if sub == "available":
                        conditions.extend(_extract_dlc_conditions(text[s_start:s_end]))
                if conditions:
                    gates[folder] = frozenset(conditions)
    return gates


def parse_tech_file(text: str, folder_gates: Dict[str, Gates]):
    """Return (tech -> gates, tech -> categories) for one technology file."""
    tech_gates: Dict[str, Gates] = {}
    tech_categories: Dict[str, Set[str]] = {}
    for name, _, body_start, body_end in _child_blocks(text, 0, len(text)):
        if name != "technologies":
            continue
        for tech, _, t_start, t_end in _child_blocks(text, body_start, body_end):
            conditions: Conditions = []
            folders: List[str] = []
            categories: Set[str] = set()
            for sub, _, s_start, s_end in _child_blocks(text, t_start, t_end):
                body = text[s_start:s_end]
                if sub == "allow_branch":
                    conditions.extend(_extract_dlc_conditions(body))
                elif sub == "folder":
                    folder = _FOLDER_NAME_RE.search(body)
                    if folder:
                        folders.append(folder.group(1))
                elif sub == "categories":
                    categories.update(_IDENT_RE.findall(body))
            # A tech reachable through even one ungated folder is not gated.
            folder_sets = {folder_gates.get(f, frozenset()) for f in folders}
            if folders and len(folder_sets) == 1:
                conditions.extend(next(iter(folder_sets)))
            tech_gates[tech] = frozenset(conditions)
            tech_categories[tech] = categories
    return tech_gates, tech_categories


def parse_tech_gates(
    mod_path: str, folder_gates: Dict[str, Gates]
) -> Tuple[Dict[str, Gates], Dict[str, Gates]]:
    """Build the tech -> gates and category -> gates maps."""
    tech_gates: Dict[str, Gates] = {}
    category_members: Dict[str, List[Gates]] = defaultdict(list)
    pattern = os.path.join(mod_path, "common", "technologies", "*.txt")
    for filepath in sorted(glob.iglob(pattern)):
        try:
            with open(filepath, encoding="utf-8-sig", errors="replace") as handle:
                raw = handle.read()
        except OSError:
            continue
        file_gates, file_categories = parse_tech_file(_sanitize(raw), folder_gates)
        tech_gates.update(file_gates)
        for tech, categories in file_categories.items():
            for category in categories:
                category_members[category].append(file_gates[tech])

    category_gates: Dict[str, Gates] = {}
    for category, member_gates in category_members.items():
        unique = set(member_gates)
        if len(unique) == 1:
            shared = next(iter(unique))
            if shared:
                category_gates[category] = shared
    return tech_gates, category_gates


def parse_project_gates(mod_path: str) -> Dict[str, Gates]:
    """Map special project id -> DLC gate from its `allowed` block."""
    gates: Dict[str, Gates] = {}
    pattern = os.path.join(mod_path, "common", "special_projects", "projects", "*.txt")
    for filepath in sorted(glob.iglob(pattern)):
        try:
            with open(filepath, encoding="utf-8-sig", errors="replace") as handle:
                text = _sanitize(handle.read())
        except OSError:
            continue
        for project, _, body_start, body_end in _child_blocks(text, 0, len(text)):
            conditions: Conditions = []
            for sub, _, s_start, s_end in _child_blocks(text, body_start, body_end):
                if sub == "allowed":
                    conditions.extend(_extract_dlc_conditions(text[s_start:s_end]))
            if conditions:
                gates[project] = frozenset(conditions)
    return gates


class Scanner:
    """Walks one file's script tree, tracking the enclosing has_dlc context."""

    def __init__(
        self,
        text: str,
        tech_gates: Dict[str, Gates],
        category_gates: Dict[str, Gates],
        project_gates: Dict[str, Gates],
    ):
        self.text = text
        self.tech_gates = tech_gates
        self.category_gates = category_gates
        self.project_gates = project_gates
        self.offsets = compute_line_offsets(text)
        self.findings: List[Tuple[str, int, str]] = []

    def _check(
        self,
        category: str,
        offset: int,
        kind: str,
        name: str,
        gates: Gates,
        ctx: Context,
    ):
        for gate_kind, dlc in sorted(gates):
            if gate_kind == "require" and dlc not in ctx.present:
                message = (
                    f'{kind} {name} requires "{dlc}" but is not inside '
                    f'if = {{ limit = {{ has_dlc = "{dlc}" }} }}'
                )
            elif gate_kind == "forbid" and dlc in ctx.present:
                message = (
                    f'{kind} {name} is unavailable with "{dlc}" but is granted '
                    f'inside a has_dlc = "{dlc}" branch'
                )
            else:
                continue
            self.findings.append(
                (category, line_for_offset(self.offsets, offset), message)
            )

    def _tech_bonus(self, body_start: int, body_end: int, ctx: Context):
        body = self.text[body_start:body_end]
        for match in _TECH_ENTRY_RE.finditer(body):
            gates = self.tech_gates.get(match.group(1))
            if gates:
                self._check(
                    "dlc_tech_bonus",
                    body_start + match.start(1),
                    "technology",
                    match.group(1),
                    gates,
                    ctx,
                )
        for match in _CATEGORY_ENTRY_RE.finditer(body):
            gates = self.category_gates.get(match.group(1))
            if gates:
                self._check(
                    "dlc_tech_bonus_category",
                    body_start + match.start(1),
                    "category",
                    match.group(1),
                    gates,
                    ctx,
                )

    def walk(self, start: int, end: int, ctx: Context, chain: Conditions = ()):
        blocks = _child_blocks(self.text, start, end)
        gate_conditions: Conditions = []
        for name, _, body_start, body_end in blocks:
            if name in _OBJECT_GATES:
                gate_conditions.extend(
                    _extract_dlc_conditions(self.text[body_start:body_end])
                )
        ctx = ctx.apply(gate_conditions)

        # HOI4 accepts `else` both as a sibling of its `if` and nested inside it,
        # so the enclosing branch seeds the ruled-out chain on the way in.
        chain = list(chain)
        for name, name_start, body_start, body_end in blocks:
            if name in _SKIP_BLOCKS or name in _OBJECT_GATES:
                continue
            if name == "add_tech_bonus":
                self._tech_bonus(body_start, body_end, ctx)
                continue
            if name in _BRANCHES:
                conditions, pure = _branch_conditions(self.text, body_start, body_end)
                if name == "if":
                    chain = []
                    branch_ctx = ctx.apply(conditions)
                else:
                    branch_ctx = ctx.invert(chain).apply(conditions)
                self.walk(body_start, body_end, branch_ctx, conditions if pure else ())
                if name == "else" or not pure:
                    # An impure branch cannot be inverted, and hides earlier ones too.
                    chain = []
                else:
                    chain = chain + conditions
                continue
            if name.startswith("sp:"):
                gates = self.project_gates.get(name[3:])
                if gates:
                    self._check(
                        "dlc_special_project",
                        name_start,
                        "special project",
                        name[3:],
                        gates,
                        ctx,
                    )
            self.walk(body_start, body_end, ctx)


_TECH_GATES: Dict[str, Gates] = {}
_CATEGORY_GATES: Dict[str, Gates] = {}
_PROJECT_GATES: Dict[str, Gates] = {}
_MOD_PATH = ""


def _init_worker(tech_gates, category_gates, project_gates, mod_path):
    global _TECH_GATES, _CATEGORY_GATES, _PROJECT_GATES, _MOD_PATH
    _TECH_GATES = tech_gates
    _CATEGORY_GATES = category_gates
    _PROJECT_GATES = project_gates
    _MOD_PATH = mod_path


def scan_file(filepath: str) -> List[Tuple[str, str, int, str]]:
    """Return (category, relative path, line, message) for one content file."""
    try:
        with open(filepath, encoding="utf-8-sig", errors="replace") as handle:
            raw = handle.read()
    except OSError:
        return []
    if "add_tech_bonus" not in raw and "sp:" not in raw:
        return []

    def compute():
        scanner = Scanner(_sanitize(raw), _TECH_GATES, _CATEGORY_GATES, _PROJECT_GATES)
        scanner.walk(0, len(scanner.text), Context())
        return scanner.findings

    findings = disk_cache.per_file_cached_by_content(
        _MOD_PATH, "dlc_guards_scan", filepath, raw, compute
    )
    relative = os.path.relpath(filepath, _MOD_PATH).replace(os.sep, "/")
    return [(category, relative, line, message) for category, line, message in findings]


class Validator(BaseValidator):
    TITLE = "DLC GUARD VALIDATION"

    def validate_dlc_guards(self):
        self._log_section("DLC-gated technology and special project guards")
        folder_gates = parse_folder_gates(self.mod_path)
        tech_gates, category_gates = parse_tech_gates(self.mod_path, folder_gates)
        project_gates = parse_project_gates(self.mod_path)
        self.log(
            f"  {len(folder_gates)} DLC-gated folders, {len(tech_gates)} technologies, "
            f"{len(category_gates)} gated categories, {len(project_gates)} gated projects"
        )

        files = self._collect_files(["common/**/*.txt", "events/**/*.txt"])
        results = self._pool_map_init(
            scan_file,
            files,
            _init_worker,
            (tech_gates, category_gates, project_gates, self.mod_path),
        )

        issues = sorted(row for rows in results for row in rows)
        for category, relative, line, message in issues:
            if category in _CRASHING:
                self.add_error(category, message, relative, line)
            else:
                self.add_warning(category, message, relative, line)

        if issues:
            self.log(f"✗ {len(issues)} unguarded DLC-gated reference(s):", "error")
            for _, relative, line, message in issues:
                self.log(f"  {relative}:{line} - {message}")
        else:
            self.log(
                "✓ All DLC-gated technologies and projects sit behind a has_dlc guard"
            )

    def run_validations(self):
        self.validate_dlc_guards()


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate that DLC-gated technologies and special projects sit behind a has_dlc guard",
    )
