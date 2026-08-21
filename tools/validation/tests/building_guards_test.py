"""Tests for validate_building_guards.

A `damage_building` / `remove_building` effect naming a building type must sit
behind a guard trigger that proves that same building type is present --
otherwise the call spams error.log at scale (issue #2806). Guard detection
must track *which* building is proven present, not merely "is there an if?" --
an `if`/`limit` guarding something else entirely (an idea, a flag) must still
flag the effect inside it.
"""

import validate_building_guards as V


def _scan(script):
    scanner = V.Scanner(V._sanitize(script))
    scanner.walk(0, len(scanner.text), V.Context())
    return scanner.findings


def _messages(script):
    return [message for _, _, message in _scan(script)]


# --- unguarded effects --------------------------------------------------


def test_unguarded_damage_building_is_flagged():
    script = (
        "652 = {\n"
        "\tdamage_building = {\n"
        "\t\ttype = fuel_silo\n"
        "\t\tdamage = 1\n"
        "\t}\n"
        "}\n"
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


def test_any_core_state_preselection_guard_is_clean():
    """Form D: common/national_focus/turkey.txt's country-scope pre-selection."""
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
