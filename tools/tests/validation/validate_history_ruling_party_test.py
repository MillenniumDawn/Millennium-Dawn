"""Tests for the ruling_party assignment check in validate_history.

start_politics_input clears ruling_party. set_politics = { ruling_party = democratic }
is the vanilla ideology token and must not count as the MD 0-23 index.
"""

import validate_history as V


def _country_file(tmp_path, body):
    d = tmp_path / "history" / "countries"
    d.mkdir(parents=True, exist_ok=True)
    p = d / "ARA - Arabistan.txt"
    p.write_text(body, encoding="utf-8")
    return str(p)


def test_no_start_politics_input_is_silent(tmp_path):
    p = _country_file(tmp_path, "capital = 1\n")
    assert V.validate_ruling_party_assigned(p) == []


def test_assignment_after_start_politics_input(tmp_path):
    p = _country_file(
        tmp_path,
        "2000.1.1 = {\n"
        "\tstart_politics_input = yes\n"
        "\tset_variable = { ruling_party = 2 }\n"
        "}\n",
    )
    assert V.validate_ruling_party_assigned(p) == []


def test_missing_assignment_after_start_politics_input(tmp_path):
    p = _country_file(
        tmp_path,
        "2000.1.1 = {\n"
        "\tstart_politics_input = yes\n"
        "\tset_variable = { party_pop_array^1 = 0.3 }\n"
        "}\n",
    )
    assert V.validate_ruling_party_assigned(p) == [
        "ARA - Arabistan.txt: 2000.1.1: start_politics_input does not assign "
        "ruling_party (0-23) after it"
    ]


def test_assignment_before_start_politics_input_does_not_count(tmp_path):
    p = _country_file(
        tmp_path,
        "2000.1.1 = {\n"
        "\tset_variable = { ruling_party = 2 }\n"
        "\tstart_politics_input = yes\n"
        "}\n",
    )
    assert V.validate_ruling_party_assigned(p) != []


def test_set_politics_ruling_party_does_not_count(tmp_path):
    p = _country_file(
        tmp_path,
        "2000.1.1 = {\n"
        "\tstart_politics_input = yes\n"
        "\tset_politics = { ruling_party = democratic }\n"
        "}\n",
    )
    assert V.validate_ruling_party_assigned(p) != []


def test_commented_assignment_does_not_count(tmp_path):
    p = _country_file(
        tmp_path,
        "2000.1.1 = {\n"
        "\tstart_politics_input = yes\n"
        "\t# set_variable = { ruling_party = 2 }\n"
        "}\n",
    )
    assert V.validate_ruling_party_assigned(p) != []


def test_out_of_range_index_does_not_count(tmp_path):
    p = _country_file(
        tmp_path,
        "2000.1.1 = {\n"
        "\tstart_politics_input = yes\n"
        "\tset_variable = { ruling_party = 24 }\n"
        "}\n",
    )
    assert V.validate_ruling_party_assigned(p) != []


def test_later_date_block_is_checked_separately(tmp_path):
    p = _country_file(
        tmp_path,
        "2000.1.1 = {\n"
        "\tstart_politics_input = yes\n"
        "\tset_variable = { ruling_party = 2 }\n"
        "}\n"
        "2017.1.1 = {\n"
        "\tstart_politics_input = yes\n"
        "}\n",
    )
    assert V.validate_ruling_party_assigned(p) == [
        "ARA - Arabistan.txt: 2017.1.1: start_politics_input does not assign "
        "ruling_party (0-23) after it"
    ]


def test_last_start_politics_input_in_block_is_the_clear(tmp_path):
    p = _country_file(
        tmp_path,
        "2000.1.1 = {\n"
        "\tstart_politics_input = yes\n"
        "\tstart_politics_input = yes\n"
        "\tset_variable = { ruling_party = 14 }\n"
        "}\n",
    )
    assert V.validate_ruling_party_assigned(p) == []


def test_undecodable_file_is_reported(tmp_path):
    d = tmp_path / "history" / "countries"
    d.mkdir(parents=True, exist_ok=True)
    p = d / "BAD - Bad.txt"
    p.write_bytes(b"\xff\xfe start_politics_input = yes\n")
    assert V.validate_ruling_party_assigned(str(p)) == [
        "BAD - Bad.txt: could not read file"
    ]
