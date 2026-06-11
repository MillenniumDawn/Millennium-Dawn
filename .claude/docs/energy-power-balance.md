# Energy / Power-Plant Balance

How the three electrical power sources (renewable, nuclear, fossil) compare on
**power per build cost** over the tech tree, and the S-curve design that shapes it.
Read this before touching any power-plant building, energy technology, or the renewable
hotspot system.

## The model

Cost-effectiveness of a power plant is **power output per unit of build cost**:

```
metric = base_GW * state_factor(renewable only) * (1 + Σ power-output techs)
                                                 / (base_cost / (1 + Σ construction-speed techs))
```

- **base_GW / base_cost** come from `common/buildings/00_buildings.txt`
  (`*_energy_gain` and `base_cost`): renewable **0.5 GW / 50000**, nuclear **4 GW / 50000**,
  fossil **2 GW / 9500**. At base (no techs) fossil is most cost-effective, then nuclear, then renewable.
- **Build cost = `base_cost`** (the construction effort civilian factories spend), **not** the
  in-game `$` figure in the building header comments — `$` is foreign investment / income, a
  separate system. Construction-speed techs (`production_speed_<building>_factor`) reduce the
  effective build cost.
- **state_factor** = `state_renewable_capacity_factor_modifier`, applies to **renewables only**
  (a per-state multiplier averaging 1.0, set by `tools/balance/set_renewable_hotspots.py` from
  real wind/solar data; see that script + `state_renewable_capacity_factor_modifier_var`).
- Power techs apply as `base * (1 + modifier)`; the runtime formulas live in
  `common/scripted_effects/00_money_system.txt` (per-state generation) and
  `common/scripted_effects/!_energy_effects.txt` (country roll-up + the renewable monthly random).

## Intended efficiency timeline (state factor 1.0, techs only)

```
fossil  < 2015 <  nuclear (fission)  < 2020 <  renewable  < 2060 <  nuclear (fusion) forever
```

Each source's cumulative tech buff (power **and** construction-speed) is a **logistic S-curve**:

| source | curve | start | shape |
| --- | --- | --- | --- |
| **fossil** | one S-curve | low (~0.25) | steeper early rise (worthwhile 1990s-2010s tech bonuses), same efficiency by 2020, less game-start edge; small total gain (power +0.30, speed +0.15) |
| **renewable** | one S-curve | bottom | shifted early (crosses fossil by 2020): steep 2010s-2020s rise → plateaus by ~2040 (power +10.8, speed +4.3) |
| **nuclear** | **two** stacked S-curves | low-mid | fission (~1990-2015) then fusion (~2050-2065); power +3.35, speed +1.01 |

Crossover amplitudes are solved so the three transitions land exactly on 2015 / 2020 / 2060.
The average metric across sources stays broadly stable and **flattens late-game** — renewable
peaks ~6.3e-4 vs the old exponential design's ~1.87e-3 (deliberately "much less efficient late").

## Tools

- **`tools/balance/set_energy_tech_scurves.py`** — the source of truth. Encodes the S-curve
  design, solves the amplitudes, derives per-tech increments, and writes them into
  `common/technologies/industry.txt` (13 renewable + 12 reactor + 10 fuel_efficiency techs).
  Re-tune by editing the `SHAPE` / `SPEED_RATIO` / `PF` constants and re-running `--apply`.
- **`tools/analysis/renewable_power_per_cost.py`** — charts power/build-cost over time for the
  four state factors vs nuclear vs fossil, parsing the live values from `industry.txt`. Use it
  to verify the crossovers after any change.

## Considerations / caveats baked into the model

- The renewable **monthly random(0..1)** is not in the metric — a renewable plant averages ~half
  its rated output in game, which shifts renewable crossovers a little later than the chart shows.
- **Fuel upkeep is excluded** (renewable 0, nuclear 40/wk, fossil 480/day). It only favours
  renewables, so the modelled crossovers are conservative for renewables.
- Fossil techs **gained a new modifier** (`production_speed_fossil_powerplant_factor`) they did
  not have before, so fossil construction also follows an S-curve.

## Potential future work

- The renewable rise is spread across the 2010s-2020s techs (no single mega-tech), but its S-curve
  plateaus by ~2040, so `renewables_11`-`renewables_13` (2060-2080) grant only token gains (floored
  to 0.001). Re-tuning `R_T`/`R_K` trades breakthrough sharpness against the length of that dead tail.
- Nuclear's fission/fusion split is numeric only; the `reactor*` tech ids and localisation could be
  re-themed (reactor1-8 fission, reactor9-12 fusion) to match the design.
- Hydroelectric and geothermal are separate systems and are **not** modelled here.
