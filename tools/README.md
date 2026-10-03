# Millennium Dawn Tools

Development tools and scripts used by the Millennium Dawn team for quality assurance, asset management, and mod publishing.

## Requirements

Python 3.12 or newer is required. CI installs 3.12 on Linux, macOS, and Windows.
Ruff, mypy, pylint, and pyright target 3.12 in `pyproject.toml`.

Some scripts rely on non-native packages for Python. The dependency lists live
in `pyproject.toml` under `[dependency-groups]`. Install them from the repo root
(pip 25.1+):

```bash
pip install --group runtime   # requests, pillow (for the scripts that need them)
pip install --group dev       # pytest (xdist, cov), coverage, pyyaml, Ruff, Black, Pylint, mypy
```

`python tools/dev_setup.py` installs these for you as part of the dev setup.
`dev` includes a smaller `test` group, which is all the CI test jobs install.

Python quality checks run on `tools/` in pre-commit and CI:

```bash
python -m pytest -n auto --cov --cov-branch --cov-report= --cov-fail-under=0
python -m coverage report
ruff check tools
black --check tools
pylint tools -j 0 --reports=no --score=no
mypy
```

`-n auto` and `-j 0` use every core. `coverage report` owns the coverage
threshold, so the pytest run only collects.

Black is the canonical formatter. Mypy checks the typed report and validator-core
surfaces declared in `pyproject.toml`; the remaining scripts are migrated in
small, behavior-tested slices rather than hidden behind broad ignores.

## Maintaining Tools

Keep code local and readable. Reuse shared helpers when they fit; do not add a
wrapper or framework for one call site. Runtime dependencies stay within the
`runtime` group in `pyproject.toml`; analysis and development dependencies are separate.
Black formats Python; Ruff checks lint and import order.

### Text Writes

Every text-mode write passes `newline=""` to prevent Windows from turning LF into
CRLF. Use explicit `open`, not `Path.write_text`, per the repository's write policy.
Specify encoding: script `.txt` files use
`encoding="utf-8"`, never `utf-8-sig`; localisation `.yml` needs its BOM.
`tools/tests/text_write_newline_test.py` enforces this and lists the rare intentional
platform-native writes. `.gitattributes` and `.editorconfig` keep the repository on LF.

### Review Checklist

- Preserve public re-exports in `shared_utils.py`, `validator_common.py`, and the other
  hub modules listed in `pyproject.toml`. Check downstream imports before removing an
  apparently unused name. For new explicit re-exports, use `from module import X as X`
  rather than adding a lint suppression.
- Reuse staged-file selection (`MD_STAGED_FILES`) instead of walking the full repository
  or calling `git diff --cached` repeatedly. Check each tool's intended directory set.
- Bound caches, subprocess runtimes, and worker counts. Use the shared CPU-budget
  helpers rather than hard-coded pool sizes; avoid multiprocessing for tiny inputs.
- Report I/O and subprocess failures. Do not silently return an empty result or use
  `errors="ignore"` to discard bad bytes. If replacement decoding is intentional,
  warn about it. Avoid broad exception handlers that hide the cause.
- Check parser edge cases and reported line numbers. Compile reused regexes once.
  Use existing collection, parser, timing, and root-resolution helpers where appropriate.
- Read [Validation Pipeline](../.claude/docs/validation-pipeline.md) before changing
  hook/CI selection or strictness. A new strict check needs an authorized baseline
  audit and triage before rollout.

### Regression Tests

Tests belong under `tools/tests/` and end in `_test.py`; `test_*.py` is not collected.
The suite runs in parallel workers, so a test writes only under `tmp_path`, never
into the real repository tree. Another worker may be scanning that tree.
Add regression coverage with changed validator, fixer, or report behavior. Run
`python -m pytest` before merging any `tools/` change, and fix failures in the same
change. Never delete, skip, or weaken a test to reach green. A correct behavior change
updates its regression expectations; a broken implementation gets fixed instead.

## Quick Start

Use `run.py` to run any tool by short name — no need to remember subdirectory paths:

```bash
python3 tools/run.py --list                              # see all available tools
python3 tools/run.py estimate_gdp USA --all              # run a tool by name
python3 tools/run.py find_idea common/ideas/Greek.txt    # partial names work too
python3 tools/run.py publish_workshop release --version 1.12.3  # pass args through
python3 tools/run.py gfx_entry_generator                  # works on any platform
```

### Fix changelog ordering

```bash
python3 tools/merge_changelog.py --fix
```

This sorts only the current version's entries within each category. Untagged
entries come first, followed by the first country tag. Equal tags keep their
order. Blank lines between entries are dropped and repeated blank lines become
one. Older versions, entry text, and duplicate entries are left alone. Resolve
conflict markers first. The Git merge driver also applies this ordering after a
successful merge.

The merge driver keeps a PR's new entry in the category the PR put it under. If
main started a new version, the entry moves to the same category there. A PR
whose category main no longer has is skipped for a human to resolve.

### Validation timing baselines

Save the Actions data without timing instrumentation:

```bash
gh run view RUN_ID --attempt ATTEMPT --json databaseId,attempt,headSha,displayTitle,status,conclusion,createdAt,startedAt,updatedAt,jobs > timing-RUN_ID-ATTEMPT.json
```

Add a `metadata` object to each export. Its required fields are `workload`,
`runner`, `tool`, `python`, `dependencies`, `cache` (`cold` or `warm`),
`worker_budget`, and `baseSha`. For example, this is user-supplied metadata,
not independently verified by the report:

```json
{
  "metadata": {
    "workload": "tools-tests",
    "runner": "ubuntu-24.04",
    "tool": "6bf489e",
    "python": "3.12.0",
    "dependencies": { "pytest": "9.1.0", "ruff": "0.15.17" },
    "cache": "cold",
    "worker_budget": 4,
    "baseSha": "4bce0fe"
  }
}
```

Run the same workload at least three times for cold-cache and three times for
warm-cache samples, keeping those fields identical within each set. Missing
memory or cache-hit counters are unknown, not zero. Fewer than three matching
samples is not an accepted baseline and does not support a speed claim. Then
run:

```bash
python3 tools/run.py validation_timing_report timing-*.json
```

The report lists each real Actions job and step, overall run span, and summed
job time. It ignores synthetic Checks API jobs that have no `steps`, excludes
incomplete or unsuccessful runs from summaries, and keeps revisions, cache
modes, and job/step outcomes separate. Existing section timers and CI artifact
logs are the timing mechanism. Do not instrument subprocess elapsed time with
parent wait timestamps. `databaseId` plus positive integer `attempt` identifies
an export, so duplicate files are ignored while distinct reruns are retained.
Run history alone is not a controlled baseline and does not establish a
performance gain. No workflow scheduling, worker count, checkout scope, or cache
portability changes are part of this report.

Observed run `34426341721` is illustrative only: head
`3a6f37f9c5677f0276fc1ff8f57802b294b5362a`, base
`4bce0fe79f9dd293a40a7200c99c63e5a58bb111`, Linux job 422s, worktree 131s,
coverage 95s, integration 64s, prepare 119s, core batch 283s, targeted-a 143s,
and targeted-b 115s. It is not a comparable baseline for this worktree.

## Directory Structure

```
tools/
├── analysis/          Analysis, reference finders, metrics
├── assets/            DDS conversion, GFX generation, texture tools
├── generators/        Content generators (tribute ideas, focus names)
├── linting/           Style checkers, formatters, encoding validators
├── publishing/        Steam Workshop publishing
├── report_lib/        PR validation report renderer + GitHub Checks API client
├── shared/            Test harness helpers and repo-anchored paths
├── standardization/   Auto-standardizers for focuses, events, decisions, ideas
├── tests/             All Python tests for tools/ (root scripts plus domain subdirs)
├── validation/        Content validators (events, decisions, variables, etc.)
├── shared_utils.py    Shared utilities (Colors, FileOpener, path helpers, arg parsers)
├── loc.py             Localisation utilities
├── logging_tool.py    Logging utility
├── precommit_validate.py Pre-commit hook: runs the commit-stage validators in parallel
├── standardize_staged.py Pre-commit hook: routes staged files to standardizers
├── generate_validation_report.py CI: generates PR validation reports
├── validate_tools.py  CI: validates Python scripts in tools/
├── COMMENT_STYLE.md   Comment style for Python tooling (why, not what)
└── README.md
```

### Architecture quick-reference

- **Writing a new validator?** Subclass `BaseValidator` from `tools/validation/validator_common.py`. Prefer `add_error(category, msg, file, line)` for structured issues; `_report(list_of_strings, ...)` still works and now auto-parses common `path:line - msg` formats into file+line for the PR comment's inline annotations.
- **Writing a new linter or fixer?** Import helpers from `tools/shared_utils.py`. Skip `validator_common` — linters don't emit the structured issue stream validators produce.
- **Reading validator output?** Import from `tools/report_lib`. It parses the JSON sidecars each validator writes and renders the PR comment + GitHub Check Runs.
- **Writing comments?** See [COMMENT_STYLE.md](COMMENT_STYLE.md). Default to none; add one when the _why_ is non-obvious.

### Writing a new validator

1. Create `tools/validation/validate_<topic>.py`.
2. Subclass `BaseValidator` from `validator_common`. Implement `run_validations(self, files: List[str]) -> None`.
3. Use `self.add_error(category, message, file, line)` for structured issues. The PR report renderer picks these up for inline annotations.
4. Use `DEFAULT_EXTRA_SKIP_PATTERNS` from `validator_common` for `EXTRA_SKIP_PATTERNS` (extend with domain-specific patterns if needed).
5. Wire into CI: add a `ValidatorSpec` for it in `tools/validation/validator_batches.py` (batch, changed-file groups, `--strict`). This is the gate for most validators — they run CI-only.
6. Decide if it should also run on `git commit`. Heavy cross-reference validators stay CI-only. A fast validator can join the commit-stage set: add it to the `_REGISTRY` in `tools/precommit_validate.py` (with its path rules and `--strict` flag) and pin its selection in `tools/tests/precommit_validate_test.py`. The `config_drift_test` enforces that every validator runs on pre-commit or CI.
7. Add tests in `tools/tests/validation/`.

```python
#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

import disk_cache
from validator_common import (
    BaseValidator,
    Colors,
    DEFAULT_EXTRA_SKIP_PATTERNS,
    Severity,
    run_validator_main,
    should_skip_file,
)

EXTRA_SKIP_PATTERNS = DEFAULT_EXTRA_SKIP_PATTERNS


class MyValidator(BaseValidator):
    def run_validations(self, files):
        for path in files:
            if should_skip_file(path, EXTRA_SKIP_PATTERNS):
                continue
            content = disk_cache.per_file_cached_by_content(
                self.mod_path, "my_ns", path, Path(path).read_text(encoding="utf-8"),
                lambda: self._validate_file(path),
            )
            # results already stored via add_error inside _validate_file

    def _validate_file(self, path):
        # ... validation logic ...
        self.add_error("my_category", "Something is wrong", path, line=42)


if __name__ == "__main__":
    run_validator_main(MyValidator, "My custom validation")
```

### Common imports from `shared_utils`

| Symbol                                                | Use                                                                                           |
| ----------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| `Colors`                                              | ANSI color constants (`GREEN`, `RED`, `YELLOW`, etc.)                                         |
| `DEFAULT_EXTRA_SKIP_PATTERNS`                         | `["FR_loc"]` — base skip patterns for validators                                              |
| `clean_filepath(path)`                                | Trim absolute path to start from `common/`, `events/`, etc.                                   |
| `should_skip_file(path, extra)`                       | Check if a file matches skip patterns                                                         |
| `strip_comments(text)`                                | Remove `#`-comments from HOI4 script text                                                     |
| `FileOpener`                                          | LRU-cached file reader (8192 entries)                                                         |
| `add_standard_file_arguments(parser, input_help=...)` | Add shared `input_file`, `--output`, `--backup`, and `--verbose` arguments                    |
| `create_validation_parser(desc)`                      | Argparse factory for validators (`--path`, `--strict`, `--staged`, `--no-cache`, `--workers`) |
| `create_linting_parser(desc)`                         | Argparse factory for linting scripts (`--mode`, `--files`, `--workers`)                       |
| `create_standard_parser(desc)`                        | Argparse factory for file-processing tools, including `--no-color`                            |
| `run_validator_main(cls, desc)`                       | Entry point for validators, parses args, creates instance, runs, exits                        |

## Scripts by Category

### Linting (`linting/`)

Style checkers, formatters, and encoding validators. These are used in pre-commit hooks and CI.

| Script                                | Description                                                                                                                                                                                                                                                                                                                                                                               |
| ------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **check_common_mistakes.py**          | Detects common scripting mistakes: bad value ranges, `allowed`/`cancel` no-ops, `ai_will_do factor` vs `base`, division instead of multiplication, stat comparisons with the wrong trigger name (`stability >` vs `has_stability >`), malformed leader rotations in `*_political_leaders.txt`. `--output FILE` also writes the `FILE`-stem `.json` sidecar the CI validation report reads |
| **fix_styling.py**                    | Comprehensive auto-fixer for style issues (tabs, spacing, braces, whitespace)                                                                                                                                                                                                                                                                                                             |
| **fix_line_endings.py**               | Converts CRLF to LF line endings                                                                                                                                                                                                                                                                                                                                                          |
| **fix_loc_yaml.py**                   | Fixes localisation YAML issues (quotes, tabs, colons, version keys)                                                                                                                                                                                                                                                                                                                       |
| **validate_localization_encoding.py** | Validates and fixes UTF-8 BOM encoding for localisation files                                                                                                                                                                                                                                                                                                                             |
| **validate_mod_encoding.py**          | Checks UTF-8 encoding for `.mod` files                                                                                                                                                                                                                                                                                                                                                    |

### Validation (`validation/`)

Content validators run in CI via matrix strategy. See `validation/README.md` for the full list and check details.

`validate_common_mistakes.py` owns the fast scripting checks formerly run as a
separate lint hook. The linting module remains its implementation library and
direct compatibility entry point.

### Standardization (`standardization/`)

Auto-standardizers for focus trees, events, decisions, and ideas. See `standardization/README.md` for details.

### Assets (`assets/`)

DDS conversion, GFX entry generation, texture and flag tools.

| Script                         | Description                                                                       |
| ------------------------------ | --------------------------------------------------------------------------------- |
| **batchdds-2.py**              | Self-contained Python DDS converter (DXT1/DXT5, no external dependencies)         |
| **convert_to_legacy_dds.py**   | Converts DX10/sRGB DDS files to legacy ARGB8888 for HOI4 compatibility            |
| **duplicate_icon.py**          | Detects duplicate icon files in a focus tree file                                 |
| **find_duplicate_textures.py** | Finds duplicate texture files in the mod                                          |
| **flag-reference-checker.py**  | Validates flag references across the mod                                          |
| **gfx_entry_generator_gui.py** | GFX sprite entry generator with GUI, calls into the root `gfx_entry_generator.py` |
| **resize_decision_icons.py**   | Resizes wrong-slot decision icon art in place or as a sibling sprite              |
| **state_gfx.py**               | Extracts province colors from state files and renders them on the map             |

### Analysis (`analysis/`)

Metrics, reference analysis, and review tools.

| Script                              | Description                                                                                                                                                     |
| ----------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **ai_path_report.py**               | Reports one country's AI path rule, flag wiring, focus ownership, killswitch orphans, and the burdens/mechanics the AI must be able to resolve (issue #3162)    |
| **calculate_days.py**               | Calculates days from January 1st for the HOI4 date system                                                                                                       |
| **estimate_gdp.py**                 | Estimates starting GDP for country tags using MD's building formulas                                                                                            |
| **event_load.py**                   | Reports how many events the yearly pulse schedules for one country and when, flagging years where several land in the same window                               |
| **validation_timing_report.py**     | Summarizes saved GitHub Actions validation job and step timings, grouped by compatible revision and environment                                                 |
| **find_idea_references.py**         | Finds which ideas from a file are referenced elsewhere in the codebase                                                                                          |
| **find_scripted_loc_references.py** | Checks whether scripted localisation names are actually referenced                                                                                              |
| **pre_place_power_plants.py**       | Bakes fossil_powerplant + composite_plant counts into `history/states/` to skip startup loops. Re-run after edits to the energy formula or country/state setup. |
| **review_branch.py**                | Generates a diff summary of the current branch vs main                                                                                                          |
| **search_add_ideas.py**             | Searches for `add_ideas` / `add_timed_idea` usage across the codebase                                                                                           |

### Generators (`generators/`)

Content generation tools.

| Script                          | Description                                                                                                                                                                                                                                         |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **add_international_system.py** | Adds a tab to the International Systems screen: strip layout, open/close wiring, title and stub files. `--icon` takes a premade icon (`--list-icons`) or a transparent image and converts it to the tab style; `--preview` draws the strip to a PNG |
| **generate_tribute_ideas.py**   | Generates tribute idea definitions and localisation for all countries                                                                                                                                                                               |

Premade tab icons reuse existing mod art, including icons already used elsewhere in the UI. Custom images must have a transparent background; opaque logos and unreadable image files are rejected before any files are written.

### Publishing (`publishing/`)

| Script                  | Description                                                      |
| ----------------------- | ---------------------------------------------------------------- |
| **publish_workshop.py** | Publishes the mod to the Steam Workshop (release, beta, or test) |

See the [Workshop Publishing Guide](#workshop-publishing-guide) below for full usage details.

### Report Library (`report_lib/`)

Internal package used by `generate_validation_report.py` to render PR comments and post GitHub Check Runs. Its inputs are the JSON sidecars produced by each validator plus the `suite-run.json` artifacts the tools-tests jobs upload.

| Module            | Responsibility                                                                                 |
| ----------------- | ---------------------------------------------------------------------------------------------- |
| **models.py**     | `Issue`, `ValidatorRun`, `ReportContext` dataclasses                                           |
| **loader.py**     | Reads `.json` sidecars and `suite-run.json`; falls back to parsing `.log` text when missing    |
| **dedupe.py**     | Collapses cross-validator duplicates, preserving first-seen order                              |
| **markdown.py**   | Renders the report Markdown: verdict banner, Tools/Mod test sections, issues-by-file, raw logs |
| **truncation.py** | Drops heavy sections when the body exceeds 60 KB, keeping the summary                          |
| **comment.py**    | Find-by-marker + PATCH/POST logic for the bot-authored PR comment                              |
| **checks_api.py** | One Check Run per CI job with up to 50 annotations per request                                 |

Tests live in `tests/report_lib/` and run on every PR via the `test-suite.yml` workflow.

### Tests (`tests/`)

| Script                             | Description                                                       |
| ---------------------------------- | ----------------------------------------------------------------- |
| **staged_validators_test.py**      | Tests staged validators using synthetic temporary files           |
| **staged_validators_real_test.py** | Tests staged validators against real mod files with known issues  |
| **staged_harness_test.py**         | Checks that both harnesses fail on a crash, timeout, or no result |

Tests for individual validators live in `tests/validation/`:

| Script                               | Description                                                                                                              |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------ |
| **all_validators_test.py**           | Suite-wide smoke test: every `validate_*.py` must expose a `BaseValidator` subclass and run cleanly on an empty mod tree |
| **validate_simplifications_test.py** | Unit tests for the scope-merge and two-bucket `random_list` detectors, including suppression edge cases                  |

### Root-Level Scripts

Hook entry points, CI tools, shared libraries, and other scripts that stay at the `tools/` root.

| Script                            | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **precommit_validate.py**         | Pre-commit hook (`md-validate-content`): runs the commit-stage validators in parallel, sharing one staged-file list                                                                                                                                                                                                                                                                                                                                                                                    |
| **standardize_staged.py**         | Pre-commit hook: routes staged files to the correct standardizer                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| **generate_validation_report.py** | CI: renders the PR validation comment + posts GitHub Check Runs                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| **merge_changelog.py**            | CI: git merge driver the changelog conflict fixer uses to merge `Changelog.txt` entries without duplicating edited lines                                                                                                                                                                                                                                                                                                                                                                               |
| **validate_tools.py**             | CI: validates Python scripts in the tools directory                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| **gfx_entry_generator.py**        | GFX sprite entry generator (cross-platform, merges into existing `.gfx` files)                                                                                                                                                                                                                                                                                                                                                                                                                         |
| **shared_utils.py**               | Shared utilities: `Colors` class, `FileOpener` (LRU cache), `clean_filepath()`, `should_skip_file()`, `DEFAULT_EXTRA_SKIP_PATTERNS`, argparse helpers (`add_standard_file_arguments`, `create_validation_parser`, `create_linting_parser`, `create_standard_parser`), entry points (`run_validator_main`, `run_tool_main`), `find_hoi4_install()` (`$HOI4_PATH`, then Steam's `libraryfolders.vdf`, the VS Code HOI4 extension `installPath` settings, then fixed paths), `extract_block_from_text()`. |
| **loc.py**                        | Localisation utilities                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| **logging_tool.py**               | Logging utility                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| **cleanup_or.py**                 | Library for `linting/check_common_mistakes.py`: finds redundant `AND`/single-condition `OR` blocks                                                                                                                                                                                                                                                                                                                                                                                                     |
| **assign_mio_icons.py**           | Manual tool: assigns MIO trait icons deterministically from the trait's winning modifier                                                                                                                                                                                                                                                                                                                                                                                                               |
| **summarize_game_log.py**         | Manual tool: parses scripted `log =` lines out of game.log into a "what happened" report after a test run                                                                                                                                                                                                                                                                                                                                                                                              |
| **sync_dynamic_tokens.py**        | Manual tool: regenerates `common/synchronized_dynamic_tokens` from error.log                                                                                                                                                                                                                                                                                                                                                                                                                           |

---

## Workshop Publishing Guide

`publishing/publish_workshop.py` handles uploading the mod to the Steam Workshop. It supports three targets (**release**, **beta**, and **test**). Full upload is the default; `--base-ref` selects a diff-only upload. Every upload requires `--version`.

### Prerequisites

- **SteamCMD** must be installed and either on your `PATH` or in one of the standard locations (`/usr/bin/steamcmd`, `C:\steamcmd\steamcmd.exe`, etc.).
- A Steam account with publish permissions on the Workshop items.

### Authentication

Provide your Steam username in one of two ways:

```bash
# Via environment variable
export STEAM_USERNAME=YourSteamUser

# Or via CLI flag
python3 tools/publishing/publish_workshop.py release --version 1.12.3 --username YourSteamUser
```

SteamCMD will prompt for your password and Steam Guard code interactively.

### Usage

#### Full Upload (release)

Uploads the entire mod (minus dev/CI files) to the release Workshop item:

```bash
python3 tools/publishing/publish_workshop.py release --version 1.12.3
```

#### Full Upload (beta)

Same as above but targets the beta Workshop item:

```bash
python3 tools/publishing/publish_workshop.py beta --version 1.12.3b
```

#### Full Upload (test)

Uploads to the test Workshop item with `TEST` banners:

```bash
python3 tools/publishing/publish_workshop.py test --version 2.0.1
```

All modes stage tracked `HEAD`; commit the intended content before publishing.
The optional `--full` flag explicitly selects the default full upload.

#### Diff-Only Upload (beta)

Uploads only files changed since a given git ref. Useful for pushing incremental beta updates without re-uploading the entire mod:

```bash
python3 tools/publishing/publish_workshop.py beta --base-ref v1.12.3b --version 1.12.4b
```

The script uses `git diff` against the base ref to identify changed files, copies
tracked `HEAD`, then prunes unchanged files. Deletions require a full upload.
`descriptor.mod` and `thumbnail.png` are always included.

#### Version String

Required `--version X.Y.Z` rewrites `version=` in the uploaded `descriptor.mod` and
both version banner keys in all ten production frontend locale files inside the
staging copy. Accepted values are `X.Y.Z`, legacy suffixes such as `X.Y.Zb` or
`X.Y.Zrc1`, and SemVer prereleases such as `X.Y.Z-beta.5`. One leading `v` or
`V` is optional.

The committed banners end with a `DEV` marker (`开发版` in Simplified Chinese).
Beta uploads show `BETA`, test uploads show `TEST`, and release uploads have no
build marker. Existing `DEV`, `BETA`, `TEST`, or `开发版` markers are replaced
across all ten locales.

Every diff publish carries all ten banner files, even when they are not part
of the diff. Missing, excluded, duplicate, or malformed banners abort before
upload rather than uploading a mismatch. The repo's own files are never touched.

Default output shows upload progress, warnings, errors, and the saved log path.
`--verbose` also prints detailed timing, VDF contents, the command, and SteamCMD
output. Full diagnostics and timing remain in the log in either mode.

#### Cleanup and Interrupted Runs

Each run stages into its own `md_publish_*` directory under the system temp
directory and removes it when the run ends: on success, on failure, on Ctrl+C,
and on `kill` or a closed terminal. The `git archive` and SteamCMD children are
stopped first. On Linux and macOS the upload runs in its own process group, so
SteamCMD's child processes stop with it. The interactive login stays attached to
your terminal, so Ctrl+C reaches it directly. On Windows only the SteamCMD
process itself is stopped, and that path is not verified.

Cleanup cannot run when the publisher is force-killed (`kill -9`, Task Manager)
or the machine crashes.

If staging cannot be removed, the tool prints a warning with the leftover path
and still reports the original error. To recover by hand, check that no
`steamcmd` process is still running, then delete that one directory. Do not
delete other `md_publish_*` directories by name or age. Another run may own
them.

Upload logs are saved as `md_publish_*.log` in the same temp directory, outside
staging. Retries append to the same log. Logs are never removed automatically,
so delete them yourself once you no longer need them.

Separate runs never share staging. That does not make two uploads to the same
Workshop item safe to run at once.

#### English Workshop Description

Public Workshop descriptions stay unchanged unless `--sync-description` is supplied:

```bash
python3 tools/publishing/publish_workshop.py release --version 2.0.1 --sync-description
```

This reads `descriptions/descriptions_EN.txt` from tracked `HEAD` in the staging
copy and sends it as the selected Workshop item's English description. Only the
`[b]Current Version:[/b]` field is updated to the normalized `--version` value.
Review and commit the source first: checksums, HOI4 compatibility, tutorial
versions, links, and all other text are copied as written. The repository source
is never modified, and neither the Workshop title nor visibility is changed.

This opt-in works with full and diff uploads; the description is read before
diff pruning. Missing or excluded files, invalid UTF-8, empty text, NUL bytes,
missing/duplicate/malformed Current Version fields, or descriptions exceeding
Steam's 8000-byte UTF-8 limit abort before Steam login. No translated descriptions
are synchronized. `--changenote` remains the separate update note.

### What Gets Excluded

The following are automatically excluded from all uploads:

`.git`, `.github`, `.claude`, `.vscode`, `docs`, `tools`, `resources`, `scenario_tests`, `CLAUDE.md`, `CONTRIBUTING.md`, `CODEOWNERS`, `README.md`, `Changelog.txt`, `Millennium_Dawn.mod`, and other dev/CI artifacts.

Use `--exclude PATTERN` to add extra exclusions, or `--no-default-excludes` to skip the built-in list entirely.

### Options Reference

| Flag                        | Description                                                            |
| --------------------------- | ---------------------------------------------------------------------- |
| `release` / `beta` / `test` | Which Workshop item to target                                          |
| `--full`                    | Upload the entire mod (default)                                        |
| `--base-ref REF`            | Upload only files changed since REF (mutually exclusive with `--full`) |
| `--username USER`           | Steam username (default: `$STEAM_USERNAME`)                            |
| `--mod-id ID`               | Override the default Workshop mod ID                                   |
| `--exclude PATTERN`         | Extra exclude pattern (repeatable)                                     |
| `--no-default-excludes`     | Skip the built-in exclude list                                         |
| `--sync-description`        | Update the English Workshop description from its tracked source        |
| `--version VERSION`         | Required uploaded version. Invalid or incomplete banners abort.        |
| `--changenote TEXT`         | Workshop update note, separate from the public description             |
| `--verbose`                 | Print detailed timing, VDF, command, and SteamCMD output               |

### Workshop Mod IDs

| Target  | Mod ID       |
| ------- | ------------ |
| release | `2777392649` |
| beta    | `3374271790` |
| test    | `2777133449` |

## Old Folder

The `old/` directory contains unused or outdated tools kept for historical reference. They are not expected to be used in current development.
