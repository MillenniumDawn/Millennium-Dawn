# Contributing to Millennium Dawn

Thank you for your interest in contributing to Millennium Dawn!

## Quick Links

- [Documentation](https://millenniumdawn.github.io/Millennium-Dawn/)
- [Discord](http://discord.gg/millenniumdawn)
- [Code Stylization Guide](./docs/dev-resources/code-stylization-guide.md)
- [Code Resources](./docs/dev-resources/code-resource.md)

## Development Setup

### Python (Required for Tools)

```bash
pip install pre-commit
pre-commit install
```

### Pre-commit Usage

```bash
# Run all hooks
pre-commit run --all-files

# Update hooks
pre-commit autoupdate
```

## Code Standards

### Localization (.yml)

- 1-space indentation
- UTF-8 with BOM encoding
- Remove trailing 0/1 after colons

### Script Files (.txt)

- 1 tab indentation
- Comments above/below code blocks
- Include logging in effects
- Follow naming conventions: `TAG_name_here`

### Key Rules

- Use `is_triggered_only = yes` for events
- Include `ai_will_do` in focuses
- Remove redundant code (`allowed = { always = no }`)

See [Code Stylization Guide](./docs/dev-resources/code-stylization-guide.md) for details.

## Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make changes following style guidelines
4. Run pre-commit hooks
5. Update [Changelog.txt](./Changelog.txt)
6. Add yourself to [AUTHORS.md](./docs/misc/authors.md)
7. Submit a pull request

## Changelog Guidelines

- Write full sentences describing changes
- No internal code references (e.g., "ENG_ideas")
- Jokes allowed if in good taste
- Document all significant changes

## AI Policy

### AI-Assisted Code

- AI-generated code is allowed with human review
- Must include personal stylization
- Cannot be pure generated content without review

### AI-Generated Art

- **Not allowed** under any circumstances
- All artwork must be human-created
- Exception: Reference images for artists (must be converted/stylized)

## Resources

- [Dev Resources](./docs/dev-resources/) - Tools and guides
- [Focus Tree Lifecycle](./docs/dev-resources/focus-tree-lifecycle-checklist.md)
- [Game Rules Reference](./docs/dev-resources/game-rules.md)

---

For questions, join the [Discord](http://discord.gg/millenniumdawn) or open an issue.
