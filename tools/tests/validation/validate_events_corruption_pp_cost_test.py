"""Event options that charge PP while attempting to decrease corruption."""

import argparse

import pytest
import validate_events as V
from shared.suite import build_validator, write_tree

_PP_COST = "\t\tadd_political_power = -400\n"
_DECREASE = "\t\tdecrease_corruption = yes\n"
_MIN_GUARD = "\t\tNOT = { has_idea = corruption_level_01 }\n"
_HIGH_CORRUPTION_GUARD = (
    "\t\tOR = {\n"
    "\t\t\thas_idea = corruption_level_06\n"
    "\t\t\thas_idea = corruption_level_07\n"
    "\t\t\thas_idea = corruption_level_08\n"
    "\t\t\thas_idea = corruption_level_09\n"
    "\t\t\thas_idea = corruption_level_10\n"
    "\t\t}\n"
)
_NESTED_GUARD = (
    "\t\tif = {\n"
    "\t\t\tlimit = { NOT = { has_idea = corruption_level_01 } }\n"
    "\t\t\tadd_political_power = -400\n"
    "\t\t\tdecrease_corruption = yes\n"
    "\t\t}\n"
)


def _option(body, trigger=""):
    option_trigger = f"\t\ttrigger = {{\n{trigger}\t\t}}\n" if trigger else ""
    return "\toption = {\n" "\t\tname = foo.1.a\n" + option_trigger + body + "\t}\n"


def _event(option, trigger=""):
    event_trigger = f"\ttrigger = {{\n{trigger}\t}}\n" if trigger else ""
    return "country_event = {\n\tid = foo.1\n" + event_trigger + option + "}\n"


_FINDING = [("foo.1.a", 3)]
# case: (event source, (option name, option line) findings)
_SCAN_CASES = {
    "unguarded charged corruption option": (
        _event(_option(_PP_COST + _DECREASE)),
        _FINDING,
    ),
    "refund covers a charge up to 150 PP per decrease": (
        _event(
            _option(
                "\t\tadd_political_power = -150\n"
                + _DECREASE
                + "\t\tadd_political_power = -150\n"
                + _DECREASE
            )
        ),
        [],
    ),
    "charge above the refund for every decrease is reported": (
        _event(_option("\t\tadd_political_power = -301\n" + _DECREASE + _DECREASE)),
        _FINDING,
    ),
    "event trigger excludes minimum corruption": (
        _event(_option(_PP_COST + _DECREASE), _MIN_GUARD),
        [],
    ),
    "higher corruption trigger protects one decrease": (
        _event(_option(_PP_COST + _DECREASE), _HIGH_CORRUPTION_GUARD),
        [],
    ),
    "low corruption bound does not protect repeated decreases": (
        _event(
            _option(_PP_COST + _DECREASE + _DECREASE),
            "\t\thas_idea = corruption_level_02\n",
        ),
        [("foo.1.a", 6)],
    ),
    "minimum exclusion does not protect repeated decreases": (
        _event(_option(_PP_COST + _DECREASE + _DECREASE), _MIN_GUARD),
        [("foo.1.a", 6)],
    ),
    "option trigger excludes minimum corruption": (
        _event(_option(_PP_COST + _DECREASE, _MIN_GUARD)),
        [],
    ),
    "immediate decrease invalidates the event trigger bound": (
        _event(_option(_PP_COST + _DECREASE), _MIN_GUARD).replace(
            _option(_PP_COST + _DECREASE),
            "\timmediate = {\n\t\tdecrease_corruption = yes\n\t}\n"
            + _option(_PP_COST + _DECREASE),
        ),
        [("foo.1.a", 9)],
    ),
    "immediate idea swap invalidates the event trigger bound": (
        _event(
            _option(_PP_COST + _DECREASE), "\thas_idea = corruption_level_02\n"
        ).replace(
            _option(_PP_COST + _DECREASE),
            "\timmediate = {\n"
            "\t\tswap_ideas = { remove_idea = corruption_level_02 "
            "add_idea = corruption_level_01 }\n"
            "\t}\n" + _option(_PP_COST + _DECREASE),
        ),
        [("foo.1.a", 9)],
    ),
    "immediate corruption idea addition invalidates the event trigger bound": (
        _event(
            _option(_PP_COST + _DECREASE), "\thas_idea = corruption_level_02\n"
        ).replace(
            _option(_PP_COST + _DECREASE),
            "\timmediate = { add_ideas = corruption_level_01 }\n"
            + _option(_PP_COST + _DECREASE),
        ),
        [("foo.1.a", 7)],
    ),
    "option idea swap invalidates the entry trigger bound": (
        _event(
            _option(
                "\t\tswap_ideas = { remove_idea = corruption_level_02 "
                "add_idea = corruption_level_01 }\n" + _PP_COST + _DECREASE
            ),
            "\thas_idea = corruption_level_02\n",
        ),
        [("foo.1.a", 6)],
    ),
    "option idea swap after the last decrease does not invalidate its bound": (
        _event(
            _option(
                _PP_COST
                + _DECREASE
                + "\t\tswap_ideas = { remove_idea = corruption_level_02 "
                "add_idea = corruption_level_01 }\n"
            ),
            "\thas_idea = corruption_level_02\n",
        ),
        [],
    ),
    "option idea swap between decreases invalidates its bound": (
        _event(
            _option(
                _PP_COST
                + _DECREASE
                + "\t\tswap_ideas = { remove_idea = corruption_level_02 "
                "add_idea = corruption_level_01 }\n" + _DECREASE
            ),
            "\thas_idea = corruption_level_06\n",
        ),
        [("foo.1.a", 6)],
    ),
    "outer idea mutation invalidates a nested hidden effect bound": (
        _event(
            _option(
                "\t\tswap_ideas = { remove_idea = corruption_level_02 "
                "add_idea = corruption_level_01 }\n"
                "\t\thidden_effect = {\n"
                "\t\t\tadd_political_power = -400\n"
                "\t\t\tdecrease_corruption = yes\n"
                "\t\t}\n"
            ),
            "\thas_idea = corruption_level_02\n",
        ),
        [("foo.1.a", 6)],
    ),
    "idea mutation and decrease in sibling wrappers stay ordered": (
        _event(
            _option(
                "\t\thidden_effect = { swap_ideas = { "
                "remove_idea = corruption_level_02 "
                "add_idea = corruption_level_01 } }\n"
                "\t\thidden_effect = {\n"
                "\t\t\tadd_political_power = -400\n"
                "\t\t\tdecrease_corruption = yes\n"
                "\t\t}\n"
            ),
            "\thas_idea = corruption_level_02\n",
        ),
        [("foo.1.a", 6)],
    ),
    "option trigger bound is invalidated before nested ROOT effects": (
        _event(
            _option(
                "\t\tswap_ideas = { remove_idea = corruption_level_02 "
                "add_idea = corruption_level_01 }\n"
                "\t\tROOT = { add_political_power = -400 "
                "decrease_corruption = yes }\n",
                _MIN_GUARD,
            )
        ),
        [("foo.1.a", 3)],
    ),
    "nested limit is invalidated by a mutation before its decrease": (
        _event(
            _option(
                "\t\tif = {\n"
                "\t\t\tlimit = { NOT = { has_idea = corruption_level_01 } }\n"
                "\t\t\tswap_ideas = { remove_idea = corruption_level_02 "
                "add_idea = corruption_level_01 }\n"
                "\t\t\tadd_political_power = -400\n"
                "\t\t\tdecrease_corruption = yes\n"
                "\t\t}\n"
            )
        ),
        _FINDING,
    ),
    "fresh nested guard remains valid after outer mutation": (
        _event(
            _option(
                "\t\tswap_ideas = { remove_idea = corruption_level_02 "
                "add_idea = corruption_level_01 }\n"
                "\t\tif = { limit = { NOT = { has_idea = corruption_level_01 } } "
                "add_political_power = -400 decrease_corruption = yes }\n"
            )
        ),
        [],
    ),
    "option trigger is checked after immediate corruption changes": (
        _event(
            _option(_PP_COST + _DECREASE, "\t\thas_idea = corruption_level_06\n"),
            "\thas_idea = corruption_level_07\n",
        ).replace(
            _option(_PP_COST + _DECREASE, "\t\thas_idea = corruption_level_06\n"),
            "\timmediate = { decrease_corruption = yes }\n"
            + _option(_PP_COST + _DECREASE, "\t\thas_idea = corruption_level_06\n"),
        ),
        [],
    ),
    "unrelated idea swap preserves the event trigger bound": (
        _event(
            _option(
                "\t\tswap_ideas = { remove_idea = foo_old add_idea = foo_new }\n"
                + _PP_COST
                + _DECREASE
            ),
            "\thas_idea = corruption_level_02\n",
        ),
        [],
    ),
    "nested guard encloses both effects": (_event(_option(_NESTED_GUARD)), []),
    "guarded pair cannot hide additional unguarded operations": (
        _event(_option(_NESTED_GUARD + _PP_COST + _DECREASE)),
        _FINDING,
    ),
    "every relevant operation has its own nested guard": (
        _event(_option(_NESTED_GUARD + _NESTED_GUARD)),
        [],
    ),
    "nested guard around decrease alone leaves PP charged": (
        _event(
            _option(
                _PP_COST + "\t\tif = {\n"
                "\t\t\tlimit = { NOT = { has_idea = corruption_level_01 } }\n"
                "\t\t\tdecrease_corruption = yes\n"
                "\t\t}\n"
            )
        ),
        _FINDING,
    ),
    "decrease without a PP charge is free": (_event(_option(_DECREASE)), []),
    "positive PP and decrease do not charge": (
        _event(_option("\t\tadd_political_power = 150\n" + _DECREASE)),
        [],
    ),
    "zero PP and decrease do not charge": (
        _event(_option("\t\tadd_political_power = -0.00\n" + _DECREASE)),
        [],
    ),
    "variable payload does not execute a PP effect": (
        _event(
            _option("\t\tset_variable = { add_political_power = -400 }\n" + _DECREASE)
        ),
        [],
    ),
    "comments and quoted logs cannot invent a PP cost": (
        _event(
            _option(
                "#add_political_power = -400\n"
                '\t\tlog = "add_political_power = -400"\n' + _DECREASE
            )
        ),
        [],
    ),
    "comments and quoted logs cannot invent a corruption call": (
        _event(
            _option(
                _PP_COST + "#decrease_corruption = yes\n"
                '\t\tlog = "decrease_corruption = yes"\n'
            )
        ),
        [],
    ),
    "disabled if effects do not execute": (
        _event(
            _option(
                "\t\tif = { limit = { always = no }\n"
                + _PP_COST
                + _DECREASE
                + "\t\t}\n"
            )
        ),
        [],
    ),
    "zero chance effects do not execute": (
        _event(
            _option("\t\trandom = { chance = 0\n" + _PP_COST + _DECREASE + "\t\t}\n")
        ),
        [],
    ),
    "matching literal receiver scope can prove the guard": (
        _event(
            _option(_PP_COST + _DECREASE),
            "\t\ttag = GER\n\t\tGER = { NOT = { has_idea = corruption_level_01 } }\n",
        ),
        [],
    ),
    "foreign scope is not the choosing country": (
        _event(
            _option(_PP_COST + "\t\tGER = { decrease_corruption = yes }\n"),
            "\t\ttag = FRA\n",
        ),
        [],
    ),
    "foreign scope counts only explicit ROOT re-entry": (
        _event(
            _option(
                "\t\tGER = { decrease_corruption = yes "
                "ROOT = { add_political_power = -400 "
                "decrease_corruption = yes } }\n"
            ),
            "\ttag = FRA\n",
        ),
        [("foo.1.a", 6)],
    ),
    "numeric state scope does not execute for the choosing country": (
        _event(_option(_PP_COST + "\t\t123 = { decrease_corruption = yes }\n")),
        [],
    ),
    "numeric state scope does not invalidate the event trigger bound": (
        _event(
            _option(_PP_COST + _DECREASE),
            "\thas_idea = corruption_level_02\n",
        ).replace(
            _option(_PP_COST + _DECREASE),
            "\timmediate = { 123 = { decrease_corruption = yes } }\n"
            + _option(_PP_COST + _DECREASE),
        ),
        [],
    ),
    "numeric immediate scope preserves explicit ROOT corruption effects": (
        _event(
            _option(_PP_COST + _DECREASE),
            "\thas_idea = corruption_level_02\n",
        ).replace(
            _option(_PP_COST + _DECREASE),
            "\timmediate = { 123 = { ROOT = { decrease_corruption = yes } } }\n"
            + _option(_PP_COST + _DECREASE),
        ),
        [("foo.1.a", 7)],
    ),
    "numeric option scope preserves explicit ROOT PP and corruption effects": (
        _event(
            _option(
                "\t\t123 = { ROOT = { add_political_power = -400 "
                "decrease_corruption = yes } }\n"
            )
        ),
        _FINDING,
    ),
    "random list numeric weights execute in the choosing country": (
        _event(
            _option(
                _PP_COST + "\t\trandom_list = { 100 = { decrease_corruption = yes } }\n"
            )
        ),
        _FINDING,
    ),
    "ROOT scope is the choosing country": (
        _event(
            _option(
                "\t\tROOT = {\n"
                "\t\t\tadd_political_power = -400\n"
                "\t\t\tdecrease_corruption = yes\n"
                "\t\t}\n"
            )
        ),
        [("foo.1.a", 3)],
    ),
}


@pytest.mark.parametrize(
    "text, expected",
    _SCAN_CASES.values(),
    ids=_SCAN_CASES.keys(),
)
def test_corruption_pp_cost_scan(text, expected):
    assert V.find_corruption_pp_cost_options(text) == expected


_VALIDATOR_SOURCES = {
    "plain effects": _event(_option(_PP_COST + _DECREASE)),
    "hash inside a log preserves following effects": _event(
        _option('\t\tlog = "# } quoted text"\n' + _PP_COST + _DECREASE)
    ),
}


@pytest.mark.parametrize(
    "source", _VALIDATOR_SOURCES.values(), ids=_VALIDATOR_SOURCES.keys()
)
def test_validator_reports_warning_for_events_and_skips_decisions(tmp_path, source):
    write_tree(
        tmp_path,
        {
            "events/Ev.txt": source,
            "common/decisions/Ev.txt": _event(_option(_PP_COST + _DECREASE)),
        },
    )
    validator = build_validator(V.Validator, tmp_path, check_corruption_pp_costs=True)

    validator.validate_corruption_pp_cost()

    assert [
        (issue.category, issue.severity, issue.file, issue.line)
        for issue in validator._issues
    ] == [("event-corruption-pp-cost", "warning", "events/Ev.txt", 3)]


def test_check_is_off_without_the_flag(tmp_path):
    write_tree(tmp_path, {"events/Ev.txt": _event(_option(_PP_COST + _DECREASE))})
    validator = build_validator(V.Validator, tmp_path)

    validator.validate_corruption_pp_cost()

    assert not validator._issues


def test_cli_flag_is_registered():
    parser = argparse.ArgumentParser()
    V._add_extra_args(parser)

    assert parser.parse_args([]).check_corruption_pp_costs is False
    assert (
        parser.parse_args(["--check-corruption-pp-costs"]).check_corruption_pp_costs
        is True
    )
