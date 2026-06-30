import pathlib
from google.adk.agents import Agent
from ..tools import write_project_file, read_project_file, list_project_files


def _p(name):
    return (pathlib.Path(__file__).parent / "prompts" / f"{name}.md").read_text(encoding="utf-8")


def create_fe_pm_agent():
    return Agent(
        name="fe_pm", model="gemini-2.5-pro",
        description="Frontend PM: turns requirements into a frontend feature spec",
        instruction=_p("fe_pm") + "\n\nBackend API contract:\n{api_contract?}",
        output_key="fe_spec",
    )


def create_fe_architect_agent():
    return Agent(
        name="fe_architect", model="gemini-2.5-pro",
        description="Frontend architect: Next.js component/file design",
        instruction=_p("fe_architect") + "\n\nFE spec:\n{fe_spec?}\n\nBackend API contract:\n{api_contract?}",
        output_key="fe_design",
        tools=[write_project_file],
    )


def create_fe_coder_agent():
    return Agent(
        name="fe_coder", model="gemini-2.5-pro",
        description="Frontend coder: implements the Next.js app",
        instruction=_p("fe_coder")
        + "\n\nFE spec:\n{fe_spec?}\n\nFE design:\n{fe_design?}\n\nBackend API contract:\n{api_contract?}",
        output_key="code_change",
        tools=[read_project_file, list_project_files],
    )
