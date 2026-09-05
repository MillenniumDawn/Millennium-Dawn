"""Regression tests for date-gated event scheduling."""

import validate_events as V
from shared.suite import collecting_validator


def _write(tmp_path, name, body):
    p = tmp_path / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return str(p)


def _gated(tmp_path, body, name="events/Ev.txt"):
    return {
        e[0]
        for e in V.scan_date_gated_events((_write(tmp_path, name, body), frozenset()))
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
    assert set(V.scan_event_fire_graph((p, frozenset()))) == {
        ("parent.1", "child.1"),
        ("parent.1", "child.2"),
    }


# --- fire-path detection ---
#
# The date-gated scheduling check exempts two on_action fire paths: a
# `random_events = { weight = id }` pool (the pool is the schedule) and a
# chance-rolled `random = { chance = N country_event = X }` poll (emulates
# MTTH). These tests exercise the scanners that recognise those paths, which
# the exemption-logic tests below mock out.


def _poll_ids(tmp_path, body, name="common/on_actions/99_GER.txt"):
    return V.scan_probability_rolled_fires((_write(tmp_path, name, body), frozenset()))


def test_poll_short_form_detected(tmp_path):
    body = """on_actions = {
\ton_monthly_GER = {
\t\teffect = {
\t\t\tif = {
\t\t\t\tlimit = { date > 2005.1.1 }
\t\t\t\trandom = {
\t\t\t\t\tchance = 17
\t\t\t\t\tcountry_event = foo.1
\t\t\t\t}
\t\t\t}
\t\t}
\t}
}
"""
    assert _poll_ids(tmp_path, body) == {"foo.1"}


def test_poll_block_form_detected(tmp_path):
    body = """on_actions = {
\ton_monthly_GER = {
\t\teffect = {
\t\t\trandom = {
\t\t\t\tchance = 50
\t\t\t\tcountry_event = { id = foo.1 random_days = 210 random_hours = 10 }
\t\t\t}
\t\t}
\t}
}
"""
    assert _poll_ids(tmp_path, body) == {"foo.1"}


def test_poll_without_chance_not_detected(tmp_path):
    """A `random = { }` block with no `chance =` is not a chance-rolled poll."""
    body = """on_actions = {
\ton_monthly_GER = {
\t\teffect = {
\t\t\trandom = {
\t\t\t\tcountry_event = foo.1
\t\t\t}
\t\t}
\t}
}
"""
    assert _poll_ids(tmp_path, body) == set()


def test_poll_scope_keywords_not_confused(tmp_path):
    """`random_country`/`random_list`/`random_events` are not `random = {`."""
    body = """on_actions = {
\ton_monthly_GER = {
\t\teffect = {
\t\t\trandom_country = { country_event = foo.1 }
\t\t\trandom_list = { 50 = foo.2 }
\t\t\trandom_events = { 50 = foo.3 }
\t\t}
\t}
}
"""
    assert _poll_ids(tmp_path, body) == set()


def test_poll_commented_out_not_detected(tmp_path):
    body = """on_actions = {
\ton_monthly_GER = {
\t\teffect = {
\t\t\t# random = {
\t\t\t# \tchance = 17
\t\t\t# \tcountry_event = foo.1
\t\t\t# }
\t\t}
\t}
}
"""
    assert _poll_ids(tmp_path, body) == set()


def test_extract_random_event_ids():
    body = """on_actions = {
\ton_new_term_election = {
\t\trandom_events = {
\t\t\t100 = foo.1
\t\t\t1000 = bar.2
\t\t}
\t}
}
"""
    assert V._extract_random_event_ids(body) == {"foo.1", "bar.2"}


# --- exemption logic ---


_FakeValidator = collecting_validator(V.Validator)


def _run(monkeypatch, gated, fires, graph, random_events=(), polls=()):
    validator = _FakeValidator("/tmp")
    monkeypatch.setattr(validator, "_collect_files", lambda *a, **kw: ["f.txt"])
    monkeypatch.setattr(validator, "_rel_posix", lambda f: f)
    monkeypatch.setattr(validator, "_get_event_fires", lambda: fires)
    monkeypatch.setattr(validator, "_get_random_event_ids", lambda: set(random_events))
    monkeypatch.setattr(validator, "_get_probability_rolled_ids", lambda: set(polls))
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


def test_random_events_pool_event_exempt(monkeypatch):
    """A `random_events` pool weights its events by MTTH; the pool is the
    schedule, so a date-gated event in one is not dead content."""
    results = _run(
        monkeypatch,
        gated=[("foo.1", "events/Ev.txt", 10)],
        fires=[("other.1", _YE, 5)],
        graph=[],
        random_events=["foo.1"],
    )
    assert results == []


def test_probability_rolled_poll_event_exempt(monkeypatch):
    """A chance-rolled on_action poll emulates MTTH and has no deterministic
    yearly slot, so a date-gated event fired from one is not dead content."""
    results = _run(
        monkeypatch,
        gated=[("foo.1", "events/Ev.txt", 10)],
        fires=[("other.1", _YE, 5), ("foo.1", "common/on_actions/99_GER.txt", 12)],
        graph=[],
        polls=["foo.1"],
    )
    assert results == []


def test_missing_scheduling_file_skips_check(monkeypatch):
    """A rename of the yearly effects must skip, not flood with findings."""
    results = _run(
        monkeypatch,
        gated=[("foo.1", "events/Ev.txt", 10)],
        fires=[("foo.1", "events/Ev.txt", 30)],
        graph=[],
    )
    assert results == []


def test_date_gated_check_reports_error_severity(monkeypatch):
    """The check is an ERROR, not a WARNING, once the backlog is clear."""
    validator = _FakeValidator("/tmp")
    monkeypatch.setattr(validator, "_collect_files", lambda *a, **kw: ["f.txt"])
    monkeypatch.setattr(validator, "_pool_map", lambda fn, args, **kw: [])
    validator.validate_date_gated_scheduling()
    assert validator.last_severity == V.Severity.ERROR


def test_get_probability_rolled_ids_wiring(tmp_path, monkeypatch):
    """The wrapper scans on_actions files and caches the result."""
    body = """on_actions = {
\ton_monthly_GER = {
\t\teffect = {
\t\t\trandom = {
\t\t\t\tchance = 17
\t\t\t\tcountry_event = foo.1
\t\t\t}
\t\t}
\t}
}
"""
    f = _write(tmp_path, "common/on_actions/99_GER.txt", body)
    validator = _FakeValidator("/tmp")
    monkeypatch.setattr(validator, "_collect_files", lambda *a, **kw: [f])
    calls = []

    def fake_pool_map(fn, args, **kw):
        calls.append(fn)
        return [fn(a) for a in args]

    monkeypatch.setattr(validator, "_pool_map", fake_pool_map)
    assert validator._get_probability_rolled_ids() == {"foo.1"}
    assert validator._get_probability_rolled_ids() == {"foo.1"}  # cached
    assert calls == [V.scan_probability_rolled_fires]


def test_get_random_event_ids_wiring(tmp_path, monkeypatch):
    """The wrapper scans on_actions files and caches the result."""
    body = """on_actions = {
\ton_new_term_election = {
\t\trandom_events = {
\t\t\t100 = foo.1
\t\t}
\t}
}
"""
    f = _write(tmp_path, "common/on_actions/99_GER.txt", body)
    validator = _FakeValidator("/tmp")
    monkeypatch.setattr(validator, "_collect_files", lambda *a, **kw: [f])
    assert validator._get_random_event_ids() == {"foo.1"}
    assert validator._get_random_event_ids() == {"foo.1"}  # cached
