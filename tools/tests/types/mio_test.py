"""Tests for the types/mio.py module."""

import pytest

from tools.types.equipment import Equipment, LandEquipmentStats
from tools.types.mio import EquipmentGroup, MIO


def test_GivenMioDefinition_WhenParsed_ThenEquipmentTypesAndTraitScopesExpand(tmp_path):
    org_path = tmp_path / "orgs"
    org_path.mkdir()
    (org_path / "mio.txt").write_text(
        """
        TEST_org = {
            allowed = { original_tag = TST }
            equipment_type = {
                mio_cat_all_utils
                infantry_weapons_type
            }

            trait = {
                token = trait_default
                name = trait_default
                equipment_bonus = { reliability = 0.05 }
            }

            trait = {
                token = trait_limited
                name = trait_limited
                limit_to_equipment_type = { mio_cat_only_small_ships }
                equipment_bonus = { reliability = 0.03 }
            }
        }
        """,
        encoding="utf-8",
    )

    groups = {
        "mio_cat_all_utils": EquipmentGroup(
            name="mio_cat_all_utils",
            types=["util_vehicle_type", "heavy_util_vehicle_type"],
        ),
        "mio_cat_only_small_ships": EquipmentGroup(
            name="mio_cat_only_small_ships",
            types=["patrol_boat", "corvette"],
        ),
    }

    parsed = MIO.from_directory(org_path, groups)
    mio = parsed["TEST_org"]

    assert mio.equipment_types == [
        "util_vehicle_type",
        "heavy_util_vehicle_type",
        "infantry_weapons_type",
    ]

    trait_by_token = {trait.token: trait for trait in mio.traits}
    assert trait_by_token["trait_default"].applies_to == mio.equipment_types
    assert trait_by_token["trait_limited"].applies_to == ["patrol_boat", "corvette"]


def test_GivenIncludedMio_WhenTraitOperationsAndTopLevelDeleteApply_ThenInheritedValuesAreUpdated(tmp_path):
    org_path = tmp_path / "orgs"
    org_path.mkdir()
    (org_path / "mio.txt").write_text(
        """
        BASE_org = {
            allowed = { original_tag = BAS }
            equipment_type = { base_type }
            research_categories = { CAT_base }

            trait = {
                token = trait_a
                name = trait_a
                equipment_bonus = { reliability = 0.01 }
            }

            trait = {
                token = trait_b
                name = trait_b
                equipment_bonus = { reliability = 0.02 }
            }
        }

        CHILD_org = {
            include = BASE_org
            delete_included_values = { research_categories }

            remove_trait = { trait_b }

            override_trait = {
                token = trait_a
                delete_included_values = { equipment_bonus }
                equipment_bonus = { reliability = 0.15 }
            }

            add_trait = {
                token = trait_c
                name = trait_c
                equipment_bonus = { reliability = 0.03 }
            }
        }
        """,
        encoding="utf-8",
    )

    parsed = MIO.from_directory(org_path, {})
    child = parsed["CHILD_org"]

    assert child.research_categories == []
    assert [trait.token for trait in child.traits] == ["trait_a", "trait_c"]


def test_GivenAllowedCountries_WhenOriginalTagsAreParsed_ThenOnlyExplicitCountriesAreIncluded(tmp_path):
    org_path = tmp_path / "orgs"
    org_path.mkdir()
    (org_path / "countries.txt").write_text(
        """
        ORG_with_tags = {
            allowed = {
                OR = {
                    original_tag = CHI
                    original_tag = HKG
                }
                is_usa_or_breakaway = yes
            }
            equipment_type = { rifle_type }
        }

        ORG_scripted_only = {
            allowed = { is_benelux_country = yes }
            equipment_type = { rifle_type }
        }
        """,
        encoding="utf-8",
    )

    parsed = MIO.from_directory(org_path, {})

    assert parsed["ORG_with_tags"].countries == ["CHI", "HKG"]
    assert parsed["ORG_scripted_only"].countries == []


def test_GivenTraitHierarchy_WhenParsed_ThenParentSemanticsArePreserved(tmp_path):
    org_path = tmp_path / "orgs"
    org_path.mkdir()
    (org_path / "parents.txt").write_text(
        """
        ORG_parent = {
            allowed = { original_tag = PAR }
            equipment_type = { base_type }

            trait = {
                token = root
                name = root
                equipment_bonus = { reliability = 0.01 }
            }

            trait = {
                token = branch_a
                name = branch_a
                parent = { root }
                equipment_bonus = { reliability = 0.02 }
            }

            trait = {
                token = branch_b
                name = branch_b
                all_parents = { root branch_a }
                equipment_bonus = { reliability = 0.03 }
            }

            trait = {
                token = branch_c
                name = branch_c
                any_parent = { branch_a branch_b }
                mutually_exclusive = { branch_b }
                equipment_bonus = { reliability = 0.04 }
            }
        }
        """,
        encoding="utf-8",
    )

    parsed = MIO.from_directory(org_path, {})
    traits = {trait.token: trait for trait in parsed["ORG_parent"].traits}

    assert traits["branch_a"].parent is traits["root"]
    assert [trait.token for trait in traits["branch_b"].all_parents] == ["root", "branch_a"]
    assert [trait.token for trait in traits["branch_c"].any_parents] == ["branch_a", "branch_b"]
    assert [trait.token for trait in traits["branch_c"].mutually_exclusive] == ["branch_b"]


def test_GivenIncludeCycle_WhenMioIsParsed_ThenValueErrorIsRaised(tmp_path):
    org_path = tmp_path / "orgs"
    org_path.mkdir()
    (org_path / "cycle.txt").write_text(
        """
        ORG_A = {
            include = ORG_B
            equipment_type = { a_type }
        }

        ORG_B = {
            include = ORG_A
            equipment_type = { b_type }
        }
        """,
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="include cycle"):
        MIO.from_directory(org_path, {})


def test_GivenEquipmentScope_WhenBonusStatsAreBuilt_ThenTraitBonusUsesEquipmentStats(tmp_path):
    org_path = tmp_path / "orgs"
    org_path.mkdir()
    (org_path / "scope.txt").write_text(
        """
        ALG_khenchela_arms_manufacturer = {
            allowed = { original_tag = ALG }
            equipment_type = { infantry_weapons_type }

            trait = {
                token = ALG_khenchela_trait_desert_hardened
                name = ALG_khenchela_trait_desert_hardened
                equipment_bonus = { reliability = 0.05 }
            }
        }
        """,
        encoding="utf-8",
    )

    equipment_index = {
        "infantry_weapons_type": Equipment(
            tag="infantry_weapons_type",
            is_archetype=True,
            archetype=None,
            types=["infantry"],
            is_buildable=True,
            stats=LandEquipmentStats(reliability=0.9),
        )
    }

    parsed = MIO.from_directory(org_path, {}, equipment_index=equipment_index)
    trait = parsed["ALG_khenchela_arms_manufacturer"].traits[0]

    assert isinstance(trait.bonuses, LandEquipmentStats)
