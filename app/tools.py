import logging
import os
import re
import sys
import json
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

def _get_target_dir() -> Path:
    target = os.environ.get("TARGET_APP_DIR")
    if not target:
        raise ValueError("TARGET_APP_DIR environment variable is not set")
    return Path(target).resolve()

def _enforce_target_dir(path: str) -> Path:
    target_dir = _get_target_dir()
    full_path = (target_dir / path).resolve()
    try:
        full_path.relative_to(target_dir)
    except ValueError:
        raise ValueError(f"Path {path} escapes the target directory {target_dir}")
    return full_path

def write_project_file(path: str, content: str) -> dict:
    """Writes a file under TARGET_APP_DIR, creating parent directories if needed."""
    try:
        full_path = _enforce_target_dir(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        return {"status": "success", "path": str(full_path)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def read_project_file(path: str) -> dict:
    """Reads a file under TARGET_APP_DIR."""
    try:
        full_path = _enforce_target_dir(path)
        content = full_path.read_text(encoding="utf-8")
        return {"status": "success", "content": content}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def list_project_files(subdir: str = ".") -> dict:
    """Lists all files in a subdirectory under TARGET_APP_DIR."""
    try:
        full_path = _enforce_target_dir(subdir)
        files = [str(p.relative_to(_get_target_dir())) for p in full_path.rglob("*") if p.is_file()]
        return {"status": "success", "files": files}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def validate_generated_code(code: str, filepath: str) -> dict:
    """Quick safety pre-check on generated code before it is written to disk.

    Catches the most critical dangerous patterns at the tool level.  The full
    scanner in guardrails/ does the heavy lifting; this is a lightweight gate
    so obviously-bad code never touches the filesystem.

    Returns {"safe": True/False, "violations": [str]}.
    """
    violations: list[str] = []

    # os.system() — arbitrary shell execution
    if re.search(r"\bos\.system\s*\(", code):
        violations.append(f"{filepath}: use of os.system() is blocked")

    # eval() not preceded by 'json.' — arbitrary code execution
    if re.search(r"(?<!json\.)\beval\s*\(", code):
        violations.append(f"{filepath}: use of eval() is blocked (json.loads is the safe alternative)")

    # exec() — arbitrary code execution
    if re.search(r"\bexec\s*\(", code):
        violations.append(f"{filepath}: use of exec() is blocked")

    # subprocess calls that sneak in a global pip install, bypassing our DepInstaller
    if re.search(r"\bsubprocess\b", code) and re.search(r"pip\s+install", code):
        violations.append(
            f"{filepath}: subprocess + 'pip install' is blocked — "
            "use the project's install_target_deps tool instead"
        )

    return {"safe": len(violations) == 0, "violations": violations}


def apply_code_change(code_change_json: str) -> dict:
    """Parses CodeChange JSON and applies each FileChange to the TARGET_APP_DIR.
    Rejects any modification under a 'tests' directory to enforce separation of concerns."""
    try:
        change = json.loads(code_change_json)
        files = change.get("files", [])

        # --- Pre-flight validation (atomic: reject ALL files if ANY is unsafe) ---
        all_violations: list[str] = []
        for f in files:
            path = f.get("path", "")
            content = f.get("content", "")
            action = f.get("action")
            if action in ("create", "modify") and content:
                result = validate_generated_code(content, path)
                if not result["safe"]:
                    all_violations.extend(result["violations"])
        if all_violations:
            return {
                "status": "error",
                "message": "Code safety check failed — no files were written",
                "violations": all_violations,
            }

        # --- Apply changes ---
        results = []
        for f in files:
            path = f.get("path")
            content = f.get("content", "")
            action = f.get("action")

            if "tests/" in path.replace("\\", "/"):
                return {"status": "error", "message": f"Coder is not allowed to edit test files: {path}"}

            full_path = _enforce_target_dir(path)

            if action == "create" or action == "modify":
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content, encoding="utf-8")
                results.append({"path": path, "action": action, "status": "success"})
            elif action == "delete":
                if full_path.exists():
                    full_path.unlink()
                results.append({"path": path, "action": "delete", "status": "success"})
            else:
                results.append({"path": path, "action": action, "status": "error", "message": "Unknown action"})

        return {"status": "success", "results": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def _target_python() -> str:
    """Path to the target app's own venv python if it exists, else this interpreter."""
    vpy = _get_target_dir() / ".venv" / "Scripts" / "python.exe"
    return str(vpy) if vpy.exists() else sys.executable


def install_target_deps() -> dict:
    """Ensure the target app has a local .venv with pytest + its requirements installed.

    Uses uv (fast, cached). Creates TARGET_APP_DIR/.venv on first use, then installs
    pytest plus the generated requirements.txt so the test suite can actually run.
    """
    try:
        target_dir = _get_target_dir()
        venv_dir = target_dir / ".venv"
        vpy = venv_dir / "Scripts" / "python.exe"
        if not vpy.exists():
            subprocess.run(["uv", "venv", str(venv_dir)], cwd=str(target_dir),
                           capture_output=True, text=True)
        # Baseline stack the generated FastAPI app + its tests always need, installed even if the
        # coder forgot to write requirements.txt (then requirements.txt is layered on top).
        cmd = ["uv", "pip", "install", "--python", str(vpy),
               "pytest", "pytest-asyncio", "fastapi", "uvicorn", "httpx", "pytz"]
        warnings: list[str] = []
        req = target_dir / "requirements.txt"
        if req.exists():
            # Validate requirements.txt: strip suspicious lines that could compromise
            # the install (malicious index URLs, editable installs from git, local paths).
            raw_lines = req.read_text(encoding="utf-8").splitlines()
            clean_lines: list[str] = []
            for line in raw_lines:
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    clean_lines.append(line)
                    continue
                lower = stripped.lower()
                if "--index-url" in lower or "--extra-index-url" in lower:
                    warnings.append(f"Stripped suspicious index redirect: {stripped}")
                elif (lower.startswith("-e ") or lower.startswith("--editable ")) and (
                    "://" in stripped
                ):
                    warnings.append(f"Stripped suspicious editable install: {stripped}")
                elif "file://" in lower:
                    warnings.append(f"Stripped suspicious file:// path: {stripped}")
                else:
                    clean_lines.append(line)
            if warnings:
                for w in warnings:
                    logger.warning("[install_target_deps] %s", w)
                # Write sanitised requirements to a temp file so we never pass
                # the suspicious lines to pip.
                safe_req = target_dir / ".requirements_safe.txt"
                safe_req.write_text("\n".join(clean_lines), encoding="utf-8")
                cmd += ["-r", str(safe_req)]
            else:
                cmd += ["-r", str(req)]
        r = subprocess.run(cmd, cwd=str(target_dir), capture_output=True, text=True)
        logs = ((r.stdout or "") + (r.stderr or ""))[-2000:]
        if warnings:
            logs = "[SANDBOX] " + "; ".join(warnings) + "\n" + logs
        return {
            "status": "success" if r.returncode == 0 else "error",
            "logs": logs[-2000:],
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def run_tests(test_path: str = ".") -> dict:
    """Runs pytest in TARGET_APP_DIR and returns a TestResults-shaped dict.

    Parses the pytest summary line for accurate pass/fail counts and flags the
    'no tests collected' case (pytest exit code 5) so the gate never treats an
    empty run as green.
    """
    try:
        target_dir = _get_target_dir()
        result = subprocess.run(
            [_target_python(), "-m", "pytest", test_path, "-v", "--tb=short",
             "--rootdir", str(target_dir),
             "--import-mode=importlib", "-o", "asyncio_mode=auto"],
            cwd=str(target_dir),
            capture_output=True,
            text=True,
        )
        out = (result.stdout or "") + "\n" + (result.stderr or "")

        passed = failed = 0
        m_p = re.search(r"(\d+) passed", out)
        m_f = re.search(r"(\d+) failed", out)
        m_e = re.search(r"(\d+) error", out)
        if m_p:
            passed = int(m_p.group(1))
        if m_f:
            failed = int(m_f.group(1))
        if m_e:
            failed += int(m_e.group(1))

        # Compact, high-signal failure list from the summary section (lines like
        # "FAILED tests/x.py::test_y - AssertionError: ..."), so the coder gets a clear
        # to-do list instead of having to parse the whole log.
        failures = [
            {"test": s[:400], "message": "", "trace": ""}
            for s in (ln.strip() for ln in out.splitlines())
            if s.startswith("FAILED ") or s.startswith("ERROR ")
        ]

        no_tests = (result.returncode == 5) or (passed == 0 and failed == 0)
        return {
            "passed": passed,
            "failed": failed,
            "failures": failures,
            # Keep enough log tail that several full --tb=short tracebacks
            # survive: with many failures, 4000 chars was only the summary
            # list, so the coder never saw the actual error text.
            "logs": out[-12000:],
            "no_tests": no_tests,
        }
    except Exception as e:
        return {
            "passed": 0,
            "failed": 1,
            "failures": [{"test": "runner", "message": str(e), "trace": ""}],
            "logs": str(e),
            "no_tests": False,
        }
