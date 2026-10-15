# Validation Pipeline

Pre-commit and CI run different hook sets. A change can pass locally and fail CI, or
the reverse. Read this before wiring, judging, or debugging a validator.

What one validator checks, its exemptions, and its known gaps are in
[Validator Check Notes](validator-check-notes.md). Search that file for the script or
category name. Do not read it whole. Track a backlog in a GitHub issue, not in a doc.

## Hard gate

- `python -m pytest` must stay green. CI runs it on every PR touching `tools/`, on
  Linux, macOS, and Windows. Run it locally before merging any `tools/` change.
- A validator change and its regression tests are one change. Update a `*_test.py` to
  the new correct behavior in the same commit. If the test holds the correct invariant,
  fix the validator. Never delete or weaken a test to pass. Removing a test is a
  separate cleanup change that keeps the missed-line and partial-branch totals.
- Tests follow [Test Structure](../../tools/README.md#test-structure): one file per
  module or group of checks, one parametrized table per check, a new case is a new
  row. A row stays only if it is the flagged or passing baseline, runs a path no other
  row runs, or is the only row that fails when one rule of the check is broken.
- The suite runs under `pytest -n auto`, so a test writes only under `tmp_path`.
- Worker pools in tests start with `spawn` on every OS. A pool worker sees what it
  imports and what it is passed, not state a test patched in the parent.
- Tests that read live game files live in `tools/tests/content/`. The `Content tests`
  job runs them once, on tools or game content changes. The tools test jobs skip
  that directory and check out only the few game files named in the workflow.
- `.jscpd.json` fails the quality job on one pasted block. Factor shared test setup into
  a helper.
- The repository ruleset requires the `Test suite gate` check.

## Where a check runs

- Most content validators are CI-only. The `mod-tests` batch jobs in
  `.github/workflows/test-suite.yml` are the gate. `tools/validation/validator_batches.py`
  is the single list of what runs, which change groups select each validator, and which
  run without `--strict`. Its `args` are also the flags of the main baseline run, so a
  PR and main enable the same checks.
- `git commit` runs only the fast subset: the `md-validate-content` dispatcher
  (`tools/precommit_validate.py`), `validate_defines.py`, and `validate_mesh_textures.py`
  on staged `gfx/models/` or `gfx/entities/` paths. The mesh check never runs in CI.
- Run a CI-only validator locally with
  `python3 tools/validation/validate_<topic>.py --staged --no-color`. Drop `--staged`
  for a full-repo scan.
- `--strict` gates on ERROR only. A check with a standing backlog ships as WARNING until
  the backlog is cleared. A new strict check needs a baseline audit first, see the
  review checklist in `tools/README.md`.
- The events batch enables `--check-ai-chance-costs` as WARNING while the existing
  backlog is reviewed. It checks relevant AI modifiers, not just their presence, and
  ignores display-only `effect_tooltip` costs. Commit hooks leave this cross-reference
  scan disabled; functional Indonesia contracts run in the `Content tests` job.
- Strictness can differ by stage. `validate_ai_equipment.py` runs without `--strict`
  locally and with it in CI.
- `validate_unused_textures.py` is a `stages: [manual]` hook. `validate_standardization.py`
  is unwired and run by hand. The `md-standardize` auto-fixer hook stays disabled.
- The Test Suite runs on every PR to `main`, drafts included. Changes under
  `tools/validation/`, `tools/linting/`, `tools/shared_utils.py`, the workflow files,
  `resources/documentation/`, or `validation_config.json` force the full suite.
- The style check is diff-scoped in CI. The nightly `main` baseline is full-repo, so
  the PR report flags only new findings, and references orphaned by a deleted
  definition surface on the nightly run. Common mistakes run full-repo in the core batch
  over `common`, `events`, `history`, and `music`. A `music/*.txt` change selects only
  that validator, through the `music` group.
- `validate_graphical_cultures.py` runs in the targeted-b batch for `common` changes,
  in warning mode while the standing backlog is triaged. It compares top-level country
  `graphical_culture` assignments with bare identifier values, matching current country
  file syntax, against entries in MD's
  `common/graphicalculturetype.txt`. The CI workspace profile includes `/common/`,
  which supplies both inputs. No local HOI4 install or vanilla culture registry was
  available to verify base-game-only fallback behavior, so the check does not add a
  guessed vanilla allowlist. Resolve this source/policy question before making the
  check strict.
- Remaining phases of [#5383](https://github.com/MillenniumDawn/Millennium-Dawn/issues/5383):
  confirm the vanilla culture source/policy; validate entity
  clone parents and `attach` targets (including vanilla entities); check that cultural
  sprite sets cover `_1` through `_7`, including the known tierless-only
  `northamerican_gfx` entries; validate cross-file clone load order; report cosmetic-tag
  users of tag-prefixed entity sets; and include `gfx/entities/` in the CI workspace.
  Those checks depend on entity parsing and/or game lookup behavior and are not covered
  by the country registration milestone.
- Everything that fans out shares `cpu_budget()` in `tools/shared_utils.py`: 75% of the
  cores locally, all of them on CI. `MD_MAX_WORKERS=N` overrides it.

## CI artifacts and reports

- `test-suite.yml` checks out the live PR head and holds no write credentials until the
  `report` job. A head predating the tooling contract stops with one error asking
  to merge main.
- `detect-changes` uses `collect_changed_files.py` and `change_groups.py`.
  `validate-paths` reads the git index. `prepare-workspace` shares one sparse artifact
  across the core, targeted-a, and targeted-b batches. It has no `.git`, no `map/`,
  and only `gfx/flags` and `gfx/interface/decisions` from the art trees.
- `tools-quality` runs Ruff, Black, pylint, mypy, jscpd, the staged-validator
  integration, and `validate_tools.py`. Coverage runs on Linux only.
- `workflow_dispatch` takes `pr_number`, `head_sha`, and `base_sha`, and skips
  diff-scoped style sections. It runs with main's token and cache scope, so it refuses
  fork PRs; their `pull_request` runs validate them. `nightly-pr-validation.yml`
  re-dispatches same-repository PRs with no successful run on their current head and
  base. `validator-cache.yml` rebuilds main's baseline.
- `changelog-conflict-fixer.yml` merges main into same-repo PRs whose only conflict is
  `Changelog.txt`, then dispatches the suite. `changelog-lint.yml` checks entry order;
  `python3 tools/merge_changelog.py --fix` repairs it.
- The report posts one PR comment: new findings against main's baseline first, then
  findings in touched files. A clean run removes the older comment. Section titles
  derive from artifact directory names, so keep those slugs stable.
- Every validator writes a sidecar, even when clean, and the baseline meta lists them.
  A missing, extra, or malformed sidecar makes the baseline unavailable, so the report
  drops the NEW tags instead of reading lost findings as new. `baseline_check.py`
  refuses a run with no sidecars or a malformed one.

## Validation config

`validation_config.json` at the repo root holds every suppression list the validators and `tools/analysis/ai_path_report.py` read: false positives, exemptions, and known-good names. To add or drop an entry, edit the JSON, not the validator.

- Shape: `version`, then one object per validator script (`validate_ideas`, `check_common_mistakes`, ...), each holding named lists. A list maps each entry to the reason it is exempt. Leave the reason empty only when nobody knows it.
- Matching depends on the list. Most match whole names, `*_prefixes` and `equipment_bonus_instant_exempt` match name starts, the `validate_variables`, `validate_set_variables`, and `validate_scripted_localisation` lists match substrings (so a short entry can swallow real names), and `false_positive_patterns` holds regexes.
- `shared_utils.validation_config(validator, key)` returns one list. A missing file, section, or key raises, and so does a `version` other than 1.
- Rule sets that describe the engine (block keywords, vanilla loc keys, placeholder textures, naming-convention prefixes) stay in code. Only lists that silence findings on specific content belong in the config.
- A config edit behaves like a validator edit. The file is in every disk-cache fingerprint and the CI validator hash, `change_groups.py` runs the full suite for it, and every CI checkout plus `staged_sparse_profile.txt` includes it. CI also scans existing focus files when the config changes; style checks on other files remain diff-scoped. `config_drift_test.py` pins that wiring. The workshop publisher excludes it.

## Refreshing vanilla-derived data

CI has no HOI4 install, so six checked-in files stand in for the game. `tools/validation/refresh_vanilla_data.py` rebuilds all of them from a local install (`$HOI4_PATH`, else auto-detected from Steam's `libraryfolders.vdf` or the VS Code HOI4 extension `installPath` settings):

Files live under `tools/validation/` except the `docs` target.

| Target    | File                           | Read by                      |
| --------- | ------------------------------ | ---------------------------- |
| `defines` | `vanilla_defines.txt`          | `validate_defines.py`        |
| `docs`    | `resources/documentation/*.md` | `validate_modifiers.py`      |
| `fonts`   | `vanilla_fonts.txt`            | `validate_gfx_references.py` |
| `gui`     | `vanilla_gui_files.txt`        | `validate_gfx_references.py` |
| `paths`   | `vanilla_paths.txt`            | `validate_file_paths.py`     |
| `sprites` | `vanilla_sprites.txt`          | `validate_gfx_references.py` |

- `docs` files are verbatim copies of the game's own `documentation/`.
- `fonts` feeds the undefined-font check; `gui` the MD-authored vs vanilla override split (ERROR/WARNING).
- `sprites` is also read by `validate_ideas.py` (names) and `validate_decisions.py` (sizes). Lines are `GFX_name WxH`; the size is the texture's header dimensions and is absent when the sprite has no `texturefile` or the file is unreadable. Names come first so every reader that only wants names keeps working. The refresh reads ~30k texture headers and takes about a minute. Sprites from DLCs the refreshing machine does not own would drop out of the manifest; the ten music-pack sprites (`GFX_sabaton_album_art`, `GFX_*_comintern`, …) were kept by hand for that reason, so check the name diff before committing a refresh.

```bash
python3 tools/validation/refresh_vanilla_data.py
python3 tools/validation/refresh_vanilla_data.py --only docs sprites
```

Run it after every HOI4 version bump and commit the diff. Stale data does not fail CI. It produces false positives instead, which is worse: a modifier Paradox added after the last refresh reads as a typo, and a sprite added in the same patch reads as an undefined reference.

The `docs` target is a straight file copy with no reformatting, so `diff -r resources/documentation "$HOI4_PATH/documentation"` is the staleness check.

## Tooling deprecation watch

- `pre-commit/mirrors-prettier` is archived upstream. Maintained fork: `rbubley/mirrors-prettier`. Migrate next time the prettier pin needs touching.
