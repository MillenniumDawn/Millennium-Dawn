"""Tests for the equipment variant module/slot cross-check.

The engine silently drops a module assigned to a slot that does not exist on the
hull, or whose category is not in that slot's allowed set (upstream PR #2510).
These cover the resolver (archetype inheritance, cloned archetypes,
module->category, module-driven slot unlocks) and each finding kind against
synthetic hull/module fixtures.
"""

import random

import pytest
from equipment_module_slots import (
    _depth0_text,
    _iter_named_blocks,
    _parse_module_assignments,
    blank_comments,
    build_indexes,
    check_created_variant_references,
    check_created_variant_upgrades,
    check_created_variants,
    check_target_variant_role_icons,
    check_target_variant_upgrades,
    check_target_variants,
    created_variant_spans,
    entity_names_from_text,
    parse_variant_names,
    role_strip_frames,
)
from shared.suite import write_under as _write
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
\t\tfor_each = {
\t\t\tvariant_name = { find_and_replace = { chassis equipment } }
\t\t}
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


_SELECTION_CASES = {
    "greater": ("gun_slot > module_test_gun", {"module_test_gun"}),
    "less": ("gun_slot < module_test_gun", {"module_test_gun"}),
    "equals greater": ("gun_slot = > module_test_gun", {"module_test_gun"}),
    "nested range": (
        "gun_slot = { module > module_test_gun upgrade = current }",
        {"module_test_gun"},
    ),
    "repeated module": (
        "gun_slot = { module = module_test_gun module = module_test_banned }",
        {"module_test_gun", "module_test_banned"},
    ),
    "repeated any_of": (
        "gun_slot = { any_of = { module_test_gun } any_of = { module_test_banned } }",
        {"module_test_gun", "module_test_banned"},
    ),
    "module plus any_of": (
        "gun_slot = { module = module_test_gun any_of = { module_test_banned } }",
        {"module_test_gun", "module_test_banned"},
    ),
}


@pytest.mark.parametrize(
    ("text", "references"), _SELECTION_CASES.values(), ids=_SELECTION_CASES
)
def test_module_selection_reader(text, references):
    assignments = _parse_module_assignments(text, 0, len(text))
    assert len(assignments) == 1
    slot, refs, offset = assignments[0]
    assert (slot, set(refs), offset) == ("gun_slot", references, 0)


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
    assert index.hull_sources["test_boat_hull_1"] == "test_ship_hull_1"
    assert index.hull_sources["test_boat"] == "test_ship"
    assert index.hull_sources["test_ship_hull_1"] == "test_ship_hull_1"


def test_explicit_clone_keeps_its_own_unlock_source():
    explicit = "equipments = { test_boat_hull_1 = { archetype = test_ship module_slots = { } } }"
    index = build_indexes([HULLS, DUPLICATES, explicit], [])
    assert index.hull_sources["test_boat_hull_1"] == "test_boat_hull_1"
    assert index.hull_sources["test_boat_hull_2"] == "test_ship_hull_2"


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
    return [
        f.kind
        for f in check_created_variants(created_variant_spans(content), _indexes())
    ]


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


def test_created_variant_unindexed_type_flagged():
    # The real index covers every equipment type, so an unindexed one is a typo.
    content = _created(
        "medium_tank_chassis_1",
        "\t\t\t\t\t\tturret_type_slot = tank_medium_cannon_2\n",
    )
    assert _created_kinds(content) == ["unknown_hull"]


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
    findings = check_created_variants(created_variant_spans(content), _indexes())
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
    findings = check_created_variants(created_variant_spans(content), _indexes())
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
    findings = check_created_variants(created_variant_spans(content), _indexes())
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


def test_ai_validator_integration_reports_errors(tmp_path):
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
    assert issues[0].severity == "error"
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
    # A template that leaves a required slot empty can never be matched.
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


@pytest.mark.parametrize(
    "modules_body, category",
    [
        (
            "\t\t\t\tgun_slot = module_test_helipad\n",
            "EQUIPMENT VARIANT: module category not allowed in slot",
        ),
        (
            "\t\t\t\tgun_slot = module_test_exact_gun\n",
            "EQUIPMENT VARIANT: module forbidden on hull type",
        ),
    ],
)
def test_ai_validator_non_ship_slot_findings_are_errors(
    tmp_path, modules_body, category
):
    issues = _variant_issues(
        tmp_path,
        LIMIT_HULLS,
        "common/ai_equipment/TST_land.txt",
        _variant("lim_tank_hull_1", modules_body),
        Validator,
        "EQUIPMENT VARIANT",
    )
    assert [(i.severity, i.category) for i in issues] == [("error", category)]


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


# --- parser edge cases ------------------------------------------------------

EDGE_HULLS = """
equipments = {
\tedge_hull = {
\t\ttype = screen_ship
\t\tname = "Edge Class"
\t\tmodule_slots = {
\t\t\tgun_slot = {
\t\t\t\trequired = no
\t\t\t\tallowed_module_categories = { module_light_guns_category }
\t\t\t\tfuture_engine_rules = { unrecognised = yes }
\t\t\t}
\t\t}
\t\tmodule_count_limit = { category = module_light_guns_category }
\t\tmodule_count_limit = { count < 3 }
\t}
\tedge_orphan_hull = {
\t\tarchetype = missing_archetype
\t\tmodule_slots = inherit
\t}
}
duplicate_archetypes = {
\tedge_untyped_clone = {
\t\ttype = screen_ship
\t}
}
"""

EDGE_MODULES = """
equipment_modules = {
\tedge_base_gun = {
\t\tcategory = module_light_guns_category
\t\tforbid_equipment_type = { screen_ship }
\t}
\tedge_child_gun = {
\t\tcategory = module_light_guns_category
\t\tparent = edge_base_gun
\t}
\tedge_grandchild_gun = {
\t\tcategory = module_light_guns_category
\t\tparent = edge_child_gun
\t}
\tedge_nested_category_only = {
\t\tcan_convert_from = {
\t\t\tcategory = module_light_guns_category
\t\t}
\t}
}
"""


def _edge_index():
    return build_indexes([EDGE_HULLS], [EDGE_MODULES])


def _edge_created(body):
    return (
        "focus_tree = {\n"
        "\tfocus = {\n"
        "\t\tcompletion_reward = {\n"
        "\t\t\tcreate_equipment_variant = {\n"
        f"{body}"
        "\t\t\t}\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )


def test_quoted_name_does_not_break_hull_parsing():
    slots = _edge_index().hull_slots["edge_hull"] or {}
    gun = slots["gun_slot"]
    assert gun is not None
    assert gun.allowed == {"module_light_guns_category"}


def test_unrecognised_slot_sub_block_is_ignored():
    gun = (_edge_index().hull_slots["edge_hull"] or {})["gun_slot"]
    assert gun is not None and gun.allowed == {"module_light_guns_category"}


def test_malformed_count_limits_are_dropped():
    """A limit with no `count <`, or with neither category nor module, caps
    nothing — keeping it would invent a finding out of an unparsed block."""
    assert _edge_index().hull_count_limits["edge_hull"] == {}


def test_inherit_from_an_undefined_archetype_leaves_slots_unresolved():
    assert _edge_index().hull_slots["edge_orphan_hull"] is None


def test_duplicate_without_an_archetype_is_not_cloned():
    assert "edge_untyped_clone" not in _edge_index().hull_slots


def test_forbid_types_are_inherited_down_a_parent_chain():
    index = _edge_index()
    assert index.module_forbid_types["edge_child_gun"] == {"screen_ship"}
    assert index.module_forbid_types["edge_grandchild_gun"] == {"screen_ship"}


def test_a_category_only_visible_inside_a_nested_block_is_not_the_module_category():
    assert "edge_nested_category_only" not in _edge_index().module_category


def test_unbalanced_equipment_file_yields_no_hulls():
    assert (
        build_indexes(
            ["equipments = { broken_hull = { module_slots = { "], []
        ).hull_slots
        == {}
    )


def test_variant_without_a_type_is_skipped():
    content = _edge_created(
        '\t\t\t\tname = "Nameless"\n'
        "\t\t\t\tmodules = {\n"
        "\t\t\t\t\tgun_slot = edge_base_gun\n"
        "\t\t\t\t}\n"
    )
    assert check_created_variants(created_variant_spans(content), _edge_index()) == []


def test_variant_with_neither_type_nor_modules_is_skipped():
    content = _edge_created('\t\t\t\tname = "Nameless"\n')
    assert check_created_variants(created_variant_spans(content), _edge_index()) == []


def test_variant_naming_an_unindexed_hull_without_modules_is_flagged():
    content = _edge_created('\t\t\t\tname = "Ghost"\n\t\t\t\ttype = not_a_hull\n')
    findings = check_created_variants(created_variant_spans(content), _edge_index())
    assert [f.kind for f in findings] == ["unknown_hull"]


def test_variant_on_an_unresolvable_hull_is_skipped():
    content = _edge_created(
        '\t\t\t\tname = "Orphan"\n'
        "\t\t\t\ttype = edge_orphan_hull\n"
        "\t\t\t\tmodules = {\n"
        "\t\t\t\t\tno_such_slot = edge_base_gun\n"
        "\t\t\t\t}\n"
    )
    assert check_created_variants(created_variant_spans(content), _edge_index()) == []


def test_blocks_before_modules_do_not_hide_it():
    content = _edge_created(
        '\t\t\t\tname = "Upgraded"\n'
        "\t\t\t\ttype = edge_hull\n"
        "\t\t\t\tupgrades = {\n"
        "\t\t\t\t\tship_engine_upgrade = 1\n"
        "\t\t\t\t}\n"
        "\t\t\t\tmodules = {\n"
        "\t\t\t\t\tno_such_slot = edge_base_gun\n"
        "\t\t\t\t}\n"
    )
    assert [
        f.kind
        for f in check_created_variants(created_variant_spans(content), _edge_index())
    ] == ["unknown_slot"]


def test_empty_modules_block_yields_no_assignments():
    content = _edge_created(
        '\t\t\t\tname = "Bare"\n\t\t\t\ttype = edge_hull\n\t\t\t\tmodules = {}\n'
    )
    assert check_created_variants(created_variant_spans(content), _edge_index()) == []


def test_non_identifier_module_value_is_skipped():
    content = _edge_created(
        '\t\t\t\tname = "Odd"\n'
        "\t\t\t\ttype = edge_hull\n"
        "\t\t\t\tmodules = {\n"
        "\t\t\t\t\tgun_slot = 2\n"
        "\t\t\t\t}\n"
    )
    assert check_created_variants(created_variant_spans(content), _edge_index()) == []


def test_block_assignment_naming_nothing_is_skipped():
    content = _edge_created(
        '\t\t\t\tname = "Odd"\n'
        "\t\t\t\ttype = edge_hull\n"
        "\t\t\t\tmodules = {\n"
        "\t\t\t\t\tgun_slot = { }\n"
        "\t\t\t\t}\n"
    )
    assert check_created_variants(created_variant_spans(content), _edge_index()) == []


def test_parse_variant_names_skips_blocks_missing_a_field():
    content = _edge_created("\t\t\t\ttype = edge_hull\n") + _edge_created(
        '\t\t\t\tname = "Real"\n\t\t\t\ttype = edge_hull\n'
    )
    names = parse_variant_names(created_variant_spans(content))
    assert [name for _type, name, _line in names] == ["Real"]


def test_unreadable_equipment_file_is_skipped(tmp_path, caplog):
    import logging

    from equipment_module_slots import build_equipment_index

    units = tmp_path / "common" / "units" / "equipment"
    (units / "broken.txt").mkdir(parents=True)
    _write(tmp_path, "common/units/equipment/MD_edge.txt", EDGE_HULLS)

    with caplog.at_level(logging.WARNING):
        index = build_equipment_index(str(units))

    assert "broken.txt" in caplog.text
    assert "edge_hull" in index.hull_slots


# --- count-limit accounting -------------------------------------------------


def test_empty_assignment_does_not_charge_a_count_limit():
    content = _variant("lim_tank_hull_1", "\t\t\t\tgun_slot = empty\n")
    assert _kinds(content) == []


def test_category_reference_charges_the_category_limit():
    content = _variant(
        "lim_tank_hull_1",
        "\t\t\t\tgun_slot = module_light_guns_category\n"
        "\t\t\t\textra_gun_slot = module_light_guns_category\n",
    )
    assert _kinds(content) == ["count_limit_exceeded"]


def test_unknown_reference_charges_no_limit():
    content = _variant("lim_tank_hull_1", "\t\t\t\tgun_slot = not_a_module\n")
    assert _kinds(content) == ["unknown_module"]


# --- unsupported variant upgrades -------------------------------------------

# The archetype lists test_nsb_upgrade; hull_1 inherits it, hull_2 declares its
# own list, and the duplicate clones the whole family (the SIBMAS shape).
UPGRADE_HULLS = """
equipments = {
\tup_tank = {
\t\tis_archetype = yes
\t\tupgrades = { test_nsb_upgrade }
\t}
\tup_tank_1 = {
\t\tarchetype = up_tank
\t}
\tup_tank_2 = {
\t\tarchetype = up_tank
\t\tupgrades = { other_upgrade }
\t}
\tup_tank_3 = {
\t\tarchetype = up_tank
\t\tparent = up_tank_2
\t}
\tup_slotted_1 = {
\t\tarchetype = up_tank
\t\tmodule_slots = {
\t\t\tgun_slot = {
\t\t\t\tupgrades = { nested_upgrade }
\t\t\t}
\t\t}
\t}
}
duplicate_archetypes = {
\tup_clone = {
\t\tarchetype = up_tank
\t}
}
"""


def _upgrade_index():
    return build_indexes([UPGRADE_HULLS], [])


def _upgraded(hull, upgrades_body):
    return (
        "create_equipment_variant = {\n"
        '\tname = "Upgraded"\n'
        f"\ttype = {hull}\n"
        "\tupgrades = {\n"
        f"{upgrades_body}"
        "\t}\n"
        "}\n"
    )


def _upgrade_findings(hull, upgrades_body):
    return check_created_variant_upgrades(
        created_variant_spans(_upgraded(hull, upgrades_body)), _upgrade_index()
    )


def test_unsupported_upgrade_is_flagged_with_engine_wording():
    findings = _upgrade_findings("up_tank_1", "\t\tlegacy_upgrade = 0\n")
    assert [f.kind for f in findings] == ["unsupported_upgrade"]
    assert findings[0].line == 5
    assert findings[0].message == (
        "'Upgraded' - Type 'up_tank_1' does not support upgrades 'legacy_upgrade'"
    )


def test_supported_upgrade_on_inherited_list_passes():
    assert _upgrade_findings("up_tank_1", "\t\ttest_nsb_upgrade = 2\n") == []


def test_only_the_unsupported_upgrade_is_flagged():
    findings = _upgrade_findings(
        "up_tank_1", "\t\ttest_nsb_upgrade = 2\n\t\tlegacy_upgrade = 1\n"
    )
    assert [f.message.rsplit("'", 2)[1] for f in findings] == ["legacy_upgrade"]


def test_own_upgrade_list_overrides_the_archetype():
    assert _upgrade_findings("up_tank_2", "\t\tother_upgrade = 1\n") == []
    findings = _upgrade_findings("up_tank_2", "\t\ttest_nsb_upgrade = 1\n")
    assert [f.kind for f in findings] == ["unsupported_upgrade"]


def test_parent_upgrade_list_wins_over_the_archetype():
    assert _upgrade_findings("up_tank_3", "\t\tother_upgrade = 1\n") == []
    findings = _upgrade_findings("up_tank_3", "\t\ttest_nsb_upgrade = 1\n")
    assert [f.kind for f in findings] == ["unsupported_upgrade"]


def test_nested_upgrades_block_is_not_the_equipment_list():
    assert _upgrade_findings("up_slotted_1", "\t\ttest_nsb_upgrade = 1\n") == []
    assert [
        f.kind for f in _upgrade_findings("up_slotted_1", "\t\tnested_upgrade = 1\n")
    ] == ["unsupported_upgrade"]


def test_cloned_family_inherits_upgrades():
    assert _upgrade_findings("up_clone_1", "\t\ttest_nsb_upgrade = 1\n") == []
    assert [
        f.kind for f in _upgrade_findings("up_clone_2", "\t\ttest_nsb_upgrade = 1\n")
    ] == ["unsupported_upgrade"]
    assert [
        f.kind for f in _upgrade_findings("up_clone_1", "\t\tlegacy_upgrade = 1\n")
    ] == ["unsupported_upgrade"]


def test_variant_of_unknown_type_has_no_upgrade_finding():
    assert _upgrade_findings("not_a_type", "\t\tlegacy_upgrade = 1\n") == []


def test_type_without_any_upgrade_list_is_skipped():
    index = build_indexes([LIMIT_HULLS], [MODULES])
    content = _upgraded("lim_tank_hull_1", "\t\tlegacy_upgrade = 1\n")
    assert check_created_variant_upgrades(created_variant_spans(content), index) == []


def test_oob_validator_reports_unsupported_upgrade(tmp_path):
    from validate_oob_units import Validator as OobValidator

    issues = _variant_issues(
        tmp_path,
        UPGRADE_HULLS,
        "common/national_focus/07_test.txt",
        _upgraded("up_tank_1", "\t\tlegacy_upgrade = 0\n\t\ttest_nsb_upgrade = 1\n"),
        OobValidator,
        "EQUIPMENT VARIANT: unsupported upgrade",
    )
    assert len(issues) == 1
    assert issues[0].severity == "error"
    assert issues[0].file == "common/national_focus/07_test.txt"
    assert "legacy_upgrade" in issues[0].message


# --- rules ported from the equipment designer -------------------------------

RULE_HULLS = """
equipments = {
\trule_plane = {
\t\tis_archetype = yes
\t\ttype = { fighter }
\t\ttype_override = main_slot
\t\tallowed_types = { fighter cas }
\t\tmodule_slots = {
\t\t\tmain_slot = { allowed_module_categories = { cat_gun } }
\t\t\taux_slot = { allowed_module_categories = { cat_bomb } }
\t\t}
\t}
\trule_plane_1 = { archetype = rule_plane module_slots = inherit }
\trule_rifle = { is_archetype = yes upgrades = { rule_upgrade } }
\trule_rifle_1 = { archetype = rule_rifle }
}
duplicate_archetypes = {
\trule_clone = { archetype = rule_plane type = { fighter } }
}
"""

# Its own file: a hull-type marker makes every hull in a file a ship.
RULE_SHIP_HULLS = """
equipments = {
\trule_ship = {
\t\tis_archetype = yes
\t\ttype = screen_ship
\t\tupgrades = { rule_upgrade }
\t\tmodule_slots = { main_slot = { } }
\t}
\trule_ship_1 = { archetype = rule_ship module_slots = inherit }
}
"""

RULE_MODULES = """
equipment_modules = {
\tgun_fighter = { category = cat_gun add_equipment_type = { fighter } }
\tgun_cas = { category = cat_gun add_equipment_type = { cas } }
\tgun_bomber = { category = cat_gun add_equipment_type = strategic_bomber }
\tgun_bomber_child = { category = cat_gun parent = gun_bomber }
\tgun_plain = { category = cat_gun }
\tgun_no_bombs = {
\t\tcategory = cat_gun
\t\tforbid_equipment_type_exact_match_for_category = { cat_bomb = fighter }
\t}
\tbomb = { category = cat_bomb }
}
"""

RULE_UPGRADES = """
upgrades = {
\trule_upgrade = { max_level = 5 }
}
"""


def _rule_index():
    return build_indexes([RULE_HULLS, RULE_SHIP_HULLS], [RULE_MODULES], [RULE_UPGRADES])


def _main_slot(module, hull="rule_plane_1", extra=""):
    return (
        f'create_equipment_variant = {{ name = "D" type = {hull} '
        f"modules = {{ main_slot = {module} {extra} }} }}\n"
    )


# rule: {case: (variant text, expected kinds)}
_VARIANT_RULE_CASES = {
    "archetype as type": (
        'create_equipment_variant = { name = "D" type = rule_plane }',
        ["archetype_type"],
    ),
    "cloned archetype as type": (
        'create_equipment_variant = { name = "D" type = rule_clone }',
        ["archetype_type"],
    ),
    "concrete type": (
        'create_equipment_variant = { name = "D" type = rule_plane_1 }',
        [],
    ),
    "unknown type without modules": (
        'create_equipment_variant = { name = "D" type = rule_plane_9 }',
        ["unknown_hull"],
    ),
    "dynamic type": ('create_equipment_variant = { name = "D" type = var:x }', []),
    "modules on a non-modular type": (
        "create_equipment_variant = { type = rule_rifle_1 modules = { a = b } }",
        ["modules_on_non_modular"],
    ),
    "empty modules on a non-modular type": (
        "create_equipment_variant = { type = rule_rifle_1 modules = { } }",
        [],
    ),
    "weapon sets the hull's own type": (_main_slot("gun_fighter"), []),
    "weapon sets an allowed type": (_main_slot("gun_cas"), []),
    "weapon sets a type the hull refuses": (
        _main_slot("gun_bomber"),
        ["type_override_role"],
    ),
    "refused type through module parent": (
        _main_slot("gun_bomber_child"),
        ["type_override_role"],
    ),
    "refused type on a clone": (
        _main_slot("gun_bomber", "rule_clone_1"),
        ["type_override_role"],
    ),
    "weapon adds no type": (_main_slot("gun_plain"), []),
    "category reference stays open": (_main_slot("cat_gun"), []),
    "one alternative fits": (
        "create_equipment_variant = { type = rule_plane_1 modules = "
        "{ main_slot = { any_of = { gun_bomber gun_cas } } } }",
        [],
    ),
    "module refuses a category": (
        _main_slot("gun_no_bombs", extra="aux_slot = bomb"),
        ["exact_category_conflict"],
    ),
    "module without the other category": (_main_slot("gun_no_bombs"), []),
}


@pytest.mark.parametrize(
    ("text", "kinds"), _VARIANT_RULE_CASES.values(), ids=_VARIANT_RULE_CASES
)
def test_variant_rules(text, kinds):
    findings = check_created_variants(created_variant_spans(text), _rule_index())
    assert [f.kind for f in findings] == kinds
    target = text.replace("create_equipment_variant", "target_variant")
    assert [f.kind for f in check_target_variants(target, _rule_index())] == kinds


def test_unknown_type_names_the_definition_spelling():
    text = "create_equipment_variant = { type = Rule_Plane_1 }"
    (finding,) = check_created_variants(created_variant_spans(text), _rule_index())
    assert "spelled 'rule_plane_1'" in finding.message


def test_exact_category_conflict_needs_a_single_type_hull():
    hulls = RULE_HULLS.replace("type = { fighter }", "type = { fighter cas }", 1)
    index = build_indexes([hulls], [RULE_MODULES], [RULE_UPGRADES])
    text = _main_slot("gun_no_bombs", extra="aux_slot = bomb")
    assert check_created_variants(created_variant_spans(text), index) == []


_UPGRADE_RULE_BODY = "create_equipment_variant = { type = HULL upgrades = { BODY } }"

# level rule: {case: (hull, upgrades body, expected kinds)}
_UPGRADE_LEVEL_CASES = {
    "at max": ("rule_rifle_1", "rule_upgrade = 5", []),
    "over max": ("rule_rifle_1", "rule_upgrade = 6", ["invalid_upgrade_level"]),
    "negative": ("rule_rifle_1", "rule_upgrade = -1", ["invalid_upgrade_level"]),
    "undefined": ("rule_rifle_1", "other_upgrade = 1", ["undefined_upgrade"]),
    "weighted within max": (
        "rule_rifle_1",
        "rule_upgrade = { base = 3 modifier = { add = 2 has_war = yes } }",
        [],
    ),
    "weighted over max": (
        "rule_rifle_1",
        "rule_upgrade = { base = 4 modifier = { add = 2 has_war = yes } }",
        ["invalid_upgrade_level"],
    ),
    "negative add hides a base over max": (
        "rule_rifle_1",
        "rule_upgrade = { base = 7 modifier = { add = -2 has_war = yes } }",
        ["invalid_upgrade_level"],
    ),
    "exclusive modifiers stay unresolved": (
        "rule_rifle_1",
        "rule_upgrade = { base = 3 modifier = { add = 2 has_war = yes } "
        "modifier = { add = 2 has_war = no } }",
        [],
    ),
    "factor stays unresolved": (
        "rule_rifle_1",
        "rule_upgrade = { base = 9 modifier = { factor = 0.5 has_war = yes } }",
        [],
    ),
    "ship": ("rule_ship_1", "rule_upgrade = 1", ["ship_upgrade"]),
}


@pytest.mark.parametrize(
    ("hull", "body", "kinds"),
    _UPGRADE_LEVEL_CASES.values(),
    ids=_UPGRADE_LEVEL_CASES,
)
def test_upgrade_level_rules(hull, body, kinds):
    text = _UPGRADE_RULE_BODY.replace("HULL", hull).replace("BODY", body)
    created = check_created_variant_upgrades(created_variant_spans(text), _rule_index())
    assert [f.kind for f in created] == kinds
    target = text.replace("create_equipment_variant", "target_variant")
    assert [f.kind for f in check_target_variant_upgrades(target, _rule_index())] == (
        kinds
    )


def test_target_upgrade_outside_the_type_list_is_flagged():
    index = build_indexes(
        [RULE_HULLS],
        [RULE_MODULES],
        [RULE_UPGRADES + "upgrades = { spare = { max_level = 1 } }"],
    )
    text = "target_variant = { type = rule_rifle_1 upgrades = { spare = 1 } }"
    (finding,) = check_target_variant_upgrades(text, index)
    assert finding.kind == "unsupported_upgrade"
    assert finding.message == "Type 'rule_rifle_1' does not support upgrades 'spare'"


_FRAMES = {
    "GFX_naval_equipment_role_icons": 3,
    "GFX_plane_niche_icon_strip": 2,
    "GFX_niche_icon_strip": 1,
}

# role icon: {case: (hull, index, expected kinds)}
_ROLE_ICON_CASES = {
    "ship in range": ("rule_ship_1", 3, []),
    "ship over": ("rule_ship_1", 4, ["role_icon_out_of_range"]),
    "plane uses its own strip": ("rule_plane_1", 3, ["role_icon_out_of_range"]),
    "other uses the niche strip": ("rule_rifle_1", 2, ["role_icon_out_of_range"]),
    "zero": ("rule_ship_1", 0, ["role_icon_out_of_range"]),
}


@pytest.mark.parametrize(
    ("hull", "role", "kinds"), _ROLE_ICON_CASES.values(), ids=_ROLE_ICON_CASES
)
def test_role_icon_range(hull, role, kinds):
    created = created_variant_spans(
        f"create_equipment_variant = {{ type = {hull} role_icon_index = {role} }}"
    )
    assert [
        f.kind
        for f in check_created_variant_references(
            created, _rule_index(), {}, None, _FRAMES
        )
    ] == kinds
    target = (
        f"group = {{ design = {{ role_icon_index = {role} "
        f"target_variant = {{ type = {hull} }} }} }}"
    )
    assert [
        f.kind for f in check_target_variant_role_icons(target, _rule_index(), _FRAMES)
    ] == kinds


def test_role_strip_frames_reads_only_declared_strips():
    frames = role_strip_frames(
        [
            'spriteType = { name = "GFX_niche_icon_strip" texturefile = "a" noOfFrames = 10 }',
            'spriteType = { name = "GFX_plane_niche_icon_strip" texturefile = "a" }',
            'spriteType = { name = "GFX_niche_icon_strip_selected" noOfFrames = 99 }',
        ]
    )
    assert frames == {"GFX_niche_icon_strip": 10}


# references: {case: (variant body, country, expected kinds)}
_REFERENCE_CASES = {
    "known name group": ("name_group = TST_NAMES", "TST", []),
    "unknown name group": ("name_group = NOPE", "TST", ["unknown_name_group"]),
    "name group of another country": (
        "name_group = TST_NAMES",
        "OTH",
        ["name_group_country"],
    ),
    "unscoped file skips the country rule": ("name_group = TST_NAMES", None, []),
    "name group for anyone": ("name_group = ANY_NAMES", "OTH", []),
    "known model": ('model = "Known_Entity"', None, []),
    "unknown model": ('model = "missing_entity"', None, ["unknown_model"]),
}


@pytest.mark.parametrize(
    ("body", "country", "kinds"), _REFERENCE_CASES.values(), ids=_REFERENCE_CASES
)
def test_variant_references(body, country, kinds):
    variants = created_variant_spans(
        f"create_equipment_variant = {{ type = rule_plane_1 {body} }}"
    )
    findings = check_created_variant_references(
        variants,
        _rule_index(),
        {"TST_NAMES": {"TST"}, "ANY_NAMES": set()},
        {"known_entity"},
        {},
        country,
    )
    assert [f.kind for f in findings] == kinds


def test_model_check_needs_entity_files():
    variants = created_variant_spans(
        'create_equipment_variant = { type = rule_plane_1 model = "x" }'
    )
    assert check_created_variant_references(variants, _rule_index(), {}, None, {}) == []


def test_entity_names_read_quoted_and_bare_names_only_from_entities():
    raw = (
        '# entity = { name = "commented" }\n'
        'pdxmesh = { name = "not_an_entity" }\n'
        'entity = { pdxmesh = "x" name = "Quoted_Entity" }\n'
        "objectTypes = { entity = { name = Bare_Entity } }\n"
    )
    assert entity_names_from_text(raw) == {"quoted_entity", "bare_entity"}


# severity: {case: (rel, kind's category, content, severity)}
_VALIDATOR_SEVERITY_CASES = {
    "gating rule": (
        "common/national_focus/07_test.txt",
        "EQUIPMENT VARIANT: upgrade level out of range",
        'create_equipment_variant = { name = "D" type = rule_rifle_1 '
        "upgrades = { rule_upgrade = 6 } }",
        "error",
    ),
    "advisory rule": (
        "common/national_focus/07_test.txt",
        "SHIP VARIANT: upgrades on a ship",
        'create_equipment_variant = { name = "D" type = rule_ship_1 '
        "upgrades = { rule_upgrade = 1 } }",
        "warning",
    ),
    "unknown type gates": (
        "common/national_focus/07_test.txt",
        "EQUIPMENT VARIANT: unknown hull type",
        'create_equipment_variant = { name = "D" type = rule_plane_9 }',
        "error",
    ),
    "created archetype gates": (
        "common/national_focus/07_test.txt",
        "EQUIPMENT VARIANT: type is an archetype",
        'create_equipment_variant = { name = "D" type = rule_plane }',
        "error",
    ),
}


def _rule_tree(tmp_path, rel, content):
    _write(tmp_path, "common/units/equipment/MD_rules.txt", RULE_HULLS)
    _write(tmp_path, "common/units/equipment/MD_rule_ships.txt", RULE_SHIP_HULLS)
    _write(tmp_path, "common/units/equipment/modules/MD_rules.txt", RULE_MODULES)
    _write(tmp_path, "common/units/equipment/upgrades/MD_rules.txt", RULE_UPGRADES)
    _write(tmp_path, rel, content)


@pytest.mark.parametrize(
    ("rel", "category", "content", "severity"),
    _VALIDATOR_SEVERITY_CASES.values(),
    ids=_VALIDATOR_SEVERITY_CASES,
)
def test_oob_validator_rule_severity(tmp_path, rel, category, content, severity):
    from validate_oob_units import Validator as OobValidator

    _rule_tree(tmp_path, rel, content)
    validator = OobValidator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.validate_created_variant_modules()
    (issue,) = [i for i in validator._issues if i.category == category]
    assert issue.severity == severity
    assert issue.file == rel


def test_oob_validator_reads_references_from_the_tree(tmp_path):
    from validate_oob_units import Validator as OobValidator

    _rule_tree(
        tmp_path,
        "history/countries/TST - Test.txt",
        'create_equipment_variant = { name = "A" type = rule_plane_1 name_group = NOPE '
        'model = "nope_entity" }\n'
        'create_equipment_variant = { name = "B" type = rule_ship_1 role_icon_index = 9 '
        'name_group = OTH_NAMES model = "MOD_entity" }\n'
        'create_equipment_variant = { name = "C" type = rule_plane_1 model = "vanilla_probe" }\n',
    )
    _write(
        tmp_path,
        "common/units/names_ships/names.txt",
        "OTH_NAMES = { for_countries = { OTH } }\n",
    )
    _write(tmp_path, "gfx/entities/mod.asset", 'entity = { name = "mod_entity" }\n')
    _write(
        tmp_path,
        "interface/equipment.gfx",
        'spriteType = { name = "GFX_naval_equipment_role_icons" noOfFrames = 3 }\n',
    )
    validator = OobValidator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.validate_created_variant_modules()
    assert {(i.category, i.severity) for i in validator._issues} == {
        ("EQUIPMENT VARIANT: unknown name_group", "error"),
        ("EQUIPMENT VARIANT: unknown model", "error"),
        ("SHIP VARIANT: name_group for another country", "warning"),
        ("SHIP VARIANT: role_icon_index out of range", "warning"),
    }
    # "vanilla_probe" has no entity anywhere, so it is the second model finding.
    models = [i for i in validator._issues if "model" in i.category]
    assert sorted("nope_entity" in i.message for i in models) == [False, True]


def test_vanilla_entity_manifest_covers_vanilla_models(tmp_path, monkeypatch):
    import validate_oob_units as oob

    manifest = tmp_path / "manifest.txt"
    manifest.write_text("# header\nvanilla_probe\n", encoding="utf-8")
    monkeypatch.setattr(oob, "_VANILLA_ENTITIES", str(manifest))
    _rule_tree(
        tmp_path,
        "history/countries/TST - Test.txt",
        'create_equipment_variant = { name = "C" type = rule_plane_1 model = "vanilla_probe" }\n',
    )
    _write(tmp_path, "gfx/entities/mod.asset", 'entity = { name = "mod_entity" }\n')
    validator = oob.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.validate_created_variant_modules()
    assert not validator._issues


# severity: {case: (category, design body, severity)}
_AI_SEVERITY_CASES = {
    "upgrade over max": (
        "EQUIPMENT VARIANT: upgrade level out of range",
        "target_variant = { type = rule_rifle_1 upgrades = { rule_upgrade = 6 } }",
        "error",
    ),
    "unknown type without modules": (
        "EQUIPMENT VARIANT: unknown hull type",
        "target_variant = { type = rule_plane_9 }",
        "error",
    ),
    "archetype only advises": (
        "EQUIPMENT VARIANT: type is an archetype",
        "target_variant = { type = rule_plane }",
        "warning",
    ),
    "role icon": (
        "NAVAL VARIANT: role_icon_index out of range",
        "role_icon_index = 9 target_variant = { type = rule_ship_1 }",
        "warning",
    ),
}


@pytest.mark.parametrize(
    ("category", "body", "severity"),
    _AI_SEVERITY_CASES.values(),
    ids=_AI_SEVERITY_CASES,
)
def test_ai_validator_rule_severity(tmp_path, category, body, severity):
    _rule_tree(
        tmp_path,
        "common/ai_equipment/TST.txt",
        f"group = {{ category = land roles = {{ r }} design = {{ {body} }} }}\n",
    )
    _write(
        tmp_path,
        "interface/equipment.gfx",
        'spriteType = { name = "GFX_naval_equipment_role_icons" noOfFrames = 3 }\n',
    )
    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.run_validations()
    (issue,) = [i for i in validator._issues if i.category == category]
    assert issue.severity == severity


def test_one_walk_feeds_every_created_variant_check_with_real_lines():
    # The second design sits after the first, so a line counted from the
    # modules block instead of the file start would come out short.
    first = _created(
        "test_ship_hull_1", "\t\t\t\t\t\tnonexistent_slot = module_test_gun\n"
    )
    second = _created("test_ship_hull_1", "\t\t\t\t\t\tother_slot = module_test_gun\n")
    variants = created_variant_spans(
        "# create_equipment_variant = { }\n" + first + second.rstrip("\n")
    )
    findings = check_created_variants(variants, _indexes())
    assert [(f.kind, f.line) for f in findings] == [
        ("unknown_slot", 11),
        ("unknown_slot", 27),
    ]
    assert parse_variant_names(variants) == [
        ("test_ship_hull_1", "Test Class", 7),
        ("test_ship_hull_1", "Test Class", 23),
    ]


def test_named_block_walk_reaches_the_last_block_past_unrelated_siblings():
    text = blank_comments(
        '# create_equipment_variant = { name = "Commented" }\n'
        "a = { b = { } }\n"
        'c = { d = { create_equipment_variant = { name = "First" } } }\n'
        "e = { }\n"
        'f = { create_equipment_variant = { name = "Middle" } }\n'
        'log = "create_equipment_variant"\n'
        'create_equipment_variant = { name = "Last" }'
    )
    spans = _iter_named_blocks(text, 0, len(text), "create_equipment_variant")
    assert [text[lo:hi].strip() for lo, hi in spans] == [
        'name = "First"',
        'name = "Middle"',
        'name = "Last"',
    ]


def _walk_depth0_text(text, lo, hi):
    """The per-character walk _depth0_text replaced."""
    out = []
    depth = 0
    in_str = False
    for i in range(lo, hi):
        c = text[i]
        if c == '"' and text[i - 1] != "\\":
            in_str = not in_str
            if depth == 0:
                out.append(c)
        elif c == "{" and not in_str:
            depth += 1
        elif c == "}" and not in_str:
            depth -= 1
        elif depth == 0:
            out.append(c)
    return "".join(out)


def test_depth0_text_matches_the_character_walk():
    """Quoted braces stay text, an escaped quote does not toggle, a stray `}`
    hides the rest, and index 0 checks the last character for a backslash."""
    rng = random.Random(20261002)
    fixed = ['"a{b}"\\', 'x = { y } z "{" w', "} a { b", '\\" { "} c']
    texts = fixed + [
        "".join(rng.choice('{}"\\ a=\n') for _ in range(rng.randint(0, 24)))
        for _ in range(300)
    ]
    for text in texts:
        for lo in range(len(text) + 1):
            for hi in range(lo, len(text) + 1):
                assert _depth0_text(text, lo, hi) == _walk_depth0_text(text, lo, hi), (
                    text,
                    lo,
                    hi,
                )
