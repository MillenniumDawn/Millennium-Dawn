#!/usr/bin/env python3
##########################
# Focus Tree Structural Validation Script
# Validates focus tree definitions for structural integrity
# Checks for:
#   1. Duplicate focus IDs across all files
#   2. Orphan focuses (prerequisite targets not found in the same tree)
#   3. Missing prerequisite targets (referenced focus IDs not defined anywhere)
#   4. Missing localisation keys (focus ID and focus ID_desc)
#   5. Dependency cycles in prerequisite chains
##########################
import os
import re
from collections import defaultdict
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

from validator_common import (
    BaseValidator,
    Colors,
    Severity,
    run_validator_main,
    should_skip_file,
    strip_comments,
)

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Opening of a focus_tree or top-level focus definition block
# (shared_focus and joint_focus are both standalone definitions that can be
# referenced as prerequisites — they live outside any focus_tree wrapper)
_FOCUS_TREE_START = re.compile(r"\bfocus_tree\s*=\s*\{")
_SHARED_FOCUS_DEF_START = re.compile(r"\b(?:shared_focus|joint_focus)\s*=\s*\{")

# focus ID extraction
_FOCUS_ID_RE = re.compile(r"\bfocus\s*=\s*\{")
_ID_LINE_RE = re.compile(r"\bid\s*=\s*(\S+)")

# prerequisite blocks: prerequisite = { focus = A  focus = B }
_PREREQ_BLOCK_RE = re.compile(r"\bprerequisite\s*=\s*\{([^}]*)\}", re.DOTALL)
_PREREQ_FOCUS_RE = re.compile(r"\bfocus\s*=\s*(\S+)")

# shared_focus reference inside a focus_tree block (not a definition)
_SHARED_REF_RE = re.compile(r"\bshared_focus\s*=\s*(\w+)")


# ---------------------------------------------------------------------------
# Per-file parsing (pool workers)
# ---------------------------------------------------------------------------


def _extract_block(text: str, start: int) -> Tuple[str, int]:
    """Return the content between the first { after *start* and its matching },
    and the position right after the closing }.  Returns ("", start) on failure."""
    open_pos = text.find("{", start)
    if open_pos == -1:
        return "", start
    depth = 1
    i = open_pos + 1
    while i < len(text) and depth > 0:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        i += 1
    if depth != 0:
        return "", start
    return text[open_pos + 1 : i - 1], i


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


def parse_focus_file(
    filepath: str,
) -> Dict:
    """Parse one focus tree file and return a structured result dict.

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
    try:
        with open(filepath, "r", encoding="utf-8-sig", errors="ignore") as fh:
            raw = fh.read()
    except Exception:
        return result

    text = strip_comments(raw)

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


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------


class Validator(BaseValidator):
    TITLE = "FOCUS TREE STRUCTURAL VALIDATION"
    STAGED_EXTENSIONS = [".txt", ".yml"]

    def __init__(self, mod_path: str, **kwargs):
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
        self._parsed_cache = self._pool_map(parse_focus_file, files, chunksize=10)
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

    def run_validations(self):
        self.validate_duplicate_focus_ids()
        self.validate_missing_prerequisite_targets()
        self.validate_orphan_focuses()
        self.validate_dependency_cycles()
        self.validate_missing_loc_keys()


if __name__ == "__main__":
    run_validator_main(
        Validator, "Validate focus tree structure in Millennium Dawn mod"
    )
