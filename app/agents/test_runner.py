from typing import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions

from ..tools import run_tests


class TestRunner(BaseAgent):
    """Deterministic loop step: runs pytest against the target app and writes the
    structured results into session state under ``test_results`` via a state_delta,
    so the EscalationChecker gate can read accurate, machine-set values (rather than
    relying on an LLM tool call landing in conversation history).
    """

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        results = run_tests(".")
        yield Event(
            author=self.name,
            actions=EventActions(state_delta={"test_results": results}),
        )
