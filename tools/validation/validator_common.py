#!/usr/bin/env python3
##########################
# Shared Validation Infrastructure
# Common classes, functions, and base validator used by all validation scripts
##########################
import glob
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass, field
from multiprocessing import Pool, cpu_count
from typing import Callable, Dict, List, Optional, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import disk_cache  # noqa: E402 — same-dir import after sys.path tweak above
from shared_utils import (
    DataCleaner,
    FileOpener,
    compute_line_offsets,
    create_validation_parser,
    find_line_number,
    get_staged_files,
    line_for_offset,
    log_message,
    print_timing_summary,
    run_validator_main,
    should_skip_file,
    strip_comments,
    timing_enabled,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


# Regex for meta_effect/meta_trigger template substitution patterns.
# Matches identifiers containing at least one [VAR] placeholder with a non-empty
# constant prefix (e.g. "set_leader_[IDEOLOGY]", "tooltip_EU_[EUXXX]_approve").
_META_TEMPLATE_RE = re.compile(
    r"(?<![/\"])\b([A-Za-z_][A-Za-z0-9_.]*(?:\[[A-Za-z_][A-Za-z0-9_]*\][A-Za-z0-9_.]*)+)"
)


def scan_meta_constructed_names(files, defined_names):
    """Return the subset of *defined_names* called via meta_effect/meta_trigger
    template substitution (e.g. ``set_leader_[IDEOLOGY] = yes``).

    For every file containing ``meta_effect`` or ``meta_trigger``, extracts
    identifier templates of the form ``prefix_[VAR]_suffix``, splits on ``[VAR]``
    segments, and matches any defined name whose lower-cased form starts with
    *prefix* and ends with *suffix*.
    """
    defined_lower = {n.lower(): n for n in defined_names}
    used = set()

    for filepath in files:
        try:
            with open(filepath, "r", encoding="utf-8-sig") as fh:
                content = fh.read()
        except Exception:
            continue

        if "meta_effect" not in content and "meta_trigger" not in content:
            continue

        content_clean = strip_comments(content)

        for m in _META_TEMPLATE_RE.finditer(content_clean):
            template = m.group(1)
            parts = re.split(r"\[[^\]]+\]", template)
            prefix = parts[0].lower()
            suffix = parts[-1].lower() if len(parts) > 1 else ""

            if not prefix and not suffix:
                continue

            for name_lower, name_orig in defined_lower.items():
                if name_orig in used:
                    continue
                if name_lower.startswith(prefix) and name_lower.endswith(suffix):
                    if len(name_lower) > len(prefix) + len(suffix):
                        used.add(name_orig)

    return used


# Log level from environment — controls output verbosity across all validators.
# Set MD_LOG_LEVEL=ERROR to see only errors, WARNING (default) for errors+Warnings,
# or INFO for full output (equivalent to the pre-MD_LOG_LEVEL behaviour).
_LOG_LEVEL = os.environ.get("MD_LOG_LEVEL", "WARNING").upper()
if _LOG_LEVEL == "ERROR":
    logging.basicConfig(level=logging.ERROR, format="%(levelname)s: %(message)s")
elif _LOG_LEVEL == "INFO":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
else:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")


class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class Severity:
    ERROR = "error"
    WARNING = "warning"


@dataclass
class Issue:
    severity: str
    category: str
    message: str
    file: str = ""
    line: int = 0

    def to_dict(self) -> dict:
        return {
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "file": self.file,
            "line": self.line,
        }

    def to_key(self) -> tuple:
        return (self.file, self.line, self.severity, self.category)


HOI4_BUILTIN_BLOCKS = frozenset(
    {
        "if",
        "else",
        "else_if",
        "limit",
        "AND",
        "OR",
        "NOT",
        "hidden_effect",
        "random_list",
        "tooltip",
        "custom_effect_tooltip",
        "custom_trigger_tooltip",
        "modifier",
        "random",
        "every_country",
        "random_country",
        "every_state",
        "random_state",
        "every_owned_state",
        "random_owned_state",
        "every_neighbor_country",
        "random_neighbor_country",
        "every_enemy_country",
        "random_enemy_country",
        "every_other_country",
        "random_other_country",
        "capital_scope",
        "owner",
        "controller",
        "ROOT",
        "PREV",
        "FROM",
        "country_event",
        "news_event",
        "state_event",
        "every_army_leader",
        "random_army_leader",
        "every_unit_leader",
        "random_unit_leader",
        "every_navy_leader",
        "random_navy_leader",
        "every_possible_country",
        "random_possible_country",
        "all_of",
        "any_of",
        "for_each_scope_loop",
        "while_loop_effect",
        "for_loop_effect",
        "effect_tooltip",
        "add_to_array",
        "remove_from_array",
        "overlord",
        "faction_leader",
        "any_country",
        "any_state",
        "any_owned_state",
        "any_neighbor_country",
        "any_enemy_country",
        "any_other_country",
        "any_allied_country",
        "any_country_with_original_tag",
        "any_army_leader",
        "any_navy_leader",
        "any_unit_leader",
        "any_possible_country",
        "every_allied_country",
        "random_allied_country",
        "every_occupied_country",
        "random_occupied_country",
        "any_occupied_country",
        "every_country_with_original_tag",
        "random_country_with_original_tag",
        "meta_effect",
        "meta_trigger",
    }
)


class BaseValidator:
    TITLE = "VALIDATION"
    STAGED_EXTENSIONS = [".txt"]

    def __init__(
        self,
        mod_path: str,
        output_file: Optional[str] = None,
        use_colors: bool = True,
        staged_only: bool = False,
        workers: int = None,
        **kwargs,
    ):
        if not mod_path.endswith(os.sep):
            mod_path += os.sep
        self.mod_path = mod_path
        self.errors_found = 0
        self.warnings_found = 0
        self.output_file = output_file
        self.use_colors = use_colors
        self.staged_only = staged_only
        self.workers = workers if workers else max(1, cpu_count() // 2)
        self.staged_files = None
        self.output_lines = []
        self._pool: Optional[Pool] = None
        self._regex_cache: Dict[str, re.Pattern] = {}
        self._line_offsets_cache: Dict[str, List[int]] = {}
        self._shared_cache: Dict[str, object] = {}
        self._issues: List[Issue] = []
        self._section_timings: List[Tuple[str, float]] = []
        self._section_start: Optional[float] = None
        self._section_title: str = ""
        self._show_timing = timing_enabled()

        if staged_only:
            self.staged_files = (
                get_staged_files(mod_path, extensions=self.STAGED_EXTENSIONS) or []
            )
            if not self.staged_files:
                logging.warning("No staged files found")

    def get_regex(self, pattern: str, flags: int = 0) -> re.Pattern:
        """Get a compiled regex pattern from cache or compile and cache it."""
        key = f"{pattern}:{flags}"
        if key not in self._regex_cache:
            self._regex_cache[key] = re.compile(pattern, flags)
        return self._regex_cache[key]

    def line_offsets(self, path: str, text: str) -> List[int]:
        # Pool workers must use compute_line_offsets() from shared_utils — this
        # cache only spans the main process.
        cached = self._line_offsets_cache.get(path)
        if cached is None:
            cached = compute_line_offsets(text)
            self._line_offsets_cache[path] = cached
        return cached

    def cached(self, key: str, factory_fn):
        # Pool workers don't see this cache; populate from the main process.
        if key not in self._shared_cache:
            self._shared_cache[key] = factory_fn()
        return self._shared_cache[key]

    def log(self, message: str, level: str = "info"):
        # Respect MD_LOG_LEVEL — skip messages below the configured threshold.
        if level == "info" and _LOG_LEVEL != "INFO":
            return
        if level == "warning" and _LOG_LEVEL == "ERROR":
            return

        display_msg = (
            message if self.use_colors else re.sub(r"\033\[[0-9;]+m", "", message)
        )
        if level == "info":
            logging.info(display_msg)
        elif level == "warning":
            logging.warning(display_msg)
        elif level == "error":
            logging.error(display_msg)
        file_msg = re.sub(r"\033\[[0-9;]+m", "", message)
        self.output_lines.append(file_msg)

    def _log_section(self, title: str):
        """Emit the standard section header and start timing this section.

        Each call closes the previous section's timer (if any) and starts a
        new one.  Call ``_finish_sections`` after all checks to close the last
        section and (when ``MD_TIMING`` is enabled) print a per-check timing
        summary to stderr.
        """
        if self._section_start is not None:
            elapsed = time.perf_counter() - self._section_start
            self._section_timings.append((self._section_title, elapsed))
        self._section_title = title
        self._section_start = time.perf_counter()
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}{title}{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

    def _finish_sections(self):
        """Close the last section timer and print a timing summary."""
        if self._section_start is not None:
            elapsed = time.perf_counter() - self._section_start
            self._section_timings.append((self._section_title, elapsed))
            self._section_start = None
        if self._show_timing and self._section_timings:
            print_timing_summary(self._section_timings)

    def save_output(self):
        if self.output_file and self.output_lines:
            try:
                with open(self.output_file, "w", encoding="utf-8") as f:
                    f.write("\n".join(self.output_lines))
                logging.info(f"Results saved to: {self.output_file}")
            except Exception as e:
                logging.error(f"Failed to write results to {self.output_file}: {e}")

        json_file = (
            os.path.splitext(self.output_file)[0] + ".json"
            if self.output_file
            else None
        )
        if json_file and self._issues:
            try:
                with open(json_file, "w", encoding="utf-8") as f:
                    f.write(self.get_issues_json())
                logging.info(f"JSON results saved to: {json_file}")
            except Exception as e:
                logging.error(f"Failed to serialize JSON to {json_file}: {e}")

    def add_issue(
        self, severity: str, category: str, message: str, file: str = "", line: int = 0
    ):
        """Add an issue to the internal list for later deduplication and reporting."""
        issue = Issue(
            severity=severity, category=category, message=message, file=file, line=line
        )
        self._issues.append(issue)
        if severity == Severity.ERROR:
            self.errors_found += 1
        elif severity == Severity.WARNING:
            self.warnings_found += 1

    def add_error(self, category: str, message: str, file: str = "", line: int = 0):
        """Convenience method to add an ERROR level issue."""
        self.add_issue(Severity.ERROR, category, message, file, line)

    def add_warning(self, category: str, message: str, file: str = "", line: int = 0):
        """Convenience method to add a WARNING level issue."""
        self.add_issue(Severity.WARNING, category, message, file, line)

    # Regex patterns for auto-extracting (file, line) from common result string
    # formats. Tried in order; first match wins. Patterns cover every format
    # currently emitted by the validators:
    #   - "path/to/file.ext:42 - something"           (standard colon form)
    #   - "path/to/file.ext:42: something"            (colon+colon variant)
    #   - "file.ext - line 42 - something"            (localisation dash form)
    #   - "file.ext, line 42, something"              (localisation comma form)
    #   - "id - path/to/file.ext - description"       (two-segment dash form,
    #                                                  captures file only)
    _LOC_PATTERNS = (
        re.compile(
            r"^(?P<file>[^\s:][^:\s]*?\.\w+):(?P<line>\d+)\s*[-:]\s*(?P<msg>.+)$"
        ),
        re.compile(
            r"^(?P<file>[^\s,]+?\.\w+)\s*-\s*line\s*(?P<line>\d+)\s*-\s*(?P<msg>.+)$"
        ),
        re.compile(r"^(?P<file>[^\s,]+?\.\w+),\s*line\s*(?P<line>\d+),\s*(?P<msg>.+)$"),
        re.compile(
            r"^(?P<prefix>[^\s].*?)\s*-\s*(?P<file>[^\s]+?\.\w+)\s*-\s*(?P<msg>.+)$"
        ),
    )

    @classmethod
    def _parse_result_location(cls, text: str) -> tuple:
        """Best-effort extraction of (message, file, line) from a result string.

        Returns the original string as the message when no known format matches.
        The ``line`` value is 0 when the pattern matched a file-only format.
        """
        for pat in cls._LOC_PATTERNS:
            m = pat.match(text)
            if not m:
                continue
            gd = m.groupdict()
            line = int(gd["line"]) if gd.get("line") else 0
            prefix = gd.get("prefix")
            msg = gd.get("msg", "")
            if prefix:
                msg = f"{prefix}: {msg}" if msg else prefix
            return msg, gd.get("file", ""), line
        return text, "", 0

    def _report(
        self,
        results: list,
        ok_msg: str,
        fail_msg: str,
        severity: str = Severity.ERROR,
        category: str = "",
    ):
        """Report results with specified severity level.

        Each entry in ``results`` may be:
          - ``str`` — legacy form. Auto-parsed via ``_parse_result_location``
            so standard ``path:line - msg`` strings get structured into an
            ``Issue`` with ``file`` / ``line`` populated.
          - ``(message, file, line)`` tuple — explicit structured form.
          - ``Issue`` instance — used directly.

        This is the single source of truth for counting and recording issues.
        Do NOT call add_error/add_warning separately for results passed here.
        """
        color = Colors.RED if severity == Severity.ERROR else Colors.YELLOW

        if len(results) > 0:
            self.log(
                f"{color if self.use_colors else ''}{fail_msg}{Colors.ENDC if self.use_colors else ''}",
                "error" if severity == Severity.ERROR else "warning",
            )
            for r in results:
                # Normalize into (display_text, Issue) so logging and storage
                # stay in sync regardless of which input shape was passed.
                if isinstance(r, Issue):
                    issue = r
                    if issue.file and issue.line > 0:
                        display_text = f"{issue.file}:{issue.line} - {issue.message}"
                    else:
                        display_text = issue.message
                elif isinstance(r, tuple):
                    # (message, file, line)
                    msg_t = str(r[0]) if len(r) > 0 else ""
                    file_t = str(r[1]) if len(r) > 1 else ""
                    line_t = int(r[2]) if len(r) > 2 and r[2] else 0
                    issue = Issue(
                        severity=severity,
                        category=category or "",
                        message=msg_t,
                        file=file_t,
                        line=line_t,
                    )
                    display_text = (
                        f"{file_t}:{line_t} - {msg_t}" if file_t and line_t else msg_t
                    )
                else:
                    text = str(r)
                    msg_p, file_p, line_p = self._parse_result_location(text)
                    issue = Issue(
                        severity=severity,
                        category=category or "",
                        message=msg_p,
                        file=file_p,
                        line=line_p,
                    )
                    display_text = text  # preserve original formatting in the log

                # Count by the issue's own severity so a pre-built WARNING Issue
                # passed via a severity=ERROR call doesn't corrupt the counters.
                actual_severity = issue.severity if isinstance(r, Issue) else severity
                self.log(
                    f"  {color if self.use_colors else ''}{display_text}{Colors.ENDC if self.use_colors else ''}",
                    "error" if actual_severity == Severity.ERROR else "warning",
                )
                if category:
                    self._issues.append(issue)
                if actual_severity == Severity.ERROR:
                    self.errors_found += 1
                else:
                    self.warnings_found += 1
            self.log(
                f"{color if self.use_colors else ''}{len(results)} issue(s) found{Colors.ENDC if self.use_colors else ''}",
                "error" if severity == Severity.ERROR else "warning",
            )
        else:
            self.log(
                f"{Colors.GREEN if self.use_colors else ''}{ok_msg}{Colors.ENDC if self.use_colors else ''}"
            )

    def get_issues_json(self) -> str:
        """Get issues as JSON string."""
        return json.dumps([issue.to_dict() for issue in self._issues], indent=2)

    def get_summary(self) -> dict:
        """Get validation summary as dict."""
        return {
            "title": self.TITLE,
            "errors": self.errors_found,
            "warnings": self.warnings_found,
            "issues": [issue.to_dict() for issue in self._issues],
        }

    def _basename_index(self, patterns: Tuple[str, ...]) -> Dict[str, List[str]]:
        # Without this cache, get_full_path() re-globs **/*.txt for every call —
        # validate_variables makes hundreds of those per run.
        key = "_basename_index:" + "|".join(patterns)
        existing = self._shared_cache.get(key)
        if existing is not None:
            return existing

        tracked: List[str] = []
        seen: Set[str] = set()
        for pattern in patterns:
            for filename in glob.iglob(
                os.path.join(self.mod_path, pattern), recursive=True
            ):
                if filename not in seen:
                    seen.add(filename)
                    tracked.append(filename)

        def _build():
            index: Dict[str, List[str]] = {}
            for filename in tracked:
                if should_skip_file(filename):
                    continue
                index.setdefault(os.path.basename(filename), []).append(filename)
            return index

        index = disk_cache.aggregate_cached(self.mod_path, key, tracked, _build)
        self._shared_cache[key] = index
        return index

    def get_full_path(
        self, basename: str, item: str, file_patterns: Optional[List[str]] = None
    ) -> Optional[str]:
        patterns = tuple(file_patterns) if file_patterns else ("**/*.txt",)
        index = self._basename_index(patterns)
        for filename in index.get(basename, ()):
            try:
                content = FileOpener.open_text_file(filename, lowercase=False)
                if item in content:
                    return filename
            except Exception:
                pass
        return None

    def _pool_map(self, func: Callable, args_list: List, chunksize: int = 50) -> List:
        # Falls back to sequential when workers == 1 so low-end machines don't
        # eat the Pool startup cost on a small staged commit.
        if self.workers == 1 or (self._pool is None and len(args_list) < 10):
            return [func(a) for a in args_list]
        if self._pool is None:
            raise RuntimeError("_pool_map called outside run_all_validations")
        return self._pool.map(func, args_list, chunksize=chunksize)

    def _collect_files(
        self,
        patterns: List[str],
        extra_skip: Optional[Callable[[str], bool]] = None,
        ignore_staged: bool = False,
    ) -> List[str]:
        """Collect mod files matching glob patterns, with staged-file support.

        In staged mode, filters self.staged_files by extension and a coarse
        directory hint derived from each pattern's first non-wildcard segment.
        In full mode, expands each pattern via glob.iglob relative to mod_path.
        Always applies should_skip_file; extra_skip adds validator-local filtering.

        Pass ``ignore_staged=True`` for cross-reference resolution passes that
        must always scan the entire repo regardless of staged mode — e.g.
        confirming a tag/idea/effect is defined somewhere even if its
        definition file isn't part of the current change set.
        """
        extensions = list(
            {os.path.splitext(p)[1] for p in patterns if os.path.splitext(p)[1]}
        ) or [".txt"]

        if self.staged_only and not ignore_staged:
            if not self.staged_files:
                return []

            # Build a precise directory-prefix hint per pattern by joining all
            # leading segments before the first wildcard. For
            # `common/ai_templates/*.txt` the hint becomes `common/ai_templates/`,
            # so an unrelated staged file in `common/national_focus/` won't match.
            dir_hints = []
            for p in patterns:
                segments = p.replace("\\", "/").split("/")
                leading = []
                for s in segments:
                    if "*" in s:
                        break
                    leading.append(s)
                # If the pattern has no wildcard (exact file), the full path
                # is the hint. Otherwise the directory prefix followed by `/`.
                if leading == segments:
                    dir_hints.append("/".join(leading))
                else:
                    dir_hints.append("/".join(leading) + "/" if leading else "")

            def _matches_hint(path: str, hint: str) -> bool:
                if hint == "":
                    return True
                normalized = path.replace("\\", "/")
                # Exact-file hint (no trailing slash): require exact suffix match
                if not hint.endswith("/"):
                    return normalized == hint or normalized.endswith("/" + hint)
                # Directory-prefix hint: path must start with the prefix (possibly
                # after a leading mod-path component)
                return hint in normalized and (
                    normalized.startswith(hint) or ("/" + hint) in normalized
                )

            files = [
                f
                for f in self.staged_files
                if any(f.endswith(ext) for ext in extensions)
                and any(_matches_hint(f, hint) for hint in dir_hints)
            ]
        else:
            seen: Set[str] = set()
            files = []
            for pattern in patterns:
                for f in glob.iglob(
                    os.path.join(self.mod_path, pattern), recursive=True
                ):
                    if f not in seen:
                        seen.add(f)
                        files.append(f)

        result = [f for f in files if not should_skip_file(f)]
        if extra_skip is not None:
            result = [f for f in result if not extra_skip(f)]
        return result

    def _load_localisation_keys(self) -> frozenset:
        """Load all defined keys from English localisation yml files."""
        yml_files = self._collect_files(["localisation/english/**/*.yml"])
        key_pattern = re.compile(r"^[ \t]*([\w.\-]+)\s*:", re.MULTILINE)
        all_keys: set = set()
        for filepath in yml_files:
            try:
                with open(filepath, encoding="utf-8-sig", errors="ignore") as f:
                    text = f.read()
            except Exception:
                continue
            all_keys.update(key_pattern.findall(text))
        return frozenset(all_keys)

    def run_validations(self):
        raise NotImplementedError("Subclasses must implement run_validations()")

    def run_all_validations(self):
        self.log(f"\n{'#'*80}")
        self.log(
            f"{Colors.BOLD if self.use_colors else ''}MILLENNIUM DAWN {self.TITLE}{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'#'*80}")
        self.log(f"Mod path: {self.mod_path}")
        self.log(f"Worker processes: {self.workers}")
        if self.staged_only:
            self.log(
                f"{Colors.CYAN if self.use_colors else ''}Mode: Git staged files only{Colors.ENDC if self.use_colors else ''}"
            )
        if self.output_file:
            self.log(f"Output file: {self.output_file}")

        if self.workers > 1:
            self._pool = Pool(processes=self.workers)
        try:
            self.run_validations()
        finally:
            self._finish_sections()
            if self._pool is not None:
                self._pool.terminate()
                self._pool.join()
                self._pool = None

        self.log(f"\n{'#'*80}")
        if self.errors_found == 0 and self.warnings_found == 0:
            self.log(
                f"{Colors.GREEN if self.use_colors else ''}✓ VALIDATION COMPLETE - NO ISSUES FOUND{Colors.ENDC if self.use_colors else ''}"
            )
        else:
            error_msg = f"✗ VALIDATION COMPLETE"
            if self.errors_found > 0:
                error_msg += f" - {self.errors_found} ERROR(S)"
            if self.warnings_found > 0:
                error_msg += f" - {self.warnings_found} WARNING(S)"
            self.log(
                f"{Colors.RED if self.use_colors else ''}{error_msg}{Colors.ENDC if self.use_colors else ''}",
                "error",
            )
        self.log(f"{'#'*80}\n")

        self.save_output()
        return self.errors_found
