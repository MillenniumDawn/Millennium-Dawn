import re
from pathlib import Path

from targeted_operations_model_test import _named_block

ROOT = Path(__file__).resolve().parents[3]


def _read(path):
    return (ROOT / path).read_text(encoding="utf-8-sig")


DECISIONS = _read("common/decisions/STALKER_antarctic_decisions.txt")
EFFECTS = _read("common/scripted_effects/99_STALKER_antarctic_effects.txt")
EVENTS = _read("events/STALKER_antarctic.txt")
OBSERVER = _read("events/MD_Antarctica.txt")
LOC = _read("localisation/english/MD_STALKER_antarctic_l_english.yml")
TRIGGERS = _read("common/scripted_triggers/99_STALKER_antarctic_triggers.txt")


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
    modifiers = _read(
        "common/dynamic_modifiers/00_STALKER_antarctic_dynamic_modifiers.txt"
    )
    samples = _named_block(modifiers, "STALKER_polar_artifact_samples")
    assert "research_speed_factor = 0.03" in samples
    assert "antarctica_lab_iteration_progress_modifier = 0.15" in samples


def test_observers_always_seize_the_study_and_penalize_only_once():
    start = OBSERVER.index("# STALKER: observers always seize Zone artifacts")
    block = _named_block(OBSERVER[start:], "if")
    assert "STALKER_scenario_enabled = yes" in block
    assert (
        "has_dynamic_modifier = { modifier = STALKER_polar_artifact_samples }" in block
    )
    penalty = _named_block(block.split("\n", 1)[1], "if")
    assert "check_variable = { station_illegal_activities < 1 }" in penalty
    assert "NOT = { check_variable = { station_open_loop_module = 1 } }" in penalty
    assert "add_to_variable = { antarctica_illegal_research_reports = 1 }" in penalty
    assert "country_event = MD_antarctica.4" in penalty
    assert "STALKER_polar_study_detected = yes" not in penalty
    assert block.rindex("STALKER_polar_study_detected = yes") > block.rindex(
        "country_event = MD_antarctica.4"
    )
    preceding = OBSERVER[
        OBSERVER.rindex("if = {\n\t\t\t\tlimit = {\n\t\t\t\t\tOR = {", 0, start) : start
    ]
    assert "station_illegal_activities > 0" in preceding


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
