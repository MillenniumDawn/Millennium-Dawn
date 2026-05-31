# CLAUDE.md

> **Project guidelines have moved to [AGENTS.md](./AGENTS.md).**
> All coding standards, formatting rules, game system conventions, and key resource links are documented there.

## Claude Code Skills

The following slash commands are available in this project (`.claude/skills/`):

| Skill                         | Description                                                                                                           |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `/validate [staged] [strict]` | Run all validation tools; optionally limit to staged files or fail on errors                                          |
| `/standardize <file>`         | Auto-standardize a focus/event/decision/idea file against MD conventions                                              |
| `/new-focus <TAG>`            | Scaffold a new country focus tree file with correct structure and localisation stubs                                  |
| `/review-branch`              | Review the current branch diff vs main for style violations, logic errors, balance issues, and adversarial edge cases |
| `/adversarial-review [file]`  | Hunt for unhandled scenarios, silent failures, and logic gaps in a file or the branch diff                            |
| `/fix-issue [number]`         | Find an open GitHub bug, diagnose the root cause, fix it, and open a PR                                               |
| `/content-review [file]`      | Check a file or branch diff against the full content review checklist (economics, politics, visual, military, AI)     |
| `/audit [file]`               | Code-quality, performance, and content audit on a file or the entire branch diff                                      |
| `/add-leader <TAG>`           | Scaffold generals, field marshals, and admirals using count formulas from new-general-guidelines                      |
| `/new-namelist <TAG>`         | Scaffold division name lists, ship hull names, and ship class design names for a country                              |
| `/lifecycle-check [TAG]`      | Audit a country branch against the focus tree lifecycle checklist — reports done/missing/partial                      |
| `/search-filter-check [file]` | Validate `search_filters` on every focus against the approved filter list and two-layer convention                    |
| `/update-claude`              | Summarize the current conversation and propose improvements to CLAUDE.md, rules, and skills                           |
| `/open-pr [issues…] ["title"]` | Create a draft PR with AngriestBird-style summary, link issues, and update Changelog.txt for unlisted changes        |
