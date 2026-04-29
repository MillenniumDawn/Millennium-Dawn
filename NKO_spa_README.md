# Supreme People's Assembly (SPA) — Millennium Dawn submod

A productivity-mandate mechanic for North Korea (DPRK). Every four months the
Supreme People's Assembly convenes; the player picks two of eight resolutions,
each suspending one chronic dysfunction for 120 days and applying a productivity
bonus on top. The other six domains continue to drag the country down. This is
the central tension of the mechanic — every session is a forced trade-off.

## Detection summary

| Field                       | Value                                                |
| --------------------------- | ---------------------------------------------------- |
| Detected country tag        | `NKO`                                                |
| Source file                 | `history/countries/NKO - North Korea.txt`            |
| MD branch assumed           | `NorthKoreanAdditions2026` (current at 2026-04-27)   |
| Conflicts with existing NKO | None — distinct from united_front / Arduous_March / black_market / Power_struggle / Navy / rus_friend categories |

## Files installed

```
common/ideas/NKO_spa_ideas.txt                                # 17 ideas: 1 umbrella + 8 debuffs + 8 timed bonuses
common/decisions/NKO_spa_decisions.txt                        # 8 resolution decisions + Pass-Resolutions, hosted in NKO_Arduous_March
common/scripted_effects/NKO_spa_effects.txt                   # init / open / close / pass-X / force-pick / suppress
common/scripted_triggers/NKO_spa_triggers.txt                 # mechanic_enabled, session_open, affordability, locks
common/scripted_localisation/NKO_spa_scripted_localisation.txt# resolves [NKO_spa_*_chip_frame] for the .gui
common/scripted_guis/NKO_spa_gui.txt                          # NKO_spa_gui (decision_category context)
common/on_actions/NKO_spa_on_actions.txt                      # on_startup, on_monthly_NKO, on_civil_war_started
events/NKO_spa.txt                                            # NKO_spa.0 / .1 / .2 / .5 / .6
interface/NKO_spa.gfx                                         # all GFX entries (verified textures, ready to swap)
interface/NKO_spa_window.gui                                  # NKO_spa_window containerWindowType
localisation/english/MD_NKO_spa_l_english.yml                 # English loc, UTF-8 with BOM
NKO_spa_README.md                                             # this file
```

## Implementation pattern (and why)

**Decision category + scripted_gui banner — consolidated under `NKO_Arduous_March`.**
Rather than spawn a new SPA-specific decision category, the 8 resolutions live
inside the existing `NKO_Arduous_March` category and the SPA banner attaches as
that category's scripted_gui. This mirrors how `NKO_united_front_department` and
`NKO_black_market` work in MD today, and keeps the political tab from sprouting
yet another NKO header.

**Two minimal edits to the existing MD categories file** (`common/decisions/categories/north_korea_decision_categories.txt`):
- Added `scripted_gui = NKO_spa_gui` to the `NKO_Arduous_March` block.
- Expanded its `visible` block to `OR = { has_dynamic_modifier = arduous_march_modifiers; has_idea = NKO_spa_umbrella }` so the category stays visible after the Arduous March modifier is removed by the focus tree (otherwise the SPA would lose its entry point mid-game).

The 8 march-recovery decisions already in `NKO_Arduous_March` continue to work
unchanged — they have their own visibility triggers, so they hide cleanly once
their conditions stop matching, leaving the SPA resolutions as the active set
in the late game.

**Why ideas (not dynamic_modifiers) for the 8 debuffs/bonuses.**
- `add_timed_idea` auto-removes after duration — no manual cleanup needed
- The bonus idea's `on_remove` hook re-adds the paired standing debuff
  automatically when the idea expires, regardless of cause (natural expiry,
  forced removal, civil-war suppression). One mechanism, no race conditions.
- Ideas integrate with the country idea slot — gives the umbrella mechanic a
  visible UI presence per the spec.
- Modifier expiry is HOI4-native, so no on_weekly polling overhead.

**Why decision PP cost field instead of `subtract_from_variable = political_power`.**
HOI4's `cost = N` field is the standard, plays nicely with the affordability
greying-out behavior, and lets MD's existing PP HUD show the deduction
animation.

**Why one umbrella idea + 8 standing debuffs (not one big merged debuff).**
- Each debuff toggles independently — merging them would force flag-juggling
  inside a single dynamic_modifier
- Tooltip clarity — players see exactly which 6 domains are penalized right now
- Civil-war cleanup is uniform (same `remove_ideas` pattern for all)

## How to test

In-game debug commands (HOI4 dev console — `\` to open):

```
tag NKO              # take control of North Korea
debug                 # toggle debug mode (logs SPA events to game.log)
pp 1000               # grant Political Power (resolutions cost 40-75 PP each)
add_treasury 10       # MD-specific; grants treasury (resolutions cost 0.3-0.75)
                      # OR use the cheat console: cheat_money 10
add_party_popularity communism 0.5
event NKO_spa.0       # manually fire the inaugural session
event NKO_spa.1       # manually open a regular session
event NKO_spa.5       # force the cabinet-acts-in-your-absence fallback
event NKO_spa.6       # manually trigger collapse cleanup
days 120              # advance 120 days to verify bonuses expire and debuffs return
days 30               # advance one month — drives the inter-session timer
```

Acceptance walkthrough:

1. Start a new game as NKO at any MD start date (2000 / 2017 / current).
   - Verify all 8 standing debuff ideas appear in the country idea bar
     (Industrial Stagnation, Production Line Decay, Hollow Force, Resource
     Hoarding, Ideological Drift, Subsistence Farming, Diplomatic Isolation,
     Construction Bottleneck) plus the Supreme People's Assembly umbrella.
2. Wait until day 1 — `NKO_spa.0` (inaugural) fires.
   - Click "Begin the session". The SPA decision category banner becomes visible.
3. Open the SPA category. 8 resolution cards visible. Pick two.
   - For each pick: PP and treasury debited, the matching standing debuff
     idea is removed, the matching bonus idea (`add_timed_idea` with 120-day
     timer) appears.
4. After 120 days: bonuses expire, paired debuffs return automatically (via
   `on_remove`).
5. Roughly 120 days from session open, `NKO_spa.1` fires for the next session.
6. Force-pick fallback: open a session, `days 119`, do nothing, `days 2`.
   `NKO_spa.5` fires; cabinet auto-picks the two cheapest affordable resolutions.
7. Civil war: trigger via `civilwar communism NKO`. The mechanic suppresses —
   all SPA ideas removed, no further sessions fire.

## Known TODOs / verification list

Every item below is annotated with `# TODO verify against MD branch` in the
relevant file. None of them block first-light functionality, but should be
audited before merging upstream.

### MD-branch verification (the spec's clarification list)

| Item | Where to look | Status |
|---|---|---|
| Country tag = NKO | `history/countries/NKO - North Korea.txt` | **confirmed** |
| Money-deduction pattern | `set_temp_variable = { treasury_change = -N }; modify_treasury_effect = yes` (defined in `common/scripted_effects/00_budget_effects.txt:1705`) | **confirmed** in `Egypt.txt:626` and elsewhere |
| Country-monthly hook | I added `on_monthly_NKO` to my own on_actions file; MD's main `on_monthly` lives in `MD_on_actions.txt:577` and is shared. Tag-specific on_actions are conventional in MD (`99_<TAG>_on_actions.txt`). | **confirmed** |
| Existing competing mechanic | Reviewed the 6 existing NKO decision categories — none touch productivity dials. | **no conflicts** |
| MD branch | `NorthKoreanAdditions2026` (post-merge with main, commit 6c3a3010d0). Mechanic should also work on `main`. | **confirmed** |

### MD-modifier verification (used by this submod)

All listed modifiers were grepped against existing MD dynamic_modifiers and
ideas to confirm they exist and behave as expected:

- `production_speed_industrial_complex_factor` ✅
- `production_speed_arms_factory_factor` ✅
- `production_speed_buildings_factor` ✅
- `production_factory_max_efficiency_factor` ✅
- `production_factory_efficiency_gain_factor` ✅
- `industrial_capacity_factory` ✅
- `consumer_goods_factor` ✅
- `local_resources_factor` ✅ (used for both the spec's "resource gain efficiency"
  and "+10% local resources" — they share the same vanilla modifier; combined
  the bonus to +0.35)
- `army_attack_factor` ✅
- `training_time_army_factor` ✅
- `stability_factor` ✅
- `war_support_factor` ✅
- `political_power_gain` ✅
- `improve_relations_maintain_cost_factor` ✅
- `trade_opinion_factor` ✅

### MD scripted-effect / trigger references used

- `modify_treasury_effect` — `common/scripted_effects/00_budget_effects.txt`
- All other scripted effects and triggers are defined inside this submod.

### Costs scaling note

The spec's PP/money costs (50–300 money) treated money like a 0–1000 scalar;
MD's actual treasury runs **0–10** (NKO starts at 6.3). I rescaled to
0.3–0.75 treasury to keep the original PP/money ratio sensible. PP costs
unchanged from spec (40–75).

| Resolution | PP | Treasury | Existing cost loc key |
|---|---|---|---|
| Industrial Acceleration | 50 | 0.5 | `cost_0_5` |
| Equipment Production | 50 | 0.7 | `cost_0_7` |
| Songun | 75 | 0.4 | `cost_0_4` |
| Juche Self-Reliance | 75 | 0.3 | `cost_0_3` |
| Ideological Mobilization | 50 | 0.4 | `cost_0_4` |
| Agricultural Drive | 60 | 0.5 | `cost_0_5` |
| Foreign Policy | 40 | 0.7 | `cost_0_7` |
| Construction Battalion | 60 | 0.75 | `cost_0_75` |

All cost keys were verified to exist in `localisation/english/MD_decisions_l_english.yml`.

## Custom GFX assets still needed

Every sprite has a working fallback to existing NKO/MD textures, so the mod
ships without missing-art warnings. Replace these for proper crimson/gold
DPRK-themed visuals matching the design spec:

| Sprite name | Current fallback | Spec requirement |
|---|---|---|
| `GFX_decisions_category_NKO_spa_assembly` | reused `decisions_category_nko_unite_korea.dds` | Crimson `#5C0808` panel with gold double frame, 9-ray sunburst, gold star |
| `GFX_decision_category_picture_NKO_spa_assembly` | same | Wider hero version of the above |
| `GFX_NKO_spa_header_bg` | same | 720×86 strip; solid `#7A1F1F` with gold pinstripes top/bottom, sunburst at 35% opacity |
| `GFX_NKO_spa_status_bg` | same | 720×42 strip; cream `#F0E2C0` with red progress bar element |
| `GFX_NKO_spa_workers_party_emblem` | reused `nko_red_youth_guard_idea.dds` | Red disc with gold border; hammer + writing brush + sickle in gold |
| `GFX_NKO_spa_chip_<domain>` (×8) | per-domain NKO idea texture | 50×40 chip with frame variants for active (gold border + gold star) and penalty (faded red border + minus sign) |
| `GFX_decision_NKO_spa_<domain>` (×8) | per-domain NKO button texture | Resolution card icon set, cream `#F5E6C8` with red top strip and Korean name in gold light |
| `GFX_decision_NKO_spa_pass` | reused `nko_un_support_button.dds` | Pass-Resolutions button, idle/hover/locked variants in `#A02525` with gold border |
| `GFX_report_event_NKO_spa_*` (×4) | reused `NKO_korea_unification.dds` | DPRK Assembly hall, Cabinet meeting, collapse imagery |

The top-bar entry icon described in the spec is intentionally **not implemented**
in this drop. MD's idiom for "session is open" is the decision category alert
on the political tab, which this mod uses. If a true top-bar icon is desired
later, add a separate scripted_gui with `context_type = player_context` and
hook it into `interface/topbar.gui`.

## Known limitations

- **Bilingual fonts**: the .gui uses `hoi_20b` / `hoi_18b` — these are the
  standard MD HOI4 fonts. Korean glyphs render only if the font has CJK
  coverage. If glyphs show as boxes in-game, the localisation strings are
  fine; swap to a CJK-capable font in the .gui (e.g., `hoi_18mbs_korean` if
  MD has one defined, otherwise add one).
- **The `NKO_spa.2` adjournment event** is defined but never auto-fired —
  kept for future modders who want a closing news beat. Wiring it in is a
  one-line addition to `NKO_spa_close_session`.
- **Non-English localisation** is untouched — Paratranz handles all other
  languages per project convention. Add the bilingual keys to non-English
  files once Paratranz pulls them.
- **CLAUDE.md says no `available = { always = no }` on focus + bypass**;
  this submod has no focuses, so the rule doesn't apply, but if you wire
  any later, follow the rule.

## Files modified vs. added

**Modified** (single MD file, two-line surgical edit):
- `common/decisions/categories/north_korea_decision_categories.txt` — added `scripted_gui = NKO_spa_gui` to the `NKO_Arduous_March` category and expanded its `visible` block. The original `arduous_march_modifiers` visibility is preserved as the first OR branch, so existing behavior is unchanged for players who don't have the SPA umbrella idea.

**Untouched**:
- `MD_on_actions.txt`, `00_on_actions.txt` (SPA hooks live in their own `NKO_spa_on_actions.txt` file)
- NKO history file (umbrella + standing debuffs apply via `on_startup`)

To remove this submod: revert the two-line edit to `north_korea_decision_categories.txt`, then delete the 11 added files.
