# Contributing to Millennium Dawn

Thank you for your interest in contributing to Millennium Dawn!

## Quick Links

- [Documentation Site](https://millenniumdawn.github.io/Millennium-Dawn/)
- [Discord](http://discord.gg/millenniumdawn)
- [Git Setup & Usage Guide](https://millenniumdawn.github.io/Millennium-Dawn/player-tutorials/manual-install-instructions/) — Cloning, branches, commits, PRs
- [Code Stylization Guide](https://millenniumdawn.github.io/Millennium-Dawn/dev-resources/code-stylization-guide/) — Formatting and code structure
- [Content Review Guide](https://millenniumdawn.github.io/Millennium-Dawn/dev-resources/content-review-guide/) — Quality checklist and developer expectations
- [Focus Tree Design Principles](https://millenniumdawn.github.io/Millennium-Dawn/dev-resources/focus-tree-design-principles/) — Branch structure, pacing, choices

## Development Setup

### Prerequisites

- **Python 3.10+** (3.12+ recommended to match CI)
- **Git** with a GUI client ([GitKraken](https://www.gitkraken.com/) recommended, or [GitHub Desktop](https://desktop.github.com/))
- **Text editor** — [Visual Studio Code](https://code.visualstudio.com/) recommended (see workspace instructions below)

### One-Command Setup

After cloning the repo, run the setup script. It installs pre-commit hooks and Python tool dependencies:

```bash
python3 tools/setup.py
```

That's it. Pre-commit hooks will now run automatically on every commit, catching style issues, encoding problems, and common mistakes before they reach CI.

To verify your environment at any time:

```bash
python3 tools/setup.py --check
```

### Docs Site Setup (Optional)

If you are editing the documentation site (under `docs/`), add the `--docs` flag. This requires [Node.js 24 LTS](https://nodejs.org/) and [Bun](https://bun.sh/):

```bash
python3 tools/setup.py --docs
```

To preview the docs site locally:

```bash
cd docs
bun run dev    # opens at http://localhost:4321/
```

Before opening a docs PR, run the full check suite:

```bash
cd docs
bun run ci
```

### VSCode Workspace (Recommended)

The repo includes a pre-configured VSCode workspace with Paradox syntax highlighting, trailing whitespace cleanup, and other useful extensions:

1. Open VSCode.
2. Go to **File** > **Open Workspace**.
3. Select `.vscode/hoi4_millennium_dawn.code-workspace`.
4. Accept the popup to install recommended extensions.

### Dev Tools

All development scripts live in `tools/` and can be run by short name:

```bash
python3 tools/run.py --list                           # see all tools
python3 tools/run.py estimate_gdp USA                 # run by name
python3 tools/run.py find_idea common/ideas/Greek.txt # partial match works
```

See [tools/README.md](./tools/README.md) for the full directory layout and descriptions.

### Pre-commit Hooks

Hooks run automatically on every commit. You can also run them manually:

```bash
pre-commit run --all-files       # run all hooks on every file
pre-commit run check-braces      # run a specific hook
pre-commit autoupdate            # update hook versions
```

## Code Standards

### Localisation (.yml)

- 1-space indentation
- UTF-8 with BOM encoding
- Remove trailing version numbers after colons (`key: "value"`, not `key:0 "value"`)

### Script Files (.txt)

- Tab indentation (not spaces)
- Include logging in all effects
- Follow naming conventions: `TAG_focus_name_here`
- Use `is_triggered_only = yes` for events
- Include `ai_will_do` in all focuses and decisions
- Remove redundant code (`allowed = { always = no }`, empty trigger blocks)

See the [Code Stylization Guide](https://millenniumdawn.github.io/Millennium-Dawn/dev-resources/code-stylization-guide/) for the complete reference.

### Docs Content (`docs/`)

- Built with Astro 6 — content lives in `docs/src/content/**`
- Use Markdown and frontmatter only (no Liquid tags)
- Internal links must be root-relative: `[Tutorial](/tutorials/)`
- Do not hardcode `"/Millennium-Dawn/..."` — base path is applied during build
- Image links follow the same pattern: `![Alt](/assets/images/example.png)`

## Pull Request Process

1. Create a feature branch from `main`
2. Run `python3 tools/setup.py --check` to verify your environment
3. Make your changes following the style guidelines above
4. Commit — pre-commit hooks run automatically and will flag issues
5. Update [Changelog.txt](./Changelog.txt) with your changes (see format below)
6. Add yourself to [AUTHORS.md](./docs/src/content/misc/authors.md) if this is your first contribution
7. Push your branch and open a pull request on GitHub
8. CI validation must pass and a team leader must approve before merge

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
