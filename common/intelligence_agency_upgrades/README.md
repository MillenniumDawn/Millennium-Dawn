# Intelligence Agency Upgrades

This directory holds the intelligence agency upgrade definitions used by the vanilla "Intelligence Agency" UI and by the Millennium Dawn **auto-agency** queue system.

`_documentation.info` describes the vanilla `upgrade = { ... }` block syntax. This README covers the MD-specific wiring that every upgrade must have so it flows through the auto-agency queue, tooltips, and icons.

## Files involved

Adding or renaming an agency upgrade touches five files. All five must stay in sync or the upgrade will be invisible, unclickable, or show as a blank icon in the queue UI.

| File                                                                   | What it holds                                                                                |
| ---------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| `common/intelligence_agency_upgrades/intelligence_agency_upgrades.txt` | Source of truth — the `upgrade_X = { ... }` block with `picture`, `ai_will_do`, `level = {}` |
| `common/on_actions/MD_auto_agency_on_actions.txt`                      | Registry — assigns the upgrade to an index in four parallel global arrays                    |
| `localisation/english/MD_auto_agency_l_english.yml`                    | Loc triple — token id / display name / gfx sprite name                                       |
| `common/scripted_guis/00_MD_auto_agency_scripted_gui.txt`              | Prerequisite gating (only if the upgrade needs `has_done_agency_upgrade = ...` prereqs)      |
| `interface/countryintelligenceagencyview.gfx`                          | Sprite definition referenced by `picture =` and the `_gfx` loc key                           |

## Adding a new upgrade — step by step

Say you are adding `upgrade_deepfake_detection` as index **25** (the next free slot). The process is:

### 1. Define the upgrade

Add the block to `intelligence_agency_upgrades.txt` inside a branch:

```
upgrade_deepfake_detection = {
    picture = GFX_agency_cyber_security        # must exist in a .gfx file
    frame = GFX_upgrade_frame_intel
    sound = Spy_Agency_Intel_Upgrades_Confirm

    ai_will_do = { base = 3 ... }
    modifiers_during_progress = { hidden_modifier = { MD_auto_agency_in_progress_boolean = 1 } }
    available = { custom_trigger_tooltip = { tooltip = cannot_manually_upgrade_agency_tt MD_auto_agency_manual_upgrade_available = yes } }

    level = { modifier = { ... } complete_effect = { ... } }
    level = { modifier = { ... } complete_effect = { ... } }
}
```

The number of `level = { }` blocks is the upgrade's **max level**. Record that — you need it in step 2.

### 2. Register the upgrade in on_actions

Open `common/on_actions/MD_auto_agency_on_actions.txt`. Two things must happen:

- Bump the `size = N` on every `resize_array` from `25` to `26` (one per array):

  ```
  resize_array = { array = global.agency_upgrades     value = 0 size = 26 }
  resize_array = { array = global.agency_names        value = 0 size = 26 }
  resize_array = { array = global.agency_gfx          value = 0 size = 26 }
  resize_array = { array = global.agency_max_upgrades value = 1 size = 26 }
  ```

- Add four `set_variable` lines at the end (one per parallel array). Index, token, and suffix **must match exactly**:

  ```
  set_variable = { global.agency_upgrades^25     = token:MD_auto_agency_25_upgrade_deepfake_detection }
  set_variable = { global.agency_names^25        = token:MD_auto_agency_25_upgrade_deepfake_detection_name }
  set_variable = { global.agency_gfx^25          = token:MD_auto_agency_25_upgrade_deepfake_detection_gfx }
  set_variable = { global.agency_max_upgrades^25 = 2 }   # number of level = {} blocks
  ```

If your upgrade has only **one level**, the `agency_max_upgrades^N` line can be omitted — the `resize_array` pre-fills it with `1`.

### 3. Add localisation

Open `localisation/english/MD_auto_agency_l_english.yml` and add the three loc keys. The pattern is fixed — prefix `MD_auto_agency_NN_` where `NN` is the zero-padded index:

```
 MD_auto_agency_25_upgrade_deepfake_detection: "upgrade_deepfake_detection"
 MD_auto_agency_25_upgrade_deepfake_detection_name: "$upgrade_deepfake_detection$"
 MD_auto_agency_25_upgrade_deepfake_detection_gfx: "GFX_agency_cyber_security"
```

- The base key's value is the literal `upgrade_X` token (used as the game's upgrade id).
- `_name` must use the `$upgrade_X$` loc reference so it pulls the name the vanilla agency UI uses.
- `_gfx` must equal the exact `picture =` GFX sprite from step 1 — the validator enforces this so the auto-agency queue and the vanilla agency view show the same icon.

### 4. Add prerequisites (only if the upgrade has them)

If the upgrade has a `has_done_agency_upgrade = upgrade_X` prereq, add a corresponding `custom_trigger_tooltip` branch inside `agency_upgrade_icon_button_click_enabled` in `common/scripted_guis/00_MD_auto_agency_scripted_gui.txt`, keyed on the index's `i` value. See the existing blocks for `i = 19` (crypto_strength_2), `i = 21-23` (cyber ops), and `i = 24` (cyber elite) as templates.

Also add a matching `MD_auto_agency_prereq_X_tt` loc key describing the prereq text, and extend `MD_auto_agency_scripted_loc_prereqs` in `common/scripted_localisation/00_MD_auto_agency_scripted_localisation.txt` to dispatch on the index.

### 5. Ensure the sprite exists

Confirm `GFX_agency_cyber_security` (or whichever sprite you used) is defined in `interface/countryintelligenceagencyview.gfx` or another `.gfx` file. If you need a brand-new sprite, add a `spriteType = { name = "..." texturefile = "gfx/..." }` entry there first.

## Validation

Run the validator to confirm everything lines up:

```bash
python3 tools/validation/validate_agency_upgrades.py --path .
```

The validator covers seven checks:

1. **Registry coverage** — every `upgrade_X` defined in this directory is registered in all four parallel arrays, and every registry entry points to a real upgrade. Parallel arrays must use the same token at the same index (`_name` and `_gfx` suffixes enforced).
2. **max_upgrades vs level count** — `global.agency_max_upgrades^N` equals the number of `level = { }` blocks in the upgrade definition.
3. **Loc triples + GFX** — each index has `MD_auto_agency_NN_*` / `_name` / `_gfx` keys, the `_gfx` value matches the definition's `picture =` field, and both resolve to a real sprite.
4. **Array size / gaps** — every `resize_array size = N` literal matches the registered index count; no missing indices between 0 and max.
5. **scripted_gui prereqs** — `has_done_agency_upgrade = X` references in the queue GUI resolve to real upgrade names.
6. **`create_intelligence_agency` icons (mod-wide)** — every country that creates an agency in focus/event/history files references a real `GFX_intelligence_agency_logo_*` sprite.
7. **`upgrade_intelligence_agency` calls (mod-wide)** — every `upgrade_intelligence_agency = upgrade_X` call (in focuses, events, history, faction goals, etc.) references a defined upgrade.

## Common mistakes

- **Index mismatch across parallel arrays** — e.g. `agency_upgrades^5 = ..._counter_terror_operations` but `agency_names^5 = ..._something_else_name`. The validator catches this.
- **Forgetting to bump `resize_array size =`** — the first four lines of on_actions need the new total.
- **Picture vs `_gfx` loc mismatch** — if `picture = GFX_A` in the def but `_gfx: "GFX_B"` in loc, the vanilla agency UI shows A while the auto-agency queue shows B.
- **Non-existent agency logo** — countries passing an invalid `icon = GFX_intelligence_agency_logo_xyz` to `create_intelligence_agency` silently render a blank. Use the `GFX_intelligence_agency_logo_generic_1..9` sprites when no country-specific one exists.
- **Prereq added to scripted_gui but not to loc** — the prereq tooltip renders as `[MD_auto_agency_prereq_X_tt]` literal text. Add the loc key and the `MD_auto_agency_scripted_loc_prereqs` dispatch entry together.
