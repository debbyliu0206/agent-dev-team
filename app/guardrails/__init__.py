"""Security guardrails for AI-generated code.

Six modules defend against coding-agent-specific threats (not chatbot PII):

- code_scanner: blocks dangerous patterns (eval, exec, subprocess, raw sockets)
- dependency_checker: slopsquatting defense via PyPI verification + allowlist
- secret_patterns: detects hardcoded AWS keys, DB URLs, passwords in source
- input_sanitizer: strips prompt-injection payloads from code comments/strings
- permission_policy: 2-tier approval system to reduce user fatigue
- Circuit breaker lives in agents/escalation.py (stall + drift detection)

All scanners run inside the deterministic pipeline agents (CodeApplier,
DepInstaller) so unsafe artifacts are caught before they reach disk.
"""
