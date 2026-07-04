# Millennium Dawn: A Modern Day Mod

![Millennium Dawn Header](https://i.imgur.com/hpEdk0J.png)
![Millennium Dawn Features](https://i.imgur.com/MYaznE7.png)

Millennium Dawn is a multi-mod project set in 2000 and continues to the modern day and beyond.
The mod boasts new and unique tech trees, focus trees, events, and decisions to immerse you in the intricacies of the modern era.

This repo is the source code for [Millennium Dawn: A Modern Day Mod](https://steamcommunity.com/sharedfiles/filedetails/?id=2777392649)

## Quick Links

- [Discord](http://discord.gg/millenniumdawn) - Community and support
- [Reddit](https://www.reddit.com/r/MillenniumDawn/)
- [Git Setup Guide](https://docs.google.com/document/d/1V8DLowqEOSmlgazlHeC-hLZzLki5e6cWhQO_ZK6HVYs) - Repository setup
- [Contribution Guide](./CONTRIBUTING.md) - Contribution policies

## Features

- **Economic Systems**: Taxation, debt management, international investment
- **Political Mechanics**: Internal factions, influence, party systems
- **Rich Content**: Focus trees, events, decisions for 150+ nations
- **Modern Era**: Realistic geopolitical organizations (EU, NATO, etc.)

## Contributing

Available issues can be found in our [GitHub Issues](https://github.com/MillenniumDawn/Millennium-Dawn/issues)

We also take open source contributions of any form whether they be localization, code, additions, content, or more.

1. Fork the repository
2. Create a feature branch
3. Make changes following style guidelines
4. Run pre-commit hooks
5. Update [Changelog.txt](./Changelog.txt)
6. Add yourself to [AUTHORS.md](./docs/src/content/misc/authors.md)
7. Submit a pull request

See [Contributing](./CONTRIBUTING.md) for more details including stylization, pre-commit information and more.

**NOTE**: Millennium Dawn's development team allows for AI assisted coding if and only if the developer is capable and is able to review the code it produces.
More details can be found in the team's [Contribution Policy](./CONTRIBUTING.md#ai-policy)

## Project Structure

```
common/          - Game data (focuses, ideas, events, decisions)
localisation/    - Language files
events/          - Event chains
history/         - Historical country data
map/             - Terrain, states
interface/       - UI definitions
gfx/             - Graphics assets
tools/           - Scripts for supporting development such as validators, standardizations, and other utilities
docs/            - Development documentation
```

## Documentation

| Topic               | Location                                                                                                    |
| ------------------- | ----------------------------------------------------------------------------------------------------------- |
| Code Style          | [docs/src/content/resources/code-stylization-guide.md](./docs/src/content/resources/code-stylization-guide.md) |
| Modifiers & Effects | [docs/src/content/resources/code-resource.md](./docs/src/content/resources/code-resource.md)                   |
| Game Rules          | [docs/src/content/tutorials/game-rules.md](./docs/src/content/tutorials/game-rules.md)                         |

## License

See [LICENSE](./LICENSE) file for details.

## Security

See [SECURITY](./SECURITY.md) file for security details.

---

_Created by the Millennium Dawn Development Team_
