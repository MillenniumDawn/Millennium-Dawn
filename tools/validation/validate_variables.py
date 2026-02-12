#!/usr/bin/env python3
##########################
# Comprehensive Variable and Event Target Validation Script (Multiprocessing Optimized)
# Validates flags (country/state/global) and event targets
# Checks for: cleared but not set, used but not set, and unused items
# Based on Kaiserreich Autotests by Pelmen, https://github.com/Pelmen323
# Optimized with multiprocessing for significantly faster execution
##########################
import glob
import os
import re
from multiprocessing import Pool
from typing import Dict, List, Optional, Tuple

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
def process_file_for_flags(
    args: Tuple[str, bool, str, str]
) -> Tuple[List[str], Dict[str, str], str]:
    filename, lowercase, flag_type, operation = args

    if should_skip_file(filename):
        return ([], {}, operation)

    flags = []
    paths = {}
    basename = os.path.basename(filename)
    text_file = FileOpener.open_text_file(
        filename, lowercase=lowercase, strip_comments_flag=True
    )

    if operation == "used":
        if (
            f"has_{flag_type}_flag =" in text_file
            or f"modify_{flag_type}_flag =" in text_file
        ):
            pattern_matches = re.findall(
                r"has_" + flag_type + r"_flag = ([^ \t\n]+)", text_file
            )
            for match in pattern_matches:
                flags.append(match)
                paths[match] = basename

            pattern_matches = re.findall(
                r"[y|s]_" + flag_type + r"_flag = \{.*?flag = ([^ \t\n\}]+).*?\}",
                text_file,
                flags=re.MULTILINE | re.DOTALL,
            )
            for match in pattern_matches:
                flags.append(match)
                paths[match] = basename

    elif operation == "set":
        if f"set_{flag_type}_flag =" in text_file:
            pattern_matches = re.findall(
                r"set_" + flag_type + r"_flag = ([^ \t\n]+)", text_file
            )
            for match in pattern_matches:
                flags.append(match)
                paths[match] = basename

            pattern_matches = re.findall(
                r"set_" + flag_type + r"_flag = \{.*?flag = ([^ \t\n\}]+).*?\}",
                text_file,
                flags=re.MULTILINE | re.DOTALL,
            )
            for match in pattern_matches:
                flags.append(match)
                paths[match] = basename

    elif operation == "cleared":
        if f"clr_{flag_type}_flag =" in text_file:
            pattern_matches = re.findall(
                r"clr_" + flag_type + r"_flag = ([^ \t\n]+)", text_file
            )
            for match in pattern_matches:
                flags.append(match)
                paths[match] = basename

    return (flags, paths, operation)


def process_file_for_targets(
    args: Tuple[str, bool, str]
) -> Tuple[List[str], Dict[str, str], str]:
    filename, lowercase, operation = args

    if should_skip_file(filename):
        return ([], {}, operation)

    targets = []
    paths = {}
    basename = os.path.basename(filename)
    text_file = FileOpener.open_text_file(
        filename, lowercase=lowercase, strip_comments_flag=True
    )

    if operation == "used":
        if "tag_aliases" in filename:
            if "global_event_target =" in text_file:
                pattern_matches = re.findall(
                    r'global_event_target = ([^ \n\t\#"]+)', text_file
                )
                for match in pattern_matches:
                    targets.append(match)
                    paths[match] = basename
        else:
            if "event_target:" in text_file:
                pattern_matches = re.findall(r'event_target:([^ \n\t\#"]+)', text_file)
                for match in pattern_matches:
                    targets.append(match)
                    paths[match] = basename

            if "has_event_target =" in text_file:
                pattern_matches = re.findall(
                    r'has_event_target = ([^ \n\t"]+)', text_file
                )
                for match in pattern_matches:
                    targets.append(match)
                    paths[match] = basename

    elif operation == "set":
        if "tag_aliases" not in filename:
            if "save_global_event_target_as =" in text_file:
                pattern_matches = re.findall(
                    r'save_global_event_target_as = ([^ \n\t\#"]+)', text_file
                )
                for match in pattern_matches:
                    targets.append(match)
                    paths[match] = basename

            if "save_event_target_as =" in text_file:
                pattern_matches = re.findall(
                    r'save_event_target_as = ([^ \n\t\#"]+)', text_file
                )
                for match in pattern_matches:
                    targets.append(match)
                    paths[match] = basename

    elif operation == "cleared":
        if "clear_global_event_target =" in text_file:
            pattern_matches = re.findall(
                r'clear_global_event_target = ([^ \n\t\#"]+)', text_file
            )
            for match in pattern_matches:
                targets.append(match)
                paths[match] = basename

    return (targets, paths, operation)


class Variables:
    @classmethod
    def _get_flags(
        cls, mod_path, lowercase, flag_type, operation, staged_files, workers
    ):
        flags = []
        paths = {}
        if flag_type not in ["country", "state", "global"]:
            raise ValueError(
                "Unsupported flag value passed. Expected country, state, global"
            )

        if staged_files:
            files_to_scan = [f for f in staged_files if f.endswith(".txt")]
        else:
            files_to_scan = list(glob.iglob(mod_path + "**/*.txt", recursive=True))

        args_list = [(f, lowercase, flag_type, operation) for f in files_to_scan]
        with Pool(processes=workers) as pool:
            results = pool.map(process_file_for_flags, args_list, chunksize=50)

        for flags_list, paths_dict, _ in results:
            flags.extend(flags_list)
            paths.update(paths_dict)

        return (flags, paths)

    @classmethod
    def get_all_used_flags(
        cls,
        mod_path,
        lowercase=True,
        flag_type="country",
        return_paths=False,
        staged_files=None,
        workers=None,
    ):
        flags, paths = cls._get_flags(
            mod_path, lowercase, flag_type, "used", staged_files, workers
        )
        return (flags, paths) if return_paths else flags

    @classmethod
    def get_all_set_flags(
        cls,
        mod_path,
        lowercase=True,
        flag_type="country",
        return_paths=False,
        staged_files=None,
        workers=None,
    ):
        flags, paths = cls._get_flags(
            mod_path, lowercase, flag_type, "set", staged_files, workers
        )
        return (flags, paths) if return_paths else flags

    @classmethod
    def get_all_cleared_flags(
        cls,
        mod_path,
        lowercase=True,
        flag_type="country",
        return_paths=False,
        staged_files=None,
        workers=None,
    ):
        flags, paths = cls._get_flags(
            mod_path, lowercase, flag_type, "cleared", staged_files, workers
        )
        return (flags, paths) if return_paths else flags


class EventTargets:
    @classmethod
    def _get_targets(cls, mod_path, lowercase, operation, staged_files, workers):
        targets = []
        paths = {}

        if staged_files:
            files_to_scan = [f for f in staged_files if f.endswith(".txt")]
        else:
            files_to_scan = list(glob.iglob(mod_path + "**/*.txt", recursive=True))

        args_list = [(f, lowercase, operation) for f in files_to_scan]
        with Pool(processes=workers) as pool:
            results = pool.map(process_file_for_targets, args_list, chunksize=50)

        for targets_list, paths_dict, _ in results:
            targets.extend(targets_list)
            paths.update(paths_dict)

        return (targets, paths)

    @classmethod
    def get_all_used_targets(
        cls,
        mod_path,
        lowercase=True,
        return_paths=False,
        staged_files=None,
        workers=None,
    ):
        targets, paths = cls._get_targets(
            mod_path, lowercase, "used", staged_files, workers
        )
        return (targets, paths) if return_paths else targets

    @classmethod
    def get_all_set_targets(
        cls,
        mod_path,
        lowercase=True,
        return_paths=False,
        staged_files=None,
        workers=None,
    ):
        targets, paths = cls._get_targets(
            mod_path, lowercase, "set", staged_files, workers
        )
        return (targets, paths) if return_paths else targets

    @classmethod
    def get_all_cleared_targets(
        cls,
        mod_path,
        lowercase=True,
        return_paths=False,
        staged_files=None,
        workers=None,
    ):
        targets, paths = cls._get_targets(
            mod_path, lowercase, "cleared", staged_files, workers
        )
        return (targets, paths) if return_paths else targets


class Validator(BaseValidator):
    TITLE = "VARIABLE AND EVENT TARGET VALIDATION"
    STAGED_EXTENSIONS = [".txt", ".yml"]

    def _report_with_locations(self, results: list, ok_msg: str, fail_msg: str):
        if len(results) > 0:
            self.log(
                f"{Colors.RED if self.use_colors else ''}{fail_msg}{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
            for result in results:
                if result["line"] > 0:
                    self.log(
                        f"  {Colors.YELLOW if self.use_colors else ''}{result['file']}:{result['line']}{Colors.ENDC if self.use_colors else ''} - {result.get('flag', result.get('target', ''))}",
                        "error",
                    )
                else:
                    self.log(
                        f"  {Colors.YELLOW if self.use_colors else ''}{result['file']}{Colors.ENDC if self.use_colors else ''} - {result.get('flag', result.get('target', ''))}",
                        "error",
                    )
            self.log(
                f"{Colors.RED if self.use_colors else ''}{len(results)} issues found{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
            self.errors_found += len(results)
        else:
            self.log(
                f"{Colors.GREEN if self.use_colors else ''}{ok_msg}{Colors.ENDC if self.use_colors else ''}"
            )

    def validate_cleared_flags(self, flag_type: str, false_positives: list):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking cleared {flag_type} flags that are never set...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        results = []
        cleared_flags, paths = Variables.get_all_cleared_flags(
            mod_path=self.mod_path,
            lowercase=False,
            flag_type=flag_type,
            return_paths=True,
            staged_files=self.staged_files,
            workers=self.workers,
        )
        set_flags = Variables.get_all_set_flags(
            mod_path=self.mod_path,
            flag_type=flag_type,
            lowercase=False,
            staged_files=self.staged_files,
            workers=self.workers,
        )
        cleared_flags = DataCleaner.clear_false_positives_partial_match(
            cleared_flags, tuple(false_positives)
        )

        for flag in cleared_flags:
            if flag not in set_flags:
                basename = paths[flag]
                full_path = self.get_full_path(
                    basename, f"clr_{flag_type}_flag = {flag}"
                )
                if full_path:
                    rel_path = os.path.relpath(full_path, self.mod_path)
                    line_num = find_line_number(
                        full_path, f"clr_{flag_type}_flag = {flag}", lowercase=False
                    )
                    results.append({"flag": flag, "file": rel_path, "line": line_num})

        self._report_with_locations(
            results,
            f"✓ No issues found with cleared {flag_type} flags",
            f"Cleared {flag_type} flags that are never set were encountered. Flags with @ are skipped.",
        )

    def validate_missing_flags(self, flag_type: str, false_positives: list):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking missing {flag_type} flags (used but not set)...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        results = []
        used_flags, paths = Variables.get_all_used_flags(
            mod_path=self.mod_path,
            lowercase=False,
            flag_type=flag_type,
            return_paths=True,
            staged_files=self.staged_files,
            workers=self.workers,
        )
        set_flags = Variables.get_all_set_flags(
            mod_path=self.mod_path,
            lowercase=False,
            flag_type=flag_type,
            staged_files=self.staged_files,
            workers=self.workers,
        )
        used_flags = DataCleaner.clear_false_positives_partial_match(
            used_flags, tuple(false_positives)
        )

        for flag in used_flags:
            if flag not in set_flags:
                basename = paths[flag]
                full_path = self.get_full_path(
                    basename, f"has_{flag_type}_flag = {flag}"
                )
                if full_path:
                    rel_path = os.path.relpath(full_path, self.mod_path)
                    line_num = find_line_number(
                        full_path, f"has_{flag_type}_flag = {flag}", lowercase=False
                    )
                    results.append({"flag": flag, "file": rel_path, "line": line_num})

        self._report_with_locations(
            results,
            f"✓ No issues found with missing {flag_type} flags",
            f"Missing {flag_type} flags were encountered - they are not set via 'set_{flag_type}_flag'. Flags with @ are skipped.",
        )

    def validate_unused_flags(self, flag_type: str, false_positives: list):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking unused {flag_type} flags (set but not used)...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        results = []
        set_flags, paths = Variables.get_all_set_flags(
            mod_path=self.mod_path,
            lowercase=False,
            flag_type=flag_type,
            return_paths=True,
            staged_files=self.staged_files,
            workers=self.workers,
        )
        used_flags = Variables.get_all_used_flags(
            mod_path=self.mod_path,
            lowercase=False,
            flag_type=flag_type,
            staged_files=self.staged_files,
            workers=self.workers,
        )
        set_flags = DataCleaner.clear_false_positives_partial_match(
            set_flags, tuple(false_positives)
        )

        for flag in set_flags:
            if flag not in used_flags:
                basename = paths[flag]
                full_path = self.get_full_path(
                    basename, f"set_{flag_type}_flag = {flag}"
                )
                if full_path:
                    rel_path = os.path.relpath(full_path, self.mod_path)
                    line_num = find_line_number(
                        full_path, f"set_{flag_type}_flag = {flag}", lowercase=False
                    )
                    results.append({"flag": flag, "file": rel_path, "line": line_num})

        self._report_with_locations(
            results,
            f"✓ No issues found with unused {flag_type} flags",
            f"Unused {flag_type} flags were encountered - they are not used via 'has_{flag_type}_flag' at least once. Flags with @ are skipped.",
        )

    def validate_cleared_event_targets(self):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking cleared event targets that are not set...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        results = []
        cleared_targets, paths = EventTargets.get_all_cleared_targets(
            mod_path=self.mod_path,
            lowercase=False,
            return_paths=True,
            staged_files=self.staged_files,
            workers=self.workers,
        )
        set_targets = EventTargets.get_all_set_targets(
            mod_path=self.mod_path,
            lowercase=False,
            staged_files=self.staged_files,
            workers=self.workers,
        )

        for target in cleared_targets:
            if target not in set_targets:
                basename = paths[target]
                full_path = self.get_full_path(
                    basename, f"clear_global_event_target = {target}"
                )
                if full_path:
                    rel_path = os.path.relpath(full_path, self.mod_path)
                    line_num = find_line_number(
                        full_path,
                        f"clear_global_event_target = {target}",
                        lowercase=False,
                    )
                    results.append(
                        {"target": target, "file": rel_path, "line": line_num}
                    )

        self._report_with_locations(
            results,
            "✓ No issues found with cleared event targets",
            "Cleared event targets that are not set were encountered.",
        )

    def validate_missing_event_targets(self):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking missing event targets (used but not set)...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        FALSE_POSITIVES = ["."]
        results = []
        used_targets, paths = EventTargets.get_all_used_targets(
            mod_path=self.mod_path,
            lowercase=False,
            return_paths=True,
            staged_files=self.staged_files,
            workers=self.workers,
        )
        set_targets = EventTargets.get_all_set_targets(
            mod_path=self.mod_path,
            lowercase=False,
            staged_files=self.staged_files,
            workers=self.workers,
        )
        used_targets = DataCleaner.clear_false_positives_partial_match(
            used_targets, tuple(FALSE_POSITIVES)
        )

        for target in used_targets:
            if target not in set_targets:
                basename = paths[target]
                full_path = self.get_full_path(basename, f"event_target:{target}")
                if not full_path:
                    full_path = self.get_full_path(
                        basename, f"has_event_target = {target}"
                    )
                if full_path:
                    rel_path = os.path.relpath(full_path, self.mod_path)
                    line_num = find_line_number(
                        full_path, f"event_target:{target}", lowercase=False
                    )
                    if line_num == 0:
                        line_num = find_line_number(
                            full_path, f"has_event_target = {target}", lowercase=False
                        )
                    results.append(
                        {"target": target, "file": rel_path, "line": line_num}
                    )

        self._report_with_locations(
            results,
            "✓ No issues found with missing event targets",
            "Used event targets that are not set were encountered.",
        )

    def validate_unused_event_targets(self):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking unused event targets (set but not used)...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        FALSE_POSITIVES = ["wca_usa_floyd_olson", "wca_usa_al_smith", "target_value"]
        results = []
        potential_results = []
        set_targets, paths = EventTargets.get_all_set_targets(
            mod_path=self.mod_path,
            lowercase=False,
            return_paths=True,
            staged_files=self.staged_files,
            workers=self.workers,
        )
        used_targets = EventTargets.get_all_used_targets(
            mod_path=self.mod_path,
            lowercase=False,
            staged_files=self.staged_files,
            workers=self.workers,
        )
        set_targets = DataCleaner.clear_false_positives_partial_match(
            set_targets, tuple(FALSE_POSITIVES)
        )

        for target in set_targets:
            if target not in used_targets:
                potential_results.append(target)

        targets_used_in_loc = []
        if self.staged_files:
            yml_files_to_scan = [f for f in self.staged_files if f.endswith(".yml")]
        else:
            yml_files_to_scan = glob.iglob(self.mod_path + "**/*.yml", recursive=True)

        for filename in yml_files_to_scan:
            if should_skip_file(filename):
                continue
            text_file = FileOpener.open_text_file(filename, strip_comments_flag=True)

            if ".get" in text_file:
                not_encountered_targets = [
                    i for i in potential_results if i not in targets_used_in_loc
                ]
                for target in not_encountered_targets:
                    if (
                        f"[{target}.getname" in text_file
                        or f"[{target}.getadjective" in text_file
                    ):
                        targets_used_in_loc.append(target)

        for target in potential_results:
            if target not in targets_used_in_loc:
                basename = paths[target]
                full_path = self.get_full_path(
                    basename, f"save_event_target_as = {target}"
                )
                if not full_path:
                    full_path = self.get_full_path(
                        basename, f"save_global_event_target_as = {target}"
                    )
                if full_path:
                    rel_path = os.path.relpath(full_path, self.mod_path)
                    line_num = find_line_number(
                        full_path, f"save_event_target_as = {target}", lowercase=False
                    )
                    if line_num == 0:
                        line_num = find_line_number(
                            full_path,
                            f"save_global_event_target_as = {target}",
                            lowercase=False,
                        )
                    results.append(
                        {"target": target, "file": rel_path, "line": line_num}
                    )

        self._report_with_locations(
            results,
            "✓ No issues found with unused event targets",
            "Unused event targets were encountered.",
        )

    def run_validations(self):
        FALSE_POSITIVES_GENERIC = ["@", "[", "{"]
        FALSE_POSITIVES_COUNTRY = [
            "@",
            "[",
            "{",
            "ire_got_guarantee",
            "ire_rejected_guarantee",
            "nfa_rebelled",
            "ire_alliance_refused",
            "nfa_previously_rebelled",
            "rom_deal",
            "rus_can_core",
            "sent_volunteers",
            "china_refused_alliance",
            "_QMV_voted",
            "recognised_opponent_",
            "rival_government_",
            "_QMV",
            "trade_agreement",
            "mutual_investment_treaty_",
            "libya_casablanca_accords_signed_by_",
            "_EP_agenda",
            "initiated_blockade_",
        ]
        FALSE_POSITIVES_GLOBAL = [
            "@",
            "[",
            "{",
            "kr_current_version",
            "_QMV_result",
            "_QMV_voted",
        ]
        FALSE_POSITIVES_COUNTRY_UNUSED = [
            "@",
            "[",
            "{",
            "saf_antagonise_",
            "default_puppet",
            "_QMV_voted",
            "_EP_approval",
            "recognised_opponent_",
        ]

        for flag_type, fp_cleared, fp_missing, fp_unused in [
            (
                "country",
                FALSE_POSITIVES_COUNTRY,
                FALSE_POSITIVES_COUNTRY,
                FALSE_POSITIVES_COUNTRY_UNUSED,
            ),
            (
                "global",
                FALSE_POSITIVES_GENERIC,
                FALSE_POSITIVES_GENERIC,
                FALSE_POSITIVES_GLOBAL,
            ),
            (
                "state",
                FALSE_POSITIVES_GENERIC,
                FALSE_POSITIVES_GENERIC,
                FALSE_POSITIVES_GENERIC,
            ),
        ]:
            self.validate_cleared_flags(flag_type, fp_cleared)
            self.validate_missing_flags(flag_type, fp_missing)
            self.validate_unused_flags(flag_type, fp_unused)

        self.validate_cleared_event_targets()
        self.validate_missing_event_targets()
        self.validate_unused_event_targets()


if __name__ == "__main__":
    run_validator_main(
        Validator, "Validate variables and event targets in Millennium Dawn mod"
    )
