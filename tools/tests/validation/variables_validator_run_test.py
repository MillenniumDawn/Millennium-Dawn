"""Validator-level behaviour for validate_variables.

The pool workers are covered elsewhere; this file drives the reporting layer —
which findings reach `_issues`, with what file and line, and which are
deliberately suppressed (dynamic `@SCOPE` setters, localisation references to
an event target, staged mode's cross-file skip).
"""

import runpy
import sys

import pytest
import validate_variables as V


def _found(validator):
    return sorted(
        (issue.message, issue.file, issue.line) for issue in validator._issues
    )


def _validator(tmp_path, **kwargs):
    return V.Validator(str(tmp_path), use_colors=False, workers=1, **kwargs)


# --- flag reporting --------------------------------------------------------


def test_cleared_flag_without_a_setter_is_reported(tmp_path, write_path):
    write_path(
        tmp_path,
        "common/scripted_effects/flags.txt",
        "TST_demo = {\n\tclr_country_flag = TST_gone\n}\n",
    )
    validator = _validator(tmp_path)

    validator.validate_cleared_flags("country", [], {"TST_gone": "flags.txt"}, {})

    assert _found(validator) == [
        ("TST_gone", "common/scripted_effects/flags.txt", 2),
    ]


def test_cleared_flag_with_a_dynamic_setter_is_not_reported(tmp_path, write_path):
    """`accords_@ROOT_left` is set as `accords_MOR_left` at runtime."""
    write_path(
        tmp_path,
        "common/scripted_effects/flags.txt",
        "TST_demo = {\n\tclr_country_flag = accords_MOR_left\n}\n",
    )
    validator = _validator(tmp_path)

    validator.validate_cleared_flags(
        "country",
        [],
        {"accords_MOR_left": "flags.txt"},
        {"accords_@ROOT_left": "flags.txt"},
    )

    assert validator._issues == []


def test_cleared_flag_that_is_also_set_is_not_reported(tmp_path, write_path):
    write_path(
        tmp_path,
        "common/scripted_effects/flags.txt",
        "TST_demo = {\n\tset_country_flag = TST_paired\n\tclr_country_flag = TST_paired\n}\n",
    )
    validator = _validator(tmp_path)

    validator.validate_cleared_flags(
        "country",
        [],
        {"TST_paired": "flags.txt", "TST_nowhere": "nowhere.txt"},
        {"TST_paired": "flags.txt"},
    )

    assert validator._issues == []


def test_missing_flag_is_reported_with_its_read_site(tmp_path, write_path):
    write_path(
        tmp_path,
        "common/scripted_triggers/reads.txt",
        "TST_check = {\n\thas_country_flag = TST_never_set\n}\n",
    )
    validator = _validator(tmp_path)

    validator.validate_missing_flags("country", [], {"TST_never_set": "reads.txt"}, {})

    assert _found(validator) == [
        ("TST_never_set", "common/scripted_triggers/reads.txt", 2),
    ]


def test_read_flag_that_is_also_set_is_not_reported(tmp_path, write_path):
    write_path(
        tmp_path,
        "common/scripted_effects/flags.txt",
        "TST_demo = {\n\tset_country_flag = TST_paired\n\thas_country_flag = TST_paired\n}\n",
    )
    validator = _validator(tmp_path)

    validator.validate_missing_flags(
        "country",
        [],
        {"TST_paired": "flags.txt", "TST_nowhere": "nowhere.txt"},
        {"TST_paired": "flags.txt"},
    )

    assert validator._issues == []


def test_read_flag_matched_by_a_dynamic_setter_is_not_reported(tmp_path, write_path):
    write_path(
        tmp_path,
        "common/scripted_effects/flags.txt",
        "TST_demo = {\n\thas_country_flag = accords_MOR_left\n}\n",
    )
    validator = _validator(tmp_path)

    validator.validate_missing_flags(
        "country",
        [],
        {"accords_MOR_left": "flags.txt"},
        {"accords_@ROOT_left": "flags.txt"},
    )

    assert validator._issues == []


def test_unused_flag_is_reported_with_its_setter(tmp_path, write_path):
    write_path(
        tmp_path,
        "common/scripted_effects/flags.txt",
        "TST_demo = {\n\tset_country_flag = TST_never_read\n}\n",
    )
    validator = _validator(tmp_path)

    validator.validate_unused_flags("country", [], {"TST_never_read": "flags.txt"}, {})

    assert _found(validator) == [
        ("TST_never_read", "common/scripted_effects/flags.txt", 2),
    ]


def test_unused_flag_matched_by_a_dynamic_reader_is_not_reported(tmp_path, write_path):
    write_path(
        tmp_path,
        "common/scripted_effects/flags.txt",
        "TST_demo = {\n\tset_country_flag = accords_MOR_left\n}\n",
    )
    validator = _validator(tmp_path)

    validator.validate_unused_flags(
        "country",
        [],
        {"accords_MOR_left": "flags.txt"},
        {"accords_@ROOT_left": "flags.txt"},
    )

    assert validator._issues == []


def test_unused_flag_with_no_locatable_source_file_is_skipped(tmp_path):
    validator = _validator(tmp_path)

    validator.validate_unused_flags("country", [], {"TST_x": "nowhere.txt"}, {})

    assert validator._issues == []


def test_flag_syntax_issues_are_reported(tmp_path, write_path):
    write_path(
        tmp_path,
        "common/scripted_effects/syntax.txt",
        "TST_demo = {\n"
        "\tset_country_flag = { flag = TST_timed days = 30 }\n"
        "\tset_global_flag = { flag = TST_long }\n"
        "}\n",
    )
    validator = _validator(tmp_path)

    validator.validate_flag_syntax()

    messages = [issue.message for issue in validator._issues]
    assert len(messages) == 2
    assert any("missing value field" in m for m in messages)
    assert any("use shorthand" in m for m in messages)


# --- event target reporting ------------------------------------------------


def test_cleared_event_target_without_a_setter_is_reported(tmp_path, write_path):
    write_path(
        tmp_path,
        "events/ev.txt",
        "TST_demo = {\n\tclear_global_event_target = TST_stale\n}\n",
    )
    validator = _validator(tmp_path)

    validator.validate_cleared_event_targets({"TST_stale": "ev.txt"}, {})

    assert _found(validator) == [("TST_stale", "events/ev.txt", 2)]


def test_cleared_event_target_that_is_set_is_not_reported(tmp_path, write_path):
    write_path(
        tmp_path,
        "events/ev.txt",
        "TST_demo = {\n"
        "\tsave_global_event_target_as = TST_paired\n"
        "\tclear_global_event_target = TST_paired\n"
        "}\n",
    )
    validator = _validator(tmp_path)

    validator.validate_cleared_event_targets(
        {"TST_paired": "ev.txt", "TST_nowhere": "nowhere.txt"},
        {"TST_paired": "ev.txt"},
    )

    assert validator._issues == []


def test_missing_event_target_located_by_its_scope_reference(tmp_path, write_path):
    write_path(
        tmp_path,
        "events/ev.txt",
        "TST_demo = {\n"
        "\tsave_event_target_as = TST_paired\n"
        "\tevent_target:TST_used = { add_stability = 0.05 }\n"
        "}\n",
    )
    validator = _validator(tmp_path)

    validator.validate_missing_event_targets(
        {
            "TST_used": "ev.txt",
            "TST_paired": "ev.txt",
            "TST_nowhere": "nowhere.txt",
        },
        {"TST_paired": "ev.txt"},
    )

    assert _found(validator) == [("TST_used", "events/ev.txt", 3)]


def test_missing_event_target_falls_back_to_the_has_form(tmp_path, write_path):
    """`has_event_target = X` has no `event_target:X` text to locate."""
    write_path(
        tmp_path,
        "events/ev.txt",
        "TST_demo = {\n\tif = { limit = { has_event_target = TST_missing } }\n}\n",
    )
    validator = _validator(tmp_path)

    validator.validate_missing_event_targets({"TST_missing": "ev.txt"}, {})

    assert _found(validator) == [("TST_missing", "events/ev.txt", 2)]


def test_unused_event_targets_reported_unless_localisation_reads_them(
    tmp_path, write_path
):
    write_path(
        tmp_path,
        "events/ev.txt",
        "TST_demo = {\n"
        "\tsave_event_target_as = TST_unused\n"
        "\tsave_global_event_target_as = TST_global_unused\n"
        "\tsave_global_event_target_as = TST_shown\n"
        "}\n",
    )
    write_path(
        tmp_path,
        "localisation/english/tst_l_english.yml",
        'l_english:\n TST_key:0 "[TST_shown.GetName] arrives"\n',
    )
    validator = _validator(tmp_path)

    validator.validate_unused_event_targets(
        {
            "TST_unused": "ev.txt",
            "TST_global_unused": "ev.txt",
            "TST_shown": "ev.txt",
        },
        {},
    )

    assert _found(validator) == [
        ("TST_global_unused", "events/ev.txt", 3),
        ("TST_unused", "events/ev.txt", 2),
    ]


def test_used_event_target_and_unlocatable_one_are_not_reported(tmp_path, write_path):
    write_path(
        tmp_path,
        "events/ev.txt",
        "TST_demo = {\n\tsave_event_target_as = TST_paired\n}\n",
    )
    validator = _validator(tmp_path)

    validator.validate_unused_event_targets(
        {"TST_paired": "ev.txt", "TST_nowhere": "nowhere.txt"},
        {"TST_paired": "ev.txt"},
    )

    assert validator._issues == []


def test_staged_mode_only_scans_staged_localisation(tmp_path, write_path):
    """An unstaged .yml is not read, so its reference cannot clear the target."""
    events = write_path(
        tmp_path,
        "events/ev.txt",
        "TST_demo = {\n\tsave_global_event_target_as = TST_shown\n}\n",
    )
    write_path(
        tmp_path,
        "localisation/english/tst_l_english.yml",
        'l_english:\n TST_key:0 "[TST_shown.GetName] arrives"\n',
    )
    validator = _validator(tmp_path)
    validator.staged_files = [str(events)]

    validator.validate_unused_event_targets({"TST_shown": "ev.txt"}, {})

    assert _found(validator) == [("TST_shown", "events/ev.txt", 2)]


# --- warning-severity checks -----------------------------------------------


def test_treasury_effect_in_state_scope_is_reported(tmp_path, write_path):
    write_path(
        tmp_path,
        "common/national_focus/focus.txt",
        "TST_focus = {\n"
        "\tcompletion_reward = {\n"
        "\t\trandom_owned_state = {\n"
        "\t\t\tmodify_treasury_effect = yes\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    validator = _validator(tmp_path)

    validator.validate_treasury_state_scope()

    assert len(validator._issues) == 1
    issue = validator._issues[0]
    assert issue.category == "treasury-state-scope"
    assert issue.severity == "warning"
    assert (issue.file, issue.line) == ("common/national_focus/focus.txt", 4)


def test_clamp_ranges_from_several_files_widen_before_comparison(tmp_path, write_path):
    write_path(
        tmp_path,
        "common/scripted_effects/a.txt",
        "TST_a = {\n"
        "\tset_variable = { TST_strength = 25 }\n"
        "\tclamp_variable = { var = TST_strength min = 0 max = 50 }\n"
        "}\n",
    )
    write_path(
        tmp_path,
        "common/scripted_effects/b.txt",
        "TST_b = {\n\tclamp_variable = { var = TST_strength min = 10 max = 100 }\n}\n",
    )
    write_path(
        tmp_path,
        "events/ev.txt",
        "TST_demo = {\n\tcheck_variable = { TST_strength > 200 }\n}\n",
    )
    validator = _validator(tmp_path)

    validator.validate_clamp_range_conflicts()

    messages = [issue.message for issue in validator._issues]
    assert len(messages) == 1
    assert "clamped to 0.0..100.0" in messages[0]
    assert "never change outcome" in messages[0]


def test_in_range_check_against_a_widened_clamp_is_clean(tmp_path, write_path):
    write_path(
        tmp_path,
        "common/scripted_effects/a.txt",
        "TST_a = {\n"
        "\tset_variable = { TST_strength = 25 }\n"
        "\tclamp_variable = { var = TST_strength min = 0 max = 50 }\n"
        "}\n",
    )
    write_path(
        tmp_path,
        "common/scripted_effects/b.txt",
        "TST_b = {\n\tclamp_variable = { var = TST_strength min = 10 max = 100 }\n}\n",
    )
    write_path(
        tmp_path,
        "events/ev.txt",
        "TST_demo = {\n\tcheck_variable = { TST_strength > 75 }\n}\n",
    )
    validator = _validator(tmp_path)

    validator.validate_clamp_range_conflicts()

    assert validator._issues == []


def test_untooltipped_check_variable_in_available_is_reported(tmp_path, write_path):
    write_path(
        tmp_path,
        "common/decisions/dec.txt",
        "TST_category = {\n"
        "\tTST_decision = {\n"
        "\t\tavailable = {\n"
        "\t\t\tcheck_variable = { TST_var > 5 }\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    validator = _validator(tmp_path)

    validator.validate_untooltipped_available_checks()

    assert len(validator._issues) == 1
    issue = validator._issues[0]
    assert issue.category == "untooltipped-available-check"
    assert (issue.file, issue.line) == ("common/decisions/dec.txt", 4)
    assert issue.severity == V.Severity.ERROR


def test_repeated_unlocalised_flag_in_one_file_is_reported_once(tmp_path, write_path):
    write_path(
        tmp_path,
        "common/decisions/dec.txt",
        "TST_category = {\n"
        "\tTST_first = {\n"
        "\t\tavailable = { has_country_flag = TST_no_loc }\n"
        "\t}\n"
        "\tTST_second = {\n"
        "\t\tavailable = { has_country_flag = TST_no_loc }\n"
        "\t}\n"
        "}\n",
    )
    validator = _validator(tmp_path)

    validator.validate_unlocalised_available_flags()

    assert len(validator._issues) == 1
    assert validator._issues[0].line == 3


def test_scripted_trigger_index_survives_an_unreadable_definition_file(
    tmp_path, write_path
):
    (tmp_path / "common" / "scripted_triggers" / "broken.txt").mkdir(parents=True)
    write_path(
        tmp_path,
        "common/scripted_triggers/border.txt",
        "TST_border_available = {\n\thas_global_flag = TST_border_open\n}\n",
    )
    validator = _validator(tmp_path)

    assert validator._collect_scripted_trigger_flag_names() == frozenset(
        {"TST_border_available"}
    )


def test_scripted_trigger_check_needs_player_facing_files(tmp_path, write_path):
    write_path(
        tmp_path,
        "common/scripted_triggers/border.txt",
        "TST_border_available = {\n\thas_global_flag = TST_border_open\n}\n",
    )
    validator = _validator(tmp_path)

    validator.validate_untooltipped_available_scripted_trigger()

    assert validator._issues == []


def test_bare_scripted_trigger_call_in_available_is_reported(tmp_path, write_path):
    write_path(
        tmp_path,
        "common/scripted_triggers/border.txt",
        "TST_border_available = {\n\thas_global_flag = TST_border_open\n}\n",
    )
    write_path(
        tmp_path,
        "common/decisions/dec.txt",
        "TST_category = {\n"
        "\tTST_decision = {\n"
        "\t\tavailable = {\n"
        "\t\t\tTST_border_available = yes\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )
    validator = _validator(tmp_path)

    validator.validate_untooltipped_available_scripted_trigger()

    assert len(validator._issues) == 1
    issue = validator._issues[0]
    assert issue.category == "untooltipped-available-scripted-trigger"
    assert (issue.file, issue.line) == ("common/decisions/dec.txt", 4)


def test_repeat_lookups_reuse_the_memoized_index(tmp_path, write_path):
    """Each index is harvested repo-wide; recomputing it per check is wasted work."""
    write_path(
        tmp_path,
        "common/scripted_triggers/border.txt",
        "TST_border_available = {\n\thas_global_flag = TST_border_open\n}\n",
    )
    write_path(
        tmp_path,
        "common/dynamic_modifiers/dyn.txt",
        "TST_modifier = {\n\tpolitical_power_factor = TST_pp\n}\n",
    )
    validator = _validator(tmp_path)

    assert validator._get_ai_only_categories() is validator._get_ai_only_categories()
    assert (
        validator._collect_scripted_trigger_flag_names()
        is validator._collect_scripted_trigger_flag_names()
    )
    assert (
        validator._collect_dynamic_modifier_vars()
        is validator._collect_dynamic_modifier_vars()
    )


# --- whole-run wiring ------------------------------------------------------


def test_staged_mode_skips_the_cross_file_checks(tmp_path, write_path):
    write_path(
        tmp_path,
        "common/scripted_effects/flags.txt",
        "TST_demo = {\n\tclr_country_flag = TST_gone\n}\n",
    )
    validator = _validator(tmp_path, staged_only=True)

    validator.run_validations()

    assert validator._issues == []


def test_full_run_reports_the_flag_lifecycle(tmp_path, write_path):
    write_path(
        tmp_path,
        "common/scripted_effects/flags.txt",
        "TST_demo = {\n"
        "\tset_country_flag = TST_never_read\n"
        "\tclr_country_flag = TST_never_set\n"
        "\thas_country_flag = TST_read_only\n"
        "\tset_global_flag = GLOBAL_paired\n"
        "\thas_global_flag = GLOBAL_paired\n"
        "\tset_state_flag = TST_state_paired\n"
        "\thas_state_flag = TST_state_paired\n"
        "}\n",
    )
    validator = _validator(tmp_path)

    validator.run_validations()

    assert _found(validator) == [
        ("TST_never_read", "common/scripted_effects/flags.txt", 2),
        ("TST_never_set", "common/scripted_effects/flags.txt", 3),
        ("TST_read_only", "common/scripted_effects/flags.txt", 4),
    ]


def test_cli_entry_point_exits_zero_on_a_clean_tree(tmp_path, monkeypatch, write_path):
    write_path(
        tmp_path,
        "common/scripted_effects/flags.txt",
        "TST_demo = {\n"
        "\tset_country_flag = TST_paired\n"
        "\thas_country_flag = TST_paired\n"
        "}\n",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [V.__file__, "--path", str(tmp_path), "--workers", "1", "--no-color"],
    )

    with pytest.raises(SystemExit) as exit_info:
        runpy.run_path(V.__file__, run_name="__main__")

    assert exit_info.value.code == 0
