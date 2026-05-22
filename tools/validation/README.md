# Millennium Dawn Validation Tools

Content validators for the Millennium Dawn mod. All validators share a common CLI interface and can be run individually or all at once via `run_all_validators.py`.

## Quick Start

```bash
# Run all validators (from the mod root)
python3 tools/validation/run_all_validators.py

# Strict mode: exit non-zero if any issues found (used in CI)
python3 tools/validation/run_all_validators.py --strict

# Only check staged files (pre-commit mode)
python3 tools/validation/run_all_validators.py --staged --strict

# Include slow validators (set-variables, unused-scripted, variables, unused-textures)
python3 tools/validation/run_all_validators.py --include-slow

# Save combined report to a file
python3 tools/validation/run_all_validators.py --output report.txt
```

Output is color-coded. Pass `--no-color` for plain text (e.g. in log files).

---

## Validators

### Standard (run by default)

| Validator                             | Checks                                                                                                                                   |
| ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **validate_ai_equipment.py**          | Nations blocked from generic AI equipment roles without custom coverage; duplicate role names                                            |
| **validate_ai_navy.py**               | Naval taskforce ship types, fleet template references, mission types, composition sizes                                                  |
| **validate_ai_roles.py**              | `role_ratio`/`build_army` references match defined roles in `common/ai_templates/`                                                       |
| **validate_cosmetic_tags.py**         | Missing cosmetic tags (used but never set); unused cosmetic tag colors                                                                   |
| **validate_decisions.py**             | Duplicate decisions; unused categories; missing AI weight; custom cost tooltip presence                                                  |
| **validate_defines.py**               | MD defines exist in vanilla with correct namespace; duplicate defines within MD                                                          |
| **validate_events.py**                | Events missing `is_triggered_only = yes`; unsupported title/desc combinations; redundant long-form event calls                           |
| **validate_factions.py**              | Faction template/goal/rule/icon references exist; no duplicate IDs; valid rule types                                                     |
| **validate_history_techs.py**         | History files grant all prerequisite technologies, and equipment variant designs only use modules the country has researched (DLC-aware) |
| **validate_localisation.py**          | Duplicate keys; unpaired brackets; color code mismatches; orphaned `_tt` tooltip keys                                                    |
| **validate_oob_units.py**             | Unit names in OOB files and AI templates match canonical names in `common/units/`                                                        |
| **validate_scripted_localisation.py** | Scripted loc keys used but not defined; defined but never referenced; missing GFX icons                                                  |

### Slow (opt-in with `--include-slow`)

These validators scan a much larger portion of the codebase and take significantly longer to run. They are excluded from the default run and from CI to keep feedback fast.

| Validator                       | Checks                                                                             |
| ------------------------------- | ---------------------------------------------------------------------------------- |
| **validate_set_variables.py**   | Variables set with `set_variable` are actually used somewhere                      |
| **validate_unused_scripted.py** | Scripted effects/triggers defined but never called                                 |
| **validate_unused_textures.py** | Texture files not referenced in any `.gfx` file; `.gfx` entries with missing files |
| **validate_variables.py**       | Country/state/global flags and event targets: cleared-but-not-set, missing, unused |

---

## Common Flags

All validators accept the same set of flags:

| Flag                       | Description                                                  |
| -------------------------- | ------------------------------------------------------------ |
| `--path PATH`              | Path to the mod root (default: current directory)            |
| `--staged`                 | Only validate files currently staged in git                  |
| `--strict`                 | Exit with code `1` if any issues are found                   |
| `--output FILE`, `-o FILE` | Write results to a file in addition to stdout                |
| `--no-color`               | Disable ANSI color codes                                     |
| `--workers N`              | Number of parallel worker processes (default: CPU count / 2) |

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

Validators are integrated into `.pre-commit-config.yaml` and run automatically on commit. The hook passes `--staged` so only the files being committed are checked, keeping commit times fast.

To bypass for a single commit (not recommended):

```bash
git commit --no-verify
```

---

## Architecture

All validators extend `BaseValidator` from `validator_common.py`. To add a new validator:

1. Create `validate_<name>.py` in this directory
2. Subclass `BaseValidator`, set `TITLE = "..."`, implement `run_validations()`
3. Use `self.add_error(category, message, file, line)` / `self.add_warning(...)` to record issues
4. Call `run_validator_main(YourValidator, "Description")` at the bottom
5. `run_all_validators.py` auto-discovers it on the next run — no registration needed

`validator_common.py` also provides `strip_comments()`, `FileOpener`, `DataCleaner`, and `HOI4_BUILTIN_BLOCKS` for use in validators.

---

## Credits

Based on Kaiserreich Autotests by [Pelmen323](https://github.com/Pelmen323), adapted for Millennium Dawn.
