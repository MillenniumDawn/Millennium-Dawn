"""Parser and per-file check coverage for validate_oob_units.py.

Covers the readers behind the OOB/namelist passes: the canonical sub-unit and
equipment-name extraction, the division-name group index, the regiments/support
reference scan, and the per-file workers the pool calls, including the empty
and unreadable-file fallbacks each one carries.
"""

import validate_oob_units as V

_UNITS = """sub_units = {
\t# a stripped comment leaves a blank line at depth 1
\tArm_Inf_Bat = {
\t\tmap_icon_category = infantry
\t\tneed = {
\t\t\tinfantry_weapons = 100
\t\t}
\t}
\t@spacer = 1
\tMech_Inf_Bat = {
\t\tneed_equipment = {
\t\t\tutil_vehicle_equipment = 40
\t\t}
\t}
}
"""


def _write(tmp_path, relative, body):
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return str(path)


def _write_units(tmp_path):
    return _write(tmp_path, "common/units/MD_land_units.txt", _UNITS)


# --- file reading -----------------------------------------------------------


def test_read_text_returns_empty_for_a_missing_file(tmp_path):
    assert V._read_text(str(tmp_path / "gone.txt"), str(tmp_path)) == ""


# --- canonical unit sources -------------------------------------------------


def test_parse_canonical_units_file_skips_non_definition_lines():
    assert V._parse_canonical_units_file(_UNITS) == {"Arm_Inf_Bat", "Mech_Inf_Bat"}


def test_parse_canonical_units_reads_the_units_directory(tmp_path):
    _write_units(tmp_path)
    assert V.parse_canonical_units(str(tmp_path)) == {"Arm_Inf_Bat", "Mech_Inf_Bat"}


def test_parse_canonical_namelist_keys_adds_equipment_names(tmp_path):
    _write_units(tmp_path)
    sub_units = V.parse_canonical_units(str(tmp_path))
    assert V.parse_canonical_namelist_keys(str(tmp_path), sub_units) == {
        "Arm_Inf_Bat",
        "Mech_Inf_Bat",
        "infantry_weapons",
        "util_vehicle_equipment",
    }


# --- division name groups ---------------------------------------------------


def test_extract_division_group_keys_only_takes_top_level_blocks():
    content = (
        "USA_ARM = {\n"
        '\tname = "Armored Divisions"\n'
        "\tfallback_name = {\n"
        "\t\tfoo = bar\n"
        "\t}\n"
        "}\n"
        "USA_INF = {\n"
        '\tname = "Infantry Divisions"\n'
        "}\n"
    )
    assert V._extract_division_group_keys(content) == {"USA_ARM", "USA_INF"}


def test_parse_division_group_keys_skips_empty_files(tmp_path):
    _write(tmp_path, "common/units/names_divisions/empty.txt", "")
    _write(
        tmp_path,
        "common/units/names_divisions/USA.txt",
        "USA_ARM = {\n\tname = NAME_USA_ARM\n}\n",
    )
    assert V.parse_division_group_keys(str(tmp_path)) == {"USA_ARM"}


def test_extract_division_names_group_refs_records_lines():
    content = (
        "units = {\n"
        "\tdivision = {\n"
        '\t\tname = "1. Division"\n'
        "\t\tdivision_names_group = USA_ARM\n"
        "\t}\n"
        "}\n"
    )
    assert V._extract_division_names_group_refs(content) == [("USA_ARM", 4)]


def test_validate_oob_division_groups_file_missing_file_is_empty(tmp_path):
    assert (
        V.validate_oob_division_groups_file(
            (str(tmp_path / "gone.txt"), {"USA_ARM"}, {}, str(tmp_path))
        )
        == []
    )


def test_validate_oob_division_groups_file_flags_unknown_group(tmp_path, monkeypatch):
    monkeypatch.setenv("MD_NO_CACHE", "1")
    path = _write(
        tmp_path,
        "history/units/USA_1990.txt",
        "units = {\n"
        "\tdivision = {\n"
        "\t\tdivision_names_group = USA_ARM\n"
        "\t\tdivision_names_group = USA_ARMM\n"
        "\t}\n"
        "}\n",
    )
    results = V.validate_oob_division_groups_file(
        (path, {"USA_ARM"}, {"usa_arm": "USA_ARM"}, str(tmp_path))
    )
    assert results == [
        "USA_1990.txt:4: unknown division_names_group 'USA_ARMM' "
        "(did you mean 'USA_ARM'?)"
    ]


# --- unit references in regiments/support blocks ----------------------------


def test_extract_unit_refs_reads_both_block_and_count_forms():
    content = (
        "division_template = {\n"
        '\tname = "Infantry Brigade"\n'
        "\tdivision_names_group = USA_INF\n"
        "\tregiments = {\n"
        "\t\tArm_Inf_Bat = {\n"
        "\t\t\tx = 0\n"
        "\t\t\ty = 0\n"
        "\t\t}\n"
        "\n"
        "\t\tMech_Inf_Bat = 2\n"
        "\t}\n"
        "\tsupport = {\n"
        "\t\tengineer = { x = 0 y = 0 }\n"
        "\t}\n"
        "}\n"
    )
    assert V._extract_unit_refs_from_blocks(content) == {
        "Arm_Inf_Bat",
        "Mech_Inf_Bat",
        "engineer",
    }


def test_validate_oob_file_missing_file_is_empty(tmp_path):
    assert (
        V.validate_oob_file((str(tmp_path / "gone.txt"), set(), {}, str(tmp_path)))
        == []
    )


def test_validate_oob_file_suggests_the_closest_unit_name(tmp_path, monkeypatch):
    monkeypatch.setenv("MD_NO_CACHE", "1")
    path = _write(
        tmp_path,
        "history/units/USA_1990.txt",
        "division_template = {\n"
        "\tregiments = {\n"
        "\t\tArm_Inf_Bt = { x = 0 y = 0 }\n"
        "\t}\n"
        "}\n",
    )
    results = V.validate_oob_file(
        (
            path,
            {"Arm_Inf_Bat"},
            {"arm_inf_bat": "Arm_Inf_Bat"},
            str(tmp_path),
        )
    )
    assert results == [
        "USA_1990.txt: unknown unit 'Arm_Inf_Bt' (did you mean 'Arm_Inf_Bat'?)"
    ]


def test_validate_oob_file_clean_for_canonical_units(tmp_path, monkeypatch):
    monkeypatch.setenv("MD_NO_CACHE", "1")
    path = _write(
        tmp_path,
        "history/units/USA_1990.txt",
        "division_template = {\n"
        "\tregiments = {\n"
        "\t\tArm_Inf_Bat = { x = 0 y = 0 }\n"
        "\t}\n"
        "}\n",
    )
    assert (
        V.validate_oob_file(
            (path, {"Arm_Inf_Bat"}, {"arm_inf_bat": "Arm_Inf_Bat"}, str(tmp_path))
        )
        == []
    )


# --- namelist dispatch ------------------------------------------------------


def test_validate_namelist_file_missing_file_is_empty(tmp_path):
    assert (
        V.validate_namelist_file((str(tmp_path / "gone.txt"), set(), {}, str(tmp_path)))
        == []
    )


def test_validate_namelist_file_ignores_an_unknown_parent_directory(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("MD_NO_CACHE", "1")
    path = _write(
        tmp_path,
        "common/units/names_other/USA.txt",
        "USA = {\n\tnot_a_real_unit_key = {\n\t\tprefix = X\n\t}\n}\n",
    )
    assert V.validate_namelist_file((path, set(), {}, str(tmp_path))) == []


# --- deleted template names and scripted-effect closure ---------------------


def test_deleted_template_names_skips_unreadable_and_nameless_blocks(tmp_path):
    path = _write(
        tmp_path,
        "common/ideas/md.txt",
        "delete_unit_template_and_units = {\n\t\tdisband = yes\n}\n"
        'delete_unit_template_and_units = {\n\t\tdivision_template = "Militia"\n}\n',
    )
    names = V._deleted_template_names(str(tmp_path), [str(tmp_path / "gone.txt"), path])
    assert names == frozenset({"Militia"})


def test_effect_template_closure_ignores_unknown_calls_and_empty_files(tmp_path):
    path = _write(
        tmp_path,
        "common/scripted_effects/md.txt",
        "ensure_militia = {\n"
        '\tdivision_template = { name = "Militia" }\n'
        "\tsome_effect_defined_elsewhere = yes\n"
        "}\n",
    )
    empty = _write(tmp_path, "common/scripted_effects/empty.txt", "")
    closure = V._effect_template_closure(str(tmp_path), [empty, path])
    assert closure["ensure_militia"] == frozenset({"Militia"})


# --- attributed archetypes --------------------------------------------------


def test_production_without_an_equipment_type_is_not_flagged():
    content = "add_equipment_production = {\n\tproducer = SWE\n\tamount = 10\n}\n"
    assert V.check_attributed_archetypes(content, {"ship_hull_light"}) == []
