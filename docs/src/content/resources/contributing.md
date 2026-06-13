---
title: Contributing to Millennium Dawn
description: How to contribute to the mod — accepted contribution types, setup, workflow, and AI policy
---

This page is a quick reference for contributing to Millennium Dawn. For the complete guide, see the full [CONTRIBUTING.md](https://github.com/MillenniumDawn/Millennium-Dawn/blob/main/CONTRIBUTING.md) on GitHub.

> **Supporting Resources:**
>
> - [Code Stylization Guide](/dev-resources/code-stylization-guide/)
> - [Content Review Guide](/dev-resources/content-review-guide/)
> - [Focus Tree Lifecycle Checklist](/dev-resources/focus-tree-lifecycle-checklist/)
> - [AI-Assisted Modding Guide](/dev-resources/ai-modding-guide/)

---

## What We Accept

| Area                     | Examples                                            |
| ------------------------ | --------------------------------------------------- |
| Focus Trees              | New trees, branch reworks, prerequisite fixes       |
| Events & Decisions       | Event chains, decision categories, triggered events |
| Ideas & National Spirits | New ideas, modifier tuning, icon assignments        |
| AI & Balance             | Strategy plans, equipment variants, stat tweaks     |
| Localisation             | English string fixes, tooltip accuracy              |
| Graphics                 | Portraits, focus icons, event pictures, 3D models   |
| Map & History            | State boundaries, country history, OOBs             |
| Documentation            | Guides, tutorials, dev diaries                      |
| Tooling                  | Python scripts, CI improvements, pre-commit hooks   |
| Bug Fixes                | Crash fixes, trigger errors, typos                  |

Non-English localisation is managed through [Paratranz](https://paratranz.cn/projects/millennium-dawn) — do not submit translations directly.

## Fork Workflow (Outside Contributors)

1. **Fork** the repo on GitHub.
2. **Clone** your fork and add the upstream remote:
   ```bash
   git clone https://github.com/<your-username>/Millennium-Dawn.git
   cd Millennium-Dawn
   git remote add upstream https://github.com/MillenniumDawn/Millennium-Dawn.git
   ```
3. **Branch** from `main`:
   ```bash
   git checkout -b my-feature main
   ```
4. **Make changes**, following code standards.
5. **Commit** — pre-commit hooks run automatically.
6. **Push** and **open a PR** against `main` on the upstream repo.

Sync before starting new work:

```bash
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

## Setup

```bash
python3 tools/setup.py          # install hooks and dependencies
python3 tools/setup.py --check  # verify environment
```

See the full [CONTRIBUTING.md](https://github.com/MillenniumDawn/Millennium-Dawn/blob/main/CONTRIBUTING.md#development-setup) for VSCode workspace setup, docs site instructions, and dev tools.

## AI Policy Summary

AI tooling is welcome under the following rules. See the full [AI Policy](https://github.com/MillenniumDawn/Millennium-Dawn/blob/main/CONTRIBUTING.md#ai-policy) for details.

### Code and Scripts

AI coding assistants (Copilot, Claude, ChatGPT, local models) may be used to draft, refactor, or debug HOI4 script code. Requirements:

- Review all AI output line-by-line before submission.
- Enforce project standards (tabs, naming, logging, `ai_will_do`, `is_triggered_only`).
- Run pre-commit hooks. Do not submit raw AI output.
- Verify triggers, effects, and modifiers exist. AI models hallucinate non-existent game objects.

### Localisation

AI may draft or proofread English strings. All output requires human review for accuracy, tone, and style compliance. Non-English localisation is managed through Paratranz and must not be AI-generated.

### Graphics

- Pure AI-generated art is **not allowed** under any circumstances.
- AI-generated military vehicle side profiles are acceptable only when no existing profile is available, and the final asset must be manually finalized and reviewed by a GFX team member.

### Documentation and PR Descriptions

AI may draft documentation and PR descriptions. Review for accuracy — AI frequently references files or tools that do not exist in this repo. Do not add "Generated with" footers or co-author trailers.

---

For questions, join the [Discord](http://discord.gg/millenniumdawn) or open an issue on GitHub.
