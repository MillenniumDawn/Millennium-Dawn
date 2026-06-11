---
title: Add an EU Nation
description: How to make a country eligible for the European Union system in Millennium Dawn
---

# Add an EU Nation

After the EU rework the system is data-driven through global arrays, so making a new country part of the EU system is just two list edits. You no longer need per-nation scripted localisation, per-party MEP blocks, or per-focus vote flags. Adding a tag to the potential list is enough.

"Potential" means the country can interact with the EU: it shows up for EU AI evaluation, its government and euroscepticism feed the EU's internal numbers, and once it gains candidacy it can apply for membership. It does **not** make the country a member on its own.

## The two lists

The same tag goes in two places, and the two **must stay in sync**:

1. **`EU_is_potential` trigger** in `common/scripted_triggers/99_EU_scripted_triggers.txt`. This is the gate every EU decision category checks (`allowed = { EU_is_potential = yes }`). Add one line to the `OR` block:

   ```
   EU_is_potential = {
       OR = {
           original_tag = ADO
           ...
           original_tag = TAG   # your new nation
       }
   }
   ```

2. **`global.EU_potential` array** in `on_startup_euu_action`, in `common/scripted_effects/99_eu_scripted_effects.txt`. This is the runtime array effects loop over. Add:

   ```
   add_to_array = { global.EU_potential = TAG }
   ```

Use `original_tag` in the trigger (not `tag`) so civil-war split-offs still resolve. Keeping both lists identical avoids the case where a nation passes the decision gate but is missing from the array the effects iterate (or vice versa).

## How the nation then joins

A potential nation is eligible, not yet a member. It becomes a member through the normal flow:

- It gains the `EU_candidate` flag, either from an enlargement council vote (the `601`/`602`/`603`/`605`-`611`/`653` agendas grant candidacy to their cohorts) or from its own focus tree.
- With `EU_candidate` set it can use the apply-for-membership decision once it meets the entry conditions (no war, breach-of-values under the cap, limited external influence, etc.).
- A country that previously left the EU rejoins through the `EU_former_member` cooldown path instead of first-time candidacy.

## Starting members vs potential members

This guide adds a **potential** member. To make a country a **founding** member that starts inside the EU, add it to the `global.EU_member` array (and give it the `EU_member` idea in its history file) rather than `global.EU_potential`. Founding members are the 15 starting states; everyone else enters through candidacy.
