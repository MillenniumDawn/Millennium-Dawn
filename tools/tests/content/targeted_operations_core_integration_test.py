"""Source-executed regression coverage for CT/native authority and legacy races."""

from copy import deepcopy

import pytest
from targeted_operations_core_test import ScriptArray, TargetScript
from targeted_operations_model_test import _named_block, _parse_race_script
from targeted_operations_redesign_test import block, read


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
    org = read("common/scripted_effects/07_targeted_operations_organization_cases.txt")
    resolution = read("common/scripted_effects/08_targeted_operations_resolution.txt")
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
        "common/scripted_effects/08_targeted_operations_resolution.txt",
        "TOP_resolve_person_operation",
    )
    assert "TOP_intelligence_roll" not in native


def test_all_generated_raids_share_core_eligibility_cost_losses_and_victim_reactions():
    raids = read("common/raids/targeted_operations_raids.txt")
    assert raids.count("raid_available_base = yes") == 320
    assert raids.count("raid_can_launch = yes") == 320
    assert raids.count("top_native_person_reaction = yes") == 1280
    assert "victim_effects = { send_raid_event_to_victim" not in raids
    assert raids.count("apply_raid_failure_losses = yes") == 160
    assert raids.count("raid_damage_units = { org_damage") == 640


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
    from targeted_operations_agency_test import AgencyScript

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
