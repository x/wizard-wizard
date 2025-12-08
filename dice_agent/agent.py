from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from random import randint

from dotenv import load_dotenv; load_dotenv()

def roll_d6():
    return randint(1, 6)

def roll_d20():
    return randint(1, 20)

root_agent = Agent(
    name="dice_roller",
    model=LiteLlm(model="openai/gpt-4o"),
    description="A dice roller for Dungeons & Dragons.",
    instruction="""You are a helpful Dungeons and Dragons
    dice rolling agent who rolls dice for the user when
    they ask, often in dice notation.
    **Example:** roll 2d6+1 -> roll two d6 and add one
    """,
    tools=[roll_d6, roll_d20]
)
