import re
from copy import deepcopy
from pathlib import Path

import pytest
from targeted_operations_core_test import ScriptArray, TargetScript
from targeted_operations_helpers import _parse_race_script, read_top_source

STATE_REFERENCE = -10737.40617


def activation_script(group=1, target=1):
    script = TargetScript()
    script.globals["TOP_group_window"][group] = 1
    script.globals["TOP_window"][target] = 1
    return script


@pytest.mark.parametrize("state", [STATE_REFERENCE, 110])
def test_hq_reference_precedes_fallback_and_activates_only_once(state):
    script = activation_script()
    script.state(-10737.40618, 4)
    script.state(state, 4)
    script.state(-10737.40619, 8)
    script.globals["active_terror_hq"] = ScriptArray([state, 0])

    script.run("TOP_activate_group_1", 1)
    script.run("TOP_activate_group_1", 1)

    assert script.globals["TOP_status"][1] == 1
    assert script.globals["TOP_host"][1] == 4
    assert script.globals["TOP_state"][1] == state
    assert script.globals["TOP_active_targets"] == [1]


@pytest.mark.parametrize("hq", [None, 0])
def test_missing_hq_falls_back_to_a_controlled_state(hq):
    script = activation_script()
    script.state(STATE_REFERENCE, 8)
    if hq is not None:
        script.globals["active_terror_hq"] = ScriptArray([hq, 0])

    script.run("TOP_activate_group_1", 1)

    assert script.globals["TOP_status"][1] == 1
    assert script.globals["TOP_host"][1] == 8
    assert script.globals["TOP_state"][1] == STATE_REFERENCE
    assert script.globals["TOP_active_targets"] == [1]


@pytest.mark.parametrize("group,target,tag", [(11, 56, "IRQ"), (25, 144, "CHI")])
def test_political_locations_accept_state_references(group, target, tag):
    script = activation_script(group, target)
    host = script.tag(tag)
    script.state(STATE_REFERENCE, host)

    script.run(f"TOP_activate_group_{group}", 1)

    assert script.globals["TOP_political"][target] == 1
    assert script.globals["TOP_status"][target] == 1
    assert script.globals["TOP_host"][target] == host
    assert script.globals["TOP_state"][target] == STATE_REFERENCE
    assert script.globals["TOP_active_targets"] == [target]


def test_no_valid_host_leaves_target_inactive():
    script = activation_script()

    script.run("TOP_activate_group_1", 1)

    assert script.globals["TOP_status"][1] == 0
    assert script.globals["TOP_host"][1] == 0
    assert script.globals["TOP_state"][1] == 0
    assert script.globals["TOP_active_targets"] == []


@pytest.mark.parametrize(
    "field,value",
    [("TOP_group_window", 0), ("TOP_window", 0), ("TOP_group_destroyed", 1)],
)
def test_closed_windows_and_destroyed_groups_remain_blocked(field, value):
    script = activation_script()
    script.state(STATE_REFERENCE, 4)
    script.globals["active_terror_hq"] = ScriptArray([STATE_REFERENCE, 0])
    script.globals[field][1] = value

    script.run("TOP_activate_group_1", 1)

    assert script.globals["TOP_status"][1] == 0
    assert script.globals["TOP_active_targets"] == []


def test_intel_discovers_an_activated_state_reference_and_preserves_its_location():
    script = activation_script()
    script.state(STATE_REFERENCE, 4)
    script.globals["active_terror_hq"] = ScriptArray([STATE_REFERENCE, 0])
    variables = script.countries[1]["vars"]
    variables["international_terror_org_intel"] = ScriptArray([38.48938, 0])
    script.stubs.add("TOP_political_country_opportunities")
    script.stubs.add("TOP_visit_country_opportunities")

    script.run("TOP_activate_group_1", 1)
    script.run("TOP_country_tick", 1)

    assert variables.get("TOP_dossiers", []) == [1]
    assert variables["TOP_known"][1] == 1
    assert variables["TOP_lead_host"][1] == 4
    assert variables["TOP_lead_state"][1] == STATE_REFERENCE


def _discovered():
    script = TargetScript()
    script.stubs.add("TOP_political_country_opportunities")
    script.stubs.add("TOP_visit_country_opportunities")
    script.globals["TOP_active_targets"] = ScriptArray([1])
    script.globals["active_terror_orgs"] = ScriptArray([10, 0, 1])
    script.globals["TOP_status"][1] = 1
    script.globals["TOP_host"][1] = 2
    script.globals["TOP_state"][1] = 101
    variables = script.countries[1]["vars"]
    variables["international_terror_org_intel"] = ScriptArray([0, 40.4443, 0])
    variables["TOP_open"] = 1

    script.run("TOP_country_tick", 1)
    assert variables["TOP_dossiers"] == [1]
    assert variables["TOP_identity_confidence"][1] == 15
    assert variables["TOP_location_confidence"][1] == 15
    assert variables["TOP_pattern_confidence"][1] == 0
    return script, variables


def test_cold_dossier_persists_when_actionable_axes_reach_zero():
    script, variables = _discovered()
    variables["international_terror_org_intel"][1] = 0
    variables["TOP_location_confidence"][1] = 5
    variables["TOP_pattern_confidence"][1] = 3

    script.run("TOP_country_tick", 1)

    assert variables["TOP_dossiers"] == [1]
    assert variables["TOP_known"][1] == 1
    assert variables["TOP_identity_confidence"][1] == 15
    assert variables["TOP_location_confidence"][1] == 0
    assert variables["TOP_pattern_confidence"][1] == 0


def test_identity_is_durable_while_location_pattern_and_age_change_monthly():
    script, variables = _discovered()
    variables["international_terror_org_intel"][1] = 0
    variables["TOP_pattern_confidence"][1] = 20

    script.globals["TOP_clock"] += 28
    script.run("TOP_country_tick", 1)

    assert variables["TOP_identity_confidence"][1] == 15
    assert variables["TOP_location_confidence"][1] == 10
    assert variables["TOP_pattern_confidence"][1] == 17
    assert variables["TOP_lead_age"][1] == 28


def test_only_native_location_reports_refresh_lead_age():
    script, variables = _discovered()
    variables["TOP_lead_age"][1] = 55
    script.temps["TOP_target"] = 1
    for focus in (1, 2, 3):
        variables["TOP_collection_focus"][1] = focus
        script.run("TOP_collect_person_pulse", 1)
        assert variables["TOP_lead_age"][1] == 55
    script.run("TOP_core_location_report", 1)
    assert variables["TOP_lead_age"][1] == 0
    assert variables["TOP_location_confidence"][1] == 100


def test_ct_inputs_preserve_durable_identity_without_spillover_or_location_gain():
    script, variables = _discovered()
    variables["international_terror_org_intel"][1] = 60
    variables["TOP_identity_confidence"][1] = 100
    variables["TOP_location_confidence"][1] = 30
    variables["TOP_pattern_confidence"][1] = 40
    script.temps["TOP_target"] = 1
    for focus in (1, 2, 3):
        variables["TOP_collection_focus"][1] = focus
        script.run("TOP_collect_person_pulse", 1)
        assert variables["TOP_identity_confidence"][1] == 100
        assert variables["TOP_location_confidence"][1] == 30
        assert variables["TOP_pattern_confidence"][1] == 60


def test_outcomes_and_custody_remain_in_the_same_persistent_dossier():
    script, variables = _discovered()
    variables["TOP_assessment"][1] = 2
    script.globals["TOP_status"][1] = 2
    script.globals["TOP_custodian"][1] = 1

    script.run("TOP_country_tick", 1)

    assert variables["TOP_dossiers"] == [1]
    assert variables["TOP_assessment"][1] == 2


def test_decay_never_mutates_global_physical_truth():
    script, _variables = _discovered()
    before = {
        name: deepcopy(value)
        for name, value in script.globals.items()
        if isinstance(value, list)
    }

    script.run("TOP_country_tick", 1)

    after = {
        name: deepcopy(value)
        for name, value in script.globals.items()
        if isinstance(value, list)
    }
    assert after == before


def test_country_belief_arrays_keep_registry_capacity_during_decay():
    script, variables = _discovered()
    sizes = {
        name: len(value) for name, value in variables.items() if isinstance(value, list)
    }

    script.run("TOP_country_tick", 1)

    assert variables["TOP_dossiers"] == [1]
    for name, size in sizes.items():
        assert len(variables[name]) == size, name


ROOT = Path(__file__).resolve().parents[3]


CT_SETUP = _parse_race_script(
    (ROOT / "common/scripted_effects/00_ct_effects.txt").read_text(encoding="utf-8")
)["counter_terror_global_setup"]


def test_registry_initialization_precedes_country_startup():
    calls = [name for name, _, _ in CT_SETUP]
    assert calls.index("TOP_initialize_global") < calls.index("create_staggered_cycle")


def test_country_case_arrays_use_registry_capacity_at_startup():
    script = TargetScript()
    script.globals.clear()
    script.globals.update(TOP_rule_mode=1)
    country_vars = script.countries[1]["vars"]
    country_vars.clear()

    initialized = []
    for name, _, operand in CT_SETUP:
        if name == "TOP_initialize_global":
            assert operand == "yes"
            script.run("TOP_setup_registry", 1)
            initialized.append(name)
        elif name == "create_staggered_cycle":
            assert operand == "yes"
            script.run("TOP_country_initialize", 1)
            initialized.append(name)

    assert sorted(initialized) == ["TOP_initialize_global", "create_staggered_cycle"]
    capacity = script.globals["TOP_registry_capacity"]
    assert capacity == 161
    assert len(country_vars["TOP_known"]) == capacity

    case_arrays = [
        operand[0][0]
        for name, _, operand in script.effects["TOP_initialize_cases"]
        if name == "resize_array"
    ]
    assert len(case_arrays) == len(set(case_arrays))
    referenced_case_arrays = set(
        re.findall(
            r"\b(TOP_case_[A-Za-z0-9_]+)\^",
            read_top_source(ROOT, "common/scripted_effects"),
        )
    )
    assert set(case_arrays) == referenced_case_arrays
    assert "TOP_case_native_prepared" in case_arrays
    assert "TOP_case_native_success_bonus" in case_arrays
    assert "TOP_case_native_success_penalty" in case_arrays
    assert all(name.startswith("TOP_case_") for name in case_arrays)
    assert {
        "TOP_case_identity",
        "TOP_case_location",
        "TOP_case_pattern",
        "TOP_case_lead_age",
        "TOP_case_access",
        "TOP_case_host_posture",
        "TOP_case_doctrine",
        "TOP_case_attribution",
        "TOP_case_harm",
        "TOP_case_oversight",
    } <= set(case_arrays)
    assert {name: len(country_vars[name]) for name in case_arrays} == {
        name: capacity for name in case_arrays
    }

    organization_arrays = [
        operand[0][0]
        for name, _, operand in script.effects["TOP_initialize_organization_cases"]
        if name == "resize_array"
    ]
    group_capacity = len(script.globals["TOP_group_class"])
    assert len(organization_arrays) == len(set(organization_arrays))
    assert all(name.startswith("TOP_org_case_") for name in organization_arrays)
    assert "TOP_org_case_protection" in organization_arrays
    assert {name: len(country_vars[name]) for name in organization_arrays} == {
        name: group_capacity for name in organization_arrays
    }


def test_only_human_countries_allocate_top_arrays_on_ct_rotation():
    effects = _parse_race_script(
        read_top_source(ROOT, "common/scripted_effects")
        + (ROOT / "common/scripted_effects/00_ct_effects.txt").read_text(
            encoding="utf-8"
        )
    )
    human_init = (
        "if",
        "=",
        [
            ("limit", "=", [("is_ai", "=", "no")]),
            ("TOP_country_initialize", "=", "yes"),
        ],
    )
    startup = effects["counter_terror_nation_startup"]
    assert human_init in startup
    assert ("TOP_country_initialize", "=", "yes") not in startup
    first = next(
        value for name, _, value in effects["TOP_country_tick"] if name == "if"
    )
    assert human_init in first
    assert ("TOP_country_initialize", "=", "yes") not in first
    liaison = effects["TOP_prepare_ai_liaison_source"]
    assert liaison[0] == (
        "if",
        "=",
        [
            ("limit", "=", [("is_ai", "=", "yes")]),
            ("TOP_country_initialize", "=", "yes"),
        ],
    )
