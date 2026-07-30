# Validation Pipeline — Pre-commit vs CI

Pre-commit and CI do not run the same hook set. Things that pass locally can still fail CI, and vice versa. Read this before wiring, judging, or debugging any validator.

## The split

- Most content validators run **CI-only**: the `validate-core` / `validate-targeted` matrices in `.github/workflows/coding-pipeline.yml` are the gate. Their old `stages: [manual]` pre-commit hooks were removed (almost nobody ran them). On `git commit` only the fast subset runs — the `md-validate-content` dispatcher (`tools/precommit_validate.py`, which fans the commit-stage validators out in parallel), plus `check_common_mistakes.py` and `validate_defines.py`. To run a CI-only validator locally: `python3 tools/validation/validate_<topic>.py --staged --no-color` (drop `--staged` for a full-repo scan).
- `validate_ai_equipment.py` runs without `--strict` locally (coverage gaps would block all commits) but **with** `--strict` on CI. Equipment-coverage gaps that are tolerated locally will fail PR validation.
- `fix_loc_yaml.py`, `validate_localization_encoding.py`, `validate_mod_encoding.py` (all `tools/linting/`) are **pre-commit-only** — never run on CI. Web-UI edits or contributors with hooks disabled can land BOM or encoding regressions. (The old `check_braces.py` hook was absorbed into `tools/validation/validate_style.py`.)
- `validate_defines.py` runs on pre-commit against the live install and on CI against the committed `tools/validation/vanilla_defines.txt` manifest. Regenerate the manifest with `gen_vanilla_defines_manifest.py` after a HOI4 version bump (same for `vanilla_sprites.txt` via `gen_vanilla_sprites_manifest.py`).
- `validate_ideas.py` is wired into both pre-commit (`--staged --strict`) and CI (`--strict`) — the undefined-idea backlog was cleared, so both sides gate identically.
- `validate_unused_textures.py` is wired into pre-commit as `stages: [manual]` only. CI cannot run it, so invoke the manual hook when a texture audit is needed.
- `validate_set_variables.py` runs **CI-only**, `--strict` (its unused-variable backlog was cleared). No pre-commit hook; run it directly (`python3 tools/validation/validate_set_variables.py`) for a local check.
- `validate_scripted_localisation.py` runs **CI-only**, `--strict` (its missing/unused scripted-loc backlog was cleared). No pre-commit hook; run it directly for a local check.

## Check notes

- `validate_variables.py` carries a **clamp-range conflict** check (WARNING, `clamp-range-conflict`). It harvests every literal `clamp_variable = { var = X min = A max = B }` and flags any `check_variable` on `X` that compares against a value outside `A..B` (dead logic — always true or always false), plus the inverse scale slip: a sub-1 value compared against a variable clamped to a wide integer range. That second half is the `taliban_strength > 0.19` shape, the same failure class as the `threat > 40` trap in `general-rules.md`. It is deliberately anchored on the clamp rather than on observed value spread — a plain "this variable is compared on two scales" heuristic fires on `treasury`, `inflation_rate_var` and every percentage display variable, which legitimately use both. Variables only ever written by `set_temp_variable` are excluded: a clamp on a scratch parameter (`pp_gain`) constrains that one invocation, not the variable, so its range is no invariant for checks elsewhere.

- `validate_oob_units.py` also slot-checks every `create_equipment_variant` ship design (shared resolver: `tools/validation/naval_module_slots.py`). That widened its run gate well past OOB files: it is now routed on `history/countries/`, `common/national_focus/`, `events/`, `common/decisions/`, `common/special_projects/` and all of `common/scripted_effects/`, in both the pre-commit registry (`tools/precommit_validate.py`) and the CI `oob` path filter. Those two lists and the golden test in `tools/tests/precommit_validate_test.py` must move together. Findings are **errors** — the backlog was cleared first, so any hit is a regression. Non-ship variants are skipped by design; tank and plane slots are not validated anywhere yet, and their frequently-empty `allowed_module_categories` blocks mean the naval resolver cannot be pointed at them as-is.

## Tooling deprecation watch

- `pre-commit/mirrors-prettier` is archived upstream. Maintained fork: `rbubley/mirrors-prettier`. Migrate next time the prettier pin needs touching.
