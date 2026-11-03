import re

import pytest
from ai_race_state_model_test import _named_block, _parse_race_script
from stalker_lifecycle_test import ROOT, StalkerScript

ZONE = 698
RELIEF_DAYS = 180


def _zone(
    *,
    ai=True,
    political_power=10,
    treasury=100,
    containment=20,
    breach=False,
    mission=None,
):
    script = StalkerScript()
    script.globals["STALKER_active_zone_anchors"] = [ZONE]
    state = script.countries[ZONE]
    state["vars"].update(
        STALKER_zone_containment=containment,
        STALKER_zone_activity=90,
        STALKER_zone_exploitation=40,
    )
    if breach:
        state["flags"]["STALKER_perimeter_breach_active"] = None
    holder_id = state["controller"]
    holder = script.countries[holder_id]
    holder["ai"] = ai
    holder["vars"].update(political_power=political_power, treasury=treasury)
    if mission:
        holder["missions"].add(mission)
    return script, state, holder_id


def _relieved(script, holder_id):
    return script.external["small_expenditure", holder_id]


def test_a_broke_ai_zone_in_crisis_is_reinforced_and_paid_from_the_treasury():
    script, state, holder_id = _zone()
    script.run("STALKER_monthly_ai_zone_relief_pulse", 1)

    assert state["vars"]["STALKER_zone_containment"] == 40
    assert state["vars"]["STALKER_zone_activity"] == 80
    assert _relieved(script, holder_id) == 1
    assert (
        state["flags"]["STALKER_zone_reinforced"]
        == script.globals["num_days"] + RELIEF_DAYS
    )


def test_a_perimeter_breach_counts_as_a_crisis_above_30_containment():
    script, state, holder_id = _zone(containment=50, breach=True)
    script.run("STALKER_monthly_ai_zone_relief_pulse", 1)
    assert state["vars"]["STALKER_zone_containment"] == 70
    assert _relieved(script, holder_id) == 1


def test_relief_waits_out_its_cooldown():
    script, state, holder_id = _zone()
    script.run("STALKER_monthly_ai_zone_relief_pulse", 1)
    state["vars"]["STALKER_zone_containment"] = 10
    script.run("STALKER_monthly_ai_zone_relief_pulse", 1)
    assert state["vars"]["STALKER_zone_containment"] == 10
    assert _relieved(script, holder_id) == 1


@pytest.mark.parametrize(
    "case",
    [
        {"ai": False},
        {"political_power": 50},
        {"treasury": 9},
        {"containment": 30},
        {"mission": "bankruptcy_incoming_collapse"},
    ],
    ids=[
        "player",
        "can_afford_the_decision",
        "empty_treasury",
        "not_in_crisis",
        "near_bankruptcy",
    ],
)
def test_no_relief_outside_a_broke_ai_crisis(case):
    script, state, holder_id = _zone(**case)
    before = state["vars"]["STALKER_zone_containment"]
    script.run("STALKER_monthly_ai_zone_relief_pulse", 1)
    assert state["vars"]["STALKER_zone_containment"] == before
    assert _relieved(script, holder_id) == 0
    assert "STALKER_zone_reinforced" not in state["flags"]


def test_a_decision_reinforcement_starts_the_relief_cooldown():
    script, state, holder_id = _zone()
    script.run("STALKER_reinforce_containment", ZONE)
    state["vars"]["STALKER_zone_containment"] = 10
    script.run("STALKER_monthly_ai_zone_relief_pulse", 1)
    assert state["vars"]["STALKER_zone_containment"] == 10
    assert _relieved(script, holder_id) == 0


def test_no_relief_while_the_zone_policy_is_pending():
    script, state, holder_id = _zone()
    state["flags"]["STALKER_zone_policy_pending"] = None
    script.run("STALKER_monthly_ai_zone_relief_pulse", 1)
    assert _relieved(script, holder_id) == 0


def test_relief_runs_from_the_monthly_pulse_and_matches_the_decision():
    pulse = (ROOT / "common/scripted_effects/99_STALKER_pulse_effects.txt").read_text(
        encoding="utf-8"
    )
    assert (
        _named_block(pulse, "STALKER_monthly_pulse").count(
            "STALKER_monthly_ai_zone_relief_pulse = yes"
        )
        == 1
    )
    decision = _named_block(
        (ROOT / "common/decisions/STALKER_decisions.txt").read_text(encoding="utf-8"),
        "STALKER_reinforce_zone_containment",
    )
    cost = int(re.search(r"\n\t\tcost = (\d+)", decision).group(1))
    cooldown = int(re.search(r"days_re_enable = (\d+)", decision).group(1))
    effects = (
        ROOT / "common/scripted_effects/99_STALKER_scripted_effects.txt"
    ).read_text(encoding="utf-8")
    relief = _named_block(effects, "STALKER_monthly_ai_zone_relief_pulse")
    reinforce = _named_block(effects, "STALKER_reinforce_containment")
    assert f"has_political_power < {cost}" in relief
    assert "check_variable = { treasury < 10 }" in decision
    assert "check_variable = { treasury < 10 }" in relief
    assert (
        "set_state_flag = { flag = STALKER_zone_reinforced value = 1 "
        f"days = {cooldown} }}" in reinforce
    )
    assert "NOT = { has_state_flag = STALKER_zone_reinforced }" in relief
    assert "FROM = { has_state_flag = STALKER_zone_reinforced }" in decision
    assert "small_expenditure = yes" in decision and "small_expenditure = yes" in relief


@pytest.mark.parametrize(
    "breach,exploitation,expected",
    [(False, 19, 15), (False, 20, 5), (True, 19, 0), (True, 20, 0)],
)
def test_trader_license_ai_respects_breach_and_exploitation_together(
    breach, exploitation, expected
):
    script, state, holder_id = _zone(breach=breach)
    state["vars"]["STALKER_zone_exploitation"] = exploitation
    decision = _named_block(
        (ROOT / "common/decisions/STALKER_decisions.txt").read_text(encoding="utf-8"),
        "STALKER_license_cordon_trader",
    )
    weights = _parse_race_script(_named_block(decision, "ai_will_do"))["ai_will_do"]
    weight = float(next(value for key, _, value in weights if key == "base"))
    for key, _, body in weights:
        if key != "modifier":
            continue
        fields = {key: value for key, _, value in body}
        conditions = [
            (str(ZONE) if key == "FROM" else key, op, value)
            for key, op, value in body
            if key not in {"factor", "add"}
        ]
        if script.condition(conditions, holder_id):
            weight *= float(fields.get("factor", 1))
            weight += float(fields.get("add", 0))
    assert weight == expected
