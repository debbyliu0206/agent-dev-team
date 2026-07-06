"""Spec gate — human-in-the-loop guard between the PM interview and the build
pipeline.

The PM agent runs a multi-turn discovery interview, so most of its turns are
questions addressed to the human — not a spec. A SequentialAgent has no notion
of "wait for the user": it would march straight on and hand the PM's question
text to the Architect as if it were the spec (observed failure: the Architect,
fed conversational text instead of a contract, hallucinated a nonexistent
`to_code` tool).

Mechanism: this is a `before_agent_callback` on the *build pipeline* wrapper
agent. In ADK, a before-agent callback that returns Content skips the agent it
guards — including the whole subtree of a workflow agent — and ends that
agent's run with the returned content as its output. (Setting
`ctx.end_invocation` from inside a sub-agent does NOT work here: each agent
runs on a `model_copy` of its parent's InvocationContext, so the flag never
propagates upward.)

Effect per turn: while the interview is in progress the user sees the PM's
question plus one "interview in progress" note, and no build agent runs. Once
state["spec"] parses as a complete machine-readable spec, the callback returns
None and the pipeline proceeds.
"""

from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.genai import types

from ..util import extract_json

# A spec is "complete" when it carries every top-level section the downstream
# agents bind to. (`architecture` is intentionally not required — older spec
# formats omit it and the Architect can derive it.)
REQUIRED_KEYS = ("features", "data_contracts", "acceptance_criteria", "tech_stack")

WAITING_NOTE = (
    "📝 Discovery interview in progress — the build pipeline is on hold until "
    "the spec is confirmed. Answer the PM's question above to continue."
)


def spec_is_complete(raw) -> bool:
    """True if the PM's output parses as a complete spec JSON."""
    spec = extract_json(raw)
    return isinstance(spec, dict) and all(k in spec for k in REQUIRED_KEYS)


def require_complete_spec(
    callback_context: CallbackContext,
) -> Optional[types.Content]:
    """before_agent_callback: skip the build pipeline until the spec is ready."""
    if spec_is_complete(callback_context.state.get("spec")):
        return None  # spec confirmed -> run the pipeline
    return types.Content(
        role="model", parts=[types.Part.from_text(text=WAITING_NOTE)]
    )
