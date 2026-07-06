import json
import logging
from typing import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions

from ..util import extract_json
from ..tools import apply_code_change
from ..guardrails.code_scanner import scan_code_change
from ..guardrails.secret_patterns import scan_for_secrets

log = logging.getLogger(__name__)


class CodeApplier(BaseAgent):
    """Deterministic loop step: parses the coder's `code_change` (which may be JSON
    wrapped in prose/fences) and actually writes the files via apply_code_change.

    Separating 'decide' (LLM coder) from 'apply' (this step) guarantees code lands
    on disk instead of depending on the model reliably calling a tool.

    Security: scans all Python files through code_scanner and secret_patterns
    before writing to disk. Blocked findings abort the entire apply.
    """

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        cc = extract_json(ctx.session.state.get("code_change"))
        if not (isinstance(cc, dict) and cc.get("files")):
            yield Event(
                author=self.name,
                actions=EventActions(state_delta={"applied_files": {
                    "status": "error", "message": "no valid code_change to apply"
                }}),
            )
            return

        cc_json = json.dumps(cc)

        scan_result = scan_code_change(cc_json)
        if not scan_result["safe"]:
            blocked = []
            for path, res in scan_result["file_results"].items():
                for f in res["findings"]:
                    if f["severity"] == "block":
                        blocked.append(f"{path}:{f['line']} — {f['description']}")
            log.warning("CODE SCAN BLOCKED: %s", blocked)
            yield Event(
                author=self.name,
                actions=EventActions(state_delta={"applied_files": {
                    "status": "blocked",
                    "message": "Security scan blocked unsafe code",
                    "violations": blocked,
                }}),
            )
            return

        secret_findings = []
        for entry in cc.get("files", []):
            path = entry.get("path", "")
            content = entry.get("content", "")
            if path.endswith(".py"):
                secrets = scan_for_secrets(content, path)
                secret_findings.extend(secrets)

        if secret_findings:
            details = [f"{s['line']}:{s['pattern_name']} — {s['match'][:60]}" for s in secret_findings]
            log.warning("SECRET SCAN BLOCKED: %s", details)
            yield Event(
                author=self.name,
                actions=EventActions(state_delta={"applied_files": {
                    "status": "blocked",
                    "message": "Secret scan found hardcoded credentials",
                    "violations": details,
                }}),
            )
            return

        result = apply_code_change(cc_json)
        yield Event(
            author=self.name,
            actions=EventActions(state_delta={"applied_files": result}),
        )
