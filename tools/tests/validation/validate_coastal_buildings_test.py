"""Tests for coastal provincial building placement checks."""

import pytest
import validate_coastal_buildings as V
from shared.suite import assert_findings, run_validator, write_tree

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


def _state(buildings):
    return f"state = {{\n\tid = 1\n\thistory = {{\n{buildings}\n\t}}\n}}\n"


def _construction(body):
    return f"effect = {{\n\tadd_building_construction = {{\n{body}\n\t}}\n}}\n"


# building definitions: {case: (file text, coastal provincial buildings)}
_DEFINITION_CASES = {
    "coastal and provincial": (_BUILDINGS, {"naval_base"}),
    "commented flag": (
        "buildings = {\n\tnaval_base = {\n\t\t# only_costal = yes\n"
        "\t\tlevel_cap = { province_max = 10 }\n\t}\n}\n",
        set(),
    ),
    "province_max outside level_cap": (
        "buildings = {\n\tnaval_base = {\n\t\tonly_costal = yes\n"
        "\t\tprovince_max = 10\n\t}\n}\n",
        set(),
    ),
}


@pytest.mark.parametrize(
    "text, expected", _DEFINITION_CASES.values(), ids=_DEFINITION_CASES
)
def test_coastal_provincial_buildings(text, expected):
    assert V.coastal_provincial_buildings(text) == expected


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


def test_finding_is_a_warning_with_file_and_line(tmp_path):
    write_tree(
        tmp_path,
        {
            "common/buildings/00_buildings.txt": _BUILDINGS,
            "map/definition.csv": _DEFINITION,
            "events/test.txt": _construction("\t\ttype = naval_base\n\t\tprovince = 2"),
        },
    )

    (issue,) = run_validator(V.Validator, tmp_path)._issues

    assert (issue.severity, issue.category, issue.file, issue.line) == (
        "warning",
        "coastal-building-not-coastal",
        "events/test.txt",
        4,
    )


def test_missing_definition_is_reported(tmp_path):
    write_tree(tmp_path, {"common/buildings/00_buildings.txt": _BUILDINGS})

    validator = run_validator(V.Validator, tmp_path)

    assert [issue.category for issue in validator._issues] == [
        "coastal-building-definition-missing"
    ]


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
