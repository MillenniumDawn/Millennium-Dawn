"""Tests for the equipment variant module/slot cross-check.

The engine silently drops a module assigned to a slot that does not exist on the
hull, or whose category is not in that slot's allowed set (upstream PR #2510).
These cover the resolver (archetype inheritance, cloned archetypes,
module->category, module-driven slot unlocks) and each finding kind against
synthetic hull/module fixtures.
"""

from equipment_module_slots import (
    build_indexes,
    check_created_variants,
    check_target_variants,
)
from validate_ai_equipment import Validator

# Archetype with two slots; hull_1 inherits, hull_2 overrides and adds a slot.
HULLS = """
equipments = {
\ttest_ship = {
\t\tis_archetype = yes
\t\ttype = screen_ship
\t\tmodule_slots = {
\t\t\tfixed_ship_battery_slot = {
\t\t\t\trequired = yes
\t\t\t\tallowed_module_categories = { module_light_guns_category }
\t\t\t}
\t\t\tfixed_ship_fire_control_system_slot = {
\t\t\t\trequired = no
\t\t\t\tallowed_module_categories = { module_screen_fire_control_system_category }
\t\t\t}
\t\t\tfixed_ship_ammo_slot = {
\t\t\t\trequired = yes
\t\t\t\tallowed_module_categories = {
\t\t\t\t}
\t\t\t}
\t\t}
\t}
\ttest_ship_hull_1 = {
\t\tarchetype = test_ship
\t\tmodule_slots = inherit
\t}
\ttest_ship_hull_2 = {
\t\tarchetype = test_ship
\t\tmodule_slots = {
\t\t\tfixed_ship_battery_slot = {
\t\t\t\tallowed_module_categories = { module_light_guns_category }
\t\t\t}
\t\t\trear_1_custom_slot = {
\t\t\t\tallowed_module_categories = { module_light_helipad_category }
\t\t\t}
\t\t}
\t}
}
"""

# A cloned family: every test_ship_hull_N gains a test_boat_hull_N twin.
DUPLICATES = """
duplicate_archetypes = {
\ttest_boat = {
\t\tarchetype = test_ship
\t\ttype = screen_ship
\t}
}
"""

MODULES = """
equipment_modules = {
\tmodule_test_gun = {
\t\tcategory = module_light_guns_category
\t\tallowed_module_categories = {
\t\t\tfixed_ship_ammo_slot = { module_gun_ammo_category }
\t\t}
\t\tcan_convert_from = { module_category = module_gun_battery_category }
\t}
\tmodule_test_screen_fc = {
\t\tcategory = module_screen_fire_control_system_category
\t}
\tmodule_test_plain_fc = {
\t\tcategory = module_fire_control_system_category
\t}
\tmodule_test_helipad = {
\t\tcategory = module_light_helipad_category
\t}
\tmodule_test_gun_ammo = {
\t\tcategory = module_gun_ammo_category
\t}
}
"""


def _indexes():
    return build_indexes([HULLS, DUPLICATES], [MODULES])


def _variant(hull, modules_body):
    return (
        "TST_navy = {\n"
        "\tcategory = naval\n"
        "\troles = { naval_destroyer }\n"
        "\tTST_design = {\n"
        "\t\ttarget_variant = {\n"
        f"\t\t\ttype = {hull}\n"
        "\t\t\tmodules = {\n"
        f"{modules_body}"
        "\t\t\t}\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )


def _kinds(content):
    return [f.kind for f in check_target_variants(content, _indexes())]


def test_build_indexes_resolves_inheritance_and_categories():
    index = _indexes()
    assert (
        index.module_category["module_test_plain_fc"]
        == "module_fire_control_system_category"
    )
    # can_convert_from's module_category must not be mistaken for the module's own.
    assert index.module_category["module_test_gun"] == "module_light_guns_category"
    # hull_1 inherits the archetype's three slots.
    assert set(index.hull_slots["test_ship_hull_1"]) == {
        "fixed_ship_battery_slot",
        "fixed_ship_fire_control_system_slot",
        "fixed_ship_ammo_slot",
    }
    assert "module_screen_fire_control_system_category" in index.known_categories
    # A module's own allowed_module_categories is a slot unlock, not its category.
    assert index.slot_unlocks["module_test_gun"]["fixed_ship_ammo_slot"] == {
        "module_gun_ammo_category"
    }
    # The same unlock is reachable through the category, for designs that name it.
    assert index.slot_unlocks["module_light_guns_category"]["fixed_ship_ammo_slot"] == {
        "module_gun_ammo_category"
    }


def test_duplicate_archetype_clones_the_whole_family():
    index = _indexes()
    assert index.hull_slots["test_boat_hull_1"] == index.hull_slots["test_ship_hull_1"]
    assert index.hull_slots["test_boat"] == index.hull_slots["test_ship"]


def test_correct_category_passes():
    content = _variant(
        "test_ship_hull_1",
        "\t\t\t\tfixed_ship_battery_slot = module_test_gun\n"
        "\t\t\t\tfixed_ship_fire_control_system_slot = module_test_screen_fc\n",
    )
    assert _kinds(content) == []


def test_wrong_category_flagged():
    content = _variant(
        "test_ship_hull_1",
        "\t\t\t\tfixed_ship_fire_control_system_slot = module_test_plain_fc\n",
    )
    assert _kinds(content) == ["category_mismatch"]


def test_unknown_module_flagged():
    content = _variant(
        "test_ship_hull_1",
        "\t\t\t\tfixed_ship_battery_slot = module_does_not_exist\n",
    )
    assert _kinds(content) == ["unknown_module"]


def test_unknown_slot_flagged():
    content = _variant(
        "test_ship_hull_1",
        "\t\t\t\tnonexistent_slot = module_test_gun\n",
    )
    assert _kinds(content) == ["unknown_slot"]


def test_unknown_hull_flagged_once():
    content = _variant(
        "no_such_hull",
        "\t\t\t\tfixed_ship_battery_slot = module_test_gun\n"
        "\t\t\t\tfixed_ship_fire_control_system_slot = module_test_screen_fc\n",
    )
    assert _kinds(content) == ["unknown_hull"]


def test_empty_is_always_legal():
    content = _variant(
        "test_ship_hull_1",
        "\t\t\t\tfixed_ship_battery_slot = empty\n"
        "\t\t\t\tfixed_ship_fire_control_system_slot = > empty\n",
    )
    assert _kinds(content) == []


def test_category_token_as_module():
    # A category token in the { module = <token> } upgrade form is a legal
    # reference; the token's category must still match the slot.
    ok = _variant(
        "test_ship_hull_1",
        "\t\t\t\tfixed_ship_fire_control_system_slot = "
        "{ module = module_screen_fire_control_system_category upgrade = current }\n",
    )
    assert _kinds(ok) == []
    bad = _variant(
        "test_ship_hull_1",
        "\t\t\t\tfixed_ship_fire_control_system_slot = "
        "{ module = module_fire_control_system_category upgrade = current }\n",
    )
    assert _kinds(bad) == ["category_mismatch"]


def test_overriding_hull_uses_own_slots():
    # test_ship_hull_2 replaces module_slots and drops the fire-control slot.
    content = _variant(
        "test_ship_hull_2",
        "\t\t\t\trear_1_custom_slot = module_test_helipad\n"
        "\t\t\t\tfixed_ship_fire_control_system_slot = module_test_screen_fc\n",
    )
    assert _kinds(content) == ["unknown_slot"]


def test_non_naval_template_also_checked():
    # Tank and plane templates follow the same slot rules; skipping them by
    # category hid every land and air mismatch.
    content = (
        "TST_tank = {\n"
        "\tcategory = land\n"
        "\tTST_design = {\n"
        "\t\ttarget_variant = {\n"
        "\t\t\ttype = test_ship_hull_1\n"
        "\t\t\tmodules = {\n"
        "\t\t\t\tfixed_ship_fire_control_system_slot = module_test_plain_fc\n"
        "\t\t\t}\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )
    assert _kinds(content) == ["category_mismatch"]


def test_empty_allowed_set_permits_nothing_on_its_own():
    # fixed_ship_ammo_slot declares an empty allowed_module_categories, so the
    # ammo only fits once a module unlocks its category.
    content = _variant(
        "test_ship_hull_1",
        "\t\t\t\tfixed_ship_ammo_slot = module_test_gun_ammo\n",
    )
    assert _kinds(content) == ["category_mismatch"]


def test_module_unlocks_its_own_slot():
    content = _variant(
        "test_ship_hull_1",
        "\t\t\t\tfixed_ship_battery_slot = module_test_gun\n"
        "\t\t\t\tfixed_ship_ammo_slot = module_test_gun_ammo\n",
    )
    assert _kinds(content) == []


def test_category_reference_unlocks_its_slot():
    # Generic AI designs name the category they want the best available of, so
    # the unlocks of everything in it are in play.
    content = _variant(
        "test_ship_hull_1",
        "\t\t\t\tfixed_ship_battery_slot = module_light_guns_category\n"
        "\t\t\t\tfixed_ship_ammo_slot = module_test_gun_ammo\n",
    )
    assert _kinds(content) == []


def _created(hull, modules_body):
    """A create_equipment_variant buried in a focus reward, as they really appear."""
    return (
        "focus_tree = {\n"
        "\tfocus = {\n"
        "\t\tid = TST_ship\n"
        "\t\tcompletion_reward = {\n"
        "\t\t\thidden_effect = {\n"
        "\t\t\t\tcreate_equipment_variant = {\n"
        '\t\t\t\t\tname = "Test Class"\n'
        f"\t\t\t\t\ttype = {hull}\n"
        "\t\t\t\t\tmodules = {\n"
        f"{modules_body}"
        "\t\t\t\t\t}\n"
        "\t\t\t\t}\n"
        "\t\t\t}\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )


def _created_kinds(content):
    return [f.kind for f in check_created_variants(content, _indexes())]


def test_created_variant_correct_passes():
    content = _created(
        "test_ship_hull_1",
        "\t\t\t\t\t\tfixed_ship_battery_slot = module_test_gun\n"
        "\t\t\t\t\t\tfixed_ship_fire_control_system_slot = module_test_screen_fc\n",
    )
    assert _created_kinds(content) == []


def test_created_variant_wrong_category_flagged():
    content = _created(
        "test_ship_hull_1",
        "\t\t\t\t\t\tfixed_ship_fire_control_system_slot = module_test_plain_fc\n",
    )
    assert _created_kinds(content) == ["category_mismatch"]


def test_created_variant_unknown_slot_flagged():
    # The real ENG Type 32 Guardian shape: a tank slot name on a ship hull.
    content = _created(
        "test_ship_hull_1",
        "\t\t\t\t\t\tengine_type_slot = module_test_gun\n",
    )
    assert _created_kinds(content) == ["unknown_slot"]


def test_created_variant_non_ship_type_skipped():
    # Tank and plane designs share the effect but not the hull index; flagging
    # their chassis as an unknown hull would be a false positive on every one.
    content = _created(
        "medium_tank_chassis_1",
        "\t\t\t\t\t\tturret_type_slot = tank_medium_cannon_2\n",
    )
    assert _created_kinds(content) == []


def test_created_variant_empty_is_legal():
    content = _created(
        "test_ship_hull_1",
        "\t\t\t\t\t\tfixed_ship_battery_slot = empty\n",
    )
    assert _created_kinds(content) == []


def test_created_variant_reports_real_line_number():
    content = _created(
        "test_ship_hull_1",
        "\t\t\t\t\t\tfixed_ship_battery_slot = module_test_gun\n"
        "\t\t\t\t\t\tnonexistent_slot = module_test_gun\n",
    )
    findings = check_created_variants(content, _indexes())
    assert len(findings) == 1
    assert (
        content.split("\n")[findings[0].line - 1].strip().startswith("nonexistent_slot")
    )


def test_created_variant_comment_does_not_hide_finding():
    content = _created(
        "test_ship_hull_1",
        "\t\t\t\t\t\tnonexistent_slot = module_test_gun # legacy slot\n",
    )
    assert _created_kinds(content) == ["unknown_slot"]


def _write(tmp_path, rel, body):
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p


def test_oob_validator_integration_reports_errors(tmp_path):
    from validate_oob_units import Validator as OobValidator

    _write(tmp_path, "common/units/equipment/MD_test_ships.txt", HULLS)
    _write(tmp_path, "common/units/equipment/modules/MD_test_modules.txt", MODULES)
    _write(
        tmp_path,
        "common/national_focus/05_test.txt",
        _created(
            "test_ship_hull_1",
            "\t\t\t\t\t\tfixed_ship_fire_control_system_slot = module_test_plain_fc\n",
        ),
    )
    validator = OobValidator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.run_validations()
    variant = [i for i in validator._issues if i.category.startswith("SHIP VARIANT")]
    assert len(variant) == 1
    assert variant[0].severity == "error"
    assert variant[0].file == "common/national_focus/05_test.txt"
    assert "module_test_plain_fc" in variant[0].message


def test_validator_integration_reports_errors(tmp_path):
    _write(tmp_path, "common/units/equipment/MD_test_ships.txt", HULLS)
    _write(tmp_path, "common/units/equipment/modules/MD_test_modules.txt", MODULES)
    _write(
        tmp_path,
        "common/ai_equipment/TST_naval.txt",
        _variant(
            "test_ship_hull_1",
            "\t\t\t\tfixed_ship_battery_slot = module_test_gun\n"
            "\t\t\t\tfixed_ship_fire_control_system_slot = module_test_plain_fc\n",
        ),
    )
    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.run_validations()
    naval = [i for i in validator._issues if i.category.startswith("NAVAL VARIANT")]
    assert len(naval) == 1
    assert naval[0].severity == "error"
    assert naval[0].file == "common/ai_equipment/TST_naval.txt"
    assert "module_test_plain_fc" in naval[0].message


def _group(designs):
    """A naval design group where each (name, history) design opts in or out."""
    body = ""
    for name, history in designs:
        body += f"\t{name} = {{\n"
        if history:
            body += "\t\thistory = yes\n"
        body += "\t\ttarget_variant = {\n\t\t\ttype = test_ship_hull_1\n\t\t}\n\t}\n"
    return (
        "TST_navy = {\n"
        "\tcategory = naval\n"
        "\troles = { naval_destroyer }\n" + body + "}\n"
    )


def test_partial_history_is_flagged(tmp_path):
    _write(tmp_path, "common/units/equipment/MD_test_ships.txt", HULLS)
    _write(tmp_path, "common/units/equipment/modules/MD_test_modules.txt", MODULES)
    _write(
        tmp_path,
        "common/ai_equipment/TST_naval.txt",
        _group([("TST_a", True), ("TST_b", False)]),
    )
    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.run_validations()
    issues = [i for i in validator._issues if "partial history" in i.category]
    assert len(issues) == 1
    assert "TST_b" in issues[0].message
    assert "1/2" in issues[0].message


def test_uniform_history_is_not_flagged(tmp_path):
    _write(tmp_path, "common/units/equipment/MD_test_ships.txt", HULLS)
    _write(tmp_path, "common/units/equipment/modules/MD_test_modules.txt", MODULES)
    for designs in (
        [("TST_a", True), ("TST_b", True)],
        [("TST_a", False), ("TST_b", False)],
    ):
        _write(tmp_path, "common/ai_equipment/TST_naval.txt", _group(designs))
        validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
        validator.run_validations()
        assert not [i for i in validator._issues if "partial history" in i.category]
