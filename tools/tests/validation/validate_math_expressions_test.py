"""Tests for the math-expression trap scanner (validate_math_expressions)."""

from shared.suite import write_under as _write
from validate_math_expressions import Validator, scan_text

BROKEN_SIBLING = """set_variable = {
\tvar = combined_units
\tvalue = num_cavalry
\tadd = num_motorized
\tadd = num_mechanized
}
"""

VALID_LONG_FORM = """set_temp_variable = {
\tfoo = {
\t\tvalue = bar
\t\tmultiply = 2
\t\tadd = baz
\t}
}
"""

VALID_SHORT_FORM = """add_to_variable = {
\tvar = global.cumulative
\tvalue = {
\t\tvalue = overall_productivity
\t\tmultiply = 0.001
\t}
}
"""

REAL_SCOPED_VARIABLES = """set_variable = {
\tglobal.average_world_productivity = {
\t\tvalue = global.cumulative_world_productivity
\t\tdivide = global.world_population
\t\tmultiply = 1000
\t}
}
set_variable = {
\tglobal.productivity_center = {
\t\tvalue = global.average_world_productivity
\t\tclamp = { min = 1000 max = 100000000 }
\t}
}
"""


def test_sibling_operators_beside_value_are_flagged():
    findings = scan_text(BROKEN_SIBLING)

    assert [f[1] for f in findings] == ["math-sibling-operator"]
    assert findings[0][0] == 1
    assert "add" in findings[0][2]


def test_sibling_operator_beside_scalar_value_is_flagged():
    findings = scan_text("set_variable = { X = 0 add = Y }\n")

    assert [f[1] for f in findings] == ["math-sibling-operator"]


def test_long_and_short_expression_forms_are_clean():
    assert scan_text(VALID_LONG_FORM + VALID_SHORT_FORM) == []


def test_real_scoped_variable_assignments_are_clean():
    assert scan_text(REAL_SCOPED_VARIABLES) == []


def test_scoped_and_array_variable_keys_are_walked():
    script = (
        "set_variable = {\n"
        "\tROOT.productivity^i = { value = PREV.productivity }\n"
        "\tevent_target:target.productivity = { value = global.productivity }\n"
        "}\n"
    )

    assert scan_text(script) == []


def test_malformed_siblings_beside_scoped_assignment_are_flagged():
    script = (
        "set_variable = {\n"
        "\tglobal.productivity = { value = current_productivity }\n"
        "\tadd = productivity_bonus\n"
        "}\n"
    )

    findings = scan_text(script)

    assert [f[1] for f in findings] == ["math-sibling-operator"]


def test_unsafe_comparator_and_from_read_in_nested_operands_are_flagged():
    script = (
        "set_variable = {\n"
        "\tglobal.productivity = {\n"
        "\t\tvalue = {\n"
        "\t\t\tadd = { value = FROM.productivity }\n"
        "\t\t\tmultiply = { value = 1 less_than_or_equals = 2 }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )

    assert [f[1] for f in scan_text(script)] == [
        "math-from-read",
        "math-unsafe-comparator",
    ]


def test_unknown_expression_blocks_do_not_leak_descendants():
    script = (
        "set_variable = {\n"
        "\tvalue = {\n"
        "\t\tvalue = 1\n"
        "\t\tunknown.scope = {\n"
        "\t\t\tif = { limit = { value = FROM.unread equals = 2 } }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )

    assert scan_text(script) == []


def test_unsafe_comparator_inside_expression_is_flagged():
    script = (
        "set_temp_variable = {\n"
        "\tchance = {\n"
        "\t\tvalue = v\n"
        "\t\tif = { limit = { value = reach equals = 1 } add = 15 }\n"
        "\t}\n"
        "}\n"
    )

    findings = scan_text(script)

    assert [f[1] for f in findings] == ["math-unsafe-comparator"]
    assert findings[0][0] == 4


def test_unsafe_comparator_in_nested_operand_is_flagged():
    script = (
        "set_variable = { X = { value = 1 add = { value = y "
        "less_than_or_equals = 3 } } }\n"
    )

    assert [f[1] for f in scan_text(script)] == ["math-unsafe-comparator"]


def test_effect_level_check_variable_comparators_are_clean():
    script = (
        "if = {\n"
        "\tlimit = { check_variable = { target = 0 } }\n"
        "\tset_variable = { var = ok value = 1 }\n"
        "}\n"
    )

    assert scan_text(script) == []


def test_check_variable_inside_expression_limit_is_not_judged():
    script = (
        "set_temp_variable = {\n"
        "\tX = {\n"
        "\t\tvalue = 1\n"
        "\t\tif = { limit = { check_variable = { test = 0 compare = equals } } "
        "add = 2 }\n"
        "\t}\n"
        "}\n"
    )

    assert scan_text(script) == []


def test_from_read_in_expression_is_flagged():
    script = (
        "set_temp_variable = {\n"
        "\tchange = {\n"
        "\t\tvalue = FROM.debt_bailout\n"
        "\t\tmultiply = -0.75\n"
        "\t}\n"
        "}\n"
    )

    findings = scan_text(script)

    assert [f[1] for f in findings] == ["math-from-read"]
    assert findings[0][0] == 3


def test_from_read_in_expression_limit_is_flagged():
    script = (
        "set_temp_variable = {\n"
        "\tX = {\n"
        "\t\tvalue = 1\n"
        "\t\tif = { limit = { value = FROM.reach less_than = 1 } add = 2 }\n"
        "\t}\n"
        "}\n"
    )

    assert [f[1] for f in scan_text(script)] == ["math-from-read"]


def test_plain_from_copy_at_effect_level_is_clean():
    script = (
        "set_temp_variable = { bailout_cost = FROM.debt_bailout }\n"
        "FROM = { set_variable = { var = local value = 1 } }\n"
    )

    assert scan_text(script) == []


def test_working_expression_constructs_are_clean():
    script = (
        "set_variable = { X = { value = units greater_than = { value = num "
        "multiply = 0.4 } } }\n"
        "set_temp_variable = { Y = { value = Z clamp = { min = 0 max = 100 } "
        "round = yes } }\n"
        "set_variable = { W = { value = ROOT.gdp multiply = 0.01 } }\n"
    )

    assert scan_text(script) == []


def test_commented_out_traps_are_not_scanned():
    script = "# set_variable = {\n#\tvar = x\n#\tadd = y\n# }\n"

    assert scan_text(script) == []


def test_clamp_and_modulo_effects_are_out_of_scope():
    script = (
        "clamp_variable = { var = X min = 0 max = 5 }\n"
        "modulo_variable = { var = Y value = Z }\n"
    )

    assert scan_text(script) == []


def _validator(tmp_path):
    return Validator(str(tmp_path), use_colors=False, workers=1, no_cache=True)


def test_validator_reports_file_and_line(tmp_path):
    _write(tmp_path, "common/scripted_effects/traps.txt", BROKEN_SIBLING)

    v = _validator(tmp_path)
    v.run_validations()

    assert [(i.category, i.file, i.line) for i in v._issues] == [
        ("math-sibling-operator", "common/scripted_effects/traps.txt", 1)
    ]
    assert all(i.severity == "warning" for i in v._issues)


def test_clean_repo_is_a_clean_pass(tmp_path):
    _write(
        tmp_path,
        "common/scripted_effects/fine.txt",
        VALID_LONG_FORM + VALID_SHORT_FORM,
    )

    v = _validator(tmp_path)
    v.run_validations()

    assert v._issues == []


def test_staged_mode_scans_only_staged_files(tmp_path, monkeypatch):
    _write(tmp_path, "common/scripted_effects/traps.txt", BROKEN_SIBLING)
    _write(tmp_path, "events/other.txt", BROKEN_SIBLING)
    monkeypatch.setenv("MD_STAGED_FILES", "common/scripted_effects/traps.txt")

    v = Validator(
        str(tmp_path), use_colors=False, workers=1, no_cache=True, staged_only=True
    )
    v.run_validations()

    assert [i.file for i in v._issues] == ["common/scripted_effects/traps.txt"]
