import pathlib
from google.adk.agents import Agent
from ..tools import read_project_file, list_project_files

def _prompt(name): 
    return (pathlib.Path(__file__).parent / "prompts" / f"{name}.md").read_text(encoding="utf-8")

def create_coder_agent():
    return Agent(
        name="coder",
        model="gemini-2.5-pro",
        description="Writes and modifies application code to pass tests",
        instruction=_prompt("coder") + "\n\nSpec:\n{spec?}\n\nAPI Contract (implement EXACTLY):\n{api_contract?}\n\nTestSuite:\n{test_suite?}\n\nTestResults:\n{test_results?}",
        output_key="code_change",
        tools=[read_project_file, list_project_files]
    )
