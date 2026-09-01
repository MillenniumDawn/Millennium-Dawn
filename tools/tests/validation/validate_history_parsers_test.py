"""Parser and per-file check coverage for validate_history.py.

Covers the pieces the focused building/capital/DLC/SP suites do not reach: the
technology-graph walk, the brace walkers used by the special-project and
nuclear_status parsers, the history token stream's malformed-input handling,
the OOB-reference and tech-prerequisite per-file checks, and the
unreadable-file fallbacks every parser carries.
"""

from collections import defaultdict

import validate_history as V


def _write(tmp_path, relative, body):
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return str(path)


def _write_undecodable(tmp_path, relative):
    """Write a file whose bytes are not valid UTF-8, as a corrupt file would be."""
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\xff\xfe technologies = {\n}\n")
    return str(path)


# --- technology graph -------------------------------------------------------


def test_parse_tech_dependencies_skips_undecodable_file(tmp_path):
    _write_undecodable(tmp_path, "common/technologies/broken.txt")
    _write(
        tmp_path,
        "common/technologies/good.txt",
        "technologies = {\n\tmbt_tech = {\n\t\tcategory = armor\n\t}\n}\n",
    )
    _prereqs, all_techs, _modules, _dlc = V.parse_tech_dependencies(str(tmp_path))
    assert all_techs == {"mbt_tech"}


def test_parse_tech_dependencies_reads_paths_and_module_unlocks(tmp_path):
    _write(
        tmp_path,
        "common/technologies/armor.txt",
        "# leading comment before the wrapper\n"
        "technologies = {\n"
        "\troot_tech = {\n"
        "\t\tpath = {\n"
        "\t\t\tleads_to_tech = child_tech\n"
        "\t\t}\n"
        "\t\tenable_equipment_modules = {\n"
        "\t\t\tengine_2\n"
        "\n"
        "\t\t\tarmor_plate\n"
        "\t\t}\n"
        "\t}\n"
        "\tchild_tech = {\n"
        "\t\tcategory = armor\n"
        "\t}\n"
        "}\n",
    )
    prereqs, all_techs, module_techs, _dlc = V.parse_tech_dependencies(str(tmp_path))
    assert all_techs == {"root_tech", "child_tech"}
    assert prereqs["child_tech"] == {"root_tech"}
    assert module_techs["engine_2"] == {"root_tech"}
    assert module_techs["armor_plate"] == {"root_tech"}


def test_parse_tech_file_without_optional_maps_still_builds_prerequisites():
    prereqs = defaultdict(set)
    all_techs = set()
    V._parse_tech_file(
        "technologies = {\n"
        "\troot_tech = {\n"
        "\t\tpath = {\n"
        "\t\t\tleads_to_tech = child_tech\n"
        "\t\t}\n"
        "\t\tenable_equipment_modules = {\n"
        "\t\t\tengine_2\n"
        "\t\t}\n"
        "\t\tallow_branch = {\n"
        '\t\t\thas_dlc = "No Step Back"\n'
        "\t\t}\n"
        "\t}\n"
        "}\n",
        prereqs,
        all_techs,
    )
    assert all_techs == {"root_tech"}
    assert prereqs == {"child_tech": {"root_tech"}}


def test_file_without_technologies_wrapper_contributes_nothing(tmp_path):
    _write(
        tmp_path,
        "common/technologies/notatech.txt",
        "some_other_root = {\n\tfoo = bar\n}\n",
    )
    _prereqs, all_techs, _modules, _dlc = V.parse_tech_dependencies(str(tmp_path))
    assert all_techs == set()
    assert V.parse_tech_sp_requirements(str(tmp_path)) == {}


# --- special-project parsers ------------------------------------------------


def test_parse_tech_sp_requirements_split_brace_block_keeps_depth(tmp_path):
    # A block whose `{` sits on the next line is not recognized as a tech, but
    # the brace bookkeeping must stay correct so the tech after it still parses.
    _write(
        tmp_path,
        "common/technologies/sp.txt",
        "technologies = {\n"
        "\t@base_year = 1965\n"
        "\todd_block =\n"
        "\t{\n"
        "\t\tis_special_project_completed = sp:sp_hidden\n"
        "\t}\n"
        "\treal_tech = {\n"
        "\t\tallow = {\n"
        "\t\t\tis_special_project_completed = sp:sp_real\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    assert V.parse_tech_sp_requirements(str(tmp_path)) == {"real_tech": {"sp_real"}}


def test_parse_tech_sp_requirements_never_treats_the_wrapper_as_a_tech(tmp_path):
    # A duplicated `technologies = {` wrapper must not register a tech named
    # `technologies`, and the tech inside it must still be parsed.
    _write(
        tmp_path,
        "common/technologies/sp.txt",
        "technologies = {\n"
        "technologies = {\n"
        "\tfoo = { allow = { is_special_project_completed = sp:sp_x } }\n"
        "}\n"
        "}\n",
    )
    assert V.parse_tech_sp_requirements(str(tmp_path)) == {"foo": {"sp_x"}}


def test_parse_tech_sp_requirements_reads_final_line_without_newline(tmp_path):
    _write(
        tmp_path,
        "common/technologies/sp.txt",
        "technologies = {\n"
        "\tfoo = { allow = { is_special_project_completed = sp:sp_x } } }",
    )
    assert V.parse_tech_sp_requirements(str(tmp_path)) == {"foo": {"sp_x"}}


def test_project_without_allowed_block_is_not_dlc_or_always_gated(tmp_path):
    _write(
        tmp_path,
        "common/special_projects/projects/test.txt",
        "sp_no_allowed = {\n\tproject_output = {\n\t}\n}\n"
        "sp_open = {\n\tallowed = { always = yes }\n}\n",
    )
    assert V.parse_sp_allowed_dlc(str(tmp_path)) == {}
    assert V.parse_sp_always_yes(str(tmp_path)) == {"sp_open"}


def test_parse_sp_output_claims_ignores_other_tooltips(tmp_path):
    _write(
        tmp_path,
        "common/special_projects/projects/test.txt",
        "sp_x = {\n"
        "\tproject_output = {\n"
        "\t\tcustom_effect_tooltip = {\n"
        "\t\t\tlocalization_key = SP_SOMETHING_ELSE\n"
        "\t\t\tTECH = decoy_tech\n"
        "\t\t}\n"
        "\t\tcustom_effect_tooltip = {\n"
        "\t\t\tlocalization_key = SP_UNLOCK_TECH\n"
        "\t\t\tTECH = mbt_tech\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    assert V.parse_sp_output_claims(str(tmp_path)) == {"sp_x": ["mbt_tech"]}


def test_parse_project_granted_buildings_ignores_typeless_grant(tmp_path):
    _write(
        tmp_path,
        "common/special_projects/projects/test.txt",
        "sp_a = {\n"
        "\tproject_output = {\n"
        "\t\tfacility_state_effects = {\n"
        "\t\t\tset_building_level = { level = 1 }\n"
        "\t\t\tset_building_level = { type = microchip_plant level = 1 }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    assert V.parse_project_granted_buildings(str(tmp_path)) == {
        "microchip_plant": {"sp_a"}
    }


def test_sp_output_consistency_reports_what_the_project_does_gate():
    errors = V.validate_sp_output_consistency(
        {"sp_a": {"tech_x"}}, {"sp_a": ["tech_y"]}
    )
    assert errors == [
        "sp:sp_a: project_output claims to unlock tech_y, but tech_y is gated by "
        "no project; this project gates tech_x"
    ]


def test_sp_output_consistency_reports_project_that_gates_nothing():
    errors = V.validate_sp_output_consistency({}, {"sp_a": ["tech_y"]})
    assert errors == [
        "sp:sp_a: project_output claims to unlock tech_y, but tech_y is gated by "
        "no project, and this project gates nothing"
    ]


# --- nuclear_status idea group ----------------------------------------------


def test_parse_nuclear_status_ideas_skips_undecodable_file(tmp_path):
    _write_undecodable(tmp_path, "common/ideas/broken.txt")
    assert V.parse_nuclear_status_ideas(str(tmp_path)) == set()


def test_parse_nuclear_status_ideas_split_brace_member_keeps_depth(tmp_path):
    _write(
        tmp_path,
        "common/ideas/test.txt",
        "ideas = {\n"
        "\tnuclear_status = {\n"
        "\t\tuse_list_view = yes\n"
        "\t\todd_member =\n"
        "\t\t{\n"
        "\t\t\tcost = 300\n"
        "\t\t}\n"
        "\t\tnuclear_energy = {\n"
        "\t\t\tcost = 300\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    assert V.parse_nuclear_status_ideas(str(tmp_path)) == {"nuclear_energy"}


def test_parse_nuclear_status_ideas_reads_member_on_the_closing_line(tmp_path):
    _write(
        tmp_path,
        "common/ideas/test.txt",
        "ideas = {\n\tnuclear_status = {\n\t\tnuclear_energy = { cost = 300 } }\n}\n",
    )
    assert V.parse_nuclear_status_ideas(str(tmp_path)) == {"nuclear_energy"}


# --- state and country file readers -----------------------------------------


def test_parse_state_building_owners_skips_undecodable_file(tmp_path):
    _write_undecodable(tmp_path, "history/states/broken.txt")
    _write(
        tmp_path,
        "history/states/1-Test.txt",
        "state = {\n"
        "\thistory = {\n"
        "\t\towner = TST\n"
        "\t\tbuildings = {\n"
        "\t\t\tnuclear_reactor = 1\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    owners = V.parse_state_building_owners(str(tmp_path), {"nuclear_reactor"})
    assert owners == {"nuclear_reactor": {"TST"}}


def test_load_country_contents_skips_undecodable_file(tmp_path):
    _write_undecodable(tmp_path, "history/countries/BAD - Bad.txt")
    _write(tmp_path, "history/countries/TST - Test.txt", "capital = 1\n")
    tag_files = V._tag_country_file_map(str(tmp_path))
    contents = V._load_country_contents(tag_files, {"BAD", "TST"})
    assert set(contents) == {"TST"}


def test_get_state_owners_collects_tags_and_skips_undecodable_file(tmp_path):
    _write_undecodable(tmp_path, "history/states/broken.txt")
    _write(
        tmp_path,
        "history/states/1-Test.txt",
        "state = {\n\thistory = {\n\t\towner = TST\n\t}\n}\n",
    )
    _write(
        tmp_path,
        "history/states/2-Other.txt",
        "state = {\n\thistory = {\n\t\towner = OTH\n\t}\n}\n",
    )
    assert V._get_state_owners(str(tmp_path)) == {"TST", "OTH"}


def test_validate_capital_defined_reports_unreadable_file(tmp_path):
    path = _write_undecodable(tmp_path, "history/countries/BAD - Bad.txt")
    assert V.validate_capital_defined(path) == ["BAD - Bad.txt: could not read file"]


# --- history token stream ---------------------------------------------------


def test_has_dlc_outside_an_if_gates_nothing():
    branches = V._parse_history_text(
        'has_dlc = "No Step Back"\nset_technology = { mbt_tech = 1 }\n'
    )
    assert branches == [({"mbt_tech"}, set(), "unconditional")]


def test_complete_special_project_without_sp_prefix_is_ignored():
    branches = V._parse_history_text(
        "complete_special_project = sp_armoured_vehicle_project\n"
        "set_technology = { mbt_tech = 1 }\n"
    )
    assert branches == [({"mbt_tech"}, set(), "unconditional")]


def test_unbalanced_braces_do_not_derail_the_token_walk():
    branches = V._parse_history_text(
        "add_ideas = { idea_a idea_b }\n"
        "}\n"
        "{\n"
        "set_technology = { mbt_tech = 1 }\n"
        "capital =\n"
    )
    assert branches == [({"mbt_tech"}, set(), "unconditional")]


def test_parse_history_file_missing_file_returns_empty(tmp_path):
    assert V.parse_history_file(str(tmp_path / "gone.txt"), str(tmp_path)) == []


def test_context_dlcs_ignores_empty_terms():
    present, absent = V._context_dlcs("No Step Back +  + NOT By Blood Alone")
    assert present == {"No Step Back"}
    assert absent == {"By Blood Alone"}


# --- special-project per-country checks -------------------------------------


def test_multi_sp_gap_uses_the_plural_message(tmp_path, monkeypatch):
    monkeypatch.setenv("MD_NO_CACHE", "1")
    path = _write(
        tmp_path,
        "history/countries/TST - Test.txt",
        "set_technology = {\n\tgen_6_medium = 1\n}\n",
    )
    errors = V.validate_country_sp_requirements(
        (path, {"gen_6_medium": {"sp_a", "sp_b"}}, {}, str(tmp_path))
    )
    assert errors == [
        "TST - Test.txt: gen_6_medium requires special projects sp:sp_a, sp:sp_b "
        "but they are not completed at game start [any DLC configuration]"
    ]


def test_sp_misplacement_missing_file_returns_empty(tmp_path):
    assert (
        V.validate_country_sp_misplacement(
            (str(tmp_path / "gone.txt"), {"sp_awacs_project"}, str(tmp_path))
        )
        == []
    )


def test_sp_misplacement_ignores_completion_in_the_non_dlc_else(tmp_path):
    path = _write(
        tmp_path,
        "history/countries/TST - Test.txt",
        "if = {\n"
        '\tlimit = { has_dlc = "No Step Back" }\n'
        "\tset_technology = { mbt_tech = 1 }\n"
        "\telse = {\n"
        "\t\tcomplete_special_project = sp:sp_awacs_project\n"
        "\t}\n"
        "}\n",
    )
    assert (
        V.validate_country_sp_misplacement((path, {"sp_awacs_project"}, str(tmp_path)))
        == []
    )


# --- OOB references ---------------------------------------------------------


def test_get_oob_refs_records_type_and_line_and_skips_comments(tmp_path):
    path = _write(
        tmp_path,
        "history/countries/TST - Test.txt",
        "capital = 1\n"
        'oob = "TST_1990"\n'
        '# oob = "TST_commented"\n'
        'set_air_oob = "TST_1990_air"\n'
        'set_naval_oob = "TST_1990_naval"\n',
    )
    assert V._get_oob_refs(path) == [
        ("TST_1990", 2, "oob"),
        ("TST_1990_air", 4, "set_air_oob"),
        ("TST_1990_naval", 5, "set_naval_oob"),
    ]


def test_get_oob_refs_missing_file_returns_empty(tmp_path):
    assert V._get_oob_refs(str(tmp_path / "gone.txt")) == []


def test_validate_oob_references_skips_non_state_owner(tmp_path):
    path = _write(tmp_path, "history/countries/TST - Test.txt", "capital = 1\n")
    assert V.validate_oob_references((path, set(), {"OTH"})) == []


def test_validate_oob_references_flags_state_owner_without_land_oob(tmp_path):
    path = _write(
        tmp_path,
        "history/countries/TST - Test.txt",
        'capital = 1\nset_air_oob = "TST_1990_air"\n',
    )
    errors = V.validate_oob_references((path, {"TST_1990_air"}, {"TST"}))
    assert len(errors) == 1
    assert errors[0].startswith("TST - Test.txt: TST owns states at game start")
    assert "no land OOB" in errors[0]


def test_validate_oob_references_flags_missing_oob_file(tmp_path):
    path = _write(
        tmp_path,
        "history/countries/TST - Test.txt",
        'capital = 1\noob = "TST_1990"\nset_oob = "TST_gone"\n',
    )
    errors = V.validate_oob_references((path, {"TST_1990"}, {"TST"}))
    assert errors == [
        'TST - Test.txt:3 - set_oob references "TST_gone" but no '
        "history/units/TST_gone.txt file exists"
    ]


def test_validate_oob_references_clean_when_land_oob_exists(tmp_path):
    path = _write(
        tmp_path,
        "history/countries/TST - Test.txt",
        'capital = 1\noob = "TST_1990"\n',
    )
    assert V.validate_oob_references((path, {"TST_1990"}, {"TST"})) == []


# --- technology prerequisites ------------------------------------------------


def _country(tmp_path, body):
    return _write(tmp_path, "history/countries/TST - Test.txt", body)


def test_validate_country_file_flags_missing_single_prerequisite(tmp_path, monkeypatch):
    monkeypatch.setenv("MD_NO_CACHE", "1")
    path = _country(tmp_path, "set_technology = {\n\tchild_tech = 1\n}\n")
    errors = V.validate_country_file(
        (
            path,
            {"child_tech": {"root_tech"}},
            {"child_tech", "root_tech"},
            str(tmp_path),
        )
    )
    assert errors == ["TST - Test.txt: child_tech requires root_tech"]


def test_validate_country_file_lists_alternative_prerequisites(tmp_path, monkeypatch):
    monkeypatch.setenv("MD_NO_CACHE", "1")
    path = _country(tmp_path, "set_technology = {\n\tchild_tech = 1\n}\n")
    errors = V.validate_country_file(
        (
            path,
            {"child_tech": {"root_a", "root_b"}},
            {"child_tech", "root_a", "root_b"},
            str(tmp_path),
        )
    )
    assert errors == ["TST - Test.txt: child_tech requires one of: root_a, root_b"]


def test_validate_country_file_clean_when_prerequisite_is_granted(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("MD_NO_CACHE", "1")
    path = _country(
        tmp_path, "set_technology = {\n\troot_tech = 1\n\tchild_tech = 1\n}\n"
    )
    assert (
        V.validate_country_file(
            (
                path,
                {"child_tech": {"root_tech"}},
                {"child_tech", "root_tech"},
                str(tmp_path),
            )
        )
        == []
    )


def test_validate_country_file_ignores_techs_it_does_not_know(tmp_path, monkeypatch):
    monkeypatch.setenv("MD_NO_CACHE", "1")
    path = _country(tmp_path, "set_technology = {\n\tdlc_only_tech = 1\n}\n")
    assert (
        V.validate_country_file(
            (path, {"dlc_only_tech": {"root_tech"}}, {"root_tech"}, str(tmp_path))
        )
        == []
    )


def test_validate_country_file_tags_branch_specific_gap_with_its_context(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("MD_NO_CACHE", "1")
    path = _country(
        tmp_path,
        "set_technology = {\n"
        "\troot_tech = 1\n"
        "}\n"
        "if = {\n"
        '\tlimit = { has_dlc = "No Step Back" }\n'
        "\tset_technology = { nsb_child = 1 }\n"
        "}\n",
    )
    errors = V.validate_country_file(
        (
            path,
            {"nsb_child": {"nsb_root"}},
            {"nsb_child", "nsb_root", "root_tech"},
            str(tmp_path),
        )
    )
    assert errors == [
        "TST - Test.txt: nsb_child requires nsb_root [No Step Back]",
    ]
