"""Tests for validate_standardization.py.

The validator states no formatting rules of its own: it runs the owning
standardizer in memory and diffs the result against the file. These tests pin
the three outcomes that behaviour has to produce — clean, unstandardized
(WARNING, with the fixing command in the message), and a standardizer that
cannot run at all (ERROR) — plus the changed-files scoping the design rests on.
"""

import pytest
import standardize_api
import validate_standardization
from shared.suite import checks_called_by_run, run_tool_script, write_under
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


def _write_event(tmp_path, body, name="events/Gulf.txt"):
    return write_under(tmp_path, name, body)


def test_standardized_file_is_clean(tmp_path):
    standardized = standardize_api.standardize_text("event", _MESSY_EVENT)
    _write_event(tmp_path, standardized)

    validator = _run(tmp_path)

    assert validator._issues == []


def test_unstandardized_file_warns_with_the_fixing_command(tmp_path):
    _write_event(tmp_path, _MESSY_EVENT)

    validator = _run(tmp_path)

    assert [issue.category for issue in validator._issues] == ["not-standardized"]
    assert validator.errors_found == 0
    assert validator.warnings_found == 1
    message = validator._issues[0].message
    assert 'standardize.py event "events/Gulf.txt"' in message
    assert validator._issues[0].file == "events/Gulf.txt"


def test_unowned_paths_are_skipped(tmp_path):
    write_under(tmp_path, "common/units/MD_land_units.txt", _MESSY_EVENT)
    # A history-owned path with no dated blocks is also skipped.
    write_under(tmp_path, "history/countries/ARA - Arabistan.txt", _MESSY_EVENT)

    assert _run(tmp_path)._issues == []


_MESSY_HISTORY = """capital = 652

2000.1.1 = {
\tset_country_flag = TST_alpha
\tcomplete_special_project = sp:sp_space_program
}
"""


def test_unstandardized_history_warns_with_the_fixing_command(tmp_path):
    write_under(tmp_path, "history/countries/ARA - Arabistan.txt", _MESSY_HISTORY)

    validator = _run(tmp_path)

    assert [issue.category for issue in validator._issues] == ["not-standardized"]
    message = validator._issues[0].message
    assert 'standardize.py history "history/countries/ARA - Arabistan.txt"' in message


def test_standardized_history_is_clean(tmp_path):
    standardized = standardize_api.standardize_text(
        "history", _MESSY_HISTORY, mod_root=str(tmp_path)
    )
    assert standardized is not None
    write_under(tmp_path, "history/countries/ARA - Arabistan.txt", standardized)

    assert _run(tmp_path)._issues == []


def test_file_with_no_matching_block_is_skipped(tmp_path):
    _write_event(tmp_path, "# nothing to standardize here\n")

    assert _run(tmp_path)._issues == []


def test_standardizer_failure_is_an_error(tmp_path, monkeypatch):
    _write_event(tmp_path, _MESSY_EVENT)

    def explode(kind, text, mod_root=None):
        raise ValueError("unbalanced braces")

    monkeypatch.setattr(validate_standardization, "standardize_text", explode)

    validator = _run(tmp_path)

    assert [issue.category for issue in validator._issues] == ["standardizer-error"]
    assert validator.errors_found == 1
    assert "unbalanced braces" in validator._issues[0].message


def test_unreadable_file_is_an_error(tmp_path):
    # Non-UTF-8 bytes: the file cannot be checked, so it must not pass silently.
    path = write_under(tmp_path, "events/Gulf.txt", "")
    path.write_bytes(b"country_event = {\n\tid = \xff\xfe\n}\n")

    validator = _run(tmp_path)

    assert [issue.category for issue in validator._issues] == ["standardizer-error"]
    assert "could not read the file" in validator._issues[0].message


def test_scan_file_ignores_a_path_no_standardizer_owns(tmp_path):
    unowned = tmp_path / "common" / "units" / "MD_land_units.txt"
    unowned.parent.mkdir(parents=True)
    unowned.write_text(_MESSY_EVENT, encoding="utf-8")

    assert validate_standardization._scan_file((str(unowned), str(tmp_path))) is None


def test_staged_mode_only_checks_staged_files(tmp_path, monkeypatch):
    _write_event(tmp_path, _MESSY_EVENT)
    _write_event(tmp_path, _MESSY_EVENT, name="events/Syria.txt")
    monkeypatch.setenv("MD_STAGED_FILES", "events/Syria.txt")

    validator = _run(tmp_path, staged_only=True)

    assert [issue.file for issue in validator._issues] == ["events/Syria.txt"]


def test_scan_all_overrides_staged_scope(tmp_path, monkeypatch):
    _write_event(tmp_path, _MESSY_EVENT)
    _write_event(tmp_path, _MESSY_EVENT, name="events/Syria.txt")
    monkeypatch.setenv("MD_STAGED_FILES", "events/Syria.txt")

    validator = _run(tmp_path, staged_only=True, scan_all=True)

    assert sorted(issue.file for issue in validator._issues) == [
        "events/Gulf.txt",
        "events/Syria.txt",
    ]


_MESSY_FOCUS = "focus = {\n\tid = TST_first\n\tx = 0\n\ty = 0\n}\n"


@pytest.mark.parametrize(
    ("kind", "expected"),
    [("focus", ["common/national_focus/test.txt"]), ("event", ["events/test.txt"])],
)
def test_kind_scope_checks_only_the_selected_standardizer(tmp_path, kind, expected):
    write_under(tmp_path, "common/national_focus/test.txt", _MESSY_FOCUS)
    write_under(tmp_path, "events/test.txt", _MESSY_EVENT)

    assert [issue.file for issue in _run(tmp_path, kind=kind)._issues] == expected


@pytest.mark.parametrize("ending", ["crlf", "missing newline", "added line"])
def test_line_ending_drift_is_reported_without_writing(tmp_path, monkeypatch, ending):
    formatted = standardize_api.standardize_text("event", _MESSY_EVENT)
    assert formatted is not None
    path = _write_event(tmp_path, "")
    if ending == "crlf":
        original = formatted.replace("\n", "\r\n").encode("utf-8")
        line = 1
    elif ending == "missing newline":
        original = formatted.rstrip("\n").encode("utf-8")
        line = len(formatted.splitlines())
    else:
        original = formatted.encode("utf-8")
        line = len(formatted.splitlines()) + 1
        monkeypatch.setattr(
            validate_standardization,
            "standardize_text",
            lambda kind, text, mod_root=None: text.rstrip("\n") + "\n\n",
        )
    path.write_bytes(original)

    validator = _run(tmp_path)

    assert [(issue.category, issue.line) for issue in validator._issues] == [
        ("not-standardized", line)
    ]
    assert path.read_bytes() == original


_REWRITE_FAILURES = {
    "unstable rewrite": ("unstable", "not idempotent", 0),
    "changed reward": ("reward", "TST_first: completion_reward content changed", 1),
    "changed identity": ("identity", "focus IDs, kinds, or order changed", 0),
}


@pytest.mark.parametrize(
    ("mutation", "message", "line"),
    _REWRITE_FAILURES.values(),
    ids=_REWRITE_FAILURES,
)
def test_unsafe_rewrite_is_an_error_without_writing(
    tmp_path, monkeypatch, mutation, message, line
):
    source = (
        "focus = {\n\tid = TST_first\n"
        "\tcompletion_reward = { add_political_power = 5 }\n}\n"
    )
    path = write_under(tmp_path, "common/national_focus/test.txt", source)
    standardize = validate_standardization.standardize_text

    def rewrite(kind, text, mod_root=None):
        if mutation == "unstable":
            return text + "\n"
        formatted = standardize(kind, text, mod_root=mod_root)
        assert formatted is not None
        if mutation == "reward":
            return formatted.replace(
                "add_political_power = 5", "add_political_power = 6"
            )
        return formatted.replace("TST_first", "TST_other")

    monkeypatch.setattr(validate_standardization, "standardize_text", rewrite)

    validator = _run(tmp_path)

    assert validator.errors_found == 1
    assert validator.warnings_found == 0
    assert validator._issues[0].category == "standardizer-error"
    assert message in validator._issues[0].message
    assert validator._issues[0].line == line
    assert path.read_text(encoding="utf-8") == source


def test_run_calls_every_check(tmp_path, monkeypatch):
    validator = Validator(str(tmp_path), workers=1)

    called, defined = checks_called_by_run(validator, monkeypatch)

    assert called == defined


def test_cli_kind_scope_is_read_only(tmp_path):
    path = write_under(tmp_path, "common/national_focus/test.txt", _MESSY_FOCUS)
    write_under(tmp_path, "events/test.txt", _MESSY_EVENT)

    result = run_tool_script(
        "validation/validate_standardization.py",
        "--path",
        tmp_path,
        "--all",
        "--kind",
        "focus",
        "--no-color",
        "--strict",
    )

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "common/national_focus/test.txt" in output
    assert "events/test.txt" not in output
    assert "Files checked: 1; unchanged: 0; drifted: 1; failed: 0" in output
    assert path.read_text(encoding="utf-8") == _MESSY_FOCUS
