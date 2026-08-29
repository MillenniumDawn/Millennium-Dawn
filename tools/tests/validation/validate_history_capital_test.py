"""Tests for the capital-defined check in validate_history.

`capital = N` is valid whether written at column 0 or indented (e.g. inside a
DLC-guarded block). The check must match it anywhere on a line, comment-aware.
"""

import validate_history as V


def _country_file(tmp_path, body):
    d = tmp_path / "history" / "countries"
    d.mkdir(parents=True, exist_ok=True)
    p = d / "ARA - Arabistan.txt"
    p.write_text(body, encoding="utf-8")
    return str(p)


def test_capital_at_column_zero(tmp_path):
    p = _country_file(tmp_path, 'capital = 700\noob = "ARA_1990"\n')
    assert V.validate_capital_defined(p) == []


def test_indented_capital(tmp_path):
    p = _country_file(tmp_path, '\tcapital = 700\n\toob = "ARA_1990"\n')
    assert V.validate_capital_defined(p) == []


def test_missing_capital(tmp_path):
    p = _country_file(tmp_path, 'oob = "ARA_1990"\n')
    assert V.validate_capital_defined(p) != []


def test_commented_capital_does_not_count(tmp_path):
    p = _country_file(tmp_path, '# capital = 700\noob = "ARA_1990"\n')
    assert V.validate_capital_defined(p) != []
