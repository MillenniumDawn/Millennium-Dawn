# Validator Check Notes

What each validator enforces where the reason is not obvious from its code: engine
behavior, exemptions, and known gaps. Search for the script or category name. Do not
read this file whole. Wiring and strictness are in `validator_batches.py`, and open
backlogs live in GitHub issues, not here. Pipeline rules:
[Validation Pipeline](validation-pipeline.md).

## CI jobs

- `test-suite.yml` checks out the live PR head and holds no write credentials until the
  `report` job. A head that predates the CI tooling contract stops with one error asking
  to merge main.
- `detect-changes` classifies the diff with `collect_changed_files.py` and
  `change_groups.py`. `validate-paths` reads the git index only. `prepare-workspace`
  packs the sparse content tree into one artifact for the `mod-tests` batches (core,
  targeted-a, targeted-b). That workspace has no `.git`, no `map/`, and only `gfx/flags`
  and `gfx/interface/decisions` from the art trees.
- `tools-tests` runs pytest on three OSes, coverage on Linux only. `tools-quality` runs
  ruff, Black, pylint, mypy, jscpd, the staged-validator integration, and
  `validate_tools.py`.
- `workflow_dispatch` takes `pr_number`, `head_sha`, and `base_sha`. It skips the
  diff-scoped style sections.
- `nightly-pr-validation.yml` re-dispatches the suite for open PRs with no successful
  run on their current head and base. `validator-cache.yml` rebuilds the `main` baseline.
- `changelog-conflict-fixer.yml` merges main into same-repo PRs whose only conflict is
  `Changelog.txt`, then dispatches the suite. `changelog-lint.yml` checks entry order.
  `python3 tools/merge_changelog.py --fix` repairs it.
- The report posts one PR comment: findings new against the main baseline first, then
  findings in files the PR touched. A clean run removes the older bot comment. Section
  titles derive from artifact directory names, so those slugs must not change.
- On CI the batch runner gives each validator the whole CPU budget. Off CI the product
  of validators and workers is capped.

## Encoding and loc format

- `fix_loc_yaml.py` fixes on commit and checks in CI, so a bare `"` inside a value fails
  CI for contributors without hooks. `validate_localization_encoding.py`,
  `validate_mod_encoding.py`, and `validate_txt_encoding.py` run in CI for the same reason.
- `validate_txt_encoding.py` scans shipped `.txt` roots only. Script `.txt` must not
  carry a BOM.
- `validate_defines.py` reads the live install on commit and `vanilla_defines.txt` in CI.

## validate_ai_path_rules.py

- `ai-path-rule-missing`, `ai-path-rule-incomplete` (WARNING): a focus tree whose
  `country` block names exactly one tag that owns a state at start needs a
  `TAG_ai_behavior` rule with a `HISTORICAL` option and a `default` block.
- Out of scope: shared trees, and tags that only spawn later.

## validate_building_guards.py

- `damage_building` or `remove_building` against a building the state lacks spams
  `error.log`. The guard must name the same building as the effect's `type`.
- Accepted guards: a count comparison in an enclosing `limit` (also on `random_owned_state`
  and similar, and through `meta_effect` wrappers), `non_damaged_building_level`,
  `any_province_building_level`, `has_building`, `num_of_buildings`, a `random_list`
  bucket zeroed by `modifier = { factor = 0  X < N }`, or an `any_core_state`-style
  pre-selection.
- Not guards: a `limit` on something else (an idea, a flag), and `trigger`, `available`,
  `visible`, `allowed`. `effect_tooltip` subtrees are skipped.

## validate_characters.py

- `trait-role-mismatch` (ERROR): a unit leader trait from the wrong branch (`land`,
  `navy`, `operative`) loads silently and never applies. Only the branch is compared.
  Corps commander traits on field marshals are not a finding, since vanilla does it.
- `undefined-unit-leader-trait` (WARNING). `common/unit_leader` is `replace_path`'d, so
  the mod's files are the whole trait universe.
- Advisor slots: each slot owns a pool file in `common/country_leader/`
  (`01_high_command_traits.txt`, `01_army_chief_traits.txt`, `01_navy_chief_traits.txt`,
  `01_air_chief_traits.txt`). A trait belongs to the pool of its file, not its name
  prefix. New pool: add the file and one `SLOT_POOL_FILES` entry.
- `advisor-trait-slot-mismatch`, `undefined-advisor-trait`, `unit-leader-trait-on-advisor`,
  `advisor-trait-on-unit-leader`, `advisor-pool-file-missing` are ERROR. Chiefs scale
  5/10/15% and high command 4/8/12%, so a crossed assignment is a sprite and tier defect.
- `TAG_`-prefixed traits are exempt from the slot check. Traits outside the four pool
  files are unclassified. `country_leader` blocks are not scanned.

## validate_country_names.py

- `country-names-missing` (ERROR): every tag defined before `dynamic_tags = yes` needs a
  top-level block in `common/names/`, or the game logs an error and uses `default`
  names. Aliases are not checked.

## validate_decisions.py

- `missing-decision-log` (ERROR): a `complete_effect` with effects but no `log =`.
- `undefined-unlock-tooltip-target` (ERROR): `unlock_decision_tooltip` and
  `unlock_decision_category_tooltip` name a definition the engine looks up at render. A
  stale name leaves the tooltip empty while the unlock still happens. The category form
  takes the bare token only.
- `validate_formable_commitment_sync` (ERROR): contract in `formable-reference.md`.
- `validate_random_seed` (ERROR): covers `random_list` and bare `random`. Exempts
  `fire_only_once = yes`. Only an absent `fixed_random_seed` is a finding.
- `missing-decision-localisation` (WARNING): a name key, `name`/`desc` override, or
  `custom_cost_text` that resolves to nothing. `<id>_desc` is not required.
- `ai-only-decision-localisation` (WARNING): a key that exists for an AI-only decision or
  category. AI-only means an unconditional depth-0 `is_ai = yes` in `visible`,
  `available`, or `allowed`, or a category gated that way. `is_ai = yes` nested in `OR`,
  `if`, or a tag scope is conditional. `custom_cost_text` and categories named by
  `unlock_decision_category_tooltip` are exempt.
- `missing-decision-icon` (WARNING, opt-in `--missing-icons`, not in CI): a decision
  `icon = X` passes if `X`, `GFX_decision_X`, or `GFX_X` exists. A category `icon = X`
  takes `GFX_decision_category_` instead. A category `picture` is the full sprite name.
  Needs a live install to avoid vanilla noise. The flag also drives the focus-tree check.
- `unannounced-decision-category` (WARNING, opt-in `--unannounced-categories`, passed in
  CI): a category whose `visible` waits on a flag, focus, idea, or variable, with no
  `unlock_decision_category_tooltip` naming it and no `unlock_decision_tooltip` naming
  one of its decisions. `unannounced_category_exempt` in the config lists categories
  whose gate is granted only at game start, and balance of power categories that have
  no name key to render.
- `decision-icon-slot-mismatch` (ERROR): the decision UI draws icons at native texture
  size, so art for one slot renders wrong in another. Bands by longest edge: decision icon
  up to 36, category icon 48 to 79, picture 80 and up. Sizes in the gaps are not reported.
  `slot_exempt_sprites` in the config are accepted anywhere.
  `tools/assets/resize_decision_icons.py --dry-run` shows the fix: it resizes in place
  when nothing else uses the texture, else writes a resized sibling and repoints. It
  skips vanilla art.
- `category-desc-image-overlap` (WARNING): a category `<id>_desc` that opens with a
  `£icon` draws the art at native size and can cover the header. Minimum leading `\n`:
  `ceil((height / 2 - 22) / 16)`. Not confirmed pixel for pixel in game.

## validate_dynamic_modifier_guards.py

- `remove_dynamic_modifier` on a scope not carrying the modifier logs an error and does
  nothing. The removal must sit under a `limit` holding `has_dynamic_modifier` for the
  same modifier, at any depth, same-scope or re-entering the target scope.
- A flag, idea, or variable proxy is still a finding. `trigger`, `available`, `visible`,
  and `allowed` are not guards. `has_dynamic_modifier`'s `scope =` is ignored.

## validate_equipment_variants.py

- `equipment-variant-unavailable` (ERROR): an effect sequence creates a named variant
  without an assured enabling technology, then uses it in `add_equipment_production`,
  `create_ship`, or `add_equipment_to_stockpile`. Technologies resolve through
  `enable_equipments`, not by matching ids.
- It follows effect order, direct technology guards, conditional grants, and
  `allow_without_tech = yes`. Country history through the earliest bookmark supplies
  starting technologies only for proven recipients. Tooltip effects and foreign scopes
  cannot supply an unlock.
- It does not follow scripted-effect calls, cross-file variant creation, focus
  prerequisites, or dynamic names, so findings need review.

## validate_events.py

- `date-gated-not-scheduled` (ERROR): MD fires historical events from
  `common/scripted_effects/00_yearly_effects.txt`, and the event's own `date >` is only
  a guard. An event with the guard and no schedule is dead content. Exempt: events
  reachable from a scheduled ancestor, fires from focuses or decisions, `random_events`
  pools, and chance-rolled `random` polls. A `date <` bound alone is an expiry guard.
- `event-fire-type-mismatch`, `malformed-event-fire` (ERROR).
- `event-option-log-without-effect` (ERROR): an option holding only `name`, `log`,
  `trigger`, and `ai_chance`. `hidden_effect`, scope blocks, and tooltips count as
  effects. `tools/linting/fix_event_option_logs.py` shares the detection and deletes the
  lines.
- `event-ai-chance-ignores-cost` (WARNING, off by default, `--check-ai-chance-costs`,
  tracked in #5106): in an event with two or more options, an option that charges its
  own country and whose `ai_chance` has no `modifier`. Costs: lowering `treasury` or
  `int_investments`, raising `debt`, moving a tax rate, or negative political power,
  stability, or war support, directly or through a scripted effect. Costs inside foreign
  scopes are skipped. The "decline" option counts when declining is what costs.
  - Known gaps: a stored variable whose negative value comes from math or an array reads
    as positive, a `[TOKEN]` in a `meta_effect` body is not substituted, and
    single-option events are never reported.
  - Fix pattern: `event-reference.md`, "Cost-aware AI weights".
- Event pictures: both event windows draw `event_picture` at native size.
  `event-picture-format-mismatch` (ERROR) classifies by aspect ratio, not name: country
  art up to 1.45, news art from 2.0. The band between is not reported. For a sprite
  shared by both windows, split it into a `news_`-prefixed and an unprefixed pair
  instead of editing call sites.
- `hidden-event-picture`, `news-event-picture-omitted`,
  `placeholder-event-picture` (ERROR). Only pictures at depth 0 of the event body count,
  so leader portraits inside `immediate` do not.

## validate_file_paths.py

- Windows resolves paths case-insensitively and Linux does not. A mod path that differs
  from a vanilla path only in case replaces it on Windows and loads beside it on Linux,
  so the platforms hash different file sets and cannot play multiplayer together.
- The checksummed set is `common/**/{*.txt,*.lua}`, `events/**/*.txt`,
  `history/**/*.txt`, and `map/**/{*.txt,*.map,*.bmp,*.csv}`. Collisions inside a
  `replace_path`'d directory are WARNING. `replace_path` is not recursive.
- It reads path names from the git index against `vanilla_paths.txt`. The in-mod case
  check overlaps the `check-case-conflict` hook on purpose.
- `source-art-format` (ERROR): under `gfx/`, `.psd`, `.xcf`, and `.tif` cannot load, and
  `.png` and `.jpg` load uncompressed without mipmaps. Convert with
  `tools/assets/md_art_convert.py`. `map/` is out of scope.

## validate_focus_tree.py

- `relative-position-forward-ref`, `relative-position-missing-target` (ERROR): the engine
  resolves focus positions in file order. Targets in another file are not checked.
- Focus geometry (WARNING): see the
  [coordinate policy](../../tools/validation/README.md#focus-coordinate-warnings).
- `focus-allow-branch-leak` (WARNING): a focus with its own `allow_branch` under an
  ancestor whose `allow_branch` can hide the branch, without repeating its conditions.

## validate_gfx_references.py

- The unused-sprite check is opt-in behind `--report-unused`. `MD_GFX_HIDE_UNUSED=1`
  hides the orphan list and keeps the case and duplicate findings.
- Sprite names the engine builds from mod data are resolved into the reference set, so a
  sprite still reports once its backing declaration is deleted: `GFX_<FOCUS_FILTER_X>`,
  `GFX_EMI_<module>`, `GFX_SMI_<module>`,
  `GFX_unit_<subunit|category>_icon_{small,medium}[_white|_black]`,
  `GFX_<TAG|graphical_culture>_ace_<m|f>_<n>`, and anything a `[...]` template in
  scripted loc or a scripted-GUI `image` can build. A template with under four literal
  characters after `GFX_` is rejected.
- True exemptions: equipment, tech, and designer icons, and any name vanilla also defines.
- `sprite-ref-case` (ERROR): an English `£name` that matches a sprite only
  case-insensitively, so the icon is missing on Linux. `unused-sprite-case` (WARNING): a
  sprite whose only reference is miscased.
- `duplicate-sprite`, `case-variant-sprite` (WARNING): the message says whether the blocks
  share a texture. Unquoted `texturefile` values are read the same as quoted ones.
- `raw-icon-path` (ERROR): `icon =` inside `create_equipment_variant`, or an entry in a
  `graphic_db` `icons = { }` block, that is a texture path instead of a `GFX_` sprite.
  Quoted and unquoted, slash or backslash. Comments and focus-tree `icon =` are ignored.
  `_documentation.info` is not scanned. Raw plane paths crash the macOS air battle window.
- `undefined-font` (ERROR): a `.gui` font naming no `bitmapfont` renders in the default
  face. Vanilla names come from an install or `vanilla_fonts.txt`.
- Sprite names in generator-managed `.gfx` files come from the texture filename. Rename
  the texture and update `texturefile`, not the entry.

## validate_ideas.py

- Missing-icon audit (WARNING, always on): the sprite is undefined, exists only under a
  different case, or resolves to placeholder art (`_PLACEHOLDER_TEXTURES`). A mod
  placeholder that shadows a vanilla sprite name still reports.
- `loc-key-collision` (WARNING): an idea's `name = X` override resolves its name to `X`
  and its description to `X_desc`. When `X` is also a focus or decision id and resolves
  in English loc, one string silently overrides the other. Intentional sharing is allowed.
- `idea-quality` (WARNING): an idea `equipment_bonus` without `instant = yes` applies only
  to variants created afterwards. Exempt name prefixes go in
  `equipment_bonus_instant_exempt`.
- `bonus-type-archetype-stack` (ERROR, also in `validate_mios.py`): a nested
  `equipment_bonus` naming a type category (`carrier`) and a child archetype of that type
  with the same modifier stacks twice. Helicopter operators are `type = carrier`.
  Distinct stats on the child are allowed.

## validate_localisation.py and validate_scripted_localisation.py

- `loc-em-dash`, `loc-backtick-apostrophe` (WARNING), and `loc-unbalanced-quote` (ERROR)
  scan only the quoted values in `localisation/english/`. Inch marks and quotes spanning
  paragraphs are expected false positives of the quote check.
- `loc-typo-watchlist` (ERROR): `typo-watchlist.md` entries in prose, excluding keys and
  runtime references. `it's` and `civilisation` are excluded as context-dependent.
- Prose warnings (repeated word, tripled letter, exact placeholder, dangling
  description): see `localisation-rules.md`.
- `loc-getter-spelling` (WARNING): a `[SCOPE.Member]` whose member is not a defined
  scripted loc is checked against `loc_objects_documentation.md`. Built-in getters match
  case-insensitively in game, so a case variant is a style finding. An unknown getter
  renders empty and logs nothing.

## validate_math_expressions.py

- `math-sibling-operator`, `math-from-read` (ERROR). The traps are in
  `hoi4-data-structures.md`. Plain `set_temp_variable = { x = FROM.y }` copies are valid.

## validate_mesh_textures.py

- Commit-stage only, since the CI workspace ships no models. `mesh-texture-empty`,
  `mesh-texture-missing` (ERROR). Lookup rules: `entity-system.md`. The missing-name
  check needs a HoI4 install and logs a skip without one.

## validate_mio_icons.py

- The engine draws an equipment group as `GFX_<group>` and an archetype or type category
  under `equipment_type` as `GFX_military_industrial_organization_<token>`. A missing
  group sprite logs an error on every MIO refresh.
- `mio-equipment-group-icon` fires once at the group definition, `mio-equipment-type-icon`
  on each org block naming a non-group token. Both ERROR. `limit_to_equipment_type`
  carries no icon.

## validate_mios.py

- Gates: org-id format, `allowed = { original_tag = TAG }`, non-empty `on_complete`,
  initial-trait naming, and trait-grid x above 9. Negative x is the standard
  first column. `generic_` orgs and `generic_` initial traits are exempt.
- Trait geometry (ERROR): `trait-geometry-parent-row` (child on or above its parent's
  row), `trait-geometry-mutex-row` (mutually exclusive traits on different rows),
  `trait-geometry-mutex-parents` (a `parent` or `all_parents` list naming two mutually
  exclusive traits locks the child out, `any_parent` is the fix). Unresolvable anchors
  and cycles report nothing.
- Localisation (ERROR): `header-text-not-tokenized` (a literal quoted `tree_header_text`
  is printed verbatim and cannot be translated), `header-text-loc-missing`,
  `trait-loc-missing`. Key resolution mirrors the engine: `TAG_<key>` wins, else the
  bare key.
- Dead `equipment_bonus` (ERROR): a bonus is a percentage of the equipment's base stat,
  so a stat the target never declares, or declares as 0, does nothing.
  `mio-bonus-no-base-stat`: nothing in scope declares it. `mio-bonus-partial-base-stat`:
  only part of the scope does. The partial check skips `initial_trait`, which cannot be
  split. `mio-equipment-type-unknown` (WARNING) suppresses the bonus check for its block.
  - Scope in `organizations/`: the trait's `limit_to_equipment_type`, else the org's
    `equipment_type`, else that of the org named by `include`.
  - `NON_STAT_BONUS_KEYS` excludes the per-archetype production keys.
    `zero_base_exempt_stats` in the config is empty on purpose: confirm in game before
    adding a stat.
  - The stat index (`equipment_stats.py`) counts a stat only with a non-zero value, and
    scopes modules to the slots a hull accepts.
- Naval production bonus: ships are built in dockyards, which have no production
  efficiency, so `production_efficiency_gain_factor`, `production_efficiency_cap_factor`,
  and `production_conversion_speed_factor` do nothing on a ship.
  `mio-production-bonus-naval` (ERROR): everything the trait reaches is naval.
  `mio-production-bonus-partial-naval` (WARNING): mixed scope, a coverage note.
  `policies/` is out of scope because `same_as_mio` is not statically resolvable.
- `mio-design-team-type-uncovered` (WARNING): a `create_equipment_variant` names
  `design_team = mio:<org>` whose `equipment_type` does not cover the variant's
  archetype after `mio_cat_*` expansion, so the engine ignores the designer. A type
  the equipment index cannot resolve (a vanilla designer airframe) is skipped. A
  staged org edit does not rescan unstaged references; the full CI run does.
- A staged change in `policies/`, `common/country_leader/`, `common/units/equipment/`,
  `common/equipment_groups/`, or English loc rescans every org.

## validate_modifiers.py

- No pre-commit hook, so `common/dynamic_modifiers/` edits get no local signal.
- `redundant-enable-gate` (ERROR): a top-level `always = yes`, `original_tag`, or `tag` in
  a dynamic modifier's own `enable`. See `common/dynamic_modifiers/README.md`.
  `tools/standardization/strip_dynmod_tag_gates.py` clears them in bulk.
- `dynamic-modifier-name-loc` (ERROR): a dynamic modifier needs a bare-name English key.
- `dynamic-modifier-enable-block` (WARNING): the whole `enable` block is re-evaluated per
  tick per holder. The state usually belongs in the effect that adds or removes the
  modifier. `unknown-modifier` (WARNING) has known false positives.

## validate_on_actions.py

- `deterministic-date-poll` (ERROR): `date >` polling from `on_daily`, `on_weekly`, or
  `on_monthly`. Historical events belong in `00_yearly_effects.txt`. Chance-rolled polls
  are exempt.

## validate_oob_units.py and validate_ai_equipment.py

- Every `create_equipment_variant` is slot-checked through `equipment_module_slots.py`
  (ERROR): unknown hulls, slots, and modules, slot categories, required slots, hull
  `module_count_limit`, `forbid_equipment_type`.
  `validate_ai_equipment.py` applies the same rules to `target_variant` designs.
- `parent_version` is not resolved. A clean run on a `parent_version > 0` design is not
  proof the runtime design is legal.
- `validate_ai_equipment.py` runs without `--strict` locally and with it in CI.
- `create_unit` is checked for state scope, `owner`, block keys, a single-line division
  string that parses, zero or near-zero factors, and template order.
- `missing-equipment-factor` (WARNING, opt-in `--missing-equipment-factor`).
- `out-of-bounds-division` (WARNING): the parser rejects German and Danish letters
  (`äöüßæøå`) in the division string, even inside quotes. Other accents render.
- `missing-template-ensure` (WARNING): a `create_unit` naming a template that
  `delete_unit_template_and_units` removes anywhere needs the template created earlier
  or a `has_template` guard. A scripted effect that creates or guards it also counts.
- `airborne-template-not-parachutable` (WARNING): a `division_template` whose name
  matches para, airborne, VDV, or desant lists a sub-unit without
  `can_be_parachuted = yes`, which stops the whole division from paradropping.
  Deliberate air-assault templates are listed in `air_assault_templates` in the
  config as `<file>:<template name>`. Staged mode checks only staged template files, so a `common/units/`
  flag change surfaces on the full CI run.
- New source directories: `config_drift_test.py` derives the routes from the
  `_*_SOURCE_PATTERNS` lists and fails until every route is updated.

## validate_party_loc.py

- Format categories are WARNING and tracked per nation in #3895. `party-loc-unknown-tag`
  is ERROR.
- The default run scopes format checks to the tags the branch touched. `--all` sweeps
  everything, `--tag TAG` audits one nation. Missing slots are never reported.

## validate_scientist_traits.py

- A trait's medal resolves to `icon = X`, else `GFX_<token>`. The sprite index is
  MD-only, because MD replaces `interface/unitleaderwindow.gfx` and vanilla's
  `GFX_scientist_trait_*` names are dead in game.
- `shadowed-scientist-trait-icon` (vanilla ships the art, re-declare the `spriteType`),
  `missing-scientist-trait-icon`, `stale-scientist-trait-icon-todo`. All WARNING.

## validate_scripted_params.py

- `call-shares-line` (ERROR): a contracted call sharing its line with another statement.
  Single-call wrappers and trailing comments are accepted. `--audit-shared-lines` adds
  uncontracted mixed lines as WARNING.
- A staged change under `common/scripted_effects/`, `common/country_tags/`, or
  `common/country_tag_aliases/` rescans every caller.
- See the [layout policy](../../tools/validation/README.md#scripted-effect-call-layout).

## validate_style.py and check_common_mistakes.py

- The style check is diff-scoped in the core job. Common mistakes run full-repo in the
  core batch through `validate_common_mistakes.py` and report ERROR only. It scans
  `common`, `events`, `history`, and `music`.
- `shared_focus_prefixes` in the config exempts `EH_` focus ids.
- An effect block whose only content is a `log` line is dead: delete the block. The
  standardizers and `tools/logging_tool.py` never inject a log into an empty block.
- Name checks resolve against mod data: equipment `type =` (with `duplicate_archetypes`
  clones expanded across numbered variants), `equipment_bonus` types,
  `has_active_mission` and `has_active_decision`, `add_opinion_modifier`, and
  `add_relation_modifier`.
- Structural checks: a `limit` directly under `else`, `province = { province = <id> }`,
  and a `#` comment swallowed into a `log` string.

## validate_variables.py

- `clamp-range-conflict` (WARNING): a `check_variable` against a value outside a literal
  `clamp_variable` range, or a sub-1 value against a variable clamped to a wide integer
  range. Variables written only by `set_temp_variable` are excluded.
- `unregistered-dynamic-token` (ERROR): every `token:X` literal and every `@X` target of a
  token game variable must be in `common/synchronized_dynamic_tokens/MD_tokens.txt`, or
  the engine logs an OOS warning per use. `@` after any other name is a scope.
  Runtime-built names are ignored. New tokens go in `MD_tokens.txt`, not
  `_ENGINE_KNOWN_TOKENS`.
- `redundant-focus-flag` (WARNING): a country flag set once, unconditionally, in a focus
  `completion_reward`, never cleared, and read only by short-form `has_country_flag`.
  `has_completed_focus` replaces it. Not reported: a second setter, a conditional or
  foreign-scope set, any `clr_country_flag` or `modify_country_flag`, a timed or valued
  form, a focus with `bypass`, and joint rewards. A file that reloads a tree gets a
  caution, since `load_focus_tree` without `keep_completed = yes` wipes completion.
- `available`-block checks (ERROR), each protecting a requirement line the player reads:
  - `untooltipped-available-check`: a bare `check_variable` renders no line.
  - `unlocalised-available-flag`: `has_country_flag` and `has_global_flag` render from a
    loc key named after the flag. Also covers `cancel_trigger`, `bypass`, and flags
    inside called scripted triggers.
  - `unlocalised-negated-trigger-tooltip`: a tooltip under an odd number of `NOT` blocks
    looks up `not_tooltip`, or `KEY_NOT` when none is set. `= no` counts as a negation.
  - `untooltipped-available-scripted-trigger`: a bare call to a scripted trigger whose
    body checks `has_global_flag` renders nothing.
  - Exempt: `custom_trigger_tooltip`, `custom_override_tooltip`, and `hidden_trigger`
    wrappers at any depth, `check_variable`'s inline `tooltip`, `visible` blocks, names
    containing `@`, AI-only decisions, and `if` branches whose `limit` holds an
    unconditional `is_ai = yes`.
- `variable-tooltip-missing-loc` (ERROR): `tooltip = KEY` in a variable effect with no
  English entry. `dynamic-modifier-tooltip-missing` (ERROR): an add or subtract on a
  variable backing a dynamic modifier with no `tooltip`, in blocks the engine renders.
  `hidden_effect` suppresses both.

## Other tools

- `validate_standardization.py` is manual. It runs the standardizers in memory and
  reports files they would rewrite. Pass `--all --no-color` for a full pass.
- `validate_unused_textures.py` is a manual-stage hook. CI cannot run it.
- `validate_set_variables.py` and `validate_scripted_localisation.py` are CI-only and
  strict. Run them directly for a local check.
- `sprite_index.py` indexes mod `.gfx` plus a live install. It reads `vanilla_sprites.txt`
  only for sizes (`build_sprite_size_index`) and for `validate_ideas.py`. Event pictures
  use `include_vanilla=False`, since MD must not rely on vanilla event pictures.
