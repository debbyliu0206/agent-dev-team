import pathlib
from google.adk.agents import Agent
from ..tools import read_project_file, list_project_files

def _prompt(name):
    return (pathlib.Path(__file__).parent / "prompts" / f"{name}.md").read_text(encoding="utf-8")

def create_user_test_guide_agent():
    return Agent(
        name="user_test_guide",
        model="gemini-2.5-flash",
        description="Generates plain-language testing instructions for non-technical users",
        instruction=_prompt("user_test_guide") + "\n\nSpec:\n{spec?}\n\nAPI Contract:\n{api_contract?}\n\nTest Results:\n{test_results?}",
        output_key="user_test_guide",
        tools=[read_project_file, list_project_files]
    )
