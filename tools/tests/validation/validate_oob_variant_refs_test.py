"""Tests for the OOB equipment-reference checks in validate_oob_units.py.

A ship's design is looked up in its creator's variant pool, so a version_name
the creator never created silently downgrades the ship to version 0 of the hull.
A production line naming an archetype instead of a concrete equipment hits the
same lookup with a design that can never exist.
"""

from validate_oob_units import (
    build_variant_name_index,
    check_attributed_archetypes,
    check_oob_variant_refs,
    parse_archetypes,
    variant_tag_from_path,
)

_CHI_VARIANTS = """
2000.1.1 = {
	create_equipment_variant = {
		name = "Type 053H3 Class"
		type = frigate_hull_3
		name_group = CHI_FRIGATE_HISTORICAL
		parent_version = 0
		modules = {
			fixed_ship_engine_slot = module_light_surface_diesel_power_1
		}
	}
	create_equipment_variant = {
		name = "Naresuan Class"
		type = frigate_hull_2
		parent_version = 1
		modules = {
			fixed_ship_engine_slot = module_light_surface_diesel_power_1
		}
	}
}
"""

_EQUIPMENT = """
equipments = {
	convoy = {
		year = 1910
		is_archetype = yes
		type = convoy
	}
	convoy_1 = {
		year = 1910
		archetype = convoy
		active = yes
	}
}
"""


def _ship(hull, name, **fields):
    attrs = " ".join(f"{k} = {v}" for k, v in fields.items())
    return (
        'units = { fleet = { task_force = { ship = { name = "Test" '
        f'equipment = {{ {hull} = {{ amount = 1 {attrs} version_name = "{name}" }} }}'
        " } } } }"
    )


def _index(*sources):
    return build_variant_name_index(list(sources))


def _kinds(findings):
    return [f.kind for f in findings]


# ---- variant ownership -----------------------------------------------------


def test_history_country_file_owns_its_variants():
    assert variant_tag_from_path("history/countries/CHI - China.txt") == "CHI"
    assert variant_tag_from_path("history\\countries\\USA - USA.txt") == "USA"


def test_runtime_sources_have_no_resolvable_tag():
    assert variant_tag_from_path("events/Egypt.txt") is None
    assert variant_tag_from_path("common/national_focus/05_china.txt") is None


# ---- unresolved version_name ----------------------------------------------


def test_matching_variant_passes():
    by_tag, wildcard = _index(("history/countries/CHI - China.txt", _CHI_VARIANTS))
    content = _ship("frigate_hull_3", "Type 053H3 Class", owner="SIA", creator="CHI")
    assert check_oob_variant_refs(content, by_tag, wildcard) == []


def test_wrong_hull_tier_fails():
    by_tag, wildcard = _index(("history/countries/CHI - China.txt", _CHI_VARIANTS))
    content = _ship("frigate_hull_3", "Naresuan Class", owner="SIA", creator="CHI")
    findings = check_oob_variant_refs(content, by_tag, wildcard)
    assert _kinds(findings) == ["unknown_variant"]
    assert "frigate_hull_3" in findings[0].message
    assert "CHI" in findings[0].message


def test_misspelled_name_fails():
    by_tag, wildcard = _index(("history/countries/CHI - China.txt", _CHI_VARIANTS))
    content = _ship("frigate_hull_2", "Nareusan Class", owner="SIA", creator="CHI")
    assert _kinds(check_oob_variant_refs(content, by_tag, wildcard)) == [
        "unknown_variant"
    ]


def test_creator_takes_precedence_over_owner():
    by_tag, wildcard = _index(("history/countries/CHI - China.txt", _CHI_VARIANTS))
    # SIA owns the ship but CHI built it, so the miss is reported against CHI.
    content = _ship("carrier_hull_2", "Liaoning Class", owner="SIA", creator="CHI")
    findings = check_oob_variant_refs(content, by_tag, wildcard)
    assert findings[0].message.startswith("CHI ")


def test_owner_used_when_no_creator():
    by_tag, wildcard = _index(("history/countries/CHI - China.txt", _CHI_VARIANTS))
    assert (
        check_oob_variant_refs(
            _ship("frigate_hull_2", "Naresuan Class", owner="CHI"), by_tag, wildcard
        )
        == []
    )
    assert _kinds(
        check_oob_variant_refs(
            _ship("frigate_hull_2", "Naresuan Class", owner="SIA"), by_tag, wildcard
        )
    ) == ["unknown_variant"]


def test_runtime_created_variant_satisfies_any_tag():
    """Egypt's carrier purchase creates its design in FRA scope inside an event,
    which no static pass can attribute, so it must not be reported."""
    by_tag, wildcard = _index(("events/Egypt.txt", _CHI_VARIANTS))
    content = _ship("frigate_hull_3", "Type 053H3 Class", owner="EGY", creator="FRA")
    assert check_oob_variant_refs(content, by_tag, wildcard) == []


def test_ship_without_version_name_is_skipped():
    by_tag, wildcard = _index(("history/countries/CHI - China.txt", _CHI_VARIANTS))
    content = (
        'units = { fleet = { task_force = { ship = { name = "Test" '
        "equipment = { frigate_hull_3 = { amount = 1 owner = CHI } } } } } }"
    )
    assert check_oob_variant_refs(content, by_tag, wildcard) == []


def test_non_tag_creator_is_skipped():
    by_tag, wildcard = _index(("history/countries/CHI - China.txt", _CHI_VARIANTS))
    content = _ship("frigate_hull_3", "Naresuan Class", owner="SIA", creator="ROOT")
    assert check_oob_variant_refs(content, by_tag, wildcard) == []


# ---- attributed archetypes -------------------------------------------------


def test_parse_archetypes_reads_is_archetype():
    assert parse_archetypes([_EQUIPMENT]) == {"convoy"}


def test_archetype_with_creator_fails():
    content = """units = {
	add_equipment_production = {
		equipment = { type = convoy creator = "SIA" }
		requested_factories = 1
	}
}"""
    findings = check_attributed_archetypes(content, {"convoy"})
    assert _kinds(findings) == ["attributed_archetype"]
    assert "convoy" in findings[0].message


def test_archetype_with_producer_fails():
    content = (
        "add_equipment_to_stockpile = { type = convoy amount = 40 producer = GRE }"
    )
    assert _kinds(check_attributed_archetypes(content, {"convoy"})) == [
        "attributed_archetype"
    ]


def test_concrete_equipment_with_producer_passes():
    content = (
        "add_equipment_to_stockpile = { type = convoy_1 amount = 40 producer = GRE }"
    )
    assert check_attributed_archetypes(content, {"convoy"}) == []


def test_archetype_without_attribution_passes():
    """calculate_starting_utility_stockpile grants the archetype unattributed,
    which never triggers a variant lookup."""
    content = (
        "add_equipment_to_stockpile = { type = convoy amount = dockyard_increase }"
    )
    assert check_attributed_archetypes(content, {"convoy"}) == []


def test_commented_out_production_line_is_ignored():
    content = '#\tadd_equipment_production = { equipment = { type = convoy creator = "SIA" } }'
    assert check_attributed_archetypes(content, {"convoy"}) == []
