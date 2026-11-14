import re
from collections import Counter
from copy import deepcopy

import pytest
from targeted_operations_core_test import ROOT, ScriptArray, TargetScript
from targeted_operations_helpers import _named_block, _parse_race_script, block, read


class CoreIntegrationScript(TargetScript):
    """Model the operation's FROM country; core intelligence is an input fixture."""

    from_country = 2

    def __init__(self):
        super().__init__()
        self.globals["active_terror_hq"] = ScriptArray([101, 102])
        self.globals["active_terror_hq_country"] = ScriptArray([2, 3])

    def value(self, name, identifier):
        if isinstance(name, str) and name in {"FROM", "FROM.id"}:
            return self.from_country
        return super().value(name, identifier)

    def condition_statement(self, statement, identifier):
        if statement[0] == "has_target_in_region_intel":
            return bool(self.value("ct_tracking_available", identifier))
        if statement[0] == "has_state_flag":
            return statement[2] in self.countries[identifier].get("flags", {})
        return super().condition_statement(statement, identifier)

    def execute_statement(self, statement, identifier):
        if statement[0] == "FROM":
            self.scoped(statement[2], identifier, self.from_country)
        elif statement[0] == "army_experience":
            self.external["army_experience", identifier] += self.value(
                statement[2], identifier
            )
        elif statement[0] == "raid_add_unit_experience":
            self.external["raid_add_unit_experience", identifier] += self.value(
                statement[2], identifier
            )
        elif statement[0] == "every_state":
            for target, country in list(self.countries.items()):
                if country["tag"].startswith("state_"):
                    data = {key: value for key, _, value in statement[2]}
                    if self.scoped(data["limit"], identifier, target, condition=True):
                        self.scoped(
                            [item for item in statement[2] if item[0] != "limit"],
                            identifier,
                            target,
                        )
        else:
            super().execute_statement(statement, identifier)


@pytest.mark.parametrize("method", [1, 2])
@pytest.mark.parametrize("tier,expected", [(0, 9), (1, 8), (2, None), (3, None)])
def test_native_tier_owns_physical_result_without_a_second_roll(method, tier, expected):
    script = CoreIntegrationScript()
    if method == 7:
        script.countries[1]["tag"] = "SOV"
    variables = script.authorize(method=method)
    for axis in ("identity", "location", "pattern"):
        variables[f"TOP_case_{axis}"][11] = 0
    script.temps.update(TOP_tier=tier)

    script.run("TOP_resolve_native_callback", 1)

    expected = expected if expected is not None else (2 if method in (2, 4, 5) else 3)
    assert variables["TOP_case_result"][11] == expected
    assert script.globals["TOP_status"][11] == (expected if expected in (2, 3) else 1)
    assert variables["TOP_case_native_prepared"][11] == 0


def test_capture_critical_success_keeps_custody_and_removes_office_once():
    script = CoreIntegrationScript()
    variables = script.authorize(target=1, method=2)
    script.globals["TOP_office"][1] = 1
    script.globals["TOP_group_leader"][1] = 1
    script.temps["TOP_tier"] = 3
    script.run("TOP_resolve_native_callback", 1)
    status = deepcopy(script.globals)

    script.run("TOP_native_result_args", 1)

    assert script.globals["TOP_status"][1] == 2
    assert script.globals["TOP_custodian"][1] == 1
    assert script.globals["TOP_removals"][1] == 1
    assert script.globals["TOP_group_leader"] == status["TOP_group_leader"]
    assert variables["TOP_case_phase"][1] == 5


def test_legacy_first_invalidates_both_actors_and_stale_native_callback():
    script = CoreIntegrationScript()
    first = script.authorize(target=1, method=1, actor=1)
    second = script.authorize(target=1, method=2, actor=3)
    script.run("TOP_enroll_pending_actor", 3)
    before_power = first["political_power"]
    script.temps.update(TOP_target=1, TOP_result=3)

    script.run("TOP_record_legacy_result", 1)
    after = deepcopy(script.globals)
    script.temps.update(TOP_target=1, TOP_method=2, TOP_tier=3, target_state=101)
    script.countries[3]["vars"]["actor_country"] = 3
    script.run("TOP_native_result_args", 3)

    assert script.globals["TOP_status"][1] == 3
    assert script.globals["TOP_removals"][1] == 1
    assert first["political_power"] == before_power
    assert first["TOP_case_phase"][1] == second["TOP_case_phase"][1] == 0
    assert script.globals["TOP_custody_counter"] == after["TOP_custody_counter"]
    assert script.external["TOP_apply_legacy_outcome", 1] == 0


@pytest.mark.parametrize("legacy_first", [True, False])
def test_legacy_and_top_removal_share_one_retirement_and_successor(legacy_first):
    script = CoreIntegrationScript()
    script.target(1)
    script.globals["TOP_office"][1] = 1
    script.globals["TOP_group_leader"][1] = 1
    script.temps.update(TOP_target=1, TOP_result=3)
    commands = ["TOP_record_legacy_result", "TOP_kill_target"]
    if not legacy_first:
        commands.reverse()
    for command in commands:
        script.temps.update(TOP_arg_target=1, TOP_target=1, TOP_result=3)
        script.run(command, 1)
    assert script.globals["TOP_removals"][1] == 1
    assert script.external["TOP_retire_registered_character", 1] == 1


def test_top_disabled_observers_leave_core_state_untouched():
    script = CoreIntegrationScript()
    script.globals["TOP_rule_mode"] = 0
    snapshot = deepcopy((script.countries, script.globals))
    script.temps.update(TOP_target=1, TOP_result=3)
    script.run("TOP_record_legacy_result", 1)
    script.run("TOP_core_raid_result", 1)
    assert (script.countries, script.globals) == snapshot


def test_collection_reads_current_ct_slot_and_cannot_invent_location():
    script = CoreIntegrationScript()
    variables = script.target(1)
    script.globals["TOP_group_ct"][1] = 10
    variables["international_terror_org_intel"] = ScriptArray([23, 74])
    variables["TOP_location_confidence"][1] = 0
    variables["TOP_identity_confidence"][1] = 0
    variables["TOP_pattern_confidence"][1] = 0
    script.temps["TOP_target"] = 1

    script.run("TOP_collect_person_pulse", 1)

    assert variables["TOP_identity_confidence"][1] == 74
    assert variables["TOP_pattern_confidence"][1] == 74
    assert variables["TOP_location_confidence"][1] == 0


def test_native_tracking_binds_start_target_and_org_across_reselection():
    script = CoreIntegrationScript()
    variables = script.target(1)
    variables["selected_org"] = 1
    variables["ct_tracking_available"] = 1
    script.temps["TOP_tracking_kind"] = 0
    script.run("TOP_tracking_started", 1)
    script.target(2, host=3, state=102)
    variables["selected_org"] = 0
    script.run("TOP_tracking_completed", 1)
    assert variables["TOP_location_confidence"][1] == 100
    assert variables["TOP_location_confidence"][2] == 85
    assert variables["TOP_tracking_person"][2] == 0


def test_native_locate_operations_have_independent_identity_snapshots():
    script = CoreIntegrationScript()
    variables = script.target(1)
    variables["selected_org"] = 1
    for kind, name in [(1, "hq"), (2, "training"), (3, "cache")]:
        script.temps["TOP_tracking_kind"] = kind
        script.run("TOP_tracking_started", 1)
        assert variables[f"TOP_locate_{name}_org"][2] == 10
    assert variables["TOP_tracking_person"][2] == 0


def test_person_and_organization_execution_have_no_timer_or_parallel_resolution():
    person = read("common/scripted_effects/04_targeted_operations_cases.txt")
    org = read("common/scripted_effects/04_targeted_operations_cases.txt")
    resolution = read("common/scripted_effects/04_targeted_operations_cases.txt")
    assert "TOP_resolve_timed_case" not in person
    assert "TOP_roll_timed_tactical_result" not in resolution
    for source in (person, org):
        assert "global.TOP_clock add = 28" not in source
    for name in (
        "TOP_damage_organization_facility",
        "TOP_apply_organization_disruption",
    ):
        assert name not in org
    native = block(
        "common/scripted_effects/04_targeted_operations_cases.txt",
        "TOP_resolve_person_operation",
    )
    assert "TOP_intelligence_roll" not in native


def test_all_generated_raids_share_core_eligibility_cost_losses_and_victim_reactions():
    raids = read("common/raids/targeted_operations_raids.txt")
    names = re.findall(r"(?m)^\s*(TOP_(?:drone|capture)_\d+)\s*=\s*\{", raids)
    assert names
    for name in names:
        raid = _named_block(raids, name)
        assert raid.count("raid_available_base = yes") == 1, name
        assert raid.count("raid_can_launch = yes") == 1, name
        assert raid.count("top_native_person_reaction = yes") == 4, name
        assert "victim_effects = { send_raid_event_to_victim" not in raid
        assert raid.count("apply_raid_failure_losses = yes") == int(
            name.startswith("TOP_drone_")
        ), name
        assert raid.count("raid_damage_units = { org_damage") == (
            4 if name.startswith("TOP_capture_") else 0
        ), name


def iraq_script():
    script = CoreIntegrationScript()
    legacy = read("common/scripted_effects/01_targeted_operations_legacy_effects.txt")
    for name in ("TOP_apply_legacy_outcome", "TOP_update_iraq_progress"):
        script.effects[name] = _parse_race_script(_named_block(legacy, name))[name]
        script.stubs.remove(name)
    return script


@pytest.mark.parametrize("top_first", [False, True])
def test_iraq_legacy_capture_and_top_capture_grant_one_reward_and_custody(top_first):
    script = iraq_script()
    script.target(56)
    event = read("events/Middle East Peace Plan.txt")
    event = event[event.index("id = iraqi_MNF.10\n") :]
    option = _parse_race_script(_named_block(event, "option"))["option"]
    script.temps["TOP_arg_target"] = 56
    if top_first:
        script.run("TOP_capture_target", 1)
    script.execute([item for item in option if item[0] not in {"name", "ai_chance"}], 1)
    if not top_first:
        script.temps["TOP_arg_target"] = 56
        script.run("TOP_capture_target", 1)
    assert script.globals["TOP_status"][56] == 2
    assert script.globals["TOP_custodian"][56] == 1
    assert script.globals["TOP_removals"][56] == 1
    assert script.external["army_experience", 1] == 100
    assert script.countries[1]["vars"]["IRQ_baathist_dead"] == 1


def test_top_observer_does_not_consume_the_core_raid_identity():
    script = CoreIntegrationScript()
    script.effects["TOP_record_core_raid"] = []
    source = read("common/scripted_effects/00_ct_effects.txt")
    script.effects["ct_resolve_raid_org"] = _parse_race_script(
        _named_block(source, "ct_resolve_raid_org")
    )["ct_resolve_raid_org"]
    script.countries[101]["vars"]["target_raid_org_id"] = 10
    script.countries[1]["vars"]["actor_country"] = 1
    script.countries[1]["vars"]["target_state"] = 101
    script.temps["TOP_core_objective"] = 0

    script.run("TOP_core_raid_result", 1)
    assert script.countries[101]["vars"]["target_raid_org_id"] == 10
    script.run("ct_resolve_raid_org", 101)

    assert script.temps["targeted_org"] == 1
    assert "target_raid_org_id" not in script.countries[101]["vars"]


def test_organization_case_records_native_result_without_own_damage_or_threat_roll():
    script = CoreIntegrationScript()
    script.countries[2]["flags"]["ct_elim_raid_prepared_by@ROOT"] = None
    variables = script.authorize_organization(group=1, host=2, state=101)
    assert variables["TOP_org_case_phase"][1] == 3
    assert variables["TOP_org_case_due"][1] == 0
    script.temps.update(
        TOP_core_org=0,
        TOP_core_objective=1,
        TOP_core_host=2,
        TOP_core_state=101,
        TOP_tier=2,
    )
    threat = deepcopy(script.globals["active_terror_org_threat_lvl"])
    draws = script.random_draws

    script.run("TOP_record_core_raid", 1)
    rows = deepcopy(variables["TOP_archive_rows"])
    script.run("TOP_record_core_raid", 1)

    assert variables["TOP_org_case_result"][1] == 11
    assert variables["TOP_org_case_phase"][1] == 5
    assert variables["TOP_operation_subject_kind"] == 0
    assert script.globals["active_terror_org_threat_lvl"] == threat
    assert script.random_draws == draws + 2
    assert variables["TOP_archive_rows"] == rows
    assert not any(name == "damage_building" for name, _actor in script.external)


def test_closed_organization_binding_cannot_accept_old_native_result_in_a_new_case():
    script = CoreIntegrationScript()
    script.countries[2]["flags"]["ct_elim_raid_prepared_by@ROOT"] = None
    variables = script.authorize_organization(group=1, host=2, state=101)
    script.temps.update(TOP_arg_group=1, TOP_arg_sequence=1)
    script.run("TOP_close_organization_case", 1)
    script.authorize_organization(group=1, host=2, state=101)
    script.temps.update(
        TOP_core_org=0,
        TOP_core_objective=1,
        TOP_core_host=2,
        TOP_core_state=101,
        TOP_tier=3,
    )
    script.run("TOP_record_core_raid", 1)
    assert variables["TOP_org_case_phase"][1] == 2
    assert variables["TOP_org_case_result"][1] == 0


@pytest.mark.parametrize("enabled", [False, True])
@pytest.mark.parametrize("raid_kind", ["hvt", "cache", "training_camp"])
@pytest.mark.parametrize(
    "tier,outcome",
    list(enumerate(["failure", "limited_success", "success", "critical_success"])),
)
def test_existing_ct_hvt_native_outcome_keeps_its_core_intel_threat_and_identity(
    enabled,
    raid_kind,
    tier,
    outcome,
):
    script = CoreIntegrationScript()
    script.target(1)
    script.globals["TOP_rule_mode"] = int(enabled)
    script.globals["TOP_group_leader"][1] = 1
    script.globals["active_terror_orgs"] = ScriptArray([10, 0])
    script.globals["active_terror_org_threat_lvl"] = ScriptArray([40, 50])
    script.globals["active_terror_org_vis_lvl"] = ScriptArray([20, 20])
    script.countries[101]["vars"]["target_raid_org_id"] = 0
    variables = script.countries[1]["vars"]
    variables["actor_country"] = 1
    variables["target_state"] = 101
    variables["international_terror_org_temp_specific_intel"] = ScriptArray([0, 0])
    script.stubs.add("international_systems_update")
    core = read("common/scripted_effects/00_ct_effects.txt")
    script.effects["ct_resolve_raid_org"] = _parse_race_script(
        _named_block(core, "ct_resolve_raid_org")
    )["ct_resolve_raid_org"]
    raid = _named_block(
        read("common/raids/special_forces_raids.txt"),
        f"counter_terror_{raid_kind}_raid",
    )
    levels = _named_block(raid, "success_levels")
    success = _named_block(levels, outcome)
    actor = _parse_race_script(_named_block(success, "actor_effects"))["actor_effects"]

    script.execute(actor, 1)

    assert script.globals["active_terror_org_threat_lvl"] == [
        40,
        (51, 45, 40, 35)[tier],
    ]
    assert variables["international_terror_org_temp_specific_intel"] == [
        0,
        (0, 1, 1, 5)[tier],
    ]
    assert script.external["raid_add_unit_experience", 1] == 0.25
    assert "target_raid_org_id" not in script.countries[101]["vars"]
    assert script.globals["TOP_status"][1] == (
        3 if enabled and raid_kind == "hvt" and tier > 1 else 1
    )


def test_delayed_iraq_execution_cannot_count_an_already_dead_person_twice():
    script = iraq_script()
    script.target(56)
    script.temps["TOP_arg_target"] = 56
    script.run("TOP_capture_target", 1)
    script.temps["TOP_arg_target"] = 56
    script.run("TOP_kill_target", 1)
    effect = _parse_race_script(
        _named_block(read("common/decisions/USA.txt"), "USA_execute_saddam")
    )["USA_execute_saddam"]
    remove = next(value for key, _, value in effect if key == "remove_effect")
    before = deepcopy(script.globals)
    script.execute(remove, 1)
    assert script.globals == before
    assert script.countries[1]["vars"]["IRQ_baathist_dead"] == 1


@pytest.mark.parametrize("objective", [1, 2, 3])
@pytest.mark.parametrize("tier,expected", [(0, 9), (1, 8), (2, 11), (3, 11)])
def test_extended_facility_objectives_follow_native_tiers_and_keep_people(
    objective, tier, expected
):
    script = CoreIntegrationScript()
    variables = script.authorize_organization(
        group=12, objective=objective, host=2, state=101
    )
    assert variables["TOP_org_case_phase"][12] == 3
    people = deepcopy(script.globals["TOP_status"])
    script.facility_callback(tier=tier)
    assert variables["TOP_org_case_result"][12] == expected
    assert script.external["damage_building", 101] == int(tier > 1)
    assert script.globals["TOP_group_disruption_type"][12] == (
        objective if tier > 1 else 0
    )
    assert script.globals["TOP_status"] == people
    assert variables["TOP_org_case_due"][12] == 0


def test_partner_capture_preserves_host_custody_and_consent_gate():
    from targeted_operations_core_integration_test import AgencyScript

    script = AgencyScript()
    variables = script.authorize(method=5)
    script.triggers["raid_show_target_intervention_check"] = []
    script.temps.update(top_agency_method=5)
    assert script.condition(script.triggers["top_agency_case_ready"], 1)
    variables["TOP_case_consent"][11] = 0
    assert not script.condition(script.triggers["top_agency_case_ready"], 1)
    variables["TOP_case_consent"][11] = 1
    script.callback(5, "on_start")
    script.callback(5, "outcome_execute")
    script.callback(5, "outcome_extra_execute")
    script.complete(5)
    assert script.globals["TOP_status"][11] == 2
    assert script.globals["TOP_custodian"][11] == 2
    assert script.globals["TOP_removals"][11] == 1


@pytest.mark.parametrize("method", [2, 4, 5, 3, 7])
def test_wrong_native_family_cannot_cancel_or_resolve_a_prepared_case(method):
    script = CoreIntegrationScript()
    if method == 7:
        script.countries[1]["tag"] = "SOV"
    variables = script.authorize(method=method)
    script.countries[1]["vars"].update(actor_country=1, target_state=101)
    script.temps.update(TOP_target=11, TOP_method=method, TOP_native_kind=1, TOP_tier=3)
    before = deepcopy(variables)
    script.run("TOP_native_result_args", 1)
    assert variables["TOP_case_phase"][11] == before["TOP_case_phase"][11] == 3
    assert script.globals["TOP_status"][11] == 1
    assert variables["TOP_attempts"][11] == 0


def test_native_facility_collection_freezes_group_and_revalidates_its_host():
    script = CoreIntegrationScript()
    script.organization_truth(12, host=2, state=101)
    variables = script.countries[1]["vars"]
    variables["TOP_selected_organization"] = 12
    script.run("TOP_facility_tracking_started", 1)
    variables["TOP_selected_organization"] = 13
    script.run("TOP_facility_tracking_completed", 1)
    assert variables["TOP_org_location"][12] == 100
    assert variables["TOP_org_lead_state"][12] == 101
    assert variables["TOP_org_location"][13] == 0
    assert variables["TOP_facility_tracking_group"][2] == 0
    variables["TOP_selected_organization"] = 12
    script.run("TOP_facility_tracking_started", 1)
    script.globals["TOP_group_host"][12] = 3
    variables["TOP_org_location"][12] = 0
    script.run("TOP_facility_tracking_completed", 1)
    assert variables["TOP_org_location"][12] == 0


def test_iran_delayed_death_option_cannot_overwrite_capture_or_duplicate_death():
    event = read("events/Iran.txt")
    start = event.index("id = iranian_focus.159\n")
    event = event[start : event.index("\ncountry_event", start)]
    options = [
        value
        for key, _, value in _parse_race_script("event = {" + event + "}")["event"]
        if key == "option"
    ]
    for status in (2, 3):
        for option in options:
            script = CoreIntegrationScript()
            script.target(64, status=status)
            before = deepcopy(script.globals)
            script.execute(
                [item for item in option if item[0] not in ("name", "ai_chance")], 1
            )
            assert script.globals == before


@pytest.mark.parametrize("tier", [0, 1, 2, 3])
def test_top_native_person_uses_the_same_ct_hvt_consequence_helper(tier):
    script = CoreIntegrationScript()
    variables = script.authorize(target=1, method=1)
    script.globals["active_terror_org_vis_lvl"] = ScriptArray([20, 20])
    script.globals["active_terror_org_threat_lvl"] = ScriptArray([50, 40])
    variables["international_terror_org_temp_specific_intel"] = ScriptArray([0, 0])
    script.temps["TOP_tier"] = tier
    script.run("TOP_resolve_native_callback", 1)
    assert script.globals["active_terror_org_threat_lvl"][0] == (51, 45, 40, 35)[tier]
    assert (
        variables["international_terror_org_temp_specific_intel"][0]
        == (0, 1, 1, 5)[tier]
    )


@pytest.mark.parametrize("legacy_id", [1, 7, 13])
@pytest.mark.parametrize("outcome", [2, 3])
def test_top_removal_retires_isi_pool_and_empty_legacy_burn_is_inert(
    legacy_id, outcome
):
    script = CoreIntegrationScript()
    script.effects.update(
        _parse_race_script(
            _named_block(
                read(
                    "common/scripted_effects/01_targeted_operations_legacy_effects.txt"
                ),
                "TOP_apply_legacy_outcome",
            )
        )
    )
    script.effects.update(
        _parse_race_script(read("common/scripted_effects/99_ISI_scripted_effects.txt"))
    )
    script.stubs.remove("TOP_apply_legacy_outcome")
    script.stubs.update(
        {
            "ISI_retire_hvt_character",
            "ISI_hvt_news_coalition",
            "ISI_hvt_news_russian",
            "add_timed_idea",
            "add_war_support",
        }
    )
    target = legacy_id + 15
    script.target(target)
    script.globals["ISI_hvt_pool"] = ScriptArray([legacy_id])
    script.globals["num_days"] = 0
    script.temps.update(TOP_arg_target=target)
    script.run("TOP_capture_target" if outcome == 2 else "TOP_kill_target", 1)
    assert script.globals["ISI_hvt_pool"] == []
    assert script.external["ISI_retire_hvt_character", script.tag("ISI")] == 1
    before = deepcopy(script.globals)
    script.run("ISI_burn_hvt", 1)
    assert script.globals == before
    assert script.globals["TOP_removals"][target] == 1


@pytest.mark.parametrize("enabled", [False, True])
def test_isi_pool_seed_respects_all_thirteen_canonical_retirements_and_off_rule(
    enabled,
):
    script = CoreIntegrationScript()
    script.effects.update(
        _parse_race_script(read("common/scripted_effects/99_ISI_scripted_effects.txt"))
    )
    script.globals["TOP_rule_mode"] = int(enabled)
    script.globals["ISI_hvt_pool"] = ScriptArray()
    for target in range(16, 29):
        script.globals["TOP_status"][target] = 2 if target % 2 else 3
    script.run("ISI_setup_hvt_pool", 1)
    assert script.globals["ISI_hvt_pool"] == ([] if enabled else list(range(1, 14)))


def test_native_ct_tracking_initializes_dossier_storage_without_opening_top():
    script = CoreIntegrationScript()
    variables = script.countries[1]["vars"]
    variables["TOP_identity_confidence"] = ScriptArray()
    variables.pop("TOP_tracking_person", None)
    variables.pop("TOP_tracking_org", None)
    variables.update(selected_org=1, ct_tracking_available=1)
    script.temps["TOP_tracking_kind"] = 0
    script.run("TOP_tracking_started", 1)
    assert len(variables["TOP_tracking_org"]) == 1000
    assert variables["TOP_tracking_org"][2] == 10
    assert variables["TOP_tracking_person"][2] == 0
    assert variables["selected_org"] == 1


METHODS = {3: "covert_killing", 4: "rendition", 5: "host_arrest", 7: "poisoning"}


class AgencyScript(CoreIntegrationScript):
    def __init__(self):
        super().__init__()
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
        read("common/scripted_effects/04_targeted_operations_cases.txt"),
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


@pytest.mark.parametrize("method", METHODS)
@pytest.mark.parametrize("legacy_first", [False, True])
def test_agency_and_legacy_resolution_retire_the_same_person_once(method, legacy_first):
    script = AgencyScript()
    if method == 7:
        script.countries[1]["tag"] = "SOV"
    variables = script.authorize(method=method)
    script.callback(method, "on_start")
    script.callback(method, "outcome_execute")
    script.callback(method, "outcome_extra_execute")
    if legacy_first:
        script.temps.update(TOP_target=11, TOP_result=3)
        script.run("TOP_record_legacy_result", 1)
    script.complete(method)
    if not legacy_first:
        script.temps.update(TOP_target=11, TOP_result=3)
        script.run("TOP_record_legacy_result", 3)
    assert script.globals["TOP_removals"][11] == 1
    assert script.globals["TOP_status"][11] == (
        3 if legacy_first or method in (3, 7) else 2
    )
    assert variables["TOP_attempts"][11] == (0 if legacy_first else 1)


def test_two_agency_actors_cannot_capture_and_kill_the_same_person_twice():
    script = AgencyScript()
    first = script.authorize(method=3)
    script.callback(3, "on_start")
    script.callback(3, "outcome_execute")
    script.callback(3, "outcome_extra_execute")
    script.countries[3]["techs"].add("special_forces_tech_1")
    script.actor = 3
    second = script.authorize(method=4, actor=3)
    script.run("TOP_enroll_pending_actor", 3)
    script.callback(4, "on_start")
    script.callback(4, "outcome_execute")
    script.callback(4, "outcome_extra_execute")
    script.complete(4)
    script.actor = 1
    script.complete(3)
    assert script.globals["TOP_status"][11] == 2
    assert script.globals["TOP_custodian"][11] == 3
    assert script.globals["TOP_removals"][11] == 1
    assert first["TOP_attempts"][11] == 0
    assert second["TOP_attempts"][11] == 1


class CrisisOpinionScript(TargetScript):
    """Execute crisis responses with native opinion-target restrictions."""

    def __init__(self):
        super().__init__()
        self.crisis_events = _parse_race_script(
            "events = {\n"
            + (ROOT / "events/Targeted Operations.txt").read_text(encoding="utf-8")
            + "\n}"
        )["events"]
        self.stubs.add("TOP_cleanup_crisis")
        self.stubs.discard("TOP_process_crisis")
        self.opinions = Counter()
        self.changes = Counter()
        self.globals.update(
            TOP_clock=100,
            TOP_crisis_active=1,
            TOP_crisis_token=7,
            TOP_crisis_until=200,
            TOP_crisis_actor=1,
            TOP_crisis_protection=2,
            TOP_crisis_host=3,
            TOP_crisis_story=1,
            TOP_crisis_visit_token=1,
            TOP_crisis_tension=50,
            TOP_crisis_sanctions_threshold=30,
            TOP_crisis_ultimatum_threshold=85,
            TOP_crisis_actor_response=1,
            TOP_crisis_settlement_apology_pp=-25,
        )
        for actor in (1, 2, 3):
            self.countries[actor]["vars"]["TOP_crisis_token"] = 7
        self.countries[3]["vars"].update(
            TOP_crisis_participant_pending=1,
            TOP_crisis_participant_token=7,
        )

    def condition_statement(self, statement, identifier):
        if statement[0] == "subtract_from_temp_variable":
            self.execute_statement(statement, identifier)
            return True
        return super().condition_statement(statement, identifier)

    def execute_statement(self, statement, identifier):
        key, _, operand = statement
        if key in {"add_opinion_modifier", "reverse_add_opinion_modifier"}:
            fields = {name: value for name, _, value in operand}
            target = fields["target"]
            assert not target.startswith(
                "var:"
            ), "The native opinion effect rejects variable scopes as its target"
            target = self.value(target, identifier)
            source, recipient = identifier, target
            if key == "reverse_add_opinion_modifier":
                source, recipient = recipient, source
            self.opinions[source, recipient, fields["modifier"]] += 1
        elif key in {"add_stability", "add_war_support"}:
            self.changes[key, identifier] += self.value(operand, identifier)
        else:
            super().execute_statement(statement, identifier)

    def choose(self, event_id, option_name, actor):
        event = next(
            body
            for key, _, body in self.crisis_events
            if key == "country_event" and ("id", "=", event_id) in body
        )
        assert self.condition(
            dict((key, value) for key, _, value in event)["trigger"], actor
        )
        option = next(
            body
            for key, _, body in event
            if key == "option" and ("name", "=", option_name) in body
        )
        fields = dict((key, value) for key, _, value in option)
        assert self.condition(fields.get("trigger", []), actor)
        self.execute(
            [
                entry
                for entry in option
                if entry[0] not in {"name", "trigger", "ai_chance"}
            ],
            actor,
        )


@pytest.mark.parametrize(
    "effect,expired,modifier",
    [
        ("TOP_apply_crisis_sanctions", False, "harsh_sanctions"),
        ("TOP_process_crisis", True, "harsh_sanctions"),
        ("TOP_settle_crisis", False, "TOP_crisis_settlement"),
    ],
)
def test_crisis_resolution_keeps_both_opinion_directions(effect, expired, modifier):
    script = CrisisOpinionScript()
    if expired:
        script.globals["TOP_crisis_until"] = 99

    script.run(effect, 2)

    assert script.opinions == Counter({(1, 2, modifier): 1, (2, 1, modifier): 1})
    if modifier == "harsh_sanctions":
        assert script.changes == Counter({("add_stability", 1): -0.01})
    else:
        assert script.countries[1]["vars"]["political_power"] == 475
    if effect != "TOP_apply_crisis_sanctions":
        assert script.external["TOP_cleanup_crisis", 2] == 1


@pytest.mark.parametrize(
    "event,option,actor,target,modifier",
    [
        ("TOP_crisis.1", "TOP_crisis.1.b", 2, 1, "TOP_sovereignty_violation"),
        ("TOP_crisis.4", "TOP_crisis.4.a", 3, 2, "established_diplomatic_relations"),
        ("TOP_crisis.4", "TOP_crisis.4.b", 3, 1, "established_diplomatic_relations"),
        ("TOP_crisis.3", "TOP_crisis.3.c", 2, 1, "TOP_sovereignty_violation"),
    ],
)
def test_crisis_option_changes_only_the_respondents_opinion(
    event, option, actor, target, modifier
):
    script = CrisisOpinionScript()

    script.choose(event, option, actor)

    assert script.opinions == Counter({(actor, target, modifier): 1})


@pytest.mark.parametrize("effect", ["TOP_apply_crisis_sanctions", "TOP_settle_crisis"])
@pytest.mark.parametrize("invalid", ["disabled", "stale", "expired"])
def test_invalid_crisis_does_not_apply_opinions_or_costs(effect, invalid):
    script = CrisisOpinionScript()
    if invalid == "disabled":
        script.globals["TOP_rule_mode"] = 0
    elif invalid == "stale":
        script.countries[2]["vars"]["TOP_crisis_token"] = 6
    else:
        script.globals["TOP_crisis_until"] = 99

    script.run(effect, 2)

    assert not script.opinions
    assert not script.changes
    assert script.countries[1]["vars"]["political_power"] == 500


def test_sanctions_require_the_recorded_victim():
    script = CrisisOpinionScript()

    script.run("TOP_apply_crisis_sanctions", 3)

    assert not script.opinions
    assert not script.changes


def test_crisis_with_annexed_principal_cleans_up_instead_of_repeating_ultimatum():
    script = CrisisOpinionScript()
    script.globals.update(TOP_crisis_tension=100, TOP_crisis_until=99)
    script.countries[2]["exists"] = False

    script.run("TOP_process_crisis", 1)

    assert script.external["TOP_cleanup_crisis", 1] == 1
    assert not script.opinions
    assert not script.events
