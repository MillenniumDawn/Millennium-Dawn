"""Regressions for the untooltipped-check_variable check in validate_variables.

check_variable renders no tooltip line, so bare inside an `available` block the
player sees a greyed-out decision/focus with a blank requirement and nothing
explaining what is missing. It must sit under a tooltip wrapper.

`visible` is deliberately not covered: a failing visible hides the object
outright, so no tooltip renders either way.
"""

import validate_variables as V


def _findings(tmp_path, text):
    f = tmp_path / "src.txt"
    f.write_text(text, encoding="utf-8")
    return V.process_file_for_untooltipped_available_checks((str(f), str(tmp_path)))


def test_bare_check_in_available_flagged(tmp_path):
    out = _findings(
        tmp_path,
        "my_decision = {\n\tavailable = {\n\t\tcheck_variable = { my_var > 5 }\n\t}\n}\n",
    )
    assert len(out) == 1 and "renders no tooltip line" in out[0][0]
    assert "—" not in out[0][0]
    assert out[0][2] == 3


def test_custom_trigger_tooltip_ok(tmp_path):
    out = _findings(
        tmp_path,
        "my_decision = {\n"
        "\tavailable = {\n"
        "\t\tcustom_trigger_tooltip = {\n"
        "\t\t\ttooltip = my_tt\n"
        "\t\t\tcheck_variable = { my_var > 5 }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    assert out == []


def test_hidden_trigger_ok(tmp_path):
    out = _findings(
        tmp_path,
        "my_decision = {\n"
        "\tavailable = {\n"
        "\t\thidden_trigger = { check_variable = { my_var > 5 } }\n"
        "\t}\n"
        "}\n",
    )
    assert out == []


def test_custom_override_tooltip_ok(tmp_path):
    # 42 repo-wide uses wrap bare variable checks this way.
    out = _findings(
        tmp_path,
        "my_decision = {\n"
        "\tavailable = {\n"
        "\t\tcustom_override_tooltip = {\n"
        "\t\t\ttooltip = my_tt\n"
        "\t\t\tcheck_variable = { my_var > 5 }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    assert out == []


def test_nested_in_boolean_still_flagged(tmp_path):
    out = _findings(
        tmp_path,
        "my_decision = {\n"
        "\tavailable = {\n"
        "\t\tNOT = { OR = { check_variable = { a > 1 } check_variable = { b > 2 } } }\n"
        "\t}\n"
        "}\n",
    )
    assert len(out) == 2


def test_wrapper_several_levels_above_ok(tmp_path):
    out = _findings(
        tmp_path,
        "my_decision = {\n"
        "\tavailable = {\n"
        "\t\tcustom_trigger_tooltip = {\n"
        "\t\t\ttooltip = my_tt\n"
        "\t\t\tNOT = { OR = { check_variable = { a > 1 } } }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    assert out == []


def test_anonymous_state_scope_still_flagged(tmp_path):
    out = _findings(
        tmp_path,
        "my_decision = {\n"
        "\tavailable = {\n"
        "\t\t828 = { check_variable = { my_var > 5 } }\n"
        "\t}\n"
        "}\n",
    )
    assert len(out) == 1


def test_if_limit_inside_available_still_flagged(tmp_path):
    # `limit` at trigger level is not an effect limit — still player-facing.
    out = _findings(
        tmp_path,
        "my_focus = {\n"
        "\tavailable = {\n"
        "\t\tif = {\n"
        "\t\t\tlimit = { is_ai = no }\n"
        "\t\t\tcheck_variable = { interest_rate < 14.999 }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    assert len(out) == 1


def test_visible_not_flagged(tmp_path):
    out = _findings(
        tmp_path,
        "my_decision = {\n\tvisible = {\n\t\tcheck_variable = { my_var > 5 }\n\t}\n}\n",
    )
    assert out == []


def test_effect_limit_not_flagged(tmp_path):
    out = _findings(
        tmp_path,
        "my_decision = {\n"
        "\tcomplete_effect = {\n"
        "\t\tif = { limit = { check_variable = { my_var > 5 } } add_political_power = 10 }\n"
        "\t}\n"
        "}\n",
    )
    assert out == []


def test_ai_will_do_modifier_not_flagged(tmp_path):
    out = _findings(
        tmp_path,
        "my_decision = {\n"
        "\tai_will_do = {\n"
        "\t\tbase = 10\n"
        "\t\tmodifier = { factor = 0 check_variable = { my_var > 5 } }\n"
        "\t}\n"
        "}\n",
    )
    assert out == []


def test_commented_line_ignored(tmp_path):
    out = _findings(
        tmp_path,
        "my_decision = {\n"
        "\tavailable = {\n"
        "\t\t# check_variable = { my_var > 5 }\n"
        "\t}\n"
        "}\n",
    )
    assert out == []


def test_brace_in_log_string_does_not_desync(tmp_path):
    # An unblanked `}` inside a quoted string would pop the stack early and
    # hide the real finding below it.
    out = _findings(
        tmp_path,
        "my_decision = {\n"
        "\tcomplete_effect = {\n"
        '\t\tlog = "[GetDateText]: broken } brace"\n'
        "\t}\n"
        "\tavailable = {\n"
        "\t\tcheck_variable = { my_var > 5 }\n"
        "\t}\n"
        "}\n",
    )
    assert len(out) == 1


def test_single_line_available_flagged(tmp_path):
    out = _findings(
        tmp_path,
        "my_decision = {\n\tavailable = { check_variable = { my_var > 5 } }\n}\n",
    )
    assert len(out) == 1
