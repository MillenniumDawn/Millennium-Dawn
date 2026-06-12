# Contributing to Millennium Dawn

Thank you for your interest in contributing to Millennium Dawn! This document covers everything you need to know, whether you are a first-time contributor or a returning team member.

## Quick Links

- [Documentation Site](https://millenniumdawn.github.io/Millennium-Dawn/)
- [Discord](http://discord.gg/millenniumdawn)
- [Git Setup & Usage Guide](#development-setup) — Cloning, branches, commits, PRs
- [Code Stylization Guide](https://millenniumdawn.github.io/Millennium-Dawn/dev-resources/code-stylization-guide/) — Formatting and code structure
- [Content Review Guide](https://millenniumdawn.github.io/Millennium-Dawn/dev-resources/content-review-guide/) — Quality checklist and developer expectations
- [Focus Tree Design Principles](https://millenniumdawn.github.io/Millennium-Dawn/dev-resources/focus-tree-design-principles/) — Branch structure, pacing, choices
- [Contributing Guide (website)](https://millenniumdawn.github.io/Millennium-Dawn/dev-resources/contributing/) — Web-friendly version of this file

## Types of Contributions

We welcome contributions in the following areas:

| Area                         | Examples                                                        |
| ---------------------------- | --------------------------------------------------------------- |
| **Focus Trees**              | New national focus trees, branch reworks, prerequisite fixes    |
| **Events & Decisions**       | New event chains, decision categories, triggered events         |
| **Ideas & National Spirits** | New ideas, modifier tuning, icon assignments                    |
| **AI & Balance**             | AI strategy plans, equipment variants, role ratios, stat tweaks |
| **Localisation**             | English string fixes, new loc keys, tooltip accuracy            |
| **Graphics**                 | Portraits, focus icons, event pictures, 3D models, map textures |
| **Map & History**            | State boundaries, province data, country history, OOBs          |
| **Documentation**            | Docs site content, guides, tutorials, dev diaries               |
| **Tooling**                  | Python scripts in `tools/`, CI improvements, pre-commit hooks   |
| **Bug Fixes**                | Crash fixes, trigger errors, scoping bugs, typos                |

If your contribution does not fit neatly into one of these categories, ask on Discord or open an issue first.

## Fork-Based Workflow

Outside contributors work from forks. Team members with write access may use branches directly on the main repo.

### For Outside Contributors

1. **Fork** the repository on GitHub.
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/<your-username>/Millennium-Dawn.git
   cd Millennium-Dawn
   ```
3. **Add the upstream remote** so you can stay current:
   ```bash
   git remote add upstream https://github.com/MillenniumDawn/Millennium-Dawn.git
   ```
4. **Create a feature branch** from `main`:
   ```bash
   git checkout -b my-feature main
   ```
5. **Make your changes**, following the style guidelines in this document.
6. **Commit** — pre-commit hooks run automatically and will flag issues.
7. **Push** your branch to your fork:
   ```bash
   git push origin my-feature
   ```
8. **Open a pull request** against `main` on the upstream repo.

### Staying Up to Date

Before starting new work, sync your fork with upstream:

```bash
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

### PR Expectations

- Keep PRs focused on a single feature or fix when possible.
- Update [Changelog.txt](./Changelog.txt) under the current top-most version heading (see [Changelog Guidelines](#changelog-guidelines)).
- Add yourself to [AUTHORS.md](./docs/src/content/misc/authors.md) if this is your first contribution.
- CI validation must pass and a team leader must approve before merge.
  - The CI validation may be bypassed by a team leader depending on their preferences and given the issues.

### What We Will Not Accept

- PRs that only reformat or restructure existing code without a functional reason.
- Machine-translated localisation (non-English languages are managed via Paratranz).
- Content that violates Paradox Interactive's Terms of Service.
- Large, unfocused PRs that touch many unrelated files. Break them up.

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

The Millennium Dawn team takes AI contributions seriously. AI tooling can improve productivity, but every contributor is responsible for the quality and integrity of what they submit. This section defines what is allowed, what is restricted, and what is prohibited.

### Guiding Principles

1. **Human ownership.** Every PR is the submitter's work product regardless of how it was produced. You own the quality, accuracy, and style compliance of everything you submit.
2. **Review before submission.** AI output is a draft, not a deliverable. All AI-assisted code, text, or localisation must be reviewed, tested, and brought into compliance with project standards before it enters a PR.
3. **Transparency.** If a substantial portion of a PR was generated or heavily shaped by AI, say so in the PR description. This is not a penalty — it helps reviewers know where to look harder.

### AI-Assisted Code (Scripts, Focus Trees, Events, Decisions, Ideas)

**Allowed** with conditions:

- You may use AI coding assistants (GitHub Copilot, Claude, ChatGPT, local models, etc.) to draft, refactor, or debug HOI4 script code.
- Several team members already integrate open-source and closed-source models into their workflow.

**Requirements:**

- All code must be personally reviewed line-by-line before submission to team review.
- All AI-generated code must adhere to team standards: correct indentation (tabs), naming conventions (`TAG_focus_name`), logging in effects, `ai_will_do` in focuses/decisions, `is_triggered_only = yes` in events.
- Run pre-commit to ensure contributions match the expected style. Do not submit raw AI output.
- Verify that AI-generated triggers, effects, and modifiers actually exist in the codebase or vanilla HOI4. AI models frequently hallucinate non-existent game objects.
- Test in-game when possible. AI cannot run the HOI4 engine; you can.

**Common AI mistakes to watch for:**

- Invented modifier names, scripted effects, or trigger keywords that do not exist
- Incorrect scoping (e.g., using `tag` where `original_tag` is required)
- Redundant `AND = { }` wrappers around implicit-AND trigger blocks
- `check_variable` with `>=` or `<=` (not valid inline syntax)
- Missing `province = XXXXX` on `add_building_construction` for `naval_base`
- `NOR = { ... }` used as a logical NOR (it scopes to Norway)

### AI-Assisted Localisation

**Allowed** with conditions:

- AI may be used to draft, proofread, or refine English localisation strings.
- The mod's non-English localisation is managed exclusively through Paratranz. Do not use AI to generate translations for other languages.

**Requirements:**

- All localisation must be reviewed by a human for accuracy, tone, and adherence to the [localisation rules](.claude/rules/localisation-rules.md).
- AI-generated localisation must not contain padding filler, em dashes, or excessive hedging.
- Every `[variable]` substitution in generated loc must correspond to a real scope getter or set variable.
- Grammar and subject-verb agreement must be correct. AI models commonly produce subtle agreement errors in complex sentences.

### AI-Generated Art and Graphics

**Prohibited** in most cases:

- Pure AI-generated art (illustrations, portraits, event pictures, loading screens) is **not allowed** under any circumstances.
- AI-generated side profiles of military vehicles are acceptable **only** when no existing side profile is available for that vehicle.
  - All graphics using this method must follow the mod's art standardization and be manually finalized by a human collaborator.
  - The final asset must be reviewed and approved by a GFX team member before submission.
- AI-upscaled images of existing assets are not considered "AI-generated" but still require human review for visual quality.

### AI-Generated Documentation and PR Descriptions

**Allowed** with conditions:

- You may use AI to draft documentation, README updates, or PR descriptions.
- Review the output for accuracy. AI-generated docs frequently reference files, tools, or workflows that do not exist in this repo.
- Do not add "Generated with" attributions, footers, or co-author trailers to PR descriptions or commit messages. The project does not use these.

### Enforcement

- PRs that contain unreviewed AI output (hallucinated game objects, broken syntax, style violations) will be returned for revision.
- Repeated submissions of raw AI output without review may result in loss of contributor trust and additional review requirements.
- Pure AI-generated art submissions will be rejected outright.

## Resources

- [Dev Resources](https://millenniumdawn.github.io/Millennium-Dawn/dev-resources/) — Tools and guides on the docs site
- [Focus Tree Lifecycle](https://millenniumdawn.github.io/Millennium-Dawn/dev-resources/focus-tree-lifecycle-checklist/) — End-to-end checklist
- [Game Rules Reference](https://millenniumdawn.github.io/Millennium-Dawn/player-tutorials/game-rules/) — Available game rules
- [AI-Assisted Modding Guide](https://millenniumdawn.github.io/Millennium-Dawn/dev-resources/ai-modding-guide/) — Setting up local AI models for development
- [tools/README.md](./tools/README.md) — Dev tools directory layout

---

For questions, join the [Discord](http://discord.gg/millenniumdawn) or open an issue.
