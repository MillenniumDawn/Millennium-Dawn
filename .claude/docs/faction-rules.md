# Faction Rules

When creating or editing files in `common/factions/rules/`, follow these conventions derived from the engine documentation in `common/factions/_documentation.md`.

## Faction Rule Structure

Every faction rule must include a `type` field. Valid built-in types and their `trigger` scopes:

| Type                     | `trigger` SCOPE                   | `trigger` FROM |
| ------------------------ | --------------------------------- | -------------- |
| `joining_rules`          | Joining country                   | Faction leader |
| `war_declaration_rules`  | Country declaring war             | Target country |
| `call_to_war_rules`      | Country calling to war            | Target country |
| `member_rules`           | Faction leader                    | —              |
| `change_leader_rules`    | Country becoming leader           | —              |
| `peace_conference_rules` | (used for peace_action_modifiers) | —              |
| `dismissal_rules`        | (dismissal member trigger)        | —              |
| `contribution_rule`      | (contribution effects)            | —              |

**Important:** The `trigger` scope varies by type (see table above), but `visible`, `available`, `can_remove`, and `ai_will_do` **always** scope to the **faction leader** country.

## Required Blocks

Every faction rule that is player-selectable should include:

1. **`type`** — always required
2. **`available`** — controls whether the rule can be selected; should include `is_locked_faction = no` for rules that shouldn't be changeable in locked factions (NATO, CSTO, Resistance Axis)
3. **`can_remove`** — controls whether an active rule can be deselected; **must** include the locked faction check for any rule with `is_locked_faction = no` in `available` or `trigger`:
   ```
   can_remove = {
       NOT = {
           ROOT = {
               is_locked_faction = yes
           }
       }
   }
   ```
4. **`ai_will_do`** — AI weighting (use `base = 0` if AI should not pick it by default)

## Locked Faction Pattern

Locked factions (NATO, CSTO, Resistance Axis) use the `is_locked_faction` scripted trigger. Rules must prevent players from changing settings on locked factions in **two** places:

- **`available`**: `is_locked_faction = no` — prevents selecting the rule
- **`can_remove`**: `NOT = { ROOT = { is_locked_faction = yes } }` — prevents deselecting an active rule

Both are needed because `available` only blocks selection, not removal. Without `can_remove`, a player could still deselect existing rules on NATO/CSTO.

For "impossible" rules (rules that are only active when the faction IS locked), invert the pattern:

```
available = {
    is_locked_faction = yes
}
can_remove = {
    NOT = {
        ROOT = {
            is_locked_faction = yes
        }
    }
}
```

## Existing `can_remove` Conditions

Some rules have additional `can_remove` conditions (e.g., `faction_manifest_fulfillment > 0.95`). When adding the locked faction check to these, place the `NOT = { ROOT = { is_locked_faction = yes } }` block **inside** the existing `can_remove`, alongside the other conditions (they AND together implicitly):

```
can_remove = {
    NOT = {
        ROOT = {
            is_locked_faction = yes
        }
    }
    faction_manifest_fulfillment > 0.95
}
```

## Common Mistake: `not_locked_faction`

`not_locked_faction` is **not a valid scripted trigger**. The engine will silently evaluate it as always-false (or always-true depending on context), breaking the rule's availability logic. Always use:

```
available = {
    is_locked_faction = no   # correct
}
```

Not:

```
available = {
    not_locked_faction = no  # WRONG — does not exist
}
```

## Rules That Don't Need Locked Faction Checks

- Rules with `available = { always = no }` — already permanently unavailable (e.g., scripted-only rules like `call_to_war_rule_chinese_united_front`)
- Rules with `can_remove = { always = no }` — already permanently locked (e.g., `change_leader_rule_never`)
- Rules with `trigger = { always = no }` — never trigger, no need for removal protection unless the rule should only exist on locked factions

## Peace Conference Rules

Rules with `type = peace_conference_rules` must include a `peace_action_modifiers` block referencing modifiers from `common/peace_conference/cost_modifiers`. The enable trigger on the modifier does **not** run — the modifier is active as long as the rule is.

## Checklist When Adding a New Faction Rule

1. Has `type` set to a valid rule type
2. Has `available` with `is_locked_faction = no` (unless intentionally locked-only or scripted-only)
3. Has `can_remove` with locked faction NOT check (unless `always = no` or scripted-only)
4. Has `ai_will_do` with appropriate weighting
5. Has `trigger` with correct scope awareness (see type table above)
6. `visible` is only included when the rule should be hidden from certain factions/governments
7. For `peace_conference_rules`: has `peace_action_modifiers` block
8. For `contribution_rule`: has `effect` block with `set_faction_member_upgrade_min`
