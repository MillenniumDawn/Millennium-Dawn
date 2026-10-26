"""Evaluate Bosnia's AI event weights against financial, stability and path state."""

import pytest
from shared.paths import REPO_ROOT
from shared.suite import EconomicScriptFixture, read_text, script_block
from shared_utils import iter_statement_ops, iter_statements, strip_comments
from validate_events import costly_scripted_effects, find_cost_blind_options

_BOSNIA_SOURCE = strip_comments(read_text(REPO_ROOT / "events/bosnia_events.txt"))
_BUDGET_EFFECTS = costly_scripted_effects(
    [
        strip_comments(
            read_text(REPO_ROOT / "common/scripted_effects/00_budget_effects.txt")
        )
    ]
)

# option: healthy weight, with no BOS_a_*_is_in_power flag set (2x NOT forms, 1x
# otherwise). The distressed column values are healthy * 0.25.
_STABILITY_LOSSES = {
    "BOS_political.26.b": 40,
    "BOS_political.38.b": 40,
    "BOS_political.43.b": 30,
    "BOS_political.44.b": 60,
    "BOS_political.47.b": 45,
    "BOS_political.48.b": 50,
    "BOS_political.54.b": 55,
    "BOS_political.58.a": 60,
    "BOS_political.58.b": 40,
    "BOS_political.59.a": 55,
    "BOS_political.59.b": 45,
    "BOS_political.67.a": 70,
    "BOS_political.69.b": 50,
    "BOS_political.70.a": 50,
    "BOS_political.71.a": 50,
    "BOS_political.74.b": 40,
    "BOS_political.77.a": 60,
}
_POWER_SPENDING = {
    "BOS_political.41.b": 35,
    "BOS_political.44.a": 40,
    "BOS_political.45.a": 45,
    "BOS_political.47.a": 55,
    "BOS_political.48.a": 50,
    "BOS_political.49.b": 60,
    "BOS_political.50.a": 60,
    "BOS_political.53.b": 40,
    "BOS_political.64.b": 30,
    "BOS_political.67.b": 65,
    "BOS_political.69.a": 50,
    "BOS_political.70.b": 50,
    "BOS_political.71.b": 50,
    "BOS_political.73.b": 60,
    "BOS_political.74.a": 60,
}
_TREASURY_SPENDING = {
    "BOS_events.56.a": 55,
    "BOS_events.57.a": 55,
    "BOS_events.58.a": 55,
    "BOS_events.63.a": 70,
    "BOS_political.60.a": 60,
    "BOS_political.79.b": 35,
}
_TREASURY_SPECIAL_CASES = {
    "BOS_events.56.c": (60, "BOS_events.56.b", False),
    "BOS_events.57.c": (60, "BOS_events.57.b", False),
    "BOS_political.58.b": (40, None, True),
    "BOS_political.59.b": (45, None, True),
}
_AUDITED_EVENTS = (
    "BOS_events.56",
    "BOS_events.57",
    "BOS_events.58",
    "BOS_events.62",
    "BOS_events.63",
    "BOS_political.26",
    "BOS_political.38",
    "BOS_political.41",
    "BOS_political.43",
    "BOS_political.44",
    "BOS_political.45",
    "BOS_political.47",
    "BOS_political.48",
    "BOS_political.49",
    "BOS_political.50",
    "BOS_political.53",
    "BOS_political.54",
    "BOS_political.58",
    "BOS_political.59",
    "BOS_political.60",
    "BOS_political.64",
    "BOS_political.67",
    "BOS_political.69",
    "BOS_political.70",
    "BOS_political.71",
    "BOS_political.73",
    "BOS_political.74",
    "BOS_political.77",
    "BOS_political.79",
)


def _evaluable(chance):
    """Adapt scopes and stability checks for the shared fixture's supported inputs."""

    def normalize(source):
        statements = []
        for key, comparison, scalar, body in iter_statement_ops(source):
            if key == "FROM" and body is not None:
                for (
                    scoped_key,
                    scoped_comparison,
                    scoped_scalar,
                    scoped_body,
                ) in iter_statement_ops(body):
                    if scoped_key == "has_war_support" and scoped_body is None:
                        statements.append(
                            "check_variable = { "
                            f"from_has_war_support {scoped_comparison} {scoped_scalar} }}"
                        )
                    else:
                        statements.append(
                            f'from_{scoped_key} {scoped_comparison} "{scoped_scalar}"'
                        )
            elif key == "has_stability" and body is None:
                statements.append(
                    f"check_variable = {{ has_stability {comparison} {scalar} }}"
                )
            elif body is not None:
                statements.append(f"{key} {comparison} {{ {normalize(body)} }}")
            else:
                statements.append(f'{key} {comparison} "{scalar}"')
        return " ".join(statements)

    return normalize(chance)


def _weight(
    option,
    *,
    bankrupt=False,
    deficit=False,
    stability=0.6,
    east=False,
    treasury=10,
    payer_bankrupt=False,
    payer_deficit=False,
    payer_war_support=0.6,
):
    fixture = EconomicScriptFixture(
        {
            "has_stability": stability,
            "treasury": treasury,
            "from_has_war_support": payer_war_support,
        },
        predicates={
            "has_active_mission": lambda mission, _: (
                mission == "bankruptcy_incoming_collapse" and bankrupt
            ),
            "ai_has_high_deficit": deficit,
            "from_has_active_mission": lambda mission, _: (
                mission == "bankruptcy_incoming_collapse" and payer_bankrupt
            ),
            "from_ai_has_high_deficit": payer_deficit,
            "has_completed_focus": lambda focus, _: (
                focus == "BOS_east_energy_partnership" and east
            ),
            "has_country_flag": lambda flag, _: False,
            "has_opinion": lambda _value, _body: False,
            "BOS_srpska_attitude_hostile_trigger": False,
        },
    )
    return fixture.weight(_evaluable(script_block(option, "ai_chance")))


def _options(source):
    options = {}
    for key, _, event in iter_statements(source):
        if key != "country_event" or event is None:
            continue
        for child, _, body in iter_statements(event):
            if child != "option" or body is None:
                continue
            name = next(
                value for key, value, _ in iter_statements(body) if key == "name"
            )
            options[name] = body
    return options


def _without_modifier(source, name, removed):
    option = _options(source)[name]
    chance = script_block(option, "ai_chance")
    changed_chance = chance.replace(removed, "", 1)
    assert changed_chance != chance
    changed_option = option.replace(chance, changed_chance, 1)
    return source.replace(option, changed_option, 1)


@pytest.fixture(scope="module")
def bosnia_options():
    return _options(_BOSNIA_SOURCE)


@pytest.mark.parametrize("distress", [dict(bankrupt=True), dict(deficit=True)])
def test_treasury_spending_discounts_financial_distress(bosnia_options, distress):
    for name, base in _TREASURY_SPENDING.items():
        option = bosnia_options[name]
        assert _weight(option) == base
        assert _weight(option, **distress) == base * (
            0.25 if "bankrupt" in distress else 0.5
        )
        assert _weight(option, **distress) > 0


@pytest.mark.parametrize("name,case", sorted(_TREASURY_SPECIAL_CASES.items()))
def test_treasury_cost_options_discount_financial_distress(bosnia_options, name, case):
    healthy, fallback, random_stability_loss = case
    option = bosnia_options[name]
    assert _weight(option) == healthy
    assert _weight(option, bankrupt=True) == healthy * 0.25
    assert _weight(option, deficit=True) == healthy * 0.5
    if fallback is not None:
        assert _weight(option, bankrupt=True, treasury=0) == 0
        assert _weight(bosnia_options[fallback], bankrupt=True, treasury=0) > 0
    if random_stability_loss:
        assert _weight(option, bankrupt=True, deficit=True, stability=0.2) == (
            healthy * 0.25 * 0.5 * 0.25
        )


def test_loan_option_carries_both_financial_guards_with_the_path_bonus(bosnia_options):
    loan = bosnia_options["BOS_political.60.b"]
    assert _weight(loan) == 40
    assert _weight(loan, bankrupt=True) == 10
    assert _weight(loan, deficit=True) == 20
    assert _weight(loan, stability=0.2) == 10
    assert _weight(loan, east=True) == 120
    assert _weight(loan, east=True, bankrupt=True, deficit=True, stability=0.2) == 3.75


@pytest.mark.parametrize("name,healthy", sorted(_STABILITY_LOSSES.items()))
def test_stability_losses_discount_low_stability(bosnia_options, name, healthy):
    option = bosnia_options[name]
    assert _weight(option) == healthy
    assert _weight(option, stability=0.2) == healthy * 0.25
    assert _weight(option, stability=0.2) > 0


@pytest.mark.parametrize("name,healthy", sorted(_POWER_SPENDING.items()))
def test_power_spending_discounts_bankruptcy(bosnia_options, name, healthy):
    option = bosnia_options[name]
    assert _weight(option) == healthy
    assert _weight(option, bankrupt=True) == healthy * 0.25
    assert _weight(option, bankrupt=True) > 0


def test_entity_competency_handout_stops_in_bankruptcy(bosnia_options):
    handout = bosnia_options["BOS_events.62.a"]
    assert _weight(handout) == 70
    assert _weight(handout, bankrupt=True) == 0
    assert _weight(bosnia_options["BOS_events.62.b"], bankrupt=True) > 0


def test_shared_power_cost_guards_only_the_dearer_option(bosnia_options):
    dearer = bosnia_options["BOS_political.50.a"]
    cheaper = bosnia_options["BOS_political.50.b"]
    assert _weight(dearer, bankrupt=True) < _weight(dearer)
    assert _weight(cheaper, bankrupt=True) == _weight(cheaper) == 70


def test_fatal_energy_path_gate_runs_after_the_financial_guards(bosnia_options):
    option = bosnia_options["BOS_political.60.a"]
    modifiers = [
        body
        for key, _, body in iter_statements(script_block(option, "ai_chance"))
        if key == "modifier" and body is not None
    ]
    first = list(iter_statement_ops(modifiers[0]))
    assert first[0][:2] == ("factor", "=")
    assert first[1] == ("has_active_mission", "=", "bankruptcy_incoming_collapse", None)
    last = list(iter_statement_ops(modifiers[-1]))
    assert last == [
        ("factor", "=", "0", None),
        ("has_completed_focus", "=", "BOS_east_energy_partnership", None),
    ]
    assert _weight(option, east=True, deficit=True) == 0
    assert _weight(option, deficit=True) == 30


@pytest.mark.parametrize("name", ["BOS_events.21.a", "BOS_events.24.a"])
def test_foreign_payer_options_stay_away_from_receiver_finances(bosnia_options, name):
    option = bosnia_options[name]
    from_blocks = [
        body
        for key, _, body in iter_statements(option)
        if key == "FROM" and body is not None
    ]
    assert len(from_blocks) == 1
    assert ("modify_treasury_effect", "yes", None) in list(
        iter_statements(from_blocks[0])
    )
    own_scope = [
        key
        for key, _, _ in iter_statements(option)
        if key
        not in {
            "FROM",
            "ai_chance",
            "name",
            "log",
            "custom_effect_tooltip",
            "hidden_effect",
        }
    ]
    assert "modify_treasury_effect" not in own_scope
    assert _weight(option) == _weight(option, bankrupt=True) == 80
    assert _weight(option, payer_bankrupt=True) == 20
    assert _weight(option, payer_deficit=True) == 40


@pytest.mark.parametrize("name", ["BOS_events.68.b", "BOS_events.70.b"])
def test_foreign_war_support_loss_checks_the_payer(bosnia_options, name):
    option = bosnia_options[name]
    assert _weight(option) == 15
    assert _weight(option, payer_war_support=0.2) == 3.75
    assert _weight(option, stability=0.2) == 15


@pytest.mark.parametrize("event_id", _AUDITED_EVENTS)
def test_every_audited_event_keeps_a_positive_fallback_when_broke_and_unstable(
    bosnia_options, event_id
):
    weights = [
        _weight(option, bankrupt=True, deficit=True, stability=0.2, treasury=0)
        for name, option in bosnia_options.items()
        if name.startswith(f"{event_id}.")
    ]
    assert weights
    assert sum(weights) > 0, event_id


@pytest.mark.parametrize(
    "removed,flagged",
    [
        (
            "\t\t\tmodifier = {\n\t\t\t\tfactor = 0.25\n\t\t\t\thas_stability < 0.3\n\t\t\t}\n",
            "BOS_political.26.b",
        ),
        (
            "\t\t\tmodifier = {\n\t\t\t\tfactor = 0.25\n\t\t\t\thas_active_mission = bankruptcy_incoming_collapse\n\t\t\t}\n",
            "BOS_political.41.b",
        ),
    ],
)
def test_cost_validator_evaluates_the_real_bosnia_options(removed, flagged):
    assert find_cost_blind_options(_BOSNIA_SOURCE, _BUDGET_EFFECTS, {}) == []
    findings = {
        name
        for name, *_ in find_cost_blind_options(
            _without_modifier(_BOSNIA_SOURCE, flagged, removed), _BUDGET_EFFECTS, {}
        )
    }
    assert findings == {flagged}
