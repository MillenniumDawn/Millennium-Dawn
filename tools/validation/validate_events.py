#!/usr/bin/env python3
##########################
# Event Validation Script (Multiprocessing Optimized)
# Validates event definitions for common issues
# Checks for:
#   1. Events with unsupported title/desc combinations
#      (having both block { } and inline value for title or desc)
#   2. Events missing is_triggered_only = yes
# Based on Kaiserreich Autotests by Pelmen, https://github.com/Pelmen323
# Adapted for Millennium Dawn with multiprocessing
##########################
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from validator_common import (
    BaseValidator,
    Colors,
    FileOpener,
    Severity,
    run_validator_main,
    should_skip_file,
)

EXTRA_SKIP_PATTERNS = ["FR_loc"]

# Pre-compiled pattern for the long-form check (used in pool worker)
_LONG_FORM_PATTERN = re.compile(
    r"\b((?:country|news|state|unit_leader|character|operative)_event)\s*=\s*\{\s*id\s*=\s*([^\s{}]+)\s*\}",
)


def _should_skip(filename: str) -> bool:
    return should_skip_file(filename, extra_skip_patterns=EXTRA_SKIP_PATTERNS)


def count_event_ids_in_file(args: Tuple[str, frozenset]) -> Dict[str, int]:
    """Pool worker: count occurrences of each tracked event ID in one file."""
    filename, tracked_ids = args
    if _should_skip(filename):
        return {}
    try:
        text = Path(filename).read_text(encoding="utf-8-sig", errors="ignore")
    except Exception:
        return {}
    cleaned = re.sub(r"#[^\n]*", "", text)
    return {eid: cleaned.count(eid) for eid in tracked_ids if eid in cleaned}


def process_txt_for_long_form_events(args: Tuple[str, str]) -> List[str]:
    """Pool worker: find id-only long-form event calls in one .txt file."""
    filename, mod_path = args
    if _should_skip(filename):
        return []
    try:
        text = Path(filename).read_text(encoding="utf-8-sig", errors="ignore")
    except Exception:
        return []
    cleaned = re.sub(r"#[^\n]*", "", text)
    results = []
    seen = set()
    for m in _LONG_FORM_PATTERN.finditer(cleaned):
        line = cleaned[: m.start()].count("\n") + 1
        rel = os.path.relpath(filename, mod_path)
        key = (rel, line, m.group(1), m.group(2))
        if key in seen:
            continue
        seen.add(key)
        results.append(
            f"{rel}:{line} - {m.group(1)} = {{ id = {m.group(2)} }} → use shorthand `{m.group(1)} = {m.group(2)}`"
        )
    return results


# --- Event parsing ---


def process_file_for_events(args: Tuple[str, bool]) -> Tuple[List[str], Dict[str, str]]:
    filename, lowercase = args
    pattern = re.compile(
        r"^(?:country_event|news_event) = \{(.*?)^\}", flags=re.DOTALL | re.MULTILINE
    )
    events = []
    paths = {}

    text_file = FileOpener.open_text_file(
        filename, lowercase=lowercase, strip_comments_flag=True
    )
    matches = pattern.findall(text_file)
    for match in matches:
        events.append(match)
        paths[match] = os.path.basename(filename)

    return events, paths


class Validator(BaseValidator):
    TITLE = "EVENT VALIDATION"
    STAGED_EXTENSIONS = [".txt"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._events_cache: Optional[Tuple[List[str], Dict[str, str]]] = None

    def _get_all_events(self) -> Tuple[List[str], Dict[str, str]]:
        if self._events_cache is not None:
            return self._events_cache
        files = self._collect_files(["events/**/*.txt"])
        args_list = [(f, False) for f in files]
        all_results = self._pool_map(process_file_for_events, args_list, chunksize=10)

        events = []
        paths = {}
        for ev_list, ev_paths in all_results:
            events.extend(ev_list)
            paths.update(ev_paths)

        self._events_cache = (events, paths)
        return self._events_cache

    def validate_unsupported_title_desc(self):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking for events with unsupported title/desc combinations...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        events, paths = self._get_all_events()
        self.log(f"  Found {len(events)} events")
        pattern_id = re.compile(r"^\tid = (\S+)", flags=re.MULTILINE)
        results = []

        for line_type in ["title", "desc"]:
            pattern_block = r"^\t" + line_type + r" = \{"
            pattern_inline = r"^\t" + line_type + r" = \w"

            for event in events:
                has_block = (
                    len(re.findall(pattern_block, event, flags=re.MULTILINE)) > 0
                )
                has_inline = (
                    len(re.findall(pattern_inline, event, flags=re.MULTILINE)) > 0
                )

                if has_block and has_inline:
                    event_id = pattern_id.findall(event)
                    eid = event_id[0] if event_id else "unknown"
                    results.append(
                        f"{eid} - {paths.get(event, 'unknown')} - invalid {line_type} (has both block and inline forms)"
                    )

        self._report(
            results,
            "✓ No unsupported title/desc combinations",
            "Events with invalid title/desc combinations (both block and inline forms):",
            Severity.ERROR,
            category="invalid-title-desc",
        )

    def validate_missing_triggered_only(self):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking for events missing is_triggered_only = yes...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        events, paths = self._get_all_events()
        self.log(f"  Found {len(events)} events")
        pattern_id = re.compile(r"^\tid = (\S+)", flags=re.MULTILINE)

        results = []
        for event in events:
            if "is_triggered_only = yes" not in event:
                event_id = pattern_id.findall(event)
                eid = event_id[0] if event_id else "unknown"
                filename = paths.get(event, "unknown")
                results.append(f"{eid} - {filename}")

        self._report(
            results,
            "✓ All events have is_triggered_only = yes",
            "Events missing is_triggered_only = yes:",
            Severity.ERROR,
            category="missing-triggered-only",
        )

    def validate_event_call_long_form(self):
        """Flag ``country_event = { id = X }`` (or ``news_event``/``state_event``)
        where the only argument is ``id``. Should use the shorthand
        ``country_event = X``.

        Scans all .txt files in the mod, not just events/, since events are
        called from focuses, decisions, scripted effects, etc.
        """
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking for redundant long-form event calls (id-only)...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        txt_files = self._collect_files(
            ["common/**/*.txt", "events/**/*.txt", "history/**/*.txt"]
        )
        args_list = [(f, self.mod_path) for f in txt_files]
        all_results = self._pool_map(
            process_txt_for_long_form_events, args_list, chunksize=30
        )
        results = [r for file_res in all_results for r in file_res]

        self._report(
            results,
            "✓ No redundant long-form event calls found",
            "Long-form event calls with only id (use shorthand instead):",
        )

    def validate_missing_localisation(self):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking for events with missing localisation keys...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        events, paths = self._get_all_events()
        loc_keys = self._load_localisation_keys()
        self.log(f"  Found {len(events)} events, {len(loc_keys)} localisation keys")

        # Extracts values from title/desc/name fields that look like loc keys (contain a dot).
        # Covers simple form (title = foo.1.t) and block form (triggered_desc { desc = foo.1.t }).
        ref_pattern = re.compile(
            r"\b(?:title|desc|name)\s*=\s*([\w][\w.]*)", re.MULTILINE
        )
        pattern_id = re.compile(r"^\tid = (\S+)", flags=re.MULTILINE)

        results = []
        for event in events:
            eid_matches = pattern_id.findall(event)
            eid = eid_matches[0] if eid_matches else "unknown"
            filename = paths.get(event, "unknown")

            loc_refs = [k for k in ref_pattern.findall(event) if "." in k]
            missing = [k for k in loc_refs if k not in loc_keys]
            for key in missing:
                results.append(f"{eid} - {filename}: missing loc key '{key}'")

        self._report(
            results,
            "✓ All event localisation keys are defined",
            "Events with missing localisation keys:",
            Severity.WARNING,
            category="missing-event-localisation",
        )

    def validate_triggered_only_unreferenced(self):
        self.log(f"\n{'='*80}")
        self.log(
            f"{Colors.CYAN if self.use_colors else ''}Checking for triggered-only events never referenced anywhere...{Colors.ENDC if self.use_colors else ''}"
        )
        self.log(f"{'='*80}")

        events, paths = self._get_all_events()
        pattern_id = re.compile(r"^\tid = (\S+)", flags=re.MULTILINE)

        triggered_only_ids: Dict[str, str] = {}
        for event in events:
            if "is_triggered_only = yes" in event:
                matches = pattern_id.findall(event)
                if matches:
                    eid = matches[0]
                    triggered_only_ids[eid] = paths.get(event, "unknown")

        self.log(
            f"  Found {len(triggered_only_ids)} triggered-only events — scanning for references..."
        )

        txt_files = self._collect_files(
            ["common/**/*.txt", "events/**/*.txt", "history/**/*.txt"]
        )
        tracked = frozenset(triggered_only_ids.keys())
        args_list = [(f, tracked) for f in txt_files]
        all_counts = self._pool_map(count_event_ids_in_file, args_list, chunksize=30)

        total_counts: Dict[str, int] = {eid: 0 for eid in tracked}
        for file_counts in all_counts:
            for eid, count in file_counts.items():
                total_counts[eid] = total_counts.get(eid, 0) + count

        # The definition itself contributes 1 occurrence (id = X inside the event block).
        # Anything > 1 means it's referenced somewhere else.
        results = []
        for eid in sorted(triggered_only_ids):
            if total_counts.get(eid, 0) <= 1:
                results.append(f"{eid} - {triggered_only_ids[eid]}")

        self._report(
            results,
            "✓ All triggered-only events are referenced somewhere",
            "Triggered-only events with no references found:",
            Severity.WARNING,
            category="unreferenced-triggered-only",
        )

    def run_validations(self):
        self.validate_unsupported_title_desc()
        self.validate_missing_triggered_only()
        self.validate_event_call_long_form()
        self.validate_triggered_only_unreferenced()
        self.validate_missing_localisation()


if __name__ == "__main__":
    run_validator_main(Validator, "Validate events in Millennium Dawn mod")
