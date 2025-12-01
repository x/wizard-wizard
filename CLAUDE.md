# Project Documentation

## Purpose (Repo-Specific)

This repository implements a **D&D 5e Level 1 Wizard Character Builder** using the AI Wizard Pattern.

The agent guides users through a 10-step character creation process:
1. Race → 2. Ability Scores → 3. Class (Wizard) → 4. Background →
5. Spellcasting config → 6. Spellbook (6 lvl-1 spells) →
7. Cantrips (3) → 8. Prepared spells → 9. Derived stats → 10. Validation

**Key constraints:**
- D&D 5e 2024 rules only
- Level 1 Wizard only
- Ability score increases come from Backgrounds (not races, per 2024 rules)
- All spell/race/background data comes from tools (never hallucinated)

**State model:** `CharacterSheet` in `wizard_agent/models/character_sheet.py`

**Root agent:** `wizard_builder` in `wizard_agent/agent.py`

**Pattern:** See [WIZARD_PATTERN.md](WIZARD_PATTERN.md) for the Automatic Looping Coordinator pattern used in this implementation.

---

## Repository Structure

```
wizard_agent/
├── agent.py              # Root coordinator agent
├── agents/               # Step-specific sub-agents
│   ├── race_agent.py
│   ├── ability_score_agent.py
│   ├── class_agent.py
│   └── ...
├── tools/                # Domain tools and state management
│   ├── character_sheet.py  # State tools
│   ├── races.py
│   ├── spells.py
│   └── ...
├── models/               # Pydantic models
│   └── character_sheet.py
└── data/                 # Static data files
    ├── races.json
    ├── spells.json
    └── ...

tests/                    # pytest tests
```

**Architecture principles:**
- `agent.py` orchestrates; keep it thin and declarative
- Each sub-agent in `agents/` handles exactly one step
- Tools in `tools/` are the source of truth for rules and state
- Models in `models/` define typed, validated state structures
- Never duplicate rule data in agent prompts

---

## Libraries & Tools Reference

### Google ADK (Agent Development Kit)

We use Google ADK for agent orchestration, tool calling, and state management.

**Documentation:**
- LLM Tooling: https://raw.githubusercontent.com/google/adk-docs/refs/heads/main/llms-full.txt
- Evaluations: https://raw.githubusercontent.com/google/adk-docs/refs/heads/main/docs/evaluate/index.md

**Key concepts:**
- Tools are first-class; define functions and the framework handles calling
- Agents use `transfer_to_agent` to delegate to sub-agents
- State persists in `tool_context.state` across agent transitions
- Sub-agents must explicitly transfer back to parent to trigger continuation

**Running the agent:**
```bash
# Interactive mode
uv run adk run wizard_agent

# With session saving
uv run adk run wizard_agent --save_session

# Replay mode (for testing)
uv run adk run wizard_agent --replay <(echo '{"state": {}, "queries": ["start", "input1", "input2"]}')
```

### Pydantic

Used for typed, validated data models.

**Documentation:** https://docs.pydantic.dev/latest/llms-full.txt

**Usage patterns:**
- Define state models with `BaseModel`
- Use `Field()` for defaults and validation
- Add `@computed_field` for derived properties
- Include validation methods on the model

```python
from pydantic import BaseModel, Field, computed_field

class MyState(BaseModel):
    data: dict = Field(default_factory=dict)

    @computed_field
    @property
    def computed_value(self) -> str:
        return self.data.get("key", "default")

    def validate_complete(self) -> tuple[bool, list[str]]:
        errors = []
        # validation logic
        return (len(errors) == 0, errors)
```

**Type conversions:** Use `@classmethod` constructors for conversions between types:

```python
@classmethod
def from_other_type(cls, other: OtherType) -> "MyState":
    return cls(data=other.some_field)
```

### uv (Package Manager)

**Add dependencies:**
```bash
uv add <package-name>
```

**Run commands:**
```bash
uv run pytest tests/
uv run ruff check .
uv run adk run wizard_agent
```

### ruff (Linter & Formatter)

**Documentation:**
- Linter: https://docs.astral.sh/ruff/linter/
- Rules: https://docs.astral.sh/ruff/rules/
- Formatter: https://docs.astral.sh/ruff/formatter/

**Usage:**
```bash
# Check code
uv run ruff check .

# Format code
uv run ruff format .
```

**Configuration:** See `pyproject.toml` for rule configuration.

### ty (Type Checker)

**Documentation:**
- Main: https://docs.astral.sh/ty/
- Rules: https://docs.astral.sh/ty/reference/rules/

**Usage:**
```bash
uv run ty check .
```

### pytest (Testing)

**Run tests:**
```bash
# All tests
uv run pytest tests/**/test_*.py

# Specific test file
uv run pytest tests/wizard_agent/test_races.py

# With verbose output
uv run pytest tests/ -v
```

### dotenv (Environment Variables)

Load environment variables from `.env` file:

```python
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
```

---

## Agent Development Workflow

### Adding Dependencies

1. Add the package:
   ```bash
   uv add <package-name>
   ```

2. Update imports in code

3. Run tests:
   ```bash
   uv run pytest tests/**/test_*.py
   ```

### Modifying Agent Logic

1. **For coordinator changes:** Edit `wizard_agent/agent.py`
   - Keep it declarative
   - Use `check_next_step` to determine flow
   - Let sub-agents do the work

2. **For step-specific changes:** Edit the relevant agent in `wizard_agent/agents/`
   - Each agent handles one step
   - Must transfer back to coordinator when complete
   - Use step-specific tools

3. **For state changes:** Edit `wizard_agent/models/character_sheet.py`
   - Add fields to `CharacterSheet` model
   - Include validation methods
   - Update `check_next_step` tool if needed

4. **For tools:** Edit files in `wizard_agent/tools/`
   - Tools are the source of truth for domain logic
   - Return `ToolResponse[T]` for consistency
   - Never duplicate data in agent prompts

### Testing & Validation

**Run tests after changes:**
```bash
uv run pytest tests/**/test_*.py
```

**Lint and format:**
```bash
uv run ruff check .
uv run ruff format .
uv run ty check .
```

**Test agent interactively:**
```bash
uv run adk run wizard_agent --save_session
```

**Quick replay testing:**
```bash
uv run adk run wizard_agent --replay <(echo '{"state": {}, "queries": ["start", "step1", "step2"]}')
```

### Evaluations

Run evaluations to test agent behavior systematically:

```bash
uv run adk eval \
    wizard_agent \
    path/to/evalset.json \
    [--config_file_path=path/to/config.json] \
    [--print_detailed_results]
```

Write evaluation sets to test:
- Happy path flows
- Error handling
- Edge cases
- State consistency

---

## Testing Strategies

### Session Analysis

Sessions capture complete conversation history, state changes, and tool calls.

**Save sessions:**
```bash
uv run adk run wizard_agent --save_session
```

**Analyze with jq:**
```bash
# View all text messages
jq '.events[] | select(.content.parts[0].text != null) | {author, text: .content.parts[0].text}' sessions/session-<UUID>.json

# View state changes
jq '.events[] | select(.actions.stateDelta != null) | {author, state: .actions.stateDelta}' sessions/session-<UUID>.json

# Track agent transfers
jq '.events[] | select(.actions.transferToAgent != null) | {from: .author, to: .actions.transferToAgent}' sessions/session-<UUID>.json

# View final state
jq '.state' sessions/session-<UUID>.json
```

**Debugging agent flow:**
- Look for "do you want to continue?" messages (shouldn't exist)
- Check that transfers happen automatically between steps
- Verify sub-agents transfer back to coordinator
- Confirm state updates occur at expected points

### Replay Testing

Test flows programmatically with replay files:

```json
{
  "state": {},
  "queries": [
    "User message 1",
    "User message 2",
    "User message 3"
  ]
}
```

**Run with file:**
```bash
uv run adk run wizard_agent --replay test_replay.json
```

**Run inline (faster iteration):**
```bash
uv run adk run wizard_agent --replay <(echo '{"state": {}, "queries": ["msg1", "msg2"]}')
```

### Unit Testing

Test tools and state logic independently:

```python
def test_state_validation():
    sheet = CharacterSheet(name="Test", race="Human")
    is_valid, errors = sheet.validate_complete()
    assert not is_valid  # Incomplete character
    assert len(errors) > 0

def test_check_next_step():
    context = create_test_context()
    result = check_next_step(context)
    assert result["result"]["next_agent"] == "race_agent"
```

### Integration Testing

Test that agents properly coordinate:

```python
def test_agent_transfers():
    response = coordinator.process("Start")
    assert response.actions.transfer_to_agent == "race_agent"

    # Simulate race_agent completing
    response = race_agent.process("My choice")
    assert response.actions.transfer_to_agent == "wizard_builder"
```

---

## The Wizard Pattern

This repository implements the **AI Wizard Pattern** - an architectural pattern for building AI-driven multi-step forms and configuration wizards.

**Core pattern:** [WIZARD_PATTERN.md](WIZARD_PATTERN.md)

**Key concepts:**
1. **Shared State** - All agents read/write a common state object
2. **Automatic Looping Coordinator** - Continuously checks what's needed and routes to specialists
3. **Specialized Sub-Agents** - Each handles one step, transfers back when complete
4. **Step-Specific Tools** - Provide options, validation, and state mutation
5. **Progress Determination** - Central `check_next_step` tool encodes workflow logic

**Implementation notes:**
- Coordinator MUST call `check_next_step` every time it's invoked
- Sub-agents MUST explicitly `transfer_to_agent("coordinator")` when done
- NO "do you want to continue?" prompts between steps
- Automatic progression creates a seamless "form wizard" experience

See [WIZARD_PATTERN.md](WIZARD_PATTERN.md) for complete documentation, diagrams, and examples.

---

## Debugging Guidance

### Common Issues

**Agent stops after sub-agent completes:**
- Check sub-agent transfers back to coordinator
- Verify coordinator calls `check_next_step` on every invocation
- Look for "STOP" finish reason in session file

**State not persisting:**
- Ensure tools use `tool_context.state` for read/write
- Call `save_state(tool_context, state)` after updates
- Check state delta in session file

**Validation fails unexpectedly:**
- Verify tool data matches exactly (names, formats)
- Check for typos in lookups
- Add defensive validation in tools

**Tool errors:**
- Most issues are input mismatch or invalid lookups
- Validate assumptions about data structure
- Check tool response format matches expectations

### Investigation Steps

1. **Look at tool errors first** - Check tool call results in session
2. **Validate assumptions** - Verify data matches expected format
3. **Add explicit checks** - Return structured errors from tools
4. **Keep tight control of names** - Ensure exact matches for lookups

---

## Style & Naming Conventions

### Code Style

- **Prefer clear names over comments**
- **Avoid long prompt strings in code** - Keep agent instructions declarative
- **Keep agent responsibilities minimal** - One step per agent
- **No duplication of rule data** - Tools are the source of truth
- **Small, pure functions** - Easy to test and understand
- **Defensive validation** - Check inputs and state consistency

### Naming Conventions

- **Agents:** `<step>_agent` (e.g., `race_agent`, `background_agent`)
- **Tools:** `<verb>_<noun>` (e.g., `list_races`, `save_character_name`)
- **Models:** `<Noun>` (e.g., `CharacterSheet`, `AbilityScores`)
- **Test files:** `test_<module>.py`
- **Constants:** `UPPER_SNAKE_CASE`

### File Organization

- One responsibility per module
- Follow existing naming patterns
- Group related functionality together
- Keep imports organized (stdlib, third-party, local)

---

## End of Documentation
