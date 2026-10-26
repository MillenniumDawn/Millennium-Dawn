"""Economic AI weights in India's multi-option events."""

import pytest
from shared.paths import REPO_ROOT
from shared.suite import EconomicScriptFixture, read_text, script_block
from shared_utils import iter_statement_ops, iter_statements, strip_comments

_EVENT_SOURCE = strip_comments(read_text(REPO_ROOT / "events" / "Indian.txt"))
_ECONOMIC_TRIGGERS = read_text(
    REPO_ROOT / "common" / "scripted_triggers" / "00_economic_triggers.txt"
)
_HIGH_DEFICIT = script_block(_ECONOMIC_TRIGGERS, "ai_has_high_deficit")


def _options():
    result = {}
    for key, _, event in iter_statements(_EVENT_SOURCE):
        if key != "country_event" or event is None:
            continue
        for name, _, option in iter_statements(event):
            if name != "option" or option is None:
                continue
            option_name = next(
                value for key, value, _ in iter_statements(option) if key == "name"
            )
            result[option_name] = option
    return result


def _modifier_bodies(option):
    return [
        body
        for key, _, body in iter_statements(script_block(option, "ai_chance"))
        if key == "modifier" and body is not None
    ]


_OPTIONS = _options()


def _economy(bankruptcy=False, deficit=False, opinion=False):
    def has_opinion(_value, block):
        assert block is not None
        assert any(key == "target" for key, _, _ in iter_statements(block))
        return opinion

    economy = EconomicScriptFixture(
        {
            "treasury_rate": -4 if deficit else 0,
            "budget_balance_ratio": 0,
        },
        predicates={
            "has_active_mission": lambda name, _block: bankruptcy
            and name == "bankruptcy_incoming_collapse",
            "has_opinion": has_opinion,
            "RAJ_both_conflict_sides_below_35": lambda _value, _block: False,
            "RAJ_has_severe_naxalite_states_trigger": lambda _value, _block: False,
            "is_historical_focus_on": lambda _value, _block: False,
        },
        triggers={"ai_has_high_deficit": _HIGH_DEFICIT},
    )
    economy.predicates["RAJ"] = lambda _value, block: economy.condition(block)
    return economy


def _weight(option, economy):
    return economy.weight(script_block(option, "ai_chance"))


@pytest.mark.parametrize(
    "name,base",
    [
        ("indian_event.10.a", 50),
        ("indian_event.11.a", 50),
        ("indian_event.18.a", 1),
        ("RAJ_religion_conflict_resolve", 10),
    ],
)
def test_treasury_spending_weights_use_live_financial_triggers(name, base):
    option = _OPTIONS[name]
    assert _weight(option, _economy()) == base
    assert _weight(option, _economy(bankruptcy=True)) == base * 0.25
    assert _weight(option, _economy(deficit=True)) == base * 0.5
    assert _weight(option, _economy(bankruptcy=True, deficit=True)) == base * 0.125


def test_brics_renewable_offer_accounts_for_both_payers():
    option = _OPTIONS["indian_event.27.o1"]
    assert _weight(option, _economy()) == 50
    assert _weight(option, _economy(bankruptcy=True)) == 50 * 0.25**2
    assert _weight(option, _economy(deficit=True)) == 50 * 0.5**2
    assert (
        _weight(option, _economy(bankruptcy=True, deficit=True))
        == 50 * 0.25**2 * 0.5**2
    )


def test_brics_choices_keep_positive_fallback_weights_when_they_cannot_pay():
    for name in ["indian_event.10.b", "indian_event.11.b"]:
        assert _weight(_OPTIONS[name], _economy(bankruptcy=True, deficit=True)) == 1

    assert (
        _weight(_OPTIONS["indian_event.27.o2"], _economy(bankruptcy=True, deficit=True))
        == 20
    )


def test_opinion_bonus_precedes_financial_cost_factors():
    option = _OPTIONS["indian_event.18.a"]
    assert _weight(option, _economy(opinion=True)) == 100
    assert _weight(option, _economy(bankruptcy=True, opinion=True)) == 25
    assert _weight(option, _economy(deficit=True, opinion=True)) == 50


@pytest.mark.parametrize(
    "name,base",
    [
        ("indian_event.13.a", 1),
        ("indian_event.25.a", 1),
        ("RAJ_naxal.14.b", 70),
    ],
)
def test_political_power_spending_only_checks_bankruptcy(name, base):
    option = _options()[name]
    assert _weight(option, _economy()) == base
    assert _weight(option, _economy(bankruptcy=True)) == base * 0.25
    assert _weight(option, _economy(deficit=True)) == base


@pytest.mark.parametrize(
    "name,base",
    [
        ("RAJ_regional.4.a", 30),
        ("RAJ_regional.9.a", 80),
        ("RAJ_regional.12.a", 50),
        ("RAJ_regional.13.c", 30),
        ("RAJ_regional.14.b", 1),
        ("RAJ_regional.15.b", 40),
        ("RAJ_regional.15.c", 30),
        ("RAJ_regional.16.a", 40),
        ("RAJ_regional.21.b", 20),
        ("RAJ_regional.24.b", 40),
    ],
)
def test_regional_political_power_costs_use_bankruptcy_weights(name, base):
    option = _OPTIONS[name]
    assert _weight(option, _economy()) == base
    assert _weight(option, _economy(bankruptcy=True)) == base * 0.25
    assert _weight(option, _economy(deficit=True)) == base


def test_political_power_costs_have_bankruptcy_modifiers():
    names = [
        "indian_event.34.b",
        "indian_event.35.b",
        "indian_event.37.b",
        "indian_event.39.b",
        "RAJ_regional.13.b",
        "pak_raj_border_crisis.4.b",
        "raj_chi_border_crisis.3.b",
    ]
    for name in names:
        assert any(
            ("factor", "0.25", None) in list(iter_statements(modifier))
            and (
                "has_active_mission",
                "bankruptcy_incoming_collapse",
                None,
            )
            in list(iter_statements(modifier))
            for modifier in _modifier_bodies(_OPTIONS[name])
        ), name


def test_export_weights_only_penalize_the_most_expensive_purchase():
    options = _OPTIONS
    for name in ["raj_exports.1.a", "raj_exports.1.c"]:
        assert not any(
            key == "ai_chance" for key, _, _ in iter_statements(options[name])
        )

    expensive = options["raj_exports.1.g"]
    assert _weight(expensive, _economy()) == 1
    assert _weight(expensive, _economy(bankruptcy=True, deficit=True)) == 0.125


def test_stability_and_war_support_loss_factors_follow_the_existing_weights():
    options = _OPTIONS
    expected = {
        "indian_event.5.a": ("has_war_support", "0.5"),
        "indian_event.8.b": ("has_stability", "0.3"),
        "indian_event.22.b": ("has_stability", "0.3"),
        "indian_event.34.b": ("has_stability", "0.5"),
        "indian_event.35.b": ("has_stability", "0.5"),
        "indian_event.37.b": ("has_stability", "0.5"),
        "indian_event.39.b": ("has_stability", "0.5"),
        "RAJ_naxal.14.a": ("has_stability", "0.3"),
        "RAJ_regional.3.b": ("has_stability", "0.3"),
        "RAJ_regional.4.b": ("has_stability", "0.3"),
        "RAJ_regional.7.b": ("has_stability", "0.3"),
        "RAJ_regional.13.a": ("has_stability", "0.3"),
        "RAJ_regional.13.b": ("has_stability", "0.3"),
        "RAJ_regional.14.a": ("has_stability", "0.3"),
        "RAJ_regional.16.b": ("has_stability", "0.3"),
        "RAJ_regional.19.b": ("has_stability", "0.3"),
        "RAJ_regional.20.b": ("has_stability", "0.3"),
        "RAJ_regional.21.a": ("has_stability", "0.3"),
        "pak_raj_border_crisis.4.b": ("has_stability", "0.3"),
        "raj_chi_border_crisis.3.b": ("has_stability", "0.3"),
    }
    for name, (trigger, threshold) in expected.items():
        assert any(
            (trigger, "<", threshold)
            in [
                (key, operator, value)
                for key, operator, value, _ in iter_statement_ops(modifier)
            ]
            for modifier in _modifier_bodies(options[name])
        ), name

    for name in [
        "indian_event.34.b",
        "indian_event.35.b",
        "indian_event.37.b",
        "indian_event.39.b",
    ]:
        modifiers = _modifier_bodies(options[name])
        last_modifier = modifiers[-1]
        assert list(iter_statements(last_modifier))[0][:2] == ("factor", "0")


def test_scripted_construction_costs_are_covered_by_their_choices():
    effects = read_text(
        REPO_ROOT / "common" / "scripted_effects" / "00_scripted_effects.txt"
    )
    network = script_block(effects, "one_random_network_infrastructure")
    assert "treasury_change = -3" in network
    assert ("one_random_network_infrastructure", "yes", None) in list(
        iter_statements(_OPTIONS["indian_event.11.a"])
    )

    renewable = script_block(effects, "one_random_renewable_energy_infra")
    assert "treasury_change = -8.50" in renewable
    option = _OPTIONS["indian_event.27.o1"]
    donor = script_block(option, "RAJ")
    assert (
        list(iter_statements(option)).count(
            ("one_random_renewable_energy_infra", "yes", None)
        )
        == 1
    )
    assert ("one_random_renewable_energy_infra", "yes", None) in list(
        iter_statements(donor)
    )


def test_free_office_construction_skips_the_scripted_treasury_charge():
    option = _OPTIONS["indian_event.9.a"]
    effects = script_block(
        read_text(
            REPO_ROOT / "common" / "scripted_effects" / "00_scripted_effects.txt"
        ),
        "one_office_construction",
    )
    setters = [
        block
        for key, _, block in iter_statements(option)
        if key == "set_temp_variable" and block is not None
    ]
    assert any(
        ("skip_payment", "1", None) in list(iter_statements(setter))
        for setter in setters
    )
    loop = script_block(option, "for_each_scope_loop")
    loop_branch = script_block(loop, "if")
    loop_setters = [
        block
        for key, _, block in iter_statements(loop_branch)
        if key == "set_temp_variable" and block is not None
    ]
    assert any(
        ("skip_payment", "1", None) in list(iter_statements(setter))
        for setter in loop_setters
    )
    charge = next(
        body
        for key, _, body in iter_statements(effects)
        if key == "if" and body is not None and "treasury_change = -12" in body
    )
    assert "check_variable = { skip_payment = 1 }" in charge
