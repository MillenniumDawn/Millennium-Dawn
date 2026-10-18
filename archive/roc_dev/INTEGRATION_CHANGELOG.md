# RoC-development integration changelog

Branch: `integration/obt-roc-unified` (local; not pushed or merged). Source: AUG's `upstream/RoC-development` at `ceb1a0c1f5`, archived byte-exact in this folder.

The unified build has one Taiwan focus tree (`common/national_focus/05_taiwan.txt`, id `taiwan_focus`) with 368 focuses: Operation Blue Tiger's 310 plus 58 of AUG's, which keep their original IDs. AUG's other 34 focus IDs are integrated into OBT focuses or decisions that already cover the same event. All 92 are listed in `ROC_DEV_MAPPING.md`. AUG's `taiwan.txt` is not loaded.

| Classification           | Focuses | Result                                                                                                                             |
| ------------------------ | ------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| Integrate into OBT focus | 36      | 34 rewards folded into OBT focuses or decisions; 2 kept as follow-on focuses in OBT lines (205th Arsenal, Sustainable Development) |
| Rework (alt-history)     | 27      | Kept with their IDs, gated and re-routed to fit OBT's systems                                                                      |
| Retain unchanged         | 17      | Kept with their IDs and rewards                                                                                                    |
| Archive / optional       | 12      | Kept as written, hidden unless an off-by-default game rule is on                                                                   |

## 1. Files

New files (all AUG content, separate from OBT's files so they can be reviewed on their own):

| File                                                            | Contents                                                                                                                                                                                           |
| --------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `common/ideas/99_TAI_roc_dev_ideas.txt`                         | AUG's 29 national spirits                                                                                                                                                                          |
| `common/decisions/ROC_dev_decisions.txt`                        | Economic Policy decisions, the three regional theaters and outlying-island militia (in the OBT reserve tab), the Seventh Fleet invitation (in the Cross-Strait tab), Launch Project National Glory |
| `common/decisions/categories/99_ROC_dev_categories.txt`         | Economic Policy and Project National Glory categories                                                                                                                                              |
| `events/ROC_dev_events.txt`                                     | AUG's events, namespace `roc_dev`                                                                                                                                                                  |
| `common/opinion_modifiers/99_TAI_roc_dev_opinion_modifiers.txt` | `tai_92`, `tai_ait`, `tai_resist`                                                                                                                                                                  |
| `common/game_rules/99_ROC_dev_game_rules.txt`                   | Southern Expansion and NATO Request rules (both off by default)                                                                                                                                    |
| `common/scripted_triggers/99_ROC_dev_scripted_triggers.txt`     | Rule checks for those two paths                                                                                                                                                                    |
| `common/on_actions/99_ROC_dev_on_actions.txt`                   | Sets the AI path flags for AUG's AI behaviour options                                                                                                                                              |
| `localisation/english/MD_ROC_dev_l_english.yml`                 | All text for the above and for AUG's 58 focuses                                                                                                                                                    |
| `gfx/leaders/TAI/John_Chiang.dds`                               | AUG's portrait, byte-identical to `ceb1a0c1f5`                                                                                                                                                     |

Changed files:

| File                                                            | Change                                                                                                                                                               |
| --------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `common/national_focus/05_taiwan.txt`                           | Regenerated: AUG's 58 focuses, three new branches (Island Society, Southern Policy, Project National Glory) in the bottom band, integrated rewards on 21 OBT focuses |
| `common/game_rules/00_game_rules.txt`                           | `TAI_ai_behavior` gains AUG's options Project National Glory, Unification Channel and Road to Separation                                                             |
| `common/scripted_triggers/99_TAI_scripted_triggers.txt`         | `TAI_ai_alt_path` counts the three new AI flags, so historical AI weights switch off when one is chosen                                                              |
| `common/decisions/OBT_defense_decisions.txt`                    | Hold the Han Kuang Exercise gains AUG's +5% war support                                                                                                              |
| `common/scripted_triggers/99_OBT_reserve_scripted_triggers.txt` | After Mobilized Reserve Troops (National Glory), reserve mobilization no longer needs a Strait crisis                                                                |
| `common/scripted_effects/99_OBT_reserve_scripted_effects.txt`   | Demobilization clears the theater and militia flags                                                                                                                  |
| `events/Taiwan_Reclamation.txt`                                 | The Republic Restored (`reclamation.20`) fires `roc_dev.19`                                                                                                          |
| `events/Taiwan_Blue_Tiger.txt`                                  | U.S. AI is more likely to defend Taiwan after AUG's Strait-policy event (`usa_intervene_taiwan`)                                                                     |
| `history/countries/TAI - Taiwan.txt`                            | AUG's `TAI_921_earthquake` starting spirit                                                                                                                           |
| `Changelog.txt`                                                 | Focus count and the three new branches                                                                                                                               |

All OBT edits are made in the generators (`spec.py`, `gen.py`, `events_spec.py`, `m5/rec_gen.py`, `m9/build9.py`, `m10/mob10.py`) and regenerated; each regenerated file differs from the previous build only by the change listed.

## 2. Focus tree

New branches:

- **Island Society** (10 focuses): 921 earthquake reconstruction as the root, then a labour line (Labour Reform, the 2016 rest-day law, 2017 pension reform, Act 748) and a welfare line (Social Welfare Reform, Long-Term Care, Sustainable Development, Affordable Housing, Welfare State of Asia). Date gates follow the real laws.
- **Southern Policy** (16 focuses): opens after OBT's Go South. Road to Peace leads to unofficial relations, a regional defence treaty and military access. Road to War and the ten conquest and ultimatum focuses are hidden unless the Southern Expansion rule is on.
- **Project National Glory** (15 focuses): needs the Return to the Mainland rule and a communist China, and excludes the democratic capstones (KMT, PFP, DPP, TSU and Green Party capstones and Democracy in the Political DNA). The exclusion is written as a completed-focus check on both sides (see Layout). Launch Our Plan opens the National Glory decision, whose war lets OBT's reclamation decisions take over.

Focuses added to OBT branches: Develop Rural Areas, Kaohsiung refinery, Taipei industrial park and Maanshan expansion (Silicon Island); 205th Arsenal, warship programme and shipbuilding (National Army); Wartime Industrial Mobilization (Operation Blue Tiger); the five-focus Red Infiltration path (Across the Strait); the Second Republic constitution (Kuomintang); the Republic of Taiwan (DPP, after the DPP or TSU capstone); the U.S. defence announcement and the NATO request (Pacific Lifeline).

Rewards folded into OBT focuses:

| OBT focus                                 | Added from AUG                                                                                |
| ----------------------------------------- | --------------------------------------------------------------------------------------------- |
| The Silicon Island                        | Industry tech bonus; opens Economic Policy                                                    |
| Found the Central Taiwan Science Park     | AUG's factory grant in Hsinchu and Taichung replaces two random factories                     |
| Finish the High-Speed Rail                | `TAI_highspeed_train`; infrastructure in the six corridor states replaces two random upgrades |
| Renewable Energy Act                      | `TAI_renewable_energy`                                                                        |
| Upgrade the Indigenous Fighter            | `fighter_production_bonus`; air experience 40                                                 |
| The Manpower Question                     | `TAI_national_mob_law`                                                                        |
| Reserve Readiness Audit                   | Army experience 60                                                                            |
| Reserve Reform                            | `TAI_afrc`; Reserve Readiness +15                                                             |
| Territorial Defense Brigades              | `TAI_expand_soldiers`                                                                         |
| Go South                                  | Trade-agreement opinion with five Southeast Asian states                                      |
| Uphold the 1992 Consensus                 | `tai_92` opinion                                                                              |
| The Status Quo Dividend                   | KMT popularity +3                                                                             |
| The National Security Council Coordinates | Stability and war support +5%                                                                 |
| Democracy in the Political DNA            | `TAI_post_kmt`                                                                                |
| Foreign Influence Transparency            | `TAI_aia` if completed after 2019                                                             |
| A Taiwan-Centered State                   | `TAI_taiwan_indep`; `tai_resist` opinion; tension +3                                          |
| A Pan-Green Majority                      | DPP popularity +5                                                                             |
| A New Generation                          | `TAI_purge_kmt`                                                                               |
| A New Constitution                        | DPP popularity +5                                                                             |
| Consult Washington                        | Friendship opinion with the U.S.                                                              |
| Friends on Capitol Hill                   | `tai_ait` opinion; fires `roc_dev.23`                                                         |

### Layout

The tree is 88 columns by 36 rows (down from 91 by 42 in the first unified build), with three columns between branches:

| Row | Branches, left to right                                                                                                                                               |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Pacific Lifeline, 2000 Succession, Silicon Island                                                                                                                     |
| 2   | Kuomintang, People First Party, DPP, Taiwan Solidarity Union, Green Party                                                                                             |
| 3   | Across the Strait (with Southern Policy and Project National Glory below it), Operation Blue Tiger, National Army, Democratic Fortress (with Island Society below it) |

- Southern Policy sits under Across the Strait, starting below Go South, in the Pacific Lifeline column. Project National Glory sits beside it, below the Kuomintang and the cross-Strait branch. Island Society sits under Democratic Fortress with the domestic branches.
- Operation Blue Tiger moved under Pacific Lifeline, which it depends on.
- Lines between branches are 24% shorter in total, the longest falls from 95 to 70 cells, and line crossings fall from 149 to 129.
- Project National Glory's first focus no longer uses `mutually_exclusive` with the six democratic capstones, which drew six lines across the whole tree. Each side instead checks `NOT = { has_completed_focus = ... }` for the other. Only one focus can be in progress at a time and none of these focuses is completed by an effect, so players and the AI are blocked from exactly the same combinations, and no `ai_will_do` changed.
- Only whole branches moved: every focus keeps its position relative to its branch's first focus, and no ID, prerequisite, reward or date changed.
- The continuous-focus panel moved to the empty area under Operation Blue Tiger.

## 3. Other content

**National spirits (29)**: all kept with their IDs. Category tags (`allowed` blocks, which do nothing for country spirits) were removed. Fixes: `TAI_cpc` used a research category that does not exist (`synth_resources`, now `CAT_fuel_refining`); `TAI_renewable_energy` used the LGBT picture; `TAI_taiwan_indep` and the pension spirit used pictures that do not exist; `TAI_walfare_state_goal` had none. `TAI_gastapo` keeps its ID and is shown as Taiwan Garrison Command.

**Decisions**:

| AUG decision                                                   | Result                                                                                                                                                                          |
| -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Consumer vouchers, construction policy                         | Kept                                                                                                                                                                            |
| Industrial development plan, self-made weapons                 | Kept; they were free and repeatable, so they now cost 75 political power and 1 billion                                                                                          |
| Han Kuang exercise propaganda                                  | Merged into OBT's Hold the Han Kuang Exercise (+5% war support)                                                                                                                 |
| Set up reserve units, first-level mobilization, demobilization | Replaced by the OBT reserve system (start the reserve programme, partial mobilization, demobilize). AUG's three division templates are not created, so reserves are not doubled |
| Northern, central and southern second-level mobilization       | Kept under their IDs in the OBT reserve tab, during general mobilization; 2, 2 and 3 reserve brigades                                                                           |
| Total mobilization                                             | Kept under its ID: militia on Kinmen, Matsu, Penghu and Pratas once all theaters are mobilized in a war                                                                         |
| Launch Project National Glory                                  | Kept with its templates and units; needs the Return to the Mainland rule; declares war through `war_with_on_complete`                                                           |

**Events**: renumbered from `taiwan.N` to `roc_dev.N`, because `taiwan.18` is used by current Millennium Dawn and was defined twice in AUG's file.

| Old              | New               | Changes                                                                                                                                                                                                              |
| ---------------- | ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| taiwan.18        | roc_dev.18        | Fired by Launch Our Plan when the resistance flags are met (AUG's check had no effect inside it). Rebels now fight as democrats instead of the government's own ideology. New option: lift martial law and negotiate |
| taiwan.19        | roc_dev.19        | Fired by The Republic Restored. The missing `partially_recognized_state` swap is replaced by removing `TAI_legacy_of_1949` and adding the Security Council seat                                                      |
| taiwan.20        | roc_dev.20        | Opens OBT's talks with Beijing (`blue_tiger.40`), which end in a referendum. The original options used a China focus that does not exist and an instant annexation                                                   |
| taiwan.21        | roc_dev.21        | The missing `china.61` reaction is replaced by Cross-Strait Tension +8 and U.S. support +5                                                                                                                           |
| taiwan.22        | roc_dev.22        | Unchanged                                                                                                                                                                                                            |
| taiwan.23        | roc_dev.23        | Also U.S. support +5; the `usa_intervene_taiwan` flag now matters to the U.S. AI                                                                                                                                     |
| taiwan.24 to .28 | roc_dev.24 to .28 | Unchanged except for existence checks; one duplicate loc key fixed                                                                                                                                                   |

The six `taiwan_news` events in AUG's file already exist in Millennium Dawn; AUG's branch only changed their whitespace.

**Game rules**: AUG's `ROC_ai_behavior` options are merged into OBT's `TAI_ai_behavior`: Status Quo is OBT's Historical, Default is No Path, Random is Random Path, and Project National Glory, Unification Channel and Road to Separation are added. Southern Expansion and NATO Request are new rules with Disabled (default), Player Only and Allowed.

## 4. Reference fixes

| Problem in AUG's branch                                                                                     | Fix                                                          |
| ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| `TAI_sar_exec` flag checked by most focuses, set nowhere                                                    | Check removed (it was always true)                           |
| `declare_independence_taiwan` decision no longer exists                                                     | Republic of Taiwan fires Washington Warns and raises tension |
| `legacy_of_1949`, `Non_State_Actor`, `fate_of_mongolian_area`, `partially_recognized_state` no longer exist | Pointed to `TAI_legacy_of_1949` or removed                   |
| `china.59`, `china.60`, `china.61` events do not exist                                                      | Replaced by Cross-Strait Tension and Washington Warns        |
| `CHI_Establish_Taiwan_SAR`, `CHI_End_of_ROC` focuses do not exist                                           | Replaced by OBT's staged talks                               |
| `TAI_ait` opinion modifier (defined as `tai_ait`)                                                           | Fixed                                                        |
| `set_state_controller = 925` in country scope; state 925 is Ilemi                                           | Not ported (held for AUG)                                    |
| Civil-war capitals not among the rebel states (592 is Xinjiang)                                             | Capitals moved to a state in each list                       |
| Placeholder `add_manpower = 114514`                                                                         | 50,000 (held for AUG to confirm)                             |
| `SP_Arty_Battery` unit does not exist                                                                       | Only in the archived templates, not ported                   |
| `complete_national_focus` on two retired mobilization focuses                                               | Replaced by their OBT rewards                                |
| Status Quo raised party index 5 (anarchist communism) with a conservatism tooltip                           | Conservatism (index 1)                                       |
| Log lines naming the wrong focus                                                                            | Regenerated                                                  |

## 5. Pressure Is Not Control

No path ends in an automatic annexation, capitulation or war. The Red Infiltration path ends in OBT's staged talks and referendum. Project National Glory and the Southern Expansion wars are deliberate player actions behind rules that are off for the AI by default. The conquest focuses create wargoals but do not declare war. AI Taiwan takes AUG's alternate-history paths only when the matching AI behaviour option is chosen.

## 6. Balance changes for AUG to review

| Item                                                                   | AUG                                       | Unified build                    | Why                                                                 |
| ---------------------------------------------------------------------- | ----------------------------------------- | -------------------------------- | ------------------------------------------------------------------- |
| Political power maluses on four focuses                                | -25 to -100                               | Removed                          | Millennium Dawn style treats focus time as the cost                 |
| High-speed rail completion                                             | 50 billion, +2 infrastructure in 6 states | 15 billion, +1                   | Real cost about US$14.5 billion; replaces OBT's two random upgrades |
| Strengthen National Government                                         | +10% stability and war support            | +5% each on the NSC focus        | OBT political focuses give 2 to 5%                                  |
| Taiwanese political power, new constitution                            | +20% DPP popularity                       | +5%                              | OBT party effects are 1 to 3%                                       |
| Clean up KMT party assets spirit                                       | -0.5% stability per week                  | -0.1%                            | -26% a year was unplayable                                          |
| Free repeatable factory decisions                                      | Free                                      | 75 political power and 1 billion | A free factory every 180 days                                       |
| Reserve quota                                                          | +50,000 manpower                          | Removed                          | Would double the OBT reserves                                       |
| Phase I and III of the rail, threat from the mainland, resist invasion | Political power                           | Not duplicated                   | Covered by the OBT focus                                            |

## 7. Not ported (preserved in the archive)

- AUG's edit to the 2000 election event (`taiwan.3`): it limited the event to before 18 January 2000, which would stop it firing at the March election, and created a Chen Shui-bian leader that OBT's election handling already creates.
- Cosmetic edits to `taiwan.13` and `taiwan.17` (option order and a removed trigger).
- The new-constitution civil war, which used state IDs from an older map (Xinjiang, Tribal Areas, Chugoku) and created a Ma Ying-jeou leader.
- The National Glory beachhead (`set_state_controller = 925`).
- AUG's three reserve division templates.
- The original Republic of Taiwan focus description, which quoted song lyrics; it was rewritten.

## 8. Validation

Millennium Dawn's validators were run on a copy of the integration branch before and after the change: focus tree, ideas, decisions, events, localisation, common mistakes, modifiers, variables, style, history, unused scripted, scripted parameters, set variables, on-actions, dynamic-modifier guards, OOB units, GFX references, building guards, cosmetic tags, party loc, AI path rules, bonus names, DLC guards, tech categories, characters, simplifications and scripted localisation. All match the pre-integration baseline. The only difference is four standardization warnings for the new files, the same formatting warning OBT's generated files already carry.

Not yet done: in-game testing of the new layout, and AI observation runs with each AI behaviour option.

## 9. Decisions for TheGeneral and AUG

1. Confirm the layout: Southern Policy and Project National Glory under Across the Strait, Island Society under Democratic Fortress.
2. Confirm that the Southern Expansion conquest and the NATO request stay off by default behind game rules.
3. AUG: the intended state for the National Glory beachhead (old ID 925) and the new-constitution civil war states.
4. AUG: the student call-up figure (now 50,000) and the balance changes in section 6.
5. Whether to keep AUG's Economic Policy decisions available from the start (they open with the Silicon Island root).
6. When to open the pull request into RoC-development for AUG's review.
