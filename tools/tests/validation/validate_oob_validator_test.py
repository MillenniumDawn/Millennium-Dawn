"""Validator-level tests for validate_oob_units.py.

Each pass is wired into `run_validations`, so these drive the passes the focused
namelist, variant and create_unit suites leave untouched: unit references in
OOB files, division_names_group resolution, air-wing template loc keys, and the
OOB/production equipment reference checks.
"""

from validate_oob_units import Validator

_UNITS = """sub_units = {
\tL_Inf_Bat = {
\t\tmap_icon_category = infantry
\t\tneed = {
\t\t\tinfantry_weapons = 100
\t\t}
\t}
}
"""

_EQUIPMENT = """equipments = {
\tship_hull_frigate = {
\t\tis_archetype = yes
\t\ttype = { naval }
\t\tmodule_slots = {
\t\t}
\t}
\tfrigate_hull_2 = {
\t\tarchetype = ship_hull_frigate
\t\tmodule_slots = inherit
\t}
}
"""

_VARIANT = """create_equipment_variant = {
\tname = "Naresuan Class"
\ttype = frigate_hull_2
}
"""


def _write(tmp_path, relative, body):
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _validator(tmp_path):
    return Validator(mod_path=str(tmp_path), use_colors=False, workers=1)


def _messages(validator):
    return [issue.message for issue in validator._issues]


def _ship_oob(version_name):
    return (
        "units = {\n"
        "\tfleet = {\n"
        '\t\tname = "Home Fleet"\n'
        "\t\tnaval_base = 9999\n"
        "\t\ttask_force = {\n"
        '\t\t\tname = "1st Squadron"\n'
        "\t\t\tship = {\n"
        "\t\t\t\tequipment = { frigate_hull_2 = { amount = 1 owner = SWE "
        f'creator = SWE version_name = "{version_name}" }} }}\n'
        "\t\t\t}\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )


def test_unknown_unit_in_an_oob_file_is_reported(tmp_path):
    _write(tmp_path, "common/units/MD_land_units.txt", _UNITS)
    _write(
        tmp_path,
        "history/units/SWE_1990.txt",
        "division_template = {\n"
        '\tname = "Infantry Brigade"\n'
        "\tregiments = {\n"
        "\t\tL_Inf_Bt = { x = 0 y = 0 }\n"
        "\t}\n"
        "}\n",
    )
    validator = _validator(tmp_path)
    validator._build_canonical_units()
    validator.validate_unit_references()

    assert validator.errors_found == 1
    assert _messages(validator) == [
        "SWE_1990.txt: unknown unit 'L_Inf_Bt' (did you mean 'L_Inf_Bat'?)"
    ]


def test_unknown_division_names_group_is_reported(tmp_path):
    _write(
        tmp_path,
        "common/units/names_divisions/SWE.txt",
        "SWE_ARM = {\n\tname = NAME_SWE_ARM\n}\n",
    )
    _write(
        tmp_path,
        "history/units/SWE_1990.txt",
        "units = {\n"
        "\tdivision = {\n"
        "\t\tdivision_names_group = SWE_ARM\n"
        "\t\tdivision_names_group = SWE_MISSING\n"
        "\t}\n"
        "}\n",
    )
    validator = _validator(tmp_path)
    validator.validate_division_names_group_references()

    assert validator.errors_found == 1
    assert _messages(validator) == ["unknown division_names_group 'SWE_MISSING'"]
    assert validator._issues[0].line == 4


def test_air_wing_template_without_a_loc_key_warns(tmp_path):
    _write(tmp_path, "common/units/names/empty.txt", "")
    _write(
        tmp_path,
        "common/units/names/00_SWE_names.txt",
        "SWE = {\n\tair_wing_names_template = AIR_WING_NAME_SWE\n}\n",
    )
    validator = _validator(tmp_path)
    validator.validate_air_wing_names_template_loc()

    assert validator.warnings_found == 1
    assert validator._issues[0].category == "air-wing-template-loc"
    assert "AIR_WING_NAME_SWE" in validator._issues[0].message


def test_air_wing_template_with_a_loc_key_is_clean(tmp_path):
    _write(
        tmp_path,
        "common/units/names/00_SWE_names.txt",
        "SWE = {\n\tair_wing_names_template = AIR_WING_NAME_SWE\n}\n",
    )
    _write(
        tmp_path,
        "localisation/english/MD_names_l_english.yml",
        'l_english:\n AIR_WING_NAME_SWE:0 "%d. Flygflottilj"\n',
    )
    validator = _validator(tmp_path)
    validator.validate_air_wing_names_template_loc()

    assert validator._issues == []


def test_created_variant_check_skips_a_mod_with_no_variant_sources(
    tmp_path, monkeypatch
):
    (tmp_path / "common" / "units" / "equipment").mkdir(parents=True)
    validator = _validator(tmp_path)
    logged = []
    monkeypatch.setattr(validator, "log", lambda msg, *a, **k: logged.append(msg))
    validator.validate_created_variant_modules()

    assert validator._issues == []
    assert logged[-1] == "  No files with equipment variants to check"


def test_created_variant_check_skips_files_without_a_variant(tmp_path, monkeypatch):
    _write(tmp_path, "common/units/equipment/MD_ships.txt", _EQUIPMENT)
    _write(tmp_path, "events/SWE.txt", "country_event = {\n\tid = swe.1\n}\n")
    validator = _validator(tmp_path)
    logged = []
    monkeypatch.setattr(validator, "log", lambda msg, *a, **k: logged.append(msg))
    validator.validate_created_variant_modules()

    assert validator._issues == []
    assert "  Found 1 files to check" in logged


def test_oob_version_name_without_a_matching_variant_is_reported(tmp_path):
    _write(tmp_path, "common/units/equipment/MD_ships.txt", _EQUIPMENT)
    _write(tmp_path, "history/countries/SWE - Sweden.txt", _VARIANT)
    _write(tmp_path, "history/units/SWE_1990.txt", _ship_oob("Ghost Class"))
    _write(tmp_path, "history/units/SWE_army.txt", "units = {\n}\n")
    validator = _validator(tmp_path)
    validator.validate_oob_variant_references()

    assert validator.errors_found == 1
    assert (
        validator._issues[0].category
        == "OOB SHIP: version_name has no matching equipment variant"
    )
    assert "Ghost Class" in validator._issues[0].message


def test_oob_version_name_matching_a_variant_is_clean(tmp_path):
    _write(tmp_path, "common/units/equipment/MD_ships.txt", _EQUIPMENT)
    _write(tmp_path, "history/countries/SWE - Sweden.txt", _VARIANT)
    _write(tmp_path, "history/units/SWE_1990.txt", _ship_oob("Naresuan Class"))
    validator = _validator(tmp_path)
    validator.validate_oob_variant_references()

    assert validator._issues == []


def test_production_line_naming_an_archetype_is_reported(tmp_path):
    _write(tmp_path, "common/units/equipment/MD_ships.txt", _EQUIPMENT)
    _write(
        tmp_path,
        "history/countries/SWE - Sweden.txt",
        _VARIANT + "add_equipment_production = {\n"
        "\tequipment = {\n"
        "\t\ttype = ship_hull_frigate\n"
        '\t\tcreator = "SWE"\n'
        "\t}\n"
        "\trequested_factories = 1\n"
        "}\n",
    )
    validator = _validator(tmp_path)
    validator.validate_oob_variant_references()

    assert validator.errors_found == 1
    assert (
        validator._issues[0].category
        == "PRODUCTION: archetype attributed to a producer"
    )
    assert "ship_hull_frigate" in validator._issues[0].message


def test_clean_mod_passes_every_oob_check(tmp_path):
    _write(tmp_path, "common/units/MD_land_units.txt", _UNITS)
    _write(tmp_path, "common/units/equipment/MD_ships.txt", _EQUIPMENT)
    _write(
        tmp_path,
        "common/units/names_divisions/SWE.txt",
        "SWE_ARM = {\n\tname = NAME_SWE_ARM\n}\n",
    )
    _write(tmp_path, "history/countries/SWE - Sweden.txt", _VARIANT)
    _write(
        tmp_path,
        "history/units/SWE_1990.txt",
        "division_template = {\n"
        '\tname = "Infantry Brigade"\n'
        "\tdivision_names_group = SWE_ARM\n"
        "\tregiments = {\n"
        "\t\tL_Inf_Bat = { x = 0 y = 0 }\n"
        "\t}\n"
        "}\n" + _ship_oob("Naresuan Class"),
    )
    validator = _validator(tmp_path)
    validator.run_validations()

    assert validator._issues == []
    assert validator.errors_found == 0
    assert validator.warnings_found == 0
