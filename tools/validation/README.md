# Millennium Dawn Validation Tools

Comprehensive validation tools for Millennium Dawn mod that check for issues with flags, event targets, and scripted localisation.

## Quick Start

Run all validators at once:
```bash
# Run all validators
./tools/validation/run_all_validators.sh

# Run all validators with strict mode (exit with error if issues found)
./tools/validation/run_all_validators.sh --strict

# Run all validators on staged files only (for pre-commit)
./tools/validation/run_all_validators.sh --staged --strict
```

Individual validators can also be run separately (see sections below).

---

# Variable and Event Target Validation

## Features

- **Line Numbers**: Shows exact line numbers where issues occur
- **Colored Output**: Color-coded results for easy reading (can be disabled)
- **File Output**: Save results to a file for later review
- **Git Integration**: Validate only staged files for pre-commit hooks
- **Comprehensive Checks**: Validates country/state/global flags and event targets
- **Case Sensitive**: Ensures Linux and macOS compatibility by validating exact case matching

## Installation

No installation required. The script is self-contained in `validate_variables.py`.

## Usage

### Basic Usage

```bash
# Validate current directory
python tools/validation/validate_variables.py

# Validate specific mod directory
python tools/validation/validate_variables.py --path /path/to/mod
```

### Advanced Options

```bash
# Exit with error code if issues found (useful for CI/CD)
python tools/validation/validate_variables.py --strict

# Save output to file
python tools/validation/validate_variables.py --output report.txt

# Validate only git staged files (for pre-commit hook)
python tools/validation/validate_variables.py --staged --strict

# Disable colored output
python tools/validation/validate_variables.py --no-color

# Combine options
python tools/validation/validate_variables.py --staged --strict --output validation.log --no-color
```

## What It Checks

### Flags (Country, State, Global)

1. **Cleared but not set**: Flags that are cleared with `clr_X_flag` but never set with `set_X_flag`
2. **Missing**: Flags that are used with `has_X_flag` but never set with `set_X_flag`
3. **Unused**: Flags that are set with `set_X_flag` but never checked with `has_X_flag`

**Important**: All flag checks are **case-sensitive**. This means:
- `my_flag` and `My_Flag` are considered different flags
- This ensures proper compatibility across Linux, macOS, and Windows
- Helps catch potential bugs from inconsistent casing

### Event Targets

1. **Cleared but not set**: Event targets cleared but never saved
2. **Missing**: Event targets used but never saved
3. **Unused**: Event targets saved but never used (checks both .txt and .yml files)

**Important**: All event target checks are **case-sensitive** for cross-platform compatibility.

## Output Format

Results include:
- **File path** (relative to mod root)
- **Line number** where the issue occurs
- **Variable/target name**

Example output:
```
================================================================================
Checking missing country flags (used but not set)...
================================================================================
ERROR: Missing country flags were encountered - they are not set via 'set_country_flag'. Flags with @ are skipped.
ERROR:   events/example.txt:42 - my_test_flag
ERROR:   events/another.txt:156 - some_other_flag
ERROR: 2 issues found
```

## Pre-Commit Hook

The validator is **already integrated** into `.pre-commit-config.yaml` and runs automatically on commit.

**How it works:**
- When you `git commit`, the validator runs with `--staged` flag
- It **only scans the files you're committing** (not the entire mod)
- Validates the **full content** of staged files for any issues
- If issues are found, the commit is blocked until they're fixed

**Note:** The staged mode validates the complete content of staged files, not just the changed lines. This ensures:
- New issues aren't introduced by your changes
- Existing issues in files you're modifying are caught
- Cross-file references are properly validated

To bypass the validator for a single commit (not recommended):
```bash
git commit --no-verify
```

## Ignored Directories

The following directories are automatically skipped:
- `gfx/`
- `tools/`
- `resources/`
- `docs/`
- `map/`

## Command-Line Arguments

| Argument | Description |
|----------|-------------|
| `--path PATH` | Path to mod folder (default: current directory) |
| `--strict` | Exit with error code if issues found |
| `--output FILE`, `-o FILE` | Save results to file |
| `--no-color` | Disable ANSI color codes |
| `--staged` | Only validate git staged files |

## Exit Codes

- `0`: Validation passed or no strict mode
- `1`: Validation failed (only in strict mode)

## False Positives

The validator has built-in lists of known false positives that are automatically skipped. These include:
- Variables with `@` (templates)
- Variables with `[` (dynamic variables)
- Specific known exceptions (like `kr_current_version`)

## Example Workflows

### Local Development
```bash
# Quick check before committing
python tools/validation/validate_variables.py --staged

# Full validation with detailed report
python tools/validation/validate_variables.py --output validation-report.txt
```

### CI/CD Pipeline
```bash
# Fail the build if validation fails
python tools/validation/validate_variables.py --strict --no-color --output ci-report.txt
```

### Pre-Commit Hook
```bash
# Automatically validate staged files
python tools/validation/validate_variables.py --staged --strict --no-color
```

## Troubleshooting

### No staged files found
If using `--staged` and getting "No staged .txt or .yml files found", make sure you have staged your changes:
```bash
git add your_file.txt
python tools/validation/validate_variables.py --staged
```

### Colors not showing
Some terminals may not support ANSI colors. Use `--no-color` to disable them.

### Performance
For large mods, the validator may take a minute or two to scan all files. The `--staged` option significantly speeds this up by only checking modified files.

---

# Scripted Localisation Validation

Validation tool for scripted localisation definitions in `common/scripted_localisation/`.

## Features

- **Line Numbers**: Shows exact line numbers where issues occur
- **Colored Output**: Color-coded results for easy reading (can be disabled)
- **File Output**: Save results to a file for later review
- **Git Integration**: Validate only staged files for pre-commit hooks
- **Comprehensive Checks**: Validates both defined and used scripted localisations
- **Interface Support**: Scans both game files (`.txt`) and interface files (`.gui`)

## What It Checks

### Scripted Localisation

1. **Missing**: Scripted localisations that are used/referenced but not defined in `common/scripted_localisation/`
2. **Unused**: Scripted localisations that are defined but never referenced anywhere

The validator scans:
- All `.txt` game files for `localization_key = <name>` references (used in scripted localisation definitions)
- All `.gui` interface files for `text = "[name]"` patterns (used in GUI)
- All `.yml` localisation files for `"[name_scripted_loc]"` or `"[name_scl]"` patterns (scripted loc references)
- All scripted localisation definitions in `common/scripted_localisation/`

**Important**: The validator correctly distinguishes between:
- **Scripted localisation** (dynamic): Defined in `common/scripted_localisation/`, ends with `_scripted_loc` or `_scl`
- **Regular localisation** (static): Defined in `.yml` files, regular `[key]` without scripted loc suffixes

The validator only flags keys ending with `_scripted_loc` or `_scl` in `.yml` files, avoiding false positives for regular localisation.

## Usage

### Basic Usage

```bash
# Validate current directory
python tools/validation/validate_scripted_localisation.py

# Validate specific mod directory
python tools/validation/validate_scripted_localisation.py --path /path/to/mod
```

### Advanced Options

```bash
# Exit with error code if issues found (useful for CI/CD)
python tools/validation/validate_scripted_localisation.py --strict

# Save output to file
python tools/validation/validate_scripted_localisation.py --output report.txt

# Validate only git staged files (for pre-commit hook)
python tools/validation/validate_scripted_localisation.py --staged --strict

# Disable colored output
python tools/validation/validate_scripted_localisation.py --no-color
```

## Output Format

Results include:
- **File path** (relative to mod root)
- **Line number** where the issue occurs
- **Scripted localisation name**

Example output:
```
================================================================================
Checking missing scripted localisations (used but not defined)...
================================================================================
ERROR: Missing scripted localisations were encountered - they are referenced but not defined in common/scripted_localisation/.
WARNING: Note: Some of these may be regular localisation keys rather than scripted localisation. Verify manually.
ERROR:   events/example.txt:42 - debt_display
ERROR: 1 issues found
```

## How It Works

The validator specifically looks for scripted localisation in these contexts:

### In Game Files (`.txt`)
Checks `localization_key = <name>` patterns, which appear in:
- Scripted localisation definitions (`defined_text` blocks)
- NOT in bracketed form `[key]` (those are regular localisation)

### In Interface Files (`.gui`)
Checks `text = "[name]"` patterns, which is how scripted loc is referenced in GUI

### In Localisation Files (`.yml`)
Checks `"[name_scripted_loc]"` or `"[name_scl]"` patterns only
- Only keys ending with `_scripted_loc` or `_scl` are considered scripted localisation
- This naming convention distinguishes them from regular localisation keys

### What It Ignores
The validator automatically ignores:
- Regular bracketed keys in `.yml` files (without `_scripted_loc` or `_scl` suffix)
- Scope references with dots (`Root.GetName`, `THIS.GetAdjective`)
- Variables with special characters (`?`, `@`, etc.)

## Command-Line Arguments

| Argument | Description |
|----------|-------------|
| `--path PATH` | Path to mod folder (default: current directory) |
| `--strict` | Exit with error code if issues found |
| `--output FILE`, `-o FILE` | Save results to file |
| `--no-color` | Disable ANSI color codes |
| `--staged` | Only validate git staged files |

## Example Workflows

### Local Development
```bash
# Quick check before committing
python tools/validation/validate_scripted_localisation.py --staged

# Full validation with detailed report
python tools/validation/validate_scripted_localisation.py --output scripted-loc-report.txt
```

### CI/CD Pipeline
```bash
# Fail the build if validation fails
python tools/validation/validate_scripted_localisation.py --strict --no-color --output ci-report.txt
```

---

## Credits

Based on Kaiserreich Autotests by [Pelmen323](https://github.com/Pelmen323)
