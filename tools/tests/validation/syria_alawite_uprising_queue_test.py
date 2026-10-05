"""Regression tests for Syria's delayed Alawite uprising event queue."""

import re
from pathlib import Path

from shared_utils import extract_block_from_text

REPO = Path(__file__).resolve().parents[3]
QUEUED_FLAG = "syr_alawite_uprising_queued"
PENDING_FLAG = "syr_alawite_uprising_event_pending"
QUEUE_CALL_RE = re.compile(r"country_event\s*=\s*\{[ \t]*id[ \t]*=\s*SyriaFocus\.26\b")


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

    assert f"NOT = {{ has_country_flag = {PENDING_FLAG} }}" in clear_at_peace
    assert all(
        f"has_war_with = {tag}" in clear_at_peace for tag in ("ROJ", "DRU", "ALA")
    )

    queue_blocks = []
    for text in (monthly, events):
        for call in QUEUE_CALL_RE.finditer(text):
            queue_blocks.append(_if_block_containing(text, call.start()))
    assert len(queue_blocks) == 2
    assert all(f"set_country_flag = {QUEUED_FLAG}" in block for block in queue_blocks)
    assert all(f"set_country_flag = {PENDING_FLAG}" in block for block in queue_blocks)
    assert f"clr_country_flag = {PENDING_FLAG}" in _event_block(events, "SyriaFocus.26")


def test_druze_event_only_queues_alawite_uprising_with_owned_core():
    events = (REPO / "events/Syria.txt").read_text(encoding="utf-8")
    druze_event = _event_block(events, "SyriaFocus.25")
    call = QUEUE_CALL_RE.search(druze_event)
    assert call is not None
    queue = _if_block_containing(druze_event, call.start())
    limit = _block(queue, queue.index("limit = {"))

    assert "any_owned_state = { is_core_of = ALA }" in limit
