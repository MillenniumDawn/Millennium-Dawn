---
name: country-ai-path
description: 'Build or standardise one country''s TAG_ai_behavior AI path game rule — write the rule options and loc, wire the global flags, own the focus weights, run the AI hardening pass, and open the PR. Use when asked to give a country AI paths or fix its AI path rule, e.g. "/country-ai-path KOS" or "/country-ai-path Kosovo #1234".'
disable-model-invocation: true
---

Give one country a working AI path game rule, one country per chat. Works for a country that has
a rule to standardise and for one that has none yet.

**Syntax:** `/country-ai-path <country or TAG> [#issue]` — e.g. `/country-ai-path KOS`,
`/country-ai-path Kosovo #1234`. The country is required; an issue number is optional.
Requested arguments: $ARGUMENTS

## Context budget

Focus trees run 8k–42k lines. **Never read one end to end, and never open another country's tree to
learn a shape.** Everything you need about the tree comes from `ai_path_report.py`; grep for the
specific lines it names. Templates for every artefact are in
[references/write.md](references/write.md).

## 1. Target

Resolve the argument to a TAG: a three-letter argument is the TAG; a name is looked up in
`common/country_tags/` and `localisation/english/` (`TAG: "Name"`). No argument, or an ambiguous
name — ask, don't guess. If the user names an issue, read it: its body lists the country's known
defects and goes into the PR as `Closes #N`.

Branch `<tag-lower>-ai-paths` off main.

## 2. Facts

```bash
python tools/analysis/ai_path_report.py --tag TAG
```

The first line of the report decides which of three shapes you are in:

- **Rule exists.** Standardise it (§3–§5). The report's RULE / WIRING section lists what deviates.
- **`no TAG_ai_behavior rule`, tree found.** Build the rule from nothing: every artefact in
  [references/write.md](references/write.md) §1–§7, in that order. The report still audits the tree,
  the flags you add and the country's own mechanics, so re-run it after each artefact.
- **`no focus file found for tag TAG`.** The country has no path layer to own. If a rule exists it is
  **removed**, not converted (São Tomé #3702, Solomon Islands #4266 are the shape): delete the
  `TAG_ai_behavior` block and its `TAG_AI_BEHAVIOR` / `RULE_OPTION_*` keys from
  `MD_game_rules_l_english.yml`, then strip every `has_game_rule` read from the country's events —
  keep `factor = 5 is_historical_focus_on = yes` on the historical option of each fork and any
  situational flavour modifier, drop `factor = 1` no-ops and the `is_historical_focus_on = no`
  coin-flip nudges, and delete an `ai_chance` block with no modifier left. Non-English files keep
  their orphaned keys. If no rule exists either, say so and stop — a rule needs a tree to steer.
  Sections 3–5 do not apply; verify with the grep set in §5 and `validate_events.py` /
  `validate_localisation.py`, and say in the PR that the report does not apply.

The report decides every mechanical question: rule and loc conformance, flag wiring, which focuses
carry path modifiers and whether they are multiplicative, path flags that appear nowhere, killswitch
orphans per rule state × historical AI on/off, mutex ties, `focus_factors` disagreements, dangerous
completion rewards, and the country's own mechanics — the burdens its history file hands it, what
relieves each, which burdens go unrelieved in some rule state, and whether each country GUI is
decision-backed or player-only. Read [references/audit.md](references/audit.md) **after** the report
— it covers only the judgment the report cannot make.

## 3. Design

The judgment calls: which fork axis and how many options, whether each branch root is reachable by
something the AI can satisfy, whether party drift smothers the ramp, what must be killswitched.
Derive the fork from the prerequisite graph and each side's `available`, never from the option
names. Where the report is ambiguous about branch structure, dispatch one `Explore` subagent for the
taxonomy — it returns the taxonomy, not file contents.

## 4. Write

Every artefact from [references/write.md](references/write.md). Focus weights are not written by
hand: author the mapping and run

```bash
python tools/standardization/apply_ai_path_weights.py --tag TAG --map <mapping>
```

Loc drafting and `_desc` sentence-count fixes go to a `localisation-editor` subagent on haiku.

**Defects you find are in scope.** A broken fork, a timing race between the country's own path
events, an asymmetric branch, a wrong state id, or a typo in an English string the path events show
gets fixed in the same PR, in its own commit, never deferred as a follow-up. English values only —
never rename a key that non-English files carry.

**Rule standard.** Exactly `HISTORICAL` + one option per alt-history path + `RANDOM_PATH` +
`NO_PATH`, and `NO_PATH` is the `default = { }` block, listed last — a country the player never
configures runs unscripted. No `DEFAULT`, no `RANDOM`; merge any duplicate `DEFAULT`/`HISTORICAL`.
Write the options fresh — don't recycle a stub's names or bucket count. The historical option's
displayed text is literally `"Historical"`; its `_desc` carries the country's history. Player-facing
names, no internal jargon, no "random" in a path name. Every `_desc` exactly two sentences, present
tense about the country, no hard dates, `§8…§!` on party names. Both files are ordered alphabetically
by displayed country name: a new rule block goes at that position in `00_game_rules.txt`, its loc
block at the same position in `MD_game_rules_l_english.yml`, and a country sub-rule (`BLR_union_state_ai_behavior`
is the shape) sits directly after the country's main rule in `RULE_GROUP_AI_BEHAVIOR`.

**Wiring.** Rule → `set_global_flag = TAG_<PATH>_FOCUS_PATH` in `999_game_rules_on_actions.txt`.
`RANDOM_PATH`'s `random_list` includes the historical bucket; `NO_PATH` gets no branch. Convert
country flags to global. Gate on `has_global_flag`, never `has_game_rule`, everywhere including
events and strategy plans — otherwise a RANDOM roll enables the flags but not the plan. Verify
`NO_PATH` leaves a working AI: an unconditionally-enabled strategy plan and a sane focus
`ai_will_do` base.

**Historical government.** Read the report's `government` section. On a **dated timeline** verdict,
write the walker ([references/write.md](references/write.md) §8) and its `00_yearly_effects.txt`
schedule lines, so historical AI delivers the historical head of government and not just the
historical party. On an **undated successor roster**, write nothing and say so in the PR — the ramp
decisions already deliver the party, and a walker over an undated roster installs the wrong person.
Never pass `change_leader_temp = 1`; never inline `create_country_leader`.

**AI hardening pass**, mandatory. `ai_is_threatened` weighting on combat-capacity focuses
(`.claude/docs/ai-strategy-reference.md`, the `ai_is_threatened` section); bankruptcy / `can_staff`
guards on spending focuses (run `tools/validation/validate_focus_tree.py --path .` first — it may
already be clean, and it flags guards on focuses that spend nothing); review
`common/ai_strategy/[TAG].txt` for gaps, reusing the mod-wide strategies per
[references/write.md](references/write.md) §7 before writing any per-TAG block. Under historical AI
the AI must stick to history: killswitch non-historical branch roots, boost the historical branch.

The country must also stay able to fix itself. Every burden it starts with keeps a live cure in every
rule state you leave standing — if killswitching a branch takes the last one, re-own the cure focus
or exempt it. Where a burden's only relief is a player-only mechanic, an `is_ai = no` decision or a
`base = 0` one, give the AI the same outcome through its `TAG_ai_path_category`
([references/write.md](references/write.md) §6). Crisis focuses get a real weighting modifier, not
the default base.

## 5. Verify

Re-run `ai_path_report.py --tag TAG`: 0 orphans in every state, no additive path modifiers, no
unreferenced flags, rule and wiring clean, a clean `mechanics` section (no burden whose cures are all
dead in a state, no cure focus at flat base, no AI-untakeable cure decision left without an AI route;
the `nothing relieves` line is inventory, not a failure — say in the PR which entries you judged
bonuses), and a clean `government` section (every walker branch asserts an in-range roster index, no
`change_leader_temp`, no unbounded party change, every scheduled date resolves to the person history
had). Then `validate_focus_tree.py --path .`, `validate_ai_path_rules.py --no-color` (the country
must no longer appear), and `validate_decisions.py` warning-group counts against a stashed baseline.

Then `git diff main -- common/ai_strategy/TAG.txt`: every added block's `enable` must name a
target, focus or flag the mod-wide files cannot express; anything on `surrender_progress`,
`enemies_strength_ratio` or bare `has_war` duplicates `MD_war_declaration_ai.txt` and is deleted.

## 6. Finish

Changelog: `Changelog.txt` carries one shared line under the current version's `Content:`,
`- Country AI path game rules standardised to Historical / alternate paths / Random Path / No Path:
TAG, TAG`. Append your TAG to it; create the line if the version has none. No per-country line.

PR body in the `/open-pr` step 5 format and nothing else: a single `### Changes` heading, one
plain bullet per player-visible outcome, no file paths, commit hashes, tables, testing section or
`## Bottom line`, then a blank line and `Closes #N` when the user gave an issue. Keep the body under
ten lines. Create the PR, or update title/body if one exists, and report the URL.

## House rules

- **Zero comments** in every file you touch — `.txt`, `.yml`, Python. Don't carry one over from a
  template, and don't add one to explain a killswitch, flag, weight or path. Delete any sitting
  inside a block you rewrite.
- Countries converted before this standard carry older shapes (`_AI_FOCUS` flags, evocative
  historical titles); don't copy them, and don't open their files to learn a shape.
- `git diff` before the PR and revert anything out of scope, including whitespace noise. Scope hooks
  with `pre-commit run --files <paths>`.
