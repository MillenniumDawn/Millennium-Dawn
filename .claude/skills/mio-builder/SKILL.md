Generate a complete Military-Industrial Organization (MIO) for Millennium Dawn, including the organizations .txt file and localisation .yml entries, based on online research about the real-world company.

Input (free text): $ARGUMENTS

Steps:

1. **Collect input.** Parse `$ARGUMENTS` for: organisation ID (e.g. `ITA_leonardo`) and number of traits. Do **not** ask for the TAG separately — derive it from the first underscore-separated segment of the ID (`ITA_leonardo` → `ITA`). Then look up `{org_id}_name` in `localisation/english/MD_{TAG}_l_english.yml` (or whichever file in `localisation/english/` contains the TAG) to get the real-world organisation name; that loc value is what step 2 researches online. If the ID or trait count is missing, ask for them. If the `{org_id}_name` loc key does not yet exist (brand-new MIO), ask the user for the real-world organisation name before continuing.

2. **Online research.** Use WebSearch and WebFetch to gather information about the organisation (seeded with the name resolved in step 1):
   - Wikipedia page: products, specialisations, founding, notable programmes
   - Official company website: divisions, product lines — include both military AND civilian branches
   - Focus on: what the organisation builds, which weapon systems they are known for, historical highlights, specific aircraft/vehicle/ship types they produce
   - Civilian branches (e.g. commercial aviation, industrial robots) are valid input for research categories

   If little or no information is found, report what is missing and ask the user for additional context (known programmes, specialisations, historical milestones) before continuing.

3. **Suggest branches.** Based on the research, propose 2–4 branches with:
   - Branch name (short, descriptive)
   - Applicable `limit_to_equipment_type` values
   - Brief motivation based on the real company

   Research categories must reflect what the organisation actually builds — do not include sub-types they do not produce (e.g. if they make fighters but not bombers, omit `CAT_bomber`).

   Ask for user approval before continuing.

4. **Show trait outline table.** Present ALL traits in a table before writing any code:

   ```
   | Branch | Trait name | Modifier type | Based on |
   |--------|-----------|---------------|----------|
   | Heli   | AW Heritage | equipment reliability | AgustaWestland legacy |
   ```

   Also show the `initial_trait` separately. Mark split points (mutually_exclusive traits) and mark which traits share the same row (can be taken simultaneously).

   **The tree must NOT be a straight line.** Design an organic network:
   - Some rows contain 2–3 parallel traits (separate parents, same y-depth) that the player can take in any order
   - Multiple parallel traits can converge to 1–2 follow-up traits
   - Mutually exclusive splits can later reconverge via `any_parent`

   Wait for user approval or adjustments before writing full code.

5. **Calculate task_capacity.** Count which of the four equipment **categories** the MIO covers, multiply by 5. Categories are the four buckets in the table below — not the individual equipment types inside them. Multiple types in the same bucket still count as one category.

   | Category | In-game equipment types |
   |----------|------------------------|
   | Material | `infantry_weapons_type`, `cnc_equipment_type`, `artillery_equipment`, `AA_Equipment`, `L_AT_Equipment`, `H_AT_Equipment`, `land_drone_equipment_type`, `train_equipment` |
   | Armor | `mio_cat_all_armor`, `util_vehicle_type`, `mio_cat_helicopters` |
   | Aircraft & Missiles | `mio_cat_eq_only_light_aircraft`, `mio_cat_eq_only_all_light_aircraft`, `mio_cat_eq_only_medium_aircraft`, `mio_cat_eq_only_all_medium_aircraft`, `mio_cat_eq_only_large_aircraft`, `mio_cat_eq_only_uav`, `guided_missile_equipment` |
   | Naval & Convoy | `ship_hull_light`, `ship_hull_cruiser`, `ship_hull_heavy`, `ship_hull_carrier`, `ship_hull_submarine`, `convoy` |

   **If the MIO covers only one category, omit `task_capacity` entirely** — 5 is the game default and writing it is redundant. Only emit the field for 2+ categories (10, 15, 20).

   Traits are always passive bonuses that unlock on completion; `task_capacity` governs how many concurrent funding tasks the MIO can run — it is not affected by how many equipment types within a single category the MIO touches.

   Example 1: helicopters + UAV + light aircraft = Armor (helicopters) + Aircraft & Missiles (UAV, aircraft) = 2 categories → `task_capacity = 10`.
   Example 2: light aircraft + medium aircraft + UAV = Aircraft & Missiles only = 1 category → omit `task_capacity`.

6. **Derive research categories** from what the organisation specifically builds (step 2). Known mappings:
   - Helicopters → `CAT_heli`
   - UAVs/drones → `CAT_uav`
   - Air superiority fighters → `CAT_fighter`
   - CAS aircraft → `CAT_cas`
   - Bombers → `CAT_bomber`
   - Transport aircraft → `CAT_transport_plane`
   - Armour/tanks → `CAT_armor`
   - Infantry weapons → `CAT_infantry_weapons`
   - Artillery → `CAT_artillery`
   - Naval vessels → relevant `CAT_*` naval types
   - Guided missiles/rockets → `CAT_missile`

7. **Trait names** must be **maximum 3 words** and based on real product names, programmes, or historical characteristics of the organisation. Examples for Leonardo: "AW Heritage", "Falco Foundation", "Anagni CoE". Never use generic names like "Improved Reliability" or "Enhanced Production".

8. **Select icons.** Use `GFX_generic_mio_trait_icon_{stat}` based on the primary modifier:
   - `reliability` → `GFX_generic_mio_trait_icon_reliability`
   - `soft_attack` → `GFX_generic_mio_trait_icon_soft_attack`
   - `hard_attack` → `GFX_generic_mio_trait_icon_hard_attack`
   - `build_cost_ic` → `GFX_generic_mio_trait_icon_production_cost`
   - `production_capacity_factor` → `GFX_generic_mio_trait_icon_production_efficiency`
   - `military_industrial_organization_research_bonus` → `GFX_generic_mio_trait_icon_task`
   - `air_agility` → `GFX_generic_mio_trait_icon_air_agility`
   - `air_attack` → `GFX_generic_mio_trait_icon_air_attack`

   If the trait has a `limit_to_equipment_type` (applies to one specific equipment category), use the icon for that equipment type instead of the generic modifier icon.

9. **Generate the full MIO code.** Read `common/military_industrial_organization/organizations/MD_ENG_organizations.txt` and `common/military_industrial_organization/organizations/MD_CHI_organizations.txt` for structural reference before writing. Then produce the complete organisation block with:

   - `token = TAG_orgname` (snake_case)
   - `name = TAG_orgname_name`
   - `allowed = { original_tag = TAG }`
   - `task_capacity` (from step 5 — **omit if 1 category**)
   - `research_categories = { ... }` (from step 6)
   - `equipment_types = { ... }`
   - `tree_header_text` for each branch at the correct x-coordinate
   - `initial_trait` (auto-generated based on the core identity of the organisation from research). Name it `{org_token}_trait` (e.g. `ITA_leonardo_trait`).
   - All traits with correct positioning

   **Trait positioning rules:**
   - **X-axis is bounded 0..9 across the entire tree.** Branch roots may use `relative_position_id` for their internal vertical chains, but every trait's *effective absolute* x must land in 0..9. Pick branch root x anchors (e.g. 1, 5, 9) that leave enough room for each branch's internal ±1 splits without spilling outside the window. Y has no upper bound.
   - **A trait's parent is always exactly one y-row above.** In relative terms that means children sit at `y = 1` relative to their parent (i.e. parent is effectively `y = -1` from the child's perspective). Never skip rows or place a child on the same row as its parent — the tree must always flow downward row by row.
   - Each branch starts at y=0, spread x-coordinates (e.g. x=1, x=5, x=9 for 3 branches)
   - Vertical chains: use `relative_position_id = parent_token` + `position = { x = 0 y = 1 }`
   - Splits: two children at `position = { x = -1 y = 1 }` and `position = { x = 1 y = 1 }` relative to parent, with `mutually_exclusive = { other_child }`
   - Reconvergence after a split: `any_parent = { left_trait right_trait }`
   - Parallel traits on the same row: multiple traits share the same parent, same y, different x offsets — player can take them in any order
   - Convergence: 2–3 parallel traits can all lead to the same follow-up trait via `any_parent` or `all_parents`

   All traits get `ai_will_do = { base = 10 }`.

10. **Generate localisation.** Keys needed:
    - `TAG_orgname_name: "Organisation Name"`
    - `TAG_orgname_trait: "Initial Trait Name"` (matches the `{org_token}_trait` name from step 9)
    - `TAG_orgname_traittoken: "Trait Name"` for every trait (max 3 words, real programme/product name)

    **No `_desc` keys for traits.**

    To find the right localisation file: search `localisation/english/` for a file whose name contains the TAG (e.g. `MD_ITA_l_english.yml`). If not found, ask the user which file to use.

11. **Write files and standardise.**
    Ask the user: add to existing `MD_[TAG]_organizations.txt` or create a new file?

    After confirmation:
    1. Write the MIO block to the organisations file
    2. Run the standardiser: `python tools/standardization/standardize_mio.py <filepath>` — this enforces property order and formatting automatically
    3. Append the localisation keys to the correct `.yml` file (UTF-8 with BOM)
