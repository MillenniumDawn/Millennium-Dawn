# Skills

Project slash commands for Claude Code. Each directory holds a `SKILL.md` whose frontmatter (`name`, `description`) is the source of truth — the session skill list is generated from it, so this table is a human-facing overview only.

| Skill                  | What it does                                                      |
| ---------------------- | ----------------------------------------------------------------- |
| `/add-leader`          | Scaffold generals, field marshals, and admirals for a TAG         |
| `/additional-income`   | Wire a country income/expense stream into the money system        |
| `/adversarial-review`  | Edge-case hunt over a diff or file (what could go wrong)          |
| `/audit`               | Full pre-merge review via parallel reviewer agents                |
| `/changelog`           | Add branch changes to Changelog.txt                               |
| `/close-issue`         | Close a GitHub issue with a fix summary (explicit-only)           |
| `/content-review`      | Check content against the MD content review checklist             |
| `/dev-diary-mdx`       | Convert a dev-diary .docx to publish-ready .mdx                   |
| `/fix-issue`           | Pick up a GitHub issue or task, fix it, open a PR                 |
| `/lifecycle-check`     | Audit a country branch against the lifecycle checklist            |
| `/md-tick-profiler`    | Flamegraph of the daily/weekly/monthly scripted tick load         |
| `/new-focus`           | Scaffold a country focus tree file with loc stubs                 |
| `/new-namelist`        | Scaffold division/ship/air namelists for a TAG                    |
| `/open-pr`             | Create a draft PR with summary, linked issues, changelog          |
| `/rework-brief`        | Reframe a rework task issue into a mechanic-by-mechanic design brief |
| `/search-filter-check` | Validate focus `search_filters` against the approved list         |
| `/standardize`         | Auto-standardize a mod file with the standardization tools        |
| `/test-plan`           | Generate a playthrough test plan for the branch (opt-in)          |
| `/update-claude`       | Propose CLAUDE.md/rules/docs/skills improvements from the session |
| `/validate`            | Run the validation tools and summarize errors (explicit-only)     |

Conventions: every skill has frontmatter with a trigger-quality `description`; `disable-model-invocation: true` marks skills that only run when the user invokes them (`/validate`, `/close-issue`, `/update-claude`). Reference material belongs in `.claude/docs/`, not in skill bodies — skills cite docs.
