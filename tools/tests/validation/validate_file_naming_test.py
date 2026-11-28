"""Tests for the scripted localisation file naming check."""

import pytest
import validate_file_naming as V
from shared.suite import (
    build_validator,
    checks_called_by_run,
    run_validator,
    write_tree,
)

# name: warning category or None
_NAMES = {
    "01_common_scripted_localisation.txt": None,
    "00_scripted_localisation.txt": None,
    "99_T4T_scripted_localisation.txt": None,
    "99_T4T_topic_scripted_localisation.txt": None,
    "01_scripted_localization.txt": "scripted-loc-file-name",
    "1_common_scripted_localisation.txt": "scripted-loc-file-name",
    "99_t4t_scripted_localisation.txt": "scripted-loc-file-name",
    "99_BAD_scripted_localisation.txt": "scripted-loc-file-tag",
    "00_scripted_localisation_FR_loc.txt": None,
    "README.md": None,
}


@pytest.mark.parametrize("name, category", _NAMES.items(), ids=_NAMES)
def test_scripted_loc_file_names(tmp_path, name, category):
    path = f"common/scripted_localisation/{name}"
    write_tree(
        tmp_path,
        {path: "", "common/country_tags/test.txt": '# BAD = "ignored"\nT4T = "test"\n'},
    )
    validator = run_validator(V.Validator, tmp_path)

    assert [(i.category, i.severity, i.file) for i in validator._issues] == (
        [(category, "warning", path)] if category else []
    )


def test_staged_country_tag_removal_checks_unchanged_names(tmp_path, monkeypatch):
    path = "common/scripted_localisation/99_OLD_scripted_localisation.txt"
    registry = "common/country_tags/test.txt"
    write_tree(tmp_path, {path: ""})
    monkeypatch.setenv("MD_STAGED_FILES", registry)
    validator = run_validator(V.Validator, tmp_path, staged_only=True)

    assert [i.file for i in validator._issues] == [path]


def test_run_validations_calls_every_check(tmp_path, monkeypatch):
    validator = build_validator(V.Validator, tmp_path)
    called, checks = checks_called_by_run(validator, monkeypatch)
    assert called == checks
