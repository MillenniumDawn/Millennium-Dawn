import re
from pathlib import Path

import pytest
from stalker_lifecycle_test import StalkerScript, _event
from targeted_operations_model_test import _named_block, _parse_race_script

ROOT = Path(__file__).resolve().parents[3]


def _read(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


DECISIONS = _read("common/decisions/STALKER_antarctic_decisions.txt")
EFFECTS = _read("common/scripted_effects/99_STALKER_antarctic_effects.txt")
EVENTS = _read("events/STALKER_antarctic.txt")
LOC = _read("localisation/english/MD_STALKER_antarctic_l_english.yml")
TRIGGERS = _read("common/scripted_triggers/99_STALKER_scripted_triggers.txt")


def test_the_study_needs_five_artifacts_and_a_working_radiation_laboratory():
    study = _named_block(DECISIONS, "STALKER_polar_artifact_study")
    available = _named_block(study, "available")
    assert "check_variable = { STALKER_artifact_stockpile > 4.99 }" in available
    assert "STALKER_has_working_radiation_lab = yes" in available
    assert (
        "has_dynamic_modifier = { modifier = STALKER_polar_artifact_samples }"
        in available
    )
    effect = _named_block(study, "complete_effect")
    assert "add_to_variable = { STALKER_artifact_stockpile = -5 }" in effect
    assert (
        "add_dynamic_modifier = { modifier = STALKER_polar_artifact_samples days = 180 }"
        in effect
    )
    assert "country_event = { id = STALKER.190 days = 180 }" in effect
    assert "has_active_mission = bankruptcy_incoming_collapse" in _named_block(
        study, "ai_will_do"
    )


def test_the_laboratory_check_reads_the_live_station():
    lab = _named_block(TRIGGERS, "STALKER_has_working_radiation_lab")
    assert "has_idea = at_member" in lab
    assert "array = country_owned_station_ids" in lab
    assert "check_variable = { stalker_station > 0 }" in lab
    assert "global.antarctica_station_controller^stalker_station = THIS.id" in lab
    for slot in range(6, 10):
        assert (
            f"global.antarctica_station_module_slot_{slot}^stalker_station = 7" in lab
        )
        assert (
            f"global.antarctica_station_module_slot_{slot}_blizzard_damaged^stalker_station > 0"
            in lab
        )
    assert "global.antarctica_station_output_storage^stalker_station > 0" in lab
    assert (
        "var = global.antarctica_station_output_power^stalker_station value = 0" in lab
    )
    assert "antarctica_lab_cat_nuclear_reactors" not in DECISIONS


def test_the_samples_speed_research_and_station_iterations():
    modifiers = _read("common/dynamic_modifiers/00_STALKER_dynamic_modifiers.txt")
    samples = _named_block(modifiers, "STALKER_polar_artifact_samples")
    assert "research_speed_factor = 0.03" in samples
    assert "antarctica_lab_iteration_progress_modifier = 0.15" in samples


@pytest.mark.parametrize(
    "illegal,open_loop,enabled,samples",
    [
        (illegal, open_loop, True, True)
        for illegal, open_loop in ((0, 0), (1, 0), (0, 1), (1, 1))
    ]
    + [(0, 0, False, True), (0, 0, True, False)],
)
def test_observers_always_seize_the_study_and_penalize_only_once(
    illegal, open_loop, enabled, samples
):
    script = StalkerScript()
    script.effects.update(_parse_race_script(EFFECTS))
    script.stubs.update(
        {
            "antarctica_observer_detected_nukes_research_effect",
            "antarctica_observer_detected_illegal_research_effect",
            "antarctica_observer_detected_open_loop_effect",
        }
    )
    actor = script.countries[1]["vars"]
    actor.update(
        antarctica_observer_target_station=7, antarctica_observer_target_country=2
    )
    holder = script.countries[2]
    holder["dynamic_modifiers"] = (
        {"STALKER_polar_artifact_samples"} if samples else set()
    )
    if not enabled:
        script.triggers["STALKER_scenario_enabled"] = [("always", "=", "no")]
    values = {
        "exists": 1,
        "observers_incoming": 1,
        "controller": 2,
        "illegal_activities_enabled": illegal,
        "module_slot_12": open_loop,
    }
    values.update({f"module_slot_{slot}": 0 for slot in range(6, 10)})
    for name, value in values.items():
        script.globals["antarctica_station_" + name] = [0] * 7 + [value]
    immediate = next(
        body
        for key, _, body in _event("MD_antarctica.2", "events/MD_Antarctica.txt")
        if key == "immediate"
    )
    script.execute(immediate, 1)
    seized = enabled and samples
    assert actor.get("antarctica_illegal_research_reports", 0) == int(seized)
    penalty = seized and not illegal and not open_loop
    assert script.events.count((2, "MD_antarctica.4")) == int(penalty)
    assert script.events.count((2, "STALKER.191")) == int(seized)
    assert holder["dynamic_modifiers"] == (
        {"STALKER_polar_artifact_samples"} if samples and not seized else set()
    )
    assert script._flag(holder["flags"], "STALKER_polar_study_cut_short") == seized
    if penalty:
        assert script.events.index((2, "MD_antarctica.4")) < script.events.index(
            (2, "STALKER.191")
        )


def test_seized_samples_end_the_study_and_use_the_treaty_penalty():
    detected = _named_block(EFFECTS, "STALKER_polar_study_detected")
    assert (
        "remove_dynamic_modifier = { modifier = STALKER_polar_artifact_samples }"
        in detected
    )
    assert (
        "set_country_flag = { flag = STALKER_polar_study_cut_short days = 181 value = 1 }"
        in detected
    )
    assert "news_event = STALKER.191" in detected
    assert "country_event = MD_antarctica.4" not in detected
    assert detected.index(
        "has_dynamic_modifier = { modifier = STALKER_polar_artifact_samples }"
    ) < detected.index("remove_dynamic_modifier")
    news = EVENTS[EVENTS.index("id = STALKER.191") :]
    assert "major = yes" in news.split("option", 1)[0]
    results = EVENTS[EVENTS.index("id = STALKER.190") :]
    assert (
        "NOT = { has_country_flag = STALKER_polar_study_cut_short }"
        in results.split("option", 1)[0]
    )


def test_the_study_ends_the_first_day_its_laboratory_stops():
    study = _named_block(DECISIONS, "STALKER_polar_artifact_study")
    assert "country_event = { id = STALKER.192 days = 1 }" in study
    check = EVENTS[EVENTS.index("id = STALKER.192") :]
    assert "hidden = yes" in check
    trigger = _named_block(check, "trigger")
    assert (
        "has_dynamic_modifier = { modifier = STALKER_polar_artifact_samples }"
        in trigger
    )
    assert "NOT = { STALKER_has_working_radiation_lab = yes }" in check
    assert "STALKER_polar_study_lab_lost = yes" in check
    assert "else = { country_event = { id = STALKER.192 days = 1 } }" in check
    lost = _named_block(EFFECTS, "STALKER_polar_study_lab_lost")
    assert "flag = STALKER_polar_study_cut_short days = 181" in lost
    assert lost.index("has_dynamic_modifier") < lost.index("remove_dynamic_modifier")
    pulses = _read("common/scripted_effects/99_STALKER_pulse_effects.txt")
    assert "STALKER_monthly_antarctic_pulse" not in pulses


def test_event_ids_stay_in_the_block_and_every_key_has_english_text():
    ids = [int(n) for n in re.findall(r"id = STALKER\.(\d+)", EVENTS)]
    assert ids and all(190 <= n <= 199 for n in ids)
    for key in re.findall(
        r"(?:title|desc|name|tooltip|custom_effect_tooltip) = (STALKER[A-Za-z0-9_.]*)",
        DECISIONS + EVENTS + EFFECTS,
    ):
        assert re.search(rf"(?m)^ {re.escape(key)}: \"", LOC), key
    for key in (
        "STALKER_polar_artifact_study",
        "STALKER_polar_artifact_study_desc",
        "STALKER_polar_artifact_samples",
        "STALKER_polar_artifact_study_bonus",
    ):
        assert re.search(rf"(?m)^ {re.escape(key)}: \"", LOC), key


@pytest.mark.parametrize(
    "slot,member,controller,damaged,fuel,storage,power,stations,expected",
    [(slot, True, 2, 0, 1, 1, 0, [7], True) for slot in range(6, 10)]
    + [
        (6, False, 2, 0, 1, 1, 0, [7], False),
        (6, True, 3, 0, 1, 1, 0, [7], False),
        (6, True, 2, 1, 1, 1, 0, [7], False),
        (6, True, 2, 0, 1, 0, 0, [7], False),
        (6, True, 2, 0, 0, 0, 0, [7], True),
        (6, True, 2, 0, 1, 1, -1, [7], False),
        (6, True, 2, 0, 1, 1, 0, [], False),
        (6, True, 2, 0, 1, 1, 0, [0], False),
        (0, True, 2, 0, 1, 1, 0, [7], False),
    ],
)
def test_polar_laboratory_evaluates_live_station_conditions(
    slot, member, controller, damaged, fuel, storage, power, stations, expected
):
    script = StalkerScript()
    script.triggers.update(_parse_race_script(TRIGGERS))
    holder = script.countries[2]
    holder["ideas"] = {"at_member"} if member else set()
    holder["vars"]["country_owned_station_ids"] = stations
    script.globals["antarctica_station_controller"] = [0] * 7 + [controller]
    for module in range(6, 10):
        script.globals[f"antarctica_station_module_slot_{module}"] = [0] * 7 + [
            7 if module == slot else 0
        ]
        script.globals[f"antarctica_station_module_slot_{module}_blizzard_damaged"] = [
            0
        ] * 7 + [damaged]
    for name, value in (("fuel_usage", fuel), ("storage", storage), ("power", power)):
        script.globals["antarctica_station_output_" + name] = [0] * 7 + [value]
    assert (
        script.condition([("STALKER_has_working_radiation_lab", "=", "yes")], 2)
        == expected
    )


@pytest.mark.parametrize(
    "effect", ["STALKER_polar_study_detected", "STALKER_polar_study_lab_lost"]
)
@pytest.mark.parametrize("samples", [False, True])
def test_polar_cancellation_removes_samples_and_blocks_the_delayed_reward(
    effect, samples
):
    script = StalkerScript()
    script.effects.update(_parse_race_script(EFFECTS))
    holder = script.countries[2]
    holder["dynamic_modifiers"] = (
        {"STALKER_polar_artifact_samples"} if samples else set()
    )
    result_gate = next(
        body
        for key, _, body in _event("STALKER.190", "events/STALKER_antarctic.txt")
        if key == "trigger"
    )
    assert script.condition(result_gate, 2)
    script.run(effect, 2)
    assert not holder["dynamic_modifiers"]
    assert (
        holder["flags"]["STALKER_polar_study_cut_short"]
        == script.globals["num_days"] + 181
    )
    assert not script.condition(result_gate, 2)
    assert ((2, "STALKER.191") in script.events) == (
        effect == "STALKER_polar_study_detected"
    )
    assert (2, "MD_antarctica.4") not in script.events
