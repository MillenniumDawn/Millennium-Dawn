#!/usr/bin/env python3
# Validate cosmetic tag definitions and usage: missing tags (has_cosmetic_tag
# but never set), unused tags (set but never referenced), and unused tag colors
# (defined in cosmetic.txt but never set).
# Based on Kaiserreich Autotests by Pelmen, https://github.com/Pelmen323
import glob
import os
import re
from functools import partial
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import disk_cache
from shared_utils import validation_config
from validator_common import (
    DEFAULT_EXTRA_SKIP_PATTERNS,
    BaseValidator,
    Colors,
    FileOpener,
    Severity,
    run_validator_main,
    should_skip_file,
)

EXTRA_SKIP_PATTERNS = DEFAULT_EXTRA_SKIP_PATTERNS

# Millennium Dawn ideology suffixes for flag .tga matching
MD_IDEOLOGY_SUFFIXES = [
    "_democratic",
    "_communism",
    "_fascism",
    "_neutrality",
    "_nationalist",
]


def _should_skip(filename: str, *, mod_path: Optional[str] = None) -> bool:
    return should_skip_file(
        filename, extra_skip_patterns=EXTRA_SKIP_PATTERNS, mod_path=mod_path
    )


# --- Multiprocessing helpers ---

_SET_COSMETIC = "set_cosmetic_tag = "
_NON_SPACE_RE = re.compile(r"\S*")


def process_file_for_set_cosmetic_tag(
    args: Tuple[str, bool, List[str]],
) -> Dict[str, int]:
    filename, lowercase, tags_to_find = args
    text_file = FileOpener.open_text_file(
        filename, lowercase=lowercase, strip_comments_flag=True
    )
    counts: Dict[str, int] = {}
    if "set_cosmetic_tag =" not in text_file:
        return counts
    # Same as text_file.count(_SET_COSMETIC + tag) per tag, but one walk over
    # the sites: tags hold no whitespace, so each is a prefix of a site's value.
    wanted = set(tags_to_find)
    next_free: Dict[str, int] = {}
    site = text_file.find(_SET_COSMETIC)
    while site != -1:
        start = site + len(_SET_COSMETIC)
        value = _NON_SPACE_RE.match(text_file, start).group()
        for stop in range(1, len(value) + 1):
            tag = value[:stop]
            if tag in wanted and site >= next_free.get(tag, 0):
                counts[tag] = counts.get(tag, 0) + 1
                next_free[tag] = start + stop
        site = text_file.find(_SET_COSMETIC, site + 1)
    return {tag: counts[tag] for tag in tags_to_find if tag in counts}


def _scan_both_cosmetic_tags(
    text_file: str, basename: str
) -> Tuple[Dict[str, int], Dict[str, str], Dict[str, int], Dict[str, str]]:
    has_tags: Dict[str, int] = {}
    has_paths: Dict[str, str] = {}
    set_tags: Dict[str, int] = {}
    set_paths: Dict[str, str] = {}
    if "has_cosmetic_tag =" in text_file:
        for match in re.findall(r"has_cosmetic_tag = (\S+)", text_file):
            if "[" not in match:
                has_tags[match] = 0
                has_paths[match] = basename
    if "set_cosmetic_tag =" in text_file:
        for match in re.findall(r"set_cosmetic_tag = (\S+)", text_file):
            if "[" not in match:
                set_tags[match] = 0
                set_paths[match] = basename
    return (has_tags, has_paths, set_tags, set_paths)


def process_file_for_both_cosmetic_tags(
    args: Tuple[str, bool, str],
) -> Tuple[Dict[str, int], Dict[str, str], Dict[str, int], Dict[str, str]]:
    # Returns (has_tags, has_paths, set_tags, set_paths). Dict values for the
    # *_tags maps are initialised to 0 so callers can sum reference counts in.
    filename, lowercase, mod_path = args
    text_file = FileOpener.open_text_file(
        filename, lowercase=lowercase, strip_comments_flag=True
    )
    basename = os.path.basename(filename)
    return disk_cache.per_file_cached_by_content(
        mod_path,
        f"cosmetic.both.lc={int(lowercase)}",
        filename,
        text_file,
        lambda: _scan_both_cosmetic_tags(text_file, basename),
    )


def process_file_for_has_cosmetic_tag_lookup(
    args: Tuple[str, frozenset], *, mod_path: Optional[str] = None
) -> Set[str]:
    """Return subset of tags_to_find referenced via has_cosmetic_tag = TAG in this file."""
    filename, tags_to_find = args
    if _should_skip(filename, mod_path=mod_path):
        return set()
    try:
        text = Path(filename).read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return set()
    cleaned = re.sub(r"#[^\n]*", "", text)
    if "has_cosmetic_tag =" not in cleaned:
        return set()
    all_matches = set(re.findall(r"has_cosmetic_tag = (\S+)", cleaned))
    return all_matches & tags_to_find


def process_file_for_cosmetic_tag_in_loc(
    args: Tuple[str, frozenset], *, mod_path: Optional[str] = None
) -> Dict[str, int]:
    """Return {tag: count} for cosmetic tag references in a yml localisation file."""
    filename, tags_to_find = args
    if _should_skip(filename, mod_path=mod_path):
        return {}
    try:
        text = Path(filename).read_text(encoding="utf-8-sig", errors="replace")
    except Exception:
        return {}
    cleaned = re.sub(r"#[^\n]*", "", text)
    counts: Dict[str, int] = {}
    # One scan for any tag at all; most loc files hold none.
    if not re.search("|".join(map(re.escape, sorted(tags_to_find))), cleaned):
        return counts
    suffixes = [":"] + [s + ":" for s in MD_IDEOLOGY_SUFFIXES]
    for tag in tags_to_find:
        if tag not in cleaned:
            continue
        total = sum(cleaned.count(f"{tag}{sfx}") for sfx in suffixes)
        if total > 0:
            counts[tag] = total
    return counts


class Validator(BaseValidator):
    TITLE = "COSMETIC TAG VALIDATION"
    STAGED_EXTENSIONS = [".txt", ".yml"]

    def _txt_files(self, *, ignore_staged: bool = False) -> List[str]:
        """Script files the checks scan, walked once; outside staged mode the
        full-repo list is the same list."""
        if ignore_staged and self.staged_only:
            return self._collect_files(
                ["**/*.txt"],
                extra_skip=partial(_should_skip, mod_path=self.mod_path),
                ignore_staged=True,
            )
        return self.cached(
            "txt_files",
            lambda: self._collect_files(
                ["**/*.txt"], extra_skip=partial(_should_skip, mod_path=self.mod_path)
            ),
        )

    def _scan_for_both_tags(self):
        # Cached so validate_missing + validate_unused share one repo walk
        # instead of each running its own pool scan.
        def _build():
            files = self._txt_files()
            args_list = [(f, False, self.mod_path) for f in files]
            scan_results = self._pool_map(
                process_file_for_both_cosmetic_tags, args_list
            )
            has_tags: Dict[str, int] = {}
            has_paths: Dict[str, str] = {}
            set_tags: Dict[str, int] = {}
            set_paths: Dict[str, str] = {}
            for h_t, h_p, s_t, s_p in scan_results:
                for tag in h_t:
                    has_tags[tag] = 0
                    if tag not in has_paths:
                        has_paths[tag] = h_p[tag]
                for tag in s_t:
                    set_tags[tag] = 0
                    if tag not in set_paths:
                        set_paths[tag] = s_p[tag]
            return (has_tags, has_paths, set_tags, set_paths, files)

        return self.cached("cosmetic_both_tags", _build)

    def validate_missing_cosmetic_tags(self, false_positives: list):
        self._log_section(
            "Checking missing cosmetic tags (has_cosmetic_tag but never set)..."
        )

        cosmetic_tags_src, paths_src, _, _, _ = self._scan_for_both_tags()
        cosmetic_tags = dict(cosmetic_tags_src)
        paths = dict(paths_src)

        self.log(f"  Found {len(cosmetic_tags)} unique has_cosmetic_tag references")
        if len(cosmetic_tags) == 0:
            self.log(f"{Colors.GREEN}✓ No cosmetic tag references found{Colors.ENDC}")
            return

        # Cross-reference resolution: a tag set in any file in the repo counts,
        # not just in the staged subset. Without ignore_staged here, a staged
        # change adding `has_cosmetic_tag = X` would false-positive whenever
        # the `set_cosmetic_tag = X` definition lives in an unmodified file.
        all_files = self._txt_files(ignore_staged=True)
        remaining_tags = list(cosmetic_tags.keys())
        args_list = [(f, False, remaining_tags) for f in all_files]
        results = self._pool_map(process_file_for_set_cosmetic_tag, args_list)

        for counts in results:
            for tag, count in counts.items():
                cosmetic_tags[tag] += count

        for tag in false_positives:
            cosmetic_tags.pop(tag, None)
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

        _, _, set_tags_src, set_paths_src, files = self._scan_for_both_tags()
        cosmetic_tags = dict(set_tags_src)
        paths = dict(set_paths_src)

        self.log(f"  Found {len(cosmetic_tags)} unique set_cosmetic_tag definitions")
        if len(cosmetic_tags) == 0:
            self.log(f"{Colors.GREEN}✓ No cosmetic tag definitions found{Colors.ENDC}")
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
                partial(
                    process_file_for_has_cosmetic_tag_lookup, mod_path=self.mod_path
                ),
                args_list,
                chunksize=30,
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
                yml_files = [
                    f for f in yml_files if not _should_skip(f, mod_path=self.mod_path)
                ]
                args_list = [(f, remaining_tags) for f in yml_files]
                yml_results = self._pool_map(
                    partial(
                        process_file_for_cosmetic_tag_in_loc, mod_path=self.mod_path
                    ),
                    args_list,
                    chunksize=30,
                )
                for counts in yml_results:
                    for tag, count in counts.items():
                        cosmetic_tags[tag] += count

        for tag in false_positives:
            cosmetic_tags.pop(tag, None)
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
                f"{Colors.YELLOW}cosmetic.txt not found, skipping{Colors.ENDC}",
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
            self.log(f"{Colors.GREEN}✓ No cosmetic tag colors found{Colors.ENDC}")
            return

        for tag in false_positives:
            cosmetic_tags.pop(tag, None)

        files = self._txt_files()
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

        pattern, meta_effect, known_bugs, incomplete = (
            list(validation_config("validate_cosmetic_tags", key))
            for key in (
                "pattern_false_positives",
                "meta_effect_tags",
                "known_bugs",
                "incomplete_tags",
            )
        )
        # validate_missing uses _collect_files() which respects staged mode
        self.validate_missing_cosmetic_tags(pattern + meta_effect)

        # Cross-reference checks scan all .tga/.yml files — skip in staged mode
        if not self.staged_only:
            self.validate_unused_cosmetic_tags(pattern + known_bugs + incomplete)
            self.validate_unused_cosmetic_tag_colors(pattern + meta_effect)


if __name__ == "__main__":
    run_validator_main(Validator, "Validate cosmetic tags in Millennium Dawn mod")
