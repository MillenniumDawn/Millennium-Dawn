"""Evaluate Mercosur spending weights, not native selection or delayed payments."""

import pytest
from shared.paths import REPO_ROOT
from shared.suite import (
    EconomicScriptFixture,
    read_decision_categories,
    read_text,
    script_block,
)

_ACCESSION = [
    f"MER_{country}_{project}"
    for countries, projects in (
        (
            ("CHL", "COL", "VEN"),
            ("tariff_alignment", "customs_system_modernization", "common_standards"),
        ),
        (
            ("PRU",),
            ("logistics_corridor", "cross_border_transport", "port_connectivity"),
        ),
        (("BOL",), ("logistics_corridor", "overland_transport", "border_connectivity")),
        (("PAN",), ("logistics_corridor", "port_transport", "trade_connectivity")),
        (
            ("ECU", "GUY"),
            ("development_funds", "civilian_industry", "infrastructure_development"),
        ),
        (
            ("SUR",),
            ("development_funds", "civilian_industry", "commercial_infrastructure"),
        ),
        (
            ("MEX",),
            (
                "industrial_investment_agreement",
                "commercial_investment_framework",
                "financial_cooperation_package",
            ),
        ),
    )
    for country in countries
    for project in projects
]
_INTEREST_LIMITED = (
    "MER_release_development_fund_round",
    "MER_unasul_integrated_corridor_plan",
    "MER_unasul_energy_security_reinforcement",
    "MER_unasul_joint_exercises",
)
_SPENDING = [
    *_ACCESSION,
    *_INTEREST_LIMITED,
    "MER_unasul_joint_health_improvement_project",
    "MER_unasul_supply_chain_strengthening",
    "MER_unasul_joint_research_exchange_project",
]


@pytest.fixture(scope="module")
def decisions():
    return read_decision_categories(
        REPO_ROOT / "common/decisions",
        (("mercosur_decisions.txt", "MER_mercosur_diplomacy"),),
    )


@pytest.fixture
def economy():
    source = read_text(REPO_ROOT / "common/scripted_triggers/00_economic_triggers.txt")
    return EconomicScriptFixture(
        {"treasury_rate": 0, "budget_balance_ratio": 0, "interest_rate": 10},
        predicates={"has_active_mission": lambda *_: False},
        triggers={"ai_has_high_deficit": script_block(source, "ai_has_high_deficit")},
    )


@pytest.mark.parametrize("name", _SPENDING)
@pytest.mark.parametrize(
    "rate,balance,bankrupt,expected",
    [
        (0, 0, False, 1),
        (-3, -0.10, False, 1),
        (-3.001, 0, False, 0.5),
        (0, -0.1001, False, 0.5),
        (0, 0, True, 0),
        (-4, -0.11, True, 0),
    ],
)
def test_project_weights_respond_to_the_sponsors_finances(
    decisions, economy, name, rate, balance, bankrupt, expected
):
    economy.values.update(treasury_rate=rate, budget_balance_ratio=balance)
    economy.predicates["has_active_mission"] = (
        lambda mission, _: bankrupt and mission == "bankruptcy_incoming_collapse"
    )
    assert economy.weight(script_block(decisions[name], "ai_will_do")) == expected


@pytest.mark.parametrize("name", _INTEREST_LIMITED)
@pytest.mark.parametrize("deficit", [False, True])
@pytest.mark.parametrize("interest,expected", [(10, 1), (10.001, 0)])
def test_existing_interest_limit_still_blocks_regional_projects(
    decisions, economy, name, deficit, interest, expected
):
    economy.values.update(interest_rate=interest, treasury_rate=-4 if deficit else 0)
    assert economy.weight(script_block(decisions[name], "ai_will_do")) == (
        expected / 2 if deficit else expected
    )
