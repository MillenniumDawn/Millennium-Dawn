"""Contracts for Australian investment, exercise, and aircraft rewards."""

import pytest
from shared.paths import REPO_ROOT
from shared.suite import read_text, script_block
from shared_utils import iter_statements, strip_comments


@pytest.fixture(scope="module")
def australia_events():
    source = strip_comments(read_text(REPO_ROOT / "events/05_australia_events.txt"))
    events = {}
    for key, _, body in iter_statements(source):
        if key == "country_event" and body is not None:
            event_id = next(
                value for name, value, _ in iter_statements(body) if name == "id"
            )
            events[event_id] = body
    return events


def test_investment_bankruptcy_gate_runs_after_opinion_bonus(australia_events):
    event = australia_events["AST_investment_opportunity_event.1"]
    option = next(
        body
        for key, _, body in iter_statements(event)
        if key == "option"
        and body is not None
        and ("name", "AST_investment_opportunity_event.1.a", None)
        in list(iter_statements(body))
    )
    modifiers = [
        body
        for key, _, body in iter_statements(script_block(option, "ai_chance"))
        if key == "modifier" and body is not None
    ]
    gate = list(iter_statements(modifiers[-1]))
    assert ("factor", "0", None) in gate
    assert ("has_active_mission", "bankruptcy_incoming_collapse", None) in gate
    assert any("add = 10" in body for body in modifiers[:-1])


def test_oil_lease_refusal_logs_its_effect(australia_events):
    option = script_block(australia_events["AST_oil_ind_lease.3"], "option")
    assert ("add_political_power", "-20", None) in list(iter_statements(option))
    assert (
        "log",
        "[GetDateText]: [This.GetName]: AST_oil_ind_lease.3.a executed",
        None,
    ) in list(iter_statements(option))


@pytest.mark.parametrize("event_id", ["4", "5", "6"])
def test_exercise_doctrine_bonus_names_its_source(australia_events, event_id):
    option = script_block(
        australia_events[f"AST_thai_mil_exercise.{event_id}"], "option"
    )
    bonus = script_block(option, "add_doctrine_cost_reduction")
    assert (
        "name",
        f"AST_thai_mil_exercise.{event_id}.t",
        None,
    ) in list(iter_statements(bonus))


def test_disappointing_exercise_uses_its_own_option_and_log(australia_events):
    option = script_block(australia_events["AST_thai_mil_exercise.6"], "option")
    fields = list(iter_statements(option))
    assert ("name", "AST_thai_mil_exercise.6.a", None) in fields
    assert (
        "log",
        "[GetDateText]: [This.GetName]: AST_thai_mil_exercise.6.a executed",
        None,
    ) in fields


def test_bomber_countermeasures_bonus_requires_bba():
    source = strip_comments(
        read_text(REPO_ROOT / "common/national_focus/05_Australia.txt")
    )
    tree = next(
        body
        for key, _, body in iter_statements(source)
        if key == "focus_tree"
        and body is not None
        and ("id", "beazleygov_focus", None) in list(iter_statements(body))
    )
    focus = next(
        body
        for key, _, body in iter_statements(tree)
        if key == "focus"
        and body is not None
        and ("id", "AST_bomber_agreement", None) in list(iter_statements(body))
    )
    reward = script_block(focus, "completion_reward")
    heavy_aircraft = script_block(reward, "add_tech_bonus")
    assert ("category", "CAT_heavy_aircraft", None) in list(
        iter_statements(heavy_aircraft)
    )
    guarded = script_block(reward, "if")
    assert ("has_dlc", "By Blood Alone", None) in list(
        iter_statements(script_block(guarded, "limit"))
    )
    assert ("category", "CAT_air_countermeasures", None) in list(
        iter_statements(script_block(guarded, "add_tech_bonus"))
    )
