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

# Save combined report to a file
python3 tools/validation/run_all_validators.py --output report.txt
```

Output is color-coded. Pass `--no-color` for plain text (e.g. in log files).

---

## Validators

### Standard (run by default)

| Validator                             | Checks                                                                                                                                                                                                                                                                                                                                                                                                                            |
| ------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **validate_agency_upgrades.py**       | Intelligence agency upgrade prerequisites and capability references are defined; no duplicate upgrade IDs                                                                                                                                                                                                                                                                                                                         |
| **validate_ai_equipment.py**          | Nations blocked from generic AI equipment roles without custom coverage; duplicate role names                                                                                                                                                                                                                                                                                                                                     |
| **validate_ai_navy.py**               | Naval taskforce ship types, fleet template references, mission types, composition sizes                                                                                                                                                                                                                                                                                                                                           |
| **validate_ai_roles.py**              | `role_ratio`/`build_army` references match defined roles in `common/ai_templates/`                                                                                                                                                                                                                                                                                                                                                |
| **validate_cosmetic_tags.py**         | Missing cosmetic tags (used but never set); unused cosmetic tag colors                                                                                                                                                                                                                                                                                                                                                            |
| **validate_decisions.py**             | Duplicate decisions; unused categories; missing AI weight; custom cost tooltip presence                                                                                                                                                                                                                                                                                                                                           |
| **validate_defines.py**               | MD defines exist in vanilla with correct namespace; duplicate defines within MD                                                                                                                                                                                                                                                                                                                                                   |
| **validate_events.py**                | Events missing `is_triggered_only = yes`; unsupported title/desc combinations; redundant long-form event calls; every `picture` resolves to an MD-defined sprite (vanilla event pictures are not allowed, so this gates in CI without the game installed)                                                                                                                                                                         |
| **validate_factions.py**              | Faction template/goal/rule/icon references exist; no duplicate IDs; valid rule types                                                                                                                                                                                                                                                                                                                                              |
| **validate_focus_tree.py**            | Duplicate focus IDs; orphan focuses; missing prerequisite targets; missing loc keys; dependency cycles. Opt-in: `--missing-icons` (focuses whose `icon` sprite is undefined)                                                                                                                                                                                                                                                      |
| **validate_gfx_references.py**        | Sprite names in `.gui` and scripted-GUI files are defined in `interface/*.gfx`; unused sprite definitions                                                                                                                                                                                                                                                                                                                         |
| **validate_history_techs.py**         | History files grant all prerequisite technologies, and equipment variant designs only use modules the country has researched (DLC-aware)                                                                                                                                                                                                                                                                                          |
| **validate_ideas.py**                 | Idea `allowed`/`visible` blocks reference defined ideas; no duplicate idea IDs; `GFX_idea_categories` has enough frames for the politics-view categories. Unused-ideas check is enabled by default (pass `--no-unused-ideas` to disable). Opt-in: `--missing-loc` (ideas without name/desc loc keys), `--missing-icons` (ideas whose `picture` sprite is undefined), `--suggest-consolidation` (advisory loc consolidation hints) |
| **validate_localisation.py**          | Duplicate keys; unpaired brackets; color code mismatches; orphaned `_tt` tooltip keys                                                                                                                                                                                                                                                                                                                                             |
| **validate_modifiers.py**             | Modifier references in focuses/decisions/ideas exist in the defines or vanilla; no duplicate modifier definitions                                                                                                                                                                                                                                                                                                                 |
| **validate_oob_units.py**             | Unit names in OOB files and AI templates match canonical names in `common/units/`                                                                                                                                                                                                                                                                                                                                                 |
| **validate_on_actions.py**            | Events referenced in `on_actions` are defined; `is_triggered_only` enforced; no duplicate refs in the same trigger block                                                                                                                                                                                                                                                                                                          |
| **validate_scripted_gui.py**          | Scripted GUI window/property names are defined; referenced effects/triggers exist                                                                                                                                                                                                                                                                                                                                                 |
| **validate_scripted_localisation.py** | Scripted loc keys used but not defined; defined but never referenced; missing GFX icons                                                                                                                                                                                                                                                                                                                                           |
| **validate_scripted_params.py**       | Scripted params declared in `common/scripted_params/` are referenced with compatible types                                                                                                                                                                                                                                                                                                                                        |
| **validate_style.py**                 | Brace matching, indent/bracket balance, spacing/quotes, focus ID format, event log standards                                                                                                                                                                                                                                                                                                                                      |
| **validate_simplifications.py**       | Suggests merging consecutive same-scope blocks (`TAG = { } TAG = { }`, state ids, `PREV`, `var:`); WARNING-only, skips OR/random_list contexts                                                                                                                                                                                                                                                                                    |

### Heavy validators

These cross-reference the entire codebase. A disk cache under `.validation_cache/` keeps re-runs fast — see [DISK_CACHE.md](DISK_CACHE.md).

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

### Pre-commit stages

Most MD validators are set to `stages: [manual]` in `.pre-commit-config.yaml` and do **not** run on ordinary `git commit`. This keeps commit latency low for contributors. The heavy cross-reference validators (`validate_scripted_gui`, `validate_localisation`, `validate_scripted_localisation`) and most others are in this category. They run in CI instead; see the comments in `.pre-commit-config.yaml` for per-hook rationale.

A handful of lighter validators (`validate_oob_units`, `validate_ai_roles`, `validate_defines`, `validate_ai_navy`, `validate_ai_equipment`, `validate_agency_upgrades`, `validate_ideas`, `validate_events`) run on every commit without a `stages` restriction.

To run a manual hook locally:

```bash
pre-commit run md-validate-scripted-gui --hook-stage manual
pre-commit run --hook-stage manual   # all manual hooks at once
```

---

## Architecture

All validators extend `BaseValidator` from `validator_common.py`. To add a new validator:

1. Create `validate_<name>.py` in this directory
2. Subclass `BaseValidator`, set `TITLE = "..."`, implement `run_validations()`
3. Use `self.add_error(category, message, file, line)` / `self.add_warning(...)` to record issues
4. To parse many files, call `self.parse_files_cached(patterns, namespace, parse_fn)` — it's staged-aware, case-preserving, and disk-caches each parse keyed on file content. Use a unique `namespace` string per call to avoid cache collisions.
5. Call `run_validator_main(YourValidator, "Description")` at the bottom
6. `run_all_validators.py` auto-discovers it on the next run — no registration needed

`validator_common.py` also provides `strip_comments()`, `FileOpener`, `DataCleaner`, `HOI4_BUILTIN_BLOCKS`, and `scan_meta_constructed_names()` for use in validators.

Module-level constants and pool-worker functions (those passed to `_pool_map`) must be defined at the **top level** — not inside the validator class — so `multiprocessing.Pool` can pickle them. Classmethods on a validator subclass are not directly picklable; use standalone functions for pool dispatch.

### `validator_common.py` public API

| Symbol                                                                                                                               | Type      | Description                                                                                                                                                                                                                                                |
| ------------------------------------------------------------------------------------------------------------------------------------ | --------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BaseValidator`                                                                                                                      | class     | Base for all validators. Provides `_pool_map`, `_collect_files`, `_report`, `_log_section`, timing, and JSON output                                                                                                                                        |
| `BaseValidator.parse_files_cached(patterns, namespace, parse_fn, *, lowercase=False, strip_comments_flag=True, ignore_staged=False)` | method    | Collect files matching glob patterns (staged-aware), read each case-preserving, strip comments, and per-file disk-cache the result keyed on content; returns `{path: parse_fn(text, path)}`. Use this as the standard way to parse many files of one kind. |
| `scan_meta_constructed_names(files, defined_names)`                                                                                  | function  | Scan files for `meta_effect`/`meta_trigger` template patterns and match against defined names                                                                                                                                                              |
| `HOI4_BUILTIN_BLOCKS`                                                                                                                | frozenset | All known HOI4 built-in effect/trigger block names                                                                                                                                                                                                         |
| `Colors`                                                                                                                             | class     | ANSI escape codes for colored output (`HEADER`, `BLUE`, `CYAN`, `GREEN`, `YELLOW`, `RED`, `ENDC`, `BOLD`, `UNDERLINE`)                                                                                                                                     |
| `Severity`                                                                                                                           | class     | String constants: `Severity.ERROR = "error"`, `Severity.WARNING = "warning"`                                                                                                                                                                               |
| `Issue`                                                                                                                              | dataclass | Structured issue with `severity`, `category`, `message`, `file`, `line` fields and `to_dict()` / `to_key()` methods                                                                                                                                        |
| `MD_LOG_LEVEL`                                                                                                                       | env var   | Set to `ERROR` / `WARNING` (default) / `INFO` to control per-validator verbosity                                                                                                                                                                           |

---

## Credits

Based on Kaiserreich Autotests by [Pelmen323](https://github.com/Pelmen323), adapted for Millennium Dawn.
