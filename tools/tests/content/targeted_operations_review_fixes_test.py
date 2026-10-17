import re

import pytest
from targeted_operations_authorization_test import ReviewScript
from targeted_operations_core_test import TargetScript
from targeted_operations_model_test import (
    _extract_block,
    _parse_race_script,
)
from targeted_operations_redesign_test import block, read


def test_top_raid_and_political_category_use_dynamic_rule_gates():
    category = read("common/decisions/categories/targeted_operations_political.txt")
    assert "allowed = { TOP_enabled = yes }" not in category
    assert "allowed = { always = yes }" in category
    assert "visible = { TOP_enabled = yes }" in category


def test_ct_registration_reads_the_unscoped_host_region():
    # Temp variables are unscoped, so the caller reads region_idx directly, as 00_ct_effects.txt does.
    effect = block(
        "common/scripted_effects/01_targeted_operations_world.txt",
        "TOP_append_ct_organization",
    )
    assert "PREV.region_idx" not in effect
    assert "global.active_terror_org_region = region_idx" in effect


def test_prosecuted_iraqi_fugitives_count_toward_resolution():
    effect = block(
        "common/scripted_effects/01_targeted_operations_legacy_effects.txt",
        "TOP_update_iraq_progress",
    )
    assert "global.TOP_status^top_iraq_target < 5" in effect


def test_false_location_keeps_the_lead_when_no_other_state_is_found():
    for name, field in (
        ("TOP_maybe_false_person_location", "TOP_lead_state^TOP_target"),
        (
            "TOP_maybe_false_organization_location",
            "TOP_org_lead_state^TOP_group_target",
        ),
    ):
        effect = block(
            "common/scripted_effects/06_targeted_operations_redesign.txt", name
        )
        assert (
            "if = { limit = { NOT = { check_variable = { TOP_false_state = 0 } } } "
            f"set_variable = {{ {field} = TOP_false_state }} }}"
        ) in effect


def test_extended_runtime_initializes_once_without_save_version_migrations():
    redesign = block(
        "common/scripted_effects/06_targeted_operations_redesign.txt",
        "TOP_initialize_redesign_global",
    )
    runtime = read("common/scripted_effects/05_targeted_operations_runtime.txt")
    setup = block(
        "common/scripted_effects/05_targeted_operations_runtime.txt",
        "TOP_setup_extended_runtime",
    )
    assert "TOP_setup_extended_runtime = yes" in redesign
    assert "TOP_extended_runtime_version" not in runtime
    assert "TOP_setup_extended_runtime = yes" not in runtime
    assert "global.TOP_visit_open_interval = 91" in setup
    assert "clear_array = global.TOP_crisis_queue_actors" in setup


ISI_FALLBACK = (
    "limit = { OR = { TOP_enabled = no AND = { check_variable = { "
    "global.TOP_group_leader^3 = 0 } check_variable = { global.TOP_status^29 < 2 } } } }"
)
SHABAAB_FALLBACK = "limit = { OR = { TOP_enabled = no check_variable = { global.TOP_status^45 < 2 } } }"


@pytest.mark.parametrize(
    "fallback,group,predecessor",
    ((ISI_FALLBACK, 3, 29), (SHABAAB_FALLBACK, 6, 45)),
    ids=("isi", "al_shabaab"),
)
@pytest.mark.parametrize(
    "leader,status,expected",
    ((0, 1, True), (0, 3, False)),
    ids=("predecessor_active", "predecessor_removed"),
)
def test_formation_falls_back_to_the_legacy_leader_until_top_selects_one(
    fallback, group, predecessor, leader, status, expected
):
    # Formation can run before the monthly pulse activates the group, so TOP has no leader to install yet.
    script = TargetScript()
    script.globals["TOP_rule_mode"] = 1
    script.globals["TOP_group_leader"][group] = leader
    script.globals["TOP_status"][predecessor] = status
    limit = _parse_race_script(fallback)["limit"]
    assert script.condition(limit, 1) == expected


def test_collection_rebuild_prunes_inactive_typed_assignments_and_pauses_packages():
    script = TargetScript()
    variables = script.target(11)
    script.target(12)
    script.target(15)
    variables["TOP_package_state"][11] = 2
    variables["TOP_package_state"][12] = 2
    variables["TOP_package_state"][15] = 2
    variables["TOP_collection_focus"][12] = 2
    script.globals["TOP_status"][11] = 2
    script.ineligible_roles.add(15)
    script.globals["TOP_group_destroyed"][2] = 1
    variables["TOP_org_package_state"][2] = 2
    variables["TOP_collecting_subjects"] = [11, 12, 15, 1002]

    script.run("TOP_process_collection_assignments", 1)

    assert variables["TOP_collecting_subjects"] == [12]
    assert variables["TOP_package_state"][11] == 1
    assert variables["TOP_package_state"][12] == 2
    assert variables["TOP_package_state"][15] == 1
    assert variables["TOP_org_package_state"][2] == 1
    suspended = [
        (
            variables["TOP_history_subject_kind"][int(row)],
            variables["TOP_history_subject_id"][int(row)],
        )
        for row in variables["TOP_history_rows"]
    ]
    assert suspended == [(1, 11), (1, 15), (2, 2)]
    assert [
        variables["TOP_history_event"][int(row)]
        for row in variables["TOP_history_rows"]
    ] == [3, 3, 3]
    assert [
        variables["TOP_history_reason"][int(row)]
        for row in variables["TOP_history_rows"]
    ] == [23, 23, 23]


def test_liaison_merge_never_replaces_a_known_location_with_an_empty_report():
    script = TargetScript()
    variables = script.target(11)
    script.globals["TOP_clock"] = 100
    variables["TOP_lead_state"][11] = 101
    variables["TOP_lead_host"][11] = 2
    variables["TOP_lead_age"][11] = 40
    variables["TOP_lead_report_clock"][11] = 60
    script.temps.update(
        TOP_liaison_snapshot_kind=1,
        TOP_liaison_snapshot_id=11,
        TOP_liaison_axis_1=90,
        TOP_liaison_axis_2=0,
        TOP_liaison_axis_3=90,
        TOP_liaison_state=0,
        TOP_liaison_host=0,
        TOP_liaison_age=0,
        TOP_liaison_response_reliability=1,
        TOP_liaison_leak_chance=0,
    )
    script.run("TOP_merge_liaison_snapshot", 1)
    assert variables["TOP_lead_state"][11] == 101
    assert variables["TOP_lead_host"][11] == 2
    assert variables["TOP_lead_age"][11] == 40

    variables["TOP_org_lead_state"][2] = 101
    variables["TOP_org_lead_host"][2] = 2
    variables["TOP_org_lead_age"][2] = 35
    variables["TOP_org_lead_report_clock"][2] = 65
    script.temps.update(
        TOP_liaison_snapshot_kind=2,
        TOP_liaison_snapshot_id=2,
        TOP_liaison_axis_1=90,
        TOP_liaison_axis_2=0,
        TOP_liaison_axis_3=90,
        TOP_liaison_state=0,
        TOP_liaison_host=0,
        TOP_liaison_age=0,
    )
    script.run("TOP_merge_liaison_snapshot", 1)
    assert variables["TOP_org_lead_state"][2] == 101
    assert variables["TOP_org_lead_host"][2] == 2
    assert variables["TOP_org_lead_age"][2] == 35


def test_linked_exploitation_skips_fully_saturated_dossiers():
    script = TargetScript()
    variables = script.target(11, status=2)
    script.globals["TOP_custodian"][11] = 1
    script.globals["TOP_exploitation_until"][11] = 100
    script.globals["TOP_affiliation"][11] = 1
    for target, score in ((12, 100), (13, 10), (14, 20)):
        script.target(target)
        script.globals["TOP_affiliation"][target] = 1
        for axis in (
            "TOP_identity_confidence",
            "TOP_location_confidence",
            "TOP_pattern_confidence",
        ):
            variables[axis][target] = score
    variables["TOP_selected"] = 11

    script.call("TOP_exploit_linked_targets", TARGET=11)

    for axis in (
        "TOP_identity_confidence",
        "TOP_location_confidence",
        "TOP_pattern_confidence",
    ):
        assert variables[axis][12] == 100
        assert variables[axis][13] == 30
        assert variables[axis][14] == 40
    assert script.globals["TOP_exploited"][11] == 1


def test_prosecuting_an_iraq_hunt_target_refreshes_legacy_progress_immediately():
    script = TargetScript()
    variables = script.target(56, status=2)
    script.globals["TOP_custodian"][56] = 1
    variables["TOP_selected"] = 56
    before = script.external["TOP_update_iraq_progress", 1]

    script.run("TOP_prosecute_selected", 1)

    assert script.globals["TOP_status"][56] == 4
    assert script.external["TOP_update_iraq_progress", 1] == before + 1


def test_review_risk_calculators_preserve_visit_exception_and_ordinary_cap():
    review = ReviewScript()
    review.actor.update(
        TOP_proposal_target=1,
        TOP_proposal_method=1,
        TOP_proposal_pattern=0,
        TOP_proposal_host_posture=1,
        TOP_proposal_doctrine=4,
        TOP_proposal_rigor=1,
    )
    review.actor["TOP_case_visit_status^1"] = 0
    review.run("TOP_calculate_person_proposal_risks")
    assert review.actor["TOP_proposal_exposure_score"] == 95
    assert review.actor["TOP_proposal_harm_risk"] == 40

    review.actor["TOP_case_visit_status^1"] = 1
    review.run("TOP_calculate_person_proposal_risks")
    assert review.actor["TOP_proposal_harm_risk"] == 100

    review.actor.update(
        TOP_proposal_pattern=0,
        TOP_proposal_host_posture=3,
        TOP_proposal_doctrine=4,
        TOP_proposal_rigor=1,
    )
    review.run("TOP_calculate_organization_proposal_risks")
    assert review.actor["TOP_proposal_exposure_score"] == 40
    assert review.actor["TOP_proposal_harm_risk"] == 40


def test_cooperative_host_recalculates_and_freezes_risk_and_liaison_relationship():
    review = ReviewScript()
    review.ready_for_host(method=1)
    assert review.actor["TOP_proposal_exposure_score"] == 85
    review.run("TOP_send_host_request")
    review.call("TOP_answer_host_request", identifier=2, POSTURE=4)
    assert review.actor["TOP_proposal_exposure_score"] == 50
    assert review.countries[2]["vars"]["TOP_liaison_partners"] == [1]
    review.run("TOP_close_review_event")
    review.run("TOP_approve_review")
    assert review.case(1, "exposure_score") == 50
    assert review.case(1, "harm_risk") == 0


def test_pending_attribution_and_open_oversight_block_case_reuse_then_reset():
    review = ReviewScript()
    review.actor["TOP_attribution_pending_people"] = [1]
    review.call("TOP_begin_review", METHOD=2)
    assert review.actor.get("TOP_proposal_stage", 0) == 0

    review.actor["TOP_attribution_pending_people"] = []
    review.actor["TOP_case_oversight_open^1"] = 1
    review.call("TOP_begin_review", METHOD=2)
    assert review.actor.get("TOP_proposal_stage", 0) == 0

    review.actor.update(
        {
            "TOP_case_oversight_open^1": 0,
            "TOP_case_attribution_due^1": 42,
            "TOP_case_attribution_investigated^1": 1,
            "TOP_case_oversight^1": 3,
            "TOP_case_crisis_opened^1": 1,
        }
    )
    review.call("TOP_begin_review", METHOD=2)
    assert review.actor["TOP_proposal_stage"] == 1
    assert review.actor["TOP_case_attribution_due^1"] == 0
    assert review.actor["TOP_case_attribution_investigated^1"] == 0
    assert review.actor["TOP_case_oversight^1"] == 0
    assert review.actor["TOP_case_oversight_open^1"] == 0
    assert review.actor["TOP_case_crisis_opened^1"] == 0

    organization = ReviewScript()
    organization.actor.update(
        {
            "TOP_selected_kind": 2,
            "TOP_selected_organization": 1,
            "TOP_org_known^1": 1,
            "TOP_org_package_state^1": 1,
            "TOP_org_verification^1": 95,
            "TOP_org_location^1": 95,
            "TOP_org_activity^1": 95,
            "TOP_org_lead_age^1": 0,
            "TOP_org_lead_state^1": 100,
            "TOP_org_lead_host^1": 2,
            "TOP_org_case_phase^1": 0,
            "TOP_org_case_oversight_open^1": 0,
            "TOP_active_organization_cases": [],
        }
    )
    organization.globals.update(
        {
            "TOP_group_window^1": 1,
            "TOP_group_destroyed^1": 0,
            "TOP_group_facility_objectives^1": 7,
        }
    )
    organization.actor["TOP_attribution_pending_organizations"] = [1]
    organization.run("TOP_begin_organization_review")
    assert organization.actor.get("TOP_proposal_stage", 0) == 0

    organization.actor["TOP_attribution_pending_organizations"] = []
    organization.actor["TOP_org_case_oversight_open^1"] = 1
    organization.run("TOP_begin_organization_review")
    assert organization.actor.get("TOP_proposal_stage", 0) == 0

    organization.actor.update(
        {
            "TOP_org_case_oversight_open^1": 0,
            "TOP_org_case_attribution_due^1": 42,
            "TOP_org_case_attribution_investigated^1": 1,
            "TOP_org_case_oversight^1": 3,
        }
    )
    organization.run("TOP_begin_organization_review")
    assert organization.actor["TOP_proposal_stage"] == 1
    assert organization.actor["TOP_org_case_attribution_due^1"] == 0
    assert organization.actor["TOP_org_case_attribution_investigated^1"] == 0
    assert organization.actor["TOP_org_case_oversight^1"] == 0
    assert organization.actor["TOP_org_case_oversight_open^1"] == 0


def test_authoritative_review_gates_and_blocker_cover_pending_consequences():
    person = block(
        "common/scripted_triggers/01_targeted_operations_triggers.txt",
        "TOP_can_authorize",
    )
    organization = block(
        "common/scripted_triggers/07_targeted_operations_redesign.txt",
        "TOP_can_review_organization",
    )
    blocker = read("common/scripted_localisation/04_targeted_operations_redesign.txt")
    localization = read(
        "localisation/english/MD_targeted_operations_redesign_l_english.yml"
    )

    assert "TOP_attribution_pending_people = TOP_selected" in person
    assert "TOP_case_oversight_open^TOP_selected = 0" in person
    assert (
        "TOP_attribution_pending_organizations = TOP_selected_organization"
        in organization
    )
    assert "TOP_org_case_oversight_open^TOP_selected_organization = 0" in organization
    assert "name = TOP_action_blocker" in blocker
    assert "TOP_blocker_attribution_pending" in blocker
    assert (
        "prior operation's attribution investigation is still pending" in localization
    )


def test_authority_blocker_shows_package_and_reachable_ready_states():
    scripted_localization = read(
        "common/scripted_localisation/04_targeted_operations_redesign.txt"
    )
    action_start = scripted_localization.index("name = TOP_action_blocker")
    action_end = scripted_localization.index("\n}\n", action_start)
    action = scripted_localization[action_start:action_end]

    package = action.index("localization_key = TOP_blocker_package_not_developed")
    ready = action.index(
        "TOP_can_begin_selected_operation = yes } localization_key = TOP_blocker_ready"
    )
    capability = action.index("localization_key = TOP_blocker_capability")
    assert "check_variable = { TOP_tab = 2 }" in action[:package]
    assert ready < capability


def test_liaison_eligibility_uses_persistent_relationship_and_free_inbox():
    trigger = block(
        "common/scripted_triggers/07_targeted_operations_redesign.txt",
        "TOP_can_request_liaison",
    )
    relationship = block(
        "common/scripted_triggers/07_targeted_operations_redesign.txt",
        "TOP_liaison_relationship_available",
    )
    request = block(
        "common/scripted_effects/09_targeted_operations_depth.txt",
        "TOP_request_liaison",
    )
    answer = block(
        "common/scripted_effects/02_targeted_operations_authorization_effects.txt",
        "TOP_answer_host_request",
    )

    assert "TOP_incoming_liaison_actor = 0" in trigger
    assert "TOP_liaison_relationship_available = yes" in trigger
    assert "is_in_array = { TOP_liaison_partners = PREV }" in relationship
    assert "TOP_case_host_posture" not in trigger
    assert "TOP_org_case_host_posture" not in trigger
    assert "TOP_liaison_partner = PREV" not in trigger
    assert request.index("TOP_can_request_liaison = yes") < request.index(
        "add_political_power = -25"
    )
    assert "add_to_array = { TOP_liaison_partners = TOP_incoming_actor }" in answer


def test_liaison_ui_uses_an_eligible_selected_source_instead_of_the_subject_host():
    selected_trigger = block(
        "common/scripted_triggers/07_targeted_operations_redesign.txt",
        "TOP_can_request_selected_liaison",
    )
    selected_effect = block(
        "common/scripted_effects/09_targeted_operations_depth.txt",
        "TOP_request_selected_liaison",
    )
    cycle = block(
        "common/scripted_effects/09_targeted_operations_depth.txt",
        "TOP_cycle_liaison_source",
    )
    gui = read("interface/targeted_operations.gui")

    assert "TOP_liaison_target_country = TOP_liaison_source" in selected_trigger
    assert "TOP_liaison_target_country = TOP_liaison_source" in selected_effect
    assert "TOP_lead_host^TOP_selected" not in selected_trigger
    assert "TOP_org_lead_host^TOP_selected_organization" not in selected_trigger
    assert "TOP_lead_host^TOP_selected" not in selected_effect
    assert "TOP_org_lead_host^TOP_selected_organization" not in selected_effect
    assert "TOP_liaison_relationship_available = yes" in cycle
    assert "TOP_liaison_sources = PREV" in cycle
    assert "TOP_liaison_source = TOP_liaison_sources^TOP_liaison_source_index" in cycle
    assert 'name = "TOP_liaison_source"' in gui


def test_capture_crisis_remote_access_vip_and_frozen_resolution_contracts():
    shared = block(
        "common/scripted_effects/08_targeted_operations_resolution.txt",
        "TOP_apply_shared_consequences",
    )
    access = block(
        "common/scripted_triggers/01_targeted_operations_triggers.txt",
        "TOP_person_access_available",
    )
    vip = block(
        "common/scripted_triggers/07_targeted_operations_redesign.txt",
        "TOP_can_assign_vip_detail",
    )
    person = block(
        "common/scripted_effects/08_targeted_operations_resolution.txt",
        "TOP_calculate_person_consequences",
    )
    organization = block(
        "common/scripted_effects/08_targeted_operations_resolution.txt",
        "TOP_calculate_organization_consequences",
    )

    assert "TOP_result = 2" in shared
    assert "TOP_start_capture_crisis = yes" in shared
    assert "TOP_start_strategic_leader_crisis = yes" in shared
    assert "Native launch revalidates base, equipment, range, and DLC gates" in access
    assert "TOP_role_target = TOP_arg_target" in vip
    assert "TOP_authored_role_eligible = yes" in vip
    assert "TOP_case_exposure_score^TOP_target" in person
    assert "TOP_case_harm_risk^TOP_target" in person
    assert "TOP_get_defensive_modifiers" not in person
    assert "TOP_org_case_exposure_score^TOP_group_target" in organization
    assert "TOP_org_case_harm_risk^TOP_group_target" in organization


def test_every_effectful_redesign_event_option_has_exactly_one_log():
    events = read("events/Targeted Operations Redesign.txt")
    options = [
        _extract_block(events, match.start())
        for match in re.finditer(r"(?m)^\toption = \{", events)
    ]
    assert options
    for option in options:
        assert option.count("\n\t\tlog = ") == 1
