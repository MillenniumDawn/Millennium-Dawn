"""Evaluate Turkish decision weights, not native AI selection or delayed charges."""

import pytest
from shared.paths import REPO_ROOT
from shared.suite import (
    EconomicScriptFixture,
    read_decision_categories,
    read_text,
    script_block,
)

_OPTIONAL = (
    "hire_gulenist_economic_advisors",
    "employ_gulenist_informants",
    "hire_gulenist_educators",
    "recall_gulenists",
    "reestablish_village_institutes",
    "incentivise_modern_farming",
    "heavily_subsidise_agriculture",
    "encourage_communal_farming",
    "implement_revolutionary_education",
    "land_reforms",
    "redesign_bosphorus",
    "ask_for_infrastructure",
    "ask_for_network",
    "ask_for_supply",
    "ask_for_radars",
    "ask_for_airbase",
)
_RECONCILIATION = ("pass_the_infrastructure_bill", "kurdish_security_apparatus")
_FINANCES = {
    "healthy": ({}, False, 1),
    "deficit boundary": (
        {"treasury_rate": -3, "budget_balance_ratio": -0.10},
        False,
        1,
    ),
    "absolute deficit": ({"treasury_rate": -3.001}, False, 0.5),
    "relative deficit": ({"budget_balance_ratio": -0.1001}, False, 0.5),
    "collapse": ({}, True, 0),
    "collapse and deficit": ({"treasury_rate": -4}, True, 0),
}


@pytest.fixture(scope="module")
def decisions():
    return read_decision_categories(
        REPO_ROOT / "common/decisions",
        tuple(
            ("Turkey.txt", category)
            for category in (
                "TUR_domestic_politics_category",
                "TUR_ciw_decisions",
                "TUR_rebuilding_kurdistan",
            )
        ),
    )


@pytest.mark.parametrize("name", (*_OPTIONAL, *_RECONCILIATION))
@pytest.mark.parametrize("values,collapse,factor", _FINANCES.values(), ids=_FINANCES)
def test_optional_spending_respects_finances_without_blocking_reconciliation(
    decisions, name, values, collapse, factor
):
    economic_triggers = read_text(
        REPO_ROOT / "common/scripted_triggers/00_economic_triggers.txt"
    )
    actor = EconomicScriptFixture(
        {"treasury_rate": 0, "budget_balance_ratio": 0, **values},
        triggers={
            "ai_has_high_deficit": script_block(
                economic_triggers, "ai_has_high_deficit"
            )
        },
        predicates={
            "has_active_mission": lambda mission, _: (
                mission == "bankruptcy_incoming_collapse" and collapse
            )
        },
    )
    actual = actor.weight(script_block(decisions[f"TUR_{name}"], "ai_will_do"))
    assert actual == (10 if name in _RECONCILIATION else factor)
