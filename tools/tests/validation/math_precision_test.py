"""Regressions for the >5-decimal math-literal check in validate_variables.

HOI4 silently truncates a numeric literal at 5 decimal places, so a value like
0.123456 computes wrong at runtime. Both the operator form (`value = 0.123456`)
and the shorthand form (`set_variable = { var = 0.123456 }`) must be caught,
including when the offending key is not the first one in the _variable block.
"""

import validate_variables as V


def _matches(text):
    hits = []
    for pat in (V._MATH_PRECISION_RE, V._MATH_PRECISION_SHORTHAND_RE):
        hits += [m.group(0) for m in pat.finditer(text)]
    return hits


def test_operator_form_flagged():
    assert _matches("add = 0.123456")


def test_shorthand_first_key_flagged():
    assert _matches("set_variable = { my_var = 0.1234567 }")


def test_shorthand_non_first_key_flagged():
    # regression: the offending decimal sits on the second key, not the first
    assert _matches("clamp_variable = { var = some_var min = 0.123456789 }")


def test_five_decimals_ok():
    assert not _matches("set_variable = { my_var = 0.12345 }")


def test_plain_block_not_flagged():
    # not a _variable opener, so a many-decimal factor is not a math literal
    assert not _matches("ai_will_do = { factor = 0.123456 }")


def test_single_literal_reports_once(tmp_path):
    # regression: the operator and shorthand patterns both fire on the same
    # `value =` literal — dedupe so one bad literal yields exactly one finding
    f = tmp_path / "x.txt"
    f.write_text(
        "effect = {\n"
        "    set_variable = {\n"
        "        var = my_var\n"
        "        value = 0.123456\n"
        "    }\n"
        "}\n",
        encoding="utf-8",
    )
    issues = V.process_file_for_math_precision((str(f), str(tmp_path)))
    assert len(issues) == 1


def test_two_distinct_literals_report_twice(tmp_path):
    f = tmp_path / "y.txt"
    f.write_text("set_variable = { var = 0.123456 add = 0.999999 }\n", encoding="utf-8")
    issues = V.process_file_for_math_precision((str(f), str(tmp_path)))
    assert len(issues) == 2
