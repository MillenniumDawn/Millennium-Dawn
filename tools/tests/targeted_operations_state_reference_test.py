from pathlib import Path

import pytest
from targeted_operations_authorization_test import ReviewScript
from targeted_operations_core_test import ScriptArray, TargetScript
from targeted_operations_model_test import (
    _extract_block,
    _named_block,
    _parse_race_script,
)

ROOT = Path(__file__).resolve().parents[2]
ENCODED_STATE = -10737.40617
STATE_GUARDS = (
    (
        "scripted_effects/00_targeted_operations_effects.txt",
        "TOP_import_target_location",
        "TOP_import_state",
    ),
    (
        # Two guards: the var: scope open, and the monthly relocation roll.
        "scripted_effects/01_targeted_operations_world.txt",
        "TOP_global_monthly",
        "global.TOP_state^TOP_target",
        2,
    ),
    (
        "scripted_effects/01_targeted_operations_world.txt",
        "TOP_register_missing_organizations",
        "global.TOP_state^TOP_target",
    ),
    (
        "scripted_effects/01_targeted_operations_world.txt",
        "TOP_update_detained_targets",
        "global.TOP_custody_state^top_prisoner",
    ),
    (
        "scripted_effects/05_targeted_operations_runtime.txt",
        "TOP_end_visit",
        "global.TOP_visit_return_state^top_visit_target",
    ),
    (
        "scripted_effects/05_targeted_operations_runtime.txt",
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
        "scripted_triggers/02_targeted_operations_authorization_triggers.txt",
        "TOP_person_review_valid",
        "TOP_proposal_state",
    ),
    (
        "scripted_triggers/07_targeted_operations_redesign.txt",
        "TOP_organization_review_valid",
        "TOP_proposal_state",
    ),
    (
        "scripted_triggers/04_targeted_operations_cases.txt",
        "TOP_native_binding_unused",
        "TOP_binding_state",
    ),
    (
        "scripted_triggers/05_targeted_operations_runtime.txt",
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


def test_nested_registry_location_selection_writes_back_to_country_scope():
    registry = (
        ROOT / "common/scripted_effects/01_targeted_operations_registry.txt"
    ).read_text(encoding="utf-8")
    for group in (1, 17):
        choice = _named_block(registry, f"TOP_choose_location_{group}")
        activation = _named_block(registry, f"TOP_activate_group_{group}")
        assert "ROOT.TOP_activation_state = THIS" in choice
        assert "set_temp_variable = { TOP_activation_state = THIS }" not in choice
        assert "PREV.TOP_activation_host = controller" in activation


def test_numeric_loop_selectors_write_results_to_the_owner_frame():
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
        "common/scripted_effects/03_targeted_operations_political_roster.txt",
        "TOP_political_country_opportunities",
    )
    successor = _effect_text(
        "common/scripted_effects/01_targeted_operations_world.txt",
        "TOP_choose_successor",
    )
    visit = _effect_text(
        "common/scripted_effects/05_targeted_operations_runtime.txt",
        "TOP_visit_country_opportunities",
    )
    liaison = _effect_text(
        "common/scripted_effects/09_targeted_operations_depth.txt",
        "TOP_request_liaison",
    )
    linked = _effect_text(
        "common/scripted_effects/09_targeted_operations_depth.txt",
        "TOP_exploit_linked_targets",
    )

    assert "PREV.TOP_org_slot = top_find_i" in find_org
    assert "PREV.TOP_new_dossiers_this_tick = 1" in country_tick
    assert "PREV.TOP_modern_candidate = top_modern_target" in modern
    assert "PREV.TOP_modern_best_score = TOP_modern_score" in modern
    assert "PREV.TOP_political_candidate = top_political_person" in political
    assert "PREV.TOP_political_lowest = TOP_political_score" in political
    assert "PREV.TOP_candidate = top_generated_id" in successor
    assert "global.TOP_state^PREV.TOP_predecessor" in successor
    assert "PREV.TOP_visit_open_candidate = top_visit_person" in visit
    assert "TOP_visit_trigger_state = PREV.TOP_visit_open_state" in visit
    assert "PREV.TOP_liaison_pair_found = 1" in liaison
    assert "PREV.TOP_liaison_pair_until^top_liaison_index" in liaison
    assert "PREV.TOP_linked_first = top_linked_target" in linked
    assert "PREV.TOP_linked_second = top_linked_target" in linked
    assert linked.count("PREV.TOP_linked_best_score = TOP_linked_score") == 2


def test_state_and_fifo_selectors_do_not_depend_on_loop_local_temporaries():
    visit = _effect_text(
        "common/scripted_effects/05_targeted_operations_runtime.txt",
        "TOP_visit_country_opportunities",
    )
    oversight = _effect_text(
        "common/scripted_effects/09_targeted_operations_depth.txt",
        "TOP_dispatch_next_oversight",
    )
    transfer = _effect_text(
        "common/scripted_effects/01_targeted_operations_world.txt",
        "TOP_transfer_recorded_custody",
    )

    assert "ROOT.TOP_visit_open_state = THIS" in visit
    assert "TOP_oversight_queue^0" in oversight
    assert "for_each_loop" not in oversight
    assert (
        "global.TOP_custody_state^PREV.TOP_transfer_recipient_target = THIS" in transfer
    )


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
    assert review.temps["TOP_binding_key"] == pytest.approx(20000 + state * 2 + 2)


def test_retired_encoded_native_binding_cannot_be_recycled():
    review = ReviewScript()
    review.move_target(1, ENCODED_STATE, 2)
    review.approve_unilateral()
    review.begin_operation()
    assert review.binding(state=ENCODED_STATE)
    sequence = review.case(1, "sequence")
    review.call("TOP_close_case", TARGET=1, SEQUENCE=sequence)
    assert review.actor["TOP_retired_native_bindings"] == pytest.approx(
        [20000 + ENCODED_STATE * 2 + 2]
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
