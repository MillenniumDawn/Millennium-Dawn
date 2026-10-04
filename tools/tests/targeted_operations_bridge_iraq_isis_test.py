"""Targeted Operations tests for the Iraq and Islamic State content bridges."""

import re

import pytest
from targeted_operations_core_test import (
    TargetScript,
)
from targeted_operations_legacy_test import (
    IRAQ,
    enabled_branch,
    news_report,
    report_available,
    report_top_texts,
    source,
)
from targeted_operations_model_test import (
    _extract_block,
    _named_block,
    _parse_race_script,
)
from targeted_operations_redesign_test import (
    block,
    read,
)


def test_isi_pulse_produces_personal_leads_without_removal():
    text = _named_block(
        source("common/scripted_effects/99_ISI_scripted_effects.txt"), "ISI_burn_hvt"
    )
    branch = enabled_branch(text)
    assert "random_scope_in_array" in branch
    assert "remove_from_array" not in branch
    assert "retire_character" not in branch
    assert "ISI_retire_hvt_character" not in branch
    normalized_branch = " ".join(branch.split())
    for target in range(16, 29):
        assert (
            f"set_temp_variable = {{ TOP_arg_target = {target} }}"
            " set_temp_variable = { TOP_arg_amount = 40 }"
            " TOP_add_target_lead = yes" in normalized_branch
        )
    assert "ISI_retire_hvt_character = yes" in _named_block(text, "else")


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


def test_prosecuted_iraqi_cards_keep_a_resolution_indicator():
    for target in range(56, 64):
        trigger = block(
            "common/scripted_guis/99_IRQ_scripted_guis.txt",
            f"TOP_card_{target}_captured_visible",
        )
        assert f"global.TOP_status^{target} = 2" in trigger
        assert f"global.TOP_status^{target} = 4" in trigger


@pytest.mark.parametrize("target", range(56, 64))
@pytest.mark.parametrize("status", (1, 2, 3, 4, 5))
def test_iraqi_card_custody_indicator_tracks_capture_and_prosecution(target, status):
    name = f"TOP_card_{target}_captured_visible"
    trigger = block("common/scripted_guis/99_IRQ_scripted_guis.txt", name)
    script = TargetScript()
    script.globals["TOP_status"][target] = status

    assert script.condition(_parse_race_script(trigger)[name], 1) == (status in (2, 4))


@pytest.mark.parametrize("event_id", ("iraq_md.74", "iraq_md.316"))
def test_qusay_succession_keeps_upstream_focus_gate_and_top_lifecycle_guard(event_id):
    text = read("events/Iraq.txt")
    marker = re.search(rf"(?m)^\s*name = {re.escape(event_id)}\.a\s*$", text)
    assert marker
    start = text.rfind("\n\toption = {", 0, marker.start()) + 1
    option = _extract_block(text, start)
    branch = _named_block(option, "if")
    limit = _parse_race_script(_named_block(branch, "limit"))["limit"]
    assert limit == [("has_completed_focus", "=", "IRQ_designate_qussay")]
    guarded_creation = _named_block(branch[branch.index("{") + 1 :], "if")
    assert 'name = "Qusay Hussein"' in _named_block(
        guarded_creation, "create_country_leader"
    )
    guard = _parse_race_script(_named_block(guarded_creation, "limit"))["limit"]
    script = TargetScript()
    for status in (1, 2, 3, 4):
        script.globals["TOP_status"][57] = status
        assert script.condition(guard, 1) == (status == 1)
    script.globals["TOP_rule_mode"] = 0
    assert script.condition(guard, 1)
