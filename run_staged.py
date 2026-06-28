"""Staged pipeline run: PM -> test_writer -> (coder -> test_runner -> spec_reviewer -> gate) loop.
No E2E / no deploy. Generates the Study Tracker into TARGET_APP_DIR. Loop capped low for a first pass."""
import asyncio
import json
import os
import pathlib

from dotenv import load_dotenv
load_dotenv(pathlib.Path(__file__).parent / "app" / ".env")

# Ensure the target app directory exists before any tool/test runs.
target = os.environ.get("TARGET_APP_DIR")
pathlib.Path(target).mkdir(parents=True, exist_ok=True)

from google.adk.agents import SequentialAgent, LoopAgent
from google.adk.runners import InMemoryRunner
from google.genai import types

from app.agents.pm import create_pm_agent
from app.agents.architect import create_architect_agent
from app.agents.test_writer import create_test_writer_agent
from app.agents.coder import create_coder_agent
from app.agents.spec_reviewer import create_spec_reviewer_agent
from app.agents.test_runner import TestRunner
from app.agents.escalation import EscalationChecker
from app.agents.code_applier import CodeApplier
from app.agents.dep_installer import DepInstaller
from app.agents.test_fixer import create_test_fixer_agent
from app.agents.keep_best import KeepBest

staged = SequentialAgent(name="dev_team_staged", sub_agents=[
    create_pm_agent(),
    create_architect_agent(),
    create_test_writer_agent(),
    LoopAgent(name="build_loop", max_iterations=6, sub_agents=[
        create_coder_agent(),
        CodeApplier(name="code_applier"),
        DepInstaller(name="dep_installer"),
        TestRunner(name="test_runner"),
        create_test_fixer_agent(),
        TestRunner(name="test_runner_2"),
        KeepBest(name="keep_best"),
        create_spec_reviewer_agent(),
        EscalationChecker(name="gate"),
    ]),
])

# Feed the Study Tracker appendix of the spec as the requirements.
spec_md = (pathlib.Path(__file__).parent / ".agents-cli-spec.md").read_text(encoding="utf-8")
idx = spec_md.find("## Appendix")
REQ = spec_md[idx:] if idx != -1 else spec_md


async def main():
    runner = InMemoryRunner(agent=staged, app_name="app")
    # Seed test_results so the coder's {test_results} placeholder resolves on iteration 1
    # (before test_runner has produced any). no_tests=True keeps the gate "not green".
    seed = {"test_results": {"passed": 0, "failed": 0, "failures": [], "logs": "", "no_tests": True}}
    await runner.session_service.create_session(
        app_name="app", user_id="u", session_id="s", state=seed
    )

    async for event in runner.run_async(
        user_id="u",
        session_id="s",
        new_message=types.Content(role="user", parts=[types.Part.from_text(text=REQ)]),
    ):
        who = getattr(event, "author", "?")
        if event.is_final_response() and event.content and event.content.parts:
            txt = event.content.parts[0].text or ""
            print(f"[{who}] final response ({len(txt)} chars)")
        else:
            # show tool activity / intermediate authorship
            print(f"[{who}] step")

    sess = await runner.session_service.get_session(app_name="app", user_id="u", session_id="s")
    st = dict(sess.state)
    pathlib.Path("staged_state.json").write_text(
        json.dumps({k: str(v)[:4000] for k, v in st.items()}, indent=2, default=str),
        encoding="utf-8",
    )
    print("\n=== STATE KEYS ===", list(st.keys()))
    tr = st.get("test_results")
    print("=== TEST_RESULTS ===", tr if isinstance(tr, dict) else str(tr)[:400])


if __name__ == "__main__":
    asyncio.run(main())
