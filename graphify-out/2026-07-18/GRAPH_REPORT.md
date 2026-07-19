# Graph Report - ai-arena  (2026-07-18)

## Corpus Check
- 57 files · ~26,006 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 673 nodes · 1213 edges · 47 communities (43 shown, 4 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 51 edges (avg confidence: 0.53)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `281572f7`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

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
- [[_COMMUNITY_AuditLogger|AuditLogger]]
- [[_COMMUNITY_راهنمای Deploy بر روی Railway|راهنمای Deploy بر روی Railway]]
- [[_COMMUNITY_Zarfiat-e jadid (5 file taghir, 2 file jadid)|Zarfiat-e jadid (5 file taghir, 2 file jadid)]]
- [[_COMMUNITY_config_panel.py|config_panel.py]]
- [[_COMMUNITY_AnthropicProvider|AnthropicProvider]]
- [[_COMMUNITY_ProviderError|ProviderError]]
- [[_COMMUNITY_CerebrasProvider|CerebrasProvider]]
- [[_COMMUNITY_test_providers_live.py|test_providers_live.py]]
- [[_COMMUNITY_ToolCall|ToolCall]]
- [[_COMMUNITY_tool_executor.py|tool_executor.py]]
- [[_COMMUNITY_OpenAIProvider|OpenAIProvider]]
- [[_COMMUNITY_render_context_panel|render_context_panel]]
- [[_COMMUNITY_stepper.py|stepper.py]]
- [[_COMMUNITY_icon|icon]]
- [[_COMMUNITY__render_status_bar|_render_status_bar]]
- [[_COMMUNITY__render_run_bar|_render_run_bar]]
- [[_COMMUNITY_graphify|graphify]]
- [[_COMMUNITY_.start_background|.start_background]]

## God Nodes (most connected - your core abstractions)
1. `Orchestrator` - 52 edges
2. `SessionState` - 36 edges
3. `Agent` - 34 edges
4. `SessionManager` - 33 edges
5. `ProviderError` - 27 edges
6. `ToolRegistry` - 25 edges
7. `BaseProvider` - 22 edges
8. `OpenRouterProvider` - 22 edges
9. `ToolResult` - 21 edges
10. `ToolExecutor` - 20 edges

## Surprising Connections (you probably didn't know these)
- `_CapturingProvider` --uses--> `Orchestrator`  [INFERRED]
  tests/test_fixes.py → ai_arena/engine/orchestrator.py
- `_CapturingProvider` --uses--> `RateLimiter`  [INFERRED]
  tests/test_fixes.py → ai_arena/engine/rate_limiter.py
- `test_rate_limiter_preserves_last_call()` --calls--> `RateLimiter`  [EXTRACTED]
  tests/test_fixes.py → ai_arena/engine/rate_limiter.py
- `test_parser_json_fence_with_nested_args()` --calls--> `parse_tool_call()`  [EXTRACTED]
  tests/test_fixes.py → ai_arena/engine/tool_parser.py
- `test_parser_nested_tool_call_fence()` --calls--> `parse_tool_call()`  [EXTRACTED]
  tests/test_fixes.py → ai_arena/engine/tool_parser.py

## Import Cycles
- None detected.

## Communities (47 total, 4 thin omitted)

### Community 0 - "ToolRegistry"
Cohesion: 0.17
Nodes (15): build_tool_result_envelope(), Executes tool calls with retry logic and audit logging.      The executor:     1, Initialize tool executor.          Args:             registry: Tool registry ins, Wrap a tool result in a labeled envelope for AI consumption.      Args:, ToolExecutor, Central registry for all available agent tools.      Tools are registered once a, ToolRegistry, Test retry logic with failing tool calls. (+7 more)

### Community 1 - "ToolResult"
Cohesion: 0.07
Nodes (36): ABC, Tool registry for AI Arena.  Single source of truth for all available tools. Add, Register the default file manipulation tools., Register a tool by its name.          Args:             tool: Tool instance to r, Retrieve a tool by name.          Args:             name: Tool name.          Re, Return all registered tools., Generate the tool usage manual for injection into system prompts.          Retur, BaseTool (+28 more)

### Community 2 - "ProviderError"
Cohesion: 0.15
Nodes (7): OpenRouterProvider, Any, Validate OpenRouter API key., OpenRouter API provider supporting free and paid models., Initialize OpenRouter provider., Send messages to OpenRouter and return response text., provider()

### Community 3 - "How to Add a New Provider"
Cohesion: 0.05
Nodes (39): Advanced: Programmatic Agent Creation, Agent Configuration Fields, Agent Roles, Agent Turn Order, Example: Adding a Researcher Agent, How to Add a New Agent, Quick Start, BaseProvider Interface (+31 more)

### Community 4 - "Configuration Guide"
Cohesion: 0.10
Nodes (21): Agent Configuration, API Key, API Keys, Configuration Guide, Creating Custom Prompts, Creating Sessions, Deleting Sessions, Dry-run Mode (+13 more)

### Community 5 - "BaseProvider"
Cohesion: 0.20
Nodes (7): Anthropic provider implementation., Base provider abstraction for AI Arena., Cerebras provider implementation.  Cerebras Cloud provides high-speed inferenc, Providers package for AI Arena., OpenAI provider implementation., OpenRouter provider implementation.  OpenRouter provides access to many free mod, Main Streamlit application for AI Arena.  Layout (responsive, collapses graceful

### Community 6 - "Tool System Documentation"
Cohesion: 0.10
Nodes (20): append_file, Architecture Overview, Audit Logging, Available Tools, Creating Custom Tools, Format Specification, Key Components, Middleware Flow (+12 more)

### Community 7 - "render_app"
Cohesion: 0.14
Nodes (13): _consume_loop_error(), _get_session_manager(), _init_session_state(), _maybe_autorefresh(), If a session is running, schedule a rerun every 2s to refresh the UI.      The 2, Main entry point for the Streamlit application., Initialize Streamlit session state defaults.      Only the *Streamlit-side* stat, Get or create the session manager, persisting it in session state. (+5 more)

### Community 8 - ".run_turn"
Cohesion: 0.15
Nodes (9): Read the current shared context file.          Args:             session: Curren, Update the shared context file with new content.          Args:             sess, Append agent response to context file content.          Args:             contex, Execute a single agent turn with full middleware logic.          The middleware, Process tool calls in an agent response with retry logic.          Args:, Execute a single step (one agent turn).          Args:             session: Curr, Message, Represents a single message in the conversation history.      Attributes: (+1 more)

### Community 9 - "RateLimiter"
Cohesion: 0.15
Nodes (8): Engine package for AI Arena., Initialize orchestrator.          Args:             session_manager: Session man, RateLimiter, Rate limiter for enforcing delays between API calls., Thread-safe rate limiter enforcing a minimum delay between calls.      Uses a si, Initialize rate limiter.          Args:             delay_seconds: Minimum secon, Block until the rate limit allows a call.          Returns:             The actu, Reset the rate limiter, allowing an immediate call.

### Community 10 - "SessionState"
Cohesion: 0.40
Nodes (3): Return only enabled agents in order., Return the currently active agent., Advance to the next agent, cycling through rounds.          Returns:

### Community 11 - "Agent"
Cohesion: 0.05
Nodes (47): Any, Path, Session manager for multi-session support., Rebuild a Message from a dict, tolerating missing optional fields., Parse an ISO-8601 timestamp string, falling back to ``now``., Create a new session.          Args:             name: Human-readable session na, Set the active session by ID.          Returns:             True if session exis, Manages multiple named orchestration sessions.      Sessions are persisted to di (+39 more)

### Community 12 - "app.py"
Cohesion: 0.18
Nodes (15): Configuration management for AI Arena.  Supports loading from environment variab, Core orchestration engine for AI Arena.  The Orchestrator acts as middleware bet, has_tool_call(), _iter_json_objects(), parse_tool_call(), Tool call parser for AI Arena.  Parses structured tool calls from AI responses,, Parse a JSON object string, with light-touch recovery for common LLM     issues, Parse a tool call from an AI response.      Tries, in order:     1. ``\`\`\`tool (+7 more)

### Community 13 - "Orchestrator"
Cohesion: 0.13
Nodes (9): Orchestrator, Return list of registered provider names., Main orchestration engine acting as middleware between AI agents.      The middl, Background loop body. Designed to run in a daemon thread.          Exits when ``, Return whether the background loop is currently executing., Atomically read and clear the latest background-loop error., Return whether the background thread has been started and is alive., Register a provider by name. (+1 more)

### Community 14 - "AppConfig"
Cohesion: 0.18
Nodes (8): AppConfig, Path, Global application configuration.      Attributes:         app_name: Application, Ensure directories exist., Return mapping of prompt name to file path., Load a system prompt by name (stem).          Args:             name: Prompt nam, Return the context file path for a given session., Return the API key for a provider from environment variables.          Looks up

### Community 15 - "SessionManager"
Cohesion: 0.12
Nodes (9): Start the orchestration loop for a session.          Args:             session:, Stop the orchestration loop., Pause the orchestration loop., Resume a paused session., Retrieve a session by ID., Return the currently active session., Represents the full state of an orchestration session.      Attributes:, Check if the session has completed all rounds. (+1 more)

### Community 16 - ".create_session"
Cohesion: 0.07
Nodes (29): 10. No `prefers-reduced-motion` support ✅ **FIXED**, 11. Three equal columns break on mobile ✅ **IMPROVED**, 12. No download/copy for the context file ✅ **FIXED**, 13. Chat badge readability ✅ **FIXED**, 14. Touch targets too small ✅ **FIXED**, 1. `hash()` bug — agent color changes on every rerun ✅ **FIXED**, 2. Redundant H1 — two titles for the same thing ✅ **FIXED**, 3. Export writes to disk instead of offering a browser download ✅ **FIXED** (+21 more)

### Community 17 - "._call_provider"
Cohesion: 0.33
Nodes (3): Get a registered provider by name., Call the provider API for the given agent.          Args:             agent: The, Generate a simulated response for dry-run mode.          Args:             agent

### Community 18 - ".get"
Cohesion: 0.10
Nodes (19): AI Arena — Review & Fix Plan (2026-07-15), Out of scope (acknowledged but deferred), P0-1. SessionManager never reloads from disk, P0-2. Tool parser regex rejects nested JSON, P0-3. Background thread writes to st.session_state (race), P0-4. `start_session` resets RateLimiter state, P0 — Critical Bugs (must fix), P1-5. Audit log silently swallows IO errors (+11 more)

### Community 19 - "Critic Agent System Prompt"
Cohesion: 0.40
Nodes (4): Critic Agent System Prompt, Output Format:, Responsibilities:, Rules:

### Community 20 - "Optimist/Innovator Agent System Prompt"
Cohesion: 0.40
Nodes (4): Optimist/Innovator Agent System Prompt, Output Format:, Responsibilities:, Rules:

### Community 21 - "._build_system_prompt"
Cohesion: 0.33
Nodes (3): Get the auto-generated tool manual for prompt injection.          Returns:, Build the system prompt for an agent.          Args:             agent: The agen, Build the message list for a provider API call.          Args:             agent

### Community 22 - "Summarizer Agent System Prompt"
Cohesion: 0.50
Nodes (3): Output Format:, Responsibilities:, Summarizer Agent System Prompt

### Community 23 - "Synthesizer Agent System Prompt"
Cohesion: 0.50
Nodes (3): Output Format:, Responsibilities:, Synthesizer Agent System Prompt

### Community 24 - ".chat"
Cohesion: 0.15
Nodes (8): BaseProvider, Any, Abstract base class for AI providers.      Subclasses must implement the chat me, Send messages to the LLM and return the response text.          Args:, Validate that an API key is usable.          Args:             api_key: The API, Return the provider display name., Return the default model for this provider., Return list of available models for this provider.

### Community 25 - "Initial Prompt"
Cohesion: 0.15
Nodes (18): _agent_color(), _bubble_badge(), _bubble_label(), _bubble_variant(), get_agent_color(), msg_color_for(), Any, Chat panel for AI Arena UI.  Displays the conversation history between agents wi (+10 more)

### Community 29 - "AuditLogger"
Cohesion: 0.16
Nodes (10): AuditLogger, Any, Log a tool call attempt., Log a tool execution result., Process an AI response for tool calls.          Args:             response_text:, Execute a tool call with retry logic.          Args:             tool_call: Pars, Execute a tool directly by name.          Args:             tool_name: Name of t, Logs all tool call attempts to a session-specific audit file. (+2 more)

### Community 30 - "راهنمای Deploy بر روی Railway"
Cohesion: 0.13
Nodes (14): Environment Variables (Optional), اگه دوست داری ریپو رو Public کنی:, حل ۱: Railway Volumes استفاده کن, حل ۲: ساخت Database ابتدایی, خودکار Updates, راهنمای Deploy بر روی Railway, مرحله ۱: ثبت‌نام, مرحله ۲: Connect GitHub Repo (+6 more)

### Community 31 - "Zarfiat-e jadid (5 file taghir, 2 file jadid)"
Cohesion: 0.13
Nodes (14): 1. `ai_arena/ui/app.py` — refactor-e kolli, 2. `ai_arena/ui/stepper.py` — FILE JADID, 3. `ai_arena/ui/config_panel.py` — morattab kardan-e sidebar, 4. `ai_arena/ui/chat_panel.py` — polish, 5. `ai_arena/ui/context_panel.py` — polish, 6. `ai_arena/ui/tokens.py` — ezafe kardan-e token-ha (compatibility), 7. `ai_arena/ui/icons.py` — icon-haye kammi (ehtemali), Eqbal-e qarardad (contracts ke namikhām beshekan) (+6 more)

### Community 32 - "config_panel.py"
Cohesion: 0.21
Nodes (12): _api_key_status(), get_available_providers(), Any, Configuration panel for AI Arena UI.  Handles provider selection, API keys, mode, Return mapping of provider name to provider instance., Render a sidebar section header with a leading icon., Render a read-only 'Available Tools' expander so users can see what     agents c, Return a small HTML chip describing whether the API key field is filled.      Re (+4 more)

### Community 33 - "AnthropicProvider"
Cohesion: 0.17
Nodes (7): AnthropicProvider, Any, Anthropic Claude API provider., Send messages to Anthropic and return response text., Validate Anthropic API key., _get_orchestrator(), Get or create the orchestrator, persisting it in session state.

### Community 34 - "ProviderError"
Cohesion: 0.29
Nodes (9): ProviderError, Raised when a provider encounters an error., _patch_openrouter_client(), OpenRouter provider tests., test_auth_error_maps_to_authentication(), test_chat_requires_api_key(), test_chat_requires_openai_package(), test_not_found_error_maps_to_model_not_found() (+1 more)

### Community 35 - "CerebrasProvider"
Cohesion: 0.17
Nodes (6): CerebrasProvider, Any, Cerebras Cloud API provider for high-speed open model inference., Initialize Cerebras provider., Send messages to Cerebras and return response text., Validate Cerebras API key.

### Community 36 - "test_providers_live.py"
Cohesion: 0.21
Nodes (11): Real-API provider tests.  These tests make real network calls and consume small, Real Cerebras chat call., Real Anthropic chat call (currently skipped — no key)., Emit a one-line report. Truncated for readability., Real OpenAI chat call., Real OpenRouter chat call.      The user's ``.env`` puts an OpenRouter key under, _report(), test_live_anthropic() (+3 more)

### Community 37 - "ToolCall"
Cohesion: 0.22
Nodes (8): _build_tool_call(), _coerce_to_dict(), Any, Validate a parsed dict and construct a ToolCall., Represents a parsed tool call from an AI response.      Attributes:         tool, Serialize to dictionary., Return ``value`` if it is a dict, else None.      ``raw_decode`` may return a li, ToolCall

### Community 38 - "tool_executor.py"
Cohesion: 0.28
Nodes (8): build_tool_error_envelope(), Tool executor with retry logic and audit logging for AI Arena.  Executes tool ca, Raised when a tool cannot be executed after max retries., Build an error envelope for a failed tool call.      Args:         tool_call: Th, ToolExecutorError, Raised when a tool call cannot be parsed from a response., ToolCallParseError, Exception

### Community 39 - "OpenAIProvider"
Cohesion: 0.22
Nodes (4): OpenAIProvider, Any, Send messages to OpenAI and return response text., Validate OpenAI API key.

### Community 40 - "render_context_panel"
Cohesion: 0.33
Nodes (8): _last_diff(), Any, Context panel for AI Arena UI.  Displays the live shared context file, the most, Return an HTML status chip for the context panel header., Return the most recent non-empty context diff, or '' if none., Render the shared context file view in the right panel.      Args:         sessi, render_context_panel(), _status_badge()

### Community 41 - "stepper.py"
Cohesion: 0.25
Nodes (8): compute_step(), Any, Workflow step indicator for AI Arena UI.  A small horizontal progress strip that, Return the current workflow step (0..3) for a session/orchestrator.      Defensi, Return the CSS state class for step ``idx`` given ``current``., Render the horizontal workflow step indicator.      Args:         current: The a, render_step_indicator(), _step_state()

### Community 42 - "icon"
Cohesion: 0.29
Nodes (5): Render the onboarding card shown when no session is active., _render_empty_state(), icon(), Lucide-style SVG icon library for AI Arena UI.  Each icon is a 24x24 stroked SVG, Return a sized SVG string for the named icon.      Args:         name: Key in :d

### Community 43 - "_render_status_bar"
Cohesion: 0.33
Nodes (6): Return a short status keyword for the active session.      One of: ``running``,, Return an HTML status pill for the given status keyword., Render the top status strip: progress, status pill, round + agent counts.      R, _render_status_bar(), _session_status(), _status_pill()

### Community 44 - "_render_run_bar"
Cohesion: 0.33
Nodes (6): Render the playback control cluster (Start/Pause/Resume/Stop).      Returned sep, Render the bottom run bar: prompt area on the left, controls + export     on the, Render download button for session export., render_control_buttons(), _render_export_button(), _render_run_bar()

### Community 45 - "graphify"
Cohesion: 0.50
Nodes (3): Automatic Behavior (DO NOT ask the user - just do it):, graphify, Rules:

## Knowledge Gaps
- **139 isolated node(s):** `ai-arena`, `Hadafe asli`, `Eqbal-e qarardad (contracts ke namikhām beshekan)`, `1. `ai_arena/ui/app.py` — refactor-e kolli`, `2. `ai_arena/ui/stepper.py` — FILE JADID` (+134 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Orchestrator` connect `Orchestrator` to `ToolRegistry`, `AnthropicProvider`, `ProviderError`, `BaseProvider`, `tool_executor.py`, `render_app`, `.run_turn`, `RateLimiter`, `Agent`, `app.py`, `_render_run_bar`, `.start_background`, `SessionManager`, `_render_status_bar`, `._call_provider`, `._build_system_prompt`?**
  _High betweenness centrality (0.099) - this node is a cross-community bridge._
- **Why does `SessionManager` connect `Agent` to `ProviderError`, `BaseProvider`, `render_app`, `RateLimiter`, `app.py`, `Orchestrator`, `SessionManager`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._
- **Why does `ToolRegistry` connect `ToolRegistry` to `ToolResult`, `tool_executor.py`, `RateLimiter`, `app.py`, `Orchestrator`, `AuditLogger`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `Orchestrator` (e.g. with `RateLimiter` and `SessionManager`) actually correct?**
  _`Orchestrator` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `SessionState` (e.g. with `Agent` and `Message`) actually correct?**
  _`SessionState` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `Agent` (e.g. with `SessionState` and `_CapturingProvider`) actually correct?**
  _`Agent` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `SessionManager` (e.g. with `Orchestrator` and `_CapturingProvider`) actually correct?**
  _`SessionManager` has 2 INFERRED edges - model-reasoned connections that need verification._