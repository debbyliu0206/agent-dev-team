"""Frontend generation run: PM -> Architect -> Coder -> CodeApplier, producing a Next.js frontend
under TARGET_APP_DIR/frontend that talks to the existing green backend. E2E validation (Playwright)
+ local run is done by the orchestrator afterward (E2E-first), so there's no pytest loop here."""
import asyncio
import os
import pathlib

from dotenv import load_dotenv
load_dotenv(pathlib.Path(__file__).parent / "app" / ".env")

target = pathlib.Path(os.environ["TARGET_APP_DIR"])

from google.adk.agents import SequentialAgent
from google.adk.runners import InMemoryRunner
from google.genai import types

from app.agents.frontend import (
    create_fe_pm_agent, create_fe_architect_agent, create_fe_coder_agent,
)
from app.agents.code_applier import CodeApplier

# Bind the frontend to the REAL backend contract.
contract = ""
cpath = target / "docs" / "api_contract.md"
if cpath.exists():
    contract = cpath.read_text(encoding="utf-8")

REQ = """Build the Next.js (app-router, TypeScript) FRONTEND for the Study Tracker. It calls the
existing backend via REST (send an X-User-ID header). Reuse the proven Study Tracker UX:

- Today tab: one big one-tap toggle between 'studying' and 'rest'; each switch opens a note modal
  (skippable); editable daily goals (minimum / ideal hours) with a progress indicator; ability to
  edit or backfill a recorded session.
- Week tab: a CALENDAR HEATMAP (columns = days of the week, rows = time slots); click a block to see
  what it was and its duration; previous/next week navigation.
- Month tab: last-30-days summary + an activity heatmap; previous/next month navigation; bucket days
  by the user's LOCAL timezone (midnight boundary).
- All data flows through lib/api.ts to the backend; read the API contract for exact request/response
  shapes, status codes, and the X-User-ID auth header.
Include package.json (next/react/react-dom/typescript + dev/build/start scripts) and tsconfig/next config.
"""

pipeline = SequentialAgent(name="fe_pipeline", sub_agents=[
    create_fe_pm_agent(),
    create_fe_architect_agent(),
    create_fe_coder_agent(),
    CodeApplier(name="fe_applier"),
])


async def main():
    runner = InMemoryRunner(agent=pipeline, app_name="app")
    await runner.session_service.create_session(
        app_name="app", user_id="u", session_id="s", state={"api_contract": contract},
    )
    async for event in runner.run_async(
        user_id="u", session_id="s",
        new_message=types.Content(role="user", parts=[types.Part.from_text(text=REQ)]),
    ):
        who = getattr(event, "author", "?")
        if event.is_final_response() and event.content and event.content.parts:
            print(f"[{who}] final ({len(event.content.parts[0].text or '')} chars)")
        else:
            print(f"[{who}] step")

    fe = target / "frontend"
    print("\n=== generated frontend files ===")
    if fe.exists():
        for f in sorted(fe.rglob("*")):
            if f.is_file() and "node_modules" not in str(f):
                print(" ", f.relative_to(target))
    else:
        print("  (none)")


if __name__ == "__main__":
    asyncio.run(main())
