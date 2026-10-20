"""Execute native agency callbacks and the complete shared raid reaction relay."""

from copy import deepcopy
import re

import pytest

from targeted_operations_core_integration_test import CoreIntegrationScript
from targeted_operations_model_test import _named_block, _parse_race_script
from targeted_operations_redesign_test import block, read

METHODS = {3: "covert_killing", 4: "rendition", 5: "host_arrest", 7: "poisoning"}


class AgencyScript(CoreIntegrationScript):
    def __init__(self):
        super().__init__()
        self.effects.update(
            _parse_race_script(
                read("common/scripted_effects/12_targeted_operations_agency.txt")
            )
        )
        self.triggers.update(
            _parse_race_script(
                read("common/scripted_triggers/09_targeted_operations_agency.txt")
            )
        )
        self.globals["num_days"] = 0
        self.operation_type = ""
        self.running = set()
        self.actor = 1

    def condition_statement(self, statement, identifier):
        key, _, operand = statement
        if key == "ROOT":
            return self.scoped(operand, identifier, self.actor, condition=True)
        if key == "is_operation_type":
            return self.operation_type == operand
        if key == "is_running_operation":
            data = dict((key, value) for key, _, value in operand)
            return (self.from_country, data["operation"]) in self.running
        return super().condition_statement(statement, identifier)

    def execute_statement(self, statement, identifier):
        if statement[0] == "ROOT":
            self.scoped(statement[2], identifier, self.actor)
        else:
            super().execute_statement(statement, identifier)

    def operation(self, method):
        source = read("common/operations/02_targeted_operations.txt")
        source = re.sub(r"(?:risk|outcome|cost)_modifiers\s*=\s*\{[^}]*\}", "", source)
        return _parse_race_script(source)["operation_top_" + METHODS[method]]

    def callback(self, method, key):
        operation = self.operation(method)
        self.execute(next(value for name, _, value in operation if name == key), 1)

    def complete(self, method):
        self.operation_type = "operation_top_" + METHODS[method]
        source = _named_block(
            read("common/on_actions/05_lar_on_actions.txt"), "on_operation_completed"
        )
        dispatch = (
            "dispatch = {"
            + "\n".join(
                line
                for line in source.splitlines()
                if "is_operation_type = operation_top_" in line
            )
            + "}"
        )
        self.execute(_parse_race_script(dispatch)["dispatch"], 1)


@pytest.mark.parametrize("method", METHODS)
@pytest.mark.parametrize("bonus_first", [False, True])
@pytest.mark.parametrize("bonus", [False, True])
def test_agency_callbacks_commit_one_native_outcome_and_keep_distinct_custody(
    method, bonus_first, bonus
):
    script = AgencyScript()
    if method == 7:
        script.countries[1]["tag"] = "SOV"
    variables = script.authorize(method=method)
    script.callback(method, "on_start")
    script.countries[1]["vars"]["TOP_selected"] = 12
    callbacks = ["outcome_execute"] + (["outcome_extra_execute"] if bonus else [])
    if bonus_first:
        callbacks.reverse()
    for callback in callbacks:
        script.callback(method, callback)
    assert script.globals["TOP_status"][11] == 1
    script.complete(method)
    expected = (2 if method in (4, 5) else 3) if bonus else 1
    assert script.globals["TOP_status"][11] == expected
    assert variables["TOP_case_result"][11] == (expected if bonus else 8)
    if bonus and method in (4, 5):
        assert script.globals["TOP_custodian"][11] == (2 if method == 5 else 1)
    assert variables["TOP_case_native_prepared"][11] == 0
    before = deepcopy(script.globals)
    script.complete(method)
    assert script.globals == before


@pytest.mark.parametrize(
    "change",
    [
        "disabled",
        "sequence",
        "person",
        "state",
        "host",
        "role",
        "legacy",
        "consent",
        "stand_down",
    ],
)
def test_agency_stale_completion_cannot_bind_a_new_or_invalid_case(change):
    script = AgencyScript()
    variables = script.authorize(method=5)
    script.callback(5, "on_start")
    script.callback(5, "outcome_execute")
    script.callback(5, "outcome_extra_execute")
    if change == "disabled":
        script.globals["TOP_rule_mode"] = 0
    elif change == "sequence":
        variables["TOP_case_sequence"][11] += 1
    elif change == "person":
        script.call("TOP_close_case", 1, TARGET=11, SEQUENCE=11)
        script.authorize(target=12, method=5)
    elif change == "state":
        variables["TOP_case_state"][11] = 102
    elif change == "host":
        script.from_country = 3
    elif change == "role":
        script.ineligible_roles.add(11)
    elif change == "legacy":
        script.temps.update(TOP_target=11, TOP_result=3)
        script.run("TOP_record_legacy_result", 1)
    elif change == "consent":
        variables["TOP_case_consent"][11] = 0
    else:
        variables["TOP_case_phase"][11] = 2
    before = deepcopy(script.globals)
    script.complete(5)
    assert script.globals["TOP_status"] == before["TOP_status"]
    assert script.globals["TOP_removals"] == before["TOP_removals"]
    if change in ("sequence", "person"):
        assert variables["TOP_case_phase"][12 if change == "person" else 11] == 3


@pytest.mark.parametrize("method", METHODS)
def test_agency_operation_uses_native_commitment_and_original_foreign_access(method):
    script = AgencyScript()
    if method == 7:
        script.countries[1]["tag"] = "SOV"
    script.authorize(method=method)
    operation = dict((key, value) for key, _, value in script.operation(method))
    assert script.condition(operation["available"], 1)
    script.running.add((2, "operation_top_" + METHODS[method]))
    assert not script.condition(operation["available"], 1)
    assert float(operation["operatives"]) >= 1
    assert float(operation["days"]) > 0
    assert float(operation["risk_chance"]) > 0
    assert operation["outcome_extra_chance"] == "0.65"
    text = _named_block(
        read("common/operations/02_targeted_operations.txt"),
        "operation_top_" + METHODS[method],
    )
    assert "operation_infiltrate_risk operation_risk" in text
    assert "operation_infiltrate_outcome operation_outcome" in text
    assert not any(
        term in text
        for term in (
            "Special_Forces",
            "raid_can_launch",
            "command_power",
            "TOP_clock",
            "random",
        )
    )
    script.running.clear()
    script.from_country = 1
    variables = script.countries[1]["vars"]
    variables["TOP_case_host"][11] = 1
    script.countries[101]["controller"] = 1
    assert not script.condition(operation["available"], 1)


class ReactionScript(AgencyScript):
    """Run the actual helper, .8/.9 relay and .1 eligibility, preserving event scopes."""

    def __init__(self):
        super().__init__()
        self.effects.update(
            _parse_race_script(
                _named_block(
                    read("common/scripted_effects/00_raid_scripted_effects.txt"),
                    "send_raid_event_to_victim",
                )
            )
        )
        self.effects.update(
            _parse_race_script(
                _named_block(
                    read("common/scripted_effects/00_raid_scripted_effects.txt"),
                    "send_events_to_others",
                )
            )
        )
        self.event_sources = {}
        for match in re.finditer(r"(?m)^country_event = \{", read("events/raids.txt")):
            source = _named_block(
                read("events/raids.txt")[match.start() :], "country_event"
            )
            event = _parse_race_script(source)["country_event"]
            ident = next(value for key, _, value in event if key == "id")
            self.event_sources[ident] = event
        self.relay = []
        self.delivered = []
        self.event_from = 1
        self.event_root = 1
        self.allied = False
        self.retaliate = False

    def _scope(self, name, identifier):
        if name.startswith("THIS."):
            return super()._scope(name[5:], identifier)
        if name.startswith("ROOT."):
            return super()._scope(name[5:], self.event_root)
        if name.startswith("FROM."):
            return super()._scope(name[5:], self.event_from)
        return super()._scope(name, identifier)

    def value(self, name, identifier):
        if name == "FROM":
            return self.event_from
        return super().value(name, identifier)

    def condition_statement(self, statement, identifier):
        key, _, operand = statement
        if key == "FROM":
            return self.scoped(operand, identifier, self.event_from, condition=True)
        if key == "ROOT":
            return self.scoped(operand, identifier, self.event_root, condition=True)
        if key in {"tag", "original_tag"} and operand in {"ROOT", "FROM"}:
            target = self.event_root if operand == "ROOT" else self.event_from
            return self.countries[identifier]["tag"] == self.countries[target]["tag"]
        if key == "is_ally_with":
            return self.allied
        return super().condition_statement(statement, identifier)

    def execute_statement(self, statement, identifier):
        key, _, operand = statement
        if key == "PREV":
            self.scoped(operand, identifier, self.scope_stack[-1])
        elif key == "country_event":
            event_id = (
                dict((key, value) for key, _, value in operand)["id"]
                if isinstance(operand, list)
                else operand
            )
            if not event_id.startswith("MD_raid."):
                self.external[event_id, identifier] += 1
                return
            self.relay.append((event_id, identifier, self.event_root))
        elif key == "FROM":
            self.scoped(operand, identifier, self.event_from)
        elif key in {
            "create_wargoal",
            "news_event",
            "add_war_support",
            "add_threat_from_wargoal_effect",
        }:
            self.external[key, identifier] += 1
        elif key == "log":
            pass
        else:
            super().execute_statement(statement, identifier)

    def flush(self):
        while self.relay:
            event_id, target, sender = self.relay.pop(0)
            self.event_from, self.event_root = sender, target
            event = self.event_sources[event_id]
            trigger = next((value for key, _, value in event if key == "trigger"), [])
            if not self.condition(trigger, target):
                continue
            self.delivered.append(event_id)
            immediate = next(
                (value for key, _, value in event if key == "immediate"), []
            )
            self.execute(immediate, target)
            if self.retaliate and event_id == "MD_raid.1":
                option = next(
                    value
                    for key, _, value in event
                    if key == "option" and ("name", "=", "MD_raid.1.a") in value
                )
                trigger = next(value for key, _, value in option if key == "trigger")
                assert self.condition(trigger, target)
                self.execute(
                    [
                        entry
                        for entry in option
                        if entry[0] not in {"name", "trigger", "ai_chance"}
                    ],
                    target,
                )


@pytest.mark.parametrize("consent", [0, 1])
@pytest.mark.parametrize("attribution", [0, 1, 2, 3])
@pytest.mark.parametrize("applied", [0, 1])
def test_top_reaction_complete_chain_rejects_consent_hidden_or_stale_callbacks(
    consent, attribution, applied
):
    script = ReactionScript()
    variables = script.authorize(method=2)
    variables.update(actor_country=1, victim_country=2)
    variables["TOP_case_consent"][11] = consent
    variables["TOP_case_attribution"][11] = attribution
    script.temps.update(
        actor_country=1,
        TOP_target=11,
        top_native_result_applied=applied,
        top_native_reaction_consent=consent,
        top_native_reaction_attribution=attribution,
    )
    script.run("top_native_person_reaction", 1)
    script.flush()
    expected = (
        ["MD_raid.8", "MD_raid.9", "MD_raid.1"]
        if applied and not consent and attribution >= 2
        else []
    )
    assert script.delivered == expected


@pytest.mark.parametrize("condition", ["ordinary", "war", "allied", "blocked", "own"])
def test_unrelated_core_raid_reaction_retains_the_entire_existing_chain(condition):
    script = ReactionScript()
    variables = script.countries[1]["vars"]
    variables.update(actor_country=1, victim_country=2)
    script.temps.update(actor_country=1, victim_country=2)
    if condition == "war":
        script.countries[1]["has_war_with"] = {2}
    elif condition == "allied":
        script.allied = True
    elif condition == "blocked":
        script.countries[2]["flags"]["block_raid_events"] = 1
    elif condition == "own":
        script.countries[2]["tag"] = "USA"
    script.run("send_raid_event_to_victim", 1)
    script.flush()
    expected = [] if condition == "war" else ["MD_raid.8", "MD_raid.9"]
    if condition == "ordinary":
        expected.append("MD_raid.1")
    assert script.delivered == expected


def test_military_delivery_is_public_but_agency_delivery_keeps_attribution_roll():
    for method in (1, 2, 3, 4, 5, 7):
        script = AgencyScript()
        if method == 7:
            script.countries[1]["tag"] = "SOV"
        variables = script.authorize(method=method)
        variables["TOP_case_exposure_score"][11] = 0
        script.temps.update(TOP_target=11, TOP_method=method)
        script.run("TOP_calculate_person_consequences", 1)
        assert variables["TOP_case_attribution"][11] == (3 if method < 3 else 0)


@pytest.mark.parametrize("consent", [0, 1])
def test_top_victim_retaliation_and_faction_neighbor_notifications_follow_consent(
    consent,
):
    script = ReactionScript()
    variables = script.authorize(method=2)
    variables.update(actor_country=1, victim_country=2)
    variables["TOP_case_consent"][11] = consent
    variables["TOP_case_attribution"][11] = 3
    script.countries[2]["vars"].update(faction_members=[2, 3], neighbors=[4])
    script.temps.update(
        actor_country=1,
        TOP_target=11,
        top_native_result_applied=1,
        top_native_reaction_consent=consent,
        top_native_reaction_attribution=3,
    )
    script.retaliate = True
    script.run("top_native_person_reaction", 1)
    script.flush()
    assert script.external["create_wargoal", 2] == (0 if consent else 1)
    assert script.external["news_event", 2] == (0 if consent else 1)
    assert script.delivered == (
        []
        if consent
        else [
            "MD_raid.8",
            "MD_raid.9",
            "MD_raid.1",
            "MD_raid.15",
            "MD_raid.12",
            "MD_raid.10",
        ]
    )


@pytest.mark.parametrize("method", METHODS)
def test_agency_visit_action_duration_leaves_room_in_existing_execution_window(method):
    script = AgencyScript()
    operation = dict((key, value) for key, _, value in script.operation(method))
    setup = _named_block(
        read("common/scripted_effects/05_targeted_operations_runtime.txt"),
        "TOP_setup_extended_runtime",
    )
    window = int(re.search(r"global.TOP_visit_execution_days = (\d+)", setup)[1])
    assert int(operation["days"]) < window
    phases = read("common/operation_phases/targeted_operations.txt")
    placement = _named_block(phases, "top_agency_placement")
    assert "days = 2" in placement
    assert "Special_Forces" not in phases


@pytest.mark.parametrize(
    "consent,protection,expected", [(0, 2, True), (1, 2, False), (1, 3, True)]
)
def test_top_sovereignty_and_crisis_respect_consent_without_silencing_a_foreign_sponsor(
    consent, protection, expected
):
    script = AgencyScript()
    variables = script.authorize(method=5)
    variables["TOP_case_consent"][11] = consent
    variables["TOP_case_protection"][11] = protection
    variables["TOP_case_attribution"][11] = 3
    script.globals["TOP_leader_role"][11] = 1
    script.globals["TOP_status"][11] = 2
    script.temps.update(
        TOP_target=11,
        TOP_result=2,
        TOP_exposure_recorded=1,
        TOP_strategic_crisis_candidate=1,
        TOP_operation_protection_country=protection,
    )
    variables.update(TOP_authorized_consent=consent, TOP_authorized_host=2)
    assert (
        script.condition(script.triggers["TOP_exposed_visit_kill_valid"], 1) == expected
    )
    script.run("TOP_apply_shared_consequences", 1)
    assert script.external["add_opinion_modifier", protection] == int(expected)


@pytest.mark.parametrize("wrong_location", [False, True])
@pytest.mark.parametrize("consent", [0, 1])
def test_generated_actor_result_and_reaction_keep_frozen_permission_after_case_closure(
    wrong_location, consent
):
    script = ReactionScript()
    variables = script.authorize(method=2)
    variables.update(actor_country=1, victim_country=2, target_state=101)
    variables["TOP_case_consent"][11] = consent
    if wrong_location:
        script.globals["TOP_state"][11] = 102
    script.stubs.add("apply_discounted_raid_pp_cost")
    source = _named_block(
        read("common/raids/targeted_operations_raids.txt"), "TOP_capture_11"
    )
    success = _named_block(_named_block(source, "success_levels"), "success")
    actor = _parse_race_script(_named_block(success, "actor_effects"))["actor_effects"]
    script.stubs.add("raid_damage_units")
    script.execute(actor, 1)
    script.flush()
    assert script.delivered == (
        [] if consent else ["MD_raid.8", "MD_raid.9", "MD_raid.1"]
    )
    assert script.globals["TOP_status"][11] == (1 if wrong_location else 2)
