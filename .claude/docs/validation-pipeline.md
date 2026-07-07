# Validation Pipeline — Pre-commit vs CI

Pre-commit and CI do not run the same hook set. Things that pass locally can still fail CI, and vice versa. Read this before wiring, judging, or debugging any validator.

## The split

- Most content validators run **CI-only**: the `validate-core` / `validate-targeted` matrices in `.github/workflows/coding-pipeline.yml` are the gate. Their old `stages: [manual]` pre-commit hooks were removed (almost nobody ran them). On `git commit` only the fast subset runs — the `md-validate-content` dispatcher (`tools/precommit_validate.py`, which fans the commit-stage validators out in parallel), plus `check_common_mistakes.py` and `validate_defines.py`. To run a CI-only validator locally: `python3 tools/validation/validate_<topic>.py --staged --no-color` (drop `--staged` for a full-repo scan).
- `validate_ai_equipment.py` runs without `--strict` locally (coverage gaps would block all commits) but **with** `--strict` on CI. Equipment-coverage gaps that are tolerated locally will fail PR validation.
- `fix_loc_yaml.py`, `validate_localization_encoding.py`, `validate_mod_encoding.py` (all `tools/linting/`) are **pre-commit-only** — never run on CI. Web-UI edits or contributors with hooks disabled can land BOM or encoding regressions. (The old `check_braces.py` hook was absorbed into `tools/validation/validate_style.py`.)
- `validate_defines.py` runs on pre-commit against the live install and on CI against the committed `tools/validation/vanilla_defines.txt` manifest. Regenerate the manifest with `gen_vanilla_defines_manifest.py` after a HOI4 version bump (same for `vanilla_sprites.txt` via `gen_vanilla_sprites_manifest.py`).
- `validate_ideas.py` is wired into both pre-commit (`--staged --strict`) and CI (`strict: false`, informational) until the ~30 pre-existing undefined-idea references on main are triaged. Once cleared, flip the CI entry to strict.
- `validate_unused_textures.py` is wired into pre-commit as `stages: [manual]` and into CI as informational (`strict: false`). The repo currently carries ~22k unreferenced textures — informational mode keeps the audit visible without blocking PRs.
- `validate_set_variables.py` runs **CI-only** (informational). Its false-positive volume at repo scale makes it too noisy for a commit gate, so it has no pre-commit hook; run it directly (`python3 tools/validation/validate_set_variables.py`) against a specific variable when needed.

## Tooling deprecation watch

- `pre-commit/mirrors-prettier` is archived upstream. Maintained fork: `rbubley/mirrors-prettier`. Migrate next time the prettier pin needs touching.
