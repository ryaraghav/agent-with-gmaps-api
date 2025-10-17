from google.adk.agents import Agent
from . import prompts
from . import tools


root_agent = Agent(
    name="curator_agent",
    model="gemini-2.0-flash",
    description=(
        "Help user find the best restaurants in a city"
    ),
    instruction= prompts.system_instruction_v4,
    tools=[tools.get_restaurants]
)

# run "adk run agent" in terminal to run the agent
#Testing 