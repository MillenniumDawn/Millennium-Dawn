# AI path audit reference

Read after `ai_path_report.py --tag <TAG>`, never before. The report decides the
mechanical questions. This file is the judgment it cannot make.

## What the report already answers

Act on these. Do not re-derive them.

- Tree ownership: additive path modifiers that lose to a multiplicative historical
  modifier, and path flags that appear nowhere in the tree.
- Killswitch orphans: children stranded because every prerequisite in their only
  OR-group was zeroed, and gates stranded without producing an orphan.
- Mutex ties: fork sides at identical priority, resolved by file order.
- Strategy plan: `focus_factors` that disagree with the tree, plans with none, and both
  sides of a fork zeroed.
- Danger rewards: rewards that disband the army, hand the country away, or start an
  unwinnable civil war.
- Mechanics: the burdens the country starts with and what relieves each, a burden whose
  every cure is dead in some rule state, a cure focus at flat base, a cure decision at
  `base = 0` or behind `is_ai = no`, and whether each country GUI is decision-backed.
- Rule and wiring: the option set, two-sentence descriptions, per-option flags,
  `RANDOM_PATH` buckets, and surviving `has_game_rule` readers.

A surviving `factor = 0` on `is_historical_focus_on = yes` still zeroes a path's own
focuses even when a strategy plan boosts them. Every such killswitch needs a `NOT`
exemption for the paths that own it. `ai_national_focuses` is a priority list, not a
whitelist. Derive killswitches from `focus_factors`.

## Is the chosen path reachable?

Trace every branch root's `available` to something the AI can satisfy: a ruling party
something grants, a popularity something can grow, a government its own ramp installs.
Fix an unreachable root with a legitimate route (popularity growth plus an AI-only
takeover decision, or the country's existing mechanic), never a scripted force-flip.

## Can the government change?

Elections resolve on raw sub-party popularity, so a dominant starting party re-elects
forever. Read the drift ledger from the history file's ideas (`western_country`,
`EU_member`, `NATO_member`, `democratic_drift`) before sizing a ramp. The working shapes
are the date-driven AI-only walk in [write.md](write.md) §8, and a decision ramp with a
drift-cancelling dynamic modifier in the country's `TAG_ai_path_category`. Read the
template, not another country's walker.

## Does the path survive its own election?

A coup or takeover that changes the ruling party without disabling elections hands power
back at the next election and strands the branch behind an in-power gate.
`change_ruling_party_effect` takes a `disable_elections` temp var. Scope it to
`is_ai = yes` so a human keeps agency.

## Does the historical path deliver the historical person?

The report's `government` section verdicts the roster and audits any walker. Judge the
rest:

- Is the roster a real timeline or a list of plausible successors? Read the
  per-sub-ideology table, not the verdict alone. The branch your path installs may have
  no dates.
- Are the people a walker asserts actually heads of government? A roster can open with
  opposition leaders.
- Does a focus tree set `do_not_retire` and never clear it? That pins the cascade.
- Does the country already own its election flow behind `generic_election_killswitch`?
  Then extend that chain. Never stack a walker on it.

## Right axis, right arity?

Derive the fork from the prerequisite graph and each side's `available`, not the option
names. Find master switches gating large sub-trees and coherent spines no option claims.
Remove options that are strategically identical.

## Crisis focuses and stranded maluses

The report's `Mechanics` section lists every burden and what relieves it, and raises
`every cure is dead under <option> / historical <on|off>` directly. Judge:

- Sign. The tool does not know a bonus from a malus, so `nothing relieves` mixes both.
  Read the idea's modifiers first. The direction rule is in
  `.claude/docs/scripting-edge-cases.md`. `tools/analysis/find_idea_references.py` shows
  where an idea is touched.
- Transitive fit. Does the crisis modifier's trigger match what the focus removes, once
  you follow the scripted effects it calls?
- The applying event. A malus applied by an event after game start never reaches the
  burden list. Gate that event off for a rule-driven AI when the curing branch is
  killswitched.
- Missions. An unconditional `activation` with `available` gated on one fork side
  strands the same way and is invisible to the report.

## Focuses the AI must never take

Zero any reward that disbands the army, locks templates, hands the country to another
power, or starts an unwinnable civil war, in every plan including the no-path one.
Prefer `focus_factors = 0` over `ai_will_do = { base = 0 }` where a plan multiplier is
in play. Base 0 is unrecoverable.

## Event-driven forks

- `complete_national_focus` from an event option, or any option that sets the ruling
  party or path, needs `ai_chance` on every option.
- A single-option event that force-feeds a wargoal needs a stand-down option.
- Hunt for an option that deletes the country, such as `change_tag_from` at the default
  weight.
- Check for `ai_chance` clauses that are true at game start, and for a later
  `factor = 0` that wipes an earlier `add = N` a path flag was meant to win.
- Check that `log =` strings cite their own option ids. `fix_log_ids.py` does not cover
  `events/`.
- Multi-option news events partitioned by mutex triggers are not bugs.

## Tautologies in `ai_will_do` guards

An `OR` of `NOT`s that spans a mutually exclusive pair is always true. A `factor = 0`
behind one zeroes the focus forever and orphans its children.

## Systems that can lose the AI the game

Find any separatism, collapse, succession, or escalation system. Check the AI's weights,
including a way back down, and whether a soft brake such as `factor = 0.25` is soft
enough that the AI spends through it anyway.

## Mechanics the AI cannot drive

The AI never clicks a scripted GUI. Only a `context_type = decision_category` GUI is
AI-reachable, because the decisions behind it are taken normally. The report labels
that `decision-backed` and a `player_context` GUI `player-only`. Where a player-only GUI
is the only relief for a burden, the AI carries the burden all game.

The fix is a decision the AI can take, in the country's `TAG_ai_path_category`
([write.md](write.md) §6): same effect, `is_ai = yes` category, no loc. Never a second
GUI, an `on_daily_<TAG>` pass, or a hidden event that repairs the country for free.

A cure decision at `base = 0` or behind `is_ai = no` means the same thing. Deliberate
is fine, but then the AI needs its own route to the outcome.

## Before adding anything new

Check that MD does not already have the mechanic. Shared focus trees serve several
countries. Never gate them on one country's path flags.
