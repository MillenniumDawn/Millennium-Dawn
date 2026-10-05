"""State-model contracts for AI race financing and sampled physical capacity."""

import copy
import re
from dataclasses import dataclass, field, replace
from decimal import ROUND_DOWN, Decimal, InvalidOperation
from pathlib import Path

import pytest
from ai_race_state_model_test import RaceScript, _parse_race_script
from shared_utils import extract_block_from_text, strip_comments

D = Decimal
ZERO = D(0)
ONE = D(1)
WEEKS = 520
UPFRONT_COSTS = (D(50), D(150), D(400), D(1000))
STAGE_REQUIREMENTS = (
    (D(20), D(10), D(2), D(5), D(2), D(2)),
    (D(40), D(20), D(8), D(20), D(8), D(5)),
    (D(80), D(40), D(25), D(60), D(25), D(10)),
    (D(150), D(80), D(60), D(150), D(60), D(20)),
)


def readiness(available, required):
    assert len(available) == len(required) == 6
    assert all(value > 0 for value in required)
    return min(
        max(ZERO, min(ONE, have / need)) for have, need in zip(available, required)
    )


@dataclass
class Package:
    principal: Decimal
    remaining: Decimal
    installment: Decimal
    weeks_left: int = WEEKS

    @classmethod
    def open(cls, principal, quantum):
        installment = (principal / WEEKS).quantize(quantum, rounding=ROUND_DOWN)
        return cls(principal, principal, installment)

    def due(self):
        if self.weeks_left <= 0:
            return ZERO
        if self.weeks_left == 1:
            return self.remaining
        return min(self.installment, self.remaining)


@dataclass(frozen=True)
class PreparedWeek:
    day: int
    included_expense: Decimal
    dues: tuple

    @property
    def due(self):
        return sum((amount for _, amount in self.dues), ZERO)

    @property
    def rate_correction(self):
        return self.included_expense - self.due


@dataclass
class RaceAccount:
    treasury: Decimal = D(10000)
    national_debt: Decimal = ZERO
    packages: dict = field(default_factory=dict)
    funded_stages: set = field(default_factory=set)
    next_bill_day: int | None = None
    economy_enabled: bool = True
    race_enabled: bool = True
    phase_months: int = 0
    quantum: Decimal = D("0.000001")

    def fund(self, stage, gdp, physical_readiness, emergency=False, day=0):
        if not self.race_enabled or stage not in range(1, 5):
            raise ValueError("stage unavailable")
        if stage in self.funded_stages:
            raise ValueError("stage already funded")
        if self.treasury < UPFRONT_COSTS[stage - 1]:
            raise ValueError("insufficient upfront treasury")
        if physical_readiness < ONE and not emergency:
            raise ValueError("physical capacity incomplete")
        if not ZERO <= physical_readiness <= ONE:
            raise ValueError("invalid readiness")
        if emergency and physical_readiness == ONE:
            raise ValueError("physical capacity already complete")
        self.treasury -= UPFRONT_COSTS[stage - 1]
        self.funded_stages.add(stage)
        if emergency:
            principal = gdp * (D("0.45") + D("0.40") * (ONE - physical_readiness))
            self.packages[stage] = Package.open(principal, self.quantum)
            if self.next_bill_day is None:
                self.next_bill_day = day + 7

    def expense(self):
        if not self.economy_enabled or not self.race_enabled:
            return ZERO
        return sum((package.due() for package in self.packages.values()), ZERO)

    def prepare(self, day, included_expense):
        billable = (
            self.economy_enabled
            and self.race_enabled
            and (self.next_bill_day is None or day >= self.next_bill_day)
        )
        dues = tuple(
            (stage, package.due())
            for stage, package in sorted(self.packages.items())
            if billable and package.weeks_left > 0
        )
        return PreparedWeek(day, included_expense, dues)

    def accrue(self, prepared, rate_with_sample):
        if not self.economy_enabled:
            return ()
        self.treasury += rate_with_sample + prepared.rate_correction
        trace = ["treasury"]
        if not self.race_enabled:
            return tuple(trace)
        for stage, amount in prepared.dues:
            package = self.packages[stage]
            package.remaining -= amount
            package.weeks_left -= 1
            if package.weeks_left == 0:
                assert package.remaining == ZERO
                package.remaining = ZERO
            trace.append(("ledger", stage, amount))
        if prepared.dues:
            self.next_bill_day = prepared.day + 7
        return tuple(trace)

    def monthly_tick(self):
        if self.race_enabled and self.funded_stages:
            self.phase_months += 1

    def turn_off(self):
        self.race_enabled = False
        self.packages.clear()
        self.funded_stages.clear()
        self.next_bill_day = None
        self.phase_months = 0


@dataclass(frozen=True)
class CapacitySample:
    controlled_civs: Decimal
    damaged_civs: Decimal
    controlled_network: Decimal
    damaged_network: Decimal
    energy_balance: Decimal
    applied_power: Decimal
    net_resources: tuple
    applied_resources: tuple
    power_multiplier: Decimal = ONE

    @property
    def available(self):
        return (
            max(ZERO, self.controlled_civs - self.damaged_civs),
            max(ZERO, self.controlled_network - self.damaged_network),
            max(ZERO, self.energy_balance + self.applied_power),
            *(
                max(ZERO, net + applied)
                for net, applied in zip(self.net_resources, self.applied_resources)
            ),
        )

    def readiness(self, stage):
        civ, network, power, chips, composites, oil = STAGE_REQUIREMENTS[stage - 1]
        requirements = (
            civ,
            network,
            power * self.power_multiplier,
            chips,
            composites,
            oil,
        )
        return readiness(self.available, requirements)


@dataclass
class CapacityTracker:
    paired_sample: CapacitySample
    requested: tuple = (ZERO, ZERO, ZERO, ZERO)
    changed_day: int | None = None
    settled: bool = True

    def commit_demand(self, day, requested):
        self.requested = requested
        self.changed_day = day
        self.settled = False

    def refresh(self, day, applied_markers, sample):
        boundary_passed = self.changed_day is None or day > self.changed_day + 1
        if not boundary_passed or applied_markers != self.requested:
            self.paired_sample = replace(sample, applied_resources=(ZERO, ZERO, ZERO))
            self.settled = False
            return False
        self.paired_sample = sample
        self.settled = True
        return True

    def quote(self, stage):
        return self.paired_sample.readiness(stage) if self.settled else None


def _sample(**changes):
    values = dict(
        controlled_civs=D(150),
        damaged_civs=ZERO,
        controlled_network=D(80),
        damaged_network=ZERO,
        energy_balance=D(60),
        applied_power=ZERO,
        net_resources=(D(150), D(60), D(20)),
        applied_resources=(ZERO, ZERO, ZERO),
    )
    values.update(changes)
    return CapacitySample(**values)


def _funded_account(readiness_value=D("0.5"), gdp=D(1000)):
    account = RaceAccount()
    account.fund(1, gdp, readiness_value, emergency=True, day=-7)
    return account


def _pay_week(account, day, ordinary_rate=ZERO):
    sample = account.expense()
    prepared = account.prepare(day, sample)
    trace = account.accrue(prepared, ordinary_rate - sample)
    return prepared.due, trace


@pytest.mark.parametrize("stage", [1, 2, 3, 4])
def test_prepared_country_pays_only_one_upfront_stage_investment(stage):
    account = RaceAccount()
    start = account.treasury
    account.fund(stage, D(1000), ONE)
    assert account.treasury == start - UPFRONT_COSTS[stage - 1]
    assert account.packages == {}
    assert account.expense() == ZERO
    with pytest.raises(ValueError, match="already funded"):
        account.fund(stage, D(1000), ONE)
    assert account.treasury == start - UPFRONT_COSTS[stage - 1]


@pytest.mark.parametrize(
    ("ready", "principal", "weekly"),
    [
        (ZERO, D(850), D("1.634615")),
        (D("0.5"), D(650), D("1.250000")),
        (D("0.999"), D("450.4"), D("0.866153")),
    ],
)
def test_emergency_price_snapshots_shortfall_and_gdp_without_lending_upfront_cash(
    ready, principal, weekly
):
    account = _funded_account(ready)
    assert account.treasury == D(9950)
    assert account.national_debt == ZERO
    package = account.packages[1]
    assert package.principal == package.remaining == principal
    assert package.installment == weekly
    assert package.weeks_left == WEEKS


def test_emergency_financing_does_not_bypass_upfront_treasury_or_capacity_choice():
    account = RaceAccount(treasury=D(49))
    before = copy.deepcopy(account)
    with pytest.raises(ValueError, match="upfront treasury"):
        account.fund(1, D(1000), ZERO, emergency=True)
    assert account == before
    account.treasury = D(50)
    before = copy.deepcopy(account)
    with pytest.raises(ValueError, match="capacity incomplete"):
        account.fund(1, D(1000), ZERO)
    assert account == before


@pytest.mark.parametrize("quantum", [D("0.01"), D("0.000001")])
def test_exactly_520_posted_installments_clear_rounding_residue(quantum):
    account = RaceAccount(quantum=quantum)
    account.fund(1, D("1234.56789"), D("0.37"), emergency=True, day=-7)
    package = account.packages[1]
    principal = package.principal
    weekly = package.installment
    start_treasury = account.treasury
    paid = ZERO
    for week in range(WEEKS):
        amount, trace = _pay_week(account, week * 7)
        paid += amount
        assert trace[0] == "treasury"
        assert trace[1] == ("ledger", 1, amount)
        assert package.remaining >= ZERO
        assert package.weeks_left == WEEKS - week - 1
        if week < WEEKS - 1:
            assert amount == weekly
    assert paid == principal
    assert account.treasury == start_treasury - principal
    assert package.remaining == account.expense() == ZERO
    assert _pay_week(account, WEEKS * 7)[0] == ZERO


def test_four_overlapping_packages_keep_separate_expiry_and_exact_lifetime_totals():
    account = RaceAccount()
    principals = {}
    paid = {stage: ZERO for stage in range(1, 5)}
    for week in range(WEEKS + 3):
        if week < 4:
            stage = week + 1
            account.fund(
                stage,
                D(1000 + stage * 100),
                D(stage) / 5,
                emergency=True,
                day=week * 7 - 7,
            )
            principals[stage] = account.packages[stage].principal
        expense = account.expense()
        prepared = account.prepare(week * 7, expense)
        assert prepared.due == sum(
            (package.due() for package in account.packages.values()), ZERO
        )
        account.accrue(prepared, -expense)
        for stage, amount in prepared.dues:
            paid[stage] += amount
        if week >= WEEKS - 1:
            expired_stage = week - WEEKS + 2
            assert account.packages[expired_stage].remaining == ZERO
            assert account.packages[expired_stage].weeks_left == 0
    assert paid == principals
    assert account.expense() == ZERO
    assert len(account.packages) == 4


def test_zero_rounded_weekly_amount_still_expires_after_520_posted_weeks():
    account = RaceAccount(quantum=D("0.01"))
    account.fund(1, D("0.001"), D("0.5"), emergency=True, day=-7)
    package = account.packages[1]
    assert package.installment == ZERO
    for week in range(519):
        assert _pay_week(account, week * 7)[0] == ZERO
        assert package.weeks_left == 519 - week
        assert account.next_bill_day == (week + 1) * 7
    assert _pay_week(account, 519 * 7)[0] == D("0.00065")
    assert package.weeks_left == 0
    assert package.remaining == ZERO


def test_expense_preview_refresh_and_abandoned_prepare_never_amortize():
    account = _funded_account()
    before = copy.deepcopy(account)
    for day in (0, 0, 7, 30, 365):
        assert account.expense() == D("1.25")
        assert account.prepare(day, account.expense()).due == D("1.25")
    assert account == before


def test_fixed_installments_enter_expenses_after_inflation():
    account = _funded_account()
    ordinary_expense = D(10)
    inflation_multiplier = D("1.5")
    total = ordinary_expense * inflation_multiplier + account.expense()
    assert total == D("16.25")
    before = account.packages[1].remaining
    prepared = account.prepare(0, account.expense())
    account.accrue(prepared, -total)
    assert before - account.packages[1].remaining == D("1.25")


@pytest.mark.parametrize("replay_day", range(7))
def test_replayed_week_and_reload_neutralize_only_the_race_component(replay_day):
    account = _funded_account()
    amount, _ = _pay_week(account, 0, ordinary_rate=D(5))
    assert amount == D("1.25")
    account = copy.deepcopy(account)
    ledger_before = copy.deepcopy(account.packages)
    treasury_before = account.treasury
    amount, trace = _pay_week(account, replay_day, ordinary_rate=D(5))
    assert amount == ZERO
    assert account.packages == ledger_before
    assert account.treasury == treasury_before + 5
    assert trace == ("treasury",)


def test_replayed_callback_prepares_a_fresh_zero_batch_before_accrual():
    account = _funded_account()
    sample = account.expense()
    prepared = account.prepare(0, sample)
    account.accrue(prepared, -sample)
    before = copy.deepcopy(account)
    replayed = account.prepare(0, sample)
    assert replayed.due == ZERO
    account.accrue(replayed, -sample)
    assert account == before


def test_package_purchased_after_weekly_billing_starts_next_week():
    account = RaceAccount()
    _pay_week(account, 0)
    account.fund(1, D(1000), D("0.5"), emergency=True)
    before = copy.deepcopy(account.packages)
    assert _pay_week(account, 0)[0] == ZERO
    assert account.packages == before
    assert _pay_week(account, 7)[0] == D("1.25")
    assert account.packages[1].weeks_left == 519


def test_first_package_waits_seven_days_and_later_packages_keep_existing_cadence():
    account = RaceAccount()
    account.fund(1, D(1000), D("0.5"), emergency=True, day=3)
    assert account.expense() == D("1.25")
    assert _pay_week(account, 7)[0] == ZERO
    assert _pay_week(account, 14)[0] == D("1.25")
    account.fund(2, D(1000), D("0.5"), emergency=True, day=20)
    assert account.next_bill_day == 21
    assert _pay_week(account, 20)[0] == ZERO
    assert _pay_week(account, 21)[0] == D("2.5")


def test_rate_correction_uses_the_sample_already_included_in_treasury_rate():
    account = _funded_account()
    old_sample = account.expense()
    account.fund(2, D(1000), D("0.5"), emergency=True)
    before = account.treasury
    prepared = account.prepare(0, old_sample)
    assert prepared.due == D("2.5")
    assert prepared.rate_correction == D("-1.25")
    account.accrue(prepared, -old_sample)
    assert account.treasury == before - D("2.5")


def test_disabled_economy_preserves_principal_and_all_remaining_installments():
    account = _funded_account()
    account.economy_enabled = False
    before = copy.deepcopy(account)
    for day in (0, 7, 365):
        assert _pay_week(account, day) == (ZERO, ())
    assert account == before
    account.economy_enabled = True
    assert _pay_week(account, 365)[0] == D("1.25")
    assert account.packages[1].weeks_left == 519


def test_capacity_recovery_gdp_changes_and_bankruptcy_do_not_refinance_packages():
    account = _funded_account()
    before = copy.deepcopy(account.packages)
    for current_gdp, inflation, current_readiness in (
        (D(10), D(3), ZERO),
        (D(5000), D("0.5"), ONE),
    ):
        assert current_gdp > 0 and inflation > 0
        assert readiness((current_readiness,) * 6, (ONE,) * 6) == current_readiness
        account.prepare(0, account.expense())
    account.national_debt = D(250)
    account.treasury = ZERO
    assert account.packages == before
    _pay_week(account, 0)
    assert account.treasury == D("-1.25")
    assert account.packages[1].remaining == D("648.75")


def test_off_clears_race_liabilities_without_refunding_paid_costs_or_national_debt():
    account = _funded_account()
    _pay_week(account, 0)
    account.national_debt = D(120)
    treasury_before = account.treasury
    account.turn_off()
    assert account.packages == {} and account.funded_stages == set()
    assert account.expense() == ZERO
    assert account.treasury == treasury_before
    assert account.national_debt == D(120)
    with pytest.raises(ValueError, match="stage unavailable"):
        account.fund(1, D(1000), ONE)


@pytest.mark.parametrize("axis", range(6))
def test_each_physical_axis_can_be_the_binding_constraint(axis):
    available = list(STAGE_REQUIREMENTS[3])
    available[axis] /= 4
    assert readiness(available, STAGE_REQUIREMENTS[3]) == D("0.25")
    available[axis] = D(-100)
    assert readiness(available, STAGE_REQUIREMENTS[3]) == ZERO
    assert (
        readiness(
            tuple(value * 3 for value in STAGE_REQUIREMENTS[3]), STAGE_REQUIREMENTS[3]
        )
        == ONE
    )


def test_damaged_controlled_industry_reduces_benefits_and_repair_restores_them():
    account = _funded_account()
    ledger = copy.deepcopy(account.packages)
    assert _sample(damaged_civs=D(75)).readiness(4) == D("0.5")
    assert _sample(damaged_network=D(60)).readiness(4) == D("0.25")
    assert _sample().readiness(4) == ONE
    for _ in range(12):
        account.monthly_tick()
    assert account.phase_months == 12
    assert account.packages == ledger


def test_resource_capacity_uses_net_supply_after_other_consumers_and_own_applied_load():
    sample = _sample(
        net_resources=(D(-10), D(35), D(10)), applied_resources=(D(60), D(25), D(10))
    )
    assert sample.available[3:] == (D(50), D(60), D(20))
    assert sample.readiness(4) == D(1) / 3
    recovered = _sample(
        net_resources=(D(90), D(35), D(10)), applied_resources=(D(60), D(25), D(10))
    )
    assert recovered.readiness(4) == ONE


def test_power_headroom_includes_usable_curtailed_fossil_but_never_battery_withdrawal():
    generation_before_curtailment = D(200)
    other_load = D(140)
    applied_race_load = D(25)
    curtailed = D(35)
    sample = _sample(
        energy_balance=generation_before_curtailment - other_load - applied_race_load,
        applied_power=applied_race_load,
    )
    post_curtailment_generation = generation_before_curtailment - curtailed
    assert sample.available[2] == post_curtailment_generation + curtailed - other_load
    assert sample.readiness(4) == ONE
    battery_supported = _sample(energy_balance=D(-20), applied_power=D(25))
    withdrawal = D(20)
    assert battery_supported.energy_balance + withdrawal == ZERO
    assert battery_supported.available[2] == D(5)
    assert battery_supported.readiness(4) == D(1) / 12


def test_fuel_shortage_cannot_turn_nameplate_fossil_capacity_into_headroom():
    fuel_limited_generation = D(100)
    sample = _sample(
        energy_balance=fuel_limited_generation - D(140) - D(25), applied_power=D(25)
    )
    assert sample.available[2] == ZERO
    assert sample.readiness(4) == ZERO


def test_power_requirement_and_applied_addback_share_the_sampled_multiplier():
    sample = _sample(
        energy_balance=D("-5"), applied_power=D("7.5"), power_multiplier=D("1.25")
    )
    assert sample.available[2] == D("2.5")
    assert sample.readiness(1) == ONE
    assert sample.readiness(2) == D("0.25")


def test_new_requested_demand_never_creates_headroom_in_an_old_snapshot():
    old = _sample(
        energy_balance=D(2),
        applied_power=D(8),
        net_resources=(D(5), D(2), D(2)),
        applied_resources=(D(20), D(8), D(5)),
    )
    tracker = CapacityTracker(old, requested=(D(8), D(20), D(8), D(5)))
    before = tracker.paired_sample.available
    tracker.commit_demand(10, (D(25), D(60), D(25), D(10)))
    assert tracker.paired_sample.available == before
    assert tracker.paired_sample.available[2:4] == (D(10), D(25))
    assert tracker.quote(3) is None


@pytest.mark.parametrize(
    ("day", "markers", "accepted"),
    [
        (10, (D(25), D(60), D(25), D(10)), False),
        (11, (D(25), D(60), D(25), D(10)), False),
        (12, (D(8), D(20), D(8), D(5)), False),
        (12, (D(25), D(60), D(25), D(10)), True),
    ],
)
def test_resource_resampling_requires_matching_applied_markers_and_a_full_boundary(
    day, markers, accepted
):
    old = _sample()
    tracker = CapacityTracker(old)
    tracker.commit_demand(10, (D(25), D(60), D(25), D(10)))
    new = _sample(
        net_resources=(D(90), D(35), D(10)), applied_resources=(D(60), D(25), D(10))
    )
    assert tracker.refresh(day, markers, new) is accepted
    assert tracker.paired_sample == (
        new if accepted else replace(new, applied_resources=(ZERO, ZERO, ZERO))
    )
    assert (tracker.quote(3) is not None) is accepted


def test_settling_and_capacity_shortfall_do_not_stop_phase_work_or_rewrite_debt():
    account = _funded_account()
    tracker = CapacityTracker(_sample())
    tracker.commit_demand(10, (D(25), D(60), D(25), D(10)))
    before = copy.deepcopy(account.packages)
    for _ in range(12):
        account.monthly_tick()
        assert tracker.quote(3) is None
    assert account.phase_months == 12
    assert account.packages == before


def test_purchase_resample_detects_lost_imports_instead_of_reusing_weekly_headroom():
    tracker = CapacityTracker(_sample())
    assert tracker.quote(4) == ONE
    lost_imports = _sample(net_resources=(D(75), D(60), D(20)))
    assert tracker.refresh(30, tracker.requested, lost_imports)
    assert tracker.quote(4) == D("0.5")


@pytest.fixture(scope="module")
def scripts():
    root = Path(__file__).resolve().parents[2]
    paths = {
        "finance": "common/scripted_effects/02_ai_race_finance_effects.txt",
        "capacity": "common/scripted_effects/01_ai_race_capacity_effects.txt",
        "progression": "common/scripted_effects/03_ai_race_progression_effects.txt",
        "money": "common/scripted_effects/00_money_system.txt",
        "energy": "common/scripted_effects/!_energy_effects.txt",
        "actions": "common/on_actions/MD_on_actions.txt",
        "modifier": "common/dynamic_modifiers/01_ai_race_modifiers.txt",
        "definitions": "common/modifier_definitions/ai_race_modifier_definitions.txt",
    }
    return {
        name: strip_comments((root / path).read_text(encoding="utf-8-sig"))
        for name, path in paths.items()
    }


def _block(text, name):
    match = re.search(rf"(?m)^\s*{re.escape(name)}\s*=\s*\{{", text)
    assert match is not None, name
    body, end = extract_block_from_text(text, match.start())
    assert end >= 0, name
    return body


_DIRECT_BLOCKS_PATTERN = re.compile(r"(?m)^\s*([\w@]+)\s*=\s*\{")


def _direct_blocks(text):
    position = 0
    while match := _DIRECT_BLOCKS_PATTERN.search(text, position):
        body, position = extract_block_from_text(text, match.start())
        assert position >= 0, match.group(1)
        yield match.group(1), body


def _compact(text):
    return " ".join(text.split())


def _ordered(text, *needles):
    positions = [text.index(needle) for needle in needles]
    assert positions == sorted(positions), needles


def test_script_stage_requirements_match_the_six_axis_balance_contract(scripts):
    requirements = _block(scripts["capacity"], "ai_race_load_stage_requirements")
    stages = [
        body for name, body in _direct_blocks(requirements) if name in {"if", "else_if"}
    ]
    assert len(stages) == 4
    axes = ("civs", "network", "power", "microchips", "composites", "oil")
    for stage, body in enumerate(stages, 1):
        values = dict(re.findall(r"ai_race_requirement_(\w+)\s*=\s*(\d+)", body))
        assert int(values["stage"]) == stage
        assert D(values["cost"]) == UPFRONT_COSTS[stage - 1]
        assert tuple(D(values[axis]) for axis in axes) == STAGE_REQUIREMENTS[stage - 1]


@pytest.mark.parametrize("scope", ["current", "offer"])
def test_script_readiness_uses_all_six_clamped_ratios_and_scales_power_units(
    scripts, scope
):
    name = (
        "ai_race_refresh_operating_state"
        if scope == "current"
        else "ai_race_refresh_offer"
    )
    body = _compact(_block(scripts["capacity"], name))
    for axis in ("civs", "network", "power", "microchips", "composites", "oil"):
        prefix = f"ai_race_{scope}_{axis}"
        assert f"check_variable = {{ {prefix}_required > 0 }}" in body
        assert (
            f"value = {prefix}_available divide = {prefix}_required clamp = {{ min = 0 max = 1 }}"
            in body
        )
        assert f"value = ai_race_{scope}_readiness min = {prefix}_ratio" in body
    assert (
        f"multiply_variable = {{ ai_race_{scope}_power_required = ai_race_power_multiplier }}"
        in body
    )
    assert "ai_race_create_financing = yes" not in body
    assert "ai_race_commit_weekly_bill = yes" not in body


def test_script_quote_snapshots_gdp_and_divides_principal_into_520_payments(scripts):
    body = _compact(_block(scripts["capacity"], "ai_race_refresh_offer"))
    assert "ai_race_refresh_capacity_sample = yes" not in body
    operating = _block(scripts["capacity"], "ai_race_refresh_operating_state")
    _ordered(
        operating, "calculate_energy_use = yes", "ai_race_refresh_capacity_sample = yes"
    )
    assert operating.count("ai_race_refresh_capacity_sample = yes") == 2
    root = Path(__file__).resolve().parents[2]
    callers = [
        scripts["progression"],
        scripts["actions"],
        strip_comments(
            (root / "common/scripted_effects/00_ai_race_effects.txt").read_text(
                encoding="utf-8-sig"
            )
        ),
    ]
    offers = 0
    for text in callers:
        previous = 0
        for match in re.finditer(r"ai_race_refresh_offer = yes", text):
            assert (
                "ai_race_refresh_operating_state = yes"
                in text[previous : match.start()]
            )
            previous = match.end()
            offers += 1
    assert offers == 8
    for name in ("ai_race_capture_quote", "ai_race_commit_review"):
        entry = _block(scripts["progression"], name)
        _ordered(
            entry,
            "ai_race_refresh_operating_state = yes",
            "ai_race_refresh_offer = yes",
        )
    assert (
        "value = 1 subtract = ai_race_offer_readiness multiply = 0.40 add = 0.45"
        in body
    )
    assert (
        "ai_race_offer_principal = { value = gdp_total multiply = ai_race_offer_rate }"
        in body
    )
    assert (
        f"ai_race_offer_payment = {{ value = ai_race_offer_principal divide = {WEEKS} }}"
        in body
    )


def test_script_capacity_counts_controlled_undamaged_buildings_and_net_resources(
    scripts,
):
    body = _compact(_block(scripts["capacity"], "ai_race_refresh_capacity_sample"))
    for building in ("industrial_complex", "internet_station"):
        assert (
            f"named_collection = controlled_states_collection add = non_damaged_building_level@{building}"
            in body
        )
    for resource in ("microchips", "composites", "oil"):
        assert (
            f"ai_race_accounted_{resource} = modifier@ai_race_applied_{resource}"
            in body
        )
        assert (
            f"ai_race_{resource}_available = {{ value = resource@{resource} add = ai_race_accounted_{resource} max = 0 }}"
            in body
        )
        assert f"add = ai_race_demand_{resource}" not in body


def test_script_settlement_requires_power_sample_day_boundary_and_all_applied_markers(
    scripts,
):
    body = _block(scripts["capacity"], "ai_race_refresh_capacity_sample")
    accepting = next(block for name, block in _direct_blocks(body) if name == "if")
    gate = _compact(_block(accepting, "limit"))
    assert "has_country_flag = energy_state_bases_initialized" in gate
    assert "has_variable = ai_race_power_multiplier" in gate
    assert (
        "check_variable = { var = global.num_days value = ai_race_demand_settle_day compare = greater_than_or_equals }"
        in gate
    )
    for demand in ("power", "microchips", "composites", "oil"):
        assert (
            f"check_variable = {{ modifier@ai_race_applied_{demand} = ai_race_demand_{demand} }}"
            in gate
        )
    rejecting = _compact(
        next(block for name, block in _direct_blocks(body) if name == "else")
    )
    for resource in ("microchips", "composites", "oil"):
        assert f"set_variable = {{ ai_race_accounted_{resource} = 0 }}" in rejecting
    operating = _compact(_block(scripts["capacity"], "ai_race_refresh_operating_state"))
    assert (
        "ai_race_demand_settle_day = { value = global.num_days add = 2 }" in operating
    )


def test_script_power_sample_is_paired_with_consumption_before_storage_and_curtailment(
    scripts,
):
    calculate = _block(scripts["energy"], "calculate_energy_use")
    _ordered(
        calculate,
        "energy_calc_consumption = yes",
        "energy_calc_generation = yes",
        "energy_calc_balance = yes",
        "ai_race_capture_power_sample = yes",
        "energy_calc_fuel = yes",
    )
    consumption = _compact(_block(scripts["energy"], "energy_calc_consumption"))
    assert (
        "ai_race_accounted_power = { value = modifier@ai_race_applied_power multiply = display_multiplier }"
        in consumption
    )
    assert "ai_race_sampled_power_multiplier = display_multiplier" in consumption
    sample = _compact(_block(scripts["capacity"], "ai_race_capture_power_sample"))
    assert (
        "ai_race_power_available = { value = energy_balance add = ai_race_accounted_power max = 0 }"
        in sample
    )
    assert "ai_race_power_multiplier = ai_race_sampled_power_multiplier" in sample
    assert not re.search(r"storage|withdraw|energy_sum|ai_race_demand_power", sample)


def test_script_demand_and_applied_markers_share_one_modifier_and_country_definitions(
    scripts,
):
    modifier = _compact(_block(scripts["modifier"], "ai_race_operating_modifier"))
    for resource in ("power", "microchips", "composites", "oil"):
        engine_key = (
            "energy_use" if resource == "power" else f"country_resource_cost_{resource}"
        )
        assert f"{engine_key} = ai_race_demand_{resource}" in modifier
        assert f"ai_race_applied_{resource} = ai_race_demand_{resource}" in modifier
        definition = _block(scripts["definitions"], f"ai_race_applied_{resource}")
        assert "category = country" in definition


def test_script_finance_snapshots_each_package_once_and_keeps_rounding_residue(scripts):
    creation = _compact(_block(scripts["finance"], "ai_race_create_financing"))
    totals = _compact(_block(scripts["finance"], "ai_race_refresh_finance_totals"))
    for stage in range(1, 5):
        assert (
            f"NOT = {{ has_variable = ai_race_finance_original_{stage} }}" in creation
        )
        assert f"ai_race_finance_original_{stage} = ai_race_offer_principal" in creation
        assert (
            f"ai_race_finance_remaining_{stage} = ai_race_offer_principal" in creation
        )
        assert f"ai_race_finance_weekly_{stage} = ai_race_offer_payment" in creation
        assert f"ai_race_finance_installments_{stage} = {WEEKS}" in creation
        assert (
            f"check_variable = {{ ai_race_finance_installments_{stage} = 1 }}" in totals
        )
        assert (
            f"ai_race_finance_due_{stage} = ai_race_finance_remaining_{stage}" in totals
        )
    assert "NOT = { has_variable = ai_race_finance_next_bill_day }" in creation
    assert (
        "ai_race_finance_next_bill_day = { value = global.num_days add = 7 }"
        in creation
    )
    assert not re.search(
        r"(?:add_to|subtract_from)_variable\s*=\s*\{\s*(?:treasury|debt)\s*=", creation
    )


@pytest.mark.parametrize(
    "effect",
    [
        "ai_race_refresh_finance_totals",
        "ai_race_refresh_finance_expense",
        "ai_race_prepare_weekly_bill",
    ],
)
def test_script_finance_projection_and_prepare_do_not_amortize_ledger(scripts, effect):
    body = _block(scripts["finance"], effect)
    mutations = re.findall(
        r"(?:set|add_to|subtract_from|multiply|divide)_variable\s*=\s*\{\s*(\w+)", body
    )
    assert not any(
        re.fullmatch(
            r"ai_race_finance_(?:original|remaining|weekly|installments)_[1-4]",
            variable,
        )
        for variable in mutations
    )
    assert "ai_race_commit_weekly_bill = yes" not in body


def test_script_weekly_prepare_neutralizes_cached_expense_and_freezes_four_slots(
    scripts,
):
    body = _compact(_block(scripts["finance"], "ai_race_prepare_weekly_bill"))
    assert (
        "var = global.num_days value = ai_race_finance_next_bill_day compare = greater_than_or_equals"
        in body
    )
    assert (
        "add_to_temp_variable = { treasury_rate_gain = ai_race_finance_rate_component }"
        in body
    )
    assert (
        "subtract_from_temp_variable = { treasury_rate_gain = ai_race_bill_total }"
        in body
    )
    for stage in range(1, 5):
        assert f"ai_race_bill_{stage} = ai_race_finance_due_{stage}" in body
        assert f"ai_race_bill_total = ai_race_bill_{stage}" in body
    assert "set_temp_variable = { ai_race_bill_prepared = 0 }" in body
    assert "set_temp_variable = { ai_race_bill_prepared = 1 }" in body


def test_script_commit_posts_zero_rounded_installments_once_and_only_after_accrual(
    scripts,
):
    commit = _compact(_block(scripts["finance"], "ai_race_commit_weekly_bill"))
    assert "check_variable = { ai_race_bill_prepared = 1 }" in commit
    assert "set_temp_variable = { ai_race_bill_prepared = 0 }" in commit
    for stage in range(1, 5):
        assert (
            f"check_variable = {{ ai_race_finance_installments_{stage} > 0 }}" in commit
        )
        assert (
            f"subtract_from_variable = {{ ai_race_finance_remaining_{stage} = ai_race_bill_{stage} }}"
            in commit
        )
        assert (
            f"subtract_from_variable = {{ ai_race_finance_installments_{stage} = 1 }}"
            in commit
        )
    assert (
        "ai_race_finance_next_bill_day = { value = global.num_days add = 7 }" in commit
    )
    assert not re.search(
        r"(?:add_to|subtract_from)_variable\s*=\s*\{\s*treasury\s*=", commit
    )
    weekly = _block(_block(scripts["actions"], "on_weekly"), "effect")
    posting = [
        body
        for name, body in _direct_blocks(weekly)
        if name == "if" and "ai_race_commit_weekly_bill = yes" in body
    ]
    assert len(posting) == 1
    assert (
        _compact(_block(posting[0], "limit"))
        == "NOT = { has_country_flag = disabled_economic_system }"
    )
    _ordered(
        _compact(posting[0]),
        "treasury_rate_gain = treasury_rate",
        "ai_race_prepare_weekly_bill = yes",
        "add_to_variable = { treasury = treasury_rate_gain }",
        "ai_race_commit_weekly_bill = yes",
        "automated_debt_taker = yes",
    )
    assert scripts["actions"].count("ai_race_commit_weekly_bill = yes") == 1


def test_script_expense_enters_after_inflation_and_records_actual_display_rate_component(
    scripts,
):
    expenses = _compact(_block(scripts["money"], "calculate_additional_expense_rate"))
    _ordered(
        expenses,
        "multiply_variable = { additional_expenses_rate = additional_expenses_inflation }",
        "ai_race_refresh_finance_expense = yes",
    )
    display = _compact(_block(scripts["money"], "update_display"))
    _ordered(
        display,
        "treasury_rate = { value = display_income subtract = display_expense }",
        "ai_race_finance_rate_component = ai_race_finance_expense_component",
    )
    component = _compact(_block(scripts["finance"], "ai_race_refresh_finance_expense"))
    assert (
        "add_to_variable = { additional_expenses_rate = ai_race_finance_expense_component }"
        in component
    )


def test_script_off_clears_only_race_financing_without_refunding_economy(scripts):
    body = _block(scripts["finance"], "ai_race_clear_finance_state")
    statements = re.findall(r"(\w+)\s*=\s*(\w+)", body)
    assert statements
    assert all(
        effect == "clear_variable" and variable.startswith("ai_race_finance_")
        for effect, variable in statements
    )
    cleared = {variable for _, variable in statements}
    assert "ai_race_finance_next_bill_day" in cleared
    for stage in range(1, 5):
        for component in ("original", "remaining", "weekly", "installments", "due"):
            assert f"ai_race_finance_{component}_{stage}" in cleared


class FinanceScript(RaceScript):
    def __init__(self, finance_source):
        super().__init__()
        self.finance_effects = _parse_race_script(finance_source)
        self.effects.update(self.finance_effects)
        self.country(1)
        self.countries[1]["vars"]["treasury"] = D(10000)
        self.globals["num_days"] = 0

    def value(self, name, identifier):
        if isinstance(name, str):
            try:
                return D(name)
            except InvalidOperation:
                pass
        return super().value(name, identifier)

    def run(self, name, identifier=1):
        if name in self.finance_effects:
            self.execute(self.finance_effects[name], identifier)
        elif name != "ai_race_refresh_gui":
            raise AssertionError(f"Unexpected finance boundary: {name}")

    @property
    def variables(self):
        return self.countries[1]["vars"]

    def fund(self, stage, principal, quantum=D("0.000001")):
        self.variables.update(
            ai_race_stage=D(stage),
            ai_race_offer_principal=principal,
            ai_race_offer_payment=(principal / WEEKS).quantize(
                quantum, rounding=ROUND_DOWN
            ),
        )
        self.run("ai_race_create_financing")

    def post(self, day, included_expense=None):
        self.globals["num_days"] = day
        self.temps.clear()
        self.variables["additional_expenses_rate"] = ZERO
        self.run("ai_race_refresh_finance_expense")
        if included_expense is None:
            included_expense = self.variables["ai_race_finance_expense_component"]
        self.variables["ai_race_finance_rate_component"] = included_expense
        self.temps["treasury_rate_gain"] = -included_expense
        before = self.ledger()
        self.run("ai_race_prepare_weekly_bill")
        assert self.ledger() == before
        treasury_before = self.variables["treasury"]
        self.execute(
            [("add_to_variable", "=", [("treasury", "=", "treasury_rate_gain")])], 1
        )
        self.run("ai_race_commit_weekly_bill")
        return treasury_before - self.variables["treasury"]

    def ledger(self):
        return {
            name: value
            for name, value in self.variables.items()
            if re.fullmatch(
                r"ai_race_finance_(?:original|remaining|weekly|installments)_[1-4]",
                name,
            )
        }


def test_executed_four_package_ledger_pays_exact_principals_including_zero_weeklies(
    scripts,
):
    runtime = FinanceScript(scripts["finance"])
    principals = (D(850), D(650), D("450.4"), D("0.00065"))
    for stage, principal in enumerate(principals, 1):
        runtime.fund(stage, principal, quantum=D("0.01"))
    initial = runtime.ledger()
    assert runtime.post(0) == ZERO
    assert runtime.ledger() == initial
    paid = ZERO
    for week in range(1, WEEKS + 1):
        paid += runtime.post(week * 7)
        for stage in range(1, 5):
            assert (
                runtime.variables[f"ai_race_finance_installments_{stage}"]
                == WEEKS - week
            )
            assert runtime.variables[f"ai_race_finance_remaining_{stage}"] >= ZERO
        before_replay = runtime.ledger()
        runtime.run("ai_race_commit_weekly_bill")
        assert runtime.ledger() == before_replay
    assert paid == sum(principals)
    assert runtime.variables["treasury"] == D(10000) - sum(principals)
    assert runtime.variables["ai_race_finance_outstanding"] == ZERO
    assert runtime.variables["ai_race_finance_weekly"] == ZERO
    assert runtime.post(WEEKS * 7 + 7) == ZERO


def test_executed_preview_and_same_week_reload_cannot_amortize_twice(scripts):
    runtime = FinanceScript(scripts["finance"])
    runtime.fund(1, D(650))
    initial = runtime.ledger()
    for _ in range(3):
        runtime.variables["additional_expenses_rate"] = ZERO
        runtime.run("ai_race_refresh_finance_expense")
        runtime.run("ai_race_refresh_finance_totals")
    assert runtime.ledger() == initial
    assert runtime.post(6) == ZERO
    assert runtime.post(7) == D("1.25")
    runtime = copy.deepcopy(runtime)
    paid_ledger = runtime.ledger()
    for day in range(7, 14):
        assert runtime.post(day, included_expense=D("1.25")) == ZERO
        assert runtime.ledger() == paid_ledger
    assert runtime.post(14) == D("1.25")
    assert runtime.variables["ai_race_finance_installments_1"] == 518


def test_executed_new_package_corrects_the_old_treasury_rate_sample(scripts):
    runtime = FinanceScript(scripts["finance"])
    runtime.fund(1, D(650))
    old_component = runtime.variables["ai_race_finance_weekly"]
    runtime.globals["num_days"] = 6
    runtime.fund(2, D(650))
    assert runtime.variables["ai_race_finance_next_bill_day"] == 7
    assert runtime.post(7, included_expense=old_component) == D("2.5")
    assert runtime.variables["ai_race_finance_remaining_1"] == D("648.75")
    assert runtime.variables["ai_race_finance_remaining_2"] == D("648.75")


def test_executed_off_cleanup_preserves_treasury_and_national_debt(scripts):
    runtime = FinanceScript(scripts["finance"])
    runtime.fund(1, D(650))
    runtime.post(7)
    runtime.variables["debt"] = D(120)
    before = {key: runtime.variables[key] for key in ("treasury", "debt")}
    runtime.run("ai_race_clear_finance_state")
    assert runtime.ledger() == {}
    assert {key: runtime.variables[key] for key in before} == before
