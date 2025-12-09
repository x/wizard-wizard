# Google ADK D&D Examples

A collection of D&D-themed agents built with Google ADK, demonstrating progressively more complex agent patterns.

## Agents

| Agent | Complexity | Description |
|-------|------------|-------------|
| `dice_agent` | Minimal | Single agent with basic tools - rolls D&D dice |
| `spell_agent` | Simple | Single agent with tool calls - looks up D&D spells |
| `wizard_agent` | Complex | Multi-agent stateful wizard - builds a Level 1 D&D Wizard character |

## Quick Start

```bash
# Install dependencies
uv sync

# Run the web UI (shows all agents)
uv run adk web

# Or run a specific agent
uv run adk run dice_agent
uv run adk run spell_agent
uv run adk run wizard_agent
```
