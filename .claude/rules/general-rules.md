# Shared Guidance

Follow `AGENTS.md` for scope, KISS, formatting, validation, and BLUF output.
Keep this always-loaded file short. Scripting recipes belong in the references below,
not in another prompt.

## Read for the Task

- Scripting: `.claude/docs/hoi4-data-structures.md` for scope, variables, arrays, and math;
  `.claude/docs/scripting-edge-cases.md` for engine traps and guards.
- Repeated branches or hot paths: `.claude/docs/simplification-patterns.md` and
  `.claude/docs/performance-patterns.md`.
- Renames and shared-state changes: `.claude/docs/refactor-checklist.md`.
- Review: `.claude/docs/bug-patterns.md` and `.claude/docs/known-false-positives.md`.
- 3D models, entities, landmarks: `.claude/docs/entity-system.md`.
- Power plants, energy techs, renewable balance: `.claude/docs/energy-power-balance.md`.
- Other domains: the task links in `AGENTS.md` and `.claude/docs/documentation-references.md`.

Verify identifiers against their definitions before using them. Check exact case,
caller scope, and tooltip behavior. Existing usage is a clue, not proof of correctness.
