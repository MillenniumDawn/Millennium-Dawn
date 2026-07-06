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
- Annexation cleanup lives in `clear_united_nations_member_state` (mission reassignment, vote abort, queue purge, array pruning, `sc_action_against@THIS`). Extend it, not the call sites.
- Sway effects (`un_sway_direction_effect`/`sc_sway_direction_effect`) are guarded on the ongoing-vote flags so pending sway events accepted after teardown cannot write into cleared tallies.
- The same guard wraps every vote-option array write (and the P5 veto set) in UN.6/UNSC.1/recognition.12/recognition.15: a human mission holder can complete the finisher early, and late answers must not pollute the next vote's tally or leak a stale veto.
- `global.security_council_members` is positional: elected seats at 0-9, P5 from 10. Never remove an entry by value; `clear_united_nations_member_state` refills a dead member's slot with a qualified GA member so the January rotation stays aligned.

## UNSC election lifecycle

June (`start_unsc_next_term_voting`): clears `new_council_members`, seeds 5 regional candidates, sets `electing_new_unsc_members` (timed 200d). Each candidate gets a type-6 GA vote. On 2/3 pass, `un_sc_new_members_step_next` confirms the seat and queues the next candidate; on fail, `un_sc_new_members_re_roll` swaps in a replacement (capped by `global.unsc_reroll_count`, 15 per election). January (`update_security_council_peeps`): rotates `security_council_members` (elected seats 0-9, P5 at 10+), clamps confirmed to 5, and backfills unfilled seats from the departing cohort so no duplicates and no P5 clobber.

Rules:

- The chain advances only when the finished vote's subject equals `new_council_members^0` AND `electing_new_unsc_members` is set. Standalone type-6 votes (focus rewards like Algeria's) only add to `confirmed_new_council_members`; they never re-roll or advance the chain.
- Stalls self-heal: the weekly pulse re-queues `new_council_members^0` when the election flag is up with no live or queued type-6 vote, or dissolves the election when no candidates remain. Do not add other termination paths; route them here.
- The GA cooldown strip during elections requires a type-6 entry somewhere in the queue. Removing that gate re-creates the #2305 vote storm.

## Adding a new GA resolution type

1. Take the next free type id (22+). Add triggered `title`/`desc` blocks in UN.6 with new `UN.<id>.t/.d` loc keys, and gate any type-specific ai_chance modifiers.
2. Add the outcome branch in `general_assembly_vote_finished` (inside the pass branch unless it genuinely applies on failure).
3. If yes-voters get a timed idea and no-voters get a choice, extend UN.410: triggered title/desc on `ga_resolution_vote_type`, a branch in the accept option's `add_timed_idea` chain, and the type range checks in ai_chance (they assume 10-21 today).
4. Add scripted loc `un_ga_vote_on_desc_<id>` and `un_ga_vote_track_<id>` plus the AI proposal weighting in `un_ai_ga_consider_resolution`.
5. Queue it via the `ga_new_vote_type`/`ga_new_vote_nation` temp vars and `update_ga_vote`.

## History

The 2026-07 overhaul (issue #2305) fixed the vote storm (election flag never expiring plus unconditional cooldown strip), the O(N^2) resolution reject sweep, per-member `meta_effect` dispatch, the 2/3 rounding, and consolidated 32 near-identical events into 3. The consolidation recipe is documented in `simplification-patterns.md` under "Consolidate Near-Identical Event Families".
