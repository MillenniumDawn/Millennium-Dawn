"""Evaluate Brazilian event AI weights against real fiscal and stability choices."""

import pytest
from shared.paths import REPO_ROOT
from shared.suite import EconomicScriptFixture, read_text, script_block
from shared_utils import iter_statement_ops, iter_statements, strip_comments

_TREASURY_COSTS = [
    ("brazil.28.a", 1),
    ("brazil.42.a", 1),
    ("brazil_flavour_events.7.a", 1),
    ("brazil_amazon.22.a", 1),
    ("brazil_amazon.24.a", 1),
    ("brazil_amazon.25.a", 1),
    ("brazil_flavour_events.9.a", 1),
    ("brazil_flavour_events.11.b", 1),
    ("brazil_amazon.6.b", 5),
    ("brazil_amazon.9.b", 1),
    ("brazil_amazon.13.c", 1),
    ("brazil_amazon.15.b", 1),
]
_BUILDING_COSTS = [
    "brazil_amazon.22.a",
    "brazil_amazon.24.a",
    "brazil_amazon.25.a",
]
_POLITICAL_POWER_COSTS = [
    "brazil_flavour_events.1.b",
    "brazil_flavour_events.4.b",
    "brazil_flavour_events.8.a",
    "brazil_amazon.10.b",
    "brazil_amazon.11.b",
    "brazil_amazon.14.a",
    "brazil_amazon.16.b",
]
_STABILITY_LOSSES = [
    "brazil.3.a",
    "brazil.14.a",
    "brazil.27.b",
    "brazil_flavour_events.4.a",
    "brazil_flavour_events.6.b",
    "brazil_flavour_events.7.b",
    "brazil_flavour_events.8.b",
    "brazil_flavour_events.11.a",
]
_FISCAL_STATES = [
    (False, False, 1),
    (True, False, 0.25),
    (False, True, 0.5),
    (True, True, 0.125),
]


@pytest.fixture(scope="module")
def brazilian_options():
    source = strip_comments(read_text(REPO_ROOT / "events/Brazilian.txt"))
    options = {}
    for key, _, event in iter_statements(source):
        if key != "country_event" or event is None:
            continue
        for option_key, _, option in iter_statements(event):
            if option_key == "option" and option is not None:
                name = next(
                    value
                    for field, value, _ in iter_statements(option)
                    if field == "name"
                )
                options[name] = option
    return options


@pytest.fixture
def economy():
    triggers = read_text(
        REPO_ROOT / "common/scripted_triggers/00_economic_triggers.txt"
    )
    result = EconomicScriptFixture(
        {"treasury_rate": 0, "budget_balance_ratio": 0},
        predicates={
            "has_active_mission": lambda *_: False,
            "has_government": lambda *_: False,
            "has_opinion": lambda *_: False,
        },
        triggers={"ai_has_high_deficit": script_block(triggers, "ai_has_high_deficit")},
    )
    result.predicates.update(
        {scope: lambda _, body: result.condition(body) for scope in ("BRA", "USA")}
    )
    return result


def _set_fiscal_state(economy, bankrupt, deficit):
    economy.values.update(
        treasury_rate=-3.01 if deficit else 0,
        budget_balance_ratio=0,
    )
    economy.predicates["has_active_mission"] = (
        lambda mission, _: bankrupt and mission == "bankruptcy_incoming_collapse"
    )


def _weight(options, economy, name):
    return economy.weight(script_block(options[name], "ai_chance"))


def _has_payment_setter(source, variable, value, effect):
    return _has_setter(source, variable, value) and (
        effect,
        "yes",
        None,
    ) in list(iter_statements(source))


def _has_setter(source, variable, value):
    return any(
        key == "set_temp_variable"
        and body is not None
        and (variable, value, None) in list(iter_statements(body))
        for key, _, body in iter_statements(source)
    )


@pytest.mark.parametrize(("name", "base"), _TREASURY_COSTS)
@pytest.mark.parametrize(("bankrupt", "deficit", "factor"), _FISCAL_STATES)
def test_treasury_cost_weights_respond_to_bankruptcy_and_deficits(
    brazilian_options, economy, name, base, bankrupt, deficit, factor
):
    _set_fiscal_state(economy, bankrupt, deficit)
    assert _weight(brazilian_options, economy, name) == pytest.approx(base * factor)


@pytest.mark.parametrize("name", _BUILDING_COSTS)
def test_charged_building_construction_is_financially_weighted(brazilian_options, name):
    state = script_block(brazilian_options[name], "random_owned_controlled_state")
    construction = script_block(state, "add_building_construction")
    assert ("skip_payment", "1", None) not in list(iter_statements(construction))


@pytest.mark.parametrize("name", _POLITICAL_POWER_COSTS)
@pytest.mark.parametrize("bankrupt", [False, True])
def test_political_power_cost_weights_stay_positive_and_avoid_bankruptcy(
    brazilian_options, economy, name, bankrupt
):
    _set_fiscal_state(economy, bankrupt, False)
    assert _weight(brazilian_options, economy, name) == pytest.approx(
        0.25 if bankrupt else 1
    )


@pytest.mark.parametrize("name", _STABILITY_LOSSES)
def test_stability_losses_are_discounted_when_stability_is_low(brazilian_options, name):
    option = brazilian_options[name]
    assert any(
        key == "add_stability" and value is not None and float(value) < 0
        for key, value, _ in iter_statements(option)
    )
    modifiers = [
        body
        for key, _, body in iter_statements(script_block(option, "ai_chance"))
        if key == "modifier" and body is not None
    ]
    assert any(
        ("factor", "=", "0.5", None) in list(iter_statement_ops(modifier))
        and ("has_stability", "<", "0.4", None) in list(iter_statement_ops(modifier))
        for modifier in modifiers
    )


def test_cost_free_fallback_weights_remain_positive(brazilian_options, economy):
    _set_fiscal_state(economy, True, True)
    for name in ("brazil.28.b", "brazil_flavour_events.9.b"):
        assert _weight(brazilian_options, economy, name) == 1


def test_debt_assistance_keeps_diplomatic_adds_before_cost_factors(
    brazilian_options, economy
):
    economy.predicates["has_opinion"] = lambda *_: True
    _set_fiscal_state(economy, False, False)
    assert _weight(brazilian_options, economy, "brazil.42.a") == 12
    _set_fiscal_state(economy, True, True)
    assert _weight(brazilian_options, economy, "brazil.42.a") == pytest.approx(1.5)


def test_french_refusal_weights_brazils_political_power_cost(
    brazilian_options, economy
):
    _set_fiscal_state(economy, False, False)
    assert _weight(brazilian_options, economy, "brazil.15.b") == 1
    _set_fiscal_state(economy, True, False)
    assert _weight(brazilian_options, economy, "brazil.15.b") == 0.25


def test_delayed_debt_assistance_payment_matches_its_weighted_preview(
    brazilian_options,
):
    preview = script_block(brazilian_options["brazil.42.a"], "effect_tooltip")
    preview_brazil = script_block(preview, "BRA")
    follow_up = brazilian_options["brazil.43.a"]
    payment = script_block(follow_up, "USA")

    assert _has_payment_setter(
        preview, "treasury_change", "-75", "modify_treasury_effect"
    )
    assert _has_payment_setter(
        preview_brazil, "debt_change", "-150", "modify_debt_effect"
    )
    assert _has_payment_setter(
        payment, "treasury_change", "-75", "modify_treasury_effect"
    )
