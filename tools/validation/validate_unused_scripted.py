#!/usr/bin/env python3
##########################
# Unused Scripted Effects & Triggers Validation
# Finds scripted effects and triggers that are defined but never called
# Checks:
#   1. Scripted effects defined in common/scripted_effects/ but never used
#   2. Scripted triggers defined in common/scripted_triggers/ but never used
##########################
import glob
import os
import re
from multiprocessing import Pool
from pathlib import Path
from typing import List, Set, Tuple

from shared_utils import strip_comments
from validator_common import BaseValidator, Colors, run_validator_main, should_skip_file

# Names that are HOI4 built-in blocks and should not be treated as definitions
BUILTIN_BLOCKS = frozenset(
    {
        "if",
        "else",
        "else_if",
        "limit",
        "AND",
        "OR",
        "NOT",
        "hidden_effect",
        "random_list",
        "tooltip",
        "custom_effect_tooltip",
        "custom_trigger_tooltip",
        "modifier",
        "random",
        "every_country",
        "random_country",
        "every_state",
        "random_state",
        "every_owned_state",
        "random_owned_state",
        "every_neighbor_country",
        "random_neighbor_country",
        "every_enemy_country",
        "random_enemy_country",
        "every_other_country",
        "random_other_country",
        "capital_scope",
        "owner",
        "controller",
        "ROOT",
        "PREV",
        "FROM",
        "country_event",
        "news_event",
        "state_event",
        "every_army_leader",
        "random_army_leader",
        "every_unit_leader",
        "random_unit_leader",
        "every_navy_leader",
        "random_navy_leader",
        "every_possible_country",
        "random_possible_country",
        "all_of",
        "any_of",
        "for_each_scope_loop",
        "while_loop_effect",
        "for_loop_effect",
        "effect_tooltip",
        "add_to_array",
        "remove_from_array",
        "overlord",
        "faction_leader",
        "any_country",
        "any_state",
        "any_owned_state",
        "any_neighbor_country",
        "any_enemy_country",
        "any_other_country",
        "any_allied_country",
        "any_country_with_original_tag",
        "any_army_leader",
        "any_navy_leader",
        "any_unit_leader",
        "any_possible_country",
        "every_allied_country",
        "random_allied_country",
        "every_occupied_country",
        "random_occupied_country",
        "any_occupied_country",
        "every_country_with_original_tag",
        "random_country_with_original_tag",
        "meta_effect",
        "meta_trigger",
    }
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
        r"^set_leader_"
    ),  # Called dynamically via meta_effect in election_effects
]

# Files whose definitions are entirely engine-referenced (all contents are false positives)
FALSE_POSITIVE_FILES = frozenset(
    {
        "00_game_rule_triggers.txt",
    }
)


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
    results = []

    try:
        with open(filename, "r", encoding="utf-8-sig") as f:
            content = f.read()
    except Exception:
        return results

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
                if name not in BUILTIN_BLOCKS:
                    rel_path = os.path.relpath(filename, mod_path)
                    results.append((name, rel_path, line_num))

        # Track brace depth
        brace_depth += stripped.count("{") - stripped.count("}")

    return results


def scan_file_for_usages(args: Tuple[str, Set[str]]) -> Set[str]:
    """Scan a file for usages of any of the given names.

    A usage is when a name appears as `name = yes`, `name = no`, or
    as a call inside another block (not as a top-level definition).
    """
    filename, names_to_find = args
    found = set()

    try:
        with open(filename, "r", encoding="utf-8-sig") as f:
            content = f.read()
    except Exception:
        return found

    content = strip_comments(content)

    for name in names_to_find:
        if name in content:
            found.add(name)

    return found


class Validator(BaseValidator):
    TITLE = "UNUSED SCRIPTED EFFECTS & TRIGGERS VALIDATION"
    STAGED_EXTENSIONS = [".txt"]

    def _collect_definitions(self, subdir: str) -> List[Tuple[str, str, int]]:
        """Collect all definitions from a scripted_effects or scripted_triggers directory."""
        search_path = str(Path(self.mod_path) / "common" / subdir)
        if not os.path.isdir(search_path):
            return []

        files = list(glob.iglob(search_path + "/**/*.txt", recursive=True))
        files = [f for f in files if not should_skip_file(f)]

        if self.staged_files:
            staged_set = set(self.staged_files)
            files = [f for f in files if f in staged_set]

        args_list = [(f, self.mod_path) for f in files]
        with Pool(processes=self.workers) as pool:
            all_results = pool.map(extract_definitions, args_list, chunksize=10)

        definitions = []
        for result in all_results:
            definitions.extend(result)

        return definitions

    def _collect_all_txt_files(self) -> List[str]:
        """Collect all .txt files in the mod directory to scan for usages."""
        all_files = []
        for pattern in ["common/**/*.txt", "events/**/*.txt", "history/**/*.txt"]:
            all_files.extend(
                glob.iglob(os.path.join(self.mod_path, pattern), recursive=True)
            )
        return [f for f in all_files if not should_skip_file(f)]

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
        all_files = self._collect_all_txt_files()

        # Split files into "definition files" and "other files"
        def_dir = f"common/{def_subdir}/"
        other_files = [f for f in all_files if def_dir not in f.replace("\\", "/")]
        def_files = [f for f in all_files if def_dir in f.replace("\\", "/")]

        # First pass: find all names used in non-definition files
        args_list = [(f, all_names) for f in other_files]
        with Pool(processes=self.workers) as pool:
            results = pool.map(scan_file_for_usages, args_list, chunksize=50)

        used_names = set()
        for found in results:
            used_names.update(found)

        # Second pass: for names not yet found, check if they're used
        # within definition files (called by other scripted effects/triggers)
        remaining = all_names - used_names
        if remaining:
            args_list = [(f, remaining) for f in def_files]
            with Pool(processes=self.workers) as pool:
                results = pool.map(scan_file_for_usages, args_list, chunksize=10)

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

    def validate_unused_effects(self):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking for unused scripted effects...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        definitions = self._collect_definitions("scripted_effects")
        self.log(f"  Found {len(definitions)} scripted effect definitions")

        unused = self._find_unused(definitions, "effect", "scripted_effects")

        self._report(
            unused,
            "✓ No unused scripted effects found",
            "Unused scripted effects (defined but never called):",
        )

    def validate_unused_triggers(self):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking for unused scripted triggers...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        definitions = self._collect_definitions("scripted_triggers")
        self.log(f"  Found {len(definitions)} scripted trigger definitions")

        unused = self._find_unused(definitions, "trigger", "scripted_triggers")

        self._report(
            unused,
            "✓ No unused scripted triggers found",
            "Unused scripted triggers (defined but never called):",
        )

    def run_validations(self):
        self.validate_unused_effects()
        self.validate_unused_triggers()


if __name__ == "__main__":
    run_validator_main(
        Validator, "Find unused scripted effects and triggers in Millennium Dawn mod"
    )
