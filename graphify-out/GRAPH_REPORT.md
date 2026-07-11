# Graph Report - ai-arena  (2026-07-11)

## Corpus Check
- 48 files · ~14,703 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 465 nodes · 851 edges · 29 communities (23 shown, 6 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 43 edges (avg confidence: 0.53)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_ToolRegistry|ToolRegistry]]
- [[_COMMUNITY_ToolResult|ToolResult]]
- [[_COMMUNITY_ProviderError|ProviderError]]
- [[_COMMUNITY_How to Add a New Provider|How to Add a New Provider]]
- [[_COMMUNITY_Configuration Guide|Configuration Guide]]
- [[_COMMUNITY_BaseProvider|BaseProvider]]
- [[_COMMUNITY_Tool System Documentation|Tool System Documentation]]
- [[_COMMUNITY_render_app|render_app]]
- [[_COMMUNITY_.run_turn|.run_turn]]
- [[_COMMUNITY_RateLimiter|RateLimiter]]
- [[_COMMUNITY_SessionState|SessionState]]
- [[_COMMUNITY_Agent|Agent]]
- [[_COMMUNITY_app.py|app.py]]
- [[_COMMUNITY_Orchestrator|Orchestrator]]
- [[_COMMUNITY_AppConfig|AppConfig]]
- [[_COMMUNITY_SessionManager|SessionManager]]
- [[_COMMUNITY_.create_session|.create_session]]
- [[_COMMUNITY_._call_provider|._call_provider]]
- [[_COMMUNITY_.get|.get]]
- [[_COMMUNITY_Critic Agent System Prompt|Critic Agent System Prompt]]
- [[_COMMUNITY_OptimistInnovator Agent System Prompt|Optimist/Innovator Agent System Prompt]]
- [[_COMMUNITY_._build_system_prompt|._build_system_prompt]]
- [[_COMMUNITY_Summarizer Agent System Prompt|Summarizer Agent System Prompt]]
- [[_COMMUNITY_Synthesizer Agent System Prompt|Synthesizer Agent System Prompt]]
- [[_COMMUNITY_.chat|.chat]]
- [[_COMMUNITY_Initial Prompt|Initial Prompt]]
- [[_COMMUNITY_AGENTS|AGENTS.md]]
- [[_COMMUNITY___init__.py|__init__.py]]
- [[_COMMUNITY_ai-arena|ai-arena]]

## God Nodes (most connected - your core abstractions)
1. `Orchestrator` - 35 edges
2. `SessionState` - 31 edges
3. `Agent` - 26 edges
4. `ToolRegistry` - 25 edges
5. `ProviderError` - 21 edges
6. `ToolResult` - 21 edges
7. `SessionManager` - 20 edges
8. `ToolExecutor` - 20 edges
9. `BaseProvider` - 20 edges
10. `BaseTool` - 19 edges

## Surprising Connections (you probably didn't know these)
- `test_chat_requires_api_key()` --indirect_call--> `ProviderError`  [INFERRED]
  tests/test_openrouter.py → ai_arena/providers/base.py
- `test_chat_requires_openai_package()` --indirect_call--> `ProviderError`  [INFERRED]
  tests/test_openrouter.py → ai_arena/providers/base.py
- `test_openrouter_integration_through_orchestrator()` --calls--> `Orchestrator`  [EXTRACTED]
  tests/test_openrouter.py → ai_arena/engine/orchestrator.py
- `test_full_middleware_flow()` --calls--> `SessionManager`  [EXTRACTED]
  tests/test_comprehensive.py → ai_arena/engine/session.py
- `test_tool_registry()` --calls--> `ToolRegistry`  [EXTRACTED]
  tests/test_middleware.py → ai_arena/engine/tool_registry.py

## Import Cycles
- None detected.

## Communities (29 total, 6 thin omitted)

### Community 0 - "ToolRegistry"
Cohesion: 0.06
Nodes (49): Engine package for AI Arena., AuditLogger, build_tool_error_envelope(), build_tool_result_envelope(), Any, Tool executor with retry logic and audit logging for AI Arena.  Executes tool ca, Log a tool call attempt., Log a tool execution result. (+41 more)

### Community 1 - "ToolResult"
Cohesion: 0.08
Nodes (34): ABC, Tool registry for AI Arena.  Single source of truth for all available tools. Add, Register the default file manipulation tools., Register a tool by its name.          Args:             tool: Tool instance to r, BaseTool, Any, Base tool abstraction and result types., Raised when a tool execution fails. (+26 more)

### Community 2 - "ProviderError"
Cohesion: 0.05
Nodes (32): AnthropicProvider, Any, Anthropic Claude API provider., Send messages to Anthropic and return response text., Validate Anthropic API key., ProviderError, Raised when a provider encounters an error., OpenAIProvider (+24 more)

### Community 3 - "How to Add a New Provider"
Cohesion: 0.05
Nodes (36): Advanced: Programmatic Agent Creation, Agent Configuration Fields, Agent Roles, Agent Turn Order, Example: Adding a Researcher Agent, How to Add a New Agent, Quick Start, BaseProvider Interface (+28 more)

### Community 4 - "Configuration Guide"
Cohesion: 0.10
Nodes (21): Agent Configuration, API Key, API Keys, Configuration Guide, Creating Custom Prompts, Creating Sessions, Deleting Sessions, Dry-run Mode (+13 more)

### Community 5 - "BaseProvider"
Cohesion: 0.14
Nodes (11): Anthropic provider implementation., BaseProvider, Base provider abstraction for AI Arena., Abstract base class for AI providers.      Subclasses must implement the chat me, Validate that an API key is usable.          Args:             api_key: The API, Return the provider display name., Return the default model for this provider., Return list of available models for this provider. (+3 more)

### Community 6 - "Tool System Documentation"
Cohesion: 0.10
Nodes (20): append_file, Architecture Overview, Audit Logging, Available Tools, Creating Custom Tools, Format Specification, Key Components, Middleware Flow (+12 more)

### Community 7 - "render_app"
Cohesion: 0.11
Nodes (17): _get_session_manager(), _init_session_state(), Main entry point for the Streamlit application., Initialize Streamlit session state defaults., Get or create the session manager, persisting it in session state., render_app(), _get_agent_color(), Any (+9 more)

### Community 8 - ".run_turn"
Cohesion: 0.15
Nodes (9): Read the current shared context file.          Args:             session: Curren, Update the shared context file with new content.          Args:             sess, Append agent response to context file content.          Args:             contex, Execute a single agent turn with full middleware logic.          The middleware, Process tool calls in an agent response with retry logic.          Args:, Execute a single step (one agent turn).          Args:             session: Curr, Message, Represents a single message in the conversation history.      Attributes: (+1 more)

### Community 9 - "RateLimiter"
Cohesion: 0.12
Nodes (10): Start the orchestration loop for a session.          Args:             session:, Initialize orchestrator.          Args:             session_manager: Session man, RateLimiter, Rate limiter for enforcing delays between API calls., Thread-safe rate limiter enforcing a minimum delay between calls.      Uses a si, Initialize rate limiter.          Args:             delay_seconds: Minimum secon, Block until the rate limit allows a call.          Returns:             The actu, Reset the rate limiter, allowing an immediate call. (+2 more)

### Community 10 - "SessionState"
Cohesion: 0.17
Nodes (12): Represents the full state of an orchestration session.      Attributes:, Return only enabled agents in order., Return the currently active agent., Advance to the next agent, cycling through rounds.          Returns:, Check if the session has completed all rounds., SessionState, _export_session(), Export session as a markdown file. (+4 more)

### Community 11 - "Agent"
Cohesion: 0.19
Nodes (10): Agent, AgentRole, Agent model representing an AI agent in the orchestration loop., Represents a configurable AI agent.      Attributes:         id: Unique identifi, Serialize agent to dictionary., Create agent from dictionary., AI Arena models package., Configuration panel for AI Arena UI.  Handles provider selection, API keys, mode (+2 more)

### Community 12 - "app.py"
Cohesion: 0.22
Nodes (7): Configuration management for AI Arena.  Supports loading from environment variab, Core orchestration engine for AI Arena.  The Orchestrator acts as middleware bet, Session manager for multi-session support., Message model for conversation history., Session state model for managing orchestration sessions., Main Streamlit application for AI Arena.  Implements the three-panel layout: - L, Chat panel for AI Arena UI.  Displays the conversation history between agents wi

### Community 13 - "Orchestrator"
Cohesion: 0.14
Nodes (9): Orchestrator, Main orchestration engine acting as middleware between AI agents.      The middl, Stop the orchestration loop., Pause the orchestration loop., Resume a paused session., Register a provider by name., Return list of registered provider names., Test a complete middleware flow with tool calls. (+1 more)

### Community 14 - "AppConfig"
Cohesion: 0.18
Nodes (8): AppConfig, Path, Global application configuration.      Attributes:         app_name: Application, Ensure directories exist., Return mapping of prompt name to file path., Load a system prompt by name (stem).          Args:             name: Prompt nam, Return the context file path for a given session., Return the API key for a provider from environment variables.          Looks up

### Community 15 - "SessionManager"
Cohesion: 0.17
Nodes (8): Any, List all sessions with metadata., Manages multiple named orchestration sessions.      Sessions are persisted to di, Retrieve a session by ID., Return the currently active session., Set the active session by ID.          Returns:             True if session exis, SessionManager, test_openrouter_integration_through_orchestrator()

### Community 16 - ".create_session"
Cohesion: 0.22
Nodes (5): Path, Delete a session and its context file.          Returns:             True if del, Persist session state to disk., Initialize session manager.          Args:             storage_dir: Directory fo, Create a new session.          Args:             name: Human-readable session na

### Community 17 - "._call_provider"
Cohesion: 0.25
Nodes (4): Build the message list for a provider API call.          Args:             agent, Call the provider API for the given agent.          Args:             agent: The, Generate a simulated response for dry-run mode.          Args:             agent, Get a registered provider by name.

### Community 18 - ".get"
Cohesion: 0.33
Nodes (3): Retrieve a tool by name.          Args:             name: Tool name.          Re, Return all registered tools., Generate the tool usage manual for injection into system prompts.          Retur

### Community 19 - "Critic Agent System Prompt"
Cohesion: 0.40
Nodes (4): Critic Agent System Prompt, Output Format:, Responsibilities:, Rules:

### Community 20 - "Optimist/Innovator Agent System Prompt"
Cohesion: 0.40
Nodes (4): Optimist/Innovator Agent System Prompt, Output Format:, Responsibilities:, Rules:

### Community 22 - "Summarizer Agent System Prompt"
Cohesion: 0.50
Nodes (3): Output Format:, Responsibilities:, Summarizer Agent System Prompt

### Community 23 - "Synthesizer Agent System Prompt"
Cohesion: 0.50
Nodes (3): Output Format:, Responsibilities:, Synthesizer Agent System Prompt

## Knowledge Gaps
- **73 isolated node(s):** `ai-arena`, `graphify`, `Features`, `Quick Start`, `Architecture` (+68 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Orchestrator` connect `Orchestrator` to `ToolRegistry`, `ProviderError`, `.run_turn`, `RateLimiter`, `SessionState`, `app.py`, `SessionManager`, `._call_provider`, `._build_system_prompt`?**
  _High betweenness centrality (0.097) - this node is a cross-community bridge._
- **Why does `ToolRegistry` connect `ToolRegistry` to `ToolResult`, `RateLimiter`, `app.py`, `Orchestrator`, `.get`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Why does `BaseProvider` connect `BaseProvider` to `ToolResult`, `ProviderError`, `Agent`, `app.py`, `Orchestrator`, `._call_provider`, `.chat`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `Orchestrator` (e.g. with `RateLimiter` and `SessionManager`) actually correct?**
  _`Orchestrator` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `SessionState` (e.g. with `Agent` and `Message`) actually correct?**
  _`SessionState` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `ToolRegistry` (e.g. with `Orchestrator` and `AuditLogger`) actually correct?**
  _`ToolRegistry` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `ProviderError` (e.g. with `AnthropicProvider` and `OpenAIProvider`) actually correct?**
  _`ProviderError` has 8 INFERRED edges - model-reasoned connections that need verification._