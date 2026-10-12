"""Source-evaluated AI choices and money previews for Indonesia's event chains."""

from itertools import product

import pytest
from shared.paths import REPO_ROOT
from shared.suite import read_text
from shared_utils import iter_statement_ops, iter_statements, strip_comments
from validate_events import costly_scripted_effects, find_cost_blind_options


@pytest.fixture(scope="module")
def indonesia_source():
    return strip_comments(read_text(REPO_ROOT / "events/Indonesia.txt"))


@pytest.fixture(scope="module")
def indonesia_events(indonesia_source):
    events = {}
    for key, _, body in iter_statements(indonesia_source):
        if key == "country_event" and body is not None:
            event_id = next(
                value for name, value, _ in iter_statements(body) if name == "id"
            )
            events[event_id] = body
    return events


@pytest.fixture(scope="module")
def indonesia_options(indonesia_events):
    options = {}
    for event in indonesia_events.values():
        for key, _, body in iter_statements(event):
            if key == "option" and body is not None:
                name = next(
                    value for key, value, _ in iter_statements(body) if key == "name"
                )
                options[name] = body
    return options


def _child(body, name):
    block = next(block for key, _, block in iter_statements(body) if key == name)
    assert block is not None
    return block


def _matches(modifier, bankruptcy, deficit, stability, opinion, war):
    checks = []
    for key, operator, value, block in iter_statement_ops(modifier):
        if key in {"factor", "add"}:
            continue
        if key == "has_active_mission":
            assert value == "bankruptcy_incoming_collapse"
            checks.append(bankruptcy)
        elif key == "ai_has_high_deficit":
            assert value == "yes"
            checks.append(deficit)
        elif key == "has_stability":
            assert operator == "<" and value is not None
            checks.append(stability < float(value))
        elif key == "has_opinion":
            assert block is not None
            assert ("target", "IND", None) in list(iter_statements(block))
            _, comparison, threshold, _ = next(
                entry for entry in iter_statement_ops(block) if entry[0] == "value"
            )
            assert comparison == ">" and threshold is not None
            checks.append(opinion > float(threshold))
        else:
            assert key == "has_war_with" and value == "IND"
            checks.append(war)
    return all(checks)


def _weight(
    option, bankruptcy=False, deficit=False, stability=0.6, opinion=0, war=False
):
    chance = _child(option, "ai_chance")
    weight = 0.0
    for key, value, block in iter_statements(chance):
        if key == "base":
            assert value is not None
            weight = float(value)
            continue
        assert key == "modifier" and block is not None
        if _matches(block, bankruptcy, deficit, stability, opinion, war):
            for operation, amount, _ in iter_statements(block):
                if operation in {"factor", "add"}:
                    assert amount is not None
                    number = float(amount)
                    weight = (
                        weight * number if operation == "factor" else weight + number
                    )
    return weight


@pytest.mark.parametrize(
    "name",
    [
        "indonesia.5.a",
        "indonesia.6.a",
        "indonesia.8.b",
        "indonesia.9.a",
        "indonesia.69.b",
        "indonesia.37.a",
        "indonesia.67.a",
        "indonesia.678.a",
    ],
)
@pytest.mark.parametrize("state", [{"bankruptcy": True}, {"deficit": True}])
def test_spending_is_less_likely_in_financial_trouble(indonesia_options, name, state):
    option = indonesia_options[name]
    assert 0 < _weight(option, **state) < _weight(option)


def test_political_power_spending_is_less_likely_in_bankruptcy(indonesia_options):
    option = indonesia_options["indonesia.477.a"]
    assert 0 < _weight(option, bankruptcy=True) < _weight(option)


@pytest.mark.parametrize("name", ["indonesia.37.b", "indonesia.477.b"])
def test_stability_losses_are_less_likely_when_unstable(indonesia_options, name):
    option = indonesia_options[name]
    assert 0 < _weight(option, stability=0.2) < _weight(option)


@pytest.mark.parametrize("name", ["indonesia.477.a", "indonesia.678.a"])
def test_stability_gains_are_more_likely_when_unstable(indonesia_options, name):
    option = indonesia_options[name]
    assert _weight(option, stability=0.2) > _weight(option)


@pytest.mark.parametrize("name", ["indonesia.5.a", "indonesia.6.a"])
def test_donor_financial_penalties_apply_after_opinion_bonuses(indonesia_options, name):
    option = indonesia_options[name]
    assert _weight(option, opinion=80) == 60
    assert _weight(option, opinion=80, bankruptcy=True, deficit=True) == 7.5
    assert _weight(option, opinion=80, war=True) == 0


@pytest.mark.parametrize(
    "bankruptcy,deficit,unstable", list(product([False, True], repeat=3))
)
def test_every_reviewed_event_keeps_a_positive_fallback(
    indonesia_options, bankruptcy, deficit, unstable
):
    for event_id in ["5", "6", "8", "9", "69", "37", "477", "67", "678"]:
        weights = [
            _weight(option, bankruptcy, deficit, 0.2 if unstable else 0.6)
            for name, option in indonesia_options.items()
            if name.startswith(f"indonesia.{event_id}.")
        ]
        assert len(weights) == 2
        assert sum(weights) > 0, event_id


def test_cost_validator_evaluates_the_real_indonesia_options(indonesia_source):
    effects = costly_scripted_effects(
        [
            strip_comments(
                read_text(REPO_ROOT / "common/scripted_effects/00_budget_effects.txt")
            )
        ]
    )
    assert find_cost_blind_options(indonesia_source, effects, {}) == []
    unchecked = indonesia_source.replace(
        "modifier = { factor = 0.25 has_active_mission = bankruptcy_incoming_collapse }",
        "",
    ).replace("modifier = { factor = 0.5 ai_has_high_deficit = yes }", "")
    findings = {name for name, *_ in find_cost_blind_options(unchecked, effects, {})}
    assert {"indonesia.5.a", "indonesia.6.a", "indonesia.9.a"} <= findings


def test_reparations_preview_matches_the_actual_charge_without_paying_twice(
    indonesia_options,
):
    acceptance = indonesia_options["indonesia.8.b"]
    preview = _child(acceptance, "effect_tooltip")
    payer = _child(indonesia_options["indonesia.800.a"], "AST")
    for effect in ["set_temp_variable", "add_opinion_modifier"]:
        assert _child(preview, effect).split() == _child(payer, effect).split()
    for body in [preview, payer]:
        assert (
            list(iter_statements(body)).count(("modify_treasury_effect", "yes", None))
            == 1
        )
    assert "indonesia.800" in _child(acceptance, "hidden_effect")
    assert "modify_treasury_effect" not in [
        key for key, _, _ in iter_statements(acceptance)
    ]
    assert "treasury_change = 51.45" in _child(payer, "IND")
