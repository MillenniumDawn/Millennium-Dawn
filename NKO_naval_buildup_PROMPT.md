# NKO Songun Naval Buildup — Build Prompt

Paste the block below into a fresh Claude session inside this repo. It captures
all the design decisions for the mechanic so a future session can implement it
in one pass.

---

You are working in the Millennium Dawn HOI4 mod (modern-era setting, country
tag NKO = North Korea). I want you to build a fun, interactive, rewarding
"Songun Naval Doctrine" buildup mechanic for NKO, driven by a scripted GUI
and decisions. Follow CLAUDE.md and .claude/rules/ conventions strictly:
tabs for indentation, UTF-8 no BOM for .txt, UTF-8 with BOM for .yml,
original_tag (not tag) in allowed blocks, log lines on every decision/option,
ai_will_do = { base = N }, NKO_-prefixed variables, no magic numbers.

## Concept

Asymmetric naval modernization with four parallel tracks the player advances
in any order. Player accumulates "Naval Buildup Points" via cooldown-gated
decisions, then spends them on tracks. Each track has 4 tiers (25/50/75/100)
that auto-swap progressively stronger hidden ideas and fire flavor pop-ups.
A capstone fires when all four tracks max out, awarding a country spirit and
a major news event.

## Tracks (each 0-100, +5 per investment)

1. **Submarine Force** — Sang-O → Yono → Romeo modernization → Sinpo/SLBM.
   Modifiers: `submarine_attack_factor`, `navy_submarine_detection_factor`,
   `navy_max_range_factor`.
2. **Missile Boat Flotillas** — Komar refits → Soju/Nongo → Kumsong-3 ASCM →
   Wolfpack doctrine. Modifiers: `naval_strike_attack_factor`,
   `naval_speed_factor`, `naval_torpedo_screen_penetration_factor`.
3. **Coastal Defense Network** — Bunkers → Mobile artillery → Fortified
   headlands → Shore-based AShM. Modifiers:
   `coastal_bunker_effectiveness_factor`, `ships_at_home_region_*_factor`,
   `amphibious_invasion_defence`.
4. **Naval Special Operations** — Recon Bureau frogmen → Sea Sniper Bde →
   Light Infantry maritime element → Storm Corps naval. Modifiers:
   `special_forces_*_factor`, `special_forces_no_supply_grace`,
   `marines_special_forces_contribution_factor`.

## Point economy (three flavors so player can pace themselves)

- **Allocate Party Funds:** +1pt, 35 PP cost, 70-day cooldown.
- **Mobilize Nampo Shipyards:** +2pt, 1 civ factory tied up, 90-day cooldown.
- **Launch Juche Naval Drive:** +4pt, 80 PP, -5% stab, +5% war support,
  requires `stab>0.4` & `war_support>0.5`, 180-day cooldown.

## Invest decisions (all 14-day cooldown, cost 0)

One per track, requires unlocked + 1+ point + track<100. Spends 1 pt for
+5 progress. Each gives a small thematic side bonus (`navy_experience`,
`army_experience`, `special_forces_cap_increase`). Each fires a hidden router
event that checks tier thresholds and auto-swaps ideas + fires flavor.

## Capstone

Fires once when all four tracks are at 100. Adds a country-category spirit
`NKO_songun_navy_capstone` with stacking modifiers (navy range, sub attack,
doctrine cost, navy XP gain, navy org, ships_at_home_region modifiers).
Triggers a major news event with NKO and "other" options.

## Files to create

- `common/scripted_guis/NKO_naval_buildup_gui.txt`
  - Top-bar toggle button (sets/clears `NKO_naval_buildup_window_open`).
  - Main window scripted_gui with tier-marker visibility triggers
    (`NKO_sub_tier_1_visible` … `NKO_so_tier_4_visible`) and a close effect.
  - Visible only if `original_tag = NKO` and
    `has_country_flag = NKO_naval_buildup_unlocked`.
- `interface/NKO_naval_buildup.gui`
  - Top-bar window with the toggle button.
  - Main window 720×540, drag-able, with title, subtitle, points readout,
    and four track containers each with: track label,
    `GFX_generic_progress_bar`, 4 tier-marker icons (3 standard + 1 capstone)
    at `x=168/336/504/660`, and a progress text line. Use placeholder GFX
    names prefixed `GFX_NKO_naval_buildup_*`.
- `common/decisions/NKO_naval_buildup.txt`
  - Category `NKO_naval_buildup_category`.
  - `NKO_unlock_naval_buildup` (fire_only_once, gated on
    `has_country_flag = NKO_naval_buildup_consider`, sets the unlocked flag,
    seeds all 5 variables to 0).
  - 3 point-gen decisions, 4 invest decisions, 1 capstone (fire_only_once).
  - All log `"[GetDateText]: [Root.GetName]: Decision <ID>"`.
  - All include `ai_will_do = { base = N }`.
- `events/NKO_naval_buildup.txt`
  - `add_namespace = nko_naval_buildup`.
  - 4 hidden router events (.10/.20/.30/.40) — each checks tier thresholds
    with `NOT = { has_country_flag = NKO_<track>_tier_<n>_reached }`,
    sets the flag, `swap_ideas` (or `add_ideas` for tier 1), then fires the
    flavor event. Uses if/else where appropriate.
  - 16 flavor events (4 per track) with title/desc/picture/option, all
    `is_triggered_only = yes`, with matching log lines on each option.
  - 1 news_event .99 (`major = yes`, two options gated by `original_tag`).
- `common/ideas/NKO_naval_buildup_ideas.txt`
  - `hidden_ideas`: 16 tier ideas (4 per track) with stacking modifiers per
    the track descriptions above.
  - `country`: `NKO_songun_navy_capstone` spirit.
  - No `allowed = { always = no }`, no `cancel = { always = no }`,
    no empty `on_add` logs.
- `localisation/english/NKO_naval_buildup_l_english.yml` (UTF-8 WITH BOM)
  - GUI labels (title, subtitle, topbar tooltip, points display, 4 track
    labels, 4 progress text lines using `[?NKO_*_progress|0]`).
  - Every decision: name + `_desc`.
  - Every idea: name + `_desc`.
  - Every event: `.t` / `.d` / `.a` (and `.b` on the news event).
  - Concise prose, no ellipsis, no all-caps, follow `localisation-rules.md`.

## Variables (all `NKO_`-prefixed)

`NKO_naval_points`, `NKO_submarine_progress`, `NKO_missile_boat_progress`,
`NKO_coastal_defense_progress`, `NKO_naval_specops_progress` — all 0–100,
`clamp_variable` on each invest.

## Flags

`NKO_naval_buildup_consider` (set externally — entry hook),
`NKO_naval_buildup_unlocked`, `NKO_naval_buildup_window_open`,
`NKO_naval_buildup_capstone_done`,
`NKO_<track>_tier_<n>_reached` (16 total, used to gate idea swaps).

## Verification

After writing the files, verify cross-file consistency: every idea referenced
in events is defined in the ideas file; every event ID called from decisions
or routers is declared; every loc key required by decisions/ideas/events
exists; the `.yml` has BOM and the `.txt` files do not.
