"""Two-tier permission policy for the multi-agent coding system.

Tier 1 (auto-approved): routine, low-risk actions that don't modify user code
or introduce unknown dependencies.

Tier 2 (requires approval): actions that write/delete files, install unknown
packages, deploy, or make external network calls. Approvals are recorded so
identical action types can be fast-tracked in the same session.
"""

from __future__ import annotations

import hashlib
import json
import logging
from enum import Enum
from typing import Any

from app.guardrails.dependency_checker import SAFE_PACKAGES

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Action types
# ---------------------------------------------------------------------------

class ActionType(str, Enum):
    """Every discrete action the agents can request."""

    VENV_CREATE = "venv_create"
    DEP_INSTALL_SAFE = "dep_install_safe"
    DEP_INSTALL_UNKNOWN = "dep_install_unknown"
    RUN_TESTS = "run_tests"
    READ_FILE = "read_file"
    LIST_FILES = "list_files"
    WRITE_CODE = "write_code"
    DELETE_FILE = "delete_file"
    START_SERVER = "start_server"
    DEPLOY = "deploy"
    EXTERNAL_NETWORK = "external_network"


# ---------------------------------------------------------------------------
# Tier definitions
# ---------------------------------------------------------------------------

TIER_1_AUTO: frozenset[str] = frozenset({
    ActionType.VENV_CREATE,
    ActionType.DEP_INSTALL_SAFE,
    ActionType.RUN_TESTS,
    ActionType.READ_FILE,
    ActionType.LIST_FILES,
    ActionType.START_SERVER,
})

TIER_2_APPROVAL: frozenset[str] = frozenset({
    ActionType.WRITE_CODE,
    ActionType.DEP_INSTALL_UNKNOWN,
    ActionType.DELETE_FILE,
    ActionType.DEPLOY,
    ActionType.EXTERNAL_NETWORK,
})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _action_hash(action: str, details: dict[str, Any]) -> str:
    """Deterministic hash for an (action, details) pair.

    Used to recognise previously-approved requests so the user isn't prompted
    twice for the exact same operation.
    """
    payload = json.dumps({"action": action, "details": details}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def _summarise_files(files: list[str], limit: int = 5) -> str:
    """Return a comma-separated preview of file names, truncated with '...'."""
    if len(files) <= limit:
        return ", ".join(files)
    return ", ".join(files[:limit]) + f", ... ({len(files)} total)"


def _format_approval_prompt(action: str, details: dict[str, Any]) -> str:
    """Build a human-readable approval prompt for a single Tier-2 action."""
    if action == ActionType.WRITE_CODE:
        files = details.get("files", [])
        summary = details.get("summary", "")
        prompt = f"Coder wants to write {len(files)} file(s): {_summarise_files(files)}"
        if summary:
            prompt += f"\n  Purpose: {summary}"
        prompt += "\n  Approve? [y/n]"
        return prompt

    if action == ActionType.DEP_INSTALL_UNKNOWN:
        packages = details.get("packages", [])
        return (
            f"Coder wants to install non-allowlisted package(s): "
            f"{', '.join(packages)}\n  Approve? [y/n]"
        )

    if action == ActionType.DELETE_FILE:
        files = details.get("files", [])
        return (
            f"Coder wants to delete {len(files)} file(s): "
            f"{_summarise_files(files)}\n  Approve? [y/n]"
        )

    if action == ActionType.DEPLOY:
        target = details.get("target", "unknown target")
        return f"Coder wants to deploy to {target}.\n  Approve? [y/n]"

    if action == ActionType.EXTERNAL_NETWORK:
        url = details.get("url", "unknown URL")
        return f"Coder wants to make an external network request to {url}.\n  Approve? [y/n]"

    # Fallback for any future Tier-2 action
    return f"Coder wants to perform '{action}' with details {details}.\n  Approve? [y/n]"


# ---------------------------------------------------------------------------
# Core policy class
# ---------------------------------------------------------------------------

class PermissionPolicy:
    """Classifies agent actions into auto-approved or approval-required.

    Usage::

        policy = PermissionPolicy()
        result = policy.check_and_format("write_code", {
            "files": ["main.py", "routes.py"],
            "summary": "Implement session endpoints",
        })
        if not result["allowed"]:
            # present result["approval_prompt"] to the human
            ...
            policy.approve("write_code", details)
    """

    def __init__(self) -> None:
        self._approval_history: set[str] = set()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def classify(self, action: str, details: dict[str, Any]) -> str:
        """Classify an action request.

        Returns
        -------
        str
            One of:
            - ``"auto_approved"``  -- Tier-1 action, no prompt needed.
            - ``"approved"``       -- Tier-2 but previously approved (same hash).
            - ``"requires_approval"`` -- Tier-2, needs human confirmation.
        """
        resolved = self._resolve_action(action, details)

        if resolved in TIER_1_AUTO:
            logger.info("Auto-approved tier-1 action: %s", resolved)
            return "auto_approved"

        h = _action_hash(resolved, details)
        if h in self._approval_history:
            logger.info(
                "Previously approved tier-2 action (hash %s): %s", h[:8], resolved
            )
            return "approved"

        logger.info("Tier-2 action requires approval: %s", resolved)
        return "requires_approval"

    def approve(self, action: str, details: dict[str, Any]) -> None:
        """Record that the human approved this action."""
        resolved = self._resolve_action(action, details)
        h = _action_hash(resolved, details)
        self._approval_history.add(h)
        logger.info("Recorded approval for action %s (hash %s)", resolved, h[:8])

    def check_and_format(self, action: str, details: dict[str, Any]) -> dict[str, Any]:
        """Check permissions and return a structured result.

        Returns
        -------
        dict
            ``allowed``         -- bool, True when action can proceed now.
            ``tier``            -- 1 or 2.
            ``reason``          -- human-readable explanation.
            ``approval_prompt`` -- str prompt for the user, or None.
        """
        resolved = self._resolve_action(action, details)
        classification = self.classify(action, details)

        if classification == "auto_approved":
            return {
                "allowed": True,
                "tier": 1,
                "reason": f"Action '{resolved}' is auto-approved (tier 1).",
                "approval_prompt": None,
            }

        if classification == "approved":
            return {
                "allowed": True,
                "tier": 2,
                "reason": f"Action '{resolved}' was previously approved this session.",
                "approval_prompt": None,
            }

        # requires_approval
        prompt = _format_approval_prompt(resolved, details)
        return {
            "allowed": False,
            "tier": 2,
            "reason": f"Action '{resolved}' requires human approval.",
            "approval_prompt": prompt,
        }

    def batch_approval(self, actions: list[dict[str, Any]]) -> dict[str, Any]:
        """Evaluate a batch of actions and produce a single approval summary.

        Parameters
        ----------
        actions
            List of ``{"action": str, "details": dict}`` items.

        Returns
        -------
        dict
            ``auto_approved``   -- list of actions that need no prompt.
            ``previously_approved`` -- list of tier-2 actions already approved.
            ``needs_approval``  -- list of actions still requiring approval.
            ``summary_prompt``  -- single human-readable prompt covering all
                                   ``needs_approval`` items, or None.
        """
        auto_approved: list[dict[str, Any]] = []
        previously_approved: list[dict[str, Any]] = []
        needs_approval: list[dict[str, Any]] = []

        for item in actions:
            action = item["action"]
            details = item.get("details", {})
            classification = self.classify(action, details)

            entry = {"action": action, "details": details}
            if classification == "auto_approved":
                auto_approved.append(entry)
            elif classification == "approved":
                previously_approved.append(entry)
            else:
                needs_approval.append(entry)

        summary_prompt: str | None = None
        if needs_approval:
            summary_prompt = self._build_batch_prompt(needs_approval)

        return {
            "auto_approved": auto_approved,
            "previously_approved": previously_approved,
            "needs_approval": needs_approval,
            "summary_prompt": summary_prompt,
        }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _resolve_action(self, action: str, details: dict[str, Any]) -> str:
        """Resolve ambiguous dep-install actions using the SAFE_PACKAGES list.

        If the caller passes a generic ``dep_install_safe`` or
        ``dep_install_unknown`` the value is returned as-is.  But this also
        allows callers to pass a neutral label (e.g. ``"dep_install"``) and
        let the policy decide based on package names in *details*.
        """
        if action in (ActionType.DEP_INSTALL_SAFE, ActionType.DEP_INSTALL_UNKNOWN):
            # Verify: if the caller said "safe" but packages aren't on the
            # allowlist, upgrade to "unknown".
            packages = details.get("packages", [])
            if packages:
                all_safe = all(
                    pkg.lower() in SAFE_PACKAGES for pkg in packages
                )
                return (
                    ActionType.DEP_INSTALL_SAFE if all_safe
                    else ActionType.DEP_INSTALL_UNKNOWN
                )
        return action

    @staticmethod
    def _build_batch_prompt(items: list[dict[str, Any]]) -> str:
        """Combine multiple Tier-2 items into one approval prompt."""
        # Group by action type for a compact summary.
        grouped: dict[str, list[dict[str, Any]]] = {}
        for item in items:
            resolved = item["action"]
            grouped.setdefault(resolved, []).append(item["details"])

        lines: list[str] = ["The following actions require your approval:\n"]
        idx = 1
        for action, details_list in grouped.items():
            for details in details_list:
                lines.append(f"  {idx}. {_format_approval_prompt(action, details)}")
                idx += 1

        lines.append("\nApprove all? [y/n/select]")
        return "\n".join(lines)
