# Fix Unrealistic Unemployment in Developing Nations

## Context

Developing nations like Algeria start with ~50% unemployment, which is wildly unrealistic (IRL Algeria had ~10-12% in 2000). This happens because the employment model only counts workers in **formal sectors** (factories, offices, power plants, healthcare, bureaucracy) plus subsistence agriculture. There is no representation for the informal economy, services, retail, construction, transport, or self-employment — sectors that employ 30-50% of workers in developing nations IRL.

The high unemployment then triggers a vicious cycle: stability penalties + social cost multiplier increase (x-2) -> welfare costs spike -> budget crisis -> player forced to slash welfare -> threshold buffer drops -> even worse penalties.

## Approach: Add Informal & Services Sector + Soften Social Cost Penalty

Two complementary changes:

### Change 1: Add Informal & Services Sector (main fix)

**File:** `common/scripted_effects/00_money_system.txt`

Insert after line 4927 (after bureaucracy/healthcare/all formal sectors, **before** the unemployment calculation at line 4929):

A new sector that absorbs remaining workforce into informal/services employment **as a residual** -- buildings and all formal sectors get workers first, then the informal sector absorbs a portion of what's left. This mirrors reality: when formal jobs appear, people leave the informal economy.

The percentage scales inversely with GDP/C:

- Formula: `percentage = 0.55 - 0.005 x GDP/C`, clamped [0.05, 0.55]
- Applied to **remaining** `workforce_total` (after ALL formal sectors have been staffed)

| GDP/C | Example    | Informal % of remaining workforce |
| ----- | ---------- | --------------------------------- |
| 1     | Very poor  | 54.5%                             |
| 8.8   | Algeria    | 50.6%                             |
| 20    | Mid income | 45%                               |
| 60    | USA        | 25%                               |
| 100+  | Rich       | 5% (floor)                        |

GDP contribution: 1.5 per worker (low productivity -- reflects informal economy reality). Supports a custom modifier `informal_services_workers_modifier` for content to adjust per-country.

**Allocation order (revised):**

1. Resource extraction -> 2. Subsistence agriculture -> 3. Power plants -> 4. Military/naval facs -> 5. Civ facs, offices -> 6. Agriculture districts, microchip/composite/synthetic -> 7. Internet stations -> 8. Healthcare -> 9. Bureaucracy -> **10. Informal & Services (NEW)** -> 11. Remaining = Unemployed

Buildings always get workers first. The informal sector only absorbs leftover workers that would otherwise be counted as unemployed.

### Change 2: Reduce Social Cost Multiplier from x-2 to x-1

**File:** `common/scripted_effects/00_money_system.txt` line 4954

Change `multiply_variable = { high_unemployment_modifier_var_2 = -2 }` to `-1`

Currently max unemployment penalty (-0.3 stability) translates to +60% social cost. With `-1` it becomes +30% -- still meaningful but breaks the death spiral.

### Change 3: Integrate Informal Sector into GDP Totals

**File:** `common/scripted_effects/00_money_system.txt`

- Line 5065: Add `add_to_variable = { gdp_total = gdp_from_informal_services }` after resource sector GDP
- Line 5081: Add `set_variable = { informal_services_percent = gdp_from_informal_services }`
- Line 5094: Add `divide_variable = { informal_services_percent = gdp_total }`
- Line 5108: Add `clamp_variable = { var = informal_services_percent min = 0 max = 1 }`

### Change 4: Register Custom Modifiers

**File:** `common/modifier_definitions/money_modifier_definitions.txt`

After `agriculture_workers_modifier` block (~line 492), add:

- `informal_services_workers_modifier` (percentage, precision 2, category country)
- `informal_services_productivity_modifier` (percentage, precision 2, category country)

### Change 5: Update Employment Tooltip

**File:** `localisation/english/MD_money_l_english.yml` line 81

In `EMPLOYMENT_TOOLTIP_DELAYED`, after `Government Administration` line, add:

```
Informal & Services: [?ROOT.informal_services_workers|3]
```

Rename `Unemployed & Subsistence` to `Unemployed` (subsistence is now covered by informal sector).

### NOT Changing (and why)

- **Workforce participation rate (0.6 base):** Would cascade through entire economy
- **GDP/C scaling on penalty:** Already protects poor nations (low GDP/C = low multiplier)
- **Unemployment threshold base (6%):** Reasonable, modified by social laws
- **Agriculture formula:** Works fine for very poor nations; informal sector covers the gap for mid-income
- **Non-English localisation files:** Per project rules, only English localisation is edited

## Expected Impact on Algeria

Before: ~50% unemployment -> -30% stability, +60% social cost multiplier
After: ~8-12% unemployment -> ~-2% stability, ~+4% social cost multiplier (realistic)

## Verification

1. Start a game as Algeria, check unemployment tooltip -- should show ~10-12% with informal sector workers visible
2. Start as USA -- unemployment should be largely unchanged (formal sector already absorbs most workers)
3. Start as a very poor African nation -- informal sector should absorb most workers, unemployment reasonable
4. Check budget screen -- welfare costs should be manageable, no immediate death spiral
5. Run validation tools to check for syntax errors
