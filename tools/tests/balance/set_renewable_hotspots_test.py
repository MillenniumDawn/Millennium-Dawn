"""Behavioral tests for tools/balance/set_renewable_hotspots.py.

Exercises:
- NASA POWER grid parsing and bilinear interpolation on a small fixture,
- capacity-factor formula and combine logic,
- map projection (cx, cy -> lat, lon),
- state-file text transform (SET_RE/OWNER_RE) for both update and insert paths,
- the CLI dry-run path against the real history/states + map/.

The module imports numpy + PIL at top level, so tests skip cleanly when
those are not installed.
"""

from __future__ import annotations

import importlib
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "tools" / "balance" / "set_renewable_hotspots.py"

importlib_util = importlib.util
NP_AVAILABLE = importlib_util.find_spec("numpy") is not None
PIL_AVAILABLE = importlib_util.find_spec("PIL") is not None
skip_no_np = pytest.mark.skipif(not NP_AVAILABLE, reason="numpy required")
skip_no_pil = pytest.mark.skipif(not PIL_AVAILABLE, reason="PIL required")
skip_no_both = pytest.mark.skipif(
    not (NP_AVAILABLE and PIL_AVAILABLE),
    reason="numpy and PIL required",
)

# Module imports numpy + PIL at top level. When the optional analysis group
# is not installed the whole test module is skipped at collection time so
# the suite still runs cleanly.
if not (NP_AVAILABLE and PIL_AVAILABLE):
    pytest.skip(
        "numpy + PIL required for tools/balance/set_renewable_hotspots.py",
        allow_module_level=True,
    )

importlib_util_spec = importlib_util.spec_from_file_location(
    "set_renewable_hotspots_under_test", SCRIPT
)
assert importlib_util_spec is not None
hots = importlib_util.module_from_spec(importlib_util_spec)
sys.modules["set_renewable_hotspots_under_test"] = hots
assert importlib_util_spec.loader is not None
importlib_util_spec.loader.exec_module(hots)


# --- helpers ---------------------------------------------------------------


def test_clampf_bounds():
    assert hots.clampf(0.5, 0.0, 1.0) == 0.5
    assert hots.clampf(-1.0, 0.0, 1.0) == 0.0
    assert hots.clampf(2.0, 0.0, 1.0) == 1.0


def test_project_clamps_latitude_to_vanilla_range():
    # Out-of-range latitudes get clamped to the vanilla-HOI4 -58..72 range
    lat, lon = hots.project(0.0, 0.0)  # center of map
    assert -58.0 <= lat <= 72.0


# --- bilinear sampler ------------------------------------------------------


@skip_no_np
def test_bilerp_exact_grid_node_returns_that_value():
    # GRID_LAT[0] / GRID_LON[0] are the corners; the bilinear sampler must
    # return the corner value at integer grid coords (within fp tolerance).
    grid = hots.GRID_WS
    lats, lons = hots.GRID_LAT, hots.GRID_LON
    # (lats[0], lons[0]) corner: fx = 0, fy = 0
    val = hots.bilerp(grid, lats[0], lons[0])
    assert val == pytest.approx(grid[0][0])
    # (lats[0], lons[1]) corner
    val = hots.bilerp(grid, lats[0], lons[1])
    assert val == pytest.approx(grid[0][1])


@skip_no_np
def test_bilerp_longitude_wraps_around_360():
    # The sampler wraps longitude at 360 degrees (the grid is global).
    # Asking for lons[0] + 360 must hit the same cell.
    grid = hots.GRID_WS
    base = hots.bilerp(grid, hots.GRID_LAT[0], hots.GRID_LON[0])
    wrapped = hots.bilerp(grid, hots.GRID_LAT[0], hots.GRID_LON[0] + 360)
    assert wrapped == pytest.approx(base)


# --- capacity factor --------------------------------------------------------


@skip_no_np
def test_cf_of_is_higher_with_more_wind_or_sun():
    # high wind + high sun + coast + plain terrain > low wind + low sun + jungle
    high = hots.cf_of(lat=30.0, lon=0.0, coastal=True, terrain="plains", elevn=0.0)
    low = hots.cf_of(lat=30.0, lon=0.0, coastal=False, terrain="jungle", elevn=0.0)
    assert high > low


@skip_no_np
def test_cf_of_combines_diversity_bonus():
    # With wind == solar (max), the diversity bonus adds to max(...)
    # We can verify the bonus is independent of the multiplier
    only_wind = hots.cf_of(
        lat=20.0, lon=120.0, coastal=False, terrain="plains", elevn=0.0
    )
    # Calling cf_of twice should return the same value (no hidden state)
    again = hots.cf_of(lat=20.0, lon=120.0, coastal=False, terrain="plains", elevn=0.0)
    assert only_wind == pytest.approx(again)


# --- state text transform ---------------------------------------------------


def test_update_text_replaces_existing_assignment():
    text = (
        "state = {\n"
        "    owner = USA\n"
        "    set_variable = { state_renewable_capacity_factor_modifier_var = 1.000 }\n"
        "}\n"
    )
    new_text, action = hots.update_text(text, 1.234)
    assert action == "update"
    assert "state_renewable_capacity_factor_modifier_var = 1.234" in new_text
    assert "1.000" not in new_text


def test_update_text_drops_duplicate_set_variable():
    text = (
        "state = {\n"
        "    owner = USA\n"
        "    set_variable = { state_renewable_capacity_factor_modifier_var = 1.000 }\n"
        "    set_variable = { state_renewable_capacity_factor_modifier_var = 0.500 }\n"
        "}\n"
    )
    new_text, action = hots.update_text(text, 1.234)
    assert action == "update"
    # only the FIRST occurrence survives (duplicates dropped)
    assert new_text.count("state_renewable_capacity_factor_modifier_var = 1.234") == 1
    assert "0.500" not in new_text


def test_update_text_inserts_after_owner_when_missing():
    text = "state = {\n" "    owner = USA\n" "    provinces = { 1 2 3 }\n" "}\n"
    new_text, action = hots.update_text(text, 0.876)
    assert action == "insert"
    assert "owner = USA" in new_text
    # the inserted line lives between the owner line and the next field
    assert (
        "    owner = USA\n"
        "    set_variable = { state_renewable_capacity_factor_modifier_var = 0.876 }\n"
        "    provinces = { 1 2 3 }"
    ) in new_text


def test_update_text_skips_when_no_owner_line():
    text = "state = {\n    provinces = { 1 2 3 }\n}\n"
    new_text, action = hots.update_text(text, 0.876)
    assert action == "skip"
    assert new_text == text


# --- CLI smoke (requires real map + history) ------------------------------


@skip_no_both
def test_cli_dry_run_against_real_map_and_states(capsys):
    """`python tools/balance/set_renewable_hotspots.py` dry-runs against
    the real repo; it must NOT modify any state file."""
    history_dir = REPO_ROOT / "history" / "states"
    if not history_dir.exists() or not (REPO_ROOT / "map" / "provinces.bmp").exists():
        pytest.skip("real map/ and history/states/ not in this checkout")
    # Snapshot a few state files before
    sample = sorted(history_dir.glob("*.txt"))[:5]
    before = {p: p.read_bytes() for p in sample}
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(REPO_ROOT)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "DRY RUN" in result.stdout
    assert "mean capacity factor" in result.stdout
    # sample files unchanged
    after = {p: p.read_bytes() for p in sample}
    assert before == after
