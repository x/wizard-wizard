import os

from dotenv import load_dotenv
from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm

from .tools import backgrounds, dice, races, spells

load_dotenv()

OPEN_AI_API_KEY = os.getenv("OPEN_AI_API_KEY")


root_agent = Agent(
    model=LiteLlm("openai/gpt-4o"),
    name="root_agent",
    description="A D&D 5e assistant for spells, races, backgrounds, and dice rolling.",
    instruction="You are a helpful D&D 5e assistant. Help users look up spells, races, backgrounds, and roll dice. Use the available tools to provide accurate D&D information.",
    tools=[
        # Spell tools
        spells.find_spell_by_name,
        spells.list_spells,
        spells.list_schools,
        spells.list_classes,
        # Race tools
        races.find_race_by_name,
        races.list_races,
        races.get_ability_bonuses,
        races.list_races_by_ability,
        races.list_sizes,
        # Background tools
        backgrounds.find_background_by_name,
        backgrounds.list_backgrounds,
        backgrounds.list_backgrounds_by_feat,
        backgrounds.list_all_skills,
        backgrounds.list_all_feats,
        # Dice tools
        dice.roll_dice,
    ],
)
