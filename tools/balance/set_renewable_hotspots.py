#!/usr/bin/env python3
"""Set each state's renewable-energy "hotspot" factor, a multiplier averaging 1.0
(``state_renewable_capacity_factor_modifier_var``, read by
``common/scripted_effects/00_money_system_utilities.txt``) from real climate data.
1.0 is the world average; a state at 1.5 generates 1.5x the average renewable output
and one at 0.5 half of it, so the geography redistributes renewable power without
changing the global total. There is no artificial cap - the spread is whatever the
data gives.

For each ``history/states/*.txt``: take the state's centroid in ``map/provinces.bmp``,
project it to lat/lon (calibrated to the vanilla 5632x2048 map), look up real NASA
POWER mean wind speed and solar irradiance there (``data/nasa_wind_solar_grid.csv``,
an 8-degree global grid), convert each to a capacity factor and combine. Every state's
factor is then that capacity factor divided by the global mean, so the mean is exactly
1.0. Coast, terrain and elevation from the map add sub-cell detail. Needs numpy + pillow.

Refresh the grid via, per point:
power.larc.nasa.gov/api/temporal/climatology/point?parameters=WS50M,ALLSKY_SFC_SW_DWN&community=RE&longitude=LON&latitude=LAT

    python tools/balance/set_renewable_hotspots.py [--apply] [--existing-only]
"""
from __future__ import annotations

import argparse
import csv
import glob
import os
import re
import sys

import numpy as np
from PIL import Image


def clampf(x, lo, hi):
    return max(lo, min(hi, x))


# --- NASA POWER grid (data/nasa_wind_solar_grid.csv), uniform 8-degree spacing ---
def _load_grid():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "data", "nasa_wind_solar_grid.csv")
    pts, lats, lons = {}, set(), set()
    for line in open(path):
        if not line[0].isdigit() and not line.startswith("-"):
            continue
        la, lo, ws, ghi = line.split(",")
        pts[(int(la), int(lo))] = (float(ws), float(ghi))
        lats.add(int(la))
        lons.add(int(lo))
    lats, lons = sorted(lats, reverse=True), sorted(lons)
    ws = [[pts[(la, lo)][0] for lo in lons] for la in lats]
    ghi = [[pts[(la, lo)][1] for lo in lons] for la in lats]
    return lats, lons, ws, ghi


GRID_LAT, GRID_LON, GRID_WS, GRID_GHI = _load_grid()


def bilerp(grid, lat, lon):
    """Bilinear sample of the uniform grid; latitude clamps, longitude wraps."""
    fi = (GRID_LAT[0] - lat) / (GRID_LAT[0] - GRID_LAT[1])
    fj = ((lon - GRID_LON[0]) % 360) / (GRID_LON[1] - GRID_LON[0])
    i = min(max(int(fi), 0), len(GRID_LAT) - 2)
    fy = clampf(fi - i, 0.0, 1.0)
    j, fx = int(fj) % len(GRID_LON), fj - int(fj)
    j1 = (j + 1) % len(GRID_LON)
    top = grid[i][j] * (1 - fx) + grid[i][j1] * fx
    bot = grid[i + 1][j] * (1 - fx) + grid[i + 1][j1] * fx
    return top * (1 - fy) + bot * fy


# --- vanilla-HOI4 map projection, fit to ~22 reference states -----------------
LON_A = (0.06414660518271005, -180.5381605233324)              # lon = a*cx + b
LAT_C = (4.874134223698823e-09, -2.3931976661852746e-05,       # lat = cubic(cy)
         -0.02616706208818681, 66.60532472853122)


def project(cx, cy):
    lon = LON_A[0] * cx + LON_A[1]
    lat = LAT_C[0] * cy ** 3 + LAT_C[1] * cy ** 2 + LAT_C[2] * cy + LAT_C[3]
    return clampf(lat, -58.0, 72.0), lon


# --- wind/solar -> capacity factor, then combine ------------------------------
WS_X = [2.0, 3.5, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 14.0]   # turbine
WS_CF = [0.04, 0.10, 0.22, 0.30, 0.38, 0.44, 0.49, 0.53, 0.55, 0.57, 0.59]  # power curve
GHI_TO_CF = 0.0367          # PV CF ~= GHI(kWh/m2/day) * PR(0.8) * tilt(1.1) / 24
COAST_WS_FACTOR = 1.20      # offshore/exposed coast ~ 1.2x the cell-average wind
ELEV_SOLAR = 0.05           # clearer skies at altitude (per normalised elevation)
DIVERSITY_BONUS = 0.25      # credit for a viable second resource
SOLAR_TERRAIN = {"desert": 1.07, "jungle": 0.90, "forest": 0.94, "marsh": 0.93}
WIND_TERRAIN = {"plains": 0.4, "desert": 0.3, "marsh": 0.3, "hills": 0.2,
                "mountain": 0.2, "forest": -0.5, "jungle": -0.8, "urban": -0.3}


def cf_of(lat, lon, coastal, terrain, elevn):
    """Raw capacity factor (~0.05..0.68). The turbine power curve and the solar
    formula bound it naturally, so there is no artificial cap; main() then divides
    every state by the global mean so the factor averages 1.0."""
    ws = bilerp(GRID_WS, lat, lon) * (COAST_WS_FACTOR if coastal else 1) + WIND_TERRAIN.get(terrain, 0.0)
    wind = float(np.interp(ws, WS_X, WS_CF))
    solar = bilerp(GRID_GHI, lat, lon) * GHI_TO_CF * SOLAR_TERRAIN.get(terrain, 1.0) + ELEV_SOLAR * elevn
    return max(wind, solar) + DIVERSITY_BONUS * min(wind, solar)


# --- per-province geometry from the map ---------------------------------------
def load_province_geo(root):
    rgb2id, ptype, pcoast, pterr = {}, {}, {}, {}
    with open(os.path.join(root, "map", "definition.csv"), encoding="latin-1") as f:
        for row in csv.reader(f, delimiter=";"):
            if len(row) < 8 or not row[0].isdigit():
                continue
            pid = int(row[0])
            rgb2id[(int(row[1]) << 16) | (int(row[2]) << 8) | int(row[3])] = pid
            ptype[pid], pcoast[pid], pterr[pid] = row[4], row[5].strip().lower() == "true", row[6]
    im = np.asarray(Image.open(os.path.join(root, "map", "provinces.bmp")).convert("RGB"))
    H, W, _ = im.shape
    enc = ((im[:, :, 0].astype(np.uint32) << 16)
           | (im[:, :, 1].astype(np.uint32) << 8) | im[:, :, 2].astype(np.uint32)).ravel()
    keys = np.array(sorted(rgb2id), dtype=np.uint32)
    vals = np.array([rgb2id[k] for k in keys], dtype=np.int32)
    idx = np.clip(np.searchsorted(keys, enc), 0, len(keys) - 1)
    pid = np.where(keys[idx] == enc, vals[idx], -1)
    ht = np.asarray(Image.open(os.path.join(root, "map", "heightmap.bmp"))
                    .convert("L")).ravel().astype(np.float64)
    ys, xs = np.divmod(np.arange(H * W), W)
    v = pid >= 0
    n = int(pid.max()) + 1
    cnt = np.bincount(pid[v], minlength=n)
    with np.errstate(invalid="ignore"):
        cx = np.bincount(pid[v], weights=xs[v], minlength=n) / cnt
        cy = np.bincount(pid[v], weights=ys[v], minlength=n) / cnt
        hm = np.bincount(pid[v], weights=ht[v], minlength=n) / cnt
    return {"cnt": cnt, "cx": cx, "cy": cy, "h": hm,
            "type": ptype, "coast": pcoast, "terr": pterr}


def state_geo(provs, geo):
    """Aggregate a state's land provinces -> (lat, lon, coastal, terrain, elevn)."""
    cnt = geo["cnt"]
    land = [p for p in provs if p < len(cnt) and cnt[p] > 0 and geo["type"].get(p) in ("land", None)]
    if not land:
        return None
    w = np.array([cnt[p] for p in land], dtype=np.float64)
    cx = float(np.dot([geo["cx"][p] for p in land], w) / w.sum())
    cy = float(np.dot([geo["cy"][p] for p in land], w) / w.sum())
    elevn = clampf((float(np.dot([geo["h"][p] for p in land], w) / w.sum()) - 100.0) / 80.0, 0.0, 1.6)
    coastal = any(geo["coast"].get(p) for p in provs if p < len(cnt))
    terr_count = {}
    for p in land:
        terr_count[geo["terr"].get(p, "plains")] = terr_count.get(geo["terr"].get(p, "plains"), 0) + cnt[p]
    lat, lon = project(cx, cy)
    return lat, lon, coastal, max(terr_count, key=terr_count.get), elevn


# --- writing the value into the state files -----------------------------------
VAR = "state_renewable_capacity_factor_modifier_var"
SET_RE = re.compile(r"set_variable\s*=\s*\{\s*" + VAR + r"\s*=\s*[0-9.]+\s*\}")
OWNER_RE = re.compile(r"^(?P<indent>[ \t]*)owner\s*=\s*[A-Z0-9]{2,3}.*$", re.M)
PROV_RE = re.compile(r"provinces\s*=\s*\{([\d\s]+)\}")


def update_text(text, value):
    """Replace the existing assignment (dropping any duplicates), else insert after owner."""
    line = f"set_variable = {{ {VAR} = {value:.3f} }}"
    m = SET_RE.search(text)
    if m:
        text = text[:m.start()] + line + text[m.end():]
        for dup in reversed(list(SET_RE.finditer(text))[1:]):
            ls = text.rfind("\n", 0, dup.start()) + 1
            le = text.find("\n", dup.end())
            text = text[:ls] + text[(len(text) if le < 0 else le + 1):]
        return text, "update"
    m = OWNER_RE.search(text)
    if not m:
        return text, "skip"
    return text[:m.start()] + f"{m.group(0)}\n{m.group('indent')}{line}" + text[m.end():], "insert"


def main():
    ap = argparse.ArgumentParser(description="Set per-state renewable hotspot values from NASA data.")
    ap.add_argument("--apply", action="store_true", help="write the files (default: dry run)")
    ap.add_argument("--existing-only", action="store_true", help="only re-rate states that already set it")
    ap.add_argument("--root", default=".")
    args = ap.parse_args()

    print("Parsing map...", file=sys.stderr)
    geo = load_province_geo(args.root)

    # Pass 1: raw capacity factor for every state.
    states, noprov = [], 0
    for path in sorted(glob.glob(os.path.join(args.root, "history", "states", "*.txt"))):
        raw = open(path, "rb").read()
        text = raw.decode("utf-8-sig")
        if args.existing_only and not SET_RE.search(text):
            continue
        pm = PROV_RE.search(text)
        sg = state_geo([int(x) for x in pm.group(1).split()], geo) if pm else None
        if sg is None:
            noprov += 1
            continue
        states.append((path, raw, text, cf_of(*sg)))
    mean_cf = sum(cf for *_, cf in states) / len(states)

    # Pass 2: factor = cf / mean, so the factor averages exactly 1.0 (no clamp).
    updated = inserted = skipped = 0
    bins, fmin, fmax = {}, 9e9, 0.0
    for path, raw, text, cf in states:
        f = round(cf / mean_cf, 3)
        fmin, fmax = min(fmin, f), max(fmax, f)
        bins[round(f * 10) / 10] = bins.get(round(f * 10) / 10, 0) + 1
        new_text, action = update_text(text, f)
        skipped += action == "skip"
        updated += action == "update"
        inserted += action == "insert"
        if args.apply and action != "skip":
            out = new_text.replace("\r\n", "\n").encode("utf-8")
            if out != raw:
                open(path, "wb").write(out)

    print(f"{'APPLIED' if args.apply else 'DRY RUN'} | updated={updated} inserted={inserted} "
          f"skipped={skipped} no-provinces={noprov}")
    print(f"mean capacity factor = {mean_cf:.4f}  ->  factor range {fmin:.2f}..{fmax:.2f} (avg 1.00)")
    print("Factor distribution (1.0 = world average):")
    top = max(bins.values(), default=1)
    for k in sorted(bins):
        print(f"  {k:4.1f} | {bins[k]:4d} {'#' * (bins[k] * 50 // top)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
