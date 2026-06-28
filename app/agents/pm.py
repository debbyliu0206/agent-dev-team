import pathlib
from google.adk.agents import Agent

def _prompt(name): 
    return (pathlib.Path(__file__).parent / "prompts" / f"{name}.md").read_text(encoding="utf-8")

def create_pm_agent():
    return Agent(
        name="pm", 
        model="gemini-2.5-pro", 
        description="Turns requirements into a structured spec",
        instruction=_prompt("pm"), 
        output_key="spec"
    )
