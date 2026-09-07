"""Behavioral tests for tools/balance/set_energy_tech_scurves.py.

Exercises the deterministic S-curve maths (logistic, cumulative, amplitudes,
per-tech increments), the industry.txt regex parser/rewriter on a small
fixture, and the CLI dry-run path.

The module imports scipy at top level; the tests skip cleanly when scipy is
not installed (the CI install matrix was extended to pull --group analysis
alongside --group runtime, so this is the steady state).
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Any, cast

import pytest
from shared.suite import write_text

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "tools" / "balance" / "set_energy_tech_scurves.py"

# `importlib.util.find_spec` needs util explicitly imported for the type checker.
importlib_util = importlib.util

SCIPY_AVAILABLE = importlib_util.find_spec("scipy") is not None
skip_no_scipy = pytest.mark.skipif(not SCIPY_AVAILABLE, reason="scipy required")

# Module is gated on scipy: when scipy is missing, skip the entire test
# module at collection time so the suite still runs cleanly on a dev install.
pytestmark = skip_no_scipy

# Load the module directly from tools/balance/ — name starts with `set_`, so
# plain `import set_energy_tech_scurves` would need tools/balance on PYTHONPATH.
# We only exec the module when scipy is available so the suite still
# collects cleanly when the optional analysis group is not installed.
_BALANCE_DIR = REPO_ROOT / "tools" / "balance"


def _load_sc():
    spec = importlib_util.spec_from_file_location(
        "set_energy_tech_scurves_under_test",
        _BALANCE_DIR / "set_energy_tech_scurves.py",
    )
    assert spec is not None
    mod = importlib_util.module_from_spec(spec)
    sys.modules["set_energy_tech_scurves_under_test"] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


if SCIPY_AVAILABLE:
    sc = _load_sc()
else:
    sc = cast(Any, None)
    # Tell pytest to skip every test in this module
    pytest.skip(
        "scipy required for tools/balance/set_energy_tech_scurves.py",
        allow_module_level=True,
    )


# --- logistic curve primitives ---------------------------------------------


def test_lg_endpoints_and_midpoint():
    # At tmid, lg == 0.5
    assert sc.lg(2010, 2010, 0.1) == pytest.approx(0.5)
    # Far below tmid: very small; far above: very close to 1
    assert sc.lg(1900, 2010, 0.1) < 1e-3
    assert sc.lg(2120, 2010, 0.1) > 1 - 1e-3


def test_chain_logistics_independent():
    # Renewable, fission and fusion helpers each hit 0.5 at their own tmid
    assert sc.Lr(2016) == pytest.approx(0.5)
    assert sc.Lfis(2002) == pytest.approx(0.5)
    assert sc.Lfus(2053) == pytest.approx(0.5)
    # And they are different curves (steepness differs)
    assert sc.Lf(2080) != sc.Lr(2080)


# --- cumulative buffs -------------------------------------------------------


def test_cum_power_fossil_is_pf_times_Lf():
    pf = 0.30
    for t in (1990, 2010, 2020, 2060):
        assert sc.cum_power("fos", t, pf, 0.0, 0.0, 0.0) == pytest.approx(pf * sc.Lf(t))


def test_cum_power_nuclear_sums_fission_and_fusion():
    pfis, pfus = 2.0, 1.5
    for t in (1990, 2010, 2050, 2080):
        assert sc.cum_power("nuc", t, 0.0, 0.0, pfis, pfus) == pytest.approx(
            pfis * sc.Lfis(t) + pfus * sc.Lfus(t)
        )


def test_cum_speed_uses_speed_ratio():
    pf = 0.30
    p = sc.cum_power("nuc", 2050, pf, 1.0, 1.0, 0.0)
    assert sc.cum_speed("nuc", 2050, pf, 1.0, 1.0, 0.0) == pytest.approx(
        sc.SPEED_RATIO["nuc"] * p
    )


def test_cum_infra_normalises_to_2080_asymptote():
    pf = 0.30
    pr = 1.0
    pfis = 1.0
    pfus = 0.0
    amps = (pf, pr, pfis, pfus)
    # renewable at 2080: cum_infra == INFRA_CAP
    full = sc.cum_infra("ren", 2080, *amps)
    assert full == pytest.approx(sc.INFRA_CAP)
    # partial year: scales as cum_power(2030)/cum_power(2080) * INFRA_CAP
    mid = sc.cum_infra("ren", 2030, *amps)
    expected = (
        sc.INFRA_CAP
        * sc.cum_power("ren", 2030, *amps)
        / sc.cum_power("ren", 2080, *amps)
    )
    assert mid == pytest.approx(expected)


def test_cum_infra_zero_asymptote_returns_zero():
    # if a chain's 2080 cum_power is 0 (zero amplitudes), infra stays at 0
    assert sc.cum_infra("ren", 2080, 0.0, 0.0, 0.0, 0.0) == 0.0
    # also when full <= 0 (degenerate), returns 0 cleanly
    assert sc.cum_infra("ren", 2080, 0.0, 0.0, 0.0, -1.0) == 0.0


# --- metric & amplitude solving --------------------------------------------


def test_metric_at_zero_amplitudes_equals_base():
    # With zero power/speed buffs the metric reduces to BASE[k]
    for k in ("fos", "ren", "nuc"):
        assert sc.metric(k, 2010, 0.0, 0.0, 0.0, 0.0) == pytest.approx(sc.BASE[k])


def test_metric_monotone_in_power():
    base = sc.metric("fos", 2050, 0.0, 0.0, 0.0, 0.0)
    high = sc.metric("fos", 2050, 0.5, 0.0, 0.0, 0.0)
    assert high > base


@skip_no_scipy
def test_solve_amplitudes_matches_design_crossovers():
    pf, pr, pfis, pfus = sc.solve_amplitudes()
    amps = (pf, pr, pfis, pfus)

    # 2015: nuclear ~ fossil (within a few percent)
    nuc_2014 = sc.metric("nuc", 2014, *amps)
    fos_2014 = sc.metric("fos", 2014, *amps)
    assert nuc_2014 == pytest.approx(fos_2014, rel=0.02)

    # 2020: renewable ~ fossil
    ren_2019 = sc.metric("ren", 2019, *amps)
    fos_2019 = sc.metric("fos", 2019, *amps)
    assert ren_2019 == pytest.approx(fos_2019, rel=0.02)

    # 2060: nuclear (fusion on) ~ renewable
    ren_2060 = sc.metric("ren", 2060, *amps)
    nuc_2060 = sc.metric("nuc", 2060, *amps)
    assert nuc_2060 == pytest.approx(ren_2060, rel=0.02)

    # 2080: nuclear still above renewable (fusion plateau holds the lead)
    ren_2080 = sc.metric("ren", 2080, *amps)
    nuc_2080 = sc.metric("nuc", 2080, *amps)
    assert nuc_2080 > ren_2080

    # all amplitudes positive
    assert pf > 0 and pr > 0 and pfis > 0 and pfus > 0


# --- increments -------------------------------------------------------------


@skip_no_scipy
def test_increments_chain_order_and_floors():
    amps = sc.solve_amplitudes()
    edits = sc.increments(amps)

    # every CHAIN tech has an entry, and the per-chain order matches CHAINS
    for key, c in sc.CHAINS.items():
        chain_techs = [t for t, (k, *_rest) in edits.items() if k == key]
        assert chain_techs == c["techs"]

    # Each per-tech power increment is non-negative (>= 0.001 floor)
    for tech, (key, p, s, iv) in edits.items():
        assert p >= 0.001
        assert s >= 0.001
        # infra is non-positive relief and never more extreme than INFRA_CAP
        assert iv <= 0.0
        assert iv >= sc.INFRA_CAP - 1e-9


@skip_no_scipy
def test_increments_cumulate_to_chain_total():
    amps = sc.solve_amplitudes()
    edits = sc.increments(amps)
    for key, c in sc.CHAINS.items():
        last_year = c["years"][-1]
        cum_p = sum(p for t, (k, p, s, iv) in edits.items() if k == key)
        # the last-year power equals the chain's cum_power at last_year
        expected = sc.cum_power(key, last_year, *amps)
        # Allow small rounding diff from the per-step rounding to 3dp
        assert cum_p == pytest.approx(expected, abs=0.005)


# --- industry.txt rewriting -------------------------------------------------

# Note: literal \t characters below MUST be tabs, not spaces — the regex in
# the script anchors each tech head with `^\t`.
INDUSTRY_TEMPLATE = (
    "\tstart_year = 1990\n"
    "\tallow = { always = yes }\n"
    "\tfuel_efficiency = {\n"
    "\t\trenewable_energy_gain_multiplier = 0.123\n"
    "\t\tfossil_pp_energy_generation_modifier = 0.05\n"
    "\t\tproduction_speed_fossil_powerplant_factor = 0.02\n"
    "\t\tfossil_infra_cost_multiplier_modifier = -0.04\n"
    "\t\tstart_year = 1990\n"
    "\t}\n"
    "\treactor1 = {\n"
    "\t\tnuclear_energy_generation_modifier = 0.10\n"
    "\t\tproduction_speed_nuclear_reactor_factor = 0.03\n"
    "\t\tnuclear_infra_cost_multiplier_modifier = -0.05\n"
    "\t\tstart_year = 1990\n"
    "\t}\n"
    "\tearly_renewables = {\n"
    "\t\trenewable_energy_gain_multiplier = 0.20\n"
    "\t\tproduction_speed_renewable_energy_infra_factor = 0.08\n"
    "\t\trenewable_infra_cost_multiplier_modifier = -0.10\n"
    "\t\tstart_year = 1990\n"
    "\t}\n"
)


ENERGY_EDITS = {
    "fuel_efficiency": ("fos", 0.5, 0.25, -0.04),
    "reactor1": ("nuc", 0.6, 0.18, -0.05),
    "early_renewables": ("ren", 0.7, 0.28, -0.10),
}


@pytest.fixture
def industry_path(tmp_path):
    return write_text(tmp_path / "industry.txt", INDUSTRY_TEMPLATE)


def test_apply_to_industry_rewrites_existing_lines(industry_path, monkeypatch):
    monkeypatch.setattr(sc, "INDUSTRY", str(industry_path))
    report, missing = sc.apply_to_industry(
        (0.3, 1.0, 1.0, 1.0), ENERGY_EDITS, apply=False
    )
    assert missing == set()
    assert {r[0] for r in report} == set(ENERGY_EDITS)
    # dry run: file untouched
    assert "renewable_energy_gain_multiplier = 0.20" in industry_path.read_text(
        encoding="utf-8"
    )


def test_apply_to_industry_writes_when_apply_true(industry_path, monkeypatch):
    monkeypatch.setattr(sc, "INDUSTRY", str(industry_path))
    report, missing = sc.apply_to_industry(
        (0.3, 1.0, 1.0, 1.0), ENERGY_EDITS, apply=True
    )
    assert missing == set()
    assert report
    text = industry_path.read_text(encoding="utf-8")
    # power/speed/infra lines replaced
    assert "\t\trenewable_energy_gain_multiplier = 0.7\n" in text
    assert "\t\tproduction_speed_renewable_energy_infra_factor = 0.28\n" in text
    assert "\t\trenewable_infra_cost_multiplier_modifier = -0.1\n" in text
    # unrelated fields preserved
    assert "\t\tstart_year = 1990" in text


def test_apply_to_industry_reports_missing(monkeypatch, tmp_path):
    p = write_text(tmp_path / "industry.txt", "\tstart_year = 1990\n")
    monkeypatch.setattr(sc, "INDUSTRY", str(p))
    edits = {"does_not_exist": ("fos", 0.1, 0.05, -0.001)}
    _, missing = sc.apply_to_industry((0.3, 1.0, 1.0, 1.0), edits, apply=False)
    assert missing == {"does_not_exist"}


def test_apply_to_industry_inserts_missing_speed_and_infra(industry_path, monkeypatch):
    """Tech block that lacks the speed line gets it inserted by the rewriter."""
    template = (
        "\tstart_year = 1990\n"
        "\tfuel_efficiency = {\n"
        "\t\trenewable_energy_gain_multiplier = 0.10\n"
        "\t\tfossil_pp_energy_generation_modifier = 0.05\n"
        "\t\tfossil_infra_cost_multiplier_modifier = -0.02\n"
        "\t\tstart_year = 1990\n"
        "\t}\n"
    )
    industry_path.write_text(template, encoding="utf-8")
    monkeypatch.setattr(sc, "INDUSTRY", str(industry_path))
    edits = {"fuel_efficiency": ("fos", 0.5, 0.25, -0.04)}
    report, missing = sc.apply_to_industry((0.3, 1.0, 1.0, 1.0), edits, apply=True)
    assert missing == set()
    flags = {r[0]: (r[5], r[6]) for r in report}
    assert flags["fuel_efficiency"][0] == "speed+"  # speed inserted
    assert flags["fuel_efficiency"][1] == "infra="  # infra replaced
    text = industry_path.read_text(encoding="utf-8")
    assert "\t\tproduction_speed_fossil_powerplant_factor = 0.25" in text


# --- CLI paths -------------------------------------------------------------


@pytest.fixture(autouse=True)
def _restore_industry_path():
    # The module is only loaded when scipy is available; when it is not,
    # pytest.mark.skipif handles the skip and this fixture short-circuits.
    if not SCIPY_AVAILABLE or sc is None:
        yield
        return
    original = sc.INDUSTRY
    yield
    setattr(sc, "INDUSTRY", original)


def test_cli_dry_run_prints_crossovers():
    """`python tools/balance/set_energy_tech_scurves.py` dry-runs against
    the real industry.txt; it must NOT modify the file and must report the
    2015/2020/2060 crossovers."""
    if not SCIPY_AVAILABLE:
        pytest.skip("scipy required for the CLI under test")
    real_industry = REPO_ROOT / "common" / "technologies" / "industry.txt"
    if not real_industry.exists():
        pytest.skip("real industry.txt not in this checkout")
    setattr(sc, "INDUSTRY", str(real_industry))
    before = real_industry.read_text(encoding="utf-8")
    import subprocess

    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "DRY RUN" in result.stdout
    assert "best source by year" in result.stdout
    assert "amplitudes:" in result.stdout
    # file unchanged
    after = real_industry.read_text(encoding="utf-8")
    assert before == after


def test_cli_apply_requires_complete_coverage(tmp_path):
    """--apply on a scratch industry.txt that doesn't contain every CHAIN
    tech must abort (return 1) without writing. We copy the script to a
    tmp location and rewrite its INDUSTRY constant so a fresh subprocess
    import (without our monkey-patch in scope) sees the scratch file."""
    if not SCIPY_AVAILABLE:
        pytest.skip("scipy required for the CLI under test")
    scratch = tmp_path / "industry.txt"
    scratch.write_text("\tstart_year = 1990\n", encoding="utf-8")
    script_copy = tmp_path / "scurves_copy.py"
    text = SCRIPT.read_text(encoding="utf-8")
    text = text.replace(
        'INDUSTRY = os.path.join(REPO, "common", "technologies", "industry.txt")',
        f"INDUSTRY = {str(scratch)!r}",
        1,
    )
    script_copy.write_text(text, encoding="utf-8")
    import subprocess

    result = subprocess.run(
        [sys.executable, str(script_copy), "--apply"],
        capture_output=True,
        text=True,
    )
    # No chain techs in the file -> missing is non-empty -> exit 1
    assert result.returncode == 1
    assert "ERROR: techs not found" in result.stdout
    # file untouched
    assert scratch.read_text(encoding="utf-8").strip() == "start_year = 1990"
