import json
from typing import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions

from ..util import extract_json
from ..tools import apply_code_change


class CodeApplier(BaseAgent):
    """Deterministic loop step: parses the coder's `code_change` (which may be JSON
    wrapped in prose/fences) and actually writes the files via apply_code_change.

    Separating 'decide' (LLM coder) from 'apply' (this step) guarantees code lands
    on disk instead of depending on the model reliably calling a tool.
    """

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        cc = extract_json(ctx.session.state.get("code_change"))
        if isinstance(cc, dict) and cc.get("files"):
            result = apply_code_change(json.dumps(cc))
        else:
            result = {"status": "error", "message": "no valid code_change to apply"}
        yield Event(
            author=self.name,
            actions=EventActions(state_delta={"applied_files": result}),
        )
