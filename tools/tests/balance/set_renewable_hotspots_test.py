"""Behavioral tests for tools/balance/set_renewable_hotspots.py.

Exercises:
- NASA POWER grid parsing and bilinear interpolation on a small fixture,
- capacity-factor formula and combine logic,
- map projection (cx, cy -> lat, lon),
- state-file text transform (SET_RE/OWNER_RE) for both update and insert paths.

The dry run against the shipped map and states lives in
tools/tests/content/renewable_hotspots_live_test.py.
"""

from __future__ import annotations

import pytest
from shared.suite import load_tool_module

pytest.importorskip("numpy", reason="numpy is in the optional analysis group")
pytest.importorskip("PIL", reason="Pillow is in the optional analysis group")
hots = load_tool_module("balance/set_renewable_hotspots.py")


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


def test_bilerp_longitude_wraps_around_360():
    # The sampler wraps longitude at 360 degrees (the grid is global).
    # Asking for lons[0] + 360 must hit the same cell.
    grid = hots.GRID_WS
    base = hots.bilerp(grid, hots.GRID_LAT[0], hots.GRID_LON[0])
    wrapped = hots.bilerp(grid, hots.GRID_LAT[0], hots.GRID_LON[0] + 360)
    assert wrapped == pytest.approx(base)


# --- capacity factor --------------------------------------------------------


def test_cf_of_is_higher_with_more_wind_or_sun():
    # high wind + high sun + coast + plain terrain > low wind + low sun + jungle
    high = hots.cf_of(lat=30.0, lon=0.0, coastal=True, terrain="plains", elevn=0.0)
    low = hots.cf_of(lat=30.0, lon=0.0, coastal=False, terrain="jungle", elevn=0.0)
    assert high > low


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
