"""Tests for the in-memory standardization entry point.

`standardize_api` is what the pre-commit router and validate_standardization.py
both drive, so routing lives in one place and neither of them has to write a
file to find out what the formatter would produce.
"""

import pytest
from standardize_api import kind_for_path, standardize_lines, standardize_text

_ROUTED = [
    ("common/national_focus/05_poland.txt", "focus"),
    ("events/Gulf.txt", "event"),
    ("common/decisions/Sudan.txt", "decision"),
    ("common/decisions/categories/MD_categories.txt", "decision"),
    ("common/ideas/Bosnian.txt", "idea"),
    ("common/military_industrial_organization/organizations/MD_ARG.txt", "mio"),
    ("common/military_industrial_organization/policies/_land_policies.txt", "mio"),
]

_UNROUTED = [
    "common/units/MD_land_units.txt",
    "history/countries/ARA - Arabistan.txt",
    "events/Gulf.yml",
    "localisation/english/MD_focus_SER_l_english.yml",
    "common/national_focus/notes.md",
]


@pytest.mark.parametrize("path,expected", _ROUTED)
def test_kind_for_path_routes_owned_paths(path, expected):
    assert kind_for_path(path) == expected


@pytest.mark.parametrize("path", _UNROUTED)
def test_kind_for_path_ignores_unowned_paths(path):
    assert kind_for_path(path) is None


def test_kind_for_path_accepts_absolute_and_windows_separators():
    assert kind_for_path("D:/checkout/common/ideas/Bosnian.txt") == "idea"
    assert kind_for_path("D:\\checkout\\events\\Gulf.txt") == "event"


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


def test_standardize_text_is_idempotent():
    once = standardize_text("event", _MESSY_EVENT)
    assert once is not None
    assert standardize_text("event", once) == once


def test_standardize_text_returns_none_when_no_block_matches():
    assert standardize_text("event", "# just a comment\n") is None


def test_standardize_text_touches_no_file(tmp_path):
    source = tmp_path / "events.txt"
    source.write_text(_MESSY_EVENT, encoding="utf-8")

    standardize_text("event", source.read_text(encoding="utf-8"))

    assert source.read_text(encoding="utf-8") == _MESSY_EVENT


def test_standardize_lines_matches_standardize_text():
    lines = _MESSY_EVENT.splitlines(keepends=True)
    from_lines = standardize_lines("event", lines)

    assert from_lines is not None
    assert "".join(line + "\n" for line in from_lines) == standardize_text(
        "event", _MESSY_EVENT
    )


def test_focus_standardization_never_reports_no_op():
    # A focus file is always rewritten (spacing is normalized line by line), so
    # the focus branch has no "nothing matched" case for a checker to skip.
    assert standardize_text("focus", "focus_tree = {\n\tid = test\n}\n") is not None
