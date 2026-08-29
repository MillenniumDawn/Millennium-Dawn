"""Tests for runtime load_oob reference validation."""

from suite_helpers import initialize_git_repository, run_git
from validate_oob_units import Validator, find_load_oob_references


def _write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as output_file:
        output_file.write(content)


def _validator(tmp_path, staged_only=False):
    return Validator(
        mod_path=str(tmp_path), use_colors=False, staged_only=staged_only, workers=1
    )


def test_find_load_oob_references_skips_comments_and_dynamic_targets():
    content = """# load_oob = ignored
load_oob = "quoted"
load_oob = bare
load_oob = "[ROOT.GetTag]_reinforcements"
load_oob = $runtime_target$
"""

    assert find_load_oob_references(content) == [("quoted", 2), ("bare", 3)]


def test_runtime_oob_references_require_existing_target_files(tmp_path):
    _write(tmp_path / "history/units/present.txt", "units = { }\n")
    _write(
        tmp_path / "events/test.txt",
        'load_oob = "present"\nload_oob = missing\n',
    )
    validator = _validator(tmp_path)

    validator.validate_load_oob_references()

    assert [
        (issue.category, issue.file, issue.line) for issue in validator._issues
    ] == [("unknown-load-oob", "events/test.txt", 2)]
    assert "history/units/missing.txt" in validator._issues[0].message


def test_runtime_oob_references_scan_all_callers_when_a_target_changes(
    tmp_path, monkeypatch
):
    _write(tmp_path / "events/unchanged.txt", "load_oob = removed\n")
    monkeypatch.setenv("MD_STAGED_FILES", "history/units/removed.txt")
    validator = _validator(tmp_path, staged_only=True)

    validator.validate_load_oob_references()

    assert [
        (issue.category, issue.file, issue.line) for issue in validator._issues
    ] == [("unknown-load-oob", "events/unchanged.txt", 1)]


def test_runtime_oob_references_only_scan_changed_callers_without_target_change(
    tmp_path, monkeypatch
):
    _write(tmp_path / "events/changed.txt", "load_oob = missing\n")
    _write(tmp_path / "events/unchanged.txt", "load_oob = also_missing\n")
    monkeypatch.setenv("MD_STAGED_FILES", "events/changed.txt")
    validator = _validator(tmp_path, staged_only=True)

    validator.validate_load_oob_references()

    assert [
        (issue.category, issue.file, issue.line) for issue in validator._issues
    ] == [("unknown-load-oob", "events/changed.txt", 1)]


def test_full_validator_rescans_unchanged_callers_when_a_target_moves(
    tmp_path, monkeypatch
):
    monkeypatch.delenv("MD_STAGED_FILES", raising=False)
    target = tmp_path / "history/units/target.txt"
    _write(target, "units = { }\n")
    _write(tmp_path / "events/unchanged.txt", "load_oob = target\n")

    initialize_git_repository(tmp_path, "history/units", "events")
    target.rename(tmp_path / "target.txt")
    run_git(tmp_path, "add", "-A")
    monkeypatch.setenv("MD_STAGED_FILES", "target.txt")

    validator = _validator(tmp_path, staged_only=True)
    validator.run_validations()

    assert [
        (issue.category, issue.file, issue.line) for issue in validator._issues
    ] == [("unknown-load-oob", "events/unchanged.txt", 1)]
