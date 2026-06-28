# agent-dev-team — Multi-Agent ADK Software-Dev System

A layered, contract-first multi-agent pipeline (Google ADK + Gemini) that turns requirements into a tested backend. Dogfooded to produce a fully-green (59/59) Study Tracker backend.

## Architecture diagrams

The following 3 diagrams are in `docs/diagrams/` and can be opened at [excalidraw.com](https://excalidraw.com):

- **agent-system-v1**: the first design and why it didn't converge (swung 47%-76%).
- **agent-system-final**: the optimized layered pipeline.
- **agent-system-journey**: the optimization route (each fix dogfooded from a real failing run).

## Agents

| Agent | Model | Tools / capability | Responsibility |
| --- | --- | --- | --- |
| PM | gemini-2.5-pro | LLM | Requirements -> features, acceptance criteria, data shapes (the spec) |
| Architect | gemini-2.5-pro | write_project_file | Spec -> precise API contract (exact status codes, errors, auth) + layered component design + canonical file layout. The single shared ground truth. |
| Test-writer | gemini-2.5-flash | write_project_file | Unit-first test pyramid: tests/unit first, then tests/api; bound to the contract |
| Coder | gemini-2.5-pro | read_project_file, list_project_files | Minimal-diff, bottom-up implementation to the canonical files |
| CodeApplier | deterministic (BaseAgent) | apply_code_change | Writes the coder's CodeChange JSON to disk (decide vs apply split) |
| DepInstaller | deterministic | install_target_deps (uv) | Creates the target's own .venv + installs baseline deps + requirements |
| TestRunner | deterministic | run_tests (pytest) | Runs the tests, writes structured results into session state |
| TestFixer | gemini-2.5-pro | read/list/write_project_file | Repairs TEST errors only (collection/fixture/syntax) — never logic, never app code |
| TestRunner #2 | deterministic | run_tests | Re-runs after TestFixer so the gate sees post-fix results |
| KeepBest | deterministic | filesystem snapshot | Snapshots the best-passing source; reverts a regression |
| Spec-Reviewer | gemini-2.5-pro | read/list_project_file | Advisory compliance review vs contract + deploy lessons |
| gate (EscalationChecker) | deterministic | — | Escalates (stops the loop) when the tests are GREEN |
| E2E-QA | gemini-2.5-flash | Playwright MCP | Drives a real browser; Stage 1 local, Stage 2 production |

(Note: these agents don't consume agents-cli "skills"; the "Tools / capability" column is what each uses.)

## How the loop works

PM -> Architect -> Test-writer -> LoopAgent[ Coder -> CodeApplier -> DepInstaller -> TestRunner -> TestFixer -> TestRunner#2 -> KeepBest -> Spec-Reviewer -> gate ] -> E2E-QA.

The loop repeats (max 5-6) until the gate escalates on green tests. Deterministic steps do the mechanical work; LLM agents do the judgment; KeepBest prevents regressions.

## Runners

- run_staged.py — full generate + build loop (no deploy/E2E)
- run_iterate.py — frozen-artifacts iterate-only loop (contract + tests fixed; runs ONLY the coder loop -> monotonic climb)
- smoke_pm.py — single-agent (PM) smoke test

## What made it converge (lessons)

1) Architect/contract-first (one shared truth) 2) layered single-responsibility 3) bottom-up test pyramid 4) canonical file layout (no duplicate-file pollution) 5) minimal-diff coder + KeepBest 6) target-venv dep install. Together these moved it from swinging 47%-76% to 59/59 green.

## Running it

`agents-cli install`; configure `app/.env` (Vertex: GOOGLE_GENAI_USE_VERTEXAI=True, project, location, TARGET_APP_DIR); then `python run_staged.py`.
