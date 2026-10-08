# Event Reference

Scripted effects library: `docs/src/content/resources/scripted-effects-reference.md`.

## Authoring rules

- Use `is_triggered_only = yes` and wire the caller. Never write open-fire MTTH events.
  MTTH weights in `random_events` pools are a separate mechanism, described below.
- Match every id to the file's declared namespace and every option log to its own id.
  `tools/linting/fix_log_ids.py` fixes copied log ids.
- Only an option that runs effects gets a log. Omit a log-only `immediate` block.
- `fire_only_once = yes` does not stop an on_action from firing the event again. Guard
  in the caller's `limit`, on state the event changes or on a flag set at queue time.
- Only news events use `major = yes`. Fire one broadcast, never one per country
  through `every_country` or `every_other_country`.
- Pure notifications use `minor_flavor = yes`. Batch repeated deliveries as described below.
- Resolve pictures against MD's `interface/*.gfx`, not vanilla event art. Check that
  the texture exists and fits the window before using the sprite.
- Raw `add_building_construction` for `naval_base` requires a `province`.
  Building scripted effects charge treasury internally; do not charge twice.
- New party entries also need the hooks in [Party Localisation](party-loc-reference.md).
- Permanent effects on another nation come from an event, so the target gets a choice.
  Aim for 10 to 15 flavor events per country.

In the examples, `tag_ns` is the namespace the file declares with `add_namespace`.

## Basic triggered event

```
country_event = {
 id = tag_ns.N
 title = tag_ns.N.t
 desc = tag_ns.N.d
 picture = GFX_some_picture
 is_triggered_only = yes

 option = {
  name = tag_ns.N.a
  log = "[GetDateText]: [This.GetName]: tag_ns.N.a executed"
  set_temp_variable = { party_popularity_increase = -0.01 }
  change_relative_party_popularity = yes

  ai_chance = { base = 1 }
 }

 option = {
  name = tag_ns.N.b
  ai_chance = { base = 0 }
 }
}
```

Conditional descriptions use `text =`, not `desc =`, inside the block:

```
desc = {
 text = my_event.d_variant_a
 trigger = { has_global_flag = chose_option_a }
}
```

## Cost-aware AI weights

An option that charges the country (treasury, debt, a tax rate change, political power,
stability, or war support) needs an `ai_chance` that checks whether the country can pay.
Set the base to the sensible default, then add modifiers for affordability and for the
problem the cost solves:

```
 option = {
  name = tag_ns.N.a
  log = "[GetDateText]: [This.GetName]: tag_ns.N.a executed"
  set_temp_variable = { treasury_change = -15 }
  modify_treasury_effect = yes
  ai_chance = {
   base = 10
   modifier = { factor = 0.25 has_active_mission = bankruptcy_incoming_collapse }
   modifier = { factor = 0.5 ai_has_high_deficit = yes }
   modifier = { factor = 3 check_variable = { TAG_department_tier < 3 } }
  }
 }

 option = {
  name = tag_ns.N.b
  log = "[GetDateText]: [This.GetName]: tag_ns.N.b executed"
  add_political_power = -50
  ai_chance = {
   base = 5
   modifier = { factor = 0.25 has_active_mission = bankruptcy_incoming_collapse }
  }
 }

 option = {
  name = tag_ns.N.c
  log = "[GetDateText]: [This.GetName]: tag_ns.N.c executed"
  add_stability = -0.02
  ai_chance = {
   base = 1
   modifier = { factor = 0 has_stability < 0.3 }
  }
 }
```

- Treasury and debt: `has_active_mission = bankruptcy_incoming_collapse` and `ai_has_high_deficit = yes`. A charge built with math needs them as much as a literal one, and so does a scripted effect that charges internally (`one_office_construction`, `small_expenditure`).
- Tax rate: a change in either direction counts. A cut gives up income, so use the treasury triggers. For a raise, check the rate itself (`check_variable = { corporate_tax_rate > N }`) so the AI does not stack raises.
- Political power: `has_active_mission = bankruptcy_incoming_collapse`, the same check as treasury. Political power can go negative, so do not check the balance and do not hide the option behind a `trigger`. An option that already has the bankruptcy modifier for a treasury cost does not need a second one.
- Stability and war support: `has_stability < N` and `has_war_support < N`. The "decline" option needs one too when declining is what costs stability.
- Country paths: weigh choices by the `TAG_ai_behavior` path triggers first. Use the sitting government only under No Path, or where the check mirrors a focus `available` gate.
- Give every event at least one option that stays above zero when the country is broke. Decisions that charge the treasury need the same checks in `ai_will_do`.
- A cost audit changes AI weights only. Ask before adding an option `trigger` to enforce a cost (`has_political_power`, `has_equipment`) or converting hand-typed costs to presets such as `small_expenditure`.

The German BfV events in `events/Germany.txt` are the reference.
`validate_events.py --check-ai-chance-costs` lists options that still need this.

## Cross-country events

When an event fires to a different country than the one that started it, weigh the
options by the receiver's situation (opinion, influence, ideology), never by base
alone. `SNDR` is the sender:

```
 option = { # reject
  name = tag_ns.N.a
  log = "[GetDateText]: [This.GetName]: tag_ns.N.a executed"
  SNDR = { country_event = { id = tag_ns.M days = 1 } }
  ai_chance = {
   base = 15
   modifier = {
    factor = 0
    sender_influence_higher_30 = yes
   }
   modifier = {
    add = 10
    has_opinion = { target = SNDR value < -15 }
   }
  }
 }
```

Wrap follow-up fires to other countries in `hidden_effect` so chain consequences stay
out of the option's tooltip:

```
 hidden_effect = {
  OTHER = { country_event = { id = my_event.2 days = 1 } }
  news_event = { id = my_news.1 days = 1 }
 }
```

When a focus reward or option fires an event to another country, show the outcome:

```
OTHER = { country_event = { id = tag_ns.N days = 1 } }
custom_effect_tooltip = TT_IF_THEY_ACCEPT
effect_tooltip = { custom_effect_tooltip = TAG_deal_signed_tt }
custom_effect_tooltip = TT_IF_THEY_REJECT
effect_tooltip = { custom_effect_tooltip = TAG_sanctions_response_tt }
```

- Add `TT_IF_THEY_REJECT` only when rejection has real sender-side consequences. Never
  write an empty reject block.
- Inside the target's options use `TT_IF_WE_ACCEPT` and `TT_IF_WE_DECLINE`.
- The keys are in `localisation/english/MD_tooltips_l_english.yml`.

## Historical events

Date-based events fire from `common/scripted_effects/00_yearly_effects.txt`:

```
MD_event_on_startup_events = {
 CAM = { country_event = { id = Cameroon.1 days = 50 random_days = 50 } }
}

trigger_year_2067_events = {
 USA = { country_event = { id = collapse_event.1 days = 30 random_days = 336 } }
}
```

- An event whose `trigger` carries a `date > YYYY.M.D` lower bound must have an entry
  here. The guard only blocks an early fire. A chain event fired by a scheduled parent
  needs no entry.
- When the intended recipient may no longer own the target state, check the expected
  owner and fall back to `random_country = { limit = { owns_state = X } }`.

## News events

News events use `news_event` with `major = yes` and their own namespace. Use option
`trigger` blocks to give different text to the involved parties, neighbors, and everyone
else. Every country must match exactly one option:

```
news_event = {
 id = my_news.1
 title = my_news.1.t
 desc = my_news.1.d
 picture = GFX_some_picture
 major = yes
 is_triggered_only = yes

 option = {
  name = my_news.1.a
  trigger = { original_tag = TAG }
 }
 option = {
  name = my_news.1.b
  trigger = { NOT = { original_tag = TAG } }
 }
}
```

Each event window draws its picture at native size. News art is wide (about 397x153)
and country art is nearly square (about 217x163). Sprite names do not tell them apart,
so check the texture before reusing a picture across the two types. A `hidden = yes`
event takes no picture. `GFX_placeholder_events`, `GFX_placeholder_news`, and
`GFX_news_md4` are drafting stand-ins.

## `random_events` dispatch

```
random_events = {
    2500 = 0          # weight of "no event fires"
    100 = brotherhood.6
    100 = brotherhood.7
}
```

- One roll runs each time the parent on_action fires. A candidate's chance is its
  weight over the sum of weights.
- The selected event still checks its own `trigger`. If it fails, nothing fires and the
  roll does not retry.
- `mean_time_to_happen` modifiers that match the rolled scope multiply the candidate's
  weight. Keep them for per-country pacing.
- Prefer `random_events` over a hand-rolled `random_list` in an on_action effect for
  systems that fire across many countries.

## Batched notification events

When many sources deliver the same kind of thing to one country, accumulate into
per-category variables at the delivery site and fire one report. Worked example:
`UKR_queue_nato_aid_report` and `ukraine_nato_help.1`.

- Never put the payload in the report. Grant the money or equipment at the delivery
  site. A report lost to annexation or a tag change would lose the payload with it.
- Time the "report pending" flag:
  `set_country_flag = { flag = X_report_pending days = N+1 value = 1 }` for an event
  fired at `days = N`. An untimed flag wedges the system the first time an event drops.
- Skip the event for AI owners and clear the accumulators.
- Use `minor_flavor = yes` on the report.

## Reuse effect tooltips

`effect_tooltip = { <the real effect> }` renders the engine's own tooltip without
running the effect. Prefer it over a new `custom_effect_tooltip` key:

```
effect_tooltip = { add_equipment_to_stockpile = { type = infantry_weapons_type amount = UKR_aid_report_infantry } }
```

`amount` accepts a variable. A `hidden_effect` setter is not visible to a following
`effect_tooltip`, so set a temp the tooltip reads at effect level, or write a loc key
that reads the persistent variable.

## Common scripted effects

```
set_temp_variable = { treasury_change = -10.00 }
modify_treasury_effect = yes

small_expenditure = yes    # medium_expenditure, large_expenditure

set_temp_variable = { debt_change = 0.1 }
modify_debt_effect = yes

set_temp_variable = { temp_productivity_change = 0.025 }
flat_productivity_change_effect = yes
```
