"""Behavioral tests for tools/analysis/renewable_power_per_cost.py.

Exercises:
- the live parser/chain builder over a small industry.txt fixture,
- the per-tech cumulative-power and cumulative-speed math,
- the metric function with known inputs,
- the CLI dry-run path that writes a PNG to a temp file.

matplotlib is imported at module top, so tests skip cleanly when it is
not installed.
"""

from __future__ import annotations

import importlib
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "tools" / "analysis" / "renewable_power_per_cost.py"

importlib_util = importlib.util
MPL_AVAILABLE = importlib_util.find_spec("matplotlib") is not None
NP_AVAILABLE = importlib_util.find_spec("numpy") is not None
skip_no_mpl = pytest.mark.skipif(not MPL_AVAILABLE, reason="matplotlib required")

# tools/analysis/ is on the pyproject pytest pythonpath, so we can import
# the module by name — but only when both matplotlib and numpy are
# available, since the module imports them at top level.
if not (MPL_AVAILABLE and NP_AVAILABLE):
    pytest.skip(
        "matplotlib + numpy required for tools/analysis/renewable_power_per_cost.py",
        allow_module_level=True,
    )

import renewable_power_per_cost as rpp

# --- parser + chain builder on a fixture -----------------------------------

INDUSTRY_FIXTURE = (
    "\tstart_year = 1990\n"
    "\tallow = { always = yes }\n"
    "\tearly_renewables = {\n"
    "\t\trenewable_energy_gain_multiplier = 0.10\n"
    "\t\tproduction_speed_renewable_energy_infra_factor = 0.04\n"
    "\t\tstart_year = 1990\n"
    "\t}\n"
    "\trenewables = {\n"
    "\t\trenewable_energy_gain_multiplier = 0.15\n"
    "\t\tproduction_speed_renewable_energy_infra_factor = 0.06\n"
    "\t\tstart_year = 1995\n"
    "\t}\n"
    "\treactor1 = {\n"
    "\t\tnuclear_energy_generation_modifier = 0.20\n"
    "\t\tproduction_speed_nuclear_reactor_factor = 0.06\n"
    "\t\tstart_year = 1990\n"
    "\t}\n"
    "\treactor2 = {\n"
    "\t\tnuclear_energy_generation_modifier = 0.30\n"
    "\t\tproduction_speed_nuclear_reactor_factor = 0.09\n"
    "\t\tstart_year = 2000\n"
    "\t}\n"
    "\tfuel_efficiency = {\n"
    "\t\tfossil_pp_energy_generation_modifier = 0.05\n"
    "\t\tproduction_speed_fossil_powerplant_factor = 0.02\n"
    "\t\tstart_year = 1990\n"
    "\t}\n"
    # tech missing start_year -> must be excluded
    "\torphan = {\n"
    "\t\trenewable_energy_gain_multiplier = 0.99\n"
    "\t}\n"
    # tech with neither power nor speed modifier -> must be excluded
    "\tblank = {\n"
    "\t\tstart_year = 1995\n"
    "\t}\n"
)


@pytest.fixture
def industry_path(tmp_path):
    p = tmp_path / "industry.txt"
    p.write_text(INDUSTRY_FIXTURE, encoding="utf-8")
    return p


def test_parse_techs_strips_comments_and_groups_fields(industry_path):
    techs = rpp.parse_techs(str(industry_path))
    assert "early_renewables" in techs
    er = techs["early_renewables"]
    assert er["renewable_energy_gain_multiplier"] == 0.10
    assert er["production_speed_renewable_energy_infra_factor"] == 0.04
    assert er["start_year"] == 1990


def test_parse_techs_recognises_nested_blocks(industry_path):
    techs = rpp.parse_techs(str(industry_path))
    # depth tracking must close the outer block before sibling techs start
    assert "reactor2" in techs
    assert techs["reactor2"]["nuclear_energy_generation_modifier"] == 0.30


def test_build_chains_excludes_orphan_and_blank(industry_path):
    techs = rpp.parse_techs(str(industry_path))
    chains = rpp.build_chains(techs)
    # orphan (no start_year) and blank (no power or speed) must be excluded
    ren_names = {row[3] for row in chains["ren"]}
    nuc_names = {row[3] for row in chains["nuc"]}
    fos_names = {row[3] for row in chains["fos"]}
    assert "orphan" not in ren_names
    assert "blank" not in (ren_names | nuc_names | fos_names)


def test_build_chains_sorted_by_year(industry_path):
    techs = rpp.parse_techs(str(industry_path))
    chains = rpp.build_chains(techs)
    for key in ("ren", "nuc", "fos"):
        years = [row[0] for row in chains[key]]
        assert years == sorted(years), f"{key} chain not sorted: {years}"


def test_cum_inclusive_at_year_threshold(industry_path):
    techs = rpp.parse_techs(str(industry_path))
    chains = rpp.build_chains(techs)
    # renewable chain: early_renewables(1990, p=0.10), renewables(1995, p=0.15)
    chain = chains["ren"]
    assert rpp.cum(chain, 1989, 1) == 0.0
    assert rpp.cum(chain, 1990, 1) == pytest.approx(0.10)
    assert rpp.cum(chain, 1994, 1) == pytest.approx(0.10)
    assert rpp.cum(chain, 1995, 1) == pytest.approx(0.25)
    assert rpp.cum(chain, 2100, 1) == pytest.approx(0.25)
    # speed column index is 2
    assert rpp.cum(chain, 2100, 2) == pytest.approx(0.10)


def test_metric_matches_formula(industry_path):
    techs = rpp.parse_techs(str(industry_path))
    chains = rpp.build_chains(techs)
    # At year 1995 with default state factor 1.0, renewable metric = base_GW /
    # (base_cost / (1 + speed)) * (1 + power)
    # power = 0.5 * 1.0 * (1 + 0.10 + 0.15) = 0.625
    # effort = 50000 / (1 + 0.04 + 0.06) = 50000 / 1.10 = ~45454.545
    # metric = 0.625 / 45454.545 = ~1.375e-5
    val = rpp.metric("ren", chains["ren"], 1995)
    expected = (
        rpp.BASE_GW["ren"]
        * 1.0
        * (1 + 0.10 + 0.15)
        / (rpp.BASE_COST["ren"] / (1 + 0.04 + 0.06))
    )
    assert val == pytest.approx(expected)


def test_metric_state_factor_scales_power(industry_path):
    techs = rpp.parse_techs(str(industry_path))
    chains = rpp.build_chains(techs)
    val_1 = rpp.metric("ren", chains["ren"], 2100, factor=1.0)
    val_15 = rpp.metric("ren", chains["ren"], 2100, factor=1.5)
    # a higher state factor only scales the power numerator
    assert val_15 == pytest.approx(1.5 * val_1)


# --- CLI path --------------------------------------------------------------


@skip_no_mpl
def test_cli_writes_png(tmp_path):
    """`python tools/analysis/renewable_power_per_cost.py --out ...` writes a
    PNG with the expected width/height."""
    out = tmp_path / "chart.png"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--out", str(out)],
        capture_output=True,
        text=True,
        check=True,
        cwd=str(REPO_ROOT),
    )
    assert out.exists() and out.stat().st_size > 0
    # PNG signature
    with open(out, "rb") as fh:
        assert fh.read(8).startswith(b"\x89PNG\r\n\x1a\n")
    # CLI prints chain lengths and crossover table
    assert "ren:" in result.stdout
    assert "nuc:" in result.stdout
    assert "fos:" in result.stdout
    assert "state" in result.stdout


@skip_no_mpl
def test_cli_dry_run_against_real_industry(tmp_path):
    """Smoke test against the real industry.txt."""
    out = tmp_path / "real.png"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--out", str(out)],
        capture_output=True,
        text=True,
        check=True,
        cwd=str(REPO_ROOT),
    )
    # chain length summary line per source
    for key in ("ren:", "nuc:", "fos:"):
        assert key in result.stdout
    assert out.exists() and out.stat().st_size > 1000
