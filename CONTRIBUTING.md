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

### Docs Content Rules (`docs/`)

- Docs are now built with Astro 5+ and content lives in `docs/src/content/**`.
- Use Markdown/frontmatter only. Do not add Liquid tags (`{% ... %}` or `{{ ... }}`).
- Internal links should be root-relative, for example: `[Tutorial](/tutorials/)`.
- Do not hardcode `"/Millennium-Dawn/..."` in markdown links. Base path is applied during build.
- Apply the same pattern to image links: `![Alt](/assets/images/example.png)`.
- For country pages, keep metadata in frontmatter and write section content in markdown body.

### Docs Local Checks

[Install Bun](https://bun.com/) first (one-time setup on your computer).

If you only want to edit docs content (and are not a developer), follow these steps:

1. Open a terminal in this repository.
2. Go to the docs folder:

```bash
cd docs
```

3. First time only, install required packages:

```bash
bun install
```

4. Start the local docs website:

```bash
bun run dev
```

5. Open the local URL shown in the terminal (usually `http://localhost:4321/`).
6. Edit content files in `docs/src/content/`, save, and refresh the browser.

Before opening a PR, run these checks from the same `docs` folder:

```bash
bun run lint:md     # checks markdown formatting
bun run build       # builds the production site
bun run check:links # checks broken links
```

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

The Millennium Dawn team takes AI contributions or usage very seriously. We understand that AI can be helpful and improve the productivity of modding, but it is your responsibility to use it appropriately.
We do not under any permissions allow any ML/AI generated assets for graphics if AI is the sole contributor.

### AI-Assisted Code

AI-assisted code is permitted assuming you are using it responsibly. Several team members already integrate open source models, closed source models and otherwise into their workflow.

_Rules_

- All code must be personally reviewed before submitted to team review
- All AI code must adhere to team standards and be properly vetted
- Use pre-commit to ensure the contributions match the expected style

### AI-Assisted Localization

- AI-generated localization is allowed with human review but must maintain accuracy, styling and must still be originally created by a human

### AI-Generated Art

- Pure AI Generated Art is **not allowed** under any circumstances
- AI-Generated side profiles of military vehicles can be acceptable if there is no side profile available for graphics
  - All graphics using this method MUST follow standardization and be hand done by a human collaborator

## Resources

- [Dev Resources](./docs/dev-resources/) - Tools and guides
- [Focus Tree Lifecycle](./docs/dev-resources/focus-tree-lifecycle-checklist.md)
- [Game Rules Reference](./docs/dev-resources/game-rules.md)

---

For questions, join the [Discord](http://discord.gg/millenniumdawn) or open an issue.
