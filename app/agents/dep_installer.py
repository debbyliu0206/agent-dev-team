from typing import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions

from ..tools import install_target_deps


class DepInstaller(BaseAgent):
    """Deterministic loop step: installs the target app's own dependencies (its
    requirements.txt + pytest) into a project-local target venv, so the test
    suite runs against the right environment. Runs after the code is applied and
    before tests execute."""

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        result = install_target_deps()
        yield Event(
            author=self.name,
            actions=EventActions(state_delta={"dep_install": result}),
        )
