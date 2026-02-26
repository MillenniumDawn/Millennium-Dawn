#!/usr/bin/env python3
##########################
# Decision Validation Script (Multiprocessing Optimized)
# Validates decision definitions and usage
# Checks for:
#   1. Duplicated decisions
#   2. Unused decisions (always=no in allowed but never manually activated)
#   3. Unused decision categories (empty categories not used in BOP)
#   4. Decisions with AI factor issues
#   5. Custom cost trigger validation (tooltip presence)
#   6. Targeted decisions without targets (performance issue)
#   7. Decisions with targets but no target_trigger (performance issue)
#   8. Decisions without allowed check in unchecked categories
# Based on Kaiserreich Autotests by Pelmen, https://github.com/Pelmen323
# Adapted for Millennium Dawn with multiprocessing
##########################
import glob
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

from validator_common import (
    BaseValidator,
    Colors,
    FileOpener,
    run_validator_main,
    should_skip_file,
)

EXTRA_SKIP_PATTERNS = ["FR_loc"]

# Decisions activated dynamically (e.g. via variable-constructed IDs) that
# cannot be detected by static analysis and should be excluded from the
# unused-decision check.
DYNAMICALLY_ACTIVATED_DECISIONS = [f"AC_project_{i}_target_decision" for i in range(15)]


def _should_skip(filename: str) -> bool:
    return should_skip_file(filename, extra_skip_patterns=EXTRA_SKIP_PATTERNS)


# --- Decision parsing helpers ---


def extract_value_single_line(obj: str, s: str) -> str:
    pattern = r"\t+" + s + r" = (\S*)"
    matches = re.findall(pattern, obj)
    return matches[0] if f"\t{s} =" in obj and matches else False


def extract_value_multi_line(obj: str, s: str) -> str:
    pattern = r"(\t+)" + s + r" = (\{([^\n]*|.*?^\1)\})"
    if f"\t{s} =" not in obj:
        return False
    matches = re.findall(pattern, obj, flags=re.DOTALL | re.MULTILINE)
    return matches[0][1] if matches else False


class DecisionFactory:
    def __init__(self, dec: str) -> None:
        self.token = re.findall(r"^\t*(.+) = \{", dec, flags=re.MULTILINE)[0]
        self.allowed = extract_value_multi_line(dec, "allowed")
        self.available = extract_value_multi_line(dec, "available")
        self.visible = extract_value_multi_line(dec, "visible")
        self.cancel_effect = extract_value_multi_line(dec, "cancel_effect")
        self.complete_effect = extract_value_multi_line(dec, "complete_effect")
        self.remove_effect = extract_value_multi_line(dec, "remove_effect")
        self.cancel_trigger = extract_value_multi_line(dec, "cancel_trigger")
        self.cancel_if_not_visible = "cancel_if_not_visible = yes" in dec
        self.target_root_trigger = extract_value_multi_line(dec, "target_root_trigger")
        self.target_trigger = extract_value_multi_line(dec, "target_trigger")
        self.targets = extract_value_multi_line(dec, "targets")
        self.target_array = extract_value_single_line(dec, "target_array")
        self.mission_subtype = "\tdays_mission_timeout =" in dec
        self.selectable_mission = (
            "\tdays_mission_timeout =" in dec and "selectable_mission = yes" in dec
        )
        self.ai_factor = extract_value_multi_line(dec, "ai_will_do")
        self.custom_cost_trigger = extract_value_multi_line(dec, "custom_cost_trigger")
        self.custom_cost_text = extract_value_single_line(dec, "custom_cost_text")
        self.ai_hint_pp_cost = extract_value_single_line(dec, "ai_hint_pp_cost")
        self.cost = extract_value_single_line(dec, "cost")
        self.has_tooltip = "tooltip =" in dec


def parse_all_decisions(
    mod_path: str, lowercase: bool = False
) -> Tuple[List[str], Dict[str, str]]:
    filepath = str(Path(mod_path) / "common" / "decisions")
    pattern = re.compile(r"^\t[^\t#]+ = \{.*?^\t\}", flags=re.MULTILINE | re.DOTALL)
    decisions = []
    paths = {}

    for filename in glob.iglob(filepath + "/**/*.txt", recursive=True):
        if "categories" in filename:
            continue
        text_file = FileOpener.open_text_file(
            filename, lowercase=lowercase, strip_comments_flag=True
        )
        matches = pattern.findall(text_file)
        for match in matches:
            decisions.append(match)
            paths[match] = os.path.basename(filename)

    return decisions, paths


def parse_all_decision_names(
    mod_path: str, lowercase: bool = False
) -> Tuple[List[str], Dict[str, str]]:
    decisions, dec_paths = parse_all_decisions(mod_path, lowercase)
    pattern = re.compile(r"^\t(.+) =", flags=re.MULTILINE)
    names = []
    name_paths = {}
    for d in decisions:
        name = pattern.findall(d)[0]
        names.append(name)
        name_paths[name] = dec_paths[d]
    return names, name_paths


def parse_decision_categories(
    mod_path: str, lowercase: bool = False, visible_when_empty: bool = True
) -> Dict[str, str]:
    filepath = str(Path(mod_path) / "common" / "decisions" / "categories")
    categories = {}
    cat_pattern = re.compile(r"^\w* = \{.*?^\}", flags=re.DOTALL | re.MULTILINE)
    name_pattern = re.compile(r"^(.*) = \{")

    for filename in glob.iglob(filepath + "/**/*.txt", recursive=True):
        text_file = FileOpener.open_text_file(
            filename, lowercase=lowercase, strip_comments_flag=True
        )
        matches = re.findall(cat_pattern, text_file)
        for match in matches:
            if not visible_when_empty and "visible_when_empty = yes" in match:
                continue
            name = re.findall(name_pattern, match)
            if name:
                categories[name[0]] = match

    return categories


def parse_categories_with_decisions(
    mod_path: str, lowercase: bool = False, visible_when_empty: bool = True
) -> Dict[str, List[str]]:
    filepath = str(Path(mod_path) / "common" / "decisions")
    category_names = list(
        parse_decision_categories(mod_path, lowercase, visible_when_empty).keys()
    )
    result = {cat: [] for cat in category_names}
    dec_pattern = re.compile(r"^\t(\S+) = \{", flags=re.MULTILINE)

    for filename in glob.iglob(filepath + "/**/*.txt", recursive=True):
        if "categories" in filename:
            continue
        text_file = FileOpener.open_text_file(
            filename, lowercase=lowercase, strip_comments_flag=True
        )
        for category in category_names:
            if f"{category} = {{" in text_file:
                pattern = r"^" + re.escape(category) + r" = \{.*?^\}"
                matches = re.findall(pattern, text_file, flags=re.DOTALL | re.MULTILINE)
                for match in matches:
                    dec_names = dec_pattern.findall(match)
                    result[category].extend(dec_names)

    return result


class Validator(BaseValidator):
    TITLE = "DECISION VALIDATION"
    STAGED_EXTENSIONS = [".txt"]

    def __init__(self, *args, fix: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.fix = fix

    def _apply_ai_factor_fixes(self, fixes: list):
        """Insert a default ai_will_do = { base = 0 } block into decisions missing one."""
        dec_filepath = str(Path(self.mod_path) / "common" / "decisions")

        by_file: Dict[str, List[str]] = {}
        for token, basename in fixes:
            by_file.setdefault(basename, []).append(token)

        fixed_total = 0
        for basename, tokens in by_file.items():
            target_file = None
            for filepath in glob.iglob(dec_filepath + "/**/*.txt", recursive=True):
                if os.path.basename(filepath) == basename:
                    target_file = filepath
                    break

            if not target_file:
                self.log(f"  Could not locate file: {basename}", "warning")
                continue

            with open(target_file, "r", encoding="utf-8-sig") as f:
                content = f.read()

            for token in tokens:
                pattern = re.compile(
                    r"(^\t" + re.escape(token) + r" = \{.*?)(^\t\})",
                    flags=re.MULTILINE | re.DOTALL,
                )

                def _inserter(m):
                    return (
                        m.group(1)
                        + "\t\tai_will_do = {\n\t\t\tbase = 0\n\t\t}\n"
                        + m.group(2)
                    )

                new_content, count = pattern.subn(_inserter, content)
                if count:
                    content = new_content
                    fixed_total += 1
                else:
                    self.log(f"  Could not patch {token} in {basename}", "warning")

            with open(target_file, "w", encoding="utf-8-sig") as f:
                f.write(content)

        self.log(
            f"{Colors.GREEN if self.use_colors else ''}  Auto-fixed {fixed_total} decision(s) with missing ai_will_do{Colors.ENDC if self.use_colors else ''}"
        )

    def validate_duplicated_decisions(self):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking for duplicated decisions...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        names, paths = parse_all_decision_names(self.mod_path)
        self.log(f"  Found {len(names)} total decisions")
        results = [f"{n} - {paths[n]}" for n in names if names.count(n) > 1]
        results = sorted(set(results))
        self._report(
            results, "✓ No duplicated decisions", "Duplicated decisions found:"
        )

    def validate_unused_decisions(self):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking for unused decisions (always=no but never activated)...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        decisions, paths = parse_all_decisions(self.mod_path)
        pattern_decision = re.compile(r"activate_targeted_decision = [^\n\t]*")
        pattern_mission = re.compile(r"activate_mission = \S*")
        manual_decisions = {}
        manual_missions = {}

        for dec_code in decisions:
            d = DecisionFactory(dec=dec_code)
            if d.allowed:
                if "always = no" in d.allowed and not d.mission_subtype:
                    manual_decisions[d.token] = 0
                elif "always = no" in d.allowed and d.mission_subtype:
                    manual_missions[d.token] = 0

        for filename in glob.iglob(self.mod_path + "**/*.txt", recursive=True):
            if _should_skip(filename):
                continue
            text_file = FileOpener.open_text_file(
                filename, lowercase=False, strip_comments_flag=True
            )
            if "activate_targeted_decision =" in text_file:
                remaining = {k: v for k, v in manual_decisions.items() if v == 0}
                all_matches = pattern_decision.findall(text_file)
                for dec in remaining:
                    for match in all_matches:
                        if f"decision = {dec}" in match:
                            manual_decisions[dec] += 1
            if "activate_mission =" in text_file:
                remaining = {k: v for k, v in manual_missions.items() if v == 0}
                all_matches = pattern_mission.findall(text_file)
                for mission in remaining:
                    if f"activate_mission = {mission}" in all_matches:
                        manual_missions[mission] += 1

        results = [
            k
            for k in manual_decisions
            if manual_decisions[k] == 0 and k not in DYNAMICALLY_ACTIVATED_DECISIONS
        ]
        results += [
            k
            for k in manual_missions
            if manual_missions[k] == 0 and k not in DYNAMICALLY_ACTIVATED_DECISIONS
        ]
        self._report(
            results,
            "✓ No unused decisions",
            "Unused decisions (always=no but never manually activated):",
        )

    def validate_unused_categories(self):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking for unused decision categories...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        cats_with_decisions = parse_categories_with_decisions(
            self.mod_path, visible_when_empty=False
        )
        cats_to_validate = {
            cat: 0 for cat in cats_with_decisions if cats_with_decisions[cat] == []
        }

        if not cats_to_validate:
            self.log(
                f"{Colors.GREEN if self.use_colors else ''}✓ No empty decision categories{Colors.ENDC if self.use_colors else ''}"
            )
            return

        bop_path = str(Path(self.mod_path) / "common" / "bop")
        found_files = False
        for filename in glob.iglob(bop_path + "/**/*.txt", recursive=True):
            found_files = True
            text_file = FileOpener.open_text_file(
                filename, lowercase=False, strip_comments_flag=True
            )
            not_found = [c for c in cats_to_validate if cats_to_validate[c] == 0]
            for cat in not_found:
                if f"decision_category = {cat}" in text_file:
                    cats_to_validate[cat] += 1

        if not found_files:
            self.log(
                f"{Colors.YELLOW if self.use_colors else ''}No BOP files found, skipping BOP check{Colors.ENDC if self.use_colors else ''}",
                "warning",
            )

        results = [cat for cat in cats_to_validate if cats_to_validate[cat] == 0]
        self._report(
            results,
            "✓ No unused decision categories",
            "Unused decision categories (empty, not in BOP):",
        )

    def validate_ai_factors(self):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking decision AI factors...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        decisions, paths = parse_all_decisions(self.mod_path)
        categories = parse_decision_categories(self.mod_path)
        cats_with_decs = parse_categories_with_decisions(self.mod_path)
        results = []
        fixes_needed = []

        for dec_code in decisions:
            d = DecisionFactory(dec=dec_code)
            if d.available and any(
                ["is_ai = no" in d.available, "always = no" in d.available]
            ):
                continue
            if d.visible and any(
                ["is_ai = no" in d.visible, "always = no" in d.visible]
            ):
                continue

            dec_category = None
            for cat in cats_with_decs:
                if d.token in cats_with_decs[cat]:
                    dec_category = cat
                    break
            if dec_category and dec_category in categories:
                cat_code = categories[dec_category]
                if "is_ai = no" in cat_code or "always = no" in cat_code:
                    continue

            if d.mission_subtype:
                if d.selectable_mission and not d.ai_factor:
                    results.append(
                        f"{d.token} - {paths[dec_code]} - Selectable mission missing AI factor"
                    )
                elif not d.selectable_mission and d.ai_factor:
                    results.append(
                        f"{d.token} - {paths[dec_code]} - Non-selectable mission has AI factor"
                    )
            elif not d.ai_factor and "debug" not in d.token:
                results.append(
                    f"{d.token} - {paths[dec_code]} - Decision missing AI factor"
                )
                if self.fix:
                    fixes_needed.append((d.token, paths[dec_code]))

            if d.ai_factor:
                ai_factors = re.findall(
                    r"(base = \S+|factor = \S+|add = \S+)", d.ai_factor
                )
                if len(ai_factors) > 0 and "base =" in d.ai_factor:
                    if "factor = 0" in ai_factors:
                        num_zeroed = ai_factors.count("factor = 0")
                        for idx in range(1, num_zeroed):
                            if ai_factors[idx] != "factor = 0":
                                results.append(
                                    f"{d.token} - {paths[dec_code]} - Zeroed AI factors not evaluated immediately"
                                )
                                break

        self._report(results, "✓ No AI factor issues", "Decision AI factor issues:")

        if self.fix and fixes_needed:
            self._apply_ai_factor_fixes(fixes_needed)

    def validate_custom_cost_trigger(self):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking decisions with custom_cost_trigger have a tooltip...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        decisions, paths = parse_all_decisions(self.mod_path)
        results = []

        for dec_code in decisions:
            d = DecisionFactory(dec=dec_code)
            if d.custom_cost_trigger and not d.has_tooltip and not d.custom_cost_text:
                results.append(
                    f"{d.token:<55}{paths[dec_code]} - has custom_cost_trigger but no tooltip or custom_cost_text"
                )

        self._report(
            results,
            "✓ No custom cost trigger issues",
            "Decisions with custom_cost_trigger but missing tooltip:",
        )

    def validate_targeted_without_target(self):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking targeted decisions without targets (performance)...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        decisions, paths = parse_all_decisions(self.mod_path)
        results = []

        for dec_code in decisions:
            d = DecisionFactory(dec=dec_code)
            if d.target_root_trigger or d.target_trigger:
                if not d.targets and not d.target_array:
                    if not d.allowed or "always = no" not in d.allowed:
                        results.append(f"{d.token:<55}{paths[dec_code]}")

        self._report(
            results,
            "✓ No targeted decisions without targets",
            "Decisions with target_root_trigger/target_trigger but no targets (checks every country daily):",
        )

    def validate_targets_no_trigger(self):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking decisions with targets but no target_trigger (performance)...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        decisions, paths = parse_all_decisions(self.mod_path)
        results = []

        for dec_code in decisions:
            d = DecisionFactory(dec=dec_code)
            if d.targets or d.target_array:
                if not d.target_trigger:
                    results.append(f"{d.token:<55}{paths[dec_code]}")

        self._report(
            results,
            "✓ No decisions with targets but no target_trigger",
            "Decisions with targets but no target_trigger (falls back to slower available/visible checks):",
        )

    def validate_without_allowed_check(self):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking decisions without allowed trigger in unchecked categories...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        cats_with_decs = parse_categories_with_decisions(self.mod_path)
        decisions, _ = parse_all_decisions(self.mod_path)
        categories = parse_decision_categories(self.mod_path)

        unchecked_cats = []
        for cat, cat_code in categories.items():
            if "allowed = {" not in cat_code:
                unchecked_cats.append(cat)

        decisions_to_check = []
        for cat in unchecked_cats:
            if cat in cats_with_decs:
                decisions_to_check.extend(cats_with_decs[cat])

        results = []
        for dec_code in decisions:
            d = DecisionFactory(dec=dec_code)
            if d.token in decisions_to_check:
                if not d.allowed:
                    results.append(d.token)

        self._report(
            results,
            "✓ No decisions missing allowed check",
            "Decisions in categories without allowed check that also lack their own allowed trigger:",
        )

    def run_validations(self):
        self.validate_duplicated_decisions()
        self.validate_unused_decisions()
        self.validate_unused_categories()
        self.validate_ai_factors()
        self.validate_custom_cost_trigger()
        self.validate_targeted_without_target()
        self.validate_targets_no_trigger()
        self.validate_without_allowed_check()


def _add_extra_args(parser):
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Auto-insert 'ai_will_do = { base = 0 }' into decisions missing an AI factor",
    )


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate decisions in Millennium Dawn mod",
        extra_args_fn=_add_extra_args,
    )
