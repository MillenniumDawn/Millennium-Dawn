"""Tests for validation workflow change grouping."""

import json

import change_groups


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
    assert groups["full_suite"] is False


def test_cli_writes_json_style_list(tmp_path, monkeypatch):
    output = tmp_path / "github-output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setattr(
        "sys.stdin",
        type("Input", (), {"__iter__": lambda self: iter(["events/example.txt\n"])})(),
    )

    assert change_groups.main([]) == 0

    values = dict(
        line.rstrip("\n").split("=", 1) for line in output.read_text().splitlines()
    )
    assert json.loads(values["style_files"]) == ["events/example.txt"]
