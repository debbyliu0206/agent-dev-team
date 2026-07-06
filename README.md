# Agent Dev Team — AI-Powered Application Builder for Everyone

> A multi-agent coding system built on Google ADK that turns plain-language requirements into tested, production-quality backend applications.

**Track**: Agents for Business | **Kaggle AI Agents Intensive Vibe Coding Capstone Project**

---

## Problem

Non-technical users — entrepreneurs, product managers, domain experts — have application ideas but lack the engineering skills to build them. Existing AI coding tools are single-agent systems that produce untested, unguarded code with no architectural coherence. A single assistant cannot replicate what a real development team provides: requirements analysis, architecture design, test-driven development, iterative debugging, and quality assurance. These users don't need a coding assistant. They need an expert team.

## Solution

Agent Dev Team is a team of specialized AI agents that mirrors a real software development organization. Each agent owns one responsibility, communicating through structured state — exactly how professional teams operate with specs, contracts, and test results.

| Agent | Role |
|---|---|
| **PM Agent** | Guides the user through a structured Discovery interview to extract features, acceptance criteria, and data shapes |
| **Architect** | Converts the spec into a precise, binding API contract with exact status codes, error handling, and a canonical file layout |
| **TestWriter** | Generates a unit-first test pyramid bound to the contract (TDD approach) |
| **Build Loop** (LoopAgent) | Iterative Coder → CodeApplier → DepInstaller → TestRunner → TestFixer → TestRunner#2 → KeepBest → SpecReviewer → Gate cycle, repeating until all tests pass |
| **UserTestGuide** | Generates plain-language testing instructions so non-technical users can verify the output themselves |
| **E2E QA** | Automated browser testing via Playwright MCP — drives a real browser against the running application |
| **FeedbackClassifier** | Routes user feedback as a bug report vs. a new requirement, enabling a continuous improvement loop |

The pipeline is fully automated: `PM → Architect → TestWriter → LoopAgent[...] → UserTestGuide → E2E QA → FeedbackClassifier`. The build loop repeats up to 5 iterations with a KeepBest snapshot mechanism that prevents regressions and a gate that escalates on green tests or stalled progress.

## Architecture Diagram

![Agent Dev Team — Final Architecture](docs/diagrams/agent-system-final.png)

## Key Concepts Covered

This project demonstrates 5 of 6 competition concepts:

| Concept | Implementation |
|---|---|
| **Multi-Agent Orchestration (ADK)** | `SequentialAgent` orchestrates the full pipeline; `LoopAgent` drives the iterative build cycle. 14 specialized agents with distinct models, tools, and output keys. |
| **MCP Server** | Playwright MCP (`@playwright/mcp@latest`) powers the E2E QA agent for automated browser testing against the generated application. |
| **Security Guardrails** | 6 guardrail modules: code scanner, dependency checker (slopsquatting defense), secret scanner, prompt injection defense, permission policy, and circuit breaker. 33 unit tests covering the guardrails alone. |
| **Deployability** | Multi-stage Dockerfile (builder + runtime) with `docker-compose.yml` for one-command deployment. Vertex AI environment configuration via env vars. |
| **Agent Evaluation** | 5 eval cases with 5 custom metrics (response quality, security compliance, spec adherence, turn count, convergence efficiency) using LLM-as-judge scoring. |

## Security Deep-Dive

Security is the strongest differentiator of this system. Every piece of LLM-generated code passes through multiple guardrail layers before reaching disk.

![Security guardrail funnel](docs/diagrams/security-guardrails.png)

### 1. Code Scanner (`app/guardrails/code_scanner.py`)

3-phase pattern matching with category-based conflict resolution:

- **Phase 1 (Priority WARN)**: Specific safe variants (e.g., `subprocess.run(["pytest"...`)`) downgrade to warnings before the broader block rule fires.
- **Phase 2 (BLOCK)**: Rejects dangerous constructs — `eval()`, `exec()`, `os.system()`, `os.popen()`, `subprocess.*`, raw sockets, `ctypes`/`cffi` FFI, `__import__()`, `importlib.import_module()`, absolute file paths, shebang lines.
- **Phase 3 (Late WARN)**: Low-specificity catch-alls (e.g., any `open()` call) suppressed when a block in the same category already fired.
- **Cross-line detection**: `compile()` paired with `exec()` anywhere in the same file is flagged as obfuscated code execution.
- **False-positive guards**: `json.loads`, `os.path.join`, `os.environ.get`, and framework imports are explicitly safe.

### 2. Dependency Checker (`app/guardrails/dependency_checker.py`)

Defends against slopsquatting — LLMs hallucinating plausible-sounding but nonexistent package names that could be registered as malware:

- Maintains a **safe-package allowlist** of 35+ vetted packages (FastAPI, SQLAlchemy, bcrypt, etc.).
- Every non-allowlisted package is **verified against PyPI** in real time.
- Packages returning HTTP 404 are blocked with an explicit "possible hallucination" warning.

### 3. Secret Scanner (`app/guardrails/secret_patterns.py`)

Detects 9 categories of hardcoded secrets:

- AWS access keys (`AKIA...`), AWS secret keys, GCP service account JSON
- Generic API keys, passwords, tokens
- Database URLs with embedded credentials (`postgresql://user:pass@host`)
- Private keys (RSA/EC/DSA PEM blocks)
- Environment variable dumps (`os.environ` without `.get`/`[]`)

Excludes test fixtures: files under `tests/` with dummy-looking values (`test`, `mock`, `fake`) are not flagged.

### 4. Prompt Injection Defense (`app/guardrails/input_sanitizer.py`)

Uses Python's `tokenize` module for **AST-level token analysis** — not naive string matching:

- Parses code into tokens, inspecting only `COMMENT` and `STRING` tokens for injection patterns.
- Detects 12 injection phrases: `IGNORE ALL`, `IGNORE PREVIOUS`, `SYSTEM PROMPT`, `JAILBREAK`, `BYPASS`, `OVERRIDE`, etc.
- Multi-line string patterns catch hidden instructions in triple-quoted strings (`"""You are...`, `"""System:...`).
- `sanitize_code_for_prompt()` neutralizes injections while preserving all executable code.

### 5. Permission Policy (`app/guardrails/permission_policy.py`)

2-tier permission system with session memory:

- **Tier 1 (auto-approve)**: Routine actions — venv creation, safe dependency installs, test runs, file reads, server starts.
- **Tier 2 (require approval)**: Writes, unknown package installs, file deletes, deploys, external network calls.
- **Session memory**: Previously approved (action, details) pairs are hashed and fast-tracked — no repeat prompts for the same operation.
- **Batch approval**: Multiple Tier-2 actions grouped into a single human-readable prompt.

### 6. Circuit Breaker (`app/agents/escalation.py`)

Prevents infinite resource consumption:

- **Stall detection**: If the passed-test count is unchanged for 3 consecutive build-loop iterations, the loop breaks with a stall report.
- **Intent drift checking**: Warns when the coder introduces files outside the canonical layout defined by the Architect.
- **Green-test escalation**: Tests are the source of truth. When `failed == 0` and tests actually ran, the loop stops — the spec reviewer's compliance flag is advisory only and cannot block a genuinely green build.

## Evaluation

5 eval cases test the full pipeline end-to-end:

| Eval Case | Scenario |
|---|---|
| `todo_api` | CRUD TODO app with SQLite |
| `user_auth` | Registration, JWT login, protected endpoints |
| `blog_api` | Posts + comments with nested CRUD |
| `expense_tracker` | Expenses with date-range filtering and category summaries |
| `bookmark_manager` | Bookmarks with tag search and duplicate URL detection |

5 metrics scored via LLM-as-judge and custom functions:

| Metric | Type | What It Measures |
|---|---|---|
| `response_quality` | LLM judge (1-5) | Accuracy, structure, completeness of agent output |
| `security_compliance` | LLM judge (1-5) | Absence of hardcoded secrets, dangerous functions, SQL injection, path traversal |
| `spec_adherence` | LLM judge (1-5) | Coverage of all requested endpoints, status codes, and features |
| `turn_count` | Custom function | Total agent turns (lower = more efficient) |
| `convergence_efficiency` | Custom function | Build-loop iterations needed to reach green (lower = better) |

## Build Story: The Spec Convergence Problem

The v1 architecture used a flat agent chain and swung between 47%-76% test pass rates — never converging. The root cause: **ambiguous specs produce infinite build loops**.

When the PM's spec said "create a todo endpoint" without specifying exact status codes, error formats, or field names, the Architect, TestWriter, and Coder each made different assumptions. Tests would pass, then break, then pass differently — oscillating without progress.

**Key insight**: The Architect must produce a **binding contract** — exact status codes, exact error shapes, exact field names — and every downstream agent must treat it as the single source of truth. This is the "contract-first" principle.

![The Convergence Journey — measured checkpoints for both apps](docs/diagrams/convergence-journey.png)

The fixes that made it converge:

1. **Contract-first architecture** — one shared truth document from the Architect
2. **Layered single-responsibility** — each agent does exactly one thing
3. **Bottom-up test pyramid** — unit tests first, then API tests, bound to the contract
4. **Canonical file layout** — the Architect defines exact file paths; drift is flagged
5. **Minimal-diff coder + KeepBest** — never rewrite the whole file; snapshot the best state
6. **Target-venv dependency isolation** — generated apps get their own `.venv`

Together these moved the system from oscillating at 47%-76% to 59/59 green tests on a Study Tracker backend.

## Quick Start

### Local (recommended)

```bash
# Install the CLI
uv tool install google-agents-cli

# Install project dependencies
agents-cli install

# Configure environment
cp app/.env.example app/.env
# Edit app/.env with your Vertex AI credentials:
#   GOOGLE_GENAI_USE_VERTEXAI=True
#   GOOGLE_CLOUD_PROJECT=your-project
#   GOOGLE_CLOUD_LOCATION=us-east1

# Launch interactive playground
agents-cli playground
```

### Docker

```bash
docker-compose up --build
```

The container exposes port 8080 and mounts `./target` for generated application output.

## Tech Stack

| Component | Technology |
|---|---|
| Agent Framework | [Google ADK](https://github.com/google/adk-python) (SequentialAgent, LoopAgent, BaseAgent) |
| LLM | Gemini 2.5 Pro (reasoning agents), Gemini 2.5 Flash (utility agents) |
| Language | Python 3.11 |
| Generated Apps | FastAPI + SQLite |
| E2E Testing | Playwright MCP |
| CLI Tooling | [agents-cli](https://pypi.org/project/google-agents-cli/) |
| Package Manager | uv |
| Containerization | Docker (multi-stage build) |
| Observability | OpenTelemetry + Google Cloud Logging |

## Project Structure

```
agent-dev-team/
├── app/
│   ├── agent.py                  # Root SequentialAgent + LoopAgent orchestration
│   ├── agents/
│   │   ├── pm.py                 # PM Agent (requirements → spec)
│   │   ├── architect.py          # Architect (spec → API contract)
│   │   ├── test_writer.py        # TestWriter (contract → test pyramid)
│   │   ├── coder.py              # Coder (contract → implementation)
│   │   ├── code_applier.py       # CodeApplier (writes code to disk)
│   │   ├── dep_installer.py      # DepInstaller (target venv + deps)
│   │   ├── test_runner.py        # TestRunner (runs pytest)
│   │   ├── test_fixer.py         # TestFixer (repairs test mechanics only)
│   │   ├── keep_best.py          # KeepBest (snapshot best-passing state)
│   │   ├── spec_reviewer.py      # SpecReviewer (advisory compliance check)
│   │   ├── escalation.py         # Gate / Circuit Breaker
│   │   ├── user_test_guide.py    # UserTestGuide (plain-language test instructions)
│   │   ├── e2e_qa.py             # E2E QA (Playwright MCP browser testing)
│   │   ├── feedback_classifier.py# FeedbackClassifier (bug vs. new requirement)
│   │   └── prompts/              # Markdown prompt files for each agent
│   ├── guardrails/
│   │   ├── code_scanner.py       # 3-phase code pattern scanner
│   │   ├── dependency_checker.py # PyPI verification + slopsquatting defense
│   │   ├── secret_patterns.py    # Hardcoded secret detection
│   │   ├── input_sanitizer.py    # Prompt injection defense (AST-level)
│   │   └── permission_policy.py  # 2-tier permission system
│   ├── callbacks/
│   │   └── progress.py           # Observability: per-agent timing + progress logs
│   ├── tools.py                  # Shared tools (file I/O, code validation)
│   └── schemas.py                # Pydantic schemas for agent communication
├── tests/
│   ├── unit/
│   │   └── test_guardrails.py    # 33 tests covering all 6 guardrail modules
│   ├── integration/
│   │   ├── test_agent.py         # Agent integration tests
│   │   └── test_server_e2e.py    # Server E2E tests
│   └── eval/
│       ├── eval_config.yaml      # 5 metrics (3 LLM-judge + 2 custom)
│       └── datasets/
│           └── full-pipeline-dataset.json  # 5 eval cases
├── docs/diagrams/                # Architecture diagrams (Excalidraw + PNG)
├── Dockerfile                    # Multi-stage build (builder + runtime)
├── docker-compose.yml            # One-command deployment
├── pyproject.toml                # Project config (uv/hatch)
└── agents-cli-manifest.yaml      # agents-cli project metadata
```

## Future Work

- **Frontend generation**: Extend the pipeline to produce React/Vue frontends that consume the generated API
- **Chat platform integration**: Slack MCP and Feishu MCP for conversational agent access
- **Production deployment**: Cloud Run deployment via `agents-cli deploy` with CI/CD pipeline
- **Multi-language support**: Generate Go, TypeScript, or Rust backends using the same contract-first approach
