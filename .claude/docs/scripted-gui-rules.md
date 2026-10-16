# Scripted GUI Rules

Scripted GUIs in `common/scripted_guis/*.txt` attach script to UI elements defined in
`interface/*.gui`. Recipes are in [scripted-gui-patterns.md](scripted-gui-patterns.md).

File prefixes: `00_` core systems, `01_` and `02_` shared features, `99_TAG_` country
GUIs.

## Structure

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

- `context_type` and `window_name` are required. `window_name` names an independent
  `containerWindowType`, not one nested in another container.
- Omit `visible` instead of writing `visible = { always = yes }`. A `decision_category`
  GUI is already gated by its category.
- Event targets cannot be used in scripted GUIs. Use variable scopes.
- Keep gameplay logic in scripted effects and triggers.

## Context types

ROOT is the player country in every context.

| Context                    | Default scope     | Notes                                        |
| -------------------------- | ----------------- | -------------------------------------------- |
| `player_context`           | Player country    | Use for most GUIs                            |
| `selected_country_context` | Selected country  | AI evaluates for every other country         |
| `selected_state_context`   | Selected state    | AI evaluates for every state                 |
| `decision_category`        | Player country    | Attached with `scripted_gui` on the category |
| `diplomatic_action`        | Player country    | Attached with `send_scripted_gui`            |
| `national_focus_context`   | Target country    | Attached to the focus view                   |
| `country_mapicon`          | Displayed country | Shown beside every country on the map        |
| `state_mapicon`            | Displayed state   | Shown beside every state on the map          |

- `diplomatic_action` logs a harmless `Unexpected token: context_type` at load.
- `parent_window_token` attaches to a base game window (`top_bar`, `decision_tab`,
  `politics_tab`). `parent_window_name` attaches to a named container. Use the
  `_instance` suffix for nested containers.
- `decision_category` and `diplomatic_action` GUIs take no parent window.

## Blocks

- `effects`: `<element>_click`, `_right_click`, `_shift_click`. Modifiers chain, as in
  `_alt_right_click`.
- `triggers`: `<element>_click_enabled` and `<element>_visible`. `_click_enabled`
  overrides modifier-specific variants. Temp variables set in a trigger block are
  usable in `properties` and `dynamic_lists`.
- `properties`: per element `image` (accepts scripted loc), `frame`, `x`, and `y`, each
  variable-driven.
- `dynamic_lists`: one entry per array index for a `gridBoxType`. Keys: `array`,
  `value` (default `v`), `index` (default `i`), `change_scope`, `entry_container`. The
  entry container is a separate `containerWindowType`.

## Dirty variable

`dirty = my_update_variable` makes the GUI refresh only when the variable changes. It
does not affect visibility checks.

- Never bind `dirty` to `global.date` or `global.num_days`. `validate_scripted_gui.py`
  reports it as `DIRTY_TIMER_GLOBAL`.
- Bump the variable only from player-initiated paths. A shared GUI's dirty variable
  refreshes every open instance, so an AI-side bump wakes every player's GUI for
  nothing:

```
my_effect = {
    if = { limit = { ROOT = { is_ai = no } } add_to_variable = { global.my_dirty = 1 } }
}
```

- The shared `update_*_dirty_variable` effects carry no guard, since they run only from
  player click paths. When an effect can also run from an AI on_action, guard the call
  site.

## AI

```
ai_enabled = { <triggers> }          # Checked once at init, never rechecked
ai_test_interval = 24                # Hours between checks
ai_test_variance = 0.2

ai_test_scopes = test_enemy_countries   # May be repeated

ai_check = { <triggers> }            # Checked each interval
ai_check_scope = { <triggers> }      # Filters scoped targets

ai_max_weight_taken_per_test = 1

ai_weights = {
 my_button_click = {
  ai_will_do = {
   base = 1
   modifier = { factor = 0 <triggers> }
  }
 }
}
```

- Use `ai_enabled = { always = no }` for player-only GUIs.
- Always set `ai_test_scopes` on selected-country and selected-state GUIs, so the AI
  does not check every country or state.
- Country scopes: `test_self_country`, `test_enemy_countries`, `test_ally_countries`,
  `test_neighbouring_countries`, `test_neighbouring_ally_countries`,
  `test_neighbouring_enemy_countries`.
- State scopes: `test_self_owned_states`, `test_enemy_owned_states`,
  `test_ally_owned_states`, `test_self_controlled_states`,
  `test_enemy_controlled_states`, `test_ally_controlled_states`,
  `test_neighbouring_states`, `test_neighbouring_enemy_states`,
  `test_neighbouring_ally_states`, `test_our_neighbouring_states`,
  `test_our_neighbouring_states_against_allies`,
  `test_our_neighbouring_states_against_enemies`, `test_contesded_states`.
- Filters: `test_if_only_major`, `test_if_only_coastal`.
