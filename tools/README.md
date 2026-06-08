# Millennium Dawn Tools

Development tools and scripts used by the Millennium Dawn team for quality assurance, asset management, and mod publishing.

## Requirements

Some scripts rely on non-native packages for Python. Install them with:

```bash
pip install -r requirements.txt
```

**Packages:** requests, pillow

## Quick Start

Use `run.py` to run any tool by short name — no need to remember subdirectory paths:

```bash
python3 tools/run.py --list                              # see all available tools
python3 tools/run.py estimate_gdp USA --all              # run a tool by name
python3 tools/run.py find_idea common/ideas/Greek.txt    # partial names work too
python3 tools/run.py publish_workshop release --full      # pass args through
python3 tools/run.py gfx_entry_generator_linux            # works on any platform
```

## Directory Structure

```
tools/
├── analysis/          Analysis, reference finders, metrics
├── assets/            DDS conversion, GFX generation, texture tools
├── generators/        Content generators (tribute ideas, focus names)
├── linting/           Style checkers, formatters, encoding validators
├── publishing/        Steam Workshop publishing
├── report_lib/        PR validation report renderer + GitHub Checks API client
├── standardization/   Auto-standardizers for focuses, events, decisions, ideas
├── tests/             Test suites for validators
├── validation/        Content validators (events, decisions, variables, etc.)
├── shared_utils.py    Shared utilities (Colors, FileOpener, path helpers, arg parsers)
├── loc.py             Localisation utilities
├── logging_tool.py    Logging utility
├── validate_staged.py Pre-commit hook: routes staged files to validators
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
5. Wire into CI:
   - Add an entry to `.github/workflows/coding-pipeline.yml` in the `validate-core` or `validate-targeted` matrix.
   - Add a `stages: [manual]` entry in `.pre-commit-config.yaml` (validators are manual-only in pre-commit; CI runs them unconditionally).
6. Wire into `validate_staged.py` if the validator should run on staged files during pre-commit.
7. Add tests in `tools/validation/tests/`.

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

| Symbol                           | Use                                                                                           |
| -------------------------------- | --------------------------------------------------------------------------------------------- |
| `Colors`                         | ANSI color constants (`GREEN`, `RED`, `YELLOW`, etc.)                                         |
| `DEFAULT_EXTRA_SKIP_PATTERNS`    | `["FR_loc"]` — base skip patterns for validators                                              |
| `clean_filepath(path)`           | Trim absolute path to start from `common/`, `events/`, etc.                                   |
| `should_skip_file(path, extra)`  | Check if a file matches skip patterns                                                         |
| `strip_comments(text)`           | Remove `#`-comments from HOI4 script text                                                     |
| `FileOpener`                     | LRU-cached file reader (8192 entries)                                                         |
| `create_validation_parser(desc)` | Argparse factory for validators (`--path`, `--strict`, `--staged`, `--no-cache`, `--workers`) |
| `create_linting_parser(desc)`    | Argparse factory for linting scripts (`--mode`, `--files`, `--workers`)                       |
| `run_validator_main(cls, desc)`  | Entry point for validators — parses args, creates instance, runs, exits                       |

## Scripts by Category

### Linting (`linting/`)

Style checkers, formatters, and encoding validators. These are used in pre-commit hooks and CI.

| Script                                | Description                                                                                                                                       |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| **check_common_mistakes.py**          | Detects common scripting mistakes: bad value ranges, `allowed`/`cancel` no-ops, `ai_will_do factor` vs `base`, division instead of multiplication |
| **fix_styling.py**                    | Comprehensive auto-fixer for style issues (tabs, spacing, braces, whitespace)                                                                     |
| **fix_line_endings.py**               | Converts CRLF to LF line endings                                                                                                                  |
| **fix_loc_yaml.py**                   | Fixes localisation YAML issues (quotes, tabs, colons, version keys)                                                                               |
| **validate_localization_encoding.py** | Validates and fixes UTF-8 BOM encoding for localisation files                                                                                     |
| **validate_mod_encoding.py**          | Checks UTF-8 encoding for `.mod` files                                                                                                            |

### Validation (`validation/`)

Content validators run in CI via matrix strategy. See `validation/README.md` for full list of all 25 validators and their checks.

### Standardization (`standardization/`)

Auto-standardizers for focus trees, events, decisions, and ideas. See `standardization/README.md` for details.

### Assets (`assets/`)

DDS conversion, GFX entry generation, texture and flag tools.

| Script                           | Description                                                               |
| -------------------------------- | ------------------------------------------------------------------------- |
| **batchdds-2.py**                | Self-contained Python DDS converter (DXT1/DXT5, no external dependencies) |
| **convert_to_legacy_dds.py**     | Converts DX10/sRGB DDS files to legacy ARGB8888 for HOI4 compatibility    |
| **duplicate_icon.py**            | Detects duplicate icon files in a focus tree file                         |
| **find_duplicate_textures.py**   | Finds duplicate texture files in the mod                                  |
| **flag-reference-checker.py**    | Validates flag references across the mod                                  |
| **gfx_entry_generator.py**       | GFX sprite entry generator (Windows)                                      |
| **gfx_entry_generator_gui.py**   | GFX sprite entry generator with GUI (Windows)                             |
| **gfx_entry_generator_linux.py** | GFX sprite entry generator (cross-platform, deterministic sort)           |
| **state_gfx.py**                 | Extracts province colors from state files and renders them on the map     |

See `assets/gfxEntryGenerator.md` for the GFX entry generator guide.

### Analysis (`analysis/`)

Metrics, reference analysis, and review tools.

| Script                              | Description                                                                                                                                                     |
| ----------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **calculate_days.py**               | Calculates days from January 1st for the HOI4 date system                                                                                                       |
| **estimate_gdp.py**                 | Estimates starting GDP for country tags using MD's building formulas                                                                                            |
| **find_idea_references.py**         | Finds which ideas from a file are referenced elsewhere in the codebase                                                                                          |
| **find_scripted_loc_references.py** | Checks whether scripted localisation names are actually referenced                                                                                              |
| **pre_place_power_plants.py**       | Bakes fossil_powerplant + composite_plant counts into `history/states/` to skip startup loops. Re-run after edits to the energy formula or country/state setup. |
| **review_branch.py**                | Generates a diff summary of the current branch vs main                                                                                                          |
| **search_add_ideas.py**             | Searches for `add_ideas` / `add_timed_idea` usage across the codebase                                                                                           |

### Generators (`generators/`)

Content generation tools.

| Script                        | Description                                                           |
| ----------------------------- | --------------------------------------------------------------------- |
| **generate_tribute_ideas.py** | Generates tribute idea definitions and localisation for all countries |

### Publishing (`publishing/`)

| Script                  | Description                                               |
| ----------------------- | --------------------------------------------------------- |
| **publish_workshop.py** | Publishes the mod to the Steam Workshop (release or beta) |

See the [Workshop Publishing Guide](#workshop-publishing-guide) below for full usage details.

### Report Library (`report_lib/`)

Internal package used by `generate_validation_report.py` to render PR comments and post GitHub Check Runs. Its only inputs are the JSON sidecars produced by each validator.

| Module            | Responsibility                                                          |
| ----------------- | ----------------------------------------------------------------------- |
| **models.py**     | `Issue`, `ValidatorRun`, `ReportContext` dataclasses                    |
| **loader.py**     | Reads `.json` sidecars; falls back to parsing `.log` text when missing  |
| **dedupe.py**     | Collapses cross-validator duplicates, preserving first-seen order       |
| **markdown.py**   | Renders the report Markdown — summary table + issues-by-file + raw logs |
| **truncation.py** | Drops heavy sections when the body exceeds 60 KB, keeping the summary   |
| **comment.py**    | Find-by-marker + PATCH/POST logic for the bot-authored PR comment       |
| **checks_api.py** | One Check Run per validator with up to 50 annotations per run           |

Tests live in `report_lib/tests/` and run on every PR via the `tools-validation.yml` workflow.

### Tests (`tests/`)

| Script                             | Description                                                      |
| ---------------------------------- | ---------------------------------------------------------------- |
| **staged_validators_test.py**      | Tests staged validators using synthetic temporary files          |
| **staged_validators_real_test.py** | Tests staged validators against real mod files with known issues |

Tests for individual validators live in `validation/tests/`:

| Script                               | Description                                                                                                              |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------ |
| **all_validators_test.py**           | Suite-wide smoke test: every `validate_*.py` must expose a `BaseValidator` subclass and run cleanly on an empty mod tree |
| **validate_simplifications_test.py** | Unit tests for the scope-merge and two-bucket `random_list` detectors, including suppression edge cases                  |

### Root-Level Scripts

Hook entry points, CI tools, and shared libraries that stay at the `tools/` root.

| Script                            | Description                                                                                                                                                                                                                                                                                                                                        |
| --------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **validate_staged.py**            | Pre-commit hook: routes staged files to the correct validator                                                                                                                                                                                                                                                                                      |
| **standardize_staged.py**         | Pre-commit hook: routes staged files to the correct standardizer                                                                                                                                                                                                                                                                                   |
| **generate_validation_report.py** | CI: renders the PR validation comment + posts GitHub Check Runs                                                                                                                                                                                                                                                                                    |
| **validate_tools.py**             | CI: validates Python scripts in the tools directory                                                                                                                                                                                                                                                                                                |
| **shared_utils.py**               | Shared utilities: `Colors` class, `FileOpener` (LRU cache), `clean_filepath()`, `should_skip_file()`, `DEFAULT_EXTRA_SKIP_PATTERNS`, argparse factories (`create_validation_parser`, `create_linting_parser`, `create_standard_parser`), entry points (`run_validator_main`, `run_tool_main`), `find_hoi4_install()`, `extract_block_from_text()`. |
| **loc.py**                        | Localisation utilities                                                                                                                                                                                                                                                                                                                             |
| **logging_tool.py**               | Logging utility                                                                                                                                                                                                                                                                                                                                    |

---

## Workshop Publishing Guide

`publishing/publish_workshop.py` handles uploading the mod to the Steam Workshop. It supports two targets (**release** and **beta**) and two modes (**full upload** and **diff-only upload**).

### Prerequisites

- **SteamCMD** must be installed and either on your `PATH` or in one of the standard locations (`/usr/bin/steamcmd`, `C:\steamcmd\steamcmd.exe`, etc.).
- A Steam account with publish permissions on the Workshop items.

### Authentication

Provide your Steam username in one of two ways:

```bash
# Via environment variable
export STEAM_USERNAME=YourSteamUser

# Or via CLI flag
python3 tools/publishing/publish_workshop.py release --full --username YourSteamUser
```

SteamCMD will prompt for your password and Steam Guard code interactively.

### Usage

#### Full Upload (release)

Uploads the entire mod (minus dev/CI files) to the release Workshop item:

```bash
python3 tools/publishing/publish_workshop.py release --full
```

#### Full Upload (beta)

Same as above but targets the beta Workshop item:

```bash
python3 tools/publishing/publish_workshop.py beta --full
```

#### Diff-Only Upload (beta)

Uploads only files changed since a given git ref. Useful for pushing incremental beta updates without re-uploading the entire mod:

```bash
python3 tools/publishing/publish_workshop.py beta --base-ref v1.12.3b
```

The script uses `git log --diff-filter=ACM` to determine which files changed, copies the full repo, then prunes unchanged files before uploading. `descriptor.mod` and `thumbnail.png` are always included.

### What Gets Excluded

The following are automatically excluded from all uploads:

`.git`, `.github`, `.claude`, `.vscode`, `docs`, `tools`, `resources`, `scenario_tests`, `CLAUDE.md`, `CONTRIBUTING.md`, `CODEOWNERS`, `README.md`, `Changelog.txt`, `Millennium_Dawn.mod`, and other dev/CI artifacts.

Use `--exclude PATTERN` to add extra exclusions, or `--no-default-excludes` to skip the built-in list entirely.

### Options Reference

| Flag                    | Description                                                            |
| ----------------------- | ---------------------------------------------------------------------- |
| `release` / `beta`      | Which Workshop item to target                                          |
| `--full`                | Upload the entire mod                                                  |
| `--base-ref REF`        | Upload only files changed since REF (mutually exclusive with `--full`) |
| `--username USER`       | Steam username (default: `$STEAM_USERNAME`)                            |
| `--mod-id ID`           | Override the default Workshop mod ID                                   |
| `--exclude PATTERN`     | Extra exclude pattern (repeatable)                                     |
| `--no-default-excludes` | Skip the built-in exclude list                                         |

### Workshop Mod IDs

| Target  | Mod ID       |
| ------- | ------------ |
| release | `2777392649` |
| beta    | `3374271790` |

## Old Folder

The `old/` directory contains unused or outdated tools kept for historical reference. They are not expected to be used in current development.
