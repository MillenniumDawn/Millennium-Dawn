---
title: AI-Assisted Modding with Ollama
description: Self-host local AI models to assist with Millennium Dawn mod development
---

This guide covers setting up Ollama, a local AI runtime, to assist with modding tasks like code generation, debugging, and documentation.

> **Note**: Using AI for code generation is subject to the mod's [AI Policy](https://github.com/MillenniumDawn/Millennium-Dawn/blob/main/CONTRIBUTING.md#ai-policy).

---

# Quick Setup

```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull a model
ollama pull codellama

# 3. Run the model
ollama run codellama
```

---

# What is Ollama?

Ollama is a tool for running large language models (LLMs) locally on your machine. Unlike cloud-based AI (ChatGPT, Claude), everything runs offline on your hardware.

**Benefits for Modding**:

- No internet required after initial setup
- Your code stays private
- Free to use (no API costs)
- Can run continuously for assistance

---

# Installation

## macOS / Linux

```bash
# Install via curl
curl -fsSL https://ollama.com/install.sh | sh

# Or via Homebrew
brew install ollama
```

## Windows

Download from [ollama.com](https://ollama.com/download/windows) and run the installer.

## Verify Installation

```bash
ollama --version
```

---

# Model Selection

## Recommended Models for Modding

| Model           | Size    | Best For                             |
| --------------- | ------- | ------------------------------------ |
| `codellama`     | 7-13 GB | Code generation, general programming |
| `llama3`        | 4-8 GB  | General conversation, documentation  |
| `mistral`       | 4 GB    | Fast responses, code completion      |
| `qwen2.5-coder` | 2-4 GB  | Specialized for code tasks           |
| `minimax-m2.5`  | Varies  | Cloud model for complex reasoning    |

## Pulling Models

```bash
# Pull a model (downloads ~4-13GB)
ollama pull codellama
ollama pull llama3

# Check installed models
ollama list
```

## Hardware Requirements

| Model Size | RAM Needed | Use Case         |
| ---------- | ---------- | ---------------- |
| 4GB        | 8GB+       | Basic assistance |
| 7GB        | 16GB+      | Code generation  |
| 13GB       | 32GB+      | Complex tasks    |

---

# Integration with Development

## Interactive Mode

```bash
# Start an interactive session
ollama run codellama

# Ask questions directly
> How do I add a new focus tree in Millennium Dawn?
```

## Using with Claude Code

You can create a script to pipe context to Ollama:

```bash
#!/bin/bash
# ollama-ask.sh

# Get the last commit's diff
DIFF=$(git diff HEAD~1 --stat)

# Send to Ollama with mod context
ollama run codellama <<EOF
You are helping with Hearts of Iron IV mod development.
The recent changes are:
$DIFF

Provide a code review focusing on:
1. Style consistency with Millennium Dawn standards
2. Potential bugs
3. Performance considerations
EOF
```

## VS Code Integration

### Using Continue Extension

1. Install [Continue](https://marketplace.visualstudio.com/items?itemName=Continue.continue) VS Code extension
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

### Using Cline Extension

1. Install [Cline](https://marketplace.visualstudio.com/items?itemName=cline.cline) VS Code extension
2. Configure in VS Code settings (`Ctrl/Cmd + ,` → Settings → Extensions → Cline):

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

3. Alternative: Create `.cline/config.json` in your project root:

```json
{
  "models": [
    {
      "name": "codellama",
      "provider": "ollama",
      "baseUrl": "http://localhost:11434",
      "model": "codellama"
    }
  ],
  "defaultModel": "codellama"
}
```

**Cline vs Continue Differences:**

- **Cline**: More lightweight, direct Ollama integration, simpler configuration
- **Continue**: More features, multi-model support, advanced context management
- **Performance**: Cline typically faster for local models
- **Setup**: Cline requires less configuration for basic Ollama usage

**Cline Usage:**

- Use `Ctrl/Cmd + Shift + P` → "Cline: Ask" for quick queries
- Select text and use `Ctrl/Cmd + Shift + P` → "Cline: Ask about selection"
- Configure custom prompts in `.cline/prompts.json`

**Millennium Dawn Project Setup with Cline:**

Create `.cline/prompts.json` in your Millennium Dawn project root:

```json
{
  "prompts": [
    {
      "name": "MD Code Review",
      "prompt": "Review this Millennium Dawn code for:\n1. Style compliance (1 tab indent, logging)\n2. Performance issues (avoid every_country)\n3. MD-specific scripted effects usage\n4. Common HOI4 modding errors\n\nCode:\n{selection}"
    },
    {
      "name": "MD Focus Tree Generator",
      "prompt": "Generate a Millennium Dawn focus tree for {country}.\nRules:\n- File: 05_{country}_focus.txt\n- Use relative_position_id\n- Include ai_will_do with game rules\n- Add completion_reward with logging\n- Use search_filters\n\nContext: {context}"
    },
    {
      "name": "MD Debug Script",
      "prompt": "Debug this HOI4 script error:\nError: {error}\n\nCode:\n{selection}\n\nCheck for:\n- Invalid triggers/effects\n- Missing semicolons\n- Incorrect scope usage\n- MD-specific requirements"
    }
  ]
}
```

**Project-Specific Cline Commands:**

- `Cline: Ask about selection` → Use "MD Code Review" prompt
- `Cline: Ask` → Use "MD Focus Tree Generator" for new focuses
- `Cline: Ask` → Use "MD Debug Script" for troubleshooting

### Using Claude Code with Ollama

Create an alias in your shell:

```bash
# Add to ~/.zshrc
alias md-ai='ollama run codellama'
```

---

# Prompts for Modding Tasks

## Code Review

```
You are reviewing Hearts of Iron IV mod code for Millennium Dawn.
Check for:
1. Correct use of MD-specific scripted effects
2. Performance issues (avoid every_country, MTTH events)
3. Style compliance (1 tab indent, logging in completion_reward)
4. Common errors in triggers and effects

Review this code:
[PASTE CODE]
```

## Generating Focus Trees

```
Create a Millennium Dawn focus tree for [COUNTRY].
Follow these rules:
- File: 05_[country]_focus.txt
- Use relative_position_id for positioning
- Include ai_will_do with game rule checks
- Add completion_reward with logging
- Use search_filters

Country context: [DESCRIBE POLITICAL SITUATION]
```

## Debugging

```
Help debug this HOI4 script error:
[ERROR MESSAGE]

Code context:
[RELEVANT CODE]
```

## Converting Ideas to Effects

```
Convert this idea definition to use MD's economic effects:
[IDEA CODE]

Use the scripted effects from common/scripted_effects/00_money_system.txt
```

---

# Advanced Configuration

## GPU Acceleration

Ollama uses GPU automatically if available. To verify:

```bash
# Check if GPU is being used
ollama list
# Look for GPU indicator in model info
```

## Custom System Prompts

Create a custom model with MD-specific instructions:

```bash
# Create a Modfile
cat > Modelfile << 'EOF'
FROM codellama

PARAMETER temperature 0.3

SYSTEM """
You are an expert Hearts of Iron IV modder specializing in Millennium Dawn.
- Follow MD coding standards: 1 tab indent, logging in effects
- Use MD-specific scripted effects from common/scripted_effects/
- Reference docs in docs/dev-resources/ for modifiers and effects
- Always include ai_will_do in focus trees
"""
EOF

# Create custom model
ollama create md-expert -f Modelfile

# Use it
ollama run md-expert
```

## API Server Mode

Run Ollama as an API server for integration:

```bash
# Start server on port 11434
ollama serve

# In another terminal, query via API
curl -X POST http://localhost:11434/api/generate -d '{
  "model": "codellama",
  "prompt": "How do I add a new idea in MD?",
  "stream": false
}'
```

---

# Troubleshooting

## Slow Performance

- Use a smaller model (4GB instead of 13GB)
- Close other applications to free RAM
- Check GPU utilization

## Out of Memory

```bash
# Check available memory
free -h  # Linux
Activity Monitor  # macOS

# Kill other Ollama instances
pkill -f ollama
```

## Model Not Found

```bash
# Re-pull the model
ollama pull codellama

# Check model list
ollama list
```

---

# Best Practices

1. **Use as Assistant, Not Replacement**: AI helps with repetitive tasks but review all code
2. **Keep Context Local**: Don't paste sensitive information into cloud AIs
3. **Verify Before Commit**: Always test generated code in-game
4. **Use Appropriate Models**: `codellama` for code, `llama3` for documentation
5. **Iterate**: Start with simple prompts, refine based on results

---

# Related Resources

- [Ollama Documentation](https://github.com/ollama/ollama)
- [HOI4 Modding Wiki](https://hoi4.paradoxwikis.com/Modding)
- [Code Stylization Guide](/dev-resources/code-stylization-guide)
- [Code Resources](/dev-resources/code-resource)
