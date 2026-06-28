import pathlib
from google.adk.agents import Agent
from ..tools import write_project_file

def _prompt(name): 
    return (pathlib.Path(__file__).parent / "prompts" / f"{name}.md").read_text(encoding="utf-8")

def create_architect_agent():
    return Agent(
        name="architect",
        model="gemini-2.5-pro",
        description="Turns the PM spec into a precise, binding API contract",
        instruction=_prompt("architect") + "\n\nSpec:\n{spec?}",
        output_key="api_contract",
        tools=[write_project_file]
    )
