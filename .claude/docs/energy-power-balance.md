# Energy and Power-Plant Balance

Read before touching a power-plant building, an energy technology, or the renewable
hotspot system. Hydroelectric and geothermal are separate systems.

## Model

Cost-effectiveness is power output per unit of build cost:

```
metric = base_GW * state_factor * (1 + sum of power techs)
         / (base_cost / (1 + sum of construction-speed techs))
```

- `base_GW` and `base_cost` come from `common/buildings/00_buildings.txt`
  (`*_energy_gain` and `base_cost`). With no techs, fossil is the most cost-effective,
  then nuclear, then renewable.
- Build cost is `base_cost`, the construction effort. It is not the `$` figure in the
  building header comments, which belongs to the investment system.
- `state_factor` is `state_renewable_capacity_factor_modifier`. It applies to renewables
  only, averages 1.0, and is set by `tools/balance/set_renewable_hotspots.py`.
- Runtime formulas: `00_money_system.txt` (per-state generation) and
  `!_energy_effects.txt` (country roll-up and the renewable monthly random).

## Intended timeline

At state factor 1.0, by techs alone:

```
fossil  < 2015 <  renewable  < 2060 <  nuclear (fusion)
```

Good renewable states (factor 1.5) beat fossil by 2010. Fission nuclear never leads at
factor 1.0, but renewables stay within 1.5x of it through 2055, and weak states (factor
0.5) never beat it.

Every energy tech grants at least 3% (`MIN_GAIN`) on power, construction speed, and
upkeep relief. On top of that, each source's cumulative tech bonus follows a logistic
S-curve. Each curve starts at zero one tech step before its chain's first tech, so no tech
carries a pre-1990 lump. Fossil has one small curve past its midpoint, so its gains shrink
from about 7% to the 3% minimum. Renewable has one large, wide curve that rises through
the 2000s to 2030s and still grants real gains on the 2060 to 2080 techs. Nuclear has two
stacked curves: a wide fission curve that keeps growing through the Gen IV techs, and a
fusion boost (about 2050 to 2065). The amplitudes are solved so the crossovers land on
2015 and 2060.

## Upkeep relief

Each energy tech also lowers the weekly upkeep of its own plant type. `update_infra_rate`
in `00_money_system.txt` computes per-source expense as plant count times per-plant rate
times the source's multiplier: `infra_cost_multiplier` plus
`nuclear_infra_cost_multiplier_modifier`, `fossil_infra_cost_multiplier_modifier`, or
`renewable_infra_cost_multiplier_modifier`. Each tech gives at least 3% relief, the rest
follows that source's power curve, and a fully researched chain reaches `INFRA_CAP` (-0.40).

## Tools

- `tools/balance/set_energy_tech_scurves.py` owns the numbers. It solves the curves and
  writes the per-tech power, construction-speed, and upkeep values into
  `common/technologies/industry.txt`. Retune by editing its `SHAPE`, `SPEED_RATIO`, `PF`,
  and `INFRA_CAP` constants and running `--apply`. Hand edits to those tech values are
  overwritten.
- `tools/analysis/renewable_power_per_cost.py` charts power per build cost over time
  from the live values. Run it to check the crossovers after a change.

## Not in the model

- The renewable monthly random(0..1). A renewable plant averages about half its rated
  output, so real renewable crossovers land a little later than the chart.
- Fuel upkeep, which only favors renewables.
