# Millennium Dawn Tools

Development tools and scripts used by the Millennium Dawn team for quality assurance, asset management, and mod publishing.

## Requirements

Some scripts rely on non-native packages for Python. Install them with:

```bash
pip install -r requirements.txt
```

**Packages:** requests, pillow

## Scripts

### Validation & Code Standards

| Script                                | Description                                                            |
| ------------------------------------- | ---------------------------------------------------------------------- |
| **check_basic_style.py**              | Style checker for mod `.txt` files (used in pre-commit + CI)           |
| **check_basic_style_2.py**            | Extended style checker with additional rules (used in pre-commit + CI) |
| **check_braces.py**                   | Validates matching braces in mod script files                          |
| **check_common_mistakes.py**          | Detects common scripting mistakes from CLAUDE.md rules                 |
| **coding_standards.py**               | Enforces Millennium Dawn coding standards                              |
| **validate_localization_encoding.py** | Validates and fixes UTF-8 BOM encoding for localisation files          |
| **validate_mod_encoding.py**          | Checks UTF-8 encoding for `.mod` files                                 |
| **validate_staged.py**                | Runs validators against staged files for pre-commit                    |
| **validate_tools.py**                 | Meta-validator for Python scripts in the tools directory               |

### Formatting & Cleanup

| Script                  | Description                                                                                   |
| ----------------------- | --------------------------------------------------------------------------------------------- |
| **fix_styling.py**      | Comprehensive auto-fixer for style issues (tabs, spacing, braces, trailing whitespace)        |
| **fix_line_endings.py** | Converts CRLF to LF line endings                                                              |
| **fix_loc_yaml.py**     | Fixes localisation YAML issues (quotes, tabs, colons, version keys) — used as pre-commit hook |

### Standardization

The `standardization/` directory contains the standardization pipeline. See its own README for details.

| Script                    | Description                          |
| ------------------------- | ------------------------------------ |
| **standardize_staged.py** | Runs standardization on staged files |

### Asset & Graphics

| Script                           | Description                                                               |
| -------------------------------- | ------------------------------------------------------------------------- |
| **batchDDS.py**                  | Generates nvtt_export batch scripts for DDS conversion                    |
| **batchdds-2.py**                | Self-contained Python DDS converter (DXT1/DXT5, no external dependencies) |
| **convert_to_legacy_dds.py**     | Converts DX10/sRGB DDS files to legacy ARGB8888 for HOI4 compatibility    |
| **duplicate_icon.py**            | Detects duplicate icon files                                              |
| **find_duplicate_textures.py**   | Finds duplicate texture files in the mod                                  |
| **flag-reference-checker.py**    | Validates flag references across the mod                                  |
| **gfx_entry_generator.py**       | Generates GFX sprite entries for goals and interface elements             |
| **gfx_entry_generator_gui.py**   | GUI version of the GFX entry generator                                    |
| **gfx_entry_generator_linux.py** | Cross-platform GFX entry generator (pathlib-based, deterministic sort)    |
| **state_gfx.py**                 | Extracts province colors from state files and renders them on the map     |

### Focus Tree & Content

| Script                                | Description                                                           |
| ------------------------------------- | --------------------------------------------------------------------- |
| **count_of_focuses.py**               | Counts focuses in focus tree files                                    |
| **text_to_focus_and_focus_to_loc.py** | Converts text to focus IDs and generates localisation entries         |
| **generate_tribute_ideas.py**         | Generates tribute idea definitions and localisation for all countries |
| **search_add_ideas.py**               | Searches for `add_ideas` / `add_timed_idea` usage across the codebase |

### Analysis & Reference

| Script                              | Description                                                            |
| ----------------------------------- | ---------------------------------------------------------------------- |
| **calculate_days.py**               | Calculates days from January 1st for the HOI4 date system              |
| **estimate_gdp.py**                 | Estimates starting GDP for country tags using MD's building formulas   |
| **find_idea_references.py**         | Finds which ideas from a file are referenced elsewhere in the codebase |
| **find_scripted_loc_references.py** | Checks whether scripted localisation names are actually referenced     |
| **generate_validation_report.py**   | Generates a validation report across the mod                           |

### Publishing

| Script                  | Description                                               |
| ----------------------- | --------------------------------------------------------- |
| **publish_workshop.py** | Publishes the mod to the Steam Workshop (release or beta) |

See the [Workshop Publishing Guide](#workshop-publishing-guide) below for full usage details.

### Internal / Shared

| Script               | Description                                            |
| -------------------- | ------------------------------------------------------ |
| **loc.py**           | Localisation utilities                                 |
| **logging_tool.py**  | Logging utility for development                        |
| **path_utils.py**    | Path manipulation utilities                            |
| **shared_utils.py**  | Shared utility functions used by other scripts         |
| **review_branch.py** | Generates a diff summary of the current branch vs main |

### Test Scripts

| Script                             | Description                                                      |
| ---------------------------------- | ---------------------------------------------------------------- |
| **staged_validators_test.py**      | Tests staged validators using synthetic temporary files          |
| **staged_validators_real_test.py** | Tests staged validators against real mod files with known issues |

## Documentation

- **gfxEntryGenerator.md** — Detailed guide on using the GFX entry generator
- **README.md** — This file

---

## Workshop Publishing Guide

`publish_workshop.py` handles uploading the mod to the Steam Workshop. It supports two targets (**release** and **beta**) and two modes (**full upload** and **diff-only upload**).

### Prerequisites

- **SteamCMD** must be installed and either on your `PATH` or in one of the standard locations (`/usr/bin/steamcmd`, `C:\steamcmd\steamcmd.exe`, etc.).
- A Steam account with publish permissions on the Workshop items.

### Authentication

Provide your Steam username in one of two ways:

```bash
# Via environment variable
export STEAM_USERNAME=YourSteamUser

# Or via CLI flag
python3 tools/publish_workshop.py release --full --username YourSteamUser
```

SteamCMD will prompt for your password and Steam Guard code interactively.

### Usage

#### Full Upload (release)

Uploads the entire mod (minus dev/CI files) to the release Workshop item:

```bash
python3 tools/publish_workshop.py release --full
```

#### Full Upload (beta)

Same as above but targets the beta Workshop item:

```bash
python3 tools/publish_workshop.py beta --full
```

#### Diff-Only Upload (beta)

Uploads only files changed since a given git ref. Useful for pushing incremental beta updates without re-uploading the entire mod:

```bash
python3 tools/publish_workshop.py beta --base-ref v1.12.3b
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
