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
- Trailing-whitespace cleanup uses `fix_styling.py --trailing-whitespace-only` on
  staged-diff lines only, preserving untouched lines and refusing worktree/index
  mismatches. The normal commit flow stashes unstaged work first. The fixer never
  stages its output; stage the changed lines and retry when it makes a correction.
- `git commit` runs only the fast subset: the `md-validate-content` dispatcher
  (`tools/precommit_validate.py`), `validate_defines.py`, and `validate_mesh_textures.py`
  on staged `gfx/models/` or `gfx/entities/` paths. The mesh check never runs in CI.
  On a merge commit the dispatcher checks only the conflicted files pre-commit passes,
  plus staged deletions and rename origins.
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

- `test-suite.yml` has read-only repository permissions, including its `report`
  job. A `pull_request` run, re-runs included, validates its event's head and base. A
  dispatch looks the PR up, which is the explicit refresh to its live head. The report
  publisher leaves the PR comment alone when the head has since moved. A head
  predating the tooling contract stops with one error asking to merge main. The
  report and base scan run the head's scripts with the workflow's flags, so a new
  flag joins the contract.
- `detect-changes` uses `collect_changed_files.py` and `change_groups.py`.
  `validate-paths` reads the git index. `prepare-workspace` shares one sparse artifact
  across the core, targeted-a, and targeted-b batches. It has no `.git`, no `map/`,
  and only `gfx/flags`, `gfx/interface/decisions`, and `gfx/texticons` from the art
  trees. Size checks report art outside them as `decision-icon-unmeasured`.
- `tools-quality` runs Ruff, Black, pylint, mypy, jscpd, the staged-validator
  integration, and `validate_tools.py`. Coverage runs on Linux only.
- `workflow_dispatch` takes `pr_number`, `head_sha`, and `base_sha`, and skips
  diff-scoped style sections. A PR dispatch requires `head_sha` so its run title
  pins the validated commit. It runs with main's token and cache scope, so it refuses
  fork PRs; their `pull_request` runs validate them. `nightly-pr-validation.yml`
  re-dispatches same-repository PRs with no successful run on their current head and
  base. `validator-cache.yml` rebuilds main's baseline.
- `validator-cache.yml` runs on every push to main. It saves each complete run as that
  commit's baseline (`md-baseline-v1-<os>-<hash>-<sha>-*`), even when the alarm fails.
  The alarm compares the run with the last accepted one (`md-accepted-v1-*`) and goes
  red on new errors until they are fixed. Main's run also widens diff-scoped checks to
  their whole domain through `baseline_args` (party-loc audits every tag).
- The report restores only the baseline of the PR's merge base, the main commit its
  content started from, and checks the commit in the meta. Against main's tip, fixes
  main made after the branch point would read as the PR's findings. When main has not
  saved one, the advisory `baseline-scan` job scans the merge base in the same run:
  the PR's tooling over the base content, no shared cache, a 20-minute budget. The
  report reads its artifact and marks the source. The scan saves no cache entry,
  because a dispatched run on main would let PR tooling write a main-scoped baseline.
  With neither, the comparison is unavailable.
- Main's findings in a file the PR renamed count as the new path's, in the file
  field and in messages. A finding that names only a basename does not move.
- Each main finding matches one PR finding with the same category, file, and message.
  `detect-changes` ships the merge-base diff's hunk headers, so a match also needs the
  same place: main's line shifted past the PR's edits, or the same changed hunk.
  Fixing one copy and adding another elsewhere reads NEW, and so does a block moved
  within a file. Findings with no line or only a basename match by count.
- Main's findings come only from the validators the PR ran, so a severity difference
  is a real transition: RAISED (warning to error) or LOWERED (error to warning).
  This needs batch spec names to equal the script-derived sidecar names.
- When a PR changes validator code or reference data, both scans use its validators,
  so findings that code adds to unchanged content read EXISTING. `detect-changes`
  flags this and the report says so. The base scan also restores main's own baseline
  of the merge base, keyed by the base's own validator hash, and the report lists per
  category what the PR's validators add to and drop from it.
- The validator hash covers `tools/validation` sources and data, `shared_utils.py`,
  `validation_config.json`, `resources/documentation/`, and the typo watchlist. All
  four `hashFiles` sites must match, and each checkout must hold those files.
- `changelog-conflict-fixer.yml` merges main into same-repo PRs whose only conflict is
  `Changelog.txt`, then dispatches the suite. `changelog-lint.yml` checks entry order
  and warns, without failing, about exact repeats and untidy entries;
  `python3 tools/merge_changelog.py --fix` repairs both. Its sparse checkout holds only
  `Changelog.txt` and `check_changelog.py`, so that script imports no other tools.
- The report uploads `report.md` and `comment.json` in `validation-report`.
  `validation-report.yml` publishes the comment after the Test Suite completes,
  including failed runs. It checks out only the default branch's trusted code and
  reads the artifact as data outside the checkout. Only this publisher has
  `pull-requests: write`; its other permissions are `actions: read` and
  `contents: read`. It has no checks, contents, or issues write access.
- The publisher verifies the source workflow, repository, run attempt, PR, and
  validated head against GitHub before writing. Fork runs often have an empty
  `pull_requests` list, so the pinned run title identifies the target. The PR's
  head repository and branch must also match the source run. Dispatches can publish
  only to same-repository PRs. Closed PRs and moved heads are left alone; unreadable
  PRs and malformed or missing payloads fail publishing. Artifact mentions are
  disabled. The new workflow must land on the default branch before it can run.
- The comment lists new findings against main's baseline first, then findings in
  touched files. A clean run removes the older comment. If change detection
  succeeds and every validation job is skipped, `--no-tests-selected` also removes
  the older comment instead of posting an empty report. Empty results without that
  flag still report missing output. The workflow no longer writes Checks API
  annotations; the validation jobs and suite gate remain the merge checks. Section
  titles derive from artifact directory names, so keep those slugs stable.
- Every validator writes a sidecar, even when clean, and the baseline meta lists them.
  A missing, extra, or malformed sidecar makes the baseline unavailable, so the report
  drops the NEW tags instead of reading lost findings as new. `baseline_check.py`
  refuses a run with no sidecars or a malformed one, and saves neither baseline.

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
