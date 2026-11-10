# STALKER Scenario

The opt-in STALKER scenario (MillenniumDawn/Millennium-Dawn#4791) keeps its original subsystem
event-ID allocations while grouping related source files into larger gameplay modules.
This reduces file proliferation without coupling the scenario to Targeted Operations.

## Rules

- **Keep related content together.** Add events, decisions, effects and localisation to the
  existing grouped files below. Do not add a separate file for each small feature or story.
  A new event-ID block can still be reserved for an independent subsystem. The
  `/scenario-subsystem` generator creates scaffolding, not the required final source layout.
- **Event IDs.** Keep the established subsystem ID blocks; never reuse or renumber an ID.
- **Localisation.** Put keys in the corresponding grouped `MD_STALKER*_l_english.yml` file.
  Keep one UTF-8 BOM and one `l_english:` header per file; never duplicate a localisation key.
- **Monthly work.** Add calls to `STALKER_monthly_pulse` in
  `common/scripted_effects/99_STALKER_scripted_effects.txt`. Do not add separate pulses to
  `MD_on_actions.txt`.
- **Changelog.** Each STALKER PR adds one BLUF line to `Changelog.txt`, as `AGENTS.md` requires.
- **Target `main`.** This upstream port has no Targeted Operations dependency. Incorporate the
  latest upstream `main` and merge STALKER PRs one at a time.

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
- Dated history on Zone 1 lives in the Zone Legend subsystem. 2006 is the second disaster and does not start management. Management still begins in 2008. In 2011 Clear Sky assaults the plant. Stopping Strelok sets `STALKER_strelok_turned_back` and the 2012 raid does not happen. The canon assault sets `STALKER_strelok_marked`. Helping him through sets `STALKER_strelok_remembers`. Scar survives all three. Operation Fairway follows the 2012 result by about four months, and a route of 1 can hold Pripyat. SIRCAA, under Dalin, and Colonel Korshunov's Ward can be chartered in 2018. From December 2010 the random Clear Sky collapse does not fire. The X-Lab option that disables the Brain Scorcher sets none of these flags. Names used here, checked against the S.T.A.L.K.E.R. Wiki: Lebedev, Scar, Major Alexander Degtyarev, Colonel Kovalsky, Operation Fairway, Dalin.
- Faction Wars and Tearlings come from GSC's pre-launch Discord event in the official
  S.T.A.L.K.E.R. server (announcements of 9, 11 and 17 November 2024). SIRCAA asked every
  faction to bring in Tearlings, common crystals long logged as worthless. The Free Stalkers
  delivered the most, 331 of 1,232, and every faction got a share of the rewards.
- Reference-map Zones follow the #4791 reference image, which shows 27 outbreak markers besides
  Chornobyl. Zones 5 (New Mexico), 12 (Paraguayan Chaco), 15 (Wielkopolska) and 27 (Lake Mungo)
  have no marker on it and are this scenario's own additions. Zone 31 (Aksai Chin) was added
  after a placement check found its marker unassigned. The map is a guideline, not a cap: add
  Zones where lore or gameplay calls for them, and note each addition in the placement table. The
  Randomized rule option registers each reference Zone with a 60% chance and swaps in the recorded
  alternative sites (Zone IDs 32 to 37) at random.
- Project X and MDST are canon (STALKER 2). Project X was the state Noosphere program the
  Regulatory Board funded after 1991. Its scientists defied the Board in 2006 and created the
  Zone by accident; the Board shut Project X down and the scientists carried on as MDST, the
  Ministry of Defense and Secret Technologies. MDST created the Monolith and the S.T.A.L.K.E.R.
  agents, keeps the X-Network running and serves the C-Consciousness. MDST is not SIRCAA, the
  Ward or Malachite. Its reach into state institutions (MDST penetration) is this scenario's
  own mechanic.

## Consolidated source layout

The event ID blocks below are unchanged. Each filename is relative to its normal engine directory:
`events/`, `common/decisions/`, `common/scripted_effects/` or `localisation/english/`.

| Module | Event IDs | Event file | Related gameplay sources |
| --- | --- | --- | --- |
| Core Zone, X-Labs, artifact market, Antarctic study | 1–19, 50–59, 190–199 | `STALKER.txt` | `STALKER_decisions.txt`, `STALKER_global_decisions.txt`, `99_STALKER_scripted_effects.txt`, `99_STALKER_society_effects.txt`, `99_STALKER_world_effects.txt`, `MD_STALKER_l_english.yml` |
| International, Belarus, Zone footprints, foreign intelligence and world reaction | 20–29, 60–69, 110–119, 130–149 | `STALKER_world.txt` | `STALKER_decisions.txt`, `99_STALKER_world_effects.txt`, `MD_STALKER_world_l_english.yml` |
| 2022 battle and aftermath | 30–39 | `STALKER_2022.txt` | `99_STALKER_legend_effects.txt`, `MD_STALKER_2022_l_english.yml` |
| Regional stories | 40–49 | `STALKER_regional.txt` | `99_STALKER_world_effects.txt`, `MD_STALKER_world_l_english.yml` |
| Monolith, mutants, MDST, factions and Tearling faction wars | 70–99, 120–129, 150–159 | `STALKER_factions.txt` | `STALKER_decisions.txt`, `99_STALKER_faction_effects.txt`, `MD_STALKER_factions_l_english.yml` (faction names and wars), `MD_STALKER_l_english.yml` (remaining keys) |
| Optional crossover | 100–109 | `STALKER_crossover.txt` | `99_STALKER_faction_effects.txt`, `MD_STALKER_crossover_l_english.yml` |
| Strelok and dated Zone Legend | 160–181 | `STALKER_legend.txt` | `99_STALKER_legend_effects.txt`, `MD_STALKER_legend_l_english.yml` |
| Field campaigns | 200–209 | `STALKER_field_campaigns.txt` | `STALKER_field_campaigns_decisions.txt`, `99_STALKER_legend_effects.txt`, `MD_STALKER_legend_l_english.yml` |

The remaining standalone scripted-effect modules are
`99_STALKER_zone_placements.txt` (Zone registry layout) and
`99_STALKER_society_effects.txt` (society, policy and artifact economy).
All STALKER event dispatches share the `STALKER` namespace.
`STALKER_decisions.txt` contains the consolidated Zone-management decisions as well as the
separate MDST decision category. Their existing IDs and effects are unchanged.
The UI files `01_STALKER_zone_overview_gui.txt` and `interface/STALKER_zone_overview.gui`,
the scripted triggers, and the game rules remain separate.

### Gameplay and timeline invariants

- **Core:** Management activates in 2008, not in the 2006 disaster. An AI holder whose
  containment is under 30 (or whose perimeter is breached) and who cannot afford 50 PP
  can instead use treasury-funded reinforcement, subject to the 180-day
  `STALKER_zone_reinforced` cooldown.
- **Zone growth:** Zone anchors stay fixed as footprints spread, recede, drift or split.
  Reference Zone splits use the original Zone ID plus 100.
- **Faction wars:** The official pre-launch Tearling contest influences the faction events.
  Crossover events are human-player only; Alice's Lake Mungo contact and delayed return
  record the answered option in `global.STALKER_alice_choice`.
- **Legend:** The 2011 Clear Sky routes and the 2012 Strelok outcome feed Fairway and
  Strider. The monthly legend pulse redelivers delayed or controller-transferred
  choices. Fairway, Strider, Clear Sky and SIRCAA retain their separate relay flags.
- **Antarctica:** The polar artifact study spends five artifacts and requires an operational
  Radiation Laboratory. It grants its 180-day research modifier, but observers seize
  samples, and a failed laboratory ends the study. `STALKER_polar_study_cut_short`
  blocks the scheduled completion event.

Events 182–189 remain available in the Legend block. The next free block is 210–219.
Decision-category definitions remain under `common/decisions/categories/`; dynamic
modifiers remain in `common/dynamic_modifiers/00_STALKER_dynamic_modifiers.txt`.

## Hooks into shared files

These are the only places the scenario touches files other MD content owns. Keep them to one line
where possible; they are what an upstream port has to carry.

- `common/on_actions/MD_on_actions.txt`: `STALKER_monthly_pulse = yes` in the monthly block.
- `common/scripted_effects/00_yearly_effects.txt`: the 2006 dispatch of STALKER.170, the 2008
  Zone activation, the 2011 dispatch of STALKER.171 and STALKER.172, the 2012 dispatch of
  STALKER.160, the 2018 dispatch of STALKER.176, and the 2022 dispatch of STALKER.34 and STALKER.35.
- `common/scripted_effects/00_startup_effects.txt`: the artifact MIO in MD's starting MIO sizing.
- `localisation/english/MD_game_rules_l_english.yml`: the three STALKER rules.
- `events/MD_Antarctica.txt`: the observer report event's block that seizes a polar artifact study
  and adds the Treaty penalty only when the station shows no other violation.

## Scripting traps found at runtime

- `on_startup` runs with no scope. Wrap scripted effects in `random_country = { }`, or they error
  with "provided: None" and do nothing. This kept the whole scenario from starting until 2026-09-27.
- `clamp_variable` on an unset variable is a runtime error. Initialize any variable that a shared
  clamp such as `STALKER_clamp_zone_society` touches, even when its value is 0.

## Original Zone field campaigns

Field Campaigns owns IDs 200-209. The Yantar, Army Warehouses and Red Forest dossiers each use an intake,
first report and final choice. They run in that order, after the original Zone opens and its policy is answered.
All phases, 60-day assignment flags, outcomes and recurring assignment cooldowns live on state 698. Campaign
steps are 0 intake, 1 investigation available, 2 investigating, 3 first report, 4 recovery available,
5 recovering and 6 final report; case 4 means all dossiers are closed. Monthly delivery binds each event to
the original Zone and its current controller. A transferred or lost report retries without changing the result.

An investigation costs 25 PP; recovery costs 50 PP. Escorting scientific supplies or patrolling the road costs
25 PP and takes 60 days, with a 180-day cooldown after completion. These share the field-assignment slot and
grant only their 5-point effects, never the campaign's research reward. Abandoning a dossier strengthens bandits.
Road patrols support both factions by 5 after an accord, or strengthen the backed faction by 5 while weakening
its rival by 5. When the existing 2022 battle begins, unfinished dossiers close unprepared and their campaign
timer stops. Completed history and recurring management assignments remain available.
Shared Yantar findings add 5 scientists when the existing 2018 SIRCAA choice resolves. A secured road offsets
5 containment loss in the 2022 battle once. Preserved Red Forest evidence discounts one MDST purge for the Zone
controller from 75 to 50 PP; its custom cost and affordability use the same site-owned condition.

Yantar, the Army Warehouses and the Red Forest are narrative locations, not new map states. These are original
government missions using existing factions. No existing dated route or ending is selected by this subsystem.
Native acceptance: save/reload during both assignments, transfer during every report, inactive Zone,
repeat pulses and options, recurring rewards, all 2018/2022 branches, and one-use purge cost.
