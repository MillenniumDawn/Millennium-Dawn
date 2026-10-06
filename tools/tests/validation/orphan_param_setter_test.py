"""Tests for the dead parameter setter check in validate_scripted_params.

A parameter declared in a "# Parameters:" block that is set in an effect block
and never used there is a dead setter: the value never reaches the effect
(Sweden_foci.57, issue #5320). Any scripted effect or trigger that reads the
parameter consumes it, with or without a contract of its own.
"""

from pathlib import Path

import pytest
import validate_scripted_params as vsp
from shared.suite import run_validator
from shared.suite import write_text as _write

ROOT = Path(__file__).resolve().parents[3]

EFFECTS = """# Parameters:
# - treasury_change: amount
modify_treasury_effect = {
	add_to_variable = { treasury = treasury_change }
}
# Parameters:
# - debt_change: amount
modify_debt_effect = {
	add_to_variable = { debt = debt_change }
}
pay_wrapper = {
	multiply_temp_variable = { treasury_change = 1.5 }
	modify_treasury_effect = yes
}
outer_pay = {
	pay_wrapper = yes
}
outermost_pay = {
	outer_pay = yes
}
negating_wrapper = {
	set_temp_variable = { treasury_change = { value = treasury_change multiply = -1 } }
	modify_treasury_effect = yes
}
read_then_reset = {
	add_to_variable = { TST_total = treasury_change }
	set_temp_variable = { treasury_change = 0 }
}
gated_write_wrapper = {
	if = {
		limit = { has_war = yes }
		set_temp_variable = { treasury_change = 0 }
	}
	modify_treasury_effect = yes
}
overwriting_wrapper = {
	set_temp_variable = { treasury_change = -5 }
	modify_treasury_effect = yes
}
write_then_read = {
	set_temp_variable = { var = treasury_change value = -5 }
	add_to_variable = { treasury = treasury_change }
}
commented_reader = {
	# add_to_variable = { treasury = treasury_change }
	add_stability = 0.01
}
random_producer = {
	set_temp_variable_to_random = {
		var = treasury_change
		min = 2
		max = 8
	}
	modify_treasury_effect = yes
}
# Parameters:
# set_temp_variable = { party_index = X } #OPTIONAL
# set_temp_variable = { party_popularity_increase = Y } #OPTIONAL
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
TRIGGERS = """is_party_banned_trigger = {
	check_variable = { party_banned_array^party_index = 1 }
}
"""

SET = "set_temp_variable = { treasury_change = -10 }"
PARTY_SET = "set_temp_variable = { party_popularity_increase = 0.25 }"
PAY = "modify_treasury_effect = yes"


def _option(*lines):
    """An event option holding the given statements, the first on line 4."""
    body = "".join(f"\t\t{line}\n" for line in lines)
    return f"country_event = {{\n\tid = tst.1\n\toption = {{\n{body}\t}}\n}}\n"


def _issues(tmp_path, body, rel="events/test.txt"):
    _write(tmp_path / "common" / "scripted_effects" / "effects.txt", EFFECTS)
    _write(tmp_path / "common" / "scripted_triggers" / "triggers.txt", TRIGGERS)
    _write(tmp_path / rel, body)
    validator = run_validator(vsp.Validator, tmp_path)
    return [i for i in validator._issues if i.category == "orphan-param-setter"]


def _findings(tmp_path, body, rel="events/test.txt"):
    """(line, kind) for each dead setter the validator reports in one file."""
    return [
        (i.line, "overwritten" if "overwritten" in i.message else "never")
        for i in _issues(tmp_path, body, rel)
    ]


def test_dead_setter_is_an_error_naming_the_declaring_effect(tmp_path):
    (issue,) = _issues(tmp_path, _option(SET))
    assert issue.severity == vsp.Severity.ERROR
    assert (issue.file, issue.line) == ("events/test.txt", 4)
    assert "no modify_treasury_effect call" in issue.message


@pytest.mark.parametrize(
    "effect, dead",
    [
        ("modify_treasury_effect", False),
        ("pay_wrapper", False),
        # outermost_pay -> outer_pay -> pay_wrapper needs the closure
        ("outermost_pay", False),
        # a write that reads the parameter folds the caller's value forward
        ("negating_wrapper", False),
        ("read_then_reset", False),
        # a write inside a branch may not run
        ("gated_write_wrapper", False),
        ("overwriting_wrapper", True),
        ("write_then_read", True),
        ("commented_reader", True),
        # set_temp_variable_to_random produces its own value (ct_ai_seize_assets)
        ("random_producer", True),
        ("modify_debt_effect", True),
    ],
)
def test_only_an_effect_that_reads_the_parameter_consumes_it(tmp_path, effect, dead):
    found = _findings(tmp_path, _option(SET, f"{effect} = yes"))
    assert found == ([(4, "never")] if dead else [])


def test_setter_overwritten_before_use_is_dead(tmp_path):
    # ALG_algerian_investments shape: nested blocks between the two writes
    body = _option(
        "set_temp_variable = { treasury_change = -15 }",
        "random_owned_state = {",
        "\tadd_extra_state_shared_building_slots = 1",
        "}",
        "set_temp_variable = { treasury_change = -17 }",
        PAY,
    )
    assert _findings(tmp_path, body) == [(4, "overwritten")]


_DEAD_FORMS = {
    "long form": "set_temp_variable = { var = treasury_change value = -10 }",
    "add_to": "add_to_temp_variable = { treasury_change = -10 }",
    "subtract_from": "subtract_from_temp_variable = { treasury_change = 10 }",
}


@pytest.mark.parametrize("setter", _DEAD_FORMS.values(), ids=_DEAD_FORMS.keys())
def test_every_form_that_hands_over_a_value_is_a_setter(tmp_path, setter):
    assert _findings(tmp_path, _option(setter)) == [(4, "never")]
    assert _findings(tmp_path, _option(setter, PAY)) == []


def test_long_form_write_overwrites_an_earlier_setter(tmp_path):
    body = _option(
        SET, "set_temp_variable = { var = treasury_change value = -20 }", PAY
    )
    assert _findings(tmp_path, body) == [(4, "overwritten")]


_NOT_CLOBBERS = {
    "used before the rewrite": (
        SET,
        PAY,
        "set_temp_variable = { treasury_change = -20 }",
        PAY,
    ),
    # Sweden shape: the cost is built up, then charged once
    "accumulated": (SET, "add_to_temp_variable = { treasury_change = -3 }", PAY),
    "if and else arms": (
        "if = {",
        "\tlimit = { has_war = yes }",
        f"\t{SET}",
        "}",
        "else = {",
        "\tset_temp_variable = { treasury_change = -20 }",
        "}",
        PAY,
    ),
    "conditional rewrite": (
        SET,
        'log = "money # note"',
        "if = { limit = { always = yes } set_temp_variable = { treasury_change = 8 } }",
        PAY,
    ),
    # raids.txt shape: the re-write folds the old value forward
    "self-reading rewrite": (
        "set_temp_variable = { treasury_change = { value = gdp_total multiply = 0.02 } }",
        "clamp_temp_variable = { var = treasury_change min = 0 max = 200 }",
        "set_temp_variable = {",
        "\ttreasury_change = {",
        "\t\tvalue = treasury_change",
        "\t\tmultiply = -1",
        "\t}",
        "}",
        PAY,
    ),
}


@pytest.mark.parametrize("lines", _NOT_CLOBBERS.values(), ids=_NOT_CLOBBERS.keys())
def test_branch_gated_and_self_reading_rewrites_do_not_clobber(tmp_path, lines):
    assert _findings(tmp_path, _option(*lines)) == []


_USES = {
    "direct read": ("add_to_variable = { TST_total = treasury_change }", False),
    "check": ("if = { limit = { check_variable = { treasury_change < 0 } } }", False),
    "changing it": ("multiply_temp_variable = { treasury_change = 2 }", True),
    "clamping it": ("clamp_temp_variable = { var = treasury_change min = 0 }", True),
    "commented-out call": ("# modify_treasury_effect = yes", True),
    "quoted call": ('log = "modify_treasury_effect = yes treasury_change"', True),
}


@pytest.mark.parametrize("line, dead", _USES.values(), ids=_USES.keys())
def test_a_read_uses_the_parameter_and_a_change_to_it_does_not(tmp_path, line, dead):
    found = _findings(tmp_path, _option(SET, line))
    assert found == ([(4, "never")] if dead else [])


def test_scripted_trigger_that_reads_the_parameter_consumes_it(tmp_path):
    body = _option(
        "if = {",
        "\tlimit = {",
        "\t\tset_temp_variable = { party_index = 3 }",
        "\t\tis_party_banned_trigger = yes",
        "\t}",
        "}",
    )
    assert _findings(tmp_path, body) == []


_TOOLTIPS = {
    # previewed there, so it must be used there
    "tooltip setter, runtime use": (("effect_tooltip = {", f"\t{SET}", "}", PAY), 5),
    "self-contained tooltip": (("effect_tooltip = {", f"\t{SET}", f"\t{PAY}", "}"), 0),
    # hidden_effect is the same execution as its parent, not a boundary
    "hidden setter": (("hidden_effect = {", f"\t{SET}", "}", PAY), 0),
    # AfricanUnion shape: the value only feeds an "if they accept" preview
    "runtime setter, tooltip use": ((SET, "effect_tooltip = {", f"\t{PAY}", "}"), 0),
}


@pytest.mark.parametrize("lines, dead_line", _TOOLTIPS.values(), ids=_TOOLTIPS.keys())
def test_effect_tooltip_is_its_own_block_for_setters_inside_it(
    tmp_path, lines, dead_line
):
    expected = [(dead_line, "never")] if dead_line else []
    assert _findings(tmp_path, _option(*lines)) == expected


_NOT_REPORTED = {
    "reset to zero": _option(PAY, "set_temp_variable = { treasury_change = 0 }"),
    "undeclared variable": _option("set_temp_variable = { TST_scratch = 5 }"),
    # an unbalanced container is dropped, so its setter has no holder block
    "unbalanced block": f"option = {{\n\t{SET}\n",
}


@pytest.mark.parametrize("body", _NOT_REPORTED.values(), ids=_NOT_REPORTED.keys())
def test_setters_that_are_not_reported(tmp_path, body):
    assert _findings(tmp_path, body) == []


def test_scripted_effect_body_is_not_scanned(tmp_path):
    # a loose body may produce the value for its caller
    rel = "common/scripted_effects/producer.txt"
    assert _findings(tmp_path, f"TST_producer = {{\n\t{SET}\n}}\n", rel) == []


def test_each_parameter_is_tracked_on_its_own(tmp_path):
    body = _option(SET, PAY, "set_temp_variable = { debt_change = -4 }", PAY)
    assert _findings(tmp_path, body) == [(6, "never")]


def test_multiline_setter_reports_its_first_line(tmp_path):
    body = _option(
        'log = "focus TAG_focus_a # inline note"',
        "set_temp_variable = {",
        "\ttreasury_change = -10",
        "}",
    )
    assert _findings(tmp_path, body) == [(5, "never")]


def test_use_in_a_sibling_option_does_not_count(tmp_path):
    body = (
        "country_event = {\n\tid = tst.1\n"
        f"\toption = {{\n\t\t{SET}\n\t}}\n"
        f"\toption = {{\n\t\t{PAY}\n\t}}\n"
        "}\n"
    )
    assert _findings(tmp_path, body) == [(4, "never")]


_BLOCKS = [
    "completion_reward",
    "completion_reward_joint_originator",
    "completion_reward_joint_member",
    "select_effect",
    "bypass_effect",
    "immediate",
    "option",
    "complete_effect",
    "remove_effect",
    "timeout_effect",
    "cancel_effect",
    "effect",
    "on_add",
    "on_remove",
    "on_activate",
    "on_deactivate",
    "on_complete",
    "outcome_extra_execute",
]


def test_block_list_names_every_effect_block_keyword():
    assert set(_BLOCKS) == vsp.EFFECT_BLOCK_KEYWORDS


@pytest.mark.parametrize("block", [*_BLOCKS, "TST_a_click", "TST_a_right_click"])
def test_each_effect_block_is_its_own_execution(tmp_path, block):
    # the first setter cannot see the call in the sibling block
    body = (
        "outer = {\n"
        f"\t{block} = {{\n\t\t{PARTY_SET}\n\t}}\n"
        f"\t{block} = {{\n\t\t{PARTY_SET}\n"
        "\t\tchange_relative_party_popularity = yes\n\t}\n"
        "}\n"
    )
    assert _findings(tmp_path, body, "common/ideas/test.txt") == [(3, "never")]


def test_second_party_setup_overwrites_the_first(tmp_path):
    # Syria shape: two parties set up back to back, one call
    body = _option(
        "set_temp_variable = { party_index = 20 }",
        "set_temp_variable = { party_popularity_increase = 0.30 }",
        "set_temp_variable = { party_index = 5 }",
        "set_temp_variable = { party_popularity_increase = 0.10 }",
        "change_relative_party_popularity = yes",
    )
    assert _findings(tmp_path, body) == [(4, "overwritten"), (5, "overwritten")]


def test_party_popularity_setter_with_a_call_after_each_is_clean(tmp_path):
    body = _option(
        "set_temp_variable = { party_popularity_increase = 0.30 }",
        "change_relative_party_popularity = yes",
        "set_temp_variable = { party_popularity_increase = 0.10 }",
        "change_relative_party_popularity = yes",
    )
    assert _findings(tmp_path, body) == []


def test_party_popularity_setter_with_no_call_names_the_effect(tmp_path):
    (issue,) = _issues(tmp_path, _option(PARTY_SET))
    assert issue.severity == vsp.Severity.ERROR
    assert issue.line == 4
    assert "party_popularity_increase" in issue.message
    assert "no change_relative_party_popularity call" in issue.message


def test_setter_clobbered_in_an_idea_on_add_is_flagged(tmp_path):
    body = (
        "ideas = {\n"
        "\tcountry = {\n"
        "\t\ttest_idea = {\n"
        "\t\t\ton_add = {\n"
        "\t\t\t\thidden_effect = {\n"
        f"\t\t\t\t\t{PARTY_SET}\n"
        f"\t\t\t\t\t{PARTY_SET}\n"
        "\t\t\t\t\tchange_relative_party_popularity = yes\n"
        "\t\t\t\t}\n"
        "\t\t\t}\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )
    assert _findings(tmp_path, body, "common/ideas/test.txt") == [(6, "overwritten")]


def test_move_party_popularity_does_not_consume_the_setter(tmp_path):
    # it writes party_popularity_increase itself, so the caller's value is lost
    body = _option(PARTY_SET, "move_party_popularity = yes")
    assert _findings(tmp_path, body) == [(4, "never")]


_BUDGET = "common/scripted_effects/00_budget_effects.txt"
_POLITICS = "common/scripted_effects/00_MD_politicsview_scripted_effects.txt"


@pytest.mark.parametrize(
    "rel, effect, required, optional",
    [
        (_BUDGET, "modify_treasury_effect", ["treasury_change"], []),
        (_BUDGET, "modify_debt_effect", ["debt_change"], []),
        (
            _BUDGET,
            "modify_international_investment_effect",
            ["int_investment_change"],
            [],
        ),
        (
            _POLITICS,
            "change_relative_party_popularity",
            [],
            ["party_index", "party_popularity_increase", "temp_outlook_increase"],
        ),
    ],
)
def test_game_file_still_declares_the_contract(rel, effect, required, optional):
    # the contract is a comment block, so a stray edit can switch the check off
    contracts = vsp._parse_effect_contracts_from_file(str(ROOT / rel))
    assert contracts[effect] == {"required": required, "optional": optional}
