# AI Strategy and Unit Production Reference

Current weights, thresholds, and per-country values live in the files named here. Read
the file for numbers. This doc covers how the layers fit and the rules that are easy
to get wrong.

## Layers

1. Startup: `give_AI_templates` creates division templates.
   `yearly_investment_targets_routine` builds the investment target list.
2. Continuous strategies in `common/ai_strategy/`: `MD_combat_ai_strategies.txt` (army,
   air, and equipment ratios), `MD_econ_ai.txt` (buildings, PP, factory ratios),
   `naval.txt`, `MD_war_declaration_ai.txt`, and the country files.
3. Periodic effects from `on_weekly` and `on_monthly` in `MD_on_actions.txt`: the
   division, plane, and ship limiter calculations, the investment pulse (`AC_event.500`),
   `ai_cyber_monthly`, `ct_ai_weekly`, `ai_weapon_dump`, `calculate_ai_taxes_desire`,
   influence (`influence.500`), `un_ai_evaluate_actions`, and `recog_ai_monthly`.
4. Event-driven: `on_puppet` and `on_liberate` rerun `give_AI_templates`, and
   `on_declare_war` adds cyber targets. Template conversion decisions
   (`99_ai_templates_decisions.txt`) upgrade militia to light infantry, motorized, and
   mechanized.
5. God of War game rule: `ai_add_xp`, `ai_add_equipment`, and `ai_spawn_units`.

## Threat and unit caps

`ai_is_threatened` is a live scripted trigger. Nothing sets or refreshes a flag for it.

```
ai_is_threatened = {
    OR = {
        has_war = yes
        threat > 0.30
        check_variable = { potential_and_current_enemies^num > 0 }
    }
}
```

`potential_and_current_enemies` is a built-in engine array: current enemies, allies of
enemies, and countries with wargoals. It covers hostile neighbors without a neighbor
loop.

`division_limiter_calculation`, `plane_limiter_calculation`, and
`ship_limiter_calculation` (`00_AI_scripted_effects.txt`) run monthly for AI countries
and on war transitions. Each computes a cap from factory count and situational
multipliers and caches it in `division_limiter_limit`, `plane_limiter_limit`, or
`ship_limiter_limit`. The limiter strategies read the cached variable in `enable`. They
do not recount live. The `potato_edition` rule halves the result.

Above its cap a country gets negative build weights for every land role. A peaceful,
unthreatened country gets a reduced cap. It is not blocked from training.

## Strategy structure

```pdx
my_strategy = {
    allowed = { ... }            # Checked once at game start
    enable = { ... }             # Checked continuously
    abort = { ... }              # If true, removes the strategy
    abort_when_not_enabled = yes

    ai_strategy = {
        type = role_ratio
        id = armor
        value = 50
    }
}
```

- Omitting `allowed` applies the strategy to every country.
- `reversed = yes` swaps direction: "id does X to this country". It needs
  `enable_reverse = { ... }`, which has no default scope.
- Token reference: vanilla `common/ai_strategy/_documentation.md` in the HOI4 install.

## War weighting

- `avoid_starting_wars` is targetless and additive with per-target `conquer` weights.
  Vanilla uses a large negative value to suppress every target, then `conquer` to carve
  one out:

```pdx
ai_strategy = { type = avoid_starting_wars value = -200 }
ai_strategy = { type = conquer id = GER value = 200 }
```

- MD uses both signs on purpose: small positive values as a general brake, and negative
  values for the suppression technique. Do not flag a value as a sign bug without
  reading the surrounding `conquer` strategies.
- `declare_war` needs `id = TAG`. `target =` is not accepted and `dont_declare_war` is
  not a token.
- `enable = { has_war_with = TARGET }` makes `declare_war` a no-op. Gate on
  `has_wargoal_against = X` with `NOT = { has_war_with = X }`, as
  `MD_war_declaration_ai.txt` does.
- One mod-wide block, `MD_avoid_new_wars_when_outmatched`, applies
  `avoid_starting_wars = -200` at `enemies_strength_ratio > 0.75`. Do not add per-tag
  `*_cancel_war_*` blocks, or a per-tag brake on a plain strength-ratio gate. A per-tag
  brake belongs only on a gate the ratio cannot express.
- Ratio direction differs. `strength_ratio = { tag = X ratio < 1 }` means the scope
  country is weaker than X. `enemies_strength_ratio` rises as the scope country's
  enemies get stronger.

## Production

- Army and equipment strategies come in tiers by military factory count. Keep tier
  `enable` ranges exclusive so role weights do not stack.
- APCs use the `amphibious` equipment category and IFVs use `flame`, not `mechanized`.
- Emergency strategies (`MD_wartime_low_*`, `MD_desperately_need_guns`,
  `default_AI_needs_to_live`) halt training and reprioritize when a stockpile runs out.
- A country gets a custom chip or composite production strategy only when it is a
  significant producer. Others use the generic logic.

## Strategy plans (`common/ai_strategy_plans/`)

```pdx
my_plan = {
    name = "Plan Name"             # aiview console only
    allowed = { ... }
    enable = { ... }               # Once met, the plan activates permanently
    abort = { ... }                # Checked daily

    ai_national_focuses = { ... }  # Focus order, ignores ai_will_do
    focus_factors = { ... }        # Multipliers on focus ai_will_do
    research = { ... }
    ideas = { ... }
    traits = { ... }
    ai_strategy = { ... }
    weight = { ... }
}
```

## Research and doctrines

- `common/ai_focuses/` holds research profiles by posture on a 1 to 10 scale. Tech
  `ai_will_do` tiers, date gates, and the GDP gate are in `common/ai_focuses/README.md`.
- The AI rechecks its best doctrine every 30 days, and the highest `ai_will_do` wins.
  Doctrine blocks go: base, context `add`s (3, 5, or 10), a national `add = 30`, then
  `factor = 0` gates last. Keep generic context adds under 30 so a national pick wins.
- Each subdoctrine track has one base 3 default. The other options sit at base 1.

## Templates (`common/ai_templates/`)

```pdx
my_role_entry = {
    role = armor                 # Role token targeted by role_ratio
    blocked_for = { ... }        # Or available_for
    upgrade_prio = { ... }       # Which role to upgrade
    enable = { ... }

    my_target_template = {
        upgrade_prio = { ... }
        enable = { ... }
        reinforce_prio = 1       # 0 low, 1 normal, 2 high
        target_template = {
            support = { SP_AA_Battery = 1 }
            regiments = { armor_Bat = 6  Arm_Inf_Bat = 4 }
        }
        replace_at_match = 0.8
        replace_with = better_template
        target_min_match = 0.5
    }
}
```

Valid roles: `garrison`, `Militia`, `L_Inf`, `marines`, `Special_Forces`,
`Air_helicopters`, `Air_mech`, `infantry`, `apc_mechanized`, `ifv_mechanized`, `armor`.
Zombie roles: `zombie_horde`, `zombie_horde_runner`, `zombie_horde_brute`.

## Weight blocks

- The value starts at 1. `base` sets it, `factor` multiplies, `add` adds. Operations
  apply top to bottom.
- `ai_will_do` (focuses, tech, decisions): the AI rolls a random number up to the value
  and picks the highest.
- `ai_chance` (event options): proportional probability with a 1% floor.

## Pitfalls

- `role_ratio id = mechanized` does nothing. Use `apc_mechanized` or `ifv_mechanized`.
- `role = armored` in a template is never selected. Use `armor`.
- A case-mismatched unit name silently drops the battalion.
- A factory count with no enabled template leaves the role empty. Keep ranges contiguous.
- A CAS design with the `medium_as_fighter` role deploys as air superiority. Use
  `medium_cas_fighter`.
- A nation in `blocked_for` needs its own coverage for every role.
