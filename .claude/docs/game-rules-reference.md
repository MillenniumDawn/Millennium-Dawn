# Game Rules Reference

`common/game_rules/00_game_rules.txt` deliberately carries **vanilla's filename**, so MD's file replaces
vanilla's wholesale instead of adding to it. Do not rename it: vanilla's file would then load alongside,
duplicating the 43 rule ids MD overrides and putting 24 WW2 path selectors plus the fragmentation and
colonization toggles back on MD's rules screen.

The consequence is that **any vanilla rule id absent from MD's file stops existing**. A saved game-rule preset
that references one fails to parse and silently drops that setting:

```
[persistent.cpp:67]: Error: "invalid rule id: POR_ai_behavior, near line: 14 ..." in file: "semi random.txt"
```

## Which vanilla rules to drop and which to mirror

- **WW2-only rules stay dropped.** `*_fragmentation_status`, `*_colonization_status`, and the vanilla
  `*_ai_behavior` ideology path selectors have no meaning in 2000-present.
- **Engine-read rules must be mirrored** into the `# VANILLA` section. A rule with no `has_game_rule` reader
  anywhere in vanilla script is read by the engine itself, so dropping it removes a working toggle from the
  rules screen and hardcodes its default. Still missing: `allow_scorched_earth`, `peace_score_to_overlord`,
  `peace_score_to_faction_leader`, `peace_score_reset_low_scores` (the whole "Peace Score distribution"
  group). Vanilla's loc keys still resolve, since MD's loc lives in `MD_game_rules_l_english.yml`.

## MD `*_ai_behavior` rules

They exist to set `TAG_*_FOCUS_PATH` global flags in `common/on_actions/999_game_rules_on_actions.txt`, read
by that country's focus tree. A tag with no MD focus tree gets a `HISTORICAL` option plus the `NO_PATH`
default and no on_action wiring, so vanilla-era presets parse without adding dead effects (`POR`, `LIT`).
Localisation only needs the option keys: vanilla already names every tag it defines a rule for, and MD adds a
`TAG_AI_BEHAVIOR` key only for tags vanilla does not.

## After a HOI4 version bump

List the vanilla rule ids MD no longer defines, then classify each as WW2-only or engine-read:

```bash
grep -oE '^[A-Za-z_0-9]+ = \{' "$HOI4_PATH/common/game_rules/00_game_rules.txt" | sed 's/ = {//' | sort -u > /tmp/van.txt
grep -oE '^[A-Za-z_0-9]+ = \{' common/game_rules/00_game_rules.txt | sed 's/ = {//' | sort -u > /tmp/md.txt
comm -23 /tmp/van.txt /tmp/md.txt
```

An unknown rule id in a preset is not always MD's problem: ids from other mods in the playset that saved it
(The Road to 56's `*_focus_tree_selection` and `player_peace_setting`, for instance) fail the same way and must
not be adopted into MD.
