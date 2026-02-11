#!/usr/bin/env python3
##########################
# Localisation Validation Script (Multiprocessing Optimized)
# Validates localisation files for common issues
# Checks for:
#   1. Duplicated localisation keys
#   2. Unpaired brackets in loc values
#   3. Loc syntax issues (color symbol pairing)
#   4. Missing mandatory l_english: line
#   5. Invalid localization_key references
#   6. add_resistance_target tooltip issues
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
    FileOpener,
    run_validator_main,
    should_skip_file,
)

EXTRA_SKIP_PATTERNS = ["FR_loc", "00_operations"]


def _should_skip(filename: str) -> bool:
    return should_skip_file(filename, extra_skip_patterns=EXTRA_SKIP_PATTERNS)


# --- Multiprocessing helpers ---


def process_yml_for_brackets(args: Tuple[str]) -> List[str]:
    filename = args[0]
    results = []
    text_file = FileOpener.open_text_file(filename)
    lines = text_file.split("\n")[1:]
    for line_idx, line in enumerate(lines):
        if line.count("[") != line.count("]"):
            results.append(
                f"{os.path.basename(filename)} - line {line_idx + 2} - unpaired bracket"
            )
    return results


def process_yml_for_syntax(args: Tuple[str, List[str]]) -> List[str]:
    filename, valid_colors = args
    results = []
    text_file = FileOpener.open_text_file(filename, lowercase=False)
    lines = text_file.split("\n")[1:]
    for line_idx, line in enumerate(lines):
        if "#" in line or line.strip() in ["", "l_english:"]:
            continue
        if "\u00a7" in line and "desc_end" not in line and "U.S.C." not in line:
            count = line.count("\u00a7")
            if count % 2 != 0:
                results.append(
                    f"{os.path.basename(filename)}, line {line_idx + 2}, colors - odd number of \u00a7 symbols ({count})"
                )
            elif count != line.count("\u00a7!") * 2:
                expected = count // 2
                actual = line.count("\u00a7!")
                results.append(
                    f"{os.path.basename(filename)}, line {line_idx + 2}, colors - expected {expected} \u00a7! but got {actual}"
                )
            else:
                try:
                    for idx, ch in enumerate(line):
                        if ch == "\u00a7" and idx + 1 < len(line):
                            next_ch = line[idx + 1]
                            if next_ch not in valid_colors and next_ch not in [
                                "!",
                                "[",
                                "$",
                            ]:
                                results.append(
                                    f"{os.path.basename(filename)}, line {line_idx + 2}, colors - unsupported color '{next_ch}'"
                                )
                except Exception:
                    continue
    return results


def process_yml_for_mandatory(args: Tuple[str]) -> List[str]:
    filename = args[0]
    results = []
    text_file = FileOpener.open_text_file(filename)
    lines = text_file.split("\n")
    if lines == [""]:
        return results
    if not any("l_english:" in line for line in lines):
        results.append(f"{os.path.basename(filename)} - l_english: line is absent")
    return results


def get_all_loc_keys(
    mod_path: str, lowercase: bool = False
) -> Tuple[Dict[str, str], List[str]]:
    filepath = str(Path(mod_path) / "localisation" / "english") + "/"
    results = []
    loc_dict = {}
    duplicated_keys = []

    for filename in glob.iglob(filepath + "**/*.yml", recursive=True):
        text_file = FileOpener.open_text_file(filename, lowercase=lowercase)
        if "l_english" not in text_file:
            continue
        lines = text_file.split("\n")
        for line in lines:
            line = line.strip()
            if ":" not in line or "l_english:" in line or (line and line[0] == "#"):
                continue
            results.append(line)

    for line in results:
        try:
            key = line[: line.index(":")].strip()
            value = line[line.index(":") + 2 :].strip()
            if key in loc_dict:
                duplicated_keys.append(key)
            else:
                loc_dict[key] = value
        except (ValueError, IndexError):
            continue

    return loc_dict, duplicated_keys


def get_all_colors(mod_path: str) -> List[str]:
    filepath = Path(mod_path) / "interface" / "core.gfx"
    if not filepath.exists():
        return list("WGRBYCMwgrbycm!")
    text_file = FileOpener.open_text_file(str(filepath), lowercase=False)
    try:
        textcolors = re.findall(
            r"\ttextcolors = \{.*?^\t\}", text_file, flags=re.DOTALL | re.MULTILINE
        )[0]
        colors = re.findall(
            r"^\t\t(\w) =.*?\n", textcolors, flags=re.DOTALL | re.MULTILINE
        )
        return colors
    except (IndexError, Exception):
        return list("WGRBYCMwgrbycm!")


class Validator(BaseValidator):
    TITLE = "LOCALISATION VALIDATION"
    STAGED_EXTENSIONS = [".txt", ".yml"]

    def _get_yml_files(self) -> List[str]:
        loc_path = str(Path(self.mod_path) / "localisation" / "english") + "/"
        if self.staged_files:
            return [
                f for f in self.staged_files if f.endswith(".yml") and "english" in f
            ]
        return list(glob.iglob(loc_path + "**/*.yml", recursive=True))

    def validate_duplicated_keys(self):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking for duplicated localisation keys...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        _, duplicated = get_all_loc_keys(self.mod_path, lowercase=False)
        self._report(
            duplicated,
            "✓ No duplicated localisation keys",
            "Duplicated localisation keys:",
        )

    def validate_brackets(self):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking for unpaired brackets in localisation...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        yml_files = self._get_yml_files()
        args_list = [(f,) for f in yml_files]

        with Pool(processes=self.workers) as pool:
            all_results = pool.map(process_yml_for_brackets, args_list, chunksize=10)

        results = []
        for file_results in all_results:
            results.extend(file_results)

        self._report(
            results,
            "✓ No unpaired brackets in localisation",
            "Unpaired brackets found in localisation:",
        )

    def validate_syntax(self):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking localisation color syntax...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        valid_colors = get_all_colors(self.mod_path)
        yml_files = self._get_yml_files()
        args_list = [(f, valid_colors) for f in yml_files]

        with Pool(processes=self.workers) as pool:
            all_results = pool.map(process_yml_for_syntax, args_list, chunksize=10)

        results = []
        for file_results in all_results:
            results.extend(file_results)

        self._report(
            results,
            "✓ No localisation color syntax issues",
            "Localisation color syntax issues:",
        )

    def validate_mandatory_line(self):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking mandatory l_english: line in loc files...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        yml_files = self._get_yml_files()
        args_list = [(f,) for f in yml_files]

        with Pool(processes=self.workers) as pool:
            all_results = pool.map(process_yml_for_mandatory, args_list, chunksize=10)

        results = []
        for file_results in all_results:
            results.extend(file_results)

        self._report(
            results,
            "✓ All loc files have mandatory l_english: line",
            "Missing l_english: line in localisation files:",
        )

    def validate_localization_key_references(self):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking localization_key references...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        loc_keys, _ = get_all_loc_keys(self.mod_path, lowercase=False)
        pattern = r"localization_key = ([^ \t\n]*)"
        results = []

        for filename in glob.iglob(self.mod_path + "**/*.txt", recursive=True):
            if _should_skip(filename):
                continue
            text_file = FileOpener.open_text_file(filename, lowercase=False)
            text_file = re.sub(r"^[ \t]*#.*$", "", text_file, flags=re.MULTILINE)
            if "localization_key =" not in text_file:
                continue

            matches = re.findall(pattern, text_file, flags=re.MULTILINE | re.DOTALL)
            for match in matches:
                k = match
                if k in loc_keys:
                    continue
                if "[" in k and "]" in k:
                    continue
                if '"' in k:
                    continue
                if k.startswith("GFX_"):
                    continue
                if "EFFECT_" in k or "TRIGGER_" in k:
                    continue
                if "EUXXX_EP_agenda" in k:
                    continue
                if re.match(r"^EU\d+$", k):
                    continue
                results.append(k)

        results = sorted(set(results))
        self._report(
            results,
            "✓ All localization_key references are valid",
            "Invalid localization_key references (key not found in loc files):",
        )

    def validate_add_resistance_tooltip(self):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking add_resistance_target tooltip localisation...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        loc_keys, _ = get_all_loc_keys(self.mod_path, lowercase=False)
        pattern = r"^(\t+)add_resistance_target = (\{\n.*?)^\1\}"
        results = []

        for filename in glob.iglob(self.mod_path + "**/*.txt", recursive=True):
            if _should_skip(filename):
                continue
            text_file = FileOpener.open_text_file(filename, lowercase=False)
            if "add_resistance_target = {" not in text_file:
                continue

            matches = re.findall(pattern, text_file, flags=re.MULTILINE | re.DOTALL)
            for match in matches:
                body = match[1]
                if "tooltip =" in body:
                    tt = re.findall(r"tooltip = ([^\t \n]+)", body)
                    if tt:
                        tt = tt[0]
                        if tt in loc_keys:
                            if "$VALUE|=-%0$" not in loc_keys[tt]:
                                results.append(
                                    f"{tt} - missing $VALUE|=-%0$ in loc value"
                                )
                        else:
                            if tt.startswith("OTT_"):
                                continue
                            results.append(f"{tt} - localization key not found")
                else:
                    snippet = body.replace("\n", " ").replace("\t", "")[:80]
                    results.append(
                        f"{snippet} - {os.path.basename(filename)} - missing tooltip"
                    )

        self._report(
            results,
            "✓ No add_resistance_target tooltip issues",
            "add_resistance_target tooltip issues:",
        )

    def run_validations(self):
        self.validate_duplicated_keys()
        self.validate_brackets()
        self.validate_syntax()
        self.validate_mandatory_line()
        self.validate_localization_key_references()
        self.validate_add_resistance_tooltip()


if __name__ == "__main__":
    run_validator_main(Validator, "Validate localisation in Millennium Dawn mod")
