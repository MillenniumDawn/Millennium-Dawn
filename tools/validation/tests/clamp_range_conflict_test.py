"""Regressions for the clamp-range conflict check in validate_variables.

A variable clamped to a literal min/max can never hold a value outside it, so a
check_variable comparing against one is dead logic — always true or always false.
The sub-1 heuristic catches the inverse slip that motivated the check: a 0-1
scale value written against a variable clamped to a wide integer range, e.g.
`taliban_strength > 0.19` on a 0..100 clamp, which fires immediately instead of
at 19%.
"""

import validate_variables as V


def _ranges(tmp_path, text):
    f = tmp_path / "src.txt"
    f.write_text(text, encoding="utf-8")
    return {
        name: (lo, hi)
        for name, lo, hi in V.collect_clamp_ranges((str(f), str(tmp_path)))
    }


def _conflicts(tmp_path, text, ranges):
    f = tmp_path / "use.txt"
    f.write_text(text, encoding="utf-8")
    return V.process_file_for_clamp_conflicts((str(f), str(tmp_path), ranges))


def test_collects_clamp_range(tmp_path):
    got = _ranges(
        tmp_path, "clamp_variable = { var = taliban_strength min = 0 max = 100 }"
    )
    assert got == {"taliban_strength": (0.0, 100.0)}


def test_global_prefix_normalised(tmp_path):
    got = _ranges(
        tmp_path, "clamp_variable = { var = global.some_var min = 0 max = 50 }"
    )
    assert "some_var" in got


def test_value_above_max_flagged(tmp_path):
    out = _conflicts(
        tmp_path,
        "check_variable = { my_var > 51 }",
        {"my_var": (0.0, 50.0)},
    )
    assert len(out) == 1 and "never change outcome" in out[0]


def test_value_below_min_flagged(tmp_path):
    out = _conflicts(
        tmp_path,
        "check_variable = { my_var < 0.6 }",
        {"my_var": (0.8, 50.0)},
    )
    assert len(out) == 1 and "never change outcome" in out[0]


def test_scale_slip_flagged(tmp_path):
    # the taliban_strength bug: 0-1 scale value against a 0..100 clamp
    out = _conflicts(
        tmp_path,
        "check_variable = { taliban_strength > 0.19 }",
        {"taliban_strength": (0.0, 100.0)},
    )
    assert len(out) == 1 and "0-1 scale value" in out[0]


def test_long_form_flagged(tmp_path):
    out = _conflicts(
        tmp_path,
        "check_variable = { var = my_var value = 200 compare = greater_than }",
        {"my_var": (0.0, 100.0)},
    )
    assert len(out) == 1


def test_in_range_value_ok(tmp_path):
    out = _conflicts(
        tmp_path,
        "check_variable = { taliban_strength > 19 }",
        {"taliban_strength": (0.0, 100.0)},
    )
    assert out == []


def test_fractional_ok_on_narrow_clamp(tmp_path):
    # a variable genuinely clamped to 0..1 should accept fractional comparisons
    out = _conflicts(
        tmp_path,
        "check_variable = { taliban_attack_strength > 0.19 }",
        {"taliban_attack_strength": (0.0, 1.0)},
    )
    assert out == []


def test_unclamped_variable_ignored(tmp_path):
    out = _conflicts(tmp_path, "check_variable = { unknown_var > 9999 }", {})
    assert out == []


def test_commented_line_ignored(tmp_path):
    out = _conflicts(
        tmp_path,
        "# check_variable = { my_var > 51 }",
        {"my_var": (0.0, 50.0)},
    )
    assert out == []
