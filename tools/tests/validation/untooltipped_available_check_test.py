"""Regressions for the untooltipped-check_variable check in validate_variables.

check_variable renders no tooltip line, so bare inside an `available` block the
player sees a greyed-out decision/focus with a blank requirement and nothing
explaining what is missing. It must sit under a tooltip wrapper.

`visible` is deliberately not covered: a failing visible hides the object
outright, so no tooltip renders either way.
"""

import validate_variables as V

# The AI-only exemption keys off the decisions path, so a test that wants it
# has to write the file where decisions actually live.
_DECISION_REL = "common/decisions/src.txt"


def _findings(tmp_path, text, ai_categories=frozenset(), rel="src.txt"):
    f = tmp_path / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text, encoding="utf-8")
    return V.process_file_for_untooltipped_available_checks(
        (str(f), str(tmp_path), ai_categories)
    )


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


def test_inline_tooltip_ok(tmp_path):
    # check_variable's own `tooltip` field renders the requirement line itself.
    out = _findings(
        tmp_path,
        "my_decision = {\n"
        "\tavailable = {\n"
        "\t\tcheck_variable = {\n"
        "\t\t\ttooltip = my_tt\n"
        "\t\t\tvar = my_var\n"
        "\t\t\tvalue = 5\n"
        "\t\t\tcompare = less_than\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    assert out == []


def test_inline_tooltip_with_nested_value_block_ok(tmp_path):
    out = _findings(
        tmp_path,
        "my_decision = {\n"
        "\tavailable = {\n"
        "\t\tcheck_variable = {\n"
        "\t\t\tvar = my_var\n"
        "\t\t\tvalue = { base = 2 add = 3 }\n"
        "\t\t\tcompare = less_than\n"
        "\t\t\ttooltip = my_tt\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    assert out == []


def test_long_form_without_tooltip_still_flagged(tmp_path):
    out = _findings(
        tmp_path,
        "my_decision = {\n"
        "\tavailable = {\n"
        "\t\tcheck_variable = {\n"
        "\t\t\tvar = my_var\n"
        "\t\t\tvalue = 5\n"
        "\t\t\tcompare = less_than\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    assert len(out) == 1


def test_inline_tooltip_does_not_mask_following_check(tmp_path):
    out = _findings(
        tmp_path,
        "my_decision = {\n"
        "\tavailable = {\n"
        "\t\tcheck_variable = { tooltip = my_tt var = a value = 5 compare = less_than }\n"
        "\t\tcheck_variable = { b > 2 }\n"
        "\t}\n"
        "}\n",
    )
    assert len(out) == 1
    assert out[0][2] == 4


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


# --- AI-only exemption -------------------------------------------------------
#
# Nobody reads a requirement line on a decision no human player can see, so the
# wrapper the check demands would be dead weight there.


_AI_DECISION = (
    "some_category = {\n"
    "\tmy_decision = {\n"
    "\t\t{gate}\n"
    "\t\tavailable = {\n"
    "\t\t\tcheck_variable = { my_var > 5 }\n"
    "\t\t}\n"
    "\t}\n"
    "}\n"
)


def _decision_file(gate):
    return _AI_DECISION.replace("{gate}", gate)


def test_is_ai_in_visible_exempts(tmp_path):
    out = _findings(
        tmp_path, _decision_file("visible = { is_ai = yes }"), rel=_DECISION_REL
    )
    assert out == []


def test_is_ai_in_allowed_exempts(tmp_path):
    out = _findings(
        tmp_path, _decision_file("allowed = { is_ai = yes }"), rel=_DECISION_REL
    )
    assert out == []


def test_is_ai_in_available_exempts(tmp_path):
    out = _findings(
        tmp_path,
        "some_category = {\n"
        "\tmy_decision = {\n"
        "\t\tavailable = {\n"
        "\t\t\tis_ai = yes\n"
        "\t\t\tcheck_variable = { my_var > 5 }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
        rel=_DECISION_REL,
    )
    assert out == []


def test_is_ai_in_available_with_ai_category_exempts(tmp_path):
    out = _findings(
        tmp_path,
        "some_category = {\n"
        "\tmy_decision = {\n"
        "\t\tavailable = {\n"
        "\t\t\tis_ai = yes\n"
        "\t\t\tcheck_variable = { my_var > 5 }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
        ai_categories=frozenset({"some_category"}),
        rel=_DECISION_REL,
    )
    assert out == []


def test_is_ai_nested_in_or_does_not_exempt(tmp_path):
    out = _findings(
        tmp_path,
        _decision_file("visible = { OR = { is_ai = yes is_debug = yes } }"),
        rel=_DECISION_REL,
    )
    assert len(out) == 1


def test_ai_only_category_exempts_member_decision(tmp_path):
    out = _findings(
        tmp_path,
        _decision_file("cost = 25"),
        ai_categories=frozenset({"some_category"}),
        rel=_DECISION_REL,
    )
    assert out == []


def test_ordinary_category_in_same_file_still_flagged(tmp_path):
    out = _findings(
        tmp_path,
        "ai_category = {\n"
        "\tai_decision = {\n"
        "\t\tavailable = {\n"
        "\t\t\tcheck_variable = { my_var > 5 }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n"
        "human_category = {\n"
        "\thuman_decision = {\n"
        "\t\tavailable = {\n"
        "\t\t\tcheck_variable = { my_var > 5 }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
        ai_categories=frozenset({"ai_category"}),
        rel=_DECISION_REL,
    )
    assert len(out) == 1
    assert out[0][2] == 11


def test_sibling_decision_of_ai_only_one_still_flagged(tmp_path):
    out = _findings(
        tmp_path,
        "some_category = {\n"
        "\tai_decision = {\n"
        "\t\tvisible = { is_ai = yes }\n"
        "\t\tavailable = {\n"
        "\t\t\tcheck_variable = { my_var > 5 }\n"
        "\t\t}\n"
        "\t}\n"
        "\thuman_decision = {\n"
        "\t\tavailable = {\n"
        "\t\t\tcheck_variable = { my_var > 5 }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
        rel=_DECISION_REL,
    )
    assert len(out) == 1
    assert out[0][2] == 10


def test_ai_only_decision_after_a_sibling_is_still_exempt(tmp_path):
    # The span walk used to land back on each decision's closing brace, driving
    # its depth count negative so only the first decision in a category was
    # ever tested. Every AI-only decision here must be exempt, whatever its
    # position, and the one human decision must still be flagged.
    out = _findings(
        tmp_path,
        "some_category = {\n"
        "\thuman_decision = {\n"
        "\t\tavailable = {\n"
        "\t\t\tcheck_variable = { my_var > 5 }\n"
        "\t\t}\n"
        "\t}\n"
        "\tfirst_ai_decision = {\n"
        "\t\tvisible = { is_ai = yes }\n"
        "\t\tavailable = {\n"
        "\t\t\tcheck_variable = { my_var > 5 }\n"
        "\t\t}\n"
        "\t}\n"
        "\tsecond_ai_decision = {\n"
        "\t\tvisible = { is_ai = yes }\n"
        "\t\tavailable = {\n"
        "\t\t\tcheck_variable = { my_var > 5 }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
        rel=_DECISION_REL,
    )
    assert len(out) == 1
    assert out[0][2] == 4


def test_category_definition_file_not_treated_as_decisions(tmp_path):
    # `common/decisions/categories/` holds the categories themselves, not the
    # category -> decision nesting the span walk assumes.
    out = _findings(
        tmp_path,
        "my_category = {\n"
        "\tvisible = { is_ai = yes }\n"
        "\tavailable = {\n"
        "\t\tcheck_variable = { my_var > 5 }\n"
        "\t}\n"
        "}\n",
        rel="common/decisions/categories/cat.txt",
    )
    assert len(out) == 1


def test_focus_tree_with_is_ai_still_flagged(tmp_path):
    # The span walk is decisions-only: a focus is not a category/decision pair.
    out = _findings(
        tmp_path,
        "focus_tree = {\n"
        "\tfocus = {\n"
        "\t\tid = MY_focus\n"
        "\t\tavailable = {\n"
        "\t\t\tis_ai = yes\n"
        "\t\t\tcheck_variable = { my_var > 5 }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
        rel="common/national_focus/my_tree.txt",
    )
    assert len(out) == 1
