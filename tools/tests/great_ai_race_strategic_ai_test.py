import copy
import re

import pytest
from great_ai_race_state_model_test import (
    ROOT,
    RaceScript,
    _named_block,
    _parse_race_script,
)

AI_EFFECTS = ROOT / "common/scripted_effects/04_great_ai_race_ai_effects.txt"
AI_TRIGGERS = ROOT / "common/scripted_triggers/MD_great_ai_race_ai_triggers.txt"
AI_STRATEGIES = ROOT / "common/ai_strategy/MD_great_ai_race_ai.txt"
CAPACITY_EFFECTS = (
    ROOT / "common/scripted_effects/01_great_ai_race_capacity_effects.txt"
)
ECONOMIC_EFFECTS = ROOT / "common/scripted_effects/00_economic_system_utilities.txt"
ECONOMIC_TRIGGERS = ROOT / "common/scripted_triggers/00_economic_triggers.txt"


class StrategicRaceScript(RaceScript):
    """Execute planner scripts with explicit native state and energy-owner inputs."""

    def __init__(self, mode="full"):
        super().__init__(mode)
        self.effects.update(_parse_race_script(AI_EFFECTS.read_text(encoding="utf-8")))
        self.effects.update(
            _parse_race_script(CAPACITY_EFFECTS.read_text(encoding="utf-8"))
        )
        self.effects["ai_repay_debt"] = _parse_race_script(
            ECONOMIC_EFFECTS.read_text(encoding="utf-8")
        )["ai_repay_debt"]
        self.triggers.update(
            _parse_race_script(AI_TRIGGERS.read_text(encoding="utf-8"))
        )
        economic_triggers = _parse_race_script(
            ECONOMIC_TRIGGERS.read_text(encoding="utf-8")
        )
        for name in (
            "ai_has_major_economic_problems",
            "can_staff_an_industrial_complex",
            "can_staff_an_microchip_plant",
            "can_staff_an_composite_plant",
        ):
            self.triggers[name] = economic_triggers[name]
        self.owner_calls = []
        self.effects["calculate_energy_use"] = None

    def country(self, identifier, **options):
        options.setdefault("ai", True)
        country = super().country(identifier, **options)
        country["flags"].update(energy_state_bases_initialized=None)
        country["states"] = [
            {
                "non_damaged_building_level@industrial_complex": 20,
                "non_damaged_building_level@internet_station": 10,
                "building_level@industrial_complex": 20,
                "building_level@internet_station": 10,
                "free_slots": {
                    building: 1
                    for building in (
                        "industrial_complex",
                        "internet_station",
                        "fossil_powerplant",
                        "renewable_energy_infra",
                        "nuclear_reactor",
                        "microchip_plant",
                        "composite_plant",
                        "synthetic_refinery",
                        "nuclear_facility",
                    )
                },
            }
        ]
        country["vars"].update(
            energy_balance=2,
            ai_race_sampled_power_multiplier=1,
            amount_research_slots=3,
            num_of_available_civilian_factories=10,
            debt=0,
            debt_ratio=0,
            interest_rate=2,
            total_unemployed_k=200,
            workers_per_civ_fac_display=20,
            workers_per_microchip_plant_display=25,
            workers_per_composite_plant_display=15,
            workers_per_synthetic_refinery_display=25,
            fuel_k=100,
        )
        country["vars"].update(
            {
                "resource@microchips": 5,
                "resource@composites": 2,
                "resource@oil": 2,
                "resource@tungsten": 12,
                "resource@chromium": 9,
                "resource@rubber": 9,
            }
        )
        country["techs"].update(
            {
                "internet1",
                "microchip_production_1",
                "composite_production_1",
                "fuel_silos",
                "reactor1",
            }
        )
        return country

    def value(self, name, identifier):
        if name == "owned_controlled_states":
            states = []
            for index, state in enumerate(self.countries[identifier]["states"]):
                if state.get("owned", True):
                    state_id = -1000 * identifier - index
                    self.countries[state_id] = {
                        "vars": state,
                        "free_slots": state.get("free_slots", {}),
                    }
                    states.append(state_id)
            return states
        if isinstance(name, list) and any(
            key == "every_collection" for key, _, _ in name
        ):
            expanded = []
            for key, comparison, operand in name:
                if key != "every_collection":
                    expanded.append((key, comparison, operand))
                    continue
                data = {key: value for key, _, value in operand}
                assert data["named_collection"] == "controlled_states_collection"
                for state in self.countries[identifier]["states"]:
                    for operation, operator, field in operand:
                        if operation != "named_collection":
                            expanded.append(
                                (operation, operator, str(state.get(field, 0)))
                            )
            return super().value(expanded, identifier)
        return super().value(name, identifier)

    def run(self, name, identifier):
        if name == "calculate_energy_use":
            self.owner_calls.append((name, identifier))
            self.execute(self.effects["ai_race_capture_power_sample"], identifier)
        elif name.startswith("ai_race_ai_") or name in {
            "ai_race_load_stage_requirements",
            "ai_race_refresh_planning_sample",
            "ai_race_refresh_capacity_sample",
            "ai_race_clear_capacity_state",
            "ai_repay_debt",
        }:
            self.execute(self.effects[name], identifier)
        else:
            super().run(name, identifier)


def _planner(*, stage=0, year=2013, month=1):
    race = StrategicRaceScript()
    country = race.country(1)
    race.goto(year, month)
    if stage:
        race.run("ai_race_initialize_country", 1)
        country["vars"]["ai_race_stage"] = stage
    race.run("ai_race_ai_register_country", 1)
    return race, country


def _capacity(race, country, target, ratios=(1, 1, 1, 1, 1, 1)):
    variables = country["vars"]
    race.temps["ai_race_requirement_stage"] = target
    race.run("ai_race_load_stage_requirements", 1)
    amounts = {
        criterion: race.temps[f"ai_race_requirement_{criterion}"] * ratio
        for criterion, ratio in zip(race.criteria, ratios)
    }
    country["states"][0].update(
        {
            "non_damaged_building_level@industrial_complex": amounts["civs"],
            "non_damaged_building_level@internet_station": amounts["network"],
            "building_level@industrial_complex": amounts["civs"],
            "building_level@internet_station": amounts["network"],
        }
    )
    race.temps["ai_race_requirement_stage"] = variables.get("ai_race_stage", 0)
    race.run("ai_race_load_stage_requirements", 1)
    for criterion in ("power", "microchips", "composites", "oil"):
        applied = race.temps[f"ai_race_requirement_{criterion}"]
        variables[f"modifier@ai_race_applied_{criterion}"] = applied
        variables[f"ai_race_demand_{criterion}"] = applied
        if criterion == "power":
            variables["ai_race_accounted_power"] = applied
            variables["energy_balance"] = amounts[criterion] - applied
        else:
            variables[f"resource@{criterion}"] = amounts[criterion] - applied


def _choose_target(race):
    race.run("ai_race_refresh_planning_sample", 1)
    race.run("ai_race_ai_choose_target", 1)


@pytest.mark.parametrize("date,expected", [((2012, 12), []), ((2013, 1), [1])])
def test_discovery_starts_in_2013_without_public_enrollment_or_research(date, expected):
    race = StrategicRaceScript()
    country = race.country(1)
    country["techs"].clear()
    race.goto(*date)
    race.run("ai_race_ai_discover_candidates", 1)
    assert race.globals.get("ai_race_ai_countries", []) == expected
    assert race.globals.get("ai_race_all_initialized", []) == []
    assert "ai_race_stage" not in country["vars"]
    assert not any(key.startswith("ai_race_demand_") for key in country["vars"])
    assert country["techs"] == set()
    assert race.events == race.charges == []


def test_discovery_replays_safely_and_adds_new_candidates_next_year():
    race = StrategicRaceScript()
    race.country(1)
    race.goto(2013, 1)
    race.run("ai_race_ai_discover_candidates", 1)
    race.country(2)
    race.run("ai_race_ai_discover_candidates", 1)
    assert race.globals["ai_race_ai_countries"] == [1]
    race.goto(2014, 1)
    race.run("ai_race_ai_discover_candidates", 1)
    assert race.globals["ai_race_ai_countries"] == [1, 2]


@pytest.mark.parametrize(
    "constraint",
    ["human", "nonexistent", "economy", "collapse", "gdp", "research", "civilians"],
)
def test_discovery_requires_a_viable_country(constraint):
    race = StrategicRaceScript()
    country = race.country(1)
    race.goto(2013, 1)
    if constraint == "human":
        country["ai"] = False
    elif constraint == "nonexistent":
        country["exists"] = False
    elif constraint == "economy":
        country["flags"]["disabled_economic_system"] = None
    elif constraint == "collapse":
        country["flags"]["collapsed_nation"] = None
    elif constraint == "gdp":
        country["vars"]["gdp_total"] = 0
    elif constraint == "research":
        country["vars"]["amount_research_slots"] = 0
    else:
        country["states"][0]["non_damaged_building_level@industrial_complex"] = 9.999
    race.run("ai_race_ai_discover_candidates", 1)
    assert race.globals.get("ai_race_ai_countries", []) == []


def test_discovery_counts_only_controlled_undamaged_civilians_and_keeps_paid_countries():
    race = StrategicRaceScript()
    country = race.country(1)
    country["states"] = [
        {"non_damaged_building_level@industrial_complex": 4},
        {"non_damaged_building_level@industrial_complex": 6},
    ]
    country["vars"]["num_of_civilian_factories"] = 99
    damaged = race.country(2)
    damaged["states"] = []
    damaged["vars"].update(ai_race_stage=2, amount_research_slots=0)
    race.goto(2013, 1)
    race.run("ai_race_ai_discover_candidates", 1)
    assert race.globals["ai_race_ai_countries"] == [1, 2]


@pytest.mark.parametrize(
    "stage,year,progress,target,earliest",
    [
        (0, 2013, 0, 1, 2016),
        (1, 2016, 0, 2, 2019),
        (1, 2020, 0, 2, 2023),
        (2, 2019, 0, 2, 2024),
        (2, 2021, 23, 2, None),
        (2, 2021, 24, 3, 2024),
        (3, 2024, 0, 4, 2025),
    ],
)
def test_target_uses_remaining_paid_work_and_exact_36_month_lookahead(
    stage, year, progress, target, earliest
):
    race, country = _planner(stage=stage, year=year)
    country["vars"]["ai_race_stage_months"] = progress
    _capacity(race, country, max(stage, 1))
    _choose_target(race)
    variables = country["vars"]
    assert variables["ai_race_ai_target_stage"] == target
    assert variables["ai_race_ai_planning_purchase"] == int(target > stage)
    assert variables["ai_race_ai_recovery"] == 0
    if earliest:
        assert variables["ai_race_ai_earliest_entry_month"] == earliest * 12 + 1
    else:
        assert variables["ai_race_ai_earliest_entry_month"] == 2024 * 12 + 2
    assert variables.get("ai_race_stage", 0) == stage
    assert variables["ai_race_stage_months"] == progress


@pytest.mark.parametrize("criterion", range(6))
def test_paid_capacity_damage_selects_recovery_before_expansion(criterion):
    race, country = _planner(stage=1, year=2019)
    ratios = [1] * 6
    ratios[criterion] = 0.9
    _capacity(race, country, 1, ratios)
    _choose_target(race)
    assert country["vars"]["ai_race_ai_target_stage"] == 1
    assert country["vars"]["ai_race_ai_recovery"] == 1
    assert country["vars"]["ai_race_ai_planning_purchase"] == 0
    assert country["vars"]["ai_race_ai_readiness"] == pytest.approx(0.9)


@pytest.mark.parametrize("criterion", ["power", "microchips", "composites"])
@pytest.mark.parametrize("ratio,expected_recovery", [(1.099, 1), (1.1, 0)])
def test_latched_paid_supply_recovers_to_110_percent_before_expansion(
    criterion, ratio, expected_recovery
):
    race, country = _planner(stage=1, year=2019)
    variables = country["vars"]
    variables.update(ai_race_ai_target_stage=1, ai_race_ai_recovery=1)
    variables[f"ai_race_ai_{criterion}_latched"] = 1
    ratios = [1] * 6
    ratios[race.criteria.index(criterion)] = ratio
    _capacity(race, country, 1, ratios)
    _choose_target(race)
    assert variables["ai_race_ai_recovery"] == expected_recovery
    assert variables["ai_race_ai_target_stage"] == 1 + (1 - expected_recovery)


@pytest.mark.parametrize(
    "readiness,target,payment", [(1, 154, 0), (0.75, 209, 550 / 520), (0.749, 0, 0)]
)
def test_savings_include_upfront_and_52_weeks_with_only_prudent_new_installment(
    readiness, target, payment
):
    race, country = _planner()
    _capacity(race, country, 1, [readiness] * 6)
    _choose_target(race)
    race.run("ai_race_ai_calculate_savings", 1)
    assert country["vars"]["ai_race_ai_savings_target"] == pytest.approx(target)
    assert country["vars"]["ai_race_ai_projected_payment"] == pytest.approx(payment)


@pytest.mark.parametrize(
    "debt,weekly,expected_payment",
    [(599.999, 550 / 520, 550 / 520), (600, 10, 0), (0, 550 / 520 - 0.001, 0)],
)
def test_savings_financing_uses_strict_debt_and_nonnegative_weekly_boundaries(
    debt, weekly, expected_payment
):
    race, country = _planner()
    country["vars"].update(debt=debt, treasury_rate=weekly)
    _capacity(race, country, 1, [0.75] * 6)
    _choose_target(race)
    race.run("ai_race_ai_calculate_savings", 1)
    assert country["vars"]["ai_race_ai_projected_payment"] == pytest.approx(
        expected_payment
    )
    assert country["vars"]["ai_race_ai_savings_target"] == pytest.approx(
        154 + expected_payment * 52
    )


def test_weekly_savings_counts_existing_installments_once_and_never_rewrites_ledger():
    race, country = _planner()
    variables = country["vars"]
    immutable = {
        "treasury": 154,
        "debt": 200,
        "ai_race_finance_original_1": 520,
        "ai_race_finance_remaining_1": 519,
        "ai_race_finance_installments_1": 519,
        "ai_race_finance_next_bill_day": 12345,
    }
    variables.update(immutable, display_expense=3)
    _capacity(race, country, 1)
    _choose_target(race)
    race.run("ai_race_ai_refresh_savings", 1)
    assert variables["ai_race_ai_savings_target"] == 206
    before = copy.deepcopy(variables)
    race.run("ai_race_ai_refresh_savings", 1)
    assert variables == before
    assert {key: variables[key] for key in immutable} == immutable
    assert race.charges == race.events == []


def test_weekly_savings_uses_the_new_owner_power_multiplier():
    race, country = _planner()
    _capacity(race, country, 1)
    _choose_target(race)
    race.run("ai_race_ai_refresh_savings", 1)
    assert country["vars"]["ai_race_ai_savings_target"] == 154
    country["vars"]["ai_race_sampled_power_multiplier"] = 2
    race.run("ai_race_ai_refresh_savings", 1)
    assert country["vars"]["ai_race_ai_power_required"] == 4
    assert country["vars"]["ai_race_ai_readiness"] == 0.5
    assert country["vars"]["ai_race_ai_savings_target"] == 0


@pytest.mark.parametrize(
    "treasury,paid", [(153, 0), (154, 0), (158.999, 0), (159, 5), (180, 26)]
)
def test_real_debt_repayment_preserves_race_floor_and_reduces_only_excess(
    treasury, paid
):
    race, country = _planner()
    variables = country["vars"]
    variables.update(treasury=treasury, debt=400, debt_ratio=0.4)
    _capacity(race, country, 1)
    _choose_target(race)
    race.run("ai_race_ai_calculate_savings", 1)
    race.run("ai_repay_debt", 1)
    assert variables["treasury"] == pytest.approx(treasury - paid)
    assert variables["debt"] == pytest.approx(400 - paid)


@pytest.mark.parametrize(
    "reason", ["war", "deficit", "bankruptcy", "human", "disabled", "outcomes_only"]
)
def test_live_expansion_brake_releases_cached_savings_before_next_planner_tick(reason):
    race, country = _planner()
    variables = country["vars"]
    variables.update(
        treasury=200, debt=400, debt_ratio=0.4, ai_race_ai_savings_target=154
    )
    if reason == "war":
        country["war"] = True
    elif reason == "deficit":
        variables["treasury_rate"] = -3.001
    elif reason == "bankruptcy":
        country["missions"].add("bankruptcy_incoming_collapse")
    elif reason == "human":
        country["ai"] = False
    else:
        race.mode = reason
    race.run("ai_repay_debt", 1)
    expected_reserve = 20 + (
        -52 * variables["treasury_rate"] if reason == "deficit" else 0
    )
    assert variables["treasury"] == pytest.approx(expected_reserve)
    assert variables["debt"] == pytest.approx(400 - (200 - expected_reserve))


def _construction_plan(race):
    _choose_target(race)
    race.run("ai_race_ai_cache_construction", 1)
    race.run("ai_race_ai_choose_construction", 1)


@pytest.mark.parametrize(
    "criterion,priority",
    [("civs", 1), ("network", 2), ("power", 3), ("microchips", 4), ("composites", 5)],
)
def test_each_actionable_shortage_can_become_the_construction_priority(
    criterion, priority
):
    race, country = _planner()
    ratios = [1] * 6
    ratios[race.criteria.index(criterion)] = 0.5
    _capacity(race, country, 1, ratios)
    _construction_plan(race)
    assert country["vars"]["ai_race_ai_priority"] == priority


def test_priority_skips_the_worst_shortage_when_no_technology_or_project_route_exists():
    race, country = _planner()
    _capacity(race, country, 1, [1, 0.5, 1, 0.1, 1, 1])
    country["techs"].discard("microchip_production_1")
    country["techs"].discard("microprocessors")
    _construction_plan(race)
    assert country["vars"]["ai_race_ai_priority"] == 2


def test_priority_chooses_largest_normalized_actionable_gap_and_keeps_stable_ties():
    race, country = _planner()
    _capacity(race, country, 1, [0.8, 0.6, 1, 0.5, 0.4, 1])
    _construction_plan(race)
    assert country["vars"]["ai_race_ai_priority"] == 5
    _capacity(race, country, 1, [0.8, 0.6, 1, 0.4, 0.4, 1])
    _construction_plan(race)
    assert country["vars"]["ai_race_ai_priority"] == 4


@pytest.mark.parametrize(
    "criterion,priority", [("power", 3), ("microchips", 4), ("composites", 5)]
)
def test_construction_latch_finishes_headroom_then_stops_at_110_percent(
    criterion, priority
):
    race, country = _planner()
    ratios = [1] * 6
    index = race.criteria.index(criterion)
    for ratio, expected in [(0.9, priority), (1.05, priority), (1.1, 0)]:
        ratios[index] = ratio
        _capacity(race, country, 1, ratios)
        _construction_plan(race)
        assert country["vars"]["ai_race_ai_priority"] == expected
        assert country["vars"][f"ai_race_ai_{criterion}_latched"] == int(expected > 0)


@pytest.mark.parametrize(
    "criterion,field,boundary",
    [
        ("microchips", "resource@tungsten", 3),
        ("microchips", "resource@chromium", 2),
        ("composites", "resource@rubber", 1),
        ("composites", "resource@chromium", 1),
        ("composites", "resource@oil", 1),
    ],
)
def test_factory_feedstock_checks_accept_imported_surplus_at_exact_boundary(
    criterion, field, boundary
):
    race, country = _planner()
    _capacity(race, country, 1)
    _construction_plan(race)
    trigger = race.triggers[f"ai_race_ai_can_add_{criterion}"]
    country["vars"][field] = boundary - 0.001
    assert not race.condition(trigger, 1)
    country["vars"][field] = boundary
    assert race.condition(trigger, 1)


@pytest.mark.parametrize("criterion,workers", [("microchips", 25), ("composites", 15)])
def test_factory_staffing_uses_the_owner_strict_worker_threshold(criterion, workers):
    race, country = _planner()
    _construction_plan(race)
    country["vars"]["total_unemployed_k"] = workers
    trigger = race.triggers[f"ai_race_ai_can_add_{criterion}"]
    assert not race.condition(trigger, 1)
    country["vars"]["total_unemployed_k"] = workers + 0.001
    assert race.condition(trigger, 1)


@pytest.mark.parametrize(
    "criterion,base_power", [("microchips", 0.75), ("composites", 0.8)]
)
def test_factory_requires_sustained_energy_for_the_extra_plant(criterion, base_power):
    race, country = _planner()
    _construction_plan(race)
    trigger = race.triggers[f"ai_race_ai_can_add_{criterion}"]
    country["vars"]["energy_balance"] = base_power - 0.001
    assert not race.condition(trigger, 1)
    country["vars"]["energy_balance"] = base_power
    assert race.condition(trigger, 1)


def test_paid_factory_shortage_plans_power_before_an_unpowerable_new_plant():
    race, country = _planner(stage=1, year=2019)
    _capacity(race, country, 1, [1, 1, 1.1, 0.5, 1, 1])
    _construction_plan(race)
    variables = country["vars"]
    assert variables["ai_race_ai_readiness"] == 0.5
    assert variables["ai_race_ai_power_required"] == 2
    assert variables["ai_race_ai_power_build_required"] == 2.75
    assert variables["ai_race_ai_priority"] == 3


def test_occupied_capacity_counts_for_readiness_but_not_owned_construction_slots():
    race, country = _planner()
    country["states"][0]["owned"] = False
    _construction_plan(race)
    assert country["vars"]["ai_race_ai_readiness"] == 1
    assert country["vars"]["ai_race_ai_slots_civs"] == 0
    assert country["vars"]["ai_race_ai_slots_microchips"] == 0
    assert country["vars"]["ai_race_ai_power_source"] == 0


def test_damage_recovery_uses_existing_buildings_instead_of_exceeding_the_target_count():
    race, country = _planner(stage=1, year=2019)
    _capacity(race, country, 1, [0.9, 0.9, 1, 1, 1, 1])
    country["states"][0].update(
        {"building_level@industrial_complex": 20, "building_level@internet_station": 10}
    )
    _construction_plan(race)
    assert country["vars"]["ai_race_ai_recovery"] == 1
    assert country["vars"]["ai_race_ai_priority"] == 0


@pytest.mark.parametrize("source", [1, 2, 3])
def test_power_source_selects_a_fueled_staffable_option(source):
    race, country = _planner()
    _capacity(race, country, 1, [1, 1, 0.5, 1, 1, 1])
    if source == 2:
        country["vars"]["fuel_k"] = 0
    elif source == 3:
        country["vars"].update(
            {
                "modifier@nuclear_energy_generation_modifier": 2,
                "var_reactor_material_stockpile": 2080,
            }
        )
    _construction_plan(race)
    assert country["vars"]["ai_race_ai_power_source"] == source


def test_balanced_wartime_policy_repairs_paid_supply_but_does_not_expand_civs():
    race, country = _planner(stage=1, year=2019)
    country["war"] = True
    _capacity(race, country, 1, [0.5, 1, 1, 0.75, 1, 1])
    _construction_plan(race)
    assert country["vars"]["ai_race_ai_recovery"] == 1
    assert country["vars"]["ai_race_ai_priority"] == 3
    assert not race.condition(race.triggers["ai_race_ai_expansion_permitted"], 1)
    assert race.condition(race.triggers["ai_race_ai_recovery_permitted"], 1)


@pytest.mark.parametrize(
    "known,year,target,expected",
    [
        (0, 2013, 1, 1),
        (3, 2013, 1, 4),
        (6, 2013, 1, 0),
        (6, 2014, 1, 7),
        (7, 2020, 2, 0),
        (7, 2018, 3, 0),
        (7, 2019, 3, 8),
    ],
)
def test_ai_research_selects_first_missing_required_tech_with_one_year_date_limit(
    known, year, target, expected
):
    race, country = _planner(year=year)
    country["vars"].update(
        ai_race_ai_target_stage=target, ai_race_ai_planning_purchase=1
    )
    country["techs"] = {
        f"artificial_intelligence_{level}" for level in range(1, known + 1)
    }
    country["researchable"] = {
        f"artificial_intelligence_{level}" for level in range(1, 9)
    }
    before = country["techs"].copy()
    race.run("ai_race_ai_choose_research", 1)
    assert country["vars"]["ai_race_ai_research_target"] == expected
    assert country["techs"] == before


def test_research_does_not_skip_a_blocked_prerequisite_to_a_later_available_tech():
    race, country = _planner(year=2020)
    country["vars"].update(ai_race_ai_target_stage=3, ai_race_ai_planning_purchase=1)
    country["techs"].clear()
    country["researchable"] = {"artificial_intelligence_2", "artificial_intelligence_8"}
    race.run("ai_race_ai_choose_research", 1)
    assert country["vars"]["ai_race_ai_research_target"] == 0


@pytest.mark.parametrize("year,expected", [(2013, 0), (2014, 106)])
def test_tokenized_support_research_respects_the_first_missing_year(year, expected):
    race, country = _planner(year=year)
    country["techs"].update(f"construction{level}" for level in range(1, 6))
    country["researchable"] = {"construction6", "construction7"}
    country["vars"]["ai_race_ai_support_tech"] = 0
    race.run("ai_race_ai_choose_construction_tech", 1)
    assert country["vars"]["ai_race_ai_support_tech"] == expected


def test_runtime_research_tokens_are_synchronized():
    research_tokens = set(
        re.findall(r"token:([A-Za-z0-9_]+)", AI_EFFECTS.read_text(encoding="utf-8"))
    )
    registrations = set()
    for path in (ROOT / "common/synchronized_dynamic_tokens").glob("*.txt"):
        registrations.update(
            line.split("#", 1)[0].strip()
            for line in path.read_text(encoding="utf-8").splitlines()
        )
    assert research_tokens
    assert research_tokens <= registrations


def test_support_research_tracks_the_largest_capacity_gap_without_granting_technology():
    race, country = _planner()
    _capacity(race, country, 1, [0.75, 1, 1, 0.5, 1, 1])
    country["researchable"] = {"basic_computing", "construction1"}
    race.run("ai_race_ai_update_plan", 1)
    assert country["vars"]["ai_race_ai_support_need"] == 4
    assert country["vars"]["ai_race_ai_support_tech"] == 201
    assert "basic_computing" not in country["techs"]


@pytest.mark.parametrize("stage", range(1, 5))
@pytest.mark.parametrize(
    "criterion,priority,building",
    [("civs", 1, "industrial_complex"), ("network", 2, "internet_station")],
)
def test_exact_declarative_build_targets_match_shared_stage_requirements(
    stage, criterion, priority, building
):
    race, country = _planner(year=2025)
    _capacity(race, country, stage)
    country["vars"].update(ai_race_ai_target_stage=stage)
    race.run("ai_race_refresh_planning_sample", 1)
    race.run("ai_race_ai_load_target", 1)
    race.run("ai_race_ai_cache_construction", 1)
    country["vars"].update(
        {"ai_race_ai_priority": priority, f"ai_race_ai_{criterion}_total": 0}
    )
    strategies = _parse_race_script(AI_STRATEGIES.read_text(encoding="utf-8"))
    matched = []
    for name, statements in strategies.items():
        if name.startswith(f"ai_race_ai_{criterion}_stage_"):
            data = {key: value for key, _, value in statements}
            if race.condition(data["enable"], 1):
                payload = {key: value for key, _, value in data["ai_strategy"]}
                matched.append(payload)
                assert data["abort_when_not_enabled"] == "yes"
    assert matched == [
        {
            "type": "building_target",
            "id": building,
            "value": str(int(race.temps[f"ai_race_requirement_{criterion}"])),
        }
    ]


def test_every_research_strategy_matches_technology_year_and_has_live_abort_gates():
    strategies = _parse_race_script(AI_STRATEGIES.read_text(encoding="utf-8"))
    industry = "\n".join(
        (ROOT / "common/technologies" / filename).read_text(encoding="utf-8")
        for filename in ("industry.txt", "engineering.txt")
    )
    race, country = _planner(year=2090)
    visited = 0
    for name, statements in strategies.items():
        data = {key: value for key, _, value in statements}
        assert data["abort_when_not_enabled"] == "yes", name
        payload = {key: value for key, _, value in data["ai_strategy"]}
        if payload["type"] != "research_weight_factor":
            continue
        technology = payload["id"]
        start_year = re.search(
            r"\bstart_year\s*=\s*(\d+)", _named_block(industry, technology)
        )
        assert start_year, technology
        country["researchable"] = {technology}
        country["techs"].discard(technology)
        country["vars"].update(ai_race_ai_support_tech=0, ai_race_ai_research_target=0)
        year_limit = None
        for key, _, operand in data["enable"]:
            if key == "check_variable":
                check = {key: value for key, _, value in operand}
                if check.get("var") == "global.year":
                    year_limit = int(check["value"])
                elif operand[0][0] in {
                    "ai_race_ai_research_target",
                    "ai_race_ai_support_tech",
                }:
                    country["vars"][operand[0][0]] = float(operand[0][2])
        assert year_limit == int(start_year[1]) - 1, technology
        race.goto(max(year_limit, 2013), 1)
        assert race.condition(data["enable"], 1), name
        country["war"] = True
        assert not race.condition(data["enable"], 1), name
        country["war"] = False
        visited += 1
    assert visited >= 80


def test_monthly_planner_replay_and_reload_do_not_mutate_paid_state_or_money():
    race, country = _planner(stage=1, year=2019)
    _capacity(race, country, 2)
    country["vars"].update(
        ai_race_stage_months=36,
        ai_race_finance_remaining_1=75,
        ai_race_finance_installments_1=100,
    )
    race.run("ai_race_ai_update_plan", 1)
    before = copy.deepcopy(country["vars"])
    reloaded = copy.deepcopy(race)
    reloaded.run("ai_race_ai_update_plan", 1)
    assert reloaded.countries[1]["vars"] == before
    assert reloaded.charges == reloaded.events == []


@pytest.mark.parametrize("reason", ["human", "nonexistent", "collapse", "economy"])
def test_inoperable_country_resets_preferences_without_erasing_paid_progress(reason):
    race, country = _planner(stage=1, year=2019)
    _capacity(race, country, 1)
    race.run("ai_race_ai_update_plan", 1)
    country["vars"].update(ai_race_stage_months=12, ai_race_finance_remaining_1=75)
    if reason == "human":
        country["ai"] = False
    elif reason == "nonexistent":
        country["exists"] = False
    elif reason == "collapse":
        country["flags"]["collapsed_nation"] = None
    else:
        country["flags"]["disabled_economic_system"] = None
    race.run("ai_race_ai_update_plan", 1)
    variables = country["vars"]
    assert all(
        value == 0
        for name, value in variables.items()
        if name.startswith("ai_race_ai_")
    )
    assert variables["ai_race_stage"] == 1
    assert variables["ai_race_stage_months"] == 12
    assert variables["ai_race_finance_remaining_1"] == 75
    assert 1 in race.globals["ai_race_ai_countries"]


@pytest.mark.parametrize("mode", ["outcomes_only", "disabled"])
def test_mode_cleanup_removes_never_enrolled_preparation_and_preserves_owner_state(
    mode,
):
    race, country = _planner()
    country["vars"]["debt"] = 99
    race.run("ai_race_ai_update_plan", 1)
    assert country["vars"]["ai_race_ai_target_stage"] == 1
    before = {
        name: value
        for name, value in country["vars"].items()
        if not name.startswith("ai_race_")
    }
    race.mode = mode
    race.run(
        (
            "ai_race_refresh_mode_state"
            if mode == "outcomes_only"
            else "ai_race_teardown_global"
        ),
        1,
    )
    assert not any(name.startswith("ai_race_") for name in country["vars"])
    assert {
        name: value
        for name, value in country["vars"].items()
        if not name.startswith("ai_race_")
    } == before
    assert race.globals["ai_race_ai_countries"] == []


def test_terminal_country_only_keeps_capacity_recovery_preferences():
    race, country = _planner(stage=4, year=2025)
    _capacity(race, country, 4)
    race.run("ai_race_ai_update_plan", 1)
    assert country["vars"]["ai_race_ai_priority"] == 0
    assert country["vars"]["ai_race_ai_savings_target"] == 0
    assert country["vars"]["ai_race_ai_research_target"] == 0
    _capacity(race, country, 4, [1, 1, 0.8, 1, 1, 1])
    race.run("ai_race_ai_update_plan", 1)
    assert country["vars"]["ai_race_ai_priority"] == 3
    assert country["vars"]["ai_race_ai_recovery"] == 1
    assert country["vars"]["ai_race_ai_savings_target"] == 0


def test_owner_order_revalues_savings_after_billing_and_before_discretionary_debt():
    on_actions = (ROOT / "common/on_actions/MD_on_actions.txt").read_text(
        encoding="utf-8"
    )
    assert (
        on_actions.index("ai_race_commit_weekly_bill = yes")
        < on_actions.index("ai_race_ai_refresh_savings = yes")
        < on_actions.index("ai_repay_debt = yes")
        < on_actions.index("automated_debt_taker = yes")
    )
    effects = _parse_race_script(
        (
            ROOT / "common/scripted_effects/03_great_ai_race_progression_effects.txt"
        ).read_text(encoding="utf-8")
    )
    monthly = effects["ai_race_run_monthly_work"]
    keys = [key for key, _, _ in monthly]
    assert (
        keys.index("for_each_loop")
        < keys.index("ai_race_ai_refresh_plans")
        < keys.index("if")
    )


def test_planner_economy_guard_matches_the_native_owner_without_a_positive_enable_flag():
    owner = (ROOT / "common/on_actions/MD_on_actions.txt").read_text(encoding="utf-8")
    triggers = AI_TRIGGERS.read_text(encoding="utf-8")
    assert "NOT = { has_country_flag = disabled_economic_system }" in owner
    assert "enabled_economy" not in triggers + AI_EFFECTS.read_text(encoding="utf-8")
    race, country = _planner()
    assert "disabled_economic_system" not in country["flags"]
    assert race.condition(race.triggers["ai_race_ai_expansion_permitted"], 1)
    country["flags"]["disabled_economic_system"] = None
    assert not race.condition(race.triggers["ai_race_ai_expansion_permitted"], 1)
    assert not race.condition(race.triggers["ai_race_ai_country_operable"], 1)
    country["vars"]["ai_race_ai_savings_target"] = 154
    race.run("ai_race_ai_refresh_savings", 1)
    assert country["vars"]["ai_race_ai_savings_target"] == 0


def test_actual_monthly_dispatch_prepares_from_2013_without_starting_the_public_race():
    race = StrategicRaceScript()
    country = race.country(1)
    country["techs"].clear()
    race.goto(2012, 12)
    race.run("ai_race_monthly_dispatch", 1)
    assert race.globals.get("ai_race_ai_countries", []) == []
    race.goto(2013, 1)
    race.run("ai_race_monthly_dispatch", 1)
    assert race.globals["ai_race_ai_countries"] == [1]
    assert country["vars"]["ai_race_ai_target_stage"] == 1
    assert country["vars"]["ai_race_ai_savings_target"] == 154
    assert race.globals.get("ai_race_all_initialized", []) == []
    assert "ai_race_stage" not in country["vars"]
    assert race.charges == race.events == []
    before = copy.deepcopy(country["vars"])
    race.run("ai_race_monthly_dispatch", 1)
    assert country["vars"] == before


def test_planning_sample_never_adds_back_new_demand_before_engine_markers_settle():
    race, country = _planner(stage=1, year=2019)
    _capacity(race, country, 1)
    variables = country["vars"]
    variables.update(ai_race_demand_power=8, ai_race_demand_microchips=20)
    race.run("ai_race_refresh_planning_sample", 1)
    assert variables["ai_race_capacity_settled"] == 0
    assert variables["ai_race_microchips_available"] == 0
    assert variables["ai_race_power_available"] == 2
    variables.update(
        {"modifier@ai_race_applied_microchips": 20, "modifier@ai_race_applied_power": 8}
    )
    variables["ai_race_demand_settle_day"] = race.globals["num_days"] + 1
    race.run("ai_race_refresh_planning_sample", 1)
    assert variables["ai_race_capacity_settled"] == 0
    race.goto(2019, 1, 2)
    race.run("ai_race_refresh_planning_sample", 1)
    assert variables["ai_race_capacity_settled"] == 1
    assert variables["ai_race_microchips_available"] == 20


@pytest.mark.parametrize("project", [False, True])
def test_refinery_repairs_rubber_dependency_for_composites_without_creating_oil(
    project,
):
    race, country = _planner()
    _capacity(race, country, 1, [1, 1, 1, 1, 0.5, 1])
    country["vars"]["resource@rubber"] = 8 if project else 0
    if project:
        country["techs"].discard("composite_production_1")
    country["researchable"] = {"fuel_efficiency"}
    oil = country["vars"]["resource@oil"]
    race.run("ai_race_ai_update_plan", 1)
    variables = country["vars"]
    assert variables["ai_race_ai_priority"] == 5
    assert variables["ai_race_ai_support_tech"] == 321
    assert race.condition(race.triggers["ai_race_ai_refinery_priority_active"], 1)
    assert variables["resource@oil"] == oil
    assert variables["ai_race_ai_oil_ratio"] == 1
    country["vars"]["resource@oil"] = 0
    race.run("ai_race_ai_update_plan", 1)
    assert variables["ai_race_ai_oil_ratio"] == 0
    if not project:
        assert not race.condition(
            race.triggers["ai_race_ai_refinery_priority_active"], 1
        )


def test_refinery_fuel_support_requires_existing_fossil_capacity_and_positive_oil():
    race, country = _planner(stage=1, year=2019)
    _capacity(race, country, 2, [1, 1, 0.625, 1, 1, 1])
    country["vars"].update(fuel_k=1, number_of_fossil_pps=1)
    country["states"][0]["free_slots"].update(
        renewable_energy_infra=0, nuclear_reactor=0
    )
    country["researchable"] = {"fuel_refining"}
    race.run("ai_race_ai_update_plan", 1)
    variables = country["vars"]
    assert variables["ai_race_ai_power_source"] == 0
    assert variables["ai_race_ai_priority"] == 3
    assert variables["ai_race_ai_support_tech"] == 381
    assert race.condition(race.triggers["ai_race_ai_refinery_priority_active"], 1)
    variables["number_of_fossil_pps"] = 0
    assert not race.condition(race.triggers["ai_race_ai_refinery_priority_active"], 1)
    variables["number_of_fossil_pps"] = 1
    variables["resource@oil"] = 0
    assert not race.condition(race.triggers["ai_race_ai_refinery_priority_active"], 1)


@pytest.mark.parametrize(
    "constraint", ["slots", "staff", "power", "technology", "construction"]
)
def test_refinery_cannot_be_selected_without_real_build_capacity(constraint):
    race, country = _planner()
    _capacity(race, country, 1, [1, 1, 1, 1, 0.5, 1])
    country["vars"]["resource@rubber"] = 0
    _construction_plan(race)
    assert race.condition(race.triggers["ai_race_ai_refinery_priority_active"], 1)
    variables = country["vars"]
    if constraint == "slots":
        variables["ai_race_ai_slots_refinery"] = 0
    elif constraint == "staff":
        variables["total_unemployed_k"] = 25
    elif constraint == "power":
        variables["energy_balance"] = 0.199
    elif constraint == "technology":
        country["techs"].discard("fuel_silos")
    else:
        variables["num_of_available_civilian_factories"] = 0
    assert not race.condition(race.triggers["ai_race_ai_refinery_priority_active"], 1)


@pytest.mark.parametrize("stage,weight", [(0, "25"), (1, "50")])
def test_refinery_strategy_uses_prepare_or_recovery_weight_and_aborts_for_humans(
    stage, weight
):
    race, country = _planner(stage=stage, year=2019)
    _capacity(race, country, 1, [1, 1, 1.5, 1, 0.5, 2])
    country["vars"]["resource@rubber"] = 0
    country["war"] = bool(stage)
    race.run("ai_race_ai_update_plan", 1)
    strategies = _parse_race_script(AI_STRATEGIES.read_text(encoding="utf-8"))
    refinery = [
        dict((key, value) for key, _, value in strategies[name])
        for name in ("ai_race_ai_prepare_refinery", "ai_race_ai_recover_refinery")
    ]
    active = [entry for entry in refinery if race.condition(entry["enable"], 1)]
    assert len(active) == 1
    assert dict((key, value) for key, _, value in active[0]["ai_strategy"]) == {
        "type": "build_building",
        "id": "synthetic_refinery",
        "value": weight,
    }
    country["ai"] = False
    assert not any(race.condition(entry["enable"], 1) for entry in refinery)


def test_wartime_support_research_skips_civilian_expansion_for_paid_material_recovery():
    race, country = _planner(stage=1, year=2019)
    _capacity(race, country, 1, [0.25, 0.25, 1.5, 0.5, 1, 1])
    country["war"] = True
    country["researchable"] = {"construction1", "internet2", "basic_computing"}
    race.run("ai_race_ai_update_plan", 1)
    assert country["vars"]["ai_race_ai_support_need"] == 4
    assert country["vars"]["ai_race_ai_support_tech"] == 201
    assert country["vars"]["ai_race_ai_research_target"] == 0
    assert country["vars"]["ai_race_ai_savings_target"] == 0
