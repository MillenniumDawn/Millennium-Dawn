"""Tests for the opt-in --unbalanced-modifiers balance check (issue #4370).

Caps apply per direct `key = number` assignment: ROI over 3%, productivity
growth over 25%, game-start policy rate over 30, game-start inflation over 50%.
"""

import pytest
import validate_modifiers as vm
from shared.suite import checks_called_by_run
from shared.suite import write_under as _write
from validate_modifiers import Validator, _scan_numeric_modifier_entries
from validator_common import Severity


def _validator(tmp_path, enabled=True):
    return Validator(
        str(tmp_path), use_colors=False, workers=1, unbalanced_modifiers=enabled
    )


def _categories(validator):
    return [issue.category for issue in validator._issues]


def test_roi_over_cap_scanned():
    entries = _scan_numeric_modifier_entries(
        "modifier = {\n\treturn_on_investment_modifier = 0.05\n}\n"
    )
    assert entries == [("return_on_investment_modifier", 0.05, 2, "modifier")]


def test_variable_reference_ignored():
    entries = _scan_numeric_modifier_entries(
        "us_economic_policies = {\n\tproductivity_growth_modifier = econ_productivity\n}\n"
    )
    assert entries == []


def test_single_line_block_harvested():
    entries = _scan_numeric_modifier_entries("set_variable = { cb_policy_rate = 3 }\n")
    assert entries == [("cb_policy_rate", 3.0, 1, "set_variable")]


def test_owner_is_innermost_block():
    text = (
        "ideas = {\n"
        "\tcountry = {\n"
        "\t\ttest_idea = {\n"
        "\t\t\tmodifier = {\n"
        "\t\t\t\treturn_on_investment_modifier = 0.10\n"
        "\t\t\t}\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )
    entries = _scan_numeric_modifier_entries(text)
    assert entries == [("return_on_investment_modifier", 0.10, 5, "modifier")]


def test_roi_end_to_end(tmp_path, monkeypatch):
    _write(
        tmp_path,
        "common/ideas/test.txt",
        "ideas = {\n\tcountry = {\n\t\tbig = {\n"
        "\t\t\tmodifier = {\n\t\t\t\treturn_on_investment_modifier = 0.10\n"
        "\t\t\t}\n\t\t}\n"
        "\t\tsmall = {\n"
        "\t\t\tmodifier = {\n\t\t\t\treturn_on_investment_modifier = 0.03\n"
        "\t\t\t}\n\t\t}\n\t}\n}\n",
    )
    validator = _validator(tmp_path)
    validator.validate_unbalanced_modifiers()
    roi = [i for i in validator._issues if i.category == "unbalanced-roi"]
    assert len(roi) == 1
    assert "0.1" in roi[0].message

    monkeypatch.setattr(
        vm,
        "_UNBALANCED_ROI_EXCEPTIONS",
        frozenset({"modifier::return_on_investment_modifier"}),
    )
    validator = _validator(tmp_path)
    validator.validate_unbalanced_modifiers()
    assert "unbalanced-roi" not in _categories(validator)


def test_productivity_variants_end_to_end(tmp_path):
    _write(
        tmp_path,
        "common/dynamic_modifiers/test.txt",
        "good = {\n\tstate_productivity_growth_modifier = 0.25\n}\n"
        "bad_country = {\n\tcountry_productivity_growth_modifier = 0.30\n}\n"
        "bad_plain = {\n\tproductivity_growth_modifier = 0.50\n}\n"
        "penalty = {\n\tstate_productivity_growth_modifier = -0.25\n}\n",
    )
    validator = _validator(tmp_path)
    validator.validate_unbalanced_modifiers()
    prod = [i for i in validator._issues if i.category == "unbalanced-productivity"]
    assert len(prod) == 2

    validator.validate_excessive_modifiers()
    assert "excessive-modifier-over-30-percent" not in _categories(validator)


def test_history_start_values_end_to_end(tmp_path):
    _write(
        tmp_path,
        "history/countries/ABC - Test.txt",
        "set_variable = { cb_policy_rate = 31 }\n"
        "set_variable = { inflation_rate_var = 0.75 }\n",
    )
    _write(
        tmp_path,
        "history/countries/DEF - Fine.txt",
        "set_variable = { cb_policy_rate = 8 }\n"
        "set_variable = { inflation_rate_var = 0.05 }\n",
    )
    validator = _validator(tmp_path)
    validator.validate_unbalanced_modifiers()
    cats = _categories(validator)
    assert cats.count("unbalanced-policy-rate") == 1
    assert cats.count("unbalanced-inflation") == 1


def test_history_inflation_hard_cap_always_on(tmp_path):
    _write(
        tmp_path,
        "history/countries/ABC - Test.txt",
        "set_variable = { inflation_rate_var = 1.1 }\n",
    )
    _write(
        tmp_path,
        "history/countries/DEF - Fine.txt",
        "set_variable = { inflation_rate_var = 0.99 }\n",
    )
    validator = _validator(tmp_path, enabled=False)
    validator.validate_history_inflation_hard_cap()
    hits = [i for i in validator._issues if i.category == "history-inflation-over-one"]
    assert len(hits) == 1
    assert "1.1" in hits[0].message


def test_flag_off_reports_nothing(tmp_path):
    _write(
        tmp_path,
        "common/ideas/test.txt",
        "ideas = {\n\tcountry = {\n\t\tbig = {\n"
        "\t\t\tmodifier = {\n\t\t\t\treturn_on_investment_modifier = 0.10\n"
        "\t\t\t}\n\t\t}\n\t}\n}\n",
    )
    _write(
        tmp_path,
        "history/countries/ABC - Test.txt",
        "set_variable = { inflation_rate_var = 2.5 }\n",
    )
    validator = _validator(tmp_path, enabled=False)
    validator.validate_unbalanced_modifiers()
    assert [c for c in _categories(validator) if c.startswith("unbalanced")] == []


_INCOME_KEYS = (
    "tax_gain_multiplier_modifier",
    "corporate_tax_income_multiplier_modifier",
    "population_tax_income_multiplier_modifier",
    "healthcare_income_multiplier_modifier",
    "infrastructure_tax_gain_multiplier_modifier",
    "civilian_industry_tax_modifier",
    "military_industry_tax_modifier",
    "agriculture_tax_modifier",
    "dockyard_income_tax_modifier",
    "office_park_income_tax_modifier",
    "agriculture_district_income_tax_modifier",
    "microchip_plant_income_tax_modifier",
    "composite_plant_income_tax_modifier",
    "synthetic_refinery_income_tax_modifier",
    "resource_export_multiplier_modifier",
    "oil_export_multiplier_modifier",
    "steel_export_multiplier_modifier",
    "aluminium_export_multiplier_modifier",
    "tungsten_export_multiplier_modifier",
    "chromium_export_multiplier_modifier",
    "rubber_export_multiplier_modifier",
    "microchip_export_multiplier_modifier",
    "composite_export_multiplier_modifier",
    "international_market_income_modifier",
)


@pytest.mark.parametrize("key", _INCOME_KEYS)
def test_income_modifier_families_warn_without_the_opt_in_flag(tmp_path, key):
    _write(
        tmp_path,
        "common/ideas/test.txt",
        f"idea = {{ modifier = {{ {key} = 0.5 }} }}\n",
    )
    validator = _validator(tmp_path, enabled=False)
    validator.validate_income_modifiers()
    assert [(i.category, i.severity, i.line) for i in validator._issues] == [
        ("income-over-25-percent", Severity.WARNING, 1)
    ]
    message = validator._issues[0].message
    assert f"{key} = 0.5" in message
    assert "+50%" in message
    assert "+25%" in message
    assert f"'idea::{key}'" in message


_TAX = "tax_gain_multiplier_modifier"

# source, relative path, expected warning lines
_INCOME_CASES = {
    "at threshold": (
        f"idea = {{ modifier = {{ {_TAX} = 0.25 }} }}",
        "common/ideas/test.txt",
        [],
    ),
    "just above threshold": (
        f"idea = {{ modifier = {{ {_TAX} = 0.25001 }} }}",
        "common/ideas/test.txt",
        [1],
    ),
    "penalty": (
        f"idea = {{ modifier = {{ {_TAX} = -0.5 }} }}",
        "common/ideas/test.txt",
        [],
    ),
    "leading decimal": (
        f"idea = {{ modifier = {{ {_TAX} = .3 }} }}",
        "common/ideas/test.txt",
        [1],
    ),
    "explicit positive sign": (
        f"idea = {{ modifier = {{ {_TAX} = +0.3 }} }}",
        "common/ideas/test.txt",
        [1],
    ),
    "variable reference": (
        f"idea = {{ modifier = {{ {_TAX} = tax_bonus }} }}",
        "common/ideas/test.txt",
        [],
    ),
    "quoted number": (
        f'idea = {{ modifier = {{ {_TAX} = "0.5" }} }}',
        "common/ideas/test.txt",
        [],
    ),
    "not a modifier assignment": (
        f"focus = {{ completion_reward = {{ set_variable = {{ {_TAX} = 0.5 }} }} }}",
        "common/national_focus/test.txt",
        [],
    ),
    "unrelated modifier": (
        "idea = { modifier = { stability_factor = 0.5 } }",
        "common/ideas/test.txt",
        [],
    ),
    "stacked sources below threshold": (
        f"a = {{ modifier = {{ {_TAX} = 0.2 }} }}\nb = {{ modifier = {{ {_TAX} = 0.2 }} }}",
        "common/ideas/test.txt",
        [],
    ),
    "comment and quoted braces": (
        f'# " }} {_TAX} = 0.5\nidea = {{\n log = "{{ \\" # {_TAX} = 0.8"\n modifier = {{\n  {_TAX} = 0.5 # }} {_TAX} = 0.9\n }}\n}}',
        "common/ideas/test.txt",
        [5],
    ),
    "multiline value and CRLF": (
        f"idea = {{\r\n modifier = {{\r\n {_TAX} =\r\n 0.5\r\n }}\r\n}}",
        "common/ideas/test.txt",
        [3],
    ),
    "direct dynamic modifier": (
        f"bonus = {{\n {_TAX} = 0.5\n}}",
        "common/dynamic_modifiers/test.txt",
        [2],
    ),
    "direct static modifier": (
        f"bonus = {{ {_TAX} = 0.5 }}",
        "common/modifiers/test.txt",
        [1],
    ),
    "direct leader trait": (
        f"leader_traits = {{ bonus = {{ {_TAX} = 0.5 }} }}",
        "common/country_leader/test.txt",
        [1],
    ),
    "direct unit leader trait": (
        f"leader_traits = {{ bonus = {{ {_TAX} = 0.5 }} }}",
        "common/unit_leader/test.txt",
        [1],
    ),
    "country modifier block": (
        f"idea = {{ country_modifier = {{ {_TAX} = 0.5 }} }}",
        "common/ideas/test.txt",
        [1],
    ),
    "state modifier block": (
        f"idea = {{ state_modifier = {{ {_TAX} = 0.5 }} }}",
        "common/ideas/test.txt",
        [1],
    ),
    "two bonuses on one line": (
        f"idea = {{ modifier = {{ {_TAX} = 0.5 corporate_tax_income_multiplier_modifier = 0.3 }} }}",
        "common/ideas/test.txt",
        [1, 1],
    ),
    "empty file": ("", "common/ideas/test.txt", []),
}


@pytest.mark.parametrize("source,path,lines", _INCOME_CASES.values(), ids=_INCOME_CASES)
def test_income_modifier_warnings(tmp_path, source, path, lines):
    _write(tmp_path, path, source)
    validator = _validator(tmp_path, enabled=False)
    validator.validate_income_modifiers()
    assert [(i.file.replace("\\", "/"), i.line) for i in validator._issues] == [
        (path, line) for line in lines
    ]
    assert all(i.severity == Severity.WARNING for i in validator._issues)


def test_income_exception_skips_only_its_owner(tmp_path, monkeypatch):
    monkeypatch.setattr(vm, "_INCOME_EXCEPTIONS", frozenset({f"a::{_TAX}"}))
    _write(
        tmp_path,
        "common/ideas/test.txt",
        f"a = {{ modifier = {{ {_TAX} = 0.5 }} }}\nb = {{ modifier = {{ {_TAX} = 0.5 }} }}",
    )
    validator = _validator(tmp_path, enabled=False)
    validator.validate_income_modifiers()
    assert [i.line for i in validator._issues] == [2]


def test_modifier_run_calls_every_check(tmp_path, monkeypatch):
    validator = _validator(tmp_path, enabled=False)
    called, checks = checks_called_by_run(validator, monkeypatch)
    assert called == checks


def _idea(name, key, value):
    block = f"{name} = {{ modifier = {{ {key} = {value} }} }}"
    return f"ideas = {{ country = {{ {block} }} }}\n"


_WEEKLY_CASES = {
    "flat over cap": ("stability_weekly", "0.06", 1),
    "flat at cap": ("stability_weekly", "0.05", 0),
    "flat penalty": ("war_support_weekly", "-0.06", 0),
    "factor over cap": ("stability_weekly_factor", "0.3", 1),
    "factor penalty over cap": ("war_support_weekly_factor", "-0.3", 1),
    "factor at cap": ("stability_weekly_factor", "0.25", 0),
}


@pytest.mark.parametrize("key,value,count", _WEEKLY_CASES.values(), ids=_WEEKLY_CASES)
def test_weekly_stability_war_support_caps(tmp_path, key, value, count):
    _write(tmp_path, "common/ideas/test.txt", _idea("test_idea", key, value))
    validator = _validator(tmp_path, enabled=False)
    validator.validate_weekly_stability_war_support()
    assert [(i.category, i.severity) for i in validator._issues] == [
        ("weekly-stability-war-support-over-cap", Severity.WARNING)
    ] * count
    if count:
        assert "'test_idea'" in validator._issues[0].message


_EXCESSIVE_CASES = {
    "bonus over cap": ("research_speed_factor", "0.31", 1),
    "bonus at cap": ("research_speed_factor", "0.30", 0),
    "penalty": ("research_speed_factor", "-0.5", 0),
    "cost bonus": ("corruption_cost_factor", "-0.4", 1),
    "cost bonus at cap": ("corruption_cost_factor", "-0.30", 0),
    "cost penalty": ("corruption_cost_factor", "0.4", 0),
    "tax change penalty": ("tax_rate_change_multiplier_modifier", "0.5", 0),
    "tax change bonus": ("tax_rate_change_multiplier_modifier", "-0.5", 1),
    "tax change bonus at cap": ("tax_rate_change_multiplier_modifier", "-0.3", 0),
    "expected-style key without definition": ("expected_welfare_modifier", "-0.4", 1),
    "listed malus key penalty": ("consumer_goods_factor", "0.4", 0),
    "listed malus key bonus": ("consumer_goods_factor", "-0.4", 1),
    "fuel suffix penalty": ("army_fuel_consumption_factor", "0.4", 0),
    "fuel suffix bonus": ("army_fuel_consumption_factor", "-0.4", 1),
    "worker requirement penalty": ("civ_facs_worker_requirement_modifier", "0.4", 0),
    "worker requirement bonus": ("civ_facs_worker_requirement_modifier", "-0.4", 1),
    "number-typed key": ("interest_rate_multiplier_modifier", "5", 0),
    "ai weight": ("ai_focus_aggressive_factor", "5", 0),
    "income key": (_TAX, "0.5", 0),
    "weekly key": ("stability_weekly_factor", "0.5", 0),
    "productivity key, opt-in check off": ("productivity_growth_modifier", "0.5", 1),
}


@pytest.mark.parametrize(
    "key,value,count", _EXCESSIVE_CASES.values(), ids=_EXCESSIVE_CASES
)
def test_excessive_modifiers(tmp_path, key, value, count):
    _write(tmp_path, "common/ideas/test.txt", _idea("test_idea", key, value))
    validator = _validator(tmp_path, enabled=False)
    validator.validate_excessive_modifiers()
    assert [(i.category, i.severity) for i in validator._issues] == [
        ("excessive-modifier-over-30-percent", Severity.WARNING)
    ] * count


@pytest.mark.parametrize(
    "key,value",
    [
        ("state_renewable_capacity_factor_modifier", "0.55"),
        ("expected_mil_modifier", "-4"),
        ("expected_police_modifier", "-3"),
        ("expected_healthcare_modifier", "-2"),
    ],
)
@pytest.mark.parametrize("value_type,count", [("number", 0), ("percentage", 1)])
@pytest.mark.parametrize("source", ["idea", "state decision"])
def test_excessive_modifiers_respect_definition_units(
    tmp_path, key, value, value_type, count, source
):
    _write(
        tmp_path,
        "common/modifier_definitions/test.txt",
        f"{key} = {{\n\t# value_type = number\n\tvalue_type = {value_type}\n}}\n",
    )
    if source == "idea":
        _write(tmp_path, "common/ideas/test.txt", _idea("test_idea", key, value))
    else:
        _write(
            tmp_path,
            "common/decisions/test.txt",
            "test_category = { test_decision = { complete_effect = { 669 = {\n"
            f"add_state_modifier = {{ modifier = {{ {key} = {value} }} }}\n"
            "} } } }\n",
        )
    validator = _validator(tmp_path, enabled=False)
    validator.validate_excessive_modifiers()
    assert _categories(validator) == ["excessive-modifier-over-30-percent"] * count


_GRANT_CASES = {
    "timed idea only": ("add_timed_idea = { idea = test_idea days = 90 }", 0),
    "timed and permanent idea": (
        "add_timed_idea = { idea = test_idea days = 90 }\nadd_ideas = test_idea",
        1,
    ),
    "idea in add_ideas list": ("add_ideas = { other_idea test_idea }", 1),
    "idea via swap_ideas": (
        "swap_ideas = { remove_idea = other_idea add_idea = test_idea }",
        1,
    ),
    "never granted": ("", 1),
}


@pytest.mark.parametrize("grant,count", _GRANT_CASES.values(), ids=_GRANT_CASES)
def test_timed_only_ideas_are_skipped(tmp_path, grant, count):
    _write(
        tmp_path,
        "common/ideas/test.txt",
        _idea("test_idea", "research_speed_factor", "0.5"),
    )
    _write(
        tmp_path,
        "common/national_focus/test.txt",
        f"focus = {{ completion_reward = {{ {grant} }} }}\n",
    )
    validator = _validator(tmp_path, enabled=False)
    validator.validate_excessive_modifiers()
    assert len(validator._issues) == count


_TIMED_DM = "add_dynamic_modifier = { modifier = test_dm days = 30 }"
_UNTIMED_DM = "add_dynamic_modifier = { modifier = test_dm }"

# grant file, grant source, expected warning count
_DYNAMIC_GRANT_CASES = {
    "timed only": ("events/test.txt", _TIMED_DM, 0),
    "untimed": ("events/test.txt", _UNTIMED_DM, 1),
    "timed and untimed": ("events/test.txt", f"{_TIMED_DM}\n{_UNTIMED_DM}", 1),
    "timed only in history": ("history/countries/ABC - Test.txt", _TIMED_DM, 0),
    "untimed in history": ("history/countries/ABC - Test.txt", _UNTIMED_DM, 1),
}


@pytest.mark.parametrize(
    "path,grant,count", _DYNAMIC_GRANT_CASES.values(), ids=_DYNAMIC_GRANT_CASES
)
def test_timed_only_dynamic_modifiers_are_skipped(tmp_path, path, grant, count):
    _write(
        tmp_path,
        "common/dynamic_modifiers/test.txt",
        "test_dm = {\n\tstability_weekly = 0.1\n}\n",
    )
    _write(tmp_path, path, f"immediate = {{ {grant} }}\n")
    validator = _validator(tmp_path, enabled=False)
    validator.validate_weekly_stability_war_support()
    assert len(validator._issues) == count
    if count:
        assert "'test_dm'" in validator._issues[0].message
