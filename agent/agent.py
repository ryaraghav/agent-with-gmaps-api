from google.adk.agents import Agent
from google.genai.types import GenerateContentConfig
from . import prompts
from . import tools


root_agent = Agent(
    name="curator_agent",
    model="gemini-2.0-flash",
    description=(
        "Help user find the best restaurants in a city"
    ),
    instruction=prompts.system_instruction_v8,
    tools=[tools.get_restaurants],
    generate_content_config=GenerateContentConfig(temperature=0.1),
)

# run "adk run agent" in terminal to run the agent
#Testing 