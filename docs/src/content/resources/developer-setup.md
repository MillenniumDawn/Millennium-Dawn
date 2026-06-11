---
title: Developer Setup & Workflow
description: Get your environment ready for Millennium Dawn mod development
---

This guide covers everything you need to start contributing: prerequisites, cloning, tooling, pre-commit hooks, and the day-to-day development workflow.

> **New contributors**: Start with the [Contributing Guide](/dev-resources/contributing/) for an overview of what we accept and how to submit changes.

---

# Prerequisites

| Tool            | Version                   | Purpose                              |
| --------------- | ------------------------- | ------------------------------------ |
| **Git**         | Any recent version        | Version control                      |
| **Python**      | 3.10+ (3.12+ recommended) | Dev tools, validators, standardizers |
| **Text editor** | VS Code recommended       | Editing script files                 |
| **HOI4**        | Latest                    | Testing changes in-game              |

Optional but useful:

| Tool                                | Purpose                                                                            |
| ----------------------------------- | ---------------------------------------------------------------------------------- |
| **Node.js 24 LTS** + **Bun**        | Docs site development only                                                         |
| **GitKraken** or **GitHub Desktop** | Git GUI (pick one)                                                                 |
| **Claude Code**                     | AI-assisted development (see [AI Modding Guide](/dev-resources/ai-modding-guide/)) |

---

# Cloning the Repository

## Team Members (Write Access)

```bash
git clone https://github.com/MillenniumDawn/Millennium-Dawn.git
cd Millennium-Dawn
```

## Outside Contributors (Fork)

1. Fork the repository on GitHub.
2. Clone your fork:
   ```bash
   git clone https://github.com/<your-username>/Millennium-Dawn.git
   cd Millennium-Dawn
   ```
3. Add the upstream remote:
   ```bash
   git remote add upstream https://github.com/MillenniumDawn/Millennium-Dawn.git
   ```

See [Git Workflow](/dev-resources/git-workflow/) for the full fork-based workflow.

## Setting Up the Mod for Testing

After cloning, the mod folder must be in the correct location for HOI4 to detect it:

| OS      | Default mod directory                                                  |
| ------- | ---------------------------------------------------------------------- |
| Windows | `C:\Users\<name>\Documents\Paradox Interactive\Hearts of Iron IV\mod\` |
| macOS   | `~/Documents/Paradox Interactive/Hearts of Iron IV/mod/`               |
| Linux   | `~/.local/share/Paradox Interactive/Hearts of Iron IV/mod/`            |

1. Copy the `Millennium_Dawn.mod` file from the cloned repo into the `mod/` directory.
2. In the HOI4 launcher, go to **Playsets** → **Add More Mods** → enable **Millennium Dawn Dev**.
3. Launch the game to verify it works.

---

# One-Command Setup

The setup script installs pre-commit hooks and Python tool dependencies:

```bash
python3 tools/setup.py
```

That's it. Pre-commit hooks will now run automatically on every commit.

To verify your environment at any time:

```bash
python3 tools/setup.py --check
```

---

# Pre-commit Hooks

Hooks run automatically on every `git commit`. They catch:

- **Style issues** — trailing whitespace, mixed line endings, encoding problems
- **Script errors** — mismatched braces, invalid localisation encoding, common HOI4 scripting mistakes
- **Standardization** — auto-reformats focuses, events, decisions, and ideas to MD conventions

## Running Manually

```bash
# Run all hooks on specific files
pre-commit run --files common/national_focus/05_SER_focus.txt

# Run a specific hook
pre-commit run check-braces

# Update hook versions
pre-commit autoupdate
```

> **Important**: Never run `pre-commit run --all-files`. It rewrites every matching file in the repo and creates hundreds of unrelated changes. Always scope to your modified files.

## What Runs Where

| Hook                             | Pre-commit      | CI (PR)             | Notes                                                     |
| -------------------------------- | --------------- | ------------------- | --------------------------------------------------------- |
| `check-braces`                   | Yes             | No                  | Pre-commit only                                           |
| `fix-loc-yaml`                   | Yes             | No                  | Pre-commit only                                           |
| `validate-localization-encoding` | Yes             | No                  | Pre-commit only                                           |
| `coding-standards`               | Manual          | Yes                 | Runs on PR, not on commit                                 |
| `check-basic-style`              | Manual          | Yes                 | Runs on PR, not on commit                                 |
| `check-common-mistakes`          | Manual          | Yes                 | Runs on PR, not on commit                                 |
| `validate-ai-equipment`          | Yes (no strict) | Yes (strict)        | Strict mode on CI blocks coverage gaps                    |
| `validate-ideas`                 | Yes (strict)    | Yes (informational) | CI is informational until pre-existing issues are cleared |
| `validate-defines`               | Yes             | Skipped             | Needs vanilla file not in CI runner                       |

---

# Dev Tools

All development scripts live in `tools/` and can be run by short name:

```bash
python3 tools/run.py --list                           # see all tools
python3 tools/run.py estimate_gdp USA                 # run by name
python3 tools/run.py find_idea common/ideas/Greek.txt # partial match works
python3 tools/run.py publish_workshop release --full  # pass args through
```

## Tool Directory Layout

```
tools/
├── analysis/          Analysis, reference finders, metrics
├── assets/            DDS conversion, GFX generation, texture tools
├── generators/        Content generators (tribute ideas, focus names)
├── linting/           Style checkers, formatters, encoding validators
├── publishing/        Steam Workshop publishing
├── report_lib/        PR validation report renderer + GitHub Checks API
├── standardization/   Auto-standardizers for focuses, events, decisions, ideas
├── tests/             Test suites for validators
├── validation/        Content validators (events, decisions, variables, etc.)
├── shared_utils.py    Shared utilities (Colors, FileOpener, path helpers)
├── loc.py             Localisation utilities
├── logging_tool.py    Logging utility
├── validate_staged.py Pre-commit hook: routes staged files to validators
└── standardize_staged.py Pre-commit hook: routes staged files to standardizers
```

See [tools/README.md](https://github.com/MillenniumDawn/Millennium-Dawn/blob/main/tools/README.md) for the full documentation.

## Writing a New Validator

1. Create `tools/validation/validate_<topic>.py`.
2. Subclass `BaseValidator` from `tools/validation/validator_common.py`.
3. Use `add_error(category, msg, file, line)` for structured issues.
4. Add a pre-commit hook entry in `.pre-commit-config.yaml`.
5. Add a CI entry in `.github/workflows/coding-pipeline.yml`.

---

# VS Code Workspace

The repo includes a pre-configured workspace with Paradox syntax highlighting, trailing whitespace cleanup, and other useful extensions:

1. Open VS Code.
2. Go to **File** → **Open Workspace**.
3. Select `.vscode/hoi4_millennium_dawn.code-workspace`.
4. Accept the popup to install recommended extensions.

**What's configured:**

- Two extensions for Paradox syntax (highlighting, snippets, problem scanning)
- Trailing whitespace cleanup on save
- Markdown support, line sorting, CODEOWNERS, editorconfig
- Workspace folders for better hierarchy in search results

---

# Docs Site Setup

The documentation site lives under `docs/` and is built with [Astro](https://astro.build/).

## Setup

```bash
python3 tools/setup.py --docs    # installs Node.js + Bun dependencies
```

Requires [Node.js 24 LTS](https://nodejs.org/) and [Bun](https://bun.sh/).

## Local Preview

```bash
cd docs
bun run dev    # opens at http://localhost:4321/
```

## Before Opening a Docs PR

```bash
cd docs
bun run ci     # runs full check suite (lint, typecheck, build)
```

## Content Structure

| Path                           | Content                                |
| ------------------------------ | -------------------------------------- |
| `docs/src/content/pages/`      | Top-level pages (FAQ, Getting Started) |
| `docs/src/content/resources/`  | Developer resource guides              |
| `docs/src/content/tutorials/`  | Player and developer tutorials         |
| `docs/src/content/countries/`  | Country-specific documentation         |
| `docs/src/content/navigation/` | Site navigation and footer             |

Content uses Markdown with frontmatter. Internal links must be root-relative (`/dev-resources/guide-name/`). Do not hardcode the base path.

---

# Day-to-Day Workflow

1. **Pull latest** from `main` (or your feature branch).
2. **Create a branch** for your work: `git checkout -b my-feature`.
3. **Make changes** — edit files, test in-game.
4. **Commit** — pre-commit hooks run automatically and flag issues.
5. **Push** your branch: `git push origin my-feature`.
6. **Open a PR** against `main` on GitHub.
7. **CI validates** your PR automatically. Fix any issues flagged.
8. **Team leader reviews** and merges.

## Branch Naming

Use descriptive branch names:

- `ser-focus-tree` — new Serbian focus tree
- `fix-election-event-bug` — bug fix
- `ai-strategy-updates` — AI behavior changes
- `docs-developer-guide` — documentation work

## Staying Up to Date

Sync your branch with `main` regularly to avoid merge conflicts:

```bash
git fetch upstream
git checkout main
git merge upstream/main
git checkout my-feature
git merge main
```

Or rebase if you prefer a cleaner history:

```bash
git checkout my-feature
git rebase main
```

---

# Related Resources

- [Contributing Guide](/dev-resources/contributing/) — What we accept, fork workflow, AI policy
- [Git Workflow](/dev-resources/git-workflow/) — Detailed branch/commit/PR process
- [Code Stylization Guide](/dev-resources/code-stylization-guide/) — Formatting and code structure
- [AI Modding Guide](/dev-resources/ai-modding-guide/) — AI tools for development
- [Content Review Guide](/dev-resources/content-review-guide/) — Quality checklist
