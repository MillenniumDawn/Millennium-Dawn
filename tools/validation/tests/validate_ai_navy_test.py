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
