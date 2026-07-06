from typing import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from google.genai import types

from ..util import extract_json


def _text_content(msg: str) -> types.Content:
    """Event.content must be a types.Content — a raw str fails pydantic
    validation and kills the whole invocation (observed with the stall report)."""
    return types.Content(role="model", parts=[types.Part.from_text(text=msg)])

STALL_WINDOW = 3  # consecutive iterations with no improvement before breaking


class EscalationChecker(BaseAgent):
    """Stops the build loop when tests pass (green-test escalation) or when the
    loop has stalled (circuit breaker). Also warns on intent drift if the coder
    introduces files outside the canonical layout.

    Uses extract_json so ```json-fenced reviewer/test output is parsed.

    Escalation triggers (checked in order):
    1. **Green**: failed == 0 and tests actually ran  ->  escalate (success).
    2. **Stall**: last 3 iterations show no improvement in passed count
       ->  escalate with a stall report to save resources.
    3. Otherwise: continue the loop.
    """

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        tr = extract_json(ctx.session.state.get("test_results")) or {}
        rv = extract_json(ctx.session.state.get("review")) or {}

        failed = tr.get("failed", 1) if isinstance(tr, dict) else 1
        no_tests = tr.get("no_tests", True) if isinstance(tr, dict) else True
        passed = tr.get("passed", 0) if isinstance(tr, dict) else 0

        # -- Iteration history (stall detection bookkeeping) ------------------
        history: list = ctx.session.state.get("iteration_history", [])
        history.append(passed)
        ctx.session.state["iteration_history"] = history

        # -- Intent drift detection -------------------------------------------
        drift_warning = self._check_drift(ctx)

        # -- 1. Green: all tests ran and passed -> done -----------------------
        # Hard done-signal: the tests are the source of truth. Green (all tests ran and passed)
        # means done. The spec reviewer's `compliant` flag is advisory only — an LLM flag must not
        # be able to block a genuinely green build (that's what kept the loop from self-declaring done).
        if failed == 0 and not no_tests:
            content = _text_content(drift_warning) if drift_warning else None
            yield Event(
                author=self.name,
                content=content,
                actions=EventActions(escalate=True),
            )
            return

        # -- 2. Stall: no progress for STALL_WINDOW consecutive iterations ----
        if len(history) >= STALL_WINDOW:
            recent = history[-STALL_WINDOW:]
            if len(set(recent)) == 1:
                stuck_at = recent[0]
                stall_msg = (
                    f"Build loop stalled: no progress in {STALL_WINDOW} consecutive "
                    f"iterations (passed count stuck at {stuck_at}). "
                    "Breaking loop to save resources."
                )
                if drift_warning:
                    stall_msg = f"{stall_msg}\n{drift_warning}"
                yield Event(
                    author=self.name,
                    content=_text_content(stall_msg),
                    actions=EventActions(escalate=True),
                )
                return

        # -- 3. Continue the loop ---------------------------------------------
        yield Event(author=self.name, content=_text_content(drift_warning) if drift_warning else None)

    # --------------------------------------------------------------------- #
    # Helpers
    # --------------------------------------------------------------------- #

    @staticmethod
    def _check_drift(ctx: InvocationContext) -> str | None:
        """Return a warning string if the coder introduced files outside the
        canonical layout, or None if everything looks fine."""
        canonical: list | None = ctx.session.state.get("canonical_files")
        if not canonical:
            return None

        coder_files: list = ctx.session.state.get("coder_files", [])
        if not coder_files:
            return None

        canonical_set = set(canonical)
        unexpected = sorted(set(coder_files) - canonical_set)
        if not unexpected:
            return None

        file_list = ", ".join(unexpected)
        return (
            f"Intent drift warning: the following files are outside the canonical "
            f"layout defined by the Architect: {file_list}"
        )
