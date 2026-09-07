import operator
import re
from pathlib import Path

import pytest
from great_ai_race_state_model_test import (
    _extract_block,
    _named_block,
    _parse_race_script,
)

ROOT = Path(__file__).resolve().parents[2]
IRAQ = tuple(
    zip(
        ("saddam", "qusay", "uday", "abid", "majid", "walter", "tilfah", "salih"),
        range(56, 64),
    )
)


def source(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


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


@pytest.mark.parametrize("name,target", IRAQ)
def test_iraq_capture_events_have_one_authoritative_enabled_outcome(name, target):
    text = event(f"iraqi_MNF.{target - 46}", "events/Middle East Peace Plan.txt")
    branch = enabled_branch(text)
    assert f"TOP_capture_target = {{ TARGET = {target} }}" in branch
    assert "army_experience" not in branch
    assert "set_country_flag" not in branch
    legacy = _named_block(text, "else")
    assert f"set_country_flag = IRQ_{name}_caught" in legacy
    assert "army_experience = 100" in legacy


@pytest.mark.parametrize("name,target", IRAQ)
def test_custody_sentences_revalidate_owner_and_use_shared_resolver(name, target):
    decisions = source("common/decisions/USA.txt")
    actual_name = "latif" if name == "tilfah" else name
    token = f"USA_execute_{actual_name}"
    if token not in decisions:
        token = f"USA_execute_{name}"
    text = _named_block(decisions, token)
    visible = _named_block(text, "visible")
    assert f"global.TOP_status^{target} = 2" in visible
    assert f"global.TOP_custodian^{target} = ROOT" in visible
    removal = _named_block(text, "remove_effect")
    assert re.search(r"remove_effect\s*=\s*\{\s*log\s*=", removal)
    branch = enabled_branch(removal)
    assert f"TOP_kill_target = {{ TARGET = {target} }}" in branch
    assert "IRQ_baathist_dead" not in branch


@pytest.mark.parametrize("host", ("SYR", "SAU", "JOR", "KUR", "PUK", "PER", "KUW"))
def test_foreign_handover_decisions_develop_leads_without_automatic_captures(host):
    text = _named_block(source("common/decisions/USA.txt"), f"USA_{host}_baathists")
    branch = enabled_branch(_named_block(text, "remove_effect"))
    assert "country_event" not in branch
    assert "TOP_capture_target" not in branch
    for target in range(60, 64):
        assert f"TOP_add_target_lead = {{ TARGET = {target} AMOUNT = 40 }}" in branch
    assert "iraqi_MNF.14" in _named_block(_named_block(text, "remove_effect"), "else")


def test_isi_pulse_produces_personal_leads_without_removal():
    text = _named_block(
        source("common/scripted_effects/99_ISI_scripted_effects.txt"), "ISI_burn_hvt"
    )
    branch = enabled_branch(text)
    assert "random_scope_in_array" in branch
    assert "remove_from_array" not in branch
    assert "retire_character" not in branch
    assert "ISI_retire_hvt_character" not in branch
    for target in range(16, 29):
        assert f"TOP_add_target_lead = {{ TARGET = {target} AMOUNT = 40 }}" in branch
    assert "ISI_retire_hvt_character = yes" in _named_block(text, "else")


def test_oef_consent_and_unilateral_choices_authorize_operations():
    consent = event("wot.24", "events/waronterror.txt")
    unilateral = event("wot.25", "events/waronterror.txt")
    for text in (consent, unilateral):
        match = re.search(r"if\s*=\s*\{\s*limit\s*=\s*\{\s*TOP_enabled\s*=\s*yes", text)
        assert match
        branch = _extract_block(text, match.start())
        assert "TOP_grant_target_mandate = { TARGET = 1 }" in branch
        assert "TOP_add_target_lead = { TARGET = 1 AMOUNT = 40 }" in branch
        assert "bin_laden_clear_hideout" not in branch
        assert "TOP_kill_target" not in branch


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
        ({56: 2, 57: 3, 58: 2, 59: 3}, 4),
        ({55: 3, 56: 4, 63: 2, 64: 3}, 1),
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
    assert values["value"] == "TOP_iraq_target"
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


def test_cards_distinguish_custody_and_death():
    gui = _named_block(
        source("common/scripted_guis/99_IRQ_scripted_guis.txt"),
        "american_playing_cards",
    )
    window = source("interface/Iraq_civil_war.gui")
    for _, target in IRAQ:
        captured = _named_block(gui, f"TOP_card_{target}_captured_visible")
        assert f"global.TOP_status^{target} = 2" in captured
        assert f'name = "TOP_card_{target}_captured"' in window
        assert f"global.TOP_status^{target} = 3" in gui
    assert 'text = "TOP_status_captured"' in window


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


def test_soleimani_historical_report_cannot_remove_an_active_target():
    report = event("iranian_focus.159", "events/Iran.txt")
    trigger_start = re.search(r"(?m)^\ttrigger\s*=\s*\{", report).start()
    assert "global.TOP_status^64 = 3" in _extract_block(report, trigger_start)
    assert "TOP_kill_target" not in report
    opportunity = event("iranian_focus.160", "events/Iran.txt")
    branch = enabled_branch(opportunity)
    assert "TOP_grant_target_mandate = { TARGET = 64 }" in branch
    assert "country_event" not in branch


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


def test_legacy_lethal_news_waits_for_confirmation_and_consumes_its_pending_delivery():
    text = source("common/scripted_effects/01_targeted_operations_legacy_effects.txt")
    outcome = _named_block(text, "TOP_apply_legacy_outcome")
    report = _named_block(text, "TOP_apply_legacy_assessment")
    assert "TOP_legacy_report_pending^TOP_target = 1" in outcome
    for token in ("wotnews.16", "iranian_focus.159", "israel_mechanic.13"):
        assert token not in outcome
        assert token in report
    assert "TOP_assessment^TOP_target = 3" in _named_block(report, "limit")
    assert report.index("TOP_legacy_report_pending^TOP_target = 0") < report.index(
        "news_event"
    )
    for token in (
        "TOP_kill_target",
        "TOP_capture_target",
        "random_list",
        "army_experience",
        "add_political_power",
    ):
        assert token not in report
    gui = _named_block(
        source("common/scripted_guis/99_IRQ_scripted_guis.txt"),
        "american_playing_cards",
    )
    for _, target in IRAQ:
        assert f"global.TOP_confirmed_dead^{target} = 1" in gui


@pytest.mark.parametrize("prefix", (1300, 11300))
def test_legacy_isis_reports_describe_the_recorded_capture_or_confirmed_death(prefix):
    text = source("events/Islamic State.txt")
    for old_id in range(1, 14):
        target = old_id + 15
        marker = re.search(rf"(?m)^\s*id\s*=\s*isisNews\.{prefix + old_id}\b", text)
        start = text.rfind("\nnews_event = {", 0, marker.start()) + 1
        body = _extract_block(text, start)
        for outcome in ("captured", "dead"):
            for field in ("t", "d"):
                assert f"TOP_legacy_person_{target}_{outcome}_{field}" in body
        assert f"global.TOP_first_outcome^{target} = 2" in body
        assert "global.TOP_status^" not in body
        assert f"global.TOP_confirmed_dead^{target} = 1" in body
        assert "trigger = { TOP_enabled = no" in body


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


@pytest.mark.parametrize("prefix", (1300, 11300))
@pytest.mark.parametrize(
    "current_status", (2, 1, 3), ids=("held", "released", "later_killed")
)
@pytest.mark.parametrize("confirmed_dead", (0, 1))
def test_queued_isis_capture_keeps_its_recorded_outcome(
    prefix, current_status, confirmed_dead
):
    for old_id in range(1, 14):
        target = old_id + 15
        report = news_report(f"isisNews.{prefix + old_id}", "events/Islamic State.txt")
        values = {
            f"global.TOP_first_outcome^{target}": 2,
            f"global.TOP_status^{target}": current_status,
            f"global.TOP_confirmed_dead^{target}": confirmed_dead,
            "TOP_selected": target + 1,
        }
        assert report_available(report, values)
        assert report_top_texts(report, values) == {
            f"TOP_legacy_person_{target}_captured_t",
            f"TOP_legacy_person_{target}_captured_d",
        }


@pytest.mark.parametrize("prefix", (1300, 11300))
@pytest.mark.parametrize("confirmed_dead", (0, 1))
def test_queued_isis_lethal_report_waits_for_its_confirmation(prefix, confirmed_dead):
    for old_id in range(1, 14):
        target = old_id + 15
        report = news_report(f"isisNews.{prefix + old_id}", "events/Islamic State.txt")
        values = {
            f"global.TOP_first_outcome^{target}": 3,
            f"global.TOP_status^{target}": 3,
            f"global.TOP_confirmed_dead^{target}": confirmed_dead,
            "TOP_selected": target + 1,
        }
        assert report_available(report, values) == bool(confirmed_dead)
        expected = {
            f"TOP_legacy_person_{target}_dead_t",
            f"TOP_legacy_person_{target}_dead_d",
        }
        assert report_top_texts(report, values) == (
            expected if confirmed_dead else set()
        )


@pytest.mark.parametrize("event_id,target", (("wotnews.12", 56), ("wotnews.15", 1)))
@pytest.mark.parametrize(
    "current_status", (2, 1, 3), ids=("held", "released", "later_killed")
)
def test_queued_wot_capture_survives_later_custody_changes(
    event_id, target, current_status
):
    report = news_report(event_id, "events/waronterror.txt")
    values = {
        f"global.TOP_first_outcome^{target}": 2,
        f"global.TOP_status^{target}": current_status,
        "TOP_selected": target + 1,
    }
    assert report_available(report, values)
    assert any("captured" in text for text in report_top_texts(report, values))


@pytest.mark.parametrize("confirmed_dead", (0, 1))
def test_bin_laden_lethal_news_uses_confirmed_first_outcome(confirmed_dead):
    report = news_report("wotnews.16", "events/waronterror.txt")
    values = {
        "global.TOP_first_outcome^1": 3,
        "global.TOP_status^1": 3,
        "global.TOP_confirmed_dead^1": confirmed_dead,
        "TOP_selected": 2,
    }
    assert report_available(report, values) == bool(confirmed_dead)
    values["global.TOP_first_outcome^1"] = 2
    assert not report_available(report, values)


def test_soleimani_reports_do_not_assume_the_operation_method_or_other_casualties():
    for event_id, path in (
        ("iranian_focus.159", "events/Iran.txt"),
        ("israel_mechanic.13", "events/Israel_events.txt"),
    ):
        body = event(event_id, path)
        assert "TOP_legacy_soleimani_dead_d" in body
        assert "global.TOP_confirmed_dead^64 = 1" in body
        assert "text = " + event_id + ".d" in body
