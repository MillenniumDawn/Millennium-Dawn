"""Tests for validate_influence_calls.

`change_influence_percentage` defaults `influence_target` only when the temp
variable is 0, and temp variables persist across `every_*` iterations, so a loop
call without a per-iteration set locks onto the first iterated country
(issue #4592: Spain's Hispanidad focus stacked ~20 passes onto Mexico).
"""

import pytest
import validate_influence_calls as V
from shared.paths import REPO_ROOT as _MOD_ROOT

LOOP_CALL = "change_influence_percentage = yes"
FIXED = "\t\t\t\tset_temp_variable = { influence_target = THIS }"


def _findings(script):
    return V.scan_text(script)


def _lines(script):
    return [line for line, _ in _findings(script)]


# --- the #4592 bug shape ---------------------------------------------------


def test_loop_call_without_set_is_flagged():
    script = (
        "completion_reward = {\n"
        "\tset_temp_variable = { percent_change = 2 }\n"
        "\tevery_other_country = {\n"
        "\t\tlimit = { has_country_flag = spanish_speaking_flag }\n"
        "\t\tchange_influence_percentage = yes\n"
        "\t}\n"
        "}\n"
    )
    findings = _findings(script)
    assert len(findings) == 1
    assert findings[0][0] == 5
    assert "every_other_country" in findings[0][1]


def test_fixed_loop_call_is_clean():
    script = (
        "every_other_country = {\n"
        "\tlimit = { has_country_flag = spanish_speaking_flag }\n"
        "\t" + FIXED + "\n"
        "\t" + LOOP_CALL + "\n"
        "}\n"
    )
    assert _findings(script) == []


def test_id_suffix_set_is_clean():
    script = (
        "every_country = {\n"
        "\tset_temp_variable = { influence_target = THIS.id }\n"
        "\t" + LOOP_CALL + "\n"
        "}\n"
    )
    assert _findings(script) == []


def test_fixed_country_set_inside_the_loop_is_clean():
    """A set naming an explicit country is the author's business; the check is
    mechanical about per-iteration coverage."""
    script = (
        "every_other_country = {\n"
        "\tset_temp_variable = { influence_target = MEX }\n"
        "\t" + LOOP_CALL + "\n"
        "}\n"
    )
    assert _findings(script) == []


# --- sets that do not count ------------------------------------------------


def test_set_before_the_loop_is_flagged():
    script = (
        "set_temp_variable = { influence_target = THIS }\n"
        "every_neighbor_country = {\n"
        "\t" + LOOP_CALL + "\n"
        "}\n"
    )
    assert len(_findings(script)) == 1


def test_set_after_the_call_is_flagged():
    script = (
        "every_neighbor_country = {\n"
        "\t" + LOOP_CALL + "\n"
        "\tset_temp_variable = { influence_target = THIS }\n"
        "}\n"
    )
    assert _lines(script) == [2]


def test_set_between_two_calls_covers_only_the_later():
    script = (
        "every_country = {\n"
        "\t" + LOOP_CALL + "\n"
        "\tset_temp_variable = { influence_target = THIS }\n"
        "\t" + LOOP_CALL + "\n"
        "}\n"
    )
    assert _lines(script) == [2]


def test_conditional_set_does_not_cover_the_call():
    """The call still runs on passes where the condition skipped the set."""
    script = (
        "every_other_country = {\n"
        "\tif = { limit = { is_ai = yes } set_temp_variable = { influence_target = THIS } }\n"
        "\t" + LOOP_CALL + "\n"
        "}\n"
    )
    assert len(_findings(script)) == 1


# --- reachability: every branch of a chain must set the target -------------


def test_if_and_else_both_set_cover_the_later_call():
    script = (
        "every_other_country = {\n"
        "\tif = { limit = { is_ai = yes } set_temp_variable = { influence_target = THIS } }\n"
        "\telse = { set_temp_variable = { influence_target = THIS } }\n"
        "\t" + LOOP_CALL + "\n"
        "}\n"
    )
    assert _findings(script) == []


def test_if_else_if_else_chain_all_set_is_clean():
    script = (
        "every_other_country = {\n"
        "\tif = { limit = { is_ai = yes } set_temp_variable = { influence_target = THIS } }\n"
        "\telse_if = { limit = { is_subject = yes } set_temp_variable = { influence_target = THIS } }\n"
        "\telse = { set_temp_variable = { influence_target = THIS } }\n"
        "\t" + LOOP_CALL + "\n"
        "}\n"
    )
    assert _findings(script) == []


def test_chain_with_a_branch_missing_the_set_is_flagged():
    script = (
        "every_other_country = {\n"
        "\tif = { limit = { is_ai = yes } set_temp_variable = { influence_target = THIS } }\n"
        "\telse = { " + LOOP_CALL + " }\n"
        "\t" + LOOP_CALL + "\n"
        "}\n"
    )
    assert _lines(script) == [3, 4]


def test_bare_if_with_set_is_not_reached_by_the_chain():
    """No else: the fall-through pass skips the set, so the later call is stale."""
    script = (
        "every_other_country = {\n"
        "\tif = { limit = { is_ai = yes } set_temp_variable = { influence_target = THIS } }\n"
        "\telse_if = { limit = { is_subject = yes } set_temp_variable = { influence_target = THIS } }\n"
        "\t" + LOOP_CALL + "\n"
        "}\n"
    )
    assert len(_findings(script)) == 1


def test_call_inside_else_after_set_is_clean():
    script = (
        "every_other_country = {\n"
        "\tif = { limit = { is_ai = yes } }\n"
        "\telse = {\n"
        "\t\tset_temp_variable = { influence_target = THIS }\n"
        "\t\t" + LOOP_CALL + "\n"
        "\t}\n"
        "\t" + LOOP_CALL + "\n"
        "}\n"
    )
    assert _lines(script) == [7]


def test_nested_chain_all_set_inside_if_branch_promotes_the_chain():
    script = (
        "every_other_country = {\n"
        "\tif = {\n"
        "\t\tlimit = { is_ai = yes }\n"
        "\t\tif = { limit = { has_war = yes } set_temp_variable = { influence_target = THIS } }\n"
        "\t\telse = { set_temp_variable = { influence_target = THIS } }\n"
        "\t}\n"
        "\telse = { set_temp_variable = { influence_target = THIS } }\n"
        "\t" + LOOP_CALL + "\n"
        "}\n"
    )
    assert _findings(script) == []


def test_set_in_inner_loop_does_not_cover_later_outer_call():
    """A zero-iteration inner loop never runs its set."""
    script = (
        "every_other_country = {\n"
        "\tevery_allied_country = {\n"
        "\t\tset_temp_variable = { influence_target = PREV }\n"
        "\t\t" + LOOP_CALL + "\n"
        "\t}\n"
        "\t" + LOOP_CALL + "\n"
        "}\n"
    )
    assert len(_findings(script)) == 1
    assert "every_other_country" in _findings(script)[0][1]


def test_set_before_inner_loop_names_the_inner_loop():
    """The pre-loop set covers enclosing passes, so the innermost uncovered
    loop is the one the message names."""
    script = (
        "every_other_country = {\n"
        "\tset_temp_variable = { influence_target = THIS }\n"
        "\tevery_allied_country = {\n"
        "\t\t" + LOOP_CALL + "\n"
        "\t}\n"
        "}\n"
    )
    findings = _findings(script)
    assert len(findings) == 1
    assert "every_allied_country" in findings[0][1]


# --- single-execution scopes are out of scope ------------------------------


def test_top_level_call_is_clean():
    assert _findings("change_influence_percentage = yes\n") == []


def test_country_scope_call_is_clean():
    script = "MEX = { change_influence_percentage = yes }\n"
    assert _findings(script) == []


def test_random_scope_call_is_clean():
    script = (
        "random_country = {\n"
        "\tlimit = { has_war_with = ROOT }\n"
        "\t" + LOOP_CALL + "\n"
        "}\n"
    )
    assert _findings(script) == []


def test_random_list_option_is_clean():
    script = (
        "random_list = {\n"
        "\t50 = { " + LOOP_CALL + " }\n"
        "\t50 = { add_political_power = 10 }\n"
        "}\n"
    )
    assert _findings(script) == []


# --- scoping corner cases ---------------------------------------------------


def test_effect_tooltip_loop_is_skipped():
    """`effect_tooltip` previews without executing (05_sweden.txt's royal-circle
    focus sits in exactly this shape)."""
    script = (
        "effect_tooltip = {\n"
        "\tevery_other_country = {\n"
        "\t\t" + LOOP_CALL + "\n"
        "\t}\n"
        "}\n"
    )
    assert _findings(script) == []


def test_meta_effect_template_is_skipped():
    script = (
        "meta_effect = {\n"
        "\ttext = { " + LOOP_CALL + " }\n"
        '\tTAG = "[ROOT.GetTag]"\n'
        "}\n"
    )
    assert _findings(script) == []


def test_nested_country_scope_inside_loop_is_flagged():
    script = "every_other_country = {\n" "\tSPR = { " + LOOP_CALL + " }\n" "}\n"
    assert len(_findings(script)) == 1


def test_for_each_loop_is_flagged():
    script = (
        "for_each_loop = {\n"
        "\tarray = influence_array\n"
        "\t" + LOOP_CALL + "\n"
        "}\n"
    )
    assert len(_findings(script)) == 1


def test_set_in_inner_loop_covers_outer():
    script = (
        "every_other_country = {\n"
        "\tevery_allied_country = {\n"
        "\t\tset_temp_variable = { influence_target = PREV }\n"
        "\t\t" + LOOP_CALL + "\n"
        "\t}\n"
        "}\n"
    )
    assert _findings(script) == []


def test_each_loop_is_checked_separately():
    script = (
        "every_other_country = {\n"
        "\tset_temp_variable = { influence_target = THIS }\n"
        "\t" + LOOP_CALL + "\n"
        "}\n"
        "every_neighbor_country = {\n"
        "\t" + LOOP_CALL + "\n"
        "}\n"
    )
    findings = _findings(script)
    assert len(findings) == 1
    assert "every_neighbor_country" in findings[0][1]


# --- wiring ----------------------------------------------------------------


def test_validator_reports_error_category(tmp_path):
    import json

    nf = tmp_path / "common" / "national_focus"
    nf.mkdir(parents=True)
    (nf / "test.txt").write_text(
        "focus = { completion_reward = { every_other_country = { "
        + LOOP_CALL
        + " } } }\n",
        encoding="utf-8",
    )
    v = V.Validator(mod_path=str(tmp_path), use_colors=False, workers=1)
    v.run_validations()
    assert v.errors_found == 1
    assert v.warnings_found == 0
    issues = json.loads(v.get_issues_json())
    assert issues[0]["category"] == "stale-influence-target"
    assert issues[0]["severity"] == "error"
    assert issues[0]["line"] == 1


def test_spain_focus_tree_is_clean():
    path = _MOD_ROOT / "common" / "national_focus" / "05_spain.txt"
    raw = path.read_text(encoding="utf-8")
    setter = "set_temp_variable = { influence_target = THIS }"
    assert raw.count(setter) == 6
    assert V.scan_file((str(path), str(_MOD_ROOT))) == []
    assert len(V.scan_text(raw.replace(setter, ""))) == 6


@pytest.mark.parametrize(
    "assignment, expected",
    [
        ("saved_target = influence_target", 1),
        ("var = saved_target value = influence_target", 1),
        ("var = influence_target value = THIS", 0),
        ("value = THIS var = influence_target", 0),
        ("influence_target_extra = THIS", 1),
    ],
)
def test_only_target_assignments_cover_calls(assignment, expected):
    script = (
        "every_country = { set_temp_variable = { "
        + assignment
        + " } "
        + LOOP_CALL
        + " }"
    )
    assert len(_findings(script)) == expected


@pytest.mark.parametrize("validator", [V, pytest.param(None, id="dynamic-modifier")])
def test_scan_file_missing_input_fails(tmp_path, validator):
    import validate_dynamic_modifier_guards

    scanner = validator or validate_dynamic_modifier_guards
    with pytest.raises(ValueError, match="Cannot scan"):
        scanner.scan_file((str(tmp_path / "missing.txt"), str(tmp_path)))


@pytest.mark.parametrize("wrapper", ["effect_tooltip", "limit", "if"])
def test_nested_set_does_not_cover_later_call(wrapper):
    script = (
        "every_country = { "
        + wrapper
        + " = { set_temp_variable = { influence_target = THIS } } "
        + LOOP_CALL
        + " }"
    )
    assert len(_findings(script)) == 1
