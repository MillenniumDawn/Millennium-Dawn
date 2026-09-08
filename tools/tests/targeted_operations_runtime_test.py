from pathlib import Path

from great_ai_race_state_model_test import _named_block

ROOT = Path(__file__).resolve().parents[2]
EFFECTS = (
    ROOT / "common/scripted_effects/05_targeted_operations_runtime.txt"
).read_text(encoding="utf-8")
TRIGGERS = (
    ROOT / "common/scripted_triggers/05_targeted_operations_runtime.txt"
).read_text(encoding="utf-8")
CASES = (ROOT / "common/scripted_effects/04_targeted_operations_cases.txt").read_text(
    encoding="utf-8"
)
CASE_TRIGGERS = (
    ROOT / "common/scripted_triggers/04_targeted_operations_cases.txt"
).read_text(encoding="utf-8")
CORE_EFFECTS = (
    ROOT / "common/scripted_effects/00_targeted_operations_effects.txt"
).read_text(encoding="utf-8")
EVENTS = (ROOT / "events/Targeted Operations Runtime.txt").read_text(encoding="utf-8")
OPINION_MODIFIERS = (
    ROOT / "common/opinion_modifiers/01_targeted_operations.txt"
).read_text(encoding="utf-8")
LOCALISATION_PATH = ROOT / "localisation/english/MD_targeted_operations_l_english.yml"
LOCALISATION = LOCALISATION_PATH.read_text(encoding="utf-8-sig")
YEARLY = (ROOT / "common/scripted_effects/00_yearly_effects.txt").read_text(
    encoding="utf-8"
)
WRAPPERS = (
    ROOT / "common/scripted_triggers/05_targeted_operations_arg_wrappers.txt"
).read_text(encoding="utf-8")


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
        assert f"TOP_case_visit_{field}^TOP_selected" in CASES
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
    assert "TOP_case_visit_execution_valid = yes" in CASE_TRIGGERS
    assert (
        "var = TOP_case_until^TOP_arg_target value = global.TOP_clock compare = greater_than_or_equals"
        in CASE_TRIGGERS
    )


def test_cancelled_visit_closes_preparation_but_underway_operation_fails_closed():
    processor = _named_block(CASES, "TOP_process_cases")
    assert "TOP_case_phase^TOP_target < 3" in processor
    assert "global.TOP_visit_status^TOP_target = 0" in processor
    assert "NOT = { TOP_authored_role_eligible = yes }" in processor
    assert "TOP_case_phase^TOP_target = 3" in processor
    assert "TOP_mission_binding_valid = yes" in processor
    waiting = _named_block(TRIGGERS, "TOP_case_visit_waiting_for_arrival")
    assert "global.TOP_visit_status^TOP_case_visit_target = 1" in waiting
    assert "global.TOP_visit_planned_token^TOP_case_visit_target" in waiting
    assert "NOT = { TOP_case_visit_waiting_for_arrival = yes }" in processor


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


def test_exposure_roll_is_single_and_host_home_penalties_are_deduplicated():
    exposure = _named_block(CORE_EFFECTS, "TOP_apply_exposure")
    assert exposure.count("chance = TOP_exposure_chance") == 1
    assert exposure.count("set_temp_variable = { TOP_exposure_recorded = 1 }") == 1
    assert "TOP_operation_protection_country = TOP_authorized_host" in exposure
    assert "TOP_operation_protection_country = THIS" in exposure
    assert exposure.count("modifier = TOP_sovereignty_violation") == 2
    assert "TOP_start_exposed_kill_crisis = yes" in exposure


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
    assert "every_country" not in EFFECTS
    assert "every_country" not in EVENTS
    assert "every_other_country" not in EFFECTS
    assert "every_other_country" not in EVENTS


def test_repeat_incident_and_timeout_dispatch_the_ultimatum_band():
    initializer = _named_block(EFFECTS, "TOP_start_exposed_kill_crisis")
    assert "global.TOP_crisis_stage = 1" in initializer
    assert "global.TOP_crisis_stage = 2" in EVENTS
    assert "global.TOP_crisis_stage = 3" in EVENTS
    assert "global.TOP_crisis_stage = 2" in initializer
    assert "TOP_crisis_tension_ultimatum = yes" in initializer
    assert "country_event = { id = TOP_crisis.3 days = 1 }" in initializer

    timeout = _named_block(EFFECTS, "TOP_process_crisis")
    assert "TOP_crisis_tension_ultimatum = yes" in timeout
    assert "add_to_variable = { global.TOP_crisis_until = 30 }" in timeout
    assert "country_event = { id = TOP_crisis.3 days = 1 }" in timeout
    assert timeout.index("TOP_crisis_tension_ultimatum = yes") < timeout.index(
        "TOP_cleanup_crisis = yes"
    )

    cleanup = _named_block(EFFECTS, "TOP_cleanup_crisis")
    assert "global.TOP_crisis_stage = 0" in cleanup


def test_crisis_preserves_physical_home_and_host_and_deduplicates_faction_consultations():
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
    assert initializer.count("country_event = { id = TOP_crisis.7 days = 1 }") == 2
    assert (
        "global.TOP_crisis_protection_faction_leader = "
        "global.TOP_crisis_actor_faction_leader"
    ) in initializer
    faction_event = _named_block(TRIGGERS, "TOP_crisis_faction_event_valid")
    assert "global.TOP_crisis_actor_faction_leader = THIS" in faction_event
    assert "global.TOP_crisis_protection_faction_leader = THIS" in faction_event
    faction_event_start = EVENTS.index("\tid = TOP_crisis.7")
    faction_event = EVENTS[faction_event_start : faction_event_start + 400]
    assert "minor_flavor = yes" in faction_event


def test_crisis_gate_requires_exact_live_headline_visit_and_lethal_result():
    gate = _named_block(TRIGGERS, "TOP_exposed_visit_kill_valid")
    for requirement in (
        "TOP_exposure_recorded = 1",
        "TOP_result = 3",
        "global.TOP_status^TOP_target = 3",
        "TOP_authorized_visit_story > 0",
        "TOP_authorized_visit_story < 6",
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
        assert f"TOP_authored_role_eligible_{target} = {{" in WRAPPERS
    assert "TOP_method_startable_7 = {" in WRAPPERS
    assert "set_temp_variable = { TOP_requested_method = 7 }" in WRAPPERS


def test_visit_retention_and_dossier_refresh_share_full_live_revalidation():
    planned = _named_block(TRIGGERS, "TOP_visit_planned_runtime_valid")
    active = _named_block(TRIGGERS, "TOP_visit_active_runtime_valid")
    for gate in (planned, active):
        assert "global.TOP_status^TOP_visit_trigger_target = 1" in gate
        assert "TOP_authored_role_eligible = yes" in gate
        assert "global.TOP_visit_host^TOP_visit_trigger_target = THIS" in gate
        assert "var:TOP_visit_trigger_state = { is_controlled_by = PREV }" in gate
        assert "TOP_visit_story_valid = yes" in gate
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
        for block in (processor, refresher):
            assert "set_temp_variable = { TOP_arg_target = TOP_visit_target }" in block
            assert f"{effect} = yes" in block
    assert "global.TOP_visit_minimum_confidence" in refresher


def test_invalid_visit_cleanup_requires_current_token_and_preserves_newer_locations():
    processor = _named_block(EFFECTS, "TOP_process_visits")
    assert (
        "global.TOP_visit_planned_token^TOP_visit_target = "
        "global.TOP_visit_token^TOP_visit_target"
    ) in processor
    assert (
        "global.TOP_visit_active_token^TOP_visit_target = "
        "global.TOP_visit_token^TOP_visit_target"
    ) in processor
    assert "var:TOP_visit_cleanup_host = { exists = yes }" in processor
    assert (
        "else = {\n"
        "\t\t\t\tset_temp_variable = { TOP_arg_target = TOP_visit_target }\n"
        "\t\t\t\tTOP_clear_visit = yes\n"
        "\t\t\t}"
    ) in processor

    end_visit = _named_block(EFFECTS, "TOP_end_visit")
    assert (
        "global.TOP_host^TOP_visit_target = global.TOP_visit_host^TOP_visit_target"
        in end_visit
    )
    assert (
        "global.TOP_state^TOP_visit_target = global.TOP_visit_state^TOP_visit_target"
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
