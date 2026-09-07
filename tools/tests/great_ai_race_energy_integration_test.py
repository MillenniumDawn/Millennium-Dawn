import pytest
from great_ai_race_state_model_test import ROOT, _named_block, _parse_race_script
from great_ai_race_strategic_ai_test import StrategicRaceScript

ENERGY_TRIGGERS = ROOT / "common/scripted_triggers/MD_great_ai_race_energy_triggers.txt"
DIPLOMACY = (
    ROOT / "common/scripted_diplomatic_actions/00_scripted_diplomatic_actions.txt"
)
ENERGY_GUI = ROOT / "common/scripted_guis/01_energy_gui.txt"
MICROCHIPS = ROOT / "common/scripted_effects/00_microchip_effects.txt"


def _body(statements, name):
    return next(value for key, _, value in statements if key == name)


def _contains(statements, token):
    for key, _, value in statements:
        if key == token or value == token:
            return True
        if isinstance(value, list) and _contains(value, token):
            return True
    return False


def _modifier(statements, token):
    matches = [
        value
        for key, _, value in statements
        if key == "modifier" and _contains(value, token)
    ]
    assert len(matches) == 1
    return [entry for entry in matches[0] if entry[0] not in {"add", "factor"}]


class EnergyRaceScript(StrategicRaceScript):
    """Exercise owner guards with explicit fuel and diplomatic sender fixtures."""

    def __init__(self, mode="full"):
        super().__init__(mode)
        self.triggers.update(
            _parse_race_script(ENERGY_TRIGGERS.read_text(encoding="utf-8"))
        )

    def condition(self, statements, identifier):
        values = self.countries[identifier]["vars"]
        results = []
        for key, comparison, operand in statements:
            if key == "ROOT":
                result = self.condition(operand, identifier)
            elif key == "set_temp_variable":
                self.execute([(key, comparison, operand)], identifier)
                result = True
            elif key == "has_fuel":
                result = self.comparisons[comparison](
                    values.get("fuel", 0), self.value(operand, identifier)
                )
            elif key in {"has_nuclear_reactors", "has_enrichment_facilities"}:
                field = (
                    "nuclear_reactors"
                    if key == "has_nuclear_reactors"
                    else "enrichment_facilities"
                )
                result = (values.get(field, 0) > 0) == (operand == "yes")
            elif key == "check_expr":
                math = [entry for entry in operand if entry[0] not in self.comparisons]
                result = all(
                    self.comparisons[operation](
                        self.value(math, identifier),
                        self.value(limit[0][2], identifier),
                    )
                    for operation, _, limit in operand
                    if operation in self.comparisons
                )
            else:
                result = super().condition([(key, comparison, operand)], identifier)
            results.append(result)
        return all(results)


def _recovering(mode="full"):
    race = EnergyRaceScript(mode)
    country = race.country(1)
    country["vars"].update(
        ai_race_ai_target_stage=1,
        ai_race_ai_recovery=1,
        ai_race_stage=1,
        ai_race_current_power_ratio=0.5,
        number_of_fossil_pps=1,
        nuclear_reactors=1,
        nuclear_fuel_consumption=10,
        total_nuclear_reactor_fuel_production=0,
        var_reactor_material_stockpile=40,
        fuel=0,
    )
    race.goto(2016, 1)
    return race, country


@pytest.mark.parametrize("imports,expected_reduction", [(0, 20), (3, 0)])
def test_delivered_tungsten_prevents_the_actual_microchip_shutdown(
    imports, expected_reduction
):
    race, country = _recovering()
    owner = _parse_race_script(MICROCHIPS.read_text(encoding="utf-8"))[
        "microchip_update"
    ]
    outer = _body(owner, "if")
    shutdown = next(
        entry
        for entry in outer
        if entry[0] == "if" and _contains(entry[2], "resource_produced@tungsten")
    )
    country["vars"].update(
        {
            "resource_produced@microchips": 20,
            "resource_produced@tungsten": 0,
            "resource_imported@tungsten": imports,
            "resource_produced@chromium": 2,
            "resource_imported@chromium": 0,
            "country_microchip_production_var": 0,
        }
    )
    race.execute([shutdown], 1)
    assert country["vars"]["country_microchip_production_var"] == expected_reduction


@pytest.mark.parametrize(
    "treasury,bankrupt,expected",
    [(0.099, False, True), (0.1, False, False), (10, True, True)],
)
def test_fuel_ai_cannot_bypass_the_existing_purchase_cost(treasury, bankrupt, expected):
    race, country = _recovering()
    country["vars"]["treasury"] = treasury
    if bankrupt:
        country["missions"].add("bankruptcy_incoming_collapse")
    weights = _parse_race_script(
        _named_block(ENERGY_GUI.read_text(encoding="utf-8"), "ai_weights")
    )["ai_weights"]
    button = _body(weights, "buy_fuel_for_money_button_click")
    assert (
        race.condition(_modifier(_body(button, "ai_will_do"), "treasury"), 1)
        is expected
    )


@pytest.mark.parametrize("plants", [0, 1])
@pytest.mark.parametrize("fuel", [399999, 400000, 500000, 999999, 1000000])
def test_fossil_recovery_uses_owner_plant_count_through_the_market_purchase_range(
    plants, fuel
):
    race, country = _recovering()
    country["vars"].update(number_of_fossil_pps=plants, fuel=fuel)
    assert "fossil_powerplants" not in country["vars"]
    assert race.condition([("ai_race_ai_needs_fossil_fuel", "=", "yes")], 1) is (
        plants > 0 and fuel < 1000000
    )


@pytest.mark.parametrize("mode", ["full", "outcomes_only", "disabled"])
def test_power_recovery_preferences_obey_modes_and_fuel_cooldown(mode):
    race, country = _recovering(mode)
    assert race.condition([("ai_race_ai_needs_fossil_fuel", "=", "yes")], 1) is (
        mode == "full"
    )
    country["flags"]["recently_bought_fuel"] = None
    assert not race.condition([("ai_race_ai_needs_fossil_fuel", "=", "yes")], 1)


@pytest.mark.parametrize(
    "weeks,expected", [(0, False), (4, False), (26, False), (27, True)]
)
def test_reactor_stockpile_guard_does_not_suppress_urgent_purchases(weeks, expected):
    race, country = _recovering()
    country["vars"]["var_reactor_material_stockpile"] = weeks * 10
    action = _parse_race_script(
        _named_block(
            DIPLOMACY.read_text(encoding="utf-8"), "purchase_reactor_grade_material"
        )
    )["purchase_reactor_grade_material"]
    assert race.condition(_modifier(_body(action, "ai_desire"), "26"), 1) is expected


@pytest.mark.parametrize(
    "mode,production,expected",
    [("full", 0, False), ("full", 10, True), ("outcomes_only", 0, True)],
)
def test_insufficient_enrichment_can_use_the_existing_reactor_market(
    mode, production, expected
):
    race, country = _recovering(mode)
    country["vars"].update(
        enrichment_facilities=1, total_nuclear_reactor_fuel_production=production
    )
    action = _parse_race_script(
        _named_block(
            DIPLOMACY.read_text(encoding="utf-8"), "purchase_reactor_grade_material"
        )
    )["purchase_reactor_grade_material"]
    assert (
        race.condition(
            _modifier(_body(action, "ai_desire"), "has_enrichment_facilities"), 1
        )
        is expected
    )


def test_reactor_recovery_checks_zero_consumption_before_division():
    race, country = _recovering()
    country["vars"]["nuclear_fuel_consumption"] = 0
    assert not race.condition([("ai_race_ai_needs_reactor_material", "=", "yes")], 1)


@pytest.mark.parametrize(
    "stockpile,expected", [(79.999, True), (80, False), (80.001, False)]
)
def test_reactor_recovery_recalculates_threshold_without_changing_saved_state(
    stockpile, expected
):
    race, country = _recovering()
    country["vars"]["var_reactor_material_stockpile"] = stockpile
    before = country["vars"].copy()
    race.temps["ai_race_ai_reactor_material_threshold"] = 9999
    assert (
        race.condition([("ai_race_ai_needs_reactor_material", "=", "yes")], 1)
        is expected
    )
    assert country["vars"] == before

    country["vars"]["nuclear_fuel_consumption"] = 20
    assert race.condition([("ai_race_ai_needs_reactor_material", "=", "yes")], 1)
    assert race.temps["ai_race_ai_reactor_material_threshold"] == 160


@pytest.mark.parametrize(
    "balance,applied,battery,curtailed,expected",
    [(-2, 0, 10, 0, 0), (20, 0, 0, 20, 20), (2, 8, 0, 0, 10)],
)
def test_planning_power_uses_only_the_owner_balance_and_represented_demand(
    balance, applied, battery, curtailed, expected
):
    race = EnergyRaceScript()
    country = race.country(1)
    country["vars"].update(
        ai_race_ai_target_stage=1,
        energy_balance=balance,
        ai_race_accounted_power=applied,
        energy_withdrawn_from_battery=battery,
        free_fossil_powerplants_power=curtailed,
        ai_race_ai_required_power=60,
    )
    race.run("ai_race_refresh_planning_sample", 1)
    assert country["vars"]["ai_race_power_available"] == expected
    assert "ai_race_stage" not in country["vars"]
    assert not any(key.startswith("ai_race_demand_") for key in country["vars"])
    assert race.events == race.charges == []
