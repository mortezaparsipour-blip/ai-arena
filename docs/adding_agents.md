# How to Add a New Agent

AI Arena is designed to make adding new agents as simple as possible.

## Quick Start

1. **Create a system prompt** in `/sys_prompts/`:
   ```markdown
   # My Custom Agent

   You are the [Role] in a multi-agent collaboration. Your responsibilities are:
   1. [Responsibility 1]
   2. [Responsibility 2]

   ## Rules
   - Always read the context first
   - Write your contributions back to the context
   ```

2. **Create a session** in the UI with the desired number of agents

3. **Assign the prompt** to an agent slot via the UI dropdown

## Agent Roles

AI Arena supports three built-in role types:

| Role | Default Behavior |
|------|-----------------|
| `critic` | Adds 3 positive points and 5 critical observations |
| `optimist` | Proposes solutions to criticisms and adds 1–3 new ideas |
| `custom` | No default behavior — fully defined by system prompt |

## Agent Configuration Fields

When creating an agent, you configure:

| Field | Description | Example |
|-------|-------------|---------|
| `id` | Unique identifier | `agent_2` |
| `name` | Display name | `Researcher` |
| `role` | Role type | `custom` |
| `system_prompt` | Instructions for the agent | Loaded from file or custom text |
| `provider` | LLM provider | `openai`, `anthropic`, `openrouter`, `cerebras` |
| `model` | Model identifier | `gpt-4o` |
| `api_key` | Provider API key | `sk-...` |
| `color` | UI display color | `#f59e0b` |
| `enabled` | Whether agent is active | `true` |

## Example: Adding a Researcher Agent

1. Create `/sys_prompts/researcher.md`:
   ```markdown
   # Researcher Agent

   You are the **Researcher** in a multi-agent collaboration. Your role is to gather
   information, identify data needs, and suggest research directions.

   ## Responsibilities:
   1. Review the current context and identify knowledge gaps
   2. Propose 2–3 research questions or data sources
   3. Summarize findings clearly

   ## Rules:
   - Always use `read_file` first
   - Use `write_file` or `append_file` to save your analysis
   - Be specific and cite reasoning
   ```

2. In the UI, set the agent count to 3
3. For Agent 3, select "researcher" from the system prompt dropdown
4. Configure the provider and model as desired
5. Start the session

## Advanced: Programmatic Agent Creation

```python
from ai_arena.models.agent import Agent, AgentRole
from ai_arena.config import config

# Load a custom prompt
prompt = config.load_sys_prompt("researcher")

# Create the agent
agent = Agent(
    id="agent_3",
    name="Researcher",
    role=AgentRole.CUSTOM,
    system_prompt=prompt,
    provider="openai",
    model="gpt-4o",
    api_key="your-api-key",
    color="#f59e0b",
)
```

## Agent Turn Order

Agents take turns in the order they are configured. The cycle repeats for each round:

```
Round 1: Agent 1 → Agent 2 → Agent 3
Round 2: Agent 1 → Agent 2 → Agent 3
...
Round N: Agent 1 → Agent 2 → Agent 3
```

To change turn order, reorder the agents in the session configuration.
