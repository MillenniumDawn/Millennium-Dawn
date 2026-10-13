# Weapon development costs: review rules

These are the rules for checking the money cost of any **decision, mission or event option that develops a new weapon or modernizes an existing one** in Millennium Dawn. The reviewer (bot or human) applies them to every such cost and reports each one that breaks them.

Three rules work together:

1. **The cost table** sets the base minimum and maximum for each kind of equipment, in 2000 prices.
2. **The date multiplier** raises the whole range in 2010, 2020 and 2030.
3. **Economy scaling** sets where inside the range a country's cost sits: the larger its GDP and productivity, the more its development costs.

## Money units in MD

The treasury is counted in **billions of USD**.

| Script value | Money |
|---|---|
| `0.05` | $50 million |
| `0.1` | $100 million |
| `0.5` | $500 million |
| `1.0` | $1 billion |
| `10.0` | $10 billion |

Money appears in three places:

- **Deduction** (the money actually taken):
  ```
  set_temp_variable = { treasury_change = -0.1 }
  modify_treasury_effect = yes
  ```
  It can sit in `complete_effect`, `remove_effect`, a mission's effects, an event option, or a scripted effect called from any of these.
- **Gate and label** (what the player sees on a decision):
  ```
  custom_cost_trigger = { check_variable = { treasury > 0.1 } }
  custom_cost_text = cost_0_1
  ```
- **Computed costs**: a variable or formula, for example a cost scaled by the date and the economy, or one that drops with each model developed earlier. Work out its value for every reachable input.

`cost = 50` on a decision is **political power**, not money. Political power, command power and other non-money costs are outside these rules.

## Cost table

These are the base ranges for the full development cost of one item, in billions of USD, in **2000–2009 prices**. For later years, apply the date multiplier.

The **Source** column shows who set each row: *author* means the rule's author; *added* means the row was filled in for this document and can be adjusted.

### Modernization

| Item | Min | Max | Source |
|---|---|---|---|
| Modernization of land equipment, air defence, missiles and other weapons | 0.05 | 0.2 | author |
| Modernization of a plane or a helicopter (twice the base) | 0.1 | 0.4 | author (helicopters added) |
| Modernization of a ship or a submarine (3 to 5 times the base) | 0.15 | 1.0 | author (submarines added) |

### Land

| Item | Min | Max | Source |
|---|---|---|---|
| New tank (MBT) | 1.0 | 5.0 | author |
| New IFV | 0.5 | 5.0 | author |
| New APC | 0.3 | 2.5 | added |
| New vehicle type on an existing hull, for example a heavy IFV on a tank hull | 0.2 | 1.0 | added |
| New towed artillery | 0.2 | 2.5 | author |
| New self-propelled artillery | 0.5 | 4.0 | author |
| New MLRS | 1.0 | 7.5 | author |
| New utility vehicle | 0.1 | 0.3 | author |
| New small arms | 0.1 | 0.3 | author |
| New ATGM | 0.1 | 0.3 | author |

### Air

| Item | Min | Max | Source |
|---|---|---|---|
| New plane, unless a row below fits | 1.0 | 5.0 | author |
| New 5th-generation fighter | 5.0 | 15.0 | author |
| New stealth bomber | 10.0 | 20.0 | author |
| New helicopter | 1.0 | 4.0 | added |
| New small drone: reconnaissance, tactical, loitering munition | 0.05 | 0.5 | added |
| New large drone: MALE, HALE, strike | 0.5 | 3.0 | added |

### Air defence

| Item | Min | Max | Source |
|---|---|---|---|
| New MANPADS | 0.15 | 0.5 | added |
| New short-range SAM system | 0.3 | 2.0 | author (min added) |
| New medium-range SAM system | 1.0 | 5.0 | added |
| New long-range SAM system | 2.0 | 10.0 | author (min added) |

### Missiles

| Item | Min | Max | Source |
|---|---|---|---|
| New anti-ship missile | 0.5 | 3.0 | added |
| New land-attack cruise missile | 0.5 | 3.0 | added |
| New tactical or operational ballistic missile | 1.0 | 5.0 | added |
| New strategic missile (ICBM, SLBM) | 5.0 | 20.0 | added |

### Naval

| Item | Min | Max | Source |
|---|---|---|---|
| New ship, unless a row below fits | 2.0 | 10.0 | author |
| New diesel-electric submarine | 2.0 | 8.0 | added |
| New nuclear submarine | 8.0 | 20.0 | added |
| New aircraft carrier | 10.0 | 20.0 | author |

### Reference points from the rule's author

| Item | Row | Cost |
|---|---|---|
| Modernized T-64 | Modernization of land equipment | ≈ 0.1 |
| New ATGM | New ATGM | ≈ 0.15 |
| Nota, a 4th-generation MBT | New tank | ≈ 4.0 |

## How to classify an item

1. **New or modernized?** It is a *modernization* when the base equipment is already available (in service, in the country's stockpile, or already designed in game) and the work upgrades it: engine, armour, ERA, fire control, armament, avionics, sensors and similar. The result keeps the base platform: T-64 → T-64BM, T-55 → T-55AGM, T-84 → T-84 Oplot-M, MiG-29 → MiG-29MU2. Pick the modernization row by the base: planes and helicopters, ships and submarines, or everything else.
2. **A new vehicle type on an existing hull** (a heavy IFV on a tank hull, an ARV or an engineering vehicle built from a tank) is neither a modernization nor a fully new vehicle. Use its own row.
3. **If new: pick the most specific row.** A 5th-generation fighter uses its own row, not "New plane". An aircraft carrier or a submarine uses its own row, not "New ship".
4. **If no row fits** (for example a radar, an electronic warfare system, a satellite), do not guess a range. Mark it **UNCLASSIFIED**, name the closest rows, and ask a maintainer.

Some ranges overlap, for example modernization (0.05–0.2) and small arms (0.1–0.3). A wrong row only matters when the cost falls outside the overlap.

## Date multiplier

Development gets more expensive over time, for every kind of equipment. Each jump multiplies the previous period's prices.

| Development starts | Jump | Total multiplier on the base table |
|---|---|---|
| 2000–2009 | none | ×1.0 |
| 2010–2019 | +5% to +7.5% | ×1.05 to ×1.075 |
| 2020–2029 | another +10% | ×1.155 to ×1.183 |
| 2030 and later | another +10% | ×1.271 to ×1.301 |

**Allowed range in a period** = row min × the period's lowest multiplier, up to row max × the period's highest multiplier.

Example, new IFV (base 0.5–5.0):

| Period | Allowed range |
|---|---|
| 2000–2009 | 0.5–5.0 |
| 2010–2019 | 0.525–5.375 |
| 2020–2029 | 0.578–5.913 |
| 2030 and later | 0.635–6.504 |

The date that counts is the in-game date when the development starts, which is when the first payment is made.

### What to check

1. **The cost must fit the period's allowed range** for every period in which the development can start.
2. **Content that can start in more than one period must raise its cost with the date**, through date checks or a computed multiplier. A fixed cost is allowed only when the content can start in a single period. Read the period from the date limits in `visible`, `available`, `allowed`, the event's trigger and the content that unlocks it. If nothing ends it, assume it can start in every period from its earliest date to the end of the game.

## Economy scaling: GDP and productivity

**Rule:** the larger a country's GDP and productivity, the more its development costs. The cost table and the date multiplier set the limits. The country's economy sets where inside them its cost sits.

MD variables, in country scope:

| Variable | Meaning |
|---|---|
| `gdp_total` | GDP, in billions of USD |
| `gdp_per_capita` | GDP per person, in thousands of USD |
| `overall_productivity` | the country's productivity |
| `global.average_world_productivity` | the world average, for comparison |

In MD, `gdp_total` already includes productivity. `overall_productivity` or `gdp_per_capita` is what separates a small rich country (high productivity) from a large poor one (low productivity).

These names come from MD's public GitLab repository. Check that they still exist in the current version before relying on them.

### What to check

1. **No inversions.** For the same kind of item in the same period, a country with higher GDP and productivity must not pay less than a country with lower ones. Compare against similar development content of other countries in the mod and report every inversion.
2. **A computed cost must rise with the economy.** When the cost is calculated, it must go up (never down) as `gdp_total` and productivity go up, and it must stay inside the allowed range.
3. **Shared content must compute its cost.** A generic decision, a shared event, or content that several countries can reach cannot follow the rule with a fixed number. Its cost must be computed from the economy.
4. **Fixed costs are allowed only in content for a single country.** The value must fit that country's economy in the years the content is available. As a guide:
   - small or low-productivity economies sit in the lower part of the range;
   - medium economies sit in the middle;
   - the largest and most productive economies sit in the upper part.

   How ambitious the item is also matters. Nota, a 4th-generation MBT, sits high in the tank range (≈ 4.0 of 1.0–5.0) even for Ukraine. Placement is therefore a **warning**, not an error.

## Example implementation

This is one acceptable way to compute a cost that follows all three rules, not a rule itself. The economy constants (`2000` and `2`) are a proposal and can be tuned. The date multipliers are the midpoints of the allowed ones.

```
# Before calling, set the row's base range (2000 prices):
#   set_temp_variable = { dev_cost_min = 0.5 }
#   set_temp_variable = { dev_cost_max = 5.0 }
# Result: dev_cost, positive, in billions of USD.
calculate_weapon_dev_cost = {
	# Economy factor: 0 for a small, low-productivity economy, 1 for the largest and most productive
	set_temp_variable = { dev_gdp_factor = gdp_total }
	divide_temp_variable = { dev_gdp_factor = 2000 }	# a GDP of $2 trillion or more gives the full weight
	clamp_temp_variable = { var = dev_gdp_factor min = 0 max = 1 }

	set_temp_variable = { dev_prod_factor = overall_productivity }
	divide_temp_variable = { dev_prod_factor = global.average_world_productivity }
	divide_temp_variable = { dev_prod_factor = 2 }	# twice the world average or more gives the full weight
	clamp_temp_variable = { var = dev_prod_factor min = 0 max = 1 }

	set_temp_variable = { dev_economy_factor = dev_gdp_factor }
	add_to_temp_variable = { dev_economy_factor = dev_prod_factor }
	divide_temp_variable = { dev_economy_factor = 2 }

	# Cost inside the base range = min + (max - min) * economy factor
	set_temp_variable = { dev_cost = dev_cost_max }
	subtract_from_temp_variable = { dev_cost = dev_cost_min }
	multiply_temp_variable = { dev_cost = dev_economy_factor }
	add_to_temp_variable = { dev_cost = dev_cost_min }

	# Date multiplier
	if = {
		limit = { date > 2030.1.1 }
		multiply_temp_variable = { dev_cost = 1.286 }
	}
	else_if = {
		limit = { date > 2020.1.1 }
		multiply_temp_variable = { dev_cost = 1.169 }
	}
	else_if = {
		limit = { date > 2010.1.1 }
		multiply_temp_variable = { dev_cost = 1.0625 }
	}
}
```

Paying for a new IFV with it:

```
set_temp_variable = { dev_cost_min = 0.5 }
set_temp_variable = { dev_cost_max = 5.0 }
calculate_weapon_dev_cost = yes
set_temp_variable = { treasury_change = dev_cost }
multiply_temp_variable = { treasury_change = -1 }
modify_treasury_effect = yes
```

A trigger cannot calculate anything. On a decision, the computed cost must therefore be stored in a country variable before the decision is shown. The money gate checks that variable, and the deduction uses the same variable.

## What to check for every item

1. **Sum the full cost of this one item.** Add every deduction that pays for its development: all stages (prototype, trials, follow-up work), every event in the chain, and recurring costs multiplied by their duration (daily or monthly expenses, a dynamic modifier that adds expenses while the work runs).
2. **The total must be inside the allowed range**: the row's range with the date multiplier applied. For a computed cost, both the lowest and the highest reachable value must be inside it.
3. **Every option counts on its own.** When an event offers choices for the same item (cheap and slow against fast and expensive, for example), each option's total must be inside the range.
4. **Date and economy scaling** must hold, as described in their sections.
5. **Gate, label and deduction must agree.** The amount named by the `custom_cost_text` key (`cost_0_1` = `0.1`) must equal the actual `treasury_change`.
   - The `custom_cost_trigger` threshold is the price or just under it. MD often writes `treasury > 9.9` for a price of 10 or `treasury > 14.99` for 15, so that having exactly the price is enough. That is correct. A threshold above the price, or far below it, is a **MISMATCH**.
   - For a computed cost, the gate and the deduction must use the same stored variable.
   - Before reporting a missing deduction, follow every scripted effect the decision or option calls, because the `treasury_change` may sit inside one of them. If there is still no deduction, the decision shows a price the player never pays. Report it as **MISMATCH**.
   - A deduction on a decision with no money gate lets the player start the work without the money. Report it as a warning.
6. **Localisation must match.** If a description or tooltip states the price, it must state the same amount as the code.

## Out of scope

Do not apply these rules to:

- Producing or buying finished equipment: procurement batches, purchases, deliveries.
- Reactivating or repairing stored equipment when the design does not change.
- Export or modernization contracts done for another country, upkeep, and running costs.
- Buying a licence with no local design work.

If one decision both develops an item and pays for its first batch, only the development part counts. If the code does not let you separate the two, report it as **UNCLASSIFIED** and ask.

## Interpretations to confirm

The following points are this document's reading of the author's rules, and a maintainer may overrule them:

- "Already available" means the base equipment exists in game for this country (in service, in stock, or already designed).
- The most specific row wins: 5th-generation fighter over "New plane", aircraft carrier and submarines over "New ship".
- Each date jump multiplies the previous period's prices (compounding), and the date that counts is when the development starts.
- Costs paid over time are summed into the total.
- Every option of a development event must fit the range on its own.
- The placement guide for fixed costs (lower, middle and upper part) and the economy constants in the example implementation are proposals.
- Every row marked *added* in the cost table.

## Report format

Write the whole report in English, whatever language the request or the code comments are in.

One entry per item:

```
[weapon-dev-cost] <file>:<line>  <decision / event option id>
  item:    <name>
  row:     <cost table row> — <one-line reason>
  period:  <periods in which the development can start>
  country: <tag>, GDP and productivity in those years
  cost:    <total> (<breakdown: stage = value, …>; for a computed cost, its min and max)
  range:   <allowed min>–<allowed max> for each period
  result:  OK | OUT OF RANGE | MISMATCH | DATE | ECONOMY | UNCLASSIFIED
  fix:     <a value or formula that satisfies the rules>
```

Severity:

| Result | Severity |
|---|---|
| OUT OF RANGE | error |
| MISMATCH | error |
| DATE: a fixed cost in content that can start in more than one period | error |
| ECONOMY: inversion, a computed cost that falls as the economy grows or leaves the range, a fixed cost in shared content | error |
| ECONOMY: a fixed cost in the wrong part of the range for the country | warning |
| UNCLASSIFIED | question to a maintainer |

## Worked examples

These are made-up cases that show how to apply the rules. They do not describe the current state of the mod.

| Case | Cost in code | Row | Result |
|---|---|---|---|
| Ukraine modernizes T-64 with a new engine; the decision is available only in 2000–2009 | `-0.1` | Modernization of land equipment | OK |
| An event option develops T-55AGM in 2000–2009 | `-0.02` | Modernization of land equipment | OUT OF RANGE, below `0.05` |
| Ukraine develops a new ATGM in 2000–2009 | `-0.5` | New ATGM | OUT OF RANGE, above `0.3`; fix to about `0.15` |
| Ukraine develops Nota in 2000–2009 | `-4.0` | New tank | OK, an ambitious design sits high in the range |
| Ukraine develops a new IFV in 2015 | `-0.5` | New IFV | OUT OF RANGE, the 2010–2019 minimum is `0.525` |
| A decision with no date limit develops a new IFV for a fixed `-1.0` | fixed | New IFV | DATE, the cost must rise in 2010, 2020 and 2030 |
| The USA develops a 5th-generation fighter in 2000–2009 | `-3.0` | 5th-generation fighter | OUT OF RANGE, below `5.0` |
| A country develops a new aircraft carrier in 2000–2009 | `-12.0` | Aircraft carrier | OK |
| A country modernizes a frigate in 2000–2009 | `-0.5` | Modernization of a ship | OK, the ship range is `0.15`–`1.0` |
| A country upgrades a fighter jet already in service, in 2000–2009 | `-1.5` | Modernization of a plane | OUT OF RANGE, above `0.4` |
| A country develops a new long-range SAM system in 2000–2009 | `-11.0` | Long-range SAM | OUT OF RANGE, above `10.0` |
| New IFV in the same period: Ukraine pays `2.0`, Germany pays `1.0` | fixed | New IFV | ECONOMY, an inversion: Germany's economy is larger |
| A generic decision any country can take develops a new MLRS for a fixed `-2.0` | fixed | New MLRS | ECONOMY, shared content must compute its cost (and DATE if it is not limited to one period) |
| A computed cost that goes down as `gdp_total` goes up | formula | Any | ECONOMY, it must rise with the economy |
| Cost computed as `0.03 - 0.003 × N`, with N from 0 to 6 | `0.012`–`0.03` | Modernization of land equipment | OUT OF RANGE at every N |
| Two stages in 2000–2009: prototype `-0.06` + trials `-0.08` | `0.14` in total | Modernization of land equipment | OK |
| A heavy IFV converted from a tank hull in 2000–2009 | `-0.4` | New vehicle type on an existing hull | OK |
| `custom_cost_text = cost_0_1`, no `treasury_change` in the effects or in any scripted effect they call | none | Any | MISMATCH |
| Gate `treasury > 0.099`, `custom_cost_text = cost_0_1`, `treasury_change = -0.1` | `0.1` | Modernization of land equipment | OK, a gate just under the price is fine |
| A new coastal radar | `-1.0` | none | UNCLASSIFIED, ask a maintainer |
