"""Tests for the canonical namelist key checks in validate_oob_units.py.

Namelist tokens are matched case-sensitively against common/units/*.txt on
Linux; a wrong-case division_types token or a dead vanilla ship_types token
means the namelist silently never applies.
"""

from validate_oob_units import Validator, _parse_canonical_units_file

_LAND_UNITS = """sub_units = {
\tArm_Inf_Bat = {
\t\tmap_icon_category = infantry
\t\tneed = {
\t\t\tinfantry_weapons = 100
\t\t}
\t}
\tMech_Inf_Bat = {
\t\tneed = {
\t\t\tutil_vehicle_equipment = 40
\t\t}
\t}
}
"""

_NAVAL_UNITS = """sub_units = {
\tcorvette = {
\t\tmap_icon_category = ship
\t\tneed = {
\t\t\tship_hull_corvette = 1
\t\t}
\t}
}
"""


def _make_units(tmp_path):
    units_dir = tmp_path / "common" / "units"
    units_dir.mkdir(parents=True)
    (units_dir / "MD_land_units.txt").write_text(_LAND_UNITS, encoding="utf-8")
    (units_dir / "MD_naval_units.txt").write_text(_NAVAL_UNITS, encoding="utf-8")
    return units_dir


def _run_namelist_check(tmp_path, subdir, filename, body):
    units_dir = _make_units(tmp_path)
    target_dir = units_dir / subdir
    target_dir.mkdir()
    (target_dir / filename).write_text(body, encoding="utf-8")

    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator._build_canonical_units()
    validator.validate_namelist_references()
    return validator


def test_parse_canonical_units_file_extracts_sub_unit_names():
    canonical = _parse_canonical_units_file(_LAND_UNITS)
    assert canonical == {"Arm_Inf_Bat", "Mech_Inf_Bat"}


def test_wrong_case_division_types_token_flagged(tmp_path):
    validator = _run_namelist_check(
        tmp_path,
        "names_divisions",
        "USA_names_divisions.txt",
        "USA_ARM = {\n"
        '\tname = "Armored Divisions"\n'
        "\tfor_countries = { USA }\n"
        '\tdivision_types = { "arm_inf_bat" }\n'
        "}\n",
    )
    assert validator.warnings_found == 1
    message = validator._issues[0].message
    assert "unknown division_types token 'arm_inf_bat'" in message
    assert "did you mean 'Arm_Inf_Bat'" in message


def test_canonical_division_types_token_clean(tmp_path):
    validator = _run_namelist_check(
        tmp_path,
        "names_divisions",
        "USA_names_divisions.txt",
        "USA_ARM = {\n"
        '\tname = "Armored Divisions"\n'
        '\tdivision_types = { "Arm_Inf_Bat" "Mech_Inf_Bat" }\n'
        "}\n",
    )
    assert validator.warnings_found == 0
    assert validator._issues == []


def test_dead_vanilla_ship_types_token_flagged(tmp_path):
    """Legacy vanilla tokens (submarine, light_cruiser, ...) were removed by
    MD — a ship_types entry using one is silently dead and must warn."""
    validator = _run_namelist_check(
        tmp_path,
        "names_ships",
        "USA_ship_names.txt",
        "USA_SUBS = {\n"
        "\tname = NAME_THEME_SUBS\n"
        "\tfor_countries = { USA }\n"
        "\ttype = ship\n"
        "\tship_types = { submarine }\n"
        "}\n",
    )
    assert validator.warnings_found == 1
    assert "unknown ship_types token 'submarine'" in validator._issues[0].message


def test_canonical_ship_types_token_clean(tmp_path):
    validator = _run_namelist_check(
        tmp_path,
        "names_ships",
        "USA_ship_names.txt",
        "USA_CORVETTES = {\n"
        "\tname = NAME_THEME_CORVETTES\n"
        "\tship_types = { corvette }\n"
        "}\n",
    )
    assert validator.warnings_found == 0


def test_namelist_block_key_accepts_equipment_type(tmp_path):
    """names/ block keys accept equipment names from need = {} blocks (air
    namelists key on airframes), while an undefined key still warns."""
    validator = _run_namelist_check(
        tmp_path,
        "names",
        "00_USA_names.txt",
        "USA = {\n"
        "\tinfantry_weapons = {\n"
        '\t\tprefix = "Rifle"\n'
        "\t}\n"
        "\tnot_a_real_unit_key = {\n"
        '\t\tprefix = "Ghost"\n'
        "\t}\n"
        "}\n",
    )
    assert validator.warnings_found == 1
    assert (
        "unknown namelist block key 'not_a_real_unit_key'"
        in validator._issues[0].message
    )
