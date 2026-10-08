"""Regression tests for Syria's delayed Alawite uprising event queue."""

import re
from pathlib import Path

from shared_utils import extract_block_from_text

REPO = Path(__file__).resolve().parents[3]
QUEUED_FLAG = "SYR_alawite_uprising_queued"
PENDING_FLAG = "SYR_alawite_uprising_event_pending"
QUEUE_CALL_RE = re.compile(
    r"^[ \t]+country_event\s*=\s*\{\s*id\s*=\s*SyriaFocus\.26\b",
    re.MULTILINE,
)


def _block(text, start):
    body, end = extract_block_from_text(text, start)
    assert end >= 0
    return body


def _if_block_containing(text, position):
    start = text.rfind("if = {", 0, position)
    assert start >= 0
    body, end = extract_block_from_text(text, start)
    assert end > position
    return body


def _event_block(text, event_id):
    marker = text.index(f"\tid = {event_id}\n\ttitle =")
    return _block(text, text.rfind("country_event = {", 0, marker))


def test_pending_alawite_event_keeps_queue_guard_until_event_fires():
    on_actions = (REPO / "common/on_actions/99_SYR_on_actions.txt").read_text(
        encoding="utf-8"
    )
    events = (REPO / "events/Syria.txt").read_text(encoding="utf-8")
    monthly = _block(on_actions, on_actions.index("on_monthly_SYR = {"))
    clear_at_peace = _if_block_containing(
        monthly, monthly.index(f"clr_country_flag = {QUEUED_FLAG}")
    )

    clear_limit = _block(clear_at_peace, clear_at_peace.index("limit = {"))
    assert f"NOT = {{ has_country_flag = {PENDING_FLAG} }}" in clear_limit
    not_blocks = [
        _block(clear_limit, match.start())
        for match in re.finditer(r"\bNOT\s*=\s*\{", clear_limit)
    ]
    war_guard = next(
        (block for block in not_blocks if re.search(r"\bOR\s*=\s*\{", block)), None
    )
    assert war_guard is not None
    war_match = re.search(r"\bOR\s*=\s*\{", war_guard)
    assert war_match is not None
    war_body = _block(war_guard, war_match.start())
    assert set(re.findall(r"has_war_with\s*=\s*(\w+)", war_body)) == {
        "ROJ",
        "DRU",
        "ALA",
    }

    queue_sources = {"monthly on_action": monthly, "Druze event": events}
    queue_sites = []
    for source_name, text in queue_sources.items():
        calls = list(QUEUE_CALL_RE.finditer(text))
        assert calls, f"{source_name} should contain a SyriaFocus.26 queue site"
        for call in calls:
            block = _if_block_containing(text, call.start())
            queue_sites.append(block)
    assert all(f"set_country_flag = {QUEUED_FLAG}" in block for block in queue_sites)
    assert all(f"set_country_flag = {PENDING_FLAG}" in block for block in queue_sites)
    assert f"clr_country_flag = {PENDING_FLAG}" in _event_block(events, "SyriaFocus.26")


def test_druze_event_only_queues_alawite_uprising_with_owned_core():
    events = (REPO / "events/Syria.txt").read_text(encoding="utf-8")
    druze_event = _event_block(events, "SyriaFocus.25")
    call = QUEUE_CALL_RE.search(druze_event)
    assert call is not None
    queue = _if_block_containing(druze_event, call.start())
    limit = _block(queue, queue.index("limit = {"))

    assert "any_owned_state = { is_core_of = ALA }" in limit
