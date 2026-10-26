from copy import deepcopy

import pytest
from stalker_lifecycle_test import ROOT, StalkerScript, _event, _option
from targeted_operations_model_test import _named_block, _parse_race_script

EVENTS = "events/STALKER_field_campaigns.txt"


class FieldScript(StalkerScript):
    def __init__(self):
        super().__init__()
        self.research_rewards = []

    def execute_statement(self, statement, identifier):
        key, _, operand = statement
        if key == "add_tech_bonus":
            self.research_rewards.append(
                (identifier, dict((name, value) for name, _, value in operand))
            )
        elif key != "custom_effect_tooltip":
            super().execute_statement(statement, identifier)

    def condition_statement(self, statement, identifier):
        if statement[0] == "FROM":
            return self.scoped(statement[2], identifier, 698, condition=True)
        return super().condition_statement(statement, identifier)


def campaign():
    script = FieldScript()
    script.effects.update(
        _parse_race_script(
            (
                ROOT / "common/scripted_effects/99_STALKER_field_campaigns_effects.txt"
            ).read_text(encoding="utf-8")
        )
    )
    script.prepare_original_zone()
    script.run("STALKER_monthly_field_campaigns_pulse", 2)
    return script


def assignment(script, name):
    text = (ROOT / "common/decisions/STALKER_field_campaigns_decisions.txt").read_text(
        encoding="utf-8"
    )
    body = _named_block(_named_block(text, name), "complete_effect")
    return _parse_race_script(body)["complete_effect"]


@pytest.mark.parametrize("case", [1, 2, 3])
@pytest.mark.parametrize("step", [0, 3, 6])
def test_pending_reports_follow_control_and_old_options_do_nothing(case, step):
    script = campaign()
    variables = script.countries[698]["vars"]
    variables.update(STALKER_field_case=case, STALKER_field_step=step)
    script.countries[698]["flags"].pop("STALKER_field_notice_pending", None)
    script.run("STALKER_monthly_field_campaigns_pulse", 2)
    event = f"STALKER.{200 + (case - 1) * 3 + step // 3}"
    before_count = script.events.count((2, event))
    script.run("STALKER_monthly_field_campaigns_pulse", 2)
    assert script.events.count((2, event)) == before_count
    script.countries[698]["controller"] = 3
    script.hidden_option(event, event + ".a", EVENTS)
    assert variables["STALKER_field_step"] == step
    script.run("STALKER_monthly_field_campaigns_pulse", 3)
    assert (3, event) in script.events


def test_both_assignments_keep_their_full_delay_after_control_change_and_reload():
    script = campaign()
    script.hidden_option("STALKER.200", "STALKER.200.a", EVENTS)
    script.execute(assignment(script, "STALKER_field_investigate"), 2)
    script.countries[698]["controller"] = 3
    script = deepcopy(script)
    script.goto(2012, 2, 29)
    script.run("STALKER_monthly_field_campaigns_pulse", 3)
    assert script.countries[698]["vars"]["STALKER_field_step"] == 2
    script.goto(2012, 3, 1)
    script.run("STALKER_monthly_field_campaigns_pulse", 3)
    assert script.countries[698]["vars"]["STALKER_field_step"] == 3
    script.actor = 3
    script.hidden_option("STALKER.201", "STALKER.201.a", EVENTS)
    script.execute(assignment(script, "STALKER_field_recover"), 3)
    script.goto(2012, 4, 29)
    script.run("STALKER_monthly_field_campaigns_pulse", 3)
    assert script.countries[698]["vars"]["STALKER_field_step"] == 5
    script.goto(2012, 4, 30)
    script.run("STALKER_monthly_field_campaigns_pulse", 3)
    assert script.countries[698]["vars"]["STALKER_field_step"] == 6


@pytest.mark.parametrize("case", [1, 2, 3])
@pytest.mark.parametrize("letter", "abc")
def test_campaign_endings_record_a_site_outcome_and_cannot_reward_twice(case, letter):
    script = campaign()
    variables = script.countries[698]["vars"]
    variables.update(STALKER_field_case=case, STALKER_field_step=6)
    event = f"STALKER.{202 + (case - 1) * 3}"
    script.hidden_option(event, event + "." + letter, EVENTS)
    result = ("yantar", "road", "forest")[case - 1]
    assert variables[f"STALKER_field_{result}_result"] == "abc".index(letter) + 1
    assert variables["STALKER_field_case"] == case + 1
    assert variables["STALKER_field_step"] == 0
    before = variables.copy()
    rewards = list(script.research_rewards)
    assert len(rewards) == int((case, letter) in {(1, "a"), (3, "b")})
    script.hidden_option(event, event + "." + letter, EVENTS)
    assert variables == before
    assert script.research_rewards == rewards


@pytest.mark.parametrize("case", [1, 2, 3])
def test_abandonment_advances_once_and_leaves_bandits_stronger(case):
    script = campaign()
    variables = script.countries[698]["vars"]
    variables.update(STALKER_field_case=case, STALKER_field_step=0)
    event = f"STALKER.{200 + (case - 1) * 3}"
    before = variables["STALKER_zone_bandits"]
    script.hidden_option(event, event + ".b", EVENTS)
    assert variables["STALKER_field_case"] == case + 1
    assert variables["STALKER_zone_bandits"] == before + 10


@pytest.mark.parametrize(
    "name,meter,delta", [("supplies", "scientists", 5), ("patrol", "bandits", -5)]
)
def test_recurring_assignment_pays_once_after_60_days(name, meter, delta):
    script = campaign()
    variables = script.countries[698]["vars"]
    variables[
        (
            "STALKER_field_yantar_result"
            if name == "supplies"
            else "STALKER_field_road_result"
        )
    ] = 1
    before = variables[f"STALKER_zone_{meter}"]
    script.execute(assignment(script, "STALKER_field_" + name), 2)
    script.goto(2012, 2, 29)
    script.run("STALKER_monthly_field_campaigns_pulse", 2)
    assert variables[f"STALKER_zone_{meter}"] == before
    script.goto(2012, 3, 1)
    script.run("STALKER_monthly_field_campaigns_pulse", 2)
    assert variables[f"STALKER_zone_{meter}"] == before + delta
    script.run("STALKER_monthly_field_campaigns_pulse", 2)
    assert variables[f"STALKER_zone_{meter}"] == before + delta
    assert script._flag(
        script.countries[698]["flags"], "STALKER_field_" + name + "_wait"
    )


@pytest.mark.parametrize("invalid", ["disabled", "inactive", "policy"])
def test_campaign_has_no_pulse_effect_outside_its_runtime_gate(invalid):
    script = campaign()
    script.countries[698]["vars"].update(STALKER_field_step=2)
    if invalid == "disabled":
        script.triggers["STALKER_scenario_enabled"] = [("always", "=", "no")]
    elif invalid == "inactive":
        script.triggers["STALKER_is_active_zone_anchor"] = [("always", "=", "no")]
    else:
        script.countries[698]["flags"]["STALKER_zone_policy_pending"] = None
    before = deepcopy(script.countries[698])
    script.run("STALKER_monthly_field_campaigns_pulse", 2)
    assert script.countries[698] == before


@pytest.mark.parametrize(
    "result,used,owner,pp,allowed",
    [
        (1, False, 2, 50, True),
        (2, False, 2, 49, False),
        (3, False, 2, 50, False),
        (1, True, 2, 50, False),
        (1, False, 3, 50, False),
        (1, True, 2, 75, True),
    ],
)
def test_purge_affordability_and_consumed_discount_agree(
    result, used, owner, pp, allowed
):
    script = campaign()
    script.countries[698]["vars"]["STALKER_field_forest_result"] = result
    script.countries[698]["controller"] = owner
    script.countries[2]["vars"].update(political_power=pp, STALKER_mdst_penetration=50)
    if used:
        script.countries[698]["flags"]["STALKER_field_purge_used"] = None
    body = _parse_race_script(
        (ROOT / "common/decisions/STALKER_mdst_decisions.txt").read_text(
            encoding="utf-8"
        )
    )["STALKER_mdst_category"]
    body = next(value for key, _, value in body if key == "STALKER_purge_mdst_channels")
    cost = next(value for key, _, value in body if key == "custom_cost_trigger")
    assert script.condition(cost, 2) == allowed
    if allowed:
        script.execute(
            next(value for key, _, value in body if key == "complete_effect"), 2
        )
        assert script.countries[2]["vars"]["political_power"] == 0


def test_2018_yantar_payoff_stays_inside_the_existing_one_time_choice():
    script = campaign()
    script.effects.update(
        _parse_race_script(
            (ROOT / "common/scripted_effects/99_STALKER_legend_effects.txt").read_text(
                encoding="utf-8"
            )
        )
    )
    script.countries[698]["vars"]["STALKER_field_yantar_result"] = 1
    before = script.countries[698]["vars"]["STALKER_zone_scientists"]
    script.run("STALKER_apply_sircaa_charter", 2)
    assert script.countries[698]["vars"]["STALKER_zone_scientists"] == before + 5
    script.run("STALKER_apply_sircaa_charter", 2)
    assert script.countries[698]["vars"]["STALKER_zone_scientists"] == before + 5


@pytest.mark.parametrize("result", [0, 1, 2, 3, 4])
def test_2022_road_preparation_offsets_five_containment_only_once(result):
    script = campaign()
    script.effects.update(
        _parse_race_script(
            (ROOT / "common/scripted_effects/99_STALKER_2022_effects.txt").read_text(
                encoding="utf-8"
            )
        )
    )
    script.globals["STALKER_active_zone_anchors"] = [698]
    variables = script.countries[698]["vars"]
    variables["STALKER_field_road_result"] = result
    script.run("STALKER_begin_battle_for_the_zone", 2)
    assert variables["STALKER_zone_containment"] == 35 + (5 if 0 < result < 4 else 0)
    script.run("STALKER_begin_battle_for_the_zone", 2)
    assert variables["STALKER_zone_containment"] == 20 + (5 if 0 < result < 4 else 0)


@pytest.mark.parametrize("case", [1, 2, 3])
@pytest.mark.parametrize("step", range(7))
def test_battle_closes_unfinished_preparation_and_rejects_delayed_reports(case, step):
    script = campaign()
    site = script.countries[698]
    variables = site["vars"]
    variables.update(STALKER_field_case=case, STALKER_field_step=step)
    names = ("yantar", "road", "forest")
    for completed in names[: case - 1]:
        variables[f"STALKER_field_{completed}_result"] = 1
    site["flags"]["STALKER_field_work_wait"] = None
    script.global_flags["STALKER_battle_for_the_zone"] = None
    script = deepcopy(script)
    script.run("STALKER_monthly_field_campaigns_pulse", 2)
    variables = script.countries[698]["vars"]
    assert variables["STALKER_field_case"] == 4
    assert variables["STALKER_field_step"] == 0
    assert "STALKER_field_work_wait" not in script.countries[698]["flags"]
    for index, name in enumerate(names):
        assert variables[f"STALKER_field_{name}_result"] == (
            1 if index < case - 1 else 4
        )
    before = variables.copy()
    event = f"STALKER.{202 + (case - 1) * 3}"
    script.hidden_option(event, event + ".a", EVENTS)
    script.run("STALKER_monthly_field_campaigns_pulse", 2)
    assert variables == before
    assert script.research_rewards == []


@pytest.mark.parametrize("result,duty,freedom", [(1, 5, 5), (2, 5, -5), (3, -5, 5)])
def test_road_patrol_follows_the_recorded_faction_settlement_once(
    result, duty, freedom
):
    script = campaign()
    variables = script.countries[698]["vars"]
    variables["STALKER_field_road_result"] = result
    before = variables["STALKER_zone_duty"], variables["STALKER_zone_freedom"]
    script.execute(assignment(script, "STALKER_field_patrol"), 2)
    script.goto(2012, 3, 1)
    script.run("STALKER_monthly_field_campaigns_pulse", 2)
    assert variables["STALKER_zone_duty"] == before[0] + duty
    assert variables["STALKER_zone_freedom"] == before[1] + freedom
    completed = variables.copy()
    script.run("STALKER_monthly_field_campaigns_pulse", 2)
    assert variables == completed
    assert script.research_rewards == []


@pytest.mark.parametrize(
    "case,step,letters",
    [
        (case, step, letters)
        for case in (1, 2, 3)
        for step, letters in ((0, "ab"), (3, "a"), (6, "abc"))
    ],
)
def test_field_report_event_and_options_keep_each_live_gate(case, step, letters):
    script = campaign()
    site = script.countries[698]
    site["vars"].update(STALKER_field_case=case, STALKER_field_step=step)
    event = f"STALKER.{200 + (case - 1) * 3 + step // 3}"
    gates = [next(body for key, _, body in _event(event, EVENTS) if key == "trigger")]
    gates.extend(
        next(
            body
            for key, _, body in _option(event, event + "." + letter, EVENTS)
            if key == "trigger"
        )
        for letter in letters
    )
    assert all(script.condition(gate, 2) for gate in gates)
    for invalid in (
        "disabled",
        "inactive",
        "zone_id",
        "policy",
        "controller",
        "case",
        "step",
    ):
        changed = script
        zone = deepcopy(site)
        changed.countries[698] = zone
        for trigger in ("STALKER_scenario_enabled", "STALKER_is_active_zone_anchor"):
            changed.triggers[trigger] = [("always", "=", "yes")]
        if invalid in {"disabled", "inactive"}:
            trigger = (
                "STALKER_scenario_enabled"
                if invalid == "disabled"
                else "STALKER_is_active_zone_anchor"
            )
            changed.triggers[trigger] = [("always", "=", "no")]
        elif invalid == "policy":
            zone["flags"]["STALKER_zone_policy_pending"] = None
        elif invalid == "controller":
            zone["controller"] = 3
        else:
            variable = (
                "STALKER_zone_id"
                if invalid == "zone_id"
                else "STALKER_field_" + invalid
            )
            zone["vars"][variable] += 1
        assert not any(changed.condition(gate, 2) for gate in gates), invalid
        before = deepcopy(zone)
        for letter in letters:
            changed.hidden_option(event, event + "." + letter, EVENTS)
        assert zone == before, invalid
        assert not changed.research_rewards, invalid
