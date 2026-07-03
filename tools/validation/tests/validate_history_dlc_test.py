"""Tests for the DLC-gated technology check in validate_history.

A tech with `allow_branch = { NOT = { has_dlc = "X" } }` (a non-DLC fallback
such as SP_arty_0) must not be granted in a history DLC branch where X is
active; a tech with `allow_branch = { has_dlc = "X" }` (a DLC-only tech such as
nsb_artillery_0) must not be granted where X is inactive. Granting it anyway
force-enables equipment whose tech branch is disabled, duplicating the active
designer's equipment. Regression for the KAZ SP_arty_0 fix.
"""

import validate_history as V


def test_extract_dlc_conditions_forbid_and_require():
    assert V._extract_dlc_conditions(
        'allow_branch = {\n\tNOT = { has_dlc = "No Step Back" }\n}'
    ) == [("forbid", "No Step Back")]
    assert V._extract_dlc_conditions(
        'allow_branch = {\n\thas_dlc = "No Step Back"\n}'
    ) == [("require", "No Step Back")]


def test_extract_dlc_conditions_ignores_non_dlc_triggers():
    assert V._extract_dlc_conditions("allow_branch = {\n\tdate > 2010.1.1\n}") == []


def test_context_dlcs_splits_present_and_absent():
    present, absent = V._context_dlcs("No Step Back + NOT By Blood Alone")
    assert present == {"No Step Back"}
    assert absent == {"By Blood Alone"}
    assert V._context_dlcs("unconditional") == (set(), set())


def _parse_tech_reqs(tmp_path, body):
    tech_dir = tmp_path / "common" / "technologies"
    tech_dir.mkdir(parents=True)
    (tech_dir / "test.txt").write_text("technologies = {\n" + body + "\n}\n")
    _, _, _, reqs = V.parse_tech_dependencies(str(tmp_path))
    return reqs


def test_parse_tech_dependencies_collects_dlc_gating(tmp_path):
    reqs = _parse_tech_reqs(
        tmp_path,
        "\tSP_arty_0 = {\n"
        '\t\tallow_branch = { NOT = { has_dlc = "No Step Back" } }\n'
        "\t\tenable_equipments = { SP_arty_0 }\n"
        "\t}\n"
        "\tnsb_artillery_0 = {\n"
        '\t\tallow_branch = { has_dlc = "No Step Back" }\n'
        "\t}\n",
    )
    assert reqs["SP_arty_0"] == [("forbid", "No Step Back")]
    assert reqs["nsb_artillery_0"] == [("require", "No Step Back")]


def test_propagate_dlc_reqs_extends_gate_to_upgrade_chain():
    # SP_arty_0 forbidden under NSB; the upgrade chain leads off it.
    prerequisites = {
        "SP_arty_1": {"SP_arty_0"},
        "SP_arty_2": {"SP_arty_1"},
        "Arty_upgrade_1": {"SP_arty_0"},
    }
    direct = {"SP_arty_0": [("forbid", "No Step Back")]}
    prop = V.propagate_dlc_reqs(prerequisites, direct)
    assert prop["SP_arty_0"] == [("forbid", "No Step Back")]
    assert prop["SP_arty_1"] == [("forbid", "No Step Back")]
    assert prop["SP_arty_2"] == [("forbid", "No Step Back")]  # transitive
    assert prop["Arty_upgrade_1"] == [("forbid", "No Step Back")]


def test_propagate_dlc_reqs_requires_all_prereqs_gated():
    # A tech reachable via an ungated prereq is NOT inherited as gated.
    prerequisites = {
        "shared_tech": {"SP_arty_0", "neutral_root"},
    }
    direct = {"SP_arty_0": [("forbid", "No Step Back")]}
    prop = V.propagate_dlc_reqs(prerequisites, direct)
    assert "shared_tech" not in prop  # neutral_root keeps it reachable under NSB


def test_propagate_dlc_reqs_require_side():
    prerequisites = {"nsb_Anti_Air_1": {"nsb_Anti_Air_0"}}
    direct = {"nsb_Anti_Air_0": [("require", "No Step Back")]}
    prop = V.propagate_dlc_reqs(prerequisites, direct)
    assert prop["nsb_Anti_Air_1"] == [("require", "No Step Back")]


def _write_country(tmp_path, name, body):
    cdir = tmp_path / "history" / "countries"
    cdir.mkdir(parents=True, exist_ok=True)
    fp = cdir / name
    fp.write_text(body)
    return str(fp)


def test_forbid_tech_in_dlc_branch_flagged(tmp_path, monkeypatch):
    monkeypatch.setenv("MD_NO_CACHE", "1")
    reqs = {"SP_arty_0": [("forbid", "No Step Back")]}
    fp = _write_country(
        tmp_path,
        "TST - Test.txt",
        "if = {\n"
        '\tlimit = { has_dlc = "No Step Back" }\n'
        "\tset_technology = {\n"
        "\t\tnsb_artillery_0 = 1\n"
        "\t\tSP_arty_0 = 1\n"
        "\t}\n"
        "\telse = {\n"
        "\t\tset_technology = {\n"
        "\t\t\tSP_arty_0 = 1\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    errors = V.validate_country_dlc_techs((fp, reqs, str(tmp_path)))
    assert len(errors) == 1
    assert "SP_arty_0" in errors[0]
    assert "No Step Back" in errors[0]


def test_require_tech_in_else_branch_flagged(tmp_path, monkeypatch):
    monkeypatch.setenv("MD_NO_CACHE", "1")
    reqs = {"nsb_Anti_Air_0": [("require", "No Step Back")]}
    fp = _write_country(
        tmp_path,
        "TST - Test.txt",
        "if = {\n"
        '\tlimit = { has_dlc = "No Step Back" }\n'
        "\tset_technology = {\n"
        "\t\tnsb_Anti_Air_0 = 1\n"
        "\t}\n"
        "\telse = {\n"
        "\t\tset_technology = {\n"
        "\t\t\tnsb_Anti_Air_0 = 1\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    errors = V.validate_country_dlc_techs((fp, reqs, str(tmp_path)))
    assert len(errors) == 1
    assert "nsb_Anti_Air_0" in errors[0]
    assert "inactive" in errors[0]


def test_correct_branch_placement_is_clean(tmp_path, monkeypatch):
    monkeypatch.setenv("MD_NO_CACHE", "1")
    reqs = {
        "SP_arty_0": [("forbid", "No Step Back")],
        "nsb_artillery_0": [("require", "No Step Back")],
    }
    fp = _write_country(
        tmp_path,
        "TST - Test.txt",
        "if = {\n"
        '\tlimit = { has_dlc = "No Step Back" }\n'
        "\tset_technology = {\n"
        "\t\tnsb_artillery_0 = 1\n"
        "\t}\n"
        "\telse = {\n"
        "\t\tset_technology = {\n"
        "\t\t\tSP_arty_0 = 1\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    assert V.validate_country_dlc_techs((fp, reqs, str(tmp_path))) == []
