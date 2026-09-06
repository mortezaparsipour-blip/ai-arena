# Graph Report - ai-arena  (2026-09-06)

## Corpus Check
- 64 files · ~39,391 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 827 nodes · 1777 edges · 55 communities (52 shown, 3 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 248 edges (avg confidence: 0.51)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `485c348a`
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
- [[_COMMUNITY__AlwaysFail|_AlwaysFail]]
- [[_COMMUNITY__AlwaysProse|_AlwaysProse]]
- [[_COMMUNITY_._call_provider|._call_provider]]
- [[_COMMUNITY_.get|.get]]
- [[_COMMUNITY_.advance|.advance]]
- [[_COMMUNITY__make_session|_make_session]]
- [[_COMMUNITY_.execute|.execute]]
- [[_COMMUNITY_.resume_session|.resume_session]]

## God Nodes (most connected - your core abstractions)
1. `Orchestrator` - 82 edges
2. `Agent` - 72 edges
3. `SessionState` - 65 edges
4. `SessionManager` - 63 edges
5. `ToolRegistry` - 43 edges
6. `ProviderError` - 43 edges
7. `BaseProvider` - 37 edges
8. `Message` - 36 edges
9. `ReadFileTool` - 29 edges
10. `WriteFileTool` - 29 edges

## Surprising Connections (you probably didn't know these)
- `_CapturingProvider` --uses--> `Orchestrator`  [INFERRED]
  tests/test_fixes.py → ai_arena/engine/orchestrator.py
- `test_orchestrator_thread_safe_accessors()` --calls--> `Orchestrator`  [EXTRACTED]
  tests/test_fixes.py → ai_arena/engine/orchestrator.py
- `_make_orch()` --indirect_call--> `Orchestrator`  [INFERRED]
  tests/test_one_shot_flow.py → ai_arena/engine/orchestrator.py
- `_NoToolRegistry` --uses--> `Orchestrator`  [INFERRED]
  tests/test_one_shot_flow.py → ai_arena/engine/orchestrator.py
- `_AlwaysFail` --uses--> `Orchestrator`  [INFERRED]
  tests/test_regression_v2.py → ai_arena/engine/orchestrator.py

## Import Cycles
- None detected.

## Communities (55 total, 3 thin omitted)

### Community 0 - "ToolRegistry"
Cohesion: 0.14
Nodes (18): Session manager for multi-session support., AgentRole, Agent model representing an AI agent in the orchestration loop., AI Arena models package., Message, Message model for conversation history., Represents a single message in the conversation history.      Attributes:, Serialize message to dictionary. (+10 more)

### Community 1 - "ToolResult"
Cohesion: 0.13
Nodes (9): OpenRouterProvider, Any, Validate OpenRouter API key., OpenRouter API provider supporting free and paid models., Initialize OpenRouter provider., Send messages to OpenRouter and return response text., provider(), Path (+1 more)

### Community 2 - "ProviderError"
Cohesion: 0.29
Nodes (9): ProviderError, Raised when a provider encounters an error., _patch_openrouter_client(), OpenRouter provider tests., test_auth_error_maps_to_authentication(), test_chat_requires_api_key(), test_chat_requires_openai_package(), test_not_found_error_maps_to_model_not_found() (+1 more)

### Community 3 - "How to Add a New Provider"
Cohesion: 0.05
Nodes (40): Advanced: Programmatic Agent Creation, Agent Configuration Fields, Agent Roles, Agent Turn Order, Example: Adding a Researcher Agent, How to Add a New Agent, Quick Start, BaseProvider Interface (+32 more)

### Community 4 - "Configuration Guide"
Cohesion: 0.10
Nodes (21): Agent Configuration, API Key, API Keys, Configuration Guide, Creating Custom Prompts, Creating Sessions, Deleting Sessions, Dry-run Mode (+13 more)

### Community 5 - "BaseProvider"
Cohesion: 0.22
Nodes (11): build_tool_error_envelope(), build_tool_result_envelope(), Tool executor with audit logging for AI Arena.  Executes tool calls — exactly, Wrap a tool result in a labeled envelope for the message log.      Args:, Build an error envelope for a failed tool call.      In the one-shot flow the, Path, Test middleware components., A failed tool call is executed exactly ONCE (no retry of identical     argument (+3 more)

### Community 6 - "Tool System Documentation"
Cohesion: 0.10
Nodes (20): append_file, Architecture Overview, Audit Logging, Available Tools, Creating Custom Tools, Failure Handling, Format Specification, Key Components (+12 more)

### Community 7 - "render_app"
Cohesion: 0.18
Nodes (9): Lucide-style SVG icon library for AI Arena UI.  Each icon is a 24x24 stroked S, compute_step(), Any, Workflow step indicator for AI Arena UI.  A small horizontal progress strip that, Return the current workflow step (0..3) for a session/orchestrator.      Defensi, Return the CSS state class for step ``idx`` given ``current``., Render the horizontal workflow step indicator.      Args:         current: The a, render_step_indicator() (+1 more)

### Community 8 - ".run_turn"
Cohesion: 0.24
Nodes (16): _make_orch(), _make_session(), _NoToolRegistry, Smoke tests for the "one-shot per turn" orchestrator refactor.  Covers: 1. _buil, _process_tool_calls must NOT re-call the provider. It returns     after exactly, When the agent already called write_file, run_turn must NOT     call _append_age, P0 regression: after a tool-call turn, step() must ADVANCE to the     next agent, The user message must contain the file content as a fenced block —     that's ho (+8 more)

### Community 9 - "RateLimiter"
Cohesion: 0.18
Nodes (6): OpenAIProvider, Any, Send messages to OpenAI and return response text., Validate OpenAI API key., _get_orchestrator(), Get or create the orchestrator, persisting it in session state.

### Community 10 - "SessionState"
Cohesion: 0.16
Nodes (10): Agent, Represents a configurable AI agent.      Attributes:         id: Unique identifi, Serialize agent to dictionary., Create agent from dictionary., Return only enabled agents in order., Return the currently active agent., Advance to the next agent, cycling through rounds.          Returns:, test_agent_max_tokens_round_trip() (+2 more)

### Community 11 - "Agent"
Cohesion: 0.12
Nodes (15): Retrieve a session by ID., Return the currently active session., Set the active session by ID.          Returns:             True if session exis, Manages multiple named orchestration sessions.      Sessions are persisted to di, SessionManager, Test a complete middleware flow with tool calls., test_full_middleware_flow(), _CapturingProvider (+7 more)

### Community 12 - "app.py"
Cohesion: 0.13
Nodes (18): _consume_loop_error(), _get_session_manager(), _init_session_state(), _maybe_autorefresh(), Main Streamlit application for AI Arena.  Layout (responsive, collapses gracef, Render the onboarding card shown when no session is active., If a session is running, schedule a rerun every 2s to refresh the UI.      The, Main entry point for the Streamlit application. (+10 more)

### Community 13 - "Orchestrator"
Cohesion: 0.10
Nodes (11): Orchestrator, Return list of registered provider names., Get the auto-generated tool manual for prompt injection.          Returns:, Main orchestration engine acting as middleware between AI agents.      One sho, Stop the orchestration loop., Pause the orchestration loop., Resume a paused session., Return whether the background loop is currently executing. (+3 more)

### Community 14 - "AppConfig"
Cohesion: 0.16
Nodes (9): AppConfig, Path, Return the context file path for a given session., Return the API key for a provider from environment variables.          Looks up, Return whether ``path`` must never be exposed to agents via read_file., Global application configuration.      Attributes:         app_name: Application, Ensure directories exist., Return mapping of prompt name to file path. (+1 more)

### Community 15 - "SessionManager"
Cohesion: 0.09
Nodes (15): Build the system prompt for an agent.          Args:             agent: The a, Build the message list for a provider API call.          The model sees ONLY t, Call the provider API for the given agent.          Args:             agent:, Generate a simulated response for dry-run mode.          Args:             ag, Read the current shared context file.          Args:             session: Cur, Execute a single agent turn with full middleware logic.          One shot per, Process AT MOST ONE tool call in an agent's response, then         return. The, Execute a single step (one agent turn).          Args:             session: C (+7 more)

### Community 16 - ".create_session"
Cohesion: 0.33
Nodes (8): _last_diff(), Any, Context panel for AI Arena UI.  Displays the live shared context file, the mos, Return an HTML status chip for the context panel header.      Delegates to ``u, Return the most recent non-empty context diff, or '' if none., Render the shared context file view in the right panel.      Args:         se, render_context_panel(), _status_badge()

### Community 17 - "._call_provider"
Cohesion: 0.12
Nodes (15): Changed, Changelog, Fixed (15 bugs), Fixed (P0 + security + 20 findings from the full code review in `docs/glm5.3-flash final/`), HIGH, HIGH, LOW, LOW (+7 more)

### Community 18 - ".get"
Cohesion: 0.13
Nodes (15): 02 — گزارش باگ‌ها (Bug Report), Importهای بلااستفاده (ruff F401 آنها را می‌گیرد), P0-1 · بعد از tool-call، حلقه به ایجنت بعدی advance نمی‌کند (خطر حلقه‌ی بی‌نهایت و دوبرابر شدن هزینه), P1-1 · وضعیت «Running» شبح‌وار هنگام switch session با حلقه‌ی زنده, P1-2 · docstring `_save_session` با پیاده‌سازی تناقض دارد (نوشتن غیراتمی), P1-3 · اولویت fallback کلید OpenRouter برعکس, P1-4 · مسیر retry envelope در orchestrator مرده است (dead path), P2-1 · `streamlit-autorefresh` در pyproject اعلام نشده + docstring از fallback دروغ می‌گوید (+7 more)

### Community 19 - "Critic Agent System Prompt"
Cohesion: 0.25
Nodes (7): Critic — System Prompt, File format you can rely on, Mandatory workflow, Rules, Runtime context, Tool call format, Working-draft template (replace with your critique)

### Community 20 - "Optimist/Innovator Agent System Prompt"
Cohesion: 0.25
Nodes (7): File format you can rely on, Mandatory workflow, Optimist — System Prompt, Rules, Runtime context, Tool call format, Working-draft template (replace with your synthesis)

### Community 21 - "._build_system_prompt"
Cohesion: 0.18
Nodes (7): Initialize orchestrator.          Args:             session_manager: Session, RateLimiter, Thread-safe rate limiter enforcing a minimum delay between calls.      Uses a la, Initialize rate limiter.          Args:             delay_seconds: Minimum secon, Block until the rate limit allows a call.          Returns:             The dela, Reset the rate limiter, allowing an immediate call., test_rate_limiter_preserves_last_call()

### Community 22 - "Summarizer Agent System Prompt"
Cohesion: 0.25
Nodes (7): File format you can rely on, Mandatory workflow, Rules, Runtime context, Summarizer — System Prompt, Tool call format, Working-draft template (replace with the snapshot)

### Community 23 - "Synthesizer Agent System Prompt"
Cohesion: 0.25
Nodes (7): File format you can rely on, Mandatory workflow, Rules, Runtime context, Synthesizer — System Prompt, Tool call format, Working-draft template (replace with the final synthesis)

### Community 24 - ".chat"
Cohesion: 0.23
Nodes (7): Anthropic provider implementation., Base provider abstraction for AI Arena., Cerebras provider implementation.  Cerebras Cloud provides high-speed inferenc, Providers package for AI Arena., OpenAI provider implementation., OpenRouter provider implementation.  OpenRouter provides access to many free mod, Configuration panel for AI Arena UI.  Handles provider selection, API keys, mode

### Community 25 - "Initial Prompt"
Cohesion: 0.15
Nodes (18): _agent_color(), _bubble_badge(), _bubble_label(), _bubble_variant(), get_agent_color(), msg_color_for(), Any, Chat panel for AI Arena UI.  Displays the conversation history between agents wi (+10 more)

### Community 26 - "AGENTS.md"
Cohesion: 0.18
Nodes (8): Executes tool calls — one attempt each — with audit logging.      The executor, Execute a tool call exactly once, without retrying.          Tool operations a, Execute a tool directly by name.          Args:             tool_name: Name o, ToolExecutor, Path, A failing tool call is executed once and yields an error envelope., test_tool_failure_single_attempt(), Quick smoke test of middleware components (runs at import time).  Kept as a fa

### Community 29 - "AuditLogger"
Cohesion: 0.13
Nodes (20): Engine package for AI Arena., Core orchestration engine for AI Arena.  The Orchestrator acts as middleware b, Rate limiter for enforcing delays between API calls., has_tool_call(), _iter_json_objects(), parse_tool_call(), Tool call parser for AI Arena.  Parses structured tool calls from AI responses,, Parse a JSON object string, with light-touch recovery for common LLM     issues (+12 more)

### Community 30 - "راهنمای Deploy بر روی Railway"
Cohesion: 0.13
Nodes (14): Environment Variables (Optional), اگه دوست داری ریپو رو Public کنی:, حل ۱: Railway Volumes استفاده کن, حل ۲: ساخت Database ابتدایی, خودکار Updates, راهنمای Deploy بر روی Railway, مرحله ۱: ثبت‌نام, مرحله ۲: Connect GitHub Repo (+6 more)

### Community 31 - "._deserialize"
Cohesion: 0.10
Nodes (13): Any, Path, Build a SessionState from a persisted dict.          Returns None if the dict is, Rebuild a Message from a dict, tolerating missing optional fields., Parse an ISO-8601 timestamp string, falling back to ``now``., Create a new session.          Args:             name: Human-readable session na, List all sessions with metadata., Delete a session and every file it owns.          Removes the session JSON, the (+5 more)

### Community 32 - "config_panel.py"
Cohesion: 0.19
Nodes (13): _api_key_status(), _provider_key_prefix_warning(), Any, Render the configuration panel in the Streamlit sidebar.      Returns:         D, Render a sidebar section header with a leading icon., Render a read-only 'Available Tools' expander so users can see what     agents c, Return a small HTML chip describing whether the API key field is filled.      Re, Return a small warning chip if the API key prefix doesn't match the     selected (+5 more)

### Community 33 - "AnthropicProvider"
Cohesion: 0.17
Nodes (7): AnthropicProvider, Any, Anthropic Claude API provider., Send messages to Anthropic and return response text., Validate Anthropic API key., get_available_providers(), Return mapping of provider name to provider instance.

### Community 34 - ".create_session"
Cohesion: 0.22
Nodes (8): _build_tool_call(), _coerce_to_dict(), Any, Validate a parsed dict and construct a ToolCall., Represents a parsed tool call from an AI response.      Attributes:         tool, Serialize to dictionary., Return ``value`` if it is a dict, else None.      ``raw_decode`` may return a li, ToolCall

### Community 35 - "CerebrasProvider"
Cohesion: 0.14
Nodes (11): CerebrasProvider, Any, Cerebras Cloud API provider for high-speed open model inference., Initialize Cerebras provider., Send messages to Cerebras and return response text., Validate Cerebras API key., build_agents(), main() (+3 more)

### Community 36 - "test_providers_live.py"
Cohesion: 0.18
Nodes (12): Configuration management for AI Arena.  Supports loading from environment variab, Real-API provider tests.  These tests make real network calls and consume small, Real Cerebras chat call., Real Anthropic chat call (currently skipped — no key)., Emit a one-line report. Truncated for readability., Real OpenAI chat call., Real OpenRouter chat call.      The user's ``.env`` puts an OpenRouter key under, _report() (+4 more)

### Community 37 - "MockProvider"
Cohesion: 0.17
Nodes (12): AuditLogger, Any, Initialize audit logger for a session.          Args:             session_id:, Append an audit log entry.          Args:             event: Event type (e.g., Log a tool call attempt (long argument values clipped)., Log a tool execution result (long output/error clipped)., Process an AI response for tool calls.          Args:             response_te, Return ``value`` clipped to ``MAX_AUDIT_ARG_CHARS`` when it is a long string. (+4 more)

### Community 38 - "tool_executor.py"
Cohesion: 0.25
Nodes (8): _build_export_content(), Render the playback control cluster (Start/Pause/Resume/Stop).      Returned s, Render the bottom run bar: prompt area on the left, controls + export     on th, Build the full Markdown export for a session., Render download button for session export.      The export body is memoized in, render_control_buttons(), _render_export_button(), _render_run_bar()

### Community 39 - "._save_session"
Cohesion: 0.05
Nodes (52): ABC, Tool registry for AI Arena.  Single source of truth for all available tools. Add, Register the default file manipulation tools., Register a tool by its name.          Args:             tool: Tool instance to r, BaseTool, Any, Base tool abstraction and result types., Raised when a tool execution fails. (+44 more)

### Community 40 - "render_context_panel"
Cohesion: 0.29
Nodes (6): _make_orch(), _make_session(), Any, Create a SessionState directly (no SessionManager overhead)., Build a minimal Orchestrator with no-op session manager., TestP1_1_ContextDiff

### Community 41 - "extract_icons.py"
Cohesion: 0.18
Nodes (11): 04 — معماری، کیفیت کد، تست‌ها و ممیزی مستندات, جریان داده (واقعیت فعلی کد، برای مرجع), شکاف‌های پوشش, نقاط ضعف ساختاری, نقاط قوت, وضعیت کلی: ۱۰ فایل، ~۱۹۰۰ خط، اجرای ترکیبی pytest + اسکریپت مستقیم, ۱) معماری, ۲) کیفیت کد (+3 more)

### Community 42 - ".get_session"
Cohesion: 0.25
Nodes (4): 01 — جمع‌بندی مدیریتی (Executive Summary), توصیه‌ی ترتیب اقدام, کارنامه ۰ تا ۱۰۰, ۱۰ یافته‌ی برتر (به ترتیب اولویت)

### Community 43 - "_render_status_bar"
Cohesion: 0.17
Nodes (14): Return a short status keyword for the active session.      Delegates to ``ui.s, Return an HTML status pill for the given status keyword., Render the top status strip: progress, status pill, round + agent counts., _render_status_bar(), _session_status(), _status_pill(), Any, Shared session-status helpers for the UI panels.  Single source of truth for sta (+6 more)

### Community 44 - ".get_active_session"
Cohesion: 0.50
Nodes (3): Path, Start the orchestration loop for a session.          Args:             sessio, Copy ``ctx_path`` to a ``.bak.md`` sibling if it holds real work.          "Re

### Community 45 - "graphify"
Cohesion: 0.50
Nodes (3): Automatic Behavior (DO NOT ask the user - just do it):, graphify, Rules:

### Community 46 - ".start_background"
Cohesion: 0.20
Nodes (5): Return the id of the session the background loop is executing., Raise if the background loop is busy with a *different* session.          Star, Spawn the orchestration loop in a daemon thread.          Returns the thread h, Return whether the background thread has been started and is alive., Thread

### Community 47 - "_AlwaysFail"
Cohesion: 0.29
Nodes (7): SEC-1 (بالا) — read_file هر راز داخل project root را می‌خواند, SEC-2 (بالا) — کلیدهای API به‌صورت plaintext روی دیسک, SEC-3 (متوسط) — Audit log خودش می‌تواند حساس شود, SEC-4 (متوسط) — هیچ سقف حجمی برای write_file, SEC-5 (پایین) — پیشوند کلید به‌عنوان «اعتبارسنجی», SEC-6 (پایین) — عدم جداسازی بین sessionها در سندباکس, یافته‌ها ⚠️

### Community 49 - "._call_provider"
Cohesion: 0.40
Nodes (5): compute_diff(), Compute a unified diff between two strings.      Lines are split without their, Test that context diffs are properly computed., test_context_diff_tracking(), test_compute_diff_clean_output()

### Community 50 - ".get"
Cohesion: 0.18
Nodes (8): Initialize tool executor.          Args:             registry: Tool registry, Central registry for all available agent tools.      Tools are registered once a, Retrieve a tool by name.          Args:             name: Tool name.          Re, Return all registered tools., Generate the tool usage manual for injection into system prompts.          Retur, ToolRegistry, Test that tool manual is properly generated and injected., test_tool_manual_injection()

### Community 51 - ".advance"
Cohesion: 0.12
Nodes (10): Register a provider by name., Get a registered provider by name., BaseProvider, Any, Abstract base class for AI providers.      Subclasses must implement the chat me, Send messages to the LLM and return the response text.          Args:, Validate that an API key is usable.          Args:             api_key: The API, Return the provider display name. (+2 more)

### Community 52 - "_make_session"
Cohesion: 0.40
Nodes (4): 03 — بازبینی امنیت (Security Review), آنچه خوب انجام شده ✅, جدول ریسک, یادداشت روی claims مستندات

### Community 53 - ".execute"
Cohesion: 0.40
Nodes (5): AI Arena — گزارش‌های بازبینی کامل (GLM-5.3-Flash), خلاصه‌ی یک‌خطی, فایل‌های خوانده‌شده به‌صورت کامل, فهرست گزارش‌ها, وضعیت رفع (2026-09-05)

### Community 54 - ".resume_session"
Cohesion: 0.67
Nodes (3): Raised when a tool call cannot be parsed from a response., ToolCallParseError, Exception

## Knowledge Gaps
- **150 isolated node(s):** `ai-arena`, `HIGH`, `MEDIUM`, `LOW`, `Changed` (+145 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Orchestrator` connect `Orchestrator` to `ToolRegistry`, `ToolResult`, `ProviderError`, `.run_turn`, `RateLimiter`, `SessionState`, `Agent`, `app.py`, `SessionManager`, `._build_system_prompt`, `AGENTS.md`, `AuditLogger`, `CerebrasProvider`, `tool_executor.py`, `._save_session`, `render_context_panel`, `_render_status_bar`, `.get_active_session`, `.start_background`, `_AlwaysProse`, `.get`, `.advance`?**
  _High betweenness centrality (0.098) - this node is a cross-community bridge._
- **Why does `SessionState` connect `SessionManager` to `ToolRegistry`, `tool_executor.py`, `._save_session`, `.run_turn`, `render_context_panel`, `SessionState`, `Agent`, `.get_active_session`, `Orchestrator`, `.start_background`, `app.py`, `_render_status_bar`, `_AlwaysProse`, `AuditLogger`, `._deserialize`?**
  _High betweenness centrality (0.059) - this node is a cross-community bridge._
- **Why does `SessionManager` connect `Agent` to `ToolRegistry`, `ToolResult`, `ProviderError`, `CerebrasProvider`, `._save_session`, `.run_turn`, `render_context_panel`, `SessionState`, `app.py`, `Orchestrator`, `_AlwaysProse`, `._build_system_prompt`, `AuditLogger`, `._deserialize`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Are the 23 inferred relationships involving `Orchestrator` (e.g. with `RateLimiter` and `SessionManager`) actually correct?**
  _`Orchestrator` has 23 INFERRED edges - model-reasoned connections that need verification._
- **Are the 17 inferred relationships involving `Agent` (e.g. with `SessionState` and `_CapturingProvider`) actually correct?**
  _`Agent` has 17 INFERRED edges - model-reasoned connections that need verification._
- **Are the 18 inferred relationships involving `SessionState` (e.g. with `Agent` and `Message`) actually correct?**
  _`SessionState` has 18 INFERRED edges - model-reasoned connections that need verification._
- **Are the 17 inferred relationships involving `SessionManager` (e.g. with `Orchestrator` and `_CapturingProvider`) actually correct?**
  _`SessionManager` has 17 INFERRED edges - model-reasoned connections that need verification._