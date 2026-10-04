"""Targeted Operations tests for the Iran, Israel and Middle East Peace Plan content bridges."""

import re

import pytest
from targeted_operations_core_test import (
    TargetScript,
)
from targeted_operations_legacy_test import (
    IRAQ,
    enabled_branch,
    event,
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
    ISI_FALLBACK,
)


@pytest.mark.parametrize("name,target", IRAQ)
def test_iraq_capture_events_have_one_authoritative_enabled_outcome(name, target):
    text = event(f"iraqi_MNF.{target - 46}", "events/Middle East Peace Plan.txt")
    branch = enabled_branch(text)
    assert (
        f"set_temp_variable = {{ TOP_arg_target = {target} }}"
        " TOP_capture_target = yes" in branch
    )
    assert "army_experience" not in branch
    assert "set_country_flag" not in branch
    legacy = _named_block(text, "else")
    assert f"set_country_flag = IRQ_{name}_caught" in legacy
    assert "army_experience = 100" in legacy


def test_soleimani_historical_report_cannot_remove_an_active_target():
    report = event("iranian_focus.159", "events/Iran.txt")
    trigger_start = re.search(r"(?m)^\ttrigger\s*=\s*\{", report).start()
    assert "global.TOP_status^64 = 3" in _extract_block(report, trigger_start)
    assert "TOP_kill_target" not in report
    opportunity = event("iranian_focus.160", "events/Iran.txt")
    branch = enabled_branch(opportunity)
    assert (
        "set_temp_variable = { TOP_arg_target = 64 }"
        " TOP_grant_target_mandate = yes" in branch
    )
    assert "country_event" not in branch


def test_soleimani_reports_do_not_assume_the_operation_method_or_other_casualties():
    for event_id, path in (
        ("iranian_focus.159", "events/Iran.txt"),
        ("israel_mechanic.13", "events/Israel_events.txt"),
    ):
        body = event(event_id, path)
        assert "TOP_legacy_soleimani_dead_d" in body
        assert "global.TOP_confirmed_dead^64 = 1" in body
        assert "text = " + event_id + ".d" in body


def test_iraqi_hunt_imports_selected_state_and_stops_resolved_saddam_loop():
    events = read("events/Middle East Peace Plan.txt")
    assert "PREV.TOP_import_state" not in events
    assert events.count("set_temp_variable = { TOP_import_state = THIS }") == 5
    relocation = events[
        events.index("country_event = { # Saddam Relocation (bi-monthly)") :
    ]
    assert (
        "TOP_enabled = yes check_variable = { global.TOP_status^56 > 1 }" in relocation
    )


def test_isi_formation_and_replacements_install_the_selected_successor():
    events = read("events/Iran.txt")
    assert events.count("TOP_target = global.TOP_group_leader^3") == 4
    assert events.count("TOP_apply_office_successor = yes") == 4
    assert events.count(ISI_FALLBACK) == 4


@pytest.mark.parametrize(
    "path,group,predecessor,successor,count",
    (("events/Iran.txt", 3, 29, 35, 4),),
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
