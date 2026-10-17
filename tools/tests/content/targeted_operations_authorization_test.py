import json
import re
from copy import deepcopy
from pathlib import Path

import pytest
from targeted_operations_helpers_test import TargetedScript
from targeted_operations_model_test import (
    _extract_block,
    _named_block,
    _parse_race_script,
)
from targeted_operations_redesign_test import read as source

ROOT = Path(__file__).resolve().parents[3]
EFFECT_PATH = "common/scripted_effects/02_targeted_operations_authorization_effects.txt"
TRIGGER_PATH = (
    "common/scripted_triggers/02_targeted_operations_authorization_triggers.txt"
)
EVENT_PATH = "events/Targeted Operations.txt"


class ReviewScript(TargetedScript):
    """Execute approval source with engine diplomacy and core eligibility as fixtures."""

    country_trigger_fields = {
        "has_political_power": "power",
        "num_of_controlled_states": "states",
    }

    def __init__(self, designated=True):
        self.effects = _parse_race_script(source(EFFECT_PATH))
        core = _parse_race_script(
            source("common/scripted_effects/00_targeted_operations_effects.txt")
        )
        self.effects.update(core)
        self.effects.update(
            _parse_race_script(
                source("common/scripted_effects/04_targeted_operations_cases.txt")
            )
        )
        self.effects.update(
            _parse_race_script(
                source("common/scripted_effects/06_targeted_operations_redesign.txt")
            )
        )
        self.effects.update(
            _parse_race_script(
                source(
                    "common/scripted_effects/07_targeted_operations_organization_cases.txt"
                )
            )
        )
        self.effects.update(
            TOP_refresh_view=[],
            TOP_enroll_pending_actor=[],
            TOP_initialize_global=[],
            TOP_country_initialize=[],
            TOP_build_view=[],
            TOP_get_defensive_modifiers=[],
            TOP_get_organization_defensive_modifiers=[],
            TOP_get_protection_country=[],
        )
        self.triggers = _parse_race_script(source(TRIGGER_PATH))
        core_triggers = _parse_race_script(
            source("common/scripted_triggers/01_targeted_operations_triggers.txt")
        )
        self.triggers.update(core_triggers)
        self.triggers.update(
            _parse_race_script(
                source(
                    "common/scripted_triggers/03_targeted_operations_political_roster.txt"
                )
            )
        )
        self.triggers.update(
            _parse_race_script(
                source("common/scripted_triggers/04_targeted_operations_cases.txt")
            )
        )
        self.triggers.update(
            _parse_race_script(
                source("common/scripted_triggers/07_targeted_operations_redesign.txt")
            )
        )
        self.countries = {
            country: {
                "vars": {},
                "exists": country > 0,
                "ai": False,
                "tag": {0: "---", 1: "USA", 2: "YEM", 3: "PAK", 100: "STATE"}[country],
                "flags": {},
                "techs": {"special_forces_tech_1", "decryption_1"},
                "missions": set(),
                "power": 200,
                "authority": True,
                "enhanced": False,
                "opinion": {},
                "allies": set(),
                "wars": set(),
                "facilities": {1, 2, 3},
                "states": 1,
                "war": False,
                "civil_war": False,
            }
            for country in (0, 1, 2, 3, 100)
        }
        self.countries[100]["controller"] = 2
        for country in self.countries.values():
            country["vars"]["TOP_liaison_partners"] = []
        manifest = json.loads(source("tools/data/targeted_operations.json"))
        self.globals = {
            "TOP_clock": 7,
            "TOP_status^num": manifest["capacity"],
            "TOP_registry_capacity": manifest["capacity"],
            "TOP_rule_mode": 2,
            "TOP_group_class^num": len(manifest["groups"]) + 1,
        }
        self.global_flags = {}
        self.temps, self.events, self.event_targets, self.scope_stack = {}, [], {}, []
        for target in (1, 2):
            self.globals[f"TOP_status^{target}"] = 1
            self.globals[f"TOP_political^{target}"] = 0
            self.globals[f"TOP_affiliation^{target}"] = target
            self.globals[f"TOP_state^{target}"] = 100
            self.globals[f"TOP_host^{target}"] = 2
            self.globals[f"TOP_group_ct^{target}"] = target - 1
            self.globals[f"TOP_group_class^{target}"] = 1
            self.globals[f"TOP_leader_role^{target}"] = 0
        self.globals["active_terror_orgs"] = [0, 1]
        self.globals["TOP_active_targets"] = [1, 2]
        self.actor = self.countries[1]["vars"]
        self.actor.update(
            TOP_selected=1,
            TOP_selected_kind=1,
            TOP_selected_facility=1,
            TOP_doctrine=2,
            TOP_collecting_subjects=[],
            TOP_organization_dossiers=[],
            TOP_attribution_pending_people=[],
            TOP_attribution_pending_organizations=[],
        )
        self.actor["TOP_dossiers"] = [1, 2]
        self.actor["TOP_active_cases"] = []
        self.actor["TOP_retired_native_bindings"] = []
        for target in (1, 2):
            self.actor[f"TOP_known^{target}"] = 1
            self.actor[f"TOP_confidence^{target}"] = 95
            self.actor[f"TOP_identity_confidence^{target}"] = 95
            self.actor[f"TOP_location_confidence^{target}"] = 95
            self.actor[f"TOP_pattern_confidence^{target}"] = 95
            self.actor[f"TOP_package_state^{target}"] = 1
            self.actor[f"TOP_lead_age^{target}"] = 0
            self.actor[f"TOP_lead_state^{target}"] = 100
            self.actor[f"TOP_lead_host^{target}"] = 2
        if designated:
            self.run("TOP_designate_selected")

    def _scope(self, name, identifier):
        if "^" in name:
            head, index = name.rsplit("^", 1)
            if index != "num":
                name = f"{head}^{int(self.value(index, identifier))}"
        return super()._scope(name, identifier)

    def value(self, name, identifier):
        if name == "THIS":
            return identifier
        if name == "PREV":
            return self.scope_stack[-1]
        if name == "controller":
            return self.countries[identifier].get("controller", 0)
        if isinstance(name, str) and name.startswith("var:"):
            return self.value(name[4:], identifier)
        if isinstance(name, str) and name.endswith("^num"):
            scope, key = self._scope(name, identifier)
            if key[:-4] in scope:
                return len(scope[key[:-4]])
            return scope.get(key, 0)
        return super().value(name, identifier)

    def condition_statement(self, statement, identifier):
        key, comparison, operand = statement
        country = self.countries[identifier]
        if key.startswith("var:") or key == "controller":
            target = self.value(key, identifier)
            self.scope_stack.append(identifier)
            try:
                result = self.condition(operand, target)
            finally:
                self.scope_stack.pop()
        elif key in {"TOP_enabled", "TOP_country_eligible"}:
            result = country["exists"] == (operand == "yes")
        elif key == "TOP_authored_role_eligible":
            result = True
        elif key == "TOP_authored_capture_override":
            result = operand == "no"
        elif key == "TOP_authored_civilian_mandate_valid":
            result = operand == "no"
        elif key == "TOP_exceptional_authority":
            result = country["authority"] == (operand == "yes")
        elif key in {
            "TOP_case_visit_review_valid",
            "TOP_case_visit_execution_valid",
            "TOP_case_visit_approval_fits",
        }:
            result = operand != "no"
        elif key == "TOP_facility_available":
            state = self.countries[self.temps["TOP_facility_state"]]
            result = (self.temps["TOP_facility_kind"] in state["facilities"]) == (
                operand == "yes"
            )
        elif key == "TOP_organization_facility_available":
            state = self.countries[self.temps["TOP_facility_state"]]
            result = (self.temps["TOP_facility_objective"] in state["facilities"]) == (
                operand == "yes"
            )
        elif key in {
            "western_conservatism_are_in_power",
            "western_liberals_are_in_power",
            "western_social_democrats_are_in_power",
        }:
            result = country["enhanced"] == (operand == "yes")
        elif key in {
            "western_autocrats_are_in_power",
            "emerging_autocracy_are_in_power",
            "emerging_hardline_shiite_are_in_power",
            "salafist_caliphate_are_in_power",
            "neutrality_neutral_autocracy_are_in_power",
            "nationalist_fascist_are_in_power",
            "nationalist_military_junta_are_in_power",
        }:
            result = operand != "yes"
        elif key == "has_civil_war":
            result = country["civil_war"] == (operand == "yes")
        elif key == "is_controlled_by":
            result = country.get("controller", 0) == self.value(operand, identifier)
        elif key in {"has_war_with", "is_in_faction_with"}:
            pool = "wars" if key == "has_war_with" else "allies"
            result = self.value(operand, identifier) in country[pool]
        elif key == "has_opinion":
            data = {name: value for name, _, value in operand}
            target = self.value(data["target"], identifier)
            _, op, bound = next((entry for entry in operand if entry[0] == "value"))
            result = self.comparisons[op](
                country["opinion"].get(target, 0), float(bound)
            )
        else:
            result = super().condition_statement(statement, identifier)
        return result

    def execute_statement(self, statement, identifier):
        key, comparison, operand = statement
        if key == "for_each_loop":
            data = {name: value for name, _, value in operand}
            for index, value in enumerate(
                list(self.value(data["array"], identifier) or [])
            ):
                self.temps[data["value"]] = value
                if "index" in data:
                    self.temps[data["index"]] = index
                self.execute(
                    [
                        entry
                        for entry in operand
                        if entry[0] not in {"array", "value", "index"}
                    ],
                    identifier,
                )
        elif key == "add_political_power":
            self.countries[identifier]["power"] += self.value(operand, identifier)
        elif key == "PREV":
            previous = self.value(key, identifier)
            self.scope_stack.append(identifier)
            try:
                self.execute(operand, previous)
            finally:
                self.scope_stack.pop()
        elif key == "save_event_target_as":
            self.event_targets[operand] = identifier
        elif key == "remove_from_array":
            name, _, value = operand[0]
            values = self.value(name, identifier) or []
            member = self.value(value, identifier)
            if member in values:
                values.remove(member)
        else:
            super().execute_statement(statement, identifier)

    def run(self, name, identifier=1):
        self.execute(self.effects[name], identifier)

    def call(self, name, identifier=1, **parameters):
        # Effects read TOP_arg_* temp variables now; see the core harness.
        if name == "TOP_answer_host_request" and "CONSENT" in parameters:
            parameters["POSTURE"] = 4 if parameters.pop("CONSENT") else 5
        for key, value in parameters.items():
            self.temps[f"TOP_arg_{key.lower()}"] = value
        self.execute([(name, "=", "yes")], identifier)

    def ready_for_host(self, method=2):
        self.run("TOP_designate_selected")
        self.call("TOP_begin_review", METHOD=method)
        self.run("TOP_close_review_event")
        self.run("TOP_submit_staff_review")
        self.run("TOP_close_review_event")

    def approve_unilateral(self, method=2):
        self.ready_for_host(method)
        self.run("TOP_open_senior_review")
        self.run("TOP_close_review_event")
        self.run("TOP_approve_review")

    def begin_operation(self, target=None):
        target = target or self.actor["TOP_selected"]
        self.call("TOP_begin_person_operation", TARGET=target)

    def set_axes(self, target, value):
        for axis in (
            "identity_confidence",
            "location_confidence",
            "pattern_confidence",
        ):
            self.actor[f"TOP_{axis}^{target}"] = value
        self.actor[f"TOP_confidence^{target}"] = value

    def binding(self, target=1, method=2, state=100):
        # TOP_case_binding_valid no longer takes parameters: the engine cannot
        # substitute $PARAM$ for a scripted trigger, so it reads temp variables.
        self.temps.update(
            TOP_target=target,
            TOP_method=method,
            TOP_operation_state=state,
            TOP_arg_target=target,
            TOP_arg_method=method,
            TOP_arg_state=state,
        )
        return self.condition(self.triggers["TOP_case_binding_valid"], 1)

    def case(self, target, field):
        return self.actor.get(f"TOP_case_{field}^{target}", 0)

    def move_target(self, target, state, host):
        self.countries[state] = deepcopy(self.countries[100])
        self.countries[state]["controller"] = host
        self.globals[f"TOP_state^{target}"] = state
        self.globals[f"TOP_host^{target}"] = host
        self.actor[f"TOP_lead_state^{target}"] = state
        self.actor[f"TOP_lead_host^{target}"] = host


def test_reselection_during_review_commits_only_the_immutable_snapshot_once():
    review = ReviewScript()
    review.ready_for_host()
    review.actor["TOP_selected"] = 2
    review.run("TOP_send_host_request")
    assert "TOP_host_request_sender" not in review.event_targets
    assert review.countries[2]["vars"]["TOP_incoming_actor"] == 1
    review.call("TOP_answer_host_request", identifier=2, CONSENT=1)
    review.run("TOP_close_review_event")
    review.run("TOP_approve_review")
    assert review.actor["TOP_authorized_target"] == 1
    assert review.actor["TOP_authorized_method"] == 2
    assert review.actor["TOP_authorized_state"] == 100
    assert review.actor["TOP_authorized_consent"] == 1
    assert review.countries[1]["power"] == 150
    review.run("TOP_approve_review")
    assert review.countries[1]["power"] == 150


def test_old_host_reply_cannot_approve_even_an_identical_later_proposal():
    review = ReviewScript()
    review.ready_for_host()
    review.run("TOP_send_host_request")
    first_sequence = review.actor["TOP_proposal_sequence"]
    review.run("TOP_cancel_review")
    review.ready_for_host()
    assert review.actor["TOP_proposal_sequence"] == first_sequence + 1
    review.actor["TOP_proposal_stage"] = 3
    review.call("TOP_answer_host_request", identifier=2, CONSENT=1)
    assert review.actor["TOP_proposal_stage"] == 3
    assert review.actor["TOP_proposal_consent"] == 0
    assert review.countries[2]["vars"]["TOP_incoming_actor"] == 0


def test_approval_waits_for_explicit_preparation_before_binding_native_operation():
    review = ReviewScript()
    review.approve_unilateral()
    original_until = review.actor["TOP_authorized_until"]
    original_sequence = review.case(1, "sequence")
    assert review.case(1, "phase") == 2
    assert review.actor.get("TOP_operation_subject_kind", 0) == 0
    assert not review.binding()

    review.begin_operation()
    assert review.case(1, "phase") == 3
    assert review.actor["TOP_operation_subject_kind"] == 1
    assert review.actor["TOP_operation_subject_id"] == 1
    assert review.actor["TOP_operation_sequence"] == original_sequence
    assert review.actor["TOP_authorized_until"] == original_until
    assert review.case(1, "sequence") == original_sequence
    assert review.actor["TOP_active_cases"] == [1]
    assert review.binding()
    assert review.countries[1]["power"] == 150


@pytest.mark.parametrize("changed", ("target", "method", "state"))
def test_explicit_replacement_cannot_accept_the_retired_native_callback(changed):
    review = ReviewScript()
    review.approve_unilateral()
    review.begin_operation()
    review.call("TOP_close_case", TARGET=1, SEQUENCE=review.case(1, "sequence"))
    method = 2
    if changed == "target":
        review.actor["TOP_selected"] = 2
    elif changed == "method":
        method = 1
    else:
        review.move_target(1, 101, 2)
    review.approve_unilateral(method)
    assert not review.binding()
    review.begin_operation()
    assert review.binding(
        target=review.actor["TOP_authorized_target"],
        method=review.actor["TOP_authorized_method"],
        state=review.actor["TOP_authorized_state"],
    )


def test_two_host_approvals_preserve_both_immutable_native_cases():
    review = ReviewScript()
    review.approve_unilateral()
    first = {name: value for name, value in review.actor.items() if name.endswith("^1")}
    review.move_target(2, 101, 3)
    review.actor["TOP_selected"] = 2
    review.approve_unilateral(method=1)
    assert review.actor["TOP_active_cases"] == [1, 2]
    assert review.case(1, "host") == 2
    assert review.case(2, "host") == 3
    assert review.case(1, "phase") == review.case(2, "phase") == 2
    assert {
        name: value for name, value in review.actor.items() if name.endswith("^1")
    } == first
    assert not review.binding(target=1, method=2, state=100)
    assert not review.binding(target=2, method=1, state=101)
    review.begin_operation(target=1)
    assert review.binding(target=1, method=2, state=100)
    review.begin_operation(target=2)
    assert review.case(2, "phase") == 2
    assert not review.binding(target=2, method=1, state=101)
    review.call("TOP_close_case", TARGET=1, SEQUENCE=review.case(1, "sequence"))
    review.begin_operation(target=2)
    assert review.binding(target=2, method=1, state=101)
    assert review.countries[1]["power"] == 100


def test_two_people_in_same_host_can_hold_parallel_waiting_mandates():
    review = ReviewScript()
    review.approve_unilateral()
    sequence = review.case(1, "sequence")
    review.actor["TOP_selected"] = 2
    review.approve_unilateral()
    assert review.actor["TOP_active_cases"] == [1, 2]
    assert review.case(1, "sequence") == sequence
    assert review.case(1, "phase") == 2
    assert review.case(2, "phase") == 2
    assert review.countries[1]["power"] == 100

    review.begin_operation(target=1)
    review.begin_operation(target=2)
    assert review.case(1, "phase") == 3
    assert review.case(2, "phase") == 2
    assert review.binding(target=1)


@pytest.mark.parametrize(
    "phase", [4, 5], ids=["assessment_pending", "confirmation_pending"]
)
def test_unconfirmed_assessment_does_not_block_another_same_host_package(phase):
    review = ReviewScript()
    review.actor["TOP_case_phase^1"] = phase
    review.actor["TOP_selected"] = 2
    review.approve_unilateral()
    assert review.case(1, "phase") == phase
    assert review.case(2, "phase") == 2
    assert review.countries[1]["power"] == 150


def test_commit_does_not_reintroduce_the_removed_one_case_per_host_limit():
    review = ReviewScript()
    review.ready_for_host()
    review.run("TOP_open_senior_review")
    review.run("TOP_close_review_event")
    review.actor["TOP_active_cases"].append(2)
    review.actor.update({"TOP_case_phase^2": 2, "TOP_case_host^2": 2})
    review.run("TOP_approve_review")
    assert review.case(1, "phase") == 2
    assert review.case(2, "phase") == 2
    assert review.countries[1]["power"] == 150


def test_closed_native_tuple_cannot_be_reused_even_by_a_fresh_review():
    review = ReviewScript()
    review.approve_unilateral()
    review.begin_operation()
    sequence = review.case(1, "sequence")
    review.call("TOP_close_case", TARGET=1, SEQUENCE=sequence)
    retired = list(review.actor["TOP_retired_native_bindings"])
    assert len(retired) == 1
    review.approve_unilateral()
    assert review.case(1, "phase") == 0
    assert review.case(1, "sequence") == sequence
    assert not review.binding()
    assert review.countries[1]["power"] == 150
    review.approve_unilateral(method=1)
    assert review.case(1, "phase") == 2
    review.begin_operation()
    assert review.binding(method=1)
    assert review.actor["TOP_retired_native_bindings"] == retired


def test_closing_the_case_during_review_invalidates_its_saved_sequence():
    review = ReviewScript()
    review.ready_for_host()
    review.run("TOP_open_senior_review")
    review.run("TOP_close_review_event")
    saved_sequence = review.actor["TOP_proposal_case_sequence"]
    review.call("TOP_close_case", TARGET=1, SEQUENCE=saved_sequence)
    review.run("TOP_approve_review")
    assert review.case(1, "phase") == 0
    assert review.countries[1]["power"] == 200
    review.run("TOP_cancel_review")
    review.call("TOP_begin_review", METHOD=2)
    assert review.case(1, "sequence") != saved_sequence
    assert review.actor["TOP_proposal_stage"] == 1


def test_core_commit_requires_senior_review_and_consumes_it_once():
    review = ReviewScript()
    review.call("TOP_begin_review", METHOD=2)
    review.run("TOP_commit_reviewed_authorization")
    assert review.countries[1]["power"] == 200
    review.run("TOP_close_review_event")
    review.run("TOP_submit_staff_review")
    review.run("TOP_close_review_event")
    review.run("TOP_open_senior_review")
    review.run("TOP_commit_reviewed_authorization")
    review.run("TOP_commit_reviewed_authorization")
    assert review.countries[1]["power"] == 150


def test_returning_review_resumes_the_original_package_without_another_cost():
    review = ReviewScript()
    review.call("TOP_begin_review", METHOD=2)
    review.actor["TOP_selected"] = 2
    text = source(EVENT_PATH)
    option_at = text.index("name = TOP_authorization.1.b")
    option = _extract_block(text, text.rfind("option = {", 0, option_at))
    effect = _parse_race_script(_named_block(option, "hidden_effect"))["hidden_effect"]
    review.execute(effect, 1)
    assert review.actor["TOP_package_state^1"] == 2
    assert review.actor["TOP_collecting_subjects"] == [1]
    assert review.actor["TOP_proposal_stage"] == 0
    assert review.countries[1]["power"] == 200


def test_return_to_existing_collection_does_not_charge_twice():
    review = ReviewScript()
    review.call("TOP_begin_review", METHOD=2)
    review.run("TOP_return_recorded_collection")
    assert review.actor["TOP_package_state^1"] == 2
    assert review.actor["TOP_collecting_subjects"] == [1]
    assert review.countries[1]["power"] == 200


@pytest.mark.parametrize("recreate", [False, True], ids=["closed", "new_sequence"])
def test_stale_return_to_collection_cannot_charge_or_reopen_a_closed_case(recreate):
    review = ReviewScript()
    review.call("TOP_begin_review", METHOD=2)
    saved_sequence = review.case(1, "sequence")
    review.call("TOP_close_case", TARGET=1, SEQUENCE=saved_sequence)
    if recreate:
        review.run("TOP_close_review_event")
        review.run("TOP_cancel_review")
        review.call("TOP_begin_review", METHOD=2)
        assert review.case(1, "sequence") != saved_sequence
        review.actor["TOP_proposal_case_sequence"] = saved_sequence
    review.run("TOP_return_recorded_collection")
    assert review.case(1, "phase") == int(recreate)
    assert review.actor["TOP_package_state^1"] == (3 if recreate else 1)
    assert review.actor["TOP_collecting_subjects"] == []
    assert review.countries[1]["power"] == 200


def test_busy_host_cannot_replace_an_open_request_or_grant_partner_authority():
    review = ReviewScript()
    review.ready_for_host(method=5)
    review.countries[2]["vars"].update(
        TOP_incoming_actor=3, TOP_incoming_sequence=27, TOP_incoming_target=2
    )
    review.run("TOP_send_host_request")
    assert review.countries[2]["vars"]["TOP_incoming_actor"] == 3
    assert review.countries[2]["vars"]["TOP_incoming_sequence"] == 27
    assert review.actor["TOP_proposal_stage"] == 4
    assert not review.condition(review.triggers["TOP_review_can_approve"], 1)
    review.run("TOP_approve_review")
    assert "TOP_authorized_target" not in review.actor


@pytest.mark.parametrize("expire", (False, True))
def test_actor_window_tombstone_prevents_stale_approval_and_releases_on_close(expire):
    review = ReviewScript()
    review.call("TOP_begin_review", METHOD=1)
    if expire:
        review.globals["TOP_clock"] = 49
        review.run("TOP_review_tick")
    else:
        review.run("TOP_cancel_review")
    sequence = review.actor["TOP_proposal_sequence"]
    review.call("TOP_begin_review", METHOD=1)
    assert review.actor["TOP_proposal_sequence"] == sequence
    review.run("TOP_approve_review")
    assert review.countries[1]["power"] == 200
    review.run("TOP_close_review_event")
    review.call("TOP_begin_review", METHOD=1)
    assert review.actor["TOP_proposal_sequence"] == sequence + 1


@pytest.mark.parametrize("method", (1, 2, 3, 4, 5))
def test_all_methods_reach_review_with_required_capabilities(method):
    review = ReviewScript()
    review.call("TOP_begin_review", METHOD=method)
    assert review.actor["TOP_proposal_stage"] == 1
    assert review.condition(review.triggers["TOP_review_staff_ready"], 1)


@pytest.mark.parametrize(
    "method,tech",
    ((2, "special_forces_tech_1"), (4, "special_forces_tech_1"), (3, "decryption_1")),
)
def test_missing_capability_cannot_bypass_review_backend(method, tech):
    review = ReviewScript()
    review.countries[1]["techs"].remove(tech)
    review.call("TOP_begin_review", METHOD=method)
    assert review.actor.get("TOP_proposal_stage", 0) == 0
    assert review.events == []


@pytest.mark.parametrize(
    "changed",
    ("controller", "status", "authority", "doctrine", "funding", "capability"),
)
def test_changed_case_invalidates_senior_approval_without_spending(changed):
    review = ReviewScript()
    review.ready_for_host()
    review.run("TOP_open_senior_review")
    if changed == "controller":
        review.countries[100]["controller"] = 3
    elif changed == "status":
        review.globals["TOP_status^1"] = 2
    elif changed == "authority":
        review.globals["TOP_rule_mode"] = 1
        review.globals["TOP_group_class^1"] = 2
    elif changed == "doctrine":
        review.actor["TOP_doctrine"] = 1
    elif changed == "funding":
        review.countries[1]["power"] = 49
    else:
        review.countries[1]["techs"].remove("special_forces_tech_1")
    power = review.countries[1]["power"]
    review.run("TOP_approve_review")
    assert review.countries[1]["power"] == power
    assert "TOP_authorized_target" not in review.actor


def test_current_dossier_changes_do_not_rewrite_an_immutable_review_snapshot():
    review = ReviewScript()
    review.ready_for_host()
    review.run("TOP_open_senior_review")
    review.actor["TOP_lead_state^1"] = 101
    review.actor["TOP_lead_host^1"] = 3
    review.set_axes(1, 0)
    review.run("TOP_approve_review")
    assert review.case(1, "phase") == 2
    assert review.case(1, "state") == 100
    assert review.case(1, "host") == 2
    assert review.case(1, "identity") == 95
    assert review.countries[1]["power"] == 150


def test_feasible_capture_warns_but_does_not_veto_a_lethal_method():
    review = ReviewScript()
    review.countries[1]["enhanced"] = True
    review.countries[2]["opinion"][1] = 75
    review.call("TOP_begin_review", METHOD=1)
    assert review.actor["TOP_proposal_capture_feasible"] == 1
    assert review.condition(review.triggers["TOP_review_staff_ready"], 1)
    review.run("TOP_cancel_review")
    review.run("TOP_close_review_event")
    review.call("TOP_begin_review", METHOD=2)
    assert review.condition(review.triggers["TOP_review_staff_ready"], 1)


def test_political_target_uses_enhanced_review_even_for_standard_government():
    review = ReviewScript()
    review.globals["TOP_political^1"] = 1
    review.globals["TOP_leader_role^1"] = 1
    review.set_axes(1, 79)
    review.call("TOP_begin_review", METHOD=2)
    assert review.actor.get("TOP_proposal_stage", 0) == 0

    review.set_axes(1, 80)
    review.call("TOP_begin_review", METHOD=2)
    assert review.actor["TOP_proposal_rigor"] == 2
    assert review.condition(review.triggers["TOP_review_staff_ready"], 1)


def test_leader_assassination_final_confirmation_commits_the_waiting_mandate():
    review = ReviewScript()
    review.globals["TOP_political^1"] = 1
    review.globals["TOP_leader_role^1"] = 1
    review.approve_unilateral(method=3)
    assert review.actor["TOP_proposal_stage"] == 5
    assert review.case(1, "phase") == 1
    assert review.countries[1]["power"] == 200

    review.run("TOP_close_review_event")
    review.run("TOP_confirm_leader_assassination")

    assert review.case(1, "phase") == 2
    assert review.case(1, "method") == 3
    assert review.countries[1]["power"] == 150
    assert review.actor.get("TOP_proposal_stage", 0) == 0


def test_facility_sabotage_uses_the_typed_organization_review_path():
    person_start = _named_block(
        source("common/scripted_triggers/01_targeted_operations_triggers.txt"),
        "TOP_method_startable",
    )
    organization_review = _named_block(
        source("common/scripted_effects/07_targeted_operations_organization_cases.txt"),
        "TOP_begin_organization_review",
    )
    organization_valid = _named_block(
        source("common/scripted_triggers/07_targeted_operations_redesign.txt"),
        "TOP_organization_review_valid",
    )
    assert "NOT = { check_variable = { TOP_requested_method = 6 } }" in person_start
    assert "set_variable = { TOP_proposal_subject_kind = 2 }" in organization_review
    assert "set_variable = { TOP_proposal_method = 6 }" in organization_review
    assert (
        "set_variable = { TOP_proposal_objective = TOP_selected_facility }"
        in organization_review
    )
    assert "TOP_facility_operational_eligible = yes" in organization_valid
    assert "TOP_facility_access_available = yes" in organization_valid


def test_annual_opportunity_grants_once_and_report_acknowledgement_has_no_payload():
    review = ReviewScript()
    review.set_axes(1, 40)
    review.set_axes(2, 10)
    review.run("TOP_modern_opportunities_2024")
    review.run("TOP_modern_country_opportunity")
    assert review.actor["TOP_confidence^1"] == 65
    assert review.actor["TOP_identity_confidence^1"] == 65
    assert review.actor["TOP_location_confidence^1"] == 65
    assert review.actor["TOP_pattern_confidence^1"] == 65
    assert review.actor["TOP_modern_2024_target"] == 1
    assert review.events == [(1, "TOP_opportunity.1")]
    review.run("TOP_modern_country_opportunity")
    assert review.actor["TOP_confidence^1"] == 65
    assert len(review.events) == 1
    text = source(EVENT_PATH)
    for number in (1, 2, 3):
        event_at = text.index(f"id = TOP_opportunity.{number}\n")
        event = _extract_block(text, text.rfind("country_event = {", 0, event_at))
        assert "minor_flavor = yes" in event
        option = _parse_race_script(_named_block(event, "option"))["option"]
        assert option == [("name", "=", f"TOP_opportunity.{number}.a")]


@pytest.mark.parametrize(
    "blocked", ("captured", "dead", "retired", "unknown", "inactive", "political")
)
def test_modern_opportunities_never_create_or_reactivate_an_ineligible_target(blocked):
    review = ReviewScript()
    review.actor["TOP_dossiers"] = [1]
    if blocked in {"captured", "dead", "retired"}:
        review.globals["TOP_status^1"] = {"captured": 2, "dead": 3, "retired": 4}[
            blocked
        ]
    elif blocked == "unknown":
        review.actor["TOP_known^1"] = 0
    elif blocked == "inactive":
        review.globals["TOP_active_targets"] = []
    else:
        review.globals["TOP_political^1"] = 1
    status = review.globals["TOP_status^1"]
    review.run("TOP_modern_opportunities_2026")
    review.run("TOP_modern_country_opportunity")
    assert review.actor["TOP_confidence^1"] == 95
    assert review.globals["TOP_status^1"] == status
    assert review.events == []
    assert "TOP_authorized_target" not in review.actor


def test_modern_threat_priority_and_yearly_report_snapshots_are_independent():
    review = ReviewScript()
    review.set_axes(1, 20)
    review.set_axes(2, 40)
    review.globals["active_terror_org_threat_lvl^0"] = 60
    review.run("TOP_modern_opportunities_2024")
    review.run("TOP_modern_country_opportunity")
    assert review.actor["TOP_modern_2024_target"] == 1
    review.set_axes(2, 90)
    review.globals["active_terror_org_threat_lvl^0"] = 0
    review.run("TOP_modern_opportunities_2025")
    review.run("TOP_modern_country_opportunity")
    assert review.actor["TOP_modern_2024_target"] == 1
    assert review.actor["TOP_modern_2025_target"] == 2


def test_modern_annual_marker_never_moves_backwards_and_ai_needs_no_popup():
    review = ReviewScript()
    review.countries[1]["ai"] = True
    review.set_axes(1, 40)
    review.set_axes(2, 10)
    review.run("TOP_modern_opportunities_2026")
    review.run("TOP_modern_opportunities_2024")
    assert review.globals["TOP_modern_year"] == 2026
    review.run("TOP_modern_country_opportunity")
    assert review.actor["TOP_confidence^1"] == 65
    assert review.actor["TOP_modern_2026_target"] == 1
    assert review.events == []


def test_expired_modern_window_does_not_replay_as_a_later_campaign_year():
    review = ReviewScript()
    review.run("TOP_modern_opportunities_2026")
    review.globals["TOP_clock"] += 365
    review.run("TOP_modern_country_opportunity")
    assert "TOP_last_modern_year" not in review.actor
    assert review.events == []


def test_event_defaults_defer_and_options_have_matching_logs_and_localisation():
    text = source(EVENT_PATH)
    loc_path = (
        ROOT / "localisation/english/MD_targeted_operations_authorization_l_english.yml"
    )
    assert loc_path.read_bytes().startswith(b"\xef\xbb\xbf")
    loc = loc_path.read_text(encoding="utf-8-sig")
    for number, first in ((1, "c"), (2, "e"), (3, "b"), (4, "c")):
        match = re.search(rf"\tid = TOP_authorization\.{number}\n", text)
        start = text.rfind("country_event = {", 0, match.start())
        event = _extract_block(text, start)
        assert "is_triggered_only = yes" in event
        assert "mean_time_to_happen" not in event
        assert f"name = TOP_authorization.{number}.{first}" in _named_block(
            event, "option"
        )
        for key in re.findall(r"(?:title|desc|name) = (TOP_authorization\.\S+)", event):
            assert f" {key}:" in loc
        for option in re.finditer(r"\n\toption = \{", event):
            body = _extract_block(event, option.start())
            name = re.search(r"name = (\S+)", body)[1]
            assert f'{name} executed"' in body


def test_final_leader_assassination_confirmation_revalidates_full_authority():
    text = source(EVENT_PATH)
    event_at = text.index("id = TOP_authorization.5\n")
    event = _extract_block(text, text.rfind("country_event = {", 0, event_at))
    authorize = _named_block(event, "option")

    assert (
        "trigger = { TOP_review_can_confirm_leader_assassination = yes }" in authorize
    )
    assert "TOP_confirm_leader_assassination = yes" in authorize


def test_snapshot_identity_and_host_slot_have_single_writers():
    effects = _parse_race_script(source(EFFECT_PATH))
    for name, body in effects.items():
        rendered = repr(body)
        if name != "TOP_begin_review":
            for field in ("target", "method", "state", "host", "sequence"):
                assert (
                    f"('set_variable', '=', [('TOP_proposal_{field}'," not in rendered
                )
        if name not in {
            "TOP_send_host_request",
            "TOP_answer_host_request",
            "TOP_clear_incoming_host_request",
        }:
            assert "TOP_incoming_actor" not in rendered
    assert "TOP_selected" not in _named_block(source(EFFECT_PATH), "TOP_approve_review")
    assert "TOP_selected" not in _named_block(source(TRIGGER_PATH), "TOP_review_valid")


def test_novichok_is_a_russia_only_high_exposure_timed_method():
    startable = _named_block(
        source("common/scripted_triggers/01_targeted_operations_triggers.txt"),
        "TOP_method_startable",
    )
    access = _named_block(
        source("common/scripted_triggers/01_targeted_operations_triggers.txt"),
        "TOP_person_access_available",
    )
    review = _named_block(source(TRIGGER_PATH), "TOP_person_review_valid")
    lethal = _named_block(source(TRIGGER_PATH), "TOP_review_lethal")
    resolution = source("common/scripted_effects/08_targeted_operations_resolution.txt")
    gui = source("common/scripted_guis/01_targeted_operations_gui.txt")
    layout = source("interface/targeted_operations.gui")
    assert "TOP_requested_method = 7" in startable
    assert "TOP_identity_confidence^TOP_selected > 89" in startable
    assert "TOP_access_method = 7" in access
    assert "original_tag = SOV" in access
    assert "has_tech = decryption_2" in access
    assert "TOP_proposal_method < 8" in review
    assert "TOP_proposal_method = 7" in review
    assert "TOP_person_access_available = yes" in review
    assert "TOP_proposal_identity > 89" in review
    assert "TOP_proposal_method = 7" in lethal
    assert "TOP_method = 7" in _named_block(resolution, "TOP_resolve_person_operation")
    exposure = _named_block(source(EFFECT_PATH), "TOP_calculate_person_proposal_risks")
    assert "TOP_proposal_method = 7" in exposure
    assert "TOP_proposal_exposure_score = 65" in exposure
    assert "set_temp_variable = { TOP_arg_method = 7 } TOP_begin_review = yes" in gui
    assert 'name = "TOP_novichok"' in layout


@pytest.mark.parametrize(
    ("path", "actor", "expected_modifiers"),
    [
        (EVENT_PATH, "TOP_incoming_actor", 5),
        (
            "events/Targeted Operations Redesign.txt",
            "TOP_incoming_liaison_actor",
            2,
        ),
    ],
)
def test_host_ai_opinion_modifiers_use_supported_country_scope(
    path, actor, expected_modifiers
):
    text = source(path)
    assert "has_opinion = { target = var:" not in text
    lines = [line for line in text.splitlines() if "has_opinion = {" in line]
    assert len(lines) == expected_modifiers
    assert f"limit = {{ check_variable = {{ {actor} > 0 }} }}" in text
    assert f"var:{actor} = {{ save_event_target_as = {actor}_target }}" in text
    for line in lines:
        assert f"has_opinion = {{ target = event_target:{actor}_target " in line
        assert "target = FROM " not in line
