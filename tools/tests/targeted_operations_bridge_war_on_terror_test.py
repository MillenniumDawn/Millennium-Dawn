"""Targeted Operations tests for the War on Terror, Somalia, North Africa and Russia content bridges."""

import re

import pytest
from targeted_operations_core_test import (
    TargetScript,
)
from targeted_operations_legacy_test import (
    IRAQ,
    enabled_branch,
    event,
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
    read,
)
from targeted_operations_review_fixes_test import (
    SHABAAB_FALLBACK,
)


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
    assert (
        f"set_temp_variable = {{ TOP_arg_target = {target} }}"
        " TOP_kill_target = yes" in branch
    )
    assert "IRQ_baathist_dead" not in branch


@pytest.mark.parametrize("host", ("SYR", "SAU", "JOR", "KUR", "PUK", "PER", "KUW"))
def test_foreign_handover_decisions_develop_leads_without_automatic_captures(host):
    text = _named_block(source("common/decisions/USA.txt"), f"USA_{host}_baathists")
    branch = enabled_branch(_named_block(text, "remove_effect"))
    assert "country_event" not in branch
    assert "TOP_capture_target" not in branch
    for target in range(60, 64):
        assert (
            f"set_temp_variable = {{ TOP_arg_target = {target} }}"
            " set_temp_variable = { TOP_arg_amount = 40 }"
            " TOP_add_target_lead = yes" in branch
        )
    assert "iraqi_MNF.14" in _named_block(_named_block(text, "remove_effect"), "else")


def test_oef_consent_and_unilateral_choices_authorize_operations():
    consent = event("wot.24", "events/waronterror.txt")
    unilateral = event("wot.25", "events/waronterror.txt")
    for text in (consent, unilateral):
        match = re.search(r"if\s*=\s*\{\s*limit\s*=\s*\{\s*TOP_enabled\s*=\s*yes", text)
        assert match
        branch = _extract_block(text, match.start())
        assert (
            "set_temp_variable = { TOP_arg_target = 1 }"
            " TOP_grant_target_mandate = yes" in branch
        )
        assert (
            "set_temp_variable = { TOP_arg_target = 1 }"
            " set_temp_variable = { TOP_arg_amount = 40 }"
            " TOP_add_target_lead = yes" in branch
        )
        assert "bin_laden_clear_hideout" not in branch
        assert "TOP_kill_target" not in branch


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


def test_both_al_shabaab_founding_options_install_the_current_successor():
    events = read("events/Somalia.txt")
    options = [
        events[events.index(f"name = somalia.10.{letter}") :][:4000]
        for letter in ("a", "b")
    ]
    for option in options:
        assert (
            "set_temp_variable = { TOP_target = global.TOP_group_leader^6 }" in option
        )
        assert "TOP_apply_office_successor = yes" in option


def test_somalia_fallbacks_guard_a_removed_godane():
    events = read("events/Somalia.txt")
    assert events.count(SHABAAB_FALLBACK) == 2


@pytest.mark.parametrize(
    "path,group,predecessor,successor,count",
    (("events/Somalia.txt", 6, 45, 46, 2),),
)
@pytest.mark.parametrize("status", (2, 3), ids=("captured", "killed"))
@pytest.mark.parametrize("enabled", (False, True), ids=("off", "enabled"))
def test_legacy_office_paths_dispatch_selected_successor_after_predecessor_removal(
    path, group, predecessor, successor, count, status, enabled
):
    events = read(path)
    pattern = re.compile(
        r"if\s*=\s*\{\s*limit\s*=\s*\{\s*TOP_enabled\s*=\s*yes\s*"
        rf"check_variable\s*=\s*\{{\s*global.TOP_group_leader\^{group}\s*>\s*0\s*\}}\s*\}}"
        rf"\s*set_temp_variable\s*=\s*\{{\s*TOP_target\s*=\s*global.TOP_group_leader\^{group}\s*\}}"
    )
    branches = [
        _extract_block(events, match.start()) for match in pattern.finditer(events)
    ]
    assert len(branches) == count
    for branch in branches:
        script = TargetScript()
        script.globals["TOP_rule_mode"] = int(enabled)
        script.globals["TOP_status"][predecessor] = status
        script.globals["TOP_group_leader"][group] = successor

        statements = _parse_race_script(f"office_path = {{ {branch} }}")["office_path"]
        script.execute(statements, 1)

        assert script.external["TOP_apply_office_successor", 1] == int(enabled)
        if enabled:
            assert script.temps["TOP_target"] == successor
        assert script.globals["TOP_status"][predecessor] == status
