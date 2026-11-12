"""Contracts for Canada's subsidy AI and economy update path."""

import pytest
from shared.paths import REPO_ROOT
from shared_utils import iter_focus_blocks, iter_statements, read_script


def _read(path):
    return read_script(str(REPO_ROOT / path))


def _block(body, name):
    [block] = [block for key, _, block in iter_statements(body) if key == name]
    assert block is not None
    return block


@pytest.mark.parametrize(
    "decision",
    [
        "CAN_subsidize_military_industry",
        "CAN_subsidize_maritime",
        "CAN_subsidize_aerospace",
    ],
)
def test_high_deficit_blocks_peacetime_purchases_but_halves_wartime_weight(decision):
    category = _block(
        _read("common/decisions/Canada.txt"), "CAN_canadian_subsidies_projects"
    )
    weights = _block(_block(category, decision), "ai_will_do")
    modifiers = [
        list(iter_statements(block))
        for key, _, block in iter_statements(weights)
        if key == "modifier"
    ]
    half = [("factor", "0.5", None), ("ai_has_high_deficit", "yes", None)]
    stop = [
        ("factor", "0", None),
        ("ai_has_high_deficit", "yes", None),
        ("has_war", "no", None),
    ]
    assert modifiers.count(half) == 1
    assert modifiers.count(stop) == 1
    assert all(
        key != "add"
        for modifier in modifiers[modifiers.index(stop) + 1 :]
        for key, _, _ in modifier
    )


def test_subsidy_limits_remain_initialized_by_focus():
    focus = next(
        body
        for name, _, _, body in iter_focus_blocks(
            _read("common/national_focus/05_canada.txt")
        )
        if name == "CAN_Canadian_Economy"
    )
    reward = _block(focus, "completion_reward")
    variables = {
        key: value
        for kind, _, body in iter_statements(reward)
        if kind == "set_variable" and body
        for key, value, _ in iter_statements(body)
    }
    assert {
        name: variables[name]
        for name in (
            "CAN_subsidy_points_max",
            "CAN_subsidy_sector_max",
            "CAN_subsidy_ai_civilian_point_cap",
        )
    } == {
        "CAN_subsidy_points_max": "8",
        "CAN_subsidy_sector_max": "3",
        "CAN_subsidy_ai_civilian_point_cap": "5",
    }
    for name in (
        "CAN_subsidy_base",
        "CAN_subsidy_military_stacks",
        "CAN_subsidy_construction_stacks",
        "CAN_subsidy_infrastructure_stacks",
        "CAN_subsidy_oil_stacks",
        "CAN_subsidy_agriculture_stacks",
        "CAN_subsidy_maritime_stacks",
        "CAN_subsidy_aerospace_stacks",
        "CAN_industrial_capacity_dockyard_var",
        "CAN_production_speed_air_base_factor_var",
    ):
        assert variables[name] == "0"
    bill = _block(
        _read("common/scripted_effects/00_CAN_scripted_effects.txt"),
        "CAN_calculate_subsidy_bill",
    )
    assert "has_variable" not in bill


@pytest.mark.parametrize(
    "effect", ["CAN_finish_subsidy_change", "CAN_modify_subsidy_changes"]
)
def test_subsidy_change_refreshes_bill_once_via_economy_update(effect):
    effects = _read("common/scripted_effects/00_CAN_scripted_effects.txt")
    statements = list(iter_statements(_block(effects, effect)))
    assert [
        (key, value)
        for key, value, _ in statements
        if key in {"CAN_calculate_subsidy_bill", "ingame_update_setup"}
    ] == [("ingame_update_setup", "yes")]
    money = _read("common/scripted_effects/00_money_system.txt")
    update = list(iter_statements(_block(money, "ingame_update_setup")))
    assert [(key, value) for key, value, _ in update].count(
        ("calculate_additional_expense_rate", "yes")
    ) == 1
    expense = _block(money, "calculate_additional_expense_rate")
    canada = [
        body
        for key, _, body in iter_statements(expense)
        if key in {"if", "else_if"}
        and body
        and ("original_tag", "CAN", None) in iter_statements(_block(body, "limit"))
    ]
    assert len(canada) == 1
    statements = list(iter_statements(canada[0]))
    assert [(key, value) for key, value, _ in statements].count(
        ("CAN_calculate_subsidy_bill", "yes")
    ) == 1
    assert statements.index(("CAN_calculate_subsidy_bill", "yes", None)) < next(
        i for i, (key, _, _) in enumerate(statements) if key == "add_to_variable"
    )
