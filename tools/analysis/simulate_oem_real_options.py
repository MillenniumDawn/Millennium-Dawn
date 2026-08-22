#!/usr/bin/env python3
"""Run the deterministic USA OEM real-options balance model.

Scenario-only scaling uses S = 10 + 4*demand + 3*innovation + 2*capital,
K = 10 + 4*fragmentation + 3*imports + 2*debt - 2*capital,
r = .01 + .012*interest + .006*debt, and
sigma = .05 + .06*uncertainty + .025*fragmentation. Those provisional
balance mappings are isolated from the formula-conformance sweep.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict, dataclass
from itertools import product
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

LABEL = "OEM REAL OPTIONS STATIC SIMULATION"
BALANCE_EVIDENCE_LABEL = "BALANCE-MODEL EVIDENCE (NOT RUNTIME)"

S_MIN = 1.0
S_MAX = 100.0
K_MIN = 1.0
K_MAX = 100.0
R_MIN = 0.0
R_MAX = 0.25
SIGMA_MIN = 0.05
SIGMA_MAX = 1.0
T_MIN = 1
T_MAX = 5
RATIO_MIN = 0.25
RATIO_MAX = 4.0
DISCOUNT_X_MAX = 1.25

SQRT_T_LOOKUP = {
    1: 1.0,
    2: 1.41421,
    3: 1.73205,
    4: 2.0,
    5: 2.23607,
}
CDF_KNOTS = (
    (0.0, 0.5),
    (0.5, 0.69146),
    (1.0, 0.84134),
    (1.5, 0.93319),
    (2.0, 0.97725),
    (2.5, 0.99379),
    (3.0, 0.99865),
)

MAX_CDF_ABS_ERROR = 0.0075
MAX_OPTION_ABS_ERROR = 5.0
MAX_BOUNDED_OPTION_ABS_ERROR = 1.35
MAX_MONOTONIC_S_REVERSAL = 0.05
MAX_INVERSE_K_REVERSAL = 0.10

TIER_THRESHOLDS = (20.0, 40.0, 60.0, 80.0)
TIER_NAMES = ("tier_1", "tier_2", "tier_3", "tier_4", "tier_5")
FOUR_TIER_THRESHOLDS = (25.0, 50.0, 75.0)
FOUR_TIER_NAMES = ("tier_1", "tier_2", "tier_3", "tier_4")
TIER_FAMILIES = {
    "USA_oem_investment_readiness": (TIER_THRESHOLDS, TIER_NAMES),
    "USA_oem_innovation_diffusion": (FOUR_TIER_THRESHOLDS, FOUR_TIER_NAMES),
    "USA_oem_industrial_depth": (FOUR_TIER_THRESHOLDS, FOUR_TIER_NAMES),
    "USA_oem_infrastructure_pressure": (TIER_THRESHOLDS, TIER_NAMES),
}
PERSISTENT_OUTPUT_KEYS = (
    "USA_oem_option_underlying_value",
    "USA_oem_option_irreversible_cost",
    "USA_oem_option_discount_rate",
    "USA_oem_option_volatility",
    "USA_oem_option_horizon",
    "USA_oem_option_call_value",
    "USA_oem_option_value",
    "USA_oem_option_value_normalized",
    "USA_oem_innovation_diffusion",
    "USA_oem_industrial_depth",
    "USA_oem_compute_infrastructure_demand",
    "USA_oem_compute_infrastructure_capacity",
    "USA_oem_infrastructure_pressure",
    "USA_oem_investment_readiness",
    "USA_oem_automation_pressure",
    "USA_oem_labor_displacement_pressure",
    "USA_oem_high_skill_labor_demand",
    "USA_oem_option_value_display",
    "USA_oem_option_value_normalized_display",
    "USA_oem_innovation_diffusion_display",
    "USA_oem_industrial_depth_display",
    "USA_oem_compute_infrastructure_demand_display",
    "USA_oem_compute_infrastructure_capacity_display",
    "USA_oem_infrastructure_pressure_display",
    "USA_oem_investment_readiness_display",
    "USA_oem_automation_pressure_display",
    "USA_oem_labor_displacement_pressure_display",
    "USA_oem_high_skill_labor_demand_display",
)

S_BASE = 10.0
S_DEMAND_WEIGHT = 4.0
S_INNOVATION_WEIGHT = 3.0
S_CAPITAL_WEIGHT = 2.0
K_BASE = 10.0
K_FRAGMENTATION_WEIGHT = 4.0
K_IMPORT_WEIGHT = 3.0
K_DEBT_WEIGHT = 2.0
K_CAPITAL_WEIGHT = -2.0
R_BASE = 0.01
R_INTEREST_WEIGHT = 0.012
R_DEBT_WEIGHT = 0.006
SIGMA_BASE = 0.05
SIGMA_UNCERTAINTY_WEIGHT = 0.06
SIGMA_FRAGMENTATION_WEIGHT = 0.025

SWEEP_S = (1.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0)
SWEEP_K = SWEEP_S
SWEEP_R = (0.0, 0.01, 0.05, 0.1, 0.25)
SWEEP_SIGMA = (0.05, 0.2, 0.5, 1.0)
SWEEP_T = (1, 2, 3, 4, 5)


class SimulationError(ValueError):
    """Raised when simulator configuration or selection is invalid."""


@dataclass(frozen=True)
class FormulaInputs:
    s: float
    k: float
    r: float
    sigma: float
    t: int


@dataclass(frozen=True)
class FormulaResult:
    inputs: FormulaInputs
    ratio: float
    log_ratio: float
    sqrt_t: float
    discount: float
    d1: float
    d2: float
    n1: float
    n2: float
    call_value: float
    normalized_value: float


@dataclass(frozen=True)
class EconomicScenario:
    name: str
    openness: float
    integration: float
    innovation: float
    capital_access: float
    compute_capacity: float
    demand_signal: float
    fragmentation: float
    import_dependence: float
    debt_burden: float
    interest_pressure: float
    uncertainty: float
    horizon: int
    unemployment_rate: float = 0.05

    def formula_inputs(self) -> FormulaInputs:
        drivers = self.drivers()
        return FormulaInputs(
            s=S_BASE
            + S_DEMAND_WEIGHT * drivers["demand_signal"]
            + S_INNOVATION_WEIGHT * drivers["innovation"]
            + S_CAPITAL_WEIGHT * drivers["capital_access"],
            k=K_BASE
            + K_FRAGMENTATION_WEIGHT * drivers["fragmentation"]
            + K_IMPORT_WEIGHT * drivers["import_dependence"]
            + K_DEBT_WEIGHT * drivers["debt_burden"]
            + K_CAPITAL_WEIGHT * drivers["capital_access"],
            r=R_BASE
            + R_INTEREST_WEIGHT * drivers["interest_pressure"]
            + R_DEBT_WEIGHT * drivers["debt_burden"],
            sigma=SIGMA_BASE
            + SIGMA_UNCERTAINTY_WEIGHT * drivers["uncertainty"]
            + SIGMA_FRAGMENTATION_WEIGHT * drivers["fragmentation"],
            t=self.horizon,
        )

    def drivers(self) -> Dict[str, float]:
        return {
            "openness": _clamp(self.openness, 0.0, 10.0),
            "integration": _clamp(self.integration, 0.0, 10.0),
            "innovation": _clamp(self.innovation, 0.0, 10.0),
            "capital_access": _clamp(self.capital_access, 0.0, 10.0),
            "compute_capacity": _clamp(self.compute_capacity, 0.0, 10.0),
            "demand_signal": _clamp(self.demand_signal, 0.0, 10.0),
            "fragmentation": _clamp(self.fragmentation, 0.0, 10.0),
            "import_dependence": _clamp(self.import_dependence, 0.0, 10.0),
            "debt_burden": _clamp(self.debt_burden, 0.0, 10.0),
            "interest_pressure": _clamp(self.interest_pressure, 0.0, 10.0),
            "uncertainty": _clamp(self.uncertainty, 0.0, 10.0),
            "unemployment_rate": _clamp(self.unemployment_rate, 0.0, 1.0),
        }

    def indicators(self) -> Dict[str, float]:
        drivers = self.drivers()
        readiness = 2.5 * (
            drivers["openness"]
            + drivers["integration"]
            + drivers["innovation"]
            + drivers["capital_access"]
        )
        diffusion = 5.0 * (drivers["openness"] + drivers["integration"])
        depth = 5.0 * (drivers["innovation"] + drivers["compute_capacity"])
        demand = 10.0 * drivers["demand_signal"]
        capacity = 10.0 * drivers["compute_capacity"]
        pressure = (
            0.6 * demand
            + 4.0 * drivers["fragmentation"]
            + 3.0 * drivers["import_dependence"]
            - 0.5 * capacity
        )
        return {
            "readiness": _clamp(readiness, 0.0, 100.0),
            "diffusion": _clamp(diffusion, 0.0, 100.0),
            "depth": _clamp(depth, 0.0, 100.0),
            "demand": _clamp(demand, 0.0, 100.0),
            "capacity": _clamp(capacity, 0.0, 100.0),
            "pressure": _clamp(pressure, 0.0, 100.0),
        }


@dataclass(frozen=True)
class BalanceSnapshot:
    year: int
    assumption: str
    existing_outcome: Mapping[str, float]
    new_dynamic: Mapping[str, float]
    program: Mapping[str, float]


SCENARIOS = {
    scenario.name: scenario
    for scenario in (
        EconomicScenario("historical_default", 5, 5, 5, 5, 5, 5, 5, 5, 4, 4, 4, 3),
        EconomicScenario("open_and_interoperable", 9, 8, 7, 7, 7, 7, 2, 3, 3, 3, 3, 4),
        EconomicScenario("integrated_but_closed", 2, 9, 7, 7, 8, 7, 4, 2, 3, 3, 4, 4),
        EconomicScenario(
            "fragmented_import_dependent", 4, 2, 3, 3, 3, 6, 9, 9, 6, 6, 8, 3
        ),
        EconomicScenario("speculative_boom", 3, 2, 8, 4, 4, 8, 7, 0, 4, 4, 8, 4),
        EconomicScenario(
            "infrastructure_bottleneck", 6, 6, 8, 6, 2, 9, 5, 6, 4, 4, 6, 3
        ),
        EconomicScenario(
            "treasury_constrained_recession", 4, 4, 4, 1, 5, 2, 6, 7, 9, 9, 8, 2
        ),
        EconomicScenario("strategic_boom", 9, 9, 8, 4, 8, 8, 4, 4, 4, 4, 2, 4),
    )
}

BALANCE_CAPS = {
    "corporate_tax_income_multiplier_modifier": 0.10,
    "investment_cost_modifier": 0.10,
    "receiving_investment_cost_modifier": 0.10,
    "investment_duration_modifier": 0.05,
    "receiving_investment_duration_modifier": 0.05,
    "bureaucracy_cost_multiplier_modifier": 0.10,
    "country_productivity_growth_modifier": 0.03,
    "offices_productivity": 0.20,
    "production_speed_offices_factor": 0.10,
    "research_speed_factor": 0.15,
    "production_factory_efficiency_gain_factor": 0.20,
    "production_factory_max_efficiency_factor": 0.30,
    "industrial_capacity_factory": 0.15,
    "microchip_plant_productivity_modifier": 0.15,
    "production_speed_microchip_plant_factor": 0.20,
    "production_speed_industrial_infrastructure_factor": 0.15,
    "local_resources_microchips_factor": 0.05,
    "industry_chip_consumption_modifier": 0.20,
    "civilian_chip_consumption_modifier": 0.30,
    "microchip_export_multiplier_modifier": 0.15,
    "energy_use_modifier_microchip_plant": 0.15,
    "energy_use_modifier_offices": 0.05,
    "consumer_goods_factor": 0.05,
    "cyber_defense_rating_modifier": 10.0,
}


def _modifier_map(**values: float) -> Dict[str, float]:
    unknown = set(values) - set(BALANCE_CAPS)
    if unknown:
        raise SimulationError(
            f"unknown balance modifiers: {', '.join(sorted(unknown))}"
        )
    return {modifier: values.get(modifier, 0.0) for modifier in BALANCE_CAPS}


PROGRAM_ENVELOPE = _modifier_map(
    receiving_investment_cost_modifier=-0.03,
    bureaucracy_cost_multiplier_modifier=0.05,
    country_productivity_growth_modifier=0.02,
    production_speed_offices_factor=0.07,
    research_speed_factor=0.03,
    production_speed_microchip_plant_factor=0.10,
    production_speed_industrial_infrastructure_factor=0.08,
    local_resources_microchips_factor=0.03,
    industry_chip_consumption_modifier=0.08,
    civilian_chip_consumption_modifier=0.03,
    energy_use_modifier_microchip_plant=0.08,
    consumer_goods_factor=0.01,
    cyber_defense_rating_modifier=2.0,
)


BALANCE_SNAPSHOTS = (
    BalanceSnapshot(
        2005,
        "year-end Outcomes Only route; representative T2/T3/T2/T3 dynamics; all-program envelope",
        _modifier_map(
            corporate_tax_income_multiplier_modifier=0.02,
            investment_cost_modifier=-0.02,
            receiving_investment_cost_modifier=-0.02,
            offices_productivity=0.03,
            civilian_chip_consumption_modifier=0.03,
        ),
        _modifier_map(
            investment_duration_modifier=0.025,
            receiving_investment_duration_modifier=0.025,
            bureaucracy_cost_multiplier_modifier=0.01,
            country_productivity_growth_modifier=0.005,
            offices_productivity=0.01,
            research_speed_factor=0.005,
        ),
        PROGRAM_ENVELOPE,
    ),
    BalanceSnapshot(
        2010,
        "year-end Outcomes Only route; representative T2/T3/T2/T3 dynamics; all-program envelope",
        _modifier_map(
            corporate_tax_income_multiplier_modifier=0.02,
            investment_cost_modifier=-0.02,
            receiving_investment_cost_modifier=-0.02,
            offices_productivity=0.03,
            civilian_chip_consumption_modifier=0.04,
        ),
        _modifier_map(
            investment_duration_modifier=0.025,
            receiving_investment_duration_modifier=0.025,
            bureaucracy_cost_multiplier_modifier=0.01,
            country_productivity_growth_modifier=0.005,
            offices_productivity=0.01,
            research_speed_factor=0.005,
        ),
        PROGRAM_ENVELOPE,
    ),
    BalanceSnapshot(
        2015,
        "year-end Outcomes Only route; representative T2/T3/T2/T3 dynamics; all-program envelope",
        _modifier_map(
            offices_productivity=0.03,
            civilian_chip_consumption_modifier=0.04,
        ),
        _modifier_map(
            investment_duration_modifier=0.025,
            receiving_investment_duration_modifier=0.025,
            bureaucracy_cost_multiplier_modifier=0.01,
            country_productivity_growth_modifier=0.005,
            offices_productivity=0.01,
            research_speed_factor=0.005,
        ),
        PROGRAM_ENVELOPE,
    ),
    BalanceSnapshot(
        2020,
        "year-end Outcomes Only route; representative T2/T3/T2/T4 dynamics; all-program envelope",
        _modifier_map(
            corporate_tax_income_multiplier_modifier=0.02,
            investment_cost_modifier=-0.02,
            receiving_investment_cost_modifier=-0.02,
            offices_productivity=0.02,
            civilian_chip_consumption_modifier=0.05,
            consumer_goods_factor=0.01,
        ),
        _modifier_map(
            investment_duration_modifier=0.025,
            receiving_investment_duration_modifier=0.025,
            bureaucracy_cost_multiplier_modifier=0.01,
            country_productivity_growth_modifier=0.005,
            offices_productivity=0.01,
            research_speed_factor=0.005,
            energy_use_modifier_microchip_plant=0.025,
            energy_use_modifier_offices=0.02,
            consumer_goods_factor=0.005,
        ),
        PROGRAM_ENVELOPE,
    ),
    BalanceSnapshot(
        2026,
        "year-end Outcomes Only permanent stack; maximum tier from every dynamic family; all-program envelope",
        _modifier_map(
            corporate_tax_income_multiplier_modifier=0.05,
            investment_cost_modifier=-0.05,
            receiving_investment_cost_modifier=-0.05,
            offices_productivity=0.14,
            research_speed_factor=0.09,
            production_factory_efficiency_gain_factor=0.15,
            production_factory_max_efficiency_factor=0.23,
            industrial_capacity_factory=0.10,
            microchip_plant_productivity_modifier=0.10,
            production_speed_microchip_plant_factor=0.05,
            industry_chip_consumption_modifier=-0.13,
            civilian_chip_consumption_modifier=0.24,
            microchip_export_multiplier_modifier=0.10,
            consumer_goods_factor=-0.03,
            cyber_defense_rating_modifier=6.0,
        ),
        _modifier_map(
            investment_duration_modifier=-0.05,
            receiving_investment_duration_modifier=-0.05,
            bureaucracy_cost_multiplier_modifier=-0.02,
            country_productivity_growth_modifier=0.01,
            offices_productivity=0.02,
            research_speed_factor=0.01,
            production_speed_microchip_plant_factor=0.05,
            production_speed_industrial_infrastructure_factor=0.05,
            production_factory_max_efficiency_factor=0.02,
            energy_use_modifier_microchip_plant=0.05,
            energy_use_modifier_offices=0.04,
            consumer_goods_factor=0.01,
        ),
        PROGRAM_ENVELOPE,
    ),
)


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def clamp_inputs(inputs: FormulaInputs) -> FormulaInputs:
    """Apply the game-side safety bounds before any derived calculation."""
    values = (inputs.s, inputs.k, inputs.r, inputs.sigma)
    if not all(math.isfinite(value) for value in values):
        raise SimulationError("formula inputs must be finite")
    if type(inputs.t) is not int:
        raise SimulationError("T must be an integer")
    return FormulaInputs(
        _clamp(inputs.s, S_MIN, S_MAX),
        _clamp(inputs.k, K_MIN, K_MAX),
        _clamp(inputs.r, R_MIN, R_MAX),
        _clamp(inputs.sigma, SIGMA_MIN, SIGMA_MAX),
        max(T_MIN, min(T_MAX, inputs.t)),
    )


def approximate_log_ratio(ratio: float) -> float:
    ratio = _clamp(ratio, RATIO_MIN, RATIO_MAX)
    z = (ratio - 1.0) / (ratio + 1.0)
    z2 = z * z
    z4 = z2 * z2
    z6 = z4 * z2
    z8 = z4 * z4
    return 2.0 * z * (1.0 + z2 / 3.0 + z4 / 5.0 + z6 / 7.0 + z8 / 9.0)


def approximate_discount(r: float, t: int) -> float:
    x = _clamp(r * t, 0.0, DISCOUNT_X_MAX)
    x2 = x * x
    numerator = 1.0 - x / 2.0 + x2 / 12.0
    denominator = 1.0 + x / 2.0 + x2 / 12.0
    return numerator / denominator


def approximate_normal_cdf(value: float) -> float:
    magnitude = abs(value)
    if magnitude >= CDF_KNOTS[-1][0]:
        positive = CDF_KNOTS[-1][1]
    else:
        positive = CDF_KNOTS[0][1]
        for (lower_x, lower_y), (upper_x, upper_y) in zip(CDF_KNOTS, CDF_KNOTS[1:]):
            if lower_x <= magnitude <= upper_x:
                fraction = (magnitude - lower_x) / (upper_x - lower_x)
                positive = lower_y + fraction * (upper_y - lower_y)
                break
    return positive if value >= 0.0 else 1.0 - positive


def exact_normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def approximate_black_scholes(inputs: FormulaInputs) -> FormulaResult:
    bounded = clamp_inputs(inputs)
    ratio = _clamp(bounded.s / bounded.k, RATIO_MIN, RATIO_MAX)
    log_ratio = approximate_log_ratio(ratio)
    sqrt_t = SQRT_T_LOOKUP[bounded.t]
    sigma_sqrt_t = bounded.sigma * sqrt_t
    d1 = _clamp(
        (log_ratio + (bounded.r + bounded.sigma * bounded.sigma / 2.0) * bounded.t)
        / sigma_sqrt_t,
        -3.0,
        3.0,
    )
    d2 = _clamp(d1 - sigma_sqrt_t, -3.0, 3.0)
    n1 = approximate_normal_cdf(d1)
    n2 = approximate_normal_cdf(d2)
    discount = approximate_discount(bounded.r, bounded.t)
    call_value = _clamp(bounded.s * n1 - bounded.k * discount * n2, 0.0, bounded.s)
    return FormulaResult(
        inputs=bounded,
        ratio=ratio,
        log_ratio=log_ratio,
        sqrt_t=sqrt_t,
        discount=discount,
        d1=d1,
        d2=d2,
        n1=n1,
        n2=n2,
        call_value=call_value,
        normalized_value=_clamp(call_value, 0.0, 100.0),
    )


def exact_black_scholes(
    inputs: FormulaInputs, bounded_ratio: bool = False
) -> FormulaResult:
    bounded = clamp_inputs(inputs)
    raw_ratio = bounded.s / bounded.k
    ratio = _clamp(raw_ratio, RATIO_MIN, RATIO_MAX) if bounded_ratio else raw_ratio
    log_ratio = math.log(ratio)
    sqrt_t = math.sqrt(bounded.t)
    sigma_sqrt_t = bounded.sigma * sqrt_t
    d1 = (
        log_ratio + (bounded.r + bounded.sigma * bounded.sigma / 2.0) * bounded.t
    ) / sigma_sqrt_t
    d2 = d1 - sigma_sqrt_t
    n1 = exact_normal_cdf(d1)
    n2 = exact_normal_cdf(d2)
    discount = math.exp(-bounded.r * bounded.t)
    call_value = _clamp(bounded.s * n1 - bounded.k * discount * n2, 0.0, bounded.s)
    return FormulaResult(
        inputs=bounded,
        ratio=ratio,
        log_ratio=log_ratio,
        sqrt_t=sqrt_t,
        discount=discount,
        d1=d1,
        d2=d2,
        n1=n1,
        n2=n2,
        call_value=call_value,
        normalized_value=_clamp(call_value, 0.0, 100.0),
    )


def tier_for_score(
    score: float,
    thresholds: Sequence[float] = TIER_THRESHOLDS,
    names: Sequence[str] = TIER_NAMES,
) -> str:
    bounded = _clamp(score, 0.0, 100.0)
    index = sum(bounded >= threshold for threshold in thresholds)
    return names[index]


def tier_for_family(family: str, score: float) -> str:
    if family not in TIER_FAMILIES:
        raise SimulationError(f"unknown tier family: {family}")
    thresholds, names = TIER_FAMILIES[family]
    return tier_for_score(score, thresholds, names)


def evaluate_scenario(name: str, mode: str = "full") -> Dict[str, object]:
    if name not in SCENARIOS:
        raise SimulationError(f"unknown scenario: {name}")
    if mode not in ("full", "outcomes_only", "off"):
        raise SimulationError(f"unknown mode: {mode}")
    if mode == "off":
        return {
            "mode": mode,
            "inert": True,
            **{key: 0.0 for key in PERSISTENT_OUTPUT_KEYS},
            "tiers": {},
        }

    scenario = SCENARIOS[name]
    result = approximate_black_scholes(scenario.formula_inputs())
    indicators = scenario.indicators()
    automation_pressure = _clamp(
        0.5 * indicators["depth"]
        + 0.3 * indicators["diffusion"]
        + 0.2 * indicators["demand"],
        0.0,
        100.0,
    )
    unemployment_displacement = _clamp(
        500.0 * scenario.drivers()["unemployment_rate"], 0.0, 50.0
    )
    labor_displacement_pressure = _clamp(
        0.5 * automation_pressure + unemployment_displacement,
        0.0,
        100.0,
    )
    high_skill_labor_demand = _clamp(
        0.45 * indicators["depth"]
        + 0.25 * indicators["diffusion"]
        + 0.3 * indicators["demand"],
        0.0,
        100.0,
    )
    outputs = {
        "USA_oem_option_underlying_value": result.inputs.s,
        "USA_oem_option_irreversible_cost": result.inputs.k,
        "USA_oem_option_discount_rate": result.inputs.r,
        "USA_oem_option_volatility": result.inputs.sigma,
        "USA_oem_option_horizon": result.inputs.t,
        "USA_oem_option_call_value": result.call_value,
        "USA_oem_option_value": result.normalized_value,
        "USA_oem_option_value_normalized": result.normalized_value,
        "USA_oem_innovation_diffusion": indicators["diffusion"],
        "USA_oem_industrial_depth": indicators["depth"],
        "USA_oem_compute_infrastructure_demand": indicators["demand"],
        "USA_oem_compute_infrastructure_capacity": indicators["capacity"],
        "USA_oem_infrastructure_pressure": indicators["pressure"],
        "USA_oem_investment_readiness": indicators["readiness"],
        "USA_oem_automation_pressure": automation_pressure,
        "USA_oem_labor_displacement_pressure": labor_displacement_pressure,
        "USA_oem_high_skill_labor_demand": high_skill_labor_demand,
        "USA_oem_option_value_display": round(result.normalized_value),
        "USA_oem_option_value_normalized_display": round(result.normalized_value),
        "USA_oem_innovation_diffusion_display": round(indicators["diffusion"]),
        "USA_oem_industrial_depth_display": round(indicators["depth"]),
        "USA_oem_compute_infrastructure_demand_display": round(indicators["demand"]),
        "USA_oem_compute_infrastructure_capacity_display": round(
            indicators["capacity"]
        ),
        "USA_oem_infrastructure_pressure_display": round(indicators["pressure"]),
        "USA_oem_investment_readiness_display": round(indicators["readiness"]),
        "USA_oem_automation_pressure_display": round(automation_pressure),
        "USA_oem_labor_displacement_pressure_display": round(
            labor_displacement_pressure
        ),
        "USA_oem_high_skill_labor_demand_display": round(high_skill_labor_demand),
    }
    tiers = {
        family: tier_for_family(family, outputs[family]) for family in TIER_FAMILIES
    }
    return {
        "mode": mode,
        "inert": False,
        **outputs,
        "tiers": tiers,
    }


def _grid_metrics() -> Dict[str, object]:
    values: Dict[Tuple[float, float, float, float, int], float] = {}
    bounded = True
    max_option_error = -1.0
    max_option_error_at: Dict[str, object] = {}
    max_bounded_option_error = -1.0
    max_bounded_option_error_at: Dict[str, object] = {}
    reachable_tiers = set()

    for point in product(SWEEP_S, SWEEP_K, SWEEP_R, SWEEP_SIGMA, SWEEP_T):
        inputs = FormulaInputs(*point)
        approximate = approximate_black_scholes(inputs)
        exact = exact_black_scholes(inputs)
        bounded_exact = exact_black_scholes(inputs, bounded_ratio=True)
        values[point] = approximate.normalized_value
        reachable_tiers.add(tier_for_score(approximate.normalized_value))
        bounded = bounded and all(
            (
                math.isfinite(approximate.normalized_value),
                0.0 <= approximate.normalized_value <= 100.0,
                0.0 <= approximate.call_value <= approximate.inputs.s,
                0.0 <= approximate.n1 <= 1.0,
                0.0 <= approximate.n2 <= 1.0,
                0.0 <= approximate.discount <= 1.0,
            )
        )
        option_error = abs(approximate.call_value - exact.call_value)
        if option_error > max_option_error:
            max_option_error = option_error
            max_option_error_at = asdict(inputs)
        bounded_option_error = abs(approximate.call_value - bounded_exact.call_value)
        if bounded_option_error > max_bounded_option_error:
            max_bounded_option_error = bounded_option_error
            max_bounded_option_error_at = asdict(inputs)

    monotonic_s_violations = 0
    max_monotonic_s_reversal = 0.0
    for k, r, sigma, t in product(SWEEP_K, SWEEP_R, SWEEP_SIGMA, SWEEP_T):
        sequence = [values[(s, k, r, sigma, t)] for s in SWEEP_S]
        for previous, current in zip(sequence, sequence[1:]):
            reversal = previous - current
            if reversal > 1e-9:
                monotonic_s_violations += 1
                max_monotonic_s_reversal = max(max_monotonic_s_reversal, reversal)

    inverse_k_violations = 0
    max_inverse_k_reversal = 0.0
    for s, r, sigma, t in product(SWEEP_S, SWEEP_R, SWEEP_SIGMA, SWEEP_T):
        sequence = [values[(s, k, r, sigma, t)] for k in SWEEP_K]
        for previous, current in zip(sequence, sequence[1:]):
            reversal = current - previous
            if reversal > 1e-9:
                inverse_k_violations += 1
                max_inverse_k_reversal = max(max_inverse_k_reversal, reversal)

    max_cdf_error = -1.0
    max_cdf_error_at = 0.0
    for index in range(-6000, 6001):
        value = index * 0.001
        error = abs(approximate_normal_cdf(value) - exact_normal_cdf(value))
        if error > max_cdf_error:
            max_cdf_error = error
            max_cdf_error_at = value

    return {
        "sample_count": len(values),
        "bounded": bounded,
        "max_cdf_abs_error": max_cdf_error,
        "max_cdf_abs_error_at": max_cdf_error_at,
        "max_option_abs_error": max_option_error,
        "max_option_abs_error_at": max_option_error_at,
        "max_bounded_option_abs_error": max_bounded_option_error,
        "max_bounded_option_abs_error_at": max_bounded_option_error_at,
        "monotonic_s_violations": monotonic_s_violations,
        "max_monotonic_s_reversal": max_monotonic_s_reversal,
        "inverse_k_violations": inverse_k_violations,
        "max_inverse_k_reversal": max_inverse_k_reversal,
        "reachable_tiers": [tier for tier in TIER_NAMES if tier in reachable_tiers],
    }


def formula_conformance_result() -> Dict[str, object]:
    metrics = _grid_metrics()
    passed = bool(
        metrics["bounded"]
        and metrics["max_monotonic_s_reversal"] <= MAX_MONOTONIC_S_REVERSAL
        and metrics["max_inverse_k_reversal"] <= MAX_INVERSE_K_REVERSAL
        and metrics["max_cdf_abs_error"] <= MAX_CDF_ABS_ERROR
        and metrics["max_option_abs_error"] <= MAX_OPTION_ABS_ERROR
        and metrics["max_bounded_option_abs_error"] <= MAX_BOUNDED_OPTION_ABS_ERROR
    )
    return {
        "name": "formula_conformance",
        "kind": "quantitative",
        "passed": passed,
        "actual": metrics,
        "limits": {
            "max_cdf_abs_error": MAX_CDF_ABS_ERROR,
            "max_option_abs_error": MAX_OPTION_ABS_ERROR,
            "max_bounded_option_abs_error": MAX_BOUNDED_OPTION_ABS_ERROR,
            "max_monotonic_s_reversal": MAX_MONOTONIC_S_REVERSAL,
            "max_inverse_k_reversal": MAX_INVERSE_K_REVERSAL,
        },
    }


def tier_analysis_result() -> Dict[str, object]:
    families: Dict[str, object] = {}
    passed = True
    for family, (thresholds, names) in TIER_FAMILIES.items():
        boundary_pairs = [
            {
                "threshold": threshold,
                "below": tier_for_score(threshold - 0.001, thresholds, names),
                "above": tier_for_score(threshold + 0.001, thresholds, names),
            }
            for threshold in thresholds
        ]
        stable = all(
            names.index(pair["above"]) - names.index(pair["below"]) == 1
            for pair in boundary_pairs
        )
        reachable = [tier_for_score(0.0, thresholds, names)] + [
            tier_for_score(threshold, thresholds, names) for threshold in thresholds
        ]
        family_passed = reachable == list(names) and stable
        passed = passed and family_passed
        families[family] = {
            "thresholds": list(thresholds),
            "reachable_tiers": reachable,
            "boundary_pairs": boundary_pairs,
            "one_tier_perturbation_stable": stable,
        }
    return {
        "name": "tier_reachability",
        "kind": "quantitative",
        "passed": passed,
        "actual": {"families": families},
    }


def scenario_result(name: str) -> Dict[str, object]:
    actual = evaluate_scenario(name)
    bounded = all(0.0 <= float(actual[key]) <= 100.0 for key in PERSISTENT_OUTPUT_KEYS)
    return {
        "name": name,
        "kind": "scenario_balance_model",
        "passed": bounded,
        "actual": actual,
    }


def scenario_relationships_result() -> Dict[str, object]:
    speculative = evaluate_scenario("speculative_boom")
    strategic = evaluate_scenario("strategic_boom")
    historical = evaluate_scenario("historical_default")
    bottleneck = evaluate_scenario("infrastructure_bottleneck")
    recession = evaluate_scenario("treasury_constrained_recession")
    checks = {
        "volatility_preserves_or_increases_option": speculative["USA_oem_option_value"]
        >= strategic["USA_oem_option_value"],
        "volatility_reduces_readiness": speculative["USA_oem_investment_readiness"]
        < strategic["USA_oem_investment_readiness"],
        "bottleneck_increases_pressure": bottleneck["USA_oem_infrastructure_pressure"]
        > historical["USA_oem_infrastructure_pressure"],
        "recession_reduces_option": recession["USA_oem_option_value"]
        < historical["USA_oem_option_value"],
    }
    return {
        "name": "scenario_relationships",
        "kind": "quantitative",
        "passed": all(checks.values()),
        "actual": checks,
    }


def mode_parity_result() -> Dict[str, object]:
    full = evaluate_scenario("historical_default", "full")
    outcomes = evaluate_scenario("historical_default", "outcomes_only")
    off = evaluate_scenario("historical_default", "off")
    full_values = {key: value for key, value in full.items() if key != "mode"}
    outcomes_values = {key: value for key, value in outcomes.items() if key != "mode"}
    off_values = [off[key] for key in PERSISTENT_OUTPUT_KEYS]
    actual = {
        "full_outcomes_equal": full_values == outcomes_values,
        "off_inert": off["inert"] and not off["tiers"] and not any(off_values),
    }
    return {
        "name": "mode_parity",
        "kind": "abstraction",
        "passed": all(actual.values()),
        "actual": actual,
    }


def balance_audit_result() -> Dict[str, object]:
    rows: List[Dict[str, object]] = []
    passed = True
    for snapshot in BALANCE_SNAPSHOTS:
        aggregate = {
            modifier: snapshot.existing_outcome[modifier]
            + snapshot.new_dynamic[modifier]
            + snapshot.program[modifier]
            for modifier in BALANCE_CAPS
        }
        within_caps = {
            modifier: abs(aggregate[modifier]) <= cap + 1e-12
            for modifier, cap in BALANCE_CAPS.items()
        }
        passed = passed and all(within_caps.values())
        rows.append(
            {
                "year": snapshot.year,
                "assumption": snapshot.assumption,
                "existing_outcome": dict(snapshot.existing_outcome),
                "new_dynamic": dict(snapshot.new_dynamic),
                "program": dict(snapshot.program),
                "aggregate": aggregate,
                "within_caps": within_caps,
            }
        )
    return {
        "name": "historical_balance_snapshots",
        "kind": "balance_model_evidence",
        "evidence_label": BALANCE_EVIDENCE_LABEL,
        "passed": passed,
        "actual": {"caps": BALANCE_CAPS, "snapshots": rows},
    }


def run_simulation(names: Sequence[str] = ()) -> Tuple[List[Dict[str, object]], bool]:
    if names:
        unknown = set(names) - set(SCENARIOS)
        if unknown:
            raise SimulationError(
                f"unknown scenario names: {', '.join(sorted(unknown))}"
            )
        results = [scenario_result(name) for name in names]
    else:
        results = [formula_conformance_result(), tier_analysis_result()]
        results.extend(scenario_result(name) for name in SCENARIOS)
        results.extend(
            (
                scenario_relationships_result(),
                mode_parity_result(),
                balance_audit_result(),
            )
        )
    return results, all(bool(result["passed"]) for result in results)


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise SimulationError(message)


def _parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenario", action="append", help="run one named balance-model scenario"
    )
    parser.add_argument(
        "--json", action="store_true", help="emit machine-readable results"
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    try:
        args = _parser().parse_args(argv)
        results, passed = run_simulation(args.scenario or ())
    except SimulationError as exc:
        print(f"{LABEL}: configuration error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(
            json.dumps(
                {"label": LABEL, "passed": passed, "results": results},
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(LABEL)
        for result in results:
            status = "PASS" if result["passed"] else "FAIL"
            print(f"[{status}] {result['name']}")
            if result.get("evidence_label"):
                print(f"  {result['evidence_label']}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
