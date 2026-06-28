from typing import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions

from ..util import extract_json


class EscalationChecker(BaseAgent):
    """Stops the build loop when tests actually ran, all passed, and the reviewer
    is satisfied. Uses extract_json so ```json-fenced reviewer output is parsed."""

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        tr = extract_json(ctx.session.state.get("test_results")) or {}
        rv = extract_json(ctx.session.state.get("review")) or {}

        failed = tr.get("failed", 1) if isinstance(tr, dict) else 1
        no_tests = tr.get("no_tests", True) if isinstance(tr, dict) else True

        # Hard done-signal: the tests are the source of truth. Green (all tests ran and passed)
        # means done. The spec reviewer's `compliant` flag is advisory only — an LLM flag must not
        # be able to block a genuinely green build (that's what kept the loop from self-declaring done).
        if failed == 0 and not no_tests:
            yield Event(author=self.name, actions=EventActions(escalate=True))
        else:
            yield Event(author=self.name)
