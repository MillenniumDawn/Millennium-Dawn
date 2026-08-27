# Dynamic Modifiers Guide

**Author(s):** BirdyBoi & BlackSyX
**Mentor:** BirdyBoi & Luigi IV (aka MD's Fijian Nationalist)

---

This guide covers how to create and use country dynamic modifiers. A dynamic modifier ties in-game modifier fields (e.g. `industrial_capacity_factory`, `army_org_factor`) to named variables so that focus trees, decisions, and events can adjust them at runtime.

**© Millennium Dawn 2016-2026**

## File Naming

| Prefix | Usage                                         |
| ------ | --------------------------------------------- |
| `05_`  | Country-specific dynamic modifiers            |
| `09_`  | Country-specific dynamic modifiers (overflow) |
| `00_`  | System/shared dynamic modifiers               |

## How to Add a New Dynamic Modifier

### Step 1: Define the Modifier

Create or edit the appropriate file in `common/dynamic_modifiers/`.

```
TAG_modifier_name = {
	icon = GFX_idea_TAG_modifier_icon

	production_speed_buildings_factor = tag_construction_speed
	industrial_capacity_factory = tag_industrial_output
}
```

Each line maps a game modifier field to a variable name. The variable defaults to 0 and can be changed via `add_to_variable` in focus trees, decisions, or events.

#### When to Write an `enable` Block

Don't, in most cases. `enable` is optional and absent means "always on", which is what the majority of MD's dynamic modifiers want. It is also re-evaluated at runtime rather than once at load, so every trigger inside it is a recurring cost on every country holding the modifier.

Two shapes are always wrong:

- `enable = { always = yes }`. That is the default. Delete it.
- `enable = { original_tag = TAG }`. `add_dynamic_modifier` already picked who gets the modifier, so gating on the same country restates the call site. Worse, `tag = TAG` (rather than `original_tag`) goes false for a civil-war split-off and silently switches the modifier off for them.

Both are flagged by `validate_modifiers.py` (`redundant-enable-gate`).

Write one only when the condition can go false **while the modifier stays attached**. The internal factions system is the worked example: `initialize_internal_faction_dynamic_modifiers` (`common/scripted_effects/00_internal_faction_effects.txt`) attaches a faction's modifier when the country has the faction idea, but nothing ever calls `remove_dynamic_modifier` for it, and focuses do remove those ideas. `enable = { has_idea = the_military }` is the only thing that turns a lost faction's modifier off. `country_exists = ISR` on the Israeli settlement modifiers is the same pattern: state-attached modifiers that have to stop applying if Israel is annexed.

The alternative is to pair every `add_dynamic_modifier` with a `remove_dynamic_modifier`, which is cheaper at runtime but easier to forget.

#### Attach Scope Decides Everything

A dynamic modifier can be attached to a country **or** to a state, and that choice governs two things that fail silently when they are wrong:

1. **Variables resolve in the attach scope.** A state-attached modifier looks up a bare variable name on the *state*; a country-attached one looks it up on the *country*. To read a country variable from a state-attached modifier, prefix it with the tag: `local_building_slots_factor = SPR.SPR_canaries_local^0` (`99_SPR_dynamic_modifiers.txt:19`). Otherwise write the variable inside the state block that owns the modifier (`common/decisions/05_GRE_decisions.txt:1173`).
2. **Country-category modifier fields do nothing on a state-attached modifier.** Check the field's category in `common/modifier_definitions/` or `resources/documentation/modifiers_documentation.md`. When a region needs both kinds, split it into a state modifier and a country twin, as `GRE_archipelagos_defense_plan` / `GRE_archipelagos_defense_plan_country` do (`99_GRE_dynamic_modifiers.txt:109-129`).

### Step 2: Attach the Modifier to a Country

Edit the country history file in `history/countries/`:

```
530 = { add_dynamic_modifier = { modifier = TAG_modifier_name } }
```

### Step 3: Register the GFX

Add entries in both:

- `interface/MD_ideas.gfx`
- `interface/MD_dynamic_modifiers.gfx`

```
spriteType = {
	name = "GFX_idea_TAG_modifier_icon"
	texturefile = "gfx/interface/state_modifiers/TAG_modifier_icon.dds"
}
```

### Step 4: Create the Icon

Create the icon in `gfx/interface/state_modifiers/`.

**Icon Guidelines:**

1. Follow Millennium Dawn visual standards (see Discord "graphics-sound" channel)
2. Use the template pinned in Discord "graphics-sound"
3. Submit for review in "gfx_request" to ensure visual consistency

### Step 5: Add Localisation

Add name and description keys in the appropriate `localisation/english/MD_focus_TAG_l_english.yml`.

## Standardized Tooltip Pattern

When a focus (or decision/event) modifies dynamic modifier variables, use the **standardized tooltip pattern** so the player sees a consistent "Modifies Dynamic Modifier" header followed by per-variable change descriptions.

### Old Pattern (Do NOT Use)

```
completion_reward = {
	log = "[GetDateText]: [Root.GetName]: Focus TAG_focus_name"
	add_to_variable = { tag_construction_speed = 0.10 }
	add_to_variable = { tag_industrial_output = 0.05 }
	custom_effect_tooltip = construction_speed10_tooltip
	custom_effect_tooltip = factory_output5_tooltip
}
```

This required a separate localisation key for every variable-value combination, leading to dozens of redundant keys per country.

### New Pattern (Standard)

```
completion_reward = {
	log = "[GetDateText]: [Root.GetName]: Focus TAG_focus_name"
	custom_effect_tooltip = { localization_key = modifies_dynamic_modifier_tt MODIFIER = TAG_modifier_name }
	add_to_variable = { tag_construction_speed = 0.10 tooltip = production_speed_buildings_factor_tt }
	add_to_variable = { tag_industrial_output = 0.05 tooltip = industrial_capacity_factory_tt }
}
```

**Key differences:**

1. A single `custom_effect_tooltip = { localization_key = modifies_dynamic_modifier_tt MODIFIER = TAG_modifier_name }` header replaces all per-variable tooltip lines
2. Each `add_to_variable` gets a `tooltip = <field>_tt` that references the standardized tooltip key for that modifier field
3. No per-country localisation keys needed for tooltips

### How to Find the Right Tooltip Key

The tooltip key follows the pattern `<modifier_field_name>_tt`, where `<modifier_field_name>` is the left-hand side of the dynamic modifier definition.

For example, if your dynamic modifier has:

```
production_speed_buildings_factor = tag_construction_speed
```

Then the tooltip key is `production_speed_buildings_factor_tt`.

All available `_tt` keys are defined in `localisation/english/MD_dm_modifiers_l_english.yml`. Always verify the key exists in that file before using it.

---

Happy Coding!
