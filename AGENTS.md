# AGENTS.md

Millennium Dawn is a Hearts of Iron IV mod (2000-present). Game data lives in
`common/`, `events/`, `history/`, `interface/`, and `gfx/`; Python tooling in `tools/`.

## Guardrails

- Edit and review English localisation only. Non-English `.yml` files are expected
  to diverge; do not modify them or flag missing, stale, or mismatched English keys.
- `resources/` is reference-only. Do not modify it unless explicitly asked.
- Keep edits within the requested scope.
- Verify identifiers against their definitions before using them: exact case, caller
  scope, and tooltip behavior. Existing usage is a clue, not proof.
- Every PR that changes game files adds exactly one BLUF `Changelog.txt` line under the
  current version, in an existing category. Skills may define their own exception.
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
- Name new identifiers in lowercase after any `TAG_` prefix, even when they wrap a
  mixed-case id (`cheat_party_western_autocracy`). Do not rename existing ids.
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

Read the relevant references before editing, not the entire catalog. Bare filenames
are under `.claude/docs/`.

- All scripting: `hoi4-data-structures.md` and `scripting-edge-cases.md`.
- Focuses: `focus-tree-reference.md` and `search-filters.md`.
- Events: `event-reference.md`. Decisions: `decision-reference.md`.
- Ideas: `idea-reference.md`. MIOs: `mio-reference.md`.
- AI strategies, templates, equipment: `ai-strategy-reference.md` and
  `ai-equipment-reference.md`.
- English strings: `localisation-rules.md`; party keys also need `party-loc-reference.md`.
- GUI: `scripted-gui-rules.md` and `scripted-gui-patterns.md`.
- UN voting, elections, recognition: `un-system-reference.md`. Formables, EU end-states,
  UAR, union cosmetics: `formable-reference.md`.
- Intelligence upgrades: `common/intelligence_agency_upgrades/README.md`.
  Loading and menu art: `loading-screen-system.md`.
- 3D models, entities, landmarks: `entity-system.md`. Power plants, energy techs,
  renewable balance: `energy-power-balance.md`.
- Hot paths or repeated branches: `performance-patterns.md` and `simplification-patterns.md`.
- Reviews: `known-false-positives.md` and `bug-patterns.md`. Renames: `refactor-checklist.md`.
- Subagents: `agent-conventions.md`.
- Other systems, art, OOBs, namelists, and content standards: `documentation-references.md`.
