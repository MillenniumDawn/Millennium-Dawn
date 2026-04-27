---
title: Claude Code Skills
description: AI-assisted development tools built into the Millennium Dawn repository
---

The Millennium Dawn repository includes a set of Claude Code skills — slash commands that automate common development tasks. They are available to anyone using [Claude Code](https://claude.ai/code) with the repository open.

> **Setup**: Claude Code reads `.claude/` automatically when you open the repo. No additional configuration is needed.

---

## Quick Reference

| Skill                         | What it does                                                                     |
| ----------------------------- | -------------------------------------------------------------------------------- |
| `/validate`                   | Run all validation tools against changed or staged files                         |
| `/standardize <file>`         | Auto-reformat a focus, event, decision, or idea file to MD conventions           |
| `/new-focus <TAG>`            | Scaffold a new focus tree file with stubs and localisation keys                  |
| `/add-leader <TAG>`           | Scaffold generals, field marshals, and admirals using the correct count formulas |
| `/lifecycle-check <TAG>`      | Audit a branch against the focus tree lifecycle checklist                        |
| `/search-filter-check <file>` | Validate `search_filters` on every focus against the approved filter list        |
| `/content-review <file>`      | Full content quality checklist (economic, political, visual, military, AI)       |
| `/review-branch`              | Quick standards review of the entire branch diff                                 |
| `/audit <file>`               | Deep multi-agent audit: simplification + performance + content                   |
| `/fix-issue <number>`         | Find and fix a GitHub issue, then open a PR                                      |
| `/changelog`                  | Summarize branch changes and update `Changelog.txt`                              |

---

## How the Review Skills Relate

There are three review skills with different scopes:

**`/review-branch`** — fast, inline, single-pass. Covers coding standards, performance patterns, logic correctness, localisation, and quick content design checks. Best for PR review gating. Runs in one pass without sub-agents.

**`/content-review`** — focused on design quality. Checks the full developer content review guide: economic balance, political guidelines, visual standards, military counts, AI rules, and miscellaneous checklist items. Best when a developer thinks their content is submission-ready.

**`/audit`** — deep, multi-agent. Spawns three parallel agents (simplification, performance, content review) and merges their findings. Can also apply fixes. Best for a pre-merge cleanup sprint or a thorough file-level analysis.

These are additive tiers, not alternatives — running all three gives the most complete picture.

---

## Lifecycle Skills

For developers building new country content, the recommended flow is:

1. `/new-focus <TAG>` — scaffold the focus tree file
2. `/add-leader <TAG>` — scaffold generals and admirals once OOB is drafted
3. `/search-filter-check <file>` — validate search filters before submitting
4. `/lifecycle-check <TAG>` — audit which lifecycle items are done
5. `/content-review` — full design quality pass
6. `/review-branch` — coding standards pass
7. `/validate` — run automated validation tools
8. `/changelog` — update the changelog

---

## Validation and Standardization

**`/validate [staged] [strict]`** runs the Python validation tools in `tools/`. The `staged` flag limits checks to staged files; `strict` fails on any error (useful in CI).

**`/standardize <file>`** runs `tools/standardization/standardize.py` against a specific file and reports what was reformatted. This handles property ordering, logging insertion, and removal of empty blocks automatically.

---

## Under the Hood

Skills are Markdown files in `.claude/skills/<name>/SKILL.md`. Each file contains instructions that Claude Code follows when the skill is invoked. Reference docs used by the skills live in `.claude/docs/`.

To update a skill's behavior, edit the relevant `.SKILL.md` file. To add a new skill, create a directory under `.claude/skills/` with a `SKILL.md` inside.

---

## Related Resources

- [Focus Tree Lifecycle Checklist](/dev-resources/focus-tree-lifecycle-checklist)
- [Content Review Guide](/dev-resources/content-review-guide)
- [New General Guidelines](/dev-resources/new-general-guidelines)
- [Code Stylization Guide](/dev-resources/code-stylization-guide)
