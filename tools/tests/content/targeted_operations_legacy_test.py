import operator
import re

import pytest
from targeted_operations_model_test import (
    _extract_block,
    _named_block,
    _parse_race_script,
)
from targeted_operations_redesign_test import read as source

IRAQ = tuple(
    zip(
        ("saddam", "qusay", "uday", "abid", "majid", "walter", "tilfah", "salih"),
        range(56, 64),
    )
)


def event(event_id, path):
    text = source(path)
    marker = re.search(rf"(?m)^\s*id\s*=\s*{re.escape(event_id)}\b", text)
    assert marker
    start = text.rfind("\ncountry_event = {", 0, marker.start()) + 1
    return _extract_block(text, start)


def enabled_branch(text):
    branch = _named_block(text, "if")
    assert "TOP_enabled = yes" in _named_block(branch, "limit")
    return branch


def test_startup_caches_targeted_operations_rule_in_country_scope():
    startup = _named_block(source("common/on_actions/00_on_actions.txt"), "on_startup")
    statements = _parse_race_script(startup)["on_startup"]
    effect = next(body for key, _, body in statements if key == "effect")
    country = next(body for key, _, body in effect if key == "ABK")
    assert country[0] == ("TOP_cache_game_rule", "=", "yes")
    assert not any(key == "TOP_cache_game_rule" for key, _, _ in effect)
    assert "TOP_cache_game_rule" not in source(
        "common/on_actions/999_game_rules_on_actions.txt"
    )


def test_ct_ledger_preserves_main_navigation_and_explicit_top_access():
    missiles_gui = _named_block(
        source("common/scripted_guis/00_missiles_scripted_guis.txt"), "MD_missiles_gui"
    )
    triggers = _named_block(missiles_gui, "triggers")
    gate = _named_block(triggers, "ct_gui_ledger_button_click_enabled")
    eligibility = _named_block(gate, "OR")
    for token in (
        "no_jihadist_government = yes",
        "TOP_country_eligible = yes",
        "TOP_security_country_eligible = yes",
    ):
        assert token in eligibility

    effects = _named_block(missiles_gui, "effects")
    ct_click = _named_block(effects, "ct_gui_ledger_button_click")
    assert "set_variable = { var_open_MD_CT_gui = 2 }" in ct_click
    top_navigation = _named_block(ct_click, "if")
    assert "TOP_enabled = yes" in _named_block(top_navigation, "limit")
    legacy_navigation = _named_block(top_navigation.partition("{")[2], "if")
    legacy_gate = _named_block(legacy_navigation, "limit")
    ct_gui = _named_block(
        source("common/scripted_guis/00_missiles_scripted_guis.txt"), "MD_CT_system_gui"
    )
    ct_visibility = _named_block(ct_gui, "visible")
    for condition in (
        "NOT = { salafist_caliphate_are_in_power = yes }",
        "NOT = { salafist_caliphate_are_in_coalition = yes }",
    ):
        assert condition in legacy_gate
        assert condition in ct_visibility
    assert "TOP_open_dossiers = yes" not in legacy_navigation
    for token in (
        "set_variable = { TOP_open = 0 }",
        "set_variable = { TOP_security_open = 0 }",
        "TOP_refresh_view = yes",
    ):
        assert token in legacy_navigation
    assert "TOP_open_dossiers = yes" in _named_block(top_navigation, "else")

    assert "TOP_open_dossiers = yes" in _named_block(
        _named_block(ct_gui, "effects"), "TOP_open_button_click"
    )

    open_dossiers = _named_block(
        source("common/scripted_effects/01_targeted_operations_view.txt"),
        "TOP_open_dossiers",
    )
    for token in (
        "set_variable = { TOP_open = 1 }",
        "set_variable = { TOP_security_open = 0 }",
        "set_variable = { TOP_tab = 0 }",
        "set_variable = { var_open_MD_CT_gui = 2 }",
        "TOP_build_view = yes",
    ):
        assert token in open_dossiers


def test_dossiers_button_is_above_the_counter_terror_hitboxes():
    windows = _parse_race_script(source("interface/MD_countrymissilesview.gui"))[
        "guiTypes"
    ]
    ct_window = next(
        body
        for kind, _, body in windows
        if kind == "containerWindowType"
        and ("name", "=", '"MD_CT_system_window"') in body
    )
    kind, _, button = ct_window[-1]
    assert kind == "buttonType"
    assert ("name", "=", '"TOP_open_button"') in button
    actions = next(
        body
        for kind, _, body in ct_window
        if kind == "containerWindowType"
        and ("name", "=", '"counter_terror_int_actions"') in body
    )
    labels = [body for kind, _, body in actions if kind == "instantTextboxType"]
    assert len(labels) == 3
    assert all(("maxHeight", "=", "20") in label for label in labels)


def test_dossiers_window_is_screen_level_and_scoped_to_counter_terror():
    gui = _named_block(
        source("common/scripted_guis/01_targeted_operations_gui.txt"),
        "TOP_dossiers_gui",
    )
    fields = {
        key: value for key, _, value in _parse_race_script(gui)["TOP_dossiers_gui"]
    }
    assert fields["context_type"] == "player_context"
    assert fields["window_name"] == "TOP_window"
    assert fields["dirty"] == "TOP_dirty"
    assert not {
        "parent_window_name",
        "parent_window_token",
        "parent_scripted_gui",
    }.intersection(fields)
    assert fields["visible"] == [
        ("TOP_enabled", "=", "yes"),
        ("has_country_flag", "=", "open_MD_countrymissilesview"),
        ("check_variable", "=", [("var_open_MD_CT_gui", "=", "2")]),
        ("check_variable", "=", [("TOP_open", "=", "1")]),
    ]

    windows = _parse_race_script(source("interface/targeted_operations.gui"))[
        "guiTypes"
    ]
    window = next(
        body
        for kind, _, body in windows
        if kind == "containerWindowType" and ("name", "=", '"TOP_window"') in body
    )
    window_fields = {key: value for key, _, value in window}
    assert window_fields["size"] == [
        ("width", "=", "1040"),
        ("height", "=", "700"),
    ]
    assert window_fields["orientation"] == "center"


def test_security_footer_is_retired_but_remains_attached_to_the_live_dossiers_gui():
    gui = _named_block(
        source("common/scripted_guis/03_targeted_operations_security.txt"),
        "TOP_security_footer_gui",
    )
    assert "parent_scripted_gui = TOP_dossiers_gui" in gui
    assert "parent_window_name" not in gui
    assert "always = no" in _named_block(gui, "visible")


def test_security_policy_attaches_to_the_live_dossiers_security_tab():
    gui = _named_block(
        source("common/scripted_guis/03_targeted_operations_security.txt"),
        "TOP_security_policy_gui",
    )
    assert "parent_scripted_gui = TOP_dossiers_gui" in gui
    assert "parent_window_name" not in gui
    visible = _named_block(gui, "visible")
    assert "TOP_security_window_visible = yes" in visible
    assert "check_variable = { TOP_security_open = 1 }" in visible
    assert "check_variable = { TOP_tab = 5 }" in visible


def test_security_footer_leaves_room_for_the_dossiers_refresh_button():
    windows = _parse_race_script(source("interface/targeted_operations_security.gui"))[
        "guiTypes"
    ]
    footer = next(
        body
        for kind, _, body in windows
        if kind == "containerWindowType"
        and ("name", "=", '"TOP_security_footer_window"') in body
    )
    fields = {key: value for key, _, value in footer}
    assert ("width", "=", "190") in fields["size"]
    badge = fields["instantTextboxType"]
    assert ("text", "=", '"TOP_security_parody_label"') in badge
    assert ("pdx_tooltip", "=", '"TOP_security_parody_tt"') in badge
    assert ("maxWidth", "=", "180") in badge


@pytest.mark.parametrize(
    "button,tab",
    (
        ("dossier_tab", 0),
        ("package_tab", 1),
        ("authority_tab", 2),
        ("custody_tab", 3),
        ("archive_tab", 4),
    ),
)
def test_dossier_navigation_leaves_the_security_overlay(button, tab):
    gui = _named_block(
        source("common/scripted_guis/01_targeted_operations_gui.txt"),
        "TOP_dossiers_gui",
    )
    click = _named_block(_named_block(gui, "effects"), f"TOP_{button}_click")
    assert "set_variable = { TOP_tab = " + str(tab) + " }" in click
    reset = "set_variable = { TOP_security_open = 0 }"
    assert reset in click
    assert click.index(reset) < click.index("TOP_build_view = yes")


def test_security_navigation_opens_the_security_overlay():
    gui = _named_block(
        source("common/scripted_guis/01_targeted_operations_gui.txt"),
        "TOP_dossiers_gui",
    )
    click = _named_block(_named_block(gui, "effects"), "TOP_security_tab_click")
    assert "set_variable = { TOP_tab = 5 }" in click
    assert "set_variable = { TOP_security_open = 1 }" in click
    assert "TOP_security_refresh_view = yes" in click
    assert "TOP_build_view = yes" in click


def test_ukrainian_leader_rotation_preserves_target_removal_guard():
    text = source("common/scripted_effects/UKR_political_leaders.txt")
    marker = re.search(
        r"if\s*=\s*\{\s*limit\s*=\s*\{\s*OR\s*=\s*\{\s*TOP_enabled\s*=\s*no",
        text,
    )
    assert marker
    guard = _extract_block(text, marker.start())
    assert "global.TOP_status^132 < 2" in _named_block(guard, "limit")
    assert "kill_country_leader = yes" in guard
    assert 'name = "Volodymyr Zelenskyy"' in guard
    assert text.count('name = "Volodymyr Zelenskyy"') == 1


def test_legacy_outcome_adapter_cannot_reenter_the_canonical_resolver():
    adapter = _named_block(
        source("common/scripted_effects/01_targeted_operations_legacy_effects.txt"),
        "TOP_apply_legacy_outcome",
    )
    assert "TOP_capture_target" not in adapter
    assert "TOP_kill_target" not in adapter
    assert "bin_laden_clear_hideout = yes" not in adapter
    assert "TOP_previous_status = 2" in adapter


def test_recapture_cannot_repeat_legacy_rewards():
    parsed = _parse_race_script(
        _named_block(
            source("common/scripted_effects/01_targeted_operations_legacy_effects.txt"),
            "TOP_apply_legacy_outcome",
        )
    )["TOP_apply_legacy_outcome"]

    def contains_first_removal(statements):
        return any(
            key == "check_variable" and ("TOP_first_removal", "=", "1") in value
            for key, _, value in statements
            if isinstance(value, list)
        )

    def walk(statements, guarded=False):
        limit = next((value for key, _, value in statements if key == "limit"), [])
        guarded = guarded or contains_first_removal(limit)
        for key, _, value in statements:
            if key in (
                "army_experience",
                "add_stability",
                "add_timed_idea",
                "TOP_bin_laden_legacy_removed",
            ):
                assert guarded, f"Repeatable legacy reward: {key}"
            if isinstance(value, list):
                walk(value, guarded)

    walk(parsed)


@pytest.mark.parametrize(
    "statuses,expected",
    [
        ({}, 0),
        ({56: 2}, 1),
        ({56: 3}, 1),
        ({56: 4}, 1),
        ({56: 2, 57: 3, 58: 2, 59: 3}, 4),
        ({55: 3, 56: 4, 63: 2, 64: 3}, 2),
        ({target: 3 for target in range(56, 64)}, 8),
    ],
)
def test_iraq_progress_reads_each_terminal_person_once(statuses, expected):
    text = _named_block(
        source("common/scripted_effects/01_targeted_operations_legacy_effects.txt"),
        "TOP_update_iraq_progress",
    )
    loop = _parse_race_script(_named_block(text, "for_loop_effect"))["for_loop_effect"]
    values = {key: value for key, _, value in loop}
    assert values["value"] == "top_iraq_target"
    conditional = next(value for key, _, value in loop if key == "if")
    conditions = next(value for key, _, value in conditional if key == "limit")
    comparisons = {">": operator.gt, "<": operator.lt, "=": operator.eq}
    result = 0
    for target in range(int(values["start"]), int(values["end"])):
        checks = [
            operand[0] for key, _, operand in conditions if key == "check_variable"
        ]
        if all(
            comparisons[op](statuses.get(target, 0), int(bound))
            for _, op, bound in checks
        ):
            result += 1
    assert result == expected
    assert "set_variable = { IRQ_baathist_dead = 0 }" in text
    assert "days_mission_timeout = 1825" in _named_block(
        source("common/decisions/USA.txt"), "USA_fugitive_countdown"
    )


def test_registered_character_removal_checks_the_person_before_each_removal():
    text = _named_block(
        source("common/scripted_effects/01_targeted_operations_legacy_effects.txt"),
        "TOP_retire_registered_character",
    )
    parsed = _parse_race_script(text)["TOP_retire_registered_character"]

    def walk(statements):
        for key, _, value in statements:
            if not isinstance(value, list):
                continue
            removals = [
                (effect, operand)
                for effect, _, operand in value
                if effect in ("kill_country_leader", "retire_character")
            ]
            if removals:
                assert key == "if"
                limit = next(
                    operand for effect, _, operand in value if effect == "limit"
                )
                for effect, operand in removals:
                    if effect == "retire_character":
                        assert ("has_character", "=", operand) in limit
                    else:
                        checks = limit
                        if len(limit) == 1 and limit[0][0] == "OR":
                            checks = limit[0][2]
                        assert checks
                        assert all(
                            effect == "has_country_leader" for effect, _, _ in checks
                        )
                        for _, _, leader in checks:
                            assert ("ruling_only", "=", "yes") in leader
                            assert any(effect == "name" for effect, _, _ in leader)
            walk(value)

    walk(parsed)
    for name in ("Saddam Hussein", "Saddam Hussein ", "Qasem Soleimani "):
        assert f'name = "{name}"' in text
    assert "IRS = {" in text
    assert "SHB = {" in text


def test_ttp_office_uses_active_canonical_successor_and_preserves_off_setter():
    adapter = _named_block(
        source("common/scripted_effects/01_targeted_operations_legacy_effects.txt"),
        "TOP_apply_office_successor",
    )
    assert "global.TOP_status^TOP_target = 1" in adapter
    assert "has_government = fascism" in adapter
    for name in (
        "Baitullah Mehsud",
        "Hakimullah Mehsud",
        "Maulana Fazlullah",
        "Noor Wali Mehsud",
    ):
        assert f'name = "{name}"' in adapter
    setter = _named_block(
        source("common/scripted_effects/TTP_political_leaders.txt"), "set_leader_TTP"
    )
    assert "TOP_apply_office_successor = yes" in enabled_branch(setter)
    assert "global.TOP_group_leader^4" in enabled_branch(setter)
    assert 'name = "Nek Muhammad Wazir"' in _named_block(setter, "else")


def test_bin_laden_release_reopens_legacy_hunt_without_replaying_rewards():
    release = _named_block(
        source("common/scripted_effects/01_targeted_operations_legacy_effects.txt"),
        "TOP_apply_legacy_release",
    )
    assert "global.TOP_status^1 = 1" in release
    assert "clr_global_flag = GLOBAL_bin_laden_killed_or_captured" in release
    assert "save_global_event_target_as = GLOBAL_bin_laden_hideout" in release
    assert "set_global_flag = GLOBAL_bin_laden_at_large" in release
    assert "TOP_apply_legacy_outcome" not in release
    assert "news_event" not in release


@pytest.mark.parametrize("tag,group", (("AQY", 2), ("ISI", 3), ("TTP", 4), ("SHB", 6)))
def test_country_movement_setters_share_registry_office(tag, group):
    setter = _named_block(
        source(f"common/scripted_effects/{tag}_political_leaders.txt"),
        f"set_leader_{tag}",
    )
    branch = enabled_branch(setter)
    assert f"global.TOP_group_leader^{group}" in branch
    assert "TOP_apply_office_successor = yes" in branch
    assert "create_country_leader" not in branch
    assert "create_country_leader" in _named_block(setter, "else")


def test_office_dispatch_never_replaces_ordinary_host_governments():
    text = source("common/scripted_effects/01_targeted_operations_legacy_effects.txt")
    office = _named_block(text, "TOP_apply_office_successor")
    for tag in ("AQY", "ISI", "TTP", "SHB"):
        body = _named_block(office, tag)
        assert "exists = yes has_government = fascism" in body
        assert "ruling_only = yes" in body
    for tag in ("YEM", "IRQ", "PAK", "SOM", "NIG", "ALG"):
        assert not re.search(rf"\b{tag}\s*=\s*{{", office)
    assert "TOP_install_generated_office = yes" in office
    retirement = _named_block(text, "TOP_retire_registered_character")
    assert "TOP_retire_generated_office = yes" in retirement
    assert "TOP_retire_authored_movement_office = yes" in retirement
    assert 'name = "Ahmad Umar" ruling_only = yes' in _named_block(
        text, "TOP_retire_authored_movement_office"
    )


def news_report(event_id, path):
    text = source(path)
    marker = re.search(rf"(?m)^\s*id\s*=\s*{re.escape(event_id)}\b", text)
    assert marker
    start = text.rfind("\nnews_event = {", 0, marker.start()) + 1
    return _parse_race_script(_extract_block(text, start))["news_event"]


def report_conditions_pass(statements, values):
    def evaluate(key, comparison, operand):
        assert comparison == "="
        if key == "TOP_enabled":
            return operand == "yes"
        if key == "check_variable":
            return all(
                values.get(variable, 0) == int(bound)
                for variable, op, bound in operand
                if op == "="
            )
        if key == "AND":
            return report_conditions_pass(operand, values)
        if key == "OR":
            return any(evaluate(*statement) for statement in operand)
        if key == "NOT":
            return not report_conditions_pass(operand, values)
        raise AssertionError(f"Unsupported news condition: {key}")

    return all(evaluate(*statement) for statement in statements)


def report_available(report, values):
    conditions = next(operand for key, _, operand in report if key == "trigger")
    return report_conditions_pass(conditions, values)


def report_top_texts(report, values):
    selected = set()
    for key, _, operand in report:
        if key not in ("title", "desc") or not isinstance(operand, list):
            continue
        fields = {field: value for field, _, value in operand}
        if fields["text"].startswith("TOP_legacy_") and report_conditions_pass(
            fields["trigger"], values
        ):
            selected.add(fields["text"])
    return selected
