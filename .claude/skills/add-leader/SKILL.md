---
name: add-leader
description: 'Scaffold generals, field marshals, and admirals for a country using the MD count formulas and region skill ranges, writing character and recruit_character entries. Use when asked to add leaders, generals, or admirals for a TAG, e.g. "/add-leader NIG".'
---

**Syntax:** `/add-leader [TAG]`

Read `docs/src/content/resources/new-general-guidelines.md` first. Count formulas,
skill ranges, and portrait sizes are in `.claude/docs/content-guidelines.md`.

## 1. Gather country data

- `history/units/TAG_*.txt`: count `division = { }` blocks and ship entries.
- `history/countries/TAG*.txt`: major power, faction member, or NATO member.
- `common/characters/TAG.txt`: existing generals, to avoid duplicates.

## 2. Counts and skills

- Apply the formulas. At least one general. No ships means no admirals.
- Counts are per bookmark. With both 2000 and 2017 bookmarks, recruit extras in 2017
  when more are needed and use `retire_character` when fewer.
- Take the skill level from the region range. A historically notable commander may
  exceed it.
- A general at level X gets `(X - 1) * 3 + 4` points across `attack_skill`,
  `defense_skill`, `planning_skill`, `logistics_skill`, and `maneuvering_skill`, each at
  least 1.

## 3. Character file

Append to or create `common/characters/TAG.txt`:

```
characters = {

	TAG_general_firstname_lastname = {
		name = "Firstname Lastname"
		portraits = {
			army = {
				large = "GFX_portrait_TAG_firstname_lastname_large"
				small = "GFX_portrait_TAG_firstname_lastname_small"
			}
		}
		field_marshal = {           # or general = { }
			traits = { trait_name }
			skill = X
			attack_skill = N
			defense_skill = N
			planning_skill = N
			logistics_skill = N
			maneuvering_skill = N
			legacy_id = -1
		}
		advisor = {                 # optional, for high command and branch chiefs
			slot = army_chief       # or high_command, navy_chief, air_chief
			idea_token = TAG_general_firstname_lastname
			ledger = army           # only for the high_command slot
			allowed = { original_tag = TAG }
			traits = { army_chief_of_defence_1 }
			cost = 100
			ai_will_do = { factor = 1 }
		}
	}

}
```

- The `allowed` block uses `original_tag`, never `tag`.
- The token suffix is `firstname_lastname`, with no initials or titles.
- Portraits go in `gfx/leaders/TAG/`. List any that do not exist yet in the report.
- Define an air chief even with no air force. Players cannot generate one mid-game.

## 4. Recruit entries

In `history/countries/TAG*.txt`, under the right bookmark:

```
recruit_character = TAG_general_firstname_lastname
retire_character = TAG_general_firstname_lastname   # 2017, when the count drops
```

## 5. Report

General, field marshal, and admiral counts with the formula breakdown, each character's
skill and traits, the files changed, and the portraits still needed.
