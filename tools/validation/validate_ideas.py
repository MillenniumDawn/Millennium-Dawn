#!/usr/bin/env python3
"""Validate idea definitions and usage in Millennium Dawn."""
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import disk_cache
from validator_common import (
    HOI4_BUILTIN_BLOCKS,
    BaseValidator,
    Colors,
    FileOpener,
    Severity,
    case_mismatch,
    casefold_index,
    run_validator_main,
    should_skip_file,
)

# --- Module-level compiled patterns ---

# Matches `has_idea = FOO`, `add_ideas = FOO`, `remove_ideas = FOO`
# Captures the full token including `:` and `[` so dynamic refs can be filtered.
# Hyphens are included so that identifiers like `NKO_Marxism-Leninism` are captured whole.
_IDEA_REF_SIMPLE = re.compile(
    r"\b(?:has_idea|add_ideas|remove_ideas)\s*=\s*([A-Za-z0-9_:\[\].-]+)"
)

# Matches `add_idea = FOO` and `remove_idea = FOO` inside swap_ideas blocks
_IDEA_REF_SWAP = re.compile(r"\b(?:add_idea|remove_idea)\s*=\s*([A-Za-z0-9_:\[\].-]+)")

# Matches swap_ideas = { ... } blocks (brace-balanced by hand after this finds the opener)
_SWAP_BLOCK_START = re.compile(r"\bswap_ideas\s*=\s*\{")

# Matches an idea definition line at brace depth 2 inside `ideas = { CATEGORY = { IDEA = { `
# We track depth manually; this just recognises `WORD = {` at the right level.
# Hyphens are included so that identifiers like `NKO_Marxism-Leninism` are recognised.
_IDEA_DEF_LINE = re.compile(r"^[\t ]*([A-Za-z][A-Za-z0-9_-]*)\s*=\s*\{")

# Idea-schema inner keys that appear at depth 2 but are not idea definitions.
# The control-flow / effect blocks (if, limit, modifier, scope iterators, etc.)
# come from the canonical HOI4_BUILTIN_BLOCKS so they don't drift; only the
# idea-specific schema keys are listed here.
_HOI4_IDEA_INNER_KEYS: frozenset = HOI4_BUILTIN_BLOCKS | frozenset(
    {
        "equipment_bonus",
        "allowed",
        "allowed_civil_war",
        "available",
        "visible",
        "cancel",
        "on_add",
        "on_remove",
        "cancel_if_invalid",
        "picture",
        "cost",
        "removal_cost",
        "level",
        "law",
        "designer",
        "use_list_view",
        "research_bonus",
        "traits",
        "ai_will_do",
        "default",
        "targeted_modifier",
        "ledger",
        "do_effect",
        "rule",
        "name",
        "priority",
    }
)

# Categories where `allowed = { always = no }` is flagged as redundant
# Dynamically parsed from common/idea_tags/*.txt — non-selectable categories
# (those without slot=/character_slot= or with hidden=yes)
from shared_utils import extract_block_from_text  # noqa: E402
from shared_utils import (  # noqa: E402
    get_non_selectable_idea_categories as _get_non_selectable_idea_categories,
)

_ALWAYS_NO_CATEGORIES = _get_non_selectable_idea_categories()

# Vanilla idea prefixes that we skip for undefined-reference checks
# (game-engine built-ins, vanilla ideas, etc.)
_VANILLA_IDEA_PREFIXES: Tuple[str, ...] = (
    "generic_",
    "neutrality_idea",
    "democratic_idea",
    "fascism_idea",
    "communism_idea",
)


def _extract_swap_idea_refs(text: str) -> List[str]:
    """Return every idea name referenced inside swap_ideas = { ... } blocks."""
    refs: List[str] = []
    for m in _SWAP_BLOCK_START.finditer(text):
        block, _ = extract_block_from_text(text, m.end() - 1)
        refs.extend(_IDEA_REF_SWAP.findall(block))
    return refs


_NAME_OVERRIDE_LINE = re.compile(r"^\s+name\s*=\s*([A-Za-z0-9_.]+)", re.MULTILINE)
_ALLOWED_ALWAYS_NO = re.compile(r"\ballowed\s*=\s*\{\s*always\s*=\s*no\s*\}")
_CANCEL_ALWAYS_NO = re.compile(r"\bcancel\s*=\s*\{\s*always\s*=\s*no\s*\}")
_ALLOWED_TAG_CHECK = re.compile(r"\ballowed\s*=\s*\{[^}]*\btag\s*=\s*([A-Z]{3})[^}]*\}")
_PICTURE_LINE = re.compile(r"^\s+picture\s*=", re.MULTILINE)
_ON_ADD_BLOCK_START = re.compile(r"\bon_add\s*=\s*\{")
_LOG_LINE = re.compile(r'^\s*log\s*=\s*"[^"]*"\s*$')


def _on_add_is_log_only(idea_text: str) -> bool:
    """True if every on_add block in this idea contains only log = "..." lines.

    Returns False if there are no on_add blocks at all, so callers can use
    the boolean directly as "should we flag this idea".
    """
    found_any = False
    for m in _ON_ADD_BLOCK_START.finditer(idea_text):
        body, _ = extract_block_from_text(idea_text, m.end() - 1)
        found_any = True

        non_log = False
        for line in body.split("\n"):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if _LOG_LINE.match(stripped):
                continue
            non_log = True
            break
        if non_log:
            return False
    return found_any


@dataclass
class IdeaIssue:
    idea_name: str
    category: str
    line: int
    issue_type: str
    detail: str = ""


def _parse_ideas_from_file(
    filepath: str, mod_path: str
) -> Tuple[Dict[str, Tuple[str, Optional[str]]], List[IdeaIssue]]:
    """Read one ideas file and return (defined_ideas, issues), content-cached."""
    text = FileOpener.open_text_file(
        filepath, lowercase=False, strip_comments_flag=True
    )
    if not text:
        return {}, []
    return disk_cache.per_file_cached_by_content(
        mod_path, "ideas.defs", filepath, text, lambda: _parse_ideas_from_text(text)
    )


def _parse_ideas_from_text(
    text: str,
) -> Tuple[Dict[str, Tuple[str, Optional[str]]], List[IdeaIssue]]:
    """Parse ideas-file text and return (defined_ideas, issues).

    defined_ideas maps idea_name -> (category_name, name_override_or_None).
    issues is a list of IdeaIssue for problems found during parsing.
    """
    defined: Dict[str, Tuple[str, Optional[str]]] = {}
    issues: List[IdeaIssue] = []

    lines = text.split("\n")
    depth = 0
    category_name: Optional[str] = None
    current_idea: Optional[str] = None
    current_idea_line: int = 0
    idea_open_depth: int = 0
    category_open_depth: int = 0
    idea_lines: List[str] = []

    for lineno, line in enumerate(lines, 1):
        opens = line.count("{")
        closes = line.count("}")

        m = _IDEA_DEF_LINE.match(line)
        token = m.group(1) if m else None

        prev_depth = depth
        depth += opens - closes

        if prev_depth == 0 and opens > 0 and token == "ideas":
            continue

        if prev_depth == 1 and opens > 0 and token is not None:
            category_name = token
            category_open_depth = depth - opens + 1
            current_idea = None
            idea_lines = []
            continue

        if (
            category_name is not None
            and prev_depth == 2
            and opens > 0
            and token is not None
        ):
            if token not in _HOI4_IDEA_INNER_KEYS:
                current_idea = token
                current_idea_line = lineno
                idea_open_depth = depth - opens + 1
                idea_lines = [line]
                defined[token] = (category_name, None)
                continue

        if current_idea is not None:
            idea_lines.append(line)
            if depth < idea_open_depth:
                idea_text = "\n".join(idea_lines)
                nm = _NAME_OVERRIDE_LINE.search(idea_text)
                name_override = nm.group(1) if nm else None
                cat, _ = defined[current_idea]
                defined[current_idea] = (cat, name_override)

                if category_name in _ALWAYS_NO_CATEGORIES:
                    if _ALLOWED_ALWAYS_NO.search(idea_text):
                        issues.append(
                            IdeaIssue(
                                current_idea,
                                category_name,
                                current_idea_line,
                                "allowed-always-no",
                            )
                        )

                if _CANCEL_ALWAYS_NO.search(idea_text):
                    issues.append(
                        IdeaIssue(
                            current_idea,
                            category_name,
                            current_idea_line,
                            "cancel-always-no",
                        )
                    )

                tag_match = _ALLOWED_TAG_CHECK.search(idea_text)
                if (
                    tag_match
                    and "original_tag"
                    not in idea_text.split("allowed")[1].split("}")[0]
                    if "allowed" in idea_text
                    else False
                ):
                    if category_name in _ALWAYS_NO_CATEGORIES:
                        issues.append(
                            IdeaIssue(
                                current_idea,
                                category_name,
                                current_idea_line,
                                "tag-not-original-tag",
                                detail=tag_match.group(1),
                            )
                        )

                if _on_add_is_log_only(idea_text):
                    issues.append(
                        IdeaIssue(
                            current_idea,
                            category_name,
                            current_idea_line,
                            "on-add-log-only",
                        )
                    )

                current_idea = None
                idea_lines = []

        if category_name is not None and depth < category_open_depth:
            category_name = None

    return defined, issues


def _scan_idea_refs(text: str) -> List[str]:
    """Return every raw idea reference token in the text (unfiltered)."""
    refs: List[str] = []
    refs.extend(_IDEA_REF_SIMPLE.findall(text))
    refs.extend(_extract_swap_idea_refs(text))
    return refs


def _check_file_for_refs(args: Tuple[str, frozenset, dict, str]) -> List[str]:
    """Pool worker: return undefined idea references found in one file.

    *defined_ci* maps lower-cased idea name -> canonical name; a ref that misses
    case-sensitively but hits here is a case mismatch that works on Windows and
    silently fails on Linux, so it gets a distinct, louder message.
    """
    filepath, defined_ideas_frozen, defined_ci, mod_path = args
    if should_skip_file(filepath):
        return []
    text = FileOpener.open_text_file(
        filepath, lowercase=False, strip_comments_flag=True
    )
    if not text:
        return []

    # Quick skip: none of the idea-reference keywords present
    if not any(
        kw in text for kw in ("has_idea", "add_ideas", "remove_ideas", "swap_ideas")
    ):
        return []

    # Cache the raw (filter-independent) ref extraction; the filter below depends
    # on the volatile defined-set, so it must run per call after the cache hit.
    refs = disk_cache.per_file_cached_by_content(
        mod_path, "ideas.refs", filepath, text, lambda: _scan_idea_refs(text)
    )

    results: List[str] = []
    basename = os.path.basename(filepath)
    for idea in refs:
        if idea in defined_ideas_frozen:
            continue
        if "[" in idea or "]" in idea or ":" in idea:
            continue
        if idea.startswith(_VANILLA_IDEA_PREFIXES):
            continue
        # Skip pure numbers and very short tokens that are clearly not idea names
        if idea.isdigit() or len(idea) < 3:
            continue
        canonical = case_mismatch(idea, defined_ci)
        if canonical:
            results.append(
                f"{basename}: case-mismatch idea reference '{idea}' — defined as "
                f"'{canonical}' (works on Windows, fails on Linux)"
            )
        else:
            results.append(f"{basename}: undefined idea reference '{idea}'")
    return results


class Validator(BaseValidator):
    TITLE = "IDEA VALIDATION"
    STAGED_EXTENSIONS = [".txt"]

    def __init__(self, *args, **kwargs):
        self.missing_loc = kwargs.pop("missing_loc", False)
        self.suggest_consolidation = kwargs.pop("suggest_consolidation", False)
        super().__init__(*args, **kwargs)

    def _parse_all_ideas(
        self,
    ) -> Tuple[
        Dict[str, Tuple[str, Optional[str]]],
        Dict[str, List[IdeaIssue]],
        Dict[str, List[str]],
    ]:
        """Parse all idea files and return (defined_ideas, issues_by_file, ideas_by_file).

        Always parses every idea file regardless of staged mode — the full
        set of defined ideas is needed as the reference for undefined-ref checks.
        """
        # Force full scan for idea definitions even in staged mode
        saved = self.staged_only
        self.staged_only = False
        idea_files = self._collect_files(["common/ideas/**/*.txt"])
        self.staged_only = saved
        self.log(f"  Parsing {len(idea_files)} idea files...")

        all_defined: Dict[str, Tuple[str, Optional[str]]] = {}
        issues_by_file: Dict[str, List[IdeaIssue]] = {}
        ideas_by_file: Dict[str, List[str]] = {}

        for filepath in idea_files:
            defined, issues = _parse_ideas_from_file(filepath, self.mod_path)
            all_defined.update(defined)
            ideas_by_file[filepath] = list(defined.keys())
            if issues:
                issues_by_file[filepath] = issues

        # Also collect idea_token entries from character files
        saved2 = self.staged_only
        self.staged_only = False
        char_files = self._collect_files(["common/characters/**/*.txt"])
        self.staged_only = saved2
        idea_token_re = re.compile(r"\bidea_token\s*=\s*([A-Za-z0-9_]+)")
        char_tokens = 0
        for filepath in char_files:
            text = FileOpener.open_text_file(
                filepath, lowercase=False, strip_comments_flag=True
            )
            if not text or "idea_token" not in text:
                continue
            for token in idea_token_re.findall(text):
                if token not in all_defined:
                    all_defined[token] = ("character", None)
                    char_tokens += 1
        self.log(f"  Found {char_tokens} character idea_token entries")

        return all_defined, issues_by_file, ideas_by_file

    def validate_undefined_idea_refs(
        self, defined_ideas: Dict[str, Tuple[str, Optional[str]]]
    ):
        self._log_section("Checking for undefined idea references...")
        self.log(f"  Known defined ideas: {len(defined_ideas)}")

        scan_files = self._collect_files(
            [
                "common/national_focus/**/*.txt",
                "common/decisions/**/*.txt",
                "events/**/*.txt",
                "common/scripted_effects/**/*.txt",
                "common/ideas/**/*.txt",
            ]
        )
        self.log(f"  Scanning {len(scan_files)} files for idea references...")

        defined_frozen = frozenset(defined_ideas.keys())
        # Case-insensitive index for Linux case-mismatch diagnostics.
        defined_ci = casefold_index(defined_ideas)
        args_list = [(f, defined_frozen, defined_ci, self.mod_path) for f in scan_files]

        raw_results = self._pool_map(_check_file_for_refs, args_list)
        results: List[str] = []
        for sub in raw_results:
            results.extend(sub)

        # Deduplicate while preserving first-seen order
        seen: Set[str] = set()
        deduped: List[str] = []
        for r in results:
            if r not in seen:
                seen.add(r)
                deduped.append(r)

        self._report(
            sorted(deduped),
            "✓ No undefined idea references",
            "Undefined idea references (has_idea / add_ideas / remove_ideas / swap_ideas):",
            severity=Severity.ERROR,
            category="undefined-idea-ref",
        )

    def _report_grouped(
        self,
        issues_by_file: Dict[str, List[str]],
        ok_msg: str,
        fail_msg: str,
        severity: str = Severity.WARNING,
        category: str = "",
        max_detail_per_file: int = 5,
    ):
        """Report issues grouped by file with capped detail lines."""
        total = sum(len(v) for v in issues_by_file.values())
        if total == 0:
            c = Colors.GREEN if self.use_colors else ""
            e = Colors.ENDC if self.use_colors else ""
            self.log(f"{c}{ok_msg}{e}")
            return

        c_err = Colors.RED if severity == Severity.ERROR else Colors.YELLOW
        c = c_err if self.use_colors else ""
        e = Colors.ENDC if self.use_colors else ""

        self.log(
            f"{c}{fail_msg}{e}", "error" if severity == Severity.ERROR else "warning"
        )
        for filepath in sorted(issues_by_file):
            items = issues_by_file[filepath]
            basename = os.path.basename(filepath)
            if len(items) <= max_detail_per_file:
                for item in items:
                    self.log(
                        f"{c}  {basename}: {item}{e}",
                        "error" if severity == Severity.ERROR else "warning",
                    )
            else:
                for item in items[:max_detail_per_file]:
                    self.log(
                        f"{c}  {basename}: {item}{e}",
                        "error" if severity == Severity.ERROR else "warning",
                    )
                self.log(
                    f"{c}  {basename}: ... and {len(items) - max_detail_per_file} more{e}",
                    "error" if severity == Severity.ERROR else "warning",
                )

        self.log(
            f"{c}{total} issue(s) found across {len(issues_by_file)} file(s){e}",
            "error" if severity == Severity.ERROR else "warning",
        )

        if severity == Severity.ERROR:
            self.errors_found += total
        else:
            self.warnings_found += total

    def validate_idea_quality(self, issues_by_file: Dict[str, List[IdeaIssue]]):
        """Validate redundant patterns and misuse found during parsing."""
        self._log_section("Checking idea definition quality...")

        idea_files = self._collect_files(["common/ideas/**/*.txt"])
        acw_pattern = re.compile(r"allowed_civil_war\s*=\s*\{\s*always\s*=\s*no\s*\}")

        grouped: Dict[str, List[str]] = defaultdict(list)

        for filepath in idea_files:
            text = FileOpener.open_text_file(
                filepath, lowercase=False, strip_comments_flag=True
            )
            if not text:
                continue
            basename = os.path.basename(filepath)
            for m in acw_pattern.finditer(text):
                lineno = text[: m.start()].count("\n") + 1
                grouped[basename].append(
                    f"line {lineno}: redundant allowed_civil_war = {{ always = no }}"
                )

        for filepath, file_issues in issues_by_file.items():
            basename = os.path.basename(filepath)
            for issue in file_issues:
                if issue.issue_type == "allowed-always-no":
                    grouped[basename].append(
                        f"line {issue.line}: '{issue.idea_name}' has allowed = {{ always = no }} in {issue.category}"
                        " (redundant; removing trades slightly more memory for faster load times)"
                    )
                elif issue.issue_type == "cancel-always-no":
                    grouped[basename].append(
                        f"line {issue.line}: '{issue.idea_name}' has cancel = {{ always = no }} (checked hourly, always false)"
                    )
                elif issue.issue_type == "tag-not-original-tag":
                    grouped[basename].append(
                        f"line {issue.line}: '{issue.idea_name}' uses tag = {issue.detail} in allowed (use original_tag for civil war safety)"
                    )
                elif issue.issue_type == "on-add-log-only":
                    grouped[basename].append(
                        f"line {issue.line}: '{issue.idea_name}' has on_add = {{ log = ... }} with no real effects"
                        " (drop the on_add block — tracing-only logs are dead weight)"
                    )

        self._report_grouped(
            grouped,
            "✓ No idea definition quality issues",
            "Idea definition issues:",
            severity=Severity.WARNING,
            category="idea-quality",
        )

    def validate_loc_consolidation(
        self,
        defined_ideas: Dict[str, Tuple[str, Optional[str]]],
        ideas_by_file: Dict[str, List[str]],
    ):
        """Suggest consolidation when sibling ideas in the same file share
        identical English loc strings but don't use `name = X` to point at a
        shared key. Catches the case where N tiers each get their own
        `TAG_idea_2`, `TAG_idea_3` loc entries with the same text — the
        upgraded tiers should set `name = TAG_idea_1` and drop the duplicate
        loc keys.

        Reports at WARNING severity only — never an error. This is an
        advisory cleanup hint, not a correctness check, so it must never
        fail CI even in strict mode.
        """
        self._log_section("Checking for loc-consolidation opportunities...")

        sys.path.insert(0, os.path.dirname(__file__))
        from validate_localisation import get_all_loc_keys

        loc_values, _ = get_all_loc_keys(self.mod_path, lowercase=False)

        def _norm(s: Optional[str]) -> Optional[str]:
            if s is None:
                return None
            s = s.strip()
            if s.startswith("$") and s.endswith("$"):
                return s[1:-1].strip()
            return s

        grouped: Dict[str, List[str]] = defaultdict(list)

        for filepath, idea_ids in ideas_by_file.items():
            by_display: Dict[str, List[str]] = defaultdict(list)

            for idea_id in idea_ids:
                _cat, name_override = defined_ideas.get(idea_id, (None, None))
                if name_override is not None:
                    continue
                display = loc_values.get(idea_id)
                if not display:
                    continue
                by_display[display].append(idea_id)

            for display, members in by_display.items():
                if len(members) < 2:
                    continue

                desc_norm: Dict[str, Optional[str]] = {}
                for m in members:
                    desc_norm[m] = _norm(loc_values.get(m + "_desc"))
                unique_descs = {v for v in desc_norm.values() if v is not None}
                if len(unique_descs) > 1:
                    continue

                base = sorted(members)[0]
                redundant = sorted(m for m in members if m != base)
                basename = os.path.basename(filepath)
                grouped[basename].append(
                    f"{len(members)} ideas share display name '{display}': "
                    f"{', '.join(members)} — set `name = {base}` on "
                    f"{', '.join(redundant)} and drop their duplicate loc keys"
                )

        self._report_grouped(
            grouped,
            "✓ No loc-consolidation opportunities found",
            "Loc-consolidation suggestions (advisory — siblings with identical loc strings):",
            severity=Severity.WARNING,
            category="loc-consolidation",
            max_detail_per_file=3,
        )

    def validate_missing_localisation(
        self, defined_ideas: Dict[str, Tuple[str, Optional[str]]]
    ):
        self._log_section("Checking for ideas with missing localisation keys...")

        sys.path.insert(0, os.path.dirname(__file__))
        from validate_localisation import get_all_loc_keys

        loc_dict, _ = get_all_loc_keys(self.mod_path, lowercase=False)
        loc_keys: frozenset = frozenset(loc_dict.keys())
        self.log(
            f"  Checking {len(defined_ideas)} ideas against {len(loc_keys)} loc keys..."
        )

        grouped: Dict[str, List[str]] = defaultdict(list)
        ideas_by_file: Dict[str, List[str]] = defaultdict(list)

        for idea_name in sorted(defined_ideas):
            _cat, name_override = defined_ideas[idea_name]
            primary_key = name_override if name_override else idea_name
            desc_key = primary_key + "_desc"

            missing: List[str] = []
            if primary_key not in loc_keys:
                missing.append(primary_key)
            if desc_key not in loc_keys:
                missing.append(desc_key)

            if not missing:
                continue

            file_key = _cat
            grouped[file_key].append(f"{idea_name}: {', '.join(missing)}")

        self._report_grouped(
            grouped,
            "✓ All idea localisation keys are defined",
            "Ideas missing localisation (grouped by category):",
            severity=Severity.WARNING,
            category="missing-idea-localisation",
            max_detail_per_file=3,
        )

    def run_validations(self):
        # Always parse all ideas — needed as the reference set even in staged mode
        defined_ideas, issues_by_file, ideas_by_file = self._parse_all_ideas()
        self.log(f"  Found {len(defined_ideas)} defined ideas total")

        if self.staged_only:
            staged_files_set = set(self.staged_files or [])
            staged_issues = {
                fp: issues
                for fp, issues in issues_by_file.items()
                if any(fp.endswith(sf) for sf in staged_files_set)
            }
            staged_ideas_by_file = {
                fp: ids
                for fp, ids in ideas_by_file.items()
                if any(fp.endswith(sf) for sf in staged_files_set)
            }
            if staged_issues:
                self.validate_idea_quality(staged_issues)
            else:
                self.log("  No staged idea files — skipping quality checks")
            self.validate_undefined_idea_refs(defined_ideas)
            ideas_for_consolidation = staged_ideas_by_file
        else:
            self.validate_undefined_idea_refs(defined_ideas)
            self.validate_idea_quality(issues_by_file)
            ideas_for_consolidation = ideas_by_file

        if self.suggest_consolidation:
            if ideas_for_consolidation:
                self.validate_loc_consolidation(defined_ideas, ideas_for_consolidation)
        else:
            self._log_section(
                "Skipping loc-consolidation suggestions (pass --suggest-consolidation to enable)"
            )

        if self.missing_loc:
            self.validate_missing_localisation(defined_ideas)
        else:
            self._log_section(
                "Skipping missing localisation check (pass --missing-loc to enable)"
            )


def _add_extra_args(parser):
    parser.add_argument(
        "--missing-loc",
        action="store_true",
        dest="missing_loc",
        help="Enable the missing localisation check (noisy until backlog is cleared)",
    )
    parser.add_argument(
        "--suggest-consolidation",
        action="store_true",
        dest="suggest_consolidation",
        help="Suggest `name = X` consolidation for sibling ideas with identical loc"
        " (advisory; emits warnings only, never errors)",
    )


if __name__ == "__main__":
    run_validator_main(
        Validator,
        "Validate ideas in Millennium Dawn mod",
        extra_args_fn=_add_extra_args,
    )
