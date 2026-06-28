import pathlib
from google.adk.agents import Agent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

def _prompt(name): 
    return (pathlib.Path(__file__).parent / "prompts" / f"{name}.md").read_text(encoding="utf-8")

def create_e2e_qa_agent():
    playwright = McpToolset(connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(command="npx", args=["-y", "@playwright/mcp@latest"])
    ))
    return Agent(
        name="e2e_qa",
        model="gemini-2.5-flash",
        description="Runs Playwright tests to ensure E2E acceptance criteria pass",
        instruction=_prompt("e2e_qa"),
        output_key="e2e_report",
        tools=[playwright]
    )
