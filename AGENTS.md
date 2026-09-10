# AGENTS.md

Millennium Dawn is a Hearts of Iron IV mod (2000-present). Game data lives in
`common/`, `events/`, `history/`, `interface/`, and `gfx/`; Python tooling in `tools/`.

## Guardrails

- Edit and review English localisation only. Non-English `.yml` files are expected
  to diverge; do not modify them or flag missing, stale, or mismatched English keys.
- `resources/` is reference-only. Do not modify it unless explicitly asked.
- Keep edits within the requested scope. Do not add `Changelog.txt` entries unless asked.
- Do not add attribution trailers or tool-generated footers, or sign commits.
- Keep the session working directory fixed. Use absolute paths or per-command flags.
- Development builds may invalidate saves. Do not add legacy migration support.

## KISS: Keep It Simple

- Optimize for the next human reader. Use plain names, local logic, and existing patterns.
- Build only what the current task needs. No speculative abstractions, configuration,
  fallbacks, or compatibility layers.
- Reuse existing code and state. Add a helper only when it removes meaningful duplication
  or makes a required boundary clearer. A little clear duplication beats indirection.
- Do not add flags that duplicate queryable game state. Record only otherwise unavailable
  state or a historical transition.
- Keep behavior-preserving cleanup separate from gameplay changes. Remove dead code
  introduced or exposed by the change, without refactoring unrelated systems.
- Default to no comments. Explain only a non-obvious reason, in one short line.

## Validation

- Content validation runs in GitHub CI at PR time. Do not run it proactively.
- Never run `pre-commit run --all-files`. Use normal staged-file hooks or
  `pre-commit run --files <changed paths>`; do not include unrelated formatter edits.
- Before changing or debugging validation, read
  [Validation Pipeline](.claude/docs/validation-pipeline.md). CI and hooks differ.
- For `tools/` changes, run `python -m pytest` before merge. Fix regressions in the
  same change; never delete, skip, or weaken tests to pass.
- For docs-site changes, follow [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md).
- Standardization: [tools/standardization/README.md](tools/standardization/README.md).
  Branch summary: `python3 tools/analysis/review_branch.py [base-branch]`.

## Formatting

- Script: tabs, opening brace on the same line, closing brace at the outer indent,
  one blank line between elements. Keep simple checks on one line.
- `.txt`: UTF-8 without BOM. English localisation `.yml`: UTF-8 with BOM.
- Match surrounding style. Naming and examples:
  [Code Stylization Guide](docs/src/content/resources/code-stylization-guide.md).
- Python writes and review rules: [tools/README.md](tools/README.md).

## Output: BLUF (Bottom Line Up Front)

- Start replies, handoffs, reviews, and PR descriptions with the conclusion.
- Give only supporting facts: findings, changed behavior, blockers, and verification.
  Cite code as `path:line`. Say what failed or was not checked.
- Skip preambles, praise, tool-by-tool narration, empty sections, and repeated summaries.
  Trim words, not findings or caveats.
- PR bodies start with `## Bottom line`. End chat replies, handoffs, and PR bodies
  with `BLUF`. Do not put that marker in code, game strings, or player guides.
- Docs lead with the answer or action where useful. Procedures keep their natural order.
  Use plain American English, short sentences, and no em dashes.

## Read for the Task

Read the relevant references before editing, not the entire catalog. Paths below are
under `.claude/docs/` unless stated otherwise.

- All scripting: [Data Structures](.claude/docs/hoi4-data-structures.md) and
  [Scripting Edge Cases](.claude/docs/scripting-edge-cases.md).
- Focuses: [Focus Trees](.claude/docs/focus-tree-reference.md) and
  [Search Filters](.claude/docs/search-filters.md).
- Events: [Events](.claude/docs/event-reference.md). Decisions:
  [Decisions](.claude/docs/decision-reference.md).
- Ideas: [Ideas](.claude/docs/idea-reference.md). MIOs: [MIOs](.claude/docs/mio-reference.md).
- AI strategies/templates/equipment: [AI Strategy](.claude/docs/ai-strategy-reference.md)
  and [AI Equipment](.claude/docs/ai-equipment-reference.md).
- English strings: [Localisation](.claude/docs/localisation-rules.md); party keys also
  need [Party Localisation](.claude/docs/party-loc-reference.md).
- GUI: [Rules](.claude/docs/scripted-gui-rules.md) and
  [Patterns](.claude/docs/scripted-gui-patterns.md).
- UN voting/elections/recognition: [UN System](.claude/docs/un-system-reference.md).
  Formables, EU end-states, UAR, union cosmetics: [Formables](.claude/docs/formable-reference.md).
- Intelligence upgrades: [Upgrade README](common/intelligence_agency_upgrades/README.md).
  Loading/menu art: [Loading Screens](.claude/docs/loading-screen-system.md).
- Hot paths or repeated branches: [Performance](.claude/docs/performance-patterns.md)
  and [Simplification](.claude/docs/simplification-patterns.md).
- Reviews: [Known False Positives](.claude/docs/known-false-positives.md) and
  [Bug Patterns](.claude/docs/bug-patterns.md). Renames: [Refactor Checklist](.claude/docs/refactor-checklist.md).
- Subagents: [Agent Conventions](.claude/docs/agent-conventions.md).
- Other systems, art, OOBs, namelists, and content standards:
  [Documentation Index](.claude/docs/documentation-references.md).
