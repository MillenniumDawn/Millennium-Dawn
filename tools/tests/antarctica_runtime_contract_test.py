from pathlib import Path

import pytest
from shared_utils import extract_block_from_text, iter_statements, strip_comments

ROOT = Path(__file__).resolve().parents[2]
EFFECTS = strip_comments(
    (ROOT / "common/scripted_effects/00_antarctica_effects.txt").read_text(
        encoding="utf-8"
    )
)
EVENTS = strip_comments((ROOT / "events/MD_Antarctica.txt").read_text(encoding="utf-8"))


def _effect(name):
    body, end = extract_block_from_text(EFFECTS, EFFECTS.index(f"{name} = {{"))
    assert end > 0
    return body


def _write_guard(body, assignment):
    for key, _, block in iter_statements(body):
        if block is None:
            continue
        children = list(iter_statements(block))
        if key == "if" and any(
            child_key in {"set_variable", "set_temp_variable"}
            and child_block is not None
            and child_block.strip() == assignment
            for child_key, _, child_block in children
        ):
            guard = next(
                child_block
                for child_key, _, child_block in children
                if child_key == "limit"
            )
            assert guard is not None
            return guard
        if assignment in block:
            return _write_guard(block, assignment)
    raise AssertionError(f"Missing conditional assignment: {assignment}")


def test_recalculation_preserves_empty_fuel_and_clamps_to_capacity():
    body = _effect("antarctica_recalculate_station_module_outputs")
    assert "set_temp_variable = { effective_storage = existing_storage }" in body
    assert "check_variable = { existing_storage > 0 }" not in body
    assert (
        "set_temp_variable = { effective_storage = out_capacity }"
        not in body.split("check_variable = { effective_storage > out_capacity }")[0]
    )
    assert "check_variable = { effective_storage < 0 }" in body
    assert (
        "set_variable = { global.antarctica_station_output_storage^station_id = effective_storage }"
        in body
    )


@pytest.mark.parametrize("slot", range(6, 10))
@pytest.mark.parametrize("reward", [False, True])
def test_damaged_laboratories_do_not_grant_benefits(slot, reward):
    if reward:
        body = _effect("antarctica_process_station_research_progress")
        index = "process_station_id"
        assignment = f"global.antarctica_iteration_lab_module_{slot - 6} = global.antarctica_station_module_slot_{slot}^{index}"
        assert (
            f"set_variable = {{ global.antarctica_iteration_lab_module_{slot - 6} = 0 }}"
            in body
        )
    else:
        body = _effect("antarctica_apply_station_laboratory_effects_to_controller")
        index = "station_id"
        assignment = (
            f"station_lab_module = global.antarctica_station_module_slot_{slot}^{index}"
        )
    guard = _write_guard(body, assignment)
    assert (
        f"NOT = {{ check_variable = {{ global.antarctica_station_module_slot_{slot}_blizzard_damaged^{index} > 0 }} }}"
        in guard
    )


def test_delayed_inspection_requires_existing_station_and_same_controller():
    body, end = extract_block_from_text(EVENTS, EVENTS.index("id = MD_antarctica.2"))
    assert end > 0
    guard = _write_guard(
        body,
        "station_illegal_activities = global.antarctica_station_illegal_activities_enabled^antarctica_observer_target_station",
    )
    assert (
        "check_variable = { global.antarctica_station_exists^antarctica_observer_target_station > 0 }"
        in guard
    )
    assert (
        "check_variable = { global.antarctica_station_controller^antarctica_observer_target_station = antarctica_observer_target_country }"
        in guard
    )
    assert body.index(
        "clr_country_flag = antarctica_observer_mission_in_progress"
    ) < body.index("global.antarctica_station_exists^")
    assert body.index("global.antarctica_station_observers_incoming^") < body.index(
        "global.antarctica_station_exists^"
    )
