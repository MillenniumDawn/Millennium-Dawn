"""Tests for the special-project completion check in validate_history.

A tech whose `allow` block contains `is_special_project_completed = sp:sp_X`
can only be researched after the matching special project is finished. A
country that starts with the tech but never completed the project has to
research the project before it can advance that branch, and its project-gated
equipment stays locked. The check walks each (tech, DLC-configuration) pair in
the history file and reports any tech whose required SP is not completed in the
same configuration, unless the SP is DLC-limited to a DLC absent in that
configuration (then the subsystem is off and the requirement is moot).
"""

import validate_history as V


def _write_tech(tmp_path, name, body):
    """Write a single tech definition to a stub common/technologies file."""
    tech_dir = tmp_path / "common" / "technologies"
    tech_dir.mkdir(parents=True, exist_ok=True)
    (tech_dir / "test.txt").write_text("technologies = {\n" + body + "\n}\n")


def _write_sp(tmp_path, body):
    """Write special-project definitions to a stub projects file."""
    sp_dir = tmp_path / "common" / "special_projects" / "projects"
    sp_dir.mkdir(parents=True, exist_ok=True)
    (sp_dir / "test.txt").write_text(body)


def _write_country(tmp_path, name, body):
    cdir = tmp_path / "history" / "countries"
    cdir.mkdir(parents=True, exist_ok=True)
    fp = cdir / name
    fp.write_text(body)
    return str(fp)


def test_parse_tech_sp_requirements_collects_single_sp(tmp_path):
    _write_tech(
        tmp_path,
        "AT_upgrade_2",
        "\tAT_upgrade_2 = {\n"
        "\t\tallow = {\n"
        "\t\t\tROOT = {\n"
        "\t\t\t\tis_special_project_completed = sp:sp_ground_fireandforget\n"
        "\t\t\t}\n"
        "\t\t}\n"
        "\t}\n",
    )
    reqs = V.parse_tech_sp_requirements(str(tmp_path))
    assert reqs == {"AT_upgrade_2": {"sp_ground_fireandforget"}}


def test_parse_tech_sp_requirements_collects_multiple_sps(tmp_path):
    _write_tech(
        tmp_path,
        "gen_6_medium",
        "\tgen_6_medium = {\n"
        "\t\tallow = {\n"
        "\t\t\tROOT = {\n"
        "\t\t\t\tis_special_project_completed = sp:sp_aircraft_project\n"
        "\t\t\t\tis_special_project_completed = sp:sp_fully_autonomous_fighters\n"
        "\t\t\t}\n"
        "\t\t}\n"
        "\t}\n",
    )
    reqs = V.parse_tech_sp_requirements(str(tmp_path))
    assert reqs == {
        "gen_6_medium": {"sp_aircraft_project", "sp_fully_autonomous_fighters"}
    }


def test_parse_tech_sp_requirements_skips_outer_technologies_block(tmp_path):
    # The literal `technologies` key must not be treated as a tech definition
    # even when its block contents have no SP allows.
    _write_tech(
        tmp_path,
        "sentinel",
        "\tAT_upgrade_2 = {\n"
        "\t\tallow = {\n"
        "\t\t\tROOT = {\n"
        "\t\t\t\tis_special_project_completed = sp:sp_ground_fireandforget\n"
        "\t\t\t}\n"
        "\t\t}\n"
        "\t}\n",
    )
    reqs = V.parse_tech_sp_requirements(str(tmp_path))
    assert "technologies" not in reqs
    assert "AT_upgrade_2" in reqs


def test_parse_sp_allowed_dlc_maps_dlc_limited_only(tmp_path):
    # A project gated on has_dlc is mapped; a generic (always yes) project and a
    # tag-locked project are not.
    _write_sp(
        tmp_path,
        "sp_armoured_vehicle_project = {\n"
        '\tallowed = { has_dlc = "No Step Back" }\n'
        "}\n"
        "sp_naval_vessel_project = {\n"
        "\tallowed = { always = yes }\n"
        "}\n"
        "sp_libya_gmmr_phase3_project = {\n"
        "\tallowed = { original_tag = LBA }\n"
        "}\n",
    )
    allowed = V.parse_sp_allowed_dlc(str(tmp_path))
    assert allowed == {"sp_armoured_vehicle_project": ["No Step Back"]}


def test_parse_sp_allowed_dlc_collects_multiple_dlcs(tmp_path):
    # A project whose allowed block ANDs two DLCs must map to both, sorted.
    _write_sp(
        tmp_path,
        "sp_air_railguns = {\n"
        '\tallowed = { has_dlc = "By Blood Alone" has_dlc = "No Step Back" }\n'
        "}\n",
    )
    allowed = V.parse_sp_allowed_dlc(str(tmp_path))
    assert allowed == {"sp_air_railguns": ["By Blood Alone", "No Step Back"]}


def test_parse_sp_always_yes(tmp_path):
    _write_sp(
        tmp_path,
        "sp_awacs_project = {\n\tallowed = { always = yes }\n}\n"
        "sp_armoured_vehicle_project = {\n"
        '\tallowed = { has_dlc = "No Step Back" }\n'
        "}\n"
        "sp_libya_gmmr_phase3_project = {\n"
        "\tallowed = { original_tag = LBA }\n"
        "}\n",
    )
    assert V.parse_sp_always_yes(str(tmp_path)) == {"sp_awacs_project"}


def test_parse_history_file_returns_sp_set_per_branch(tmp_path, monkeypatch):
    # A country that completes the SP only in the NSB branch should have it
    # in the NSB set but not the non-NSB set.
    monkeypatch.setenv("MD_NO_CACHE", "1")
    fp = _write_country(
        tmp_path,
        "TST - Test.txt",
        "if = {\n"
        '\tlimit = { has_dlc = "No Step Back" }\n'
        "\tcomplete_special_project = sp:sp_armoured_vehicle_project\n"
        "\tset_technology = { mbt_tech = 1 }\n"
        "\telse = {\n"
        "\t\tset_technology = { mbt_tech = 1 }\n"
        "\t}\n"
        "}\n",
    )
    branches = V.parse_history_file(fp, str(tmp_path))
    by_ctx = {ctx: (techs, sps) for techs, sps, ctx in branches}
    assert "No Step Back" in by_ctx
    assert "NOT No Step Back" in by_ctx
    assert "sp_armoured_vehicle_project" in by_ctx["No Step Back"][1]
    assert "sp_armoured_vehicle_project" not in by_ctx["NOT No Step Back"][1]


def test_nested_else_keeps_tech_in_correct_branch(tmp_path, monkeypatch):
    # Regression: a tech that sits after a nested `else` inside a DLC `if` body
    # must keep the enclosing `if`'s DLC guard, not be flipped into its branch.
    monkeypatch.setenv("MD_NO_CACHE", "1")
    fp = _write_country(
        tmp_path,
        "TST - Test.txt",
        "if = {\n"
        '\tlimit = { has_dlc = "By Blood Alone" }\n'
        "\tset_technology = { gen_4_medium = 1 }\n"
        "\tif = {\n"
        "\t\tlimit = { has_country_flag = foo }\n"
        "\t\tset_technology = { gen_3_medium = 1 }\n"
        "\t\telse = {\n"
        "\t\t\tset_technology = { gen_2_medium = 1 }\n"
        "\t\t}\n"
        "\t}\n"
        "\tset_technology = { awacs_plane1 = 1 }\n"
        "}\n",
    )
    branches = V.parse_history_file(fp, str(tmp_path))
    by_ctx = {ctx: techs for techs, _sps, ctx in branches}
    # awacs_plane1 comes after the nested (non-DLC) if/else but is still inside
    # the By Blood Alone if body.
    assert "awacs_plane1" in by_ctx["By Blood Alone"]
    assert "awacs_plane1" not in by_ctx["NOT By Blood Alone"]


def test_validate_country_sp_requirements_flags_missing_sp(tmp_path, monkeypatch):
    monkeypatch.setenv("MD_NO_CACHE", "1")
    tech_sp_reqs = {"mbt_tech": {"sp_armoured_vehicle_project"}}
    fp = _write_country(
        tmp_path,
        "TST - Test.txt",
        "set_technology = {\n\tmbt_tech = 1\n}\n",
    )
    errors = V.validate_country_sp_requirements((fp, tech_sp_reqs, {}, str(tmp_path)))
    assert len(errors) == 1
    assert "mbt_tech" in errors[0]
    assert "sp_armoured_vehicle_project" in errors[0]
    assert "not completed" in errors[0]


def test_validate_country_sp_requirements_clean_when_sp_completed(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("MD_NO_CACHE", "1")
    tech_sp_reqs = {"AT_upgrade_2": {"sp_ground_fireandforget"}}
    fp = _write_country(
        tmp_path,
        "TST - Test.txt",
        "complete_special_project = sp:sp_ground_fireandforget\n"
        "set_technology = {\n\tAT_upgrade_2 = 1\n}\n",
    )
    assert (
        V.validate_country_sp_requirements((fp, tech_sp_reqs, {}, str(tmp_path))) == []
    )


def test_validate_country_sp_requirements_scopes_to_dlc_branch(tmp_path, monkeypatch):
    # The SP is completed only in the NSB branch; the non-NSB branch must
    # not be flagged because the tech is only granted in the NSB branch.
    monkeypatch.setenv("MD_NO_CACHE", "1")
    tech_sp_reqs = {"mbt_tech": {"sp_armoured_vehicle_project"}}
    fp = _write_country(
        tmp_path,
        "TST - Test.txt",
        "if = {\n"
        '\tlimit = { has_dlc = "No Step Back" }\n'
        "\tcomplete_special_project = sp:sp_armoured_vehicle_project\n"
        "\tset_technology = { mbt_tech = 1 }\n"
        "\telse = {\n"
        "\t\tset_technology = { MBT_1 = 1 }\n"
        "\t}\n"
        "}\n",
    )
    assert (
        V.validate_country_sp_requirements((fp, tech_sp_reqs, {}, str(tmp_path))) == []
    )


def test_generic_sp_completed_only_in_dlc_branch_is_flagged(tmp_path, monkeypatch):
    # A generic project (available regardless of DLC) completed only inside a
    # DLC `if` leaves the non-DLC branch's tech uncovered.
    monkeypatch.setenv("MD_NO_CACHE", "1")
    tech_sp_reqs = {"awacs_plane1": {"sp_awacs_project"}}
    fp = _write_country(
        tmp_path,
        "TST - Test.txt",
        "if = {\n"
        '\tlimit = { has_dlc = "By Blood Alone" }\n'
        "\tcomplete_special_project = sp:sp_awacs_project\n"
        "\tset_technology = { awacs_plane1 = 1 }\n"
        "\telse = {\n"
        "\t\tset_technology = { awacs_plane1 = 1 }\n"
        "\t}\n"
        "}\n",
    )
    # sp_awacs_project is generic: not in sp_allowed_dlc, so never suppressed.
    errors = V.validate_country_sp_requirements((fp, tech_sp_reqs, {}, str(tmp_path)))
    assert len(errors) == 1
    assert "awacs_plane1" in errors[0]
    assert "NOT By Blood Alone" in errors[0]


def test_dlc_limited_sp_suppressed_when_dlc_absent(tmp_path, monkeypatch):
    # A tech gated on a DLC-limited project, granted only where that DLC is
    # absent, must not be flagged: without the DLC the subsystem does not exist.
    monkeypatch.setenv("MD_NO_CACHE", "1")
    tech_sp_reqs = {"nsb_armor_tech": {"sp_armoured_vehicle_project"}}
    sp_allowed_dlc = {"sp_armoured_vehicle_project": ["No Step Back"]}
    fp = _write_country(
        tmp_path,
        "TST - Test.txt",
        "if = {\n"
        '\tlimit = { has_dlc = "No Step Back" }\n'
        "\tset_technology = { other_tech = 1 }\n"
        "\telse = {\n"
        "\t\tset_technology = { nsb_armor_tech = 1 }\n"
        "\t}\n"
        "}\n",
    )
    assert (
        V.validate_country_sp_requirements(
            (fp, tech_sp_reqs, sp_allowed_dlc, str(tmp_path))
        )
        == []
    )


def test_dlc_limited_sp_flagged_when_dlc_present_and_missing(tmp_path, monkeypatch):
    # Same project, but the tech is granted where the DLC is present and the
    # project is never completed: this is a real gap.
    monkeypatch.setenv("MD_NO_CACHE", "1")
    tech_sp_reqs = {"mbt_tech": {"sp_armoured_vehicle_project"}}
    sp_allowed_dlc = {"sp_armoured_vehicle_project": ["No Step Back"]}
    fp = _write_country(
        tmp_path,
        "TST - Test.txt",
        "if = {\n"
        '\tlimit = { has_dlc = "No Step Back" }\n'
        "\tset_technology = { mbt_tech = 1 }\n"
        "\telse = {\n"
        "\t\tset_technology = { MBT_1 = 1 }\n"
        "\t}\n"
        "}\n",
    )
    errors = V.validate_country_sp_requirements(
        (fp, tech_sp_reqs, sp_allowed_dlc, str(tmp_path))
    )
    assert len(errors) == 1
    assert "mbt_tech" in errors[0]
    assert "No Step Back" in errors[0]


def test_compound_dlc_sp_suppressed_when_any_required_dlc_absent(tmp_path, monkeypatch):
    # A tech gated on a project that needs BOTH DLCs must not be flagged in a
    # configuration missing either one — the project cannot exist there. Here the
    # tech is granted in the NOT-No-Step-Back branch, and the project also needs
    # No Step Back, so the requirement is moot. The old first-DLC-only parse
    # (which recorded only "By Blood Alone") would have flagged this.
    monkeypatch.setenv("MD_NO_CACHE", "1")
    tech_sp_reqs = {"tech_tank_nuclear_engine_1": {"sp_nuclear_engine_tank"}}
    sp_allowed_dlc = {"sp_nuclear_engine_tank": ["By Blood Alone", "No Step Back"]}
    fp = _write_country(
        tmp_path,
        "TST - Test.txt",
        "if = {\n"
        '\tlimit = { has_dlc = "No Step Back" }\n'
        "\tset_technology = { other_tech = 1 }\n"
        "\telse = {\n"
        "\t\tset_technology = { tech_tank_nuclear_engine_1 = 1 }\n"
        "\t}\n"
        "}\n",
    )
    assert (
        V.validate_country_sp_requirements(
            (fp, tech_sp_reqs, sp_allowed_dlc, str(tmp_path))
        )
        == []
    )


def test_sp_misplacement_flags_dlc_only_completion(tmp_path):
    always_yes = {"sp_helicopter_project"}
    fp = _write_country(
        tmp_path,
        "TST - Test.txt",
        "if = {\n"
        '\tlimit = { has_dlc = "No Step Back" }\n'
        "\tcomplete_special_project = sp:sp_helicopter_project\n"
        "}\n",
    )
    errors = V.validate_country_sp_misplacement((fp, always_yes, str(tmp_path)))
    assert len(errors) == 1
    assert "sp_helicopter_project" in errors[0]
    assert "No Step Back" in errors[0]


def test_sp_misplacement_clean_when_unconditional(tmp_path):
    always_yes = {"sp_helicopter_project"}
    fp = _write_country(
        tmp_path,
        "TST - Test.txt",
        "complete_special_project = sp:sp_helicopter_project\n",
    )
    assert V.validate_country_sp_misplacement((fp, always_yes, str(tmp_path))) == []


def test_sp_misplacement_clean_with_redundant_dlc_duplicate(tmp_path):
    # An unconditional completion plus a redundant one inside a DLC block is fine.
    always_yes = {"sp_helicopter_project"}
    fp = _write_country(
        tmp_path,
        "TST - Test.txt",
        "complete_special_project = sp:sp_helicopter_project\n"
        "if = {\n"
        '\tlimit = { has_dlc = "No Step Back" }\n'
        "\tcomplete_special_project = sp:sp_helicopter_project\n"
        "}\n",
    )
    assert V.validate_country_sp_misplacement((fp, always_yes, str(tmp_path))) == []


def test_sp_misplacement_ignores_dlc_gated_project(tmp_path):
    # A genuinely DLC-gated project (not in always_yes) completed inside its
    # matching DLC block is correct, not a misplacement.
    always_yes = {"sp_helicopter_project"}
    fp = _write_country(
        tmp_path,
        "TST - Test.txt",
        "if = {\n"
        '\tlimit = { has_dlc = "Gotterdammerung" }\n'
        "\tcomplete_special_project = sp:sp_nuclear_warhead_program\n"
        "}\n",
    )
    assert V.validate_country_sp_misplacement((fp, always_yes, str(tmp_path))) == []


def test_validate_country_sp_requirements_flags_multi_sp_tech(tmp_path, monkeypatch):
    monkeypatch.setenv("MD_NO_CACHE", "1")
    tech_sp_reqs = {
        "gen_6_medium": {"sp_aircraft_project", "sp_fully_autonomous_fighters"}
    }
    # Only one of the two SPs is completed — the tech still needs both.
    fp = _write_country(
        tmp_path,
        "TST - Test.txt",
        "complete_special_project = sp:sp_aircraft_project\n"
        "set_technology = {\n\tgen_6_medium = 1\n}\n",
    )
    errors = V.validate_country_sp_requirements((fp, tech_sp_reqs, {}, str(tmp_path)))
    assert len(errors) == 1
    assert "gen_6_medium" in errors[0]
    assert "sp_fully_autonomous_fighters" in errors[0]
    # The already-completed SP must not be listed as missing.
    assert "sp_aircraft_project" not in errors[0]


def test_parse_sp_output_claims(tmp_path):
    _write_sp(
        tmp_path,
        "sp_agriculture_drone = {\n"
        "\tproject_output = {\n"
        "\t\tcountry_effects = {\n"
        "\t\t\tcustom_effect_tooltip = {\n"
        "\t\t\t\tlocalization_key = SP_UNLOCK_TECH\n"
        "\t\t\t\tTECH = programmable_harvesters\n"
        "\t\t\t}\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
        "sp_no_tooltip = {\n\tallowed = { always = yes }\n}\n",
    )
    claims = V.parse_sp_output_claims(str(tmp_path))
    assert claims == {"sp_agriculture_drone": ["programmable_harvesters"]}


def test_sp_output_consistency_flags_wrong_tech():
    # The project gates programmable_harvesters but its tooltip advertises a
    # different tech that another project gates.
    sp_gated = {
        "sp_agriculture_drone": {"programmable_harvesters"},
        "sp_other": {"improved_harvesting_automation"},
    }
    claims = {"sp_agriculture_drone": ["improved_harvesting_automation"]}
    errors = V.validate_sp_output_consistency(sp_gated, claims)
    assert len(errors) == 1
    assert "sp_agriculture_drone" in errors[0]
    assert "improved_harvesting_automation" in errors[0]
    assert "sp:sp_other" in errors[0]


def test_sp_output_consistency_flags_gateless_project():
    # A project that gates nothing but advertises a tech is flagged.
    sp_gated = {"sp_real": {"air_tech_gunship_railgun_1"}}
    claims = {"sp_air_gunship_railcannons": ["air_tech_gunship_railgun_1"]}
    errors = V.validate_sp_output_consistency(sp_gated, claims)
    assert len(errors) == 1
    assert "sp_air_gunship_railcannons" in errors[0]
    assert "sp:sp_real" in errors[0]


def test_sp_output_consistency_clean_when_matches():
    sp_gated = {"sp_agriculture_drone": {"programmable_harvesters"}}
    claims = {"sp_agriculture_drone": ["programmable_harvesters"]}
    assert V.validate_sp_output_consistency(sp_gated, claims) == []


def test_validate_country_sp_requirements_unknown_tech_passes(tmp_path, monkeypatch):
    # A tech with no SP requirement in the map should never be flagged, even
    # if the country has it in its `set_technology` block.
    monkeypatch.setenv("MD_NO_CACHE", "1")
    fp = _write_country(
        tmp_path,
        "TST - Test.txt",
        "set_technology = {\n\tinfantry_equipment_1 = 1\n}\n",
    )
    assert V.validate_country_sp_requirements((fp, {}, {}, str(tmp_path))) == []
