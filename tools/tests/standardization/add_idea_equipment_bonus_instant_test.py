"""Tests for the surgical idea equipment-bonus update."""

import pytest
from add_idea_equipment_bonus_instant import add_instant
from equipment_module_slots import blank_comments
from validate_ideas import _parse_ideas_from_text


def test_adds_instant_to_each_missing_entry_without_touching_existing_entries():
    text = (
        "ideas = {\n\tcountry = {\n\t\tBONUS_idea = {\n"
        "\t\t\tequipment_bonus = {\n"
        "\t\t\t\tinfantry_weapons_type = { build_cost_ic = -0.1 }\n"
        "\t\t\t\tartillery_equipment = {\n"
        "\t\t\t\t\tsoft_attack = 0.05\n"
        "\t\t\t\t}\n"
        "\t\t\t\tAA_Equipment = { build_cost_ic = -0.1 instant = yes }\n"
        "\t\t\t}\n"
        "\t\t\t# equipment_bonus = { not_real = { build_cost_ic = 0.5 } }\n"
        "\t\t}\n\t}\n}\n"
    )
    expected = text.replace(
        "infantry_weapons_type = { build_cost_ic = -0.1 }",
        "infantry_weapons_type = { build_cost_ic = -0.1 instant = yes }",
    ).replace(
        "\t\t\t\t\tsoft_attack = 0.05\n",
        "\t\t\t\t\tsoft_attack = 0.05\n\t\t\t\t\tinstant = yes\n",
    )

    updated, count = add_instant(text)

    assert count == 2
    assert updated == expected
    assert add_instant(updated) == (updated, 0)
    assert not [
        issue
        for issue in _parse_ideas_from_text(blank_comments(updated), frozenset())[1]
        if issue.issue_type == "equipment-bonus-not-instant"
    ]


def test_one_line_bonus_and_unclosed_block():
    text = (
        "ideas = {\n\tcountry = {\n\t\tBONUS_idea = {\n"
        "\t\t\tequipment_bonus = { convoy = { build_cost_ic = -0.1 } }\n"
        "\t\t}\n\t}\n}\n"
    )

    updated, count = add_instant(text)

    assert count == 1
    assert "convoy = { build_cost_ic = -0.1 instant = yes }" in updated
    with pytest.raises(ValueError, match="unclosed equipment_bonus"):
        add_instant("equipment_bonus = { convoy = { build_cost_ic = -0.1 }")
    with pytest.raises(ValueError, match="unexpected instant value for convoy"):
        add_instant("equipment_bonus = { convoy = { instant = no } }")


def test_commented_instant_does_not_count():
    text = (
        "equipment_bonus = {\n"
        "\tconvoy = {\n"
        "\t\tbuild_cost_ic = -0.1 # instant = yes\n"
        "\t}\n"
        "}\n"
    )

    updated, count = add_instant(text)

    assert count == 1
    assert "\t\tinstant = yes\n" in updated
    assert add_instant(updated) == (updated, 0)
