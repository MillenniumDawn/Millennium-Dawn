"""Behavior tests for the common-scripting-mistake validator wrapper.

The wrapper owns three things the underlying linter does not: which trees are
scanned, which paths are exempt, and turning `(path, line, message)` triples
into mod-relative findings.
"""

import runpy
import sys

import pytest
import validate_common_mistakes as common_mistakes
from shared_utils import run_validator_main

FACTION_MISTAKE = "some_trigger = {\n\tis_in_faction = GER\n}\n"


def _write(root, relative, content):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(content)
    return path


def _validator(root):
    return common_mistakes.Validator(str(root), use_colors=False, workers=1)


def test_mistake_is_reported_with_relative_path_and_line(tmp_path):
    _write(tmp_path, "common/scripted_triggers/faction.txt", FACTION_MISTAKE)

    validator = _validator(tmp_path)
    validator.run_validations()

    assert [(i.category, i.file, i.line) for i in validator._issues] == [
        ("common-mistakes", "common/scripted_triggers/faction.txt", 2)
    ]
    assert "is_in_faction_with = GER" in validator._issues[0].message
    assert validator.errors_found == 1


def test_events_and_history_trees_are_scanned(tmp_path):
    _write(tmp_path, "events/MD_test.txt", FACTION_MISTAKE)
    _write(tmp_path, "history/countries/GER - Germany.txt", FACTION_MISTAKE)

    validator = _validator(tmp_path)
    validator.run_validations()

    assert sorted(i.file for i in validator._issues) == [
        "events/MD_test.txt",
        "history/countries/GER - Germany.txt",
    ]


def test_clean_script_reports_nothing(tmp_path):
    _write(
        tmp_path,
        "common/scripted_triggers/faction.txt",
        "some_trigger = {\n\tis_in_faction_with = GER\n}\n",
    )

    validator = _validator(tmp_path)
    validator.run_validations()

    assert validator._issues == []
    assert validator.errors_found == 0


@pytest.mark.parametrize(
    "relative",
    ["common/descriptions/blurbs.txt", "common/Changelog.txt", "common/AUTHORS.txt"],
)
def test_exempt_paths_are_never_scanned(tmp_path, relative):
    _write(tmp_path, relative, FACTION_MISTAKE)

    validator = _validator(tmp_path)
    validator.run_validations()

    assert validator._issues == []
    assert validator.errors_found == 0


def _cli_argv(tmp_path, *extra):
    return [
        common_mistakes.__file__,
        "--path",
        str(tmp_path),
        "--workers",
        "1",
        "--no-color",
        *extra,
    ]


def test_script_entry_point_exits_nonzero_under_strict(tmp_path, monkeypatch):
    _write(tmp_path, "common/scripted_triggers/faction.txt", FACTION_MISTAKE)
    monkeypatch.setattr(sys, "argv", _cli_argv(tmp_path, "--strict"))

    with pytest.raises(SystemExit) as exit_info:
        runpy.run_path(common_mistakes.__file__, run_name="__main__")

    assert exit_info.value.code == 1


def test_cli_without_strict_exits_zero_despite_findings(tmp_path, monkeypatch):
    _write(tmp_path, "common/scripted_triggers/faction.txt", FACTION_MISTAKE)
    monkeypatch.setattr(sys, "argv", _cli_argv(tmp_path))

    with pytest.raises(SystemExit) as exit_info:
        run_validator_main(common_mistakes.Validator, "common mistakes")

    assert exit_info.value.code == 0
