"""Unit tests for tick_audit's parsing and accuracy guarantees.

These cover the pure helpers where correctness lives — brace-aware block
extraction, direct-only event attribution, decision-timer detection that
ignores nested `days`, and the immediate-vs-option loop classification. They do
not touch the live mod, so they stay fast and deterministic.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "analysis"))

import tick_audit as ta  # noqa: E402

# --- brace-depth field reading ---------------------------------------------


def test_depth0_assignments_ignores_nested():
    body = """
        days_re_enable = 30
        timeout_effect = {
            set_country_flag = { flag = x value = 1 days = 28 }
            country_event = { id = foo.1 days = 5 }
        }
        fire_only_once = no
    """
    fields = ta._depth0_assignments(body)
    assert fields["days_re_enable"] == "30"
    assert fields["fire_only_once"] == "no"
    # The nested `days = 28` / `days = 5` must NOT surface as a decision field.
    assert "days" not in fields


def test_depth0_assignments_reads_variable_timer():
    fields = ta._depth0_assignments("days_mission_timeout = ROOT.battery_park_time")
    assert fields["days_mission_timeout"] == "ROOT.battery_park_time"


# --- event-fire extraction --------------------------------------------------


def test_extract_direct_event_fires_block_and_bare():
    body = """
        country_event = { id = econvent.1 days = 3 }
        news_event = germany.5
    """
    fires = dict(ta.extract_direct_event_fires(body))
    assert fires["econvent.1"] == 3
    assert fires["germany.5"] is None


def test_random_events_pool_ids():
    body = """
        random_events = {
            1500 = 0
            25 = econvent.1
            10 = econvent.4
        }
    """
    assert ta.extract_random_events(body) == ["econvent.1", "econvent.4"]


def test_scripted_calls_only_known_names():
    effects = {"recalculate_party": "", "update_mafia_strength": ""}
    body = "recalculate_party = yes\n add_stability = 0.1\n update_mafia_strength = yes"
    assert ta.extract_scripted_calls(body, effects) == {
        "recalculate_party",
        "update_mafia_strength",
    }


# --- top-level block parsing ------------------------------------------------


def test_top_level_blocks_depth0_only():
    text = """
    cat = {
        decision_a = { days_remove = 7 }
        decision_b = { available = { always = yes } }
    }
    """
    names = [n for n, _b, _s in ta._top_level_blocks(text)]
    assert names == ["cat"]  # nested decisions are not depth 0


# --- decision timers (accuracy: real fields, not nested days) ---------------


def test_timed_decision_bucketing():
    assert ta.bucket_for_days(1) == "daily"
    assert ta.bucket_for_days(7) == "weekly"
    assert ta.bucket_for_days(30) == "monthly"
    assert ta.bucket_for_days(90) == "other"
    assert ta.bucket_for_days(None) == "other"


# --- self-loop classification (immediate=auto vs option=player) -------------


def test_event_loop_immediate_is_auto():
    events = {
        "loop.1": {
            "type": "country_event",
            "file": "e.txt",
            "line": 1,
            "body": "immediate = { country_event = { id = loop.1 days = 7 } }",
        }
    }
    loops = ta.collect_event_loops(events)
    assert len(loops) == 1
    assert loops[0]["trigger"] == "immediate"
    assert loops[0]["bucket"] == "weekly"


def test_event_loop_option_is_player():
    events = {
        "loop.2": {
            "type": "country_event",
            "file": "e.txt",
            "line": 1,
            "body": (
                "option = { name = a "
                "hidden_effect = { country_event = { id = loop.2 days = 1 } } }"
            ),
        }
    }
    loops = ta.collect_event_loops(events)
    assert len(loops) == 1
    assert loops[0]["trigger"] == "option"
    # Player-driven: never attributed to a daily/weekly/monthly tick.
    assert loops[0]["bucket"] == "player"


def test_non_self_firing_event_is_not_a_loop():
    events = {
        "chain.1": {
            "type": "country_event",
            "file": "e.txt",
            "line": 1,
            "body": "immediate = { country_event = { id = chain.2 days = 1 } }",
        }
    }
    assert ta.collect_event_loops(events) == []
