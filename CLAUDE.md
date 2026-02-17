# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Millennium Dawn is a Hearts of Iron IV mod set in the modern era (2000-present). It's a Paradox Interactive game modification with extensive game systems including focus trees, events, decisions, ideas, technologies, and more.

## Development Commands

### Pre-commit Setup

```bash
pip install pre-commit
pre-commit install
```

### Running Validation

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Run specific style checks
python3 tools/check_basic_style.py
python3 tools/check_basic_style_2.py
python3 tools/coding_standards.py
python3 tools/check_braces.py

# Validate localization encoding
python3 tools/validate_localization_encoding.py
```

### Python Tools

```bash
# Install tool dependencies
pip install -r tools/requirements.txt

# Common tools
python3 tools/gfx_entry_generator.py          # Generate GFX entries for UI
python3 tools/logging_tool.py                # Logging utilities
python3 tools/standardize_focus_tree.py      # Format focus trees
```

## Code Architecture

### Directory Structure

- `common/` - Game data (focuses, ideas, events, decisions, technologies, modifiers, AI configs)
- `localisation/` - Language files (English yml files with UTF-8 BOM)
- `events/` - Event chains and triggered events
- `history/` - Historical country data, states, units
- `map/` - Terrain, states, provinces
- `interface/` - UI definitions
- `gfx/` - Graphics assets (loadingscreens, portraits, unit models)
- `tools/` - Python development and validation scripts
- `docs/` - Development documentation

### Key File Patterns

- HOI4 mod files use `.txt` extension but are Paradox script format
- Localization uses `.yml` files in `localisation/english/`
- Focus trees: `common/national_focus/`
- Ideas: `common/ideas/`
- Events: `events/` directory

## Code Style Guidelines

### Localization Files (.yml)

- 1-space indentation
- Remove trailing 0/1 after colons (e.g., use `key: "value"` not `key: "value0"`)
- UTF-8 with BOM encoding required

### Script Files (.txt)

- 1 tab indentation (4 spaces equivalent)
- Comments go above or below code blocks (not inline)
- Focus ID format: `TAG_focus_name_here`
- Include logging in completion rewards: `log = "[GetDateText]: [Root.GetName]: Focus TAG_your_focus"`

### Focus Tree Structure (specific to this mod)

- File naming: `00_` for shared trees, `05_` for country-specific
- Order: `allow_branch` → `prerequisite/mutually_exclusive` → `available/bypass/cancel` → `completion_reward` → `ai_will_do`
- Use `relative_position_id` for positioning
- Always include `ai_will_do` with game options checks

### Ideas

- Include `allowed_civil_war = { always = yes }` for civil war tags
- Remove unnecessary `allowed = { always = no }` statements (default behavior)
- Use logging in `on_add` only when needed

## Important Resources

- [Game Rules Reference](./docs/player-tutorials/game-rules.md) - Complete guide to all game rules
- [Code Resources](./docs/dev-resources/code-resource.md) - Modifiers, effects, and how-to guides
- [Focus Tree Styling Guide](./.cursor/.ai-guides/code_styling.md)
- [Error Debug Codes](./docs/dev-resources/error-debug-codes.md)
- [Focus Tree Lifecycle](./docs/dev-resources/focus-tree-lifecycle-checklist.md)
- [Code Stylization Guide](./docs/dev-resources/code-stylization-guide.md)
- [Contributing Guidelines](./CONTRIBUTING.md)

## Common Development Tasks

### Adding a New Country

1. Create country definition in `common/countries/`
2. Add localization in `localisation/english/`
3. Create focus tree in `common/national_focus/`
4. Add ideas in `common/ideas/`
5. Add historical data in `history/countries/`

### Adding Events

1. Create event file in `events/` or add to existing
2. Add localization keys
3. Use `is_triggered_only = yes` for triggered events
4. Include proper logging in effects

### Running the Mod

The mod is loaded through the Paradox launcher. Copy or symlink the mod directory to your HOI4 mod folder, or use Steam workshop.
