"""Iterate-only runner (frozen artifacts): the contract + tests are FIXED. We run ONLY the build
loop (coder -> apply -> deps -> test -> test_fixer -> test -> keep_best -> gate) against the
existing target, so the coder climbs a stable, valid target instead of re-rolling a fresh lottery
each run.

No architect, no test_writer -> tests are never REgenerated. TestFixer is included (same as the
main build loop) because broken test MECHANICS (fixtures/collection/syntax) are unfixable from the
application side — observed: a TestClient fixture bug error'd 18 API tests and the coder-only loop
stalled against them. TestFixer repairs mechanics only, never assertions/logic.
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
from app.agents.test_fixer import create_test_fixer_agent
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
    create_test_fixer_agent(),          # fixes test MECHANICS only (fixtures/imports/syntax)
    TestRunner(name="test_runner_2"),   # verify the fixes before snapshotting
    KeepBest(name="keep_best"),
    EscalationChecker(name="gate"),
])


async def main():
    runner = InMemoryRunner(agent=iterate, app_name="app")

    # Seed with REAL test results by running pytest NOW — otherwise the coder's
    # first iteration edits blind (observed: it "fixed" imaginary problems and
    # broke 11 passing tests before the first TestRunner ever ran). Also
    # refresh .best_snapshot to the CURRENT source so KeepBest can roll back a
    # bad first edit to today's state instead of a stale previous session's.
    import shutil
    from app.tools import run_tests
    baseline = run_tests()
    print(f"[seed] baseline: passed={baseline.get('passed')} failed={baseline.get('failed')}")
    snap = target / ".best_snapshot"
    if snap.exists():
        shutil.rmtree(snap, ignore_errors=True)
    snap.mkdir(parents=True)
    for name in ("backend", "tests"):  # mirror KeepBest.GUARDED_DIRS layout
        src = target / name
        if src.exists():
            shutil.copytree(src, snap / name)

    seed = {
        "api_contract": contract,
        "test_results": baseline,
        "best_passed": baseline.get("passed", 0),
        "best_test_results": baseline,
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
            text="Make the frozen test suite pass by fixing the backend code. The API contract is in state. "
                 "If test ERRORs come from library incompatibilities (e.g. a TypeError raised inside a "
                 "third-party client/fixture), fix them by pinning compatible versions in requirements.txt "
                 "— never by editing tests.")]),
    ):
        who = getattr(event, "author", "?")
        # Per-iteration diagnostics: surface pass/fail counts, apply status and
        # keep_best actions as they happen, so a stalled run is explainable.
        delta = getattr(getattr(event, "actions", None), "state_delta", None) or {}
        notes = []
        tr = delta.get("test_results")
        if isinstance(tr, dict):
            notes.append(f"tests passed={tr.get('passed')} failed={tr.get('failed')}")
        af = delta.get("applied_files")
        if isinstance(af, dict):
            notes.append(f"apply={af.get('status')}" + (f" ({af.get('message')})" if af.get('status') != 'success' else ""))
        if "keep_best" in delta:
            notes.append(f"keep_best={delta['keep_best']}")
        suffix = ("  <-- " + "; ".join(notes)) if notes else ""
        if event.is_final_response() and event.content and event.content.parts:
            print(f"[{who}] final ({len(event.content.parts[0].text or '')} chars){suffix}")
        else:
            print(f"[{who}] step{suffix}")

    sess = await runner.session_service.get_session(app_name="app", user_id="u", session_id="s")
    tr = sess.state.get("test_results")
    print("\n=== best_passed:", sess.state.get("best_passed"))
    print("=== final test_results:", tr if isinstance(tr, dict) else str(tr)[:300])


if __name__ == "__main__":
    asyncio.run(main())
