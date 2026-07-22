---
title: Corporate History Framework
description: Millennium Dawn corporate-history chains - framework effects, game rule, start-date policy, tier budgets, and integration rules
---

The corporate-history framework powers the dated company chains (IBM, Sun/Microsoft, HP, Apple, Sony, Matrox, Nokia, and (at dispatch level only) Siemens, Ericsson, BlackBerry). It centralizes control flow, value bounds, and game-rule gating; each company binds its own names, dates, and deltas in thin wrapper effects.

# File Map

> **Location**: `common/scripted_effects/00_corporate_history_effects.txt` (core), `00_corporate_history_dispatch_effects.txt` (yearly dispatch), `common/scripted_triggers/MD_corporate_history_triggers.txt` (rule gates)

| Piece | File |
| --- | --- |
| Primitives (`corporate_history_apply_delta`, `corporate_history_clamp_value`), startup driver, monthly Outcomes-Only drivers | `common/scripted_effects/00_corporate_history_effects.txt` |
| `<TAG>_corporate_trigger_year_<YYYY>` yearly dispatch (one effect per country per year) | `common/scripted_effects/00_corporate_history_dispatch_effects.txt` |
| Rule gates `corporate_history_full_enabled` / `corporate_history_outcomes_only_enabled` | `common/scripted_triggers/MD_corporate_history_triggers.txt` |
| Per-company wrappers (init/clamp/reconstruct/schedule/capstone) | `common/scripted_effects/USA_ibm_effects.txt`, `USA_apple_effects.txt`, `USA_microsoft_effects.txt`, `JAP_sony_effects.txt`, `CAN_matrox_effects.txt`, `FIN_nokia_effects.txt` |
| Game rule `rule_corporate_history` | `common/game_rules/00_game_rules.txt` |

# Game Rule Semantics

`rule_corporate_history` has three options, fixed at game setup (no mid-game transitions):

- **Full** (default): story events, decision windows, and the IBM crisis engine run exactly as authored.
- **Outcomes Only**: no corporate story events fire. The historical path (flags, state variables, outcome ideas) is applied silently by the per-company `*_reconstruct_history` effects, invoked at startup and then from per-country monthly drivers. Each milestone lands on the **first monthly tick after its historical date** (≤ ~31 days lag, the same order of slop as the yearly dispatcher's early-January day offsets). The IBM crisis engine is Full-only (its events are popups), so no crisis ideas appear in this mode. Siemens, Ericsson, BlackBerry, and HP are suppressed without replacement (no reconstruction exists for them).
- **Off**: dispatchers never run, so no corporate events, variables, flags, or ideas ever exist for any country.

**Gating happens only at dispatcher level**: the startup driver, the `<TAG>_corporate_trigger_year_*` effects, the monthly drivers, and the `USA_ibm_monthly_crisis_checks` call site in `99_USA_on_actions.txt`. Never add rule checks inside individual events: an event that was never scheduled needs no gate, and per-event gates rot.

# Start-Date Policy (January-1 Invariant)

The yearly dispatcher (`on_monthly` → `trigger_year_[year]_events`) fires on the first monthly tick of each calendar year, and **the start year's own block never runs**; startup scheduling covers it. Every milestone `days = N` offset therefore assumes its clock starts on January 1 (bookmark start) or the early-January dispatch tick.

The framework handles start dates with a **hard guard, not day-of-year math**:

- A chain that has milestones in a potential start year ships a `*_schedule_current_year_events` effect whose blocks are guarded by the per-year window `NOT = { has_start_date < Y.1.1 }` + `has_start_date < Y.1.2` (i.e. they only queue events when the campaign starts **exactly on January 1 of that year**), keeping all offsets calendar-correct. `USA_apple_schedule_current_year_events` is the reference implementation.
- For any later start, the per-company `*_reconstruct_history` effects silently apply every milestone whose date has passed (each step is `date >` + marker-flag guarded, idempotent, and event-free).
- Non-January-1 starts are **deliberately not scheduled**: passed milestones reconstruct; the start year's remaining milestones are skipped rather than fired on wrong dates. MD ships a single 2000.1.1 bookmark, so this path is theoretical.

# Wrapper Contract

HOI4 cannot parameterize identifier names (variables, flags, ideas, event ids) without meta_effect renames, so the framework owns **control flow, bounds, and gates**, and each company binds its names in wrapper effects that contain data, not logic:

| Wrapper | Shape |
| --- | --- |
| `<TAG>_<co>_initialize_state` | flag-guarded `set_variable` defaults + trailing clamp call |
| `<TAG>_<co>_clamp_state` | per variable: `set_temp_variable = { corp_value = X }` → `corporate_history_clamp_value = yes` → `set_variable = { X = corp_value }` |
| `<TAG>_<co>_reconstruct_history` | date-ascending ladder; every step `date > D` + `NOT` on **all** sibling outcome markers; `add_ideas` steps guarded by `NOT has_idea` on all alternatives; no event fires; ends with silent capstone resolution where the chain has one, then sets `<TAG>_<co>_reconstruct_complete` once the final milestone date has passed (the monthly driver's only terminal check). A ladder can end *after* its capstone (IBM's integrations run to 2027.6.1, past the 2026.6.2 capstone), so the completion date is the last step's date, not the capstone's |
| `<TAG>_<co>_events.90` | hidden, `fire_only_once` event whose immediate is a thin call to the reconstruct effect (IBM's also keeps its `date < 2000.2.1` prehistory-scheduling branch) |
| `<TAG>_<co>_schedule_current_year_events` | per-year Jan-1 window guard + `country_event` offsets (optional; Apple only so far) |
| capstone family | `clear_capstone_outcome` (remove all competing ideas + flags) / `apply_*_capstone` (clear, add one idea, set outcome + resolved flags) / `resolve_capstone` (threshold ladder) |

The primitives:

```hoiscript
set_temp_variable = { corp_value = USA_apple_ecosystem_control }
set_temp_variable = { corp_delta = 2 }
corporate_history_apply_delta = yes # adds, then clamps to the 0..10 band
set_variable = { USA_apple_ecosystem_control = corp_value }
```

`corporate_history_apply_delta` is the single owner of the 0..10 band; `corporate_history_clamp_value` is the delta-0 binding of it. Event options keep plain `add_to_variable` + `<TAG>_<co>_clamp_state`; do not rewrite option bodies onto the primitives.

AI weighting on event options follows the house pattern: `is_historical_focus_on` and `has_active_mission = bankruptcy_incoming_collapse` appear as **separate** `factor = 0` modifiers, never combined in one modifier block. (Existing chains vary in idiom, `base`+`add` vs `factor`, and keep their authored numbers; new chains should use separate `factor = 0` guards.)

# Interaction Policy

A chain may read **only its own flags and variables**, plus the cross-links declared in the table below. Cross-chain **writes** are forbidden except through the owning chain's scripted effects (the Sun/Microsoft → IBM write-through is the grandfathered exception). Reads of another chain's state are allowed only in `ai_chance` / flavor triggers and must be declared here when added.

| Reader | State read | Where |
| --- | --- | --- |
| Sun/Microsoft | IBM shared state `USA_oem_*`, `USA_ibm_faction_*` (write-through + `ai_chance` reads); calls `USA_ibm_initialize_state`/`USA_ibm_clamp_state` | `events/USA_sun_microsoft_events.txt` |
| Apple | IBM outcome flags `USA_ibm_watson_enterprise`, `USA_ibm_x86_divested`; Microsoft outcome flags `USA_microsoft_azure_*`, `USA_microsoft_cloud_*` (`ai_chance` only) | `events/USA_apple_events.txt` |
| Siemens | Nokia NSN flags `FIN_nokia_siemens_networks_formed`, `FIN_nokia_networks_wholly_owned`, `FIN_nokia_exited_networks` (option triggers) | `events/GER_siemens_events.txt` |
| Sony | GPU-chain flags `JAP_gpu_*` (capstone option triggers/`ai_chance`) | `events/JAP_sony_events.txt` |
| Matrox | BlackBerry/AI flags `CAN_blackberry_qnx_embedded`, `CAN_ai_public_research_network` (capstone option triggers) | `events/CAN_matrox_events.txt` |
| IBM (inbound) | US politics via `USA_ibm_*_administration` triggers, reads non-corporate state, allowed | `common/scripted_triggers/MD_oem_triggers.txt` |

`gpu_development`, `USA_oem_events`, BlackBerry, and Ericsson read **no** state of the covered chains, so gating the chains cannot strand them. The three Nokia NSN flags are a stable API; Siemens depends on them; do not rename.

# Tier Budgets

New chains must fit one of three budgets. Anything larger needs maintainer sign-off.

- **Tier 1**: full chain, ~12-15 events, bounded 0..10 state variables, full capstone set (mutually exclusive outcome ideas + resolved flag), reconstruction, monthly-driver coverage.
- **Tier 2**: focused chain, 4-6 events, a single outcome idea, flag-based state, reconstruction.
- **Tier 3**: flavor, 1-2 events, no persistent state, no reconstruction needed.

Classification of the existing chains (chains predating the budgets are marked *grandfathered*; do not copy their scale):

| Chain | Tier | Notes |
| --- | --- | --- |
| Apple (USA) | 1 | Reference implementation: 15 events, 7 variables, 5 outcome ideas, scheduler + reconstruction |
| Sony (JAP) | 1 | 15 events, flag-based state, 4 outcome ideas, player-choice capstone |
| Matrox (CAN) | 1 | 12 events, flag-based state, 4 outcome ideas, player-choice capstone |
| IBM (USA) | 1 *(grandfathered)* | 50 events, 13 ideas, consequence schedulers, monthly crisis engine, over every budget |
| Sun/Microsoft (USA) | 2 *(satellite)* | 11 events, no own state or ideas; declared write-through into IBM state |
| Nokia (FIN) | 2 | 8 events, flag-only, no capstone ideas; NSN flags are a Siemens-read API |
| HP (USA) | 3 *(grandfathered)* | 13 events but no persistent corporate state, no reconstruction; flavor economics only |
| Siemens (GER), Ericsson (SWE), BlackBerry (CAN/USA) | 2 | Dispatch-moved + rule-gated only; internals not yet on the framework |

# New-Chain Checklist

1. Wrapper effect file in `common/scripted_effects/` with the contract set above (init, clamp, reconstruct; capstone family for Tier 1; scheduler if the chain has potential start-year milestones).
2. Hidden `.90` event whose immediate is a thin reconstruct call.
3. Schedule entries added to the matching `<TAG>_corporate_trigger_year_<YYYY>` effects (create new ones as needed; never schedule inline in `00_yearly_effects.txt`), plus the startup entry in `corporate_history_on_startup` (both branches).
4. Monthly-driver coverage: add the reconstruct call to `<TAG>_corporate_history_monthly_outcomes`; the driver terminates on the chain's `*_reconstruct_complete` flag, so the ladder must set that flag at its true final milestone (create the `on_monthly_<TAG>` hook if the country has none).
5. Outcome ideas: `allowed = { original_tag = <TAG> }` **and** `allowed_civil_war = { always = yes }`.
6. Guard audit on every reconstruct step: `date >` gate; `NOT` on the step's own marker **and all sibling markers**; `add_ideas` guarded by `NOT has_idea` on all alternatives; no event fires inside reconstruction; single-child `NOT`s only.
7. Cross-links declared in the table above; localisation; changelog.

# TODO Register

- **Siemens / Ericsson / BlackBerry**: no reconstruction effects; Outcomes Only suppresses their events with no silent replacement. Ericsson's existing `SWE_ericsson_events.90` is the natural first extraction; Siemens and BlackBerry have no `.90` at all and need ladders authored from their option effects.
- **Start-year schedulers** for IBM, Sun/Microsoft, Sony, Matrox, Nokia (Apple-pattern; inert while MD ships only the 2000.1.1 bookmark).
- **HP**: no persistent corporate state by design; decide whether to formalize as Tier 3 or extend to Tier 2 with an outcome idea.
- **Sun/Microsoft**: consider its own capstone/state if ever split from the IBM substrate; the current write-through is the declared exception.
