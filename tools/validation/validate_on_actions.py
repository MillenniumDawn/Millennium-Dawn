#!/usr/bin/env python3
##########################
# on_actions Reference Validation Script
# Validates event references in on_actions files against defined event IDs
# Checks for:
#   1. Missing event references (event fired in on_actions but not defined)
#   2. Non-triggered-only events referenced in on_actions (MTTH may double-fire)
#   3. Duplicate event references within the same on_action trigger block
##########################
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from validator_common import (
    BaseValidator,
    FileOpener,
    Severity,
    run_validator_main,
    should_skip_file,
)

# ---------------------------------------------------------------------------
# Regex patterns (module-level for pool workers)
# ---------------------------------------------------------------------------

# Declared namespaces: add_namespace = foo
_ADD_NAMESPACE_RE = re.compile(r"^\s*add_namespace\s*=\s*(\S+)", re.MULTILINE)

# Top-level event block openers (country_event, news_event, state_event, …).
# Allow optional leading whitespace — some files indent the top-level blocks
# with a tab (e.g. agricultural_events.txt).
_EVENT_BLOCK_OPEN_RE = re.compile(
    r"^[ \t]*(country_event|news_event|state_event|unit_leader_event|operative_leader_event)\s*=\s*\{",
    re.MULTILINE,
)

# id = XXX.N inside an event block body
_EVENT_ID_IN_BODY_RE = re.compile(r"^\s*id\s*=\s*(\S+)", re.MULTILINE)

# is_triggered_only inside an event block body
_TRIGGERED_ONLY_RE = re.compile(r"\bis_triggered_only\s*=\s*yes\b")

# random_events = { ... } block opener
_RANDOM_EVENTS_BLOCK_RE = re.compile(r"\brandom_events\s*=\s*\{")

# numeric weight = event_id inside a random_events body (e.g. `50 = econvent.1`)
# The event ID must contain a dot.
_RANDOM_EVENT_ENTRY_RE = re.compile(r"\b\d+\s*=\s*([A-Za-z_]\w*\.[A-Za-z0-9_.]+)")

# Long-form event call: country_event = { id = foo.1 ... }
_LONG_FORM_EVENT_RE = re.compile(
    r"\b(?:country_event|news_event|state_event|unit_leader_event|operative_leader_event)"
    r"\s*=\s*\{\s*id\s*=\s*([A-Za-z_]\w*\.[A-Za-z0-9_.]+)",
    re.DOTALL,
)

# Short-form event call: country_event = foo.1
_SHORT_FORM_EVENT_RE = re.compile(
    r"\b(?:country_event|news_event|state_event|unit_leader_event|operative_leader_event)"
    r"\s*=\s*([A-Za-z_]\w*\.[A-Za-z0-9_.]+)"
)


# ---------------------------------------------------------------------------
# Pool workers (module-level so multiprocessing can pickle them)
# ---------------------------------------------------------------------------


def _scan_event_file(filepath: str) -> Tuple[Set[str], Set[str]]:
    """Return (defined_ids, triggered_only_ids) from a single events/*.txt file."""
    defined_ids: Set[str] = set()
    triggered_only_ids: Set[str] = set()

    try:
        text = Path(filepath).read_text(encoding="utf-8-sig", errors="ignore")
    except Exception:
        return defined_ids, triggered_only_ids

    # Strip comments
    text = re.sub(r"#[^\n]*", "", text)

    for m in _EVENT_BLOCK_OPEN_RE.finditer(text):
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

        id_match = _EVENT_ID_IN_BODY_RE.search(body)
        if not id_match:
            continue
        eid = id_match.group(1)
        defined_ids.add(eid)
        if _TRIGGERED_ONLY_RE.search(body):
            triggered_only_ids.add(eid)

    return defined_ids, triggered_only_ids


def _extract_random_events_ids(text: str) -> Set[str]:
    """Return all event IDs found inside random_events = { ... } blocks."""
    ids: Set[str] = set()
    for m in _RANDOM_EVENTS_BLOCK_RE.finditer(text):
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
        for entry in _RANDOM_EVENT_ENTRY_RE.finditer(body):
            ids.add(entry.group(1))
    return ids


def _scan_on_action_block(text: str, block_name: str, filepath: str) -> Tuple[
    List[Tuple[str, str, int]],  # (event_id, on_action_name, line_number)
    List[Tuple[str, str, int]],  # duplicates: (event_id, on_action_name, line_number)
]:
    """Extract all event references from a single on_action trigger block body.

    Returns (references, duplicates) where each entry is
    (event_id, block_name, line_number_in_file).
    """
    refs: List[Tuple[str, str, int]] = []
    duplicates: List[Tuple[str, str, int]] = []
    seen: Set[str] = set()

    def _line_of(pos: int) -> int:
        return text[:pos].count("\n") + 1

    # Collect random_events entries
    for m in _RANDOM_EVENTS_BLOCK_RE.finditer(text):
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
        body_offset = start
        for entry in _RANDOM_EVENT_ENTRY_RE.finditer(body):
            eid = entry.group(1)
            line = _line_of(body_offset + entry.start())
            if eid in seen:
                duplicates.append((eid, block_name, line))
            else:
                seen.add(eid)
                refs.append((eid, block_name, line))

    # Collect long-form calls
    for m in _LONG_FORM_EVENT_RE.finditer(text):
        eid = m.group(1)
        line = _line_of(m.start())
        if eid in seen:
            duplicates.append((eid, block_name, line))
        else:
            seen.add(eid)
            refs.append((eid, block_name, line))

    # Collect short-form calls — but only when the match isn't already inside a
    # long-form call (the long-form pattern consumes the id= part, so a
    # short-form match immediately following an event keyword and = is the
    # actual token we want).
    long_form_spans = {(m.start(), m.end()) for m in _LONG_FORM_EVENT_RE.finditer(text)}

    def _in_long_form(pos: int) -> bool:
        for start, end in long_form_spans:
            if start <= pos < end:
                return True
        return False

    for m in _SHORT_FORM_EVENT_RE.finditer(text):
        if _in_long_form(m.start()):
            continue
        eid = m.group(1)
        line = _line_of(m.start())
        if eid in seen:
            duplicates.append((eid, block_name, line))
        else:
            seen.add(eid)
            refs.append((eid, block_name, line))

    return refs, duplicates


def _parse_on_actions_file(
    filepath: str,
) -> Tuple[
    List[Tuple[str, str, int, str]],  # (event_id, block_name, line, relpath)
    List[Tuple[str, str, int, str]],  # duplicates
]:
    """Parse a single on_actions file and return all event references."""
    all_refs: List[Tuple[str, str, int, str]] = []
    all_dupes: List[Tuple[str, str, int, str]] = []

    try:
        text = Path(filepath).read_text(encoding="utf-8-sig", errors="ignore")
    except Exception:
        return all_refs, all_dupes

    relpath = filepath
    # Strip comments
    text_clean = re.sub(r"#[^\n]*", "", text)

    # Locate the outer on_actions = { ... } wrapper and iterate on_action blocks
    outer_re = re.compile(r"\bon_actions\s*=\s*\{")
    trigger_open_re = re.compile(r"\b([A-Za-z_]\w*)\s*=\s*\{")

    for outer_m in outer_re.finditer(text_clean):
        # Find the body of the on_actions block
        start = outer_m.end()
        depth = 1
        i = start
        while i < len(text_clean) and depth > 0:
            if text_clean[i] == "{":
                depth += 1
            elif text_clean[i] == "}":
                depth -= 1
            i += 1
        outer_body = text_clean[start : i - 1]
        outer_offset = start

        # Each top-level key inside on_actions is an on_action trigger name
        pos = 0
        while pos < len(outer_body):
            tm = trigger_open_re.search(outer_body, pos)
            if not tm:
                break
            block_name = tm.group(1)
            # Skip known HOI4 sub-blocks that aren't on_action names
            if block_name in (
                "effect",
                "random_events",
                "if",
                "else",
                "else_if",
                "limit",
                "AND",
                "OR",
                "NOT",
                "hidden_effect",
                "random_list",
                "modifier",
            ):
                pos = tm.end()
                continue

            # Extract this trigger block's body
            bstart = tm.end()
            bdepth = 1
            bi = bstart
            while bi < len(outer_body) and bdepth > 0:
                if outer_body[bi] == "{":
                    bdepth += 1
                elif outer_body[bi] == "}":
                    bdepth -= 1
                bi += 1
            block_body = outer_body[bstart : bi - 1]

            refs, dupes = _scan_on_action_block(
                block_body,
                block_name,
                filepath,
            )
            # Adjust line numbers: outer_offset accounts for the on_actions = { header,
            # and bstart for the trigger block's own header
            body_line_base = text_clean[: outer_offset + bstart].count("\n")
            for eid, bname, lno in refs:
                all_refs.append((eid, bname, body_line_base + lno, relpath))
            for eid, bname, lno in dupes:
                all_dupes.append((eid, bname, body_line_base + lno, relpath))

            pos = bi

    return all_refs, all_dupes


class Validator(BaseValidator):
    TITLE = "ON_ACTIONS REFERENCE VALIDATION"
    STAGED_EXTENSIONS = [".txt"]

    def __init__(self, mod_path: str, **kwargs):
        super().__init__(mod_path, **kwargs)
        self._defined_ids_cache: Optional[Set[str]] = None
        self._triggered_only_cache: Optional[Set[str]] = None

    # ------------------------------------------------------------------
    # Data collection
    # ------------------------------------------------------------------

    def _get_defined_event_ids(self) -> Tuple[Set[str], Set[str]]:
        """Return (all_defined_ids, triggered_only_ids) from the full events tree.

        Always scans the full repo (ignore_staged=True) so that on_actions
        references can be resolved even when the event definition file itself
        is not staged.
        """
        if self._defined_ids_cache is not None:
            return self._defined_ids_cache, self._triggered_only_cache

        event_files = self._collect_files(["events/**/*.txt"], ignore_staged=True)
        results = self._pool_map(_scan_event_file, event_files, chunksize=20)

        all_defined: Set[str] = set()
        all_triggered: Set[str] = set()
        for defined, triggered in results:
            all_defined.update(defined)
            all_triggered.update(triggered)

        self._defined_ids_cache = all_defined
        self._triggered_only_cache = all_triggered
        return all_defined, all_triggered

    def _get_on_actions_refs(self) -> Tuple[
        List[Tuple[str, str, int, str]],
        List[Tuple[str, str, int, str]],
    ]:
        """Return (all_references, all_duplicates) from on_actions files.

        In staged mode, only scans staged on_actions files.
        """
        on_actions_files = self._collect_files(["common/on_actions/**/*.txt"])
        all_refs: List[Tuple[str, str, int, str]] = []
        all_dupes: List[Tuple[str, str, int, str]] = []

        results = self._pool_map(_parse_on_actions_file, on_actions_files, chunksize=10)
        for refs, dupes in results:
            all_refs.extend(refs)
            all_dupes.extend(dupes)

        return all_refs, all_dupes

    # ------------------------------------------------------------------
    # Checks
    # ------------------------------------------------------------------

    def validate_missing_event_refs(self):
        """Report event IDs referenced in on_actions that are not defined anywhere."""
        self._log_section("Checking for missing event references in on_actions...")

        all_defined, _ = self._get_defined_event_ids()
        all_refs, _ = self._get_on_actions_refs()
        self.log(
            f"  Defined event IDs: {len(all_defined)}, on_actions references: {len(all_refs)}"
        )

        results = []
        for eid, block_name, line, filepath in sorted(all_refs, key=lambda x: x[2]):
            if eid not in all_defined:
                relpath = os.path.relpath(filepath, self.mod_path)
                results.append(
                    (
                        f"Undefined event '{eid}' referenced in on_action '{block_name}'",
                        relpath,
                        line,
                    )
                )

        self._report(
            results,
            "All event references in on_actions are defined",
            "on_actions references to undefined events (event will silently never fire):",
            Severity.ERROR,
            category="missing-event-ref",
        )

    def validate_non_triggered_on_action_refs(self):
        """Warn when an on_actions reference points to an event without is_triggered_only.

        Such events have a mean_time_to_happen block of their own, so they can
        fire both on their MTTH schedule and from on_actions — almost always
        unintended. Add is_triggered_only = yes to the event if on_actions is
        the only intended trigger, or remove the on_actions reference.
        """
        self._log_section(
            "Checking for on_actions references to non-triggered-only events..."
        )

        all_defined, triggered_only = self._get_defined_event_ids()
        all_refs, _ = self._get_on_actions_refs()

        results = []
        for eid, block_name, line, filepath in sorted(all_refs, key=lambda x: x[2]):
            if eid not in all_defined:
                continue  # already reported by validate_missing_event_refs
            if eid in triggered_only:
                continue
            relpath = os.path.relpath(filepath, self.mod_path)
            results.append(
                (
                    f"Event '{eid}' in on_action '{block_name}' lacks is_triggered_only = yes"
                    " (may also fire on its own MTTH)",
                    relpath,
                    line,
                )
            )

        self._report(
            results,
            "All on_actions event references point to triggered-only events",
            "on_actions references to events without is_triggered_only = yes"
            " (event may double-fire from MTTH):",
            Severity.WARNING,
            category="non-triggered-on-action",
        )

    def validate_duplicate_event_refs(self):
        """Warn when the same event ID appears more than once in the same on_action block."""
        self._log_section(
            "Checking for duplicate event references within on_action blocks..."
        )

        _, all_dupes = self._get_on_actions_refs()

        results = []
        for eid, block_name, line, filepath in sorted(all_dupes, key=lambda x: x[2]):
            relpath = os.path.relpath(filepath, self.mod_path)
            results.append(
                (
                    f"Duplicate event reference '{eid}' in on_action '{block_name}'",
                    relpath,
                    line,
                )
            )

        self._report(
            results,
            "No duplicate event references within on_action blocks",
            "Duplicate event references in on_action blocks (event may fire twice per trigger):",
            Severity.WARNING,
            category="duplicate-event-ref",
        )

    def run_validations(self):
        self.validate_missing_event_refs()
        self.validate_non_triggered_on_action_refs()
        self.validate_duplicate_event_refs()


if __name__ == "__main__":
    run_validator_main(
        Validator, "Validate on_actions event references in Millennium Dawn mod"
    )
