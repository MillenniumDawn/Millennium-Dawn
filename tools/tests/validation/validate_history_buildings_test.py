"""Tests for the nuclear-reactor/nuclear_status check and the
project-granted-building check in validate_history.

A state that starts with `nuclear_reactor >= 1` implies its owner's country
file grants one of the nuclear_status idea group's non-default members. A
state that starts with a building a special project's reward grants (e.g.
`microchip_plant` via sp_microchip_production) implies its owner's country
file completes a granting project. Both checks share one pass over
history/states/*.txt via `parse_state_building_owners`.
"""

import validate_history as V


def _write_ideas(tmp_path, body):
    ideas_dir = tmp_path / "common" / "ideas"
    ideas_dir.mkdir(parents=True, exist_ok=True)
    (ideas_dir / "test.txt").write_text(body)


def _write_state(tmp_path, name, body):
    states_dir = tmp_path / "history" / "states"
    states_dir.mkdir(parents=True, exist_ok=True)
    (states_dir / name).write_text(body)


def _write_projects(tmp_path, body):
    projects_dir = tmp_path / "common" / "special_projects" / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    (projects_dir / "test.txt").write_text(body)


def _write_country(tmp_path, name, body):
    cdir = tmp_path / "history" / "countries"
    cdir.mkdir(parents=True, exist_ok=True)
    (cdir / name).write_text(body)


_NUCLEAR_STATUS_IDEAS = (
    "ideas = {\n"
    "\tnuclear_status = {\n"
    "\t\tuse_list_view = yes\n"
    "\t\tnon_nuclear_power = {\n"
    "\t\t\tdefault = yes\n"
    "\t\t\tcost = 300\n"
    "\t\t}\n"
    "\t\tnuclear_energy = {\n"
    "\t\t\tcost = 300\n"
    "\t\t\tavailable = { has_tech = reactor1 }\n"
    "\t\t}\n"
    "\t\tnuclear_power_def = {\n"
    "\t\t\tcost = 300\n"
    "\t\t}\n"
    "\t\tnuclear_power_off = {\n"
    "\t\t\tcost = 300\n"
    "\t\t}\n"
    "\t}\n"
    "}\n"
)


def test_parse_nuclear_status_ideas_excludes_default(tmp_path):
    _write_ideas(tmp_path, _NUCLEAR_STATUS_IDEAS)
    ideas = V.parse_nuclear_status_ideas(str(tmp_path))
    assert ideas == {"nuclear_energy", "nuclear_power_def", "nuclear_power_off"}


def test_parse_nuclear_status_ideas_empty_when_group_absent(tmp_path):
    _write_ideas(tmp_path, "ideas = {\n\tnuclear_stance = {\n\t\tfoo = {}\n\t}\n}\n")
    assert V.parse_nuclear_status_ideas(str(tmp_path)) == set()


def test_parse_state_building_owners_scalar_only(tmp_path):
    # nuclear_reactor at the top level counts; a province-keyed sub-block must
    # not be read into, and commented-out / zero-level entries must not count.
    _write_state(
        tmp_path,
        "1-Test.txt",
        "state = {\n"
        "\thistory = {\n"
        "\t\towner = TST\n"
        "\t\tbuildings = {\n"
        "\t\t\tnuclear_reactor = 1\n"
        "\t\t\t# nuclear_reactor = 5\n"
        "\t\t\tmicrochip_plant = 0\n"
        "\t\t\t1234 = {\n"
        "\t\t\t\tnuclear_reactor = 9\n"
        "\t\t\t}\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    owners = V.parse_state_building_owners(
        str(tmp_path), {"nuclear_reactor", "microchip_plant"}
    )
    assert owners == {"nuclear_reactor": {"TST"}}


def test_parse_state_building_owners_missing_owner_not_attributed(tmp_path):
    _write_state(
        tmp_path,
        "1-Test.txt",
        "state = {\n"
        "\thistory = {\n"
        "\t\tbuildings = {\n"
        "\t\t\tnuclear_reactor = 1\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    assert V.parse_state_building_owners(str(tmp_path), {"nuclear_reactor"}) == {}


def test_parse_project_granted_buildings(tmp_path):
    _write_projects(
        tmp_path,
        "sp_microchip_production = {\n"
        "\tproject_output = {\n"
        "\t\tfacility_state_effects = {\n"
        "\t\t\tset_building_level = {\n"
        "\t\t\t\ttype = microchip_plant\n"
        "\t\t\t\tlevel = 1\n"
        "\t\t\t}\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
        "sp_composite_production = {\n"
        "\tproject_output = {\n"
        "\t\tfacility_state_effects = {\n"
        "\t\t\tset_building_level = {\n"
        "\t\t\t\ttype = composite_plant\n"
        "\t\t\t}\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    granted = V.parse_project_granted_buildings(str(tmp_path))
    assert granted == {
        "microchip_plant": {"sp_microchip_production"},
        "composite_plant": {"sp_composite_production"},
    }


def test_parse_project_granted_buildings_multi_project_same_building(tmp_path):
    _write_projects(
        tmp_path,
        "sp_a = {\n\tproject_output = {\n\t\tfacility_state_effects = {\n"
        "\t\t\tset_building_level = { type = shared_plant }\n\t\t}\n\t}\n}\n"
        "sp_b = {\n\tproject_output = {\n\t\tfacility_state_effects = {\n"
        "\t\t\tset_building_level = { type = shared_plant }\n\t\t}\n\t}\n}\n",
    )
    granted = V.parse_project_granted_buildings(str(tmp_path))
    assert granted == {"shared_plant": {"sp_a", "sp_b"}}


def test_find_reactor_owners_flags_missing_idea():
    errors = V._find_reactor_owners_without_nuclear_status(
        {"TST"}, {"nuclear_energy", "nuclear_power_def"}, {"TST": "capital = 1"}
    )
    assert len(errors) == 1
    assert "TST" in errors[0]


def test_find_reactor_owners_clean_when_idea_present():
    errors = V._find_reactor_owners_without_nuclear_status(
        {"TST"},
        {"nuclear_energy", "nuclear_power_def"},
        {"TST": "add_ideas = { nuclear_energy }"},
    )
    assert errors == []


def test_find_reactor_owners_idea_only_in_comment_still_flagged():
    # Callers pass comment-stripped content (via _load_country_contents);
    # simulate that pipeline so a commented-out grant does not satisfy the check.
    raw = "# add_ideas = { nuclear_energy }\nadd_ideas = { non_nuclear_power }\n"
    stripped = V.strip_comments(raw)
    errors = V._find_reactor_owners_without_nuclear_status(
        {"TST"}, {"nuclear_energy", "nuclear_power_def"}, {"TST": stripped}
    )
    assert len(errors) == 1
    assert "TST" in errors[0]


def test_find_reactor_owners_missing_country_file():
    errors = V._find_reactor_owners_without_nuclear_status(
        {"TST"}, {"nuclear_energy"}, {}
    )
    assert len(errors) == 1
    assert "TST" in errors[0]
    assert "no history/countries/" in errors[0]


def test_find_buildings_without_granting_project_flags_gap():
    errors = V._find_buildings_without_granting_project(
        {"microchip_plant": {"SWE"}},
        {"microchip_plant": {"sp_microchip_production"}},
        {"SWE": "complete_special_project = sp:sp_composite_production"},
    )
    assert len(errors) == 1
    assert "SWE" in errors[0]
    assert "microchip_plant" in errors[0]
    assert "sp:sp_microchip_production" in errors[0]


def test_find_buildings_without_granting_project_clean_when_completed():
    errors = V._find_buildings_without_granting_project(
        {"microchip_plant": {"SWE"}},
        {"microchip_plant": {"sp_microchip_production"}},
        {"SWE": "complete_special_project = sp:sp_microchip_production"},
    )
    assert errors == []


def test_find_buildings_multi_project_satisfied_by_either():
    # A building granted by two different projects is satisfied by completing
    # any one of them.
    errors = V._find_buildings_without_granting_project(
        {"shared_plant": {"TST"}},
        {"shared_plant": {"sp_a", "sp_b"}},
        {"TST": "complete_special_project = sp:sp_b"},
    )
    assert errors == []


def test_find_buildings_without_granting_project_missing_country_file():
    errors = V._find_buildings_without_granting_project(
        {"microchip_plant": {"TST"}},
        {"microchip_plant": {"sp_microchip_production"}},
        {},
    )
    assert len(errors) == 1
    assert "no history/countries/" in errors[0]


def test_tag_country_file_map(tmp_path):
    _write_country(tmp_path, "SWE - Sweden.txt", "capital = 34\n")
    mapping = V._tag_country_file_map(str(tmp_path))
    assert "SWE" in mapping
    assert mapping["SWE"].endswith("SWE - Sweden.txt")


def test_load_country_contents_strips_comments(tmp_path):
    _write_country(
        tmp_path,
        "TST - Test.txt",
        "# complete_special_project = sp:sp_x\ncapital = 1\n",
    )
    tag_files = V._tag_country_file_map(str(tmp_path))
    contents = V._load_country_contents(tag_files, {"TST"})
    assert "sp_x" not in contents["TST"]
    assert "capital" in contents["TST"]


def test_load_country_contents_skips_unknown_tag(tmp_path):
    tag_files = V._tag_country_file_map(str(tmp_path))
    assert V._load_country_contents(tag_files, {"ZZZ"}) == {}
