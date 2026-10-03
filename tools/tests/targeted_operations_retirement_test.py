"""Cold dossiers persist while actionable beliefs decay independently."""

from copy import deepcopy

from targeted_operations_core_test import ScriptArray, TargetScript


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


def test_only_location_focus_refreshes_lead_age():
    script, variables = _discovered()
    variables["TOP_package_state"][1] = 2
    variables["TOP_lead_age"][1] = 55
    script.stubs.add("TOP_maybe_false_person_location")
    script.temps.update(TOP_target=1, TOP_gain=20)

    variables["TOP_collection_focus"][1] = 1
    script.run("TOP_apply_person_collection_gain", 1)
    assert variables["TOP_lead_age"][1] == 55

    variables["TOP_collection_focus"][1] = 3
    script.run("TOP_apply_person_collection_gain", 1)
    assert variables["TOP_lead_age"][1] == 55

    variables["TOP_collection_focus"][1] = 2
    script.run("TOP_apply_person_collection_gain", 1)
    assert variables["TOP_lead_age"][1] == 0


def test_focus_gain_uses_full_axis_and_quarter_spillover():
    script, variables = _discovered()
    variables["TOP_identity_confidence"][1] = 20
    variables["TOP_location_confidence"][1] = 30
    variables["TOP_pattern_confidence"][1] = 40
    variables["TOP_collection_focus"][1] = 3
    script.temps.update(TOP_target=1, TOP_gain=20)

    script.run("TOP_apply_person_collection_gain", 1)

    assert variables["TOP_identity_confidence"][1] == 25
    assert variables["TOP_location_confidence"][1] == 35
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
