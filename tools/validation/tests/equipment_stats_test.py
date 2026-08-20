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
