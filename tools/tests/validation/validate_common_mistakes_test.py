"""Behavior tests for the common-scripting-mistake validator wrapper.

The wrapper owns three things the underlying linter does not: which trees are
scanned, which paths are exempt, and turning `(path, line, message)` triples
into mod-relative findings.
"""

import importlib
import runpy
import sys

import pytest
import validate_common_mistakes as common_mistakes
from shared.suite import write_under as _write
from shared_utils import run_validator_main

FACTION_MISTAKE = "some_trigger = {\n\tis_in_faction = GER\n}\n"


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


def _findings(validator):
    return [(i.file, i.line, i.message) for i in validator._issues]


def test_pooled_run_matches_the_in_process_run(tmp_path, monkeypatch):
    # Ten files clear the pool threshold; the nation finding only appears when
    # _init_worker hands each worker the flag set scanned from the whole tree.
    for index in range(10):
        _write(tmp_path, f"events/TST_{index:02}.txt", FACTION_MISTAKE)
    _write(
        tmp_path,
        "common/scripted_effects/nation.txt",
        "TST_effect = {\n\tif = { limit = { is_arab_nation = yes } }\n}\n",
    )
    _write(
        tmp_path,
        "common/scripted_effects/flags.txt",
        "TST_flags = {\n\tset_country_flag = arab_nation_flag\n}\n",
    )
    checker = importlib.import_module(common_mistakes.check_file.__module__)
    # Forked workers inherit these, so only _init_worker can fill them in.
    for name in (
        "_SCRIPT_COMPLETED_FOCUSES",
        "_SCRIPT_COMPLETED_DECISIONS",
        "_REAL_NATION_FLAGS",
    ):
        monkeypatch.setattr(checker, name, set())
    monkeypatch.setenv("MD_MAX_WORKERS", "2")

    pooled = common_mistakes.Validator(str(tmp_path), use_colors=False, workers=2)
    assert pooled.workers == 2
    pooled.run_validations()
    in_process = _validator(tmp_path)
    in_process.run_validations()

    assert _findings(pooled) == _findings(in_process)
    assert sorted((file, line) for file, line, _message in _findings(pooled)) == [
        ("common/scripted_effects/nation.txt", 2),
        *((f"events/TST_{index:02}.txt", 2) for index in range(10)),
    ]


def test_events_history_and_music_trees_are_scanned(tmp_path):
    _write(tmp_path, "events/MD_test.txt", FACTION_MISTAKE)
    _write(tmp_path, "history/countries/GER - Germany.txt", FACTION_MISTAKE)
    _write(tmp_path, "music/MD_test_songs.txt", FACTION_MISTAKE)

    validator = _validator(tmp_path)
    validator.run_validations()

    assert sorted(i.file for i in validator._issues) == [
        "events/MD_test.txt",
        "history/countries/GER - Germany.txt",
        "music/MD_test_songs.txt",
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


def test_staged_plain_file_skips_the_global_ref_scan(tmp_path, monkeypatch):
    path = _write(
        tmp_path,
        "common/scripted_effects/plain.txt",
        "test_effect = { add_political_power = 10 }\n",
    )

    def _boom(_root):
        raise AssertionError("global ref scan should be skipped")

    monkeypatch.setattr(common_mistakes, "_scan_global_refs", _boom)
    validator = common_mistakes.Validator(
        str(tmp_path), use_colors=False, workers=1, staged_only=True
    )
    validator.staged_files = [str(path)]
    validator.run_validations()
    assert validator._issues == []


def test_staged_nation_trigger_still_scans_global_refs(tmp_path, monkeypatch):
    path = _write(
        tmp_path,
        "common/scripted_triggers/nation.txt",
        "test_trigger = { is_arab_nation = yes }\n",
    )
    scanned = []

    def _scan(root):
        scanned.append(root)
        return set(), set(), set()

    monkeypatch.setattr(common_mistakes, "_scan_global_refs", _scan)
    validator = common_mistakes.Validator(
        str(tmp_path), use_colors=False, workers=1, staged_only=True
    )
    validator.staged_files = [str(path)]
    validator.run_validations()
    assert scanned == [validator.mod_path]
