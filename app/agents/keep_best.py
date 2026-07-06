import shutil
from typing import AsyncGenerator, ClassVar

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions

from ..tools import _get_target_dir
from ..util import extract_json


class KeepBest(BaseAgent):
    """Regression guard. After tests run, snapshot the backend/ source whenever the pass count
    reaches a new high; if a later iteration regresses (fewer passing), restore the best snapshot
    AND restore the best test_results into state — so the gate and the next coder iteration both
    work from the best-known-good state instead of sliding backwards.
    """

    # Guard BOTH the app source and the tests: TestFixer edits tests/ inside the
    # loop, and an unguarded fixer can oscillate (observed: post-coder run hit 20
    # passed, fixer edits dropped the re-run to 18 and the damage persisted).
    GUARDED_DIRS: ClassVar[tuple[str, ...]] = ("backend", "tests")

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        tr = extract_json(ctx.session.state.get("test_results")) or {}
        passed = tr.get("passed", 0) if isinstance(tr, dict) else 0
        best = ctx.session.state.get("best_passed", -1)

        target = _get_target_dir()
        snap = target / ".best_snapshot"

        delta = {}
        action = "none"
        if passed >= best and (target / "backend").exists():
            # New (or equal) best -> snapshot the guarded dirs and remember the results.
            if snap.exists():
                shutil.rmtree(snap, ignore_errors=True)
            snap.mkdir(parents=True)
            for name in self.GUARDED_DIRS:
                src = target / name
                if src.exists():
                    shutil.copytree(src, snap / name)
            delta["best_passed"] = passed
            delta["best_test_results"] = tr
            action = f"snapshot(passed={passed})"
        elif passed < best and snap.exists():
            # Regression -> roll back the guarded dirs and results to the best snapshot.
            for name in self.GUARDED_DIRS:
                src = target / name
                best_copy = snap / name
                if best_copy.exists():
                    shutil.rmtree(src, ignore_errors=True)
                    shutil.copytree(best_copy, src)
            best_tr = ctx.session.state.get("best_test_results") or tr
            delta["test_results"] = best_tr
            action = f"restore(best={best})"

        delta["keep_best"] = action
        yield Event(author=self.name, actions=EventActions(state_delta=delta))
