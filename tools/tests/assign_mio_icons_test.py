"""Behavior tests for MIO trait modifier selection."""

from assign_mio_icons import PRE, choose_icon, inner_block, winning_modifier


def test_winning_modifier_uses_absolute_value():
    block = """
    equipment_bonus = {
        soft_attack = -0.4
        hard_attack = 0.6
    }
    production_bonus = {
        production_speed = 0.5
    }
    """

    assert winning_modifier(block) == "hard_attack"


def test_winning_modifier_returns_none_without_supported_modifiers():
    assert winning_modifier("limit_to_equipment_type = tank") is None


def test_inner_block_returns_empty_when_the_brace_never_closes():
    assert inner_block("equipment_bonus = { soft_attack = 0.5", "equipment_bonus") == ""


def test_choose_icon_prefers_the_family_alias():
    sprites = {PRE + "apc_armor", PRE + "armor_value"}
    assert choose_icon("apc", "armor_value", sprites) == PRE + "apc_armor"


def test_choose_icon_uses_the_standard_suffix_when_no_alias_exists():
    sprites = {PRE + "soft_attack"}
    assert choose_icon("smallarms", "soft_attack", sprites) == PRE + "soft_attack"


def test_choose_icon_falls_back_to_the_prefix_when_the_modifier_has_no_icon():
    sprites = {PRE + "smallarms"}
    assert choose_icon("smallarms", "max_organisation", sprites) == PRE + "smallarms"


def test_choose_icon_returns_unique_when_nothing_matches():
    assert choose_icon("apc", "armor_value", set()) == PRE + "unique"
