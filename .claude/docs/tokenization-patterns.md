# Tokenization Patterns

How to use HOI4 tokens (`token:NAME`) and `meta_effect` / `meta_trigger` runtime substitution to collapse N-branch dispatch cascades into one parameterized call.

The pattern lets a single effect or trigger handle 23 MIOs / 40 votes / N decisions without copy-paste branching, while keeping `[!trigger]` tooltip rendering intact.

---

## What a token is

`token:GENERIC_krepost_state_defense_bureau` is a parse-time reference to a registered game object — MIO, idea, decision, focus, etc. Tokens can be:

- Stored in arrays (`add_to_array = { my_array = token:GENERIC_krepost_state_defense_bureau }`)
- Read back with `[?my_array^i.GetTokenKey]` — returns the literal token name as a string at runtime
- Used to seed an indexed lookup over many game objects without naming each one in every dispatch

The token's name string is what `mio:<NAME>`, `idea:<NAME>`, etc. consumers expect — `unlock_military_industrial_organization_tooltip = mio:GENERIC_krepost_state_defense_bureau`.

---

## `meta_effect` — runtime substitution into an effect block

```
temp_effect = {
    add_to_array = { temp_array = token:GENERIC_krepost_state_defense_bureau }

    meta_effect = {
        text = {
            unlock_military_industrial_organization_tooltip = mio:[ORG]
        }
        ORG = "[?temp_array^0.GetTokenKey]"
    }
}
```

At evaluation time, `ORG` resolves to `GENERIC_krepost_state_defense_bureau` and the engine sees the literal effect `unlock_military_industrial_organization_tooltip = mio:GENERIC_krepost_state_defense_bureau`. Reference: `common/scripted_effects/00_ct_ai_effects.txt:3-13`.

### Use case: unlock the right MIO from a dynamic_list iteration

```
mio_catalog_entry_unlock_yes = {
    # ...per-entry XP cost + bare-name flag set via if/else_if cascade
    meta_effect = {
        text = {
            unlock_military_industrial_organization_tooltip = mio:[ORG]
        }
        ORG = "[?global.mio_catalog_all_tokens^v.GetTokenKey]"
    }
}
```

One scripted effect; one call from the click handler; the correct MIO unlocks based on the loop variable `v`.

---

## `meta_trigger` — runtime substitution into a trigger block

```
mio_catalog_entry_prereqs_yes = {
    meta_trigger = {
        text = {
            [TRIG] = yes
        }
        TRIG = "[?global.mio_catalog_all_tokens^v.GetTokenKey]_unlock_btn_enabled"
    }
}
```

`TRIG` resolves to (e.g.) `GENERIC_krepost_state_defense_bureau_unlock_btn_enabled` — a real scripted trigger name. The engine evaluates that per-MIO trigger and its `custom_trigger_tooltip` lines render with green/red icons.

Reference: `common/scripted_triggers/01_international_triggers.txt:11-24` (`has_support_of_p5` uses meta_trigger with `thname = "[?FROM.GetTag]"`).

### Why this matters for tooltips

`[!trigger_name]` is a **parse-time** loc directive. You can't write `[![?dynamic_name]]`. But you **can** put `[!mio_catalog_entry_prereqs_yes]` in a static loc value, and that outer trigger uses `meta_trigger` to forward into the per-entry check at evaluation time. The `[!]` walks into the substituted trigger and shows its `custom_trigger_tooltip` lines correctly.

```yaml
MIO_CAT_UNLOCK_BTN_REQUIREMENTS_TT: "[!mio_catalog_entry_prereqs_yes]"
```

Per-MIO requirements with checkmarks behind a single static loc key.

### Defensive fallback

If the array lookup returns nothing (array empty / `v` out of range), `[?array^v.GetTokenKey]` resolves to an empty string. `TRIG = "_unlock_btn_enabled"` then references a trigger named `_unlock_btn_enabled` — define a no-op fallback so the engine doesn't error:

```
_unlock_btn_enabled = {
    always = no
}
```

---

## Naming convention that unlocks meta_trigger / meta_effect

For meta_trigger/effect to interpolate cleanly, the target trigger/effect names must be derivable from the token key with simple string concatenation. The Millennium Dawn MIO catalog uses:

| Token                                  | Derived trigger                                           | Notes                    |
| -------------------------------------- | --------------------------------------------------------- | ------------------------ |
| `GENERIC_krepost_state_defense_bureau` | `GENERIC_krepost_state_defense_bureau_unlock_btn_enabled` | Suffix concatenation     |
| `GENERIC_krepost_state_defense_bureau` | `GENERIC_krepost_state_defense_bureau_<anything_else>`    | Add per-purpose suffixes |

**Rule:** name your per-entity triggers/effects `<TOKEN_KEY>_<purpose>` from day one. Cheap to do, impossible to retrofit cleanly if you start with short names like `mio_cat_krepost_*`.

---

## When meta substitution does _not_ help

- **`mio:`, `idea:`, `decision:` scope references** with prefix mismatches. If your flag is `krepost_state_defense_bureau_unlocked` (no `GENERIC_` prefix) but the token is `GENERIC_krepost_state_defense_bureau`, you can't strip the prefix in substitution. Either rename flags or fall back to an if/else_if cascade for the prefix-mismatched parts.
- **`[!trigger_name]` rendering with a runtime name.** `[!]` is parse-time. Solve by wrapping a static-name outer trigger around a meta_trigger that does the runtime dispatch (see "Why this matters for tooltips" above).
- **`localization_key = X` chained dispatch where X contains `[!]`.** The engine resolves `localization_key` to the loc value as text but does **not** re-process `[!]` on the substituted result. Put `[!]` in the same flat loc value as any scripted-loc invocation, never behind a dispatcher.

---

## End-to-end example — MIO Unlock Catalog

```
# 1. Master array seeded at startup
add_to_array = { global.mio_catalog_all_tokens = token:GENERIC_krepost_state_defense_bureau }
# ...22 more

# 2. Per-entity trigger named after the token
GENERIC_krepost_state_defense_bureau_unlock_btn_enabled = {
    num_of_military_factories > 9
    custom_trigger_tooltip = {
        tooltip = MIO_CAT_REQ_KREPOST_TECH_TT
        has_tech = infantry_weapons_1
    }
}

# 3. Single meta_trigger dispatcher
mio_catalog_entry_prereqs_yes = {
    meta_trigger = {
        text = { [TRIG] = yes }
        TRIG = "[?global.mio_catalog_all_tokens^v.GetTokenKey]_unlock_btn_enabled"
    }
}

# 4. Static loc value calls the dispatcher with [!] — ✓/✗ icons preserved
# MIO_CAT_UNLOCK_BTN_REQUIREMENTS_TT: "[!mio_catalog_entry_prereqs_yes]"

# 5. Single unlock effect with meta_effect for the mio: reference
mio_catalog_entry_unlock_yes = {
    # ...per-entry XP cost via if/else_if (PP/flag cascade unavoidable without rename)
    meta_effect = {
        text = { unlock_military_industrial_organization_tooltip = mio:[ORG] }
        ORG = "[?global.mio_catalog_all_tokens^v.GetTokenKey]"
    }
}
```

Adding a 24th MIO is: append a token to the master array, add one `GENERIC_<token>_unlock_btn_enabled` trigger, one branch in the unlock cost cascade, one branch in each scripted-loc dispatcher. No new GUI, no new dispatch entries in the meta_trigger, no scripted-loc reference renaming.
