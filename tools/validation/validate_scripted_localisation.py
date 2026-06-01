#!/usr/bin/env python3
##########################
# Scripted Localisation Validation Script (Multiprocessing Optimized)
# Validates scripted localisation definitions and usage
# Checks for: used but not defined, defined but not used, GFX_ icons not defined in .gfx files
# Based on Millennium Dawn validation framework
# Optimized with multiprocessing for significantly faster execution
##########################
import glob
import os
import re
from multiprocessing import Pool
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import disk_cache
from validator_common import (
    BaseValidator,
    Colors,
    DataCleaner,
    FileOpener,
    Severity,
    find_line_number,
    run_validator_main,
    scan_meta_constructed_names,
    should_skip_file,
)


# Multiprocessing helper functions
def _scan_defined_locs(text: str, basename: str) -> Tuple[List[str], Dict[str, str]]:
    localisations: List[str] = []
    paths: Dict[str, str] = {}
    if "defined_text" in text and "name =" in text:
        for match in re.findall(r"name\s*=\s*([a-zA-Z_0-9]+)", text):
            localisations.append(match)
            paths[match] = basename
    return (localisations, paths)


def process_file_for_defined_localisations(
    args: Tuple[str, bool, str],
) -> Tuple[List[str], Dict[str, str]]:
    filename, lowercase, mod_path = args

    if should_skip_file(filename):
        return ([], {})

    if "00_scripted_localisation_FR_loc" in filename:
        return ([], {})

    text_file = FileOpener.open_text_file(
        filename, lowercase=lowercase, strip_comments_flag=True
    )
    basename = os.path.basename(filename)
    return disk_cache.per_file_cached_by_content(
        mod_path,
        f"scripted_loc.defined.lc={int(lowercase)}",
        filename,
        text_file,
        lambda: _scan_defined_locs(text_file, basename),
    )


def _scan_loc_tokens(text: str, is_scripted_loc_file: bool) -> Set[str]:
    if is_scripted_loc_file:
        # Only bracket tokens — full tokenisation would treat `name = X` as a usage.
        tokens: Set[str] = set(re.findall(r"\[(\w+)\]", text))
        tokens |= set(re.findall(r"\[\w+\.(\w+)\]", text))
        return tokens
    # Tokenise once; also extract [name] and [Scope.name] bracket calls
    # (\w catches digit-prefixed names missed by [A-Za-z_][A-Za-z0-9_]*).
    tokens = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text))
    tokens |= set(re.findall(r"\[(\w+)\]", text))
    tokens |= set(re.findall(r"\[\w+\.(\w+)\]", text))
    return tokens


def process_file_for_used_localisations(
    args: Tuple[str, Set[str], bool, str],
) -> Tuple[List[str], Dict[str, str]]:
    filename, search_names, lowercase, mod_path = args

    if should_skip_file(filename):
        return ([], {})

    basename = os.path.basename(filename)

    text_file = FileOpener.open_text_file(
        filename, lowercase=lowercase, strip_comments_flag=True
    )

    # Cache the file's token set (independent of search_names); intersect after
    # the cache hit so a changing defined-set never invalidates the entry.
    is_sl = "scripted_localisation" in filename
    tokens = disk_cache.per_file_cached_by_content(
        mod_path,
        f"scripted_loc.tokens.lc={int(lowercase)}.{'b' if is_sl else 't'}",
        filename,
        text_file,
        lambda: _scan_loc_tokens(text_file, is_sl),
    )

    # Case-insensitive intersection — recover original casing for downstream matching.
    search_lower = {n.lower(): n for n in search_names}
    found_original = {
        search_lower[t.lower()] for t in tokens if t.lower() in search_lower
    }

    if not found_original:
        return ([], {})

    localisations = list(found_original)
    paths = {name: basename for name in found_original}
    return (localisations, paths)


class ScriptedLocalisation:
    @classmethod
    def get_all_defined_localisations(
        cls,
        mod_path,
        lowercase=True,
        return_paths=False,
        staged_files=None,
        workers=None,
        pool=None,
    ):
        localisations = []
        paths = {}

        if staged_files is not None:
            files_to_scan = [
                f
                for f in staged_files
                if "scripted_localisation" in f and f.endswith(".txt")
            ]
        else:
            pattern = os.path.join(mod_path, "common", "scripted_localisation", "*.txt")
            files_to_scan = glob.glob(pattern)

        args_list = [(f, lowercase, mod_path) for f in files_to_scan]
        p = pool if pool else Pool(processes=workers)
        results = p.map(process_file_for_defined_localisations, args_list, chunksize=10)
        if not pool:
            p.close()
            p.join()

        for locs_list, paths_dict in results:
            localisations.extend(locs_list)
            paths.update(paths_dict)

        return (localisations, paths) if return_paths else localisations

    @classmethod
    def get_all_used_localisations(
        cls,
        mod_path,
        defined_names,
        lowercase=True,
        return_paths=False,
        staged_files=None,
        workers=None,
        pool=None,
    ):
        localisations = []
        paths = {}

        search_names = (
            {name.lower() for name in defined_names} if lowercase else defined_names
        )

        if staged_files is not None:
            files_to_scan = [
                f
                for f in staged_files
                if f.endswith(".gui") or f.endswith(".yml") or f.endswith(".txt")
            ]
        else:
            gui_files = list(
                glob.iglob(os.path.join(mod_path, "**", "*.gui"), recursive=True)
            )
            yml_files = list(
                glob.iglob(os.path.join(mod_path, "**", "*.yml"), recursive=True)
            )
            txt_files = list(
                glob.iglob(os.path.join(mod_path, "**", "*.txt"), recursive=True)
            )
            files_to_scan = gui_files + yml_files + txt_files

        args_list = [(f, search_names, lowercase, mod_path) for f in files_to_scan]
        p = pool if pool else Pool(processes=workers)
        results = p.map(process_file_for_used_localisations, args_list, chunksize=50)
        if not pool:
            p.close()
            p.join()

        found_names = set()
        for locs_list, paths_dict in results:
            for loc in locs_list:
                if loc not in found_names:
                    localisations.append(loc)
                    paths[loc] = paths_dict[loc]
                    found_names.add(loc)

        # Additional pass: detect scripted locs called via meta_effect/meta_trigger
        # template substitution (e.g. `custom_effect_tooltip = tooltip_EU_[EUXXX]_approve`).
        # Only check names not already found to keep scanning cost low.
        still_unfound = set(defined_names) - found_names
        if still_unfound:
            txt_files_for_meta = [
                f
                for f in files_to_scan
                if f.endswith(".txt") and "scripted_localisation" not in f
            ]
            for loc in scan_meta_constructed_names(txt_files_for_meta, still_unfound):
                if loc not in found_names:
                    localisations.append(loc)
                    paths[loc] = "<meta_effect>"
                    found_names.add(loc)

        return (localisations, paths) if return_paths else localisations


class Validator(BaseValidator):
    TITLE = "SCRIPTED LOCALISATION VALIDATION"
    STAGED_EXTENSIONS = [".txt", ".yml", ".gui"]

    def validate_missing_scripted_localisations(
        self,
        false_positives,
        defined_locs: List[str],
        used_locs: List[str],
        used_paths: Dict[str, str],
    ):
        self._log_section(
            "Checking missing scripted localisations (used but not defined)..."
        )

        defined_locs_lower = [loc.lower() for loc in defined_locs]
        used_locs_lower_raw = [loc.lower() for loc in used_locs]
        used_lower_to_original = {loc.lower(): loc for loc in used_locs}

        used_locs_lower = DataCleaner.clear_false_positives_partial_match(
            used_locs_lower_raw, tuple(false_positives)
        )

        results = []
        reported = set()
        for loc in used_locs_lower:
            if loc not in defined_locs_lower and loc not in reported:
                original_loc = used_lower_to_original.get(loc, loc)
                basename = used_paths.get(original_loc, used_paths.get(loc, "unknown"))
                full_path = self.get_full_path(
                    basename, loc, file_patterns=["**/*.txt", "**/*.gui"]
                )
                if full_path:
                    rel_path = os.path.relpath(full_path, self.mod_path)
                    line_num = find_line_number(full_path, loc, lowercase=True)
                    results.append((loc, rel_path, line_num))
                    reported.add(loc)

        if len(results) > 0:
            self.log(
                f"{Colors.YELLOW if self.use_colors else ''}Note: Some of these may be regular localisation keys rather than scripted localisation. Verify manually.{Colors.ENDC if self.use_colors else ''}",
                "warning",
            )
            self._report(
                results,
                "✓ No issues found with missing scripted localisations",
                "Missing scripted localisations - referenced but not defined:",
                Severity.ERROR,
                category="missing-scripted-loc",
            )

    def validate_unused_scripted_localisations(
        self,
        false_positives,
        defined_locs: List[str],
        defined_paths: Dict[str, str],
        used_locs: List[str],
    ):
        self._log_section(
            "Checking unused scripted localisations (defined but not used)..."
        )

        # Preemptive slot libraries — defined for all possible slots even if only a
        # subset are active.  Suppress unused warnings for the unoccupied slots rather
        # than requiring every slot to have a live caller.
        UNUSED_ONLY_FALSE_POSITIVES = ("eu_parl_pg_party_",)

        defined_lower_to_original = {loc.lower(): loc for loc in defined_locs}
        defined_locs_lower = [loc.lower() for loc in defined_locs]
        used_locs_lower = [loc.lower() for loc in used_locs]

        defined_locs_lower = DataCleaner.clear_false_positives_partial_match(
            defined_locs_lower,
            tuple(false_positives) + tuple(UNUSED_ONLY_FALSE_POSITIVES),
        )

        results = []
        reported = set()
        for loc in defined_locs_lower:
            if loc not in used_locs_lower and loc not in reported:
                original_loc = defined_lower_to_original.get(loc, loc)
                basename = defined_paths.get(
                    original_loc, defined_paths.get(loc, "unknown")
                )

                full_path = None
                pattern = os.path.join(
                    self.mod_path, "common", "scripted_localisation", basename
                )
                if os.path.exists(pattern):
                    full_path = pattern
                else:
                    for filename in glob.iglob(
                        os.path.join(
                            self.mod_path, "common", "scripted_localisation", "*.txt"
                        )
                    ):
                        if os.path.basename(filename) == basename:
                            full_path = filename
                            break

                if full_path:
                    rel_path = os.path.relpath(full_path, self.mod_path)
                    line_num = find_line_number(
                        full_path, f"name = {loc}", lowercase=True
                    )
                    results.append((loc, rel_path, line_num))
                    reported.add(loc)

        self._report(
            results,
            "✓ No issues found with unused scripted localisations",
            "Unused scripted localisations - defined but not referenced:",
            Severity.ERROR,
            category="unused-scripted-loc",
        )

    def validate_gfx_icons(self):
        self._log_section(
            "Checking GFX_ icon references in scripted localisation against .gfx definitions..."
        )

        # Collect all GFX_ names defined in interface/*.gfx
        gfx_path = str(Path(self.mod_path) / "interface") + "/"
        defined_gfx = set()
        for filename in glob.iglob(gfx_path + "**/*.gfx", recursive=True):
            text_file = FileOpener.open_text_file(
                filename, lowercase=False, strip_comments_flag=True
            )
            matches = re.findall(r'name\s*=\s*"(GFX_[^"]+)"', text_file)
            for m in matches:
                defined_gfx.add(m)

        # Collect all GFX_ references from scripted localisation files
        if self.staged_files:
            files_to_scan = [
                f
                for f in self.staged_files
                if "scripted_localisation" in f and f.endswith(".txt")
            ]
        else:
            pattern = os.path.join(
                self.mod_path, "common", "scripted_localisation", "*.txt"
            )
            files_to_scan = glob.glob(pattern)

        results = []
        reported = set()
        for filename in files_to_scan:
            text_file = FileOpener.open_text_file(
                filename, lowercase=False, strip_comments_flag=True
            )
            matches = re.findall(r"localization_key\s*=\s*(GFX_[^\s\}]+)", text_file)
            for gfx_name in matches:
                if gfx_name not in defined_gfx and gfx_name not in reported:
                    rel_path = os.path.relpath(filename, self.mod_path)
                    line_num = find_line_number(filename, gfx_name, lowercase=False)
                    results.append((gfx_name, rel_path, line_num))
                    reported.add(gfx_name)

        self._report(
            results,
            "✓ All GFX_ icons in scripted localisation are defined in .gfx files",
            "GFX_ icons referenced in scripted localisation but not defined in interface/*.gfx:",
            Severity.ERROR,
            category="gfx-icon",
        )

    def run_validations(self):
        if self.staged_only and not self.staged_files:
            self.log(
                "No staged files found — skipping scripted localisation validation",
                "warning",
            )
            return

        FALSE_POSITIVES = [
            "root.getname",
            "this.getname",
            "from.getname",
            "prev.getname",
            "root.getadjective",
            "this.getadjective",
            "from.getadjective",
            "getdatetext",
            "getyear",
            "getmonth",
            "getday",
            "tt",
            "_tt",
            "_desc",
            "_title",
            "button",
            "tooltip",
            "euxxx_ep_agenda",
            # Plain loc keys used as $KEY$ nested substitution wrappers in formable
            # state integration tooltips \u2014 not scripted localisations
            "gip",
            "gis",
            "\u00a7",
            "\u00a3",
            "$",
            "var:",
            "@",
            "[",
        ]

        # Build defined/used lists once and share between both checks — avoids
        # scanning the entire mod twice (once per validator call).
        defined_locs, defined_paths = (
            ScriptedLocalisation.get_all_defined_localisations(
                mod_path=self.mod_path,
                lowercase=False,
                return_paths=True,
                staged_files=self.staged_files,
                workers=self.workers,
                pool=self._pool,
            )
        )
        # Usage scan ALWAYS goes full-repo — even in staged mode. Restricting
        # the usage scan to staged files only would falsely flag any defined-
        # text whose only consumer lives in a non-staged file (e.g. editing
        # 99_PER_scripted_localisation.txt would report every loc as unused
        # if the matching 99_PER_scripted_guis.txt isn't also staged).
        used_locs, used_paths = ScriptedLocalisation.get_all_used_localisations(
            mod_path=self.mod_path,
            defined_names=set(defined_locs),
            lowercase=False,
            return_paths=True,
            staged_files=None,
            workers=self.workers,
            pool=self._pool,
        )

        self.validate_missing_scripted_localisations(
            FALSE_POSITIVES, defined_locs, used_locs, used_paths
        )
        self.validate_unused_scripted_localisations(
            FALSE_POSITIVES, defined_locs, defined_paths, used_locs
        )

        # GFX icon check scans all interface/*.gfx files — skip in staged mode
        if not self.staged_only:
            self.validate_gfx_icons()


if __name__ == "__main__":
    run_validator_main(
        Validator, "Validate scripted localisation in Millennium Dawn mod"
    )
