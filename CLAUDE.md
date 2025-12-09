# Project Documentation

## Purpose

This repository contains **D&D-themed Google ADK agent examples** demonstrating different levels of agent complexity:

- **`dice_agent`** - Simple single agent with basic tool calls (roll dice)
- **`spell_agent`** - Simple single agent with complex tool calls (spell lookup)
- **`wizard_agent`** - Complex multi-agent with state management (character builder)

All agents use D&D 5e 2024 rules and get their data from JSON files via tools.

---

## Repository Structure

```
dice_agent                    # Simple single-agent example
└── agent.py

spell_agent/                  # Multi-tool single-agent example
├── agent.py                  # Root agent - spell lookup assistant
├── tools/
│   └── spells.py             # Spell search and lookup tools
└── data/
    └── spells.json           # Spell database

wizard_agent/                 # Complex multi-agent example
├── agent.py                  # Root coordinator agent
├── agents/                   # Step-specific sub-agents (10 total)
│   ├── race_agent.py
│   ├── ability_score_agent.py
│   └── ...
├── tools/                    # Domain tools and state management
│   ├── character_sheet.py    # State tools
│   ├── races.py
│   ├── spells.py
│   └── ...
├── models/
│   └── character_sheet.py    # Pydantic state model
└── data/                     # Static data files
    ├── races.json
    ├── spells.json
    └── backgrounds.json

tests/                        # pytest tests for both agents
```

---

## Libraries & Tools Reference

### Google ADK (Agent Development Kit)

**Documentation:**
- LLM Tooling: https://raw.githubusercontent.com/google/adk-docs/refs/heads/main/llms-full.txt
- Evaluations: https://raw.githubusercontent.com/google/adk-docs/refs/heads/main/docs/evaluate/index.md

**Key concepts:**
- Tools are first-class; define functions and the framework handles calling
- Agents use `transfer_to_agent` to delegate to sub-agents
- State persists in `tool_context.state` across agent transitions
- Sub-agents must explicitly transfer back to parent to continue

**Running agents:**
```bash
# Web UI (all agents)
uv run adk web

# Specific agent
uv run adk run spell_agent
uv run adk run wizard_agent

# With session saving
uv run adk run wizard_agent --save_session

# Replay mode: Run a specific set of queries against a specific agent in a single command
uv run adk run wizard_agent --replay <(echo '{"state": {}, "queries": ["start", "input1", "input2"]}')
```

### Pydantic

Used for typed, validated data models.

**Documentation:** https://docs.pydantic.dev/latest/llms-full.txt

```python
from pydantic import BaseModel, Field, computed_field

class MyState(BaseModel):
    data: dict = Field(default_factory=dict)

    @computed_field
    @property
    def computed_value(self) -> str:
        return self.data.get("key", "default")
```

### uv (Package Manager)

```bash
uv add <package-name>      # Add dependency
uv sync                    # Install dependencies
uv run pytest tests/       # Run command
```

### ruff (Linter & Formatter)

**Documentation:** https://docs.astral.sh/ruff/

```bash
uv run ruff check .        # Lint
uv run ruff format .       # Format
```

### ty (Type Checker)

**Documentation:** https://docs.astral.sh/ty/

```bash
uv run ty check .
```

### pytest (Testing)

```bash
uv run pytest tests/ -v                    # All tests
uv run pytest tests/spell_agent/ -v        # One agent's tests
```

---

## Development Workflow

### Adding a New Agent

1. Create folder: `<agent_name>/`
2. Add `agent.py` with root agent
3. Add `tools/` with tool functions
4. Add `data/` with any JSON data files
5. Add `__init__.py` files
6. Add tests in `tests/<agent_name>/`

### Modifying Tools

1. Tools are the source of truth for domain logic
2. Return `ToolResponse[T]` for consistency
3. Never duplicate data in agent prompts
4. Add unit tests for all tools

### Testing

```bash
# Run all tests
uv run pytest tests/ -v

# Lint and format
uv run ruff check . && uv run ruff format .

# Type check
uv run ty check .
```

### Evaluations

```bash
uv run adk eval \
    <agent_name> \
    path/to/evalset.json \
    [--print_detailed_results]
```

---

## Agent Patterns

### Simple Agent (spell_agent)

Single LLM agent with tools. Good for:
- Lookup/search functionality
- Q&A with data retrieval
- Simple task completion

```python
root_agent = Agent(
    name="spell_agent",
    model=LiteLlm(model="openai/gpt-4o"),
    instruction="...",
    tools=[find_spell, list_spells, ...],
)
```

### Multi-Agent with State (wizard_agent)

Coordinator agent that routes to specialized sub-agents. Good for:
- Multi-step workflows
- Form-like interactions
- Complex state management

```python
root_agent = Agent(
    name="wizard_builder",
    model=_model,
    instruction="...",
    tools=[get_character_sheet],
    sub_agents=[race_agent, ability_score_agent, ...],
)
```

**Key patterns:**
- State lives in `tool_context.state`
- Sub-agents use `transfer_to_agent` to return control
- Coordinator checks state to determine next step
- Each sub-agent handles one step of the workflow

---

## Style & Naming Conventions

- **Agents:** `<name>_agent` (e.g., `race_agent`, `spell_agent`)
- **Tools:** `<verb>_<noun>` (e.g., `list_races`, `find_spell_by_name`)
- **Models:** `PascalCase` (e.g., `CharacterSheet`)
- **Test files:** `test_<module>.py`

---

## Debugging

### Common Issues

**Agent stops unexpectedly:**
- Check sub-agent transfers back to coordinator
- Look for "STOP" finish reason in session

**State not persisting:**
- Ensure tools use `tool_context.state`
- Check state delta in session file

**Tool errors:**
- Validate input matches expected format
- Check tool response structure

### Session Analysis

```bash
# Save session
uv run adk run wizard_agent --save_session

# Analyze with jq
jq '.events[] | select(.content.parts[0].text != null) | {author, text: .content.parts[0].text}' sessions/session-*.json
```
