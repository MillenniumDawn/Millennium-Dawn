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

# Archetype with three slots; hull_1 inherits, hull_2 overrides and adds a slot.
# Nothing here is `required = yes`: the required-slot rule has its own fixture
# (REQUIRED_HULLS below) so these tests stay about slot/category rules.
HULLS = """
equipments = {
\ttest_ship = {
\t\tis_archetype = yes
\t\ttype = screen_ship
\t\tmodule_slots = {
\t\t\tfixed_ship_battery_slot = {
\t\t\t\trequired = no
\t\t\t\tallowed_module_categories = { module_light_guns_category }
\t\t\t}
\t\t\tfixed_ship_fire_control_system_slot = {
\t\t\t\trequired = no
\t\t\t\tallowed_module_categories = { module_screen_fire_control_system_category }
\t\t\t}
\t\t\tfixed_ship_ammo_slot = {
\t\t\t\trequired = no
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

# The required-slot rule: battery and ammo are `required = yes`, the sensor slot
# is not. The ammo slot's empty allowed set means the gun module must unlock it,
# which is how a tank's main gun picks its ammunition (the Challenger 2 shape).
# hull_2 re-declares battery without a `required` line, which must default to
# not required.
REQUIRED_HULLS = """
equipments = {
\treq_ship = {
\t\tis_archetype = yes
\t\ttype = screen_ship
\t\tmodule_slots = {
\t\t\tfixed_ship_battery_slot = {
\t\t\t\trequired = yes
\t\t\t\tallowed_module_categories = { module_light_guns_category }
\t\t\t}
\t\t\tfixed_ship_ammo_slot = {
\t\t\t\trequired = yes
\t\t\t\tallowed_module_categories = {
\t\t\t\t}
\t\t\t}
\t\t\toptional_sensor_slot = {
\t\t\t\trequired = no
\t\t\t\tallowed_module_categories = { module_screen_fire_control_system_category }
\t\t\t}
\t\t}
\t}
\treq_ship_hull_1 = {
\t\tarchetype = req_ship
\t\tmodule_slots = inherit
\t}
\treq_ship_hull_2 = {
\t\tarchetype = req_ship
\t\tmodule_slots = {
\t\t\tfixed_ship_battery_slot = {
\t\t\t\tallowed_module_categories = { module_light_guns_category }
\t\t\t}
\t\t}
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
		category = module_gun_ammo_category
	}
	module_test_banned = {
		category = module_light_guns_category
	}
	module_test_amphib_gun = {
		category = module_light_guns_category
		forbid_equipment_type = { amphibious }
	}
	module_test_exact_gun = {
		category = module_light_guns_category
		forbid_equipment_type_exact_match = armor
	}
}
"""


LIMIT_HULLS = """
equipments = {
\tlim_tank = {
\t\tis_archetype = yes
\t\ttype = armor
\t\tmodule_slots = {
\t\t\tgun_slot = {
\t\t\t\trequired = no
\t\t\t\tallowed_module_categories = { module_light_guns_category }
\t\t\t}
\t\t\textra_gun_slot = {
\t\t\t\trequired = no
\t\t\t\tallowed_module_categories = { module_light_guns_category }
\t\t\t}
\t\t}
\t\tmodule_count_limit = { category = module_light_guns_category count < 2 }
\t\tmodule_count_limit = { module = module_test_banned count < 1 }
\t}
\tlim_tank_hull_1 = {
\t\tarchetype = lim_tank
\t\tmodule_slots = inherit
\t}
\tlim_amphib_hull_1 = {
\t\tarchetype = lim_tank
\t\ttype = { armor amphibious }
\t\tmodule_slots = inherit
\t}
}
duplicate_archetypes = {
\tlim_clone = {
\t\tarchetype = lim_tank
\t\ttype = { armor amphibious }
\t}
}
"""


def _indexes():
    return build_indexes([HULLS, DUPLICATES, REQUIRED_HULLS, LIMIT_HULLS], [MODULES])


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
    assert set(index.hull_slots["test_ship_hull_1"] or {}) == {
        "fixed_ship_battery_slot",
        "fixed_ship_fire_control_system_slot",
        "fixed_ship_ammo_slot",
    }
    # The required fixture's hull inherits its slots with the required flags.
    req_slots = index.hull_slots["req_ship_hull_1"] or {}
    battery = req_slots["fixed_ship_battery_slot"]
    ammo = req_slots["fixed_ship_ammo_slot"]
    sensor = req_slots["optional_sensor_slot"]
    assert battery and battery.required
    assert ammo and ammo.required
    assert sensor is not None and not sensor.required
    # A slot re-declared without a `required` line defaults to not required.
    hull2_slots = index.hull_slots["req_ship_hull_2"] or {}
    hull2_battery = hull2_slots["fixed_ship_battery_slot"]
    assert hull2_battery is not None and not hull2_battery.required
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


def test_created_variant_missing_required_slot_flagged():
    # The battery is filled, so only the required ammo slot is left empty — the
    # runtime error this validator exists for (equipment_effects.cpp).
    content = _created(
        "req_ship_hull_1",
        "\t\t\t\t\t\tfixed_ship_battery_slot = module_test_gun\n"
        "\t\t\t\t\t\toptional_sensor_slot = module_test_screen_fc\n",
    )
    findings = check_created_variants(content, _indexes())
    assert [f.kind for f in findings] == ["missing_required_module"]
    assert "fixed_ship_ammo_slot" in findings[0].message
    assert findings[0].hull == "req_ship_hull_1"


def test_created_variant_empty_does_not_fill_required_slot():
    # `= empty` leaves the slot without a module, same as omitting it.
    content = _created(
        "req_ship_hull_1",
        "\t\t\t\t\t\tfixed_ship_battery_slot = empty\n",
    )
    assert _created_kinds(content) == [
        "missing_required_module",
        "missing_required_module",
    ]


def test_created_variant_required_slot_via_unlock_passes():
    # The ammo slot's allowed set is empty, but the equipped gun unlocks it —
    # the Challenger 2 shape, and every required slot is filled.
    content = _created(
        "req_ship_hull_1",
        "\t\t\t\t\t\tfixed_ship_battery_slot = module_test_gun\n"
        "\t\t\t\t\t\tfixed_ship_ammo_slot = module_test_gun_ammo\n",
    )
    assert _created_kinds(content) == []


def test_created_variant_without_modules_block_flagged():
    # No modules at all means every required slot is missing.
    content = (
        "focus_tree = {\n"
        "\tfocus = {\n"
        "\t\tcompletion_reward = {\n"
        "\t\t\tcreate_equipment_variant = {\n"
        '\t\t\t\tname = "Test Class"\n'
        "\t\t\t\ttype = req_ship_hull_1\n"
        "\t\t\t}\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )
    findings = check_created_variants(content, _indexes())
    assert [f.kind for f in findings] == [
        "missing_required_module",
        "missing_required_module",
    ]


def test_created_variant_absent_required_defaults_to_optional():
    # req_ship_hull_2 re-declares battery without a `required` line; the
    # engine default is not required, so no finding.
    content = _created(
        "req_ship_hull_2",
        "\t\t\t\t\t\tfixed_ship_battery_slot = module_test_gun\n",
    )
    assert _created_kinds(content) == []


def test_target_variant_missing_required_slot_flagged():
    # AI templates are held to the same rule: a template no design can match.
    content = _variant(
        "req_ship_hull_1",
        "\t\t\t\tfixed_ship_battery_slot = module_test_gun\n",
    )
    assert _kinds(content) == ["missing_required_module"]


def _write(tmp_path, rel, body):
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p


def _variant_issues(tmp_path, hulls, rel, content, validator_cls, prefix):
    _write(tmp_path, "common/units/equipment/MD_test_ships.txt", hulls)
    _write(tmp_path, "common/units/equipment/modules/MD_test_modules.txt", MODULES)
    _write(tmp_path, rel, content)
    validator = validator_cls(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.run_validations()
    return [i for i in validator._issues if i.category.startswith(prefix)]


def test_oob_validator_integration_reports_errors(tmp_path):
    from validate_oob_units import Validator as OobValidator

    issues = _variant_issues(
        tmp_path,
        HULLS,
        "common/national_focus/05_test.txt",
        _created(
            "test_ship_hull_1",
            "\t\t\t\t\t\tfixed_ship_fire_control_system_slot = module_test_plain_fc\n",
        ),
        OobValidator,
        "SHIP VARIANT",
    )
    assert len(issues) == 1
    assert issues[0].severity == "error"
    assert issues[0].file == "common/national_focus/05_test.txt"
    assert "module_test_plain_fc" in issues[0].message


def test_validator_integration_reports_warnings(tmp_path):
    issues = _variant_issues(
        tmp_path,
        HULLS,
        "common/ai_equipment/TST_naval.txt",
        _variant(
            "test_ship_hull_1",
            "\t\t\t\tfixed_ship_battery_slot = module_test_gun\n"
            "\t\t\t\tfixed_ship_fire_control_system_slot = module_test_plain_fc\n",
        ),
        Validator,
        "NAVAL VARIANT",
    )
    assert len(issues) == 1
    assert issues[0].severity == "warning"
    assert issues[0].file == "common/ai_equipment/TST_naval.txt"
    assert "module_test_plain_fc" in issues[0].message


def test_oob_validator_reports_missing_required_slot(tmp_path):
    from validate_oob_units import Validator as OobValidator

    issues = _variant_issues(
        tmp_path,
        REQUIRED_HULLS,
        "common/national_focus/06_test.txt",
        _created(
            "req_ship_hull_1",
            "\t\t\t\t\t\tfixed_ship_battery_slot = module_test_gun\n",
        ),
        OobValidator,
        "SHIP VARIANT",
    )
    assert len(issues) == 1
    assert issues[0].severity == "error"
    assert issues[0].file == "common/national_focus/06_test.txt"
    assert "fixed_ship_ammo_slot" in issues[0].message


def test_ai_validator_missing_required_slot_is_error(tmp_path):
    # A template that leaves a required slot empty can never be matched, so the
    # AI validator escalates it above its usual slot-rule warning.
    issues = _variant_issues(
        tmp_path,
        REQUIRED_HULLS,
        "common/ai_equipment/TST_naval.txt",
        _variant(
            "req_ship_hull_1",
            "\t\t\t\tfixed_ship_battery_slot = module_test_gun\n"
            "\t\t\t\toptional_sensor_slot = module_test_screen_fc\n",
        ),
        Validator,
        "NAVAL VARIANT",
    )
    assert len(issues) == 1
    assert issues[0].severity == "error"
    assert issues[0].file == "common/ai_equipment/TST_naval.txt"
    assert "fixed_ship_ammo_slot" in issues[0].message


def test_ai_validator_count_limit_is_error(tmp_path):
    issues = _variant_issues(
        tmp_path,
        LIMIT_HULLS,
        "common/ai_equipment/TST_land.txt",
        _variant(
            "lim_tank_hull_1",
            "\t\t\t\tgun_slot = module_test_gun\n"
            "\t\t\t\textra_gun_slot = module_test_gun\n",
        ),
        Validator,
        "EQUIPMENT VARIANT",
    )
    assert len(issues) == 1
    assert issues[0].severity == "error"
    assert "module_light_guns_category" in issues[0].message


def test_two_guns_exceed_category_count_limit():
    content = _variant(
        "lim_tank_hull_1",
        "\t\t\t\tgun_slot = module_test_gun\n"
        "\t\t\t\textra_gun_slot = module_test_gun\n",
    )
    assert _kinds(content) == ["count_limit_exceeded"]


def test_one_gun_respects_category_count_limit():
    content = _variant(
        "lim_tank_hull_1",
        "\t\t\t\tgun_slot = module_test_gun\n",
    )
    assert _kinds(content) == []


def test_banned_module_hits_module_count_limit():
    content = _variant(
        "lim_tank_hull_1",
        "\t\t\t\tgun_slot = module_test_banned\n",
    )
    assert _kinds(content) == ["count_limit_exceeded"]


def test_mixed_any_of_does_not_count_toward_limit():
    content = _variant(
        "lim_tank_hull_1",
        "\t\t\t\tgun_slot = module_test_gun\n"
        "\t\t\t\textra_gun_slot = { any_of = { module_test_gun module_test_helipad } }\n",
    )
    assert _kinds(content) == ["category_mismatch"]


def test_amphibious_forbid_flags_on_amphib_hull():
    content = _variant(
        "lim_amphib_hull_1",
        "\t\t\t\tgun_slot = module_test_amphib_gun\n",
    )
    assert _kinds(content) == ["forbidden_equipment_type"]


def test_amphibious_forbid_allows_armor_hull():
    content = _variant(
        "lim_tank_hull_1",
        "\t\t\t\tgun_slot = module_test_amphib_gun\n",
    )
    assert _kinds(content) == []


def test_exact_match_forbids_armor_only_hull():
    content = _variant(
        "lim_tank_hull_1",
        "\t\t\t\tgun_slot = module_test_exact_gun\n",
    )
    assert _kinds(content) == ["forbidden_equipment_type"]


def test_exact_match_allows_amphibious_hull():
    content = _variant(
        "lim_amphib_hull_1",
        "\t\t\t\tgun_slot = module_test_exact_gun\n",
    )
    assert _kinds(content) == []


def test_duplicate_clone_carries_extra_types():
    index = _indexes()
    assert index.hull_types["lim_clone_hull_1"] == {"armor", "amphibious"}
    assert index.hull_types["lim_tank_hull_1"] == {"armor"}
    content = _variant(
        "lim_clone_hull_1",
        "\t\t\t\tgun_slot = module_test_amphib_gun\n",
    )
    assert _kinds(content) == ["forbidden_equipment_type"]


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
