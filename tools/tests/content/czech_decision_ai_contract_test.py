"""Evaluate Czech decision weights with explicit inputs at native scope boundaries."""

import pytest
from shared.paths import REPO_ROOT
from shared.suite import (
    EconomicScriptFixture,
    read_decision_categories,
    read_text,
    script_block,
)
from shared_utils import iter_statements

_SPENDING = {
    **{
        name: 180
        for name in (
            "CZE_quick_modernization",
            "CZE_research_grants_utility",
            "CZE_research_grants_czech",
            "CZE_research_grants_mbt",
            "CZE_skoda_enyak_iv_development",
        )
    },
    **{
        name: 250
        for name in (
            "CZE_open_planning_phase",
            "CZE_prepare_construction_site",
            "CZE_build_one_kilometer_of_electric_highway",
        )
    },
    **{
        name: 350
        for name in (
            "CZE_gather_funds",
            "CZE_SLO_law_sector_change_the_labor_law",
            "CZE_civilian_investment_in_rural_areas",
            "CZE_infrastructure_of_an_empire",
            "CZE_skoda_learnings",
        )
    },
    "CZE_prepare_zbynek_stanjura_for_new_job": 400,
    **{
        name: 50
        for name in (
            "CZE_SLO_welfare_sector_organize_common_events",
            "CZE_SLO_welfare_sector_increase_culture_expenditure",
            "CZE_AUS_prepare_the_media",
            "CZE_AUS_support_promonarchists",
            "CZE_AUS_reform_one_castle",
        )
    },
    **{
        f"CZE_{stage}_renovation": 200 for stage in ("first", "second", "third", "last")
    },
}
_UNCHANGED = {
    "CZE_change_fuel_injectors": 180,
    "CZE_borrow_state_factory": 150,
    "CZE_construction_site": 350,
    "CZE_additional_laboratory_equipment": 350,
    "CZE_start_with_better_fuel": 350,
    "CZE_thermonuclear_reactor": 350,
    "CZE_czech_railways": 350,
    "CZE_cez_group": 350,
}


@pytest.fixture(scope="module")
def decisions():
    return read_decision_categories(
        REPO_ROOT / "common/decisions",
        tuple(
            ("Czech_Republic.txt", category)
            for category in (
                "CZE_vop_cz_category",
                "CZE_skoda_laboratories_category",
                "CZE_skoda_superb_cars_export_category",
                "CZE_electric_highway_category",
                "CZE_start_selling_state_companies_category",
                "CZE_new_nuclear_power_plant_category",
                "CZE_spolu_government_formation_category",
                "CZE_SLO_czechoslovakia_category",
                "CZE_SLO_slovakian_nuclear_research",
                "CZE_prague_castle_renovation_decisions",
                "CZE_AUS_return_of_archduke",
                "CZE_the_prague_conference_category",
            )
        ),
    )


@pytest.fixture
def economy():
    triggers = read_text(
        REPO_ROOT / "common/scripted_triggers/00_economic_triggers.txt"
    )
    return EconomicScriptFixture(
        {"treasury_rate": -4, "budget_balance_ratio": -0.11},
        predicates={
            "has_active_mission": lambda mission, _: mission
            == "bankruptcy_incoming_collapse"
        },
        triggers={"ai_has_high_deficit": script_block(triggers, "ai_has_high_deficit")},
    )


@pytest.mark.parametrize("name,base", _SPENDING.items())
@pytest.mark.parametrize(
    "rate,ratio,bankrupt,multiplier",
    [
        (0, 0, False, 1),
        (-3, -0.10, False, 1),
        (-3.001, 0, False, 0.5),
        (0, -0.1001, False, 0.5),
        (0, 0, True, 0),
        (-4, -0.11, True, 0),
    ],
)
def test_national_expenses_use_the_taking_countrys_budget(
    decisions, economy, name, base, rate, ratio, bankrupt, multiplier
):
    economy.values.update(treasury_rate=rate, budget_balance_ratio=ratio)
    economy.predicates["has_active_mission"] = lambda mission, _: (
        bankrupt and mission == "bankruptcy_incoming_collapse"
    )
    assert (
        economy.weight(script_block(decisions[name], "ai_will_do")) == base * multiplier
    )


@pytest.mark.parametrize(
    "rate,ratio,bankrupt,expected",
    [
        (0, 0, False, 350),
        (-3, -0.10, False, 350),
        (-3.001, 0, False, 175),
        (0, -0.1001, False, 175),
        (0, 0, True, 0),
        (-4, -0.11, True, 0),
    ],
)
def test_slovak_reactor_uses_its_controllers_budget_not_the_decision_takers(
    decisions, economy, rate, ratio, bankrupt, expected
):
    controller = EconomicScriptFixture(
        {"treasury_rate": rate, "budget_balance_ratio": ratio},
        predicates={
            "has_active_mission": lambda mission, _: bankrupt
            and mission == "bankruptcy_incoming_collapse"
        },
        triggers=economy.triggers,
    )

    def state_scope(value, body):
        assert value is None
        entries = list(iter_statements(body))
        assert len(entries) == 1 and entries[0][0] == "CONTROLLER"
        return controller.condition(script_block(body, "CONTROLLER"))

    economy.predicates["reactor_state"] = state_scope
    decision = decisions["CZE_SLO_begin_construction_of_new_nuclear_reactor"]
    weight = script_block(decision, "ai_will_do")
    assert weight.count("119 =") == 2
    # The fixture cannot parse numeric scope names.
    assert economy.weight(weight.replace("119 =", "reactor_state =")) == expected


@pytest.mark.parametrize("name,base", _UNCHANGED.items())
def test_ringfenced_funds_and_net_revenue_remain_usable_during_collapse(
    decisions, economy, name, base
):
    assert economy.weight(script_block(decisions[name], "ai_will_do")) == base
