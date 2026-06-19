---
title: Developer Setup & Workflow
description: The main developer guide for Millennium Dawn. Get your environment ready, learn the workflow, and ship your first PR.
---

This is the main developer guide for contributing to Millennium Dawn. It covers everything you need to start: prerequisites, cloning, tooling, pre-commit hooks, the day-to-day workflow, and where to find the rest of the team docs.

> **For docs site work specifically**, see the [Contributing Guide](/dev-resources/contributing/) which covers `bun run dev`, content conventions, and the docs CI pipeline.
>
> **For repo-root context**, see [`CONTRIBUTING.md`](https://github.com/MillenniumDawn/Millennium-Dawn/blob/main/CONTRIBUTING.md), a slim pointer to the right docs.

---

# Prerequisites

| Tool            | Version                   | Purpose                              |
| --------------- | ------------------------- | ------------------------------------ |
| **Git**         | Any recent version        | Version control                      |
| **Python**      | 3.10+ (3.12+ recommended) | Dev tools, validators, standardizers |
| **Text editor** | VS Code recommended       | Editing script files                 |
| **HOI4**        | Latest                    | Testing changes in-game              |

Optional but useful:

| Tool                                | Purpose                                                                                |
| ----------------------------------- | -------------------------------------------------------------------------------------- |
| **Node.js 24 LTS** + **Bun**        | Docs site development only (see the [Contributing Guide](/dev-resources/contributing/) |
| **GitKraken** or **GitHub Desktop** | Git GUI (pick one)                                                                     |
| **Claude Code**                     | AI-assisted development (see [AI Modding Guide](/dev-resources/ai-modding-guide/)      |

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

4. Create a feature branch from `main`:

   ```bash
   git checkout -b my-feature main
   ```

See [Git Workflow](/dev-resources/git-workflow/) for the full fork-based workflow.

## Staying Up to Date

Before starting new work, sync your fork or branch with upstream:

```bash
git fetch upstream
git checkout main
git merge upstream/main
```

Or rebase if you prefer a cleaner history:

```bash
git checkout my-feature
git rebase main
```

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
python3 tools/dev_setup.py
```

That's it. Pre-commit hooks will now run automatically on every commit.

To verify your environment at any time:

```bash
python3 tools/dev_setup.py --check
```

For docs site work, also install the Node and Bun dependencies (see the [Contributing Guide](/dev-resources/contributing/):

```bash
python3 tools/dev_setup.py --docs
```

---

# Pre-commit Hooks

Hooks run automatically on every `git commit`. They catch:

- **Style issues**: trailing whitespace, mixed line endings, encoding problems.
- **Script errors**: mismatched braces, invalid localisation encoding, common HOI4 scripting mistakes.
- **Standardization**: auto-reformats focuses, events, decisions, and ideas to MD conventions.

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
├── docs_checks/       Docs-site checks (link syntax, a11y, perf, etc.) + check_docs.py runner
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
├── precommit_validate.py Pre-commit hook: runs commit-stage validators in parallel
├── validate_staged.py Legacy staged-file router (no longer wired into pre-commit)
└── standardize_staged.py Pre-commit hook: routes staged files to standardizers
```

Python dependencies live in `pyproject.toml` under `[dependency-groups]` (a `runtime` group and a `dev` group); there are no `requirements.txt` files. `tools/dev_setup.py` installs them, and `pyproject.toml` also configures ruff (lint, import order, and formatting) and pytest.

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

- Two extensions for Paradox syntax (highlighting, snippets, problem scanning).
- Trailing whitespace cleanup on save.
- Markdown support, line sorting, CODEOWNERS, editorconfig.
- Workspace folders for better hierarchy in search results.

---

# Code Standards

A summary. The full reference is the [Code Stylization Guide](/dev-resources/code-stylization-guide/), but the rules below are the most common ones to get right.

### Localisation (.yml)

- 1-space indentation.
- UTF-8 with BOM encoding.
- Remove trailing version numbers after colons (`key: "value"`, not `key:0 "value"`).

### Script Files (.txt)

- Tab indentation (not spaces).
- Include logging in all effects.
- Follow naming conventions: `TAG_focus_name_here`.
- Use `is_triggered_only = yes` for events.
- Include `ai_will_do` in all focuses and decisions.
- Remove redundant code (`allowed = { always = no }`, empty trigger blocks).

### Docs Content (`docs/`)

If you are editing the docs site, see the [Contributing Guide](/dev-resources/contributing/) for the docs-specific rules. The high-level point: frontmatter is required, internal links must be root-relative, and do not hardcode `"/Millennium-Dawn/..."` (the base path is applied during build).

---

# Day-to-Day Workflow

1. **Pull latest** from `main` (or your feature branch).
2. **Create a branch** for your work: `git checkout -b my-feature`.
3. **Make changes**: edit files, test in-game.
4. **Commit**: pre-commit hooks run automatically and flag issues.
5. **Push** your branch: `git push origin my-feature`.
6. **Open a PR** against `main` on GitHub.
7. **CI validates** your PR automatically. Fix any issues flagged.
8. **Team leader reviews** and merges.

## Branch Naming

Use descriptive branch names:

- `ser-focus-tree`: new Serbian focus tree.
- `fix-election-event-bug`: bug fix.
- `ai-strategy-updates`: AI behavior changes.
- `docs-developer-guide`: documentation work.

---

# Related Resources

- [Contributing Guide](/dev-resources/contributing/): docs site workflow, `bun run dev`, content conventions.
- [Git Workflow](/dev-resources/git-workflow/): detailed branch/commit/PR process.
- [Code Stylization Guide](/dev-resources/code-stylization-guide/): formatting and code structure.
- [AI Modding Guide](/dev-resources/ai-modding-guide/): AI tools for development.
- [Content Review Guide](/dev-resources/content-review-guide/): quality checklist.
- [tools/README.md](https://github.com/MillenniumDawn/Millennium-Dawn/blob/main/tools/README.md): dev tools directory layout.
