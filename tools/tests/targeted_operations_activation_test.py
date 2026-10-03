import pytest
from targeted_operations_core_test import ScriptArray, TargetScript

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
