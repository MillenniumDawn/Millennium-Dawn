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

EXTRA_SKIP_PATTERNS = ["FR_loc"]


def _should_skip(filename: str) -> bool:
    return should_skip_file(filename, extra_skip_patterns=EXTRA_SKIP_PATTERNS)


# --- Event parsing ---


def _strip_comments(text: str) -> str:
    """Remove lines that are entirely comments (starting with optional whitespace then #)."""
    return re.sub(r"^[ \t]*#.*$", "", text, flags=re.MULTILINE)


def parse_all_events(
    mod_path: str, lowercase: bool = False
) -> Tuple[List[str], Dict[str, str]]:
    events_path = str(Path(mod_path) / "events") + "/"
    pattern = re.compile(
        r"^(?:country_event|news_event) = \{(.*?)^\}", flags=re.DOTALL | re.MULTILINE
    )
    events = []
    paths = {}

    for filename in glob.iglob(events_path + "**/*.txt", recursive=True):
        text_file = _strip_comments(
            FileOpener.open_text_file(filename, lowercase=lowercase)
        )
        matches = pattern.findall(text_file)
        for match in matches:
            events.append(match)
            paths[match] = os.path.basename(filename)

    return events, paths


def process_file_for_events(args: Tuple[str, bool]) -> Tuple[List[str], Dict[str, str]]:
    filename, lowercase = args
    pattern = re.compile(
        r"^(?:country_event|news_event) = \{(.*?)^\}", flags=re.DOTALL | re.MULTILINE
    )
    events = []
    paths = {}

    text_file = _strip_comments(
        FileOpener.open_text_file(filename, lowercase=lowercase)
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
        events_path = str(Path(self.mod_path) / "events") + "/"
        if self.staged_files:
            files = [
                f for f in self.staged_files if f.endswith(".txt") and "events" in f
            ]
        else:
            files = list(glob.iglob(events_path + "**/*.txt", recursive=True))

        args_list = [(f, False) for f in files]
        with Pool(processes=self.workers) as pool:
            all_results = pool.map(process_file_for_events, args_list, chunksize=10)

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
                results.append(f"{eid} - {paths.get(event, 'unknown')}")

        self._report(
            results,
            "✓ All events have is_triggered_only = yes",
            "Events missing is_triggered_only = yes:",
        )

    def run_validations(self):
        self.validate_unsupported_title_desc()
        self.validate_missing_triggered_only()


if __name__ == "__main__":
    run_validator_main(Validator, "Validate events in Millennium Dawn mod")
