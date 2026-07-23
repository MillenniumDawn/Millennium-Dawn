"""Tests for the naval variant module/slot cross-check.

The engine silently drops a module assigned to a slot that does not exist on the
hull, or whose category is not in that slot's allowed set (upstream PR #2510).
These cover the resolver (archetype inheritance, module->category) and each
finding kind against synthetic hull/module fixtures.
"""

from naval_module_slots import build_indexes, check_naval_variants
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

MODULES = """
equipment_modules = {
\tmodule_test_gun = {
\t\tcategory = module_light_guns_category
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
}
"""


def _indexes():
    return build_indexes([HULLS], [MODULES])


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
    hull_slots, module_category, known = _indexes()
    return [
        f.kind
        for f in check_naval_variants(content, hull_slots, module_category, known)
    ]


def test_build_indexes_resolves_inheritance_and_categories():
    hull_slots, module_category, known = _indexes()
    assert (
        module_category["module_test_plain_fc"] == "module_fire_control_system_category"
    )
    # can_convert_from's module_category must not be mistaken for the module's own.
    assert module_category["module_test_gun"] == "module_light_guns_category"
    # hull_1 inherits the archetype's two slots.
    assert set(hull_slots["test_ship_hull_1"]) == {
        "fixed_ship_battery_slot",
        "fixed_ship_fire_control_system_slot",
    }
    assert "module_screen_fire_control_system_category" in known


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


def test_non_naval_template_ignored():
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
    assert _kinds(content) == []


def _write(tmp_path, rel, body):
    p = tmp_path / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    return p


def test_validator_integration_reports_warnings(tmp_path):
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
    assert naval[0].severity == "warning"
    assert naval[0].file == "common/ai_equipment/TST_naval.txt"
    assert "module_test_plain_fc" in naval[0].message
