"""Iterate-only runner (frozen artifacts): the contract + tests are FIXED. We run ONLY the coder
loop (coder -> apply -> deps -> test -> keep_best -> gate) against the existing target, so the coder
climbs a stable, valid target instead of re-rolling a fresh lottery each run.

No architect, no test_writer, no test_fixer -> tests are never regenerated or edited.
"""
import asyncio
import json
import os
import pathlib

from dotenv import load_dotenv
load_dotenv(pathlib.Path(__file__).parent / "app" / ".env")

target = pathlib.Path(os.environ["TARGET_APP_DIR"])

from google.adk.agents import LoopAgent
from google.adk.runners import InMemoryRunner
from google.genai import types

from app.agents.coder import create_coder_agent
from app.agents.code_applier import CodeApplier
from app.agents.dep_installer import DepInstaller
from app.agents.test_runner import TestRunner
from app.agents.keep_best import KeepBest
from app.agents.escalation import EscalationChecker

# Load the FROZEN contract + component design from the target's docs/.
contract = ""
docs = target / "docs"
for fn in ("api_contract.md", "component_design.md"):
    p = docs / fn
    if p.exists():
        contract += f"\n\n===== {fn} =====\n" + p.read_text(encoding="utf-8")

iterate = LoopAgent(name="iterate_loop", max_iterations=8, sub_agents=[
    create_coder_agent(),
    CodeApplier(name="code_applier"),
    DepInstaller(name="dep_installer"),
    TestRunner(name="test_runner"),
    KeepBest(name="keep_best"),
    EscalationChecker(name="gate"),
])


async def main():
    runner = InMemoryRunner(agent=iterate, app_name="app")
    seed = {
        "api_contract": contract,
        "test_results": {"passed": 0, "failed": 0, "failures": [], "logs": "", "no_tests": True},
        # No spec_reviewer in this loop; the bar is tests-green, so mark compliant so the gate
        # escalates purely on the test results.
        "review": {"compliant": True, "violations": []},
    }
    await runner.session_service.create_session(
        app_name="app", user_id="u", session_id="s", state=seed
    )

    async for event in runner.run_async(
        user_id="u", session_id="s",
        new_message=types.Content(role="user", parts=[types.Part.from_text(
            text="Make the frozen test suite pass by fixing the backend code. The API contract is in state.")]),
    ):
        who = getattr(event, "author", "?")
        if event.is_final_response() and event.content and event.content.parts:
            print(f"[{who}] final ({len(event.content.parts[0].text or '')} chars)")
        else:
            print(f"[{who}] step")

    sess = await runner.session_service.get_session(app_name="app", user_id="u", session_id="s")
    tr = sess.state.get("test_results")
    print("\n=== best_passed:", sess.state.get("best_passed"))
    print("=== final test_results:", tr if isinstance(tr, dict) else str(tr)[:300])


if __name__ == "__main__":
    asyncio.run(main())
