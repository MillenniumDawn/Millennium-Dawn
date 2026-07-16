"""Tests for the orphan money-setter check in validate_variables.

A set_temp_variable of treasury_change/debt_change/int_investment_change with
no consumer call afterwards in the same effect block is a dead setter — the
transfer silently never happens (Sweden_foci.57). Consumers are derived from
scripted-effect bodies so wrappers (GRE_pay_or_defer) clear the setter too.
"""

from validate_variables import (
    build_money_consumer_map,
    process_file_for_orphan_money,
)

BASE_EFFECTS = """modify_treasury_effect = {
	add_to_variable = { treasury = treasury_change }
}
modify_debt_effect = {
	add_to_variable = { debt = debt_change }
}
modify_international_investment_effect = {
	add_to_variable = { int_investments = int_investment_change }
}
pay_wrapper = {
	multiply_temp_variable = { treasury_change = 1.5 }
	modify_treasury_effect = yes
}
overwriting_wrapper = {
	set_temp_variable = { treasury_change = -5 }
	modify_treasury_effect = yes
}
"""

FOCUS_TEMPLATE = """focus_tree = {{
	id = test_tree
	focus = {{
		id = TAG_focus_a
		x = 0
		y = 0
		cost = 1
		completion_reward = {{
			{reward}
		}}
	}}
}}
"""


def _setup(tmp_path):
    fx_dir = tmp_path / "common" / "scripted_effects"
    fx_dir.mkdir(parents=True, exist_ok=True)
    (fx_dir / "00_budget_effects.txt").write_text(BASE_EFFECTS, encoding="utf-8")
    return build_money_consumer_map([str(fx_dir / "00_budget_effects.txt")])


def _lines(tmp_path, reward, consumer_map):
    nf_dir = tmp_path / "common" / "national_focus"
    nf_dir.mkdir(parents=True, exist_ok=True)
    fpath = nf_dir / "test.txt"
    fpath.write_text(FOCUS_TEMPLATE.format(reward=reward), encoding="utf-8")
    return process_file_for_orphan_money((str(fpath), str(tmp_path), consumer_map))


def test_consumed_setter_is_clean(tmp_path):
    cmap = _setup(tmp_path)
    reward = (
        "set_temp_variable = { treasury_change = -10 }\n"
        "\t\t\tmodify_treasury_effect = yes"
    )
    assert _lines(tmp_path, reward, cmap) == []


def test_orphan_setter_is_flagged(tmp_path):
    cmap = _setup(tmp_path)
    reward = "set_temp_variable = { treasury_change = -10 }"
    issues = _lines(tmp_path, reward, cmap)
    assert len(issues) == 1
    assert "treasury_change" in issues[0][0]


def test_wrong_consumer_is_flagged(tmp_path):
    cmap = _setup(tmp_path)
    reward = (
        "set_temp_variable = { treasury_change = -10 }\n\t\t\tmodify_debt_effect = yes"
    )
    assert len(_lines(tmp_path, reward, cmap)) == 1


def test_wrapper_consumer_is_clean(tmp_path):
    cmap = _setup(tmp_path)
    assert "pay_wrapper" in cmap["treasury_change"]
    reward = "set_temp_variable = { treasury_change = -10 }\n\t\t\tpay_wrapper = yes"
    assert _lines(tmp_path, reward, cmap) == []


def test_overwriting_wrapper_is_not_a_consumer(tmp_path):
    cmap = _setup(tmp_path)
    assert "overwriting_wrapper" not in cmap["treasury_change"]


def test_tooltip_setter_needs_tooltip_consumer(tmp_path):
    cmap = _setup(tmp_path)
    reward = (
        "effect_tooltip = {\n"
        "\t\t\t\tset_temp_variable = { treasury_change = -10 }\n"
        "\t\t\t}\n"
        "\t\t\tmodify_treasury_effect = yes"
    )
    assert len(_lines(tmp_path, reward, cmap)) == 1


def test_tooltip_selfcontained_is_clean(tmp_path):
    cmap = _setup(tmp_path)
    reward = (
        "effect_tooltip = {\n"
        "\t\t\t\tset_temp_variable = { treasury_change = -10 }\n"
        "\t\t\t\tmodify_treasury_effect = yes\n"
        "\t\t\t}"
    )
    assert _lines(tmp_path, reward, cmap) == []


def test_multiple_vars_tracked_independently(tmp_path):
    cmap = _setup(tmp_path)
    reward = (
        "set_temp_variable = { int_investment_change = 5 }\n"
        "\t\t\tmodify_international_investment_effect = yes\n"
        "\t\t\tset_temp_variable = { debt_change = -4 }\n"
        "\t\t\tmodify_treasury_effect = yes"
    )
    issues = _lines(tmp_path, reward, cmap)
    assert len(issues) == 1
    assert "debt_change" in issues[0][0]
