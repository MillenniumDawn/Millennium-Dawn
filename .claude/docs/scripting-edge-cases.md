# Scripting Edge Cases

Niche scripting pitfalls moved out of the always-loaded `general-rules.md`. Read this when editing influence code (`change_influence_percentage`) or any function that uses `^index` array subscripts.

## change_influence_percentage

The scripted effect uses temp-variable arguments with these defaults:

| Temp variable      | Required | Default   |
| ------------------ | -------- | --------- |
| `percent_change`   | yes      | —         |
| `tag_index`        | no       | `ROOT.id` |
| `influence_target` | no       | `THIS.id` |

Three pitfalls:

1. **Don't write redundant defaults.** `set_temp_variable = { tag_index = ROOT.id }` and `set_temp_variable = { influence_target = THIS.id }` are no-ops. Leave them out.
2. **Orphan setters are silent bugs.** A `percent_change` / `tag_index` / `influence_target` triple with no following `change_influence_percentage = yes` does nothing. When auditing influence code, grep for `percent_change` setters and confirm each has a matching invocation in the same scope.
3. **Loop-local temp vars need the call inside the loop.** Setting temp vars inside `random_other_country` / `random_country` / `every_country` then calling `change_influence_percentage = yes` outside the block runs the effect once with stale or undefined values. The invocation must live in the same scope as the temp-var writes.

```
# Wrong — call runs outside the loop; tag_index/influence_target resolve to outer scope
random_other_country = {
    limit = { ... }
    set_temp_variable = { percent_change = 3 }
    set_temp_variable = { tag_index = THIS.id }
    set_temp_variable = { influence_target = PREV.id }
}
change_influence_percentage = yes

# Correct — call inside the loop with the loop-local scopes
random_other_country = {
    limit = { ... }
    set_temp_variable = { percent_change = 3 }
    set_temp_variable = { tag_index = THIS.id }
    set_temp_variable = { influence_target = PREV.id }
    change_influence_percentage = yes
}
```

Also watch for typos in the temp-var name itself (e.g., `influence_tBRAet` from a botched search-and-replace) — the engine accepts any name, so a typo silently sets a never-read variable and the influence change uses the default `THIS.id` target.

## Array Index Semantics

When a function uses `^index` array subscripts, the **meaning of the index variable** must be obvious and consistent. Bugs arise when two different index types are stored in similarly-named variables.

| Variable name              | Should hold                  | Must NOT hold                                   |
| -------------------------- | ---------------------------- | ----------------------------------------------- |
| `project`, `slot`, `idx`   | Slot / array position (0..N) | Building type, category ID, or other lookup key |
| `type`, `kind`, `category` | Lookup key / type ID (1..N)  | Slot index                                      |

**Rule:** Document an array-index parameter in the function comment. Verify every caller passes the right kind of index. See `.claude/docs/refactor-checklist.md` for the full verification steps.
