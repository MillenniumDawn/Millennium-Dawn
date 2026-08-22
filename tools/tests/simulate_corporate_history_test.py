import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))

from simulate_corporate_history import (
    LABEL,
    ScenarioError,
    ScriptIndex,
    _simulate_bridge,
    main,
    run_scenarios,
)


def _manifest(schema_version=6):
    return {
        "schema_version": schema_version,
        "chains": [
            {
                "root": "USA_test",
                "tag": "USA",
                "full_start_strategies": [
                    "yearly_dispatcher",
                    "current_year_scheduler",
                    "reconstruction",
                ],
                "outcomes_only_strategy": "reconstruction",
                "terminal_marker": "USA_test_reconstruct_complete",
                "terminal_date": "2025-01-01",
                "dependency_order": ["USA_dependency"],
                "expected_callers": {
                    "USA_test_events.2": [
                        "effect:USA_test_schedule_current_year_events"
                    ],
                    "USA_test_events.3": ["effect:USA_corporate_trigger_year_2025"],
                },
            },
            {
                "root": "USA_dependency",
                "tag": "USA",
                "full_start_strategies": ["reconstruction"],
                "outcomes_only_strategy": "reconstruction",
                "terminal_marker": "USA_dependency_reconstruct_complete",
                "terminal_date": "2025-01-01",
                "dependency_order": [],
            },
        ],
    }


def _history(mode="full", start_date="2024-01-01"):
    return {
        "name": "history",
        "type": "corporate_history",
        "chain": "USA_test",
        "owner": "USA",
        "mode": mode,
        "start_date": start_date,
        "initial_markers": [],
        "dependencies": ["USA_dependency"],
        "milestones": [
            {"event_id": "USA_test_events.1", "date": "2023-01-01", "marker": "past"},
            {
                "event_id": "USA_test_events.2",
                "date": "2024-06-01",
                "marker": "current",
            },
            {"event_id": "USA_test_events.3", "date": "2025-06-01", "marker": "future"},
        ],
    }


def test_full_late_start_reconstructs_past_and_schedules_remaining():
    scenario = _history()
    scenario["expected"] = {
        "completion_markers": [],
        "reconstructed_markers": ["past"],
        "stranded_markers": [],
        "visible_events": ["USA_test_events.2", "USA_test_events.3"],
    }
    results, passed = run_scenarios(_manifest(), {"scenarios": [scenario]})
    assert passed
    assert results[0]["passed"]


def test_schema_v6_non_january_start_uses_monthly_recovery():
    scenario = _history(start_date="2024-02-01")
    scenario["expected"] = {
        "completion_markers": [],
        "reconstructed_markers": ["past"],
        "stranded_markers": [],
        "visible_events": ["USA_test_events.2", "USA_test_events.3"],
    }

    _results, passed = run_scenarios(_manifest(), {"scenarios": [scenario]})

    assert passed


def test_schema_v5_non_january_start_keeps_legacy_scheduler_behavior():
    scenario = _history(start_date="2024-02-01")
    scenario["expected"] = {
        "completion_markers": [],
        "reconstructed_markers": ["past"],
        "stranded_markers": ["current"],
        "visible_events": ["USA_test_events.3"],
    }

    _results, passed = run_scenarios(
        _manifest(schema_version=5), {"scenarios": [scenario]}
    )

    assert passed


def test_schema_v6_owner_restoration_bootstraps_and_recovers_locally():
    scenario = _history()
    scenario["owner_available_from"] = "2024-02-01"
    scenario["expected"] = {
        "completion_markers": [],
        "reconstructed_markers": ["past"],
        "stranded_markers": [],
        "visible_events": ["USA_test_events.2", "USA_test_events.3"],
    }

    _results, passed = run_scenarios(_manifest(), {"scenarios": [scenario]})

    assert passed


def test_schema_v6_owner_restoration_reconstructs_elapsed_current_year_event():
    scenario = _history()
    scenario["owner_available_from"] = "2024-07-01"
    scenario["expected"] = {
        "completion_markers": [],
        "reconstructed_markers": ["current", "past"],
        "stranded_markers": [],
        "visible_events": ["USA_test_events.3"],
    }

    _results, passed = run_scenarios(_manifest(), {"scenarios": [scenario]})

    assert passed


def test_outcomes_only_is_silent_and_completes_after_terminal_date():
    scenario = _history(mode="outcomes_only", start_date="2026-01-01")
    scenario["expected"] = {
        "completion_markers": ["USA_test_reconstruct_complete"],
        "reconstructed_markers": ["current", "future", "past"],
        "stranded_markers": [],
        "visible_events": [],
    }
    _results, passed = run_scenarios(_manifest(), {"scenarios": [scenario]})
    assert passed


def test_disabled_mode_never_mutates_or_delivers():
    scenario = _history(mode="disabled")
    scenario["expected"] = {
        "completion_markers": [],
        "reconstructed_markers": [],
        "stranded_markers": [],
        "visible_events": [],
    }
    _results, passed = run_scenarios(_manifest(), {"scenarios": [scenario]})
    assert passed


def test_bridge_clamps_axes_and_uses_exact_thresholds():
    for score, level in (
        (14, 1),
        (15, 2),
        (21, 2),
        (22, 3),
        (28, 3),
        (29, 4),
        (37, 4),
        (38, 5),
        (50, 5),
    ):
        scenario = {
            "name": f"bridge_{score}",
            "type": "bridge",
            "score": score,
            "expected": {
                "score": score,
                "idea": f"USA_corporate_systems_economic_integration_{level}",
            },
        }
        _results, passed = run_scenarios(_manifest(), {"scenarios": [scenario]})
        assert passed

    axis_scenario = {
        "name": "axes",
        "type": "bridge",
        "axes": [
            {"base": 9, "contribution": 3},
            {"base": 2, "contribution": -5},
            {"base": 5, "contribution": 0},
            {"base": 5, "contribution": 0},
            {"base": 5, "contribution": 0},
        ],
        "expected": {
            "effective_axes": [10, 0, 5, 5, 5],
            "applied_deltas": [1, -2, 0, 0, 0],
            "score": 25,
            "idea": "USA_corporate_systems_economic_integration_3",
        },
    }
    _results, passed = run_scenarios(_manifest(), {"scenarios": [axis_scenario]})
    assert passed


@pytest.mark.parametrize(
    ("scenario", "label"),
    [
        ({"axes": [{"base": None}]}, "axes[0].base"),
        ({"axes": [{"contribution": "invalid"}]}, "axes[0].contribution"),
        ({"score": []}, "score"),
    ],
)
def test_bridge_rejects_non_integer_values_with_scenario_error(scenario, label):
    with pytest.raises(ScenarioError) as exc_info:
        _simulate_bridge(scenario)

    assert str(exc_info.value) == f"{label} must be an integer"


def test_cli_labels_output_and_fails_on_mismatch(tmp_path, capsys):
    manifest_path = tmp_path / "manifest.json"
    scenarios_path = tmp_path / "scenarios.json"
    (tmp_path / "common/scripted_effects").mkdir(parents=True)
    manifest_path.write_text(json.dumps(_manifest()), encoding="utf-8")
    scenario = {
        "name": "bad_bridge",
        "type": "bridge",
        "score": 15,
        "expected": {"idea": "wrong"},
    }
    scenarios_path.write_text(json.dumps({"scenarios": [scenario]}), encoding="utf-8")

    result = main(
        [
            "--all",
            "--manifest",
            str(manifest_path),
            "--scenarios",
            str(scenarios_path),
            "--mod-path",
            str(tmp_path),
        ]
    )
    output = capsys.readouterr().out
    assert result == 1
    assert LABEL in output
    assert "[FAIL] bad_bridge" in output


def test_declared_cross_chain_dependency_is_reported():
    scenario = _history()
    scenario["dependencies"] = ["USA_dependency"]
    scenario["expected"] = {"dependencies": ["USA_dependency"]}

    results, passed = run_scenarios(_manifest(), {"scenarios": [scenario]})

    assert passed
    assert results[0]["actual"]["dependencies"] == ["USA_dependency"]


def test_undeclared_cross_chain_dependency_is_rejected():
    scenario = _history()
    scenario["dependencies"] = ["USA_unknown"]

    try:
        run_scenarios(_manifest(), {"scenarios": [scenario]})
    except ValueError as exc:
        assert "dependencies must exactly match dependency_order" in str(exc)
    else:
        raise AssertionError("undeclared dependency was accepted")


def test_checked_in_blackberry_usa_2009_scenario_uses_real_scripts():
    mod_root = Path(__file__).resolve().parents[2]
    manifest = json.loads(
        (mod_root / "tools/corporate_history_contract.json").read_text(encoding="utf-8")
    )
    scenarios = json.loads(
        (mod_root / "tools/corporate_history_scenarios.json").read_text(
            encoding="utf-8"
        )
    )

    results, passed = run_scenarios(
        manifest,
        scenarios,
        ["blackberry_usa_full_2009_current_year"],
        ScriptIndex.load(mod_root),
    )

    assert passed
    assert results[0]["actual"]["visible_events"] == ["blackberry_events.4"]


def test_checked_in_sov_computing_scenarios_use_real_scripts():
    mod_root = Path(__file__).resolve().parents[2]
    manifest = json.loads(
        (mod_root / "tools/corporate_history_contract.json").read_text(encoding="utf-8")
    )
    scenarios = json.loads(
        (mod_root / "tools/corporate_history_scenarios.json").read_text(
            encoding="utf-8"
        )
    )
    scenario_names = [
        scenario["name"]
        for scenario in scenarios["scenarios"]
        if scenario.get("chain") == "SOV_computing_sovereignty"
    ]
    assert scenario_names == [
        "sov_computing_full_2000_complete_lifecycle",
        "sov_computing_full_2015_current_year",
        "sov_computing_outcomes_only_2026_preterminal",
        "sov_computing_outcomes_only_2026_terminal",
        "sov_computing_disabled_2026",
    ]

    results, passed = run_scenarios(
        manifest,
        scenarios,
        scenario_names,
        ScriptIndex.load(mod_root),
    )

    assert passed
    assert [result["name"] for result in results] == scenario_names


def test_script_backed_simulation_rejects_wrong_terminal_guard(tmp_path):
    effects = tmp_path / "common/scripted_effects/test_effects.txt"
    effects.parent.mkdir(parents=True)
    effects.write_text(
        """USA_test_reconstruct_history = {
\tif = {
\t\tlimit = { date > 2024.12.31 }
\t\tset_country_flag = USA_test_reconstruct_complete
\t}
}

USA_test_schedule_current_year_events = {
\tif = {
\t\tlimit = {
\t\t\tNOT = { has_start_date < 2024.1.1 }
\t\t\thas_start_date < 2024.1.2
\t\t}
\t\tcountry_event = { id = USA_test_events.2 days = 151 }
\t}
}

USA_corporate_trigger_year_2025 = {
\tcountry_event = { id = USA_test_events.3 days = 151 }
}
""",
        encoding="utf-8",
    )
    scenario = _history(start_date="2026-01-01")

    try:
        run_scenarios(
            _manifest(),
            {"scenarios": [scenario]},
            scripts=ScriptIndex.load(tmp_path),
        )
    except ValueError as exc:
        assert "terminal guard differs from the manifest" in str(exc)
    else:
        raise AssertionError("wrong scripted terminal guard was accepted")


def test_script_index_reaches_idea_marker(tmp_path):
    effects = tmp_path / "common/scripted_effects/test_effects.txt"
    effects.parent.mkdir(parents=True)
    effects.write_text(
        """USA_test_reconstruct_history = {
\tUSA_test_apply_outcome = yes
}

USA_test_apply_outcome = {
\tadd_ideas = USA_test_outcome
}
""",
        encoding="utf-8",
    )

    scripts = ScriptIndex.load(tmp_path)

    assert scripts.reaches_marker("USA_test_reconstruct_history", "USA_test_outcome")


def test_script_backed_simulation_detects_wrong_scheduler_window(tmp_path):
    effects = tmp_path / "common/scripted_effects/test_effects.txt"
    effects.parent.mkdir(parents=True)
    effects.write_text(
        """USA_test_reconstruct_history = {
\tset_country_flag = past
\tif = {
\t\tlimit = { date > 2025.1.1 }
\t\tset_country_flag = USA_test_reconstruct_complete
\t}
}

USA_test_schedule_current_year_events = {
\tif = {
\t\tlimit = {
\t\t\tNOT = { has_start_date < 2023.1.1 }
\t\t\thas_start_date < 2023.1.2
\t\t}
\t\tcountry_event = { id = USA_test_events.2 days = 151 }
\t}
}

USA_corporate_trigger_year_2025 = {
\tcountry_event = { id = USA_test_events.3 days = 151 }
}
""",
        encoding="utf-8",
    )
    scenario = _history()
    scenario["expected"] = {
        "visible_events": ["USA_test_events.2", "USA_test_events.3"]
    }

    try:
        run_scenarios(
            _manifest(),
            {"scenarios": [scenario]},
            scripts=ScriptIndex.load(tmp_path),
        )
    except ValueError as exc:
        assert "scheduler window differs from its milestone year" in str(exc)
    else:
        raise AssertionError("wrong scripted scheduler window was accepted")
