# Architecture Overview

## System Design

AI Arena is a modular multi-agent orchestration platform built with Python and Streamlit. The architecture follows a clean separation of concerns across six primary layers:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Streamlit UI Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Config Panel │  │ Chat Panel   │  │ Context Panel        │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Orchestration Engine                         │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────────────┐  │
│  │ Session Manager│  │ Rate Limiter   │  │ Orchestrator      │  │
│  │                │  │                │  │ (Middleware)      │  │
│  └────────────────┘  └────────────────┘  └───────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Tool Layer                                                  │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │ │
│  │  │ Tool Registry│  │ Tool Parser  │  │ Tool Executor   │  │ │
│  │  └──────────────┘  └──────────────┘  └─────────────────┘  │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Agent Layer                               │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────────────┐  │
│  │ Agent A        │  │ Agent B        │  │ Agent N            │  │
│  │ (Critic)       │  │ (Optimist)     │  │ (Custom)           │  │
│  └────────────────┘  └────────────────┘  └───────────────────┘  │
│  Each agent has: system prompt, provider, model, tool access     │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Provider Abstraction Layer                   │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────────────┐  │
│  │ OpenAI         │  │ Anthropic      │  │ OpenRouter        │  │
│  └────────────────┘  └────────────────┘  └───────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Shared Context File                           │
│                    (on disk, per session)                        │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

The middleware flow for each agent turn (one-shot per turn):

```
1. Orchestrator selects next agent
2. Agent is called with:
   - System prompt (agent instructions + tool manual)
   - User message: current file content inlined as a fenced code block
     (agent does NOT need to call read_file — content is pre-injected)
3. Response is received from the LLM
4. Parser detects tool calls in the response
   ├─ No tool call → record agent message → advance to next agent
   └─ Tool call detected → execute via registry (one shot, no re-call)
       ├─ Success → record envelope as system message → advance
       └─ Failure → retry up to tool_max_retries (default 3)
           ├─ Retry success → record envelope → advance
           └─ Max retries exceeded → error envelope, graceful degradation
5. Context file is already updated (via write_file tool)
6. Advance to next agent in the ping-pong loop
```

> **Key design:** The orchestrator does NOT re-call the provider after a tool
> call. Each agent turn is exactly one provider call. The file content is
> injected into the user message so agents never need to call `read_file`.

## Key Design Decisions

### Why middleware pattern?
The app acts as an intelligent middleware between agents because:
- It can detect and execute tool calls transparently
- It can retry failed tool calls without involving the user
- It can inject tool manuals into system prompts automatically
- It can log all tool interactions for debugging
- It ensures agents never get stuck — always succeeds, retries, or degrades gracefully

### Why a real file on disk?
The shared context is a real file on disk to:
- Enable diff tracking between turns
- Allow manual inspection and editing by the user
- Support pause/resume by simply reading the current file state
- Enable multi-tool access outside the orchestration loop

### Why provider abstraction?
The `BaseProvider` interface allows new LLM providers to be added without modifying the orchestration engine. Each provider implements the same `chat()` interface, making the system provider-agnostic.

### Why session-based state?
Sessions are persisted to disk as JSON, enabling:
- Multi-session support
- Resume after restart (stale running/paused flags are auto-reset)
- Audit trail of all agent interactions
- Export and sharing of completed sessions
- Per-session save locks (thread-safe, TOCTOU-safe via `setdefault`)

### Why threading.Event for stop control?
The background loop uses a `threading.Event` instead of a plain bool to:
- Provide proper memory barriers between threads
- Enable `Event.wait(timeout)` for cooperative cancellation
- Avoid relying on CPython's GIL for correctness

### Why tool-based file access?
Instead of giving agents raw file system access, they use typed tools that:
- Enforce consistent interfaces
- Enable validation and error handling
- Make the agent's capabilities explicit
- Support future tool expansion (web search, code execution, etc.)

### Why tool registry?
A single registry provides:
- One source of truth for all tools
- Dynamic tool manual generation for prompt injection
- Easy tool discovery and registration
- No hardcoded tool names in multiple places
