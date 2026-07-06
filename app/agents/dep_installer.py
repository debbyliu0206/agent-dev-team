import logging
import os
from typing import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions

from ..tools import install_target_deps
from ..guardrails.dependency_checker import check_requirements

log = logging.getLogger(__name__)


class DepInstaller(BaseAgent):
    """Deterministic loop step: installs the target app's own dependencies (its
    requirements.txt + pytest) into a project-local target venv, so the test
    suite runs against the right environment. Runs after the code is applied and
    before tests execute.

    Security: runs dependency_checker (slopsquatting defense) before installing.
    Packages not on the allowlist AND not found on PyPI are blocked.
    """

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        target_dir = os.environ.get("TARGET_APP_DIR", "target")
        req_path = os.path.join(target_dir, "requirements.txt")

        if os.path.isfile(req_path):
            dep_report = check_requirements(req_path)
            if not dep_report["safe"]:
                suspicious = [
                    f"{p['name']}: {p['reason']}"
                    for p in dep_report["packages"]
                    if p["status"] in ("not_found", "suspicious")
                ]
                log.warning("DEP CHECK BLOCKED: %s", suspicious)
                yield Event(
                    author=self.name,
                    actions=EventActions(state_delta={"dep_install": {
                        "status": "blocked",
                        "message": "Dependency check found suspicious packages",
                        "violations": suspicious,
                    }}),
                )
                return

        result = install_target_deps()
        yield Event(
            author=self.name,
            actions=EventActions(state_delta={"dep_install": result}),
        )
