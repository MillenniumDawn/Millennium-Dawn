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
random_producer = {
	set_temp_variable_to_random = {
		var = treasury_change
		min = 2
		max = 8
	}
	modify_treasury_effect = yes
}
outer_pay = {
	pay_wrapper = yes
}
outermost_pay = {
	outer_pay = yes
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


def test_random_writer_is_not_a_consumer(tmp_path):
    # set_temp_variable_to_random produces its own value (ct_ai_seize_assets)
    cmap = _setup(tmp_path)
    assert "random_producer" not in cmap["treasury_change"]


def test_wrapper_of_wrapper_transitive_closure(tmp_path):
    # outermost_pay -> outer_pay -> pay_wrapper needs a second closure pass
    cmap = _setup(tmp_path)
    assert "outer_pay" in cmap["treasury_change"]
    assert "outermost_pay" in cmap["treasury_change"]
    reward = "set_temp_variable = { treasury_change = -10 }\n\t\t\toutermost_pay = yes"
    assert _lines(tmp_path, reward, cmap) == []


def test_clobbered_setter_is_flagged(tmp_path):
    cmap = _setup(tmp_path)
    reward = (
        "set_temp_variable = { treasury_change = 150 }\n"
        "\t\t\tset_temp_variable = { treasury_change = -1 }\n"
        "\t\t\tmodify_treasury_effect = yes"
    )
    issues = _lines(tmp_path, reward, cmap)
    assert len(issues) == 1
    assert "overwritten" in issues[0][0]


def test_clobber_seen_across_intervening_block(tmp_path):
    # ALG_algerian_investments shape: nested blocks between the two writes
    cmap = _setup(tmp_path)
    reward = (
        "set_temp_variable = { treasury_change = -15 }\n"
        "\t\t\trandom_owned_state = {\n"
        "\t\t\t\tadd_extra_state_shared_building_slots = 1\n"
        "\t\t\t}\n"
        "\t\t\tset_temp_variable = { treasury_change = -17 }\n"
        "\t\t\tmodify_treasury_effect = yes"
    )
    issues = _lines(tmp_path, reward, cmap)
    assert len(issues) == 1
    assert "overwritten" in issues[0][0]


def test_branch_gated_writes_are_not_clobbers(tmp_path):
    # if { set X } else { set X } shared-consumer idiom must stay clean
    cmap = _setup(tmp_path)
    reward = (
        "if = {\n"
        "\t\t\t\tlimit = { has_war = yes }\n"
        "\t\t\t\tset_temp_variable = { treasury_change = -10 }\n"
        "\t\t\t}\n"
        "\t\t\telse = {\n"
        "\t\t\t\tset_temp_variable = { treasury_change = -20 }\n"
        "\t\t\t}\n"
        "\t\t\tmodify_treasury_effect = yes"
    )
    assert _lines(tmp_path, reward, cmap) == []


def test_self_referential_rewrite_is_not_a_clobber(tmp_path):
    # raids.txt shape: the re-write folds the old value forward (negation)
    cmap = _setup(tmp_path)
    reward = (
        "set_temp_variable = {\n"
        "\t\t\t\ttreasury_change = {\n"
        "\t\t\t\t\tvalue = gdp_total\n"
        "\t\t\t\t\tmultiply = 0.02\n"
        "\t\t\t\t}\n"
        "\t\t\t}\n"
        "\t\t\tclamp_temp_variable = { var = treasury_change min = 0 max = 200 }\n"
        "\t\t\tset_temp_variable = {\n"
        "\t\t\t\ttreasury_change = {\n"
        "\t\t\t\t\tvalue = treasury_change\n"
        "\t\t\t\t\tmultiply = -1\n"
        "\t\t\t\t}\n"
        "\t\t\t}\n"
        "\t\t\tmodify_treasury_effect = yes"
    )
    assert _lines(tmp_path, reward, cmap) == []


def test_conditional_rewrite_is_not_a_clobber(tmp_path):
    # a deeper, branch-gated re-write may never run; the setter can still win
    cmap = _setup(tmp_path)
    reward = (
        "set_temp_variable = { treasury_change = -10 }\n"
        "\t\t\tif = {\n"
        "\t\t\t\tlimit = { has_war = yes }\n"
        "\t\t\t\tset_temp_variable = { treasury_change = -20 }\n"
        "\t\t\t}\n"
        "\t\t\tmodify_treasury_effect = yes"
    )
    assert _lines(tmp_path, reward, cmap) == []


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


def test_hidden_effect_setter_consumed_outside_is_clean(tmp_path):
    # hidden_effect is the same execution as its parent, not a boundary
    cmap = _setup(tmp_path)
    reward = (
        "hidden_effect = {\n"
        "\t\t\t\tset_temp_variable = { treasury_change = -10 }\n"
        "\t\t\t}\n"
        "\t\t\tmodify_treasury_effect = yes"
    )
    assert _lines(tmp_path, reward, cmap) == []


def test_tooltip_only_consumer_does_not_clear_runtime_setter(tmp_path):
    # a consumer that only exists inside an effect_tooltip never executes
    cmap = _setup(tmp_path)
    reward = (
        "set_temp_variable = { treasury_change = -10 }\n"
        "\t\t\teffect_tooltip = {\n"
        "\t\t\t\tmodify_treasury_effect = yes\n"
        "\t\t\t}"
    )
    assert len(_lines(tmp_path, reward, cmap)) == 1


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


def test_quoted_hash_does_not_break_container_tracking(tmp_path):
    # a '#' inside a log string must not desync brace tracking; the orphan
    # right after it must still be found (and at the right line)
    cmap = _setup(tmp_path)
    reward = (
        'log = "focus TAG_focus_a # inline note"\n'
        "\t\t\tset_temp_variable = { treasury_change = -10 }"
    )
    issues = _lines(tmp_path, reward, cmap)
    assert len(issues) == 1
    assert issues[0][2] == 10


def test_multiline_setter_is_matched(tmp_path):
    cmap = _setup(tmp_path)
    reward = "set_temp_variable = {\n\t\t\t\ttreasury_change = -10\n\t\t\t}"
    assert len(_lines(tmp_path, reward, cmap)) == 1


def test_sibling_container_consumer_does_not_clear(tmp_path):
    # consumer in a different option is a different execution
    cmap = _setup(tmp_path)
    nf_dir = tmp_path / "events"
    nf_dir.mkdir(parents=True, exist_ok=True)
    fpath = nf_dir / "test.txt"
    fpath.write_text(
        "country_event = {\n"
        "\tid = test.1\n"
        "\toption = {\n"
        "\t\tname = test.1.a\n"
        "\t\tset_temp_variable = { treasury_change = -10 }\n"
        "\t}\n"
        "\toption = {\n"
        "\t\tname = test.1.b\n"
        "\t\tmodify_treasury_effect = yes\n"
        "\t}\n"
        "}\n",
        encoding="utf-8",
    )
    issues = process_file_for_orphan_money((str(fpath), str(tmp_path), cmap))
    assert len(issues) == 1


def test_cancel_effect_is_a_container(tmp_path):
    cmap = _setup(tmp_path)
    d_dir = tmp_path / "common" / "decisions"
    d_dir.mkdir(parents=True, exist_ok=True)
    fpath = d_dir / "test.txt"
    fpath.write_text(
        "cat = {\n"
        "\tdec = {\n"
        "\t\tcancel_effect = {\n"
        "\t\t\tset_temp_variable = { treasury_change = -10 }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
        encoding="utf-8",
    )
    issues = process_file_for_orphan_money((str(fpath), str(tmp_path), cmap))
    assert len(issues) == 1


def test_validator_reports_warning_not_error(tmp_path):
    # WARNING severity is what keeps the repo backlog from failing CI --strict
    from validate_variables import Validator

    _setup(tmp_path)
    nf_dir = tmp_path / "common" / "national_focus"
    nf_dir.mkdir(parents=True, exist_ok=True)
    (nf_dir / "test.txt").write_text(
        FOCUS_TEMPLATE.format(reward="set_temp_variable = { treasury_change = -10 }"),
        encoding="utf-8",
    )
    v = Validator(str(tmp_path), use_colors=False, workers=1)
    v.validate_orphan_money_setters()
    assert v.warnings_found == 1
    assert v.errors_found == 0
