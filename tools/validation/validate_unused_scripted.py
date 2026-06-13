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
from validator_common import (
    HOI4_BUILTIN_BLOCKS,
    BaseValidator,
    Severity,
    run_validator_main,
    should_skip_file,
    strip_comments,
)

# Patterns for known false positives — these are referenced by the game engine,
# called dynamically, or serve as convention-based callbacks rather than being
# explicitly invoked via `name = yes` in script files.
FALSE_POSITIVE_PATTERNS = [
    re.compile(r"^trigger_year_"),  # Year-based triggers, engine-referenced
    re.compile(
        r"^EU_update_AI_focus_.*_voting_modifier$"
    ),  # EU voting AI, dynamically called
    re.compile(r"_accepted$"),  # Focus accepted callbacks (engine convention)
    re.compile(
        r"^DIPLOMACY_.*_ENABLE_TRIGGER"
    ),  # Game rule triggers, engine-referenced
    re.compile(
        r"^is_diplomatic_action_valid_"
    ),  # Diplo-action validity gates, engine-referenced by action token
    re.compile(
        r"^_unlock_btn_enabled$"
    ),  # MIO catalog meta-dispatch empty-token-key fallback
]

# Files whose definitions are entirely engine-referenced (all contents are false positives)
FALSE_POSITIVE_FILES = frozenset(
    {
        "00_game_rule_triggers.txt",
        # Internal faction opinion triggers — a convention-based preset library
        # (enthusiastic_X / positive_X / indifferent_X / negative_X / hostile_X
        # for every internal faction). Kept fully populated so any content that
        # wants to check a faction mood level has a ready-made trigger, even if
        # many are not currently referenced anywhere in the mod.
        "00_internal_factions_trigger.txt",
    }
)


# Regex: identifier containing at least one [VAR] placeholder with a non-empty
# constant prefix (e.g. "set_leader_[IDEOLOGY]", "tooltip_EU_[EUXXX]_approve").
# Requires a non-empty prefix so pure "[VAR]" expansions (like "[TECH] = 1") are
# excluded — those don't call scripted effects/triggers by constructed name.
_TEMPLATE_RE = re.compile(
    r"(?<![/\"])\b([A-Za-z_][A-Za-z0-9_.]*(?:\[[A-Za-z_][A-Za-z0-9_]*\][A-Za-z0-9_.]*)+"
    r")"
)

# Regex: quoted meta-substitution value carrying the constant anchor, where the
# placeholder may lead (e.g. `TRIG = "[?global.tokens^v.GetTokenKey]_unlock_btn_enabled"`).
# Here the `text` block holds a bare `[TRIG] = yes` and the real prefix/suffix lives
# in the quoted assignment, so a leading placeholder with only a trailing constant
# must still resolve. The suffix anchor keeps the match from over-firing.
_QUOTED_TEMPLATE_RE = re.compile(r'"([^"]*\[[^\]]+\][^"]*)"')


def scan_for_meta_constructed_names(
    files: List[str], defined_names: Set[str]
) -> Set[str]:
    """Return the subset of *defined_names* that are called via meta_effect/
    meta_trigger template substitution (e.g. ``set_leader_[IDEOLOGY] = yes``).

    For every file that contains a ``meta_effect`` or ``meta_trigger`` keyword,
    we extract identifier templates of the form ``prefix_[VAR]_suffix``, split
    them on ``[VAR]`` segments to recover the constant (prefix, suffix) pair,
    and match any defined name whose lower-cased form starts with *prefix* and
    ends with *suffix*.
    """
    defined_lower = {n.lower(): n for n in defined_names}
    used: Set[str] = set()

    for filepath in files:
        try:
            with open(filepath, "r", encoding="utf-8-sig") as fh:
                content = fh.read()
        except Exception:
            continue

        if "meta_effect" not in content and "meta_trigger" not in content:
            continue

        content_clean = strip_comments(content)

        templates = [m.group(1) for m in _TEMPLATE_RE.finditer(content_clean)]
        templates += [m.group(1) for m in _QUOTED_TEMPLATE_RE.finditer(content_clean)]

        for template in templates:
            # Split on every [VAR] segment — constant parts become prefix/suffix
            parts = re.split(r"\[[^\]]+\]", template)
            prefix = parts[0].lower()
            suffix = parts[-1].lower() if len(parts) > 1 else ""

            # Skip pure-placeholder templates where no constant anchors the match
            if not prefix and not suffix:
                continue

            for name_lower, name_orig in defined_lower.items():
                if name_orig in used:
                    continue
                if name_lower.startswith(prefix) and name_lower.endswith(suffix):
                    # Guard: VAR must resolve to something non-empty
                    if len(name_lower) > len(prefix) + len(suffix):
                        used.add(name_orig)

    return used


def _is_false_positive(name: str, filepath: str) -> bool:
    """Check if a definition name is a known false positive."""
    basename = os.path.basename(filepath)
    if basename in FALSE_POSITIVE_FILES:
        return True
    for pattern in FALSE_POSITIVE_PATTERNS:
        if pattern.search(name):
            return True
    return False


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
            files = [f for f in files if not should_skip_file(f)]
            staged_set = set(self.staged_files)
            files = [f for f in files if f in staged_set]
        else:
            files = self._collect_files([f"common/{subdir}/**/*.txt"])

        args_list = [(f, self.mod_path) for f in files]
        all_results = self._pool_map(extract_definitions, args_list, chunksize=10)

        definitions = []
        for result in all_results:
            definitions.extend(result)

        return definitions

    def _find_unused(
        self, definitions: List[Tuple[str, str, int]], kind: str, def_subdir: str
    ) -> List[str]:
        """Find definitions that are never used outside their own definition.

        For each definition, we check if the name appears in ANY file outside
        the definition directory. We also check if it's used within the same
        directory but in a different definition block (i.e., called by another
        scripted effect/trigger).
        """
        if not definitions:
            return []

        # Build a set of all definition names
        all_names = {d[0] for d in definitions}

        # Scan all txt files for usages
        all_files = self._collect_files(
            [
                "common/**/*.txt",
                "events/**/*.txt",
                "history/**/*.txt",
            ]
        )

        # Split files into "definition files" and "other files"
        def_dir = f"common/{def_subdir}/"
        other_files, def_files = [], []
        for f in all_files:
            (def_files if def_dir in f.replace("\\", "/") else other_files).append(f)

        # First pass: find all names used in non-definition files
        args_list = [(f, all_names, self.mod_path) for f in other_files]
        results = self._pool_map(scan_file_for_usages, args_list)

        used_names = set()
        for found in results:
            used_names.update(found)

        # Second pass: for names not yet found, check if they're used
        # within definition files (called by other scripted effects/triggers)
        remaining = all_names - used_names
        if remaining:
            args_list = [(f, remaining, self.mod_path) for f in def_files]
            results = self._pool_map(scan_file_for_usages, args_list, chunksize=10)

            # For each name found in definition files, check if it appears
            # more than just its own definition (i.e., it's called somewhere)
            potentially_used = set()
            for found in results:
                potentially_used.update(found)

            # Read each def file once and check all potentially-used names
            # for call patterns (name = yes/no or custom tooltip references)
            for def_file in def_files:
                try:
                    with open(def_file, "r", encoding="utf-8-sig") as f:
                        content = strip_comments(f.read())
                except Exception:
                    continue
                for name in list(potentially_used - used_names):
                    if name not in content:
                        continue
                    if re.search(rf"\b{re.escape(name)}\s*=\s*(?:yes|no)\b", content):
                        used_names.add(name)
                    elif re.search(
                        rf"custom_(?:effect|trigger)_tooltip\s*=\s*{re.escape(name)}\b",
                        content,
                    ):
                        used_names.add(name)

        # Build results for unused definitions
        unused = []
        # Build a lookup: name -> (file, line_number)
        name_to_location = {}
        for name, filepath, line_num in definitions:
            if name not in name_to_location:
                name_to_location[name] = []
            name_to_location[name].append((filepath, line_num))

        for name in sorted(all_names - used_names):
            locations = name_to_location.get(name, [])
            for filepath, line_num in locations:
                if _is_false_positive(name, filepath):
                    continue
                unused.append(f"{filepath}:{line_num} - {name}")

        return unused

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
        other_files, def_files = [], []
        for f in all_files:
            norm = f.replace("\\", "/")
            if effect_dir in norm or trigger_dir in norm:
                def_files.append(f)
            else:
                other_files.append(f)

        # First pass: find all names used outside definition dirs
        args_list = [(f, all_names, self.mod_path) for f in other_files]
        results = self._pool_map(scan_file_for_usages, args_list)

        used_names: set = set()
        for found in results:
            used_names.update(found)

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
                    with open(def_file, "r", encoding="utf-8-sig") as f:
                        content = strip_comments(f.read())
                except Exception:
                    continue
                for name in list(potentially_used - used_names):
                    if name not in content:
                        continue
                    if re.search(rf"\b{re.escape(name)}\s*=\s*(?:yes|no)\b", content):
                        used_names.add(name)
                    elif re.search(
                        rf"custom_(?:effect|trigger)_tooltip\s*=\s*{re.escape(name)}\b",
                        content,
                    ):
                        used_names.add(name)

        # Third pass: detect names called via meta_effect/meta_trigger template
        # substitution (e.g. `set_leader_[IDEOLOGY] = yes`).  Only scan the
        # names still remaining after the first two passes to keep cost low.
        still_remaining = all_names - used_names
        if still_remaining:
            used_names.update(
                scan_for_meta_constructed_names(all_files, still_remaining)
            )

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

    def validate_unused_effects(self):
        self._log_section("Checking for unused scripted effects...")

    def validate_unused_triggers(self):
        self._log_section("Checking for unused scripted triggers...")

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
