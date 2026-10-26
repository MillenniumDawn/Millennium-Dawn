"""Evaluate Hezbollah spending weights, not native selection or timed effects."""

import pytest
from shared.paths import REPO_ROOT
from shared.suite import (
    EconomicScriptFixture,
    read_decision_categories,
    read_text,
    script_block,
)

_SPENDING = {
    **{
        f"{action}_{target}": 1
        for action in (
            "HEZ_sabotage_the_jewish_sectors",
            "deals_with_drug_cartels",
            "support_anti_zionist_parties",
        )
        for target in ("arg", "bra", "col", "VEN", "MEX")
    },
    **{
        f"HEZ_weapon_raidings_{target}": 1
        for target in ("LBA", "SUD", "NIG", "EGY", "CHA")
    },
    "destabilize_the_us": 20,
    "kill_rushdie": 100,
    "smuggle_weapons_from_south_sudanese_rebillions": 1,
    "smuggle_fuel_from_lybia": 1,
    "smuggle_fuel_from_egypt": 1,
    "critsize_the_muslim_brotherhood_in_egypt": 1,
    "question_the_disappearance_of_musa_al_sadr_in_libyan_government": 1,
    "HEZ_weapons_from_iran": 1,
    "HEZ_our_funds_for_the_iraqi_people": 1,
    "HEZ_sabotage_wahhabi_schools": 1,
    "HEZ_fund_protests_against_wahabbis_in_sanaa": 1,
    "HEZ_infrastructure_in_saadaa": 1,
    "HEZ_fund_houthi_propaganda": 1,
    "HEZ_fund_propaganda_for_badr": 1,
    "HEZ_weapons_for_the_resistance": 1,
    "HEZ_the_might_of_muqawimat": 1,
}


@pytest.fixture(scope="module")
def decisions():
    return read_decision_categories(
        REPO_ROOT / "common/decisions",
        tuple(
            ("Hezbollah.txt", category)
            for category in (
                "HEZ_our_step_in_latin_america_decisions",
                "HEZ_assassination_of_salman_rushdie",
                "HEZ_our_boots_on_africa_decisions",
                "HEZ_missions_in_the_middle_east_decisions",
            )
        ),
    )


@pytest.mark.parametrize("name,base", _SPENDING.items())
@pytest.mark.parametrize(
    "threat,rate,balance,bankrupt,factor",
    [
        (0.091, 0, 0, False, 1),
        (0.091, -3, -0.10, False, 1),
        (0.091, -3.001, 0, False, 0.5),
        (0.091, 0, -0.1001, False, 0.5),
        (0.091, 0, 0, True, 0),
        (0.091, -4, -0.11, True, 0),
        (0.09, 0, 0, False, 0),
    ],
)
def test_spending_weights_keep_the_threat_gate_and_respond_to_finances(
    decisions, name, base, threat, rate, balance, bankrupt, factor
):
    source = read_text(REPO_ROOT / "common/scripted_triggers/00_economic_triggers.txt")
    economy = EconomicScriptFixture(
        {"threat": threat, "treasury_rate": rate, "budget_balance_ratio": balance},
        predicates={
            "has_active_mission": lambda mission, _: (
                bankrupt and mission == "bankruptcy_incoming_collapse"
            )
        },
        triggers={"ai_has_high_deficit": script_block(source, "ai_has_high_deficit")},
    )
    assert economy.weight(script_block(decisions[name], "ai_will_do")) == base * factor
