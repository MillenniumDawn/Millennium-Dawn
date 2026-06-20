# Contributing to Millennium Dawn

Thank you for your interest in contributing to Millennium Dawn! This file is a pointer to the team docs. The full guides live on the [documentation site](https://millenniumdawn.github.io/Millennium-Dawn/).

## Quick Links

| Guide                                                                                                                        | What it covers                                                                                    |
| ---------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| [Developer Setup Guide](https://millenniumdawn.github.io/Millennium-Dawn/dev-resources/developer-setup/)                     | Prerequisites, cloning, pre-commit hooks, dev tools, VSCode, day-to-day workflow. **Start here.** |
| [Contributing Guide (Docs Site)](https://millenniumdawn.github.io/Millennium-Dawn/dev-resources/contributing/)               | Docs site setup, `bun run dev`, content conventions, link rules, the docs CI pipeline.            |
| [Code Stylization Guide](https://millenniumdawn.github.io/Millennium-Dawn/dev-resources/code-stylization-guide/)             | Formatting and code structure for HOI4 script files.                                              |
| [Content Review Guide](https://millenniumdawn.github.io/Millennium-Dawn/dev-resources/content-review-guide/)                 | Quality checklist and developer expectations.                                                     |
| [Focus Tree Design Principles](https://millenniumdawn.github.io/Millennium-Dawn/dev-resources/focus-tree-design-principles/) | Branch structure, pacing, choices.                                                                |
| [Git Workflow](https://millenniumdawn.github.io/Millennium-Dawn/dev-resources/git-workflow/)                                 | Fork workflow, branch naming, commits, PRs.                                                       |
| [AI Modding Guide](https://millenniumdawn.github.io/Millennium-Dawn/dev-resources/ai-modding-guide/)                         | Setting up local AI models for development.                                                       |

## One-Command Setup

```bash
python3 tools/dev_setup.py          # install hooks and Python tool dependencies
python3 tools/dev_setup.py --check  # verify environment
python3 tools/dev_setup.py --docs   # also install Node.js + Bun for docs site work
```

See the [Developer Setup Guide](https://millenniumdawn.github.io/Millennium-Dawn/dev-resources/developer-setup/) for the full walkthrough.

## Types of Contributions

| Area                     | Examples                                            |
| ------------------------ | --------------------------------------------------- |
| Focus Trees              | New trees, branch reworks, prerequisite fixes       |
| Events & Decisions       | Event chains, decision categories, triggered events |
| Ideas & National Spirits | New ideas, modifier tuning, icon assignments        |
| AI & Balance             | Strategy plans, equipment variants, stat tweaks     |
| Localisation             | English string fixes, tooltip accuracy              |
| Graphics                 | Portraits, focus icons, event pictures, 3D models   |
| Map & History            | State boundaries, country history, OOBs             |
| Documentation            | Docs site content, guides, tutorials, dev diaries   |
| Tooling                  | Python scripts, CI improvements, pre-commit hooks   |
| Bug Fixes                | Crash fixes, trigger errors, typos                  |

Non-English localisation is managed through [Paratranz](https://paratranz.cn/projects/millennium-dawn). Do not submit translations directly.

## AI Policy Summary

AI tooling is welcome. The full policy is on the [Developer Setup Guide](https://millenniumdawn.github.io/Millennium-Dawn/dev-resources/developer-setup/). The short version:

- **Code**: AI may draft, refactor, or debug. Review all output line-by-line. Run pre-commit. Verify game objects exist. Do not submit raw AI output.
- **Localisation**: AI may draft English strings. Human review required. Non-English is Paratranz-only.
- **Graphics**: Pure AI-generated art is not allowed. AI-generated military vehicle side profiles are acceptable only when no existing profile is available, and must be manually finalized and reviewed.
- **Docs/PRs**: AI may draft. Review for accuracy. Do not add "Generated with" footers or co-author trailers.

## PR Expectations

- Keep PRs focused on a single feature or fix when possible.
- Update [Changelog.txt](./Changelog.txt) under the current top-most version heading (see [Changelog Guidelines](https://millenniumdawn.github.io/Millennium-Dawn/dev-resources/contributing/)).
- Add yourself to [AUTHORS.md](./docs/src/content/misc/authors.md) if this is your first contribution.
- CI validation must pass and a team leader must approve before merge.

## What We Will Not Accept

- PRs that only reformat or restructure existing code without a functional reason.
- Machine-translated localisation.
- Content that violates Paradox Interactive's Terms of Service.
- Large, unfocused PRs that touch many unrelated files. Break them up.

## Resources

- [Documentation Site](https://millenniumdawn.github.io/Millennium-Dawn/) — all guides, tutorials, and reference docs
- [Discord](http://discord.gg/millenniumdawn) — team communication
- [tools/README.md](./tools/README.md) — dev tools directory layout

---

For questions, join the [Discord](http://discord.gg/millenniumdawn) or open an issue.
