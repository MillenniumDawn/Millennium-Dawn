"""Evaluate shared decision weights, not native AI selection or timed effects."""

import pytest
from shared.paths import REPO_ROOT
from shared.suite import EconomicScriptFixture, read_text, script_block
from shared_utils import iter_statements

_AGRICULTURE = "agricultural_district_tax_credits_decision"
_LABOUR = "raise_wages_labour_unions_decision"
_ALLOW_RECRUITS = "allow_foreign_nationals_military_decision"
_REPEAL_RECRUITS = "repeal_foreign_nationals_military_decision"
_PRODUCTION = "encourage_additional_resource_production_decision"
_REGULATIONS = "allow_temporary_cut_backs_on_regulations_decision"
_RICH = "cut_taxes_on_the_rich_decision"
_TAX_RELIGION = "impose_taxes_on_religious_institutions_decision"
_REPEAL_RELIGION = "repeal_taxes_on_religious_institutions_decision"
_PROPAGANDA = "encourage_further_party_propaganda"
_OFFICES = "sell_political_positions_to_the_highest_bidder"
_INDUSTRY = "cut_taxes_industry_decision"
_SMALL_BUSINESS = "raise_wages_small_medium_business_owners_decision"
_SPENDING = "promote_reduced_spending_campaigns"
_RELIGIONS = ("the_clergy", "the_ulema", "wahabi_ulema", "the_priesthood")
_RESOURCES = ("oil", "aluminium", "rubber", "tungsten", "steel", "chromium")
_OPINION_REMEDIES = {
    _AGRICULTURE: ("farmers",),
    _LABOUR: ("labour_unions",),
    _RICH: ("international_bankers", "landowners", "oligarchs"),
    _REPEAL_RELIGION: _RELIGIONS,
    _PROPAGANDA: ("communist_cadres",),
    _INDUSTRY: (
        "defense_industry",
        "maritime_industry",
        "industrial_conglomerates",
        "fossil_fuel_industry",
    ),
    _SMALL_BUSINESS: ("small_medium_business_owners",),
}
_FACTIONS = {faction for factions in _OPINION_REMEDIES.values() for faction in factions}
_CONTEXTS = {
    **{
        name: {f"{factions[0]}_opinion": 49}
        for name, factions in _OPINION_REMEDIES.items()
    },
    _ALLOW_RECRUITS: {},
    _REPEAL_RECRUITS: {},
    _PRODUCTION: {"resource@steel": -1},
    _REGULATIONS: {"treasury_rate": -4},
    _TAX_RELIGION: {
        "treasury_rate": -4,
        **{f"{faction}_opinion": 70 for faction in _RELIGIONS},
    },
    _OFFICES: {"treasury_rate": -4},
    _SPENDING: {"treasury_rate": -1},
}
_COSTLY = (
    _AGRICULTURE,
    _RICH,
    _REPEAL_RELIGION,
    _PROPAGANDA,
    _PRODUCTION,
    _INDUSTRY,
    _SMALL_BUSINESS,
)


@pytest.fixture(scope="module")
def decisions():
    result = {}
    for filename, category in (
        ("Internal Factions.txt", "decision_category_internal_factions"),
        ("00_political_decisions.txt", "generic_coalition_politics_decisions"),
    ):
        source = read_text(REPO_ROOT / "common/decisions" / filename)
        result.update(
            (name, body)
            for name, _, body in iter_statements(script_block(source, category))
            if body is not None
        )
    return result


@pytest.fixture
def economy():
    source = read_text(REPO_ROOT / "common/scripted_triggers/00_economic_triggers.txt")
    return EconomicScriptFixture(
        {
            "treasury_rate": 1,
            "budget_balance_ratio": 0,
            "agriculture_district_total": 1,
            "stability": 0.7,
            "resource_sale_rate": 1,
            "manpower_per_military_factory": 999,
            **{f"{faction}_opinion": 50 for faction in _FACTIONS},
            **{f"resource@{resource}": 10 for resource in _RESOURCES},
            **{f"resource_produced@{resource}": 10 for resource in _RESOURCES},
        },
        predicates={
            "has_idea": lambda idea, _: idea in _FACTIONS
            or idea == "corruption_level_02",
            "has_war": False,
            "has_active_mission": lambda *_: False,
        },
        triggers={
            name: script_block(source, name)
            for name in ("ai_has_deficit", "ai_has_high_deficit", "ai_has_surplus")
        },
    )


def _ready(economy, name):
    economy.values.update(_CONTEXTS[name])
    economy.predicates["has_war"] = name == _ALLOW_RECRUITS


@pytest.mark.parametrize("name", _CONTEXTS)
def test_each_candidate_has_a_positive_weight_in_its_useful_situation(
    decisions, economy, name
):
    _ready(economy, name)
    assert economy.weight(script_block(decisions[name], "ai_will_do")) > 0


@pytest.mark.parametrize(
    "name,faction",
    [
        (name, faction)
        for name, factions in _OPINION_REMEDIES.items()
        for faction in factions
    ],
)
@pytest.mark.parametrize(
    "opinion,present,expected",
    [(49.999, True, 1), (50, True, 0), (0, False, 0)],
)
def test_opinion_remedies_require_an_unhappy_present_faction(
    decisions, economy, name, faction, opinion, present, expected
):
    economy.values[f"{faction}_opinion"] = opinion
    other = next((item for item in _OPINION_REMEDIES[name] if item != faction), None)
    economy.predicates["has_idea"] = lambda idea, _: (
        (present and idea == faction)
        or idea == other
        or idea == "internal_factions_taxing_religious_institutions"
    )
    decision = decisions[name]
    visible = economy.condition(script_block(decision, "visible"))
    weight = economy.weight(script_block(decision, "ai_will_do")) if visible else 0
    assert weight == expected


@pytest.mark.parametrize("name", _COSTLY)
@pytest.mark.parametrize(
    "deficit,bankrupt", [(True, False), (False, True), (True, True)]
)
def test_money_guards_halve_high_deficit_weights_and_block_bankruptcy(
    decisions, economy, name, deficit, bankrupt
):
    _ready(economy, name)
    weights = script_block(decisions[name], "ai_will_do")
    healthy = economy.weight(weights)
    assert healthy > 0
    economy.values["budget_balance_ratio"] = -0.11 if deficit else 0
    economy.predicates["has_active_mission"] = (
        lambda mission, _: bankrupt and mission == "bankruptcy_incoming_collapse"
    )
    assert economy.weight(weights) == (0 if bankrupt else healthy / 2)


@pytest.mark.parametrize("name", [_SPENDING, _OFFICES, _TAX_RELIGION, _REGULATIONS])
def test_fiscal_relief_is_not_blocked_by_bankruptcy(decisions, economy, name):
    _ready(economy, name)
    economy.values.update(treasury_rate=-4, budget_balance_ratio=-0.11)
    economy.predicates["has_active_mission"] = lambda *_: True
    assert economy.weight(script_block(decisions[name], "ai_will_do")) > 0


@pytest.mark.parametrize(
    "name,balance,expected",
    [
        (_SPENDING, -0.05, 0),
        (_SPENDING, -0.051, 10),
        (_OFFICES, -3, 0),
        (_OFFICES, -3.001, 1),
        (_TAX_RELIGION, -3, 0),
        (_TAX_RELIGION, -3.001, 1),
        (_AGRICULTURE, -0.051, 0),
        (_AGRICULTURE, -0.05, 1),
        (_SMALL_BUSINESS, -0.051, 0),
        (_SMALL_BUSINESS, -0.05, 1),
        (_RICH, 0.05, 0),
        (_RICH, 0.051, 1),
        (_INDUSTRY, 0.05, 0),
        (_INDUSTRY, 0.051, 1),
    ],
)
def test_budget_gates_match_existing_deficit_and_surplus_boundaries(
    decisions, economy, name, balance, expected
):
    _ready(economy, name)
    economy.values["treasury_rate"] = balance
    assert economy.weight(script_block(decisions[name], "ai_will_do")) == expected


@pytest.mark.parametrize("level,expected", [(1, 1), (2, 1), (3, 1), (4, 0), (10, 0)])
def test_office_sales_require_low_corruption(decisions, economy, level, expected):
    _ready(economy, _OFFICES)
    economy.predicates["has_idea"] = (
        lambda idea, _: idea == f"corruption_level_{level:02}"
    )
    assert economy.weight(script_block(decisions[_OFFICES], "ai_will_do")) == expected


@pytest.mark.parametrize("resource", _RESOURCES)
@pytest.mark.parametrize(
    "balance,production,expected", [(-1, 1, 1), (0, 1, 0), (-1, 0, 0)]
)
def test_production_needs_a_shortage_of_a_resource_the_country_produces(
    decisions, economy, resource, balance, production, expected
):
    economy.values.update(
        {f"resource@{resource}": balance, f"resource_produced@{resource}": production}
    )
    assert (
        economy.weight(script_block(decisions[_PRODUCTION], "ai_will_do")) == expected
    )


@pytest.mark.parametrize("name", [_PRODUCTION, _REGULATIONS])
@pytest.mark.parametrize("stability,expected", [(0.6, 0), (0.6001, 1)])
def test_resource_measures_require_a_stability_buffer(
    decisions, economy, name, stability, expected
):
    _ready(economy, name)
    economy.values.update(stability=stability, treasury_rate=-1)
    assert economy.weight(script_block(decisions[name], "ai_will_do")) == expected


@pytest.mark.parametrize("income,balance,expected", [(0, -1, 0), (1, 0, 0), (1, -1, 1)])
def test_regulation_cuts_need_export_revenue_and_a_deficit(
    decisions, economy, income, balance, expected
):
    economy.values.update(resource_sale_rate=income, treasury_rate=balance)
    assert (
        economy.weight(script_block(decisions[_REGULATIONS], "ai_will_do")) == expected
    )


@pytest.mark.parametrize("faction", _RELIGIONS)
@pytest.mark.parametrize("other_present", [False, True])
@pytest.mark.parametrize(
    "opinion,stability,expected",
    [(64.999, 0.7, 0), (65, 0.7, 1), (70, 0.6, 0)],
)
def test_religious_taxation_preserves_active_faction_opinion_and_stability(
    decisions, economy, faction, other_present, opinion, stability, expected
):
    economy.values.update(treasury_rate=-4, stability=stability)
    economy.values.update({f"{religion}_opinion": 0 for religion in _RELIGIONS})
    economy.values[f"{faction}_opinion"] = opinion
    other = next(item for item in _RELIGIONS if item != faction)
    economy.values[f"{other}_opinion"] = 70
    economy.predicates["has_idea"] = lambda idea, _: idea == faction or (
        other_present and idea == other
    )
    assert (
        economy.weight(script_block(decisions[_TAX_RELIGION], "ai_will_do")) == expected
    )


@pytest.mark.parametrize("name", [_ALLOW_RECRUITS, _REPEAL_RECRUITS])
@pytest.mark.parametrize(
    "at_war,manpower,allow,repeal",
    [(True, 999.999, 10, 0), (True, 1000, 0, 0), (False, 999, 0, 1)],
)
def test_foreign_recruitment_tracks_wartime_manpower_need(
    decisions, economy, name, at_war, manpower, allow, repeal
):
    economy.predicates["has_war"] = at_war
    economy.values["manpower_per_military_factory"] = manpower
    expected = allow if name == _ALLOW_RECRUITS else repeal
    assert economy.weight(script_block(decisions[name], "ai_will_do")) == expected


@pytest.mark.parametrize(
    "name",
    [
        "fascism_extremist_civil_war",
        "nat_autocracy_extremist_civil_war",
        "monarchist_extremist_civil_war",
        "caliphate_extremist_civil_war",
        "communist_state_extremist_civil_war",
        "neutral_communist_extremist_civil_war",
        "vilayat_e_faqih_extremist_civil_war",
        "leave_UNASUL",
        "remove_usaid",
        "HOL_add_dutchaid",
        "HOL_remove_dutchaid",
        "GEN_remove_saudi_aid",
        "denounce_status_as_the_commonwealth_of_nation_member",
        "GEN_ban_al_jazeera",
        "GEN_allow_al_jazeera",
        "discourage_population_growth_decision",
        "GLOBAL_turkey_annex_nachi_azer",
    ],
)
def test_intentionally_disabled_shared_decisions_stay_disabled(
    decisions, economy, name
):
    assert economy.weight(script_block(decisions[name], "ai_will_do")) == 0
