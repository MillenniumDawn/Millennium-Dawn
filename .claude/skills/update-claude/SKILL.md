Summarize the current conversation and propose improvements to CLAUDE.md, rules, and skills.

**Syntax:** `/update-claude`

## Execution

### 1. Summarize the session

Review the full conversation and extract:

- **What was built or changed** — new files, refactored systems, validator additions, etc.
- **Patterns discovered** — recurring issues, anti-patterns, common mistakes found during the work.
- **Rules applied or created** — any coding conventions, scripting patterns, or process rules that emerged.
- **Decisions made** — architectural choices, tradeoffs, why something was done a certain way.

### 2. Identify generalizable improvements

For each pattern or rule discovered, assess whether it applies broadly or only to the specific task:

- **Broad rules** go in `.claude/rules/general-rules.md` or `.claude/rules/localisation-rules.md`
- **Documentation references** go in `.claude/docs/`
- **Skill improvements** go in `.claude/skills/*/SKILL.md`
- **Project context** (non-obvious, persists across sessions) goes in memory

Filter ruthlessly — only propose additions that:

1. Cannot be derived by reading the current codebase
2. Would prevent a future mistake or speed up future work
3. Are general enough to apply beyond the specific files touched

### 3. Check existing documentation for staleness

Read the current state of:

- `CLAUDE.md` — is the skill table up to date?
- `.claude/rules/general-rules.md` — any rules that conflict with what we learned?
- `.claude/rules/localisation-rules.md` — any gaps?
- `AGENTS.md` — any conventions that need updating?

Flag anything that is outdated or contradicts current practice.

### 4. Propose changes

Present a structured list of proposed changes:

```
## Rules to add/update
- [file] — [what to add] — [why]

## Skills to add/update
- [skill name] — [what changed] — [why]

## Documentation to update
- [file] — [what's stale] — [what it should say]

## Memory to save
- [type] — [content] — [why it matters for future sessions]
```

### 5. Apply changes (with confirmation)

After presenting the proposals, ask the user which ones to apply. Then:

- Edit the relevant files directly
- Update `CLAUDE.md` skill table if new skills were added
- Save any memory items

## Important Notes

- Do NOT add implementation details, file paths, or architecture that can be derived from reading the code.
- Do NOT duplicate what's already in AGENTS.md or existing rules files.
- Focus on **why** not **what** — rules should explain the reasoning so edge cases can be judged.
- Keep rules concise — one pattern per entry, with a wrong/right example where helpful.
- Check for conflicts before adding — grep the rules files to avoid contradictions.
