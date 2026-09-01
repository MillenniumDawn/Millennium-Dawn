"""Tests for `equipment_stats.py` (which stats each equipment token declares)."""

import equipment_stats as S

_AA = """
equipments = {
\tAA_Equipment = {
\t\tis_archetype = yes
\t\ttype = {
\t\t\tinfantry
\t\t\tanti_air
\t\t}
\t\tupgrades = {
\t\t\tAA_Fire_Control
\t\t}
\t\treliability = 0.9
\t\tarmor_value = 0
\t\t# soft_attack = 3
\t\tbuild_cost_ic = 0.9
\t}

\tAnti_Air_0 = {
\t\tarchetype = AA_Equipment
\t\tair_attack = 0.375
\t}
}
"""


def _index(equipment="", modules="", groups=""):
    return S.build_index([equipment], [modules], [groups])


def _aa_stats():
    return _index(_AA).resolve("AA_Equipment")


def test_variant_stats_union_into_archetype():
    stats = _aa_stats()
    assert "reliability" in stats
    assert "air_attack" in stats  # declared only by the variant


def test_zero_valued_stat_is_not_a_base():
    # armor_value = 0 is declared but a percentage of it is still 0.
    assert "armor_value" not in _aa_stats()


def test_commented_out_stat_is_not_declared():
    assert "soft_attack" not in _aa_stats()


def test_block_valued_key_does_not_swallow_the_next_stat():
    # `upgrades = { ... }` sits directly above reliability in the fixture.
    assert "reliability" in _aa_stats()


def test_type_category_resolves_to_member_stats():
    index = _index(_AA)
    assert index.resolve("anti_air") == index.resolve("AA_Equipment")


def test_unknown_token_resolves_to_none():
    assert _index(_AA).resolve("helicopter_equipment") is None


_HULL = """
equipments = {
\ttank_chassis = {
\t\tis_archetype = yes
\t\treliability = 0.8
\t\tmodule_slots = {
\t\t\tmain_armament_slot = {
\t\t\t\tallowed_module_categories = {
\t\t\t\t\tmodule_gun_category
\t\t\t\t}
\t\t\t}
\t\t}
\t}
}
"""

_MODULES = """
equipment_modules = {
\ttank_gun = {
\t\tcategory = module_gun_category
\t\tadd_stats = {
\t\t\thard_attack = 5
\t\t}
\t}
\tship_hull = {
\t\tcategory = module_ship_category
\t\tadd_stats = {
\t\t\tmax_organisation = 20
\t\t}
\t}
}
"""


def test_module_stats_reach_only_hulls_whose_slots_accept_them():
    index = _index(_HULL, _MODULES)
    stats = index.resolve("tank_chassis")
    assert "hard_attack" in stats
    # The ship module is in no slot this hull accepts — pooling every module is
    # what handed tank chassis a max_organisation they do not have.
    assert "max_organisation" not in stats


def test_plain_archetype_gets_no_module_stats():
    index = _index(_AA + _HULL, _MODULES)
    assert "hard_attack" not in index.resolve("AA_Equipment")


_DUPLICATES = """
equipments = {
\tsmall_plane_airframe = {
\t\tis_archetype = yes
\t\tair_range = 1000
\t}
}
duplicate_archetypes = {
\tsmall_plane_cas_airframe = {
\t\tarchetype = small_plane_airframe
\t\ttype = cas
\t\tfor_each = {
\t\t\tair_ground_attack = { set = 3 }
\t\t\tair_superiority = { set = 0 }
\t\t}
\t\tsubstitute = cv_small_plane_cas_airframe
\t}
}
"""


def test_duplicate_archetype_inherits_base_and_adds_for_each():
    stats = _index(_DUPLICATES).resolve("small_plane_cas_airframe")
    assert "air_range" in stats  # from the base archetype
    assert "air_ground_attack" in stats  # from for_each
    assert "air_superiority" not in stats  # for_each set it to 0


def test_substitute_registers_the_carrier_twin():
    index = _index(_DUPLICATES)
    assert index.resolve("cv_small_plane_cas_airframe") == index.resolve(
        "small_plane_cas_airframe"
    )


_GROUPS = """
mio_cat_frigates = {
\tequipment_type = {
\t\tfrigate
\t\tstealth_frigate
\t}
}
"""


def test_group_expands_to_members():
    index = _index(_AA, groups=_GROUPS)
    assert index.expand("mio_cat_frigates") == ["frigate", "stealth_frigate"]


def test_non_group_token_expands_to_itself():
    assert _index(_AA, groups=_GROUPS).expand("AA_Equipment") == ["AA_Equipment"]


_SPLIT = """
equipments = {
\tsplit_entry = {
\t\tis_archetype = yes
\t\treliability = 0.9
\t}
}
equipments = {
\tsplit_entry = {
\t\ttype = escort
\t\tair_attack = 0.5
\t}
}
"""


def test_an_entry_restated_in_a_second_block_unions_its_stats_and_types():
    index = _index(_SPLIT)
    stats = index.resolve("split_entry")
    assert {"reliability", "air_attack"} <= stats
    assert index.resolve("escort") == stats


_EDGE_DUPLICATES = """
equipments = {
\tedge_base = {
\t\tis_archetype = yes
\t\tair_range = 1000
\t}
}
duplicate_archetypes = {
\tedge_clone = {
\t\tarchetype = edge_base
\t\tvariant_name = { find_and_replace = { chassis equipment } }
\t\tfor_each = {
\t\t\tair_ground_attack = { set = 3 }
\t\t}
\t}
}
"""


def test_clone_without_a_substitute_registers_only_itself():
    index = _index(_EDGE_DUPLICATES)
    stats = index.resolve("edge_clone")
    assert {"air_range", "air_ground_attack"} <= stats
    assert index.resolve("cv_edge_clone") is None


_UNLOCK_HULLS = """
equipments = {
\tunlock_hull = {
\t\tis_archetype = yes
\t\treliability = 0.8
\t\tmodule_slots = {
\t\t\tgun_slot = {
\t\t\t\tallowed_module_categories = { gun_category }
\t\t\t}
\t\t\tfree_slot = {
\t\t\t\trequired = no
\t\t\t}
\t\t}
\t}
\tbare_hull = {
\t\tis_archetype = yes
\t\tarmor_value = 5
\t\tmodule_slots = {
\t\t\tquiet_slot = {
\t\t\t\tallowed_module_categories = { silent_category }
\t\t\t}
\t\t}
\t}
}
"""

_UNLOCK_MODULES = """
not_equipment_modules = {
\tignored_entry = { }
}
equipment_modules = {
\tgun_module = {
\t\tcategory = gun_category
\t\tcan_convert_from = { module_category = old_gun_category }
\t\tallowed_module_categories = {
\t\t\tgun_slot = { ammo_category }
\t\t}
\t\tadd_stats = {
\t\t\thard_attack = 5
\t\t}
\t}
\tammo_module = {
\t\tcategory = ammo_category
\t\tmultiply_stats = {
\t\t\tbreakthrough = 1.1
\t\t}
\t}
\tsilent_module = {
\t\tcategory = silent_category
\t}
}
"""


def test_hull_reaches_stats_of_categories_its_modules_unlock():
    """gun_module unlocks ammo_category into gun_slot, so the hull can carry
    ammo stats even though its own slot list never names that category."""
    stats = _index(_UNLOCK_HULLS, _UNLOCK_MODULES).resolve("unlock_hull")
    assert {"reliability", "hard_attack", "breakthrough"} <= stats


def test_a_hull_whose_modules_declare_no_stats_gains_nothing():
    stats = _index(_UNLOCK_HULLS, _UNLOCK_MODULES).resolve("bare_hull")
    assert "armor_value" in stats
    assert "hard_attack" not in stats
    assert "breakthrough" not in stats


_EDGE_GROUPS = """
mio_cat_edge = {
\tallowed = { always = yes }
\tequipment_type = {
\t\tfrigate
\t}
}
"""


def test_group_ignores_blocks_other_than_equipment_type():
    assert _index(_AA, groups=_EDGE_GROUPS).expand("mio_cat_edge") == ["frigate"]
