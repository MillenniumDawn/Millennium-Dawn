"""Date-gated event scheduling.

An event whose trigger waits for a date needs the yearly effects to schedule it.
The reverse check flags an event the yearly effects already schedule that still
carries a date bound of its own.
"""

import pytest
import validate_events as V
from shared.suite import assert_findings, collecting_validator, event_block
from shared.suite import write_under_str as _write

_YEARLY = V._YEARLY_EFFECTS_REL
_EVENT_FILE = "events/Ev.txt"
_FOCUS_FILE = "common/national_focus/GER.txt"
_ON_ACTION_FILE = "common/on_actions/99_GER.txt"
_FakeValidator = collecting_validator(V.Validator)
# The expected finding of a case where the check returns before it reports.
_SKIPPED = object()


def _assert_reported(validator, finding, severity):
    """`finding` is fragments of the one finding, None for a clean report."""
    assert_findings(
        validator.collected, [finding] if isinstance(finding, tuple) else []
    )
    assert validator.last_severity == (None if finding is _SKIPPED else severity)


def _event(event_id, *fields):
    option = f"option = {{ name = {event_id}.a }}"
    return event_block(event_id, "is_triggered_only = yes", *fields, option)


def _on_action(*effect_lines):
    lines = "".join(f"\t\t\t{line}\n" for line in effect_lines)
    return f"on_actions = {{\n\ton_monthly_GER = {{\n\t\teffect = {{\n{lines}\t\t}}\n\t}}\n}}\n"


# `date <` alone is a chain-event expiry guard, not a schedule anchor. On a
# scheduled event it still counts as a bound: it can only drop the fire.
# case: (event, ids read as date-gated, ids read as date-bounded)
_DATE_SCAN_CASES = {
    "lower bound": (
        _event("foo.1", "trigger = {\n\t\tdate > 2005.1.1\n\t}"),
        {"foo.1"},
        {"foo.1"},
    ),
    "upper bound": (
        _event("foo.2", "trigger = {\n\t\tdate < 2005.1.1\n\t}"),
        set(),
        {"foo.2"},
    ),
    "commented bound": (
        _event("foo.4", "trigger = {\n\t\t#date > 2005.1.1\n\t}"),
        set(),
        set(),
    ),
    "date outside the trigger": (
        _event(
            "foo.3",
            "immediate = {\n\t\tif = { limit = { date < 2005.1.1 } set_country_flag = x }\n\t}",
            "option = {\n\t\tname = foo.3.b\n"
            "\t\tif = { limit = { date > 2005.1.1 } add_political_power = 5 }\n\t}",
        ),
        set(),
        set(),
    ),
}


@pytest.mark.parametrize(
    ("event", "gated", "bounded"), _DATE_SCAN_CASES.values(), ids=_DATE_SCAN_CASES
)
def test_date_comparisons_are_read_from_the_event_trigger(
    tmp_path, event, gated, bounded
):
    args = (_write(tmp_path, _EVENT_FILE, event), frozenset())

    assert {found[0] for found in V.scan_date_gated_events(args)} == gated
    assert {found[0] for found in V.scan_date_bounded_events(args)} == bounded


def test_fire_graph_pairs_an_event_with_the_events_it_fires(tmp_path):
    path = _write(
        tmp_path,
        _EVENT_FILE,
        _event(
            "parent.1",
            "immediate = {\n\t\tcountry_event = { id = child.1 days = 3 }\n"
            "\t\tnews_event = child.2\n\t\tcountry_event = UN.[ID]\n\t}",
        ),
    )

    assert set(V.scan_event_fire_graph((path, frozenset()))) == {
        ("parent.1", "child.1"),
        ("parent.1", "child.2"),
    }


# A chance-rolled `random = { chance = N country_event = X }` poll emulates MTTH.
# case: (on_action effect lines, ids read as chance-rolled)
_POLL_CASES = {
    "short form": (
        ["random = {", "\tchance = 17", "\tcountry_event = foo.1", "}"],
        {"foo.1"},
    ),
    "block form": (
        [
            "random = {",
            "\tchance = 50",
            "\tcountry_event = { id = foo.1 random_days = 210 random_hours = 10 }",
            "}",
        ],
        {"foo.1"},
    ),
    "no chance": (["random = {", "\tcountry_event = foo.1", "}"], set()),
    # None of these is `random = {`.
    "commented out": (
        ["# random = {", "# \tchance = 17", "# \tcountry_event = foo.1", "# }"],
        set(),
    ),
    "lookalike scope keywords": (
        [
            "random_country = { chance = 5 country_event = foo.1 }",
            "random_list = { 50 = foo.2 }",
            "random_events = { 50 = foo.3 }",
        ],
        set(),
    ),
}


@pytest.mark.parametrize(("effect", "rolled"), _POLL_CASES.values(), ids=_POLL_CASES)
def test_chance_rolled_fires_are_read_from_on_actions(tmp_path, effect, rolled):
    path = _write(tmp_path, _ON_ACTION_FILE, _on_action(*effect))

    assert V.scan_probability_rolled_fires((path, frozenset())) == rolled


def _stub(monkeypatch, fires, scanned):
    """A validator whose file walk, fire list and scans are fixed."""
    validator = _FakeValidator("/tmp")
    stubs = {
        "_collect_files": lambda *a, **k: ["f.txt"],
        "_rel_posix": lambda path: path,
        "_get_event_fires": lambda: [(eid, path, 5) for eid, path in fires],
        "_pool_map": lambda fn, args, **k: [scanned(fn)],
    }
    for name, stub in stubs.items():
        monkeypatch.setattr(validator, name, stub)
    return validator


# case: (date-gated event, (id, file) fires, fire graph, exemptions, finding)
_SCHEDULING_CASES = {
    "fired from the yearly effects": ("foo.1", [("foo.1", _YEARLY)], [], {}, None),
    "chain event of a scheduled parent": (
        "child.1",
        [("parent.1", _YEARLY), ("child.1", _EVENT_FILE)],
        [("parent.1", "child.1")],
        {},
        None,
    ),
    "nothing fires it": (
        "foo.1",
        [("other.1", _YEARLY)],
        [],
        {},
        ("foo.1", "nothing"),
    ),
    # A focus decides when it completes, so a date window is availability.
    "fired from a focus": (
        "foo.1",
        [("other.1", _YEARLY), ("foo.1", _FOCUS_FILE)],
        [],
        {},
        None,
    ),
    # A daily on_action waiting for a date is a poll, not a schedule.
    "fired from an on_action": (
        "foo.1",
        [("other.1", _YEARLY), ("foo.1", _ON_ACTION_FILE)],
        [],
        {},
        ("foo.1", _ON_ACTION_FILE),
    ),
    "in a random_events pool": (
        "foo.1",
        [("other.1", _YEARLY)],
        [],
        {"_get_random_event_ids": {"foo.1"}},
        None,
    ),
    "fired from a chance-rolled poll": (
        "foo.1",
        [("other.1", _YEARLY), ("foo.1", _ON_ACTION_FILE)],
        [],
        {"_get_probability_rolled_ids": {"foo.1"}},
        None,
    ),
    # A rename of the yearly effects must skip, not flood with findings.
    "no yearly effects file": ("foo.1", [("foo.1", _EVENT_FILE)], [], {}, _SKIPPED),
}


@pytest.mark.parametrize(
    ("gated", "fires", "graph", "exemptions", "finding"),
    _SCHEDULING_CASES.values(),
    ids=_SCHEDULING_CASES,
)
def test_date_gated_event_needs_a_schedule(
    monkeypatch, gated, fires, graph, exemptions, finding
):
    graph_scans = (V.scan_event_fire_graph, V._cached_scan_event_fire_graph)
    validator = _stub(
        monkeypatch,
        fires,
        lambda fn: graph if fn in graph_scans else [(gated, _EVENT_FILE, 10)],
    )
    for name in ("_get_random_event_ids", "_get_probability_rolled_ids"):
        monkeypatch.setattr(
            validator, name, lambda name=name: exemptions.get(name, set())
        )

    validator.validate_date_gated_scheduling()

    _assert_reported(validator, finding, V.Severity.ERROR)


# A second fire path may need the guard, so only sole-source events count.
# case: ((id, file) fires, finding)
_DATE_BOUND_CASES = {
    "scheduled only": ([("foo.1", _YEARLY)], ("foo.1", _YEARLY)),
    "also fired from a focus": ([("foo.1", _YEARLY), ("foo.1", _FOCUS_FILE)], None),
    "also fired from an event": ([("foo.1", _YEARLY), ("foo.1", _EVENT_FILE)], None),
    "no yearly effects file": ([("foo.1", _EVENT_FILE)], _SKIPPED),
}


@pytest.mark.parametrize(
    ("fires", "finding"), _DATE_BOUND_CASES.values(), ids=_DATE_BOUND_CASES
)
def test_scheduled_event_needs_no_date_bound(monkeypatch, fires, finding):
    validator = _stub(monkeypatch, fires, lambda fn: [("foo.1", _EVENT_FILE, 10)])

    validator.validate_scheduled_date_bounds()

    # Warning-only until the backlog is cleared.
    _assert_reported(validator, finding, V.Severity.WARNING)


def _on_actions_validator(tmp_path, monkeypatch, body):
    path = _write(tmp_path, _ON_ACTION_FILE, body)
    validator = _FakeValidator(str(tmp_path))
    monkeypatch.setattr(validator, "_collect_files", lambda *a, **k: [path])
    return validator


def test_chance_rolled_ids_are_scanned_once_from_on_actions(tmp_path, monkeypatch):
    body = _on_action(*_POLL_CASES["short form"][0])
    validator = _on_actions_validator(tmp_path, monkeypatch, body)
    calls = []

    def fake_pool_map(fn, args, **kw):
        calls.append(fn)
        return [fn(a) for a in args]

    monkeypatch.setattr(validator, "_pool_map", fake_pool_map)

    assert validator._get_probability_rolled_ids() == {"foo.1"}
    assert validator._get_probability_rolled_ids() == {"foo.1"}
    assert [call.func for call in calls] == [V.scan_probability_rolled_fires]
    assert calls[0].keywords == {"mod_path": validator.mod_path}


def test_random_event_ids_are_read_from_on_action_pools(tmp_path, monkeypatch):
    body = (
        "on_actions = {\n\ton_new_term_election = {\n\t\trandom_events = {\n"
        "\t\t\t100 = foo.1\n\t\t\t1000 = bar.2\n\t\t}\n\t}\n}\n"
    )
    validator = _on_actions_validator(tmp_path, monkeypatch, body)

    assert validator._get_random_event_ids() == {"foo.1", "bar.2"}
    # The second read comes from the cache.
    monkeypatch.setattr(validator, "_collect_files", lambda *a, **k: [])
    assert validator._get_random_event_ids() == {"foo.1", "bar.2"}
