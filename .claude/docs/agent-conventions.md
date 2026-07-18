# Agent Conventions

Shared rules for every agent under `.claude/agents/`. Read once at the start of any subagent task; each agent file lists only the conventions specific to its role.

## Universal anti-rules

Apply to every agent. Individual agents may add more; they never relax these.

- **Do NOT run validators or `pre-commit run --all-files`.** Validation runs on GitHub CI at PR time. Pre-commit's auto-fixers rewrite the whole repo and leave hundreds of unrelated whitespace edits. To preview a hook locally, scope it: `pre-commit run --files <path1> <path2>`.
- **Do NOT add Claude attribution.** No `Co-Authored-By: Claude`, no `Generated with Claude Code` footer in commits or PR descriptions. The user commits under their own identity.
- **Do NOT modify files outside the requested scope.** If a task names a file or country tag, edits stay within that scope. Subagents have silently leaked edits to neighbor files before; always mentally `git diff --stat` before claiming done.
- **Do NOT touch non-English localisation files** (`*_l_french.yml`, `*_l_russian.yml`, etc.). Managed via Paratranz.
- **Do NOT modify anything under `resources/`** unless the user explicitly asks. Reference material only.
- **Do NOT invent identifier names.** Modifier names, define names, event IDs, GFX sprites, scripted effect names — grep first. The engine accepts unknown names silently and the code does nothing.

## Standard required reading

Most agents read these in addition to anything in their own "Required reading" section:

- `AGENTS.md` — project-wide conventions, pre-commit/CI divergence, formatting rules.
- `.claude/rules/general-rules.md` — scoping traps, modifier rules, scripting patterns.
- `.claude/docs/known-false-positives.md` — patterns that look wrong but are intentional.

Reviewer / analyzer agents also read:

- `.claude/docs/performance-patterns.md` — performance anti-patterns.

Loc-touching agents also read:

- `.claude/docs/localisation-rules.md` — encoding, key format, style.
- `.claude/docs/typo-watchlist.md` — recurring typos.

## Output format conventions

Reviewer and analyzer agents return findings in this shape. Builder agents have their own templated output (described in their file).

- **Summary** — one sentence: "clean" or "N issues found".
- **Findings by category** — each: `file:line — issue — suggested fix`. Skip empty categories rather than padding.
- **Severity counts** — `Critical / High / Medium / Low` totals.
- **Open questions / notes** — anything flagged but not certain.

Severity rubric (when applicable):

| Tier     | Meaning                                                                                                                    |
| -------- | -------------------------------------------------------------------------------------------------------------------------- |
| Critical | Game-breaking, silently-broken behavior, or perf catastrophe (unbounded daily `every_country`, GUI `dirty = global.date`). |
| High     | Clear correctness bug or significant perf hit, but the surface still works.                                                |
| Medium   | Style / readability / minor perf — should fix but won't block.                                                             |
| Low      | Cosmetic; nice-to-have.                                                                                                    |

## Hand-back contract

Every agent must end its turn with a self-contained report the caller can act on without re-reading source files:

- Quote file paths and line numbers, not "in the thing we just looked at".
- State what changed (writer agents) or what was found (reviewers) in plain prose at the top.
- Flag anything the caller must verify themselves (in-game test, grep, opinion modifier wiring).
- If you couldn't complete the task, say so explicitly with the blocker; never claim done on partial work.
- Be terse (see `AGENTS.md` > Output Style): lead with the conclusion, report facts not process, cut padding confirmations and tool-by-tool narration. Trim words, never information — no dropped path, line, finding, or caveat.

## Scripting & encoding rules

Scripting-pattern and encoding rules are always in context via `.claude/rules/general-rules.md` — re-read its Scripting Patterns section before flagging; do not restate rules in findings, cite them.
