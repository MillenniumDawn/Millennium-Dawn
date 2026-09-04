"""Tests for the ruling_party assignment check in validate_history.

start_politics_input clears ruling_party. set_politics = { ruling_party = democratic }
is the vanilla ideology token and must not count as the MD 0-23 index.
"""

import pytest
import validate_history as V

_MISSING_2000 = (
    "ARA - Arabistan.txt: 2000.1.1: start_politics_input does not assign "
    "ruling_party (0-23) after it"
)


def _dated(inner):
    return "2000.1.1 = {\n" + inner + "}\n"


def test_no_start_politics_input_is_silent(country_file):
    assert V.validate_ruling_party_assigned(country_file("capital = 1\n")) == []


def test_assignment_after_start_politics_input(country_file):
    body = _dated(
        "\tstart_politics_input = yes\n\tset_variable = { ruling_party = 2 }\n"
    )
    assert V.validate_ruling_party_assigned(country_file(body)) == []


def test_missing_assignment_after_start_politics_input(country_file):
    body = _dated(
        "\tstart_politics_input = yes\n\tset_variable = { party_pop_array^1 = 0.3 }\n"
    )
    assert V.validate_ruling_party_assigned(country_file(body)) == [_MISSING_2000]


@pytest.mark.parametrize(
    "inner",
    [
        "\tset_variable = { ruling_party = 2 }\n\tstart_politics_input = yes\n",
        "\tstart_politics_input = yes\n\tset_politics = { ruling_party = democratic }\n",
        "\tstart_politics_input = yes\n\t# set_variable = { ruling_party = 2 }\n",
        "\tstart_politics_input = yes\n\tset_variable = { ruling_party = 24 }\n",
    ],
)
def test_invalid_ruling_party_assignment_is_reported(country_file, inner):
    assert V.validate_ruling_party_assigned(country_file(_dated(inner))) == [
        _MISSING_2000
    ]


def test_later_date_block_is_checked_separately(country_file):
    body = (
        _dated("\tstart_politics_input = yes\n\tset_variable = { ruling_party = 2 }\n")
        + "2017.1.1 = {\n\tstart_politics_input = yes\n}\n"
    )
    assert V.validate_ruling_party_assigned(country_file(body)) == [
        "ARA - Arabistan.txt: 2017.1.1: start_politics_input does not assign "
        "ruling_party (0-23) after it"
    ]


def test_last_start_politics_input_in_block_is_the_clear(country_file):
    body = _dated(
        "\tstart_politics_input = yes\n"
        "\tstart_politics_input = yes\n"
        "\tset_variable = { ruling_party = 14 }\n"
    )
    assert V.validate_ruling_party_assigned(country_file(body)) == []


def test_undecodable_file_is_reported(tmp_path):
    d = tmp_path / "history" / "countries"
    d.mkdir(parents=True, exist_ok=True)
    p = d / "BAD - Bad.txt"
    p.write_bytes(b"\xff\xfe start_politics_input = yes\n")
    assert V.validate_ruling_party_assigned(str(p)) == [
        "BAD - Bad.txt: could not read file"
    ]
