# CLAUDE.md

> **Project guidelines have moved to [AGENTS.md](./AGENTS.md).**
> All coding standards, formatting rules, game system conventions, and key resource links are documented there.

@AGENTS.md

## Claude Code Skills

The following slash commands are available in this project (`.claude/skills/`):

| Skill                           | Description                                                                                                                       |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `/validate [staged] [strict]`   | Run all validation tools; optionally limit to staged files or fail on errors                                                      |
| `/standardize <file>`           | Auto-standardize a focus/event/decision/idea file against MD conventions                                                          |
| `/new-focus <TAG>`              | Scaffold a new country focus tree file with correct structure and localisation stubs                                              |
| `/adversarial-review [file]`    | Hunt for unhandled scenarios, silent failures, and logic gaps in a file or the branch diff                                        |
| `/fix-issue [number or "task"]` | Find an actionable GitHub issue (bug or well-scoped task), or a described task, implement it, and open a PR                       |
| `/close-issue [number]`         | Close a GitHub issue with a brief comment summarizing the applied fix                                                             |
| `/content-review [file]`        | Check a file or branch diff against the full content review checklist (economics, politics, visual, military, AI)                 |
| `/audit [file]`                 | Comprehensive review of a file or branch: correctness, edge cases, performance, simplification, content (replaces /review-branch) |
| `/add-leader <TAG>`             | Scaffold generals, field marshals, and admirals using count formulas from new-general-guidelines                                  |
| `/new-namelist <TAG>`           | Scaffold division name lists, ship hull names, and ship class design names for a country                                          |
| `/lifecycle-check [TAG]`        | Audit a country branch against the focus tree lifecycle checklist — reports done/missing/partial                                  |
| `/search-filter-check [file]`   | Validate `search_filters` on every focus against the approved filter list and two-layer convention                                |
| `/update-claude`                | Summarize the current conversation and propose improvements to CLAUDE.md, rules, and skills                                       |
| `/open-pr [issues…] ["title"]`  | Create a draft PR with AngriestBird-style summary, link issues, and update Changelog.txt for unlisted changes                     |
| `/changelog [version]`          | Summarize branch changes vs main and add them to Changelog.txt under existing categories                                          |
| `/test-plan [issues…]`          | Generate an approximate playthrough test plan for the branch in PR format (run after /open-pr)                                    |
| `/dev-diary-mdx [file]`         | Convert a Word/Google-Docs `.docx` dev diary into a publish-ready `.mdx` with extracted, in-order images                          |
