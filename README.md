# AI Arena

A fully configurable, production-grade multi-AI orchestration platform where AI agents collaborate on a shared context file — with a professional Streamlit interface.

## Features

- **Multi-Agent Ping-Pong Loop** — 2+ agents take turns processing a shared context file
- **Provider Agnostic** — Supports OpenAI, Anthropic, OpenRouter, and extensible to more
- **Real File-Based Context** — Shared context is a real Markdown file on disk
- **Live UI** — Three-panel layout: configuration, conversation history, context viewer
- **Session Management** — Create, switch between, and export multiple sessions
- **Pause/Resume** — Inspect or edit context mid-run, then continue
- **Dry-Run Mode** — Test the UI and flow logic without real API calls
- **Rate Limiting** — Configurable delay between API calls
- **Context Diff** — See exactly what changed after each agent's turn
- **System Prompts** — File-based prompts in `/sys_prompts/`, selectable per agent

## Tech Stack

- **Python** >= 3.10
- **Streamlit** — UI
- **OpenAI / Anthropic / OpenRouter** — LLM providers
- **Pydantic** — data validation

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/<username>/ai-arena.git
cd ai-arena

# 2. Create virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate.bat

# macOS/Linux
source .venv/bin/activate

# 3. Install dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# 4. Copy environment file and add your API keys
cp .env.example .env

# 5. Run the app
streamlit run run.py
```

## GitHub Codespaces

1. Open the repository in GitHub Codespaces.
2. The devcontainer will automatically:
   - Build a Python 3.11 environment
   - Install all dependencies from `requirements.txt`
   - Start the Streamlit app on port 8501
3. Click "Open in Browser" when the port forwards.

## Editable Install (Development)

```bash
pip install -e .
```

## Project Structure

```
ai-arena/
├── ai_arena/
│   ├── __init__.py
│   ├── config.py           # App configuration (dirs, API keys)
│   ├── engine/             # Orchestrator, rate limiter, session, tools
│   │   ├── orchestrator.py
│   │   ├── rate_limiter.py
│   │   ├── session.py
│   │   ├── tool_executor.py
│   │   ├── tool_parser.py
│   │   └── tool_registry.py
│   ├── models/             # Data models (Agent, Message, SessionState)
│   │   ├── agent.py
│   │   ├── message.py
│   │   └── session_state.py
│   ├── providers/          # LLM provider abstraction
│   │   ├── base.py
│   │   ├── openai_provider.py
│   │   ├── anthropic_provider.py
│   │   └── openrouter_provider.py
│   ├── tools/              # Agent file tools
│   │   ├── base.py
│   │   └── file_tools.py
│   └── ui/                 # Streamlit UI components
│       ├── app.py          # Entry point
│       ├── chat_panel.py
│       ├── config_panel.py
│       └── context_panel.py
├── sys_prompts/            # System prompt files (.md)
├── contexts/               # Runtime context files
├── docs/                   # Full documentation
├── tests/                  # Test suite
├── run.py                  # Streamlit entry point
├── start_ui.bat            # Windows local startup
├── requirements.txt        # Python dependencies
├── pyproject.toml          # Build/install config
├── pyrightconfig.json      # Pyright type checker config
└── .streamlit/             # Streamlit config
```

## Agent Roles

| Agent  | Default Role | Behavior                                  |
|--------|-------------|-------------------------------------------|
| Agent A | Critic     | 3 positive points + 5 critical observations |
| Agent B | Optimist   | Solutions to criticisms + 1–3 new ideas   |
| Agent C | Summarizer | Summarize the discussion                  |
| Agent D | Synthesizer| Final synthesis of all contributions      |

## Documentation

See the [docs/](docs/) folder for:
- [Architecture Overview](docs/architecture.md)
- [Configuration Guide](docs/configuration.md)
- [Adding New Agents](docs/adding_agents.md)
- [Adding New Providers](docs/adding_providers.md)
- [Tool System](docs/tools.md)

## License

MIT
