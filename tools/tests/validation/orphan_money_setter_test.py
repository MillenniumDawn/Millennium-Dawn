"""Tests for the orphan money-setter check in validate_variables.

A set_temp_variable of treasury_change/debt_change/int_investment_change with
no consumer call afterwards in the same effect block is a dead setter — the
transfer silently never happens (Sweden_foci.57). Consumers are derived from
scripted-effect bodies so wrappers (GRE_pay_or_defer) clear the setter too.
party_popularity_increase and change_relative_party_popularity follow the
same rule (issue #5320).
"""

import pytest
from shared.suite import variable_scan
from validate_variables import Validator, build_money_consumer_map

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
change_relative_party_popularity = {
	if = {
		limit = { check_variable = { party_popularity_increase > 1 } }
		set_temp_variable = { party_popularity_increase = 1 }
	}
	add_to_variable = { party_pop_array^party_index = party_popularity_increase }
}
move_party_popularity = {
	set_temp_variable = { party_popularity_increase = _party_pop_delta }
	change_relative_party_popularity = yes
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
    return build_money_consumer_map(
        [str(fx_dir / "00_budget_effects.txt")], str(tmp_path)
    )


def _lines(tmp_path, reward, consumer_map):
    nf_dir = tmp_path / "common" / "national_focus"
    nf_dir.mkdir(parents=True, exist_ok=True)
    fpath = nf_dir / "test.txt"
    fpath.write_text(FOCUS_TEMPLATE.format(reward=reward), encoding="utf-8")
    return variable_scan(fpath, "orphan", tmp_path, consumer_map=consumer_map)


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
    issues = variable_scan(fpath, "orphan", tmp_path, consumer_map=cmap)
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
    issues = variable_scan(fpath, "orphan", tmp_path, consumer_map=cmap)
    assert len(issues) == 1


def test_party_popularity_setter_needs_its_consumer(tmp_path):
    cmap = _setup(tmp_path)
    setter = "set_temp_variable = { party_popularity_increase = 0.45 }"
    assert _lines(tmp_path, setter, cmap)[0][0].endswith("never applied")
    consumed = setter + "\n\t\t\tchange_relative_party_popularity = yes"
    assert _lines(tmp_path, consumed, cmap) == []


def test_party_popularity_setter_clobbered_by_next_party(tmp_path):
    # Syria shape: two parties set up back to back, one consumer call
    cmap = _setup(tmp_path)
    reward = (
        "set_temp_variable = { party_index = 20 }\n"
        "\t\t\tset_temp_variable = { party_popularity_increase = 0.30 }\n"
        "\t\t\tset_temp_variable = { party_index = 5 }\n"
        "\t\t\tset_temp_variable = { party_popularity_increase = 0.10 }\n"
        "\t\t\tchange_relative_party_popularity = yes"
    )
    issues = _lines(tmp_path, reward, cmap)
    assert [(i[2], "overwritten" in i[0]) for i in issues] == [(10, True)]


def test_move_party_popularity_does_not_consume_the_setter(tmp_path):
    # it writes party_popularity_increase itself, so the caller's value is lost
    cmap = _setup(tmp_path)
    assert "move_party_popularity" not in cmap["party_popularity_increase"]
    reward = (
        "set_temp_variable = { party_popularity_increase = 0.05 }\n"
        "\t\t\tmove_party_popularity = yes"
    )
    assert len(_lines(tmp_path, reward, cmap)) == 1


PARTY_SETTER = "set_temp_variable = { party_popularity_increase = 0.25 }"


def _validator_rows(tmp_path, rel, text):
    _setup(tmp_path)
    fpath = tmp_path / rel
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(text, encoding="utf-8")
    v = Validator(str(tmp_path), use_colors=False, workers=1)
    v.validate_orphan_money_setters()
    return [(i.file, i.line) for i in v._issues]


@pytest.mark.parametrize(
    "rel, first, second",
    [
        ("common/ideas/test.txt", "on_add", "on_remove"),
        ("common/bop/test.txt", "on_activate", "on_deactivate"),
        ("common/scripted_guis/test.txt", "TST_a_click", "TST_a_right_click"),
    ],
)
def test_effect_blocks_outside_focuses_and_events(tmp_path, rel, first, second):
    # each block is its own execution, so neither setter sees the other's call
    text = (
        "outer = {\n"
        f"\t{first} = {{\n\t\t{PARTY_SETTER}\n\t}}\n"
        f"\t{second} = {{\n\t\t{PARTY_SETTER}\n"
        "\t\tchange_relative_party_popularity = yes\n\t}\n"
        f"\t{second} = {{\n\t\t{PARTY_SETTER}\n\t}}\n"
        "}\n"
    )
    assert _validator_rows(tmp_path, rel, text) == [(rel, 3), (rel, 10)]


def test_scripted_effect_body_is_a_container(tmp_path):
    # the consumer in BASE_EFFECTS re-sets its own input and must stay clean
    rel = "common/scripted_effects/test.txt"
    text = (
        f"TST_dead = {{\n\t{PARTY_SETTER}\n}}\n"
        f"TST_applied = {{\n\t{PARTY_SETTER}\n"
        "\tchange_relative_party_popularity = yes\n}\n"
    )
    assert _validator_rows(tmp_path, rel, text) == [(rel, 2)]


def test_validator_reports_error(tmp_path):
    _setup(tmp_path)
    nf_dir = tmp_path / "common" / "national_focus"
    nf_dir.mkdir(parents=True, exist_ok=True)
    (nf_dir / "test.txt").write_text(
        FOCUS_TEMPLATE.format(reward="set_temp_variable = { treasury_change = -10 }"),
        encoding="utf-8",
    )
    v = Validator(str(tmp_path), use_colors=False, workers=1)
    v.validate_orphan_money_setters()
    assert v.errors_found == 1
    assert v.warnings_found == 0
