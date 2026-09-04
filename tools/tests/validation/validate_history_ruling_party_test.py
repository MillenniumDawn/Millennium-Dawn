"""Tests for the ruling_party assignment check in validate_history.

start_politics_input clears ruling_party. set_politics = { ruling_party = democratic }
is the vanilla ideology token and must not count as the MD 0-23 index.
"""

import validate_history as V


def test_no_start_politics_input_is_silent(country_file):
    p = country_file("capital = 1\n")
    assert V.validate_ruling_party_assigned(p) == []


def test_assignment_after_start_politics_input(country_file):
    p = country_file(
        "2000.1.1 = {\n"
        "\tstart_politics_input = yes\n"
        "\tset_variable = { ruling_party = 2 }\n"
        "}\n",
    )
    assert V.validate_ruling_party_assigned(p) == []


def test_missing_assignment_after_start_politics_input(country_file):
    p = country_file(
        "2000.1.1 = {\n"
        "\tstart_politics_input = yes\n"
        "\tset_variable = { party_pop_array^1 = 0.3 }\n"
        "}\n",
    )
    assert V.validate_ruling_party_assigned(p) == [
        "ARA - Arabistan.txt: 2000.1.1: start_politics_input does not assign "
        "ruling_party (0-23) after it"
    ]
