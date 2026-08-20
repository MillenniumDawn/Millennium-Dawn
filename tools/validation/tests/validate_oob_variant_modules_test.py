"""Tank and plane coverage for the created-variant slot check.

Ship designs were the only ones validated; a tank or helicopter design with a
module in a slot that rejects it loaded just as silently. These cover the whole
set of sources a variant can be created from, the module-unlock rule that keeps
legal designs quiet, and the severity split against ship designs.
"""

from validate_oob_units import Validator

_HULLS = """
equipments = {
\ttest_tank_chassis = {
\t\tis_archetype = yes
\t\ttype = { armor }
\t\tmodule_slots = {
\t\t\tturret_type_slot = {
\t\t\t\trequired = yes
\t\t\t\tallowed_module_categories = {
\t\t\t\t\ttest_turret_type
\t\t\t\t}
\t\t\t}
\t\t\tarmor_type_slot = {
\t\t\t\trequired = no
\t\t\t\tallowed_module_categories = {
\t\t\t\t}
\t\t\t}
\t\t}
\t}
\ttest_tank_chassis_1 = {
\t\tarchetype = test_tank_chassis
\t\tmodule_slots = inherit
\t}
}
"""

_MODULES = """
equipment_modules = {
\ttest_turret = {
\t\tcategory = test_turret_type
\t\tallowed_module_categories = {
\t\t\tarmor_type_slot = { test_composite_armor_type }
\t\t}
\t}
\ttest_plain_turret = {
\t\tcategory = test_turret_type
\t}
\ttest_composite_armor = {
\t\tcategory = test_composite_armor_type
\t}
}
"""


def _variant(modules_body):
    return (
        "create_equipment_variant = {\n"
        '\tname = "Test Tank"\n'
        "\ttype = test_tank_chassis_1\n"
        "\tmodules = {\n"
        f"{modules_body}"
        "\t}\n"
        "}\n"
    )


def _write(tmp_path, rel, body):
    path = tmp_path / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _run(tmp_path, sources):
    _write(tmp_path, "common/units/equipment/MD_test_tank_chassis.txt", _HULLS)
    _write(
        tmp_path, "common/units/equipment/modules/MD_test_tank_modules.txt", _MODULES
    )
    for rel, body in sources.items():
        _write(tmp_path, rel, body)
    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.run_validations()
    return [i for i in validator._issues if i.category.startswith("EQUIPMENT VARIANT")]


_UNLOCKED = (
    "\t\tturret_type_slot = test_turret\n\t\tarmor_type_slot = test_composite_armor\n"
)
_NOT_UNLOCKED = (
    "\t\tturret_type_slot = test_plain_turret\n"
    "\t\tarmor_type_slot = test_composite_armor\n"
)


def test_variant_sources_preserve_staged_and_full_scopes(tmp_path):
    staged_path = _write(tmp_path, "events/05_staged.txt", _variant(_UNLOCKED))
    _write(tmp_path, "events/06_full.txt", _variant(_UNLOCKED))

    validator = Validator(
        mod_path=str(tmp_path), use_colors=False, workers=1, staged_only=True
    )
    validator.staged_files = [str(staged_path)]

    staged = validator._get_variant_sources(ignore_staged=False)
    full = validator._get_variant_sources(ignore_staged=True)
    assert {rel for rel, _ in staged} == {"events/05_staged.txt"}
    assert {rel for rel, _ in full} == {
        "events/05_staged.txt",
        "events/06_full.txt",
    }

    full_validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    assert full_validator._get_variant_sources(ignore_staged=False) is full_validator._get_variant_sources(
        ignore_staged=True
    )


def test_flags_land_variant_in_every_source(tmp_path):
    sources = {
        "events/05_test.txt": _variant(_NOT_UNLOCKED),
        "common/national_focus/05_test.txt": _variant(_NOT_UNLOCKED),
        "common/decisions/05_test.txt": _variant(_NOT_UNLOCKED),
        "history/countries/TST - Test.txt": _variant(_NOT_UNLOCKED),
        "common/scripted_effects/05_test.txt": _variant(_NOT_UNLOCKED),
        "common/special_projects/05_test.txt": _variant(_NOT_UNLOCKED),
    }
    issues = _run(tmp_path, sources)
    assert {i.file for i in issues} == set(sources)
    assert all("test_composite_armor" in i.message for i in issues)


def test_land_variant_blocks_merge(tmp_path):
    issues = _run(tmp_path, {"events/05_test.txt": _variant(_NOT_UNLOCKED)})
    assert len(issues) == 1
    assert issues[0].severity == "error"
    assert (
        issues[0].category == "EQUIPMENT VARIANT: module category not allowed in slot"
    )


def test_module_unlock_keeps_legal_design_quiet(tmp_path):
    # test_turret unlocks composite armor in armor_type_slot; without modelling
    # that, every real tank design here is a false positive.
    assert _run(tmp_path, {"events/05_test.txt": _variant(_UNLOCKED)}) == []


def test_unknown_slot_on_tank_chassis_flagged(tmp_path):
    issues = _run(
        tmp_path,
        {"events/05_test.txt": _variant("\t\tfixed_ship_battery_slot = test_turret\n")},
    )
    assert len(issues) == 1
    assert issues[0].category == "EQUIPMENT VARIANT: slot not on hull"
