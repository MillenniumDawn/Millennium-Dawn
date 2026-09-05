"""Behavior tests for AI navy parser and cross-reference checks."""

from validate_ai_navy import (
    Validator,
    parse_fleet_files,
    parse_naval_units,
    parse_taskforce_files,
)


def _write_navy_fixture(tmp_path):
    units_dir = tmp_path / "common" / "units"
    taskforce_dir = tmp_path / "common" / "ai_navy" / "taskforce"
    fleet_dir = tmp_path / "common" / "ai_navy" / "fleet"
    units_dir.mkdir(parents=True)
    taskforce_dir.mkdir(parents=True)
    fleet_dir.mkdir(parents=True)

    (units_dir / "MD_naval_units.txt").write_text(
        "sub_units = {\n"
        "\tcarrier = { type = carrier }\n"
        "\tfrigate = { type = frigate }\n"
        "}\n",
        encoding="utf-8",
    )
    (taskforce_dir / "taskforces.txt").write_text(
        "tf_alpha = {\n"
        "\ttask = {\n"
        "\t\toptimal_composition = {\n"
        "\t\t\tcarrier = {\n"
        "\t\t\t\tamount = 3\n"
        "\t\t\t}\n"
        "\t\t\tfrigat = {\n"
        "\t\t\t\tamount = 1\n"
        "\t\t\t}\n"
        "\t\t}\n"
        "\t\tmission = { bad_mission }\n"
        "\t}\n"
        "}\n",
        encoding="utf-8",
    )
    (fleet_dir / "fleets.txt").write_text(
        "fleet_alpha = {\n"
        "\trequired_taskforces = {\n"
        "\t\ttf_alpha = 1\n"
        "\t\tmissing_taskforce = 1\n"
        "\t}\n"
        "}\n",
        encoding="utf-8",
    )


def test_parse_naval_units_and_taskforce_composition(tmp_path):
    _write_navy_fixture(tmp_path)

    assert parse_naval_units(str(tmp_path)) == {"carrier", "frigate"}
    defined, ship_refs, mission_refs, compositions = parse_taskforce_files(
        str(tmp_path)
    )

    assert defined == {"tf_alpha"}
    assert {ship for ship, _, _ in ship_refs} == {"carrier", "frigat"}
    assert mission_refs == [("bad_mission", "taskforces.txt", 11)]
    assert compositions == [
        ("tf_alpha", "taskforces.txt", 1, {"carrier": 3, "frigat": 1})
    ]


def test_parse_fleet_taskforce_references_preserves_line_numbers(tmp_path):
    _write_navy_fixture(tmp_path)

    assert parse_fleet_files(str(tmp_path)) == [
        ("tf_alpha", "fleets.txt", 3),
        ("missing_taskforce", "fleets.txt", 4),
    ]


def test_validator_reports_unknown_ship_mission_taskforce_and_limit(tmp_path):
    _write_navy_fixture(tmp_path)
    validator = Validator(str(tmp_path), use_colors=False, workers=1)

    validator.run_validations()
    messages = [issue.message for issue in validator._issues]

    assert any("unknown ship type 'frigat'" in message for message in messages)
    assert any("unknown mission type 'bad_mission'" in message for message in messages)
    assert any(
        "unknown taskforce 'missing_taskforce'" in message for message in messages
    )
    assert any("carrier=3>2" in message for message in messages)


_UNITS = """sub_units = {
\tcarrier = { type = carrier }
\tdestroyer = { type = destroyer }
\tfrigate = { type = frigate }
\tattack_submarine = { type = attack_submarine }
}
"""

_TASKFORCES = """# fleet doctrine notes

tf_overloaded = {
\ttask = {
\t\tmin_composition = {
\t\t\tdestroyer = {
\t\t\t\tamount = 1
\t\t\t}
\t\t}
\t\toptimal_composition = { # the AI never fields this many
\t\t\tdestroyer = {
\t\t\t\tamount = 7
\t\t\t}
\t\t\tfrigate = {
\t\t\t\tamount = 9
\t\t\t}
\t\t\tattack_submarine = {
\t\t\t\tamount = 9
\t\t\t}
\t\t\tzzzz = {
\t\t\t\tamount = 1
\t\t\t}
\t\t}
\t\tmission = { naval_patrol naval_patrl }
\t}
}

tf_small = {
\ttask = {
\t\toptimal_composition = {
\t\t\tcarrier = {
\t\t\t\tamount = 1
\t\t\t}
\t\t}
\t}
}

tf_minimum_only = {
\ttask = {
\t\tmin_composition = {
\t\t\tdestroyer = {
\t\t\t\tamount = 1
\t\t\t}
\t\t}
\t}
}
"""

_FLEETS = """# home fleet

fleet_home = {
\trequired_taskforces = {
\t\ttf_smal = 1
\t}
}
"""


def _write_limits_fixture(tmp_path, write_path):
    write_path(tmp_path, "common/units/MD_naval_units.txt", _UNITS)
    write_path(
        tmp_path,
        "common/units/MD_land_units.txt",
        "sub_units = {\n\tinfantry = { }\n}\n",
    )
    write_path(tmp_path, "common/ai_navy/taskforce/limits.txt", _TASKFORCES)
    write_path(tmp_path, "common/ai_navy/fleet/fleets.txt", _FLEETS)


def _messages(tmp_path):
    validator = Validator(str(tmp_path), use_colors=False, workers=1)
    validator.run_validations()
    return [issue.message for issue in validator._issues]


def test_land_unit_files_supply_no_ship_types(tmp_path, write_path):
    _write_limits_fixture(tmp_path, write_path)

    assert parse_naval_units(str(tmp_path)) == {
        "carrier",
        "destroyer",
        "frigate",
        "attack_submarine",
    }


def test_every_composition_category_limit_is_reported(tmp_path, write_path):
    _write_limits_fixture(tmp_path, write_path)

    messages = _messages(tmp_path)
    overload = [m for m in messages if "tf_overloaded exceeds" in m]

    assert len(overload) == 1
    assert "capital=7>6" in overload[0]
    assert "screen=9>8" in overload[0]
    assert "sub=9>8" in overload[0]
    assert "carrier=" not in overload[0]
    assert not any("tf_small exceeds" in m for m in messages)


def test_min_composition_is_not_charged_against_the_limits(tmp_path, write_path):
    _write_limits_fixture(tmp_path, write_path)

    _defined, _ships, _missions, compositions = parse_taskforce_files(str(tmp_path))

    assert [name for name, _f, _l, _c in compositions] == ["tf_overloaded", "tf_small"]
    assert compositions[0][3] == {
        "destroyer": 7,
        "frigate": 9,
        "attack_submarine": 9,
        "zzzz": 1,
    }


def test_suggestions_are_offered_only_when_a_close_name_exists(tmp_path, write_path):
    _write_limits_fixture(tmp_path, write_path)

    messages = _messages(tmp_path)

    assert any(
        m.endswith("unknown ship type 'zzzz'") for m in messages if "ship type" in m
    )
    assert any(
        "unknown mission type 'naval_patrl' (did you mean 'naval_patrol'?)" in m
        for m in messages
    )
    assert any(
        "unknown taskforce 'tf_smal' (did you mean 'tf_small'?)" in m for m in messages
    )
    # naval_patrol shares the line and is valid — only the typo is reported.
    assert len([m for m in messages if "unknown mission type" in m]) == 1


def test_stray_closing_brace_does_not_break_taskforce_parsing(tmp_path, write_path):
    write_path(
        tmp_path,
        "common/ai_navy/taskforce/stray.txt",
        "tf_stray = {\n\ttask = { }\n}\n}\n",
    )

    defined, _ships, _missions, _compositions = parse_taskforce_files(str(tmp_path))

    assert defined == {"tf_stray"}


def test_unreadable_inputs_are_skipped(tmp_path, write_path):
    _write_limits_fixture(tmp_path, write_path)
    (tmp_path / "common" / "units" / "naval_broken.txt").mkdir()
    (tmp_path / "common" / "ai_navy" / "taskforce" / "broken.txt").mkdir()
    (tmp_path / "common" / "ai_navy" / "fleet" / "broken.txt").mkdir()

    assert "carrier" in parse_naval_units(str(tmp_path))
    assert parse_taskforce_files(str(tmp_path))[0] == {
        "tf_overloaded",
        "tf_small",
        "tf_minimum_only",
    }
    assert parse_fleet_files(str(tmp_path)) == [("tf_smal", "fleets.txt", 5)]


def test_missing_navy_directories_yield_nothing(tmp_path):
    assert parse_taskforce_files(str(tmp_path)) == (set(), [], [], [])
    assert parse_fleet_files(str(tmp_path)) == []


def test_staged_run_without_navy_files_skips(tmp_path, write_path, monkeypatch):
    _write_limits_fixture(tmp_path, write_path)
    write_path(tmp_path, "common/ideas/unrelated.txt", "ideas = { }\n")
    monkeypatch.setenv("MD_STAGED_FILES", "common/ideas/unrelated.txt")

    validator = Validator(str(tmp_path), use_colors=False, staged_only=True, workers=1)
    validator.run_validations()

    assert validator._issues == []


def test_staged_navy_file_still_runs_every_check(tmp_path, write_path, monkeypatch):
    _write_limits_fixture(tmp_path, write_path)
    monkeypatch.setenv("MD_STAGED_FILES", "common/ai_navy/taskforce/limits.txt")

    validator = Validator(str(tmp_path), use_colors=False, staged_only=True, workers=1)
    validator.run_validations()

    assert any("tf_overloaded exceeds" in i.message for i in validator._issues)
