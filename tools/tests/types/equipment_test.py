"""Tests for the types/equipment.py module."""

import pytest

# pyradox ships in the optional analysis group; only the Linux CI leg installs it.
pytest.importorskip("pyradox")

from tools.types.equipment import Equipment, LandEquipmentStats


def test_GivenEquipmentTree_WhenReadEquipment_ThenReturnsEquipment():
    import pyradox

    raw = pyradox.parse("""
		is_archetype = yes
		is_buildable = no
		type = infantry
		group_by = archetype

		priority = 10

		interface_category = interface_category_land

		upgrades = {
			inf_eq_gadjets
			inf_eq_mortars
			inf_eq_heavy_weapons
			inf_eq_cutting_corners
		}

		#Misc Abilities
		reliability = 0.9
		maximum_speed = 4
		supply_consumption = 0.01

		#Defensive Abilities
		defense = 12
		breakthrough = 0.25
		hardness = 0
		armor_value = 0

		#Offensive Abilities
		soft_attack = 1.25
		hard_attack = 0
		additional_collateral_damage = 0.125
		ap_attack = 0
		air_attack = 0
		#Space taken in convoy
		lend_lease_cost = 0.45

		build_cost_ic = 0.31
		resources = {
			steel = 1
		}
    """)
    parsed: Equipment = Equipment.read_equipment("infantry_weapons_type", raw, dict())
    assert parsed.is_archetype
    assert not parsed.is_buildable
    assert parsed.tag == "infantry_weapons_type"
    assert isinstance(parsed.stats, LandEquipmentStats)
    assert parsed.stats.reliability == 0.9
    assert parsed.stats.maximum_speed == 4
    assert parsed.stats.supply_consumption == 0.01
    assert parsed.stats.defense == 12
    assert parsed.stats.breakthrough == 0.25
    assert parsed.stats.hardness == 0
    assert parsed.stats.armor_value == 0
    assert parsed.stats.soft_attack == 1.25
    assert parsed.stats.hard_attack == 0
    assert parsed.stats.additional_collateral_damage == 0.125
    assert parsed.stats.ap_attack == 0
    assert parsed.stats.air_attack == 0
    assert parsed.stats.lend_lease_cost == 0.45
    assert parsed.stats.build_cost_ic == 0.31


def test_GivenEquipmentFile_WhenFromFile_ThenReturnsAllEquipmentTagsAndTypeLists(
    tmp_path,
):
    path = tmp_path / "equipment_file.txt"
    path.write_text(
        """
        equipments = {
            infantry_weapons_type = {
                is_archetype = yes
                type = infantry
                reliability = 0.9
                soft_attack = 1.25
            }
            infantry_weapons_1 = {
                archetype = infantry_weapons_type
                type = { infantry anti_tank }
                reliability = 0.95
                soft_attack = 2.5
            }
        }
        """,
        encoding="utf-8",
    )

    parsed = Equipment.from_file(str(path))

    assert set(parsed) == {"infantry_weapons_type", "infantry_weapons_1"}
    assert parsed["infantry_weapons_1"].types == ["infantry", "anti_tank"]
    assert parsed["infantry_weapons_1"].stats.reliability == 0.95
    assert parsed["infantry_weapons_1"].stats.soft_attack == 2.5


def test_GivenEquipmentInheritance_WhenParsed_ThenParentBlockIsAppliedBeforeOverride(
    tmp_path,
):
    path = tmp_path / "inheritance.txt"
    path.write_text(
        """
        equipments = {
            ship_base = {
                is_archetype = yes
                type = screen_ship
                naval_speed = 12
                surface_detection = 3
                lg_attack = 2
            }
            destroyer = {
                archetype = ship_base
                parent = ship_base
                type = screen_ship
                naval_speed = 13
                surface_detection = 4
            }
        }
        """,
        encoding="utf-8",
    )

    parsed = Equipment.from_file(str(path))

    assert parsed["destroyer"].stats.naval_speed == 13
    assert parsed["destroyer"].stats.surface_detection == 4
    assert parsed["destroyer"].stats.lg_attack == 2


def test_GivenEquipmentIndexLoader_WhenCalled_ThenSharedSingletonIsAvailable():
    assert callable(Equipment.load_default_equipment_index)
    assert callable(Equipment.get_equipment_index)
    assert Equipment.get_equipment_index() is Equipment.load_default_equipment_index()


def test_GivenEquipmentDirectory_WhenFromDirectory_ThenParsesRecursiveFilesAndCrossFileArchetypes(
    tmp_path,
):
    root = tmp_path / "equipment_root"
    root.mkdir()

    base_dir = root / "base"
    base_dir.mkdir()
    (base_dir / "land_base.txt").write_text(
        """
        equipments = {
            infantry_base = {
                is_archetype = yes
                type = infantry
                reliability = 0.9
                soft_attack = 1.25
            }
        }
        """,
        encoding="utf-8",
    )

    nested_dir = root / "nested"
    nested_dir.mkdir()
    (nested_dir / "derived.txt").write_text(
        """
        equipments = {
            infantry_derived = {
                archetype = infantry_base
                type = infantry
                reliability = 0.95
                soft_attack = 2.5
            }
        }
        """,
        encoding="utf-8",
    )

    parsed = Equipment.from_directory(str(root))

    assert set(parsed) == {"infantry_base", "infantry_derived"}
    assert parsed["infantry_derived"].archetype is not None
    assert parsed["infantry_derived"].archetype.tag == "infantry_base"
    assert parsed["infantry_derived"].stats.reliability == 0.95
    assert parsed["infantry_derived"].stats.soft_attack == 2.5
