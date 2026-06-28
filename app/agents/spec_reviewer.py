import pathlib
from google.adk.agents import Agent
from ..tools import read_project_file, list_project_files

def _prompt(name): 
    return (pathlib.Path(__file__).parent / "prompts" / f"{name}.md").read_text(encoding="utf-8")

def create_spec_reviewer_agent():
    return Agent(
        name="spec_reviewer",
        model="gemini-2.5-pro",
        description="Reviews code against the specification",
        instruction=_prompt("spec_reviewer") + "\n\nSpec:\n{spec?}\n\nAPI Contract:\n{api_contract?}\n\nCodeChange:\n{code_change?}",
        output_key="review",
        tools=[read_project_file, list_project_files]
    )
