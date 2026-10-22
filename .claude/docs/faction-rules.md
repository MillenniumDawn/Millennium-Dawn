# Faction Rules

For files in `common/factions/rules/`. Engine documentation:
`common/factions/_documentation.md`.

`create_faction = NAME` is deprecated in MD. Use
`create_faction_from_template = TEMPLATE`.

## Rule types

| Type                     | `trigger` scope          | `trigger` FROM |
| ------------------------ | ------------------------ | -------------- |
| `joining_rules`          | Joining country          | Faction leader |
| `war_declaration_rules`  | Country declaring war    | Target country |
| `call_to_war_rules`      | Country calling to war   | Target country |
| `member_rules`           | Faction leader           |                |
| `change_leader_rules`    | Country becoming leader  |                |
| `peace_conference_rules` | Used for peace modifiers |                |
| `dismissal_rules`        | Dismissal member trigger |                |
| `contribution_rule`      | Contribution effects     |                |

`visible`, `available`, `can_remove`, and `ai_will_do` always scope to the faction
leader, whatever the type.

## Locked factions

NATO, CSTO, and the Resistance Axis are locked. A player-selectable rule blocks changes
in two places, because `available` stops selection but not removal:

```
available = {
    is_locked_faction = no
}
can_remove = {
    NOT = {
        ROOT = {
            is_locked_faction = yes
        }
    }
    faction_manifest_fulfillment > 0.95   # other conditions sit alongside
}
```

- For a rule that is active only on locked factions, use `is_locked_faction = yes` in
  `available` and keep the same `can_remove`.
- `not_locked_faction` is not a trigger. Use `is_locked_faction = no`.
- No locked check is needed on a rule with `available = { always = no }`,
  `can_remove = { always = no }`, or `trigger = { always = no }`.

## Checklist

1. `type` is a valid rule type, and `trigger` uses that type's scope.
2. `available` has `is_locked_faction = no`, unless the rule is locked-only or
   scripted-only.
3. `can_remove` has the locked check.
4. `ai_will_do` is set. Use `base = 0` if the AI should not pick it.
5. `visible` appears only when the rule is hidden from some factions or governments.
6. `peace_conference_rules` has a `peace_action_modifiers` block referencing
   `common/peace_conference/cost_modifiers`. The modifier's own enable trigger does not
   run. It is active as long as the rule is.
7. `contribution_rule` has an `effect` block with `set_faction_member_upgrade_min`.
