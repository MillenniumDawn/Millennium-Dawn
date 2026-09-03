---
name: country-ai-path
description: 'Standardise one country''s TAG_ai_behavior AI path game rule for issue #3162 — rewrite the rule options and loc, rewire the global flags, re-own the focus weights, run the AI hardening pass, and open the PR. Use when asked to continue #3162 or work a country''s AI paths, e.g. "/country-ai-path CZE".'
disable-model-invocation: true
---

Continue issue #3162 (country AI path game rules), one country per chat.

**Syntax:** `/country-ai-path [country or TAG]` — e.g. `/country-ai-path CZE`. With no argument, pick
the target from the issue checklist.
Requested arguments: $ARGUMENTS

## Context budget

Focus trees run 8k–42k lines. **Never read one end to end, and never open another country's tree to
learn a shape.** Everything you need about the tree comes from `ai_path_report.py`; grep for the
specific lines it names. Templates for every artefact are in
[references/write.md](references/write.md).

## 1. Target

An argument names the country; find its checklist line. Otherwise `gh issue view 3162` → first
unchecked `- [ ]` in the Checklist. Its annotation names that country's known defects. Line numbers
in the checklist are stale — `grep TAG_ai_behavior`. If only "Cross-cutting" is left, say so and
stop.

Branch `3162-[country]-ai-paths` off main.

## 2. Facts

```bash
python tools/analysis/ai_path_report.py --tag TAG
```

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
python tools/standardization/apply_ai_path_weights.py --map <mapping>
```

Loc drafting and `_desc` sentence-count fixes go to a `localisation-editor` subagent on haiku.

**Rule standard.** Exactly `HISTORICAL` + one option per alt-history path + `RANDOM_PATH` +
`NO_PATH`, and `NO_PATH` is the `default = { }` block, listed last — a country the player never
configures runs unscripted. Delete `DEFAULT`; merge any duplicate `DEFAULT`/`HISTORICAL`. Write the
options fresh — don't recycle a stub's names or bucket count. The historical option's displayed text
is literally `"Historical"`; its `_desc` carries the country's history. Player-facing names, no
internal jargon, no "random" in a path name. Every `_desc` exactly two sentences, present tense
about the country, no hard dates, `§8…§!` on party names. Don't reorder the file — the alphabetical
pass is a separate cross-cutting item.

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
`common/ai_strategy/[TAG].txt` for gaps, especially a losing-war brake on any wargoal-generating
focus. Under historical AI the AI must stick to history: killswitch non-historical branch roots,
boost the historical branch.

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
bonuses), and a clean `government` section (every walker branch
asserts an in-range roster index, no `change_leader_temp`, no unbounded party change, every scheduled
date resolves to the person history had). Then `validate_focus_tree.py --path .`, and
`validate_decisions.py` warning-group counts against a stashed baseline.

## 6. Finish

PR (create, or update title/body if one exists), then tick the checklist line to `- [x]` and append
` (#PR)` via `gh issue edit 3162 --body-file` — re-fetch the body and change only that line. Report
the PR URL. The next country starts in a fresh chat with `/country-ai-path`.

## House rules

- **Zero comments** in every file you touch — `.txt`, `.yml`, Python. Don't carry one over from a
  template, and don't add one to explain a killswitch, flag, weight or path. Delete any sitting
  inside a block you rewrite.
- Belarus, Brazil, Bulgaria and Comoros are naming references only, never files to open. Cuba is a
  bad example. Countries converted before this standard carry older shapes; don't copy them.
- `git diff` before the PR and revert anything out of scope, including whitespace noise. Scope hooks
  with `pre-commit run --files <paths>`.
