"""Research weight and category contracts, not an HOI4 score simulation."""

from pathlib import Path

import pytest
from shared_utils import iter_statement_ops, iter_statements, read_script

ROOT = Path(__file__).resolve().parents[3]


def _blocks(source):
    blocks = {}
    for name, _, body in iter_statements(source):
        if body is not None:
            assert name not in blocks, name
            blocks[name] = body
    return blocks


@pytest.fixture(scope="module")
def techs():
    result = {}
    for filename in (
        "engineering.txt",
        "industry.txt",
        "naval.txt",
        "fixed_wing.txt",
        "helicopter_techs.txt",
    ):
        source = read_script(
            str(ROOT / "common/technologies" / filename), keep_quotes=True
        )
        definitions = _blocks(_blocks(source)["technologies"])
        assert not result.keys() & definitions.keys()
        result.update(definitions)
    return result


@pytest.fixture(scope="module")
def triggers():
    result = _blocks(
        read_script(str(ROOT / "common/scripted_triggers/00_scripted_triggers.txt"))
    )
    result.update(
        _blocks(
            read_script(
                str(ROOT / "common/scripted_triggers/05_energy_scripted_triggers.txt")
            )
        )
    )
    return result


def _number(value, state):
    assert value is not None
    try:
        return float(value)
    except ValueError:
        return state.get(value, 0)


def _float(value):
    assert value is not None
    return float(value)


def _compare(left, operator, right):
    if operator == "=":
        return left == right
    if operator == ">":
        return left > right
    assert operator == "<", operator
    return left < right


def _matches(body, state, triggers):
    results = []
    for name, operator, scalar, nested in iter_statement_ops(body):
        if name in ("factor", "add", "base", "tooltip"):
            continue
        if name in ("OR", "AND", "NOT", "custom_trigger_tooltip"):
            assert nested is not None
            values = [
                _matches(
                    (
                        f"{key} {op} {{ {block} }}"
                        if block is not None
                        else f"{key} {op} {value}"
                    ),
                    state,
                    triggers,
                )
                for key, op, value, block in iter_statement_ops(nested)
                if key != "tooltip"
            ]
            result = any(values) if name == "OR" else all(values)
            if name == "NOT":
                result = not result
        elif name == "check_variable":
            assert nested is not None
            # The shared lexer does not accept array subscripts as keys.
            arguments = nested.replace(
                "potential_and_current_enemies^num", "enemy_count"
            )
            [(variable, op, value, block)] = list(iter_statement_ops(arguments))
            assert block is None
            result = _compare(state.get(variable, 0), op, _number(value, state))
        elif name in triggers:
            assert scalar in ("yes", "no")
            result = _matches(triggers[name], state, triggers) == (scalar == "yes")
        elif name == "has_idea":
            result = scalar in state.get("ideas", ())
        elif name in ("has_tech", "can_research"):
            result = scalar in state.get(
                "techs" if name == "has_tech" else "researchable", ()
            )
        elif name == "any_owned_state":
            assert nested is not None
            result = any(
                _matches(nested, owned, triggers) for owned in state["owned_states"]
            )
        elif name == "date":
            assert scalar is not None
            date = tuple(int(part) for part in scalar.split("."))
            result = _compare(state["date"], operator, date)
        else:
            assert nested is None, name
            assert name in state, name
            value = scalar
            if scalar in ("yes", "no"):
                value = scalar == "yes"
            elif isinstance(state[name], (int, float)):
                value = _float(scalar)
            result = _compare(state[name], operator, value)
        results.append(result)
    return all(results)


def _weight(tech, state, triggers):
    [body] = [block for key, _, block in iter_statements(tech) if key == "ai_will_do"]
    assert body is not None
    weight = 1.0
    for name, scalar, nested in iter_statements(body):
        if name == "base":
            weight = _float(scalar)
        elif name == "factor":
            weight *= _float(scalar)
        else:
            assert name == "modifier"
            assert nested is not None
            if _matches(nested, state, triggers):
                for key, value, body in iter_statements(nested):
                    if key in ("factor", "add"):
                        assert body is None
                        weight = (
                            weight * _float(value)
                            if key == "factor"
                            else weight + _float(value)
                        )
    return weight


def _state(**overrides):
    state = {
        "date": (2000, 1, 1),
        "has_war": False,
        "threat": 0.0,
        "enemy_count": 0,
        "is_major": False,
        "tag": "TST",
        "original_tag": "TST",
        "gdp_per_capita": 30,
        "population_total_m": 10,
        "num_of_factories": 20,
        "num_of_naval_factories": 1,
        "total_unemployed_percentage_display": 0.10,
        "energy_sum": 100,
        "energy_consumption": 80,
        "agriculture_district_total": 0,
        "agriculture_percent": 0,
        "max_manpower_k": 4000,
        "oil": 0,
        "aluminium": 0,
        "tungsten": 0,
        "steel": 0,
    }
    state.update(overrides)
    return state


@pytest.mark.parametrize(
    "filename", ["MD_generic.txt", "MD_USA.txt", "MD_SOV.txt", "MD_RAJ.txt"]
)
def test_peacetime_profiles_favor_compounding_research_without_dropping_military(
    filename,
):
    profiles = _blocks(read_script(str(ROOT / "common/ai_focuses" / filename)))
    peaceful = next(
        body for name, body in profiles.items() if name.startswith("ai_focus_peaceful")
    )
    research = {
        key: _float(value)
        for key, value, _ in iter_statements(_blocks(peaceful)["research"])
    }
    assert research.get("CAT_computing", 0) > research.get(
        "CAT_information_technology", 0
    )
    assert research["CAT_internet_access"] > 0
    assert research["CAT_robotics"] > 0
    for focus in (
        "military_equipment",
        "military_advancements",
        "defense",
        "aviation",
        "naval",
    ):
        profile = next(
            body
            for name, body in profiles.items()
            if name.startswith(f"ai_focus_{focus}")
        )
        assert any(
            _float(value) > 0
            for _, value, _ in iter_statements(_blocks(profile)["research"])
        )


@pytest.mark.parametrize("tech", [f"construction{number}" for number in range(1, 13)])
@pytest.mark.parametrize("war", [False, True])
@pytest.mark.parametrize("factories", [20, 100, 150])
def test_construction_catch_up_weights_stay_bounded(
    techs, triggers, tech, war, factories
):
    weight = _weight(
        techs[tech],
        _state(date=(2090, 1, 1), has_war=war, num_of_factories=factories),
        triggers,
    )
    assert 0 < weight <= 20


@pytest.mark.parametrize("tech", [f"excavation{number}" for number in range(1, 13)])
@pytest.mark.parametrize("major", [False, True])
def test_excavation_exporter_bonuses_stay_bounded(techs, triggers, tech, major):
    exporter = _state(
        date=(2090, 1, 1),
        is_major=major,
        oil=100,
        ideas={"export_economy"},
    ) | {"resource_produced@oil": 100, "resource_consumed@oil": 10}
    assert 0 < _weight(techs[tech], exporter, triggers) <= 20


@pytest.mark.parametrize("tech", [f"agriculture_{number}" for number in range(1, 14)])
def test_agriculture_uses_farming_and_labor_not_military_manpower(
    techs, triggers, tech
):
    normal = _state(
        date=(2090, 1, 1), agriculture_district_total=20, agriculture_percent=0.5
    )
    scarce = normal | {"total_unemployed_percentage_display": 0.005}
    assert (
        0
        < _weight(techs[tech], normal, triggers)
        < _weight(techs[tech], scarce, triggers)
        <= 20
    )
    assert _weight(techs[tech], normal, triggers) == _weight(
        techs[tech], normal | {"max_manpower_k": 20000}, triggers
    )
    no_farms = _state(date=(2090, 1, 1))
    assert _weight(techs[tech], no_farms, triggers) == _weight(
        techs[tech], no_farms | {"total_unemployed_percentage_display": 0.005}, triggers
    )
    assert _weight(techs[tech], normal, triggers) == _weight(
        techs[tech], scarce | {"population_total_m": 0}, triggers
    )


@pytest.mark.parametrize(
    "tech", [f"artificial_intelligence_{number}" for number in range(1, 4)]
)
@pytest.mark.parametrize("gdp", [7, 20, 50, 90, 100])
def test_early_research_ai_prefers_safe_peace_but_not_threats(
    techs, triggers, tech, gdp
):
    peace = _weight(techs[tech], _state(gdp_per_capita=gdp), triggers)
    war = _weight(techs[tech], _state(gdp_per_capita=gdp, has_war=True), triggers)
    threatened = _weight(
        techs[tech], _state(gdp_per_capita=gdp, enemy_count=1), triggers
    )
    tense = _weight(techs[tech], _state(gdp_per_capita=gdp, threat=0.5), triggers)
    assert peace > war > 0
    assert threatened == tense == war
    assert _weight(techs[tech], _state(gdp_per_capita=5), triggers) == 0
    assert _weight(techs[tech], _state(gdp_per_capita=5, is_major=True), triggers) > 0


@pytest.mark.parametrize("tech", ["robotics_1", "robotics_2"])
def test_automation_responds_to_labor_shortage_without_bypassing_gates(
    techs, triggers, tech
):
    normal = _state(date=(2015, 1, 1))
    scarce = _state(date=(2015, 1, 1), total_unemployed_percentage_display=0.005)
    assert _weight(techs[tech], scarce, triggers) > _weight(
        techs[tech], normal, triggers
    )
    assert _weight(techs[tech], _state(date=(2000, 1, 1)), triggers) == 0
    assert (
        _weight(techs[tech], _state(date=(2015, 1, 1), gdp_per_capita=5), triggers) == 0
    )
    assert (
        _weight(
            techs[tech],
            _state(date=(2015, 1, 1), gdp_per_capita=5, is_major=True),
            triggers,
        )
        > 0
    )
    assert _weight(
        techs[tech],
        _state(
            date=(2015, 1, 1),
            population_total_m=0,
            total_unemployed_percentage_display=0,
        ),
        triggers,
    ) == _weight(techs[tech], normal, triggers)


@pytest.mark.parametrize(
    "tech", [f"electrification_{number}" for number in range(1, 15)]
)
def test_electrification_waits_for_electricity_capacity(techs, triggers, tech):
    surplus = _weight(techs[tech], _state(date=(2090, 1, 1)), triggers)
    deficit = _weight(techs[tech], _state(date=(2090, 1, 1), energy_sum=60), triggers)
    assert 0 < deficit < surplus


@pytest.mark.parametrize(
    "tech",
    ["energy_efficiency"]
    + [f"energy_efficiency{number}" for number in range(2, 9)]
    + [f"energy_efficiency_{number}" for number in range(9, 13)],
)
def test_energy_efficiency_reacts_to_a_shortage(techs, triggers, tech):
    surplus = _weight(techs[tech], _state(date=(2090, 1, 1)), triggers)
    deficit = _weight(techs[tech], _state(date=(2090, 1, 1), energy_sum=60), triggers)
    assert surplus < deficit <= 20


@pytest.mark.parametrize(
    "coasts,dockyards,expected",
    [
        ([True], 1, True),
        ([True, False], 1, True),
        ([False], 1, False),
        ([], 1, False),
        ([True], 0, False),
    ],
)
def test_corvette_gate_requires_some_coast_and_a_dockyard(
    techs, triggers, coasts, dockyards, expected
):
    state = _state(
        owned_states=[{"is_coastal": coast} for coast in coasts],
        num_of_naval_factories=dockyards,
    )
    assert (_weight(techs["corvette_hull_1"], state, triggers) > 0) == expected


@pytest.mark.parametrize("family", ["AS_Fighter", "MR_Fighter", "Strike_fighter"])
def test_older_fighter_tiers_yield_to_available_modern_equipment(
    techs, triggers, family
):
    available = _state(date=(2013, 1, 1), researchable={f"{family}4"})
    unavailable = _state(date=(2013, 1, 1))
    early = _state(date=(2010, 1, 1), researchable={f"{family}4"})
    assert (
        0
        < _weight(techs[f"{family}3"], available, triggers)
        < _weight(techs[f"{family}3"], unavailable, triggers)
    )
    assert _weight(techs[f"{family}3"], early, triggers) == _weight(
        techs[f"{family}3"], unavailable, triggers
    )


@pytest.mark.parametrize("tier", [6, 7])
def test_helicopter_atgm_connectors_keep_useful_descendants_researchable(
    techs, triggers, tier
):
    connector = techs[f"nsb_atgm_tech_{tier}"]
    assert _weight(connector, _state(date=(2090, 1, 1)), triggers) > 0
    successors = set()
    for key, _, body in iter_statements(connector):
        if key == "path":
            assert body is not None
            successors.update(
                value
                for name, value, _ in iter_statements(body)
                if name == "leads_to_tech"
            )
    modules = _blocks(
        _blocks(
            read_script(
                str(ROOT / "common/units/equipment/modules/MD_helicopter_modules.txt")
            )
        )["equipment_modules"]
    )
    for kind in ("multiple", "heavy"):
        successor = f"nsb_{kind}_atgm_tech_{tier}"
        assert successor in successors
        assert _weight(techs[successor], _state(date=(2090, 1, 1)), triggers) > 0
        module = f"helicopter_{kind}_atgm_gen{tier}"
        assert _blocks(techs[successor])["enable_equipment_modules"].split() == [module]
        assert module in modules


def test_context_bonuses_preserve_ahead_of_time_gates(techs, triggers):
    for name, tech in techs.items():
        if not name.startswith(
            (
                "construction",
                "excavation",
                "agriculture",
                "electrification",
                "energy_efficiency",
                "robotics",
            )
        ):
            continue
        [year] = [
            value for key, value, _ in iter_statements(tech) if key == "start_year"
        ]
        year = int(_float(year))
        if year > 2000:
            assert (
                _weight(
                    tech,
                    _state(
                        date=(year - 3, 1, 1),
                        energy_sum=60,
                        total_unemployed_percentage_display=0.005,
                    ),
                    triggers,
                )
                == 0
            ), name
