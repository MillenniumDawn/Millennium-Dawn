from pathlib import Path

import pytest
from shared.suite import read_text
from shared_utils import extract_block_from_text, iter_statement_ops, strip_comments

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
STATUS = read_text(
    ROOT / "common/scripted_localisation/00_investment_scripted_localisation.txt"
)
LOC = read_text(ROOT / "localisation/english/MD_investments_l_english.yml")
REQUESTS = "automated_internal_investment_requests@var:internal_investment_state"
QUEUE = "automated_internal_investment_states"
ACTIONS = [
    (
        "encourage_investments",
        "encourage_investments_in_state",
        "currently_encouraged_investments",
        160,
        "0.006",
    ),
    (
        "encourage_productivity",
        "encourage_productivity_in_state",
        "state_owned_encouraged_productivity",
        160,
        "{ value = 0.009 multiply = state_population_k multiply = 0.0001 }",
    ),
    (
        "expand_building_capacity",
        "expand_local_building_capacity",
        "expand_local_building_capacity",
        120,
        "{ value = expanded_building_slot_times add = 1 multiply = 0.007 }",
    ),
    (
        "expand_renewable_capacity",
        "expand_local_renewable_capacity",
        "state_owned_local_renewable_capacity_modifier",
        180,
        "0.001",
    ),
    (
        "expand_infrastructure",
        "expand_local_infrastructure",
        "state_owned_local_infrastructure_modifier",
        180,
        "0.002",
    ),
    (
        "expand_military_infrastructure",
        "expand_local_military_infrastructure",
        "state_owned_local_military_infrastructure_modifier",
        180,
        "0.002",
    ),
    (
        "expand_energy_infrastructure",
        "expand_local_energy_infrastructure",
        "state_owned_local_energy_infrastructure_modifier",
        180,
        "0.003",
    ),
    (
        "build_logistics_base",
        "build_forward_logistics_base",
        "state_owned_build_forward_logistics_base_modifier",
        180,
        "0.004",
    ),
    (
        "improve_rebuilding",
        "improve_rebuilding_efforts",
        "state_owned_improve_rebuilding_efforts_modifier",
        180,
        "{ value = 0.004 multiply = state_population_k multiply = 0.0001 }",
    ),
    (
        "hire_primary_workers",
        "hire_extra_primary_sector_workers",
        "state_owned_hire_extra_primary_sector_workers_modifier",
        180,
        "0.006",
    ),
    (
        "expand_coastal_infrastructure",
        "expand_local_coastal_infrastructure",
        "state_owned_local_naval_infrastructure_modifier",
        180,
        "0.005",
    ),
    (
        "expand_fortifications",
        "expand_local_fortification_efforts",
        "state_owned_local_fortification_efforts_modifier",
        180,
        "0.005",
    ),
    (
        "conservation",
        "improve_local_conservation_efforts",
        "improve_local_conservation_efforts",
        180,
        "0.002",
    ),
]


def _block(source, name):
    source = strip_comments(source)
    body, end = extract_block_from_text(source, source.index(f"{name} = {{"))
    assert end != -1, name
    return body


def _tree(body):
    return [
        (key, op, scalar, _tree(block) if block is not None else None)
        for key, op, scalar, block in iter_statement_ops(strip_comments(body))
    ]


def _walk(body, path=()):
    for key, op, scalar, block in iter_statement_ops(strip_comments(body)):
        yield path, key, op, scalar, block
        if block is not None:
            yield from _walk(block, (*path, key))


def _branches(source, name):
    return [
        block
        for key, _, _, block in iter_statement_ops(_block(source, name))
        if key in {"if", "else_if"} and block is not None
    ]


def _loc(key):
    return next(line for line in LOC.splitlines() if line.startswith(f" {key}:"))


@pytest.mark.parametrize("index,action", list(enumerate(ACTIONS, 1)))
def test_action_wiring_cost_benefit_and_cooldown(index, action):
    slug, button, cooldown, days, cost = action
    for suffix, effect in (
        ("click", "purchase_action"),
        ("right_click", "toggle_request"),
    ):
        assert _tree(_block(GUI, f"{button}_{suffix}")) == _tree(
            f"set_temp_variable = {{ internal_investment_action = {index} }} internal_investment_{effect} = yes"
        )
    costs = _block(AUTOMATION, "internal_investment_set_action_cost")
    selected = [
        branch
        for branch in _branches(AUTOMATION, "internal_investment_set_action_cost")
        if any(
            key == "internal_investment_action" and scalar == str(index)
            for _, key, _, scalar, _ in _walk(_block(branch, "limit"))
        )
    ]
    assert len(selected) <= 1
    assert _tree(
        _block(selected[0] if selected else costs, "set_temp_variable")
    ) == _tree(f"ii_cost = {cost}")
    benefit = _branches(AUTOMATION, "internal_investment_apply_benefit")[index - 1]
    gate = _branches(TRIGGERS, "internal_investment_action_on_cooldown")[index - 1]
    for branch in (benefit, gate):
        assert _tree(_block(branch, "limit")) == _tree(
            f"check_variable = {{ internal_investment_action = {index} }}"
        )
    if index in {1, 3, 13}:
        assert _tree(_block(benefit, "set_state_flag")) == _tree(
            f"flag = {cooldown} value = 1 days = {days}"
        )
        assert ("has_state_flag", "=", cooldown, None) in _tree(gate)
    else:
        assert _tree(_block(benefit, "add_dynamic_modifier")) == _tree(
            f"modifier = {cooldown} days = {days}"
        )
        assert _tree(_block(gate, "has_dynamic_modifier")) == _tree(
            f"modifier = {cooldown}"
        )
        assert "set_state_flag" not in benefit
    tooltip = _loc(f"{button}_delayed_tt")
    assert f"[!{button}_click]" in tooltip
    assert f"[auto_repeat_internal_{slug}_status]" in tooltip
    assert "_requirements]" not in tooltip
    status = next(
        block
        for key, _, _, block in iter_statement_ops(strip_comments(STATUS))
        if key == "defined_text"
        and ("name", "=", f"auto_repeat_internal_{slug}_status", None) in _tree(block)
    )
    assert _tree(_block(_block(status, "text"), "trigger")) == _tree(f"""
        set_temp_variable = {{ internal_investment_state = id }}
        ROOT = {{ is_in_array = {{ array = {REQUESTS} value = {index} }} }}
    """)


def test_single_preview_and_guarded_purchase_do_not_require_repeat_selection():
    purchase = _block(AUTOMATION, "internal_investment_purchase_action")
    top = list(iter_statement_ops(purchase))
    assert [key for key, _, _, _ in top[:4]] == [
        "set_temp_variable",
        "internal_investment_set_action_cost",
        "calculate_internal_investment_costs",
        "effect_tooltip",
    ]
    assert _tree(purchase)[:1] == _tree(
        "set_temp_variable = { internal_investment_state = id }"
    )
    assert _tree(_block(purchase, "effect_tooltip")) == _tree(
        "internal_investment_apply_benefit = yes"
    )
    assert _tree(_block(purchase, "ROOT")) == _tree(
        "custom_effect_tooltip = internal_investment_cost_tt"
    )
    guarded = _block(_block(purchase, "hidden_effect"), "if")
    assert _tree(_block(guarded, "limit")) == _tree("""
        automated_internal_investment_state_available = yes
        internal_investment_action_eligible = yes
        NOT = { internal_investment_action_on_cooldown = yes }
        internal_investment_can_pay = yes
    """)
    assert [key for key, _, _, _ in iter_statement_ops(guarded)] == [
        "limit",
        "internal_investment_apply_benefit",
        "internal_investment_charge_costs",
    ]
    assert "repeat_selected" not in purchase and REQUESTS not in purchase
    calls = [
        (path, key)
        for path, key, _, _, _ in _walk(AUTOMATION)
        if key
        in {"calculate_internal_investment_costs", "internal_investment_charge_costs"}
    ]
    assert calls == [
        (
            ("internal_investment_purchase_action",),
            "calculate_internal_investment_costs",
        ),
        (
            ("internal_investment_purchase_action", "hidden_effect", "if"),
            "internal_investment_charge_costs",
        ),
    ]
    feedback = {
        scalar
        for path, key, _, scalar, _ in _walk(purchase)
        if key == "custom_effect_tooltip"
        and "if" in path
        and "hidden_effect" not in path
    }
    assert feedback == {
        f"internal_investment_{reason}_tt"
        for reason in (
            "no_slot",
            "bankruptcy",
            "active",
            "capacity_limit",
            "coastal_required",
            "amazon_required",
            "insufficient_funds",
        )
    }
    for key in feedback:
        assert "§R" in _loc(key)


@pytest.mark.parametrize(
    "index,opinion,effects",
    [
        (4, -3, ["fossil_fuel_industry"]),
        (6, 5, ["the_military", "intelligence_community"]),
        (7, 5, ["fossil_fuel_industry"]),
        (11, 5, ["maritime_industry", "the_military"]),
        (12, 5, ["the_military"]),
    ],
)
def test_country_opinions_are_preserved(index, opinion, effects):
    branch = _branches(AUTOMATION, "internal_investment_apply_benefit")[index - 1]
    expected = f"set_temp_variable = {{ temp_opinion = {opinion} }} "
    expected += " ".join(f"change_{effect}_opinion = yes" for effect in effects)
    assert _tree(_block(branch, "ROOT")) == _tree(expected)


def test_capacity_limit_deselects_only_action_three_and_conservation_recalculates():
    benefits = _branches(AUTOMATION, "internal_investment_apply_benefit")
    assert len(benefits) == 13
    capacity = benefits[2]
    assert ("add_extra_state_shared_building_slots", "=", "1", None) in _tree(capacity)
    assert _tree(_block(capacity, "add_to_variable")) == _tree(
        "expanded_building_slot_times = 1"
    )
    assert _tree(_block(capacity, "hidden_effect")) == _tree(f"""
        if = {{
            limit = {{ check_variable = {{ expanded_building_slot_times > 4 }} }}
            ROOT = {{ remove_from_array = {{ array = {REQUESTS} value = 3 }} }}
        }}
    """)
    assert _tree(_block(benefits[12], "hidden_effect")) == _tree(
        "ROOT = { BRA_calculate_amazon_system = yes }"
    )
    eligibility = _branches(TRIGGERS, "internal_investment_action_eligible")
    assert _tree(_block(eligibility[0], "check_variable")) == _tree(
        "internal_investment_action = 3"
    )
    assert "expanded_building_slot_times < 5" in eligibility[0]
    assert ("is_coastal", "=", "yes", None) in _tree(eligibility[1])
    assert _tree(_block(eligibility[2], "has_dynamic_modifier")) == _tree(
        "modifier = BRA_amazon_modifier"
    )
    assert _tree(_block(eligibility[2], "ROOT")) == _tree("original_tag = BRA")


def test_modified_costs_and_payment_are_calculated_and_charged_once():
    costs = _block(INVESTMENT_EFFECTS, "calculate_internal_investment_costs")
    assert _tree(_block(costs, "internal_investment_pp_cost")) == _tree("""
        value = 75
        multiply = { value = 1 add = modifier@internal_investments_pp_cost_modifier }
        clamp = { min = 25 max = 999999999 }
    """)
    assert _tree(_block(costs, "internal_investment_money_cost")) == _tree("""
        value = gdp_total
        multiply = ii_cost
        multiply = { value = 1 add = modifier@internal_investments_money_cost_modifier }
        max = { value = gdp_total multiply = 0.001 }
    """)
    charge = _block(INVESTMENT_EFFECTS, "internal_investment_charge_costs")
    country = _block(charge, "ROOT")
    for variable, price in (
        ("pp_cost", "internal_investment_pp_cost"),
        ("treasury_change", "internal_investment_money_cost"),
    ):
        assert _tree(_block(country, variable)) == _tree(
            f"value = {price} multiply = -1"
        )
    for effect, value in (
        ("add_political_power", "pp_cost"),
        ("modify_treasury_effect", "yes"),
        ("state_owned_concurrent_investment_limit_implement", "yes"),
    ):
        assert [node for node in _tree(country) if node[0] == effect] == [
            (effect, "=", value, None)
        ]
    assert _tree(_block(country, "if")) == _tree("""
        limit = { check_variable = { automation_internal_investment_attempt = 1 } }
        set_temp_variable = { automation_internal_investment_started = 1 }
    """)
    assert ("refresh_investment_gui", "=", "yes", None) in _tree(charge)
    slots = _block(
        INVESTMENT_EFFECTS, "state_owned_concurrent_investment_limit_implement"
    )
    for index in range(1, 7):
        assert f"soi_slot_state^{index} = PREV.id" in slots


def test_exact_pp_equality_manual_borrowing_and_automation_reserve():
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


def test_repeat_arrays_are_country_owned_and_selection_can_always_be_removed():
    for source in (AUTOMATION, TRIGGERS, STATUS):
        for path, key, _, scalar, _ in _walk(source):
            if (
                (key == "array" and scalar == REQUESTS)
                or (key == "clear_array" and scalar == REQUESTS)
                or key == f"{REQUESTS}^num"
            ):
                assert "ROOT" in path, (path, key)
    allowed = _block(TRIGGERS, "internal_investment_repeat_toggle_allowed")
    assert _tree(_block(allowed, "OR"))[0] == (
        "internal_investment_repeat_selected",
        "=",
        "yes",
        None,
    )
    for index, (_, button, _, _, _) in enumerate(ACTIONS, 1):
        assert f"{button}_click_enabled =" not in GUI
        if index in {3, 11, 13}:
            assert _tree(_block(GUI, f"{button}_right_click_enabled")) == _tree(
                f"set_temp_variable = {{ internal_investment_action = {index} }} internal_investment_repeat_toggle_allowed = yes"
            )
    toggle = _block(AUTOMATION, "internal_investment_toggle_request")
    country = _block(toggle, "ROOT")
    assert _tree(_block(country, "if")) == _tree(f"""
        limit = {{ is_in_array = {{ array = {REQUESTS} value = internal_investment_action }} }}
        remove_from_array = {{ array = {REQUESTS} value = internal_investment_action }}
    """)
    assert _tree(_block(country, "else")) == _tree(
        f"add_to_array = {{ array = {REQUESTS} value = internal_investment_action }}"
    )
    queue_add = [
        path
        for path, key, _, scalar, _ in _walk(country)
        if key == "array" and scalar == QUEUE
    ]
    assert queue_add == [
        ("if", "if", "limit", "NOT", "is_in_array"),
        ("if", "if", "add_to_array"),
        ("else", "remove_from_array"),
    ]


def test_weekly_priority_fallthrough_single_success_and_stable_requeue():
    weekly = _block(AUTOMATION, "automation_internal_investments_weekly")
    traversal = _block(weekly, "for_each_scope_loop")
    loop = _block(traversal, "for_loop_effect")
    assert _tree(loop)[:4] == _tree("""
        start = 1
        end = 14
        value = internal_investment_action
        break = automation_internal_investment_started
    """)
    attempt = _block(loop, "if")
    assert _tree(_block(attempt, "limit")) == _tree("""
        internal_investment_repeat_selected = yes
        internal_investment_action_eligible = yes
        NOT = { internal_investment_action_on_cooldown = yes }
    """)
    assert ("internal_investment_purchase_action", "=", "yes", None) in _tree(attempt)
    assert (
        "set_temp_variable = { automation_internal_investment_started = 0 }"
        in traversal
    )
    assert _tree(
        _block(traversal, "automation_internal_investment_available_pp")
    ) == _tree("value = ROOT.political_power subtract = ROOT.automation_pp_reserve")
    assert _tree(_block(traversal, "if")) == _tree(f"""
        limit = {{ NOT = {{ OR = {{ is_owned_by = ROOT is_controlled_by = ROOT }} }} }}
        ROOT = {{ clear_array = {REQUESTS} }}
    """)
    for path, key, _, scalar, _ in _walk(traversal):
        assert not (
            key == "array"
            and scalar == QUEUE
            and any(p in {"add_to_array", "remove_from_array"} for p in path)
        )
        assert not (key == "clear_array" and scalar == QUEUE)
    top = _tree(weekly)
    assert top[3][0] == "for_each_scope_loop"
    assert top[4:6] == _tree(
        f"set_temp_variable = {{ automation_internal_investment_attempt = 0 }} clear_array = {QUEUE}"
    )
    assert top[6:8] == _tree(f"""
        for_each_scope_loop = {{ array = automated_internal_investment_waiting ROOT = {{ add_to_array = {{ array = {QUEUE} value = PREV }} }} }}
        for_each_scope_loop = {{ array = automated_internal_investment_rotate ROOT = {{ add_to_array = {{ array = {QUEUE} value = PREV }} }} }}
    """)
    rotation = [
        block
        for _, key, _, _, block in _walk(traversal)
        if key == "ROOT"
        and block is not None
        and "automated_internal_investment_rotate" in block
    ]
    assert len(rotation) == 1
    assert _tree(rotation[0]) == _tree("""
        if = {
            limit = { check_variable = { automation_internal_investment_started = 1 } }
            add_to_temp_array = { automated_internal_investment_rotate = PREV }
        }
        else = { add_to_temp_array = { automated_internal_investment_waiting = PREV } }
    """)
    assert "has_automated_internal_investment_request = yes" in traversal


def test_daily_upkeep_and_display_prices_are_preserved():
    daily = _block(AUTOMATION, "automation_internal_investments_daily")
    assert _tree(_block(daily, "automation_internal_investment_available_pp")) == _tree(
        "value = political_power subtract = automation_pp_reserve"
    )
    assert _tree(_block(daily, "check_variable")) == _tree(
        "var = automation_internal_investment_available_pp value = 0.15 compare = greater_than_or_equals"
    )
    assert ("add_political_power", "=", "-0.15", None) in _tree(_block(daily, "if"))
    assert _tree(_block(daily, "set_country_flag")) == _tree(
        "flag = automation_internal_investment_upkeep_paid value = 1 days = 2"
    )
    assert "construction-speed bonus" in _loc("encourage_investments_in_state_click_tt")
    assert "For 180 Days" in _loc("improve_local_conservation_efforts_click_tt")
    for price in ("internal_investment_pp_cost", "internal_investment_money_cost"):
        assert f"[?{price}|2]" in _loc("internal_investment_cost_tt")
    for token in (
        "ROOT.internal_investment_action",
        "ROOT.internal_investment_state",
        "ROOT.automation_internal_investment_started",
        "auto_repeat_internal_",
        "block_future_expand_local_building_capacity",
        "internal_investment_pp_affordable",
    ):
        assert token not in AUTOMATION + TRIGGERS + GUI
