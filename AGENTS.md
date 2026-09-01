# AGENTS.md

**NOTE**: Non-English localisation files are **not** currently mirrored against English — full translation is deferred to a later translation project. Do **not** modify them, and do **not** flag non-English `.yml` files in reviews, audits, or branch checks for missing, stale, or diverging keys relative to English. They are expected to be out of sync; any absent key degrades gracefully to the English string or an empty value. Only English keys (and the script objects that reference them) are in scope for review.

Millennium Dawn is a Hearts of Iron IV mod (2000-present). Key directories: `common/` (game data), `events/`, `localisation/` (English `.yml`, UTF-8 BOM), `history/`, `interface/`, `gfx/`, `tools/` (Python dev scripts).

**IMPORTANT**: The `resources/` directory is for reference material only. Do NOT modify files under `resources/` unless explicitly asked by the user. It holds the vanilla docs the validators read plus the unsorted art dumps (`resources/README.md`); everything else retired from the mod lives in the [millennium-dawn-resources](https://github.com/MillenniumDawn/millennium-dawn-resources) repo.

## Validation & Tools

Validation runs on GitHub CI at PR time — don't run proactively. Standardization tools: `tools/standardization/` (see its README). Diff summary: `python3 tools/analysis/review_branch.py [base-branch]`.

**Never run `pre-commit run --all-files`.** The auto-fixers rewrite every matching file in the repo and leave hundreds of unrelated whitespace-only modifications in the worktree. Always scope runs to actually-modified files (`pre-commit run --files <path1> <path2>`) or rely on the normal `git commit` flow, which only feeds staged files to the hooks. If the branch already carries whitespace noise from a prior `--all-files` run, revert anything outside the task's scope before committing.

Pre-commit and CI run **different hook sets** — passing locally does not guarantee passing CI, and vice versa. Before wiring, judging, or debugging any validator, read `.claude/docs/validation-pipeline.md` (CI-only validators, pre-commit-only fixers, strictness divergences, vanilla-manifest regeneration, deprecation watch).

**The validator test suite must stay green permanently.** CI runs `python -m pytest` on every PR that touches `tools/` (`testpaths` in `pyproject.toml` is `tools/tests`). Do not introduce regressions into the testing schema. When a validator behavior change breaks a regression test, fix it in the same change: update the affected `*_test.py` to match the new correct behavior, or fix the validator if the test is right. Never delete or weaken a regression test to hide a failure — the suite is a gate, not a suggestion. Before merging any `tools/` change, run `python -m pytest` and confirm zero failures.

## Formatting

- Tabs for indentation; `{` on same line, `}` on own line at outer indent; 1 blank line between elements
- Simple checks on one line: `available = { has_country_flag = some_flag }`
- Comments are small, targeted, and load-bearing — comment policy: `.claude/rules/general-rules.md` (Python tooling: `tools/COMMENT_STYLE.md`)
- Remove unused/commented-out code
- `* 0.01` not `/ 100`; `if/else` not two `if` with complementary conditions
- Prefix country-specific variables with tag; `snake_case`
- Flag naming: `TAG_` single-nation, `GLOBAL_` global, bare domain prefix for any-nation
- Flag/var casing: `<TAG/GLOBAL/SYSTEMACRONYM>_name_of_entity`, `snake_case`
- Do not add flags that duplicate authoritative state. Use `has_idea`,
  `has_completed_focus`, variables, event targets, ideology, subject status,
  faction membership, and similar direct checks instead. Use a flag only for
  state that cannot be queried directly or must record a historical transition.

### Line endings in Python tooling

Every text-mode write in `tools/` must pass `newline=""`. Without it, Python's text mode turns each `\n` into `\r\n` on Windows, so a tool that rewrites a mod file hands back CRLF; `git add` normalises the index but the working tree stays CRLF, and the next commit touching that file gets bounced by the `mixed-line-ending` hook. `Path.write_text` is banned outright (its `newline` parameter only exists on 3.10+) — use an explicit `open(..., newline="")`. Writes to `.txt` use `encoding="utf-8"`, never `utf-8-sig`, which would inject a BOM. `tools/tests/text_write_newline_test.py` enforces both and carries a documented allowlist for the rare write that genuinely needs platform-native endings. Repo-wide, `.gitattributes` (`* text=auto eol=lf`) and `.editorconfig` keep everything else on LF.

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
- Money-spending focuses need bankruptcy guard in `ai_will_do` — see `.claude/docs/focus-tree-reference.md`
- Ref: `.claude/docs/focus-tree-reference.md`

## Decisions

- Logging: `log = "[GetDateText]: [Root.GetName]: Decision DECISION_ID"` as the first statement of every effect block the engine runs (`complete_effect`, `remove_effect`, `timeout_effect`, `cancel_effect`). A log nested inside an `if`/`hidden_effect` records which branch ran and stays there
- `ai_will_do = { base = N }` — `base` not `factor` at root
- Don't repeat category `allowed` in decisions — put nation gate on category, dynamic checks in `available`/`visible`
- AI-only decisions get **no localisation and no tooltip wrappers**. A decision is AI-only when an unconditional `is_ai = yes` sits at the top level of its `visible`/`available`/`allowed`, or its category is gated that way — no human sees it, so a loc key is dead weight and is flagged. An AI-only category's own key is flagged the same way. Write `check_variable` bare in such an `available` block: `custom_trigger_tooltip` / `custom_effect_tooltip` render to nobody, and the `available`-block tooltip checks skip AI-only decisions
- A category that becomes visible mid-game (flag, completed focus, idea, variable) should get `unlock_decision_category_tooltip = <category>` in whatever turns it on, or `unlock_decision_tooltip` on one of its decisions. Otherwise a whole tab appears with no indication of where it came from. Always-on and tag-gated categories need nothing. Audit with `validate_decisions.py --unannounced-categories` (opt-in, not in CI — 118 existing cases)
- An effect that sets a flag another decision's `visible`/`available` waits on has unlocked it. If the block already calls `unlock_decision_tooltip` for some, it must call it for all of them (`unannounced-decision-unlock`). Gates only count at depth 0 — inside a `NOT` the flag hides rather than unlocks
- Ref: `.claude/docs/decision-reference.md`

## Events

- Always `is_triggered_only = yes`; log only if option has effects; `major = yes` for news only
- Date-based events: owner-guard pattern in `common/scripted_effects/00_yearly_effects.txt`
- `add_building_construction` for `naval_base` requires `province = XXXXX`
- New subideology parties: register in `common/scripted_localisation/00_MD_politicsview_scripted_localisation.txt`
- Pure notifications get `minor_flavor = yes`. When many sources deliver to one country, batch them into a single report event instead of one event per delivery, and keep the payload at the delivery site (rules and traps: `.claude/docs/event-reference.md`)
- Describe an effect with `effect_tooltip = { <the real effect> }` before writing a new `custom_effect_tooltip` loc key
- Every `picture = GFX_*` must resolve to a sprite defined in `interface/*.gfx` — MD must not use vanilla event pictures. An undefined name is a commit blocker (`validate_events` → `missing-event-picture`), so grep `interface/` for it before writing it
- Ref: `.claude/docs/event-reference.md`

## Ideas

- Always `picture = sprite_name` (no picture = blank icon); `original_tag` not `tag` in `allowed` blocks; no `available` in `country`/`hidden_ideas`
- Category-specific `allowed`/`available`-block scoping and removable defaults (`cancel`, `on_add`, `allowed_civil_war`): `.claude/docs/idea-reference.md`

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
- Do NOT write `Changelog.txt` entries unless explicitly asked. A system new in 2.0.0 never needs an entry for its own changes
- Dev builds may invalidate saves — no legacy migration needed

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
- [UN System](.claude/docs/un-system-reference.md) (read before editing UN voting, elections, or recognition, or adding a Security Council / General Assembly resolution type)
- [Faction Rules](.claude/docs/faction-rules.md) | [Typo Watchlist](.claude/docs/typo-watchlist.md)
- [Localisation Rules](.claude/docs/localisation-rules.md) (read when editing any `*_l_english.yml`)
- [Scripted GUI Rules](.claude/docs/scripted-gui-rules.md) + [Patterns](.claude/docs/scripted-gui-patterns.md) (read when editing `interface/*.gui` or `common/scripted_guis/`)
- [MD Custom Modifiers](.claude/docs/md-custom-modifiers.md) — non-vanilla modifier keys in `common/modifier_definitions/`
