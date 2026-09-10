---
title: Developer Setup & Workflow
description: The main developer guide for Millennium Dawn. Get your environment ready, learn the workflow, and ship your first PR.
---

Clone the mod, connect it to the launcher, install the tools, then work on a feature
branch. If you only want to play, use [Getting Started](/getting-started/) instead.

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
| **HOI4**        | Match mod descriptor      | Testing changes in-game              |

Optional but useful:

| Tool                         | Purpose                                                                                 |
| ---------------------------- | --------------------------------------------------------------------------------------- |
| **Node.js 24 LTS** + **Bun** | Docs site development only (see the [Contributing Guide](/dev-resources/contributing/)) |
| **GitHub Desktop**           | Git GUI (recommended)                                                                   |
| **Claude Code**              | AI-assisted development (see [AI Modding Guide](/dev-resources/ai-modding-guide/))      |

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

The checked-in `Millennium_Dawn.mod` uses `path="mod/Millennium-Dawn"`. For that
path to work, clone the repository into a folder named `Millennium-Dawn` directly
inside your HOI4 mod directory:

| OS      | Default mod directory                                                  |
| ------- | ---------------------------------------------------------------------- |
| Windows | `C:\Users\<name>\Documents\Paradox Interactive\Hearts of Iron IV\mod\` |
| macOS   | `~/Documents/Paradox Interactive/Hearts of Iron IV/mod/`               |
| Linux   | `~/.local/share/Paradox Interactive/Hearts of Iron IV/mod/`            |

1. Copy `Millennium_Dawn.mod` from the checkout into the parent `mod/` directory.
   If your checkout is elsewhere, change `path` in this local copy to the checkout's
   absolute path using forward slashes. Do not commit your machine-specific path.
2. Match HOI4 to `supported_version` in the checkout's descriptor, not automatically
   the latest game patch.
3. In the launcher, use **Playsets** → **Add More Mods** and enable
   **Millennium Dawn: Developer Version**. Disable Workshop copies and submods in this playset.
4. Start a new game to verify the checkout loads.

Development updates may invalidate saves. Keep separate test saves and do not rely
on a development checkout for a long-running campaign.

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
- **Standardization**: reports changed files that need formatting. The bulk auto-standardizer
  is disabled; use the command in the finding on the affected file.

## Running Manually

```bash
# Run all hooks on specific files
pre-commit run --files common/national_focus/05_SER_focus.txt

# Run a specific hook
pre-commit run md-validate-content

# Update hook versions
pre-commit autoupdate
```

> **Important**: Never run `pre-commit run --all-files`. It rewrites every matching file in the repo and creates hundreds of unrelated changes. Always scope to your modified files.

## What Runs Where

| Hook                          | Pre-commit | CI (PR) | Notes                                |
| ----------------------------- | ---------- | ------- | ------------------------------------ |
| `md-validate-content`         | Yes        | Yes     | Fast subset; CI runs all batches     |
| `md-validate-defines`         | Yes        | Yes     | CI uses `vanilla_defines.txt`        |
| `md-validate-descriptors`     | Yes        | Yes     | Also runs in the core batch job      |
| `fix-localization-encoding`   | Yes        | No      | Fixer; CI checks BOM without fixing  |
| `fix-loc-yaml`                | Yes        | No      | Pre-commit only                      |
| `md-fix-styling`              | Manual     | No      | CI checks style in batches           |
| `md-validate-unused-textures` | Manual     | No      | CI cannot run it                     |
| `tools-pytest`                | Pre-push   | Yes     | CI Tools tests job when tools change |

The CI (PR) column is the Test Suite (`test-suite.yml`). The full pre-commit vs
CI map, including per-validator strictness, lives in
`.claude/docs/validation-pipeline.md`.

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

Python dependencies live in `pyproject.toml` under `[dependency-groups]` (a `runtime` group and a `dev` group); there are no `requirements.txt` files. `tools/dev_setup.py` installs them, and `pyproject.toml` configures Ruff for lint/import order, Black for formatting, and pytest for tests.

See [tools/README.md](https://github.com/MillenniumDawn/Millennium-Dawn/blob/main/tools/README.md) for the full documentation.

## Changing Tools

Follow [Maintaining Tools](https://github.com/MillenniumDawn/Millennium-Dawn/blob/main/tools/README.md#maintaining-tools)
for text writes, shared helpers, and regression tests. The same README owns the
[validator recipe](https://github.com/MillenniumDawn/Millennium-Dawn/blob/main/tools/README.md#writing-a-new-validator).
Run `python -m pytest` for `tools/` changes and fix regressions before merge.

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

Keep changes small and easy for another human to maintain. Reuse existing code and
queryable state before adding helpers, flags, or configuration. Prefer clear local
logic over clever abstractions. The [Code Stylization Guide](/dev-resources/code-stylization-guide/)
owns the detailed conventions.

### Localisation (.yml)

- Edit English only. Other languages are not currently mirrored and may differ.
- 1-space indentation.
- UTF-8 with BOM encoding.
- Remove trailing version numbers after colons (`key: "value"`, not `key:0 "value"`).

### Script Files (.txt)

- Tab indentation (not spaces).
- Follow the focus, decision, and event logging rules. Dismiss-only event options need no log.
- Follow naming conventions: `TAG_focus_name_here`.
- Use `is_triggered_only = yes` for events.
- Include `ai_will_do` in all focuses and decisions.
- Remove redundant code (empty trigger blocks). Keep `allowed = { always = no }` on slotted ideas that must not appear in the picker.

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

## PR Descriptions and Handoffs

Use BLUF (Bottom Line Up Front): state the result first, then the supporting facts.
PR descriptions start with `## Bottom line`. Explain why when it is not obvious;
include changed behavior and any limits, not a file-by-file narration. Keep reviews
to findings with paths, impact, and a suggested fix. Say what was not verified.

Do not add AI attribution trailers or tool-generated footers. Add `Changelog.txt`
entries only when requested.

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
