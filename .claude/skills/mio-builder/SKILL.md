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
   | Branch | # | Trait name | Modifier type | Icon | abs_x | abs_y | rel_x | rel_y | ME partner | Cross-branch parent | limit_to_equipment_type |
   ```

   List `initial_trait` separately at the top (no coordinates needed). Mark mutually_exclusive splits. **A mutually_exclusive pair counts as 1 trait in the budget** (only one can be completed); max 2 traits per pair per branch. The tree must be an organic network: some rows have 2–3 parallel traits, splits can reconverge, cross-branch parents allowed.

   **Per-branch `limit_to_equipment_type` is mandatory when the MIO covers multiple equipment types and the branches map to different subsets.** Before drawing the table, determine the equipment subset each branch represents (e.g. branch "Tanks" → `medium_tank_chassis`, branch "APCs" → `APC_chassis mod_APC_chassis`). Fill the `limit_to_equipment_type` column for **every** trait in that branch that has an `equipment_bonus` or `production_bonus` — not just one per branch. Write the explicit token list in each row; `—` only when a skip rule applies (see step 9). Skip rules: single-equipment MIO, `organization_modifier`-only trait, or the bonus genuinely applies to the whole MIO scope.

   **Two coordinate systems — fill in both for every trait** before presenting the table:
   - `abs_x / abs_y` = absolute position on the global grid (0–9 range for x). Used for overlap checks and cross-branch parent validation only.
   - `rel_x / rel_y` = offset from branch root. This is what goes into the code `position = { x = ... y = ... }`.
     - Branch root traits: `rel_x = abs_x`, `rel_y = 0` (they have no `relative_position_id` in code).
     - All other traits: `rel_x = abs_x − root_abs_x`, `rel_y = abs_y − root_abs_y`.

   Layout rules (validated against `abs_x / abs_y`):
   - Branches occupy distinct x-lanes; total spread stays within 0–9
   - Mutual exclusives share the same `abs_y`, placed side-by-side
   - Every child is at `abs_y = parent_abs_y + 1` (no skipped rows, no same-row parent/child)
   - No two traits share the same `(abs_x, abs_y)` pair
   - Cross-branch parent must have a lower `abs_y` than its child

   Wait for approval.

4b. **Modifier planning — coverage + diversity cap.** Before finalising the outline, run an explicit planning pass. This is the _thinking_ layer: determine what modifiers each trait carries before any code is written.

**Plan framework (answer in order, do not skip):**

1.  **Which equipment_type does this MIO cover?** Map it to the legal-modifier list in [`.claude/docs/mio-modifiers-reference.md`](../../docs/mio-modifiers-reference.md). List the **required** keys (coverage ≥ 1×) and **preferred** keys (may stack up to 3×) for this equipment group.
2.  **Which traits are thematic vs cross-cutting?** Thematic traits (chassis / platform-specific) keep their `limit_to_equipment_type`. Cross-cutting traits (production, maintenance, research, funds) carry no limit. Mutual-exclusive pairs may split on limit.
3.  **Which keys go in `equipment_bonus` vs `production_bonus` vs `organization_modifier`?** They count as separate keys even when the underlying stat overlaps.

**Planning table (required before writing any trait):**

```
| # | trait_token | block types | eq_bonus keys | prod_bonus keys | org_mod keys | limit_to_equipment_type |
```

**Fill logic:**

- Walk the required-key list and assign each key to at least one trait (coverage first).
- Preferred keys may stack up to **3×** across the whole MIO (`initial_trait` counts). Required keys stay at 1–2× unless also preferred.
- `equipment_bonus` and `production_bonus` variants of the same stat count as separate keys. `organization_modifier` keys count separately from each other.
- Max 3 blocks per trait: at most 1× `equipment_bonus` + 1× `production_bonus` + 1× `organization_modifier`.

**Pre-write count check (mandatory):** tally each key across the planning table and write the totals below it (e.g. `soft_attack(eq): 3, reliability(eq): 2, build_cost_ic(prod): 2, ...`). If any total is ≥ 4, redistribute the excess to an under-covered key before finalising. If any required key has 0 occurrences, add it before a second instance of any already-covered key. Only finalise the outline once every required key has ≥ 1 and no key has ≥ 4.

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

8. **Icons** — always write `icon = x` as a literal placeholder. This will produce a game error, which is expected and intentional — the user assigns real icon values manually afterwards. Do not attempt to resolve or replace `x` with any icon path.

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
- Complete approved trait outline table (branch, name, modifier type, abs_x/abs_y, rel_x/rel_y, icon token, ME partners, cross-branch parents, limit_to_equipment_type per trait where applicable)
- Positioning rule: branch root traits use `position = { x = abs_x y = 0 }` with no `relative_position_id`; all child traits use `relative_position_id = <branch_root_token>` and `position = { x = rel_x y = rel_y }` from the outline. Never use abs_x/abs_y directly in child trait code.
- `limit_to_equipment_type` rules: (1) MIO has exactly one `equipment_type` entry → never include (redundant). (2) Trait has only `organization_modifier` (no `equipment_bonus` / `production_bonus`) → skip. (3) Trait bonuses apply to all equipment types equally → skip. (4) Only add when the trait targets a strict subset of multiple equipment types. (5) When `equipment_type` uses a category group (e.g. `mio_cat_all_armor`), individual traits may still use `limit_to_equipment_type` with specific tokens from within that category (e.g. `limit_to_equipment_type = { medium_tank_chassis medium_tank_artillery_chassis }`). (6) **Per-branch rule (critical):** when branches map to different equipment subsets, every `equipment_bonus` / `production_bonus` trait in a branch MUST carry the `limit_to_equipment_type` value from its outline row — do not omit it because "the branch name already implies it". Copy the token list verbatim from the outline table into each trait.
- Target `.txt` file path and `.yml` path
- Pointers to `~/.claude/CLAUDE.md`, project `CLAUDE.md`, `.claude/docs/mio-reference.md`
- Explicit task: write MIO block to `.txt`, append loc keys to `.yml` under `### MIO` per step 10
- Hard constraint: steps 9–10 only. No design changes. If ambiguous, stop and report.

**Large MIO (> 25 traits) — parallel branch subagents.** Launch one Sonnet subagent per branch in a single parallel `Agent` call. Each subagent prompt must include:

- MIO token, TAG, `task_capacity` (or "omit"), `equipment_type`, `research_categories`
- Only the trait rows for **this branch** (name, modifier type, icon, abs_x, abs_y, rel_x, rel_y, ME partner if any, limit_to_equipment_type where applicable)
- Cross-branch parents referenced by this branch: name + abs_x/abs_y only (no full other-branch data)
- Positioning rule: branch root traits use `position = { x = abs_x y = 0 }` with no `relative_position_id`; all child traits use `relative_position_id = <branch_root_token>` and `position = { x = rel_x y = rel_y }` from the outline. Never use abs_x/abs_y directly in child trait code.
- `limit_to_equipment_type` rules: (1) MIO has exactly one `equipment_type` entry → never include (redundant). (2) Trait has only `organization_modifier` (no `equipment_bonus` / `production_bonus`) → skip. (3) Trait bonuses apply to all equipment types equally → skip. (4) Only add when the trait targets a strict subset of multiple equipment types. (5) When `equipment_type` uses a category group (e.g. `mio_cat_all_armor`), individual traits may still use `limit_to_equipment_type` with specific tokens from within that category (e.g. `limit_to_equipment_type = { medium_tank_chassis medium_tank_artillery_chassis }`). (6) **Per-branch rule (critical):** when branches map to different equipment subsets, every `equipment_bonus` / `production_bonus` trait in a branch MUST carry the `limit_to_equipment_type` value from its outline row — do not omit it because "the branch name already implies it". Copy the token list verbatim from the outline table into each trait.
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
   - **Per-branch rule (critical, most-often-forgotten):** If the MIO has multiple `equipment_type` entries **and** branches map to different equipment subsets, every `equipment_bonus` / `production_bonus` trait in a branch must carry `limit_to_equipment_type` for that branch's subset. Copy the token list straight from the outline table — do not rely on the branch name alone to communicate scope to the game engine.
   - **Category groups:** When `equipment_type` uses a category group (e.g. `mio_cat_all_armor`), individual traits may still use `limit_to_equipment_type` with specific equipment type tokens from within that category (e.g. `limit_to_equipment_type = { medium_tank_chassis medium_tank_artillery_chassis }`).

10. **Localisation + write.**
    Required keys (no `_desc` for traits):
    - `TAG_orgname_name: "Organisation Name"`
    - `TAG_orgname_trait: "Initial Trait Name"`
    - `TAG_orgname_traittoken: "Trait Name"` per trait

    **Skeleton detection (no question needed):** Check if a block matching the org ID already exists in `MD_[TAG]_organizations.txt`. If yes, write traits into that existing block automatically. If no existing block is found, ask: add to existing `MD_[TAG]_organizations.txt` or create a new file.

    **Localisation file:** Find `localisation/english/` file with TAG in the filename; multiple matches → pick the main country file; no match → ask.

    **Append strategy:** look for `### MIO` near the bottom. If absent, add it at EOF and append keys beneath. If present, append after the last existing MIO key. Never insert mid-file.

**Post-write sanity check (mandatory before reporting done):** After files are written, re-verify `limit_to_equipment_type` coverage against the outline table:

1. For each branch with a non-empty `limit_to_equipment_type` value in the outline, grep the generated `.txt` block and confirm the expected number of traits carry that exact token list.
2. If any trait that should have `limit_to_equipment_type` is missing it, patch the file immediately — do not report the MIO as done until the coverage matches the outline.
3. Only skip this check when the MIO has a single `equipment_type` entry (rule 1 always applies).

**Civil War (CW) errors:** Do not validate or flag CW-related errors during generation. Only check for them at the very end, and treat any CW errors found as potentially false positives caused by caching — report them as advisory only, not blockers.
