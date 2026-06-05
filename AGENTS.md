# AGENTS.md

**NOTE**: Non-English localisation files are managed via Paratranz — never modify them.

Millennium Dawn is a Hearts of Iron IV mod (2000-present). Key directories: `common/` (game data), `events/`, `localisation/` (English `.yml`, UTF-8 BOM), `history/`, `interface/`, `gfx/`, `tools/` (Python dev scripts).

**IMPORTANT**: The `resources/` directory is for reference material only. Do NOT modify files under `resources/` unless explicitly asked by the user.

## Validation & Tools

Validation runs on GitHub CI at PR time — don't run proactively. Standardization tools: `tools/standardization/` (see its README). Diff summary: `python3 tools/analysis/review_branch.py [base-branch]`.

**Never run `pre-commit run --all-files`.** Pre-commit's auto-fixers (trailing-whitespace, end-of-file-fixer, mixed-line-ending, fix-byte-order-marker) rewrite every matching file in the repo and leave hundreds of unrelated whitespace-only modifications in the worktree. Always scope runs to actually-modified files: `pre-commit run --files <path1> <path2>`, or rely on the normal `git commit` flow which only feeds staged files to the hooks. The branch you are on may already carry whitespace noise from a prior `--all-files` run — if it does, revert anything outside the scope of the task before committing.

### Pre-commit vs CI divergence

Pre-commit and CI do not run the same hook set. Things that pass locally can still fail CI, and vice versa:

- `coding_standards.py`, `check_basic_style.py`, `check_common_mistakes.py` are `stages: [manual]` in pre-commit but **unconditional** in `.github/workflows/coding-pipeline.yml`. They will not run on `git commit`; they will run on PRs. To preview locally: `pre-commit run --hook-stage manual --files <paths>`.
- `validate_ai_equipment.py` runs without `--strict` locally (coverage gaps would block all commits) but **with** `--strict` on CI. Equipment-coverage gaps that are tolerated locally will fail PR validation.
- `check_braces.py`, `fix_loc_yaml.py`, `validate_localization_encoding.py`, `validate_mod_encoding.py` are **pre-commit-only** — never run on CI. Web-UI edits or contributors with hooks disabled can land broken braces or BOM regressions.
- `validate_defines.py` runs on pre-commit but is **skipped on CI** (needs the vanilla `00_defines.lua` not present in the runner). Dead-renamed defines slip through CI unless caught locally.
- `validate_ideas.py` is wired into both pre-commit (`--staged --strict`) and CI (`strict: false`, informational) until the ~30 pre-existing undefined-idea references on main are triaged. Once cleared, flip the CI entry to strict.
- `validate_unused_textures.py` is wired into pre-commit as `stages: [manual]` and into CI as informational (`strict: false`). The repo currently carries ~22k unreferenced textures — informational mode keeps the audit visible without blocking PRs.
- `validate_set_variables.py` is intentionally **not wired** anywhere. False-positive volume at repo scale (across the full common/events/history scope) makes it noisy as a gate. Run it manually against a specific variable when needed.

### Tooling deprecation watch

- `pre-commit/mirrors-prettier` is archived upstream. Maintained fork: `rbubley/mirrors-prettier`. Migrate next time the prettier pin needs touching.

## Formatting

- Tabs for indentation; `{` on same line, `}` on own line at outer indent; 1 blank line between elements
- Simple checks on one line: `available = { has_country_flag = some_flag }`
- Comments are small, targeted, and load-bearing: add one only when the _why_ is non-obvious and removing it would lose real information, and keep it to a single line. Cut anything that restates the code, narrates a change, points at callers, or justifies a mechanic in flavour prose (see `.claude/rules/general-rules.md`; Python tooling: `tools/COMMENT_STYLE.md`)
- Remove unused/commented-out code
- `* 0.01` not `/ 100`; `if/else` not two `if` with complementary conditions
- Prefix country-specific variables with tag (e.g., `ISR_operation_success`)
- **snake_case** for all identifiers

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
- High-cost focuses (cost >= 8, or >= 5 for mil/econ/research): add `NOT = { has_active_mission = bankruptcy_incoming_collapse }` in `available`
- Ref: `.claude/docs/focus-tree-reference.md`

## Decisions

- Logging in `complete_effect`: `log = "[GetDateText]: [Root.GetName]: Decision DECISION_ID"`
- `ai_will_do = { base = N }` — `base` not `factor` at root
- Ref: `.claude/docs/decision-reference.md`

## Events

- Always `is_triggered_only = yes`; log only if option has effects; `major = yes` for news only
- Date-based events: use `common/scripted_effects/00_yearly_effects.txt` with owner-guard pattern
- Cross-country events: add `TT_IF_THEY_ACCEPT` tooltip; add `TT_IF_THEY_REJECT` only if rejection has consequences (see `.claude/rules/general-rules.md`)
- `add_building_construction` for `naval_base` requires `province = XXXXX`
- New subideology parties: register in `common/scripted_localisation/00_subideology_scripted_localisation.txt`
- Ref: `.claude/docs/event-reference.md`

## Ideas

- Always include `picture = sprite_name` — ideas without a picture show a blank icon
- Include `allowed_civil_war = { always = yes }` for civil war tags
- Use `original_tag` not `tag` in `allowed` blocks
- `country`/`hidden_ideas` categories: remove `allowed = { always = no }` (default) and `allowed = { tag = TAG }`; other categories: `allowed` is load-bearing
- Remove `cancel = { always = no }` and empty `on_add = { log = "" }`
- Ref: `.claude/docs/idea-reference.md`

## MIOs

- ID: `TAG_organization_name`; always `allowed = { original_tag = TAG }`
- `task_capacity` proportional to nation size (10-25)
- Trait grid `y = 0..9`; add `initial_trait` for defining bonus
- Ref: `.claude/docs/mio-reference.md`

## Intelligence Agency Upgrades

New upgrades require wiring across five files: definition, on_actions registry (four arrays + bump `resize_array size =`), loc triple (`id`/`_name`/`_gfx`), scripted_gui prereqs, sprite in `interface/*.gfx`. See `common/intelligence_agency_upgrades/README.md`.

## AI Strategies & Equipment

Unit production has three layers: building gate (`AI_is_threatened`), role ratios, templates. See `.claude/docs/ai-strategy-reference.md`.

- `role_ratio id` must match `role` in `common/ai_templates/` (validated by pre-commit hook)
- Unit names are case-sensitive (validated by pre-commit hook)
- Subject/puppet nations always get `AI_is_threatened`
- `give_AI_templates` uses `division_template` with `has_template` guards

Equipment variants (`common/ai_equipment/`): see `.claude/docs/ai-equipment-reference.md`. Key rules:

- Every role template needs `category`, `roles`, top-level `priority`; every design needs `target_variant` with `type`, `match_value`, `modules`
- Nations blocked from generic files must have all roles covered in custom/shared files (validated by pre-commit hook)
- CV planes: `ai_type` must be one of `cv_fighter`/`cv_interceptor`/`cv_cas`/`cv_naval_bomber`/`cv_suicide`
- `equipment_variant_production_factor` penalties cascade to subtypes — keep base penalties <= -25%

## Shell Session

- **Never reset the working directory.** Do not `cd` to a different repo, drive, or temp path "just to run one command." The working directory is fixed for the session; relative paths and follow-up edits assume it. Use absolute paths or per-command flags (e.g., `git -C <dir>`, `grep <path>`, `pre-commit run --files <path>`) instead. Even commands that appear to recover (`cd <repo-root> && ...`) have already broken the invariant for any tool that snapshots cwd before the command runs.

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

- [HOI4 Scripting](.claude/docs/hoi4-data-structures.md) | [Documentation Index](.claude/docs/documentation-references.md)
- [Focus Trees](.claude/docs/focus-tree-reference.md) | [Events](.claude/docs/event-reference.md) | [Decisions](.claude/docs/decision-reference.md)
- [Ideas](.claude/docs/idea-reference.md) | [MIOs](.claude/docs/mio-reference.md) | [Search Filters](.claude/docs/search-filters.md)
- [AI Strategy](.claude/docs/ai-strategy-reference.md) | [AI Equipment](.claude/docs/ai-equipment-reference.md)
- [Diplomatic Actions](.claude/docs/diplomatic-action-reference.md) | [Content Guidelines](.claude/docs/content-guidelines.md)
- [Faction Rules](.claude/docs/faction-rules.md) | [Typo Watchlist](.claude/docs/typo-watchlist.md)
- [MD Custom Modifiers](.claude/docs/md-custom-modifiers.md) — full list of non-vanilla modifier keys defined in `common/modifier_definitions/`
