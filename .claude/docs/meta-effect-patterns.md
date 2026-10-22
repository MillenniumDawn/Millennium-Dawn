# Meta-Effect Patterns

Tokens with `meta_effect` and `meta_trigger` collapse an N-branch dispatch into one
parameterized call, and keep `[!trigger]` tooltips working. Reference: the MIO unlock
catalog.

## Tokens

`token:NAME` refers to a registered game object (MIO, idea, decision, focus). A token
can be stored in an array and read back as its name string with
`[?my_array^i.GetTokenKey]`. That string is what `mio:<NAME>` and `idea:<NAME>` expect.

## `meta_effect`

```
mio_catalog_entry_unlock_yes = {
    meta_effect = {
        text = { unlock_military_industrial_organization_tooltip = mio:[ORG] }
        ORG = "[?global.mio_catalog_all_tokens^v.GetTokenKey]"
    }
}
```

`ORG` resolves to the token name and the engine runs the literal effect. One scripted
effect unlocks the right MIO for the loop variable `v`.

## `meta_trigger`

```
mio_catalog_entry_prereqs_yes = {
    meta_trigger = {
        text = { [TRIG] = yes }
        TRIG = "[?global.mio_catalog_all_tokens^v.GetTokenKey]_unlock_btn_enabled"
    }
}
```

`TRIG` resolves to a real scripted trigger name, such as
`GENERIC_krepost_state_defense_bureau_unlock_btn_enabled`.

- `[!trigger_name]` is a parse-time loc directive, so `[![?dynamic_name]]` is invalid.
  Put `[!mio_catalog_entry_prereqs_yes]` in a static loc value. The outer trigger
  forwards through `meta_trigger`, and `[!]` shows the inner `custom_trigger_tooltip`
  lines:

```yaml
MIO_CAT_UNLOCK_BTN_REQUIREMENTS_TT: "[!mio_catalog_entry_prereqs_yes]"
```

- `v` is 1-based and `add_to_array` is 0-based, so `array^v` is off by one. A scripted
  trigger cannot decrement `v`. Reserve an unused index 0 when seeding the array.
- An empty lookup resolves to an empty string, so `TRIG` becomes `_unlock_btn_enabled`.
  Define that as a fallback: `_unlock_btn_enabled = { always = no }`.

## Naming

Substitution only concatenates. Name per-entity triggers and effects
`<TOKEN_KEY>_<purpose>` from the start. It is hard to retrofit.

## Limits

- A prefix mismatch cannot be stripped. If the flag is
  `krepost_state_defense_bureau_unlocked` and the token is
  `GENERIC_krepost_state_defense_bureau`, rename the flag or use an `if`/`else_if`
  cascade for that part.
- A `localization_key = X` dispatcher does not re-process `[!]` in the value it returns.
  Keep `[!]` in the same flat loc value as the scripted-loc call.
- Substitution takes static text or `[]`-formatted variables only.

Adding an entity then costs one token in the master array, one
`<TOKEN>_unlock_btn_enabled` trigger, and one branch in each remaining cascade or
scripted-loc dispatcher. No new GUI and no new dispatch entries.
