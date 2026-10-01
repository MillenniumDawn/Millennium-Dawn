"""Event options whose flat ai_chance ignores what the option costs (issue #5096)."""

import argparse

import pytest
from shared.suite import write_under_str as _write
from validate_events import Validator, _add_extra_args, find_cost_blind_options

_FLAT = "\t\tai_chance = { base = 5 }\n"
_AWARE = (
    "\t\tai_chance = {\n"
    "\t\t\tbase = 10\n"
    "\t\t\tmodifier = { factor = 0.25 has_political_power < 25 }\n"
    "\t\t}\n"
)
_PP_COST = "\t\tadd_political_power = -50\n"


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


def _validator(tmp_path, **kwargs):
    return Validator(mod_path=str(tmp_path), use_colors=False, workers=1, **kwargs)


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
    assert find_cost_blind_options(_two_options(_PP_COST + _AWARE)) == []


def test_modifier_on_another_option_does_not_cover_the_costed_one():
    text = _event(
        _option("foo.1.a", _PP_COST + _FLAT),
        _option("foo.1.b", _AWARE),
    )
    assert [name for name, _line, _costs in find_cost_blind_options(text)] == [
        "foo.1.a"
    ]


def test_single_option_event_is_clean():
    assert find_cost_blind_options(_event(_option("foo.1.a", _PP_COST + _FLAT))) == []


def test_missing_ai_chance_is_flat_and_reports_the_option_line():
    assert find_cost_blind_options(_two_options(_PP_COST)) == [
        ("foo.1.a", 5, "political power")
    ]


@pytest.mark.parametrize(
    ("effects", "costs"),
    [
        (
            "\t\tset_temp_variable = { treasury_change = -15.00 }\n"
            "\t\tmodify_treasury_effect = yes\n",
            "treasury",
        ),
        ("\t\tsmall_expenditure = yes\n", "treasury"),
        ("\t\tmedium_expenditure = yes\n", "treasury"),
        ("\t\tlarge_expenditure = yes\n", "treasury"),
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
            "\t\tlarge_expenditure = yes\n" + _PP_COST + "\t\tadd_stability = -0.02\n",
            "treasury, political power, stability",
        ),
    ],
)
def test_cost_kinds_are_detected(effects, costs):
    found = find_cost_blind_options(_two_options(effects + _FLAT))
    assert [(name, kinds) for name, _line, kinds in found] == [("foo.1.a", costs)]


@pytest.mark.parametrize(
    "effects",
    [
        "\t\tadd_political_power = 50\n",
        "\t\tadd_stability = 0.02\n",
        "\t\tset_temp_variable = { treasury_change = 15 }\n"
        "\t\tmodify_treasury_effect = yes\n",
        "\t\tset_temp_variable = { treasury_change = -15 }\n",
        "\t\tFROM = { add_political_power = -50 }\n",
        "\t\tevery_other_country = { add_stability = -0.02 }\n",
        '\t\tlog = "add_political_power = -50"\n',
    ],
)
def test_not_a_cost_to_the_choosing_country(effects):
    assert find_cost_blind_options(_two_options(effects + _FLAT)) == []


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
    assert find_cost_blind_options(text) == [("foo.1.b", 17, "stability")]
