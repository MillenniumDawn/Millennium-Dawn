"""Tests for validate_equipment_upkeep."""

from shared.suite import write_under as _write
from validate_equipment_upkeep import Validator

_EQUIPMENT = """equipments = {
\tmedium_tank_chassis = {
\t\tis_archetype = yes
\t}
\tmedium_tank_chassis_0 = {
\t\tarchetype = medium_tank_chassis
\t}
\tsmall_plane_airframe = {
\t\tis_archetype = yes
\t}
\tzombie = {
\t\tis_archetype = yes
\t}
}
duplicate_archetypes = {
\tmedium_tank_rocket_chassis = {
\t\tarchetype = medium_tank_chassis
\t\ttype = { armor rocket }
\t}
}
"""

_MBT_BATTALION = """\tarmor_Bat = {
\t\tmap_icon_category = armored
\t\tneed = { medium_tank_chassis = 40 }
\t}
"""


def _money(*entries: str) -> str:
    body = "".join(entries)
    return (
        "update_military_rate = {\n"
        "\tset_variable = { equipment_operative_cost = 0 }\n" + body + "}\n"
    )


def _entry(archetype: str, deployed: bool = True, stockpile: bool = True) -> str:
    lines = [
        "\tadd_to_variable = {\n\t\tvar = equipment_operative_cost\n\t\tvalue = {\n"
    ]
    if deployed:
        lines.append(f"\t\t\tvalue = num_equipment_in_armies@{archetype}\n")
    lines.append("\t\t\tmultiply = 0.7\n")
    if stockpile:
        lines.append(
            f"\t\t\tadd = {{ value = num_equipment@{archetype} multiply = 0.14 }}\n"
        )
    lines.append("\t\t}\n\t}\n")
    return "".join(lines)


def _run(tmp_path, battalions: str, money: str, equipment: str = _EQUIPMENT):
    _write(tmp_path, "common/units/equipment/MD_test_equipment.txt", equipment)
    _write(
        tmp_path,
        "common/units/MD_land_units.txt",
        "sub_units = {\n" + battalions + "}\n",
    )
    _write(tmp_path, "common/scripted_effects/00_money_system.txt", money)

    v = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    v.run_validations()
    return v


def _messages(v, category):
    return [i.message for i in v._issues if i.category == category]


def test_costed_archetype_passes(tmp_path):
    v = _run(tmp_path, _MBT_BATTALION, _money(_entry("medium_tank_chassis")))
    assert v._issues == []
    assert v.errors_found == 0


def test_uncosted_archetype_is_reported(tmp_path):
    battalions = _MBT_BATTALION + (
        "\tSP_R_Arty_Bat = {\n"
        "\t\tmap_icon_category = armored\n"
        "\t\tneed = { medium_tank_rocket_chassis = 12 }\n"
        "\t}\n"
    )
    v = _run(tmp_path, battalions, _money(_entry("medium_tank_chassis")))
    messages = _messages(v, "uncosted-land-equipment")
    assert len(messages) == 1
    assert "medium_tank_rocket_chassis" in messages[0]
    assert "SP_R_Arty_Bat" in messages[0]
    assert v.errors_found == 1


def test_exempt_archetype_is_not_reported(tmp_path):
    battalions = _MBT_BATTALION + (
        "\tzombie_Bat = {\n"
        "\t\tmap_icon_category = infantry\n"
        "\t\tneed = { zombie = 100 }\n"
        "\t}\n"
    )
    v = _run(tmp_path, battalions, _money(_entry("medium_tank_chassis")))
    assert _messages(v, "uncosted-land-equipment") == []


def test_variant_resolves_to_its_archetype(tmp_path):
    # A battalion may name a numbered variant directly; only the archetype is
    # ever counted, so the archetype's entry covers it.
    battalions = (
        "\tarmor_Bat = {\n"
        "\t\tmap_icon_category = armored\n"
        "\t\tneed = { medium_tank_chassis_0 = 40 }\n"
        "\t}\n"
    )
    v = _run(tmp_path, battalions, _money(_entry("medium_tank_chassis")))
    assert v._issues == []


def test_transport_reference_is_checked(tmp_path):
    battalions = _MBT_BATTALION + (
        "\tSP_R_Arty_Bat = {\n"
        "\t\tmap_icon_category = armored\n"
        "\t\ttransport = medium_tank_rocket_chassis\n"
        "\t}\n"
    )
    v = _run(tmp_path, battalions, _money(_entry("medium_tank_chassis")))
    messages = _messages(v, "uncosted-land-equipment")
    assert len(messages) == 1
    assert "medium_tank_rocket_chassis" in messages[0]


def test_deployed_only_entry_is_reported_as_partial(tmp_path):
    v = _run(
        tmp_path,
        _MBT_BATTALION,
        _money(_entry("medium_tank_chassis", stockpile=False)),
    )
    messages = _messages(v, "partial-equipment-cost")
    assert len(messages) == 1
    assert "num_equipment@medium_tank_chassis" in messages[0]


def test_stockpile_only_entry_is_reported_as_partial(tmp_path):
    v = _run(
        tmp_path,
        _MBT_BATTALION,
        _money(_entry("medium_tank_chassis", deployed=False)),
    )
    messages = _messages(v, "partial-equipment-cost")
    assert len(messages) == 1
    assert "num_equipment_in_armies@medium_tank_chassis" in messages[0]


def test_air_wing_equipment_is_out_of_scope(tmp_path):
    # Planes carry land_air_wing_size and no map icon; their upkeep is a
    # different model entirely and never reaches equipment_operative_cost.
    battalions = _MBT_BATTALION + (
        "\tlight_fighter = {\n"
        "\t\tland_air_wing_size = 24\n"
        "\t\tneed = { small_plane_airframe = 1 }\n"
        "\t}\n"
    )
    v = _run(tmp_path, battalions, _money(_entry("medium_tank_chassis")))
    assert v._issues == []


def test_missing_accumulator_is_reported_once(tmp_path):
    battalions = _MBT_BATTALION + (
        "\tSP_R_Arty_Bat = {\n"
        "\t\tmap_icon_category = armored\n"
        "\t\tneed = { medium_tank_rocket_chassis = 12 }\n"
        "\t}\n"
    )
    v = _run(tmp_path, battalions, "update_military_rate = {\n}\n")
    assert [i.category for i in v._issues] == ["upkeep-accumulator-missing"]


def test_exempt_archetype_that_gained_a_cost_is_reported_as_stale(tmp_path):
    v = _run(
        tmp_path,
        _MBT_BATTALION,
        _money(_entry("medium_tank_chassis"), _entry("zombie")),
    )
    messages = _messages(v, "stale-upkeep-exemption")
    assert len(messages) == 1
    assert "zombie" in messages[0]
    assert v.errors_found == 0
    assert v.warnings_found == 1


def test_commented_out_entry_does_not_count_as_coverage(tmp_path):
    money = _money().replace(
        "\tset_variable = { equipment_operative_cost = 0 }\n",
        "\tset_variable = { equipment_operative_cost = 0 }\n"
        "#" + _entry("medium_tank_chassis").replace("\n", "\n#") + "\n",
    )
    v = _run(tmp_path, _MBT_BATTALION, money)
    assert [i.category for i in v._issues] == ["upkeep-accumulator-missing"]
