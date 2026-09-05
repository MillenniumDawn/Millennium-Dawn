"""Behavioural tests for check_common_mistakes' entry points and file-level checks.

check_common_mistakes_test.py drills the individual `_check_*` scanners with
hand-built line lists. This file covers what sits around them: check_file's
per-directory dispatch and its own inline rules, the reference scan and report
writer, and main()'s exit codes.
"""

import runpy
import sys

import check_common_mistakes as checker
import pytest


def _write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(content)


def _script(*lines):
    return "".join(line + "\n" for line in lines)


def _messages(tmp_path, rel, *lines):
    path = tmp_path / rel
    _write(path, _script(*lines))
    return [message for _fp, _line, message in checker.check_file(str(path))]


def _matching(messages, needle):
    return [message for message in messages if needle in message]


@pytest.fixture
def scoped_refs(monkeypatch):
    """Give one test its own view of the codebase-wide reference sets."""

    def _apply(focuses=(), decisions=(), nation_flags=()):
        monkeypatch.setattr(checker, "_SCRIPT_COMPLETED_FOCUSES", set(focuses))
        monkeypatch.setattr(checker, "_SCRIPT_COMPLETED_DECISIONS", set(decisions))
        monkeypatch.setattr(checker, "_REAL_NATION_FLAGS", set(nation_flags))

    _apply()
    return _apply


@pytest.fixture
def fake_mod_root(monkeypatch, tmp_path):
    """Point the cached common/ readers at an empty tree, then reset them."""
    cached = (
        checker._equipment_bonus_enum,
        checker._equipment_names,
        checker._decision_ids,
        checker._opinion_modifier_names,
        checker._static_modifier_names,
    )
    root = tmp_path / "modroot"
    root.mkdir()
    for function in cached:
        function.cache_clear()
    monkeypatch.setattr(checker, "_mod_root", lambda: str(root))
    yield root
    for function in cached:
        function.cache_clear()


# ---------------------------------------------------------------------------
# check_file — inline rules and per-directory dispatch
# ---------------------------------------------------------------------------


def test_percentage_ranges_are_flagged(tmp_path, scoped_refs):
    messages = _messages(
        tmp_path,
        "common/national_focus/TAG.txt",
        "focus = {",
        "\tid = TAG_focus",
        "\tavailable = {",
        "\t\tthreat > 40",
        "\t\thas_war_support > 50",
        "\t\thas_stability > 60",
        "\t}",
        "}",
    )

    assert _matching(messages, "threat > 40.0 looks like a percentage")
    assert _matching(messages, "has_war_support > 50 looks like a percentage")
    assert _matching(messages, "has_stability > 60 looks like a percentage")


def test_absolute_threat_effects_are_not_percentages(tmp_path, scoped_refs):
    messages = _messages(
        tmp_path,
        "common/national_focus/TAG.txt",
        "focus = {",
        "\tid = TAG_focus",
        "\tcompletion_reward = { add_threat = 3 }",
        "}",
    )

    assert not _matching(messages, "looks like a percentage")


def test_idea_file_rules(tmp_path, scoped_refs):
    messages = _messages(
        tmp_path,
        "common/ideas/MD_test_ideas.txt",
        "ideas = {",
        "\tcountry = {",
        "\t\tone_idea = {",
        "\t\t\tallowed = { always = no }",
        "\t\t\tallowed_civil_war = { always = no }",
        "\t\t\tcancel = { always = no }",
        "\t\t}",
        "\t\ttwo_idea = {",
        "\t\t\tallowed = { tag = USA }",
        "\t\t}",
        "\t\tthree_idea = {",
        "\t\t\tallowed = {",
        "\t\t\t\talways = no",
        "\t\t\t}",
        "\t\t}",
        "\t}",
        "}",
    )

    assert len(_matching(messages, "is the default for ideas in 'country'")) == 2
    assert _matching(messages, "allowed_civil_war = { always = no } has no effect")
    assert _matching(messages, "cancel = { always = no } is checked hourly")
    assert _matching(messages, "breaks for civil war split-offs")


def test_multi_line_allowed_block_with_real_conditions_is_kept(tmp_path, scoped_refs):
    messages = _messages(
        tmp_path,
        "common/ideas/MD_test_ideas.txt",
        "ideas = {",
        "\tcountry = {",
        "\t\tone_idea = {",
        "\t\t\tallowed = {",
        "\t\t\t\toriginal_tag = USA",
        "\t\t\t\talways = no",
        "\t\t\t}",
        "\t\t}",
        "\t}",
        "}",
    )

    assert not _matching(messages, "is the default for ideas in 'country'")


def test_selectable_idea_categories_are_not_flagged(tmp_path, scoped_refs):
    messages = _messages(
        tmp_path,
        "common/ideas/MD_test_ideas.txt",
        "ideas = {",
        "\tmobilization_laws = {",
        "\t\tone_idea = {",
        "\t\t\tallowed = { always = no }",
        "\t\t}",
        "\t}",
        "}",
    )

    assert not _matching(messages, "is the default for ideas in")


def test_focus_file_dispatch_covers_the_focus_only_checks(tmp_path, scoped_refs):
    messages = _messages(
        tmp_path,
        "common/national_focus/TAG.txt",
        "focus = {",
        "\tid = TAG_war",
        "\tavailable = { always = no }",
        "\tai_will_do = { factor = 5 }",
        "\tcompletion_reward = {",
        '\t\tlog = "[GetDateText]: Focus TAG_other"',
        "\t\tcreate_wargoal = { type = annex_everything target = USA }",
        "\t}",
        "}",
    )

    assert _matching(messages, "focus is permanently unreachable")
    assert _matching(messages, "no will_lead_to_war_with")
    assert _matching(messages, "log references Focus TAG_other")
    assert _matching(messages, "ai_will_do root-level 'factor ='")


def test_decision_file_dispatch_covers_the_decision_only_checks(tmp_path, scoped_refs):
    messages = _messages(
        tmp_path,
        "common/decisions/MD_test.txt",
        "test_category = {",
        "\tmy_decision = {",
        "\t\tfire_only_once = yes",
        "\t\tavailable = { always = no }",
        "\t\tallowed = { num_of_factories > 5 }",
        "\t\tcomplete_effect = {",
        '\t\t\tlog = "[GetDateText]: Decision other_decision"',
        "\t\t\tadd_political_power = 10",
        "\t\t}",
        "\t}",
        "}",
    )

    assert _matching(messages, "add visible = { always = no } for script-triggered")
    assert _matching(messages, "dynamic trigger 'num_of_factories'")
    assert _matching(messages, "log references Decision other_decision")


def test_event_file_dispatch_covers_the_event_only_checks(tmp_path, scoped_refs):
    messages = _messages(
        tmp_path,
        "events/MD_test_events.txt",
        "country_event = {",
        "\tid = test.1",
        "\toption = {",
        "\t\tname = test.1.a",
        '\t\tlog = "[GetDateText]: Event test.2"',
        "\t\tadd_political_power = 10",
        "\t}",
        "}",
    )

    assert _matching(messages, "log references Event test.2")


def test_political_leaders_file_dispatch(tmp_path, scoped_refs):
    messages = _messages(
        tmp_path,
        "common/scripted_effects/MD_TAG_political_leaders.txt",
        "set_leader_TAG = {",
        "\tif = {",
        "\t\tlimit = { check_variable = { ruling_party = 1 } }",
        "\t\tif = {",
        "\t\t\tlimit = { check_variable = { conservatism_leader = 0 } }",
        "\t\t\tadd_to_variable = { conservatism_leader = 2 }",
        "\t\t}",
        "\t}",
        "}",
    )

    assert _matching(messages, "advances the counter by 2")


def test_faction_and_arithmetic_rules(tmp_path, scoped_refs):
    messages = _messages(
        tmp_path,
        "common/scripted_effects/MD_test.txt",
        "test_effect = {",
        "\tif = {",
        "\t\tlimit = { is_in_faction = SOV }",
        "\t\tset_variable = { share = money_total/100 }",
        "\t}",
        "\tif = {",
        "\t\tlimit = { has_trade_agreement_with = USA }",
        "\t\tadd_political_power = 10",
        "\t}",
        "}",
    )

    assert _matching(messages, "use is_in_faction_with = SOV")
    assert _matching(messages, "has_trade_agreement_with is not a valid trigger")
    assert _matching(
        messages, "use multiplication instead of division (/ 100 -> * 0.01)"
    )


def test_redundant_or_and_and_wrappers_are_reported(tmp_path, scoped_refs):
    messages = _messages(
        tmp_path,
        "common/scripted_triggers/MD_test.txt",
        "test_trigger = {",
        "\tOR = {",
        "\t\thas_war = yes",
        "\t}",
        "\tAND = {",
        "\t\thas_civil_war = yes",
        "\t\thas_war = no",
        "\t}",
        "}",
    )

    assert _matching(messages, "redundant OR = { } wrapper")
    assert _matching(messages, "redundant AND = { } wrapper")


def test_provincial_building_checks_only_run_for_common_and_events(
    tmp_path, scoped_refs
):
    body = (
        "test_effect = {",
        "\tadd_building_construction = {",
        "\t\ttype = naval_base",
        "\t\tlevel = 1",
        "\t\tinstant_build = yes",
        "\t}",
        "}",
    )

    inside = _messages(tmp_path, "common/scripted_effects/MD_test.txt", *body)
    outside = _messages(tmp_path, "history/countries/TAG - Test.txt", *body)

    assert _matching(inside, "it is a provincial building")
    assert not _matching(outside, "it is a provincial building")


def test_check_file_ignores_a_path_it_cannot_read(tmp_path):
    directory = tmp_path / "common" / "unreadable.txt"
    directory.mkdir(parents=True)

    assert checker.check_file(str(directory)) == []


# ---------------------------------------------------------------------------
# _scan_global_refs / _files_need_global_refs
# ---------------------------------------------------------------------------


def test_scan_global_refs_collects_ids_from_the_scanned_directories(tmp_path):
    _write(
        tmp_path / "common" / "refs.txt",
        _script(
            "complete_national_focus = TAG_one",
            "unlock_national_focus = TAG_two",
            "activate_decision = TAG_decision",
            "set_country_flag = arab_nation_flag",
        ),
    )
    _write(
        tmp_path / "events" / "notes.md",
        _script("complete_national_focus = TAG_ignored"),
    )

    focuses, decisions, flags = checker._scan_global_refs(str(tmp_path))

    assert focuses == {"TAG_one", "TAG_two"}
    assert decisions == {"TAG_decision"}
    assert flags == {"arab_nation_flag"}


def test_scan_global_refs_survives_an_unreadable_file(tmp_path):
    common = tmp_path / "common"
    common.mkdir()
    _write(common / "good.txt", _script("complete_national_focus = TAG_one"))
    try:
        (common / "broken.txt").symlink_to(common / "no_such_target.txt")
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable on this platform")

    focuses, _decisions, _flags = checker._scan_global_refs(str(tmp_path))

    assert focuses == {"TAG_one"}


def test_files_need_global_refs_gate(tmp_path):
    plain = tmp_path / "common" / "plain.txt"
    _write(plain, _script("test_effect = { add_political_power = 10 }"))
    nation = tmp_path / "common" / "nation.txt"
    _write(nation, _script("test_trigger = { is_arab_nation = yes }"))
    gated = tmp_path / "common" / "national_focus" / "TAG.txt"
    _write(gated, _script("focus = { id = TAG_x available = { always = no } }"))

    assert not checker._files_need_global_refs([str(plain)])
    assert checker._files_need_global_refs([str(nation)])
    assert checker._files_need_global_refs([str(gated)])
    assert checker._files_need_global_refs([str(tmp_path / "gone.txt")])


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------


def _run_main(monkeypatch, tmp_path, *argv):
    monkeypatch.setattr(checker, "get_root_dir", lambda: str(tmp_path))
    monkeypatch.setattr(checker, "_SCRIPT_COMPLETED_FOCUSES", set())
    monkeypatch.setattr(checker, "_SCRIPT_COMPLETED_DECISIONS", set())
    monkeypatch.setattr(checker, "_REAL_NATION_FLAGS", set())
    monkeypatch.setattr(sys, "argv", [checker.__file__, *argv])
    return checker.main()


def test_main_passes_a_clean_file(tmp_path, monkeypatch, capsys):
    path = tmp_path / "common" / "clean.txt"
    _write(path, _script("test_effect = { add_political_power = 10 }"))

    assert _run_main(monkeypatch, tmp_path, str(path)) == 0

    assert "Check PASSED" in capsys.readouterr().out


def test_main_reports_issues_and_exits_nonzero(tmp_path, monkeypatch, capsys):
    path = tmp_path / "common" / "dirty.txt"
    _write(path, _script("test_trigger = { is_at_war = yes }"))

    assert _run_main(monkeypatch, tmp_path, str(path)) == 1

    out = capsys.readouterr().out
    assert "is_at_war is not a HOI4 trigger" in out
    assert "Found 1 issue(s)" in out


def test_main_writes_a_report_and_a_json_sidecar(tmp_path, monkeypatch):
    path = tmp_path / "common" / "dirty.txt"
    _write(path, _script("test_trigger = { is_at_war = yes }"))
    output = tmp_path / "report.log"

    assert _run_main(monkeypatch, tmp_path, str(path), "--output", str(output)) == 1

    report = output.read_text(encoding="utf-8")
    assert "✗ VALIDATION COMPLETE - 1 ERROR(S) - 0 WARNING(S)" in report
    sidecar = (tmp_path / "report.json").read_text(encoding="utf-8")
    assert '"category": "common-mistakes"' in sidecar
    assert '"line": 1' in sidecar


def test_main_reports_an_empty_run(tmp_path, monkeypatch, capsys):
    output = tmp_path / "report.log"

    assert _run_main(monkeypatch, tmp_path, "--output", str(output)) == 0

    assert "No files to check" in capsys.readouterr().out
    assert "0 ERROR(S)" in output.read_text(encoding="utf-8")
    assert (tmp_path / "report.json").read_text(encoding="utf-8") == "[]"


def test_main_writes_no_report_without_the_output_flag(tmp_path, monkeypatch, capsys):
    assert _run_main(monkeypatch, tmp_path) == 0

    assert "No files to check" in capsys.readouterr().out
    assert list(tmp_path.iterdir()) == []


def test_main_scans_the_tree_when_a_targeted_file_needs_the_reference_sets(
    tmp_path, monkeypatch, capsys
):
    focus = tmp_path / "common" / "national_focus" / "TAG.txt"
    _write(
        focus,
        _script(
            "focus = {",
            "\tid = TAG_locked",
            "\tavailable = { always = no }",
            "}",
        ),
    )
    _write(
        tmp_path / "common" / "unlockers.txt",
        _script("test_effect = { complete_national_focus = TAG_locked }"),
    )

    assert _run_main(monkeypatch, tmp_path, str(focus)) == 0

    assert "scan global refs" in capsys.readouterr().err


def test_main_skips_the_tree_scan_for_files_that_cannot_need_it(
    tmp_path, monkeypatch, capsys
):
    path = tmp_path / "common" / "clean.txt"
    _write(path, _script("test_effect = { add_political_power = 10 }"))

    assert _run_main(monkeypatch, tmp_path, str(path)) == 0

    assert "scan global refs (skipped)" in capsys.readouterr().err


def test_main_walks_the_whole_tree_in_all_mode(tmp_path, monkeypatch, capsys):
    _write(
        tmp_path / "common" / "dirty.txt", _script("test_trigger = { is_at_war = yes }")
    )

    assert _run_main(monkeypatch, tmp_path, "--mode", "all") == 1

    assert "Checking 1 files for common mistakes" in capsys.readouterr().out


def test_script_entry_point_exits_with_the_finding_count(tmp_path, monkeypatch):
    path = tmp_path / "common" / "dirty.txt"
    _write(path, _script("test_trigger = { is_at_war = yes }"))
    monkeypatch.setattr(sys, "argv", [checker.__file__, str(path)])

    with pytest.raises(SystemExit) as excinfo:
        runpy.run_path(checker.__file__, run_name="__main__")

    assert excinfo.value.code == 1


def test_targeted_mode_recognises_every_scoping_flag():
    class Args:
        filenames = None
        files = None
        mode = "all"

    assert not checker._targeted_mode(Args())
    Args.mode = "staged"
    assert checker._targeted_mode(Args())
    Args.mode = "all"
    Args.files = ["a.txt"]
    assert checker._targeted_mode(Args())


# ---------------------------------------------------------------------------
# focus / decision availability gates
# ---------------------------------------------------------------------------


def _focus_lines(*extra):
    return [
        "\n",
        "focus = {\n",
        "\tid = TAG_locked\n",
        "\tavailable = { always = no }\n",
        *extra,
        "}\n",
    ]


def test_unreachable_focus_is_flagged(scoped_refs):
    assert len(checker._check_focus_available_always_no(_focus_lines())) == 1


def test_focus_with_a_bypass_is_reachable(scoped_refs):
    lines = _focus_lines("\tbypass = { has_war = yes }\n")

    assert checker._check_focus_available_always_no(lines) == []


def test_focus_completed_by_script_is_reachable(scoped_refs):
    scoped_refs(focuses={"TAG_locked"})

    assert checker._check_focus_available_always_no(_focus_lines()) == []


def _decision_lines(*decision_body):
    return [
        "\n",
        "test_category = {\n",
        "\n",
        "\tmy_decision = {\n",
        "\t\tfire_only_once = yes\n",
        "\t\tavailable = { always = no }\n",
        *decision_body,
        "\t}\n",
        "}\n",
    ]


def test_unreachable_decision_is_flagged(scoped_refs):
    assert len(checker._check_decision_available_always_no(_decision_lines())) == 1


@pytest.mark.parametrize(
    "escape",
    ["\t\tvisible = { always = no }\n", "\t\tdays_mission_timeout = 30\n"],
)
def test_decision_with_a_completion_mechanism_is_kept(scoped_refs, escape):
    assert checker._check_decision_available_always_no(_decision_lines(escape)) == []


def test_decision_activated_by_script_is_kept(scoped_refs):
    scoped_refs(decisions={"my_decision"})

    assert checker._check_decision_available_always_no(_decision_lines()) == []


def test_block_without_a_decision_marker_is_not_a_decision(scoped_refs):
    lines = [
        "test_category = {\n",
        "\tnot_a_decision = {\n",
        "\t\tavailable = { always = no }\n",
        "\t}\n",
        "}\n",
    ]

    assert checker._check_decision_available_always_no(lines) == []


# ---------------------------------------------------------------------------
# log-only blocks and is_X_nation
# ---------------------------------------------------------------------------


def test_log_only_option_and_complete_effect_are_flagged():
    lines = [
        "\toption = {\n",
        '\t\tlog = "[GetDateText]: Event test.1 Option a"\n',
        "\t}\n",
        "\tcomplete_effect = {\n",
        "\t\t# a comment does not count as content\n",
        '\t\tlog = "[GetDateText]: Decision my_decision"\n',
        "\t}\n",
    ]

    issues = checker._check_empty_log_only_blocks(lines)

    assert [message.split(" -- ")[0] for _line, message in issues] == [
        'log = "..." is the only content in this option block',
        'log = "..." is the only content in this complete_effect block',
    ]


def test_log_beside_a_real_effect_is_kept():
    lines = [
        "\toption = {\n",
        '\t\tlog = "[GetDateText]: Event test.1 Option a"\n',
        "\t\tadd_political_power = 10\n",
        "\t}\n",
    ]

    assert checker._check_empty_log_only_blocks(lines) == []


def test_is_x_nation_flagged_only_when_a_real_flag_exists(scoped_refs):
    lines = ["\tavailable = { is_arab_nation = yes }\n"]

    assert checker._check_is_x_nation_runtime(lines) == []

    scoped_refs(nation_flags={"arab_nation_flag"})
    issues = checker._check_is_x_nation_runtime(lines)

    assert len(issues) == 1
    assert "has_country_flag = arab_nation_flag" in issues[0][1]


def test_is_x_nation_is_free_inside_an_allowed_block(scoped_refs):
    scoped_refs(nation_flags={"arab_nation_flag"})
    lines = [
        "\tallowed = {\n",
        "\t\tis_arab_nation = yes\n",
        "\t}\n",
    ]

    assert checker._check_is_x_nation_runtime(lines) == []


def test_is_x_nation_is_free_at_the_flag_definition_site(scoped_refs):
    scoped_refs(nation_flags={"arab_nation_flag"})
    lines = [
        "\tif = {\n",
        "\t\tlimit = { is_arab_nation = yes }\n",
        "\t\tset_country_flag = arab_nation_flag\n",
        "\t}\n",
    ]

    assert checker._check_is_x_nation_runtime(lines) == []


def test_is_x_nation_is_free_where_the_triggers_are_defined(scoped_refs):
    scoped_refs(nation_flags={"arab_nation_flag"})
    lines = ["\tis_arab_nation = yes\n"]

    assert (
        checker._check_is_x_nation_runtime(
            lines, "common\\scripted_triggers\\MD_nations.txt"
        )
        == []
    )


def test_percentages_below_one_are_left_alone(tmp_path, scoped_refs):
    messages = _messages(
        tmp_path,
        "common/national_focus/TAG.txt",
        "focus = {",
        "\tid = TAG_focus",
        "\tavailable = {",
        "\t\tthreat > 0.4",
        "\t\thas_war_support > 0.5",
        "\t}",
        "}",
    )

    assert not _matching(messages, "looks like a percentage")


def test_worker_initialiser_publishes_the_reference_sets(scoped_refs):
    checker._init_worker({"TAG_focus"}, {"a_decision"}, {"arab_nation_flag"})

    assert checker._SCRIPT_COMPLETED_FOCUSES == {"TAG_focus"}
    assert checker._SCRIPT_COMPLETED_DECISIONS == {"a_decision"}
    assert checker._REAL_NATION_FLAGS == {"arab_nation_flag"}


# ---------------------------------------------------------------------------
# Robustness: malformed script must not derail a scanner
# ---------------------------------------------------------------------------


def test_stray_closing_brace_is_absorbed_by_every_brace_scanner():
    lines = ["}\n"]

    assert checker._check_mutually_exclusive_contradictions(lines) == []
    assert checker._check_has_idea_mutex_in_not_block(lines) == []
    assert checker._check_country_exists_scope_contradiction(lines) == []
    assert checker._check_consecutive_scope_blocks(lines) == []


def test_stray_closing_brace_still_leaves_an_embargo_unguarded():
    lines = ["}\n", "\tsend_embargo = { target = USA }\n"]

    issues = checker._check_embargo_dlc_guard(lines)

    assert len(issues) == 1
    assert 'without has_dlc = "By Blood Alone" guard' in issues[0][1]


def test_a_dlc_check_outside_every_block_guards_nothing():
    lines = [
        'has_dlc = "By Blood Alone"\n',
        "send_embargo = { target = USA }\n",
    ]

    assert len(checker._check_embargo_dlc_guard(lines)) == 1


def test_unterminated_while_loop_still_reports_max_iterations():
    lines = ["\twhile_loop_effect = {\n", "\t\tmax_iterations = 10\n"]

    assert len(checker._check_while_loop_max_iterations(lines)) == 1


def test_while_loop_without_max_iterations_is_clean():
    lines = [
        "\twhile_loop_effect = {\n",
        "\t\tbreak = loop_done\n",
        "\t}\n",
    ]

    assert checker._check_while_loop_max_iterations(lines) == []


def test_unterminated_else_still_reports_its_limit():
    lines = ["\telse = {\n", "\t\tlimit = { has_war = yes }\n"]

    assert len(checker._check_else_with_limit(lines)) == 1


# ---------------------------------------------------------------------------
# Scanners with no coverage from the line-list suite
# ---------------------------------------------------------------------------


def test_nor_is_flagged_but_only_as_a_block_opener():
    assert len(checker._check_nor_block(["\tNOR = { has_war = yes }\n"])) == 1
    assert checker._check_nor_block(["\t# NOR = { has_war = yes }\n"]) == []
    assert checker._check_nor_block(["\tNORMANDY_flag = yes\n"]) == []


def test_max_iterations_inside_a_while_loop_is_flagged():
    lines = [
        "\twhile_loop_effect = {\n",
        "\t\tbreak = loop_done\n",
        "\t\tmax_iterations = 10\n",
        "\t}\n",
    ]

    issues = checker._check_while_loop_max_iterations(lines)

    assert [line for line, _msg in issues] == [3]
    assert "bound the loop with its break variable" in issues[0][1]


def test_var_index_shorthand_is_flagged_outside_comments():
    assert (
        len(checker._check_var_index_shorthand(["\tset_variable = { x = var:a^i }\n"]))
        == 1
    )
    assert checker._check_var_index_shorthand(["\t# var:a^i\n"]) == []
    assert checker._check_var_index_shorthand(["\tset_variable = { x = 1 }\n"]) == []


def test_display_only_country_loops_are_exempt():
    lines = [
        "every_country = {\n",
        "\tlimit = { has_idea = NATO_member }\n",
        "\tdisplay_individual_scopes = yes\n",
        "}\n",
    ]

    assert checker._check_every_country_member_array(lines) == []


def test_any_country_over_two_blocs_is_told_to_split():
    lines = [
        "any_country = {\n",
        "\thas_idea = EU_member\n",
        "\thas_idea = NATO_member\n",
        "}\n",
    ]

    issues = checker._check_any_country_member_array(lines)

    assert len(issues) == 1
    assert "use one any_of_scopes per array" in issues[0][1]


def test_a_malformed_clamp_minimum_is_not_a_zero_guard():
    lines = [
        "\tclamp_variable = { var = my_var min = . max = 5 }\n",
        "\tdivide_variable = { total = my_var }\n",
    ]

    issues = checker._check_divide_variable_zero_guard(lines)

    assert len(issues) == 1
    assert "divide_variable by 'my_var'" in issues[0][1]


def test_a_malformed_set_variable_literal_is_not_an_initialisation():
    lines = [
        "\tset_variable = { my_var = .. }\n",
        "\tdivide_variable = { total = my_var }\n",
    ]

    assert len(checker._check_divide_variable_zero_guard(lines)) == 1


def test_a_gateless_dlc_check_guards_its_own_block():
    lines = [
        "\tsome_block = {\n",
        '\t\thas_dlc = "By Blood Alone"\n',
        "\t\tsend_embargo = { target = USA }\n",
        "\t}\n",
    ]

    assert checker._check_embargo_dlc_guard(lines) == []


def test_a_non_blank_line_between_scope_blocks_blocks_the_merge_hint():
    lines = [
        "\t\tSOV = {\n",
        "\t\t\tadd_stability = 0.05\n",
        "\t\t}\n",
        "\t\t\tadd_war_support = 0.05\n",
        "\t\tSOV = {\n",
        "\t\t\tadd_stability = 0.05\n",
        "\t\t}\n",
    ]

    assert checker._check_consecutive_scope_blocks(lines) == []


def test_decision_traversal_skips_blank_and_markerless_blocks():
    lines = [
        "\n",
        "test_category = {\n",
        "\n",
        "\tnot_a_decision = {\n",
        "\t\tallowed = { has_opinion = { target = USA value > 50 } }\n",
        "\t}\n",
        "\tmy_decision = {\n",
        "\t\tfire_only_once = yes\n",
        "\t\tallowed = { has_army_size = { size > 10 } }\n",
        "\t}\n",
        "}\n",
    ]

    issues = checker._check_decision_allowed_dynamic(lines)

    assert len(issues) == 1
    assert "dynamic trigger 'has_army_size'" in issues[0][1]


def test_focus_log_check_needs_an_id_to_compare_against():
    lines = [
        "\n",
        "focus = {\n",
        '\tlog = "[GetDateText]: Focus TAG_other"\n',
        "}\n",
    ]

    assert checker._check_focus_log_id(lines) == []


def test_decision_log_check_skips_a_malformed_block_header():
    lines = [
        "test_category = {\n",
        "\tsome thing = {\n",
        '\t\tlog = "[GetDateText]: Decision other_decision"\n',
        "\t}\n",
        "}\n",
    ]

    assert checker._check_decision_log_id(lines) == []


def test_event_log_check_needs_an_id_and_an_option_name():
    without_id = [
        "\n",
        "country_event = {\n",
        "\toption = {\n",
        '\t\tlog = "[GetDateText]: Event other.1"\n',
        "\t}\n",
        "}\n",
    ]
    without_option_name = [
        "country_event = {\n",
        "\tid = test.1\n",
        "\toption = {\n",
        '\t\tlog = "[GetDateText]: Event other.1"\n',
        "\t}\n",
        "}\n",
    ]

    assert checker._check_event_log_id(without_id) == []
    assert checker._check_event_log_id(without_option_name) == []


def test_explode_braces_keeps_the_tail_after_the_last_brace():
    assert checker._explode_braces("option = { base = 5 } # note") == [
        "option = {",
        " base = 5 }",
        " # note",
    ]


def test_scope_classification_exempts_a_proxy_war_and_an_untagged_focus():
    lines = [
        "\n",
        "focus = {\n",
        "\tid = generic_focus\n",
        "\tavailable = { NOT = { has_war = yes } }\n",
        "\tcompletion_reward = {\n",
        "\t\tvar:my_ally = { declare_war_on = ROOT }\n",
        "\t}\n",
        "}\n",
    ]

    assert checker._check_focus_missing_war_hint(lines) == []


def test_war_hint_names_an_unidentified_focus():
    lines = [
        "focus = {\n",
        "\tcompletion_reward = { declare_war_on = USA }\n",
        "}\n",
    ]

    issues = checker._check_focus_missing_war_hint(lines)

    assert len(issues) == 1
    assert "Focus <unknown> has create_wargoal" in issues[0][1]


# ---------------------------------------------------------------------------
# AI-chance classification for the bankruptcy fallback check
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "body",
    [
        "modifier = { NOT = { has_war = yes } factor = 0 }",
        "factor = 0 is_historical_focus_on = yes",
        "modifier = { factor = 0 is_historical_focus_on = yes stray }",
        "modifier = { add = abc is_historical_focus_on = yes }",
        "modifier = { add = -1 is_historical_focus_on = yes }",
        "modifier = { has_war = yes factor = 0 }",
        "modifier = { factor = 0 }",
    ],
)
def test_unclassifiable_ai_modifiers_report_none(body):
    assert checker._ai_zero_modifier_conditions([body]) == ("none", False)


def test_bankruptcy_zero_is_classified():
    block = [
        "modifier = { factor = 0 has_active_mission = bankruptcy_incoming_collapse }"
    ]

    assert checker._ai_zero_modifier_conditions(block) == ("zero", True)


def test_event_fallback_check_tolerates_options_it_cannot_classify():
    lines = [
        "\n",
        "country_event = {\n",
        "\tid = test.1\n",
        "\toption = {\n",
        "\t\tname = test.1.a\n",
        "\t\ttrigger = { has_war = yes }\n",
        "\t\tai_chance = {\n",
        "\t\t\tbase = 1\n",
        "\t\t\tmodifier = { factor = 0 }\n",
        "\t\t}\n",
        "\t}\n",
        "}\n",
        "country_event = {\n",
        "\toption = { name = other.1.a }\n",
        "}\n",
    ]

    assert checker._check_event_ai_historical_bankruptcy_fallback(lines) == []


# ---------------------------------------------------------------------------
# Definition lookups under common/
# ---------------------------------------------------------------------------


def test_provincial_building_types_read_only_the_txt_files_it_can_open(tmp_path):
    buildings = tmp_path / "common" / "buildings"
    _write(
        buildings / "00_buildings.txt",
        _script(
            "buildings = {",
            "\tnaval_base = {",
            "\t\tlevel_cap = { province_max = 5 }",
            "\t}",
            "\tinfrastructure = {",
            "\t\tlevel_cap = { state_max = 5 }",
            "\t}",
            "}",
        ),
    )
    _write(buildings / "notes.md", "not a buildings file\n")
    (buildings / "a_directory.txt").mkdir()

    assert checker._provincial_building_types(str(tmp_path)) == frozenset(
        {"naval_base"}
    )


def test_missing_common_directories_disable_the_definition_checks(fake_mod_root):
    bonus = [
        "\tadd_equipment_bonus = {\n",
        "\t\tbonus = { not_a_real_bonus_type = 0.1 }\n",
        "\t}\n",
    ]

    issues = checker._check_equipment_bonus(bonus)

    assert len(issues) == 1
    assert "has no name = <loc key>" in issues[0][1]
    assert (
        checker._check_equipment_type_defined(
            ["\tadd_equipment_to_stockpile = { type = made_up_gun amount = 1 }\n"]
        )
        == []
    )
    assert (
        checker._check_active_decision_defined(
            ["\thas_active_decision = made_up_decision\n"]
        )
        == []
    )
    assert (
        checker._check_modifier_ref_defined(
            [
                "\tadd_opinion_modifier = { target = USA modifier = made_up }\n",
                "\tadd_relation_modifier = { target = USA modifier = made_up }\n",
            ]
        )
        == []
    )


def test_definition_lookups_skip_entries_they_cannot_use(fake_mod_root):
    _write(
        fake_mod_root / "common" / "script_enums.txt",
        _script("script_enum_some_other_thing = {", "\tvalue", "}"),
    )
    equipment = fake_mod_root / "common" / "units" / "equipment"
    _write(
        equipment / "infantry.txt",
        _script(
            "equipments = {",
            "\treal_gun = {",
            "\t\tyear = 2000",
            "\t}",
            "\tduplicate_archetypes = {",
            "\t\tclone_without_a_base = {",
            "\t\t\tyear = 2000",
            "\t\t}",
            "\t}",
            "}",
        ),
    )
    (equipment / "a_directory.txt").mkdir()

    assert checker._equipment_bonus_enum() is None
    assert checker._equipment_names() == frozenset({"real_gun", "duplicate_archetypes"})


def test_equipment_effect_without_a_type_is_ignored():
    assert (
        checker._check_equipment_type_defined(
            ["\tadd_equipment_to_stockpile = { amount = 100 }\n"]
        )
        == []
    )


# ---------------------------------------------------------------------------
# Leader rotation tree walking
# ---------------------------------------------------------------------------


def test_rotation_walker_tolerates_incomplete_branches():
    lines = [
        "other_effect = {\n",
        "\tadd_political_power = 1\n",
        "}\n",
        "set_leader_TST = {\n",
        "\tclr_country_flag = temp_flag\n",
        "\tif = {\n",
        "\t\tadd_political_power = 1\n",
        "\t}\n",
        "\tif = {\n",
        "\t\tlimit = { has_country_flag = set_conservatism date > 2010.1.1 }\n",
        "\t\tif = {\n",
        "\t\t\tadd_political_power = 1\n",
        "\t\t}\n",
        "\t\tif = {\n",
        "\t\t\tlimit = { check_variable = { b = 1 } check_variable = { conservatism_leader = 0 } }\n",
        "\t\t\tadd_to_variable = { conservatism_leader = step_size }\n",
        '\t\t\tcreate_country_leader = { name = "L" traits = { some_trait } }\n',
        "\t\t\tif = {\n",
        "\t\t\t\tadd_political_power = 1\n",
        "\t\t\t}\n",
        "\t\t\tif = {\n",
        "\t\t\t\tlimit = { has_war = yes }\n",
        "\t\t\t\tadd_political_power = 1\n",
        "\t\t\t}\n",
        "\t\t}\n",
        "\t}\n",
        "}\n",
    ]

    assert checker._check_leader_rotation(lines) == []
