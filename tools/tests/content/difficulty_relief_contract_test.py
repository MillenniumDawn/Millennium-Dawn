"""Difficulty relief wiring contracts, not an HOI4 runtime simulation."""

from pathlib import Path

import pytest
from shared.suite import read_text
from shared_utils import iter_statements, read_script
from validate_localisation import _parse_loc_keys_from_text

ROOT = Path(__file__).resolve().parents[3]
DIFFICULTIES = [
    ("diff_very_easy_player", 1.00, -0.50),
    ("diff_easy_player", 0.75, -0.25),
    ("diff_normal_player", None, None),
    ("diff_hard_player", None, None),
    ("diff_very_hard_player", None, None),
    ("diff_very_easy_ai", None, None),
    ("diff_easy_ai", None, None),
    ("diff_normal_ai", None, None),
    ("diff_hard_ai", 0.75, -0.25),
    ("diff_very_hard_ai", 1.00, -0.50),
]


def _block(source, name):
    matches = [body for key, _, body in iter_statements(source) if key == name]
    assert len(matches) == 1, name
    assert matches[0] is not None, name
    return matches[0]


def _numeric_values(body, name):
    values = []
    for key, value, nested in iter_statements(body):
        if key == name:
            assert nested is None, name
            assert value is not None, name
            values.append(float(value))
    return values


def _english_value(pairs, name):
    values = [value for key, value in pairs if key == name]
    assert len(values) == 1, name
    assert values[0].strip('"').strip(), name
    return values[0]


@pytest.fixture(scope="module")
def difficulty_source():
    return read_script(str(ROOT / "common/modifiers/00_static_modifiers.txt"))


@pytest.fixture(scope="module")
def english():
    return [
        pair
        for filename in (
            "MD_currency_l_english.yml",
            "replace/replaced_from_vanilla_frontend_l_english.yml",
            "replace/replaced_from_vanilla_modifiers_l_english.yml",
        )
        for pair in _parse_loc_keys_from_text(
            read_text(ROOT / "localisation/english" / filename)
        )
    ]


@pytest.mark.parametrize("difficulty,expected", [(d, f) for d, f, _ in DIFFICULTIES])
def test_currency_floor_is_configured_only_for_approved_scopes(
    difficulty_source, difficulty, expected
):
    values = _numeric_values(
        _block(difficulty_source, difficulty), "currency_strength_minimum_modifier"
    )
    assert values == ([] if expected is None else [expected])


@pytest.mark.parametrize("difficulty,expected", [(d, r) for d, _, r in DIFFICULTIES])
def test_inflation_relief_is_configured_only_for_approved_scopes(
    difficulty_source, difficulty, expected
):
    values = _numeric_values(
        _block(difficulty_source, difficulty), "inflation_gain_multiplier_modifier"
    )
    assert values == ([] if expected is None else [expected])


@pytest.mark.parametrize(
    "modifier,value_type,color_type",
    [
        ("currency_strength_minimum_modifier", "number", "good"),
        ("inflation_gain_multiplier_modifier", "percentage", "bad"),
    ],
)
def test_relief_modifiers_resolve_country_definitions_tokens_and_english(
    english, modifier, value_type, color_type
):
    definitions = read_script(
        str(ROOT / "common/modifier_definitions/money_modifier_definitions.txt")
    )
    body = _block(definitions, modifier)
    for name, expected in (
        ("category", "country"),
        ("value_type", value_type),
        ("color_type", color_type),
    ):
        assert [
            (value, nested)
            for key, value, nested in iter_statements(body)
            if key == name
        ] == [(expected, None)]
    tokens = read_text(ROOT / "common/synchronized_dynamic_tokens/MD_tokens.txt")
    assert tokens.splitlines().count(modifier) == 1
    _english_value(english, modifier)


@pytest.mark.parametrize(
    "difficulty,recipient",
    [
        ("VERY_EASY", "Player"),
        ("EASY", "Player"),
        ("NORMAL", None),
        ("HARD", "AI"),
        ("VERY_HARD", "AI"),
    ],
)
def test_difficulty_tooltip_links_relief_to_the_correct_recipient(
    english, difficulty, recipient
):
    tooltip = _english_value(english, f"FE_DIFFICULTY_{difficulty}_TOOLTIP")
    reference = "$difficulty_economic_relief_tt$"
    if recipient is None:
        assert reference not in tooltip
        return
    assert f"§Y{recipient} economic relief:§!" in tooltip
    assert tooltip.count(reference) == 1
    explanation = _english_value(english, "difficulty_economic_relief_tt")
    for modifier in (
        "currency_strength_minimum_modifier",
        "inflation_gain_multiplier_modifier",
    ):
        assert explanation.count(f"${modifier}$") == 1
        _english_value(english, modifier)
