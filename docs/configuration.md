# Configuration Guide

## Overview

AI Arena is configured through the Streamlit UI — no code changes are required for standard use. This guide explains all configuration options.

## Global Settings

### Ping-pong Rounds
- **Default:** 10
- **Range:** 1–50
- **Description:** Number of full cycles through all active agents. Each round gives each enabled agent one turn.

### Rate Limit (seconds)
- **Default:** 60
- **Range:** 0–300
- **Description:** Minimum delay between API calls. Prevents hitting rate limits on provider APIs. Set to 0 for no delay (use with caution).

### Dry-run Mode
- **Default:** Off
- **Description:** When enabled, the orchestrator simulates responses without making real API calls. Useful for testing UI and flow logic.

## Agent Configuration

Each agent can be configured independently with:

### Name
Human-readable identifier shown in the conversation history and context file.

### Provider
The LLM provider to use. Available options:
- **OpenAI** — GPT-4o, GPT-4 Turbo, GPT-4, GPT-3.5
- **Anthropic** — Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku
- **OpenRouter** — Free and paid models via OpenRouter (e.g. `openrouter/free`)

### Model
Specific model variant for the selected provider. Choices are populated dynamically based on provider selection.

### API Key
Your API key for the selected provider. Keys are not persisted to disk — they are stored only in the Streamlit session state during the session.

### System Prompt
Pre-configured prompt loaded from `/sys_prompts/` or a custom prompt entered directly.

## System Prompts

System prompts are stored as Markdown files in the `/sys_prompts/` directory. Available prompts:

| File | Agent Role | Description |
|------|-----------|-------------|
| `critic.md` | Critic | Adds 3 positive points and 5 critical observations |
| `optimist.md` | Optimist | Proposes solutions to criticisms and adds 1–3 new ideas |
| `synthesizer.md` | Synthesizer | Produces final synthesis report (optional) |
| `summarizer.md` | Summarizer | Creates concise summaries of context (optional) |

### Creating Custom Prompts
1. Create a new `.md` file in `/sys_prompts/`
2. Select it from the dropdown in the UI config panel
3. The prompt will be loaded automatically

### Editing Prompts
Prompts can be edited directly in the `/sys_prompts/` directory while the app is running. Changes will be reflected in new sessions.

## Sessions

### Creating Sessions
- Enter a session name in the sidebar
- Click "Create Session"
- The session creates a new context file in `/contexts/`

### Switching Sessions
- Select a session from the dropdown
- Click "Switch to Session"

### Deleting Sessions
- Select a session from the dropdown
- Click "Delete Session"
- The session file and context file are removed

## API Keys

API keys are entered in the Streamlit sidebar per agent. The UI will automatically fill the field from a `.env` file if one exists in the project root.

Required environment variables (in `.env`):

```
OPENAI_API_KEY=sk-...
OPENROUTER_API_KEY=sk-or-...
ANTHROPIC_API_KEY=sk-ant-...
```

UI-configured keys take precedence over `.env` values.

## Environment Variables
