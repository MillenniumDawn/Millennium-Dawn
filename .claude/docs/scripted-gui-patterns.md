# Scripted GUI Patterns

Recurring patterns for data-driven scripted GUIs in Millennium Dawn. The MIO Unlock Catalog (`common/scripted_guis/00_mio_unlock_catalog.txt`) and the EU council (`common/scripted_guis/01_european_union_guis.txt`) are the reference implementations.

For raw scripted*gui mechanics (context types, parent windows, AI checks), see [`/.claude/rules/scripted-gui-rules.md`](../rules/scripted-gui-rules.md). This doc is about the recurring \_shapes* you build on top of those primitives.

---

## Data-driven entries via `dynamic_lists`

When a catalog/list has N similar entries (votes, MIO unlocks, member states), replace N hardcoded `containerWindowType` blocks with one `entry_container` template + a `gridboxType` driven by `dynamic_lists`. Entries that should be hidden are simply absent from the backing array — no `_visible` games on nested containers (which silently fail anyway).

### Backing array

Holds integer entry IDs (1..N), not tokens. EU votes use the vote ID directly; MIO catalog uses 1..23 mapped to a parallel `global.mio_catalog_all_tokens` master array.

```
add_to_array = { mio_catalog_visible_array = 1 }
add_to_array = { mio_catalog_visible_array = 2 }
```

### GUI side

```
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
    # ...one entry's worth of buttonType / iconType / instantTextboxType
}
```

Note `100%%` — gridboxType requires double `%` for percentage sizes.

### Scripted_gui side

```
dynamic_lists = {
    mio_catalog_grid = {
        array = mio_catalog_visible_array
        entry_container = "mio_catalog_entry_container"
        # value = v, index = i, change_scope = no — all defaults
    }
}
```

`v` is the loop variable (default name; rarely worth renaming). Inside trigger / effect / property / scripted-loc evaluation, `v` holds the current entry's array value. EU votes use it as a vote ID; MIO uses it as a 1..23 entry index.

### Element-name reuse

Each entry container is instantiated N times, but the scripted_gui only writes one set of `_click_enabled` / `_visible` / `_click` blocks. The engine evaluates them once per entry, with `v` set to that entry's value. So `mio_cat_unlock_btn_click_enabled` runs 23 times per refresh (once per visible entry), each time with `v` set to that entry's ID.

---

## Per-entry display via scripted-localisation dispatchers

Per-entry data (name, icon, tooltip) lives in `defined_text` blocks keyed on `v`. The GUI references the dispatcher by name; the dispatcher returns the right loc key per entry.

```
defined_text = {
    name = mio_catalog_entry_name
    text = { trigger = { check_variable = { v = 1 } }   localization_key = GENERIC_krepost_state_defense_bureau_name }
    text = { trigger = { check_variable = { v = 2 } }   localization_key = GENERIC_north_plains_heavy_industries_name }
    # ...
}
```

Reference in the entry container:

```
instantTextboxType = {
    name = "name"
    text = "[mio_catalog_entry_name]"
}
```

### Where scripted-loc invocation works

| Attribute                                          | Works      | Notes                                                     |
| -------------------------------------------------- | ---------- | --------------------------------------------------------- |
| `text = "[scripted_loc]"`                          | yes        | `instantTextboxType.text`, also `buttonText`              |
| `pdx_tooltip = "[scripted_loc]"`                   | yes        | Precedent: `interface/eu.gui`                             |
| `pdx_tooltip_delayed = "[scripted_loc]"`           | use direct | Don't wrap through a static YAML key — `v` scope may drop |
| `image = "[scripted_loc]"` (in `properties` block) | yes        | Sprite name returned by scripted-loc                      |

### What scripted-loc dispatch can't do

- Return a loc key whose value contains `[!trigger_name]` and have the `[!]` re-evaluate. The engine substitutes the dispatched loc value as raw text. Put `[!]` directly in the same flat loc value as your scripted-loc call, not chained through a dispatcher.
- Compute or transform — only branch on `check_variable` (or other triggers) and return a static `localization_key`. For runtime string construction, use `meta_trigger`/`meta_effect` instead (see [`tokenization-patterns.md`](tokenization-patterns.md)).

### Dispatcher size economics

23 entries × 5 fields (name, trait, equip label, icon, desc) = 115 `defined_text` branches. Verbose, but every branch is one line; the alternative is 23 entry-container copies with 5 hardcoded fields each (~30 lines per copy = 690 lines). Net win once you have ~6+ entries.

---

## Dirty variable — MD standard

GUIs with `dirty = global.X` only refresh when X's value changes. Use this to avoid per-tick re-evaluation of expensive triggers / scripted-loc.

### Standard scripted-effect shape

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

The else branch rolls over before integer overflow. Threshold is typically 10000 (NATO, MIO catalog) or 1000000 (ledger). Pick something well above the realistic player-action count.

References:

- `common/scripted_effects/00_ledger_scripted_effects.txt:282` (`update_ledger_dirty_var`, 1M threshold)
- `common/scripted_effects/01_NATO_effects.txt:2` (`update_nato_dirty_variable`, 10K threshold)
- `common/scripted_effects/00_mio_scripted_effects.txt` (`update_mio_catalog_dirty_variable`, 10K)

### Variable naming convention

`global.<system>_dirty_update_var` (NATO, MIO) or `global.<system>_ui_dirty_var` (ledger). Either is acceptable — pick one for the system and use it everywhere.

### Call from every state-changing effect

Every click handler / state-toggling effect in the scripted*gui should end with `update*<system>\_dirty_variable = yes`. Including the close/toggle-off paths, not just the open path.

### Player-only guard

The [`scripted-gui-rules.md` dirty rule](../rules/scripted-gui-rules.md) says to guard bumps with `is_ai = no` for GUIs the AI also interacts with. In practice, MD's `update_*_dirty_variable` effects don't carry the guard — the dirty variable is only bumped from player-initiated click paths in the scripted_gui's `effects` block, and those paths are reached only when the player clicks. If your effect can be invoked from an AI on_action, wrap the call site (not the dirty effect itself) with `is_ai = no`.

---

## Filter checkbox — image swap, not frame swap

`GFX_generic_checkbox` is a single-frame sprite. The `_frame` trigger pattern silently fails on it (renders as nothing on the "checked" frame). Mirror the construction-UI pattern instead: two separate sprites swapped via a scripted-loc and the GUI's `properties` block.

```
# Scripted-loc
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

# Scripted_gui properties
properties = {
    mio_catalog_filter_toggle_btn = {
        image = "[mio_catalog_filter_toggle_icon]"
    }
}

# GUI buttonType — default sprite is the "off" state; properties overrides per-frame
buttonType = {
    name = "mio_catalog_filter_toggle_btn"
    spriteType = "GFX_generic_checkbox_open"
    clicksound = click_checkbox
}
```

Reference: `interface/MD_countryconstructionsview.gui:13-21` (`toggle_construction_building_speed`).

---

## Per-entry tooltip with dynamic per-MIO ✓/✗ icons

Standard `[!trigger]` rendering shows each subcondition with a green/red icon. To make it per-entry (different requirements per MIO/vote/etc), put `[!]` on a static-name outer trigger that uses `meta_trigger` to forward into the per-entity check.

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

See [`tokenization-patterns.md`](tokenization-patterns.md) for the meta_trigger mechanics and why this is the only way to keep `[!]` rendering working with per-entry dispatch.

---

## Visibility rule of thumb

`visible` on the scripted_gui's `window_name` works fine. `_visible` triggers on **nested** `containerWindowType` elements (entries inside a scrollable parent) silently fail to hide them — there is no working precedent in MD. Always use array filtering instead: rebuild the visible array to exclude the entries that shouldn't show. Hiding individual button/icon/textbox elements within a rendered entry **does** work via `_visible`; only the wrapping containerWindowType is the broken case.

---

## State that needs to persist across saves

`set_country_flag` and `set_global_flag` persist with the save. Variables persist if they're `set_variable` (not `set_temp_variable`). Master arrays seeded once at game start — put them in `setup_global_arrays` (`common/scripted_effects/00_startup_effects.txt`) so the master is populated for every save without lazy-seeding logic. Per-country derived arrays should be rebuilt on demand via the scripted_gui's `effects`, not stored in the save (cheap to rebuild, expensive to bloat the save).

For initial AI population — call your `rebuild_*_yes` effect inside `every_country = { ... }` at the bottom of `setup_global_arrays` so every AI starts with the array populated. Without that, AI never triggers a click that would build it.
