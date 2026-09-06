# Folder Structure Reference

```
ai-arena/
├── ai_arena/                          # Main application package
│   ├── __init__.py                    # Package init
│   ├── config.py                      # Global configuration and env loader
│   ├── models/                        # Data models
│   │   ├── __init__.py
│   │   ├── agent.py                   # Agent model (id, name, role, provider, model, etc.)
│   │   ├── message.py                 # Message model (conversation history entry)
│   │   └── session_state.py           # Session state model (rounds, agents, status)
│   ├── providers/                     # LLM provider implementations
│   │   ├── __init__.py
│   │   ├── base.py                    # BaseProvider abstract class
│   │   ├── openai_provider.py         # OpenAI API implementation
│   │   ├── anthropic_provider.py      # Anthropic Claude API implementation
│   │   ├── openrouter_provider.py     # OpenRouter API implementation (free models)
│   │   └── cerebras_provider.py       # Cerebras Cloud API implementation (high-speed inference)
│   ├── tools/                         # Agent tool implementations
│   │   ├── __init__.py
│   │   ├── base.py                    # BaseTool abstract class and ToolResult
│   │   └── file_tools.py              # File manipulation tools (read, write, append, patch, summarize)
│   ├── engine/                        # Core orchestration logic
│   │   ├── __init__.py
│   │   ├── orchestrator.py            # Main middleware engine (one-shot turns, tool detection, advance)
│   │   ├── rate_limiter.py            # Thread-safe rate limiter
│   │   ├── session.py                 # SessionManager for multi-session support (atomic saves)
│   │   ├── tool_registry.py           # Central registry for all tools + agent-facing manual
│   │   ├── tool_parser.py             # Robust parser for tool calls from AI responses
│   │   └── tool_executor.py           # Single-attempt tool executor with audit logging
│   └── ui/                            # Streamlit UI components
│       ├── __init__.py
│       ├── app.py                     # Main app entry point with dark theme
│       ├── config_panel.py            # Sidebar configuration panel
│       ├── chat_panel.py              # Left panel: conversation history
│       ├── context_panel.py           # Right panel: shared context viewer
│       ├── status.py                  # Shared session-status helpers (pills, priority)
│       ├── stepper.py                 # Workflow step indicator
│       ├── tokens.py                  # Design tokens (single source of colors)
│       └── icons.py                   # Lucide SVG icon library
├── sys_prompts/                       # System prompt files (Markdown)
│   ├── critic.md                      # Critic agent prompt
│   ├── optimist.md                    # Optimist/Innovator agent prompt
│   ├── synthesizer.md                 # Final synthesis agent prompt (optional)
│   └── summarizer.md                  # Summarizer agent prompt (optional)
├── contexts/                          # Runtime context files (one per session)
│   ├── <session_id>.md                # Shared context file for a session
│   └── audit_<session_id>.log         # Tool call audit log per session
├── docs/                              # Project documentation
│   ├── README.md                      # Documentation index
│   ├── architecture.md                # Architecture overview
│   ├── folder_structure.md            # This file
│   ├── configuration.md               # Configuration guide
│   ├── adding_agents.md               # How to add new agents
│   ├── adding_providers.md            # How to add new providers
│   └── tools.md                       # Tool system documentation
├── tests/                             # Test suite (run with pytest)
│   ├── conftest.py                    # Shared fixtures (sandbox reset)
│   ├── test_comprehensive.py          # Full middleware flow
│   ├── test_dryrun_5rounds.py         # 5-round dry-run smoke (standalone script)
│   ├── test_fixes.py                  # Regression tests for the 2026-07-15 fixes
│   ├── test_middleware.py             # Registry/parser/executor unit tests
│   ├── test_one_shot_flow.py          # One-shot-per-turn flow + P0 advance regression
│   ├── test_openrouter.py             # OpenRouter provider tests (mocked)
│   ├── test_providers_live.py         # Real API tests (gated by AI_ARENA_LIVE_TESTS=1)
│   ├── test_quick.py                  # Import-time smoke test
│   └── test_regression_v2.py          # Regression tests for the 2026-07-20 fixes
├── requirements.txt                   # Python dependencies
├── pyproject.toml                     # Project metadata
├── .env.example                       # Example environment variables
├── .env                               # Actual environment variables (git-ignored)
├── run.py                             # Application entry point
└── README.md                          # Project readme
```

## Module Responsibilities

| Module | Responsibility |
|--------|---------------|
| `config.py` | Global config, directory setup, `.env` loading, API key lookup |
| `models/agent.py` | Agent data structure and serialization |
| `models/message.py` | Message data structure for conversation history |
| `models/session_state.py` | Session state tracking and progression |
| `providers/base.py` | Abstract provider interface |
| `providers/openai_provider.py` | OpenAI API integration |
| `providers/anthropic_provider.py` | Anthropic Claude API integration |
| `providers/openrouter_provider.py` | OpenRouter API integration (free models) |
| `providers/cerebras_provider.py` | Cerebras Cloud API integration (high-speed inference) |
| `tools/base.py` | Abstract tool interface and result types |
| `tools/file_tools.py` | File-based tools (read, write, append, patch, summarize) |
| `engine/orchestrator.py` | Middleware: one-shot agent turns, tool detection/execution, loop advance |
| `engine/rate_limiter.py` | Thread-safe rate limiting |
| `engine/session.py` | Session creation, persistence (atomic writes), and listing |
| `engine/tool_registry.py` | Central tool registry and manual generation |
| `engine/tool_parser.py` | Robust tool call parser with JSON fallback fixes |
| `engine/tool_executor.py` | Single-attempt tool executor with audit logging |
| `ui/app.py` | Streamlit app entry point with dark theme |
| `ui/config_panel.py` | Sidebar configuration UI |
| `ui/chat_panel.py` | Conversation history display |
| `ui/context_panel.py` | Context file viewer and progress indicator |
| `ui/status.py` | Shared session-status keyword + HTML pill helpers |
| `ui/stepper.py` | Workflow step indicator (pure `compute_step` + renderer) |
| `ui/tokens.py` | Design tokens: single source of colors |
| `ui/icons.py` | Lucide SVG icon helpers |
