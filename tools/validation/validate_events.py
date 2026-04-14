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
from typing import Dict, List, Tuple

from validator_common import (
    BaseValidator,
    Colors,
    FileOpener,
    Severity,
    run_validator_main,
    should_skip_file,
)

EXTRA_SKIP_PATTERNS = ["FR_loc"]


def _should_skip(filename: str) -> bool:
    return should_skip_file(filename, extra_skip_patterns=EXTRA_SKIP_PATTERNS)


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

    def _get_all_events(self) -> Tuple[List[str], Dict[str, str]]:
        files = self._collect_files(["events/**/*.txt"])
        args_list = [(f, False) for f in files]
        all_results = self._pool_map(process_file_for_events, args_list, chunksize=10)

        events = []
        paths = {}
        for ev_list, ev_paths in all_results:
            events.extend(ev_list)
            paths.update(ev_paths)

        return events, paths

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

        # Match `(country|news|state|unit_leader|character)_event = { id = X }` where
        # the block contains ONLY the id assignment.
        pattern = re.compile(
            r"\b((?:country|news|state|unit_leader|character|operative)_event)\s*=\s*\{\s*id\s*=\s*([^\s{}]+)\s*\}",
        )

        results = []
        seen = set()
        for ext_dir in ("common", "events", "history"):
            base = Path(self.mod_path) / ext_dir
            if not base.exists():
                continue
            for fp in base.rglob("*.txt"):
                if _should_skip(str(fp)):
                    continue
                try:
                    text = fp.read_text(encoding="utf-8-sig", errors="ignore")
                except Exception:
                    continue
                # Strip line comments to avoid false positives
                cleaned = re.sub(r"#[^\n]*", "", text)
                for m in pattern.finditer(cleaned):
                    line = cleaned[: m.start()].count("\n") + 1
                    rel = fp.relative_to(self.mod_path)
                    key = (str(rel), line, m.group(1), m.group(2))
                    if key in seen:
                        continue
                    seen.add(key)
                    results.append(
                        f"{rel}:{line} - {m.group(1)} = {{ id = {m.group(2)} }} → use shorthand `{m.group(1)} = {m.group(2)}`"
                    )

        self._report(
            results,
            "✓ No redundant long-form event calls found",
            "Long-form event calls with only id (use shorthand instead):",
        )

    def run_validations(self):
        self.validate_unsupported_title_desc()
        self.validate_missing_triggered_only()
        self.validate_event_call_long_form()


if __name__ == "__main__":
    run_validator_main(Validator, "Validate events in Millennium Dawn mod")
