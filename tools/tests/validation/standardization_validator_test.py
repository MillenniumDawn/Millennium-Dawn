"""Tests for validate_standardization.py.

The validator states no formatting rules of its own: it runs the owning
standardizer in memory and diffs the result against the file. These tests pin
the three outcomes that behaviour has to produce — clean, unstandardized
(WARNING, with the fixing command in the message), and a standardizer that
cannot run at all (ERROR) — plus the changed-files scoping the design rests on.
"""

import standardize_api
import validate_standardization
from validate_standardization import Validator

_MESSY_EVENT = """country_event = {
\tid = test.1
\tis_triggered_only = yes
\ttitle = test.1.t
\tdesc = test.1.d
\toption = {
\t\tname = test.1.a
\t}
}
"""


def _run(tmp_path, **kwargs):
    validator = Validator(mod_path=str(tmp_path), use_colors=False, workers=1, **kwargs)
    validator.validate_standardization()
    return validator


def _write_event(write_path, tmp_path, body, name="events/Gulf.txt"):
    return write_path(tmp_path, name, body)


def test_standardized_file_is_clean(write_path, tmp_path):
    standardized = standardize_api.standardize_text("event", _MESSY_EVENT)
    _write_event(write_path, tmp_path, standardized)

    validator = _run(tmp_path)

    assert validator._issues == []


def test_unstandardized_file_warns_with_the_fixing_command(write_path, tmp_path):
    _write_event(write_path, tmp_path, _MESSY_EVENT)

    validator = _run(tmp_path)

    assert [issue.category for issue in validator._issues] == ["not-standardized"]
    assert validator.errors_found == 0
    assert validator.warnings_found == 1
    message = validator._issues[0].message
    assert 'standardize.py event "events/Gulf.txt"' in message
    assert validator._issues[0].file == "events/Gulf.txt"


def test_unowned_paths_are_skipped(write_path, tmp_path):
    write_path(tmp_path, "common/units/MD_land_units.txt", _MESSY_EVENT)
    write_path(tmp_path, "history/countries/ARA - Arabistan.txt", _MESSY_EVENT)

    assert _run(tmp_path)._issues == []


def test_file_with_no_matching_block_is_skipped(write_path, tmp_path):
    _write_event(write_path, tmp_path, "# nothing to standardize here\n")

    assert _run(tmp_path)._issues == []


def test_standardizer_failure_is_an_error(write_path, tmp_path, monkeypatch):
    _write_event(write_path, tmp_path, _MESSY_EVENT)

    def explode(kind, text):
        raise ValueError("unbalanced braces")

    monkeypatch.setattr(validate_standardization, "standardize_text", explode)

    validator = _run(tmp_path)

    assert [issue.category for issue in validator._issues] == ["standardizer-error"]
    assert validator.errors_found == 1
    assert "unbalanced braces" in validator._issues[0].message


def test_unreadable_file_is_an_error(write_path, tmp_path):
    # Non-UTF-8 bytes: the file cannot be checked, so it must not pass silently.
    path = write_path(tmp_path, "events/Gulf.txt", "")
    path.write_bytes(b"country_event = {\n\tid = \xff\xfe\n}\n")

    validator = _run(tmp_path)

    assert [issue.category for issue in validator._issues] == ["standardizer-error"]
    assert "could not read the file" in validator._issues[0].message


def test_scan_file_ignores_a_path_no_standardizer_owns(tmp_path):
    unowned = tmp_path / "common" / "units" / "MD_land_units.txt"
    unowned.parent.mkdir(parents=True)
    unowned.write_text(_MESSY_EVENT, encoding="utf-8")

    assert validate_standardization._scan_file((str(unowned), str(tmp_path))) is None


def test_staged_mode_only_checks_staged_files(write_path, tmp_path, monkeypatch):
    _write_event(write_path, tmp_path, _MESSY_EVENT)
    _write_event(write_path, tmp_path, _MESSY_EVENT, name="events/Syria.txt")
    monkeypatch.setenv("MD_STAGED_FILES", "events/Syria.txt")

    validator = _run(tmp_path, staged_only=True)

    assert [issue.file for issue in validator._issues] == ["events/Syria.txt"]


def test_scan_all_overrides_staged_scope(write_path, tmp_path, monkeypatch):
    _write_event(write_path, tmp_path, _MESSY_EVENT)
    _write_event(write_path, tmp_path, _MESSY_EVENT, name="events/Syria.txt")
    monkeypatch.setenv("MD_STAGED_FILES", "events/Syria.txt")

    validator = _run(tmp_path, staged_only=True, scan_all=True)

    assert sorted(issue.file for issue in validator._issues) == [
        "events/Gulf.txt",
        "events/Syria.txt",
    ]
