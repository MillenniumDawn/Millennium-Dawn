# AI Naval Equipment Optimization Plan

## Context

After renaming 298 `ai_equipment` headers and adding 768+150 tech-gated priority blocks across all naval files, two systemic issues remain:

1. **Wrong max tier values** caused the original script to omit `-999` deprioritize modifiers on non-final tiers for 3 hull types
2. **`generic_naval.txt` blocked_for lists are severely incomplete** — 52 countries now have dedicated naval files but the blocked_for lists only cover ~20, causing the AI to waste XP building both generic AND country-specific designs for the same role

---

## Step 1: Fix Max Tier Values & Add Missing -999 Modifiers

The original `fix_naval_ai.py` script used incorrect max tiers for 3 hull types:

| Hull Type           | Script used | Actual (from MTG_naval.txt) |
| ------------------- | ----------- | --------------------------- |
| frigate_hull        | 5           | **6**                       |
| battle_cruiser_hull | 3           | **4**                       |
| carrier_hull        | 3           | **5**                       |

**Impact:** Priority blocks generated for these hull types at the (wrong) "last tier" are missing the `-999 has_tech = next_tier` line. The AI will never deprioritize these variants when a newer hull becomes available.

**Affected variants:**

- `frigate_hull_5` — missing `-999 has_tech = frigate_hull_6` (27 files)
- `battle_cruiser_hull_3` — missing `-999 has_tech = battleship_hull_4` (uses TECH_OVERRIDE)
- `carrier_hull_3` — missing `-999 has_tech = carrier_hull_4`
- `carrier_hull_4` — missing `-999 has_tech = carrier_hull_5`
- Also: `battle_cruiser_hull_4` and `carrier_hull_5` variants may exist and need priorities added with no -999 (true last tier)

**Action:** Write `tools/fix_max_tier_priorities.py` to:

1. Scan all naval files for priority blocks with `has_tech = frigate_hull_5` / `battle_cruiser_hull_3` / `carrier_hull_3` / `carrier_hull_4`
2. If the priority block lacks a `-999` modifier for the next tier, add one
3. Check for variants using hull tiers 4+ for battle_cruiser and 4-5 for carrier that may be missing priorities entirely
4. Update `fix_naval_ai.py` and `fix_missing_naval_priorities.py` MAX_TIER values for future runs

**Files modified:** All naval ai_equipment files containing affected hull types + the two tool scripts

### Research findings (from exploration)

**frigate_hull_5 issues:**

- 26 files have frigate_hull_6 variants BUT their frigate_hull_5 priority blocks are missing `-999 has_tech = frigate_hull_6`
- These include: AST, BRA, CAN, CHI, DEN, EGY, ENG, FRA, GER, GRE, HOL, IND, ITA, JAP, KOR, NKO, PER, POR, RAJ, SIA, SOV, SPR, SWE, TAI, USA, generic_naval
- Most files have 2 blocks missing the modifier; SPR and generic_naval have 1 each
- 27 additional files have frigate_hull_5 variants but NO frigate_hull_6 variants — these are correct as-is (no need for -999)

**battle_cruiser_hull and carrier_hull:** Still need exploration to identify exact affected files.

---

## Step 2: Update `generic_naval.txt` blocked_for Lists

The blocked*for lists were written when only ~20 countries had dedicated naval files. Now 52+ countries have them plus regional zzz*\* files cover additional tags.

**Current state vs needed (tags to ADD):**

| Design Group                      | Role                      | Current blocked count | Tags to add                                                                                                                                                                                  |
| --------------------------------- | ------------------------- | --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `generic_corvettes`               | naval_corvettes           | 21                    | +31: AGL ALG ARG AST BEL CHL COL DEN EGY ENG EST FIN FRA GAH ISR KEN LAT LIT LUX MOR NIG NOR PHI PRU SAF SAU SIN SPA UAE UKR VEN                                                             |
| `generic_frigates`                | naval_frigate             | 23                    | +29: AGL ALG ARG BEL CHL COL EGY ENG EST FIN FRA GAH ISR KEN LAT LIT LUX MOR NIG NOR PHI PRU SAF SAU SIN SPA UAE UKR VEN                                                                     |
| `generic_destroyer`               | naval_destroyer           | 22                    | +29: AGL ALG BEL CHL DEN EGY ENG EST FIN FRA GAH ISR KEN LAT LIT LUX MOR NIG NKO NOR PHI PRU SAF SAU SIN SPA UAE UKR VEN                                                                     |
| `cruiser_gun_based`               | naval_cruiser             | 5                     | +46: AGL ALG ARG AST BEL BRA CHL COL DEN EGY ENG EST FIN FRA GAH GRE HOL IND ISR KEN KOR LAT LIT LUX MAY MOR NIG NKO NOR PER PHI POR PRU RAJ SAF SAU SIA SIN SPA SWE TAI TUR UAE UKR VEN VIE |
| `generic_heavy_nuclear_submarine` | naval_attack_submarine    | 21                    | +31: AGL ALG ARG AST BEL CHL COL DEN EGY ENG EST FIN FRA GAH ISR KEN LAT LIT LUX MOR NIG NOR PHI PRU SAF SAU SIN SPA UAE UKR VEN                                                             |
| `generic_missile_submarine`       | naval_missile_submarine   | 9                     | +42: AGL ALG ARG AST BEL BRA CAN CHL COL DEN EGY ENG EST FIN FRA GAH GER GRE HOL IND ISR KEN LAT LIT LUX MOR NIG NOR PER PHI POR PRU SAF SAU SIA SIN SPA SWE TUR UAE UKR VEN                 |
| `helicopter_operator`             | naval_helicopter_operator | 19                    | +7: AST DEN EGY ENG FRA JAP NKO                                                                                                                                                              |
| `generic_carrier`                 | naval_carrier             | 11                    | +43: AGL ALG ARG AST BEL CAN CHL COL DEN EGY ENG EST FIN FRA GAH GER HOL IND ISR KEN LAT LIT LUX MAY MOR NIG NKO NOR PER PHI POR PRU SAF SAU SIN SPA SWE TAI TUR UAE UKR VEN VIE             |
| `stealth_destroyer`               | naval_stealth_destroyer   | 13                    | +4: AST ENG FRA NKO                                                                                                                                                                          |

**Groups left unchanged:**

- `lhd_heli_operator` (naval_lhd) — no country-specific LHD designs exist, universal is intentional
- `mine_sweeper` (naval_mine_sweeper) — same, no country-specific files

**Action:** Write `tools/fix_generic_naval_blocked.py` to programmatically update each blocked_for list. The script will:

1. Parse all non-generic naval files to find which tags have specific coverage for each role
2. Merge with existing blocked_for
3. Sort alphabetically and rewrite the blocked_for line

**File modified:** `common/ai_equipment/generic_naval.txt`

---

## Step 3: Fix KOR Carrier Overlap

**Problem:** KOR appears in both:

- `KOR_naval.txt` (has its own carrier design group)
- `zzz_SEA_Carriers.txt` (`available_for = { TAI SIN IND PHI KOR }`)

**Action:** Remove KOR from `zzz_SEA_Carriers.txt` available_for since KOR has its own dedicated carrier designs.

**File modified:** `common/ai_equipment/zzz_SEA_Carriers.txt`

---

## Step 4: Update Tool Scripts

Update the MAX_TIER constants in both tool scripts for future use:

- `tools/fix_naval_ai.py` — update MAX_TIER
- `tools/fix_missing_naval_priorities.py` — update MAX_TIER

Correct values:

```python
MAX_TIER = {
    'attack_submarine_hull': 6, 'missile_submarine_hull': 6,
    'corvette_hull': 6, 'frigate_hull': 6,
    'destroyer_hull': 5, 'cruiser_hull': 5,
    'battleship_hull': 4, 'battle_cruiser_hull': 4,
    'carrier_hull': 5, 'mine_sweeper_hull': 2,
}
```

---

## Not Changing (Intentional Patterns)

- **Unique vs regular design groups** (e.g., `USA_unique_frigates` + `USA_frigates`): The "unique" groups contain historical ship classes (Knox, Type 21, Niterói) while "regular" groups are era-based generics. This redundancy appears intentional for AI flexibility.
- **USA/FRA battlecruiser duplicates**: Multiple BC groups per country may represent different specializations (AAW vs ASuW).
- **LHD and mine_sweeper universal access**: No country-specific designs exist for these roles.

---

## Verification

After all changes:

1. `grep -c 'blocked_for' common/ai_equipment/generic_naval.txt` — should show blocked_for on all 9 relevant design groups
2. Run the overlap analysis script again to confirm overlaps reduced from 376 to near-zero for generic conflicts
3. Spot-check a few files to verify -999 modifiers were correctly added
4. Check brace matching: `python3 -c "..."` brace-counting script on modified files
