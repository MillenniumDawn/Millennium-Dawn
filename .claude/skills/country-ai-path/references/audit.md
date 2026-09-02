# AI path audit reference

Read **after** `ai_path_report.py --tag <TAG>`, never before. The report already decides the
mechanical questions; this file is the judgment the report cannot make. Every check below caught a
real bug in an earlier country.

## The report answers these — act on its findings, don't re-derive them

| Report section | Bug it catches |
| --- | --- |
| Tree ownership | Additive path modifiers that lose to any multiplicative historical modifier (Ethiopia); a path flag that appears in the tree zero times (Japan had 36 historical modifiers and none for path two; Italy's ten had none at all) |
| Killswitch orphans | Children stranded because every prerequisite in their sole OR-group was zeroed, and gates (`has_completed_focus`, `check_variable`, a flag set only by a zeroed focus) stranded without producing an orphan |
| Mutex ties | Fork sides at identical priority resolving by file order (Italy's ~30 doctrine pairs at `base = 80`; Comoros' social-democracy/dictatorship mutex) |
| Strategy plan | `focus_factors` disagreeing with the tree, plans with no `focus_factors` at all, both sides of a fork zeroed |
| Danger rewards | Completion rewards that disband the army, hand the country away, or start an unwinnable civil war |
| Rule / Wiring | Option set, two-sentence descs, `@TAG` header, per-option flags, `RANDOM_PATH` buckets, surviving `has_game_rule` readers |

A surviving `factor = 0` `is_historical_focus_on = yes` killswitch in the tree still zeroes a path's
own focuses even when a strategy plan boosts them (10 × 0 × 100 = 0) — every such killswitch needs a
`NOT` exemption for the paths that own it. `ai_national_focuses` is a priority list, not a
whitelist; derive killswitches from `focus_factors`.

## Is the chosen path reachable?

Trace every branch root's `available` to something the AI can satisfy. HOL and UK selected branches
needing a ruling party nothing grants; `CHI_Equal_Partners` required `has_government = SOV`; Japan's
imperial branch needed a party at exactly the 0.05 `election_threshold` default; Italy's conquest
tree needed `has_expansionist_government`, which its own ramp's party doesn't satisfy, behind a
three-way fork resolving by file order; Comoros' Orange Party focus required the conservative
government its own reward installs, and its Islamism root required a popularity nothing in the
country could grow. Fix with a legitimate route (popularity growth + AI-only takeover decision, or
the country's existing mechanic), never a scripted force-flip.

## Can the government change, and does drift smother it?

Elections resolve on raw sub-party popularity, so a dominant starting party re-elects forever. Read
the drift ledger from the history file's ideas before sizing a ramp: UK `democratic_drift = 0.40`;
Japan `western_country` (0.08 + `drift_defence_factor` 0.40); Italy `western_country` + `EU_member` +
`NATO_member` (+0.11 net); Comoros has none. Patterns: the date-driven AI-only walk (shape in
[write.md](write.md) §8 — `HOL_politics.86` and `britain_md.400` are the only live examples and both
are wrong, so read the template, not them), `JAP_ai_path_category` / `ITA_ai_path_category` /
`BOT_ai_path_category` / `COM_ai_path_category` (decision ramp + drift-cancelling dynamic modifier).

## Does the chosen path survive its own election?

A coup or takeover event that changes the ruling party without disabling elections hands power back
at the next scheduled election and strands the whole branch behind an in-power gate.
`change_ruling_party_effect` takes a `disable_elections` temp var; scope it to `is_ai = yes` so a
human keeps their agency.

## Does the historical path deliver the historical person?

The report's `government` section verdicts the roster and audits any walker; these are the judgments
it cannot make. Is the roster a real **timeline** or just a list of plausible successors? A file can
clear the dated-entry threshold on one branch while the branch your path installs has no dates at all
— read the per-sub-ideology table, not the verdict alone. Are the people a walker asserts actually
heads of government? ENG's conservatism roster opens with William Hague and Michael Howard, both
opposition leaders who were never Prime Minister, so index 0 is not "the first Tory PM". Does a focus
tree leave `do_not_retire` set and never clear it (`common/national_focus/05_afghanistan.txt:7249`,
`05_iraq.txt:10571` do), pinning the cascade for the rest of the game? And does the country already
own its election flow behind `generic_election_killswitch` (AST, BOT, BRA, HAI, PER, ROM, SAO, SIA,
SIN, SOM, SPR) — if so extend that chain, never stack a walker on it.

## Right axis, right arity?

Derive the fork from the prerequisite graph and each side's `available`, not the option names. Find
master switches gating large sub-trees, and coherent spines no option claims (Japan: a ~30-focus
pacifist spine zeroed by both plans; Italy: a 92-focus authoritarian spine and 37-focus conquest
root claimed by nobody; Comoros: a 12-focus Orange Party spine). Kill options that are strategically
identical — Italy had ten producing the same country, Comoros' "Democracy Route" was its historical
path under another name.

## Crisis focuses and stranded maluses

Crisis / problem-resolution focuses sitting at flat base priority, and whether the modifier's
trigger matches what the focus actually removes, transitively. If the idea-removal detector comes
back empty, look for negatively-seeded dynamic-modifier variables in the history file.

Then: does killswitching strand a malus? Gate the applying event off for a rule-driven AI. Italy's
only cure for its starting southern-question idea sat under one side of an unclaimed mutex fork.
Also check for a mission with unconditional `activation` but `available` gated on one fork side.

## Focuses the AI must never take

Rewards that disband the army, lock templates, hand the country to another power, or start an
unwinnable civil war (`JAP_dissolving_sdf` ran `delete_unit = { disband = yes }` across every owned
state; `ITA_seize_power` handed 76% of Italy to rebels; `COM_rejoin_france` turns Comoros into a
French overseas department) get zeroed in every plan including the no-path one. Prefer
`focus_factors = 0` over `ai_will_do = { base = 0 }` where a plan multiplier is in play — base 0 is
unrecoverable.

## Event-driven forks

`complete_national_focus` from an event option, or any option setting the ruling party or path,
needs `ai_chance` on every option. A single-option event force-feeding a wargoal needs a stand-down
option, not just an `ai_chance`. Hunt for an option that deletes the country — `italy_md.37` offered
`change_tag_from` against an empty option, both at the default weight of 1. Check `ai_chance`
clauses unconditionally true at game start, and whether a later `factor = 0` wipes an earlier
`add = N` a path flag was supposed to win (`italy_md.70` made Comoros' Warrior King path impossible
under default settings). Check `log =` strings cite their own option IDs — `check_common_mistakes.py`
misses event log-ID drift and `fix_log_ids.py` doesn't cover `events/`; a naive regex matches
`[This.GetName]` before the real ID, and options with a `trigger` block between `name` and `log`
need a line-wise fix. Multi-option news events partitioned by mutex triggers are not bugs.

## Tautologies in `ai_will_do` guards

`ITA_pesky_states` was zeroed forever by `OR = { NOT(A) NOT(B) NOT(C) }` where A and C are mutually
exclusive, orphaning six conquest focuses. Any OR of NOTs spanning a mutex pair is always true.

## Country-specific systems that can lose the AI the game

Find any separatism / collapse / succession / escalation system, check the AI's weights including a
way back down, and check whether a soft brake (`factor = 0.25`) is soft enough that the AI spends
through it anyway. UK devolution was a coin flip toward losing Scotland/Wales/NI; China's Taiwan
blockade set a permanent tension tick with no off-ramp; Japan's Article 9 balance of power sets
`can_not_declare_war = yes` on all five ranges; Italy's Padania branch tag-switched the country out
of existence on a `factor = 400` that Lega drift makes likelier yearly.

## Before adding anything new

Check MD already has the mechanic. UK's influence path needed no new script (`influence.500` +
`influence_targets`); Italy's ramp reused existing party-head focuses sitting at `base = 0`.

**Shared focus trees** (`shared_focus` includes) serve several countries — never gate them on one
country's path flags.