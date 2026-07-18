# UN System Reference

Architecture and edit rules for the United Nations voting, membership, and election systems. Read this before touching any of the files below; the system is a distributed state machine and most of its historical bugs came from editing one piece without honoring the invariants.

## Files

| File                                                           | Owns                                                                                     |
| -------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `common/scripted_effects/01_international_systems_effects.txt` | Vote queues, finishers, UNSC elections, aborts, sanctions, recognition helpers           |
| `events/UN_Voting_Events.txt`                                  | Generic vote events (UN.6, UNSC.1), result event (UN.410), sway chains (UN/UNSC.200-204) |
| `events/International Recognition.txt`                         | Type-5 membership chain (recognition.10-15, 71-73)                                       |
| `common/decisions/un_voting_decisions.txt`                     | Finisher missions (UN_GA/SC_voting_mission + result timers)                              |
| `common/scripted_triggers/01_international_triggers.txt`       | `un_ga_2_3_required`, `has_passed_sc_vote`, auto-vote triggers                           |
| `common/scripted_guis/00_missiles_scripted_guis.txt`           | UN windows: propose, tallies, sway, queue reorder, budget                                |
| `common/on_actions/MD_on_actions.txt`                          | Weekly queue pulse, monthly AI actors, June election start, January rotation             |

## Vote lifecycle

1. Anything wanting a vote sets `sc_new_vote_type`/`sc_new_vote_nation` (or `ga_*`) temp vars and calls `update_sc_vote` / `update_ga_vote`. Busy or cooling down means the pair is appended to the parallel queue arrays (`*_vote_type_tracker` / `*_vote_nation_tracker`); type 6/7 GA votes are front-loaded.
2. `un_check_for_next_queued_vote` (weekly pulse, ~4 days) pops one SC and one GA vote when free. Type 5 routes to the recognition chain (recognition.10 for SC, recognition.13 for GA); everything else fires UN.100/UNSC.100 to the vote subject.
3. The start event picks ONE random member, gives it `has_ga_mission`/`has_sc_mission` plus the finisher mission, then fires the generic vote event (UN.6/UNSC.1) to every non-auto-vote member. Voters land in the `*_vote_yes/no/abstain` arrays.
4. The mission holder's complete/timeout runs the finisher (`general_assembly_vote_finished` / `security_council_vote_finished`), which applies the outcome, clears arrays and globals, clears the ongoing flag, and sets the cooldown.

Key state: `global.current_ga_vote_type/nation`, `current_ongoing_ga_vote`, `un_ga_vote_cooldown` (50d GA / 20d SC), `global.un_2_3_number` (yes votes REQUIRED, ceil of 2n/3, computed by `recompute_un_2_3_number` at vote start and once at game start).

## Invariants (break these and you reintroduce fixed bugs)

- Exactly one mission holder per live vote. The finisher runs only from that mission, guarded by `has_ga_mission`/`has_sc_mission`; the else branch is a tooltip no-op by design.
- `current_ongoing_*_vote` is cleared ONLY by the finisher or `un_abort_ga_vote`/`un_abort_sc_vote`. Any new path that kills a vote must go through the abort effects; they also disarm surviving mission holders, clear sway lockouts, and bump the GUI before dropping the flag.
- The queue pairs are parallel arrays. Never remove entries in place; use `un_remove_dying_nation_queued_votes` / `remove_stale_ga_membership_votes_for_this` (rebuild via scratch arrays).
- Vote events (UN.6/UNSC.1) fire with no delay and may read the current-type globals in triggered titles and ai_chance. The result event (UN.410) fires `days = 1` after the finisher cleared those globals, so it reads per-recipient `ga_resolution_vote_type`/`ga_resolution_proposer` set by `fire_ga_resolution_result_event`, which skips recipients with an unanswered window. Clear both vars in every option.
- Annexation cleanup lives in `clear_united_nations_member_state` (mission reassignment, vote abort, queue purge, array pruning, `sc_action_against@THIS`). Extend it, not the call sites. It runs from `on_annex`; as a backstop, the weekly pulse (`un_check_for_next_queued_vote`) sweeps the GA and Council for dead entries and runs the cleanup on any it finds (P5 arrays handled inline, since `p5_member`'s `on_remove` cannot fire on a dead country), catching annexation paths that skip `on_annex` and recovering a vote stalled by a dead mission holder.
- Sway effects (`un_sway_direction_effect`/`sc_sway_direction_effect`) are guarded on the ongoing-vote flags so pending sway events accepted after teardown cannot write into cleared tallies.
- The same guard wraps every vote-option array write (and the P5 veto set) in UN.6/UNSC.1/recognition.12/recognition.15: a human mission holder can complete the finisher early, and late answers must not pollute the next vote's tally or leak a stale veto.
- `global.security_council_members` is positional: elected seats at 0-9, P5 from 10. Never remove an entry by value; `clear_united_nations_member_state` refills a dead member's slot with a qualified GA member so the January rotation stays aligned.
- **A veto is a flag, not a tally.** `has_passed_sc_vote` is "no `security_council_veto` AND more than 8 yes". Every path that records a P5 "no" must set the flag — the manual option in UNSC.1 _and_ `process_auto_sc_vote`. Miss one and a permanent member on auto-reject gets outvoted on its own veto.
- **Aborts must clear `sc_action_against@<subject>` before wiping `global.current_sc_vote_nation`.** That flag is what stops a nation being the subject of two proposals at once; leak it and the nation is immune to every future Security Council proposal for the rest of the campaign. The finisher already clears it; `un_abort_sc_vote` must too, and ordering matters because the abort clears the subject variable a few lines later.
- **The Assembly and the Council have separate sway lockouts** (`has_had_current_un_ga_vote_swayed` / `has_had_current_un_sc_vote_swayed`). They shared one flag, so a GA vote concluding during a live SC vote lifted the Council's lockout and let a member be swayed twice. Do not re-merge them.
- Known narrow hole: `update_security_council_peeps` (January rotation) rebuilds `global.security_council_members` with no ongoing-vote guard, so a mission holder rotated off mid-vote keeps `has_sc_mission` and `un_abort_sc_vote`'s disarm sweep cannot find it. Harmless today only because the 20-day cooldown outlasts the 5-day mission window. Shorten that cooldown and this becomes a live bug.
- **Election candidate pools are never pruned.** Candidates come from the power-ranking regional arrays (`asian_nations`, `sub_saharan_nations`, `middle_eastern_nations`, `american_nations`) plus `sc_updates_euro_america`, all built once at startup — an annexed or capitulated country stays in them forever. Every candidate pick (`start_unsc_next_term_voting`, `un_sc_new_members_re_roll`), the seat confirmation in `un_sc_new_members_step_next`, the January seating prune in `update_security_council_peeps`, and the dead-seat backfill in `clear_united_nations_member_state` must keep their `exists = yes` / `has_capitulated = no` guards (#2428, #2429).
- **Mission-holder picks must guard `exists = yes`** (UNSC.100, UN.100, recognition.11, recognition.14, and the reassignment sweeps in `clear_united_nations_member_state`). A dead holder never completes the finisher mission, so `current_ongoing_*_vote` is never cleared and all voting stalls for the rest of the campaign.

## UNSC election lifecycle

June (`start_unsc_next_term_voting`): clears `new_council_members`, seeds 5 regional candidates, sets `electing_new_unsc_members` (timed 200d). Each candidate gets a type-6 GA vote. On 2/3 pass, `un_sc_new_members_step_next` confirms the seat and queues the next candidate; on fail, `un_sc_new_members_re_roll` swaps in a replacement (capped by `global.unsc_reroll_count`, 15 per election). January (`update_security_council_peeps`): rotates `security_council_members` (elected seats 0-9, P5 at 10+), clamps confirmed to 5, and backfills unfilled seats from the departing cohort so no duplicates and no P5 clobber.

Rules:

- The chain advances only when the finished vote's subject equals `new_council_members^0` AND `electing_new_unsc_members` is set. Standalone type-6 votes (focus rewards like Algeria's) only add to `confirmed_new_council_members`; they never re-roll or advance the chain.
- Stalls self-heal: the weekly pulse re-queues `new_council_members^0` when the election flag is up with no live or queued type-6 vote, or dissolves the election when no candidates remain. Do not add other termination paths; route them here.
- The GA cooldown strip during elections requires a type-6 entry somewhere in the queue. Removing that gate re-creates the #2305 vote storm.

## Vote types

SC and GA type ids live in **separate namespaces** (`global.current_sc_vote_type` vs `global.current_ga_vote_type`) and are dispatched by separate finishers. The numbers overlap and that is fine: SC type 6 (disarmament) and GA type 6 (UNSC seat confirmation) coexist because nothing ever reads them from the same variable. **Type 5 is the one deliberate exception** — a passed SC recognition vote calls `update_ga_vote` and hands the same id across to the Assembly. Do not add another cross-namespace type without going through that handoff.

### Security Council (`security_council_vote_finished`)

| Type | Resolution                      | On pass, the **subject** gets                                                  | Proposable by |
| ---- | ------------------------------- | ------------------------------------------------------------------------------ | ------------- |
| 1    | Cease offensive operations      | `has_end_war_mission` + `UNSC_end_all_offensive_wars`                          | AI, GUI       |
| 2    | Economic sanctions              | `apply_united_nations_sanctions`                                               | AI, GUI       |
| 3    | Restrict foreign volunteers     | `unsc_restricted_volunteers_too`                                               | GUI           |
| 4    | Arms embargo                    | `unsc_arms_embargo`                                                            | AI, GUI       |
| 5    | Recognition                     | routes to the GA via `update_ga_vote`                                          | script only   |
| 6    | Disarmament / material breach   | `unsc_material_breach` (fail: `unsc_disarmament_rejected`)                     | script only   |
| 7    | Demand surrender of a terrorist | `unsc_extradition_demanded` + UN sanctions (fail: `unsc_extradition_rejected`) | script only   |

Type 7 only calls `apply_united_nations_sanctions` if the subject doesn't already carry `united_nations_security_council_sanctions` (it may predate the demand via a type 2 vote), and records that ownership with `unsc_extradition_sanctions_applied`. The extradition chain (`wot.11.a`) clears `unsc_extradition_demanded` unconditionally but only strips the dynamic modifier when it owns that flag, so it never lifts sanctions a separate type-2 vote applied.

### General Assembly (`general_assembly_vote_finished`)

| Type  | Resolution                                               |
| ----- | -------------------------------------------------------- |
| 5     | Recognition (arrives from SC type 5)                     |
| 6     | Confirm a UNSC seat — front-loaded in the queue          |
| 7     | Non-binding condemnation — front-loaded in the queue     |
| 8 / 9 | Decrease / increase the UN operating budget contribution |
| 10-21 | Standing resolutions (poverty, food security, health, …) |
| 22+   | Free                                                     |

### Who can propose what

- **AI**: `un_ai_sc_consider_resolution` sets `sc_ai_action_type` from an explicit `if`/`else_if` chain that only ever yields **1, 2 or 4**. There is no random pick over a type range and no fallback branch — the `random = { chance = 40 }` decides _whether_ to propose, never _what_. GA proposals come from `un_ai_ga_consider_resolution`.
- **Player**: the propose window in `00_missiles_scripted_guis.txt` has hardcoded buttons writing `sc_selected_action` = 1, 2, 3 or 4.
- **Script only**: everything else. A type that has no branch in the AI chain and no GUI button cannot be proposed against an arbitrary country, and some types must stay that way — a randomly proposed "demand this nation surrender a terrorist" is nonsense. If you add a type that should stay script-only, add nothing to either path and say so in the table above.

### The Council has no proposer concept

SC outcomes apply to the **subject** (`var:global.current_sc_vote_nation`). There is no `sc_resolution_proposer` and you should not add one — the GA has `ga_resolution_proposer` because its result event fans out to every member, but the Council's does not need it. If a petitioner needs to react to the outcome, set a flag on the subject in the finisher and have the petitioner read it (this is how the Iraq chain works: `usa_petition_invasion_of_iraq` queues the vote, and `wot.15` triggers on `IRQ = { has_country_flag = unsc_material_breach }`).

Passage is `has_passed_sc_vote`: no veto, and more than 8 yes votes. Any P5 member voting no sets `security_council_veto` in its own option, so a veto is not a tally, it is a flag — do not try to infer it by counting.

## Adding a new SC resolution type

1. Take the next free SC id. Add the outcome branch in `security_council_vote_finished`, in the pass chain **and** in the fail `else` chain if the petitioner needs to distinguish "rejected" from "still voting". Both branches set a flag on `var:global.current_sc_vote_nation`.
2. Add triggered `title`/`desc` blocks in UNSC.1 keyed on `global.current_sc_vote_type`, with `UNSC.<id>.t/.d` loc keys.
3. Add the resolution name to `UNSCGetResolutionTypePassDesc` in `01_ledger_localisation.txt` (`UNSC_pass_type_<id>_desc`), or UNSC.10/11 render a blank where the resolution should be.
4. Weight it in UNSC.1's yes/no/abstain `ai_chance`. `FROM` inside UNSC.1 is the **subject**, not the proposer, so `has_opinion = { target = FROM }` reads how the voter feels about the country being voted on. The generic `check_variable = { global.current_sc_vote_type > 1 }` modifiers already apply to any new type — check whether that is what you want before adding more.
5. Queue it with `set_temp_variable = { sc_new_vote_type = <id> }` + `{ sc_new_vote_nation = <TAG>.id }` + `update_sc_vote = yes`. Never set `global.current_sc_vote_type` directly; `update_sc_vote` decides between starting the vote and queueing it behind a live one. `update_sc_vote` does **not** set `sc_action_against@<subject>` — the GUI and AI proposer paths set it themselves, and a script caller must too (`<TAG> = { set_global_flag = sc_action_against@THIS }`), or the one-proposal-per-subject invariant breaks. Gate the proposing decision on `NOT = { has_global_flag = sc_action_against@<TAG> }` (tooltip `TT_UNSC_NO_PENDING_SUBJECT_VOTE`) so it cannot double-queue behind someone else's proposal.
6. Decide whether the AI and the propose GUI should be able to raise it, and wire (or deliberately do not wire) them. Record the decision in the table above.
7. A subject that can die mid-vote needs teardown. `clear_united_nations_member_state` aborts a live vote whose subject is the dying nation and purges the queue via `un_remove_dying_nation_queued_votes`, and it does that for **any** subject, GA member or not — the membership pruning is just one part of it. It runs from `on_annex`. But a country removed by a scripted `annex_country` in a decision or event is not worth betting on, so call `clear_united_nations_member_state` explicitly on the dying nation before you remove it. Any SC type whose subject is not a normal member (TAL, for instance) is exposed to this.

## Adding a new GA resolution type

1. Take the next free type id (22+). Add triggered `title`/`desc` blocks in UN.6 with new `UN.<id>.t/.d` loc keys, and gate any type-specific ai_chance modifiers.
2. Add the outcome branch in `general_assembly_vote_finished` (inside the pass branch unless it genuinely applies on failure).
3. If yes-voters get a timed idea and no-voters get a choice, extend UN.410: triggered title/desc on `ga_resolution_vote_type`, a branch in the accept option's `add_timed_idea` chain, and the type range checks in ai_chance (they assume 10-21 today).
4. Add scripted loc `un_ga_vote_on_desc_<id>` and `un_ga_vote_track_<id>` plus the AI proposal weighting in `un_ai_ga_consider_resolution`.
5. Queue it via the `ga_new_vote_type`/`ga_new_vote_nation` temp vars and `update_ga_vote`.

## History

The 2026-07 overhaul (issue #2305) fixed the vote storm (election flag never expiring plus unconditional cooldown strip), the O(N^2) resolution reject sweep, per-member `meta_effect` dispatch, the 2/3 rounding, and consolidated 32 near-identical events into 3. The consolidation recipe is documented in `simplification-patterns.md` under "Consolidate Near-Identical Event Families".
