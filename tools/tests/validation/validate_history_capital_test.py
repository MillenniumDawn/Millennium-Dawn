"""Tests for the capital-defined check in validate_history.

`capital = N` is valid whether written at column 0 or indented (e.g. inside a
DLC-guarded block). The check must match it anywhere on a line, comment-aware.
"""

import validate_history as V


def test_capital_at_column_zero(country_file):
    p = country_file('capital = 700\noob = "ARA_1990"\n')
    assert V.validate_capital_defined(p) == []


def test_indented_capital(country_file):
    p = country_file('\tcapital = 700\n\toob = "ARA_1990"\n')
    assert V.validate_capital_defined(p) == []


def test_missing_capital(country_file):
    p = country_file('oob = "ARA_1990"\n')
    assert V.validate_capital_defined(p) != []


def test_commented_capital_does_not_count(country_file):
    p = country_file('# capital = 700\noob = "ARA_1990"\n')
    assert V.validate_capital_defined(p) != []
