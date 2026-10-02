"""Tests for the opt-in --unbalanced-modifiers balance check (issue #4370).

Caps apply per direct `key = number` assignment: ROI over 3%, productivity
growth over 25%, game-start policy rate over 20, game-start inflation over 50%.
"""

import validate_modifiers as vm
from validate_modifiers import Validator, _scan_numeric_modifier_entries


def _write(tmp_path, rel, content):
    path = tmp_path / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


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
        "set_variable = { cb_policy_rate = 25 }\n"
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
