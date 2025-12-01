## **Purpose**

This repository contains a set of **Google ADK agents and tools** that cooperate to build a **valid Level-1 Wizard (D&D 5e 2024 rules)**.
All code in this repo supports that single workflow.

The root agent coordinates a sequence of sub-agents (Race, Ability Scores, Class, Background, Spellcasting, Spellbook, Cantrips, Preparation, Derived Stats, Validation).
Each agent updates a shared character-sheet structure.

---

## **How to Work in This Repo**

### **Add dependencies**

Use standard Python packaging.
If you add a library, update:

```
pyproject.toml
```

using `uv`

```
uv add <package-name>
```

Run tests (see below) after adding any dependencies.

```
uv run pytest tests/**/test_*.py
```

### **Run tests**

Tests are written using the `pytest` framework.

If tests exist, run them with:

```
uv run pytest tests/**/test_*.py
```

or an appropriate subset.

If none exist yet, keep code modular so tests can be added easily.

### **Evaluations**

You can run evaluation of an eval set file through the command line interface.

The docs for evaluations are available at:
https://raw.githubusercontent.com/google/adk-docs/refs/heads/main/docs/evaluate/index.md

You should write evaluations to test your agents and tools.

We only care about running the evaluations with the CLI (you must wrap with `uv run`)

Here is the command:

```
uv run adk eval \
    <AGENT_MODULE_FILE_PATH> \
    <EVAL_SET_FILE_PATH> \
    [--config_file_path=<PATH_TO_TEST_JSON_CONFIG_FILE>] \
    [--print_detailed_results]
```

For example:

```
uv run adk eval \
    samples_for_testing/hello_world \
    samples_for_testing/hello_world/hello_world_eval_set_001.evalset.json
```

---

## **Google ADK**

We use the **Google ADK LiteLlm + Agent** classes for orchestrating the character-building workflow.

You should read this documentation before modifying agent logic:

**Google ADK LLM Tooling**
[https://raw.githubusercontent.com/google/adk-docs/refs/heads/main/llms-full.txt](https://raw.githubusercontent.com/google/adk-docs/refs/heads/main/llms-full.txt)

Key points:

* Tools are first-class and should be used rather than re-implementing logic.
* The root agent should be declarative: describe goals and rely on sub-agents + tools to do work.
* Agents should read & write to the shared character sheet consistently.


---

## **Pydantic, Dataclasses, and Dicts**

Use pydantic when appropriate for serialization and deserialization.

Full docs here:
https://docs.pydantic.dev/latest/llms-full.txt

If the data you're working with is simple (flat, typed, doesn't need to be serialized) it's fine to just use a dataclass. Python dictionaries should really only be used to interface with APIs that require them, handling kwargs, and handling unknown keys.

When working converting between types, use the `fromFoo` static-method constructor approach.

For example:

```
@dataclass
class Foo:
    qux: str
    baz: float

    @classmethod
    def from_bar(bar: Bar) -> "Foo":
        return Foo(bar.other_name_for_qux, bar.other_name_for_baz)
```

This works for both Dataclasses and Pydantic Models.

---

## **Code Structure**

* **`wizard_agent/tools`** → Spell, race, background, and dice lookup functionality.
  *Always use these; do not recreate rule data in agent code.*

* **`wizard_agent/agent.py`** → Orchestrates the Wizard-building pipeline.
  Should remain thin: describe the task, call sub-agents, and handle errors.

* **`wizard_agent/agents`** → Sub-agents for each step of the pipeline.
  Each should handle one step and return updated sheet or a structured error.

* **`wizard_agent/models`** → The character sheet dataclass or structured object.

When creating new files, follow existing naming patterns and keep one responsibility per module.

---

## **Linting and Formatting**

You should lint and format the code as part of your workflow. The primary linter and formatter are `ruff`, runnable with:

```
uv run ruff check .
```

You can look at the docs for the linter here:
https://docs.astral.sh/ruff/linter/

You can look at all the rules for ruff check here:
https://docs.astral.sh/ruff/rules/

```
uv run ruff format .
```

You can look at the docs for ruff format here:
https://docs.astral.sh/ruff/formatter/


You can additionally type-check the code with:

```
uv run ty check .
```

You can look at the docs here:
https://docs.astral.sh/ty/

And the rules for ty here:
https://docs.astral.sh/ty/reference/rules/#invalid-overload

In all of the above cases, there are some things that may not work with ruff and ty so it may be necessary to update the pyproject.toml

---

## **Debugging Guidance**

1. **Look at tool errors first** (most issues will be input mismatch or invalid lookups).
2. **Validate assumptions** about spell counts, ability-score methods, etc.
3. If an agent writes invalid data, add explicit checks or return structured errors.
4. Keep tight control of names: spell names, race names, etc. must match tool data exactly.

---

## **Testing & Session Analysis**

### **Running the Agent Interactively**

Test the wizard builder agent by running:

```bash
uv run adk run wizard_agent --save_session
```

This will:
- Start an interactive session where you can build a wizard
- Save the session to `sessions/session-<UUID>.json` for later analysis
- Use `--model` flag to specify a different model if needed

### **Testing with Replay**

You can test agent flows by providing pre-defined queries using the `--replay` flag.

**Quick testing with process substitution:**

```bash
# Test just the initial greeting
uv run adk run wizard_agent --replay <(echo '{"state": {}, "queries": ["I'\''d like to build a wizard"]}')

# Test through race selection
uv run adk run wizard_agent --replay <(echo '{"state": {}, "queries": ["I'\''d like to build a wizard", "Gandalf", "Human", "yes"]}')

# Test through multiple steps
uv run adk run wizard_agent --replay <(echo '{"state": {}, "queries": ["I'\''d like to build a wizard", "Elminster", "Elf", "yes", "standard array", "yes that works"]}')
```

**For repeatable test cases, create a file:**

```json
{
  "state": {},
  "queries": [
    "I'd like to build a wizard",
    "Elminster",
    "Human",
    "yes",
    "Can you explain my options?",
    "Standard array please",
    "Yes that recommended distribution is perfect"
  ]
}
```

Then run: `uv run adk run wizard_agent --replay test_replay.json`

**Verifying automatic transitions:**
- Watch for direct agent-to-agent transitions (e.g., race_agent completes → ability_score_agent starts)
- There should be NO "Would you like to continue?" prompts between steps
- Each sub-agent should only interact during its own step, then immediately stop responding

### **Analyzing Session Files**

Session files contain the complete conversation history, state changes, and tool calls. They're useful for:
- Understanding agent flow and where users get stuck
- Debugging why agents wait for confirmation instead of auto-continuing
- Checking what state was modified at each step

**Useful commands for session analysis:**

```bash
# Pretty-print the entire session
jq '.' sessions/session-<UUID>.json

# Extract just the conversation turns (user + agent messages)
jq '.events[] | select(.content.parts[0].text != null) | {author, text: .content.parts[0].text}' sessions/session-<UUID>.json

# See state changes over time
jq '.events[] | select(.actions.stateDelta.character_sheet != null) | {author, state: .actions.stateDelta.character_sheet}' sessions/session-<UUID>.json

# Find where agents transfer control
jq '.events[] | select(.actions.transferToAgent != null) | {from: .author, to: .actions.transferToAgent}' sessions/session-<UUID>.json

# Check final character sheet state
jq '.state.character_sheet' sessions/session-<UUID>.json
```

**What to look for when debugging agent flow:**
- Messages that ask "do you want to continue?" or "ready for the next step?" indicate the agent is waiting unnecessarily
- Look for patterns where user says "yes", "continue", "next" repeatedly - this means agents aren't auto-continuing
- Check transfer points: after each agent completes work, it should immediately transfer back to wizard_builder
- The wizard_builder should immediately transfer to the next agent without waiting for user confirmation

---

## **Business Logic Overview**

The core workflow:

1. Race → 2. Ability Scores → 3. Class (Wizard) → 4. Background →
5. Spellcasting config → 6. Spellbook (6 lvl-1 spells) →
7. Cantrips (3) → 8. Prepared spells → 9. Derived stats → 10. Validation

Each step should:

* Only modify its own slice of the sheet
* Validate before returning
* Never guess or hallucinate rule content (use tools instead)

Patterns we like:

* Small, pure functions inside each agent
* Defensive validation
* Clear naming, minimal comments

---

## **Agent Orchestration Pattern**

The wizard builder uses an **automatic looping coordinator** pattern:

### **How It Works**

1. **wizard_builder** (root agent) operates in a loop:
   - Calls `check_next_step` tool to determine what needs to be done
   - Transfers to the appropriate sub-agent
   - When sub-agent completes, the loop repeats automatically

2. **Sub-agents** complete their work and explicitly transfer back:
   - After completing their task, they use `transfer_to_agent` to return to `wizard_builder`
   - This triggers wizard_builder to check what's next and continue the flow
   - NO user "continue" message needed between steps

3. **check_next_step** tool determines the flow:
   - Examines the character sheet state
   - Returns which agent should handle the next step
   - This keeps the flow logic centralized and maintainable

### **Example Flow**

```
User: "I'd like to build a wizard"
  ↓
wizard_builder: [checks next step] → transfers to race_agent
  ↓
race_agent: [user picks name/race] → transfers back to wizard_builder
  ↓
wizard_builder: [checks next step] → transfers to ability_score_agent
  ↓
ability_score_agent: [user sets scores] → transfers back to wizard_builder
  ↓
wizard_builder: [checks next step] → transfers to class_agent
  ↓
... continues automatically until all steps complete
```

### **Key Implementation Details**

- **wizard_builder** must ALWAYS call `check_next_step` when invoked
- **Sub-agents** must explicitly `transfer_to_agent("wizard_builder")` when done
- The `CharacterSheet` model includes `completed_steps` for progress tracking
- The `check_next_step` tool encodes the business logic for step ordering

---

## **Style & Naming Conventions**

* Prefer clear names over comments.
* Avoid long prompt strings inside code; keep prompts declarative and short.
* Keep agent responsibilities minimal and explicit.
* No duplication of rules data—tools are the source of truth.

---

## **End of CLAUDE.md**
