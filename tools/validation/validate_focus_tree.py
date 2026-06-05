#!/usr/bin/env python3
"""Validate focus tree structural integrity in Millennium Dawn."""
import os
import re
import sys
from collections import defaultdict
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import disk_cache
from shared_utils import extract_block_from_text as _extract_block
from sprite_index import build_sprite_index
from validator_common import (
    BaseValidator,
    Severity,
    case_mismatch,
    casefold_index,
    run_validator_main,
    strip_comments,
)

# Opening of a focus_tree or top-level focus definition block
# (shared_focus and joint_focus are both standalone definitions that can be
# referenced as prerequisites — they live outside any focus_tree wrapper)
_FOCUS_TREE_START = re.compile(r"\bfocus_tree\s*=\s*\{")
_SHARED_FOCUS_DEF_START = re.compile(r"\b(?:shared_focus|joint_focus)\s*=\s*\{")

# focus ID extraction
_FOCUS_ID_RE = re.compile(r"\bfocus\s*=\s*\{")
_ID_LINE_RE = re.compile(r"\bid\s*=\s*(\S+)")

# focus icon: `icon = X` or `icon = "GFX X"`. The value resolves verbatim to a
# spriteType of that exact name (MD uses bare names like `money` as well as
# GFX_-prefixed ones), so it is checked against the full sprite-name index.
# Quoted values are captured whole, including embedded/trailing spaces, because
# the engine matches the sprite name verbatim (a quoted value with a space is a
# real, distinct sprite name, not two tokens).
_FOCUS_BLOCK_START = re.compile(r"\b(?:focus|shared_focus|joint_focus)\s*=\s*\{")
_ICON_LINE_RE = re.compile(r'\bicon\s*=\s*(?:"([^"]*)"|([^\s{}]+))')

# prerequisite blocks: prerequisite = { focus = A  focus = B }
_PREREQ_BLOCK_RE = re.compile(r"\bprerequisite\s*=\s*\{([^}]*)\}", re.DOTALL)
_PREREQ_FOCUS_RE = re.compile(r"\bfocus\s*=\s*(\S+)")

# shared_focus reference inside a focus_tree block (not a definition)
_SHARED_REF_RE = re.compile(r"\bshared_focus\s*=\s*(\w+)")


def _line_of(text: str, pos: int) -> int:
    """Return the 1-based line number of *pos* in *text*."""
    return text[:pos].count("\n") + 1


def _parse_focus_ids_from_block(block: str) -> List[Tuple[str, int, List[List[str]]]]:
    """Parse all focus = { ... } blocks from a tree/shared block body.

    Returns a list of (focus_id, relative_line_offset, prerequisite_groups).
    prerequisite_groups is a list of lists — each inner list is the OR-group
    of focus IDs from one prerequisite = { ... } block.
    """
    results: List[Tuple[str, int, List[List[str]]]] = []
    search_start = 0
    while True:
        m = _FOCUS_ID_RE.search(block, search_start)
        if not m:
            break
        body, end = _extract_block(block, m.start())
        if not body:
            search_start = m.end()
            continue

        id_match = _ID_LINE_RE.search(body)
        if not id_match:
            search_start = end
            continue

        focus_id = id_match.group(1)
        line_offset = block[: m.start()].count("\n")

        prereq_groups: List[List[str]] = []
        for pb in _PREREQ_BLOCK_RE.finditer(body):
            group = _PREREQ_FOCUS_RE.findall(pb.group(1))
            if group:
                prereq_groups.append(group)

        results.append((focus_id, line_offset, prereq_groups))
        search_start = end
    return results


def parse_focus_file(args: Tuple[str, str]) -> Dict:
    """Read one focus tree file and return its parsed structure, content-cached."""
    filepath, mod_path = args
    try:
        with open(filepath, "r", encoding="utf-8-sig", errors="replace") as fh:
            raw = fh.read()
    except Exception:
        return {"filepath": filepath, "trees": [], "shared_defs": {}}
    text = strip_comments(raw)
    return disk_cache.per_file_cached_by_content(
        mod_path,
        "focus_tree.parse",
        filepath,
        text,
        lambda: _parse_focus_text(text, filepath),
    )


def _extract_focus_icons(args: Tuple[str, str]) -> List[Tuple[str, str, str, int]]:
    """Pool worker: return (focus_id, icon, filepath, line) for each focus.

    Takes the first `icon =` inside each focus/shared_focus/joint_focus block.
    Focuses that omit `icon` (or use a dynamic `[...]` value) are skipped.
    """
    filepath, mod_path = args
    try:
        with open(filepath, "r", encoding="utf-8-sig", errors="replace") as fh:
            raw = fh.read()
    except Exception:
        return []
    text = strip_comments(raw)

    def _compute() -> List[Tuple[str, str, str, int]]:
        out: List[Tuple[str, str, str, int]] = []
        pos = 0
        while True:
            m = _FOCUS_BLOCK_START.search(text, pos)
            if not m:
                break
            body, end = _extract_block(text, m.start())
            if not body:
                pos = m.end()
                continue
            idm = _ID_LINE_RE.search(body)
            icm = _ICON_LINE_RE.search(body)
            if idm and icm:
                icon = icm.group(1) if icm.group(1) is not None else icm.group(2)
                if "[" not in icon and "]" not in icon:
                    out.append(
                        (idm.group(1), icon, filepath, _line_of(text, m.start()))
                    )
            pos = end
        return out

    return disk_cache.per_file_cached_by_content(
        mod_path, "focus_tree.icons", filepath, text, _compute
    )


def _parse_focus_text(text: str, filepath: str) -> Dict:
    """Parse comment-stripped focus tree text into a structured result dict.

    Keys:
      "filepath"      — absolute path
      "trees"         — list of tree dicts (see below)
      "shared_defs"   — dict of shared_focus_id -> (line, filepath)

    Each tree dict:
      "focuses"       — list of (focus_id, abs_line, prereq_groups)
      "shared_refs"   — set of shared_focus IDs referenced inside the tree
    """
    result = {
        "filepath": filepath,
        "trees": [],
        "shared_defs": {},
    }

    # --- collect shared_focus definitions (top-level) ---
    pos = 0
    while True:
        m = _SHARED_FOCUS_DEF_START.search(text, pos)
        if not m:
            break
        body, end = _extract_block(text, m.start())
        if not body:
            pos = m.end()
            continue
        id_match = _ID_LINE_RE.search(body)
        if id_match:
            sfid = id_match.group(1)
            abs_line = _line_of(text, m.start())
            prereq_groups: List[List[str]] = []
            for pb in _PREREQ_BLOCK_RE.finditer(body):
                group = _PREREQ_FOCUS_RE.findall(pb.group(1))
                if group:
                    prereq_groups.append(group)
            # Store shared focus definition for the global duplicate check and
            # prerequisite resolution.  We also expose (line, filepath) so the
            # caller can report accurate locations.
            result["shared_defs"][sfid] = {
                "line": abs_line,
                "filepath": filepath,
                "prereq_groups": prereq_groups,
            }
        pos = end

    # --- collect focus_tree blocks ---
    pos = 0
    while True:
        m = _FOCUS_TREE_START.search(text, pos)
        if not m:
            break
        body, end = _extract_block(text, m.start())
        if not body:
            pos = m.end()
            continue

        tree_focuses: List[Tuple[str, int, List[List[str]]]] = []
        for focus_id, line_offset, prereq_groups in _parse_focus_ids_from_block(body):
            abs_line = _line_of(text, m.start()) + line_offset
            tree_focuses.append((focus_id, abs_line, prereq_groups))

        # shared_focus references inside the tree (not definitions)
        shared_refs: Set[str] = set()
        for sr in _SHARED_REF_RE.finditer(body):
            # Only consider bare `shared_focus = NAME` (not `shared_focus = {`)
            next_non_ws = body[sr.end() :].lstrip()
            if next_non_ws.startswith("{"):
                continue
            shared_refs.add(sr.group(1))

        result["trees"].append(
            {
                "focuses": tree_focuses,
                "shared_refs": shared_refs,
            }
        )
        pos = end

    return result


class Validator(BaseValidator):
    TITLE = "FOCUS TREE STRUCTURAL VALIDATION"
    STAGED_EXTENSIONS = [".txt", ".yml"]

    def __init__(self, mod_path: str, **kwargs):
        self.missing_icons = kwargs.pop("missing_icons", False)
        super().__init__(mod_path, **kwargs)
        self._parsed_cache: Optional[List[Dict]] = None
        self._staged_paths: Optional[Set[str]] = None

    # -----------------------------------------------------------------------
    # Data collection
    # -----------------------------------------------------------------------

    def _get_staged_paths(self) -> Set[str]:
        """Return the set of staged focus file paths (relative to mod_path).

        In non-staged mode returns an empty set (meaning: report all files).
        """
        if self._staged_paths is not None:
            return self._staged_paths
        if self.staged_only:
            staged = self._collect_files(["common/national_focus/*.txt"])
            self._staged_paths = {os.path.relpath(f, self.mod_path) for f in staged}
        else:
            self._staged_paths = set()
        return self._staged_paths

    def _is_reportable(self, filepath: str) -> bool:
        """Return True if issues in this file should be reported.

        In staged mode, only report for staged files. In full mode, report all.
        """
        staged = self._get_staged_paths()
        if not staged and self.staged_only:
            return False
        if not self.staged_only:
            return True
        rel = os.path.relpath(filepath, self.mod_path)
        return rel in staged

    def _get_parsed_files(self) -> List[Dict]:
        if self._parsed_cache is not None:
            return self._parsed_cache
        files = self._collect_files(["common/national_focus/*.txt"], ignore_staged=True)
        self._parsed_cache = self._pool_map(
            parse_focus_file, [(f, self.mod_path) for f in files], chunksize=10
        )
        return self._parsed_cache

    def _build_focus_registry(
        self, parsed_files: List[Dict]
    ) -> Tuple[
        Dict[str, List[Tuple[str, int]]], Dict[str, Tuple[str, int, List[List[str]]]]
    ]:
        """Build two lookup structures from parsed data.

        Returns:
          all_focuses   — focus_id -> list of (filepath, line)  (for dup detection)
          focus_info    — focus_id -> (filepath, line, prereq_groups)  (first seen)
        """
        all_focuses: Dict[str, List[Tuple[str, int]]] = defaultdict(list)
        focus_info: Dict[str, Tuple[str, int, List[List[str]]]] = {}

        for parsed in parsed_files:
            fp = parsed["filepath"]
            # shared focus definitions
            for sfid, sdata in parsed["shared_defs"].items():
                all_focuses[sfid].append((fp, sdata["line"]))
                if sfid not in focus_info:
                    focus_info[sfid] = (fp, sdata["line"], sdata["prereq_groups"])
            # focuses inside trees
            for tree in parsed["trees"]:
                for focus_id, line, prereq_groups in tree["focuses"]:
                    all_focuses[focus_id].append((fp, line))
                    if focus_id not in focus_info:
                        focus_info[focus_id] = (fp, line, prereq_groups)

        return all_focuses, focus_info

    # -----------------------------------------------------------------------
    # Check 1: Duplicate focus IDs
    # -----------------------------------------------------------------------

    def validate_duplicate_focus_ids(self):
        self._log_section("Checking for duplicate focus IDs...")

        parsed = self._get_parsed_files()
        all_focuses, _ = self._build_focus_registry(parsed)

        results = []
        for focus_id, locations in sorted(all_focuses.items()):
            if len(locations) < 2:
                continue
            if not any(self._is_reportable(fp) for fp, _ in locations):
                continue
            loc_strs = ", ".join(
                f"{os.path.relpath(fp, self.mod_path)}:{ln}" for fp, ln in locations
            )
            results.append(
                (
                    f"Duplicate focus ID '{focus_id}' defined {len(locations)} times: {loc_strs}",
                    os.path.relpath(locations[0][0], self.mod_path),
                    locations[0][1],
                )
            )

        self._report(
            results,
            "No duplicate focus IDs found",
            "Duplicate focus IDs (second definition overwrites the first):",
            Severity.ERROR,
            category="duplicate-focus-id",
        )

    # -----------------------------------------------------------------------
    # Check 2: Orphan focuses
    # -----------------------------------------------------------------------

    def validate_orphan_focuses(self):
        self._log_section(
            "Checking for orphan focuses (missing prerequisite targets in tree)..."
        )

        parsed = self._get_parsed_files()
        # Build global set of all defined focus IDs for missing-prereq resolution
        _, focus_info = self._build_focus_registry(parsed)
        all_defined: FrozenSet[str] = frozenset(focus_info.keys())

        results = []
        for pf in parsed:
            fp = pf["filepath"]
            if not self._is_reportable(fp):
                continue
            rel = os.path.relpath(fp, self.mod_path)
            for tree in pf["trees"]:
                # The IDs in this tree (NOT counting shared refs)
                tree_ids: Set[str] = {f[0] for f in tree["focuses"]}
                # Include shared focuses referenced into this tree
                effective_ids = tree_ids | tree["shared_refs"]

                for focus_id, line, prereq_groups in tree["focuses"]:
                    if not prereq_groups:
                        continue  # root focus — no prerequisites
                    # A focus is orphaned if ANY prerequisite block is entirely
                    # unsatisfied (none of its focus alternatives exist in the tree).
                    for group in prereq_groups:
                        group_satisfied = any(fid in effective_ids for fid in group)
                        if not group_satisfied:
                            # Also check if ALL alternatives are simply missing
                            # from the entire mod (that's a missing-prereq bug,
                            # not an orphan bug — only report orphan here when at
                            # least one alternative actually exists somewhere).
                            all_missing_globally = all(
                                fid not in all_defined for fid in group
                            )
                            if all_missing_globally:
                                # Will be caught by missing-prerequisite check; skip.
                                continue
                            results.append(
                                (
                                    f"Orphan focus '{focus_id}': prerequisite group {group} not present in tree",
                                    rel,
                                    line,
                                )
                            )
                            break  # one report per focus is enough

        self._report(
            results,
            "No orphan focuses found",
            "Orphan focuses (prerequisite group not found in same tree):",
            Severity.WARNING,
            category="orphan-focus",
        )

    # -----------------------------------------------------------------------
    # Check 3: Missing prerequisite targets
    # -----------------------------------------------------------------------

    def validate_missing_prerequisite_targets(self):
        self._log_section(
            "Checking for prerequisite targets that don't exist anywhere in the mod..."
        )

        parsed = self._get_parsed_files()
        _, focus_info = self._build_focus_registry(parsed)
        all_defined: FrozenSet[str] = frozenset(focus_info.keys())
        defined_ci = casefold_index(all_defined)

        results = []
        seen_missing: Set[str] = set()
        for pf in parsed:
            fp = pf["filepath"]
            if not self._is_reportable(fp):
                continue
            rel = os.path.relpath(fp, self.mod_path)
            # Check shared focus defs
            for sfid, sdata in pf["shared_defs"].items():
                for group in sdata["prereq_groups"]:
                    for prereq_id in group:
                        if (
                            prereq_id not in all_defined
                            and prereq_id not in seen_missing
                        ):
                            seen_missing.add(prereq_id)
                            canonical = case_mismatch(prereq_id, defined_ci)
                            if canonical:
                                results.append(
                                    (
                                        f"Missing prerequisite target '{prereq_id}' (referenced by '{sfid}')"
                                        f": case-mismatch reference '{prereq_id}' — defined as '{canonical}'"
                                        " (works on Windows, fails on Linux)",
                                        rel,
                                        sdata["line"],
                                    )
                                )
                            else:
                                results.append(
                                    (
                                        f"Missing prerequisite target '{prereq_id}' (referenced by '{sfid}')",
                                        rel,
                                        sdata["line"],
                                    )
                                )
            # Check focuses inside trees
            for tree in pf["trees"]:
                for focus_id, line, prereq_groups in tree["focuses"]:
                    for group in prereq_groups:
                        for prereq_id in group:
                            if (
                                prereq_id not in all_defined
                                and prereq_id not in seen_missing
                            ):
                                seen_missing.add(prereq_id)
                                canonical = case_mismatch(prereq_id, defined_ci)
                                if canonical:
                                    results.append(
                                        (
                                            f"Missing prerequisite target '{prereq_id}' (referenced by '{focus_id}')"
                                            f": case-mismatch reference '{prereq_id}' — defined as '{canonical}'"
                                            " (works on Windows, fails on Linux)",
                                            rel,
                                            line,
                                        )
                                    )
                                else:
                                    results.append(
                                        (
                                            f"Missing prerequisite target '{prereq_id}' (referenced by '{focus_id}')",
                                            rel,
                                            line,
                                        )
                                    )

        self._report(
            results,
            "No missing prerequisite targets found",
            "Missing prerequisite targets (focus ID not defined anywhere — likely a typo):",
            Severity.ERROR,
            category="missing-prerequisite",
        )

    # -----------------------------------------------------------------------
    # Check 4: Missing localisation keys
    # -----------------------------------------------------------------------

    def validate_missing_loc_keys(self):
        self._log_section(
            "Checking for missing localisation keys (focus ID and _desc)..."
        )

        parsed = self._get_parsed_files()
        _, focus_info = self._build_focus_registry(parsed)

        # Load all English loc keys (always full repo scan)
        loc_keys = self._load_localisation_keys()
        self.log(
            f"  Found {len(focus_info)} focuses, {len(loc_keys)} localisation keys"
        )

        results = []
        for focus_id, (fp, line, _) in sorted(focus_info.items()):
            if not self._is_reportable(fp):
                continue
            rel = os.path.relpath(fp, self.mod_path)
            missing_keys = []
            if focus_id not in loc_keys:
                missing_keys.append(focus_id)
            desc_key = f"{focus_id}_desc"
            if desc_key not in loc_keys:
                missing_keys.append(desc_key)
            for key in missing_keys:
                results.append(
                    (
                        f"Missing loc key '{key}' for focus '{focus_id}'",
                        rel,
                        line,
                    )
                )

        self._report(
            results,
            "No missing localisation keys found",
            "Focuses with missing localisation keys (may use inline name= override — verify before fixing):",
            Severity.WARNING,
            category="missing-loc-key",
        )

    # -----------------------------------------------------------------------
    # Check 5: Dependency cycles
    # -----------------------------------------------------------------------

    def validate_dependency_cycles(self):
        self._log_section("Checking for dependency cycles in prerequisite chains...")

        parsed = self._get_parsed_files()

        results = []
        for pf in parsed:
            fp = pf["filepath"]
            if not self._is_reportable(fp):
                continue
            rel = os.path.relpath(fp, self.mod_path)
            for tree in pf["trees"]:
                # Build adjacency: focus_id -> set of direct prerequisite IDs
                # (flatten OR-groups — for cycle detection any edge matters)
                tree_ids: Set[str] = {f[0] for f in tree["focuses"]}
                adjacency: Dict[str, Set[str]] = {fid: set() for fid in tree_ids}
                id_to_line: Dict[str, int] = {}

                for focus_id, line, prereq_groups in tree["focuses"]:
                    id_to_line[focus_id] = line
                    for group in prereq_groups:
                        for prereq_id in group:
                            if prereq_id in tree_ids:
                                adjacency[focus_id].add(prereq_id)

                # DFS cycle detection
                WHITE, GRAY, BLACK = 0, 1, 2
                color: Dict[str, int] = {fid: WHITE for fid in tree_ids}
                stack: List[str] = []

                def dfs(node: str) -> Optional[List[str]]:
                    color[node] = GRAY
                    stack.append(node)
                    for neighbor in adjacency.get(node, set()):
                        if color[neighbor] == GRAY:
                            # Found a cycle — extract it from the stack
                            cycle_start = stack.index(neighbor)
                            return stack[cycle_start:] + [neighbor]
                        if color[neighbor] == WHITE:
                            cycle = dfs(neighbor)
                            if cycle:
                                return cycle
                    stack.pop()
                    color[node] = BLACK
                    return None

                reported_cycles: Set[FrozenSet] = set()
                for fid in tree_ids:
                    if color[fid] == WHITE:
                        cycle = dfs(fid)
                        if cycle:
                            cycle_key = frozenset(cycle)
                            if cycle_key not in reported_cycles:
                                reported_cycles.add(cycle_key)
                                cycle_str = " -> ".join(cycle)
                                line = id_to_line.get(cycle[0], 0)
                                results.append(
                                    (
                                        f"Dependency cycle detected: {cycle_str}",
                                        rel,
                                        line,
                                    )
                                )

        self._report(
            results,
            "No dependency cycles found",
            "Dependency cycles in prerequisite chains:",
            Severity.ERROR,
            category="dependency-cycle",
        )

    # -----------------------------------------------------------------------
    # Entry point
    # -----------------------------------------------------------------------

    def validate_focus_icons(self):
        """Flag focuses whose `icon = X` sprite is not defined.

        A focus icon resolves verbatim to a spriteType named exactly `X` (MD
        uses bare names like `money` as well as `GFX_`-prefixed ones). When no
        such sprite exists in any interface/*.gfx (mod or vanilla) the focus
        shows a placeholder icon.
        """
        self._log_section("Checking for focuses with missing icons...")

        # Built sequentially (no pool_map): a sub-second scan that can't be left
        # empty by a 'spawn' pool worker that fails to start. An empty index
        # would otherwise flag every focus icon as missing.
        sprites = build_sprite_index(self.mod_path, gfx_only=False)
        if len(sprites) < 1000:
            self.log(
                f"  Only {len(sprites)} GFX sprites loaded — sprite definitions "
                "did not load; skipping the icon check",
                "warning",
            )
            return
        files = self._collect_files(["common/national_focus/*.txt"], ignore_staged=True)
        icon_lists = self._pool_map(
            _extract_focus_icons, [(f, self.mod_path) for f in files]
        )

        results = []
        for sub in icon_lists:
            for focus_id, icon, fp, line in sub:
                if icon in sprites:
                    continue
                if not self._is_reportable(fp):
                    continue
                rel = os.path.relpath(fp, self.mod_path)
                results.append(
                    (f"Missing icon sprite '{icon}' for focus '{focus_id}'", rel, line)
                )

        self._report(
            results,
            "No missing focus icons found",
            "Focuses with missing icons (icon sprite not defined in interface/*.gfx):",
            Severity.WARNING,
            category="missing-focus-icon",
        )

    def run_validations(self):
        self.validate_duplicate_focus_ids()
        self.validate_missing_prerequisite_targets()
        self.validate_orphan_focuses()
        self.validate_dependency_cycles()
        self.validate_missing_loc_keys()

        if self.missing_icons:
            self.validate_focus_icons()
        else:
            self._log_section(
                "Skipping missing icon check (pass --missing-icons to enable)"
            )


def _add_extra_args(parser):
    parser.add_argument(
        "--missing-icons",
        action="store_true",
        dest="missing_icons",
        help="Flag focuses whose icon sprite is undefined in interface/*.gfx",
    )


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate focus tree structure in Millennium Dawn mod",
        extra_args_fn=_add_extra_args,
    )
