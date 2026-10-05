import pytest

# pyradox ships in the optional analysis group; only the Linux CI leg installs it.
pytest.importorskip("pyradox")

from tools.types.equipment import Equipment, LandEquipmentStats
from tools.types.mio import MIO, Trait
from tools.utils.pyradox_utils import (
    as_mapping,
    dedupe_preserve_order,
    normalize_node,
    stats_value,
    token_list,
)


def test_dedupe_preserve_order_keeps_first_seen_values():
    assert dedupe_preserve_order(["b", "a", "b", "c", "a"]) == ["b", "a", "c"]


def test_token_list_flattens_nested_values():
    value = {"left": ["a", 2], "right": {"x": "b", "y": [True, "c"]}}
    assert token_list(value) == ["a", "2", "b", "True", "c"]


def test_as_mapping_normalizes_string_keys():
    assert as_mapping({"A": 1, "B": {"C": 2}}) == {"A": 1, "B": {"C": 2}}


def test_stats_value_coerces_common_script_literals():
    assert stats_value("yes") is True
    assert stats_value("OFF") is False
    assert stats_value("3.5") == 3.5
    assert stats_value("7") == 7
    assert stats_value("plain") == "plain"


def test_normalize_node_recurses_through_container_types():
    payload = {"a": [1, {"b": "two"}]}
    assert normalize_node(payload) == {"a": [1, {"b": "two"}]}


def test_mio_average_boost_ignores_traits_without_that_stat():
    equipment = Equipment(
        tag="infantry_weapons",
        is_archetype=False,
        archetype=None,
        types=["infantry"],
        is_buildable=True,
        stats=LandEquipmentStats(),
    )
    mio = MIO(
        token="test_org",
        countries=[],
        equipment_types={"infantry_weapons"},
        research_categories=set(),
        traits=[
            Trait(
                token="trait_1",
                name="Trait 1",
                applies_to={"infantry_weapons"},
                bonuses=LandEquipmentStats(soft_attack=2.0, defense=4.0),
            ),
            Trait(
                token="trait_2",
                name="Trait 2",
                applies_to={"infantry_weapons"},
                bonuses=LandEquipmentStats(soft_attack=6.0),
            ),
            Trait(
                token="trait_3",
                name="Trait 3",
                applies_to={"infantry_weapons"},
                bonuses=LandEquipmentStats(defense=2.0),
            ),
        ],
    )

    report = mio.sum_bonuses_for(equipment)

    assert report.boost.soft_attack == 8.0
    assert report.boost.defense == 6.0
    assert report.averaged_boost.soft_attack == 4.0
    assert report.averaged_boost.defense == 3.0
