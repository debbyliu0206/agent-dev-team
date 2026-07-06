"""Code scanner guardrail — vets LLM-generated Python before it reaches disk.

Used by the CodeApplier agent in the multi-agent ADK pipeline.  Every .py
file in a CodeChange payload is scanned; non-Python files are silently
skipped.

Design
------
Patterns are split into three priority tiers that are checked per-line:

  1. **Priority WARN** — more-specific variants of a blocked category
     (e.g. ``subprocess.run(["pytest"...``) that should downgrade to a
     warning.  Checked first so they claim the category before the broader
     block rule fires.
  2. **BLOCK** — dangerous constructs that must be rejected.
  3. **Late WARN** — low-specificity catch-alls (e.g. any ``open()`` call)
     suppressed when a block in the same category already fired.

A cross-line check detects ``compile()`` paired with ``exec()`` anywhere
in the same file (obfuscated execution).

Explicitly safe patterns (``json.loads``, ``os.path.join``, framework
imports, etc.) either never match the dangerous regexes in the first
place or are guarded by a false-positive check.
"""

from __future__ import annotations

import json
import re
from typing import Any

# ────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ────────────────────────────────────────────────────────────────────────────

# Matches one, two, or three quote characters (covers regular and triple-
# quoted strings as well as f-strings).
_Q = r"""["']{1,3}"""


def _finding(
    pattern: str,
    line: int,
    severity: str,
    match: str,
    description: str,
) -> dict[str, Any]:
    """Build a single finding dict, truncating *match* to 100 chars."""
    return {
        "pattern": pattern,
        "line": line,
        "severity": severity,
        "match": match[:100],
        "description": description,
    }


# ────────────────────────────────────────────────────────────────────────────
# Pattern tables
#
# Each entry is (name, compiled_regex, description, category).
#
# *category* resolves conflicts when a WARN and a BLOCK both fire on one
# line — only the first match in a category is kept.
# ────────────────────────────────────────────────────────────────────────────

PatternEntry = tuple[str, re.Pattern[str], str, str]

# ── Priority WARN (checked BEFORE block) ───────────────────────────────────
# More-specific variants that downgrade a category from block to warn.

PRIORITY_WARN_PATTERNS: list[PatternEntry] = [
    (
        "subprocess_pytest",
        re.compile(
            r"\bsubprocess\.(?:run|call|Popen)\s*\("
            r"(?=.*(?:pytest|['\"]pytest['\"]))"
        ),
        "Subprocess call appears to run pytest — likely intentional test execution",
        "subprocess",
    ),
    (
        "requests_http",
        re.compile(
            r"\brequests\.(?:get|post|put|patch|delete|head|options)\s*\("
        ),
        "HTTP client call via requests — common in web apps but review the target URL",
        "http_client",
    ),
    (
        "httpx_client",
        re.compile(
            r"\bhttpx\.(?:get|post|put|patch|delete|head|options"
            r"|Client|AsyncClient)\b"
        ),
        "HTTP client usage via httpx — common in web apps but review the target URL",
        "http_client",
    ),
]

# ── BLOCK (must be rejected) ──────────────────────────────────────────────

BLOCK_PATTERNS: list[PatternEntry] = [
    # -- Shell execution --
    (
        "os.system",
        re.compile(r"\bos\.system\s*\("),
        "Arbitrary shell command execution via os.system()",
        "os_exec",
    ),
    (
        "os.popen",
        re.compile(r"\bos\.popen\s*\("),
        "Shell pipe via os.popen()",
        "os_exec",
    ),

    # -- Code execution --
    (
        "eval",
        re.compile(r"(?<![.\w])eval\s*\("),
        "Arbitrary code execution via eval()",
        "eval",
    ),
    (
        "exec",
        re.compile(r"(?<![.\w])exec\s*\("),
        "Arbitrary code execution via exec()",
        "exec",
    ),
    (
        "__import__",
        re.compile(r"\b__import__\s*\("),
        "Dynamic import bypasses static analysis",
        "dynamic_import",
    ),

    # -- Subprocess --
    (
        "subprocess.Popen",
        re.compile(r"\bsubprocess\.Popen\s*\("),
        "Process spawning via subprocess.Popen()",
        "subprocess",
    ),
    (
        "subprocess.run",
        re.compile(r"\bsubprocess\.run\s*\("),
        "Process spawning via subprocess.run()",
        "subprocess",
    ),
    (
        "subprocess.call",
        re.compile(r"\bsubprocess\.call\s*\("),
        "Process spawning via subprocess.call()",
        "subprocess",
    ),

    # -- Raw sockets --
    (
        "socket.socket",
        re.compile(r"\bsocket\.socket\s*\("),
        "Raw network socket creation",
        "socket",
    ),
    (
        "socket.connect",
        re.compile(r"\bsocket\.connect\s*\("),
        "Raw network socket connection",
        "socket",
    ),

    # -- FFI escape hatches --
    (
        "ctypes",
        re.compile(r"\bctypes\b"),
        "FFI escape hatch via ctypes — can call arbitrary C functions",
        "ffi",
    ),
    (
        "cffi",
        re.compile(r"\bcffi\b"),
        "FFI escape hatch via cffi — can call arbitrary C functions",
        "ffi",
    ),

    # -- Dynamic import via importlib --
    (
        "importlib.import_module",
        re.compile(r"\bimportlib\.import_module\s*\("),
        "Dynamic import via importlib bypasses static analysis",
        "dynamic_import",
    ),

    # -- Shebang lines --
    (
        "shebang",
        re.compile(r"^#!\s*/bin/"),
        "Shebang line — file is an embedded shell script",
        "shebang",
    ),

    # -- File open with absolute paths --
    # Any absolute Unix path (starts with /) is suspicious — generated code
    # should use paths relative to the target directory.
    (
        "open_absolute_unix",
        re.compile(r"\bopen\s*\(\s*f?" + _Q + r"/"),
        "File open with absolute Unix path outside the target directory",
        "open",
    ),
    # Any absolute Windows path (drive letter + colon + backslash).
    (
        "open_absolute_windows",
        re.compile(r"\bopen\s*\(\s*f?" + _Q + r"[A-Za-z]:\\"),
        "File open with absolute Windows path",
        "open",
    ),
]

# ── Late WARN (checked AFTER block) ───────────────────────────────────────
# Low-specificity catch-alls suppressed when a block in the same category
# already fired on the line.

LATE_WARN_PATTERNS: list[PatternEntry] = [
    (
        "open_relative",
        re.compile(r"\bopen\s*\("),
        "File open() call — verify the path is within the target directory",
        "open",
    ),
]

# ────────────────────────────────────────────────────────────────────────────
# Explicitly safe patterns (ALLOW)
#
# These constructs look like they might trigger a rule but are harmless.
# Most are handled implicitly: the dangerous regexes simply do not match
# them (e.g. ``os.environ.get`` cannot match ``\bos\.system\s*\(``).
# The _is_false_positive() guard covers the few remaining edge cases.
#
# Safe — DO NOT FLAG:
#   json.loads(, json.dumps(, json.load(, json.dump(
#   pathlib.Path( (relative paths)
#   os.environ.get(, os.environ[, os.getenv(
#   os.path.join(, os.path.exists(, os.path.* in general
#   logging.*, print(
#   Imports of: fastapi, pydantic, sqlalchemy, uvicorn
# ────────────────────────────────────────────────────────────────────────────


def _is_false_positive(line: str, category: str) -> bool:
    """Return True if the match on *line* for *category* is a false positive."""
    if category == "os_exec":
        # Guard against a hypothetical regex overlap where ``os.environ``
        # or ``os.path`` somehow matched the os_exec rule.
        if re.search(r"\bos\.(?:environ|getenv|path)\b", line):
            if not re.search(r"\bos\.(?:system|popen)\s*\(", line):
                return True
    return False


# ────────────────────────────────────────────────────────────────────────────
# Public API
# ────────────────────────────────────────────────────────────────────────────

def scan_code(code: str, filepath: str) -> dict[str, Any]:
    """Scan a single Python source string for dangerous patterns.

    Parameters
    ----------
    code : str
        The full Python source text to scan.
    filepath : str
        The intended destination path (for context in findings — the file
        is **not** read from disk).

    Returns
    -------
    dict
        ``{"safe": bool, "findings": [...]}``.  ``safe`` is ``True`` only
        when there are zero ``"block"``-severity findings.
    """
    findings: list[dict[str, Any]] = []
    lines = code.split("\n")

    # Pre-scan for the cross-line compile()+exec() obfuscation pattern.
    # compile() here means the *builtin* compile, not re.compile or similar.
    has_raw_compile = bool(re.search(r"(?<![.\w])compile\s*\(", code))
    has_exec = bool(re.search(r"(?<![.\w])exec\s*\(", code))

    for lineno, line in enumerate(lines, start=1):
        matched_categories: set[str] = set()

        # Phase 1 — priority WARN (e.g. subprocess+pytest)
        for name, regex, desc, category in PRIORITY_WARN_PATTERNS:
            if category in matched_categories:
                continue
            m = regex.search(line)
            if m:
                findings.append(
                    _finding(name, lineno, "warn", m.group(), desc)
                )
                matched_categories.add(category)

        # Phase 2 — BLOCK
        for name, regex, desc, category in BLOCK_PATTERNS:
            if category in matched_categories:
                continue
            m = regex.search(line)
            if m:
                if _is_false_positive(line, category):
                    continue
                findings.append(
                    _finding(name, lineno, "block", m.group(), desc)
                )
                matched_categories.add(category)

        # Phase 3 — late WARN (e.g. generic open())
        for name, regex, desc, category in LATE_WARN_PATTERNS:
            if category in matched_categories:
                continue
            m = regex.search(line)
            if m:
                findings.append(
                    _finding(name, lineno, "warn", m.group(), desc)
                )
                matched_categories.add(category)

        # Phase 4 — cross-line: compile() + exec()
        if has_raw_compile and has_exec:
            if re.search(r"(?<![.\w])compile\s*\(", line):
                findings.append(_finding(
                    "compile_exec",
                    lineno,
                    "block",
                    line.strip(),
                    "compile() paired with exec() elsewhere in file "
                    "— obfuscated code execution",
                ))

    safe = not any(f["severity"] == "block" for f in findings)
    return {"safe": safe, "findings": findings}


def scan_code_change(code_change_json: str) -> dict[str, Any]:
    """Scan every Python file in a CodeChange JSON payload.

    Parameters
    ----------
    code_change_json : str
        A JSON string conforming to the ``CodeChange`` schema.  Must
        contain a ``files`` array whose items have ``path`` and ``content``
        keys.

    Returns
    -------
    dict
        ``{"safe": bool, "file_results": {"path": {...}, ...}}``.
        ``safe`` is ``True`` only when **all** scanned Python files are safe.
    """
    try:
        payload = json.loads(code_change_json)
    except (json.JSONDecodeError, TypeError) as exc:
        return {
            "safe": False,
            "file_results": {
                "<invalid_json>": {
                    "safe": False,
                    "findings": [
                        _finding(
                            "json_parse_error",
                            0,
                            "block",
                            str(exc),
                            "Could not parse CodeChange JSON — refusing to proceed",
                        )
                    ],
                }
            },
        }

    files = payload.get("files", [])
    file_results: dict[str, dict[str, Any]] = {}
    all_safe = True

    for entry in files:
        path: str = entry.get("path", "")
        content: str = entry.get("content", "")

        # Only scan Python files — skip .txt, .md, .json, .html, etc.
        if not path.endswith(".py"):
            continue

        result = scan_code(content, path)
        file_results[path] = result
        if not result["safe"]:
            all_safe = False

    return {"safe": all_safe, "file_results": file_results}
