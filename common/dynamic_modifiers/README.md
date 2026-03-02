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
	enable = { always = yes }

	icon = GFX_idea_TAG_modifier_icon

	production_speed_buildings_factor = tag_construction_speed
	industrial_capacity_factory = tag_industrial_output
}
```

Each line maps a game modifier field to a variable name. The variable defaults to 0 and can be changed via `add_to_variable` in focus trees, decisions, or events.

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
