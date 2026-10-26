"""Source-evaluated cost awareness for Swedish event choices."""

import re

import pytest
from shared.paths import REPO_ROOT
from shared.suite import EconomicScriptFixture, read_text, script_block
from shared_utils import iter_statements, strip_comments
from validate_events import costly_scripted_effects, find_cost_blind_options


@pytest.fixture(scope="module")
def sweden_source():
    return strip_comments(read_text(REPO_ROOT / "events/05_sweden.txt"))


@pytest.fixture(scope="module")
def sweden_events(sweden_source):
    events = {}
    for event_type, _, event in iter_statements(sweden_source):
        if event_type not in {"country_event", "news_event"} or event is None:
            continue
        event_id = next(
            value for key, value, _ in iter_statements(event) if key == "id"
        )
        events[event_id] = event
    return events


@pytest.fixture(scope="module")
def sweden_options(sweden_events):
    options = {}
    for event_id, event in sweden_events.items():
        for key, _, option in iter_statements(event):
            if key != "option" or option is None:
                continue
            name = next(
                value for field, value, _ in iter_statements(option) if field == "name"
            )
            options[name] = (event_id, option)
    return options


def _weight(option, *, bankruptcy=False, deficit=False, stability=0.6, war_support=0.6):
    chance = script_block(option, "ai_chance")
    chance = re.sub(
        r"has_stability < ([0-9.]+)",
        r"check_variable = { fixture_stability < \1 }",
        chance,
    )
    chance = re.sub(
        r"has_war_support < ([0-9.]+)",
        r"check_variable = { fixture_war_support < \1 }",
        chance,
    )
    fixture = EconomicScriptFixture(
        {
            "fixture_stability": stability,
            "fixture_war_support": war_support,
            "interest_rate": 8,
        },
        predicates={
            "has_active_mission": lambda value, _body: (
                bankruptcy and value == "bankruptcy_incoming_collapse"
            ),
            "ai_has_high_deficit": lambda value, _body: deficit and value == "yes",
            "has_idea": lambda value, _body: value == "depression" and False,
            "has_government": lambda value, _body: value == "FROM",
            "is_historical_focus_on": lambda value, _body: value == "yes",
        },
    )
    return fixture.weight(chance)


def test_sweden_playable_costs_have_affordability_aware_weights(sweden_source):
    effects = costly_scripted_effects(
        [
            read_text(path)
            for path in sorted((REPO_ROOT / "common/scripted_effects").glob("*.txt"))
        ]
    )
    findings = find_cost_blind_options(sweden_source, effects, {})
    assert not findings, "\n".join(map(str, findings))


def test_shared_stability_loss_only_penalizes_the_more_expensive_crisis_choice(
    sweden_options,
):
    options = {
        name: sweden_options[name][1]
        for name in ["Sweden.20.o1", "Sweden.20.o2", "Sweden.20.o3"]
    }
    assert _weight(options["Sweden.20.o1"], stability=0.2) == 10
    assert _weight(options["Sweden.20.o2"], stability=0.2) == 8
    assert _weight(options["Sweden.20.o3"], stability=0.6) == 2
    assert _weight(options["Sweden.20.o3"], stability=0.3) == 1
    assert _weight(options["Sweden.20.o3"], stability=0.2) == 0


def test_disabled_political_power_options_remain_disabled(sweden_options):
    for name in ["Sweden.5.o2", "Sweden.6.o2"]:
        assert _weight(sweden_options[name][1]) == 0


def test_stability_and_war_support_losses_lower_the_actual_choice_weight(
    sweden_options,
):
    assert _weight(sweden_options["Sweden.5.o1"][1]) == 10
    assert _weight(sweden_options["Sweden.5.o1"][1], stability=0.3) == 5
    for name in [
        "Sweden_foci.1.o3",
        "Sweden_foci.2.o4",
        "Sweden_foci.3.o4",
        "Sweden_foci.4.o4",
        "Sweden_foci.5.o4",
    ]:
        assert _weight(sweden_options[name][1], war_support=0.4) == 10
        assert _weight(sweden_options[name][1], war_support=0.2) == 5


def _gdp_charges(source):
    charges = []
    statements = list(iter_statements(source))
    for index, (key, _, block) in enumerate(statements):
        if key == "set_temp_variable" and block is not None:
            variable = next(
                (
                    value
                    for name, value, _ in iter_statements(block)
                    if name == "treasury_change"
                ),
                None,
            )
            if variable and variable.endswith(".gdp_per_capita"):
                multiplier_block = next(
                    (
                        nested
                        for name, _, nested in statements[index + 1 :]
                        if name == "multiply_temp_variable"
                    ),
                    None,
                )
                assert multiplier_block is not None
                multiplier = next(
                    (
                        value
                        for name, value, _ in iter_statements(multiplier_block)
                        if name == "treasury_change"
                    ),
                    None,
                )
                assert multiplier is not None
                assert any(
                    name == "modify_treasury_effect"
                    for name, _, _ in statements[index + 2 :]
                )
                charges.append(
                    (variable.removesuffix(".gdp_per_capita"), float(multiplier))
                )
        if block is not None:
            charges.extend(_gdp_charges(block))
    return charges


def _recipient_for_event(option, event_id):
    recipients = [
        scope
        for scope, _, body in iter_statements(option)
        if body is not None
        and any(
            key == "country_event"
            and target is not None
            and ("id", event_id, None) in list(iter_statements(target))
            for key, _, target in iter_statements(body)
        )
    ]
    assert len(recipients) == 1, (event_id, recipients)
    return recipients[0]


def _helicopter_delivery_branches(option):
    branches = {}
    for key, _, branch in iter_statements(option):
        if key != "if" or branch is None:
            continue
        limit = next(
            (body for name, _, body in iter_statements(branch) if name == "limit"),
            None,
        )
        if limit is None:
            continue
        suppliers = [
            tag
            for tag, _, scope in iter_statements(limit)
            if scope is not None
            and ("has_country_flag", "i_like_potato_2", None)
            in list(iter_statements(scope))
        ]
        if suppliers:
            assert len(suppliers) == 1
            branches[suppliers[0]] = branch
    return branches


def test_helicopter_offer_reaches_only_guarded_suppliers(sweden_options):
    request_suppliers = {
        "Sweden_foci.5.o1": "USA",
        "Sweden_foci.5.o2": "SOV",
        "Sweden_foci.5.o3": "FRA",
    }
    for name, supplier in request_suppliers.items():
        assert (
            _recipient_for_event(sweden_options[name][1], "Sweden_foci.5001")
            == supplier
        )

    acceptance = sweden_options["Sweden_foci.5001.o2"][1]
    assert ("set_country_flag", "i_like_potato_2", None) in list(
        iter_statements(acceptance)
    )
    assert _recipient_for_event(acceptance, "Sweden_foci.5002") == "SWE"
    delivery = sweden_options["Sweden_foci.5002.o1"][1]
    # FRA's accepted request sets the FRA flag, but the delayed delivery checks NRY.
    delivery_branches = _helicopter_delivery_branches(delivery)
    assert set(delivery_branches) == {"USA", "SOV", "NRY"}
    reachable_suppliers = set(request_suppliers.values()) & set(delivery_branches)
    assert reachable_suppliers == {"USA", "SOV"}
    assert {
        supplier: set(_gdp_charges(delivery_branches[supplier]))
        for supplier in reachable_suppliers
    } == {
        "USA": {("USA", -0.07)},
        "SOV": {("SOV", -0.07)},
    }


def test_delayed_purchase_charges_use_the_quoted_donor_gdp(sweden_options):
    costs = {
        "Sweden_foci.1002.o1": {("USA", -0.10), ("SOV", -0.10)},
        "Sweden_foci.2002.o1": {
            ("USA", -0.10),
            ("SOV", -0.10),
            ("GER", -0.10),
        },
        "Sweden_foci.3002.o1": {
            ("USA", -0.10),
            ("SOV", -0.10),
            ("FRA", -0.10),
        },
        "Sweden_foci.4002.o1": {
            ("GER", -0.10),
            ("SOV", -0.10),
            ("NRY", -0.10),
        },
        "Sweden_foci.6004.o1": {
            ("GER", -0.15),
            ("SOV", -0.15),
            ("USA", -0.15),
        },
        "Sweden_foci.7004.o1": {
            ("GER", -0.12),
            ("SOV", -0.12),
            ("FIN", -0.12),
        },
    }
    for name, expected in costs.items():
        assert set(_gdp_charges(sweden_options[name][1])) == expected


def test_delayed_gdp_costs_reduce_the_original_request_weights(sweden_options):
    for name in [
        "Sweden_foci.1.o1",
        "Sweden_foci.1.o2",
        "Sweden_foci.2.o1",
        "Sweden_foci.2.o2",
        "Sweden_foci.2.o3",
        "Sweden_foci.3.o1",
        "Sweden_foci.3.o2",
        "Sweden_foci.3.o3",
        "Sweden_foci.4.o1",
        "Sweden_foci.4.o2",
        "Sweden_foci.4.o3",
        "Sweden_foci.5.o1",
        "Sweden_foci.5.o2",
        "Sweden_foci.6.o1",
        "Sweden_foci.6.o2",
        "Sweden_foci.6.o3",
        "Sweden_foci.7.o1",
        "Sweden_foci.7.o2",
        "Sweden_foci.7.o3",
    ]:
        option = sweden_options[name][1]
        assert _weight(option, bankruptcy=True) == _weight(option) * 0.25
        assert _weight(option, deficit=True) == _weight(option) * 0.5


def test_pp_cost_weights_apply_bankruptcy_without_changing_paths(sweden_options):
    assert _weight(sweden_options["Sweden_foci.52.a"][1]) == 70
    assert _weight(sweden_options["Sweden_foci.52.a"][1], bankruptcy=True) == 17.5
    assert _weight(sweden_options["Sweden.300.a"][1]) == 500
    assert _weight(sweden_options["Sweden.300.a"][1], bankruptcy=True) == 125


def test_gdp_cost_weights_keep_cheaper_alternatives_preferred(sweden_options):
    cases = [
        ("Sweden_foci.40.b", "Sweden_foci.40.a", 1, 1),
        ("Sweden_foci.41.c", "Sweden_foci.41.b", 1, 2),
        ("Sweden_foci.42.a", "Sweden_foci.42.b", 4, 1),
        ("Sweden_foci.43.a", "Sweden_foci.43.b", 2, 3),
        ("Sweden_foci.46.a", "Sweden_foci.46.b", 2, 3),
        ("Sweden_Forsvarsbeslutet.2.a", "Sweden_Forsvarsbeslutet.2.c", 3, 1),
        ("Sweden_Forsvarsbeslutet.2.b", "Sweden_Forsvarsbeslutet.2.c", 2, 1),
        ("Sweden_Forsvarsbeslutet.3.a", "Sweden_Forsvarsbeslutet.3.c", 2, 1),
        ("Sweden_Forsvarsbeslutet.3.b", "Sweden_Forsvarsbeslutet.3.c", 3, 1),
        ("Sweden_Forsvarsbeslutet.4.a", "Sweden_Forsvarsbeslutet.4.c", 4, 1),
        ("Sweden_Forsvarsbeslutet.4.b", "Sweden_Forsvarsbeslutet.4.c", 2, 1),
        ("Sweden_Forsvarsbeslutet.10.a", "Sweden_Forsvarsbeslutet.10.b", 4, 2),
    ]
    for dear, cheap, dear_base, cheap_base in cases:
        assert _weight(sweden_options[dear][1], bankruptcy=True) == dear_base * 0.25
        assert _weight(sweden_options[dear][1], deficit=True) == dear_base * 0.5
        assert _weight(sweden_options[cheap][1], bankruptcy=True) == cheap_base
        assert _weight(sweden_options[cheap][1], deficit=True) == cheap_base
