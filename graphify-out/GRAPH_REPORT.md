# Graph Report - ai-arena  (2026-07-19)

## Corpus Check
- 60 files · ~29,852 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 725 nodes · 1327 edges · 47 communities (40 shown, 7 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 65 edges (avg confidence: 0.53)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e4b38a0f`
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
- [[_COMMUNITY_._deserialize|._deserialize]]
- [[_COMMUNITY_config_panel.py|config_panel.py]]
- [[_COMMUNITY_AnthropicProvider|AnthropicProvider]]
- [[_COMMUNITY_.create_session|.create_session]]
- [[_COMMUNITY_CerebrasProvider|CerebrasProvider]]
- [[_COMMUNITY_test_providers_live.py|test_providers_live.py]]
- [[_COMMUNITY_MockProvider|MockProvider]]
- [[_COMMUNITY_tool_executor.py|tool_executor.py]]
- [[_COMMUNITY_._save_session|._save_session]]
- [[_COMMUNITY_render_context_panel|render_context_panel]]
- [[_COMMUNITY_extract_icons.py|extract_icons.py]]
- [[_COMMUNITY_.get_session|.get_session]]
- [[_COMMUNITY__render_status_bar|_render_status_bar]]
- [[_COMMUNITY_.get_active_session|.get_active_session]]
- [[_COMMUNITY_graphify|graphify]]
- [[_COMMUNITY_.start_background|.start_background]]

## God Nodes (most connected - your core abstractions)
1. `Orchestrator` - 55 edges
2. `Agent` - 42 edges
3. `SessionState` - 41 edges
4. `SessionManager` - 36 edges
5. `ProviderError` - 27 edges
6. `ToolResult` - 26 edges
7. `ToolRegistry` - 25 edges
8. `BaseProvider` - 22 edges
9. `OpenRouterProvider` - 22 edges
10. `parse_tool_call()` - 21 edges

## Surprising Connections (you probably didn't know these)
- `_CapturingProvider` --uses--> `Orchestrator`  [INFERRED]
  tests/test_fixes.py → ai_arena/engine/orchestrator.py
- `_make_orch()` --indirect_call--> `Orchestrator`  [INFERRED]
  tests/test_one_shot_flow.py → ai_arena/engine/orchestrator.py
- `_NoToolRegistry` --uses--> `Orchestrator`  [INFERRED]
  tests/test_one_shot_flow.py → ai_arena/engine/orchestrator.py
- `_CapturingProvider` --uses--> `RateLimiter`  [INFERRED]
  tests/test_fixes.py → ai_arena/engine/rate_limiter.py
- `_NoToolRegistry` --uses--> `SessionManager`  [INFERRED]
  tests/test_one_shot_flow.py → ai_arena/engine/session.py

## Import Cycles
- None detected.

## Communities (47 total, 7 thin omitted)

### Community 0 - "ToolRegistry"
Cohesion: 0.15
Nodes (15): Session manager for multi-session support., AgentRole, Agent model representing an AI agent in the orchestration loop., AI Arena models package., Message, Message model for conversation history., Represents a single message in the conversation history.      Attributes:, Serialize message to dictionary. (+7 more)

### Community 1 - "ToolResult"
Cohesion: 0.08
Nodes (36): ABC, Tool registry for AI Arena.  Single source of truth for all available tools. Add, Register the default file manipulation tools., Register a tool by its name.          Args:             tool: Tool instance to r, BaseTool, Any, Base tool abstraction and result types., Raised when a tool execution fails. (+28 more)

### Community 2 - "ProviderError"
Cohesion: 0.11
Nodes (17): ProviderError, Raised when a provider encounters an error., OpenRouterProvider, Any, Validate OpenRouter API key., OpenRouter API provider supporting free and paid models., Initialize OpenRouter provider., Send messages to OpenRouter and return response text. (+9 more)

### Community 3 - "How to Add a New Provider"
Cohesion: 0.05
Nodes (39): Advanced: Programmatic Agent Creation, Agent Configuration Fields, Agent Roles, Agent Turn Order, Example: Adding a Researcher Agent, How to Add a New Agent, Quick Start, BaseProvider Interface (+31 more)

### Community 4 - "Configuration Guide"
Cohesion: 0.10
Nodes (21): Agent Configuration, API Key, API Keys, Configuration Guide, Creating Custom Prompts, Creating Sessions, Deleting Sessions, Dry-run Mode (+13 more)

### Community 5 - "BaseProvider"
Cohesion: 0.18
Nodes (6): OpenAIProvider, Any, Send messages to OpenAI and return response text., Validate OpenAI API key., get_available_providers(), Return mapping of provider name to provider instance.

### Community 6 - "Tool System Documentation"
Cohesion: 0.10
Nodes (20): append_file, Architecture Overview, Audit Logging, Available Tools, Creating Custom Tools, Format Specification, Key Components, Middleware Flow (+12 more)

### Community 7 - "render_app"
Cohesion: 0.18
Nodes (9): Lucide-style SVG icon library for AI Arena UI.  Each icon is a 24x24 stroked S, compute_step(), Any, Workflow step indicator for AI Arena UI.  A small horizontal progress strip that, Return the current workflow step (0..3) for a session/orchestrator.      Defensi, Return the CSS state class for step ``idx`` given ``current``., Render the horizontal workflow step indicator.      Args:         current: The a, render_step_indicator() (+1 more)

### Community 8 - ".run_turn"
Cohesion: 0.23
Nodes (17): Agent, Represents a configurable AI agent.      Attributes:         id: Unique identifi, Serialize agent to dictionary., _make_orch(), _make_session(), _NoToolRegistry, Smoke tests for the "one-shot per turn" orchestrator refactor.  Covers: 1. _buil, _process_tool_calls must NOT re-call the provider. It returns     after exactly (+9 more)

### Community 9 - "RateLimiter"
Cohesion: 0.18
Nodes (7): Initialize orchestrator.          Args:             session_manager: Session, RateLimiter, Thread-safe rate limiter enforcing a minimum delay between calls.      Uses a si, Initialize rate limiter.          Args:             delay_seconds: Minimum secon, Block until the rate limit allows a call.          Returns:             The actu, Reset the rate limiter, allowing an immediate call., test_rate_limiter_preserves_last_call()

### Community 11 - "Agent"
Cohesion: 0.22
Nodes (12): Manages multiple named orchestration sessions.      Sessions are persisted to di, SessionManager, _CapturingProvider, Path, Regression tests for the 2026-07-15 review fixes.  Covers: - P0-1: SessionManage, OpenAIProvider subclass that records the kwargs it was called with,     so we ca, test_orchestrator_forwards_max_tokens(), test_parser_json_fence_with_nested_args() (+4 more)

### Community 12 - "app.py"
Cohesion: 0.14
Nodes (16): _consume_loop_error(), _get_session_manager(), _init_session_state(), _maybe_autorefresh(), Main Streamlit application for AI Arena.  Layout (responsive, collapses gracef, Render the onboarding card shown when no session is active., If a session is running, schedule a rerun every 2s to refresh the UI.      The, Main entry point for the Streamlit application. (+8 more)

### Community 13 - "Orchestrator"
Cohesion: 0.09
Nodes (15): Orchestrator, Get a registered provider by name., Return list of registered provider names., Call the provider API for the given agent.          Args:             agent:, Generate a simulated response for dry-run mode.          Args:             ag, Append agent response to context file content.          Args:             con, Main orchestration engine acting as middleware between AI agents.      The mid, Execute a single agent turn with full middleware logic.          The middlewar (+7 more)

### Community 14 - "AppConfig"
Cohesion: 0.18
Nodes (8): AppConfig, Path, Global application configuration.      Attributes:         app_name: Application, Ensure directories exist., Return mapping of prompt name to file path., Load a system prompt by name (stem).          Args:             name: Prompt nam, Return the context file path for a given session., Return the API key for a provider from environment variables.          Looks up

### Community 15 - "SessionManager"
Cohesion: 0.11
Nodes (12): Start the orchestration loop for a session.          Args:             sessio, Stop the orchestration loop., Pause the orchestration loop., Resume a paused session., Spawn the orchestration loop in a daemon thread.          Returns the thread h, Represents the full state of an orchestration session.      Attributes:, Return only enabled agents in order., Return the currently active agent. (+4 more)

### Community 16 - ".create_session"
Cohesion: 0.07
Nodes (29): 10. No `prefers-reduced-motion` support ✅ **FIXED**, 11. Three equal columns break on mobile ✅ **IMPROVED**, 12. No download/copy for the context file ✅ **FIXED**, 13. Chat badge readability ✅ **FIXED**, 14. Touch targets too small ✅ **FIXED**, 1. `hash()` bug — agent color changes on every rerun ✅ **FIXED**, 2. Redundant H1 — two titles for the same thing ✅ **FIXED**, 3. Export writes to disk instead of offering a browser download ✅ **FIXED** (+21 more)

### Community 17 - "._call_provider"
Cohesion: 0.12
Nodes (15): `ai_arena/engine/orchestrator.py`, Changes, Design rules, Execution order, File format (after `start_session`), Files not touched, Files touched, Goal (+7 more)

### Community 18 - ".get"
Cohesion: 0.10
Nodes (19): AI Arena — Review & Fix Plan (2026-07-15), Out of scope (acknowledged but deferred), P0-1. SessionManager never reloads from disk, P0-2. Tool parser regex rejects nested JSON, P0-3. Background thread writes to st.session_state (race), P0-4. `start_session` resets RateLimiter state, P0 — Critical Bugs (must fix), P1-5. Audit log silently swallows IO errors (+11 more)

### Community 19 - "Critic Agent System Prompt"
Cohesion: 0.25
Nodes (7): Critic — System Prompt, File format you can rely on, Mandatory workflow, Rules, Runtime context, Tool call format, Working-draft template (replace with your critique)

### Community 20 - "Optimist/Innovator Agent System Prompt"
Cohesion: 0.25
Nodes (7): File format you can rely on, Mandatory workflow, Optimist — System Prompt, Rules, Runtime context, Tool call format, Working-draft template (replace with your synthesis)

### Community 21 - "._build_system_prompt"
Cohesion: 0.20
Nodes (5): Get the auto-generated tool manual for prompt injection.          Returns:, Build the system prompt for an agent.          Args:             agent: The a, Build the message list for a provider API call.          The model sees ONLY t, Read the current shared context file.          Args:             session: Cur, Update the shared context file with new content.          Args:             s

### Community 22 - "Summarizer Agent System Prompt"
Cohesion: 0.25
Nodes (7): File format you can rely on, Mandatory workflow, Rules, Runtime context, Summarizer — System Prompt, Tool call format, Working-draft template (replace with the snapshot)

### Community 23 - "Synthesizer Agent System Prompt"
Cohesion: 0.25
Nodes (7): File format you can rely on, Mandatory workflow, Rules, Runtime context, Synthesizer — System Prompt, Tool call format, Working-draft template (replace with the final synthesis)

### Community 24 - ".chat"
Cohesion: 0.13
Nodes (9): Register a provider by name., BaseProvider, Any, Abstract base class for AI providers.      Subclasses must implement the chat me, Send messages to the LLM and return the response text.          Args:, Validate that an API key is usable.          Args:             api_key: The API, Return the provider display name., Return the default model for this provider. (+1 more)

### Community 25 - "Initial Prompt"
Cohesion: 0.15
Nodes (18): _agent_color(), _bubble_badge(), _bubble_label(), _bubble_variant(), get_agent_color(), msg_color_for(), Any, Chat panel for AI Arena UI.  Displays the conversation history between agents wi (+10 more)

### Community 29 - "AuditLogger"
Cohesion: 0.05
Nodes (61): Configuration management for AI Arena.  Supports loading from environment variab, Engine package for AI Arena., Core orchestration engine for AI Arena.  The Orchestrator acts as middleware b, Rate limiter for enforcing delays between API calls., AuditLogger, build_tool_error_envelope(), build_tool_result_envelope(), Any (+53 more)

### Community 30 - "راهنمای Deploy بر روی Railway"
Cohesion: 0.13
Nodes (14): Environment Variables (Optional), اگه دوست داری ریپو رو Public کنی:, حل ۱: Railway Volumes استفاده کن, حل ۲: ساخت Database ابتدایی, خودکار Updates, راهنمای Deploy بر روی Railway, مرحله ۱: ثبت‌نام, مرحله ۲: Connect GitHub Repo (+6 more)

### Community 31 - "._deserialize"
Cohesion: 0.20
Nodes (7): Any, Rebuild a Message from a dict, tolerating missing optional fields., Parse an ISO-8601 timestamp string, falling back to ``now``., List all sessions with metadata., Build a SessionState from a persisted dict.          Returns None if the dict is, Create agent from dictionary., test_agent_max_tokens_round_trip()

### Community 32 - "config_panel.py"
Cohesion: 0.19
Nodes (13): _api_key_status(), _provider_key_prefix_warning(), Any, Render the configuration panel in the Streamlit sidebar.      Returns:         D, Render a sidebar section header with a leading icon., Render a read-only 'Available Tools' expander so users can see what     agents c, Return a small HTML chip describing whether the API key field is filled.      Re, Return a small warning chip if the API key prefix doesn't match the     selected (+5 more)

### Community 33 - "AnthropicProvider"
Cohesion: 0.17
Nodes (7): AnthropicProvider, Any, Anthropic Claude API provider., Send messages to Anthropic and return response text., Validate Anthropic API key., _get_orchestrator(), Get or create the orchestrator, persisting it in session state.

### Community 34 - ".create_session"
Cohesion: 0.15
Nodes (8): Path, Create a new session.          Args:             name: Human-readable session na, Delete a session and its context file.          Returns:             True if del, Persist session state to disk atomically.          Writes to ``session_<id>.json, Initialize session manager.          Args:             storage_dir: Directory fo, Return (and lazily create) a per-session lock for atomic writes., Load every ``session_*.json`` file under ``storage_dir`` into memory.          T, Lock

### Community 35 - "CerebrasProvider"
Cohesion: 0.17
Nodes (6): CerebrasProvider, Any, Cerebras Cloud API provider for high-speed open model inference., Initialize Cerebras provider., Send messages to Cerebras and return response text., Validate Cerebras API key.

### Community 36 - "test_providers_live.py"
Cohesion: 0.21
Nodes (11): Real-API provider tests.  These tests make real network calls and consume small, Real Cerebras chat call., Real Anthropic chat call (currently skipped — no key)., Emit a one-line report. Truncated for readability., Real OpenAI chat call., Real OpenRouter chat call.      The user's ``.env`` puts an OpenRouter key under, _report(), test_live_anthropic() (+3 more)

### Community 37 - "MockProvider"
Cohesion: 0.23
Nodes (7): Anthropic provider implementation., Base provider abstraction for AI Arena., Cerebras provider implementation.  Cerebras Cloud provides high-speed inferenc, Providers package for AI Arena., OpenAI provider implementation., OpenRouter provider implementation.  OpenRouter provides access to many free mod, Configuration panel for AI Arena UI.  Handles provider selection, API keys, mode

### Community 38 - "tool_executor.py"
Cohesion: 0.33
Nodes (6): Render the playback control cluster (Start/Pause/Resume/Stop).      Returned s, Render the bottom run bar: prompt area on the left, controls + export     on th, Render download button for session export., render_control_buttons(), _render_export_button(), _render_run_bar()

### Community 39 - "._save_session"
Cohesion: 0.33
Nodes (8): _last_diff(), Any, Context panel for AI Arena UI.  Displays the live shared context file, the mos, Return an HTML status chip for the context panel header., Return the most recent non-empty context diff, or '' if none., Render the shared context file view in the right panel.      Args:         se, render_context_panel(), _status_badge()

### Community 40 - "render_context_panel"
Cohesion: 0.25
Nodes (7): Agent-1 (Round 1), Agent-1 (Round 1), Agent-1 (Round 2), Agent-1 (Round 2), Agent-2 (Round 1), Agent-2 (Round 1), Agent-2 (Round 2)

### Community 41 - "extract_icons.py"
Cohesion: 0.25
Nodes (7): 1. Fix auto-refresh fallback — `ai_arena/ui/app.py:350-355`, 2. Lower default rate limit — two files, 3. Install missing dependency, Changes, Files Modified, Fix: Run loop stuck at "Round 1 / 10", Root Causes

### Community 43 - "_render_status_bar"
Cohesion: 0.33
Nodes (6): Return a short status keyword for the active session.      One of: ``running``, Return an HTML status pill for the given status keyword., Render the top status strip: progress, status pill, round + agent counts., _render_status_bar(), _session_status(), _status_pill()

### Community 45 - "graphify"
Cohesion: 0.50
Nodes (3): Automatic Behavior (DO NOT ask the user - just do it):, graphify, Rules:

## Knowledge Gaps
- **166 isolated node(s):** `ai-arena`, `Root Causes`, `1. Fix auto-refresh fallback — `ai_arena/ui/app.py:350-355``, `2. Lower default rate limit — two files`, `3. Install missing dependency` (+161 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Orchestrator` connect `Orchestrator` to `ToolRegistry`, `AnthropicProvider`, `ProviderError`, `tool_executor.py`, `.run_turn`, `RateLimiter`, `SessionState`, `Agent`, `app.py`, `_render_status_bar`, `SessionManager`, `._build_system_prompt`, `.chat`, `AuditLogger`?**
  _High betweenness centrality (0.090) - this node is a cross-community bridge._
- **Why does `SessionManager` connect `Agent` to `ToolRegistry`, `.create_session`, `ProviderError`, `.run_turn`, `RateLimiter`, `.get_session`, `SessionState`, `.get_active_session`, `Orchestrator`, `.start_background`, `app.py`, `AuditLogger`, `._deserialize`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._
- **Why does `SessionState` connect `SessionManager` to `ToolRegistry`, `.create_session`, `tool_executor.py`, `.run_turn`, `.get_session`, `_render_status_bar`, `.get_active_session`, `Orchestrator`, `app.py`, `._build_system_prompt`, `AuditLogger`, `._deserialize`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `Orchestrator` (e.g. with `RateLimiter` and `SessionManager`) actually correct?**
  _`Orchestrator` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `Agent` (e.g. with `SessionState` and `_CapturingProvider`) actually correct?**
  _`Agent` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `SessionState` (e.g. with `Agent` and `Message`) actually correct?**
  _`SessionState` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `SessionManager` (e.g. with `Orchestrator` and `_CapturingProvider`) actually correct?**
  _`SessionManager` has 3 INFERRED edges - model-reasoned connections that need verification._