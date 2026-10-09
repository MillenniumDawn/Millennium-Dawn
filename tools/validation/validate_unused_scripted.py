#!/usr/bin/env python3
# Find scripted effects and triggers defined in common/scripted_effects/ and
# common/scripted_triggers/ that are never called anywhere in the mod.
import glob
import os
import re
import sys
from pathlib import Path
from typing import List, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import disk_cache
from shared_utils import validation_config
from validator_common import (
    HOI4_BUILTIN_BLOCKS,
    BaseValidator,
    Severity,
    run_validator_main,
    scan_meta_constructed_names,
    should_skip_file,
    strip_comments,
)

# A name counts as "called" when it appears as `name = yes/no` or as a
# custom_(effect|trigger)_tooltip target. Extracting every such token from a
# def-file once and testing set membership is equivalent to the old per-name
# `\bname\s*=\s*(?:yes|no)\b` search (same word boundaries, same identifier
# capture) but avoids compiling a pattern per (name, file) — millions of calls.
_CALL_YES_NO_RE = re.compile(r"\b([A-Za-z_]\w*)\s*=\s*(?:yes|no)\b")
_CUSTOM_TT_REF_RE = re.compile(
    r"custom_(?:effect|trigger)_tooltip\s*=\s*([A-Za-z_]\w*)\b"
)

FALSE_POSITIVE_PATTERNS = [
    re.compile(p)
    for p in validation_config("validate_unused_scripted", "false_positive_patterns")
]
FALSE_POSITIVE_NAMES = frozenset(
    validation_config("validate_unused_scripted", "false_positive_names")
)
PENDING_IMPLEMENTATION_NAMES = frozenset(
    validation_config("validate_unused_scripted", "pending_implementation_names")
)
FALSE_POSITIVE_FILES = frozenset(
    validation_config("validate_unused_scripted", "false_positive_files")
)


def _is_false_positive(name: str, filepath: str) -> bool:
    """Check if a definition name is a known false positive."""
    if os.path.basename(filepath) in FALSE_POSITIVE_FILES:
        return True
    if name in FALSE_POSITIVE_NAMES or name in PENDING_IMPLEMENTATION_NAMES:
        return True
    return any(pattern.search(name) for pattern in FALSE_POSITIVE_PATTERNS)


def extract_definitions(args: Tuple[str, str]) -> List[Tuple[str, str, int]]:
    """Extract top-level scripted effect/trigger definitions from a file.

    Returns list of (name, filename, line_number) tuples.
    """
    filename, mod_path = args

    try:
        with open(filename, "r", encoding="utf-8-sig") as f:
            content = f.read()
    except Exception:
        return []

    def _compute():
        results = []
        clean_content = strip_comments(content)

        # Find top-level definitions by tracking brace depth
        lines = clean_content.split("\n")
        brace_depth = 0
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped:
                continue

            # Only match definitions at brace depth 0 (top level)
            if brace_depth == 0:
                m = re.match(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\{", stripped)
                if m:
                    name = m.group(1)
                    if name not in HOI4_BUILTIN_BLOCKS:
                        rel_path = os.path.relpath(filename, mod_path)
                        results.append((name, rel_path, line_num))

            # Track brace depth
            brace_depth += stripped.count("{") - stripped.count("}")

        return results

    return disk_cache.per_file_cached_by_content(
        mod_path, "unused_scripted.definitions", filename, content, _compute
    )


def scan_file_for_usages(args: Tuple[str, Set[str], str]) -> Set[str]:
    """Scan a file for usages of any of the given names.

    A usage is when a name appears as a whole word — guarded by
    word boundaries so ``foo_bar`` does not spuriously mark ``foo``
    or ``bar`` as used. This is a fast pre-filter; callers still
    verify call-site syntax (``name = yes/no`` or
    ``custom_effect_tooltip = name``) before trusting the hit for
    definition-directory files.
    """
    filename, names_to_find, mod_path = args

    try:
        with open(filename, "r", encoding="utf-8-sig") as f:
            content = f.read()
    except Exception:
        return set()

    # Cache the content-dependent token extraction (the expensive part); the
    # intersection with names_to_find is cheap and varies per call, so it stays
    # outside the cache.
    def _compute():
        cleaned = strip_comments(content)
        # Collect every identifier-like token in the file once, then intersect.
        # Cheaper than running a word-boundary regex per name when names_to_find
        # is large.
        return set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", cleaned))

    tokens = disk_cache.per_file_cached_by_content(
        mod_path, "unused_scripted.tokens", filename, content, _compute
    )
    return names_to_find & tokens


class Validator(BaseValidator):
    TITLE = "UNUSED SCRIPTED EFFECTS & TRIGGERS VALIDATION"
    STAGED_EXTENSIONS = [".txt"]

    def _collect_definitions(self, subdir: str) -> List[Tuple[str, str, int]]:
        """Collect all definitions from a scripted_effects or scripted_triggers directory."""
        search_path = str(Path(self.mod_path) / "common" / subdir)
        if not os.path.isdir(search_path):
            return []

        if self.staged_files:
            files = list(glob.iglob(search_path + "/**/*.txt", recursive=True))
            files = [
                f for f in files if not should_skip_file(f, mod_path=self.mod_path)
            ]
            staged_set = set(self.staged_files)
            files = [f for f in files if f in staged_set]
        else:
            files = self._collect_files([f"common/{subdir}/**/*.txt"])

        args_list = [(f, self.mod_path) for f in files]
        definitions = self._pool_flat_map(extract_definitions, args_list, chunksize=10)

        return definitions

    def _find_unused_combined(
        self,
        effect_defs: List[Tuple[str, str, int]],
        trigger_defs: List[Tuple[str, str, int]],
    ) -> Tuple[List[str], List[str]]:
        """Find unused effects and triggers in a single codebase scan.

        Merges both definition sets and scans the full codebase once instead of
        calling _find_unused() twice (which would scan the codebase twice).
        Returns (unused_effects, unused_triggers).
        """
        all_defs = effect_defs + trigger_defs
        if not all_defs:
            return [], []

        effect_names = {d[0] for d in effect_defs}
        trigger_names = {d[0] for d in trigger_defs}
        all_names = effect_names | trigger_names

        all_files = self._collect_files(
            [
                "common/**/*.txt",
                "events/**/*.txt",
                "history/**/*.txt",
            ]
        )

        # Split files into definition files and other files
        effect_dir = "common/scripted_effects/"
        trigger_dir = "common/scripted_triggers/"
        other_files: List[str] = []
        def_files: List[str] = []
        for f in all_files:
            norm = f.replace("\\", "/")
            if effect_dir in norm or trigger_dir in norm:
                def_files.append(f)
            else:
                other_files.append(f)

        # First pass: find all names used outside definition dirs
        args_list = [(f, all_names, self.mod_path) for f in other_files]
        used_names = set(self._pool_flat_map(scan_file_for_usages, args_list))

        # Second pass: check cross-calls within definition files
        remaining = all_names - used_names
        if remaining:
            args_list = [(f, remaining, self.mod_path) for f in def_files]
            def_results = self._pool_map(scan_file_for_usages, args_list, chunksize=10)

            potentially_used: set = set()
            for found in def_results:
                potentially_used.update(found)

            for def_file in def_files:
                try:
                    with open(def_file, "r", encoding="utf-8-sig") as definition_file:
                        content = strip_comments(definition_file.read())
                except (OSError, UnicodeError):
                    continue
                called = set(_CALL_YES_NO_RE.findall(content))
                called.update(_CUSTOM_TT_REF_RE.findall(content))
                used_names |= called & potentially_used

        # Third pass: detect names called via meta_effect/meta_trigger template
        # substitution (e.g. `set_leader_[IDEOLOGY] = yes`).  Only scan the
        # names still remaining after the first two passes to keep cost low.
        still_remaining = all_names - used_names
        if still_remaining:
            used_names.update(scan_meta_constructed_names(all_files, still_remaining))

        # Build result lists, partitioned by kind
        name_to_location: dict = {}
        for name, filepath, line_num in all_defs:
            if name not in name_to_location:
                name_to_location[name] = []
            name_to_location[name].append((filepath, line_num))

        unused_effects: List[str] = []
        unused_triggers: List[str] = []
        for name in sorted(all_names - used_names):
            locations = name_to_location.get(name, [])
            for filepath, line_num in locations:
                if _is_false_positive(name, filepath):
                    continue
                entry = f"{filepath}:{line_num} - {name}"
                if name in effect_names:
                    unused_effects.append(entry)
                else:
                    unused_triggers.append(entry)

        return unused_effects, unused_triggers

    def run_validations(self):
        if self.staged_only:
            self.log(
                "Unused scripted check requires full codebase scan — skipping in staged mode",
                "warning",
            )
            return

        effect_defs = self._collect_definitions("scripted_effects")
        trigger_defs = self._collect_definitions("scripted_triggers")
        self.log(
            f"  Found {len(effect_defs)} scripted effect definitions, "
            f"{len(trigger_defs)} scripted trigger definitions"
        )

        # Single codebase scan for both effects and triggers.
        unused_effects, unused_triggers = self._find_unused_combined(
            effect_defs, trigger_defs
        )

        self._report(
            unused_effects,
            "✓ No unused scripted effects found",
            "Unused scripted effects (defined but never called):",
            Severity.WARNING,
            category="unused-scripted-effect",
        )
        self._report(
            unused_triggers,
            "✓ No unused scripted triggers found",
            "Unused scripted triggers (defined but never called):",
            Severity.WARNING,
            category="unused-scripted-trigger",
        )


if __name__ == "__main__":
    run_validator_main(
        Validator, "Find unused scripted effects and triggers in Millennium Dawn mod"
    )
