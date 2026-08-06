"""Tests for validate_events.py: date-gated events must be scheduled.

MD fires its historical events from
`common/scripted_effects/00_yearly_effects.txt` and uses the event's own
`date >` check only as a guard. An event carrying the guard with no scheduling
entry is dead content: it is triggered-only, so nothing ever fires it.

A `date <` bound alone is an expiry guard on a chain event and says nothing
about scheduling, so only `date >` counts. Chain events inherit whatever
schedules an ancestor.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import validate_events as V
from validate_events import scan_date_gated_events, scan_event_fire_graph


def _write(tmp_path, name, body):
    p = tmp_path / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return str(p)


def _gated(tmp_path, body, name="events/Ev.txt"):
    return {
        e[0]
        for e in scan_date_gated_events((_write(tmp_path, name, body), frozenset()))
    }


DATE_GATED = """country_event = {
\tid = foo.1
\tis_triggered_only = yes
\ttrigger = {
\t\tdate > 2005.1.1
\t}
\toption = { name = foo.1.a }
}
"""

EXPIRY_ONLY = """country_event = {
\tid = foo.2
\tis_triggered_only = yes
\ttrigger = {
\t\tdate < 2005.1.1
\t}
\toption = { name = foo.2.a }
}
"""


def test_date_lower_bound_detected(tmp_path):
    assert _gated(tmp_path, DATE_GATED) == {"foo.1"}


def test_expiry_bound_only_not_detected(tmp_path):
    """`date <` alone is a chain-event expiry guard, not a schedule anchor."""
    assert _gated(tmp_path, EXPIRY_ONLY) == set()


def test_nested_inside_trigger_detected(tmp_path):
    body = DATE_GATED.replace(
        "\t\tdate > 2005.1.1\n", "\t\tOR = {\n\t\t\tdate > 2005.1.1\n\t\t}\n"
    )
    assert _gated(tmp_path, body) == {"foo.1"}


def test_indented_definition_detected(tmp_path):
    """Several event files indent definitions one tab deeper than the norm."""
    body = "".join(
        "\t" + line if line.strip() else line for line in DATE_GATED.splitlines(True)
    )
    assert _gated(tmp_path, body) == {"foo.1"}


def test_date_in_option_limit_not_detected(tmp_path):
    body = """country_event = {
\tid = foo.3
\tis_triggered_only = yes
\toption = {
\t\tname = foo.3.a
\t\tif = { limit = { date > 2005.1.1 } add_political_power = 5 }
\t}
}
"""
    assert _gated(tmp_path, body) == set()


def test_date_in_immediate_not_detected(tmp_path):
    body = """country_event = {
\tid = foo.4
\tis_triggered_only = yes
\timmediate = {
\t\tif = { limit = { date > 2005.1.1 } set_country_flag = x }
\t}
\toption = { name = foo.4.a }
}
"""
    assert _gated(tmp_path, body) == set()


def test_date_in_mtth_modifier_not_detected(tmp_path):
    body = """country_event = {
\tid = foo.5
\ttitle = foo.5.t
\tmean_time_to_happen = {
\t\tdays = 30
\t\tmodifier = { factor = 0 date > 2005.1.1 }
\t}
\toption = { name = foo.5.a }
}
"""
    assert _gated(tmp_path, body) == set()


def test_commented_date_not_detected(tmp_path):
    body = DATE_GATED.replace("\t\tdate > 2005.1.1", "\t\t#date > 2005.1.1")
    assert _gated(tmp_path, body) == set()


def test_fire_block_is_not_an_event(tmp_path):
    body = "x = {\n\tcountry_event = { id = foo.1 days = 3 }\n}\n"
    assert _gated(tmp_path, body, name="common/f.txt") == set()


def test_fire_graph_pairs(tmp_path):
    body = """country_event = {
\tid = parent.1
\tis_triggered_only = yes
\toption = {
\t\tname = parent.1.a
\t\tcountry_event = { id = child.1 days = 3 }
\t\tnews_event = child.2
\t\tcountry_event = UN.[ID]
\t}
}
"""
    p = _write(tmp_path, "events/Ev.txt", body)
    assert set(scan_event_fire_graph((p, frozenset()))) == {
        ("parent.1", "child.1"),
        ("parent.1", "child.2"),
    }


# --- exemption logic ---


class _FakeValidator(V.Validator):
    """Validator whose _report collects results instead of rendering."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.collected = []

    def _report(self, results, ok_msg, fail_msg, severity=None, category=""):
        self.collected.extend(results)


def _run(monkeypatch, gated, fires, graph):
    validator = _FakeValidator("/tmp")
    monkeypatch.setattr(validator, "_collect_files", lambda *a, **kw: ["f.txt"])
    monkeypatch.setattr(validator, "_rel_posix", lambda f: f)
    monkeypatch.setattr(validator, "_get_event_fires", lambda: fires)
    monkeypatch.setattr(
        validator,
        "_pool_map",
        lambda fn, args, **kw: [graph if fn is V.scan_event_fire_graph else gated],
    )
    validator.validate_date_gated_scheduling()
    return validator.collected


_YE = V._YEARLY_EFFECTS_REL


def test_scheduled_event_not_flagged(monkeypatch):
    results = _run(
        monkeypatch,
        gated=[("foo.1", "events/Ev.txt", 10)],
        fires=[("foo.1", _YE, 5)],
        graph=[],
    )
    assert results == []


def test_chain_event_inherits_parent_schedule(monkeypatch):
    results = _run(
        monkeypatch,
        gated=[("child.1", "events/Ev.txt", 20)],
        fires=[("parent.1", _YE, 5), ("child.1", "events/Ev.txt", 30)],
        graph=[("parent.1", "child.1")],
    )
    assert results == []


def test_unscheduled_event_flagged(monkeypatch):
    results = _run(
        monkeypatch,
        gated=[("foo.1", "events/Ev.txt", 10)],
        fires=[("other.1", _YE, 5)],
        graph=[],
    )
    assert len(results) == 1
    assert "foo.1" in results[0] and "nothing" in results[0]


def test_focus_fired_event_exempt(monkeypatch):
    """A focus decides when it completes, so a date window is availability."""
    results = _run(
        monkeypatch,
        gated=[("foo.1", "events/Ev.txt", 10)],
        fires=[("other.1", _YE, 5), ("foo.1", "common/national_focus/GER.txt", 12)],
        graph=[],
    )
    assert results == []


def test_on_action_fired_event_flagged(monkeypatch):
    """A daily on_action waiting for a date is a poll, not a schedule."""
    results = _run(
        monkeypatch,
        gated=[("foo.1", "events/Ev.txt", 10)],
        fires=[("other.1", _YE, 5), ("foo.1", "common/on_actions/99_GER.txt", 12)],
        graph=[],
    )
    assert len(results) == 1
    assert "common/on_actions/99_GER.txt" in results[0]


def test_missing_scheduling_file_skips_check(monkeypatch):
    """A rename of the yearly effects must skip, not flood with findings."""
    results = _run(
        monkeypatch,
        gated=[("foo.1", "events/Ev.txt", 10)],
        fires=[("foo.1", "events/Ev.txt", 30)],
        graph=[],
    )
    assert results == []
