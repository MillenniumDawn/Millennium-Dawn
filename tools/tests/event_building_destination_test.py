from pathlib import Path

import pytest
from shared_utils import iter_statements, strip_comments

ROOT = Path(__file__).resolve().parents[2]


def _block(source, key, identity=None):
    for name, _, body in iter_statements(source):
        if name != key or body is None:
            continue
        if identity is None or identity in list(iter_statements(body)):
            return body
    raise AssertionError(f"Missing {key}: {identity}")


def _event(path, event_id):
    source = strip_comments((ROOT / "events" / path).read_text(encoding="utf-8"))
    return _block(source, "country_event", ("id", event_id, None))


def _option(event, name):
    return _block(event, "option", ("name", name, None))


def _normalized(body):
    return " ".join(body.split())


@pytest.mark.parametrize(
    "event_id,building", [("14", "industrial_complex"), ("15", "offices")]
)
def test_private_investment_eligibility_matches_reward_destination(event_id, building):
    event = _event("Econ_events.txt", f"econvent.{event_id}")
    eligible = _block(_block(event, "trigger"), "any_owned_state")
    destination = _block(
        _option(event, f"econvent.{event_id}.a"), "random_owned_controlled_state"
    )
    selection = _block(destination, "limit")

    assert ("is_controlled_by", "OWNER", None) in list(iter_statements(eligible))
    assert _normalized(_block(eligible, "free_building_slots")) == _normalized(
        _block(selection, "free_building_slots")
    )
    assert _normalized(_block(selection, "free_building_slots")) == (
        f"building = {building} size > 0 include_locked = no"
    )
    assert ("type", building, None) in list(
        iter_statements(_block(destination, "add_building_construction"))
    )
    assert "free_shared_building_slots" not in event


@pytest.mark.parametrize("event_id", ["14", "15"])
def test_private_investment_preserves_country_reward_scope(event_id):
    option = _option(
        _event("Econ_events.txt", f"econvent.{event_id}"), f"econvent.{event_id}.a"
    )
    destination = _block(option, "random_owned_controlled_state")
    country_effects = list(iter_statements(option))

    assert ("change_relative_party_popularity", "yes", None) in country_effects
    assert "party_popularity_increase = 0.03" in option
    assert "temp_outlook_increase = 0.03" in option
    assert "set_country_flag" in [key for key, _, _ in country_effects]
    assert "change_relative_party_popularity" not in destination
    assert "set_country_flag" not in destination


def test_italy_cooperation_requires_capacity_on_both_sides_before_payment():
    option = _option(_event("Italy.txt", "italy_md.17"), "italy_md.17.o1")
    acceptance = _block(option, "trigger")
    italy = _block(option, "ITA")
    destinations = [
        (
            _block(acceptance, "any_owned_state"),
            _block(option, "random_owned_controlled_state"),
        ),
        (
            _block(_block(acceptance, "ITA"), "any_owned_state"),
            _block(italy, "random_owned_controlled_state"),
        ),
    ]
    for eligible, destination in destinations:
        assert ("is_controlled_by", "OWNER", None) in list(iter_statements(eligible))
        selection = _block(destination, "limit")
        assert _normalized(_block(eligible, "free_building_slots")) == _normalized(
            _block(selection, "free_building_slots")
        )
        assert "include_locked = no" in _block(selection, "free_building_slots")
        assert "building = industrial_complex" in _block(
            selection, "free_building_slots"
        )
    assert "region = 23" in destinations[1][0]
    assert "region = 23" in _block(destinations[1][1], "limit")
    assert "treasury_change = -8.5" in option
    assert "mafia_industrial_focus_base_cost = -8.5" in italy
    assert "one_random_industrial_complex" not in option
    assert "skip_payment" not in option


def test_farm_conversion_checks_owned_controlled_farms_and_civilian_cap():
    event = _event("Internal Faction Events.txt", "internal_factions_events.31")
    eligible = _block(_block(event, "trigger"), "any_owned_state")
    assert "is_controlled_by = OWNER" in eligible
    assert "agriculture_district > 0" in eligible
    assert "industrial_complex < 50" in eligible
    assert "agriculture_district_total" not in _block(event, "trigger")

    for suffix, count in [("a", 1), ("c", 2)]:
        option = _option(event, f"internal_factions_events.31.{suffix}")
        destinations = [
            body
            for key, _, body in iter_statements(option)
            if key == "random_owned_controlled_state"
        ]
        assert len(destinations) == count
        for destination in destinations:
            assert destination is not None
            selection = _block(destination, "limit")
            assert "agriculture_district > 0" in selection
            assert "industrial_complex < 50" in selection
            assert destination.index("remove_building") < destination.index(
                "add_building_construction"
            )
            assert "add_extra_state_shared_building_slots" not in destination
        country_effects = list(iter_statements(option))
        assert ("change_farmers_opinion", "yes", None) in country_effects
        assert "set_country_flag" in [key for key, _, _ in country_effects]

    buildings = strip_comments(
        (ROOT / "common/buildings/00_buildings.txt").read_text(encoding="utf-8")
    )
    cap = _block(
        _block(_block(buildings, "buildings"), "industrial_complex"), "level_cap"
    )
    assert ("state_max", "50", None) in list(iter_statements(cap))


def test_double_farm_conversion_requires_two_convertible_farms():
    option = _option(
        _event("Internal Faction Events.txt", "internal_factions_events.31"),
        "internal_factions_events.31.c",
    )
    alternatives = _block(_block(option, "trigger"), "OR")
    single_state = _block(alternatives, "any_owned_state")
    assert "is_controlled_by = OWNER" in single_state
    assert "agriculture_district > 1" in single_state
    assert "industrial_complex < 49" in single_state
    multiple_states = _block(alternatives, "collection_size")
    collection = _block(multiple_states, "input")
    assert ("input", "game:scope", None) in list(iter_statements(collection))
    assert "value > 2" in multiple_states
    assert "agriculture_district_total" not in alternatives
    assert "operators" not in [key for key, _, _ in iter_statements(multiple_states)]
    operators = _block(collection, "operators")
    assert "owned_states" in operators
    eligible = _block(operators, "limit")
    assert "is_controlled_by = OWNER" in eligible
    assert "agriculture_district > 0" in eligible
    assert "industrial_complex < 50" in eligible
