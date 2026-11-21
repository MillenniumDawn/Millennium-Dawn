#!/usr/bin/env python3
"""Validate that special project unlocks are announced on the right source.

A tech or focus that unlocks a special project shows it with
`custom_effect_tooltip = { localization_key = SP_UNLOCK_PROJECT PROJECT = sp_x }`.
The project's `visible` and `available` blocks decide what unlocks it:

  - `OR` branches and the branches of an if/else chain are separate ways in.
  - Everything else in one way in is needed together. Members are `has_tech`,
    `has_completed_focus`, `is_special_project_completed` and the
    `special_project_parent` list. Other triggers are ignored.

`sp-unlock-tooltip-missing`: a way in that needs a tech or focus has no member
announcing the project. One tooltip is enough, since printing it on every
required tech would claim each one unlocks the project alone. A parent
project's tooltip and a focus's `complete_special_project` count.

`sp-unlock-tooltip-misplaced`: a tech, focus, or project shows the tooltip for a
project it does not unlock, or for a project that does not exist.

Both are WARNING. Events, decisions and scripted effects are not read.

`inherit_special_projects_from_prev` copies completed projects between countries
with one line per project, so the list has to follow the project files.

A project is open to every country when its `allowed` holds only `always = yes`,
`has_dlc` and `has_game_rule`, alone or under `NOT`, `OR` and `AND`. Any other
trigger, a comparison, or `always = no` anywhere ties it to a country or scenario.

`sp-inherit-missing`: an open project is not in the effect.

`sp-inherit-locked`: the effect names a project that is not open.

`sp-inherit-unknown`: the effect names a project that does not exist.

`sp-inherit-effect-missing`: the effect or its file is gone.

All four are ERROR.
"""

import os
import re
import sys
from collections import defaultdict
from itertools import product
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from shared_utils import (  # noqa: E402
    blank_quoted_strings,
    compute_line_offsets,
    line_for_offset,
    list_files,
    read_text_strict,
)
from validator_common import (  # noqa: E402
    BaseValidator,
    _child_blocks,
    run_validator_main,
    strip_comments,
)

Member = Tuple[str, str]
Way = FrozenSet[Member]

_MEMBER_RE = re.compile(
    r"\b(has_tech|has_completed_focus|is_special_project_completed)"
    r"\s*=\s*(?:sp:)?([A-Za-z0-9_]+)"
)
_KIND = {
    "has_tech": "tech",
    "has_completed_focus": "focus",
    "is_special_project_completed": "project",
}
_TOOLTIP_RE = re.compile(r"\bcustom_effect_tooltip\s*=\s*\{([^{}]*)\}")
_SP_KEY_RE = re.compile(r"\blocalization_key\s*=\s*SP_UNLOCK_PROJECT\b")
_PROJECT_RE = re.compile(r"\bPROJECT\s*=\s*([A-Za-z0-9_:]+)")
_COMPLETE_RE = re.compile(r"\bcomplete_special_project\s*=\s*sp:([A-Za-z0-9_]+)")
_FOCUS_ID_RE = re.compile(r"(?m)^\s*id\s*=\s*([A-Za-z0-9_]+)")
_FOCUS_BLOCKS = frozenset({"focus", "shared_focus", "joint_focus"})
# Nothing under these has to hold for the project to unlock.
_NOT_REQUIRED = frozenset({"NOT", "NOR", "NAND", "count_triggers", "limit"})

_KEY_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*=")
# `always = no` closes a project even under NOT, which nobody writes.
_CLOSED_RE = re.compile(r"\balways\s*=\s*no\b|[<>]")
# An `allowed` body made of these alone leaves the project open to every country.
_OPEN_ALLOWED = frozenset(
    {"always", "has_dlc", "has_game_rule", "rule", "option", "NOT", "OR", "AND"}
)

_PROJECTS_DIR = "common/special_projects/projects"
_INHERIT_FILE = "common/scripted_effects/00_special_project_effects.txt"
_INHERIT_EFFECT = "inherit_special_projects_from_prev"
_SOURCE_DIRS = (
    ("tech", "common/technologies"),
    ("focus", "common/national_focus"),
    ("project", _PROJECTS_DIR),
)


def _read(path: str) -> str:
    return blank_quoted_strings(strip_comments(read_text_strict(path)))


def _branches(ways: List[Way]) -> List[Way]:
    """Alternatives that name a member; a branch gated only by a tag or flag
    check would otherwise excuse every other country."""
    return [way for way in ways if way] or [frozenset()]


def _join(left: List[Way], right: List[Way]) -> List[Way]:
    return sorted({a | b for a, b in product(left, right)}, key=sorted)


def _direct_members(text: str, start: int, end: int, blocks) -> Way:
    return frozenset(
        (_KIND[m.group(1)], m.group(2))
        for m in _MEMBER_RE.finditer(text, start, end)
        if not any(b_start <= m.start() < b_end for _, b_start, _, b_end in blocks)
    )


def _either(text: str, start: int, end: int) -> List[Way]:
    """An OR body: each member line and each block is its own way in."""
    blocks = _child_blocks(text, start, end)
    ways = [frozenset([member]) for member in _direct_members(text, start, end, blocks)]
    for name, _, b_start, b_end in blocks:
        if name == "OR":
            ways.extend(_either(text, b_start, b_end))
        elif name not in _NOT_REQUIRED:
            ways.extend(ways_in(text, b_start, b_end))
    return _branches(ways)


def ways_in(text: str, start: int, end: int) -> List[Way]:
    """The ways a trigger body can hold, each a set of members needed together."""
    blocks = _child_blocks(text, start, end)
    ways = [_direct_members(text, start, end, blocks)]
    chain: List[Way] = []
    for name, _, b_start, b_end in blocks:
        if chain and name in ("else_if", "else"):
            chain.extend(ways_in(text, b_start, b_end))
            continue
        if chain:
            ways, chain = _join(ways, _branches(chain)), []
        if name == "if":
            chain = ways_in(text, b_start, b_end)
        elif name == "OR":
            ways = _join(ways, _either(text, b_start, b_end))
        elif name not in _NOT_REQUIRED:
            ways = _join(ways, ways_in(text, b_start, b_end))
    if chain:
        ways = _join(ways, _branches(chain))
    return ways


def parse_projects(text: str) -> Dict[str, Tuple[int, List[Way]]]:
    """Map project id -> (definition offset, ways in) for one project file."""
    projects = {}
    for name, name_start, start, end in _child_blocks(text, 0, len(text)):
        ways: List[Way] = [frozenset()]
        for sub, _, s_start, s_end in _child_blocks(text, start, end):
            if sub in ("visible", "available"):
                ways = _join(ways, ways_in(text, s_start, s_end))
            elif sub == "special_project_parent":
                parents = text[s_start:s_end].split()
                ways = _join(ways, [frozenset(("project", p) for p in parents)])
        projects[name] = (name_start, ways)
    return projects


def _owners(kind: str, text: str) -> List[Tuple[str, int, int]]:
    """(id, body start, body end) of each tech, focus, or project in a file."""
    top = _child_blocks(text, 0, len(text))
    if kind == "project":
        return [(name, start, end) for name, _, start, end in top]
    if kind == "tech":
        return [
            (name, start, end)
            for block, _, b_start, b_end in top
            if block == "technologies"
            for name, _, start, end in _child_blocks(text, b_start, b_end)
        ]
    focuses = [block for block in top if block[0] in _FOCUS_BLOCKS]
    for _, _, b_start, b_end in top:
        focuses.extend(
            block
            for block in _child_blocks(text, b_start, b_end)
            if block[0] in _FOCUS_BLOCKS
        )
    owners = []
    for _, _, start, end in focuses:
        match = _FOCUS_ID_RE.search(text, start, end)
        if match:
            owners.append((match.group(1), start, end))
    return owners


def parse_sources(kind: str, text: str):
    """Return (tooltip sites, completed projects) for one file.

    A site is (owner, project, offset). Completions map owner -> projects.
    """
    sites: List[Tuple[str, str, int]] = []
    completes: Dict[str, Set[str]] = defaultdict(set)
    for owner, start, end in _owners(kind, text):
        for match in _TOOLTIP_RE.finditer(text, start, end):
            body = match.group(1)
            project = _PROJECT_RE.search(body)
            if _SP_KEY_RE.search(body) and project:
                sites.append((owner, project.group(1), match.start()))
        for match in _COMPLETE_RE.finditer(text, start, end):
            completes[owner].add(match.group(1))
    return sites, completes


def _is_open(allowed: str) -> bool:
    return not _CLOSED_RE.search(allowed) and _OPEN_ALLOWED.issuperset(
        _KEY_RE.findall(allowed)
    )


def parse_allowed(text: str) -> Dict[str, Tuple[int, bool]]:
    """Map project id -> (definition offset, open to every country)."""
    projects = {}
    for name, name_start, start, end in _child_blocks(text, 0, len(text)):
        projects[name] = (
            name_start,
            all(
                _is_open(text[s_start:s_end])
                for sub, _, s_start, s_end in _child_blocks(text, start, end)
                if sub == "allowed"
            ),
        )
    return projects


def parse_inherit_list(text: str) -> Optional[Dict[str, int]]:
    """Map each project the inherit effect copies to its offset, None without it."""
    for name, _, start, end in _child_blocks(text, 0, len(text)):
        if name == _INHERIT_EFFECT:
            return {
                match.group(1): match.start()
                for match in _COMPLETE_RE.finditer(text, start, end)
            }
    return None


class Validator(BaseValidator):
    TITLE = "SPECIAL PROJECT VALIDATION"

    def _relative(self, path: str) -> str:
        return os.path.relpath(path, self.mod_path).replace(os.sep, "/")

    def validate_unlock_tooltips(self):
        self._log_section("Special project unlock tooltips")
        projects: Dict[str, Tuple[str, int, List[Way]]] = {}
        for path in list_files(os.path.join(self.mod_path, _PROJECTS_DIR)):
            text = _read(path)
            offsets = compute_line_offsets(text)
            for name, (offset, ways) in parse_projects(text).items():
                projects[name] = (
                    self._relative(path),
                    line_for_offset(offsets, offset),
                    ways,
                )

        announced: Dict[Member, Set[str]] = defaultdict(set)
        sites = []
        for kind, folder in _SOURCE_DIRS:
            for path in list_files(os.path.join(self.mod_path, folder)):
                text = _read(path)
                if (
                    "SP_UNLOCK_PROJECT" not in text
                    and "complete_special_project" not in text
                ):
                    continue
                file_sites, completes = parse_sources(kind, text)
                offsets = compute_line_offsets(text)
                for owner, project, offset in file_sites:
                    announced[(kind, owner)].add(project)
                    line = line_for_offset(offsets, offset)
                    sites.append((kind, owner, project, self._relative(path), line))
                for owner, done in completes.items():
                    announced[(kind, owner)].update(done)

        for kind, owner, project, relative, line in sites:
            if project not in projects:
                message = f"{owner} has an SP_UNLOCK_PROJECT tooltip for unknown special project {project}"
            elif not any((kind, owner) in way for way in projects[project][2]):
                message = f"{owner} has an SP_UNLOCK_PROJECT tooltip for {project}, which it does not unlock"
            else:
                continue
            self.add_warning("sp-unlock-tooltip-misplaced", message, relative, line)

        for project, (relative, line, ways) in sorted(projects.items()):
            for way in ways:
                if not any(kind in ("tech", "focus") for kind, _ in way):
                    continue
                if any(project in announced.get(member, ()) for member in way):
                    continue
                names = " + ".join(sorted(name for _, name in way))
                self.add_warning(
                    "sp-unlock-tooltip-missing",
                    f"special project {project} is unlocked by {names}, but no "
                    "SP_UNLOCK_PROJECT tooltip there names it",
                    relative,
                    line,
                )

        self.log(
            f"  {len(projects)} projects, {len(sites)} unlock tooltips, "
            f"{self.warnings_found} findings"
        )

    def validate_inherit_list(self):
        self._log_section("Special project inherit list")
        path = os.path.join(self.mod_path, _INHERIT_FILE)
        text = _read(path) if os.path.isfile(path) else ""
        listed = parse_inherit_list(text)
        if listed is None:
            self.add_error(
                "sp-inherit-effect-missing",
                f"{_INHERIT_EFFECT} is not defined",
                _INHERIT_FILE,
                1,
            )
            return

        known: Dict[str, bool] = {}
        for project_path in list_files(os.path.join(self.mod_path, _PROJECTS_DIR)):
            project_text = _read(project_path)
            offsets = compute_line_offsets(project_text)
            for name, (offset, is_open) in parse_allowed(project_text).items():
                known[name] = is_open
                if is_open and name not in listed:
                    self.add_error(
                        "sp-inherit-missing",
                        f"special project {name} is open to every country, but "
                        f"{_INHERIT_EFFECT} does not copy it",
                        self._relative(project_path),
                        line_for_offset(offsets, offset),
                    )

        offsets = compute_line_offsets(text)
        for name, offset in listed.items():
            if name not in known:
                category, what = "sp-inherit-unknown", "unknown special project"
            elif not known[name]:
                category, what = "sp-inherit-locked", "country or scenario project"
            else:
                continue
            self.add_error(
                category,
                f"{_INHERIT_EFFECT} copies {what} {name}",
                _INHERIT_FILE,
                line_for_offset(offsets, offset),
            )

    def run_validations(self):
        self.validate_unlock_tooltips()
        self.validate_inherit_list()


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate that special project unlocks are announced on the right tech or focus",
    )
