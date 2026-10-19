"""Tests for validate_variables.py."""

import argparse
import os
import re
import runpy
import sys

import pytest
import validate_variables as V
import validator_common
from shared.suite import checks_called_by_run, variable_scan
from shared.suite import issue_rows as _issue_rows
from shared.suite import write_under as _write

_SHARED_CHECKS = (
    "validate_clamp_range_conflicts",
    "validate_math_precision",
    "validate_missing_variable_tooltips",
    "validate_negated_trigger_tooltips",
    "validate_treasury_state_scope",
    "validate_unlocalised_available_flags",
    "validate_unregistered_dynamic_tokens",
    "validate_untooltipped_available_checks",
    "validate_untooltipped_available_scripted_trigger",
    "validate_variable_tooltip_keys",
)


def _validator(tmp_path, **kwargs):
    return V.Validator(str(tmp_path), use_colors=False, workers=1, **kwargs)


def _found(validator):
    return sorted(
        (issue.message, issue.file, issue.line) for issue in validator._issues
    )


@pytest.mark.parametrize(
    "redundant, staged",
    [(True, False), (False, False), (True, True)],
    ids=["full run", "redundant flags off", "staged run"],
)
def test_run_validations_calls_every_check(tmp_path, monkeypatch, redundant, staged):
    validator = _validator(
        tmp_path, redundant_focus_flags=redundant, staged_only=staged
    )
    called, checks = checks_called_by_run(validator, monkeypatch)

    if staged:
        expected = list(_SHARED_CHECKS)
    else:
        expected = [
            check
            for check in checks
            if redundant or check != "validate_redundant_focus_flags"
        ]
    assert sorted(set(called)) == expected


def test_staged_run_with_nothing_in_scope_reports_nothing(tmp_path):
    _write(tmp_path, _FLAGS, _flag_demo("clr_country_flag = TST_gone"))
    validator = _validator(tmp_path, staged_only=True)

    validator.run_validations()

    assert validator._issues == []


def test_cli_exposes_the_redundant_focus_flag():
    parser = argparse.ArgumentParser()
    V._add_extra_args(parser)

    assert parser.parse_args(["--redundant-focus-flags"]).redundant_focus_flags
    assert not parser.parse_args([]).redundant_focus_flags


def test_cli_entry_point_exits_zero_on_a_clean_tree(tmp_path, monkeypatch):
    _write(
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


# --- flag scanning and reporting --------------------------------------------

_FLAGS = "common/scripted_effects/flags.txt"


def test_flag_scan_collects_set_used_and_cleared(tmp_path):
    path = _write(
        tmp_path,
        _FLAGS,
        "flag_demo = {\n"
        "\tset_country_flag = TST_set_flag\n"
        "\thas_country_flag = TST_read_flag\n"
        "\tclr_country_flag = TST_cleared_flag\n"
        "}\n",
    )

    set_paths, used_paths, cleared_paths = V.process_file_for_all_flags(
        (str(path), False, "country", str(tmp_path))
    )

    assert set(set_paths) == {"TST_set_flag"}
    assert set(used_paths) == {"TST_read_flag"}
    assert set(cleared_paths) == {"TST_cleared_flag"}


@pytest.mark.parametrize(
    "rel, worker",
    [
        (
            "common/scripted_effects/empty.txt",
            lambda f, m: V.process_file_for_all_flags((f, False, "country", m)),
        ),
        (
            "events/empty.txt",
            lambda f, m: V.process_file_for_all_targets((f, False, m)),
        ),
    ],
    ids=["flags", "event targets"],
)
def test_scan_returns_nothing_for_an_empty_file(tmp_path, rel, worker):
    assert worker(str(_write(tmp_path, rel, "")), str(tmp_path)) == ({}, {}, {})


def test_flag_pass_scans_only_the_supported_flag_types(tmp_path):
    path = _write(
        tmp_path, _FLAGS, "set_country_flag = TST_c\nset_character_flag = TST_ch\n"
    )

    flags, _targets = V.process_file_for_flags_and_targets((str(path), str(tmp_path)))

    assert list(flags) == ["country", "global", "state"]


def _flag_fixture(tmp_path):
    for name, flag in (("a", "TST_one"), ("b", "TST_two")):
        _write(
            tmp_path,
            f"common/scripted_effects/{name}.txt",
            f"set_country_flag = {flag}\nhas_global_flag = {flag}_g\n"
            f"clr_state_flag = {flag}_s\nsave_event_target_as = {flag}_t\n",
        )


def test_flags_and_targets_worker_matches_the_separate_workers(tmp_path):
    _flag_fixture(tmp_path)
    path = str(tmp_path / "common" / "scripted_effects" / "a.txt")
    mod = str(tmp_path)

    flags, targets = V.process_file_for_flags_and_targets((path, mod))

    assert flags == {
        flag_type: V.process_file_for_all_flags((path, False, flag_type, mod))
        for flag_type in ("country", "global", "state")
    }
    assert targets == V.process_file_for_all_targets((path, False, mod))
    assert set(flags["global"][1]) == {"TST_one_g"}


def test_dynamic_flag_matcher_only_expands_scope_substitutions():
    patterns = V.Validator._build_dynamic_flag_matchers(
        ["accords_@ROOT_left", "trade_agreement@USA", "plain_flag"]
    )

    assert len(patterns) == 1
    assert patterns[0].match("accords_MOR_left")
    assert patterns[0].match("accords_MOR_CW_0_left")
    assert not patterns[0].match("accords_lowercase_left")


def _flag_demo(*lines):
    return "TST_demo = {\n" + "".join(f"\t{line}\n" for line in lines) + "}\n"


_DYNAMIC = {"accords_@ROOT_left": "flags.txt"}

# case: (check, flags.txt or None, the paths it reports from, the paths that
#        clear them, (flag, line) per finding)
_FLAG_REPORT_CASES = {
    "cleared flag without a setter": (
        "validate_cleared_flags",
        _flag_demo("clr_country_flag = TST_gone"),
        {"TST_gone": "flags.txt"},
        {},
        [("TST_gone", 2)],
    ),
    # `accords_@ROOT_left` is set as `accords_MOR_left` at runtime.
    "cleared flag with a dynamic setter": (
        "validate_cleared_flags",
        _flag_demo("clr_country_flag = accords_MOR_left"),
        {"accords_MOR_left": "flags.txt"},
        _DYNAMIC,
        [],
    ),
    "cleared flag that is also set": (
        "validate_cleared_flags",
        _flag_demo("set_country_flag = TST_paired", "clr_country_flag = TST_paired"),
        {"TST_paired": "flags.txt", "TST_nowhere": "nowhere.txt"},
        {"TST_paired": "flags.txt"},
        [],
    ),
    "read flag without a setter": (
        "validate_missing_flags",
        _flag_demo("has_country_flag = TST_never_set"),
        {"TST_never_set": "flags.txt"},
        {},
        [("TST_never_set", 2)],
    ),
    "read flag that is also set": (
        "validate_missing_flags",
        _flag_demo("set_country_flag = TST_paired", "has_country_flag = TST_paired"),
        {"TST_paired": "flags.txt", "TST_nowhere": "nowhere.txt"},
        {"TST_paired": "flags.txt"},
        [],
    ),
    "read flag with a dynamic setter": (
        "validate_missing_flags",
        _flag_demo("has_country_flag = accords_MOR_left"),
        {"accords_MOR_left": "flags.txt"},
        _DYNAMIC,
        [],
    ),
    "set flag never read": (
        "validate_unused_flags",
        _flag_demo("set_country_flag = TST_never_read"),
        {"TST_never_read": "flags.txt"},
        {},
        [("TST_never_read", 2)],
    ),
    "set flag with a dynamic reader": (
        "validate_unused_flags",
        _flag_demo("set_country_flag = accords_MOR_left"),
        {"accords_MOR_left": "flags.txt"},
        _DYNAMIC,
        [],
    ),
    "set flag with no locatable file": (
        "validate_unused_flags",
        None,
        {"TST_x": "nowhere.txt"},
        {},
        [],
    ),
}


@pytest.mark.parametrize(
    "check, content, reported, matched, expected",
    _FLAG_REPORT_CASES.values(),
    ids=_FLAG_REPORT_CASES,
)
def test_flag_reports(tmp_path, check, content, reported, matched, expected):
    if content is not None:
        _write(tmp_path, _FLAGS, content)
    validator = _validator(tmp_path)

    getattr(validator, check)("country", [], reported, matched)

    assert _found(validator) == [(flag, _FLAGS, line) for flag, line in expected]


def test_full_run_reports_the_flag_lifecycle(tmp_path):
    _write(
        tmp_path,
        _FLAGS,
        _flag_demo(
            "set_country_flag = TST_never_read",
            "clr_country_flag = TST_never_set",
            "has_country_flag = TST_read_only",
            "set_global_flag = GLOBAL_paired",
            "has_global_flag = GLOBAL_paired",
            "set_state_flag = TST_state_paired",
            "has_state_flag = TST_state_paired",
        ),
    )
    validator = _validator(tmp_path)

    validator.run_validations()

    assert _found(validator) == [
        ("TST_never_read", _FLAGS, 2),
        ("TST_never_set", _FLAGS, 3),
        ("TST_read_only", _FLAGS, 4),
    ]


def test_flag_syntax_scan_reports_days_without_value_and_long_form(tmp_path):
    path = _write(
        tmp_path,
        "common/scripted_effects/syntax.txt",
        _flag_demo(
            "set_country_flag = { flag = TST_timed days = 30 }",
            "set_global_flag = { flag = TST_long_form }",
        ),
    )

    days, long_form = variable_scan(path, "flag_syntax", tmp_path)

    relative = os.path.join("common", "scripted_effects", "syntax.txt")
    assert len(days) == 1 and "missing value field" in days[0]
    assert days[0].startswith(f"{relative}:2")
    assert len(long_form) == 1 and "use shorthand" in long_form[0]
    assert long_form[0].startswith(f"{relative}:3")


def test_flag_syntax_accepts_days_with_value(tmp_path):
    path = _write(
        tmp_path,
        "common/scripted_effects/ok.txt",
        "set_country_flag = { flag = TST_timed days = 30 value = 1 }\n",
    )
    assert variable_scan(path, "flag_syntax", tmp_path) == ([], [])


def test_flag_syntax_issues_are_reported(tmp_path):
    _write(
        tmp_path,
        "common/scripted_effects/syntax.txt",
        _flag_demo(
            "set_country_flag = { flag = TST_timed days = 30 }",
            "set_global_flag = { flag = TST_long }",
        ),
    )
    validator = _validator(tmp_path)

    validator.validate_flag_syntax()

    messages = [issue.message for issue in validator._issues]
    assert len(messages) == 2
    assert any("missing value field" in m for m in messages)
    assert any("use shorthand" in m for m in messages)


_CANAL_EFFECT = (
    "canal_block_effect = {\n"
    "\tif = {\n"
    "\t\tlimit = { has_war_with = TUR }\n"
    "\t\tset_global_flag = TEST_CANAL_BLOCKED\n"
    "\t}\n"
    "\telse = { clr_global_flag = TEST_CANAL_BLOCKED }\n"
    "}\n"
)
_CANAL_RULE = (
    "adjacency_rule = {\n"
    '\tname = "TEST_STRAIT"\n'
    "\tis_disabled = {\n"
    "\t\thas_global_flag = TEST_CANAL_BLOCKED\n"
    "\t\ttooltip = test_blocked_tt\n"
    "\t}\n"
    "}\n"
)


@pytest.mark.parametrize(
    "with_map, expected",
    [
        (True, []),
        (False, [("TEST_CANAL_BLOCKED", "common/scripted_effects/00_test.txt", 4)]),
    ],
    ids=["read in map/adjacency_rules.txt", "never read"],
)
def test_flag_read_only_in_adjacency_rules_counts_as_used(tmp_path, with_map, expected):
    _write(tmp_path, "common/scripted_effects/00_test.txt", _CANAL_EFFECT)
    if with_map:
        _write(tmp_path, "map/adjacency_rules.txt", _CANAL_RULE)
    validator = _validator(tmp_path)

    validator.run_validations()

    assert [
        (issue.message, issue.file, issue.line)
        for issue in validator._issues
        if issue.category == "variables"
    ] == expected


# --- event targets ----------------------------------------------------------

_EVENTS = "events/ev.txt"


def test_event_target_scan_collects_set_used_and_cleared(tmp_path):
    path = _write(
        tmp_path,
        _EVENTS,
        "country_event = {\n"
        "\tid = tst.1\n"
        "\toption = {\n"
        "\t\tname = tst.1.a\n"
        "\t\tsave_event_target_as = TST_local\n"
        "\t\tsave_global_event_target_as = TST_global\n"
        "\t\tclear_global_event_target = TST_stale\n"
        "\t\tif = { limit = { has_event_target = TST_checked } }\n"
        "\t\tevent_target:TST_used = { add_stability = 0.05 }\n"
        "\t}\n"
        "}\n",
    )

    set_paths, used_paths, cleared_paths = V.process_file_for_all_targets(
        (str(path), False, str(tmp_path))
    )

    assert set(set_paths) == {"TST_local", "TST_global"}
    assert set(used_paths) == {"TST_checked", "TST_used"}
    assert set(cleared_paths) == {"TST_stale"}


@pytest.mark.parametrize(
    "body, used",
    [
        (
            "TST_alias = {\n\tglobal_event_target = TST_alias_target\n}\n",
            {"TST_alias_target"},
        ),
        ("TST_alias = {\n\toriginal_tag = YEM\n}\n", set()),
    ],
    ids=["global event target", "no global event target"],
)
def test_tag_alias_file_only_contributes_global_event_target_reads(
    tmp_path, body, used
):
    path = _write(tmp_path, "common/country_tag_aliases/00_tag_aliases.txt", body)

    set_paths, used_paths, cleared_paths = V.process_file_for_all_targets(
        (str(path), False, str(tmp_path))
    )

    assert (set_paths, set(used_paths), cleared_paths) == ({}, used, {})


_TST_SHOWN_LOC = 'l_english:\n TST_key:0 "[TST_shown.GetName] arrives"\n'

# case: (check, ev.txt, localisation or None, the targets it reports from, the
#        targets that clear them, (target, line) per finding)
_TARGET_REPORT_CASES = {
    "cleared target without a setter": (
        "validate_cleared_event_targets",
        _flag_demo("clear_global_event_target = TST_stale"),
        None,
        {"TST_stale": "ev.txt"},
        {},
        [("TST_stale", 2)],
    ),
    "cleared target that is set": (
        "validate_cleared_event_targets",
        _flag_demo(
            "save_global_event_target_as = TST_paired",
            "clear_global_event_target = TST_paired",
        ),
        None,
        {"TST_paired": "ev.txt", "TST_nowhere": "nowhere.txt"},
        {"TST_paired": "ev.txt"},
        [],
    ),
    "missing target located by its scope reference": (
        "validate_missing_event_targets",
        _flag_demo(
            "save_event_target_as = TST_paired",
            "event_target:TST_used = { add_stability = 0.05 }",
        ),
        None,
        {"TST_used": "ev.txt", "TST_paired": "ev.txt", "TST_nowhere": "nowhere.txt"},
        {"TST_paired": "ev.txt"},
        [("TST_used", 3)],
    ),
    # `has_event_target = X` has no `event_target:X` text to locate.
    "missing target located by its has form": (
        "validate_missing_event_targets",
        _flag_demo("if = { limit = { has_event_target = TST_missing } }"),
        None,
        {"TST_missing": "ev.txt"},
        {},
        [("TST_missing", 2)],
    ),
    "unused targets unless localisation reads them": (
        "validate_unused_event_targets",
        _flag_demo(
            "save_event_target_as = TST_unused",
            "save_global_event_target_as = TST_global_unused",
            "save_global_event_target_as = TST_shown",
        ),
        _TST_SHOWN_LOC,
        {"TST_unused": "ev.txt", "TST_global_unused": "ev.txt", "TST_shown": "ev.txt"},
        {},
        [("TST_global_unused", 3), ("TST_unused", 2)],
    ),
    "used target and an unlocatable one": (
        "validate_unused_event_targets",
        _flag_demo("save_event_target_as = TST_paired"),
        None,
        {"TST_paired": "ev.txt", "TST_nowhere": "nowhere.txt"},
        {"TST_paired": "ev.txt"},
        [],
    ),
}


@pytest.mark.parametrize(
    "check, events, loc, reported, matched, expected",
    _TARGET_REPORT_CASES.values(),
    ids=_TARGET_REPORT_CASES,
)
def test_event_target_reports(
    tmp_path, check, events, loc, reported, matched, expected
):
    _write(tmp_path, _EVENTS, events)
    if loc is not None:
        _write(tmp_path, "localisation/english/tst_l_english.yml", loc)
    validator = _validator(tmp_path)

    getattr(validator, check)(reported, matched)

    assert _found(validator) == [(target, _EVENTS, line) for target, line in expected]


def test_staged_mode_only_scans_staged_localisation(tmp_path):
    """An unstaged .yml is not read, so its reference cannot clear the target."""
    events = _write(
        tmp_path, _EVENTS, _flag_demo("save_global_event_target_as = TST_shown")
    )
    _write(tmp_path, "localisation/english/tst_l_english.yml", _TST_SHOWN_LOC)
    validator = _validator(tmp_path)
    validator.staged_files = [str(events)]

    validator.validate_unused_event_targets({"TST_shown": "ev.txt"}, {})

    assert _found(validator) == [("TST_shown", _EVENTS, 2)]


def test_full_run_collects_event_targets_from_txt_files(tmp_path):
    _write(tmp_path, _EVENTS, "save_event_target_as = TST_staged\n")
    _write(tmp_path, "localisation/english/a_l_english.yml", "l_english:\n")
    validator = _validator(tmp_path)

    validator.run_validations()

    assert _found(validator) == [("TST_staged", _EVENTS, 1)]


_LOC = "localisation/english/tst_l_english.yml"


@pytest.mark.parametrize(
    "value, targets, found",
    [
        (
            'l_english:\n TST_key:0 "[TST_shown.GetName] speaks"\n',
            ("TST_shown", "TST_hidden"),
            {"TST_shown"},
        ),
        ('l_english:\n TST_key:0 "plain text"\n', ("TST_shown",), set()),
        (
            "l_english:\n"
            ' a:0 "[TST_A.GetName] [event_target:TST_B.GetAdjective]"\n'
            ' b:0 "[TST_C.GetAdjective] [Event_Target:tst_d.getname]"\n'
            ' # c:0 "[TST_E.GetName]"\n',
            ("TST_A", "TST_B", "TST_C", "TST_D", "TST_E", "TST_F"),
            {"TST_A", "TST_B", "TST_C", "TST_D"},
        ),
    ],
    ids=["getter reference", "no getter", "every reference form outside comments"],
)
def test_localisation_target_scan(tmp_path, value, targets, found):
    path = _write(tmp_path, _LOC, value)
    assert V._scan_targets_in_loc((str(path), targets)) == found


# --- treasury scope ---------------------------------------------------------


@pytest.mark.parametrize(
    "token,parent,expected",
    [
        ("123", "", "STATE"),
        ("0.5", "random_list", "INHERIT"),
        ("random_owned_state", "", "STATE"),
        ("every_coastal_state", "", "STATE"),
        ("owner", "", "NONSTATE"),
        ("ROOT.CAPITAL", "", "NONSTATE"),
        ("random_country", "", "NONSTATE"),
        ("USA", "", "NONSTATE"),
        ("if", "", "INHERIT"),
    ],
)
def test_scope_token_classification(token, parent, expected):
    assert V._classify_scope_token(token, parent) == expected


@pytest.mark.parametrize(
    "body",
    [
        "my_focus = {\n\tcompletion_reward = {\n\t\tadd_stability = 0.05\n\t}\n}\n",
        "}\nmodify_treasury_effect = yes\n",
    ],
    ids=["no money effect", "stray close brace"],
)
def test_treasury_scan_finds_nothing(tmp_path, body):
    path = _write(tmp_path, "common/national_focus/focus.txt", body)
    assert variable_scan(path, "treasury", tmp_path) == []


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_treasury_scan_reports_the_first_and_last_line(tmp_path, newline):
    lines = [
        "random_owned_state = { modify_treasury_effect = yes }",
        "TAG = { every_state = { owner = { modify_treasury_effect = yes } } }",
        "every_state = {",
        "modify_treasury_effect = yes }",
    ]
    path = _write(tmp_path, _EVENTS, newline.join(lines))

    issues = variable_scan(path, "treasury", tmp_path)

    assert [
        (line, "random_owned_state" in message) for message, _rel, line in issues
    ] == [
        (1, True),
        (4, False),
    ]


def test_treasury_effect_in_state_scope_is_reported(tmp_path):
    _write(
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

    assert [(i.category, i.severity, i.file, i.line) for i in validator._issues] == [
        ("treasury-state-scope", "warning", "common/national_focus/focus.txt", 4)
    ]


# --- clamp ranges -----------------------------------------------------------


def _clamp_harvest(tmp_path, text):
    path = _write(tmp_path, "common/scripted_effects/clamp.txt", text)
    return V.collect_clamp_ranges((str(path), str(tmp_path)))


@pytest.mark.parametrize(
    "text, found",
    [
        pytest.param(
            "clamp_variable = { var = TST_partial min = 0 }\n"
            "clamp_variable = { var = TST_full min = 0 max = 100 }\n",
            [("TST_full", 0.0, 100.0)],
            id="a clamp without a max is not a range",
        ),
        pytest.param(
            "clamp_variable = { var = global.some_var min = 0 max = 50 }\n",
            [("some_var", 0.0, 50.0)],
            id="the global prefix is dropped",
        ),
    ],
)
def test_collected_clamp_ranges(tmp_path, text, found):
    assert _clamp_harvest(tmp_path, text)[0] == found


def test_clamp_harvest_separates_temp_and_persistent_writes(tmp_path):
    _found, temp, persistent = _clamp_harvest(
        tmp_path,
        "set_temp_variable = { pp_gain = political_power_daily }\n"
        "set_variable = { var = expected_military_sp value = 2 }\n"
        "set_global_variable = { GLOBAL_war_count = 0 }\n",
    )

    assert temp == ["pp_gain"]
    assert set(persistent) == {"expected_military_sp", "GLOBAL_war_count"}


@pytest.mark.parametrize(
    "text, ranges, fragment",
    [
        pytest.param(
            "check_variable = { my_var < 0.6 }",
            {"my_var": (0.8, 50.0)},
            "never change outcome",
            id="value below the minimum",
        ),
        pytest.param(
            "check_variable = { taliban_strength > 0.19 }",
            {"taliban_strength": (0.0, 100.0)},
            "0-1 scale value",
            id="0-1 scale value on a wide clamp",
        ),
        pytest.param(
            "check_variable = { var = my_var value = 200 compare = greater_than }",
            {"my_var": (0.0, 100.0)},
            "never change outcome",
            id="long form",
        ),
        pytest.param(
            "check_variable = { taliban_attack_strength > 0.19 }",
            {"taliban_attack_strength": (0.0, 1.0)},
            None,
            id="fraction on a 0..1 clamp",
        ),
        pytest.param(
            "check_variable = { unknown_var > 9999 }", {}, None, id="unclamped variable"
        ),
    ],
)
def test_clamp_conflicts(tmp_path, text, ranges, fragment):
    path = _write(tmp_path, "use.txt", text)

    out = V._resolve_clamp_checks(
        variable_scan(path, "clamp_checks", tmp_path), "use.txt", ranges
    )

    if fragment is None:
        assert out == []
    else:
        assert len(out) == 1 and fragment in out[0]


@pytest.mark.parametrize(
    "threshold, messages",
    [
        (
            200,
            [("clamped to 0.0..100.0", "never change outcome")],
        ),
        (75, []),
    ],
    ids=["check past the widened clamp", "check inside the widened clamp"],
)
def test_clamp_ranges_from_several_files_widen_before_comparison(
    tmp_path, threshold, messages
):
    _write(
        tmp_path,
        "common/scripted_effects/a.txt",
        "TST_a = {\n"
        "\tset_variable = { TST_strength = 25 }\n"
        "\tclamp_variable = { var = TST_strength min = 0 max = 50 }\n"
        "}\n",
    )
    _write(
        tmp_path,
        "common/scripted_effects/b.txt",
        "TST_b = {\n\tclamp_variable = { var = TST_strength min = 10 max = 100 }\n}\n",
    )
    _write(
        tmp_path,
        _EVENTS,
        f"TST_demo = {{\n\tcheck_variable = {{ TST_strength > {threshold} }}\n}}\n",
    )
    validator = _validator(tmp_path)

    validator.validate_clamp_range_conflicts()

    found = [issue.message for issue in validator._issues]
    assert len(found) == len(messages)
    for message, fragments in zip(found, messages):
        assert all(fragment in message for fragment in fragments)


# --- math precision ---------------------------------------------------------


@pytest.mark.parametrize(
    "text, count",
    [
        pytest.param(
            "effect = {\n"
            "\tset_variable = {\n"
            "\t\tvar = my_var\n"
            "\t\tvalue = 0.123456\n"
            "\t}\n"
            "}\n",
            1,
            id="a literal both patterns match reports once",
        ),
        pytest.param(
            "set_variable = { var = 0.123456 add = 0.999999 }\n",
            2,
            id="two distinct literals report twice",
        ),
        pytest.param(
            "set_variable = { my_var = 0.12345 }\n", 0, id="five decimals are fine"
        ),
    ],
)
def test_math_precision(tmp_path, text, count):
    path = _write(tmp_path, "x.txt", text)
    assert len(variable_scan(path, "math", tmp_path)) == count


# --- dynamic tokens ---------------------------------------------------------

_REGISTRY = "common/synchronized_dynamic_tokens/MD_tokens.txt"


def _tokens(text, registered=()):
    return [
        (message.split(" ", 1)[0], line)
        for message, _rel, line in V._scan_dynamic_tokens_text(
            text, "common/scripted_effects/x.txt", frozenset(registered)
        )
    ]


@pytest.mark.parametrize(
    ("text", "registered", "found"),
    [
        pytest.param(
            "set_variable = { x = token:Gen_7_Light }\n",
            {"gen_7_light"},
            [("token:Gen_7_Light", 1)],
            id="registration is case-sensitive",
        ),
        pytest.param(
            "set_variable = { x = token:a_b }\nset_variable = { y = token:a_b }\n",
            (),
            [("token:a_b", 1)],
            id="a repeated literal reports once per file",
        ),
        *(
            pytest.param(
                f"check_variable = {{ {ref} > 0 }}\n",
                (),
                [(ref.split(".")[-1], 1)],
                id=ref,
            )
            for ref in (
                "THIS.building_level@TST_custom_factor",
                "num_battalions_with_type@TST_custom_factor",
                "party_popularity_100@TST_custom_factor",
                "resource_produced@TST_custom_factor",
            )
        ),
        pytest.param(
            'desc = "Uses num_equipment@TST_a."\n',
            (),
            [("num_equipment@TST_a", 1)],
            id="trailing punctuation is not part of the token",
        ),
        *(
            pytest.param(text, (), [], id=text.strip())
            for text in (
                "set_variable = { x = token:topbar_[THIS.GetTag] }\n",
                "set_variable = { x = token:gen_$LEVEL$_light }\n",
                # Engine-known tokens need no registration.
                "check_variable = { resource@steel > 0 }\n",
                "check_variable = { party_popularity@democratic > 0.5 }\n",
                "check_variable = { modifier@political_power_gain > 0 }\n",
                # `@` after an ordinary variable is a scope, not a token target.
                "set_variable = { my_resource@TST_custom_factor = 1 }\n",
                # The target is read from a variable.
                "set_temp_variable = { size = party_popularity@var:ideology }\n",
            )
        ),
    ],
)
def test_dynamic_tokens_in_script(text, registered, found):
    assert _tokens(text, registered) == found


def test_validator_reports_unregistered_tokens_as_errors(tmp_path):
    _write(tmp_path, _REGISTRY, "gen_3_light\n")
    _write(
        tmp_path,
        "common/scripted_effects/tokens.txt",
        "TST_demo = {\n"
        "\tadd_to_temp_array = { techs = token:gen_3_light }\n"
        "\tadd_to_temp_array = { techs = token:gen_7_light }\n"
        "\t# add_to_temp_array = { techs = token:commented_out }\n"
        '\tlog = "[GetDateText]: [?modifier@TST_logged_factor]"\n'
        "}\n",
    )
    validator = _validator(tmp_path)

    validator.validate_unregistered_dynamic_tokens()

    assert [
        (issue.category, issue.severity, issue.file, issue.line)
        for issue in validator._issues
    ] == [
        (
            "unregistered-dynamic-token",
            V.Severity.ERROR,
            "common/scripted_effects/tokens.txt",
            line,
        )
        for line in (3, 5)
    ]
    assert validator._issues[0].message.startswith("token:gen_7_light ")
    assert validator._issues[1].message.startswith("modifier@TST_logged_factor ")


@pytest.mark.parametrize(
    ("path", "content", "line"),
    [
        (
            "history/countries/TST - Test.txt",
            "set_variable = { x = modifier@TST_custom_factor }\n",
            1,
        ),
        (
            "events/tst.txt",
            "TST_demo = {\n\tset_variable = { x = token:TST_custom_factor }\n}\n",
            2,
        ),
        (
            "interface/tst.gui",
            "guiTypes = {\n"
            "\t# instantTextBoxType\n"
            '\ttext = "[?modifier@TST_custom_factor|%0=+]"\n'
            "}\n",
            3,
        ),
    ],
    ids=["history", "events", "interface"],
)
def test_every_scanned_root_reports(tmp_path, path, content, line):
    _write(tmp_path, _REGISTRY, "gen_3_light\n")
    _write(tmp_path, path, content)
    validator = _validator(tmp_path)

    validator.validate_unregistered_dynamic_tokens()

    assert [(issue.file, issue.line) for issue in validator._issues] == [(path, line)]


def test_only_english_localisation_is_scanned(tmp_path):
    _write(tmp_path, _REGISTRY, "TST_mission\n")
    _write(
        tmp_path,
        "localisation/english/tst_l_english.yml",
        "l_english:\n"
        ' # TST_c: "[?modifier@TST_commented_out]"\n'
        ' TST_a: "[?days_mission_timeout@TST_mission] days"\n'
        ' TST_b: "[?modifier@TST_custom_factor|%1]"\n',
    )
    _write(
        tmp_path,
        "localisation/french/tst_l_french.yml",
        'l_french:\n TST_a: "[?modifier@TST_other_factor]"\n',
    )
    validator = _validator(tmp_path)

    validator.validate_unregistered_dynamic_tokens()

    assert [
        (issue.message.split(" ", 1)[0], issue.file, issue.line)
        for issue in validator._issues
    ] == [("modifier@TST_custom_factor", "localisation/english/tst_l_english.yml", 4)]


def test_missing_registry_reports_every_literal(tmp_path):
    _write(
        tmp_path,
        "events/tokens.txt",
        "TST_demo = {\n\tset_variable = { x = token:gen_3_light }\n}\n",
    )
    validator = _validator(tmp_path)

    validator.validate_unregistered_dynamic_tokens()

    assert [(issue.file, issue.line) for issue in validator._issues] == [
        ("events/tokens.txt", 2)
    ]


@pytest.mark.parametrize(
    ("registry", "exit_code"),
    [("gen_3_light\n", 1), ("gen_3_light\nTST_custom_factor\n", 0)],
    ids=["unregistered token", "every token registered"],
)
def test_unregistered_token_fails_a_strict_run(
    tmp_path, monkeypatch, registry, exit_code
):
    """CI runs the validator with --strict, so one finding must fail the job."""
    _write(tmp_path, _REGISTRY, registry)
    _write(
        tmp_path,
        "common/scripted_effects/tokens.txt",
        "TST_demo = {\n\tset_variable = { x = modifier@TST_custom_factor }\n}\n",
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            V.__file__,
            "--path",
            str(tmp_path),
            "--workers",
            "1",
            "--no-color",
            "--strict",
        ],
    )

    with pytest.raises(SystemExit) as exit_info:
        runpy.run_path(V.__file__, run_name="__main__")

    assert exit_info.value.code == exit_code


# --- variable tooltips and dynamic modifiers --------------------------------

DYN_MODS = """\
test_modifier = {
\ticon = x
\tpolitical_power_factor = tag_pp_var
\tstability_factor = tag_dual_var
\twar_support_factor = tag_dual_var
\tresearch_speed_factor = var:tag_scoped_var
\tmonthly_population = global.tag_global_var
\tlocal_building_slots_factor = TAG.tag_array_var^0
\tmaster_build_autonomy_factor = 0.05
\tarmy_speed_factor = tag_unlocalised_var
\tcustom_modifier_tooltip = tag_custom_tt
\tremove_trigger = {
\t\toriginal_tag = TAG
\t}
}
"""

# army_speed_factor_tt is deliberately absent; tag_custom_tt is present to show
# custom_modifier_tooltip is still not a modifier key.
TOOLTIP_LOC = """\
l_english:
 political_power_factor_tt: "a"
 stability_factor_tt: "a"
 war_support_factor_tt: "a"
 research_speed_factor_tt: "a"
 monthly_population_tt: "a"
 local_building_slots_factor_tt: "a"
 tag_custom_tt: "a"
"""


def _tooltip_mod(tmp_path, files):
    _write(tmp_path, "common/dynamic_modifiers/00_test.txt", DYN_MODS)
    _write(tmp_path, "localisation/english/test_l_english.yml", TOOLTIP_LOC)
    for rel, body in files.items():
        _write(tmp_path, rel, body)
    return _validator(tmp_path)


def test_dynamic_modifier_map_keeps_only_backing_variables(tmp_path):
    """A literal value, the icon, a custom tooltip key and a remove_trigger body
    never become backing variables; var:, global. and TAG.x^0 normalise."""
    assert _tooltip_mod(tmp_path, {})._collect_dynamic_modifier_vars() == {
        "tag_pp_var": ("political_power_factor",),
        "tag_dual_var": ("stability_factor", "war_support_factor"),
        "tag_scoped_var": ("research_speed_factor",),
        "tag_global_var": ("monthly_population",),
        "tag_array_var": ("local_building_slots_factor",),
        "tag_unlocalised_var": ("army_speed_factor",),
    }


@pytest.mark.parametrize(
    "body, pairs",
    [
        (
            "TST_modifier = {\n"
            "\ticon = GFX_idea_unknown\n"
            "\tpolitical_power_factor = TST_pp\n"
            "\tresearch_speed_factor = var:\n"
            "\tstability_factor = 0.05\n"
            "\tenable = {\n"
            "\t\thas_country_flag = TST_on\n"
            "\t}\n"
            "}\n",
            [("TST_pp", "political_power_factor")],
        ),
    ],
    ids=["pair with no variable name"],
)
def test_dynamic_modifier_worker(tmp_path, body, pairs):
    path = _write(tmp_path, "common/dynamic_modifiers/dyn.txt", body)
    assert V.collect_dynamic_modifier_vars((str(path), str(tmp_path))) == pairs


def _reward(body):
    return "focus = {\n\tid = TAG_test\n\tcompletion_reward = {\n%s\n\t}\n}\n" % body


def _moves(name, key, fix, effect="add_to_variable"):
    return (
        f"{effect} = {{ {name} ... }} moves dynamic modifier `{key}` with no"
        f" tooltip - the change is invisible to the player; {fix}"
    )


_WRITE = "add_to_variable = { tag_pp_var = 0.05 }"
_PP_MOVE = _moves(
    "tag_pp_var", "political_power_factor", "add tooltip = political_power_factor_tt"
)
_FOCUS_TT = "common/national_focus/t.txt"
_DECISION_TT = "common/decisions/t.txt"


def _decision(block):
    return "cat = {\n\td = {\n\t\t%s = {\n\t\t\t%s\n\t\t}\n\t}\n}\n" % (block, _WRITE)


# case: (file, content, finding messages)
_MISSING_TOOLTIP_CASES = {
    "untooltipped write": (_FOCUS_TT, _reward("\t\t" + _WRITE), [_PP_MOVE]),
    "tooltipped write": (
        _FOCUS_TT,
        _reward(
            "\t\tadd_to_variable = { tag_pp_var = 0.05"
            " tooltip = political_power_factor_tt }"
        ),
        [],
    ),
    "subtract_from_variable": (
        _FOCUS_TT,
        _reward("\t\tsubtract_from_variable = { tag_pp_var = 0.05 }"),
        [
            _moves(
                "tag_pp_var",
                "political_power_factor",
                "add tooltip = political_power_factor_tt",
                effect="subtract_from_variable",
            )
        ],
    ),
    "long-form target": (
        _FOCUS_TT,
        _reward("\t\tadd_to_variable = { var = tag_pp_var value = 0.05 }"),
        [_PP_MOVE],
    ),
    "variable backing two modifiers": (
        _FOCUS_TT,
        _reward("\t\tadd_to_variable = { tag_dual_var = 0.05 }"),
        [
            _moves(
                "tag_dual_var",
                "stability_factor",
                "add tooltip = stability_factor_tt or tooltip = war_support_factor_tt",
            )
        ],
    ),
    "modifier without a _tt key": (
        _FOCUS_TT,
        _reward("\t\tadd_to_variable = { tag_unlocalised_var = 0.05 }"),
        [
            _moves(
                "tag_unlocalised_var",
                "army_speed_factor",
                "`army_speed_factor_tt` does not exist either, so add it to"
                " MD_dm_modifiers_l_english.yml first",
            )
        ],
    ),
    "variable that backs no modifier": (
        _FOCUS_TT,
        _reward("\t\tadd_to_variable = { TAG_some_counter = 1 }"),
        [],
    ),
    "complete_effect": (_DECISION_TT, _decision("complete_effect"), [_PP_MOVE]),
    "timeout_effect": (_DECISION_TT, _decision("timeout_effect"), [_PP_MOVE]),
    "remove_effect": (_DECISION_TT, _decision("remove_effect"), [_PP_MOVE]),
    "cancel_effect": (_DECISION_TT, _decision("cancel_effect"), []),
    "event option": (
        "events/t.txt",
        "country_event = {\n\tid = t.1\n\toption = {\n\t\tname = t.1.a\n"
        f"\t\t{_WRITE}\n\t}}\n}}\n",
        [_PP_MOVE],
    ),
    "MIO trait on_complete": (
        "common/military_industrial_organization/organizations/t.txt",
        "org = {\n\ttrait = {\n\t\ttoken = a\n\t\ton_complete = {\n"
        f"\t\t\t{_WRITE}\n\t\t}}\n\t}}\n}}\n",
        [_PP_MOVE],
    ),
    "joint focus": (
        _FOCUS_TT,
        "joint_focus = {\n\tid = TAG_joint\n\tcompletion_reward = {\n"
        f"\t\t{_WRITE}\n\t}}\n}}\n",
        [_PP_MOVE],
    ),
    "nested inside a rendered block": (
        _FOCUS_TT,
        _reward("\t\tif = {\n\t\t\tlimit = { has_war = no }\n\t\t\t%s\n\t\t}" % _WRITE),
        [_PP_MOVE],
    ),
    # The history/ bootstrap shape: no enclosing effect block, no tooltip.
    "top-level write": (_FOCUS_TT, _WRITE + "\n", []),
    "hidden_effect inside a rendered block": (
        _FOCUS_TT,
        _reward("\t\thidden_effect = {\n\t\t\t%s\n\t\t}" % _WRITE),
        [],
    ),
    "temp variable writes": (
        _FOCUS_TT,
        _reward(
            "\t\tset_temp_variable = { tag_pp_var = 0.05 }\n"
            "\t\tadd_to_temp_variable = { tag_pp_var = 0.05 }\n"
            "\t\tsubtract_from_temp_variable = { tag_pp_var = 0.05 }"
        ),
        [],
    ),
    "commented write": (_FOCUS_TT, _reward("\t\t# " + _WRITE), []),
    # An unbalanced `{` in a log string used to eat the reward span.
    "brace in a log string": (
        _FOCUS_TT,
        _reward('\t\tlog = "stray { brace"\n\t\t' + _WRITE),
        [_PP_MOVE],
    ),
}


@pytest.mark.parametrize(
    "rel, body, expected",
    _MISSING_TOOLTIP_CASES.values(),
    ids=_MISSING_TOOLTIP_CASES,
)
def test_missing_variable_tooltips(tmp_path, rel, body, expected):
    validator = _tooltip_mod(tmp_path, {rel: body})
    validator.validate_missing_variable_tooltips()

    assert [i.message for i in validator._issues] == expected
    assert {(i.category, i.severity) for i in validator._issues} <= {
        ("dynamic-modifier-tooltip-missing", V.Severity.ERROR)
    }


def test_variable_write_without_a_target_is_ignored(tmp_path):
    path = _write(
        tmp_path,
        "common/national_focus/focus.txt",
        _reward("\t\tadd_to_variable = { }"),
    )

    backing = {"TST_pp": ("political_power_factor",)}
    assert variable_scan(path, "missing", tmp_path, backing=backing) == []


def _no_loc(key):
    return (
        f"tooltip = {key} has no English localisation entry - the tooltip renders"
        " the raw key; add it to MD_dm_modifiers_l_english.yml"
    )


_BAD_KEY_WRITE = "add_to_variable = { tag_pp_var = 0.05 tooltip = no_such_key_tt }"

# case: (file, content, finding messages)
_TOOLTIP_KEY_CASES = {
    "unlocalised key": (
        _FOCUS_TT,
        _reward("\t\t" + _BAD_KEY_WRITE),
        [_no_loc("no_such_key_tt")],
    ),
    "localised key": (
        _FOCUS_TT,
        _reward(
            "\t\tadd_to_variable = { tag_pp_var = 0.05"
            " tooltip = political_power_factor_tt }"
        ),
        [],
    ),
    "vanilla key": (
        _FOCUS_TT,
        _reward(
            "\t\tadd_to_variable = { tag_pp_var = 0.05 tooltip = air_range_factor_tt }"
        ),
        [],
    ),
    "every variable effect": (
        _FOCUS_TT,
        _reward(
            "\t\tset_variable = { a = 1 tooltip = bad_one_tt }\n"
            "\t\tmultiply_variable = { b = 1 tooltip = bad_two_tt }\n"
            "\t\tclamp_variable = { var = c min = 0 max = 1 tooltip = bad_three_tt }"
        ),
        [_no_loc("bad_one_tt"), _no_loc("bad_two_tt"), _no_loc("bad_three_tt")],
    ),
    "inside hidden_effect": (
        _FOCUS_TT,
        _reward("\t\thidden_effect = {\n\t\t\t" + _BAD_KEY_WRITE + "\n\t\t}"),
        [],
    ),
    # Unlike the missing-tooltip check, a broken key is broken wherever it sits.
    "outside a rendered block": (
        "common/scripted_effects/t.txt",
        "e = {\n\tadd_to_variable = { tag_pp_var = 1 tooltip = no_such_key_tt }\n}\n",
        [_no_loc("no_such_key_tt")],
    ),
    "repeated key in one file": (
        _FOCUS_TT,
        _reward(
            "\t\t" + _BAD_KEY_WRITE + "\n"
            "\t\tadd_to_variable = { tag_dual_var = 0.05 tooltip = no_such_key_tt }"
        ),
        [_no_loc("no_such_key_tt")],
    ),
    "commented tooltip": (_FOCUS_TT, _reward("\t\t# " + _BAD_KEY_WRITE), []),
}


@pytest.mark.parametrize(
    "rel, body, expected", _TOOLTIP_KEY_CASES.values(), ids=_TOOLTIP_KEY_CASES
)
def test_variable_tooltip_keys(tmp_path, rel, body, expected):
    validator = _tooltip_mod(tmp_path, {rel: body})
    validator.validate_variable_tooltip_keys()

    assert [i.message for i in validator._issues] == expected
    assert {(i.category, i.severity) for i in validator._issues} <= {
        ("variable-tooltip-missing-loc", V.Severity.ERROR)
    }


# --- redundant focus flags --------------------------------------------------

_TREE = "common/national_focus/05_tag.txt"
_READER = "common/decisions/tag.txt"
_DONE_READER = "d = { available = { has_country_flag = tag_done } }"
_SET_DONE = "\t\t\tset_country_flag = tag_done\n"
_DONE_LOC = {
    "localisation/english/test_l_english.yml": 'l_english:\n tag_done: "done"\n'
}
_RELOAD = "; caution: this file reloads a focus tree without keep_completed = yes"
_HAS_LOC = "; flag has a loc key - the effect tooltip line changes"


def _focus(reward_body, focus_id="TAG_focus", extra=""):
    return (
        "focus_tree = {\n"
        "\tid = tag_focus\n"
        "\tfocus = {\n"
        f"\t\tid = {focus_id}\n"
        f"{extra}"
        "\t\tcompletion_reward = {\n"
        f"{reward_body}"
        "\t\t}\n"
        "\t}\n"
        "}\n"
    )


def _redundant(readers, flag="tag_done", focus_id="TAG_focus", suffix=""):
    shown = ", ".join(readers[:8])
    more = f", +{len(readers) - 8} more" if len(readers) > 8 else ""
    return (
        f"{flag} - set only by focus {focus_id}; replace {len(readers)} read(s)"
        f" with `has_completed_focus = {focus_id}`: {shown}{more}{suffix}"
    )


def _read_at(line, scope=""):
    return f"{os.path.normpath(_READER)}:{line}" + (
        f" (in {scope} scope - keep the wrapper)" if scope else ""
    )


_ONE_READ = _redundant([_read_at(1)])
_SWAP_TREE = _focus(_SET_DONE) + _focus(
    "\t\t\tload_focus_tree = generic_focus\n", focus_id="TAG_swap"
)

# case: (files beside the default tree and reader, finding message or None)
_REDUNDANT_FLAG_CASES = {
    "flag set once in a reward": ({}, _ONE_READ),
    "set nested in hidden_effect": (
        {_TREE: _focus("\t\t\thidden_effect = { set_country_flag = tag_done }\n")},
        _ONE_READ,
    ),
    "reader in a tag scope": (
        {_READER: "d = { available = { SAZ = { has_country_flag = tag_done } } }"},
        _redundant([_read_at(1, "SAZ")]),
    ),
    "two setters": (
        {_TREE: _focus(_SET_DONE) + _focus(_SET_DONE, focus_id="TAG_other")},
        None,
    ),
    "setter outside any focus": (
        {
            _TREE: "",
            "common/scripted_effects/tag.txt": "tag_effect = { set_country_flag = tag_done }",
        },
        None,
    ),
    "timed set": (
        {
            _TREE: _focus(
                "\t\t\tset_country_flag = { flag = tag_done days = 30 value = 1 }\n"
            )
        },
        None,
    ),
    **{
        f"set under {block}": (
            {
                _TREE: _focus(
                    f"\t\t\t{block} = {{\n"
                    "\t\t\t\tlimit = { has_war = yes }\n"
                    "\t\t\t\tset_country_flag = tag_done\n"
                    "\t\t\t}\n"
                )
            },
            None,
        )
        for block in ("if", "else_if", "else", "random", "random_list")
    },
    "set in another country scope": (
        {_TREE: _focus("\t\t\tSAZ = {\n\t" + _SET_DONE + "\t\t\t}\n")},
        None,
    ),
    "set in select_effect": (
        {
            _TREE: "focus_tree = {\n\tid = tag_focus\n\tfocus = {\n\t\tid = TAG_focus\n"
            "\t\tselect_effect = {\n\t\t\tset_country_flag = tag_done\n\t\t}\n\t}\n}\n"
        },
        None,
    ),
    "cleared flag": (
        {
            _READER: _DONE_READER[:-1]
            + "complete_effect = { clr_country_flag = tag_done } }"
        },
        None,
    ),
    "modified flag": (
        {
            _READER: _DONE_READER[:-1] + "complete_effect = "
            "{ modify_country_flag = { flag = tag_done value = 1 } } }"
        },
        None,
    ),
    # Zero readers belongs to the unused flag check.
    "no readers": ({_READER: ""}, None),
    "long-form read": (
        {
            _READER: "d = { available = { has_country_flag = { flag = tag_done value > 0 } } }"
        },
        None,
    ),
    "dynamic scope flag": (
        {_TREE: _focus("\t\t\tset_country_flag = tag_done_@ROOT\n")},
        None,
    ),
    "bypassable focus": (
        {_TREE: _focus(_SET_DONE, extra="\t\tbypass = { has_war = yes }\n")},
        None,
    ),
    "joint reward": (
        {
            _TREE: "joint_focus = {\n\tid = TAG_focus\n"
            "\tcompletion_reward_joint_originator = {\n"
            "\t\tset_country_flag = tag_done\n\t}\n}\n"
        },
        None,
    ),
    "tree reload without keep_completed": (
        {_TREE: _SWAP_TREE},
        _redundant([_read_at(1)], suffix=_RELOAD),
    ),
    "tree reload with keep_completed": (
        {
            _TREE: _focus(_SET_DONE)
            + _focus(
                "\t\t\tload_focus_tree = { tree = generic_focus keep_completed = yes }\n",
                focus_id="TAG_swap",
            )
        },
        _ONE_READ,
    ),
    "flag with a loc key": (_DONE_LOC, _redundant([_read_at(1)], suffix=_HAS_LOC)),
    # UKR_vitrenko_power / IRQ_spring_of_islam shape.
    "reload caution then loc key": (
        {_TREE: _SWAP_TREE, **_DONE_LOC},
        _redundant([_read_at(1)], suffix=_RELOAD + _HAS_LOC),
    ),
    "two readers": (
        {_READER: _DONE_READER + "\n" + _DONE_READER + "\n"},
        _redundant([_read_at(1), _read_at(2)]),
    ),
    "readers past eight are counted": (
        {
            _READER: "".join(
                f"d{i} = {{ available = {{ has_country_flag = tag_done }} }}\n"
                for i in range(10)
            )
        },
        _redundant([_read_at(line) for line in range(1, 11)]),
    ),
}


@pytest.mark.parametrize(
    "files, expected", _REDUNDANT_FLAG_CASES.values(), ids=_REDUNDANT_FLAG_CASES
)
def test_redundant_focus_flags(tmp_path, files, expected):
    for rel, body in {_TREE: _focus(_SET_DONE), _READER: _DONE_READER, **files}.items():
        _write(tmp_path, rel, body)
    validator = _validator(tmp_path, redundant_focus_flags=True)

    validator.validate_redundant_focus_flags(
        [str(p) for p in tmp_path.rglob("*.txt") if p.is_file()]
    )

    assert [(i.category, i.message, i.file, i.line) for i in validator._issues] == (
        [("redundant-focus-flag", expected, _TREE, 6)] if expected else []
    )


def test_self_read_in_the_setter_focus_is_still_reported(tmp_path):
    # TUR_beacon_of_islam gates its own availability on its own flag: dead
    # under both constructs, so a future skip-self-reads change must confront it.
    _write(
        tmp_path,
        _TREE,
        _focus(
            "\t\t\tset_country_flag = beacon_done\n",
            focus_id="TUR_beacon_of_islam",
            extra="\t\tavailable = { has_country_flag = beacon_done }\n",
        ),
    )
    validator = _validator(tmp_path, redundant_focus_flags=True)

    validator.validate_redundant_focus_flags([str(tmp_path / _TREE)])

    assert [(i.message, i.line) for i in validator._issues] == [
        (
            "beacon_done - set only by focus TUR_beacon_of_islam; replace 1 read(s)"
            " with `has_completed_focus = TUR_beacon_of_islam`:"
            f" {os.path.normpath(_TREE)}:5",
            7,
        )
    ]


def test_full_run_passes_every_file_to_the_redundant_flag_check(tmp_path):
    _write(tmp_path, _TREE, _focus(_SET_DONE))
    _write(tmp_path, _READER, _DONE_READER)
    validator = _validator(tmp_path, redundant_focus_flags=True)

    validator.run_validations()

    assert [
        (issue.message, issue.file, issue.line)
        for issue in validator._issues
        if issue.category == "redundant-focus-flag"
    ] == [(_ONE_READ, _TREE, 6)]


def test_focus_flag_sets_belong_to_the_reward_that_holds_them():
    text = (
        "focus_tree = {\n"
        "\tfocus = {\n"
        "\t\tid = TST_first\n"
        "\t\tcompletion_reward = { set_country_flag = TST_a }\n"
        "\t}\n"
        "\tset_country_flag = TST_between\n"
        "\tfocus = {\n"
        "\t\tid = TST_second\n"
        "\t\tcompletion_reward = { set_country_flag = TST_c }\n"
        "\t}\n"
        "}\n"
        "set_country_flag = TST_after"
    )

    set_sites = V._scan_focus_flag_sites(text, "f.txt", True)[0]

    assert set_sites == {
        "TST_a": [("f.txt", 4, "TST_first", None)],
        "TST_between": [("f.txt", 6, None, "not-in-focus")],
        "TST_c": [("f.txt", 9, "TST_second", None)],
        "TST_after": [("f.txt", 12, None, "not-in-focus")],
    }


def test_focus_flag_read_past_the_last_brace_has_no_scope():
    text = (
        "SAZ = { has_country_flag = TST_inside }\n"
        "SAZ = {\n"
        "\thas_country_flag = TST_open"
    )

    read_sites = V._scan_focus_flag_sites(text, "d.txt", False)[1]

    assert read_sites == {
        "TST_inside": [("d.txt", 1, "SAZ")],
        "TST_open": [("d.txt", 3, None)],
    }


# --- shared scan, workers and indexes ---------------------------------------


def _unreadable(tmp_path, name="src.txt"):
    """A directory where a .txt is expected; opening it raises."""
    path = tmp_path / name
    path.mkdir(parents=True)
    return path


_SHARED_SECTION_EMPTY = {
    "math": [],
    "treasury": [],
    "clamp_checks": [],
    "available": [],
    "available_flags": [],
    "scripted": [],
    "var_tooltips": [],
    "missing": [],
    "flag_syntax": ([], []),
}


@pytest.mark.parametrize("section, empty", _SHARED_SECTION_EMPTY.items())
def test_shared_scan_is_empty_for_an_unreadable_path(tmp_path, section, empty):
    assert variable_scan(_unreadable(tmp_path), section, tmp_path) == empty


@pytest.mark.parametrize(
    "worker, empty",
    [
        (V.collect_clamp_ranges, ([], [], [])),
        (V.collect_dynamic_modifier_vars, []),
    ],
    ids=["clamp harvest", "dynamic modifiers"],
)
def test_harvest_survives_an_unreadable_path(tmp_path, worker, empty):
    assert worker((str(_unreadable(tmp_path)), str(tmp_path))) == empty


def test_shared_scan_masks_only_read_errors(tmp_path, monkeypatch):
    assert variable_scan(tmp_path / "does_not_exist.txt", "math", tmp_path) == []

    existing = tmp_path / "valid.txt"
    existing.write_text("add = 0.1234567\n", encoding="utf-8")

    def bad_scan(*args, **kwargs):
        raise ValueError("Unexpected error")

    monkeypatch.setattr(V, "_scan_math_precision_text", bad_scan)
    with pytest.raises(ValueError, match="Unexpected error"):
        variable_scan(existing, "math", tmp_path)


def test_matching_brace_falls_back_to_end_of_text():
    text = "set_variable = { x = 1"
    assert V._matching_brace(text, text.index("{")) == len(text)


def _reference_scope_stack(text, pos):
    """Openers enclosing ``pos``, innermost first, by the original sorted walk."""
    events = [(m.end() - 1, m.group(1)) for m in V._SCOPE_OPEN_RE.finditer(text)]
    events += [(m.start(), None) for m in re.finditer(r"\}", text)]
    stack = []
    for at, token in sorted(events, key=lambda event: event[0]):
        if at >= pos:
            break
        if token is not None:
            stack.append(token)
        elif stack:
            stack.pop()
    return stack[::-1]


_INDEX_CASES = {
    "brace in a string": 'outer = { log = "x } y" inner = { c = 1 } }\n',
    "hash in a string": 'outer = { log = "#}" inner = { } }\n',
    "comment with braces": "outer = { b = 1 } # skip = { d }\nnext = { }\n",
    "unbalanced": "} } outer = { middle = { c = 1 }\n",
    "three deep": "outer = {\n\tmiddle = {\n\t\tinner = { d = 1 }\n\t}\n}\n",
    "first and last line": "first = { y }\n\nlast = { w }",
    "empty": "",
    "no trailing newline": "outer = { inner = { } }",
    "crlf": "outer = {\r\n\tinner = {\r\n\t}\r\n}\r\n",
    "odd openers": "ab = { x.y = { 1.5={ } } a = bc = { } = { } }",
}


@pytest.mark.parametrize("text", _INDEX_CASES.values(), ids=_INDEX_CASES.keys())
def test_scope_index_matches_the_sorted_event_walk(text):
    index = V._ScopeIndex(text)
    for pos in range(len(text) + 1):
        assert index.stack_at(pos) == _reference_scope_stack(text, pos), pos


@pytest.mark.parametrize("text", _INDEX_CASES.values(), ids=_INDEX_CASES.keys())
def test_source_line_matches_a_count_from_the_start(text):
    src = V._Source(text, "x.txt")
    forward = list(range(len(text) + 1))
    for pos in forward + forward[::-1] + forward[::3]:
        assert src.line(pos) == text.count("\n", 0, pos) + 1, pos


@pytest.mark.parametrize(
    "text",
    ["set_x = a", "aset_x = b", "_set_x = c", "x\nset_x = d", "set_x = e set_x = f"]
    + ["éset_x = g", "set_xset_x = h", ""],
)
def test_literal_first_pattern_keeps_the_leading_word_boundary(text):
    fast = V.word_start_re("set_x", r"\s*=\s*(\w+)")
    plain = re.compile(r"\bset_x\s*=\s*(\w+)")

    assert [(m.span(), m.groups()) for m in fast.finditer(text)] == [
        (m.span(), m.groups()) for m in plain.finditer(text)
    ]


# Each worker gets one file that yields a result. The mod root sits inside a
# `docs/` folder, so a worker that dropped mod_path would skip the file.
_SKIP_RULE_CASES = {
    "flags": (
        "common/scripted_effects/a.txt",
        "set_country_flag = TST_a\n",
        lambda f, m: V.process_file_for_all_flags((f, False, "country", m))[0],
    ),
    "flag syntax": (
        "common/scripted_effects/b.txt",
        "set_country_flag = { flag = TST_b }\n",
        lambda f, m: variable_scan(f, "flag_syntax", m)[1],
    ),
    "math precision": (
        "common/scripted_effects/c.txt",
        "add = 0.1234567\n",
        lambda f, m: variable_scan(f, "math", m),
    ),
    "clamp harvest": (
        "common/scripted_effects/d.txt",
        "clamp_variable = { var = TST_v min = 0 max = 10 }\n",
        lambda f, m: V.collect_clamp_ranges((f, m))[0],
    ),
    "clamp checks": (
        "events/e.txt",
        "check_variable = { TST_v > 50 }\n",
        lambda f, m: variable_scan(f, "clamp_checks", m),
    ),
    "variable tooltips": (
        "events/g.txt",
        "set_variable = { TST_v = 1 tooltip = TST_tt }\n",
        lambda f, m: variable_scan(f, "var_tooltips", m),
    ),
    "event targets": (
        "events/i.txt",
        "save_event_target_as = TST_t\n",
        lambda f, m: V.process_file_for_all_targets((f, False, m))[0],
    ),
    "localisation targets": (
        "localisation/english/x_l_english.yml",
        'l_english:\n a:0 "[TST_t.GetName]"\n',
        lambda f, m: V._scan_targets_in_loc((f, ("TST_t",)), mod_path=m),
    ),
    "focus flags": (
        "common/national_focus/f.txt",
        "focus = {\n\tid = TST_f\n\tcompletion_reward = { set_country_flag = TST_f }\n}\n",
        lambda f, m: V.process_file_for_focus_flag_sites((f, m))[0],
    ),
    "available checks": (
        "common/decisions/j.txt",
        "c = {\n\td = {\n\t\tavailable = { check_variable = { TST_v > 5 } }\n\t}\n}\n",
        lambda f, m: variable_scan(f, "available", m),
    ),
    "available flags": (
        "common/decisions/m.txt",
        "d = {\n\tavailable = {\n\t\thas_country_flag = TST_flag\n\t}\n}\n",
        lambda f, m: variable_scan(f, "available_flags", m),
    ),
    "scripted trigger calls": (
        "common/decisions/k.txt",
        "c = {\n\td = {\n\t\tavailable = { TST_border = yes }\n\t}\n}\n",
        lambda f, m: variable_scan(
            f, "scripted", m, flagged_names=frozenset({"TST_border"})
        ),
    ),
    "missing variable tooltips": (
        "events/l.txt",
        "option = { add_to_variable = { TST_pp = 1 } }\n",
        lambda f, m: variable_scan(
            f, "missing", m, backing={"TST_pp": ("political_power_factor",)}
        ),
    ),
    "treasury scope": (
        "events/n.txt",
        "option = { random_owned_state = { modify_treasury_effect = yes } }\n",
        lambda f, m: variable_scan(f, "treasury", m),
    ),
}


@pytest.mark.parametrize(
    "rel, content, scan", _SKIP_RULE_CASES.values(), ids=_SKIP_RULE_CASES.keys()
)
def test_workers_apply_skip_rules_relative_to_the_mod_root(
    tmp_path, rel, content, scan
):
    mod = tmp_path / "docs" / "mod"
    path = _write(mod, rel, content)

    assert scan(str(path), str(mod))


@pytest.mark.parametrize(
    "rel, content, scan", _SKIP_RULE_CASES.values(), ids=_SKIP_RULE_CASES.keys()
)
def test_workers_skip_non_script_directories(tmp_path, rel, content, scan):
    """Content the test above shows yields a result once it is read."""
    path = _write(tmp_path, f"gfx/{os.path.basename(rel)}", content)

    assert not scan(str(path), str(tmp_path))


# --- pool and disk cache ----------------------------------------------------


def _full_run(tmp_path, workers=1):
    validator = V.Validator(
        str(tmp_path), use_colors=False, workers=workers, redundant_focus_flags=True
    )
    try:
        validator.run_validations()
        assert (validator._pool is not None) == (workers > 1)
    finally:
        if validator._pool is not None:
            validator._pool.terminate()
            validator._pool.join()
    return _issue_rows(validator)


def test_flag_target_and_focus_caches_hit_then_follow_new_content(
    tmp_path, monkeypatch
):
    monkeypatch.delenv("MD_NO_CACHE", raising=False)
    _write(
        tmp_path,
        "common/national_focus/tree.txt",
        "focus = {\n"
        "\tid = TST_focus\n"
        "\tcompletion_reward = {\n"
        "\t\tset_country_flag = TST_done\n"
        "\t\tsave_event_target_as = TST_target\n"
        "\t}\n"
        "}\n",
    )
    reader = _write(
        tmp_path,
        "common/decisions/dec.txt",
        "d = { available = { has_country_flag = TST_done } }\n",
    )
    cold = _full_run(tmp_path)

    def miss(*_args):
        raise AssertionError("expected a cache hit")

    with monkeypatch.context() as patch:
        for scan in (
            "_scan_flags_in_file",
            "_scan_targets_in_text",
            "_scan_focus_flag_sites",
        ):
            patch.setattr(V, scan, miss)
        warm = _full_run(tmp_path)

    _write(
        tmp_path,
        "common/decisions/dec.txt",
        "d = { available = { has_country_flag = TST_other } }\n",
    )
    # A fresh process would read the edit; drop this process's in-memory copy.
    V.FileOpener.invalidate(str(reader))
    changed = _full_run(tmp_path)

    assert warm == cold
    assert [row[0] for row in cold].count("redundant-focus-flag") == 1
    assert ("variables", "TST_other", "common/decisions/dec.txt", 1) in changed
    assert ("variables", "TST_done", "common/national_focus/tree.txt", 4) in changed
    assert "redundant-focus-flag" not in [row[0] for row in changed]


def test_pooled_run_matches_the_in_process_run(tmp_path, monkeypatch):
    # Past the pool threshold of ten files, so the shared scan really fans out.
    monkeypatch.setenv("MD_MAX_WORKERS", "2")
    for index in range(12):
        _write(
            tmp_path,
            f"common/decisions/dec{index}.txt",
            f"TST_category_{index} = {{\n"
            f"\tTST_decision_{index} = {{\n"
            "\t\tavailable = { check_variable = { TST_v > 5 } }\n"
            "\t\tcomplete_effect = {\n"
            "\t\t\tadd_to_variable = { TST_v = 0.1234567 }\n"
            "\t\t\trandom_owned_state = { modify_treasury_effect = yes }\n"
            f"\t\t\tset_country_flag = {{ flag = TST_flag_{index} }}\n"
            "\t\t}\n"
            "\t}\n"
            "}\n",
        )

    in_process = _full_run(tmp_path, workers=1)
    pooled = _full_run(tmp_path, workers=2)

    assert pooled == in_process
    assert {row[0] for row in in_process} >= {
        "untooltipped-available-check",
        "math-precision",
        "treasury-state-scope",
    }
    assert len(in_process) >= 12 * 4


def test_one_worker_flag_pass_stays_in_process_and_matches_the_pool(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("MD_MAX_WORKERS", "2")
    expected = []
    for index in range(12):
        flag = f"TST_{index:02}"
        rel = f"common/scripted_effects/{flag}.txt"
        _write(
            tmp_path,
            rel,
            f"set_country_flag = {flag}\nhas_global_flag = {flag}_g\n"
            f"clr_state_flag = {flag}_s\nsave_event_target_as = {flag}_t\n",
        )
        expected += [
            ("variables", name, rel, line)
            for line, name in enumerate(
                (flag, f"{flag}_g", f"{flag}_s", f"{flag}_t"), 1
            )
        ]
    pooled = _full_run(tmp_path, workers=2)

    def no_pool(*_args, **_kwargs):
        raise AssertionError("one worker must not start a pool")

    monkeypatch.setattr(validator_common, "Pool", no_pool)
    in_process = _full_run(tmp_path, workers=1)

    assert in_process == pooled
    assert in_process == sorted(expected)
