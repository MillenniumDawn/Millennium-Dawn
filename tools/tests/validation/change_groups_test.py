"""Tests for validation workflow change grouping."""

import io

import change_groups
import pytest
from validate_file_paths import CONTENT_ROOTS


def test_localisation_only_change():
    groups = change_groups.classify(["localisation/english/example.yml"])

    assert groups["localisation"] is True
    assert groups["content"] is True
    assert groups["full_suite"] is False
    assert groups["tools"] is False
    assert groups["style_files"] == []


def test_tools_change_runs_full_suite():
    groups = change_groups.classify(["tools/validation/change_groups.py"])

    assert groups["full_suite"] is True
    assert groups["tools"] is True
    assert all(
        groups[name] is True for name in change_groups.GROUP_PATTERNS if name != "style"
    )
    assert groups["style"] is False


def test_dispatch_is_distinct_from_empty_diff():
    empty = change_groups.classify([])
    dispatch = change_groups.classify([], dispatch=True)

    assert empty["full_suite"] is False
    assert empty["content"] is False
    assert empty["style"] is False
    assert dispatch["full_suite"] is True
    assert dispatch["content"] is True
    assert dispatch["file-paths"] is True
    assert dispatch["style"] is False
    assert dispatch["style_files"] == []


def test_rename_classifies_both_old_and_new_paths():
    groups = change_groups.classify(
        [
            "localisation/english/old.yml",
            "events/old.txt",
            "events/new.txt",
        ]
    )

    assert groups["localisation"] is True
    assert groups["events"] is True
    assert groups["style_files"] == ["events/new.txt", "events/old.txt"]


def test_style_files_are_diff_scoped():
    groups = change_groups.classify(
        [
            "common/national_focus/example.txt",
            "music/example.txt",
            "common/national_focus/example.yml",
            "docs/example.txt",
        ]
    )

    assert groups["style"] is True
    assert groups["style_files"] == [
        "common/national_focus/example.txt",
        "music/example.txt",
    ]


def test_github_action_edit_runs_full_suite():
    groups = change_groups.classify([".github/actions/setup-md-python/action.yml"])

    assert groups["full_suite"] is True
    assert groups["tools"] is True


def test_map_adjacency_is_a_content_group():
    groups = change_groups.classify(["map/adjacency_rules.txt"])

    assert groups["map-adjacency"] is True
    assert groups["content"] is True
    assert groups["file-paths"] is True
    assert groups["full_suite"] is False


@pytest.mark.parametrize("root", CONTENT_ROOTS)
def test_every_shipped_root_runs_index_validation(root):
    groups = change_groups.classify([f"{root}/path-probe"])

    assert groups["file-paths"] is True
    assert groups["full_suite"] is False


@pytest.mark.parametrize(
    "path", ("gfx/interface/icon.dds", "map/strategicregions/region.txt")
)
def test_graphics_and_map_paths_skip_expensive_content_job(path):
    groups = change_groups.classify([path])

    assert groups["file-paths"] is True
    assert groups["content"] is False


@pytest.mark.parametrize(
    "path",
    ("gfx/interface/decisions/politics/crisis.dds", "interface/MD_decisions.gfx"),
)
def test_decision_art_change_runs_decision_validation(path):
    groups = change_groups.classify([path])

    assert groups["decisions"] is True
    assert groups["content"] is True
    assert groups["full_suite"] is False


def test_file_path_roots_match_validator_content_roots():
    assert set(change_groups._FILE_PATH_ROOTS) == set(CONTENT_ROOTS)


def test_unshipped_path_skips_index_validation():
    groups = change_groups.classify(["docs/validation-notes.md"])

    assert groups["file-paths"] is False
    assert groups["content"] is False


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("events/example.txt", {"style_files": '["events/example.txt"]'}),
        ("gfx/interface/icon.dds", {"file-paths": "true", "content": "false"}),
        (
            "map/strategicregions/region.txt",
            {"file-paths": "true", "content": "false"},
        ),
    ],
)
def test_cli_writes_expected_outputs(tmp_path, monkeypatch, path, expected):
    output = tmp_path / "github-output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setattr("sys.stdin", io.StringIO(f"{path}\n"))

    assert change_groups.main([]) == 0

    values = dict(
        line.rstrip("\n").split("=", 1) for line in output.read_text().splitlines()
    )
    assert {key: values[key] for key in expected} == expected
