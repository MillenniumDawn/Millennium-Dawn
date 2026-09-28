# STALKER Scenario

The opt-in STALKER scenario (MillenniumDawn/Millennium-Dawn#4791) is split into subsystems. Each
subsystem owns its own files and its own block of event IDs, so parallel work does not collide.
Add content to the subsystem that owns it, and touch shared files only through the hooks below.

## Rules

- **Own files only.** New events, decisions, effects and localisation go in the subsystem's
  files. A new subsystem gets new files and the next free event-ID block.
- **Event IDs.** Use only your subsystem's block. Never reuse or renumber an ID.
- **Localisation.** Keys live in the subsystem's `MD_STALKER_<subsystem>_l_english.yml`. Keys
  used by two or more subsystems live in the core file `MD_STALKER_l_english.yml`.
- **Monthly work.** Add a line to `STALKER_monthly_pulse` in
  `common/scripted_effects/99_STALKER_pulse_effects.txt`. Do not add lines to `MD_on_actions.txt`.
- **Changelog.** Each STALKER PR adds one BLUF line to `Changelog.txt`, as `AGENTS.md` requires.
- **Target `main`.** The scenario landed on `main` with #372; `feature/stalker-global-zones-4791`
  is retired. Merge STALKER PRs one at a time, and merge the latest `main` into each one first.

## Canon

Player-facing text follows GSC Game World's games. GSC's own pages carry little lore, so check
names and events against the in-game text as documented by the S.T.A.L.K.E.R. Wiki and Game8.

- Use STALKER 2 spellings: Chornobyl, and Dr. Kaymanov, the Doctor.
- In the Kaymanov ending, Skif defies Strelok, spares the Doctor, enters the eighth
  C-Consciousness pod and cedes control to the Zone. New Zones then form around the world.
- The Ward is SIRCAA's private army under Colonel Korshunov. SIRCAA does the research.
- The Spark follows Scar and seeks the Shining Zone. Noon is former Monolith under Strider.
- The IPSF is the International Perimeter Security Force.
- The in-game scientists are the Ecologists.
- Faction Wars and Tearlings come from GSC's pre-launch Discord event in the official
  S.T.A.L.K.E.R. server (announcements of 9, 11 and 17 November 2024). SIRCAA asked every
  faction to bring in Tearlings, common crystals long logged as worthless. The Free Stalkers
  delivered the most, 331 of 1,232, and every faction got a share of the rewards.
- Reference-map Zones follow the #4791 reference image, which shows 27 outbreak markers besides
  Chornobyl. Zones 5 (New Mexico), 12 (Paraguayan Chaco), 15 (Wielkopolska) and 27 (Lake Mungo)
  have no marker on it and are this scenario's own additions. Zone 31 (Aksai Chin) was added
  after a placement check found its marker unassigned. The map is a guideline, not a cap: add
  Zones where lore or gameplay calls for them, and note each addition in the placement table.
- Not canon, and specific to this scenario's design: "Project X" and MDST. Keep them clearly
  framed as this scenario's own inventions.

## Subsystems

- **Core Zone (1–9):** `STALKER.txt`; loc `MD_STALKER_l_english.yml`; `STALKER_decisions.txt`;
  `99_STALKER_scripted_effects.txt`, `_society_`, `_zone_placements`, `_pulse_`, `_top_`.
- **X-Labs (10–19):** `STALKER_xlabs.txt`; loc `_xlabs_`; `STALKER_xlab_decisions.txt`;
  `99_STALKER_xlab_effects.txt`.
- **International (20–29):** `STALKER_international.txt`; loc `_international_`;
  `STALKER_international_decisions.txt`; `99_STALKER_international_effects.txt`.
- **2022 arc (30–39):** `STALKER_2022.txt`, `STALKER_aftermath.txt`; loc `_2022_`, `_aftermath_`;
  `99_STALKER_2022_effects.txt`, `_global_`, `_aftermath_`.
- **Regional flavor (40–49):** `STALKER_regional.txt`; loc `_regional_`;
  `99_STALKER_regional_effects.txt`.
- **Economy (50–59):** `STALKER_economy.txt`; loc `_economy_`; `STALKER_global_decisions.txt`;
  `99_STALKER_economy_effects.txt`; the artifact MIO.
- **Belarus (60–69):** `STALKER_belarus.txt`; loc `_belarus_`; `STALKER_belarus_decisions.txt`;
  `99_STALKER_belarus_effects.txt`.
- **Monolith (70–79):** `STALKER_monolith.txt`; loc `_monolith_`;
  `STALKER_monolith_decisions.txt`; society effects in core.
- **MDST (80–89):** `STALKER_mdst.txt`; loc `_mdst_`; `STALKER_mdst_decisions.txt`;
  `99_STALKER_mdst_effects.txt`.
- **Mutants (90–99):** `STALKER_mutants.txt`; loc `_mutants_`; `STALKER_mutant_decisions.txt`;
  `99_STALKER_mutant_effects.txt`.
- **Crossover (100–109):** `STALKER_crossover.txt`; loc `_crossover_`;
  `99_STALKER_meme_effects.txt`.
- **Footprint (110–119):** `STALKER_footprint.txt`; loc `_footprint_`;
  `99_STALKER_footprint_effects.txt`.
- **Factions (120–129):** `STALKER_factions.txt`; loc `_factions_`;
  `99_STALKER_faction_effects.txt`.
- **World reaction (130–139):** `STALKER_world.txt`; loc `_world_`;
  `99_STALKER_world_effects.txt`.
- **Foreign intelligence (140–149):** `STALKER_intel.txt`; loc `_intel_`;
  `99_STALKER_intel_effects.txt`.
- **Faction Wars (150–159):** `STALKER_faction_wars.txt`; loc `_faction_wars_`;
  `99_STALKER_faction_wars_effects.txt`.

Localisation file names are `MD_STALKER_<subsystem>_l_english.yml`.

The next free block is 160–169. Decision categories are one file each in
`common/decisions/categories/00_STALKER_*_category.txt`. Dynamic modifiers are one file per
subsystem in `common/dynamic_modifiers/00_STALKER_*dynamic_modifiers.txt`.

## Hooks into shared files

These are the only places the scenario touches files other MD content owns. Keep them to one line
where possible; they are what an upstream port has to carry.

- `common/on_actions/MD_on_actions.txt`: `STALKER_monthly_pulse = yes` in the monthly block.
- `common/scripted_effects/00_yearly_effects.txt`: the 2008 Zone activation and the 2022 dispatch
  of STALKER.34 and STALKER.35.
- `common/scripted_effects/00_startup_effects.txt`: the artifact MIO in MD's starting MIO sizing.
- Targeted Operations: `STALKER_check_top_zone_crisis` calls in the TOP proposal and resolution
  effects, and `[STALKER_top_package_zone_crisis]` in the package-page localisation. See
  [Targeted Operations](targeted-operations.md).
- `localisation/english/MD_game_rules_l_english.yml`: the three STALKER rules.

## Scripting traps found at runtime

- `on_startup` runs with no scope. Wrap scripted effects in `random_country = { }`, or they error
  with "provided: None" and do nothing. This kept the whole scenario from starting until 2026-09-27.
- `clamp_variable` on an unset variable is a runtime error. Initialize any variable that a shared
  clamp such as `STALKER_clamp_zone_society` touches, even when its value is 0.
