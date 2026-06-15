# PR Description Conventions

How to write PR descriptions for Millennium Dawn. Applies to any agent (Claude, Copilot, manual) opening a PR via `gh pr create` or otherwise.

## Principles

1. **Lead with the user-visible change** in the first sentence. What does the player or modder notice that's different?
2. **Tight, not exhaustive.** 5–15 lines of body: what changed, why, what to watch for. Nothing more.
3. **No marketing.** No "comprehensive", "robust", "extensive". State facts.
4. **No exhaustive change logs.** The diff and commit history have that; the PR body summarises.
5. **No emoji, no AI attribution footers.** Per `~/.claude/CLAUDE.md`: never add "Generated with Claude Code" or co-author trailers.
6. **No "this PR ..." preamble.** The reader already knows it's a PR.
7. **No em dashes** (`—`). Use a period when the clause stands alone, a comma for participial phrases, a colon when introducing a list. Same rule applies to player-facing loc (see `.claude/rules/localisation-rules.md`).

## Structure

```
<title — under 70 chars, imperative mood, no period>

## Summary
- <1-3 bullets: what changed at a user-visible level>

## Why
<1-2 sentences explaining motivation when not obvious from the title>
(omit this section if the title already conveys the why)

## Risk / follow-up
- <Anything reviewers should pay attention to: scope of testing,
  known gaps, intentional debt, planned pt.2 work>
(omit if there's nothing notable)

## Test plan
- [ ] <One or two key smoke checks. Skip detailed enumeration.>
```

Section order is fixed. Omit a section by leaving it out entirely; don't write "N/A".

## Length budget

| Section          | Target                        |
| ---------------- | ----------------------------- |
| Title            | ≤ 70 chars                    |
| Summary          | 1–3 bullets, each ≤ 100 chars |
| Why              | 0–2 sentences                 |
| Risk / follow-up | 0–4 bullets                   |
| Test plan        | 0–3 checkboxes                |

If the PR is large (multiple subsystems, weeks of work), use one paragraph per subsystem under **Summary** rather than expanding the section. Still no exhaustive listing.

## What NOT to write

- "This PR adds X, Y, Z and improves A, B, C". Start with "Adds X." Drop "this PR".
- "Comprehensive overhaul" / "robust" / "complete refactor". Say what the actual change is.
- "All tests pass" / "Pre-commit hooks pass" — default state, CI shows it. Mention only when _manually_ verified or _bypassed_.
- File-by-file changelog — the diff has it. Summarise by subsystem if needed.
- "Co-Authored-By:" trailers and Generated-with-Claude footers. Forbidden globally per user CLAUDE.md.
- Lists of every commit on the branch.
- Restatements of the commit messages.
- Detailed test instructions when "load a save, do X" suffices.

## Examples

### Good (small feature)

```
Add weighted enemy selection to CPD AI peace offers

## Summary
- AI now prefers enemies near capitulation (surrender > 0.3) when
  choosing whom to offer peace to; falls back to random if none match.

## Risk / follow-up
- Targeting is two-pass random_enemy_country; not a top-1-of-N pick.
  In 50+ enemy wars the bias is statistical not deterministic.
```

### Good (bug fix)

```
Fix regime change in conditional peace deals

## Summary
- Regime change now installs the sender's exact subideology via
  change_ruling_party_effect (previous code read a non-existent
  variable and was a silent no-op).

## Test plan
- [ ] Sign a regime-change deal between two AIs of different ideology
- [ ] Confirm receiver's politics view shows the sender's party
```

### Good (large feature, multi-subsystem)

```
Conditional Peace Deals pt.1: terms, AI, validator

## Summary
- New negotiated peace system with 11 deal terms (state-level + country-
  level), AI deal builder, dynamic GUI status, and live tooltips.
- Built on top of MD's subideology, money, and white-peace systems.
- New tools/validation/validate_scripted_gui.py wired into pre-commit.

## Risk / follow-up
- Balance numbers are first-pass: reparations 0.05% GDP/wk capped at
  £15B; CPD_VP differential capped at ±150 in acceptance math.
- 35 pre-existing scripted-GUI bugs surfaced by the new validator (none
  CPD-related, separate cleanup work).
- AI subject initiation depends on autonomy state; overlord scans
  vassals with restricted autonomy.

## Test plan
- [ ] Build + sign a deal in every category (territorial, country
  action, ceasefire, empty deal blocked)
- [ ] Confirm war reparations show on payer's expense line and
  receiver's income line in the money UI
```

### Bad

```
This PR adds a comprehensive Conditional Peace Deal system with extensive
new functionality including but not limited to:

- Annexation, puppeting, demilitarization, liberation, resource rights
- Ceasefire, war reparations, forced neutrality, regime change, military basing, full puppet
- A robust AI deal builder
- A new validator
- Updated tooltips
- Bug fixes
- ...

All tests pass.

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
```

That breaks: AI attribution footers (forbidden), marketing language, exhaustive enumeration, redundant "this PR adds", redundant "all tests pass", emoji.

## How to enforce this

When an agent uses `gh pr create`, it reads this doc first if it's been recently touched on the branch; otherwise it applies the principles from memory. For repeat offenders, paste the relevant "Bad" example into your reply and reference this doc.
