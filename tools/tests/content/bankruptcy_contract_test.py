"""Debt-default contracts from economy-guide.md and PR #5873.

These execute the shipped decision arithmetic and policy, not native AI selection,
timers, depression effects, or country scopes.
"""

import pytest
from shared.paths import REPO_ROOT
from shared.suite import EconomicScriptFixture, read_text, script_block
from shared_utils import iter_statements, strip_comments


@pytest.fixture(scope="module")
def decisions():
    source = strip_comments(
        read_text(REPO_ROOT / "common/decisions/bankruptcy_decisions.txt")
    )
    return {
        name: body
        for category in ("bankruptcy_decisions", "debt_default_decisions")
        for name, _, body in iter_statements(script_block(source, category))
        if body is not None
    }


@pytest.fixture(scope="module")
def economic_triggers():
    source = read_text(REPO_ROOT / "common/scripted_triggers/00_economic_triggers.txt")
    return {
        name: script_block(source, name)
        for name in ("interest_rate_higher_than_15", "treasury_lower_than_5")
    }


_NATIVE_EFFECTS = (
    "depression",
    "add_timed_idea",
    "modify_timed_idea",
    "activate_mission",
)

# case: (pre-default debt, expected regular debt, expected deferred debt)
_PARTITION_CASES = {"100 billion": (100, 10, 50), "200 billion": (200, 20, 100)}


@pytest.mark.parametrize(
    "debt,regular,deferred", _PARTITION_CASES.values(), ids=_PARTITION_CASES
)
def test_default_partitions_debt_without_spending_treasury(
    decisions, debt, regular, deferred
):
    script = EconomicScriptFixture(
        {"debt": debt, "gdp_total": 200, "treasury": 7, "int_investments": 12},
        predicates={
            "has_war": True,
            "has_dynamic_modifier": lambda *_: False,
            "has_idea": lambda *_: False,
        },
        native_effects=_NATIVE_EFFECTS,
    )
    script.execute(
        script_block(decisions["bankruptcy_default_on_debts"], "complete_effect")
    )
    assert script.values == {
        "debt": regular,
        "debt_default_left": deferred,
        "debt_default_total": deferred,
        "old_gdp": 200,
        "gdp_total": 200,
        "treasury": 7,
        "int_investments": 12,
    }
    assert debt - regular - deferred == pytest.approx(debt * 0.4)
    assert ("activate_mission", "debt_default_main_mission", None) in script.calls


# case: (AI, war, subject, interest, treasury, available)
_AVAILABILITY_CASES = {
    "AI at war with cash": (True, True, False, 30, 10, True),
    "AI at peace with cash": (True, False, False, 30, 10, True),
    "player just below cash limit": (False, True, False, 30, 4.999, True),
    "player at cash limit": (False, False, False, 30, 5, False),
    "subject cannot default": (True, True, True, 30, 0, False),
    "interest below visibility threshold": (True, False, False, 14.999, 0, False),
}


@pytest.mark.parametrize(
    "ai,war,subject,interest,treasury,expected",
    _AVAILABILITY_CASES.values(),
    ids=_AVAILABILITY_CASES,
)
def test_default_availability_keeps_player_cash_gate_separate_from_ai(
    decisions, economic_triggers, ai, war, subject, interest, treasury, expected
):
    script = EconomicScriptFixture(
        {"interest_rate": interest, "treasury": treasury},
        predicates={"is_ai": ai, "has_war": war, "is_subject": subject},
        triggers=economic_triggers,
    )
    assert (
        script.condition(
            script_block(decisions["bankruptcy_default_on_debts"], "available")
        )
        is expected
    )


# case: (decision, war, fiscal gate, interest, positive AI weight)
_POLICY_CASES = {
    "wartime default": ("bankruptcy_default_on_debts", True, True, 25, True),
    "interest below AI threshold": (
        "bankruptcy_default_on_debts",
        True,
        True,
        24.999,
        False,
    ),
    "fiscal gate closed": ("bankruptcy_default_on_debts", False, False, 30, False),
    "IMF at peace": ("debt_default_concessions_to_the_imf", False, True, 30, True),
    "IMF at war": ("debt_default_concessions_to_the_imf", True, True, 30, False),
    "first influencer with factories": (
        "debt_default_political_concessions_to_biggest_influencer",
        False,
        True,
        30,
        True,
    ),
    "second influencer with factories": (
        "debt_default_political_concessions_to_second_biggest_influencer",
        False,
        True,
        30,
        True,
    ),
}


@pytest.mark.parametrize(
    "name,war,fiscal,interest,positive", _POLICY_CASES.values(), ids=_POLICY_CASES
)
def test_default_ai_policy_preserves_wartime_exit_and_influencer_options(
    decisions, name, war, fiscal, interest, positive
):
    script = EconomicScriptFixture(
        {"interest_rate": interest},
        predicates={
            "has_war": war,
            "ai_fiscal_last_resort_open": fiscal,
            "num_of_civilian_factories": lambda *_: True,
            "num_of_military_factories": lambda *_: True,
            "num_of_naval_factories": lambda *_: True,
        },
    )
    assert (script.weight(script_block(decisions[name], "ai_will_do")) > 0) is positive


_SALES = (
    "debt_default_sell_civilian_factories",
    "debt_default_dismantle_military_factories",
    "debt_default_scrap_dockyard",
    "debt_default_cut_down_government_services",
)
# case: (deferred debt, current GDP, positive AI weight)
_SALE_CASES = {
    "both boundaries included": (50, 800, True),
    "more than final 50 billion": (50.001, 1000, False),
    "below GDP floor": (40, 799.999, False),
}


@pytest.mark.parametrize("name", _SALES)
@pytest.mark.parametrize("left,gdp,positive", _SALE_CASES.values(), ids=_SALE_CASES)
def test_building_sale_ai_weights_respect_debt_and_gdp_boundaries(
    decisions, name, left, gdp, positive
):
    script = EconomicScriptFixture(
        {"debt_default_left": left, "gdp_total": gdp, "old_gdp": 1000}
    )
    assert (script.weight(script_block(decisions[name], "ai_will_do")) > 0) is positive
