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

from validator_common import (
    BaseValidator,
    Colors,
    DataCleaner,
    FileOpener,
    find_line_number,
    run_validator_main,
    should_skip_file,
)


# Multiprocessing helper functions
def process_file_for_defined_localisations(
    args: Tuple[str, bool]
) -> Tuple[List[str], Dict[str, str]]:
    filename, lowercase = args

    if should_skip_file(filename):
        return ([], {})

    if "00_scripted_localisation_FR_loc" in filename:
        return ([], {})

    localisations = []
    paths = {}
    basename = os.path.basename(filename)

    text_file = FileOpener.open_text_file(filename, lowercase=lowercase)

    if "defined_text" in text_file and "name =" in text_file:
        pattern_matches = re.findall(
            r"name\s*=\s*([a-zA-Z_0-9]+)", text_file if lowercase else text_file
        )
        if len(pattern_matches) > 0:
            for match in pattern_matches:
                localisations.append(match)
                paths[match] = basename

    return (localisations, paths)


def process_file_for_used_localisations(
    args: Tuple[str, Set[str], bool]
) -> Tuple[List[str], Dict[str, str]]:
    filename, search_names, lowercase = args

    if should_skip_file(filename):
        return ([], {})

    if "scripted_localisation" in filename:
        return ([], {})

    localisations = []
    paths = {}
    basename = os.path.basename(filename)

    text_file = FileOpener.open_text_file(filename, lowercase=lowercase)

    for name in search_names:
        if name in text_file:
            localisations.append(name)
            paths[name] = basename

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
    ):
        localisations = []
        paths = {}

        if staged_files:
            files_to_scan = [
                f
                for f in staged_files
                if "scripted_localisation" in f and f.endswith(".txt")
            ]
        else:
            pattern = os.path.join(mod_path, "common", "scripted_localisation", "*.txt")
            files_to_scan = glob.glob(pattern)

        args_list = [(f, lowercase) for f in files_to_scan]
        with Pool(processes=workers) as pool:
            results = pool.map(
                process_file_for_defined_localisations, args_list, chunksize=10
            )

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
    ):
        localisations = []
        paths = {}

        search_names = (
            {name.lower() for name in defined_names} if lowercase else defined_names
        )

        if staged_files:
            files_to_scan = [
                f
                for f in staged_files
                if f.endswith(".gui")
                or f.endswith(".yml")
                or (f.endswith(".txt") and "scripted_guis" in f)
            ]
        else:
            gui_files = list(glob.iglob(mod_path + "**/*.gui", recursive=True))
            yml_files = list(glob.iglob(mod_path + "**/*.yml", recursive=True))
            scripted_gui_files = list(
                glob.iglob(mod_path + "common/scripted_guis/*.txt", recursive=True)
            )
            files_to_scan = gui_files + yml_files + scripted_gui_files

        args_list = [(f, search_names, lowercase) for f in files_to_scan]
        with Pool(processes=workers) as pool:
            results = pool.map(
                process_file_for_used_localisations, args_list, chunksize=50
            )

        found_names = set()
        for locs_list, paths_dict in results:
            for loc in locs_list:
                if loc not in found_names:
                    localisations.append(loc)
                    paths[loc] = paths_dict[loc]
                    found_names.add(loc)

        return (localisations, paths) if return_paths else localisations


class Validator(BaseValidator):
    TITLE = "SCRIPTED LOCALISATION VALIDATION"
    STAGED_EXTENSIONS = [".txt", ".yml", ".gui"]

    def validate_missing_scripted_localisations(self, false_positives):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking missing scripted localisations (used but not defined)...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        results = []
        defined_locs = ScriptedLocalisation.get_all_defined_localisations(
            mod_path=self.mod_path,
            lowercase=False,
            staged_files=self.staged_files,
            workers=self.workers,
        )

        defined_names_set = set(defined_locs)
        used_locs, paths = ScriptedLocalisation.get_all_used_localisations(
            mod_path=self.mod_path,
            defined_names=defined_names_set,
            lowercase=False,
            return_paths=True,
            staged_files=self.staged_files,
            workers=self.workers,
        )

        defined_locs_lower = [loc.lower() for loc in defined_locs]
        used_locs_lower = [loc.lower() for loc in used_locs]

        used_locs_lower = DataCleaner.clear_false_positives_partial_match(
            used_locs_lower, tuple(false_positives)
        )

        reported = set()
        for i, loc in enumerate(used_locs_lower):
            if loc not in defined_locs_lower and loc not in reported:
                original_loc = used_locs[i]
                basename = paths.get(original_loc, paths.get(loc, "unknown"))
                full_path = self.get_full_path(
                    basename, loc, file_patterns=["**/*.txt", "**/*.gui"]
                )
                if full_path:
                    rel_path = os.path.relpath(full_path, self.mod_path)
                    line_num = find_line_number(full_path, loc, lowercase=True)
                    results.append(
                        {"localisation": loc, "file": rel_path, "line": line_num}
                    )
                    reported.add(loc)

        if len(results) > 0:
            self.log(
                f"{Colors.RED if self.use_colors else ''}Missing scripted localisations were encountered - they are referenced but not defined in common/scripted_localisation/.{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
            self.log(
                f"{Colors.YELLOW if self.use_colors else ''}Note: Some of these may be regular localisation keys rather than scripted localisation. Verify manually.{Colors.ENDC if self.use_colors else ''}",
                "warning",
            )
            for result in results:
                if result["line"] > 0:
                    self.log(
                        f"  {Colors.YELLOW if self.use_colors else ''}{result['file']}:{result['line']}{Colors.ENDC if self.use_colors else ''} - {result['localisation']}",
                        "error",
                    )
                else:
                    self.log(
                        f"  {Colors.YELLOW if self.use_colors else ''}{result['file']}{Colors.ENDC if self.use_colors else ''} - {result['localisation']}",
                        "error",
                    )
            self.log(
                f"{Colors.RED if self.use_colors else ''}{len(results)} issues found{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
            self.errors_found += len(results)
        else:
            self.log(
                f"{Colors.GREEN if self.use_colors else ''}✓ No issues found with missing scripted localisations{Colors.ENDC if self.use_colors else ''}"
            )

    def validate_unused_scripted_localisations(self, false_positives):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking unused scripted localisations (defined but not used)...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        results = []
        defined_locs, paths = ScriptedLocalisation.get_all_defined_localisations(
            mod_path=self.mod_path,
            lowercase=False,
            return_paths=True,
            staged_files=self.staged_files,
            workers=self.workers,
        )

        defined_names_set = set(defined_locs)
        used_locs = ScriptedLocalisation.get_all_used_localisations(
            mod_path=self.mod_path,
            defined_names=defined_names_set,
            lowercase=False,
            staged_files=self.staged_files,
            workers=self.workers,
        )

        defined_locs_lower = [loc.lower() for loc in defined_locs]
        used_locs_lower = [loc.lower() for loc in used_locs]

        defined_locs_lower = DataCleaner.clear_false_positives_partial_match(
            defined_locs_lower, tuple(false_positives)
        )

        reported = set()
        for i, loc in enumerate(defined_locs_lower):
            if loc not in used_locs_lower and loc not in reported:
                original_loc = defined_locs[i]
                basename = paths.get(original_loc, paths.get(loc, "unknown"))

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
                    results.append(
                        {"localisation": loc, "file": rel_path, "line": line_num}
                    )
                    reported.add(loc)

        if len(results) > 0:
            self.log(
                f"{Colors.RED if self.use_colors else ''}Unused scripted localisations were encountered - they are defined but not referenced anywhere.{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
            for result in results:
                if result["line"] > 0:
                    self.log(
                        f"  {Colors.YELLOW if self.use_colors else ''}{result['file']}:{result['line']}{Colors.ENDC if self.use_colors else ''} - {result['localisation']}",
                        "error",
                    )
                else:
                    self.log(
                        f"  {Colors.YELLOW if self.use_colors else ''}{result['file']}{Colors.ENDC if self.use_colors else ''} - {result['localisation']}",
                        "error",
                    )
            self.log(
                f"{Colors.RED if self.use_colors else ''}{len(results)} issues found{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
            self.errors_found += len(results)
        else:
            self.log(
                f"{Colors.GREEN if self.use_colors else ''}✓ No issues found with unused scripted localisations{Colors.ENDC if self.use_colors else ''}"
            )

    def validate_gfx_icons(self):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking GFX_ icon references in scripted localisation against .gfx definitions...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        # Collect all GFX_ names defined in interface/*.gfx
        gfx_path = str(Path(self.mod_path) / "interface") + "/"
        defined_gfx = set()
        for filename in glob.iglob(gfx_path + "**/*.gfx", recursive=True):
            text_file = FileOpener.open_text_file(filename, lowercase=False)
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
            text_file = FileOpener.open_text_file(filename, lowercase=False)
            matches = re.findall(r"localization_key\s*=\s*(GFX_[^\s\}]+)", text_file)
            for gfx_name in matches:
                if gfx_name not in defined_gfx and gfx_name not in reported:
                    rel_path = os.path.relpath(filename, self.mod_path)
                    line_num = find_line_number(filename, gfx_name, lowercase=False)
                    results.append(
                        {"gfx": gfx_name, "file": rel_path, "line": line_num}
                    )
                    reported.add(gfx_name)

        if len(results) > 0:
            self.log(
                f"{Colors.RED if self.use_colors else ''}GFX_ icons referenced in scripted localisation but not defined in interface/*.gfx:{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
            for result in results:
                if result["line"] > 0:
                    self.log(
                        f"  {Colors.YELLOW if self.use_colors else ''}{result['file']}:{result['line']}{Colors.ENDC if self.use_colors else ''} - {result['gfx']}",
                        "error",
                    )
                else:
                    self.log(
                        f"  {Colors.YELLOW if self.use_colors else ''}{result['file']}{Colors.ENDC if self.use_colors else ''} - {result['gfx']}",
                        "error",
                    )
            self.log(
                f"{Colors.RED if self.use_colors else ''}{len(results)} issues found{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
            self.errors_found += len(results)
        else:
            self.log(
                f"{Colors.GREEN if self.use_colors else ''}✓ All GFX_ icons in scripted localisation are defined in .gfx files{Colors.ENDC if self.use_colors else ''}"
            )

    def run_validations(self):
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
            "\u00a7",
            "\u00a3",
            "$",
            "var:",
            "@",
            "[",
        ]
        self.validate_missing_scripted_localisations(FALSE_POSITIVES)
        self.validate_unused_scripted_localisations(FALSE_POSITIVES)
        self.validate_gfx_icons()


if __name__ == "__main__":
    run_validator_main(
        Validator, "Validate scripted localisation in Millennium Dawn mod"
    )
