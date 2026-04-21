Generate a complete Military-Industrial Organization (MIO) for Millennium Dawn, including the organizations `.txt` block and localisation `.yml` entries, based on online research about the real-world company.

Input (free text): $ARGUMENTS

**All questions to the user must go through `AskUserQuestion`.** Never ask inline in text output. The first question must be a single call asking for the org ID and trait count.

**Authoritative rule sources** (apply silently):

- `~/.claude/CLAUDE.md` — plan-mode workflow, legal modifiers per equipment group, ORG bonus keys + magnitudes, effect magnitude table, layout/dependency rules, cross-branch rules, mutually_exclusive rules, the mandatory `on_complete` + `ai_will_do` blocks, sanity-check list.
- project `CLAUDE.md` + `.claude/docs/mio-reference.md` — MIO naming, `allowed = { original_tag = TAG }`, canonical example, x-range 0..9, parent exactly one row above child, `{org_token}_trait` naming.
- `.claude/docs/mio-modifiers-reference.md` — canonical modifier keys per block type (equipment_bonus / production_bonus / organization_modifier) and equipment category; use this to verify which keys are legal before writing any trait.

Steps:

1. **Collect input.** Parse `$ARGUMENTS` for: organisation ID (e.g. `ITA_leonardo`) and trait count. Derive TAG from the first underscore segment. Look up `{org_id}_name` in `localisation/english/MD_{TAG}*.yml` for the real-world name. If ID or trait count is missing, ask via `AskUserQuestion`:
   - Org ID (free text)
   - Trait count: **15 / 25 / 35 / Other** (structured choice)
   - Number of branches: **1 / 2 / 3** (structured choice)

   If the `_name` loc key does not exist, ask the user for the real-world name.

   **Trait count = regular traits only.** `initial_trait` is always additional. Total written = user count + 1.

   **Never rename the token.** Use the ID verbatim as `TAG_orgname` and as the base for `{org_token}_trait` and all loc keys.

   **Token naming `{org_token}_trait` is fixed per `mio-reference.md`.** Do not search mod files to derive naming patterns.

2. **Online research.** WebSearch + WebFetch (Wikipedia + official site) for: divisions, product lines (military AND civilian), notable programmes, specific vehicle/aircraft/ship/weapon names. If findings are thin, ask for user-supplied context.

3. **Propose branches** (count = user's answer from step 1). Use `AskUserQuestion` with exactly 3 options — no surrounding plain text. Each option lists branch names only, one per line:
   - Option A: primary proposal
   - Option B: first alternative
   - Option C: second alternative

4. **Show a trait outline table** — this is the plan result. Do not summarize or paraphrase it in surrounding text.

   ```
   | Branch | # | Trait name | Modifier type | Icon | x | y | ME partner | Cross-branch parent |
   ```

   List `initial_trait` separately at the top (no x/y needed). Mark mutually_exclusive splits. **A mutually_exclusive pair counts as 1 trait in the budget** (only one can be completed); max 2 traits per pair per branch. The tree must be an organic network: some rows have 2–3 parallel traits, splits can reconverge, cross-branch parents allowed.

   **Fill in absolute x/y for every trait** before presenting the table. Rules:
   - Branches occupy distinct x-lanes; total spread stays within 0–9
   - Mutual exclusives share the same y, placed side-by-side
   - Every child is at y = parent_y + 1 (no skipped rows, no same-row parent/child)
   - Cross-branch parent must have a lower y than its child

   Wait for approval.

4b. **Coverage check.** Before finalising the outline, verify every required modifier for the equipment group appears at least once — use the minimum coverage table in `~/.claude/CLAUDE.md` ("Vermijd repetitie" section). Preferred modifiers must appear on multiple traits if the trait budget allows. Add missing modifiers to existing traits (as a second modifier) or insert a new trait rather than omitting them.

**Locked fields:** If the user's input already contains `equipment_type = { ... }` and/or `research_categories = { ... }`, treat both as final. Steps 5–6 only derive `task_capacity` and confirm consistency — never change the values.

5. **`task_capacity` = 5 × number of equipment _categories_ covered.** Omit if only 1 category (5 is the game default).

   | Category            | In-game equipment types                                                                                                                                                                                                               |
   | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
   | Material            | `infantry_weapons_type`, `cnc_equipment_type`, `artillery_equipment`, `AA_Equipment`, `L_AT_Equipment`, `H_AT_Equipment`, `land_drone_equipment_type`, `train_equipment`                                                              |
   | Armor               | `mio_cat_all_armor`, `util_vehicle_type`, `mio_cat_helicopters`, `heavy_tank_chassis`, `heavy_tank_amphibious_chassis`                                                                                                                |
   | Aircraft & Missiles | `mio_cat_eq_only_light_aircraft`, `mio_cat_eq_only_all_light_aircraft`, `mio_cat_eq_only_medium_aircraft`, `mio_cat_eq_only_all_medium_aircraft`, `mio_cat_eq_only_large_aircraft`, `mio_cat_eq_only_uav`, `guided_missile_equipment` |
   | Naval & Convoy      | `ship_hull_light`, `ship_hull_cruiser`, `ship_hull_heavy`, `ship_hull_carrier`, `ship_hull_submarine`, `convoy`                                                                                                                       |

6. **Research categories** — map what the org actually builds:
   Helicopters → `CAT_heli` · UAVs → `CAT_uav` · fighters → `CAT_fighter` · CAS → `CAT_cas` · bombers → `CAT_bomber` · transport → `CAT_transport_plane` · armour → `CAT_armor` · infantry weapons → `CAT_infantry_weapons` · artillery → `CAT_artillery` · missiles/rockets → `CAT_missile` · naval → relevant `CAT_*` naval types.

7. **Trait names:** max 3 words, always based on a real product, programme, or historical hallmark (e.g. "AW Heritage", "Falco Foundation"). Never generic ("Improved Reliability").

8. **Icons** — `GFX_generic_mio_trait_icon_{kind}` based on primary modifier. Use the table below exclusively; do not search mod files.

   | Modifier                                          | Icon suffix             |
   | ------------------------------------------------- | ----------------------- |
   | `reliability`                                     | `reliability`           |
   | `soft_attack`                                     | `soft_attack`           |
   | `hard_attack`                                     | `hard_attack`           |
   | `build_cost_ic`                                   | `production_cost`       |
   | `production_capacity_factor`                      | `production_efficiency` |
   | `military_industrial_organization_research_bonus` | `task`                  |
   | `air_agility`                                     | `air_agility`           |
   | `air_attack`                                      | `air_attack`            |

   If the trait has `limit_to_equipment_type` for one specific category, use that equipment's icon instead.

   **Helicopter MIOs:** In MD, helicopters use tank chassis — `heavy_tank_amphibious_chassis` (attack) and `heavy_tank_chassis` (transport). They use tank-equivalent stats. Use these icon families:
   - Attack helis: `GFX_generic_mio_trait_icon_attackheli_{reliability|soft_attack|hard_attack|breakthrough|armor|defense|speed|efficiency_gain|buildcost|resource|weight}`
   - Transport/operator helis: `GFX_generic_mio_trait_icon_heli_operator_{reliability|armor|defense|speed|range|buildcost|resources|hg_attack|lg_attack|anti_air_attack|sub_detection|surface_detection}`

**Delegation strategy.** Choose based on trait count:

| Trait count | Strategy                                                                              |
| ----------- | ------------------------------------------------------------------------------------- |
| ≤ 25 traits | One Sonnet subagent for steps 9–10 (current behaviour)                                |
| > 25 traits | One Sonnet subagent **per branch**, all launched in parallel in a single `Agent` call |

**Small MIO (≤ 25 traits) — single subagent.** Same as before: delegate steps 9–10 to one Sonnet subagent (`subagent_type: "general-purpose"`, `model: "sonnet"`). Prompt must include:

- MIO token, TAG, total trait count, `task_capacity` value (or "omit" flag)
- Full `equipment_type` and `research_categories` lists
- Complete approved trait outline table (branch, name, modifier type, absolute x/y, icon token, ME partners, cross-branch parents)
- Target `.txt` file path and `.yml` path
- Pointers to `~/.claude/CLAUDE.md`, project `CLAUDE.md`, `.claude/docs/mio-reference.md`
- Explicit task: write MIO block to `.txt`, append loc keys to `.yml` under `### MIO` per step 10
- Hard constraint: steps 9–10 only. No design changes. If ambiguous, stop and report.

**Large MIO (> 25 traits) — parallel branch subagents.** Launch one Sonnet subagent per branch in a single parallel `Agent` call. Each subagent prompt must include:

- MIO token, TAG, `task_capacity` (or "omit"), `equipment_type`, `research_categories`
- Only the trait rows for **this branch** (name, modifier type, icon, absolute x, absolute y, ME partner if any)
- Cross-branch parents referenced by this branch: name + x/y only (no full other-branch data)
- Pointers to `~/.claude/CLAUDE.md`, project `CLAUDE.md`, `.claude/docs/mio-reference.md`
- Explicit task: **return only the `trait = { ... }` blocks for this branch as plain text.** No `initial_trait`, no MIO header, no file writes.
- Hard constraint: no design changes. If a position or rule is ambiguous, stop and report.

**Assembly (large MIO only).** After all branch subagents return:

1. Combine: MIO header + `initial_trait` block (written by orchestrator) + all branch trait blocks from subagents
2. Sort traits by ascending y, then ascending x (for readability only — does not affect game logic)
3. Write the complete assembled block to `.txt` and append loc keys to `.yml` under `### MIO` — one atomic write each

After writing, relay the result in one short sentence. Do not re-read the files unless a subagent or write reported an error.

9. **Generate the full MIO.** Structure per `.claude/docs/mio-reference.md`. Do not read any organizations `.txt` to derive patterns. Token: `TAG_orgname`. Initial trait name: `{org_token}_trait`. Layout and mandatory blocks follow `~/.claude/CLAUDE.md`.

   **`on_complete` form:** Use `expenditure_for_mio_upgrade = yes` for standard traits. Only use the full HOI4 block when custom country effects are explicitly needed.

   **`limit_to_equipment_type` usage:**
   - MIO has exactly one `equipment_type` entry → never include (redundant).
   - Trait has only `organization_modifier` (no `equipment_bonus` / `production_bonus`) → skip.
   - Trait bonuses apply to all equipment types equally → skip.
   - Only add when the trait targets a strict subset of multiple equipment types.
   - **Category groups:** When `equipment_type` uses a category group (e.g. `mio_cat_all_armor`), individual traits may still use `limit_to_equipment_type` with specific equipment type tokens from within that category (e.g. `limit_to_equipment_type = { medium_tank_chassis medium_tank_artillery_chassis }`).

10. **Localisation + write.**
    Required keys (no `_desc` for traits):
    - `TAG_orgname_name: "Organisation Name"`
    - `TAG_orgname_trait: "Initial Trait Name"`
    - `TAG_orgname_traittoken: "Trait Name"` per trait

    **Skeleton detection (no question needed):** Check if a block matching the org ID already exists in `MD_[TAG]_organizations.txt`. If yes, write traits into that existing block automatically. If no existing block is found, ask: add to existing `MD_[TAG]_organizations.txt` or create a new file.

    **Localisation file:** Find `localisation/english/` file with TAG in the filename; multiple matches → pick the main country file; no match → ask.

    **Append strategy:** look for `### MIO` near the bottom. If absent, add it at EOF and append keys beneath. If present, append after the last existing MIO key. Never insert mid-file.
