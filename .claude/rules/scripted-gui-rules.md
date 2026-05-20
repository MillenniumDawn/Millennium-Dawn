# Scripted GUI Rules

Scripted GUIs are defined in `common/scripted_guis/*.txt` and assign scripted functionality to UI elements defined in `interface/*.gui` files.

## File Naming

| Prefix | Usage                                     |
| ------ | ----------------------------------------- |
| `00_`  | Core system GUIs (money, resources, etc.) |
| `01_`  | Shared/global feature GUIs                |
| `02_`  | Secondary shared feature GUIs             |
| `99_`  | Country-specific GUIs (`99_TAG_...`)      |

## Structure

Every scripted GUI lives inside a `scripted_gui = { ... }` container block:

```
scripted_gui = {
	my_gui_name = {
		context_type = player_context
		window_name = "my_gui_window"

		visible = { }
		effects = { }
		triggers = { }
		properties = { }
		dynamic_lists = { }
		ai_enabled = { }
	}
}
```

## Required Properties

1. **`context_type`** — determines scope and available data (see Context Types below)
2. **`window_name`** — must reference an independent `containerWindowType` name in an `interface/*.gui` file

## Context Types

| Type                       | Default Scope     | ROOT           | Notes                                                                                  |
| -------------------------- | ----------------- | -------------- | -------------------------------------------------------------------------------------- |
| `player_context`           | Player country    | Player country | Baseline context; use for most GUIs                                                    |
| `selected_country_context` | Selected country  | Player country | GUI only appears when a country is selected; AI evaluates for every other country      |
| `selected_state_context`   | Selected state    | Player country | GUI only appears when a state is selected; AI evaluates for every state                |
| `decision_category`        | Player country    | Player country | Embeds in a decision category via `scripted_gui` attribute; no parent window needed    |
| `diplomatic_action`        | Player country    | Player country | Attached via `send_scripted_gui`/`receive_scripted_gui` in scripted diplomatic actions |
| `national_focus_context`   | Target country    | Player country | Attached to the national focus view for the targeted country                           |
| `country_mapicon`          | Displayed country | Player country | Shows next to every country on the world map                                           |
| `state_mapicon`            | Displayed state   | Player country | Shows next to every state on the world map                                             |

**Note:** `diplomatic_action` context logs harmless parse errors (`Unexpected token: context_type`) during load. This is a known engine quirk — the GUIs work correctly at runtime when invoked through `scripted_diplomatic_actions`.

## Parent Window

- `parent_window_token` — attach to a base game window (e.g., `top_bar`, `decision_tab`, `politics_tab`)
- `parent_window_name` — attach to a named container; use `_instance` suffix for nested containers
- `decision_category` context GUIs should **not** have a parent window
- `diplomatic_action` context GUIs should **not** have a parent window

## Effects Block

Map button element names to click effects:

```
effects = {
	my_button_click = { <effects> }
	my_button_right_click = { <effects> }
	my_button_shift_click = { <effects> }
}
```

Click modifiers can be chained: `my_button_alt_right_click`, `my_button_control_shift_click`, etc.

## Triggers Block

Control element visibility and clickability:

```
triggers = {
	my_button_click_enabled = { <triggers> }
	my_button_visible = { <triggers> }
	my_icon_visible = { <triggers> }
}
```

- `_click_enabled` — when the element is clickable (greyed out otherwise)
- `_visible` — when the element is visible (hidden elements are also unclickable by AI)
- `_click_enabled` overrides modifier-specific variants like `_right_click_enabled`
- Temporary variables set inside trigger blocks can be used in `properties` and `dynamic_lists`

## Properties Block

Manipulate element textures, frames, and positions:

```
properties = {
	my_icon = {
		image = "[get_my_icon_texture]"    # supports scripted localisation
		frame = my_variable                 # variable-driven frame
		x = my_x_var                        # variable-driven position
		y = my_y_var
	}
}
```

## Dynamic Lists

Used with `gridBoxType` elements to draw one entry per array index:

```
dynamic_lists = {
	my_gridbox = {
		array = my_array           # draws one GUI per index
		value = v                  # optional, default = v
		index = i                  # optional, default = i
		change_scope = no          # if yes, scopes to the array value
		entry_container = "my_entry_container"
	}
}
```

The `entry_container` must be a separate `containerWindowType` defined in the GUI file.

## Dirty Variable (Performance)

For large GUIs, use a dirty variable to avoid per-tick updates:

```
dirty = my_update_variable
```

The GUI only refreshes when this variable's value changes. This does **not** affect visibility checks.

**Only bump the dirty variable from player-initiated paths.** A shared GUI's dirty variable refreshes any open instance — AI-side state changes that bump it wake every player's open GUI for no visible benefit. Guard the bump with `is_ai = no`:

```
# Wrong — AI changes wake every player's open GUI
my_effect = {
    add_to_variable = { global.my_dirty = 1 }
    # ...actual logic...
}

# Right — player paths only
my_effect = {
    if = {
        limit = { ROOT = { is_ai = no } }
        add_to_variable = { global.my_dirty = 1 }
    }
    # ...actual logic...
}
```

This matters most for any GUI the AI also interacts with — peace deal builders, investment dialogs, scripted-effect-driven menus.

## AI Configuration

```
ai_enabled = { <triggers> }          # checked once at init; failures never rechecked
ai_test_interval = 24                # hours between checks (default: 24)
ai_test_variance = 0.2               # variance as decimal (default: 0.2)

ai_test_scopes = test_enemy_countries   # limits which scopes AI evaluates
ai_test_scopes = test_ally_countries    # can specify multiple

ai_check = { <triggers> }            # checked each interval tick; false = skip
ai_check_scope = { <triggers> }      # filters scoped targets

ai_max_weight_taken_per_test = 1     # max actions per tick (default: 1)

ai_weights = {
	my_button_click = {
		ai_will_do = {
			base = 1
			modifier = {
				factor = 0
				<triggers>
			}
		}
	}
}
```

### AI Test Scopes

For `selected_country_context`:
`test_self_country`, `test_enemy_countries`, `test_ally_countries`, `test_neighbouring_countries`, `test_neighbouring_ally_countries`, `test_neighbouring_enemy_countries`

For `selected_state_context`:
`test_self_owned_states`, `test_enemy_owned_states`, `test_ally_owned_states`, `test_self_controlled_states`, `test_enemy_controlled_states`, `test_ally_controlled_states`, `test_neighbouring_states`, `test_neighbouring_enemy_states`, `test_neighbouring_ally_states`, `test_our_neighbouring_states`, `test_our_neighbouring_states_against_allies`, `test_our_neighbouring_states_against_enemies`, `test_contesded_states`

Additional filters: `test_if_only_major`, `test_if_only_coastal`

- Use `ai_enabled = { always = no }` to disable AI entirely for decorative/player-only GUIs
- Always specify `ai_test_scopes` to avoid AI checking every country/state (performance)

## Best Practices

- Always set `context_type` — without it, the GUI cannot read or modify game state
- Use `dirty` variables on large/complex GUIs to reduce per-tick overhead
- Event targets **cannot** be used in scripted GUIs (breaks everything) — use variable scopes instead
- Use scripted effects and triggers to separate GUI logic from gameplay logic
- Keep the `window_name` container fully independent (not nested in another container)
- For `decision_category` context, attach via the `scripted_gui = GUI_NAME` attribute in the decision category definition
- For `diplomatic_action` context, attach via `send_scripted_gui` / `receive_scripted_gui` in the scripted diplomatic action

## Example

```
scripted_gui = {
	my_feature_gui = {
		context_type = player_context
		window_name = "my_feature_window"
		parent_window_token = decision_tab

		dirty = my_feature_dirty_var

		visible = {
			has_country_flag = my_feature_enabled
		}

		dynamic_lists = {
			my_list_gridbox = {
				array = my_data_array
				change_scope = yes
				entry_container = "my_list_entry"
			}
		}

		effects = {
			my_action_button_click = {
				log = "[GetDateText]: [Root.GetName]: my_feature_gui action clicked"
				my_scripted_effect = yes
			}
		}

		triggers = {
			my_action_button_click_enabled = {
				my_scripted_trigger = yes
			}
			my_info_icon_visible = {
				check_variable = { my_var > 0 }
			}
		}

		properties = {
			my_status_icon = {
				image = "[get_my_status_texture]"
			}
		}

		ai_enabled = { always = no }
	}
}
```
