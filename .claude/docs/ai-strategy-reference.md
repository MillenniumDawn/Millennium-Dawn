# AI Strategy & Unit Production Reference

## System Architecture

5 AI layers firing at different frequencies:

```
LAYER 1: INITIALIZATION (on_startup, once)
  give_AI_templates ──► creates division templates
  yearly_investment_targets_routine ──► builds investment target list

LAYER 2: CONTINUOUS STRATEGIES (ai_strategy files, always-evaluated)
  MD_combat_ai_strategies ──► army/air/equipment ratios (reads ai_is_threatened trigger + cached *_limiter_limit vars)
  MD_econ_ai ──► building targets, PP priorities, factory ratios
  naval.txt ──► ship ratios, mission thresholds
  Country-specific files ──► diplomacy, war, production overrides

LAYER 3: PERIODIC EFFECTS (on_daily / on_weekly / on_monthly)
  Daily (AI only):
    division/plane/ship_limiter_calculation ──► cache unit caps into *_limiter_limit vars
  Weekly:
    AI Investment Pulse ──► AC_event.500 ──► AI_get_*_score effects
    ai_cyber_monthly ──► cyber operations against enemies
    ct_ai_weekly ──► counter-terror actions
  Monthly:
    ai_weapon_dump ──► sell excess equipment for cash
    calculate_ai_taxes_desire ──► adjust tax rates
    AI influence spreading ──► influence.500 ──► AI_select_influence_target
    un_ai_evaluate_actions ──► SC/GA proposals
    recog_ai_monthly ──► recognition campaigns
    yearly_investment_targets_routine (January) ──► rebuild targets

LAYER 4: EVENT-DRIVEN (on_war, on_puppet, etc.)
  on_declare_war ──► cyber targeting
  on_puppet / on_liberate ──► give_AI_templates
  on_join/leave_faction ──► reserve currency switch
  Template conversions ──► militia→L_Inf→mot→mech (every 300 days)

LAYER 5: GOD OF WAR OVERRIDES (game rule gated)
  ai_add_xp ──► monthly XP
  ai_add_equipment ──► top up stockpiles when facing players
  ai_spawn_units ──► spawn divisions when facing players
```

## On-Action Entry Points

### on_startup (`common/on_actions/00_on_actions.txt`)

- **AI Template Init** (line ~1710): every AI country (zombie/joke tags excluded, see `give_AI_templates`) → `give_AI_templates`. Also sets microstate tax rates and investment targets.

### on_daily (`common/on_actions/00_on_actions.txt`)

- **AI Unit-Cap Cache** (line ~101): AI only → `division_limiter_calculation` + `plane_limiter_calculation` + `ship_limiter_calculation`. Each recomputes the cached `*_limiter_limit` variable the matching limiter strategy reads in its `enable`.

### on_monthly (`common/on_actions/MD_on_actions.txt`)

- **AI Weapon Dump** (line ~939): All AI → `ai_weapon_dump`
- **AI Taxes** (line ~964): All AI → `calculate_ai_taxes_desire`
- **AI Influence** (line ~817): AI + PP > 200 + not subject + not bankrupt → `influence.500`
- **AI Investment Targets** (January only, line ~730): Regional+ powers → `yearly_investment_targets_routine`
- **AI UN Actions** (line ~1241): `un_ai_evaluate_actions`
- **AI Recognition** (line ~1243): `recog_ai_monthly`
- **God of War** (line ~966): `ai_add_xp`, and if no player allies + threat > 0.3: `ai_add_equipment` + `ai_spawn_units`

### on_weekly (`common/on_actions/MD_on_actions.txt`)

- **AI Investment Pulse** (line ~80): Regional+ powers with investment targets → `AC_event.500`
- **AI Cyber** (line ~178): Rotates through 4 weekly batches → `ai_cyber_monthly`
- **AI Counter-Terror** (same lines): `global.active_terror_orgs^num > 0` → `ct_ai_weekly`

### Other on_actions

- **on_puppet** (`01_tfv_on_actions.txt:93`): AI puppeted nations → `give_AI_templates`
- **on_declare_war** (`00_on_actions.txt:2049`): AI combatants with cyber capability → `ai_cyber_add_target` on each other
- **on_join_faction / on_leave_faction** (`MD_on_actions.txt:1270`): AI reserve currency auto-switch (Chinese faction → yuan, Russian → rouble, else → dollar)

Threat state is no longer pushed by these hooks. It is evaluated live by the `ai_is_threatened` scripted trigger (see below), so nothing has to set or refresh a flag on war/justification/liberation.

## Scripted Effects

### `ai_is_threatened` (`common/scripted_triggers/00_scripted_triggers.txt`)

Live threat check, evaluated on demand (no cached flag, no daily refresh):

```
ai_is_threatened = {
    OR = {
        has_war = yes
        threat > 0.30
        check_variable = { potential_and_current_enemies^num > 0 }
    }
}
```

`potential_and_current_enemies` is a built-in engine array (current enemies + allies-of-enemies + countries with wargoals), so it already covers hostile neighbours without a live neighbour loop. When `ai_is_threatened`:

- The division/plane/ship limiter caps expand (1.25x multiplier inside the daily calc).
- `ai_default_no_build_units` deactivates → unit training allowed.

This replaced the old `ai_update_build_units` effect and its `AI_is_threatened` country flag (removed). Subjects are no longer auto-flagged; `ai_default_no_build_units` excludes them with `is_subject = no`.

### `division_limiter_calculation` / `plane_limiter_calculation` / `ship_limiter_calculation` (`00_AI_scripted_effects.txt`)

Run daily for AI countries. Each computes a cap from factory count and situational multipliers (war, `ai_is_threatened`, major, NATO/EU, threat, faction, great-power) and stores it in `division_limiter_limit` / `plane_limiter_limit` / `ship_limiter_limit`. The matching limiter strategy reads that variable in `enable` instead of recomputing the math every evaluation. Under the `potato_edition` game rule the same formula runs, then the result is halved (`x0.5`) and re-rounded.

### `ai_weapon_dump` (`99_weapon_dump_effects.txt`)

Monthly, all AI at peace with threat < 0.51. Sells excess equipment for 30 treasury per dump:

- Infantry weapons > 150k → dump 25k (x2)
- CNC > 20k → dump 5k
- L_AT/AA > 12k → dump 2k each
- Various tank chassis > 2.5-5k → dump 500 each
- Artillery > 5k → dump 750

### `calculate_ai_taxes_desire` (`00_money_system.txt:5210`)

Monthly tax rate adjustment:

- **Raise taxes** if deficit (treasury_rate < -1 for pop, < -2 for corp, or interest > 8%). Caps: pop=40, corp=50.
- **Lower taxes** if surplus (treasury_rate > 2, debt_ratio < 0.30, interest < 5). Prefers lowering corp first.
- **Low stability override**: Lowers pop tax if stability < 0.25.

### AI Investment System (`99_AI_investment_scripted_effects.txt`)

10 building-type scoring effects. Each scores states with base value + bonuses/penalties:

- CIC (base 170), MIC (base 150), Dockyard (base 170), Infra (base 175), Offices (base 180)
- AA (base 120), Radar (base 115), Airbase (base 130)
- High `threat` (tiered at 0.1 / 0.2 / 0.4) adds to military buildings
- All add randomization (±15) to prevent same state always winning

### AI Influence System (`99_AI_influence_scripted_effects.txt`)

Monthly target selection scoring: player targets (+30 veteran), faction members (+25), guarantees (+20), trade agreements (+35), existing influence position (up to +95), same ideology (+25), opinion (0.3x clamped), same continent (+25).

### Template Conversion Decisions (`99_ai_templates_decisions.txt`)

| Decision                       | Cooldown  | Requirements                             | Converts                              |
| ------------------------------ | --------- | ---------------------------------------- | ------------------------------------- |
| `convert_militia_to_light_inf` | 300 days  | No war, weapons > 2k, CNC > 500, MIL > 5 | 5 militia → L_Inf                     |
| `convert_l_inf_to_mot_inf`     | 300 days  | No war, util vehicles > 500, MIL > 10    | 5 L_Inf → motorized                   |
| `convert_mot_to_mech_inf`      | 300 days  | No war, APC chassis > 500, MIL > 20      | 5 mot → mechanized                    |
| `UKR_convert_stuff`            | Fire once | UKR, date > 2000.6, no war               | All militia → L_Inf, all L_Inf → mech |

## AI Strategy Files

### Strategy Structure

```pdx
my_strategy = {
    allowed = { ... }            # Checked ONCE at game start (permanent gate)
    enable = { ... }             # Checked continuously
    abort = { ... }              # If true, removes strategy (must be false to activate)
    abort_when_not_enabled = yes # Also removes if enable becomes false

    ai_strategy = {
        type = role_ratio        # Strategy type
        id = armor               # Target (role, tag, etc.)
        value = 50               # Positive = more, negative = less
    }
}
```

### Reversed Strategies

`reversed = yes` swaps direction: instead of "this country does X to id", it becomes "id does X to this country". Requires `enable_reverse = { ... }` (no default scope, must scope into a country).

Example: Iran's `PER_support_shias` makes Shia countries support Iran (rather than Iran supporting them).

### War & Conquer Weighting (`conquer` + `avoid_starting_wars`)

`avoid_starting_wars` is **additive with the `conquer` strategy and targetless** (per vanilla `_documentation.md`) — it combines with per-target `conquer` weights rather than acting as a standalone "avoidance" dial, so its effect depends on the conquer context. Vanilla's example uses a large negative value to suppress all targets, then `conquer` to carve out one:

```pdx
ai_strategy = { type = avoid_starting_wars value = -200 }   # targetless, additive with conquer
ai_strategy = { type = conquer id = GER value = 200 }       # GER: -200+200 = 0 (the only viable target); everyone else -200
```

Vanilla notes this is "meant for very specific situations, and should not be used widely."

In MD both signs appear intentionally:

- Small **positive** values as a general brake on opening new wars (e.g. RAJ's insurgency strategies use `+20` / `+50` while suppressing a rebellion). The mod author has confirmed positive = stronger avoidance in this usage.
- **Negative** values for the targetless-suppression technique above (e.g. RAJ's `-100` while already at war with Pakistan, to avoid opening new fronts).

**Do not flag an `avoid_starting_wars` value as a sign bug** in either direction without checking the surrounding `conquer` strategies and the author's intent. It is nuanced, not a simple "higher = more peaceful" scalar.

Authoritative token reference: vanilla `common/ai_strategy/_documentation.md` (in the HOI4 install). Mirror gotchas here as they come up.

### `MD_combat_ai_strategies.txt` — Production & Combat

**Army production (3 tiers by factory count):**
| Strategy | MIL Range | Key Ratios |
|----------|-----------|------------|
| `default_army_production_strategy` | < 11 | L_Inf=30, infantry=20, mech/IFV=50, armor=35 |
| `default_army_production_strategy_maj` | > 10 | IFV=50, armor=40, SF=50, marines=20 |
| `default_army_production_strategy_global` | > 29 | Further IFV/armor emphasis |

**Note:** `_maj` and `_global` stack at MIL > 29, doubling role weights.

**Emergency strategies:**

- `default_AI_needs_to_live`: surrender > 49% → L_Inf=150
- `MD_build_equipment_not_units_while_at_war`: At war + low stocks → halt training, boost weapons
- `MD_desperately_need_guns`: Zero infantry weapons → massive production, all training halted

**Equipment production (3 tiers):**
| Strategy | MIL Range | Focus |
|----------|-----------|-------|
| `MD_poor_production_strategy` | < 6 | Infantry weapons dominate |
| `MD_default_production_strategy` | 6-10 | Balanced with mech/armor intro |
| `MD_major_production_strategy` | > 10 | Full spectrum with min factory targets |

**Division/Ship/Plane Limiters:**

- `division_limiter`: factories × situational modifiers. Active war scales up (~1.75x, wars demand more divisions than peacetime), `AI_is_threatened` adds ~1.25x, major status adds ~1.15x. Alliances that constrain unilateral builds (NATO, EU) apply a negative multiplier (~-0.8x) so members don't all maintain peer-major standing armies.
- `division_limiter_potato_edition`: 0.5x base for the "performance" rule path, extra penalties for very large factions (CHI/SOV) so end-game stutter stays manageable.
- `ship_limiter`: naval_factories × ~7 (or ×3 potato), tuned so a typical naval power lands at a plausible fleet size, not the engine's hard cap.
- `plane_limiter`: mil_factories × ~80 + 50 (or ×40 potato), accounts for air industries producing many cheap units per factory vs ground.

**Unit build controls:**

- `ai_default_no_build_units`: No war + not threatened → all roles -500
- `ai_subject_defensive_build`: Subjects at peace → garrison=5, L_Inf=10, infantry=5, force_build=25

**Air production (3 tiers):**

- `< 25 MIL`: Tactical bombers only
- `25-49 MIL`: Mixed CAS + interceptors + tactical
- `> 49 MIL`: Full air force (heavy fighters, strategic bombers)

### `MD_econ_ai.txt` — Economic Behavior

**PP spending:**

- `save_pp_for_laws`: Major economic problems → save all PP for law changes
- `AI_idea_focus`: Surplus + lacking top ideas → massive idea spending (5000)

**Factory building targets (scaled by power level):**
| Power Level | CIC Target |
|-------------|-----------|
| Minor/non-power | +50 |
| Regional | +75 |
| Large | +100 |
| Great | +125 |
| Super | +150 |

**Economic crisis response:**

- `AI_stop_building_civilian_industry`: < 1% unemployment → halt industry, build internet/infra
- `AI_reduce_construction_on_deficit`: High deficit → -20 all building
- `AI_halt_construction_major_crisis`: Major problems → -50 all building
- `AI_no_military_industry`: Peacetime + low threat + < 5 available civs → no mils

**Microchip/composite production:**

- Nations consuming + importing more than producing → build chip/composite factories.
- Custom production strategies exist for the major industrial powers (currently USA, CHI, FRA, GER, JAP, KOR, CAN); other nations fall back to generic logic. Add a new strategy when a country becomes a significant chip/composite producer in scenario terms.

### `naval.txt` — Naval Behavior

**Default ratios:** Corvettes=30, frigates=20, destroyers=10, attack subs=25, mine sweepers=5

**Mission management:**

- Peacetime: Patrol, strike force, convoy escort/raid
- Fuel < 25%: Halt most missions
- All enemies landlocked: Halt all naval
- Peacetime + any navy: Halt all missions (conserve fuel)

**Regional dominance (war-triggered):** 10 theater-specific strategies covering Pacific, Chinese coastline, Middle East, Mediterranean, Atlantic, Indian Ocean.

### Country-Specific Files (107 files)

**Key force_build_armies values:**

| Country | Value     | Condition                             |
| ------- | --------- | ------------------------------------- |
| USA     | 50        | Always                                |
| SOV     | 50        | Always                                |
| CHI     | 50        | Always                                |
| GER     | 50        | Always                                |
| UKR     | 50/150/50 | Always / SOV threatening / BLR allied |
| CAN     | 100       | Preparing for war                     |
| ARG     | 100       | Preparing for war                     |
| RAJ     | 100       | China aggressive                      |
| KOS     | 150       | Always                                |
| DPR/HPR | 150       | Always                                |
| CHE     | 150       | Always                                |
| ZOM     | 200       | Always                                |

**Notable diplomacy patterns:**

- **Japan**: Most pacifist AI, `declare_war = -200` against 24 neighbors
- **SOV**: `declare_war = -4000` against nations guaranteed by TUR/CHI
- **USA during War on Terror**: `pp_spend_priority` forces decision spending (decisions=250, all others=-9999)

## AI Strategy Plans (`common/ai_strategy_plans/`)

22 files defining political path priorities. Key features:

```pdx
my_plan = {
    name = "Plan Name"           # For aiview console (never shown to player)
    allowed = { ... }            # Checked once at start
    enable = { ... }             # Once met, plan activates permanently
    abort = { ... }              # Checked daily to deactivate

    ai_national_focuses = { ... }  # Focus order (ignores ai_will_do)
    focus_factors = { ... }        # Multipliers on focus ai_will_do
    research = { ... }             # Multipliers on tech category ai_will_do
    ideas = { ... }                # Multipliers on idea/advisor ai_will_do
    traits = { ... }               # Multipliers on leader trait ai_will_do
    ai_strategy = { ... }          # Strategies when plan is active
    weight = { ... }               # MTTH block for overall plan weight
}
```

**Countries with strategy plans:** BHR, BOS, BRA, BRM (5 paths), CAN, CHI (3), CZE (4), FRA (3), HOL (3), ITA (10), JAP, LBA (7), NIG (3), NKO (3), POL (5), SAU (5), SIN (3), SWE (3), SWI (4), SYR (5)

**Notable:** CAN nationalist plan sets `force_build_armies = 1000`, antagonizes USA. HOL all plans set `force_build_armies = 100`.

## AI Focuses (`common/ai_focuses/`)

4 files defining research emphasis by AI posture:

| Profile                       | Key Research Categories                              |
| ----------------------------- | ---------------------------------------------------- |
| `ai_focus_defense`            | Artillery, infantry weapons, SAM (SOV/USA)           |
| `ai_focus_aggressive`         | Armor                                                |
| `ai_focus_war_production`     | Construction, fuel, nanofibers, 3D printing, AI tech |
| `ai_focus_military_equipment` | Infantry weapons, AT, AA, artillery, doctrine (SOV)  |

Country-specific overrides: SOV (very high war production weights 55.0), USA (SAM in defense, lighter war production), RAJ (India-specific).

## AI Templates (`common/ai_templates/`)

### Structure

```pdx
my_role_entry = {
    role = armor                 # Role token (targeted by role_ratio)
    blocked_for = { ... }        # OR available_for (one country = one template per role)
    upgrade_prio = { ... }       # MTTH: weighted-random for which role to upgrade
    enable = { ... }             # If false, template doesn't exist

    my_target_template = {
        upgrade_prio = { ... }   # Deterministic: which target to aim for
        enable = { ... }
        reinforce_prio = 1       # 0=low, 1=normal, 2=high
        target_template = {
            support = { SP_AA_Battery = 1 }
            regiments = { armor_Bat = 6  Arm_Inf_Bat = 4 }
        }
        replace_at_match = 0.8   # Switch to replace_with at this match score
        replace_with = better_template
        target_min_match = 0.5
    }
}
```

### Valid Roles

`garrison`, `Militia`, `L_Inf`, `marines`, `Special_Forces`, `Air_helicopters`, `Air_mech`, `infantry`, `apc_mechanized`, `ifv_mechanized`, `armor`

God of War additional: `Air_helicopters`, `ifv_mechanized`, `armor`, `marines`, `Special_Forces`

Zombie: `zombie_horde`, `zombie_horde_runner`, `zombie_horde_brute`

### Factory Threshold Coverage

| Role            | Template                 | MIL Range              |
| --------------- | ------------------------ | ---------------------- |
| garrison        | Militia_garrison         | < 11, not major        |
| garrison        | L_Inf_gar                | < 21, not major        |
| Militia         | Militia_generic          | War + < 4, not major   |
| Militia         | militia_brigade          | War or < 10, not major |
| L_Inf           | L_Inf_brigade            | < 8, not major         |
| L_Inf           | L_Inf_division           | 7-15 or major          |
| infantry        | infantry_generic         | < 8                    |
| infantry        | infantry_division        | 8-15                   |
| apc_mechanized  | mechanized_generic       | < 15                   |
| apc_mechanized  | mechanized_divisions     | > 14                   |
| ifv_mechanized  | ifv_infantry_generic     | < 16                   |
| ifv_mechanized  | ifv_infantry_divisions   | > 15                   |
| armor           | armor_generic            | 11-20                  |
| armor           | armor_division           | > 20                   |
| marines         | light_marine_brigades    | < 5, naval > 0         |
| marines         | mot_marines_brigades     | < 12, naval > 0        |
| marines         | meh_marines_division_maj | 12-24, naval > 0       |
| marines         | armored_marines_division | > 14, naval > 0        |
| Special_Forces  | Special_Forces_generic   | 5-10                   |
| Special_Forces  | special_forces_division  | > 10                   |
| Air_helicopters | Arm_Air_assault_brigade  | > 20                   |
| Air_mech        | Air_Mech_generic         | 10-15                  |
| Air_mech        | Air_Mech_division        | > 15                   |

## MTTH Blocks (Priority/Weight Syntax)

Used throughout the AI system for priorities, weights, and `ai_will_do` values.

- Starts at assumed value of **1**
- `base = N` — sets value to N
- `factor = N` — multiplies current value by N
- `add = N` — adds N to current value
- Operations apply **in order** (top to bottom)
- `modifier = { ... }` — conditional: triggers + value operations
- Variables can be used in value arguments

### ai_will_do vs ai_chance

- `ai_will_do` — focuses, tech, decisions. AI picks highest value after generating random [0, value].
- `ai_chance` — event options. Probability-proportional-to-size with d100. Min probability = 1%.

## Common Pitfalls

| Issue                                          | Impact                                | Prevention                               |
| ---------------------------------------------- | ------------------------------------- | ---------------------------------------- |
| `role_ratio id = mechanized`                   | Wasted production weight              | Use `apc_mechanized` or `ifv_mechanized` |
| `role = armored` in templates                  | Template never selected               | Use `armor`                              |
| Case-mismatched unit names                     | Battalion silently missing            | `validate_oob_units` pre-commit hook     |
| Factory threshold gaps                         | No template at specific factory count | Ensure contiguous ranges                 |
| `_maj` + `_global` stacking at MIL > 29        | Doubled role weights                  | By design but notable                    |
| Missing equipment coverage for blocked nations | AI can't produce equipment            | Check all roles covered                  |
| CAS designs with `medium_as_fighter` role      | Deployed as air superiority           | Use `medium_cas_fighter`                 |
