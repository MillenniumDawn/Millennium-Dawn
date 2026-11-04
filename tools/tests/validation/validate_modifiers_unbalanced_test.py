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
