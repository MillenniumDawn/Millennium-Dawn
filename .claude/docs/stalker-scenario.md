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
- **Changelog.** STALKER feature PRs into `feature/stalker-global-zones-4791` do not edit
  `Changelog.txt`. The scenario keeps one STALKER entry, rewritten when it lands on `main` and
  again when it is ported upstream. This is the one exception to the one-line-per-PR rule in
  `AGENTS.md`.
- **One integration branch.** Feature PRs target `feature/stalker-global-zones-4791`. Do not push
  to it directly. Merge PRs one at a time, and merge the latest base into each one first.

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

Localisation file names are `MD_STALKER_<subsystem>_l_english.yml`.

The next free block is 120–129. Decision categories are one file each in
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
