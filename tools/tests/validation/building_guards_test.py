"""Tests for validate_building_guards.

A `damage_building` / `remove_building` effect naming a building type must sit
behind a guard trigger that proves that same building type is present --
otherwise the call spams error.log at scale (issue #2806). Guard detection
must track *which* building is proven present, not merely "is there an if?" --
an `if`/`limit` guarding something else entirely (an idea, a flag) must still
flag the effect inside it.
"""

import disk_cache
import pytest
import validate_building_guards as V
from shared.suite import assert_findings, run_validator, write_tree, write_under

_PROVINCE_BUILDINGS = frozenset(
    {"naval_base", "bunker", "supply_node", "rail_way", "naval_supply_hub"}
)


@pytest.fixture(autouse=True)
def _province_buildings():
    """The province buildings a validator run reads from common/buildings/."""
    V._init_worker(_PROVINCE_BUILDINGS, frozenset(), frozenset(), frozenset())


def _scan(script):
    scanner = V.Scanner(V._sanitize(script))
    scanner.walk(0, len(scanner.text), V.Context())
    return scanner.findings


def _messages(script):
    return [message for _, _, message in _scan(script)]


def _scan_province(script):
    scanner = V.Scanner(V._sanitize(script))
    scanner.check_province_building_triggers()
    return scanner.findings


_RANDOM_INFRASTRUCTURE_CASES = {
    "unguarded random state": (
        "random_owned_state = { add_building_construction = { type = infrastructure level = 1 } }",
        1,
    ),
    "scripted guard": (
        "random_owned_state = { limit = { infrastructure_random_build_loc = yes } "
        "add_building_construction = { type = infrastructure level = 1 } }",
        0,
    ),
    "matching free slots": (
        "random_owned_state = { limit = { AND = { free_building_slots = "
        "{ building = infrastructure size >= 1 } } } "
        "add_building_construction = { type = infrastructure level = 1 } }",
        0,
    ),
    "wrong building": (
        "random_owned_state = { limit = { free_building_slots = "
        "{ building = air_base size > 0 } } "
        "add_building_construction = { type = infrastructure level = 1 } }",
        1,
    ),
    "zero slots": (
        "random_owned_state = { limit = { free_building_slots = "
        "{ building = infrastructure size = 0 } } "
        "add_building_construction = { type = infrastructure level = 1 } }",
        1,
    ),
    "fractional negative threshold": (
        "random_owned_state = { limit = { free_building_slots = "
        "{ building = infrastructure size > -0.5 } } "
        "add_building_construction = { type = infrastructure level = 1 } }",
        1,
    ),
    "nested size is not the slot count": (
        "random_owned_state = { limit = { free_building_slots = "
        "{ building = infrastructure other = { size > 0 } } } "
        "add_building_construction = { type = infrastructure level = 1 } }",
        1,
    ),
    "guard in OR": (
        "random_owned_state = { limit = { OR = { infrastructure_random_build_loc = yes "
        "always = yes } } add_building_construction = { type = infrastructure level = 1 } }",
        1,
    ),
    "guard in other state": (
        "random_owned_state = { limit = { any_owned_state = "
        "{ infrastructure_random_build_loc = yes } } "
        "add_building_construction = { type = infrastructure level = 1 } }",
        1,
    ),
    "random subset": (
        "every_owned_state = { random_select_amount = 2 "
        "add_building_construction = { type = infrastructure level = 1 } }",
        1,
    ),
    "controlled state": (
        "random_controlled_state = { add_building_construction = { type = infrastructure level = 1 } }",
        1,
    ),
    "owned controlled state": (
        "random_owned_controlled_state = { limit = { infrastructure_random_build_loc = yes } "
        "add_building_construction = { type = infrastructure level = 1 } }",
        0,
    ),
    "core state": (
        "random_core_state = { add_building_construction = { type = infrastructure level = 1 } }",
        1,
    ),
    "controlled subset": (
        "every_controlled_state = { random_select_amount = 1 "
        "add_building_construction = { type = infrastructure level = 1 } }",
        1,
    ),
    "all controlled states": (
        "every_controlled_state = { add_building_construction = { type = infrastructure level = 1 } }",
        0,
    ),
    "all states": (
        "every_owned_state = { add_building_construction = { type = infrastructure level = 1 } }",
        0,
    ),
    "nested random selection": (
        "every_owned_state = { if = { random_select_amount = 1 } "
        "add_building_construction = { type = infrastructure level = 1 } }",
        0,
    ),
    "other building": (
        "random_owned_state = { add_building_construction = { type = air_base level = 1 } }",
        0,
    ),
    "nested effect excluded": (
        "random_owned_state = { if = { add_building_construction = "
        "{ type = infrastructure level = 1 } } }",
        0,
    ),
    "tooltip excluded": (
        "effect_tooltip = { random_owned_state = { add_building_construction = "
        "{ type = infrastructure level = 1 } } }",
        0,
    ),
    "quoted and commented guards": (
        'random_owned_state = { limit = { log = "infrastructure_random_build_loc = yes" '
        "# infrastructure_random_build_loc = yes\n } "
        "add_building_construction = { type = infrastructure level = 1 } }",
        1,
    ),
}


@pytest.mark.parametrize(
    "script,count",
    _RANDOM_INFRASTRUCTURE_CASES.values(),
    ids=_RANDOM_INFRASTRUCTURE_CASES,
)
def test_random_infrastructure_slots(script, count):
    scanner = V.Scanner(V._sanitize(script))
    scanner.check_random_infrastructure_slots(0, len(scanner.text))
    assert len(scanner.findings) == count


@pytest.mark.parametrize(
    "limit,has_bound",
    [
        ("infrastructure < 5", True),
        ("AND = { infrastructure <= 4 }", True),
        ("OR = { infrastructure < 5 always = yes }", False),
        ("any_owned_state = { infrastructure < 5 }", False),
    ],
)
def test_level_bounds_are_reported_without_suppressing_warning(limit, has_bound):
    script = (
        f"random_owned_state = {{ limit = {{ {limit} }} "
        "add_building_construction = { type = infrastructure level = 1 } }"
    )
    scanner = V.Scanner(V._sanitize(script))
    scanner.check_random_infrastructure_slots(0, len(scanner.text))
    assert len(scanner.findings) == 1
    assert ("a level bound is present" in scanner.findings[0][2]) is has_bound


# --- unguarded effects --------------------------------------------------


def test_unguarded_damage_building_is_flagged():
    script = (
        "652 = {\n\tdamage_building = {\n\t\ttype = fuel_silo\n\t\tdamage = 1\n\t}\n}\n"
    )
    findings = _scan(script)
    assert len(findings) == 1
    assert findings[0][0] == "unguarded-damage-building"
    assert "fuel_silo" in findings[0][2]


def test_unguarded_remove_building_is_flagged():
    script = (
        "652 = {\n"
        "\tremove_building = {\n"
        "\t\ttype = arms_factory\n"
        "\t\tlevel = 1\n"
        "\t}\n"
        "}\n"
    )
    findings = _scan(script)
    assert len(findings) == 1
    assert findings[0][0] == "unguarded-remove-building"
    assert "arms_factory" in findings[0][2]


def test_effect_tooltip_preview_is_ignored():
    script = (
        "effect_tooltip = {\n"
        "\t652 = {\n"
        "\t\tdamage_building = { type = fuel_silo damage = 1 }\n"
        "\t}\n"
        "}\n"
    )
    assert _scan(script) == []


# --- accepted guard idioms -----------------------------------------------


def test_bare_count_guard_is_clean():
    """Form A: the building's own name is the trigger."""
    script = (
        "652 = {\n"
        "\tif = { limit = { fuel_silo > 0 }\n"
        "\t\tdamage_building = { type = fuel_silo damage = 1 }\n"
        "\t}\n"
        "}\n"
    )
    assert _scan(script) == []


def test_bare_count_guard_through_meta_effect_is_clean():
    """Form A as used in common/raids/: wrapped in meta_effect/text, with the
    damage amount itself a [DAM] macro substituted via a quoted value."""
    script = (
        "var:target_state = {\n"
        "\tif = { limit = { fuel_silo > 0 }\n"
        "\t\tmeta_effect = {\n"
        "\t\t\ttext = {\n"
        "\t\t\t\tdamage_building = {\n"
        "\t\t\t\t\ttype = fuel_silo\n"
        "\t\t\t\t\tdamage = [DAM]\n"
        "\t\t\t\t}\n"
        "\t\t\t}\n"
        '\t\t\tDAM = "[?building_damage_by_missile]"\n'
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )
    assert _scan(script) == []


def test_non_damaged_building_level_guard_is_clean():
    """Form B: common/decisions/Burma.txt's long-form guard."""
    script = (
        "if = {\n"
        "\tlimit = {\n"
        "\t\t931 = {\n"
        "\t\t\tnon_damaged_building_level = {\n"
        "\t\t\t\tbuilding = infrastructure\n"
        "\t\t\t\tlevel > 0\n"
        "\t\t\t}\n"
        "\t\t}\n"
        "\t}\n"
        "\t931 = {\n"
        "\t\tdamage_building = {\n"
        "\t\t\ttype = infrastructure\n"
        "\t\t\tdamage = 2\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )
    assert _scan(script) == []


def test_random_list_factor_zero_guard_is_clean():
    """Form C: common/decisions/bankruptcy_decisions.txt's weight-zeroing."""
    script = (
        "random_list = {\n"
        "\t33 = {\n"
        "\t\tmodifier = {\n"
        "\t\t\tfactor = 0\n"
        "\t\t\tindustrial_complex < 1\n"
        "\t\t}\n"
        "\t\tremove_building = {\n"
        "\t\t\ttype = industrial_complex\n"
        "\t\t\tlevel = 1\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )
    assert _scan(script) == []


def test_random_list_factor_zero_guard_does_not_leak_to_sibling_bucket():
    script = (
        "random_list = {\n"
        "\t33 = {\n"
        "\t\tmodifier = { factor = 0  industrial_complex < 1 }\n"
        "\t\tremove_building = { type = industrial_complex level = 1 }\n"
        "\t}\n"
        "\t33 = {\n"
        "\t\tremove_building = { type = arms_factory level = 1 }\n"
        "\t}\n"
        "}\n"
    )
    findings = _scan(script)
    assert len(findings) == 1
    assert "arms_factory" in findings[0][2]


def test_any_core_state_preselection_does_not_guard_random_core_state():
    """common/national_focus/turkey.txt: `any_core_state` proves some state has
    the factory, never that the state random_core_state picks does."""
    script = (
        "if = {\n"
        "\tlimit = {\n"
        "\t\tany_core_state = {\n"
        "\t\t\tarms_factory > 1\n"
        "\t\t}\n"
        "\t}\n"
        "\trandom_core_state = {\n"
        "\t\tremove_building = {\n"
        "\t\t\ttype = arms_factory\n"
        "\t\t\tlevel = 1\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )
    findings = _scan(script)
    assert len(findings) == 1
    assert "arms_factory" in findings[0][2]


def test_state_selector_with_its_own_limit_is_clean():
    script = (
        "if = {\n"
        "\tlimit = {\n"
        "\t\tany_core_state = {\n"
        "\t\t\tarms_factory > 1\n"
        "\t\t}\n"
        "\t}\n"
        "\trandom_core_state = {\n"
        "\t\tlimit = { arms_factory > 1 }\n"
        "\t\tremove_building = {\n"
        "\t\t\ttype = arms_factory\n"
        "\t\t\tlevel = 1\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )
    assert _scan(script) == []


def test_fixed_state_scope_inherits_the_outer_guard():
    """A numbered state names one specific state, so an outer limit on that
    same state still holds inside it."""
    script = (
        "if = {\n"
        "\tlimit = { 931 = { infrastructure > 0 } }\n"
        "\t931 = { damage_building = { type = infrastructure damage = 2 } }\n"
        "}\n"
    )
    assert _scan(script) == []


def test_random_owned_state_limit_is_clean():
    script = (
        "random_owned_state = {\n"
        "\tlimit = { dockyard > 0 }\n"
        "\tremove_building = { type = dockyard level = 1 }\n"
        "}\n"
    )
    assert _scan(script) == []


def test_every_owned_state_limit_is_clean():
    script = (
        "every_owned_state = {\n"
        "\tlimit = { infrastructure > 0 }\n"
        "\tdamage_building = { type = infrastructure damage = 1 }\n"
        "}\n"
    )
    assert _scan(script) == []


def test_random_controlled_state_limit_is_clean():
    script = (
        "random_controlled_state = {\n"
        "\tlimit = { arms_factory > 0 }\n"
        "\tdamage_building = { type = arms_factory damage = 2 }\n"
        "}\n"
    )
    assert _scan(script) == []


# --- guard must name the same building ------------------------------------


def test_guard_on_an_unrelated_condition_still_flags():
    """The exact SOV_foreign_cars_idea1 counter-example: an if/limit guarding
    an idea, not the building, must not be treated as a guard."""
    script = (
        "if = {\n"
        "\tlimit = { has_idea = SOV_foreign_cars_idea1 }\n"
        "\t652 = {\n"
        "\t\tremove_building = {\n"
        "\t\t\ttype = industrial_complex\n"
        "\t\t\tlevel = 2\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )
    findings = _scan(script)
    assert len(findings) == 1
    assert findings[0][0] == "unguarded-remove-building"
    assert "industrial_complex" in findings[0][2]


def test_guard_naming_a_different_building_still_flags():
    script = (
        "if = {\n"
        "\tlimit = { arms_factory > 1 }\n"
        "\tremove_building = {\n"
        "\t\ttype = industrial_complex\n"
        "\t\tlevel = 1\n"
        "\t}\n"
        "}\n"
    )
    findings = _scan(script)
    assert len(findings) == 1
    assert "industrial_complex" in findings[0][2]


def test_random_owned_state_limit_for_other_building_still_flags():
    script = (
        "random_owned_state = {\n"
        "\tlimit = { dockyard > 0 }\n"
        "\tremove_building = { type = arms_factory level = 1 }\n"
        "}\n"
    )
    findings = _scan(script)
    assert len(findings) == 1
    assert "arms_factory" in findings[0][2]


def test_unfiltered_random_owned_state_is_flagged():
    script = (
        "random_owned_state = {\n"
        "\tdamage_building = { type = infrastructure damage = 1 }\n"
        "}\n"
    )
    findings = _scan(script)
    assert len(findings) == 1
    assert "infrastructure" in findings[0][2]


def test_event_trigger_does_not_guard_option_effects():
    script = (
        "country_event = {\n"
        "\ttrigger = { any_owned_state = { industrial_complex > 0 } }\n"
        "\toption = {\n"
        "\t\t652 = {\n"
        "\t\t\tremove_building = { type = industrial_complex level = 1 }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )
    findings = _scan(script)
    assert len(findings) == 1
    assert "industrial_complex" in findings[0][2]


def test_decision_available_does_not_guard_remove_effect():
    script = (
        "debt_default_dismantle_military_factories = {\n"
        "\tavailable = { any_owned_state = { arms_factory > 0 } }\n"
        "\tremove_effect = {\n"
        "\t\t652 = {\n"
        "\t\t\tremove_building = { type = arms_factory level = 1 }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )
    findings = _scan(script)
    assert len(findings) == 1
    assert "arms_factory" in findings[0][2]


# --- the comparison must prove presence -----------------------------------


def test_absence_comparison_in_a_limit_still_flags():
    """`arms_factory < 1` guards the branch where the factory is *missing*."""
    script = (
        "if = {\n"
        "\tlimit = { arms_factory < 1 }\n"
        "\tremove_building = { type = arms_factory level = 1 }\n"
        "}\n"
    )
    findings = _scan(script)
    assert len(findings) == 1
    assert "arms_factory" in findings[0][2]


def test_at_most_zero_comparison_in_a_limit_still_flags():
    script = (
        "if = {\n"
        "\tlimit = { arms_factory <= 0 }\n"
        "\tremove_building = { type = arms_factory level = 1 }\n"
        "}\n"
    )
    assert len(_scan(script)) == 1


def test_equals_zero_comparison_in_a_limit_still_flags():
    script = (
        "if = {\n"
        "\tlimit = { arms_factory == 0 }\n"
        "\tremove_building = { type = arms_factory level = 1 }\n"
        "}\n"
    )
    assert len(_scan(script)) == 1


def test_at_least_one_and_exact_count_comparisons_are_clean():
    script = (
        "if = {\n"
        "\tlimit = { arms_factory >= 1 }\n"
        "\tremove_building = { type = arms_factory level = 1 }\n"
        "}\n"
        "if = {\n"
        "\tlimit = { dockyard == 2 }\n"
        "\tremove_building = { type = dockyard level = 1 }\n"
        "}\n"
    )
    assert _scan(script) == []


def test_or_branch_is_not_a_guard():
    """Either branch may be the one that held, so neither proves presence."""
    script = (
        "if = {\n"
        "\tlimit = {\n"
        "\t\tOR = {\n"
        "\t\t\tarms_factory > 0\n"
        "\t\t\thas_idea = SOV_foreign_cars_idea1\n"
        "\t\t}\n"
        "\t}\n"
        "\tremove_building = { type = arms_factory level = 1 }\n"
        "}\n"
    )
    findings = _scan(script)
    assert len(findings) == 1
    assert "arms_factory" in findings[0][2]


def test_negated_presence_check_is_not_a_guard():
    script = (
        "if = {\n"
        "\tlimit = { NOT = { arms_factory > 0 } }\n"
        "\tremove_building = { type = arms_factory level = 1 }\n"
        "}\n"
    )
    assert len(_scan(script)) == 1


def test_inverted_factor_zero_modifier_still_flags():
    """events/Brazilian.txt's polarity slip: zeroing the weight when the
    building is *present* leaves the bucket running only when it is absent."""
    script = (
        "random_list = {\n"
        "\t10 = {\n"
        "\t\tmodifier = {\n"
        "\t\t\tfactor = 0\n"
        "\t\t\tcheck_variable = { building_level@industrial_complex > 0 }\n"
        "\t\t}\n"
        "\t\tdamage_building = { type = industrial_complex damage = 0.5 }\n"
        "\t}\n"
        "}\n"
    )
    findings = _scan(script)
    assert len(findings) == 1
    assert "industrial_complex" in findings[0][2]


def test_factor_zero_modifier_with_negated_presence_is_clean():
    """`NOT = { X > 0 }` is the dual of the bare `X < 1` form."""
    script = (
        "random_list = {\n"
        "\t10 = {\n"
        "\t\tmodifier = {\n"
        "\t\t\tfactor = 0\n"
        "\t\t\tNOT = { industrial_complex > 0 }\n"
        "\t\t}\n"
        "\t\tremove_building = { type = industrial_complex level = 1 }\n"
        "\t}\n"
        "}\n"
    )
    assert _scan(script) == []


# --- province buildings in state-only triggers ------------------------------


def test_province_building_in_non_damaged_building_level_is_flagged():
    """The JAP_quake_damage case: naval_base is a province building, so the
    trigger never validates and the game logs a load error."""
    script = (
        "if = {\n"
        "\tlimit = { non_damaged_building_level = { building = naval_base level > 0 } }\n"
        "\tdamage_building = { type = naval_base damage = 0.05 }\n"
        "}\n"
    )
    findings = _scan_province(script)
    assert len(findings) == 1
    assert findings[0][0] == "province-building-state-trigger"
    assert findings[0][1] == 2
    assert "naval_base" in findings[0][2]


def test_state_building_in_non_damaged_building_level_is_clean():
    script = (
        "if = {\n"
        "\tlimit = { non_damaged_building_level = { building = air_base level > 0 } }\n"
        "\tdamage_building = { type = air_base damage = 0.05 }\n"
        "}\n"
    )
    assert _scan_province(script) == []


def test_province_building_in_any_province_building_level_is_clean():
    script = (
        "if = {\n"
        "\tlimit = { any_province_building_level = { building = naval_base level > 0 } }\n"
        "\tdamage_building = { type = naval_base damage = 0.05 }\n"
        "}\n"
    )
    assert _scan_province(script) == []


def test_province_building_trigger_does_not_count_as_a_guard():
    script = (
        "if = {\n"
        "\tlimit = { non_damaged_building_level = { building = naval_base level > 0 } }\n"
        "\tdamage_building = { type = naval_base damage = 0.05 }\n"
        "}\n"
    )
    findings = _scan(script)
    assert len(findings) == 1
    assert findings[0][0] == "unguarded-damage-building"


@pytest.mark.parametrize("building", ["supply_node", "rail_way", "naval_supply_hub"])
def test_supply_province_buildings_in_state_only_trigger_are_flagged(building):
    script = (
        "if = {\n"
        f"\tlimit = {{ non_damaged_building_level = {{ building = {building} level > 0 }} }}\n"
        f"\tdamage_building = {{ type = {building} damage = 0.05 }}\n"
        "}\n"
    )
    findings = _scan_province(script)
    assert len(findings) == 1
    assert building in findings[0][2]


def test_bare_comparison_guards_a_province_building():
    script = (
        "if = {\n"
        "\tlimit = { naval_base > 0 }\n"
        "\tdamage_building = { type = naval_base damage = 0.05 }\n"
        "}\n"
    )
    assert _scan(script) == []
    assert _scan_province(script) == []


# --- effects with no type field --------------------------------------------


def test_effect_without_a_type_field_is_not_flagged():
    """`type =` names the building; without it there is nothing to guard."""
    script = "652 = {\n\tdamage_building = {\n\t\tdamage = 1\n\t}\n}\n"
    assert _scan(script) == []


def test_modifier_without_factor_zero_is_not_a_guard():
    script = (
        "random_list = {\n"
        "\t33 = {\n"
        "\t\tmodifier = { factor = 2  industrial_complex > 0 }\n"
        "\t\tmodifier = { factor = 0  arms_factory < 1 }\n"
        "\t\tremove_building = { type = industrial_complex level = 1 }\n"
        "\t}\n"
        "}\n"
    )
    findings = _scan(script)
    assert len(findings) == 1
    assert "industrial_complex" in findings[0][2]


# --- validator wiring -------------------------------------------------------


def _run(tmp_path, monkeypatch, script):
    import validator_common

    monkeypatch.setattr(validator_common, "_LOG_LEVEL", "INFO")
    write_tree(
        tmp_path,
        {
            "common/buildings/00_buildings.txt": _BUILDINGS,
            "map/definition.csv": _DEFINITION,
            "events/test_events.txt": script,
        },
    )
    validator = V.Validator(str(tmp_path), use_colors=False, workers=1, no_cache=True)
    validator.run_validations()
    return validator


def test_run_reports_and_logs_each_unguarded_effect(tmp_path, monkeypatch):
    validator = _run(
        tmp_path,
        monkeypatch,
        "652 = {\n\tdamage_building = { type = fuel_silo damage = 1 }\n}\n",
    )

    assert [(i.severity, i.category) for i in validator._issues] == [
        ("error", "unguarded-damage-building")
    ]
    assert validator._issues[0].file == "events/test_events.txt"
    assert any(
        line.startswith("  events/test_events.txt:2 - ")
        for line in validator.output_lines
    )
    assert any(
        "1 unguarded building effect(s)" in line for line in validator.output_lines
    )


def test_run_reports_province_building_state_trigger_as_error(tmp_path, monkeypatch):
    validator = _run(
        tmp_path,
        monkeypatch,
        "if = {\n"
        "\tlimit = { non_damaged_building_level = { building = naval_base level > 0 } }\n"
        "}\n",
    )

    assert [(i.severity, i.category) for i in validator._issues] == [
        ("error", "province-building-state-trigger")
    ]


def test_random_infrastructure_slot_guard_is_a_warning(tmp_path, monkeypatch):
    validator = _run(
        tmp_path,
        monkeypatch,
        "random_owned_state = { add_building_construction = { type = infrastructure level = 1 } }",
    )
    assert [(i.severity, i.category) for i in validator._issues] == [
        ("warning", "random-infrastructure-slot-guard")
    ]


def test_run_stays_quiet_when_every_effect_is_guarded(tmp_path, monkeypatch):
    validator = _run(
        tmp_path,
        monkeypatch,
        "652 = {\n"
        "\tif = { limit = { fuel_silo > 0 }\n"
        "\t\tdamage_building = { type = fuel_silo damage = 1 }\n"
        "\t}\n"
        "}\n",
    )

    assert validator._issues == []
    assert any("All damage_building" in line for line in validator.output_lines)


# --- building placement and starting owners --------------------------------

_BUILDINGS = """buildings = {
	naval_base = {
		only_costal = yes
		level_cap = { province_max = 10 }
	}
	bunker = {
		level_cap = { province_max = 7 }
	}
	dockyard = {
		only_costal = yes
		level_cap = { state_max = 20 }
	}
}
"""

_DEFINITION = """0;0;0;0;land;false;unknown;0
1;1;1;1;land;true;plains;1
2;2;2;2;land;false;plains;1
3;3;3;3;sea;true;ocean;0
"""

_INLAND = "province 2, which map/definition.csv does not mark as coastal land"
_NO_PROVINCE = "add_building_construction type = bunker has no province"
_ID_SELECTOR = "province = { province = <id> } is not a valid selector"


def _state(body, owner="TST"):
    owner_line = f"\towner = {owner}\n" if owner else ""
    return f"state = {{\n\tid = 1\n\thistory = {{\n{owner_line}{body}\n\t}}\n}}\n"


def _construction(body):
    return f"effect = {{\n\tadd_building_construction = {{\n{body}\n\t}}\n}}\n"


# building definitions: {case: (file text, (provincial, coastal provincial))}
_DEFINITION_CASES = {
    "buildings file": (_BUILDINGS, ({"naval_base", "bunker"}, {"naval_base"})),
    "commented flags": (
        "buildings = {\n\tnaval_base = {\n\t\t# only_costal = yes\n"
        "\t\t# province_max = 10\n\t\tlevel_cap = { state_max = 10 }\n\t}\n}\n",
        (set(), set()),
    ),
    "province_max outside level_cap": (
        "buildings = {\n\tnaval_base = {\n\t\tonly_costal = yes\n"
        "\t\tprovince_max = 10\n\t}\n}\n",
        (set(), set()),
    ),
}


@pytest.mark.parametrize(
    "text, expected", _DEFINITION_CASES.values(), ids=_DEFINITION_CASES
)
def test_building_classes(text, expected):
    assert V.building_classes(text) == expected


# definition.csv: {case: (row, coastal land ids)}
_PROVINCE_CASES = {
    "coastal land": ("1;1;1;1;land;true;plains;1", {1}),
    "inland": ("2;2;2;2;land;false;plains;1", set()),
    "coastal sea": ("3;3;3;3;sea;true;ocean;0", set()),
    "header": ("province;red;green;blue;type;coastal;terrain;continent", set()),
}


@pytest.mark.parametrize("row, expected", _PROVINCE_CASES.values(), ids=_PROVINCE_CASES)
def test_coastal_land_provinces(row, expected):
    assert V.coastal_land_provinces(row)[1] == expected


# placement: {case: (file path, file text, expected findings)}
_PLACEMENT_CASES = {
    "history coastal province": (
        "history/states/1-Test.txt",
        _state("\t\tbuildings = {\n\t\t\t1 = { naval_base = 1 }\n\t\t}"),
        [],
    ),
    "history inland province": (
        "history/states/1-Test.txt",
        _state("\t\tbuildings = {\n\t\t\t2 = { naval_base = 1 }\n\t\t}"),
        [("'naval_base'", _INLAND)],
    ),
    "history date block": (
        "history/states/1-Test.txt",
        _state(
            "\t\t2017.1.1 = {\n\t\t\tbuildings = {\n"
            "\t\t\t\t2 = { naval_base = 1 }\n\t\t\t}\n\t\t}"
        ),
        [("'naval_base'", _INLAND)],
    ),
    "history province block outside a state file": (
        "common/scripted_effects/test.txt",
        _state("\t\tbuildings = {\n\t\t\t2 = { naval_base = 1 }\n\t\t}"),
        [],
    ),
    "history non-coastal building": (
        "history/states/1-Test.txt",
        _state("\t\tbuildings = {\n\t\t\t2 = { bunker = 1 }\n\t\t}"),
        [],
    ),
    "construction scalar province": (
        "events/test.txt",
        _construction("\t\ttype = naval_base\n\t\tprovince = 2"),
        [("'naval_base'", _INLAND)],
    ),
    "construction province ids": (
        "common/national_focus/test.txt",
        _construction("\t\ttype = naval_base\n\t\tprovince = { id = 1 id = 2 }"),
        [("'naval_base'", _INLAND)],
    ),
    "construction runtime provinces": (
        "events/test.txt",
        _construction(
            "\t\ttype = naval_base\n"
            "\t\tprovince = { all_provinces = yes limit_to_coastal = yes }"
        ),
        [],
    ),
    "construction state building": (
        "events/test.txt",
        _construction("\t\ttype = dockyard\n\t\tprovince = 2"),
        [],
    ),
    "sea province": (
        "events/test.txt",
        _construction("\t\ttype = naval_base\n\t\tprovince = 3"),
        [("province 3, which map/definition.csv does not mark as coastal land",)],
    ),
    "unknown province": (
        "events/test.txt",
        _construction("\t\ttype = naval_base\n\t\tprovince = 99"),
        [("province 99, which is not in map/definition.csv",)],
    ),
    "provincial building without province": (
        "events/test.txt",
        _construction("\t\ttype = bunker\n\t\tlevel = 1"),
        [(_NO_PROVINCE,)],
    ),
    "state building without province": (
        "events/test.txt",
        _construction("\t\ttype = dockyard\n\t\tlevel = 1"),
        [],
    ),
    "province id in a selector block": (
        "events/test.txt",
        _construction("\t\ttype = bunker\n\t\tprovince = { province = 2 }"),
        [(_ID_SELECTOR,)],
    ),
    "consecutive constructions": (
        "events/test.txt",
        "effect = {\n"
        "\tadd_building_construction = { type = bunker province = 1 }\n"
        "\tadd_building_construction = { type = bunker level = 1 }\n}\n",
        [(_NO_PROVINCE,)],
    ),
}


@pytest.mark.parametrize(
    "path, text, expected", _PLACEMENT_CASES.values(), ids=_PLACEMENT_CASES
)
def test_placement(tmp_path, path, text, expected):
    write_tree(
        tmp_path,
        {
            "common/buildings/00_buildings.txt": _BUILDINGS,
            "map/definition.csv": _DEFINITION,
            path: text,
        },
    )

    validator = run_validator(V.Validator, tmp_path)

    assert_findings([issue.message for issue in validator._issues], expected)


# finding position: {case: (file text, (category, line))}
_POSITION_CASES = {
    "coastal": (
        _construction("\t\ttype = naval_base\n\t\tprovince = 2"),
        ("coastal-building-not-coastal", 4),
    ),
    "missing province": (
        _construction("\t\ttype = bunker"),
        ("building-missing-province", 2),
    ),
    "id selector": (
        _construction("\t\ttype = bunker\n\t\tprovince = { province = 2 }"),
        ("province-id-in-selector-block", 4),
    ),
}


@pytest.mark.parametrize(
    "text, expected", _POSITION_CASES.values(), ids=_POSITION_CASES
)
def test_placement_finding_is_an_error_with_file_and_line(tmp_path, text, expected):
    write_tree(
        tmp_path,
        {
            "common/buildings/00_buildings.txt": _BUILDINGS,
            "map/definition.csv": _DEFINITION,
            "events/test.txt": text,
        },
    )

    (issue,) = run_validator(V.Validator, tmp_path)._issues

    assert (issue.severity, issue.file, (issue.category, issue.line)) == (
        "error",
        "events/test.txt",
        expected,
    )


def test_missing_definition_is_reported(tmp_path):
    write_tree(tmp_path, {"common/buildings/00_buildings.txt": _BUILDINGS})

    validator = run_validator(V.Validator, tmp_path)

    assert [issue.category for issue in validator._issues] == [
        "coastal-building-definition-missing"
    ]


# state facts: {case: (state file text, (owner, state-level buildings))}
_STATE_FACT_CASES = {
    "levels of one or more": (
        _state(
            "\t\tbuildings = {\n\t\t\tnuclear_reactor = 1 # comment\n"
            "\t\t\tmicrochip_plant = 0\n\t\t\t1 = { naval_base = 9 }\n\t\t}"
        ),
        ("TST", {"nuclear_reactor"}),
    ),
    "unowned": (
        _state("\t\tbuildings = { nuclear_reactor = 1 }", owner=None),
        (None, {"nuclear_reactor"}),
    ),
}


@pytest.mark.parametrize(
    "text, expected", _STATE_FACT_CASES.values(), ids=_STATE_FACT_CASES
)
def test_state_facts(text, expected):
    assert V.placement_findings(text, True)[1:] == expected


def _status_group(*members):
    return "ideas = {\n\tnuclear_status = {\n" + "\n".join(members) + "\n\t}\n}\n"


# nuclear_status: {case: (ideas file, non-default members)}
_NUCLEAR_STATUS_CASES = {
    "default member": (
        _status_group(
            "use_list_view = yes",
            "non_nuclear_power = { default = yes cost = 300 }",
            "nuclear_energy = { cost = 300 available = { has_tech = reactor_01 } }",
            "nuclear_power_def = { cost = 300 }",
        ),
        {"nuclear_energy", "nuclear_power_def"},
    ),
    "another group": ("ideas = { nuclear_stance = { foo = {} } }\n", set()),
    "brace on the next line": (
        _status_group("odd_member =", "{", "cost = 300", "}"),
        {"odd_member"},
    ),
}


@pytest.mark.parametrize(
    "text, expected", _NUCLEAR_STATUS_CASES.values(), ids=_NUCLEAR_STATUS_CASES
)
def test_nuclear_status_ideas(text, expected):
    assert V.nuclear_status_ideas(text) == expected


def test_project_building_grants_name_the_top_level_project():
    text = (
        "sp_chips = {\n\tproject_output = { facility_state_effects = {\n"
        "\t\tset_building_level = { type = microchip_plant level = 1 }\n\t} }\n}\n"
        "sp_other = { allowed = { always = yes } }\n"
    )

    assert V.project_building_grants(text) == {("microchip_plant", "sp_chips")}


def test_country_facts_read_tokens_and_completed_projects():
    tokens, completed = V.country_facts(
        "add_ideas = { nuclear_energy }\n"
        "complete_special_project = sp:sp_chips\n"
        "complete_special_project = sp_bare\n"
        "# complete_special_project = sp:sp_commented\n"
    )

    assert "nuclear_energy" in tokens
    assert completed == {"sp_chips"}


_COUNTRY = "history/countries/TST - Test.txt"
_IDEAS = {"common/ideas/md.txt": {"nuclear_ideas": {"nuclear_energy"}}}
_GRANT = {"common/special_projects/projects/md.txt": {"granted": {("chips", "sp_a")}}}


def _owner(*buildings):
    return {"history/states/1-Test.txt": {"owner": "TST", "buildings": set(buildings)}}


def _country(tokens=(), completed=()):
    return {_COUNTRY: {"tokens": set(tokens), "completed": set(completed)}}


# ownership join: {case: (per-file facts, expected findings)}
_OWNERSHIP_CASES = {
    "reactor owner grants an idea": (
        {**_IDEAS, **_owner("nuclear_reactor"), **_country({"nuclear_energy"})},
        [],
    ),
    "reactor owner without an idea": (
        {**_IDEAS, **_owner("nuclear_reactor"), **_country({"non_nuclear_power"})},
        [("TST", "grants no nuclear_status idea (nuclear_energy)")],
    ),
    "reactor owner without a country file": (
        {**_IDEAS, **_owner("nuclear_reactor")},
        [("TST", "nuclear_reactor", "no history/countries/")],
    ),
    "no nuclear_status group": ({**_owner("nuclear_reactor"), **_country()}, []),
    "granted building with its project": (
        {**_GRANT, **_owner("chips"), **_country(completed={"sp_a"})},
        [],
    ),
    "granted building without its project": (
        {**_GRANT, **_owner("chips"), **_country(completed={"sp_b"})},
        [("TST", "chips", "(sp:sp_a)")],
    ),
    "granted building without a country file": (
        {**_GRANT, **_owner("chips")},
        [("TST", "chips", "no history/countries/")],
    ),
}


@pytest.mark.parametrize(
    "facts, expected", _OWNERSHIP_CASES.values(), ids=_OWNERSHIP_CASES
)
def test_ownership_findings(facts, expected):
    rows = V.ownership_findings(facts)

    assert_findings([message for _category, _file, _line, message in rows], expected)


_OWNERSHIP_TREE = {
    "common/ideas/md.txt": _status_group("nuclear_energy = { cost = 300 }"),
    "history/states/1-Test.txt": _state("\t\tbuildings = { nuclear_reactor = 1 }"),
    _COUNTRY: "add_ideas = { non_nuclear_power }\n",
    "events/unrelated.txt": "effect = { add_stability = 0.1 }\n",
}


def test_ownership_finding_is_an_error_on_the_country_file(tmp_path):
    validator = run_validator(V.Validator, write_tree(tmp_path, _OWNERSHIP_TREE))

    (issue,) = validator._issues

    assert (issue.severity, issue.category, issue.file) == (
        "error",
        "reactor-owner-without-nuclear-status",
        _COUNTRY,
    )


def test_staged_run_joins_unstaged_ownership_inputs(tmp_path, monkeypatch):
    write_tree(tmp_path, _OWNERSHIP_TREE)
    monkeypatch.setenv("MD_STAGED_FILES", "events/unrelated.txt")

    validator = run_validator(V.Validator, tmp_path, staged_only=True)

    assert [issue.file for issue in validator._issues] == [_COUNTRY]


# staged: {case: (staged paths, files with findings)}
_STAGED_CASES = {
    "placement file": ("events/a.txt", {"events/a.txt"}),
    "definition change": ("map/definition.csv", {"events/a.txt", "events/b.txt"}),
    "buildings change": (
        "common/buildings/00_buildings.txt",
        {"events/a.txt", "events/b.txt"},
    ),
}


@pytest.mark.parametrize("staged, expected", _STAGED_CASES.values(), ids=_STAGED_CASES)
def test_staged_scope(tmp_path, monkeypatch, staged, expected):
    inland = _construction("\t\ttype = naval_base\n\t\tprovince = 2")
    write_tree(
        tmp_path,
        {
            "common/buildings/00_buildings.txt": _BUILDINGS,
            "map/definition.csv": _DEFINITION,
            "events/a.txt": inland,
            "events/b.txt": inland,
        },
    )
    monkeypatch.setenv("MD_STAGED_FILES", staged)

    validator = run_validator(V.Validator, tmp_path, staged_only=True)

    assert {issue.file for issue in validator._issues} == expected


# --- scan_file input contract -----------------------------------------------


def test_scan_file_reads_and_relativizes_path(tmp_path, monkeypatch):
    monkeypatch.delenv("MD_NO_CACHE", raising=False)
    path = write_under(
        tmp_path,
        "events/Test.txt",
        "wrapper = {\n\tdamage_building = { type = fuel_silo damage = 1 }\n}\n",
    )
    args = (str(path), str(tmp_path) + "/")
    expected = (
        [
            (
                "unguarded-damage-building",
                "events/Test.txt",
                2,
                "damage_building = { type = fuel_silo ... } is not guarded by a "
                "check that fuel_silo exists",
            )
        ],
        {},
    )

    assert V.scan_file(args) == expected
    assert V.scan_file(args) == expected


def test_scan_file_skips_files_without_building_content(tmp_path, monkeypatch):
    def scanned(*_args):
        raise AssertionError("a file without building content reached the scan")

    monkeypatch.setattr(disk_cache, "per_file_cached_by_content", scanned)
    path = write_under(tmp_path, "quiet.txt", "focus = { id = TST_focus }\n")

    assert V.scan_file((str(path), str(tmp_path) + "/")) == ([], {})


def test_scan_file_reports_unreadable_input(tmp_path):
    with pytest.raises(ValueError, match="Cannot scan"):
        V.scan_file((str(tmp_path / "missing.txt"), str(tmp_path)))
