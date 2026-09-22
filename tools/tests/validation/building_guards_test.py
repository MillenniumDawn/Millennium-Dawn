"""Tests for validate_building_guards.

A `damage_building` / `remove_building` effect naming a building type must sit
behind a guard trigger that proves that same building type is present --
otherwise the call spams error.log at scale (issue #2806). Guard detection
must track *which* building is proven present, not merely "is there an if?" --
an `if`/`limit` guarding something else entirely (an idea, a flag) must still
flag the effect inside it.
"""

import re

import pytest
import validate_building_guards as V
from shared.paths import REPO_ROOT as _MOD_ROOT


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


def test_province_building_list_covers_every_province_max_building():
    """`_PROVINCE_BUILDINGS` is a hand-kept mirror of the buildings that carry a
    province_max level cap; this fails when a new one is added to the game."""
    text = (_MOD_ROOT / "common" / "buildings" / "00_buildings.txt").read_text(
        encoding="utf-8-sig"
    )
    declared = set()
    building = None
    for line in text.splitlines():
        match = re.match(r"^\t([A-Za-z_][A-Za-z0-9_]*) = \{", line)
        if match:
            building = match.group(1)
        elif building and re.search(r"\bprovince_max\s*=", line):
            declared.add(building)
    assert declared
    assert declared <= V._PROVINCE_BUILDINGS


def test_bare_comparison_guards_a_province_building():
    script = (
        "if = {\n"
        "\tlimit = { naval_base > 0 }\n"
        "\tdamage_building = { type = naval_base damage = 0.05 }\n"
        "}\n"
    )
    assert _scan(script) == []
    assert _scan_province(script) == []


# --- scan_file cache --------------------------------------------------------


def test_scan_file_reads_and_relativizes_path(tmp_path, monkeypatch):
    monkeypatch.delenv("MD_NO_CACHE", raising=False)
    events_dir = tmp_path / "events"
    events_dir.mkdir()
    filepath = events_dir / "test_events.txt"
    filepath.write_text(
        "652 = {\n"
        "\tdamage_building = {\n"
        "\t\ttype = fuel_silo\n"
        "\t\tdamage = 1\n"
        "\t}\n"
        "}\n",
        encoding="utf-8",
    )
    mod_path = str(tmp_path) + "/"
    findings = V.scan_file((str(filepath), mod_path))
    assert len(findings) == 1
    category, relative, line, message = findings[0]
    assert category == "unguarded-damage-building"
    assert relative == "events/test_events.txt"
    assert line == 2
    assert "fuel_silo" in message


def test_scan_file_skips_files_without_building_effects(tmp_path):
    filepath = tmp_path / "no_buildings.txt"
    filepath.write_text("focus = { id = TST_focus }\n", encoding="utf-8")
    assert V.scan_file((str(filepath), str(tmp_path) + "/")) == []


def test_scan_file_skips_unreadable_files(tmp_path):
    (tmp_path / "damage_building.txt").mkdir()
    assert V.scan_file((str(tmp_path / "damage_building.txt"), str(tmp_path))) == []


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


def _run(tmp_path, write_path, monkeypatch, script):
    import validator_common

    monkeypatch.setattr(validator_common, "_LOG_LEVEL", "INFO")
    write_path(tmp_path, "events/test_events.txt", script)
    validator = V.Validator(str(tmp_path), use_colors=False, workers=1, no_cache=True)
    validator.run_validations()
    return validator


def test_run_reports_and_logs_each_unguarded_effect(tmp_path, write_path, monkeypatch):
    validator = _run(
        tmp_path,
        write_path,
        monkeypatch,
        "652 = {\n\tdamage_building = { type = fuel_silo damage = 1 }\n}\n",
    )

    assert [(i.severity, i.category) for i in validator._issues] == [
        ("warning", "unguarded-damage-building")
    ]
    assert validator._issues[0].file == "events/test_events.txt"
    assert any(
        line.startswith("  events/test_events.txt:2 - ")
        for line in validator.output_lines
    )
    assert any(
        "1 unguarded building effect(s)" in line for line in validator.output_lines
    )


def test_run_stays_quiet_when_every_effect_is_guarded(
    tmp_path, write_path, monkeypatch
):
    validator = _run(
        tmp_path,
        write_path,
        monkeypatch,
        "652 = {\n"
        "\tif = { limit = { fuel_silo > 0 }\n"
        "\t\tdamage_building = { type = fuel_silo damage = 1 }\n"
        "\t}\n"
        "}\n",
    )

    assert validator._issues == []
    assert any("All damage_building" in line for line in validator.output_lines)
