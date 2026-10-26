"""Evaluate Greenland spending weights, not native selection or delayed payments."""

import pytest
from shared.paths import REPO_ROOT
from shared.suite import (
    EconomicScriptFixture,
    read_decision_categories,
    read_text,
    script_block,
)

_PROJECTS = (
    "capital_city_expansion",
    "naval_priority_act",
    "national_commission",
    "project_northern_projection",
    "fort_vortex",
    "glacial_shine",
    "frostbury",
    "fort_seal",
    "southern_interior_basic_roads",
    "southern_interior_improved_roads",
    "great_polar_railway",
    "basic_industrial_jobs",
    "local_food_supply",
    "extensive_geological_surveying",
    "creating_dedicated_mining_operations",
    "regional_economic_sector_synergy",
    "fort_frostfields",
    "frigidville",
    "aurora",
    "snowdenson",
    "blizzards_peak",
    "crystal_flake",
    "snowberry",
    "plateau_interior_basic_roads",
    "plateau_interior_improved_roads",
    "central_arctic_railroad",
    "basic_industrial_jobs_two",
    "local_food_supply_two",
    "extensive_geological_surveying_two",
    "creating_dedicated_mining_operations_two",
    "regional_economic_sector_synergy_two",
)


@pytest.fixture(scope="module")
def decisions():
    return read_decision_categories(
        REPO_ROOT / "common/decisions",
        tuple(
            ("Greenland.txt", category)
            for category in (
                "GRN_national_decisions",
                "GRN_southern_interior_development_decisions",
                "GRN_central_plateau_development_decisions",
            )
        ),
    )


@pytest.mark.parametrize("project", _PROJECTS)
@pytest.mark.parametrize(
    "rate,balance,bankrupt,expected",
    [
        (0, 0, False, 100),
        (-3, -0.10, False, 100),
        (-3.001, 0, False, 50),
        (0, -0.1001, False, 50),
        (0, 0, True, 0),
        (-4, -0.11, True, 0),
    ],
)
def test_project_weights_respond_to_fiscal_distress(
    decisions, project, rate, balance, bankrupt, expected
):
    triggers = read_text(
        REPO_ROOT / "common/scripted_triggers/00_economic_triggers.txt"
    )
    economy = EconomicScriptFixture(
        {"treasury_rate": rate, "budget_balance_ratio": balance},
        predicates={
            "has_active_mission": lambda mission, _: (
                bankrupt and mission == "bankruptcy_incoming_collapse"
            )
        },
        triggers={"ai_has_high_deficit": script_block(triggers, "ai_has_high_deficit")},
    )
    weight = script_block(decisions[f"GRN_decision_{project}"], "ai_will_do")
    assert economy.weight(weight) == expected
