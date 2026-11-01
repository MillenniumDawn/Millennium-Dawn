"""Event options whose ai_chance ignores what the option costs (issue #5096)."""

import argparse
import subprocess
import sys
from multiprocessing import get_context
from pathlib import Path

import pytest
import validate_events
import validator_common
from shared.suite import write_under_str as _write
from validate_events import (
    Validator,
    _add_extra_args,
    costly_scripted_effects,
    find_option_cost_weights,
    money_commitment_effects,
    stored_variable_signs,
)

_FLAT = "\t\tai_chance = { base = 5 }\n"
_AWARE = (
    "\t\tai_chance = {\n"
    "\t\t\tbase = 10\n"
    "\t\t\tmodifier = { factor = 0.25 has_active_mission = "
    "bankruptcy_incoming_collapse }\n"
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
    "TAG_war_only_cost = {\n"
    "\tif = {\n"
    "\t\tlimit = { has_war = yes }\n"
    "\t\tadd_political_power = -50\n"
    "\t}\n"
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
_COMMITMENTS = money_commitment_effects(
    {
        "TAG_raise_spending": "set_country_flag = spending_law_scripted_change",
        "TAG_reform": "TAG_raise_spending = yes",
    }
)


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
    return find_option_cost_weights(text, _EFFECTS, _STORED, _COMMITMENTS)[0]


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

    assert "foo.1.a - ai_chance ignores the political power cost" in result.stderr


def test_flag_is_registered_on_the_parser():
    parser = argparse.ArgumentParser()
    _add_extra_args(parser)
    assert parser.parse_args([]).check_ai_chance_costs is False
    assert parser.parse_args(["--check-ai-chance-costs"]).check_ai_chance_costs is True


_GATE = "\t\ttrigger = { has_country_flag = foo_flag }\n"
_ALL_GATED = _event(
    _option("foo.1.a", _GATE + _PP_COST + _FLAT),
    _option("foo.1.b", "\t\ttrigger = { NOT = { has_country_flag = foo_flag } }\n"),
)
_TAG_SPLIT = _event(
    _option("foo.1.a", "\t\ttrigger = { tag = ISR }\n" + _PP_COST + _FLAT),
    _option("foo.1.b", "\t\ttrigger = { tag = HEZ }\n" + _AWARE),
)
_PP_BLIND = "foo.1.a - ai_chance ignores the political power cost"
_TREASURY_BLIND = "foo.1.a - ai_chance ignores the treasury cost"
_BUDGET = "common/scripted_effects/00_budget_effects.txt"


_BLIND_AND_UNNEEDED = _event(
    _option("foo.1.a", _PP_COST + _FLAT), _option("foo.1.b", _AWARE)
)
_COST_CATEGORIES = {"event-ai-chance-ignores-cost", "event-unneeded-treasury-guard"}


def test_check_is_off_without_the_flag(tmp_path):
    _write(tmp_path, "events/Ev.txt", _BLIND_AND_UNNEEDED)
    v = _validator(tmp_path)
    v.run_validations()
    assert not [i for i in v._issues if i.category in _COST_CATEGORIES]


def test_both_cost_checks_share_one_scan(tmp_path, monkeypatch):
    _write(tmp_path, "events/Ev.txt", _BLIND_AND_UNNEEDED)
    loads = []
    load = validate_events.load_cost_lookups
    monkeypatch.setattr(
        validate_events,
        "load_cost_lookups",
        lambda validator: loads.append(validator) or load(validator),
    )
    v = _validator(tmp_path, check_ai_chance_costs=True)

    v.validate_ai_chance_ignores_cost()
    v.validate_unneeded_treasury_checks()

    assert len(loads) == 1
    assert [(i.category, i.severity, i.message, i.line) for i in v._issues] == [
        (
            "event-ai-chance-ignores-cost",
            validator_common.Severity.WARNING,
            _PP_BLIND,
            8,
        ),
        (
            "event-unneeded-treasury-guard",
            validator_common.Severity.WARNING,
            "foo.1.b - ai_chance lowers the weight on bankruptcy, but the option has"
            " no money or political power cost",
            12,
        ),
    ]


# case: (files, (message, line) per finding in Ev.txt)
_VALIDATOR_CASES = {
    "flat weight on a costed option": (
        {"events/Ev.txt": _two_options(_PP_COST + _FLAT)},
        [(_PP_BLIND, 8)],
    ),
    "unequal shared literal cost": (
        {
            "events/Ev.txt": _event(
                _option("foo.1.a", _PP_COST + _FLAT),
                _option("foo.1.b", "\t\tadd_political_power = -25\n" + _FLAT),
            ),
        },
        [(_PP_BLIND, 8)],
    ),
    "empty tree": ({}, []),
    "the mod's scripted effects": (
        {
            _BUDGET: _SCRIPTED_EFFECTS,
            "events/Ev.txt": _two_options(
                "\t\tone_office_construction = yes\n" + _FLAT
            ),
        },
        [(_TREASURY_BLIND, 8)],
    ),
    "stored signs from the whole mod": (
        {
            _BUDGET: _SCRIPTED_EFFECTS,
            "common/decisions/TAG.txt": "TAG_decision = {\n"
            "\tcomplete_effect = { set_variable = { TAG_rail_cost = -4 } }\n"
            "}\n",
            "events/Ev.txt": _two_options(
                "\t\tset_temp_variable = { treasury_change = TAG_rail_cost }\n"
                "\t\tmodify_treasury_effect = yes\n" + _FLAT
            ),
        },
        [(_TREASURY_BLIND, 9)],
    ),
    "every option gated": (
        {"events/Ev.txt": _ALL_GATED},
        [
            (
                _PP_BLIND
                + " (every option has a trigger; check the AI sees more than one)",
                9,
            )
        ],
    ),
    "tag-split options": ({"events/Ev.txt": _TAG_SPLIT}, []),
    "commented cost": (
        {"events/Ev.txt": _two_options("\t\t#add_political_power = -50\n" + _FLAT)},
        [],
    ),
}


@pytest.mark.parametrize(
    "files, expected", _VALIDATOR_CASES.values(), ids=_VALIDATOR_CASES
)
def test_validate_ai_chance_ignores_cost(tmp_path, files, expected):
    for rel, body in files.items():
        _write(tmp_path, rel, body)
    v = _validator(tmp_path, check_ai_chance_costs=True)
    v.validate_ai_chance_ignores_cost()

    assert [(i.category, i.message, i.file, i.line) for i in v._issues] == [
        ("event-ai-chance-ignores-cost", message, "events/Ev.txt", line)
        for message, line in expected
    ]
    assert (v.warnings_found, v.errors_found) == (len(expected), 0)


# case: (event, (option, line, cost kinds, every option gated) per finding)
_OPTION_CASES = {
    "modifier on the costed option": (_two_options(_PP_COST + _AWARE), []),
    "modifier on another option": (
        _event(_option("foo.1.a", _PP_COST + _FLAT), _option("foo.1.b", _AWARE)),
        [("foo.1.a", 8, "political power", False)],
    ),
    "single option event": (_event(_option("foo.1.a", _PP_COST + _FLAT)), []),
    "missing ai_chance reports the option line": (
        _two_options(_PP_COST),
        [("foo.1.a", 5, "political power", False)],
    ),
    "every option gated": (_ALL_GATED, [("foo.1.a", 9, "political power", True)]),
    "gated option with an always-visible sibling": (
        _two_options(_GATE + _PP_COST + _FLAT),
        [("foo.1.a", 9, "political power", False)],
    ),
    "reference pattern and its flat sibling": (
        _event(
            _option(
                "foo.1.a",
                "\t\tset_temp_variable = { treasury_change = -15.00 }\n"
                "\t\tmodify_treasury_effect = yes\n" + _AWARE,
            ),
            _option(
                "foo.1.b", "\t\tadd_stability = -0.02\n\t\tai_chance = { base = 1 }\n"
            ),
        ),
        [("foo.1.b", 17, "stability", False)],
    ),
    "decision-only resources do not widen the event check": (
        _two_options(
            "\t\tadd_command_power = -20\n\t\tadd_manpower = -100\n"
            "\t\tadd_equipment_to_stockpile = { type = infantry_equipment amount = -100 }\n"
            + _FLAT
        ),
        [],
    ),
    "base 0 option beside one that can win": (
        _two_options(_PP_COST + "\t\tai_chance = { base = 0 }\n"),
        [],
    ),
    "base 0 option with an add": (
        _two_options(
            _PP_COST
            + "\t\tai_chance = { base = 0 modifier = { add = 5 has_war = yes } }\n"
        ),
        [("foo.1.a", 8, "political power", False)],
    ),
    "every option at base 0": (
        _event(
            _option("foo.1.a", _PP_COST + "\t\tai_chance = { base = 0 }\n"),
            _option("foo.1.b", "\t\tai_chance = { base = 0 }\n"),
        ),
        [("foo.1.a", 8, "political power", False)],
    ),
    "cost every option pays": (
        _event(
            _option("foo.1.a", _PP_COST + _FLAT), _option("foo.1.b", _PP_COST + _FLAT)
        ),
        [],
    ),
    "unconditional scripted costs stay shared": (
        _event(
            _option("foo.1.a", "\t\tlose_pp_for_15_days = yes\n" + _FLAT),
            _option("foo.1.b", "\t\tlose_pp_for_15_days = yes\n" + _FLAT),
        ),
        [],
    ),
    "unconditional variable costs stay shared": (
        _event(
            _option("foo.1.a", "\t\tadd_to_variable = { treasury = -5 }\n" + _FLAT),
            _option("foo.1.b", "\t\tadd_to_variable = { treasury = -5 }\n" + _FLAT),
        ),
        [],
    ),
    "own-country wrappers keep unconditional shared costs": (
        _event(
            _option(
                "foo.1.a", "\t\thidden_effect = { add_political_power = -50 }\n" + _FLAT
            ),
            _option("foo.1.b", "\t\tROOT = { add_political_power = -50 }\n" + _FLAT),
        ),
        [],
    ),
    "always-paid and war-only costs are not shared": (
        _event(
            _option("foo.1.a", _PP_COST + _FLAT),
            _option(
                "foo.1.b",
                "\t\tif = { limit = { has_war = yes } add_political_power = -50 }\n"
                + _FLAT,
            ),
        ),
        [
            ("foo.1.a", 8, "political power", False),
            ("foo.1.b", 13, "political power", False),
        ],
    ),
    "nested conditional cost is not shared": (
        _event(
            _option("foo.1.a", _PP_COST + _FLAT),
            _option(
                "foo.1.b",
                "\t\tif = {\n"
                "\t\t\tlimit = { has_war = yes }\n"
                "\t\t\tif = { limit = { has_country_flag = foo } add_political_power = -50 }\n"
                "\t\t}\n" + _FLAT,
            ),
        ),
        [
            ("foo.1.a", 8, "political power", False),
            ("foo.1.b", 16, "political power", False),
        ],
    ),
    "random conditional cost is not shared": (
        _event(
            _option("foo.1.a", _PP_COST + _FLAT),
            _option(
                "foo.1.b",
                "\t\trandom = { chance = 50 add_political_power = -50 }\n" + _FLAT,
            ),
        ),
        [
            ("foo.1.a", 8, "political power", False),
            ("foo.1.b", 13, "political power", False),
        ],
    ),
    "random-list conditional cost is not shared": (
        _event(
            _option("foo.1.a", _PP_COST + _FLAT),
            _option(
                "foo.1.b",
                "\t\trandom_list = { 50 = { add_political_power = -50 } 50 = { } }\n"
                + _FLAT,
            ),
        ),
        [
            ("foo.1.a", 8, "political power", False),
            ("foo.1.b", 13, "political power", False),
        ],
    ),
    "scripted conditional cost is not shared": (
        _event(
            _option("foo.1.a", _PP_COST + _FLAT),
            _option("foo.1.b", "\t\tTAG_war_only_cost = yes\n" + _FLAT),
        ),
        [
            ("foo.1.a", 8, "political power", False),
            ("foo.1.b", 13, "political power", False),
        ],
    ),
    "scripted charge after conditional variable change is not shared": (
        _event(
            _option(
                "foo.1.a",
                "\t\tset_temp_variable = { debt_change = 5 }\n"
                "\t\tmodify_debt_effect = yes\n" + _FLAT,
            ),
            _option(
                "foo.1.b",
                "\t\tset_temp_variable = { bill = 0 }\n"
                "\t\tif = {\n"
                "\t\t\tlimit = { has_war = yes }\n"
                "\t\t\tset_temp_variable = { bill = 5 }\n"
                "\t\t}\n"
                "\t\tset_temp_variable = { debt_change = bill }\n"
                "\t\tmodify_debt_effect = yes\n" + _FLAT,
            ),
        ),
        [
            ("foo.1.a", 9, "debt", False),
            ("foo.1.b", 20, "debt", False),
        ],
    ),
    "unconditional reset restores a shared charge": (
        _event(
            _option("foo.1.a", "\t\tadd_to_variable = { debt = 5 }\n" + _FLAT),
            _option(
                "foo.1.b",
                "\t\tset_temp_variable = { debt_change = 0 }\n"
                "\t\tif = { limit = { has_war = yes } set_temp_variable = { debt_change = 5 } }\n"
                "\t\tset_temp_variable = { debt_change = 5 }\n"
                "\t\tmodify_debt_effect = yes\n" + _FLAT,
            ),
        ),
        [],
    ),
    "branch-only positive variable assignment stays conditional": (
        _event(
            _option("foo.1.a", "\t\tadd_to_variable = { debt = 5 }\n" + _FLAT),
            _option(
                "foo.1.b",
                "\t\tif = { limit = { has_war = yes } set_temp_variable = { debt_change = 5 } }\n"
                "\t\tmodify_debt_effect = yes\n" + _FLAT,
            ),
        ),
        [("foo.1.a", 8, "debt", False), ("foo.1.b", 14, "debt", False)],
    ),
    "charge-skip guards stay shared": (
        _event(
            _option("foo.1.a", "\t\tsmall_expenditure = yes\n" + _FLAT),
            _option("foo.1.b", "\t\tone_office_construction = yes\n" + _FLAT),
        ),
        [],
    ),
    "if and else that both charge stay shared": (
        _event(
            _option(
                "foo.1.a",
                "\t\tif = { limit = { has_war = yes } add_political_power = -50 }\n"
                "\t\telse = { add_political_power = -25 }\n" + _FLAT,
            ),
            _option("foo.1.b", _PP_COST + _FLAT),
        ),
        [],
    ),
    "if and else_if without else are not shared": (
        _event(
            _option(
                "foo.1.a",
                "\t\tif = { limit = { has_war = yes } add_political_power = -50 }\n"
                "\t\telse_if = { limit = { has_war = no } add_political_power = -25 }\n"
                + _FLAT,
            ),
            _option("foo.1.b", _PP_COST + _FLAT),
        ),
        [
            ("foo.1.a", 9, "political power", False),
            ("foo.1.b", 14, "political power", False),
        ],
    ),
    "random-list buckets that all charge stay shared": (
        _event(
            _option(
                "foo.1.a",
                "\t\trandom_list = { 50 = { add_political_power = -50 } "
                "50 = { add_political_power = -10 } }\n" + _FLAT,
            ),
            _option("foo.1.b", _PP_COST + _FLAT),
        ),
        [],
    ),
    "costs every option pays only sometimes stay shared": (
        _event(
            _option(
                "foo.1.a",
                "\t\tif = { limit = { has_war = yes } add_political_power = -50 }\n"
                + _FLAT,
            ),
            _option(
                "foo.1.b",
                "\t\trandom = { chance = 50 add_political_power = -50 }\n" + _FLAT,
            ),
        ),
        [],
    ),
    "only the shared kind is skipped": (
        _event(
            _option("foo.1.a", _PP_COST + "\t\tadd_stability = -0.02\n" + _FLAT),
            _option("foo.1.b", _PP_COST + _FLAT),
        ),
        [("foo.1.a", 9, "stability", False)],
    ),
    "player-only event": (
        _two_options(_PP_COST + _FLAT).replace(
            "\tis_triggered_only = yes\n",
            "\tis_triggered_only = yes\n\ttrigger = { is_ai = no }\n",
        ),
        [],
    ),
    "is_ai = no inside OR still reports": (
        _two_options(_PP_COST + _FLAT).replace(
            "\tis_triggered_only = yes\n",
            "\tis_triggered_only = yes\n\ttrigger = { OR = { is_ai = no has_war = yes } }\n",
        ),
        [("foo.1.a", 9, "political power", False)],
    ),
    "tax rate moved by every option": (
        _event(
            _option(
                "foo.1.a",
                "\t\tset_temp_variable = { corp_change = -2 }\n"
                "\t\tmodify_corporate_tax_rate_effect = yes\n" + _FLAT,
            ),
            _option(
                "foo.1.b",
                "\t\tset_temp_variable = { corp_change = 3 }\n"
                "\t\tmodify_corporate_tax_rate_effect = yes\n" + _FLAT,
            ),
        ),
        [("foo.1.a", 9, "tax rate", False), ("foo.1.b", 15, "tax rate", False)],
    ),
}


@pytest.mark.parametrize("text, expected", _OPTION_CASES.values(), ids=_OPTION_CASES)
def test_find_cost_blind_options(text, expected):
    assert _found(text) == expected


# case: (option triggers, at most one option per receiver)
_RECEIVER_CASES = {
    "distinct tags": (("tag = ISR", "tag = HEZ"), True),
    "distinct original tags": (("original_tag = ISR", "original_tag = HEZ"), True),
    "same tag": (("tag = ISR", "tag = ISR"), False),
    "different identity fields can overlap": (
        ("tag = D01", "original_tag = ISR"),
        False,
    ),
    "conjunctive receiver wrappers": (
        (
            "AND = { has_war = no hidden_trigger = { ROOT = { tag = ISR } } }",
            "THIS = { tag = HEZ }",
        ),
        True,
    ),
    "tag inside OR": (("OR = { tag = ISR has_war = yes }", "tag = HEZ"), False),
    "tag in another country": (("FROM = { tag = ISR }", "tag = HEZ"), False),
    "tag complement": (("tag = ISR", "NOT = { tag = ISR }"), True),
    "original tag complement reversed": (
        ("NOT = { original_tag = ISR }", "original_tag = ISR"),
        True,
    ),
    "exclusion of a different tag": (("NOT = { tag = ISR }", "tag = HEZ"), False),
    "two exclusions overlap": (("NOT = { tag = ISR }", "NOT = { tag = HEZ }"), False),
    "negated conjunction does not exclude its tag": (
        ("tag = ISR", "NOT = { AND = { tag = ISR has_war = yes } }"),
        False,
    ),
    "untagged sibling": (("tag = ISR", "has_war = yes"), False),
    "third option overlaps the second": (
        ("tag = ISR", "tag = HEZ", "tag = HEZ"),
        False,
    ),
    "both identity fields constrain the receiver": (
        ("tag = D01 original_tag = ISR", "tag = D01 original_tag = HEZ"),
        True,
    ),
    "commented tag is not a pin": (("# tag = ISR\nhas_war = yes", "tag = HEZ"), False),
    "country alias is not a literal tag": (("tag = FROM", "tag = HEZ"), False),
}


# case: (option bodies, (option suffix, uncovered cost kinds) per finding)
_SHARED_PRICE_CASES = {
    "dearer political power option": (
        ("add_political_power = -50", "add_political_power = -25"),
        [("a", "political power")],
    ),
    "dearer choice has its guard": (
        ("add_political_power = -50\n" + _AWARE, "add_political_power = -25"),
        [],
    ),
    "only the cheaper choice has a guard": (
        ("add_political_power = -50", "add_political_power = -25\n" + _AWARE),
        [("a", "political power")],
    ),
    "every tier above the cheapest": (
        (
            "add_political_power = -50",
            "add_political_power = -25",
            "add_political_power = -100",
        ),
        [("a", "political power"), ("c", "political power")],
    ),
    "stability fractions sum exactly": (
        ("add_stability = -0.1 add_stability = -0.2", "add_stability = -0.3"),
        [],
    ),
    "dearer war support choice": (
        ("add_war_support = -0.01", "add_war_support = -0.02"),
        [("b", "war support")],
    ),
    "treasury charges add across short and long forms": (
        (
            "add_to_variable = { var = treasury value = -3 } "
            "subtract_from_variable = { treasury = 4 }",
            "add_to_variable = { treasury = -5 }",
        ),
        [("a", "treasury")],
    ),
    "debt increases are costs": (
        ("add_to_variable = { debt = 5 }", "add_to_variable = { debt = 2 }"),
        [("a", "debt")],
    ),
    "investment losses are costs": (
        (
            "add_to_variable = { int_investments = -5 }",
            "add_to_variable = { int_investments = -8 }",
        ),
        [("b", "international investment")],
    ),
    "different cheapest choices per kind": (
        (
            "add_political_power = -50 add_stability = -0.01",
            "add_political_power = -25 add_stability = -0.02",
        ),
        [("a", "political power"), ("b", "stability")],
    ),
    "mixed gains and charges are not a fixed price": (
        (
            "add_political_power = -50 add_political_power = 25",
            "add_political_power = -30",
        ),
        [],
    ),
    "zero stat effect does not hide an unequal price": (
        (
            "add_political_power = -50 add_political_power = 0",
            "add_political_power = -25",
        ),
        [("a", "political power")],
    ),
    "money refund remains unmeasured": (
        (
            "add_to_variable = { treasury = -5 } add_to_variable = { treasury = 3 }",
            "add_to_variable = { treasury = -3 }",
        ),
        [],
    ),
    "unrelated stored variable does not change the price": (
        (
            "set_variable = { foo = 3 } add_political_power = -50",
            "add_political_power = -25",
        ),
        [("a", "political power")],
    ),
    "balance reset is not a known price": (
        (
            "add_to_variable = { treasury = -5 } set_variable = { treasury = 100 }",
            "add_to_variable = { treasury = -2 }",
        ),
        [],
    ),
    "balance clamp is not a known price": (
        (
            "add_to_variable = { treasury = -5 } clamp_variable = { var = treasury min = 0 }",
            "add_to_variable = { treasury = -2 }",
        ),
        [],
    ),
    "variable-priced money remains unmeasured": (
        (
            "add_to_variable = { treasury = TAG_project_cost }",
            "add_to_variable = { treasury = -2 }",
        ),
        [],
    ),
    "same-country wrappers keep prices": (
        (
            "hidden_effect = { ROOT = { THIS = { add_political_power = -50 } } }",
            "add_political_power = -25",
        ),
        [("a", "political power")],
    ),
    "foreign charges do not change the price": (
        (
            "add_political_power = -25 FROM = { add_political_power = -200 }",
            "add_political_power = -50",
        ),
        [("b", "political power")],
    ),
    "preview is not a charge": (
        (
            "add_political_power = -25 effect_tooltip = { add_political_power = -200 }",
            "add_political_power = -50",
        ),
        [("b", "political power")],
    ),
    "conditional add-on is not a known price": (
        (
            "add_political_power = -25 if = { limit = { has_war = yes } add_political_power = -100 }",
            "add_political_power = -50",
        ),
        [],
    ),
    "scripted price stays unmeasured": (
        ("lose_pp_for_15_days = yes", "add_political_power = -50"),
        [],
    ),
    "a scripted reward can change the price": (
        (
            "add_political_power = -50 increase_economic_growth = yes",
            "add_political_power = -25",
        ),
        [],
    ),
    "wrapped scripted price stays unmeasured": (
        ("hidden_effect = { lose_pp_for_15_days = yes }", "add_political_power = -50"),
        [],
    ),
    "stored price stays unmeasured": (
        ("add_political_power = TAG_project_cost", "add_political_power = -50"),
        [],
    ),
    "tag-split prices do not imply a choice": (
        (
            "trigger = { tag = ISR } add_political_power = -50",
            "trigger = { tag = HEZ } add_political_power = -25",
        ),
        [],
    ),
    "even one gated option needs receiver analysis": (
        (
            "trigger = { has_country_flag = foo } add_political_power = -50",
            "add_political_power = -25",
        ),
        [],
    ),
    "only one AI choice remains": (
        (
            "add_political_power = -25 ai_chance = { base = 0 }",
            "add_political_power = -50",
        ),
        [],
    ),
    "disabled cheap option is not the baseline": (
        (
            "add_political_power = -25 ai_chance = { base = 0 }",
            "add_political_power = -50",
            "add_political_power = -100",
        ),
        [("c", "political power")],
    ),
    "an add can make a base-zero option eligible": (
        (
            "add_political_power = -25 ai_chance = { base = 0 modifier = { add = 1 has_war = yes } }",
            "add_political_power = -50",
        ),
        [("b", "political power")],
    ),
}


@pytest.mark.parametrize(
    "triggers, split", _RECEIVER_CASES.values(), ids=_RECEIVER_CASES
)
def test_tag_split_options_need_no_cost_weights(triggers, split):
    text = _event(
        *(
            _option(
                f"foo.1.{letter}",
                f"\t\ttrigger = {{ {trigger} }}\n"
                + (_PP_COST + _FLAT if letter == "a" else _AWARE),
            )
            for letter, trigger in zip("abc", triggers)
        )
    )
    blind, unneeded = find_option_cost_weights(text, _EFFECTS, _STORED, _COMMITMENTS)
    assert (bool(blind), bool(unneeded)) == (not split, not split)


@pytest.mark.parametrize(
    "bodies, expected", _SHARED_PRICE_CASES.values(), ids=_SHARED_PRICE_CASES
)
def test_shared_literal_prices(bodies, expected):
    text = _event(
        *(_option(f"foo.1.{letter}", body) for letter, body in zip("abc", bodies))
    )
    assert [(name, costs) for name, _line, costs, _gated in _found(text)] == [
        (f"foo.1.{letter}", costs) for letter, costs in expected
    ]


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
            "\t\tif = { limit = { has_war = yes } set_temp_variable = { bill = 0 } }\n"
            "\t\tsubtract_from_temp_variable = { bill = 5 }\n"
            "\t\tadd_to_variable = { treasury = bill }\n",
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
        (
            "\t\tset_temp_variable = { var = bill value = { value = 2 multiply = { value = gdp_total divide = -500 } } }\n"
            "\t\tadd_to_variable = { treasury = bill }\n",
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
        "\t\tset_temp_variable = { bill = { value = 2 multiply = { value = gdp_total multiply = -0.002 } multiply = -1 } }\n"
        "\t\tadd_to_variable = { treasury = bill }\n",
        "\t\tif = { limit = { always = no } add_political_power = -50 }\n",
        "\t\trandom = { chance = 0 add_political_power = -50 }\n",
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
        "TAG_war_only_cost",
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


def _weighted(condition, weight="factor = 0.25"):
    return f"\t\tai_chance = {{ base = 5 modifier = {{ {weight} {condition} }} }}\n"


@pytest.mark.parametrize(
    "condition,weight",
    [
        ("has_opinion = { target = IND value > 50 }", "add = 20"),
        ("is_historical_focus_on = yes", "factor = 10"),
        ("has_war_with = IND", "factor = 0"),
        ("has_stability < 0.3", "factor = 0.25"),
        ("", "factor = 0.25"),
        ("has_active_mission = bankruptcy_incoming_collapse", "factor = 1"),
        ("has_active_mission = bankruptcy_incoming_collapse", "add = 0"),
        ("has_active_mission = bankruptcy_incoming_collapse", "factor = score"),
        ("FROM = { has_active_mission = bankruptcy_incoming_collapse }", "factor = 0"),
        ("IND = { has_active_mission = bankruptcy_incoming_collapse }", "factor = 0"),
        (
            "has_active_mission = bankruptcy_incoming_collapse "
            "check_variable = { factor = 0.25 }",
            "factor = 1",
        ),
    ],
)
def test_unrelated_neutral_or_foreign_modifiers_do_not_cover_costs(condition, weight):
    found = _found(_two_options(_PP_COST + _weighted(condition, weight)))
    assert [(name, costs) for name, _line, costs, _gated in found] == [
        ("foo.1.a", "political power")
    ]


@pytest.mark.parametrize(
    "condition,flagged",
    [
        ("has_war = yes", True),
        ("has_active_mission = bankruptcy_incoming_collapse", False),
        ("ai_has_high_deficit = yes", False),
        ("check_variable = { treasury < 15 }", False),
        (
            "check_variable = { var = ROOT.treasury value = 15 compare = less_than }",
            False,
        ),
        ("ROOT = { ai_has_high_deficit = yes }", False),
        ("THIS = { ai_has_high_deficit = yes }", False),
        ("OR = { ai_has_high_deficit = yes has_war = yes }", False),
        ("NOT = { ai_has_high_deficit = yes }", False),
    ],
)
def test_financial_modifiers_cover_treasury_costs(condition, flagged):
    body = "\t\tsmall_expenditure = yes\n" + _weighted(condition)
    found = [costs for _name, _line, costs, _gated in _found(_two_options(body))]
    assert found == (["treasury"] if flagged else [])


@pytest.mark.parametrize(
    "cost,condition",
    [
        ("add_to_variable = { debt = 5 }", "ai_has_high_deficit = yes"),
        (
            "subtract_from_variable = { int_investments = 5 }",
            "ai_has_high_deficit = yes",
        ),
        (
            "subtract_from_variable = { population_tax_rate = 5 }",
            "check_variable = { population_tax_rate > 40 }",
        ),
        ("add_stability = -0.02", "has_stability < 0.3"),
        ("add_war_support = -0.02", "has_war_support < 0.3"),
    ],
)
def test_each_cost_kind_accepts_its_relevant_modifier(cost, condition):
    assert _found(_two_options(f"\t\t{cost}\n" + _weighted(condition))) == []


_BANKRUPT = "has_active_mission = bankruptcy_incoming_collapse"
_DEFICIT = "ai_has_high_deficit = yes"
_NO_COST = "but the option has no money or political power cost"

# case: (event, (option, line, reason) per unneeded treasury check)
_UNNEEDED_CASES = {
    "bankruptcy check on a free option": (
        _two_options(_weighted(_BANKRUPT)),
        [("foo.1.a", 7, f"lowers the weight on bankruptcy, {_NO_COST}")],
    ),
    "bankruptcy check on a political power cost": (
        _two_options(_PP_COST + _weighted(_BANKRUPT)),
        [],
    ),
    "deficit check on a political power cost": (
        _two_options(_PP_COST + _weighted(_DEFICIT)),
        [
            (
                "foo.1.a",
                8,
                "lowers the weight on high deficit, but the option has no money cost",
            )
        ],
    ),
    "deficit check on a debt cost": (
        _two_options("\t\tadd_to_variable = { debt = 5 }\n" + _weighted(_DEFICIT)),
        [],
    ),
    "both checks on a free option": (
        _two_options(
            f"\t\tai_chance = {{ base = 5 modifier = {{ factor = 0.25 {_BANKRUPT} }}"
            f" modifier = {{ factor = 0.5 {_DEFICIT} }} }}\n"
        ),
        [
            (
                "foo.1.a",
                7,
                f"lowers the weight on bankruptcy and high deficit, {_NO_COST}",
            )
        ],
    ),
    "negative add": (
        _two_options(_weighted(_BANKRUPT, "add = -2")),
        [("foo.1.a", 7, f"lowers the weight on bankruptcy, {_NO_COST}")],
    ),
    "raising add": (_two_options(_weighted(_BANKRUPT, "add = 10")), []),
    "factor above 1": (_two_options(_weighted(_BANKRUPT, "factor = 2")), []),
    "variable factor": (_two_options(_weighted(_BANKRUPT, "factor = score")), []),
    "inside NOT": (_two_options(_weighted(f"NOT = {{ {_BANKRUPT} }}")), []),
    "the sender's bankruptcy": (
        _two_options(_weighted(f"FROM = {{ {_BANKRUPT} }}")),
        [],
    ),
    "scripted treasury cost": (
        _two_options("\t\tsmall_expenditure = yes\n" + _weighted(_BANKRUPT)),
        [],
    ),
    "charge back to ROOT from a state scope": (
        _two_options(
            "\t\trandom_owned_state = { ROOT = { small_expenditure = yes } }\n"
            + _weighted(_BANKRUPT)
        ),
        [],
    ),
    "a war": (
        _two_options("\t\tdeclare_war_on = { target = GER }\n" + _weighted(_DEFICIT)),
        [],
    ),
    "a spending law change behind a caller": (
        _two_options("\t\tTAG_reform = yes\n" + _weighted(_DEFICIT)),
        [],
    ),
    "an option the AI never picks": (
        _two_options(
            f"\t\tai_chance = {{ base = 0 modifier = {{ factor = 0.25 {_BANKRUPT} }} }}\n"
        ),
        [],
    ),
}


@pytest.mark.parametrize(
    "text, expected", _UNNEEDED_CASES.values(), ids=_UNNEEDED_CASES
)
def test_unneeded_treasury_checks(text, expected):
    assert (
        find_option_cost_weights(text, _EFFECTS, _STORED, _COMMITMENTS)[1] == expected
    )


def test_mixed_costs_report_only_the_uncovered_kind():
    body = "\t\tsmall_expenditure = yes\n\t\tadd_stability = -0.02\n" + _AWARE
    found = _found(_two_options(body))
    assert [(name, costs) for name, _line, costs, _gated in found] == [
        ("foo.1.a", "stability")
    ]
    covered = body.replace(
        "base = 10", "base = 10 modifier = { factor = 0.25 has_stability < 0.3 }"
    )
    assert _found(_two_options(covered)) == []


@pytest.mark.parametrize(
    "scope, trigger",
    [
        ("ROOT", "tag = AST"),
        ("THIS", "tag = AST"),
        ("AST", "tag = AST"),
        ("AST", "tag = AST has_war = no"),
        ("AST", "AND = { tag = AST has_war = no }"),
        ("AST", "ROOT = { tag = AST }"),
        ("AST", "THIS = { tag = AST }"),
        ("AST", "tag = AST AND = { has_war = no }"),
    ],
)
def test_choosing_country_cost_scopes_are_checked(scope, trigger):
    text = _two_options(f"\t\t{scope} = {{ add_political_power = -50 }}\n" + _FLAT)
    text = text.replace("id = foo.1", f"id = foo.1\n\ttrigger = {{ {trigger} }}")
    assert [found[0] for found in _found(text)] == ["foo.1.a"]
    assert _found(text.replace(_FLAT, _AWARE)) == []


def test_literal_receiver_scope_can_cover_its_own_cost():
    body = "\t\tAST = { small_expenditure = yes }\n" + _weighted(
        "AST = { ai_has_high_deficit = yes }"
    )
    text = _two_options(body).replace(
        "id = foo.1", "id = foo.1\n\ttrigger = { tag = AST }"
    )
    assert _found(text) == []


@pytest.mark.parametrize(
    "trigger",
    [
        "NOT = { tag = AST }",
        "OR = { tag = AST tag = IND }",
        "original_tag = AST",
        "FROM = { tag = AST }",
        "tag = AST tag = IND",
    ],
)
def test_nonexclusive_tag_checks_do_not_make_foreign_costs_local(trigger):
    body = "\t\tAST = { add_political_power = -50 }\n" + _FLAT
    text = _two_options(body).replace(
        "id = foo.1", f"id = foo.1\n\ttrigger = {{ {trigger} }}"
    )
    assert _found(text) == []


@pytest.mark.parametrize(
    "preview",
    ["add_political_power = -50", "small_expenditure = yes", "add_stability = -0.1"],
)
def test_effect_tooltip_is_not_an_executed_cost(preview):
    assert _found(_two_options(f"\t\teffect_tooltip = {{ {preview} }}\n" + _FLAT)) == []


def test_preview_only_scripted_effect_is_not_costly():
    effects = costly_scripted_effects(
        ["preview = { effect_tooltip = { add_political_power = -50 } }\n"]
    )
    assert effects == {}


@pytest.mark.parametrize("actual,preview,expected", [(5, -5, []), (-5, 5, ["foo.1.a"])])
def test_preview_temp_writes_do_not_change_the_executed_cost(actual, preview, expected):
    body = (
        f"\t\tset_temp_variable = {{ treasury_change = {actual} }}\n"
        f"\t\teffect_tooltip = {{ set_temp_variable = {{ treasury_change = {preview} }} "
        "modify_treasury_effect = yes }\n"
        "\t\tmodify_treasury_effect = yes\n" + _FLAT
    )
    assert [found[0] for found in _found(_two_options(body))] == expected
