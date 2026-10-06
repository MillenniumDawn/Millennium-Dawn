# Millennium Dawn Validation Tools

Content validators for the Millennium Dawn mod. All validators share a common CLI interface. Cacheable validators can be run all at once via `run_all_validators.py`.

## Quick Start

```bash
# Run all cacheable validators (from the mod root)
python3 tools/validation/run_all_validators.py

# Strict mode: exit non-zero if any issues found (used in CI)
python3 tools/validation/run_all_validators.py --strict

# Only check staged files (pre-commit mode)
python3 tools/validation/run_all_validators.py --staged --strict

# Save combined report to a file
python3 tools/validation/run_all_validators.py --output report.txt
```

Output is color-coded. Pass `--no-color` for plain text (e.g. in log files).

---

## Validators

### Standard (run by default)

| Validator                             | Checks                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| ------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **validate_agency_upgrades.py**       | Intelligence agency upgrade prerequisites and capability references are defined; no duplicate upgrade IDs                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| **validate_ai_equipment.py**          | Nations blocked from generic AI equipment roles without custom coverage; duplicate role names                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| **validate_ai_navy.py**               | Naval taskforce ship types, fleet template references, mission types, composition sizes                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| **validate_ai_roles.py**              | `role_ratio`/`build_army` references match defined roles in `common/ai_templates/`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| **validate_bonus_names.py**           | The `name =` of `add_tech_bonus`, `add_equipment_bonus`, `add_design_template_bonus`, `add_doctrine_cost_reduction`, `add_daily_mastery` and `add_mastery_bonus` identifies the object granting the bonus: missing entirely (players see no source), a `CAT_` technology category (names the tech field instead of the source), or unlocalised. Resolves the enclosing block — focus id, decision token, event id or its `.t` title key, MIO trait token. Opt-in: `--name-not-owner-id` (name is localised but is not the owner's token)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| **validate_characters.py**            | Unit leader traits match the branch of the role they are assigned to (a navy trait on a general never applies); `common/country_leader/` advisor traits on a unit leader, which load silently and never apply; traits that no `common/unit_leader/` file defines (WARNING). Advisor slots share the same pass: a trait is used on the slot whose `common/country_leader/` pool file defines it, is defined at all, and is not a `common/unit_leader/` trait that does nothing on an advisor; a pool file named in `SLOT_POOL_FILES` that is missing. `TAG_`-prefixed traits are exempt from the slot check                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| **validate_cosmetic_tags.py**         | Missing cosmetic tags (used but never set); unused cosmetic tag colors                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| **validate_country_names.py**         | Every static tag in `common/country_tags/` has a names block in `common/names/` (a missing block makes the game log an error and fall back to `default` names); tags after `dynamic_tags = yes` and tag aliases are exempt (ERROR)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| **validate_ai_path_rules.py**         | Every focus tree owned by a single tag that holds states at game start has a `TAG_ai_behavior` rule with a `HISTORICAL` option and a `default = { }` block; shared trees and tags that only spawn later are skipped (WARNING)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| **validate_decisions.py**             | Duplicate decisions; unused categories; missing AI weight; custom cost tooltip presence; repeatable decisions rolling `random_list` / `random` without an explicit `fixed_random_seed`; icons drawn from the wrong slot's art (a category-sized sprite on a decision, and the reverse; MD and vanilla art, the latter via the size column of `vanilla_sprites.txt`); category descriptions that open with a `£` image too tall for their leading newlines, so it overlaps the category header; decision localisation in both directions — a missing name key, and a key that exists for an AI-only decision or AI-only decision category that nothing renders; effects that announce some of the decisions they unlock but not others gated on the same flag. Opt-in: `--missing-icons` (decisions/categories whose icon or picture sprite is undefined), `--unannounced-categories` (categories that become visible mid-game with no `unlock_decision_category_tooltip` telling the player), `--fix` (auto-insert missing `ai_will_do` factors, move identical `available` blocks into `visible`) |
| **validate_defines.py**               | MD defines exist in vanilla with correct namespace; duplicate defines within MD                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| **validate_events.py**                | Events missing `is_triggered_only = yes`; unsupported title/desc combinations; redundant long-form event calls; every `picture` resolves to an MD-defined sprite (vanilla event pictures are not allowed, so this gates in CI without the game installed); events with a `date >` guard that nothing schedules from `00_yearly_effects.txt`; options carrying a `log` while running no effects (ERROR); option logs that cite another option's id (ERROR); pictures whose art is authored for the other event window — wide news art on a `country_event` and the reverse, classified by aspect ratio because sprite names do not separate the two families (ERROR); `hidden = yes` events declaring a picture nothing renders (ERROR). Opt-in: `--check-ai-chance-costs` (options of multi-option events that charge treasury, debt, a tax rate change, political power, stability, or war support behind a flat `ai_chance`, WARNING)                                                                                                                                                            |
| **validate_factions.py**              | Faction template/goal/rule/icon references exist; no duplicate IDs; valid rule types                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| **validate_file_paths.py**            | Tracked paths that differ from a vanilla one only in case (Windows overrides it, Linux loads both — multiplayer checksum mismatch); case collisions inside the mod; names Windows cannot check out; source art shipped under a content root — `.psd`/`.xcf` the engine cannot load and `.png`/`.jpg`/`.jpeg` that load uncompressed and unmipmapped, convert with `tools/assets/md_art_convert.py` (WARNING; `.bmp` is exempt because `map/` requires it). Reads the git index, so it covers `map/` and `sound/` too                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| **validate_focus_tree.py**            | Duplicate focus IDs; orphan focuses; missing prerequisite targets; missing loc keys; dependency cycles; focus titles carrying a `§` color code, and focus descriptions coloured outside `§Y`/`§G`/`§R`. Opt-in: `--missing-icons` (focuses whose `icon` sprite is undefined). Bonus `name =` parameters moved to `validate_bonus_names.py`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| **validate_gfx_references.py**        | Sprite names in `.gui` and scripted-GUI files are defined in `interface/*.gfx`; English `£name` loc refs that match a sprite only case-insensitively (ERROR — no icon on Linux); one name defined twice, and names differing only in case (WARNING). Raw texture paths in variant icon values and designer icon pools are ERROR. Opt-in: `--report-unused` (sprites defined but never referenced). Sprites the engine builds from mod data are resolved into the reference set — focus search-filter icons, `GFX_EMI_<module>`, ace portraits, and anything a `[...]` scripted-loc/GUI template can produce — while equipment/tech icons and vanilla-name overrides are exempted outright. `MD_GFX_HIDE_UNUSED=1` drops just the orphan list from that run                                                                                                                                                                                                                                                                                                                                         |
| **validate_history.py**               | History files: technology dependencies, equipment variant modules, DLC-gated techs, OOB references, capital definitions                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| **validate_ideas.py**                 | Idea `allowed`/`visible` blocks reference defined ideas; no duplicate idea IDs; `GFX_idea_categories` has enough frames for the politics-view categories. Unused-ideas check is enabled by default (pass `--no-unused-ideas` to disable). The missing-icon audit runs by default as WARNING and flags three cases: the picture sprite is undefined, it differs only in case from one that is defined, or it resolves to placeholder art. Opt-in: `--missing-loc` (ideas without name/desc loc keys), `--suggest-consolidation` (advisory loc consolidation hints)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| **validate_localisation.py**          | Duplicate keys; unpaired brackets; color code mismatches; orphaned `_tt` tooltip keys; opinion modifiers without localisation (WARNING)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| **validate_mesh_textures.py**         | A rendered material in a used `.mesh` that, after `meshsettings`, still has an empty texture name, or names a texture no file under `gfx/` carries (mod or vanilla; skipped without an install). Both ERROR. Commit-stage only, since CI ships no model files                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| **validate_mios.py**                  | MIO org id format; `allowed = { original_tag = TAG }`; initial-trait naming; trait grid x ≤ 9; non-empty `on_complete`; `tree_header_text` uses a localisation key rather than a literal string; header keys and trait/`initial_trait` names resolve to an English loc key (all localisation failures are errors); `production_bonus` efficiency and conversion keys on a wholly naval roster, which ships never accumulate (ERROR), and the same keys on a mixed naval/land roster, where only the land half benefits (WARNING)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| **validate_mio_icons.py**             | Every MIO equipment group resolves to `GFX_<group>` and every non-group `equipment_type` token in an org to `GFX_military_industrial_organization_<token>` (mod or vanilla sprite); a missing group sprite spams `GFX key ... is missing` in error.log (both ERROR, CI-only)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| **validate_mod_descriptors.py**       | replace_path entries in descriptor.mod and Millennium_Dawn.mod must match (checksum safety); duplicate replace_path within a file flagged                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| **validate_modifiers.py**             | Modifier references in focuses/decisions/ideas exist in the defines or vanilla; no duplicate modifier definitions. Always-on: history `inflation_rate_var` over 1.0. Opt-in: `--unbalanced-modifiers` (balance caps per single reward: ROI over 3 percent, productivity growth over 25 percent, game-start policy rate over 30, game-start inflation over 50 percent)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| **validate_oob_units.py**             | Unit names in OOB files and AI templates match canonical names in `common/units/`; every `create_equipment_variant` ship design uses slots its hull has and modules those slots accept; every `upgrades = { key = N }` entry in a `create_equipment_variant` is one its equipment type lists ("does not support upgrades"); `create_unit` `division = "..."` strings parse as army data (inner keys, quotes, factors, `force_equipment_variants`); German/Danish letters in that string are WARNING; a `create_unit` of a template that `delete_unit_template_and_units` also removes, with no in-effect create, `has_template` guard, or prior call to a scripted effect that ensures it, is WARNING. Opt-in: `--missing-equipment-factor` (warn when a `create_unit` division string omits `start_equipment_factor`)                                                                                                                                                                                                                                                                             |
| **validate_on_actions.py**            | Events referenced in `on_actions` are defined; `is_triggered_only` enforced; no duplicate refs in the same trigger block                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| **validate_party_loc.py**             | Party loc keys pair with a per-tag politics-view hook and follow the `£sprite (ABBRV) - Party Name` shape. Branch-scoped by default; `--all` audits every tag, `--tag TAG` audits one country (repeatable)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| **validate_scientist_traits.py**      | Every scientist trait resolves to a medal sprite MD defines (`icon = X`, else `GFX_<token>`); sprites declared only in the vanilla file MD replaces; stale `#TODO: ICON` markers (all WARNING)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| **validate_scripted_gui.py**          | Scripted GUI window/property names are defined; referenced effects/triggers exist                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| **validate_scripted_localisation.py** | Scripted loc keys used but not defined; defined but never referenced; missing GFX icons                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| **validate_scripted_params.py**       | Every call site of a scripted effect that documents required temp variables sets them, in a scope the call can still see them from. A declared parameter that is set and then never used is an `orphan-param-setter` ERROR. Call sites are scanned across `common/`, `events/` and `history/`. Quoted text and comments are ignored. An input that cannot be read is an `unreadable-input` ERROR. A contracted call sharing a line with other statements is a `call-shares-line` ERROR. Single-call wrappers are accepted. Opt-in `--audit-shared-lines` reports uncontracted mixed lines as `audit-call-shares-line` WARNINGs. With `--staged`, a changed, deleted, or renamed scripted effect, scripted trigger, country tag, or tag alias file rescans every caller                                                                                                                                                                                                                                                                                                                             |
| **validate_standardization.py**       | Files the project standardizers would rewrite — focus trees, events, decisions, ideas, MIOs. Runs the owning standardizer from `tools/standardization/` in memory and diffs its output against the file, so the check cannot drift from the formatter. Manual-only (unwired from pre-commit and CI); `--all` scans the whole repo (a backlog of ~745 files). A standardizer that raises is an ERROR, since running it would leave the file half-rewritten                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| **validate_style.py**                 | Brace matching, indent/bracket balance, spacing/quotes, focus ID format, event log standards                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| **validate_simplifications.py**       | Suggests merging consecutive same-scope blocks (`TAG = { } TAG = { }`, state ids, `PREV`, `var:`); WARNING-only, skips OR/random_list contexts. Opt-in: `--owner-scope-only` (only the redundant owner-scope pass over focus trees and decisions)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| **validate_tech_categories.py**       | Every `category = CAT_x`, `research_bonus` / `research` key, MIO `research_categories` token and tech-file `categories` token is declared in `common/technology_tags/` (ERROR, compiles silently otherwise). The tag set itself: every tag is `CAT_lowercase`, has both `CAT_x` and `CAT_x_research` English loc keys, and is carried by at least one technology (all ERROR, #4250)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| **validate_technologies.py**          | Tech generation chains (ids identical after stripping digits/underscores) must carry every category their parent carries; a gen dropping a category its lineage has is flagged. Distinct-subtype branches (e.g. `countermeasures` vs `air_weapons`, `Anti_Air` vs `AA_upgrade`) are intentionally different and skipped                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |

### Heavy validators

These cross-reference the entire codebase. A disk cache under `.validation_cache/` keeps re-runs fast — see [DISK_CACHE.md](DISK_CACHE.md).

| Validator                       | Checks                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **validate_set_variables.py**   | Variables set with `set_variable` are actually used somewhere. Tuning: `--min-refs N` (minimum references required, default 0)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| **validate_unused_scripted.py** | Scripted effects/triggers defined but never called                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| **validate_unused_textures.py** | Texture files not referenced in any `.gfx` file; `.gfx` entries with missing files. Manual-only.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| **validate_variables.py**       | Country/state/global flags and event targets: cleared-but-not-set, missing, unused; untooltipped `check_variable` in `available` (error); country flags checked in `available` with no localisation key (warning) — all three `available` checks skip AI-only decisions and AI-only categories; variable-effect `tooltip =` keys with no localisation entry (warning); dynamic-modifier writes in player-facing effect blocks with no `tooltip =` (warning); `token:X` literals and token game-variable targets (`modifier@X`, `resource@X`, ...) in script, English localisation or `.gui` text missing from `common/synchronized_dynamic_tokens/MD_tokens.txt` (error). Opt-in: `--redundant-focus-flags` (country flags set by exactly one focus `completion_reward` that `has_completed_focus` could replace) |

---

## Common Flags

All validators accept the same set of flags:

| Flag                       | Description                                                                             |
| -------------------------- | --------------------------------------------------------------------------------------- |
| `--path PATH`              | Path to the mod root (default: current directory)                                       |
| `--staged`                 | Only validate files currently staged in git                                             |
| `--strict`                 | Exit with code `1` if any issues are found                                              |
| `--output FILE`, `-o FILE` | Write results to a file in addition to stdout                                           |
| `--no-color`               | Disable ANSI color codes                                                                |
| `--workers N`              | Number of parallel worker processes (default: CPU count / 2, clamped to the CPU budget) |

### CPU budget

Tooling takes 75% of the cores and leaves the rest, so a run does not lock up
the machine someone is working on. Everything that fans out draws on the same
ceiling (`cpu_budget` in `tools/shared_utils.py`): the suite caps how many
validators run at once and passes each a share of the workers, the pre-commit
hook splits the same budget across its fan-out, and `--workers N` is clamped to
it. CI runners get every core. `MD_MAX_WORKERS=N` overrides both.

---

## Running a Single Validator

Every validator can be run standalone with the same flags:

```bash
python3 tools/validation/validate_events.py --path .
python3 tools/validation/validate_localisation.py --path . --staged --strict
python3 tools/validation/validate_ai_roles.py --path . --output ai-roles.txt
```

---

## Output Format

When validators find issues they print a grouped summary and write a `.json` sidecar file (used by `run_all_validators.py` to build the combined report):

```
================================================================================
Checking events missing is_triggered_only = yes...
================================================================================
  events/example.txt:42 - some_event.1 is missing is_triggered_only = yes
1 issue(s) found

################################################################################
✗ VALIDATION COMPLETE - 1 ERROR(S)
################################################################################
```

When `run_all_validators.py` detects failures it prints a **combined report** grouped by file with line numbers:

```
================================================================================
COMBINED VALIDATION REPORT
================================================================================
Total validators run: 12

✗ 2 ERROR(S)

  events/example.txt (2 issue(s))
    - events/example.txt:42: [events] some_event.1 is missing is_triggered_only = yes
    - events/example.txt:87: [events] some_event.2 is missing is_triggered_only = yes
```

---

## Pre-Commit Integration

Validators are integrated into `.pre-commit-config.yaml` and run automatically
on commit. The hook passes `--staged` so only the files being committed are
checked, keeping commit times fast.

To bypass for a single commit (not recommended):

```bash
git commit --no-verify
```

### Pre-commit vs CI

To keep commit latency low, only a fast subset of validators runs on
`git commit`. Heavy cross-reference validators such as
`validate_scripted_gui`, `validate_localisation`, `validate_cosmetic_tags`,
`validate_variables`, and `validate_focus_tree` run
**CI-only**. The
`mod-tests` batch jobs in
`.github/workflows/test-suite.yml` gate them instead of pre-commit.
Their list, changed-group selection, and `--strict` gates live in
`tools/validation/validator_batches.py`.

The commit-stage validators (`validate_common_mistakes`, `validate_style`,
`validate_oob_units`, `validate_ai_roles`, `validate_ai_navy`,
`validate_characters`, `validate_ai_equipment`, `validate_agency_upgrades`,
`validate_ideas`, `validate_events`, and
`validate_mios`) run through the
`md-validate-content` pre-commit hook. It fans them out in parallel through
`tools/precommit_validate.py`. `validate_defines` keeps its own commit-stage
hook. `validate_mesh_textures` also keeps its own commit-stage hook, keyed on
`gfx/models/` and `gfx/entities/`, because the CI workspace ships neither.
`validate_unused_textures` keeps a `stages: [manual]` hook because CI
cannot run it. `validate_standardization` is manual-only tooling: run it
directly for a cleanup pass, it is not wired into either pipeline.

`validate_file_paths` runs CI-only in the `prepare-workspace` job of
`test-suite.yml`. It reads the PR git index rather than the working tree,
against a blob:none checkout that keeps `.git`. The batch jobs restore the
prepared content bundle with no `.git` and no `map/`. Standalone style,
descriptor, and encoding checks run inside the core batch job; the manual
texture audit stays excluded.

To run any validator locally, including a CI-only one, invoke it directly:

```bash
python3 tools/validation/validate_scripted_gui.py --staged --no-color  # changed files only
python3 tools/validation/validate_scripted_gui.py --no-color           # full-repo scan
```

---

## Refreshing Vanilla Data

CI has no HOI4 install, so `validate_defines`, `validate_file_paths`, `validate_gfx_references` and `validate_modifiers` read checked-in copies of vanilla data instead: `vanilla_defines.txt`, `vanilla_gui_files.txt`, `vanilla_paths.txt`, `vanilla_sprites.txt`, and `resources/documentation/*.md`. `refresh_vanilla_data.py` rebuilds all five from a local install (`$HOI4_PATH`, else auto-detected from Steam's `libraryfolders.vdf` or the VS Code HOI4 extension `installPath` settings):

```bash
python3 tools/validation/refresh_vanilla_data.py
python3 tools/validation/refresh_vanilla_data.py --only docs sprites
```

Run it after every HOI4 version bump and commit the diff. Stale data never fails CI. It produces false positives instead, which is worse: a modifier or sprite Paradox added after the last refresh reads as a typo. Details in `.claude/docs/validation-pipeline.md`.

---

## Architecture

All validators extend `BaseValidator` from `validator_common.py`. To add a new validator:

1. Create `validate_<name>.py` in this directory
2. Subclass `BaseValidator`, set `TITLE = "..."`, implement `run_validations()`
3. Use `self.add_error(category, message, file, line)` / `self.add_warning(...)` to record issues
4. To parse many files, call `self.parse_files_cached(patterns, namespace, parse_fn)` — it's staged-aware, case-preserving, and disk-caches each parse keyed on file content. Use a unique `namespace` string per call to avoid cache collisions.
5. Call `run_validator_main(YourValidator, "Description")` at the bottom
6. `run_all_validators.py` auto-discovers it on the next run unless it is intentionally manual-only

`validator_common.py` also provides `strip_comments()`, `FileOpener`, `drop_partial_matches()`, `HOI4_BUILTIN_BLOCKS`, and `scan_meta_constructed_names()` for use in validators.

Module-level constants and pool-worker functions (those passed to `_pool_map`) must be defined at the **top level** — not inside the validator class — so `multiprocessing.Pool` can pickle them. Classmethods on a validator subclass are not directly picklable; use standalone functions for pool dispatch.

### `validator_common.py` public API

| Symbol                                                                                                                               | Type      | Description                                                                                                                                                                                                                                                |
| ------------------------------------------------------------------------------------------------------------------------------------ | --------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BaseValidator`                                                                                                                      | class     | Base for all validators. Provides `_pool_map`, `_collect_files`, `_report`, `_log_section`, timing, and JSON output                                                                                                                                        |
| `BaseValidator.parse_files_cached(patterns, namespace, parse_fn, *, lowercase=False, strip_comments_flag=True, ignore_staged=False)` | method    | Collect files matching glob patterns (staged-aware), read each case-preserving, strip comments, and per-file disk-cache the result keyed on content; returns `{path: parse_fn(text, path)}`. Use this as the standard way to parse many files of one kind. |
| `scan_meta_constructed_names(files, defined_names)`                                                                                  | function  | Scan files for `meta_effect`/`meta_trigger` template patterns and match against defined names                                                                                                                                                              |
| `HOI4_BUILTIN_BLOCKS`                                                                                                                | frozenset | All known HOI4 built-in effect/trigger block names                                                                                                                                                                                                         |
| `Colors`                                                                                                                             | class     | ANSI escape codes for colored output (`HEADER`, `BLUE`, `CYAN`, `GREEN`, `YELLOW`, `RED`, `ENDC`, `BOLD`, `UNDERLINE`)                                                                                                                                     |
| `Severity`                                                                                                                           | class     | String constants: `Severity.ERROR = "error"`, `Severity.WARNING = "warning"`                                                                                                                                                                               |
| `Issue`                                                                                                                              | dataclass | Structured issue with `severity`, `category`, `message`, `file`, `line` fields and `to_dict()` / `to_key()` methods                                                                                                                                        |
| `MD_LOG_LEVEL`                                                                                                                       | env var   | Set to `ERROR` / `WARNING` (default) / `INFO` to control per-validator verbosity                                                                                                                                                                           |

---

## Scripted effect call layout

`validate_scripted_params.py` checks `NAME = yes` calls to effects with required
parameter contracts by default. `call-shares-line` is an ERROR: a contracted call
must not share its physical line with another statement. `--strict` gates it in
CI. This is a readability policy, not an engine requirement for newlines.

The same layout policy applies in the opt-in `--audit-shared-lines` scan, which
also recognizes uncontracted scripted effects. Those additional findings use
`audit-call-shares-line` at WARNING severity, even with `--strict`. The flag never
downgrades contracted-call or parameter errors. A mixed line is reported once;
if it contains both kinds of call, the contracted call owns the error regardless
of call order. Counts are physical lines, not calls or defects.

Accepted forms:

- A call on its own line, with an optional trailing comment.
- A single call inside one or more enclosing wrappers, including numeric random
  weights, `hidden_effect`, country scopes and effect containers. For example,
  `25 = { change_the_priesthood_opinion = yes }` and
  `hidden_effect = { ROOT = { some_effect = yes } }` are accepted.
- A call followed only by closing braces. Delimiters alone are not another
  statement. Other validators still own structural validity.

Split setters and calls, multiple calls, or another statement beside a call.
`if = { limit = { always = yes } some_effect = yes }` still has another statement
and is reported: ERROR for a contracted call, advisory in the uncontracted audit.
Simple checks and parameter blocks may remain compact. The single-leaf output of
`shared_utils.collapse_or_compact` agrees with these exceptions; no path-specific
allowlist is used. Avoid whole-file standardizers for this cleanup because they
also reorder properties and inject logging.

## Focus coordinate warnings

`validate_focus_tree.py` reports `focus-coordinate-overlap` when two static focuses
in the same assembled tree share a row and are less than two columns apart.
Both exact stacks and neighboring positions are checked, including every pair
between stacked groups. Findings include the tree, both IDs, resolved coordinates
and source locations. These are WARNINGs, including under `--strict`.

The existing per-file read/cache pass supplies geometry. Each tree imports its
explicit `shared_focus` references plus shared/joint descendants whose shared
prerequisites have been imported. The shared registry spans files, so cross-file
shared branches and relative anchors resolve in their host tree. Unimported
fragments and other trees are never coordinate targets or collision partners.
Repeated imports do not duplicate a focus; duplicate definitions are ambiguous.
This covers standalone shared/joint definitions used by the audited MD files.
Nested focus-group containers and nested prerequisite groups supported by the
VSCode preview are not expanded. Neither occurs in the audited MD files; this
validator does not claim complete preview or engine-layout parity.

Relative chains use iterative memoization, including failed resolutions. Signed
decimal coordinates are preserved exactly, without rounding to integer columns.
Missing or nonnumeric coordinates, missing anchors/imports, duplicate definitions
and cycles produce `focus-coordinate-unresolved` WARNINGs. Dependents of a broken
anchor remain unresolved, with one diagnostic for the root cause per tree.
Existing duplicate-ID and missing/forward-relative-target ERROR checks remain.

Missing `x` or `y` is deliberately unknown, not an assumed zero. The existing
`tools/analysis/focus_overlap_report.py` defaults omitted axes to zero, while
[MD MCP's resolver](https://github.com/MillenniumDawn/millennium-dawn-mcp/blob/d3de458fca7c58c74c301df22d373177dc8fdb17/src/md_mcp/analysis/focus_layout.py#L111)
rejects them. No engine-backed default has been established for this validator;
the warning identifies a coverage gap, not a proven content defect. Two existing
Czech focuses omit `x`, leaving their 29 combined tree instances unresolved.

Dynamic layout is not simulated. Any focus with an `offset`, and every relative
descendant of it, is skipped. A focus with `allow_branch`, and every prerequisite
descendant that could depend on that gate, is skipped conservatively, including
alternative prerequisite paths. This can omit real problems but avoids claiming
that hypothetical static positions are drawn together. `available` and
`mutually_exclusive` alone do not exempt icons. No content-specific exemptions
were added; the remaining candidates stay visible for review.

In staged mode, changed country trees and all shared-consuming trees are checked
after any focus-file change. Rechecking shared consumers is intentional: removing
or reparenting a shared descendant can erase its old dependency from the current
registry. Deleted focus paths are retained; a deletion rechecks all trees.
Staging no focus files runs no geometry scan. Per-file cached records are reused,
but assembly and geometry are recomputed so changed imports cannot leave stale
results. The separate scenario report remains useful for dynamic investigations.

`focus-allow-branch-leak` (WARNING) covers the gap gated focuses leave. A focus
whose own `allow_branch` is true shows even when an ancestor's `allow_branch`
hid its branch, so it floats on top of the visible path (#5042). The check
hides each gated focus, follows prerequisites (a focus hides once one of its
`prerequisite` groups is fully hidden), and stops at the first descendant with
its own `allow_branch`. That descendant must repeat every `key = value` leaf of
the ancestor's `allow_branch`, in any structure. `NOT` is not distinguished from
a plain condition. It stays a WARNING until the existing backlog is cleared.

### Measured backlog for #5126

At `f99f2055f069e41c6f51623c82d2fcc6a7f7338b`, 114 files contain 106 trees and
32,684 assembled focus instances (a shared focus counts once in each host tree).
The check resolves 32,655 instances, skips 9,814 resolved dynamic instances and
checks 22,841 static instances. Gated instances number 8,373 and offset-dependent
instances 8,996; these overlap and must not be added. There are no missing shared
imports. The two unresolved root diagnostics account for 29 unresolved instances.

The static backlog is **8 candidate pairs across 5 trees**:

| Tree                            | Candidate pairs                                                                                                        |
| ------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| San Marino                      | `SMA_healthy_people` / `SMA_vatican_union`                                                                             |
| Czech Republic                  | `CZE_2000st_apc` / `CZE_2000st_ifv`; `CZE_2000st_utility_vehichles` / `CZE_2000st_tank_modernization`                  |
| Generic                         | `GENERIC_eastern_emergence` / `GENERIC_non_aligned`; `GENERIC_the_rising_powers` / `GENERIC_the_conservative_approach` |
| Ukrainian provisional republics | `DRP_dnieper_logistics` / `UKR_prp_emergency_economy`; `DRP_moscow_alignment` / `UKR_prp_utilities_repair`             |
| USA                             | `USA_net_zero_green_house` / `USA_new_path_ways_for_greens`                                                            |

Removing dynamic exclusions yields 543 raw pairs, not 543 established bugs. The
eight static candidates have not been repositioned or exempted without in-game
review. The Brazil pre-#5122 fixture reports its one-column pair; the corrected
two-column spacing passes. Fractional coordinates account for four candidates
missed by the earlier integer-only exploratory scan.

Run `MD_LOG_LEVEL=INFO python tools/validation/validate_focus_tree.py --path .
--workers 1 --no-color` on one line to print counts with findings. Existing
unrelated validator errors can still make the complete validator exit nonzero.

Three cold-cache and three warm-cache measurements on the same 114 files with
Python 3.12.14 and one worker compared the existing parse/relative-position scans
with those same scans plus geometry. Median times were 0.911s versus 2.658s cold,
and 0.226s versus 0.471s warm. These measure this scan component, not the full
validator or CI; they are not a speedup claim. Resolution avoids recursive depth
limits, and sorted row buckets enumerate only pairs within the spacing window.

## Credits

Based on Kaiserreich Autotests by [Pelmen323](https://github.com/Pelmen323), adapted for Millennium Dawn.
