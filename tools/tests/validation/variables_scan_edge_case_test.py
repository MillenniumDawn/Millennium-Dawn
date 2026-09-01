"""Edge cases for the validate_variables pool workers and scan helpers.

Every worker runs in a forked process over whatever the repo actually holds, so
the failure mode that matters is a worker that raises, hangs, or invents a
finding on input it cannot parse: a skipped path, a file it may not read, an
unbalanced brace, a stray quote. Each case here pins "degrade to no finding"
rather than the crash or false positive.
"""

import os

import pytest
import validate_variables as V


def _write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as file:
        file.write(content)
    return path


def _skipped(tmp_path, name="src.txt"):
    """A path validate_variables must never open (gfx/ is not game script)."""
    return _write(tmp_path / "gfx" / name, "set_country_flag = TST_x\n")


def _unreadable(tmp_path, name="src.txt"):
    """A directory where a .txt is expected — opening it raises."""
    path = tmp_path / name
    path.mkdir(parents=True)
    return path


# --- flag scanning ---------------------------------------------------------


def test_flag_scan_collects_set_used_and_cleared(tmp_path):
    path = _write(
        tmp_path / "common" / "scripted_effects" / "flags.txt",
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


def test_flag_scan_skips_non_script_directories(tmp_path):
    path = _skipped(tmp_path)
    assert V.process_file_for_all_flags(
        (str(path), False, "country", str(tmp_path))
    ) == (
        {},
        {},
        {},
    )


def test_flag_scan_returns_nothing_for_an_empty_file(tmp_path):
    path = _write(tmp_path / "common" / "scripted_effects" / "empty.txt", "")
    assert V.process_file_for_all_flags(
        (str(path), False, "country", str(tmp_path))
    ) == (
        {},
        {},
        {},
    )


def test_unsupported_flag_type_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="Unsupported flag_type"):
        V.Variables.get_all_flags(str(tmp_path), flag_type="character", workers=1)


# --- set_*_flag syntax -----------------------------------------------------


def test_flag_syntax_reports_days_without_value_and_long_form(tmp_path):
    path = _write(
        tmp_path / "common" / "scripted_effects" / "syntax.txt",
        "flag_demo = {\n"
        "\tset_country_flag = { flag = TST_timed days = 30 }\n"
        "\tset_global_flag = { flag = TST_long_form }\n"
        "}\n",
    )

    days, long_form = V.process_file_for_flag_syntax((str(path), str(tmp_path)))

    relative = os.path.join("common", "scripted_effects", "syntax.txt")
    assert len(days) == 1 and "missing value field" in days[0]
    assert days[0].startswith(f"{relative}:2")
    assert len(long_form) == 1 and "use shorthand" in long_form[0]
    assert long_form[0].startswith(f"{relative}:3")


def test_flag_syntax_accepts_days_with_value(tmp_path):
    path = _write(
        tmp_path / "common" / "scripted_effects" / "ok.txt",
        "set_country_flag = { flag = TST_timed days = 30 value = 1 }\n",
    )
    assert V.process_file_for_flag_syntax((str(path), str(tmp_path))) == ([], [])


def test_flag_syntax_skips_non_script_directories(tmp_path):
    assert V.process_file_for_flag_syntax((str(_skipped(tmp_path)), str(tmp_path))) == (
        [],
        [],
    )


def test_flag_syntax_survives_an_unreadable_path(tmp_path):
    assert V.process_file_for_flag_syntax(
        (str(_unreadable(tmp_path)), str(tmp_path))
    ) == ([], [])


def test_dynamic_flag_matcher_only_expands_scope_substitutions():
    patterns = V.Validator._build_dynamic_flag_matchers(
        ["accords_@ROOT_left", "trade_agreement@USA", "plain_flag"]
    )

    assert len(patterns) == 1
    assert patterns[0].match("accords_MOR_left")
    assert patterns[0].match("accords_MOR_CW_0_left")
    assert not patterns[0].match("accords_lowercase_left")


# --- math precision --------------------------------------------------------


def test_math_precision_skips_non_script_directories(tmp_path):
    assert (
        V.process_file_for_math_precision((str(_skipped(tmp_path)), str(tmp_path)))
        == []
    )


def test_math_precision_survives_an_unreadable_path(tmp_path):
    assert (
        V.process_file_for_math_precision((str(_unreadable(tmp_path)), str(tmp_path)))
        == []
    )


# --- brace matching --------------------------------------------------------


def test_matching_brace_falls_back_to_end_of_text():
    text = "set_variable = { x = 1"
    assert V._matching_brace(text, text.index("{")) == len(text)


# --- clamp harvesting ------------------------------------------------------


def test_clamp_without_a_max_is_not_a_range(tmp_path):
    path = _write(
        tmp_path / "common" / "scripted_effects" / "clamp.txt",
        "clamp_variable = { var = TST_partial min = 0 }\n"
        "clamp_variable = { var = TST_full min = 0 max = 100 }\n",
    )

    found, _temp, _persistent = V.collect_clamp_ranges((str(path), str(tmp_path)))

    assert found == [("TST_full", 0.0, 100.0)]


def test_clamp_harvest_skips_non_script_directories(tmp_path):
    assert V.collect_clamp_ranges((str(_skipped(tmp_path)), str(tmp_path))) == (
        [],
        [],
        [],
    )


def test_clamp_harvest_survives_an_unreadable_path(tmp_path):
    assert V.collect_clamp_ranges((str(_unreadable(tmp_path)), str(tmp_path))) == (
        [],
        [],
        [],
    )


def test_clamp_conflicts_skip_non_script_directories(tmp_path):
    args = (str(_skipped(tmp_path)), str(tmp_path), {"TST_x": (0.0, 10.0)})
    assert V.process_file_for_clamp_conflicts(args) == []


def test_clamp_conflicts_survive_an_unreadable_path(tmp_path):
    args = (str(_unreadable(tmp_path)), str(tmp_path), {"TST_x": (0.0, 10.0)})
    assert V.process_file_for_clamp_conflicts(args) == []


# --- available-block scanning ----------------------------------------------


def test_available_scan_skips_non_script_directories(tmp_path):
    args = (str(_skipped(tmp_path)), str(tmp_path), frozenset())
    assert V._scan_available_file(args) == ([], [])


def test_check_variable_outside_available_is_not_flagged(tmp_path):
    """A stray `}` must not pop the block stack and mislabel the enclosing block."""
    path = _write(
        tmp_path / "common" / "national_focus" / "focus.txt",
        "}\n"
        "my_focus = {\n"
        "\tcompletion_reward = {\n"
        "\t\tcheck_variable = { TST_var > 5 }\n"
        "\t}\n"
        "}\n",
    )

    args = (str(path), str(tmp_path), frozenset())
    assert V.process_file_for_untooltipped_available_checks(args) == []


def test_scripted_trigger_body_with_a_stray_close_brace():
    assert V._scripted_trigger_body_has_unwrapped_global_flag("} has_global_flag = x")


def test_scripted_trigger_call_scan_skips_unreadable_paths(tmp_path):
    args = (
        str(_unreadable(tmp_path)),
        str(tmp_path),
        frozenset({"tst_border_available"}),
        frozenset(),
    )
    assert V.process_file_for_untooltipped_available_scripted_trigger(args) == []


def test_scripted_trigger_call_scan_survives_a_stray_close_brace(tmp_path):
    path = _write(
        tmp_path / "common" / "decisions" / "dec.txt",
        "}\n"
        "my_category = {\n"
        "\tmy_decision = {\n"
        "\t\tavailable = {\n"
        "\t\t\ttst_border_available = yes\n"
        "\t\t}\n"
        "\t}\n"
        "}\n",
    )

    args = (
        str(path),
        str(tmp_path),
        frozenset({"tst_border_available"}),
        frozenset(),
    )
    issues = V.process_file_for_untooltipped_available_scripted_trigger(args)

    assert len(issues) == 1
    assert issues[0][2] == 5


# --- dynamic modifier backing variables ------------------------------------


def test_dynamic_modifier_pair_with_no_variable_name_is_dropped(tmp_path):
    path = _write(
        tmp_path / "common" / "dynamic_modifiers" / "dyn.txt",
        "TST_modifier = {\n"
        "\ticon = GFX_idea_unknown\n"
        "\tpolitical_power_factor = TST_pp\n"
        "\tresearch_speed_factor = var:\n"
        "\tstability_factor = 0.05\n"
        "\tenable = {\n"
        "\t\thas_country_flag = TST_on\n"
        "\t}\n"
        "}\n",
    )

    assert V.collect_dynamic_modifier_vars((str(path), str(tmp_path))) == [
        ("TST_pp", "political_power_factor")
    ]


def test_dynamic_modifier_scan_survives_an_unreadable_path(tmp_path):
    assert (
        V.collect_dynamic_modifier_vars((str(_unreadable(tmp_path)), str(tmp_path)))
        == []
    )


# --- variable tooltips -----------------------------------------------------


def test_variable_tooltip_scan_skips_non_script_directories(tmp_path):
    assert (
        V.process_file_for_variable_tooltips((str(_skipped(tmp_path)), str(tmp_path)))
        == []
    )


def test_variable_tooltip_scan_survives_an_unreadable_path(tmp_path):
    assert (
        V.process_file_for_variable_tooltips(
            (str(_unreadable(tmp_path)), str(tmp_path))
        )
        == []
    )


def test_missing_tooltip_scan_skips_non_script_directories(tmp_path):
    args = (
        str(_skipped(tmp_path)),
        str(tmp_path),
        {"TST_pp": ("political_power_factor",)},
    )
    assert V.process_file_for_missing_variable_tooltips(args) == []


def test_variable_write_without_a_target_is_ignored(tmp_path):
    path = _write(
        tmp_path / "common" / "national_focus" / "focus.txt",
        "my_focus = {\n\tcompletion_reward = {\n\t\tadd_to_variable = { }\n\t}\n}\n",
    )

    args = (str(path), str(tmp_path), {"TST_pp": ("political_power_factor",)})
    assert V.process_file_for_missing_variable_tooltips(args) == []


# --- treasury scope classification -----------------------------------------


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


def test_treasury_scan_skips_unreadable_paths(tmp_path):
    assert (
        V.process_file_for_treasury_scope((str(_unreadable(tmp_path)), str(tmp_path)))
        == []
    )


def test_treasury_scan_skips_files_without_a_money_effect(tmp_path):
    path = _write(
        tmp_path / "common" / "national_focus" / "focus.txt",
        "my_focus = {\n\tcompletion_reward = {\n\t\tadd_stability = 0.05\n\t}\n}\n",
    )
    assert V.process_file_for_treasury_scope((str(path), str(tmp_path))) == []


def test_treasury_scan_survives_a_stray_close_brace(tmp_path):
    path = _write(
        tmp_path / "common" / "national_focus" / "focus.txt",
        "}\nmodify_treasury_effect = yes\n",
    )
    assert V.process_file_for_treasury_scope((str(path), str(tmp_path))) == []


# --- money consumer map ----------------------------------------------------


def test_consumer_map_reads_first_use_not_every_use(tmp_path):
    path = _write(
        tmp_path / "common" / "scripted_effects" / "money.txt",
        "double_write_effect = {\n"
        "\tset_temp_variable = { treasury_change = 5 }\n"
        "\tset_temp_variable = { treasury_change = 6 }\n"
        "}\n"
        "double_read_effect = {\n"
        "\tadd_to_variable = { TST_total = treasury_change }\n"
        "\tadd_to_variable = { TST_other = treasury_change }\n"
        "}\n"
        "read_then_write_effect = {\n"
        "\tadd_to_variable = { TST_total = treasury_change }\n"
        "\tset_temp_variable = { treasury_change = 0 }\n"
        "}\n"
        "unterminated_effect = {\n"
        "\tadd_to_variable = { TST_total = treasury_change }\n",
    )

    consumers = V.build_money_consumer_map([str(path)], str(tmp_path))[
        "treasury_change"
    ]

    assert "double_read_effect" in consumers
    assert "read_then_write_effect" in consumers
    assert "double_write_effect" not in consumers
    assert "unterminated_effect" not in consumers


def test_consumer_map_refuses_a_file_outside_the_mod(tmp_path):
    outside = str(tmp_path.parent / "outside_effects.txt")

    consumers = V.build_money_consumer_map([outside], str(tmp_path))

    assert consumers["treasury_change"] == frozenset({"modify_treasury_effect"})


# --- orphan money setters --------------------------------------------------


MONEY_CONSUMERS = {
    "treasury_change": frozenset({"modify_treasury_effect"}),
    "debt_change": frozenset({"modify_debt_effect"}),
    "int_investment_change": frozenset({"modify_international_investment_effect"}),
}


def test_orphan_money_scan_skips_non_script_directories(tmp_path):
    args = (str(_skipped(tmp_path)), str(tmp_path), {"treasury_change": frozenset()})
    assert V.process_file_for_orphan_money(args) == []


def test_orphan_money_scan_survives_an_unreadable_path(tmp_path):
    args = (str(_unreadable(tmp_path)), str(tmp_path), {"treasury_change": frozenset()})
    assert V.process_file_for_orphan_money(args) == []


def test_orphan_money_scan_skips_files_without_a_setter(tmp_path):
    path = _write(
        tmp_path / "events" / "ev.txt",
        "country_event = {\n\tid = tst.1\n\toption = {\n\t\tname = tst.1.a\n\t}\n}\n",
    )
    args = (str(path), str(tmp_path), {"treasury_change": frozenset()})
    assert V.process_file_for_orphan_money(args) == []


def test_setter_outside_any_effect_container_is_not_flagged(tmp_path):
    """An unbalanced container is dropped, so its setter has no holder block."""
    path = _write(
        tmp_path / "events" / "ev.txt",
        "completion_reward = {\n"
        "\tset_temp_variable = { treasury_change = 5 }\n"
        "\tmodify_treasury_effect = yes\n"
        "}\n"
        "option = {\n"
        "\tset_temp_variable = { debt_change = 5 }\n",
    )

    assert (
        V.process_file_for_orphan_money((str(path), str(tmp_path), MONEY_CONSUMERS))
        == []
    )


def test_branch_gated_rewrites_do_not_clobber_the_setter(tmp_path):
    """Re-writes nested in if arms sit below the setter's depth, so they are
    not clobbers — and a quoted log string between them must not desync the
    depth walk."""
    path = _write(
        tmp_path / "events" / "ev.txt",
        "completion_reward = {\n"
        "\tset_temp_variable = { treasury_change = 5 }\n"
        '\tlog = "money note"\n'
        "\tif = { limit = { always = yes } set_temp_variable = { treasury_change = 8 } }\n"
        "\tif = { limit = { always = yes } set_temp_variable = { treasury_change = 9 } }\n"
        "\tmodify_treasury_effect = yes\n"
        "}\n",
    )

    assert (
        V.process_file_for_orphan_money((str(path), str(tmp_path), MONEY_CONSUMERS))
        == []
    )


# --- event targets ---------------------------------------------------------


def test_event_target_scan_collects_set_used_and_cleared(tmp_path):
    path = _write(
        tmp_path / "events" / "ev.txt",
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


def test_tag_alias_file_only_contributes_global_event_target_reads(tmp_path):
    path = _write(
        tmp_path / "common" / "country_tag_aliases" / "00_tag_aliases.txt",
        "TST_alias = {\n\tglobal_event_target = TST_alias_target\n}\n",
    )

    set_paths, used_paths, cleared_paths = V.process_file_for_all_targets(
        (str(path), False, str(tmp_path))
    )

    assert set_paths == {}
    assert set(used_paths) == {"TST_alias_target"}
    assert cleared_paths == {}


def test_tag_alias_file_without_a_global_target_contributes_nothing(tmp_path):
    path = _write(
        tmp_path / "common" / "country_tag_aliases" / "00_tag_aliases.txt",
        "TST_alias = {\n\toriginal_tag = YEM\n}\n",
    )
    assert V.process_file_for_all_targets((str(path), False, str(tmp_path))) == (
        {},
        {},
        {},
    )


def test_event_target_scan_skips_non_script_directories(tmp_path):
    assert V.process_file_for_all_targets(
        (str(_skipped(tmp_path)), False, str(tmp_path))
    ) == (
        {},
        {},
        {},
    )


def test_event_target_scan_returns_nothing_for_an_empty_file(tmp_path):
    path = _write(tmp_path / "events" / "empty.txt", "")
    assert V.process_file_for_all_targets((str(path), False, str(tmp_path))) == (
        {},
        {},
        {},
    )


def test_localisation_reference_marks_a_target_used(tmp_path):
    path = _write(
        tmp_path / "localisation" / "english" / "tst_l_english.yml",
        'l_english:\n TST_key:0 "[TST_shown.GetName] speaks"\n',
    )

    found = V._scan_targets_in_loc((str(path), ("TST_shown", "TST_hidden")))

    assert found == {"TST_shown"}


def test_localisation_without_a_getter_reference_matches_nothing(tmp_path):
    path = _write(
        tmp_path / "localisation" / "english" / "tst_l_english.yml",
        'l_english:\n TST_key:0 "plain text"\n',
    )
    assert V._scan_targets_in_loc((str(path), ("TST_shown",))) == set()


def test_localisation_scan_skips_non_script_directories(tmp_path):
    path = _write(
        tmp_path / "gfx" / "tst_l_english.yml", 'l_english:\n a:0 "[x.GetName]"\n'
    )
    assert V._scan_targets_in_loc((str(path), ("x",))) == set()


def test_staged_target_scan_only_reads_staged_txt_files(tmp_path):
    txt = _write(
        tmp_path / "events" / "ev.txt",
        "save_event_target_as = TST_staged\n",
    )
    yml = _write(
        tmp_path / "localisation" / "english" / "a_l_english.yml", "l_english:\n"
    )

    set_paths, _used, _cleared = V.EventTargets.get_all_targets(
        str(tmp_path), staged_files=[str(txt), str(yml)], workers=1
    )

    assert set(set_paths) == {"TST_staged"}
