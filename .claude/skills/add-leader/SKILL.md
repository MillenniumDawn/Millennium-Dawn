Scaffold generals, field marshals, and admirals for a country following the Millennium Dawn new-general-guidelines.

**Syntax:** `/add-leader [TAG]`

The authoritative guide is `docs/src/content/resources/new-general-guidelines.md`. Read it before starting.

---

## Execution

### 1. Gather country data

Read the following files for TAG:

- OOB file(s): `history/units/TAG_*.oob` — count the number of **division** entries to get starting unit count. Each `division = { }` block is one unit.
- History file: `history/countries/TAG*.txt` — identify whether the country is a major power, faction member, or NATO member.
- Existing character file: `common/characters/TAG.txt` — check if generals already exist to avoid duplicating.

### 2. Calculate counts

Use these formulas:

```
Generals    = ROUND(units / 15) + 1 + IsMajor + IsInFaction + IsNATO
FieldMarshals = ROUND(generals / 3)
Admirals    = ROUND(ships / 15)   # ships = total ship entries in OOB
```

- `IsMajor`, `IsInFaction`, `IsNATO` are each 1 if true, 0 if not.
- Minimum 1 general even if the formula produces 0.
- If the country has no ships, no admirals are needed.
- Counts are per bookmark. If the country has a 2000 and 2017 bookmark, calculate separately. If more leaders are needed in 2017, recruit extras there; if fewer, use `retire_character`.

### 3. Determine skill levels

Use the region table from `.claude/docs/content-guidelines.md` (Generals & Admirals section) for the correct skill range.

Exceptions are allowed for historically notable commanders — justify briefly in the file comment if you exceed the region range.

### 4. Assign skill points

Each general at skill level X gets `(X - 1) * 3 + 4` total skill points distributed across:
`attack_skill`, `defense_skill`, `planning_skill`, `logistics_skill`, `maneuvering_skill`

Every individual skill must be at least 1. Distribute the remaining points to reflect the general's real-world strengths.

### 5. Write the character file

Append to or create `common/characters/TAG.txt`. Follow this structure:

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
		advisor = {                 # optional — for High Command / branch chiefs
			slot = army_chief       # or high_command, navy_chief, air_chief
			idea_token = TAG_general_firstname_lastname
			ledger = army           # army / air / navy — only for high_command slot
			allowed = { original_tag = TAG }
			traits = { army_chief_of_defence_1 }
			cost = 100
			ai_will_do = { factor = 1 }
		}
	}

}
```

**Naming rules:**

- `idea_token` must use `original_tag = TAG` in the `allowed` block — never `tag = TAG`
- Use `firstname_lastname` as the idea_token suffix (no initials, no titles)
- For Field Marshals use `field_marshal = { }`, for regular generals use `general = { }`

**Portrait requirements:**

- Large portrait: 156×210 px — `GFX/leaders/TAG/TAG_firstname_lastname.dds`
- Small portrait: 38×51 px — same folder, `_small` suffix
- If portraits don't exist yet, note them as needed in a comment; place portrait stubs in `gfx/leaders/portrait_dump/` until real portraits are created

### 6. Write recruit_character entries

In `history/countries/TAG*.txt`, add `recruit_character` lines under the correct bookmark:

```
# 2000 bookmark
recruit_character = TAG_general_firstname_lastname

# 2017 bookmark (if count changes between bookmarks)
recruit_character = TAG_general_firstname_extra
```

If a general should be retired between bookmarks, add under the 2017 entry:

```
retire_character = TAG_general_firstname_lastname
```

### 7. Create Air Chief even if no air force

Even if the country has no air force, at least one Air Chief must be defined — players cannot generate them mid-game. Create a minimal Air Chief entry:

```
advisor = {
    slot = air_chief
    idea_token = TAG_general_air_chief
    allowed = { original_tag = TAG }
    traits = { air_chief_all_weather_2 }
    cost = 100
    ai_will_do = { factor = 1 }
}
```

### 8. Report output

Summarise what was written:

- General count (with formula breakdown)
- Field marshal count
- Admiral count
- List of characters with skill levels and traits
- Files modified
- Portraits still needed (names and sizes)
