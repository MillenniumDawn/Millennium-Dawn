---
name: update-claude
description: "Summarize the current session and propose improvements to CLAUDE.md, rules, docs, and skills, applying them after user confirmation. Use only when explicitly invoked."
disable-model-invocation: true
---

Summarize the current conversation and propose improvements to CLAUDE.md, rules, and skills.

**Syntax:** `/update-claude`

## Placement rules

- One home per rule: grep `.claude/` for an existing statement before adding anywhere; extend the existing home, and put at most a one-line pointer elsewhere.
- Always-loaded files (`CLAUDE.md`, `AGENTS.md`, `.claude/rules/*.md` without `paths:` frontmatter) hold only high-frequency, broadly-applicable rules in <=2 lines; worked examples and niche topics go to `.claude/docs/`.
- Every new `.claude/docs` file must be added to `.claude/docs/documentation-references.md`.
- New skills need frontmatter (`name` + a trigger-quality `description`); never add tables duplicating harness-injected lists.
- Topic guidance that should auto-load for certain files → `.claude/rules/*.md` with `paths:` glob frontmatter.

## Execution

### 1. Summarize the session

Review the full conversation and extract:

- **What was built or changed** — new files, refactored systems, validator additions, etc.
- **Patterns discovered** — recurring issues, anti-patterns, common mistakes found during the work.
- **Rules applied or created** — coding conventions, scripting patterns, or process rules that emerged.
- **Decisions made** — architectural choices, tradeoffs, why something was done a certain way.

### 2. Identify generalizable improvements

For each pattern or rule, assess whether it applies broadly or only to the specific task:

- **Broad rules** → `.claude/rules/general-rules.md` or `.claude/docs/localisation-rules.md`
- **Documentation references** → `.claude/docs/`
- **Skill improvements** → `.claude/skills/*/SKILL.md`
- **Project context** (non-obvious, persists across sessions) → memory

Filter ruthlessly — only propose additions that:

1. Cannot be derived by reading the current codebase
2. Would prevent a future mistake or speed up future work
3. Are general enough to apply beyond the specific files touched

### 3. Check existing documentation for staleness

Read the current state of:

- `CLAUDE.md` — is the skill table up to date?
- `.claude/rules/general-rules.md` — any rules that conflict with what we learned?
- `.claude/docs/localisation-rules.md` — any gaps?
- `AGENTS.md` — any conventions needing updates?

Flag anything outdated or contradicting current practice.

### 4. Propose changes

Present a structured list:

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

After presenting the proposals, ask the user which to apply. Then:

- Edit the relevant files directly
- Update `CLAUDE.md` skill table if new skills were added
- Save any memory items

## Important Notes

- Do NOT add implementation details, file paths, or architecture derivable from reading the code.
- Do NOT duplicate what's already in AGENTS.md or existing rules files.
- Focus on **why** not **what** — rules should explain the reasoning so edge cases can be judged.
- Keep rules concise — one pattern per entry, with a wrong/right example where helpful.
- Check for conflicts before adding — grep the rules files to avoid contradictions.
