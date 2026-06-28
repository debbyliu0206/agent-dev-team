import pathlib
from google.adk.agents import Agent
from ..tools import write_project_file

def _prompt(name): 
    return (pathlib.Path(__file__).parent / "prompts" / f"{name}.md").read_text(encoding="utf-8")

def create_test_writer_agent():
    return Agent(
        name="test_writer",
        model="gemini-2.5-flash",
        description="Writes executable tests for the requirements",
        instruction=_prompt("test_writer") + "\n\nSpec:\n{spec?}\n\nAPI Contract (assert EXACTLY this):\n{api_contract?}",
        output_key="test_suite",
        tools=[write_project_file]
    )
