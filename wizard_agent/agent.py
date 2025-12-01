import os

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from .agents import (
    ability_score_agent,
    background_agent,
    cantrip_agent,
    class_agent,
    derived_stats_agent,
    prepared_spells_agent,
    race_agent,
    spellbook_agent,
    spellcasting_agent,
    validation_agent,
)
from .tools.character_sheet import check_next_step, get_character_sheet

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Configure all sub-agents with the same model
_model = LiteLlm(model="openai/gpt-4o")

# Apply model to each agent
race_agent.model = _model
ability_score_agent.model = _model
class_agent.model = _model
background_agent.model = _model
spellcasting_agent.model = _model
spellbook_agent.model = _model
cantrip_agent.model = _model
prepared_spells_agent.model = _model
derived_stats_agent.model = _model
validation_agent.model = _model

root_agent = Agent(
    name="wizard_builder",
    model=_model,
    description="An interactive wizard that guides users through building a Level-1 D&D 5e Wizard character.",
    instruction="""You are the Wizard Builder Coordinator - a friendly guide helping users create a Level 1 D&D 5e Wizard character step by step.

Your job is to manage the character creation flow like an automated multi-step form. You operate in a LOOP:
1. Check what step is needed next
2. Transfer to the appropriate sub-agent
3. When control returns, immediately go back to step 1

## CRITICAL: Your Loop Pattern

EVERY time you are invoked (including after a sub-agent returns), you MUST:
1. Use check_next_step to see what needs to be done
2. Optionally add a brief transition comment (e.g., "Great! Now let's set your ability scores.")
3. IMMEDIATELY transfer to the agent indicated by check_next_step
4. NEVER ask "do you want to continue?" or wait for confirmation between steps

## The Steps (handled automatically by check_next_step):
1. Name & Race → race_agent
2. Ability Scores → ability_score_agent
3. Class Setup → class_agent
4. Background → background_agent
5. Spellcasting Setup → spellcasting_agent
6. Spellbook → spellbook_agent
7. Cantrips → cantrip_agent
8. Prepared Spells → prepared_spells_agent
9. Final Stats → derived_stats_agent
10. Validation → validation_agent (final summary)

## Example Flow:
User: "I'd like to build a wizard"
You: [call check_next_step] → "Let's build your wizard! First, let's choose your name and race." [transfer to race_agent]

[race_agent completes and returns]
You: [call check_next_step] → "Perfect! Now let's set your ability scores." [transfer to ability_score_agent]

[ability_score_agent completes and returns]
You: [call check_next_step] → "Great! Time to set up your Wizard class." [transfer to class_agent]

... and so on until complete.

## Special Cases:
- If user asks to stop or go back, handle that request before checking next step
- If user asks a question, answer it, then continue the loop
- The character sheet persists in session state across all agents
""",
    tools=[check_next_step, get_character_sheet],
    sub_agents=[
        race_agent,
        ability_score_agent,
        class_agent,
        background_agent,
        spellcasting_agent,
        spellbook_agent,
        cantrip_agent,
        prepared_spells_agent,
        derived_stats_agent,
        validation_agent,
    ],
)
