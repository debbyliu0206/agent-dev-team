"""Dumb-request smoke test: run ONLY the PM agent on a short brief to validate
Vertex generation + strict-JSON output before running the full pipeline."""
import asyncio
import pathlib

from dotenv import load_dotenv
load_dotenv(pathlib.Path(__file__).parent / "app" / ".env")

from app.agents.pm import create_pm_agent
from google.adk.runners import InMemoryRunner
from google.genai import types

REQ = """Build a multi-user Study Tracker web app.
- Today tab: one-tap toggle between 'studying' and 'rest'; each switch prompts a note. Editable daily goals (min/ideal hours). Allow editing/backfilling a recorded segment.
- Week tab: a calendar heatmap (columns=days, rows=time slots), click a block to see what it was and its duration; navigate previous/next week.
- Month tab: last-30-days summary + activity heatmap; navigate months; bucket days by the user's LOCAL timezone midnight.
- Auth: Firebase Auth (Google/email/phone) for cross-device sync.
- Backend: Python FastAPI (REST). DB: Cloud SQL (PostgreSQL). Hosting: Google Cloud Run.
- Data: Session{id, userId, date(YYYY-MM-DD local), start, end, type(study|rest), notes}; UserSettings{userId, minHours, idealHours, timezone}. Every query scoped to the authenticated userId.
"""


async def main():
    pm = create_pm_agent()
    runner = InMemoryRunner(agent=pm, app_name="app")
    await runner.session_service.create_session(app_name="app", user_id="u", session_id="s")
    final = None
    async for event in runner.run_async(
        user_id="u",
        session_id="s",
        new_message=types.Content(role="user", parts=[types.Part.from_text(text=REQ)]),
    ):
        if event.is_final_response() and event.content and event.content.parts:
            final = event.content.parts[0].text

    print("=== PM RAW OUTPUT (first 4000 chars) ===")
    print((final or "NONE")[:4000])

    # Validate it parses as our Spec contract
    import json
    from app.schemas import Spec
    try:
        text = (final or "").strip()
        if text.startswith("```"):
            text = text.strip("`")
            text = text[text.find("{"):text.rfind("}") + 1]
        spec = Spec.model_validate_json(text)
        print("\n=== SPEC VALIDATION: OK ===")
        print("features:", len(spec.features), "| criteria:", len(spec.acceptance_criteria),
              "| contracts:", len(spec.data_contracts))
        print("tech_stack:", spec.tech_stack.model_dump())
    except Exception as e:
        print("\n=== SPEC VALIDATION: FAILED ===", type(e).__name__, str(e)[:400])


if __name__ == "__main__":
    asyncio.run(main())
