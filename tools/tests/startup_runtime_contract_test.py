from pathlib import Path

from shared.suite import read_text

ROOT = Path(__file__).resolve().parents[2]


def _read_common(path):
    return read_text(ROOT / "common" / path)


def _effect_body(source, name):
    start = source.index(f"{name} = {{")
    depth = 0
    opening = source.index("{", start)
    for index in range(opening, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]
    raise AssertionError(f"unterminated effect: {name}")


def test_game_startup_drops_redundant_zero_seeds_and_keeps_order():
    on_actions = _read_common("on_actions/00_on_actions.txt")
    startup = on_actions[on_actions.index("# Initialize On Startup") :]
    country_setup = startup[startup.index("every_country = {") :]

    assert "set_variable = { protest_strength = 0 }" not in country_setup
    assert "set_variable = { protest_radicalisation = 0 }" not in country_setup
    assert "set_variable = { anti_bully_wars = 0 }" not in country_setup
    assert (
        country_setup.index("cyber_nation_startup = yes")
        < country_setup.index("currency_startup = yes")
        < country_setup.index("ingame_update_setup = yes")
    )


def test_cyber_startup_recalculates_without_zero_seeds():
    cyber = _effect_body(
        _read_common("scripted_effects/00_cyber_effects.txt"), "cyber_nation_startup"
    )

    assert "set_variable = { cyber_max_targets = 0 }" not in cyber
    assert "set_variable = { cyber_offense_power = 0 }" not in cyber
    assert "set_variable = { cyber_defense_rating = 0 }" not in cyber
    assert "set_variable = { cyber_attribution_bonus = 0 }" not in cyber
    assert "set_variable = { cyber_ongoing_operations = 0 }" not in cyber
    assert "calculate_cyber_capability = yes" in cyber
    assert "cyber_rebuild_potential_targets = yes" in cyber


def test_currency_startup_preserves_strength_without_migrated_defaults():
    currency = _effect_body(
        _read_common("scripted_effects/00_currency_effects.txt"), "currency_startup"
    )

    assert "set_variable = { currency_strength = 1.0 }" in currency
    for variable in (
        "currency_inflation_feed",
        "inflation_cost_combined_var",
        "reserve_roi_bonus",
        "reserve_trade_bonus",
    ):
        assert f"set_variable = {{ {variable} = 0 }}" not in currency
    assert "cb_policy_rate" not in currency
    assert "no_currency_backing" not in currency
    assert "update_currency_issuers = yes" in currency


def test_runtime_spawn_initializer_keeps_resets_defaults_and_required_order():
    setup = _effect_body(
        _read_common("scripted_effects/00_scripted_effects.txt"),
        "ingame_startup_nations_effect",
    )
    for modifier in (
        "civilian_microchip_consumption_modifier",
        "inflation_dynamic_modifier",
    ):
        guard_start = setup.index(
            f"if = {{ limit = {{ NOT = {{ has_dynamic_modifier = {{ modifier = {modifier} }} }} }}"
        )
        guard = _effect_body(setup[guard_start:], "if")
        assert f"add_dynamic_modifier = {{ modifier = {modifier} }}" in guard
    fresh_only = setup.index(
        "if = { limit = { check_variable = { fresh_nation_temp = 1 } }"
    )

    for variable in (
        "currency_inflation_feed",
        "inflation_cost_combined_var",
        "reserve_roi_bonus",
        "reserve_trade_bonus",
    ):
        assert setup.index(f"set_variable = {{ {variable} = 0 }}") < fresh_only
    cyber_start = setup.index(
        "\t\tif = { limit = { NOT = { has_variable = cyber_capability }"
    )
    cyber_guard = _effect_body(setup[cyber_start:], "if")
    for variable in ("cyber_attribution_bonus", "cyber_ongoing_operations"):
        assert cyber_guard.index(
            f"set_variable = {{ {variable} = 0 }}"
        ) < cyber_guard.index("cyber_nation_startup = yes")
    for variable in ("protest_strength", "protest_radicalisation", "anti_bully_wars"):
        assert f"set_variable = {{ {variable} = 0 }}" not in setup
    assert "set_variable = { cb_policy_rate = 3 }" in setup
    assert "add_ideas = no_currency_backing" in setup
    assert setup.index("currency_startup = yes") < setup.index(
        "ingame_update_setup = yes"
    )
    for required in (
        "update_neighbors_effects = yes",
        "economic_cycle_drift_popularity = yes",
        "calculate_expected_spending = yes",
        "recalculate_law_desires = yes",
    ):
        assert required in setup

    civil_war = _effect_body(
        _read_common("scripted_effects/00_scripted_effects.txt"),
        "civil_war_replication_effect",
    )
    assert civil_war.index("ingame_startup_nations_effect = yes") < civil_war.index(
        "replicate_configure_politics = yes"
    )
