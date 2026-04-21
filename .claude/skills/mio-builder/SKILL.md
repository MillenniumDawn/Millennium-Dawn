Generate a complete Military-Industrial Organization (MIO) for Millennium Dawn, including the organizations `.txt` block and localisation `.yml` entries, based on online research about the real-world company.

Input (free text): $ARGUMENTS

**All questions to the user must go through `AskUserQuestion`.** Never ask inline in text output — applies to missing input, branch approval, outline approval, file-choice, etc. The first question needs to be one question where you ask the user in provide the ID of the organisation and the amount of traits.

**Authoritative rule sources** (apply silently, don't repeat their contents here):

- `~/.claude/CLAUDE.md` — plan-mode workflow, legal modifiers per equipment group, ORG bonus keys + magnitudes, effect magnitude table, layout/dependency rules, cross-branch rules, mutually_exclusive rules, the mandatory `on_complete` + `ai_will_do` blocks, sanity-check list.
- project `CLAUDE.md` + `.claude/docs/mio-reference.md` — MIO naming, `allowed = { original_tag = TAG }`, canonical example, x-range 0..9, parent exactly one row above child, `{org_token}_trait` naming.

Steps:

1. **Collect input.** Parse `$ARGUMENTS` for: organisation ID (e.g. `ITA_leonardo`) and trait count. Derive TAG from the first underscore segment (`ITA_leonardo` → `ITA`). Look up `{org_id}_name` in the matching `localisation/english/MD_{TAG}*.yml` file to get the real-world name for research. If ID or trait count is missing, ask. If the `_name` loc key does not yet exist (brand-new MIO), ask the user for the real-world name.

   **Never rename the token.** The ID the user provides is the final token — use it verbatim as `TAG_orgname` and as the base for `{org_token}_trait` and all loc keys. Do not normalise case, swap underscores, shorten, or "correct" it, even if it looks inconsistent with other MIOs.

2. **Online research.** WebSearch + WebFetch (Wikipedia + official site) for: divisions, product lines (military AND civilian), notable programmes, specific vehicle/aircraft/ship/weapon names. If findings are thin, ask for user-supplied context.

3. **Propose 2–3 branches** — short name, applicable `limit_to_equipment_type` values, 1-sentence motivation grounded in the real company. Research categories must reflect what the org actually builds (no bombers if they make only fighters). Ask for approval.

4. **Show a trait outline table** before writing any code:

   ```
   | Branch | Trait name | Modifier type | Based on |
   ```

   List `initial_trait` separately. Mark mutually_exclusive splits and which traits share a row. The tree must be an organic network, not a straight line: some rows have 2–3 parallel traits, splits can reconverge, cross-branch parents allowed. Wait for approval.

5. **`task_capacity` = 5 × number of equipment _categories_ covered.** Categories are the four buckets below (multiple types in one bucket = one category). **Omit the field entirely if only 1 category** — 5 is the game default.

   | Category            | In-game equipment types                                                                                                                                                                                                               |
   | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
   | Material            | `infantry_weapons_type`, `cnc_equipment_type`, `artillery_equipment`, `AA_Equipment`, `L_AT_Equipment`, `H_AT_Equipment`, `land_drone_equipment_type`, `train_equipment`                                                              |
   | Armor               | `mio_cat_all_armor`, `util_vehicle_type`, `mio_cat_helicopters`, `heavy_tank_chassis`, `heavy_tank_amphibious_chassis`                                                                                                                |
   | Aircraft & Missiles | `mio_cat_eq_only_light_aircraft`, `mio_cat_eq_only_all_light_aircraft`, `mio_cat_eq_only_medium_aircraft`, `mio_cat_eq_only_all_medium_aircraft`, `mio_cat_eq_only_large_aircraft`, `mio_cat_eq_only_uav`, `guided_missile_equipment` |
   | Naval & Convoy      | `ship_hull_light`, `ship_hull_cruiser`, `ship_hull_heavy`, `ship_hull_carrier`, `ship_hull_submarine`, `convoy`                                                                                                                       |

6. **Research categories** — map what the org actually builds:
   - Helicopters → `CAT_heli` · UAVs → `CAT_uav` · fighters → `CAT_fighter` · CAS → `CAT_cas` · bombers → `CAT_bomber` · transport → `CAT_transport_plane` · armour → `CAT_armor` · infantry weapons → `CAT_infantry_weapons` · artillery → `CAT_artillery` · missiles/rockets → `CAT_missile` · naval → relevant `CAT_*` naval types.

7. **Trait names:** max 3 words, always based on a real product, programme, or historical hallmark (e.g. "AW Heritage", "Falco Foundation", "Anagni CoE"). Never generic ("Improved Reliability").

8. **Icons** — `GFX_generic_mio_trait_icon_{kind}` based on primary modifier:

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

   If the trait has `limit_to_equipment_type` for one specific equipment category, use that equipment's icon instead.

   **Helicopter MIOs (IMPORTANT):** In MD, helicopters are implemented on tank chassis — `heavy_tank_amphibious_chassis` (attack helicopters) and `heavy_tank_chassis` (transport helicopters). They use tank-equivalent stats (`reliability`, `soft_attack`, `hard_attack`, `ap_attack`, `breakthrough`, `armor_value`, `maximum_speed`, `defense`, `hardness`, `build_cost_ic`, `anti_air_attack`). Use these dedicated heli icon families:
   - Attack helis: `GFX_generic_mio_trait_icon_attackheli_{reliability|soft_attack|hard_attack|breakthrough|armor|defense|speed|efficiency_gain|buildcost|resource|weight}`
   - Transport/operator helis: `GFX_generic_mio_trait_icon_heli_operator_{reliability|armor|defense|speed|range|buildcost|resources|hg_attack|lg_attack|anti_air_attack|sub_detection|surface_detection}`

**Model delegation (Opus → Sonnet).** Before executing steps 9-10, check the active model. If the system prompt states _"You are powered by the model named Opus"_, steps 9-10 are mechanical file writes — delegate to a Sonnet subagent to conserve tokens. On any other model, run steps 9-10 inline.

Delegation call: `Agent` with `subagent_type: "general-purpose"` and `model: "sonnet"`. The subagent starts cold; the prompt must be fully self-contained and include:

- MIO token (e.g. `ITA_leonardo`), TAG, total trait count, and the `task_capacity` value — or an explicit "omit (only 1 category)" flag
- Full `equipment_type` list and `research_categories` list
- Complete trait outline table approved in step 4, with icons resolved per step 8: per trait the branch, name, modifier type, absolute x/y position, icon token, mutually_exclusive partners, cross-branch parents
- Target `.txt` file path: append to existing `MD_[TAG]_organizations.txt` or create new (user's step 10 choice)
- Absolute path of the target localisation `.yml` (confirmed in step 10)
- Pointer to authoritative rules — `~/.claude/CLAUDE.md` (mandatory `on_complete` + `ai_will_do` blocks, layout rules, ORG-modifier keys + magnitudes, effect magnitude table), project `CLAUDE.md`, `.claude/docs/mio-reference.md`. Do **not** re-derive or summarise them in the prompt.
- Explicit task: write the MIO block to the `.txt`, then append loc keys to the `.yml` under `### MIO` (UTF-8 with BOM), exactly per step 10.
- Hard constraint: execute steps 9-10 **only**. No design changes, no renaming, no inventing traits/modifiers/icons. If the outline is ambiguous or rules conflict, stop and report — do not improvise.

After the subagent returns, relay the result to the user in one short sentence (file written, loc keys appended). Do not re-read the generated files unless the subagent reported an error. If the subagent fails or the model cannot be determined, fall back to executing steps 9-10 inline.

9. **Generate the full MIO.** _If Model delegation applies, the Sonnet subagent performs this step and step 10 — the main conversation stops here._ Structure per `.claude/docs/mio-reference.md` and `common/military_industrial_organization/organizations/MD_ENG_organizations.txt` / `MD_CHI_organizations.txt`. Token: `TAG_orgname`. Initial trait name: `{org_token}_trait`. Layout and mandatory code blocks follow the global `~/.claude/CLAUDE.md` rules — don't re-derive them.

   **`limit_to_equipment_type` usage (skill-specific, not in CLAUDE.md):**
   - MIO has exactly **one** entry in `equipment_type` → **never** include it (redundant).
   - Trait has **only** an `organization_modifier` block (no `equipment_bonus` / `production_bonus`) → skip it.
   - Trait's bonuses apply to **all** of the MIO's equipment types equally → skip it.
   - Only add it when the trait targets a strict subset of multiple equipment types.

10. **Localisation + write**
    Required keys (no `_desc` for traits):
    - `TAG_orgname_name: "Organisation Name"`
    - `TAG_orgname_trait: "Initial Trait Name"`
    - `TAG_orgname_traittoken: "Trait Name"` per trait

    Find the file: `localisation/english/` with TAG in the filename (e.g. `MD_ITA_l_english.yml`); multiple matches → pick the main country file; no match → ask.

    Append strategy: look for a `### MIO` comment near the bottom. If absent, add it at EOF and append keys beneath it. If present, append new keys directly after the last existing MIO key. Never insert mid-file.

    Ask: add to existing `MD_[TAG]_organizations.txt` or create a new file. After confirmation:
    1. Write the MIO block.
    2. Append loc keys to the `.yml` (UTF-8 with BOM).
