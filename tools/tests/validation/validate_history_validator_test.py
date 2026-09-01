"""End-to-end tests for the validate_history Validator over a synthetic mod.

Each check is wired into `run_validations`, so one clean mod proves every pass
stays silent on correct content and one deliberately broken mod proves each
pass still reports its own finding when the others also fire.
"""

import os

import pytest
import validate_history as V
from shared.suite import write_under_str as _write

_TECHNOLOGIES = """technologies = {
\troot_tech = {
\t\tpath = {
\t\t\tleads_to_tech = child_tech
\t\t}
\t\tenable_equipment_modules = {
\t\t\tengine_2
\t\t}
\t}
\tchild_tech = {
\t\tcategory = armor
\t}
\tadvanced_engines = {
\t\tenable_equipment_modules = {
\t\t\tengine_9
\t\t}
\t}
\tsp_tech = {
\t\tallow = {
\t\t\tis_special_project_completed = sp:sp_microchip
\t\t}
\t}
\tnsb_tech = {
\t\tallow_branch = {
\t\t\thas_dlc = "No Step Back"
\t\t}
\t}
}
"""

_PROJECTS = """sp_microchip = {
\tallowed = { always = yes }
\tproject_output = {
\t\tcustom_effect_tooltip = {
\t\t\tlocalization_key = SP_UNLOCK_TECH
\t\t\tTECH = sp_tech
\t\t}
\t\tfacility_state_effects = {
\t\t\tset_building_level = {
\t\t\t\ttype = microchip_plant
\t\t\t\tlevel = 1
\t\t\t}
\t\t}
\t}
}
sp_open = {
\tallowed = { always = yes }
}
"""

_IDEAS = """ideas = {
\tnuclear_status = {
\t\tnon_nuclear_power = {
\t\t\tdefault = yes
\t\t}
\t\tnuclear_energy = {
\t\t\tcost = 300
\t\t}
\t}
}
"""

_GOOD_COUNTRY = """capital = 1
oob = "TST_1990"
add_ideas = { nuclear_energy }
complete_special_project = sp:sp_microchip
complete_special_project = sp:sp_open
set_technology = {
\troot_tech = 1
\tchild_tech = 1
\tsp_tech = 1
}
create_equipment_variant = {
\tname = "Type 32"
\ttype = frigate_hull_2
\tmodules = {
\t\tengine_slot = engine_2
\t}
}
"""

_BAD_COUNTRY = """oob = "BAD_missing"
add_ideas = { non_nuclear_power }
set_technology = {
\tchild_tech = 1
\tsp_tech = 1
}
if = {
\tlimit = { has_dlc = "No Step Back" }
\tcomplete_special_project = sp:sp_open
\telse = {
\t\tset_technology = { nsb_tech = 1 }
\t}
}
create_equipment_variant = {
\tname = "Ghost"
\ttype = frigate_hull_2
\tmodules = {
\t\tengine_slot = engine_9
\t}
}
"""


def _state(tag, state_id):
    return (
        "state = {\n"
        f"\tid = {state_id}\n"
        "\thistory = {\n"
        f"\t\towner = {tag}\n"
        "\t\tbuildings = {\n"
        "\t\t\tnuclear_reactor = 1\n"
        "\t\t\tmicrochip_plant = 1\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )


def _base_mod(tmp_path):
    _write(tmp_path, "common/technologies/md.txt", _TECHNOLOGIES)
    _write(tmp_path, "common/special_projects/projects/md.txt", _PROJECTS)
    _write(tmp_path, "common/ideas/md.txt", _IDEAS)
    _write(tmp_path, "history/units/TST_1990.txt", "units = {\n}\n")
    _write(tmp_path, "history/states/1-Test.txt", _state("TST", 1))
    _write(tmp_path, "history/countries/TST - Test.txt", _GOOD_COUNTRY)


def _run(tmp_path):
    validator = V.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    validator.run_validations()
    return validator


@pytest.fixture(autouse=True)
def _no_disk_cache(monkeypatch):
    monkeypatch.setenv("MD_NO_CACHE", "1")


def test_clean_mod_passes_every_history_check(tmp_path):
    _base_mod(tmp_path)
    validator = _run(tmp_path)
    assert validator._issues == []
    assert validator.errors_found == 0


def test_each_history_check_reports_its_own_finding(tmp_path):
    _base_mod(tmp_path)
    _write(tmp_path, "history/states/2-Bad.txt", _state("BAD", 2))
    _write(tmp_path, "history/countries/BAD - Bad.txt", _BAD_COUNTRY)

    validator = _run(tmp_path)
    messages = sorted(issue.message for issue in validator._issues)

    assert messages == [
        "BAD - Bad.txt: child_tech requires root_tech",
        "BAD - Bad.txt: no capital defined",
        'BAD - Bad.txt: nsb_tech is granted while "No Step Back" is inactive, '
        "but its tech branch requires that DLC [NOT No Step Back]",
        "BAD - Bad.txt: sp:sp_open is always-available but is completed only "
        'inside a "No Step Back" block - hoist it to unconditional scope so '
        "players without that DLC still complete it",
        "BAD - Bad.txt: sp_tech requires special project sp:sp_microchip but it "
        "is not completed at game start [any DLC configuration]",
        'BAD - Bad.txt: variant "Ghost" uses engine_9 without enabling tech '
        "advanced_engines",
        "BAD: owns a state starting with microchip_plant but never completes "
        "the granting special project (sp:sp_microchip)",
        "BAD: owns a state with a nuclear_reactor at game start but grants no "
        "nuclear_status idea (nuclear_energy)",
        'oob references "BAD_missing" but no history/units/BAD_missing.txt file exists',
    ]
    assert validator.errors_found == len(messages)


def test_missing_oob_target_is_reported_with_its_line(tmp_path):
    _base_mod(tmp_path)
    _write(
        tmp_path,
        "history/countries/TST - Test.txt",
        _GOOD_COUNTRY.replace('oob = "TST_1990"', 'oob = "TST_gone"'),
    )
    validator = _run(tmp_path)
    assert [(i.file, i.line, i.message) for i in validator._issues] == [
        (
            "TST - Test.txt",
            2,
            'oob references "TST_gone" but no history/units/TST_gone.txt file exists',
        )
    ]


def test_state_owner_without_a_land_oob_is_reported(tmp_path):
    _base_mod(tmp_path)
    _write(
        tmp_path,
        "history/countries/TST - Test.txt",
        _GOOD_COUNTRY.replace('oob = "TST_1990"', 'set_air_oob = "TST_1990"'),
    )
    validator = _run(tmp_path)
    assert len(validator._issues) == 1
    assert "has no land OOB" in validator._issues[0].message


def test_project_output_claiming_an_ungated_tech_is_reported(tmp_path):
    _base_mod(tmp_path)
    _write(
        tmp_path,
        "common/special_projects/projects/md.txt",
        _PROJECTS.replace("TECH = sp_tech", "TECH = child_tech"),
    )
    validator = _run(tmp_path)
    messages = [issue.message for issue in validator._issues]
    assert (
        "sp:sp_microchip: project_output claims to unlock child_tech, but "
        "child_tech is gated by no project; this project gates sp_tech"
    ) in messages


def test_building_checks_are_skipped_without_ideas_or_projects(tmp_path):
    # No nuclear_status group and no set_building_level grant: both building
    # checks must skip rather than report every reactor owner.
    _write(tmp_path, "common/technologies/md.txt", _TECHNOLOGIES)
    _write(tmp_path, "history/units/TST_1990.txt", "units = {\n}\n")
    _write(tmp_path, "history/states/1-Test.txt", _state("TST", 1))
    _write(
        tmp_path,
        "history/countries/TST - Test.txt",
        'capital = 1\noob = "TST_1990"\n',
    )
    validator = _run(tmp_path)
    assert validator._issues == []


def test_staged_mode_limits_history_files_to_staged_country_files(
    tmp_path, monkeypatch
):
    _base_mod(tmp_path)
    _write(tmp_path, "history/countries/BAD - Bad.txt", _BAD_COUNTRY)
    monkeypatch.setenv("MD_STAGED_FILES", "history/countries/TST - Test.txt")

    validator = V.Validator(
        mod_path=str(tmp_path), use_colors=False, staged_only=True, workers=1
    )
    files = validator._get_history_files()
    assert [os.path.basename(f) for f in files] == ["TST - Test.txt"]


def test_staged_mode_without_staged_files_checks_nothing(tmp_path, monkeypatch):
    _base_mod(tmp_path)
    monkeypatch.setenv("MD_STAGED_FILES", "")

    validator = V.Validator(
        mod_path=str(tmp_path), use_colors=False, staged_only=True, workers=1
    )
    assert validator._get_history_files() == []
