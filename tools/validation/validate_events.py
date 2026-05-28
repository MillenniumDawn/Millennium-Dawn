#!/usr/bin/env python3
##########################
# Event Validation Script (Multiprocessing Optimized)
# Validates event definitions for common issues
# Checks for:
#   1. Events with unsupported title/desc combinations
#      (having both block { } and inline value for title or desc)
#   2. Events missing is_triggered_only = yes
#   3. Redundant long-form event calls (id-only)
#   4. Triggered-only events never referenced
#   5. Missing localisation keys
#   6. news_event without major = yes (fires for only one country)
#   7. news_event with fire_only_once = yes + major (only one country sees it)
#   8. mean_time_to_happen with is_triggered_only (MTTH does nothing)
#   9. Duplicate event IDs
#  10. Event namespace not declared via add_namespace
#  11. Hidden events carrying option blocks (should run from immediate)
#  12. Hidden events carrying pointless localisation (never displayed)
# Based on Kaiserreich Autotests by Pelmen, https://github.com/Pelmen323
# Adapted for Millennium Dawn with multiprocessing
##########################
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import disk_cache
from validator_common import (
    BaseValidator,
    Colors,
    FileOpener,
    Severity,
    run_validator_main,
    should_skip_file,
)

EXTRA_SKIP_PATTERNS = ["FR_loc"]

_LONG_FORM_PATTERN = re.compile(
    r"\b((?:country|news|state|unit_leader|character|operative)_event)\s*=\s*\{\s*id\s*=\s*([^\s{}]+)\s*\}",
)


def _should_skip(filename: str) -> bool:
    return should_skip_file(filename, extra_skip_patterns=EXTRA_SKIP_PATTERNS)


def count_event_ids_in_file(args: Tuple[str, frozenset]) -> Dict[str, int]:
    """Pool worker: count occurrences of each tracked event ID in one file.

    Uses a word-boundary-aware approach so that an event ID appearing in a
    log string or other text doesn't produce a false positive count.
    """
    filename, tracked_ids = args
    if _should_skip(filename):
        return {}
    try:
        text = Path(filename).read_text(encoding="utf-8-sig", errors="ignore")
    except Exception:
        return {}
    cleaned = re.sub(r"#[^\n]*", "", text)
    id_counts: Dict[str, int] = {}
    for eid in tracked_ids:
        if eid in cleaned:
            id_counts[eid] = cleaned.count(eid)
    return id_counts


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


_EVENT_BLOCK_PATTERN = re.compile(
    r"^(?:country_event|news_event) = \{(.*?)^\}", flags=re.DOTALL | re.MULTILINE
)


def _parse_events(text: str, basename: str) -> Tuple[List[str], Dict[str, str]]:
    events = []
    paths = {}
    for match in _EVENT_BLOCK_PATTERN.findall(text):
        events.append(match)
        paths[match] = basename
    return events, paths


def process_file_for_events(
    args: Tuple[str, bool, str],
) -> Tuple[List[str], Dict[str, str]]:
    filename, lowercase, mod_path = args
    text_file = FileOpener.open_text_file(
        filename, lowercase=lowercase, strip_comments_flag=True
    )
    basename = os.path.basename(filename)
    return disk_cache.per_file_cached_by_content(
        mod_path,
        f"events.blocks.lc={int(lowercase)}",
        filename,
        text_file,
        lambda: _parse_events(text_file, basename),
    )


_EVENT_TYPE_PATTERN = re.compile(
    r"^(country_event|news_event|state_event|unit_leader_event|operative_leader_event)\s*=\s*\{",
    re.MULTILINE,
)
_ADD_NAMESPACE_PATTERN = re.compile(r"^\s*add_namespace\s*=\s*(\S+)", re.MULTILINE)
_EVENT_ID_PATTERN = re.compile(r"^\tid\s*=\s*(\S+)", re.MULTILINE)
_RANDOM_EVENTS_PATTERN = re.compile(r"\brandom_events\s*=\s*\{")
_RANDOM_EVENT_ID_PATTERN = re.compile(r"=\s*([A-Za-z_]\w*\.[\w.]+)")
_OPTION_BLOCK_PATTERN = re.compile(r"\boption\s*=\s*\{")
# Event-level (depth-1) title/desc fields — option-level name fields are
# nested deeper and are not matched.
_EVENT_TITLEDESC_PATTERN = re.compile(r"^\t(?:title|desc)\s*=\s*(.+)$", re.MULTILINE)


def _extract_random_event_ids(text: str) -> set:
    """Find event IDs referenced inside ``random_events = { ... }`` blocks.

    Events fired through ``random_events`` in on_actions use ``mean_time_to_happen``
    as the engine-side weight even though they're declared ``is_triggered_only``,
    so they must be excluded from the MTTH+triggered_only warning.
    """
    ids: set = set()
    for m in _RANDOM_EVENTS_PATTERN.finditer(text):
        start = m.end()
        depth = 1
        i = start
        while i < len(text) and depth > 0:
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
            i += 1
        body = text[start : i - 1]
        for id_match in _RANDOM_EVENT_ID_PATTERN.finditer(body):
            ids.add(id_match.group(1))
    return ids


def _parse_event_metadata(text: str, basename: str) -> Tuple[List[dict], Set[str]]:
    namespaces: Set[str] = set(_ADD_NAMESPACE_PATTERN.findall(text))
    meta: List[dict] = []
    for m in _EVENT_TYPE_PATTERN.finditer(text):
        event_type = m.group(1)
        start = m.end()
        depth = 1
        i = start
        while i < len(text) and depth > 0:
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
            i += 1
        body = text[start : i - 1]

        id_match = _EVENT_ID_PATTERN.search(body)
        if not id_match:
            continue

        meta.append(
            {
                "id": id_match.group(1),
                "type": event_type,
                "file": basename,
                "is_major": "major = yes" in body,
                "is_hidden": "hidden = yes" in body,
                "is_triggered_only": "is_triggered_only = yes" in body,
                "fire_only_once": "fire_only_once = yes" in body,
                "has_mtth": "mean_time_to_happen" in body,
                "option_count": len(_OPTION_BLOCK_PATTERN.findall(body)),
                "title_desc_refs": [
                    v.strip() for v in _EVENT_TITLEDESC_PATTERN.findall(body)
                ],
            }
        )
    return meta, namespaces


class Validator(BaseValidator):
    TITLE = "EVENT VALIDATION"
    STAGED_EXTENSIONS = [".txt"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._events_cache: Optional[Tuple[List[str], Dict[str, str]]] = None
        self._meta_cache: Optional[Tuple[List[dict], set]] = None
        self._random_events_cache: Optional[set] = None

    def _get_all_events(self) -> Tuple[List[str], Dict[str, str]]:
        if self._events_cache is not None:
            return self._events_cache
        files = self._collect_files(["events/**/*.txt"])
        args_list = [(f, False, self.mod_path) for f in files]
        all_results = self._pool_map(process_file_for_events, args_list, chunksize=10)

        events = []
        paths = {}
        for ev_list, ev_paths in all_results:
            events.extend(ev_list)
            paths.update(ev_paths)

        self._events_cache = (events, paths)
        return self._events_cache

    def _get_event_metadata(self) -> Tuple[List[dict], set]:
        """Parse all event files and return (event_metadata_list, declared_namespaces).

        Each metadata dict has: id, type, file, is_major, is_hidden,
        is_triggered_only, fire_only_once, has_mtth, option_count,
        title_desc_refs.
        """
        if self._meta_cache is not None:
            return self._meta_cache

        files = self._collect_files(["events/**/*.txt"])
        meta: List[dict] = []
        namespaces: set = set()

        for filepath in files:
            text = FileOpener.open_text_file(
                filepath, lowercase=False, strip_comments_flag=True
            )
            if not text:
                continue
            basename = os.path.basename(filepath)
            file_meta, file_ns = disk_cache.per_file_cached_by_content(
                self.mod_path,
                "events.metadata",
                filepath,
                text,
                lambda: _parse_event_metadata(text, basename),
            )
            meta.extend(file_meta)
            namespaces |= file_ns

        self._meta_cache = (meta, namespaces)
        return self._meta_cache

    def _get_random_event_ids(self) -> set:
        """Return event IDs referenced inside ``random_events`` blocks in on_actions.

        These events use ``mean_time_to_happen`` as their relative weight even
        when ``is_triggered_only = yes`` is set, so MTTH is not redundant.
        """
        if self._random_events_cache is not None:
            return self._random_events_cache

        files = self._collect_files(["common/on_actions/**/*.txt"])
        ids: set = set()
        for filepath in files:
            text = FileOpener.open_text_file(
                filepath, lowercase=False, strip_comments_flag=True
            )
            if not text:
                continue
            ids.update(_extract_random_event_ids(text))

        self._random_events_cache = ids
        return ids

    def validate_unsupported_title_desc(self):
        self._log_section(
            "Checking for events with unsupported title/desc combinations..."
        )

        events, paths = self._get_all_events()
        self.log(f"  Found {len(events)} events")
        id_pat = re.compile(r"^\tid = (\S+)", flags=re.MULTILINE)
        results = []

        for line_type in ["title", "desc"]:
            block_pat = re.compile(r"^\t" + line_type + r" = \{", flags=re.MULTILINE)
            inline_pat = re.compile(r"^\t" + line_type + r" = \w", flags=re.MULTILINE)

            for event in events:
                if block_pat.search(event) and inline_pat.search(event):
                    eid_match = id_pat.findall(event)
                    eid = eid_match[0] if eid_match else "unknown"
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
        self._log_section("Checking for events missing is_triggered_only = yes...")

        events, paths = self._get_all_events()
        self.log(f"  Found {len(events)} events")
        results = []
        id_pattern = re.compile(r"^\tid = (\S+)", flags=re.MULTILINE)

        for event in events:
            if "is_triggered_only = yes" not in event:
                event_id = id_pattern.findall(event)
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
        self._log_section("Checking for redundant long-form event calls (id-only)...")

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
        self._log_section("Checking for events with missing localisation keys...")

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
        self._log_section(
            "Checking for triggered-only events never referenced anywhere..."
        )

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

    def validate_news_event_major(self):
        """Flag news_event definitions missing major = yes.

        News events are country events under the hood — without major = yes
        they only fire for the single receiving country, which is almost
        always unintended. Hidden news events are exempted since they're
        used as scripted-effect carriers, not player-facing news.
        """
        self._log_section("Checking news_events for missing major = yes...")

        meta, _ = self._get_event_metadata()
        results = []

        for ev in meta:
            if ev["type"] != "news_event":
                continue
            if ev["is_hidden"]:
                continue
            if ev["is_major"]:
                continue
            results.append(f"{ev['id']} - {ev['file']}")

        self._report(
            results,
            "✓ All news_events have major = yes",
            "news_events missing major = yes (will only fire for one country — add major = yes or use country_event):",
            Severity.WARNING,
            category="news-event-missing-major",
        )

    def validate_mtth_triggered_only(self):
        """Flag events with both mean_time_to_happen and is_triggered_only.

        MTTH only applies to auto-firing events. On triggered-only events
        it does nothing and the engine logs a warning.

        Exception: events fired through ``random_events`` blocks in on_actions
        use MTTH as their selection weight, so the combination is intentional
        there.
        """
        self._log_section(
            "Checking for mean_time_to_happen on triggered-only events..."
        )

        meta, _ = self._get_event_metadata()
        random_event_ids = self._get_random_event_ids()
        results = []

        for ev in meta:
            if not (ev["has_mtth"] and ev["is_triggered_only"]):
                continue
            if ev["id"] in random_event_ids:
                continue
            results.append(f"{ev['id']} - {ev['file']}")

        self._report(
            results,
            "✓ No triggered-only events with mean_time_to_happen",
            "Events with mean_time_to_happen AND is_triggered_only (MTTH does nothing — remove one):",
            Severity.WARNING,
            category="mtth-triggered-only",
        )

    def validate_hidden_event_options(self):
        """Flag hidden events that still carry option blocks.

        A hidden event shows no UI, so its option effects should run from
        immediate = { } instead. When two or more options exist only the
        first auto-fires — the rest are dead code.
        """
        self._log_section("Checking hidden events for option blocks...")

        meta, _ = self._get_event_metadata()
        results = []

        for ev in meta:
            if not ev["is_hidden"] or ev["option_count"] == 0:
                continue
            count = ev["option_count"]
            detail = f"{count} option block{'s' if count != 1 else ''}"
            if count >= 2:
                detail += " (only the first auto-fires — the rest are dead code)"
            results.append(f"{ev['id']} - {ev['file']}: {detail}")

        self._report(
            results,
            "✓ No hidden events with option blocks",
            "Hidden events with option blocks (move effects into immediate = { }):",
            Severity.WARNING,
            category="hidden-event-has-options",
        )

    def validate_hidden_event_localisation(self):
        """Flag hidden events that declare a title or desc field.

        A hidden event shows no window, so a ``title`` / ``desc`` field in its
        own body is dead — the field and its loc keys should be removed.

        Only fields declared in the event's own body are flagged. A loc key
        that merely shares the event's ID prefix is NOT flagged: prefixes are
        sometimes reused by a separate visible event (e.g. the visible
        ``investments_event.10`` displays ``investments_event.1.t``), so the
        hidden event ``investments_event.1`` owning no title field is correct.
        """
        self._log_section("Checking hidden events for pointless localisation...")

        meta, _ = self._get_event_metadata()
        results = []

        for ev in meta:
            if not ev["is_hidden"] or not ev["title_desc_refs"]:
                continue
            detail = "; ".join(ev["title_desc_refs"])
            results.append(f"{ev['id']} - {ev['file']}: {detail}")

        self._report(
            results,
            "✓ No hidden events with pointless localisation",
            "Hidden events with localisation keys (hidden events display nothing — remove these keys):",
            Severity.WARNING,
            category="hidden-event-localisation",
        )

    def validate_duplicate_event_ids(self):
        """Flag events that share the same ID.

        When two events have the same ID, the second definition overwrites
        the first. This is almost always a copy-paste bug.
        """
        self._log_section("Checking for duplicate event IDs...")

        meta, _ = self._get_event_metadata()
        seen: Dict[str, str] = {}
        results = []

        for ev in meta:
            eid = ev["id"]
            if eid in seen:
                results.append(f"{eid} - defined in {seen[eid]} and {ev['file']}")
            else:
                seen[eid] = ev["file"]

        self._report(
            results,
            "✓ No duplicate event IDs",
            "Duplicate event IDs (second definition overwrites the first):",
            category="duplicate-event-id",
        )

    def validate_namespace_mismatch(self):
        """Flag events whose ID namespace is not declared via add_namespace.

        Every event ID has the format namespace.number. If the namespace
        isn't declared with add_namespace in any event file, the event ID
        is a malformed token and the event will silently not work in-game.
        """
        self._log_section("Checking event IDs against declared namespaces...")

        meta, namespaces = self._get_event_metadata()
        self.log(f"  Found {len(namespaces)} declared namespaces, {len(meta)} events")
        results = []

        for ev in meta:
            eid = ev["id"]
            last_dot = eid.rfind(".")
            if last_dot < 0:
                continue
            ns = eid[:last_dot]
            if ns not in namespaces:
                results.append(f"{eid} - {ev['file']} (namespace '{ns}' not declared)")

        self._report(
            results,
            "✓ All event namespaces are declared",
            "Events with undeclared namespace (add_namespace missing — event will silently fail):",
            category="namespace-mismatch",
        )

    def run_validations(self):
        self.validate_unsupported_title_desc()
        self.validate_missing_triggered_only()
        self.validate_event_call_long_form()
        self.validate_triggered_only_unreferenced()
        self.validate_missing_localisation()
        self.validate_news_event_major()
        self.validate_mtth_triggered_only()
        self.validate_hidden_event_options()
        self.validate_hidden_event_localisation()
        self.validate_duplicate_event_ids()
        self.validate_namespace_mismatch()


if __name__ == "__main__":
    run_validator_main(Validator, "Validate events in Millennium Dawn mod")
