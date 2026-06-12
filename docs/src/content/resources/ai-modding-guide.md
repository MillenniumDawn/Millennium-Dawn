---
title: AI-Assisted Modding Guide
description: Use AI tools to accelerate Millennium Dawn development — local models, Claude Code, Copilot, and best practices
---

AI coding assistants can speed up repetitive tasks, generate boilerplate, and help debug scripts. This guide covers the tools available in the Millennium Dawn repo, how to set them up, and how to use them responsibly.

> **AI Policy**: All AI-assisted contributions must be reviewed before submission. See the full [AI Policy in CONTRIBUTING.md](https://github.com/MillenniumDawn/Millennium-Dawn/blob/main/CONTRIBUTING.md#ai-policy) for what is allowed, restricted, and prohibited.

---

# What the Repo Provides

Millennium Dawn ships with first-class support for AI-assisted development:

| Resource                  | Location                 | Purpose                                                                                                                        |
| ------------------------- | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| **AGENTS.md**             | `/AGENTS.md`             | Repo-wide instructions for AI agents — coding standards, formatting rules, performance patterns, scripting pitfalls            |
| **Claude Code rules**     | `.claude/rules/`         | Detailed rules for localisation, scripted GUIs, general scripting, and more                                                    |
| **Claude Code skills**    | `.claude/skills/`        | Slash commands for common tasks: `/validate`, `/standardize`, `/new-focus`, `/review-branch`, `/audit`, `/fix-issue`, and more |
| **Documentation index**   | `.claude/docs/`          | Deep references for focuses, events, decisions, ideas, MIOs, AI strategy, AI equipment, diplomatic actions, and more           |
| **Validation tools**      | `tools/validation/`      | Python validators that catch common mistakes — run via pre-commit or manually                                                  |
| **Standardization tools** | `tools/standardization/` | Auto-reformatters for focuses, events, decisions, and ideas                                                                    |

These resources are designed to work together. An AI agent reading `AGENTS.md` knows the project's coding standards; the skills let it apply those standards mechanically.

---

# Tool Options

## Claude Code (Recommended)

[Claude Code](https://claude.ai/code) is a terminal-based AI assistant that reads the repo context automatically. The team uses it daily.

**Setup:**

1. Install Claude Code from [claude.ai/code](https://claude.ai/code).
2. Open a terminal in the Millennium Dawn repo directory.
3. Run `claude` — it reads `AGENTS.md` and `.claude/` automatically.

**Key skills available:**

| Skill          | Command                  | What it does                                               |
| -------------- | ------------------------ | ---------------------------------------------------------- |
| Validate       | `/validate`              | Run all validators on changed/staged files                 |
| Standardize    | `/standardize <file>`    | Auto-reformat a file to MD conventions                     |
| New focus tree | `/new-focus <TAG>`       | Scaffold a focus tree with stubs and loc keys              |
| Review branch  | `/review-branch`         | Quick standards review of the full branch diff             |
| Content review | `/content-review <file>` | Full quality checklist (economic, political, military, AI) |
| Deep audit     | `/audit <file>`          | Multi-agent audit: simplification + performance + content  |
| Fix issue      | `/fix-issue <number>`    | Find and fix a GitHub issue, open a PR                     |
| Changelog      | `/changelog`             | Summarize branch changes, update Changelog.txt             |

**Typical workflow:**

```bash
# Start Claude Code in the repo
claude

# Ask it to scaffold a focus tree
> /new-focus SER

# Review your changes before committing
> /review-branch

# Validate before pushing
> /validate
```

See [Claude Code Skills](/dev-resources/claude-code-skills/) for the full skill reference.

## GitHub Copilot

[GitHub Copilot](https://github.com/features/copilot) provides inline code suggestions in VS Code and other editors. It works well for HOI4 script completion but does not read repo-specific rules automatically.

**Setup:**

1. Install the GitHub Copilot extension in VS Code.
2. Sign in with your GitHub account.

**Best for:** Autocompleting repetitive script patterns, generating boilerplate event/decision/focus blocks.

**Limitations:** Copilot does not know MD-specific conventions (tab indentation, logging requirements, `ai_will_do` patterns). Always review its output against the [Code Stylization Guide](/dev-resources/code-stylization-guide/).

## Local Models with Ollama

[Ollama](https://ollama.com/) runs large language models locally on your machine. Everything stays offline after the initial model download.

**Benefits:**

- No internet required after setup
- Your code stays private
- Free to use (no API costs)
- Can run continuously for assistance

### Quick Setup

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh   # macOS/Linux
# Or download from ollama.com/download/windows   # Windows

# Pull a model
ollama pull codellama

# Run interactively
ollama run codellama
```

### Recommended Models

| Model           | Size    | Best For                             |
| --------------- | ------- | ------------------------------------ |
| `codellama`     | 7-13 GB | Code generation, general programming |
| `llama3`        | 4-8 GB  | General conversation, documentation  |
| `mistral`       | 4 GB    | Fast responses, code completion      |
| `qwen2.5-coder` | 2-4 GB  | Specialized for code tasks           |

### Hardware Requirements

| Model Size | RAM Needed | Use Case         |
| ---------- | ---------- | ---------------- |
| 4GB        | 8GB+       | Basic assistance |
| 7GB        | 16GB+      | Code generation  |
| 13GB       | 32GB+      | Complex tasks    |

### VS Code Integration

**Continue extension** — full-featured, multi-model support:

1. Install [Continue](https://marketplace.visualstudio.com/items?itemName=Continue.continue).
2. Configure in `~/.continue/config.json`:

```json
{
  "models": [
    {
      "model": "codellama",
      "provider": "ollama"
    }
  ]
}
```

**Cline extension** — lightweight, direct Ollama integration:

1. Install [Cline](https://marketplace.visualstudio.com/items?itemName=cline.cline).
2. Configure in VS Code settings (Ctrl/Cmd + , → Extensions → Cline):

```json
{
  "cline.models": [
    {
      "name": "codellama",
      "provider": "ollama",
      "baseUrl": "http://localhost:11434",
      "model": "codellama"
    }
  ],
  "cline.defaultModel": "codellama"
}
```

### Custom MD Expert Model

Create a model pre-loaded with MD conventions:

```bash
cat > Modelfile << 'EOF'
FROM codellama
PARAMETER temperature 0.3

SYSTEM """
You are an expert Hearts of Iron IV modder specializing in Millennium Dawn.
- Follow MD coding standards: 1 tab indent, logging in effects
- Use MD-specific scripted effects from common/scripted_effects/
- Reference docs in .claude/docs/ for modifiers and effects
- Always include ai_will_do in focus trees
- Use original_tag, not tag, in idea allowed blocks
- Use is_triggered_only = yes for events
"""
EOF

ollama create md-expert -f Modelfile
ollama run md-expert
```

### GPU Acceleration

Ollama uses GPU automatically if available. Verify with `ollama list` — look for the GPU indicator in model info.

### API Server Mode

Run Ollama as an API server for integration with other tools:

```bash
ollama serve    # starts on port 11434

# Query from another terminal
curl -X POST http://localhost:11434/api/generate -d '{
  "model": "codellama",
  "prompt": "How do I add a new idea in MD?",
  "stream": false
}'
```

---

# Effective Prompts for Modding

Good prompts include context about the mod's conventions. Generic prompts produce generic output.

## Code Review

```
You are reviewing Hearts of Iron IV mod code for Millennium Dawn.
Check for:
1. Correct use of MD-specific scripted effects
2. Performance issues (avoid every_country, MTTH events)
3. Style compliance (1 tab indent, logging in completion_reward)
4. Common errors: wrong scoping, invented modifier names, redundant AND wrappers

Review this code:
[PASTE CODE]
```

## Focus Tree Generation

```
Create a Millennium Dawn focus tree for [COUNTRY].
Rules:
- File: 05_[country]_focus.txt
- Use relative_position_id for positioning
- Include ai_will_do with game rule checks
- Add completion_reward with logging
- Use search_filters (two-layer pattern)
- Prefix focus IDs with TAG_

Country context: [DESCRIBE POLITICAL SITUATION]
```

## Debugging

```
Help debug this HOI4 script error:
[ERROR MESSAGE]

Code context:
[RELEVANT CODE]

Check for:
- Invalid triggers/effects
- Incorrect scope usage (tag vs original_tag)
- check_variable using >= or <= (not valid inline)
- NOR used as logical NOR (it scopes to Norway)
```

## Converting Ideas to Effects

```
Convert this idea definition to use MD's economic effects:
[IDEA CODE]

Use the scripted effects from common/scripted_effects/00_money_system.txt
Include picture = sprite_name and allowed_civil_war = { always = yes }
```

---

# Common AI Mistakes in HOI4 Scripting

AI models frequently produce these errors. Always check for them:

| Mistake                            | Why it's wrong                                                          | Fix                                           |
| ---------------------------------- | ----------------------------------------------------------------------- | --------------------------------------------- |
| Invented modifier names            | AI hallucinates modifiers that don't exist                              | Verify with `grep -r "modifier_name" common/` |
| `tag` in idea `allowed` blocks     | `tag` changes for civil war countries                                   | Use `original_tag`                            |
| Redundant `AND = { }`              | Implicit AND in triggers makes this unnecessary                         | Remove the wrapper                            |
| `check_variable = { v >= 0 }`      | `>=` and `<=` are not valid inline                                      | Use `compare = greater_than_or_equals`        |
| `NOR = { ... }` as logical NOR     | `NOR` is Norway's country tag, not a logic keyword                      | Use separate `NOT` blocks                     |
| Missing `province` on `naval_base` | `add_building_construction` for naval bases requires `province = XXXXX` | Add the province ID                           |
| `is_in_faction = TAG`              | `is_in_faction` is boolean, not a scope check                           | Use `is_in_faction_with = TAG`                |
| `has_trade_agreement_with`         | Not a valid HOI4 trigger                                                | Use `has_country_flag = trade_agreement@TAG`  |
| Empty `on_add = { log = "" }`      | Useless code                                                            | Remove it                                     |
| `cancel = { always = no }`         | Default behavior, adds nothing                                          | Remove it                                     |

Run `/validate` or `pre-commit run --files <path>` to catch these automatically.

---

# Best Practices

1. **AI output is a draft, not a deliverable.** Review every line before submission.
2. **Verify game objects exist.** AI invents modifier names, scripted effects, and triggers. Grep the codebase to confirm they're real.
3. **Test in-game when possible.** AI cannot run the HOI4 engine; you can.
4. **Use the repo's built-in tools.** The validation hooks and standardization scripts catch what AI misses.
5. **Disclose AI use in PRs.** If a substantial portion was AI-generated, say so in the PR description. This helps reviewers know where to look harder.
6. **Don't paste sensitive info into cloud AI.** Use local models (Ollama) for anything you wouldn't post publicly.
7. **Match the model to the task.** `codellama` for scripts, `llama3` for documentation, smaller models for quick completions.

---

# Troubleshooting (Ollama)

**Slow performance:** Use a smaller model (4GB instead of 13GB). Close other applications to free RAM. Check GPU utilization.

**Out of memory:** Run `free -h` (Linux) or check Activity Monitor (macOS). Kill stale instances with `pkill -f ollama`.

**Model not found:** Re-pull with `ollama pull codellama`. Check installed models with `ollama list`.

---

# Related Resources

- [Contributing Guide](/dev-resources/contributing/) — Contribution types, fork workflow, AI policy
- [Claude Code Skills](/dev-resources/claude-code-skills/) — Full skill reference
- [Code Stylization Guide](/dev-resources/code-stylization-guide/) — Formatting and code structure
- [Content Review Guide](/dev-resources/content-review-guide/) — Quality checklist
- [Ollama Documentation](https://github.com/ollama/ollama)
- [HOI4 Modding Wiki](https://hoi4.paradoxwikis.com/Modding)
