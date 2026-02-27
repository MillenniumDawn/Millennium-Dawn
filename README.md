# Millennium Dawn

A modern-era Hearts of Iron IV modification spanning from 2000 to the present day and beyond.

## Quick Links

- [Discord](http://discord.gg/millenniumdawn) - Community and support
- [Git Setup Guide](https://docs.google.com/document/d/1V8DLowqEOSmlgazlHeC-hLZzLki5e6cWhQO_ZK6HVYs) - Repository setup
- [Contribution Guide](./CONTRIBUTING.md) - Contribution policies

## Features

- **Economic Systems**: Taxation, debt management, international investment
- **Political Mechanics**: Internal factions, influence, party systems
- **Rich Content**: Focus trees, events, decisions for 150+ nations
- **Modern Era**: Realistic geopolitical organizations (EU, NATO, etc.)

## Development Setup

### Prerequisites

- Python 3.x (for development tools only)
- Hearts of Iron IV (for testing)

### Install Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

### Running Tests

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Run specific tools
python3 tools/check_basic_style.py
python3 tools/coding_standards.py
```

## Code Standards

### Localization (.yml)

- 1-space indentation
- UTF-8 with BOM
- No trailing 0/1 after colons

### Script Files (.txt)

- 1 tab indentation
- Comments above/below code blocks
- Follow naming conventions: `TAG_focus_name`

### Key Style Points

- Include logging: `log = "[GetDateText]: [Root.GetName]: ..."`
- Use `is_triggered_only = yes` for events
- Remove redundant code (`allowed = { always = no }`)

See [Code Stylization Guide](./docs/dev-resources/code-stylization-guide.md) for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes following style guidelines
4. Run pre-commit hooks
5. Update [Changelog.txt](./Changelog.txt)
6. Add yourself to [AUTHORS.md](./docs/misc/authors.md)
7. Submit a pull request

## Documentation

| Topic               | Location                                                                                       |
| ------------------- | ---------------------------------------------------------------------------------------------- |
| Code Style          | [docs/dev-resources/code-stylization-guide.md](./docs/dev-resources/code-stylization-guide.md) |
| Modifiers & Effects | [docs/dev-resources/code-resource.md](./docs/dev-resources/code-resource.md)                   |
| Game Rules          | [docs/dev-resources/game-rules.md](./docs/dev-resources/game-rules.md)                         |
| Focus Trees         | [.cursor/.ai-guides/code_styling.md](./.cursor/.ai-guides/code_styling.md)                     |

## Project Structure

```
common/          - Game data (focuses, ideas, events, decisions)
localisation/    - Language files
events/          - Event chains
history/         - Historical country data
map/             - Terrain, states
interface/       - UI definitions
gfx/             - Graphics assets
tools/           - Python development scripts
docs/            - Development documentation
```

## License

See [LICENSE](./LICENSE) file for details.

## Security

See [SECURITY](./SECURITY.md) file for security details.

---

_Created by the Millennium Dawn Development Team_
