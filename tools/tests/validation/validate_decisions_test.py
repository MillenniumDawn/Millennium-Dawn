"""Tests for validate_decisions.py.

Checks that read parsed decisions share one table of decision texts. Checks that
scan the tree build a small mod first.
"""

import argparse
import os
import re
import sys
from collections.abc import Mapping, Sequence

import pytest
import validate_decisions as V
from shared.suite import (
    assert_findings,
    build_validator,
    checks_called_by_run,
    dds_stub,
    decision_factory,
    decisions_results_for,
    issue_rows,
    write_tree,
)
from shared_utils import run_validator_main
from sprite_index import SpriteSizeIndex
from validate_events import costly_scripted_effects

_OPT_IN_CHECKS = {
    "validate_missing_icons",
    "validate_unannounced_categories",
    "validate_naming_style",
}


def _flat(*parts, token="dec_one"):
    """A decision at column zero."""
    return token + " = {\n" + "".join(parts) + "}"


def _effect(body, block="complete_effect"):
    return "\t" + block + " = {\n" + body + "\t}\n"


def _nested(token, body=""):
    """A decision one tab in, the way a category holds it."""
    return f"\t{token} = {{\n{body}\t}}\n"


def _block(name, content):
    body = "".join(f"\t\t\t{line}\n" for line in content.split("\n"))
    return f"\t\t{name} = {{\n{body}\t\t}}\n"


def _mod(tmp_path, files, **kwargs):
    write_tree(tmp_path, files)
    return build_validator(V.Validator, tmp_path, **kwargs)


# ---- checks on parsed decisions ---------------------------------------------

_LOG = '\t\tlog = "[GetDateText]: [Root.GetName]: Decision dec_one"\n'
_GAIN = "\t\tadd_political_power = 10\n"
_SPEND = "\t\tadd_political_power = -75\n"
_SPEND_50 = "\t\tadd_political_power = -50\n"
_NO_LOG = "dec_one - X.txt: %s has no log line"
_EFFECT_BLOCKS = ("complete_effect", "remove_effect", "timeout_effect", "cancel_effect")
_RANDOM = "\t\trandom = {\n\t\t\tchance = 50\n\t\t\tadd_stability = 0.01\n\t\t}\n"
_RANDOM_LIST = (
    "\t\trandom_list = {\n\t\t\t50 = { add_stability = 0.01 }\n"
    "\t\t\t50 = { add_stability = -0.01 }\n\t\t}\n"
)

_BILL = "pay_the_bill = {\n\tadd_to_variable = { treasury = -3 }\n}\n"
_BUILD = (
    "build_a_factory = {\n\trandom_owned_state = {\n"
    "\t\tadd_building_construction = { type = arms_factory level = 1 }\n\t}\n"
    "\tadd_to_variable = { treasury = -3 }\n}\n"
)
_CUSTOM_BILLS = (
    "pay_command_power = { add_command_power = -20 }\n"
    "forward_command_power = { pay_command_power = yes }\n"
    "pay_manpower = { set_temp_variable = { troops = -100 } add_manpower = troops }\n"
    "pay_equipment = { add_equipment_to_stockpile = { type = infantry_equipment amount = -100 } }\n"
    "preview_command_power = { effect_tooltip = { add_command_power = -20 } }\n"
    "foreign_command_power = { FROM = { add_command_power = -20 } }\n"
)
_PAYMENT = (
    "modify_treasury_effect = { add_to_variable = { treasury = treasury_change } }\n"
)
_EFFECTS = costly_scripted_effects([_BILL, _BUILD, _CUSTOM_BILLS, _PAYMENT])
_CHARGE = "\t\tadd_to_variable = { treasury = -5 }\n"
_WEIGHT = "\tai_will_do = { base = 10 }\n"
_BANKRUPTCY_WEIGHT = (
    "\tai_will_do = {\n\t\tbase = 10\n\t\tmodifier = { factor = 0 "
    "has_active_mission = bankruptcy_incoming_collapse }\n\t}\n"
)
_DEFICIT_WEIGHT = (
    "\tai_will_do = {\n\t\tbase = 10\n\t\tmodifier = { factor = 0.5 "
    "ai_has_high_deficit = yes }\n\t}\n"
)
_UNNEEDED_BANKRUPTCY = [
    (
        "dec_one - ai_will_do lowers the weight on bankruptcy, but the decision has"
        " no money or political power cost",
        "X.txt",
        0,
    )
]
_ZERO_BASE_ADD = (
    "\tai_will_do = {\n\t\tbase = 0\n\t\tmodifier = { add = 5 has_war = yes }\n\t}\n"
)
_MISSION = "\tdays_mission_timeout = 90\n"
_SELECTABLE = _MISSION + "\tselectable_mission = yes\n"
_TREASURY_GATE = "\tcustom_cost_trigger = { check_variable = { treasury > 5 } }\n"
_PAID = _effect(_CHARGE)
_PAID_ON_REMOVE = _effect(_CHARGE, "remove_effect")
# Scripted triggers by name: the body is what a decision's gate or read resolves to.
_TRIGGERS = {
    "treasury_higher_than_50": " custom_trigger_tooltip = { tooltip = tip"
    " check_variable = { treasury > 49 } } ",
    "calculate_fee": " set_temp_variable = { fee = 5 } ",
}
_TOOLTIPPED_GATE = (
    "\tavailable = { custom_trigger_tooltip = { tooltip = tip"
    " check_variable = { treasury > 1 } } }\n"
)
_APPLY = "\t\tmodify_treasury_effect = yes\n"


def _take(*amounts):
    """A complete_effect that charges each literal treasury amount."""
    return _effect(
        "".join(
            f"\t\tset_temp_variable = {{ treasury_change = -{amount} }}\n{_APPLY}"
            for amount in amounts
        )
    )


def _floor(amount, block="custom_cost_trigger"):
    return f"\t{block} = {{ check_variable = {{ treasury > {amount} }} }}\n"


_LATE = [
    (
        "dec_one - remove_effect charges treasury, charge it in complete_effect",
        "X.txt",
        0,
    )
]


def _below(gate, charge):
    message = f"dec_one - treasury gate {gate} is below the {charge} it charges"
    return [(message + " in complete_effect", "X.txt", 0)]


def _temp_read(block):
    message = f"dec_one - {block} reads pay, a temp variable only the effects set"
    return (message + ", so it is always 0 here", "X.txt", 0)


def _reads(block, name="pay"):
    return f"\t{block} = {{ check_variable = {{ treasury > {name} }} }}\n"


def _sets(name="pay", block="complete_effect", op="set_temp_variable"):
    return _effect(f"\t\t{op} = {{ {name} = 5 }}\n", block)


_UNLOCK_MISSED = (
    "md_setter - X.txt: complete_effect announces 1 unlock(s) but not md_missed"
)
_AI_ONLY = "\tvisible = {\n\t\tis_ai = yes\n\t}\n"
_AI_ONLY_AVAILABLE = "\tavailable = {\n\t\tis_ai = yes\n\t}\n"


def _ignores(what):
    return [(f"dec_one - ai_will_do ignores the {what}", "X.txt", 0)]


def _unpaid(kind: str) -> list[object]:
    return [
        (
            f"dec_one - custom cost checks {kind} but has no charge in complete_effect",
            "X.txt",
            0,
        )
    ]


def _setter(*unlocks, flag="set_country_flag = md_gate_flag"):
    announced = "".join(f"\t\tunlock_decision_tooltip = {name}\n" for name in unlocks)
    return _flat(_effect(f"\t\t{flag}\n{announced}"), token="md_setter")


def _gated(token, block="visible", check="has_country_flag = md_gate_flag"):
    return _flat(f"\t{block} = {{\n\t\t{check}\n\t}}\n", token=token)


_ANNOUNCED = [_setter("md_announced"), _gated("md_announced")]

# check: {case: (decisions, what each finding must match)}
_CHECK_CASES: Mapping[str, Mapping[str, tuple[Sequence[str], Sequence[object]]]] = {
    "validate_missing_log": {
        "logged": ([_flat(_effect(_LOG))], []),
        "unquoted log": (
            [_flat(_effect("\t\tlog = some_unquoted_thing\n"))],
            [_NO_LOG % "complete_effect"],
        ),
        "every effect block needs one": (
            [_flat(*(_effect(_GAIN, block) for block in _EFFECT_BLOCKS))],
            [_NO_LOG % block for block in _EFFECT_BLOCKS],
        ),
        "a log covers only its own block": (
            [_flat(_effect(_LOG + _GAIN), _effect(_GAIN, "remove_effect"))],
            [_NO_LOG % "remove_effect"],
        ),
    },
    "validate_log_not_first": {
        "log first": ([_flat(_effect(_LOG + _GAIN, "remove_effect"))], []),
        "log after an effect": (
            [_flat(_effect(_GAIN + _LOG, "timeout_effect"))],
            [("timeout_effect", "add_political_power")],
        ),
        # A log inside a branch records which branch ran, so it is not late.
        "nested log": (
            [
                _flat(
                    _effect(
                        "\t\tcustom_effect_tooltip = some_tt\n"
                        "\t\thidden_effect = {\n\t" + _LOG + "\t\t}\n"
                    )
                )
            ],
            [],
        ),
        "comment before the log": (
            [_flat(_effect("\t\t#the treasury hit is deliberate\n" + _LOG + _GAIN))],
            [],
        ),
        "quoted brace before the log": (
            [
                _flat(
                    _effect(
                        '\t\tcustom_effect_tooltip = "a { brace } in a string"\n' + _LOG
                    )
                )
            ],
            [("custom_effect_tooltip",)],
        ),
        "two logs at the block's level": (
            [_flat(_effect(_LOG + _LOG))],
            [("complete_effect has 2 log lines",)],
        ),
        "a nested second log": (
            [
                _flat(
                    _effect(
                        _LOG + "\t\tif = {\n\t\t\tlimit = { has_war = yes }\n"
                        "\t" + _LOG + "\t\t}\n"
                    )
                )
            ],
            [],
        ),
    },
    "validate_money_charged_after_entry": {
        "charged on removal": ([_flat(_PAID_ON_REMOVE)], _LATE),
        "exempt id": (
            [
                _flat(
                    _PAID_ON_REMOVE,
                    token=sorted(V._LATE_CHARGE_EXEMPT - V._AI_COST_EXEMPT)[0],
                )
            ],
            [],
        ),
        "payment effect on removal": (
            [
                _flat(
                    _effect(
                        "\t\tset_temp_variable = { treasury_change = -5 }\n" + _APPLY,
                        "remove_effect",
                    )
                )
            ],
            _LATE,
        ),
        "scripted effect that charges": (
            [_flat(_effect("\t\tpay_the_bill = yes\n", "remove_effect"))],
            _LATE,
        ),
        # A construction effect pays when the building is delivered; that is intended.
        "building effect that charges": (
            [_flat(_effect("\t\tbuild_a_factory = yes\n", "remove_effect"))],
            [],
        ),
        "charged when taken": ([_flat(_PAID)], []),
        "payout on removal": (
            [
                _flat(
                    _effect("\t\tadd_to_variable = { treasury = 5 }\n", "remove_effect")
                )
            ],
            [],
        ),
        "political power on removal": (
            [_flat(_effect(_SPEND_50, "remove_effect"))],
            [],
        ),
        "charged on cancellation": ([_flat(_effect(_CHARGE, "cancel_effect"))], []),
        "selectable mission": ([_flat(_SELECTABLE, _PAID_ON_REMOVE)], []),
        "plain mission": ([_flat(_MISSION, _PAID_ON_REMOVE)], []),
        # validate_custom_cost_charged already reports this one as late.
        "late custom cost": ([_flat(_TREASURY_GATE, _PAID_ON_REMOVE)], []),
        "paid up front and again on removal": (
            [_flat(_TREASURY_GATE, _PAID, _PAID_ON_REMOVE)],
            _LATE,
        ),
    },
    "validate_treasury_gate_below_charge": {
        "gate below the charge": ([_flat(_floor(1.75), _take(2))], _below(1.75, 2)),
        "gate at the charge": ([_flat(_floor(2), _take(2))], []),
        "gate with >=": (
            [
                _flat(
                    "\tcustom_cost_trigger = { check_variable = { treasury >= 1 } }\n",
                    _take(2),
                )
            ],
            _below(1, 2),
        ),
        # `> 0.4` for a 0.5 charge is how the mod writes `>= 0.5`.
        "gate 0.1 under the charge": ([_flat(_floor(0.4), _take(0.5))], []),
        "gate 0.11 under the charge": (
            [_flat(_floor(0.39), _take(0.5))],
            _below(0.39, 0.5),
        ),
        # The scripted trigger's name says 50, its body 49.
        "scripted gate read from its body": (
            [_flat("\tavailable = { treasury_higher_than_50 = yes }\n", _take(50))],
            _below(49, 50),
        ),
        "tooltip wrapper": ([_flat(_TOOLTIPPED_GATE, _take(2))], _below(1, 2)),
        "highest gate counts": (
            [_flat(_floor(1, "available"), _floor(5), _take(5))],
            [],
        ),
        "gate inside an OR": (
            [
                _flat(
                    "\tavailable = { OR = { check_variable = { treasury > 1 }"
                    " has_war = yes } }\n",
                    _take(2),
                )
            ],
            [],
        ),
        "no treasury gate": ([_flat(_take(2))], []),
        "charges add up": ([_flat(_floor(3), _take(2, 2))], _below(3, 4)),
        "charge inside an if": (
            [
                _flat(
                    _floor(1),
                    _effect(
                        "\t\tif = {\n\t\t\tlimit = { has_war = yes }\n"
                        "\t\t\tset_temp_variable = { treasury_change = -2 }\n"
                        "\t\t\tmodify_treasury_effect = yes\n\t\t}\n"
                    ),
                )
            ],
            [],
        ),
        "charge rewritten before it is applied": (
            [
                _flat(
                    _floor(1),
                    _effect(
                        "\t\tset_temp_variable = { treasury_change = -2 }\n"
                        "\t\tmultiply_temp_variable = { treasury_change = -3 }\n"
                        + _APPLY
                    ),
                )
            ],
            [],
        ),
        "computed charge": (
            [
                _flat(
                    _floor(1),
                    _effect(
                        "\t\tset_temp_variable = { treasury_change = { value = gdp_total"
                        " multiply = -0.03 } }\n" + _APPLY
                    ),
                )
            ],
            [],
        ),
        "plain mission": ([_flat(_MISSION, _floor(1), _take(2))], []),
    },
    "validate_trigger_reads_temp_variable": {
        "custom cost reads it": (
            [_flat(_reads("custom_cost_trigger"), _sets())],
            [_temp_read("custom_cost_trigger")],
        ),
        "available and visible read it": (
            [_flat(_reads("available"), _reads("visible"), _sets())],
            [_temp_read("available"), _temp_read("visible")],
        ),
        "set in remove_effect": (
            [_flat(_reads("available"), _sets(block="remove_effect"))],
            [_temp_read("available")],
        ),
        "reads a stored variable": (
            [_flat(_reads("available", "stored"), _sets())],
            [],
        ),
        "also set persistently": (
            [
                _flat(
                    _reads("available"),
                    _sets(),
                    _sets(block="remove_effect", op="set_variable"),
                )
            ],
            [],
        ),
        "trigger sets it": (
            [
                _flat(
                    "\tavailable = { set_temp_variable = { pay = 5 }"
                    " check_variable = { treasury > pay } }\n",
                    _sets(),
                )
            ],
            [],
        ),
        "scripted trigger sets it": (
            [
                _flat(
                    "\tavailable = { calculate_fee = yes"
                    " check_variable = { treasury > fee } }\n",
                    _sets("fee"),
                )
            ],
            [],
        ),
        "plain mission": ([_flat(_MISSION, _reads("available"), _sets())], []),
    },
    "validate_custom_cost_ai_hint": {
        "custom_cost_trigger": (
            [
                _flat(
                    "\tcustom_cost_trigger = {\n\t\thas_political_power > 74\n\t}\n"
                    "\tcustom_cost_text = some_key\n"
                )
            ],
            [("dec_one", "custom_cost_trigger")],
        ),
        "complete_effect": (
            [_flat(_effect(_SPEND))],
            [("dec_one", "complete_effect spends 75 PP")],
        ),
        "remove_effect": (
            [_flat("\tdays_remove = 365\n", _effect(_SPEND_50, "remove_effect"))],
            [("remove_effect spends 50 PP",)],
        ),
        "hint present": ([_flat("\tai_hint_pp_cost = 75\n", _effect(_SPEND))], []),
        # A conditional charge is an outcome, not a price the AI budgets for.
        "conditional charge": (
            [
                _flat(
                    _effect(
                        "\t\tif = {\n\t\t\tlimit = { has_war = yes }\n"
                        "\t\t\tadd_political_power = -75\n\t\t}\n"
                    )
                )
            ],
            [],
        ),
        "AI never takes it": (
            [_flat("\tai_will_do = { base = 0 }\n", _effect(_SPEND))],
            [],
        ),
        "mission timeout": (
            [_flat("\tdays_mission_timeout = 365\n", _effect(_SPEND, "remove_effect"))],
            [],
        ),
        "both blocks charge": (
            [_flat(_effect(_SPEND), _effect(_SPEND_50, "remove_effect"))],
            [("complete_effect spends 75 PP",)],
        ),
    },
    "validate_random_seed": {
        "random_list": ([_flat(_effect(_RANDOM_LIST))], [("dec_one",)]),
        # A roll inside effect_tooltip renders but never runs.
        "random_list in effect_tooltip": (
            [_flat(_effect("\t\teffect_tooltip = {\n" + _RANDOM_LIST + "\t\t}\n"))],
            [],
        ),
        "random in remove_effect": (
            [_flat(_effect(_RANDOM, "remove_effect"))],
            [("dec_one",)],
        ),
        "seed set to no": (
            [_flat("\tfixed_random_seed = no\n", _effect(_RANDOM, "remove_effect"))],
            [],
        ),
        "seed set to yes": (
            [_flat("\tfixed_random_seed = yes\n", _effect(_RANDOM_LIST))],
            [],
        ),
        "fire_only_once": ([_flat("\tfire_only_once = yes\n", _effect(_RANDOM))], []),
        "fire_only_once = no": (
            [_flat("\tfire_only_once = no\n", _effect(_RANDOM))],
            [("dec_one",)],
        ),
        # random_owned_state and random_country change scope, they do not roll.
        "random scopes": (
            [
                _flat(
                    _effect(
                        "\t\trandom_owned_state = { add_extra_state_shared_building_slots = 1 }\n"
                        "\t\trandom_country = { add_opinion_modifier = { target = ROOT modifier = x } }\n"
                    )
                )
            ],
            [],
        ),
    },
    # Issue #5738.
    "validate_ai_will_do_ignores_cost": {
        "flat weight": ([_flat(_PAID, _WEIGHT)], _ignores("treasury cost")),
        "exempt id": (
            [
                _flat(
                    _PAID,
                    _WEIGHT,
                    token=sorted(V._AI_COST_EXEMPT - V._LATE_CHARGE_EXEMPT)[0],
                )
            ],
            [],
        ),
        "scripted effect": (
            [_flat(_effect("\t\tpay_the_bill = yes\n"), _WEIGHT)],
            _ignores("treasury cost"),
        ),
        "remove_effect": (
            [_flat("\tdays_remove = 30\n", _PAID_ON_REMOVE)],
            _ignores("treasury cost"),
        ),
        "two kinds listed once": (
            [
                _flat(
                    _PAID,
                    _effect("\t\tadd_to_variable = { debt = 4 }\n", "remove_effect"),
                    _WEIGHT,
                )
            ],
            _ignores("debt, treasury cost"),
        ),
        "treasury cost gate": (
            [_flat(_TREASURY_GATE, _PAID, _WEIGHT)],
            _ignores("treasury cost (behind a treasury custom_cost_trigger; verify)"),
        ),
        "zero base with an add": (
            [_flat(_PAID, _ZERO_BASE_ADD)],
            _ignores("treasury cost"),
        ),
        # `base = 0` must not match `base = 0.5`.
        "fractional base": (
            [_flat(_PAID, "\tai_will_do = { base = 0.5 }\n")],
            _ignores("treasury cost"),
        ),
        "selectable mission": (
            [_flat(_SELECTABLE, _PAID, _WEIGHT)],
            _ignores("treasury cost"),
        ),
        "bankruptcy modifier": ([_flat(_PAID, _BANKRUPTCY_WEIGHT)], []),
        "income": (
            [_flat(_effect("\t\tadd_to_variable = { treasury = 5 }\n"), _WEIGHT)],
            [],
        ),
        "political power only": ([_flat(_effect(_SPEND_50), _WEIGHT)], []),
        "AI never takes it": ([_flat(_PAID, "\tai_will_do = { base = 0 }\n")], []),
        "player only": ([_flat(_PAID, _WEIGHT, "\tavailable = { is_ai = no }\n")], []),
        "never visible": (
            [_flat(_PAID, _WEIGHT, "\tvisible = { always = no }\n")],
            [],
        ),
        "plain mission": ([_flat(_MISSION, _PAID)], []),
        # An is_ai = no under a tag scope is about that country, not the caller.
        "is_ai = no for another country": (
            [
                _flat(
                    _PAID,
                    _WEIGHT,
                    "\tvisible = {\n\t\tAFG = {\n\t\t\tif = {\n"
                    "\t\t\t\tlimit = { is_ai = no }\n\t\t\t\tinfluence_higher_15 = yes\n"
                    "\t\t\t}\n\t\t}\n\t}\n",
                )
            ],
            _ignores("treasury cost"),
        ),
        "gate in a custom_override_tooltip": (
            [
                _flat(
                    _PAID,
                    _WEIGHT,
                    "\tavailable = { custom_override_tooltip = { tooltip = tip"
                    " always = no } }\n",
                )
            ],
            [],
        ),
        "gate in a hidden_trigger": (
            [
                _flat(
                    _PAID,
                    _WEIGHT,
                    "\tavailable = { hidden_trigger = { always = no } }\n",
                )
            ],
            [],
        ),
    },
    "validate_unneeded_treasury_guard": {
        "free decision": (
            [_flat(_effect(_GAIN), _BANKRUPTCY_WEIGHT)],
            _UNNEEDED_BANKRUPTCY,
        ),
        "treasury charge": ([_flat(_PAID, _BANKRUPTCY_WEIGHT)], []),
        "scripted charge": (
            [_flat(_effect("\t\tpay_the_bill = yes\n"), _BANKRUPTCY_WEIGHT)],
            [],
        ),
        "charge back to ROOT from a state scope": (
            [
                _flat(
                    _effect(
                        "\t\trandom_owned_state = { ROOT = { pay_the_bill = yes } }\n"
                    ),
                    _BANKRUPTCY_WEIGHT,
                )
            ],
            [],
        ),
        "bankruptcy check on a political power price": (
            [_flat("\tcost = 25\n", _effect(_GAIN), _BANKRUPTCY_WEIGHT)],
            [],
        ),
        "deficit check on a political power price": (
            [_flat("\tcost = 25\n", _effect(_GAIN), _DEFICIT_WEIGHT)],
            [
                (
                    "dec_one - ai_will_do lowers the weight on high deficit, but the"
                    " decision has no money cost",
                    "X.txt",
                    0,
                )
            ],
        ),
        "money modifier while active": (
            [
                _flat(
                    "\tdays_remove = 30\n",
                    "\tmodifier = { social_cost_multiplier_modifier = 0.1 }\n",
                    _effect(_GAIN),
                    _DEFICIT_WEIGHT,
                )
            ],
            [],
        ),
        "treasury custom cost": (
            [_flat(_TREASURY_GATE, _effect(_GAIN), _DEFICIT_WEIGHT)],
            [],
        ),
        "remove_effect charge": (
            [_flat("\tdays_remove = 30\n", _PAID_ON_REMOVE, _BANKRUPTCY_WEIGHT)],
            [],
        ),
        "selectable mission's timeout charge": (
            [_flat(_SELECTABLE, _PAID_ON_REMOVE, _BANKRUPTCY_WEIGHT)],
            [],
        ),
        "plain mission": ([_flat(_MISSION, _BANKRUPTCY_WEIGHT)], []),
        "AI never takes it": (
            [
                _flat(
                    "\tai_will_do = {\n\t\tbase = 0\n\t\tmodifier = { factor = 0"
                    " has_active_mission = bankruptcy_incoming_collapse }\n\t}\n"
                )
            ],
            [],
        ),
        "player only": (
            [_flat(_BANKRUPTCY_WEIGHT, "\tavailable = { is_ai = no }\n")],
            [],
        ),
    },
    "validate_custom_cost_charged": {
        "charged when taken": ([_flat(_TREASURY_GATE, _PAID)], []),
        "scripted charge": (
            [_flat(_TREASURY_GATE, _effect("\t\tpay_the_bill = yes\n"))],
            [],
        ),
        "charged on removal": (
            [_flat(_TREASURY_GATE, _PAID_ON_REMOVE)],
            [
                (
                    "dec_one - custom cost charges treasury in remove_effect, not"
                    " complete_effect",
                    "X.txt",
                    0,
                )
            ],
        ),
        "never charged": (
            [
                _flat(
                    "\tcustom_cost_trigger = {\n\t\tcommand_power > 49\n"
                    "\t\thas_political_power > 74\n\t}\n",
                    _effect(_SPEND),
                )
            ],
            [
                (
                    "dec_one - custom cost checks command power but has no charge in complete_effect",
                    "X.txt",
                    0,
                )
            ],
        ),
        "equipment handed over": (
            [
                _flat(
                    "\tcustom_cost_trigger = { has_equipment = { infantry_equipment > 99 } }\n",
                    _effect(
                        "\t\tadd_equipment_to_stockpile = { type = infantry_equipment"
                        " amount = -100 }\n"
                    ),
                )
            ],
            [],
        ),
        "ROOT payment inside a hidden effect": (
            [
                _flat(
                    "\tcustom_cost_trigger = { command_power > 19 }\n",
                    _effect(
                        "\t\thidden_effect = { ROOT = { add_command_power = -20 } }\n"
                    ),
                )
            ],
            [],
        ),
        "enabled branch": (
            [
                _flat(
                    "\tcustom_cost_trigger = { command_power > 19 }\n",
                    _effect(
                        "\t\tif = { limit = { always = yes } add_command_power = -20 }\n"
                    ),
                )
            ],
            [],
        ),
        "negated false limit allows payment": (
            [
                _flat(
                    "\tcustom_cost_trigger = { command_power > 19 }\n",
                    _effect(
                        "\t\tif = { limit = { NOT = { always = no } } add_command_power = -20 }\n"
                    ),
                )
            ],
            [],
        ),
        "no custom cost": ([_flat(_PAID)], []),
        "human-only decision still needs payment": (
            [_flat(_TREASURY_GATE, "\tai_will_do = { base = 0 }\n")],
            _unpaid("treasury"),
        ),
        "scripted command power": (
            [
                _flat(
                    "\tcustom_cost_trigger = { command_power > 19 }\n",
                    _effect("\t\tforward_command_power = yes\n"),
                )
            ],
            [],
        ),
        "scripted manpower": (
            [
                _flat(
                    "\tcustom_cost_trigger = { has_manpower > 99 }\n",
                    _effect("\t\tpay_manpower = yes\n"),
                )
            ],
            [],
        ),
        "scripted equipment": (
            [
                _flat(
                    "\tcustom_cost_trigger = { has_equipment = { infantry_equipment > 99 } }\n",
                    _effect("\t\tpay_equipment = yes\n"),
                )
            ],
            [],
        ),
        "nested math charge": (
            [
                _flat(
                    _TREASURY_GATE,
                    _effect(
                        "\t\tset_temp_variable = { bill = { value = times_taken multiply = { value = gdp_total multiply = -0.002 } } }\n"
                        "\t\tadd_to_variable = { treasury = bill }\n"
                    ),
                )
            ],
            [],
        ),
        "nested math income": (
            [
                _flat(
                    _TREASURY_GATE,
                    _effect(
                        "\t\tset_temp_variable = { var = bill value = { value = times_taken multiply = { value = gdp_total multiply = 0.002 } } }\n"
                        "\t\tadd_to_variable = { treasury = bill }\n"
                    ),
                )
            ],
            _unpaid("treasury"),
        ),
        "scripted charge on removal": (
            [
                _flat(
                    "\tcustom_cost_trigger = { command_power > 19 }\n",
                    _effect("\t\tpay_command_power = yes\n", "remove_effect"),
                )
            ],
            [
                (
                    "dec_one - custom cost charges command power in remove_effect, not complete_effect",
                    "X.txt",
                    0,
                )
            ],
        ),
        "payment only on timeout or cancellation": (
            [
                _flat(
                    _SELECTABLE,
                    _TREASURY_GATE,
                    _effect(_CHARGE, "timeout_effect"),
                    _effect(_CHARGE, "cancel_effect"),
                )
            ],
            _unpaid("treasury"),
        ),
        "selectable mission must pay when taken": (
            [_flat(_SELECTABLE, _TREASURY_GATE, _PAID_ON_REMOVE)],
            [
                (
                    "dec_one - custom cost charges treasury in remove_effect, not complete_effect",
                    "X.txt",
                    0,
                )
            ],
        ),
        **{
            f"not an executed owner charge: {name}": (
                [
                    _flat(
                        "\tcustom_cost_trigger = { command_power > 19 }\n",
                        _effect(f"\t\t{body}\n"),
                    )
                ],
                _unpaid("command power"),
            )
            for name, body in {
                "preview": "effect_tooltip = { add_command_power = -20 }",
                "foreign scope": "FROM = { add_command_power = -20 }",
                "quoted log": 'log = "add_command_power = -20"',
                "scripted preview": "preview_command_power = yes",
                "scripted foreign scope": "foreign_command_power = yes",
                "disabled branch": "if = { limit = { always = no } add_command_power = -20 }",
                "zero chance": "random = { chance = 0 add_command_power = -20 }",
                "income": "add_command_power = 20",
                "zero": "add_command_power = -0",
            }.items()
        },
        "equipment transfer": (
            [
                _flat(
                    "\tcustom_cost_trigger = { has_equipment = { infantry_equipment > 99 } }\n",
                    _effect(
                        "\t\tsend_equipment = { type = infantry_equipment amount = 100 target = UKR }\n"
                    ),
                )
            ],
            [],
        ),
        "plain mission": ([_flat(_MISSION, _TREASURY_GATE)], []),
    },
    # Only the inconsistent case is a defect: a block that announces one unlock
    # and misses a sibling gated on the flag it just set.
    "validate_unannounced_decision_unlocks": {
        "missed sibling": ([*_ANNOUNCED, _gated("md_missed")], [_UNLOCK_MISSED]),
        "every unlock announced": (
            [_setter("md_one", "md_two"), _gated("md_one"), _gated("md_two")],
            [],
        ),
        "quoted tooltip text": (
            [
                _setter(
                    flag='log = "[GetDateText]: unlock_decision_tooltip = md_announced"'
                    "\n\t\tset_country_flag = md_gate_flag"
                ),
                _gated("md_announced"),
                _gated("md_missed"),
            ],
            [],
        ),
        "available gate": (
            [*_ANNOUNCED, _gated("md_missed", block="available")],
            [_UNLOCK_MISSED],
        ),
        "timed flag": (
            [
                _setter(
                    "md_announced",
                    flag="set_country_flag = { flag = md_gate_flag days = 30 }",
                ),
                _gated("md_announced"),
                _gated("md_missed"),
            ],
            [_UNLOCK_MISSED],
        ),
        "AI-only sibling": ([*_ANNOUNCED, _gated("md_ai")], []),
        "setter gated on its own flag": (
            [
                _flat(
                    "\tvisible = {\n\t\thas_country_flag = md_gate_flag\n\t}\n",
                    _effect(
                        "\t\tset_country_flag = md_gate_flag\n"
                        "\t\tunlock_decision_tooltip = md_announced\n"
                    ),
                    token="md_setter",
                ),
                _gated("md_announced"),
            ],
            [],
        ),
    },
    "validate_targeted_without_target": {
        "disabled and map-click decisions are skipped": (
            [
                _nested(
                    "disabled",
                    _block("target_root_trigger", "always = yes")
                    + _block("allowed", "always = no"),
                ),
                _nested(
                    "map_click",
                    _block("target_trigger", "always = yes")
                    + "\t\tstate_target = yes\n",
                ),
                _nested("daily_scan", _block("target_root_trigger", "always = yes")),
            ],
            [("daily_scan",)],
        ),
    },
    "validate_targets_no_trigger": {
        "FROM filter in available": (
            [
                _nested(
                    "avail_from",
                    "\t\ttargets = { GER }\n"
                    + _block("available", "FROM = { has_war = yes }"),
                ),
                _nested("no_from", "\t\ttargets = { GER }\n"),
            ],
            [("avail_from",)],
        ),
    },
    "validate_from_without_targets": {
        "every block is read": (
            [
                _nested(
                    "disabled",
                    _block("allowed", "always = no")
                    + _block("visible", "FROM = { has_war = yes }"),
                ),
                _nested(
                    "map_click",
                    "\t\tstate_target = yes\n"
                    + _block("visible", "FROM = { has_war = yes }"),
                ),
                _nested("avail_from", _block("available", "FROM = { has_war = yes }")),
                _nested(
                    "effect_from",
                    _block("complete_effect", "FROM = { add_stability = 0.1 }"),
                ),
            ],
            [
                ("avail_from", "FROM used in available"),
                ("effect_from", "FROM used in complete_effect"),
            ],
        ),
    },
    "validate_redundant_tag_checks": {
        "both pin forms and the available block": (
            [
                _nested(
                    "multi_pin",
                    _block("allowed", "original_tag = GER\noriginal_tag = FRA"),
                ),
                _nested(
                    "both_pins", _block("allowed", "tag = GER\noriginal_tag = GER")
                ),
                _nested("runtime_pin", _block("allowed", "tag = GER")),
                _nested(
                    "avail_recheck",
                    _block("allowed", "original_tag = GER")
                    + _block("available", "tag = GER"),
                ),
                _nested(
                    "avail_scope",
                    _block("allowed", "original_tag = GER")
                    + _block("available", "GER = { has_war = no }"),
                ),
            ],
            [
                ("both_pins", "allowed has both 'tag' and 'original_tag'"),
                ("runtime_pin", "allowed uses 'tag'"),
                ("avail_recheck", "available re-checks tag"),
                ("avail_scope", "available self-scopes"),
            ],
        ),
    },
    "validate_pp_charge_in_effect": {
        "scripted cost counts as zero": (
            [
                _nested(
                    "scripted_cost",
                    "\t\tcost = var:GER_reform_cost\n"
                    + _block("complete_effect", "add_political_power = -50"),
                )
            ],
            [("scripted_cost",)],
        ),
    },
    "validate_state_target_with_targets": {
        "state_target = yes is accepted": (
            [
                _nested("ok", "\t\tstate_target = yes\n\t\ttargets = { GER }\n"),
                _nested(
                    "broken",
                    "\t\tstate_target = current_state\n\t\ttargets = { GER }\n",
                ),
            ],
            [("broken",)],
        ),
    },
}


@pytest.mark.parametrize(
    ("check", "decisions", "expected"),
    [
        pytest.param(check, *case, id=f"{check}: {name}")
        for check, cases in _CHECK_CASES.items()
        for name, case in cases.items()
    ],
)
def test_decision_check(monkeypatch, check, decisions, expected):
    monkeypatch.setattr(V, "load_cost_lookups", lambda validator: (_EFFECTS, {}, set()))
    monkeypatch.setattr(V.Validator, "_get_ai_only_by_category", lambda self: {"md_ai"})
    monkeypatch.setattr(V.Validator, "_get_scripted_triggers", lambda self: _TRIGGERS)
    monkeypatch.setattr(
        V.Validator, "_get_building_payments", lambda self: {"build_a_factory"}
    )
    factories = [decision_factory(text) for text in decisions]

    assert_findings(decisions_results_for(factories, monkeypatch, check), expected)


def test_cost_check_reads_the_mods_scripted_effects(tmp_path):
    validator = _mod(
        tmp_path,
        {
            "common/scripted_effects/00_bills.txt": _BILL,
            "common/decisions/Bills.txt": "bills_category = {\n"
            + _nested("dec_bill", _block("complete_effect", "pay_the_bill = yes"))
            + "}\n",
        },
    )

    validator.validate_ai_will_do_ignores_cost()

    assert {i.severity for i in validator._issues} == {V.Severity.ERROR}
    assert issue_rows(validator) == [
        (
            "decision-ai-will-do-ignores-cost",
            "dec_bill - ai_will_do ignores the treasury cost",
            "common/decisions/Bills.txt",
            2,
        )
    ]


def test_unneeded_treasury_guard_shares_the_cost_pass(tmp_path, monkeypatch):
    walks = []
    walk = V.ai_weight_cost_checks
    monkeypatch.setattr(
        V,
        "ai_weight_cost_checks",
        lambda weights: walks.append(weights) or walk(weights),
    )
    validator = _mod(
        tmp_path,
        {
            "common/decisions/Free.txt": "free_category = {\n"
            + _nested(
                "dec_free",
                _block("complete_effect", "add_political_power = 10")
                + _block(
                    "ai_will_do",
                    "base = 10\nmodifier = { factor = 0.5 ai_has_high_deficit = yes }",
                ),
            )
            + "}\n",
        },
    )

    validator.validate_ai_will_do_ignores_cost()
    validator.validate_unneeded_treasury_guard()

    assert len(walks) == 1
    assert {i.severity for i in validator._issues} == {V.Severity.WARNING}
    assert issue_rows(validator) == [
        (
            "decision-unneeded-treasury-guard",
            "dec_free - ai_will_do lowers the weight on high deficit, but the"
            " decision has no money cost",
            "common/decisions/Free.txt",
            2,
        )
    ]


def test_late_charge_check_follows_scripted_effects_but_not_buildings(tmp_path):
    waived = (
        "pay_unless_waived = {\n\tif = {\n"
        "\t\tlimit = { NOT = { check_variable = { skip_payment = 1 } } }\n"
        "\t\tadd_to_variable = { treasury = -3 }\n\t}\n}\n"
    )
    calls = ("pay_the_bill", "build_a_factory", "pay_unless_waived")
    validator = _mod(
        tmp_path,
        {
            "common/scripted_effects/00_bills.txt": _BILL + _BUILD + waived,
            "common/decisions/Bills.txt": "bills_category = {\n"
            + "".join(
                _nested(f"dec_{call}", _block("remove_effect", f"{call} = yes"))
                for call in calls
            )
            + "}\n",
        },
    )

    validator.validate_money_charged_after_entry()

    assert [(i.severity, i.category, i.message) for i in validator._issues] == [
        (
            V.Severity.ERROR,
            "decision-money-charged-late",
            "dec_pay_the_bill - remove_effect charges treasury,"
            " charge it in complete_effect",
        )
    ]


def test_custom_cost_check_loads_scripted_charges_and_keeps_warnings(tmp_path):
    validator = _mod(
        tmp_path,
        {
            "common/scripted_effects/00_bills.txt": _CUSTOM_BILLS,
            "common/decisions/Bills.txt": "bills_category = {\n"
            + _nested(
                "paid",
                "\t\tcustom_cost_trigger = { command_power > 19 }\n"
                + _block("complete_effect", "forward_command_power = yes"),
            )
            + _nested("unpaid", "\t\tcustom_cost_trigger = { command_power > 19 }\n")
            + "}\n",
        },
    )

    validator.validate_custom_cost_charged()

    assert issue_rows(validator) == [
        (
            "decision-custom-cost-not-charged",
            "unpaid - custom cost checks command power but has no charge in complete_effect",
            "common/decisions/Bills.txt",
            8,
        )
    ]
    assert (validator.warnings_found, validator.errors_found) == (1, 0)


_GATE_TRIGGERS = (
    "treasury_higher_than_2 = {\n\tcustom_trigger_tooltip = {\n\t\ttooltip = tip\n"
    "\t\tcheck_variable = { treasury > 2 }\n\t}\n}\n"
    "calculate_pay = {\n\tset_temp_variable = { pay = 5 }\n}\n"
)


def test_gate_and_temp_variable_checks_read_the_mods_scripted_triggers(tmp_path):
    validator = _mod(
        tmp_path,
        {
            "common/scripted_triggers/00_gates.txt": _GATE_TRIGGERS,
            "common/decisions/Gates.txt": "gates_category = {\n"
            + _nested(
                "low_gate",
                _block("available", "treasury_higher_than_2 = yes")
                + _block(
                    "complete_effect",
                    "set_temp_variable = { treasury_change = -3 }\n"
                    "modify_treasury_effect = yes",
                ),
            )
            + _nested(
                "fee_read",
                _block("available", "check_variable = { treasury > fee }")
                + _block("complete_effect", "set_temp_variable = { fee = 5 }"),
            )
            + _nested(
                "pay_read",
                _block(
                    "available",
                    "calculate_pay = yes\ncheck_variable = { treasury > pay }",
                )
                + _block("complete_effect", "set_temp_variable = { pay = 5 }"),
            )
            + "}\n",
        },
    )

    validator.validate_treasury_gate_below_charge()
    validator.validate_trigger_reads_temp_variable()

    assert [row[:3] for row in issue_rows(validator)] == [
        (
            "decision-treasury-gate-below-charge",
            "low_gate - treasury gate 2 is below the 3 it charges in complete_effect",
            "common/decisions/Gates.txt",
        ),
        (
            "decision-trigger-reads-temp-variable",
            "fee_read - available reads fee, a temp variable only the effects set,"
            " so it is always 0 here",
            "common/decisions/Gates.txt",
        ),
    ]
    assert (validator.warnings_found, validator.errors_found) == (2, 0)


# A category's own gate blocks hide its decisions from the AI; a tag scope does not.
_AI_CATEGORY_CASES = {
    "flat is_ai = no": ("\tvisible = {\n\t\tis_ai = no\n\t}\n", False),
    "flat always = no": ("\tallowed = {\n\t\talways = no\n\t}\n", False),
    "inside a hidden_trigger": (
        "\tavailable = {\n\t\thidden_trigger = { is_ai = no }\n\t}\n",
        False,
    ),
    "under a tag scope": ("\tvisible = {\n\t\tAFG = { is_ai = no }\n\t}\n", True),
    "no gate": ("", True),
}


@pytest.mark.parametrize(
    ("gate", "reachable"),
    list(_AI_CATEGORY_CASES.values()),
    ids=list(_AI_CATEGORY_CASES),
)
def test_category_gate_hides_its_decisions_from_the_ai(tmp_path, gate, reachable):
    validator = _mod(
        tmp_path,
        {
            "common/decisions/categories/cat.txt": f"cat = {{\n{gate}}}\n",
            "common/decisions/d.txt": "cat = {\n" + _nested("in_cat") + "}\n",
        },
    )

    validator.validate_ai_factors()

    flagged = any("in_cat" in row[1] for row in issue_rows(validator))
    assert flagged is reachable


_SLOT = "cyber_op_slot_[SLOT]_[TYPE]"
_PROJECT = "investments_project_[INDEX]_target_decision"

# `activate_mission = cyber_op_slot_[SLOT]_[TYPE]` reaches the scan with its
# placeholders intact, so the check matches on the text around each `[...]`.
# case: (defined decisions, activated decisions, activated missions, reported)
_UNUSED_CASES = {
    "placeholder covers its tokens": (
        ["cyber_op_slot_0_gps_tracking", "cyber_op_slot_9_infra_tracking"],
        set(),
        {_SLOT},
        [],
    ),
    "slot and type outside the domain": (
        ["cyber_op_slot_10_gps_tracking", "cyber_op_slot_0_typo_tracking"],
        set(),
        {_SLOT},
        ["cyber_op_slot_0_typo_tracking", "cyber_op_slot_10_gps_tracking"],
    ),
    "index outside the domain": (
        ["investments_project_15_target_decision"],
        {_PROJECT},
        set(),
        ["investments_project_15_target_decision"],
    ),
    "unknown template": (
        ["custom_slot_0_mission"],
        set(),
        {"custom_slot_[SLOT]_mission"},
        ["custom_slot_0_mission"],
    ),
    "never activated": (
        ["get_md_light_infantry"],
        {"get_blackwater_light_infantry"},
        {"get_wagner_light_infantry"},
        ["get_md_light_infantry"],
    ),
}


@pytest.mark.parametrize(
    ("tokens", "decisions", "missions", "unused"),
    _UNUSED_CASES.values(),
    ids=_UNUSED_CASES,
)
def test_unused_decisions(monkeypatch, tokens, decisions, missions, unused):
    monkeypatch.setattr(
        V.Validator,
        "_get_activation_removal_scan",
        lambda self: (decisions, missions, set(), set(), set()),
    )
    factories = [
        decision_factory(_flat("\tallowed = { always = no }\n", token=token))
        for token in tokens
    ]

    results = decisions_results_for(factories, monkeypatch, "validate_unused_decisions")

    assert results == unused


# An AI-only decision is hidden from every player: it needs no localisation and
# must not carry any. The same holds for an AI-only category.
# case: (decisions, loc keys, patched validator state, findings)
_AI_ONLY_LOC_CASES = {
    "AI-only decision without loc": ([_flat(_AI_ONLY)], set(), {}, []),
    "AI-only through available": ([_flat(_AI_ONLY_AVAILABLE)], set(), {}, []),
    "AI-only decision with loc": (
        [_flat(_AI_ONLY)],
        {"dec_one", "dec_one_desc"},
        {},
        [
            ("AI-only decision has localisation key 'dec_one'",),
            ("AI-only decision has localisation key 'dec_one_desc'",),
        ],
    ),
    "keep-listed AI-only decision": (
        [_flat(_AI_ONLY, token="monetary_policy_austerity")],
        {"monetary_policy_austerity"},
        {},
        [],
    ),
    "ordinary decision without loc": (
        [_flat("\tcost = 25\n")],
        set(),
        {},
        [("missing loc key 'dec_one'",)],
    ),
    "description is optional": ([_flat("\tcost = 25\n")], {"dec_one"}, {}, []),
    "AI-only category without loc": ([], set(), {"categories": {"md_cat"}}, []),
    "AI-only category with loc": (
        [],
        {"md_cat", "md_cat_desc"},
        {"categories": {"md_cat"}},
        [
            ("AI-only decision category has localisation key 'md_cat'",),
            ("AI-only decision category has localisation key 'md_cat_desc'",),
        ],
    ),
    # unlock_decision_category_tooltip shows the name key to a player.
    "unlocked AI-only category": (
        [],
        {"md_cat"},
        {"categories": {"md_cat"}, "unlocked": {"md_cat"}},
        [],
    ),
}


@pytest.mark.parametrize(
    ("decisions", "loc_keys", "state", "expected"),
    _AI_ONLY_LOC_CASES.values(),
    ids=_AI_ONLY_LOC_CASES,
)
def test_ai_only_localisation(monkeypatch, decisions, loc_keys, state, expected):
    unlocks = [("category", name, "cat.txt", 1) for name in state.get("unlocked", ())]
    patched = {
        "_load_localisation_keys": loc_keys,
        "_get_ai_only_by_category": set(),
        "_get_ai_only_categories": dict.fromkeys(state.get("categories", ()), "c.txt"),
        "_get_activation_removal_scan": (set(), set(), set(), unlocks, set()),
    }
    for name, value in patched.items():
        monkeypatch.setattr(V.Validator, name, lambda self, value=value: value)
    monkeypatch.setattr(V, "_load_scripted_localisation_keys", lambda mod_path: set())
    factories = [decision_factory(text) for text in decisions]

    results = decisions_results_for(
        factories, monkeypatch, "validate_missing_localisation"
    )

    assert_findings(results, expected)


def test_factory_is_ai_only_on_a_flat_gate():
    nested = "\tvisible = {\n\t\tOR = {\n\t\t\tis_ai = yes\n\t\t\tis_debug = yes\n\t\t}\n\t}\n"

    assert decision_factory(_flat(_AI_ONLY)).ai_only
    assert decision_factory(_flat(_AI_ONLY_AVAILABLE)).ai_only
    assert not decision_factory(_flat(nested)).ai_only


_GER = ("original_tag", "GER")
_RECHECK = {"dec1": _block("available", "original_tag = GER")}

# A category locked to one tag makes the same check on its decisions redundant.
# case: ({decision: body}, category pins, findings)
_CATEGORY_RECHECK_CASES = {
    "original_tag lock, original_tag recheck": (
        _RECHECK,
        {_GER},
        [("dec1", "available")],
    ),
    # An original_tag lock admits civil-war split-offs, so `tag` still narrows.
    "original_tag lock, tag check": (
        {"dec1": _block("available", "tag = GER")},
        {_GER},
        [],
    ),
    "tag lock, either recheck": (
        {
            "dec_tag": _block("available", "tag = GER"),
            "dec_origtag": _block("visible", "original_tag = GER"),
        },
        {("tag", "GER")},
        [("dec_tag",), ("dec_origtag",)],
    ),
    "NOT-wrapped recheck": (
        {"dec1": _block("available", "NOT = {\n\toriginal_tag = GER\n}")},
        {_GER},
        [],
    ),
    "two-tag lock": (_RECHECK, {_GER, ("original_tag", "ITA")}, []),
    "no tag lock": (_RECHECK, set(), []),
    # validate_allowed_redundant_with_category owns this one.
    "allowed holding only the pin": (
        {"dec1": _block("allowed", "original_tag = GER")},
        {_GER},
        [],
    ),
}


@pytest.mark.parametrize(
    ("decisions", "pins", "expected"),
    _CATEGORY_RECHECK_CASES.values(),
    ids=_CATEGORY_RECHECK_CASES,
)
def test_category_lock_makes_a_decision_recheck_redundant(decisions, pins, expected):
    factories = [
        decision_factory(_nested(token, body)) for token, body in decisions.items()
    ]

    rows = V._find_category_redundant_rows(
        factories, {"cat": pins}, {"cat": list(decisions)}
    )

    assert_findings(rows, expected)


# ---- formable commitment ratchet --------------------------------------------


def _gate(fid, size):
    return (
        "\t\tai_will_do = {\n"
        "\t\t\tbase = 10\n"
        "\t\t\tmodifier = {\n"
        "\t\t\t\tfactor = 0\n"
        f"\t\t\t\tNOT = {{ check_variable = {{ formable_committed_id = {fid} }} }}\n"
        "\t\t\t\tcheck_variable = {\n"
        "\t\t\t\t\tvar = formable_committed_size\n"
        f"\t\t\t\t\tvalue = {size}\n"
        "\t\t\t\t\tcompare = greater_than_or_equals\n"
        "\t\t\t\t}\n"
        "\t\t\t}\n"
        "\t\t}\n"
    )


def _commit(fid, size):
    return (
        "\t\tcomplete_effect = {\n"
        "\t\t\thidden_effect = {\n"
        f"\t\t\t\tset_variable = {{ formable_committed_id = {fid} }}\n"
        f"\t\t\t\tset_variable = {{ formable_committed_size = {size} }}\n"
        "\t\t\t}\n"
        "\t\t}\n"
    )


def _start(tag, fid, size):
    return _nested(f"{tag}_integrate_start", _gate(fid, size) + _commit(fid, size))


def _update_flag(tag, fid, size, state_count, write=True):
    states = "\n".join(
        f"{100 + n} = {{ is_core_of = ROOT }}" for n in range(state_count)
    )
    commit = _gate(fid, size) + _commit(fid, size) if write else ""
    return _nested(f"{tag}_update_flag", commit + _block("available", states))


def _set_pair(fid, size):
    return (
        f"\t\tset_variable = {{ formable_committed_id = {fid} }}\n"
        f"\t\tset_variable = {{ formable_committed_size = {size} }}\n"
    )


_AAA = _update_flag("AAA", 1, 3, 3)
_FOCUS_COMMIT = "focus = {\n\thidden_effect = {\n%s\t}\n}\n"
_GUARDED_FOCUS_COMMIT = (
    "\t\tif = {\n\t\t\tlimit = {\n\t\t\t\tcheck_variable = {\n"
    "\t\t\t\t\tvar = formable_committed_size\n\t\t\t\t\tvalue = 3\n"
    "\t\t\t\t\tcompare = less_than\n\t\t\t\t}\n\t\t\t}\n" + _set_pair(1, 3) + "\t\t}\n"
)

# case: (formable decisions, {other file: text}, what the rows must mention)
_FORMABLE_CASES = {
    "consistent": ([_start("AAA", 1, 3), _AAA], {}, []),
    "id collision": (
        [_AAA, _update_flag("BBB", 1, 5, 5)],
        {},
        ["BBB: commit id 1 collides with AAA"],
    ),
    "gate id mismatch": (
        [_AAA, _nested("AAA_integrate_BBB", _gate(2, 3))],
        {},
        ["gate id 2 != AAA commit id 1"],
    ),
    "guarded focus commit": (
        [_start("AAA", 1, 3), _AAA],
        {"05_spain.txt": _FOCUS_COMMIT % _GUARDED_FOCUS_COMMIT},
        [],
    ),
    "special call in the formables file": (
        [
            _AAA,
            _nested(
                "AAA_integrate_BBB",
                _gate(1, 3) + "\t\tset_temp_variable = { special_formable_id = 101 }\n"
                "\t\tcommit_special_formable = yes\n",
            ),
        ],
        {},
        ["decision formables commit by id/size, not commit_special_formable"],
    ),
    "commit id in the special range": (
        [_start("AAA", 101, 3), _update_flag("AAA", 101, 3, 3)],
        {},
        ["AAA: commit id 101 is in the reserved special range"],
    ),
    "no commit write": (
        [_update_flag("GER", 1, 2, 2, write=False)],
        {},
        ["GER: no commit write", "missing commitment gate"],
    ),
    "conflicting ids and stray references": (
        [
            _nested(
                "ZZZ_integrate_start",
                "\t\tvar = formable_committed_size value = 8\n"
                + _set_pair(1, 9)
                + _set_pair(2, 9)
                + "\t\tNOT = { check_variable = { formable_committed_id = 9 } }\n",
            ),
            _update_flag("ZZZ", 1, 2, 2, write=False),
            _AAA,
            _nested("CCC_integrate_start"),
            _nested("ordinary"),
        ],
        {
            "focus.txt": _set_pair(99, 2)
            + _set_pair(1, 2)
            + "var = formable_committed_size value = 8"
        },
        [
            "ZZZ: conflicting commit ids [1, 2]",
            "size literal 9 != ZZZ update_flag state count 2",
            "references unknown formable id 9",
            "focus.txt: commit references unknown formable id 99",
            "focus.txt: commit size 2 != update_flag state count 3 for id 1",
            "focus.txt: guard size 8 matches no formable state count",
            "CCC: no update_flag available block",
            "not a formable decision shape",
        ],
    ),
}


def _assert_mentions(rows, fragments):
    assert bool(rows) == bool(fragments), rows
    for fragment in fragments:
        assert any(fragment in row for row in rows), (fragment, rows)


@pytest.mark.parametrize(
    ("decisions", "texts", "mentions"), _FORMABLE_CASES.values(), ids=_FORMABLE_CASES
)
def test_formable_commitment_drift(decisions, texts, mentions):
    factories = [
        decision_factory(text, V._FORMABLE_DECISIONS_BASENAME) for text in decisions
    ]

    _assert_mentions(V._find_formable_commitment_rows(factories, texts), mentions)


_SPECIAL_EFFECTS = "common/scripted_effects/00_formable_effects.txt"
_SPECIAL_DEFINITION = (
    "commit_special_formable = {\n\thidden_effect = {\n"
    "\t\tset_variable = { formable_committed_id = special_formable_id }\n"
    "\t\tset_variable = { formable_committed_size = %d }\n\t}\n}\n"
)
_SPECIAL_CALL = (
    "\t\t\tset_temp_variable = { special_formable_id = %d }\n"
    "\t\t\tcommit_special_formable = yes\n"
)
_DEFINED = {_SPECIAL_EFFECTS: _SPECIAL_DEFINITION % 1000}

# Special identities commit through commit_special_formable, right after a
# special_formable_id setter. The known ids here are 101 (X) and 102 (Y).
# case: ({file: text}, largest formable, what the rows must mention)
_SPECIAL_FORMABLE_CASES = {
    "every id committed": (
        {**_DEFINED, "events/x.txt": _SPECIAL_CALL % 101 + _SPECIAL_CALL % 102},
        83,
        [],
    ),
    "unknown id": (
        {**_DEFINED, "events/x.txt": _SPECIAL_CALL % 150},
        83,
        ["unknown special formable id 150"],
    ),
    "setter without the call": (
        {
            **_DEFINED,
            "events/x.txt": "\t\t\tset_temp_variable = { special_formable_id = 101 }\n",
        },
        83,
        ["1 special_formable_id setter(s) not immediately followed"],
    ),
    "call without the setter": (
        {**_DEFINED, "events/x.txt": "\t\t\tcommit_special_formable = yes\n"},
        83,
        ["1 commit_special_formable call(s) without a preceding"],
    ),
    "drifted definition": (
        {_SPECIAL_EFFECTS: _SPECIAL_DEFINITION % 500},
        83,
        ["must set formable_committed_id = special_formable_id"],
    ),
    "no definition": (
        {"events/x.txt": _SPECIAL_CALL % 101},
        83,
        [
            "expected exactly one commit_special_formable definition, found 0",
            "special formable id 102 (Y) has no call site",
        ],
    ),
    "sentinel no larger than a formable": (
        _DEFINED,
        1000,
        ["does not exceed the largest formable state count 1000"],
    ),
    "sentinel written inline": (
        {**_DEFINED, "events/x.txt": _set_pair(105, 1000)},
        83,
        [
            "sentinel size literal 1000 outside commit_special_formable",
            "special formable id 105 written inline",
        ],
    ),
    # An effect_tooltip body renders but never runs.
    "call inside effect_tooltip": (
        {
            **_DEFINED,
            "events/x.txt": "\t\teffect_tooltip = {\n"
            + _SPECIAL_CALL % 101
            + "\t\t}\n",
        },
        83,
        ["special formable id 101 (X) has no call site"],
    ),
}


@pytest.mark.parametrize(
    ("texts", "largest", "mentions"),
    _SPECIAL_FORMABLE_CASES.values(),
    ids=_SPECIAL_FORMABLE_CASES,
)
def test_special_formable_commits(monkeypatch, texts, largest, mentions):
    monkeypatch.setattr(V, "_SPECIAL_FORMABLE_IDS", {101: "X", 102: "Y"})

    _assert_mentions(V._find_special_formable_rows(texts, largest), mentions)


@pytest.mark.parametrize(
    ("files", "mentions"),
    (
        ({"common/decisions/other.txt": "cat = {\n}\n"}, []),
        (
            {"events/x.txt": "x.1 = {\n" + _SPECIAL_CALL % 101 + "}\n"},
            ["expected exactly one commit_special_formable definition, found 0"],
        ),
    ),
    ids=("no ratchet site", "sentinel mention"),
)
def test_formable_sync_runs_on_any_ratchet_mention(tmp_path, files, mentions):
    validator = _mod(tmp_path, files)

    validator.validate_formable_commitment_sync()

    _assert_mentions([issue.message for issue in validator._issues], mentions)


# ---- icons and description images -------------------------------------------

_SPRITES = frozenset(
    {
        "tungsten",
        "GFX_decision_generic_intelligence_operation",
        "GFX_decision_category_generic_economy",
        "GFX_zsr_parlament",
        "GFX_decision_oil",
    }
)

# (reference kind, value): the finding, or None when a sprite resolves
_SPRITE_CASES = {
    ("decision", "tungsten"): None,
    ("decision", "[GetIcon]"): None,
    # The engine prepends GFX_decision_ to a bare name.
    ("decision", "nope"): (
        "owner: icon = nope -> no sprite nope / GFX_decision_nope / GFX_nope defined "
        "in interface/*.gfx (create the sprite or pick an existing icon)"
    ),
    ("category_icon", "generic_economy"): None,
    # GFX_decision_oil exists, but a category needs GFX_decision_category_oil.
    ("category_icon", "oil"): (
        "owner: icon = oil -> no sprite oil / GFX_decision_category_oil defined "
        "in interface/*.gfx (create the sprite or pick an existing icon)"
    ),
    ("category_picture", "zsr_parlament"): (
        "owner: picture = zsr_parlament -> no sprite zsr_parlament defined "
        "in interface/*.gfx (create the sprite or pick an existing icon)"
    ),
}


@pytest.mark.parametrize(
    ("reference", "message"), _SPRITE_CASES.items(), ids=map(" ".join, _SPRITE_CASES)
)
def test_missing_sprite_message(reference, message):
    kind, value = reference

    assert V._missing_sprite_message(kind, "owner", value, _SPRITES) == message


def test_qualified_icon_is_not_prefixed_again():
    assert V._sprite_candidates("decision", "GFX_decision_x") == ["GFX_decision_x"]


_DECISION_FILE = "common/decisions/d.txt"

# case: (file, text, references read as (owner, kind, value, line))
_ICON_REFERENCE_CASES = {
    # The sprite pattern stops at the space in a quoted name.
    "bare and quoted": (
        _DECISION_FILE,
        'cat = {\n\tfirst = {\n\t\ticon = money\n\t}\n\tsecond = {\n\t\ticon = "GFX_a b"\n\t}\n}\n',
        [("first", "decision", "money", 3)],
    ),
    "commented icon": (
        _DECISION_FILE,
        "cat = {\n\tfirst = {\n\t\t# icon = ghost\n\t\ticon = money\n\t}\n}\n",
        [("first", "decision", "money", 4)],
    ),
    "CRLF lines": (
        _DECISION_FILE,
        "cat = {\r\n\tfirst = {\r\n\t\ticon = money\r\n\t}\r\n}\r\n",
        [("first", "decision", "money", 3)],
    ),
    "dot and hyphen in a name": (
        _DECISION_FILE,
        "cat = {\n\ta = {\n\t\ticon = GFX_CTC.5\n\t}\n\tb = {\n\t\ticon = GFX_MIG-29-GER\n\t}\n}\n",
        [("a", "decision", "GFX_CTC.5", 3), ("b", "decision", "GFX_MIG-29-GER", 6)],
    ),
    "dynamic icon block": (
        _DECISION_FILE,
        "cat = {\n\tdyn = {\n\t\ticon = {\n"
        "\t\t\tkey = GFX_decision_high\n\t\t\ttrigger = { has_war = yes }\n"
        "\t\t}\n\t\ticon = {\n\t\t\tkey = GFX_decision_low\n\t\t}\n\t}\n}\n",
        [
            ("dyn", "decision", "GFX_decision_high", 3),
            ("dyn", "decision", "GFX_decision_low", 7),
        ],
    ),
    "icon nested in an effect": (
        _DECISION_FILE,
        "cat = {\n\tdec = {\n\t\ticon = money\n\t\tcomplete_effect = {\n"
        "\t\t\tcreate_intelligence_agency = {\n\t\t\t\ticon = GFX_agency_logo\n"
        "\t\t\t}\n\t\t}\n\t}\n}\n",
        [("dec", "decision", "money", 3)],
    ),
    "quoted opening brace in an earlier decision": (
        _DECISION_FILE,
        'cat = {\n\ta = {\n\t\tcomplete_effect = { log = "a {" }\n\t}\n'
        "\tb = {\n\t\ticon = money\n\t}\n}\n",
        [("b", "decision", "money", 6)],
    ),
    "quoted closing brace in an earlier decision": (
        _DECISION_FILE,
        'cat = {\n\ta = {\n\t\tcomplete_effect = { log = "a }" }\n\t}\n'
        "\tb = {\n\t\ticon = money\n\t}\n}\n",
        [("b", "decision", "money", 6)],
    ),
    "unbalanced dynamic icon block": (
        _DECISION_FILE,
        "cat = {\n\tdec = {\n\t\ticon = {\n\t\t\tkey = GFX_decision_x\n",
        [],
    ),
    "category file": (
        "common/decisions/categories/c.txt",
        "ABK_politics = {\n\ticon = generic_economy\n\tpicture = GFX_decision_abkhaz\n}\n",
        [
            ("ABK_politics", "category_icon", "generic_economy", 2),
            ("ABK_politics", "category_picture", "GFX_decision_abkhaz", 3),
        ],
    ),
    "unreadable file": (_DECISION_FILE, None, []),
}


@pytest.mark.parametrize(
    ("relative", "text", "references"),
    _ICON_REFERENCE_CASES.values(),
    ids=_ICON_REFERENCE_CASES,
)
def test_icon_references_are_read_with_their_owner(
    tmp_path, relative, text, references
):
    if text is not None:
        write_tree(tmp_path, {relative: text})

    found = V._extract_decision_icons((str(tmp_path / relative), str(tmp_path)))

    assert found == references


def test_category_file_is_recognised_with_windows_separators():
    assert V._is_category_file(r"mod\common\decisions\categories\99_x.txt")
    assert not V._is_category_file("mod/common/decisions/99_x.txt")


def test_slot_follows_the_size_band():
    sizes = ((33, 32), (52, 40), (114, 101), (38, 40))

    assert [V._slot_for_size(*size) for size in sizes] == [
        "decision",
        "category_icon",
        "category_picture",
        None,
    ]


def _textures(tmp_path, sprites, vanilla=None):
    index = {}
    for name, size in sprites.items():
        path = tmp_path / f"{name}.dds"
        path.write_bytes(dds_stub(*size))
        index[name] = str(path)
    return SpriteSizeIndex(index, vanilla)


_DECISION_SIZE = (33, 32)
_CATEGORY_SIZE = (52, 40)

# case: (slot, value, mod sprite sizes, vanilla sprite sizes, message fragments)
_ICON_TYPE_CASES = {
    "category art on a decision": (
        "decision",
        "politics",
        {"GFX_decision_politics": _CATEGORY_SIZE},
        None,
        ("category icon art", V._MOD_ART_HINT),
    ),
    "exempt sprite": (
        "decision",
        "GFX_decision_sinaloa_high",
        {"GFX_decision_sinaloa_high": _CATEGORY_SIZE},
        None,
        None,
    ),
    "vanilla art in the wrong slot": (
        "decision",
        "GFX_decision_category_x",
        {},
        {"GFX_decision_category_x": _CATEGORY_SIZE},
        ("category icon art", V._VANILLA_ART_HINT),
    ),
    "mod texture shadows the vanilla one": (
        "decision",
        "politics",
        {"GFX_decision_politics": _DECISION_SIZE},
        {"GFX_decision_politics": _CATEGORY_SIZE},
        None,
    ),
    "decision art on a category": (
        "category_icon",
        "x",
        {"GFX_decision_category_x": _DECISION_SIZE},
        None,
        ("decision icon art",),
    ),
    "art sized for its slot": (
        "decision",
        "politics",
        {"GFX_decision_politics": _DECISION_SIZE},
        None,
        None,
    ),
    # The missing icon check owns a sprite that does not resolve.
    "unresolved sprite": ("decision", "nothing", {}, None, None),
    "runtime value": (
        "decision",
        "[?var]",
        {"GFX_decision_politics": _CATEGORY_SIZE},
        None,
        None,
    ),
}


@pytest.mark.parametrize(
    ("slot", "value", "sprites", "vanilla", "fragments"),
    _ICON_TYPE_CASES.values(),
    ids=_ICON_TYPE_CASES,
)
def test_icon_type_message(tmp_path, slot, value, sprites, vanilla, fragments):
    textures = _textures(tmp_path, sprites, vanilla)

    message = V._icon_type_message(slot, "owner", value, textures)

    if fragments is None:
        assert message is None
    else:
        assert all(fragment in message for fragment in fragments), message


_ICON_POLITICS = "\t\ticon = politics\n"


def test_texture_missing_from_disk_is_counted_not_reported(tmp_path):
    textures = SpriteSizeIndex({"GFX_decision_politics": str(tmp_path / "gone.dds")})

    assert V._icon_type_message("decision", "d", "politics", textures) is None
    assert textures.unreadable == 1


def test_icon_with_a_missing_texture_is_a_warning_at_its_line(tmp_path, monkeypatch):
    textures = {f"GFX_filler_{i}": "unused.dds" for i in range(1000)}
    textures["GFX_decision_politics"] = str(tmp_path / "gone.dds")
    monkeypatch.setattr(
        V, "build_sprite_size_index", lambda *a, **k: SpriteSizeIndex(textures)
    )
    validator = _mod(
        tmp_path,
        {
            "common/decisions/d.txt": "cat = {\n"
            + _nested("dec_one", _ICON_POLITICS)
            + "}\n"
        },
    )

    validator.validate_icon_types()

    assert [(i.category, i.severity, i.line) for i in validator._issues] == [
        ("decision-icon-unmeasured", V.Severity.WARNING, 3)
    ]


def test_icon_checks_skip_themselves_without_a_sprite_index(tmp_path, monkeypatch):
    monkeypatch.setattr(V, "build_sprite_index", lambda *a, **k: {"GFX_one": "x"})
    monkeypatch.setattr(
        V, "build_sprite_size_index", lambda *a, **k: SpriteSizeIndex({})
    )
    validator = _mod(tmp_path, {})

    validator.validate_missing_icons()
    validator.validate_icon_types()

    assert validator._issues == []
    assert sum("did not load" in line for line in validator.output_lines) == 2


_PMC_LOC = (
    "l_english:\n"
    ' pmc_global_management: "Global PMC management"\n'
    ' pmc_global_management_desc: "\\n£CHVK_desctext_pmc\\n\\n\\n\\nManage it."\n'
)
_PMC_PICTURE = {"GFX_CHVK_desctext_pmc": (480, 225)}


def test_desc_image_padding_scales_with_height():
    assert [V._desc_image_min_newlines(height) for height in (20, 73, 225)] == [0, 1, 6]


def test_leading_desc_icon_is_read_with_its_newlines_and_line():
    after_prose = 'l_english:\n cat_desc: "Some prose first.\\n£CHVK_desctext_pmc"\n'

    assert V._leading_desc_icons(_PMC_LOC) == [
        ("pmc_global_management", 1, "CHVK_desctext_pmc", 3)
    ]
    assert V._leading_desc_icons(after_prose) == []


# case: (newlines after the icon, icon, sprite sizes, message fragments)
_DESC_IMAGE_CASES = {
    "tall picture with banner padding": (
        1,
        "CHVK_desctext_pmc",
        _PMC_PICTURE,
        ("480x225", "6"),
    ),
    "tall picture with six newlines": (6, "CHVK_desctext_pmc", _PMC_PICTURE, None),
    "unresolved icon": (0, "nothing", {}, None),
}


@pytest.mark.parametrize(
    ("newlines", "icon", "sprites", "fragments"),
    _DESC_IMAGE_CASES.values(),
    ids=_DESC_IMAGE_CASES,
)
def test_desc_image_message(newlines, icon, sprites, fragments):
    message = V._desc_image_message("cat", newlines, icon, SpriteSizeIndex({}, sprites))

    if fragments is None:
        assert message is None
    else:
        assert all(fragment in message for fragment in fragments), message


@pytest.mark.parametrize(
    ("key", "expected"),
    (
        (
            "pmc_global_management",
            [("category-desc-image-overlap", V.Severity.WARNING, 3)],
        ),
        ("some_focus", []),
    ),
)
def test_desc_image_check_reads_category_descriptions(
    tmp_path, monkeypatch, key, expected
):
    monkeypatch.setattr(
        V, "build_sprite_size_index", lambda *a, **k: SpriteSizeIndex({}, _PMC_PICTURE)
    )
    validator = _mod(
        tmp_path,
        {
            "common/decisions/categories/categories.txt": "pmc_global_management = {\n"
            "\ticon = GFX_decision_category_generic\n}\n",
            "localisation/english/pmc_l_english.yml": _PMC_LOC.replace(
                "pmc_global_management", key
            ),
        },
    )

    validator.validate_category_desc_images()

    assert [(i.category, i.severity, i.line) for i in validator._issues] == expected


# ---- unlock tooltips and category announcements -----------------------------

_GENERIC_ICON = "\t\ticon = GFX_decision_generic\n"
_UNLOCK_FOCUS = "common/national_focus/test.txt"
_UNLOCK_MOD = {
    "common/decisions/categories/cat.txt": "md_category = {\n\ticon = GFX_decision_generic\n}\n"
    "md_hyphen-category = {\n\ticon = GFX_decision_generic\n}\n",
    "common/decisions/dec.txt": "md_category = {\n"
    + _nested("md_real_decision", _GENERIC_ICON)
    + _nested("md_hyphen-decision", _GENERIC_ICON)
    + "}\n",
}
_BLOCK_FORM = (
    "unlock_decision_tooltip = {\n\t\t\tdecision = %s\n"
    "\t\t\tshow_effect_tooltip = yes\n\t\t}"
)
_QUOTED_UNLOCK = 'log = "[GetDateText]: unlock_decision_tooltip = md_typo"'


def _no_decision(name):
    return (
        f"unlock_decision_tooltip = {name} -> no decision named {name} is defined "
        "in common/decisions (fix the typo or define it)"
    )


def _no_category(name):
    return (
        f"unlock_decision_category_tooltip = {name} -> no category named {name} is "
        "defined in common/decisions/categories (fix the typo or define it)"
    )


# A typo or a rename leaves the tooltip naming nothing (#3961).
# case: (completion_reward lines, (message, line) per finding)
_UNLOCK_TARGET_CASES = {
    "decision": (["unlock_decision_tooltip = md_real_decision"], []),
    "category": (["unlock_decision_category_tooltip = md_category"], []),
    "block form": ([_BLOCK_FORM % "md_real_decision"], []),
    "commented out": (
        [
            "# unlock_decision_tooltip = md_typo",
            "unlock_decision_tooltip = md_real_decision  # keep this one",
        ],
        [],
    ),
    "longer key around the keyword": (
        [
            "md_unlock_decision_tooltip = md_typo",
            "md_unlock_decision_category_tooltip = md_typo",
            "unlock_decision_tooltip_days = md_typo",
            "unlock_decision_category_tooltip_of = md_typo",
        ],
        [],
    ),
    "undefined decision": (
        ["unlock_decision_tooltip = md_typo"],
        [(_no_decision("md_typo"), 4)],
    ),
    # #3957: a decision used where the tooltip needs its category.
    "decision named as a category": (
        ["unlock_decision_category_tooltip = md_real_decision"],
        [(_no_category("md_real_decision"), 4)],
    ),
    "undefined block form": ([_BLOCK_FORM % "md_typo"], [(_no_decision("md_typo"), 4)]),
    "undefined hyphenated decision": (
        ["unlock_decision_tooltip = md_hyphen-typo"],
        [(_no_decision("md_hyphen-typo"), 4)],
    ),
    "undefined hyphenated category": (
        ["unlock_decision_category_tooltip = md_hyphen-catagory"],
        [(_no_category("md_hyphen-catagory"), 4)],
    ),
    # Blanking the quoted string keeps offsets, so the next line is still 5.
    "after a quoted keyword": (
        [_QUOTED_UNLOCK, "unlock_decision_tooltip = md_typo"],
        [(_no_decision("md_typo"), 5)],
    ),
}


def _unlock_mod(tmp_path, effects, extra=None):
    reward = "".join(f"\t\t{line}\n" for line in effects)
    focus = f"focus = {{\n\tid = md_test_focus\n\tcompletion_reward = {{\n{reward}\t}}\n}}\n"
    return _mod(tmp_path, {**_UNLOCK_MOD, _UNLOCK_FOCUS: focus, **(extra or {})})


@pytest.mark.parametrize(
    ("effects", "expected"), _UNLOCK_TARGET_CASES.values(), ids=_UNLOCK_TARGET_CASES
)
def test_undefined_unlock_targets(tmp_path, effects, expected):
    findings = _unlock_mod(tmp_path, effects)._undefined_unlock_targets()

    assert findings == [
        (message, os.path.normpath(_UNLOCK_FOCUS), line) for message, line in expected
    ]


def test_undefined_unlock_target_is_an_error_at_every_site(tmp_path):
    effect = "unlock_decision_tooltip = md_typo"
    validator = _unlock_mod(
        tmp_path,
        [effect],
        {
            "events/md_test_events.txt": "country_event = {\n\timmediate = {\n"
            f"\t\t{effect}\n\t}}\n}}\n",
            "history/countries/md_test.txt": "unlock_decision_category_tooltip = md_typo\n",
        },
    )

    validator.validate_undefined_unlock_tooltips()

    assert {(i.file, i.line, i.severity, i.category) for i in validator._issues} == {
        (path, line, V.Severity.ERROR, "undefined-unlock-tooltip-target")
        for path, line in (
            (_UNLOCK_FOCUS, 4),
            ("events/md_test_events.txt", 3),
            ("history/countries/md_test.txt", 1),
        )
    }


def _visible(*triggers):
    return "\tvisible = {\n" + "".join(f"\t\t{t}\n" for t in triggers) + "\t}\n"


_FLAG = "has_country_flag = md_test_flag"
_FLAG_GATE = _visible(_FLAG)
_COUNTRY_HISTORY = "history/countries/MDT - Test.txt"


def _category_mod(tmp_path, gate, files=None, category="md_test_category", **kwargs):
    base = {
        "common/decisions/categories/cat.txt": f"{category} = {{\n"
        f"\ticon = GFX_decision_generic\n{gate}}}\n",
        "common/decisions/dec.txt": f"{category} = {{\n"
        + _nested("md_test_decision", _GENERIC_ICON + "\t\tcost = 25\n")
        + "}\n",
    }
    return _mod(tmp_path, {**base, **(files or {})}, **kwargs)


# A category gated on state that flips during play shows up part-way through a
# game. History does not exempt it: the gate still has to be announced.
# case: (category gate, {other file: text}, the trigger the finding names)
_CATEGORY_GATE_CASES = {
    "flag": (_FLAG_GATE, {}, _FLAG),
    "focus": (
        _visible("has_completed_focus = md_other_focus"),
        {},
        "has_completed_focus = md_other_focus",
    ),
    "global flag": (
        _visible("has_global_flag = md_test_flag"),
        {},
        "has_global_flag = md_test_flag",
    ),
    "idea": (_visible("has_idea = md_test_idea"), {}, "has_idea = md_test_idea"),
    "variable": (
        _visible("check_variable = { md_test_var > 0 }"),
        {},
        "check_variable",
    ),
    "flag set in history": (
        _FLAG_GATE,
        {_COUNTRY_HISTORY: "set_country_flag = md_test_flag\n"},
        _FLAG,
    ),
    "flag commented out in history": (
        _FLAG_GATE,
        {_COUNTRY_HISTORY: "# set_country_flag = md_test_flag\n"},
        _FLAG,
    ),
    "first of two gates set in history": (
        _visible("has_country_flag = md_start", _FLAG),
        {_COUNTRY_HISTORY: "set_country_flag = md_start\n"},
        "has_country_flag = md_start",
    ),
    "no visible block": ("", {}, None),
    # On from the first day for that country, so there is nothing to announce.
    "tag": (_visible("original_tag = JAP"), {}, None),
    "AI only": (_visible("is_ai = yes", _FLAG), {}, None),
}


@pytest.mark.parametrize(
    ("gate", "files", "reported"),
    _CATEGORY_GATE_CASES.values(),
    ids=_CATEGORY_GATE_CASES,
)
def test_unannounced_category_gate(tmp_path, gate, files, reported):
    findings = _category_mod(tmp_path, gate, files)._unannounced_categories()

    assert_findings(
        findings,
        [("md_test_category", f"becomes visible on {reported} but")] * bool(reported),
    )


# Where an announcement can live: one file under each scanned root, with `%s`
# standing in for the effect.
_SOURCES = {
    "focus": (
        "common/national_focus/test.txt",
        "focus = {\n\tid = md_test_focus\n\tcompletion_reward = {\n\t\t%s\n\t}\n}\n",
    ),
    "event": (
        "events/test.txt",
        "country_event = {\n\tid = md_test.1\n\toption = {\n\t\t%s\n\t}\n}\n",
    ),
    "idea": (
        "common/ideas/test.txt",
        "ideas = {\n\tcountry = {\n\t\tmd_test_idea = {\n"
        "\t\t\ton_add = {\n\t\t\t\t%s\n\t\t\t}\n\t\t}\n\t}\n}\n",
    ),
    "decision": (
        "common/decisions/other.txt",
        "md_other_category = {\n\tmd_other_decision = {\n"
        "\t\tcomplete_effect = {\n\t\t\t%s\n\t\t}\n\t}\n}\n",
    ),
    "history": ("history/countries/md_test.txt", "%s\n"),
}
_ANNOUNCEMENTS = (
    "unlock_decision_category_tooltip = md_test_category",
    "unlock_decision_tooltip = md_test_decision",
    "unlock_decision_tooltip = { decision = md_test_decision }",
)
_NOT_ANNOUNCEMENTS = (
    "add_political_power = 10",
    "# unlock_decision_category_tooltip = md_test_category",
    'log = "unlock_decision_category_tooltip = md_test_category"',
    "md_unlock_decision_category_tooltip = md_test_category",
    "unlock_decision_category_tooltip = md_other_category",
)


@pytest.mark.parametrize(
    ("source", "effect", "findings"),
    [(source, _ANNOUNCEMENTS[0], 0) for source in _SOURCES]
    + [("focus", effect, 0) for effect in _ANNOUNCEMENTS[1:]]
    + [("focus", effect, 1) for effect in _NOT_ANNOUNCEMENTS],
)
def test_only_an_unlock_tooltip_announces_the_category(
    tmp_path, source, effect, findings
):
    path, template = _SOURCES[source]
    validator = _category_mod(tmp_path, _FLAG_GATE, {path: template % effect})

    assert len(validator._unannounced_categories()) == findings


def test_config_exempts_a_category_with_a_reason(tmp_path):
    exemptions = V.validation_config(
        "validate_decisions", "unannounced_category_exempt"
    )
    exempt = sorted(V._UNANNOUNCED_CATEGORY_EXEMPT)[0]

    assert all(reason.strip() for reason in exemptions.values())
    assert (
        _category_mod(tmp_path, _FLAG_GATE, category=exempt)._unannounced_categories()
        == []
    )


_CATEGORY_LOC = "localisation/english/test_l_english.yml"
_CATEGORY_UNLOCK = {
    _UNLOCK_FOCUS: _SOURCES["focus"][1]
    % "unlock_decision_category_tooltip = md_test_category"
}


def test_ai_only_category_is_resolved_from_the_tree(tmp_path):
    loc = 'l_english:\n md_test_decision: "Test"\n md_test_category: "Category"\n'
    validator = _category_mod(tmp_path, _visible("is_ai = yes"), {_CATEGORY_LOC: loc})

    assert validator._get_ai_only_by_category() == {"md_test_decision"}
    assert validator._get_ai_only_categories() == {"md_test_category": "cat.txt"}
    assert validator._ai_only_category_loc({"md_test_category"}) == [
        "md_test_category - cat.txt: AI-only decision category has "
        "localisation key 'md_test_category'"
    ]
    validator.validate_missing_localisation()
    assert validator.warnings_found == 2


def test_debug_gated_category_is_not_ai_only(tmp_path):
    gate = _visible("OR = {", "\tis_ai = yes", "\tis_debug = yes", "}")

    assert _category_mod(tmp_path, gate)._get_ai_only_by_category() == set()


def test_focus_unlock_exempts_the_ai_only_category_key(tmp_path):
    validator = _category_mod(tmp_path, _visible("is_ai = yes"), _CATEGORY_UNLOCK)

    assert validator._ai_only_category_loc({"md_test_category"}) == []


# ---- parsing and scanning ---------------------------------------------------


def test_stray_tab_brace_does_not_jump_into_column_zero_block():
    # The decision name is confined to its own line. Before that, a dangling
    # tab-indented `}` let the match jump across the next category header.
    text = (
        "cat_one = {\n"
        + _nested("alpha_decision", "\t\tdays_remove = 5\n")
        + "\t}\n}\n\ncat_two = {\n"
        + _nested("beta_decision", "\t\tdays_remove = 5\n")
        + "}\n"
    )

    blocks = V._DECISIONS_BLOCK_RE.findall(text)

    assert [V._DECISION_TOKEN_LINE_RE.findall(block)[0] for block in blocks] == [
        "alpha_decision",
        "beta_decision",
    ]
    assert not any(re.search(r"^\w+ = \{", block, re.MULTILINE) for block in blocks)


def test_factory_token_matches_noncanonical_header_spacing():
    spaced = "\tdecision_one= {\n\t\tdays_remove = 5\n\t}\n"

    assert decision_factory(spaced).token == "decision_one"


def test_quoted_brace_does_not_truncate_decision_block(tmp_path):
    # A `}` inside a multi-line quoted field lands on its own `\t}` line, the
    # shape the block closer matches.
    write_tree(
        tmp_path,
        {
            "common/decisions/quoted_brace.txt": "my_category = {\n"
            "\tstray_brace_decision = {\n"
            '\t\tname = "Broken\n\t}\n\tstring"\n'
            "\t\tcost = 42\n\t}\n}\n"
        },
    )

    decisions, _ = V.parse_all_decisions(str(tmp_path))

    assert len(decisions) == 1
    assert V.DecisionFactory(dec=decisions[0]).token == "stray_brace_decision"
    assert V.DecisionFactory(dec=decisions[0]).cost == "42"


# case: (file, text, (decisions, missions, removals, unlock references, checked))
_ACTIVATION_SCAN_CASES: dict[
    str,
    tuple[str, str, tuple[set[str], set[str], set[str], list[object], set[str]]],
] = {
    # The substring gate must admit a file that only removes targeted decisions.
    "remove_targeted_decision only": (
        "effects.txt",
        "some_effect = {\n"
        "\tremove_targeted_decision = { target = ROOT decision = my_targeted_dec }\n}\n",
        (set(), set(), {"my_targeted_dec"}, [], set()),
    ),
    "plain activate_decision": (
        "effects.txt",
        "some_effect = {\n\tactivate_decision = my_timed_dec\n}\n",
        ({"my_timed_dec"}, set(), set(), [], set()),
    ),
    "skipped file": (
        "events/FR_loc_events.txt",
        "remove_decision = some_decision\n",
        (set(), set(), set(), [], set()),
    ),
}


@pytest.mark.parametrize(
    ("relative", "text", "scan"),
    _ACTIVATION_SCAN_CASES.values(),
    ids=_ACTIVATION_SCAN_CASES,
)
def test_activation_scan_of_one_file(tmp_path, relative, text, scan):
    write_tree(tmp_path, {relative: text})

    assert V._scan_activations_and_removals(str(tmp_path / relative)) == scan


def test_activation_scan_uses_only_shipped_content_roots(tmp_path):
    validator = _mod(
        tmp_path,
        {
            "common/scripted_effects/effects.txt": "activate_mission = shipped_mission\n",
            "resources/archive.txt": "activate_mission = archived_mission\n",
        },
    )

    assert validator._get_activation_removal_scan() == (
        set(),
        {"shipped_mission"},
        set(),
        [],
        set(),
    )


def test_scripted_localisation_keys_skip_ignored_files(tmp_path):
    write_tree(
        tmp_path,
        {
            "common/scripted_localisation/00_keys.txt": "defined_text = {\n"
            "\tname = GetDecisionCost\n\ttext = { trigger = { } }\n}\n",
            "common/scripted_localisation/FR_loc_keys.txt": "defined_text = {\n"
            "\tname = GetFrenchCost\n}\n",
            "common/scripted_localisation/no_defs.txt": "# nothing here\n",
        },
    )

    assert V._load_scripted_localisation_keys(str(tmp_path)) == {"GetDecisionCost"}


def test_block_helpers_tolerate_empty_and_unbalanced_input(tmp_path):
    nested = " OR = { has_war = yes } tag = GER "

    assert V._extract_from_blocks("FROM = {" + nested + "}") == [nested]
    assert V._extract_from_blocks("FROM = {") == []
    assert V._extract_from_blocks("") == []
    assert V._is_sole_flat_pin("", "GER") is False
    assert _mod(tmp_path, {})._normalize_block("") == ""
    with pytest.raises(ValueError):
        V._int_literal("bad")


def test_flat_tag_pins_reads_a_nested_category_allowed_block():
    categories = {
        "cat": '\tallowed = {\n\t\tNOT = { has_dlc = "x" }\n\t\toriginal_tag = GER\n\t}\n'
    }

    assert V._category_allowed_pins(categories) == {"cat": {_GER}}


_WITH_AVAILABLE = _nested(
    "dec", _block("available", "NOT = { has_war = yes }") + "\t\tcost = 10\n"
)

# case: (file content, decision, content after the available block is removed)
_REMOVE_AVAILABLE_CASES = {
    "nested braces": (_WITH_AVAILABLE, "dec", _nested("dec", "\t\tcost = 10\n")),
    "unknown decision": (_WITH_AVAILABLE, "missing_token", None),
    "no available block": (_nested("dec", "\t\tcost = 10\n"), "dec", None),
    "unbalanced block": ("\tdec = {\n\t\tavailable = {\n", "dec", None),
}


@pytest.mark.parametrize(
    ("content", "token", "patched"),
    _REMOVE_AVAILABLE_CASES.values(),
    ids=_REMOVE_AVAILABLE_CASES,
)
def test_remove_available_block(content, token, patched):
    assert V._remove_available_block_for_token(content, token) == patched


def test_decision_file_fixes_report_what_they_cannot_apply(tmp_path):
    validator = _mod(
        tmp_path, {"common/decisions/present.txt": "cat = {\n\tdec = { }\n}\n"}
    )

    fixed = validator._apply_decision_file_fixes(
        [("absent_token", "absent.txt"), ("dec", "present.txt")],
        lambda content, token: None,
    )

    assert fixed == 0
    assert any("Could not locate file: absent.txt" in m for m in validator.output_lines)
    assert any(
        "Could not patch dec in present.txt" in m for m in validator.output_lines
    )


def test_fix_rewrites_missing_ai_factors_and_duplicate_available(tmp_path):
    validator = _mod(
        tmp_path,
        {
            "common/decisions/fix.txt": "cat = {\n"
            + _nested("missing_ai", "\t\tvisible = { has_war = yes }\n")
            + _nested(
                "same_blocks",
                _block("visible", "has_war = yes")
                + _block("available", "has_war = yes"),
            )
            + "}\n"
        },
        fix=True,
    )
    decision_file = tmp_path / "common/decisions/fix.txt"

    validator.validate_ai_factors()
    assert "ai_will_do = {" in decision_file.read_text()
    validator.validate_visible_equals_available()
    assert "same_blocks = {\n\t\tvisible" in decision_file.read_text()
    assert "\n\t\tavailable =" not in decision_file.read_text()


# ---- whole-validator runs ---------------------------------------------------


@pytest.mark.parametrize(
    "flags",
    (
        {},
        {"missing_icons": True, "unannounced_categories": True, "naming_style": True},
    ),
    ids=("default", "opt-in checks"),
)
def test_run_validations_calls_every_check(tmp_path, monkeypatch, flags):
    called, checks = checks_called_by_run(_mod(tmp_path, {}, **flags), monkeypatch)

    if not flags:
        checks = [name for name in checks if name not in _OPT_IN_CHECKS]
    assert called == checks


def test_cli_exposes_the_opt_in_checks():
    parser = argparse.ArgumentParser()
    V._add_extra_args(parser)

    assert parser.parse_args(["--unannounced-categories"]).unannounced_categories
    assert not parser.parse_args([]).unannounced_categories
    assert parser.parse_args(["--naming-style"]).naming_style
    assert not parser.parse_args([]).naming_style


_ICON = "\t\ticon = icon\n"
_GER_TARGET = _block("targets", "GER = { }")
_FROM_WAR = "FROM = { has_war = yes }"
_MISSION_DAYS = "\t\tdays_mission_timeout = 3\n"

# One decision per finding the full run reports.
_FINDING_DECISIONS = {
    "manual_unused": _block("allowed", "always = no"),
    "manual_used": _block("allowed", "always = no"),
    "missing_ai": "",
    "selectable_mission": _MISSION_DAYS + "\t\tselectable_mission = yes\n",
    "nonselect_mission": _MISSION_DAYS + "\t\tai_will_do = { base = 1 }\n",
    "custom_cost": _block("custom_cost_trigger", "has_political_power > 10"),
    "target_no_set": _block("target_trigger", "has_war = yes"),
    "cosmetic_targets": _block("targets", "GER FRA"),
    "from_no_trigger": _GER_TARGET + _block("visible", _FROM_WAR),
    "root_visible": _GER_TARGET + _block("visible", "has_war = yes"),
    "from_duplicate": _GER_TARGET
    + _block("target_trigger", _FROM_WAR)
    + _block("visible", _FROM_WAR),
    "from_move": _GER_TARGET
    + _block("target_trigger", _FROM_WAR)
    + _block("visible", _FROM_WAR + "\nFROM = { has_stability = yes }"),
    "from_unscoped": _block("visible", _FROM_WAR),
    "random_decision": _block("complete_effect", "random = { chance = 50 }"),
    "tag_checks": _block("allowed", "tag = GER\noriginal_tag = GER")
    + _block("visible", "tag = GER"),
    "category_recheck": _block("visible", "original_tag = GER"),
    "pp_hidden": _block("complete_effect", "add_political_power = -5"),
    "pp_double": "\t\tcost = 5\n"
    + _block("complete_effect", "add_political_power = -3"),
    "same_visible_available": _block("visible", "has_war = yes")
    + _block("available", "has_war = yes"),
    "bare_trigger": _block("available", "political_power < 5"),
    "missing_loc": "\t\tname = missing_name\n\t\tdesc = missing_desc\n"
    "\t\tcustom_cost_text = missing_cost\n",
    "missing_log": _block("complete_effect", "add_stability = 1"),
    "late_log": _block("complete_effect", 'add_stability = 1\nlog = "late"'),
    "mission_visible": _MISSION_DAYS + _block("visible", "has_war = yes"),
    "mission_script": _MISSION_DAYS
    + "\t\tactivation = { always = no }\n"
    + _block("visible", "has_war = yes"),
    "war_target": "\t\ttargets = { GER }\n\t\twar_with_on_complete = FROM\n",
    "war_all": "\t\twar_with_on_remove = FROM\n\t\twar_with_on_timeout = FROM\n",
    "war_no_hint": _block("complete_effect", "create_wargoal = yes"),
    "cancel_missing_visible": "\t\tcancel_if_not_visible = yes\n",
    "state_bad": "\t\tstate_target = any_owned_state\n" + _GER_TARGET,
    "mission_only": "\t\ttimeout_effect = { }\n\t\tactivation = { always = no }\n"
    "\t\tis_good = yes\n\t\tselectable_mission = yes\n"
    "\t\twar_with_on_timeout = GER\n\t\twar_with_target_on_timeout = yes\n",
    "orphan_remove": _block("remove_effect", "add_stability = 1"),
    "orphan_modifiers": "\t\ttargets_dynamic = yes\n\t\ttarget_non_existing = yes\n",
    "skip_ai_available": _block("available", "is_ai = no"),
    "skip_ai_visible": _block("visible", "always = no"),
    "late_money": _block("remove_effect", "add_to_variable = { treasury = -5 }"),
    "low_gate": _block("available", "check_variable = { treasury > 1 }")
    + _block(
        "complete_effect",
        "set_temp_variable = { treasury_change = -2 }\nmodify_treasury_effect = yes",
    ),
    "temp_read": _block("available", "check_variable = { treasury > pay }")
    + _block("complete_effect", "set_temp_variable = { pay = 5 }"),
    "double_log": _block("complete_effect", 'log = "first"\nlog = "second"'),
}
_FINDINGS_MOD = {
    "common/decisions/categories/categories.txt": "cat_allowed = {\n"
    "\tallowed = { original_tag = GER }\n}\n"
    "cat_unchecked = {\n}\ncat_empty = {\n}\ncat_orphan = {\n}\n"
    "cat_ai_disabled = {\n\tallowed = { always = no }\n}\n",
    "common/decisions/decisions.txt": "cat_allowed = {\n"
    + _nested(
        "decision_dup",
        _ICON
        + _block("allowed", "original_tag = GER")
        + _block("visible", "tag = GER\nGER = { has_war = yes }")
        + "\t\tdays_remove = 2\n"
        + _block("remove_effect", "add_stability = 1")
        + "\t\tcreate_wargoal = yes\n",
    )
    + _nested(
        "category_recheck_allowed", _ICON + _block("visible", "original_tag = GER")
    )
    + "}\ncat_unchecked = {\n"
    + _nested("decision_dup", _ICON)
    + _nested("no_allowed", _ICON)
    # The block matcher reads the decisions below without a category around them.
    + "}\ncat_empty = { }\n"
    + "".join(
        _nested(token, _ICON + body) for token, body in _FINDING_DECISIONS.items()
    )
    + "}\ncat_ai_disabled = {\n"
    + _nested("category_ai_skip", _ICON)
    + "}\n",
    "events/activations.txt": "activate_targeted_decision = { decision = manual_used }\n",
    "common/bop/bop.txt": "decision_category = cat_empty\n",
    "localisation/english/decisions_l_english.yml": 'l_english:\nmissing_ai:0 "Missing AI"\n',
    # validate_missing_icons skips itself below 1000 indexed sprites.
    "interface/filler.gfx": "spriteTypes = {\n"
    + "".join(f'\tspriteType = {{ name = "GFX_filler_{i}" }}\n' for i in range(1000))
    + "}\n",
}
# WARNINGs held back until their backlog clears.
_BACKLOG_WARNINGS = (
    "decision-cosmetic-targeting",
    "decision-duplicate-log",
    "decision-treasury-gate-below-charge",
    "decision-trigger-reads-temp-variable",
)
_PROMOTED_ERRORS = ("missing-decision-log", "decision-money-charged-late")
_REPORTED_CATEGORIES = (
    "missing-decision-localisation",
    *_PROMOTED_ERRORS,
    "decision-log-not-first",
    *_BACKLOG_WARNINGS,
    "bare-trigger-name",
    "missing-decision-war-hint",
    "missing-decision-icon",
    "Decision AI factor issues",
    "Decisions in categories without allowed",
    "Decisions with custom_cost_trigger",
    "Decisions with redundant tag checks",
    "Missions with visible block",
    "Regular decisions using mission-only",
    "Targeted decisions using war_with_on_",
    "Decisions charging political power",
    "Decisions double-charging PP",
    "Decisions using FROM without",
    "Decisions with FROM checks in visible/available",
    "Decisions with `allowed` redundant",
    "Decisions with cancel_if_not_visible",
    "Decisions with identical visible and available",
    "Decisions with tag/original_tag",
    "Decisions with target_root_trigger",
    "Decisions with targets_dynamic",
    "Duplicated decisions found",
    "Repeatable decisions",
    "State-targeted decisions",
    "Targeted decisions with FROM checks",
    "Unused decision categories",
    "Unused decisions",
    "Decisions spending political power",
    "Decisions with remove_effect",
)


def test_full_run_reports_every_finding_category(tmp_path):
    validator = _mod(tmp_path, _FINDINGS_MOD, missing_icons=True)

    validator.run_all_validations()

    categories = {issue.category for issue in validator._issues}
    messages = [issue.message for issue in validator._issues]
    for marker in _REPORTED_CATEGORIES:
        assert any(marker in category for category in categories), marker
    assert "unannounced-decision-category" not in categories
    for category in _PROMOTED_ERRORS:
        severities = {i.severity for i in validator._issues if i.category == category}
        assert severities == {V.Severity.ERROR}, category
    for category in _BACKLOG_WARNINGS:
        severities = {i.severity for i in validator._issues if i.category == category}
        assert severities == {V.Severity.WARNING}, category
    for token in ("manual_unused", "pp_hidden", "orphan_modifiers"):
        assert any(token in message for message in messages), token
    assert not any(
        "category_ai_skip" in message and "AI factor" in message for message in messages
    )
    assert any("from_move" in m and "move the FROM" in m for m in messages)


def test_clean_mod_passes_full_staged_and_strict_runs(tmp_path, monkeypatch):
    files = {
        "common/decisions/categories/cat.txt": "cat = { }\n",
        "common/decisions/clean.txt": "cat = {\n"
        + _nested("clean_decision", "\t\tai_will_do = { base = 0 }\n")
        + _nested(
            "paid_decision",
            _block("available", "check_variable = { treasury > 2 }")
            + _block(
                "complete_effect",
                _LOG.strip() + "\nset_temp_variable = { treasury_change = -2 }"
                "\nmodify_treasury_effect = yes",
            )
            + "\t\tai_will_do = { base = 0 }\n",
        )
        + "}\n",
        "localisation/english/clean.yml": 'l_english:\nclean_decision:0 "Clean"\n'
        'paid_decision:0 "Paid"\n',
    }
    clean = _mod(tmp_path, files)
    assert clean.run_all_validations() == 0
    assert clean._issues == []

    monkeypatch.setenv("MD_STAGED_FILES", "common/decisions/clean.txt")
    staged = _mod(tmp_path, {}, staged_only=True)
    staged.run_all_validations()
    assert staged._issues == []

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "validate_decisions.py",
            "--path",
            str(tmp_path),
            "--strict",
            "--workers",
            "1",
        ],
    )
    with pytest.raises(SystemExit) as result:
        run_validator_main(V.Validator, "decisions", extra_args_fn=V._add_extra_args)
    assert result.value.code == 0


_LOGGED = _block("complete_effect", _LOG.strip())
_ONE_LINE_REMOVE = "\t\tremove_effect = { add_stability = 0.1 }\n"
_SPRITE = (
    '\tspriteType = {\n\t\tname = "%s"\n\t\ttexturefile = "gfx/interface/%s.dds"\n\t}\n'
)
_OPT_IN_MOD = {
    "common/decisions/decisions.txt": "cat_bop_only = {\n"
    + _nested(
        "bop_decision",
        '\t\ticon = good\n\t\tcustom_cost_text = "[GetUnknownCost]"\n' + _LOGGED,
    )
    + "}\ncat_main = {\n"
    + _nested("wrong_icon", "\t\ticon = wrong\n" + _LOGGED)
    + _nested(
        "partial_allowed",
        _block("allowed", "original_tag = GER\nhas_war = no") + _LOGGED,
    )
    + _nested("disabled_remove", "\t\tallowed = { always = no }\n" + _ONE_LINE_REMOVE)
    + _nested("removed_elsewhere", _ONE_LINE_REMOVE)
    + _nested("mission_remove", "\t\tdays_mission_timeout = 30\n" + _ONE_LINE_REMOVE)
    + "}\n",
    "common/decisions/FR_loc_decisions.txt": "cat_fr = { }\n",
    "common/decisions/categories/categories.txt": "".join(
        f"{category} = {{\n\ticon = GFX_decision_category_generic_operation\n{gate}}}\n"
        for category, gate in (
            ("cat_empty", ""),
            ("cat_bop_only", ""),
            ("cat_main", "\tvisible = { has_country_flag = midgame_flag }\n"),
        )
    ),
    "interface/filler.gfx": "spriteTypes = {\n"
    + "".join(_SPRITE % (f"GFX_filler_{i}", "filler") for i in range(1000))
    + _SPRITE % ("GFX_decision_good", "filler")
    + _SPRITE % ("GFX_decision_wrong", "banner")
    + "}\n",
    "common/bop/bop.txt": "decision_category = cat_empty\n",
    "common/national_focus/germany.txt": "GER_unify = {\n\tcompletion_reward = {\n"
    "\t\tset_variable = { formable_committed_id = 1 }\n\t}\n}\n",
    "events/removals.txt": "remove_decision = removed_elsewhere\n",
    "localisation/english/decisions_l_english.yml": 'l_english:\n bop_decision:0 "BOP"\n'
    ' wrong_icon:0 "Wrong"\n disabled_remove:0 "Disabled"\n'
    ' removed_elsewhere:0 "Removed"\n mission_remove:0 "Mission"\n'
    ' cat_bop_only:0 "BOP category"\n cat_main:0 "Main"\n cat_empty:0 "Empty"\n',
}


def _opt_in_mod(tmp_path, **kwargs):
    banner = tmp_path / "gfx" / "interface" / "banner.dds"
    banner.parent.mkdir(parents=True)
    banner.write_bytes(dds_stub(114, 101))
    return _mod(tmp_path, _OPT_IN_MOD, **kwargs)


def test_full_run_with_both_opt_in_checks(tmp_path):
    validator = _opt_in_mod(tmp_path, missing_icons=True, unannounced_categories=True)

    validator.run_validations()

    severities = {(i.category, i.severity) for i in validator._issues}
    assert ("decision-icon-slot-mismatch", V.Severity.ERROR) in severities
    assert ("unannounced-decision-category", V.Severity.WARNING) in severities
    assert any("cat_main" in i.message for i in validator._issues)
    assert any(
        "GetUnknownCost" in i.message
        for i in validator._issues
        if i.category == "missing-decision-localisation"
    )
    # `icon = good` and `icon = wrong` both resolve, so neither is missing.
    assert not any(
        "wrong_icon" in i.message or "bop_decision" in i.message
        for i in validator._issues
        if i.category == "missing-decision-icon"
    )


def test_orphaned_remove_effect_skips_every_exempt_shape(tmp_path):
    validator = _opt_in_mod(tmp_path)

    validator.validate_orphaned_remove_effect()

    assert validator._issues == []


_TIMER = "\t\tdays_remove = 30\n"
# case: (decision token, decision body, reported)
_TIMER_CASES = {
    "nothing reads the timer": (
        "timer_dec",
        _TIMER + _block("ai_will_do", "base = 1\nmodifier = { factor = 0 }"),
        True,
    ),
    "remove_effect at the end": ("timer_dec", _TIMER + _ONE_LINE_REMOVE, False),
    "modifier while active": (
        "timer_dec",
        _TIMER + _block("modifier", "stability_factor = 0.1"),
        False,
    ),
    "targeted modifier while active": (
        "timer_dec",
        _TIMER + _block("targeted_modifier", "tag = FROM"),
        False,
    ),
    "has_decision reads the timer": ("checked_timer", _TIMER, False),
    "mission": ("timer_dec", _TIMER + _MISSION_DAYS, False),
}


@pytest.mark.parametrize(
    ("token", "body", "reported"), _TIMER_CASES.values(), ids=_TIMER_CASES
)
def test_timer_without_remove_effect(tmp_path, token, body, reported):
    validator = _mod(
        tmp_path,
        {
            "common/decisions/timers.txt": "cat = {\n" + _nested(token, body) + "}\n",
            "events/checks.txt": "checks = { has_decision = checked_timer }\n",
        },
    )

    validator.validate_timer_without_remove_effect()

    expected = (
        "decision-days-remove-without-effect",
        f"{token} - days_remove = 30 but no remove_effect, modifier, or has_decision"
        " check reads the timer",
        "common/decisions/timers.txt",
        2,
    )
    assert issue_rows(validator) == [expected] * reported
    assert validator.warnings_found == reported


_DECISIONS_FILE = "common/decisions/ser.txt"
_VOJ_PREFIX_ROW = (
    "decision-prefix-owner",
    "Decision VOJ_integrate has the VOJ prefix but allowed admits SER",
    _DECISIONS_FILE,
    2,
)
# case: (category, category allowed, decision, decision allowed, rows as
#        (category, message, file, line))
_NAMING_CASES = {
    "lowercase ids": ("SER_main", "", "SER_invite_bosnia", "original_tag = SER", []),
    "uppercase decision": (
        "SER_main",
        "",
        "SER_The_Confederacy",
        "original_tag = SER",
        [
            (
                "decision-id-case",
                "Decision SER_The_Confederacy is not lowercase after its prefix",
                _DECISIONS_FILE,
                2,
            )
        ],
    ),
    "uppercase category": (
        "SER_Political",
        "",
        "SER_invite_bosnia",
        "",
        [
            (
                "decision-id-case",
                "Category SER_Political is not lowercase after its prefix",
                "common/decisions/categories/cats.txt",
                1,
            )
        ],
    ),
    "decision allowed names another country": (
        "SER_main",
        "",
        "VOJ_integrate",
        "original_tag = SER",
        [_VOJ_PREFIX_ROW],
    ),
    "category lock names another country": (
        "SER_main",
        "original_tag = SER",
        "VOJ_integrate",
        "",
        [_VOJ_PREFIX_ROW],
    ),
    "prefix that is not a country": (
        "SER_main",
        "",
        "SUB_annex",
        "original_tag = SER",
        [],
    ),
}


@pytest.mark.parametrize(
    ("category", "category_allowed", "token", "allowed", "rows"),
    _NAMING_CASES.values(),
    ids=_NAMING_CASES,
)
def test_naming_style(tmp_path, category, category_allowed, token, allowed, rows):
    category_body = (
        f"\tallowed = {{ {category_allowed} }}\n" if category_allowed else ""
    )
    validator = _mod(
        tmp_path,
        {
            "common/country_tags/00_countries.txt": 'SER = "countries/Serbia.txt"\n'
            'VOJ = "countries/Vojvodina.txt"\n',
            "common/decisions/categories/cats.txt": f"{category} = {{\n"
            + category_body
            + "}\n",
            _DECISIONS_FILE: f"{category} = {{\n"
            + _nested(token, _block("allowed", allowed) if allowed else "")
            + "}\n",
        },
    )

    validator.validate_naming_style()

    assert issue_rows(validator) == rows
    assert validator.warnings_found == len(rows)


def test_unused_category_check_skips_bop_and_always_visible_categories(tmp_path):
    validator = _mod(
        tmp_path,
        {
            "common/decisions/categories/c.txt": "cat_unused = {\n}\ncat_bop = {\n}\n"
            "cat_shown = {\n\tvisible_when_empty = yes\n}\n",
            "common/bop/bop.txt": "decision_category = cat_bop\n",
        },
    )

    validator.validate_unused_categories()

    assert_findings([issue.message for issue in validator._issues], [("cat_unused",)])


def test_missing_bop_directory_is_reported(tmp_path):
    validator = _mod(tmp_path, {"common/decisions/categories/c.txt": "cat = {\n}\n"})

    validator.validate_unused_categories()

    assert any("No BOP files found" in line for line in validator.output_lines)
