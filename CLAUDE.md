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

## **Style & Naming Conventions**

* Prefer clear names over comments.
* Avoid long prompt strings inside code; keep prompts declarative and short.
* Keep agent responsibilities minimal and explicit.
* No duplication of rules data—tools are the source of truth.

---

## **End of CLAUDE.md**
