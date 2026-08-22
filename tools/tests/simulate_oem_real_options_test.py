import json
import math
import sys
from dataclasses import replace
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))

import simulate_oem_real_options as simulator
from simulate_oem_real_options import (
    BALANCE_EVIDENCE_LABEL,
    BALANCE_SNAPSHOTS,
    CDF_KNOTS,
    FOUR_TIER_NAMES,
    FOUR_TIER_THRESHOLDS,
    LABEL,
    MAX_BOUNDED_OPTION_ABS_ERROR,
    MAX_CDF_ABS_ERROR,
    MAX_INVERSE_K_REVERSAL,
    MAX_MONOTONIC_S_REVERSAL,
    MAX_OPTION_ABS_ERROR,
    SCENARIOS,
    SQRT_T_LOOKUP,
    TIER_FAMILIES,
    TIER_NAMES,
    TIER_THRESHOLDS,
    FormulaInputs,
    approximate_black_scholes,
    approximate_discount,
    approximate_log_ratio,
    approximate_normal_cdf,
    balance_audit_result,
    evaluate_scenario,
    exact_black_scholes,
    formula_conformance_result,
    main,
    run_simulation,
    tier_analysis_result,
    tier_for_family,
)


def test_formula_reference_at_the_money():
    inputs = FormulaInputs(100.0, 100.0, 0.05, 0.2, 1)

    exact = exact_black_scholes(inputs)
    approximate = approximate_black_scholes(inputs)

    assert exact.call_value == pytest.approx(10.4505835722, abs=1e-9)
    assert approximate.call_value == pytest.approx(exact.call_value, abs=0.08)


def test_approximation_knots_match_script_contract():
    assert approximate_log_ratio(1.0) == 0.0
    assert approximate_log_ratio(0.01) == approximate_log_ratio(0.25)
    assert approximate_log_ratio(100.0) == approximate_log_ratio(4.0)
    for horizon, expected in SQRT_T_LOOKUP.items():
        result = approximate_black_scholes(
            FormulaInputs(50.0, 50.0, 0.05, 0.2, horizon)
        )
        assert result.sqrt_t == expected
    for magnitude, expected in CDF_KNOTS:
        assert approximate_normal_cdf(magnitude) == pytest.approx(expected)
        assert approximate_normal_cdf(-magnitude) == pytest.approx(1.0 - expected)
    assert approximate_normal_cdf(4.0) == pytest.approx(CDF_KNOTS[-1][1])
    assert approximate_normal_cdf(-4.0) == pytest.approx(1.0 - CDF_KNOTS[-1][1])
    assert approximate_discount(0.0, 5) == 1.0
    assert approximate_discount(0.25, 5) == pytest.approx(
        (1.0 - 1.25 / 2.0 + 1.25**2 / 12.0) / (1.0 + 1.25 / 2.0 + 1.25**2 / 12.0)
    )


def test_script_formula_constants_and_clamp_order_match_simulator():
    script_path = (
        Path(__file__).resolve().parents[2]
        / "common/scripted_effects/USA_oem_real_options_effects.txt"
    )
    script = script_path.read_text(encoding="utf-8")

    for fragment in (
        "add = { value = USA_oem_log_z_squared divide = 3 }",
        "add = { value = USA_oem_log_z_fourth divide = 5 }",
        "add = { value = USA_oem_log_z_sixth divide = 7 }",
        "add = { value = USA_oem_log_z_eighth divide = 9 }",
        "set_temp_variable = { USA_oem_sqrt_horizon = 1.41421 }",
        "set_temp_variable = { USA_oem_sqrt_horizon = 1.73205 }",
        "set_temp_variable = { USA_oem_sqrt_horizon = 2.23607 }",
        "subtract = { value = USA_oem_discount_x multiply = 0.5 }",
        "add = { value = USA_oem_discount_x_squared divide = 12 }",
        "add = { value = USA_oem_discount_x multiply = 0.5 }",
        (
            "value = microchip_plant_total\n"
            "\t\t\t\tmultiply = 0.75\n"
            "\t\t\t\tclamp = { min = 0 max = 30 }"
        ),
        (
            "value = total_unemployed_percentage_display\n"
            "\t\t\t\t\tmultiply = 500\n"
            "\t\t\t\t\tclamp = { min = 0 max = 50 }"
        ),
        (
            "\telse = {\n\t\tif = {\n"
            "\t\t\tlimit = { has_country_flag = USA_oem_real_options_initialized }\n"
            "\t\t\tclr_country_flag = USA_oem_real_options_initialized"
        ),
    ):
        assert fragment in script

    d1_start = script.index("USA_oem_option_d1 = {")
    d2_start = script.index("USA_oem_option_d2 = {")
    cdf_start = script.index("USA_oem_cdf_input = USA_oem_option_d1")
    assert d1_start < d2_start < cdf_start
    d1_block = script[d1_start:d2_start]
    d2_block = script[d2_start:cdf_start]
    assert "divide = USA_oem_sigma_sqrt_horizon" in d1_block
    assert "clamp = { min = -3 max = 3 }" in d1_block
    assert "value = USA_oem_option_d1" in d2_block
    assert "subtract = USA_oem_sigma_sqrt_horizon" in d2_block
    assert "clamp = { min = -3 max = 3 }" in d2_block

    extreme = approximate_black_scholes(FormulaInputs(100, 1, 0.25, 0.05, 1))
    assert extreme.d1 == 3.0
    assert extreme.d2 == pytest.approx(2.95)


def test_bounded_grid_has_no_non_finite_or_out_of_range_values():
    result = formula_conformance_result()

    assert result["actual"]["sample_count"] > 10_000
    assert result["actual"]["bounded"]


def test_sweep_has_no_material_monotonicity_reversals():
    actual = formula_conformance_result()["actual"]

    assert actual["max_monotonic_s_reversal"] <= MAX_MONOTONIC_S_REVERSAL
    assert actual["max_inverse_k_reversal"] <= MAX_INVERSE_K_REVERSAL


def test_maximum_errors_are_measured_and_within_declared_limits():
    result = formula_conformance_result()
    actual = result["actual"]

    assert result["passed"]
    assert actual["max_cdf_abs_error"] <= MAX_CDF_ABS_ERROR
    assert actual["max_option_abs_error"] <= MAX_OPTION_ABS_ERROR
    assert actual["max_bounded_option_abs_error"] <= MAX_BOUNDED_OPTION_ABS_ERROR
    assert actual["max_option_abs_error"] >= actual["max_bounded_option_abs_error"]


def test_tier_boundaries_are_reachable_and_perturb_by_one_tier():
    result = tier_analysis_result()

    assert result["passed"]
    assert TIER_FAMILIES["USA_oem_investment_readiness"] == (
        TIER_THRESHOLDS,
        TIER_NAMES,
    )
    assert TIER_FAMILIES["USA_oem_innovation_diffusion"] == (
        FOUR_TIER_THRESHOLDS,
        FOUR_TIER_NAMES,
    )
    for family, (thresholds, names) in TIER_FAMILIES.items():
        actual = result["actual"]["families"][family]
        assert actual["thresholds"] == list(thresholds)
        assert actual["reachable_tiers"] == list(names)
        for threshold in thresholds:
            below = names.index(tier_for_family(family, threshold - 0.001))
            above = names.index(tier_for_family(family, threshold + 0.001))
            assert above - below == 1


def test_high_volatility_preserves_option_value_but_reduces_readiness():
    speculative = evaluate_scenario("speculative_boom")
    strategic = evaluate_scenario("strategic_boom")

    assert (
        speculative["USA_oem_option_underlying_value"]
        == strategic["USA_oem_option_underlying_value"]
    )
    assert (
        speculative["USA_oem_option_irreversible_cost"]
        == strategic["USA_oem_option_irreversible_cost"]
    )
    assert (
        speculative["USA_oem_option_discount_rate"]
        == strategic["USA_oem_option_discount_rate"]
    )
    assert speculative["USA_oem_option_horizon"] == strategic["USA_oem_option_horizon"]
    assert (
        speculative["USA_oem_option_volatility"]
        > strategic["USA_oem_option_volatility"]
    )
    assert speculative["USA_oem_option_value"] >= strategic["USA_oem_option_value"]
    assert (
        speculative["USA_oem_investment_readiness"]
        < strategic["USA_oem_investment_readiness"]
    )


@pytest.mark.parametrize(
    ("unemployment_rate", "expected_contribution"), ((0.05, 25.0), (0.2, 50.0))
)
def test_labor_displacement_normalizes_fractional_unemployment(
    unemployment_rate, expected_contribution
):
    scenario = replace(
        SCENARIOS["historical_default"],
        name="unemployment_normalization",
        unemployment_rate=unemployment_rate,
    )
    simulator.SCENARIOS[scenario.name] = scenario
    try:
        actual = evaluate_scenario(scenario.name)
    finally:
        del simulator.SCENARIOS[scenario.name]

    automation = actual["USA_oem_automation_pressure"]
    assert actual["USA_oem_labor_displacement_pressure"] == pytest.approx(
        0.5 * automation + expected_contribution
    )


@pytest.mark.parametrize("name", tuple(SCENARIOS))
def test_all_named_scenarios_are_present_and_bounded(name):
    expected_names = {
        "historical_default",
        "open_and_interoperable",
        "integrated_but_closed",
        "fragmented_import_dependent",
        "speculative_boom",
        "infrastructure_bottleneck",
        "treasury_constrained_recession",
        "strategic_boom",
    }
    actual = evaluate_scenario(name)

    assert set(SCENARIOS) == expected_names
    assert actual["USA_oem_option_value_normalized"] == actual["USA_oem_option_value"]
    for key in (
        "USA_oem_option_value",
        "USA_oem_investment_readiness",
        "USA_oem_innovation_diffusion",
        "USA_oem_industrial_depth",
        "USA_oem_compute_infrastructure_demand",
        "USA_oem_compute_infrastructure_capacity",
        "USA_oem_infrastructure_pressure",
        "USA_oem_automation_pressure",
        "USA_oem_labor_displacement_pressure",
        "USA_oem_high_skill_labor_demand",
    ):
        assert 0.0 <= actual[key] <= 100.0


def test_off_is_inert_and_full_matches_outcomes_only():
    full = evaluate_scenario("historical_default", "full")
    outcomes = evaluate_scenario("historical_default", "outcomes_only")
    off = evaluate_scenario("historical_default", "off")

    assert {key: value for key, value in full.items() if key != "mode"} == {
        key: value for key, value in outcomes.items() if key != "mode"
    }
    assert off["inert"]
    assert off["tiers"] == {}
    assert not any(
        off[key]
        for key in (
            "USA_oem_option_underlying_value",
            "USA_oem_option_irreversible_cost",
            "USA_oem_option_discount_rate",
            "USA_oem_option_volatility",
            "USA_oem_option_horizon",
            "USA_oem_option_call_value",
            "USA_oem_option_value",
            "USA_oem_innovation_diffusion",
            "USA_oem_industrial_depth",
            "USA_oem_compute_infrastructure_demand",
            "USA_oem_compute_infrastructure_capacity",
            "USA_oem_infrastructure_pressure",
            "USA_oem_investment_readiness",
            "USA_oem_automation_pressure",
            "USA_oem_labor_displacement_pressure",
            "USA_oem_high_skill_labor_demand",
            "USA_oem_automation_pressure_display",
            "USA_oem_labor_displacement_pressure_display",
            "USA_oem_high_skill_labor_demand_display",
        )
    )


def test_historical_balance_snapshots_are_static_model_evidence_within_caps():
    result = balance_audit_result()

    assert result["evidence_label"] == BALANCE_EVIDENCE_LABEL
    assert [snapshot.year for snapshot in BALANCE_SNAPSHOTS] == [
        2005,
        2010,
        2015,
        2020,
        2026,
    ]
    assert result["passed"]
    for row in result["actual"]["snapshots"]:
        assert set(row) == {
            "year",
            "assumption",
            "existing_outcome",
            "new_dynamic",
            "program",
            "aggregate",
            "within_caps",
        }
        assert all(row["within_caps"].values())
    stress = result["actual"]["snapshots"][-1]
    assert stress["aggregate"]["energy_use_modifier_microchip_plant"] == pytest.approx(
        0.13
    )
    assert stress["within_caps"]["energy_use_modifier_microchip_plant"]
    assert stress["aggregate"]["country_productivity_growth_modifier"] == pytest.approx(
        0.03
    )


def test_cli_json_schema_and_success_exit(capsys):
    result = main(["--scenario", "historical_default", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert result == 0
    assert set(payload) == {"label", "passed", "results"}
    assert payload["label"] == LABEL
    assert payload["passed"]
    assert [entry["name"] for entry in payload["results"]] == ["historical_default"]


def test_cli_returns_two_for_bad_selection(capsys):
    result = main(["--scenario", "not_a_scenario"])

    assert result == 2
    assert "configuration error" in capsys.readouterr().err


def test_cli_returns_two_for_bad_argument(capsys):
    result = main(["--not-an-option"])

    assert result == 2
    assert "configuration error" in capsys.readouterr().err


def test_cli_returns_one_for_quantitative_failure(monkeypatch, capsys):
    monkeypatch.setattr(simulator, "MAX_CDF_ABS_ERROR", -1.0)

    result = main(["--json"])
    payload = json.loads(capsys.readouterr().out)

    assert result == 1
    assert not payload["passed"]


def test_no_argument_run_covers_formula_scenarios_modes_and_balance():
    results, passed = run_simulation()
    names = {result["name"] for result in results}

    assert passed
    assert set(SCENARIOS) <= names
    assert {
        "formula_conformance",
        "tier_reachability",
        "scenario_relationships",
        "mode_parity",
        "historical_balance_snapshots",
    } <= names
    assert math.isfinite(
        next(
            result["actual"]["max_option_abs_error"]
            for result in results
            if result["name"] == "formula_conformance"
        )
    )
