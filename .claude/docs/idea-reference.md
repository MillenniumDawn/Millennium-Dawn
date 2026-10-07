# Idea Reference

```
BRA_idea_higher_minimum_wage_1 = {
 name = BRA_idea_higher_minimum_wage
 allowed_civil_war = { always = yes }

 picture = gold

 modifier = {
  political_power_factor = 0.1
  stability_factor = 0.05
  consumer_goods_factor = 0.075
  population_tax_income_multiplier_modifier = 0.05
 }
}
```

- Always include `picture = sprite_name`. Without it the idea shows a blank icon.
- Include `allowed_civil_war = { always = yes }` so civil war tags keep the idea.
- Use `original_tag`, not `tag`, in `allowed`.
- In a category with no slot (`country`, `hidden_ideas`), drop `allowed` and `available`
  entirely. Nothing picks from those categories, and `add_idea` never consults either
  block. Use `cancel` if the idea should remove itself.
  `tools/standardization/strip_idea_allowed_gates.py` removes them in bulk.
- In a slotted category, keep `allowed = { always = no }` on ideas that must not appear
  in the picker (religion, other laws). `add_idea` still applies them.
- A slotted idea whose `available` can turn false mid-game needs a `cancel` with the
  negated condition. `available` gates picking only, and the spirit categories have
  `removal_cost = -1`, so nothing else frees the slot. Precedent: the doctrine-gated
  office spirits in `common/ideas/zzz_{army,navy,air}_spirits.txt`.
- Remove `cancel = { always = no }`. It is checked hourly and is never true.
- Drop an `on_add` or `on_remove` whose only statement is a log.
- Tiered ideas use suffix numbering (`TAG_idea_name_1`, `TAG_idea_name_2`) with a shared
  `name = TAG_idea_name`.
- `name = X` makes the game read `X` for the name and `X_desc` for the description. Pick
  an `X` that no focus, decision, or other idea uses, or one string overrides the other.
  A tier that needs its own text takes a distinct `name`.
