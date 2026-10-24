import re
from copy import deepcopy

import pytest
from targeted_operations_core_test import ROOT, ScriptArray, TargetScript
from targeted_operations_model_test import _named_block, _parse_race_script

LOOP_PATTERN = re.compile(r"\b(for_each_loop|for_loop_effect|any_of|all_of)\s*=\s*\{")
SCRIPT_PATHS = sorted(
    path
    for folder in ("common/scripted_effects", "common/scripted_triggers")
    for path in (ROOT / folder).glob("*targeted_operations*.txt")
)


@pytest.mark.parametrize("path", SCRIPT_PATHS, ids=lambda path: path.name)
def test_top_loop_bindings_use_engine_resolvable_lowercase_names(path):
    text = path.read_text(encoding="utf-8")
    for match in LOOP_PATTERN.finditer(text):
        kind = match.group(1)
        loop = _parse_race_script(_named_block(text[match.start() :], kind))[kind]
        bindings = {
            key: value for key, _, value in loop if key in {"value", "index", "break"}
        }
        for key, name in bindings.items():
            assert name == name.lower(), (path.name, kind, key, name)


def discovery_script():
    script = TargetScript()
    script.effects.update(
        _parse_race_script(
            (
                ROOT / "common/scripted_effects/01_targeted_operations_view.txt"
            ).read_text(encoding="utf-8")
        )
    )
    script.stubs.discard("TOP_build_view")
    script.stubs.add("TOP_political_country_opportunities")
    script.stubs.add("TOP_visit_country_opportunities")
    script.globals["TOP_active_targets"] = ScriptArray([1, 2, 3])
    script.globals["active_terror_orgs"] = ScriptArray([10, 0, 1])
    for target in (1, 2, 3):
        script.globals["TOP_status"][target] = 1
        script.globals["TOP_host"][target] = 2
        script.globals["TOP_state"][target] = 101
    variables = script.countries[1]["vars"]
    variables["international_terror_org_intel"] = ScriptArray([0, 40.4443, 0])
    variables["TOP_open"] = 1
    variables["TOP_status_filter"] = 2
    return script, variables


def test_existing_campaign_discovers_real_ids_and_builds_named_rows_one_at_a_time():
    script, variables = discovery_script()
    registry = deepcopy(script.globals)
    country_arrays = {
        name: len(value)
        for name, value in variables.items()
        if isinstance(value, list) and name != "TOP_organization_dossiers"
    }

    script.run("TOP_country_tick", 1)

    assert variables["TOP_dossiers"] == [1]
    assert variables["TOP_visible_people"] == [1]
    assert variables["TOP_known"][1] == 1
    assert variables["TOP_known"][0] == 0
    assert variables["TOP_lead_host"][1] == 2
    assert variables["TOP_lead_state"][1] == 101
    assert variables["TOP_identity_confidence"][1] == 15
    assert variables["TOP_location_confidence"][1] == 15
    assert variables["TOP_pattern_confidence"][1] == 0
    assert script.globals == registry
    assert all(len(variables[name]) == size for name, size in country_arrays.items())

    script.globals["TOP_clock"] += 28
    script.run("TOP_country_tick", 1)

    assert variables["TOP_dossiers"] == [1, 2]
    assert variables["TOP_visible_people"] == [1, 2]
    assert variables["TOP_known"][3] == 0
    assert variables["TOP_lead_age"][1] == 28
    assert variables["TOP_identity_confidence"][1] == 15
    assert variables["TOP_location_confidence"][1] == 10
    assert variables["TOP_pattern_confidence"][1] == 0


@pytest.mark.parametrize("intel", [0, 24])
def test_foreign_dossier_discovery_keeps_the_existing_intelligence_requirement(intel):
    script, variables = discovery_script()
    variables["international_terror_org_intel"][1] = intel

    script.run("TOP_country_tick", 1)

    assert not variables.get("TOP_dossiers")
    assert variables["TOP_visible_people"] == []
    assert not any(variables["TOP_known"])


def test_reconciliation_visits_real_groups_without_overwriting_saved_registry_state():
    script = TargetScript()
    script.globals["active_terror_orgs"] = ScriptArray(
        [script.globals["TOP_group_ct"][2], script.globals["TOP_group_ct"][1]]
    )
    script.globals["TOP_group_created"][0] = 1
    statuses = list(script.globals["TOP_status"])

    script.run("TOP_reconcile_organizations", 1)

    assert script.globals["TOP_group_created"][:4] == [1, 1, 1, 0]
    assert script.globals["TOP_status"] == statuses
    assert len(script.globals["TOP_group_created"]) == 35


def test_resuming_collection_preserves_the_package_and_review_snapshot():
    script, variables = discovery_script()
    script.target(1)
    variables["TOP_case_phase"][1] = 0
    variables["TOP_package_state"][1] = 1
    script.globals["TOP_clock"] = 100
    script.run("TOP_build_view", 1)
    assert variables["TOP_view_case_days"] == 0
    political_power = variables["political_power"]

    script.run("TOP_collect_selected", 1)

    assert variables["TOP_package_state"][1] == 2
    assert variables["TOP_collecting_subjects"] == [1]
    assert variables["TOP_case_phase"][1] == 0
    assert variables["TOP_view_case_days"] == 0
    assert variables["political_power"] == political_power
    assert variables["TOP_visible_people"] == [1]
