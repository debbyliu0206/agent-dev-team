import pathlib
from google.adk.agents import Agent
from ..tools import read_project_file, list_project_files, write_project_file


def _prompt(name):
    return (pathlib.Path(__file__).parent / "prompts" / f"{name}.md").read_text(encoding="utf-8")


def create_test_fixer_agent():
    """Repairs TEST files that fail to collect/import (syntax, imports). Unlike the
    coder, this agent is allowed to edit tests — but only to fix mechanics, never to
    weaken assertions or change test intent."""
    return Agent(
        name="test_fixer",
        model="gemini-2.5-pro",
        description="Fixes broken test files so they parse, import, and collect",
        instruction=_prompt("test_fixer") + "\n\nLatest test results:\n{test_results?}",
        output_key="test_fix",
        tools=[read_project_file, list_project_files, write_project_file],
    )
