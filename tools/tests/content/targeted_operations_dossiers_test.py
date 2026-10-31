import re
from copy import deepcopy
from pathlib import Path

import pytest
import validate_scripted_params as vsp
from targeted_operations_authorization_test import ReviewScript
from targeted_operations_core_test import ScriptArray, TargetScript
from targeted_operations_helpers import _extract_block, _named_block, _parse_race_script

ROOT = Path(__file__).resolve().parents[3]


def test_cleared_or_decayed_assessment_axes_do_not_show_stale_sources():
    localisation = (
        ROOT / "common/scripted_localisation/01_targeted_operations_status.txt"
    ).read_text(encoding="utf-8")
    for name, confidence in (
        ("TOP_selected_axis_2_source", "TOP_location_confidence"),
        ("TOP_selected_axis_3_source", "TOP_pattern_confidence"),
        ("TOP_selected_axis_2_source", "TOP_org_location"),
        ("TOP_selected_axis_3_source", "TOP_org_activity"),
    ):
        match = re.search(rf"name = {name}\b", localisation)
        assert match
        definition = _extract_block(
            localisation, localisation.rfind("defined_text", 0, match.start())
        )
        subject = (
            "TOP_selected_organization"
            if confidence.startswith("TOP_org_")
            else "TOP_selected"
        )
        gate = f"check_variable = {{ {confidence}^{subject} > 0 }}"
        assert definition.count(gate) == 5


def test_public_identity_and_authored_lead_keep_distinct_sources():
    script = TargetScript()
    variables = script.target(11)
    script.globals["TOP_public_identity"][11] = 1
    variables["TOP_identity_confidence"][11] = 0
    variables["TOP_identity_source"][11] = 0
    variables["TOP_lead_state"][11] = 0
    script.execute(script.effects["TOP_seed_public_subjects"], 1)

    assert variables["TOP_identity_confidence"][11] == 100
    assert variables["TOP_identity_source"][11] == 1
    assert variables["TOP_lead_state"][11] == 0
    assert variables["TOP_lead_source"][11] == 0

    variables["TOP_location_confidence"][11] = 0
    variables["TOP_pattern_confidence"][11] = 0
    script.call("TOP_add_target_lead", TARGET=11, AMOUNT=10)

    assert variables["TOP_identity_source"][11] == 1
    assert variables["TOP_location_source"][11] == 2
    assert variables["TOP_pattern_source"][11] == 2
    assert variables["TOP_lead_source"][11] == 2


def test_core_collection_relabels_only_axes_that_increase():
    from targeted_operations_core_test import ScriptArray

    script = TargetScript()
    variables = script.target(11)
    variables["TOP_identity_confidence"][11] = 100
    variables["TOP_identity_source"][11] = 1
    variables["TOP_location_source"][11] = 4
    variables["TOP_lead_source"][11] = 4
    variables["international_terror_org_intel"] = ScriptArray([90, 0])
    script.globals["TOP_group_ct"][int(script.globals["TOP_affiliation"][11])] = 0
    script.temps["TOP_target"] = 11
    script.run("TOP_collect_person_pulse", 1)
    assert variables["TOP_identity_source"][11] == 1
    assert variables["TOP_pattern_source"][11] == 2
    assert variables["TOP_location_source"][11] == 4
    assert variables["TOP_lead_source"][11] == 4


def test_liaison_source_changes_only_for_accepted_assessment_and_lead():
    script = TargetScript()
    variables = script.target(11)
    script.globals["TOP_clock"] = 100
    variables["TOP_enabled"] = 1
    variables["TOP_lead_report_clock"][11] = 95
    variables["TOP_lead_age"][11] = 5
    for field in ("identity", "location", "pattern", "lead"):
        variables[f"TOP_{field}_source"][11] = 3
    script.temps.update(
        TOP_liaison_snapshot_kind=1,
        TOP_liaison_snapshot_id=11,
        TOP_liaison_axis_1=50,
        TOP_liaison_axis_2=50,
        TOP_liaison_axis_3=50,
        TOP_liaison_state=102,
        TOP_liaison_host=3,
        TOP_liaison_age=20,
        TOP_liaison_response_reliability=1,
        TOP_liaison_leak_chance=0,
    )
    script.run("TOP_merge_liaison_snapshot", 1)
    assert [
        variables[f"TOP_{field}_source"][11]
        for field in ("identity", "location", "pattern", "lead")
    ] == [3, 3, 3, 3]
    assert variables["TOP_lead_state"][11] == 101

    script.temps.update(TOP_liaison_axis_2=95, TOP_liaison_age=1)
    variables["TOP_view_lead_age"] = 5
    script.run("TOP_merge_liaison_snapshot", 1)
    assert [
        variables[f"TOP_{field}_source"][11]
        for field in ("identity", "location", "pattern", "lead")
    ] == [3, 4, 3, 4]
    assert variables["TOP_lead_state"][11] == 102
    assert variables["TOP_view_lead_age"] == 1


def test_liaison_confidence_gain_does_not_relabel_unchanged_local_lead():
    script = TargetScript()
    variables = script.target(11)
    script.globals["TOP_clock"] = 100
    for field, value in (
        ("TOP_lead_state", 101),
        ("TOP_lead_host", 2),
        ("TOP_lead_age", 10),
        ("TOP_lead_report_clock", 90),
    ):
        variables[field][11] = value
    variables["TOP_lead_source"][11] = 3
    variables["TOP_location_confidence"][11] = 20
    script.temps.update(
        TOP_liaison_snapshot_kind=1,
        TOP_liaison_snapshot_id=11,
        TOP_liaison_axis_1=50,
        TOP_liaison_axis_2=80,
        TOP_liaison_axis_3=50,
        TOP_liaison_state=101,
        TOP_liaison_host=2,
        TOP_liaison_age=10,
        TOP_liaison_response_reliability=1,
        TOP_liaison_leak_chance=0,
    )

    script.run("TOP_merge_liaison_snapshot", 1)

    assert variables["TOP_location_source"][11] == 4
    assert variables["TOP_lead_source"][11] == 3
    assert variables["TOP_lead_report_clock"][11] == 90


def test_liaison_age_cache_requires_matching_subject_kind_for_overlapping_ids():
    script = TargetScript()
    variables = script.target(2)
    script.organization_truth(2, state=101, public=True)
    script.globals["TOP_group_class"][2] = 1
    variables["TOP_org_known"][2] = 1
    variables["TOP_enabled"] = 1
    variables["TOP_view_lead_age"] = 99
    variables["TOP_lead_age"][2] = 11
    script.globals["TOP_clock"] = 100

    script.temps.update(
        TOP_liaison_snapshot_kind=2,
        TOP_liaison_snapshot_id=2,
        TOP_liaison_axis_1=50,
        TOP_liaison_axis_2=95,
        TOP_liaison_axis_3=50,
        TOP_liaison_state=102,
        TOP_liaison_host=3,
        TOP_liaison_age=1,
        TOP_liaison_response_reliability=1,
        TOP_liaison_leak_chance=0,
    )
    script.run("TOP_merge_liaison_snapshot", 1)
    assert variables["TOP_view_lead_age"] == 99

    variables["TOP_selected_kind"] = 2
    variables["TOP_selected_organization"] = 2
    variables["TOP_view_lead_age"] = 88
    variables["TOP_org_lead_age"][2] = 12
    script.temps.update(TOP_liaison_snapshot_kind=1)
    script.run("TOP_merge_liaison_snapshot", 1)
    assert variables["TOP_view_lead_age"] == 88


def test_organization_sources_follow_authored_collection_and_liaison_reports():
    script = TargetScript()
    script.organization_truth(2, state=101, public=True)
    variables = script.countries[1]["vars"]
    script.call("TOP_add_organization_lead", GROUP=2, AMOUNT=10)
    assert variables["TOP_org_verification_source"][2] == 1
    assert variables["TOP_org_location_source"][2] == 2
    assert variables["TOP_org_activity_source"][2] == 2
    assert variables["TOP_org_lead_source"][2] == 2

    variables["TOP_org_collection_focus"][2] = 1
    script.temps.update(TOP_group_target=2, TOP_gain=12)
    variables["international_terror_org_intel"] = ScriptArray([90, 90])
    script.run("TOP_collect_organization_pulse", 1)
    assert variables["TOP_org_verification_source"][2] == 1
    assert variables["TOP_org_location_source"][2] == 2
    assert variables["TOP_org_activity_source"][2] == 2

    script.globals["TOP_clock"] = 100
    variables["TOP_enabled"] = 1
    variables["TOP_selected_kind"] = 2
    variables["TOP_selected_organization"] = 2
    variables["TOP_org_lead_report_clock"][2] = 95
    script.temps.update(
        TOP_liaison_snapshot_kind=2,
        TOP_liaison_snapshot_id=2,
        TOP_liaison_axis_1=50,
        TOP_liaison_axis_2=5,
        TOP_liaison_axis_3=5,
        TOP_liaison_state=102,
        TOP_liaison_host=3,
        TOP_liaison_age=20,
        TOP_liaison_response_reliability=1,
        TOP_liaison_leak_chance=0,
    )
    script.run("TOP_merge_liaison_snapshot", 1)
    assert variables["TOP_org_lead_source"][2] == 2
    script.temps.update(TOP_liaison_axis_2=95, TOP_liaison_age=1)
    script.run("TOP_merge_liaison_snapshot", 1)
    assert variables["TOP_org_location_source"][2] == 4
    assert variables["TOP_org_lead_source"][2] == 4
    variables["TOP_view_lead_age"] = 5
    script.run("TOP_merge_liaison_snapshot", 1)
    assert variables["TOP_view_lead_age"] == 1


def test_host_report_labels_only_axes_it_can_raise():
    review = ReviewScript()
    review.ready_for_host()
    review.run("TOP_send_host_request")
    review.globals["TOP_clock"] = 1
    review.actor["TOP_identity_confidence^1"] = 100
    review.actor["TOP_identity_source^1"] = 1
    review.actor["TOP_location_confidence^1"] = 95
    review.actor["TOP_location_source^1"] = 3
    review.actor["TOP_lead_source^1"] = 3
    review.call("TOP_answer_host_request", identifier=2, POSTURE=2)

    assert review.actor["TOP_identity_source^1"] == 1
    assert review.actor["TOP_location_confidence^1"] == 100
    assert review.actor["TOP_location_source^1"] == 5
    assert review.actor["TOP_lead_source^1"] == 5


def test_host_report_marks_encoded_person_and_organization_leads():
    encoded_state = -10737.40617
    person = ReviewScript()
    person.ready_for_host()
    person.run("TOP_send_host_request")
    person.globals["TOP_clock"] = 1
    person.actor["TOP_lead_state^1"] = encoded_state
    person.actor["TOP_lead_report_clock^1"] = 0
    person.call("TOP_answer_host_request", identifier=2, POSTURE=2)
    assert person.actor["TOP_lead_source^1"] == 5

    host_answer = (
        ROOT
        / "common/scripted_effects/02_targeted_operations_authorization_effects.txt"
    ).read_text(encoding="utf-8")
    assert (
        "NOT = { check_variable = { TOP_org_lead_state^TOP_proposal_subject_id = 0 } }"
        in host_answer
    )


def test_review_return_records_resumed_collection():
    review = ReviewScript()
    review.call("TOP_begin_review", METHOD=2)

    review.run("TOP_return_recorded_collection")

    rows = review.actor["TOP_history_rows"]
    assert review.actor[f"TOP_history_event^{int(rows[-1])}"] == 2
    assert review.actor[f"TOP_history_subject_kind^{int(rows[-1])}"] == 1
    assert review.actor[f"TOP_history_subject_id^{int(rows[-1])}"] == 1


def test_source_and_freshness_dispatchers_require_a_current_lead():
    source = (
        ROOT / "common/scripted_localisation/01_targeted_operations_status.txt"
    ).read_text(encoding="utf-8")
    script = TargetScript()
    variables = script.target(11)
    variables["TOP_selected"] = 11
    variables["TOP_lead_source"][11] = 3

    for name, expected_when_present in (
        ("TOP_selected_lead_source", "TOP_source_3"),
        ("TOP_selected_lead_freshness", "TOP_lead_freshness_known"),
    ):
        start = source.rfind("defined_text = {", 0, source.index(f"name = {name}"))
        entries = _parse_race_script(_extract_block(source, start))["defined_text"]

        def selected_key():
            for key, _, fields in entries:
                if key != "text":
                    continue
                values = {field: value for field, _, value in fields}
                if "trigger" not in values or script.condition(values["trigger"], 1):
                    return values["localization_key"]
            raise AssertionError("No matching defined text")

        variables["TOP_lead_state"][11] = -10737.40617
        assert selected_key() == expected_when_present
        variables["TOP_lead_state"][11] = 0
        assert selected_key() == (
            "TOP_source_0"
            if name == "TOP_selected_lead_source"
            else "TOP_lead_freshness_none"
        )


def test_person_case_milestones_follow_real_package_transitions():
    script = TargetScript()
    variables = script.target(11)
    variables["TOP_package_state"][11] = 0
    script.run("TOP_designate_selected", 1)
    script.call("TOP_open_person_review_case", TARGET=11)
    script.call("TOP_close_case", TARGET=11, SEQUENCE=1)
    script.run("TOP_abandon_person_package", 1)
    script.run("TOP_designate_selected", 1)

    rows = variables["TOP_history_rows"]
    assert [variables["TOP_history_event"][int(row)] for row in rows] == [1, 4, 8, 9, 1]
    assert [variables["TOP_history_package_cycle"][int(row)] for row in rows] == [
        1,
        1,
        1,
        1,
        2,
    ]
    assert [variables["TOP_history_case_sequence"][int(row)] for row in rows] == [
        0,
        1,
        1,
        0,
        0,
    ]


def test_preparation_operation_and_reports_use_separate_milestones():
    person = TargetScript()
    person_variables = person.authorize(method=1)
    assert person_variables["TOP_history_event"][0] == 6
    assert person_variables["TOP_history_reason"][0] == 31
    person.temps["TOP_tier"] = 2
    person.run("TOP_complete_operation", 1)
    person_events = [
        person_variables["TOP_history_event"][int(row)]
        for row in person_variables["TOP_history_rows"]
    ]
    assert person_events[:3] == [6, 10, 7]

    organization = TargetScript()
    organization_variables = organization.authorize_organization(objective=2)
    assert organization_variables["TOP_history_event"][0] == 10
    assert organization_variables["TOP_history_reason"][0] == 42
    organization.run("TOP_resolve_organization_operation", 1)
    assert organization_variables["TOP_history_event"][1] == 7


def test_history_rows_retain_package_and_case_keys_and_roll_over():
    script = TargetScript()
    variables = script.target(11)
    variables["TOP_history_cycle"][11] = 1
    variables["TOP_case_sequence"][11] = 5
    script.globals["TOP_clock"] = 40
    script.temps["TOP_history_current_event"] = 4
    script.call("TOP_log_person_milestone", TARGET=11)

    assert variables["TOP_history_rows"] == [0]
    assert variables["TOP_history_package_cycle"][0] == 1
    assert variables["TOP_history_case_sequence"][0] == 5
    assert variables["TOP_history_day"][0] == 40

    variables["TOP_history_cycle"][11] = 2
    variables["TOP_case_sequence"][11] = 9
    script.globals["TOP_clock"] = 60
    script.temps["TOP_history_current_event"] = 1
    script.call("TOP_log_person_milestone", TARGET=11)
    assert variables["TOP_history_package_cycle"][1] == 2
    assert variables["TOP_history_case_sequence"][1] == 0

    for day in range(61, 190):
        script.globals["TOP_clock"] = day
        script.temps["TOP_history_current_event"] = 2
        script.call("TOP_log_person_milestone", TARGET=11)

    assert len(variables["TOP_history_rows"]) == 128
    assert variables["TOP_history_rows"][0] == 3
    assert variables["TOP_history_day"][0] == 187
    assert variables["TOP_history_day"][1] == 188
    assert variables["TOP_history_day"][2] == 189


def test_history_view_follows_selected_subject():
    script = TargetScript()
    variables = script.target(11)
    script.target(12)
    view = (
        ROOT / "common/scripted_effects/00_targeted_operations_effects.txt"
    ).read_text(encoding="utf-8")
    script.effects.update(_parse_race_script(view))
    script.stubs.remove("TOP_build_view")
    variables["TOP_tab"] = 6
    for target in (11, 12):
        variables["TOP_history_cycle"][target] = 1
        script.temps["TOP_history_current_event"] = 1
        script.call("TOP_log_person_milestone", TARGET=target)

    variables["TOP_selected"] = 11
    script.run("TOP_build_view", 1)
    assert variables["TOP_visible_history"] == [0]
    variables["TOP_selected"] = 12
    script.run("TOP_build_view", 1)
    assert variables["TOP_visible_history"] == [1]


def test_history_wrap_refreshes_an_open_tab_when_another_subject_replaces_its_row():
    script = TargetScript()
    variables = script.target(11)
    script.target(12)
    variables["TOP_tab"] = 6
    variables["TOP_selected_kind"] = 1
    variables["TOP_selected"] = 11
    variables["TOP_history_rows"] = [0]
    variables["TOP_visible_history"] = [0]
    variables["TOP_history_cursor"] = 0
    before = script.external["TOP_refresh_view", 1]
    script.temps["TOP_history_current_event"] = 2

    script.call("TOP_log_person_milestone", TARGET=12)

    assert variables["TOP_visible_history"] == []
    assert script.external["TOP_refresh_view", 1] == before + 1


def test_top_loop_bindings_use_shared_static_validation():
    paths = [
        path
        for folder in ("common/scripted_effects", "common/scripted_triggers")
        for path in (ROOT / folder).glob("*targeted_operations*.txt")
    ]
    assert paths
    findings = [
        finding
        for path in paths
        for finding in vsp._validate_call_sites_in_file(
            (str(path), {}, str(ROOT), frozenset(), frozenset(), frozenset())
        )
        if finding[0] == "uppercase-loop-binding"
    ]
    assert findings == []


def discovery_script():
    script = TargetScript()
    script.effects.update(
        _parse_race_script(
            (
                ROOT / "common/scripted_effects/00_targeted_operations_effects.txt"
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


ENCODED_STATE = -10737.40617


STATE_GUARDS = (
    (
        "scripted_effects/00_targeted_operations_effects.txt",
        "TOP_import_target_location",
        "TOP_import_state",
    ),
    (
        # Two guards: the var: scope open, and the monthly relocation roll.
        "scripted_effects/00_targeted_operations_effects.txt",
        "TOP_global_monthly",
        "global.TOP_state^TOP_target",
        2,
    ),
    (
        "scripted_effects/00_targeted_operations_effects.txt",
        "TOP_register_missing_organizations",
        "global.TOP_state^TOP_target",
    ),
    (
        "scripted_effects/00_targeted_operations_effects.txt",
        "TOP_update_detained_targets",
        "global.TOP_custody_state^top_prisoner",
    ),
    (
        "scripted_effects/04_targeted_operations_cases.txt",
        "TOP_end_visit",
        "global.TOP_visit_return_state^top_visit_target",
    ),
    (
        "scripted_effects/04_targeted_operations_cases.txt",
        "TOP_end_visit",
        "TOP_visit_restore_state",
    ),
    (
        "scripted_triggers/01_targeted_operations_triggers.txt",
        "TOP_person_package_ready",
        "TOP_lead_state^TOP_arg_target",
    ),
    (
        "scripted_triggers/01_targeted_operations_triggers.txt",
        "TOP_organization_package_ready",
        "TOP_org_lead_state^TOP_group_target",
    ),
    (
        "scripted_triggers/01_targeted_operations_triggers.txt",
        "TOP_person_access_available",
        "TOP_access_state",
    ),
    (
        "scripted_triggers/01_targeted_operations_triggers.txt",
        "TOP_facility_access_available",
        "TOP_access_state",
    ),
    (
        "scripted_triggers/01_targeted_operations_triggers.txt",
        "TOP_facility_available",
        "TOP_facility_state",
    ),
    (
        "scripted_triggers/01_targeted_operations_triggers.txt",
        "TOP_person_review_valid",
        "TOP_proposal_state",
    ),
    (
        "scripted_triggers/01_targeted_operations_triggers.txt",
        "TOP_organization_review_valid",
        "TOP_proposal_state",
    ),
    (
        "scripted_triggers/01_targeted_operations_triggers.txt",
        "TOP_native_binding_unused",
        "TOP_binding_state",
    ),
    (
        "scripted_triggers/01_targeted_operations_triggers.txt",
        "TOP_visit_can_invite",
        "TOP_visit_trigger_state",
    ),
    (
        "scripted_localisation/01_targeted_operations_status.txt",
        "TOP_selected_location",
        "TOP_lead_state^TOP_selected",
    ),
)


def _location_guards(statements, variable):
    found = []
    for statement in statements:
        key, _, operand = statement
        if key == "NOT" and operand == [
            ("check_variable", "=", [(variable, "=", "0")])
        ]:
            found.append(statement)
        elif key == "check_variable" and operand == [(variable, ">", "0")]:
            found.append(statement)
        elif isinstance(operand, list):
            found.extend(_location_guards(operand, variable))
    return found


def _effect_text(path, name):
    text = (ROOT / path).read_text(encoding="utf-8")
    return _named_block(text, name)


def test_nested_registry_location_selection_writes_the_chain_temp():
    registry = (
        ROOT / "common/scripted_effects/01_targeted_operations_registry.txt"
    ).read_text(encoding="utf-8")
    for group in (1, 17):
        choice = _named_block(registry, f"TOP_choose_location_{group}")
        activation = _named_block(registry, f"TOP_activate_group_{group}")
        assert "set_temp_variable = { TOP_activation_state = THIS }" in choice
        assert "set_temp_variable = { TOP_activation_host = controller }" in activation


def test_numeric_loop_selectors_write_results_to_chain_temps():
    find_org = _effect_text(
        "common/scripted_effects/00_targeted_operations_effects.txt",
        "TOP_find_group_org",
    )
    country_tick = _effect_text(
        "common/scripted_effects/00_targeted_operations_effects.txt",
        "TOP_country_tick",
    )
    modern = _effect_text(
        "common/scripted_effects/02_targeted_operations_authorization_effects.txt",
        "TOP_modern_country_opportunity",
    )
    political = _effect_text(
        "common/scripted_effects/02_targeted_operations_authorization_effects.txt",
        "TOP_political_country_opportunities",
    )
    successor = _effect_text(
        "common/scripted_effects/00_targeted_operations_effects.txt",
        "TOP_choose_successor",
    )
    visit = _effect_text(
        "common/scripted_effects/04_targeted_operations_cases.txt",
        "TOP_visit_country_opportunities",
    )
    liaison = _effect_text(
        "common/scripted_effects/00_targeted_operations_effects.txt",
        "TOP_request_liaison",
    )
    linked = _effect_text(
        "common/scripted_effects/00_targeted_operations_effects.txt",
        "TOP_exploit_linked_targets",
    )

    assert "{ TOP_org_slot = top_find_i }" in find_org
    assert "{ TOP_new_dossiers_this_tick = 1 }" in country_tick
    assert "{ TOP_modern_candidate = top_modern_target }" in modern
    assert "{ TOP_modern_best_score = TOP_modern_score }" in modern
    assert "{ TOP_political_candidate = top_political_person }" in political
    assert "{ TOP_political_lowest = TOP_political_score }" in political
    assert "{ TOP_candidate = top_generated_id }" in successor
    assert "global.TOP_state^TOP_predecessor" in successor
    assert "{ TOP_visit_open_candidate = top_visit_person }" in visit
    assert "TOP_visit_trigger_state = TOP_visit_open_state" in visit
    assert "{ TOP_liaison_pair_found = 1 }" in liaison
    assert "PREV.TOP_liaison_pair_until^top_liaison_index" in liaison
    assert "{ TOP_linked_first = top_linked_target }" in linked
    assert "{ TOP_linked_second = top_linked_target }" in linked
    assert linked.count("{ TOP_linked_best_score = TOP_linked_score }") == 2


def test_state_and_fifo_selectors_do_not_depend_on_loop_local_temporaries():
    visit = _effect_text(
        "common/scripted_effects/04_targeted_operations_cases.txt",
        "TOP_visit_country_opportunities",
    )
    oversight = _effect_text(
        "common/scripted_effects/00_targeted_operations_effects.txt",
        "TOP_dispatch_next_oversight",
    )
    transfer = _effect_text(
        "common/scripted_effects/00_targeted_operations_effects.txt",
        "TOP_transfer_recorded_custody",
    )

    assert "{ TOP_visit_open_state = THIS }" in visit
    assert "TOP_oversight_queue^0" in oversight
    assert "for_each_loop" not in oversight
    assert "global.TOP_custody_state^TOP_transfer_recipient_target = THIS" in transfer


@pytest.mark.parametrize("entry", STATE_GUARDS)
@pytest.mark.parametrize("state", (ENCODED_STATE, 101, 0))
def test_location_presence_guards_accept_nonzero_state_references(entry, state):
    path, block, variable = entry[:3]
    expected = entry[3] if len(entry) > 3 else 1
    text = (ROOT / "common" / path).read_text(encoding="utf-8")
    if block == "TOP_selected_location":
        start = text.rfind("defined_text", 0, text.index(f"name = {block}"))
        statements = _parse_race_script(_extract_block(text, start))["defined_text"]
    else:
        statements = _parse_race_script(_named_block(text, block))[block]
    guards = _location_guards(statements, variable)
    assert len(guards) == expected
    script = TargetScript()
    script.temps[variable] = state
    for guard in guards:
        assert script.condition([guard], 1) == (state != 0)


@pytest.mark.parametrize("state", (ENCODED_STATE, 105))
def test_import_preserves_explicit_state_instead_of_random_fallback(state):
    script = TargetScript()
    script.state(state, 2)
    assert script.countries[2]["states"][0] != state
    script.temps["TOP_import_state"] = state
    script.call("TOP_import_target_location", 2, TARGET=1)
    assert script.globals["TOP_state"][1] == state
    assert script.globals["TOP_host"][1] == 2
    assert script.globals["TOP_active_targets"] == [1]
    assert script.temps["TOP_import_state"] == 0


@pytest.mark.parametrize("state", (ENCODED_STATE, 105))
def test_monthly_host_refresh_resolves_changed_state_controller(state):
    script = TargetScript()
    script.state(state, 3)
    script.target(1, host=2, state=state)
    # The harness always takes a `chance`, so the monthly relocation roll would
    # move the target. A target mid-visit is exempt from it.
    script.globals["TOP_visit_status"] = ScriptArray([0] * 200)
    script.globals["TOP_visit_status"][1] = 1
    script.stubs.add("TOP_activate_candidates")
    script.run("TOP_global_monthly", 1)
    assert script.globals["TOP_state"][1] == state
    assert script.globals["TOP_host"][1] == 3


@pytest.mark.parametrize("state", (ENCODED_STATE, 105))
def test_monthly_organization_truth_tracks_the_recorded_state_controller(state):
    script = TargetScript()
    script.state(state, 3)
    script.organization_truth(12, host=2, state=state)
    script.stubs.add("TOP_activate_candidates")

    script.run("TOP_global_monthly", 1)

    assert script.globals["TOP_group_host"][12] == 3
    assert script.globals["TOP_group_state"][12] in script.countries[3]["states"]


def test_monthly_truth_clears_zero_state_hosts_without_opening_country_zero_scope():
    script = TargetScript()
    script.target(1, host=2, state=0)
    script.organization_truth(12, host=2, state=0)
    script.stubs.add("TOP_activate_candidates")

    script.run("TOP_global_monthly", 1)

    assert script.globals["TOP_host"][1] == 0
    assert script.globals["TOP_group_host"][12] == 0


@pytest.mark.parametrize("state", (ENCODED_STATE, 105, 0))
@pytest.mark.parametrize("kind", (1, 2, 3))
def test_facility_availability_keeps_building_and_missing_state_requirements(
    state, kind
):
    script = TargetScript()
    if state:
        script.state(state, 2)
        script.countries[state]["vars"]["industrial_complex"] = 1
        script.countries[state]["resources"] = ["oil"]
    script.temps.update(TOP_facility_state=state, TOP_facility_kind=kind)
    trigger = script.triggers["TOP_facility_available"]
    assert script.condition(trigger, 1) == (state != 0)
    if state:
        script.countries[state]["vars"].update(industrial_complex=0, infrastructure=0)
        script.countries[state]["resources"] = []
        assert not script.condition(trigger, 1)


@pytest.mark.parametrize("state", (ENCODED_STATE, 105))
@pytest.mark.parametrize("method", (2, 5))
def test_host_review_and_case_preserve_state_and_normal_cost(state, method):
    review = ReviewScript()
    review.move_target(1, state, 2)
    review.ready_for_host(method)
    assert review.actor.get("TOP_proposal_stage") == 2
    assert review.actor["TOP_proposal_state"] == state
    assert review.countries[1]["power"] == 200
    review.run("TOP_send_host_request")
    assert review.countries[2]["vars"]["TOP_incoming_state"] == state
    review.call("TOP_answer_host_request", identifier=2, CONSENT=1)
    review.run("TOP_close_review_event")
    review.run("TOP_approve_review")
    assert review.case(1, "state") == state
    assert review.case(1, "consent") == 1
    assert review.case(1, "phase") == 2
    assert review.actor["TOP_authorized_state"] == state
    assert review.countries[1]["power"] == 150
    assert not review.binding(method=method, state=state)
    review.begin_operation()
    assert review.case(1, "phase") == 3
    assert review.binding(method=method, state=state)
    review.run("TOP_approve_review")
    assert review.countries[1]["power"] == 150


@pytest.mark.parametrize("blocked", ("funding", "consent"))
def test_encoded_state_cannot_bypass_review_funding_or_cooperation_consent(blocked):
    review = ReviewScript()
    review.move_target(1, ENCODED_STATE, 2)
    review.ready_for_host(method=5 if blocked == "consent" else 2)
    assert review.actor.get("TOP_proposal_stage") == 2
    review.run("TOP_open_senior_review")
    review.run("TOP_close_review_event")
    if blocked == "funding":
        review.countries[1]["power"] = 49
    power = review.countries[1]["power"]
    review.run("TOP_approve_review")
    assert review.case(1, "phase") == 1
    assert review.countries[1]["power"] == power
    assert "TOP_authorized_target" not in review.actor


@pytest.mark.parametrize("state", (ENCODED_STATE, 9999, 10000, 0))
def test_native_binding_preserves_upper_boundary_and_zero_sentinel(state):
    review = ReviewScript()
    review.temps.update(TOP_arg_target=1, TOP_arg_method=2, TOP_arg_state=state)
    assert review.condition(review.triggers["TOP_native_binding_unused"], 1) == (
        state != 0 and state < 10000
    )
    assert review.temps["TOP_binding_key"] == pytest.approx(40000 + state * 4 + 2)


def test_retired_encoded_native_binding_cannot_be_recycled():
    review = ReviewScript()
    review.move_target(1, ENCODED_STATE, 2)
    review.approve_unilateral()
    review.begin_operation()
    assert review.binding(state=ENCODED_STATE)
    sequence = review.case(1, "sequence")
    review.call("TOP_close_case", TARGET=1, SEQUENCE=sequence)
    assert review.actor["TOP_retired_native_bindings"] == pytest.approx(
        [40000 + ENCODED_STATE * 4 + 2]
    )
    review.approve_unilateral()
    assert review.case(1, "phase") == 0
    assert not review.binding(state=ENCODED_STATE)
    assert review.countries[1]["power"] == 150
    review.approve_unilateral(method=1)
    assert review.case(1, "phase") == 2
    review.begin_operation()
    assert review.binding(method=1, state=ENCODED_STATE)
    assert review.countries[1]["power"] == 100


SCOPED_NAME = re.compile(r"(?<![\w.])(?:(?:PREV|ROOT|FROM)\.)+([A-Za-z_]\w*)")


TEMP_NAME = re.compile(
    r"\b(?:(?:set|add_to|subtract_from|multiply|divide|clamp)_temp_variable\s*=\s*\{"
    r"|\b(?:value|index)\s*=)\s*(?:(?:PREV|ROOT|FROM)\.)*([A-Za-z_]\w*)"
)


PERSISTENT_NAME = re.compile(
    r"\bset_variable\s*=\s*\{\s*(?:var\s*=\s*)?(?:(?:PREV|ROOT|FROM)\.)*([A-Za-z_]\w*)"
)


def test_temp_variables_are_never_scope_prefixed():
    # The engine reads PREV.x / ROOT.x as 0 when x is a temp; temps are chain-wide.
    scripts = [
        path
        for folder in ("common", "events")
        for path in (ROOT / folder).rglob("*argeted*perations*.txt")
    ]
    texts = {
        path: "\n".join(
            line.split("#", 1)[0]
            for line in path.read_text(encoding="utf-8-sig").splitlines()
        )
        for path in scripts
    }
    temps = {match for text in texts.values() for match in TEMP_NAME.findall(text)}
    temps -= {
        match for text in texts.values() for match in PERSISTENT_NAME.findall(text)
    }
    found = [
        f"{path.relative_to(ROOT)}: {match.group(0)}"
        for path, text in texts.items()
        for match in SCOPED_NAME.finditer(text)
        if match.group(1) in temps
    ]
    assert not found
