#!/usr/bin/env python3
"""Validate shipped file paths for cross-platform load and checksum divergence.

Windows resolves paths case-insensitively and Linux does not, so a mod file whose
path differs from a vanilla one only in case replaces it on Windows but loads
beside it on Linux. The two platforms then checksum different file sets and
cannot play multiplayer together.
"""

import os
import re
import subprocess
import sys
from typing import Dict, Iterator, List, Optional, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared_utils import find_hoi4_install
from validator_common import (
    BaseValidator,
    Severity,
    case_mismatch,
    casefold_index,
    run_validator_main,
)

CONTENT_ROOTS = (
    "common",
    "descriptions",
    "events",
    "gfx",
    "history",
    "interface",
    "localisation",
    "map",
    "music",
    "portraits",
    "scenario_tests",
    "sound",
    "tutorial",
)

_ROOT_PREFIXES = tuple(f"{root}/" for root in CONTENT_ROOTS)

_MANIFEST = os.path.join(os.path.dirname(__file__), "vanilla_paths.txt")

_REPLACE_PATH_RE = re.compile(r'replace_path\s*=\s*"([^"]+)"')

_WINDOWS_ILLEGAL = re.compile(r'[<>:"|?*\x00-\x1f]')
_WINDOWS_RESERVED = (
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{i}" for i in range(1, 10)}
    | {f"LPT{i}" for i in range(1, 10)}
)


def parse_checksum_manifest(text: str) -> List[Tuple[str, str, bool]]:
    """Parse checksum_manifest.txt into (directory, extension, recurse) rules.

    The game ships this file in its root; it is the authoritative list of what
    the multiplayer checksum covers, so anything outside it can differ between
    platforms without breaking cross-platform play.
    """
    rules: List[Tuple[str, str, bool]] = []
    name: Optional[str] = None
    recurse = True
    for raw in text.splitlines():
        line = raw.strip()
        if line == "directory":
            name, recurse = None, True
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if key == "name":
            name = value
        elif key == "sub_directories":
            recurse = value == "yes"
        elif key == "file_extension" and name:
            rules.append((name, value.lower(), recurse))
    return rules


def vanilla_content_roots(install: str) -> Iterator[str]:
    """The install root plus every DLC root, each holding its own common/, map/, ..."""
    yield install
    for group in ("dlc", "integrated_dlc"):
        base = os.path.join(install, group)
        if not os.path.isdir(base):
            continue
        for name in sorted(os.listdir(base)):
            path = os.path.join(base, name)
            if os.path.isdir(path):
                yield path


def collect_vanilla_paths(install: str) -> Set[str]:
    try:
        with open(
            os.path.join(install, "checksum_manifest.txt"), encoding="utf-8-sig"
        ) as fh:
            rules = parse_checksum_manifest(fh.read())
    except (OSError, UnicodeDecodeError):
        return set()

    paths: Set[str] = set()
    for root in vanilla_content_roots(install):
        for name, extension, recurse in rules:
            top = os.path.join(root, name)
            if not os.path.isdir(top):
                continue
            for dirpath, dirnames, filenames in os.walk(top):
                if not recurse:
                    dirnames.clear()
                relative = os.path.relpath(dirpath, root).replace(os.sep, "/")
                paths.update(
                    f"{relative}/{fn}"
                    for fn in filenames
                    if fn.lower().endswith(extension)
                )
    return paths


def load_paths_manifest() -> Set[str]:
    # UnicodeDecodeError too: a corrupt manifest must read as absent (loud setup
    # error) rather than crash the validator.
    try:
        with open(_MANIFEST, encoding="utf-8") as fh:
            return {
                line.strip() for line in fh if line.strip() and not line.startswith("#")
            }
    except (OSError, UnicodeDecodeError):
        return set()


def tracked_content_paths(mod_path: str) -> Optional[List[str]]:
    """Tracked repo-relative paths under the directories HOI4 loads.

    Reads the git index rather than the filesystem so the check still sees every
    shipped path under a sparse checkout, where most of the tree is absent.
    """
    try:
        result = subprocess.run(
            ["git", "-C", mod_path, "ls-files", "-z"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return [
        path for path in result.stdout.split("\0") if path.startswith(_ROOT_PREFIXES)
    ]


def replaced_dirs(mod_path: str) -> Set[str]:
    """Directories descriptor.mod hides from vanilla, where a case clash is inert.

    replace_path is not recursive — MD lists `common/decisions` and
    `common/decisions/categories` separately — so these match a parent directory
    exactly, never as a prefix.
    """
    try:
        with open(os.path.join(mod_path, "descriptor.mod"), encoding="utf-8-sig") as fh:
            text = fh.read()
    except (OSError, UnicodeDecodeError):
        return set()
    return {m.group(1).strip("/") for m in _REPLACE_PATH_RE.finditer(text)}


def case_collision_groups(paths) -> List[List[str]]:
    """Groups of paths that only a case-insensitive filesystem would merge."""
    buckets: Dict[str, List[str]] = {}
    for path in paths:
        buckets.setdefault(path.lower(), []).append(path)
    return sorted(sorted(g) for g in buckets.values() if len(g) > 1)


def windows_name_problem(path: str) -> Optional[str]:
    """Why Windows cannot check this path out, or None when it can."""
    for part in path.split("/"):
        illegal = _WINDOWS_ILLEGAL.search(part)
        if illegal:
            return f"contains {illegal.group()!r}, which Windows forbids in a name"
        if part != part.rstrip(" ."):
            return "ends in a space or dot, which Windows silently strips"
        stem = part.partition(".")[0].upper()
        if stem in _WINDOWS_RESERVED:
            return f"uses the reserved device name {stem}"
    return None


class Validator(BaseValidator):
    TITLE = "FILE PATH VALIDATION"

    def run_validations(self):
        paths = tracked_content_paths(self.mod_path)
        if paths is None:
            self.add_error(
                "paths-setup",
                "git ls-files failed — the check needs the repository, not a copy "
                "of the working tree",
            )
            return

        # An unreadable descriptor would read as "nothing is replaced" and turn
        # every inert case clash into a blocking error.
        if not os.path.isfile(os.path.join(self.mod_path, "descriptor.mod")):
            self.add_error(
                "paths-setup",
                "descriptor.mod not found — its replace_path directives decide "
                "which case clashes actually diverge",
            )
            return

        install = find_hoi4_install()
        vanilla = collect_vanilla_paths(install) if install else set()
        source = install
        if not vanilla:
            vanilla, source = load_paths_manifest(), "vanilla_paths.txt manifest"
        if not vanilla:
            self.add_error(
                "paths-setup",
                "No vanilla path list: install HOI4 via Steam, set $HOI4_PATH, or "
                "regenerate vanilla_paths.txt with refresh_vanilla_data.py "
                "on a machine with the game.",
            )
            return

        self.log(f"  Vanilla paths: {source} ({len(vanilla)} checksummed)")
        self.log(f"  Mod content paths: {len(paths)}")

        self._check_vanilla_collisions(paths, vanilla)
        self._check_internal_collisions(paths)
        self._check_windows_hostile_names(paths)

    def _check_vanilla_collisions(self, paths: List[str], vanilla: Set[str]):
        self._log_section("Checking mod paths against vanilla...")
        replaced = replaced_dirs(self.mod_path)
        file_index = casefold_index(vanilla)
        dir_index = casefold_index({os.path.dirname(p) for p in vanilla})

        diverging, inert = [], []
        for path in paths:
            canonical = case_mismatch(path, file_index)
            if canonical is None:
                continue
            target = inert if os.path.dirname(path) in replaced else diverging
            target.append((f"differs only in case from vanilla {canonical}", path, 0))

        for directory in sorted({os.path.dirname(p) for p in paths}):
            canonical = case_mismatch(directory, dir_index)
            if canonical is not None:
                diverging.append(
                    (
                        f"directory differs only in case from vanilla {canonical}, so "
                        "Linux never loads what it holds",
                        directory,
                        0,
                    )
                )

        self._report(
            diverging,
            "✓ No mod path collides with a vanilla path by case alone",
            "Paths differing from vanilla only in case (Windows overrides it, Linux "
            "loads both — multiplayer checksum mismatch):",
            category="vanilla-path-case",
        )
        self._report(
            inert,
            "✓ No case collision hides inside a replace_path'd directory",
            "Paths differing from vanilla only in case inside a replace_path'd "
            "directory (inert while the replace_path stands):",
            severity=Severity.WARNING,
            category="vanilla-path-case-replaced",
        )

    def _check_internal_collisions(self, paths: List[str]):
        self._log_section("Checking for case collisions inside the mod...")
        results = [
            (f"tracked paths differ only in case: {', '.join(group)}", group[0], 0)
            for group in case_collision_groups(paths)
        ]
        results += [
            (
                f"tracked directories differ only in case: {', '.join(group)}",
                group[0],
                0,
            )
            for group in case_collision_groups({os.path.dirname(p) for p in paths})
        ]
        self._report(
            results,
            "✓ No two tracked paths differ only in case",
            "Paths a case-insensitive checkout would merge (Windows and macOS "
            "clones lose one of them):",
            category="internal-path-case",
        )

    def _check_windows_hostile_names(self, paths: List[str]):
        self._log_section("Checking for names Windows cannot check out...")
        results = []
        for path in paths:
            problem = windows_name_problem(path)
            if problem:
                results.append((problem, path, 0))
        self._report(
            results,
            "✓ Every tracked name is checkout-safe on Windows",
            "Names Windows cannot check out (the file is missing there, so the "
            "checksum differs):",
            category="windows-hostile-name",
        )


if __name__ == "__main__":
    run_validator_main(
        Validator, "Validate mod file paths for cross-platform divergence"
    )
