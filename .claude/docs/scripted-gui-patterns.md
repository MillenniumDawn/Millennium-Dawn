# Scripted GUI Patterns

Recurring shapes for data-driven scripted GUIs. Reference implementations: the MIO
unlock catalog (`common/scripted_guis/00_mio_unlock_catalog.txt`) and the EU GUIs
(`common/scripted_guis/01_european_union_guis.txt`). Engine mechanics are in
[scripted-gui-rules.md](scripted-gui-rules.md).

## Data-driven entries with `dynamic_lists`

For N similar entries, use one entry container and a `gridboxType` driven by an array.
Hidden entries are simply absent from the array.

```
# GUI
gridboxType = {
    name = "mio_catalog_grid"
    position = { x = @entryx y = 5 }
    size = { width = @entryw height = 100%% }
    slotsize = { width = @entryw height = 100 }
    format = "UPPER_LEFT"
    max_slots_horizontal = 1
}

containerWindowType = {
    name = "mio_catalog_entry_container"
}

# Scripted GUI
dynamic_lists = {
    mio_catalog_grid = {
        array = mio_catalog_visible_array
        entry_container = "mio_catalog_entry_container"
    }
}
```

- `gridboxType` needs a double `%` for percentage sizes.
- The backing array holds integer entry ids, not tokens. Inside triggers, effects,
  properties, and scripted loc, `v` is the current entry's value.
- Ids are 1-based and arrays are 0-based. A parallel token array reserves an unused
  index 0 so `array^v` lines up.
- The scripted GUI writes one set of `_click_enabled`, `_visible`, and `_click` blocks.
  The engine evaluates them once per entry.

## Per-entry display with scripted loc

Per-entry names, icons, and tooltips live in `defined_text` blocks keyed on `v`:

```
defined_text = {
    name = mio_catalog_entry_name
    text = { trigger = { check_variable = { v = 1 } }   localization_key = GENERIC_krepost_state_defense_bureau_name }
    text = { trigger = { check_variable = { v = 2 } }   localization_key = GENERIC_north_plains_heavy_industries_name }
}
```

```
instantTextboxType = {
    name = "name"
    text = "[mio_catalog_entry_name]"
}
```

- `text`, `buttonText`, `pdx_tooltip`, and `image` (in a `properties` block) accept a
  `"[scripted_loc]"` value.
- For `pdx_tooltip_delayed`, call the scripted loc directly. Wrapping it in a static
  loc key can drop the `v` scope.
- A dispatcher only branches and returns a static key. A `[!trigger_name]` inside the
  returned value does not re-evaluate. Put `[!]` in the same flat loc value as the
  scripted-loc call. For runtime string construction see
  [meta-effect-patterns.md](meta-effect-patterns.md).

## Lists over an array of scopes

A dispatcher on `v` scales in one dimension. For an entity by category matrix, or an
entity set that grows with content, render from data: a gridbox over an array of scope
objects with `change_scope = yes`, reading generic getters and per-scope variables.

```
# Rebuild the array for the selected category
EU_select_party_members = {
    clear_array = global.EU_MEP_members_current
    set_temp_variable = { sel_party = global.EU_selected_party }
    for_each_scope_loop = {
        array = global.EU_member
        meta_effect = {
            text = {
                if = {
                    limit = { check_variable = { THIS.MEP_party_[sp] > 0 } }
                    set_variable = { THIS.MEP_party_selected_display = THIS.MEP_party_[sp] }
                    add_to_array = { global.EU_MEP_members_current = THIS }
                }
            }
            sp = "[?sel_party]"
        }
    }
}

dynamic_lists = {
    eu_party_members_list = {
        array = global.EU_MEP_members_current
        entry_container = "eu_party_member_detail"
        change_scope = yes
    }
}

instantTextBoxType = { name = "..._tag"   text = "[?THIS.GetNameWithFlag]" }
instantTextBoxType = { name = "..._seats" text = "[?THIS.MEP_party_selected_display]" }
```

- Adding one more entity should need no localisation or GUI edits. If it does, the
  display is still enumerated.
- A gridbox cannot live in a tooltip. Move the data into a window or side panel first.

## Dirty variable

A GUI with `dirty = global.X` refreshes only when X changes. Standard shape:

```
update_<system>_dirty_variable = {
    if = { limit = { check_variable = { global.<system>_dirty_update_var < 10000 } }
        add_to_variable = { global.<system>_dirty_update_var = 1 }
    }
    else = {
        set_variable = { global.<system>_dirty_update_var = 1 }
    }
}
```

- The `else` branch rolls over before overflow. Pick a threshold well above the
  realistic action count.
- Name the variable `global.<system>_dirty_update_var` or `global.<system>_ui_dirty_var`.
  Use one per system.
- Call it at the end of every click handler and state-changing effect, including the
  close and toggle-off paths. The `is_ai = no` guard rule is in `scripted-gui-rules.md`.
- References: `update_ledger_dirty_var`, `update_nato_dirty_variable`,
  `update_mio_catalog_dirty_variable`.

## Filter checkbox

`GFX_generic_checkbox` is a single-frame sprite, so the `_frame` trigger pattern fails
on it. Swap two sprites through a scripted loc and the `properties` block:

```
defined_text = {
    name = mio_catalog_filter_toggle_icon
    text = {
        trigger = { has_country_flag = mio_catalog_filter_available }
        localization_key = GFX_generic_checkbox_checked
    }
    text = {
        localization_key = GFX_generic_checkbox_open
    }
}

properties = {
    mio_catalog_filter_toggle_btn = {
        image = "[mio_catalog_filter_toggle_icon]"
    }
}

buttonType = {
    name = "mio_catalog_filter_toggle_btn"
    spriteType = "GFX_generic_checkbox_open"
    clicksound = click_checkbox
}
```

## Per-entry requirement tooltips

`[!trigger]` renders each subcondition with a pass or fail icon. To make it per entry,
put `[!]` on a static outer trigger that forwards through `meta_trigger`:

```yaml
MIO_CAT_UNLOCK_BTN_REQUIREMENTS_TT: "[!mio_catalog_entry_prereqs_yes]"
```

```
mio_catalog_entry_prereqs_yes = {
    meta_trigger = {
        text = { [TRIG] = yes }
        TRIG = "[?global.mio_catalog_all_tokens^v.GetTokenKey]_unlock_btn_enabled"
    }
}
```

## Visibility

`visible` on the scripted GUI's `window_name` works. `_visible` on a nested
`containerWindowType` inside a scrollable parent silently fails. Filter the backing
array instead. `_visible` on individual buttons, icons, and text boxes inside an entry
works.

## Persistent state

- Flags and `set_variable` values persist in the save.
- Seed master arrays once in `setup_global_arrays`
  (`common/scripted_effects/00_startup_effects.txt`).
- Rebuild per-country derived arrays on demand from the scripted GUI's `effects`. Do not
  store them in the save.
- The AI never clicks, so call the rebuild effect inside `every_country` at the end of
  `setup_global_arrays` when the AI needs the array.
