# Action Plan — Implementation Schedule & Task Assignment

> Last updated: 2026-07-01
> Deadline: July 6, 2026, 11:59 PM PT

## Parallelization Analysis

### Dependency Graph

```
Feature 1 (Security Guardrails)  ──┐
                                    ├──→ Feature 9 (Comments + README)
Feature 2 (Enhanced PM)  ──────────┤
                                    │
Feature 3 (Progress Stream)  ──────┤
                                    │
Feature 4 (Permission Policy)  ────┘
                                         ↓
Feature 5 (UserTestGuide)  ←── depends on Features 1-4 being stable
Feature 6 (FeedbackClassifier) ←── depends on Feature 5
Feature 7 (Eval Expansion)  ←── can start after Feature 1-2 (needs stable agents to eval)
Feature 8 (Dockerfile)  ──────── fully independent, can run anytime
```

### What Can Run in Parallel

**Parallel Group A** (no dependencies between them):
- Feature 1: Security Guardrails (code scanner, dep checker, sandbox, secrets, circuit breaker, prompt injection defense)
- Feature 2: Enhanced PM Agent (Discovery skill integration)
- Feature 3: Progress Stream Callbacks
- Feature 8: Dockerfile + deploy config

**Parallel Group B** (depends on Group A being done):
- Feature 4: Permission Policy (needs guardrails module structure from Feature 1)
- Feature 7: Eval Expansion (needs stable agents to evaluate)

**Sequential** (each depends on the previous):
- Feature 5: UserTestGuide → Feature 6: FeedbackClassifier

**Final** (needs everything else done):
- Feature 9: Code Comments + README Rewrite

---

## Agent Assignment: Claude Code vs Antigravity

### How Antigravity CLI Works (reference)

```bash
agy -p "<task>. Write the result to C:/Users/Debby/Desktop/Learning/antigravity-output/<filename>" --dangerously-skip-permissions
```

**Antigravity strengths**: It has access to agents-cli skills (they're symlinked to `~/.gemini/antigravity-cli/skills/`). It can read files, write files, and execute commands. It works well for self-contained tasks with clear specs.

**Antigravity limitations**: On Windows, output goes to console not stdout — must write to file. No real-time interaction. Best for "fire and forget" tasks with clear deliverables.

### Assignment Matrix

| Task | Assigned To | Rationale |
|---|---|---|
| **Feature 1A: Code Safety Scanner** | Claude Code | Core security logic — needs iterative testing and careful regex/AST work |
| **Feature 1B: Dependency Checker** | Antigravity | Self-contained module with clear spec: parse requirements.txt, check PyPI API, return result. Clear input/output. |
| **Feature 1C: Sandbox Enforcement** | Claude Code | Modifies existing `tools.py` — needs context of current codebase |
| **Feature 1D: Secret Scanner** | Antigravity | Self-contained regex patterns module. Clear spec: list of patterns → scanner function. Can merge into code_scanner.py after. |
| **Feature 1E: Circuit Breaker** | Claude Code | Modifies existing `escalation.py` — needs understanding of current gate logic |
| **Feature 1F: Prompt Injection Defense** | Antigravity | Self-contained sanitizer module. Clear spec: strip instruction-like patterns from code strings. |
| **Feature 2: Enhanced PM** | Claude Code | Needs deep understanding of Discovery skill + current PM prompt + how they integrate. Too context-heavy for Antigravity. |
| **Feature 3: Progress Stream** | Antigravity | Self-contained callback module. Clear spec: before/after callbacks that log agent name + duration. Doesn't need existing codebase context. |
| **Feature 4: Permission Policy** | Claude Code | Needs to integrate with guardrails module from Feature 1 + understand ADK callback system |
| **Feature 5: UserTestGuide** | Claude Code | New agent — needs understanding of pipeline and how it connects to existing agents |
| **Feature 6: FeedbackClassifier** | Antigravity | Self-contained agent + prompt. Clear spec: input (feedback + spec) → output (bug/new_requirement classification). |
| **Feature 7: Eval Expansion** | Antigravity | Writing eval dataset JSON + eval_config.yaml metrics. Self-contained, spec-driven. |
| **Feature 8: Dockerfile** | Antigravity | Standard Dockerfile + docker-compose for a Python ADK project. Well-defined task. |
| **Feature 9: Code Comments** | Claude Code | Needs deep understanding of WHY each design decision was made — context from our conversation history |
| **Feature 9: README Rewrite** | Claude Code | Needs to weave the competition narrative — context-heavy |

### Summary

| Agent | Tasks | Est. % of work |
|---|---|---|
| **Claude Code** | 1A, 1C, 1E, 2, 4, 5, 9 (comments + README) | ~60% |
| **Antigravity** | 1B, 1D, 1F, 3, 6, 7, 8 | ~40% |

---

## Day-by-Day Schedule

### Day 1 (July 1): Security Guardrails + Parallelizable Starts

**Claude Code** (sequential, core work):
- [ ] Create `app/guardrails/__init__.py`
- [ ] Implement Feature 1A: Code Safety Scanner (`app/guardrails/code_scanner.py`)
- [ ] Implement Feature 1C: Sandbox enforcement (modify `tools.py`)
- [ ] Implement Feature 1E: Circuit breaker (modify `escalation.py`)
- [ ] Register all guardrail callbacks in `app/agent.py`
- [ ] Write unit tests for code scanner

**Antigravity** (parallel, fire-and-forget):
- [ ] Feature 1B: Dependency checker → write to `antigravity-output/dependency_checker.py`
  ```
  agy -p "Write a Python module called dependency_checker.py. It parses a requirements.txt file, checks each package against PyPI API (https://pypi.org/pypi/{name}/json), and returns a report. Include an allowlist of common safe packages (fastapi, uvicorn, sqlalchemy, pytest, httpx, pydantic, etc.) that bypass the PyPI check. Return format: {'safe': bool, 'packages': [{'name': str, 'status': 'allowed'|'verified'|'not_found'|'suspicious', 'reason': str}]}. Include a check_requirements(filepath: str) -> dict function. Write the result to C:/Users/Debby/Desktop/Learning/antigravity-output/dependency_checker.py" --dangerously-skip-permissions
  ```
- [ ] Feature 1D: Secret scanner patterns → write to `antigravity-output/secret_patterns.py`
  ```
  agy -p "Write a Python module called secret_patterns.py with a function scan_for_secrets(code: str, filepath: str) -> list[dict]. It uses regex to detect hardcoded secrets in source code: AWS keys (AKIA...), GCP service account JSON, generic api_key/password assignments, database URLs with embedded credentials, environment variable dumps. Each finding returns {'pattern': str, 'line': int, 'severity': 'block', 'match': str}. Exclude test fixtures (files under tests/ with password='testpass' style assignments). Write the result to C:/Users/Debby/Desktop/Learning/antigravity-output/secret_patterns.py" --dangerously-skip-permissions
  ```
- [ ] Feature 1F: Prompt injection sanitizer → write to `antigravity-output/input_sanitizer.py`
  ```
  agy -p "Write a Python module called input_sanitizer.py with a function sanitize_code_for_prompt(code: str) -> str. It strips patterns from code that could be prompt injection when fed to an LLM: lines matching 'IGNORE.*INSTRUCTIONS', 'SYSTEM.*PROMPT', 'you are now', 'disregard.*above', and similar instruction-override patterns commonly found in code comments or strings. Preserve all actual code logic. Return the sanitized code string. Write the result to C:/Users/Debby/Desktop/Learning/antigravity-output/input_sanitizer.py" --dangerously-skip-permissions
  ```

**End of Day 1 checkpoint**:
- Code scanner catches dangerous patterns ✓
- Circuit breaker stops stalled loops ✓
- Antigravity outputs reviewed and integrated into `app/guardrails/`

---

### Day 2 (July 2): Enhanced PM + Progress Stream + Eval Start

**Claude Code** (core work):
- [ ] Feature 2: Enhanced PM Agent
  - [ ] Copy reference files: `decision-catalog.md`, `spec-quality-lessons.md` → `app/agents/references/`
  - [ ] Rewrite `app/agents/prompts/pm.md` with Discovery interview protocol
  - [ ] Update `app/agents/pm.py` if output format changes
  - [ ] Test: give vague input → PM asks clarifying questions
  - [ ] Test: PM presents tech stack options with pros/cons

**Antigravity** (parallel):
- [ ] Feature 3: Progress stream callbacks → write to `antigravity-output/progress_callbacks.py`
  ```
  agy -p "Write a Python module for Google ADK (google.adk) agent callbacks. Create two functions: (1) make_before_callback(agent_description: str) that returns an async before_agent_callback logging '[timestamp] agent_name started — description', (2) make_after_callback() that returns an async after_agent_callback logging '[timestamp] agent_name done (duration) — summary'. Use Python logging module. Also create a register_progress_callbacks(agent, description: str) function that sets both callbacks on an agent. The callbacks should track start time to compute duration. Import types from google.adk.agents.callback_context. Write the result to C:/Users/Debby/Desktop/Learning/antigravity-output/progress_callbacks.py" --dangerously-skip-permissions
  ```
- [ ] Feature 7 (start): Eval dataset → write to `antigravity-output/eval_dataset.json`
  ```
  agy -p "Write a JSON eval dataset file for a multi-agent coding system. Format: {'eval_cases': [...]}. Create 3 eval cases: (1) 'Build a TODO API' - user asks for a simple CRUD TODO app with FastAPI, (2) 'Build a user auth service' - user asks for registration/login endpoints, (3) 'Build a blog API' - user asks for posts and comments CRUD. Each case uses Shape A format with eval_case_id and prompt containing role:user and parts with text. Write the result to C:/Users/Debby/Desktop/Learning/antigravity-output/eval_dataset.json" --dangerously-skip-permissions
  ```

**End of Day 2 checkpoint**:
- PM agent guides non-technical users through spec creation ✓
- Progress stream shows which agent is active ✓
- Review and integrate Antigravity outputs

---

### Day 3 (July 3): Permission Policy + New Agents + Eval Metrics

**Claude Code**:
- [ ] Feature 4: Permission Policy
  - [ ] Implement `app/guardrails/permission_policy.py`
  - [ ] Define Tier 1 (auto-approve) and Tier 2 (require approval) action lists
  - [ ] Register as `before_tool_callback` on relevant tools
  - [ ] Test: routine actions auto-approved, risky actions prompt
- [ ] Feature 5: UserTestGuide Agent
  - [ ] Create `app/agents/user_test_guide.py` + `app/agents/prompts/user_test_guide.md`
  - [ ] Wire into pipeline after build loop green
  - [ ] Test: given a spec → produces plain-language testing instructions

**Antigravity** (parallel):
- [ ] Feature 6: FeedbackClassifier agent prompt → write to `antigravity-output/feedback_classifier_prompt.md`
  ```
  agy -p "Write a prompt (markdown format) for an LLM agent called FeedbackClassifier. The agent receives: (1) the original product specification (JSON), (2) user feedback text. It must classify the feedback as 'bug' (the spec was violated — something that should work doesn't) or 'new_requirement' (the spec never covered this — the user wants something new). Output format: JSON with type, reasoning, related_criteria fields. Include examples of both types in the prompt. Write the result to C:/Users/Debby/Desktop/Learning/antigravity-output/feedback_classifier_prompt.md" --dangerously-skip-permissions
  ```
- [ ] Feature 7 (continue): Eval metrics config → write to `antigravity-output/eval_config_expanded.yaml`
  ```
  agy -p "Write a YAML eval config file for agents-cli eval. Include these custom metrics: (1) security_compliance - LLM judge prompt that checks generated code for common vulnerabilities (SQL injection, hardcoded secrets, unsafe subprocess calls), scores 1-5. (2) convergence_efficiency - custom_function that counts the number of build loop iterations from agent_data turns, lower is better. (3) spec_adherence - LLM judge prompt that compares the generated API endpoints against the spec and scores completeness 1-5. Keep the existing custom_response_quality and agent_turn_count metrics. Write the result to C:/Users/Debby/Desktop/Learning/antigravity-output/eval_config_expanded.yaml" --dangerously-skip-permissions
  ```

**End of Day 3 checkpoint**:
- Permission policy reduces approval fatigue ✓
- UserTestGuide produces non-technical testing instructions ✓
- FeedbackClassifier skeleton ready ✓

---

### Day 4 (July 4): Dockerfile + Documentation + Integration

**Claude Code**:
- [ ] Feature 6: Wire FeedbackClassifier into codebase (using Antigravity's prompt)
  - [ ] Create `app/agents/feedback_classifier.py`
  - [ ] Connect to pipeline (optional post-human-review step)
- [ ] Feature 9: Code Comments
  - [ ] Add design-rationale comments to all agent files
  - [ ] Focus on: WHY decisions were made, not WHAT the code does
- [ ] Feature 9: README Rewrite
  - [ ] Restructure for competition (Problem → Solution → Architecture → Key Concepts → Security → Eval → Setup → Deploy → Journey)
- [ ] Integration testing: run the full pipeline end-to-end
- [ ] Run `agents-cli eval generate` + `agents-cli eval grade` with expanded dataset

**Antigravity** (parallel):
- [ ] Feature 8: Dockerfile + docker-compose → write to `antigravity-output/`
  ```
  agy -p "Write two files for a Python ADK (Google Agent Development Kit) project: (1) Dockerfile - multi-stage build, Python 3.11, uses uv for dependency management, copies app/ directory, exposes port 8080, runs with uvicorn. (2) docker-compose.yml - defines the agent service with environment variables (GOOGLE_GENAI_USE_VERTEXAI, GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION, TARGET_APP_DIR), mounts a local volume for TARGET_APP_DIR, exposes port 8080. Write both files to C:/Users/Debby/Desktop/Learning/antigravity-output/ as Dockerfile and docker-compose.yml" --dangerously-skip-permissions
  ```

**End of Day 4 checkpoint**:
- All features implemented and integrated ✓
- Eval results documented ✓
- README competition-ready ✓
- Docker build succeeds ✓

---

### Day 5 (July 5): Video + Writeup + Final Polish

**Claude Code** (support role):
- [ ] Final review of all code and documentation
- [ ] Fix any issues found during integration testing
- [ ] Help draft writeup structure and talking points

**Human (Debby)** (primary):
- [ ] Record 5-minute YouTube video
  - Problem statement (non-technical users can't build apps)
  - Architecture diagram walkthrough
  - Live demo: run the system, show progress stream, show testing guide
  - Security features highlight
  - Build story: convergence journey, dogfooding Study Tracker
- [ ] Write Kaggle writeup (≤2500 words)
- [ ] Submit to Kaggle

---

## Review Checklist (before Antigravity output integration)

Every Antigravity output MUST be reviewed by Claude Code before integration:

- [ ] Code correctness: does it actually work?
- [ ] API compatibility: does it use the right ADK callback signatures?
- [ ] Style consistency: matches existing codebase patterns
- [ ] Security: no hardcoded values, no unsafe patterns
- [ ] Test coverage: write tests for integrated modules

---

## Risk Mitigation

| Risk | Mitigation |
|---|---|
| Antigravity outputs don't match ADK API | Claude Code reviews + adapts all outputs before integration |
| GCP account issues block deployment | Dockerfile demonstrates deployability without live deployment |
| Not enough time for all features | Priority order: Security (1) > PM (2) > Progress (3) > Eval (7) > Docker (8) > README (9) > rest |
| Eval doesn't run (needs working pipeline) | Use existing pipeline as baseline; expanded eval is additive |
| Video takes longer than expected | Draft script on Day 4, record Day 5 morning, edit afternoon |

---

## Completion Tracking

| Feature | Status | Last Updated |
|---|---|---|
| 1A Code Safety Scanner | **Done** | 2026-07-01 — `app/guardrails/code_scanner.py` (400 lines, 3-phase pattern matching) |
| 1B Dependency Checker | **Done** | 2026-07-01 — `app/guardrails/dependency_checker.py` (Antigravity, reviewed + integrated) |
| 1C Sandbox Enforcement | **Done** | 2026-07-01 — `app/tools.py` hardened (rootdir, requirements validation, validate_generated_code) |
| 1D Secret Scanner | **Done** | 2026-07-01 — `app/guardrails/secret_patterns.py` (Antigravity, reviewed + integrated) |
| 1E Circuit Breaker | **Done** | 2026-07-01 — `app/agents/escalation.py` (stall detection + intent drift) |
| 1F Prompt Injection Defense | **Done** | 2026-07-01 — `app/guardrails/input_sanitizer.py` (Antigravity, tokenize-based, reviewed + integrated) |
| 2 Enhanced PM Agent | **Done** | 2026-07-01 — PM prompt rewritten (280 lines), decision catalog + spec-quality-lessons copied to references/ |
| 3 Progress Stream | **Done** | 2026-07-01 — `app/callbacks/progress.py` (Antigravity, reviewed + integrated). Needs wiring in agent.py |
| 4 Permission Policy | **Done** | 2026-07-01 — `app/guardrails/permission_policy.py` (2-tier system, batch approval, SAFE_PACKAGES integration) |
| 5 UserTestGuide Agent | **Done** | 2026-07-01 — `app/agents/user_test_guide.py` + prompt. Wired into pipeline after build loop |
| 6 FeedbackClassifier Agent | **Done** | 2026-07-01 — `app/agents/feedback_classifier.py` + prompt. Wired into pipeline after E2E-QA |
| 7 Eval Expansion | **Done** | 2026-07-01 — 5 eval cases + 5 metrics (response_quality, security_compliance, spec_adherence, turn_count, convergence_efficiency) |
| 8 Dockerfile + Deploy | **Done** | 2026-07-01 — Dockerfile (multi-stage), docker-compose.yml, .dockerignore created |
| 9 Code Comments + README | **Done** | 2026-07-01 — Code comments (agent.py docstring, guardrails/__init__.py) + competition-grade README (12 sections, security deep-dive, build story) |
