import json
import re
from copy import deepcopy
from pathlib import Path

import pytest
from great_ai_race_state_model_test import (
    _extract_block,
    _named_block,
    _parse_race_script,
    _substitute_script_parameters,
)
from targeted_operations_helpers_test import TargetedScript

ROOT = Path(__file__).resolve().parents[2]
EFFECT_PATH = "common/scripted_effects/02_targeted_operations_authorization_effects.txt"
TRIGGER_PATH = (
    "common/scripted_triggers/02_targeted_operations_authorization_triggers.txt"
)
EVENT_PATH = "events/Targeted Operations.txt"


def source(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


class ReviewScript(TargetedScript):
    """Execute approval source with engine diplomacy and core eligibility as fixtures."""

    country_trigger_fields = {"has_political_power": "power"}

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
            TOP_refresh_view=[],
            TOP_enroll_pending_actor=[],
            TOP_initialize_global=[],
            TOP_country_initialize=[],
            TOP_build_view=[],
        )
        self.triggers = _parse_race_script(source(TRIGGER_PATH))
        core_triggers = _parse_race_script(
            source("common/scripted_triggers/01_targeted_operations_triggers.txt")
        )
        self.triggers.update(core_triggers)
        self.triggers.update(
            _parse_race_script(
                source("common/scripted_triggers/04_targeted_operations_cases.txt")
            )
        )
        self.countries = {
            country: {
                "vars": {},
                "exists": country > 0,
                "ai": False,
                "techs": {"special_forces_tech_1", "decryption1"},
                "power": 200,
                "authority": True,
                "enhanced": False,
                "opinion": {},
                "allies": set(),
                "wars": set(),
                "facilities": {1, 2, 3},
            }
            for country in (0, 1, 2, 3, 100)
        }
        self.countries[100]["controller"] = 2
        manifest = json.loads(source("tools/data/targeted_operations.json"))
        self.globals = {
            "TOP_clock": 7,
            "TOP_status^num": manifest["capacity"],
            "TOP_registry_capacity": manifest["capacity"],
        }
        self.temps, self.events, self.scope_stack = {}, [], []
        for target in (1, 2):
            self.globals[f"TOP_status^{target}"] = 1
            self.globals[f"TOP_political^{target}"] = 0
            self.globals[f"TOP_affiliation^{target}"] = target
            self.globals[f"TOP_state^{target}"] = 100
            self.globals[f"TOP_host^{target}"] = 2
            self.globals[f"TOP_group_ct^{target}"] = target - 1
        self.globals["active_terror_orgs"] = [0, 1]
        self.globals["TOP_active_targets"] = [1, 2]
        self.actor = self.countries[1]["vars"]
        self.actor.update(TOP_selected=1, TOP_selected_facility=1)
        self.actor["TOP_dossiers"] = [1, 2]
        self.actor["TOP_active_cases"] = []
        self.actor["TOP_retired_native_bindings"] = []
        for target in (1, 2):
            self.actor[f"TOP_known^{target}"] = 1
            self.actor[f"TOP_confidence^{target}"] = 95
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
        elif key == "TOP_exceptional_authority":
            result = country["authority"] == (operand == "yes")
        elif key == "TOP_facility_available":
            state = self.countries[self.temps["TOP_facility_state"]]
            result = (self.temps["TOP_facility_kind"] in state["facilities"]) == (
                operand == "yes"
            )
        elif key in {
            "western_conservatism_are_in_power",
            "western_liberals_are_in_power",
            "western_social_democrats_are_in_power",
        }:
            result = country["enhanced"] == (operand == "yes")
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
        operand = [(key, "=", str(value)) for key, value in parameters.items()]
        self.execute([(name, "=", operand or "yes")], identifier)

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


def test_identical_native_renewal_extends_the_same_prepared_case_binding():
    review = ReviewScript()
    review.approve_unilateral()
    original_until = review.actor["TOP_authorized_until"]
    original_sequence = review.case(1, "sequence")
    assert review.binding()
    review.globals["TOP_clock"] += 7
    review.approve_unilateral()
    assert review.actor["TOP_authorized_until"] == original_until + 7
    assert review.case(1, "sequence") == original_sequence
    assert review.actor["TOP_active_cases"] == [1]
    assert review.binding()
    assert review.countries[1]["power"] == 100


@pytest.mark.parametrize("changed", ("target", "method", "state"))
def test_explicit_replacement_cannot_accept_the_retired_native_callback(changed):
    review = ReviewScript()
    review.approve_unilateral()
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
    assert review.binding(target=1, method=2, state=100)
    assert review.binding(target=2, method=1, state=101)
    assert review.countries[1]["power"] == 100


def test_second_person_in_same_host_cannot_replace_an_active_approval():
    review = ReviewScript()
    review.approve_unilateral()
    sequence = review.case(1, "sequence")
    review.actor["TOP_selected"] = 2
    review.approve_unilateral()
    assert review.actor["TOP_active_cases"] == [1]
    assert review.case(1, "sequence") == sequence
    assert review.case(1, "phase") == 2
    assert review.case(2, "phase") == 0
    assert review.countries[1]["power"] == 150
    assert review.binding()


@pytest.mark.parametrize(
    "phase", [4, 5], ids=["assessment_pending", "confirmation_pending"]
)
def test_unconfirmed_assessment_blocks_that_host_but_allows_other_hosts(phase):
    review = ReviewScript()
    review.actor["TOP_case_phase^1"] = phase
    review.actor["TOP_selected"] = 2
    review.approve_unilateral()
    assert review.case(1, "phase") == phase
    assert review.case(2, "phase") == 0
    assert review.countries[1]["power"] == 200
    review.move_target(2, 101, 3)
    review.approve_unilateral()
    assert review.case(1, "phase") == phase
    assert review.case(2, "phase") == 2
    assert review.countries[1]["power"] == 150


def test_commit_rechecks_host_occupancy_after_staff_review():
    review = ReviewScript()
    review.ready_for_host()
    review.run("TOP_open_senior_review")
    review.run("TOP_close_review_event")
    review.actor["TOP_active_cases"].append(2)
    review.actor.update({"TOP_case_phase^2": 2, "TOP_case_host^2": 2})
    review.run("TOP_approve_review")
    assert review.case(1, "phase") == 1
    assert review.case(2, "phase") == 2
    assert review.countries[1]["power"] == 200


def test_closed_native_tuple_cannot_be_reused_even_by_a_fresh_review():
    review = ReviewScript()
    review.approve_unilateral()
    sequence = review.case(1, "sequence")
    review.call("TOP_close_case", TARGET=1, SEQUENCE=sequence)
    retired = list(review.actor["TOP_retired_native_bindings"])
    assert len(retired) == 1
    review.approve_unilateral()
    assert review.case(1, "phase") == 1
    assert review.case(1, "sequence") != sequence
    assert not review.binding()
    assert review.countries[1]["power"] == 150
    review.approve_unilateral(method=1)
    assert review.case(1, "phase") == 2
    assert review.binding(method=1)
    assert review.actor["TOP_retired_native_bindings"] == retired


def test_closing_the_case_during_review_invalidates_its_saved_sequence():
    review = ReviewScript()
    review.ready_for_host()
    review.run("TOP_open_senior_review")
    review.run("TOP_close_review_event")
    saved_sequence = review.actor["TOP_proposal_case_sequence"]
    review.call("TOP_close_case", TARGET=1, SEQUENCE=saved_sequence)
    review.run("TOP_designate_selected")
    assert review.case(1, "sequence") != saved_sequence
    review.run("TOP_approve_review")
    assert review.case(1, "phase") == 1
    assert review.countries[1]["power"] == 200


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


def test_returning_review_to_collection_pays_normal_cost_for_original_person():
    review = ReviewScript()
    review.call("TOP_begin_review", METHOD=2)
    review.actor["TOP_selected"] = 2
    text = source(EVENT_PATH)
    option_at = text.index("name = TOP_authorization.1.b")
    option = _extract_block(text, text.rfind("option = {", 0, option_at))
    effect = _parse_race_script(_named_block(option, "hidden_effect"))["hidden_effect"]
    review.execute(effect, 1)
    assert review.case(1, "collecting") == 1
    assert review.actor["TOP_proposal_stage"] == 0
    assert review.countries[1]["power"] == 175


def test_return_to_existing_collection_does_not_charge_twice():
    review = ReviewScript()
    review.call("TOP_begin_review", METHOD=2)
    review.actor["TOP_case_collecting^1"] = 1
    review.run("TOP_return_recorded_collection")
    assert review.case(1, "collecting") == 1
    assert review.countries[1]["power"] == 200


@pytest.mark.parametrize("recreate", [False, True], ids=["closed", "new_sequence"])
def test_stale_return_to_collection_cannot_charge_or_reopen_a_closed_case(recreate):
    review = ReviewScript()
    review.call("TOP_begin_review", METHOD=2)
    saved_sequence = review.case(1, "sequence")
    review.call("TOP_close_case", TARGET=1, SEQUENCE=saved_sequence)
    if recreate:
        review.run("TOP_designate_selected")
        assert review.case(1, "sequence") != saved_sequence
    review.run("TOP_return_recorded_collection")
    assert review.case(1, "phase") == int(recreate)
    assert review.case(1, "collecting") == 0
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


@pytest.mark.parametrize("method", (1, 2, 3, 4, 5, 6))
def test_all_methods_reach_review_with_required_capabilities(method):
    review = ReviewScript()
    review.call("TOP_begin_review", METHOD=method)
    assert review.actor["TOP_proposal_stage"] == 1
    assert review.condition(review.triggers["TOP_review_staff_ready"], 1)


@pytest.mark.parametrize(
    "method,tech",
    ((2, "special_forces_tech_1"), (4, "special_forces_tech_1"), (3, "decryption1")),
)
def test_missing_capability_cannot_bypass_review_backend(method, tech):
    review = ReviewScript()
    review.countries[1]["techs"].remove(tech)
    review.call("TOP_begin_review", METHOD=method)
    assert review.actor.get("TOP_proposal_stage", 0) == 0
    assert review.events == []


@pytest.mark.parametrize(
    "changed", ("controller", "state", "status", "authority", "funding", "confidence")
)
def test_changed_case_invalidates_senior_approval_without_spending(changed):
    review = ReviewScript()
    review.ready_for_host()
    review.run("TOP_open_senior_review")
    if changed == "controller":
        review.countries[100]["controller"] = 3
    elif changed == "state":
        review.actor["TOP_lead_state^1"] = 101
    elif changed == "status":
        review.globals["TOP_status^1"] = 2
    elif changed == "authority":
        review.countries[1]["authority"] = False
    elif changed == "funding":
        review.countries[1]["power"] = 49
    else:
        review.actor["TOP_confidence^1"] = 59
    power = review.countries[1]["power"]
    review.run("TOP_approve_review")
    assert review.countries[1]["power"] == power
    assert "TOP_authorized_target" not in review.actor


def test_enhanced_lethal_review_rejects_a_feasible_capture_alternative():
    review = ReviewScript()
    review.countries[1]["enhanced"] = True
    review.countries[2]["opinion"][1] = 75
    review.call("TOP_begin_review", METHOD=1)
    assert review.actor["TOP_proposal_capture_feasible"] == 1
    assert not review.condition(review.triggers["TOP_review_staff_ready"], 1)
    review.run("TOP_cancel_review")
    review.run("TOP_close_review_event")
    review.call("TOP_begin_review", METHOD=2)
    assert review.condition(review.triggers["TOP_review_staff_ready"], 1)


def test_political_target_uses_enhanced_review_even_for_standard_government():
    review = ReviewScript()
    review.globals["TOP_political^1"] = 1
    review.call("TOP_begin_review", METHOD=2)
    assert review.actor["TOP_proposal_rigor"] == 2
    review.actor["TOP_confidence^1"] = 75
    assert not review.condition(review.triggers["TOP_review_staff_ready"], 1)


def test_sabotage_keeps_facility_selection_fixed_and_rechecks_availability():
    review = ReviewScript()
    review.actor["TOP_selected_facility"] = 3
    review.ready_for_host(method=6)
    review.actor["TOP_selected_facility"] = 1
    review.run("TOP_open_senior_review")
    review.run("TOP_close_review_event")
    assert review.actor["TOP_proposal_facility"] == 3
    review.countries[100]["facilities"].remove(3)
    review.run("TOP_approve_review")
    assert "TOP_authorized_target" not in review.actor


def test_annual_opportunity_grants_once_and_report_acknowledgement_has_no_payload():
    review = ReviewScript()
    review.actor["TOP_confidence^1"] = 40
    review.actor["TOP_confidence^2"] = 10
    review.run("TOP_modern_opportunities_2024")
    review.run("TOP_modern_country_opportunity")
    assert review.actor["TOP_confidence^1"] == 65
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
    review.actor["TOP_confidence^1"] = 20
    review.actor["TOP_confidence^2"] = 40
    review.globals["active_terror_org_threat_lvl^0"] = 60
    review.run("TOP_modern_opportunities_2024")
    review.run("TOP_modern_country_opportunity")
    assert review.actor["TOP_modern_2024_target"] == 1
    review.actor["TOP_confidence^2"] = 90
    review.globals["active_terror_org_threat_lvl^0"] = 0
    review.run("TOP_modern_opportunities_2025")
    review.run("TOP_modern_country_opportunity")
    assert review.actor["TOP_modern_2024_target"] == 1
    assert review.actor["TOP_modern_2025_target"] == 2


def test_modern_annual_marker_never_moves_backwards_and_ai_needs_no_popup():
    review = ReviewScript()
    review.countries[1]["ai"] = True
    review.actor["TOP_confidence^1"] = 40
    review.actor["TOP_confidence^2"] = 10
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


def test_snapshot_identity_and_host_slot_have_single_writers():
    effects = _parse_race_script(source(EFFECT_PATH))
    for name, body in effects.items():
        rendered = repr(body)
        if name != "TOP_begin_review":
            for field in ("target", "method", "state", "host", "sequence"):
                assert not re.search(
                    rf"'set_variable'.*?\[\('TOP_proposal_{field}'", rendered
                )
        if name not in {"TOP_send_host_request", "TOP_answer_host_request"}:
            assert "TOP_incoming_actor" not in rendered
    assert "TOP_selected" not in _named_block(source(EFFECT_PATH), "TOP_approve_review")
    assert "TOP_selected" not in _named_block(source(TRIGGER_PATH), "TOP_review_valid")
