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
from multiprocessing import Pool
from pathlib import Path
from typing import Dict, List, Tuple

from validator_common import (
    BaseValidator,
    Colors,
    DataCleaner,
    FileOpener,
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
    if _should_skip(filename):
        return ({}, {})
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
    if _should_skip(filename):
        return {}
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


def process_file_for_set_cosmetic_tag_defined(
    args: Tuple[str, bool]
) -> Tuple[Dict[str, int], Dict[str, str]]:
    filename, lowercase = args
    if _should_skip(filename):
        return ({}, {})
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

    def _get_txt_files(self) -> List[str]:
        if self.staged_files:
            return [f for f in self.staged_files if f.endswith(".txt")]
        return list(glob.iglob(self.mod_path + "**/*.txt", recursive=True))

    def validate_missing_cosmetic_tags(self, false_positives: list):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking missing cosmetic tags (has_cosmetic_tag but never set)...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        files = self._get_txt_files()

        args_list = [(f, False) for f in files]
        with Pool(processes=self.workers) as pool:
            results = pool.map(
                process_file_for_has_cosmetic_tag, args_list, chunksize=50
            )

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

        remaining_tags = list(cosmetic_tags.keys())
        args_list = [(f, False, remaining_tags) for f in files]
        with Pool(processes=self.workers) as pool:
            results = pool.map(
                process_file_for_set_cosmetic_tag, args_list, chunksize=50
            )

        for counts in results:
            for tag, count in counts.items():
                cosmetic_tags[tag] += count

        cosmetic_tags = DataCleaner.clear_false_positives(
            cosmetic_tags, tuple(false_positives)
        )
        missing = [tag for tag in cosmetic_tags if cosmetic_tags[tag] == 0]

        if len(missing) > 0:
            self.log(
                f"{Colors.RED if self.use_colors else ''}Missing cosmetic tags - referenced via has_cosmetic_tag but never set:{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
            for tag in missing:
                self.log(
                    f"  {Colors.YELLOW if self.use_colors else ''}{tag}{Colors.ENDC if self.use_colors else ''} - {paths.get(tag, 'unknown')}",
                    "error",
                )
            self.log(
                f"{Colors.RED if self.use_colors else ''}{len(missing)} issues found{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
            self.errors_found += len(missing)
        else:
            self.log(
                f"{Colors.GREEN if self.use_colors else ''}✓ No missing cosmetic tags{Colors.ENDC if self.use_colors else ''}"
            )

    def validate_unused_cosmetic_tags(self, false_positives: list):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking unused cosmetic tags (set but never referenced)...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        files = self._get_txt_files()

        args_list = [(f, False) for f in files]
        with Pool(processes=self.workers) as pool:
            results = pool.map(
                process_file_for_set_cosmetic_tag_defined, args_list, chunksize=50
            )

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
            country_flags.append(os.path.basename(filename.lower())[:-4])

        for tag in list(cosmetic_tags.keys()):
            if cosmetic_tags[tag] == 0:
                if tag in country_flags:
                    cosmetic_tags[tag] += 1
                else:
                    for suffix in MD_IDEOLOGY_SUFFIXES:
                        if tag + suffix in country_flags:
                            cosmetic_tags[tag] += 1
                            break

        for filename in files:
            if _should_skip(filename):
                continue
            text_file = FileOpener.open_text_file(
                filename, lowercase=False, strip_comments_flag=True
            )
            not_found = [t for t in cosmetic_tags if cosmetic_tags[t] == 0]
            if "has_cosmetic_tag =" in text_file:
                all_matches = re.findall(r"has_cosmetic_tag = \S*", text_file)
                for tag in not_found:
                    cosmetic_tags[tag] += all_matches.count(f"has_cosmetic_tag = {tag}")

        yml_files = list(glob.iglob(self.mod_path + "**/*.yml", recursive=True))
        for filename in yml_files:
            if _should_skip(filename):
                continue
            text_file = FileOpener.open_text_file(
                filename, lowercase=False, strip_comments_flag=True
            )
            not_found = [t for t in cosmetic_tags if cosmetic_tags[t] == 0]
            for tag in not_found:
                if tag in text_file:
                    all_matches = re.findall(tag + r".*", text_file)
                    for match in all_matches:
                        suffixes = [":"] + [s + ":" for s in MD_IDEOLOGY_SUFFIXES]
                        for p in suffixes:
                            cosmetic_tags[tag] += match.count(f"{tag}{p}")

        cosmetic_tags = DataCleaner.clear_false_positives(
            cosmetic_tags, tuple(false_positives)
        )
        unused = [tag for tag in cosmetic_tags if cosmetic_tags[tag] == 0]

        if len(unused) > 0:
            self.log(
                f"{Colors.RED if self.use_colors else ''}Unused cosmetic tags - set but not referenced in cosmetic.txt, .tga flags, has_cosmetic_tag, or loc:{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
            for tag in unused:
                self.log(
                    f"  {Colors.YELLOW if self.use_colors else ''}{tag}{Colors.ENDC if self.use_colors else ''} - {paths.get(tag, 'unknown')}",
                    "error",
                )
            self.log(
                f"{Colors.RED if self.use_colors else ''}{len(unused)} issues found{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
            self.errors_found += len(unused)
        else:
            self.log(
                f"{Colors.GREEN if self.use_colors else ''}✓ No unused cosmetic tags{Colors.ENDC if self.use_colors else ''}"
            )

    def validate_unused_cosmetic_tag_colors(self, false_positives: list):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking unused cosmetic tag colors (defined in cosmetic.txt but never set)...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

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

        files = self._get_txt_files()
        for filename in files:
            if _should_skip(filename):
                continue
            text_file = FileOpener.open_text_file(
                filename, lowercase=False, strip_comments_flag=True
            )
            if "set_cosmetic_tag =" in text_file:
                not_found = [t for t in cosmetic_tags if cosmetic_tags[t] == 0]
                for tag in not_found:
                    cosmetic_tags[tag] += text_file.count(f"set_cosmetic_tag = {tag}")

        unused = [tag for tag in cosmetic_tags if cosmetic_tags[tag] == 0]

        if len(unused) > 0:
            self.log(
                f"{Colors.RED if self.use_colors else ''}Unused cosmetic tag colors - defined in cosmetic.txt but never assigned with set_cosmetic_tag:{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
            for tag in unused:
                self.log(
                    f"  {Colors.YELLOW if self.use_colors else ''}{tag}{Colors.ENDC if self.use_colors else ''}",
                    "error",
                )
            self.log(
                f"{Colors.RED if self.use_colors else ''}{len(unused)} issues found{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
            self.errors_found += len(unused)
        else:
            self.log(
                f"{Colors.GREEN if self.use_colors else ''}✓ No unused cosmetic tag colors{Colors.ENDC if self.use_colors else ''}"
            )

    def run_validations(self):
        FALSE_POSITIVES = ["[", "{"]
        self.validate_missing_cosmetic_tags(FALSE_POSITIVES)
        self.validate_unused_cosmetic_tags(FALSE_POSITIVES)
        self.validate_unused_cosmetic_tag_colors(FALSE_POSITIVES)


if __name__ == "__main__":
    run_validator_main(Validator, "Validate cosmetic tags in Millennium Dawn mod")
