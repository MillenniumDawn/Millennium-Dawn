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
#   6. Missing custom_effect_tooltip / custom_trigger_tooltip keys
#   7. add_resistance_target tooltip issues
#   8. Orphaned _tt tooltip keys (defined in loc but never referenced)
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

EXTRA_SKIP_PATTERNS = ["FR_loc", "00_operations", "MD_dm_modifiers"]

# Vanilla or known loc keys that are valid but not defined in mod localisation files
VANILLA_LOC_KEYS = {
    "SP_UNLOCK_PROJECT",
    "SP_UNLOCK_TECH",
    "available_scientist_one_line_tt",
    # Vanilla US Congress keys borrowed from MTG
    "mtg_usa_congress_add_state_tt",
    "mtg_usa_congress_large_opposition_tt",
    "mtg_usa_congress_large_support_tt",
    "mtg_usa_congress_medium_opposition_tt",
    "mtg_usa_congress_medium_support_tt",
    "mtg_usa_congress_remove_state_tt",
    "mtg_usa_congress_small_opposition_tt",
    "mtg_usa_congress_small_support_tt",
    "mtg_usa_house_large_opposition_tt",
    "mtg_usa_house_large_support_tt",
    "mtg_usa_house_medium_opposition_tt",
    "mtg_usa_house_medium_support_tt",
    "mtg_usa_house_small_opposition_tt",
    "mtg_usa_house_small_support_tt",
    "mtg_usa_senate_large_opposition_tt",
    "mtg_usa_senate_large_support_tt",
    "mtg_usa_senate_medium_opposition_tt",
    "mtg_usa_senate_medium_support_tt",
    "mtg_usa_senate_small_opposition_tt",
    "mtg_usa_senate_small_support_tt",
    "free_agency_upgrade_tt",
    # Vanilla operative mission tooltip keys
    "OPERATIVE_MISSION_BOOST_IDEOLOGY_TT",
    "OPERATIVE_MISSION_BUILD_INTEL_NETWORK_TT",
    "OPERATIVE_MISSION_CONTROL_TRADE_TT",
    "OPERATIVE_MISSION_COUNTER_INTELLIGENCE_TT",
    "OPERATIVE_MISSION_DIPLOMATIC_PRESSURE_TT",
    "OPERATIVE_MISSION_NO_MISSION_TT",
    "OPERATIVE_MISSION_PROPAGANDA_TT",
    "OPERATIVE_MISSION_QUIET_INTEL_NETWORK_TT",
    "OPERATIVE_MISSION_ROOT_OUT_RESISTANCE_TT",
    # Vanilla diplomatic action rule tooltip keys (defined in vanilla loc)
    "RULE_ALLOW_GUARANTEES_BLOCKED_TOOLTIP",
    "RULE_ALLOW_GUARANTEES_SAME_IDEOLOGY_TOOLTIP",
    "RULE_ALLOW_LEAVE_FACTION_BLOCKED_TOOLTIP",
    "RULE_ALLOW_LEND_LEASE_BLOCKED_TT",
    "RULE_ALLOW_LEND_LEASE_SAME_FACTION_TT",
    "RULE_ALLOW_LEND_LEASE_SAME_IDEOLOGY_TT",
    "RULE_ALLOW_LICENSING_BLOCKED_TT",
    "RULE_ALLOW_LICENSING_SAME_FACTION_TT",
    "RULE_ALLOW_LICENSING_SAME_IDEOLOGY_TT",
    "RULE_ALLOW_MILITARY_ACCESS_BLOCKED_TT",
    "RULE_ALLOW_MILITARY_ACCESS_SAME_IDEOLOGY_TT",
    "RULE_ALLOW_RELEASE_NATIONS_BLOCKED_TOOLTIP",
    "RULE_ALLOW_REVOKE_GUARANTEES_BLOCKED_TOOLTIP",
    "RULE_ASSUME_LEADERSHIP_BLOCKED_TOOLTIP",
    "RULE_BOOST_PARTY_AI_ONLY_TT",
    "RULE_BOOST_PARTY_BLOCKED_TT",
    "RULE_BOOST_PARTY_PLAYER_ONLY_TT",
    "RULE_COUP_AI_ONLY_TT",
    "RULE_COUP_BLOCKED_TT",
    "RULE_KICK_FROM_FACTION_BLOCKED_TOOLTIP",
    "RULE_VOLUNTEERS_BLOCKED_TT",
    "RULE_VOLUNTEERS_SAME_IDEOLOGY_TT",
    "RULE_WARGOALS_BLOCKED_TT",
}


def _should_skip(filename: str) -> bool:
    return should_skip_file(filename, extra_skip_patterns=EXTRA_SKIP_PATTERNS)


# --- Multiprocessing helpers ---


def process_yml_for_brackets(args: Tuple[str]) -> List[str]:
    filename = args[0]
    results = []
    text_file = FileOpener.open_text_file(filename, strip_comments_flag=True)
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
    text_file = FileOpener.open_text_file(
        filename, lowercase=False, strip_comments_flag=True
    )
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
    text_file = FileOpener.open_text_file(filename, strip_comments_flag=True)
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
        text_file = FileOpener.open_text_file(
            filename, lowercase=lowercase, strip_comments_flag=True
        )
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
    text_file = FileOpener.open_text_file(
        str(filepath), lowercase=False, strip_comments_flag=True
    )
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


def process_txt_for_loc_key_refs(
    args: Tuple,
) -> List[str]:
    """Pool worker: check localization_key = VALUE references in one .txt file."""
    filename, valid_keys, scripted_keys = args
    if _should_skip(filename):
        return []
    text_file = FileOpener.open_text_file(
        filename, lowercase=False, strip_comments_flag=True
    )
    if "localization_key =" not in text_file:
        return []
    pattern = r"localization_key = ([^ \t\n]*)"
    results = []
    for k in re.findall(pattern, text_file, flags=re.MULTILINE | re.DOTALL):
        if k in valid_keys or k in scripted_keys or k in VANILLA_LOC_KEYS:
            continue
        if "[" in k and "]" in k:
            continue
        if "|" in k or '"' in k:
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
    return results


def process_txt_for_custom_tt_refs(
    args: Tuple,
) -> List[str]:
    """Pool worker: check custom_effect_tooltip / custom_trigger_tooltip keys in one .txt file."""
    filename, valid_keys, scripted_keys = args
    if _should_skip(filename):
        return []
    text_file = FileOpener.open_text_file(
        filename, lowercase=False, strip_comments_flag=True
    )
    if (
        "custom_effect_tooltip" not in text_file
        and "custom_trigger_tooltip" not in text_file
    ):
        return []
    simple_pattern = r"custom_effect_tooltip\s*=\s*(?!\{)(\S+)"
    trigger_pattern = r"custom_trigger_tooltip\s*=\s*\{[^}]*?tooltip\s*=\s*(\S+)"
    basename = os.path.basename(filename)
    results = []
    for pattern in [simple_pattern, trigger_pattern]:
        for key in re.findall(pattern, text_file):
            if key in valid_keys or key in VANILLA_LOC_KEYS or key in scripted_keys:
                continue
            if "[" in key or "|" in key or '"' in key:
                continue
            if key.startswith("GFX_"):
                continue
            if key.startswith("cannot_go_higher_than_") or key.startswith(
                "cannot_go_lower_than_"
            ):
                continue
            results.append(f"{key} - {basename}")
    return results


def _extract_not_blocks(text: str) -> List[str]:
    """Return the bodies of every ``NOT = { ... }`` block in ``text``,
    brace-balanced so nested trigger blocks are kept intact."""
    out: List[str] = []
    not_re = re.compile(r"\bNOT\s*=\s*\{")
    i = 0
    while True:
        m = not_re.search(text, i)
        if not m:
            break
        start = m.end()
        depth = 1
        j = start
        while j < len(text) and depth > 0:
            ch = text[j]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
            j += 1
        if depth == 0:
            out.append(text[start : j - 1])
            i = j
        else:
            break
    return out


def process_file_for_orphan_tt_refs(
    args: Tuple,
) -> Tuple[set, List[str], set]:
    """Pool worker: collect tooltip references and dynamic patterns from one file.

    Returns ``(referenced, dynamic_raw, negated_refs)`` where ``negated_refs``
    is the subset of tooltip references that appear inside a ``NOT = { ... }``
    block. Callers use ``negated_refs`` to decide whether ``_NOT``-suffixed
    tooltip keys can be treated as implicitly referenced via HOI4's automatic
    negation lookup.
    """
    filename, patterns = args
    if _should_skip(filename):
        return set(), [], set()
    text_file = FileOpener.open_text_file(
        filename, lowercase=False, strip_comments_flag=True
    )
    referenced = set()
    dynamic_raw = []
    for pat in patterns:
        for m in re.findall(pat, text_file, re.DOTALL):
            token = m.strip('"')
            referenced.add(token)
            if "[" in token and "]" in token:
                dynamic_raw.append(token)

    negated_refs: set = set()
    if "NOT" in text_file:
        for block_body in _extract_not_blocks(text_file):
            for pat in patterns:
                for m in re.findall(pat, block_body, re.DOTALL):
                    negated_refs.add(m.strip('"'))

    return referenced, dynamic_raw, negated_refs


def _get_skipped_loc_keys(mod_path: str) -> set:
    """Get all loc keys defined in yml files matching EXTRA_SKIP_PATTERNS."""
    filepath = str(Path(mod_path) / "localisation" / "english") + "/"
    keys = set()
    for filename in glob.iglob(filepath + "**/*.yml", recursive=True):
        if not _should_skip(filename):
            continue
        text_file = FileOpener.open_text_file(
            filename, lowercase=False, strip_comments_flag=True
        )
        if "l_english" not in text_file:
            continue
        for line in text_file.split("\n"):
            line = line.strip()
            if ":" not in line or "l_english:" in line or (line and line[0] == "#"):
                continue
            try:
                key = line[: line.index(":")].strip()
                keys.add(key)
            except (ValueError, IndexError):
                continue
    return keys


def _get_scripted_loc_keys(mod_path: str) -> set:
    """Get all keys defined via 'defined_text { name = KEY }' in scripted localisation."""
    loc_dir = str(Path(mod_path) / "common" / "scripted_localisation") + "/"
    keys = set()
    pattern = r"^\tname\s*=\s*(\S+)"
    for filename in glob.iglob(loc_dir + "**/*.txt", recursive=True):
        text_file = FileOpener.open_text_file(
            filename, lowercase=False, strip_comments_flag=True
        )
        for m in re.findall(pattern, text_file, re.MULTILINE):
            keys.add(m.strip('"'))
    return keys


class Validator(BaseValidator):
    TITLE = "LOCALISATION VALIDATION"
    STAGED_EXTENSIONS = [".txt", ".yml"]

    def _get_yml_files(self) -> List[str]:
        return self._collect_files(
            ["localisation/english/**/*.yml"], extra_skip=_should_skip
        )

    def validate_duplicated_keys(self, duplicated: List[str], skipped_keys: set):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking for duplicated localisation keys...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        filtered = [k for k in duplicated if k not in skipped_keys]
        self._report(
            filtered,
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

        all_results = self._pool_map(process_yml_for_brackets, args_list, chunksize=10)

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

        all_results = self._pool_map(process_yml_for_syntax, args_list, chunksize=10)

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

        all_results = self._pool_map(process_yml_for_mandatory, args_list, chunksize=10)

        results = []
        for file_results in all_results:
            results.extend(file_results)

        self._report(
            results,
            "✓ All loc files have mandatory l_english: line",
            "Missing l_english: line in localisation files:",
        )

    def validate_localization_key_references(
        self, loc_keys: Dict, scripted_loc_keys: set
    ):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking localization_key references...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        txt_files = self._collect_files(["**/*.txt"])
        args_list = [(f, loc_keys, scripted_loc_keys) for f in txt_files]
        all_results = self._pool_map(
            process_txt_for_loc_key_refs, args_list, chunksize=30
        )

        results = sorted({k for file_res in all_results for k in file_res})
        self._report(
            results,
            "✓ All localization_key references are valid",
            "Invalid localization_key references (key not found in loc files):",
        )

    def validate_custom_tooltip_references(
        self, loc_keys: Dict, scripted_loc_keys: set
    ):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking custom tooltip references...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        txt_files = self._collect_files(["**/*.txt"])
        args_list = [(f, loc_keys, scripted_loc_keys) for f in txt_files]
        all_results = self._pool_map(
            process_txt_for_custom_tt_refs, args_list, chunksize=30
        )

        results = sorted({r for file_res in all_results for r in file_res})
        self._report(
            results,
            "✓ All custom tooltip references are valid",
            "Custom tooltip references not found in localisation:",
        )

    def validate_add_resistance_tooltip(self, loc_keys: Dict):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking add_resistance_target tooltip localisation...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        pattern = r"^(\t+)add_resistance_target = (\{\n.*?)^\1\}"
        results = []

        for filename in glob.iglob(
            os.path.join(self.mod_path, "**", "*.txt"), recursive=True
        ):
            if _should_skip(filename):
                continue
            text_file = FileOpener.open_text_file(
                filename, lowercase=False, strip_comments_flag=True
            )
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

    def validate_orphaned_tooltip_keys(
        self, loc_keys: Dict, skipped_keys: set, scripted_loc_keys: set
    ):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking for orphaned tooltip keys...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        # Tooltip-named keys: anything ending in _tt/_TT or starting with `tooltip_`.
        # The latter catches modder-named explicit tooltip strings like
        # `tooltip_influence_on_all_other_EU_members_25_percent` that aren't suffixed.
        tt_keys = {
            k
            for k in loc_keys
            if (k.endswith("_tt") or k.endswith("_TT") or k.startswith("tooltip_"))
            and k not in skipped_keys
            and not k.startswith("cannot_go_higher_than_")
            and not k.startswith("cannot_go_lower_than_")
            and not k.startswith("OPERATIVE_MISSION_")
        }

        if not tt_keys:
            self._report(
                [],
                "✓ No orphaned tooltip keys found",
                "Orphaned tooltip keys (defined in loc but never referenced):",
            )
            return

        # 1. Collect all tooltip keys referenced in script, GUI, and scripted loc files.
        #    Use pool_map for parallel file scanning instead of a serial loop.
        referenced_in_scripts: set = set(scripted_loc_keys)
        txt_patterns = [
            r"custom_effect_tooltip\s*=\s*(?!\{)(\S+)",
            r"custom_trigger_tooltip\s*=\s*\{[^}]*?tooltip\s*=\s*(\S+)",
            r"tooltip\s*=\s*(\S+)",
            r"localization_key\s*=\s*(\S+)",
        ]
        gui_patterns = [
            r'(?:pdx_tooltip|pdx_tooltip_delayed|tooltip|text|buttonText)\s*=\s*"([^"]+)"',
            r"(?:tooltip|text|buttonText)\s*=\s*(\S+)",
        ]

        txt_files = self._collect_files(["**/*.txt"])
        gui_files = self._collect_files(["**/*.gui"])
        args_list = [(f, txt_patterns) for f in txt_files] + [
            (f, gui_patterns) for f in gui_files
        ]
        all_scan_results = self._pool_map(
            process_file_for_orphan_tt_refs, args_list, chunksize=30
        )

        # Dynamic-key patterns (compiled regexes) collected from meta_effect
        # substitutions like `tooltip_EU_parliament_focus_[EUXXX]_approve`.
        # A literal tooltip_*_approve key matching this pattern is considered
        # referenced even though the call site uses runtime substitution.
        raw_dynamic_tokens: List[str] = []
        negated_script_refs: set = set()
        for referenced, dynamic_raw, negated in all_scan_results:
            referenced_in_scripts.update(referenced)
            raw_dynamic_tokens.extend(dynamic_raw)
            negated_script_refs.update(negated)

        # Compile dynamic patterns once, deduplicating raw tokens first.
        dynamic_ref_patterns = []
        seen_raw = set()
        for token in raw_dynamic_tokens:
            if token in seen_raw:
                continue
            seen_raw.add(token)
            esc = re.escape(token)
            esc = re.sub(
                r"\\\[[A-Za-z_][A-Za-z0-9_]*\\\]",
                r"[A-Za-z0-9_]+",
                esc,
            )
            try:
                dynamic_ref_patterns.append(re.compile(f"^{esc}$"))
            except re.error:
                pass

        def _matches_dynamic_ref(key: str) -> bool:
            return any(p.match(key) for p in dynamic_ref_patterns)

        # HOI4 auto-looks-up `_NOT` variants only for tooltip keys whose base
        # is referenced *inside* a ``NOT = { ... }`` block. A `foo_tt` only
        # used in positive context never causes the engine to look up
        # `foo_tt_NOT`, so we must not suppress the orphan warning for those.
        def _has_not_base_referenced(key: str) -> bool:
            if not key.endswith("_NOT"):
                return False
            base = key[: -len("_NOT")]
            if base in negated_script_refs:
                return True
            return False

        # 2. Collect _tt keys referenced by other loc values via $KEY$
        referenced_in_loc = set()
        for key, value in loc_keys.items():
            for ref in re.findall(r"\$([A-Za-z0-9_]+(?:_tt|_TT))\$", value):
                if ref in tt_keys:
                    referenced_in_loc.add(ref)

        # 3. Report orphans
        all_referenced = referenced_in_scripts | referenced_in_loc
        orphaned = sorted(
            k
            for k in (tt_keys - all_referenced)
            if not _matches_dynamic_ref(k) and not _has_not_base_referenced(k)
        )

        self._report(
            orphaned,
            "✓ No orphaned tooltip keys found",
            "Orphaned tooltip keys (defined in loc but never referenced):",
        )

    def run_validations(self):
        if self.staged_only and not self.staged_files:
            self.log(
                "No staged files found — skipping localisation validation",
                "warning",
            )
            return

        # Pre-compute shared data once — avoids re-reading all loc files for each check.
        loc_keys, duplicated = get_all_loc_keys(self.mod_path, lowercase=False)
        skipped_keys = _get_skipped_loc_keys(self.mod_path)
        scripted_loc_keys = _get_scripted_loc_keys(self.mod_path)

        self.validate_duplicated_keys(duplicated, skipped_keys)
        self.validate_brackets()
        self.validate_syntax()
        self.validate_mandatory_line()

        # Cross-reference checks scan all .txt/.gui files — skip in staged mode
        if not self.staged_only:
            self.validate_localization_key_references(loc_keys, scripted_loc_keys)
            self.validate_custom_tooltip_references(loc_keys, scripted_loc_keys)
            self.validate_add_resistance_tooltip(loc_keys)
            self.validate_orphaned_tooltip_keys(
                loc_keys, skipped_keys, scripted_loc_keys
            )


if __name__ == "__main__":
    run_validator_main(Validator, "Validate localisation in Millennium Dawn mod")
