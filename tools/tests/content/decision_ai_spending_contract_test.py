"""Evaluate shipped decision weights and payment contracts, not native AI selection."""

import pytest
from shared.paths import REPO_ROOT
from shared.suite import EconomicScriptFixture, read_text, script_block
from shared_utils import extract_block_from_text, iter_statements

_CANADA = [
    (f"CAN_improve_infrastructure_{state}", 2.5)
    for state in (759, 760, 761, 762, 763, 757, 756, 755, 754, 753, 758, 1159, 1160)
]
_GREECE = [
    ("GRE_aegean_survey", 4.5),
    ("GRE_aegean_extraction", 3.75),
    ("GRE_aegean_offshore_industry", 13.5),
    ("GRE_crete_survey", 4.5),
    ("GRE_crete_extraction", 5.63),
    ("GRE_crete_offshore_industry", 19.75),
]
_ITALY = [
    ("ITA_run_support_campaigns_short", 5),
    ("ITA_run_support_campaigns_long", 10),
    ("ITA_expand_space_program", 40),
    ("ITA_launch_commercial_satellite", 4),
    ("ITA_setup_lunar_base", 50),
    *[
        (f"ITA_increase_asteroid_mining_{resource}{suffix}", cost)
        for resource in ("precious", "aluminium", "tungsten")
        for suffix, cost in (("", 10), ("_2", 15), ("_3", 20))
    ],
]
_SPENDING = _CANADA + [("SWE_Officer_education_course", 6)] + _GREECE + _ITALY


@pytest.fixture(scope="module")
def decisions():
    result = {}
    for filename, category in (
        ("Canada.txt", "CAN_provincial_infrastructure"),
        ("05_sweden_decision.txt", "SWE_decision_Forsvarsmarkten_category"),
        ("05_GRE_decisions.txt", "GRE_generic_decisions_category"),
        ("Italy.txt", "ITA_italian_space_decision_category"),
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
    triggers = read_text(
        REPO_ROOT / "common/scripted_triggers/00_economic_triggers.txt"
    )
    return EconomicScriptFixture(
        {
            "treasury": 100,
            "treasury_rate": 0,
            "budget_balance_ratio": 0,
            "ITA_peoples_support": 60,
            "ITA_space_program_level": 1,
            **{
                f"resource_{kind}@{resource}": amount
                for resource in ("chromium", "aluminium", "tungsten")
                for kind, amount in (("consumed", 20), ("produced", 10))
            },
        },
        predicates={
            "has_active_mission": lambda *_: False,
            "has_country_flag": lambda *_: False,
            "has_decision": lambda *_: False,
            "has_idea": lambda *_: False,
            "has_defensive_war": False,
            "any_of_scopes": lambda *_: False,
            "naval_strength_ratio": lambda *_: True,
            "SWE_under_military_threat": True,
        },
        triggers={"ai_has_high_deficit": script_block(triggers, "ai_has_high_deficit")},
    )


@pytest.mark.parametrize("name,cost", _SPENDING)
@pytest.mark.parametrize(
    "bankrupt,deficit", [(False, True), (True, False), (True, True)]
)
def test_optional_spending_weights_respond_to_fiscal_distress(
    decisions, economy, name, cost, bankrupt, deficit
):
    economy.values["treasury"] = cost
    weights = script_block(decisions[name], "ai_will_do")
    healthy = economy.weight(weights)
    assert healthy > 0
    economy.predicates["has_active_mission"] = lambda *_: bankrupt
    economy.values["treasury_rate"] = -4 if deficit else 0
    expected = 0 if bankrupt or name == "ITA_expand_space_program" else healthy / 2
    assert economy.weight(weights) == expected


@pytest.mark.parametrize("name,cost", _SPENDING)
@pytest.mark.parametrize("offset,affordable", [(-0.001, False), (0, True)])
def test_ai_affordability_matches_the_full_upfront_price(
    decisions, economy, name, cost, offset, affordable
):
    decision = decisions[name]
    economy.values["treasury"] = cost + offset
    gates = [
        body
        for key, _, body in iter_statements(decision)
        if key == "custom_cost_trigger" and body is not None
    ]
    can_select = economy.weight(script_block(decision, "ai_will_do")) > 0 and all(
        economy.condition(gate) for gate in gates
    )
    assert can_select is affordable


@pytest.mark.parametrize("name,cost", _CANADA)
def test_canadian_infrastructure_charges_once_on_selection(decisions, name, cost):
    decision = decisions[name]
    complete = list(iter_statements(script_block(decision, "complete_effect")))
    assert [key for key, _, _ in complete] == [
        "log",
        "set_temp_variable",
        "modify_treasury_effect",
    ]
    payment = script_block(
        script_block(decision, "complete_effect"), "set_temp_variable"
    )
    assert list(iter_statements(payment)) == [("treasury_change", str(-cost), None)]
    assert complete[2] == ("modify_treasury_effect", "yes", None)
    removal = next(
        body for key, _, body in iter_statements(decision) if key == "remove_effect"
    )
    assert removal is not None and "treasury" not in removal
    state = name.rsplit("_", 1)[1]
    assert list(iter_statements(script_block(decision, "available"))) == [
        ("has_full_control_of_state", state, None),
        ("owns_state", state, None),
    ]
    construction, end = extract_block_from_text(removal, removal.index(f"{state} ="))
    assert end > 0
    assert list(
        iter_statements(script_block(construction, "add_building_construction"))
    ) == [
        ("type", "infrastructure", None),
        ("level", "1", None),
    ]


@pytest.mark.parametrize("name,cost", _GREECE)
def test_greek_deferral_avoids_cash_gate_but_not_fiscal_policy(
    decisions, economy, name, cost
):
    economy.values["treasury"] = 0
    economy.predicates["has_country_flag"] = (
        lambda flag, _: flag == "GRE_defer_payments_flag"
    )
    weights = script_block(decisions[name], "ai_will_do")
    healthy = economy.weight(weights)
    assert healthy > 0
    economy.values["budget_balance_ratio"] = -0.11
    assert economy.weight(weights) == healthy / 2
    economy.predicates["has_active_mission"] = lambda *_: True
    assert economy.weight(weights) == 0
    complete = list(iter_statements(script_block(decisions[name], "complete_effect")))
    payment = script_block(
        script_block(decisions[name], "complete_effect"), "set_temp_variable"
    )
    entries = list(iter_statements(payment))
    assert len(entries) == 1
    variable, amount, nested = entries[0]
    assert variable == "debt_change" and nested is None and amount is not None
    assert float(amount) == cost
    assert complete[2] == ("GRE_pay_or_defer", "yes", None)


@pytest.mark.parametrize("name,cost", _GREECE)
@pytest.mark.parametrize("previous_stage", [False, True])
def test_greek_project_stages_keep_their_prerequisites(
    decisions, economy, name, cost, previous_stage
):
    state = "143" if "aegean" in name else "144"
    economy.predicates["owns_state"] = lambda value, _: value == state
    economy.predicates["has_country_flag"] = lambda *_: previous_stage
    available = economy.condition(script_block(decisions[name], "available"))
    assert available is (name.endswith("survey") or previous_stage)


@pytest.mark.parametrize("name", ["SWE_Home_Guard", "SWE_fortifications"])
@pytest.mark.parametrize(
    "defensive,justifying,expected",
    [(False, False, 0), (True, False, 5), (False, True, 5)],
)
def test_swedish_emergency_defense_survives_fiscal_distress(
    decisions, economy, name, defensive, justifying, expected
):
    def incoming_justification(_, body):
        entries = list(iter_statements(body))
        assert ("array", "SWE.potential_and_current_enemies", None) in entries
        assert ("is_justifying_wargoal_against", "SWE", None) in entries
        return justifying

    economy.values["treasury_rate"] = -4
    economy.predicates.update(
        has_active_mission=lambda *_: True,
        has_defensive_war=defensive,
        any_of_scopes=incoming_justification,
    )
    assert economy.weight(script_block(decisions[name], "ai_will_do")) == expected


@pytest.mark.parametrize(
    "general,pending", [(True, False), (False, False), (True, True)]
)
def test_swedish_officer_training_needs_an_eligible_recipient(
    decisions, economy, general, pending
):
    def eligible_general(_, body):
        assert list(iter_statements(body)) == [("is_field_marshal", "no", None)]
        return general

    economy.predicates.update(
        any_army_leader=eligible_general, has_country_flag=lambda *_: pending
    )
    assert economy.condition(
        script_block(decisions["SWE_Officer_education_course"], "available")
    ) is (general and not pending)


@pytest.mark.parametrize(
    "threatened,mobilized", [(True, True), (True, False), (False, True)]
)
def test_swedish_ai_does_not_repeat_or_immediately_reverse_mobilization(
    decisions, economy, threatened, mobilized
):
    economy.predicates.update(
        SWE_under_military_threat=threatened,
        has_idea=lambda *_: mobilized,
    )
    launch = decisions["SWE_launch_total_defence"]
    launch_allowed = economy.condition(script_block(launch, "visible")) and (
        economy.weight(script_block(launch, "ai_will_do")) > 0
    )
    assert launch_allowed is (threatened and not mobilized)
    normal = decisions["SWE_back_to_normality"]
    normal_weight = economy.weight(script_block(normal, "ai_will_do"))
    assert (normal_weight > 0) is (not threatened)


@pytest.mark.parametrize(
    "support,level,expand,shrink",
    [
        (34.999, 1, 0, 1),
        (35, 1, 0, 0),
        (49.999, 1, 0, 0),
        (50, 1, 10, 0),
        (60, 5, 0, 0),
    ],
)
def test_italian_expansion_has_a_support_buffer_and_program_limit(
    decisions, economy, support, level, expand, shrink
):
    economy.values.update(ITA_peoples_support=support, ITA_space_program_level=level)
    assert (
        economy.weight(
            script_block(decisions["ITA_expand_space_program"], "ai_will_do")
        )
        == expand
    )
    assert (
        economy.weight(
            script_block(decisions["ITA_shrink_space_program"], "ai_will_do")
        )
        == shrink
    )


@pytest.mark.parametrize("bankrupt", [False, True])
def test_italian_budget_relief_stays_available_in_fiscal_distress(
    decisions, economy, bankrupt
):
    economy.values["treasury_rate"] = -4
    economy.predicates["has_active_mission"] = lambda *_: bankrupt
    assert (
        economy.weight(
            script_block(decisions["ITA_shrink_space_program"], "ai_will_do")
        )
        == 10
    )
    assert (
        economy.weight(
            script_block(decisions["ITA_rebalance_the_ASI_budget"], "ai_will_do")
        )
        == 30
    )


@pytest.mark.parametrize(
    "name,other",
    [
        ("ITA_run_support_campaigns_short", "ITA_run_support_campaigns_long"),
        ("ITA_run_support_campaigns_long", "ITA_run_support_campaigns_short"),
        ("ITA_expand_space_program", "ITA_shrink_space_program"),
        ("ITA_shrink_space_program", "ITA_expand_space_program"),
    ],
)
def test_italian_ai_does_not_queue_conflicting_space_actions(
    decisions, economy, name, other
):
    if name == "ITA_shrink_space_program":
        economy.values["ITA_peoples_support"] = 30
    weights = script_block(decisions[name], "ai_will_do")
    assert economy.weight(weights) > 0
    economy.predicates["has_decision"] = lambda active, _: active == other
    assert economy.weight(weights) == 0
