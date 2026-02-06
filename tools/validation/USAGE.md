# Validation Tools - Quick Reference

## Available Validators

| Script | Purpose |
|--------|---------|
| `run_all_validators.sh` | Run all validators at once (recommended) |
| `validate_variables.py` | Validate flags and event targets |
| `validate_scripted_localisation.py` | Validate scripted localisation definitions |

## Common Usage Patterns

### Run All Validators

```bash
# Basic validation
./tools/validation/run_all_validators.sh

# Strict mode (fail on any issues)
./tools/validation/run_all_validators.sh --strict

# Only check staged files (before committing)
./tools/validation/run_all_validators.sh --staged --strict

# Without colors (for CI/CD)
./tools/validation/run_all_validators.sh --strict --no-color
```

### Individual Validators

#### Variables and Event Targets
```bash
# Check all files
python3 tools/validation/validate_variables.py

# Check staged files only
python3 tools/validation/validate_variables.py --staged

# Save report to file
python3 tools/validation/validate_variables.py --output report.txt
```

#### Scripted Localisation
```bash
# Check all files
python3 tools/validation/validate_scripted_localisation.py

# Check staged files only
python3 tools/validation/validate_scripted_localisation.py --staged

# Save report to file
python3 tools/validation/validate_scripted_localisation.py --output loc-report.txt
```

## Common Options

All validators support these options:

| Option | Description |
|--------|-------------|
| `--path <path>` | Validate a specific directory (default: current directory) |
| `--staged` | Only validate git staged files |
| `--strict` | Exit with error code if issues found (useful for CI/CD) |
| `--output <file>` | Save results to a file |
| `--no-color` | Disable colored output |

## Integration

### Pre-Commit Hook

Copy `pre-commit-hook-example.sh` to `.git/hooks/pre-commit`:
```bash
cp tools/validation/pre-commit-hook-example.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### CI/CD Pipeline

Add to your CI/CD configuration:
```bash
./tools/validation/run_all_validators.sh --strict --no-color
```

## What Gets Validated

### Variables (validate_variables.py)
- ✓ Country flags (set/used/cleared consistency)
- ✓ State flags (set/used/cleared consistency)
- ✓ Global flags (set/used/cleared consistency)
- ✓ Event targets (saved/used/cleared consistency)

### Scripted Localisation (validate_scripted_localisation.py)
- ✓ Defined scripted localisations in `common/scripted_localisation/`
- ✓ Referenced scripted localisations across all game files (`.txt`)
- ✓ Referenced scripted localisations in interface files (`.gui`)
- ✓ Referenced scripted localisations in localisation files (`.yml` - with `_scripted_loc` or `_scl` suffix)
- ✓ Unused definitions
- ✓ Missing definitions

## Troubleshooting

### "No staged files found"
Make sure you've staged your changes:
```bash
git add your_files.txt
./tools/validation/run_all_validators.sh --staged
```

### False Positives
Some false positives are expected, especially for scripted localisation. The validators have built-in filters for common patterns, but you may need to manually verify some results.

### Performance
Validating the entire mod can take 1-2 minutes. Use `--staged` to only check modified files for faster validation.

## Getting Help

For detailed documentation, see [README.md](README.md)

For issues or questions, check the script source code or contact the development team.
