#!/usr/bin/env python3
"""Validate scripted localisation definitions and usage in Millennium Dawn."""

import glob
import os
import re
from multiprocessing import Pool
from pathlib import Path
from typing import Dict, List, Set, Tuple

import disk_cache
from shared_utils import validation_config
from validate_gfx_references import sprite_names_from_gfx_text
from validator_common import (
    BaseValidator,
    Colors,
    DataCleaner,
    FileOpener,
    Issue,
    Severity,
    find_line_number,
    run_validator_main,
    scan_meta_constructed_names,
    should_skip_file,
)


def _scan_defined_locs(text: str, basename: str) -> Tuple[List[str], Dict[str, str]]:
    localisations: List[str] = []
    paths: Dict[str, str] = {}
    if "defined_text" in text and "name =" in text:
        for match in re.findall(r"name\s*=\s*(\w[\w-]*)", text):
            localisations.append(match)
            paths[match] = basename
    return (localisations, paths)


def process_file_for_defined_localisations(
    args: Tuple[str, bool, str],
) -> Tuple[List[str], Dict[str, str]]:
    filename, lowercase, mod_path = args

    if should_skip_file(filename, mod_path=mod_path):
        return ([], {})

    if "00_scripted_localisation_FR_loc" in filename:
        return ([], {})

    text_file = FileOpener.open_text_file(
        filename, lowercase=lowercase, strip_comments_flag=True
    )
    basename = os.path.basename(filename)
    return disk_cache.per_file_cached_by_content(
        mod_path,
        f"scripted_loc.defined.v3.lc={1 if lowercase else 0}",
        filename,
        text_file,
        lambda: _scan_defined_locs(text_file, basename),
    )


# Scripted loc names may contain hyphens and non-ASCII letters
# (additional_income_GER_Ökosteuer); an ASCII-only class truncates both and invents findings.
_LOC_REFERENCE_RE = re.compile(
    r"\b(?:custom_(?:effect|trigger|prerequisite|gain_xp)_tooltip|"
    r"localization_key)\s*=\s*(\w[\w-]*)"
)
# Scope chains can be multi-level: a map-mode tooltip scopes to a state, so the country
# scripted loc is only reachable as [FROM.CONTROLLER.name]. A single-segment prefix misses
# those calls and reports the target as unused.
_BRACKET_LOC_RE = re.compile(r"\[((?:[A-Za-z_][A-Za-z0-9_]*\.)+)?(\w[\w-]*)\]")


def _find_reference_line(path: str, name: str) -> int:
    # A bare substring search lands on the wrong line: looking for `adjective` matches
    # inside `GetAdjective`. Anchor on the call syntax instead.
    try:
        text = FileOpener.open_text_file(
            path, lowercase=False, strip_comments_flag=False
        )
    except OSError:
        return 0

    target = name.lower()
    for match in _BRACKET_LOC_RE.finditer(text):
        if match.group(2).lower() == target:
            return text.count("\n", 0, match.start()) + 1
    for match in _LOC_REFERENCE_RE.finditer(text):
        if match.group(1).lower() == target:
            return text.count("\n", 0, match.start()) + 1
    return find_line_number(path, name, lowercase=True)


def _find_definition_line(path: str, name: str) -> int:
    # `name = communist` as a substring also matches `name = communist_state_valid`.
    try:
        text = FileOpener.open_text_file(
            path, lowercase=False, strip_comments_flag=False
        )
    except OSError:
        return 0

    pattern = re.compile(
        r"name\s*=\s*" + re.escape(name) + r"(?![A-Za-z0-9_-])", re.IGNORECASE
    )
    match = pattern.search(text)
    if match:
        return text.count("\n", 0, match.start()) + 1
    return find_line_number(path, f"name = {name}", lowercase=True)


def _filter_bracket_loc_candidates(
    candidates: Set[Tuple[str, bool]], defined_names: Set[str]
) -> Set[str]:
    defined_lower = {name.lower() for name in defined_names}
    return {
        name
        for name, _scoped in candidates
        if name.lower() in defined_lower or not name.lower().startswith("get")
    }


def _scan_loc_token_candidates(
    text: str, is_scripted_loc_file: bool
) -> Tuple[Set[Tuple[str, bool]], Set[str]]:
    bracketed = {
        (member, bool(scope)) for scope, member in _BRACKET_LOC_RE.findall(text)
    }
    explicit = set() if is_scripted_loc_file else set(_LOC_REFERENCE_RE.findall(text))
    return bracketed, explicit


def _scan_loc_tokens(
    text: str, is_scripted_loc_file: bool, defined_names: Set[str] | None = None
) -> Set[str]:
    bracketed, explicit = _scan_loc_token_candidates(text, is_scripted_loc_file)
    return _filter_bracket_loc_candidates(bracketed, defined_names or set()) | explicit


_LOC_OBJECTS_DOC = os.path.join(
    "resources", "documentation", "loc_objects_documentation.md"
)
_DOC_GETTER_RE = re.compile(r"^\*\*(\w+)\*\*\s*$", re.MULTILINE)
# Vanilla defined_text that the mod's replace/ strings call but does not ship.
_VANILLA_SCRIPTED_LOCS = frozenset({"GetCountryContinent"})


def _documented_getters(mod_path: str) -> frozenset:
    try:
        with open(
            os.path.join(mod_path, _LOC_OBJECTS_DOC), "r", encoding="utf-8"
        ) as handle:
            return frozenset(_DOC_GETTER_RE.findall(handle.read()))
    except OSError:
        return frozenset()


def _getter_spelling_message(
    member: str, defined_lower: Set[str], documented: frozenset
) -> str:
    """Why a bracket member is neither a scripted loc nor a documented getter, or ""."""
    if (
        member in documented
        or member in _VANILLA_SCRIPTED_LOCS
        or member.lower() in defined_lower
    ):
        return ""
    spelling = next((g for g in documented if g.lower() == member.lower()), None)
    if spelling:
        return f"'{member}' is not the documented getter spelling '{spelling}'"
    if member.lower().startswith("get"):
        return (
            f"'{member}' is neither a defined scripted localisation "
            "nor a documented engine getter"
        )
    return ""


def process_file_for_getter_refs(filename: str) -> List[Tuple[str, int]]:
    """Pool worker: (member, line) for every [SCOPE.Member] call in one file."""
    text = FileOpener.open_text_file(
        filename, lowercase=False, strip_comments_flag=True
    )
    refs = []
    # Matches come in file order, so count only the newlines since the last one.
    line, pos = 1, 0
    for match in _BRACKET_LOC_RE.finditer(text):
        line += text.count("\n", pos, match.start())
        pos = match.start()
        refs.append((match.group(2), line))
    return refs


def _path_key(mod_path: str, filename: str) -> str:
    return os.path.normpath(os.path.join(mod_path, filename))


def process_file_for_used_localisations(
    args: Tuple[str, Set[str], bool, str],
) -> Tuple[List[str], Dict[str, str]]:
    filename, search_names, lowercase, mod_path = args

    if should_skip_file(filename, mod_path=mod_path):
        return ([], {})

    basename = os.path.basename(filename)

    text_file = FileOpener.open_text_file(
        filename, lowercase=lowercase, strip_comments_flag=True
    )

    # Cache raw candidates (independent of search_names); filter after the cache
    # hit so a changing defined set never invalidates the entry.
    is_sl = "scripted_localisation" in filename
    bracketed, explicit = disk_cache.per_file_cached_by_content(
        mod_path,
        f"scripted_loc.tokens.v5.lc={1 if lowercase else 0}.{'b' if is_sl else 't'}",
        filename,
        text_file,
        lambda: _scan_loc_token_candidates(text_file, is_sl),
    )
    tokens = _filter_bracket_loc_candidates(bracketed, search_names) | explicit

    # Scripted-localisation, GUI, and English localisation files use bracket
    # syntax for scripted loc calls. Keep candidates even when undefined so
    # the missing check can report them.
    normalized_filename = filename.replace("\\", "/").lstrip("/")
    is_english_yml = "localisation/english/" in normalized_filename
    if (
        is_sl
        or filename.endswith(".gui")
        or (filename.endswith(".yml") and is_english_yml)
    ):
        found_original = tokens
    else:
        search_lower = {n.lower(): n for n in search_names}
        found_original = {
            search_lower[t.lower()] for t in tokens if t.lower() in search_lower
        }

    if not found_original:
        return ([], {})

    localisations = sorted(found_original)
    paths = {name: basename for name in found_original}
    return (localisations, paths)


def _scan_used_and_getter_refs(
    args: Tuple[str, Set[str], bool, str],
) -> Tuple[Tuple[List[str], Dict[str, str]], List[Tuple[str, int]] | None]:
    """Pool worker: the usage scan, plus a .yml or .gui file's getter calls
    from FileOpener's copy of the text the usage scan just read."""
    used = process_file_for_used_localisations(args)
    filename, _names, _lowercase, mod_path = args
    if not filename.endswith((".yml", ".gui")) or should_skip_file(
        filename, mod_path=mod_path
    ):
        return used, None
    return used, process_file_for_getter_refs(filename)


def _map_files(func, args_list, workers, pool, chunksize):
    """Use the caller's pool, map in-process for one worker, else a transient pool."""
    if pool is not None:
        return pool.map(func, args_list, chunksize=chunksize)
    if workers == 1:
        return [func(args) for args in args_list]
    with Pool(processes=workers) as p:
        return p.map(func, args_list, chunksize=chunksize)


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
        results = _map_files(
            process_file_for_defined_localisations, args_list, workers, pool, 10
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
        pool=None,
        *,
        getter_refs: Dict[str, List[Tuple[str, int]]] | None = None,
    ):
        """Scripted locs the scanned files use.

        When ``getter_refs`` is given, each scanned .yml and .gui file's getter
        calls are added to it, keyed by ``_path_key``, from the same read.
        """
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
                glob.iglob(
                    os.path.join(mod_path, "localisation", "english", "**", "*.yml"),
                    recursive=True,
                )
            )
            txt_files = list(
                glob.iglob(os.path.join(mod_path, "**", "*.txt"), recursive=True)
            )
            files_to_scan = gui_files + yml_files + txt_files

        args_list = [(f, search_names, lowercase, mod_path) for f in files_to_scan]
        if getter_refs is None:
            results = _map_files(
                process_file_for_used_localisations, args_list, workers, pool, 50
            )
        else:
            scans = _map_files(_scan_used_and_getter_refs, args_list, workers, pool, 50)
            results = [used for used, _refs in scans]
            for filename, (_used, refs) in zip(files_to_scan, scans):
                if refs is not None:
                    getter_refs[_path_key(mod_path, filename)] = refs

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

        used_locs_lower = (
            DataCleaner.clear_false_positives_partial_match(
                used_locs_lower_raw, tuple(false_positives)
            )
            or []
        )

        results = []
        reported = set()
        for loc in used_locs_lower:
            if loc not in defined_locs_lower and loc not in reported:
                original_loc = used_lower_to_original.get(loc) or loc
                basename = used_paths.get(original_loc, used_paths.get(loc, "unknown"))
                full_path = self.get_full_path(
                    basename,
                    original_loc,
                    file_patterns=[
                        "**/*.txt",
                        "**/*.gui",
                        "localisation/english/**/*.yml",
                    ],
                )
                if full_path:
                    rel_path = os.path.relpath(full_path, self.mod_path)
                    line_num = _find_reference_line(full_path, loc)
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

        unused_only = validation_config(
            "validate_scripted_localisation", "unused_only_false_positives"
        )

        defined_lower_to_original = {loc.lower(): loc for loc in defined_locs}
        defined_locs_lower = [loc.lower() for loc in defined_locs]
        used_locs_lower = [loc.lower() for loc in used_locs]

        defined_locs_lower = (
            DataCleaner.clear_false_positives_partial_match(
                defined_locs_lower,
                tuple(false_positives) + tuple(unused_only),
            )
            or []
        )

        results = []
        reported = set()
        for loc in defined_locs_lower:
            if loc not in used_locs_lower and loc not in reported:
                original_loc = defined_lower_to_original.get(loc, loc)
                basename = defined_paths.get(
                    original_loc or loc, defined_paths.get(loc, "unknown")
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
                    line_num = _find_definition_line(full_path, loc)
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
                filename, lowercase=False, strip_comments_flag=False
            )
            defined_gfx.update(sprite_names_from_gfx_text(text_file))

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

    def validate_getter_spelling(
        self,
        defined_locs: List[str],
        scanned_refs: Dict[str, List[Tuple[str, int]]] | None = None,
    ):
        """``scanned_refs`` holds getter calls the usage scan already read,
        keyed by ``_path_key``; any other file is read here."""
        self._log_section("Checking engine getter spelling in localisation...")

        documented = _documented_getters(self.mod_path)
        if not documented:
            self.log(
                f"{_LOC_OBJECTS_DOC} not found — skipping getter spelling check",
                "warning",
            )
            return

        defined_lower = {name.lower() for name in defined_locs}
        files = self._collect_files(
            ["localisation/english/**/*.yml", "interface/**/*.gui"],
            extra_skip=lambda f: should_skip_file(f, mod_path=self.mod_path),
        )
        refs_by_key = dict(scanned_refs or {})
        unscanned = [f for f in files if _path_key(self.mod_path, f) not in refs_by_key]
        for filename, refs in zip(
            unscanned, self._pool_map(process_file_for_getter_refs, unscanned)
        ):
            refs_by_key[_path_key(self.mod_path, filename)] = refs
        results = []
        for filename in files:
            rel_path = os.path.relpath(filename, self.mod_path)
            for member, line in refs_by_key[_path_key(self.mod_path, filename)]:
                message = _getter_spelling_message(member, defined_lower, documented)
                if message:
                    results.append(
                        Issue(
                            severity=Severity.WARNING,
                            category="loc-getter-spelling",
                            message=message,
                            file=rel_path,
                            line=line,
                        )
                    )

        self._report(
            results,
            "✓ All getter calls use a defined scripted loc or documented getter",
            "Getter calls that are neither scripted loc nor documented getters:",
            Severity.WARNING,
            category="loc-getter-spelling",
        )

    def run_validations(self):
        if self.staged_only and not self.staged_files:
            self.log(
                "No staged files found — skipping scripted localisation validation",
                "warning",
            )
            return

        # Entries match as substrings, so a short suffix entry swallows real names.
        false_positives = list(
            validation_config("validate_scripted_localisation", "false_positives")
        )

        getter_refs: Dict[str, List[Tuple[str, int]]] = {}
        if self.staged_only:
            # Staged scans cover a handful of files, so they map in-process.
            all_defined_locs = ScriptedLocalisation.get_all_defined_localisations(
                mod_path=self.mod_path, lowercase=False, workers=1
            )
            defined_locs, defined_paths = (
                ScriptedLocalisation.get_all_defined_localisations(
                    mod_path=self.mod_path,
                    lowercase=False,
                    return_paths=True,
                    staged_files=self.staged_files,
                    workers=1,
                )
            )
            missing_locs, missing_paths = (
                ScriptedLocalisation.get_all_used_localisations(
                    mod_path=self.mod_path,
                    defined_names=set(all_defined_locs),
                    lowercase=False,
                    return_paths=True,
                    staged_files=self.staged_files,
                    workers=1,
                    getter_refs=getter_refs,
                )
            )
            # The unused check reports staged definitions only, so it needs the
            # repo-wide consumer scan only when a definition file is staged.
            all_used_locs: List[str] = []
            if defined_locs:
                all_used_locs = ScriptedLocalisation.get_all_used_localisations(
                    mod_path=self.mod_path,
                    defined_names=set(all_defined_locs),
                    lowercase=False,
                    workers=self.workers,
                    pool=self._get_pool(),
                )
        else:
            all_defined_locs, all_defined_paths = (
                ScriptedLocalisation.get_all_defined_localisations(
                    mod_path=self.mod_path,
                    lowercase=False,
                    return_paths=True,
                    staged_files=None,
                    workers=self.workers,
                    pool=self._get_pool(),
                )
            )
            all_used_locs, all_used_paths = (
                ScriptedLocalisation.get_all_used_localisations(
                    mod_path=self.mod_path,
                    defined_names=set(all_defined_locs),
                    lowercase=False,
                    return_paths=True,
                    staged_files=None,
                    workers=self.workers,
                    pool=self._get_pool(),
                    getter_refs=getter_refs,
                )
            )
            defined_locs, defined_paths = all_defined_locs, all_defined_paths
            missing_locs, missing_paths = all_used_locs, all_used_paths

        self.validate_missing_scripted_localisations(
            false_positives, all_defined_locs, missing_locs, missing_paths
        )
        self.validate_unused_scripted_localisations(
            false_positives, defined_locs, defined_paths, all_used_locs
        )
        self.validate_getter_spelling(all_defined_locs, getter_refs)

        # GFX icon check scans all interface/*.gfx files — skip in staged mode
        if not self.staged_only:
            self.validate_gfx_icons()


if __name__ == "__main__":
    run_validator_main(
        Validator, "Validate scripted localisation in Millennium Dawn mod"
    )
