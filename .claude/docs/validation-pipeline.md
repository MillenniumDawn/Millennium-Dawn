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
  fix the validator. Never delete or weaken a test to pass.
- The suite runs under `pytest -n auto`, so a test writes only under `tmp_path`.
- `.jscpd.json` fails the quality job on one pasted block. Factor shared test setup into
  a helper.
- The repository ruleset requires the `Test suite gate` check.

## Where a check runs

- Most content validators are CI-only. The `mod-tests` batch jobs in
  `.github/workflows/test-suite.yml` are the gate. `tools/validation/validator_batches.py`
  is the single list of what runs, which change groups select each validator, and which
  run without `--strict`.
- `git commit` runs only the fast subset: the `md-validate-content` dispatcher
  (`tools/precommit_validate.py`), `validate_defines.py`, and `validate_mesh_textures.py`
  on staged `gfx/models/` or `gfx/entities/` paths. The mesh check never runs in CI.
- Run a CI-only validator locally with
  `python3 tools/validation/validate_<topic>.py --staged --no-color`. Drop `--staged`
  for a full-repo scan.
- `--strict` gates on ERROR only. A check with a standing backlog ships as WARNING until
  the backlog is cleared. A new strict check needs a baseline audit first, see the
  review checklist in `tools/README.md`.
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
- Everything that fans out shares `cpu_budget()` in `tools/shared_utils.py`: 75% of the
  cores locally, all of them on CI. `MD_MAX_WORKERS=N` overrides it.

## Validation config

`validation_config.json` at the repo root holds every suppression list the validators read: false positives, exemptions, and known-good names. To add or drop an entry, edit the JSON, not the validator.

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
