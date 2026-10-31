"""Guaranteed and possible starting research from the shared history reader."""

import pytest
from equipment_variant_context import dlc_truth, script_nodes, starting_techs

# case: history, DLC configuration, guaranteed research, possible research.
_RESEARCH_CASES = {
    "unknown branch": (
        "if = { limit = { has_country_flag = test } set_technology = { tech = 1 } }",
        {},
        set(),
        {"tech"},
    ),
    "future date": ("2017.1.1 = { set_technology = { tech = 1 } }", {}, set(), set()),
    "hidden": (
        "hidden_effect = { set_technology = { tech = 1 } }",
        {},
        {"tech"},
        {"tech"},
    ),
    "removed": (
        "set_technology = { tech = 1 } set_technology = { tech = 0 }",
        {},
        set(),
        set(),
    ),
    "NOT is NOR": (
        'if = { limit = { NOT = { has_dlc = "A" has_dlc = "B" } } set_technology = { tech = 1 } }',
        {"A": True, "B": False},
        set(),
        set(),
    ),
    "foreign scope": ("BBB = { set_technology = { tech = 1 } }", {}, set(), {"tech"}),
    "tooltip is not an effect": (
        "effect_tooltip = { set_technology = { tech = 1 } }",
        {},
        set(),
        set(),
    ),
    "custom tooltip is not an effect": (
        "custom_effect_tooltip = { set_technology = { tech = 1 } }",
        {},
        set(),
        set(),
    ),
    "trigger metadata is not an effect": (
        "limit = { set_technology = { tech = 1 } }",
        {},
        set(),
        set(),
    ),
}


@pytest.mark.parametrize(
    ("text", "dlcs", "known", "possible"), _RESEARCH_CASES.values(), ids=_RESEARCH_CASES
)
def test_starting_research_bounds(text, dlcs, known, possible):
    nodes = script_nodes(text)
    assert starting_techs(nodes, dlcs, (2000, 1, 1)) == known
    assert starting_techs(nodes, dlcs, (2000, 1, 1), possible=True) == possible


# case: trigger, DLC configuration, truth value.
_TRIGGER_CASES = {
    "NOR": ('NOT = { has_dlc = "A" has_dlc = "B" }', {"A": True, "B": False}, False),
    "unknown NOR": ('NOT = { has_dlc = "A" has_dlc = "B" }', {"A": False}, None),
    "empty NOR": ("NOT = {}", {}, True),
}


@pytest.mark.parametrize(
    ("text", "dlcs", "expected"), _TRIGGER_CASES.values(), ids=_TRIGGER_CASES
)
def test_dlc_logic(text, dlcs, expected):
    assert dlc_truth(script_nodes(text), dlcs) is expected
