"""Airborne template paradrop check in validate_oob_units.py.

One sub-unit without `can_be_parachuted = yes` stops its whole division from
paradropping, so an airborne-named division_template must not reference one.
"""

import pytest
import validate_oob_units as V
from validate_oob_units import Validator

_UNITS = """sub_units = {
\tPara_Inf_Bat = {
\t\tcan_be_parachuted = yes
\t}
\tPara_Support_Comp = {
\t\tcan_be_parachuted = yes
\t}
\tSP_Arty_Bat = {
\t\tcan_be_parachuted = no
\t}
}
"""


def _template(name, unit):
    return (
        "division_template = {\n"
        f'\tname = "{name}"\n'
        "\tregiments = {\n"
        "\t\tPara_Inf_Bat = { x = 0 y = 0 }\n"
        "\t}\n"
        "\tsupport = {\n"
        f"\t\t{unit} = {{ x = 0 y = 0 }}\n"
        "\t}\n"
        "}\n"
    )


def _check(tmp_path, name, unit):
    units = tmp_path / "common" / "units"
    units.mkdir(parents=True)
    (units / "MD_land_units.txt").write_text(_UNITS, encoding="utf-8")
    history = tmp_path / "history" / "units"
    history.mkdir(parents=True)
    (history / "SWE_2000.txt").write_text(_template(name, unit), encoding="utf-8")
    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator._build_canonical_units()
    validator.validate_airborne_templates()
    return validator


def test_airborne_template_with_non_parachutable_unit_is_flagged(tmp_path):
    validator = _check(tmp_path, "Parachute Brigade", "SP_Arty_Bat")

    assert validator.warnings_found == 1
    assert validator.errors_found == 0
    issue = validator._issues[0]
    assert issue.severity == "warning"
    assert issue.category == "airborne-template-not-parachutable"
    assert issue.file == "history/units/SWE_2000.txt"
    assert issue.line == 7
    assert "'Parachute Brigade' (line 1) uses 'SP_Arty_Bat'" in issue.message


def test_airborne_template_with_only_parachutable_units_is_clean(tmp_path):
    validator = _check(tmp_path, "Parachute Brigade", "Para_Support_Comp")
    assert validator._issues == []


def test_non_airborne_template_with_the_same_unit_is_not_flagged(tmp_path):
    validator = _check(tmp_path, "Separate Artillery Brigade", "SP_Arty_Bat")
    assert validator._issues == []


def test_allowlisted_air_assault_template_is_not_flagged(tmp_path, monkeypatch):
    monkeypatch.setattr(V, "_AIR_ASSAULT_TEMPLATES", frozenset({"Airborne Brigade"}))
    validator = _check(tmp_path, "Airborne Brigade", "SP_Arty_Bat")
    assert validator._issues == []


@pytest.mark.parametrize(
    "name",
    ["Parachute Brigade", "Para Commando Unit", "Airborne Division", "Brigada VDV"],
)
def test_configured_patterns_match_airborne_names(name):
    assert any(pattern.search(name) for pattern in V._AIRBORNE_NAME_RES)


def test_configured_patterns_skip_names_that_only_contain_para():
    assert not any(
        pattern.search("Separate Infantry BDE") for pattern in V._AIRBORNE_NAME_RES
    )
