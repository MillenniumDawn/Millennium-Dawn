# Millennium Dawn Standardization Tools

This directory contains Python scripts for automatically standardizing HOI4 mod files according to Millennium Dawn coding standards.

## Overview

The standardization tools help maintain consistent code formatting and best practices across the mod. They automatically:

- Format code blocks with proper indentation and spacing
- Add required logging where missing
- Remove performance-hurting code patterns
- Enforce Millennium Dawn specific formatting rules

## Available Standardizers

### Focus Trees (`standardize_focus_tree.py`)
Standardizes national focus files according to Millennium Dawn standards.

**Key features:**
- Enforces proper property ordering
- Adds missing logging to completion rewards and effects
- Formats search_filters into single lines
- Ensures ai_will_do is properly formatted

**Usage:**
```bash
python3 standardize_focus_tree.py input.txt -o output.txt --backup --verbose
```

### Events (`standardize_events.py`)
Standardizes event files according to Millennium Dawn standards.

**Key features:**
- Ensures `is_triggered_only = yes` for triggered events
- Adds logging to options only when they have effects
- Maintains proper property ordering
- Removes excessive blank lines

**Usage:**
```bash
python3 standardize_events.py input.txt -o output.txt --backup --verbose
```

### Decisions (`standardize_decisions.py`)
Standardizes decision files according to Millennium Dawn standards.

**Key features:**
- Adds logging to complete_effect blocks
- Enforces proper property ordering
- Maintains consistent formatting
- Preserves ai_will_do blocks

**Usage:**
```bash
python3 standardize_decisions.py input.txt -o output.txt --backup --verbose
```

### Ideas (`standardize_ideas.py`)
Standardizes idea files according to Millennium Dawn standards.

**Key features:**
- Removes performance-hurting properties (`allowed = { always = no }`, `cancel = { always = no }`)
- Adds logging to on_add/on_remove when they have effects
- Preserves allowed_civil_war for civil war tags
- Maintains proper formatting

**Usage:**
```bash
python3 standardize_ideas.py input.txt -o output.txt --backup --verbose
```

## Unified Interface

For convenience, use the unified `standardize.py` script:

```bash
# Standardize focus trees
python3 standardize.py focus input.txt -o output.txt --backup

# Standardize events
python3 standardize.py event input.txt --verbose

# Standardize decisions
python3 standardize.py decision input.txt

# Standardize ideas
python3 standardize.py idea input.txt -v
```

## Common Options

All standardizers support these command-line options:

- `input_file` - The file to standardize (required)
- `-o, --output` - Output file (default: overwrites input)
- `-b, --backup` - Create backup before modifying (recommended)
- `-v, --verbose` - Verbose output for debugging

## Code Standards Enforced

### Focus Trees
- Use `relative_position_id` for positioning
- Include logging in completion_reward/select_effect/bypass_effect
- Proper property ordering (id, icon, position, cost, prerequisites, etc.)
- ai_will_do always last

### Events
- Use `is_triggered_only = yes` for triggered events
- Log only options that have actual effects
- Proper property ordering
- Remove excessive blank lines

### Decisions
- Include logging in complete_effect
- Use `fire_only_once` sparingly
- Proper property ordering
- Include ai_will_do

### Ideas
- Remove `allowed = { always = no }` (performance optimization)
- Remove `cancel = { always = no }` (performance optimization)
- Remove empty `on_add = { log = "" }`
- Include `allowed_civil_war = { always = yes }` for civil war tags
- Log only when on_add/on_remove have actual effects

## Performance Optimizations

The standardizers automatically remove or optimize code patterns that hurt performance:

- **Division operations**: Suggest multiplication instead of division
- **Empty logging**: Remove `log = ""` statements
- **Default properties**: Remove `allowed = { always = no }` and `cancel = { always = no }`
- **MTTH events**: Warn about open-fire MTTH events
- **Arrays**: Suggest replacing `every_country`/`random_country` with specific arrays

## Architecture

The standardization tools use a modular architecture:

- `common_utils.py` - Shared utilities and base classes
- `BaseStandardizer` - Abstract base class for all standardizers
- Individual standardizer classes inherit from `BaseStandardizer`
- Each standardizer implements specific formatting rules for its file type

## Contributing

When adding new standardizers:

1. Inherit from `BaseStandardizer`
2. Implement `get_block_pattern()`, `extract_properties()`, and `format_block()`
3. Follow the existing code patterns
4. Add appropriate logging and error handling
5. Update this README with usage instructions

## Troubleshooting

### Common Issues

**Import errors**: Make sure you're running from the `tools/standardization/` directory
```bash
cd tools/standardization
python3 standardize.py focus input.txt
```

**File not found**: Verify the input file path is correct
```bash
ls -la input.txt  # Check if file exists
```

**Permission errors**: Ensure you have write permissions for the output directory
```bash
chmod 644 input.txt  # Make sure file is writable
```

### Debug Mode

Use `--verbose` to see detailed processing information:
```bash
python3 standardize.py focus input.txt --verbose
```

This will show:
- Files being processed
- Blocks being reformatted
- Properties being extracted
- Formatting decisions being made

## Integration with Development Workflow

### Pre-commit Hook

Consider adding standardization to your pre-commit hooks:

```bash
# In .git/hooks/pre-commit
#!/bin/bash
python3 tools/standardization/standardize.py focus common/national_focus/*.txt
python3 tools/standardization/standardize.py event events/*.txt
```

### CI/CD Pipeline

Add standardization checks to your continuous integration:

```yaml
# .github/workflows/standardize.yml
- name: Standardize Files
  run: |
    python3 tools/standardization/standardize.py focus common/national_focus/*.txt --backup
    python3 tools/standardization/standardize.py event events/*.txt --backup
```

## Related Documentation

- [Code Stylization Guide](../../docs/dev-resources/code-stylization-guide.md) - Complete coding standards
- [Performance Guidelines](../../docs/dev-resources/code-stylization-guide.md#performance-tips) - Performance optimization tips
- [Focus Tree Standards](../../docs/dev-resources/code-stylization-guide.md#focus-trees) - Focus-specific guidelines
