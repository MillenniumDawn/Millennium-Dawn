# CLAUDE.md

> **Project guidelines have moved to [AGENTS.md](./AGENTS.md).**
> All coding standards, formatting rules, game system conventions, and key resource links are documented there.

## Claude Code Skills

The following slash commands are available in this project (`.claude/skills/`):

| Skill                         | Description                                                                                   |
| ----------------------------- | --------------------------------------------------------------------------------------------- |
| `/validate [staged] [strict]` | Run all validation tools; optionally limit to staged files or fail on errors                  |
| `/standardize <file>`         | Auto-standardize a focus/event/decision/idea file against MD conventions                      |
| `/new-focus <TAG>`            | Scaffold a new country focus tree file with correct structure and localisation stubs          |
| `/review-branch`              | Review the current branch diff vs main for style violations, logic errors, and balance issues |
| `/fix-issue [number]`         | Find an open GitHub bug, diagnose the root cause, fix it, and open a PR                       |
