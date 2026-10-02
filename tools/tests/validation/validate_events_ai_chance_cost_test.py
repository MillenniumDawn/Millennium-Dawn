"""Event options whose flat ai_chance ignores what the option costs (issue #5096)."""

import argparse
import subprocess
import sys
from multiprocessing import get_context
from pathlib import Path

import pytest
import validator_common
from shared.suite import write_under_str as _write
from validate_events import (
    Validator,
    _add_extra_args,
    costly_scripted_effects,
    find_cost_blind_options,
    stored_variable_signs,
)

_FLAT = "\t\tai_chance = { base = 5 }\n"
_AWARE = (
    "\t\tai_chance = {\n"
    "\t\t\tbase = 10\n"
    "\t\t\tmodifier = { factor = 0.25 has_political_power < 25 }\n"
    "\t\t}\n"
)
_PP_COST = "\t\tadd_political_power = -50\n"

# The shapes of the real effects in common/scripted_effects/00_budget_effects.txt.
_SCRIPTED_EFFECTS = (
    "modify_treasury_effect = {\n"
    "\tif = {\n"
    "\t\tlimit = { NOT = { has_country_flag = MD_skip_treasury_cost } }\n"
    "\t\tadd_to_variable = { treasury = treasury_change }\n"
    "\t}\n"
    "}\n"
    "modify_debt_effect = {\n"
    "\tadd_to_variable = { debt = debt_change }\n"
    "\tclamp_variable = { var = debt min = 0 }\n"
    "}\n"
    "modify_international_investment_effect = {\n"
    "\tadd_to_variable = { int_investments = int_investment_change }\n"
    "}\n"
    "small_expenditure = {\n"
    "\tset_temp_variable = { treasury_change = "
    "{ value = gdp_total multiply = -0.002 } }\n"
    "\tmodify_treasury_effect = yes\n"
    "}\n"
    "one_office_construction = {\n"
    "\tevery_controlled_state = { add_extra_state_shared_building_slots = 1 }\n"
    "\tif = {\n"
    "\t\tlimit = { NOT = { check_variable = { skip_payment = 1 } } }\n"
    "\t\tset_temp_variable = { treasury_change = -12 }\n"
    "\t\tmodify_treasury_effect = yes\n"
    "\t}\n"
    "}\n"
    "two_office_construction = {\n"
    "\tone_office_construction = yes\n"
    "\tone_office_construction = yes\n"
    "}\n"
    "lose_pp_for_15_days = {\n"
    "\tadd_political_power = -25\n"
    "}\n"
    "TAG_pay_or_defer = {\n"
    "\tset_temp_variable = { treasury_change = debt_change }\n"
    "\tmultiply_temp_variable = { treasury_change = -1 }\n"
    "\tmodify_treasury_effect = yes\n"
    "}\n"
    "TAG_bill_the_neighbour = {\n"
    "\tFROM = {\n"
    "\t\tset_temp_variable = { treasury_change = -5 }\n"
    "\t\tmodify_treasury_effect = yes\n"
    "\t}\n"
    "}\n"
    "TAG_loops_forever = {\n"
    "\tadd_stability = -0.01\n"
    "\tTAG_loops_forever = yes\n"
    "}\n"
    "increase_economic_growth = {\n"
    "\tadd_political_power = 10\n"
    "}\n"
    "modify_corporate_tax_rate_effect = {\n"
    "\tset_temp_variable = { calculator_diff = 0 }\n"
    "\tif = {\n"
    "\t\tlimit = { check_variable = { corp_change < 0 } }\n"
    "\t\tsubtract_from_temp_variable = { calculator_diff = corp_change }\n"
    "\t\tadd_to_temp_variable = { corp_change = calculator_diff }\n"
    "\t}\n"
    "\tadd_to_variable = { var = corporate_tax_rate value = corp_change }\n"
    "}\n"
)
_EFFECTS = costly_scripted_effects([_SCRIPTED_EFFECTS])
# What stored_variable_signs reports for a variable only ever set negative.
_STORED = stored_variable_signs(["set_variable = { TAG_project_cost = -4 }\n"])


def _option(name: str, body: str) -> str:
    return "\toption = {\n\t\tname = " + name + "\n" + body + "\t}\n"


def _event(*options: str) -> str:
    return (
        "country_event = {\n"
        "\tid = foo.1\n"
        "\ttitle = foo.1.t\n"
        "\tis_triggered_only = yes\n" + "".join(options) + "}\n"
    )


def _two_options(cost_body: str) -> str:
    return _event(_option("foo.1.a", cost_body), _option("foo.1.b", _FLAT))


def _found(text: str):
    return find_cost_blind_options(text, _EFFECTS, _STORED)


def _validator(tmp_path, **kwargs):
    return Validator(mod_path=str(tmp_path), use_colors=False, workers=1, **kwargs)


@pytest.mark.parametrize("checkout", ["repo", ".claude/worktrees/repo"])
@pytest.mark.parametrize("workers", [1, 2])
def test_worktree_cost_scans_reach_serial_and_parallel_workers(
    tmp_path, monkeypatch, checkout, workers
):
    root = tmp_path / checkout
    for number in range(10):
        _write(root, f"events/{number}.txt", _two_options(_PP_COST + _FLAT))
    _write(
        root,
        ".claude/worktrees/stale/events/ignored.txt",
        _two_options(_PP_COST + _FLAT),
    )
    _write(root, "resources/vanilla/events/ignored.txt", _two_options(_PP_COST + _FLAT))
    v = _validator(root, check_ai_chance_costs=True)
    v.workers = workers
    monkeypatch.setattr(v, "run_validations", v.validate_ai_chance_ignores_cost)
    monkeypatch.setattr(validator_common, "Pool", get_context("spawn").Pool)

    v.run_all_validations()

    assert len(v._issues) == 10
    assert {issue.category for issue in v._issues} == {"event-ai-chance-ignores-cost"}
    assert all("foo.1.a" in issue.message for issue in v._issues)
    assert v._pool is None


def test_cli_path_under_worktrees_reports_known_cost_defect(tmp_path):
    root = tmp_path / ".claude/worktrees/repo"
    _write(root, "events/Ev.txt", _two_options(_PP_COST + _FLAT))
    script = Path(__file__).resolve().parents[2] / "validation/validate_events.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--path",
            str(root),
            "--check-ai-chance-costs",
            "--workers",
            "1",
            "--no-color",
            "--no-cache",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )

    assert "foo.1.a - flat ai_chance ignores the political power cost" in result.stderr


def test_flat_weight_on_a_costed_option_is_flagged(tmp_path):
    _write(tmp_path, "events/Ev.txt", _two_options(_PP_COST + _FLAT))
    v = _validator(tmp_path, check_ai_chance_costs=True)
    v.validate_ai_chance_ignores_cost()
    assert [(i.message, i.file, i.line) for i in v._issues] == [
        ("foo.1.a - flat ai_chance ignores the political power cost", "Ev.txt", 8)
    ]
    assert v._issues[0].category == "event-ai-chance-ignores-cost"
    assert v.warnings_found == 1
    assert v.errors_found == 0


def test_validator_reads_the_mods_scripted_effects(tmp_path):
    _write(tmp_path, "common/scripted_effects/00_budget_effects.txt", _SCRIPTED_EFFECTS)
    _write(
        tmp_path,
        "events/Ev.txt",
        _two_options("\t\tone_office_construction = yes\n" + _FLAT),
    )
    v = _validator(tmp_path, check_ai_chance_costs=True)
    v.validate_ai_chance_ignores_cost()
    assert [i.message for i in v._issues] == [
        "foo.1.a - flat ai_chance ignores the treasury cost"
    ]


def test_check_is_off_without_the_flag(tmp_path):
    _write(tmp_path, "events/Ev.txt", _two_options(_PP_COST + _FLAT))
    v = _validator(tmp_path)
    v.run_validations()
    assert not [i for i in v._issues if i.category == "event-ai-chance-ignores-cost"]


def test_flag_is_registered_on_the_parser():
    parser = argparse.ArgumentParser()
    _add_extra_args(parser)
    assert parser.parse_args([]).check_ai_chance_costs is False
    assert parser.parse_args(["--check-ai-chance-costs"]).check_ai_chance_costs is True


def test_empty_tree_reports_nothing(tmp_path):
    v = _validator(tmp_path, check_ai_chance_costs=True)
    v.validate_ai_chance_ignores_cost()
    assert v._issues == []


def test_modifier_on_the_costed_option_is_clean():
    assert _found(_two_options(_PP_COST + _AWARE)) == []


def test_modifier_on_another_option_does_not_cover_the_costed_one():
    text = _event(
        _option("foo.1.a", _PP_COST + _FLAT),
        _option("foo.1.b", _AWARE),
    )
    assert [found[0] for found in _found(text)] == ["foo.1.a"]


def test_single_option_event_is_clean():
    assert _found(_event(_option("foo.1.a", _PP_COST + _FLAT))) == []


def test_missing_ai_chance_is_flat_and_reports_the_option_line():
    assert _found(_two_options(_PP_COST)) == [("foo.1.a", 5, "political power", False)]


_GATE = "\t\ttrigger = { has_country_flag = foo_flag }\n"


def test_event_with_every_option_gated_is_marked_for_review(tmp_path):
    text = _event(
        _option("foo.1.a", _GATE + _PP_COST + _FLAT),
        _option("foo.1.b", "\t\ttrigger = { NOT = { has_country_flag = foo_flag } }\n"),
    )
    assert _found(text) == [("foo.1.a", 9, "political power", True)]
    _write(tmp_path, "events/Ev.txt", text)
    v = _validator(tmp_path, check_ai_chance_costs=True)
    v.validate_ai_chance_ignores_cost()
    assert [i.message for i in v._issues] == [
        "foo.1.a - flat ai_chance ignores the political power cost"
        " (every option has a trigger; check the AI sees more than one)"
    ]


def test_gated_option_with_an_always_visible_sibling_is_not_marked():
    found = _found(_two_options(_GATE + _PP_COST + _FLAT))
    assert found == [("foo.1.a", 9, "political power", False)]


@pytest.mark.parametrize(
    ("effects", "costs"),
    [
        (
            "\t\tset_temp_variable = { treasury_change = -15.00 }\n"
            "\t\tmodify_treasury_effect = yes\n",
            "treasury",
        ),
        (
            "\t\tset_temp_variable = { treasury_change = gdp_total }\n"
            "\t\tmultiply_temp_variable = { treasury_change = -0.01 }\n"
            "\t\tmodify_treasury_effect = yes\n",
            "treasury",
        ),
        (
            "\t\tset_temp_variable = { treasury_change = GER.gdp_per_capita }\n"
            "\t\tdivide_temp_variable = { treasury_change = -2 }\n"
            "\t\tmodify_treasury_effect = yes\n",
            "treasury",
        ),
        (
            "\t\tset_temp_variable = { treasury_change = "
            "{ value = gdp_total multiply = -0.03 } }\n"
            "\t\tmodify_treasury_effect = yes\n",
            "treasury",
        ),
        (
            "\t\tset_temp_variable = { our_cost = -5 }\n"
            "\t\tset_temp_variable = { treasury_change = our_cost }\n"
            "\t\tmodify_treasury_effect = yes\n",
            "treasury",
        ),
        (
            "\t\tset_temp_variable = { debt_change = 10 }\n"
            "\t\tmodify_debt_effect = yes\n",
            "debt",
        ),
        (
            "\t\tset_temp_variable = { debt_change = ROOT.gdp_per_capita }\n"
            "\t\tmultiply_temp_variable = { debt_change = 0.5 }\n"
            "\t\tmodify_debt_effect = yes\n",
            "debt",
        ),
        (
            "\t\tset_temp_variable = { int_investment_change = -5 }\n"
            "\t\tmodify_international_investment_effect = yes\n",
            "international investment",
        ),
        (
            "\t\tset_temp_variable = { treasury_change = 5 }\n"
            "\t\tmodify_treasury_effect = yes\n"
            "\t\tset_temp_variable = { treasury_change = -5 }\n"
            "\t\tmodify_treasury_effect = yes\n",
            "treasury",
        ),
        (
            "\t\tset_temp_variable = { needed_money = 0 }\n"
            "\t\tsubtract_from_temp_variable = { needed_money = 4.5 }\n"
            "\t\tset_temp_variable = { treasury_change = needed_money }\n"
            "\t\tmodify_treasury_effect = yes\n",
            "treasury",
        ),
        (
            "\t\tset_temp_variable = { treasury_change = 5 }\n"
            "\t\tif = {\n"
            "\t\t\tlimit = { has_war = yes }\n"
            "\t\t\tset_temp_variable = { treasury_change = -5 }\n"
            "\t\t}\n"
            "\t\tmodify_treasury_effect = yes\n",
            "treasury",
        ),
        (
            "\t\tif = {\n"
            "\t\t\tlimit = { has_war = yes }\n"
            "\t\t\tset_temp_variable = { treasury_change = 5 }\n"
            "\t\t}\n"
            "\t\telse = {\n"
            "\t\t\tset_temp_variable = { treasury_change = -5 }\n"
            "\t\t}\n"
            "\t\tmodify_treasury_effect = yes\n",
            "treasury",
        ),
        (
            "\t\tset_temp_variable = { treasury_change = gdp_total }\n"
            "\t\trandom_list = {\n"
            "\t\t\t50 = { multiply_temp_variable = { treasury_change = -1 } }\n"
            "\t\t\t50 = { }\n"
            "\t\t}\n"
            "\t\tmodify_treasury_effect = yes\n",
            "treasury",
        ),
        (
            "\t\tset_temp_variable = { treasury_change = FROM.TAG_project_cost }\n"
            "\t\tmodify_treasury_effect = yes\n",
            "treasury",
        ),
        ("\t\tadd_to_variable = { treasury = -5 }\n", "treasury"),
        ("\t\tadd_to_variable = { var = treasury value = -5 }\n", "treasury"),
        ("\t\tsubtract_from_variable = { treasury = loan_amount }\n", "treasury"),
        (
            "\t\tset_temp_variable = { corp_change = 10 }\n"
            "\t\tmodify_corporate_tax_rate_effect = yes\n",
            "tax rate",
        ),
        (
            "\t\tset_temp_variable = { corp_change = -5 }\n"
            "\t\tmodify_corporate_tax_rate_effect = yes\n",
            "tax rate",
        ),
        ("\t\tsubtract_from_variable = { population_tax_rate = 5 }\n", "tax rate"),
        (
            "\t\tmeta_effect = {\n"
            "\t\t\ttext = { add_stability = -[LOSS] }\n"
            '\t\t\tLOSS = "0.05"\n'
            "\t\t}\n",
            "stability",
        ),
        ("\t\tadd_to_variable = { debt = 5 }\n", "debt"),
        (
            "\t\tsubtract_from_variable = { int_investments = 5 }\n",
            "international investment",
        ),
        ("\t\tsmall_expenditure = yes\n", "treasury"),
        ("\t\tone_office_construction = yes\n", "treasury"),
        ("\t\ttwo_office_construction = yes\n", "treasury"),
        ("\t\tlose_pp_for_15_days = yes\n", "political power"),
        (
            "\t\tset_temp_variable = { debt_change = 3 }\n\t\tTAG_pay_or_defer = yes\n",
            "treasury",
        ),
        ("\t\tTAG_loops_forever = yes\n", "stability"),
        ("\t\tadd_stability = -0.02\n", "stability"),
        ("\t\tadd_war_support = -0.05\n", "war support"),
        (
            "\t\tif = {\n"
            "\t\t\tlimit = { has_war = no }\n"
            "\t\t\tadd_stability = -0.02\n"
            "\t\t}\n",
            "stability",
        ),
        ("\t\thidden_effect = { add_political_power = -25 }\n", "political power"),
        (
            "\t\tadd_stability = -0.02\n" + _PP_COST + "\t\tsmall_expenditure = yes\n",
            "treasury, political power, stability",
        ),
    ],
)
def test_cost_kinds_are_detected(effects, costs):
    found = _found(_two_options(effects + _FLAT))
    assert [(name, kinds) for name, _line, kinds, _gated in found] == [
        ("foo.1.a", costs)
    ]


@pytest.mark.parametrize(
    "effects",
    [
        "\t\tadd_political_power = 50\n",
        "\t\tadd_stability = 0.02\n",
        "\t\tset_temp_variable = { treasury_change = 15 }\n"
        "\t\tmodify_treasury_effect = yes\n",
        "\t\tset_temp_variable = { treasury_change = -15 }\n",
        "\t\tmodify_treasury_effect = yes\n",
        "\t\tset_temp_variable = { treasury_change = gdp_total }\n"
        "\t\tmodify_treasury_effect = yes\n",
        "\t\tset_temp_variable = { treasury_change = -5 }\n"
        "\t\tmultiply_temp_variable = { treasury_change = -1 }\n"
        "\t\tmodify_treasury_effect = yes\n",
        "\t\tset_temp_variable = { treasury_change = "
        "{ value = gdp_total multiply = 0.09 } }\n"
        "\t\tmodify_treasury_effect = yes\n",
        "\t\tset_temp_variable = { treasury_change = -15 }\n"
        "\t\tFROM = { modify_treasury_effect = yes }\n",
        "\t\tset_temp_variable = { debt_change = -10 }\n\t\tmodify_debt_effect = yes\n",
        "\t\tset_temp_variable = { debt_change = "
        "{ value = debt_bailout multiply = -1 } }\n"
        "\t\tmodify_debt_effect = yes\n",
        "\t\tset_temp_variable = { int_investment_change = 5 }\n"
        "\t\tmodify_international_investment_effect = yes\n",
        "\t\tset_temp_variable = { treasury_change = 0 }\n"
        "\t\tmodify_treasury_effect = yes\n",
        "\t\tadd_to_variable = { debt = 0 }\n",
        "\t\tset_temp_variable = { treasury_change = TAG_income }\n"
        "\t\tmodify_treasury_effect = yes\n",
        "\t\tif = {\n"
        "\t\t\tlimit = { has_war = yes }\n"
        "\t\t\tset_temp_variable = { treasury_change = 5 }\n"
        "\t\t}\n"
        "\t\telse = {\n"
        "\t\t\tset_temp_variable = { treasury_change = 10 }\n"
        "\t\t}\n"
        "\t\tmodify_treasury_effect = yes\n",
        "\t\tset_temp_variable = { relief = int_investments }\n"
        "\t\tif = {\n"
        "\t\t\tlimit = { check_variable = { relief > debt } }\n"
        "\t\t\tsubtract_from_temp_variable = { relief = debt }\n"
        "\t\t\tadd_to_variable = { treasury = relief }\n"
        "\t\t}\n"
        "\t\telse = {\n"
        "\t\t\tsubtract_from_variable = { debt = relief }\n"
        "\t\t}\n",
        "\t\tif = {\n"
        "\t\t\tlimit = { has_war = yes }\n"
        "\t\t\tset_temp_variable = { treasury_change = -5 }\n"
        "\t\t\telse = {\n"
        "\t\t\t\tmodify_treasury_effect = yes\n"
        "\t\t\t}\n"
        "\t\t}\n",
        "\t\tset_variable = { treasury = 100 }\n",
        "\t\tadd_to_temp_variable = { treasury = -5 }\n",
        "\t\tadd_to_variable = { treasury = SOV.treasury }\n",
        "\t\tsubtract_from_variable = { debt = debt_bailout }\n",
        "\t\tadd_to_variable = { TAG_other_variable = -5 }\n",
        "\t\tincrease_economic_growth = yes\n",
        "\t\tTAG_bill_the_neighbour = yes\n",
        "\t\tTAG_unknown_effect = yes\n",
        "\t\tFROM = { add_political_power = -50 }\n",
        "\t\tFROM = { one_office_construction = yes }\n",
        "\t\tevery_other_country = { add_stability = -0.02 }\n",
        '\t\tlog = "add_political_power = -50"\n',
    ],
)
def test_not_a_cost_to_the_choosing_country(effects):
    assert _found(_two_options(effects + _FLAT)) == []


def test_only_effects_that_can_charge_the_caller_are_kept():
    assert set(_EFFECTS) == {
        "modify_treasury_effect",
        "modify_debt_effect",
        "modify_international_investment_effect",
        "small_expenditure",
        "one_office_construction",
        "two_office_construction",
        "lose_pp_for_15_days",
        "TAG_pay_or_defer",
        "TAG_loops_forever",
        "modify_corporate_tax_rate_effect",
    }


def test_stored_variable_signs_keeps_what_is_set_negative():
    text = (
        "set_variable = { TAG_cost = -4 }\n"
        "set_variable = { var = FROM.TAG_other value = -2 }\n"
        "set_variable = { TAG_income = 3 }\n"
        "set_variable = { TAG_mixed = -1 }\n"
        "set_variable = { TAG_mixed = 2 }\n"
        "set_variable = { TAG_copy = TAG_cost }\n"
        "set_temp_variable = { TAG_temp = -1 }\n"
    )
    assert stored_variable_signs([text]) == {
        "TAG_cost": 1,
        "TAG_other": 1,
        "TAG_mixed": 3,
    }


def test_validator_reads_stored_signs_from_the_whole_mod(tmp_path):
    _write(tmp_path, "common/scripted_effects/00_budget_effects.txt", _SCRIPTED_EFFECTS)
    _write(
        tmp_path,
        "common/decisions/TAG.txt",
        "TAG_decision = {\n"
        "\tcomplete_effect = { set_variable = { TAG_rail_cost = -4 } }\n"
        "}\n",
    )
    body = (
        "\t\tset_temp_variable = { treasury_change = TAG_rail_cost }\n"
        "\t\tmodify_treasury_effect = yes\n"
    )
    _write(tmp_path, "events/Ev.txt", _two_options(body + _FLAT))
    v = _validator(tmp_path, check_ai_chance_costs=True)
    v.validate_ai_chance_ignores_cost()
    assert [i.message for i in v._issues] == [
        "foo.1.a - flat ai_chance ignores the treasury cost"
    ]


def test_commented_cost_is_ignored_by_the_validator(tmp_path):
    body = "\t\t#add_political_power = -50\n" + _FLAT
    _write(tmp_path, "events/Ev.txt", _two_options(body))
    v = _validator(tmp_path, check_ai_chance_costs=True)
    v.validate_ai_chance_ignores_cost()
    assert v._issues == []


def test_reference_pattern_is_clean_and_its_flat_sibling_is_flagged():
    pay = (
        "\t\tset_temp_variable = { treasury_change = -15.00 }\n"
        "\t\tmodify_treasury_effect = yes\n"
        "\t\tai_chance = {\n"
        "\t\t\tbase = 10\n"
        "\t\t\tmodifier = { factor = 0.25 has_active_mission = "
        "bankruptcy_incoming_collapse }\n"
        "\t\t}\n"
    )
    decline = "\t\tadd_stability = -0.02\n\t\tai_chance = { base = 1 }\n"
    text = _event(_option("foo.1.a", pay), _option("foo.1.b", decline))
    assert _found(text) == [("foo.1.b", 17, "stability", False)]
