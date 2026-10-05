"""Edge cases for the validate_variables pool workers and scan helpers.

Every worker runs in a forked process over whatever the repo actually holds, so
the failure mode that matters is a worker that raises, hangs, or invents a
finding on input it cannot parse: a skipped path, a file it may not read, an
unbalanced brace, a stray quote. Each case here pins "degrade to no finding"
rather than the crash or false positive.
"""

import os
import re

import pytest
import validate_variables as V
from shared.suite import variable_scan
from shared.suite import write_text as _write


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


def test_flag_scan_returns_nothing_for_an_empty_file(tmp_path):
    path = _write(tmp_path / "common" / "scripted_effects" / "empty.txt", "")
    assert V.process_file_for_all_flags(
        (str(path), False, "country", str(tmp_path))
    ) == (
        {},
        {},
        {},
    )


def test_flag_pass_scans_only_the_supported_flag_types(tmp_path):
    path = _write(
        tmp_path / "common" / "scripted_effects" / "flags.txt",
        "set_country_flag = TST_c\nset_character_flag = TST_ch\n",
    )

    flags, _targets = V.process_file_for_flags_and_targets((str(path), str(tmp_path)))

    assert list(flags) == ["country", "global", "state"]


# --- set_*_flag syntax -----------------------------------------------------


def test_flag_syntax_reports_days_without_value_and_long_form(tmp_path):
    path = _write(
        tmp_path / "common" / "scripted_effects" / "syntax.txt",
        "flag_demo = {\n"
        "\tset_country_flag = { flag = TST_timed days = 30 }\n"
        "\tset_global_flag = { flag = TST_long_form }\n"
        "}\n",
    )

    days, long_form = variable_scan(path, "flag_syntax", tmp_path)

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
    assert variable_scan(path, "flag_syntax", tmp_path) == ([], [])


def test_dynamic_flag_matcher_only_expands_scope_substitutions():
    patterns = V.Validator._build_dynamic_flag_matchers(
        ["accords_@ROOT_left", "trade_agreement@USA", "plain_flag"]
    )

    assert len(patterns) == 1
    assert patterns[0].match("accords_MOR_left")
    assert patterns[0].match("accords_MOR_CW_0_left")
    assert not patterns[0].match("accords_lowercase_left")


# --- shared scan on a path it cannot read -----------------------------------

_SHARED_SECTION_EMPTY = {
    "math": [],
    "orphan": [],
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


def test_clamp_harvest_survives_an_unreadable_path(tmp_path):
    assert V.collect_clamp_ranges((str(_unreadable(tmp_path)), str(tmp_path))) == (
        [],
        [],
        [],
    )


# --- available-block scanning ----------------------------------------------


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

    assert variable_scan(path, "available", tmp_path) == []


def test_scripted_trigger_body_with_a_stray_close_brace():
    assert V._scripted_trigger_body_has_unwrapped_global_flag("} has_global_flag = x")


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

    issues = variable_scan(
        path, "scripted", tmp_path, flagged_names=frozenset({"tst_border_available"})
    )

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


def test_variable_write_without_a_target_is_ignored(tmp_path):
    path = _write(
        tmp_path / "common" / "national_focus" / "focus.txt",
        "my_focus = {\n\tcompletion_reward = {\n\t\tadd_to_variable = { }\n\t}\n}\n",
    )

    backing = {"TST_pp": ("political_power_factor",)}
    assert variable_scan(path, "missing", tmp_path, backing=backing) == []


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


def test_treasury_scan_skips_files_without_a_money_effect(tmp_path):
    path = _write(
        tmp_path / "common" / "national_focus" / "focus.txt",
        "my_focus = {\n\tcompletion_reward = {\n\t\tadd_stability = 0.05\n\t}\n}\n",
    )
    assert variable_scan(path, "treasury", tmp_path) == []


def test_treasury_scan_survives_a_stray_close_brace(tmp_path):
    path = _write(
        tmp_path / "common" / "national_focus" / "focus.txt",
        "}\nmodify_treasury_effect = yes\n",
    )
    assert variable_scan(path, "treasury", tmp_path) == []


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


def test_orphan_money_scan_skips_files_without_a_setter(tmp_path):
    path = _write(
        tmp_path / "events" / "ev.txt",
        "country_event = {\n\tid = tst.1\n\toption = {\n\t\tname = tst.1.a\n\t}\n}\n",
    )
    consumers = {"treasury_change": frozenset()}
    assert variable_scan(path, "orphan", tmp_path, consumer_map=consumers) == []


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

    assert variable_scan(path, "orphan", tmp_path, consumer_map=MONEY_CONSUMERS) == []


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

    assert variable_scan(path, "orphan", tmp_path, consumer_map=MONEY_CONSUMERS) == []


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


def test_localisation_scan_finds_every_reference_form_outside_comments(tmp_path):
    path = _write(
        tmp_path / "localisation" / "english" / "tst_l_english.yml",
        "l_english:\n"
        ' a:0 "[TST_A.GetName] [event_target:TST_B.GetAdjective]"\n'
        ' b:0 "[TST_C.GetAdjective] [Event_Target:tst_d.getname]"\n'
        ' # c:0 "[TST_E.GetName]"\n',
    )
    targets = ("TST_A", "TST_B", "TST_C", "TST_D", "TST_E", "TST_F")

    found = V._scan_targets_in_loc((str(path), targets))

    assert found == {"TST_A", "TST_B", "TST_C", "TST_D"}


# --- flag and target pass --------------------------------------------------


def _flag_fixture(tmp_path):
    for name, flag in (("a", "TST_one"), ("b", "TST_two")):
        _write(
            tmp_path / "common" / "scripted_effects" / f"{name}.txt",
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


# --- shared per-file indexes -----------------------------------------------


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
    "odd openers": "ab = { x.y = { 1.5={ } } a = bc = { } = { } }",
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


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_treasury_scan_reports_the_first_and_last_line(tmp_path, newline):
    lines = [
        "random_owned_state = { modify_treasury_effect = yes }",
        "TAG = { every_state = { owner = { modify_treasury_effect = yes } } }",
        "every_state = {",
        "modify_treasury_effect = yes }",
    ]
    path = _write(tmp_path / "events" / "ev.txt", newline.join(lines))

    issues = variable_scan(path, "treasury", tmp_path)

    assert [
        (line, "random_owned_state" in message) for message, _rel, line in issues
    ] == [
        (1, True),
        (4, False),
    ]


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


# --- mod-relative skip rules -----------------------------------------------

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
    "orphan money": (
        "events/h.txt",
        "option = {\n\tset_temp_variable = { treasury_change = 5 }\n}\n",
        lambda f, m: variable_scan(f, "orphan", m, consumer_map=MONEY_CONSUMERS),
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
    path = _write(mod / rel, content)

    assert scan(str(path), str(mod))


@pytest.mark.parametrize(
    "rel, content, scan", _SKIP_RULE_CASES.values(), ids=_SKIP_RULE_CASES.keys()
)
def test_workers_skip_non_script_directories(tmp_path, rel, content, scan):
    """Content the test above shows yields a result once it is read."""
    path = _write(tmp_path / "gfx" / os.path.basename(rel), content)

    assert not scan(str(path), str(tmp_path))
