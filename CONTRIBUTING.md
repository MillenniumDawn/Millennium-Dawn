# Contributing to Millennium Dawn

Thank you for your interest in contributing to Millennium Dawn!

## Quick Links

- [Documentation](https://millenniumdawn.github.io/Millennium-Dawn/)
- [Discord](http://discord.gg/millenniumdawn)
- [Code Stylization Guide](./docs/src/content/resources/code-stylization-guide.md)
- [Code Resources](./docs/src/content/resources/code-resource.md)

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

- Docs are built with Astro 6 and content lives in `docs/src/content/**`.
- Use Markdown/frontmatter only. Do not add Liquid tags (`{% ... %}` or `{{ ... }}`).
- Internal links should be root-relative, for example: `[Tutorial](/tutorials/)`.
- Do not hardcode `"/Millennium-Dawn/..."` in markdown links. Base path is applied during build.
- Apply the same pattern to image links: `![Alt](/assets/images/example.png)`.
- For country pages, keep metadata in frontmatter and write section content in markdown body.

### Docs Local Checks

**Prerequisites:**
- [Node.js 24 LTS](https://nodejs.org/) or newer (required by Astro 6)
- [Bun](https://bun.com/) (package manager and script runner)

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
bun run ci
```

Or run individual checks: `lint:md`, `lint:remark`, `check`, `build`, `check:links`, `check:og`, `check:a11y`, `check:perf`. Full checks also require Python 3 for some validation scripts.

See [Code Stylization Guide](./docs/src/content/resources/code-stylization-guide.md) for details.

## Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make changes following style guidelines
4. Run pre-commit hooks
5. Update [Changelog.txt](./Changelog.txt)
6. Add yourself to [AUTHORS.md](./docs/src/content/misc/authors.md)
7. Submit a pull request

## Changelog Guidelines

All PRs must update [Changelog.txt](./Changelog.txt) under the current top-most version heading.

### Formatting

- **Version heading**: standalone line (e.g., `v2.0.0`), blank line after
- **Category header**: 1 space + category name + colon (e.g., ` Bugfix:`)
- **Entry**: 2 spaces + `- ` + text (e.g., `  - Fixed something`)
- **Sub-entry**: 4 spaces + `- ` + text (e.g., `    - Detail about the fix`)
- **Continuation text**: 6 spaces to align with the parent entry's text
- Blank line between categories

### Categories

Use only these categories (skip any that have no entries):

| Category        | Use for                                                                      |
| --------------- | ---------------------------------------------------------------------------- |
| Achievements    | New or changed achievements                                                  |
| AI              | AI behavior, strategy, or decision-making changes                            |
| Balance         | Stat tweaks, modifier adjustments, cost/value changes                        |
| Bugfix          | Bug fixes, crash fixes, typo corrections                                     |
| Content         | New focus trees, events, decisions, ideas, MIOs, or significant new gameplay |
| Database        | Country history, OOBs, state data, technology assignments                    |
| Documentation   | Docs, guides, modding resources                                              |
| Factions        | Faction mechanics, membership, leadership changes                            |
| Game Rules      | New or modified game rules                                                   |
| Graphics        | GFX, icons, portraits, sprites, 3D models                                    |
| Localization    | Localisation strings, translations, formatting                               |
| Map             | Map changes, state boundaries, provinces, map modes                          |
| Music           | New or changed music tracks, sound triggers                                  |
| Performance     | Optimizations, removed redundant triggers, on_action improvements            |
| Quality of Life | QoL improvements, UI polish, tooltips                                        |
| Sound           | Sound effects and audio changes                                              |
| Technology      | Tech tree changes, research categories                                       |
| User Interface  | UI layout, scripted GUIs, interface definitions                              |

### Writing Style

- Use past tense ("Added", "Fixed", "Reduced", "Reworked")
- Write full sentences describing the change — no internal code references (e.g., write "Fixed Serbian election focus prerequisite", not "Fixed SER_elections prereq")
- Be specific: name the focus, event, decision, or mechanic affected
- Prefix country-specific entries with `[TAG]` (e.g., `  - [SER] Fixed focus prerequisite for Serbian elections`)
- No tag prefix for global or system-wide changes
- One bullet per distinct change; group related micro-changes as sub-entries under a parent
- Reference issue numbers when applicable (e.g., `(Issue #330)`)
- Jokes allowed if in good taste
- Use spaces only — no tab characters

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

- [Dev Resources](./docs/src/content/resources/) - Tools and guides
- [Focus Tree Lifecycle](./docs/src/content/resources/focus-tree-lifecycle-checklist.md)
- [Game Rules Reference](./docs/src/content/tutorials/game-rules.md)

---

For questions, join the [Discord](http://discord.gg/millenniumdawn) or open an issue.
