from pathlib import Path

import pytest
from shared.suite import read_text
from shared_utils import (
    extract_block_from_text,
    iter_statement_ops,
    iter_statements,
    strip_comments,
)

ROOT = Path(__file__).resolve().parents[2]
AUTOMATION = read_text(
    ROOT / "common/scripted_effects/00_internal_investment_automation_effects.txt"
)
INVESTMENT_EFFECTS = read_text(
    ROOT / "common/scripted_effects/99_investment_scripted_effects.txt"
)
GUI = read_text(ROOT / "common/scripted_guis/01_investment_scripted_gui.txt")
TRIGGERS = read_text(
    ROOT / "common/scripted_triggers/00_investment_scripted_triggers.txt"
)
LOC = read_text(ROOT / "localisation/english/MD_investments_l_english.yml")

ACTIONS = [
    (
        "encourage_investments",
        "encourage_investments_in_state",
        "currently_encouraged_investments",
        160,
        "0.006",
        None,
    ),
    (
        "encourage_productivity",
        "encourage_productivity_in_state",
        "encourage_productivity_in_state",
        160,
        "{ value = 0.009 multiply = state_population_k multiply = 0.0001 }",
        "state_owned_encouraged_productivity",
    ),
    (
        "expand_building_capacity",
        "expand_local_building_capacity",
        "expand_local_building_capacity",
        120,
        "{ value = expanded_building_slot_times add = 1 multiply = 0.007 }",
        None,
    ),
    (
        "expand_renewable_capacity",
        "expand_local_renewable_capacity",
        "expand_local_renewable_capacity",
        180,
        "0.001",
        "state_owned_local_renewable_capacity_modifier",
    ),
    (
        "expand_infrastructure",
        "expand_local_infrastructure",
        "expand_local_infrastructure",
        180,
        "0.002",
        "state_owned_local_infrastructure_modifier",
    ),
    (
        "expand_military_infrastructure",
        "expand_local_military_infrastructure",
        "expand_local_military_infrastructure",
        180,
        "0.002",
        "state_owned_local_military_infrastructure_modifier",
    ),
    (
        "expand_energy_infrastructure",
        "expand_local_energy_infrastructure",
        "expand_local_energy_infrastructure",
        180,
        "0.003",
        "state_owned_local_energy_infrastructure_modifier",
    ),
    (
        "build_logistics_base",
        "build_forward_logistics_base",
        "build_forward_logistics_base",
        180,
        "0.004",
        "state_owned_build_forward_logistics_base_modifier",
    ),
    (
        "improve_rebuilding",
        "improve_rebuilding_efforts",
        "improve_rebuilding_efforts",
        180,
        "{ value = 0.004 multiply = state_population_k multiply = 0.0001 }",
        "state_owned_improve_rebuilding_efforts_modifier",
    ),
    (
        "hire_primary_workers",
        "hire_extra_primary_sector_workers",
        "hire_extra_primary_sector_workers",
        180,
        "0.006",
        "state_owned_hire_extra_primary_sector_workers_modifier",
    ),
    (
        "expand_coastal_infrastructure",
        "expand_local_coastal_infrastructure",
        "expand_local_coastal_infrastructure",
        180,
        "0.005",
        "state_owned_local_naval_infrastructure_modifier",
    ),
    (
        "expand_fortifications",
        "expand_local_fortification_efforts",
        "expand_local_fortification_efforts",
        180,
        "0.005",
        "state_owned_local_fortification_efforts_modifier",
    ),
    (
        "conservation",
        "improve_local_conservation_efforts",
        "improve_local_conservation_efforts",
        180,
        "0.002",
        None,
    ),
]
EXTRA_GUARDS = {
    "expand_building_capacity": "NOT = { has_state_flag = block_future_expand_local_building_capacity }",
    "expand_coastal_infrastructure": "is_coastal = yes",
    "conservation": "has_dynamic_modifier = { modifier = BRA_amazon_modifier } ROOT = { original_tag = BRA }",
}
EXTRA_BENEFITS = {
    "expand_building_capacity": """
        add_extra_state_shared_building_slots = 1
        add_to_variable = { expanded_building_slot_times = 1 }
        if = {
            limit = { check_variable = { expanded_building_slot_times = 5 } }
            set_state_flag = block_future_expand_local_building_capacity
            clr_state_flag = auto_repeat_internal_expand_building_capacity_@ROOT
        }
    """,
    "expand_renewable_capacity": "ROOT = { set_temp_variable = { temp_opinion = -3 } change_fossil_fuel_industry_opinion = yes }",
    "expand_military_infrastructure": "ROOT = { set_temp_variable = { temp_opinion = 5 } change_the_military_opinion = yes change_intelligence_community_opinion = yes }",
    "expand_energy_infrastructure": "ROOT = { set_temp_variable = { temp_opinion = 5 } change_fossil_fuel_industry_opinion = yes }",
    "expand_coastal_infrastructure": "ROOT = { set_temp_variable = { temp_opinion = 5 } change_maritime_industry_opinion = yes change_the_military_opinion = yes }",
    "expand_fortifications": "ROOT = { set_temp_variable = { temp_opinion = 5 } change_the_military_opinion = yes }",
    "conservation": "hidden_effect = { ROOT = { BRA_calculate_amazon_system = yes } }",
}
PP_FORMULA = """
    value = 75
    multiply = { value = 1 add = modifier@internal_investments_pp_cost_modifier }
    clamp = { min = 25 max = 999999999 }
"""


def _block(source, name):
    source = strip_comments(source)
    body, end = extract_block_from_text(source, source.index(f"{name} = {{"))
    assert end != -1, name
    return body


def _tree(body):
    return [
        (key, operator, scalar, _tree(block) if block is not None else None)
        for key, operator, scalar, block in iter_statement_ops(strip_comments(body))
    ]


def _loc(key):
    return next(line for line in LOC.splitlines() if line.startswith(f" {key}:"))


def test_contract_parser_does_not_count_commented_effects():
    assert _tree("# add_political_power = pp_cost") == []
    source = "# payment = { add_political_power = pp_cost }\npayment = { }"
    assert _tree(_block(source, "payment")) == []
    assert _tree(
        "add_political_power = pp_cost # modify_treasury_effect = yes"
    ) == _tree("add_political_power = pp_cost")


@pytest.mark.parametrize("action,button,flag,days,cost,modifier", ACTIONS)
def test_action_preview_purchase_and_requirements_match(
    action, button, flag, days, cost, modifier
):
    entry = _block(AUTOMATION, f"internal_investment_apply_{action}")
    benefit_call = f"internal_investment_benefit_{action} = yes"
    expected_preview = f"""
        set_temp_variable = {{ ii_cost = {cost} }}
        calculate_internal_investment_costs = yes
        custom_effect_tooltip = {button}_click_tt
        effect_tooltip = {{ {benefit_call} }}
        ROOT = {{ custom_effect_tooltip = internal_investment_cost_tt }}
    """
    eligibility = f"""
        automated_internal_investment_state_available = yes
        NOT = {{ has_state_flag = {flag} }}
        {EXTRA_GUARDS.get(action, '')}
    """
    expected_purchase = f"""
        hidden_effect = {{
            if = {{
                limit = {{ {eligibility} internal_investment_can_pay = yes }}
                {benefit_call}
                internal_investment_charge_costs = yes
            }}
        }}
    """
    assert _tree(entry) == _tree(expected_preview + expected_purchase)
    assert _tree(_block(GUI, f"{button}_click")) == _tree(
        f"internal_investment_apply_{action} = yes"
    )
    assert _tree(_block(GUI, f"{button}_requirements")) == _tree(
        eligibility + "internal_investment_pp_affordable = yes"
    )
    assert f"{button}_click_enabled =" not in GUI
    assert f"[!{button}_click]" in _loc(f"{button}_delayed_tt")
    assert f"[!{button}_requirements]" in _loc(f"{button}_delayed_tt")

    expected_benefit = f"set_state_flag = {{ flag = {flag} value = 1 days = {days} }}"
    if modifier:
        expected_benefit += (
            f" add_dynamic_modifier = {{ modifier = {modifier} days = {days} }}"
        )
    expected_benefit += EXTRA_BENEFITS.get(action, "")
    assert _tree(_block(AUTOMATION, f"internal_investment_benefit_{action}")) == _tree(
        expected_benefit
    )


def test_cached_cost_calculation_and_tooltip_pp_formula_agree():
    costs = _block(INVESTMENT_EFFECTS, "calculate_internal_investment_costs")
    expected = f"""
        ROOT = {{
            set_temp_variable = {{ internal_investment_pp_cost = {{ {PP_FORMULA} }} }}
            set_temp_variable = {{ internal_investment_money_cost = {{
                value = gdp_total
                multiply = ii_cost
                multiply = {{ value = 1 add = modifier@internal_investments_money_cost_modifier }}
                max = {{ value = gdp_total multiply = 0.001 }}
            }} }}
        }}
    """
    assert _tree(costs) == _tree(expected)
    affordable = _block(TRIGGERS, "internal_investment_pp_affordable")
    assert _tree(affordable) == _tree(f"""
        set_temp_variable = {{ internal_investment_pp_cost = {{
            {PP_FORMULA.replace('add = modifier@', 'add = ROOT.modifier@')}
        }} }}
        custom_trigger_tooltip = {{
            tooltip = internal_investment_pp_affordable_tt
            check_variable = {{
                var = ROOT.political_power
                value = internal_investment_pp_cost
                compare = greater_than_or_equals
            }}
        }}
    """)
    for obsolete in (
        "pp_cost_temp",
        "internal_investment_prepare_payment",
        "internal_investment_mark_started",
        "calculate_internal_investments_costs",
    ):
        assert obsolete not in AUTOMATION + INVESTMENT_EFFECTS + GUI + TRIGGERS


def test_payment_uses_cached_prices_once_and_retains_slot_scope():
    charge = _block(INVESTMENT_EFFECTS, "internal_investment_charge_costs")
    assert _tree(charge) == _tree("""
        ROOT = {
            set_temp_variable = { pp_cost = { value = internal_investment_pp_cost multiply = -1 } }
            add_political_power = pp_cost
            set_temp_variable = { treasury_change = { value = internal_investment_money_cost multiply = -1 } }
            modify_treasury_effect = yes
            if = {
                limit = { check_variable = { automation_internal_investment_attempt = 1 } }
                set_temp_variable = { automation_internal_investment_started = 1 }
            }
            state_owned_concurrent_investment_limit_implement = yes
        }
        refresh_investment_gui = yes
    """)
    slots = _block(
        INVESTMENT_EFFECTS, "state_owned_concurrent_investment_limit_implement"
    )
    for index in range(1, 7):
        assert f"soi_slot_state^{index} = PREV.id" in slots


def test_affordability_keeps_manual_borrowing_and_automation_reserves():
    assert _tree(_block(TRIGGERS, "internal_investment_can_pay")) == _tree("""
        ROOT = {
            if = {
                limit = { check_variable = { automation_internal_investment_attempt = 1 } }
                check_variable = { var = automation_internal_investment_available_pp value = internal_investment_pp_cost compare = greater_than_or_equals }
                check_variable = { var = treasury value = internal_investment_money_cost compare = greater_than_or_equals }
            }
            else = {
                check_variable = { var = political_power value = internal_investment_pp_cost compare = greater_than_or_equals }
            }
        }
    """)
    assert _tree(
        _block(TRIGGERS, "automated_internal_investment_state_available")
    ) == _tree(
        """
        NOT = { has_state_category = state_inhospitable }
        OR = { is_owned_by = ROOT is_controlled_by = ROOT }
        check_for_investment_project_limits = yes
        ROOT = { NOT = { has_active_mission = bankruptcy_incoming_collapse } }
    """
    )


def test_automation_attempt_keeps_priority_and_rotates_only_on_success():
    expected = """
        ROOT = {
            set_temp_variable = { automation_internal_investment_attempt = 1 }
            set_temp_variable = { automation_internal_investment_started = 0 }
            set_temp_variable = { automation_internal_investment_available_pp = {
                value = political_power subtract = automation_pp_reserve
            } }
        }
    """
    for index, (action, _button, flag, _days, _cost, _modifier) in enumerate(ACTIONS):
        started = (
            "ROOT = { check_variable = { automation_internal_investment_started = 0 } }"
            if index
            else ""
        )
        expected += f"""
            if = {{
                limit = {{
                    {started}
                    has_state_flag = auto_repeat_internal_{action}_@ROOT
                    NOT = {{ has_state_flag = {flag} }}
                    {EXTRA_GUARDS.get(action, '')}
                }}
                internal_investment_apply_{action} = yes
            }}
        """
    expected += """
        ROOT = { set_temp_variable = { automation_internal_investment_attempt = 0 } }
        if = {
            limit = { ROOT = { check_variable = { automation_internal_investment_started = 1 } } }
            ROOT = { add_to_temp_array = { automated_internal_investment_rotate = PREV } }
        }
    """
    assert _tree(
        _block(AUTOMATION, "automation_try_internal_investment_state")
    ) == _tree(expected)


def test_weekly_queue_mutations_follow_attempt_traversal():
    weekly = _block(AUTOMATION, "automation_internal_investments_weekly")
    loops = [
        body for key, _, body in iter_statements(weekly) if key == "for_each_scope_loop"
    ]
    assert len(loops) == 3
    assert _tree(loops[0]) == _tree("""
        array = automated_internal_investment_states
        if = {
            limit = { OR = {
                NOT = { OR = { is_owned_by = ROOT is_controlled_by = ROOT } }
                NOT = { has_automated_internal_investment_request = yes }
            } }
            clear_automated_internal_investment_requests = yes
            ROOT = { add_to_temp_array = { automated_internal_investment_remove = PREV } }
        }
        else_if = {
            limit = { automated_internal_investment_state_available = yes }
            automation_try_internal_investment_state = yes
        }
    """)
    assert _tree(loops[1]) == _tree("""
        array = automated_internal_investment_remove
        ROOT = { remove_from_array = { array = automated_internal_investment_states value = PREV } }
    """)
    assert _tree(loops[2]) == _tree("""
        array = automated_internal_investment_rotate
        ROOT = {
            remove_from_array = { array = automated_internal_investment_states value = PREV }
            add_to_array = { array = automated_internal_investment_states value = PREV }
        }
    """)


def test_english_descriptions_and_fractional_prices():
    encourage = _loc("encourage_investments_in_state_click_tt")
    assert "+15" in encourage and "construction-speed bonus" in encourage
    assert "cheaper" not in encourage
    assert "For 180 Days" in _loc("improve_local_conservation_efforts_click_tt")
    cost = _loc("internal_investment_cost_tt")
    assert "[?internal_investment_pp_cost|2]" in cost
    assert "[?internal_investment_money_cost|2]" in cost
    assert "§! Billion" not in cost
    affordable = _loc("internal_investment_pp_affordable_tt")
    assert "[?internal_investment_pp_cost|2]" in affordable
    assert "[?ROOT.political_power|2]" in affordable
