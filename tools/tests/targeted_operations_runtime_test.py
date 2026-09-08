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
        assert (
            f"TOP_plan_visit = {{ TARGET = {target} STATE = {state} STORY = {story} }}"
            in EVENTS
        )
        assert f"country_event = {{ id = TOP_visit.1{story} days = 60 }}" in EVENTS
        assert (
            f"TOP_activate_visit = {{ TARGET = {target} STATE = {state} STORY = {story} }}"
            in EVENTS
        )
        assert f"country_event = {{ id = TOP_visit.2{story} days = 21 }}" in EVENTS
        assert f"TOP_end_visit = {{ TARGET = {target} STORY = {story} }}" in EVENTS


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
        "global.TOP_clock < global.TOP_visit_execution_until^TOP_case_visit_target"
        in execution
    )
    assert "TOP_case_visit_execution_valid = yes" in CASE_TRIGGERS


def test_cancelled_visit_closes_preparation_but_underway_operation_fails_closed():
    processor = _named_block(CASES, "TOP_process_cases")
    assert "TOP_case_phase^TOP_target < 3" in processor
    assert "global.TOP_visit_status^TOP_target = 0" in processor
    assert "NOT = { TOP_authored_role_eligible = yes }" in processor
    assert "TOP_case_phase^TOP_target = 3" in processor
    assert "TOP_mission_binding_valid = yes" in processor


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
        assert f"TOP_adjust_crisis_tension = {{ AMOUNT = {delta} }}" in EVENTS
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
