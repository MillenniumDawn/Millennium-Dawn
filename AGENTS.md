# AGENTS.md

**NOTE**: Non-English localisation files are **not** currently mirrored against English — full translation is deferred to a later translation project. Do **not** modify them, and do **not** flag non-English `.yml` files in reviews, audits, or branch checks for missing, stale, or diverging keys relative to English. They are expected to be out of sync; any absent key degrades gracefully to the English string or an empty value. Only English keys (and the script objects that reference them) are in scope for review.

Millennium Dawn is a Hearts of Iron IV mod (2000-present). Key directories: `common/` (game data), `events/`, `localisation/` (English `.yml`, UTF-8 BOM), `history/`, `interface/`, `gfx/`, `tools/` (Python dev scripts).

**IMPORTANT**: The `resources/` directory is for reference material only. Do NOT modify files under `resources/` unless explicitly asked by the user.

## Validation & Tools

Validation runs on GitHub CI at PR time — don't run proactively. Standardization tools: `tools/standardization/` (see its README). Diff summary: `python3 tools/analysis/review_branch.py [base-branch]`.

**Never run `pre-commit run --all-files`.** The auto-fixers rewrite every matching file in the repo and leave hundreds of unrelated whitespace-only modifications in the worktree. Always scope runs to actually-modified files (`pre-commit run --files <path1> <path2>`) or rely on the normal `git commit` flow, which only feeds staged files to the hooks. If the branch already carries whitespace noise from a prior `--all-files` run, revert anything outside the task's scope before committing.

Pre-commit and CI run **different hook sets** — passing locally does not guarantee passing CI, and vice versa. Before wiring, judging, or debugging any validator, read `.claude/docs/validation-pipeline.md` (CI-only validators, pre-commit-only fixers, strictness divergences, vanilla-manifest regeneration, deprecation watch).

## Formatting

- Tabs for indentation; `{` on same line, `}` on own line at outer indent; 1 blank line between elements
- Simple checks on one line: `available = { has_country_flag = some_flag }`
- Comments are small, targeted, and load-bearing — comment policy: `.claude/rules/general-rules.md` (Python tooling: `tools/COMMENT_STYLE.md`)
- Remove unused/commented-out code
- `* 0.01` not `/ 100`; `if/else` not two `if` with complementary conditions
- Prefix country-specific variables with tag (e.g., `ISR_operation_success`); **snake_case** for all identifiers

## Performance

- Always `is_triggered_only = yes`; use `on_daily_TAG` not global triggers
- Replace `every_country`/`random_country` with array triggers
- Use dynamic modifiers sparingly; avoid `force_update_dynamic_modifier`

## Focus Trees

- ID: `TAG_focus_name`; use `relative_position_id`
- Always: logging, `ai_will_do = { base = N }`, `search_filters` (two-layer pattern, see `.claude/docs/search-filters.md`)
- Omit defaults: `cancel_if_invalid = yes`, `continue_if_invalid = no`, `available_if_capitulated = no`
- No empty `mutually_exclusive`/`available` blocks; limit permanent effects to 5
- Never `available = { always = no }` with a `bypass` — use matching condition
- High-cost focuses (cost >= 8, or >= 5 for mil/econ/research): add the standard bankruptcy guard (`has_active_mission = bankruptcy_incoming_collapse` → `factor = 0`) inside `ai_will_do` — block in `.claude/docs/focus-tree-reference.md`
- Ref: `.claude/docs/focus-tree-reference.md`

## Decisions

- Logging in `complete_effect`: `log = "[GetDateText]: [Root.GetName]: Decision DECISION_ID"`
- `ai_will_do = { base = N }` — `base` not `factor` at root
- Ref: `.claude/docs/decision-reference.md`

## Events

- Always `is_triggered_only = yes`; log only if option has effects; `major = yes` for news only
- Date-based events: owner-guard pattern in `common/scripted_effects/00_yearly_effects.txt`
- `add_building_construction` for `naval_base` requires `province = XXXXX`
- New subideology parties: register in `common/scripted_localisation/00_MD_politicsview_scripted_localisation.txt`
- Ref: `.claude/docs/event-reference.md`

## Ideas

- Always `picture = sprite_name` (no picture = blank icon); `original_tag` not `tag` in `allowed` blocks
- Category-specific `allowed`-block scoping and removable defaults (`cancel`, `on_add`, `allowed_civil_war`): `.claude/docs/idea-reference.md`

## MIOs

- ID: `TAG_organization_name`; always `allowed = { original_tag = TAG }`; sizing, trait grid, and `initial_trait` rules: `.claude/docs/mio-reference.md`

## Intelligence Agency Upgrades

New upgrades require wiring across five files — read `common/intelligence_agency_upgrades/README.md` before touching them.

## AI Strategies & Equipment

Unit production has three layers — threat gate (`ai_is_threatened`), role ratios, templates: `.claude/docs/ai-strategy-reference.md`. Equipment variants (role coverage, `target_variant`, CV-plane `ai_type`s, penalty cascades): `.claude/docs/ai-equipment-reference.md`. Both dirs have pre-commit-validated naming (role_ratio ↔ ai_templates roles, case-sensitive unit names, nation coverage) — read the doc before editing `common/ai_strategy/`, `common/ai_equipment/`, or `common/ai_templates/`.

## Shell Session

**Never reset the working directory.** No `cd` to another repo, drive, or temp path — the cwd is fixed for the session, and relative paths, follow-up edits, and tool snapshots assume it. Use absolute paths or per-command flags (`git -C <dir>`, `grep <path>`, `pre-commit run --files <path>`).

## Git Commits

- Do NOT add `Co-Authored-By` or sign commits — the project does not use commit signing

## Output Style

Keep all output token-efficient: conversation replies, agent hand-back reports, PR/issue/Changelog text, and commit messages alike.

- Lead with the conclusion (the answer, what changed, what was found). Cut preamble and restating the request.
- Report facts, not process. Skip "I read X, then I...", tool-by-tool narration, and self-congratulation.
- No padding confirmations ("As requested, I have successfully..."). State the result plainly.
- Prefer terse bullets and `file:line` references over prose paragraphs. Drop empty sections rather than writing "N/A".
- Be complete, not verbose: never drop a real finding, caveat, path, or identifier to save space. Trim words, not information.

## Key Resources

- [HOI4 Scripting](.claude/docs/hoi4-data-structures.md) | [Documentation Index](.claude/docs/documentation-references.md) (complete doc catalog)
- [Focus Trees](.claude/docs/focus-tree-reference.md) | [Events](.claude/docs/event-reference.md) | [Decisions](.claude/docs/decision-reference.md)
- [Ideas](.claude/docs/idea-reference.md) | [MIOs](.claude/docs/mio-reference.md) | [Search Filters](.claude/docs/search-filters.md)
- [AI Strategy](.claude/docs/ai-strategy-reference.md) | [AI Equipment](.claude/docs/ai-equipment-reference.md)
- [OOB & Equipment Variants](.claude/docs/oob-variants-reference.md) | [Namelists](.claude/docs/namelist-reference.md)
- [Diplomatic Actions](.claude/docs/diplomatic-action-reference.md) | [Content Guidelines](.claude/docs/content-guidelines.md)
- [UN System](.claude/docs/un-system-reference.md) (read before editing UN voting, elections, or recognition)
- [Faction Rules](.claude/docs/faction-rules.md) | [Typo Watchlist](.claude/docs/typo-watchlist.md)
- [Localisation Rules](.claude/docs/localisation-rules.md) (read when editing any `*_l_english.yml`)
- [Scripted GUI Rules](.claude/docs/scripted-gui-rules.md) + [Patterns](.claude/docs/scripted-gui-patterns.md) (read when editing `interface/*.gui` or `common/scripted_guis/`)
- [MD Custom Modifiers](.claude/docs/md-custom-modifiers.md) — non-vanilla modifier keys in `common/modifier_definitions/`
