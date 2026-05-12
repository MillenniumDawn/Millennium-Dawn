#!/usr/bin/env python3
##########################
# Cosmetic Tag Validation Script (Multiprocessing Optimized)
# Validates cosmetic tag definitions and usage
# Checks for:
#   1. Missing cosmetic tags (has_cosmetic_tag but never set_cosmetic_tag)
#   2. Unused cosmetic tags (set_cosmetic_tag but never referenced)
#   3. Unused cosmetic tag colors (defined in cosmetic.txt but never set)
# Based on Kaiserreich Autotests by Pelmen, https://github.com/Pelmen323
# Adapted for Millennium Dawn with multiprocessing
##########################
import glob
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

from validator_common import (
    BaseValidator,
    Colors,
    DataCleaner,
    FileOpener,
    Severity,
    run_validator_main,
    should_skip_file,
)

EXTRA_SKIP_PATTERNS = ["FR_loc"]

# Millennium Dawn ideology suffixes for flag .tga matching
MD_IDEOLOGY_SUFFIXES = [
    "_democratic",
    "_communism",
    "_fascism",
    "_neutrality",
    "_nationalist",
]


def _should_skip(filename: str) -> bool:
    return should_skip_file(filename, extra_skip_patterns=EXTRA_SKIP_PATTERNS)


# --- Multiprocessing helpers ---


def process_file_for_has_cosmetic_tag(
    args: Tuple[str, bool]
) -> Tuple[Dict[str, int], Dict[str, str]]:
    filename, lowercase = args
    text_file = FileOpener.open_text_file(
        filename, lowercase=lowercase, strip_comments_flag=True
    )
    tags = {}
    paths = {}
    if "has_cosmetic_tag =" in text_file:
        matches = re.findall(r"has_cosmetic_tag = (\S+)", text_file)
        for match in matches:
            if "[" not in match:
                tags[match] = 0
                paths[match] = os.path.basename(filename)
    return (tags, paths)


def process_file_for_set_cosmetic_tag(args: Tuple[str, bool]) -> Dict[str, int]:
    filename, lowercase, tags_to_find = args
    text_file = FileOpener.open_text_file(
        filename, lowercase=lowercase, strip_comments_flag=True
    )
    counts = {}
    if "set_cosmetic_tag =" in text_file:
        for tag in tags_to_find:
            count = text_file.count(f"set_cosmetic_tag = {tag}")
            if count > 0:
                counts[tag] = count
    return counts


def process_file_for_has_cosmetic_tag_lookup(args: Tuple[str, frozenset]) -> Set[str]:
    """Return subset of tags_to_find referenced via has_cosmetic_tag = TAG in this file."""
    filename, tags_to_find = args
    if _should_skip(filename):
        return set()
    try:
        text = Path(filename).read_text(encoding="utf-8-sig", errors="ignore")
    except Exception:
        return set()
    cleaned = re.sub(r"#[^\n]*", "", text)
    if "has_cosmetic_tag =" not in cleaned:
        return set()
    all_matches = set(re.findall(r"has_cosmetic_tag = (\S+)", cleaned))
    return tags_to_find & all_matches


def process_file_for_cosmetic_tag_in_loc(args: Tuple[str, frozenset]) -> Dict[str, int]:
    """Return {tag: count} for cosmetic tag references in a yml localisation file."""
    filename, tags_to_find = args
    if _should_skip(filename):
        return {}
    try:
        text = Path(filename).read_text(encoding="utf-8-sig", errors="ignore")
    except Exception:
        return {}
    cleaned = re.sub(r"#[^\n]*", "", text)
    counts: Dict[str, int] = {}
    suffixes = [":"] + [s + ":" for s in MD_IDEOLOGY_SUFFIXES]
    for tag in tags_to_find:
        if tag not in cleaned:
            continue
        total = sum(cleaned.count(f"{tag}{sfx}") for sfx in suffixes)
        if total > 0:
            counts[tag] = total
    return counts


def process_file_for_set_cosmetic_tag_defined(
    args: Tuple[str, bool]
) -> Tuple[Dict[str, int], Dict[str, str]]:
    filename, lowercase = args
    text_file = FileOpener.open_text_file(
        filename, lowercase=lowercase, strip_comments_flag=True
    )
    tags = {}
    paths = {}
    if "set_cosmetic_tag =" in text_file:
        matches = re.findall(r"set_cosmetic_tag = (\S+)", text_file)
        for match in matches:
            tags[match] = 0
            paths[match] = os.path.basename(filename)
    return (tags, paths)


class Validator(BaseValidator):
    TITLE = "COSMETIC TAG VALIDATION"
    STAGED_EXTENSIONS = [".txt", ".yml"]

    def validate_missing_cosmetic_tags(self, false_positives: list):
        self._log_section(
            "Checking missing cosmetic tags (has_cosmetic_tag but never set)..."
        )

        files = self._collect_files(["**/*.txt"], extra_skip=_should_skip)

        args_list = [(f, False) for f in files]
        results = self._pool_map(process_file_for_has_cosmetic_tag, args_list)

        cosmetic_tags = {}
        paths = {}
        for tags_dict, paths_dict in results:
            for tag, count in tags_dict.items():
                cosmetic_tags[tag] = 0
                paths[tag] = paths_dict[tag]

        self.log(f"  Found {len(cosmetic_tags)} unique has_cosmetic_tag references")
        if len(cosmetic_tags) == 0:
            self.log(
                f"{Colors.GREEN if self.use_colors else ''}✓ No cosmetic tag references found{Colors.ENDC if self.use_colors else ''}"
            )
            return

        # Cross-reference resolution: a tag set in any file in the repo counts,
        # not just in the staged subset. Without ignore_staged here, a staged
        # change adding `has_cosmetic_tag = X` would false-positive whenever
        # the `set_cosmetic_tag = X` definition lives in an unmodified file.
        all_files = self._collect_files(
            ["**/*.txt"], extra_skip=_should_skip, ignore_staged=True
        )
        remaining_tags = list(cosmetic_tags.keys())
        args_list = [(f, False, remaining_tags) for f in all_files]
        results = self._pool_map(process_file_for_set_cosmetic_tag, args_list)

        for counts in results:
            for tag, count in counts.items():
                cosmetic_tags[tag] += count

        cosmetic_tags = DataCleaner.clear_false_positives(
            cosmetic_tags, tuple(false_positives)
        )
        missing = [tag for tag in cosmetic_tags if cosmetic_tags[tag] == 0]

        if missing:
            report_items = [(tag, paths.get(tag, "unknown"), 0) for tag in missing]
            self._report(
                report_items,
                "✓ No missing cosmetic tags",
                "Missing cosmetic tags - referenced via has_cosmetic_tag but never set:",
                Severity.ERROR,
                category="missing-cosmetic-tag",
            )

    def validate_unused_cosmetic_tags(self, false_positives: list):
        self._log_section("Checking unused cosmetic tags (set but never referenced)...")

        files = self._collect_files(["**/*.txt"], extra_skip=_should_skip)

        args_list = [(f, False) for f in files]
        results = self._pool_map(process_file_for_set_cosmetic_tag_defined, args_list)

        cosmetic_tags = {}
        paths = {}
        for tags_dict, paths_dict in results:
            for tag in tags_dict:
                cosmetic_tags[tag] = 0
                paths[tag] = paths_dict[tag]

        self.log(f"  Found {len(cosmetic_tags)} unique set_cosmetic_tag definitions")
        if len(cosmetic_tags) == 0:
            self.log(
                f"{Colors.GREEN if self.use_colors else ''}✓ No cosmetic tag definitions found{Colors.ENDC if self.use_colors else ''}"
            )
            return

        cosmetic_file = Path(self.mod_path) / "common" / "countries" / "cosmetic.txt"
        if cosmetic_file.exists():
            text_file = FileOpener.open_text_file(
                str(cosmetic_file), lowercase=False, strip_comments_flag=True
            )
            for tag in list(cosmetic_tags.keys()):
                if cosmetic_tags[tag] == 0 and f"{tag} =" in text_file:
                    cosmetic_tags[tag] += 1

        country_flags = []
        flag_path = str(Path(self.mod_path) / "gfx" / "flags" / "**/*.tga")
        for filename in glob.iglob(flag_path, recursive=True):
            country_flags.append(os.path.basename(filename)[:-4])

        for tag in list(cosmetic_tags.keys()):
            if cosmetic_tags[tag] == 0:
                if tag in country_flags:
                    cosmetic_tags[tag] += 1
                else:
                    for suffix in MD_IDEOLOGY_SUFFIXES:
                        if tag + suffix in country_flags:
                            cosmetic_tags[tag] += 1
                            break

        remaining_tags = frozenset(t for t in cosmetic_tags if cosmetic_tags[t] == 0)

        if remaining_tags:
            # Pool scan over txt files for has_cosmetic_tag = TAG references
            args_list = [(f, remaining_tags) for f in files]
            txt_results = self._pool_map(
                process_file_for_has_cosmetic_tag_lookup, args_list, chunksize=30
            )
            for found_set in txt_results:
                for tag in found_set:
                    cosmetic_tags[tag] += 1

            # Pool scan over yml files for loc references
            remaining_tags = frozenset(
                t for t in cosmetic_tags if cosmetic_tags[t] == 0
            )
            if remaining_tags:
                yml_files = list(
                    glob.iglob(
                        os.path.join(self.mod_path, "**", "*.yml"), recursive=True
                    )
                )
                yml_files = [f for f in yml_files if not _should_skip(f)]
                args_list = [(f, remaining_tags) for f in yml_files]
                yml_results = self._pool_map(
                    process_file_for_cosmetic_tag_in_loc, args_list, chunksize=30
                )
                for counts in yml_results:
                    for tag, count in counts.items():
                        cosmetic_tags[tag] += count

        cosmetic_tags = DataCleaner.clear_false_positives(
            cosmetic_tags, tuple(false_positives)
        )
        unused = [tag for tag in cosmetic_tags if cosmetic_tags[tag] == 0]

        if unused:
            report_items = [(tag, paths.get(tag, "unknown"), 0) for tag in unused]
            self._report(
                report_items,
                "✓ No unused cosmetic tags",
                "Unused cosmetic tags - set but not referenced:",
                Severity.ERROR,
                category="unused-cosmetic-tag",
            )

    def validate_unused_cosmetic_tag_colors(self, false_positives: list):
        self._log_section(
            "Checking unused cosmetic tag colors (defined in cosmetic.txt but never set)..."
        )

        cosmetic_file = Path(self.mod_path) / "common" / "countries" / "cosmetic.txt"
        if not cosmetic_file.exists():
            self.log(
                f"{Colors.YELLOW if self.use_colors else ''}cosmetic.txt not found, skipping{Colors.ENDC if self.use_colors else ''}",
                "warning",
            )
            return

        text_file = FileOpener.open_text_file(
            str(cosmetic_file), lowercase=False, strip_comments_flag=True
        )
        pattern_matches = re.findall(r"^(\S+) = \{", text_file, flags=re.MULTILINE)
        cosmetic_tags = {}
        for match in pattern_matches:
            cosmetic_tags[match] = 0

        self.log(f"  Found {len(cosmetic_tags)} cosmetic tag color definitions")
        if len(cosmetic_tags) == 0:
            self.log(
                f"{Colors.GREEN if self.use_colors else ''}✓ No cosmetic tag colors found{Colors.ENDC if self.use_colors else ''}"
            )
            return

        cosmetic_tags = DataCleaner.clear_false_positives(
            cosmetic_tags, tuple(false_positives)
        )

        files = self._collect_files(["**/*.txt"], extra_skip=_should_skip)
        remaining_tags = [t for t in cosmetic_tags if cosmetic_tags[t] == 0]
        if remaining_tags:
            args_list = [(f, False, remaining_tags) for f in files]
            results = self._pool_map(
                process_file_for_set_cosmetic_tag, args_list, chunksize=30
            )
            for counts in results:
                for tag, count in counts.items():
                    cosmetic_tags[tag] += count

        unused = [tag for tag in cosmetic_tags if cosmetic_tags[tag] == 0]

        if unused:
            report_items = [(tag, "", 0) for tag in unused]
            self._report(
                report_items,
                "✓ No unused cosmetic tag colors",
                "Unused cosmetic tag colors - defined in cosmetic.txt but never assigned with set_cosmetic_tag:",
                Severity.ERROR,
                category="unused-cosmetic-color",
            )

    def run_validations(self):
        if self.staged_only and not self.staged_files:
            self.log(
                "No staged files found — skipping cosmetic tags validation",
                "warning",
            )
            return

        # Tags containing [ or { are from meta_effect text blocks and should be ignored
        PATTERN_FALSE_POSITIVES = ["[", "{"]
        # Tags that are generated dynamically via meta_effects (e.g. [ROOTTAG]_REB)
        # and so never appear as literal set_cosmetic_tag = TAG calls
        META_EFFECT_TAGS = [
            "PER_REB",  # from [ROOTTAG]_REB
            "GER_AUTH_S",  # from [ROOTTAG]_AUTH_S
            "CRO_Serbian_Krajina",  # checked in scripted loc but set externally
            "ENG_England",  # checked in formable nations but never set
        ]
        KNOWN_BUGS = []
        # Tags set in focus trees that lack cosmetic.txt/flag definitions (incomplete)
        INCOMPLETE_TAGS = [
            "BSH_limonka",  # 05_bashkiriya.txt - nationalist fascist override
            "BSH_REB_S_nationalist",  # 05_bashkiriya.txt - nationalist junta override
            "TAT_REB_S_nationalist",  # Tatarstan.txt - nationalist junta override
        ]
        # validate_missing uses _collect_files() which respects staged mode
        self.validate_missing_cosmetic_tags(PATTERN_FALSE_POSITIVES + META_EFFECT_TAGS)

        # Cross-reference checks scan all .tga/.yml files — skip in staged mode
        if not self.staged_only:
            self.validate_unused_cosmetic_tags(
                PATTERN_FALSE_POSITIVES + KNOWN_BUGS + INCOMPLETE_TAGS
            )
            self.validate_unused_cosmetic_tag_colors(
                PATTERN_FALSE_POSITIVES + META_EFFECT_TAGS
            )


if __name__ == "__main__":
    run_validator_main(Validator, "Validate cosmetic tags in Millennium Dawn mod")
