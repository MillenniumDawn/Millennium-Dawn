import json
import re
from pathlib import Path

import pytest
from targeted_operations_authorization_test import ReviewScript
from targeted_operations_core_test import TargetScript
from targeted_operations_helpers import (
    _extract_block,
    _named_block,
    _parse_race_script,
    block,
    read,
    read_top_source,
)

ROOT = Path(__file__).resolve().parents[3]


def test_game_rule_modes_and_authoritative_eligibility_contract():
    rules = read("common/game_rules/01_targeted_operations.txt")
    triggers = read("common/scripted_triggers/01_targeted_operations_triggers.txt")
    effects = read("common/scripted_effects/00_targeted_operations_effects.txt")

    rule = _parse_race_script(rules)["TOP_game_rule"]
    options = [
        (next(value for key, _, value in body if key == "name"), kind)
        for kind, _, body in rule
        if kind in {"default", "option"}
    ]
    assert len(options) == len({name for name, _ in options})
    assert dict(options) == {
        "TOP_limited_sandbox_option": "default",
        "TOP_full_sandbox_option": "option",
        "TOP_disabled_option": "option",
    }
    predicates = _parse_race_script(triggers)
    assert {
        "TOP_enabled",
        "TOP_limited_sandbox",
        "TOP_full_sandbox",
        "TOP_person_operational_eligible",
        "TOP_organization_operational_eligible",
        "TOP_facility_operational_eligible",
    } <= predicates.keys()
    assert ("is_ai", "=", "no") in predicates["TOP_human_offense"]
    for name in (
        "TOP_person_operational_eligible",
        "TOP_organization_operational_eligible",
    ):
        assert ("TOP_human_offense", "=", "yes") in predicates[name]

    assert "TOP_rule_enabled" not in effects


def test_all_generated_native_raids_are_player_only():
    raids = _parse_race_script(read("common/raids/targeted_operations_raids.txt"))[
        "types"
    ]
    assert raids
    for name, _, definition in raids:
        ai = next(value for key, _, value in definition if key == "ai_will_do")
        assert ("base", "=", "0") in ai, name


def test_manifest_has_four_classes_and_first_class_irgc_organizations():
    manifest = json.loads(read("tools/data/targeted_operations.json"))
    groups = {group["id"]: group for group in manifest["groups"]}

    assert set(manifest["facility_objective_defaults"]) == {
        "militant_network",
        "state_security",
        "political_executive",
        "civilian_organization",
    }
    assert {groups[index]["group_class"] for index in range(1, 11)} == {
        "militant_network"
    }
    assert {groups[index]["group_class"] for index in range(22, 25)} == {
        "militant_network"
    }
    assert groups[11]["group_class"] == "state_security"
    assert {groups[index]["group_class"] for index in (12, 17, 18, 19, 20)} == {
        "state_security"
    }
    assert {groups[index]["group_class"] for index in (13, 14, 15, 16)} == {
        "political_executive"
    }
    assert groups[21]["group_class"] == "civilian_organization"

    for index in (12, 17, 18, 19, 20):
        assert groups[index]["public_identity"] is True
        assert "ct_id" not in groups[index]


def test_facility_objective_defaults_match_organization_classes():
    manifest = json.loads(read("tools/data/targeted_operations.json"))
    defaults = manifest["facility_objective_defaults"]

    assert defaults["militant_network"] == ["command", "training", "funding"]
    assert defaults["state_security"] == ["command", "training", "funding"]
    assert defaults["political_executive"] == ["command", "funding"]
    assert defaults["civilian_organization"] == ["command", "funding"]


def test_public_and_nonpublic_subject_seeding_uses_three_axes():
    public_seed = block(
        "common/scripted_effects/00_targeted_operations_effects.txt",
        "TOP_seed_public_subjects",
    )
    compatibility = read("common/scripted_effects/00_targeted_operations_effects.txt")

    assert "TOP_identity_confidence^top_public_target = 100" in public_seed
    assert "TOP_location_confidence^top_public_target" not in public_seed
    assert "TOP_pattern_confidence^top_public_target" not in public_seed
    assert "TOP_org_verification^top_public_group = 100" in public_seed
    assert "TOP_org_location^top_public_group" not in public_seed
    assert "TOP_org_activity^top_public_group" not in public_seed
    assert "TOP_identity_confidence^TOP_target = 15" in compatibility
    assert "TOP_location_confidence^TOP_target = 15" in compatibility
    assert "TOP_pattern_confidence^TOP_target = 0" in compatibility
    assert "TOP_org_verification^TOP_arg_group = 15" in compatibility
    assert "TOP_org_location^TOP_arg_group = 15" in compatibility
    organization_adapter = _named_block(compatibility, "TOP_add_organization_lead")
    assert "TOP_org_activity^TOP_arg_group = 15" not in organization_adapter
    assert (
        "add_to_variable = { TOP_org_activity^TOP_arg_group = TOP_arg_amount }"
        in organization_adapter
    )


def test_core_collection_preserves_decay_and_staleness_without_parallel_gains():
    effects = read("common/scripted_effects/00_targeted_operations_effects.txt")
    compatibility = read("common/scripted_effects/00_targeted_operations_effects.txt")
    triggers = read("common/scripted_triggers/01_targeted_operations_triggers.txt")
    for name in ("TOP_collect_person_pulse", "TOP_collect_organization_pulse"):
        gain = _named_block(effects, name)
        assert "international_terror_org_intel^TOP_org_slot" in gain
        assert "random" not in gain
        assert "TOP_gain" not in gain
        assert "lead_report_clock" not in gain
    for token in (
        "TOP_location_confidence^top_tick_target = 5",
        "TOP_pattern_confidence^top_tick_target = 3",
        "TOP_org_location^top_tick_group = 5",
        "TOP_org_activity^top_tick_group = 3",
    ):
        assert token in compatibility
    assert "TOP_lead_report_clock^TOP_arg_target" in triggers
    assert "TOP_org_lead_report_clock^TOP_group_target" in triggers
    assert triggers.count("TOP_current_lead_age < 57") == 2


def test_package_and_operation_capacity_are_independent():
    triggers = read("common/scripted_triggers/01_targeted_operations_triggers.txt")
    person_begin = block(
        "common/scripted_effects/04_targeted_operations_cases.txt",
        "TOP_begin_person_operation",
    )
    organization_begin = block(
        "common/scripted_effects/04_targeted_operations_cases.txt",
        "TOP_begin_organization_operation",
    )

    assert "TOP_collecting_subjects^num < 3" in triggers
    assert "TOP_operation_subject_kind = 0" in read(
        "common/scripted_triggers/01_targeted_operations_triggers.txt"
    )
    assert "TOP_operation_subject_kind = 1" in person_begin
    assert "TOP_operation_subject_kind = 2" in organization_begin
    assert "TOP_case_phase^TOP_arg_target = 3" in person_begin
    assert "TOP_org_case_phase^TOP_arg_group = 3" in organization_begin


def test_native_success_adjustments_are_frozen_into_the_engine_probability():
    person_begin = block(
        "common/scripted_effects/04_targeted_operations_cases.txt",
        "TOP_begin_person_operation",
    )
    callback = block(
        "common/scripted_effects/00_targeted_operations_effects.txt",
        "TOP_resolve_native_callback",
    )

    assert "TOP_case_native_success_bonus^TOP_arg_target = 10" in person_begin
    assert (
        "TOP_case_native_success_penalty^TOP_arg_target = TOP_defensive_success_penalty"
        in person_begin
    )
    assert "TOP_tier = 1" not in callback
    assert "TOP_defensive_success_penalty" not in callback


def test_packages_pause_resume_and_abandon_without_erasing_knowledge():
    effects = read("common/scripted_effects/04_targeted_operations_cases.txt")
    person_abandon = _named_block(effects, "TOP_abandon_person_package")
    organization_abandon = _named_block(effects, "TOP_abandon_organization_package")

    assert "TOP_package_state^TOP_selected = 0" in person_abandon
    assert "TOP_identity_confidence" not in person_abandon
    assert "TOP_location_confidence" not in person_abandon
    assert "TOP_pattern_confidence" not in person_abandon
    assert "TOP_org_package_state^TOP_selected_organization = 0" in organization_abandon
    assert "TOP_org_verification" not in organization_abandon
    assert "TOP_org_location" not in organization_abandon
    assert "TOP_org_activity" not in organization_abandon
    assert "TOP_stop_organization_collection = {" in effects


def test_typed_selection_and_immutable_review_snapshots_are_separate():
    person_review = block(
        "common/scripted_effects/02_targeted_operations_authorization_effects.txt",
        "TOP_begin_review",
    )
    organization_review = block(
        "common/scripted_effects/04_targeted_operations_cases.txt",
        "TOP_begin_organization_review",
    )

    assert "TOP_proposal_subject_kind = 1" in person_review
    assert "TOP_proposal_subject_kind = 2" in organization_review
    assert "TOP_proposal_method = 6" in organization_review
    for snapshot in (
        "TOP_proposal_identity",
        "TOP_proposal_location",
        "TOP_proposal_pattern",
        "TOP_proposal_lead_age",
        "TOP_proposal_state",
        "TOP_proposal_host",
        "TOP_proposal_access",
        "TOP_proposal_host_posture",
        "TOP_proposal_doctrine",
        "TOP_proposal_capability",
    ):
        assert snapshot in person_review
        assert snapshot in organization_review
    person_risk = block(
        "common/scripted_effects/02_targeted_operations_authorization_effects.txt",
        "TOP_calculate_person_proposal_risks",
    )
    organization_risk = block(
        "common/scripted_effects/04_targeted_operations_cases.txt",
        "TOP_calculate_organization_proposal_risks",
    )
    for review in (person_risk, organization_risk):
        assert "TOP_proposal_harm_risk > 40" in review
        assert "TOP_proposal_harm_risk = 40" in review
        assert "var = TOP_proposal_harm_risk min = 0 max = 100" in review
    assert "TOP_case_visit_status^TOP_proposal_target = 0" in person_risk


def test_delegated_doctrine_compresses_only_nonleader_review():
    person_review = block(
        "common/scripted_effects/02_targeted_operations_authorization_effects.txt",
        "TOP_begin_review",
    )
    organization_review = block(
        "common/scripted_effects/04_targeted_operations_cases.txt",
        "TOP_begin_organization_review",
    )
    triggers = read("common/scripted_triggers/01_targeted_operations_triggers.txt")

    assert "TOP_review_is_political_leader = {" in triggers
    assert "check_variable = { TOP_proposal_doctrine = 4 }" in person_review
    assert "NOT = { TOP_review_is_political_leader = yes }" in person_review
    assert "TOP_open_senior_review = yes" in person_review
    assert "check_variable = { TOP_proposal_doctrine = 4 }" in organization_review
    assert "TOP_open_senior_review = yes" in organization_review
    assert "country_event = TOP_authorization.1" in person_review
    assert "country_event = TOP_authorization.1" in organization_review


def test_leader_assassination_is_explicit_and_requires_enhanced_package():
    triggers = read("common/scripted_triggers/01_targeted_operations_triggers.txt")
    authorization = read(
        "common/scripted_effects/02_targeted_operations_authorization_effects.txt"
    )
    localization = read(
        "localisation/english/MD_targeted_operations_l_english.yml"
    ) + read("localisation/english/MD_targeted_operations_l_english.yml")

    assert "TOP_identity_confidence^TOP_arg_target > 79" in triggers
    assert "TOP_location_confidence^TOP_arg_target > 79" in triggers
    assert "TOP_pattern_confidence^TOP_arg_target > 79" in triggers
    assert "TOP_review_is_leader_assassination = yes" in authorization
    assert '"Assassination"' in localization
    assert '"Authorize Assassination"' in localization
    assert "capture feasibility" in localization.lower()


def test_native_facility_extension_owns_damage_and_replaces_disruption_only():
    organization = read("common/scripted_effects/04_targeted_operations_cases.txt")
    result = block(
        "common/scripted_effects/00_targeted_operations_effects.txt",
        "TOP_native_facility_damage",
    )
    for building in ("infrastructure", "arms_factory", "industrial_complex"):
        assert f"damage_building = {{ type = {building}" in result
    assert "TOP_tier > 1" in result
    assert "calculate_aa_defense_value = yes" in result
    assert "apply_raid_building_damage_success = yes" in result
    assert "apply_raid_building_damage_critical = yes" in result
    assert "TOP_group_disruption_type^TOP_group_target" in result
    assert "TOP_group_disruption_until^TOP_group_target" in result
    assert "add = 90" in result
    assert "kill_country_leader" not in organization + result
    assert "global.TOP_status" not in result
    assert "damage_building" not in _named_block(
        organization, "TOP_resolve_organization_operation"
    )


def test_resolution_uses_native_tiers_and_bda_never_rerolls_truth():
    resolution = read("common/scripted_effects/04_targeted_operations_cases.txt")
    compatibility = read("common/scripted_effects/00_targeted_operations_effects.txt")
    person_resolution = _named_block(resolution, "TOP_resolve_person_operation")
    bda = _named_block(compatibility, "TOP_process_timers")
    investigation = _named_block(resolution, "TOP_process_attribution_investigations")

    assert "randomize_temp_variable" not in person_resolution
    assert "TOP_intelligence_roll" not in person_resolution
    assert "TOP_tier > 1" in person_resolution
    assert "TOP_kill_target" not in bda
    assert "TOP_capture_target" not in bda
    assert (
        investigation.count(
            "random = { chance = TOP_investigation_chance add_to_variable"
        )
        == 2
    )
    assert "TOP_case_attribution^top_attribution_target < 3" in investigation
    assert "TOP_org_case_attribution^top_attribution_group < 3" in investigation


def test_exact_duration_processors_include_the_due_day():
    effects = read("common/scripted_effects/00_targeted_operations_effects.txt")
    cases = read("common/scripted_effects/04_targeted_operations_cases.txt")
    organizations = read("common/scripted_effects/04_targeted_operations_cases.txt")
    resolution = read("common/scripted_effects/04_targeted_operations_cases.txt")
    pressure = read("common/scripted_effects/00_targeted_operations_effects.txt")

    for token, source in (
        ("TOP_bda_due^top_bda_target compare = greater_than_or_equals", effects),
        ("TOP_case_until^top_timer_case compare = greater_than_or_equals", cases),
        (
            "TOP_org_case_until^top_org_case compare = greater_than_or_equals",
            organizations,
        ),
        (
            "TOP_case_attribution_due^top_attribution_target compare = greater_than_or_equals",
            resolution,
        ),
        (
            "TOP_org_case_attribution_due^top_attribution_group compare = greater_than_or_equals",
            resolution,
        ),
        (
            "global.TOP_pressure_decay_due compare = greater_than_or_equals",
            pressure,
        ),
    ):
        assert token in source


def test_archive_is_typed_and_circular_at_128_rows():
    initialization = read(
        "common/scripted_effects/01_targeted_operations_registry.txt"
    ) + read("common/scripted_effects/00_targeted_operations_effects.txt")
    resolution = read("common/scripted_effects/04_targeted_operations_cases.txt")

    for field in (
        "subject_kind",
        "subject_id",
        "objective",
        "host",
        "identity",
        "location",
        "pattern",
        "lead_age",
        "access",
        "host_posture",
        "doctrine",
        "rigor",
        "physical",
        "bda",
        "attribution",
        "harm",
        "custodian",
        "disposition",
        "custody_token",
        "sequence",
    ):
        assert f"TOP_archive_{field} = 128" in initialization
    compatibility = read("common/scripted_effects/00_targeted_operations_effects.txt")
    assert (resolution + compatibility).count(
        "modulo_variable = { TOP_archive_cursor = 128 }"
    ) == 2


def test_doctrine_vip_liaison_and_custody_depth_contracts():
    triggers = read("common/scripted_triggers/01_targeted_operations_triggers.txt")
    depth = read("common/scripted_effects/00_targeted_operations_effects.txt")

    assert "has_political_power > 99" in block(
        "common/scripted_triggers/01_targeted_operations_triggers.txt",
        "TOP_can_change_doctrine",
    )
    assert "add = 365" in block(
        "common/scripted_effects/00_targeted_operations_effects.txt",
        "TOP_change_doctrine",
    )
    assert "TOP_vip_capacity = 2" in triggers
    assert triggers.count("TOP_vip_capacity = 1") == 2
    assert "add = 91" in block(
        "common/scripted_effects/00_targeted_operations_effects.txt",
        "TOP_assign_vip_detail",
    )
    assert "TOP_liaison_multiplier = 0.75" in depth
    assert "TOP_liaison_multiplier = 0.5" in depth
    assert "TOP_liaison_pair_until" in depth
    assert "global.TOP_exploited^TOP_arg_target = 1" in depth
    custody = depth + read("common/scripted_effects/00_targeted_operations_effects.txt")
    for disposition in (
        "TOP_prosecute_selected",
        "TOP_transfer_selected",
        "TOP_exchange_selected",
        "TOP_release_selected",
    ):
        assert f"{disposition} = {{" in custody


def test_vip_deception_and_waiting_mandates_have_no_expiry_dead_zone():
    core = read("common/scripted_effects/00_targeted_operations_effects.txt")
    person_cases = read("common/scripted_effects/04_targeted_operations_cases.txt")
    organization_cases = read(
        "common/scripted_effects/04_targeted_operations_cases.txt"
    )
    triggers = read("common/scripted_triggers/01_targeted_operations_triggers.txt")
    person_case_triggers = read(
        "common/scripted_triggers/01_targeted_operations_triggers.txt"
    )

    weekly = _named_block(core, "TOP_global_weekly")
    assert "TOP_refresh_vip_details = yes" in weekly
    deception = _named_block(triggers, "TOP_can_fund_deception")
    assert "NOT = { has_idea = TOP_defensive_deception }" in deception
    assert "TOP_case_phase^top_timer_case < 3" in person_cases
    assert "TOP_org_case_phase^top_org_case < 3" in organization_cases
    assert (
        "TOP_case_phase^top_timer_case = 3 } check_variable = { "
        "TOP_case_until^top_timer_case < global.TOP_clock" not in person_cases
    )
    assert (
        "TOP_org_case_phase^top_org_case = 3 } check_variable = { "
        "TOP_org_case_until^top_org_case < global.TOP_clock" not in organization_cases
    )
    assert "TOP_case_until^TOP_arg_target" not in _named_block(
        person_case_triggers, "TOP_case_binding_valid"
    )
    assert "TOP_org_case_until^TOP_arg_group" not in _named_block(
        triggers, "TOP_organization_mission_binding_valid"
    )


def test_oversight_uses_a_typed_queue_without_overwriting_open_subjects():
    depth = read("common/scripted_effects/00_targeted_operations_effects.txt")
    person_open = _named_block(depth, "TOP_open_oversight")
    organization_open = _named_block(depth, "TOP_open_organization_oversight")
    dispatcher = _named_block(depth, "TOP_dispatch_next_oversight")
    resolver = _named_block(depth, "TOP_resolve_oversight")
    events = read("events/Targeted Operations.txt")

    assert "TOP_oversight_subject_id" not in person_open
    assert "TOP_oversight_subject_id" not in organization_open
    assert "add_to_array = { TOP_oversight_queue" in person_open
    assert "add = 1000" in organization_open
    assert "TOP_oversight_subject_id = 0" in dispatcher
    assert "TOP_oversight_queue^num > 0" in dispatcher
    assert "remove_from_array = { TOP_oversight_queue" in dispatcher
    assert "TOP_oversight_subject_kind = 1" in dispatcher
    assert "TOP_oversight_subject_kind = 2" in dispatcher
    assert "TOP_dispatch_next_oversight = yes" in resolver
    oversight_event = events[events.index("\tid = TOP_redesign.20") :]
    assert (
        "trigger = { check_variable = { TOP_oversight_subject_id > 0 } }"
        in oversight_event
    )


def test_strategic_crisis_consults_faction_partners_and_guarantors():
    runtime = block(
        "common/scripted_effects/04_targeted_operations_cases.txt",
        "TOP_start_exposed_kill_crisis",
    )
    crisis_event = read("events/Targeted Operations.txt")
    crisis_event = crisis_event[crisis_event.index("\tid = TOP_crisis.7") :]

    assert "every_country = {" in runtime
    assert "is_in_faction_with = var:global.TOP_crisis_actor" in runtime
    assert "is_in_faction_with = var:global.TOP_crisis_protection" in runtime
    assert "is_guaranteed_by = PREV" in runtime
    for choice in (
        "harsh_sanctions",
        "add_war_support",
        "TOP_defensive_deception",
        "TOP_adjust_crisis_tension",
    ):
        assert choice in crisis_event
    for option in ("a", "b", "c", "g", "e", "f"):
        assert f"name = TOP_crisis.7.{option}" in crisis_event


def test_capture_uses_distinct_custody_crisis_copy():
    events = read("events/Targeted Operations.txt")
    localization = read("localisation/english/MD_targeted_operations_l_english.yml")
    for event_id in ("TOP_crisis.10", "TOP_crisis.1", "TOP_crisis.2", "TOP_crisis.4"):
        event_start = events.index(f"\tid = {event_id}\n")
        event = events[event_start : event_start + 1400]
        assert "global.TOP_crisis_capture = 1" in event
        assert f"{event_id}.t_capture" in event
        assert f"{event_id}.d_capture" in event
        assert f" {event_id}.t_capture:" in localization
        assert f" {event_id}.d_capture:" in localization
    assert "custody and hostage crisis" in localization
    assert "negotiated return" in localization


def test_public_compatibility_interfaces_remain_available():
    effects = read("common/scripted_effects/00_targeted_operations_effects.txt")
    effects += read("common/scripted_effects/00_targeted_operations_effects.txt")

    for name in (
        "TOP_add_target_lead",
        "TOP_grant_target_mandate",
        "TOP_add_organization_lead",
        "TOP_grant_group_mandate",
        "TOP_kill_target",
        "TOP_capture_target",
        "TOP_release_selected",
        "TOP_transfer_selected",
        "TOP_offer_exchange",
    ):
        assert f"{name} = {{" in effects


def test_custody_bda_and_crisis_queues_preserve_immutable_records():
    depth = read("common/scripted_effects/00_targeted_operations_effects.txt")
    core = read("common/scripted_effects/00_targeted_operations_effects.txt")
    people = read("common/scripted_effects/04_targeted_operations_cases.txt")
    organizations = read("common/scripted_effects/04_targeted_operations_cases.txt")
    runtime = read("common/scripted_effects/04_targeted_operations_cases.txt")
    events = read("events/Targeted Operations.txt")

    custody_queue = _named_block(depth, "TOP_queue_custody_event")
    custody_dispatch = _named_block(depth, "TOP_dispatch_next_custody_event")
    assert "TOP_custody_event_queue = TOP_arg_target" in custody_queue
    assert "TOP_custody_event_queue^0" in custody_dispatch
    assert "TOP_finish_custody_event = yes" in events

    report_queue = _named_block(depth, "TOP_queue_field_report")
    report_dispatch = _named_block(depth, "TOP_dispatch_next_field_report")
    report_finish = _named_block(depth, "TOP_finish_field_report")
    for field in (
        "subject_kinds",
        "subject_ids",
        "results",
        "states",
        "hosts",
        "objectives",
        "impacts",
    ):
        assert f"TOP_report_{field}" in report_queue
        assert f"TOP_report_{field}^0" in report_dispatch
    assert "TOP_queue_field_report = yes" in _named_block(
        people, "TOP_resolve_person_operation"
    )
    assert "TOP_queue_field_report = yes" in _named_block(
        organizations, "TOP_resolve_organization_operation"
    )
    facility_damage = block(
        "common/scripted_effects/00_targeted_operations_effects.txt",
        "TOP_native_facility_damage",
    )
    assert facility_damage.count("set_temp_variable = { TOP_native_impact =") == 6
    assert "TOP_dispatch_next_field_report = yes" in report_finish
    report_event = events[
        events.index("id = TOP_redesign.10") : events.index("id = TOP_redesign.11")
    ]
    assert "TOP_finish_field_report = yes" in report_event
    assert "TOP_report_subject_kind = 1" in report_event
    assert "text = TOP_redesign.10.d" in report_event
    assert "text = TOP_redesign.10.d_organization_success" in report_event
    assert "text = TOP_redesign.10.d_organization_failure" in report_event

    bda_queue = _named_block(depth, "TOP_queue_bda_notice")
    bda_dispatch = _named_block(depth, "TOP_dispatch_next_bda_notice")
    for field in ("targets", "assessments", "sequences", "rows"):
        assert f"TOP_bda_notice_{field}" in bda_queue
        assert f"TOP_bda_notice_{field}^0" in bda_dispatch
    assert "TOP_arg_sequence = TOP_bda_token^top_bda_target" in core
    assert "TOP_archive_bda_token^TOP_archive_update_row" in core
    assert "TOP_finish_bda_notice = yes" in events

    crisis_start = _named_block(runtime, "TOP_start_exposed_kill_crisis")
    crisis_dispatch = _named_block(runtime, "TOP_dispatch_next_strategic_crisis")
    for field in (
        "actors",
        "protections",
        "hosts",
        "targets",
        "states",
        "results",
        "attributions",
        "consents",
        "visit_statuses",
        "visit_stories",
        "visit_tokens",
        "sequences",
    ):
        assert f"global.TOP_crisis_queue_{field}" in crisis_start
        if field == "sequences":
            assert (
                "global.TOP_crisis_queue_sequences = TOP_case_sequence^TOP_target"
                in crisis_start
            )
            assert (
                "array = global.TOP_crisis_queue_sequences index = 0" in crisis_dispatch
            )
        else:
            assert f"global.TOP_crisis_queue_{field}^0" in crisis_dispatch
    consequence_update = _named_block(
        read("common/scripted_effects/04_targeted_operations_cases.txt"),
        "TOP_apply_shared_consequences",
    )
    assert (
        "global.TOP_crisis_queue_sequences^top_crisis_queue_index = TOP_case_sequence^TOP_target"
        in consequence_update
    )
    assert "global.TOP_crisis_capture = 1" in crisis_start
    assert "TOP_result = 2" in crisis_start


def test_exchange_requires_an_authored_offer_and_transfer_uses_the_selected_country():
    depth = read("common/scripted_effects/00_targeted_operations_effects.txt")
    core = read("common/scripted_effects/00_targeted_operations_effects.txt")
    triggers = read("common/scripted_triggers/01_targeted_operations_triggers.txt")

    offer = _named_block(depth, "TOP_offer_exchange")
    exchange = _named_block(depth, "TOP_exchange_selected")
    transfer = _named_block(core, "TOP_transfer_selected")
    exchange_gate = _named_block(triggers, "TOP_can_exchange_selected")

    assert "global.TOP_custodian^TOP_arg_target = THIS" in offer
    assert "TOP_exchange_country^TOP_arg_target = TOP_arg_country" in offer
    assert "TOP_exchange_until^TOP_arg_target" in offer
    assert "TOP_can_exchange_selected = yes" in exchange
    assert "TOP_exchange_country^TOP_selected" in exchange_gate
    assert "TOP_exchange_until^TOP_selected > global.TOP_clock" in exchange_gate
    assert "TOP_transfer_host = TOP_transfer_country" in transfer
    assert "global.TOP_host^TOP_selected" not in transfer


def test_operations_center_exposes_required_filters_tabs_and_dimensions():
    gui = read("interface/targeted_operations.gui")
    scripted_gui = read("common/scripted_guis/01_targeted_operations_gui.txt")
    dispatch = read("common/scripted_localisation/01_targeted_operations_names.txt")

    assert "size = { width = 1040 height = 700 }" in gui
    title = gui[gui.index('name = "TOP_title"') :][:250]
    assert 'font = "hoi_24header"' in title
    assert "hoi_22mbs" not in gui
    for control in (
        "TOP_filter_active",
        "TOP_filter_cold",
        "TOP_filter_all",
        "TOP_filter_people",
        "TOP_filter_organizations",
        "TOP_dossier_tab",
        "TOP_package_tab",
        "TOP_authority_tab",
        "TOP_custody_tab",
        "TOP_archive_tab",
        "TOP_security_tab",
    ):
        assert control in gui
        assert control in scripted_gui
        control_block = gui[gui.index(f'name = "{control}"') :][:260]
        assert 'quadTextureSprite = "GFX_button_94x31"' in control_block
    assert 'text = "[TOP_organization_row_name]"' in gui
    redesign_loc = read("localisation/english/MD_targeted_operations_l_english.yml")
    assert (
        'TOP_select_organization_tt: "§Y[TOP_organization_row_class]§!' in redesign_loc
    )
    assert 'pdx_tooltip = "TOP_person_row_intel_tt"' in gui
    assert 'pdx_tooltip = "TOP_organization_row_intel_tt"' in gui
    assert " TOP_person_row_intel_tt:" in redesign_loc
    assert " TOP_organization_row_intel_tt:" in redesign_loc
    assert 'name = "TOP_begin_operation" position = { x = 840 y = 455 }' in gui
    assert 'name = "TOP_members_grid_scroll"' in gui
    assert 'name = "TOP_select_member"' in gui
    assert "TOP_members_grid = { array = TOP_visible_members" in scripted_gui
    assert "TOP_select_member_click" in scripted_gui
    assert (
        "TOP_facility_click_enabled = { TOP_can_cycle_selected_facility = yes }"
        in scripted_gui
    )
    view = read("common/scripted_effects/00_targeted_operations_effects.txt")
    assert "global.TOP_affiliation^top_view_member = TOP_selected_organization" in view
    assert "add_to_array = { TOP_visible_members = top_view_member }" in view
    assert "name = TOP_authorized_name" not in dispatch
    assert "name = TOP_row_name" not in dispatch
    security_close = block(
        "common/scripted_guis/01_targeted_operations_gui.txt",
        "TOP_security_close_button_click",
    )
    assert "TOP_security_open = 0" in security_close
    assert "TOP_tab = 0" in security_close


def test_async_person_case_lifecycle_rebuilds_the_selected_view():
    cases = read("common/scripted_effects/04_targeted_operations_cases.txt")
    view = block(
        "common/scripted_effects/00_targeted_operations_effects.txt",
        "TOP_build_view",
    )
    for effect in ("TOP_finish_case", "TOP_close_case"):
        assert "TOP_build_view = yes" in _named_block(cases, effect)
    assert "TOP_arg_target = TOP_selected" in view
    assert "TOP_load_case = yes" in view


def test_pressure_warnings_and_custody_disposition_are_reachable_for_ai():
    pressure = block(
        "common/scripted_effects/00_targeted_operations_effects.txt",
        "TOP_check_person_pressure_threshold",
    ) + block(
        "common/scripted_effects/00_targeted_operations_effects.txt",
        "TOP_check_group_pressure_threshold",
    )
    vip = block(
        "common/scripted_triggers/01_targeted_operations_triggers.txt",
        "TOP_can_assign_vip_detail",
    )
    custody = block(
        "common/scripted_effects/00_targeted_operations_effects.txt",
        "TOP_ai_manage_custody",
    )
    events = read("events/Targeted Operations.txt")
    dispatcher = block(
        "common/scripted_effects/00_targeted_operations_effects.txt",
        "TOP_dispatch_next_pressure_notice",
    )

    assert pressure.count("TOP_enqueue_pressure_notice = yes") == 2
    assert "country_event = { id = TOP_redesign.1 days = 1 }" in dispatcher
    assert "country_event = { id = TOP_redesign.2 days = 1 }" in dispatcher
    assert "is_ai = no" not in pressure
    assert "is_ai = no" not in vip
    assert "is_ai = yes" in custody
    assert "TOP_transfer_recorded_custody = yes" in custody
    assert events.count("TOP_ai_manage_custody = yes") == 3
    assert events.count("TOP_finish_pressure_notice = yes") == 7


def test_ai_liaison_reports_bootstrap_defensive_knowledge_without_offense():
    depth = read("common/scripted_effects/00_targeted_operations_effects.txt")
    triggers = read("common/scripted_triggers/01_targeted_operations_triggers.txt")
    source = block(
        "common/scripted_effects/00_targeted_operations_effects.txt",
        "TOP_prepare_ai_liaison_source",
    )

    assert "is_ai = yes" in source
    assert "TOP_identity_confidence^TOP_incoming_liaison_id = 100" in source
    assert "TOP_org_verification^TOP_incoming_liaison_id = 100" in source
    assert "TOP_location_confidence^TOP_incoming_liaison_id" not in source
    assert "TOP_pattern_confidence^TOP_incoming_liaison_id" not in source
    assert "TOP_org_location^TOP_incoming_liaison_id" not in source
    assert "TOP_org_activity^TOP_incoming_liaison_id" not in source
    assert "TOP_package_state" not in source
    assert "TOP_org_package_state" not in source
    assert "TOP_prepare_ai_liaison_source = yes" in depth
    assert "TOP_liaison_source_available = {" in triggers
    assert "TOP_liaison_deception_available = {" in triggers


def test_playtest_gui_and_runtime_fixes_stay_wired():
    view = block(
        "common/scripted_effects/00_targeted_operations_effects.txt", "TOP_build_view"
    )
    assert "limit = { check_variable = { TOP_tab = 4 } }" in view
    assert (
        "if = { limit = { check_variable = { TOP_tab = 0 } } add_to_array = { TOP_visible_members"
        in view
    )

    on_actions = read("common/on_actions/00_on_actions.txt")
    assert (
        "if = { limit = { check_variable = { TOP_open = 1 } } TOP_refresh_view = yes }"
        in on_actions
    )

    events = read("events/Targeted Operations.txt")
    unilateral = events[events.index("name = TOP_authorization.2.b") :]
    unilateral = unilateral[: unilateral.index("log =")]
    assert "NOT = { check_variable = { TOP_proposal_doctrine = 1 } }" in unilateral
    assert "var:TOP_proposal_host = { has_war_with = PREV }" in unilateral

    feedback = read("common/scripted_localisation/01_targeted_operations_status.txt")
    for key in (
        "TOP_designation_package_exists",
        "TOP_designation_organization_ready",
        "TOP_designation_organization_locked",
        "TOP_designation_needs_power",
    ):
        assert key in feedback
    assert "localization_key = TOP_authorized_method_none" in feedback

    legacy = read("common/scripted_effects/01_targeted_operations_legacy_effects.txt")
    assert "event_target:GLOBAL_bin_laden_hideout = {" not in legacy
    assert 'icon = "GFX_coups"' in read("common/game_rules/01_targeted_operations.txt")


EFFECTS = (ROOT / "common/scripted_effects/04_targeted_operations_cases.txt").read_text(
    encoding="utf-8"
)


TRIGGERS = (
    ROOT / "common/scripted_triggers/01_targeted_operations_triggers.txt"
).read_text(encoding="utf-8")


CORE_EFFECTS = (
    ROOT / "common/scripted_effects/00_targeted_operations_effects.txt"
).read_text(encoding="utf-8")


EVENTS = (ROOT / "events/Targeted Operations.txt").read_text(encoding="utf-8")


OPINION_MODIFIERS = (
    ROOT / "common/opinion_modifiers/01_targeted_operations.txt"
).read_text(encoding="utf-8")


LOCALISATION_PATH = ROOT / "localisation/english/MD_targeted_operations_l_english.yml"


LOCALISATION = LOCALISATION_PATH.read_text(encoding="utf-8-sig")


YEARLY = (ROOT / "common/scripted_effects/00_yearly_effects.txt").read_text(
    encoding="utf-8"
)


REGISTRY = (
    ROOT / "common/scripted_effects/01_targeted_operations_registry.txt"
).read_text(encoding="utf-8")


def test_every_post_start_window_is_dispatched_by_its_yearly_effect():
    years = set(re.findall(r"(?m)^TOP_open_windows_(\d{4}) = \{", REGISTRY))
    assert years
    for year in years - {"2000"}:
        yearly = _named_block(YEARLY, f"trigger_year_{year}_events")
        assert f"TOP_open_windows_{year} = yes" in yearly


def test_2026_yearly_hook_opens_maduro_before_reviewing_opportunities():
    yearly = _named_block(YEARLY, "trigger_year_2026_events")
    assert yearly.index("TOP_open_windows_2026 = yes") < yearly.index(
        "TOP_modern_opportunities_2026 = yes"
    )


def test_visit_constants_and_capacity_sized_storage_are_explicit():
    assert "global.TOP_visit_notice_days = 60" in EFFECTS
    assert "global.TOP_visit_active_days = 21" in EFFECTS
    assert "global.TOP_visit_execution_days = 7" in EFFECTS
    assert "global.TOP_visit_minimum_confidence = 40" in EFFECTS
    for field in (
        "status",
        "token",
        "planned_token",
        "active_token",
        "story",
        "state",
        "host",
        "return_state",
        "return_host",
        "start",
        "until",
        "execution_until",
    ):
        assert (
            f"resize_array = {{ global.TOP_visit_{field} = "
            "global.TOP_registry_capacity }"
        ) in EFFECTS


def test_headline_visit_schedule_and_fixed_story_bindings():
    invitations = {
        1: ("CHI", 1, 129, 547),
        2: ("SOV", 65, 144, 652),
        3: ("POL", 129, 132, 114),
        4: ("SAU", 193, 159, 176),
        5: ("ISR", 257, 158, 207),
    }
    for story, (host, day, target, state) in invitations.items():
        assert (
            f"{host} = {{ country_event = {{ id = TOP_visit.{story} days = {day} }} }}"
            in YEARLY
        )
        plan_call = "\n".join(
            (
                f"\t\tset_temp_variable = {{ TOP_arg_target = {target} }}",
                f"\t\tset_temp_variable = {{ TOP_arg_state = {state} }}",
                f"\t\tset_temp_variable = {{ TOP_arg_story = {story} }}",
                "\t\tTOP_plan_visit = yes",
            )
        )
        assert plan_call in EVENTS
        assert f"country_event = {{ id = TOP_visit.1{story} days = 60 }}" in EVENTS
        activate_call = plan_call.replace("TOP_plan_visit", "TOP_activate_visit")
        assert activate_call in EVENTS
        assert f"country_event = {{ id = TOP_visit.2{story} days = 21 }}" in EVENTS
        end_call = "\n".join(
            (
                f"\t\tset_temp_variable = {{ TOP_arg_target = {target} }}",
                f"\t\tset_temp_variable = {{ TOP_arg_story = {story} }}",
                "\t\tTOP_end_visit = yes",
            )
        )
        assert end_call in EVENTS


def test_visit_cases_snapshot_story_and_require_the_active_token_for_execution():
    for field in ("token", "status", "story"):
        assert f"TOP_case_visit_{field}^TOP_arg_target" in EFFECTS
    execution = _named_block(TRIGGERS, "TOP_case_visit_execution_valid")
    assert (
        "TOP_case_visit_token^TOP_case_visit_target = global.TOP_visit_active_token^TOP_case_visit_target"
        in execution
    )
    assert "global.TOP_visit_status^TOP_case_visit_target = 2" in execution
    assert (
        "var = global.TOP_clock value = global.TOP_visit_execution_until^TOP_case_visit_target compare = less_than_or_equals"
        in execution
    )
    assert "TOP_case_visit_execution_valid = yes" in TRIGGERS
    assert (
        "var = TOP_case_until^TOP_arg_target value = global.TOP_clock compare = greater_than_or_equals"
        not in _named_block(TRIGGERS, "TOP_case_binding_valid")
    )
    assert "TOP_case_until^TOP_arg_target > global.TOP_clock" in _named_block(
        TRIGGERS, "TOP_can_begin_person_operation"
    )
    stood_down = _named_block(TRIGGERS, "TOP_native_callback_matches_stood_down")
    for requirement in (
        "TOP_native_callback_matches_stood_down_tuple = yes",
        "TOP_case_until^TOP_target > global.TOP_clock",
        "TOP_authored_role_eligible = yes",
        "TOP_person_access_available = yes",
        "is_controlled_by = var:TOP_access_host",
        "TOP_case_visit_execution_valid = yes",
        "TOP_person_operational_eligible = yes",
    ):
        assert requirement in stood_down


def test_cancelled_visit_closes_preparation_but_underway_operation_fails_closed():
    processor = _named_block(EFFECTS, "TOP_process_cases")
    assert "TOP_case_phase^TOP_target < 3" in processor
    assert "global.TOP_visit_status^TOP_target = 0" in processor
    assert "NOT = { TOP_authored_role_eligible = yes }" in processor
    assert "TOP_case_phase^TOP_target = 3" in processor
    callback = _named_block(
        (
            ROOT / "common/scripted_effects/00_targeted_operations_effects.txt"
        ).read_text(),
        "TOP_native_result_args",
    )
    assert "TOP_mission_binding_valid = yes" in callback
    assert "TOP_close_case = yes" in callback
    execution = _named_block(TRIGGERS, "TOP_case_visit_execution_valid")
    assert "global.TOP_visit_active_token^TOP_case_visit_target" in execution
    assert "global.TOP_visit_status^TOP_case_visit_target = 2" in execution
    assert "TOP_case_visit_execution_valid = yes" in _named_block(
        TRIGGERS, "TOP_native_callback_matches_stood_down"
    )
    assert "TOP_case_visit_execution_valid = yes" in TRIGGERS


def test_visit_review_deadline_and_specific_tooltip_are_wired():
    approval = _named_block(TRIGGERS, "TOP_case_visit_approval_fits")
    assert "add_to_temp_variable = { TOP_visit_candidate_due = 28 }" in approval
    assert (
        "TOP_visit_candidate_due = global.TOP_visit_start^TOP_case_visit_target"
        in approval
    )
    assert (
        "TOP_visit_candidate_due < global.TOP_visit_execution_until^TOP_case_visit_target"
        in approval
    )
    authorization_events = (ROOT / "events/Targeted Operations.txt").read_text(
        encoding="utf-8"
    )
    assert authorization_events.count("tooltip = TOP_visit_window_too_short_tt") == 2


def test_exposure_roll_is_single_and_sovereignty_penalty_is_applied_once():
    resolution = (
        ROOT / "common/scripted_effects/04_targeted_operations_cases.txt"
    ).read_text(encoding="utf-8")
    roll = _named_block(resolution, "TOP_calculate_person_consequences")
    assert roll.count("randomize_temp_variable = { var = TOP_exposure_roll") == 1
    penalty = (
        "add_opinion_modifier = { target = PREV modifier = TOP_sovereignty_violation }"
    )
    for name in (
        "TOP_apply_shared_consequences",
        "TOP_apply_organization_consequences",
    ):
        assert _named_block(resolution, name).count(penalty) == 1


def test_crisis_constants_deltas_bands_and_single_war_path():
    assert "global.TOP_crisis_opening_tension = 40" in EFFECTS
    assert "global.TOP_crisis_repeat_tension = 15" in EFFECTS
    assert "global.TOP_crisis_sanctions_threshold = 36" in EFFECTS
    assert "global.TOP_crisis_ultimatum_threshold = 70" in EFFECTS
    for delta in (-20, -15, -10, 5, 10, 20):
        assert (
            f"set_temp_variable = {{ TOP_arg_amount = {delta} }}\n"
            "\t\tTOP_adjust_crisis_tension = yes"
        ) in EVENTS
    assert EVENTS.count("declare_war_on = {") == 1
    assert (
        "declare_war_on = { target = var:global.TOP_crisis_actor "
        "type = topple_government }"
    ) in EVENTS
    assert EVENTS.count("major = yes") == 1
    initializer = _named_block(EFFECTS, "TOP_start_exposed_kill_crisis")
    assert initializer.count("every_country = {") == 1
    assert EFFECTS.count("every_country = {") == 2
    assert "every_country" not in EVENTS
    assert "every_other_country" not in EFFECTS
    assert "every_other_country" not in EVENTS


def test_repeat_incident_and_timeout_dispatch_the_ultimatum_band():
    initializer = _named_block(EFFECTS, "TOP_start_exposed_kill_crisis")
    assert "global.TOP_crisis_stage = 1" in initializer
    assert (
        initializer.count("global.TOP_crisis_story = TOP_authorized_visit_story") == 1
    )
    assert (
        initializer.count("global.TOP_crisis_visit_token = TOP_authorized_visit_token")
        == 1
    )
    assert "global.TOP_crisis_stage = 2" in EVENTS
    assert "global.TOP_crisis_stage = 3" in EVENTS
    assert "global.TOP_crisis_stage = 2" in initializer
    assert "TOP_crisis_tension_ultimatum = yes" in initializer
    assert "country_event = { id = TOP_crisis.3 days = 1 }" in initializer

    repeat_news = initializer.index("news_event = { id = TOP_crisis.11 days = 1 }")
    repeat_branch_start = initializer.rfind("\t\telse_if = {", 0, repeat_news)
    queued_branch_start = initializer.index(
        "add_to_array = { global.TOP_crisis_queue_actors = global.TOP_crisis_candidate_actor }"
    )
    queued_branch_start = initializer.rfind("\t\telse_if = {", 0, queued_branch_start)
    repeat_branch = initializer[repeat_branch_start:queued_branch_start]
    queued_branch = initializer[queued_branch_start:]
    assert (
        "global.TOP_crisis_candidate_actor = global.TOP_crisis_actor" in repeat_branch
    )
    assert (
        "global.TOP_crisis_candidate_protection = global.TOP_crisis_protection"
        in repeat_branch
    )
    assert "global.TOP_crisis_capture = 1" in repeat_branch
    assert "TOP_result = 2" in repeat_branch
    assert "global.TOP_crisis_target = TOP_target" in repeat_branch
    assert "global.TOP_crisis_repeat_tension" in repeat_branch
    for field in (
        "actors",
        "protections",
        "hosts",
        "targets",
        "states",
        "results",
        "attributions",
        "consents",
        "visit_statuses",
        "visit_stories",
        "visit_tokens",
        "sequences",
    ):
        assert f"global.TOP_crisis_queue_{field}" in queued_branch

    dispatcher = _named_block(EFFECTS, "TOP_dispatch_next_strategic_crisis")
    assert "global.TOP_crisis_queue_targets^num > 0" in dispatcher
    assert "TOP_start_exposed_kill_crisis = yes" in dispatcher
    for field in (
        "actors",
        "protections",
        "hosts",
        "targets",
        "states",
        "results",
        "attributions",
        "consents",
        "visit_statuses",
        "visit_stories",
        "visit_tokens",
        "sequences",
    ):
        assert (
            f"remove_from_array = {{ array = global.TOP_crisis_queue_{field} index = 0 }}"
            in dispatcher
        )

    timeout = _named_block(EFFECTS, "TOP_process_crisis")
    principals = _named_block(TRIGGERS, "TOP_crisis_principals_valid")
    assert "global.TOP_crisis_actor > 0" in principals
    assert "global.TOP_crisis_protection > 0" in principals
    assert "var:global.TOP_crisis_actor = { exists = yes }" in principals
    assert "var:global.TOP_crisis_protection = { exists = yes }" in principals
    assert "NOT = { TOP_crisis_principals_valid = yes }" in timeout
    assert "global.TOP_crisis_story < 1" in timeout
    assert "global.TOP_crisis_story > 6" in timeout
    assert "global.TOP_crisis_visit_token < 1" in timeout
    assert "TOP_crisis_tension_ultimatum = yes" in timeout
    assert "add_to_variable = { global.TOP_crisis_until = 30 }" in timeout
    assert "country_event = { id = TOP_crisis.3 days = 1 }" in timeout
    assert timeout.index("TOP_crisis_tension_ultimatum = yes") < timeout.rindex(
        "TOP_cleanup_crisis = yes"
    )

    cleanup = _named_block(EFFECTS, "TOP_cleanup_crisis")
    assert "global.TOP_crisis_story = 0" in cleanup
    assert "global.TOP_crisis_visit_token = 0" in cleanup
    assert "global.TOP_crisis_stage = 0" in cleanup
    assert "TOP_dispatch_next_strategic_crisis = yes" in cleanup


def test_unmatched_exposed_killing_uses_independent_news_snapshots():
    event_id = EVENTS.index("\tid = TOP_crisis.12")
    event_start = EVENTS.rfind("news_event = {", 0, event_id)
    event_end = EVENTS.index("\ncountry_event = {", event_id)
    event = EVENTS[event_start:event_end]
    assert "picture = GFX_news_gulf_terror" in event
    assert "is_triggered_only = yes" in event
    assert "major = yes" not in event
    option = event[event.index("\toption = {") :]
    assert option.index('log = "[GetDateText]') < option.index(
        "set_variable = { TOP_unmatched_incident_actor = 0 }"
    )
    for variable in (
        "TOP_unmatched_incident_actor",
        "TOP_unmatched_incident_protection",
        "TOP_unmatched_incident_host",
    ):
        assert f"set_variable = {{ {variable} = 0 }}" in option
        assert f"[?{variable}.GetNameDef]" in LOCALISATION
    independent_desc = next(
        line
        for line in LOCALISATION.splitlines()
        if line.startswith(" TOP_crisis.12.d:")
    )
    assert "global.TOP_crisis_" not in independent_desc


def test_crisis_preserves_hosts_and_dispatches_deduplicated_support_consultations():
    initializer = _named_block(EFFECTS, "TOP_start_exposed_kill_crisis")
    assert (
        "OVERLORD = { set_variable = { global.TOP_crisis_candidate_actor = THIS } }"
        in initializer
    )
    assert (
        "global.TOP_crisis_candidate_protection = TOP_operation_protection_country"
        in initializer
    )
    assert "global.TOP_crisis_candidate_host = TOP_authorized_host" in initializer
    assert "global.TOP_crisis_candidate_protection = THIS" not in initializer
    assert "global.TOP_crisis_candidate_host = THIS" not in initializer
    assert initializer.count("country_event = { id = TOP_crisis.7 days = 1 }") == 1
    assert "every_country = {" in initializer
    assert "is_in_faction_with = var:global.TOP_crisis_actor" in initializer
    assert "is_in_faction_with = var:global.TOP_crisis_protection" in initializer
    assert "is_guaranteed_by = PREV" in initializer
    assert "TOP_crisis_support_token = global.TOP_crisis_token" in initializer
    faction_event = _named_block(TRIGGERS, "TOP_crisis_faction_event_valid")
    assert "global.TOP_crisis_actor_faction_leader = THIS" in faction_event
    assert "global.TOP_crisis_protection_faction_leader = THIS" in faction_event
    assert "TOP_crisis_support_token = global.TOP_crisis_token" in faction_event
    faction_event_start = EVENTS.index("\tid = TOP_crisis.7")
    faction_event = EVENTS[faction_event_start : faction_event_start + 4000]
    assert "minor_flavor = yes" in faction_event
    for option in ("a", "b", "c", "g", "e", "f"):
        assert f"name = TOP_crisis.7.{option}" in faction_event
    for option in ("a", "b", "c", "g", "e", "f"):
        assert (
            f'log = "[GetDateText]: [Root.GetName]: TOP_crisis.7.{option} executed"'
            in faction_event
        )


def test_crisis_cleanup_waits_for_bound_participant_notices():
    initializer = _named_block(EFFECTS, "TOP_start_exposed_kill_crisis")
    cleanup = _named_block(EFFECTS, "TOP_cleanup_crisis")
    recount = _named_block(EFFECTS, "TOP_recount_crisis_participant_notices")
    finish = _named_block(EFFECTS, "TOP_finish_crisis_participant_notice")
    processor = _named_block(EFFECTS, "TOP_process_crisis")
    host_gate = _named_block(TRIGGERS, "TOP_crisis_host_event_valid")
    faction_gate = _named_block(TRIGGERS, "TOP_crisis_faction_event_valid")

    assert "global.TOP_crisis_participant_pending = 0" in initializer
    assert (
        initializer.count("TOP_crisis_participant_token = global.TOP_crisis_token") == 2
    )
    assert (
        len(
            re.findall(
                r"(?<!global\.)TOP_crisis_participant_pending = 1",
                initializer,
            )
        )
        == 2
    )
    assert (
        initializer.count(
            "add_to_variable = { global.TOP_crisis_participant_pending = 1 }"
        )
        == 2
    )

    assert "TOP_recount_crisis_participant_notices = yes" in cleanup
    assert cleanup.index(
        "TOP_recount_crisis_participant_notices = yes"
    ) < cleanup.index("global.TOP_crisis_participant_pending > 0")
    assert "global.TOP_crisis_participant_pending = 0" in recount
    assert "every_country = {" in recount
    assert "exists = yes" in recount
    assert "TOP_crisis_participant_pending = 1" in recount
    assert "TOP_crisis_participant_token = global.TOP_crisis_token" in recount
    assert "add_to_variable = { global.TOP_crisis_participant_pending = 1 }" in recount
    assert "global.TOP_crisis_participant_pending > 0" in cleanup
    assert "global.TOP_crisis_cleanup_requested = 1" in cleanup
    assert cleanup.index("global.TOP_crisis_participant_pending > 0") < cleanup.index(
        "TOP_crisis_cleanup_token = global.TOP_crisis_token"
    )
    assert cleanup.index("global.TOP_crisis_cleanup_requested = 0") < cleanup.index(
        "TOP_dispatch_next_strategic_crisis = yes"
    )

    assert "TOP_crisis_participant_token = global.TOP_crisis_token" in finish
    assert "global.TOP_crisis_participant_pending = 0" in finish
    assert "global.TOP_crisis_cleanup_requested = 1" in finish
    for field in (
        "TOP_crisis_participant_pending",
        "TOP_crisis_participant_token",
        "TOP_crisis_token",
        "TOP_crisis_counterpart",
        "TOP_crisis_target",
        "TOP_crisis_support_token",
        "TOP_crisis_support_side",
    ):
        assert f"{field} = 0" in finish

    for gate in (host_gate, faction_gate):
        assert "TOP_crisis_participant_pending = 1" in gate
        assert "TOP_crisis_participant_token = global.TOP_crisis_token" in gate
    assert EVENTS.count("TOP_finish_crisis_participant_notice = yes") == 8
    assert processor.count("global.TOP_crisis_cleanup_requested = 0") == 3
    assert "global.TOP_crisis_cleanup_requested = 1" in processor
    assert "TOP_recount_crisis_participant_notices = yes" in processor
    assert "global.TOP_crisis_participant_pending = 0" in processor
    assert processor.index(
        "TOP_recount_crisis_participant_notices = yes"
    ) < processor.index("global.TOP_crisis_cleanup_requested = 0")

    repeat_news = initializer.index("news_event = { id = TOP_crisis.11 days = 1 }")
    repeat_branch_start = initializer.rfind("\t\telse_if = {", 0, repeat_news)
    queue_write = initializer.index(
        "add_to_array = { global.TOP_crisis_queue_actors = global.TOP_crisis_candidate_actor }"
    )
    queued_branch_start = initializer.rfind("\t\telse_if = {", 0, queue_write)
    repeat_branch = initializer[repeat_branch_start:queued_branch_start]
    queued_branch = initializer[queued_branch_start:]
    assert "global.TOP_crisis_cleanup_requested = 0" in repeat_branch
    assert "global.TOP_crisis_cleanup_requested = 0" not in queued_branch


def test_crisis_gate_requires_exact_live_headline_visit_and_lethal_result():
    gate = _named_block(TRIGGERS, "TOP_exposed_visit_kill_valid")
    for requirement in (
        "TOP_exposure_recorded = 1",
        "TOP_result = 3",
        "global.TOP_status^TOP_target = 3",
        "TOP_authorized_visit_story > 0",
        "TOP_authorized_visit_story < 7",
        "TOP_authorized_visit_token = global.TOP_visit_active_token^TOP_target",
        "global.TOP_visit_status^TOP_target = 2",
        "TOP_authorized_host = global.TOP_visit_host^TOP_target",
        "TOP_operation_state = global.TOP_visit_state^TOP_target",
    ):
        assert requirement in gate


def test_engine_safe_wrappers_cover_every_appended_target_and_novichok():
    assert "$TARGET$" not in TRIGGERS
    assert "$STORY$" not in TRIGGERS
    for target in range(129, 161):
        assert f"TOP_authored_role_eligible_{target} = {{" in TRIGGERS
    assert "TOP_method_startable_7 = {" in TRIGGERS
    assert "set_temp_variable = { TOP_requested_method = 7 }" in TRIGGERS


def test_visit_retention_and_dossier_refresh_share_full_live_revalidation():
    planned = _named_block(TRIGGERS, "TOP_visit_planned_runtime_valid")
    active = _named_block(TRIGGERS, "TOP_visit_active_runtime_valid")
    for gate in (planned, active):
        assert "global.TOP_status^TOP_visit_trigger_target = 1" in gate
        assert "TOP_authored_role_eligible = yes" in gate
        assert "global.TOP_visit_host^TOP_visit_trigger_target = THIS" in gate
        assert "var:TOP_visit_trigger_state = { is_controlled_by = PREV }" in gate
        assert "TOP_visit_story_valid = yes" in gate
    invite = _named_block(TRIGGERS, "TOP_visit_can_invite")
    arrival = _named_block(TRIGGERS, "TOP_visit_can_arrive")
    assert "TOP_visit_pressure_allows_travel = yes" in invite
    assert "TOP_visit_pressure_allows_travel = yes" in arrival
    assert "TOP_visit_pressure_allows_travel = yes" in planned
    assert "TOP_visit_pressure_allows_travel = yes" not in active
    pressure_gate = _named_block(TRIGGERS, "TOP_visit_pressure_allows_travel")
    assert "global.TOP_pressure^TOP_visit_trigger_target" in pressure_gate
    assert (
        "global.TOP_group_pressure^TOP_visit_pressure_group multiply = 0.5"
        in pressure_gate
    )
    assert "TOP_visit_effective_pressure < 75" in pressure_gate
    assert (
        "global.TOP_visit_planned_token^TOP_visit_trigger_target = "
        "global.TOP_visit_token^TOP_visit_trigger_target"
    ) in planned
    assert (
        "global.TOP_visit_active_token^TOP_visit_trigger_target = "
        "global.TOP_visit_token^TOP_visit_trigger_target"
    ) in active
    assert "global.TOP_host^TOP_visit_trigger_target = THIS" in active
    assert (
        "global.TOP_state^TOP_visit_trigger_target = TOP_visit_trigger_state" in active
    )

    processor = _named_block(EFFECTS, "TOP_process_visits")
    refresher = _named_block(EFFECTS, "TOP_refresh_visit_dossiers")
    for effect in (
        "TOP_revalidate_planned_visit",
        "TOP_revalidate_active_visit",
    ):
        for source_block in (processor, refresher):
            assert (
                "set_temp_variable = { TOP_arg_target = top_visit_target }"
                in source_block
            )
            assert f"{effect} = yes" in source_block
    assert "global.TOP_visit_minimum_confidence" in refresher


def test_invalid_visit_cleanup_requires_current_token_and_preserves_newer_locations():
    processor = _named_block(EFFECTS, "TOP_process_visits")
    assert (
        "global.TOP_visit_planned_token^top_visit_target = "
        "global.TOP_visit_token^top_visit_target"
    ) in processor
    assert (
        "global.TOP_visit_active_token^top_visit_target = "
        "global.TOP_visit_token^top_visit_target"
    ) in processor
    assert "var:TOP_visit_cleanup_host = { exists = yes }" in processor
    assert (
        "else = {\n"
        "\t\t\t\tset_temp_variable = { TOP_arg_target = top_visit_target }\n"
        "\t\t\t\tTOP_clear_visit = yes\n"
        "\t\t\t}"
    ) in processor

    end_visit = _named_block(EFFECTS, "TOP_end_visit")
    assert (
        "global.TOP_host^top_visit_target = global.TOP_visit_host^top_visit_target"
        in end_visit
    )
    assert (
        "global.TOP_state^top_visit_target = global.TOP_visit_state^top_visit_target"
        in end_visit
    )


def test_negotiated_closure_is_temporary_and_response_priced():
    modifier = _named_block(OPINION_MODIFIERS, "TOP_crisis_settlement")
    assert "value = 15" in modifier
    assert "months = 6" in modifier
    assert 'TOP_crisis_settlement: "Negotiated Crisis Settlement"' in LOCALISATION
    assert LOCALISATION_PATH.read_bytes().startswith(b"\xef\xbb\xbf")

    settlement = _named_block(EFFECTS, "TOP_settle_crisis")
    assert "established_diplomatic_relations" not in settlement
    assert settlement.count("modifier = TOP_crisis_settlement") == 2
    costs = (
        (1, "global.TOP_crisis_settlement_apology_pp", -25),
        (2, "global.TOP_crisis_settlement_denial_pp", -50),
        (3, "global.TOP_crisis_settlement_defiance_pp", -75),
    )
    for response, variable, amount in costs:
        assert f"set_variable = {{ {variable} = {amount} }}" in EFFECTS
        assert f"add_political_power = {variable}" in settlement
        if response < 3:
            assert f"global.TOP_crisis_actor_response = {response}" in settlement

    actor_response = EVENTS[
        EVENTS.index("\tid = TOP_crisis.2") : EVENTS.index("\tid = TOP_crisis.3")
    ]
    for response in (1, 2, 3):
        assert f"global.TOP_crisis_actor_response = {response}" in actor_response
    ultimatum = EVENTS[
        EVENTS.index("\tid = TOP_crisis.5") : EVENTS.index("\tid = TOP_crisis.6")
    ]
    assert "TOP_settle_crisis = yes" in ultimatum
    assert "established_diplomatic_relations" not in ultimatum


def test_ultimatum_ai_uses_latched_coalition_balance_snapshot():
    snapshot = _named_block(EFFECTS, "TOP_snapshot_crisis_coalition_balance")
    assert (
        "global.TOP_crisis_actor_coalition_anchor = "
        "global.TOP_crisis_actor_faction_leader"
    ) in snapshot
    assert (
        "global.TOP_crisis_victim_coalition_anchor = "
        "global.TOP_crisis_protection_faction_leader"
    ) in snapshot
    assert snapshot.count("tag = PREV") == 2
    assert "ratio > 1.25" in snapshot
    assert "ratio < 0.80" in snapshot
    assert "global.TOP_crisis_coalition_balance = 1" in snapshot
    assert "global.TOP_crisis_coalition_balance = -1" in snapshot

    initializer = _named_block(EFFECTS, "TOP_start_exposed_kill_crisis")
    assert "TOP_snapshot_crisis_coalition_balance = yes" in initializer
    assert initializer.index("TOP_snapshot_crisis_coalition_balance = yes") > (
        initializer.index("global.TOP_crisis_protection_faction_leader = THIS")
    )
    cleanup = _named_block(EFFECTS, "TOP_cleanup_crisis")
    for variable in (
        "global.TOP_crisis_actor_coalition_anchor",
        "global.TOP_crisis_victim_coalition_anchor",
        "global.TOP_crisis_coalition_balance",
    ):
        assert f"set_variable = {{ {variable} = 0 }}" in cleanup

    ultimatum = EVENTS[
        EVENTS.index("\tid = TOP_crisis.5") : EVENTS.index("\tid = TOP_crisis.6")
    ]
    assert ultimatum.count("global.TOP_crisis_coalition_balance = 1") == 2
    assert ultimatum.count("global.TOP_crisis_coalition_balance = -1") == 2


def test_open_story_is_held_to_serving_office_holders():
    """Targets 56-64 are the hunted Ba'athists and Soleimani.

    They carry political = 1 and so clear the invite gate, but a state visit to
    a fugitive is nonsense, and TOP_open_visit_name has no branch for them.
    """
    story = _named_block(TRIGGERS, "TOP_visit_story_valid")
    assert "TOP_visit_trigger_story = 6" in story
    assert "TOP_visit_trigger_target > 128" in story
    # The resolver is generated across the whole registry, so the fugitives are
    # nameable; it is this trigger that keeps them from being invited.
    names = (
        ROOT / "common/scripted_localisation/01_targeted_operations_names.txt"
    ).read_text(encoding="utf-8")
    assert "name = TOP_open_visit_name" in names


def test_open_story_is_reusable_where_the_authored_stories_are_spent():
    gate = _named_block(TRIGGERS, "TOP_visit_can_invite")
    assert "TOP_visit_trigger_story < 7" in gate
    # The spend check must not apply to story 6, or it fires once like the rest.
    assert "TOP_visit_trigger_story = 6" in gate
    assert "global.TOP_visit_story_used^TOP_visit_trigger_story = 0" in gate
    setup = _named_block(EFFECTS, "TOP_setup_extended_runtime")
    assert "resize_array = { global.TOP_visit_story_used = 7 }" in setup
    assert "global.TOP_visit_open_interval = 91" in setup
    assert "TOP_extended_runtime_version" not in setup


def test_open_story_dispatcher_throttles_globally_and_frees_a_stalled_host():
    dispatch = _named_block(EFFECTS, "TOP_visit_country_opportunities")
    assert "TOP_country_eligible = yes" in dispatch
    # Global clock, not a per-country timer, so the rate does not scale with
    # how many hosts happen to be eligible.
    assert "global.TOP_visit_open_after < global.TOP_clock" in dispatch
    assert (
        "set_variable = { global.TOP_visit_open_after = "
        "{ value = global.TOP_clock add = global.TOP_visit_open_interval } }"
        in dispatch
    )
    # A chain that stalls must not wedge the host out of every later invitation.
    assert "TOP_open_visit_target = 0" in dispatch
    assert "global.TOP_visit_status^TOP_open_visit_target = 0" in dispatch
    assert "TOP_visit_can_invite = yes" in dispatch
    assert "end = global.TOP_registry_capacity" in dispatch
    assert "country_event = { id = TOP_visit.6 days = 1 }" in dispatch
    assert "TOP_visit_country_opportunities = yes" in _named_block(
        CORE_EFFECTS, "TOP_country_tick"
    )


def test_open_story_chain_carries_its_pick_in_country_variables():
    """Temporaries do not survive the 60 day notice or the 21 day stay."""
    for event_id, follow_up, days in (("6", "16", 60), ("16", "26", 21)):
        block = EVENTS[EVENTS.index(f"id = TOP_visit.{event_id}\n") :]
        block = block[: block.index("\ncountry_event = {")]
        assert "TOP_arg_target = TOP_open_visit_target" in block
        assert (
            f"country_event = {{ id = TOP_visit.{follow_up} days = {days} }}" in block
        )
    closing = EVENTS[EVENTS.index("id = TOP_visit.26\n") :]
    assert "TOP_end_visit = yes" in closing
    assert "clear_variable = TOP_open_visit_target" in closing


def test_top_raid_and_political_category_use_dynamic_rule_gates():
    category = read("common/decisions/categories/targeted_operations_political.txt")
    assert "allowed = { TOP_enabled = yes }" not in category
    assert "allowed = { always = yes }" in category
    assert "visible = { TOP_enabled = yes }" in category


def test_ct_registration_reads_the_unscoped_host_region():
    # Temp variables are unscoped, so the caller reads region_idx directly, as 00_ct_effects.txt does.
    effect = block(
        "common/scripted_effects/00_targeted_operations_effects.txt",
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


def test_core_collection_cannot_invent_a_false_location():
    for name in ("TOP_collect_person_pulse", "TOP_collect_organization_pulse"):
        effect = block(
            "common/scripted_effects/00_targeted_operations_effects.txt", name
        )
        assert "random" not in effect
        assert "lead_state" not in effect
    for name in ("TOP_tracking_completed", "TOP_facility_tracking_completed"):
        effect = _named_block(read_top_source(ROOT, "common/scripted_effects"), name)
        assert "TOP_enabled = yes" in effect
        assert "TOP_tracking_host" in effect


def test_extended_runtime_initializes_once_without_save_version_migrations():
    redesign = block(
        "common/scripted_effects/00_targeted_operations_effects.txt",
        "TOP_initialize_redesign_global",
    )
    runtime = read("common/scripted_effects/04_targeted_operations_cases.txt")
    setup = block(
        "common/scripted_effects/04_targeted_operations_cases.txt",
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
        "common/scripted_triggers/01_targeted_operations_triggers.txt",
        "TOP_can_review_organization",
    )
    blocker = read("common/scripted_localisation/01_targeted_operations_status.txt")
    localization = read("localisation/english/MD_targeted_operations_l_english.yml")

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
        "common/scripted_localisation/01_targeted_operations_status.txt"
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
        "common/scripted_triggers/01_targeted_operations_triggers.txt",
        "TOP_can_request_liaison",
    )
    relationship = block(
        "common/scripted_triggers/01_targeted_operations_triggers.txt",
        "TOP_liaison_relationship_available",
    )
    request = block(
        "common/scripted_effects/00_targeted_operations_effects.txt",
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
        "common/scripted_triggers/01_targeted_operations_triggers.txt",
        "TOP_can_request_selected_liaison",
    )
    selected_effect = block(
        "common/scripted_effects/00_targeted_operations_effects.txt",
        "TOP_request_selected_liaison",
    )
    cycle = block(
        "common/scripted_effects/00_targeted_operations_effects.txt",
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
        "common/scripted_effects/04_targeted_operations_cases.txt",
        "TOP_apply_shared_consequences",
    )
    access = block(
        "common/scripted_triggers/01_targeted_operations_triggers.txt",
        "TOP_person_access_available",
    )
    vip = block(
        "common/scripted_triggers/01_targeted_operations_triggers.txt",
        "TOP_can_assign_vip_detail",
    )
    person = block(
        "common/scripted_effects/04_targeted_operations_cases.txt",
        "TOP_calculate_person_consequences",
    )
    organization = block(
        "common/scripted_effects/04_targeted_operations_cases.txt",
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


def test_every_effectful_event_option_has_exactly_one_log():
    events = read("events/Targeted Operations.txt")
    options = [
        _parse_race_script(_extract_block(events, match.start()))["option"]
        for match in re.finditer(r"(?m)^\toption = \{", events)
    ]
    assert options
    for option in options:
        effects = [
            key
            for key, _, _ in option
            if key not in {"name", "ai_chance", "trigger", "log"}
        ]
        if effects:
            assert sum(key == "log" for key, _, _ in option) == 1, option
