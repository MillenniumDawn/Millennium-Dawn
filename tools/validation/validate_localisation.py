#!/usr/bin/env python3
"""Validate localisation files for common issues in Millennium Dawn.

Based on Kaiserreich Autotests by Pelmen (https://github.com/Pelmen323),
adapted for Millennium Dawn with multiprocessing.
"""

import functools
import glob
import logging
import os
import re
import sys
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Set, Tuple, Union

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import disk_cache
from shared_utils import (
    extract_block_from_text,
    iter_statements,
    read_text_strict,
    strip_comments,
)
from validator_common import (
    DEFAULT_EXTRA_SKIP_PATTERNS,
    KNOWN_VANILLA_LOC_KEYS,
    BaseValidator,
    FileOpener,
    Issue,
    Severity,
    run_validator_main,
    should_skip_file,
)

EXTRA_SKIP_PATTERNS = DEFAULT_EXTRA_SKIP_PATTERNS + ["00_operations", "MD_dm_modifiers"]

# Vanilla / reused-vanilla loc keys that are valid but not defined in the mod's
# localisation files. Single source of truth lives in validator_common so the
# focus/idea loc loaders and this reference checker share one allowlist.
VANILLA_LOC_KEYS = KNOWN_VANILLA_LOC_KEYS


def _should_skip(filename: str) -> bool:
    return should_skip_file(filename, extra_skip_patterns=EXTRA_SKIP_PATTERNS)


# --- Multiprocessing helpers ---


def _scan_brackets_text(text: str, basename: str) -> List[str]:
    results = []
    for line_idx, line in enumerate(text.split("\n")[1:]):
        if line.count("[") != line.count("]"):
            results.append(f"{basename} - line {line_idx + 2} - unpaired bracket")
    return results


def process_yml_for_brackets(args: Tuple[str]) -> List[str]:
    filename = args[0]
    text = FileOpener.open_text_file(filename, strip_comments_flag=True)
    return _scan_brackets_text(text, os.path.basename(filename))


_SUBST_KEY_RE = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)\$")
_LINE_KEY_RE = re.compile(r"^[ \t]*([\w.\-]+)\s*:")
_NOT_OPEN_RE = re.compile(r"\bNOT\s*=\s*\{")
# A § followed by whitespace and a digit is a prose section sign (e.g. a legal
# citation like "15 U.S.C. § 1"), never a color code; game markup never puts a
# space after §. Requiring the digit keeps a dangling/broken code (§ before a
# word, quote, or line end) flagged instead of silently exempted.
_PROSE_SECTION_SIGN_RE = re.compile(r"§(?=\s+\d)")

# A formatter (Prettier/pre-commit --all-files) once split Paradox loc
# `KEY:0 "value"` lines across two lines and rewrote double quotes to single
# quotes. Paradox YAML is not real YAML — both mangle silently in-game rather
# than erroring, so they must be caught here.
# Opinion modifiers sit exactly one level under the file's `opinion_modifiers
# = { }` wrapper. Spaces are accepted alongside the tab MD actually uses, but
# only one level deep — `\s+` would swallow blank lines and match nested blocks.
_OPINION_MODIFIER_RE = re.compile(
    r"^(?:\t| {1,4})([A-Za-z0-9_]+)\s*=\s*\{", re.MULTILINE
)
_MANGLED_KEY_NO_VALUE_RE = re.compile(r"^\s*\w[\w.\-]*:\d*\s*$")
_MANGLED_SINGLE_QUOTE_VALUE_RE = re.compile(r"^\s*\w[\w.\-]*:\d*\s*'.*'\s*$")


def _mangled_loc_issue(basename: str, line: int, message: str) -> Issue:
    return Issue(
        severity=Severity.ERROR,
        category="mangled-loc-line",
        message=message,
        file=basename,
        line=line,
    )


def _scan_syntax_text(
    text: str, basename: str, valid_colors: List[str]
) -> List[Tuple[Union[Issue, str], Optional[str]]]:
    """Return (finding, line-key) pairs in line order for one yml file.

    Mangled-line findings carry a None key so they are never filtered; color
    findings carry their line's loc key so the caller can drop keys resolved
    through $KEY$ substitution once the repo-wide set is known.
    """
    out: List[Tuple[Union[Issue, str], Optional[str]]] = []
    for line_idx, line in enumerate(text.split("\n")[1:]):
        if "#" in line or line.strip() in ["", "l_english:"]:
            continue
        if _MANGLED_SINGLE_QUOTE_VALUE_RE.match(line):
            out.append(
                (
                    _mangled_loc_issue(
                        basename,
                        line_idx + 2,
                        "Loc value uses single quotes instead of double quotes (formatter-mangled, breaks in-game)",
                    ),
                    None,
                )
            )
        elif _MANGLED_KEY_NO_VALUE_RE.match(line):
            out.append(
                (
                    _mangled_loc_issue(
                        basename,
                        line_idx + 2,
                        "Loc key has no value on the same line (formatter-mangled, breaks in-game)",
                    ),
                    None,
                )
            )
        if "\u00a7" in line:
            key_match = _LINE_KEY_RE.match(line)
            key = key_match.group(1) if key_match else None
            color_line = _PROSE_SECTION_SIGN_RE.sub("", line)
            if "\u00a7" not in color_line:
                continue
            count = color_line.count("\u00a7")
            if count % 2 != 0:
                out.append(
                    (
                        f"{basename}, line {line_idx + 2}, colors - odd number of \u00a7 symbols ({count})",
                        key,
                    )
                )
            elif count != color_line.count("\u00a7!") * 2:
                expected = count // 2
                actual = color_line.count("\u00a7!")
                out.append(
                    (
                        f"{basename}, line {line_idx + 2}, colors - expected {expected} \u00a7! but got {actual}",
                        key,
                    )
                )
            else:
                for idx, ch in enumerate(color_line):
                    if ch == "\u00a7" and idx + 1 < len(color_line):
                        next_ch = color_line[idx + 1]
                        if next_ch not in valid_colors and next_ch not in [
                            "!",
                            "[",
                            "$",
                        ]:
                            out.append(
                                (
                                    f"{basename}, line {line_idx + 2}, colors - unsupported color '{next_ch}'",
                                    key,
                                )
                            )
    return out


def process_yml_for_syntax(args: Tuple[str, List[str], frozenset]) -> List[Issue | str]:
    filename, valid_colors, subst_keys = args
    text_file = FileOpener.open_text_file(
        filename, lowercase=False, strip_comments_flag=True
    )
    pairs = _scan_syntax_text(text_file, os.path.basename(filename), valid_colors)
    return [finding for finding, key in pairs if key not in subst_keys]


def _scan_mandatory_text(text: str, basename: str) -> List[str]:
    results: List[str] = []
    lines = text.split("\n")
    if lines == [""]:
        return results
    if not any("l_english:" in line for line in lines):
        results.append(f"{basename} - l_english: line is absent")
    return results


def process_yml_for_mandatory(args: Tuple[str]) -> List[str]:
    filename = args[0]
    text_file = FileOpener.open_text_file(filename, strip_comments_flag=True)
    return _scan_mandatory_text(text_file, os.path.basename(filename))


# .claude/docs/typo-watchlist.md's catalogued misspellings, lowered. `it's`
# (possessive-rule, context-dependent) and `civilisation` (legitimate British
# spelling) are excluded; `civillisation` (double-L) has no legitimate reading
# and stays in.
_TYPO_WATCHLIST: Dict[str, str] = {
    "estabilish": "establish",
    "innvoations": "innovations",
    "irreperable": "irreparable",
    "irrepairable": "irreparable",
    "unrepairable": "irreparable",
    "unenmployed": "unemployed",
    "existance": "existence",
    "effectivness": "effectiveness",
    "disproportinate": "disproportionate",
    "tarditions": "traditions",
    "contrats": "by contrast",
    "airforce": "Air Force",
    "miltiary": "military",
    "coaltion": "coalition",
    "tumultous": "tumultuous",
    "recgonized": "recognized",
    "propgramme": "Programme",
    "poeple": "people",
    "unloyal": "disloyal",
    "isreal": "Israel",
    "bocme": "become",
    "hovewer": "however",
    "acomplish": "accomplish",
    "endevours": "Endeavours",
    "quiantified": "Quantified",
    "convering": "converting",
    "encomapassing": "encompassing",
    "fundamnetals": "fundamentals",
    "civillian": "civilian",
    "civillisation": "civilization",
    "suprised": "surprised",
    "alledged": "alleged",
    "succesful": "successful",
    "succesfull": "successful",
    "huminliating": "humiliating",
    "reffered": "referred",
    "stronly": "strongly",
    "togeather": "together",
    "disasterous": "disastrous",
    "religous": "religious",
    "suzerainity": "suzerainty",
    "seperation": "separation",
    "seperate": "separate",
    "seperated": "separated",
}

# Exact-phrase substrings exempt from typo flagging (populate as intentional uses surface).
_TYPO_EXEMPTIONS: Set[str] = set()

_TYPO_RE = re.compile(
    r"\b(?:" + "|".join(re.escape(t) for t in _TYPO_WATCHLIST) + r")\b",
    re.IGNORECASE,
)
_TYPO_VALUE_RE = re.compile(r'^\s*[\w.\-]+:\d*\s*"(.*)"')
_TYPO_RUNTIME_REFERENCE_RE = re.compile(r"\[[^\]]*\]|\$[\w.@|+\-]+\$|£[\w.@\-]+")


def _iter_loc_values(text: str) -> Iterator[Tuple[int, str]]:
    """Yield (line_idx, value) for each non-blank body line with a quoted value."""
    for line_idx, line in enumerate(text.split("\n")[1:]):
        if not line.strip():
            continue
        value_match = _TYPO_VALUE_RE.match(line)
        if not value_match:
            continue
        yield line_idx, value_match.group(1)


def _scan_typos_text(text: str, basename: str) -> List[str]:
    results = []
    for line_idx, value in _iter_loc_values(text):
        if any(exempt in value for exempt in _TYPO_EXEMPTIONS):
            continue
        prose = _TYPO_RUNTIME_REFERENCE_RE.sub("", value)
        for m in _TYPO_RE.finditer(prose):
            correction = _TYPO_WATCHLIST[m.group(0).lower()]
            results.append(
                f"{basename} - line {line_idx + 2} - '{m.group(0)}' -> '{correction}'"
            )
    return results


def process_yml_for_typos(args: Tuple[str]) -> List[str]:
    filename = args[0]
    text = FileOpener.open_text_file(filename, strip_comments_flag=True)
    return _scan_typos_text(text, os.path.basename(filename))


def _scan_prose_text(text: str, basename: str) -> List[Issue]:
    results: List[Issue] = []
    for line_idx, value in _iter_loc_values(text):
        for _ in range(value.count("\u2014")):
            results.append(
                Issue(
                    severity=Severity.WARNING,
                    category="loc-em-dash",
                    message="Em dash in loc value: replace with a period, comma, or colon (see .claude/docs/localisation-rules.md)",
                    file=basename,
                    line=line_idx + 2,
                )
            )
        for _ in range(value.count("`")):
            results.append(
                Issue(
                    severity=Severity.WARNING,
                    category="loc-backtick-apostrophe",
                    message="Backtick used as apostrophe in loc value: use ' instead",
                    file=basename,
                    line=line_idx + 2,
                )
            )
    return results


def process_yml_for_prose(args: Tuple[str]) -> List[Issue]:
    filename = args[0]
    text = FileOpener.open_text_file(filename, strip_comments_flag=True)
    return _scan_prose_text(text, os.path.basename(filename))


def _scan_subst_keys_text(text: str) -> Set[str]:
    return set(_SUBST_KEY_RE.findall(text))


def _scan_var_refs_text(raw: str, basename: str) -> List[Tuple[str, str, int]]:
    out: List[Tuple[str, str, int]] = []
    for number, line in enumerate(raw.split("\n"), 1):
        for token in _LOC_VAR_REF_RE.findall(line):
            name = _loc_var_name(token)
            if name:
                out.append((name, basename, number))
    return out


def _parse_loc_keys_from_text(text: str) -> List[Tuple[str, str]]:
    """Return (key, value) pairs in file order. Pairs (not a dict) so the caller
    can still detect within-file and cross-file duplicates exactly as before."""
    pairs: List[Tuple[str, str]] = []
    for line in text.split("\n"):
        line = line.strip()
        if ":" not in line or "l_english:" in line or (line and line[0] == "#"):
            continue
        colon_idx = line.find(":")
        if colon_idx < 0:
            continue
        key = line[:colon_idx].strip()
        value = line[colon_idx + 2 :].strip()
        pairs.append((key, value))
    return pairs


def get_all_loc_keys(
    mod_path: str, lowercase: bool = False
) -> Tuple[Dict[str, str], List[str]]:
    filepath = str(Path(mod_path) / "localisation" / "english") + "/"
    loc_dict: Dict[str, str] = {}
    duplicated_keys: List[str] = []
    namespace = f"loc.keys.lc={'1' if lowercase else '0'}"

    for filename in glob.iglob(filepath + "**/*.yml", recursive=True):
        text_file = FileOpener.open_text_file(
            filename, lowercase=lowercase, strip_comments_flag=True
        )
        if "l_english" not in text_file:
            continue
        pairs = disk_cache.per_file_cached_by_content(
            mod_path,
            namespace,
            filename,
            text_file,
            lambda: _parse_loc_keys_from_text(text_file),
        )
        for key, value in pairs:
            if key in loc_dict:
                duplicated_keys.append(key)
            else:
                loc_dict[key] = value

    return loc_dict, duplicated_keys


def get_all_colors(mod_path: str) -> List[str]:
    filepath = Path(mod_path) / "interface" / "core.gfx"
    if not filepath.exists():
        logging.warning(
            "interface/core.gfx not found — color validation will use fallback set"
        )
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
        logging.warning(
            "Failed to parse interface/core.gfx — color validation will use fallback set"
        )
        return list("WGRBYCMwgrbycm!")


# The valid/scripted loc key sets are ~200k entries; shipping them with every
# pool task pickled ~23 MB per chunk and dominated this validator's runtime.
# _txt_refs_init plants them as worker globals once per worker instead.
_W_VALID_KEYS: frozenset = frozenset()
_W_SCRIPTED_KEYS: frozenset = frozenset()


def _txt_refs_init(valid_keys: frozenset, scripted_keys: frozenset) -> None:
    global _W_VALID_KEYS, _W_SCRIPTED_KEYS
    _W_VALID_KEYS = valid_keys
    _W_SCRIPTED_KEYS = scripted_keys


def process_txt_for_loc_key_refs(filename: str) -> List[str]:
    """Pool worker: check localization_key = VALUE references in one .txt file.

    Reads the valid/scripted key sets from worker globals (set by
    _txt_refs_init), so the large set is shipped once per worker, not per task.
    """
    if _should_skip(filename):
        return []
    valid_keys, scripted_keys = _W_VALID_KEYS, _W_SCRIPTED_KEYS
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


def _trigger_tooltip_keys(text: str) -> List[str]:
    """Keys from every custom_trigger_tooltip, past any nested trigger body."""
    keys: List[str] = []
    for match in re.finditer(r"custom_trigger_tooltip\s*=\s*\{", text):
        depth = 0
        start = text.index("{", match.end() - 1)
        for token in re.finditer(r"[{}]|\btooltip\s*=\s*(?!\{)(\S+)", text[start:]):
            symbol = token.group(0)
            if symbol == "{":
                depth += 1
            elif symbol == "}":
                depth -= 1
                if depth == 0:
                    break
            elif depth == 1:
                keys.append(token.group(1))
                break
    return keys


# --- [?variable] references -------------------------------------------------

# An unwritten [?name] renders as 0 rather than erroring, so it is invisible.

_LOC_VAR_REF_RE = re.compile(r"\[\?([^\]]+)\]")
_LOC_VAR_WRITE_RE = re.compile(
    r"(?:set_variable|set_temp_variable|set_global_variable|set_variable_to_random|"
    r"set_temp_variable_to_random|randomize_variable|"
    r"add_to_variable|add_to_temp_variable|subtract_from_variable|"
    r"subtract_from_temp_variable|multiply_variable|multiply_temp_variable|"
    r"divide_variable|divide_temp_variable|clamp_variable|clamp_temp_variable|"
    r"modulo_variable|modulo_temp_variable|round_variable|round_temp_variable|"
    r"min_variable|max_variable)\s*=\s*\{\s*"
    r"(?:var\s*=\s*)?((?:\d+\.)?(?:[A-Za-z_]|[0-9]+_)[\w.:@^]*)"
)
_LOC_VAR_ARRAY_RE = re.compile(
    r"(?:add_to_array|add_to_temp_array|resize_array)\s*=\s*\{\s*"
    r"(?:array\s*=\s*)?([A-Za-z_][\w.:@^]*)"
)

_VAR_SCOPE_WORDS = frozenset(
    {
        "root",
        "this",
        "from",
        "prev",
        "owner",
        "controller",
        "capital",
        "global",
        "var",
        "event_target",
        "token",
    }
)

# Engine-side, but absent from resources/documentation.
_EXTRA_ENGINE_LOC_VARS = frozenset(
    {"days_left", "war_support", "strength_ratio", "random"}
)
# Written by vanilla common/on_actions/05_lar_on_actions.txt, which MD does not replace.
_VANILLA_WRITTEN_VARS = frozenset({"historical_capital_for_country"})

_DYNAMIC_VAR_DOC = os.path.join(
    "resources", "documentation", "dynamic_variables_documentation.md"
)
_DOC_HEADING_RE = re.compile(r"^#{2,4}\s+([A-Za-z_][\w.]*)\s*$", re.M)


@functools.lru_cache(maxsize=1)
def _engine_loc_vars(mod_path: str) -> frozenset:
    """Read-only dynamic variables the engine supplies, from the vanilla docs."""
    try:
        with open(
            os.path.join(mod_path, _DYNAMIC_VAR_DOC), "r", encoding="utf-8"
        ) as handle:
            body = handle.read()
    except OSError:
        return _EXTRA_ENGINE_LOC_VARS
    return frozenset(_DOC_HEADING_RE.findall(body)) | _EXTRA_ENGINE_LOC_VARS


def _loc_var_name(raw: str) -> str:
    """The variable a `[?...]` names, or "" for a promote or scope.

    Leading scope hops (`var:`, `CONTROLLER:`, `ROOT.`, `145.`) are stripped.
    A `name@target` dynamic variable yields `name`.
    """
    name = raw.split("|", 1)[0].strip()
    if not name:
        return ""
    if "@" in name:
        name = name.split("@", 1)[0]
    name = name.split("^", 1)[0]
    while ":" in name:
        head, _, tail = name.partition(":")
        if not re.fullmatch(r"[A-Za-z_]\w*", head):
            break
        name = tail
    parts = [seg for seg in name.split(".") if seg]
    if any(seg[:1].isupper() and seg[1:2].islower() for seg in parts[1:]):
        return ""  # a promote such as .GetName, not a variable read
    while len(parts) > 1 and (
        parts[0].lower() in _VAR_SCOPE_WORDS
        or re.fullmatch(r"[A-Z]{3}", parts[0])
        or parts[0].isdigit()
    ):
        parts.pop(0)
    name = ".".join(parts).strip()
    # A scope hop can sit behind the dotted prefix too: FROM.CONTROLLER:var.
    while ":" in name:
        head, _, tail = name.partition(":")
        if not re.fullmatch(r"[A-Za-z_]\w*", head):
            break
        name = tail
    if not name or name.lower() in _VAR_SCOPE_WORDS or re.fullmatch(r"[A-Z]{3}", name):
        return ""
    if len(name) < 3 or name.endswith("_array") or "." in name:
        return ""
    return name


def process_txt_for_var_writes(args: Tuple[str]) -> Set[str]:
    """Pool worker: variable names one script file writes."""
    filename = args[0]
    text = FileOpener.open_text_file(
        filename, lowercase=False, strip_comments_flag=True
    )
    if not text:
        return set()
    written: Set[str] = set()
    for raw in _LOC_VAR_WRITE_RE.findall(text) + _LOC_VAR_ARRAY_RE.findall(text):
        written.add(raw.split("^")[0].split(".")[-1])
        name = _loc_var_name(raw)
        if name:
            written.add(name)
    if any(
        key in text
        for key in (
            "for_each_loop",
            "for_each_scope_loop",
            "for_loop_effect",
            "while_loop_effect",
            "find_highest_in_array",
            "find_lowest_in_array",
            "any_of",
            "all_of",
        )
    ):
        search_from = 0
        while True:
            match = _COLLECTION_BIND_OPEN_RE.search(text, search_from)
            if not match:
                break
            body, end = extract_block_from_text(text, match.end() - 1)
            if end == -1:
                break
            for key, scalar, _block in iter_statements(body):
                if (
                    key in {"value", "index"}
                    and scalar
                    and _BIND_NAME_RE.fullmatch(scalar)
                ):
                    written.add(scalar)
            search_from = end
    if "dynamic_lists" in text:
        search_from = 0
        while True:
            match = _DYNAMIC_LISTS_OPEN_RE.search(text, search_from)
            if not match:
                break
            body, end = extract_block_from_text(text, match.end() - 1)
            if end == -1:
                break
            for _key, _scalar, entry in iter_statements(body):
                if entry is None:
                    continue
                for key, scalar, _block in iter_statements(entry):
                    if key == "value" and scalar and _BIND_NAME_RE.fullmatch(scalar):
                        written.add(scalar)
            search_from = end
    if "var =" in text or "var=" in text:
        search_from = 0
        while True:
            match = _WRITE_OPEN_RE.search(text, search_from)
            if not match:
                break
            body, end = extract_block_from_text(text, match.end() - 1)
            if end == -1:
                break
            for raw in _VAR_BIND_RE.findall(body):
                written.add(raw.split("^")[0].split(".")[-1])
                name = _loc_var_name(raw)
                if name:
                    written.add(name)
            search_from = end
    return written


# name@target. Trailing `_@SCOPE` is a flag token, not a dynamic variable.
_TARGETED_VAR_RE = re.compile(r"(?<![A-Za-z0-9_])([A-Za-z][A-Za-z0-9_]*[A-Za-z0-9])@")
_FLAG_LINE_RE = re.compile(
    r"(?:"
    r"\b(?:has|set|clr|modify)_"
    r"(?:country|global|state|character|mio|project|unit_leader)_flag\s*="
    r"|\bflag\s*="
    r")"
)


def _scan_targeted_var_text(text: str, basename: str) -> List[Tuple[str, str, int]]:
    """(prefix, file, line) for every name@target that is not a flag token."""
    if "@" not in text:
        return []
    out: List[Tuple[str, str, int]] = []
    for number, line in enumerate(text.split("\n"), 1):
        if "@" not in line or _FLAG_LINE_RE.search(line):
            continue
        for prefix in _TARGETED_VAR_RE.findall(line):
            out.append((prefix, basename, number))
    return out


def process_txt_for_targeted_vars(args: Tuple[str]) -> List[Tuple[str, str, int]]:
    """Pool worker: name@target prefixes one script file uses."""
    filename = args[0]
    text = FileOpener.open_text_file(
        filename, lowercase=False, strip_comments_flag=True
    )
    if not text:
        return []
    return _scan_targeted_var_text(text, os.path.basename(filename))


_WRITE_OPEN_RE = re.compile(
    r"\b(?:set_variable|set_temp_variable|set_global_variable|"
    r"set_variable_to_random|set_temp_variable_to_random|randomize_variable|"
    r"add_to_variable|add_to_temp_variable|subtract_from_variable|"
    r"subtract_from_temp_variable|multiply_variable|multiply_temp_variable|"
    r"divide_variable|divide_temp_variable|clamp_variable|clamp_temp_variable|"
    r"modulo_variable|modulo_temp_variable|round_variable|round_temp_variable|"
    r"min_variable|max_variable)\s*=\s*\{"
)
_VAR_BIND_RE = re.compile(r"\bvar\s*=\s*((?:[A-Za-z_]|[0-9]+_)[\w.:@^]*)")
_DYNAMIC_LISTS_OPEN_RE = re.compile(r"\bdynamic_lists\s*=\s*\{")
_BIND_NAME_RE = re.compile(r"[A-Za-z_]\w*")
_COLLECTION_BIND_OPEN_RE = re.compile(
    r"\b(?:for_each_loop|for_each_scope_loop|for_loop_effect|while_loop_effect|"
    r"find_highest_in_array|find_lowest_in_array|any_of|all_of)\s*=\s*\{"
)
_CHECK_VARIABLE_OPEN_RE = re.compile(r"\bcheck_variable\s*=\s*\{")
_HAS_VARIABLE_RE = re.compile(r"\bhas_variable\s*=\s*([^\s{}]+)")
_CHECK_VAR_TOKEN_RE = re.compile(r"(?:[A-Za-z_]|[0-9]+_)[\w.:@^]*")
_CHECK_VAR_TOOLTIP_RE = re.compile(r"\btooltip\s*=\s*\S+")
_CHECK_VAR_CONSTANT_RE = re.compile(r"(?<![A-Za-z0-9_])@[A-Za-z_][\w]*")
# The engine supplies these temporary values only while scoring occupation laws.
_OCCUPATION_LAW_CONTEXT_VARS = frozenset(
    {
        "uncapped_resistance_target",
        "resistance_target_without_law",
        "garrison_min_support_ratio",
    }
)
_CHECK_VAR_KEYWORDS = frozenset(
    {
        "var",
        "variable",
        "value",
        "compare",
        "tooltip",
        "greater",
        "greater_than",
        "less",
        "less_than",
        "equals",
        "not_equals",
        "greater_than_or_equals",
        "less_than_or_equals",
        "AND",
        "OR",
        "NOT",
        "limit",
        "if",
        "else",
    }
)


def _scan_script_var_reads_text(text: str, basename: str) -> List[Tuple[str, str, int]]:
    """Unwritten check_variable / has_variable names. @ targets are a separate check."""
    if "check_variable" not in text and "has_variable" not in text:
        return []
    out: List[Tuple[str, str, int]] = []
    for number, line in enumerate(text.split("\n"), 1):
        if "has_variable" not in line:
            continue
        for raw in _HAS_VARIABLE_RE.findall(line):
            if "@" in raw or raw.startswith("token:"):
                continue
            name = _loc_var_name(raw)
            if name:
                out.append((name, basename, number))
    search_from = 0
    while True:
        match = _CHECK_VARIABLE_OPEN_RE.search(text, search_from)
        if not match:
            break
        body, end = extract_block_from_text(text, match.end() - 1)
        if end == -1:
            break
        search_from = end
        if "[" in body:
            continue
        lineno = text.count("\n", 0, match.start()) + 1
        body = _CHECK_VAR_TOOLTIP_RE.sub("", body)
        body = _CHECK_VAR_CONSTANT_RE.sub("", body)
        for raw in _CHECK_VAR_TOKEN_RE.findall(body):
            if "@" in raw or raw.startswith("token:") or raw in _CHECK_VAR_KEYWORDS:
                continue
            name = _loc_var_name(raw)
            if name:
                out.append((name, basename, lineno))
        search_from = end
    return out


def process_txt_for_script_var_reads(args: Tuple[str]) -> List[Tuple[str, str, int]]:
    """Pool worker: check_variable / has_variable names one script file reads."""
    filename = args[0]
    text = FileOpener.open_text_file(
        filename, lowercase=False, strip_comments_flag=True
    )
    if not text:
        return []
    return _scan_script_var_reads_text(text, os.path.basename(filename))


def process_yml_for_var_refs(args: Tuple[str]) -> List[Tuple[str, str, int]]:
    """Pool worker: (variable, file, line) for every `[?...]` in one loc file."""
    filename = args[0]
    try:
        with open(filename, "r", encoding="utf-8-sig", newline="") as handle:
            raw = handle.read()
    except (OSError, UnicodeDecodeError):
        return []
    return _scan_var_refs_text(raw, os.path.basename(filename))


def _scan_shared_yml_file(args) -> Tuple:
    """Pool worker: run every yml check on one file after a single read.

    Reads the file once and shares the comment-stripped text across the
    brackets, syntax, mandatory, typo, and prose scans instead of one read
    plus strip pass per check. Each scan calls the same ``_scan_*_text``
    helper its standalone worker uses, so findings are unchanged. Variable
    references scan the raw lines and substitution keys are harvested from
    the same stripped text; the syntax color exemption resolves parent-side
    once the repo-wide substitution set is known.
    Returns (brackets, syntax_pairs, mandatory, typos, prose, var_refs, subst).
    """
    filename, valid_colors = args
    raw = read_text_strict(filename)
    text = strip_comments(raw)
    basename = os.path.basename(filename)
    return (
        _scan_brackets_text(text, basename),
        _scan_syntax_text(text, basename, valid_colors),
        _scan_mandatory_text(text, basename),
        _scan_typos_text(text, basename),
        _scan_prose_text(text, basename),
        _scan_var_refs_text(raw, basename),
        _scan_subst_keys_text(text),
    )


def process_txt_for_custom_tt_refs(filename: str) -> List[str]:
    """Pool worker: check custom_effect_tooltip / custom_trigger_tooltip keys in one .txt file.

    Valid/scripted key sets come from worker globals set by _txt_refs_init.
    """
    if _should_skip(filename):
        return []
    valid_keys, scripted_keys = _W_VALID_KEYS, _W_SCRIPTED_KEYS
    text_file = FileOpener.open_text_file(
        filename, lowercase=False, strip_comments_flag=True
    )
    if (
        "custom_effect_tooltip" not in text_file
        and "custom_trigger_tooltip" not in text_file
    ):
        return []
    simple_pattern = r"custom_effect_tooltip\s*=\s*(?!\{)(\S+)"
    basename = os.path.basename(filename)
    results = []
    for key in re.findall(simple_pattern, text_file) + _trigger_tooltip_keys(text_file):
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
    i = 0
    while True:
        m = _NOT_OPEN_RE.search(text, i)
        if not m:
            break
        body, end = extract_block_from_text(text, m.end() - 1)
        if end == -1:
            break
        out.append(body)
        i = end
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
                colon_idx = line.index(":")
                keys.add(line[:colon_idx].strip())
            except ValueError:
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

    def _collect_substitution_keys(self, yml_files: List[str]) -> frozenset:
        """Return loc keys referenced via $KEY$ string interpolation.

        These keys intentionally split § color codes across multiple values
        (e.g. `gip` ends with §Y and `gis` supplies §!) so the per-key
        §-balance check produces false positives. Caller skips that check
        for any key in this set.
        """
        keys: set = set()
        for filepath in yml_files:
            try:
                text = FileOpener.open_text_file(
                    filepath, lowercase=False, strip_comments_flag=True
                )
            except Exception:
                continue
            keys.update(_SUBST_KEY_RE.findall(text))
        return frozenset(keys)

    def _get_shared_yml_scan(self) -> dict:
        """Run every yml check in one pool pass over the yml file set.

        Reads each file once and shares the stripped text across all scans;
        each file runs exactly the scans its own check would have run, so
        findings are unchanged. The syntax color exemption against $KEY$
        substitution resolves parent-side once the repo-wide set is known.
        """
        memo = getattr(self, "_shared_yml_memo", None)
        if memo is not None:
            return memo
        self._log_section("Sharing per-file reads across localisation checks...")

        yml_files = self._get_yml_files()
        valid_colors = get_all_colors(self.mod_path)
        args_list = [(f, valid_colors) for f in yml_files]

        brackets_all: List[str] = []
        syntax_all: List = []
        mandatory_all: List[str] = []
        typos_all: List[str] = []
        prose_all: List[Issue] = []
        var_refs_all: List[Tuple[str, str, int]] = []
        subst_all: Set[str] = set()
        syntax_tagged: List = []
        for brackets, pairs, mandatory, typos, prose, var_refs, subst in self._pool_map(
            _scan_shared_yml_file, args_list, chunksize=10
        ):
            brackets_all.extend(brackets)
            syntax_tagged.extend(pairs)
            mandatory_all.extend(mandatory)
            typos_all.extend(typos)
            prose_all.extend(prose)
            var_refs_all.extend(var_refs)
            subst_all.update(subst)
        subst_keys = frozenset(subst_all)
        syntax_all.extend(
            finding for finding, key in syntax_tagged if key not in subst_keys
        )
        empty: dict = {
            "brackets": brackets_all,
            "syntax": syntax_all,
            "mandatory": mandatory_all,
            "typos": typos_all,
            "prose": prose_all,
            "var_refs": var_refs_all,
            "subst": subst_keys,
        }
        self._shared_yml_memo = empty
        return empty

    def validate_duplicated_keys(self, duplicated: List[str], skipped_keys: set):
        self._log_section("Checking for duplicated localisation keys...")

        filtered = [k for k in duplicated if k not in skipped_keys]
        self._report(
            filtered,
            "✓ No duplicated localisation keys",
            "Duplicated localisation keys:",
        )

    def validate_brackets(self):
        self._log_section("Checking for unpaired brackets in localisation...")

        results = list(self._get_shared_yml_scan()["brackets"])

        self._report(
            results,
            "✓ No unpaired brackets in localisation",
            "Unpaired brackets found in localisation:",
        )

    def validate_syntax(self):
        self._log_section("Checking localisation color syntax...")

        results = list(self._get_shared_yml_scan()["syntax"])

        self._report(
            results,
            "✓ No localisation color syntax issues",
            "Localisation color syntax issues:",
        )

    def validate_mandatory_line(self):
        self._log_section("Checking mandatory l_english: line in loc files...")

        results = list(self._get_shared_yml_scan()["mandatory"])

        self._report(
            results,
            "✓ All loc files have mandatory l_english: line",
            "Missing l_english: line in localisation files:",
        )

    def validate_typo_watchlist(self):
        self._log_section("Checking localisation values against the typo watchlist...")

        results = list(self._get_shared_yml_scan()["typos"])

        self._report(
            results,
            "✓ No typo-watchlist matches in localisation",
            "Typo-watchlist matches in localisation values:",
            severity=Severity.WARNING,
            category="loc-typo-watchlist",
        )

    def validate_prose_conventions(self):
        self._log_section(
            "Checking localisation prose conventions (em dashes, backtick apostrophes)..."
        )

        em_dash_results: List[Issue] = []
        backtick_results: List[Issue] = []
        for issue in self._get_shared_yml_scan()["prose"]:
            if issue.category == "loc-em-dash":
                em_dash_results.append(issue)
            else:
                backtick_results.append(issue)

        self._report(
            em_dash_results,
            "✓ No em dashes in localisation values",
            "Em dashes in localisation values:",
            severity=Severity.WARNING,
            category="loc-em-dash",
        )
        self._report(
            backtick_results,
            "✓ No backtick-as-apostrophe in localisation values",
            "Backtick used as apostrophe in localisation values:",
            severity=Severity.WARNING,
            category="loc-backtick-apostrophe",
        )

    def _scan_txt_refs(self, worker, txt_files, loc_keys, scripted_loc_keys):
        """Scan txt files with a worker that needs the valid/scripted key sets,
        shipped once per worker (loc_keys is ~200k entries; per-task shipping
        pickled it ~23 MB per chunk)."""
        return self._pool_map_init(
            worker,
            txt_files,
            _txt_refs_init,
            (frozenset(loc_keys), frozenset(scripted_loc_keys)),
            chunksize=30,
        )

    def validate_localization_key_references(
        self, loc_keys: Dict, scripted_loc_keys: set
    ):
        self._log_section("Checking localization_key references...")

        txt_files = self._collect_files(["**/*.txt"])
        all_results = self._scan_txt_refs(
            process_txt_for_loc_key_refs, txt_files, loc_keys, scripted_loc_keys
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
        self._log_section("Checking custom tooltip references...")

        txt_files = self._collect_files(["**/*.txt"])
        all_results = self._scan_txt_refs(
            process_txt_for_custom_tt_refs, txt_files, loc_keys, scripted_loc_keys
        )

        results = sorted({r for file_res in all_results for r in file_res})
        self._report(
            results,
            "✓ All custom tooltip references are valid",
            "Custom tooltip references not found in localisation:",
        )

    def validate_add_resistance_tooltip(self, loc_keys: Dict):
        self._log_section("Checking add_resistance_target tooltip localisation...")

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
        self._log_section("Checking for orphaned tooltip keys...")

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
            dynamic_ref_patterns.append(re.compile(f"^{esc}$"))

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

    def validate_opinion_modifiers(self, loc_keys: Dict, scripted_loc_keys: set):
        self._log_section("Checking opinion modifier localisation...")

        modifier_files = self._collect_files(
            ["common/opinion_modifiers/**/*.txt"], ignore_staged=True
        )
        modifiers: Dict[str, str] = {}
        for filepath in modifier_files:
            try:
                text = FileOpener.open_text_file(
                    filepath, lowercase=False, strip_comments_flag=True
                )
            except OSError:
                continue
            basename = os.path.basename(filepath)
            for match in _OPINION_MODIFIER_RE.finditer(text):
                name = match.group(1)
                if name not in modifiers:
                    modifiers[name] = basename

        missing = []
        for name, basename in sorted(modifiers.items()):
            if (
                name in loc_keys
                or name in scripted_loc_keys
                or name in VANILLA_LOC_KEYS
            ):
                continue
            missing.append(
                f"{name} - {basename}: opinion modifier without localisation"
            )
        self._report(
            missing,
            "\u2713 All opinion modifiers have localisation",
            "Opinion modifiers without localisation:",
            severity=Severity.WARNING,
            category="missing-opinion-modifier-localisation",
        )

    def _script_txt_files(self) -> List[str]:
        return self._collect_files(
            ["common/**/*.txt", "events/**/*.txt", "history/**/*.txt"]
        )

    def _script_written_variables(self) -> Set[str]:
        memo = getattr(self, "_script_written_vars", None)
        if memo is not None:
            return memo
        written: Set[str] = set()
        for names in self._pool_map(
            process_txt_for_var_writes,
            [(f,) for f in self._script_txt_files()],
            chunksize=30,
        ):
            written |= names
        self._script_written_vars = written
        return written

    def validate_variable_references(self):
        """`[?name]` in English loc must name a variable some script writes."""
        self._log_section("Checking [?variable] references in localisation...")

        written = self._script_written_variables()
        engine = _engine_loc_vars(self.mod_path)
        results = []
        for name, basename, number in self._get_shared_yml_scan()["var_refs"]:
            if name not in written and name not in engine:
                results.append((f"{name} - {basename}", basename, number))

        self._report(
            results,
            "✓ Every [?variable] reference resolves to a written variable",
            "Localisation reads a variable no script writes (renders as 0):",
            severity=Severity.ERROR,
            category="loc-unwritten-variable",
        )

    def validate_unwritten_script_variables(self):
        """check_variable / has_variable must name a written or engine variable."""
        self._log_section("Checking check_variable and has_variable reads...")

        known = (
            self._script_written_variables()
            | _engine_loc_vars(self.mod_path)
            | _VANILLA_WRITTEN_VARS
        )
        results = []
        for hits in self._pool_map(
            process_txt_for_script_var_reads,
            [(f,) for f in self._script_txt_files()],
            chunksize=30,
        ):
            for name, basename, number in hits:
                if name not in known and not (
                    basename == "occupation_laws.txt"
                    and name in _OCCUPATION_LAW_CONTEXT_VARS
                ):
                    results.append((f"{name} - {basename}", basename, number))

        self._report(
            results,
            "✓ Every check_variable / has_variable read is documented or written",
            "Script reads a variable no script writes (reads as 0):",
            severity=Severity.WARNING,
            category="script-unwritten-variable",
        )

    def validate_targeted_dynamic_variables(self):
        """name@target in script must be a documented dynamic var or a write."""
        self._log_section("Checking name@target dynamic variables...")

        known = self._script_written_variables() | _engine_loc_vars(self.mod_path)
        results = []
        for hits in self._pool_map(
            process_txt_for_targeted_vars,
            [(f,) for f in self._script_txt_files()],
            chunksize=30,
        ):
            for prefix, basename, number in hits:
                if prefix not in known:
                    results.append((f"{prefix} - {basename}", basename, number))

        self._report(
            results,
            "✓ Every name@target dynamic variable is documented or written",
            "Unknown name@target dynamic variable (typos read as 0):",
            severity=Severity.ERROR,
            category="unknown-dynamic-variable",
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
        self.validate_typo_watchlist()
        self.validate_prose_conventions()

        # Cross-reference checks scan all .txt/.gui files — skip in staged mode
        if not self.staged_only:
            self.validate_localization_key_references(loc_keys, scripted_loc_keys)
            self.validate_custom_tooltip_references(loc_keys, scripted_loc_keys)
            self.validate_add_resistance_tooltip(loc_keys)
            self.validate_orphaned_tooltip_keys(
                loc_keys, skipped_keys, scripted_loc_keys
            )
            self.validate_opinion_modifiers(loc_keys, scripted_loc_keys)
            self.validate_variable_references()
            self.validate_unwritten_script_variables()
            self.validate_targeted_dynamic_variables()


if __name__ == "__main__":
    run_validator_main(Validator, "Validate localisation in Millennium Dawn mod")
